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


# Context membership: the typed Form edges whose TARGET is a Context. A Context's members are the records that
# point at it through these real fields. Never inferred from names, codes or captions.
MEMBER_EDGES = [e for e in EDGES if e[3] == "synapsys.context" and e[4] == "Form"]


def _restricted(actor, model):
    return model in actor.get("restricted_models", ())


def _readable(graph, actor, model, rid):
    """A record is exposed only if the actor can see it, its model is not restricted, and it exists in the source."""
    return (not _restricted(actor, model)) and _visible(actor, model, rid) and _rec(graph, model, rid) is not None


def _edge_supported(graph, actor, fm, field, sid, tid):
    """strategy.service_ids is a readonly COMPUTED relation derived from Work Objects: the edge exists for this actor only
    if a Work Object the actor can read supports it. Every other typed edge is a stored field and needs no extra support."""
    if (fm, field) == ("synapsys.strategy", "service_ids"):
        return bool(_supporting_work(graph, actor, [sid], tid))
    return True


def _incoming(graph, actor, model, rid, perspective):
    """One hop of governed INCOMING typed edges: records elsewhere whose real field points at (model, rid)."""
    out = []
    for (fm, field, typ, tm, p, ev) in edges_for(perspective):
        if tm != model or _restricted(actor, fm):
            continue
        for sid, rec in graph.get("records", {}).get(fm, {}).items():
            if rid in _targets(rec, field) and _readable(graph, actor, fm, sid) and _edge_supported(graph, actor, fm, field, sid, rid):
                out.append({"from": [fm, sid], "field": field, "type": typ, "to": [model, rid], "direction": "in"})
    return out


def _members(graph, actor, ctx_id):
    return [e for e in (_incoming(graph, actor, "synapsys.context", ctx_id, "Form"))]


def _walk_out(graph, actor, start, perspective, nodes, edges, seen):
    frontier = [start]
    while frontier:
        cm, cid = frontier.pop()
        if (cm, cid) in seen:
            continue
        seen.add((cm, cid))
        rec = _rec(graph, cm, cid)
        if rec is None:
            continue
        for (fm, field, typ, tm, p, ev) in edges_for(perspective):
            if fm != cm:
                continue
            for t in _targets(rec, field):
                if _readable(graph, actor, tm, t) and _edge_supported(graph, actor, cm, field, cid, t):
                    edges.append({"from": [cm, cid], "field": field, "type": typ, "to": [tm, t], "direction": "out"})
                    nodes.add((tm, t))
                    frontier.append((tm, t))


def coverage(graph, actor, model, rid, perspective, projected_edges):
    """Catalogue-level honesty, never record-level: which typed edge kinds touch this model in this perspective, and
    whether any was projected. 'NONE_VISIBLE_TO_ACTOR' deliberately does not say whether absent or restricted."""
    keyed = {(e["from"][0], e["field"], e["to"][0], e["direction"]) for e in projected_edges}
    rows = []
    for (fm, field, typ, tm, p, ev) in edges_for(perspective):
        for d, here, other in (("out", fm, tm), ("in", tm, fm)):
            if here != model:
                continue
            if _restricted(actor, other):
                st = "SOURCE_MODEL_RESTRICTED"
            elif (fm, field, tm, d) in keyed:
                st = "PROJECTED"
            else:
                st = "NONE_VISIBLE_TO_ACTOR"
            rows.append({"edge": "%s.%s" % (fm, field), "direction": d, "state": st})
    return sorted(rows, key=json.dumps)


