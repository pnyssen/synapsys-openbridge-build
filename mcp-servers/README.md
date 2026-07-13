# SynapSys MCP Servers

Reference copies of the MCP servers used to give an AI lane Odoo/N8N tool
access, committed here per the Steward-ruled full-CRUD parity grant
recorded in `CLAUDE.md`'s Capability Contract (see the "Amendment 2 —
Odoo/N8N Full CRUD Parity with Cowork" section, once merged).

## Status of each file

- **`odoo_mcp.py`** — as-supplied. Env-var-driven credentials
  (`ODOO_URL`/`ODOO_DB`/`ODOO_LOGIN`/`ODOO_API_KEY`), no hardcoded secrets.
  `execute_odoo` is a generic `execute_kw` passthrough — the broadest-privilege
  tool in the file, since it can invoke any method on any model, not just the
  named CRUD helpers.

- **`n8n_mcp.py`** — **the file's own docstring describes it as a REFERENCE
  implementation** that "may differ" from whatever is actually deployed at
  `~/synapsys-mcp/n8n_mcp.py`, and instructs whoever deploys it to diff and
  merge rather than replace wholesale. Committed here unmodified, byte-for-byte
  as supplied, specifically so that caveat travels with the file rather than
  getting lost. **Do not treat this copy as authoritative for what's actually
  running** — if the deployed version differs, that version should replace
  this one via a follow-up PR, not the other way around.

## What neither file does on its own

Committing these files does not configure any MCP connector or issue any
credential for this repository's own Claude Code sessions. That remains a
separate Steward/D007 action (`claude mcp add` against the target
environment, with its own distinct, registered credential) — per the same
"will not self-configure an MCP connector or self-issue a credential" clause
that governs this lane regardless of what capability grants exist on paper.

## Both require secrets to run

Neither file has default/embedded credentials. Both fail loudly (`odoo_mcp.py`
raises on missing/invalid Odoo credentials at first call; `n8n_mcp.py` exits
at import time if `N8N_URL`/`N8N_API_TOKEN` are unset) rather than running
with silent, unintended access.
