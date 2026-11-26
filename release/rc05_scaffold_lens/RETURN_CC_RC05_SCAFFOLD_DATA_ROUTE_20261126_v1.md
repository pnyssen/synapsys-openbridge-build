# RETURN: Claude Code, RC05 scaffold data route (source-ready delta against the verified live RC04g tree)
Work Object WO-SYNAPSYS-CANONICAL-REFERENCE-ARCHITECTURE-001 | CTX-SS | 26 Nov 2026 | Status: CANDIDATE. SOURCE-READY for the data route only. Not installed, not D007, not D009, not Steward-accepted. Nothing on V20 changed. Supersedes the "projection core only" state in RETURN_CC_RC05_SCAFFOLD_LENS_SLICE_20261126_v1.md (sha256 a6723aaf...).

## State ladder
| Level | State |
|---|---|
| Source-ready | YES for one read-only JSON route /synapsys/scaffold/context (N.CONTEXT, H.CTX roles, N.CAPABILITY and N.SERVICE peers, Enable/Enhance/Enrich). NOT the Architecture > Lenses screen, NOT 390/1024 layout. |
| Installed | NO |
| Observed with real actors | NO. Offline fake-Odoo tests only. No Collaborator login exists; the connector identity is read-only. |
| Independently challenged | NO |
| Steward-accepted | NO |

## Base (proved, not assumed)
Live /opt/odoo20/addons/synapsys on srv1536619, tree hash 82e69741dda90f830726e6119a9013faa50382b58b8c05e4518fef44eb36b104 (50 files, recomputed from the pasted list; see RETURN_CC_RC04G_BASELINE_VERIFIED_20261126_v1.md sha256 818d3ba1...). Byte-exact copies of the live lens_contract.py (c101592a...), controllers/lenses.py (47db8392...) and static/src/home.xml (03b40742...) were transferred as base64 and verified against those hashes. The live controllers/__init__.py is exactly the three lines "from . import home / arch_map / lenses" (its sha256 begins 5ebbe7c4a3a3a7f9, equal to the live value).
The RC04g patch bytes (sha256 47e19de8726fa37953d8a42a96b2221b1e94c7b4e3491d12b4feb19ed8bed9d9, verified on the box via zcat) were NOT transcribed byte-exactly; a chat-pasted copy hashed differently (tabs lost). The base64 copy was supplied but not transcribed; the patch is therefore not filed here.

## Delta (RC05_scaffold_data_route_vs_RC04g_live.patch.txt, 10,758 B, sha256 0ac83247f979a9479f8c7e7826295a21f73e620973ca6a15dadc80b4f9e62dad)
Applies with patch -p1 to the live synapsys tree (dry run and real apply verified on a tree holding the exact live controllers/__init__.py). Adds: synapsys/scaffold_lens.py (f50f7b2b...), synapsys/scaffold_wire.py (10c21eef...), synapsys/controllers/scaffold.py (46ebf74f...); changes controllers/__init__.py by one added line "from . import scaffold". No manifest, view, model, ACL or data change; no schema; no new Service. The route is auth='user', reads with request.env (the caller's own rights): no sudo, no with_user, no writes, no raw SQL (source scan test).

## Behaviour (as tested)
Registry read with the caller's rights; refuses if the caller lacks the read right (no fallback); checks sha256(body) equals the stored sha; Steward may reach Enrich, Collaborator is capped at Enhance (conservative DEFAULT, a proposal, not a ruling); caller with neither group is refused before any read; no library or evidence source is passed because none is registered in V20 (SC-04 test_state PENDING, version_state VERSION_BINDING_REQUIRED; synapsys.service/method not reader-visible), so both peers show NO_OPERATING_SOURCE with HOLD. The incorrect-source and foreign-Context negatives are tested in the core with fixture sources (SOURCE_HASH_MISMATCH, SOURCE_NOT_FOUND, FOREIGN_CONTEXT, ACTOR_NOT_IN_CONTEXT).

## Tests (offline, sandbox python, no Odoo): 27/27 pass
16 core (tests/test_scaffold_lens.py a1567fa2...) and 11 wiring (tests/test_scaffold_wire.py c41fa16b...). 8 mutation controls (core: no Context check, no hash check, no group gate, fail-open unknown actor; wiring: no body-hash check, sudo, collaborator Enrich, swallowed AccessError) each fail at least one test. Git: pnyssen/synapsys-openbridge-build, branch claude/synapsys-v20-release-service-tvjpyn, release/rc05_scaffold_lens/.

## NOT done / limits
- No Odoo ran any of this: route registration, jsonrpc encoding, group xmlids (synapsys.group_synapsys_steward / synapsys.group_synapsys_user taken from the RC03b security file in git, not from the live file), real AccessError behaviour and the registry search under real ACLs are UNTESTED.
- Context membership is not modelled (context_ids empty): the model that maps a user to a Context was not read. The core's Context filters are tested only with fixtures.
- No UI: the Architecture > Lenses screen, depth bar placement (D3), 390px/1024px, navigation. lens_render.py and home.js were not transferred.
- Rights: who sees Enrich, and R1/D6 (sudo reads and the open /synapsys/lenses/data route in the existing code) are unchanged by this delta; this delta does not fix them, it only avoids repeating them.
- Release to dev needs D007 (exact prestate = tree hash above, rollback copy, backup, readback), then actor tests with a Steward-created dev-only Collaborator login.

## ONE NEXT
Owner Steward/D007: authorise a dev install of this patch (restart only, no module upgrade needed) or say what else is required; and create the dev-only Collaborator login. Claude Code then provides the exact apply, readback and rollback commands pinned to the tree hash 82e69741..., and Cowork runs the Steward and Collaborator route tests plus the denial checks.
