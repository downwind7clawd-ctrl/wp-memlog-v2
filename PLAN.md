# wp-memlog — Agent Infinite Memory System

> **Status:** Implementation Complete v5.1 (Phase 1-2 Complete, Bug Fixes Applied)
> **Created:** 2026-04-24
> **Updated:** 2026-04-29 (P0/P1 Bug Fixes + Documentation Update)


---

## 1. Goal

### What we're building

**A system that permanently stores agent (Hermes, OpenCode, etc.) session transcripts in WordPress, and returns summarized excerpts on demand via semantic search when past context is needed.**

### Why needed

| Current Problem | Solution |
|---|---|
| Conversations lost when session ends | Store transcripts permanently |
| `session_search` returns only summary, no full text | **Preserve both transcript + summary** |
| 3 years = ~7,500 sessions → search explosion | Plugin searches→summarizes→returns top N |
| Daily logs are manual/summary level | Auto transcript storage + auto enrichment |
| hindsight is structured memory, not conversation transcript | **Transcript-only storage** (complementary with hindsight) |

### Core Principle

> **Transcript storage → Plugin pre-enriches → Agent consumes only the enrichment**

Agent doesn't read transcripts directly. WP plugin automatically indexes/summarizes/embeds on post save, returns only enriched info on search.

> v3.3 Architecture Change: **Disabled** Meilisearch for WP automatic indexing. Python package manages Meilisearch indexing independently. ClassifAI runs async, doesn't affect save/search.

---

## 2. Definition

### System Architecture

```
┌──────────────────────┐
│ Agent (Hermes,       │
│ OpenCode, GeminiCLI) │
│                      │  ① Session end → transcript REST API POST
└──────────┬───────────┘
            │
            ▼
┌──────────────────────────────────────────────────────┐
│  WordPress (Docker Local)                             │
│                                                      │
│  ┌─────────────────────────────────────────────────┐ │
│  │  Private posts (transcript storage)            │ │
│  │  [deus] 2026-04-26 Session — wp-memlog      │ │
│  │  macguffin/hubris in separate categories      │ │
│  │  meta: _memlog_idem (UUID), _classifai_status│ │
│  └─────────────────────┬───────────────────────────┘ │
│                        │                              │
│                        ▼ WP save_post hook (async)     │
│  ┌─────────────────────────────────────────────────┐ │
│  │  ClassifAI (enrichment plugin, async)           │ │
│  │  ② Auto summary (excerpt)                   │ │
│  │  ③ Auto tagging / category classification   │ │
│  │  ④ OpenAI Embeddings generated + stored   │ │
│  │  On complete → Meilisearch excerpt update │ │
│  └─────────────────────────────────────────────────┘ │
│                        │                              │
│                        ▼ Python package indexes directly  │
│  ┌─────────────────────────────────────────────────┐ │
│  │  Meilisearch (search engine)                  │ │
│  │  ⑤ Transcript + summary hybrid index         │ │
│  │  ⑥ REST API :7700 (agent direct call)       │ │
│  │     POST /indexes/wp_posts/search           │ │
│  │  v3.3: WP plugin disabled, Python only   │ │
│  └─────────────────────┬───────────────────────────┘ │
│                        │                              │
│  ┌─────────────────────┴───────────────────────────┐ │
│  │  WordPress MCP (Automattic, optional)        │ │
│  │  ⑦ MCP protocol CRUD exposure             │ │
│  └─────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
            │
            ▼ ⑧ Search → summary + metadata returned
┌──────────────────────┐
│ Agent               │
│ "Find what we discussed 3 years ago" → Meilisearch → top 5 (~1000 tokens)
└──────────────────────┘
```

### Pipeline Flow (v3.3: Event-driven)

```
POST → WP save (always succeeds) → Immediate response
          ↓
          WP save_post hook fires
          ├→ Meilisearch direct index (immediate, excerpt=null)
          └→ ClassifAI async (background)
               On complete:
               ↓
               WP meta update (excerpt)
               └→ Meilisearch document update (excerpt added)
```

> v3.3 Key: ClassifAI failure doesn't affect save/search. Save always succeeds, search works regardless of excerpt presence.

### Plugin Selection (Final)

| Role | Plugin | Reason |
|---|---|---|
| **Search/Index** | **Meilisearch for WP** | Hybrid(keyword+semantic) search, REST API :7700 direct call, single binary Docker deploy. **v3.3: Auto-index disabled, Python package manages alone** |
| **AI Enrichment** | **ClassifAI** (10up) | Auto summary+tagging+embedding on publish. **v3.4: Multi-provider confirmed (OpenAI, xAI/Grok, Together AI, Google AI, Ollama, Azure, AWS Bedrock). OpenAI provider can override URL via `classifai_openai_api_request_post_url` filter → OpenRouter available.** **v3.3: Async processing. Failure doesn't affect save/search** |
| **Embedding (search)** | **bge-m3** (HuggingFace, local) | For Meilisearch semantic search. Runs on CPU, $0 cost. Multi-language (Korean included) |
| **MCP Bridge** | **WordPress MCP** (Automattic, optional) | Expose WP features via MCP protocol. Review after Phase 3 |

