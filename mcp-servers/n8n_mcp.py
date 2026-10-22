#!/usr/bin/env python3
"""
synapsys-n8n MCP server — v1.1
================================
CHG-2026-271 / DEC-D001-MCP-ISSUE4-002 — Full Replace model for update_workflow.

This is a REFERENCE implementation. The actual ~/synapsys-mcp/n8n_mcp.py may
differ in framework choice, auth pattern, helper structure, or tool decorators.
Before deploying, DIFF this against the existing file and merge only the parts
that fix the destructive-merge defect (the new update_workflow + the
_strip_forbidden, _identify_critical, _audit helpers).

Issue 4 defect (CHG-2026-269 evidence):
  Previous update_workflow performed an unsafe partial merge that silently
  removed unmodified nodes (W7 — Log Exception, W7 — Write to Odoo, Respond —
  Error all lost; node count 26 -> 24). MCP returned success despite the loss.

Issue 4 fix (this version):
  - update_workflow REQUIRES a full payload (nodes + connections present).
  - A snapshot is captured BEFORE the PUT.
  - The PUT is a Full Replace (no merge logic, no node-level mutation, no
    payload transformation beyond stripping N8N-forbidden top-level keys).
  - After the PUT, the live workflow is fetched and structurally validated:
    node count, node-name set, and critical-path preservation.
  - On ANY integrity failure, the snapshot is pushed back via PUT (rollback)
    and a MutationError is raised. No silent corruption.
  - All mutations are audit-logged to ~/synapsys-mcp/mutation_audit.log.

Behavioural compatibility:
  - All other tools (ping_n8n, list_workflows, get_workflow, activate_workflow,
    deactivate_workflow, list_executions, get_execution, list_credentials,
    trigger_webhook) are unchanged in interface.
  - Only update_workflow's contract has changed: it now REJECTS partial
    payloads (was previously: tolerated and merged silently).

Deployment: see CHG-2026-271-deployment-runbook.md in outputs.

Transport (added — network-hosted deployment candidate, not yet deployed):
  MCP_TRANSPORT=stdio (default, unchanged behaviour) or MCP_TRANSPORT=http.
  HTTP mode requires MCP_AUTH_TOKEN and uses FastMCP's own streamable-http
  transport (spec-compliant, unlike odoo_mcp.py's simplified HTTP mode — see
  mcp-servers/README.md). Also reads MCP_HOST/MCP_PORT/MCP_PUBLIC_URL/
  MCP_ALLOWED_HOSTS/MCP_ALLOWED_ORIGINS/MCP_HTTP_TRANSPORT.
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
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
import _write_safety as ws  # noqa: E402

# ---------------------------------------------------------------------------
# MCP framework — FastMCP. The existing file may use a different import path
# (mcp.server.fastmcp.FastMCP vs fastmcp.FastMCP). Match what the existing
# file uses; only the update_workflow body needs the new logic.
# ---------------------------------------------------------------------------
try:
    from fastmcp import FastMCP
except ImportError:
    from mcp.server.fastmcp import FastMCP  # type: ignore

mcp = FastMCP("synapsys-n8n")


@mcp.custom_route("/health", methods=["GET"])
async def _health(request):
    from starlette.responses import PlainTextResponse

    return PlainTextResponse("ok")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
N8N_URL = (os.environ.get("N8N_URL") or "").rstrip("/")
N8N_TOKEN = os.environ.get("N8N_API_TOKEN") or os.environ.get("N8N_API_KEY")

if not N8N_URL or not N8N_TOKEN:
    sys.stderr.write("ERROR: N8N_URL and N8N_API_TOKEN (or N8N_API_KEY) must be set\n")
    sys.exit(1)

AUDIT_LOG_PATH = Path.home() / "synapsys-mcp" / "mutation_audit.log"
TRACE_LOG_PATH = Path.home() / "synapsys-mcp" / "mutation_trace.log"


def _trace_sink(event: dict) -> None:
    """P1 trace-emission contract (RELEASE_D007_SYNAPSYS_MCP_FFE_MUTATION_SAFETY_
    ENFORCEMENT_V1, group B): append one structured event per mutating tool call
    covering tool/target/consent_classes/timestamps/result/refusal_reason.
    Never raises — a trace-sink failure must not block or alter the underlying
    mutation's own success/failure semantics (mirrors _audit()'s own contract)."""
    try:
        TRACE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(TRACE_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, default=str) + "\n")
    except Exception:
        pass

# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------
class MutationError(Exception):
    """Raised when a workflow mutation fails integrity checks (post-rollback)."""


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------
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


def _request(
    method: str,
    path: str,
    body: dict | None = None,
    *,
    timeout: float = 30,
    deadline: float | None = None,
    extra_headers: dict[str, str] | None = None,
) -> Any:
    """HTTP helper. ``timeout`` bounds each socket operation (connect, each
    recv); ``deadline``, if given, is a hard cap in seconds on reading the
    response body as a whole. Every transport failure surfaces as a
    RuntimeError naming the method and path."""
    url = f"{N8N_URL}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    req.add_header("X-N8N-API-KEY", N8N_TOKEN)
    for _header, _value in (extra_headers or {}).items():
        req.add_header(_header, _value)
    # A mutation whose response is lost may still have been applied.
    unknown = (
        "" if method == "GET"
        else "; the request was sent, so the change MAY have been applied -- re-read before retrying"
    )
    deadline_at = time.monotonic() + deadline if deadline is not None else None
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = _read_body(resp, deadline_at)
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8", errors="replace")
        except Exception:
            err_body = ""
        raise RuntimeError(f"N8N {method} {path} -> HTTP {e.code}: {err_body}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"N8N {method} {path} -> network error: {e.reason}")
    except _DeadlineExceeded:
        raise RuntimeError(
            f"N8N {method} {path} -> exceeded the {deadline}s total deadline reading the "
            f"response body (payload too large or too slow to stream){unknown}"
        )
    except TimeoutError:
        # A read-phase timeout (urlopen() connected, but a recv while reading
        # the body exceeded `timeout`) is raised directly, NOT wrapped as
        # URLError, so it needs its own clause.
        raise RuntimeError(
            f"N8N {method} {path} -> no data for {timeout}s while reading the response "
            f"body (stalled, or too large/slow to stream){unknown}"
        )
    except (http.client.HTTPException, OSError) as e:
        # Connection closed or reset mid-body (IncompleteRead,
        # ConnectionResetError, ...) or a malformed status line.
        raise RuntimeError(
            f"N8N {method} {path} -> connection dropped mid-response "
            f"({type(e).__name__}: {e}){unknown}"
        )
    return _decode_json(method, path, payload)


# ---------------------------------------------------------------------------
# Workflow PUT helpers — Issue 4 fix
# ---------------------------------------------------------------------------
FORBIDDEN_KEYS: tuple[str, ...] = (
    "id",
    "versionId",
    "createdAt",
    "updatedAt",
    "triggerCount",
    "tags",
    "pinData",
    "meta",
    "shared",
    "active",
    "isArchived",
    "projectId",
    "usedCredentials",
    "homeProject",
    "scopes",
)


def _strip_forbidden(workflow: dict) -> dict:
    """Return a shallow copy of workflow without N8N-forbidden top-level keys."""
    return {k: v for k, v in workflow.items() if k not in FORBIDDEN_KEYS}


def _identify_critical(workflow: dict) -> set[str]:
    """
    Identify nodes whose loss would constitute a critical-path regression.

    Heuristic — flagged as 'critical':
      - Any node whose name contains 'W7' (W7 emission path)
      - Any node whose name contains 'Exception' (exception handlers)
      - Any node whose name contains 'Respond' (response/error endpoints)
      - Any node whose parameters reference 'x_ss_w7_exception' (write target)
    """
    critical: set[str] = set()
    for node in workflow.get("nodes", []):
        name = node.get("name", "") or ""
        try:
            params_text = json.dumps(node.get("parameters", {}), default=str)
        except Exception:
            params_text = ""
        if (
            "W7" in name
            or "Exception" in name
            or "Respond" in name
            or "x_ss_w7_exception" in params_text
        ):
            critical.add(name)
    return critical


def _audit(event: dict) -> None:
    """Append a structured event to the mutation audit log. Never raises."""
    try:
        AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        event = dict(event)
        event["timestamp"] = datetime.utcnow().isoformat() + "Z"
        with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, default=str) + "\n")
    except Exception:
        pass


def _node_name_set(workflow: dict) -> set[str]:
    return {str(n.get("name", "")) for n in workflow.get("nodes", [])}


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------
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
    """List N8N workflows with optional filters.

    CLAUDE-LIST-WORKFLOWS-FRICTION-FIX-20260711: N8N's list endpoint returns
    each workflow's full nodes+connections body regardless of `limit`, which
    made even limit=5 return ~180KB. Summarised by default now (id, name,
    active, tags, nodeCount, createdAt, updatedAt, isArchived). Pass
    full=True for N8N's raw per-item bodies, or use get_workflow(id) for one
    workflow's complete definition. Read-only change; no N8N mutation.
    """
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
        "_note": "Pass full=True for raw N8N bodies (nodes+connections per item), or get_workflow(id) for one workflow's complete definition.",
    }


@mcp.tool()
def get_workflow(id: str) -> dict:
    """Get a workflow's full JSON."""
    return _request("GET", f"/api/v1/workflows/{_path_id(id, 'workflow id')}")


