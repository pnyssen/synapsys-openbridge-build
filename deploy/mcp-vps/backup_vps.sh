#!/usr/bin/env bash
# Back up the state this VPS's odoo-mcp / n8n-mcp deployment can't easily
# recreate from git: the OAuth session-state Docker volumes and (if N8N_URL /
# N8N_API_TOKEN are set) a workflow export.
#
# Uses restic (https://restic.net) instead of hand-rolled tar.gz archives —
# gets encryption, deduplication, and real retention/pruning policy for
# free, plus native support for offsite backends (S3, B2, SFTP, etc.)
# instead of a local-only directory that doesn't survive the box failing.
# The full init/backup/check/restore/forget sequence below was smoke-tested
# locally against a real restic repository before this script was written.
#
# Deliberately does NOT back up .env — that file holds live plaintext
# secrets, and copying it into a backup archive just multiplies the number
# of places a leak can happen. Secrets belong in the password manager
# (see SECRETS_INDEX.md); this script backs up state, not credentials.
#
# Required env (add to .env — see .env.example):
#   RESTIC_REPOSITORY   Where snapshots live. Local path (e.g.
#                        /var/backups/mcp-vps-restic) works but doesn't
#                        protect against the VPS itself failing — point
#                        this at s3:..., b2:..., or sftp:... for real
#                        offsite backup. See https://restic.readthedocs.io/en/stable/030_preparing_a_new_repo.html
#   RESTIC_PASSWORD     Repository encryption password. Losing it means
#                        losing the backups — store it in the password
#                        manager (SynapSys - VPS - RESTIC_PASSWORD), not
#                        only in .env.
# Optional env:
#   RESTIC_KEEP_DAILY / RESTIC_KEEP_WEEKLY / RESTIC_KEEP_MONTHLY
#     (default 14 / 8 / 6, same policy validated in the local smoke test)
#   AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY / AWS_DEFAULT_REGION
#     (only needed if RESTIC_REPOSITORY is an s3:... backend)
#
# Usage:
#   ./backup_vps.sh              # backup + prune
#   ./backup_vps.sh check        # integrity check only (run periodically,
#                                  e.g. weekly, alongside the daily backup)
#
# Suggested cron:
#   15 3 * * * cd /path/to/deploy/mcp-vps && ./backup_vps.sh >> backup.log 2>&1
#   30 4 * * 0 cd /path/to/deploy/mcp-vps && ./backup_vps.sh check >> backup.log 2>&1

set -euo pipefail

: "${RESTIC_REPOSITORY:?Set RESTIC_REPOSITORY in .env first (see header comment)}"
: "${RESTIC_PASSWORD:?Set RESTIC_PASSWORD in .env first — store it in the password manager too}"

RESTIC_IMAGE="restic/restic:0.17.3"
KEEP_DAILY="${RESTIC_KEEP_DAILY:-14}"
KEEP_WEEKLY="${RESTIC_KEEP_WEEKLY:-8}"
KEEP_MONTHLY="${RESTIC_KEEP_MONTHLY:-6}"
CACHE_VOL="mcp-vps-restic-cache"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"

# Bind-mount the repository path into the container only when it's local
# (starts with "/"). Remote backends (s3:/b2:/sftp:) need no such mount —
# just network reachability and, for s3, the AWS_* env vars.
RESTIC_MOUNTS=(-v "${CACHE_VOL}:/root/.cache/restic")
if [[ "$RESTIC_REPOSITORY" == /* ]]; then
  mkdir -p "$RESTIC_REPOSITORY"
  RESTIC_MOUNTS+=(-v "${RESTIC_REPOSITORY}:${RESTIC_REPOSITORY}")
fi

RESTIC_ENV=(-e RESTIC_REPOSITORY -e RESTIC_PASSWORD)
for V in AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_DEFAULT_REGION; do
  [[ -n "${!V:-}" ]] && RESTIC_ENV+=(-e "$V")
done

run_restic() {
  docker run --rm "${RESTIC_MOUNTS[@]}" "${RESTIC_ENV[@]}" "$RESTIC_IMAGE" "$@"
}

if [[ "${1:-}" == "check" ]]; then
  echo "[$STAMP] Running restic check (integrity only, no backup)"
  run_restic check
  exit 0
fi

echo "[$STAMP] Ensuring restic repository exists at ${RESTIC_REPOSITORY}"
run_restic snapshots >/dev/null 2>&1 || run_restic init

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
  echo "  backing up ${FULL_VOL} via restic..."
  docker run --rm "${RESTIC_MOUNTS[@]}" "${RESTIC_ENV[@]}" \
    -v "${FULL_VOL}:/data:ro" \
    "$RESTIC_IMAGE" backup /data --tag "$VOL" --host mcp-vps
done

echo "-- N8N workflow export (if credentials available) --"
STAGING="$(mktemp -d)"
trap 'rm -rf "$STAGING"' EXIT
if [[ -f .env ]]; then
  N8N_URL="$(grep -E '^N8N_URL=' .env | cut -d= -f2- || true)"
  N8N_API_TOKEN="$(grep -E '^N8N_API_TOKEN=' .env | cut -d= -f2- || true)"
  if [[ -n "${N8N_URL:-}" && -n "${N8N_API_TOKEN:-}" ]]; then
    if curl -fsS "${N8N_URL}/api/v1/workflows" \
      -H "X-N8N-API-KEY: ${N8N_API_TOKEN}" \
      -o "${STAGING}/n8n_workflows_export.json"; then
      docker run --rm "${RESTIC_MOUNTS[@]}" "${RESTIC_ENV[@]}" \
        -v "${STAGING}:/data:ro" \
        "$RESTIC_IMAGE" backup /data --tag n8n-workflows --host mcp-vps
      echo "  n8n workflow export backed up"
    else
      echo "  WARNING: n8n workflow export failed — check N8N_URL/N8N_API_TOKEN"
    fi
  else
    echo "  skip: N8N_URL / N8N_API_TOKEN not set in .env"
  fi
else
  echo "  skip: .env not found"
fi

echo "-- Retention: keep ${KEEP_DAILY} daily / ${KEEP_WEEKLY} weekly / ${KEEP_MONTHLY} monthly, prune the rest --"
run_restic forget --keep-daily "$KEEP_DAILY" --keep-weekly "$KEEP_WEEKLY" --keep-monthly "$KEEP_MONTHLY" --prune

echo "[$STAMP] Backup complete. List snapshots any time with:"
echo "  docker run --rm ${RESTIC_MOUNTS[*]} ${RESTIC_ENV[*]} $RESTIC_IMAGE snapshots"
if [[ "$RESTIC_REPOSITORY" == /* ]]; then
  echo "NOTE: RESTIC_REPOSITORY is a local path — it does not survive this VPS"
  echo "      failing. Point RESTIC_REPOSITORY at s3:/b2:/sftp: for real offsite"
  echo "      protection (see header comment)."
fi
