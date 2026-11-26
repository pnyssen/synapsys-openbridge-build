# RECEIPT: RC05 scaffold data route, dev install on Hostinger V20 (26 Nov 2026)
Work Object WO-SYNAPSYS-CANONICAL-REFERENCE-ARCHITECTURE-001 | CTX-SS | Status: INSTALLED ON DEV (restart only), OBSERVED AT TRANSPORT LEVEL ONLY. Not D007, not D009, not Steward-accepted. Basis: Steward's chat words ("1 authorised"), dev fast path.

## Executed by the Steward in an SSH session as root on srv1536619 (pasted output, not independently re-run by Claude Code)
- Commit 5d7353dc3085e4026e5355702a4f4916a2ef7722 checked out (COMMIT_OK). Patch sha256 6b8b80a90a2a7217d170f7ac91e33d76dde19e937751dcbeea598fd391db0d7d on the box (equals the filed v2 patch).
- Prestate gate PRESTATE_OK: tree hash 82e69741dda90f830726e6119a9013faa50382b58b8c05e4518fef44eb36b104 (v3 baseline script, filed copy hash fe9e401c...).
- Rollback copy /root/rc05/rollback_synapsys taken before the change. patch -p1 dry run clean, applied (4 files: controllers/__init__.py, controllers/scaffold.py, scaffold_lens.py, scaffold_wire.py); the three Python files parse.
- Poststate gate POSTSTATE_OK: tree hash c06edf7172a52e3540b61d136b9f5145571dd7643816377369374962cb8bafcb (computed offline before install; matches).
- docker restart odoo20-odoo-1; after 45 s: no traceback/critical/importerror/syntaxerror lines in the last 2 minutes of the container log; GET /web/login returned 200; an anonymous POST to /synapsys/scaffold/context returned HTTP 200 with a JSON-RPC "Odoo Session Expired" error. The route is therefore registered and refuses an anonymous caller.

## Independent readback by Claude Code via the read-only V20 connector (after the restart)
synapsys installed, latest_version 20.0.2.4.9, write_date 2026-11-25 14:43:36 (unchanged: no module upgrade ran); synapsys_mesh installed 20.0.0.7.0; synapsys.mesh.registry id 1, version 0.3.5, sha 7c31aa1de4c97e8e062c5ae9e2f907b4c67ea0949bf143235499c32b1a30f423, state candidate, ppv potential (unchanged).

## NOT observed
Authenticated behaviour: no Steward or Collaborator call to the route has been made; group ids synapsys.group_synapsys_steward / synapsys.group_synapsys_user, real AccessError behaviour and the registry read under real ACLs are untested in a running Odoo. No UI. No 390/1024 checks. No Collaborator login yet. D6 in the existing routes is unchanged.

## Rollback
cd /opt/odoo20/addons && patch -R -E -p1 < RC05_scaffold_data_route_vs_RC04g_live.patch && docker restart odoo20-odoo-1 (fallback: restore /root/rc05/rollback_synapsys). The Postgres database was not touched; no dump was taken because no schema or data changed.

## ONE NEXT
Steward creates the dev-only Collaborator login (group SynapSys / Collaborator only) and a Steward session; Cowork runs the route tests Claude Code supplies (Steward Enrich, Collaborator Enrich, no-role denial, depth parameter validation, registry-right denial) and returns raw JSON.
