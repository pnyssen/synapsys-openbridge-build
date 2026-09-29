"""JobContract + replay/idempotency validation.

Detects exact-message replays and logical-job duplicates (the same
underlying decision arriving under a different message_id -- e.g. a
resend still bound to the same state_revision). Never recomputes a
hashing scheme this package doesn't own; a HASH_MISMATCH is only raised
when the *same* message_id is seen twice with a *different* replay_hash,
which is tamper/corruption evidence, not a guess at the original algorithm.
"""

from dataclasses import dataclass
from typing import Optional

from transport_types import OutboxJob

REPLAY_OUTCOMES = frozenset({"NEW", "DUPLICATE_MESSAGE_ID", "DUPLICATE_LOGICAL_JOB", "HASH_MISMATCH"})


@dataclass(frozen=True)
class ReplayCheck:
    outcome: str
    reason: str


@dataclass(frozen=True)
class ReplayLedger:
    """Immutable snapshot of what the router has already seen.

    Callers accumulate seen_message_ids / seen_logical_keys / hashes_by_message_id
    across polls; this module only ever reads them, never mutates state itself.
    """

    seen_message_ids: frozenset
    seen_logical_keys: frozenset
    hashes_by_message_id: dict


def validate_replay(job: OutboxJob, ledger: ReplayLedger) -> ReplayCheck:
    if job.message_id in ledger.seen_message_ids:
        prior_hash = ledger.hashes_by_message_id.get(job.message_id)
        if prior_hash is not None and job.replay_hash is not None and prior_hash != job.replay_hash:
            return ReplayCheck(
                outcome="HASH_MISMATCH",
                reason=(
                    f"message_id {job.message_id} seen before with a different "
                    f"replay_hash -- possible tampering or corruption, not a clean replay"
                ),
            )
        return ReplayCheck(
            outcome="DUPLICATE_MESSAGE_ID",
            reason=f"message_id {job.message_id} already processed -- idempotent no-op",
        )

    if job.logical_key() in ledger.seen_logical_keys:
        return ReplayCheck(
            outcome="DUPLICATE_LOGICAL_JOB",
            reason=(
                f"logical job {job.logical_key()} already in flight under a "
                f"different message_id -- do not duplicate, this is the same "
                f"underlying decision"
            ),
        )

    return ReplayCheck(outcome="NEW", reason="not previously seen")
