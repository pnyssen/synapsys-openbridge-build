# RETURN: screen architecture RC06a, source-only candidate build (claude_code), 27 Nov 2026
Work Object WO-SYNAPSYS-CANONICAL-REFERENCE-ARCHITECTURE-001 | CTX-SS | CANDIDATE | NON_AUTHORISING
Contract: BUILD_CONTRACT_SCREEN_ARCHITECTURE_RC06A_20261127_v1.md, sha256 f971598aa9d4b2d67dd1715edda5dd0b0ac0efa70177538e8076fe8e809f70c5 (read via sp_read_bytes, hash matched).
Evidence state: offline tests run and passing; live tests NOT run. Authority: none conferred. Implementation: source built, NOT installed anywhere. PPV: no movement. Filed status: new file only. This return supersedes the earlier stop return RETURN_CC_SCREEN_ARCHITECTURE_RC06A_STOP_BASE_UNVERIFIABLE_20261127_v1.md (sha256 d455321a894b6d309e87d4443e9508a492bce8571a16cb4d8c16890acbd38ce4), which stopped because the installed tree was not in Git.

## Consumed base state and hash (verified before any change)
- RC05E_INSTALLED_ADDON_TREE_54FILES_20261127_v1.zip: 96005 bytes, sha256 dbb38d528c0e5216eeebfe7517dea7edc38de6cbea12afedbd6efff1b0fb509a (matches the value given). 54 files extracted outside the repo.
- Base tree hash from rc04g_baseline_hash_20261126_v3.sh: 15c37960d1707be2be9b1dbdf18e623d82c97f78f1b009e02af34e46a5837e4b. EQUAL to the contract's value. No differing files.
- The tree was committed verbatim as the base (commit dfde661) and re-hashed in the repo: same value, 54 files.
- Git base commit afbafd8199f610d33fca1f25fcbe9119a142a941 is an ancestor of the checkout, but Git did not hold the 54-file tree before this commit. The tree itself, not the commit, is the verified base.

## What was built (D1 to D6)
- D1 declaration schema: `data/screen_declarations.json` (schema `synapsys.screen.declaration/1`), validated by `screen_decl.validate_screen`. Fields: noun, screen_type (noun|record), slots per depth, claims (text bound to the registry element, status, source chips with name, date or null, and a quote), open-question stems (derived, not authored), verbs (empty allowed; a verb needs a source and status "bound", so no proposed or candidate verbs), and for record screens the kind (`field` or `fixed`).
- D2 one renderer: `screen_render.render_screen` builds the fixed frame (header, answer, trust line, movement) and the declared depth sections through one table of generic slot builders. `scaffold_view.py` is now a thin adapter, so the Context-specific rendering (the role-name table, the peer card, the provenance block) is gone from code and lives in the declaration.
- D3 Context noun declaration (SCR.CONTEXT.NOUN): every text value is read from the registry element or the catalogue record the installed screen already read. A source chip is shown only if its quote occurs in the registry element's `definition_source`; otherwise it is dropped and noted. Where the screen has nothing it says so ("None recorded", "No operating source: HOLD", "none recorded", "UNSOURCED").
- D4 stage: `screen_decl.stage_for_kind` is pure (K-1/K-3/K-4 to enable, K-6/K-8 to enhance, K-12 to enrich, anything else to "not bound"). `resolve_depth` makes `depth_clamped` real for record screens and names the reason (`clamp_reason` is "stage" or "role"). Noun screens never clamp for stage. Stage is computed at render time and stored nowhere (no model field, no stored key in the declarations).
- D5 record path: `scaffold_wire.screen_record` reads one record with the caller's own rights (no sudo) and projects it. Declarations: SCR.CONTEXT.RECORD (kind from `synapsys.context.kind`) and SCR.ASSET.RECORD (own noun kind K-4, Context kind shown as a neighbour only). Exercised offline with in-memory fake records that raise on any write. An Odoo TransactionCase version (rolled-back fixtures) is written but NOT RUN. No controller route was added for record screens.
- D6 tests: acceptance checks 1 to 17 automated against the declarations (66 offline tests); the 31 UI checks re-expressed as `verify/ui_verify_console_rc06a_v1.js` (38 checks: 31 mapped plus 7 new), tested under node against fixtures from the new code and six deliberately wrong installs.

