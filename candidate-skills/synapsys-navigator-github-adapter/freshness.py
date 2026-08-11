"""Freshness/last-read stamping for SynapSys Agent state providers.

Implements the five-state freshness vocabulary already ruled in
AI_NAVIGATOR_SERVICE_CATALOGUE_OPERATING_ARCHITECTURE_v0.1 (section 7):
CURRENT_MATCHED / CURRENT_WITH_NON_MATERIAL_VARIANCE / STALE_PROJECTION /
CONFLICTED / CONTENT_EXTRACTION_PENDING -- generalised here from
single-query use to continuous/persistent-agent use, per the gap named in
STATE_PROVIDER_CONTRACT.md.

Pure classification only: no network, no subprocess, no filesystem access,
no call to time.time()/datetime.now(). Callers supply timestamps and a
success flag from their own MCP connector call; this module only decides
which of the five states that combination represents. Isolation verified
by test_freshness.py via an AST-based import check, matching the pattern
already used by validator.py and evidence_validator.py in this repo.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

FRESHNESS_STATES = (
    "CURRENT_MATCHED",
    "CURRENT_WITH_NON_MATERIAL_VARIANCE",
    "STALE_PROJECTION",
    "CONFLICTED",
    "CONTENT_EXTRACTION_PENDING",
)


@dataclass(frozen=True)
class FreshnessStamp:
    state: str
    source: str
    checked_at_iso: str
    last_successful_read_iso: Optional[str]
    staleness_seconds: Optional[float]
    reason: str


def _seconds_between(earlier_iso: str, later_iso: str) -> Optional[float]:
    try:
        earlier = datetime.fromisoformat(earlier_iso)
        later = datetime.fromisoformat(later_iso)
    except (TypeError, ValueError):
        return None
    return (later - earlier).total_seconds()


def classify(
    *,
    source: str,
    checked_at_iso: str,
    last_successful_read_iso: Optional[str],
    max_age_seconds: float,
    read_succeeded: bool,
    conflict_detected: bool = False,
    conflict_detail: str = "",
) -> FreshnessStamp:
    """Classify one provider read into exactly one of the five freshness states.

    max_age_seconds is caller-supplied per source (e.g. Odoo operational
    records might get a short window; a Working Memory receipt that never
    changes once filed might get a much longer one) -- this module does not
    impose a single global window, since different sources have genuinely
    different natural change rates.
    """
    if not read_succeeded:
        return FreshnessStamp(
            "CONTENT_EXTRACTION_PENDING", source, checked_at_iso,
            last_successful_read_iso, None,
            "Read attempt did not succeed this cycle.",
        )

    if conflict_detected:
        return FreshnessStamp(
            "CONFLICTED", source, checked_at_iso, last_successful_read_iso, 0.0,
            conflict_detail or "Two sources disagree on the same fact.",
        )

    if last_successful_read_iso is None:
        return FreshnessStamp(
            "CONTENT_EXTRACTION_PENDING", source, checked_at_iso, None, None,
            "No prior successful read recorded for this source.",
        )

    age = _seconds_between(last_successful_read_iso, checked_at_iso)
    if age is None:
        return FreshnessStamp(
            "CONTENT_EXTRACTION_PENDING", source, checked_at_iso,
            last_successful_read_iso, None,
            "Timestamp could not be parsed; treated as unresolved, not guessed.",
        )

    if age < 0:
        return FreshnessStamp(
            "CONFLICTED", source, checked_at_iso, last_successful_read_iso, age,
            "last_successful_read_iso is after checked_at_iso -- clock or "
            "ordering inconsistency, surfaced rather than silently clamped to zero.",
        )

    if age <= max_age_seconds:
        return FreshnessStamp(
            "CURRENT_MATCHED", source, checked_at_iso, last_successful_read_iso, age,
            f"Within the {max_age_seconds}s freshness window for this source.",
        )

    if age <= max_age_seconds * 3:
        return FreshnessStamp(
            "CURRENT_WITH_NON_MATERIAL_VARIANCE", source, checked_at_iso,
            last_successful_read_iso, age,
            f"Beyond the {max_age_seconds}s window but within 3x it; treated "
            "as non-material variance, not stale, per this source's own tolerance.",
        )

    return FreshnessStamp(
        "STALE_PROJECTION", source, checked_at_iso, last_successful_read_iso, age,
        f"Age {age:.0f}s exceeds 3x the {max_age_seconds}s freshness window.",
    )
