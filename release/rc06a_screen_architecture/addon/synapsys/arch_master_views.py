"""Master Architecture VIEWS (source-only candidate; NOT installed). Pure functions over the RC01 engine: no Odoo import, SQL, sudo or write.

One engine, many doorways: every view is a projection of arch_master.build_master / arch_graph over the caller's own rights. Nothing here
defines architecture, promotes PPV/Benefit/Asset, or authorises execution. Honest states only (CONNECTED, RESTRICTED, NONE_VISIBLE_TO_ACTOR,
DEFINED_NO_READABLE_INSTANCE, FIELD_NOT_PRESENT, HOLD, UNOBSERVED). Counts are of rows the actor can read; hidden rows are never counted or named.

Perspectives (Form/Flow/Evolve) change which typed edges and instance edges are shown. Display depth (enable/enhance/enrich) changes how much
DETAIL is shown for the same data; it never changes data, a K-kind, a stage, a right or an outcome.
"""
import json

try:
    from . import arch_graph as G, arch_master as A, arch_master_drill as DR
except ImportError:                       # offline tests load these files by path, outside a package
    import arch_graph as G
    import arch_master as A
    import arch_master_drill as DR

SECTIONS = ("overview", "value", "kinematics", "fractals", "perspectives", "effects", "mesh", "drill", "actors", "evidence", "holds")
ACTORS = ("steward", "collaborator", "client")
DEPTHS = A.DEPTHS
STRATEGY_GROUPS = ("live", "build", "adapt")
BOOLEAN_FIELDS = frozenset({"baseline_observed", "qualifies", "rights_confirmed"})

# Explicit local HOLDs: unresolved architectural rules and unavailable capabilities, shown rather than silently decided.
HOLDS = (
    ("H01", "Stage versus display depth", "RULING_OPEN",
     "Stage comes only from a ruled Context K-kind (Cut B: K-1/3/4 Enable, K-6/8 Enhance, K-12 Enrich). Enable/Enhance/Enrich is presentation depth only. The unresolved stage-conflict ruling is not decided here; no stage is shown for an unruled kind."),
    ("H02", "Collaborator and Client perspectives", "SOURCE_PARTIAL_NOT_TESTED",
     "Collaborator: the group exists in the installed security source (synapsys.group_synapsys_user, display name Collaborator) with read-mostly, row-scoped access per ir.access.csv; no real Collaborator account has been tested, so its view is NOT_TESTED. Client: no Client group, privilege or access row exists in the source, so that perspective is HOLD. No group is created and no right is inferred or widened here."),
    ("H03", "Master menu home and release", "RELEASE_REQUIRED",
     "Menu and action definitions are unreleased candidates in addon/synapsys/candidates/, outside the manifest. No live menu without an exact D007 release and a Steward ruling on its semantic home."),
    ("H04", "Product and Industry nouns", "SOURCE_OPEN",
     "Source status OPEN. No definition is invented and no operational instance is implied."),
    ("H05", "Verb grammar status", "SOURCE_CANDIDATE",
     "All 27 verbs carry grammar_status=candidate. Nothing is promoted and no verb is executable from this interface."),
    ("H06", "Service to Context and Method links", "RELEASE_REQUIRED",
     "Services carry no direct Context or Method FK in the observed source. 19 source-backed Context links need their own D007 release. A blank link is labelled NO_DIRECT_SERVICE_CONTEXT_FK, not asserted absent."),
    ("H07", "Realisation", "NEVER_PROMOTED_BY_AI",
     "Realisation needs an observed Outcome, an accepted net Benefit and a qualified Asset. This interface shows source values only; it never promotes PPV, Benefit, Asset or Realisation."),
    ("H08", "Purpose.context_ids stored flag", "RULING_OPEN",
     "Open question carried from the post-rowscope gate; no inference is made from it."),
    ("H09", "Strategy to Asset", "NO_SOURCE_EDGE",
     "There is no Strategy to Asset field. The historical cross-Context link is shown as a membrane case, never as a Strategy to Asset edge."),
    ("H10", "CoWork prototype source", "NOT_ACCESSIBLE",
     "The v1.1 prototype artifact source was not retrievable from this session. This interface follows the design recorded in the CoWork returns (drill-down, 3x3 as a lens only, definition versus effective configuration versus actual records, Cut B 3/2/1). Nothing from the prototype is copied as canon."),
)


