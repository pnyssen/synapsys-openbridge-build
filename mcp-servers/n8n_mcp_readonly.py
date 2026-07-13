#!/usr/bin/env python3
"""
synapsys-n8n-readonly MCP server — v1.0
=========================================
Read-only variant of n8n_mcp.py, built for the Code (Codex/cloud) lane's
verification role per Part B of CODE_VERIFICATION_CLOSURE_PROGRAM_AND_READONLY_
AUTHORITY_CASE_v0.1.md (2026-07-13): "every Odoo/N8N gap this lane actually hit
this session was a verification need, not a write need."

Enforcement note: N8N API keys in this deployment are not natively role-scoped
(unlike Odoo's res.groups model) — the same key grants whatever the REST API
allows. Read-only here means read-only BY CONSTRUCTION: the write-capable tool
functions (update_workflow, create_workflow, activate_workflow,
deactivate_workflow, bind_workflow_credentials_by_id) are not defined in this
file at all, not merely hidden or permission-gated. There is no code path in
this process that can issue a PUT, POST, or DELETE to N8N.

Tools exposed (read-only):
  ping_n8n, list_workflows, get_workflow, list_executions, get_execution,
  list_credentials

Deliberately NOT exposed (present in the full n8n_mcp.py, omitted here):
  update_workflow, create_workflow, activate_workflow, deactivate_workflow,
  bind_workflow_credentials_by_id, trigger_webhook (webhook triggers can have
  side effects in the target workflow, so excluded from a read-only server)

Env vars required (same as full server):
  N8N_URL
  N8N_API_TOKEN or N8N_API_KEY

Can reuse the existing Code-SynapSys-N8N credential — the restriction here is
enforced by the absence of write code paths in this process, not by a
different key. If true credential-level isolation is also wanted later, issue
a distinct N8N API key/user for this specific process.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

try:
    from fastmcp import FastMCP
except ImportError:
    from mcp.server.fastmcp import FastMCP  # type: ignore

mcp = FastMCP("synapsys-n8n-readonly")

N8N_URL = (os.environ.get("N8N_URL") or "").rstrip("/")
N8N_TOKEN = os.environ.get("N8N_API_TOKEN") or os.environ.get("N8N_API_KEY")

if not N8N_URL or not N8N_TOKEN:
    sys.stderr.write("ERROR: N8N_URL and N8N_API_TOKEN (or N8N_API_KEY) must be set\n")
    sys.exit(1)


def _request(method: str, path: str, *, timeout: int = 30) -> Any:
    """GET-only HTTP helper. No body parameter exists — by construction,
    nothing calling this function can send a payload to mutate state."""
    if method != "GET":
        raise RuntimeError(f"synapsys-n8n-readonly: refused non-GET method {method!r}")
    url = f"{N8N_URL}{path}"
    req = urllib.request.Request(url, method="GET")
    req.add_header("Accept", "application/json")
    req.add_header("X-N8N-API-KEY", N8N_TOKEN)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8", errors="replace")
        except Exception:
            err_body = ""
        raise RuntimeError(f"N8N GET {path} -> HTTP {e.code}: {err_body}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"N8N GET {path} -> network error: {e.reason}")


@mcp.tool()
def ping_n8n() -> dict:
    """Connectivity and auth probe."""
    try:
        r = _request("GET", "/api/v1/workflows?limit=1")
        return {"url": N8N_URL, "ok": True, "sample_response_keys": list(r.keys()) if isinstance(r, dict) else []}
    except Exception as e:
        return {"url": N8N_URL, "ok": False, "error": str(e)}


@mcp.tool()
def list_workflows(
    active: bool | None = None,
    tags: str | None = None,
    name: str | None = None,
    limit: int = 50,
    cursor: str | None = None,
    full: bool = False,
) -> dict:
    """List N8N workflows with optional filters. Summarised by default
    (id, name, active, tags, nodeCount, timestamps); full=True for raw bodies."""
    params: list[str] = []
    if active is not None:
        params.append(f"active={'true' if active else 'false'}")
    if tags:
        params.append(f"tags={urllib.parse.quote(tags)}")
    if name:
        params.append(f"name={urllib.parse.quote(name)}")
    if limit:
        params.append(f"limit={int(limit)}")
    if cursor:
        params.append(f"cursor={urllib.parse.quote(cursor)}")
    qs = ("?" + "&".join(params)) if params else ""
    result = _request("GET", f"/api/v1/workflows{qs}")

    if full or not isinstance(result, dict):
        return result

    data = result.get("data")
    if not isinstance(data, list):
        return result

    summarised = []
    for wf in data:
        if not isinstance(wf, dict):
            continue
        summarised.append({
            "id": wf.get("id"),
            "name": wf.get("name"),
            "active": wf.get("active"),
            "tags": wf.get("tags"),
            "nodeCount": len(wf.get("nodes", []) or []),
            "createdAt": wf.get("createdAt"),
            "updatedAt": wf.get("updatedAt"),
            "isArchived": wf.get("isArchived"),
        })

    return {
        "data": summarised,
        "nextCursor": result.get("nextCursor"),
        "_summarised": True,
    }


@mcp.tool()
def get_workflow(id: str) -> dict:
    """Get a workflow's full JSON (read-only)."""
    return _request("GET", f"/api/v1/workflows/{id}")


@mcp.tool()
def list_executions(
    workflow_id: str | None = None,
    status: str | None = None,
    limit: int = 25,
    cursor: str | None = None,
) -> dict:
    """List recent executions."""
    params: list[str] = []
    if workflow_id:
        params.append(f"workflowId={urllib.parse.quote(workflow_id)}")
    if status:
        params.append(f"status={urllib.parse.quote(status)}")
    if limit:
        params.append(f"limit={int(limit)}")
    if cursor:
        params.append(f"cursor={urllib.parse.quote(cursor)}")
    qs = ("?" + "&".join(params)) if params else ""
    return _request("GET", f"/api/v1/executions{qs}")


@mcp.tool()
def get_execution(id: str, include_data: bool = False) -> dict:
    """Get a single execution."""
    suffix = "?includeData=true" if include_data else ""
    return _request("GET", f"/api/v1/executions/{id}{suffix}")


@mcp.tool()
def list_credentials(limit: int = 50) -> dict:
    """List credentials (metadata only — N8N's own API never returns secret
    values via this endpoint, read or write)."""
    return _request("GET", f"/api/v1/credentials?limit={int(limit)}")


if __name__ == "__main__":
    mcp.run()
