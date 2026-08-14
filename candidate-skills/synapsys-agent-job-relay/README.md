# synapsys-agent-job-relay

Candidate implementation of components 5.3 (job contract) and 5.1 (relay
outbox, logic only) from the filed design
`05_AI_RETURNS_HASHED/WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001/20260814--claude-code--design-candidate--synapsys-agent-full-ecosystem-integration-design--v1-0.md`
(SHA-256 `6070ad3a18527820d00171ccba501502eccf4488cfc32f9476077115be3c6d90`).

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

## What this is not

Not a working relay — no N8N workflow exists, no `create_trigger`
Routine exists, nothing here is wired to any live SharePoint/N8N/Odoo
call. `outbox.py` performs zero I/O by design; a future caller (a
scheduler Routine, or a human operator) is responsible for actually
reading/writing WM and handing this module plain data. Building the
live N8N relay workflow itself requires a filed CR first, per this
repo's N8N Workflow Change Control Rule — not started, not in scope for
this candidate.

## Status

CANDIDATE. Design-and-code-only, per this lane's standing authority
boundary — no runtime, no credentials, no live wiring, no CR filed for
the N8N side. Next steps (per the design's own §9): reconcile the job
contract against the Navigator's real field shape once ChatGPT Hub
responds to the filed relay request; draft the N8N relay CR; draft the
scheduler Routine spec — none of those are performed by this candidate.
