"""Guarded, idempotent 19-row synapsys.service.context_id loader (source-only candidate; NOT run on any host).

Runs inside `odoo shell` on the destination (credentials stay there). Writes ONE field, context_id, on
at most the 19 frozen rows. Dry run is the default and writes nothing. Apply needs an explicit release id.
Never touches method_id, canon, pattern, kind, rights, ACL, PPV or the other 30 Services; never deletes a Service.
"""
import json

CTX_CODE, CTX_V19 = "CTX-SS", 1
# (V20 id, V19 id, code) frozen from NAV_SERVICE_CTXSS_19_LINK_PREFLIGHT_20261128_v1.json (sha 9c8abc0b...061a as reported)
MAPPING = [(1, 1, "SC-01"), (2, 2, "SC-02"), (48, 3, "SC-03"), (3, 4, "SC-04"), (4, 5, "SB-01"), (5, 6, "SB-02"),
           (6, 7, "SB-03"), (7, 8, "SB-04"), (8, 9, "SA-01"), (9, 10, "SA-02"), (10, 11, "SC-05"), (11, 12, "SB-05"),
           (12, 13, "SA-03"), (49, 14, "SA-04"), (13, 15, "SA-05"), (14, 16, "SA-06"), (32, 35, "GV-TEC-001"),
           (33, 36, "GV-TEC-002"), (43, 61, "GV-GOV-005")]
WRITE_FIELDS = ("context_id",)


class Hold(Exception):
    pass


def _ref(rec, f):
    v = getattr(rec, f, None)
    return (v.id if v else False) if v is not None else False


def resolve_context(env):
    c = env["synapsys.context"].search([("code", "=", CTX_CODE), ("v19_id", "=", CTX_V19)])
    if len(c) != 1:
        raise Hold("CONTEXT_NOT_EXACTLY_ONE:%d" % len(c))
    return c[0]


def plan(env, ctx):
    rows, svc = [], env["synapsys.service"]
    for vid, v19, code in MAPPING:
        r = svc.browse(vid)
        if not r.exists() or r.code != code or r.v19_id != v19:
            rows.append({"id": vid, "code": code, "state": "ROW_HOLD_CONFLICT", "why": "IDENTITY_MISMATCH"}); continue
        cur = _ref(r, "context_id")
        if cur is False or cur == 0:
            st = "UPDATE_CANDIDATE"
        elif cur == ctx.id:
            st = "UNCHANGED"
        else:
            st = "ROW_HOLD_CONFLICT"
        rows.append({"id": vid, "code": code, "state": st, "prior": cur})
    return rows


def snapshot_others(env):
    ids = {m[0] for m in MAPPING}
    return {r.id: (_ref(r, "context_id"), _ref(r, "method_id")) for r in env["synapsys.service"].search([]) if r.id not in ids}


def run(env, mode="dry", release_id=None, journal=None):
    if mode not in ("dry", "apply"):
        raise Hold("BAD_MODE")
    if mode == "apply" and not release_id:
        raise Hold("APPLY_REQUIRES_RELEASE_ID")
    ctx = resolve_context(env)
    before_others = snapshot_others(env)
    rows = plan(env, ctx)
    out = {"mode": mode, "release_id": release_id, "context_id": ctx.id,
           "counts": {s: sum(1 for r in rows if r["state"] == s) for s in ("UPDATE_CANDIDATE", "UNCHANGED", "ROW_HOLD_CONFLICT")}, "rows": rows}
    if mode == "apply":
        written = []
        for r in rows:
            if r["state"] == "UPDATE_CANDIDATE":
                env["synapsys.service"].browse(r["id"]).write({"context_id": ctx.id})
                written.append({"id": r["id"], "prior": r["prior"]})
        out["written"] = written
        if journal is not None:
            journal.extend(written)
        if snapshot_others(env) != before_others:
            raise Hold("OTHER_30_CHANGED")
    return out


def readback(env, ctx_id):
    ids = {m[0] for m in MAPPING}
    svc = env["synapsys.service"].search([])
    linked = sum(1 for r in svc if r.id in ids and _ref(r, "context_id") == ctx_id)
    other = sum(1 for r in svc if r.id not in ids and not _ref(r, "context_id"))
    method_false = sum(1 for r in svc if not _ref(r, "method_id"))
    return {"total": len(svc), "linked_19": linked, "others_unlinked": other, "method_false": method_false}


def rollback(env, journal, ctx_id):
    """Restore ONLY the prior FK values this run changed, and only where the row still holds our value."""
    n = 0
    for j in journal:
        r = env["synapsys.service"].browse(j["id"])
        if _ref(r, "context_id") == ctx_id:
            r.write({"context_id": j["prior"] or False}); n += 1
    return n


if __name__ == "__main__":
    print(json.dumps({"mapping_rows": len(MAPPING)}))
