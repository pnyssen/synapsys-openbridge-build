"""
Deterministic, offline tests only. No network call is made anywhere in
this file. Every fixture used is either a synthetic value or an
explicitly labelled placeholder — never the real Stream A bundle
content and never a real credential.
"""
from __future__ import annotations

import hashlib
import io
import json
import pathlib
import unittest
import zipfile
from datetime import datetime, timezone

import jsonschema

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

from mock.mock_transport_gateway import (
    AuthorityBoundaryError,
    BinaryIntegrityError,
    DuplicateMountError,
    ManifestExpiredError,
    NonceRegistry,
    ReplayError,
    TransportValidationError,
    ZipSafetyError,
    check_existing_mount,
    safe_extract_members,
    validate_authority,
    validate_manifest_expiry,
    validate_request,
    verify_binary,
)
from validate.receipt_validator import ReceiptValidationError, load_schema, validate_receipt

VALID_REQUEST = {
    "transport_request_id": "TR-TEST-01",
    "run_id": "RUN-TEST-01",
    "work_object_id": "WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001",
    "target_lane": "codex",
    "nonce": "NONCE-TEST-01",
}


class RequestValidationTests(unittest.TestCase):
    def test_valid_request_passes(self):
        validate_request(dict(VALID_REQUEST))  # must not raise

    def test_missing_nonce_fails(self):
        bad = {k: v for k, v in VALID_REQUEST.items() if k != "nonce"}
        with self.assertRaises(TransportValidationError):
            validate_request(bad)

    def test_forbidden_source_path_override_fails(self):
        bad = dict(VALID_REQUEST, source_path="Obsidian/whatever.zip")
        with self.assertRaises(TransportValidationError):
            validate_request(bad)

    def test_forbidden_expected_sha256_override_fails(self):
        bad = dict(VALID_REQUEST, expected_sha256="0" * 64)
        with self.assertRaises(TransportValidationError):
            validate_request(bad)

    def test_wrong_target_lane_fails(self):
        bad = dict(VALID_REQUEST, target_lane="claude_code")
        with self.assertRaises(TransportValidationError):
            validate_request(bad)

    def test_schema_matches_gateway_rules(self):
        schema = json.loads((REPO_ROOT / "schemas" / "transport_request_schema.json").read_text())
        jsonschema.validate(instance=VALID_REQUEST, schema=schema)
        bad = dict(VALID_REQUEST, source_path="x")
        with self.assertRaises(jsonschema.exceptions.ValidationError):
            jsonschema.validate(instance=bad, schema=schema)


class ManifestExpiryTests(unittest.TestCase):
    def test_unexpired_manifest_passes(self):
        manifest = {"expires_at": "2026-08-02T14:00:00+10:00"}
        now = datetime(2026, 8, 2, 2, 0, 0, tzinfo=timezone.utc)  # 12:00 AEST, before 14:00 AEST
        validate_manifest_expiry(manifest, now=now)  # must not raise

    def test_expired_manifest_fails(self):
        manifest = {"expires_at": "2026-08-02T14:00:00+10:00"}
        now = datetime(2026, 8, 2, 5, 0, 0, tzinfo=timezone.utc)  # 15:00 AEST, after expiry
        with self.assertRaises(ManifestExpiredError):
            validate_manifest_expiry(manifest, now=now)


class AuthorityBoundaryTests(unittest.TestCase):
    def test_authority_with_all_phrases_passes(self):
        text = "Authority is limited to one inactive candidate build, one controlled delivery, and deactivation after."
        validate_authority(text)  # must not raise

    def test_authority_missing_phrase_fails(self):
        text = "Authority is limited to one inactive candidate build only."
        with self.assertRaises(AuthorityBoundaryError):
            validate_authority(text)


class ReplayAndNonceTests(unittest.TestCase):
    def test_first_use_passes(self):
        registry = NonceRegistry()
        registry.check_and_consume("NONCE-A")  # must not raise

    def test_reuse_fails(self):
        registry = NonceRegistry()
        registry.check_and_consume("NONCE-A")
        with self.assertRaises(ReplayError):
            registry.check_and_consume("NONCE-A")


class DuplicateMountTests(unittest.TestCase):
    def test_new_path_passes(self):
        check_existing_mount("mounts/RUN-A", existing_paths=set())  # must not raise

    def test_existing_path_fails(self):
        with self.assertRaises(DuplicateMountError):
            check_existing_mount("mounts/RUN-A", existing_paths={"mounts/RUN-A"})


