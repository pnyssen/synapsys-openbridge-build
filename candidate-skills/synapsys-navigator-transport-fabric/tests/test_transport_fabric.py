"""Regression tests for the Navigator transport fabric.

Covers, per the Architecture Decision: duplicate replay, authority
non-expansion, unavailable runtime, D009 source-not-ready decline, valid
return, and rollback/disable.
"""

import ast
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest  # noqa: E402

from transport_types import (  # noqa: E402
    ClaimRecord,
    OutboxJob,
    RegistryEntry,
    RuntimeInvocationRequest,
    RuntimeInvocationResult,
)
from registry_resolver import resolve_endpoint  # noqa: E402
from replay_validator import ReplayLedger, validate_replay  # noqa: E402
from eligibility import check_eligibility, select_eligible_jobs  # noqa: E402
from claim_state_machine import attempt_claim, heartbeat, is_stale, release, expire  # noqa: E402
from adapter_interface import dispatch_to_adapter  # noqa: E402
from d009_adapter import D009_TARGET_LANE, build_d009_packet, d009_adapter_invoke, probe_d009_capability  # noqa: E402
from return_bridge import consume_return  # noqa: E402
from health_projection import build_health_projection  # noqa: E402

FORBIDDEN_MODULES = {"socket", "subprocess", "urllib", "requests", "http", "os", "sys"}


# ---------------------------------------------------------------------------
# Isolation: zero I/O across the whole package
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "module_file",
    [
        "transport_types.py",
        "registry_resolver.py",
        "replay_validator.py",
        "eligibility.py",
        "claim_state_machine.py",
        "adapter_interface.py",
        "d009_adapter.py",
        "return_bridge.py",
        "health_projection.py",
    ],
)
def test_isolation_no_forbidden_imports(module_file):
    path = os.path.join(os.path.dirname(__file__), "..", module_file)
    with open(path, "r") as f:
        tree = ast.parse(f.read(), filename=path)
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module.split(".")[0])
    forbidden_found = found & FORBIDDEN_MODULES
    assert not forbidden_found, f"{module_file}: forbidden imports {forbidden_found}"


def test_isolation_no_wallclock_calls():
    """No module may call datetime.now()/utcnow() or time.time() -- 'now' must
    always be an explicit parameter from the caller."""
    package_dir = os.path.join(os.path.dirname(__file__), "..")
    for filename in os.listdir(package_dir):
        if not filename.endswith(".py"):
            continue
        path = os.path.join(package_dir, filename)
        with open(path, "r") as f:
            source = f.read()
        assert ".now()" not in source, f"{filename} calls a wall-clock .now()"
        assert ".utcnow()" not in source, f"{filename} calls a wall-clock .utcnow()"
        assert "time.time()" not in source, f"{filename} calls a wall-clock time.time()"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

D009_REGISTRY_ENTRY = RegistryEntry(
    agent_code="AGT-D009-01",
    primary_domain="D009",
    owner_lane="gemini",
    authority_class="read_and_route",
    activation_status="authorised",
    target_lane=D009_TARGET_LANE,
)

HELD_REGISTRY_ENTRY = RegistryEntry(
    agent_code="AGT-D007-01",
    primary_domain="D007",
    owner_lane="mixed",
    authority_class="read_and_route",
    activation_status="held",
    target_lane="d007_lane",
)

READ_ONLY_REGISTRY_ENTRY = RegistryEntry(
    agent_code="AGT-D002-01",
    primary_domain="D002",
    owner_lane="mixed",
    authority_class="read_only",
    activation_status="authorised",
    target_lane="d002_lane",
)


def _job(message_id="msg-1", target_lane=D009_TARGET_LANE, status="open", claimed_by=None,
         context_id="CTX-BASIN", control_marker="TEST_MARKER", state_revision="316",
         enqueued_at_iso="2026-08-15T10:00:00Z", replay_hash=None):
    return OutboxJob(
        message_id=message_id,
        target_lane=target_lane,
        status=status,
        claimed_by=claimed_by,
        context_id=context_id,
        control_marker=control_marker,
        state_revision=state_revision,
        enqueued_at_iso=enqueued_at_iso,
        replay_hash=replay_hash,
    )


def _empty_ledger():
    return ReplayLedger(seen_message_ids=frozenset(), seen_logical_keys=frozenset(), hashes_by_message_id={})


# ---------------------------------------------------------------------------
# Scenario 1: duplicate replay
# ---------------------------------------------------------------------------

