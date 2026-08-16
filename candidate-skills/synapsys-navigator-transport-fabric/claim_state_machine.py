"""Idempotent claim/heartbeat/release/expire state transitions.

Pure functions only -- every transition takes "now" as an explicit
ISO-8601 string from the caller. True atomicity (compare-and-swap against
the actual storage layer) belongs to the live wiring layer; what this
module guarantees is that the *decision* of whether a claim attempt is
granted, already-held, or stale is deterministic and side-effect-free.
"""

from dataclasses import dataclass, replace
from typing import Optional

from transport_types import ClaimRecord

DEFAULT_STALE_AFTER_SECONDS = 120.0


@dataclass(frozen=True)
class ClaimAttempt:
    outcome: str  # "GRANTED" | "ALREADY_CLAIMED" | "RECLAIMED_EXPIRED"
    claim: ClaimRecord
    reason: str


def _seconds_between(earlier_iso: str, later_iso: str) -> float:
    from datetime import datetime

    earlier = datetime.fromisoformat(earlier_iso.replace("Z", "+00:00"))
    later = datetime.fromisoformat(later_iso.replace("Z", "+00:00"))
    return (later - earlier).total_seconds()


def is_stale(claim: ClaimRecord, now_iso: str, stale_after_seconds: float = DEFAULT_STALE_AFTER_SECONDS) -> bool:
    if claim.status in ("RELEASED", "EXPIRED"):
        return False
    return _seconds_between(claim.heartbeat_at_iso, now_iso) > stale_after_seconds


def attempt_claim(
    existing_claim: Optional[ClaimRecord],
    message_id: str,
    claimed_by: str,
    now_iso: str,
    stale_after_seconds: float = DEFAULT_STALE_AFTER_SECONDS,
) -> ClaimAttempt:
    """Idempotent claim attempt.

    - No existing claim, or existing claim RELEASED/EXPIRED -> GRANTED (new claim).
    - Existing live claim, same claimant, not stale -> GRANTED (idempotent re-claim,
      same outcome as the first successful claim -- calling this twice for the
      same worker is safe).
    - Existing live claim, different claimant, not stale -> ALREADY_CLAIMED.
    - Existing live claim, stale -> RECLAIMED_EXPIRED (previous holder's claim
      is treated as abandoned; this caller now holds it).
    """
    if existing_claim is None or existing_claim.status in ("RELEASED", "EXPIRED"):
        new_claim = ClaimRecord(
            message_id=message_id,
            claimed_by=claimed_by,
            claimed_at_iso=now_iso,
            heartbeat_at_iso=now_iso,
            status="CLAIMED",
        )
        return ClaimAttempt(outcome="GRANTED", claim=new_claim, reason="no live prior claim")

    if is_stale(existing_claim, now_iso, stale_after_seconds):
        reclaimed = ClaimRecord(
            message_id=message_id,
            claimed_by=claimed_by,
            claimed_at_iso=now_iso,
            heartbeat_at_iso=now_iso,
            status="CLAIMED",
        )
        return ClaimAttempt(
            outcome="RECLAIMED_EXPIRED",
            claim=reclaimed,
            reason=f"prior claim by {existing_claim.claimed_by} was stale, treated as abandoned",
        )

    if existing_claim.claimed_by == claimed_by:
        return ClaimAttempt(
            outcome="GRANTED",
            claim=existing_claim,
            reason="idempotent re-claim by the same worker, no-op",
        )

    return ClaimAttempt(
        outcome="ALREADY_CLAIMED",
        claim=existing_claim,
        reason=f"live claim already held by {existing_claim.claimed_by}",
    )


def heartbeat(claim: ClaimRecord, now_iso: str) -> ClaimRecord:
    if claim.status not in ("CLAIMED", "HEARTBEAT"):
        raise ValueError(f"cannot heartbeat a claim in status {claim.status!r}")
    return replace(claim, heartbeat_at_iso=now_iso, status="HEARTBEAT")


def release(claim: ClaimRecord) -> ClaimRecord:
    """Rollback/disable: explicitly return a claim to a re-claimable state."""
    return replace(claim, status="RELEASED")


def expire(claim: ClaimRecord) -> ClaimRecord:
    return replace(claim, status="EXPIRED")