def _ids(graph, actor, model):
    return A._readable_ids(graph, actor, model)


def _rec(graph, model, rid):
    return graph["records"].get(model, {}).get(rid) or {}


def _label(graph, model, rid):
    r = _rec(graph, model, rid)
    return str(r.get("code") or r.get("name") or "%s/%s" % (model.split(".")[-1], rid))


def _state(actor, notes, model):
    if model in actor["restricted_models"]:
        return "RESTRICTED"
    if model in notes["model_absent"]:
        return "MODEL_NOT_INSTALLED"
    return "OK"


def _tally(graph, actor, notes, model, field):
    """Distribution of ONE source field over rows the actor can read. Absent field and restricted model are stated, never zeroed."""
    st = _state(actor, notes, model)
    if st != "OK":
        return {"state": st, "total": None, "by_value": {}}
    if field in notes["field_absent"].get(model, ()):
        return {"state": "FIELD_NOT_PRESENT", "total": None, "by_value": {}}
    ids = _ids(graph, actor, model)
    by = {}
    for i in ids:
        v = _rec(graph, model, i).get(field)
        k = "(unset)" if v in (None, "") or (v is False and field not in BOOLEAN_FIELDS) else str(v)     # a False many2one/char means unset; a Boolean field's False is a value
        by[k] = by.get(k, 0) + 1
    return {"state": "REAL_ACTOR_VISIBLE" if ids else "NONE_VISIBLE_TO_ACTOR", "total": len(ids) if ids else None, "by_value": dict(sorted(by.items()))}


# ---------------------------------------------------------------------------------------------------------------- Value
def value_view(defn, graph, actor, notes, strategy_groups=None, depth="enable"):
    """Purpose / Strategies / Assets, with Strategy Live / Build / Adapt. Group comes only from the declared source mapping (strategy code -> group)."""
    groups = strategy_groups or {}
    pur, strat, ast = _ids(graph, actor, "synapsys.purpose"), _ids(graph, actor, "synapsys.strategy"), _ids(graph, actor, "synapsys.asset")
    by_group = {g: [] for g in STRATEGY_GROUPS}
    ungrouped = []
    for s in strat:
        g = groups.get(_rec(graph, "synapsys.strategy", s).get("code"))
        (by_group[g] if g in by_group else ungrouped).append(s)
    edges = {}
    for key, (fm, field, tm) in {"context_to_purpose": ("synapsys.context", "purpose_id", "synapsys.purpose"),
                                 "strategy_to_purpose": ("synapsys.strategy", "purpose_id", "synapsys.purpose"),
                                 "strategy_to_context": ("synapsys.strategy", "context_id", "synapsys.context"),
                                 "asset_to_context": ("synapsys.asset", "context_id", "synapsys.context")}.items():
        pairs = A._instance_edges(graph, actor, fm, field, tm)
        edges[key] = {"state": A._edge_state(graph, actor, notes, fm, field, tm, len(pairs)), "instance_edges": len(pairs)}
    detail = depth != "enable"
    return {"purposes": {"state": _state(actor, notes, "synapsys.purpose") if _state(actor, notes, "synapsys.purpose") != "OK" else ("REAL_ACTOR_VISIBLE" if pur else "NONE_VISIBLE_TO_ACTOR"),
                         "count": len(pur) if pur else None, "items": [{"id": i, "label": _label(graph, "synapsys.purpose", i)} for i in pur] if detail else []},
            "strategies": {"state": _state(actor, notes, "synapsys.strategy") if _state(actor, notes, "synapsys.strategy") != "OK" else ("REAL_ACTOR_VISIBLE" if strat else "NONE_VISIBLE_TO_ACTOR"),
                           "count": len(strat) if strat else None,
                           "groups": {g: {"count": len(v) or None, "items": [{"id": i, "label": _label(graph, "synapsys.strategy", i)} for i in v] if detail else []} for g, v in by_group.items()},
                           "ungrouped_count": len(ungrouped) or None, "group_source": "declared strategy code -> Live/Build/Adapt mapping (models/work.py); never inferred"},
            "assets": {"state": _state(actor, notes, "synapsys.asset") if _state(actor, notes, "synapsys.asset") != "OK" else ("REAL_ACTOR_VISIBLE" if ast else "NONE_VISIBLE_TO_ACTOR"),
                       "count": len(ast) if ast else None, "items": [{"id": i, "label": _label(graph, "synapsys.asset", i),
                                                                      "context_id": _rec(graph, "synapsys.asset", i).get("context_id")} for i in ast] if detail else []},
            "edges": edges, "no_strategy_to_asset_edge": True}


