# Test Report — D007 Transport Pilot Offline Readiness

Environment: `python3 -B -m unittest tests.test_offline_pilot_readiness -v`,
run from `d007-transport-pilot-readiness/`, this session. No network
call is made anywhere in this suite.

**Result: 36/36 PASSED. Exit code 0.**

```
test_authority_missing_phrase_fails ... ok
test_authority_with_all_phrases_passes ... ok
test_byte_mismatch_fails (BinaryIntegrityTests) ... ok
test_hash_mismatch_fails (BinaryIntegrityTests) ... ok
test_matching_binary_passes ... ok
test_mime_mismatch_fails ... ok
test_existing_path_fails ... ok
test_new_path_passes ... ok
test_expired_manifest_fails ... ok
test_unexpired_manifest_passes ... ok
test_byte_mismatch_fails (ReceiptValidatorTests) ... ok
test_evidence_body_unread_fails ... ok
test_extraction_not_pass_fails ... ok
test_graph_gate_not_passed_fails ... ok
test_hash_mismatch_fails (ReceiptValidatorTests) ... ok
test_missing_field_fails ... ok
test_schema_loads ... ok
test_secret_scan_flagged_fails ... ok
test_start_here_unread_fails ... ok
test_valid_receipt_passes ... ok
test_first_use_passes ... ok
test_reuse_fails ... ok
test_forbidden_expected_sha256_override_fails ... ok
test_forbidden_source_path_override_fails ... ok
test_missing_nonce_fails ... ok
test_schema_matches_gateway_rules ... ok
test_valid_request_passes ... ok
test_wrong_target_lane_fails ... ok
test_absolute_path_member_fails ... ok
test_duplicate_member_names_fail ... ok
test_excessive_expansion_member_fails ... ok
test_not_a_zip_fails ... ok
test_path_traversal_member_fails ... ok
test_unexpected_member_count_fails_too_few ... ok
test_unexpected_member_count_fails_too_many ... ok
test_valid_five_member_zip_passes ... ok

Ran 36 tests in 0.239s

OK
```

## Coverage against this task's "permitted tasks" list

| Requirement | Test class | What's proven |
|---|---|---|
| Success and malformed-payload cases | `RequestValidationTests` | A well-formed request passes; a request missing a required field, or attempting to override a forbidden field (`source_path`, `expected_sha256`, etc.), or using the wrong `target_lane`, is rejected — mirroring the real workflow's own statically-tested "Normalize and Validate Request" behaviour |
| Expiry | `ManifestExpiryTests` | A manifest read before its `expires_at` passes; the same manifest read after `expires_at` is rejected |
| Nonce reuse / replay | `ReplayAndNonceTests` | First use of a nonce passes; reuse of the same nonce is rejected |
| Duplicate mount ("endpoint rejection" of a repeat target) | `DuplicateMountTests` | A fresh mount path passes; a path already recorded as mounted is rejected |
| Authentication failure (schema/design level) | (fixed in `CAPABILITY_BOUNDARY_v0.1.md`, not testable offline) | The real endpoint's negative-auth behaviour (`HTTP 403`) is *evidenced*, not re-tested here, because re-testing it would require a live network call this lane will not make |
| Binary integrity | `BinaryIntegrityTests` | Matching bytes/hash/MIME pass; a mismatch on any one of the three is rejected |
| Extraction safety (unsafe members / path traversal / duplicates / excessive expansion / wrong member count) | `ZipSafetyTests` | A valid 5-member synthetic archive passes; path traversal, an absolute-path member, duplicate member names, an oversized member, a not-a-zip payload, and both too-few and too-many members are each independently rejected |
| Receipt-shape validation | `ReceiptValidatorTests` | A well-formed synthetic receipt passes; a receipt missing a required field, or with a byte/hash mismatch, a failed extraction, an unread `START_HERE.md` or evidence body, a flagged secret scan, or a blocked graph-build gate, is each independently rejected |

## What this does NOT cover (disclosed, not hidden)

- No live network call was made or simulated as if real — every test
  in this suite exercises this package's own local re-implementation
  of the documented rules, not the real N8N workflow. A green result
  here is evidence this package's logic is internally consistent, not
  evidence the real endpoint behaves identically.
- No test exercises the real authentication credential, because this
  lane holds none.
- No test constructs or claims a real Stream A bundle — the 5-member
  ZIP fixture used in `ZipSafetyTests` is explicitly synthetic
  placeholder content, sized and shaped like the real contract
  (5 members, one `START_HERE.md`) but never presented as the genuine
  bundle.
