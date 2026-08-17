"""Tests for shadow_pilot_metrics.py."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from shadow_pilot_metrics import (
    ClaimReplayEvent,
    RoutingPilotEvent,
    compute_claim_replay_metric,
    compute_hold_correctness,
    compute_routing_accuracy,
    compute_steward_intervention_rate,
)


def test_routing_pilot_event_rejects_unrecognised_gate_result():
    with pytest.raises(ValueError):
        RoutingPilotEvent(signal_id="s1", gate_result="HUMAN_DECISION", ground_truth_correct=None, steward_intervened=False)


def test_routing_accuracy_empty_events():
    metric = compute_routing_accuracy([])
    assert metric.total_auto_continue == 0
    assert metric.accuracy is None


def test_routing_accuracy_only_unreviewed_events_gives_none_accuracy():
    events = [
        RoutingPilotEvent("s1", "AUTO_CONTINUE_WITHIN_DELEGATION", None, False),
        RoutingPilotEvent("s2", "AUTO_CONTINUE_WITHIN_DELEGATION", None, False),
    ]
    metric = compute_routing_accuracy(events)
    assert metric.total_auto_continue == 2
    assert metric.not_yet_reviewed == 2
    assert metric.accuracy is None


def test_routing_accuracy_computed_only_over_reviewed_subset():
    events = [
        RoutingPilotEvent("s1", "AUTO_CONTINUE_WITHIN_DELEGATION", True, False),
        RoutingPilotEvent("s2", "AUTO_CONTINUE_WITHIN_DELEGATION", True, False),
        RoutingPilotEvent("s3", "AUTO_CONTINUE_WITHIN_DELEGATION", False, False),
        RoutingPilotEvent("s4", "AUTO_CONTINUE_WITHIN_DELEGATION", None, False),
        RoutingPilotEvent("s5", "HOLD_EVIDENCE", True, False),
    ]
    metric = compute_routing_accuracy(events)
    assert metric.total_auto_continue == 4
    assert metric.confirmed_correct == 2
    assert metric.confirmed_incorrect == 1
    assert metric.not_yet_reviewed == 1
    assert metric.accuracy == pytest.approx(2 / 3)


def test_hold_correctness_distinguishes_correct_from_false_holds():
    events = [
        RoutingPilotEvent("s1", "HOLD_EVIDENCE", True, False),
        RoutingPilotEvent("s2", "HOLD_EVIDENCE", False, False),
        RoutingPilotEvent("s3", "HOLD_EVIDENCE", False, False),
        RoutingPilotEvent("s4", "AUTO_CONTINUE_WITHIN_DELEGATION", True, False),
    ]
    metric = compute_hold_correctness(events)
    assert metric.total_holds == 3
    assert metric.correctly_held == 1
    assert metric.incorrectly_held == 2
    assert metric.correctness == pytest.approx(1 / 3)


def test_hold_correctness_no_holds_gives_none():
    metric = compute_hold_correctness([RoutingPilotEvent("s1", "AUTO_CONTINUE_WITHIN_DELEGATION", True, False)])
    assert metric.total_holds == 0
    assert metric.correctness is None


def test_claim_replay_metric_counts_and_replay_safe_true_when_no_incidents():
    events = [
        ClaimReplayEvent("m1", "GRANTED", False, False),
        ClaimReplayEvent("m1", "REFUSED", True, False),
        ClaimReplayEvent("m2", "GRANTED", False, False),
    ]
    metric = compute_claim_replay_metric(events)
    assert metric.total_claim_attempts == 3
    assert metric.granted == 2
    assert metric.refused == 1
    assert metric.replay_attempts == 1
    assert metric.duplicate_processing_incidents == 0
    assert metric.replay_safe is True


def test_claim_replay_metric_replay_safe_false_on_any_incident():
    events = [
        ClaimReplayEvent("m1", "GRANTED", False, False),
        ClaimReplayEvent("m1", "GRANTED", True, True),
    ]
    metric = compute_claim_replay_metric(events)
    assert metric.duplicate_processing_incidents == 1
    assert metric.replay_safe is False


def test_steward_intervention_rate_empty_events_gives_none():
    metric = compute_steward_intervention_rate([])
    assert metric.total_events == 0
    assert metric.intervention_rate is None


def test_steward_intervention_rate_computed_over_all_gate_results():
    events = [
        RoutingPilotEvent("s1", "AUTO_CONTINUE_WITHIN_DELEGATION", True, False),
        RoutingPilotEvent("s2", "HOLD_EVIDENCE", None, True),
        RoutingPilotEvent("s3", "HOLD_EVIDENCE", None, True),
        RoutingPilotEvent("s4", "AUTO_CONTINUE_WITHIN_DELEGATION", True, False),
    ]
    metric = compute_steward_intervention_rate(events)
    assert metric.total_events == 4
    assert metric.steward_interventions == 2
    assert metric.intervention_rate == pytest.approx(0.5)
