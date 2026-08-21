# Obsidian WM -> iCloud mobile sync

Mirrors the SynapSys SharePoint Working Memory Obsidian vault
(`11_WORKING_MEMORY/Obsidian/`) into the Obsidian app's iCloud Drive
container, so the current WM vault state IS what you see in Obsidian on
iPhone/iPad — no manual export, no attaching files.

**This must run on a Mac (or any device with iCloud Drive mounted as a
filesystem) — not in a cloud/remote Claude Code session.** Nothing running
in a hosted container can write into your personal iCloud Drive; iCloud
sync only happens through a device where you're signed into that iCloud
account.

**Direction is one-way: WM -> iCloud, confirmed.** This uses `rclone
sync`, which makes the destination match the source exactly — including
deleting anything in the destination that isn't in WM.

**Target, confirmed 2026-08-21**: the destination is the Obsidian app's
iCloud container root itself
(`~/Library/Mobile Documents/iCloud~md~obsidian/Documents`) — the same
"Obsidian" folder you see under iCloud Drive in the Files app — not a
separate dedicated mirror folder. That means this tool will make that
folder's contents match Working Memory exactly, on purpose. Anything
already in there that isn't part of the WM vault will be deleted on the
first real run. If you keep other, unrelated vaults or files inside that
same container, say so before running this for real — as configured, it
does not distinguish them.

**Edits made on mobile will not survive.** Because sync is one-way and
destination-clobbering, anything you edit in this vault on your phone/iPad
gets overwritten on the next sync from WM. Treat the mobile copy as
read-only. A true two-way sync (`rclone bisync`) is possible later but
needs real care around conflict handling — not built here.

## Safety: dry-run by default

The script **never performs a real, deleting sync unless you pass
`--apply`**. Running it with no arguments (or `--dry-run` explicitly) only
logs what it *would* do. This is deliberate: the target is your live
Obsidian container, not a disposable folder, so an accidental automated
run should never be able to delete something for real without that
explicit flag having been set on purpose (the launchd template below
already includes `--apply`, since automation is meant to actually run —
set it up only after you've verified a manual dry run and a manual
`--apply` run both look right).

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
4. Edit `sync_obsidian_to_icloud.sh` if your remote name or the WM path
   differ from the defaults.
5. **Dry run** (the default — no flag needed): `./sync_obsidian_to_icloud.sh`
   — read the log at `~/Library/Logs/synapsys-obsidian-sync/sync.log`
   carefully. Look specifically for `Deleted` lines: those are files
   currently in your Obsidian iCloud folder that are about to be removed
   because they're not part of the WM vault. If anything unexpected shows
   up there, stop and figure out why before proceeding.
6. Once the dry run looks right: `./sync_obsidian_to_icloud.sh --apply`.
7. Open Obsidian on your iPhone/iPad — the vault backed by that iCloud
   folder now reflects Working Memory's current state.

## Automate it (macOS)

See `com.synapsys.obsidian-icloud-sync.plist` — a launchd agent that runs
`sync_obsidian_to_icloud.sh --apply` every 30 minutes while the Mac is on.
Install steps are in the comment block at the top of that file. Only
install this after step 5 and 6 above have both been run manually and
looked correct. `cron` works too if you prefer it; the script itself
doesn't care how it's invoked.

## What this does not do

- Does not sync edits made on mobile back to Working Memory. One-way only.
- Does not touch anything outside `11_WORKING_MEMORY/Obsidian/` on the WM
  side.
- Does not run anywhere automatically on its own — it needs to be
  installed and scheduled on a real device you control.
- Does not perform a real sync without `--apply` — see Safety, above.

## Provenance

Also committed to git: `pnyssen/synapsys-openbridge-build`,
`tools/obsidian-icloud-sync/`.
