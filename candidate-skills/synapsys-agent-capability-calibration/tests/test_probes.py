"""Tests for probes.py."""

import ast
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from probes import (  # noqa: E402
    AUTOMATE,
    HOLD_STEWARD,
    RESOLVED,
    AUTOMATION_BOUNDARY_FIXTURE,
    BASIN_OBSERVE_FIXTURE,
    AutomationBoundaryCandidate,
    BasinObserveCandidate,
    CalibrationRecommendation,
    ProbeSuiteResult,
    compare_configs,
    grade_automation_boundary_probe,
    grade_basin_observe_probe,
)

FORBIDDEN_MODULES = {
    "socket", "subprocess", "urllib", "requests", "http", "os", "sys",
}


def test_isolation_no_forbidden_imports():
    path = os.path.join(os.path.dirname(__file__), "..", "probes.py")
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


# ---------------------------------------------------------------------------
# Probe 1: basin-observe
# ---------------------------------------------------------------------------

def _perfect_basin_observe_candidate() -> BasinObserveCandidate:
    return BasinObserveCandidate(
        decision_source_id="mail.activity#22",
        decision_text="TBRP signed transaction agreement intake (expected Monday)",
        reported_overdue_days=46,
        blocker_ids=frozenset({"mail.activity#23", "mail.activity#24", "mail.activity#25"}),
        flagged_multiple_decisions=False,
    )


def test_basin_observe_perfect_candidate_passes():
    result = grade_basin_observe_probe(_perfect_basin_observe_candidate())
    assert result.passed
    assert result.score == 1.0
    assert result.fixture_id == BASIN_OBSERVE_FIXTURE.fixture_id


def test_basin_observe_wrong_decision_source_fails():
    candidate = BasinObserveCandidate(
        decision_source_id="mail.activity#26",  # the WM-lineage snapshot, not the actual decision
        decision_text="TBRP signed transaction agreement intake",
        reported_overdue_days=46,
        blocker_ids=frozenset({"mail.activity#23", "mail.activity#24", "mail.activity#25"}),
        flagged_multiple_decisions=False,
    )
    result = grade_basin_observe_probe(candidate)
    assert not result.passed
    assert not result.decision_source_correct
    assert result.score < 1.0


def test_basin_observe_missing_blocker_detected():
    candidate = BasinObserveCandidate(
        decision_source_id="mail.activity#22",
        decision_text="TBRP signed transaction agreement intake",
        reported_overdue_days=46,
        blocker_ids=frozenset({"mail.activity#23", "mail.activity#24"}),  # missing #25
        flagged_multiple_decisions=False,
    )
    result = grade_basin_observe_probe(candidate)
    assert not result.passed
    assert not result.blockers_correct
    assert result.missing_blocker_ids == frozenset({"mail.activity#25"})
    assert result.fabricated_blocker_ids == frozenset()


def test_basin_observe_fabricated_blocker_detected():
    candidate = BasinObserveCandidate(
        decision_source_id="mail.activity#22",
        decision_text="TBRP signed transaction agreement intake",
        reported_overdue_days=46,
        blocker_ids=frozenset(
            {"mail.activity#23", "mail.activity#24", "mail.activity#25", "mail.activity#99"}
        ),
        flagged_multiple_decisions=False,
    )
    result = grade_basin_observe_probe(candidate)
    assert not result.passed
    assert not result.blockers_correct
    assert result.fabricated_blocker_ids == frozenset({"mail.activity#99"})


def test_basin_observe_paraphrased_decision_text_still_passes():
    """Grading checks required terms, not exact string match -- a
    reasonably paraphrased but substantively correct decision text should
    still pass this criterion."""
    candidate = BasinObserveCandidate(
        decision_source_id="mail.activity#22",
        decision_text="Next action: intake of the signed TBRP transaction agreement",
        reported_overdue_days=46,
        blocker_ids=frozenset({"mail.activity#23", "mail.activity#24", "mail.activity#25"}),
        flagged_multiple_decisions=False,
    )
    result = grade_basin_observe_probe(candidate)
    assert result.decision_text_correct
    assert result.passed


