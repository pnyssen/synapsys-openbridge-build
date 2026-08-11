# State Provider Contract — SynapSys Agent / GitHub Adapter (candidate)

Specification only. No implementation, no runtime, no credential issuance.
Maps the dispatched brief's "Data and state requirements for the future
Agent" list directly onto what already exists in this repo's `mcp-servers/`,
so a future Agent host adapter reuses existing, already-tested connectors
instead of inventing new ones.

## Why this exists

The live Current Navigator (`SYNAPSYS_NAVIGATOR.html` v4.1) states its
source/currentness facts as hardcoded text — e.g. `wm: REV_152_PENDING_FINAL_READBACK`
baked into the page at generation time. That is correct for a static,
regenerated-per-change HTML file, but it is not a live read, and the state
control folder for this Work Object has moved through 150+ revisions in the
last ten days alone — often minutes apart. A host that actually serves live
state (the future Agent adapter) needs each of the items below resolved by
an explicit read at request time, not copied from the last time the page
was generated.

## Provider mapping

| Requirement (from the dispatched brief) | Provider today | Status |
|---|---|---|
| Canonical Working Memory controller state | SharePoint MCP (`sp_read`/`sp_list` against `STATE_CONTROL/NAVIGATOR_STATE_CONTROL_v*.json`) | Live, already used this session |
| Durable Goal Anchor | Same SharePoint MCP, `STATE_CONTROL/NAVIGATOR_GOAL_ANCHOR_v1.0.md` | Live, already used this session |
| Current Work Object | Same SharePoint MCP, plus `x_ss_work_object_register` in Odoo | Partially live — WM side confirmed; Odoo side needs `mcp-servers/odoo_mcp_readonly.py` |
| Context / Offering relationships | Odoo readonly connector (`search_odoo`/`read_odoo` against `x_ss_context`/offering models) | Connector exists (`mcp-servers/odoo_mcp_readonly.py`), not yet exercised against these specific models this session |
| Odoo operational records (Services, Benefits, Canonical Library, etc.) | `mcp-servers/odoo_mcp_readonly.py` | Built, tested (37/37 transport tests per this repo's CI), read-only by design |
| Current Obsidian design/projection routes | SharePoint MCP against `Obsidian/00_SYSTEM/NAVIGATOR_SUPPORT/CURRENT/` | Live, already used this session (this is how `SYNAPSYS_NAVIGATOR.html` itself was read) |
| Services / Methods / Patterns / Canonical references | Odoo readonly connector, same as above | Connector exists |
| Evidence / Benefit / Outcomes / Assets | Odoo readonly connector + Working Memory SharePoint reads | Both connectors exist |
| AI-lane routing / expected returns | Working Memory (`AI_LANE_ALIGNMENT_REGISTER_v0.1.md`, `LANE_VOCABULARY_AND_ROLE_REGISTER_v0.1.md`) | Live, both read this session |
| Authority / D007 release state | Working Memory CR/release filings (`05_AI_RETURNS_HASHED/.../*_RELEASE_v*.md`) | Live via SharePoint MCP; no live "current release state" query exists yet — reading the latest filed release packet is today's only mechanism |
| Freshness / last-successful-read state | Not implemented anywhere today | **Gap.** Every connector above returns data; none of them currently stamp a machine-readable freshness/last-read field the way the Service Catalogue architecture's `CURRENT_MATCHED`/`STALE_PROJECTION`/`CONFLICTED` vocabulary already specifies. This is the one genuinely new piece of plumbing needed, not a reuse of something that exists. |
| N8N runtime state | `mcp-servers/n8n_mcp_readonly.py` | Built, tested, read-only — held from any Evolve-mode display per the brief's own N8N boundary |

## What this means for the Agent adapter, concretely

A future SynapSys Agent host adapter does not need six new connectors. It
needs: (a) the three connectors already in `mcp-servers/` wired into one
adapter process instead of used ad hoc per session, and (b) the one missing
piece — a freshness/last-read stamp applied uniformly across all of them,
reusing the five-state vocabulary already ruled in
`AI_NAVIGATOR_SERVICE_CATALOGUE_OPERATING_ARCHITECTURE_v0.1` rather than
inventing a sixth vocabulary for this purpose.

## Explicit non-claims

This document does not implement a provider, does not grant the Agent any
write path, and does not change what any existing MCP connector is
authorised to do. Every connector referenced above remains read-only exactly
as currently configured. No SynapSys Agent runtime exists to consume this
contract yet.

## Status

CANDIDATE — specification only, per the dispatching brief's
`DESIGN_AND_ALIGNMENT_ONLY` authority boundary.