# ---------------------------------------------------------------------------------------------------------------- Kinematics
def kinematics_view(defn, graph, actor, notes, depth="enable"):
    verbs = {v["id"]: v for v in defn["verbs"]}
    cut = {"Enable": sorted(k for k, s in G.CUT_B.items() if s == "Enable"), "Enhance": sorted(k for k, s in G.CUT_B.items() if s == "Enhance"),
           "Enrich": sorted(k for k, s in G.CUT_B.items() if s == "Enrich")}
    actions = []
    for group, names in G.ACTION_GROUPS.items():
        for name in names:
            ids = defn["action_verbs"].get(name, [])
            actions.append({"perspective": group, "action": name, "verbs": [{"id": i, "name": verbs[i]["name"], "human_only": verbs[i]["human_only"],
                                                                              "grammar_status": verbs[i]["grammar_status"]} for i in ids]})
    ctxs = []
    for cid in _ids(graph, actor, "synapsys.context"):
        r = _rec(graph, "synapsys.context", cid)
        ruled = bool(r.get("kind") and r.get("kind_ruling"))
        el = G.eligible_verbs({"kind": r.get("kind"), "kind_ruling": r.get("kind_ruling")}, defn["verbs"], defn["modes"])
        ctxs.append({"context_id": cid, "label": _label(graph, "synapsys.context", cid), "kind": r.get("kind") if ruled else None,
                     "kind_state": "RULED" if ruled else "UNRULED_HOLD", "stage": G.CUT_B.get(r.get("kind")) if ruled else None,
                     "eligible": el, "eligible_names": [verbs[i]["name"] for i in el["verb_ids"]] if depth != "enable" else []})
    return {"cut_b": cut, "modes": {k: sorted(v) for k, v in sorted(defn["modes"].items())}, "actions": actions, "contexts": ctxs,
            "human_only_ids": sorted(i for i, v in verbs.items() if v["human_only"]), "execution_authorised": False,
            "stage_vs_depth": "HOLD:H01"}


# ---------------------------------------------------------------------------------------------------------------- Fractals
def fractals_view(defn, graph, actor, notes, depth="enable"):
    """Recursive lens: the lineage tree from stored FKs the actor can read (cycle-safe), and the fractal evidence records the actor can read."""
    parents = A.lineage_parents(graph, actor)
    kids = {}
    for child, par in parents.items():
        kids.setdefault(par, []).append(child)
    roots = sorted(p for p in kids if p not in parents)
    seen = set()

    def node(tag, level):
        if tag in seen:
            return {"id": tag, "cycle": True}
        seen.add(tag)
        return {"id": tag, "children": [node(c, level + 1) for c in sorted(kids.get(tag, ()))]}
    tree = [node(r, 0) for r in roots]
    return {"lineage_basis": "stored FK only (purpose_id, context_id) read through the actor's rights; never inferred from names, codes or captions",
            "tree": tree, "nodes": len(parents) + len(roots), "fractal_records": {"ffe_position": _tally(graph, actor, notes, "synapsys.fractal", "ffe_position"),
                                                                                 "evidence_state": _tally(graph, actor, notes, "synapsys.fractal", "evidence_state")},
            "recursion": "the same element, relationship, source and depth rules apply at every level"}


