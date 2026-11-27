# BUILD CONTRACT: RC06d batch 3, declarations for the screens sourced from project documents (v1)
Work Object WO-SYNAPSYS-CANONICAL-REFERENCE-ARCHITECTURE-001 | CTX-SS | CANDIDATE | NON_AUTHORISING | one builder per object | plan: PLAN_ENABLE_ALL51_SEQUENCED_BUILD_20261127_v1.md (sha 2aea7035b25cdd6f985211ea27805411e37b208693fe419b49a8639888631115)
Author's note: the source table below was copied by Claude (chat lane) from the SynapSys project documents named in each row, because the builder cannot read project documents. Quotes are exact copies; D009 or the Navigator should re-check them against the documents. The builder treats this table as the only source for these screens and must not add text from memory.

## Base (verify first, stop if different)
Start from the RC06c commit if batch 2 has been pushed (read git log; state the HEAD and its tree hash and that it matches the RC06c return), otherwise from 798eb07 (tree 936d365b0b11f3d80ce96de96048d65ec5039dda741e288d684790ca215c6c0d, 59 files, rc04g_baseline_hash_20261126_v3.sh). Do not start until batch 2's return is filed or the Steward says to build in parallel: one builder per object, and both batches edit the loader's declaration list.

## Goal
Declare these seven screens on schema synapsys.screen.declaration/1 in a new sibling file data/screen_declarations_batch3.json, as noun-less "menu screens" (no registry noun exists for them; no stage; verbs empty = HOLD): Strategies, Navigator Progress, Navigator Inbox, Navigator Learning, Mesh Benefit-Asset links, Mesh Door receipts, Mesh Measures. Every claim is bound to a source row below (name, document, timestamp, exact quote). Where the schema ties a claim to a registry element, make the minimal schema extension for a document source (kind "doc", row id, quote) and report it; do not weaken the registry rule for the existing 33 screens. Registry status is NOT shown for these screens (no registry element): the Status cell shows the source's own status: RULED (ledger row), CANDIDATE (proposal document), or OPEN (ledger row marked open). Conflicts are shown as open and never resolved.

## Source table (id | source file | when | status | exact quote)
S1 | claude/rulings-ledger-addendum-2026-11-19-2240-architecture-nouns-verbs-separate.md | 20 Nov 07:29 | RULED | "The Navigator has its own screen and three lenses, to be progressively mapped and integrated into the Architecture."
S2 | same | 20 Nov 07:33 | RULED | "Navigator lenses: OBA is value, UIQ is prioritisation, KDA is approvals."
S3 | same | 20 Nov 10:05 | RULED | "ranked Probable->Verified first, then Potential->Probable, then the rest; work with no value link is shown last, flagged 'no value link' (nothing hidden)."
S4 | same | 20 Nov 10:03 | RULED | "An intelligent Inbox and Learning, built around value (OBA) and approval (KDA), both aligned to the Navigator."
S5 | same | 20 Nov 10:05 | RULED | "AI proposes the value (Strategy KPI, OBA element) and the approval needed for each Signal; a person routes it into a Work Object in the Navigator. AI never routes or grades."
S6 | same | 20 Nov 10:05 | RULED | "Learning captures every approval decision: when KDA approves, holds or rejects a PPV step, record why, what evidence moved it and what was missing."
S7 | same | 20 Nov 07:35 | RULED (menu shape; Learning placement conflicts with S4) | "Learning under Pattern."
S8 | same | 20 Nov 10:20 | OPEN (question, not yet a ruling) | "align Progress, Inbox and Learning to the Adapt strategies"
S9 | same | 20 Nov 07:33 | RULED | "Strategy grouping: Live / Build / Adapt (3x3), applied to all nine strategies"
S10 | claude/rulings-ledger-addendum-2026-11-19-1334-strategy-groups-live-build-adapt.md | 19 Nov 13:34 | RULED | "Strategy groups are **Live / Build / Adapt**"  (strip the markdown asterisks in the displayed text; keep the quote match on the plain words "Strategy groups are" and "Live / Build / Adapt")
S11 | claude/navigator-screen-and-strategy-lens-v0.1-2026-11-20.md | 20 Nov | CANDIDATE (open decision D4) | "The artifact's grouping and the root nesting are therefore two different 3 × 3 cuts of the same 27."
S12 | claude/navigator-screen-and-strategy-lens-v0.1-2026-11-20.md section 3 table | 20 Nov | CANDIDATE | nine strategies by group: Live: Balanced Lives, Synergistic Collaboration, Enduring Wealth. Adapt: Renewal, Prioritisation, Stewardship. Build (Deliver in the artifact): Capture Valuable Markets, Compound Innovation, Integrate Value Networks. Show names only; verbs are NOT shown (verbs not yet bound).
S13 | claude/kinematic-domain-overlays-live-build-adapt-v0.1-2026-11-20.md section 4 | 20 Nov | CANDIDATE (proposal, Steward decision 3 unruled) | proposed Navigator menu "Progress · Approvals · Learning" with the Inbox kept as the entry point, replacing "Progress · Inbox · Learning"; Progress = Prioritisation, Approvals = Stewardship, Learning = Renewal. Show as OPEN, not as the menu.
S14 | claude/library-sorting-framework-and-critical-questions-v0.1-2026-11-14.md s3 | 14 Nov | CANDIDATE | "Asset needs 3 or more qualified Benefits plus rights."
S15 | same | 14 Nov | CANDIDATE | "Benefit needs accepted, attributable net change with no double count"
S16 | claude/mesh-registry-door-87866af-2026-11-20.patch.txt (commit message) | 20 Nov | CANDIDATE (local only, not pushed) | "Door ADMIT/DOOR_PENDING receipts append-only and keyed to the active registry sha"
S17 | claude/mesh-architecture-persisted-in-odoo-and-door-bound-v0.1-2026-11-20.md | 20 Nov | CANDIDATE | "The job ships switched off; switching it on is your release decision"
S18 | claude/v20-architecture-menu-map-and-integration-routine-v0.1-2026-11-22.md section 3 | 22 Nov | CANDIDATE | "Empty: Door receipts and Measures. The Mesh pulse and Door jobs are switched off."
S19 | claude/mesh-registry-door-87866af-2026-11-20.patch.txt (model description) | 20 Nov | CANDIDATE | "A measure stored by Mesh address"

