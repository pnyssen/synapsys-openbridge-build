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

v0.3 -- Active Outcome Supervisor JSON_FILE_LIMITED preparation (D007
decision `20260818--d007--decision--active-outcome-supervisor-claim-substrate--v1-0.md`,
status JSON_FILE_LIMITED, processor_source_commit_preparation=YES). Adds
lease/heartbeat/attempt_count/processor_id/last_transition_at,
return-matching receipt fields (state_consumed_revision, return_filed_path,
return_readback_sha256, controller_match_result), and control-version
identity fields (control_branch, control_commit, control_skill_version)
plus CONTROL_VERSION_DRIFT classification -- all purely additive to the v0.2
OutboxMessage shape, with the original 2-arg claim()/complete() call shapes
still valid via optional keyword arguments. try_deserialize_message(), first
introduced only in an uncommitted scratchpad copy earlier this session, is
included here as this candidate's committed source.

IMPORTANT -- this file is a *candidate*, prepared but not committed, per
the JSON_FILE_LIMITED D007 decision: claim-then-verify (see
verify_claim_ownership() below) is an explicitly NON-ATOMIC concurrency
mitigation. It narrows but does not close the TOCTOU race between a
caller's claim-write and its own readback-verify. Do not describe it as
compare-and-set or atomic anywhere this module is used or cited. Any
multi-processor or production use requires a separate atomic-substrate
D007 release (e.g. moving claim arbitration to Odoo using the already-
proven atomic_claim_sql_pattern() in
candidate-skills/synapsys-navigator-transport-fabric/dispatch_task_mapping.py)
-- JSON_FILE_LIMITED does not satisfy that gate.
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

COMPLETION_STATUSES = ("returned", "closed", "blocked")
CONTROL_VERSION_DRIFT = "CONTROL_VERSION_DRIFT"


@dataclass(frozen=True)
class OutboxMessage:
    message_id: str
    job: JobContract
    enqueued_at_iso: str
    status: str
    claimed_by: Optional[str] = None
    claimed_at_iso: Optional[str] = None

    # -- Active Outcome Supervisor additive fields (JSON_FILE_LIMITED prep,
    #    all optional/defaulted so every v0.2 message and call site remains
    #    valid unchanged) --
    lease_expires_at: Optional[str] = None
    heartbeat_at: Optional[str] = None
    attempt_count: int = 0
    processor_id: Optional[str] = None
    last_transition_at: Optional[str] = None
    state_consumed_revision: Optional[str] = None
    return_filed_path: Optional[str] = None
    return_readback_sha256: Optional[str] = None
    controller_match_result: Optional[str] = None
    control_branch: Optional[str] = None
    control_commit: Optional[str] = None
    control_skill_version: Optional[str] = None


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


def claim(
    message: OutboxMessage,
    claimed_by: str,
    claimed_at_iso: str,
    processor_id: Optional[str] = None,
    lease_expires_at: Optional[str] = None,
    control_branch: Optional[str] = None,
    control_commit: Optional[str] = None,
    control_skill_version: Optional[str] = None,
) -> OutboxMessage:
    """Returns a new, claimed copy -- OutboxMessage is frozen, so this is a
    pure transition, not a mutation. Refuses to claim a message that isn't
    in 'proposed' state, so a message already claimed or closed can't be
    silently re-claimed. Which of two racing real-world claim() callers
    "wins" is decided by whichever write actually lands first in the real
    outbox -- outside this module's scope, since it performs no I/O.

    The original 2-required-arg call shape (message, claimed_by,
    claimed_at_iso) is unchanged and still valid -- every new parameter is
    optional. lease_expires_at is an exact ISO-8601 timestamp supplied by
    the caller; this module never computes "now + N seconds" itself, since
    it has no wall clock."""
    if message.status != "proposed":
        raise ValueError(
            f"Cannot claim message {message.message_id}: status is "
            f"'{message.status}', not 'proposed' -- already claimed or closed."
        )
    return replace(
        message,
        status="active",
        claimed_by=claimed_by,
        claimed_at_iso=claimed_at_iso,
        processor_id=processor_id,
        lease_expires_at=lease_expires_at,
        attempt_count=message.attempt_count + 1,
        last_transition_at=claimed_at_iso,
        control_branch=control_branch,
        control_commit=control_commit,
        control_skill_version=control_skill_version,
    )


def heartbeat(
    message: OutboxMessage,
    heartbeat_at_iso: str,
    new_lease_expires_at: Optional[str] = None,
) -> OutboxMessage:
    """Extends a live claim's evidence. Refuses on a message that isn't
    'active' -- a claim that was never taken or already completed cannot
    be heartbeated. If new_lease_expires_at is omitted, the existing lease
    (if any) is left unchanged -- a heartbeat that only proves liveness
    without extending the lease is a valid, distinct call."""
    if message.status != "active":
        raise ValueError(
            f"Cannot heartbeat message {message.message_id}: status is "
            f"'{message.status}', not 'active'."
        )
    return replace(
        message,
        heartbeat_at=heartbeat_at_iso,
        lease_expires_at=new_lease_expires_at if new_lease_expires_at is not None else message.lease_expires_at,
        last_transition_at=heartbeat_at_iso,
    )