## Diff and file list
Patch: `RC06a_screen_architecture_vs_RC05e_installed.patch`, sha256 539d02f20a8d8ee1459a17593776249838d8ca9590c6e593b181600c3e0bfab5 (apply with `cd /opt/odoo20/addons && patch -p1`; it was applied and reversed offline on a clean copy of the base: forward hash f53ea79e... and reverse hash 15c37960..., both as expected).

| File (under addon/synapsys) | Expected | Actual | sha256 |
|---|---|---|---|
| screen_decl.py | new | new | 1d829d3a321d93e7ab5d081c063b0320bafb580430b8eb5bc650cf251ad385d0 |
| screen_render.py | new | new | 6effe7cdbc3611a1d08d12825bb275eb765717979a81e83377e66f76e20b04e9 |
| data/screen_declarations.json | new | new | 2aa425778fe3a7e2f20d242440c907161484318d3ea91a51120b5a8e31144fe0 |
| scaffold_view.py | changed | changed | ad15b1620a7df39572ff1e96bf35705489c22557e3a949a1b53684dae8182c2a |
| scaffold_wire.py | changed | changed | 4e470ef0e6fb3cd409ae099e3ac407a8651ba34b7726dd0e54304ed794cff956 |
| tests/test_screen_record.py | new | new | 309cfb5cb218c1b4edc4e444ec1e9714d7b59ccf34e00a1ec7697848dce07eb8 |
| tests/__init__.py | changed (one import) | changed | e306074a66839477ddfbb4b5d79d0c10ca4ca02eebfb575ef94df2bd2bae0350 |
| the other 51 files | unchanged | unchanged (byte-identical to base) | n/a |

