# Lane B — Schema / Link / Count / Determinism Test Report

Environment: `python3 -m unittest tests.test_compiler -v`, run from
`lane-b-n8n-viewer-canvas-compiler/`, this session, immediately after
`generate_canvases.py`.

**Result: 21/21 PASSED. Exit code 0. No skips, no expected failures.**

```
test_edge_count_is_relationships_plus_one_return_edge ... ok
test_every_profile_node_and_edge_count_matches_its_source_graph ... ok
test_node_count_is_objects_plus_two_fixed_panels ... ok
test_every_profile_is_deterministic_across_two_compiles ... ok
test_identical_input_produces_identical_structural_output ... ok
test_object_input_order_does_not_affect_output ... ok
test_snapshot_only_change_does_not_affect_structural_output ... ok
test_all_generated_canvas_files_share_one_grammar ... ok
test_required_deliverables_exist_and_are_valid_json_canvas ... ok
test_compiled_edges_all_resolve_to_compiled_nodes ... ok
test_missing_verb_fails_closed ... ok
test_unknown_relationship_from_fails_closed ... ok
test_unknown_relationship_to_fails_closed ... ok
test_every_fixture_file_conforms_to_the_declared_schema ... ok
test_schema_loads_and_is_valid_json_schema ... ok
test_duplicate_object_id_fails_closed ... ok
test_empty_object_authority_fails_closed ... ok
test_invalid_lifecycle_state_fails_closed ... ok
test_missing_object_authority_fails_closed ... ok
test_missing_required_top_level_field_fails_closed ... ok
test_valid_graph_passes ... ok

Ran 21 tests in 0.708s
OK
```

## Coverage against the dispatch's five test categories

| Category | Test class(es) | What's proven |
|---|---|---|
| Schema | `SchemaValidationTests`, `SchemaFileTests` | Valid graphs pass; missing/empty/invalid required fields (top-level or per-object) are rejected; every one of the 11 fixture files actually conforms to `graph_schema.json` |
| Link | `LinkIntegrityTests` | Unknown `from`/`to` ids and empty verbs are rejected before any output is written; every edge in every compiled canvas resolves to a real compiled node id |
| Count | `CountTests` | Node count = `len(objects) + 2` (metadata panel + Home-return) and edge count = `len(relationships) + 1` (return edge), verified per-profile across all 11 profiles, not just one example |
| Determinism | `DeterminismTests` | Same graph compiled twice is byte-identical (structural); reordering the input `objects[]` list doesn't change output; changing only `snapshot` doesn't change anything else (including the copy of it embedded in the metadata-panel node's text); proven for all 11 profiles, not just one |
| Generated-file integrity | `GeneratedCanvasFileTests` | Both required deliverables (`N8N_OVERVIEW.canvas`, `D007_WORKFLOW_TOPOLOGY.canvas`) exist, parse as JSON, and every edge resolves; all 11 generated `.canvas` files share the identical `grammar` string in their metadata (proves "one control/visual grammar" structurally, not by claim) |

## What this does NOT cover (disclosed, not hidden)

- No visual/rendering test inside actual Obsidian — this is a JSON-structure
  and JSON-Schema-conformance test suite, run headless. The acceptance test
  "generated canvases use one control/visual grammar" is verified at the
  grammar-string/structure level; visually opening each file in Obsidian was
  not done this session.
- No test of `viewer/n8n_viewer.py`'s HTML output beyond manual inspection
  (it was rendered and read, but no automated HTML-structure test was
  written — the viewer is a formatting layer over already-tested snapshot
  data, not the pass/fail-critical component).
- No test against Stream A's real object/relationship JSON, since it has not
  returned. `SchemaFileTests.test_every_fixture_file_conforms_to_the_declared_schema`
  is the closest available proxy — any Stream A payload that also conforms
  to `graph_schema.json` will pass the same check.