def _update_workflow_core(id: str, workflow: dict) -> dict:
    """Exact, unchanged body of update_workflow (CHG-2026-271 Full Replace +
    CHG-2026-275 settings sanitisation). Renamed, not rewritten, so the
    D007 group-B trace/consent envelope below wraps this call without
    altering its control flow — no regression to this behaviour or to
    PR35's get_execution_summary, which does not go through this path."""
    if not isinstance(workflow, dict) or not workflow:
        raise ValueError("update_workflow: 'workflow' must be a non-empty dict (Full Replace — partial payloads rejected)")
    if "nodes" not in workflow or not isinstance(workflow.get("nodes"), list):
        raise ValueError("update_workflow: 'nodes' missing or not a list — Full payload required")
    if "connections" not in workflow:
        raise ValueError("update_workflow: 'connections' missing — Full payload required")
    id = _path_id(id, "workflow id")
    # Snapshot
    snapshot = get_workflow(id)
    snap_node_count = len(snapshot.get("nodes", []))
    snap_critical = _identify_critical(snapshot)
    # Build PUT payload
    payload = _strip_forbidden(dict(workflow))
    payload.setdefault("name", snapshot.get("name", "Untitled"))
    payload.setdefault("settings", snapshot.get("settings", {}) or {})
    expected_node_count = len(workflow["nodes"])
    expected_name_set = {str(n.get("name", "")) for n in workflow["nodes"]}
    # --- SETTINGS SANITISATION (CHG-2026-275 / DEC-D001-STAB-005-006-002) ---
    ALLOWED_SETTINGS = {"executionOrder"}
    original_settings_keys = []
    retained_settings_keys = []
    removed_settings_keys = []
    if "settings" in payload and isinstance(payload["settings"], dict):
        original_settings_keys = list(payload["settings"].keys())
        sanitised_settings = {}
        for k, v in payload["settings"].items():
            if k in ALLOWED_SETTINGS:
                sanitised_settings[k] = v
                retained_settings_keys.append(k)
            else:
                removed_settings_keys.append(k)
        payload["settings"] = sanitised_settings
    # --- END SETTINGS SANITISATION ---
    # PUT
    try:
        result = _request("PUT", f"/api/v1/workflows/{id}", payload)
    except Exception as e:
        try:
            _request("PUT", f"/api/v1/workflows/{id}", _strip_forbidden(dict(snapshot)))
            _audit({"tool": "update_workflow", "workflow_id": id, "node_count_before": snap_node_count,
                    "node_count_after": snap_node_count, "result": "put_failed_restored",
                    "rollback_triggered": True, "error": str(e), "cr_reference": "CHG-2026-271",
                    "settings_keys_original": original_settings_keys,
                    "settings_keys_retained": retained_settings_keys,
                    "settings_keys_removed": removed_settings_keys})
            raise MutationError(f"PUT failed; snapshot restored: {e}")
        except MutationError:
            raise
        except Exception as restore_err:
            _audit({"tool": "update_workflow", "workflow_id": id, "node_count_before": snap_node_count,
                    "node_count_after": None, "result": "put_failed_restore_failed",
                    "rollback_triggered": True, "error": f"put: {e}; restore: {restore_err}",
                    "cr_reference": "CHG-2026-271",
                    "settings_keys_original": original_settings_keys,
                    "settings_keys_retained": retained_settings_keys,
                    "settings_keys_removed": removed_settings_keys})
            raise MutationError(f"PUT failed AND snapshot restore failed: {e} / {restore_err}")
    # Post-write validation
    post = get_workflow(id)
    post_node_count = len(post.get("nodes", []))
    post_name_set = _node_name_set(post)
    post_critical = _identify_critical(post)
    failures: list[str] = []
    if post_node_count != expected_node_count:
        failures.append(f"node count mismatch: expected={expected_node_count} got={post_node_count}")
    if post_name_set != expected_name_set:
        missing = sorted(expected_name_set - post_name_set)
        added = sorted(post_name_set - expected_name_set)
        failures.append(f"node-name divergence: missing={missing} added={added}")
    expected_critical = snap_critical & expected_name_set
    lost_critical = expected_critical - post_critical
    if lost_critical:
        failures.append(f"critical-path nodes lost: {sorted(lost_critical)}")
    if failures:
        try:
            _request("PUT", f"/api/v1/workflows/{id}", _strip_forbidden(dict(snapshot)))
            _audit({"tool": "update_workflow", "workflow_id": id, "node_count_before": snap_node_count,
                    "node_count_after": post_node_count, "result": "integrity_failed_restored",
                    "rollback_triggered": True, "failures": failures, "cr_reference": "CHG-2026-271",
                    "settings_keys_original": original_settings_keys,
                    "settings_keys_retained": retained_settings_keys,
                    "settings_keys_removed": removed_settings_keys})
            raise MutationError(f"Post-write integrity failure; snapshot restored: {'; '.join(failures)}")
        except MutationError:
            raise
        except Exception as restore_err:
            _audit({"tool": "update_workflow", "workflow_id": id, "node_count_before": snap_node_count,
                    "node_count_after": post_node_count, "result": "integrity_failed_restore_failed",
                    "rollback_triggered": True, "failures": failures + [f"restore: {restore_err}"],
                    "cr_reference": "CHG-2026-271",
                    "settings_keys_original": original_settings_keys,
                    "settings_keys_retained": retained_settings_keys,
                    "settings_keys_removed": removed_settings_keys})
            raise MutationError(f"Integrity failed AND restore failed: {failures}; restore err: {restore_err}")
    # Success
    _audit({"tool": "update_workflow", "workflow_id": id, "node_count_before": snap_node_count,
            "node_count_after": post_node_count, "result": "success",
            "rollback_triggered": False, "cr_reference": "CHG-2026-271",
            "settings_keys_original": original_settings_keys,
            "settings_keys_retained": retained_settings_keys,
            "settings_keys_removed": removed_settings_keys})
    return result


