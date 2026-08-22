"""Email as a NOTIFY_ONLY transport -- correlation, identity and spoof checks.

No email is sent or read by this module -- it defines the pure logic a
live mail adapter would need: deterministic subject correlation, a
sender allowlist check, and replay/spoof detection via a seen
Message-ID set. Declared NOTIFY_ONLY (see destination_registry.py) --
this module never promotes an email reply to an authenticated decision.
"""

import re
from dataclasses import dataclass
from typing import Optional

SUBJECT_TOKEN_PATTERN = re.compile(r"\[SS-(\d{16}|[0-9a-f]{16})\]")


def build_subject_token(message_id: str) -> str:
    if len(message_id) != 16 or not re.fullmatch(r"[0-9a-f]{16}", message_id):
        raise ValueError(f"message_id must be a 16-char lowercase hex id, got {message_id!r}")
    return f"[SS-{message_id}]"


def extract_subject_token(subject: str) -> Optional[str]:
    match = SUBJECT_TOKEN_PATTERN.search(subject or "")
    return match.group(1) if match else None


@dataclass(frozen=True)
class EmailClassification:
    is_correlated: bool
    message_id: Optional[str]
    is_duplicate: bool
    is_spoof_suspect: bool
    sender_allowed: bool
    reason: str


def classify_email_reply(
    internet_message_id: str,
    subject: str,
    sender_address: str,
    allowed_sender_domain: str,
    seen_internet_message_ids: frozenset,
) -> EmailClassification:
    if internet_message_id in seen_internet_message_ids:
        return EmailClassification(
            is_correlated=False,
            message_id=None,
            is_duplicate=True,
            is_spoof_suspect=False,
            sender_allowed=False,
            reason=f"DUPLICATE_REPLY: Internet Message-ID {internet_message_id} already processed",
        )

    sender_allowed = sender_address.lower().endswith(f"@{allowed_sender_domain.lower()}")
    message_id = extract_subject_token(subject)

    if not sender_allowed:
        return EmailClassification(
            is_correlated=message_id is not None,
            message_id=message_id,
            is_duplicate=False,
            is_spoof_suspect=True,
            sender_allowed=False,
            reason=f"SPOOF_SUSPECT: sender {sender_address} not in allowed domain {allowed_sender_domain}",
        )

    if message_id is None:
        return EmailClassification(
            is_correlated=False,
            message_id=None,
            is_duplicate=False,
            is_spoof_suspect=False,
            sender_allowed=True,
            reason="NO_CORRELATION_TOKEN: subject carries no [SS-<id>] marker",
        )

    return EmailClassification(
        is_correlated=True,
        message_id=message_id,
        is_duplicate=False,
        is_spoof_suspect=False,
        sender_allowed=True,
        reason="CORRELATED_NOTIFY_ONLY: not an authenticated decision surface",
    )
