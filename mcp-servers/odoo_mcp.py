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

Transport:
  MCP_TRANSPORT=stdio (default, unchanged behaviour) or MCP_TRANSPORT=http.
  HTTP mode now runs on the real `fastmcp` framework's own streamable-HTTP
  transport (same as n8n_mcp.py — no longer a simplified stateless shim),
  and requires MCP_AUTH_TOKEN + MCP_ALLOWED_HOSTS. Reads MCP_HOST/MCP_PORT
  (default 0.0.0.0:8000), MCP_ALLOWED_ORIGINS, MCP_HTTP_TRANSPORT. Optional
  Entra ID OAuth (for connector UIs that require OAuth, e.g. Cowork) via
  ENTRA_TENANT_ID/OAUTH_CLIENT_ID/OAUTH_CLIENT_SECRET/MCP_API_AUDIENCE/
  MCP_PUBLIC_URL — see mcp-servers/_azure_auth.py. See mcp-servers/README.md
  "Network (HTTP) deployment" for the full picture, including what this does
  NOT yet cover (rate limiting, TLS termination — expected to sit behind a
  reverse proxy, not handled by this process).

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

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
import _write_safety as ws  # noqa: E402

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


# ---- Write-safety membrane (RELEASE_D007_SYNAPSYS_MCP_FFE_MUTATION_SAFETY_ENFORCEMENT_V1, group A) ----
#
# Common prepare/execute write-set core (mcp-servers/_write_safety.py) wired
# against this module's own Odoo primitives. See _write_safety.py for the
# full contract; this section only supplies the model-specific read/count/
# mutate closures and the tool-facing wrapping described in the D007
# prewrite's "Implementation groups / A. Odoo MCP code":
#   - add common prepare/execute write-set core            -> _write_safety
#   - wrap create/write/unlink                              -> below
#   - constrain generic execute_odoo mutation methods        -> below
#   - retain read tools unchanged                            -> untouched above

_WRITE_SET_STORE = ws.WriteSetStore()
_RETRY_TRACKER = ws.RetryTracker()


def _note_refusal_retry(tool: str, model: str, operation: str, preview: Dict) -> int:
    """B2/L-07 — record this refused proposal's fingerprint and return the
    occurrence count (1 on first refusal, 2+ on an identical retry)."""
    fingerprint = ws.refusal_fingerprint(
        tool=tool, model=model, operation=operation,
        ids=preview["enumerated_ids"], proposed=preview.get("proposed", {}),
    )
    return _RETRY_TRACKER.note(fingerprint)

# Models whose create/config-method mutation is itself a runtime/config
# surface change (automation, actions, cron, access control, field/model
# definitions) rather than ordinary operational data — classified
# CONFIGURATION_RUNTIME_MUTATION per the D007 prewrite's fixed consent
# classes. Not exhaustive by design: this is the minimum needed to satisfy
# "constrain generic execute_odoo mutation methods" without inventing new
# governance scope: any *.actions.*, base.automation, ir.cron, ir.model*
# write is runtime configuration.
_RUNTIME_CONFIG_MODEL_PREFIXES = (
    "ir.actions.", "base.automation", "ir.cron", "ir.model", "ir.rule",
    "ir.ui.view", "ir.ui.menu", "ir.filters",
)


def _is_runtime_config_model(model: str) -> bool:
    return any(model == p or model.startswith(p) for p in _RUNTIME_CONFIG_MODEL_PREFIXES)


def _ws_read_fn(model: str, ids: List[int], fields: List[str]) -> List[dict]:
    return _exec(model, "read", [ids], {"fields": fields})


def _ws_count_fn(model: str) -> int:
    return _exec(model, "search_count", [[]])


def _ws_mutate_fn(model: str, operation: str, ids: List[int], proposed: Dict[str, Any]) -> Any:
    if operation == "write":
        return _exec(model, "write", [ids, proposed])
    if operation == "unlink":
        return _exec(model, "unlink", [ids])
    raise ValueError(f"_ws_mutate_fn: unsupported operation {operation!r}")


def _ws_search_fn(model: str, domain: list) -> List[dict]:
    return _exec(model, "search_read", [domain], {"fields": ["id", "name"]})


