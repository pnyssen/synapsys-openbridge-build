"""Tests for outbox.py v0.3 (Active Outcome Supervisor JSON_FILE_LIMITED
preparation) -- lease/heartbeat, claim-then-verify, control-version drift,
and full backward compatibility with the v0.2 shape already used by every
real outbox message this session.
"""

import ast
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from job_contract import JobContract
from outbox import (
    CONTROL_VERSION_DRIFT,
    OutboxMessage,
    build_message,
    claim,
    classify_control_version_drift,
    complete,
    detect_stale_claims,
    heartbeat,
    is_lease_expired,
    select_claimable,
    serialize_message,
    try_deserialize_message,
    verify_claim_ownership,
)

FORBIDDEN_IMPORTS = {"socket", "subprocess", "urllib", "requests", "http", "os.system", "time", "random"}


def test_module_has_no_forbidden_imports():
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outbox.py")
    with open(path) as f:
        tree = ast.parse(f.read(), filename=path)
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    assert not (names & FORBIDDEN_IMPORTS), names


def _job(target_lane="claude_code"):
    return JobContract(
        control_marker="TEST_MARKER", origin_lane="chatgpt_hub", target_lane=target_lane,
        role="architect", context_id="CTX-SS", work_object_id="WO-TEST",
        state_revision="1", objective="x", source_refs="x", reality_state="x",
        ppv_state="Potential_HELD", authority_state="x", owner_lane="x", stop_hold="NONE",
        required_return="x", next_action="x", replay_validity="PRESERVED",
        origin_signal="x",
        stream="platform-capability", processor_route="x", distribution_class="centre",
        filing_state="FILED", exception_route="NONE", status="proposed",
        replay_hash="deadbeef" * 8,
    )


def _proposed_message():
    return build_message(_job(), enqueued_at_iso="2026-08-18T00:00:00")


# ---------------------------------------------------------------------------
# Backward compatibility with the v0.2 shape (every real message this
# session was built without any of the new fields)
# ---------------------------------------------------------------------------

def test_v02_shape_message_still_deserializes():
    raw = {
        "message_id": "abc123", "job": _job().__dict__, "enqueued_at_iso": "2026-08-18T00:00:00",
        "status": "proposed", "claimed_by": None, "claimed_at_iso": None,
    }
    m = try_deserialize_message(raw)
    assert m is not None
    assert m.lease_expires_at is None
    assert m.attempt_count == 0
    assert m.control_branch is None


def test_original_claim_call_shape_still_valid():
    m = _proposed_message()
    claimed = claim(m, "claude_code", "2026-08-18T00:05:00")
    assert claimed.status == "active"
    assert claimed.claimed_by == "claude_code"
    assert claimed.lease_expires_at is None
    assert claimed.attempt_count == 1


def test_original_complete_call_shape_still_valid():
    m = claim(_proposed_message(), "claude_code", "2026-08-18T00:05:00")
    completed = complete(m, "returned")
    assert completed.status == "returned"
    assert completed.return_filed_path is None


def test_detect_stale_claims_unchanged_for_no_lease_messages():
    m = claim(_proposed_message(), "claude_code", "2026-08-18T00:00:00")
    stale = detect_stale_claims([m], now_iso="2026-08-18T05:00:00", max_claim_age_seconds=3600)
    assert m in stale
    fresh = detect_stale_claims([m], now_iso="2026-08-18T00:10:00", max_claim_age_seconds=3600)
    assert m not in fresh


# ---------------------------------------------------------------------------
# Lease / heartbeat
# ---------------------------------------------------------------------------

def test_claim_sets_lease_and_processor_id():
    m = claim(
        _proposed_message(), "claude_code", "2026-08-18T00:00:00",
        processor_id="claude_code:session-1", lease_expires_at="2026-08-18T00:10:00",
    )
    assert m.processor_id == "claude_code:session-1"
    assert m.lease_expires_at == "2026-08-18T00:10:00"
    assert m.last_transition_at == "2026-08-18T00:00:00"


