#!/usr/bin/env bash
# wp-memlog — Health check & diagnostics
# Usage: ./scripts/doctor.sh [--fix]
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_DIR/.env"
FIX_MODE="${1:-}"

PASS=0
FAIL=0
WARN=0

ok()   { echo -e "  ${GREEN}✓${NC} $1"; PASS=$((PASS + 1)); }
fail() { echo -e "  ${RED}✗${NC} $1"; FAIL=$((FAIL + 1)); }
warn() { echo -e "  ${YELLOW}⚠${NC} $1"; WARN=$((WARN + 1)); }
info() { echo -e "  ${BLUE}ℹ${NC} $1"; }

WP="docker exec wp-memlog-wp wp --allow-root --path=/var/www/html"

echo -e "\n${BOLD}${CYAN}━━━ wp-memlog Doctor ━━━${NC}\n"

# ── 1. Docker containers ───────────────────────────────
echo -e "${BOLD}[1/8] Docker Containers${NC}"
declare -A CNAME=( [meilisearch]="wp-memlog-meilisearch" [wordpress]="wp-memlog-wp" [db]="wp-memlog-db" )
for svc in meilisearch wordpress db; do
    local_name="${CNAME[$svc]}"
    status=$(docker inspect --format='{{.State.Health.Status}}' "$local_name" 2>/dev/null || echo "not found")
    running=$(docker inspect --format='{{.State.Running}}' "$local_name" 2>/dev/null || echo "false")

    if [[ "$status" == "healthy" ]]; then
        ok "$svc: healthy"
    elif [[ "$running" == "true" ]]; then
        warn "$svc: running but not healthy ($status)"
    else
        fail "$svc: not running"
        if [[ "$FIX_MODE" == "--fix" ]]; then
            info "  → Starting containers..."
            (cd "$PROJECT_DIR" && docker compose up -d)
        fi
    fi
done

# ── 2. Environment ─────────────────────────────────────
echo -e "\n${BOLD}[2/8] Environment${NC}"
if [[ -f "$ENV_FILE" ]]; then
    ok ".env exists"
    # Check key vars
    for var in MEILI_MASTER_KEY MEILI_SEARCH_KEY MYSQL_ROOT_PASSWORD WP_ADMIN_PASSWORD WP_MEMLOG_MEILI_KEY; do
        if grep -q "^${var}=" "$ENV_FILE" && [[ -n "$(grep "^${var}=" "$ENV_FILE" | cut -d= -f2)" ]]; then
            ok "  $var set"
        else
            fail "  $var missing or empty"
        fi
    done
else
    fail ".env not found — run ./scripts/setup.sh"
fi

# ── 3. WordPress ───────────────────────────────────────
echo -e "\n${BOLD}[3/8] WordPress${NC}"
if $WP core is-installed 2>/dev/null; then
    ok "WordPress installed"
else
    fail "WordPress not installed"
fi

