# synapsys-mesh-scaffold (candidate v0.1, dry run)

Schemas, validators and a coverage report for the four repeatable mesh scaffold modules
(contribution test with bear case, RACI, baselines, shock readiness). Generic: no Context
content, no third-party names. Candidate only: Potential, authority HELD, not canon.

- `ss_scaffold/rules.py` one validator per module; `errors` = a rule is broken, `gaps` = unknown or
  unaccepted (`[n]`), never counted, never guessed.
- `ss_scaffold/report.py` one report per Context: one verb, one tested number (RACI coverage), the
  other three coverage numbers in the drill-down; a module not supplied is `[n] not supplied`, not 0.
- `schemas/` descriptive field lists (the rules live in code).
- Run: `python -m ss_scaffold CONTEXT.json [...] --out DIR` · test: `pytest -q`.
- Reads JSON only. No Odoo, N8N or network. Odoo has no model for these modules; any model needs a D007 CR.
- RACI interpretation (to confirm): a row is covered when it has an accepted Accountable (with
  acceptance evidence), an accepted Responsible, and no cell left as a proposal.
