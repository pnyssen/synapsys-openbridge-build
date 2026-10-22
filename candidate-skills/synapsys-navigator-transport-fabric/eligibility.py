"""Detect and validate eligible AGENT_OUTBOX jobs for transport claiming.

A job is eligible only when ALL of:
  - status == "open" and claimed_by is None (nothing already has it)
  - its target_lane resolves to a routable, authorised registry entry
  - it is not a replay/duplicate of something already in flight

This module composes registry_resolver and replay_validator; it does not
duplicate their logic.
"""

from dataclasses import dataclass
from typing import Optional

from transport_types import OutboxJob, RegistryEntry
from registry_resolver import resolve_endpoint
from replay_validator import ReplayLedger, validate_replay


@dataclass(frozen=True)
class EligibilityResult:
    eligible: bool
    job: OutboxJob
    reason: str


def check_eligibility(job: OutboxJob, registry: list, ledger: ReplayLedger) -> EligibilityResult:
    if job.status != "open":
        return EligibilityResult(eligible=False, job=job, reason=f"status is {job.status!r}, not open")

    if job.claimed_by is not None:
        return EligibilityResult(eligible=False, job=job, reason=f"already claimed_by {job.claimed_by}")

    replay = validate_replay(job, ledger)
    if replay.outcome != "NEW":
        return EligibilityResult(eligible=False, job=job, reason=replay.reason)

    resolution = resolve_endpoint(job.target_lane, registry)
    if not resolution.resolved:
        return EligibilityResult(eligible=False, job=job, reason=resolution.reason)

    return EligibilityResult(eligible=True, job=job, reason="RESOLVED and NEW")


def select_eligible_jobs(jobs: list, registry: list, ledger: ReplayLedger) -> list:
    results = [check_eligibility(job, registry, ledger) for job in jobs]
    return [r.job for r in results if r.eligible]
