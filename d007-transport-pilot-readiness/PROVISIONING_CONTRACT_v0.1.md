# D007 Transport Pilot — Provisioning Contract Review v0.1

This is **not** a from-scratch design. Fresh `sp_read` calls this
session against `D007_WM_TO_CODEX_TRANSPORT_PILOT_v0.1/` found that
D007/the Hub controller had already built, statically tested, and
activated a real pilot workflow before this lane was asked to prepare
anything. This document reviews that existing provisioning against the
minimum-infrastructure checklist this task specified, field by field,
marking each `SPECIFIED` (with the exact evidence) or `UNRESOLVED`
(no source states it — not silently assumed).

Workflow: `SDGlH8QqeHpIIErz` — "Navigator WM Binary Delivery Gateway —
Stream A Pilot", version `9b9ee8a6-cfee-4b24-98c7-a86b5f229028`, 19
nodes, `active=true` as of `2026-08-02T10:57:53+10:00`.

| Field | Status | Evidence / gap |
|---|---|---|
| Exact endpoint purpose | `SPECIFIED` | Deliver the exact, single Stream A evidence bundle (`NAVIGATOR_STREAM_A_HUB_EVIDENCE_BUNDLE_v0.1.zip`) to one authenticated `target_lane: codex` caller, once. Workflow name and `CODEX_TARGET_PREFLIGHT_AND_LIVE_MOUNT_DISPATCH_v0.1.md`'s Objective section. |
| HTTP method | `UNRESOLVED` | No file read this session states the method explicitly (only "Authenticated Webhook — Transport Request" as a node name, and a JSON request body). POST is the conventional inference for an N8N webhook accepting a JSON body, but this document does not assert it as fact — the dispatch's own rule is to mark unresolved fields as such rather than design silently. |
| Required headers | `PARTIALLY SPECIFIED` | One inbound header-auth credential is required (name/value never disclosed by design); the response carries integrity headers "request ID, run ID, hash, bytes, Work Object and replay state" (`D007_WM_TO_CODEX_TRANSPORT_STATIC_TEST_REPORT_v0.1.md`, "Integrity headers included" row). The exact header *keys* (e.g. the literal auth header name) are not stated in any file this lane can read — `UNRESOLVED` at the key-name level. |
| Payload schema | `SPECIFIED` | `fixed_contract` block in `D007_WM_TO_CODEX_TRANSPORT_WORKFLOW_EXPORT_SUMMARY_v0.1.json`: `transport_request_id`, `run_id`, `work_object_id`, `target_lane`, `nonce`. Matches `schemas/transport_request_schema.json` in this package exactly. |
| Authentication method | `SPECIFIED` | `headerAuth`, credential reference `H1-CGPT-N8N-Inbound-Auth` (id `9gaq6IiZhQLiEJV7`, type `httpHeaderAuth`). A negative probe without a valid credential returned `HTTP 403 — Authorization data is wrong` (`D007_WM_TO_CODEX_TRANSPORT_PILOT_ACTIVATION_RECEIPT_v0.1.md`) — fail-closed is evidenced, not assumed. |
| Secret-storage requirement | `SPECIFIED` | Credential referenced by ID/name only inside N8N's own credential store; static test report confirms "Secret values exported or logged: PASS — absent." No secret value has ever appeared in any Working Memory file this lane read. |
| Expiry and replay controls | `SPECIFIED` | Manifest `expires_at: 2026-08-02T14:00:00+10:00`, `allowed_attempts: 1`, `replay_policy: single_use_no_overwrite`; a dedicated "Replay and Nonce Gate" node and "Inspect Existing Source Receipt" no-overwrite check are both named in the workflow export. |
| Allowed caller identity | `PARTIALLY SPECIFIED` | The contract fixes `target_lane: "codex"`, but caller identity is enforced only via possession of the shared header-auth credential — there is no per-caller/per-session identity check beyond that. This lane's own receipt schema requires a self-declared `target_runtime_identity` field precisely because the endpoint itself does not verify one. |
| Response schema | `PARTIALLY SPECIFIED` | Success: binary body + integrity headers. Failure (invalid request): `JSON 422` (static test report, "Failure branches cannot return binary" row). The exact JSON error body shape and the complete header list are not enumerated in any source this lane read — `UNRESOLVED` in full detail. |
| Logging and receipt requirements | `SPECIFIED` | Source-side: no-overwrite receipt written via `W17_SP_WorkingMemory_Filing_Write` before the binary response is ever sent. Target-side: `TARGET_MOUNT_RECEIPT_<RUN_ID>.json` required per `CODEX_TARGET_PREFLIGHT_AND_LIVE_MOUNT_DISPATCH_v0.1.md`'s "Required receipt fields" list — reproduced as `schemas/target_mount_receipt_schema.json` in this package. |
| Activation and rollback controls | `SPECIFIED` | Activated `2026-08-02T10:57:53+10:00`; scheduled close `2026-08-02T14:00:00+10:00` or earlier on return; rollback = deactivate workflow `SDGlH8QqeHpIIErz`, delete only under separate explicit authority (`D007_WM_TO_CODEX_TRANSPORT_WORKFLOW_EXPORT_SUMMARY_v0.1.json`, `rollback` field). |
| Test endpoint / production endpoint distinction | `UNRESOLVED` | No source names a separate low-stakes test endpoint. `allowed_attempts: 1` means the single live endpoint is simultaneously the only way to validate the real auth path and the one permitted real delivery — there is no evidenced way to rehearse the authenticated call without consuming the pilot's one attempt. Flagged as a genuine gap, not designed around. |
| Evidence required before the endpoint is declared usable | `SPECIFIED` | Explicit gate ladder in the activation receipt: `G1` authority `PASS`, `G2` inactive build `PASS`, `G3` credential-reference binding `PASS`, `G4` static inspection `PASS_WITH_DYNAMIC_GATES_OUTSTANDING`, `G5` exact source execution `PENDING`, `G6` Codex target preflight `PENDING`, `G7` target mount/read/live graph `PENDING`, `G8` deactivation `SCHEDULED`. As of this reading, `G5`–`G7` remain open — the endpoint is activated but not yet proven end-to-end. |

## Net assessment

D007 provisioning for **this specific pilot window** is essentially
complete and evidenced — not a gap this lane needs to close. What
remains genuinely open, from evidence rather than assumption, is:
whether the `H1-CGPT-N8N-Inbound-Auth` credential is actually present
in the real Codex runtime's environment (this lane cannot see that),
and whether the human delivery step (Steward pasting the dispatch into
the Codex thread) has happened yet. Both are outside D007's
infrastructure and outside this lane's capability — see
`CAPABILITY_BOUNDARY_v0.1.md`.
