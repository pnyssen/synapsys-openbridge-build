"""Master Architecture builder (source-only candidate; NOT installed, no menu). Pure functions; no Odoo import, SQL, sudo or write.

ONE definition (data/arch_master_definition.json, a versioned FILE) + ONE live-instance projection over the CALLER'S OWN rights.
Reuses arch_graph.py (typed edges, rights-first readability, the Work-supported computed relation) - no second resolver.

Honest states only: CONNECTED (>=1 readable, source-backed instance edge), RESTRICTED (model refused), FIELD_NOT_PRESENT (installed model
lacks the field), NONE_VISIBLE_TO_ACTOR (zero readable rows: never called EMPTY, never told apart from hidden), DEFINED_NO_READABLE_INSTANCE
(rows are readable but none carries this edge), NOT_APPLICABLE (container). Display depth (Enable/Enhance/Enrich) is presentation only and
never confers a K-kind, stage, write right, asset or outcome. Eligibility never authorises execution.
"""
import json
import os

try:
    from . import arch_graph as G
except ImportError:                       # offline tests load this file by path, outside a package
    import arch_graph as G

HERE = os.path.dirname(os.path.abspath(__file__))
READ_LIMIT = 2000
DEPTHS = ("enable", "enhance", "enrich")
BASE_FIELDS = ("name", "code", "context_id", "kind", "kind_ruling")
# Operational-evidence fields read through the caller's own rights, per model. Real field names only (checked against models/*.py); a field the installed
# model lacks is reported in notes.field_absent, never guessed. Never a computed or inferred value; no field here can promote PPV, Benefit or Asset.
EVIDENCE_FIELDS = {
    "synapsys.signal": ("state", "source"),
    "synapsys.outcome": ("baseline_observed", "measure", "observed_date", "acceptance_condition", "evidence_link", "lifecycle"),
    "synapsys.benefit": ("ppv", "position", "lifecycle", "measure", "unit", "direction", "baseline_rule"),
    "synapsys.asset": ("qualifies", "qualified_benefit_count", "rights_confirmed", "lifecycle", "ppv", "rights_holder_id", "asset_class", "class_status"),
    "synapsys.oba.link": ("type", "ppv"),
    "synapsys.fractal": ("realisation", "ffe_position", "evidence_state", "admission", "gate_level", "res_model", "res_id"),
    "synapsys.context": ("partner_id",),
    "synapsys.strategy": ("lifecycle",),
}


def load_definition(path=None):
    p = path or os.path.join(HERE, "data", "arch_master_definition.json")
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None                        # reported as DEFINITION_NOT_LOADED, never guessed


def load_roles(path=None):
    """The EXISTING role definitions (data/arch_master_roles.json, generated from the installed security source). None if missing: stated, never guessed."""
    p = path or os.path.join(HERE, "data", "arch_master_roles.json")
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _models(defn):
    ms = {m["model"] for m in defn["menus"] if m.get("model")}
    for e in defn["typed_edges"]:
        ms.add(e["from_model"]); ms.add(e["to_model"])
    return sorted(ms)


def _wanted_fields(defn, model):
    f = {e["field"] for e in defn["typed_edges"] if e["from_model"] == model}
    f.update(e["field"] for m in defn["menus"] if m.get("model") == model for e in m["edges"])
    return sorted(f | set(BASE_FIELDS) | set(EVIDENCE_FIELDS.get(model, ())))


def collect(env, access_error, defn, limit=READ_LIMIT):
    """Read what THIS actor may read, through the caller's own env. Never widens rights, never raises for access."""
    graph, actor = {"records": {}}, {"visible": {}, "restricted_models": set()}
    notes = {"field_absent": {}, "truncated": [], "restricted": [], "model_absent": []}
    for model in _models(defn):
        try:
            M = env[model]
        except KeyError:
            notes["model_absent"].append(model); continue          # not installed here: stated, not restricted, not empty
        except access_error:
            actor["restricted_models"].add(model); notes["restricted"].append(model); continue
        have = getattr(M, "_fields", None)
        want = _wanted_fields(defn, model)
        fields = [f for f in want if have is None or f in have]
        absent = [f for f in want if have is not None and f not in have and f not in BASE_FIELDS]
        if absent:
            notes["field_absent"][model] = absent
        try:
            rows = M.search_read([], fields, limit=limit + 1)
        except access_error:
            actor["restricted_models"].add(model); notes["restricted"].append(model); continue
        if len(rows) > limit:
            rows = rows[:limit]; notes["truncated"].append(model)
        table = {}
        for r in rows:
            rec = {}
            for f in fields:
                v = r.get(f)
                rec[f] = (v[0] if isinstance(v, (list, tuple)) and len(v) == 2 and isinstance(v[0], int) and isinstance(v[1], str) else v)
            table[r["id"]] = rec
        graph["records"][model] = table
        actor["visible"][model] = set(table)
    return graph, actor, notes


def _readable_ids(graph, actor, model):
    return sorted(i for i in graph["records"].get(model, {}) if G._readable(graph, actor, model, i))