**Alternatives reviewed and rejected:** ElasticPress(ES too heavy), Relevanssi(no semantic), WP Vector Search(immature), WP Semantic Search(immature), Ghost(plugin inferior), Notion(rate limit), GitHub Issues(65K char limit), Supabase(500MB limit)

### Agent Categories

| Agent | Category Slug | Description |
|---|---|---|
| 데우스 (Hermes) | `deus` | AI assistant sessions |
| 맥거핀 (OpenCode) | `macguffin` | Coding agent sessions |
| 휴브리스 (GeminiCLI) | `hubris` | Gemini CLI agent sessions |

### Session Collection Strategy

| Agent Type | Collection Method | Target |
|---|---|---|
| **Exit-type** (session kill) | Session end hook → transcript immediate POST | 데우스 (Hermes), 맥거핀 (OpenCode) |
| **Always-on** (no kill) | Cron incremental (last checkpoint) | 휴브리스 (GeminiCLI) |

### Data Format

**Post Title:** `[deus] 2026-04-26 Session — wp-memlog planning rewrite`
**Post Content:** Full transcript (stored as-is)
**Post Status:** `private` (accessible only after admin login)
**Summary:** Auto-generated excerpt by ClassifAI (async, updated on completion)
**Tags:** Auto-generated by ClassifAI (topic-based)
**Embeddings:** Created by ClassifAI OpenAI Embeddings (for enrichment)
**Semantic Search:** Meilisearch + bge-m3 local embedder (for search, $0 API cost)
**Idempotency Key:** `_memlog_idem` custom field (UUID v4, created at session start)

> ℹ️ **ClassifAI `private` status handling (v3.1 fix):** In ClassifAI v2.2.2+, you can **directly check the `post_status` checkbox** in UI settings (`ClassifAI > Language Processing > Settings`). Default only `publish` is checked, so **checking `private` makes it work immediately** (no code change needed). Also programmable via `classifai_post_statuses_for_post_type_or_id` hook. Phase 1: verify `private` option exists in settings UI.

> If that option doesn't exist (older version), alternatives:
> - A) REST API manual trigger: `GET /classifai/v1/generate-excerpt/{post_id}`
> - B) Custom hook via `classifai_should_classify_post` filter
> - C) WP-CLI: `wp classifai classify {post_id}`

### Token Efficiency

| Scenario | Tokens Agent Receives |
|---|---|
| "Find the 'idea' I mentioned last time" (3 years, 7,500 sessions) | Top 5 summaries × ~200 tokens = **~1,000 tokens** |
| Read full 30-day daily logs via read_file | Thousands of tokens (inefficient) |

---

## 3. Risk Analysis (v3.3)

### 🔴 Critical — Resolve in Phase 1

| # | Risk | Details | Mitigation |
|---|--------|------|------|
| C1 | **Meilisearch for WP doesn't index `private` posts** | Most WP search plugins only index `publish` | **v3.3: WP plugin disabled. Python package indexes private posts alone** |
| C2 | **Search fails when ClassifAI fails** | API outage/rate limit → enrichment fails | **v3.3: Event-driven separation. Save always succeeds. Search works without excerpt** |
| C3 | **bge-m3 model download fails** | Network instability → partial download → corrupted model | HF cache volume explicit mount(`hf_cache`). Cache persists in Docker volume |
| C4 | **MariaDB utf8 default** (v3.3 new) | Default utf8 is 3-byte → emoji (4-byte) save fails | `utf8mb4` + `utf8mb4_unicode_ci` explicit |
| C5 | **`read_private_posts` permission missing** (v3.3 new) | Default `read` capability can't read private posts | Custom WP role gets `read_private_posts` explicitly |

### 🟠 High — Resolve Before Phase 2 Start

| # | Risk | Details | Mitigation |
|---|--------|------|------|
| H1 | **Idempotency key duplication** (v3.3 fix) | Content-based key duplicates on timestamp change | **UUID-based external injection** (created at session start, kept until end) |
| H2 | **Large session handling** | Single session >6K tokens → ClassifAI limit exceeded | `tiktoken` accurate count + sentence-based chunking |
| H3 | **Meilisearch excessive memory** | bge-m3 load ~2.2GB + inference + index | 6GB resource limit + monitoring script |
| H4 | **WP REST API meta query disabled** | Custom field search disabled by default | Alternative via WP-CLI (`docker exec wp post list --meta_key=...`) |
| H5 | **Meilisearch uid collision** | WP plugin + Python package both index → duplicate | **v3.3: WP plugin disabled, Python manages alone. uid `str(post_id)` format** |
| H6 | **Volume data loss** | `docker compose down -v` deletes volumes | `safe-compose.sh` wrapper + volume label protection + daily backup |

### 🟡 Medium — Manage During Operations

