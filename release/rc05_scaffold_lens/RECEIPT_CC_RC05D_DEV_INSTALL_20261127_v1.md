# RECEIPT: RC05d evidence source (SP-01) and spacing fix, dev install on Hostinger V20 (27 Nov 2026)
Work Object WO-SYNAPSYS-CANONICAL-REFERENCE-ARCHITECTURE-001 | CTX-SS | Status: INSTALLED ON DEV (restart only), OBSERVED AT TRANSPORT LEVEL ONLY. Not D007, not D009, not Steward acceptance. Basis: Steward's chat words "keep SP-01" (binding confirmed) and the Steward running the install commands (dev fast path).

## Executed by the Steward in the hPanel Web console as root on srv1536619 (pasted output; not re-run by Claude Code)
- Commit c595407206db69f7028c8212d8195af47b490c0e checked out: COMMIT_OK. install_patch.sh sha256 on the box c2ee1f8e8249979bed55ba47cdc40d51adfe92ca567cd74974d45a879605204c (equals the filed script).
- install_patch.sh with RC05d_evidence_sp01_vs_RC05c_installed.patch (sha256 51d8fc4cc43e0d9def5635e466474bc40fee2a4ec2f10275cc2bd2be01ff3c47): patch hash ok; PRESTATE_OK (tree hash f963b951fc1706c25983e1e2bd6fbd39c60b60073dd48edca9dc3d9c9ebb291e, the RC05c state); BACKUP_OK /root/rc05d/rollback_synapsys; APPLIED (scaffold_lens.py, scaffold_wire.py, scaffold_view.py, controllers/lenses.py); PARSES_OK; POSTSTATE_OK (tree hash 5422298f65c9e0654c4248d93a3d7b277c5b43993cab797ce1cb77242f942ef6, 54 files, computed offline before install); docker restart odoo20-odoo-1; after 45 s the log-error section was empty; GET /web/login 200; anonymous POSTs to /synapsys/scaffold/context and /synapsys/scaffold/view returned 200 "Odoo Session Expired" (registered, anonymous refused). INSTALL_DONE.
## Independent readback by Claude Code (read-only V20 connector, after the restart)
synapsys installed 20.0.2.4.9, write_date 2026-11-25 14:43:36 (unchanged: no module upgrade); synapsys_mesh installed 20.0.0.7.0. The bound catalogue record SP-01 was read earlier the same day (x_service_catalogue id 4, 4 records in the model) and its pinned hash 608938cd...17c was computed from those live values; it was not re-read after the install.
## NOT observed
The rendered result: the Service peer's "CATALOGUE RECORD FOUND" block and qualifications, whether the Steward login can read x_service_catalogue under real ACLs (an AccessError would show HOLD plus a note), the Lenses spacing fix, 390 px and 1024 px layouts, Collaborator/portal behaviour (Option A: not served). SP-01 as the right record for N.SERVICE remains a Claude Code inference confirmed by the Steward in chat, not a D001/D007 ruling.
## Rollback
cd /opt/odoo20/addons && patch -R -E -p1 < /root/rc04g_run/sob/release/rc05_scaffold_lens/RC05d_evidence_sp01_vs_RC05c_installed.patch && docker restart odoo20-odoo-1. No database change.
## ONE NEXT
Steward sends two screenshots as admin after a hard reload: Lenses level 1, and the scaffold view at Enrich.
