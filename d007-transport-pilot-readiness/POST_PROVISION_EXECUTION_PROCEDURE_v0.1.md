# Post-Provision Execution Procedure v0.1

The exact sequence this lane (or any lane inheriting this package)
follows once a real endpoint, credential, and delivery mechanism are
evidenced — not before.

## 1. Verify endpoint identity

Compare the URL actually used against the one and only endpoint value
recorded in Working Memory evidence this session:
`https://n8n.srv1536619.hstgr.cloud/webhook/navigator-wm-codex-stream-a-pilot-20260802`
(from `NAVIGATOR_INTEGRATED_MVP_DISPATCH_MANIFEST_v1.1.md`'s "Active
endpoint" section and `D007_WM_TO_CODEX_TRANSPORT_PILOT_ACTIVATION_RECEIPT_v0.1.md`).
Any other host or path is out of scope for this pilot and must not be
called under this authority. Also verify the transport manifest has
not expired: `expires_at < now` must be false — use
`mock.mock_transport_gateway.validate_manifest_expiry()` against the
real manifest JSON before treating the endpoint as current.

## 2. Check credential presence without disclosure

Do not read, print, log, or echo the credential value at any point.
The only permitted check is a **boolean presence test** — e.g. "does
an environment variable / credential reference bound to
`H1-CGPT-N8N-Inbound-Auth` exist in this runtime, yes or no" — never a
value comparison, dump, or partial reveal. If the answer is no, stop
immediately and return `TOOL_BLOCKED_AUTH_CHANNEL`; do not attempt an
unauthenticated call as a fallback.

## 3. Dry run

There is no evidenced separate test endpoint (see
`PROVISIONING_CONTRACT_v0.1.md`, "test endpoint / production endpoint
distinction: UNRESOLVED") and `allowed_attempts: 1` means the live
endpoint cannot be rehearsed without consuming the pilot's one
permitted attempt. The closest available dry run is entirely local:
run this package's test suite
(`tests/test_offline_pilot_readiness.py`) to confirm the request body
you are about to send validates against `schemas/transport_request_schema.json`,
and that the receipt shape you expect back validates against
`schemas/target_mount_receipt_schema.json`, before spending the one
live attempt.

## 4. Distinguish success from failure

- **Success**: HTTP success status, all named integrity headers
  present, binary body received, and `mock.mock_transport_gateway.verify_binary()`
  confirms the received bytes match `expected_bytes` (`8565`) and
  `expected_sha256` (`df535de7985e0d924008cf157241a060e51f28a30d5050231a6a3254a6d1c81f`)
  exactly.
- **Failure (fail-closed, expected)**: `HTTP 403` (bad/missing
  credential — matches the already-proven negative-auth test) or `HTTP
  422` (invalid request shape). Either is a normal, evidenced failure
  mode, not an anomaly requiring escalation beyond reporting it.
- **Failure (anomalous, requires HOLD)**: any binary or partial binary
  returned on a non-success status; any response whose bytes/hash
  don't match after a reported HTTP success; any second successful
  response to a replayed nonce or request ID.

## 5. Required receipt

`TARGET_MOUNT_RECEIPT_<RUN_ID>.json` must be produced and must pass
`validate.receipt_validator.validate_receipt()` against
`schemas/target_mount_receipt_schema.json` before the pilot is reported
as `TARGET_MOUNT_PASS_LIVE_GRAPH_COMPLETE`. A receipt that fails
validation means the pilot is not complete, regardless of what the
narrative summary claims.

## 6. What constitutes STOP/HOLD

- Missing or unverifiable credential → `TOOL_BLOCKED_AUTH_CHANNEL`, stop before any request.
- Expired manifest → stop; do not fetch; report expiry, request re-provisioning.
- Any forbidden-field override accepted by the endpoint (i.e. the
  endpoint let a caller-supplied `source_path`/`expected_sha256`/etc.
  through) → STOP and escalate; this would mean the real workflow's
  "Normalize and Validate Request" gate is not behaving as statically
  tested.
- Byte count, SHA-256, or member count mismatch on the delivered
  binary → STOP before extraction; do not attempt to "fix" or
  re-derive a passing hash.
- Any ZIP safety violation (path traversal, absolute path, duplicate
  member, oversized member, wrong member count) → STOP before
  extraction; do not extract partially and continue.
- Secret scan flags anything → STOP before filing the receipt or
  regenerating the graph.
- Second attempt against a single-use, `allowed_attempts: 1` manifest
  → STOP; do not retry silently.

## 7. Which action remains manual

Delivering the executable dispatch text into the actual Codex Stream A
thread. No tool available to this lane, this session, or (per the
governing manifest's own "Exactly one controller action") to the Hub
automatically, performs that delivery — it is explicitly a human
Steward action: *"Who: Steward to existing Codex Stream A thread."*
Everything upstream and downstream of that one manual step can be
prepared, validated, or checked by tooling; that step itself cannot.
