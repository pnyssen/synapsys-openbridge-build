"""The normalized ReturnContract envelope and the live consume/verify rules.

Every producer lane's response -- N8N, GitHub, email, Odoo, an AI runtime,
or a human -- must normalize into this one shape before the return bridge
will consider consuming it. Nothing here calls a transport; this module
only validates a ReturnContract object the caller already constructed.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ReturnContract:
    message_id: str
    work_object_id: str
    control_marker: str
    producer_lane: str
    consumed_state_revision: str
    result_status: str  # e.g. RELEASE, HOLD, PASS, DEGRADED, DECLINED, ATTEMPTED_RETURNED
    authority_reference: Optional[str]
    result_file_path: Optional[str]
    result_bytes: Optional[int]
    result_sha256: Optional[str]
    evidence_state: str
    mutation_disclosure: str
    blocker_state: str
    next_action: str
    replay_validity: str
    is_transport_ack_only: bool = False
    authenticated: bool = False


@dataclass(frozen=True)
class ConsumeVerifyOutcome:
    accepted: bool
    reason: str


def validate_return_contract(
    contract: ReturnContract,
    expected_message_id: str,
    expected_work_object_id: str,
    dispatch_bound_state_revision: str,
    controller_current_state_revision: str,
    requires_authenticated_authority: bool,
    already_consumed_message_ids: frozenset,
) -> ConsumeVerifyOutcome:
    """The ten live return-bridge rules from the challenge (section C).

    Order matters -- each rule is checked independently so the reason
    reported is the specific one that actually failed, not a generic
    rejection.
    """
    # Rule: idempotent if the same return arrives by multiple transports.
    if contract.message_id in already_consumed_message_ids:
        return ConsumeVerifyOutcome(
            accepted=False,
            reason=f"IDEMPOTENT_NO_OP: message_id {contract.message_id} already consumed",
        )

    # Rule: reject wrong message_id.
    if contract.message_id != expected_message_id:
        return ConsumeVerifyOutcome(
            accepted=False,
            reason=f"WRONG_MESSAGE_ID: expected {expected_message_id!r}, got {contract.message_id!r}",
        )

    if contract.work_object_id != expected_work_object_id:
        return ConsumeVerifyOutcome(
            accepted=False,
            reason=(
                f"WRONG_WORK_OBJECT_ID: expected {expected_work_object_id!r}, "
                f"got {contract.work_object_id!r}"
            ),
        )

    # Rule: reject a transport ACK as a substantive return.
    if contract.is_transport_ack_only:
        return ConsumeVerifyOutcome(
            accepted=False,
            reason="TRANSPORT_ACK_ONLY: delivery confirmation is not a substantive return",
        )

    # Rule: reject wrong bound state revision, UNLESS it's the dispatch's own
    # older bound revision -- a genuine return for an older job stays valid
    # even after the controller has advanced past it.
    if contract.consumed_state_revision != dispatch_bound_state_revision:
        return ConsumeVerifyOutcome(
            accepted=False,
            reason=(
                f"WRONG_STATE_REVISION: return cites {contract.consumed_state_revision!r}, "
                f"dispatch was bound to {dispatch_bound_state_revision!r}"
            ),
        )
    # (The controller's current revision may be higher -- that is expected
    # and does not itself invalidate an older-bound genuine return.)
    _ = controller_current_state_revision  # recorded for the caller's audit trail, not a gate

    # Rule: reject unauthenticated authority claims.
    if requires_authenticated_authority and not contract.authenticated:
        return ConsumeVerifyOutcome(
            accepted=False,
            reason="UNAUTHENTICATED_AUTHORITY: this destination requires an authenticated decision surface",
        )

    if requires_authenticated_authority and not contract.authority_reference:
        return ConsumeVerifyOutcome(
            accepted=False,
            reason="MISSING_AUTHORITY_REFERENCE: authenticated authority requires a stated reference",
        )

    # Rule: reject wrong return class/shape -- minimum required fields present.
    required_nonempty = (
        contract.evidence_state,
        contract.mutation_disclosure,
        contract.blocker_state,
        contract.next_action,
        contract.replay_validity,
    )
    if not all(required_nonempty):
        return ConsumeVerifyOutcome(
            accepted=False,
            reason="INCOMPLETE_SHAPE: one or more required ReturnContract fields is empty",
        )

    return ConsumeVerifyOutcome(accepted=True, reason="VALIDATED")
