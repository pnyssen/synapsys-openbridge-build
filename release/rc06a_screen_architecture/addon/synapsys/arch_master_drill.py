"""Master Architecture DRILL-DOWN (source-only candidate; NOT installed). Pure functions; no Odoo import, SQL, sudo or write.

Application -> Menu group -> Screen -> View -> Field -> Data, plus authorised per-record Outcome / Benefit / Asset evidence.
Every level keeps THREE things apart and never merges them:
  canonical definition   : the versioned definition file and its source status (arch_master_definition.json)
  effective configuration: what the platform actually holds for this action / field, read under the CALLER's rights and passed in;
                           when it was not read the state is SOURCE_UNVERIFIED, never a guess and never a copy of the definition
  actual records         : rows the actor can read (rights-first; hidden rows are never counted or named)
Existing machinery is REUSED, not copied: the scaffold screen renderer (scaffold_wire.menu_enable / screen_record, injected as providers) and the
lens renderer (lens_contract.render_element with its lineage and local-override rules). No relationship engine is duplicated: edges, readability
and lineage come from arch_graph / arch_master.

Links to native Odoo screens are emitted ONLY for menus the caller can see and records the caller can read, built from integer ids only.
An unknown, malformed, hidden, foreign or absent identifier yields ONE uniform NOT_AVAILABLE answer that discloses nothing.
"""
import re

try:
    from . import arch_graph as G, arch_master as A, lens_contract as LC
except ImportError:                       # offline tests load these files by path, outside a package
    import arch_graph as G
    import arch_master as A
    import lens_contract as LC

LEVELS = ("app", "grp", "scr", "view", "fld", "data", "rec")
RECORD_MODELS = ("synapsys.outcome", "synapsys.benefit", "synapsys.asset")
RECORD_FIELDS = {
    "synapsys.outcome": ("name", "measure", "baseline_observed", "observed_date", "acceptance_condition", "evidence_link", "lifecycle"),
    "synapsys.benefit": ("code", "name", "measure", "unit", "direction", "baseline_rule", "ppv", "position", "lifecycle"),
    "synapsys.asset": ("name", "asset_class", "class_status", "lifecycle", "ppv", "qualifies", "qualified_benefit_count", "rights_confirmed", "rights_holder_id"),
}
CARD = {"many2one": "one", "one2many": "many", "many2many": "many"}
DATA_CAP = 50
TEXT_CAP = 400
NOT_AVAILABLE = {"state": "NOT_AVAILABLE", "reason": "no such element, or not available to your account"}   # one answer for every cause
_PATH = re.compile(r"(app|grp:\d{1,5}|scr:\d{1,5}|view:\d{1,5}|fld:\d{1,5}:[a-z][a-z0-9_]{0,48}|data:\d{1,5}:[a-z][a-z0-9_]{0,48}|rec:synapsys\.(?:outcome|benefit|asset):\d{1,10})")
_UNSAFE = re.compile(r"<\s*script|javascript:|\son[a-z]+\s*=|<\s*iframe", re.I)


def parse_path(path):
    """('app',) | ('grp', menu_id) | ('scr', menu_id) | ('view', menu_id) | ('fld', menu_id, field) | ('data', menu_id, field) | ('rec', model, id). ValueError otherwise."""
    if not isinstance(path, str) or not _PATH.fullmatch(path):          # fullmatch: '$' would accept a trailing newline
        raise ValueError("path")
    parts = path.split(":")
    if parts[0] == "rec":
        return ("rec", parts[1], int(parts[2]))
    return tuple([parts[0]] + [int(x) if x.isdigit() else x for x in parts[1:]])


def _menus(defn):
    return {m["menu_id"]: m for m in defn["menus"]}


def _children(defn, mid):
    return [m for m in defn["menus"] if m["parent_id"] == mid]


def _trail(defn, mid):
    by, out = _menus(defn), []
    while mid is not None and mid in by and len(out) < 12:
        out.append(by[mid]); mid = by[mid]["parent_id"]
    return list(reversed(out))


def _action_id(m):
    try:
        return int(str(m["action_ref"]).split(",")[1])
    except (IndexError, ValueError, TypeError):
        return None


