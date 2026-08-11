# synapsys-navigator-github-adapter

Candidate architecture for the GitHub/Agent side of the SynapSys Navigator's
one-core, multi-host-adapter model. Built in direct response to a dispatched
alignment brief (`SYNAPSYS_AGENT_GITHUB__NAVIGATOR_ALIGNMENT__STATE_REV152`),
filed at
`05_AI_RETURNS_HASHED/WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001/20260811--chatgpt-hub--dispatch--synapsys-agent-github-navigator-alignment--v1-0.md`.

## Mirrors

Full architecture assessment and design:
`05_AI_RETURNS_HASHED/WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001/SYNAPSYS_AGENT_GITHUB_NAVIGATOR_ALIGNMENT_RETURN_v1.0.md`
(SynapSys Working Memory).

## What this is

The Current Navigator (`Obsidian/00_SYSTEM/NAVIGATOR_SUPPORT/CURRENT/SYNAPSYS_NAVIGATOR.html`,
v4.1, state revision 152) is a single self-contained HTML file: one role
model (Steward/Architect/Collaborator), one operating-mode model
(Form/Flow/Evolve), one evidence-state vocabulary, and one source/
currentness bar — all implemented client-side in about 100 lines of vanilla
JS, with Odoo and Obsidian route targets hardcoded directly into the markup.

This folder extracts the one part of that file that is host-specific — the
mapping from a *logical* route name to a *host* target (an Obsidian-relative
file path, an Odoo action ID, or a future Agent-served endpoint) — into a
single JSON manifest. Nothing else about the Navigator changes: the same
role model, mode model, evidence vocabulary, and visual contract (white
background, dark text, 14/12/10 font sizes only) stay exactly as already
built and already live.

## What's here

- `routes.json` — the logical route registry, reverse-engineered field-for-
  field from the live `SYNAPSYS_NAVIGATOR.html` (read directly this
  session, not guessed): every Form-mode lens link, every Flow-mode Odoo
  action ID, and the six source-bar entries, each tagged with its logical
  name and its current host-specific target. This is the artifact a
  Navigator Core would read instead of having those targets baked into the
  page markup — the same registry could, in principle, be re-emitted with
  different targets for an Odoo-native or Agent-hosted build without
  touching the role/mode/evidence logic at all. Updated once already, from
  a v4.1/revision-152 extraction to v4.2/revision-153 — the live Navigator
  advanced between the two reads, which is itself recorded as a finding
  (see `known_gaps_disclosed` in the file) rather than silently absorbed.
- `STATE_PROVIDER_CONTRACT.md` — a specification, not an implementation, for
  how a future host (the SynapSys Agent, or any other) would resolve the
  same canonical state (Working Memory controller revision, Goal Anchor,
  current Work Object, Odoo operational records) that the current static
  HTML has hardcoded as text. Maps each requirement directly onto this
  repo's existing `mcp-servers/odoo_mcp_readonly.py`,
  `mcp-servers/n8n_mcp_readonly.py`, and the SharePoint MCP connector
  already declared in `.mcp.json` — reused, not reinvented.
- `freshness.py` + `tests/test_freshness.py` — a real, executed (12/12
  passing), zero-network implementation of the five-state freshness
  vocabulary this contract's own identified gap called for
  (`CURRENT_MATCHED` / `CURRENT_WITH_NON_MATERIAL_VARIANCE` /
  `STALE_PROJECTION` / `CONFLICTED` / `CONTENT_EXTRACTION_PENDING`). Pure
  classification function — callers supply timestamps and a success flag
  from their own connector call; this module never calls out itself.
- `admin_task_dry_run.py` + `tests/test_admin_task_dry_run.py` — a
  dry-run-only precondition validator for the already-fully-specified
  "Publish Obsidian Mobile" Admin Task (spec filed separately by ChatGPT
  Hub at `Obsidian/00_SYSTEM/NAVIGATOR_SUPPORT/CURRENT/CONTROLS/NAVIGATOR_ADMIN_TASK_OBSIDIAN_MOBILE_PUBLISH_v1.0.md`,
  not duplicated here). Built directly from a real, read-only `sp_list`
  check performed this session: `08_MOBILE_DISPATCH` is currently empty —
  no prior Obsidian mobile publication exists — which the existing spec's
  step 3 ("rename current published folder to a backup") doesn't
  explicitly cover. 11/11 tests passing, including one built from that
  real result, not a synthetic fixture.
- `PROPOSED_SERVICE_CATALOGUE_RECORD.md` — a draft `x_service_catalogue`
  record for the SynapSys Agent, every field name read live from
  `ir.model.fields` this session (68 real fields, not guessed). Explicitly
  not created — this lane's Odoo access is read-only regardless, and two
  required-feeling fields (`x_offering_layer`, `x_service_ppv_ceiling`)
  plus three owner `many2one` fields are left open rather than guessed,
  since a wrong guess there would misfile the record from day one.

## What this is not

Not a rebuild of the Navigator. Not a second front door, a second ontology,
or a competing source of operational truth — `routes.json` is a data
extraction from the one Current Navigator, and `STATE_PROVIDER_CONTRACT.md`
specifies read-only providers only. Does not touch Odoo, Obsidian, N8N,
SharePoint folder structure, or the live `SYNAPSYS_NAVIGATOR.html` itself.
No runtime, no credentials, no production mutation of any kind.

## Status

CANDIDATE — design-and-alignment scope only, per the dispatching brief's own
authority boundary (`DESIGN_AND_ALIGNMENT_ONLY__NO_RUNTIME_OR_PRODUCTION_MUTATION_AUTHORISED`).
Not merged, not adopted, not a Navigator Core implementation — the next step
after this is Steward review of the full return, not further build.
