"""Read-only, rights-aware Context -> Strategy -> Service slice (source-only candidate; not installed, not released).

Pure functions over an env-like adapter. NO sudo, NO write, NO SQL, NO new model, NO menu. The adapter must be the CALLER'S OWN
environment so Odoo's ACL and record rules decide what is visible; this module never widens that. The common resolver arch_graph.py
(byte-identical to review/all61/arch_graph.py, checked by a test) supplies the typed edges, the Form/Flow/Evolve projection and the audit.

Honest states only: RESTRICTED (access refused), NONE_VISIBLE_TO_ACTOR (zero rows seen; never called EMPTY), FIELD_NOT_PRESENT
(the installed model does not declare the field), REAL_ACTOR_VISIBLE, plus WRONG_CONTEXT / NO_DIRECT_SERVICE_CONTEXT for Services.
"""
import json
import os

try:
    from . import arch_graph as G
except ImportError:                       # offline tests load this file by path, outside a package
    import arch_graph as G

HERE = os.path.dirname(os.path.abspath(__file__))
SLICE_MODELS = {
    "synapsys.context": ("code", "name", "kind", "kind_ruling", "purpose_id"),
    "synapsys.strategy": ("code", "name", "context_id", "purpose_id", "service_ids"),
    "synapsys.service": ("code", "name", "context_id", "method_id"),
    "synapsys.purpose": ("code", "name"),
    "synapsys.method": ("code", "name", "context_id"),
    "synapsys.asset": ("name", "context_id"),
    "synapsys.work.object": ("strategy_id", "service_id", "method_id", "progress_outcome_id"),
    "synapsys.benefit": ("service_id",),
}
READ_LIMIT = 2000                          # bound the read; a truncated read is reported, never hidden


def _acceptance():
    p = os.path.join(HERE, "data", "arch_slice_acceptance.json")
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None                        # missing evidence is reported as NOT_LOADED, never guessed


def collect(env, access_error, limit=READ_LIMIT):
    """Read what THIS actor may read. Returns (graph, actor, notes). Never raises for access; never widens rights."""
    graph = {"records": {}}
    actor = {"visible": {}, "restricted_models": set()}
    notes = {"field_absent": {}, "truncated": [], "restricted": []}
    for model, wanted in SLICE_MODELS.items():
        try:
            M = env[model]
        except (KeyError, access_error):
            actor["restricted_models"].add(model); notes["restricted"].append(model); continue
        have = getattr(M, "_fields", None)
        fields = [f for f in wanted if have is None or f in have]
        absent = [f for f in wanted if have is not None and f not in have]
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


def _tier(model, graph, actor, ids=None):
    if model in actor["restricted_models"]:
        return {"state": "RESTRICTED", "ids": []}
    seen = sorted(i for i in (ids if ids is not None else graph["records"].get(model, {})) if G._readable(graph, actor, model, i))
    return {"state": "REAL_ACTOR_VISIBLE" if seen else "NONE_VISIBLE_TO_ACTOR", "ids": seen}


def build_slice(graph, actor, notes, context_id=None):
    """Context -> Strategy -> Service for the contexts the actor may see. Stops truthfully; invents nothing; reports no hidden ids."""
    out = {"schema": "synapsys.arch.slice.v1", "read_only": True, "writes": 0, "master_menu": "NOT_INSTALLED_RELEASE_REQUIRED",
           "status": "SOURCE_READY_NOT_INSTALLED", "notes": {"field_absent": notes["field_absent"], "truncated": notes["truncated"]}}
    ctx = _tier("synapsys.context", graph, actor)
    if context_id is not None:
        ctx["ids"] = [i for i in ctx["ids"] if i == context_id]
        if not ctx["ids"] and ctx["state"] == "REAL_ACTOR_VISIBLE":
            ctx["state"] = "NONE_VISIBLE_TO_ACTOR"
    out["context"] = ctx
    if not ctx["ids"]:
        out["stopped_at"] = "Context"; out["reason"] = ctx["state"]; out["contexts"] = []; out["acceptance"] = acceptance_view(); return out
    svc_field_ok = "synapsys.strategy" not in notes["field_absent"] or "service_ids" not in notes["field_absent"]["synapsys.strategy"]
    rows = []
    for cid in ctx["ids"]:
        crec = graph["records"]["synapsys.context"][cid]
        strat = _tier("synapsys.strategy", graph, actor,
                      [s for s, r in graph["records"].get("synapsys.strategy", {}).items() if r.get("context_id") == cid])
        sv_rows = []
        for sid in strat["ids"]:
            srec = graph["records"]["synapsys.strategy"][sid]
            if not svc_field_ok:
                sv_rows.append({"strategy": sid, "services": {"state": "FIELD_NOT_PRESENT", "ids": []}}); continue
            targets = [t for t in G._targets(srec, "service_ids")]
            svc = _tier("synapsys.service", graph, actor, targets)
            items = []
            for t in svc["ids"]:
                sc = graph["records"]["synapsys.service"][t].get("context_id")
                items.append({
                    "id": t,
                    "relationship_basis": "STRATEGY_SERVICE_IDS_VIA_WORK_OBJECTS",
                    "link": "LINKED_TO_THIS_CONTEXT" if sc == cid else
                            "NO_DIRECT_SERVICE_CONTEXT" if not sc else "WRONG_CONTEXT",
                })
            svc["items"] = items
            sv_rows.append({"strategy": sid, "services": svc})
        rows.append({"context": {"id": cid, "code": crec.get("code"), "kind": crec.get("kind"),
                                 "kind_ruled": bool(crec.get("kind") and crec.get("kind_ruling"))},
                     "strategies": strat, "strategy_services": sv_rows,
                     "projection": {p: _proj_summary(graph, actor, "synapsys.context", cid, p) for p in G.PERSPECTIVES},
                     "audit": G.projection_audit(graph, actor, "synapsys.context", cid)})
    out["contexts"] = rows
    out["acceptance"] = acceptance_view()
    return out


def _proj_summary(graph, actor, model, rid, perspective):
    r = G.project(graph, actor, model, rid, perspective)
    return {"state": r["state"], "edges": r["edges"], "nodes": r["nodes"], "coverage": r["coverage"]}


def acceptance_view():
    a = _acceptance()
    if a is None:
        return {"state": "NOT_LOADED"}
    return {"state": "LOADED", "matrix_sha256": a["matrix_sha256"], "rows": a["rows"],
            "role_tests": "NOT_TESTED", "note": "matrix statuses are source facts from one read-only actor; they are not role test results"}