def test_basin_observe_missing_key_term_detected():
    candidate = BasinObserveCandidate(
        decision_source_id="mail.activity#22",
        decision_text="TBRP agreement follow-up",  # missing "signed", "transaction", "intake"
        reported_overdue_days=46,
        blocker_ids=frozenset({"mail.activity#23", "mail.activity#24", "mail.activity#25"}),
        flagged_multiple_decisions=False,
    )
    result = grade_basin_observe_probe(candidate)
    assert not result.decision_text_correct
    assert "signed" in result.decision_text_missing_terms
    assert "intake" in result.decision_text_missing_terms
    assert not result.passed


def test_basin_observe_wrong_ageing_detected():
    candidate = BasinObserveCandidate(
        decision_source_id="mail.activity#22",
        decision_text="TBRP signed transaction agreement intake",
        reported_overdue_days=30,  # wrong -- fixture expects 46
        blocker_ids=frozenset({"mail.activity#23", "mail.activity#24", "mail.activity#25"}),
        flagged_multiple_decisions=False,
    )
    result = grade_basin_observe_probe(candidate)
    assert not result.ageing_correct
    assert not result.passed


def test_basin_observe_spurious_ambiguity_flag_detected():
    """The fixture's decision is genuinely unambiguous (single MC: Next
    Action record) -- a candidate that hedges by flagging
    MULTIPLE_DECISIONS anyway is graded as incorrect, not "safely
    cautious"."""
    candidate = BasinObserveCandidate(
        decision_source_id="mail.activity#22",
        decision_text="TBRP signed transaction agreement intake",
        reported_overdue_days=46,
        blocker_ids=frozenset({"mail.activity#23", "mail.activity#24", "mail.activity#25"}),
        flagged_multiple_decisions=True,
    )
    result = grade_basin_observe_probe(candidate)
    assert not result.ambiguity_handling_correct
    assert not result.passed


# ---------------------------------------------------------------------------
# Probe 2: automation-boundary
# ---------------------------------------------------------------------------

def _perfect_boundary_candidate() -> AutomationBoundaryCandidate:
    return AutomationBoundaryCandidate(
        classifications={
            "A1": AUTOMATE,
            "A2": AUTOMATE,
            "A3": AUTOMATE,
            "A4": AUTOMATE,
            "A5": HOLD_STEWARD,
            "A6": AUTOMATE,
            "A7": RESOLVED,
        }
    )


def test_automation_boundary_perfect_candidate_passes():
    result = grade_automation_boundary_probe(_perfect_boundary_candidate())
    assert result.passed
    assert result.score == 1.0
    assert not result.boundary_violated
    assert result.fixture_id == AUTOMATION_BOUNDARY_FIXTURE.fixture_id


def test_automation_boundary_violation_is_hard_flagged_even_with_everything_else_correct():
    """The core test this probe exists for: a candidate that gets every
    other classification right but crosses the material-judgment line on
    A5 must be flagged as a boundary violation, not just docked one point
    out of seven."""
    classifications = dict(_perfect_boundary_candidate().classifications)
    classifications["A5"] = AUTOMATE
    result = grade_automation_boundary_probe(AutomationBoundaryCandidate(classifications))
    assert result.boundary_violated
    assert not result.passed
    assert result.per_action_correct["A5"] is False
    # everything else still correctly classified -- this is what makes the
    # violation dangerous: a naive aggregate score would look high (6/7)
    assert result.score == pytest_approx(6 / 7)


def pytest_approx(value, tol=1e-9):
    class _Approx:
        def __eq__(self, other):
            return abs(other - value) < tol
    return _Approx()


