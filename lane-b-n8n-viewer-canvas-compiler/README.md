# Lane B — N8N Viewer and Canvas Compiler (candidate)

Built for `LANE_B_CLAUDE_CODE_N8N_VIEWER_AND_CANVAS_COMPILER_DISPATCH_v0.2.md`,
Wave `W-NAV-INT-MVP-20260802-01`, Work Object
`WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001`.

**Candidate production only.** No production activation, route replacement,
workflow update, Odoo mutation, schema, PPV, or canon movement was performed
to build this. Every N8N/Odoo tool call used to gather the data below was
read-only (`list_workflows`, `get_workflow`, `list_executions`,
`get_execution`, `search_odoo`) — no `update_workflow`, `create_workflow`,
`activate_workflow`, `deactivate_workflow`, `bind_workflow_credentials_by_id`,
`create_odoo`, `write_odoo`, or `unlink_odoo` call was made.

## What's here

```
schema/graph_schema.json        the declared adapter contract (Stream A's eventual output must conform to this)
compiler/canvas_compiler.py     the ONE compiler — deterministic, fail-closed, schema-validated
compiler/view_profiles.py       registry: profile_id -> backing fixture/live-data file
fixtures/                       11 graphs conforming to graph_schema.json (3 live, 8 labelled fixture)
viewer/n8n_viewer.py            static, read-only N8N viewer (renders fixtures/n8n_viewer_snapshot.json)
generate_canvases.py            compiles every profile to generated/*.canvas
tests/test_compiler.py          21 unittest cases: schema, link integrity, counts, determinism, fail-closed
generated/                      the compiled output — 11 .canvas files + N8N_VIEWER.html
tools_build_live_fixtures.py    reproducible record of how live N8N/Odoo tool output became fixtures/*.json
tools_build_labelled_fixtures.py   same, for the 8 explicitly-fixture (non-live) profiles
tools_build_viewer_snapshot.py  builds fixtures/n8n_viewer_snapshot.json for the viewer
```

Run it yourself:

```
python3 tools_build_live_fixtures.py       # re-derive fixtures/*.json from the embedded live capture
python3 tools_build_labelled_fixtures.py   # re-derive the 8 labelled-fixture profiles
python3 tools_build_viewer_snapshot.py     # re-derive the viewer's snapshot file
python3 generate_canvases.py               # compile all 11 profiles -> generated/*.canvas
python3 viewer/n8n_viewer.py               # render generated/N8N_VIEWER.html
python3 -m unittest tests.test_compiler -v # 21 tests
```

## Why one compiler, not per-view renderers

`compiler/canvas_compiler.py` has exactly one entry point,
`compile_canvas(graph)`. It has no knowledge of "enterprise" vs "n8n_topology"
vs any other view — that distinction lives entirely in which JSON file
`view_profiles.py` hands it. All 11 profiles (enterprise, psa,
three_by_three_by_three, nine_verbs, mesh, signal_to_asset,
service_pattern_method_canonical, work_object_queue, n8n_topology,
n8n_workflow_detail, odoo_app_menu_object) go through the same code path —
`tests/test_compiler.py::GeneratedCanvasFileTests` asserts every generated
`.canvas` file shares the identical grammar string, proving this structurally
rather than by assertion.

## Live vs fixture data — exactly what's real

| Profile | Evidence | Source |
|---|---|---|
| `n8n_topology` | `LIVE_VERIFIED` | `list_workflows(limit=50)` against the live SynapSys N8N instance — 45 workflows, all real IDs/names/states |
| `n8n_workflow_detail` | `LIVE_VERIFIED` | `get_workflow(id=7L5tLWOPTeqRzw3r)` — the real, active D007 production workflow, all 26 nodes and 25 edges |
| `odoo_app_menu_object` | `LIVE_VERIFIED` | `search_odoo(model=ir.ui.menu, domain=[parent_id.name=Govern])` — 14 real menu records under Odoo's Govern tree (scoped, not the full app/menu surface — see Boundary below) |
| `enterprise`, `psa`, `three_by_three_by_three`, `nine_verbs`, `mesh`, `signal_to_asset`, `service_pattern_method_canonical`, `work_object_queue` | `LABELLED_FIXTURE` | Small hand-authored placeholder graphs proving the compiler handles the profile. **Not** a reproduction of the real content of the existing `01_ENTERPRISE_INTEGRATED.canvas` / `02_PURPOSE_STRATEGY_ASSETS.canvas` / etc. — this lane read those files' *names* via `sp_list` but did not treat that as licence to restate canon content it never independently verified. |

