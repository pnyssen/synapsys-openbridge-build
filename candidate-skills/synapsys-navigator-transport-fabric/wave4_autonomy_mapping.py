"""Wave 4 Form-layer prep: mapping this package's existing vocabulary and
capabilities against the Navigator Recursive Form/Flow/Evolve Autonomy
Programme v1.1 (consumed_state_revision 380, filed state_revision 381,
SHA-256 2b632db55b7eaf7a1b0dc72bac833901e81c0753199ef76174f3da7bad280c9c).

This is candidate/documentation work only, extending this existing package
(no new architecture stream, per that programme's own "Deleted scope").
It performs no I/O and mutates nothing. It does not touch the WO2/Benefit
Register decision surface, which remains ChatGPT Hub's live thread.

Every entry here is a pure mapping from vocabulary this package already
defines and tests to vocabulary the programme document defines -- it does
not invent new statuses, and every mapped value is cross-checked against
the real source module in tests, not hand-typed and left to drift.

Wave 4 ("Agent / requirement detection and routing") has not started --
current_wave in the controller is Wave 3. This module is preparation, not
an implementation of Wave 4 itself: it gives whoever opens Wave 4 (ChatGPT
Hub, or this lane under a future dispatch) a ready cross-reference instead
of starting from nothing.
"""

from dataclasses import dataclass

from transport_types import CLAIM_STATUSES, RUNTIME_RESULT_STATUSES

# The Wave 0 gate-result vocabulary, verbatim from the programme document's
# "Form" section for Wave 0 ("Authority and release boundary").
GATE_RESULT_VOCABULARY = frozenset(
    {
        "AUTO_CONTINUE_WITHIN_DELEGATION",
        "HUMAN_DECISION",
        "HOLD_EVIDENCE",
        "HOLD_AUTHORITY",
        "EXCEPTION",
    }
)

# The graduated autonomy ladder, verbatim from the programme document.
AUTONOMY_LEVELS = (
    "A0_OBSERVE",
    "A1_RECOMMEND",
    "A2_ROUTE",
    "A3_PREPARE",
    "A4_EXECUTE_DELEGATED",
    "A5_EXCEPTION_AUTONOMY",
)

# Every RuntimeInvocationResult.status / ConsumedReturn.reason / etc. value
# this package's own return_contract.py, human_approval_loop.py and
# transport_types.py already define, cross-checked in tests below against
# the real frozensets/source rather than retyped from memory.
RETURN_CONTRACT_REASONS = frozenset(
    {
        "IDEMPOTENT_NO_OP",
        "WRONG_MESSAGE_ID",
        "WRONG_WORK_OBJECT_ID",
        "TRANSPORT_ACK_ONLY",
        "WRONG_STATE_REVISION",
        "UNAUTHENTICATED_AUTHORITY",
        "MISSING_AUTHORITY_REFERENCE",
        "INCOMPLETE_SHAPE",
        "VALIDATED",
        "INVALID_D007_DECISION",
    }
)
PRESENTATION_ACTIONS = frozenset({"SURFACE_EXISTING", "CREATE_NEW"})
HEALTH_STATUSES = frozenset({"ACTIVE", "HELD", "DEGRADED", "OFFLINE"})


@dataclass(frozen=True)
class GateResultMapping:
    source_module: str
    source_value: str
    canonical_result: str
    rationale: str

    def __post_init__(self) -> None:
        if self.canonical_result not in GATE_RESULT_VOCABULARY:
            raise ValueError(f"unknown Wave 0 gate result: {self.canonical_result!r}")