@mcp.tool()
def update_workflow(id: str, workflow: dict) -> dict:
    """
    Update a workflow via PUT — Full Replace model (CHG-2026-271).
    Settings sanitisation: CHG-2026-275 / DEC-D001-STAB-005-006-002.
    Rejects partial payloads. Captures snapshot. Validates post-write. Restores on failure.

    D007 group-B trace/consent envelope (RELEASE_D007_SYNAPSYS_MCP_FFE_MUTATION_
    SAFETY_ENFORCEMENT_V1): wraps the above, unchanged, behaviour with one
    CONFIGURATION_RUNTIME_MUTATION trace event; does not alter its control flow.
    """
    return ws.with_trace_envelope(
        tool="update_workflow", consent_classes=[ws.CONSENT_CONFIGURATION_RUNTIME_MUTATION],
        target=f"workflow:{id}", trace_sink=_trace_sink,
        fn=lambda: _update_workflow_core(id, workflow),
    )


@mcp.tool()
def activate_workflow(id: str) -> dict:
    """Activate a workflow."""
    # id is validated inside the envelope so a rejected id is still traced.
    return ws.with_trace_envelope(
        tool="activate_workflow", consent_classes=[ws.CONSENT_CONFIGURATION_RUNTIME_MUTATION],
        target=f"workflow:{id}", trace_sink=_trace_sink,
        fn=lambda: _request("POST", f"/api/v1/workflows/{_path_id(id, 'workflow id')}/activate"),
    )