class BinaryIntegrityTests(unittest.TestCase):
    def test_matching_binary_passes(self):
        data = b"synthetic test payload, not the real Stream A bundle"
        sha = hashlib.sha256(data).hexdigest()
        verify_binary(
            data, expected_sha256=sha, expected_bytes=len(data),
            expected_mime="application/zip", actual_mime="application/zip",
        )  # must not raise

    def test_byte_mismatch_fails(self):
        data = b"synthetic"
        sha = hashlib.sha256(data).hexdigest()
        with self.assertRaises(BinaryIntegrityError):
            verify_binary(
                data, expected_sha256=sha, expected_bytes=len(data) + 1,
                expected_mime="application/zip", actual_mime="application/zip",
            )

    def test_hash_mismatch_fails(self):
        data = b"synthetic"
        with self.assertRaises(BinaryIntegrityError):
            verify_binary(
                data, expected_sha256="0" * 64, expected_bytes=len(data),
                expected_mime="application/zip", actual_mime="application/zip",
            )

    def test_mime_mismatch_fails(self):
        data = b"synthetic"
        sha = hashlib.sha256(data).hexdigest()
        with self.assertRaises(BinaryIntegrityError):
            verify_binary(
                data, expected_sha256=sha, expected_bytes=len(data),
                expected_mime="application/zip", actual_mime="text/plain",
            )


def _build_synthetic_zip(member_names_and_bodies: list) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, body in member_names_and_bodies:
            zf.writestr(name, body)
    return buf.getvalue()


SYNTHETIC_FIVE_MEMBERS = [
    ("START_HERE.md", b"SYNTHETIC TEST FIXTURE - not the real Stream A bundle. Read order: A, B, C, D."),
    ("EVIDENCE_A.md", b"synthetic evidence body A"),
    ("EVIDENCE_B.md", b"synthetic evidence body B"),
    ("EVIDENCE_C.md", b"synthetic evidence body C"),
    ("EVIDENCE_D.md", b"synthetic evidence body D"),
]


class ZipSafetyTests(unittest.TestCase):
    def test_valid_five_member_zip_passes(self):
        z = _build_synthetic_zip(SYNTHETIC_FIVE_MEMBERS)
        names = safe_extract_members(z, expected_member_count=5)
        self.assertEqual(len(names), 5)
        self.assertIn("START_HERE.md", names)

    def test_path_traversal_member_fails(self):
        members = SYNTHETIC_FIVE_MEMBERS[:4] + [("../evil.txt", b"x")]
        z = _build_synthetic_zip(members)
        with self.assertRaises(ZipSafetyError):
            safe_extract_members(z, expected_member_count=5)

    def test_absolute_path_member_fails(self):
        members = SYNTHETIC_FIVE_MEMBERS[:4] + [("/etc/passwd", b"x")]
        z = _build_synthetic_zip(members)
        with self.assertRaises(ZipSafetyError):
            safe_extract_members(z, expected_member_count=5)

    def test_duplicate_member_names_fail(self):
        # zipfile allows writing duplicate names into the archive; the
        # safety check must catch it even though the ZIP itself is well-formed.
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("START_HERE.md", b"one")
            zf.writestr("START_HERE.md", b"two")
            zf.writestr("EVIDENCE_A.md", b"a")
            zf.writestr("EVIDENCE_B.md", b"b")
            zf.writestr("EVIDENCE_C.md", b"c")
        with self.assertRaises(ZipSafetyError):
            safe_extract_members(buf.getvalue(), expected_member_count=5)

    def test_excessive_expansion_member_fails(self):
        members = SYNTHETIC_FIVE_MEMBERS[:4] + [("EVIDENCE_HUGE.md", b"x" * 2_000_000)]
        z = _build_synthetic_zip(members)
        with self.assertRaises(ZipSafetyError):
            safe_extract_members(z, expected_member_count=5, max_member_bytes=1_000_000)

    def test_unexpected_member_count_fails_too_few(self):
        z = _build_synthetic_zip(SYNTHETIC_FIVE_MEMBERS[:4])
        with self.assertRaises(ZipSafetyError):
            safe_extract_members(z, expected_member_count=5)

    def test_unexpected_member_count_fails_too_many(self):
        members = SYNTHETIC_FIVE_MEMBERS + [("EVIDENCE_EXTRA.md", b"extra")]
        z = _build_synthetic_zip(members)
        with self.assertRaises(ZipSafetyError):
            safe_extract_members(z, expected_member_count=5)

    def test_not_a_zip_fails(self):
        with self.assertRaises(ZipSafetyError):
            safe_extract_members(b"this is not a zip file", expected_member_count=5)


