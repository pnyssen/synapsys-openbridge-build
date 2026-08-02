"""
Validates a TARGET_MOUNT_RECEIPT_<RUN_ID>.json produced by a real,
credentialed execution of the D007 transport pilot against the
schema in schemas/target_mount_receipt_schema.json, plus business
rules that JSON Schema alone cannot express (received values must
equal expected values).

This module does not execute the pilot, does not fabricate a receipt,
and returns FAIL for any receipt it has not been given.
"""
from __future__ import annotations

import json
import pathlib

import jsonschema

_SCHEMA_PATH = pathlib.Path(__file__).resolve().parent.parent / "schemas" / "target_mount_receipt_schema.json"


class ReceiptValidationError(ValueError):
    pass


def load_schema() -> dict:
    return json.loads(_SCHEMA_PATH.read_text())


def validate_receipt(receipt: dict, *, schema: dict | None = None) -> None:
    """Raises ReceiptValidationError on any schema or business-rule
    violation. Returns None (silently) on a well-formed receipt.

    A well-formed receipt is NOT proof a live execution occurred — it is
    only proof the receipt's own internal fields are consistent and
    complete. Provenance (was this actually returned by the real
    endpoint) is outside this function's scope by design.
    """
    schema = schema or load_schema()
    try:
        jsonschema.validate(instance=receipt, schema=schema)
    except jsonschema.exceptions.ValidationError as exc:
        raise ReceiptValidationError(f"SCHEMA_VIOLATION: {exc.message}") from exc

    if receipt["received_bytes"] != receipt["expected_bytes"]:
        raise ReceiptValidationError(
            f"BYTE_MISMATCH: expected {receipt['expected_bytes']}, received {receipt['received_bytes']}"
        )
    if receipt["received_sha256"] != receipt["expected_sha256"]:
        raise ReceiptValidationError(
            f"SHA256_MISMATCH: expected {receipt['expected_sha256']}, received {receipt['received_sha256']}"
        )
    if receipt["extraction_result"] != "PASS":
        raise ReceiptValidationError(f"EXTRACTION_NOT_PASS: {receipt['extraction_result']}")
    if not receipt["start_here_read"]:
        raise ReceiptValidationError("START_HERE_NOT_READ")
    if not all(body.get("read") for body in receipt["evidence_bodies_read"]):
        unread = [b["name"] for b in receipt["evidence_bodies_read"] if not b.get("read")]
        raise ReceiptValidationError(f"EVIDENCE_BODIES_UNREAD: {unread}")
    if receipt["secret_scan_result"] != "CLEAN":
        raise ReceiptValidationError(f"SECRET_SCAN_NOT_CLEAN: {receipt['secret_scan_result']}")
    if receipt["graph_build_gate_state"] != "PASSED":
        raise ReceiptValidationError(f"GRAPH_BUILD_GATE_NOT_PASSED: {receipt['graph_build_gate_state']}")


__all__ = ["validate_receipt", "load_schema", "ReceiptValidationError"]