def test_lease_not_expired_before_expiry():
    m = claim(_proposed_message(), "claude_code", "2026-08-18T00:00:00", lease_expires_at="2026-08-18T00:10:00")
    assert is_lease_expired(m, "2026-08-18T00:05:00") is False


def test_lease_expired_after_expiry():
    m = claim(_proposed_message(), "claude_code", "2026-08-18T00:00:00", lease_expires_at="2026-08-18T00:10:00")
    assert is_lease_expired(m, "2026-08-18T00:10:01") is True


def test_lease_expired_at_exact_boundary():
    m = claim(_proposed_message(), "claude_code", "2026-08-18T00:00:00", lease_expires_at="2026-08-18T00:10:00")
    assert is_lease_expired(m, "2026-08-18T00:10:00") is True


def test_no_lease_never_expires():
    m = claim(_proposed_message(), "claude_code", "2026-08-18T00:00:00")
    assert is_lease_expired(m, "2099-01-01T00:00:00") is False


def test_heartbeat_extends_lease_and_preserves_claim_evidence():
    m = claim(_proposed_message(), "claude_code", "2026-08-18T00:00:00", lease_expires_at="2026-08-18T00:10:00")
    hb = heartbeat(m, "2026-08-18T00:05:00", new_lease_expires_at="2026-08-18T00:15:00")
    assert hb.lease_expires_at == "2026-08-18T00:15:00"
    assert hb.heartbeat_at == "2026-08-18T00:05:00"
    assert hb.claimed_by == "claude_code"
    assert hb.claimed_at_iso == "2026-08-18T00:00:00"
    assert hb.attempt_count == 1


def test_heartbeat_without_new_lease_leaves_lease_unchanged():
    m = claim(_proposed_message(), "claude_code", "2026-08-18T00:00:00", lease_expires_at="2026-08-18T00:10:00")
    hb = heartbeat(m, "2026-08-18T00:05:00")
    assert hb.lease_expires_at == "2026-08-18T00:10:00"


def test_heartbeat_refuses_non_active_message():
    m = _proposed_message()
    with pytest.raises(ValueError):
        heartbeat(m, "2026-08-18T00:00:00")


def test_detect_stale_claims_uses_lease_when_present():
    m = claim(_proposed_message(), "claude_code", "2026-08-18T00:00:00", lease_expires_at="2026-08-18T00:10:00")
    not_stale = detect_stale_claims([m], now_iso="2026-08-18T00:05:00", max_claim_age_seconds=1)
    assert m not in not_stale  # lease not expired even though max_claim_age_seconds=1s would fail the old heuristic
    stale = detect_stale_claims([m], now_iso="2026-08-18T00:20:00", max_claim_age_seconds=999999)
    assert m in stale  # lease expired even though the old heuristic (huge max age) would say fresh


def test_stale_claim_preserves_prior_evidence():
    m = claim(_proposed_message(), "claude_code", "2026-08-18T00:00:00", lease_expires_at="2026-08-18T00:10:00")
    stale = detect_stale_claims([m], now_iso="2026-08-18T00:20:00", max_claim_age_seconds=999999)[0]
    assert stale.claimed_by == "claude_code"
    assert stale.claimed_at_iso == "2026-08-18T00:00:00"
    assert stale.attempt_count == 1
    assert stale is m  # detect_stale_claims reports, never mutates


# ---------------------------------------------------------------------------
# Duplicate-claim rejection (claim-then-verify, explicitly non-atomic)
# ---------------------------------------------------------------------------

def test_second_claim_attempt_on_active_message_raises():
    m = claim(_proposed_message(), "claude_code", "2026-08-18T00:00:00")
    with pytest.raises(ValueError):
        claim(m, "claude_code_other_session", "2026-08-18T00:01:00")


def test_verify_claim_ownership_true_for_matching_readback():
    m = claim(_proposed_message(), "claude_code", "2026-08-18T00:00:00", processor_id="claude_code:s1")
    assert verify_claim_ownership(m, "claude_code", "claude_code:s1") is True


