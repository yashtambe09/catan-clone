#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="$REPO_ROOT/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILE="$BACKUP_DIR/catan_${TIMESTAMP}.sql.gz"

mkdir -p "$BACKUP_DIR"

docker compose -f "$REPO_ROOT/docker-compose.yml" exec -T postgres pg_dump -U catan catan | gzip > "$FILE"

echo "Backup written to $FILE"

# Keep the last 14 days; prune anything older.
find "$BACKUP_DIR" -name 'catan_*.sql.gz' -mtime +14 -delete

# To restore a dump (drops and recreates data in the running postgres container):
#   gunzip -c backups/catan_TIMESTAMP.sql.gz | docker compose exec -T postgres psql -U catan catan
