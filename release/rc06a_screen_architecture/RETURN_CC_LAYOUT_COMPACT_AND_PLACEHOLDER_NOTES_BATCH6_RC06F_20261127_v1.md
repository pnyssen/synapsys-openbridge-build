# RETURN: RC06f batch 6, compact "made of" and "linked peers" lists; S12 and S13 placeholder notes, source-only candidate (claude_code), 27 Nov 2026
Work Object WO-SYNAPSYS-CANONICAL-REFERENCE-ARCHITECTURE-001 | CTX-SS | CANDIDATE | NON_AUTHORISING
Contract: BUILD_CONTRACT_LAYOUT_COMPACT_AND_PLACEHOLDER_NOTES_BATCH6_RC06F_20261127_v1.md, sha256 f874250aa16a9ceef2c2dd9c3f89deef9baa6b10a6430db5da65797105f23ce8 (read with sp_read_bytes, hash matched).
Evidence state: offline tests run and passing; live tests: none. Authority: none conferred. Implementation: source built, NOT installed. PPV: no movement. Filed status: new file only.
Steward instruction carried: the Context date edit (D7) stays NOT approved and is not applied. The contract's layout word authorises changing Context's rendered HTML for layout only; Context's declaration file is untouched.

## Consumed base state and hash (verified before any change or push)
- Branch claude/synapsys-v20-release-service-tvjpyn, HEAD 970528c (RC06e), equal to origin; no later commit; working tree clean.
- Addon tree release/rc06a_screen_architecture/addon/synapsys: 64 files, tree hash f1f3707d095f6c2ad53b6c4e1ed4212dbbd5068eb9e9ee6417f2ccb4d47460d6 with rc04g_baseline_hash_20261126_v3.sh. EQUAL to the value given.