def _resolve_ids_for_prepare(args: Dict) -> List[int]:
    """Resolve the caller's target to actual current IDs. Accepts either
    explicit `ids` (normalised) or a `domain` (search'd fresh — this is the
    exact P0-A path: a domain is resolved to real IDs at prepare time, and
    the caller's own `intended_count` belief is carried through only as an
    informational field, never trusted for scope)."""
    if args.get("ids") is not None:
        return normalize_ids(args["ids"])
    if args.get("domain") is not None:
        return _exec(args["model"], "search", [args["domain"]])
    raise ValueError("either 'ids' or 'domain' is required to resolve a write set")


def tool_prepare_write_odoo(args: Dict) -> Any:
    return ws.prepare_write_set(
        model=args["model"], operation="write",
        resolve_ids=lambda: _resolve_ids_for_prepare(args),
        read_fn=_ws_read_fn, count_fn=_ws_count_fn,
        proposed=args["values"], intended_count=args.get("intended_count"),
        store=_WRITE_SET_STORE,
    )


def tool_execute_write_odoo(args: Dict) -> Any:
    return ws.execute_write_set(
        write_set_id=args["write_set_id"], enumerated_ids=normalize_ids(args["enumerated_ids"]),
        read_fn=_ws_read_fn, mutate_fn=_ws_mutate_fn, store=_WRITE_SET_STORE,
        protected_state_confirmed=bool(args.get("protected_state_confirmed", False)),
        observability_default_confirmed=bool(args.get("observability_default_confirmed", False)),
    )


def tool_prepare_unlink_odoo(args: Dict) -> Any:
    return ws.prepare_write_set(
        model=args["model"], operation="unlink",
        resolve_ids=lambda: _resolve_ids_for_prepare(args),
        read_fn=_ws_read_fn, count_fn=_ws_count_fn,
        proposed={}, intended_count=args.get("intended_count"),
        store=_WRITE_SET_STORE,
    )


def tool_execute_unlink_odoo(args: Dict) -> Any:
    return ws.execute_write_set(
        write_set_id=args["write_set_id"], enumerated_ids=normalize_ids(args["enumerated_ids"]),
        read_fn=_ws_read_fn, mutate_fn=_ws_mutate_fn, store=_WRITE_SET_STORE,
        protected_state_confirmed=bool(args.get("protected_state_confirmed", False)),
        observability_default_confirmed=bool(args.get("observability_default_confirmed", False)),
    )


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
    model = args["model"]
    values = args["values"]

    # A4/L-02 — secret refusal before any proposed value enters a preview,
    # store or the create call itself.
    offending = ws.scan_for_secrets(values)
    if offending is not None:
        raise ws.WriteSafetyRefusal(
            "SECRET_MATERIAL_REFUSED",
            f"Proposed value at field {offending['field']!r} matches a high-confidence "
            f"secret pattern ({offending['pattern']}) and is refused. The value itself "
            "is never echoed.",
            actual={"field": offending["field"], "pattern": offending["pattern"]},
            correction="Remove the secret-shaped value from this field.",
        )

    # L-09/L-10 — creating an ir.actions.act_window with a view_mode set
    # that already exists on the same res_model is refused as
    # REUSABLE_CAPABILITY_EXISTS: the check is run here rather than trusted
    # from the caller, since a caller reporting "no equivalent exists"
    # without actually running the check is the exact defect this closes.
    if model == "ir.actions.act_window" and values.get("res_model") and values.get("view_mode"):
        existing = ws.check_action_window_reuse(
            res_model=values["res_model"], view_mode=values["view_mode"], search_fn=_ws_search_fn,
        )
        if existing:
            raise ws.WriteSafetyRefusal(
                "REUSABLE_CAPABILITY_EXISTS",
                f"An ir.actions.act_window already exists for res_model={values['res_model']!r} "
                f"with the identical view_mode set — refusing to create a parallel capability.",
                actual={"existing": existing},
                correction="Reuse one of the existing action windows listed in `actual.existing` instead of creating a duplicate.",
            )

    if _is_runtime_config_model(model):
        ack = set(args.get("consent_ack") or [])
        if ws.CONSENT_CONFIGURATION_RUNTIME_MUTATION not in ack:
            raise ws.WriteSafetyRefusal(
                "CONFIGURATION_RUNTIME_MUTATION_CONFIRMATION_REQUIRED",
                f"create on {model!r} is a runtime/configuration-surface mutation "
                "and requires explicit consent_ack.",
                actual={"model": model, "consent_class": ws.CONSENT_CONFIGURATION_RUNTIME_MUTATION},
                correction=(
                    "Re-call with consent_ack=['CONFIGURATION_RUNTIME_MUTATION'] after "
                    "separate explicit review of the runtime/config impact."
                ),
            )
    return _exec(model, "create", [values])


