# RETURN: RC06d batch 3, seven menu screens sourced from project documents, source-only candidate (claude_code), 27 Nov 2026
Work Object WO-SYNAPSYS-CANONICAL-REFERENCE-ARCHITECTURE-001 | CTX-SS | CANDIDATE | NON_AUTHORISING
Contract: BUILD_CONTRACT_ENABLE_DOC_SOURCED_SCREENS_BATCH3_RC06D_20261127_v1.md, sha256 85d9e13712bafa656e542ac564d0f9b877d57373c3508325e29941cf621b4b9c (read with sp_read_bytes, hash matched; the decoded copy used for parsing was hash-checked again).
Evidence state: offline tests run and passing; live tests: none. Authority: none conferred. Implementation: source built, NOT installed. PPV: no movement. Filed status: new file only.
Steward instruction carried: the Context date edit (D7 of the batch 2 return) is NOT approved, so Context is unchanged.

## Consumed base state and hash (verified before any change or push)
- Branch claude/synapsys-v20-release-service-tvjpyn, HEAD 9919b67 (RC06c, batch 2), equal to origin; no later commit; working tree clean.
- Addon tree release/rc06a_screen_architecture/addon/synapsys: 60 files, tree hash 376d5386477779b8c447144070100d0113395033b90b7e2e0b64e2d622436c23 with rc04g_baseline_hash_20261126_v3.sh. EQUAL to the value given, and to the RC06c return's new tree hash.
- The RC06a, RC06b and RC06c declaration files and all six Context goldens are byte-identical to 9919b67 (checked with git diff, and pinned by tests).

## What was built (D1 to D5)
- D1: seven declarations in a new sibling file data/screen_declarations_batch3.json: Strategies, Navigator Progress, Navigator Inbox, Navigator Learning, Mesh Benefit-Asset links, Mesh Door receipts, Mesh Measures. Each is a new screen_type "menu": no registry noun, no stage, verbs empty (HOLD), no peers.
- Source table: data/screen_sources_batch3.json holds the 19 rows S1 to S19, parsed by tools/gen_batch3_sources.py from the contract text itself (never retyped); a test reproduces the file byte for byte from a hash-checked copy of the contract kept in tests/fixtures. Each row keeps the table's own file, when, status, and exact quote; displayed text is the quote with only three stated mechanical edits (S10 markdown asterisks stripped, as the contract says; the last sentence of S12 and S13, which is an instruction to the builder, is kept out of screen text and out of citations).
- Minimal schema extension for a document source (reported): (a) screen_type menu, with claims of type doc whose rows point into the source table (a registry claim still needs a registry element; the existing 33 screens' rules are unchanged and still validated as before); (b) the loader validates a menu screen against its source table and refuses a screen that shows text beyond the rows unless that text is listed in the file's contract_text; (c) project_menu builds the same depth-limited model as project, from rows; (d) wire entry scaffold_menu(env, screen_id, depth): no registry read, no catalogue read, no route.
- Renderer (one renderer, minimal changes): the Stage label says "a menu screen has no stage"; the Enhance section can list source rows; a claim longer than one line keeps its full text behind a disclosure; the citation label and Technical details can name source rows; the footer omits the registry line when a screen has no registry. Existing pages are unchanged (goldens pass).
- Status: the Status cell, header pill and trust line show the source row's own status word (RULED, CANDIDATE or OPEN) and the row's own note (for example "menu shape; Learning placement conflicts with S4"). No registry status is shown. A CANDIDATE answer leads with "CANDIDATE:" (the RC06c status rule).
- Conflicts shown, never resolved: Learning's open question reads "“Learning under Pattern.” (20 Nov 07:35) versus “An intelligent Inbox and Learning, …” (20 Nov 10:03) and “Learning captures every approval decision: …” (20 Nov 10:05) The live menu follows the later." Strategies keeps both cuts: S9 and S10 (the root grouping), S12 (the artifact's grouping) and the open decision D4 (S11). The unruled proposal S13 is an open item on Progress, Inbox and Learning, never the menu.

