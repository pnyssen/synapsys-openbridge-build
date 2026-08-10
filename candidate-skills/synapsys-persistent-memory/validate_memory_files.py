"""Offline, zero-network validator for the synapsys.md / steward.md pair.

Checks required section headers are present and rejects any line that
asserts settled authority/decision status rather than observation --
the same "self_authority_claim" discipline used in the sibling
synapsys-tobe-realignment candidate, applied here to a different file
shape (free-form sections, not per-entry fields).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

SYNAPSYS_REQUIRED_HEADERS = ["Purpose", "Operating discipline", "Standing rule"]
STEWARD_REQUIRED_HEADERS = ["Role", "Observed this session"]

# Words that, unqualified, assert a settled decision rather than an
# observation. "context, not authority" / "not a grant of authority"
# framing nearby is what keeps steward.md honest -- a bare claim
# without that framing is the failure mode.
AUTHORITY_ASSERTION_WORDS = ["DECIDED", "RATIFIED", "MANDATED", "APPROVED BY DEFAULT"]


@dataclass
class FileReport:
    name: str
    missing_headers: list[str] = field(default_factory=list)
    authority_flags: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.missing_headers and not self.authority_flags


def _headers(text: str) -> list[str]:
    return [m.group(1).strip() for m in re.finditer(r"^##\s+(.+)$", text, re.MULTILINE)]


def _missing_headers(required: list[str], present: list[str]) -> list[str]:
    # A present header may carry a parenthetical/date suffix (e.g.
    # "Purpose (Steward-ratified 2026-07-14)") -- match on prefix, not
    # exact equality, or every real-world header fails a trivial check.
    return [r for r in required if not any(p == r or p.startswith(r) for p in present)]


def _unattributed_authority_flags(text: str) -> list[str]:
    flags = []
    for word in AUTHORITY_ASSERTION_WORDS:
        for m in re.finditer(rf"\b{word}\b", text, re.IGNORECASE):
            # Attributed if immediately hyphen-joined to a preceding word
            # ("Steward-ratified") -- that's a cited source, not a bare
            # self-assertion. Only flag the unattributed form.
            prefix = text[max(0, m.start() - 20) : m.start()]
            if re.search(r"[A-Za-z]+-$", prefix):
                continue
            flags.append(f"asserts '{word}' without attribution")
    return flags


def validate_synapsys_md(text: str) -> FileReport:
    report = FileReport(name="synapsys.md")
    report.missing_headers = _missing_headers(SYNAPSYS_REQUIRED_HEADERS, _headers(text))
    report.authority_flags = _unattributed_authority_flags(text)
    return report


def validate_steward_md(text: str) -> FileReport:
    report = FileReport(name="steward.md")
    report.missing_headers = _missing_headers(STEWARD_REQUIRED_HEADERS, _headers(text))
    report.authority_flags = _unattributed_authority_flags(text)
    if "not a grant of authority" not in text.lower():
        report.authority_flags.append(
            "missing the explicit 'not a grant of authority' qualifier -- required "
            "for a file that records observations about the Steward"
        )
    return report


if __name__ == "__main__":
    import sys
    from pathlib import Path

    here = Path(__file__).parent
    reports = [
        validate_synapsys_md((here / "synapsys.md").read_text()),
        validate_steward_md((here / "steward.md").read_text()),
    ]
    ok = True
    for r in reports:
        status = "PASS" if r.ok else "FAIL"
        print(f"[{status}] {r.name}")
        for h in r.missing_headers:
            print(f"    missing header: {h}")
        for a in r.authority_flags:
            print(f"    authority flag: {a}")
        ok = ok and r.ok
    sys.exit(0 if ok else 1)
