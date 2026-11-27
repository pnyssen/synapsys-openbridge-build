# RETURN: RC06i Service 1-3-1 layout and menu-page correction, source-only candidate (claude_code), 27 Nov 2026
Work Object WO-SYNAPSYS-CANONICAL-REFERENCE-ARCHITECTURE-001 | CTX-SS | CANDIDATE | NON_AUTHORISING
Contract: BUILD_CONTRACT_SERVICE_1_3_1_LAYOUT_CORRECTION_RC06I_20261127_v1.md, 10,597 bytes, sha256 d8240b5f1a020032af901c98da3830e1f083aaa35e2d316f097576ee9d8b993b (read with sp_read_bytes; hash matched).
Evidence state: offline tests and a real-browser (Chromium) matrix in a MOCK Odoo-shaped shell; live tests: none. Authority: none conferred. Implementation: source built, NOT installed, no dev contact. PPV: no movement. Canonical state revision 56 untouched. Filed status: new files only.
Replay: RC06I_CONTRACT_SOURCE_ONLY__NAV_CORRECTIONS_CONSUMED__NO_INSTALL__STATE56_UNCHANGED

## Result in one line
All of R1 to R9 are built and pass in the browser matrix (Service 297, Measures 189, one RULED noun; 390 and 1024 px; Enable, Enhance, Enrich); the same checks fail on RC06g and RC06h as the contract requires. R8 is not blocked (probe: ASSUMPTION_HOLDS) but the probe showed the placement alone is not enough, so I changed how the page scrolls (see Mechanism). No stop condition was hit: no new read, route, schema, ACL or menu, and no Code-authored Service prose.

## 1. Consumption and readback receipt (hashes recomputed from SharePoint's own bytes; sp_read_bytes for the contract, sp_finalize_upload read-back for the rest)
| Input | Bytes | sha256 | Result |
|---|---|---|---|
| BUILD_CONTRACT_SERVICE_1_3_1_LAYOUT_CORRECTION_RC06I (this contract) | 10,597 | d8240b5f1a020032af901c98da3830e1f083aaa35e2d316f097576ee9d8b993b | MATCH |
| BUILD_CONTRACT_SCREEN_ARCHITECTURE_RC06A | 5,898 | f971598aa9d4b2d67dd1715edda5dd0b0ac0efa70177538e8076fe8e809f70c5 | MATCH |
| BUILD_CONTRACT_MENU_PAGE_LAYOUT_LENS_TEMPLATE_BATCH7_RC06H | 5,702 | eca46e084a46bd0d4b6cc2f4cd5407357ac603b54d1b0ccbf88a49dc2adb796d | MATCH |
| SERVICE_CATALOGUE_MASTER_REFERENCE_v1.3.md (05_AI_RETURNS_HASHED/) | 12,152 | 9079aa529d36b330951746f98cd7447999cdfc859c0c6939dbdd2f4744559612 | MATCH (read in full; s1, s4, s9, s10 used; front matter says ADOPTED, Steward/D001) |
| NAV_RC06H_ADOPTED_TEMPLATE_CONFORMANCE_AND_VISUAL_ACCEPTANCE_DELTA | 11,936 | a599e5af0563b97cf0ed5229ea59cb611eaf3115f26ad1c584229ab8f364d4ac | MATCH (read in full) |
| NAV_RC06H_BUILD_RETURN_UI_QUALITY_DISPOSITION | 7,875 | 00443fd0b51f371d77dd0b201785976e1bf60dcdc21b32bbde9dc946e7aac1ca | MATCH |
| DECISION_CC_RC06H_SERVICE_V1_3_CONFORMANCE (contract gives no hash) | 12,253 | 1ce48f8cd54a7f69287ae02f378ae0780ea7a7c85b4e793005d66d273c7bb887 | COMPUTED; the repo copy at c5496a6 has the same bytes and hash |
| SPECIMEN_service_1_3_1_20261127_v1.html.txt | 4,065 | f77cfb80b839c5945449d8b1608dee4075534e27ae0fbf4c37b82328da523f2d | MATCH (repo copy identical) |
| METRICS_rc06h_mockshell_20261127_v1.json | 3,812 | 9bca39302ea88503b822789e2dc070ea0b5f9e349f335bf7afd6dd4346b422e3 | MATCH (truncated "9bca3930..." completed; repo copy identical) |
| dom_probe_console_rc06h_v1.js.txt | 2,200 | 6270a983c0b3e1b76150f637525683a39d1b740fd4c6eb446448aa5990676fc8 | MATCH (truncated "6270a983..." completed; repo copy identical) |
| RETURN_COWORK_DOM_PROBE_RC06G_DEV_SERVICES (added by the Steward in chat) | 2,255 | f69e3c93a27e13c5df7bc883b20414b345f4d12e8cbc27ae147fcdac6076635f | MATCH (read in full) |
| NAV_N2_..._45_SLOTS_20261127_v2.json | 541,891 | 69dab4060d9d9fd13d8e585e3af9023c7a595123291c810e96b37abe4c334c21 | MATCH (hash only; not read: candidate, not promoted, nothing built from it) |
| MESH_QUEUE/KIT/SCREEN_STANDARD_v1.md | 2,682 | a6ec4268e3ec17c75fa90c742f2ccd8641000945d623112a3897909d5d538598 | MATCH to the contract's "a6ec4268..." (completed; candidate, only its 14/12/10 hierarchy is used, for Service, under v1.3) |
| NAVIGATOR_ALL_LEVELS_..._v0.3_CANDIDATE.md (Obsidian/00_SYSTEM/DESIGN_STANDARDS/) | 7,978 | 2f2188d2cc8ab8ad8044ddc07254c6b6fbf04a4f0dd970197615faa6f3919c99 | MATCH to "2f2188d2..." (completed; candidate, not promoted) |
| STATE_v56.json (WO-SYNAPSYS-CANONICAL-REFERENCE-ARCHITECTURE-001/STATE_CONTROL/) | 16,545 | d2de2edbaece0f780ea603a5acf6dc21b54c56cb5bb589c1f01118dc9c09b269 | MATCH; consumed, unchanged. Other WOs also hold a STATE_v56.json; this is the one in this work object's folder |
| D001 adoption 5c693657b6a1a15b541c3126f33e1ee3facd3e35079fc87288b91a84bf7edd77 | not located | | UNVERIFIED: the Navigator cites path WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001/D001_DECISIONS/...; I did not open it. v1.3 itself states ADOPTED |
| Navigator RC06i corrections message (19:19 Brisbane) | | | UNVERIFIED, as the contract says: pasted in chat, not filed; I built from the contract's own R1 to R9 |
Hash methods differ only in how bytes were obtained; all were computed by the SharePoint tool over its stored bytes, not taken from a citation.
Repo state consumed: branch claude/synapsys-v20-release-service-tvjpyn. Local HEAD was 2b26e9d; origin had two later commits, e5322c9 (gitleaks allowlist; addon identical to 2b26e9d, tree 5671fcaf…) and c5496a6 (RC06h decision, specimen, probe, mock-shell metrics, files only under verify/ and one .md). I fast-forwarded to c5496a6 (no force, no rebase) and built on it. Contract/prompt asked for patches against 88eb331 (what is installed on dev) and e5322c9; both are given.

