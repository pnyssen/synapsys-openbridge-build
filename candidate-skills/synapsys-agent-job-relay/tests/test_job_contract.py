"""Tests for job_contract.py. Fixtures 1 and 2 are modeled after two real
dispatches actually filed this session --
20260812--claude-code--dispatch--wave-accelerator-alignment-request--v1-0.md
and
20260814--claude-code--dispatch--synapsys-agent-full-ecosystem-design-relay--v1-0.md
-- reconstructed into this schema's shape to show it can represent real,
already-filed work, not synthetic examples. Neither original document
used this schema when filed (the schema didn't exist yet); this is the
gap it fills, not a claim those documents were already structured this
way."""

import ast
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from job_contract import (  # noqa: E402
    JobContract,
    ValidationResult,
    PROCESSOR_VALUES,
    STATUS_VALUES,
    STREAM_VALUES,
    DISTRIBUTION_CLASS_VALUES,
    PROCESSOR_ROLE_TABLE,
    role_table_for,
    compute_replay_hash,
    looks_like_multiple_actions,
    validate_job_contract,
    detect_unquoted_authority_claim,
    to_dict,
    from_dict,
)

FORBIDDEN_MODULES = {
    "socket", "subprocess", "urllib", "requests", "http", "os", "sys",
}


def _base_kwargs(**overrides):
    kwargs = dict(
        work_object_id="WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001",
        origin_signal="Steward direct instruction",
        stream="platform-capability",
        owner="claude_code",
        processor="gpt",
        processor_route="produce -> relay -> await Hub response",
        distribution_class="centre",
        authority_state="RELAY_REQUEST_ONLY__NO_MUTATION__PHIL_RELAYS_MANUALLY",
        evidence_state="SUFFICIENT_FOR_REQUEST",
        filing_state="FILED",
        return_packet="",
        next_valid_action="ChatGPT Hub reviews and responds",
        exception_route="NONE",
        replay_hash="",
        status="proposed",
    )
    kwargs.update(overrides)
    return kwargs


def _valid_job(**overrides) -> JobContract:
    kwargs = _base_kwargs(**overrides)
    job = JobContract(**{**kwargs, "replay_hash": "placeholder"})
    real_hash = compute_replay_hash(job)
    kwargs["replay_hash"] = real_hash
    return JobContract(**kwargs)


def test_isolation_no_forbidden_imports():
    """Mirrors freshness.py's own AST isolation check."""
    path = os.path.join(os.path.dirname(__file__), "..", "job_contract.py")
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


def test_valid_job_validates_ok():
    job = _valid_job()
    result = validate_job_contract(job)
    assert result.ok, result.errors


def test_all_processor_values_accepted():
    for p in PROCESSOR_VALUES:
        job = _valid_job(processor=p)
        assert validate_job_contract(job).ok, f"processor {p} should validate"


def test_out_of_vocabulary_processor_holds():
    job = _valid_job(processor="chatgpt")
    result = validate_job_contract(job)
    assert not result.ok
    assert any("processor" in e for e in result.errors)


def test_out_of_vocabulary_status_holds():
    job = _valid_job(status="pending")
    result = validate_job_contract(job)
    assert not result.ok
    assert any("status" in e for e in result.errors)


def test_out_of_vocabulary_stream_holds():
    job = _valid_job(stream="misc")
    result = validate_job_contract(job)
    assert not result.ok
    assert any("stream" in e for e in result.errors)


def test_out_of_vocabulary_distribution_class_holds():
    job = _valid_job(distribution_class="global")
    result = validate_job_contract(job)
    assert not result.ok
    assert any("distribution_class" in e for e in result.errors)


def test_empty_work_object_id_holds():
    job = _valid_job(work_object_id="")
    result = validate_job_contract(job)
    assert not result.ok
    assert any("work_object_id" in e for e in result.errors)


def test_empty_next_valid_action_holds():
    job = _valid_job(next_valid_action="")
    result = validate_job_contract(job)
    assert not result.ok
    assert any("next_valid_action must not be empty" in e for e in result.errors)


def test_plural_next_valid_action_flagged():
    job = _valid_job(next_valid_action="Do the first thing; then do the second thing")
    result = validate_job_contract(job)
    assert not result.ok
    assert any("more than one action" in e for e in result.errors)


def test_empty_authority_state_holds():
    job = _valid_job(authority_state="")
    result = validate_job_contract(job)
    assert not result.ok
    assert any("authority_state" in e for e in result.errors)


def test_empty_evidence_state_holds():
    job = _valid_job(evidence_state="")
    result = validate_job_contract(job)
    assert not result.ok
    assert any("evidence_state" in e for e in result.errors)