# ---------------------------------------------------------------------------------------------------------------- Perspectives
def perspectives_view(defn, graph, actor, notes, perspective, depth="enable", context_id=None):
    """Form / Flow / Evolve for the SAME definition and instances: only menus that carry a typed edge in this perspective are listed."""
    m = A.build_master(defn, graph, actor, notes, perspective, depth, context_id)
    rows = [{"menu_id": x["menu_id"], "path": x["path"], "model": x["model"], "record_state": x["record_state"]["state"], "edges": x["edges"],
             "matrix_status": x["matrix_status"], "hold": x["hold"]} for x in m["menus"] if x["edges"]]
    return {"perspective": perspective, "typed_edges": m["edge_totals"]["typed_edges"], "instance_edges": m["edge_totals"]["instance_edges"],
            "menus_with_edges": len(rows), "menus_total": len(m["menus"]), "rows": rows,
            "edges_elsewhere": sum(x["edges_in_other_perspectives"] for x in m["menus"])}


# ---------------------------------------------------------------------------------------------------------------- Enterprise effects
def effects_view(defn, graph, actor, notes, depth="enable"):
    """Enterprise Signal / Benefits / Realisation. Effects, not data levels and not a 9-cell symmetry. Source values only; never promoted."""
    real = _tally(graph, actor, notes, "synapsys.fractal", "realisation")
    return {"signal": {"records": _tally(graph, actor, notes, "synapsys.signal", "state")},
            "benefits": {"records": _tally(graph, actor, notes, "synapsys.benefit", "ppv"), "outcomes_baseline_observed": _tally(graph, actor, notes, "synapsys.outcome", "baseline_observed"),
                         "qualified_assets": _tally(graph, actor, notes, "synapsys.asset", "qualifies"),
                         "benefit_asset_links": {"count": len(_ids(graph, actor, "synapsys.oba.link")) or None}},
            "realisation": {"source_values": real, "rule": "observed Outcome + accepted net Benefit + qualified Asset; otherwise UNOBSERVED",
                            "state": "UNOBSERVED" if not real["total"] else "SOURCE_VALUES_SHOWN_NOT_VERIFIED", "ai_promotion": False, "ppv_movement": False}}


# ---------------------------------------------------------------------------------------------------------------- One Mesh
def mesh_view(defn, graph, actor, notes, depth="enable"):
    """Scaffold (Context and its direct members), Membrane (readable cross-Context relationships) and External (rights holders, partners)."""
    scaffold = []
    for cid in _ids(graph, actor, "synapsys.context"):
        row = {"context_id": cid, "label": _label(graph, "synapsys.context", cid)}
        for key, model in (("strategies", "synapsys.strategy"), ("services_direct_fk", "synapsys.service"), ("methods", "synapsys.method"), ("assets", "synapsys.asset")):
            if _state(actor, notes, model) != "OK":
                row[key] = _state(actor, notes, model); continue
            n = sum(1 for i in _ids(graph, actor, model) if _rec(graph, model, i).get("context_id") == cid)
            row[key] = n or None
        scaffold.append(row)
    membrane = []
    for (fm, field, typ, tm, p, ev) in G.EDGES:
        if fm in actor["restricted_models"] or tm in actor["restricted_models"]:
            continue
        for sid, t in A._instance_edges(graph, actor, fm, field, tm):
            cs = sid if fm == "synapsys.context" else _rec(graph, fm, sid).get("context_id")
            ct = t if tm == "synapsys.context" else _rec(graph, tm, t).get("context_id")
            if cs not in (None, False) and ct not in (None, False) and cs != ct:
                membrane.append({"edge": "%s.%s" % (fm, field), "from_context": cs, "to_context": ct, "ruling": "UNRULED_NOT_ACCEPTED", "perspective": p})
    external = {"asset_rights_holder": _tally(graph, actor, notes, "synapsys.asset", "rights_holder_id"),
                "context_partner": _tally(graph, actor, notes, "synapsys.context", "partner_id"),
                "rights_confirmed": _tally(graph, actor, notes, "synapsys.asset", "rights_confirmed")}
    return {"scaffold": scaffold, "membrane": sorted(membrane, key=json.dumps), "external": external,
            "membrane_rule": "a readable cross-Context relationship is shown as a membrane case; it is never accepted as a member of the other Context"}


