# RECEIPT: RC05b scaffold screen, dev install on Hostinger V20 (27 Nov 2026)
Work Object WO-SYNAPSYS-CANONICAL-REFERENCE-ARCHITECTURE-001 | CTX-SS | Status: INSTALLED ON DEV (restart only), OBSERVED AT TRANSPORT LEVEL ONLY. Not D007, not D009, not Steward-accepted. Basis: Steward's chat words "apply RC05b", dev fast path.

## Executed by the Steward in the hPanel Web console as root on srv1536619 (pasted output, not re-run by Claude Code)
- Block 1 (commit 6b836c6134f6596ac796d9ba592736aa6576e119 checkout, patch hash, prestate gate against tree hash c06edf71...bafcb): its output was NOT pasted into the thread, so COMMIT_OK, the patch hash on the box and PRESTATE_OK are NOT directly observed by Claude Code. The poststate result below is evidence the starting tree was the expected one.
- Block 2: rollback copy /root/rc05b/rollback_synapsys taken; patch RC05b_scaffold_screen_vs_RC05_installed.patch (sha256 d7f0956fe7165b9085864d5c2a8f25729c0895a1b3592fbd29120d538da3a893) dry run clean, applied to four files (controllers/lenses.py, controllers/scaffold.py, scaffold_view.py new, static/src/home.js); the three Python files parse. APPLIED_AND_PARSES.
- Block 3: poststate gate POSTSTATE_OK: tree hash 46df7bc09f15003840431f46dcf3495eb4512556a052c0be0eee4a718e39bd8a (54 files, computed offline before install; matches). docker restart odoo20-odoo-1; after 45 s no traceback/critical/importerror/syntaxerror lines in the last 2 minutes of the log; GET /web/login 200; anonymous POST to /synapsys/scaffold/context and /synapsys/scaffold/view each returned HTTP 200 with a JSON-RPC "Odoo Session Expired" error (both routes registered; anonymous refused).

## Independent readback by Claude Code via the read-only V20 connector
synapsys installed 20.0.2.4.9, write_date 2026-11-25 14:43:36 (unchanged: no module upgrade ran); synapsys_mesh installed 20.0.0.7.0.

## NOT observed
The screen itself: no browser check of the Lenses card, the depth bar behaviour, the view content, the back link, 390 px and 1024 px layouts, bundle regeneration, or the web client loading after the new home.js. A JavaScript error in this asset could blank the backend until rollback. Collaborator and portal behaviour (Option A: not served). D6 unchanged.

## Rollback
cd /opt/odoo20/addons && patch -R -E -p1 < RC05b_scaffold_screen_vs_RC05_installed.patch && docker restart odoo20-odoo-1 (fallback: restore /root/rc05b/rollback_synapsys). No database change was made.

## ONE NEXT
Steward runs the six acceptance checks in Chrome (hard reload; Lenses card; Enable/Enhance/Enrich; HOLD text; back link; 390/1024 px; no errors) and reports pass or fail per check with a screenshot of any failure.
