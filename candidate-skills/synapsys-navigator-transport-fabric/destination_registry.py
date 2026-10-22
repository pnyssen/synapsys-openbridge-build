"""Destination/transport separation.

`target_lane` names a logical destination (who should act), never a
transport (how the packet physically gets there). One destination may be
reachable over more than one transport, with an explicit fallback order,
while a single logical message_id/replay identity is preserved end to end.
"""

from dataclasses import dataclass
from typing import Optional

TRANSPORT_CAPABILITIES = frozenset(
    {
        "NOTIFY_ONLY",
        "DELIVER_ONLY",
        "DELIVER_AND_RETURN",
        "AUTHORITATIVE_HUMAN_DECISION_SURFACE",
        "AI_RUNTIME",
        "UNSUPPORTED",
    }
)

TRANSPORTS = frozenset(
    {
        "n8n_webhook",
        "github",
        "email",
        "odoo_discuss_channel",
        "ai_direct_runtime",
        "human_approval_surface",
        "working_memory_file",
        "browser_manual",
    }
)


@dataclass(frozen=True)
class TransportDeclaration:
    transport: str
    capability: str

    def __post_init__(self) -> None:
        if self.transport not in TRANSPORTS:
            raise ValueError(f"unknown transport: {self.transport!r}")
        if self.capability not in TRANSPORT_CAPABILITIES:
            raise ValueError(f"unknown capability: {self.capability!r}")


@dataclass(frozen=True)
class DestinationRoute:
    """One logical destination's transport fallback chain, primary first."""

    destination: str
    chain: tuple  # tuple[TransportDeclaration, ...], primary first

    def primary(self) -> TransportDeclaration:
        return self.chain[0]

    def authoritative_decision_transport(self) -> Optional[TransportDeclaration]:
        """Return the transport declared as the actual decision surface, if any.

        A destination may have NOTIFY_ONLY transports (email, GitHub comment)
        in its chain without either of them being authority-bearing. This
        returns None unless a transport is explicitly declared
        AUTHORITATIVE_HUMAN_DECISION_SURFACE.
        """
        for declared in self.chain:
            if declared.capability == "AUTHORITATIVE_HUMAN_DECISION_SURFACE":
                return declared
        return None


# The declared capability matrix from the challenge document (section B).
# This is documentation encoded as data, not a live routing table -- no
# transport call is made from this module.
DECLARED_CAPABILITY_MATRIX = {
    "n8n_webhook": "DELIVER_ONLY",
    "github": "NOTIFY_ONLY",
    "email": "NOTIFY_ONLY",
    "odoo_discuss_channel": "NOTIFY_ONLY",
    "ai_direct_runtime": "AI_RUNTIME",
    "human_approval_surface": "AUTHORITATIVE_HUMAN_DECISION_SURFACE",
    "working_memory_file": "DELIVER_AND_RETURN",
    "browser_manual": "UNSUPPORTED",
}
"""
Rationale, per transport:

n8n_webhook: DELIVER_ONLY -- the Agent Job Relay (MfH4LqF18MpIebDn) proves
  ingress delivery into AGENT_OUTBOX; it has no return/claim path today.

github: NOTIFY_ONLY -- PR/issue/comment/check-run events can carry a
  correlation token and deliver signals, but a GitHub event is not proof
  of an authenticated D007 decision; CI result is evidence, not authority.

email: NOTIFY_ONLY -- without sender/thread authentication and a governed
  identity check, an email reply cannot be trusted as an authority-bearing
  return. Declared NOTIFY_ONLY, not AUTHORITATIVE, until that identity
  check is built and independently reviewed.

odoo_discuss_channel: NOTIFY_ONLY -- the "AI Auditor" channel (id 49,
  ai_chat type) delivers a message; nothing currently confirms an agent
  is invoked or a substantive return is produced from posting into it
  (matches the D009 finding this session that posting there did not
  invoke the agent).

ai_direct_runtime: AI_RUNTIME -- an actual callable AI endpoint (e.g. a
  live D009/Gemini API call) both invokes and can return a result; this
  is the only transport where DELIVER_AND_RETURN would come from a single
  call, once a live callable exists (none is wired in this candidate).

human_approval_surface: AUTHORITATIVE_HUMAN_DECISION_SURFACE -- a
  purpose-built, identity-checked decision UI (not email or GitHub) is
  the only surface this package treats as capable of bearing D001/D007
  authority. This candidate does not build that UI; it declares the
  requirement so nothing else silently gets treated as if it had it.

working_memory_file: DELIVER_AND_RETURN -- filing + independent readback
  (sp_write followed by sp_read) is the one transport already proven,
  repeatedly, this session, to durably deliver and return evidence.

browser_manual: UNSUPPORTED -- explicitly the last-resort fallback only
  when no callable/authenticated runtime exists; never a default.
"""
