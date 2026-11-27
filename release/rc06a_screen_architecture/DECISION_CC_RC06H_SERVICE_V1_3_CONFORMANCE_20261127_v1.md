# DECISION (source-only): RC06h against adopted Service v1.3 and the Navigator quality gate (claude_code), 27 Nov 2026
Work Object WO-SYNAPSYS-CANONICAL-REFERENCE-ARCHITECTURE-001 | CTX-SS | CANDIDATE | NON_AUTHORISING
Evidence state: source read, offline tests re-run, Chromium renders of the real RC06h output in a MOCK shell; no signed-in Odoo browser test. Authority: none conferred. Implementation: nothing installed or changed on dev. PPV: no movement. Canonical revision 56 untouched. Filed status: new files only.
Independence: this review is by the same lane that builds the source. It is NOT the independent reviewer or D009 challenge; those remain open.

## Decision (one)
RETURN_DEFECTS_RC06H_FOR_SERVICE. 
1. The RC06h generic menu-page frame is kept as the base (same shared depth service, same slot builders, 43 bindings, 8 native exceptions, role refusals: all re-verified, 245/245 tests pass when re-run here).
2. RC06h is NOT conformant to Service Catalogue Master Reference v1.3 for the Service page (SCR.SERVICE.NOUN, menu 200, action 297). Per the Navigator's V3, the Service page is declared SOURCE_CONTENT_INCOMPLETE and NOT an acceptable example.
3. RC06h as it stands should not go to a dev canary. Next: a source-only RC06i limited to items C1 to C7 below, after two inputs: (a) a read-only DOM probe result from dev (script filed, needs no release), and (b) the Steward's cognitive acceptance of the filed specimen.
4. Menu renames Register / Links: agreed with the Navigator, held, separate source-module release. Not touched.