def test_duplicate_message_id_detected():
    job = _job()
    ledger = ReplayLedger(
        seen_message_ids=frozenset({"msg-1"}), seen_logical_keys=frozenset(), hashes_by_message_id={}
    )
    result = validate_replay(job, ledger)
    assert result.outcome == "DUPLICATE_MESSAGE_ID"


def test_duplicate_logical_job_detected_under_new_message_id():
    """Same underlying decision (context_id, control_marker, state_revision),
    different message_id -- must still be caught, per the D009-rev316
    do-not-duplicate requirement."""
    job = _job(message_id="msg-2")  # new message_id, same logical content as default fixture
    ledger = ReplayLedger(
        seen_message_ids=frozenset({"some-other-msg"}),
        seen_logical_keys=frozenset({("CTX-BASIN", "TEST_MARKER", "316")}),
        hashes_by_message_id={},
    )
    result = validate_replay(job, ledger)
    assert result.outcome == "DUPLICATE_LOGICAL_JOB"


def test_hash_mismatch_on_same_message_id_different_hash():
    job = _job(replay_hash="hash-b")
    ledger = ReplayLedger(
        seen_message_ids=frozenset({"msg-1"}),
        seen_logical_keys=frozenset(),
        hashes_by_message_id={"msg-1": "hash-a"},
    )
    result = validate_replay(job, ledger)
    assert result.outcome == "HASH_MISMATCH"


def test_duplicate_claim_attempt_is_idempotent_not_double_processed():
    """Claiming the same message_id twice by the same worker is a safe no-op,
    not a second grant."""
    first = attempt_claim(None, "msg-1", "claude_code", "2026-08-16T00:00:00Z")
    assert first.outcome == "GRANTED"

    second = attempt_claim(first.claim, "msg-1", "claude_code", "2026-08-16T00:00:05Z")
    assert second.outcome == "GRANTED"
    assert second.reason.startswith("idempotent")
    # claim identity unchanged -- not re-issued
    assert second.claim.claimed_at_iso == first.claim.claimed_at_iso


def test_second_claimant_blocked_while_first_claim_is_live():
    first = attempt_claim(None, "msg-1", "claude_code", "2026-08-16T00:00:00Z")
    second = attempt_claim(first.claim, "msg-1", "some_other_worker", "2026-08-16T00:00:05Z")
    assert second.outcome == "ALREADY_CLAIMED"


# ---------------------------------------------------------------------------
# Scenario 2: authority non-expansion
# ---------------------------------------------------------------------------

def test_registry_entry_rejects_unknown_authority_class():
    with pytest.raises(ValueError):
        RegistryEntry(
            agent_code="AGT-BAD",
            primary_domain="D099",
            owner_lane="mixed",
            authority_class="execute",  # not a real value -- must be refused
            activation_status="authorised",
            target_lane="bad_lane",
        )


def test_resolver_refuses_read_only_entry_for_routing():
    registry = [READ_ONLY_REGISTRY_ENTRY]
    result = resolve_endpoint("d002_lane", registry)
    assert not result.resolved
    assert "NOT_ELIGIBLE" in result.reason


def test_resolver_refuses_held_entry_even_if_read_and_route():
    registry = [HELD_REGISTRY_ENTRY]
    result = resolve_endpoint("d007_lane", registry)
    assert not result.resolved
    assert "NOT_AUTHORISED" in result.reason


def test_resolver_never_invents_an_entry_not_in_registry():
    result = resolve_endpoint("nonexistent_lane", [D009_REGISTRY_ENTRY])
    assert not result.resolved
    assert "NOT_REGISTERED" in result.reason


def test_eligibility_excludes_read_only_targets_from_transport():
    job = _job(target_lane="d002_lane")
    result = check_eligibility(job, [READ_ONLY_REGISTRY_ENTRY], _empty_ledger())
    assert not result.eligible


# ---------------------------------------------------------------------------
# Scenario 3: unavailable runtime
# ---------------------------------------------------------------------------

def test_dispatch_with_no_registered_adapter_returns_waiting_external_runtime():
    request = RuntimeInvocationRequest(
        message_id="msg-1",
        target_lane=D009_TARGET_LANE,
        context_id="CTX-BASIN",
        control_marker="TEST",
        state_revision="316",
        objective="x",
        source_refs="x",
    )
    result = dispatch_to_adapter(D009_TARGET_LANE, request, adapters={})
    assert result.status == "WAITING_EXTERNAL_RUNTIME"


# ---------------------------------------------------------------------------
# Scenario 4: D009 source-not-ready decline
# ---------------------------------------------------------------------------

