# D007 Transport Pilot — Offline Readiness Package

Built in response to the "CODE REISSUE — STREAM A AUTH-CHANNEL AND
PILOT READINESS VERIFICATION" instruction, Work Object
`WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001`. This lane
(Claude Code / "Code") accepted `TOOL_BLOCKED_AUTH_CHANNEL` for the
live pilot itself and did every piece of useful work that does not
require a live endpoint, credential, or cross-session delivery
mechanism.

**This package never calls the real endpoint, never holds or invents a
credential, and never claims delivery to another AI thread.**

## Layout

```
schemas/transport_request_schema.json        the real workflow's fixed request contract, restated as JSON Schema
schemas/target_mount_receipt_schema.json      the required TARGET_MOUNT_RECEIPT_<RUN_ID>.json shape
mock/mock_transport_gateway.py                LOCAL MOCK — offline re-implementation of the documented validation rules
client/client_stub.py                         placeholder-only request/curl builder; never sends anything
validate/receipt_validator.py                 validates a real receipt (once one exists) against the schema + business rules
tests/test_offline_pilot_readiness.py         36 deterministic tests, no network calls
CAPABILITY_BOUNDARY_v0.1.md                   what this lane can and cannot do, and exactly where it stops
PROVISIONING_CONTRACT_v0.1.md                 review of the ALREADY-BUILT D007 pilot infrastructure, field by field
POST_PROVISION_EXECUTION_PROCEDURE_v0.1.md    exact steps once a real credential + delivery mechanism exist
MANUAL_HANDOFF_PACKET_v0.1.md                 points at the real existing dispatch; does not duplicate or claim to send it
TEST_REPORT.md                                full test transcript and coverage table
CANDIDATE_MANIFEST_SHA256.csv                 final file/byte/hash manifest, regenerated last
```

Run it yourself:

```
python3 -m unittest tests.test_offline_pilot_readiness -v
```

## Why this package does not re-design the pilot infrastructure

Fresh `sp_read` calls this session found that D007/the Hub controller
had already built, statically tested (`G1`–`G4` all `PASS` or
`PASS_WITH_DYNAMIC_GATES_OUTSTANDING`), and activated a real N8N
workflow (`SDGlH8QqeHpIIErz`) with a real endpoint and a real
`headerAuth` credential reference, *before* this lane was asked to
prepare anything. `PROVISIONING_CONTRACT_v0.1.md` reviews that existing
provisioning rather than inventing a competing design — inventing one
would risk drifting from the contract the real, already-activated
workflow was built against.

## What is genuinely new here

- A schema pair (`schemas/`) that turns the prose contract described
  across several D007 filings into something machine-checkable.
- A local mock (`mock/mock_transport_gateway.py`) that lets the
  request-validation, expiry, replay, nonce, binary-integrity, and
  ZIP-extraction-safety rules be exercised deterministically, with 36
  passing tests, without any network access or credential.
- A receipt validator (`validate/receipt_validator.py`) that can check
  whatever `TARGET_MOUNT_RECEIPT_<RUN_ID>.json` the real pilot
  eventually produces, the moment it exists — closing the loop between
  "D007 built the endpoint" and "someone can mechanically verify the
  receipt it returns" without this lane ever touching the endpoint
  itself.

## Boundary

No endpoint URL invented (the real one, already public in Working
Memory, is cited by reference — not minted here). No credential, API
key, token, or signature secret minted, guessed, or requested from the
Steward. No `transport_request_id`/`run_id`/`nonce`/`expiry` invented
and presented as live — every identifier used in fixtures and tests is
explicitly synthetic (`TR-TEST-01`, `NONCE-TEST-01`, etc.), and the one
place the real pilot's actual IDs appear (`_valid_receipt()` in the
test file) is a synthetic receipt used only to prove the validator
works, never claimed as a real execution result. No N8N workflow
created, modified, or activated by this lane. No Odoo, SharePoint
runtime state, schema, connector, or production configuration touched.
No claim of contact with, dispatch to, or acknowledgement from another
AI thread.
