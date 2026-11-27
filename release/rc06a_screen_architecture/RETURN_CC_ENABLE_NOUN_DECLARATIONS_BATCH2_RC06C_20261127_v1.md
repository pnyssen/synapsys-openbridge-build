# RETURN: RC06c batch 2, noun declarations for the 10 PROPOSAL and 2 OPEN nouns, source-only candidate (claude_code), 27 Nov 2026
Work Object WO-SYNAPSYS-CANONICAL-REFERENCE-ARCHITECTURE-001 | CTX-SS | CANDIDATE | NON_AUTHORISING
Contract: BUILD_CONTRACT_ENABLE_NOUN_DECLARATIONS_BATCH2_RC06C_20261127_v1.md, sha256 a8bd28eb2b31a789c8342d7ca08234bed5035588bc1cb9b86e6a48d5bf7b4dd6 (read via sp_read_bytes, hash matched).
Evidence state: offline tests run and passing; live tests: none. Authority: none conferred. Implementation: source built, NOT installed. PPV: no movement. Filed status: new file only.

## Consumed base state and hash (verified before any change or push)
- Branch claude/synapsys-v20-release-service-tvjpyn, HEAD 798eb07 (RC06b), equal to origin; no later commit; working tree clean.
- Addon tree release/rc06a_screen_architecture/addon/synapsys: 59 files, tree hash 936d365b0b11f3d80ce96de96048d65ec5039dda741e288d684790ca215c6c0d with rc04g_baseline_hash_20261126_v3.sh. EQUAL to the contract's value.
- RC06b was extended, not rebuilt. The RC06a file (sha 2aa42577...) and the RC06b file (sha 2e278bc8...) are byte-identical to 798eb07 (a test pins both).

## What was built
- D1: 12 noun-screen declarations in a new sibling file data/screen_declarations_batch2.json: PROPOSAL (10): Purpose, Capability, Chain, Partner, Method, Work, Pattern, Signal, Change, Market; OPEN (2): Industry, Product. A test confirms these are exactly the nouns the registry 0.3.5 holds as non-RULED (10 PROPOSAL, 2 OPEN). Each screen reports the sha256 of its own file as its fingerprint. Content rules as batch 1: every text read from the registry element, each chip tied to a quote in the registry text, no invented peer, claim, date, verb or open question, no stage, verbs empty (HOLD). Generator: tools/gen_batch2_declarations.py (reproducible byte for byte, tested).
- D2 (minimal changes, reported): (a) screen_decl.DEFAULT_PATHS gained the batch 2 file; (b) new rule answer_lead (screen_decl.project) and one line in the answer slot of screen_render: when the registry status is not RULED, the answer line leads with the registry's own status word ("PROPOSAL:"), and "UNSOURCED:" when the registry has no status. Nothing is added when the definition already opens with that word (Industry's definition starts "OPEN." and Product's "OPEN:"), so there is no "OPEN: OPEN." doubling. RULED screens get no lead and no new key: all 16 RULED noun screens and Context are byte-identical to RC06b (golden test passes). Validator, loader logic and wire are otherwise unchanged.
- Status honesty (new in this batch): the trust line, the header pill and the Status cell of the trust table carry the registry status in exactly the same positions and markup as a RULED noun; only the word differs. Tests: status text equals the registry's at every depth; the trust line and Status cell markup match a RULED noun's once the word is blanked; the answer line starts with the status word at every depth; no "RULED" appears for the noun itself on any screen, and none anywhere on a screen without a Made of section; if the registry status is changed to RULED, PROPOSAL, OPEN or removed, the screen follows it (read, never assumed).

## Diff and file list
Patch against the RC06b tree: RC06c_batch2_noun_declarations_vs_RC06b.patch, sha256 4a75427ed9b62976e15fe1dc98f22e0fbeb5365383235f434a5b1877ea890a9d (cd /opt/odoo20/addons && patch -p1). Applied and reversed offline on a clean RC06b tree: forward 376d5386..., reverse 936d365b....
| File (under addon/synapsys) | Expected | Actual | sha256 |
|---|---|---|---|
| data/screen_declarations_batch2.json | new | new | 19aef83e13c26a6b5e8062a7df9114eb085bb34a5d305e5332b2b43ee9d117b5 |
| screen_decl.py | changed | changed | 786b2356bb75882eba5b0ee19da8af9b967cbde2732c1e3a1b0e9e0d194b8960 |
| screen_render.py | changed | changed | 416abae6035ffeccb08f635f4584144dcab9abeabd0c634916741650f7e490fd |
| the other 57 files | unchanged | unchanged | n/a |
New tree: 60 files, tree hash **376d5386477779b8c447144070100d0113395033b90b7e2e0b64e2d622436c23**. Not installed anywhere. Outside the addon: tools/gen_batch2_declarations.py, tools/batch2_report.py, tests/test_batch2.py, the offline log.

