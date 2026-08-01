# Overnight Stream B — Integrated Candidate Navigator Generation System

Built for `OVERNIGHT_STREAM_B_CLAUDE_CODE_INTEGRATED_COMPILER_DISPATCH_v0.1.md`
(SHA-256 `6bb0415d2faa2b512b5d72d85025b03e186f580ad9205917ba736bf6447c60ac`,
7,013 bytes — independently recomputed and byte-count-cross-checked against
`sp_list` before execution), Wave `W-NAV-INT-MVP-20260802-01`, Work Object
`WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001`.

**Candidate build only.** No Navigator promotion, Obsidian front-door
replacement, Odoo/N8N mutation, workflow activation, schema/menu change,
credential/ACL change, PPV movement, canon promotion, or Service/Pattern/
Method/asset mutation was performed. Current Architecture v1.2, the current
Obsidian Home, and all 15 accepted canvases were read but never written to —
confirmed by never calling anything but `sp_read`/`sp_list` against those
paths this session, and by `NoCompetingHomeTests`/`ManifestIntegrityTests`
in `tests/test_integrated.py`.

## What this is

Continues the consumed Lane B build (`lane-b-n8n-viewer-canvas-compiler/`,
commit `86ffa850a92f23e5f35436b66e4d0063e1662ccd`) without redesigning it —
every file in that directory is imported, read, and reused; **none is
edited**. This directory adds an SCVS v0.2.1 rendering layer (consumed from
Lane C) on top, and uses the combination to regenerate the accepted Canvas
suite, the 11 Lane B profiles, and the N8N viewer as one coherent candidate
set, plus a candidate Architecture v1.3 shell.

## Layout

```
schema/graph_schema_v0.2.json     additive extension of Lane B's v0.1 contract (optional evidence/ppv/owner_lane/source_tag)
scvs/scvs_compiler.py             the ONE compiler: imports Lane B's compile_canvas() unmodified, adds the SCVS chip-line pass
scvs/stream_a_adapter.py          StreamAAdapter — bounded contract + refusing stub (Stream A has not returned)
adapters/accepted_canvas_raw_capture.py   byte-faithful capture of the 15 accepted canvases, read live this session
adapters/existing_canvas_adapter.py       ONE generic function: accepted canvas -> graph_schema_v0.2 (all 15, no per-canvas branching)
architecture/architecture_v1_2_raw_capture.html   reference capture of v1.2 (build input only, see its own header comment)
architecture/build_architecture_v1_3.py   derives the v1.3 candidate shell via fixed, fail-closed string substitutions
viewer/n8n_viewer_scvs.py         SCVS-rendered N8N viewer, reusing Lane B's live-sourced snapshot data unchanged
build_overnight_candidate.py      builds all 15 candidate canvases + 11 candidate profiles
fixtures_canvas_suite/*.json      the 15 adapted graphs (inspectable, re-buildable)
fixtures_live/*.json              the 11 re-derived Lane B profile graphs
generated/                        all compiled output — see below
tests/test_integrated.py          26 tests: schema, link/route, determinism, accessibility, white-bg, no-competing-home, Stream A adapter, manifest integrity
INVERSION_AND_DELETION_LOG_v0.1.md  step-6 inversion/challenge findings and what was deleted or disclosed
```

Run it yourself:

```
python3 build_overnight_candidate.py         # 15 candidate canvases + 11 candidate profiles
python3 viewer/n8n_viewer_scvs.py             # SCVS-integrated N8N viewer
python3 architecture/build_architecture_v1_3.py  # candidate Architecture v1.3 shell
python3 -m unittest tests.test_integrated -v  # 26 tests (run AFTER the three builds above and the manifest, see TEST_REPORT.md)
```

## Generated output (`generated/`)

- `SYNAPSYS_NAVIGATOR_MVP_ARCHITECTURE_v1.3_CANDIDATE.html` — the candidate shell.
- `candidate_canvases/*_CANDIDATE.canvas` — 15 files, one per accepted canvas (01–15).
- `candidate_profiles/*.canvas` — 11 files, the Lane B view profiles re-derived with SCVS grammar.
- `N8N_VIEWER_CANDIDATE.html` — SCVS-integrated read-only N8N viewer.

## One compiler, still

`scvs.scvs_compiler.compile_canvas_scvs()` is the single function every one
of the 26 `.canvas` outputs passes through. It does not reimplement
Lane B's node/edge/metadata grammar — it imports
`lane-b-n8n-viewer-canvas-compiler/compiler/canvas_compiler.py` **unmodified**
(that file's own row in Lane B's consumed manifest,
`LANE_B_CANDIDATE_BUILD_v0.2/CANDIDATE_MANIFEST_SHA256.csv`, is untouched by
this build) and adds exactly one additional pass: an SCVS chip line appended
to every object node's text. Fail-closed behaviour (unknown relationship
endpoints, missing authority, arrow-notation return routes) is inherited
unchanged from Lane B — `LinkAndRouteTests.test_arrow_notation_return_route_fails_closed`
proves it still fires through the new wrapper.

