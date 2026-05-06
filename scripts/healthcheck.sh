#!/bin/bash
# healthcheck.sh — 컨테이너 헬스체크

PROJECT=${COMPOSE_PROJECT_NAME:-wp-memlog}

declare -A CONTAINER_MAP=(
    [meilisearch]="${PROJECT}_meilisearch_1"
    [wordpress]="${PROJECT}_wordpress_1"
    [db]="${PROJECT}_db_1"
)

check_service() {
    local name=$1
    local container="${CONTAINER_MAP[$name]}"

    if docker ps --filter "name=${container}" --filter "status=running" | grep -q "${container}"; then
        echo "✓ ${name}: running"
        return 0
    else
        echo "✗ ${name}: not running"
        return 1
    fi
}

echo "Checking ${PROJECT} services..."
echo ""

failed=0

check_service "meilisearch" || ((failed++))
check_service "wordpress" || ((failed++))
check_service "db" || ((failed++))

echo ""

if [ $failed -eq 0 ]; then
    echo "All services healthy ✓"
    exit 0
else
    echo "${failed} service(s) unhealthy ✗"
    exit 1
fi