"""Tests for outbox.py."""

import ast
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from job_contract import JobContract, compute_replay_hash, validate_job_contract  # noqa: E402
from outbox import (  # noqa: E402
    OutboxMessage,
    build_message,
    claim,
    complete,
    select_claimable,
    detect_stale_claims,
    outbox_filename,
    serialize_message,
    deserialize_message,
    try_deserialize_message,
    compute_message_id,
)

FORBIDDEN_MODULES = {
    "socket", "subprocess", "urllib", "requests", "http", "os", "sys",
}


def _job(**overrides) -> JobContract:
    kwargs = dict(
        control_marker="SYNAPSYS_AGENT_GITHUB__TEST_JOB",
        origin_lane="claude_code",
        target_lane="gpt",
        role="architect",
        context_id="CTX-SS",
        work_object_id="WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001",
        state_revision="239",
        objective="test objective",
        source_refs="candidate-skills/synapsys-agent-job-relay/outbox.py",
        reality_state="Candidate code",
        ppv_state="Potential_HELD",
        authority_state="RELAY_REQUEST_ONLY__NO_MUTATION",
        owner_lane="claude_code",
        stop_hold="NONE",
        required_return="",
        next_action="Review and respond",
        replay_validity="PRESERVED",
        origin_signal="test origin",
        stream="platform-capability",
        processor_route="produce -> relay -> await response",
        distribution_class="centre",
        filing_state="FILED",
        exception_route="NONE",
        status="proposed",
        replay_hash="placeholder",
    )
    kwargs.update(overrides)
    job = JobContract(**kwargs)
    return JobContract(**{**kwargs, "replay_hash": compute_replay_hash(job)})


def test_isolation_no_forbidden_imports():
    path = os.path.join(os.path.dirname(__file__), "..", "outbox.py")
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
    assert not forbidden_found, f"Forbidden imports found: {forbidden_found}"


def test_build_message_from_valid_job():
    job = _job()
    msg = build_message(job, enqueued_at_iso="2026-08-14T10:00:00")
    assert msg.status == "proposed"
    assert msg.job == job
    assert msg.claimed_by is None


def test_build_message_rejects_invalid_job():
    job = _job(target_lane="chatgpt")  # out of vocabulary
    try:
        build_message(job, enqueued_at_iso="2026-08-14T10:00:00")
        assert False, "expected ValueError"
    except ValueError as e:
        assert "invalid JobContract" in str(e)


def test_compute_message_id_deterministic():
    job = _job()
    id_1 = compute_message_id(job, "2026-08-14T10:00:00")
    id_2 = compute_message_id(job, "2026-08-14T10:00:00")
    assert id_1 == id_2
    assert len(id_1) == 16


def test_compute_message_id_changes_with_enqueue_time():
    job = _job()
    id_1 = compute_message_id(job, "2026-08-14T10:00:00")
    id_2 = compute_message_id(job, "2026-08-14T11:00:00")
    assert id_1 != id_2


def test_claim_transitions_to_active():
    job = _job()
    msg = build_message(job, "2026-08-14T10:00:00")
    claimed = claim(msg, claimed_by="claude_code", claimed_at_iso="2026-08-14T10:05:00")
    assert claimed.status == "active"
    assert claimed.claimed_by == "claude_code"
    assert claimed.claimed_at_iso == "2026-08-14T10:05:00"
    # original message is unchanged -- frozen, pure transition
    assert msg.status == "proposed"


def test_claim_rejects_already_claimed_message():
    job = _job()
    msg = build_message(job, "2026-08-14T10:00:00")
    claimed = claim(msg, "claude_code", "2026-08-14T10:05:00")
    try:
        claim(claimed, "gemini_d009", "2026-08-14T10:06:00")
        assert False, "expected ValueError"
    except ValueError as e:
        assert "not 'proposed'" in str(e)


def test_complete_transitions_active_to_closed():
    job = _job()
    msg = build_message(job, "2026-08-14T10:00:00")
    claimed = claim(msg, "claude_code", "2026-08-14T10:05:00")
    done = complete(claimed, status="closed")
    assert done.status == "closed"


def test_complete_rejects_non_active_message():
    job = _job()
    msg = build_message(job, "2026-08-14T10:00:00")
    try:
        complete(msg, status="closed")
        assert False, "expected ValueError"
    except ValueError as e:
        assert "not 'active'" in str(e)


def test_complete_rejects_invalid_status_argument():
    job = _job()
    msg = build_message(job, "2026-08-14T10:00:00")
    claimed = claim(msg, "claude_code", "2026-08-14T10:05:00")
    try:
        complete(claimed, status="proposed")
        assert False, "expected ValueError"
    except ValueError as e:
        assert "returned/closed/blocked" in str(e)


