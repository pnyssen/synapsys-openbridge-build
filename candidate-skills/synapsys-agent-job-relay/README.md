# synapsys-agent-job-relay

Candidate implementation of components 5.3 (job contract) and 5.1 (relay
outbox, logic only) from the filed design
`05_AI_RETURNS_HASHED/WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001/20260814--claude-code--design-candidate--synapsys-agent-full-ecosystem-integration-design--v1-0.md`
(SHA-256 `6070ad3a18527820d00171ccba501502eccf4488cfc32f9476077115be3c6d90`).

## Update 2026-08-14 — job_contract.py reconciled (v0.2)

ChatGPT Hub answered the relay requesting this design's Navigator-side
review (verdict `ACCEPT_AS_EVOLVE_INTEGRATION_BASIS`, see
`20260814--chatgpt-hub--integration-basis--evolve-view-synapsys-agent--v1-0.md`)
and specified a 17-field merged job contract extending the Navigator's
own Level-2 prompt-builder fields, reconciled against this module's
original 15-field sk07-agent-handoff-derived shape "by semantics ...
field count is secondary to one semantic contract." `job_contract.py` is
rewritten accordingly: 17 Navigator-aligned core fields (renamed where
Navigator specified an explicit name — e.g. `processor` → `target_lane`,
`owner` → `owner_lane`, `evidence_state` → `reality_state` — plus new
fields Navigator's list required that v0.1 didn't have: `control_marker`,
`origin_lane`, `role`, `context_id`, `state_revision`, `objective`,
`source_refs`, `ppv_state`, `stop_hold`, `replay_validity`) plus 8
sk07-heritage fields kept as named extensions (`stream`,
`processor_route`, `distribution_class`, `filing_state`,
`exception_route`, `status`, `replay_hash`, `origin_signal`). Full
field-by-field mapping is in the module's own docstring.

**Compatibility note**: two messages already sit in
`AGENT_OUTBOX/` written under the old 15-field shape (from before this
reconciliation existed) — `outbox.deserialize_message()` will raise on
them. `outbox.try_deserialize_message()` returns `None` instead, so a
polling loop can skip old-schema messages rather than crash on them.

## What's here

- `job_contract.py` — the 15-field job/handoff schema, built from the
  `sk07-agent-handoff` skill's own work-object shape (loaded this
  session; SANDBOX/TEST ONLY, `RUNTIME_ACTIVATION=NO` — reused here as a
  well-specified template, not as an authorising mechanism). Closed
  vocabularies (`processor`, `status`, `stream`, `distribution_class`),
  the processor role table (verbatim from the skill), replay-hash
  computation, and structural validation (`validate_job_contract`).
  **DRAFT v0.1** — the design's own §4/§9.1 flags this as pending
  reconciliation against the Navigator's actual "Ask / Analyse"
  prompt-builder field shape, which this lane could not read this
  session (no browser access). Treat this schema as a starting point,
  not final, until that reconciliation happens.
- `outbox.py` — pure message-queue logic for the relay's WM outbox:
  message construction (validates the job first), claim/complete
  state transitions (frozen-dataclass pure transitions, not mutation),
  a `select_claimable()` filter, a `detect_stale_claims()` check for
  claims that were never completed, a WM-naming-compliant filename
  generator, and serialize/deserialize round-trip. **Zero I/O of any
  kind** — no `sp_read`/`sp_write`/`sp_list` call, no network, no
  wall-clock call anywhere in this module. Callers fetch data and pass
  it in; callers perform the actual write of whatever this module
  returns. Mirrors `admin_task_dry_run.py`'s own pattern in this repo.
- `tests/test_job_contract.py` — 26 tests, including two built from real
  dispatches actually filed this session (the Wave Accelerator alignment
  request, and the still-pending SynapSys Agent design relay), not
  synthetic-only examples.
- `tests/test_outbox.py` — 19 tests covering build/claim/complete state
  transitions, stale-claim detection, filename compliance, and
  serialize/deserialize round-trips.
- 45/45 tests passing (`python3 -m pytest tests/ -v`).

## Update 2026-08-14 — outbox proven live, N8N deferred for v0

The full loop (build a `JobContract` → `build_message()` → `sp_write` to
`05_AI_RETURNS_HASHED/WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001/AGENT_OUTBOX/`
→ `sp_read` back → `deserialize_message()` → `select_claimable()` →
`claim()` → `complete()`) was run against a real, live WM file this
session and worked end to end — no N8N workflow needed for this lane to
enqueue and process its own work. See
`20260814--claude-code--routine-spec--synapsys-agent-outbox-scheduler--v0-2.md`
(WM) for the confirmed outbox path and the corrected wake-prompt using
it. The N8N relay CR (still filed, still HELD) is now understood as
needed only for *other lanes* to submit jobs into this same outbox
later — deferred, not required for v0 operability.

## What this is not (still true)

No `create_trigger` Routine exists yet — the scheduler spec is filed and
ready, but this lane does not self-authorise new persistent automation
without explicit Steward go-ahead. `outbox.py` itself still performs
zero I/O by design; the real `sp_write`/`sp_read` calls proving the loop
above were made by the calling session, not by this module.

## Status

CANDIDATE, with one component now live-proven (the outbox read/write/
claim/complete loop, against real WM data) and one still pending an
explicit go-ahead (the scheduler Routine itself). No CR filed/actioned
for the N8N side (deferred). Next step: Steward decides whether to
actually create the Routine now.
