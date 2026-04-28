#!/bin/bash
# safe-compose.sh — docker compose down -v 방지 래퍼
# 사용: ./scripts/safe-compose.sh up -d

set -e

if [[ "$1" == "down" && "$*" == *"-v"* ]]; then
    echo "WARNING: -v flag will DELETE all volumes!"
    echo "Run 'scripts/backup.sh' first if needed."
    read -p "Are you sure? (type YES): " confirm
    [[ "$confirm" != "YES" ]] && exit 1
fi

docker compose "$@"