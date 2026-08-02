"""
Reusable manifest-completeness / byte-and-SHA-256-parity checker.

Takes a manifest as a list of (path, expected_bytes, expected_sha256)
rows and an "actual" lookup — either a dict of {path: (bytes, sha256)}
(e.g. built from sp_list results) or a real filesystem root — and
reports every row that is missing, stale (byte or hash mismatch), or
extra (present on disk/live but absent from the manifest).

Does not fetch anything itself and does not know about SharePoint,
Working Memory, or any network call — callers supply the "actual"
side, so this module stays fully offline and unit-testable.
"""
from __future__ import annotations

import csv
import hashlib
import io
import pathlib
from dataclasses import dataclass, field


@dataclass
class ManifestRow:
    path: str
    bytes: int
    sha256: str


@dataclass
class ParityFinding:
    path: str
    kind: str  # MISSING_ON_DISK | BYTE_MISMATCH | HASH_MISMATCH | EXTRA_NOT_IN_MANIFEST
    manifest_bytes: int | None = None
    actual_bytes: int | None = None
    manifest_sha256: str | None = None
    actual_sha256: str | None = None

    def as_dict(self) -> dict:
        return {
            "path": self.path, "kind": self.kind,
            "manifest_bytes": self.manifest_bytes, "actual_bytes": self.actual_bytes,
            "manifest_sha256": self.manifest_sha256, "actual_sha256": self.actual_sha256,
        }


def parse_manifest_csv(text: str) -> list[ManifestRow]:
    """Parses a `path,bytes,sha256` or `path,sha256,bytes` header CSV.
    Column order is detected from the header row so either convention
    used across this Work Object's manifests is accepted."""
    reader = csv.reader(io.StringIO(text))
    header = next(reader)
    header_lower = [h.strip().lower() for h in header]
    idx_path = header_lower.index("path")
    idx_bytes = header_lower.index("bytes")
    idx_sha = header_lower.index("sha256")
    rows = []
    for record in reader:
        if not record:
            continue
        rows.append(ManifestRow(
            path=record[idx_path].strip(),
            bytes=int(record[idx_bytes].strip()),
            sha256=record[idx_sha].strip(),
        ))
    return rows


def check_parity(manifest_rows: list[ManifestRow], actual: dict) -> list[ParityFinding]:
    """actual: {path: (bytes:int, sha256:str|None)} — sha256 may be None
    when only a byte count is available (e.g. from a directory listing
    without a hash), in which case only the byte check runs for that row."""
    findings: list[ParityFinding] = []
    manifest_paths = {r.path for r in manifest_rows}

    for row in manifest_rows:
        if row.path not in actual:
            findings.append(ParityFinding(path=row.path, kind="MISSING_ON_DISK",
                                           manifest_bytes=row.bytes, manifest_sha256=row.sha256))
            continue
        actual_bytes, actual_sha256 = actual[row.path]
        if actual_bytes != row.bytes:
            findings.append(ParityFinding(
                path=row.path, kind="BYTE_MISMATCH",
                manifest_bytes=row.bytes, actual_bytes=actual_bytes,
                manifest_sha256=row.sha256, actual_sha256=actual_sha256,
            ))
            continue  # a byte mismatch already proves staleness; do not also report a hash mismatch for the same row
        if actual_sha256 is not None and actual_sha256 != row.sha256:
            findings.append(ParityFinding(
                path=row.path, kind="HASH_MISMATCH",
                manifest_bytes=row.bytes, actual_bytes=actual_bytes,
                manifest_sha256=row.sha256, actual_sha256=actual_sha256,
            ))

    for path in actual:
        if path not in manifest_paths:
            actual_bytes, actual_sha256 = actual[path]
            findings.append(ParityFinding(path=path, kind="EXTRA_NOT_IN_MANIFEST",
                                           actual_bytes=actual_bytes, actual_sha256=actual_sha256))

    return findings


def hash_local_tree(root: pathlib.Path, *, exclude_names: frozenset = frozenset()) -> dict:
    """Convenience for the common case: build the 'actual' dict from a
    real local directory tree. Not used against Working Memory (which
    has no filesystem this process can walk) — only for local git-tree
    self-checks."""
    actual = {}
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.name not in exclude_names and "__pycache__" not in p.parts:
            data = p.read_bytes()
            actual[str(p.relative_to(root))] = (len(data), hashlib.sha256(data).hexdigest())
    return actual


__all__ = ["ManifestRow", "ParityFinding", "parse_manifest_csv", "check_parity", "hash_local_tree"]
