# N8N Viewer (read-only candidate)

`n8n_viewer.py` renders `../fixtures/n8n_viewer_snapshot.json` into
`../generated/N8N_VIEWER.html`. It makes no N8N/Odoo call and holds no
credential — all facts come from the snapshot file, which was itself built
(`../tools_build_viewer_snapshot.py`) from live `synapsys-n8n-readonly-code`
tool calls made in this candidate-build session.

Sections: overview (all 45 live workflows: identity/state/version/group),
single-workflow topology (D007 — Navigator Static Adoption Production, all
26 nodes + 25 edges, per-node authority/credential scope), execution trace
(both real executions on that workflow), security/authority surface (the
transport-auth gap independently found and filed in
`NAVIGATOR_MVP_CLAUDE_CODE_D007_WORKFLOW_VALIDATION_RETURN_v0.1.md`), and
receipts/superseded-workflow lineage.

Presentation: explicit white background / dark text, no dark-mode CSS. The
page states in its own banner that it is a temporary candidate specimen, not
the current Navigator control surface, and links back to Navigator Home.

Run: `python3 n8n_viewer.py` (from this directory or the repo root — path is
resolved relative to the script file, not the cwd).

To refresh with a new live capture: re-run the relevant
`mcp__synapsys-n8n-readonly-code__*` tool calls, update the `WORKFLOWS` /
`D007_NODES` / `D007_EDGES` literals in `../tools_build_live_fixtures.py`
(or replace that script's data-capture step with a live call if run from an
environment where those MCP tools are reachable), re-run
`../tools_build_viewer_snapshot.py`, then re-run this script.