| # | Risk | Details | Mitigation |
|---|--------|------|------|
| M1 | **Meilisearch index size growth** | 7,500 sessions × 6K tokens → ~90MB+ embedding | `monitor.sh` 1-min monitoring + alert on threshold |
| M2 | **ClassifAI plugin EOL** | May break on WP major version update | Check ClassifAI compatibility before WP update |
| M3 | **WP REST API pagination limit** (v3.3 new) | Default per_page=100. 7,500 sessions = 75 pages | Bulk fetch via WP-CLI directly |
| M4 | **Volume protection blind spot** (v3.3 new) | `safe-compose.sh` only prevents `down -v`. Can't prevent `docker volume rm` | Volume label added (reference only). Real protection: backup reliability + access control |

### Verification Checklist

**Phase 1 (V1~V7):**
| # | Item | Verification Method |
|---|------|----------|
| V1 | ClassifAI private post auto-processing | Save private post → ClassifAI summarize/tag runs |
| V2 | Meilisearch private post indexing | Index private post via Python → Meilisearch search works |
| V3 | Semantic search quality | Test bge-m3 search accuracy with 10 Korean queries |
| V4 | Meilisearch memory stability | Run 24 hours on 6GB limit → memory stable |
| V5 | ClassifAI failure fallback | Simulate OpenAI API failure → save succeeds, excerpt only null |
| V6 | Backup/restore works correctly | Delete volume after backup → restore → data integrity |
| V7 | Application Passwords authentication | Writer/reader REST API POST/GET succeed |

**Phase 2 (V8~V11):**
| # | Item | Verification Method |
|---|------|----------|
| V8 | Idempotency key works correctly | Same UUID re-POST → 409 or existing post update |
| V9 | Chunking quality | 10K token session → chunk → each part ClassifAI enriched |
| V10 | Search result quality | Query 10 past sessions → top 5 relevance 80%+ |
| V11 | Error recovery | Simulate WP down/Meilisearch down → auto-recover → retry success |

---

## 4. Roadmap

> **v3.3 Execution Principles:**
> - ❌ Don't run Phase 1 and Phase 2 simultaneously. Writing Python code before passing V1~V7 shakes validation baseline.
> - ❌ Don't run WP plugin index and direct index simultaneously. Don't know truth. Pick one and disable other.
> - ❌ Don't hardcode secrets in docker-compose.yml. Even with .env, accidentally committed.
> - ✅ First task: `docker compose up -d` → 3 container healthcheck pass → Phase 1a complete.

### Phase 1: WordPress Docker Local Setup (v3.3: 4-step split)

**Goal:** Local environment with WP + Meilisearch + ClassifAI working

> v3.3: Grouping V1~V7 in one Phase blocks everything on one failure. Split by actual implementation steps.

#### Phase 1a: Docker Setup
**Verification:** 3 containers pass healthcheck

- [ ] Docker Compose (WordPress + MariaDB + Meilisearch)
  ```yaml
  services:
    meilisearch:
      image: getmeili/meilisearch:v1.12
      restart: unless-stopped
      deploy:
        resources:
          limits:
            memory: 6G           # v3.2: bge-m3 ~2.2GB + inference + index safety margin
          reservations:
            memory: 2G
      environment:
        - MEILI_ENV=production
        - MEILI_MASTER_KEY=${MEILI_MASTER_KEY}
        - MEILI_NO_ANALYTICS=true
      volumes:
        - meili_data:/meili_data
        - hf_cache:/root/.cache/huggingface  # v3.3: bge-m3 model cache (prevent re-download on restart)
      ports:
        - "127.0.0.1:7700:7700"            # Local access only (H3)
      healthcheck:                          # v3.2
        test: ["CMD", "wget", "--no-verbose", "--spider", "http://localhost:7700/health"]
        interval: 10s
        timeout: 5s
        retries: 5

    wordpress:
      image: wordpress:6.7
      restart: unless-stopped
      deploy:
        resources:
          limits:
            memory: 512M
      environment:
        - WORDPRESS_DB_HOST=db
        - WORDPRESS_DB_USER=wp
        - WORDPRESS_DB_PASSWORD=${WP_DB_PASSWORD}
        - WORDPRESS_DB_NAME=wp_memlog
      volumes:
        - wp_data:/var/www/html
      ports:
        - "8080:80"
      healthcheck:                          # v3.2
        test: ["CMD", "curl", "-f", "http://localhost:80"]
        interval: 10s
        timeout: 5s
        retries: 5

    db:
      image: mariadb:11.4
      restart: unless-stopped
      deploy:
        resources:
          limits:
            memory: 512M
      environment:
        - MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}
        - MYSQL_DATABASE=wp_memlog
        - MYSQL_USER=wp
        - MYSQL_PASSWORD=${WP_DB_PASSWORD}
        - MYSQL_CHARSET=utf8mb4          # v3.3: Required for Korean emoji
        - MYSQL_COLLATION=utf8mb4_unicode_ci
      command: >                           # v3.3: Force utf8mb4 at server level
        --character-set-server=utf8mb4
        --collation-server=utf8mb4_unicode_ci
        --innodb-buffer-pool-size=256M
      volumes:
        - db_data:/var/lib/mysql
      healthcheck:
        test: ["CMD", "healthcheck.sh", "--connect", "--innodb_initialized"]
        interval: 10s
        timeout: 5s
        retries: 5

  volumes:
    meili_data:
      labels:
        com.wp-memlog.protect: "true"       # v3.3: Volume protection label
    wp_data:
      labels:
        com.wp-memlog.protect: "true"
    db_data:
      labels:
        com.wp-memlog.protect: "true"
    hf_cache:                                # v3.3: HuggingFace model cache
  ```
