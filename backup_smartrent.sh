#!/bin/bash
set -euo pipefail

# --- Configuration ---
PG_CONTAINER="smartrent_postgres"
PG_USER="smartrent"
PG_DATABASE="smartrent_db"
BACKUP_DIR="$HOME/location-des-biens/backups"
AGE_PUBLIC_KEY="age1x7lrl6ll77auzstpqgn4ptrzxcpnrna4e22mzfx2cd705atfwf2q2mtmym"
RETENTION_DAYS=14

mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUT_FILE="$BACKUP_DIR/smartrent_backup_${TIMESTAMP}.sql.age"

echo "Sauvegarde de la base '$PG_DATABASE' en cours..."

docker exec "$PG_CONTAINER" pg_dump -U "$PG_USER" "$PG_DATABASE" | age -r "$AGE_PUBLIC_KEY" -o "$OUT_FILE"

if [ ! -s "$OUT_FILE" ]; then
  echo "Échec de la sauvegarde — vérifie que le conteneur '$PG_CONTAINER' est bien lancé (docker compose ps)."
  exit 1
fi

SIZE=$(du -h "$OUT_FILE" | cut -f1)
echo "OK : $OUT_FILE ($SIZE)"

# --- Purge des sauvegardes trop anciennes ---
find "$BACKUP_DIR" -name "smartrent_backup_*.sql.age" -mtime "+${RETENTION_DAYS}" -print -delete

echo "Terminé."
