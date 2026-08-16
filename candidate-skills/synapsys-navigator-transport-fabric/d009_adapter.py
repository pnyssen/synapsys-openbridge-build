"""D009 (Gemini assurance) adapter -- packet builder and capability probe.

The router does not assure; it delivers the exact governed packet to the
actual callable D009 runtime and relays the response. This module builds
that packet and decides, from an explicitly supplied readiness signal,
whether an attempt should even be made.

`ai_auditor_sources_fully_processed` is passed in by the caller (the
live wiring layer would read Odoo `ai.agent` id 7 "AI Auditor",
`sources_fully_processed`, and pass the boolean here) -- this module
performs no I/O of its own. If the gate is closed, the result is an
explicit governed decline, never a silent PASS.
"""

from transport_types import RuntimeInvocationRequest, RuntimeInvocationResult

D009_TARGET_LANE = "gemini_d009"


def build_d009_packet(request: RuntimeInvocationRequest) -> dict:
    """The exact governed assurance packet, built only from fields already on the request."""
    return {
        "message_id": request.message_id,
        "context_id": request.context_id,
        "control_marker": request.control_marker,
        "state_revision": request.state_revision,
        "objective": request.objective,
        "source_refs": request.source_refs,
        "assurance_domain": "D009",
    }


def probe_d009_capability(ai_auditor_sources_fully_processed: bool) -> str:
    """Pure decision: ATTEMPT or DECLINE_SOURCES_NOT_READY."""
    return "ATTEMPT" if ai_auditor_sources_fully_processed else "DECLINE_SOURCES_NOT_READY"


def d009_adapter_invoke(
    request: RuntimeInvocationRequest, ai_auditor_sources_fully_processed: bool
) -> RuntimeInvocationResult:
    """The D009 adapter's `invoke`, matching the RuntimeAdapter contract.

    Phase 1 scope: the actual live call to the D009 runtime is the
    deployment delta explicitly deferred out of this candidate build (see
    package README). When the capability probe says ATTEMPT, this returns
    WAITING_EXTERNAL_RUNTIME rather than fabricating a result -- there is
    no live runtime wired in yet. When the probe says the source gate is
    not ready, this returns a governed DEGRADED decline, never RETURNED.
    """
    decision = probe_d009_capability(ai_auditor_sources_fully_processed)

    if decision == "DECLINE_SOURCES_NOT_READY":
        return RuntimeInvocationResult(
            status="DEGRADED",
            detail=(
                "D009 source gate not ready: ai.agent[7] AI Auditor "
                "sources_fully_processed=False -- governed partial-context "
                "decline, not treated as PASS"
            ),
        )

    return RuntimeInvocationResult(
        status="WAITING_EXTERNAL_RUNTIME",
        detail=(
            "capability probe is ATTEMPT-eligible (sources_fully_processed=True) "
            "but no live D009 runtime call is wired in Phase 1 candidate code -- "
            "this is the deployment delta, not a failure"
        ),
    )