def tool_write_odoo(args: Dict) -> Any:
    """Wraps the prepare/execute write-set core (group A). A small,
    unprotected, non-observability write auto-prepares and auto-executes in
    one call for convenience; anything bulk (>10 ids or >20% of the
    register), touching a protected Benefit state, or touching an
    observability default MUST go through prepare_write_odoo /
    execute_write_odoo explicitly with the matching confirmation — this
    tool refuses rather than silently downgrading the requirement."""
    preview = tool_prepare_write_odoo(args)
    if preview.get("no_change_required"):
        # B2/L-06 — intended end-state already holds. Return without ever
        # issuing an EXECUTE_WRITE_SET call, so no mutating call and no
        # associated client prompt occurs.
        return "NO_CHANGE_REQUIRED"
    if (preview["requires_enumerated_ids"] or preview["requires_protected_state_confirmation"]
            or preview["requires_observability_default_confirmation"]):
        retry_count = _note_refusal_retry("write_odoo", args["model"], "write", preview)
        escalated = retry_count >= 2
        raise ws.WriteSafetyRefusal(
            "TWO_PHASE_CONFIRMATION_REQUIRED" + ("_ESCALATED" if escalated else ""),
            (
                f"This exact proposal has now been refused {retry_count} times unchanged — "
                "escalating rather than re-proposing identically. "
                if escalated else ""
            ) + "This write's actual scope/classification requires the explicit "
            "prepare_write_odoo / execute_write_odoo two-phase path.",
            actual={**preview, "retry_count": retry_count},
            correction=(
                "Do not re-submit this exact proposal again unchanged. "
                if escalated else ""
            ) + (
                "Call prepare_write_odoo with the same model/ids-or-domain/values, "
                "review the returned preview, then execute_write_odoo with its "
                "write_set_id, enumerated_ids, and any required confirmation flag."
            ),
        )
    result = tool_execute_write_odoo({
        "write_set_id": preview["write_set_id"],
        "enumerated_ids": preview["enumerated_ids"],
    })
    return result["result"]


def tool_unlink_odoo(args: Dict) -> Any:
    """Wraps the prepare/execute write-set core (group A) — see
    tool_write_odoo. unlink is always DESTRUCTIVE_MUTATION; bulk unlinks
    still require the explicit two-phase path (protected-state/
    observability classification never applies to unlink itself, since it
    has no proposed field values)."""
    preview = tool_prepare_unlink_odoo(args)
    if preview["requires_enumerated_ids"]:
        retry_count = _note_refusal_retry("unlink_odoo", args["model"], "unlink", preview)
        raise ws.WriteSafetyRefusal(
            "TWO_PHASE_CONFIRMATION_REQUIRED" + ("_ESCALATED" if retry_count >= 2 else ""),
            "This unlink's actual scope requires the explicit "
            "prepare_unlink_odoo / execute_unlink_odoo two-phase path.",
            actual={**preview, "retry_count": retry_count},
            correction=(
                "Call prepare_unlink_odoo with the same model/ids-or-domain, "
                "review the returned preview, then execute_unlink_odoo with its "
                "write_set_id and enumerated_ids."
            ),
        )
    result = tool_execute_unlink_odoo({
        "write_set_id": preview["write_set_id"],
        "enumerated_ids": preview["enumerated_ids"],
    })
    return result["result"]


# Methods on the generic execute_odoo passthrough that are read-only and
# therefore exempt from the CONFIGURATION_RUNTIME_MUTATION consent gate
# below. Deliberately narrow (an allowlist, not a denylist) — anything not
# on it is treated as a possible mutation and gated, per "constrain generic
# execute_odoo mutation methods" in the D007 prewrite.
_EXECUTE_ODOO_READ_SAFE_METHODS = {
    "read", "search", "search_read", "search_count", "fields_get",
    "default_get", "name_get", "name_search", "check_access_rights",
    "check_access_rule", "get_metadata", "exists",
}
# Always refused outright on execute_odoo regardless of consent_ack — these
# have dedicated wrapped tools (create_odoo/write_odoo/unlink_odoo) that
# apply the actual safety membrane; execute_odoo must not be usable to
# bypass it.
_EXECUTE_ODOO_REFUSED_METHODS = {"write", "create", "unlink"}


