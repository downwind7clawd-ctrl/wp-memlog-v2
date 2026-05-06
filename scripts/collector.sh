#!/bin/bash
# wp-memlog collector - Collect sessions from multiple agents
# Usage: collector.sh --run [--agent AGENT]
#        collector.sh --daemon  (runs continuously)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CONFIG="$PROJECT_DIR/config/agents.yaml"
INTERVAL="${COLLECTOR_INTERVAL:-21600}"  # default 6 hours

run_collector() {
    AGENT="$1"
    echo "[$(date)] Collecting sessions from: $AGENT"
    "$PROJECT_DIR/.venv/bin/python3" "$PROJECT_DIR/src/collector_cli.py" --config "$CONFIG" collect "$AGENT" 2>&1
}

    daemon_mode() {
        echo "Starting collector daemon (interval: ${INTERVAL}s)"
        while true; do
            # Load enabled agents dynamically from agents.yaml
            AGENTS=$(python3 -c "
import yaml
cfg = yaml.safe_load(open('$CONFIG'))
agents = cfg.get('agents', {})
enabled = [k for k, a in agents.items() if a.get('enabled', False)]
print(' '.join(enabled))
" 2>/dev/null)
            if [ -z "$AGENTS" ]; then
                echo "[$(date)] WARNING: No enabled agents in agents.yaml, using 'hermes'"
                AGENTS="hermes"
            fi
            for AGENT in $AGENTS; do
                run_collector "$AGENT"
            done
            sleep "$INTERVAL"
        done
    }

case "${1:-}" in
    --run)
        AGENT="${2:-hermes}"
        run_collector "$AGENT"
        ;;
    --daemon)
        daemon_mode
        ;;
    *)
        echo "Usage: $0 {--run [agent]|--daemon}"
        exit 1
        ;;
esac