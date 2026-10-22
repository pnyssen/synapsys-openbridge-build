"""Shared frozen dataclasses for the Navigator transport fabric.

Zero I/O -- no network, filesystem, subprocess, or wall-clock reads
anywhere in this package. Every function that needs "now" takes it as
an explicit ISO-8601 string parameter from the caller.

Scope boundary (Architecture Decision, this session): `x_ss_agent_registry`
is the domain/agent governance and routing plane. `read_and_route` is the
highest authority it can express -- there is no execute value, by
platform-wide schema design. This transport fabric is a separate D007
platform transport component: it claims, routes, and hands a governed
packet to a runtime adapter. It never decides, assures, approves, or
rejects on the target domain's behalf, and it never treats a resolved
route as execute authority.
"""

from dataclasses import dataclass, field
from typing import Optional


AUTHORITY_CLASSES = frozenset({"read_only", "read_and_flag", "read_and_route"})
ROUTABLE_AUTHORITY_CLASS = "read_and_route"

CLAIM_STATUSES = frozenset({"CLAIMED", "HEARTBEAT", "RELEASED", "EXPIRED"})
TRANSPORT_STATUSES = frozenset(
    {"WAITING_EXTERNAL_RUNTIME", "DEGRADED", "RETURNED", "CLAIMED", "RELEASED", "EXPIRED"}
)
RUNTIME_RESULT_STATUSES = frozenset(
    {"ATTEMPTED_RETURNED", "DECLINED", "TIMEOUT", "WAITING_EXTERNAL_RUNTIME", "DEGRADED"}
)


@dataclass(frozen=True)
class OutboxJob:
    """A single AGENT_OUTBOX message, as read from the outbox (transport view only)."""

    message_id: str
    target_lane: str
    status: str  # "open" | "closed"
    claimed_by: Optional[str]
    context_id: str
    control_marker: str
    state_revision: str
    enqueued_at_iso: str
    replay_hash: Optional[str] = None

    def logical_key(self) -> tuple:
        """Identity of the underlying unit of work, independent of message_id.

        Two jobs sharing this key represent the same logical piece of work
        (e.g. a resend with a new message_id but the same decision bound to
        the same state_revision) and must not both be in flight at once.
        """
        return (self.context_id, self.control_marker, self.state_revision)


@dataclass(frozen=True)
class RegistryEntry:
    """A read-only projection of one x_ss_agent_registry row."""

    agent_code: str
    primary_domain: str
    owner_lane: str
    authority_class: str  # must be one of AUTHORITY_CLASSES
    activation_status: str  # e.g. "authorised", "active", "held", "deactivated"
    target_lane: str  # the outbox target_lane string this entry resolves for

    def __post_init__(self) -> None:
        if self.authority_class not in AUTHORITY_CLASSES:
            raise ValueError(
                f"authority_class {self.authority_class!r} is not a recognised "
                f"x_ss_agent_registry value -- refusing to construct a "
                f"RegistryEntry with an authority class the live schema "
                f"does not support (no 'execute' class exists by design)."
            )


@dataclass(frozen=True)
class ClaimRecord:
    """Transport-layer claim state for one OutboxJob. Not a domain decision."""

    message_id: str
    claimed_by: str
    claimed_at_iso: str
    heartbeat_at_iso: str
    status: str  # one of CLAIM_STATUSES

    def __post_init__(self) -> None:
        if self.status not in CLAIM_STATUSES:
            raise ValueError(f"invalid claim status: {self.status!r}")


@dataclass(frozen=True)
class RuntimeInvocationRequest:
    """The exact governed packet handed to a runtime adapter."""

    message_id: str
    target_lane: str
    context_id: str
    control_marker: str
    state_revision: str
    objective: str
    source_refs: str


@dataclass(frozen=True)
class RuntimeInvocationResult:
    """A runtime adapter's response to one RuntimeInvocationRequest."""

    status: str  # one of RUNTIME_RESULT_STATUSES
    detail: str
    returned_message_id: Optional[str] = None
    returned_payload: Optional[dict] = field(default=None)

    def __post_init__(self) -> None:
        if self.status not in RUNTIME_RESULT_STATUSES:
            raise ValueError(f"invalid runtime result status: {self.status!r}")


@dataclass(frozen=True)
class ConsumedReturn:
    """The outcome of the return bridge validating and consuming a runtime return."""

    accepted: bool
    reason: str
    consumed_state_revision: Optional[str] = None
    controller_state_revision_at_consumption: Optional[str] = None


@dataclass(frozen=True)
class HealthProjectionEntry:
    """One row of the Navigator transport-health projection."""

    domain: str
    owner_lane: str
    status: str  # ACTIVE | HELD | DEGRADED | OFFLINE
    last_heartbeat_iso: Optional[str]
    pending_jobs: int
    claim_latency_seconds: Optional[float]
    last_return_iso: Optional[str]
    authority_boundary: str  # verbatim echo of the registry's authority_class
