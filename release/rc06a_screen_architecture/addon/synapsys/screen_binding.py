"""Menu-to-screen bindings (RC06g, source-only candidate). Pure: no Odoo, no writes, no I/O except loading the binding file by path.

A binding ties one existing menu and its native action to ONE declared screen, by the exact immutable screen id, with menu_id plus
action_xmlid as anchors (the Navigator's N1 spec). It never replaces the native action: the native fields are carried only so that they can
be checked, and 8 menus are NOT bound (their rows have no screen id and are never routed). Nothing here derives an id from a UI label.
"""
import json
import os

DEFAULT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "screen_bindings_batch5.json")
BOUND = "BIND_ENABLE_OVERLAY_PRESERVE_NATIVE_ACTION"
UNBOUND = "NONE_KEEP_EXISTING_NATIVE"
SCREEN_TYPES_ROUTED = ("noun", "menu")  # record screens are conditional record views, never menu defaults
NEVER_A_MENU_DEFAULT = ("SCR.CONTEXT.RECORD", "SCR.ASSET.RECORD", "SCR.MESH.NOUN")
NATIVE_FIELDS = ("model", "view_type", "action_view_refs", "action_context", "action_domain", "client_tag")


def validate(doc, decls):
    """Returns a list of errors; empty means valid. decls is {screen id: declaration}."""
    errs = []
    if doc.get("schema") != "synapsys.screen.bindings/1":
        return ["unknown schema %r" % (doc.get("schema"),)]
    rows = doc.get("rows") or []
    seen = {"menu_id": set(), "action_id": set(), "screen_id": set()}
    for r in rows:
        n = r.get("screen_no")
        for k in ("screen_no", "menu_id", "menu_name", "action_type", "native", "bind_decision", "menu_groups", "binding_status"):
            if k not in r:
                errs.append("row %s: missing %s" % (n, k))
        if errs:
            continue
        if r["bind_decision"] not in (BOUND, UNBOUND):
            errs.append("row %s: unknown bind_decision" % n)
        if not isinstance(r["menu_id"], int) or r["menu_id"] in seen["menu_id"]:
            errs.append("row %s: menu_id missing or repeated" % n)
        seen["menu_id"].add(r["menu_id"])
        if r.get("action_id") is not None:
            if r["action_id"] in seen["action_id"]:
                errs.append("row %s: action_id repeated" % n)
            seen["action_id"].add(r["action_id"])
        for k in NATIVE_FIELDS:
            if k not in r["native"]:
                errs.append("row %s: native.%s missing" % (n, k))
        if r["bind_decision"] == BOUND:
            sid = r.get("screen_id")
            if not sid or sid not in decls:
                errs.append("row %s: screen %r is not a declared screen" % (n, sid))
                continue
            if sid in seen["screen_id"]:
                errs.append("row %s: screen %r bound twice" % (n, sid))
            seen["screen_id"].add(sid)
            if sid in NEVER_A_MENU_DEFAULT or decls[sid]["screen_type"] not in SCREEN_TYPES_ROUTED:
                errs.append("row %s: screen %r may not be a menu default" % (n, sid))
            if r["action_type"] != "ir.actions.act_window" or not r.get("action_xmlid") or not isinstance(r.get("action_id"), int) or not r["native"].get("model"):
                errs.append("row %s: a bound menu needs a window action with an xmlid, an id and a model" % n)
        else:
            if r.get("screen_id") or not r.get("none_reason"):
                errs.append("row %s: an unbound menu has no screen id and states its reason" % n)
    return errs


def load(path=None, decls=None):
    """Returns (rows, by_action_id, by_menu_id). Raises ValueError listing every error; never returns a half-valid table."""
    p = path or DEFAULT_PATH
    doc = json.load(open(p, encoding="utf-8"))
    errs = validate(doc, decls or {})
    if errs:
        raise ValueError("; ".join(errs))
    rows = doc["rows"]
    bound = [r for r in rows if r["bind_decision"] == BOUND]
    return rows, {r["action_id"]: r for r in bound}, {r["menu_id"]: r for r in bound}
