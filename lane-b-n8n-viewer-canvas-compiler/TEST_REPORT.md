# Lane B — Schema / Link / Count / Determinism / Correction Test Report

Environment: `python3 -m unittest tests.test_compiler tests.test_corrections -v`,
run from `lane-b-n8n-viewer-canvas-compiler/`, this session, after
`tools_build_live_fixtures.py`, `tools_build_labelled_fixtures.py`,
`tools_build_viewer_snapshot.py`, `generate_canvases.py`, `viewer/n8n_viewer.py`,
and — last, only after every other edit was final — the manifest regeneration.

**Result: 32/32 PASSED. Exit code 0. No skips, no expected failures.**

`tests/test_compiler.py` (21 tests, unchanged from the original candidate) +
`tests/test_corrections.py` (11 new tests, added for Correction v0.1):

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
test_compiler_fails_closed_on_arrow_notation_in_return_route ... ok
test_every_profile_return_route_has_no_arrow_notation ... ok
test_every_profile_return_route_is_a_single_clean_path ... ok
test_viewer_html_return_href_points_at_the_v1_2_primary_interface ... ok
test_viewer_html_return_links_have_no_arrow_notation_and_are_well_formed ... ok
test_every_manifest_row_matches_the_file_on_disk ... ok
test_manifest_does_not_still_record_the_pre_correction_readme_byte_count ... ok
test_manifest_exists ... ok
test_every_profile_snapshot_is_not_later_than_hub_intake_plus_reasonable_build_window ... ok
test_every_profile_snapshot_is_not_later_than_now ... ok
test_no_profile_still_carries_the_old_future_dated_snapshot ... ok

Ran 32 tests in 0.792s
OK
```

## Coverage against the dispatch's five test categories (unchanged, still holds)

| Category | Test class(es) | What's proven |
|---|---|---|
| Schema | `SchemaValidationTests`, `SchemaFileTests` | Valid graphs pass; missing/empty/invalid required fields are rejected; every one of the 11 fixture files conforms to `graph_schema.json`, including its new `return_route` pattern |
| Link | `LinkIntegrityTests` | Unknown `from`/`to` ids and empty verbs are rejected; every edge in every compiled canvas resolves to a real compiled node id |
| Count | `CountTests` | Node/edge counts verified per-profile across all 11 profiles |
| Determinism | `DeterminismTests` | Same graph compiled twice is byte-identical; input reordering and snapshot-only changes don't affect structure |
| Generated-file integrity | `GeneratedCanvasFileTests` | Both required deliverables exist, parse, and share the identical grammar string |

## Coverage against Correction v0.1's four required test additions

| Requirement | Test class | What's proven |
|---|---|---|
| Snapshot not later than build/receipt time | `TimestampTests` | No profile still carries the old `2026-08-02T02:15:00Z` value; every profile's snapshot is `<= now()`; every profile's snapshot is within a 6-hour sanity window of the cited Hub intake time (`2026-08-02T01:56:00+10:00`) — the previous defect was ~10h19m past intake, this catches any regression of that scale |
| HTML/Canvas return links valid, no literal arrow notation | `LinkValidityTests` | `compile_canvas`/`validate_graph` fail closed on an arrow-notation `return_route` (enforced at both the JSON-Schema `pattern` layer and the explicit code-level check); every profile's compiled canvas metadata and Home-return node text contain no `"->"`; the generated `N8N_VIEWER.html`'s `href` attributes contain no `"->"` or raw spaces and are well-formed absolute/relative URLs; the return link specifically resolves to the `v1.2` primary interface |
| Every filed review-subset file matches the final manifest | `ManifestIntegrityTests` | Every row in `CANDIDATE_MANIFEST_SHA256.csv` is read back and its SHA-256 + byte count recomputed from the file on disk and compared exactly; a dedicated regression test guards specifically against the README byte-count drift the correction dispatch flagged (8,920 filed vs 8,472 recorded) |
| Full suite re-run after all fixes | (this file) | 32/32, exit code 0, captured above |

## What this does NOT cover (disclosed, not hidden — unchanged from the original candidate)

- No visual/rendering test inside actual Obsidian.
- No automated HTML-structure test of `viewer/n8n_viewer.py`'s output beyond
  the return-link `href` regex checks added this pass.
- No test against Stream A's real object/relationship JSON, since it has not
  returned.
- `ManifestIntegrityTests` validates the **local Git tree** copy of every
  file the manifest lists. It cannot itself verify the **Working Memory**
  filed copies byte-for-byte from inside this test run (no live `sp_read`
  from a `unittest` case) — that equivalence is established instead by
  filing byte-identical content and citing the SHA-256 each `sp_write` call
  returns against the same manifest value, per the correction return.