def test_select_claimable_filters_by_status_and_processor():
    job_gpt = _job(target_lane="gpt")
    job_codex = _job(target_lane="codex", next_action="Verify a claim")
    msg_gpt = build_message(job_gpt, "2026-08-14T10:00:00")
    msg_codex = build_message(job_codex, "2026-08-14T10:01:00")
    msg_gpt_claimed = claim(msg_gpt, "chatgpt_hub", "2026-08-14T10:02:00")

    claimable = select_claimable([msg_gpt, msg_codex, msg_gpt_claimed], processor="gpt")
    assert msg_gpt in claimable
    assert msg_codex not in claimable
    assert msg_gpt_claimed not in claimable  # already active, not proposed


def test_detect_stale_claims_flags_old_active_claims():
    job = _job()
    msg = build_message(job, "2026-08-14T10:00:00")
    claimed = claim(msg, "claude_code", claimed_at_iso="2026-08-14T10:00:00")
    stale = detect_stale_claims([claimed], now_iso="2026-08-14T12:00:00", max_claim_age_seconds=3600)
    assert claimed in stale


def test_detect_stale_claims_ignores_fresh_claims():
    job = _job()
    msg = build_message(job, "2026-08-14T10:00:00")
    claimed = claim(msg, "claude_code", claimed_at_iso="2026-08-14T10:00:00")
    stale = detect_stale_claims([claimed], now_iso="2026-08-14T10:10:00", max_claim_age_seconds=3600)
    assert stale == []


def test_detect_stale_claims_ignores_proposed_and_closed_messages():
    job = _job()
    msg = build_message(job, "2026-08-14T10:00:00")
    claimed = claim(msg, "claude_code", "2026-08-14T10:00:00")
    done = complete(claimed, status="closed")
    stale = detect_stale_claims([msg, done], now_iso="2026-08-14T20:00:00", max_claim_age_seconds=60)
    assert stale == []


def test_detect_stale_claims_flags_unparseable_claim_timestamp():
    job = _job()
    msg = build_message(job, "2026-08-14T10:00:00")
    claimed = claim(msg, "claude_code", claimed_at_iso="not-a-timestamp")
    stale = detect_stale_claims([claimed], now_iso="2026-08-14T10:10:00", max_claim_age_seconds=3600)
    assert claimed in stale


def test_outbox_filename_is_wm_naming_compliant():
    job = _job()
    msg = build_message(job, "2026-08-14T10:00:00")
    name = outbox_filename(msg, date_yyyymmdd="20260814", lane="claude-code")
    assert name.startswith("20260814--claude-code--job-outbox--job-outbox-")
    assert name.endswith("--v1-0.json")
    assert name == name.lower()


def test_serialize_deserialize_round_trip():
    job = _job()
    msg = build_message(job, "2026-08-14T10:00:00")
    claimed = claim(msg, "claude_code", "2026-08-14T10:05:00")
    data = serialize_message(claimed)
    restored = deserialize_message(data)
    assert restored == claimed


def test_try_deserialize_message_returns_none_on_old_schema_data():
    """Real-world case: two messages already sit in Working Memory,
    written under job_contract.py's earlier (v0.1) 15-field job shape,
    before this schema was reconciled per the accepted Navigator
    integration basis. A future poll must not crash on them."""
    old_schema_job = {
        "work_object_id": "WO-X", "origin_signal": "x", "stream": "S1",
        "owner": "claude_code", "processor": "gpt", "processor_route": "x",
        "distribution_class": "centre", "authority_state": "HELD",
        "evidence_state": "SUFFICIENT", "filing_state": "FILED",
        "return_packet": "", "next_valid_action": "x",
        "exception_route": "NONE", "replay_hash": "abc", "status": "closed",
    }
    old_message = {
        "message_id": "old123", "job": old_schema_job,
        "enqueued_at_iso": "2026-08-14T00:00:00", "status": "closed",
        "claimed_by": None, "claimed_at_iso": None,
    }
    assert try_deserialize_message(old_message) is None


def test_try_deserialize_message_returns_message_on_current_schema():
    job = _job()
    msg = build_message(job, "2026-08-14T10:00:00")
    data = serialize_message(msg)
    result = try_deserialize_message(data)
    assert result == msg


def test_serialize_deserialize_round_trip_unclaimed_message():
    """claimed_by/claimed_at_iso default to None on a never-claimed
    message -- round trip must preserve that, not coerce to empty string
    or drop the keys."""
    job = _job()
    msg = build_message(job, "2026-08-14T10:00:00")
    data = serialize_message(msg)
    assert data["claimed_by"] is None
    restored = deserialize_message(data)
    assert restored == msg