@mcp.tool()
def deactivate_workflow(id: str) -> dict:
    """Deactivate a workflow."""
    # id is validated inside the envelope so a rejected id is still traced.
    return ws.with_trace_envelope(
        tool="deactivate_workflow", consent_classes=[ws.CONSENT_CONFIGURATION_RUNTIME_MUTATION],
        target=f"workflow:{id}", trace_sink=_trace_sink,
        fn=lambda: _request("POST", f"/api/v1/workflows/{_path_id(id, 'workflow id')}/deactivate"),
    )


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
    """List credentials."""
    return _request("GET", f"/api/v1/credentials?limit={int(limit)}")


# ---------------------------------------------------------------------------
# CHG-2027-088 — server-held webhook auth profiles for header-protected
# webhooks (e.g. W15-CR1 dispatch-submit / dispatch-complete).
# Callers pass only a profile NAME; the header name/value live in this
# server's environment and never cross the tool boundary, logs or traces.
#   N8N_WEBHOOK_AUTH_PROFILES=w15_dispatch
#   N8N_WEBHOOK_AUTH_W15_DISPATCH_HEADER=<header name>
#   N8N_WEBHOOK_AUTH_W15_DISPATCH_VALUE=<header value>
#   N8N_WEBHOOK_AUTH_W15_DISPATCH_PATHS=dispatch-submit,dispatch-route,dispatch-complete
# A profile only works for its allowlisted paths. No profile = unchanged.
# ---------------------------------------------------------------------------
class WebhookAuthError(Exception):
    """Profile unknown, incomplete, or not bound to the requested path."""


# Headers _request() sets itself; a profile must never override them (in
# particular X-N8N-API-KEY, which would swap the server's API credential).
_RESERVED_WEBHOOK_HEADERS = frozenset({"x-n8n-api-key", "content-type", "accept", "host", "content-length"})
_HEADER_NAME_RE = re.compile(r"^[!#$%&'*+.^_`|~0-9A-Za-z-]+$")