def tool_execute_odoo(args: Dict) -> Any:
    method = args["method"]
    if method in _EXECUTE_ODOO_REFUSED_METHODS:
        raise ws.WriteSafetyRefusal(
            "RAW_MUTATION_METHOD_REFUSED",
            f"execute_odoo cannot be used to call {method!r} directly — this would "
            "bypass the write-set safety membrane.",
            actual={"model": args.get("model"), "method": method},
            correction=f"Use {method}_odoo (or prepare_{method}_odoo/execute_{method}_odoo) instead.",
        )
    if method not in _EXECUTE_ODOO_READ_SAFE_METHODS:
        ack = set(args.get("consent_ack") or [])
        if ws.CONSENT_CONFIGURATION_RUNTIME_MUTATION not in ack:
            raise ws.WriteSafetyRefusal(
                "CONFIGURATION_RUNTIME_MUTATION_CONFIRMATION_REQUIRED",
                f"execute_odoo method {method!r} is not on the read-safe allowlist and "
                "is treated as a possible mutation; it requires explicit consent_ack.",
                actual={
                    "model": args.get("model"), "method": method,
                    "consent_class": ws.CONSENT_CONFIGURATION_RUNTIME_MUTATION,
                },
                correction="Re-call with consent_ack=['CONFIGURATION_RUNTIME_MUTATION'] after separate explicit review.",
            )
    return _exec(
        args["model"],
        method,
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
        "description": (
            "Create a single record. Returns the new id. If the model is a runtime/"
            "configuration surface (ir.actions.*, base.automation, ir.cron, ir.model*, "
            "ir.rule, ir.ui.view/menu, ir.filters), requires "
            "consent_ack=['CONFIGURATION_RUNTIME_MUTATION']."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "model": {"type": "string"},
                "values": {"type": "object"},
                "consent_ack": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["model", "values"],
        },
    },
    {
        "name": "write_odoo",
        "description": (
            "Update one or more records by explicit ids. Small, unprotected, "
            "non-observability writes execute in one call. Bulk (>10 ids or >20% of "
            "the model's register), protected Benefit-state transitions, or "
            "observability-default changes are refused with "
            "TWO_PHASE_CONFIRMATION_REQUIRED — use prepare_write_odoo / "
            "execute_write_odoo explicitly for those."
        ),
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
        "name": "prepare_write_odoo",
        "description": (
            "PHASE 1 (non-mutating) of the write-set safety membrane. Resolves ids or "
            "a domain to the exact current record IDs, captures prestate, actual "
            "affected count/percentage, and protected-state/observability "
            "classification. Returns a write_set_id to pass to execute_write_odoo. "
            "No mutation occurs."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "model": {"type": "string"},
                "ids": {"type": ["array", "integer"]},
                "domain": {"type": "array"},
                "values": {"type": "object"},
                "intended_count": {"type": "integer", "description": "Caller's belief about scope; informational only, never trusted for actual scope."},
            },
            "required": ["model", "values"],
        },
    },
    {
        "name": "execute_write_odoo",
        "description": (
            "PHASE 2 (mutating) of the write-set safety membrane. Accepts only a "
            "write_set_id from prepare_write_odoo plus the exact enumerated_ids it "
            "represents; refuses on any set mismatch or prestate drift. Set "
            "protected_state_confirmed / observability_default_confirmed when the "
            "prepare preview required them."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "write_set_id": {"type": "string"},
                "enumerated_ids": {"type": ["array", "integer"]},
                "protected_state_confirmed": {"type": "boolean", "default": False},
                "observability_default_confirmed": {"type": "boolean", "default": False},
            },
            "required": ["write_set_id", "enumerated_ids"],
        },
    },
    {
        "name": "unlink_odoo",
        "description": (
            "Delete records by id. Small unlinks (<=10 ids and <=20% of the model's "
            "register) execute in one call; bulk unlinks are refused with "
            "TWO_PHASE_CONFIRMATION_REQUIRED — use prepare_unlink_odoo / "
            "execute_unlink_odoo explicitly. Odoo will also raise on records with "
            "protective constraints."
        ),
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
        "name": "prepare_unlink_odoo",
        "description": "PHASE 1 (non-mutating) of the write-set safety membrane for unlink. See prepare_write_odoo.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "model": {"type": "string"},
                "ids": {"type": ["array", "integer"]},
                "domain": {"type": "array"},
                "intended_count": {"type": "integer"},
            },
            "required": ["model"],
        },
    },
    {
        "name": "execute_unlink_odoo",
        "description": "PHASE 2 (mutating) of the write-set safety membrane for unlink. See execute_write_odoo.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "write_set_id": {"type": "string"},
                "enumerated_ids": {"type": ["array", "integer"]},
            },
            "required": ["write_set_id", "enumerated_ids"],
        },
    },
    {
        "name": "execute_odoo",
        "description": (
            "Generic execute_kw passthrough for any Odoo model method (e.g. name_search, "
            "copy, custom actions). 'write'/'create'/'unlink' are always refused here "
            "(use the dedicated wrapped tools). Any other method not on the read-safe "
            "allowlist requires consent_ack=['CONFIGURATION_RUNTIME_MUTATION']."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "model": {"type": "string"},
                "method": {"type": "string"},
                "args": {"type": "array"},
                "kwargs": {"type": "object"},
                "consent_ack": {"type": "array", "items": {"type": "string"}},
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
    "prepare_write_odoo": tool_prepare_write_odoo,
    "execute_write_odoo": tool_execute_write_odoo,
    "unlink_odoo": tool_unlink_odoo,
    "prepare_unlink_odoo": tool_prepare_unlink_odoo,
    "execute_unlink_odoo": tool_execute_unlink_odoo,
    "execute_odoo": tool_execute_odoo,
    "search_multi": tool_search_multi,
    "create_fields_batch": tool_create_fields_batch,
    "create_acls_batch": tool_create_acls_batch,
}


# ---- MCP JSON-RPC wiring --------------------------------------------------

def _result_msg(id_, result):
    return {"jsonrpc": "2.0", "id": id_, "result": result}


def _error_msg(id_, code, message):
    return {"jsonrpc": "2.0", "id": id_, "error": {"code": code, "message": message}}


def build_response(request: Dict) -> Optional[Dict]:
    """Pure JSON-RPC handler: request dict in, response dict out (or None
    for notifications that have no response, e.g. notifications/initialized).

    No I/O here — this is the exact same dispatch logic the original
    stdio-only handle() contained, extracted so both the stdio loop and the
    HTTP transport can share one tested code path instead of the HTTP mode
    reimplementing tool dispatch.
    """
    method = request.get("method", "")
    req_id = request.get("id")

    if method == "initialize":
        return _result_msg(req_id, {
            "protocolVersion": "2025-11-25",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "synapsys-odoo", "version": "2.0"},
        })
    elif method == "tools/list":
        return _result_msg(req_id, {"tools": TOOLS})
    elif method == "tools/call":
        params = request.get("params", {})
        tool_name = params.get("name")
        tool_args = params.get("arguments") or {}
        handler = TOOL_HANDLERS.get(tool_name)
        if handler is None:
            return _result_msg(req_id, {
                "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}],
                "isError": True,
            })
        try:
            result = handler(tool_args)
            return _result_msg(req_id, {
                "content": [{"type": "text", "text": json.dumps(result, indent=2, default=str)}]
            })
        except ws.WriteSafetyRefusal as ex:
            # P1-L REFUSAL_FEEDBACK: machine-readable invariant code, actual
            # scope, and smallest correction — never a generic string.
            return _result_msg(req_id, {
                "content": [{"type": "text", "text": json.dumps(ex.to_dict(), indent=2, default=str)}],
                "isError": True,
            })
        except xmlrpc.client.Fault as ex:
            return _result_msg(req_id, {
                "content": [{"type": "text", "text": f"Odoo error: {ex.faultString}"}],
                "isError": True,
            })
        except Exception as ex:
            return _result_msg(req_id, {
                "content": [{"type": "text", "text": f"Error: {ex}"}],
                "isError": True,
            })
    elif method == "notifications/initialized":
        return None
    elif method == "ping":
        return _result_msg(req_id, {})
    else:
        # Unknown method — respond with empty result so MCP clients don't hang
        if req_id is not None:
            return _error_msg(req_id, -32601, f"Method not found: {method}")
        return None


