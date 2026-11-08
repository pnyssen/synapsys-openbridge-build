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
  get_execution_summary, list_credentials

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

import http.client
import json
import os
import re
import sys
import time
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


# --- shared with n8n_mcp.py / n8n_mcp_readonly.py: keep the two copies identical ---
_READ_CHUNK = 64 * 1024
_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_SUMMARY_MAX_TIMEOUT = 300
_SUMMARY_TEXT_LIMIT = 2000


class _DeadlineExceeded(Exception):
    """Total wall-clock deadline for one _request() call ran out."""


def _path_id(value: Any, field: str = "id") -> str:
    """Validate an N8N resource id before it is interpolated into a URL path.

    N8N workflow ids are short alphanumeric strings and execution ids are
    numeric. Anything else (``../credentials``, ``1?includeData=false``,
    ``1#``) is rejected rather than escaped: escaping would still let ``..``
    through to a proxy or server that normalises paths.
    """
    s = str(value)
    if not _ID_RE.fullmatch(s):
        raise ValueError(f"invalid N8N {field} {s!r}: expected 1-64 characters of [A-Za-z0-9_-]")
    return s


def _read_body(resp: Any, deadline_at: float | None) -> bytes:
    """Read the whole response body, enforcing an absolute monotonic deadline.

    urllib's ``timeout`` bounds each socket operation, not the whole read: a
    body that keeps trickling in can take arbitrarily long. With a deadline,
    the socket timeout is narrowed to the time remaining before every chunk,
    so no single recv can run past it. If the socket can't be reached (a
    non-CPython response object), the overrun is bounded by one ``timeout``.
    """
    if deadline_at is None:
        return resp.read()
    # read1() returns after a single recv; read(n) would keep blocking until
    # n bytes arrive, so a slow drip could run far past the deadline.
    read = getattr(resp, "read1", resp.read)
    chunks: list[bytes] = []
    while True:
        # http.client closes the response (and its socket) itself once a
        # Content-Length body is fully read; touching that socket again
        # raises EBADF, so stop here instead.
        if getattr(resp, "isclosed", lambda: False)():
            return b"".join(chunks)
        remaining = deadline_at - time.monotonic()
        if remaining <= 0:
            raise _DeadlineExceeded()
        # Re-resolve each time: fp is None once the response has closed.
        sock = getattr(getattr(getattr(resp, "fp", None), "raw", None), "_sock", None)
        if sock is not None:
            sock.settimeout(remaining)
        try:
            chunk = read(_READ_CHUNK)
        except TimeoutError:
            if time.monotonic() >= deadline_at - 0.05:
                raise _DeadlineExceeded()
            raise
        if not chunk:
            return b"".join(chunks)
        chunks.append(chunk)


def _decode_json(method: str, path: str, payload: bytes) -> Any:
    try:
        raw = payload.decode("utf-8")
        return json.loads(raw) if raw else {}
    except ValueError as e:  # UnicodeDecodeError, json.JSONDecodeError
        snippet = payload[:200].decode("utf-8", errors="replace")
        raise RuntimeError(
            f"N8N {method} {path} -> response was not valid UTF-8 JSON "
            f"({type(e).__name__}: {e}); body starts: {snippet!r}"
        )


def _clip(value: Any) -> Any:
    if isinstance(value, str) and len(value) > _SUMMARY_TEXT_LIMIT:
        return value[:_SUMMARY_TEXT_LIMIT] + f"... [{len(value) - _SUMMARY_TEXT_LIMIT} chars clipped]"
    return value


def _summarise_error(error: Any) -> dict | None:
    """Pull the diagnostic fields N8N serialises on NodeApiError /
    NodeOperationError / WorkflowOperationError: name, message, description,
    httpCode, and the failing node. Never returns ``stack`` or ``context``."""
    if not isinstance(error, dict):
        return None
    node = error.get("node") if isinstance(error.get("node"), dict) else {}
    error_response = error.get("errorResponse")
    return {
        "node": node.get("name"),
        "nodeType": node.get("type"),
        # errorName is the pre-existing field (errorResponse.name, when N8N
        # sets it); kept as-is for callers already reading it.
        "errorName": error_response.get("name") if isinstance(error_response, dict) else None,
        "name": error.get("name"),
        "message": _clip(error.get("message")),
        "description": _clip(error.get("description")),
        "httpCode": error.get("httpCode"),
    }