def test_d009_declines_when_sources_not_fully_processed():
    """Matches live current state this session: ai.agent[7] AI Auditor
    sources_fully_processed=False."""
    assert probe_d009_capability(ai_auditor_sources_fully_processed=False) == "DECLINE_SOURCES_NOT_READY"

    request = RuntimeInvocationRequest(
        message_id="msg-1", target_lane=D009_TARGET_LANE, context_id="CTX-BASIN",
        control_marker="TEST", state_revision="316", objective="x", source_refs="x",
    )
    result = d009_adapter_invoke(request, ai_auditor_sources_fully_processed=False)
    assert result.status == "DEGRADED"
    assert result.status != "ATTEMPTED_RETURNED"
    assert "not treated as PASS" in result.detail


def test_d009_does_not_silently_pass_when_sources_not_ready():
    """The specific invariant named in the architecture decision: silence
    must never become PASS."""
    request = RuntimeInvocationRequest(
        message_id="msg-1", target_lane=D009_TARGET_LANE, context_id="CTX-BASIN",
        control_marker="TEST", state_revision="316", objective="x", source_refs="x",
    )
    result = d009_adapter_invoke(request, ai_auditor_sources_fully_processed=False)
    assert result.status in ("DEGRADED", "DECLINED")


def test_d009_capability_result_when_sources_ready():
    assert probe_d009_capability(ai_auditor_sources_fully_processed=True) == "ATTEMPT"

    request = RuntimeInvocationRequest(
        message_id="msg-1", target_lane=D009_TARGET_LANE, context_id="CTX-BASIN",
        control_marker="TEST", state_revision="316", objective="x", source_refs="x",
    )
    result = d009_adapter_invoke(request, ai_auditor_sources_fully_processed=True)
    # ATTEMPT-eligible, but no live runtime wired in Phase 1 -- explicit waiting, not a fabricated pass
    assert result.status == "WAITING_EXTERNAL_RUNTIME"


def test_build_d009_packet_uses_only_request_fields():
    request = RuntimeInvocationRequest(
        message_id="msg-1", target_lane=D009_TARGET_LANE, context_id="CTX-BASIN",
        control_marker="TEST_MARKER", state_revision="316",
        objective="assess Basin critical path", source_refs="project.project 100",
    )
    packet = build_d009_packet(request)
    assert packet["message_id"] == "msg-1"
    assert packet["state_revision"] == "316"
    assert packet["assurance_domain"] == "D009"


# ---------------------------------------------------------------------------
# Scenario 5: valid return
# ---------------------------------------------------------------------------

def test_valid_return_is_consumed_with_job_bound_revision_not_controller_revision():
    """The D009 job stays bound to state rev316; a genuine return consuming
    rev316 remains valid even though the controller has since moved to rev318."""
    runtime_result = RuntimeInvocationResult(
        status="ATTEMPTED_RETURNED", detail="ok", returned_message_id="msg-1",
        returned_payload={"assurance": "PASS"},
    )
    outcome = consume_return(
        dispatch_task_state_revision="316",
        controller_state_revision="318",
        runtime_result=runtime_result,
        expected_message_id="msg-1",
    )
    assert outcome.accepted
    assert outcome.consumed_state_revision == "316"
    assert outcome.controller_state_revision_at_consumption == "318"


def test_return_rejected_on_identity_mismatch():
    runtime_result = RuntimeInvocationResult(
        status="ATTEMPTED_RETURNED", detail="ok", returned_message_id="wrong-msg-id",
    )
    outcome = consume_return(
        dispatch_task_state_revision="316", controller_state_revision="318",
        runtime_result=runtime_result, expected_message_id="msg-1",
    )
    assert not outcome.accepted
    assert "identity mismatch" in outcome.reason


def test_return_rejected_when_runtime_status_is_not_returned():
    runtime_result = RuntimeInvocationResult(status="DEGRADED", detail="declined")
    outcome = consume_return(
        dispatch_task_state_revision="316", controller_state_revision="318",
        runtime_result=runtime_result, expected_message_id="msg-1",
    )
    assert not outcome.accepted


# ---------------------------------------------------------------------------
# Scenario 6: rollback/disable
# ---------------------------------------------------------------------------

def test_release_returns_claim_to_reclaimable_state():
    claimed = attempt_claim(None, "msg-1", "claude_code", "2026-08-16T00:00:00Z").claim
    released = release(claimed)
    assert released.status == "RELEASED"

    reclaimed = attempt_claim(released, "msg-1", "another_worker", "2026-08-16T00:01:00Z")
    assert reclaimed.outcome == "GRANTED"
    assert reclaimed.claim.claimed_by == "another_worker"


