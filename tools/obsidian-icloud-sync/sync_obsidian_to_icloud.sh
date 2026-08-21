#!/usr/bin/env bash
#
# One-way mirror: SynapSys SharePoint Working Memory's Obsidian vault ->
# the Obsidian app's iCloud Drive container root, so the current WM vault
# state IS what shows up in the Obsidian app on iPhone/iPad via iCloud
# sync -- no separate mirror vault, this replaces the container's contents
# directly, by explicit choice (confirmed 2026-08-21: target the container
# itself, not a subfolder).
#
# Requires: rclone (https://rclone.org), configured once with a remote
# named REMOTE_NAME below pointing at the SynapSys SharePoint site's
# document library. See README.md in this folder for the one-time setup.
#
# Direction is WM -> iCloud only. This uses `rclone sync`, which makes the
# destination match the source exactly -- including DELETING anything
# currently in LOCAL_VAULT_PATH that isn't in WM. Because this now points
# at the live container root rather than a dedicated mirror subfolder,
# that includes any existing local-only vault content. ALWAYS run
# `--dry-run` first (see below) before the first real run, and after any
# change to REMOTE_PATH, so you see exactly what would be deleted before
# it happens.
set -euo pipefail

# ---- Configuration -- edit these three for your machine ----
REMOTE_NAME="synapsys-sp"
REMOTE_PATH="SynapSys-Control/11_WORKING_MEMORY/Obsidian"
LOCAL_VAULT_PATH="$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents"
# --------------------------------------------------------------

LOG_DIR="$HOME/Library/Logs/synapsys-obsidian-sync"
LOG_FILE="$LOG_DIR/sync.log"
mkdir -p "$LOG_DIR" "$LOCAL_VAULT_PATH"

# Safe by default: this only performs a real, deleting sync when called
# with --apply. Anything else (no args, --dry-run, a typo) is a dry run.
# This is deliberate -- LOCAL_VAULT_PATH is the live Obsidian iCloud
# container, not a disposable mirror folder, so an accidental real run
# (a bad cron edit, a fat-fingered flag) should never be the default path.
DRY_RUN_FLAG="--dry-run"
if [[ "${1:-}" == "--apply" ]]; then
  DRY_RUN_FLAG=""
  echo "REAL RUN -- files in ${LOCAL_VAULT_PATH} will be created/overwritten/deleted to match WM."
else
  echo "DRY RUN -- no files will actually be written or deleted. Pass --apply to perform the real sync."
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