def _load_webhook_auth_profile(name: str) -> dict:
    enabled = {p.strip().lower() for p in os.environ.get("N8N_WEBHOOK_AUTH_PROFILES", "").split(",") if p.strip()}
    key = (name or "").strip().lower()
    if not key or key not in enabled:
        raise WebhookAuthError(f"AUTH_PROFILE_UNKNOWN: '{name}' is not an enabled profile")
    prefix = f"N8N_WEBHOOK_AUTH_{key.upper()}_"
    header = os.environ.get(prefix + "HEADER", "").strip()
    value = os.environ.get(prefix + "VALUE", "")
    paths = {p.strip().strip("/") for p in os.environ.get(prefix + "PATHS", "").split(",") if p.strip()}
    if not header or not value or not paths:
        raise WebhookAuthError(f"AUTH_PROFILE_INCOMPLETE: '{name}' missing HEADER, VALUE or PATHS")
    # Validate here so http.client never raises its own "Invalid header
    # value %r" error, which would echo the secret. Never include the value.
    if (not _HEADER_NAME_RE.match(header) or header.lower() in _RESERVED_WEBHOOK_HEADERS
            or any(c in value for c in "\r\n\0")):
        raise WebhookAuthError(f"AUTH_PROFILE_INVALID: '{name}' has a reserved/invalid HEADER or invalid VALUE")
    return {"header": header, "value": value, "paths": paths}


@mcp.tool()
def trigger_webhook(path: str, payload: dict | None = None, auth_profile: str | None = None) -> dict:
    """Trigger a webhook by path.

    Optional auth_profile (CHG-2027-088): name of a server-held header-auth
    profile for header-protected webhooks. The profile must allowlist the
    path; the secret is never returned or logged.

    D007 group-B trace/consent envelope: classified DATA_MUTATION (it
    invokes a workflow's execution, not n8n's own configuration state, but
    the workflow it triggers may itself mutate operational data downstream)."""
    body = payload if payload is not None else {}
    clean_path = path.lstrip("/")
    extra = None
    target = f"webhook:{clean_path}"
    if auth_profile:
        prof = _load_webhook_auth_profile(auth_profile)
        if clean_path.rstrip("/") not in prof["paths"]:
            raise WebhookAuthError(
                f"AUTH_PATH_NOT_ALLOWED: profile '{auth_profile}' is not bound to '{clean_path}'")
        extra = {prof["header"]: prof["value"]}
        target = f"webhook:{clean_path}|auth_profile:{auth_profile.strip().lower()}"
    if extra is None:
        call = lambda: _request("POST", f"/webhook/{clean_path}", body)
    else:
        call = lambda: _request("POST", f"/webhook/{clean_path}", body, extra_headers=extra)
    return ws.with_trace_envelope(
        tool="trigger_webhook", consent_classes=[ws.CONSENT_DATA_MUTATION],
        target=target, trace_sink=_trace_sink, fn=call,
    )


# ---------------------------------------------------------------------------
# CHG-2026-400 / STWD-MCP-CREATE-WORKFLOW-PATCH-AUTHORITY-v0.1
# Add create_workflow tool per prior STWD §5 design intent and §6 safety rules.
# Safety: inactive by default ; no credential binding ; no secret returned ;
# no activation ; no Odoo calls ; explicit id returned ; audit logged ;
# rollback via DELETE /api/v1/workflows/{id} (delete_workflow helper NOT
# added under this packet — separately authorised packet required).
# ---------------------------------------------------------------------------

# Keys n8n rejects on workflow create (POST /api/v1/workflows) and / or that
# violate the safety contract: never set on create. Mirrors FORBIDDEN_KEYS
# in spirit but tuned for the create endpoint specifically.
CREATE_REJECTED_KEYS: tuple[str, ...] = (
    "id",
    "active",
    "tags",
    "createdAt",
    "updatedAt",
    "versionId",
    "meta",
    "pinData",
    "staticData",
    "triggerCount",
    "shared",
    "isArchived",
    "projectId",
    "usedCredentials",
    "homeProject",
    "scopes",
    "credentials",  # explicit: never bind credentials by name on create
)


