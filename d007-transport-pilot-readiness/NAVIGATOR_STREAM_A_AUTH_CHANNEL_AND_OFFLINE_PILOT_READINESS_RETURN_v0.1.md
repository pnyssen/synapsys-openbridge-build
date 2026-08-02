# Navigator Stream A — Auth-Channel and Offline Pilot Readiness Return v0.1

Work Object: `WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001`
Role: Codex / Code technical-reality lane. Mode: read-only verification
and offline candidate preparation. Control marker accepted:
`TOOL_BLOCKED_AUTH_CHANNEL_ACCEPTED`.
Built: `2026-08-02T01:32:08Z` (UTC, real capture via `date -u`).

**Verdict: `READY_FOR_PROVISIONING_WITH_GAPS`**

## Capability state

Full detail in `CAPABILITY_BOUNDARY_v0.1.md` (filed alongside this
return). Summary: this lane has read-only Working Memory and N8N/Odoo
MCP access, local git/GitHub push, and local Python execution. It has
no environment-bound header-auth credential for the pilot endpoint, no
N8N write/activation access, and no tool-mediated channel to another AI
thread or session. These are accepted as capability facts, not retried.

## Source files inspected

All read fresh via `sp_read`/`sp_list` this session (not recalled from
earlier context), from
`05_AI_RETURNS_HASHED/WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001/WAVE_INTEGRATED_NAVIGATOR_MVP_20260802/`:

- `NAVIGATOR_INTEGRATED_MVP_DISPATCH_MANIFEST_v1.1.md` (current governing manifest at read time)
- `D007_WM_TO_CODEX_TRANSPORT_PILOT_v0.1/CODEX_TARGET_PREFLIGHT_AND_LIVE_MOUNT_DISPATCH_v0.1.md`
- `D007_WM_TO_CODEX_TRANSPORT_PILOT_v0.1/D007_WM_TO_CODEX_TRANSPORT_MANIFEST_v0.1.json`
- `D007_WM_TO_CODEX_TRANSPORT_PILOT_v0.1/D007_WM_TO_CODEX_TRANSPORT_PILOT_ACTIVATION_RECEIPT_v0.1.md`
- `D007_WM_TO_CODEX_TRANSPORT_PILOT_v0.1/D007_WM_TO_CODEX_TRANSPORT_PILOT_AUTHORITY_RELEASE_v0.1.md`
- `D007_WM_TO_CODEX_TRANSPORT_PILOT_v0.1/D007_WM_TO_CODEX_TRANSPORT_STATIC_TEST_REPORT_v0.1.md`
- `D007_WM_TO_CODEX_TRANSPORT_PILOT_v0.1/D007_WM_TO_CODEX_TRANSPORT_WORKFLOW_EXPORT_SUMMARY_v0.1.json`
- `STREAM_A_LOCAL_FIXTURE_RETURN_INTAKE_AND_LIVE_MOUNT_HOLD_RECEIPT_v0.1.md`
- `STREAM_A_REPORTED_RETURN_CONTROLLER_UPDATE_RECEIPT_v0.1.md`
- `sp_list` of the WO root and the wave folder, to confirm current filenames/sizes before citing any of them

## Source files unavailable

`D007_WM_TO_CODEX_TRANSPORT_IMPLEMENTATION_PACKET_v0.1.md` — named as
the authority-release packet's target in
`D007_WM_TO_CODEX_TRANSPORT_PILOT_AUTHORITY_RELEASE_v0.1.md`'s "Packet:"
field, but not found in the wave folder listing at read time. The
authority release, activation receipt, static test report, and
workflow export summary together supply enough detail to review the
provisioning contract without it; its absence is recorded, not
papered over.

## Live endpoint state

