"""Validate and convert Working Memory filenames/front matter to the
naming standard actually enforced by the SharePoint write server.

Codifies discipline this lane applied by hand, repeatedly, this session:
the server rejects any filename not matching
`YYYYMMDD--lane--artifact-type--slug--vMAJOR-MINOR.ext` (lowercase ASCII),
and rejects durable content missing required YAML front matter. Both
patterns below were derived empirically from real `sp_write` rejection
error text, not from a published spec this lane has seen -- if the server's
actual rule differs from this module's regex/field list, this module is
wrong, not the server, and should be corrected against a fresh rejection
message rather than assumed still accurate.

Pure functions only: no network calls, no `sp_write`/`sp_read` of any
kind. Callers pass in strings; this module classifies and transforms them.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional

FILENAME_PATTERN = re.compile(
    r"^(?P<date>\d{8})--"
    r"(?P<lane>[a-z0-9]+(?:-[a-z0-9]+)*)--"
    r"(?P<artifact_type>[a-z0-9]+(?:-[a-z0-9]+)*)--"
    r"(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)--"
    r"v(?P<major>\d+)-(?P<minor>\d+)"
    r"\.(?P<ext>[a-z0-9]+)$"
)

REQUIRED_FRONT_MATTER_FIELDS = (
    "title",
    "work_object_id",
    "created_date",
    "owner_lane",
    "ppv",
    "evidence_state",
    "aliases",
    "source_paths",
    "supersedes",
)


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    errors: List[str] = field(default_factory=list)


def validate_filename(name: str) -> ValidationResult:
    """True only if `name` matches the enforced pattern exactly."""
    if FILENAME_PATTERN.match(name):
        return ValidationResult(ok=True)
    errors = []
    if name != name.lower():
        errors.append("filename must be lowercase")
    if "--" not in name:
        errors.append("filename must use '--' to separate date/lane/artifact-type/slug/version")
    if not FILENAME_PATTERN.match(name):
        errors.append(
            "does not match YYYYMMDD--lane--artifact-type--slug--vMAJOR-MINOR.ext"
        )
    return ValidationResult(ok=False, errors=errors)


def validate_front_matter(fields_present: dict) -> ValidationResult:
    """fields_present: a dict of front-matter keys already parsed by the
    caller (this module does not parse YAML itself, to stay dependency-free
    and avoid disagreeing with whatever YAML parser the actual server
    uses)."""
    missing = [f for f in REQUIRED_FRONT_MATTER_FIELDS if f not in fields_present]
    if missing:
        return ValidationResult(
            ok=False,
            errors=[f"durable Working Memory content must begin with YAML front matter; missing: {', '.join(missing)}"],
        )
    return ValidationResult(ok=True)


_TOKEN_SPLIT = re.compile(r"[_\-\s]+")


def slug_from_legacy_name(legacy_name: str, drop_version: bool = True) -> str:
    """Extract a lowercase, dash-joined slug from a legacy filename,
    preserving its literal recognisable tokens (so a plain filename
    substring search for the old name still has a real chance of matching
    the new one) rather than semantically rewording them away.

    drop_version=True strips a trailing vN.NN / vN token and file
    extension, since those are handled separately by
    build_compliant_filename() below.
    """
    base = legacy_name
    for ext_sep in (".md", ".json", ".html", ".csv", ".py", ".zip"):
        if base.lower().endswith(ext_sep):
            base = base[: -len(ext_sep)]
            break
    tokens = [t for t in _TOKEN_SPLIT.split(base) if t]
    if drop_version:
        tokens = [t for t in tokens if not re.match(r"^v?\d+(\.\d+)?$", t, re.IGNORECASE)]
    return "-".join(t.lower() for t in tokens)


def extract_legacy_version(legacy_name: str) -> Optional[str]:
    """Finds a v<major>.<minor> (or v<major>) version token in a legacy
    name and returns it as 'major-minor' (zero-padded minor untouched --
    v0.195 stays 195, not renumbered), or None if no version token found."""
    m = re.search(r"v(\d+)\.(\d+)", legacy_name)
    if m:
        return f"{m.group(1)}-{m.group(2)}"
    m = re.search(r"v(\d+)(?!\.\d)", legacy_name)
    if m:
        return f"{m.group(1)}-0"
    return None


def build_compliant_filename(
    *,
    date_yyyymmdd: str,
    lane: str,
    artifact_type: str,
    legacy_name: str,
    ext: str = "md",
    fallback_minor: str = "0",
) -> str:
    """Builds a compliant filename from a legacy name, preserving its
    version number exactly (per the Wave Accelerator response's own
    guidance: 'the major.minor slot already accepts arbitrary numbers')
    and its literal recognisable tokens as the slug (not just a semantic
    aliases: entry) so plain filename search still has a chance of
    matching."""
    slug = slug_from_legacy_name(legacy_name)
    version = extract_legacy_version(legacy_name) or f"0-{fallback_minor}"
    name = f"{date_yyyymmdd}--{lane}--{artifact_type}--{slug}--v{version}.{ext}"
    result = validate_filename(name)
    if not result.ok:
        raise ValueError(f"Built filename still fails validation: {name} -- {result.errors}")
    return name
