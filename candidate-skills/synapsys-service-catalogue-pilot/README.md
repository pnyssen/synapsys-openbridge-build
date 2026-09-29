# synapsys-service-catalogue-pilot

**mirrors**: `CODEX_ASSESSMENT_SERVICE_CATALOGUE_LIFECYCLE_IMPLEMENTATION_READINESS_v0.1.md`
(cited below as the authorizing source — added retroactively to conform
to the mirrors convention introduced in
`candidate-skills/README.md`; not a new claim, just the existing
citation surfaced into the standard format).

Candidate tooling for the SynapSys Service Catalogue whole-of-lifecycle
proposal, built within the exact boundary Codex T1 authorized in
`CODEX_ASSESSMENT_SERVICE_CATALOGUE_LIFECYCLE_IMPLEMENTATION_READINESS_v0.1.md`:
one manual pilot, Working Memory file substrate only, no Odoo/N8N/
Contribution Ledger/runtime touch.

## What's here

- `validator.py` — offline, zero-network, zero-subprocess validator for
  Service Request / outcome-receipt front matter: required-field
  presence, status-vocabulary and origin-identity-state enforcement,
  and self-hash verification against both boundary conventions observed
  cross-lane this session (this lane's own, and Claude Cowork's).
- `tests/test_validator.py` — 12 boundary tests, including one that
  caught and fixed a real bug in the initial hash-boundary
  implementation before this was filed (see commit history — a naive
  `rstrip`-based boundary reconstruction produced false negatives; the
  fix uses direct substring slicing on the literal marker instead).
- `templates/` — `SERVICE_REQUEST_TEMPLATE_v0.1.md` and
  `OUTCOME_RECEIPT_TEMPLATE_v0.1.md`, the two artefact types the
  whole-of-lifecycle proposal's Stages 2 and 5 define.
- `pilot/SERVICE_REQUEST_PILOT_001_v0.1.md` — the actual, real pilot
  instance: a request to add `T1 Navigator` and `T3 Mesh` to
  `AI_LANE_ALIGNMENT_REGISTER_v0.1.md`'s Lane Roster as Claude Cowork
  sub-identities — Codex T1's own named "highest-leverage next evidence
  move," not an invented example. Passes validation clean (`ok=True`,
  zero errors, zero warnings).

## What this is not

Not an activated Service Catalogue. Not connected to Odoo, N8N, or any
runtime. Does not extend the Contribution Ledger. Does not mutate
anything outside this directory. `validator.py` reads a single file's
text and returns a report — it has no side effects.

## Status

CANDIDATE_CODE_AUTHORISED, per direct Steward instruction and Codex
T1's explicit `GO_FOR_MANUAL_PHASE_2_PILOT` verdict. Not installed as a
standing skill.