## Adapted vs live vs fixture — exactly what's real in the 26 candidate canvases

| Source | Count | Evidence label | What it means |
|---|---|---|---|
| Accepted canvas suite (01–15), adapted | 15 | `ADAPTED_FROM_ACCEPTED_CANVAS` | Every node/edge/id/label is taken directly from the live-read accepted `.canvas` file; `lifecycle_state` is a deterministic keyword scan (SUPERSEDED/HELD/CANDIDATE/else active) over the original text — see `adapters/existing_canvas_adapter.py` docstring for the exact rule. The originals are **unchanged**. |
| N8N topology, N8N workflow detail, Odoo Govern menu | 3 | `LIVE_VERIFIED` | Unchanged from Lane B's own live capture (workflow list, D007 topology, Odoo `ir.ui.menu` under Govern) — reused, not re-fetched. |
| Enterprise / PSA / 3x3x3 / nine verbs / Mesh / Signal-to-Asset / Service-Pattern-Method-Canonical / Work-Object-queue | 8 | `LABELLED_FIXTURE` | Unchanged from Lane B's own labelled placeholder fixtures — still explicitly not claiming to be governed content. |

## StreamAAdapter — the bounded seam (dispatch requirement)

`scvs/stream_a_adapter.py::adapt_stream_a_payload()` is the one place a real
Stream A payload will be mapped into `graph_schema_v0.2`'s shape. As of this
build, Stream A has **not** returned — verified directly this session
against `NAVIGATOR_INTEGRATED_MVP_DISPATCH_MANIFEST_v0.7.md` (Lane A state
`TOOL_BLOCKED`, controller disposition `HELD_WM_TO_CODEX_TRANSPORT`). Calling
the function with no payload raises `StreamANotReturnedError` — this is
intentional and tested (`StreamAAdapterTests.test_adapter_refuses_when_no_payload`),
not a stub that silently returns empty data. No Stream A data is fabricated
anywhere in this build; every one of the 26 canvases is `ADAPTED_FROM_ACCEPTED_CANVAS`,
`LIVE_VERIFIED`, or `LABELLED_FIXTURE` — never a guessed Stream A shape.

When Stream A returns, only the body of `adapt_stream_a_payload()` needs to
change to match its real field names — nothing downstream (the compiler, the
15 canvases, the 11 profiles, the viewer, the tests) needs to change, because
they all already consume the same `graph_schema_v0.2.json` contract
regardless of where the data originated.

## SCVS integration — what was actually implemented vs what's a known gap

Implemented, tested: chip-line grammar (owner lane, lifecycle border word,
evidence, PPV, authority, optional STOP/HOLD) on every object node in every
one of the 26 `.canvas` outputs and in the N8N viewer's cards; verb-labelled
edges (inherited from Lane B, unchanged); white-background/dark-text on both
HTML outputs, no dark-mode CSS; source corner tags (`[N8N]`/`[ODOO]`) on the
three live profiles.

Known gap, disclosed not hidden: Obsidian Canvas JSON nodes have no native
border-style property (only fill colour) — SCVS's lifecycle border grammar
is therefore expressed as `BORDER: <word>` text inside the chip line for
`.canvas` outputs (not an actual dashed/dotted/double border), while the
N8N viewer HTML (which does support CSS `border-style`) renders it as a real
border. This is a real constraint of the Obsidian Canvas file format, not an
oversight — and it's exactly why the chip line's text also states it, so
nothing in a `.canvas` output depends on colour alone even without a real
border-style.

## Link/route testing (dispatch step 5)

Every generated canvas's `return_route` is the single clean candidate v1.3
path (no arrow notation — enforced at both the schema-pattern and
code-check layers, inherited from Lane B's Correction v0.1). Every HTML
`href`/`src` is checked for arrow notation and Mac-absolute paths. The three
`COMPONENTS/*.html` iframe sources on the Architecture v1.3 shell are a
**disclosed, named exception**: they are vault-relative by original v1.2
design (this candidate is meant to be evaluated for eventual placement at
the same vault location as v1.2, not as a fully freestanding Working-Memory-
hosted page) — they will not resolve if this HTML file is opened directly
from its Working Memory filing location. This is stated here and allow-
listed by name in `tests/test_integrated.py`, not silently passed.

## Boundary / what this candidate does NOT claim

- Current Architecture v1.2 (`Obsidian/00_SYSTEM/NAVIGATOR_SUPPORT/CURRENT/SYNAPSYS_NAVIGATOR_MVP_ARCHITECTURE_v1.2.html`) is unchanged — read, never written.
- The 15 accepted canvases (`Obsidian/10_WORKSPACES/NAVIGATOR_MVP_v0.2/*.canvas`) are unchanged — read, never written.
- No file in `generated/` declares itself current, implemented, or promoted.
- No new Home, dashboard, or wave-control page was created — one tab was added to the existing v1.3 shell.
- No N8N/Odoo mutation call was made this session beyond the read-only calls already disclosed in this README and the return packet.
