# MCP pull-based deployer (CHG-2027-093)

The VPS deploys **only what the Steward has merged to `main`**. Nothing pushes into the
server, and no AI holds a key to it.

```
Claude PR ──► Steward approves + merges ──► CI green on that SHA ──► VPS timer pulls main
          ──► rebuild changed service ──► health + source-provenance check ──► (auto-rollback on failure)
```

**Merging this deployer does not authorise deployment.** Installing it changes
nothing: `run` is a HOLD until the Steward runs `ss-mcp-deploy enable <CHG-ref>`
under an approved release, and `enable` itself refuses until a
provenance-verified baseline exists.

## One-time setup (Steward, on the VPS)

```bash
cd /docker/mcp-src
git remote set-url origin https://github.com/pnyssen/synapsys-openbridge-build.git   # public repo: no token needed
git fetch origin main
install -m 755 deploy/mcp-vps/deployer/ss-mcp-deploy.sh /usr/local/sbin/ss-mcp-deploy
install -m 644 deploy/mcp-vps/deployer/ss-mcp-deploy.{service,timer} /etc/systemd/system/
systemctl daemon-reload
ss-mcp-deploy adopt <SHA>    # refused unless the running containers' source matches <SHA>; rebuilds nothing
ss-mcp-deploy status         # must show "provenance: OK"
# Only under an approved release, after D009 assurance of the first delta:
ss-mcp-deploy enable CHG-YYYY-NNN
systemctl enable --now ss-mcp-deploy.timer
```

From then on, every merge to `main` whose required CI checks are green on that
exact commit is deployed within about 5 minutes. `ss-mcp-deploy disable` stops it.

## Day to day

| Command | What it does |
|---|---|
| `ss-mcp-deploy status` | deployed SHA, `origin/main`, local edits, auto-deploy gate, provenance, timer state |
| `ss-mcp-deploy enable CHG-…` / `disable` | open / close the release gate for `run` |
| `ss-mcp-deploy run` | deploy now, instead of waiting for the timer |
| `ss-mcp-deploy rollback` | back to the previous deployed SHA and images |
| `tail /var/log/ss-mcp-deploy.log` | deploy history (SHA, services, result) |
| `systemctl disable --now ss-mcp-deploy.timer` | stop auto-deploying (containers keep running) |

## Behaviour

Every failed gate is a **HOLD**: logged, nothing changed.

- **Off by default.** `run` does nothing until `enable <CHG-ref>`.
- **Needs a verified baseline.** `adopt <SHA>` hashes every app file inside each running
  container (`/app/*`, as the Dockerfile at `<SHA>` copies them) and records the baseline
  only if all match `<SHA>`. A VPS-only build that is not a commit on `main` cannot be adopted.
- **Divergent history holds.** If the deployed SHA is not an ancestor of `origin/main`
  (rewritten history), the deploy is refused — never a warning followed by a deploy.
- **CI must be green on the exact commit.** Required check runs (`SS_REQUIRED_CHECKS`,
  default `test` from `mcp-tests.yml`) must be `completed/success` on that SHA, read from
  the public GitHub API. Unreachable or pending = HOLD; the timer retries later.
- **Drift holds.** If the running containers no longer match the deployed SHA, the deploy is refused.
- **Local edits block deploys.** If `/docker/mcp-src` has edits under `mcp-servers/` or `deploy/`, the deploy is held and logged.
- **Only changed services are rebuilt:**
  - `n8n_mcp.py` rebuilds `n8n-mcp`;
  - `odoo_mcp.py` rebuilds `odoo-mcp`;
  - shared modules, `requirements.txt`, `Dockerfile` and the compose file rebuild both;
  - tests and docs rebuild nothing.
- **Rollback identity is recorded first.** Before anything is rebuilt, the previous SHA and
  image IDs are written to `rollback_identity` and the log, and images are tagged `ss-prev/<service>`.
- **Health and provenance checks with auto-rollback.** A failed build, a failed `/health`
  check, or containers whose source doesn't match the new SHA roll back to the previous SHA
  and images. A rollback is reported `done` only once health and provenance verify;
  otherwise it logs `ROLLBACK FAILED … manual intervention required` and exits non-zero.
- **Secrets stay put.** `.env` is never read or printed. Secrets stay on the host.

## Before enabling (release conditions)

`main` carries commits that have never run in production, and the VPS runs a local build
(`4d6d332`) that is not a commit on `main`, so `adopt` will correctly refuse it. Before `enable`:

1. Merge PR #53 (ports the VPS-only OAuth fixes, copies `_write_safety.py` into the image,
   keeps the static bearer working under Entra on FastMCP 4.x) and PR #55.
2. Under the approved release, build and start a known `main` SHA manually, then `adopt` it
   and confirm `status` shows `provenance: OK`.
3. Verify on that build: `/health`, OAuth login end-to-end, the ChatGPT connector's tool
   list (including `trigger_webhook.auth_profile`), and `rollback`.
4. Obtain D009 independent assurance of the delta, then `enable <CHG-ref>`.
