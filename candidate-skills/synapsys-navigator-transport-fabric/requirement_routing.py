"""Wave 4 prep: the requirement-detection chain named in the recursive FFE
programme's Wave 4 Form section but not yet built anywhere in this package:

    requirement signal -> Context resolution -> eligible Service ->
    selected Method -> Work Object binding recommendation.

Everything downstream of this chain (registry_resolver, eligibility,
claim_state_machine, adapter_interface, return_contract) already assumes a
job/Work Object exists. This module is the missing upstream half: given a
detected requirement signal and caller-supplied live-state snapshots (known
Context ids, Service activation rows, Method candidate rows -- this module
performs no I/O and reads none of Odoo itself), it recommends which
Context/Service/Method a Work Object should bind to, or holds with an exact
reason.

Classified A1_RECOMMEND in wave4_autonomy_mapping.py: this chain only ever
recommends or holds. It never creates a Work Object, never selects between
ambiguous candidates by guessing, and by design never returns
HUMAN_DECISION, HOLD_AUTHORITY or EXCEPTION -- it doesn't touch authority
or exception state at all, only Context/Service/Method resolution. Any
ambiguity or missing evidence resolves to HOLD_EVIDENCE, never an
inference. `eligible != selected != executing` is preserved: this module
never claims a job, dispatches to an adapter, or performs the binding it
recommends.
"""

from dataclasses import dataclass
from typing import List, Optional

from wave4_autonomy_mapping import GATE_RESULT_VOCABULARY

# The only two gate results this chain can ever produce -- see module
# docstring for why HUMAN_DECISION/HOLD_AUTHORITY/EXCEPTION are out of
# scope for a pure recommendation chain that touches no authority state.
ROUTING_GATE_RESULTS = frozenset({"AUTO_CONTINUE_WITHIN_DELEGATION", "HOLD_EVIDENCE"})
assert ROUTING_GATE_RESULTS <= GATE_RESULT_VOCABULARY


@dataclass(frozen=True)
class RequirementSignal:
    """A detected requirement/trigger, before Context resolution.

    candidate_context_id is what the signal itself claims (e.g. a source
    system tag) -- it is not trusted until resolve_context confirms it
    against the caller-supplied set of known live Context ids.
    """

    signal_id: str
    description: str
    candidate_context_id: Optional[str]
    detected_at_iso: str
    source: str


@dataclass(frozen=True)
class ServiceActivationRow:
    """One caller-supplied x_ss_context_service_activation-shaped row."""

    context_id: str
    service_code: str
    activation_status: str


@dataclass(frozen=True)
class MethodCandidateRow:
    """One caller-supplied Method eligible for a given service_code."""

    service_code: str
    method_id: str


@dataclass(frozen=True)
class ContextResolution:
    resolved: bool
    context_id: Optional[str]
    reason: str


def resolve_context(signal: RequirementSignal, known_context_ids: frozenset) -> ContextResolution:
    """Confirm the signal's claimed Context against live known Context ids.

    Never invents a Context id not present in `known_context_ids`, and
    never resolves an unset candidate_context_id by guessing."""
    if not signal.candidate_context_id:
        return ContextResolution(
            resolved=False, context_id=None,
            reason="NO_CANDIDATE_CONTEXT: signal carries no context_id to resolve",
        )
    if signal.candidate_context_id not in known_context_ids:
        return ContextResolution(
            resolved=False, context_id=None,
            reason=f"UNKNOWN_CONTEXT: {signal.candidate_context_id!r} not in known live Contexts",
        )
    return ContextResolution(resolved=True, context_id=signal.candidate_context_id, reason="RESOLVED")


@dataclass(frozen=True)
class ServiceEligibility:
    service_code: str
    eligible: bool
    reason: str