def respond(id_, result):
    msg = _result_msg(id_, result)
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def respond_error(id_, code, message):
    msg = _error_msg(id_, code, message)
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def handle(request):
    """Stdio entry point: build_response() then write the line to stdout.
    Unchanged behaviour from the original file — same dispatch, now shared
    with the HTTP path instead of duplicated by it."""
    response = build_response(request)
    if response is not None:
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()


def main_stdio():
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


# ---- HTTP transport (added for network-hosted deployment) -----------------
#
# Built on the real `fastmcp` framework (the same one n8n_mcp.py already
# uses), not a hand-rolled Starlette endpoint — the prior version of this
# file was a deliberately simplified, stateless JSON-RPC-over-HTTP shim,
# documented at the time as needing this exact follow-up: migrating onto
# the framework's own session manager so odoo-mcp is genuinely
# spec-compliant streamable-HTTP (matching n8n-mcp) instead of an
# approximation. It's also what lets it use FastMCP's official Entra ID
# OAuth-Proxy support (`_azure_auth.py`) without hand-replicating that
# machinery's routes/middleware — that machinery is exactly what this
# module would otherwise need to reimplement by hand.
#
# The underlying tool_* functions and Odoo XML-RPC helpers above are
# unchanged; this just exposes them as native FastMCP tools instead of the
# hand-rolled TOOLS/TOOL_HANDLERS/build_response dispatch, which remains
# in place unchanged for the stdio path (main_stdio(), handle()) and its
# existing tests.

