#!/bin/bash
# backup.sh — wp-memlog 백업 스크립트

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/.."

BACKUP_DIR="${SCRIPT_DIR}/backup"
DATE="$(date +%Y%m%d_%H%M%S)"

mkdir -p "${BACKUP_DIR}"

echo "Backing up ${COMPOSE_PROJECT_NAME}..."

# Resolve container names from COMPOSE_PROJECT_NAME
MEILI_CT="${COMPOSE_PROJECT_NAME}_meilisearch_1"
WP_CT="${COMPOSE_PROJECT_NAME}_wordpress_1"
DB_CT="${COMPOSE_PROJECT_NAME}_db_1"

# Meilisearch data
docker run --rm \
    -v "${COMPOSE_PROJECT_NAME}_meili_data:/data" \
    -v "${BACKUP_DIR}:/backup" \
    alpine tar czf "/backup/meili_${DATE}.tar.gz" -C /data .

# WordPress files
docker run --rm \
    -v "${COMPOSE_PROJECT_NAME}_wp_data:/data" \
    -v "${BACKUP_DIR}:/backup" \
    alpine tar czf "/backup/wp_${DATE}.tar.gz" -C /data .

# MariaDB dump (password via defaults file to avoid ps exposure)
docker exec "${DB_CT}" bash -c '
cat > /tmp/.my.cnf <<EOF
[mysqldump]
user=root
password=${MYSQL_ROOT_PASSWORD}
EOF
chmod 600 /tmp/.my.cnf
mysqldump --defaults-extra-file=/tmp/.my.cnf wp_memlog
rm -f /tmp/.my.cnf
' > "${BACKUP_DIR}/db_${DATE}.sql"

echo "Done! Files:"
ls -lh "${BACKUP_DIR}"/