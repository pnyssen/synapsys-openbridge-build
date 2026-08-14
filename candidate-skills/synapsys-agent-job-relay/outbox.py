"""WM Outbox -- pure message-queue logic for the SynapSys Agent relay.
Component 5.1 of the filed design
(05_AI_RETURNS_HASHED/WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001/
20260814--claude-code--design-candidate--synapsys-agent-full-ecosystem-integration-design--v1-0.md).

The relay's job is transport only: write a JobContract-shaped message to a
Working Memory "outbox" location, let the addressed processor claim and
complete it. This module is the pure logic underneath that -- message
construction, claim-state transitions, and a WM-naming-compliant filename
generator. It never calls sp_read/sp_write/sp_list itself.

Zero I/O: no network, no filesystem, no subprocess, no wall-clock call.
Callers fetch listings and pass them in as plain data; callers perform the
actual sp_write of whatever this module returns. This mirrors
admin_task_dry_run.py's own pattern in this repo -- caller-supplied data
in, a plan/transition out, never a live call performed by the module
itself.
"""

import hashlib
import re
from dataclasses import asdict, dataclass, replace
from datetime import datetime
from typing import List, Optional

from job_contract import JobContract, from_dict, validate_job_contract

# Deliberately not imported from synapsys-wm-filing-compliance (a sibling
# candidate-skill in a different folder) to keep this module dependency-
# free and independently testable. Mirrors that module's own enforced
# pattern by hand -- keep the two in sync if the server's real rule ever
# changes; re-derive from a fresh sp_write rejection, don't patch from
# assumption.
_FILENAME_PATTERN = re.compile(
    r"^\d{8}--[a-z0-9]+(?:-[a-z0-9]+)*--[a-z0-9]+(?:-[a-z0-9]+)*--"
    r"[a-z0-9]+(?:-[a-z0-9]+)*--v\d+-\d+\.[a-z0-9]+$"
)


@dataclass(frozen=True)
class OutboxMessage:
    message_id: str
    job: JobContract
    enqueued_at_iso: str
    status: str
    claimed_by: Optional[str] = None
    claimed_at_iso: Optional[str] = None


def compute_message_id(job: JobContract, enqueued_at_iso: str) -> str:
    """Deterministic id: SHA-256 of the job's own replay_hash plus the
    enqueue timestamp, truncated to 16 hex chars for a manageable
    filename component. Deterministic (no random UUID) since this module
    has no random source available under the zero-wall-clock/zero-network
    discipline it's held to -- the same (job, enqueued_at_iso) pair always
    yields the same id."""
    basis = f"{job.replay_hash}:{enqueued_at_iso}"
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:16]


def build_message(job: JobContract, enqueued_at_iso: str) -> OutboxMessage:
    """Validates the job contract first -- an invalid job never becomes an
    outbox message. Raises ValueError carrying the validation errors
    rather than silently enqueueing something malformed."""
    result = validate_job_contract(job)
    if not result.ok:
        raise ValueError(f"Cannot enqueue an invalid JobContract: {result.errors}")
    return OutboxMessage(
        message_id=compute_message_id(job, enqueued_at_iso),
        job=job,
        enqueued_at_iso=enqueued_at_iso,
        status="proposed",
    )


def claim(message: OutboxMessage, claimed_by: str, claimed_at_iso: str) -> OutboxMessage:
    """Returns a new, claimed copy -- OutboxMessage is frozen, so this is a
    pure transition, not a mutation. Refuses to claim a message that isn't
    in 'proposed' state, so a message already claimed or closed can't be
    silently re-claimed. Which of two racing real-world claim() callers
    "wins" is decided by whichever write actually lands first in the real
    outbox -- outside this module's scope, since it performs no I/O."""
    if message.status != "proposed":
        raise ValueError(
            f"Cannot claim message {message.message_id}: status is "
            f"'{message.status}', not 'proposed' -- already claimed or closed."
        )
    return replace(message, status="active", claimed_by=claimed_by, claimed_at_iso=claimed_at_iso)


