"""Tests for requirement_routing.py.

Covers every HOLD_EVIDENCE branch of the chain (no candidate context, unknown
context, no eligible service, ambiguous eligible services, no method
candidate, ambiguous method candidates) plus the single
AUTO_CONTINUE_WITHIN_DELEGATION success path, and confirms the module stays
zero-I/O and never produces a gate result outside its declared subset.
"""

import ast
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from requirement_routing import (
    ROUTING_GATE_RESULTS,
    MethodCandidateRow,
    RequirementSignal,
    ServiceActivationRow,
    WorkObjectBindingRecommendation,
    eligible_services_for_context,
    recommend_work_object_binding,
    resolve_context,
    select_minimum_method,
)
from wave4_autonomy_mapping import GATE_RESULT_VOCABULARY

FORBIDDEN_IMPORTS = {"socket", "subprocess", "urllib", "requests", "http", "os.system"}


def test_module_has_no_forbidden_imports():
    """This module claims zero I/O -- enforce it by parsing its own source
    rather than trusting the docstring."""
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "requirement_routing.py")
    with open(path) as f:
        tree = ast.parse(f.read(), filename=path)
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    assert not (names & FORBIDDEN_IMPORTS), names


def test_routing_gate_results_is_subset_of_programme_vocabulary():
    assert ROUTING_GATE_RESULTS <= GATE_RESULT_VOCABULARY
    assert ROUTING_GATE_RESULTS == {"AUTO_CONTINUE_WITHIN_DELEGATION", "HOLD_EVIDENCE"}


def _signal(candidate_context_id="ctx-1", signal_id="sig-1"):
    return RequirementSignal(
        signal_id=signal_id,
        description="test signal",
        candidate_context_id=candidate_context_id,
        detected_at_iso="2026-08-17T00:00:00Z",
        source="test",
    )


def test_resolve_context_holds_when_no_candidate_context():
    result = resolve_context(_signal(candidate_context_id=None), known_context_ids=frozenset({"ctx-1"}))
    assert not result.resolved
    assert result.reason.startswith("NO_CANDIDATE_CONTEXT")


def test_resolve_context_holds_when_context_unknown():
    result = resolve_context(_signal(candidate_context_id="ctx-9"), known_context_ids=frozenset({"ctx-1"}))
    assert not result.resolved
    assert result.reason.startswith("UNKNOWN_CONTEXT")


def test_resolve_context_resolves_known_context():
    result = resolve_context(_signal(candidate_context_id="ctx-1"), known_context_ids=frozenset({"ctx-1"}))
    assert result.resolved
    assert result.context_id == "ctx-1"


def test_eligible_services_filters_by_context_and_active_status():
    activations = [
        ServiceActivationRow(context_id="ctx-1", service_code="svc-a", activation_status="active"),
        ServiceActivationRow(context_id="ctx-1", service_code="svc-b", activation_status="suspended"),
        ServiceActivationRow(context_id="ctx-2", service_code="svc-c", activation_status="active"),
    ]
    results = eligible_services_for_context("ctx-1", activations)
    assert {r.service_code for r in results} == {"svc-a", "svc-b"}
    assert next(r for r in results if r.service_code == "svc-a").eligible
    assert not next(r for r in results if r.service_code == "svc-b").eligible


def test_select_minimum_method_no_candidates():
    result = select_minimum_method("svc-a", [])
    assert result.method_id is None
    assert result.rationale.startswith("NO_METHOD")


def test_select_minimum_method_ambiguous():
    candidates = [
        MethodCandidateRow(service_code="svc-a", method_id="m1"),
        MethodCandidateRow(service_code="svc-a", method_id="m2"),
    ]
    result = select_minimum_method("svc-a", candidates)
    assert result.method_id is None
    assert result.rationale.startswith("AMBIGUOUS_METHOD")


def test_select_minimum_method_unique_match():
    candidates = [MethodCandidateRow(service_code="svc-a", method_id="m1")]
    result = select_minimum_method("svc-a", candidates)
    assert result.method_id == "m1"
    assert result.rationale == "UNIQUE_MATCH"


def test_binding_recommendation_rejects_result_outside_routing_gate_results():
    with pytest.raises(ValueError):
        WorkObjectBindingRecommendation("sig-1", "HUMAN_DECISION", None, None, None, "invalid")


