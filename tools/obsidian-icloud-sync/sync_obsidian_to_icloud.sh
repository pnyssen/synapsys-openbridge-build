#!/usr/bin/env bash
#
# One-way mirror: SynapSys SharePoint Working Memory's Obsidian vault ->
# the user's actual vault folder in general iCloud Drive, so the current
# WM vault state IS what shows up in the Obsidian app on iPhone/iPad via
# iCloud sync.
#
# IMPORTANT, confirmed 2026-08-21 via Files app "Get Info" (Where: iCloud
# Drive > Obsidian): the real vault is a plain top-level folder the user
# created directly in general iCloud Drive -- NOT Obsidian's own private
# per-app ubiquity container (~/Library/Mobile Documents/iCloud~md~obsidian/).
# Those are two different locations on disk; earlier revisions of this
# script pointed at the wrong one. General iCloud Drive maps to
# ~/Library/Mobile Documents/com~apple~CloudDocs/ on a Mac.
#
# Requires: rclone (https://rclone.org), configured once with a remote
# named REMOTE_NAME below pointing at the SynapSys SharePoint site's
# document library. See README.md in this folder for the one-time setup.
#
# Direction is WM -> iCloud only. This uses `rclone sync`, which makes the
# destination match the source exactly -- including DELETING anything
# currently in LOCAL_VAULT_PATH that isn't in WM. LOCAL_VAULT_PATH is the
# user's live, real vault folder, confirmed dedicated to this purpose --
# ALWAYS run a dry run first (the default -- see below) after any change
# to REMOTE_PATH or LOCAL_VAULT_PATH, so you see exactly what would be
# deleted before it happens.
set -euo pipefail

# ---- Configuration -- edit these three for your machine ----
REMOTE_NAME="synapsys-sp"
REMOTE_PATH="SynapSys-Control/11_WORKING_MEMORY/Obsidian"
LOCAL_VAULT_PATH="$HOME/Library/Mobile Documents/com~apple~CloudDocs/Obsidian"
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