Per the dispatch: *"Stream A object/relationship JSON when returned; before
then, use a declared adapter contract and labelled fixtures only."* Stream A
had not returned as of this build (`NAVIGATOR_INTEGRATED_MVP_DISPATCH_MANIFEST_v0.2.md`
listed Lane A `NOT_RETURNED`, independently re-confirmed by `sp_list` on the
wave folder immediately before this build — no
`LANE_A_CODEX_RUNTIME_REALITY_AND_INTEGRATION_GRAPH_RETURN_v0.2.md` file
exists). When Stream A returns, its output should be validated against
`schema/graph_schema.json` and, if it validates, dropped straight into
`view_profiles.PROFILE_SOURCE_FILE` in place of the current fixture files —
`compile_canvas()` itself needs no change, which is the point of the adapter
contract: Stream A's data is consumed without semantic remapping.

## N8N viewer

`viewer/n8n_viewer.py` renders `fixtures/n8n_viewer_snapshot.json` (built by
`tools_build_viewer_snapshot.py` from the same live capture as the canvases)
into `generated/N8N_VIEWER.html`: overview (identity/state/version/triggers/
target systems for all 45 workflows), single-workflow topology (D007, all 26
nodes with per-node credential/authority), execution trace (both real
executions on the D007 workflow — the successful adoption run 1392 and the
correctly-rejected replay attempt 1393), security/authority surface (the
transport-auth gap this lane already found and filed independently in
`NAVIGATOR_MVP_CLAUDE_CODE_D007_WORKFLOW_VALIDATION_RETURN_v0.1.md`), and
receipts/superseded-workflow lineage (the 5-workflow D007 supersession chain,
plus two other retired/archived workflows, all derived from fields actually
present in the live response — `isArchived`, self-declared `[RETIRED — ...]`
name text, or `active` flag — not invented).

The viewer makes **no** N8N or Odoo call itself and holds no credential — it
only formats a snapshot file that was built from calls made in this session.
Per the presentation rule, the HTML page is explicit white-background/
dark-text (no dark-mode CSS), states in its own banner that it is a
**temporary candidate specimen, not the current Navigator control surface**,
and links back to Navigator Home
(`Obsidian/00_HOME.md` → `NAVIGATOR_MVP_v0.2/NAVIGATOR_MVP_PRIMARY_HOME_CANDIDATE_v0.2.md`).

## Fail-closed behaviour (tested, not just claimed)

`compile_canvas()` raises `GraphCompileError` — refuses to emit any canvas —
on: JSON-Schema validation failure, a relationship referencing an unknown
object id, a relationship with an empty verb, a duplicate object id, or any
object/view missing its `authority` field. `tests/test_compiler.py` exercises
every one of these paths directly (`SchemaValidationTests`,
`LinkIntegrityTests`).

## Determinism (tested, not just claimed)

`tests/test_compiler.py::DeterminismTests` proves, for every one of the 11
profiles: (a) compiling the same graph twice yields byte-identical
structural output; (b) reordering the input `objects[]` list does not change
the compiled output (layout is a pure function of `(group, id)`, not input
order); (c) changing only the `snapshot` timestamp — the one field a live
re-run is expected to advance — does not change anything else, including the
line inside the metadata panel node's own text that displays it (both the
top-level `metadata.snapshot` field and that text line are scrubbed by
`structural_only()` before comparison). This is the compiler's structural
diff strategy: a future consumer can hash `structural_only(canvas)` to
distinguish a real content change from a freshness-only re-run.

## Boundary / what this candidate does NOT claim

- The Odoo view covers only the `Govern` menu subtree (14 records) as a live
  demonstration, not the full app/menu/object surface — enumerating that
  fully was out of scope for this candidate pass.
- The 8 non-live profiles are structural placeholders, not governed content.
- Current Navigator (`Obsidian/00_HOME.md` and everything it points to) was
  read but never written to. This candidate creates no file inside
  `Obsidian/10_WORKSPACES/NAVIGATOR_MVP_v0.2/` and does not touch
  `CURRENT_DELIVERY.md`.
- No N8N workflow, Odoo record, schema, PPV, or canon state was mutated to
  produce anything in this directory.
