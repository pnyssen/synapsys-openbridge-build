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

## Both require secrets to run

Neither file has default/embedded credentials. Both fail loudly (`odoo_mcp.py`
raises on missing/invalid Odoo credentials at first call; `n8n_mcp.py` exits
at import time if `N8N_URL`/`N8N_API_TOKEN` are unset) rather than running
with silent, unintended access.

## Network (HTTP) deployment — candidate, not yet deployed

`odoo_mcp.py` and `n8n_mcp.py` (not the `*_readonly.py` variants, which are
unmodified) now support two transports, selected by `MCP_TRANSPORT`:

- `MCP_TRANSPORT=stdio` (default) — unchanged behaviour: spawned locally by
  a client over stdin/stdout, same as today.
- `MCP_TRANSPORT=http` — runs as a persistent, network-reachable process
  instead, so a Claude session anywhere (browser claude.ai, Claude Code,
  Cowork) can reach the same live Odoo/N8N access without the client
  spawning a local process on a specific machine.

Built in response to a real operational problem: local MCP server processes
running continuously on a laptop contribute to thermal/CPU load severe
enough to trigger reboots. Moving them to a persistent host removes that
local load — the actual motivating reason for this change, not a
generic "let's support HTTP" exercise.

**This is candidate code — authored, tested, not deployed.** Actually
running this on internet-facing infrastructure with live Odoo/N8N write
credentials is a platform/runtime change under this ecosystem's own
change-control rules (Configuration Lane / D007 territory), needing a CR
before real deployment — writing and testing the code itself doesn't
require that, running it against production credentials on a public host
does.

### Required environment variables (HTTP mode only, in addition to the
existing Odoo/N8N credential vars documented above)

| Variable | Required | Purpose |
|---|---|---|
| `MCP_TRANSPORT` | Yes (`http`) | Selects HTTP mode; omit or set `stdio` for unchanged local behaviour |
| `MCP_AUTH_TOKEN` | Yes | Shared bearer-token secret. Both servers refuse to start in HTTP mode without one — no accidental unauthenticated network exposure. |
| `MCP_HOST` | No (default `0.0.0.0`) | Bind address |
| `MCP_PORT` | No (default `8000`) | Bind port |
| `MCP_ALLOWED_HOSTS` | Yes, for `n8n_mcp.py` HTTP mode | Comma-separated hostnames expected in the `Host` header (e.g. the real deployment domain). Required, not defaulted — refuses to start rather than guess a safe value for a network-exposed, credential-bearing server. |
| `MCP_ALLOWED_ORIGINS` | No | Comma-separated browser origins, if browser-JS clients ever need CORS |
| `MCP_HTTP_TRANSPORT` | No | `odoo_mcp.py`: always the simplified stateless mode described below (this var isn't read by it). `n8n_mcp.py`: `http` (default), `sse`, or `streamable-http`. |

### A real asymmetry between the two servers, disclosed not hidden

- **`n8n_mcp.py`** already used `FastMCP` (the standalone `fastmcp` PyPI
  package — confirmed via `pip show fastmcp`, not the bare SDK's bundled
  `mcp.server.fastmcp`, which has a different, incompatible API). Its HTTP
  mode is the framework's own, fully spec-compliant HTTP/streamable-HTTP
  transport — real session management, not approximated.
- **`odoo_mcp.py`** was hand-rolled JSON-RPC over stdin/stdout with no MCP
  SDK involved at all. Its HTTP mode is a **simplified, stateless
  JSON-RPC-over-HTTP endpoint** (`POST /mcp`, one request in, one response
  out) built with Starlette, reusing the exact same tested dispatch
  function (`build_response()`) the stdio path already used — not a full
  spec-compliant streamable-HTTP transport with session resumability or
  server-initiated SSE push. Adequate for straightforward tool-calling use;
  a client that strictly requires the full streamable-HTTP spec would need
  a further migration onto `mcp.server.Server` +
  `StreamableHTTPSessionManager` (the same machinery FastMCP itself uses)
  — named here as the honest follow-up, not silently assumed done.

### Local smoke test (no live credentials, no deployment)

```bash
cd mcp-servers
python3 -m pytest tests/test_transport.py -v   # 32 tests, all mocked/offline
```

### What deploying this for real would still need (not done here)

1. A host to run it — a VPS/container with a persistent process and a
   stable domain, not shared/PHP-only hosting (can't run a background
   process). Confirm which Hostinger product this actually is before
   assuming a VPS is available.
2. A real secret-management decision for `ODOO_API_KEY`/`N8N_API_TOKEN`/
   `MCP_AUTH_TOKEN` once they live on a remote host instead of a local
   machine only — a genuine security-surface change, not a copy-paste.
3. TLS termination — this process serves plain HTTP; a reverse proxy
   (nginx/Caddy) or the platform's own TLS handling is expected in front of
   it, not built into these files.
4. The CR itself, with `x_test_evidence` (this test suite, plus a real
   integration smoke test once deployed) and `x_rollback_plan` (stop the
   process / revert to `MCP_TRANSPORT=stdio` — no data migration involved,
   since this changes transport only, not what the tools do).