## What was built
- D1 layout (screen_render.py, the shared style block and one class): the "made of" list and the "linked peers" list get a second class, "cp", on their container (class="cd" becomes class="cd cp"). The CSS rule, in the shared style block: the list block has max-width 44rem (the contract's 40 to 48); each row is flex-wrap with its label in a fixed 12rem column and its chips following on the same line, wrapping within the list; at 600 px and below the existing stacked layout applies and the 12rem basis is reset (otherwise it would become a height in a column). Pure CSS; no script. Every screen with these lists is compacted by this one change: 30 of the 46 screens have such a list (64 list blocks across Enhance and Enrich); the other 16 have no roles or peers to list (for example Asset record, Strategy, Portfolio). The Trust table, header, answer, trust line, movement line, open-questions list and Technical details are untouched, and no text changed.
- D2 placeholders: the batch 3 generator takes an optional overrides file (tools/overrides_batch3_sources_rc06f.json) that may change a row's note and nothing else; with it, S12 and S13 carry the note "placeholder compiled by the chat lane; replace with sourced text" and stay CANDIDATE. Their text, date and file are unchanged. screen_sources_batch3.json is regenerated from the batch 3 contract table plus that override (not hand-edited); the generator still reproduces it byte for byte, and without the override still reproduces the RC06e table byte for byte. The row's earlier status is kept in a new field previous_status. The note shows wherever those rows show a note: Strategies lists S12 under "Nine strategies by group" with the note beside its pill (Enhance), and S12 and S13 each have the note in their trust-table Status cell and full citation (Enrich). Declaration files are untouched.

## Diff and file list
Patch against the RC06e tree: RC06f_layout_compact_and_placeholder_notes_vs_RC06e.patch, sha256 c7b2ea76846b6a0ccc01e34b041c8d8e14586cf165e0d21610d50d3d25021c99 (cd /opt/odoo20/addons && patch -p1). Applied and reversed offline on a clean RC06e tree: forward baad1cc6..., reverse f1f3707d....
| File (under addon/synapsys) | Expected | Actual | sha256 |
|---|---|---|---|
| screen_render.py | changed | changed | 87046bdedfcf45d71a31faef2d05f695d16bfdeb521dee3b2a1325eecacb9ecd |
| data/screen_sources_batch3.json | changed | changed | c6af8087d1265e4cac50d44f4c01cdd2522290378d6d8188521d4177985aa210 |
| the other 62 files | unchanged | unchanged | n/a |
New tree: 64 files, tree hash **baad1cc64c151d0ce099a48cbfd1473355713df87733665d4143259a1fcfae16**. Not installed anywhere. Outside the addon: tools/gen_batch3_sources.py (override option), tools/overrides_batch3_sources_rc06f.json, tools/gen_rc06e_baseline.py, tests/pages_all.py, tests/test_batch6.py, tests/golden (the RC06e baseline, the RC06e Context views and the RC06e source table, kept as the "before"), the offline log.

## Golden diffs (Context, the contract asked for each)
The route JSON goldens (three) are byte-identical to RC06e: declaration_sha is unchanged (2aa42577...). The three view goldens (tests/golden/rc06a_context_noun_view_*.html) changed as follows; the RC06e originals are kept beside them as rc06e_context_noun_view_*.html.
- Enable: only the style block (the new rules below). Zero markup change.
- Enhance: the style block, plus class="cd" becomes class="cd cp" twice (the "What a Context is made of" list and the "Linked peers" list).
- Enrich: the same as Enhance (the style block and those two class names).
Style block, removed from the end of the block: @media (max-width:600px){.syn-sc .kv{flex-direction:column;gap:2px}.syn-sc .kv span:last-child{text-align:left}.syn-sc .tt th:nth-child(3),.syn-sc .tt td:nth-child(3){display:none (that media rule is rewritten with additions). Added in its place:
.syn-sc .cp{max-width:44rem}
.syn-sc .cp .kv{justify-content:flex-start;flex-wrap:wrap;gap:4px 14px}
.syn-sc .cp .kv span:first-child{flex:0 0 12rem;min-width:0}
.syn-sc .cp .kv span:last-child{flex:1 1 12rem;text-align:left}
@media (max-width:600px){ ...the same three existing rules... .syn-sc .cp .kv{gap:2px} .syn-sc .cp .kv span:first-child,.syn-sc .cp .kv span:last-child{flex:0 1 auto} }
A test proves that outside the style block each golden differs from the RC06e one by those class names only, and that the visible text is identical.

## Offline tests run versus live tests not run
Run: 192 tests, all pass (log tests/TEST_LOG_rc06f_batch6_offline.txt, sha256 a781c842632a717d47b9d25466c87c9643f70449c6ef58cd6cca626be38d4d8d): the 174 earlier plus 18 new in test_batch6.
New tests: for all 46 screens at all 3 depths (138 pages) the visible text equals the RC06e text (compared by sha256 against a baseline generated from commit 970528c itself, with two stated normalisations: the S13 old note and the placeholder note are removed from each side, and the batch 3 pages' "Source table fingerprint" line, which changes because the source table does); the markup of every page that does not show S12 or S13 is identical to RC06e once the style block is removed and the "cp" class is put back; the compact class is on both lists wherever they exist and nowhere else (not the Trust table, header, answer, trust line, movement line, open questions or Technical details); the CSS rule is checked statically (44rem within 40 to 48, wrap, fixed 12rem label column, the 600 px reset, no fixed pixel width, no script); S12 and S13 show the placeholder note and are still CANDIDATE, no other row carries it, and the rest of the source table equals the RC06e table field by field; the override may change a note and nothing else; the declaration files, UNSOURCED wording and registry are pinned unchanged.
Edits to earlier tests, each listed, none weakening: the three Context view goldens were regenerated (layout markup only, shown above); batch 3's generator test now passes the override file; batch 4's pin of the batch 3 source-table hash was updated (9144a0bc... to c6af8087...).
Mutation checks, 8 faults, each made tests fail: the placeholder note removed from the override (2 failures), the sources file hand-edited (8), a screen's text changed by the layout edit (2), the compact class dropped from the peers list (7), max-width back to full width (6), the compact class leaking onto the Trust table (6), the placeholder note added to a RULED row (2), the narrow-screen reset removed (6).
NOT run: any browser render. The 390 px and 1024 px behaviour is checked by the CSS rule only; I cannot confirm how it looks. Also not run: live tests, install, the Odoo TransactionCase file, the UI script on dev.

## Findings and choices to review (mine, not rulings)
1. The Enable golden also changes (style block only). The contract expected only Enhance and Enrich to change. The compact rules live in the one shared style block that every page carries, so every page (all 46 screens, all depths) carries the new CSS; only the Enhance and Enrich pages have the new class. I did not make the CSS conditional to keep Enable byte-identical; say if you want that.
2. S13's earlier note "proposal, Steward decision 3 unruled" is replaced, as the contract directs, and is no longer shown on any screen (it is kept in the source table as previous_status). Progress, Inbox and Learning still show S13 as CANDIDATE and as an open item, but a reader no longer sees "Steward decision 3 unruled" next to it.
3. The contract says the note shows in the "trust line note". The trust line has no note slot (it shows status and source count), and S12 and S13 are never the trust claim, so the note appears in the Status cell, the Made-of item and the full citation, not on the trust line. No renderer change was made for it.
4. With the 12rem label column, a long label wraps inside its column rather than widening it; the chips column wraps below it on narrow lists. I could not look at it.
5. The batch 3 pages print a source-table fingerprint in Technical details; it changes because the source table changed (9144a0bc... to c6af8087...). This is the only visible-text change outside S12 and S13.
6. The "UNSOURCED" wording and every declaration text are untouched (D4).

## Rights and gaps
Rights: no registry read, no catalogue read, no sudo, no write, no raw SQL; nothing written to dev or V20. Registry 0.3.5 unchanged. Not touched: declaration texts, the Trust table, menus, routes, install, verb binding, Context's declaration file.
Gaps: never rendered in a browser; no live run; the patch assumes RC06a to RC06e are installed (RC06e is installed on dev; the earlier ones are in that tree).

## Dissent
None against the rulings. One observation: the placeholder note is long ("placeholder compiled by the chat lane; replace with sourced text"). In the Status cell it sits on the one allowed line and is clipped with an ellipsis on narrow widths, with the full text behind the row's full-text and citation disclosures.

## Delivered versus Realised
Delivered: the compact layout in one renderer place, the S12 and S13 placeholder notes through a reproducible override, 192 passing offline tests, patch and hashes, this return. Realised: UNOBSERVED until the Steward looks at it on dev; nothing is installed.

## Release path (not authorised here)
Needs a fresh Steward word and the dev fast path (backup, verified transfer, upgrade, restart, read-back, rollback patch recorded). The rollback is the reverse of this patch, which restores tree hash f1f3707d... (RC06e, as installed).

## ONE NEXT
Owner: Steward. After this goes to dev, look at the Context screen at Enhance and Enrich (and at 390 px) and say whether the compact lists are right; say whether finding 1 (Enable also carries the new CSS) and finding 2 (S13's old note no longer shown) are acceptable; then the later placeholder-wording batch can proceed. The Context date edit (D7) stays unapproved and unapplied.