def test_full_chain_holds_on_no_candidate_context():
    rec = recommend_work_object_binding(
        _signal(candidate_context_id=None), frozenset({"ctx-1"}), [], []
    )
    assert rec.gate_result == "HOLD_EVIDENCE"
    assert rec.reason.startswith("NO_CANDIDATE_CONTEXT")
    assert rec.context_id is None


def test_full_chain_holds_on_unknown_context():
    rec = recommend_work_object_binding(
        _signal(candidate_context_id="ctx-9"), frozenset({"ctx-1"}), [], []
    )
    assert rec.gate_result == "HOLD_EVIDENCE"
    assert rec.reason.startswith("UNKNOWN_CONTEXT")


def test_full_chain_holds_on_no_eligible_service():
    rec = recommend_work_object_binding(
        _signal(candidate_context_id="ctx-1"),
        frozenset({"ctx-1"}),
        [ServiceActivationRow(context_id="ctx-1", service_code="svc-a", activation_status="suspended")],
        [],
    )
    assert rec.gate_result == "HOLD_EVIDENCE"
    assert rec.reason.startswith("NO_ELIGIBLE_SERVICE")
    assert rec.context_id == "ctx-1"


def test_full_chain_holds_on_ambiguous_eligible_services():
    rec = recommend_work_object_binding(
        _signal(candidate_context_id="ctx-1"),
        frozenset({"ctx-1"}),
        [
            ServiceActivationRow(context_id="ctx-1", service_code="svc-a", activation_status="active"),
            ServiceActivationRow(context_id="ctx-1", service_code="svc-b", activation_status="active"),
        ],
        [],
    )
    assert rec.gate_result == "HOLD_EVIDENCE"
    assert rec.reason.startswith("AMBIGUOUS_SERVICE_SELECTION")


def test_full_chain_holds_on_no_method_candidate():
    rec = recommend_work_object_binding(
        _signal(candidate_context_id="ctx-1"),
        frozenset({"ctx-1"}),
        [ServiceActivationRow(context_id="ctx-1", service_code="svc-a", activation_status="active")],
        [],
    )
    assert rec.gate_result == "HOLD_EVIDENCE"
    assert rec.reason.startswith("NO_METHOD")
    assert rec.service_code == "svc-a"


def test_full_chain_holds_on_ambiguous_method_candidates():
    rec = recommend_work_object_binding(
        _signal(candidate_context_id="ctx-1"),
        frozenset({"ctx-1"}),
        [ServiceActivationRow(context_id="ctx-1", service_code="svc-a", activation_status="active")],
        [
            MethodCandidateRow(service_code="svc-a", method_id="m1"),
            MethodCandidateRow(service_code="svc-a", method_id="m2"),
        ],
    )
    assert rec.gate_result == "HOLD_EVIDENCE"
    assert rec.reason.startswith("AMBIGUOUS_METHOD")


def test_full_chain_success_path():
    rec = recommend_work_object_binding(
        _signal(candidate_context_id="ctx-1"),
        frozenset({"ctx-1"}),
        [ServiceActivationRow(context_id="ctx-1", service_code="svc-a", activation_status="active")],
        [MethodCandidateRow(service_code="svc-a", method_id="m1")],
    )
    assert rec.gate_result == "AUTO_CONTINUE_WITHIN_DELEGATION"
    assert rec.context_id == "ctx-1"
    assert rec.service_code == "svc-a"
    assert rec.method_id == "m1"


def test_chain_never_returns_result_outside_routing_gate_results():
    """No combination of inputs this chain can see should ever escape the
    declared two-value subset -- authority/human-decision/exception states
    are structurally out of reach for a pure recommendation chain."""
    scenarios = [
        (_signal(candidate_context_id=None), frozenset(), [], []),
        (_signal(candidate_context_id="ctx-1"), frozenset({"ctx-1"}), [], []),
        (
            _signal(candidate_context_id="ctx-1"),
            frozenset({"ctx-1"}),
            [ServiceActivationRow(context_id="ctx-1", service_code="svc-a", activation_status="active")],
            [MethodCandidateRow(service_code="svc-a", method_id="m1")],
        ),
    ]
    for signal, known_ctx, activations, methods in scenarios:
        rec = recommend_work_object_binding(signal, known_ctx, activations, methods)
        assert rec.gate_result in ROUTING_GATE_RESULTS
