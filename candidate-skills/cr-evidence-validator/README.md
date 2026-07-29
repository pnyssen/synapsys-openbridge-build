# cr-evidence-validator

Bounded Change Request **evidence-completeness** check — the third real
consumer of the shared validation core
(`candidate-skills/synapsys-service-catalogue-pilot/_validation_core.py`),
built to prove that core generalises beyond the Service Catalogue
pilot's own `validator.py`/`scoping_validator.py` pair, per Wave 3 of
`PROG-CLAUDE-CODE-MULTI-SERVICE-ENABLEMENT-001`.

## Discovery trail (source of the field list actually used)

No Odoo `x_change_request` (or equivalent) model/schema exists anywhere
in this repository — unlike `x_service_catalogue`, which has live
fixtures in the pilot's own test suite. The only repository-authoritative
source for what a Change Request needs before a CR-gated action is
`CLAUDE.md`'s **GitHub Change Control Rule** section (governing CR
`CHG-2026-410`):

> "CR needs `x_test_evidence` and `x_rollback_plan` populated before the
> action, or retrospective emergency registration immediately after."

That is the *only* place in this repository naming required CR evidence
fields, and it names exactly two. Wave 3's own instruction suggested four
further candidate fields (`x_change_reason`, `x_risk_assessment`,
`x_implementation_plan`, `x_validation_result`) as illustrative
("fields such as") — none of them appear anywhere else in this
repository (`mcp-servers/`, `candidate-skills/`, `CLAUDE.md`). Per this
programme's own SOURCE AND LINEAGE rule ("do not invent field names or
business rules where the repository already defines them differently"),
this validator:

- requires only `x_test_evidence` and `x_rollback_plan` (the two
  repo-evidenced fields);
- recognises the four additional fields **if present**, warning only on
  a populated-but-blank value, never requiring them and never applying
  an invented business rule to them.

No repository-native CR-status vocabulary was found either. The one
vocabulary this module reuses via `check_vocabulary()` is this
programme's own standing **VERDICT OPTIONS** list (`PASS`,
`PASS_WITH_CONDITIONS`, `HOLD`, `FAIL`, `SOURCE_OR_BASELINE_CONFLICT`,
`TESTS_NOT_RUN`, `AUTHORITY_REQUIRED`) — a real, quoted, in-thread
source, applied to an optional `verdict` field a caller may attach to an
evidence record (e.g. a filed Wave/CR outcome), not a fabricated
Odoo-style enum.

## What this is

`evidence_validator.py` — pure function over a plain dict (no network,
no subprocess, no Odoo/N8N call). Reuses
`_validation_core.check_required_fields`, `_validation_core.odoo_absent`
(the `False`/`None`/blank-string-absent convention, matching this
repo's existing `scoping_validator.py` precedent for `x_`-prefixed
field records) and `_validation_core.Finding` directly as its result
type, and `_validation_core.check_vocabulary` for the optional `verdict`
field.

## What this is not

Not a Change Request approval mechanism. Not connected to Odoo, N8N, or
GitHub. Does not mutate anything, imply implementation authority, move
PPV, or change workflow/catalogue/production state. `Finding.ok is True`
means only "the evidence fields CHG-2026-410 requires are populated" —
nothing more.

## Status

CANDIDATE, Potential PPV, reversible repository implementation only —
per Wave 3's own AUTHORITY AND STATE section. Not a governed Asset.
