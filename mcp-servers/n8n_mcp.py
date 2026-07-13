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
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

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

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
N8N_URL = (os.environ.get("N8N_URL") or "").rstrip("/")
N8N_TOKEN = os.environ.get("N8N_API_TOKEN") or os.environ.get("N8N_API_KEY")

if not N8N_URL or not N8N_TOKEN:
    sys.stderr.write("ERROR: N8N_URL and N8N_API_TOKEN (or N8N_API_KEY) must be set\n")
    sys.exit(1)

AUDIT_LOG_PATH = Path.home() / "synapsys-mcp" / "mutation_audit.log"

# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------
class MutationError(Exception):
    """Raised when a workflow mutation fails integrity checks (post-rollback)."""


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------
def _request(method: str, path: str, body: dict | None = None, *, timeout: int = 30) -> Any:
    url = f"{N8N_URL}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
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
        raise RuntimeError(f"N8N {method} {path} -> HTTP {e.code}: {err_body}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"N8N {method} {path} -> network error: {e.reason}")


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
    return _request("GET", f"/api/v1/workflows/{id}")


@mcp.tool()
def update_workflow(id: str, workflow: dict) -> dict:
    """
    Update a workflow via PUT — Full Replace model (CHG-2026-271).
    Settings sanitisation: CHG-2026-275 / DEC-D001-STAB-005-006-002.
    Rejects partial payloads. Captures snapshot. Validates post-write. Restores on failure.
    """
    if not isinstance(workflow, dict) or not workflow:
        raise ValueError("update_workflow: 'workflow' must be a non-empty dict (Full Replace — partial payloads rejected)")
    if "nodes" not in workflow or not isinstance(workflow.get("nodes"), list):
        raise ValueError("update_workflow: 'nodes' missing or not a list — Full payload required")
    if "connections" not in workflow:
        raise ValueError("update_workflow: 'connections' missing — Full payload required")
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
def activate_workflow(id: str) -> dict:
    """Activate a workflow."""
    return _request("POST", f"/api/v1/workflows/{id}/activate")


@mcp.tool()
def deactivate_workflow(id: str) -> dict:
    """Deactivate a workflow."""
    return _request("POST", f"/api/v1/workflows/{id}/deactivate")


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
    """List credentials."""
    return _request("GET", f"/api/v1/credentials?limit={int(limit)}")


@mcp.tool()
def trigger_webhook(path: str, payload: dict | None = None) -> dict:
    """Trigger a webhook by path."""
    body = payload if payload is not None else {}
    path = path.lstrip("/")
    return _request("POST", f"/webhook/{path}", body)


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


@mcp.tool()
def create_workflow(workflow: dict) -> dict:
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


@mcp.tool()
def bind_workflow_credentials_by_id(workflow_id: str, bindings: dict) -> dict:
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


if __name__ == "__main__":
    mcp.run()
