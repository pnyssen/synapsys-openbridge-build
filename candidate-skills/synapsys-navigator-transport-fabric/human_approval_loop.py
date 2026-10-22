"""The D001/D007 human authority loop (load-bearing, per the Architecture Decision).

`Navigator request -> authenticated human approval surface -> RELEASE/HOLD
-> correlated identity-backed return -> Hub consume`.

This module never decides anything -- it only (a) determines whether an
open decision request already exists for a logical job, so a live wiring
layer never creates a second one, and (b) validates that a RELEASE/HOLD
return carries authenticated authority before it can be consumed. No
transport call, no Odoo/N8N mutation, no decision made.
"""

from dataclasses import dataclass
from typing import Optional

from transport_types import OutboxJob
from return_contract import ReturnContract, ConsumeVerifyOutcome, validate_return_contract

HUMAN_TARGET_LANE = "human"
STEWARD_ROLE = "steward"


@dataclass(frozen=True)
class PresentationDecision:
    action: str  # "SURFACE_EXISTING" | "CREATE_NEW"
    job: OutboxJob
    reason: str


def present_for_decision(candidate_job: OutboxJob, open_jobs: list) -> PresentationDecision:
    """Decide whether to surface an existing open D007 request or create a new one.

    A live approval surface calls this before ever writing a new dispatch.
    If any open job shares the candidate's logical_key() (same context_id,
    control_marker, state_revision) or the exact message_id, that existing
    job is surfaced instead -- never a second decision request for the same
    underlying decision.
    """
    for existing in open_jobs:
        if existing.status != "open" and existing.status != "proposed":
            continue
        if existing.message_id == candidate_job.message_id:
            return PresentationDecision(
                action="SURFACE_EXISTING",
                job=existing,
                reason=f"exact message_id {existing.message_id} already open -- present as-is",
            )
        if existing.logical_key() == candidate_job.logical_key():
            return PresentationDecision(
                action="SURFACE_EXISTING",
                job=existing,
                reason=(
                    f"logical job {existing.logical_key()} already open under "
                    f"message_id {existing.message_id} -- do not create a second request"
                ),
            )

    return PresentationDecision(
        action="CREATE_NEW", job=candidate_job, reason="no existing open request for this logical job"
    )


def resolve_d007_visibility(open_jobs: list, target_message_id: str) -> PresentationDecision:
    """How message `ae677703699303a3` (or any D007 job) becomes visible to D007
    without creating a second decision request.

    A live approval surface queries open_jobs filtered to
    target_lane == "human", role == "steward", and renders every match --
    it does not dispatch anything new. This function models exactly that
    read: find the existing job by message_id among what's already open,
    and confirm presentation is SURFACE_EXISTING, never CREATE_NEW, for a
    job that's already there.
    """
    steward_jobs = [j for j in open_jobs if j.target_lane == HUMAN_TARGET_LANE]
    match = next((j for j in steward_jobs if j.message_id == target_message_id), None)
    if match is None:
        raise LookupError(
            f"message_id {target_message_id!r} not found among open target_lane={HUMAN_TARGET_LANE!r} jobs -- "
            f"a live surface would show nothing to decide, not fabricate a job"
        )
    return present_for_decision(match, open_jobs)


def consume_decision_return(
    contract: ReturnContract,
    expected_message_id: str,
    expected_work_object_id: str,
    dispatch_bound_state_revision: str,
    controller_current_state_revision: str,
    already_consumed_message_ids: frozenset,
) -> ConsumeVerifyOutcome:
    """D007/D001 returns always require authenticated authority -- no exceptions.

    This is the same validate_return_contract() every other lane uses, but
    called with requires_authenticated_authority=True unconditionally, since
    this loop is load-bearing: an unauthenticated RELEASE/HOLD must never be
    accepted regardless of how plausible its content looks.
    """
    if contract.result_status not in ("RELEASE", "HOLD"):
        return ConsumeVerifyOutcome(
            accepted=False,
            reason=f"INVALID_D007_DECISION: result_status must be RELEASE or HOLD, got {contract.result_status!r}",
        )

    return validate_return_contract(
        contract=contract,
        expected_message_id=expected_message_id,
        expected_work_object_id=expected_work_object_id,
        dispatch_bound_state_revision=dispatch_bound_state_revision,
        controller_current_state_revision=controller_current_state_revision,
        requires_authenticated_authority=True,
        already_consumed_message_ids=already_consumed_message_ids,
    )
