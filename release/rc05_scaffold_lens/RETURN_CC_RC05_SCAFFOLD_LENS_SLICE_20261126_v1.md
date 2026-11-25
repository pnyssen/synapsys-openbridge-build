# RETURN: Claude Code, RC05 scaffold lens slice (projection core only)
Work Object WO-SYNAPSYS-CANONICAL-REFERENCE-ARCHITECTURE-001 | CTX-SS | Status: CANDIDATE, SOURCE-READY FOR THE PROJECTION CORE ONLY. Not installed, not integrated, not D007/D009, not Steward-accepted. Nothing on V20 changed.

## State ladder (honest)
| Level | State |
|---|---|
| Source-ready | PARTIAL: pure projection core + 16 offline tests. NOT the UI, controller or lens_contract integration. |
| Installed | NO (nothing deployed; live synapsys 20.0.2.4.9 / synapsys_mesh 20.0.0.7.0 read back this session, unchanged by me). |
| Observed (actor tests) | NO real actor ran. Offline fixtures only (steward / collaborator / collaborator-outside-Context / client / unknown). |
| 390px / 1024px, navigation | NOT RUN (no browser, no restricted login in this lane). |
| Independently challenged | NO. |
| Steward-accepted | NO. |

## Identity (recomputed)
- Registry baseline: git blob 7086338bcce8eac1601c154d07f6b52b753fd8ad, sha256 7c31aa1de4c97e8e062c5ae9e2f907b4c67ea0949bf143235499c32b1a30f423; 361 elements, 196 clusters, matches the Navigator's stated hashes (read from pnyssen/synapsys-odoo v20-dev).
- src/scaffold_lens.py sha256 e38c974b8cea54cb79ab7214b322d403cefd459903acaa0aaf7d01975df77fb5
- tests/test_scaffold_lens.py sha256 a1567fa29a5a0457d9a67f4afbc274bb9fd66a4fce8f711f7f6576f81da51065
- Repo pnyssen/synapsys-openbridge-build, branch claude/synapsys-v20-release-service-tvjpyn, commit 8ddd7304a317b5787706d239980bb158a7312ccd, path release/rc05_scaffold_lens/.

## What the core does (reuses the registry; no new ontology/table/Service)
N.CONTEXT with H.CTX roles read from cluster MC-390147223f2d (7 role bindings, 3 required, human labels from R.* elements); N.CAPABILITY (PROPOSAL) and N.SERVICE (RULED) as peers, each SOURCED only when a library record resolves with matching sha256 in the actor's own Context, else NO_OPERATING_SOURCE + HOLD; Enable/Enhance/Enrich cumulative; filtering happens before data is returned; rejected evidence returns only a reason code (no ids/bodies).

## Tests (16/16 pass, log tests/TEST_LOG_scaffold_lens.txt)
Positive: registry identity, H.CTX roles, depth rules, valid library source. Negatives: wrong source hash, unknown source, foreign Context, collaborator outside the Context, client clamped to Enhance with no evidence, unknown actor refused, no mutation / no sudo / no write calls (source scan). Mutation controls: 4 mutants (no Context check, no hash check, no group gate, fail-open unknown actor) each fail at least one test. A first version of the group-gate mutant was syntactically broken and wrongly looked like a surviving mutant; fixed and re-run, now detected.

## NOT done and why
1. Integration into lens_contract.py / controllers / home.xml: the installed RC04f/g source and RC04h patch bytes are not in git or Working Memory (only hashes in returns). A delta against an unseen base would be a guess. Needed: the installed synapsys tree (or rc04f/g/h patches) filed to WM.
2. Rights policy (who may see Enrich, evidence) is a parameter here (ROLE_MAX_DEPTH, EVIDENCE_GROUPS), a proposal. Not a ruling; Steward/D001 decide.
3. The evidence/library_index inputs need a real source: the one source-bound library relationship is a fixture (SC-04 label) until a registered SC-04/GV-NAV-002 Method and an authoritative library record are named. SC-04 reports test_state PENDING, version_state VERSION_BINDING_REQUIRED; V20 synapsys.service / synapsys.method are not reader-visible. No Service registered by this work.
4. Live D6 risk persists in the installed code: /synapsys/lenses/data requires only a logged-in user and the map reads use sudo (builder-reported, code-read, not observed by me).

## Defects/risks carried
D3-D7, D8-D12 from the RC04 returns unchanged; static risk flags on synapsys_mesh registry.py (load_body sudo, release_ref check) unchanged.

## ONE NEXT
Owner: RC04 builder lane or Steward. File the installed synapsys tree (or rc04f/g/h patches) to Working Memory, then I produce one exact delta wiring this core into lens_contract and the lens route with the real actor (no sudo), and Cowork runs the 390/1024 and Collaborator tests on a Steward-created dev Collaborator login.
