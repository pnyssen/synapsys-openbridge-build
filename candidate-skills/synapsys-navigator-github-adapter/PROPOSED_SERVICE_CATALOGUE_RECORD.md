# Proposed `x_service_catalogue` Record — SynapSys Agent

**Status: PROPOSED SPEC ONLY. No `create_odoo` call has been made. This
lane's toolset only has read-only Odoo access (`search_odoo`/`read_odoo`/
`count_odoo`) — there is no write path available even if one were wanted.
Registering this is a decision for the Steward, per `steward.md`'s own
recorded caution about new recurring costs — a persistent Agent service is
exactly that, and this draft exists so that decision is one line-item
review, not a from-scratch design task.**

**Update 2026-08-14**: the five previously-OPEN fields below are now
resolved, per Steward's direct answers this session (`x_offering_layer`,
`x_service_ppv_ceiling`, and the three owner fields — see the filed
decision receipt
`05_AI_RETURNS_HASHED/WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001/20260814--claude-code--decision-receipt--service-catalogue-open-fields-resolved--v1-0.md`
for the exact quoted answers). **Still no `create_odoo` call has been
made** — this lane's Odoo access remains read-only; the table below is
now complete and ready for whichever lane holds Odoo write access to
execute in one call.

Every field name below was read live from `ir.model.fields` for
`x_service_catalogue` this session (68 real fields returned) — nothing here
is a guessed field name.

## Proposed field values

| Field | Proposed value | Rationale |
|---|---|---|
| `x_service_code` | `SC-AGENT-01` | Follows the existing `SC-01` pattern already visible in the live Navigator's own Service field |
| `x_service_name` | `SynapSys Agent — Navigator Evolve Host & Mesh Enablement` | States what it does, not a marketing name |
| `x_offering_layer` | `C` (`C - Collaboration`, confirmed real selection value via `ir.model.fields.selection`) | Steward, 2026-08-14, verbatim: "It's an internal technical service enabling collaboration." Matches `C - Collaboration` as the closest real category, consistent with `x_service_class: internal` already set below. |
| `x_service_status` | `draft` | Matches Potential PPV |
| `x_lifecycle_gate` | `draft` | Same reason |
| `x_service_class` | `internal` | Serves the Navigator/ecosystem itself, not directly sold as a client offering — though this may need revisiting if it later reaches collaborators/clients directly (membrane) |
| `x_service_role` / `x_platform_role` / `x_method_role` | `platform` | It's infrastructure capability, not a discrete method or a billable service |
| `x_service_ppv_entry` | `Potential` | Matches this candidate's actual current state |
| `x_service_ppv_ceiling` | `Probable` (confirmed real selection value) | Steward, 2026-08-14: selected "Probable (Recommended)" — allowed to mature past draft once the design proves out, capped short of full `Verified` production status until a later, separate decision |
| `x_default_workflow_phase` | `learn` | Of the five phases (sense/design/deliver/realise/learn), "learn" matches the Evolve-mode description already live in the Navigator: "turns observed signals... into learning" |
| `x_entry_point` | `direct_d001_request` | Steward-initiated, this thread, not a CRM lead or webhook |
| `x_named_consumer` | `steward` | Primary consumer today; `platform_system` (other AI lanes) is also plausible — single-select field forces a primary, not a claim the other doesn't apply |
| `x_ffe_state` | `evolve` | Matches its designated role in the Navigator's own Form/Flow/Evolve model exactly |
| `x_context_id` | `CTX-SS` | Same Context already bound to `WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001` in the live Navigator |
| `x_delivery_lead_id` / `x_steward_contact_id` / `x_service_owner_id` | `res.partner` id `6` ("Phil Nyssen", `phil@synapsys.com.au`) for all three | Steward, 2026-08-14: selected "All three = you (Phil) (Recommended)". **Flagging an ambiguity, not silently resolved**: `search_odoo` on `res.partner` for "Nyssen" returns two Phil Nyssen records — id `6` (`phil@synapsys.com.au`) and id `43` ("Phil Nyssen (Vitae Capital)", `phil.nyssen@vitaecapital.com.au`). id `6` was selected on the strength of the `synapsys.com.au` email domain matching this ecosystem, not independently confirmed by Steward — worth a one-line Steward confirmation before the actual `create_odoo` call, since a wrong pick here would misfile the owner. |
| `x_operations_pattern` | **None selected** | Checked all 28 `PAT-*` options in the live selection list; none clearly fits a persistent monitoring/mesh-integrity service. Selecting a poor fit to fill the field would misclassify it — may warrant a new `PAT-CAND-*` entry, not proposed here |
| `x_itil_utility` | "Continuous, read-only monitoring and freshness/drift detection across Odoo, Working Memory, Obsidian, GitHub and N8N, surfaced through the Navigator's Evolve mode." | Plain description of function |
| `x_itil_warranty` | "No write/mutation authority under any circumstance. Every claim carries one of five ruled freshness states (see `freshness.py`). Relay-only to other AI lanes — no assumed direct channel. Every action traces to a Work Object and exactly one next-valid-step." | States what's actually guaranteed, not aspirational |
| `x_itil_service_level_target` | `TBD` | No SLA proposed — uptime/recurring-cost targets are a Steward decision this draft deliberately does not presume |
| `x_itil_support_model` | `TBD` | Same reason |
| `x_itil_service_owner_role` | `D001 / Steward, pending named delegate` | Honest placeholder, not a fabricated name |
| `x_itil_csi_log` | *(empty)* | Nothing to log yet — a draft service has no improvement history |
| `x_context_binding_required` | `true` | Should not silently apply beyond `CTX-SS` without an explicit binding decision |
| `x_context_binding_notes` | "Scoped to CTX-SS per the Navigator MVP Work Object. Cross-Context monitoring is a separate, unmade decision." | |
| `x_productisation_status` | `not_productised` | Accurate — this is infrastructure, not a sellable unit today |
| `x_validation_status` | `pending` | No D009 challenge has been run against this specific proposal |
| `x_service_activation_requires_decision` | `true` | The one field on this list that should never be anything but true for this record |
| `x_authority_reference` | `SYNAPSYS_AGENT_GITHUB__NAVIGATOR_ALIGNMENT__STATE_REV152; steward.md recurring-cost caution recorded 20260811--claude-code--design-note--synapsys-agent-identity-anchor-loop-item1--v1-0.md` | Traceable, not asserted |
| `x_source_document` / `x_source_version` | This file / `v1.0` | |
| `x_warranty_commitment_type` | `none_declared` | Nothing committed yet — matches the draft/Potential state honestly rather than overclaiming a warranty tier |
| `x_description` | "Persistent, Navigator-led monitoring and mesh-integrity layer. Read-only across Odoo/WM/Obsidian/GitHub/N8N via existing MCP connectors. Never claims write/mutation authority. Design/candidate stage only — not activated." | |

## What this file does not do

Does not call `create_odoo` — this lane's Odoo access remains read-only
regardless of the fields below now being resolved. Does not independently
confirm which of the two "Phil Nyssen" `res.partner` records (id `6` vs
`43`) is correct beyond the email-domain match reasoning stated above.
Does not invent a `x_operations_pattern` fit that isn't there — still
none selected, unchanged from the original draft.

## Next valid step

All five previously-open fields are now resolved (see the "Update
2026-08-14" note at the top and the filed decision receipt). This table
is ready for one `create_odoo` call by whichever lane holds Odoo write
access — this lane does not. Worth a one-line Steward confirmation on the
`res.partner` id `6` vs `43` ambiguity before that call, since it's the
one item resolved by inference rather than direct Steward selection.