## 2. Commits, tree, patches
- Base commits: 88eb331 (RC06g, installed on dev, addon tree 2ab96fd52ace9dee2b7cf0f388f805a7232a4addabfed22ca355291983a4017b) and e5322c9 (RC06h + allowlist, addon tree 5671fcafea9009845ee97b1fc511c335846a7bc38723ef302355457509ac5433, 69 files). Parent of the RC06i code commit: c5496a6.
- RC06i code commit: 169b1b54469d3530c807d64f378abcb1fdd471bf (source, tests, verify evidence). A second commit adds this return and the two patches; its id is in the push report (a commit cannot name its own hash).
- Addon tree hash, method rc04g_baseline_hash_20261126_v3.sh (file list sha of release/rc06a_screen_architecture/addon/synapsys, excluding caches): 69 files, 7df241359197b2b191db513e2e7ea871584c0a1abefd694dfd613f10d4ae5eae.
- Cumulative patch against 88eb331 (installable on the current dev tree): RC06i_service_1_3_1_cumulative_vs_88eb331.patch, 21,785 bytes, sha256 66565c3a511f314a27caaf9c8dc8259c734d1aca8d353390213101cb50d101a6. `git apply --check -p1` passed on a clean extract of the 88eb331 addon tree; applying it gave tree 7df24135… (69 files).
- Incremental patch against e5322c9: RC06i_service_1_3_1_incremental_vs_e5322c9.patch, 17,491 bytes, sha256 108a23dc1794776716583b557c6ad76fd755566e67dcd08a928cb15d7a1ef788. `git apply --check -p1` passed on a clean e5322c9 extract; applying it gave the same tree 7df24135….
- Changed addon files vs RC06h: screen_render.py, static/src/enable_panel.js, static/src/enable_panel.xml. Nothing else (scaffold_wire.py, controllers, views, security, models, data, manifest byte-identical; proved by file hash against tests/golden/rc06h_tree_manifest.json). So there is no new read, route, schema, menu, ACL or declaration. Patches use the same format as the earlier ones (apply with -p1 in the directory that holds synapsys/).

