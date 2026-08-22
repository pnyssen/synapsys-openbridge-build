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

from typing import Callable, Optional

from transport_types import RuntimeInvocationRequest, RuntimeInvocationResult

D009_TARGET_LANE = "gemini_d009"

# The seam a live wiring layer plugs into: a callable taking the built
# packet dict and returning a raw response dict, or None/raising on
# failure. This module never constructs or calls a real one -- passing
# None (the default) preserves today's WAITING_EXTERNAL_RUNTIME behaviour
# exactly.
D009RuntimeCaller = Callable[[dict], Optional[dict]]


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
    request: RuntimeInvocationRequest,
    ai_auditor_sources_fully_processed: bool,
    runtime_caller: Optional[D009RuntimeCaller] = None,
) -> RuntimeInvocationResult:
    """The D009 adapter's `invoke`, matching the RuntimeAdapter contract.

    Source-readiness is always checked first, regardless of whether a
    runtime_caller is supplied -- a caller must never be able to bypass the
    source gate by passing one in. When the probe says ATTEMPT and no
    runtime_caller is supplied (Phase 1 default), this returns
    WAITING_EXTERNAL_RUNTIME rather than fabricating a result. When a
    runtime_caller IS supplied and ATTEMPT-eligible, it is invoked and its
    result normalized -- this is the pluggable seam a live wiring layer
    uses; this module still makes no network call itself.
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

    if runtime_caller is None:
        return RuntimeInvocationResult(
            status="WAITING_EXTERNAL_RUNTIME",
            detail=(
                "capability probe is ATTEMPT-eligible (sources_fully_processed=True) "
                "but no live D009 runtime call is wired in Phase 1 candidate code -- "
                "this is the deployment delta, not a failure"
            ),
        )

    packet = build_d009_packet(request)
    try:
        raw_response = runtime_caller(packet)
    except Exception as exc:  # the caller's transport failed, not a source-readiness issue
        return RuntimeInvocationResult(
            status="TIMEOUT",
            detail=f"runtime_caller raised: {exc!r}",
        )

    if not raw_response:
        return RuntimeInvocationResult(
            status="TIMEOUT",
            detail="runtime_caller returned no response",
        )

    return RuntimeInvocationResult(
        status="ATTEMPTED_RETURNED",
        detail="D009 runtime call completed, normalized into RuntimeInvocationResult",
        returned_message_id=request.message_id,
        returned_payload=raw_response,
    )
