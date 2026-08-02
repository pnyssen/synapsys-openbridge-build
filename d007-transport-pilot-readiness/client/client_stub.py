"""
Candidate client stub for the real, already-provisioned D007 transport
pilot endpoint. THIS MODULE NEVER MAKES A NETWORK CALL and never reads,
holds, or invents a real credential value. It only shows the shape of
the authenticated request that a credentialed runtime (Codex, or a
Steward acting manually) would send.

Placeholders used throughout (never replaced with realistic-looking
fabricated values, per this task's explicit prohibition):

    <STREAM_A_ENDPOINT>
    <STREAM_A_AUTH_HEADER>
    <STREAM_A_CREDENTIAL>
    <TRANSPORT_REQUEST_ID>
    <RUN_ID>
    <NONCE>
    <EXPIRY_UTC>

The real, currently-active values for the endpoint URL and request body
(which are not secrets — they are meant to be handed to the executing
runtime) are recorded separately in MANUAL_HANDOFF_PACKET_v0.1.md,
sourced from the already-filed CODEX_TARGET_PREFLIGHT_AND_LIVE_MOUNT_DISPATCH_v0.1.md
(SHA-256 cc8fe34620bc51a634639fc5a34ced35ba543c8174ef4ec5ea1074b1930e2b0b).
Only the credential VALUE is a placeholder here — never invented.
"""
from __future__ import annotations

import json


def build_request_body(*, transport_request_id: str, run_id: str, work_object_id: str, nonce: str) -> dict:
    """Builds the exact request body shape the real workflow accepts.
    Caller-side helper only — does not send anything."""
    return {
        "transport_request_id": transport_request_id,
        "run_id": run_id,
        "work_object_id": work_object_id,
        "target_lane": "codex",
        "nonce": nonce,
    }


def build_placeholder_headers() -> dict:
    """Never a real credential value — always the literal placeholder
    string. A real runtime substitutes its own environment-bound value
    at call time; this function is not that runtime."""
    return {
        "<STREAM_A_AUTH_HEADER>": "<STREAM_A_CREDENTIAL>",
        "Content-Type": "application/json",
    }


def build_candidate_curl_command(request_body: dict) -> str:
    """Produces a copy-ready curl command using explicit placeholders
    only, per this task's 'Permitted tasks' list. Never executed by
    this module or this session."""
    body_json = json.dumps(request_body, separators=(",", ": "))
    return (
        "curl -sS -X POST '<STREAM_A_ENDPOINT>' "
        "-H '<STREAM_A_AUTH_HEADER>: <STREAM_A_CREDENTIAL>' "
        "-H 'Content-Type: application/json' "
        f"-d '{body_json}' "
        "-o TARGET_MOUNT_RECEIPT_<RUN_ID>.json"
    )


__all__ = ["build_request_body", "build_placeholder_headers", "build_candidate_curl_command"]
