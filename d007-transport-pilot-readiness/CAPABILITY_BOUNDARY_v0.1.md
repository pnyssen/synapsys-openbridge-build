# Capability Boundary v0.1 — Claude Code / "Code" lane, this session

Stated plainly, per this task's "Controlling finding" and "accepted capability facts" framing — these are not retried, not worked around, and not treated as something Steward authority can waive.

## Available to this lane, this session

- Read-only SynapSys SharePoint Working Memory access (`sp_read`/`sp_list`) — used to fetch every fact cited in this readiness package, all freshly re-read this session rather than recalled from earlier context.
- Read-only N8N MCP tools (`synapsys-n8n-readonly-code`: `list_workflows`, `get_workflow`, `list_executions`, `get_execution`, `list_credentials`, `ping_n8n`) and read-only Odoo MCP tools (`synapsys-odoo-readonly-code`) — neither was needed for this task beyond what Working Memory already evidenced, since the pilot workflow's own export summary and static test report were already filed.
- Local git/GitHub push access to `pnyssen/synapsys-openbridge-build`, this branch.
- Local Python execution (offline, deterministic) — used for every schema/fixture/test in this package.

## Not available to this lane, this session

- **No environment-bound header-auth credential** for `H1-CGPT-N8N-Inbound-Auth` (credential ID `9gaq6IiZhQLiEJV7`, per `D007_WM_TO_CODEX_TRANSPORT_WORKFLOW_EXPORT_SUMMARY_v0.1.json`), or for any other credential scoped to the pilot endpoint. This is confirmed by absence, not by a failed lookup attempt — no tool in this session exposes such a credential, and per this repository's CLAUDE.md capability contract, self-issuing or self-configuring one is explicitly barred even under direct instruction.
- **No N8N write or activation access.** Only the two read-only N8N/Odoo MCP servers are declared in this session's `.mcp.json`/`enabledMcpjsonServers`. The write-capable server that could create or activate a workflow is not connected. This lane did not, and could not, create the pilot workflow `SDGlH8QqeHpIIErz` — it already existed, built by a different actor, before this session inspected it.
- **No tool-mediated channel to another AI thread or session**, Codex's or otherwise. This session has no tool that addresses, messages, or delivers a payload to a session outside itself. This matches the governing manifest's own "Exactly one controller action" for this pilot (`NAVIGATOR_INTEGRATED_MVP_DISPATCH_MANIFEST_v1.1.md`, read fresh this session): *"Who: Steward to existing Codex Stream A thread."* — i.e. the real delivery mechanism is a human pasting text, not an automated inter-AI channel, and this lane holds no privileged position in that mechanism either.

## First live dependency that cannot be crossed

The authenticated HTTP request to
`https://n8n.srv1536619.hstgr.cloud/webhook/navigator-wm-codex-stream-a-pilot-20260802`
requires the `H1-CGPT-N8N-Inbound-Auth` header-auth credential. That is
the exact point at which this lane's local, offline, credential-free
work stops. Everything before that point (schema/request-shape
validation, extraction-safety rules, receipt-shape validation,
provisioning-contract review) has been completed. Nothing after that
point has been attempted, simulated-as-real, or claimed.
