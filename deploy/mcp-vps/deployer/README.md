# MCP pull-based deployer (CHG-2027-093)

The VPS deploys **only what the Steward has merged to `main`**. Nothing pushes into the
server, and no AI holds a key to it.

```
Claude PR ──► Steward approves + merges ──► VPS timer pulls main ──► rebuild changed service ──► health check ──► (auto-rollback on failure)
```

## One-time setup (Steward, on the VPS)

```bash
cd /docker/mcp-src
git remote set-url origin https://github.com/pnyssen/synapsys-openbridge-build.git   # public repo: no token needed
git fetch origin main
install -m 755 deploy/mcp-vps/deployer/ss-mcp-deploy.sh /usr/local/sbin/ss-mcp-deploy
install -m 644 deploy/mcp-vps/deployer/ss-mcp-deploy.{service,timer} /etc/systemd/system/
systemctl daemon-reload
ss-mcp-deploy adopt          # records what is running now as the baseline; rebuilds nothing
ss-mcp-deploy status
systemctl enable --now ss-mcp-deploy.timer
```

From then on, every merge to `main` is deployed within about 5 minutes.

## Day to day

| Command | What it does |
|---|---|
| `ss-mcp-deploy status` | deployed SHA, `origin/main`, local edits, timer state |
| `ss-mcp-deploy run` | deploy now, instead of waiting for the timer |
| `ss-mcp-deploy rollback` | back to the previous deployed SHA and images |
| `tail /var/log/ss-mcp-deploy.log` | deploy history (SHA, services, result) |
| `systemctl disable --now ss-mcp-deploy.timer` | stop auto-deploying (containers keep running) |

## Behaviour

- **Needs a baseline.** Nothing happens until `adopt` has run.
- **Local edits block deploys.** If `/docker/mcp-src` has edits under `mcp-servers/` or `deploy/`, the deploy is held and logged.
- **Only changed services are rebuilt:**
  - `n8n_mcp.py` rebuilds `n8n-mcp`;
  - `odoo_mcp.py` rebuilds `odoo-mcp`;
  - shared modules, `requirements.txt`, `Dockerfile` and the compose file rebuild both;
  - tests and docs rebuild nothing.
- **Previous images are kept.** They're tagged `ss-prev/<service>` for rollback.
- **Health checks with auto-rollback.** A failed build or a failed `/health` check rolls back to the previous SHA and images automatically.
- **Secrets stay put.** `.env` is never read or printed. Secrets stay on the host.

## Before enabling the timer

`main` currently carries commits that have never run in production. Merge
PR #53 first: it ports the OAuth fixes running on the VPS (`4d6d332`), and without it
deploying `main` would drop them. Review what's on `main`, then `adopt` and enable.