## Inputs consumed (hash recomputed from bytes by sp_read_bytes, this session)
- SERVICE_CATALOGUE_MASTER_REFERENCE_v1.3.md, 12,152 B, sha256 9079aa529d36b330951746f98cd7447999cdfc859c0c6939dbdd2f4744559612 (matches the Navigator's citation). Status in its own front matter: ADOPTED, Steward/D001; sections 1, 4, 9, 10 used.
- NAV_RC06H_ADOPTED_TEMPLATE_CONFORMANCE_AND_VISUAL_ACCEPTANCE_DELTA_20261127_v1.md, 11,936 B, sha256 a599e5af0563b97cf0ed5229ea59cb611eaf3115f26ad1c584229ab8f364d4ac (matches).
- NAV_RC06H_BUILD_RETURN_UI_QUALITY_DISPOSITION_20261127_v1.md, 7,875 B, sha256 00443fd0b51f371d77dd0b201785976e1bf60dcdc21b32bbde9dc946e7aac1ca (computed here; the review did not cite its own hash).
- Not re-hashed here, cited as given: Standalone D001 adoption 5c693657..., SCREEN_STANDARD_v1 a6ec4268..., N2 v2 index 69dab406... (candidates stay non-authorising, as the Navigator says).
- Source: repo pnyssen/synapsys-openbridge-build branch claude/synapsys-v20-release-service-tvjpyn at 2b26e9d (RC06h). Files read: addon/synapsys/screen_render.py sha256 0288fe5cc3d3214f6eb2af787cab4e3146ee63588fd9c28df2035dca0926235c; static/src/enable_panel.js 60d696a25c6dea41fca8f7f645c476bf7f846b34465df50fbd63f3df54c79edc; static/src/enable_panel.xml c4c7380f26138da58c14cbff498de054ba427eb8ed9928cc33fdb7e4ab899781; static/src/lens_mode.js 822ec7c3e6d01ce1ddedda045c044189f56b0821b67ca6ddddbac939531f369f; static/src/home.xml 03b40742268f4c6a33542dc1360892d75a5a897914d8b8d939d14e888795b3d6.
- Live read, fresh, V20 Odoo MCP (read-only jq003): x_service_catalogue = 4; synapsys.mesh.measure = 0. Agrees with the Navigator. V19's 34/29 are historical and are not shown anywhere in this decision as V20 counts.

## Reconciliation: what RC06h is, against v1.3
| Question | Finding | Basis |
|---|---|---|
| Q1 reuse | Reused: the shared `synapsys_lens_mode` service (one depth state with Context) and the same slot builders in screen_render.py. Not reused: Context's depth bar markup. The panel carries its own copy of the modebar markup in enable_panel.xml (inline styles, no 44 px rule), so there are now two copies to keep in step. | Source read |
| Q2 depth vs FFE | Not addressed. The only control is "Depth" with lowercase enable / enhance / enrich buttons. Form, Flow and Evolve appear nowhere on any page. The Service declaration has `movement.verbs = []` and no Form / Flow / Evolve field; the only Service state it carries is HOLD. v1.3 section 4 says x_ffe_state must not be inferred from placement, so grouping slots under Form / Flow / Evolve is a presentation choice that needs the Steward's cognitive acceptance, not a code decision. | Source read; v1.3 s1, s4 |
| Q3 content above records | Mechanism works in a mock shell (panel above list at 390 and 1024, no horizontal scroll). Real Odoo 20 container hierarchy is unverified: it rests on `.o_web_client` being a flex column with the panel's container as a direct child. | Chromium, mock shell, metrics file |
| Q4 phone / tablet | FAIL on two points found here, rest unverified live: (i) at 600 px or less the Source column (column 3 of the Enrich trust table) is hidden by CSS, so provenance, dates and quotes vanish on a phone; (ii) Depth buttons have no minimum height (21 px in the mock; Odoo's own btn-sm differs, unverified), against the 44 px target. | Source CSS; Chromium |
| Q5 Service content | FAIL. One registry sentence plus a made-of list; no Value band; no Form / Flow / Evolve; no source-state labelling beyond the chip. | Rendered output |
| Q6 Measures | Partial. Duplicate "CANDIDATE:" lead is gone from the page (chip carries it). The answer is the one quote "A measure stored by Mesh address"; Enrich shows dated, CANDIDATE-marked quotations that the job ships switched off and Door receipts and Measures are empty. No count is displayed; the native empty state under Records conveys 0. | Rendered output; declaration S17-S19 |
| Q7 roles | Source-tested only (refusals at every depth, role depth cap). Collaborator / Client / foreign Context on a real database: not run. | RC06h tests, re-run |
| Q8 receipt | Not yet possible: no live evidence. | n/a |

## New defect found here (not in the RC06h return): clipping NOT fixed for Measures
RC06h's R5 wraps cells in columns 2 and up but keeps column 1 (the claim label) as no-wrap with an ellipsis. Measures' Enrich claims are whole sentences, so they are cut: in Chromium at 1024 px two cells are truncated ("The job ships switched off; switching it on is your release decision"; "Empty: Door receipts and Measures. The Mesh pulse and Door jobs are switched off."), three at 390 px. This is the "clipped cells" the Steward saw. The 245 tests cannot see it (they check the CSS rule text). Service Enrich at 390 px truncates one ("Service meaning"). Method: real RC06h `menu_enable` output for action 189 and 297 at all three depths, fixture-backed registry and declarations, in a mock Odoo-shaped shell; see the metrics and repro files. Limit: fixtures, not the live registry; mock shell, not Odoo.

## Specimen (Q2: answer before any dev install)
SPECIMEN_service_1_3_1_20261127_v1.html.txt (save as .html and open). Composition: full-width Answer band (title, RULED chip, answer, source count) with Depth as a small secondary "Detail" control inside the band; three apertures Form / Flow / Evolve side by side at 1024 px and stacked at 390 px; an always-visible Value band with the five-link chain; then Records. Depth is progressive disclosure inside the apertures (Enable: one line each; Enhance: adds made-of and peers; Enrich: adds citations and open questions). Every statement is taken from the Service declaration, the registry fixture, or the fresh counts above; the Value cells say "No source declared on this screen", not a number or a claim of absence in the world. Measured in Chromium: no horizontal scroll at 390 or 1024; all buttons 44 px. Observed at 390 px: the head is about 1,190 px tall at Enhance, so on a phone the default must stay Enable (head about one screen) and Records follows below. The specimen shows the composition only; it is not installed and not accepted.
Steward cognitive acceptance needed on the specimen: (1) is Detail as a secondary control inside the Answer band right, rather than a row above it; (2) is the slot-to-aperture grouping acceptable (Form = definition and what it is made of; Flow = movement and HOLD and peers; Evolve = trust, open questions, technical, observed counts).

## RC06i bounded source-only delta (proposed; no build until the two inputs arrive)
C1 One control, server-rendered: the Depth buttons move out of enable_panel.xml into the renderer (one copy), with a delegated click handler in enable_panel.js that calls the shared service; pressed state comes from the served depth. Removes the duplicated markup; allows the 44 px rule and keyboard focus styling in one place.
C2 Service projection: a service-specific page function in screen_render.py (selected by the declaration, SCR.SERVICE.NOUN only) producing Answer band, Form / Flow / Evolve apertures, Value band, Records heading, from existing slot data only. No new declaration fields, no schema, no new route.
C3 Value band content: cells read "No source declared on this screen" unless the declaration carries a sourced value. A live Mesh Measure count is the only candidate new read (search_count on synapsys.mesh.measure under the caller's own rights, refused cleanly when not permitted); that is a new read and needs the Steward's yes before it is built. Never V19 numbers.
C4 Trust table: first column wraps; at 600 px or less the table becomes stacked rows that include Source, instead of hiding column 3.
C5 Depth buttons min-height 44 px and visible focus.
C6 Tests added: a real-browser (Playwright) layout test replacing CSS-text checks for C4 and C5, run in CI-free offline fashion with the shell shaped by the DOM probe result; the original RC06g page must fail the order test and the clipping test, RC06i must pass; fixtures for all three depths at 390 and 1024.
C7 Placement fallback decision: if the DOM probe refutes the flex-order assumption, the ActionContainer inheritance becomes necessary and needs exact Odoo 20 template text (a Steward / D007 action to obtain it from the box); I will not guess the xpath.
Out of scope: content authoring (Navigator N2), menu renames, Service data, any dev install.

## Read-only DOM probe (no release needed)
dom_probe_console_rc06h_v1.js.txt (save as .js; paste into the browser Console on dev, signed in as Steward, on Services). Writes nothing, calls no route, changes no style. It reports the panel's parent chain, `.o_web_client` children, display / order values, and a verdict line. RC06g already mounts the same main component, so it works on what is installed now. Tested here against the mock shell (verdict ASSUMPTION_HOLDS), a negative control (flex missing: ASSUMPTION_REFUTED_OR_PARTIAL) and an empty page (NO_PANEL). Running it is the Steward's or Cowork's act; nothing in this lane can run it.

## Verified versus not
Verified here: hashes above; 245/245 offline tests (re-run, log not re-filed); mock-shell render, order and overflow metrics (files below); fresh counts 4 and 0.
Not verified: anything in real Odoo 20; real registry content (fixtures used for the Service made-of list); roles on a real database; whether Odoo's `btn-sm` meets 44 px; D009 independent challenge; D007 release identity.

## Delivered versus Realised
Delivered: this decision, specimen, probe, metrics, repro script. Realised: nothing on any screen.

## Hash receipts of companion files (computed before filing)
- SPECIMEN_service_1_3_1_20261127_v1.html.txt, 4,065 B, sha256 f77cfb80b839c5945449d8b1608dee4075534e27ae0fbf4c37b82328da523f2d
- METRICS_rc06h_mockshell_20261127_v1.json, 3,812 B, sha256 9bca39302ea88503b822789e2dc070ea0b5f9e349f335bf7afd6dd4346b422e3
- dom_probe_console_rc06h_v1.js.txt, 2,200 B, sha256 6270a983c0b3e1b76150f637525683a39d1b740fd4c6eb446448aa5990676fc8
- REPRO_rc06h_mockshell_20261127_v1.txt, 4,688 B, sha256 e20a28f0e92825610f478094dabde37a9ccc8b04eca1e014c57baa11f0725a9d
Screenshots (PNG) are not filed: the Working Memory upload allowlist takes text types; their content is reproducible from the repro file. Repo copies: release/rc06a_screen_architecture/verify/rc06h_conformance/.

## ONE NEXT
Owner Steward (or Cowork on the Steward's word): run the read-only DOM probe on dev Services and paste the verdict and JSON; and say yes / no / change to the two specimen questions. Then claude_code builds RC06i (C1 to C6) source-only and returns it with the real-browser layout test. A dev canary needs its own D007-authorised release after that.