- [ ] `.env` template
  ```bash
  # .env (NEVER commit to git)
  MEILI_MASTER_KEY=<random-32-char>
  MYSQL_ROOT_PASSWORD=<random-24-char>
  WP_DB_PASSWORD=<random-24-char>
  COMPOSE_PROJECT_NAME=wp-memlog    # Explicit project name (needed for backup/restore)
  ```
- [ ] **`safe-compose.sh`** — `docker compose down -v` prevention wrapper
  ```bash
  #!/bin/bash
  # Warn + confirmation on -v
  if [[ "$1" == "down" && "$*" == *"-v"* ]]; then
      echo "⛔ WARNING: -v flag will DELETE all volumes!"
      echo "Run 'scripts/backup.sh' first if needed."
      read -p "Are you sure? (type YES): " confirm
      [[ "$confirm" != "YES" ]] && exit 1
  fi
  docker compose "$@"
  ```

#### Phase 1b: Basic Integration
**Verification:** WP admin login, REST API response, category creation, custom role creation

- [ ] WordPress install and initial setup (private site)
- [ ] Category creation (deus, macguffin, hubris)
- [ ] **WP custom role creation** (v3.3: default roles can't control permissions)
  - Create via `functions.php` or custom plugin:
    ```php
    // Memlog Writer: create/edit/read posts
    add_role('memlog_writer', 'Memlog Writer', [
        'read' => true,
        'edit_posts' => true,
        'publish_posts' => true,
        'read_private_posts' => true,   // v3.3: required for private post read
        'edit_private_posts' => true,
        'delete_posts' => false,        // Disable delete (safety)
    ]);
    // Memlog Reader: read-only
    add_role('memlog_reader', 'Memlog Reader', [
        'read' => true,
        'read_private_posts' => true,   # v3.3: can't read private without this!
    ]);
    ```
  - `memlog-writer` account → Application Password → `WP_MEMLOG_POST_APPPW`
  - `memlog-reader` account → Application Password → `WP_MEMLOG_READ_APPPW`

#### Phase 1c: ClassifAI + Meilisearch Integration
**Verification:** V1, V2, V3, V5

- [ ] ClassifAI plugin install + **OpenAI API key** setting (OpenRouter not supported)
  - Settings → ClassifAI → Enter OpenAI API Key
- [ ] ClassifAI `private` status handling (v2.2.2+ checkbox)
- [ ] **Meilisearch for WP plugin install** → **disable auto-index** (v3.3)
  > ⚠️ Turn off WP plugin auto-index. Python package manages alone.
  > Keeping both as "backup" causes uid collision hell. Phase 1d: verify WP plugin uid format, match Python package.
- [ ] **Meilisearch embedder setting:**
  ```bash
  curl -X PATCH "http://127.0.0.1:7700/indexes/wp_posts/settings/embedders" \
    -H "Authorization: Bearer ${MEILI_MASTER_KEY}" \
    -H "Content-Type: application/json" \
    -d '{
      "default": {
        "source": "huggingFace",
        "model": "BAAI/bge-m3",
        "documentTemplate": "{{doc.title}} {{doc.content}}",
        "documentTemplateMaxBytes": 10000
      }
    }'
  ```
  - ⚠️ bge-m3 first index auto-downloads (~2.2GB, 5-15min). Saved in HF cache volume, no re-download on restart.
  - v3.3 fix: `documentTemplateMaxBytes: 10000` is **max bytes of text for embedding** (not document storage limit). Transcripts stored unlimited. 10,000 bytes ≈ 5,000 Korean chars ≈ within bge-m3 input limit (8,192 tokens) — safe. Chunking is for embedding quality.
- [ ] **Index schema definition:**
  ```bash
  curl -X PATCH "http://127.0.0.1:7700/indexes/wp_posts/settings" \
    -H "Authorization: Bearer ${MEILI_MASTER_KEY}" \
    -H "Content-Type: application/json" \
    -d '{
      "filterableAttributes": ["categories", "tags", "status", "date", "_enriched"],
      "sortableAttributes": ["date"],
      "searchableAttributes": ["title", "content", "excerpt"],
      "displayedAttributes": ["title", "content", "excerpt", "categories", "tags", "date", "status", "_enriched"]
    }'
  ```
- [ ] **Meilisearch Search API Key creation** (search-only key instead of master)
  ```bash
  curl -X POST "http://127.0.0.1:7700/keys" \
    -H "Authorization: Bearer ${MEILI_MASTER_KEY}" \
    -H "Content-Type: application/json" \
    -d '{
      "name": "agent_search",
      "description": "Search-only for agents",
      "actions": ["search"],
      "indexes": ["wp_posts"],
      "expiresAt": null
    }'
  ```
- [ ] **🧪 V1 test:** Save private post → ClassifAI auto enrichment runs
- [ ] **🧪 V2 test:** Private post → Python indexes to Meilisearch → search works
- [ ] **🧪 V3 test:** Korean queries (10) → bge-m3 semantic search accuracy
- [ ] **🧪 V5 test:** Simulate ClassifAI failure → save succeeds, excerpt only null

#### Phase 1d: Security + Stability
**Verification:** V4, V6, V7

- [ ] **🧪 V4:** 24-hour memory monitoring via `docker stats` on 6GB limit
- [ ] **🧪 V7:** writer/reader Application Passwords REST API POST/GET succeed
- [ ] Minimum backup setup
  ```bash
  PROJECT=${COMPOSE_PROJECT_NAME:-wp-memlog}
  # Meilisearch (index + embedding cache)
  docker run --rm -v ${PROJECT}_meili_data:/data -v $(pwd):/backup \
    alpine tar czf /backup/meili_backup_$(date +%Y%m%d).tar.gz /data
  # WordPress (files)
  docker run --rm -v ${PROJECT}_wp_data:/data -v $(pwd):/backup \
    alpine tar czf /backup/wp_backup_$(date +%Y%m%d).tar.gz /data
  # MariaDB dump
  docker exec ${PROJECT}-db-1 mysqldump -u root -p"${MYSQL_ROOT_PASSWORD}" wp_memlog \
    > backup/db_$(date +%Y%m%d).sql
  ```
- [ ] **🧪 V6:** Backup → volume delete → restore → data integrity
- [ ] Resource usage measurement (RAM, CPU, disk I/O)
- [ ] **`monitor.sh`** — Alert only on threshold exceed (1-min cron)
  ```bash
  #!/bin/bash
  MEILI_MEM=$(docker stats wp-memlog-meilisearch-1 \
    --no-stream --format "{{.MemUsage}}" | awk '{print $1}' | \
    sed 's/GiB//' | awk '{print int($1 * 1024)}')  # MB
  THRESHOLD=5325  # 5.2GB in MB
  if [ "$MEILI_MEM" -gt "$THRESHOLD" ]; then
    MSG="🚨 wp-memlog: Meilisearch memory ${MEILI_MEM}MB (exceeds ${THRESHOLD}MB)"
    curl -s -X POST "https://api.telegram.org/bot${TG_TOKEN}/sendMessage" \
      -d "chat_id=${TG_CHAT_ID}&text=${MSG}" > /dev/null 2>&1
  fi
  DISK_USAGE=$(df /var/lib/docker/volumes | tail -1 | awk '{print $5}' | sed 's/%//')
  if [ "$DISK_USAGE" -gt 80 ]; then
    echo "🚨 $(date): Docker volume disk ${DISK_USAGE}%" >> /var/log/wp-memlog-monitor.log
  fi
  ```

### Phase 2: wp-memlog Python Package

**Goal:** Agent auto-posts session transcripts to WP + Meilisearch indexes

- [ ] **Package structure** (v3.3: MVP simplified)
  > Only what's actually needed for Phase 1 MVP. Premature module separation = unstable interfaces → refactoring cost.
  ```toml
  # pyproject.toml key dependencies
  [project.dependencies]
  python = ">=3.10"
  httpx = ">=0.27"            # async HTTP (replaces requests)
  meilisearch = ">=0.31"      # Official Python SDK (instead of REST direct)
  tiktoken = ">=0.7"          # v3.3: required (250KB, accurate token count)
  python-dotenv = ">=1.0"     # .env loading
  tenacity = ">=8.0"          # retry (exponential backoff)
  ```
  ```
  wp-memlog/
  ├── pyproject.toml
  ├── src/wp_memlog/
  │   ├── __init__.py
  │   ├── client.py          # WP REST API + Meilisearch search + session POST (integrated)
  │   ├── session.py         # SessionPayload + idempotency + chunking (integrated)
  │   └── indexer.py         # Meilisearch direct index (WP plugin disabled, manages alone)
  ├── scripts/
  │   ├── healthcheck.sh
  │   ├── safe-compose.sh
  │   └── monitor.sh
  └── tests/
      ├── test_client.py
      ├── test_session.py
      └── test_indexer.py
  ```
  > Refactor module separation when stable in Phase 2-3.

- [ ] **Error handling strategy** (v3.3 new)
  ```python
  class WpMemlogError(Exception): pass
  class WpApiError(WpMemlogError): pass
  class MeilisearchError(WpMemlogError): pass
  class ClassifAIError(WpMemlogError): pass

  from tenacity import retry, stop_after_attempt, wait_exponential

  @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
  def post_session(payload: SessionPayload) -> PostResult:
      ...
  ```

- [ ] **`session.py` — Session payload + idempotency + chunking** (v3.3 fix)
  ```python
  import uuid

  @dataclass
  class SessionPayload:
      """Payload created at session start, kept until session end."""
      agent: str
      date: str
      content: str
      idem_key: str = field(default_factory=lambda: str(uuid.uuid4()))
      # Same idem_key on retry → duplicate prevention
      # UUID-based, not content-based → unaffected by timestamp/format change

  def check_existing(idem_key: str) -> int | None:
      """Check existing via WP-CLI (bypass REST API meta query disabled)."""
      result = subprocess.run([
          "docker", "exec", "wp-memlog-wp-1", "wp", "post", "list",
          "--post_type=post", "--post_status=private",
          "--meta_key=_memlog_idem", f"--meta_value={idem_key}",
          "--fields=ID", "--format=json"
      ], capture_output=True, text=True)
      posts = json.loads(result.stdout)
      return int(posts[0]["ID"]) if posts else None
  ```

- [ ] **`client.py` — WP REST API + Meilisearch search** (v3.3: Event-driven)
  ```python
  @dataclass
  class PostResult:
      post_id: int
      indexed: bool
      enriched: bool     # ClassifAI enrichment complete

  def post_session(payload: SessionPayload) -> PostResult:
      """v3.3: Separate save and enrichment. ClassifAI failure doesn't affect save/search."""
      # Step 1: Save to WP (must always succeed)
      existing = check_existing(payload.idem_key)
      if existing:
          post_id = existing
      else:
          post_id = wp_client.create_post(
              title=payload.title, content=payload.content,
              status="private",
              meta={"_memlog_idem": payload.idem_key,
                    "_classifai_status": "pending"}
          )

      # Step 2: Index to Meilisearch directly (immediate, even without excerpt)
      index_post(post_id, payload.title, payload.content,
                 excerpt=None, categories=[payload.category])

      # Step 3: ClassifAI handled async via WP save_post hook
      # ClassifAI complete → WP meta update → Meilisearch excerpt update
      return PostResult(post_id=post_id, indexed=True, enriched=False)
  ```

  **Search result structure** (v3.3 improved):
  ```python
  @dataclass
  class SearchResult:
      post_id: int
      title: str
      excerpt: str | None        # None = ClassifAI incomplete
      content_preview: str       # First 500 chars (fallback when no excerpt)
      date: str
      categories: list[str]
      tags: list[str]
      relevance_score: float     # Meilisearch _rankingScore
      enriched: bool             # ClassifAI enrichment complete
      url: str

  def search_sessions(query: str, category: str = None, limit: int = 5) -> list[SearchResult]:
      results = index.search(query, {
          'limit': limit,
          'hybrid': {'semanticRatio': 0.7, 'embedder': 'default'},
          'filter': [f'categories = {category}'] if category else None,
      })
      # Return with metadata agent can judge
  ```

- [ ] **`indexer.py` — Meilisearch direct index** (v3.3)
  ```python
  from meilisearch import Client  # v3.3: Official SDK instead of REST direct

  meili = Client("http://127.0.0.1:7700", api_key=MEILI_SEARCH_API_KEY)
  index = meili.index(MEILI_INDEX_NAME)

  def index_post(post_id: int, title: str, content: str,
                 excerpt: str | None = None, categories: list = None):
      """Index WP post to Meilisearch directly.
      v3.3: WP plugin auto-index disabled, Python package manages alone.
      """
      index.add_documents([{
          "id": str(post_id),
          "title": title,
          "content": content,
          "excerpt": excerpt or "",
          "categories": categories or [],
          "date": ...,
          "status": "private",
          "_enriched": bool(excerpt),
      }])

  def update_excerpt(post_id: int, excerpt: str):
      """Update only summary after ClassifAI completes."""
      index.update_documents([{
          "id": str(post_id),
          "excerpt": excerpt,
          "_enriched": True,
      }])
  ```
  > ⚠️ **v3.3 key decision:** **Disable** Meilisearch for WP auto-index.
  > Python package manages alone. Even matching uid format, running both sources
  > means "which is truth?" Phase 1d: verify WP plugin uid format,
  > then use identical `id: str(post_id)` as Python package.

- [ ] **Session chunking logic** (`session.py`)
  ```python
  import tiktoken
  _enc = tiktoken.encoding_for_model("gpt-4")

  def count_tokens(text: str) -> int:
      """Accurate token count (tiktoken). v3.3: required."""
      return len(_enc.encode(text))

  def chunk_session(transcript: str, max_tokens: int = 6000) -> list[str]:
      """Chunk by sentence + line break. Korean conversation support."""
      # Protect markdown code blocks
      code_blocks = []
      def _protect(m):
          code_blocks.append(m.group(0))
          return f'\x00CODEBLOCK_{len(code_blocks)-1}\x00'
      transcript = re.sub(r'```.*?```', _protect, transcript, flags=re.DOTALL)
      # Protect triple backticks (prevent nesting)
      transcript = transcript.replace('```', '\x00TRIPLE_BACKTICK\x00')

      # Split by sentence + line break
      parts = re.split(r'(?<=[.!?。])\s*|\n{2,}', transcript)

      chunks, current = [], ""
      for p in parts:
          if count_tokens(current + p) > max_tokens:
              if current.strip():
                  chunks.append(current.strip())
              current = p
          else:
              current += (" " if current and not current.endswith('\n') else "") + p
      if current.strip():
          chunks.append(current.strip())

      # v3.3: Restoration logic bug fix (old: loop var unused, some chunks unrestored)
      result = []
      for chunk in chunks:
          restored = chunk
          for i, block in enumerate(code_blocks):
              restored = restored.replace(f"\x00CODEBLOCK_{i}\x00", block)
          restored = restored.replace("\x00TRIPLE_BACKTICK\x00", "```")
          result.append(restored)
      return chunks
  ```
  - Title separator between chunks: `... Session — {topic} (1/3)`, `... (2/3)` ...
  - v3.3 TODO: Problem when code block > `max_tokens`. One chunk infinitely large. Code block split strategy decided in Phase 2 test.

- [ ] Auto session topic extraction
  - Method 1 (default): LLM prompt topic extraction → created by agent at session end
  - Method 2 (fallback): Extract 3 keywords from first 10 turns
- [ ] **ClassifAI failure reprocessing**
  ```bash
  # Get failed post IDs
  wp post list --meta_key=_classifai_error --fields=ID --format=csv
  # Bulk reprocess
  wp post list --meta_key=_classifai_error --field=ID --format=ids \
    | xargs -I{} wp classifai classify {}
  ```

### Phase 3: Search Integration

**Goal:** Agent searches past sessions via Meilisearch API

- [ ] Meilisearch search functions
  - Category filter (specific agent results only)
  - Date range filter
  - Hybrid search: keyword/semantic ratio via `hybrid` param (default `0.7` semantic / `0.3` keyword)
  - Semantic search handled by **bge-m3 local embedder** → $0 API cost
- [ ] Search results → `SearchResult` structure return (v3.3)
  - Fallback to content_preview (first 500 chars) if no excerpt
  - `_enriched` flag indicates ClassifAI completion
- [ ] session-cleanup skill wp-memlog hook
- [ ] Hermes `config.yaml` MCP server registration (optional)

### Phase 4: Multi-Agent Integration

**Goal:** Auto-run from 데우스/맥거핀/휴브리스

- [ ] 데우스 (Hermes): Auto-call from session-cleanup skill
- [ ] 맥거-pin (OpenCode): Session end hook integration
- [ ] 휴브리스 (GeminiCLI): Cron incremental collection
- [ ] Cross-reference: One agent searches another's past

### Phase 5: Enhancement (Optional)

- [ ] GitHub repo creation (`wp-memlog`)
- [ ] README: Getting started guide (Docker Compose, plugin setup, API auth)
- [ ] ClassifAI + Ollama integration (v3.3.1+, complete $0 API cost)
- [ ] Dashboard (operations monitoring)
- [ ] Personalization guide (connect to own WP)

---

## 5. Cost Estimate (OpenAI Direct Billing)

### API Requirements
- **ClassifAI enrichment:** Multi-provider support (OpenAI, xAI/Grok, Together AI, Google AI, Ollama, Azure, AWS Bedrock). **v3.4: OpenAI provider can override URL via `classifai_openai_api_request_post_url` filter → OpenRouter available.** Cost varies by provider.
- **Meilisearch semantic search:** bge-m3 local embedder → **$0 API cost**
- **Search queries:** Meilisearch handles locally → **0 API requests**

### API Call Structure (ClassifAI OpenAI calls only)

| Step | API | Model | Tokens (per session) | Rate |
|---|---|---|---|---|
| ClassifAI Summary | **O** | gpt-4o-mini | ~3,000(in) + ~200(out) | $0.00057 |
| ClassifAI Embedding | **O** | text-embedding-3-small | ~3,000(in) | $0.00006 |
| Meilisearch Search | **X** | bge-m3 local | 0 | $0 |
| **Total per session** | | | ~6,200 | **~$0.00063** |

### Monthly Cost Scenario

**Basic: 5 sessions per day**

| Item | Daily | Monthly (30 days) | Cost |
|---|---|---|---|
| ClassifAI Summary | 5 | 150 | ~$0.09 |
| ClassifAI Embedding | 5 | 150 | ~$0.009 |
| **Monthly total** | | | **~$0.10/month** |

**Maximum: 3 agents × 10 sessions per day**

| Item | Daily | Monthly (30 days) | Cost |
|---|---|---|---|
| ClassifAI Summary | 30 | 900 | ~$0.54 |
| ClassifAI Embedding | 30 | 900 | ~$0.054 |
| **Monthly total** | | | **~$0.60/month** |

> ⭐ **Key: All search handled locally by Meilisearch → $0 API cost. Only ClassifAI enrichment billed. Under $1/month = effectively free.**

### Cost Savings Options

| Method | Savings | Description |
|---|---|---|
| **OpenRouter** (v3.4) | **Use desired model** | Override OpenRouter endpoint via `classifai_openai_api_request_post_url` filter. Free/cheap models available |
| **xAI/Grok** (v3.4) | **xAI pricing** | ClassifAI native xAI provider support. Separate API key |
| **Ollama** (v3.4) | **$0 API** | ClassifAI native Ollama provider support. Set endpoint URL directly. Local summarization. Requires RAM 8GB+ |
| bge-m3 local (default) | Search API $0 | Semantic queries handled locally (already applied) |

---

## 6. Success Criteria

- [ ] Session transcripts from 3 agents automatically saved to WordPress
- [ ] ClassifAI auto-enriches (summary/tag) private posts
- [ ] Korean hybrid search (keyword+semantic) works correctly
- [ ] Top 5 search results more relevant than direct file reading
- [ ] Monthly API cost maintained under $1
- [ ] Save + search work when ClassifAI fails (v3.3)

---

## 7. Glossary

| Term | Meaning |
|---|---|
| **Transcript** | Full session conversation (original text as-is) |
| **Enrichment** | Summary/tag/embedding generation done by ClassifAI |
| **Session** | Single agent conversation session (start→end) |
| **Idempotency** | Same request multiple times = same result (duplicate prevention) |
| **Event-driven** | Async processing via WP save_post hook (v3.3) |

---

## 8. Unresolved / Decision Needed

| Item | Status | Notes |
|---|---|---|
| WordPress MCP adoption | Pending | Review in Phase 3. Search works without MCP via Meilisearch REST API |
| ClassifAI summary model | gpt-4o-mini (default) | Cost optimal. Can switch to Claude etc. after Phase 2 test |
| Meilisearch for WP `private` index | **WP plugin disabled** | v3.3: Python package indexes alone. WP plugin installed only (disabled) |
| Meilisearch memory | **6GB confirmed** | bge-m3 ~2.2GB + inference + index safety margin |
| ClassifAI sync/async | **Async separated (v3.3)** | Separate save/enrichment. ClassifAI failure doesn't affect save/search |
| `draft` vs `private` | **`private` confirmed** | Check `private` in ClassifAI settings → works immediately (v2.2.2+) |
| Local LLM switch | TBD | ClassifAI native Ollama provider support (v3.4 check). Set endpoint directly. Requires RAM 8GB+ |
| OpenRouter integration | ✅ **Implemented in Python directly** | `src/wp_memlog/enrichment.py` - Call OpenRouter API directly from Python instead of ClassifAI WP plugin |
| Large code block chunking | TBD | Code block split strategy decided in Phase 2 test |

**v5.0 Improvement Tasks:**

| # | Item | Details | Priority |
|---|---|---|---|
| I1 | ClassifAI OpenRouter auth problem | **High** - Currently only Python works, WP plugin no automation |
| I2 | WP save_post hook integration | Auto summarization after ClassifAI alternative implementation |

---

## 9. References

- [Meilisearch for WordPress](https://wordpress.org/plugins/meilisearch-wordpress/)
- [ClassifAI (10up)](https://wordpress.org/plugins/classifai/)
- [WordPress MCP (Automattic)](https://github.com/automattic/wordpress-mcp)
- [WordPress MCP Adapter](https://github.com/WordPress/mcp-adapter)
- Existing site: https://downwind7.wordpress.com/ (Football&gossip)

---

## 10. Changelog

| Version | Date | Changes |
|---|---|---|
| v1.0 | 2026-04-24 | Draft (WP + ClassifAI + Meilisearch architecture confirmed) |
| v2.0 | 2026-04-24 | Plugin comparison, Meilisearch confirmed, ClassifAI confirmed, bge-m3 local |
| v3.0 | 2026-04-25 | Idempotency, chunking, cost analysis, Phase structure |
| v3.1 | 2026-04-27 | ClassifAI private=checkbox fix, REST GET fix, Korean chunking, estimate_tokens, Meilisearch Search API Key, minimal backup |
| v3.2 | 2026-04-27 | C1/C2 fail alternative matrix, direct Meilisearch index, docker-compose加固, idempotency key, estimate_tokens tiktoken, healthcheck/safe-compose, verification checklist, .env template, Phase 3~5 detail, monitoring/alert, volume protection |
| v3.3 | 2026-04-27 | 15-year review 2nd: idempotency UUID injection, chunker restoration bug fix, MariaDB utf8mb4+innodb-buffer-pool, read_private_posts+custom WP roles, ClassifAI async separation(event-driven), Phase 1 split(1a~1d), bge-m3 HF cache volume, Meilisearch Python SDK, tiktoken required, tenacity error handling, WP plugin disabled(alone manage), SearchResult structure, documentTemplateMaxBytes fix, volume labels, monitor.sh, package structure MVP simplified(3 modules) |
| **v4.0** | **2026-04-27** | **Implementation complete: Phase 1-2 complete, Docker-compose WP+MariaDB+Meilisearch, WordPress install+roles+App Password, Meilisearch index+schema, Python package(bge-m3 embedder+indexer+session+client), CLI(post+search), WP-CLI based auth, V1~V7 verification complete** |
| **v4.1** | **2026-04-27** | **Phase 3 search integration: category filter, hybrid search, excerpt fallback, CLI update** |
| **v4.2** | **2026-04-27** | **Phase 4 multi-agent: collector_adapters, agents.yaml, collector_cli, Hermes memory/*.md support** |
| **v5.0** | **2026-04-28** | **Verification complete + Collector, OpenRouter direct integration (Python), .env setup, improvement tasks(I1,I2) added** |
| **v5.1** | **2026-04-29** | **P0/P1 bug fixes: idempotency logic (try/except/else), docker-compose env var names, backup.sh hardcoded password removal, collector.sh dry-run fix, collector_cli.py dead code removal, memlog-setup.php security (random password, no error_log), PyYAML dependency added. Documentation update.** |

Detailed work log: See IMPLEMENTATION_LOG.md