def test_stale_claim_is_detected_and_can_be_expired_then_reclaimed():
    claimed = attempt_claim(None, "msg-1", "claude_code", "2026-08-16T00:00:00Z").claim
    later = "2026-08-16T00:05:00Z"  # 300s later, past the 120s default stale threshold
    assert is_stale(claimed, later)

    expired = expire(claimed)
    assert expired.status == "EXPIRED"

    reclaim_attempt = attempt_claim(claimed, "msg-1", "another_worker", later)
    assert reclaim_attempt.outcome == "RECLAIMED_EXPIRED"


def test_heartbeat_prevents_staleness():
    claimed = attempt_claim(None, "msg-1", "claude_code", "2026-08-16T00:00:00Z").claim
    refreshed = heartbeat(claimed, "2026-08-16T00:01:00Z")
    assert not is_stale(refreshed, "2026-08-16T00:02:00Z")  # only 60s since refreshed heartbeat


def test_heartbeat_rejects_released_claim():
    claimed = attempt_claim(None, "msg-1", "claude_code", "2026-08-16T00:00:00Z").claim
    released = release(claimed)
    with pytest.raises(ValueError):
        heartbeat(released, "2026-08-16T00:01:00Z")


# ---------------------------------------------------------------------------
# Eligibility + selection, end to end
# ---------------------------------------------------------------------------

def test_select_eligible_jobs_end_to_end():
    open_job = _job(message_id="msg-open")
    already_claimed = _job(message_id="msg-claimed", claimed_by="someone")
    closed_job = _job(message_id="msg-closed", status="closed")
    wrong_lane_job = _job(message_id="msg-wrong-lane", target_lane="nonexistent_lane")

    eligible = select_eligible_jobs(
        [open_job, already_claimed, closed_job, wrong_lane_job],
        [D009_REGISTRY_ENTRY],
        _empty_ledger(),
    )
    assert eligible == [open_job]


# ---------------------------------------------------------------------------
# Health projection
# ---------------------------------------------------------------------------

def test_health_projection_offline_when_never_claimed():
    projection = build_health_projection(
        registry=[D009_REGISTRY_ENTRY], jobs=[], claims=[],
        last_return_iso_by_target_lane={}, now_iso="2026-08-16T00:00:00Z",
    )
    assert len(projection) == 1
    assert projection[0].status == "OFFLINE"
    assert projection[0].authority_boundary == "read_and_route"


def test_health_projection_held_when_registry_entry_not_authorised():
    projection = build_health_projection(
        registry=[HELD_REGISTRY_ENTRY], jobs=[], claims=[],
        last_return_iso_by_target_lane={}, now_iso="2026-08-16T00:00:00Z",
    )
    assert projection[0].status == "HELD"


def test_health_projection_active_with_fresh_claim():
    job = _job(message_id="msg-1", enqueued_at_iso="2026-08-16T00:00:00Z")
    claim = ClaimRecord(
        message_id="msg-1", claimed_by="claude_code",
        claimed_at_iso="2026-08-16T00:00:05Z", heartbeat_at_iso="2026-08-16T00:00:05Z",
        status="CLAIMED",
    )
    projection = build_health_projection(
        registry=[D009_REGISTRY_ENTRY], jobs=[job], claims=[claim],
        last_return_iso_by_target_lane={D009_TARGET_LANE: "2026-08-15T23:00:00Z"},
        now_iso="2026-08-16T00:00:10Z",
    )
    entry = projection[0]
    assert entry.status == "ACTIVE"
    assert entry.claim_latency_seconds == pytest.approx(5.0)
    assert entry.last_return_iso == "2026-08-15T23:00:00Z"


def test_health_projection_degraded_when_heartbeat_stale():
    job = _job(message_id="msg-1", enqueued_at_iso="2026-08-16T00:00:00Z")
    claim = ClaimRecord(
        message_id="msg-1", claimed_by="claude_code",
        claimed_at_iso="2026-08-16T00:00:05Z", heartbeat_at_iso="2026-08-16T00:00:05Z",
        status="CLAIMED",
    )
    projection = build_health_projection(
        registry=[D009_REGISTRY_ENTRY], jobs=[job], claims=[claim],
        last_return_iso_by_target_lane={}, now_iso="2026-08-16T00:10:00Z",  # far past stale threshold
    )
    assert projection[0].status == "DEGRADED"