# ---------------------------------------------------------------------------------------------------------------- Actors
def actors_view(defn, role, requested="steward", roles=None):
    """Rights come from the SERVER-SIDE role of the real account. Selecting another perspective never widens data: it shows definition-level
    entitlement only (from the installed security source), labelled NOT_TESTED. role: 'steward' | 'collaborator' | 'other'."""
    if requested not in ACTORS:
        raise ValueError(requested)
    steward_only = sorted(m["menu_id"] for m in defn["menus"] if m.get("steward_only"))
    own = role if role in ("steward", "collaborator") else None
    perspectives = {"steward": {"state": "ACTUAL_ACCOUNT" if own == "steward" else "NOT_YOUR_ACCOUNT"},
                    "collaborator": {"state": "ACTUAL_ACCOUNT" if own == "collaborator" else "GROUP_IN_SOURCE_NOT_TESTED"},
                    "client": {"state": "HOLD:H02"}}
    out = {"actual_role": role, "requested": requested, "data_view": "ACTUAL_ACCOUNT" if requested == own else "DEFINITION_ONLY_NOT_TESTED",
           "steward_only_menu_ids": steward_only, "menus_total": len(defn["menus"]), "perspectives": perspectives,
           "role_definitions": role_definitions(defn, roles)}
    for k, v in perspectives.items():
        v["entitled_menus"] = out["role_definitions"]["entitled_menus"].get(k)
    return out


def role_definitions(defn, roles):
    """Existing role definitions as DEFINITION facts. Entitled menus = menus whose model the group can read per ir.access.csv (container and
    client menus are navigation only and are not counted). Row scoping is shown, never evaluated: the real rule is Odoo's server-side record rule."""
    if roles is None:
        return {"state": "ROLES_NOT_LOADED", "entitled_menus": {}, "groups": {}, "client": "HOLD:H02"}
    gk = {"steward": "synapsys.group_synapsys_steward", "collaborator": "synapsys.group_synapsys_user"}
    implied = {"synapsys.group_synapsys_steward": {"synapsys.group_synapsys_steward", "synapsys.group_synapsys_user"}, "synapsys.group_synapsys_user": {"synapsys.group_synapsys_user"}}
    models = sorted({m["model"] for m in defn["menus"] if m.get("model")})
    ent, rows = {}, {}
    for who, g in gk.items():
        n = 0
        for model in models:
            acc = roles["access"].get(model, {})
            rows_g = [acc[x] for x in sorted(implied[g]) if x in acc]
            ops = "".join(sorted(set("".join(r["operations"] for r in rows_g)))) or None
            granting = [r for r in rows_g if "r" in r["operations"]]
            # additive ACL rows: unscoped if ANY granting row is unscoped; scoped only if every granting row carries a row rule (shown, never evaluated)
            rows.setdefault(model, {})[who] = {"operations": ops or "NO_ROW_IN_THIS_ADDON", "row_scoped": bool(granting) and all(r["row_scoped"] for r in granting)}
            if ops and "r" in ops:
                n += sum(1 for m in defn["menus"] if m.get("model") == model)
        ent[who] = n
    ent["client"] = None
    return {"state": "LOADED", "groups": {k: {"display_name": v["display_name"], "implies": v["implies"]} for k, v in roles["groups"].items()},
            "client": "HOLD:H02", "client_note": roles["client_note"], "entitled_menus": ent,
            "entitled_basis": "menus whose model has a read row in this addon's ir.access.csv; models governed by another addon (for example synapsys_mesh) show NO_ROW_IN_THIS_ADDON and are not counted", "by_model": rows, "pins": roles["source_pins"]}


