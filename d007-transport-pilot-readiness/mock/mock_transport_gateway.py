"""
LOCAL MOCK — NOT THE REAL N8N ENDPOINT.

This module makes no network call, holds no credential, and does not
claim to be, replace, deploy, or have executed
https://n8n.srv1536619.hstgr.cloud/webhook/navigator-wm-codex-stream-a-pilot-20260802.

It is an offline re-implementation of the validation RULES described in
the real, already-provisioned N8N workflow `SDGlH8QqeHpIIErz`
("Navigator WM Binary Delivery Gateway — Stream A Pilot"), sourced from
two files read live via sp_read this session:

- D007_WM_TO_CODEX_TRANSPORT_WORKFLOW_EXPORT_SUMMARY_v0.1.json
  (node sequence, fixed_contract, credential references)
- D007_WM_TO_CODEX_TRANSPORT_STATIC_TEST_REPORT_v0.1.md
  (the specific PASS rows this module's functions correspond to)

Its only purpose is to let the request/response/receipt CONTRACT be
exercised deterministically, offline, before a credentialed Codex
runtime uses the real endpoint. A function in this file passing proves
nothing about the real N8N workflow's behaviour — it only proves this
module's own re-implementation of the documented rules is internally
consistent.
"""
from __future__ import annotations

import io
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone


class TransportValidationError(ValueError):
    """Request shape or forbidden-override violation (mirrors the real
    workflow's 'Normalize and Validate Request' / 'IF Request Valid' /
    'Respond Fail-Closed' nodes)."""


class ManifestExpiredError(ValueError):
    """Mirrors the real workflow's 'Validate Manifest and Expiry' node."""


class AuthorityBoundaryError(ValueError):
    """Mirrors the real workflow's 'Validate Authority and Boundary' node."""


class ReplayError(ValueError):
    """Mirrors the real workflow's 'Replay and Nonce Gate' node."""


class DuplicateMountError(ValueError):
    """Mirrors the real workflow's 'Inspect Existing Source Receipt'
    no-overwrite check, and the target-side 'reject an existing mount
    path' control named in CODEX_TARGET_PREFLIGHT_AND_LIVE_MOUNT_DISPATCH_v0.1.md."""


class BinaryIntegrityError(ValueError):
    """Mirrors the real workflow's 'Validate Binary and Build Source
    Receipt' node (SHA-256 / bytes / MIME gates)."""


class ZipSafetyError(ValueError):
    """Mirrors the target-side extraction-safety controls named in the
    dispatch: path traversal, unsafe members, duplicate members,
    excessive expansion, unexpected member count."""


# The real workflow's own fixed contract, restated here as constants for
# the mock's default expectations — NOT a live credential or endpoint.
FORBIDDEN_CALLER_OVERRIDE_FIELDS = (
    "source_path", "expected_sha256", "expected_bytes",
    "expected_mime", "authority",
)
REQUIRED_REQUEST_FIELDS = (
    "transport_request_id", "run_id", "work_object_id", "target_lane", "nonce",
)


def validate_request(payload: dict, *, allowed_target_lane: str = "codex") -> None:
    """Mirrors 'Caller cannot override source path/hash/bytes/MIME/authority'
    and the required-field gate — both PASS rows in the static test report."""
    if not isinstance(payload, dict):
        raise TransportValidationError("REQUEST_NOT_AN_OBJECT")
    missing = [f for f in REQUIRED_REQUEST_FIELDS if f not in payload]
    if missing:
        raise TransportValidationError(f"MISSING_REQUIRED_FIELDS: {missing}")
    overridden = [f for f in FORBIDDEN_CALLER_OVERRIDE_FIELDS if f in payload]
    if overridden:
        raise TransportValidationError(f"FORBIDDEN_CALLER_OVERRIDE: {overridden}")
    if payload["target_lane"] != allowed_target_lane:
        raise TransportValidationError(
            f"WRONG_TARGET_LANE: expected {allowed_target_lane!r}, got {payload['target_lane']!r}"
        )


def validate_manifest_expiry(manifest: dict, *, now: datetime) -> None:
    """Mirrors 'Expired manifest rejected — PASS by inspection'."""
    expires_at = datetime.fromisoformat(manifest["expires_at"])
    if now >= expires_at:
        raise ManifestExpiredError(f"MANIFEST_EXPIRED: expires_at={expires_at.isoformat()}, now={now.isoformat()}")


