#!/usr/bin/env bash
# Back up the state this VPS's odoo-mcp / n8n-mcp deployment can't easily
# recreate from git: the OAuth session-state Docker volumes and (if N8N_URL /
# N8N_API_TOKEN are set) a workflow export. Addresses the gap named in the
# Hostinger assessment: no backup automation existed before this — the only
# documented backup step was a one-off manual instruction in the Hermes
# installation runbook.
#
# Deliberately does NOT back up .env — that file holds live plaintext
# secrets, and copying it into a backup archive just multiplies the number
# of places a leak can happen. Secrets belong in the password manager
# (see SECRETS_INDEX.md); this script backs up state, not credentials.
#
# Usage:
#   ./backup_vps.sh                 # backup to ./backups/
#   BACKUP_DIR=/mnt/offsite ./backup_vps.sh
#
# Suggested cron (daily at 03:15, keep default 14-day retention below):
#   15 3 * * * cd /path/to/deploy/mcp-vps && ./backup_vps.sh >> backup.log 2>&1

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
DEST="${BACKUP_DIR}/${STAMP}"

mkdir -p "$DEST"
chmod 700 "$BACKUP_DIR" "$DEST"

echo "[$STAMP] Backing up to $DEST"

echo "-- Docker volumes --"
for VOL in odoo-mcp-oauth-state n8n-mcp-oauth-state; do
  if docker volume inspect "$(basename "$(pwd)")_${VOL}" >/dev/null 2>&1; then
    FULL_VOL="$(basename "$(pwd)")_${VOL}"
  elif docker volume inspect "${VOL}" >/dev/null 2>&1; then
    FULL_VOL="${VOL}"
  else
    echo "  skip: volume ${VOL} not found (not yet created?)"
    continue
  fi
  echo "  archiving ${FULL_VOL}..."
  docker run --rm \
    -v "${FULL_VOL}:/source:ro" \
    -v "$(cd "$DEST" && pwd):/backup" \
    alpine tar czf "/backup/${VOL}.tar.gz" -C /source .
done

echo "-- N8N workflow export (if credentials available) --"
if [[ -f .env ]]; then
  N8N_URL="$(grep -E '^N8N_URL=' .env | cut -d= -f2- || true)"
  N8N_API_TOKEN="$(grep -E '^N8N_API_TOKEN=' .env | cut -d= -f2- || true)"
  if [[ -n "${N8N_URL:-}" && -n "${N8N_API_TOKEN:-}" ]]; then
    curl -fsS "${N8N_URL}/api/v1/workflows" \
      -H "X-N8N-API-KEY: ${N8N_API_TOKEN}" \
      -o "${DEST}/n8n_workflows_export.json" \
      && echo "  saved n8n_workflows_export.json" \
      || echo "  WARNING: n8n workflow export failed — check N8N_URL/N8N_API_TOKEN"
  else
    echo "  skip: N8N_URL / N8N_API_TOKEN not set in .env"
  fi
else
  echo "  skip: .env not found"
fi

echo "-- Compose + Dockerfile snapshot (no secrets, safe to keep) --"
cp docker-compose.yml Dockerfile "$DEST/" 2>/dev/null || true

echo "-- Manifest --"
( cd "$DEST" && sha256sum * > SHA256SUMS.txt 2>/dev/null || true )

echo "-- Retention: pruning backups older than ${RETENTION_DAYS} days --"
find "$BACKUP_DIR" -maxdepth 1 -mindepth 1 -type d -mtime "+${RETENTION_DAYS}" -print -exec rm -rf {} \;

echo "[$STAMP] Backup complete: $DEST"
echo "Reminder: this directory is LOCAL to the VPS. Copy $DEST offsite (or point"
echo "BACKUP_DIR at an already-mounted offsite path) — a backup that lives on"
echo "the same box it protects doesn't survive that box failing."
