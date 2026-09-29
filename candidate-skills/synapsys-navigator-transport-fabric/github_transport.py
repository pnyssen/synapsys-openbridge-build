"""GitHub as a NOTIFY_ONLY transport -- correlation and dedup only.

PR #31 is candidate code, not a runtime; this module does not call the
GitHub API. It defines how a GitHub event (PR comment, check-run,
issue comment) would be correlated back to a message_id and deduplicated,
so a live wiring layer has an unambiguous contract to implement against.
"""

import re
from dataclasses import dataclass
from typing import Optional

CORRELATION_MARKER_PATTERN = re.compile(r"\[SS-MSG:([0-9a-f]{16})\]")


def build_correlation_marker(message_id: str) -> str:
    if len(message_id) != 16 or not re.fullmatch(r"[0-9a-f]{16}", message_id):
        raise ValueError(f"message_id must be a 16-char lowercase hex id, got {message_id!r}")
    return f"[SS-MSG:{message_id}]"


def extract_message_id(event_body: str) -> Optional[str]:
    """Pull the correlation marker out of a PR/issue/comment body, if present."""
    match = CORRELATION_MARKER_PATTERN.search(event_body or "")
    return match.group(1) if match else None


@dataclass(frozen=True)
class GithubEventClassification:
    is_correlated: bool
    message_id: Optional[str]
    is_duplicate: bool
    is_authority_bearing: bool
    reason: str


def classify_github_event(
    event_id: str,
    event_body: str,
    seen_event_ids: frozenset,
) -> GithubEventClassification:
    """Classify one GitHub event for the transport layer.

    GitHub is always NOTIFY_ONLY here (see destination_registry.py) -- this
    function never marks an event authority-bearing, regardless of content,
    because CI results and comments are evidence, not D001/D007 decisions.
    """
    if event_id in seen_event_ids:
        return GithubEventClassification(
            is_correlated=False,
            message_id=None,
            is_duplicate=True,
            is_authority_bearing=False,
            reason=f"DUPLICATE_EVENT: event_id {event_id} already processed",
        )

    message_id = extract_message_id(event_body)
    if message_id is None:
        return GithubEventClassification(
            is_correlated=False,
            message_id=None,
            is_duplicate=False,
            is_authority_bearing=False,
            reason="NO_CORRELATION_MARKER: cannot link this event to a dispatch",
        )

    return GithubEventClassification(
        is_correlated=True,
        message_id=message_id,
        is_duplicate=False,
        is_authority_bearing=False,
        reason="CORRELATED_NOTIFY_ONLY: evidence signal, not an authority decision",
    )
