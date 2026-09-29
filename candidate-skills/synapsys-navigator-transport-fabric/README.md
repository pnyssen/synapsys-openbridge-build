# synapsys-navigator-transport-fabric

Candidate implementation of Navigator Interface Fabric Phase 1, per the
Architecture Decision (Option 2: separation, not schema expansion) filed
this session against
`05_AI_RETURNS_HASHED/WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001/`.

## Scope boundary (load-bearing, not incidental)

`x_ss_agent_registry` is the domain/agent governance and routing plane.
`read_and_route` is the highest authority it expresses -- there is no
`execute` value, by platform-wide schema design (confirmed live: the
field's only selection options are `read_only`, `read_and_flag`,
`read_and_route`; the existing "Service Catalogue Agent" registry row's
own `x_bounded_by` states this explicitly). This package does **not**
add an execute value, does not modify that boundary, and structurally
cannot construct a `RegistryEntry` with an unrecognised authority class
(`transport_types.RegistryEntry.__post_init__` raises `ValueError`).

This transport fabric is a separate D007 platform transport component --
not an agent, not a domain authority holder. It claims, routes, and
hands a governed packet to a runtime adapter. It never decides on the
target domain's behalf, never assures, never approves or rejects
anything, and never elevates a resolved route into execute authority.

## What's here

- `transport_types.py` -- shared frozen dataclasses (not named `types.py`
  deliberately, to avoid shadowing the stdlib `types` module once this
  directory is on `sys.path`).
- `registry_resolver.py` -- read-only resolution of `target_lane` against
  registry rows. Only `authority_class == "read_and_route"` +
  `activation_status` in `{authorised, active}` resolves; everything else
  is an explicit, reasoned refusal.
- `replay_validator.py` -- exact-message-id replay detection, logical-job
  duplicate detection (same `(context_id, control_marker, state_revision)`
  under a different `message_id`), and hash-mismatch detection on
  same-id/different-hash. Does not attempt to recompute a hashing scheme
  this package doesn't own.
- `eligibility.py` -- composes the resolver + replay validator into
  `select_eligible_jobs()`.
- `claim_state_machine.py` -- idempotent claim/heartbeat/release/expire.
  `attempt_claim()` is safe to call twice for the same worker (no-op, not
  a second grant); a stale claim (default 120s since last heartbeat) is
  treated as abandoned and reclaimable.
- `adapter_interface.py` -- the `RuntimeAdapter` callable contract and
  `dispatch_to_adapter()`. No adapter registered for a `target_lane` is
  not an error -- it's an explicit `WAITING_EXTERNAL_RUNTIME`.
- `d009_adapter.py` -- the D009/Gemini capability probe and packet
  builder. `probe_d009_capability()` takes the AI Auditor's
  `sources_fully_processed` boolean as an explicit parameter (this
  package performs no Odoo I/O itself); when `False`, the adapter returns
  a governed `DEGRADED` decline, never a silent `PASS`.
- `return_bridge.py` -- `consume_return()` validates identity (returned
  `message_id` must match) and status (`ATTEMPTED_RETURNED` only) before
  accepting. Consumption records the **job's own bound** `state_revision`,
  not the controller's current revision -- a genuine return for an older
  job stays valid even after the controller has advanced.
- `health_projection.py` -- `build_health_projection()`, the Navigator
  transport-health view: domain, owner lane, ACTIVE/HELD/DEGRADED/OFFLINE,
  last heartbeat, pending jobs, claim latency, last return,
  `authority_boundary` (always a verbatim echo of the registry's own
  `authority_class`).
- `tests/test_transport_fabric.py` -- 37 tests: isolation (no forbidden
  imports, no wall-clock calls anywhere in the package), and the six named
  regression scenarios (duplicate replay, authority non-expansion,
  unavailable runtime, D009 source-not-ready decline, valid return,
  rollback/disable), plus eligibility and health-projection coverage.

## What this is not (yet) -- the live deployment delta

- **No live Odoo/N8N wiring.** Every function takes its inputs (registry
  rows, jobs, claims, the `sources_fully_processed` boolean) as plain
  arguments from the caller. The live wiring layer that reads
  `x_ss_agent_registry`/`x_ss_dispatch_task`/`AGENT_OUTBOX` and actually
  calls a D009 runtime is explicitly out of scope for this candidate
  build.
- **No persistent process.** `select_eligible_jobs()` /
  `dispatch_to_adapter()` / etc. are pure functions a live poller would
  call on each tick; this package does not itself run continuously.
  Standing up that poller (most plausibly an N8N workflow on a short
  cron) is CR-gated infrastructure, deliberately not touched here.
- **No credential binding, no new register, no execute enum, no new
  governance fields, no Navigator Current write.** All excluded per the
  Architecture Decision's explicit Phase-1 boundary.
- **The D009 adapter never actually calls Gemini.** When the capability
  probe is ATTEMPT-eligible, `d009_adapter_invoke()` still returns
  `WAITING_EXTERNAL_RUNTIME` rather than fabricating a result -- there is
  no live runtime call wired in.

## Status

CANDIDATE. Built and tested this session (37/37 passing, plus full
`candidate-skills/` suite re-run clean, no regression). Not committed to
`main`; pushed to a feature branch, no PR opened yet pending Steward
review of this receipt.
