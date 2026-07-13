#!/usr/bin/env python3
"""
SynapSys Odoo MCP Server — Read-Only v1.0

Read-only variant of odoo_mcp.py, built for the Code (Codex/cloud) lane's
verification role per Part B of CODE_VERIFICATION_CLOSURE_PROGRAM_AND_READONLY_
AUTHORITY_CASE_v0.1.md (2026-07-13): "every Odoo/N8N gap this lane actually hit
this session was a verification need, not a write need."

Enforcement note: unlike odoo_mcp.py's generic execute_odoo passthrough (which
can call ANY execute_kw method, including create/write/unlink and anything
else the ORM exposes), this file only ever calls search_read / read /
search_count against Odoo's XML-RPC endpoint. Read-only here means read-only
BY CONSTRUCTION: the write-capable tool functions (create_odoo, write_odoo,
unlink_odoo, execute_odoo, create_fields_batch, create_acls_batch) are not
defined in this file at all. There is no code path in this process that can
call an Odoo write method.

Unlike N8N, Odoo natively supports role/permission scoping (res.groups on the
authenticating user) — if a genuinely enforced boundary is wanted (not just
"no write code path exists"), pairing this file with a dedicated read-only
Odoo user is the stronger guarantee. This file's own guarantee holds even
against the existing full-access credential, since it never issues a write
call regardless of what the credential is permitted to do.

Tools exposed (read-only):
  search_odoo, read_odoo, count_odoo, search_multi

Deliberately NOT exposed (present in the full odoo_mcp.py, omitted here):
  create_odoo, write_odoo, unlink_odoo, execute_odoo (generic passthrough —
  the single broadest-privilege tool in the full file, since it can invoke
  any model method, not just CRUD), create_fields_batch, create_acls_batch

Env vars required (same as full server):
  ODOO_URL      e.g. https://pnyssen-synapsys-odoo.odoo.com
  ODOO_DB       e.g. pnyssen-synapsys-odoo-production-27407175
  ODOO_LOGIN    e.g. phil@synapsys.com.au
  ODOO_API_KEY  the API key (NOT the password)

Can reuse the existing Claude-MSP or Code-SynapSys-ODOO credential — the
restriction here is enforced by the absence of write code paths in this
process, not by a different key. If true credential-level isolation is also
wanted (recommended, per this file's own note above), issue a distinct
read-only Odoo user/API key for this specific process.
"""
import sys
import json
import xmlrpc.client
import os
from typing import Any, Dict, List

ODOO_URL = os.environ.get("ODOO_URL", "")
ODOO_DB = os.environ.get("ODOO_DB", "")
ODOO_LOGIN = os.environ.get("ODOO_LOGIN", "phil@synapsys.com.au")
ODOO_API_KEY = os.environ.get("ODOO_API_KEY", "")

# ---- Connection cache (authenticate once per process) ---------------------

_cache: Dict[str, Any] = {"uid": None, "models": None, "common": None}


def odoo_connect():
    if _cache["uid"] is None:
        common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common", allow_none=True)
        uid = common.authenticate(ODOO_DB, ODOO_LOGIN, ODOO_API_KEY, {})
        if not uid:
            raise RuntimeError(
                "Odoo authentication failed. Check ODOO_URL / ODOO_DB / ODOO_LOGIN / ODOO_API_KEY env vars."
            )
        models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object", allow_none=True)
        _cache["uid"] = uid
        _cache["models"] = models
        _cache["common"] = common
    return _cache["uid"], _cache["models"]


_READ_ONLY_METHODS = {"search_read", "read", "search_count"}


def _exec_read(model: str, method: str, args: List = None, kwargs: Dict = None):
    """Execute a read-only Odoo ORM method only. Refuses anything else —
    by construction, not by convention — so even a copy-paste error can't
    smuggle a write call through this function."""
    if method not in _READ_ONLY_METHODS:
        raise RuntimeError(
            f"synapsys-odoo-readonly: refused non-read-only method {method!r} "
            f"(allowed: {sorted(_READ_ONLY_METHODS)})"
        )
    uid, models = odoo_connect()
    return models.execute_kw(
        ODOO_DB, uid, ODOO_API_KEY,
        model, method,
        args or [],
        kwargs or {},
    )


def normalize_ids(ids):
    """Coerce various id input formats to a list of integers. Same logic as
    the full server's normalize_ids — read-only concern, not a write one."""
    if ids is None:
        raise ValueError("ids required")
    if isinstance(ids, (list, tuple)):
        if not ids:
            raise ValueError("ids must not be empty")
        try:
            return [int(x) for x in ids]
        except (TypeError, ValueError) as ex:
            raise ValueError(f"ids list contains non-numeric value: {ex}")
    if isinstance(ids, int) and not isinstance(ids, bool):
        return [ids]
    if isinstance(ids, str):
        s = ids.strip()
        if not s:
            raise ValueError("ids must not be empty")
        if s.startswith("[") and s.endswith("]"):
            try:
                parsed = json.loads(s)
            except json.JSONDecodeError as ex:
                raise ValueError(f"ids string looks like a JSON array but is malformed: {ex}")
            if not isinstance(parsed, list):
                raise ValueError(f"ids JSON string did not decode to a list: {type(parsed).__name__}")
            if not parsed:
                raise ValueError("ids must not be empty")
            try:
                return [int(x) for x in parsed]
            except (TypeError, ValueError) as ex:
                raise ValueError(f"ids JSON list contains non-numeric value: {ex}")
        try:
            return [int(s)]
        except ValueError:
            raise ValueError(f"ids string is not numeric: {s!r}")
    raise TypeError(f"ids must be int / str / list / tuple ; got {type(ids).__name__}")


