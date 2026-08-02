"""
State-collapse and displayed-state-vs-test-hook-contradiction checks.

State collapse: an object/panel that is explicitly labelled `candidate`
should not, in the same breath, also claim `implemented`, `accepted`,
or `canonical` of itself without qualification — that is exactly the
"candidate, implemented, accepted and canonical state collapse" failure
mode this task's checklist names. The check requires an explicit
linking pattern ("is", "are", "now", "remains", "marked as", "becomes")
between the two words within one HTML chunk, and ignores raw <script>
content — a first version of this check that only required word
*proximity* produced nine false positives on real Navigator content
(governance vocabulary like "canonical candidates" legitimately using
both words about two different things in the same sentence); this
version was tightened specifically against that real evidence.

Test-hook contradiction: many of this Work Object's HTML surfaces embed
a `window.<something> = {...}` status object as a machine-readable
mirror of the visible panel counts (e.g. `window.navigatorStatus`).
This module extracts that object's data-valued fields (skipping
function-valued ones, which this offline extractor cannot evaluate)
and compares them against counts the caller has independently derived
from the visible DOM text, flagging any field where they disagree.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

WINDOW_HOOK_RE = re.compile(
    r"window\.(?P<name>[A-Za-z_$][\w$]*)\s*=\s*(?P<body>\{.*?\});",
    re.DOTALL,
)
SCRIPT_BLOCK_RE = re.compile(r"<script\b[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL)
CHUNK_BOUNDARY_RE = re.compile(r"</(?:li|p|dd|small|span|b|div|article)>", re.IGNORECASE)
TAG_RE = re.compile(r"<[^>]+>")

STATE_WORDS_NEAR_CANDIDATE = ("implemented", "accepted", "canonical", "current")
LINKING_PATTERN = r"(?:\bis\b|\bare\b|\bnow\b|\balready\b|\bremains\b|\bmarked as\b|\bbecomes\b)"


@dataclass
class StateFinding:
    kind: str  # STATE_COLLAPSE_NEAR_CANDIDATE | TEST_HOOK_FIELD_MISMATCH | TEST_HOOK_NOT_FOUND
    detail: str

    def as_dict(self) -> dict:
        return {"kind": self.kind, "detail": self.detail}


def find_state_collapse(html: str) -> list[StateFinding]:
    """Flags a chunk of text only when 'candidate' and one of
    STATE_WORDS_NEAR_CANDIDATE are linked by an explicit copula/verb
    pattern within the same HTML chunk (split at the nearest block-level
    closing tag), and the linking word is not itself negated
    ('not implemented', 'not yet current'). Raw <script> content is
    excluded — data field names co-occurring in a JS object are not
    prose claims."""
    findings: list[StateFinding] = []
    prose = SCRIPT_BLOCK_RE.sub(" ", html)
    chunks = CHUNK_BOUNDARY_RE.split(prose)

    for chunk in chunks:
        text = TAG_RE.sub(" ", chunk).lower()
        if "candidate" not in text:
            continue
        for word in STATE_WORDS_NEAR_CANDIDATE:
            if word not in text:
                continue
            forward = re.search(rf"\bcandidate\b.{{0,40}}?{LINKING_PATTERN}.{{0,40}}?\b{word}\b", text)
            backward = re.search(rf"\b{word}\b.{{0,40}}?{LINKING_PATTERN}.{{0,40}}?\bcandidate\b", text)
            match = forward or backward
            if not match:
                continue
            span = match.group(0)
            if re.search(r"\bnot\s+(yet\s+)?" + re.escape(word), span):
                continue
            findings.append(StateFinding(
                "STATE_COLLAPSE_NEAR_CANDIDATE",
                f"linked 'candidate' <-> {word!r}: ...{span.strip()[:200]}...",
            ))
    return findings


def _split_top_level(inner: str) -> list[str]:
    """Splits the inner content of a JS object literal (no outer braces)
    into top-level `key: value` entries, respecting nested {}/[]/() and
    quoted strings so commas inside them are not treated as separators."""
    entries: list[str] = []
    depth = 0
    current: list[str] = []
    in_string: str | None = None
    i = 0
    while i < len(inner):
        ch = inner[i]
        if in_string:
            current.append(ch)
            if ch == "\\" and i + 1 < len(inner):
                current.append(inner[i + 1])
                i += 2
                continue
            if ch == in_string:
                in_string = None
            i += 1
            continue
        if ch in "'\"":
            in_string = ch
            current.append(ch)
            i += 1
            continue
        if ch in "{[(":
            depth += 1
            current.append(ch)
            i += 1
            continue
        if ch in "}])":
            depth -= 1
            current.append(ch)
            i += 1
            continue
        if ch == "," and depth == 0:
            entries.append("".join(current))
            current = []
            i += 1
            continue
        current.append(ch)
        i += 1
    if "".join(current).strip():
        entries.append("".join(current))
    return entries


def _key_and_value(entry: str) -> tuple[str, str] | None:
    idx = entry.find(":")
    if idx == -1:
        return None
    return entry[:idx].strip(), entry[idx + 1:].strip()


def extract_window_hook(html: str, name: str) -> dict | None:
    for m in WINDOW_HOOK_RE.finditer(html):
        if m.group("name") != name:
            continue
        body = m.group("body")
        inner = body[1:-1]  # strip outer { }
        data_entries = []
        for entry in _split_top_level(inner):
            parsed = _key_and_value(entry)
            if parsed is None:
                continue
            key, value = parsed
            if value.startswith("(") or value.startswith("function"):
                continue  # function-valued key — not data this offline extractor can evaluate; skip it
            data_entries.append(f"{key}:{value}")
        js_ish = "{" + ",".join(data_entries) + "}"
        js_ish = re.sub(r"'([^']*)'", r'"\1"', js_ish)
        js_ish = re.sub(r"([{,]\s*)([A-Za-z_$][\w$]*)\s*:", r'\1"\2":', js_ish)
        try:
            return json.loads(js_ish)
        except json.JSONDecodeError:
            return None
    return None


def compare_hook_to_expected(hook: dict, expected: dict, *, prefix: str = "") -> list[StateFinding]:
    """expected: a dict of dotted-path -> expected value, independently
    derived by the caller from the visible DOM (not from this hook)."""
    findings: list[StateFinding] = []
    for path, expected_value in expected.items():
        node = hook
        ok = True
        for part in path.split("."):
            if not isinstance(node, dict) or part not in node:
                ok = False
                break
            node = node[part]
        if not ok:
            findings.append(StateFinding("TEST_HOOK_NOT_FOUND", f"{prefix}{path} not present in test hook"))
            continue
        if node != expected_value:
            findings.append(StateFinding(
                "TEST_HOOK_FIELD_MISMATCH",
                f"{prefix}{path}: displayed={expected_value!r} hook={node!r}",
            ))
    return findings


__all__ = [
    "StateFinding", "find_state_collapse", "extract_window_hook", "compare_hook_to_expected",
]