# ------------------------------------------------------------------------------------------------------------------ links
def menu_link(m, ctx):
    """Native link to a menu's screen: only for a non-container menu the caller can SEE. None otherwise (never a guess)."""
    vis = ctx.get("visible_menu_ids")
    aid = _action_id(m)
    if vis is None or m["menu_id"] not in vis or m["kind"] == "CONTAINER" or aid is None:
        return None
    return "/odoo/action-%d" % aid


def record_link(m, rid, graph, actor, ctx):
    """Native link to one record: menu visible, model readable (real check passed in), act_window action, and the row readable by this actor."""
    base = menu_link(m, ctx)
    rm = ctx.get("readable_models")
    if base is None or m["kind"] != "ACT_WINDOW" or not m.get("model") or rm is None or m["model"] not in rm:
        return None
    if not isinstance(rid, int) or isinstance(rid, bool) or not G._readable(graph, actor, m["model"], rid):
        return None
    return "%s/%d" % (base, rid)


# ------------------------------------------------------------------------------------------------------------------ effective configuration
def effective_action(m, ctx):
    """Compare the definition's action facts with the platform's action read under the caller's rights. SOURCE_UNVERIFIED when not read."""
    eff = (ctx.get("effective") or {}).get("actions")
    aid = _action_id(m)
    if eff is None or aid is None:
        return {"state": "SOURCE_UNVERIFIED", "reason": "effective action configuration was not read", "differences": []}
    got = eff.get(aid, eff.get(str(aid)))
    if got in (None, "UNREADABLE"):
        return {"state": "SOURCE_UNVERIFIED", "reason": "this action could not be read under your rights", "differences": []}
    diffs = []
    if m.get("model") and got.get("res_model") != m["model"]:
        diffs.append({"fact": "model", "definition": m["model"], "effective": got.get("res_model")})
    if m["kind"] == "ACT_WINDOW":
        if (got.get("domain") or "").replace(" ", "") != (m.get("domain") or "").replace(" ", ""):
            diffs.append({"fact": "domain", "definition": m.get("domain"), "effective": got.get("domain")})
        if A_modes(got.get("view_mode")) != A_modes(m.get("view_mode")):
            diffs.append({"fact": "view_mode", "definition": m.get("view_mode"), "effective": got.get("view_mode")})
    if m["kind"] == "CLIENT_ACTION" and m.get("client_tag") and got.get("tag") != m["client_tag"]:
        diffs.append({"fact": "client_tag", "definition": m["client_tag"], "effective": got.get("tag")})
    return {"state": "DRIFT" if diffs else "MATCHES_DEFINITION", "differences": diffs, "effective": {k: got.get(k) for k in ("res_model", "domain", "view_mode", "tag") if got.get(k) is not None}}


def A_modes(v):
    return [x.strip() for x in str(v).split(",") if x.strip()] if v else []


def effective_field(model, field, edge, ctx):
    eff = (ctx.get("effective") or {}).get("fields")
    if eff is None:
        return {"state": "SOURCE_UNVERIFIED", "reason": "effective field metadata was not read"}
    got = eff.get(model)
    if got in (None, "UNREADABLE"):
        return {"state": "SOURCE_UNVERIFIED", "reason": "field metadata for this model could not be read under your rights"}
    f = got.get(field)
    if f is None:
        return {"state": "FIELD_NOT_PRESENT", "reason": "the installed model does not declare this field"}
    diffs = []
    if f.get("relation") != edge["target_model"]:
        diffs.append({"fact": "target_model", "definition": edge["target_model"], "effective": f.get("relation")})
    if CARD.get(f.get("type")) != edge["cardinality"]:
        diffs.append({"fact": "cardinality", "definition": edge["cardinality"], "effective": f.get("type")})
    return {"state": "DRIFT" if diffs else "MATCHES_DEFINITION", "differences": diffs, "effective": {"type": f.get("type"), "relation": f.get("relation")}}


