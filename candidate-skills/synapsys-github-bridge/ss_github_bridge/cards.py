"""LRN card profile (PKT-20261031-AVL-004 learning_card_profile) and the
inbound normaliser: GitHub signal -> LRN card.

Pure functions, no I/O. Rules this module enforces:
  * enums are exactly the ones in the packet; anything else is rejected.
  * standard_refs are never invented. An identifier is only recorded when it
    appears verbatim in the signal itself (e.g. a CVE/GHSA id in an advisory),
    and it is always written with checked_on "[n]" until a human checks it
    against the publisher's page.
  * delete / merge / simplify happen before any card is raised (dedupe, merge
    by category+title, then a per-run cap).
  * trigger detection is not authority: every card is Potential, authority HELD.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any, Dict, Iterable, List, Optional

KINDS = ("requirement", "learning", "defect", "capability")
CATEGORIES = ("retrieval", "schema_field", "authority", "wording", "role_accountability",
              "value_chain", "security", "tooling", "other")
SCOPES = ("lane", "cross_lane", "synapsys_wide")
SOURCE_TYPES = ("ai_lane", "github", "incident_feed", "steward", "n8n_signal", "other")
NIST_FUNCTIONS = ("GOVERN", "MAP", "MEASURE", "MANAGE")
MIRROR_CATEGORIES = ("tooling", "schema_field", "security")
NOT_CHECKED = "[n] not checked on official page"

# Candidate mapping only (AVL-004 standards_layering.key); Steward/Navigator confirm.
CATEGORY_TO_NIST = {
    "authority": "GOVERN", "role_accountability": "GOVERN",
    "retrieval": "MEASURE",
    "security": "MANAGE", "tooling": "MANAGE", "schema_field": "MANAGE",
    "value_chain": "MAP", "wording": "MAP", "other": "MAP",
}

_ID_PATTERNS = (
    ("CVE", re.compile(r"\bCVE-\d{4}-\d{4,}\b")),
    ("CWE", re.compile(r"\bCWE-\d{1,5}\b")),
    ("GHSA", re.compile(r"\bGHSA(?:-[23456789cfghjmpqrvwx]{4}){3}\b")),
)

# First matching rule wins. Deterministic and order-significant.
_CATEGORY_RULES = (
    ("security", ("advisory", "vulnerab", "cve-", "secret", "security", "ghsa")),
    ("authority", ("authority", "d001", "d007", "d009", "steward", "approval", "release class")),
    ("role_accountability", ("accountab", "raci", "role ")),
    ("schema_field", ("schema", "field", "odoo model", "x_ss_", "x_itc_")),
    ("retrieval", ("retriev", "resolver", "search miss", "not found", "keyword search")),
    ("value_chain", ("outcome", "benefit", "asset register", "value chain")),
    ("wording", ("wording", "naming", "terminology", "typo")),
    ("tooling", ("ci ", "build", "test", "workflow", "dependabot", "bump ", "lint",
                 "deploy", "check", "mcp", "connector", "pytest")),
)


def categorise(text: str, signal_type: str = "") -> str:
    hay = f"{signal_type} {text}".lower()
    for category, needles in _CATEGORY_RULES:
        if any(n in hay for n in needles):
            return category
    return "other"


def kind_for(signal_type: str) -> str:
    return {"ci_failure": "defect", "advisory": "defect", "pull_request": "capability",
            "issue": "requirement"}.get(signal_type, "learning")


def extract_standard_refs(text: str) -> List[Dict[str, str]]:
    """Identifiers present verbatim in the text. Never inferred, never version-guessed."""
    refs, seen = [], set()
    for standard, pattern in _ID_PATTERNS:
        for match in pattern.findall(text or ""):
            if (standard, match) not in seen:
                seen.add((standard, match))
                refs.append({"standard": standard, "id": match, "version": "[n]",
                             "checked_on": NOT_CHECKED})
    return refs


def _sig_text(sig: Dict[str, Any]) -> str:
    return f"{sig.get('title', '')}\n{sig.get('body', '')}"


def signal_key(sig: Dict[str, Any]) -> str:
    return f"{sig['repo']}#{sig['type']}#{sig['number']}"


def card_id(sig: Dict[str, Any]) -> str:
    """Stable id from the signal key, so a re-run never mints a second card."""
    return "LRN-GH-" + hashlib.sha256(signal_key(sig).encode()).hexdigest()[:10]


def normalise(sig: Dict[str, Any]) -> Dict[str, Any]:
    text = _sig_text(sig)
    category = categorise(text, sig["type"])
    body_first = (sig.get("body") or "").strip().splitlines()
    return {
        "id": card_id(sig),
        "kind": kind_for(sig["type"]),
        "category": category,
        "scope": "synapsys_wide",
        "source_type": "github",
        "nist_function": CATEGORY_TO_NIST[category],
        "standard_refs": extract_standard_refs(text),
        "signal": f"{sig['repo']} {sig['type']} #{sig['number']}: {sig['title'].strip()}",
        "root_cause": "[unobserved]",
        "evidence": {"url": sig.get("url"), "state": sig.get("state"),
                     "first_line": body_first[0][:200] if body_first else ""},
        "observing_lane": "claude_code",
        "affected_lanes": [],
        "owning_service_candidates": ["SC-04 Capability Encoding and Reuse",
                                      "SC-05 Assurance Audit and Learning"],
        "ppv": "Potential",
        "authority_state": "HELD (trigger detection is not authority)",
        "delete_merge_defer": "Merge if same category and title as another card in this run.",
        "next_valid_movement": "Navigator rank (QIU) and route",
        "merged_signals": [signal_key(sig)],
    }


def validate_card(card: Dict[str, Any]) -> List[str]:
    errs = []
    for field, allowed in (("kind", KINDS), ("category", CATEGORIES), ("scope", SCOPES),
                           ("source_type", SOURCE_TYPES), ("nist_function", NIST_FUNCTIONS)):
        if card.get(field) not in allowed:
            errs.append(f"{field}={card.get(field)!r} not in {allowed}")
    for ref in card.get("standard_refs", []):
        if set(ref) != {"standard", "id", "version", "checked_on"}:
            errs.append(f"standard_ref has wrong keys: {sorted(ref)}")
    if card.get("ppv") != "Potential":
        errs.append("ppv must be Potential for a new card")
    return errs


# Cap keeps the most consequential cards; this is an ordering aid, not a QIU rank
# (Navigator does the ranking).
_RANK = {"security": 0, "authority": 1, "schema_field": 2, "tooling": 3}


def _title_key(card: Dict[str, Any]) -> str:
    title = card["signal"].split(": ", 1)[-1].lower()
    return card["category"] + "|" + re.sub(r"[^a-z0-9]+", " ", title).strip()


def build_cards(signals: Iterable[Dict[str, Any]], cap: Optional[int]) -> Dict[str, Any]:
    """delete (dupes, non-open noise) -> merge (same category+title) -> simplify -> cap."""
    deleted, merged = [], []
    unique: Dict[str, Dict[str, Any]] = {}
    for sig in signals:
        key = signal_key(sig)
        if key in unique or sig.get("state", "open") != "open":
            deleted.append(key)          # exact duplicate, or no longer open
            continue
        unique[key] = sig
    by_title: Dict[str, Dict[str, Any]] = {}
    for sig in unique.values():
        card = normalise(sig)
        tk = _title_key(card)
        if tk in by_title:
            by_title[tk]["merged_signals"].append(signal_key(sig))
            merged.append(signal_key(sig))
            continue
        by_title[tk] = card
    cards = sorted(by_title.values(), key=lambda c: (_RANK.get(c["category"], 9),
                                                     c["kind"] != "defect", c["id"]))
    over = cards[cap:] if cap is not None else []
    cards = cards[:cap] if cap is not None else cards
    return {"cards": cards, "deleted": deleted, "merged": merged,
            "deferred_over_cap": [c["id"] for c in over]}