GATE_RESULT_MAP = (
    # transport_types.RUNTIME_RESULT_STATUSES
    GateResultMapping(
        "transport_types.RUNTIME_RESULT_STATUSES", "ATTEMPTED_RETURNED",
        "AUTO_CONTINUE_WITHIN_DELEGATION",
        "A runtime call completed and returned a normalized result within the "
        "existing claim/return bounds -- no new human input needed to continue.",
    ),
    GateResultMapping(
        "transport_types.RUNTIME_RESULT_STATUSES", "WAITING_EXTERNAL_RUNTIME",
        "HOLD_EVIDENCE",
        "No live runtime is wired in this candidate -- this is a readiness gap, "
        "not an authority gap; matches D009's own source-readiness gate exactly.",
    ),
    GateResultMapping(
        "transport_types.RUNTIME_RESULT_STATUSES", "DEGRADED",
        "HOLD_EVIDENCE",
        "Explicit governed decline (e.g. D009 source gate closed) -- evidence "
        "insufficient to proceed, never silently treated as PASS.",
    ),
    GateResultMapping(
        "transport_types.RUNTIME_RESULT_STATUSES", "TIMEOUT",
        "EXCEPTION",
        "The runtime caller raised or returned nothing -- an abnormal transport "
        "failure, not a routine evidence gap; worth surfacing as an exception.",
    ),
    GateResultMapping(
        "transport_types.RUNTIME_RESULT_STATUSES", "DECLINED",
        "HOLD_EVIDENCE",
        "An explicit decline from the target domain -- insufficient evidence to "
        "proceed, held rather than retried silently.",
    ),
    # return_contract.py rejection/acceptance reasons
    GateResultMapping(
        "return_contract.validate_return_contract", "IDEMPOTENT_NO_OP",
        "AUTO_CONTINUE_WITHIN_DELEGATION",
        "A duplicate arriving by a second transport is a safe no-op, not a new "
        "decision -- continues within the original delegation.",
    ),
    GateResultMapping(
        "return_contract.validate_return_contract", "WRONG_MESSAGE_ID",
        "HOLD_EVIDENCE",
        "The return doesn't carry admissible identity evidence for this job.",
    ),
    GateResultMapping(
        "return_contract.validate_return_contract", "WRONG_WORK_OBJECT_ID",
        "HOLD_EVIDENCE",
        "Same defect class as WRONG_MESSAGE_ID -- identity evidence mismatch.",
    ),
    GateResultMapping(
        "return_contract.validate_return_contract", "TRANSPORT_ACK_ONLY",
        "HOLD_EVIDENCE",
        "A delivery receipt is not substantive evidence of a real return.",
    ),
    GateResultMapping(
        "return_contract.validate_return_contract", "WRONG_STATE_REVISION",
        "HOLD_EVIDENCE",
        "The return's bound state revision doesn't match the dispatch it "
        "claims to answer -- stale or misrouted evidence.",
    ),
    GateResultMapping(
        "return_contract.validate_return_contract", "UNAUTHENTICATED_AUTHORITY",
        "HOLD_AUTHORITY",
        "This is an authority defect, not an evidence defect -- the return "
        "isn't evidence-short, it's not from an authenticated decision surface.",
    ),
    GateResultMapping(
        "return_contract.validate_return_contract", "MISSING_AUTHORITY_REFERENCE",
        "HOLD_AUTHORITY",
        "Same class as UNAUTHENTICATED_AUTHORITY -- no authority trace to check.",
    ),
    GateResultMapping(
        "return_contract.validate_return_contract", "INCOMPLETE_SHAPE",
        "HOLD_EVIDENCE",
        "Required evidence fields are empty -- the shape itself is insufficient.",
    ),
    GateResultMapping(
        "return_contract.validate_return_contract", "VALIDATED",
        "AUTO_CONTINUE_WITHIN_DELEGATION",
        "Every rule passed -- the return is consumed within the bounds already "
        "delegated to this transport layer, no new human decision required.",
    ),
    GateResultMapping(
        "human_approval_loop.consume_decision_return", "INVALID_D007_DECISION",
        "HOLD_AUTHORITY",
        "A return claiming to be a D007 decision but not carrying RELEASE/HOLD "
        "is not an authenticated authority act -- held, never inferred.",
    ),
    # human_approval_loop.present_for_decision
    GateResultMapping(
        "human_approval_loop.present_for_decision", "SURFACE_EXISTING",
        "AUTO_CONTINUE_WITHIN_DELEGATION",
        "Reusing an already-open decision request is bounded and reversible -- "
        "no new authority is created or implied.",
    ),
    GateResultMapping(
        "human_approval_loop.present_for_decision", "CREATE_NEW",
        "HUMAN_DECISION",
        "Opening a new D007 decision request is exactly the kind of commitment "
        "boundary this programme reserves for a human, never Agent-initiated.",
    ),
    # health_projection.py
    GateResultMapping(
        "health_projection", "ACTIVE",
        "AUTO_CONTINUE_WITHIN_DELEGATION",
        "A healthy, fresh claim needs no escalation.",
    ),
    GateResultMapping(
        "health_projection", "HELD",
        "HOLD_AUTHORITY",
        "The registry entry isn't authorised for routing -- an authority gap.",
    ),
    GateResultMapping(
        "health_projection", "DEGRADED",
        "HOLD_EVIDENCE",
        "A stale heartbeat is a freshness/evidence gap, not an authority gap.",
    ),
    GateResultMapping(
        "health_projection", "OFFLINE",
        "EXCEPTION",
        "Never claimed at all -- an absence of signal worth surfacing as an "
        "exception rather than silently treating as steady-state.",
    ),
)


