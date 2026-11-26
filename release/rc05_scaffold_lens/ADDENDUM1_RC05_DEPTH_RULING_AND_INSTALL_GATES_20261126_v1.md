# ADDENDUM 1 to RETURN_CC_RC05_SCAFFOLD_DATA_ROUTE_20261126_v1.md (sha256 519bc1f1...)
Work Object WO-SYNAPSYS-CANONICAL-REFERENCE-ARCHITECTURE-001 | CTX-SS | 26 Nov 2026 | Status: CANDIDATE, source-ready, NOT installed. Supersedes the patch in the parent return (sha256 0ac83247...) and its Collaborator-at-Enhance default.

## Steward words received in this thread (chat, 26 Nov 2026; not a filed decision, not D007/D009)
1. Authorised the dev install of the RC05 data-route patch.
2. Yes to a dev-only Collaborator test login (to be created by the Steward).
3. Collaborators are limited to their Context but can act to enrich: Collaborator depth cap lifted to Enrich.
This is the dev fast path on the Steward's word only. No D007 release, no D009 challenge, no CHG is claimed.

## Change
scaffold_wire.DEFAULT_ROLE_MAX_DEPTH collaborator: enhance -> enrich. Context-bound evidence stays gated by Context membership in scaffold_lens (fail-closed). Offline tests 27/27; 8 mutation controls fail as intended (collaborator-capped mutant now fails W2).
New patch: RC05_scaffold_data_route_vs_RC04g_live_v2.patch.txt, 10,869 B, sha256 6b8b80a90a2a7217d170f7ac91e33d76dde19e937751dcbeea598fd391db0d7d. Dry run, apply and reverse (patch -R -E) verified on a tree holding the exact live controllers/__init__.py: reverse restores it and removes the three added files.

## Install gates (pinned)
Prestate: /opt/odoo20/addons/synapsys tree hash 82e69741dda90f830726e6119a9013faa50382b58b8c05e4518fef44eb36b104, 50 files, manifest 20.0.2.4.9.
Poststate expected (computed offline from the verified live file list plus the four changed or added files): 53 files, tree hash c06edf7172a52e3540b61d136b9f5145571dd7643816377369374962cb8bafcb. New file prefixes: controllers/__init__.py d637d4c0b927..., controllers/scaffold.py 46ebf74fc60a..., scaffold_lens.py f50f7b2b3f4, scaffold_wire.py 6c3cf5620bc4.
No schema, ACL, data or manifest change; restart only, no module upgrade. Rollback: reverse the patch, or restore the rollback copy; restart.

## Still NOT established after install
Route behaviour in a real Odoo (registration, rights, group ids), Steward and Collaborator actor tests, denial checks, 390px/1024px (no UI exists), D6 in the existing routes.