def project(graph, actor, model, rid, perspective):
    """Form / Flow / Evolve: the SAME element, different typed edges walked from it, outgoing AND governed incoming.
    A Context also exposes its members (records pointing at it) and the perspective's edges among them.
    A caption-only switch would return identical nodes and edges and must fail the tests."""
    if perspective not in PERSPECTIVES:
        raise ValueError(perspective)
    if not _readable(graph, actor, model, rid):
        return {"state": "DENIED_REDACTED", "perspective": perspective, "nodes": [], "edges": [], "coverage": []}
    nodes, edges, seen = {(model, rid)}, [], set()
    _walk_out(graph, actor, (model, rid), perspective, nodes, edges, seen)
    for e in _incoming(graph, actor, model, rid, perspective):          # one governed hop in; does not recurse
        edges.append(e); nodes.add(tuple(e["from"]))
    if model == "synapsys.context":
        for m in _members(graph, actor, rid):                           # Context -> members, then the perspective among them
            mn = tuple(m["from"])
            before = len(edges)
            _walk_out(graph, actor, mn, perspective, nodes, edges, seen)
            for e in _incoming(graph, actor, mn[0], mn[1], perspective):
                edges.append(e); nodes.add(tuple(e["from"]))
            if len(edges) > before:
                nodes.add(mn)
    uniq = {}
    for e in edges:                                                      # one logical edge = one entry, whichever way it was reached
        uniq.setdefault((tuple(e["from"]), e["field"], tuple(e["to"])), e)
    edges = list(uniq.values())
    for e in edges:                                                      # direction is relative to the element being projected
        e["direction"] = "out" if e["from"] == [model, rid] else "in" if e["to"] == [model, rid] else "via"
    edges = sorted(edges, key=json.dumps)
    root_rec = _rec(graph, model, rid) or {}
    root_context = rid if model == "synapsys.context" else root_rec.get("context_id")
    for e in edges:                                                      # flag governed cross-Context relationships at every root
        contexts = []
        for end in (e["from"], e["to"]):
            rec = _rec(graph, end[0], end[1]) or {}
            ctx = end[1] if end[0] == "synapsys.context" else rec.get("context_id")
            if ctx not in (None, False):
                contexts.append(ctx)
        if ((len(contexts) == 2 and contexts[0] != contexts[1])
                or (root_context not in (None, False) and any(c != root_context for c in contexts))):
            e["cross_context"] = True
    return {"state": "PROJECTED", "perspective": perspective,
            "nodes": sorted(map(list, nodes)), "edges": edges,
            "coverage": coverage(graph, actor, model, rid, perspective, edges)}


def projection_audit(graph, actor, model, rid, projector=None):
    """Independent check of a projector against the source. Brute force over the raw records, not the projector's own walk.
    Findings: CAPTION_ONLY, EMPTY_WHERE_SOURCE_BACKED, MISSING_SOURCE_BACKED_EDGE, INVENTED_EDGE, LEAKED_NODE.
    Zero visible is never reported as a defect when no source-backed readable edge exists."""
    projector = projector or project
    findings, out = [], {}
    for p in PERSPECTIVES:
        r = projector(graph, actor, model, rid, p)
        out[p] = r
        truth = set()
        anchors = {(model, rid)}
        if model == "synapsys.context":            # a Context's members are real records that point at it
            for (fm, field, typ, tm, pp, ev) in MEMBER_EDGES:
                for sid, rec in graph.get("records", {}).get(fm, {}).items():
                    if rid in _targets(rec, field) and _readable(graph, actor, fm, sid):
                        anchors.add((fm, sid))
        for (fm, field, typ, tm, pp, ev) in edges_for(p):
            for sid, rec in graph.get("records", {}).get(fm, {}).items():
                for t in _targets(rec, field):
                    if (fm, sid) in anchors or (tm, t) in anchors:
                        if (_readable(graph, actor, fm, sid) and _readable(graph, actor, tm, t) and not _restricted(actor, fm) and not _restricted(actor, tm)
                                and _edge_supported(graph, actor, fm, field, sid, t)):
                            truth.add((fm, sid, field, tm, t))
        got = {(e["from"][0], e["from"][1], e["field"], e["to"][0], e["to"][1]) for e in r.get("edges", [])}
        for miss in sorted(truth - got):
            findings.append({"finding": "EMPTY_WHERE_SOURCE_BACKED" if not got else "MISSING_SOURCE_BACKED_EDGE", "perspective": p, "edge": list(miss)})
        for e in sorted(got):
            rec = _rec(graph, e[0], e[1])
            if rec is None or e[4] not in _targets(rec, e[2]):
                findings.append({"finding": "INVENTED_EDGE", "perspective": p, "edge": list(e)})
        for n in r.get("nodes", []):
            if not _readable(graph, actor, n[0], n[1]):
                findings.append({"finding": "LEAKED_NODE", "perspective": p, "node": n})
    sig = {p: json.dumps([out[p].get("nodes"), out[p].get("edges", [])], sort_keys=True) for p in PERSPECTIVES}
    for i, p in enumerate(PERSPECTIVES):
        for q in PERSPECTIVES[i + 1:]:
            if sig[p] == sig[q] and out[p].get("edges"):
                findings.append({"finding": "CAPTION_ONLY", "perspective": "%s=%s" % (p, q)})
    return {"ok": not findings, "findings": findings}


