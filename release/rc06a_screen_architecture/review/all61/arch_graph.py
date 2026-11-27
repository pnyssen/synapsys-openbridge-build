"""Common Architecture resolver (source-only candidate). No Odoo imports, SQL or writes.

One path for every menu family:
  definition -> model -> field -> relationship -> permitted record -> eligible verb -> operating state

Inputs are plain data (a live read snapshot, or a fixture). Actor rights are INPUT, never
decided here: the real boundary is Odoo's server-side ACL and record rules.
"""
import hashlib
import json

CUT_B = {"K-1": "Enable", "K-3": "Enable", "K-4": "Enable",
         "K-6": "Enhance", "K-8": "Enhance", "K-12": "Enrich"}
ACTION_GROUPS = {"Form": ("Orient", "Canonicalise", "Structure"),
                 "Flow": ("Assure", "Navigate", "Compose"),
                 "Evolve": ("Activate", "Transform", "Project")}
PERSPECTIVES = tuple(ACTION_GROUPS)

# Typed edge catalogue. (from_model, field, type, to_model, perspective, evidence)
# evidence OBSERVED = read with fields_get on synapsys_v20, 28 Nov 2026 (this run).
EDGES = [
    ("synapsys.context", "purpose_id", "many2one", "synapsys.purpose", "Form", "OBSERVED"),
    ("synapsys.strategy", "context_id", "many2one", "synapsys.context", "Form", "OBSERVED"),
    ("synapsys.strategy", "purpose_id", "many2one", "synapsys.purpose", "Form", "OBSERVED"),
    ("synapsys.asset", "context_id", "many2one", "synapsys.context", "Form", "OBSERVED"),
    ("synapsys.asset", "rights_holder_id", "many2one", "res.partner", "Form", "OBSERVED"),
    ("synapsys.service", "context_id", "many2one", "synapsys.context", "Form", "OBSERVED"),
    ("synapsys.method", "context_id", "many2one", "synapsys.context", "Form", "OBSERVED"),
    ("synapsys.method", "canon_id", "many2one", "synapsys.canon", "Form", "OBSERVED"),
    ("synapsys.strategy", "service_ids", "many2many", "synapsys.service", "Flow", "OBSERVED"),
    ("synapsys.service", "method_id", "many2one", "synapsys.method", "Flow", "OBSERVED"),
    ("synapsys.work.object", "strategy_id", "many2one", "synapsys.strategy", "Flow", "OBSERVED"),
    ("synapsys.work.object", "service_id", "many2one", "synapsys.service", "Flow", "OBSERVED"),
    ("synapsys.work.object", "method_id", "many2one", "synapsys.method", "Flow", "OBSERVED"),
    ("synapsys.work.object", "gate_ids", "one2many", "synapsys.gate.decision", "Flow", "OBSERVED"),
    ("synapsys.work.object", "progress_outcome_id", "many2one", "synapsys.outcome", "Evolve", "OBSERVED"),
    ("synapsys.work.object", "progress_benefit_id", "many2one", "synapsys.benefit", "Evolve", "OBSERVED"),
    ("synapsys.work.object", "progress_asset_id", "many2one", "synapsys.asset", "Evolve", "OBSERVED"),
    ("synapsys.outcome", "benefit_ids", "many2many", "synapsys.benefit", "Evolve", "OBSERVED"),
    ("synapsys.benefit", "service_id", "many2one", "synapsys.service", "Evolve", "OBSERVED"),
    ("synapsys.oba.link", "benefit_id", "many2one", "synapsys.benefit", "Evolve", "OBSERVED"),
    ("synapsys.oba.link", "asset_id", "many2one", "synapsys.asset", "Evolve", "OBSERVED"),
]
# NOT edges: there is no Strategy -> Asset field. Never inferred from Context membership.
FORBIDDEN_PAIRS = {("synapsys.strategy", "synapsys.asset")}

# Operational journey, in order. Each hop names how to find the next record from the last.
CHAIN = [
    ("Context", "synapsys.context", None),
    ("Purpose", "synapsys.purpose", ("synapsys.context", "purpose_id", "fwd")),
    ("Strategy", "synapsys.strategy", ("synapsys.strategy", "purpose_id", "rev")),
    ("Service", "synapsys.service", ("synapsys.strategy", "service_ids", "fwd")),
    ("Method", "synapsys.method", ("synapsys.service", "method_id", "fwd")),
    ("Work Object", "synapsys.work.object", ("synapsys.work.object", "method_id", "rev")),
    ("Outcome", "synapsys.outcome", ("synapsys.work.object", "progress_outcome_id", "fwd")),
    ("Benefit", "synapsys.benefit", ("synapsys.outcome", "benefit_ids", "fwd")),
    ("Asset", "synapsys.asset", ("synapsys.oba.link", "asset_id", "via_benefit")),
]


class NoWriteRights(Exception):
    pass


def edges_for(perspective):
    return [e for e in EDGES if e[4] == perspective]


def edge_defined(from_model, to_model):
    if (from_model, to_model) in FORBIDDEN_PAIRS:
        return False
    return any(e[0] == from_model and e[3] == to_model for e in EDGES)


# ---- record state: what an ACTOR can honestly say about a table ----------------------
def record_state(model, counts, restricted, reference_only=False, count_key=None):
    """Zero visible to a read-only actor is NEVER reported as EMPTY: it may be restriction."""
    if model in restricted:
        return "RESTRICTED"
    n = counts.get(count_key or model)
    if n is None:
        return "NOT_TESTED"
    if n > 0:
        return "REFERENCE_ONLY" if reference_only else "REAL_ACTOR_VISIBLE"
    return "UNOBSERVED_ZERO_VISIBLE"