REQUIRED_AUTHORITY_BOUNDARY_PHRASES = (
    "one inactive candidate build",
    "one controlled delivery",
    "deactivation",
)


def validate_authority(authority_text: str, *, required_phrases=REQUIRED_AUTHORITY_BOUNDARY_PHRASES) -> None:
    """Mirrors 'Validate Authority and Boundary' — the real workflow gates
    on exact authority body/hash plus boundary phrases, per the static
    test report's 'fixed authority SHA-256 ... and phrase gates' row."""
    missing_phrases = [p for p in required_phrases if p not in authority_text]
    if missing_phrases:
        raise AuthorityBoundaryError(f"AUTHORITY_MISSING_BOUNDARY_PHRASES: {missing_phrases}")


@dataclass
class NonceRegistry:
    """Mirrors 'Replay and Nonce Gate' plus 'Duplicate run/source receipt
    rejected — PASS by inspection'."""
    _seen: set = field(default_factory=set)

    def check_and_consume(self, nonce: str) -> None:
        if nonce in self._seen:
            raise ReplayError(f"NONCE_REPLAYED: {nonce}")
        self._seen.add(nonce)


def check_existing_mount(path: str, *, existing_paths: set) -> None:
    """Mirrors the target-side 'reject an existing mount path' control."""
    if path in existing_paths:
        raise DuplicateMountError(f"MOUNT_PATH_ALREADY_EXISTS: {path}")


def verify_binary(data: bytes, *, expected_sha256: str, expected_bytes: int, expected_mime: str,
                   actual_mime: str) -> None:
    """Mirrors 'Binary SHA-256/bytes/MIME checked — PASS by inspection'."""
    import hashlib
    actual_sha256 = hashlib.sha256(data).hexdigest()
    if len(data) != expected_bytes:
        raise BinaryIntegrityError(f"BYTE_COUNT_MISMATCH: expected {expected_bytes}, got {len(data)}")
    if actual_sha256 != expected_sha256:
        raise BinaryIntegrityError(f"SHA256_MISMATCH: expected {expected_sha256}, got {actual_sha256}")
    if actual_mime != expected_mime:
        raise BinaryIntegrityError(f"MIME_MISMATCH: expected {expected_mime}, got {actual_mime}")


def safe_extract_members(zip_bytes: bytes, *, expected_member_count: int,
                          max_member_bytes: int = 1_000_000) -> list:
    """Mirrors the dispatch's 'Reject path traversal, unsafe members,
    excessive expansion and unexpected member count' target control.

    Returns the list of member names on success. Raises ZipSafetyError
    with a specific reason otherwise. Never writes to disk.
    """
    try:
        zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
    except zipfile.BadZipFile as exc:
        raise ZipSafetyError(f"NOT_A_VALID_ZIP: {exc}") from exc

    infos = zf.infolist()
    names = [i.filename for i in infos]

    if len(names) != len(set(names)):
        raise ZipSafetyError("DUPLICATE_MEMBER_NAMES")

    for info in infos:
        name = info.filename
        if name.startswith("/") or name.startswith("\\"):
            raise ZipSafetyError(f"ABSOLUTE_PATH_MEMBER: {name}")
        if ".." in name.replace("\\", "/").split("/"):
            raise ZipSafetyError(f"PATH_TRAVERSAL_MEMBER: {name}")
        if info.file_size > max_member_bytes:
            raise ZipSafetyError(f"EXCESSIVE_EXPANSION_MEMBER: {name} declares {info.file_size} bytes")

    if len(names) != expected_member_count:
        raise ZipSafetyError(f"UNEXPECTED_MEMBER_COUNT: expected {expected_member_count}, got {len(names)}")

    return names


__all__ = [
    "TransportValidationError", "ManifestExpiredError", "AuthorityBoundaryError",
    "ReplayError", "DuplicateMountError", "BinaryIntegrityError", "ZipSafetyError",
    "validate_request", "validate_manifest_expiry", "validate_authority",
    "NonceRegistry", "check_existing_mount", "verify_binary", "safe_extract_members",
    "FORBIDDEN_CALLER_OVERRIDE_FIELDS", "REQUIRED_REQUEST_FIELDS",
]