## Per screen (what each declares; nothing beyond)
- Strategies: answer from S9, S10; the nine strategy names in three groups from S12; D4 shown as OPEN from S11 (two cuts of the same 27, both kept); verbs HOLD. Strategy records: none (the screen is a lens, not a record list).
- Navigator Progress: S1, S2 (three lenses OBA value, UIQ prioritisation, KDA approvals), S3 (ranking and the "no value link" flag). Status: RULED per row. S13 shown as an open proposal (Progress = Prioritisation).
- Navigator Inbox: S4, S5. Open: S13 (Inbox kept as entry point in the proposal).
- Navigator Learning: S4, S6. OPEN conflict shown as two statements: S7 (Learning under Pattern, 20 Nov 07:35) versus S4/S6 (under the Navigator, 20 Nov 10:03-10:05); say the live menu follows the later; do not choose. S13 Learning = Renewal shown as proposal.
- Mesh Benefit-Asset links: S14, S15 (CANDIDATE; the Asset test). Say records: none and that promotion is a human act only if a source row says so (none of the rows above do; do not add it).
- Mesh Door receipts: S16, S17, S18. Status CANDIDATE (not pushed, D007 release needed).
- Mesh Measures: S19, S17, S18. Same status.
Open questions for each screen are only those shown above (conflicts and unruled proposals). Do not invent others.

## Rules carried (do not re-open)
Fixed frame (header, answer, trust line, movement) at every depth; one question per depth; four-column Enrich trust table (Claim, Status, Source, Open question); source chips: short name plus date, at most three then a count, no date invented; screens declared as data, one renderer; stage not applicable; verbs HOLD ("verbs not yet bound"); Context and all earlier declarations byte-identical (goldens still pass); registry 0.3.5 unchanged.

## Deliverables
D1 seven declarations plus the minimal doc-source schema extension (reported). D2 tests: acceptance checks 1 to 17 over all declarations; per-screen provenance (each quote found verbatim in the source table that ships in the repo as data/screen_sources_batch3.json; add that file); status test (the Status cell equals the source row's status; nothing shown RULED unless the row says RULED); conflict test (Learning shows both placements and chooses neither; Strategies shows both cuts); no-verbs test; goldens unchanged; two mutation faults. D3 run all tests, report counts. D4 patch against the base tree, new tree hash, expected-vs-actual file table. D5 per-screen table: sources used, chips kept/dropped, open questions, sections reading None recorded.

## Out of scope
Menu binding, routes, install, registry release, verb binding, nine action screens (batch 4), Architecture register and Lexicon (held), any data write, any wording not in the source table.

## Return
RETURN_CC_ENABLE_DOC_SOURCED_SCREENS_BATCH3_RC06D_20261127_v1.md in 05_AI_RETURNS_HASHED/WO-SYNAPSYS-CANONICAL-REFERENCE-ARCHITECTURE-001/CANDIDATES/ (not the top-level CANDIDATES folder), with consumed base hash, diff, expected-vs-actual files, offline-vs-live tests (live: none), rights, gaps, dissent, ONE NEXT and owner. Push only after the base hash matches. Release path needs a fresh Steward word.