## Offline tests run versus live tests not run
Run: 121 tests, all pass (log tests/TEST_LOG_rc06c_batch2_offline.txt, sha256 314045037f3e89944a7d91c335880725d1e9e43f310d5db9276547d011e1a962): 63 test_screen_arch + 3 test_ui_script + 30 test_batch1 + 25 new test_batch2. Acceptance checks 1 to 17 run over all 30 declarations (test_screen_arch's all-declarations list picks the 12 up).
Test edits, none weakening: (1) the batch 1 test of the declaration file list became a subset check and now also pins the RC06b file's sha; (2) acceptance check 6 (one answer sentence) now ignores the status lead and the registry's own leading marker "OPEN." before counting sentences, because Industry's registry definition is literally "OPEN. Builder proposal: ..." (two sentences in the registry text itself; it is shown verbatim).
Mutation sanity, 8 new faults, each made tests fail: answer lead removed (2 failures), trust status hardcoded RULED (5), header pill hardcoded RULED (3), a batch 2 chip quote altered (6), an invented chip date (2), a relationship chosen for Chain (2), a peer invented for Capability (6), the RC06b file touched (3).
NOT run: live tests, install, browser render, the RC06a TransactionCase file, the UI script against dev. Real-size layout (check 10) remains UNOBSERVED.

## D6: per noun (no chip dropped on the real registry; every quote is in the registry text)
| Noun | Registry status | Chips kept | Chips dropped | Answer line leads with | Open questions | made_of (registry relationship) | Sections that read "None recorded" or say nothing is declared |
|---|---|---|---|---|---|---|---|
| Purpose | PROPOSAL | 3 of 3 | 0 | PROPOSAL | 2 | H.CTX | Linked peers: none declared |
| Capability | PROPOSAL | 3 of 3 | 0 | PROPOSAL | 3 | H.SVC | Linked peers: none declared |
| Chain | PROPOSAL | 4 of 4 | 0 | PROPOSAL | 2 | none | Made of: no roles declared; Linked peers: none declared |
| Partner | PROPOSAL | 3 of 3 | 0 | PROPOSAL | 2 | none | Made of: no roles declared; Linked peers: none declared |
| Method | PROPOSAL | 5 of 5 | 0 | PROPOSAL | 2 | none | Made of: no roles declared; Linked peers: none declared |
| Work | PROPOSAL | 4 of 4 | 0 | PROPOSAL | 2 | H.WRK | Linked peers: none declared |
| Pattern | PROPOSAL | 3 of 3 | 0 | PROPOSAL | 3 | H.LRN | Linked peers: none declared |
| Signal | PROPOSAL | 5 of 5 | 0 | PROPOSAL | 3 | H.SIG | Linked peers: none declared |
| Change | PROPOSAL | 3 of 3 | 0 | PROPOSAL | 4 | none | Made of: no roles declared; Linked peers: none declared |
| Market | PROPOSAL | 4 of 4 | 0 | PROPOSAL | 4 | none | Made of: no roles declared; Linked peers: none declared |
| Industry | OPEN | 4 of 4 | 0 | (definition already opens with OPEN) | 3 | none | Made of: no roles declared; Linked peers: none declared |
| Product | OPEN | 4 of 4 | 0 | (definition already opens with OPEN) | 4 | none | Made of: no roles declared; Linked peers: none declared |
Made of left null: Chain (the registry names it the subject of a required role in two relationships, H.BEN and H.PRG; none chosen); Partner, Method, Change, Market, Industry, Product (no registry relationship names them the subject of a required role). Declared by the batch 1 rule: Purpose H.CTX, Capability H.SVC, Work H.WRK, Pattern H.LRN, Signal H.SIG.
Capability, Product and Change (item 2): noun screens, nothing said about records beyond the registry's own text (a test removes every registry-derived string from the page and finds no "record" left). The registry's own open question that Capability has no V20 model is shown as the registry words it.

## D7: Context consistency note (report only; Context is NOT changed in this batch)
- Which chip: the Service peer row of the trust table in the RC06a Context declaration. In data/screen_declarations.json, claim peer.service has the source {"name": "Ledger", "date": "20 Nov 10:51", "quote": "10:51 (KDA seats"}. It appears twice: SCR.CONTEXT.NOUN (line 60) and SCR.CONTEXT.RECORD (line 115). SCR.ASSET.RECORD has no such chip.
- What the registry text holds (N.SERVICE definition_source): "ledger 20 Nov 07:06 (Service Catalogue is the key interface), 10:51 (KDA seats are Services run by named engines)". It gives "10:51" with no date of its own; "20 Nov 10:51" is not a string in the registry text. The chip inherits the date from the preceding entry. The batch 1 Service screen shows the same fact as "Ledger 10:51".
- Minimal edit: change "date": "20 Nov 10:51" to "date": "10:51" at those two lines (the quote is unchanged and still found). I applied it to a scratch copy to measure the effect: the declaration file's sha256 changes (2aa42577... to 7cf21a6acd4b965e6fd1c33faafecfb86243cfdd68f1451469e9888fa6b90fc3), so the fingerprint shown for all three RC06a screens changes too. Golden files that change: 4 of the 6 Context noun goldens (rc06a_context_noun_route_enable.json, _enhance.json, _enrich.json: the declaration_sha field; rc06a_context_noun_view_enrich.html: the chip text "Ledger 20 Nov 10:51" becomes "Ledger 10:51" and the printed fingerprint changes; the enable and enhance views are unchanged). Tests that pin the old values and would need the new constant or golden: 7 (3 in test_batch1, 3 in test_batch2, 1 in test_screen_arch). No other output changes. This needs a Steward word because Context is frozen and the golden is the evidence of that.
- Alternative the Steward may prefer: keep "20 Nov 10:51" and change batch 1's Service chip to match; I do not recommend it, since it writes a date the registry text does not contain.

## Findings and choices to review (mine, not rulings)
1. The status lead is generic (status-driven, not noun-specific) and visible at every depth. Pill styling is the same plain pill for RULED, PROPOSAL and OPEN, as the contract asks (same position and form); the difference is only the word. If the Steward wants PROPOSAL and OPEN visually distinct (colour), that is a renderer change.
2. Made of is declared by a mechanical rule, not a judgement. Purpose gets H.CTX, so its Made of is the same role table as the Context screen's; Capability gets H.SVC (Service operation), where it is the first required role. Review these five; they can be set to null in the declaration.
3. Chip dates are as the registry text writes them: "20 Nov 05:5x" (Chain, the lens.json citation, a partial time in the registry text), "19 Nov" (Partner, "ledger 19 Nov line 10"), "16 Nov 23:32" (Purpose, the date inside the design_d.json citation), "07:35", "10:05", "10:33" (times only, no date inherited). Chip short names are authored by me, each tied to a quote.
4. No peers are declared for any of the 12 (the registry holds no peer list). Enhance is thin for the 7 nouns with no Made of.
5. The wire still reads the SP-01 catalogue record on every noun-screen call even though no batch screen declares a peer (existing behaviour, unchanged; not shown on these screens, tested).

## Rights and gaps
Rights: reads only, as the caller; no sudo, no writes, no raw SQL (source scan test passes). Nothing written to dev or V20. Registry 0.3.5 unchanged. Not touched: Strategies and the six project-document screens (batch 3), the nine action screens (batch 4), Architecture register and Lexicon, menus, routes, install, verb binding.
Gaps: never rendered in a browser; no live run; the patch assumes the RC06a and RC06b trees are installed first (none is). With this batch the declarations cover 30 screens (Context noun and record, Asset record, 15 RULED, 12 PROPOSAL/OPEN).

## Dissent
None against the rulings. One observation: a PROPOSAL screen and a RULED screen now look the same apart from one word in four places (header pill, answer lead, trust line, Status cell). That is what the contract asks for comparability; whether it is loud enough to stop a reader treating a PROPOSAL as settled is a Steward judgement I cannot test offline.

## Delivered versus Realised
Delivered: 12 declarations, the status-lead rule, 121 passing offline tests, patch and hashes, the D7 note, this return. Realised: UNOBSERVED until the Steward accepts on dev; nothing is installed.

## Release path (not authorised here)
Needs a fresh Steward word and the dev fast path (backup, verified transfer, upgrade, restart, read-back, rollback patch recorded). RC06a, RC06b and RC06c would install together, since each is built on the uninstalled tree before it; reversing the three patches restores RC05e (15c37960...).

## ONE NEXT
Owner: Steward. Say yes or no to the D7 edit (Context chip date "10:51"), then say whether RC06a to RC06c go to the dev fast path or batch 3 (Strategies and the six project-document screens, which need the project-document sources) is built next.
