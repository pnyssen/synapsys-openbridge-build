"""Source-only architecture binder candidate. No Odoo imports, SQL, or writes.
This is NOT a deployed loader; source fixtures and actor rights are simulated.
"""
import hashlib
import json

KINDS = {"K-1": "Enable", "K-3": "Enable", "K-4": "Enable",
         "K-6": "Enhance", "K-8": "Enhance", "K-12": "Enrich"}

class NoWriteRights(Exception):
    pass


def has_duplicate_source_key(source):
    for family in ("contexts", "purposes", "strategies", "assets"):
        rows = source.get(family, [])
        ids = [r.get("id") for r in rows]
        if None in ids or len(ids) != len(set(ids)):
            return True
        codes = [r.get("code") for r in rows if r.get("code")]
        if len(codes) != len(set(codes)):
            return True
    return False


def exactly_one(rows, **match):
    found = [r for r in rows if all(r.get(k) == v for k, v in match.items())]
    return found[0] if len(found) == 1 else None, len(found)


def denied():
    return {"state": "DENIED_REDACTED", "data": None, "relationships": [],
            "reason": "ACCESS_DENIED", "writes": 0}


def held(reason):
    return {"state": "UNSOURCED_HELD", "data": None, "relationships": [],
            "reason": reason, "writes": 0}


def envelope(noun, result):
    # One shared source/rights presentation contract for Context and Service.
    return {"contract": "architecture-master/binder-source-0.2",
            "noun": noun, "display_depth": "Enable", "reality": "SIMULATED_OFFLINE",
            "authority": "NO_EXECUTION_OR_SOURCE_ADOPTION", **result}


def preview(noun, ctx_code, actor, source, target, *, requested_asset=None,
            write=False):
    if write:
        raise NoWriteRights("No apply path or write authority in source-only candidate")
    if ctx_code not in actor.get("allowed_contexts", ()):
        return envelope(noun, denied())
    if has_duplicate_source_key(source):
        return envelope(noun, held("DUPLICATE_SOURCE_PROVENANCE"))
    # Do not stage Services or infer an operational Service from catalogue labels.
    if noun == "N.SERVICE":
        return envelope(noun, held("SERVICE_OPERATION_AND_CAPABILITY_UNBOUND"))
    if noun != "N.CONTEXT":
        return envelope(noun, held("UNSUPPORTED_NOUN"))
    csrc, n = exactly_one(source["contexts"], code=ctx_code)
    if n != 1:
        return envelope(noun, held("MISSING_OR_DUPLICATE_SOURCE_CONTEXT"))
    cid = csrc["id"]
    # Critical: source actor access precedes all target record and edge projection.
    cx, n = exactly_one(target["contexts"], v19_id=cid, code=ctx_code)
    if n != 1:
        return envelope(noun, held("MISSING_OR_DUPLICATE_TARGET_CONTEXT"))
    if cx["id"] not in actor.get("visible", {}).get("context", ()):
        return envelope(noun, denied())
    kind = cx.get("kind")
    if kind not in KINDS or not cx.get("kind_ruling"):
        return envelope(noun, held("K_KIND_NOT_RULED"))
    psrc, n = exactly_one(source["purposes"], id=csrc.get("purpose_id"))
    if n != 1 or not psrc.get("code"):
        return envelope(noun, held("PURPOSE_SOURCE_IDENTITY_UNRESOLVED"))
    # V20 Purpose has no native v19_id or context_id; use unique stable code.
    pv20, n = exactly_one(target["purposes"], code=psrc["code"])
    if n != 1:
        return envelope(noun, held("PURPOSE_TARGET_CODE_AMBIGUOUS_OR_MISSING"))
    if cx.get("purpose_id") != pv20["id"]:
        return envelope(noun, held("CONTEXT_PURPOSE_FK_MISMATCH"))
    if pv20["id"] not in actor.get("visible", {}).get("purpose", ()):
        return envelope(noun, denied())
    edges = [("Context", "Purpose", "purpose_id", "many2one", "SOURCE_BOUND_FIXTURE")]
    for ss in source["strategies"]:
        if ss["context_id"] != cid:
            continue
        sv20, n = exactly_one(target["strategies"], v19_id=ss["id"], code=ss["code"])
        if n != 1:
            return envelope(noun, held("STRATEGY_IDENTITY_MISSING_OR_DUPLICATE"))
        if sv20.get("context_id") != cx["id"] or sv20.get("purpose_id") != pv20["id"]:
            return envelope(noun, held("STRATEGY_CONTEXT_OR_PURPOSE_MISMATCH"))
        if ss.get("purpose_id") != psrc["id"]:
            return envelope(noun, held("STRATEGY_SOURCE_PURPOSE_MISMATCH"))
        if sv20["id"] not in actor.get("visible", {}).get("strategy", ()):
            return envelope(noun, denied())
        edges.append(("Context", "Strategy", "context_id", "many2one", "SOURCE_BOUND_FIXTURE"))
        edges.append(("Strategy", "Purpose", "purpose_id", "many2one", "SOURCE_BOUND_FIXTURE"))
    assets = [x for x in source["assets"] if x["context_id"] == cid]
    if requested_asset is not None and requested_asset not in [a["id"] for a in assets]:
        # No existence or identifier disclosed for foreign assets.
        return envelope(noun, denied())
    for ass in assets:
        av20, n = exactly_one(target["assets"], v19_id=ass["id"])
        if n != 1:
            return envelope(noun, held("ASSET_IDENTITY_MISSING_OR_DUPLICATE"))
        if av20.get("context_id") != cx["id"]:
            return envelope(noun, held("ASSET_CONTEXT_MISMATCH"))
        if av20["id"] not in actor.get("visible", {}).get("asset", ()):
            return envelope(noun, denied())
        edges.append(("Context", "Asset", "context_id", "many2one", "SOURCE_BOUND_FIXTURE"))
    # Never invent Strategy->Asset causal attribution from Context membership.
    mode = target.get("mode_verbs", {}).get(kind, ())
    eligible = [v["id"] for v in mode if not v.get("human_only", False)]
    result = {"state": "SOURCE_BOUND_FIXTURE", "reason": None,
              "data": {"source_context_code": ctx_code,
                       "context_kind": kind, "cut_b": KINDS[kind],
                       "purpose_source_code": psrc["code"],
                       "eligible_verbs": sorted(eligible),
                       "execution_authorised": False,
                       "owner_authority": "UNATTESTED_HELD",
                       "actor_entitlement": "ASSUMED_IN_FIXTURE_NOT_RUNTIME_PROVEN",
                       "source_strategy_count": len([x for x in source["strategies"] if x["context_id"] == cid]),
                       "context_asset_count": len(assets),
                       "strategy_asset_causality": "NOT_PROVEN"},
              "relationships": [dict(zip(("from", "to", "field", "type", "evidence"), e)) for e in edges],
              "writes": 0}
    return envelope(noun, result)


def dry_run(noun, ctx_code, actor, source, target, **kwargs):
    out = preview(noun, ctx_code, actor, source, target, **kwargs)
    # Simulated no-write plan: no CREATE or UPDATE path exists.
    count = len(out["relationships"]) if out["state"] == "SOURCE_BOUND_FIXTURE" else 0
    out["simulation"] = {"CREATE": 0, "UPDATE": 0,
                         "HOLD": 0 if out["state"] == "SOURCE_BOUND_FIXTURE" else 1,
                         "NO_CHANGE": count}
    digest = hashlib.sha256(json.dumps(out, sort_keys=True).encode()).hexdigest()
    out["dry_run_sha256"] = digest
    return out