def complete(message: OutboxMessage, status: str = "closed") -> OutboxMessage:
    """Transitions a claimed ('active') message to a terminal state.
    status must be one of returned/closed/blocked -- 'proposed'/'active'
    are not valid completion states."""
    if status not in ("returned", "closed", "blocked"):
        raise ValueError(f"complete() status must be one of returned/closed/blocked, got '{status}'")
    if message.status != "active":
        raise ValueError(
            f"Cannot complete message {message.message_id}: status is "
            f"'{message.status}', not 'active' -- claim it first."
        )
    return replace(message, status=status)


def select_claimable(messages: List[OutboxMessage], processor: str) -> List[OutboxMessage]:
    """Pure filter: 'proposed' messages whose job.target_lane addresses
    the given processor (parameter kept as 'processor' for call-site
    continuity; matches job_contract.py's renamed target_lane field,
    reconciled per ChatGPT Hub's accepted integration basis). Does not
    sort by priority/urgency -- this module has no cadence/priority
    model; that belongs to the scheduler Routine (component 5.2 of the
    design), not this module."""
    return [m for m in messages if m.status == "proposed" and m.job.target_lane == processor]


def detect_stale_claims(
    messages: List[OutboxMessage],
    now_iso: str,
    max_claim_age_seconds: float,
) -> List[OutboxMessage]:
    """Flags 'active' (claimed but never completed) messages whose claim
    is older than max_claim_age_seconds -- a claimer that crashed or hung
    without calling complete(). Pure computation on caller-supplied
    now_iso; this module never calls a wall clock itself. An unparseable
    claimed_at_iso is treated as stale/suspect rather than silently
    skipped, matching freshness.py's own "surface, don't guess" rule for
    unparseable timestamps."""
    stale: List[OutboxMessage] = []
    for m in messages:
        if m.status != "active" or not m.claimed_at_iso:
            continue
        try:
            claimed = datetime.fromisoformat(m.claimed_at_iso)
            now = datetime.fromisoformat(now_iso)
        except (TypeError, ValueError):
            stale.append(m)
            continue
        age = (now - claimed).total_seconds()
        if age < 0 or age > max_claim_age_seconds:
            stale.append(m)
    return stale


def outbox_filename(message: OutboxMessage, date_yyyymmdd: str, lane: str) -> str:
    """Builds a WM-naming-compliant filename for filing this message
    (YYYYMMDD--lane--artifact-type--slug--vMAJOR-MINOR.ext), so an outbox
    write is never rejected by sp_write's naming enforcement. Does not
    call sp_write itself -- returns a name only."""
    slug = f"job-outbox-{message.message_id}"
    name = f"{date_yyyymmdd}--{lane}--job-outbox--{slug}--v1-0.json"
    assert _FILENAME_PATTERN.match(name), f"outbox_filename produced a non-compliant name: {name}"
    return name


def serialize_message(message: OutboxMessage) -> dict:
    return asdict(message)


def deserialize_message(data: dict) -> OutboxMessage:
    data = dict(data)
    job_data = data.pop("job")
    job = from_dict(job_data)
    return OutboxMessage(job=job, **data)


def try_deserialize_message(data: dict):
    """Same as deserialize_message(), but returns None instead of raising
    on a schema mismatch -- e.g. a message written under an earlier
    job_contract.py field shape (this schema was itself reconciled once
    already, per the accepted Navigator integration basis; old on-disk
    messages from before that reconciliation are exactly this case).
    Lets a polling loop skip a message it can't parse rather than crash
    on it -- 'skip and flag', not 'skip silently': callers should log
    which raw dict failed to parse, this function only decides not to
    raise."""
    try:
        return deserialize_message(data)
    except (ValueError, TypeError, KeyError):
        return None