def _create_workflow_core(workflow: dict) -> dict:
    """
    Create a NEW n8n workflow (inactive by default).

    Inputs:
        workflow: dict
            name (str, required) — workflow display name
            nodes (list, default []) — node definitions
            connections (dict, default {}) — connection graph
            settings (dict, default {}) — only keys in ALLOWED_CREATE_SETTINGS retained
            tags (optional, dropped on create — n8n rejects on POST)

    Safety guarantees:
        - active=false enforced ; create_workflow cannot activate
        - no credential binding by name ; "credentials" stripped from body
        - no secret returned ; output limited to id/name/active/createdAt/receipt fields
        - no activation ; use activate_workflow separately under explicit authority
        - no Odoo call ; this tool never invokes Odoo
        - audit logged to mutation_audit.log

    Returns:
        {
            id, name, active(=False), createdAt,
            activation_performed: False,
            secrets_returned: False,
            rollback: "DELETE /api/v1/workflows/{id}"
        }

    Authority: STWD-MCP-CREATE-WORKFLOW-PATCH-AUTHORITY-v0.1 (CHG-2026-400).
    """
    if not isinstance(workflow, dict):
        raise ValueError("create_workflow: 'workflow' must be a dict")
    name = workflow.get("name")
    if not name or not isinstance(name, str):
        raise ValueError("create_workflow: 'name' is required and must be a non-empty string")

    # Build minimal-safe body
    nodes_in = workflow.get("nodes", [])
    if not isinstance(nodes_in, list):
        nodes_in = []
    connections_in = workflow.get("connections", {})
    if not isinstance(connections_in, dict):
        connections_in = {}

    body: dict = {
        "name": name,
        "nodes": nodes_in,
        "connections": connections_in,
        "settings": {},
    }

    # Settings sanitisation — mirror update_workflow ALLOWED_SETTINGS (CHG-2026-275)
    ALLOWED_CREATE_SETTINGS = {"executionOrder"}
    settings_in = workflow.get("settings", {})
    if isinstance(settings_in, dict):
        for k, v in settings_in.items():
            if k in ALLOWED_CREATE_SETTINGS:
                body["settings"][k] = v

    # Strip every CREATE_REJECTED_KEY from any source location ; never bind credentials
    for k in CREATE_REJECTED_KEYS:
        body.pop(k, None)

    # POST to n8n create endpoint
    try:
        result = _request("POST", "/api/v1/workflows", body)
    except Exception as e:
        _audit({
            "tool": "create_workflow",
            "name": name,
            "result": "create_failed",
            "error": str(e),
            "cr_reference": "CHG-2026-400",
        })
        raise

    if not isinstance(result, dict):
        result = {}

    wf_id = result.get("id")
    wf_active = bool(result.get("active", False))

    _audit({
        "tool": "create_workflow",
        "name": name,
        "workflow_id": wf_id,
        "active": wf_active,
        "result": "success",
        "cr_reference": "CHG-2026-400",
    })

    return {
        "id": wf_id,
        "name": result.get("name"),
        "active": wf_active,
        "createdAt": result.get("createdAt"),
        "activation_performed": False,
        "secrets_returned": False,
        "rollback": f"DELETE /api/v1/workflows/{wf_id}" if wf_id else "rollback unavailable: id not returned",
    }


@mcp.tool()
def create_workflow(workflow: dict) -> dict:
    """Create a NEW n8n workflow (inactive by default). See _create_workflow_core
    for the full contract (CHG-2026-400 / STWD-MCP-CREATE-WORKFLOW-PATCH-AUTHORITY-v0.1).

    D007 group-B trace/consent envelope: wraps the above, unchanged, behaviour
    with one CONFIGURATION_RUNTIME_MUTATION trace event."""
    return ws.with_trace_envelope(
        tool="create_workflow", consent_classes=[ws.CONSENT_CONFIGURATION_RUNTIME_MUTATION],
        target=f"workflow:{workflow.get('name')}", trace_sink=_trace_sink,
        fn=lambda: _create_workflow_core(workflow),
    )


# ---------------------------------------------------------------------------
# STWD-H1-MCP-BIND-WORKFLOW-CREDENTIALS-BY-ID-PATCH-AUTHORITY-v0.1 (additive)
# Narrow, safety-bounded credential-reference binding for INACTIVE workflows.
# Binds {id, name} references only ; never reads/returns secrets ; never activates.
# ---------------------------------------------------------------------------
BIND_REJECTED_KEYS: tuple[str, ...] = (
    "data", "token", "password", "secret", "value",
    "headervalue", "apikey", "key", "accesstoken", "clientsecret",
)


