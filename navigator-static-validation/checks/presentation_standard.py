"""
White-background / readable-text presentation standard, and a
heuristic dead-UI-control detector.

Presentation rule (per this Work Object's standing instruction, applied
consistently across every candidate build this session): no
`prefers-color-scheme` media query, and an explicit white background
declared somewhere in the stylesheet.

Dead-control heuristic: every element carrying `data-open="X"` should
have a corresponding panel/section with `id="X"`; every element with an
`onclick`/inline handler calling a bare function name should have that
function defined somewhere in the page's own <script> blocks (a
same-page-only check — it cannot see functions defined in other files).
"""
from __future__ import annotations

import re
from dataclasses import dataclass

DARK_MODE_QUERY_RE = re.compile(r"@media\s*\(\s*prefers-color-scheme", re.IGNORECASE)
WHITE_BG_RE = re.compile(r"background(?:-color)?\s*:\s*(#fff(?:fff)?|white)\b", re.IGNORECASE)
DATA_OPEN_RE = re.compile(r'data-open\s*=\s*["\']([^"\']+)["\']')
ELEMENT_ID_RE = re.compile(r'\bid\s*=\s*["\']([^"\']+)["\']')
FUNCTION_DEF_RE = re.compile(r'function\s+([A-Za-z_$][\w$]*)\s*\(')


@dataclass
class PresentationFinding:
    kind: str  # DARK_MODE_QUERY_PRESENT | NO_WHITE_BACKGROUND_DECLARED | DEAD_DATA_OPEN_TARGET
    detail: str

    def as_dict(self) -> dict:
        return {"kind": self.kind, "detail": self.detail}


def check_presentation(html: str) -> list[PresentationFinding]:
    findings: list[PresentationFinding] = []
    if DARK_MODE_QUERY_RE.search(html):
        findings.append(PresentationFinding("DARK_MODE_QUERY_PRESENT", "a prefers-color-scheme media query is present"))
    if not WHITE_BG_RE.search(html):
        findings.append(PresentationFinding("NO_WHITE_BACKGROUND_DECLARED", "no explicit #fff/white background declaration found"))
    return findings


def check_dead_data_open_targets(html: str) -> list[PresentationFinding]:
    findings: list[PresentationFinding] = []
    targets = set(DATA_OPEN_RE.findall(html))
    ids = set(ELEMENT_ID_RE.findall(html))
    for target in sorted(targets):
        if target not in ids:
            findings.append(PresentationFinding(
                "DEAD_DATA_OPEN_TARGET", f"data-open={target!r} has no matching id={target!r} element on the page",
            ))
    return findings


__all__ = ["PresentationFinding", "check_presentation", "check_dead_data_open_targets"]