def _valid_receipt() -> dict:
    return {
        "endpoint": "https://n8n.srv1536619.hstgr.cloud/webhook/navigator-wm-codex-stream-a-pilot-20260802",
        "transport_request_id": "TR-WM-CODEX-A-20260802-01",
        "run_id": "RUN-WM-CODEX-A-20260802-01",
        "target_runtime_identity": "<TARGET_RUNTIME_IDENTITY>",
        "source_path": (
            "05_AI_RETURNS_HASHED/WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001/"
            "WAVE_INTEGRATED_NAVIGATOR_MVP_20260802/NAVIGATOR_STREAM_A_HUB_EVIDENCE_BUNDLE_v0.1.zip"
        ),
        "expected_bytes": 8565,
        "received_bytes": 8565,
        "expected_sha256": "df535de7985e0d924008cf157241a060e51f28a30d5050231a6a3254a6d1c81f",
        "received_sha256": "df535de7985e0d924008cf157241a060e51f28a30d5050231a6a3254a6d1c81f",
        "integrity_headers": {"x-transport-request-id": "TR-WM-CODEX-A-20260802-01"},
        "immutable_mount_path": "mounts/RUN-WM-CODEX-A-20260802-01_df535de7/",
        "extraction_result": "PASS",
        "members": [
            {"name": "START_HERE.md", "bytes": 100, "sha256": "0" * 64},
            {"name": "EVIDENCE_A.md", "bytes": 100, "sha256": "1" * 64},
            {"name": "EVIDENCE_B.md", "bytes": 100, "sha256": "2" * 64},
            {"name": "EVIDENCE_C.md", "bytes": 100, "sha256": "3" * 64},
            {"name": "EVIDENCE_D.md", "bytes": 100, "sha256": "4" * 64},
        ],
        "start_here_read": True,
        "evidence_bodies_read": [
            {"name": "EVIDENCE_A.md", "read": True},
            {"name": "EVIDENCE_B.md", "read": True},
            {"name": "EVIDENCE_C.md", "read": True},
            {"name": "EVIDENCE_D.md", "read": True},
        ],
        "secret_scan_result": "CLEAN",
        "graph_build_gate_state": "PASSED",
        "authority": "Read-only projection of Stream A's own returned graph",
        "ppv": "Potential",
        "replay_validity": "PRESERVED",
    }


class ReceiptValidatorTests(unittest.TestCase):
    def test_schema_loads(self):
        schema = load_schema()
        self.assertEqual(schema["title"].startswith("TARGET_MOUNT_RECEIPT"), True)

    def test_valid_receipt_passes(self):
        validate_receipt(_valid_receipt())  # must not raise

    def test_missing_field_fails(self):
        bad = _valid_receipt()
        del bad["secret_scan_result"]
        with self.assertRaises(ReceiptValidationError):
            validate_receipt(bad)

    def test_byte_mismatch_fails(self):
        bad = _valid_receipt()
        bad["received_bytes"] = 9999
        with self.assertRaises(ReceiptValidationError):
            validate_receipt(bad)

    def test_hash_mismatch_fails(self):
        bad = _valid_receipt()
        bad["received_sha256"] = "f" * 64
        with self.assertRaises(ReceiptValidationError):
            validate_receipt(bad)

    def test_extraction_not_pass_fails(self):
        bad = _valid_receipt()
        bad["extraction_result"] = "FAIL"
        with self.assertRaises(ReceiptValidationError):
            validate_receipt(bad)

    def test_start_here_unread_fails(self):
        bad = _valid_receipt()
        bad["start_here_read"] = False
        with self.assertRaises(ReceiptValidationError):
            validate_receipt(bad)

    def test_evidence_body_unread_fails(self):
        bad = _valid_receipt()
        bad["evidence_bodies_read"][1]["read"] = False
        with self.assertRaises(ReceiptValidationError):
            validate_receipt(bad)

    def test_secret_scan_flagged_fails(self):
        bad = _valid_receipt()
        bad["secret_scan_result"] = "FLAGGED"
        with self.assertRaises(ReceiptValidationError):
            validate_receipt(bad)

    def test_graph_gate_not_passed_fails(self):
        bad = _valid_receipt()
        bad["graph_build_gate_state"] = "BLOCKED"
        with self.assertRaises(ReceiptValidationError):
            validate_receipt(bad)


if __name__ == "__main__":
    unittest.main()