Unchanged on purpose: controllers/scaffold.py (route contract kept), controllers/lenses.py, static/src/lens_mode.js, static/src/home.js, lens_contract.py, lens_render.py, scaffold_lens.py, __manifest__.py (the declaration file is read by path, not loaded as Odoo data).
New tree: 58 files, tree hash **f53ea79ea501cf63feae758bdcc0efbaa0994cc2136acb287eb6af84435beb5f**, computed with rc04g_baseline_hash_20261126_v3.sh (the repo's tree-hash method). Not installed anywhere: this is the hash a later install would have to reproduce.

## Offline tests run versus live tests not run
Run (66 tests, all pass, log tests/TEST_LOG_rc06a_offline.txt sha256 d14a8a3b6c9c9ad8f9285348b36037d07ee3c7a61a981a3e534cde782996c458):
- test_screen_arch.py (63 checks incl. schema, stage, frame, trust table, entitlement, record screens, D3 provenance) and test_ui_script.py (3, node).
- Mutation sanity: four deliberate source faults (a changed stage mapping, a removed ceiling clamp, a removed table column, depth content leaking to Enable) each made tests fail. A reordered frame slot is refused earlier by the declaration loader.
- RC05 suites against the new files: test_scaffold_lens 18/18 pass unchanged; test_scaffold_view_ui 20 of 30 pass (J1 to J6 and L1 to L9 and V5, V6, V7, V11, V15 pass); test_scaffold_wire 12 of 17 pass.
NOT run: the Odoo TransactionCase file (no Odoo here); the UI script against live dev; any browser render; any real-size check (acceptance check 10 is set aside by the Steward, so only a structural proxy exists); any install.

## Acceptance checks 1 to 17: how each is tested
1 frame order (all depths, all 3 declarations); 2 nothing removed or re-worded (slot-by-slot equality, only the Depth label differs); 3 four columns; 4 one line per cell (one top-level line per cell, long text in a disclosure); 5 each open question once, count per row; 6 Enable one answer, one trust line, one movement; 7 verbs only where bound (validator plus HOLD rendering plus a bound-verb case); 8 entitlement incl. hidden JSON; 9 no writes, no sudo; 10 structural proxy only, real size UNTESTED; 11 Stage and Depth separate, Stage constant across depths; 12 stage computed, not stored; 13 not applicable shown above ceiling; 14 not bound is Enable only with the reason; 15 no screen-specific code, plus a new screen added as a declaration only; 16 checks run over every declaration; 17 each declaration states its type and only record screens clamp.

## D6 mapping: the 31 RC05e UI checks (ui_verify_console_v1.js.txt, sha f8e1e97a97a75b41edd4f1f46e932886d5ca5964abc302bd084697d50c22bd1e, confirmed unchanged)
Run against the new pages, the old script passes 30 of 31 (it fails only enrich_technical_details_present, because the `<details>` now carries a `data-slot` attribute). The new script passes 38 of 38 on the correct fixtures.
| # | Old check | Status | Note |
|---|---|---|---|
| 1-3 | L1_loads, L2_loads, L3_loads | RETAIN | lens routes untouched |
| 4-7 | D16_level1_position_only, D16_level1_note_once, scaffold_card_once_for_steward, D13_card_inside_lens_wrapper | RETAIN | lenses.py untouched |
| 8-9 | D16_level2_position_only, D16_level2_note_once | RETAIN | |
| 10-11 | D16_level3_position_only, D16_level3_no_list_note | RETAIN | |
| 12-14 | scaffold_enable_loads, scaffold_enhance_loads, scaffold_enrich_loads | RETAIN | |
| 15 | enable_headline_only | CHANGED | also asserts the Enable slots are exactly header, answer, trust, movement (ruling 4) |
| 16 | enhance_roles_section_present | RETAIN | heading kept |
| 17 | enhance_plain_role_names | RETAIN | names now come from the declaration |
| 18 | enhance_no_registry_codes_in_roles | RETAIN | |
| 19 | enhance_service_record_found | CHANGED | now read inside the Linked peers slot, because the page is slotted (the old regex would pass anywhere on the page) |
| 20 | enhance_capability_hold | CHANGED | same reason |
| 21 | enhance_no_technical_details | RETAIN | |
| 22 | enrich_four_qualifiers | CHANGED | the four qualifiers are now in the Service row of the trust table (first in Status, three behind "+3 more"); the check reads that row |
| 23 | enrich_evidence_names_SP01 | CHANGED | read inside the Service row's full citation ("Evidence: SP-01 ...") |
| 24 | enrich_hash_not_in_ordinary_copy | RETAIN | |
| 25 | enrich_technical_details_present | CHANGED | selector allows the slot attribute |
| 26 | enrich_technical_details_content | RETAIN | |
| 27 | enrich_presentation_only_statement | RETAIN | |
| 28 | no_script_or_handler_in_view | RETAIN | |
| 29 | bad_depth_refused | RETAIN | |
| 30 | route_read_only_writes_zero | RETAIN | |
| 31 | registry_fingerprint_is_pinned_0.3.5 | RETAIN | |
RETIRED: none. NEW (7): frame order at all depths; frame not re-worded by depth; Stage and Depth two labels; one trust line and one movement with HOLD; trust table four columns; open questions rolled up once; route reports the declaration fingerprint and screen type.
RC05 offline unit tests that read the old data model (V1 to V4, V8 to V10, V12 to V14; W1, W2, W12 to W14) fail against the new files by design, because roles and peers moved under `enhance` and the trust rows under `enrich`. They are CHANGED, not dropped: each behaviour is re-expressed in test_screen_arch.py (escaping, clamp explanation, presentation-only note, empty open questions, catalogue qualification, plain role names, Technical details content, hash-pinned evidence, unreadable and missing catalogue, collaborator gating). The old files are left untouched in release/rc05_scaffold_lens as the RC05e record.

## Open items flagged, not decided
1. Where the declaration block sits in the registry fixture format, and what a registry release needs. Not decided. In this build the declarations are a separate source file (`data/screen_declarations.json`) beside, not inside, registry 0.3.5 (unchanged, sha 7c31aa1d...). A registry release would have to carry them in a new registry version and re-pin the sha; I have not read the registry release procedure, so I state no steps for it. D007 step.
2. Asset record stage. Implemented as the default in the contract: the record's own noun kind K-4 (always Enable) with the Context's kind shown as a neighbour and never used for stage. Switching to `context_kind` is a one-line declaration change. Note: registry open question on N.ASSET ("Is an Asset ever itself a Context of kind K-4, or is 'Asset K-4' only the kind of the Context that holds Assets?") bears on this ruling.
3. The route ignoring context_id. Confirmed by test as current behaviour for the noun screen (empty and non-existent ids give the same screen apart from the echoed id); the id only feeds the evidence gate. Not decided whether that is intended.

## Choices to review (mine, not rulings)
- Source chip display names ("Project instr. v2.2.2", "Registry H.CTX", "Ledger", "design_d.json", "pack.md OV-02") follow the wording of the Claude Doc specimen; each is tied to a quote that exists in the registry text, but the short names themselves are authored. Where the registry text holds no date, the chip shows the name only and does not invent a date. Context's ledger date is shown as the registry holds it ("20 Nov 07:20-07:21").
- Movement HOLD reason ("noun-to-verb governance waits on the Architecture tab") is the specimen's wording, held in the declaration.
- Enhance peer rows show label, registry status, operating-source state and the definition behind a "what it is" disclosure; Qualification moved from Enhance to the Enrich Status cell (ruling 3). The installed Enhance showed qualification only when evidence was present, which in practice it was not, so no installed Enhance content is lost (checked by a golden comparison with the RC05e pages).
- `scaffold_lens.build_scaffold` is retained but no longer called by the wire. It is a retirement candidate once nothing depends on it.
- Roles: a Client-only actor still clamps to Enhance through the existing role table; the wire's table gives Steward and Collaborator Enrich, unchanged.

## Rights and gaps
- Rights: reads only, with the caller's own environment; no sudo, no writes, no raw SQL (tested). Nothing was written to dev or to V20 data. Registry 0.3.5, other 49 screens, verb binding and screen text canon are untouched.
- Gaps: no Odoo here, so the TransactionCase file and any install are unproven; the new HTML was never opened in a browser, so layout and the 390 px and 1024 px widths are UNOBSERVED; the live UI script has not been run against dev; the patch assumes the installed tree equals the RC05e tree hash above.

## Dissent
None recorded against the rulings. One observation for the Steward: the one-line-per-cell rule forces the Status cell to carry the pill and the one-line qualifier on the same line, so the Service qualifiers sit behind "+3 more"; a reader must open that disclosure to see all four. That follows ruling 5 and acceptance check 4, but it hides content the installed Enrich screen showed openly.

## Delivered versus Realised
Delivered: source candidate (patch and tree), 66 offline tests passing, UI verification script for the new structure, this return. Realised: UNOBSERVED until the Steward accepts on dev. Nothing has been installed.

## Release path (not authorised by this contract)
Install on dev needs a fresh Steward word and the dev fast path: backup, verified transfer, upgrade, restart, read-back, with the rollback patch recorded (reverse of the patch above restores tree hash 15c37960...). Production is not in scope.

## ONE NEXT
Owner: Steward. Review the three open items and the "choices to review", then say whether to take RC06a to the dev fast path; if yes, D007/Cowork installs the patch and runs ui_verify_console_rc06a_v1.js, and the result decides Realised.
