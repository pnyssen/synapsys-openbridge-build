"""Validate and consume a runtime adapter's return.

Two checks gate acceptance: identity (the returned message_id must match
what was sent) and status (only ATTEMPTED_RETURNED consumes). Consuming a
return records the JOB's own bound state_revision as consumed -- not the
controller's current state_revision at consumption time. A genuine return
for an older job remains valid even after the controller has advanced,
since those are two different revision counters tracking different things.
"""

from transport_types import ConsumedReturn, RuntimeInvocationResult


def consume_return(
    dispatch_task_state_revision: str,
    controller_state_revision: str,
    runtime_result: RuntimeInvocationResult,
    expected_message_id: str,
) -> ConsumedReturn:
    if runtime_result.status != "ATTEMPTED_RETURNED":
        return ConsumedReturn(
            accepted=False,
            reason=f"runtime status is {runtime_result.status!r}, not ATTEMPTED_RETURNED -- nothing to consume",
        )

    if runtime_result.returned_message_id != expected_message_id:
        return ConsumedReturn(
            accepted=False,
            reason=(
                f"identity mismatch: expected message_id {expected_message_id!r}, "
                f"runtime returned {runtime_result.returned_message_id!r} -- refusing to consume"
            ),
        )

    return ConsumedReturn(
        accepted=True,
        reason="identity and status validated, return consumed",
        consumed_state_revision=dispatch_task_state_revision,
        controller_state_revision_at_consumption=controller_state_revision,
    )
