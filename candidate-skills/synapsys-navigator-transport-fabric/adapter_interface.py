"""Runtime-adapter interface, keyed by target_lane.

A runtime adapter is any zero-argument-bound callable matching
`Callable[[RuntimeInvocationRequest], RuntimeInvocationResult]`. This
module defines the dispatch contract only -- it holds no live adapters
itself. The live wiring layer (out of scope for Phase 1 candidate code)
is responsible for registering real adapters (HTTP calls, Odoo calls,
N8N triggers, etc.) into a dict passed in at call time.
"""

from typing import Callable, Dict

from transport_types import RuntimeInvocationRequest, RuntimeInvocationResult

RuntimeAdapter = Callable[[RuntimeInvocationRequest], RuntimeInvocationResult]


def dispatch_to_adapter(
    target_lane: str, request: RuntimeInvocationRequest, adapters: Dict[str, RuntimeAdapter]
) -> RuntimeInvocationResult:
    """Hand the governed packet to the adapter registered for target_lane.

    If no adapter is registered, this is not an error -- it is an
    explicit WAITING_EXTERNAL_RUNTIME, matching the requirement to never
    silently stop.
    """
    adapter = adapters.get(target_lane)
    if adapter is None:
        return RuntimeInvocationResult(
            status="WAITING_EXTERNAL_RUNTIME",
            detail=f"no runtime adapter registered for target_lane={target_lane!r}",
        )
    return adapter(request)
