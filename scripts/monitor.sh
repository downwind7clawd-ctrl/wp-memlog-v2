#!/bin/bash
# monitor.sh — 임계치 초과 시 알림 (1분 cron용)
# 사용: crontab -e → */1 * * * * /path/to/wp-memlog/scripts/monitor.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/../.env"

PROJECT=${COMPOSE_PROJECT_NAME:-wp-memlog}
THRESHOLD_MB=5325  # 5.2GB in MB
LOG_FILE=/var/log/wp-memlog-monitor.log

MEILI_CONTAINER="wp-memlog-meilisearch"

if ! docker ps --filter "name=${MEILI_CONTAINER}" --filter "status=running" | grep -q "${MEILI_CONTAINER}"; then
    exit 0
fi

MEM_USAGE=$(docker stats "${MEILI_CONTAINER}" --no-stream --format "{{.MemUsage}}" | awk '{print $1}' | sed 's/GiB//')
MEILI_MEM=$(echo "${MEM_USAGE}" | awk '{print int($1 * 1024)}')

if [ "${MEILI_MEM}" -gt "${THRESHOLD_MB}" ]; then
    MSG="wp-memlog: Meilisearch 메모리 ${MEILI_MEM}MB (임계 ${THRESHOLD_MB}MB 초과)"
    echo "$(date): ${MSG}" >> "${LOG_FILE}"
    
    if [ -n "${TG_TOKEN}" ] && [ -n "${TG_CHAT_ID}" ]; then
        curl -s -X POST "https://api.telegram.org/bot${TG_TOKEN}/sendMessage" \
            -d "chat_id=${TG_CHAT_ID}&text=${MSG}" > /dev/null 2>&1
    fi
fi

DISK_USAGE=$(df /var/lib/docker/volumes | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "${DISK_USAGE}" -gt 80 ]; then
    echo "$(date): Docker 볼륨 디스크 ${DISK_USAGE}% 사용" >> "${LOG_FILE}"
fi