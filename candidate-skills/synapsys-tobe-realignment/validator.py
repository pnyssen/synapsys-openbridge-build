"""Offline, zero-network validator for TOBE priority stack documents.

Reads a single markdown file's text and returns a structural report.
Does not fetch anything, does not mutate anything, does not decide
whether a priority stack's content is *correct* -- only whether it is
structurally honest about what it does and doesn't currently know,
per the required-field schema in templates/TOBE_PRIORITY_STACK_TEMPLATE_v0.1.md.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

REQUIRED_ENTRY_FIELDS = [
    "tobe_goal",
    "as_is_state",
    "source_of_truth",
    "verification_instruction",
    "next_valid_action",
    "self_authority_claim",
]

REQUIRED_FRONT_MATTER_FIELDS = ["status", "authority_state", "replay_validity"]

# Self-authority claims that are NOT allowed to appear as a bare,
# unqualified claim about the entry itself. Quoting these words from a
# cited source ("the register shows ADOPTED") is fine; asserting them
# about the entry's own state is the failure mode this exists to catch.
FORBIDDEN_SELF_CLAIMS = ["VERIFIED", "ADOPTED", "AUTHORISED", "AUTHORIZED"]

ENTRY_HEADER_RE = re.compile(r"^###\s+\d+\.\s+.+$", re.MULTILINE)
FIELD_RE = re.compile(r"\*\*([a-z_]+)\*\*:\s*(.+)", re.IGNORECASE)


@dataclass
class EntryReport:
    title: str
    fields_present: dict[str, str] = field(default_factory=dict)
    missing_fields: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.missing_fields and not self.errors


@dataclass
class DocumentReport:
    front_matter_ok: bool
    missing_front_matter: list[str]
    entries: list[EntryReport]
    global_errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return (
            self.front_matter_ok
            and not self.global_errors
            and all(e.ok for e in self.entries)
        )

    def summary(self) -> str:
        lines = [f"ok={self.ok}", f"entries={len(self.entries)}"]
        if self.missing_front_matter:
            lines.append(f"missing_front_matter={self.missing_front_matter}")
        for e in self.entries:
            status = "PASS" if e.ok else "FAIL"
            lines.append(f"  [{status}] {e.title}")
            for m in e.missing_fields:
                lines.append(f"      missing: {m}")
            for err in e.errors:
                lines.append(f"      error: {err}")
            for w in e.warnings:
                lines.append(f"      warning: {w}")
        for err in self.global_errors:
            lines.append(f"global error: {err}")
        return "\n".join(lines)


def _extract_front_matter(text: str) -> str:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    return m.group(1) if m else ""


def _split_entries(text: str) -> list[str]:
    """Split the document body into per-entry blocks at '### N. ' headers."""
    headers = list(ENTRY_HEADER_RE.finditer(text))
    if not headers:
        return []
    blocks = []
    for i, h in enumerate(headers):
        start = h.start()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        blocks.append(text[start:end])
    return blocks


def _parse_entry(block: str) -> EntryReport:
    title_line = block.splitlines()[0].lstrip("# ").strip()
    report = EntryReport(title=title_line)

    for field_match in FIELD_RE.finditer(block):
        field_name = field_match.group(1).lower()
        field_value = field_match.group(2).strip()
        report.fields_present[field_name] = field_value

    for required in REQUIRED_ENTRY_FIELDS:
        if required not in report.fields_present:
            report.missing_fields.append(required)

    # self_authority_claim must be present and must not assert elevated
    # authority about the entry itself.
    claim = report.fields_present.get("self_authority_claim", "")
    if claim:
        claim_upper = claim.upper()
        for forbidden in FORBIDDEN_SELF_CLAIMS:
            if forbidden in claim_upper and "none" not in claim.lower() and "held" not in claim.lower():
                report.errors.append(
                    f"self_authority_claim asserts '{forbidden}' about itself: {claim!r}"
                )

    # as_is_state should carry an explicit date (a 4-digit year is the
    # cheap, reliable check -- this is deliberately loose, not a full
    # date parser).
    as_is = report.fields_present.get("as_is_state", "")
    if as_is and not re.search(r"\b20\d{2}\b", as_is):
        report.warnings.append("as_is_state has no visible year -- may be undated")

    # source_of_truth should look like a path, not a description.
    source = report.fields_present.get("source_of_truth", "")
    if source and "/" not in source and ".md" not in source:
        report.warnings.append(
            "source_of_truth doesn't look like a path -- may be a description instead"
        )

    return report


def validate(text: str) -> DocumentReport:
    front_matter = _extract_front_matter(text)
    missing_fm = [f for f in REQUIRED_FRONT_MATTER_FIELDS if f"{f}:" not in front_matter]

    global_errors = []
    if front_matter and "authority_state" in front_matter:
        if "HELD" not in front_matter.upper():
            global_errors.append(
                "document-level authority_state is not HELD -- this template "
                "is only valid for HELD/candidate documents"
            )

    entry_blocks = _split_entries(text)
    if not entry_blocks:
        global_errors.append("no '### N. ' priority entries found")

    entries = [_parse_entry(b) for b in entry_blocks]

    return DocumentReport(
        front_matter_ok=not missing_fm,
        missing_front_matter=missing_fm,
        entries=entries,
        global_errors=global_errors,
    )


def validate_file(path: str) -> DocumentReport:
    with open(path, "r", encoding="utf-8") as fh:
        return validate(fh.read())


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("usage: python validator.py <path-to-tobe-stack.md>")
        raise SystemExit(2)

    report = validate_file(sys.argv[1])
    print(report.summary())
    raise SystemExit(0 if report.ok else 1)