# ---- kind -> eligible verbs ----------------------------------------------------------
def eligible_verbs(context, verbs, modes):
    """Verbs come only from a RULED Context kind. Human-only verbs are never eligible for
    automated execution. Eligibility never authorises execution."""
    kind = (context or {}).get("kind")
    if kind not in CUT_B or not (context or {}).get("kind_ruling"):
        return {"state": "UNKNOWN_HOLD", "kind": None, "cut_b": None,
                "verb_ids": [], "execution_authorised": False}
    by_id = {v["id"]: v for v in verbs}
    ids = [i for i in modes.get(kind, []) if i in by_id and not by_id[i]["human_only"]]
    return {"state": "ELIGIBLE_LIST", "kind": kind, "cut_b": CUT_B[kind],
            "verb_ids": sorted(ids), "execution_authorised": False}


def display_depth_is_not_stage(depth, context):
    """Enable/Enhance/Enrich as a presentation depth never confers a kind."""
    kind = (context or {}).get("kind")
    return {"display_depth": depth, "stage": CUT_B.get(kind) if (context or {}).get("kind_ruling") else None}


# ---- graph access, always through actor visibility ------------------------------------
def _visible(actor, model, rid):
    return rid in actor.get("visible", {}).get(model, ())


def _rec(graph, model, rid):
    return graph.get("records", {}).get(model, {}).get(rid)


def _targets(rec, field):
    v = rec.get(field)
    if v in (None, False, []):
        return []
    return list(v) if isinstance(v, (list, tuple)) else [v]


def project(graph, actor, model, rid, perspective):
    """Form / Flow / Evolve: the SAME element, different typed edges walked from it.
    A caption-only switch would return identical nodes and edges and must fail the tests."""
    if perspective not in PERSPECTIVES:
        raise ValueError(perspective)
    if not _visible(actor, model, rid) or _rec(graph, model, rid) is None:
        return {"state": "DENIED_REDACTED", "perspective": perspective, "nodes": [], "edges": []}
    nodes, edges = {(model, rid)}, []
    frontier = [(model, rid)]
    seen = set()
    while frontier:
        cm, cid = frontier.pop()
        if (cm, cid) in seen:
            continue
        seen.add((cm, cid))
        for (fm, field, typ, tm, p, ev) in edges_for(perspective):
            rec = _rec(graph, cm, cid)
            if fm == cm and rec is not None:
                for t in _targets(rec, field):
                    if _visible(actor, tm, t) and _rec(graph, tm, t) is not None:
                        edges.append({"from": [cm, cid], "field": field, "type": typ, "to": [tm, t]})
                        nodes.add((tm, t))
                        frontier.append((tm, t))
    return {"state": "PROJECTED", "perspective": perspective,
            "nodes": sorted(map(list, nodes)), "edges": sorted(edges, key=json.dumps)}


def walk_chain(graph, actor, context_id):
    """Context -> Purpose -> Strategy -> Service -> Method -> Work -> Outcome -> Benefit -> Asset.
    Stops truthfully at the first hop that is missing, unobserved, or not permitted."""
    steps, cur = [], {"synapsys.context": context_id}
    if not _visible(actor, "synapsys.context", context_id) or _rec(graph, "synapsys.context", context_id) is None:
        return {"stopped_at": "Context", "reason": "UNOBSERVED_TO_ACTOR", "steps": [
            {"step": "Context", "state": "UNOBSERVED_TO_ACTOR"}]}
    steps.append({"step": "Context", "state": "CONNECTED", "id": context_id})
    prev_model, prev_ids = "synapsys.context", [context_id]
    for name, model, how in CHAIN[1:]:
        found = []
        fm, field, mode = how
        if mode == "fwd":
            for pid in prev_ids:
                rec = _rec(graph, fm, pid)
                if rec is not None:
                    found += _targets(rec, field)
        elif mode == "rev":
            for rid, rec in graph.get("records", {}).get(fm, {}).items():
                if any(t in prev_ids for t in _targets(rec, field)):
                    found.append(rid)
        elif mode == "via_benefit":
            for rid, rec in graph.get("records", {}).get("synapsys.oba.link", {}).items():
                if rec.get("benefit_id") in prev_ids and rec.get("asset_id") is not None:
                    found.append(rec["asset_id"])
        have = [i for i in found if _rec(graph, model, i) is not None]
        ok = [i for i in have if _visible(actor, model, i)]
        if not have:
            steps.append({"step": name, "state": "MISSING"})
            return {"stopped_at": name, "reason": "MISSING", "steps": steps}
        if not ok:
            steps.append({"step": name, "state": "DENIED_REDACTED"})
            return {"stopped_at": name, "reason": "DENIED_REDACTED", "steps": steps}
        # Cross-Context association is never accepted as a Strategy/Asset of this Context.
        if model in ("synapsys.asset", "synapsys.strategy"):
            ctx = [i for i in ok if _rec(graph, model, i).get("context_id") == context_id]
            if not ctx:
                steps.append({"step": name, "state": "WRONG_CONTEXT"})
                return {"stopped_at": name, "reason": "WRONG_CONTEXT", "steps": steps}
            ok = ctx
        steps.append({"step": name, "state": "CONNECTED", "ids": sorted(ok)})
        prev_ids = ok
    return {"stopped_at": None, "reason": None, "steps": steps}


def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()
