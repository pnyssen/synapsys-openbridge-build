"""Context builder for the Master drill-down (source-only candidate; NOT installed). No Odoo import: the caller's environment, the AccessError class and the
EXISTING scaffold modules (scaffold_wire as sw, scaffold_view as sv) are passed in, so everything here is testable with fakes.

Every read goes through the CALLER'S OWN env: no sudo(), no with_user(), no write. Each probe is independent and fails CLOSED:
a probe that raises an access error or any other error yields None (SOURCE_UNVERIFIED / no link), never a permissive default and never a guess.
"""


def _safe(fn, access_error):
    try:
        return fn()
    except access_error:
        return None
    except Exception:                      # noqa: BLE001 - an unreadable probe is "not read", not a crash and not a leak
        return None


def visible_menu_ids(env, defn, access_error):
    """Menus the caller can SEE: ir.ui.menu searched under the caller's own env (its record rules and groups apply)."""
    ids = [m["menu_id"] for m in defn["menus"]]
    def probe():
        return set(env["ir.ui.menu"].search([("id", "in", ids)]).ids)
    return _safe(probe, access_error)


def readable_models(env, defn, access_error, sw):
    """The actor's REAL read right per model via the existing fail-closed helper scaffold_wire._can_read. None if the probe itself fails."""
    models = sorted({m["model"] for m in defn["menus"] if m.get("model")})
    def probe():
        return {m for m in models if sw._can_read(env, m)}
    return _safe(probe, access_error)


def effective_actions(env, defn, access_error):
    """Effective action facts read under the caller's rights. An action that cannot be read is 'UNREADABLE'; a failed probe is None."""
    win = {int(m["action_ref"].split(",")[1]): m for m in defn["menus"] if m["kind"] == "ACT_WINDOW" and m.get("action_ref")}
    cli = {int(m["action_ref"].split(",")[1]): m for m in defn["menus"] if m["kind"] == "CLIENT_ACTION" and m.get("action_ref")}
    out = {}
    def probe():
        for rec in env["ir.actions.act_window"].search([("id", "in", sorted(win))]):
            out[rec.id] = {"res_model": rec.res_model, "domain": rec.domain or "", "view_mode": rec.view_mode}
        for rec in env["ir.actions.client"].search([("id", "in", sorted(cli))]):
            out[rec.id] = {"tag": rec.tag, "res_model": None}
        return True
    if _safe(probe, access_error) is None:
        return None
    for aid in list(win) + list(cli):
        out.setdefault(aid, "UNREADABLE")
    return out


def effective_fields(env, defn, access_error):
    """Effective field type and relation per model, via fields_get under the caller's rights. A model that cannot be read is 'UNREADABLE'."""
    want = {}
    for m in defn["menus"]:
        if m.get("model"):
            want.setdefault(m["model"], set()).update(e["field"] for e in m["edges"])
    out = {}
    for model, fields in sorted(want.items()):
        def probe(model=model, fields=fields):
            got = env[model].fields_get(sorted(fields), ["type", "relation"])
            return {k: {"type": v.get("type"), "relation": v.get("relation")} for k, v in got.items()}
        r = _safe(probe, access_error)
        out[model] = r if r is not None else "UNREADABLE"
    return out


def bindings_by_menu(sw):
    try:
        return sw.bindings()[2]
    except Exception:                      # noqa: BLE001
        return None


def build_ctx(env, defn, access_error, sw, sv):
    """Everything the drill-down needs from the live platform. Any piece may be None: the drill then says SOURCE_UNVERIFIED and emits no link."""
    ctx = {"visible_menu_ids": visible_menu_ids(env, defn, access_error), "readable_models": readable_models(env, defn, access_error, sw),
           "bindings": bindings_by_menu(sw)}
    ea, ef = effective_actions(env, defn, access_error), effective_fields(env, defn, access_error)
    ctx["effective"] = {"actions": ea, "fields": ef} if ea is not None else {"actions": None, "fields": ef}

    def screen_html(menu_id, action_id, depth):
        try:
            return sw.menu_enable(env, action_id, menu_id, "", depth)
        except Exception:                  # noqa: BLE001
            return {"result": "REFUSED", "reason": "NOT_AVAILABLE"}

    def record_screen_html(screen_id, rid, depth):
        try:
            out = sw.screen_record(env, screen_id, rid, depth)
            return {"result": out.get("result"), "html": sv.render(out, depth) if out.get("result") == "OK" else None}
        except Exception:                  # noqa: BLE001
            return {"result": "REFUSED", "html": None}
    ctx["screen_html"], ctx["record_screen_html"] = screen_html, record_screen_html
    return ctx
