"""Read-only resolver over x_ss_agent_registry rows.

Never elevates authority. A job is only transport-eligible when its
resolved registry entry has authority_class == "read_and_route" AND
activation_status indicates it is live for routing. Anything else is a
resolution failure with an explicit reason -- never a silent allow.
"""

from dataclasses import dataclass
from typing import Optional

from transport_types import RegistryEntry, ROUTABLE_AUTHORITY_CLASS

ELIGIBLE_ACTIVATION_STATUSES = frozenset({"authorised", "active"})


@dataclass(frozen=True)
class ResolutionResult:
    resolved: bool
    entry: Optional[RegistryEntry]
    reason: str


def resolve_endpoint(target_lane: str, registry: list) -> ResolutionResult:
    """Resolve target_lane to a routable RegistryEntry, or explain why not.

    This function only ever reads and compares. It never returns an entry
    implying execute authority, and never invents an entry that isn't in
    `registry`.
    """
    matches = [entry for entry in registry if entry.target_lane == target_lane]

    if not matches:
        return ResolutionResult(
            resolved=False, entry=None, reason="NOT_REGISTERED: no x_ss_agent_registry row for this target_lane"
        )

    entry = matches[0]

    if entry.authority_class != ROUTABLE_AUTHORITY_CLASS:
        return ResolutionResult(
            resolved=False,
            entry=entry,
            reason=(
                f"NOT_ELIGIBLE: authority_class is {entry.authority_class!r}, "
                f"only {ROUTABLE_AUTHORITY_CLASS!r} is transport-routable"
            ),
        )

    if entry.activation_status not in ELIGIBLE_ACTIVATION_STATUSES:
        return ResolutionResult(
            resolved=False,
            entry=entry,
            reason=f"NOT_AUTHORISED: activation_status is {entry.activation_status!r}",
        )

    return ResolutionResult(resolved=True, entry=entry, reason="RESOLVED")