def _instance_edges(graph, actor, from_model, field, to_model):
    """Source-backed instance edges the actor can read at BOTH ends (and, for a computed relation, with readable supporting Work)."""
    out = []
    for sid in _readable_ids(graph, actor, from_model):
        for t in G._targets(graph["records"][from_model][sid], field):
            if G._readable(graph, actor, to_model, t) and G._edge_supported(graph, actor, from_model, field, sid, t):
                out.append((sid, t))
    return out


def _edge_state(graph, actor, notes, from_model, field, to_model, n):
    if from_model in actor["restricted_models"] or to_model in actor["restricted_models"]:
        return "RESTRICTED"
    if field in notes["field_absent"].get(from_model, ()):
        return "FIELD_NOT_PRESENT"
    if from_model in notes["model_absent"] or to_model in notes["model_absent"]:
        return "MODEL_NOT_INSTALLED"
    if n:
        return "CONNECTED"
    return "DEFINED_NO_READABLE_INSTANCE" if _readable_ids(graph, actor, from_model) else "NONE_VISIBLE_TO_ACTOR"


def _menu_state(m, graph, actor, notes):
    if m["kind"] == "CONTAINER":
        return {"state": "NOT_APPLICABLE", "reason": "container: navigation and ACLs only, no record model"}
    model = m.get("model")
    if not model:
        return {"state": "NOT_APPLICABLE", "reason": "client action without a record model"}
    if model in actor["restricted_models"]:
        return {"state": "RESTRICTED"}
    if model in notes["model_absent"]:
        return {"state": "MODEL_NOT_INSTALLED"}
    n = len(_readable_ids(graph, actor, model))
    return {"state": "REAL_ACTOR_VISIBLE" if n else "NONE_VISIBLE_TO_ACTOR", "readable_count": n if n else None}


def _verbs_view(defn, graph, actor, context_id=None):
    verbs = defn["verbs"]
    by_action = {a: [v["id"] for v in verbs if v["action"] == a] for a in defn["action_verbs"]}
    ctxs = []
    for cid in _readable_ids(graph, actor, "synapsys.context"):
        if context_id is not None and cid != context_id:
            continue
        rec = graph["records"]["synapsys.context"][cid]
        ruled = bool(rec.get("kind") and rec.get("kind_ruling"))
        el = G.eligible_verbs({"kind": rec.get("kind"), "kind_ruling": rec.get("kind_ruling")}, verbs, defn["modes"])
        ctxs.append({"context_id": cid, "code": rec.get("code"), "kind_ruled": ruled, "eligible": el,
                     "stage": G.CUT_B.get(rec.get("kind")) if ruled else None})
    return {"governed_verbs": len(verbs), "actions": {a: ids for a, ids in sorted(by_action.items())},
            "human_only_ids": sorted(v["id"] for v in verbs if v["human_only"]),
            "grammar_status_counts": {s: sum(1 for v in verbs if v["grammar_status"] == s) for s in sorted({v["grammar_status"] for v in verbs})},
            "execution_authorised": False, "contexts": ctxs}


# Actual relationship lineage for the shared recursive lens (lens_contract.lineage / mode_for). Parent = the record's OWN stored FK, read through the
# actor's rights. Never inferred from names, codes, captions or a Work-mediated relation; a blank or unreadable FK yields NO parent.
LINEAGE_FKS = (("synapsys.context", "purpose_id", "pur", "ctx"), ("synapsys.strategy", "context_id", "ctx", "str"),
               ("synapsys.service", "context_id", "ctx", "svc"), ("synapsys.method", "context_id", "ctx", "mth"),
               ("synapsys.asset", "context_id", "ctx", "ast"))


def lineage_parents(graph, actor):
    """{'svc:30': 'ctx:1', ...}: one hop per DIRECT stored FK whose both ends the actor can read. Feed to lens_contract.lineage."""
    out = {}
    for model, field, ptag, tag in LINEAGE_FKS:
        to_model = {"purpose_id": "synapsys.purpose", "context_id": "synapsys.context"}[field]
        for rid in _readable_ids(graph, actor, model):
            t = G._targets(graph["records"][model][rid], field)
            if len(t) == 1 and G._readable(graph, actor, to_model, t[0]):
                out["%s:%s" % ({"ctx": "ctx", "str": "str", "svc": "svc", "mth": "mth", "ast": "ast"}[tag], rid)] = "%s:%s" % (ptag, t[0])
    return out