## Diff and file list
Patch against the RC06c tree: RC06d_batch3_menu_screens_vs_RC06c.patch, sha256 7ac9a6c0934133130eb2e3a0d426019f7774a76bedbad1c96c48bee746df9c60 (cd /opt/odoo20/addons && patch -p1). Applied and reversed offline on a clean RC06c tree: forward 8e6e4e50..., reverse 376d5386....
| File (under addon/synapsys) | Expected | Actual | sha256 |
|---|---|---|---|
| data/screen_declarations_batch3.json | new | new | 200d26ffedde56eace0191438f8cad5449812c87dee749bbe9918955d7954b70 |
| data/screen_sources_batch3.json | new | new | 9144a0bc8f01a02a9afdb97743e305319f988586d13dfffb3490f1fd082a78ee |
| screen_decl.py | changed | changed | fdaf7e26e564542032105cff5a5e521e531dbd392122f3ce03ac7c8be9bb230e |
| screen_render.py | changed | changed | 4fa2c4c136ceeff9398f8023a7d423fdd1f21fe928337c2be354da83e51782c0 |
| scaffold_wire.py | changed | changed | b4171f276dd30fa5ac90e5df266e160d406252143098db07c7a8476fa6ee0e00 |
| the other 57 files | unchanged | unchanged | n/a |
New tree: 62 files, tree hash **8e6e4e50120b3a8338989ff84e25b601b58542d7512022ead2e180d3a1ca38c6** (the repo's tree-hash method). Not installed anywhere. Outside the addon: tools/gen_batch3_sources.py, gen_batch3_declarations.py, batch3_report.py, tests/test_batch3.py, tests/fixtures (the contract copy), the offline log.

## Offline tests run versus live tests not run
Run: 152 tests, all pass (log tests/TEST_LOG_rc06d_batch3_offline.txt, sha256 096aa2e3df66f7019873126db6f40f6d2607970a160dc74ebacfccd1836e6b0a): 63 test_screen_arch + 3 test_ui_script + 30 test_batch1 + 25 test_batch2 + 31 new test_batch3. Acceptance checks 1 to 17 run over all 37 declarations.
New tests: provenance (every shown text is a source row verbatim; each quote is in the contract table; both generators reproduce their files byte for byte); no wording outside the source table (after removing every source string, the contract-listed text and the open-question stems, each remaining word must be one of the renderer's own); status (Status cell equals the row's status and note; nothing shown RULED unless its row says RULED; the status follows a changed row); conflict (Learning shows both placements and chooses neither; Strategies shows both cuts and D4); S13 only as an Enrich open item; open questions are only conflicts and unruled proposals; no verbs; "Records: none" only where the contract says it, and no promotion wording anywhere; menu schema enforced (10 malformed declarations refused); entitlement (Enable holds only the frame and the answer row; a client gets no Enrich content); wire reads nothing from the environment and writes nothing; row S8 is used by no screen; goldens unchanged.
Edits to earlier tests, none weakening: the type list now includes menu; the one-line-cell and table checks treat menu like noun; check 6 counts a verbatim quotation with no final full stop as one sentence (the text is never edited to add one); the registry-quote test skips menu screens (they have no registry element); a count of declarations was raised from 30 to 37.
Mutation sanity, 9 faults, each made tests fail: a source row text altered (2 failures), row status hardcoded RULED (5), screen status hardcoded RULED (3 plus 1 error), Learning conflict dropping the earlier statement (2), a verb bound on a menu (2 plus 4 errors), an invented open question on Door receipts (2), the answer lead removed (1 plus 1 error), the unused row S8 pulled into Progress (2), the RC06c file touched (2).
NOT run: live tests, install, browser render, the RC06a TransactionCase file, the UI script against dev. Real-size layout remains UNOBSERVED. The 19 quotes could not be checked against the project documents (the builder cannot read them): they are the chat lane's copies, as the contract says, and D009 or the Navigator should re-check them.

## D5: per screen
| Screen | Answer row | Rows used (status) | Chips kept | Chips dropped | Open questions | Sections that read "none recorded" or say nothing is declared |
|---|---|---|---|---|---|---|
| Strategies | S9 | S9 (RULED), S10 (RULED), S12 (CANDIDATE), S11 (CANDIDATE) | 4 of 4 | 0 | decision on S11 | Linked peers: none declared |
| Navigator Progress | S1 | S1 (RULED), S2 (RULED), S3 (RULED), S13 (CANDIDATE) | 4 of 4 | 0 | proposal on S13 | Linked peers: none declared |
| Navigator Inbox | S4 | S4 (RULED), S5 (RULED), S13 (CANDIDATE) | 3 of 3 | 0 | proposal on S13 | Linked peers: none declared |
| Navigator Learning | S6 | S6 (RULED), S4 (RULED), S7 (RULED), S13 (CANDIDATE) | 4 of 4 | 0 | conflict on S7; proposal on S13 | Linked peers: none declared |
| Mesh Benefit-Asset links | S14 | S14 (CANDIDATE), S15 (CANDIDATE) | 2 of 2 | 0 | 0 | Linked peers: none declared; Open questions: none recorded |
| Mesh Door receipts | S16 | S16 (CANDIDATE), S17 (CANDIDATE), S18 (CANDIDATE) | 3 of 3 | 0 | 0 | Linked peers: none declared; Open questions: none recorded |
| Mesh Measures | S19 | S19 (CANDIDATE), S17 (CANDIDATE), S18 (CANDIDATE) | 3 of 3 | 0 | 0 | Linked peers: none declared; Open questions: none recorded |
Chips are one per source row (short source name plus the row's own "when"; S11 to S19 have a date but no time, and none is added). Every row used is kept; none dropped. Open questions are only those the contract names (a conflict, the open decision D4, the unruled proposal S13).

## Findings and choices to review (mine, not rulings)
1. Wording beyond the source rows (all listed in the declaration file's contract_text, or fixed renderer wording): "Records: none" (Strategies and Mesh Benefit-Asset links, from the contract's "say records: none"); "The live menu follows the later." (the contract's instruction "say the live menu follows the later"; no source row states it, so it is the contract author's statement and is unverified against the documents); the heading "Nine strategies by group" (S12's own phrase, first letter capitalised); the connectors "versus" and "and" in the conflict question (the contract's own "versus"); the heading "Made of" for the Enhance list of further rows; the HOLD reason "noun-to-verb governance waits on the Architecture tab", carried from the earlier batches because the contract only says verbs HOLD. If any of these is more than the Steward wants, say so.
2. Row S8 ("align Progress, Inbox and Learning to the Adapt strategies", OPEN) is in the source table but the contract's per-screen lists use it on no screen, so no screen shows it. A test records this. If it should appear, name the screens.
3. "Answer from S9, S10" for Strategies: the answer line is S9; S10 is its own row in the trust table (Enrich) with its asterisks stripped. The trust line therefore counts 1 source, the answer row's own. S10 is not shown at Enable or Enhance.
4. S12 (the nine names in three groups) is shown as one verbatim line, including the label "Build (Deliver in the artifact)", not split into a structure; the grouping is the source's own text. S13 is likewise shown as one verbatim line.
5. Learning's answer line is S6 (what Learning does) and its Made of lists S4; Inbox's answer is S4 and its Made of lists S5. The contract names the rows but not which is the answer; I took the first row that describes the screen itself. Change in the declaration if the Steward prefers another.
6. The ten source short names ("Ledger addendum (nouns, verbs)", "Navigator screen v0.1 s3", "Door patch (commit message)" and so on) are authored by me, one per source file string in the table.
7. S7's status is "RULED (menu shape; ...)": the Status cell shows RULED with the row's own conflict note, and the conflict is also an open question. That is faithful to the row, but a reader sees a RULED pill beside a conflict.
8. Door receipts and Measures say CANDIDATE (not pushed, D007 release needed) only through S16's own note "local only, not pushed"; the contract's wording "D007 release needed" is not in any row, so it is not shown.

## Rights and gaps
Rights: no registry read, no catalogue read, no sudo, no write, no raw SQL; scaffold_menu reads nothing from the environment except the caller's groups. Nothing written to dev or V20. Registry 0.3.5 unchanged. Not touched: menu binding, routes, install, registry release, verb binding, the nine action screens (batch 4), Architecture register and Lexicon, the Context declaration (frozen; D7 not approved).
Gaps: never rendered in a browser; no live run; the patch assumes the RC06a to RC06c trees are installed first (none is). With this batch the declarations cover 37 screens.

## Dissent
None against the rulings. One observation: Navigator Learning shows a RULED row (S7) and a RULED answer (S6) next to an open conflict that says the two disagree; the screen reports the conflict but cannot say which ruling governs, as instructed. Until a Steward ruling settles it, a reader of this screen sees two RULED statements in tension.

## Delivered versus Realised
Delivered: seven declarations, the source table, the minimal doc-source schema extension, 152 passing offline tests, patch and hashes, this return. Realised: UNOBSERVED until the Steward accepts on dev; nothing is installed.

## Release path (not authorised here)
Needs a fresh Steward word and the dev fast path (backup, verified transfer, upgrade, restart, read-back, rollback patch recorded). RC06a to RC06d would install together, since each is built on the uninstalled tree before it; reversing the four patches restores RC05e (15c37960...).

## ONE NEXT
Owner: Steward. Say whether the wording in finding 1 is acceptable and whether S8 should appear on a screen; have D009 or the Navigator check the 19 source quotes against the project documents; then say whether RC06a to RC06d go to the dev fast path or batch 4 (the nine action screens) is built next. The Context date edit (D7) stays unapproved and unapplied.
