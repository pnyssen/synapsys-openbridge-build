"""Outbound mirror (CAP-010): plan GitHub issues for tooling / schema_field /
security cards. DRY RUN ONLY in this candidate: it builds the exact issue
payloads, the label set, and the canary + rollback plan, and performs no write.

Write path is deliberately absent. Turning it on needs (a) an explicit Steward
ACCEPT recorded in Working Memory, (b) the release class, and (c) a token from
the environment. Until then `execute` refuses.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List

from .labels import is_mirror_eligible, label_set_for_cards, labels_for

WM_DRAFTS_DIR = "MESH_QUEUE/STREAMS/DRAFTS"


def card_bytes(card: Dict[str, Any]) -> bytes:
    """Canonical serialisation: the bytes filed to Working Memory and hashed."""
    return (json.dumps(card, indent=1, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def card_sha256(card: Dict[str, Any]) -> str:
    return hashlib.sha256(card_bytes(card)).hexdigest()


def card_wm_path(card: Dict[str, Any]) -> str:
    return f"{WM_DRAFTS_DIR}/{card['id']}--v0-1.json"


def issue_payload(card: Dict[str, Any]) -> Dict[str, Any]:
    body = "\n".join([
        f"**Card** `{card['id']}`  ·  PPV **{card['ppv']}**  ·  authority HELD",
        "",
        f"Working Memory path: `{card_wm_path(card)}`",
        f"sha256: `{card_sha256(card)}`",
        "",
        f"**Signal:** {card['signal']}",
        f"**Source:** {card['evidence'].get('url') or '[unobserved]'}",
        "",
        "Working Memory holds the card and evidence; Odoo stays operational truth; this issue is a",
        "technical working copy, never the source of truth. Status changes flow back to the card as a delta.",
    ])
    return {"title": f"[{card['id']}] {card['signal'].split(': ', 1)[-1]}"[:200],
            "body": body, "labels": labels_for(card)}


def plan(cards: List[Dict[str, Any]]) -> Dict[str, Any]:
    eligible = [c for c in cards if is_mirror_eligible(c)]
    skipped = [c["id"] for c in cards if not is_mirror_eligible(c)]
    canary = eligible[0] if eligible else None
    return {
        "mode": "DRY_RUN",
        "writes_performed": 0,
        "labels_required": label_set_for_cards(cards),
        "issues": [{"card": c["id"], **issue_payload(c)} for c in eligible],
        "skipped_not_mirrored": skipped,
        "canary": None if canary is None else {
            "card": canary["id"],
            "steps": ["prestate: list issues + labels", "create ONE issue for this card",
                      "read back: title, labels, WM path and sha256 match", "rollback: close as not_planned",
                      "poststate: issue closed, no other issue touched", "receipt: sha256 of readback"],
        },
    }


def execute(*_a, **_k):
    raise PermissionError("Mirror write is OFF. Needs a recorded Steward ACCEPT, the release class, "
                          "and a token from the environment; none are present in this candidate.")
