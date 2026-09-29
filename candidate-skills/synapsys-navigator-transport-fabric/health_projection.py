"""Navigator transport-health projection.

Pure read-only aggregation over registry + jobs + claims into the compact
per-domain view Navigator needs: status, last heartbeat, pending jobs,
claim latency, last return, and authority boundary. `authority_boundary`
is always a verbatim echo of the registry's own authority_class -- this
projection never upgrades or interprets it as anything more.
"""

from typing import Dict, List, Optional

from transport_types import ClaimRecord, HealthProjectionEntry, OutboxJob, RegistryEntry
from claim_state_machine import is_stale
from registry_resolver import ELIGIBLE_ACTIVATION_STATUSES


def _seconds_between(earlier_iso: str, later_iso: str) -> float:
    from datetime import datetime

    earlier = datetime.fromisoformat(earlier_iso.replace("Z", "+00:00"))
    later = datetime.fromisoformat(later_iso.replace("Z", "+00:00"))
    return (later - earlier).total_seconds()


def build_health_projection(
    registry: List[RegistryEntry],
    jobs: List[OutboxJob],
    claims: List[ClaimRecord],
    last_return_iso_by_target_lane: Dict[str, Optional[str]],
    now_iso: str,
) -> List[HealthProjectionEntry]:
    jobs_by_id = {job.message_id: job for job in jobs}
    entries = []

    for entry in registry:
        entry_claims = [c for c in claims if jobs_by_id.get(c.message_id, None) and jobs_by_id[c.message_id].target_lane == entry.target_lane]
        pending_jobs = sum(1 for job in jobs if job.target_lane == entry.target_lane and job.status == "open")

        if entry.activation_status not in ELIGIBLE_ACTIVATION_STATUSES:
            status = "HELD"
        elif not entry_claims:
            status = "OFFLINE"
        else:
            latest_claim = max(entry_claims, key=lambda c: c.heartbeat_at_iso)
            status = "DEGRADED" if is_stale(latest_claim, now_iso) else "ACTIVE"

        last_heartbeat = max((c.heartbeat_at_iso for c in entry_claims), default=None)

        claim_latency = None
        if entry_claims:
            latest_claim = max(entry_claims, key=lambda c: c.claimed_at_iso)
            matching_job = jobs_by_id.get(latest_claim.message_id)
            if matching_job is not None:
                claim_latency = _seconds_between(matching_job.enqueued_at_iso, latest_claim.claimed_at_iso)

        entries.append(
            HealthProjectionEntry(
                domain=entry.primary_domain,
                owner_lane=entry.owner_lane,
                status=status,
                last_heartbeat_iso=last_heartbeat,
                pending_jobs=pending_jobs,
                claim_latency_seconds=claim_latency,
                last_return_iso=last_return_iso_by_target_lane.get(entry.target_lane),
                authority_boundary=entry.authority_class,
            )
        )

    return entries
