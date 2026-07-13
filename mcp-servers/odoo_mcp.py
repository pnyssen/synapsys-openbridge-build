#!/usr/bin/env python3
"""
SynapSys Odoo MCP Server — v2.0

Extends the original read-only server to full read/write access via XML-RPC.
Bypasses the Cowork sandbox network restrictions and Chrome CDP timeouts
that constrained prior sessions.

Tools:
  Reads:       search_odoo, read_odoo, count_odoo
  Writes:      create_odoo, write_odoo, unlink_odoo
  Passthrough: execute_odoo (generic execute_kw for anything not covered)
  Batch:       create_fields_batch, create_acls_batch  (sequential, safe)

Env vars required:
  ODOO_URL      e.g. https://pnyssen-synapsys-odoo.odoo.com
  ODOO_DB       e.g. pnyssen-synapsys-odoo-production-27407175
  ODOO_LOGIN    e.g. phil@synapsys.com.au
  ODOO_API_KEY  the API key (NOT the password)

CLAUDE.md canonical usage:
  - Read ops preferred via this server.
  - Write ops via this server eliminate Chrome CDP timeouts on bulk field creation.
  - Field creation in batches uses a small inter-call delay so Odoo's model
    cache doesn't throw "dictionary changed size during iteration".
"""
import sys
import json
import time
import xmlrpc.client
import os
from typing import Any, Dict, List, Optional

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


def _exec(model: str, method: str, args: List = None, kwargs: Dict = None):
    uid, models = odoo_connect()
    return models.execute_kw(
        ODOO_DB, uid, ODOO_API_KEY,
        model, method,
        args or [],
        kwargs or {},
    )


def normalize_ids(ids):
    """Coerce various id input formats to a list of integers.

    Handles transport-layer serialisation quirks where lists may arrive as
    JSON-encoded strings (e.g. "[4211]") instead of native list values,
    which would otherwise pass through as a single-element list containing
    a string and trigger Odoo SQL errors like:
        invalid input syntax for type integer: '[4211]'
        WHERE "ir_ui_view"."id" IN ('[4211]')

    Accepts:
      4211           -> [4211]
      "4211"         -> [4211]
      [4211]         -> [4211]
      ["4211"]       -> [4211]
      "[4211]"       -> [4211]
      (4211, 4212)   -> [4211, 4212]

    Rejects:
      None / empty / non-numeric / malformed JSON / SQL-injection patterns

    Returns: list[int] (always).
    """
    if ids is None:
        raise ValueError("ids required")
    # Already a list or tuple
    if isinstance(ids, (list, tuple)):
        if not ids:
            raise ValueError("ids must not be empty")
        try:
            return [int(x) for x in ids]
        except (TypeError, ValueError) as ex:
            raise ValueError(f"ids list contains non-numeric value: {ex}")
    # Scalar int (exclude bool which is a subclass of int)
    if isinstance(ids, int) and not isinstance(ids, bool):
        return [ids]
    # String form
    if isinstance(ids, str):
        s = ids.strip()
        if not s:
            raise ValueError("ids must not be empty")
        # JSON array form like "[4211]" or "[4211, 4212]"
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
        # Single numeric string like "4211"
        try:
            return [int(s)]
        except ValueError:
            raise ValueError(f"ids string is not numeric: {s!r}")
    raise TypeError(f"ids must be int / str / list / tuple ; got {type(ids).__name__}")


# ---- Tool implementations -------------------------------------------------