def test_verify_claim_ownership_false_for_different_claimant():
    m = claim(_proposed_message(), "claude_code_other", "2026-08-18T00:00:00")
    assert verify_claim_ownership(m, "claude_code") is False


def test_verify_claim_ownership_false_for_non_active():
    m = _proposed_message()
    assert verify_claim_ownership(m, "claude_code") is False


# ---------------------------------------------------------------------------
# Return matching / receipt fields
# ---------------------------------------------------------------------------

def test_complete_records_receipt_fields():
    m = claim(_proposed_message(), "claude_code", "2026-08-18T00:00:00")
    done = complete(
        m, "returned", at_iso="2026-08-18T00:30:00",
        state_consumed_revision="404", return_filed_path="05_.../return.md",
        return_readback_sha256="abc123", controller_match_result="EXPECTED_RETURN_COMPLETE",
    )
    assert done.state_consumed_revision == "404"
    assert done.return_filed_path == "05_.../return.md"
    assert done.return_readback_sha256 == "abc123"
    assert done.controller_match_result == "EXPECTED_RETURN_COMPLETE"
    assert done.last_transition_at == "2026-08-18T00:30:00"


def test_complete_omitted_fields_leave_prior_values_unchanged():
    m = claim(_proposed_message(), "claude_code", "2026-08-18T00:00:00")
    m = complete(m, "blocked", state_consumed_revision="404")
    # re-claim is not possible once terminal; test the single completion preserves what was set
    assert m.state_consumed_revision == "404"
    assert m.return_filed_path is None


# ---------------------------------------------------------------------------
# Control-version drift
# ---------------------------------------------------------------------------

def test_control_version_drift_detected():
    m = claim(
        _proposed_message(), "claude_code", "2026-08-18T00:00:00",
        control_branch="claude/old-branch", control_commit="deadbeef",
    )
    result = classify_control_version_drift(m, "claude/new-branch", "cafef00d")
    assert result == CONTROL_VERSION_DRIFT


def test_control_version_match_no_drift():
    m = claim(
        _proposed_message(), "claude_code", "2026-08-18T00:00:00",
        control_branch="claude/agent-outcome-supervisor-json-limited-prep", control_commit="cafef00d",
    )
    result = classify_control_version_drift(m, "claude/agent-outcome-supervisor-json-limited-prep", "cafef00d")
    assert result is None


def test_no_declared_control_identity_is_not_drift_by_default():
    m = claim(_proposed_message(), "claude_code", "2026-08-18T00:00:00")
    result = classify_control_version_drift(m, "any-branch", "any-commit")
    assert result is None


def test_control_version_drift_scoped_to_one_message_not_a_global_failure():
    """Classification is a pure per-message function -- callers are
    responsible for not failing an entire poll on one drifted receipt.
    This test only proves the function itself never raises or affects
    other messages."""
    drifted = claim(_proposed_message(), "claude_code", "2026-08-18T00:00:00", control_branch="old", control_commit="old")
    clean = claim(_proposed_message(), "claude_code", "2026-08-18T00:01:00", control_branch="new", control_commit="new")
    results = [classify_control_version_drift(m, "new", "new") for m in [drifted, clean]]
    assert results == [CONTROL_VERSION_DRIFT, None]


# ---------------------------------------------------------------------------
# select_claimable / try_deserialize_message still work on the extended shape
# ---------------------------------------------------------------------------

def test_select_claimable_still_works_with_extended_dataclass():
    m1 = _proposed_message()
    m2 = build_message(_job(target_lane="gpt"), enqueued_at_iso="2026-08-18T00:00:01")
    claimable = select_claimable([m1, m2], processor="claude_code")
    assert claimable == [m1]


def test_serialize_then_try_deserialize_roundtrips_new_fields():
    m = claim(
        _proposed_message(), "claude_code", "2026-08-18T00:00:00",
        processor_id="claude_code:s1", lease_expires_at="2026-08-18T00:10:00",
        control_branch="b", control_commit="c",
    )
    raw = serialize_message(m)
    roundtripped = try_deserialize_message(raw)
    assert roundtripped == m
