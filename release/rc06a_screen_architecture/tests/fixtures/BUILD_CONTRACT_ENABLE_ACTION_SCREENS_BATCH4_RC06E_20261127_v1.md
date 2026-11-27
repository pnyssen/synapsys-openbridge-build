# BUILD CONTRACT: Enable content for the nine action screens, batch 4 (RC06e), 27 Nov 2026
Work Object WO-SYNAPSYS-CANONICAL-REFERENCE-ARCHITECTURE-001 | CTX-SS | CANDIDATE | NON_AUTHORISING | author: Claude (chat lane) | builder: Claude Code | source-only, offline tests, no install.

## Base (verify first; STOP and report if anything differs)
- Repo pnyssen/synapsys-openbridge-build, branch claude/synapsys-v20-release-service-tvjpyn, HEAD 6f5f4d9 (RC06d, batch 3), tree release/rc06a_screen_architecture/addon/synapsys: 62 files, tree hash 8e6e4e50120b3a8338989ff84e25b601b58542d7512022ead2e180d3a1ca38c6 (release/rc04g_baseline/rc04g_baseline_hash_20261126_v3.sh). Push only after this matches.
- Method: exactly batch 3's (BUILD_CONTRACT_ENABLE_DOC_SOURCED_SCREENS_BATCH3_RC06D_20261127_v1.md, sha256 85d9e13712bafa656e542ac564d0f9b877d57373c3508325e29941cf621b4b9c): screen_type "menu", source table parsed from THIS contract's table by a generator (never retyped), a hash-checked copy of this contract in tests/fixtures, new sibling files data/screen_declarations_batch4.json and data/screen_sources_batch4.json, no registry or catalogue read, no stage, verbs HOLD, no peers, one renderer. Reuse the batch 3 schema and wire (scaffold_menu); add the smallest change only if a screen cannot be declared with it, and report it.
- Not to be touched: Context (frozen; D7 date edit NOT approved), every earlier declaration and golden, registry 0.3.5, menus, routes, install, verb binding, Architecture register, Lexicon.

## Scope: nine screens, one per operating action
Orient, Canonicalise, Structure | Assure, Navigate, Compose | Activate, Transform, Project. Each screen is a menu screen under its own id (SCR.ACTION.ORIENT and so on). Where it will sit in a menu is NOT decided (batch 5, Steward).

## Source table (exact quotes; the builder cannot read the documents, the chat lane read them on 27 Nov; D009 or the Navigator should re-check)
Columns: id | file | when | status | note | quote. Status is the row's own word. Quotes are substrings copied verbatim from the files.

| id | file | when | status | note | quote |
|---|---|---|---|---|---|
| A1 | claude/mesh-fit-to-shapes-test-v0.3-verbs-verified-and-product-in-disciplines-2026-11-25.md s1 | 25 Nov | CANDIDATE | read from live V20 synapsys.verb on 25 Nov | Orient (sense, map, derive) |
| A2 | same file s1 | 25 Nov | CANDIDATE | same | Canonicalise (capture, supersedes, validates) |
| A3 | same file s1 | 25 Nov | CANDIDATE | same | Structure (instantiates, composes, parent) |
| A4 | same file s1 | 25 Nov | CANDIDATE | same | Assure (evidences, challenge, verify) |
| A5 | same file s1 | 25 Nov | CANDIDATE | same | Navigate (route, balance, filter) |
| A6 | same file s1 | 25 Nov | CANDIDATE | same | Compose (consumes, execute, requires) |
| A7 | same file s1 | 25 Nov | CANDIDATE | same | Activate (engage, commit, seize) |
| A8 | same file s1 | 25 Nov | CANDIDATE | same | Transform (compound, succeed, transform) |
| A9 | same file s1 | 25 Nov | CANDIDATE | same | Project (join, package, implements_candidate) |
| P1 | same file s1 | 25 Nov | CANDIDATE | plane of A1 to A3 | Govern plane (Form) |
| P2 | same file s1 | 25 Nov | CANDIDATE | plane of A4 to A6 | Deliver plane (Flow) |
| P3 | same file s1 | 25 Nov | CANDIDATE | plane of A7 to A9 | Realise plane (Evolve) |
| C1 | same file s1 | 25 Nov | CANDIDATE | not verbs | Form, Flow and Evolve are the three stages (planes) that group the verbs, and the Movement values of the Control Cube; they are not verbs. |
| C2 | claude/synapsys-toolkit-verbs-rules-intelligence-and-adaptability-by-level-v0.1-2026-11-13.md s1 | 13 Nov | OPEN | relation to the 27 unruled | Its relation to the 27 is unruled, and "transform" is in both sets. |
| C3 | claude/mesh-fit-to-shapes-test-v0.3-verbs-verified-and-product-in-disciplines-2026-11-25.md s1 | 25 Nov | CANDIDATE | live read | Live V20 `synapsys.verb` read 25 Nov: 27 rows, none named Form, Flow or Evolve. |

## Per-screen declaration (D1)
Each screen: answer line = its own A row (A1 to A9) verbatim; Made of (Enhance) lists its plane row (P1, P2 or P3) and nothing else; Enrich trust table rows = its A row, its P row, C1, C2, C3 (C2 and C3 on all nine). Chips: one per row, short source name plus the row's own "when". Status: the row's own word; an A or P row shows CANDIDATE and its note; C2 shows OPEN.
- Open questions on every screen, only these two, worded as the fixed contract text: "Definition: UNSOURCED. No project document states what this action means." and C2 as an open item (relation of the nine to the 27 unruled).
- Transform: add nothing beyond C2; the "transform" in both sets is already C2's own words. Do not resolve it.
- The verbs inside an A row are source text, not a binding: the movement line stays "HOLD: verbs not yet bound" (renderer wording as batch 3). No verb is made selectable, linked or counted.
- No definition, purpose, example, "what it does" or peer text of any kind may appear that is not a source row or the fixed contract text above. Definitions stay UNSOURCED.

## Tests (D2): same classes as batch 3, plus
Every shown text is a source row verbatim or fixed renderer/contract text; each quote reproduces from the contract table byte for byte; nine screens exist, each with exactly its A row and its plane row; no screen shows another action's A row; status follows the row; C2 appears as open on all nine; "UNSOURCED" appears on all nine; no verb bound; Context and all earlier files and goldens byte-identical to 6f5f4d9; both generators reproduce their files. Acceptance checks 1 to 17 over all declarations (46 expected). Add mutation checks: a definition invented, an A row swapped between screens, a status hardcoded RULED, a verb bound.

## Return (D3)
Write RETURN_CC_ENABLE_ACTION_SCREENS_BATCH4_RC06E_20261127_v1.md to 05_AI_RETURNS_HASHED/WO-SYNAPSYS-CANONICAL-REFERENCE-ARCHITECTURE-001/CANDIDATES/ (not the top-level CANDIDATES folder): consumed base hash, what was built, diff and file table (expected vs actual), offline vs live tests, new tree hash, patch against the RC06d tree, findings and choices to review, rights, dissent, Delivered vs Realised, ONE NEXT. Also commit and push the same files to the branch. Offline tests run; live tests NOT run; nothing installed.
