"""Read-only scaffold lens projection (RC05 slice, source-ready candidate).

Pure functions over (a) the Mesh registry body, (b) an actor, (c) evidence records.
No Odoo, no writes, no sudo. The caller (controller) must pass the actor's REAL
Odoo identity (never sudo) and evidence rows read with that actor's own rights;
this module then applies a second, fail-closed filter before anything is returned.

Depth is cumulative: enable < enhance < enrich. Missing operating records are
reported as UNSOURCED / NO_OPERATING_SOURCE (HOLD), never invented.
"""
import hashlib

DEPTHS = ("enable", "enhance", "enrich")
# Policy knobs (a proposal; rights are NOT decided here -- caller may tighten).
ROLE_MAX_DEPTH = {"steward": "enrich", "collaborator": "enrich", "client": "enhance"}
EVIDENCE_GROUPS = {"steward", "collaborator"}
PEERS = ("N.CAPABILITY", "N.SERVICE")


def _depth_ix(d):
    if d not in DEPTHS:
        raise ValueError("unknown depth %r" % (d,))
    return DEPTHS.index(d)


def index_registry(reg):
    els = {e["id"]: e for e in reg["elements"]}
    if len(els) != len(reg["elements"]):
        raise ValueError("duplicate element ids")
    return els


def clusters_for(reg, noun_id):
    out = []
    for c in reg["clusters"]:
        if any(m[1] == noun_id for m in c["members"]):
            out.append(c)
    return out


def _h_of(cluster):
    for role, ref in cluster["members"]:
        if role == "relationship":
            return ref
    return None


def roles_for(reg, els, relationship_id):
    """Human-readable role list for one relationship (e.g. H.CTX)."""
    rows = []
    for c in reg["clusters"]:
        if _h_of(c) != relationship_id:
            continue
        for role, ref in c["members"]:
            if role == "relationship":
                continue
            r, n = els.get(role), els.get(ref)
            rows.append({
                "cluster_id": c["id"],
                "role_id": role,
                "role_label": (r or {}).get("label", role),
                "required": bool((r or {}).get("required", False)),
                "many": bool((r or {}).get("many", False)),
                "bound_id": ref,
                "bound_label": (n or {}).get("label", ref),
                "bound_status": (n or {}).get("status"),
            })
    return sorted(rows, key=lambda x: (not x["required"], x["role_label"], x["bound_id"]))


def _effective_depth(actor, requested, role_max_depth=None):
    table = ROLE_MAX_DEPTH if role_max_depth is None else role_max_depth
    cap = None
    for g in actor.get("groups", ()):
        m = table.get(g)
        if m and (cap is None or _depth_ix(m) > _depth_ix(cap)):
            cap = m
    if cap is None:
        return None  # unknown actor: fail closed
    return DEPTHS[min(_depth_ix(requested), _depth_ix(cap))]


def sha256_hex(b):
    return hashlib.sha256(b).hexdigest()


def _evidence_for(noun_id, actor, evidence, library_index, context_id):
    """Apply Context + group + source-integrity filters BEFORE returning anything."""
    shown, rejected = [], []
    if not (set(actor.get("groups", ())) & EVIDENCE_GROUPS):
        return shown, rejected
    is_steward = "steward" in actor.get("groups", ())
    for rec in evidence:
        if rec.get("noun_id") != noun_id:
            continue
        if rec.get("context_id") != context_id:
            rejected.append({"id": rec.get("id"), "reason": "FOREIGN_CONTEXT"})
            continue
        if not is_steward and context_id not in actor.get("context_ids", ()):
            rejected.append({"id": rec.get("id"), "reason": "ACTOR_NOT_IN_CONTEXT"})
            continue
        src = library_index.get(rec.get("source_ref"))
        if src is None:
            rejected.append({"id": rec.get("id"), "reason": "SOURCE_NOT_FOUND"})
            continue
        if src.get("sha256") != rec.get("sha256"):
            rejected.append({"id": rec.get("id"), "reason": "SOURCE_HASH_MISMATCH"})
            continue
        shown.append({"id": rec["id"], "kind": rec.get("kind"), "source_ref": rec["source_ref"],
                      "sha256": rec["sha256"], "label": src.get("label")})
    return shown, rejected


def _peer_block(els, noun_id, depth, actor, evidence, library_index, context_id):
    n = els[noun_id]
    block = {"id": noun_id, "label": n["label"], "status": n.get("status"),
             "definition": n.get("definition")}
    shown, rejected = _evidence_for(noun_id, actor, evidence, library_index, context_id)
    # Evidence qualification is an Enhance+ statement; Enable stays definitional.
    if _depth_ix(depth) >= 1:
        if shown:
            block["operating_source"] = "SOURCED"
        else:
            block["operating_source"] = "NO_OPERATING_SOURCE"
            block["hold"] = True
    if _depth_ix(depth) >= 2:
        block["evidence"] = shown
        block["rejected_evidence"] = [{"reason": r["reason"]} for r in rejected]  # no ids/bodies leaked
        block["open_questions"] = list(n.get("open_questions", []))
        block["definition_source"] = n.get("definition_source")
    return block


def build_scaffold(reg, noun_id, requested_depth, actor, evidence, library_index, context_id, role_max_depth=None):
    els = index_registry(reg)
    if noun_id not in els:
        return {"result": "REFUSED", "reason": "UNKNOWN_NOUN"}
    depth = _effective_depth(actor or {}, requested_depth, role_max_depth)
    if depth is None:
        return {"result": "REFUSED", "reason": "NO_RECOGNISED_ROLE"}
    n = els[noun_id]
    out = {
        "result": "OK", "registry_version": reg["version"], "noun": noun_id,
        "label": n["label"], "status": n.get("status"), "definition": n.get("definition"),
        "depth_requested": requested_depth, "depth_effective": depth,
        "depth_clamped": depth != requested_depth, "context_id": context_id,
        "writes": 0,
    }
    if _depth_ix(depth) >= 1:
        out["roles"] = roles_for(reg, els, "H.CTX") if noun_id == "N.CONTEXT" else []
        out["peers"] = [_peer_block(els, p, depth, actor, evidence, library_index, context_id) for p in PEERS]
    if _depth_ix(depth) >= 2:
        out["kind"] = n.get("kind")
        out["definition_source"] = n.get("definition_source")
        out["open_questions"] = list(n.get("open_questions", []))
    return out