def is_lease_expired(message: OutboxMessage, now_iso: str) -> bool:
    """Pure lease check: True if the message has a lease_expires_at set
    and now_iso is at or past it. A message with no lease_expires_at is
    never expired by this check -- older-shape/no-lease messages behave
    exactly as they did before this field existed. An unparseable
    timestamp is treated as expired/suspect, matching
    detect_stale_claims()'s own "surface, don't guess" rule."""
    if not message.lease_expires_at:
        return False
    try:
        expires = datetime.fromisoformat(message.lease_expires_at)
        now = datetime.fromisoformat(now_iso)
    except (TypeError, ValueError):
        return True
    return now >= expires


def verify_claim_ownership(
    message_as_written: OutboxMessage,
    expected_claimant: str,
    expected_processor_id: Optional[str] = None,
) -> bool:
    """The JSON_FILE_LIMITED concurrency mitigation's pure half: after the
    caller sp_write's a claim and sp_read's it back, call this to confirm
    the read-back message really shows THIS claimant as owner before
    treating the claim as held.

    NOT atomic compare-and-set. A second writer could still have raced
    between this caller's own write and its own read of that same write --
    this function cannot detect that specific interleaving; it only
    detects the case where the readback already shows a different owner
    by the time this check runs. This is the JSON_FILE_LIMITED D007
    decision's explicit, disclosed limitation, not a solved problem."""
    if message_as_written.status != "active":
        return False
    if message_as_written.claimed_by != expected_claimant:
        return False
    if expected_processor_id is not None and message_as_written.processor_id != expected_processor_id:
        return False
    return True


def complete(
    message: OutboxMessage,
    status: str = "closed",
    at_iso: Optional[str] = None,
    state_consumed_revision: Optional[str] = None,
    return_filed_path: Optional[str] = None,
    return_readback_sha256: Optional[str] = None,
    controller_match_result: Optional[str] = None,
) -> OutboxMessage:
    """Transitions a claimed ('active') message to a terminal state.
    status must be one of returned/closed/blocked -- 'proposed'/'active'
    are not valid completion states. The original 2-arg call shape
    (message, status) is unchanged and still valid -- every new parameter
    is optional and, if omitted, leaves the corresponding field on
    `message` unchanged rather than clearing it."""
    if status not in COMPLETION_STATUSES:
        raise ValueError(f"complete() status must be one of {COMPLETION_STATUSES}, got '{status}'")
    if message.status != "active":
        raise ValueError(
            f"Cannot complete message {message.message_id}: status is "
            f"'{message.status}', not 'active' -- claim it first."
        )
    return replace(
        message,
        status=status,
        last_transition_at=at_iso if at_iso is not None else message.last_transition_at,
        state_consumed_revision=state_consumed_revision if state_consumed_revision is not None else message.state_consumed_revision,
        return_filed_path=return_filed_path if return_filed_path is not None else message.return_filed_path,
        return_readback_sha256=return_readback_sha256 if return_readback_sha256 is not None else message.return_readback_sha256,
        controller_match_result=controller_match_result if controller_match_result is not None else message.controller_match_result,
    )


def classify_control_version_drift(
    message: OutboxMessage,
    expected_control_branch: str,
    expected_control_commit: str,
) -> Optional[str]:
    """Returns CONTROL_VERSION_DRIFT if the message's declared control
    identity does not match what the consuming lane expects, else None.

    Scoped to this one message's receipt only -- a caller must classify
    each message independently and must never let one drifted receipt
    fail or block an entire poll of otherwise-unrelated messages. A
    message with no declared control identity at all (both fields None --
    e.g. an older-shape message from before this field existed) is not
    treated as drift by default; there is nothing to compare."""
    if message.control_branch is None and message.control_commit is None:
        return None
    if message.control_branch != expected_control_branch or message.control_commit != expected_control_commit:
        return CONTROL_VERSION_DRIFT
    return None


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
    """Flags 'active' (claimed but never completed) messages that are
    stale. If a message carries a lease_expires_at, that lease is
    authoritative (via is_lease_expired()) and max_claim_age_seconds is
    not consulted for it. If no lease is set, falls back to the original
    v0.2 age-based heuristic unchanged -- fully backward compatible with
    messages that predate the lease field. An unparseable claimed_at_iso
    (fallback path only) is treated as stale/suspect rather than silently
    skipped, matching freshness.py's own "surface, don't guess" rule for
    unparseable timestamps. Preserves all prior claim evidence -- this
    function only reports staleness, it never mutates a message."""
    stale: List[OutboxMessage] = []
    for m in messages:
        if m.status != "active" or not m.claimed_at_iso:
            continue
        if m.lease_expires_at:
            if is_lease_expired(m, now_iso):
                stale.append(m)
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