def build_fastmcp_app():
    """Build the FastMCP app used for HTTP transport. Imported lazily so
    stdio-mode callers (including tests that only exercise build_response())
    never need fastmcp installed."""
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
    from fastmcp import FastMCP
    from starlette.requests import Request
    from starlette.responses import PlainTextResponse
    from _bearer_auth import load_required_token  # noqa: E402
    from _azure_auth import build_combined_auth  # noqa: E402

    app_mcp = FastMCP("synapsys-odoo")

    @app_mcp.custom_route("/health", methods=["GET"])
    async def health(request: Request) -> PlainTextResponse:
        return PlainTextResponse("ok")

    @app_mcp.tool()
    def search_odoo(
        model: str,
        domain: list | None = None,
        fields: list | None = None,
        limit: int = 1000,
        offset: int = 0,
        order: str | None = None,
    ) -> Any:
        """Search any Odoo model (search_read). Returns records matching domain."""
        return tool_search_odoo({
            "model": model, "domain": domain or [], "fields": fields,
            "limit": limit, "offset": offset, "order": order,
        })

    @app_mcp.tool()
    def read_odoo(model: str, ids: Any, fields: list | None = None) -> Any:
        """Read specific records by id. Faster than search_read when ids are known."""
        return tool_read_odoo({"model": model, "ids": ids, "fields": fields})

    @app_mcp.tool()
    def count_odoo(model: str, domain: list | None = None) -> Any:
        """Return the count of records matching a domain (search_count)."""
        return tool_count_odoo({"model": model, "domain": domain or []})

    @app_mcp.tool()
    def create_odoo(model: str, values: dict, consent_ack: list | None = None) -> Any:
        """Create a single record. Returns the new id. Runtime/configuration-surface
        models require consent_ack=['CONFIGURATION_RUNTIME_MUTATION']."""
        return tool_create_odoo({"model": model, "values": values, "consent_ack": consent_ack or []})

    @app_mcp.tool()
    def write_odoo(model: str, ids: Any, values: dict) -> Any:
        """Update one or more records. Bulk/protected/observability writes are
        refused — use prepare_write_odoo / execute_write_odoo for those."""
        return tool_write_odoo({"model": model, "ids": ids, "values": values})

    @app_mcp.tool()
    def prepare_write_odoo(
        model: str, values: dict, ids: Any = None, domain: list | None = None,
        intended_count: int | None = None,
    ) -> Any:
        """PHASE 1 (non-mutating): resolve ids/domain to actual current record IDs
        and prestate. Returns a write_set_id for execute_write_odoo."""
        return tool_prepare_write_odoo({
            "model": model, "values": values, "ids": ids, "domain": domain,
            "intended_count": intended_count,
        })

    @app_mcp.tool()
    def execute_write_odoo(
        write_set_id: str, enumerated_ids: Any,
        protected_state_confirmed: bool = False, observability_default_confirmed: bool = False,
    ) -> Any:
        """PHASE 2 (mutating): execute a previously prepared write set."""
        return tool_execute_write_odoo({
            "write_set_id": write_set_id, "enumerated_ids": enumerated_ids,
            "protected_state_confirmed": protected_state_confirmed,
            "observability_default_confirmed": observability_default_confirmed,
        })

    @app_mcp.tool()
    def unlink_odoo(model: str, ids: Any) -> Any:
        """Delete records by id. Bulk unlinks are refused — use prepare_unlink_odoo /
        execute_unlink_odoo. Odoo raises on records with protective constraints."""
        return tool_unlink_odoo({"model": model, "ids": ids})

    @app_mcp.tool()
    def prepare_unlink_odoo(
        model: str, ids: Any = None, domain: list | None = None, intended_count: int | None = None,
    ) -> Any:
        """PHASE 1 (non-mutating) of the write-set safety membrane for unlink."""
        return tool_prepare_unlink_odoo({
            "model": model, "ids": ids, "domain": domain, "intended_count": intended_count,
        })

    @app_mcp.tool()
    def execute_unlink_odoo(write_set_id: str, enumerated_ids: Any) -> Any:
        """PHASE 2 (mutating) of the write-set safety membrane for unlink."""
        return tool_execute_unlink_odoo({"write_set_id": write_set_id, "enumerated_ids": enumerated_ids})

    @app_mcp.tool()
    def execute_odoo(
        model: str, method: str, args: list | None = None, kwargs: dict | None = None,
        consent_ack: list | None = None,
    ) -> Any:
        """Generic execute_kw passthrough for any Odoo model method. 'write'/'create'/
        'unlink' are refused here; other mutating methods require consent_ack."""
        return tool_execute_odoo({
            "model": model, "method": method, "args": args or [], "kwargs": kwargs or {},
            "consent_ack": consent_ack or [],
        })

    @app_mcp.tool()
    def search_multi(queries: list, labels: list | None = None) -> Any:
        """Run multiple search_read queries in one call. Use for 3+ model fetches."""
        return tool_search_multi({"queries": queries, "labels": labels})

    @app_mcp.tool()
    def create_fields_batch(model_id: int, fields: list, delay_ms: int = 400) -> Any:
        """Sequentially create many ir.model.fields on a target model."""
        return tool_create_fields_batch({"model_id": model_id, "fields": fields, "delay_ms": delay_ms})

    @app_mcp.tool()
    def create_acls_batch(model_id: int, acls: list) -> Any:
        """Create multiple ir.model.access records on a model."""
        return tool_create_acls_batch({"model_id": model_id, "acls": acls})

    auth_token = load_required_token()
    app_mcp.auth = build_combined_auth(auth_token)
    return app_mcp


def _configure_http_kwargs() -> dict:
    """Build host/binding + hostname allow-list for HTTP transport, mirroring
    n8n_mcp.py's equivalent so the two servers behave the same way here."""
    host = os.environ.get("MCP_HOST", "0.0.0.0")
    port = int(os.environ.get("MCP_PORT", "8000"))

    allowed_hosts_raw = os.environ.get("MCP_ALLOWED_HOSTS", "")
    if not allowed_hosts_raw:
        sys.stderr.write(
            "ERROR: MCP_TRANSPORT=http requires MCP_ALLOWED_HOSTS (comma-separated "
            "hostnames expected in the Host header) — refusing to guess a safe "
            "default for a network-exposed server.\n"
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
    }


def main_http():
    app_mcp = build_fastmcp_app()
    app_mcp.run(**_configure_http_kwargs())


def main():
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    if transport == "stdio":
        main_stdio()
    elif transport == "http":
        main_http()
    else:
        sys.stderr.write(
            f"ERROR: unsupported MCP_TRANSPORT={transport!r}; use 'stdio' or 'http'\n"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
