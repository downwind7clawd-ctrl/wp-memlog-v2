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
    "$PROJECT_DIR/.venv/bin/python3" "$PROJECT_DIR/src/collector_cli.py" --config "$CONFIG" collect "$AGENT" --dry-run 2>&1
}

daemon_mode() {
    echo "Starting collector daemon (interval: ${INTERVAL}s)"
    while true; do
        for AGENT in hermes opencode; do
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