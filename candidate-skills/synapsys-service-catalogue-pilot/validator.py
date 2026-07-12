"""Local, offline validator for SynapSys Service Catalogue artefacts
(Service Requests, Capability Cards, outcome receipts).

Zero network access, zero subprocess calls, zero filesystem writes.
Reads a single markdown file's text and reports structural findings.
Authorized scope per CODEX_ASSESSMENT_SERVICE_CATALOGUE_LIFECYCLE_IMPLEMENTATION_READINESS_v0.1.md:
"Code may prepare... a local validation script for required fields and SHA-256 checks."
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field

ALLOWED_STATUS = {
    "SUBMITTED",
    "WORKING",
    "INPUT_REQUIRED",
    "COMPLETED",
    "FAILED",
    "REJECTED",
    "CANCELED",
}

ALLOWED_ORIGIN_IDENTITY_STATE = {
    "DECLARED",
    "ROSTER_MATCHED",
    "ROSTER_GAP",
    "UNRESOLVED",
}

REQUIRED_FRONT_MATTER_FIELDS = (
    "artefact_type",
    "request_id",
    "origin_lane",
    "origin_identity_state",
    "status",
    "ppv_state",
    "authority_state",
)

_FRONT_MATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
_FIELD_RE = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*):\s*(.*)$")
_RECEIPT_LINE_RE = re.compile(r"^RECEIPT: SHA-256.*$", re.MULTILINE)
_HASH_VALUE_RE = re.compile(r"\b([0-9a-f]{64})\b")


@dataclass
class ValidationResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    front_matter: dict[str, str] = field(default_factory=dict)
    hash_match_convention: str | None = None


def parse_front_matter(text: str) -> dict[str, str]:
    """Parse a leading '---\\n...\\n---\\n' block into a flat key/value dict.

    Only supports simple 'key: value' lines (no nested structures) —
    sufficient for this artefact type's flat schema, deliberately not a
    full YAML parser (no third-party dependency, smaller attack/parse
    surface).
    """
    m = _FRONT_MATTER_RE.match(text)
    if not m:
        return {}
    fields: dict[str, str] = {}
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        fm = _FIELD_RE.match(line)
        if fm:
            fields[fm.group(1)] = fm.group(2).strip()
    return fields


def _extract_claimed_hash(text: str) -> str | None:
    """Find a claimed SHA-256 near a 'RECEIPT: SHA-256' marker, else the
    first bare 64-hex-char token in the document (covers both this
    session's WM_03 trailing-receipt convention and a front-matter
    'self_hash:' field)."""
    front_matter = parse_front_matter(text)
    if "self_hash" in front_matter:
        m = _HASH_VALUE_RE.search(front_matter["self_hash"])
        if m:
            return m.group(1)

    receipt_match = _RECEIPT_LINE_RE.search(text)
    if receipt_match:
        tail = text[receipt_match.end():]
        m = _HASH_VALUE_RE.search(tail)
        if m:
            return m.group(1)
    return None


def check_self_hash(text: str) -> tuple[bool, str | None]:
    """Try both self-hash boundary conventions observed cross-lane this
    session, each as a direct substring slice (no rstrip/re-add
    normalization — that heuristic under/over-trims real newlines and
    was caught producing false negatives during this module's own test
    development):

      (a) 'with_trailing_separator' — content up to (not including) the
          'RECEIPT: SHA-256' line itself, i.e. including the '---'
          separator line immediately before it. This lane's own filing
          convention (matches `awk '/^RECEIPT: SHA-256/{exit}{print}'`).
      (b) 'without_trailing_separator' — content up to (not including)
          the blank-line + '---' separator that precedes the RECEIPT
          line. Confirmed by direct reproduction against
          CLAUDE_COWORK_REPLY_TO_SERVICE_CATALOGUE_LIFECYCLE_PROPOSAL_v0.1.md
          this session (claimed self-hash `806c57fb...` only reproduces
          under this boundary).

    Returns (matched, convention_name). Never raises on a missing/absent
    claimed hash — that is reported by the caller as its own finding.
    """
    claimed = _extract_claimed_hash(text)
    if claimed is None:
        return False, None

    idx_receipt = text.find("RECEIPT: SHA-256")
    if idx_receipt == -1:
        # front-matter self_hash with no RECEIPT block: nothing to hash
        # against by this tool's rules — caller treats as unverifiable.
        return False, None

    with_sep = text[:idx_receipt]
    if hashlib.sha256(with_sep.encode()).hexdigest() == claimed:
        return True, "with_trailing_separator"

    marker = "\n---\nRECEIPT: SHA-256"
    idx_marker = text.find(marker)
    if idx_marker != -1:
        without_sep = text[:idx_marker]
        if hashlib.sha256(without_sep.encode()).hexdigest() == claimed:
            return True, "without_trailing_separator"

    return False, None


def validate(text: str) -> ValidationResult:
    result = ValidationResult(ok=True)
    front_matter = parse_front_matter(text)
    result.front_matter = front_matter

    if not front_matter:
        result.ok = False
        result.errors.append("No parseable '---' front matter block found.")
        return result

    for required in REQUIRED_FRONT_MATTER_FIELDS:
        if required not in front_matter or not front_matter[required]:
            result.ok = False
            result.errors.append(f"Missing required field: {required!r}")

    status = front_matter.get("status")
    if status is not None and status not in ALLOWED_STATUS:
        result.ok = False
        result.errors.append(
            f"status {status!r} not in allowed vocabulary {sorted(ALLOWED_STATUS)}"
        )

    origin_state = front_matter.get("origin_identity_state")
    if origin_state is not None and origin_state not in ALLOWED_ORIGIN_IDENTITY_STATE:
        result.ok = False
        result.errors.append(
            f"origin_identity_state {origin_state!r} not in allowed vocabulary "
            f"{sorted(ALLOWED_ORIGIN_IDENTITY_STATE)}"
        )

    if origin_state == "DECLARED":
        result.warnings.append(
            "origin_identity_state is DECLARED (self-asserted only) — "
            "per this session's own finding, verify roster match before trusting."
        )

    claimed_hash = _extract_claimed_hash(text)
    if claimed_hash is None:
        result.warnings.append(
            "No self-hash found (neither a 'RECEIPT: SHA-256' block nor a "
            "front-matter 'self_hash' field) — artefact is not self-verifiable."
        )
    else:
        matched, convention = check_self_hash(text)
        if matched:
            result.hash_match_convention = convention
        else:
            result.ok = False
            result.errors.append(
                f"Claimed self-hash {claimed_hash!r} does not match either known "
                "boundary convention (with/without trailing '---' separator)."
            )

    return result


def validate_file(path: str) -> ValidationResult:
    with open(path, encoding="utf-8") as fh:
        return validate(fh.read())
