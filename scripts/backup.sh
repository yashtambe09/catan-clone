#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="$REPO_ROOT/backups"
# Placeholder off-disk destination - just another local path for now, so a
# single-disk failure taking out the repo checkout doesn't also take out
# every backup. Revisit per decisions.md (cloud storage / external drive /
# S3 or B2 bucket still an open decision).
OFFSITE_DIR="/c/Users/yasht/CatanBackups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILE="$BACKUP_DIR/catan_${TIMESTAMP}.sql.gz"
# Must match the project name the prod stack is actually running under
# (docker-compose.yml's implicit project name, derived from the containing
# directory, won't necessarily be "catan-prod" - the deploy job starts it
# with `docker compose -p catan-prod ...` explicitly).
COMPOSE_PROJECT="catan-prod"

mkdir -p "$BACKUP_DIR" "$OFFSITE_DIR"

docker compose -p "$COMPOSE_PROJECT" -f "$REPO_ROOT/docker-compose.yml" exec -T postgres pg_dump -U catan catan | gzip > "$FILE"

echo "Backup written to $FILE"
cp "$FILE" "$OFFSITE_DIR/"
echo "Copied to $OFFSITE_DIR"

# Keep the last 14 days; prune anything older, in both locations.
find "$BACKUP_DIR" -name 'catan_*.sql.gz' -mtime +14 -delete
find "$OFFSITE_DIR" -name 'catan_*.sql.gz' -mtime +14 -delete

# To restore a dump (drops and recreates data in the running postgres container):
#   gunzip -c backups/catan_TIMESTAMP.sql.gz | docker compose -p catan-prod exec -T postgres psql -U catan catan