def _bind_scan_reject(obj: Any, path: str = "bindings") -> None:
    """Reject any secret-like field anywhere in the bindings input (defence in depth)."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if str(k).lower() in BIND_REJECTED_KEYS:
                raise ValueError(f"bind_workflow_credentials_by_id: secret-like field '{k}' rejected at {path}")
            _bind_scan_reject(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _bind_scan_reject(v, f"{path}[{i}]")


def _bind_workflow_credentials_by_id_core(workflow_id: str, bindings: dict) -> dict:
    """
    Bind credential REFERENCES (id + name only) to nodes of an INACTIVE workflow.

    bindings = { "<node_name>": { "<credential_type>": {"id": "<id>", "name": "<name>"} } }

    Safety (STWD-H1-MCP-BIND-WORKFLOW-CREDENTIALS-BY-ID-PATCH-AUTHORITY-v0.1):
      - rejects active workflows ; binds inactive only
      - accepts credential references only as {id, name}
      - rejects any secret/data/token/password/header-value field
      - never reads or returns credential secret values
      - never activates ; delegates the write to update_workflow (which strips 'active')
      - changes only node 'credentials' references ; all other content preserved
      - returns before/after credential-reference metadata only
      - snapshot + restore-on-failure inherited from update_workflow
    """
    import copy

    if not isinstance(workflow_id, str) or not workflow_id:
        raise ValueError("bind_workflow_credentials_by_id: 'workflow_id' must be a non-empty string")
    if not isinstance(bindings, dict) or not bindings:
        raise ValueError("bind_workflow_credentials_by_id: 'bindings' must be a non-empty dict of node_name -> {credential_type: {id,name}}")

    # Reject secret-like fields anywhere in bindings
    _bind_scan_reject(bindings)

    # Validate each ref is exactly {id, name} with id present
    for node_name, creds in bindings.items():
        if not isinstance(creds, dict) or not creds:
            raise ValueError(f"bind_workflow_credentials_by_id: binding for node '{node_name}' must be a non-empty dict")
        for ctype, ref in creds.items():
            if not isinstance(ref, dict) or (set(ref.keys()) - {"id", "name"}):
                raise ValueError(f"bind_workflow_credentials_by_id: credential ref {node_name}.{ctype} must contain only 'id' and 'name'")
            if not ref.get("id"):
                raise ValueError(f"bind_workflow_credentials_by_id: credential ref {node_name}.{ctype} missing 'id'")

    # Snapshot via GET ; reject active workflows
    snapshot = get_workflow(workflow_id)
    if snapshot.get("active") is True:
        raise ValueError("bind_workflow_credentials_by_id: workflow is active; this tool binds INACTIVE workflows only")

    node_by_name = {str(n.get("name", "")): n for n in snapshot.get("nodes", [])}
    missing = [nm for nm in bindings if nm not in node_by_name]
    if missing:
        raise ValueError(f"bind_workflow_credentials_by_id: nodes not found in workflow: {missing}")

    before_refs = {nm: copy.deepcopy(n.get("credentials", {})) for nm, n in node_by_name.items()}

    # Build a modified full payload: inject ONLY credential references
    new_nodes = copy.deepcopy(snapshot.get("nodes", []))
    nn_by_name = {str(n.get("name", "")): n for n in new_nodes}
    for node_name, creds in bindings.items():
        node = nn_by_name[node_name]
        node.setdefault("credentials", {})
        for ctype, ref in creds.items():
            node["credentials"][ctype] = {"id": ref["id"], "name": ref.get("name")}

    payload = {
        "name": snapshot.get("name", "Untitled"),
        "nodes": new_nodes,
        "connections": snapshot.get("connections", {}),
        "settings": snapshot.get("settings", {}) or {},
    }

    # Delegate the write — update_workflow strips 'active' (cannot activate),
    # sanitises settings, validates node integrity, and restores on failure.
    update_workflow(workflow_id, payload)

    # Post-write activation guard
    post = get_workflow(workflow_id)
    if post.get("active") is True:
        raise RuntimeError("bind_workflow_credentials_by_id: post-write activation detected (unexpected)")

    after_refs = {str(n.get("name", "")): n.get("credentials", {}) for n in post.get("nodes", [])}

    _audit({
        "tool": "bind_workflow_credentials_by_id",
        "workflow_id": workflow_id,
        "bound_nodes": list(bindings.keys()),
        "result": "success",
        "cr_reference": "STWD-H1-MCP-BIND-WORKFLOW-CREDENTIALS-BY-ID-PATCH-AUTHORITY-v0.1",
    })

    # Reference-only return (no secrets)
    return {
        "workflow_id": workflow_id,
        "active": bool(post.get("active", False)),
        "bound_nodes": [{"node": nm, "credential_types": list(c.keys())} for nm, c in bindings.items()],
        "before_refs": before_refs,
        "after_refs": after_refs,
        "secrets_returned": False,
        "activation_performed": False,
        "rollback": "re-bind prior refs from before_refs, or DELETE /api/v1/workflows/" + workflow_id,
    }


@mcp.tool()
def bind_workflow_credentials_by_id(workflow_id: str, bindings: dict) -> dict:
    """Bind credential REFERENCES (id + name only) to nodes of an INACTIVE workflow.
    See _bind_workflow_credentials_by_id_core for the full contract
    (STWD-H1-MCP-BIND-WORKFLOW-CREDENTIALS-BY-ID-PATCH-AUTHORITY-v0.1).

    D007 group-B trace/consent envelope: wraps the above, unchanged, behaviour
    with one CONFIGURATION_RUNTIME_MUTATION trace event."""
    return ws.with_trace_envelope(
        tool="bind_workflow_credentials_by_id", consent_classes=[ws.CONSENT_CONFIGURATION_RUNTIME_MUTATION],
        target=f"workflow:{workflow_id}", trace_sink=_trace_sink,
        fn=lambda: _bind_workflow_credentials_by_id_core(workflow_id, bindings),
    )


# ---------------------------------------------------------------------------
# Transport selection — added for network-hosted deployment (candidate, not
# yet deployed). Default is unchanged: stdio, spawned locally. HTTP mode
# reuses FastMCP's own http/streamable-http transport (the framework's real
# session manager, not a hand-rolled substitute) so this one is fully
# spec-compliant where odoo_mcp.py's HTTP mode is a simplified stateless
# approximation — that asymmetry is real, not an oversight, and is called
# out in mcp-servers/README.md rather than left implicit.
#
# Note on the library itself: this file imports `fastmcp` (the standalone
# PyPI package, `pip show fastmcp` — Jeremiah Lowin's actively-maintained
# superset), not `mcp.server.fastmcp` (the bare SDK's own bundled minimal
# version) — the `try/except ImportError` at the top of this file prefers
# the former when both are installed. The two have materially different
# APIs (no shared `.settings` object; auth and host/port are wired
# differently) — this port targets the standalone package's actual API,
# checked directly against the installed version rather than assumed.
# ---------------------------------------------------------------------------
def _configure_http_kwargs() -> dict:
    """Build auth + host/binding + hostname allow-list for HTTP transport.
    Returns the kwarg dict to pass to mcp.run(transport=..., **kwargs)."""
    sys.path.insert(0, str(Path(__file__).parent))
    from _bearer_auth import load_required_token  # noqa: E402
    from _azure_auth import build_combined_auth  # noqa: E402
    from _oauth_debug_middleware import OAuthErrorLoggingMiddleware  # noqa: E402
    from starlette.middleware import Middleware  # noqa: E402

    auth_token = load_required_token()
    mcp.auth = build_combined_auth(auth_token)

    host = os.environ.get("MCP_HOST", "0.0.0.0")
    port = int(os.environ.get("MCP_PORT", "8000"))

    # Required explicitly, not inferred from the library's own default
    # protection behaviour (which differs from what a bare-SDK FastMCP
    # would do, and wasn't independently confirmed this pass) — same
    # fail-closed pattern as the auth token: refuse to start rather than
    # guess at a safe default for a network-exposed, credential-bearing
    # server.
    allowed_hosts_raw = os.environ.get("MCP_ALLOWED_HOSTS", "")
    if not allowed_hosts_raw:
        sys.stderr.write(
            "ERROR: MCP_TRANSPORT=http requires MCP_ALLOWED_HOSTS (comma-separated "
            "hostnames expected in the Host header, e.g. the real deployment domain) "
            "— refusing to guess a safe default for a network-exposed server.\n"
        )
        sys.exit(1)
    allowed_hosts = [h.strip() for h in allowed_hosts_raw.split(",") if h.strip()]

    allowed_origins_raw = os.environ.get("MCP_ALLOWED_ORIGINS", "")
    allowed_origins = [o.strip() for o in allowed_origins_raw.split(",") if o.strip()] or None

    http_transport = os.environ.get("MCP_HTTP_TRANSPORT", "http")
    if http_transport not in ("http", "sse", "streamable-http"):
        sys.stderr.write(
            f"ERROR: unsupported MCP_HTTP_TRANSPORT={http_transport!r}; "
            "use 'http', 'sse', or 'streamable-http'\n"
        )
        sys.exit(1)

    return {
        "transport": http_transport,
        "host": host,
        "port": port,
        "allowed_hosts": allowed_hosts,
        "allowed_origins": allowed_origins,
        "host_origin_protection": "auto",
        "middleware": [Middleware(OAuthErrorLoggingMiddleware)],
    }


if __name__ == "__main__":
    _transport_mode = os.environ.get("MCP_TRANSPORT", "stdio")
    if _transport_mode == "stdio":
        mcp.run()
    elif _transport_mode == "http":
        mcp.run(**_configure_http_kwargs())
    else:
        sys.stderr.write(
            f"ERROR: unsupported MCP_TRANSPORT={_transport_mode!r}; use 'stdio' or 'http'\n"
        )
        sys.exit(1)