def test_empty_replay_hash_holds():
    kwargs = _base_kwargs(replay_hash="")
    job = JobContract(**kwargs)
    result = validate_job_contract(job)
    assert not result.ok
    assert any("replay_hash" in e for e in result.errors)


def test_compute_replay_hash_deterministic():
    job = _valid_job()
    assert compute_replay_hash(job) == compute_replay_hash(job)


def test_compute_replay_hash_changes_with_content():
    job_a = _valid_job(next_valid_action="Action A")
    job_b = _valid_job(next_valid_action="Action B")
    assert compute_replay_hash(job_a) != compute_replay_hash(job_b)


def test_compute_replay_hash_ignores_current_replay_hash_field():
    """The hash must be stable regardless of what garbage is currently
    sitting in the replay_hash field being replaced -- it's excluded from
    the payload that gets hashed."""
    kwargs = _base_kwargs(replay_hash="garbage-1")
    job_1 = JobContract(**kwargs)
    kwargs["replay_hash"] = "garbage-2-totally-different"
    job_2 = JobContract(**kwargs)
    assert compute_replay_hash(job_1) == compute_replay_hash(job_2)


def test_round_trip_to_dict_from_dict_zero_field_loss():
    """T-A from sk07-agent-handoff: emit 15-field packet -> parse -> zero
    field loss."""
    job = _valid_job()
    data = to_dict(job)
    assert len(data) == 15
    restored = from_dict(data)
    assert restored == job


def test_from_dict_missing_field_raises():
    job = _valid_job()
    data = to_dict(job)
    del data["next_valid_action"]
    try:
        from_dict(data)
        assert False, "expected ValueError"
    except ValueError as e:
        assert "next_valid_action" in str(e)


def test_from_dict_extra_field_raises():
    job = _valid_job()
    data = to_dict(job)
    data["unexpected_field"] = "surprise"
    try:
        from_dict(data)
        assert False, "expected ValueError"
    except ValueError as e:
        assert "unexpected_field" in str(e)


def test_role_table_for_known_processor():
    table = role_table_for("gpt")
    assert table is not None
    assert "execute" in table["must_not"]
    assert "route" in table["may"]


def test_role_table_for_unknown_processor_returns_none():
    assert role_table_for("chatgpt") is None


def test_role_table_covers_every_processor_value():
    """Regression guard: every value in the closed vocabulary must have a
    role-table entry, or validate_job_contract() could accept a processor
    this module has no role guidance for."""
    for p in PROCESSOR_VALUES:
        assert p in PROCESSOR_ROLE_TABLE, f"processor '{p}' missing from PROCESSOR_ROLE_TABLE"


def test_detect_unquoted_authority_claim_flags_grant_language():
    result = detect_unquoted_authority_claim(
        "This work is approved for execution", carries_quoted_reference=False,
    )
    assert result == "approved for execution"


def test_detect_unquoted_authority_claim_clean_when_reference_present():
    result = detect_unquoted_authority_claim(
        "This work is approved for execution", carries_quoted_reference=True,
    )
    assert result is None


def test_detect_unquoted_authority_claim_clean_when_no_grant_language():
    result = detect_unquoted_authority_claim(
        "RELAY_REQUEST_ONLY__NO_MUTATION__PHIL_RELAYS_MANUALLY",
        carries_quoted_reference=False,
    )
    assert result is None


# --- Real session examples -------------------------------------------------

def test_real_example_wave_accelerator_request_validates_ok():
    """Modeled after 20260812--claude-code--dispatch--wave-accelerator-
    alignment-request--v1-0.md, actually filed and actually answered this
    session."""
    job = _valid_job(
        origin_signal="Steward named 'SynapSys Wave Accelerator' as ChatGPT Hub's pacing mechanism; this lane had no visibility into it",
        next_valid_action="ChatGPT Hub defines the Wave Accelerator mechanism and its plug-in point for the GitHub lane's candidate deliverables",
        return_packet="20260812--chatgpt-hub--dispatch--synapsys-agent-wave-accelerator-alignment-response--v1-0.md",
        status="returned",
    )
    result = validate_job_contract(job)
    assert result.ok, result.errors


def test_real_example_agent_design_relay_still_pending_validates_ok():
    """Modeled after 20260814--claude-code--dispatch--synapsys-agent-full-
    ecosystem-design-relay--v1-0.md, filed and, as of this test's
    writing, not yet answered -- return_packet is legitimately empty for
    a pending relay, which this schema must accept, not reject."""
    job = _valid_job(
        origin_signal="Steward asked for a complete SynapSys Agent design and its ecosystem integration",
        next_valid_action="ChatGPT Hub shares the Ask/Analyse prompt-builder field shape for reconciliation",
        return_packet="",
        status="active",
    )
    result = validate_job_contract(job)
    assert result.ok, result.errors
