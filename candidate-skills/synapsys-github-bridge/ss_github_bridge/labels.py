"""Card -> GitHub label mapping and mirror eligibility (CAP-010 rules).

One label per axis, namespaced `axis:value`. The ppv label is always the card's
own state; GitHub never moves PPV.
"""
from __future__ import annotations

from typing import Any, Dict, List

from .cards import MIRROR_CATEGORIES

LABEL_AXES = ("kind", "category", "scope", "ppv", "nist")


def is_mirror_eligible(card: Dict[str, Any]) -> bool:
    return card.get("category") in MIRROR_CATEGORIES


def labels_for(card: Dict[str, Any]) -> List[str]:
    return [
        f"kind:{card['kind']}",
        f"category:{card['category']}",
        f"scope:{card['scope']}",
        f"ppv:{card['ppv'].lower()}",
        f"nist:{card['nist_function'].lower()}",
    ]


def label_set_for_cards(cards: List[Dict[str, Any]]) -> List[str]:
    """Distinct labels that must exist before an issue can carry them."""
    return sorted({lab for c in cards if is_mirror_eligible(c) for lab in labels_for(c)})
