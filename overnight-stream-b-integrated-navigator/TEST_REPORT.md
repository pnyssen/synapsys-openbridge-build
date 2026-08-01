# Overnight Stream B — Test Report

Environment: `python3 -m unittest tests.test_integrated -v`, run from
`overnight-stream-b-integrated-navigator/`, this session, after
`build_overnight_candidate.py`, `viewer/n8n_viewer_scvs.py`,
`architecture/build_architecture_v1_3.py`, and — last, only after every
other file was final — the manifest regeneration.

**Result: 26/26 PASSED. Exit code 0. No skips, no expected failures.**

```
test_architecture_v13_has_lang_and_skip_link ... ok
test_architecture_v13_tabs_carry_aria_roles ... ok
test_viewer_html_has_lang_attribute ... ok
test_every_adapted_canvas_suite_graph_is_deterministic ... ok
test_rebuild_from_unchanged_inputs_matches_files_on_disk ... ok
test_same_graph_compiles_byte_identical_twice ... ok
test_architecture_v13_does_not_self_declare_implemented_or_current ... ok
test_architecture_v13_links_have_no_arrow_notation_or_mac_absolute_paths ... ok
test_architecture_v13_return_link_points_at_v12 ... ok
test_arrow_notation_return_route_fails_closed ... ok
test_every_generated_canvas_edge_resolves_to_a_real_node ... ok
test_every_generated_canvas_return_route_is_the_v13_candidate_path ... ok
test_viewer_html_links_have_no_arrow_notation_or_mac_absolute_paths ... ok
test_every_manifest_row_matches_file_on_disk ... ok
test_manifest_exists ... ok
test_architecture_v13_does_not_declare_itself_a_new_home_or_dashboard ... ok
test_no_generated_file_is_named_00_home ... ok
test_only_one_architecture_shell_file_is_generated ... ok
test_every_adapted_canvas_suite_graph_conforms ... ok
test_minimal_graph_compiles ... ok
test_optional_v02_fields_do_not_break_v01_shaped_graphs ... ok
test_v02_schema_loads ... ok
test_adapter_maps_a_well_formed_payload_without_fabrication ... ok
test_adapter_refuses_when_no_payload ... ok
test_architecture_v13_has_no_dark_mode_media_query ... ok
test_viewer_html_has_no_dark_mode_media_query ... ok

Ran 26 tests in 0.815s
OK
```

## Coverage against the dispatch's required test categories

| Requirement | Test class | What's proven |
|---|---|---|
| Schema validation | `SchemaTests` | The v0.2 schema loads; a minimal graph compiles; all 15 adapted-canvas graphs conform; v0.1-shaped graphs (no optional fields) still compile through the same compiler |
| Fixture/live-label separation | `SchemaTests`, README's "Adapted vs live vs fixture" table | Every one of the 26 canvases carries one of exactly three evidence labels (`ADAPTED_FROM_ACCEPTED_CANVAS`, `LIVE_VERIFIED`, `LABELLED_FIXTURE`), never an unlabelled or invented state |
| Link/route validity | `LinkAndRouteTests` | Fail-closed on arrow-notation return routes (inherited from Lane B, proven through the new SCVS wrapper); every canvas return route is the single v1.3 candidate path; every canvas edge resolves to a real node; viewer and Architecture HTML `href`/`src` contain no arrow notation and no Mac-absolute paths; the one disclosed vault-relative exception (`COMPONENTS/`) is named, not silently passed |
| Accessibility | `AccessibilityTests` | `lang="en"`, skip-to-main link, ARIA tablist/tabpanel/aria-selected roles present on the Architecture v1.3 shell; `lang` attribute on the viewer |
| White background | `WhiteBackgroundTests` | No `prefers-color-scheme` media query in either HTML output; explicit white background declared in both |
| No competing Home | `NoCompetingHomeTests` | No generated file named anything resembling `00_HOME`; exactly one architecture shell file exists; the shell never claims to be a new Home/dashboard, only ever refers back to the existing ones |
| Determinism | `DeterminismTests` | Same graph compiled twice is byte-identical (structural); every one of the 15 adapted-canvas graphs is independently proven deterministic; the actual on-disk output of canvas 01 is re-derived from its inputs right now and matches byte-for-byte, proving the *build script's* output is reproducible, not just the compiler function in isolation |
| Stream A adapter (no fabrication) | `StreamAAdapterTests` | Calling with no payload raises `StreamANotReturnedError`; a well-formed synthetic unit-test payload maps correctly into a compilable graph without needing any change downstream |
| Manifest integrity | `ManifestIntegrityTests` | Every row in `CANDIDATE_MANIFEST_SHA256.csv` is read back and its SHA-256 + byte count recomputed from the file on disk and compared exactly |

## What this does NOT cover (disclosed, not hidden)

- No visual/rendering test inside actual Obsidian — structural/JSON-level testing only, same limitation Lane B's own test suite already disclosed.
- No live browser rendering of the two HTML outputs (Architecture v1.3, N8N viewer) — structural checks (lang, ARIA roles, background CSS, href patterns) only, not a rendered-DOM or screen-reader test.
- The `COMPONENTS/*.html` iframe sources are allow-listed as a disclosed exception, not verified to actually resolve — they cannot resolve from this candidate's Working-Memory filing location by design (see README, "Link/route testing").
- No test against Stream A's real payload shape, since it does not exist yet — `StreamAAdapterTests` uses a synthetic unit-test fixture, explicitly not presented as real Stream A data anywhere.