## Mechanism (what the probe changed)
The probe on dev showed body.o_web_client is a viewport-height flex column (navbar 46 px, a flexible .o_action_manager with overflow hidden, then .o-main-components-container holding the panel). RC06h's flex order put the panel above the list but squeezed the list into a small scroll area and needed an inner 60vh scroll to hide it. RC06i: while a menu page is on screen (CSS :has(.syn-pg); the rules travel with the page html, so nothing else changes) the container is ordered before the action manager, the web client grows to its content, and the page scrolls as ONE page; the native view keeps a full-height area under the Records heading. There is no scroll container inside the panel (R6: removed, not defended). I also found and removed a 48 px padding band between the Records heading and the view. Rejected: ActionContainer template inheritance (not needed now; a wrong xpath breaks every backend asset, and I do not have Odoo 20's text).

## What was built (R1 to R9)
- R1 One control. detail_control() in screen_render.py renders the Detail control once on the server (role=group, aria-label "Detail level", three buttons with aria-pressed following the served depth, 44 px targets, visible focus ring). enable_panel.xml lost its modebar; enable_panel.js has one delegated click handler that calls the shared synapsys_lens_mode service. No second depth state.
- R2 Service projection. render_service_page(), selected only by SCR.SERVICE.NOUN (menu 200, action 297): Answer band (title, status chip, answer, source count, Detail control), Form / Flow / Evolve apertures, Value band, then the Records heading and the native view. Form = definition source line (+ made-of at Enhance); Flow = movement/HOLD (+ peers at Enhance); Evolve = trust line (+ open questions, trust table, technical at Enrich). These are perspective groupings, not x_ffe_state; nothing is inferred. A slot with no source says so ("No linked peers are declared for this screen.", "No registry source is declared for this screen."). Other pages keep the generic frame, with the Detail control directly after the answer.
- R3 Value band, always visible at every depth: a labelled definition of the value chain from v1.3 s1 (Service performance, Outcome, Verified Benefit contribution, Realisation, Enduring Asset effect) and ONE statement: "Benefits and Assets recorded against this Service are not read on this screen." No counts, no V19 numbers, no claim that the world has none.
- R4 14 / 12 / 10 px, Service projection only (computed sizes in the browser are exactly {14, 12, 10}); the specimen's 22 / 15 / 17 are gone. Other screens and Context CSS are unchanged.
- R5 On every menu page the trust table wraps (no nowrap, no ellipsis) and at 600 px and below becomes stacked rows labelled Claim / Status / Source / Open question; Source is never hidden. Expanders (summary) are 44 px targets.
- R6 No inner scroll. Service Enable at 390 px: Records heading ends at 844 px or less in the mock shell (measured 838 px incl. the 46 px navbar); Enhance and Enrich are taller and the page scrolls as one.
- R7 Measures: the answer is the row's own words ("A measure stored by Mesh address"), status chip CANDIDATE, lead stays removed; plus "Observations: not available on this screen. No stored measure is read here; the native list under Records shows what exists." and "Owner: none declared on this screen."; HOLD and the declared route (movement line) as before. No count query, no chart, no new read (proved: no registry, catalogue or count call is made). Native model synapsys.mesh.measure and action 189 preserved.
- R8 Placement as above; verdict from the probe consumed. The mock shell is structural evidence, not proof of correct placement in Odoo.
- R9 Preserved: 43 bindings, 8 native exceptions, entitlement order and reason-only refusals, shared depth service, role depth cap.

