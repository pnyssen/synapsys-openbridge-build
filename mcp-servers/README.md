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

- **`n8n_mcp_readonly.py`** — new, built specifically for a **read-only**
  Odoo/N8N authority request this lane filed
  (`CODE_VERIFICATION_CLOSURE_PROGRAM_AND_READONLY_AUTHORITY_CASE_v0.1.md`,
  SynapSys Working Memory), narrower than the full-CRUD parity `odoo_mcp.py`
  and `n8n_mcp.py` above already grant on paper. Read-only **by
  construction**, not by permission-gating: the write-capable tool functions
  (`update_workflow`, `create_workflow`, `activate_workflow`,
  `deactivate_workflow`, `bind_workflow_credentials_by_id`, `trigger_webhook`)
  are not defined anywhere in the file, and its one HTTP helper hard-rejects
  any non-`GET` method. Independently verified byte-for-byte by this lane
  against the copy in SynapSys Working Memory
  (`SynapSys-Control/10_SCRATCH_TRANSIT/n8n_mcp_readonly.py`), SHA-256
  `a445a6700fc5584e546f4326bd7ff509a8a8df5fc1194497cacbf93ebbb0d6ca`, exact
  match. Reported as Steward-approved for the N8N side of the read-only
  request; that approval itself was relayed, not independently confirmed by
  this lane against a filed Steward record — worth checking before treating
  it as settled. The Odoo-side counterpart is explicitly **not** ready: it's
  pending one unresolved choice (a dedicated read-only Odoo user/seat vs.
  reusing the existing full-access key with self-restraint only) that has a
  real cost implication and hasn't been decided.

- **`odoo_mcp_readonly.py`** — new, the Odoo-side counterpart to
  `n8n_mcp_readonly.py`, built the same session and for the same request,
  without waiting on the credential-provisioning decision above (the code
  doesn't depend on which credential it's eventually given). Read-only **by
  construction**: only exposes `search_odoo`/`read_odoo`/`count_odoo`/
  `search_multi`, all backed by a single `_exec_read` helper that hard-refuses
  any Odoo ORM method outside `{search_read, read, search_count}` — so
  `create_odoo`/`write_odoo`/`unlink_odoo`/`execute_odoo` (the full server's
  broadest-privilege, generic-passthrough tool) and the two batch-write tools
  are simply absent, not permission-gated. Notably weaker guarantee than the
  N8N version in one specific way, disclosed rather than glossed over: Odoo
  natively supports `res.groups`-based permission scoping and N8N does not,
  so pairing this file with an actually-restricted Odoo user is a stronger
  guarantee than code-only enforcement — that's the real tradeoff behind the
  still-open dedicated-user-vs-shared-key decision, not a merely bureaucratic
  choice. This file works correctly either way; the credential decision
  determines how strong the enforcement actually is, not whether the code
  behaves.

## What Neither Full-CRUD File Does On Its Own

Committing `odoo_mcp.py`/`n8n_mcp.py` does not configure any MCP connector or
issue any credential for this repository's own Claude Code sessions. That
remains a separate Steward/D007 action (`claude mcp add` against the target
environment, with its own distinct, registered credential) — per the same
"will not self-configure an MCP connector or self-issue a credential" clause
that governs this lane regardless of what capability grants exist on paper.
The same applies to `n8n_mcp_readonly.py`: its existence in this repo does
not itself grant this lane N8N access.

## Both require secrets to run

Neither file has default/embedded credentials. Both fail loudly (`odoo_mcp.py`
raises on missing/invalid Odoo credentials at first call; `n8n_mcp.py` exits
at import time if `N8N_URL`/`N8N_API_TOKEN` are unset) rather than running
with silent, unintended access.
