"""Wave 4 prep: shadow-pilot metrics computation.

Once Wave 4 opens and a bounded read-only/shadow pilot of
requirement_routing.py runs against real recorded events, this module is
what turns those recorded events into the evidence the recursive FFE
programme's autonomy-ladder promotion rule requires ("measured evidence per
transaction class, never self-promoted"): routing accuracy, HOLD
correctness, claim/replay behaviour, and Steward intervention rate.

Zero I/O: every function here takes caller-supplied recorded run events as
plain data and returns computed metrics. It reads no Odoo, no Working
Memory, no live state, and calls no clock -- the same discipline as the
rest of this package. This module does not run a pilot and does not decide
whether a promotion is warranted; it only scores a pilot's recorded
results after the fact, for a human (or the Steward) to judge against.
"""

from dataclasses import dataclass
from typing import List, Optional

from requirement_routing import ROUTING_GATE_RESULTS


@dataclass(frozen=True)
class RoutingPilotEvent:
    """One recorded outcome of requirement_routing.recommend_work_object_binding
    during a shadow pilot, plus a human/Steward's after-the-fact judgement of
    whether that recommendation was actually correct.

    ground_truth_correct is None until a human has reviewed it -- an
    unreviewed event contributes to neither the accuracy numerator nor
    denominator of confirmed cases, so accuracy is never computed on
    self-graded evidence.
    """

    signal_id: str
    gate_result: str
    ground_truth_correct: Optional[bool]
    steward_intervened: bool

    def __post_init__(self) -> None:
        if self.gate_result not in ROUTING_GATE_RESULTS:
            raise ValueError(f"unrecognised gate_result for a routing pilot event: {self.gate_result!r}")


@dataclass(frozen=True)
class ClaimReplayEvent:
    """One recorded claim attempt during a shadow pilot, claim_state_machine-shaped."""

    message_id: str
    claim_outcome: str  # "GRANTED" | "REFUSED"
    was_replay: bool
    duplicate_processing_detected: bool


@dataclass(frozen=True)
class RoutingAccuracyMetric:
    total_auto_continue: int
    confirmed_correct: int
    confirmed_incorrect: int
    not_yet_reviewed: int
    accuracy: Optional[float]


@dataclass(frozen=True)
class HoldCorrectnessMetric:
    total_holds: int
    correctly_held: int
    incorrectly_held: int
    not_yet_reviewed: int
    correctness: Optional[float]


@dataclass(frozen=True)
class ClaimReplayMetric:
    total_claim_attempts: int
    granted: int
    refused: int
    replay_attempts: int
    duplicate_processing_incidents: int
    replay_safe: bool


@dataclass(frozen=True)
class StewardInterventionMetric:
    total_events: int
    steward_interventions: int
    intervention_rate: Optional[float]


def compute_routing_accuracy(events: List[RoutingPilotEvent]) -> RoutingAccuracyMetric:
    """Of the AUTO_CONTINUE_WITHIN_DELEGATION recommendations, what fraction
    were confirmed correct by human/Steward review. Unreviewed events are
    counted but excluded from the accuracy ratio -- accuracy is never
    computed against a partially-reviewed set as if it were complete."""
    auto = [e for e in events if e.gate_result == "AUTO_CONTINUE_WITHIN_DELEGATION"]
    correct = [e for e in auto if e.ground_truth_correct is True]
    incorrect = [e for e in auto if e.ground_truth_correct is False]
    unreviewed = [e for e in auto if e.ground_truth_correct is None]
    reviewed_total = len(correct) + len(incorrect)
    accuracy = (len(correct) / reviewed_total) if reviewed_total else None
    return RoutingAccuracyMetric(
        total_auto_continue=len(auto),
        confirmed_correct=len(correct),
        confirmed_incorrect=len(incorrect),
        not_yet_reviewed=len(unreviewed),
        accuracy=accuracy,
    )


def compute_hold_correctness(events: List[RoutingPilotEvent]) -> HoldCorrectnessMetric:
    """Of the HOLD_EVIDENCE recommendations, what fraction were genuinely
    correct to hold (ground_truth_correct=True means the hold itself was
    the right call, e.g. evidence really was missing/ambiguous) versus a
    false hold that should have auto-continued."""
    holds = [e for e in events if e.gate_result == "HOLD_EVIDENCE"]
    correctly_held = [e for e in holds if e.ground_truth_correct is True]
    incorrectly_held = [e for e in holds if e.ground_truth_correct is False]
    unreviewed = [e for e in holds if e.ground_truth_correct is None]
    reviewed_total = len(correctly_held) + len(incorrectly_held)
    correctness = (len(correctly_held) / reviewed_total) if reviewed_total else None
    return HoldCorrectnessMetric(
        total_holds=len(holds),
        correctly_held=len(correctly_held),
        incorrectly_held=len(incorrectly_held),
        not_yet_reviewed=len(unreviewed),
        correctness=correctness,
    )


def compute_claim_replay_metric(events: List[ClaimReplayEvent]) -> ClaimReplayMetric:
    """replay_safe is the load-bearing field: it must be True (zero
    duplicate_processing_incidents) for any promotion evidence to count --
    a single incident here is a correctness defect, not a metric to average
    away."""
    granted = [e for e in events if e.claim_outcome == "GRANTED"]
    refused = [e for e in events if e.claim_outcome == "REFUSED"]
    replays = [e for e in events if e.was_replay]
    incidents = [e for e in events if e.duplicate_processing_detected]
    return ClaimReplayMetric(
        total_claim_attempts=len(events),
        granted=len(granted),
        refused=len(refused),
        replay_attempts=len(replays),
        duplicate_processing_incidents=len(incidents),
        replay_safe=(len(incidents) == 0),
    )


def compute_steward_intervention_rate(events: List[RoutingPilotEvent]) -> StewardInterventionMetric:
    """Fraction of all recorded events (any gate_result) where the Steward
    had to intervene -- a high rate is itself evidence against promotion,
    independent of whether the underlying recommendations were accurate."""
    interventions = [e for e in events if e.steward_intervened]
    rate = (len(interventions) / len(events)) if events else None
    return StewardInterventionMetric(
        total_events=len(events),
        steward_interventions=len(interventions),
        intervention_rate=rate,
    )
