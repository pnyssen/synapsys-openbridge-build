# RECEIPT: RC05c scaffold polish, dev install on Hostinger V20 (27 Nov 2026)
Work Object WO-SYNAPSYS-CANONICAL-REFERENCE-ARCHITECTURE-001 | CTX-SS | Status: INSTALLED ON DEV (restart only), OBSERVED AT TRANSPORT LEVEL ONLY. Not D007, not D009, not Steward-accepted. Basis: Steward's chat words "apply RC05c", dev fast path.

## Executed by the Steward in the hPanel Web console as root on srv1536619 (pasted output; not re-run by Claude Code)
- Commit 2ef2a169c24b1a536880628662f06ac5cfe83f1a checked out: COMMIT_OK. install_patch.sh sha256 on the box c2ee1f8e8249979bed55ba47cdc40d51adfe92ca567cd74974d45a879605204c (equals the filed script).
- install_patch.sh with the RC05c patch (sha256 83de7a4551dd79c0dcdc59caae9ac60fe464317b234ef0f5e021cf3c67155195): patch hash ok; PRESTATE_OK (tree hash 46df7bc09f15003840431f46dcf3495eb4512556a052c0be0eee4a718e39bd8a, the RC05b state); BACKUP_OK /root/rc05c/rollback_synapsys; APPLIED (scaffold_view.py, controllers/lenses.py); PARSES_OK; POSTSTATE_OK (tree hash f963b951fc1706c25983e1e2bd6fbd39c60b60073dd48edca9dc3d9c9ebb291e, 54 files, computed offline before install); docker restart odoo20-odoo-1; after 45 s the log-error section was empty; GET /web/login 200; anonymous POSTs to /synapsys/scaffold/context and /synapsys/scaffold/view returned 200 with "Odoo Session Expired" (routes registered, anonymous refused). INSTALL_DONE.
## Independent readback by Claude Code (read-only V20 connector, after the restart)
synapsys installed 20.0.2.4.9, write_date 2026-11-25 14:43:36 (unchanged: no module upgrade); synapsys_mesh installed 20.0.0.7.0.
## NOT observed
The visual result: Lenses card spacing and the scaffold view's open-questions lists after RC05c (screenshots requested), 390 px and 1024 px layouts (not tested), D15 left-gap cause, D16 depth-bar behaviour on list screens, Collaborator/portal behaviour (Option A, not served), D6.
## Rollback
cd /opt/odoo20/addons && patch -R -E -p1 < /root/rc04g_run/sob/release/rc05_scaffold_lens/RC05c_scaffold_polish_vs_RC05b_installed.patch && docker restart odoo20-odoo-1. No database change.
## ONE NEXT
Steward sends two screenshots after a hard reload: Lenses level 1 and the scaffold view at Enrich.