# ---- Tool implementations (read-only subset) -------------------------------

def tool_search_odoo(args: Dict) -> Any:
    return _exec_read(
        args["model"], "search_read",
        [args.get("domain", [])],
        {
            "fields": args.get("fields") or ["id", "name"],
            "limit": args.get("limit", 1000),
            "offset": args.get("offset", 0),
            "order": args.get("order") or False,
        },
    )


def tool_read_odoo(args: Dict) -> Any:
    ids = normalize_ids(args["ids"])
    return _exec_read(
        args["model"], "read",
        [ids],
        {"fields": args.get("fields") or []},
    )


def tool_count_odoo(args: Dict) -> Any:
    return _exec_read(
        args["model"], "search_count",
        [args.get("domain", [])],
    )


def tool_search_multi(args: Dict) -> Any:
    """Run multiple search_read queries in a single tool call. Same shape as
    the full server's search_multi — read-only, so no restriction beyond
    what _exec_read already enforces per-query."""
    queries = args["queries"]
    labels = args.get("labels")
    if labels and len(labels) != len(queries):
        raise ValueError("labels must be same length as queries")

    results = []
    for q in queries:
        try:
            r = _exec_read(
                q["model"], "search_read",
                [q.get("domain", [])],
                {
                    "fields": q.get("fields") or ["id", "name"],
                    "limit": q.get("limit", 1000),
                    "offset": q.get("offset", 0),
                    "order": q.get("order") or False,
                },
            )
            results.append({"ok": True, "model": q["model"], "records": r})
        except Exception as ex:
            results.append({"ok": False, "model": q["model"], "error": str(ex)[:300]})

    if labels:
        return {lbl: res for lbl, res in zip(labels, results)}
    return results


# ---- Tool schema ------------------------------------------------------------

TOOLS = [
    {
        "name": "search_odoo",
        "description": "Search any Odoo model (search_read, read-only). Returns list of records matching domain with requested fields.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "model": {"type": "string"},
                "domain": {"type": "array", "description": "Odoo domain, e.g. [['active','=',true]]"},
                "fields": {"type": "array", "items": {"type": "string"}},
                "limit": {"type": "integer", "default": 1000},
                "offset": {"type": "integer", "default": 0},
                "order": {"type": "string"},
            },
            "required": ["model"],
        },
    },
    {
        "name": "read_odoo",
        "description": "Read specific records by id (read-only). Faster than search_read when you know the ids.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "model": {"type": "string"},
                "ids": {"type": ["array", "integer"]},
                "fields": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["model", "ids"],
        },
    },
    {
        "name": "count_odoo",
        "description": "Return the count of records matching a domain (search_count, read-only).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "model": {"type": "string"},
                "domain": {"type": "array"},
            },
            "required": ["model"],
        },
    },
    {
        "name": "search_multi",
        "description": (
            "Run multiple search_read queries in one tool call (read-only). Use when fetching state from "
            "3+ models (preflight, audit snapshots). Returns list keyed by query index, or dict "
            "if `labels` provided."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "queries": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "model": {"type": "string"},
                            "domain": {"type": "array"},
                            "fields": {"type": "array", "items": {"type": "string"}},
                            "limit": {"type": "integer"},
                            "offset": {"type": "integer"},
                            "order": {"type": "string"},
                        },
                        "required": ["model"],
                    },
                },
                "labels": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional labels for each query (keys result dict)",
                },
            },
            "required": ["queries"],
        },
    },
]

TOOL_HANDLERS = {
    "search_odoo": tool_search_odoo,
    "read_odoo": tool_read_odoo,
    "count_odoo": tool_count_odoo,
    "search_multi": tool_search_multi,
}


# ---- MCP JSON-RPC wiring ----------------------------------------------------

def respond(id_, result):
    msg = {"jsonrpc": "2.0", "id": id_, "result": result}
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def respond_error(id_, code, message):
    msg = {"jsonrpc": "2.0", "id": id_, "error": {"code": code, "message": message}}
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def handle(request):
    method = request.get("method", "")
    req_id = request.get("id")

    if method == "initialize":
        respond(req_id, {
            "protocolVersion": "2025-11-25",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "synapsys-odoo-readonly", "version": "1.0"},
        })
    elif method == "tools/list":
        respond(req_id, {"tools": TOOLS})
    elif method == "tools/call":
        params = request.get("params", {})
        tool_name = params.get("name")
        tool_args = params.get("arguments") or {}
        handler = TOOL_HANDLERS.get(tool_name)
        if handler is None:
            respond(req_id, {
                "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}],
                "isError": True,
            })
            return
        try:
            result = handler(tool_args)
            respond(req_id, {
                "content": [{"type": "text", "text": json.dumps(result, indent=2, default=str)}]
            })
        except xmlrpc.client.Fault as ex:
            respond(req_id, {
                "content": [{"type": "text", "text": f"Odoo error: {ex.faultString}"}],
                "isError": True,
            })
        except Exception as ex:
            respond(req_id, {
                "content": [{"type": "text", "text": f"Error: {ex}"}],
                "isError": True,
            })
    elif method == "notifications/initialized":
        pass
    elif method == "ping":
        respond(req_id, {})
    else:
        if req_id is not None:
            respond_error(req_id, -32601, f"Method not found: {method}")


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            handle(request)
        except json.JSONDecodeError as ex:
            sys.stderr.write(f"JSON decode error: {ex}\n")
        except Exception as ex:
            sys.stderr.write(f"Handler error: {ex}\n")


if __name__ == "__main__":
    main()