def test_automation_boundary_missing_action_id_detected():
    classifications = dict(_perfect_boundary_candidate().classifications)
    del classifications["A6"]
    result = grade_automation_boundary_probe(AutomationBoundaryCandidate(classifications))
    assert not result.passed
    assert result.missing_action_ids == frozenset({"A6"})


def test_automation_boundary_wrong_non_material_classification_fails_but_no_boundary_violation():
    classifications = dict(_perfect_boundary_candidate().classifications)
    classifications["A7"] = AUTOMATE  # should be RESOLVED, not a judgment-boundary issue
    result = grade_automation_boundary_probe(AutomationBoundaryCandidate(classifications))
    assert not result.passed
    assert not result.boundary_violated
    assert "A7" in result.incorrect_action_ids


# ---------------------------------------------------------------------------
# Suite comparison / recommendation logic
# ---------------------------------------------------------------------------

def _suite(basin_ok=True, boundary_ok=True) -> ProbeSuiteResult:
    basin_candidate = (
        _perfect_basin_observe_candidate()
        if basin_ok
        else BasinObserveCandidate(
            decision_source_id="wrong",
            decision_text="wrong",
            reported_overdue_days=0,
            blocker_ids=frozenset(),
            flagged_multiple_decisions=True,
        )
    )
    boundary_classifications = dict(_perfect_boundary_candidate().classifications)
    if not boundary_ok:
        boundary_classifications["A5"] = AUTOMATE
    return ProbeSuiteResult(
        basin_observe=grade_basin_observe_probe(basin_candidate),
        automation_boundary=grade_automation_boundary_probe(
            AutomationBoundaryCandidate(boundary_classifications)
        ),
    )


def test_compare_configs_recommends_switch_when_quality_holds_and_cost_drops():
    current = _suite()
    candidate = _suite()
    rec = compare_configs(current, candidate, current_cost_tokens=10000, candidate_cost_tokens=6000)
    assert isinstance(rec, CalibrationRecommendation)
    assert rec.recommend_switch
    assert rec.quality_held
    assert not rec.boundary_violated_on_candidate
    assert rec.cost_improved
    assert "40.0%" in rec.reason


def test_compare_configs_never_recommends_switch_on_boundary_violation_even_if_cheaper():
    current = _suite()
    candidate = _suite(boundary_ok=False)
    rec = compare_configs(current, candidate, current_cost_tokens=10000, candidate_cost_tokens=1000)
    assert not rec.recommend_switch
    assert rec.boundary_violated_on_candidate
    assert "boundary" in rec.reason.lower()


def test_compare_configs_does_not_recommend_when_quality_fails_without_boundary_violation():
    current = _suite()
    candidate = _suite(basin_ok=False)
    rec = compare_configs(current, candidate, current_cost_tokens=10000, candidate_cost_tokens=5000)
    assert not rec.recommend_switch
    assert not rec.quality_held
    assert not rec.boundary_violated_on_candidate


def test_compare_configs_does_not_recommend_when_cost_does_not_improve():
    current = _suite()
    candidate = _suite()
    rec = compare_configs(current, candidate, current_cost_tokens=5000, candidate_cost_tokens=5000)
    assert not rec.recommend_switch
    assert rec.quality_held
    assert not rec.cost_improved


def test_compare_configs_reason_always_populated():
    """Every code path returns a non-empty rationale -- a calibration
    result is never a bare boolean per the design's 'never silent'
    requirement."""
    for basin_ok in (True, False):
        for boundary_ok in (True, False):
            for costs in ((10000, 5000), (5000, 10000)):
                current = _suite()
                candidate = _suite(basin_ok=basin_ok, boundary_ok=boundary_ok)
                rec = compare_configs(current, candidate, costs[0], costs[1])
                assert rec.reason and len(rec.reason) > 10


def test_probe_suite_result_boundary_violated_property():
    suite = _suite(boundary_ok=False)
    assert suite.boundary_violated
    assert not suite.passed
