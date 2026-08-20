# Obsidian WM -> iCloud mobile sync

Mirrors the SynapSys SharePoint Working Memory Obsidian vault
(`11_WORKING_MEMORY/Obsidian/`) into a local folder inside iCloud Drive's
Obsidian container, so the current vault state shows up in the Obsidian
app on iPhone/iPad — no manual export, no attaching files.

**This must run on a Mac (or any device with iCloud Drive mounted as a
filesystem) — not in a cloud/remote Claude Code session.** Nothing running
in a hosted container can write into your personal iCloud Drive; iCloud
sync only happens through a device where you're signed into that iCloud
account.

**Direction is one-way: WM -> iCloud, on purpose.** This uses `rclone
sync`, which makes the destination match the source exactly, including
deleting anything in the destination that isn't in the source. That's why
this points at a dedicated mirror vault (`SynapSys-WM-Mirror`), not your
everyday personal vault — if you edit inside the mirror on mobile, those
edits will be silently overwritten on the next sync. Treat the mirror as
read-only on mobile. A true two-way sync (`rclone bisync`) is possible
later but needs more care around conflict handling — not built here.

## One-time setup

1. Install rclone: `brew install rclone` (or see https://rclone.org/downloads/).
2. Configure a remote pointing at the SynapSys SharePoint site:
   ```
   rclone config
   ```
   - `n` for new remote, name it `synapsys-sp` (matches `REMOTE_NAME` in
     the script — change both if you use a different name).
   - Storage type: `onedrive`.
   - Leave client ID/secret blank to use rclone's own registered app,
     unless this ecosystem already has a preferred Entra app registration
     for delegated access — ask before creating a new one if so.
   - Region: `global` (or your tenant's region).
   - When asked "Type of connection", choose **SharePoint site**, then
     search for the SynapSys site and select it. rclone will complete an
     interactive browser OAuth login as your own Microsoft account — you
     need at least read access to `SynapSys-Control/11_WORKING_MEMORY`.
   - Confirm the config, `q` to quit.
3. Test the connection: `rclone lsd synapsys-sp:SynapSys-Control/11_WORKING_MEMORY`
   should list folders including `Obsidian`.
4. Edit `sync_obsidian_to_icloud.sh` if your remote name, WM path, or
   preferred mirror vault name differ from the defaults.
5. Dry run first: `./sync_obsidian_to_icloud.sh --dry-run` — check the log
   at `~/Library/Logs/synapsys-obsidian-sync/sync.log` for what it *would*
   do before letting it write anything.
6. Real run: `./sync_obsidian_to_icloud.sh`.
7. On your iPhone/iPad Obsidian app: "Open folder as vault" -> browse to
   iCloud Drive -> the `SynapSys-WM-Mirror` folder that just appeared.

## Automate it (macOS)

See `com.synapsys.obsidian-icloud-sync.plist` — a launchd agent that runs
the sync every 30 minutes while the Mac is on. Install steps are in the
comment block at the top of that file. `cron` works too if you prefer it;
the script itself doesn't care how it's invoked.

## What this does not do

- Does not sync edits made on mobile back to Working Memory. One-way only.
- Does not touch anything outside `11_WORKING_MEMORY/Obsidian/` on the WM
  side, or anything outside the dedicated mirror folder on the iCloud
  side.
- Does not run anywhere automatically on its own — it needs to be
  installed and scheduled on a real device you control.
