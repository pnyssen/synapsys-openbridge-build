# Test Report — Navigator Static-Validation Regression Suite

Environment: `python3 -B -m unittest tests.test_checks -v`, run from
`navigator-static-validation/`, this session. No network call anywhere
in this suite.

**Result: 32/32 PASSED. Exit code 0.**

```
test_absolute_url_and_anchor_not_flagged_as_unresolved ... ok
test_arrow_notation_detected ... ok
test_clean_page_with_home_return_has_no_findings ... ok
test_competing_interface_claim_detected ... ok
test_missing_home_return_detected ... ok
test_unresolved_relative_link_detected ... ok
test_byte_mismatch_detected ... ok
test_byte_mismatch_does_not_also_report_hash_mismatch ... ok
test_extra_not_in_manifest_detected ... ok
test_hash_mismatch_detected_when_bytes_match ... ok
test_matching_row_produces_no_finding ... ok
test_missing_on_disk_detected ... ok
test_parse_path_bytes_sha_header ... ok
test_parse_path_sha_bytes_header ... ok
test_dark_mode_query_flagged ... ok
test_dead_data_open_target_detected ... ok
test_live_data_open_target_not_flagged ... ok
test_missing_white_background_flagged ... ok
test_white_background_no_dark_mode_passes ... ok
test_backward_order_collapse_flagged ... ok
test_canonical_count_sentence_not_flagged ... ok
test_clean_candidate_language_not_flagged ... ok
test_compare_hook_matching_reports_nothing ... ok
test_compare_hook_mismatch_reported ... ok
test_compare_hook_missing_field_reported ... ok
test_current_objective_sentence_not_flagged ... ok
test_extract_window_hook_parses_simple_object ... ok
test_extract_window_hook_returns_none_for_missing_name ... ok
test_extract_window_hook_skips_arrow_function_valued_keys ... ok
test_script_block_content_not_flagged ... ok
test_unqualified_collapse_flagged ... ok
test_unrelated_canonical_candidates_phrase_not_flagged ... ok

Ran 32 tests in 0.005s

OK
```

## Coverage against this cycle's checklist

| Checklist item | Module | Status |
|---|---|---|
| Manifest completeness; byte and SHA-256 parity | `checks/manifest_parity.py` | Implemented, tested (7 tests), run against real data — found 1 real defect |
| Broken relative links | `checks/link_checker.py` | Implemented, tested, run against real data — no findings |
| Missing return-to-Home paths | `checks/link_checker.py` | Implemented, tested, run against real data — no findings |
| Duplicate/competing primary-interface claims | `checks/link_checker.py` | Implemented (heuristic phrase-repetition scan), tested, run against real data — no findings |
| Invalid Canvas JSON / missing Canvas targets | — | **Deferred** — see README, "What this cycle deliberately did not attempt" |
| Stale source/freshness/PPV/evidence/authority markers | `checks/manifest_parity.py` (byte/hash staleness only) | Partial — this cycle covers manifest-vs-file staleness; marker-text staleness (e.g. a `snapshot:` field older than N days) is not yet implemented |
| Candidate/implemented/accepted/canonical state collapse | `checks/state_vocabulary.py` | Implemented, tested (8 tests including 4 real-content regression fixtures), run against real data — 9 initial false positives found and fixed, 0 real findings after the fix |
| White-background / readable-text standard | `checks/presentation_standard.py` | Implemented, tested, run against real data — no findings |
| Dead UI controls | `checks/presentation_standard.py` (heuristic: `data-open` targets only) | Partial — covers `data-open`/`id` pairing; does not yet cover `onclick` handlers calling undefined functions |
| Displayed-state vs embedded-test-hook contradictions | `checks/state_vocabulary.py` | Implemented, tested (5 tests), run against real data — parser could not handle the real hook's function-valued field until fixed; 0 contradictions across 29 fields after the fix |
| CURRENT_DELIVERY.md inclusion | `checks/manifest_parity.py` (as a manifest row) | Covered as part of the manifest-parity run — this is exactly the row found stale |

## What this does NOT cover (disclosed, not hidden)

- No Canvas JSON structural validation this cycle (schema conformity,
  unique node/edge IDs, resolvable edge targets) — deferred to a future
  cycle rather than rushed; Lane B's and Overnight B's compilers already
  cover this for candidate builds, and building a *general* validator
  well needs more room than this cycle's "smallest isolated correction"
  scope allows.
- No test exercises against a live N8N/Odoo call — this suite is
  entirely static/offline, matching this cycle's authority boundary.
- The "competing primary-interface claims" check is a literal-phrase
  repetition heuristic, not semantic understanding — it would miss a
  claim phrased differently from the four tracked phrases.
- The dead-control check only covers the `data-open`/`id` convention
  used by this Work Object's own HTML surfaces; it does not check
  `onclick="someFunction()"` handlers against defined functions.