## 3. Reused template components (reused versus new)
| File | sha256 | Status |
|---|---|---|
| addon/synapsys/screen_render.py | 60312b8624a77da99a97fafbbee84e87bfee8bcf789c70d308fb6b8cb3fc4252 | reused: STYLE, SLOT_BUILDERS, all slot builders, status chips, the trust table; modified: PAGE_STYLE, detail_control, render_menu_page, new render_service_page |
| addon/synapsys/static/src/lens_mode.js | 822ec7c3e6d01ce1ddedda045c044189f56b0821b67ca6ddddbac939531f369f | reused unchanged (the one shared depth state) |
| addon/synapsys/static/src/home.xml | 03b40742268f4c6a33542dc1360892d75a5a897914d8b8d939d14e888795b3d6 | reused unchanged (Context/Lenses modebar; not copied) |
| addon/synapsys/static/src/enable_panel.js | 4207a915ee645a703e7f9716811b3b122c1f894af77c1c959ce453ba6b891433 | modified: one delegated handler |
| addon/synapsys/static/src/enable_panel.xml | dff52fa731ecd2707fe647ec4a0f716255f3d02b0d296e200867b75a126fb0b9 | modified: modebar removed |
| addon/synapsys/scaffold_wire.py | f6a64c5012c66ca38547479fa8e9e91753a6e89198efd7a30f7f041c353347a5 | unchanged from RC06h |
Confirmed: one depth state (synapsys_lens_mode), no second copy; the Detail control exists once, in the server render.