def build_master(defn, graph, actor, notes, perspective="Form", depth="enable", context_id=None):
    """The same 61-row definition, projected for ONE perspective. Switching perspective changes which typed edges, instance edges and counts
    are shown, never just a caption. Rights-first: only counts of rows the actor can read; hidden rows are never counted or named."""
    if defn is None:
        return {"state": "DEFINITION_NOT_LOADED", "writes": 0}
    if perspective not in G.PERSPECTIVES:
        raise ValueError(perspective)
    if depth not in DEPTHS:
        raise ValueError(depth)
    persp_edges = {(e["from_model"], e["field"]): e for e in defn["typed_edges"] if e["perspective"] == perspective}
    inst = {}
    for (fm, field), e in persp_edges.items():
        inst[(fm, field)] = _instance_edges(graph, actor, fm, field, e["to_model"])
    menus = []
    for m in defn["menus"]:
        edges = []
        for e in m["edges"]:
            te = persp_edges.get((m.get("model"), e["field"]))
            if te is None:
                continue
            pairs = inst[(m["model"], e["field"])]
            edges.append({"field": e["field"], "target_model": e["target_model"], "cardinality": e["cardinality"], "direction": e["direction"],
                          "type": te["type"], "state": _edge_state(graph, actor, notes, m["model"], e["field"], e["target_model"], len(pairs)),
                          "instance_edges": len(pairs)})
        menus.append({"menu_id": m["menu_id"], "path": m["path"], "kind": m["kind"], "model": m["model"], "source_status": m["source_status"],
                      "definition_state": m["definition_state"], "definition_gap": m["definition_gap"], "matrix_status": m["matrix_status"],
                      "hold": ({"reason": m["status_reason"] or m["definition_gap"]} if m["matrix_status"] in ("HONEST_HOLD", "RELEASE_BLOCKED", "NOT_TESTED") else None),
                      "record_state": _menu_state(m, graph, actor, notes),
                      "edges": edges, "edges_in_other_perspectives": sum(1 for e in m["edges"] if (m.get("model"), e["field"]) not in persp_edges)})
    cut = (lambda c: {"display_depth": depth, **G.display_depth_is_not_stage(depth, c)})
    out = {"schema": "synapsys.arch.master.v1", "read_only": True, "writes": 0, "status": "SOURCE_READY_NOT_INSTALLED",
           "master_menu": "NOT_INSTALLED_RELEASE_REQUIRED", "definition": {"schema": defn["schema"], "pins": defn["source_pins"], "counts": defn["counts"]},
           "perspective": perspective, "display_depth": depth, "depth_note": "presentation only; never a K-kind, stage, right, asset or outcome",
           "notes": {k: notes[k] for k in ("field_absent", "truncated", "model_absent")}, "menus": menus,
           "edge_totals": {"typed_edges": len(persp_edges), "instance_edges": sum(len(v) for v in inst.values())},
           "verbs": _verbs_view(defn, graph, actor, context_id), "role_tests": "NOT_TESTED", "lens_lineage": lineage_parents(graph, actor),
           "stage_by_context": {str(c["context_id"]): cut({"kind": graph["records"]["synapsys.context"][c["context_id"]].get("kind"),
                                                          "kind_ruling": graph["records"]["synapsys.context"][c["context_id"]].get("kind_ruling")})
                                for c in _verbs_view(defn, graph, actor, context_id)["contexts"]}}
    return out


def master_audit(defn, graph, actor, notes):
    """Independent check over all three perspectives. Findings: CAPTION_ONLY, MENU_COUNT_DRIFT, VERB_COUNT_DRIFT, LEAKED_COUNT, INVENTED_EDGE."""
    findings, outs = [], {p: build_master(defn, graph, actor, notes, p) for p in G.PERSPECTIVES}
    for p, o in outs.items():
        if len(o["menus"]) != defn["counts"]["menus"]:
            findings.append({"finding": "MENU_COUNT_DRIFT", "perspective": p})
        if o["verbs"]["governed_verbs"] != 27 or sum(len(v) for v in o["verbs"]["actions"].values()) != 27 or len(o["verbs"]["actions"]) != 9:
            findings.append({"finding": "VERB_COUNT_DRIFT", "perspective": p})
        for m in o["menus"]:
            for e in m["edges"]:
                truth = len(_instance_edges(graph, actor, m["model"], e["field"], e["target_model"]))
                if e["instance_edges"] != truth:
                    findings.append({"finding": "LEAKED_COUNT" if e["instance_edges"] > truth else "INVENTED_EDGE", "perspective": p, "menu_id": m["menu_id"], "field": e["field"]})
                if (m["model"], e["field"]) in G.FORBIDDEN_PAIRS or (m["model"], e["target_model"]) in G.FORBIDDEN_PAIRS:
                    findings.append({"finding": "INVENTED_EDGE", "perspective": p, "menu_id": m["menu_id"], "field": e["field"]})
    sig = {p: json.dumps([[(m["menu_id"], [(e["field"], e["state"], e["instance_edges"]) for e in m["edges"]]) for m in o["menus"]], o["edge_totals"]], sort_keys=True)
           for p, o in outs.items()}
    ps = list(G.PERSPECTIVES)
    for i, p in enumerate(ps):
        for q in ps[i + 1:]:
            if sig[p] == sig[q] and outs[p]["edge_totals"]["typed_edges"]:
                findings.append({"finding": "CAPTION_ONLY", "perspective": "%s=%s" % (p, q)})
    return {"ok": not findings, "findings": findings}
