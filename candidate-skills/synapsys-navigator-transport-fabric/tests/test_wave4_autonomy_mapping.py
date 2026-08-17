"""Tests for wave4_autonomy_mapping.py.

These don't just check the mapping module is internally consistent -- they
cross-check its coverage against the real status/reason vocabularies
defined elsewhere in this package, so the mapping can't silently drift out
of sync with the code it describes.
"""

import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from transport_types import CLAIM_STATUSES, RUNTIME_RESULT_STATUSES
from wave4_autonomy_mapping import (
    AUTONOMY_LEVELS,
    CAPABILITY_AUTONOMY_MAP,
    GATE_RESULT_MAP,
    GATE_RESULT_VOCABULARY,
    HEALTH_STATUSES,
    PRESENTATION_ACTIONS,
    RETURN_CONTRACT_REASONS,
)


def test_gate_result_vocabulary_matches_programme_contract():
    """Pinned to the exact five values from the programme document's Wave 0
    Form section -- any drift here means the source document changed and
    this mapping needs deliberate re-review, not silent divergence."""
    assert GATE_RESULT_VOCABULARY == frozenset(
        {
            "AUTO_CONTINUE_WITHIN_DELEGATION",
            "HUMAN_DECISION",
            "HOLD_EVIDENCE",
            "HOLD_AUTHORITY",
            "EXCEPTION",
        }
    )


def test_autonomy_levels_match_programme_contract():
    assert AUTONOMY_LEVELS == (
        "A0_OBSERVE",
        "A1_RECOMMEND",
        "A2_ROUTE",
        "A3_PREPARE",
        "A4_EXECUTE_DELEGATED",
        "A5_EXCEPTION_AUTONOMY",
    )


def test_every_runtime_result_status_is_mapped():
    """Every real status in transport_types.RUNTIME_RESULT_STATUSES must
    have a corresponding GateResultMapping entry -- coverage is checked
    against the live frozenset, not retyped by hand."""
    mapped = {
        m.source_value
        for m in GATE_RESULT_MAP
        if m.source_module == "transport_types.RUNTIME_RESULT_STATUSES"
    }
    assert mapped == RUNTIME_RESULT_STATUSES


def test_every_return_contract_reason_is_mapped():
    mapped = {
        m.source_value
        for m in GATE_RESULT_MAP
        if m.source_module == "return_contract.validate_return_contract"
    }
    expected = RETURN_CONTRACT_REASONS - {"INVALID_D007_DECISION"}
    assert mapped == expected


def test_invalid_d007_decision_is_mapped():
    mapped = {
        m.source_value
        for m in GATE_RESULT_MAP
        if m.source_module == "human_approval_loop.consume_decision_return"
    }
    assert mapped == {"INVALID_D007_DECISION"}


def test_every_presentation_action_is_mapped():
    mapped = {
        m.source_value
        for m in GATE_RESULT_MAP
        if m.source_module == "human_approval_loop.present_for_decision"
    }
    assert mapped == PRESENTATION_ACTIONS


def test_every_health_status_is_mapped():
    mapped = {m.source_value for m in GATE_RESULT_MAP if m.source_module == "health_projection"}
    assert mapped == HEALTH_STATUSES


def test_all_canonical_results_are_valid():
    for m in GATE_RESULT_MAP:
        assert m.canonical_result in GATE_RESULT_VOCABULARY


def test_all_autonomy_classifications_are_valid_levels():
    for c in CAPABILITY_AUTONOMY_MAP:
        assert c.current_autonomy_level in AUTONOMY_LEVELS


def test_create_new_decision_always_maps_to_human_decision():
    """Load-bearing: opening a new D007 decision request must never be
    classified as anything this transport layer could act on itself."""
    entry = next(
        m
        for m in GATE_RESULT_MAP
        if m.source_module == "human_approval_loop.present_for_decision"
        and m.source_value == "CREATE_NEW"
    )
    assert entry.canonical_result == "HUMAN_DECISION"


def test_authority_defects_map_to_hold_authority_not_hold_evidence():
    """UNAUTHENTICATED_AUTHORITY / MISSING_AUTHORITY_REFERENCE /
    INVALID_D007_DECISION are authority defects, not evidence defects --
    conflating the two would blur exactly the distinction Wave 0 exists to
    make explicit."""
    authority_defect_sources = {
        ("return_contract.validate_return_contract", "UNAUTHENTICATED_AUTHORITY"),
        ("return_contract.validate_return_contract", "MISSING_AUTHORITY_REFERENCE"),
        ("human_approval_loop.consume_decision_return", "INVALID_D007_DECISION"),
        ("health_projection", "HELD"),
    }
    for m in GATE_RESULT_MAP:
        if (m.source_module, m.source_value) in authority_defect_sources:
            assert m.canonical_result == "HOLD_AUTHORITY", (m.source_module, m.source_value)


def test_no_capability_is_classified_above_a3_prepare():
    """This package performs zero I/O and wires no live adapter -- nothing
    in it can actually execute or run unattended, so nothing in it may
    claim A4_EXECUTE_DELEGATED or A5_EXCEPTION_AUTONOMY. Matches the
    programme's own 'no Agent self-authorisation' deleted-scope rule."""
    disallowed = {"A4_EXECUTE_DELEGATED", "A5_EXCEPTION_AUTONOMY"}
    for c in CAPABILITY_AUTONOMY_MAP:
        assert c.current_autonomy_level not in disallowed, c.capability


def test_human_decision_creation_capability_is_capped_at_a1():
    """present_for_decision must never be classified above A1_RECOMMEND --
    it recommends SURFACE_EXISTING vs CREATE_NEW but must never itself be
    trusted to act on that recommendation."""
    entry = next(
        c
        for c in CAPABILITY_AUTONOMY_MAP
        if "present_for_decision" in c.capability
    )
    assert entry.current_autonomy_level == "A1_RECOMMEND"


def test_notify_only_transports_stay_at_a0_observe():
    for c in CAPABILITY_AUTONOMY_MAP:
        if "github_transport" in c.capability or "email_transport" in c.capability:
            assert c.current_autonomy_level == "A0_OBSERVE"


def test_every_capability_string_names_a_real_function():
    """Catches exactly the class of error this test was added to fix: an
    earlier revision named 'registry_resolver.resolve_route', but the real
    function is 'resolve_endpoint'. Every capability string is parsed as
    'module.func[ / func2][ / module2.func3]' and each named function is
    checked to actually exist on its module via getattr -- a typo or a
    future rename in the real modules fails this test instead of silently
    documenting something that no longer exists."""
    for c in CAPABILITY_AUTONOMY_MAP:
        segments = c.capability.split(" / ")
        first_module_name, first_func = segments[0].split(".", 1)
        module_obj = importlib.import_module(first_module_name)
        assert hasattr(module_obj, first_func), c.capability
        current_module_obj = module_obj
        for seg in segments[1:]:
            if "." in seg:
                mod_name, func_name = seg.split(".", 1)
                current_module_obj = importlib.import_module(mod_name)
            else:
                func_name = seg
            assert hasattr(current_module_obj, func_name), c.capability