# ------------------------------------------------------------------------------------------------------------------ small builders
def _crumbs(defn, parts, ctx=None):
    by = _menus(defn)
    out = [{"level": "app", "label": "Application", "drill": "app"}]
    if parts[0] == "app":
        return out
    if parts[0] == "rec":
        return out + [{"level": "rec", "label": "Record %s/%d" % (parts[1].split(".")[-1], parts[2]), "drill": "rec:%s:%d" % (parts[1], parts[2])}]
    mid = parts[1]
    m = by[mid]
    chain = [x for x in _trail(defn, mid) if x["parent_id"] is not None]
    for x in chain:
        if x["kind"] == "CONTAINER":
            out.append({"level": "grp", "label": x["path"].split("/")[-1], "drill": "grp:%d" % x["menu_id"]})
    if m["kind"] != "CONTAINER":
        out.append({"level": "scr", "label": m["path"].split("/")[-1], "drill": "scr:%d" % mid})
        if parts[0] in ("view", "fld", "data"):
            out.append({"level": "view", "label": "View", "drill": "view:%d" % mid})
        if parts[0] in ("fld", "data"):
            out.append({"level": "fld", "label": parts[2], "drill": "fld:%d:%s" % (mid, parts[2])})
        if parts[0] == "data":
            out.append({"level": "data", "label": "Data", "drill": "data:%d:%s" % (mid, parts[2])})
    return out


def _safe_embed(html):
    return html if isinstance(html, str) and not _UNSAFE.search(html) else None


def _lens_html(defn, graph, actor, eid, label, depth, ov, **kw):
    """The EXISTING lens renderer, with its lineage and local-override rules. Ancestors come from actual readable stored links or the menu tree."""
    el = LC.element(eid, label, **kw)
    return LC.render_element(el, depth, LC.parse_overrides(ov or ""))


def _strip_repeat_style(html):
    """lens_contract prefixes every element with its STYLE block; keep the first occurrence only."""
    first = html.find(LC.STYLE)
    if first < 0:
        return html
    head = html[:first + len(LC.STYLE)]
    return head + html[first + len(LC.STYLE):].replace(LC.STYLE, "")


def _row_menu(m, graph, actor, notes, ctx):
    rs = A._menu_state(m, graph, actor, notes)
    return {"menu_id": m["menu_id"], "label": m["path"].split("/")[-1], "kind": m["kind"], "model": m.get("model"), "matrix_status": m["matrix_status"],
            "record_state": rs["state"], "hold": m["matrix_status"] in ("HONEST_HOLD", "RELEASE_BLOCKED", "NOT_TESTED"),
            "drill": ("grp:%d" % m["menu_id"]) if m["kind"] == "CONTAINER" else ("scr:%d" % m["menu_id"]), "native_link": menu_link(m, ctx)}