def eligible_services_for_context(
    context_id: str, activations: List[ServiceActivationRow]
) -> List[ServiceEligibility]:
    """Which Services are activated for this Context -- an eligibility
    whitelist only, never itself the MECE selection decision (matches the
    live-verified distinction: 'eligible != selected')."""
    results = []
    for row in activations:
        if row.context_id != context_id:
            continue
        eligible = row.activation_status == "active"
        reason = "active" if eligible else f"activation_status={row.activation_status!r}"
        results.append(ServiceEligibility(service_code=row.service_code, eligible=eligible, reason=reason))
    return results


@dataclass(frozen=True)
class MethodSelection:
    method_id: Optional[str]
    rationale: str


def select_minimum_method(service_code: str, method_candidates: List[MethodCandidateRow]) -> MethodSelection:
    """Pick the single Method candidate for this service. Requires the
    caller's candidate set to already be MECE for this service -- this
    function does not itself disambiguate; more than one match is a
    reported gap, not a guess."""
    matches = [m for m in method_candidates if m.service_code == service_code]
    if not matches:
        return MethodSelection(
            method_id=None, rationale=f"NO_METHOD: no Method candidate registered for service {service_code!r}"
        )
    if len(matches) > 1:
        return MethodSelection(
            method_id=None,
            rationale=(
                f"AMBIGUOUS_METHOD: {len(matches)} candidates for service {service_code!r}; "
                "MECE selection requires exactly one and this candidate has no tie-break rule"
            ),
        )
    return MethodSelection(method_id=matches[0].method_id, rationale="UNIQUE_MATCH")


@dataclass(frozen=True)
class WorkObjectBindingRecommendation:
    """The chain's final output: a recommendation only. Creating or
    binding an actual Work Object is a separate, higher-autonomy-level
    action this module never performs."""

    signal_id: str
    gate_result: str
    context_id: Optional[str]
    service_code: Optional[str]
    method_id: Optional[str]
    reason: str

    def __post_init__(self) -> None:
        if self.gate_result not in ROUTING_GATE_RESULTS:
            raise ValueError(
                f"requirement_routing may only produce {sorted(ROUTING_GATE_RESULTS)}, got {self.gate_result!r}"
            )


def recommend_work_object_binding(
    signal: RequirementSignal,
    known_context_ids: frozenset,
    activations: List[ServiceActivationRow],
    method_candidates: List[MethodCandidateRow],
) -> WorkObjectBindingRecommendation:
    """The full chain: requirement -> Context -> eligible Service ->
    selected Method -> binding recommendation. Stops at the first
    unsupported state with an exact reason, per the programme's own
    'unavailable state returns GAP/HOLD, never inference' rule."""
    ctx = resolve_context(signal, known_context_ids)
    if not ctx.resolved:
        return WorkObjectBindingRecommendation(
            signal.signal_id, "HOLD_EVIDENCE", None, None, None, ctx.reason
        )

    services = eligible_services_for_context(ctx.context_id, activations)
    eligible = [s for s in services if s.eligible]

    if not eligible:
        return WorkObjectBindingRecommendation(
            signal.signal_id, "HOLD_EVIDENCE", ctx.context_id, None, None,
            "NO_ELIGIBLE_SERVICE: no active Service activation for this Context",
        )
    if len(eligible) > 1:
        return WorkObjectBindingRecommendation(
            signal.signal_id, "HOLD_EVIDENCE", ctx.context_id, None, None,
            (
                f"AMBIGUOUS_SERVICE_SELECTION: {len(eligible)} eligible Services and no MECE "
                "tie-break rule implemented in this candidate yet"
            ),
        )

    service = eligible[0]
    method = select_minimum_method(service.service_code, method_candidates)
    if method.method_id is None:
        return WorkObjectBindingRecommendation(
            signal.signal_id, "HOLD_EVIDENCE", ctx.context_id, service.service_code, None, method.rationale
        )

    return WorkObjectBindingRecommendation(
        signal.signal_id,
        "AUTO_CONTINUE_WITHIN_DELEGATION",
        ctx.context_id,
        service.service_code,
        method.method_id,
        "Context resolved, exactly one eligible Service, exactly one Method candidate -- "
        "recommendation only, no Work Object created or bound by this call",
    )