def tool_search_odoo(args: Dict) -> Any:
    return _exec(
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
    return _exec(
        args["model"], "read",
        [ids],
        {"fields": args.get("fields") or []},
    )


def tool_count_odoo(args: Dict) -> Any:
    return _exec(
        args["model"], "search_count",
        [args.get("domain", [])],
    )


def tool_create_odoo(args: Dict) -> Any:
    return _exec(args["model"], "create", [args["values"]])


def tool_write_odoo(args: Dict) -> Any:
    ids = normalize_ids(args["ids"])
    return _exec(args["model"], "write", [ids, args["values"]])


def tool_unlink_odoo(args: Dict) -> Any:
    ids = normalize_ids(args["ids"])
    return _exec(args["model"], "unlink", [ids])


def tool_execute_odoo(args: Dict) -> Any:
    return _exec(
        args["model"],
        args["method"],
        args.get("args", []),
        args.get("kwargs", {}),
    )


def tool_search_multi(args: Dict) -> Any:
    """
    Run multiple search_read queries in a single tool call.

    Args:
      queries: list of {model, domain, fields, limit} dicts. Each entry is
               passed to search_read. Results are returned in the same order.
      labels:  optional parallel list of labels to key the result dict by.
               If omitted, results are returned as a list.

    Use this when a session needs to fetch state from 3+ models in sequence
    (e.g. preflight, audit, pre-stage snapshot). Saves an MCP round-trip per
    query.
    """
    queries = args["queries"]
    labels = args.get("labels")
    if labels and len(labels) != len(queries):
        raise ValueError("labels must be same length as queries")

    results = []
    for q in queries:
        try:
            r = _exec(
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


def tool_create_fields_batch(args: Dict) -> Any:
    """
    Sequentially create multiple ir.model.fields on a target model.

    Odoo's model registry cache throws "dictionary changed size during iteration"
    when many field creates arrive in parallel. This tool serialises with a short
    inter-call delay (configurable, default 0.4s) and returns per-field results.

    Args:
      model_id:  int — target ir.model id
      fields:    list of field dicts, each with at least
                   {name, ttype, field_description, ...}
                 Selection fields use selection_ids: [[0,0,{value,name,sequence}], ...]
      delay_ms:  int — inter-call delay in ms (default 400)
    """
    model_id = args["model_id"]
    fields = args["fields"]
    delay = (args.get("delay_ms", 400)) / 1000.0
    results = []
    for f in fields:
        payload = {"model_id": model_id, "state": "manual"}
        payload.update(f)
        try:
            fid = _exec("ir.model.fields", "create", [payload])
            results.append({"name": f.get("name"), "id": fid, "ok": True})
        except xmlrpc.client.Fault as ex:
            results.append({
                "name": f.get("name"),
                "ok": False,
                "error": str(ex.faultString)[:400],
            })
        except Exception as ex:
            results.append({
                "name": f.get("name"),
                "ok": False,
                "error": str(ex)[:400],
            })
        if delay > 0:
            time.sleep(delay)
    return results


def tool_create_acls_batch(args: Dict) -> Any:
    """
    Create multiple ir.model.access records on a model.

    Args:
      model_id: int — target ir.model id
      acls:     list of {name, group_id, perm_read, perm_write, perm_create, perm_unlink}
                name defaults to 'access_{model_name}_{group_id}' if not provided
    """
    model_id = args["model_id"]
    acls = args["acls"]
    results = []
    for a in acls:
        payload = {
            "model_id": model_id,
            "group_id": a.get("group_id"),
            "name": a.get("name") or f"access_model_{model_id}_group_{a.get('group_id')}",
            "perm_read": bool(a.get("perm_read", True)),
            "perm_write": bool(a.get("perm_write", False)),
            "perm_create": bool(a.get("perm_create", False)),
            "perm_unlink": bool(a.get("perm_unlink", False)),
        }
        try:
            aid = _exec("ir.model.access", "create", [payload])
            results.append({"group_id": a.get("group_id"), "id": aid, "ok": True})
        except Exception as ex:
            results.append({
                "group_id": a.get("group_id"),
                "ok": False,
                "error": str(ex)[:400],
            })
    return results


# ---- Tool schema ----------------------------------------------------------

TOOLS = [
    {
        "name": "search_odoo",
        "description": "Search any Odoo model (search_read). Returns list of records matching domain with requested fields.",
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
        "description": "Read specific records by id. Faster than search_read when you know the ids.",
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
        "description": "Return the count of records matching a domain (search_count).",
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
        "name": "create_odoo",
        "description": "Create a single record. Returns the new id.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "model": {"type": "string"},
                "values": {"type": "object"},
            },
            "required": ["model", "values"],
        },
    },
    {
        "name": "write_odoo",
        "description": "Update one or more records. Returns true on success.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "model": {"type": "string"},
                "ids": {"type": ["array", "integer"]},
                "values": {"type": "object"},
            },
            "required": ["model", "ids", "values"],
        },
    },
    {
        "name": "unlink_odoo",
        "description": "Delete records by id. Use with caution — Odoo will raise on records with protective constraints.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "model": {"type": "string"},
                "ids": {"type": ["array", "integer"]},
            },
            "required": ["model", "ids"],
        },
    },
    {
        "name": "execute_odoo",
        "description": "Generic execute_kw passthrough for any Odoo model method (e.g. name_search, copy, custom actions).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "model": {"type": "string"},
                "method": {"type": "string"},
                "args": {"type": "array"},
                "kwargs": {"type": "object"},
            },
            "required": ["model", "method"],
        },
    },
    {
        "name": "search_multi",
        "description": (
            "Run multiple search_read queries in one tool call. Use when fetching state from "
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
    {
        "name": "create_fields_batch",
        "description": (
            "Sequentially create many ir.model.fields on a target model. "
            "Serialises calls with an inter-call delay to avoid Odoo's registry-cache "
            "'dictionary changed size during iteration' race. Use for bulk field deployment."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "model_id": {"type": "integer", "description": "Target ir.model id"},
                "fields": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "ttype": {"type": "string"},
                            "field_description": {"type": "string"},
                            "required": {"type": "boolean"},
                            "relation": {"type": "string"},
                            "selection_ids": {"type": "array"},
                            "on_delete": {"type": "string"},
                        },
                        "required": ["name", "ttype"],
                    },
                },
                "delay_ms": {"type": "integer", "default": 400},
            },
            "required": ["model_id", "fields"],
        },
    },
    {
        "name": "create_acls_batch",
        "description": "Create multiple ir.model.access records on a model in one call.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "model_id": {"type": "integer"},
                "acls": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "group_id": {"type": ["integer", "boolean"]},
                            "perm_read": {"type": "boolean"},
                            "perm_write": {"type": "boolean"},
                            "perm_create": {"type": "boolean"},
                            "perm_unlink": {"type": "boolean"},
                        },
                        "required": ["group_id"],
                    },
                },
            },
            "required": ["model_id", "acls"],
        },
    },
]

TOOL_HANDLERS = {
    "search_odoo": tool_search_odoo,
    "read_odoo": tool_read_odoo,
    "count_odoo": tool_count_odoo,
    "create_odoo": tool_create_odoo,
    "write_odoo": tool_write_odoo,
    "unlink_odoo": tool_unlink_odoo,
    "execute_odoo": tool_execute_odoo,
    "search_multi": tool_search_multi,
    "create_fields_batch": tool_create_fields_batch,
    "create_acls_batch": tool_create_acls_batch,
}


# ---- MCP JSON-RPC wiring --------------------------------------------------

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
            "serverInfo": {"name": "synapsys-odoo", "version": "2.0"},
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
        # Unknown method — respond with empty result so MCP clients don't hang
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
