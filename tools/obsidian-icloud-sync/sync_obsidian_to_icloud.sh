#!/usr/bin/env bash
#
# One-way mirror: SynapSys SharePoint Working Memory's Obsidian vault ->
# a local folder inside iCloud Drive's Obsidian container, so the current
# vault state is readable (and editable, subject to the caution below) from
# the Obsidian app on iPhone/iPad via iCloud sync.
#
# Requires: rclone (https://rclone.org), configured once with a remote
# named REMOTE_NAME below pointing at the SynapSys SharePoint site's
# document library. See README.md in this folder for the one-time setup.
#
# Direction is WM -> iCloud only. This uses `rclone sync`, which makes the
# destination match the source exactly -- including deleting local files
# that don't exist in WM. That is why this script targets a DEDICATED
# mirror vault folder, not your everyday personal vault: never point
# LOCAL_VAULT_PATH at a vault you also edit directly on mobile, or your
# own edits will be silently deleted on the next run.
set -euo pipefail

# ---- Configuration -- edit these three for your machine ----
REMOTE_NAME="synapsys-sp"
REMOTE_PATH="SynapSys-Control/11_WORKING_MEMORY/Obsidian"
LOCAL_VAULT_PATH="$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/SynapSys-WM-Mirror"
# --------------------------------------------------------------

LOG_DIR="$HOME/Library/Logs/synapsys-obsidian-sync"
LOG_FILE="$LOG_DIR/sync.log"
mkdir -p "$LOG_DIR" "$LOCAL_VAULT_PATH"

DRY_RUN_FLAG=""
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN_FLAG="--dry-run"
  echo "DRY RUN -- no files will actually be written or deleted."
fi

echo "$(date -u +%FT%TZ)  starting sync: ${REMOTE_NAME}:${REMOTE_PATH} -> ${LOCAL_VAULT_PATH}" | tee -a "$LOG_FILE"

rclone sync \
  "${REMOTE_NAME}:${REMOTE_PATH}" \
  "${LOCAL_VAULT_PATH}" \
  --fast-list \
  --checksum \
  --exclude ".obsidian/workspace*.json" \
  ${DRY_RUN_FLAG} \
  --log-file "$LOG_FILE" \
  --log-level INFO

echo "$(date -u +%FT%TZ)  sync complete" | tee -a "$LOG_FILE"