# ------------------------------------------------------------------------------------------------------------------ levels
def drill(defn, graph, actor, notes, path="app", ctx=None, depth="enable", ov=""):
    """One drill-down level. Never raises for a bad path or an unavailable element: returns the uniform NOT_AVAILABLE answer."""
    ctx = ctx or {}
    if depth not in A.DEPTHS:
        raise ValueError(depth)
    try:
        parts = parse_path(path)
    except ValueError:
        return dict(NOT_AVAILABLE, level=None, writes=0)
    by = _menus(defn)
    out = {"state": "OK", "level": parts[0], "path": path, "depth": depth, "writes": 0, "read_only": True,
           "link_scheme": "/odoo/action-<id>[/<res_id>] built from integer ids only; scheme itself SOURCE_UNVERIFIED in V20 (not executed here)"}
    if parts[0] == "rec":
        r = record_evidence(defn, graph, actor, notes, parts[1], parts[2], ctx, depth, ov)
        if r["state"] != "OK":
            return dict(NOT_AVAILABLE, level="rec", writes=0)
        out.update(r); out["breadcrumb"] = _crumbs(defn, parts); return out
    if parts[0] == "app":
        root = [m for m in defn["menus"] if m["parent_id"] is None][0]
        out.update({"breadcrumb": _crumbs(defn, parts), "root": {"menu_id": root["menu_id"], "label": root["path"], "kind": root["kind"], "client_tag": root["client_tag"],
                                                                 "native_link": menu_link(root, ctx)},
                    "canonical": _canonical(root), "effective": effective_action(root, ctx), "actual": {"state": "NOT_APPLICABLE", "reason": "the application root holds navigation only"},
                    "children": [_row_menu(m, graph, actor, notes, ctx) for m in _children(defn, root["menu_id"])], "child_label": "Menu groups and screens"})
        return out
    mid = parts[1]
    m = by.get(mid)
    if m is None:
        return dict(NOT_AVAILABLE, level=parts[0], writes=0)
    if parts[0] == "grp":
        if m["kind"] != "CONTAINER":
            return dict(NOT_AVAILABLE, level="grp", writes=0)
        out.update({"breadcrumb": _crumbs(defn, parts), "group": {"menu_id": mid, "label": m["path"]}, "canonical": _canonical(m),
                    "effective": {"state": "NOT_APPLICABLE", "reason": "a container has no action"}, "actual": {"state": "NOT_APPLICABLE", "reason": "container: navigation and access control only"},
                    "children": [_row_menu(x, graph, actor, notes, ctx) for x in _children(defn, mid)], "child_label": "Screens in this group"})
        return out
    if m["kind"] == "CONTAINER":
        return dict(NOT_AVAILABLE, level=parts[0], writes=0)
    rs = A._menu_state(m, graph, actor, notes)
    base = {"breadcrumb": _crumbs(defn, parts), "menu": {"menu_id": mid, "label": m["path"], "kind": m["kind"], "native_link": menu_link(m, ctx)},
            "canonical": _canonical(m), "effective": effective_action(m, ctx),
            "actual": {"state": rs["state"], "readable_count": rs.get("readable_count"), "hold": m["matrix_status"] in ("HONEST_HOLD", "RELEASE_BLOCKED", "NOT_TESTED")}}
    out.update(base)
    if parts[0] == "scr":
        out["screen"] = _screen_panel(m, ctx, depth)
        anc = [("menu:%d" % x["menu_id"]) for x in reversed(_trail(defn, mid)[:-1])]
        out["lens"] = _strip_repeat_style(_lens_html(defn, graph, actor, "menu:%d" % mid, m["path"].split("/")[-1], depth, ov, noun=m.get("model"), status=m["source_status"],
                                                      definition=m["definition"] or m["definition_gap"], source="arch_master_definition.json (versioned file)",
                                                      relationships=[(e["field"], "out", "fld:%d:%s" % (mid, e["field"]), e["target_model"]) for e in m["edges"]], ancestors=anc,
                                                      evidence="record state %s; matrix status %s" % (rs["state"], m["matrix_status"])))
        out["children"] = [{"label": "View", "drill": "view:%d" % mid}] + [{"label": e["field"], "drill": "fld:%d:%s" % (mid, e["field"])} for e in m["edges"]]
        out["child_label"] = "Below this screen"
        return out
    if parts[0] == "view":
        eff_modes = A_modes(((ctx.get("effective") or {}).get("actions") or {}).get(_action_id(m), {}).get("view_mode") if isinstance(((ctx.get("effective") or {}).get("actions") or {}).get(_action_id(m)), dict) else None)
        b = (ctx.get("bindings") or {}).get(mid)
        out["view"] = {"definition_modes": A_modes(m.get("view_mode")), "effective_modes": eff_modes or None,
                       "effective_state": out["effective"]["state"] if m["kind"] == "ACT_WINDOW" else "NOT_APPLICABLE",
                       "declared_native_snapshot": ({"view_type": b["native"].get("view_type"), "view_refs": b["native"].get("action_view_refs")} if b else None),
                       "view_architecture": {"state": "SOURCE_UNVERIFIED", "reason": "ir.ui.view architectures are not read by this interface"}}
        out["children"] = [{"label": e["field"], "drill": "fld:%d:%s" % (mid, e["field"])} for e in m["edges"]]; out["child_label"] = "Fields (typed relationships)"
        return out
    field = parts[2]
    edge = next((e for e in m["edges"] if e["field"] == field), None)
    if edge is None or not m.get("model"):
        return dict(NOT_AVAILABLE, level=parts[0], writes=0)
    pairs = A._instance_edges(graph, actor, m["model"], field, edge["target_model"])
    state = A._edge_state(graph, actor, notes, m["model"], field, edge["target_model"], len(pairs))
    fld = {"field": field, "model": m["model"], "canonical": {k: edge[k] for k in ("target_model", "cardinality", "direction", "perspective")},
           "effective": effective_field(m["model"], field, edge, ctx), "actual": {"state": state, "instance_edges": len(pairs)}}
    if parts[0] == "fld":
        out["field"] = fld
        out["lens"] = _strip_repeat_style(_lens_html(defn, graph, actor, "fld:%d:%s" % (mid, field), "%s.%s" % (m["model"], field), depth, ov, noun=edge["target_model"], status=edge["perspective"],
                                                      definition="%s %s to %s (stored field)" % (edge["cardinality"], edge["direction"], edge["target_model"]), ancestors=["menu:%d" % mid],
                                                      source="typed edge catalogue (arch_graph.EDGES)", evidence="%s; %d readable instance edges" % (state, len(pairs))))
        out["children"] = [{"label": "Data", "drill": "data:%d:%s" % (mid, field)}]; out["child_label"] = "Below this field"
        return out
    shown = []
    tm = edge["target_model"]
    for sid, t in pairs[:DATA_CAP]:
        tmenu = next((x for x in defn["menus"] if x.get("model") == tm and x["kind"] == "ACT_WINDOW"), None)
        shown.append({"from": {"id": sid, "label": _lab(graph, m["model"], sid), "link": record_link(m, sid, graph, actor, ctx), "rec": _rec_drill(m["model"], sid)},
                      "to": {"id": t, "label": _lab(graph, tm, t), "link": record_link(tmenu, t, graph, actor, ctx) if tmenu else None, "rec": _rec_drill(tm, t)}})
    out["field"] = fld
    out["data"] = {"state": state, "shown": len(shown), "total_readable": len(pairs), "truncated": len(pairs) > DATA_CAP, "pairs": shown if depth != "enable" else [],
                   "rule": "only edges whose both ends you can read; the count never includes rows you cannot see"}
    return out


