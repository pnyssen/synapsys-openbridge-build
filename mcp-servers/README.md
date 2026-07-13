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

- **`n8n_mcp.py`** — originally committed as the file's own self-described
  REFERENCE implementation (its docstring said it "may differ" from whatever
  was actually deployed at `~/synapsys-mcp/n8n_mcp.py`). Superseded by a
  byte-for-byte copy of the actually-deployed file, supplied directly and
  independently SHA-256-verified after writing:
  `a957007bc72a871230f49d9514b9aec7cb7dfbdd5bd2811cc95381b3eba01e73`. This
  copy now matches production rather than a reference draft — the file's own
  internal docstring still carries its original "reference implementation"
  header text verbatim (untouched, since the replacement was a byte-for-byte
  content swap), so treat this README note as the current status, not that
  docstring.

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
