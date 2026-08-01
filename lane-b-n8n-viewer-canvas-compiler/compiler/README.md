# Canvas Compiler (candidate)

`canvas_compiler.py` exports one function that matters: `compile_canvas(graph)`.
It takes a dict conforming to `../schema/graph_schema.json` (objects +
relationships + a required source/evidence/reality/ppv/authority/return_route
block) and returns an Obsidian JSON Canvas dict: `nodes[]`, `edges[]`, plus a
`metadata` block. It is the only renderer in this candidate — every view
profile in `view_profiles.py` (enterprise, psa, three_by_three_by_three,
nine_verbs, mesh, signal_to_asset, service_pattern_method_canonical,
work_object_queue, n8n_topology, n8n_workflow_detail, odoo_app_menu_object)
goes through it, with zero per-view branching inside the compiler itself.

## Contract enforced (fail-closed, not best-effort)

1. JSON-Schema validation against `graph_schema.json` (`jsonschema.validate`).
2. Every `relationships[].from`/`.to` must resolve to a known `objects[].id`
   — else `GraphCompileError("UNKNOWN_RELATIONSHIP_ENDPOINT: ...")`.
3. Every `objects[].id` must be unique.
4. Every relationship must carry a non-empty `verb` (rendered as the edge
   label — "verbs on edges" per the dispatch).
5. Every object AND the view itself must carry non-empty `authority` (plus
   `evidence`/`reality`/`ppv`/`source` at the view level) — else
   `GraphCompileError("MISSING_AUTHORITY_METADATA: ...")`.

No canvas is ever partially emitted on a violation — `compile_canvas` raises
before writing anything.

## Determinism

Layout is `_layout()`: objects are grouped into columns by their `group`
field (default column if absent), columns sorted alphabetically, objects
within a column sorted by `id`. This is a pure function of `(group, id)` —
independent of input list order, the clock, or randomness. Two compiles of
the same graph, or the same graph with its `objects[]` list reordered,
produce byte-identical `nodes[]`/`edges[]` (see `../tests/test_compiler.py`
`DeterminismTests`). The one legitimately-volatile field is `snapshot`
(freshness timestamp) — `structural_only()` strips it (from both the
top-level metadata and the metadata-panel node's own text) so a
freshness-only re-run can be distinguished from a real structural change,
which is this candidate's structural/visual diff strategy.

## Lifecycle distinctions

`lifecycle_state` (`active`/`held`/`superseded`/`failed`/`candidate`/
`proposed`/`retired`/`draft`) maps to an Obsidian canvas color slot
(`_LIFECYCLE_COLOR`), so superseded/retired/failed/held nodes are visually
distinguishable from active ones without reading their text.

## Fixed structural elements every compiled canvas gets

- A metadata panel node (`__source_evidence_authority_panel__`) carrying
  source/freshness/evidence/reality/PPV/authority for the whole view.
- A Home-return node (`__return_to_navigator_home__`) + edge, pointing at
  `graph["return_route"]` — direct return to Navigator, per the dispatch.

## Extending to a new view profile

Add a JSON file conforming to `graph_schema.json` under `../fixtures/`, then
one line in `view_profiles.PROFILE_SOURCE_FILE`. No change to
`canvas_compiler.py` is needed — this is what "one compiler, not ad hoc
renderers" means in practice, and it's also the seam Stream A's real
object/relationship JSON slots into once it returns (see the top-level
README's "Live vs fixture data" section).