def _lab(graph, model, rid):
    r = graph["records"].get(model, {}).get(rid) or {}
    return str(r.get("code") or r.get("name") or "%s/%s" % (model.split(".")[-1], rid))[:80]


def _rec_drill(model, rid):
    return "rec:%s:%d" % (model, rid) if model in RECORD_MODELS else None


def _canonical(m):
    return {"path": m["path"], "kind": m["kind"], "action_ref": m["action_ref"], "model": m["model"], "domain": m["domain"], "view_mode": m["view_mode"], "client_tag": m["client_tag"],
            "source_status": m["source_status"], "definition_state": m["definition_state"], "definition": m["definition"], "definition_gap": m["definition_gap"],
            "steward_only": m["steward_only"], "matrix_status": m["matrix_status"], "hold_reason": m["status_reason"] if m["matrix_status"] in ("HONEST_HOLD", "RELEASE_BLOCKED", "NOT_TESTED") else None}


def _screen_panel(m, ctx, depth):
    """The EXISTING scaffold screen renderer (scaffold_wire.menu_enable, passed in), fail-closed under the caller's real read right."""
    prov = ctx.get("screen_html")
    if prov is None:
        return {"state": "SOURCE_UNVERIFIED", "reason": "the scaffold screen provider was not supplied", "html": None}
    r = prov(m["menu_id"], _action_id(m), depth)
    if not isinstance(r, dict) or r.get("result") != "OK":
        return {"state": "REFUSED", "reason": (r or {}).get("reason", "NOT_AVAILABLE") if isinstance((r or {}).get("reason"), str) and re.fullmatch(r"[A-Z_]{3,40}", r["reason"]) else "NOT_AVAILABLE", "html": None}
    h = _safe_embed(r.get("html"))
    return {"state": "OK" if h else "EMBED_REFUSED_UNSAFE_MARKUP", "binding_status": r.get("binding_status"), "html": h}