# Check categories from agents.yaml (dynamic)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
categories=$(python3 -c "
import yaml
cfg = yaml.safe_load(open('$PROJECT_DIR/config/agents.yaml'))
agents = cfg.get('agents', {})
enabled = [a['category'] for a in agents.values() if a.get('category') and a.get('enabled', False)]
print(' '.join(enabled))
" 2>/dev/null)
if [ -z "$categories" ]; then
    categories="deus"
fi
for cat in $categories; do
    if $WP term list category --slug="$cat" --field=slug 2>/dev/null | grep -q "$cat"; then
        ok "  category: $cat"
    else
        fail "  category: $cat missing"
        if [[ "$FIX_MODE" == "--fix" ]]; then
            $WP term create category "$cat" 2>/dev/null && info "  → Created $cat"
        fi
    fi
done

# Check roles
role_check() { $WP eval "echo get_role('$1') ? 'ok' : 'fail';" 2>/dev/null | grep -q ok; }
if role_check memlog_writer; then ok "  role: memlog_writer"; else fail "  role: memlog_writer missing"; fi
if role_check memlog_reader; then ok "  role: memlog_reader"; else fail "  role: memlog_reader missing"; fi

# ── 4. Meilisearch ─────────────────────────────────────
echo -e "\n${BOLD}[4/8] Meilisearch${NC}"
meili_url=$(grep WP_MEMLOG_MEILI_URL "$ENV_FILE" 2>/dev/null | cut -d= -f2 || echo "http://127.0.0.1:7700")
meili_key=$(grep MEILI_MASTER_KEY "$ENV_FILE" 2>/dev/null | cut -d= -f2 || echo "")

health=$(curl -sf "${meili_url}/health" 2>/dev/null || echo "unreachable")
if echo "$health" | grep -q "available"; then
    ok "Meilisearch healthy"
else
    fail "Meilisearch unreachable"
fi

stats=$(curl -sf -H "Authorization: Bearer ${meili_key}" "${meili_url}/indexes/wp_posts/stats" 2>/dev/null || echo "{}")
docs=$(echo "$stats" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('numberOfDocuments',d.get('number_of_documents',0)))" 2>/dev/null || echo "?")
info "  Indexed documents: $docs"

# ── 5. Python package ──────────────────────────────────
echo -e "\n${BOLD}[5/8] Python Package${NC}"
if [[ -d "$PROJECT_DIR/.venv" ]]; then
    ok "venv exists"
else
    fail "venv not found — run ./scripts/setup.sh"
fi

if "$PROJECT_DIR/.venv/bin/python3" -c "from wp_memlog import session, client, embedder, indexer" 2>/dev/null; then
    ok "Package imports OK"
else
    fail "Package import failed"
    if [[ "$FIX_MODE" == "--fix" ]]; then
        info "  → Reinstalling..."
        "$PROJECT_DIR/.venv/bin/pip" install -e "$PROJECT_DIR" 2>&1 | tail -3
    fi
fi

# ── 6. CLI smoke test ──────────────────────────────────
echo -e "\n${BOLD}[6/8] CLI Smoke Test${NC}"
test_title="[doctor] $(date +%s)"
post_output=$("$PROJECT_DIR/.venv/bin/python3" "$PROJECT_DIR/src/wp_memlog_cli.py" post \
    --agent doctor --date "$(date +%Y-%m-%d)" \
    --content "Doctor health check test" \
    --title "$test_title" 2>&1)

if echo "$post_output" | grep -q "Indexed"; then
    ok "post command works"
else
    fail "post command failed: $(echo "$post_output" | tail -3)"
fi

search_output=$("$PROJECT_DIR/.venv/bin/python3" "$PROJECT_DIR/src/wp_memlog_cli.py" search "doctor" --limit 1 2>&1)
if echo "$search_output" | grep -q "result"; then
    ok "search command works"
else
    fail "search command failed: $(echo "$search_output" | tail -3)"
fi

# ── 7. Disk & Memory ───────────────────────────────────
echo -e "\n${BOLD}[7/8] Resources${NC}"
meili_mem=$(docker stats wp-memlog-meilisearch --no-stream --format "{{.MemUsage}}" 2>/dev/null | awk '{print $1}' || echo "?")
info "  Meilisearch memory: $meili_mem"

wp_mem=$(docker stats wp-memlog-wp --no-stream --format "{{.MemUsage}}" 2>/dev/null | awk '{print $1}' || echo "?")
info "  WordPress memory: $wp_mem"

disk_pct=$(df "$PROJECT_DIR" | tail -1 | awk '{print $5}')
info "  Disk usage: $disk_pct"

# ── 8. Backup ──────────────────────────────────────────
echo -e "\n${BOLD}[8/8] Backup${NC}"
backup_dir="$PROJECT_DIR/scripts/backup"
if [[ -d "$backup_dir" ]] && [[ "$(ls -A "$backup_dir" 2>/dev/null)" ]]; then
    latest=$(ls -t "$backup_dir"/meili_*.tar.gz 2>/dev/null | head -1)
    if [[ -n "$latest" ]]; then
        backup_age=$(( ($(date +%s) - $(stat -c %Y "$latest")) / 3600 ))
        if [[ $backup_age -lt 24 ]]; then
            ok "Recent backup (${backup_age}h ago)"
        else
            warn "Last backup ${backup_age}h ago — consider running backup.sh"
        fi
    else
        warn "No backup files found"
    fi
else
    warn "No backup directory — run ./scripts/backup.sh"
fi



# ── Summary ────────────────────────────────────────────
echo ""
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}Results: ${GREEN}${PASS} passed${NC} / ${RED}${FAIL} failed${NC} / ${YELLOW}${WARN} warnings${NC}"
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if [[ $FAIL -gt 0 ]]; then
    echo ""
    if [[ "$FIX_MODE" != "--fix" ]]; then
        info "Run with --fix to auto-repair issues"
    fi
    exit 1
else
    echo -e "\n${GREEN}${BOLD}All systems operational! 🎯${NC}\n"
    exit 0
fi
