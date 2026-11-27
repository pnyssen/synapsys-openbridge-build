# RETURN: RC06e batch 4, nine action screens sourced from document rows, source-only candidate (claude_code), 27 Nov 2026
Work Object WO-SYNAPSYS-CANONICAL-REFERENCE-ARCHITECTURE-001 | CTX-SS | CANDIDATE | NON_AUTHORISING
Contract: BUILD_CONTRACT_ENABLE_ACTION_SCREENS_BATCH4_RC06E_20261127_v1.md, sha256 743e92bb0eb588a3a28b4fddf6f0d52211e7485e6dcbbc10e7c4c5a7e481b9d6 (read with sp_read_bytes, hash matched; the decoded copy used for parsing was hash-checked again).
Evidence state: offline tests run and passing; live tests: none. Authority: none conferred. Implementation: source built, NOT installed. PPV: no movement. Filed status: new file only.
Steward instruction carried: Context stays unchanged (D7 not approved).

## Consumed base state and hash (verified before any change or push)
- Branch claude/synapsys-v20-release-service-tvjpyn, HEAD 6f5f4d9 (RC06d, batch 3), equal to origin; no later commit; working tree clean.
- Addon tree release/rc06a_screen_architecture/addon/synapsys: 62 files, tree hash 8e6e4e50120b3a8338989ff84e25b601b58542d7512022ead2e180d3a1ca38c6 with rc04g_baseline_hash_20261126_v3.sh. EQUAL to the value given.
- Unchanged from 6f5f4d9 (git diff clean, and pinned by tests): the RC06a to RC06d declaration files, the batch 3 source table, screen_render.py, scaffold_wire.py, all Context goldens.

