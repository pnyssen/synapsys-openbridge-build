"""Guarded 19-row synapsys.service.context_id loader v2 (source-only candidate; NOT run on any host). Fixes P0-3.

Runs inside `odoo shell` on the destination. Writes ONE field, context_id, on at most the 19 frozen rows.
Dry run is the default and writes nothing. Apply needs an Admission token that only admit() can mint, and admit()
requires the router's APPLY_ADMITTED from a pinned destination-bound verifier, a held RUN_LOCK, a durable journal,
and a live prestate digest equal to the one frozen in the release scope. An arbitrary release_id string does nothing.
"""
import hashlib, json, os
import kda_router as K

CTX_CODE, CTX_V19 = "CTX-SS", 1
MAPPING = [(1, 1, "SC-01"), (2, 2, "SC-02"), (48, 3, "SC-03"), (3, 4, "SC-04"), (4, 5, "SB-01"), (5, 6, "SB-02"),
           (6, 7, "SB-03"), (7, 8, "SB-04"), (8, 9, "SA-01"), (9, 10, "SA-02"), (10, 11, "SC-05"), (11, 12, "SB-05"),
           (12, 13, "SA-03"), (49, 14, "SA-04"), (13, 15, "SA-05"), (14, 16, "SA-06"), (32, 35, "GV-TEC-001"),
           (33, 36, "GV-TEC-002"), (43, 61, "GV-GOV-005")]
WRITE_FIELDS = ("context_id",)
_TOKEN = object()


class Hold(Exception):
    pass


class DurableJournal:
    """Write-ahead journal on disk. Entry is flushed and fsynced BEFORE the write it describes."""
    def __init__(self, path):
        self.path = path

    def ready(self):
        try:
            d = os.path.dirname(os.path.abspath(self.path)) or "."
            return os.path.isdir(d) and os.access(d, os.W_OK) and not os.path.islink(self.path)
        except Exception:
            return False

    def append(self, entry):
        with open(self.path, "a") as f:
            f.write(json.dumps(entry, sort_keys=True) + "\n"); f.flush(); os.fsync(f.fileno())

    def entries(self):
        if not os.path.exists(self.path):
            return []
        with open(self.path) as f:
            return [json.loads(l) for l in f if l.strip()]


class Admission:
    def __init__(self, token, **kw):
        if token is not _TOKEN:
            raise Hold("ADMISSION_ONLY_VIA_admit()")
        self.__dict__.update(kw)


def _ref(rec, f):
    v = getattr(rec, f, None)
    return (v.id if v else False) if v is not None else False


def resolve_context(env):
    c = env["synapsys.context"].search([("code", "=", CTX_CODE), ("v19_id", "=", CTX_V19)])
    if len(c) != 1:
        raise Hold("CONTEXT_NOT_EXACTLY_ONE:%d" % len(c))
    return c[0]


def prestate_digest(env):
    rows = sorted((r.id, r.code, r.v19_id, _ref(r, "context_id"), _ref(r, "method_id")) for r in env["synapsys.service"].search([]))
    return hashlib.sha256(json.dumps(rows).encode()).hexdigest()


def frozen_scope(env, ctx, work_object):
    return {"env": "odoo_v20", "model": "synapsys.service", "fields": list(WRITE_FIELDS), "target_ids": sorted(m[0] for m in MAPPING),
            "mapping": [list(m) for m in MAPPING], "context_code": CTX_CODE, "context_v19_id": CTX_V19, "context_id": ctx.id,
            "prestate_digest": prestate_digest(env), "work_object": work_object}


def plan(env, ctx):
    rows, svc = [], env["synapsys.service"]
    for vid, v19, code in MAPPING:
        r = svc.browse(vid)
        if not r.exists() or r.code != code or r.v19_id != v19:
            rows.append({"id": vid, "code": code, "state": "ROW_HOLD_CONFLICT", "why": "IDENTITY_MISMATCH"}); continue
        cur = _ref(r, "context_id")
        st = "UPDATE_CANDIDATE" if not cur else "UNCHANGED" if cur == ctx.id else "ROW_HOLD_CONFLICT"
        rows.append({"id": vid, "code": code, "state": st, "prior": cur})
    return rows


