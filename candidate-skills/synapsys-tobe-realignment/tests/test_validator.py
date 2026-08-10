import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from validator import validate, validate_file  # noqa: E402

FRONT_MATTER_OK = """---
status: LIVING — UPDATE IN PLACE AS STATE CHANGES
authority_state: HELD — this document tracks and orients; it grants no authority
replay_validity: PRESERVED
---
"""

VALID_ENTRY = """### 1. thread-a — a title

- **tobe_goal**: the target state, one sentence.
- **as_is_state**: as of 2026-08-10, current reality here.
- **source_of_truth**: 05_AI_RETURNS_HASHED/SOME_FILE_v0.1.md
- **verification_instruction**: re-fetch the path above before acting.
- **next_valid_action**: the one thing this is waiting on.
- **self_authority_claim**: none.
"""


def make_doc(entry: str = VALID_ENTRY, front_matter: str = FRONT_MATTER_OK) -> str:
    return front_matter + "\n# TOBE stack\n\n" + entry


def test_valid_document_passes():
    report = validate(make_doc())
    assert report.ok, report.summary()
    assert len(report.entries) == 1
    assert report.entries[0].ok


def test_real_current_state_file_v01_passes():
    path = os.path.join(
        os.path.dirname(__file__), "..", "state", "TOBE_PRIORITY_STACK_CURRENT_v0.1.md"
    )
    report = validate_file(path)
    assert report.ok, report.summary()
    assert len(report.entries) == 3


def test_real_current_state_file_v02_passes():
    # v0.2 corrected v0.1's structural error (sequential queue vs.
    # aligned-capabilities-with-an-integration-point) -- superseding
    # content, but must still pass the same schema.
    path = os.path.join(
        os.path.dirname(__file__), "..", "state", "TOBE_PRIORITY_STACK_CURRENT_v0.2.md"
    )
    report = validate_file(path)
    assert report.ok, report.summary()
    assert len(report.entries) == 3


def test_real_current_state_file_v03_passes():
    # v0.3 updates capability 2 with a real executed proxy-test result.
    # Each "current" file stays fully self-contained (no "see v0.2"
    # shortcuts) -- the validator caught this the first time this file
    # was drafted, when capabilities 1 and 3 were left as pointers
    # instead of full entries.
    path = os.path.join(
        os.path.dirname(__file__), "..", "state", "TOBE_PRIORITY_STACK_CURRENT_v0.3.md"
    )
    report = validate_file(path)
    assert report.ok, report.summary()
    assert len(report.entries) == 3


def test_real_current_state_file_v04_passes():
    # v0.4 resolves capability 1 with independently-verified evidence
    # (4/4 file hashes, 3/3 Odoo records) rather than trusting a relay.
    path = os.path.join(
        os.path.dirname(__file__), "..", "state", "TOBE_PRIORITY_STACK_CURRENT_v0.4.md"
    )
    report = validate_file(path)
    assert report.ok, report.summary()
    assert len(report.entries) == 3


def test_missing_source_of_truth_fails():
    entry = VALID_ENTRY.replace(
        "- **source_of_truth**: 05_AI_RETURNS_HASHED/SOME_FILE_v0.1.md\n", ""
    )
    report = validate(make_doc(entry))
    assert not report.ok
    assert "source_of_truth" in report.entries[0].missing_fields


def test_missing_verification_instruction_fails():
    entry = VALID_ENTRY.replace(
        "- **verification_instruction**: re-fetch the path above before acting.\n", ""
    )
    report = validate(make_doc(entry))
    assert not report.ok
    assert "verification_instruction" in report.entries[0].missing_fields


def test_missing_tobe_goal_fails():
    entry = VALID_ENTRY.replace(
        "- **tobe_goal**: the target state, one sentence.\n", ""
    )
    report = validate(make_doc(entry))
    assert not report.ok
    assert "tobe_goal" in report.entries[0].missing_fields


def test_self_asserted_verified_claim_fails():
    entry = VALID_ENTRY.replace(
        "- **self_authority_claim**: none.",
        "- **self_authority_claim**: VERIFIED, this thread is complete.",
    )
    report = validate(make_doc(entry))
    assert not report.ok
    assert any("VERIFIED" in e for e in report.entries[0].errors)


def test_self_authority_claim_held_is_allowed():
    entry = VALID_ENTRY.replace(
        "- **self_authority_claim**: none.",
        "- **self_authority_claim**: HELD / candidate only.",
    )
    report = validate(make_doc(entry))
    assert report.ok, report.summary()


def test_quoting_verified_from_a_source_is_allowed():
    # Quoting another document's status is fine -- only a bare, unheld
    # self-claim should fail.
    entry = VALID_ENTRY.replace(
        "- **as_is_state**: as of 2026-08-10, current reality here.",
        "- **as_is_state**: as of 2026-08-10, the cited register shows "
        "this item as VERIFIED per its own record.",
    )
    report = validate(make_doc(entry))
    assert report.ok, report.summary()


def test_missing_authority_state_front_matter_fails():
    front_matter = """---
status: LIVING — UPDATE IN PLACE AS STATE CHANGES
replay_validity: PRESERVED
---
"""
    report = validate(make_doc(front_matter=front_matter))
    assert not report.ok
    assert "authority_state" in report.missing_front_matter


def test_non_held_authority_state_fails():
    front_matter = """---
status: LIVING — UPDATE IN PLACE AS STATE CHANGES
authority_state: ADOPTED
replay_validity: PRESERVED
---
"""
    report = validate(make_doc(front_matter=front_matter))
    assert not report.ok
    assert any("HELD" in e for e in report.global_errors)


def test_no_entries_found_fails():
    report = validate(FRONT_MATTER_OK + "\n# Empty stack\n\nNo entries here.\n")
    assert not report.ok
    assert any("no '### N." in e for e in report.global_errors)


def test_undated_as_is_state_produces_warning_not_failure():
    entry = VALID_ENTRY.replace(
        "- **as_is_state**: as of 2026-08-10, current reality here.",
        "- **as_is_state**: currently fine, no date given.",
    )
    report = validate(make_doc(entry))
    assert report.ok, report.summary()  # warning only, not a failure
    assert any("undated" in w for w in report.entries[0].warnings)


def test_multiple_entries_parsed_independently():
    second_entry = VALID_ENTRY.replace("### 1. thread-a", "### 2. thread-b").replace(
        "- **source_of_truth**: 05_AI_RETURNS_HASHED/SOME_FILE_v0.1.md\n", ""
    )
    report = validate(make_doc(VALID_ENTRY + "\n" + second_entry))
    assert len(report.entries) == 2
    assert report.entries[0].ok
    assert not report.entries[1].ok
    assert not report.ok
