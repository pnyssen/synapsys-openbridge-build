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

## What None Of These Files Do On Their Own

Committing these scripts does not configure any MCP connector or issue any
credential for this repository's own Claude Code sessions. Declaring a
server also isn't the same as it running — see "How This Actually Gets
Configured" below for the corrected mechanism, and note the earlier,
now-superseded assumption this repo's history briefly carried: `claude mcp
add --scope user`, run inside a live cloud session, does **not** work for
cloud/remote sessions — cloud sessions are fresh, ephemeral VMs each time,
and anything `claude mcp add` writes to local user config on one VM does not
survive to the next session. That was corrected once found; the project-scope
`.mcp.json` mechanism below is what's actually durable.

## How This Actually Gets Configured

Per Claude Code's own docs (`code.claude.com/docs/en/claude-code-on-the-web`,
`code.claude.com/docs/en/mcp`), cloud sessions clone `.mcp.json` from the repo
(project scope) — that's what a fresh session actually has access to, unlike
anything written by `claude mcp add --scope user`. The repo's `.mcp.json`
(root of this repository) declares both `synapsys-n8n-readonly-code` and
`synapsys-odoo-readonly-code`, each pointing at the matching read-only script
here and referencing credentials via `${VAR}` environment-variable expansion,
not hardcoded values.

Two things this repo file cannot do, still outstanding:
1. **The referenced env vars must be set in the cloud environment's own
   "Environment variables" panel** (Settings → select the environment →
   settings icon), not in a setup script — a real, filed platform bug means
   setup scripts don't see those values
   ([anthropics/claude-code#63541](https://github.com/anthropics/claude-code/issues/63541)).
   `N8N_URL`/`N8N_API_KEY` for the N8N server; `ODOO_URL`/`ODOO_DB`/
   `ODOO_LOGIN`/`ODOO_API_KEY` for the Odoo one, pending its own credential
   decision.
2. **Project-scoped servers require interactive approval** the first time a
   session uses them (`⏸ Pending approval` in `claude mcp list` until then).
   That approval step, like connector configuration generally, is not
   something this lane performs for itself.

## Status update, 2026-07-13 — both connectors confirmed working in a live cloud session

The "still outstanding" list above was accurate when written but is now
resolved. Both `synapsys-odoo-readonly-code` and `synapsys-n8n-readonly-code`
were live-verified this session in an actual `claude.ai/code` cloud session:
`count_odoo` on `res.partner` returned 63 real records; `ping_n8n` returned
`ok: true` with a valid paginated workflows response. Interactive approval
(item 2 above) turned out not to be a separate blocker in practice once the
items below were fixed.

Getting there took four independent, unrelated fixes — recorded here so
nobody has to rediscover them:

1. **`ODOO_URL` was empty/scheme-less** in the environment's Environment
   Variables panel. This fails at XML-RPC URL validation
   (`urllib.parse.urlsplit(uri).scheme not in ("http", "https")`) with the
   misleading error `unsupported XML-RPC protocol` — easy to misdiagnose as
   a proxy/transport problem (as an earlier pass on this file did), when
   it's actually pure URL validation, before any network code runs at all.
2. **`ODOO_API_KEY` and `N8N_API_KEY` held literal placeholder text**
   (`<the ...key>`-style) instead of real values, including the literal
   angle brackets — those aren't delimiters, they're stored as part of the
   value, same reason the panel's own docs warn against wrapping values in
   quotes.
3. **`fastmcp` (imported by `n8n_mcp_readonly.py`) isn't in the base cloud
   image.** Fixing this needs the cloud environment's **Setup script**
   (runs before Claude Code launches, before MCP servers spawn) — a repo-
   committed `SessionStart` hook alone runs too late to catch the first
   connection attempt on a fresh session, since MCP server spawning happens
   as part of Claude Code's own launch.
4. **A plain `pip install fastmcp` in that Setup script silently failed**
   — `fastmcp`'s `pyjwt` dependency conflicts with a Debian/apt-installed
   `PyJWT` already on the base image, and pip can't uninstall an apt-managed
   package (no RECORD file). Fix: `pip install --ignore-installed fastmcp`.
   Also: a Setup script only reruns when its own content or the allowed
   network hosts change — every session in between reuses whatever got
   cached the first time, silently including a broken install.

On item 1 in the original list above (`anthropics/claude-code#63541`): that
issue is real, but narrower than implied — it's specifically about env vars
not being visible *during the Setup script's own execution*, not about
whether a live session's MCP server subprocess can see them. In this case
the env vars were visible to the subprocess the whole time; the actual
values were just wrong (empty/scheme-less, then placeholder text).

Full diagnostic chain and receipts:
`05_AI_RETURNS_HASHED/20260713_RET_GEN_claude-code-odoo-n8n-readonly-connector-diagnosis_v0.1.md`
and
`05_AI_RETURNS_HASHED/20260713_RET_GEN_claude-code-odoo-n8n-readonly-connector-resolution_v0.1.md`.

## Both require secrets to run

Neither file has default/embedded credentials. Both fail loudly (`odoo_mcp.py`
raises on missing/invalid Odoo credentials at first call; `n8n_mcp.py` exits
at import time if `N8N_URL`/`N8N_API_TOKEN` are unset) rather than running
with silent, unintended access.
