"""Client-side pre-write validation for the SynapSys SharePoint MCP.

The remote SynapSys_SharePoint MCP server (confirmed v12 baseline, ACR digest
sha256:3d3acd3bd1f4392533757d476222526477d6969343e8efe3b14265aedc63f187,
deployed as synapsys-spmcp-dev--0000019) enforces the Working Memory filename
contract server-side and rejects non-conforming names before persisting —
confirmed live 2026-08-11 via a deliberately rejected sp_write call, whose
error text is the literal source of FILENAME_PATTERN below. This module lets
a caller check that same contract locally before spending a round trip on
sp_write, which matters for unattended/batch filing runs. It performs no
network I/O and never silently renames a file — non-conforming names are
reported, not corrected.

This repo has no source access to the SharePoint MCP server itself; this
module is a client-side convenience layer only, not a patch to that server.
"""

import re

FILENAME_PATTERN = re.compile(
    r"^(?P<date>\d{8})--"
    r"(?P<lane>[a-z0-9]+(?:-[a-z0-9]+)*)--"
    r"(?P<artifact_type>[a-z0-9]+(?:-[a-z0-9]+)*)--"
    r"(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)--"
    r"v(?P<major>\d+)-(?P<minor>\d+)"
    r"\.(?P<ext>[a-z0-9]+)$"
)

_WORD = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


def validate_filename(filename):
    """Check filename against the server-enforced Working Memory naming
    contract. Returns (True, None) if compliant, else (False, reason).
    Never renames or mutates the input.
    """
    if FILENAME_PATTERN.fullmatch(filename):
        return True, None
    return False, (
        "filename must match YYYYMMDD--lane--artifact-type--searchable-slug--"
        "vMAJOR-MINOR.ext (lowercase ASCII)"
    )


def normalize_filename(date, lane, artifact_type, slug, major, minor, ext="md"):
    """Deterministically build a compliant Working Memory filename.

    Every field is validated; invalid input raises ValueError rather than
    being silently corrected — this function never auto-renames.
    """
    if not re.fullmatch(r"\d{8}", date):
        raise ValueError(f"date must be YYYYMMDD: {date!r}")
    for field_name, value in (
        ("lane", lane),
        ("artifact_type", artifact_type),
        ("slug", slug),
    ):
        if not _WORD.fullmatch(value):
            raise ValueError(
                f"{field_name} must be lowercase ASCII words joined by single "
                f"hyphens: {value!r}"
            )
    if not re.fullmatch(r"\d+", str(major)) or not re.fullmatch(r"\d+", str(minor)):
        raise ValueError(f"major/minor must be non-negative integers: {major!r}.{minor!r}")
    if not re.fullmatch(r"[a-z0-9]+", ext):
        raise ValueError(f"ext must be lowercase ASCII: {ext!r}")

    filename = f"{date}--{lane}--{artifact_type}--{slug}--v{major}-{minor}.{ext}"
    ok, reason = validate_filename(filename)
    if not ok:
        raise ValueError(f"normalize_filename produced a non-conforming name: {reason}")
    return filename


def preflight_write(path, content):
    """Read-only pre-write check: filename contract + path safety only.

    Performs no I/O and never calls the SharePoint MCP. Mirrors the
    server's confirmed pre-write rejection so batch/overnight callers can
    fail fast locally instead of spending a round trip on a write the
    server will reject anyway.
    """
    errors = []
    if not path:
        errors.append("path must not be empty")
        return {"ok": False, "errors": errors}

    if path.startswith("/") or ".." in path.split("/"):
        errors.append(
            "path must be relative to the Working Memory root and must not "
            "contain '..'"
        )

    filename = path.rsplit("/", 1)[-1]
    ok, reason = validate_filename(filename)
    if not ok:
        errors.append(reason)

    if content is None:
        errors.append("content must not be None")

    return {"ok": not errors, "errors": errors}