def _supporting_work(graph, actor, strategy_ids, service_id):
    """Work Objects the ACTOR CAN READ that bind one of these Strategies to this Service. strategy.service_ids is a readonly
    computed relation derived from Work Objects, so a Strategy->Service edge is shown only with a readable supporting Work Object."""
    return sorted(wid for wid, w in graph.get("records", {}).get("synapsys.work.object", {}).items()
                  if w.get("service_id") == service_id and w.get("strategy_id") in strategy_ids
                  and _readable(graph, actor, "synapsys.work.object", wid))


def service_context_link(graph, service_id, context_id):
    """DIRECT Service->Context FK only. Distinct from the Work-mediated Strategy->Service relationship."""
    sc = (_rec(graph, "synapsys.service", service_id) or {}).get("context_id")
    return ("LINKED_TO_THIS_CONTEXT" if sc == context_id else
            "NO_DIRECT_SERVICE_CONTEXT_FK" if sc in (None, False) else "WRONG_CONTEXT")


def walk_chain(graph, actor, context_id):
    """Context -> Purpose -> Strategy -> Service -> Method -> Work -> Outcome -> Benefit -> Asset.
    Rights-first and non-disclosing: existence is judged ONLY over records the actor can read, so a hidden record, an absent record
    and a foreign record are never told apart. When nothing readable continues the chain the step is UNOBSERVED_TO_ACTOR
    (MISSING only where the caller attests complete visibility of that model via actor['complete_view']).
    WRONG_CONTEXT is reported only for a record the actor can already read. Strategy->Service needs a readable supporting Work Object."""
    steps = []
    if not _readable(graph, actor, "synapsys.context", context_id):
        return {"stopped_at": "Context", "reason": "UNOBSERVED_TO_ACTOR", "steps": [
            {"step": "Context", "state": "UNOBSERVED_TO_ACTOR"}]}
    steps.append({"step": "Context", "state": "CONNECTED", "id": context_id})
    prev_ids = [context_id]
    complete = set(actor.get("complete_view", ()))
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
                if rec.get("benefit_id") in prev_ids and rec.get("asset_id") is not None and _readable(graph, actor, "synapsys.oba.link", rid):
                    found.append(rec["asset_id"])
        ok = sorted({i for i in found if _readable(graph, actor, model, i)})
        support = {}
        if model == "synapsys.service":            # Work-mediated: no readable supporting Work Object, no relationship shown
            for i in list(ok):
                w = _supporting_work(graph, actor, prev_ids, i)
                if w:
                    support[i] = w
                else:
                    ok.remove(i)
        if not ok:
            state = "MISSING" if model in complete else "UNOBSERVED_TO_ACTOR"
            steps.append({"step": name, "state": state})
            return {"stopped_at": name, "reason": state, "steps": steps}
        # Cross-Context association is never accepted as a Strategy/Asset of this Context (readable records only).
        if model in ("synapsys.asset", "synapsys.strategy"):
            ctx = [i for i in ok if _rec(graph, model, i).get("context_id") == context_id]
            if not ctx:
                steps.append({"step": name, "state": "WRONG_CONTEXT"})
                return {"stopped_at": name, "reason": "WRONG_CONTEXT", "steps": steps}
            ok = ctx
        step = {"step": name, "state": "CONNECTED", "ids": ok}
        if model == "synapsys.service":
            step["relationship_basis"] = "STRATEGY_SERVICE_IDS_VIA_WORK_OBJECTS"
            step["supporting_work_ids"] = {str(i): support[i] for i in ok}
            step["service_context_link"] = {str(i): service_context_link(graph, i, context_id) for i in ok}
        steps.append(step)
        prev_ids = ok
    return {"stopped_at": None, "reason": None, "steps": steps}


def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()