`ACTIVATED_BY_D007 / G5-G7 PENDING`. A real N8N workflow
(`SDGlH8QqeHpIIErz`, "Navigator WM Binary Delivery Gateway — Stream A
Pilot") is active at
`https://n8n.srv1536619.hstgr.cloud/webhook/navigator-wm-codex-stream-a-pilot-20260802`,
activated `2026-08-02T10:57:53+10:00`, scheduled to close
`2026-08-02T14:00:00+10:00` or earlier on return. A negative
authentication probe already returned `HTTP 403`, proving fail-closed
behaviour. No successful authenticated call has been evidenced yet
(gates `G5` source test, `G6` target preflight, and `G7` pilot all
`PENDING` in the activation receipt). This lane did not call the
endpoint and did not attempt to.

## Credential state

`ABSENT_TO_THIS_LANE / UNVERIFIED_IN_CODEX_RUNTIME`. The required
credential is `H1-CGPT-N8N-Inbound-Auth` (reference ID `9gaq6IiZhQLiEJV7`,
type `httpHeaderAuth`). This lane holds no such credential and made no
attempt to substitute another one. Whether the real Codex runtime holds
it is outside what this lane can observe.

## Cross-thread delivery state

`NO_MECHANISM`. This lane has no tool that addresses, messages, or
delivers a payload to another AI session. The governing manifest's own
"Exactly one controller action" names the real mechanism as a human
action: *"Who: Steward to existing Codex Stream A thread."* No claim of
contact, dispatch, or acknowledgement is made here.

## Offline harness produced

Yes — `d007-transport-pilot-readiness/` (this package): two JSON
Schemas, a local mock re-implementation of the documented validation
rules (`mock/mock_transport_gateway.py`), a placeholder-only client
stub (`client/client_stub.py`), a receipt validator
(`validate/receipt_validator.py`), and a 36-test deterministic suite.
Full detail in `README.md` and `PROVISIONING_CONTRACT_v0.1.md`.

## Tests executed

`python3 -B -m unittest tests.test_offline_pilot_readiness -v`

## Test results

`36/36 PASSED`. Full transcript and coverage table in `TEST_REPORT.md`.

## Unresolved specification fields

From `PROVISIONING_CONTRACT_v0.1.md` (marked `UNRESOLVED`, not
silently designed): exact HTTP method (no source states it); exact
auth-header and response-integrity-header key names (only their
existence and purpose are documented); the complete failure-response
JSON schema (only "`HTTP 422`" is evidenced); and whether a separate
test/sandbox endpoint exists distinct from the single, single-use
(`allowed_attempts: 1`) production pilot endpoint (none is evidenced —
this means the real auth path cannot be rehearsed without consuming
the one permitted live attempt).

## D007 provisioning requirements

Already substantially met — see the full field-by-field table in
`PROVISIONING_CONTRACT_v0.1.md`. D007 has already built, statically
tested, and activated the pilot workflow; this lane's contribution is
the review and the offline-checkable schemas, not a redesign.

## Post-provision execution procedure

Full procedure in `POST_PROVISION_EXECUTION_PROCEDURE_v0.1.md`:
endpoint-identity check against the one evidenced URL and manifest
expiry, boolean-only credential-presence check, a fully local dry run
(schema validation only, since no rehearsal endpoint exists),
success/failure/anomaly distinctions, the mandatory
`TARGET_MOUNT_RECEIPT_<RUN_ID>.json` validation gate, explicit
STOP/HOLD triggers, and the one remaining manual-only action (human
delivery into the Codex thread).

## Manual handoff packet prepared

Yes, but as a **pointer**, not a duplicate — `MANUAL_HANDOFF_PACKET_v0.1.md`
identifies the real, already-filed dispatch
(`CODEX_TARGET_PREFLIGHT_AND_LIVE_MOUNT_DISPATCH_v0.1.md`, SHA-256
`cc8fe34620bc51a634639fc5a34ced35ba543c8174ef4ec5ea1074b1930e2b0b`) as
the payload to use, rather than authoring a second, independently
worded dispatch that could drift from the one the real workflow was
actually tested against. It restates destination/timing/payload/expected
return/filing/boundary for completeness and states plainly that nothing
has been sent.

## Files produced

16 files. Full manifest below and in `CANDIDATE_MANIFEST_SHA256.csv`.

| Path | Bytes | SHA-256 |
|---|---:|---|
| `CAPABILITY_BOUNDARY_v0.1.md` | 3202 | `ac2a8092ee376070cfad481d719d976770558a4c703160d81c7d0a944735a47f` |
| `MANUAL_HANDOFF_PACKET_v0.1.md` | 3536 | `65e897b246d7b2e8528a9db84a2de82885e56cbe361d0683431972131392f38a` |
| `POST_PROVISION_EXECUTION_PROCEDURE_v0.1.md` | 4882 | `d6b8eb414c1a9fa68eee16f77f83821829748f5f6eb98cd1a4d920c9b995faeb` |
| `PROVISIONING_CONTRACT_v0.1.md` | 6246 | `4841c85c71740eb7d38d3ca6e1551aa7459e4c925607530bf608030cc7a2548e` |
| `README.md` | 4247 | `22d4db7bc6f9f496c31e6940bd97500bcbdb2b96bda6b9fef571d11b1d1d74c4` |
| `TEST_REPORT.md` | 4469 | `347375b48021c9af1ee4ccb326ced660ab6055ef707602700724976a07c0dd4f` |
| `client/__init__.py` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `client/client_stub.py` | 2542 | `73e2f70e5728088d54f8eb410f20f8e34ebcf138457ec32ca1c500c1b37cdc59` |
| `mock/__init__.py` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `mock/mock_transport_gateway.py` | 7877 | `0f69d343211be3d71875f7e0f8f37344e0ed4dbfb37a30022a012d710e6d3c98` |
| `schemas/target_mount_receipt_schema.json` | 3053 | `9ee8eea89470592552cf9627ed302966c30887f0e67ba0bdf03764bd1c9f723c` |
| `schemas/transport_request_schema.json` | 1332 | `1d8d43050b0de3480dbee4c5fa68019c2f0ee90424ba5edb5fcca247870ab513` |
| `tests/__init__.py` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `tests/test_offline_pilot_readiness.py` | 12928 | `5952f3e647c6c4a4c8c92b1da76114c75318c9b0e7830013ef5aad57dbea7b29` |
| `validate/__init__.py` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `validate/receipt_validator.py` | 2777 | `46c531f392c2c456a2e4dce71acedd89568d716e155a9b0e447b11b85b2df56b` |

## Exact Working Memory path

`05_AI_RETURNS_HASHED/WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001/WAVE_INTEGRATED_NAVIGATOR_MVP_20260802/D007_WM_TO_CODEX_TRANSPORT_PILOT_v0.1/`

## Bytes

This return file's own bytes and SHA-256 are stated by `sp_write`'s
response at filing time (see the filing confirmation appended after
this return is written) — not self-computed in advance, since prior
turns in this session showed local reconstruction can drift by a
trailing-newline byte from the filed copy.

## SHA-256

See above.

## Readback state

Every file listed under "Files produced" was written locally, hashed
from disk (not typed by hand), and will be filed via `sp_write` with
each returned hash cross-checked against this table before being
reported as filed.

## Evidence state

`BODY_VERIFIED_LOCAL / D007_INFRASTRUCTURE_EVIDENCE_FRESH_THIS_SESSION`.
Every fact cited about the pilot workflow, endpoint, gates, and manifest
came from `sp_read` calls made in this turn, not from memory of earlier
turns in this conversation.

## Reality state

Offline harness: `IMPLEMENTED_AND_TESTED`. Live pilot: `NOT_ATTEMPTED_BY_THIS_LANE`.
D007 provisioning: `ACTIVE_WITH_DYNAMIC_GATES_OUTSTANDING` (per the
real activation receipt, not this lane's claim).

## Authority state

This lane's own actions: read-only WM/N8N/Odoo access plus local file
creation and git push — no mutation of any production system. Live
relay execution, credential binding, N8N/Odoo runtime state, PPV, and
canon movement all remain `HELD`, unchanged by this return.

## Mutation state

`NONE`. No N8N workflow created/modified/activated by this lane, no
Odoo change, no SharePoint runtime-state change beyond filing new files
under the one folder this lane's write authority already covers, no
credential issued or exposed.

## STOP/HOLD

`HOLD` on: consuming the pilot's one live attempt without Codex-side
credential confirmation; treating any of the `UNRESOLVED` provisioning
fields as decided; re-sending or rewording the existing Codex dispatch
instead of using the filed original; routing this readiness return back
to this lane for a repeated live-endpoint attempt.

## Exactly one next valid action

Route this filed provisioning-contract review and offline-pilot
readiness return to the authorised D007/N8N runtime lane and to the
Steward, for the one remaining manual step: confirm the
`H1-CGPT-N8N-Inbound-Auth` credential is present in the actual Codex
runtime, then paste the unmodified
`CODEX_TARGET_PREFLIGHT_AND_LIVE_MOUNT_DISPATCH_v0.1.md` into the
existing Codex Stream A thread before the manifest's
`2026-08-02T14:00:00+10:00` expiry. Do not route back to this lane for
repeated endpoint attempts until real provisioning evidence (a
completed `TARGET_MOUNT_RECEIPT_*.json`) exists.

## Replay-validity

`PRESERVED`. Every claim above is either a freshly re-read Working
Memory fact (cited by exact filename and, where available, SHA-256), a
locally recomputed hash, or an explicitly labelled boundary/gap — no
assertion here depends on trusting an earlier turn's unrechecked claim
or on treating this lane's own narrative as proof of a live execution
that did not happen.