# ------------------------------------------------------------------------------------------------------------------ per-record evidence
def record_evidence(defn, graph, actor, notes, model, rid, ctx=None, depth="enable", ov=""):
    """Authorised per-record Outcome / Benefit / Asset evidence. Source values only; evidence maturity, authority and Realisation boundaries stated.
    Not available (uniformly) for any other model, a malformed id, or a row the actor cannot read."""
    ctx = ctx or {}
    if model not in RECORD_MODELS or not isinstance(rid, int) or isinstance(rid, bool) or not G._readable(graph, actor, model, rid):
        return dict(NOT_AVAILABLE)
    rec = graph["records"][model][rid]
    absent = set(notes["field_absent"].get(model, ()))
    fields = []
    for f in RECORD_FIELDS[model]:
        if f in absent:
            fields.append({"field": f, "state": "FIELD_NOT_PRESENT", "value": None}); continue
        if f not in rec:
            continue
        v = rec[f]
        shown = "(unset)" if v in (None, "") or (v is False and f not in ("baseline_observed", "qualifies", "rights_confirmed")) else str(v)
        fields.append({"field": f, "state": "SOURCE_VALUE", "value": shown[:TEXT_CAP], "truncated": len(shown) > TEXT_CAP})
    rels = []
    for (fm, field, typ, tm, p, ev) in G.EDGES:
        if fm == model:
            for t in G._targets(rec, field):
                if G._readable(graph, actor, tm, t) and G._edge_supported(graph, actor, fm, field, rid, t):
                    rels.append({"direction": "out", "field": field, "model": tm, "id": t, "label": _lab(graph, tm, t), "rec": _rec_drill(tm, t)})
        elif tm == model:
            for sid, srec in graph["records"].get(fm, {}).items():
                if rid in G._targets(srec, field) and G._readable(graph, actor, fm, sid) and G._edge_supported(graph, actor, fm, field, sid, rid):
                    rels.append({"direction": "in", "field": field, "model": fm, "id": sid, "label": _lab(graph, fm, sid), "rec": _rec_drill(fm, sid)})
    fr = []
    for fid in A._readable_ids(graph, actor, "synapsys.fractal"):
        x = graph["records"]["synapsys.fractal"][fid]
        if x.get("res_model") == model and x.get("res_id") == rid:
            fr.append({"id": fid, "label": _lab(graph, "synapsys.fractal", fid), "realisation": x.get("realisation"), "evidence_state": x.get("evidence_state"),
                       "admission": x.get("admission"), "gate_level": x.get("gate_level")})
    menu = next((m for m in defn["menus"] if m.get("model") == model and m["kind"] == "ACT_WINDOW"), None)
    consistency = "NOT_ASSESSED_BY_THIS_INTERFACE"
    if model == "synapsys.asset" and rec.get("qualifies") is True and (not rec.get("rights_confirmed") or (rec.get("qualified_benefit_count") or 0) < 3):
        consistency = "FLAG_INCONSISTENT_WITH_RULE_FOR_STEWARD_REVIEW"       # Asset needs >=3 qualified Benefits plus rights; shown, never corrected
    out = {"state": "OK", "model": model, "id": rid, "label": _lab(graph, model, rid), "fields": fields, "relationships": rels[:50], "relationships_total": len(rels),
           "linked_fractal_evidence": fr[:20],
           "evidence_maturity": {"basis": "source values shown as stored; nothing is computed, promoted or inferred",
                                 "ppv": rec.get("ppv") if "ppv" in rec else "NOT_A_FIELD_OF_THIS_MODEL", "qualification_flag_check": consistency},
           "authority": {"acceptance": "Outcome, Benefit and Asset acceptance is a Steward / Context Stream act; this interface records none and promotes none",
                         "ppv_movement": False, "ai_promotion": False},
           "realisation": {"state": "UNOBSERVED_BY_THIS_INTERFACE" if not fr else "SOURCE_VALUES_SHOWN_NOT_VERIFIED",
                           "rule": "Realisation needs an observed Outcome, an accepted net Benefit and a qualified Asset; fractal evidence rows linked to this record are shown as stored"},
           "native_link": record_link(menu, rid, graph, actor, ctx) if menu else None}
    ps = A.lineage_parents(graph, actor)
    tag = {"synapsys.asset": "ast"}.get(model)
    anc = list(LC.lineage(ps, "%s:%d" % (tag, rid))) if tag else []
    out["lens"] = _strip_repeat_style(_lens_html(defn, graph, actor, "%s:%d" % (model, rid), out["label"], depth, ov, noun=model, status="SOURCE_VALUES", ancestors=anc,
                                                  definition="%s record (source values; no promotion)" % model.split(".")[-1],
                                                  relationships=[(r["field"], r["direction"], r["rec"] or "", r["label"]) for r in rels[:12]],
                                                  evidence="%d linked fractal evidence rows; qualification check %s" % (len(fr), consistency),
                                                  oba="Outcome, Benefit, Asset: accepted by Stewards only", source="records read under your own rights"))
    if model == "synapsys.asset" and ctx.get("record_screen_html"):
        r = ctx["record_screen_html"]("SCR.ASSET.RECORD", rid, depth)
        h = _safe_embed(r.get("html")) if isinstance(r, dict) and r.get("result") == "OK" else None
        out["record_screen"] = {"state": "OK" if h else "REFUSED", "html": h}
    return out