# ---------------------------------------------------------------------------------------------------------------- Evidence
def evidence_view(defn, graph, actor, notes, depth="enable", acceptance=None):
    """Operational evidence beyond counts: per readable Context the actual chain walk (which hop is connected, supporting Work Objects, direct
    Service->Context labels), the definition pins, and the menu acceptance matrix (source facts, not role test results)."""
    chains = []
    for cid in _ids(graph, actor, "synapsys.context"):
        w = G.walk_chain(graph, actor, cid)
        steps = []
        for s in w["steps"]:
            row = {"step": s["step"], "state": s["state"]}
            if depth != "enable":
                for k in ("id", "ids", "supporting_work_ids", "service_context_link", "relationship_basis"):
                    if k in s:
                        row[k] = s[k]
            steps.append(row)
        chains.append({"context_id": cid, "label": _label(graph, "synapsys.context", cid), "stopped_at": w["stopped_at"], "reason": w["reason"], "steps": steps})
    status = {}
    for m in defn["menus"]:
        status[m["matrix_status"]] = status.get(m["matrix_status"], 0) + 1
    return {"chains": chains, "pins": defn["source_pins"], "menu_status_counts": dict(sorted(status.items())),
            "definition_states": {k: sum(1 for m in defn["menus"] if m["definition_state"] == k) for k in sorted({m["definition_state"] for m in defn["menus"]})},
            "acceptance": acceptance or {"state": "NOT_LOADED"}, "role_tests": "NOT_TESTED", "browser_tests": "NOT_TESTED_IN_V20",
            "installed": False}


def assemble(defn, graph, actor, notes, role="collaborator", section="overview", perspective="Form", depth="enable", requested_actor="steward",
             strategy_groups=None, context_id=None, acceptance=None, roles=None, drill="app", ctx=None, ov=""):
    """Everything the page needs for one navigation state. Unknown section / perspective / depth / actor raise ValueError (no silent default)."""
    if section not in SECTIONS:
        raise ValueError(section)
    if perspective not in G.PERSPECTIVES:
        raise ValueError(perspective)
    if depth not in DEPTHS:
        raise ValueError(depth)
    out = {"schema": "synapsys.arch.master.page.v1", "status": "SOURCE_READY_NOT_INSTALLED", "read_only": True, "writes": 0, "section": section,
           "perspective": perspective, "depth": depth, "definition": {"schema": defn["schema"], "counts": defn["counts"], "pins": defn["source_pins"]},
           "actors": actors_view(defn, role, requested_actor, roles), "holds": [{"id": h[0], "title": h[1], "state": h[2], "text": h[3]} for h in HOLDS],
           "notes": {k: notes[k] for k in ("field_absent", "truncated", "model_absent")}}
    if section in ("overview", "value"):
        out["value"] = value_view(defn, graph, actor, notes, strategy_groups, depth)
    if section in ("overview", "kinematics"):
        out["kinematics"] = kinematics_view(defn, graph, actor, notes, depth)
    if section in ("overview", "fractals"):
        out["fractals"] = fractals_view(defn, graph, actor, notes, depth)
    if section in ("overview", "perspectives"):
        out["perspectives"] = {p: perspectives_view(defn, graph, actor, notes, p, depth, context_id) for p in (G.PERSPECTIVES if section == "overview" else (perspective,))}
    if section in ("overview", "effects"):
        out["effects"] = effects_view(defn, graph, actor, notes, depth)
    if section in ("overview", "mesh"):
        out["mesh"] = mesh_view(defn, graph, actor, notes, depth)
    if section in ("overview", "evidence"):
        out["evidence"] = evidence_view(defn, graph, actor, notes, depth, acceptance)
    if section == "drill":
        out["drill"] = DR.drill(defn, graph, actor, notes, drill, ctx, depth, ov)
    return out