def _summarise_execution(raw: Any, id: str) -> dict:
    if not isinstance(raw, dict):
        return {"id": id, "error": "unexpected response shape from N8N"}

    data = raw.get("data") if isinstance(raw.get("data"), dict) else {}
    result_data = data.get("resultData") if isinstance(data.get("resultData"), dict) else {}
    run_data = result_data.get("runData") if isinstance(result_data.get("runData"), dict) else {}

    nodes = []
    for node_name, runs in run_data.items():
        if not isinstance(runs, list):
            continue
        for run in runs:
            if not isinstance(run, dict):
                continue
            node_error = run.get("error")
            status = run.get("executionStatus")
            if status is None and node_error:
                # Older N8N versions omit executionStatus; a run-level error
                # is the only failure signal there.
                status = "error"
            start = run.get("startTime")
            nodes.append({
                "node": node_name,
                "status": status,
                "executionTimeMs": run.get("executionTime"),
                "startTime": start if isinstance(start, (int, float)) else None,
                "error": _summarise_error(node_error),
            })
    nodes.sort(key=lambda n: (n["startTime"] is None, n["startTime"] or 0))

    return {
        "id": raw.get("id", id),
        "status": raw.get("status"),
        "finished": raw.get("finished"),
        "mode": raw.get("mode"),
        "workflowId": raw.get("workflowId"),
        "startedAt": raw.get("startedAt"),
        "stoppedAt": raw.get("stoppedAt"),
        "lastNodeExecuted": result_data.get("lastNodeExecuted"),
        "nodeCount": len(nodes),
        "nodes": nodes,
        "error": _summarise_error(result_data.get("error")),
    }
# --- end shared helpers ---


def _request(method: str, path: str, *, timeout: float = 30, deadline: float | None = None) -> Any:
    """GET-only HTTP helper. No body parameter exists — by construction,
    nothing calling this function can send a payload to mutate state.

    ``timeout`` bounds each socket operation (connect, each recv);
    ``deadline``, if given, is a hard cap in seconds on reading the response
    body as a whole. Every transport failure surfaces as a RuntimeError."""
    if method != "GET":
        raise RuntimeError(f"synapsys-n8n-readonly: refused non-GET method {method!r}")
    url = f"{N8N_URL}{path}"
    req = urllib.request.Request(url, method="GET")
    req.add_header("Accept", "application/json")
    req.add_header("X-N8N-API-KEY", N8N_TOKEN)
    deadline_at = time.monotonic() + deadline if deadline is not None else None
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = _read_body(resp, deadline_at)
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8", errors="replace")
        except Exception:
            err_body = ""
        raise RuntimeError(f"N8N GET {path} -> HTTP {e.code}: {err_body}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"N8N GET {path} -> network error: {e.reason}")
    except _DeadlineExceeded:
        raise RuntimeError(
            f"N8N GET {path} -> exceeded the {deadline}s total deadline reading the "
            f"response body (payload too large or too slow to stream)"
        )
    except TimeoutError:
        # A read-phase timeout (urlopen() connected, but a recv while reading
        # the body exceeded `timeout`) is raised directly, NOT wrapped as
        # URLError, so it needs its own clause.
        raise RuntimeError(
            f"N8N GET {path} -> no data for {timeout}s while reading the response "
            f"body (stalled, or too large/slow to stream)"
        )
    except (http.client.HTTPException, OSError) as e:
        # Connection closed or reset mid-body (IncompleteRead,
        # ConnectionResetError, ...) or a malformed status line.
        raise RuntimeError(
            f"N8N GET {path} -> connection dropped mid-response ({type(e).__name__}: {e})"
        )
    return _decode_json("GET", path, payload)


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
    return _request("GET", f"/api/v1/workflows/{_path_id(id, 'workflow id')}")


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
    return _request("GET", f"/api/v1/executions/{_path_id(id, 'execution id')}{suffix}")


@mcp.tool()
def get_execution_summary(id: str, timeout: int = 50) -> dict:
    """Get a single execution's per-node timing/status/error summary,
    without the full node input/output payloads.

    Returns per-node name/status/executionTime/startTime (plus any node-level
    error), and the top-level error (node, type, name, message, description,
    httpCode) if the execution failed. Node input/output bodies are never
    returned, and error text is clipped to 2000 characters.

    N8N's API has no way to fetch run metadata without the payloads, so this
    tool still downloads and parses the full includeData=true response
    internally -- it shrinks what the caller receives, not what the server
    transfers or holds in memory while summarising.

    `timeout` (1-300 seconds) is a TOTAL deadline for reading the response,
    measured from the start of the request, not a per-read idle timeout. Each
    network wait (connect, waiting for headers) is also capped at `timeout`,
    so only a slow connect followed by a slow first byte can push the call
    past it, to at most 2x `timeout`. The default of 50s is chosen to finish
    inside the ~60s tool-call limit common in MCP clients; raise it only if your
    client allows longer calls, otherwise the client gives up first and you
    get an opaque transport timeout instead of this tool's clear error.
    """
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not 1 <= timeout <= _SUMMARY_MAX_TIMEOUT:
        raise ValueError(f"timeout must be between 1 and {_SUMMARY_MAX_TIMEOUT} seconds, got {timeout!r}")
    exec_id = _path_id(id, "execution id")
    raw = _request(
        "GET", f"/api/v1/executions/{exec_id}?includeData=true",
        timeout=timeout, deadline=timeout,
    )
    return _summarise_execution(raw, exec_id)


@mcp.tool()
def list_credentials(limit: int = 50) -> dict:
    """List credentials (metadata only — N8N's own API never returns secret
    values via this endpoint, read or write)."""
    return _request("GET", f"/api/v1/credentials?limit={int(limit)}")


if __name__ == "__main__":
    mcp.run()
