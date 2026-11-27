"""Governed source crosswalk for the enterprise KDA Service GV-GOV-004 (read-only, source-only). Fixes P1-5.

Resolves V20 identities by stable code, never by reusing a V19 integer as a V20 FK. Never invents a Context ruling,
a Method record or an engine. Returns a truthful state; it produces no write. The 19-link loader does not touch
GV-GOV-004; binding it is a distinct protected effect that needs its own release.
"""

def method_code(v19_method_name):
    """'D002-CGE — Common Gate Evaluation ...' -> 'D002-CGE' (code is the token before the em dash)."""
    if not isinstance(v19_method_name, str):
        return None
    return v19_method_name.split("—")[0].strip() or None


def crosswalk(v19_row, v20_service, v20_methods, v20_methods_visible_count, context_ruling=None):
    """v19_row: source x_service_catalogue row. v20_service: V20 synapsys.service row. v20_methods: V20 method rows visible to the actor.
    context_ruling: a filed source ruling {'context_code','v19_id','ruling_sha256'} or None."""
    out = {"service": None, "context": None, "method": None, "writes": [], "binding_effect": "NOT_PROPOSED"}
    code = v19_row.get("x_service_code")
    ok = bool(v20_service) and v20_service.get("code") == code and v20_service.get("v19_id") == v19_row.get("id")
    out["service"] = {"state": "IDENTITY_MATCH" if ok else "IDENTITY_MISMATCH", "v20_id": v20_service.get("id") if ok else None,
                      "code": code, "v19_id": v19_row.get("id")}
    # Context: source says unbound; a binding needs an actual ruling, never inference
    src_ctx = v19_row.get("x_context_id")
    if src_ctx:
        out["context"] = {"state": "SOURCE_BOUND", "source": src_ctx}
    elif context_ruling and context_ruling.get("context_code") and len(str(context_ruling.get("ruling_sha256", ""))) == 64:
        out["context"] = {"state": "RULED_BY_FILED_SOURCE_RULING", "ruling": context_ruling}
    else:
        out["context"] = {"state": "UNRULED_HOLD", "why": "source x_context_id is false and no filed ruling; not invented"}
    # Method: resolve by stable code AND source id carried as v19_id, never by integer reuse
    sm = v19_row.get("x_method_id")
    if not sm:
        out["method"] = {"state": "SOURCE_HAS_NO_METHOD"}
    else:
        mcode, mv19 = method_code(sm[1]), sm[0]
        hits = [m for m in v20_methods if m.get("code") == mcode and m.get("v19_id") == mv19]
        if v20_methods_visible_count == 0:
            out["method"] = {"state": "UNOBSERVED_HOLD", "why": "0 V20 Methods visible to this actor: restriction or absence not distinguishable", "wanted": {"code": mcode, "v19_id": mv19}}
        elif len(hits) == 1:
            out["method"] = {"state": "RESOLVED", "v20_id": hits[0]["id"], "code": mcode, "v19_id": mv19}
        elif len(hits) > 1:
            out["method"] = {"state": "CONFLICT_HOLD", "ids": [h["id"] for h in hits]}
        else:
            out["method"] = {"state": "ABSENT_HOLD", "why": "visible Methods contain no code+v19_id match; not created", "wanted": {"code": mcode, "v19_id": mv19}}
    ready = ok and out["context"]["state"] in ("SOURCE_BOUND", "RULED_BY_FILED_SOURCE_RULING") and out["method"]["state"] == "RESOLVED"
    out["binding_effect"] = "SEPARATE_PROTECTED_EFFECT_NEEDS_OWN_RELEASE" if ready else "HOLD"
    return out
