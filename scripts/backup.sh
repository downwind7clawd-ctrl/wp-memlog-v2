#!/bin/bash
# backup.sh — wp-memlog 백업 스크립트

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT="wp-memlog"
BACKUP_DIR="${SCRIPT_DIR}/backup"
DATE="$(date +%Y%m%d_%H%M%S)"

source "${SCRIPT_DIR}/../.env"

mkdir -p "${BACKUP_DIR}"

echo "Backing up ${PROJECT}..."

# Meilisearch data
docker run --rm \
    -v "${PROJECT}_meili_data:/data" \
    -v "${SCRIPT_DIR}/backup:/backup" \
    alpine tar czf "/backup/meili_${DATE}.tar.gz" -C /data .

# WordPress files
docker run --rm \
    -v "${PROJECT}_wp_data:/data" \
    -v "${SCRIPT_DIR}/backup:/backup" \
    alpine tar czf "/backup/wp_${DATE}.tar.gz" -C /data .

# MariaDB dump (password via defaults file to avoid ps exposure)
docker exec wp-memlog-db bash -c '
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