## What was built
- Nine screens in a new sibling file data/screen_declarations_batch4.json, ids SCR.ACTION.ORIENT, CANONICALISE, STRUCTURE, ASSURE, NAVIGATE, COMPOSE, ACTIVATE, TRANSFORM, PROJECT. Each is a menu screen (the batch 3 type): no registry or catalogue read, no stage, verbs empty (HOLD), no peers. Where each will sit in a menu is not decided and nothing is bound (batch 5, Steward).
- Source table data/screen_sources_batch4.json: the 15 rows A1 to A9, P1 to P3, C1 to C3, parsed by tools/gen_batch4_sources.py from the contract text (never retyped); a test reproduces it byte for byte from a hash-checked copy of the contract in tests/fixtures, and checks each quote against the contract's table line. Every row is shown verbatim (no mechanical edit was needed).
- Per screen, as the contract says: the answer line is its own A row; Made of (Enhance) lists its plane row only (P1 for A1 to A3, P2 for A4 to A6, P3 for A7 to A9); the Enrich trust table has its A row, its plane row, C1, C2, C3; chips are one per row (short source name plus the row's own "when"); status is the row's own word (A, P, C1 and C3 are CANDIDATE with their notes; C2 is OPEN). The two open questions on every screen are the fixed contract text "Definition: UNSOURCED. No project document states what this action means." and C2. Transform adds nothing beyond C2. The verbs inside an A row are source text only: no verb is bound, selectable, linked or counted, and the movement line stays "HOLD ... verbs not yet bound".
- Schema extension (smallest, reported): one new open-item kind "unsourced" carrying fixed contract text instead of a source row; the text must be listed in the file's contract_text, like the other contract wording. This touches screen_decl.py only (validator, loader check, open-text builder, the declaration list). The renderer and the wire are untouched: scaffold_menu serves all nine as it served batch 3.

## Diff and file list
Patch against the RC06d tree: RC06e_batch4_action_screens_vs_RC06d.patch, sha256 65dc4c0ca8db80073116ddbe4fe8040660ff4bbc49eb4055f67ae2f65bba8990 (cd /opt/odoo20/addons && patch -p1). Applied and reversed offline on a clean RC06d tree: forward f1f3707d..., reverse 8e6e4e50....
| File (under addon/synapsys) | Expected | Actual | sha256 |
|---|---|---|---|
| data/screen_declarations_batch4.json | new | new | ab487f8647114cd3eeb434793112a50d28f835d95b1d5f7bda858e63c07fd387 |
| data/screen_sources_batch4.json | new | new | 3957e18430502fe57a1e27904145907e5c3c95b9e93524d7f06ad1b6263b4425 |
| screen_decl.py | changed | changed | ef0714d18434cab5f579153cd1cd1f0e85cce1bfb399b874e0333f07434eedce |
| the other 61 files | unchanged | unchanged | n/a |
New tree: 64 files, tree hash **f1f3707d095f6c2ad53b6c4e1ed4212dbbd5068eb9e9ee6417f2ccb4d47460d6** (the repo's tree-hash method). Not installed anywhere. Outside the addon: tools/gen_batch4_sources.py, tools/gen_batch4_declarations.py, tests/test_batch4.py, tests/fixtures (the contract copy), the offline log.

## Offline tests run versus live tests not run
Run: 174 tests, all pass (log tests/TEST_LOG_rc06e_batch4_offline.txt, sha256 9f4122d07add881c511c31e34e1ca94d04bef1f7cb695d92da8c6dd684b78f4f): 63 test_screen_arch + 3 test_ui_script + 30 test_batch1 + 25 test_batch2 + 31 test_batch3 + 22 new test_batch4. Acceptance checks 1 to 17 run over all 46 declarations (the 46 the contract expects).
New tests: nine screens exist, each with exactly its A row and its plane row, and no screen shows another action's A row or plane row; each quote reproduces from the contract table byte for byte; both generators reproduce their files byte for byte; status follows the row (CANDIDATE with note, OPEN for C2, nothing RULED, a changed row changes the screen); C2 is an open item on all nine and "UNSOURCED" appears on all nine; exactly two open questions per screen; Transform adds nothing beyond C2; the fixed text must be listed in contract_text; no verb bound, selectable, linked or counted; no wording outside the source rows and the fixed contract text; no definition, purpose, example or peer text; the earlier declaration files, batch 3 sources, goldens and registry are pinned; no route, menu placement or manifest change.
One edit to an earlier test, not weakening: batch 3's count of declarations now excludes the nine action screens (the total is asserted at 46 in test_batch4).
Mutation checks, 9 faults, each made tests fail: a definition invented (2 failures), an A row swapped between screens (4 plus 1 error), a status hardcoded RULED (5 plus 2 errors), a verb bound (2 plus 5 errors), C2 dropped from a screen (2), a wrong plane row (3), a source quote altered (2), the batch 3 file touched (2), the answer lead removed (1 plus 2 errors).
NOT run: live tests, install, browser render, the RC06a TransactionCase file, the UI script against dev. Real-size layout remains UNOBSERVED. The 15 quotes could not be checked against the project documents (the builder cannot read them); D009 or the Navigator should re-check them, as the contract says.

## Per screen
| Screen | A row (answer) | Plane row | Rows in the trust table | Chips kept / dropped | Open questions |
|---|---|---|---|---|---|
| Orient | A1 | P1 | A1, P1, C1, C2, C3 | 5 / 0 | definition (fixed text), C2 |
| Canonicalise | A2 | P1 | A2, P1, C1, C2, C3 | 5 / 0 | same two |
| Structure | A3 | P1 | A3, P1, C1, C2, C3 | 5 / 0 | same two |
| Assure | A4 | P2 | A4, P2, C1, C2, C3 | 5 / 0 | same two |
| Navigate | A5 | P2 | A5, P2, C1, C2, C3 | 5 / 0 | same two |
| Compose | A6 | P2 | A6, P2, C1, C2, C3 | 5 / 0 | same two |
| Activate | A7 | P3 | A7, P3, C1, C2, C3 | 5 / 0 | same two |
| Transform | A8 | P3 | A8, P3, C1, C2, C3 | 5 / 0 | same two (nothing added beyond C2) |
| Project | A9 | P3 | A9, P3, C1, C2, C3 | 5 / 0 | same two |
Every screen reads "No linked peers are declared for this screen." in the peers slot. Each answer line leads with "CANDIDATE:" (its row's status, the RC06c rule), and the trust line reads "CANDIDATE 1 source" (the answer row's own).

## Findings and choices to review (mine, not rulings)
1. "UNSOURCED" appears at Enrich only (inside the open question), not on the Enable or Enhance view. The contract says it "appears on all nine"; I read that as on every screen, at the depth where open questions live. If it should be visible at Enable (for example next to the answer), that is a renderer change and a Steward word.
2. The answer line shows an A row as the source writes it, including the verbs in its parenthesis (for example "Orient (sense, map, derive)"). That is source text, as the contract says, but a reader may take it as the verbs this action binds. Movement says HOLD on the same screen.
3. The contract's "same" notes (A2 to A9) and "same file s1" (A2 to A9, P1 to P3, C1) are resolved to A1's note and A1's file string. That is how I read the table; it is mechanical and tested.
4. Source short names ("Mesh fit-to-shapes test v0.3 s1", "Toolkit verbs rules v0.1 s1") are authored by me, one per file string.
5. C2 is both a claim row and an open item, so in the open-question roll-up its text appears as the row's label and again as the question (the same as S11 and S13 in batch 3). Each question appears once as a question. I did not change the renderer for this.
6. The definition question's one-line stem in the trust-table cell reads "Definition… (1 open)" because stems are cut at the first colon; the full text is in the roll-up.
7. The HOLD reason ("noun-to-verb governance waits on the Architecture tab") is carried from the earlier batches; the contract only says verbs HOLD. Titles are the first word of each A row ("Orient", "Canonicalise", and so on).
8. Rows C1 ("they are not verbs") and C3 ("none named Form, Flow or Evolve") are shown on every screen as trust-table rows, in the rows' own words, as the contract lists them.

## Rights and gaps
Rights: no registry read, no catalogue read, no sudo, no write, no raw SQL; scaffold_menu reads nothing from the environment but the caller's groups (tested). Nothing written to dev or V20. Registry 0.3.5 unchanged. Not touched: menus, routes, install, verb binding, Architecture register, Lexicon, Context.
Gaps: never rendered in a browser; no live run; the patch assumes RC06a to RC06d are installed first (none is). With this batch the declarations cover 46 screens: Context noun and record, Asset record, 15 RULED nouns, 12 PROPOSAL/OPEN nouns, 7 menu screens and these 9 action screens.

## Dissent
None against the rulings. One observation: all nine action screens say, at Enrich, that no document defines the action, while their answer line is the verb list from a live V20 read. The two statements are both in the sources; the screen cannot say which a Steward would rely on.

## Delivered versus Realised
Delivered: nine declarations, the action source table, the one-kind schema extension, 174 passing offline tests, patch and hashes, this return. Realised: UNOBSERVED until the Steward accepts on dev; nothing is installed.

## Release path (not authorised here)
Needs a fresh Steward word and the dev fast path (backup, verified transfer, upgrade, restart, read-back, rollback patch recorded). RC06a to RC06e would install together, since each is built on the uninstalled tree before it; reversing the five patches restores RC05e (15c37960...).

## ONE NEXT
Owner: Steward. Say whether findings 1 and 2 are acceptable (where UNSOURCED shows, and the verbs inside an A row); have D009 or the Navigator re-check the 15 quotes; then say whether RC06a to RC06e go to the dev fast path or batch 5 (menu placement, Steward) is taken first. The Context date edit (D7) stays unapproved and unapplied.