## 4. Original-failure regression (same checks, each version's real route output, mock shell; failures / cases run; RC06g serves only Enable, so its Enhance and Enrich cases cannot be rendered at all)
| Check | RC06g 88eb331 | RC06h e5322c9 | RC06i |
|---|---|---|---|
| DOM order (Answer, apertures, Value, Records, native view) | 6/6 fail (panel below the view) | 13/18 fail | 0/18 |
| No truncated cell / no ellipsis (first-column clipping) | n/a (no table) | 6/18 fail | 0/18 |
| Source visible at 390 px (Enrich) | n/a | 3/18 fail (column hidden) | 0/18 |
| One accessible Detail control (in the Answer band for Service) | 6/6 fail (missing) | 14/18 fail | 0/18 |
| Every target >= 44 px | 6/6 fail | 18/18 fail (21 px) | 0/18 |
| No scroll container in the panel | 0/6 | 18/18 fail (60vh) | 0/18 |
| Native list not squeezed (dev's viewport-height column) | 6/6 fail | 18/18 fail | 0/18 |
| Records heading adjacent to the native view | 6/6 fail | 7/18 fail | 0/18 |
| All content reachable by page scroll | 0/6 | 7/18 fail | 0/18 |
| Form / Flow / Evolve apertures (Service) | 2/2 fail | 6/6 fail | 0/6 |
| Value band at every depth (Service) | 2/2 fail | 6/6 fail | 0/6 |
| Computed 14 / 12 / 10 (Service) | 2/2 fail | 6/6 fail | 0/6 |
| Enable head within 844 px at 390 | 3/3 fail | 0/3 | 0/3 |
| No horizontal scroll | 0/6 | 0/18 | 0/18 |
Keyboard Tab reaches the control and shows a focus ring: RC06g fails (no control), RC06h and RC06i pass. The required failures (first-column clipping, hidden Source at 390, no FFE apertures, no Value band, missing or duplicate single control, nested scroll) all fail on RC06h or RC06g and pass on RC06i.
Test counts: old 245; now 270 (245 + 1 client click test in test_batch5, + 18 in test_batch8, + 6 real-browser tests in test_layout_browser). All pass, none skipped, in this container (log TEST_LOG_rc06i_service_1_3_1_offline.txt, sha256 8c0369163d255e2788f9f72199ecb07b143054cd1adfbf1848773c01b4a59f7c). The browser tests are skipped (never passed) if node, Chromium or the older commits are missing.
Mutation checks, each caught: a second depth control in the client template, the 60vh scroll restored, first-column clipping restored, Source hidden at 390 again, a 22 px title, the Value band dropped at Enable, the 48 px band restored, 20 px targets, the order rule removed (panel at the foot), the web client left at viewport height (list squeezed), the focus ring removed, the apertures dropped.
Assertions changed (R9): test_screen_arch check 15 ("no screen has its own slot code") now excludes the Service projection's own function bodies and constants, because R2 requires exactly that one screen-selected function; everything else in the renderer is still checked. test_batch5: the "panel holds only the four frame slots" test now states the per-screen slot lists (Service, Measures, others) and requires exactly one Detail control; the client "tabs" test now checks that the modebar is gone and one handler exists; the node harness gained the click cases. test_batch7: the "Depth:" label is not required on the Service page; the slot-order lists were extended for the Service and Measures pages; two CSS-text tests were rewritten for the new placement rules (they were never layout proof; the browser matrix replaces them) and one Records CSS string was updated. No refusal, binding or entitlement assertion was changed.

## 5. Rendering evidence (MOCK SHELL; not signed-in Odoo)
Committed under release/rc06a_screen_architecture/verify/rc06i_service_1_3_1/: evidence/rc06i_mockshell_matrix_v1.json (all metrics for the three versions), evidence/screenshots_rc06i/*.png (Service, Measures at Enable and Enrich, 390 and 1024), screenshots_rc06h (Service Enable and Enrich) and screenshots_rc06g (Service Enable) for comparison, evidence/shell_rc06i/*.html. matrix JSON sha256 59a1f62452849d034f428eed87c7f3ab2e4fe4f59e9344022de1416a3ed09862. Repro, from the repo root: `python3 release/rc06a_screen_architecture/verify/rc06i_service_1_3_1/run_matrix.py /tmp/rc06i_matrix` and `cd release/rc06a_screen_architecture/tests && python3 -m unittest test_layout_browser`. Viewports 390 x 844 and 1024 x 854; the shell uses the probe's real structure and heights (navbar 46 px, flexible action manager with overflow hidden, main-components container).

## 6. Fixed UI strings (all of them; everything else on a page comes from the declaration, the registry projection or a source row)
Detail, Enable, Enhance, Enrich, Detail level (aria-label), Form, Flow, Evolve, Value, Records; "SynapSys: definition and alignment"; "Disciplines: operation and movement"; "Mesh: evidence, learning and value realisation"; "Definition source: registry <version>, <state>."; "No registry source is declared for this screen."; "Trust: <status> <n source(s)>."; "Definition of the value chain, from the Service Catalogue Master Reference v1.3. It is not a record of this Service."; the five chain labels Service performance, Outcome, Verified Benefit contribution, Realisation, Enduring Asset effect (v1.3 s1); "Benefits and Assets recorded against this Service are not read on this screen."; "Observations: not available on this screen. No stored measure is read here; the native list under Records shows what exists."; "Owner: none declared on this screen."; trust-table stacked labels Claim, Status, Source, Open question; "Binding: <status>."; "Presentation only: this view changes no data, kind, PPV, approval or right." Carried over from RC06h and earlier (unchanged): "No linked peers are declared for this screen.", the depth note sentences on non-Service pages, and the existing slot headings. A test checks that no other prose literal exists in the new functions.

## 7. Offline versus live; remaining live gaps
Offline and run: 270 tests; browser matrix (Chromium, mock shell) at 390 and 1024 px; mutation checks; patch apply checks on clean extracts.
Live and NOT run: real Odoo 20 placement (the shell copies the probe's structure, not Odoo's CSS; if Odoo's own stylesheet overrides `height:auto` on the web client, the page would not grow and the squeeze would return); mobile navbar height (the 46 px in the rule `calc(100vh - 46px)` is the desktop probe value; the mobile navbar differs and was not measured); Odoo's real btn-sm and any Odoo CSS that restyles the Detail buttons; signed-in 390 and 1024 px screenshots; Collaborator, Client and foreign-Context behaviour on a real database; real registry and catalogue content (the fixtures stand in); effective read rights on the real database; restore and rollback. A dev canary needs its own D007 release; nothing here was installed.

## 8. Open dissent and pending
- Steward cognitive acceptance of (1) the Detail control inside the Answer band and (2) the slot-to-aperture grouping (Form = definition source and made-of; Flow = movement/HOLD and peers; Evolve = trust, open questions, technical). The Evolve trust line repeats the status and source count that the Answer band already shows, as in the specimen; the Steward may prefer it removed.
- At 1024 px Enrich, Form and Flow sit in two of three columns and Evolve spans the row below, leaving one empty cell; this is a presentation choice to confirm.
- 10 px text (aperture captions, notes) is what the adopted hierarchy specifies; it is small on a phone.
- The 48 px page-level change is a CSS override scoped to menu pages (:has(.syn-pg)); if Odoo's own rules win, the effect is the RC06h behaviour again, which is visible, not silent.
- D009 independent challenge and D007 release are open; this return is by the same lane that builds the source and is not independent review. The N2 content for the other 45 screens is the Navigator's, not built here.
- Menu renames (Register / Links) stay held.

## 9. ONE NEXT
Owner: Steward or CoWork on the Steward's word. Re-run the read-only DOM probe on dev Services only after a D007-authorised dev canary of the cumulative patch (sha256 66565c3a…); until then no step is needed on dev. If a canary is authorised: open Services and Measures as Steward at 390 and 1024 px and report whether the page head sits above the list, the list is a normal size under the Records heading, and the page scrolls as one.