def admit(env, verifier, release_ref, lock, journal, work_object, builder_provider="anthropic"):
    """Executor-local admission. Any failure raises Hold with nothing written."""
    ctx = resolve_context(env)
    scope = frozen_scope(env, ctx, work_object)
    effect = {"env": "odoo_v20", "model": "synapsys.service", "effect_class": "protected_change", "mutates": True, "offerings_services_chains": True,
              "builder_may_be_decider": True, "builder_provider": builder_provider, "work_object": work_object, "context": CTX_CODE,
              "fields": list(WRITE_FIELDS), "target_ids": scope["target_ids"], "scope": scope, "pins": verifier.current_pins() if K.trusted(verifier) else None}
    d = K.decide(effect, rel=release_ref, verifier=verifier)
    if d["disposition"] != "APPLY_ADMITTED":
        raise Hold("NOT_ADMITTED:" + ",".join(d.get("blockers") or [d["disposition"]]))
    if not (hasattr(lock, "acquire") and lock.acquire() is True):
        raise Hold("RUN_LOCK_NOT_HELD")
    if not isinstance(journal, DurableJournal) or not journal.ready():
        lock.release(); raise Hold("DURABLE_JOURNAL_NOT_READY")
    return Admission(_TOKEN, ctx_id=ctx.id, prestate=scope["prestate_digest"], verifier=verifier, release_ref=release_ref, lock=lock, journal=journal)


def snapshot_others(env):
    ids = {m[0] for m in MAPPING}
    return {r.id: (_ref(r, "context_id"), _ref(r, "method_id")) for r in env["synapsys.service"].search([]) if r.id not in ids}


def run(env, mode="dry", release_id=None, journal=None, admission=None):
    """`release_id` is ignored by design: a string is not a release."""
    if mode not in ("dry", "apply"):
        raise Hold("BAD_MODE")
    if mode == "apply":
        if not isinstance(admission, Admission):
            raise Hold("APPLY_REQUIRES_ADMISSION_TOKEN")
        if getattr(admission.lock, "held", False) is not True:
            raise Hold("RUN_LOCK_NOT_HELD_AT_WRITE_BOUNDARY")
        if not admission.journal.ready():
            raise Hold("DURABLE_JOURNAL_NOT_READY_AT_WRITE_BOUNDARY")
    ctx = resolve_context(env)
    if mode == "apply" and (ctx.id != admission.ctx_id or prestate_digest(env) != admission.prestate):
        raise Hold("PRESTATE_DRIFT_SINCE_ADMISSION")
    before_others = snapshot_others(env)
    rows = plan(env, ctx)
    out = {"mode": mode, "context_id": ctx.id, "counts": {s: sum(1 for r in rows if r["state"] == s) for s in ("UPDATE_CANDIDATE", "UNCHANGED", "ROW_HOLD_CONFLICT")}, "rows": rows}
    if mode == "dry":
        return out
    j = admission.journal
    written = []
    try:
        for r in rows:
            if r["state"] == "UPDATE_CANDIDATE":
                j.append({"id": r["id"], "prior": r["prior"], "ctx": ctx.id})   # write-ahead
                env["synapsys.service"].browse(r["id"]).write({"context_id": ctx.id})
                written.append(r["id"])
        if snapshot_others(env) != before_others:
            raise Hold("OTHER_30_CHANGED")
        if any(_ref(x, "method_id") for x in env["synapsys.service"].search([]) if x.id in {m[0] for m in MAPPING}):
            raise Hold("METHOD_FIELD_TOUCHED")
    except Exception as e:
        rollback(env, j, ctx.id)
        admission.lock.release()
        raise Hold("APPLY_FAILED_ROLLED_BACK:%s" % e)
    out["written"] = written
    admission.verifier.consume(admission.release_ref["receipt_id"])
    admission.lock.release()
    return out


def readback(env, ctx_id):
    ids = {m[0] for m in MAPPING}
    svc = env["synapsys.service"].search([])
    return {"total": len(svc), "linked_19": sum(1 for r in svc if r.id in ids and _ref(r, "context_id") == ctx_id),
            "others_unlinked": sum(1 for r in svc if r.id not in ids and not _ref(r, "context_id")),
            "method_false": sum(1 for r in svc if not _ref(r, "method_id"))}


def rollback(env, journal, ctx_id):
    """Restore ONLY prior values this run journalled, and only where the row still holds our value. Reads the on-disk journal."""
    entries = journal.entries() if isinstance(journal, DurableJournal) else list(journal)
    n = 0
    for j in entries:
        r = env["synapsys.service"].browse(j["id"])
        if r.exists() and _ref(r, "context_id") == ctx_id:
            r.write({"context_id": j["prior"] or False}); n += 1
    return n
