"""
Reusable link/route checker for Navigator HTML surfaces and Canvas
return routes.

Covers, per the regression-suite priority list:
- duplicate or competing primary-interface claims (heuristic phrase scan)
- broken relative links (resolution against a supplied known-path set)
- missing return-to-Home paths
- arrow-notation return routes (inherited rule from the Lane B correction)

Does not fetch anything — callers supply the HTML text and the set of
paths known to exist (e.g. from sp_list results), so this stays fully
offline and unit-testable.
"""
from __future__ import annotations

import posixpath
import re
from dataclasses import dataclass

HREF_SRC_RE = re.compile(r'''(?:href|src)\s*=\s*["']([^"']+)["']''', re.IGNORECASE)

ARROW_NOTATION_RE = re.compile(r"->")

COMPETING_INTERFACE_PHRASES = (
    "the current interface", "the current home", "new home", "primary interface",
    "current control surface", "current navigator control surface",
)


@dataclass
class LinkFinding:
    kind: str  # ARROW_NOTATION | UNRESOLVED_RELATIVE | NO_HOME_RETURN | COMPETING_INTERFACE_CLAIM
    detail: str

    def as_dict(self) -> dict:
        return {"kind": self.kind, "detail": self.detail}


def extract_links(html: str) -> list[str]:
    return HREF_SRC_RE.findall(html)


def resolve_relative(base_dir: str, link: str) -> str | None:
    """Resolves a relative link (posix-style, Obsidian/SharePoint use
    forward slashes) against base_dir. Returns None for absolute URLs
    (http.../https...) or in-page anchors (#...), which this function
    does not attempt to resolve."""
    if link.startswith(("http://", "https://", "#", "mailto:")):
        return None
    joined = posixpath.normpath(posixpath.join(base_dir, link))
    return joined


def check_links(html: str, *, base_dir: str, known_paths: set[str],
                 require_home_return: bool = True,
                 home_return_markers: tuple[str, ...] = ("00_HOME.md",)) -> list[LinkFinding]:
    findings: list[LinkFinding] = []

    if ARROW_NOTATION_RE.search(html):
        for m in re.finditer(r"[^\n]*->.+", html):
            findings.append(LinkFinding("ARROW_NOTATION", m.group(0)[:200]))

    links = extract_links(html)
    home_return_seen = False
    for link in links:
        resolved = resolve_relative(base_dir, link)
        if resolved is None:
            continue
        if resolved not in known_paths:
            findings.append(LinkFinding("UNRESOLVED_RELATIVE", f"{link} -> {resolved}"))
        if any(marker in resolved for marker in home_return_markers):
            home_return_seen = True

    if require_home_return and not home_return_seen:
        findings.append(LinkFinding("NO_HOME_RETURN", "no link resolving to a Home-return marker was found"))

    lower_html = html.lower()
    for phrase in COMPETING_INTERFACE_PHRASES:
        occurrences = lower_html.count(phrase)
        if occurrences > 1:
            findings.append(LinkFinding(
                "COMPETING_INTERFACE_CLAIM",
                f"phrase {phrase!r} appears {occurrences} times — review for duplicate/competing primary-interface claims",
            ))

    return findings


__all__ = ["LinkFinding", "extract_links", "resolve_relative", "check_links"]