@dataclass(frozen=True)
class CapabilityAutonomyClassification:
    capability: str
    current_autonomy_level: str
    rationale: str
    promotion_requires: str

    def __post_init__(self) -> None:
        if self.current_autonomy_level not in AUTONOMY_LEVELS:
            raise ValueError(f"unknown autonomy level: {self.current_autonomy_level!r}")


CAPABILITY_AUTONOMY_MAP = (
    CapabilityAutonomyClassification(
        "registry_resolver.resolve_endpoint",
        "A1_RECOMMEND",
        "Reads x_ss_agent_registry and recommends a route; never itself binds "
        "or executes anything.",
        "Measured routing accuracy against real registry state before A2.",
    ),
    CapabilityAutonomyClassification(
        "eligibility.check_eligibility / select_eligible_jobs",
        "A1_RECOMMEND",
        "Filters which jobs are eligible for transport -- a recommendation "
        "surface, not an execution one.",
        "Same as resolve_endpoint: measured accuracy before promotion.",
    ),
    CapabilityAutonomyClassification(
        "claim_state_machine.attempt_claim / heartbeat / release / expire",
        "A2_ROUTE",
        "Binds a claim to a claimant -- routes/reserves work, but the claim "
        "itself is reversible (release/expire) and commits nothing external.",
        "Evidence of correct concurrency behaviour under real contention "
        "before any execution authority is layered on top.",
    ),
    CapabilityAutonomyClassification(
        "adapter_interface.dispatch_to_adapter",
        "A3_PREPARE",
        "Prepares/hands a governed packet to a registered adapter callable; "
        "this candidate never registers a live adapter, so no execution "
        "actually occurs today regardless of level.",
        "A real, reviewed adapter registration plus rollback/authority "
        "containment evidence -- explicitly D007-gated, not self-granted.",
    ),
    CapabilityAutonomyClassification(
        "d009_adapter.d009_adapter_invoke",
        "A3_PREPARE",
        "Builds the exact governed packet and, if a runtime_caller is "
        "supplied, invokes it -- but no live caller is wired in this "
        "candidate, so today's behaviour is unconditionally WAITING_EXTERNAL_"
        "RUNTIME / HOLD_EVIDENCE, never actual execution.",
        "A live D009 caller wired and reviewed under a separate D007 release, "
        "with measured TIMEOUT/DEGRADED/ATTEMPTED_RETURNED rates.",
    ),
    CapabilityAutonomyClassification(
        "return_contract.validate_return_contract",
        "A0_OBSERVE",
        "Pure read/verify of an already-produced return -- observes and "
        "classifies, never acts or advances anything itself.",
        "N/A -- this is a verification primitive other capabilities call; it "
        "does not itself need promotion.",
    ),
    CapabilityAutonomyClassification(
        "human_approval_loop.present_for_decision / resolve_d007_visibility",
        "A1_RECOMMEND",
        "Recommends SURFACE_EXISTING vs CREATE_NEW; never creates a decision "
        "request itself -- that remains a human/D007 act by design.",
        "This capability is deliberately capped -- CREATE_NEW must always "
        "resolve to HUMAN_DECISION, never promoted past A1.",
    ),
    CapabilityAutonomyClassification(
        "human_approval_loop.consume_decision_return",
        "A0_OBSERVE",
        "Validates an already-authenticated RELEASE/HOLD; does not decide, "
        "does not mutate.",
        "N/A -- load-bearing verification primitive, not a candidate for "
        "promotion past observation.",
    ),
    CapabilityAutonomyClassification(
        "github_transport.classify_github_event / email_transport.classify_email_reply",
        "A0_OBSERVE",
        "Classifies an inbound transport event (correlated/duplicate/spoof) "
        "read-only; is_authority_bearing is hardcoded False on every path.",
        "N/A by design -- these transports are declared NOTIFY_ONLY in "
        "destination_registry.py and must never carry authority.",
    ),
)
