# RECEIPT: RC05e D16 ruling and plain-language copy, dev install on Hostinger V20 (27 Nov 2026)
Work Object WO-SYNAPSYS-CANONICAL-REFERENCE-ARCHITECTURE-001 | CTX-SS | Status: INSTALLED ON DEV (restart only), OBSERVED AT TRANSPORT LEVEL ONLY. Not D007, not D009, not Steward acceptance. Basis: Steward's chat words "approve D16 as proposed" and the Steward running the install commands (dev fast path).

## Executed by the Steward in the hPanel Web console as root on srv1536619 (pasted output; not re-run by Claude Code)
- Commit afbafd8199f610d33fca1f25fcbe9119a142a941 checked out: COMMIT_OK. install_patch.sh sha256 on the box c2ee1f8e8249979bed55ba47cdc40d51adfe92ca567cd74974d45a879605204c (equals the filed script).
- install_patch.sh with RC05e_D16_and_plain_copy_vs_RC05d_installed.patch (sha256 dd5cd95350e2e555592dc7bfb671860ba36d6f6e117cb781276a11e8ec3add7d): patch hash ok; PRESTATE_OK (tree hash 5422298f65c9e0654c4248d93a3d7b277c5b43993cab797ce1cb77242f942ef6, the RC05d state); BACKUP_OK /root/rc05e/rollback_synapsys; APPLIED (controllers/lenses.py, scaffold_view.py); PARSES_OK; POSTSTATE_OK (tree hash 15c37960d1707be2be9b1dbdf18e623d82c97f78f1b009e02af34e46a5837e4b, 54 files, computed offline before install); docker restart odoo20-odoo-1; after 45 s the log-error section was empty; GET /web/login 200; anonymous POSTs to /synapsys/scaffold/context and /synapsys/scaffold/view returned 200 "Odoo Session Expired". INSTALL_DONE.
## Independent readback by Claude Code (read-only V20 connector, after the restart)
synapsys installed 20.0.2.4.9, write_date 2026-11-25 14:43:36 (unchanged: no module upgrade); synapsys_mesh installed 20.0.0.7.0.
## NOT observed
The rendered result: level lines without stage words at levels 1 to 3, the list-screen note, plain role names, the Technical details area. Whether the live crumb format still matches the rule (a mismatch would leave the stage word in place, fail-safe). 390/1024 px (set aside by the Steward). Collaborator/portal behaviour (Option A). D6 open.
## Rollback
cd /opt/odoo20/addons && patch -R -E -p1 < /root/rc04g_run/sob/release/rc05_scaffold_lens/RC05e_D16_and_plain_copy_vs_RC05d_installed.patch && docker restart odoo20-odoo-1. No database change.
## ONE NEXT
Steward sends screenshots as admin after a hard reload: Lenses level 1 and level 2, and the scaffold view at Enrich with Technical details open.
