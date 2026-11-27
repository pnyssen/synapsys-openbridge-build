"""Offline fixtures: fake ORM + fake DESTINATION verifier. Proves the tool's logic, NOT Odoo behaviour."""
import hashlib, json, os, sys, tempfile
from datetime import datetime, timezone
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import kda_router as K
import service_ctxss_link_loader as L


class Ref:
    def __init__(s, i): s.id = i
    def __bool__(s): return bool(s.id)
class Rec:
    def __init__(s, db, model, i): s._db, s._m, s.id = db, model, i
    def exists(s): return s.id in s._db.t[s._m]
    def __getattr__(s, f):
        row = s._db.t[s._m].get(s.id, {})
        if f in ("context_id", "method_id", "purpose_id"): return Ref(row.get(f)) if row.get(f) else None
        return row.get(f)
    def write(s, v):
        if s._db.fail_on_write == s.id: raise RuntimeError("boom")
        s._db.writes.append((s._m, s.id, dict(v))); s._db.t[s._m][s.id].update(v)
class Model:
    def __init__(s, db, m): s.db, s.m = db, m
    def browse(s, i): return Rec(s.db, s.m, i)
    def search(s, dom):
        return [Rec(s.db, s.m, i) for i, r in s.db.t[s.m].items() if all(r.get(f) == v for f, op, v in dom)]
class Env:
    def __init__(s, db): s.db = db
    def __getitem__(s, m): return Model(s.db, m)
class DB:
    def __init__(s, ctx_rows=1, drift=None, fail_on_write=None):
        s.writes, s.fail_on_write = [], fail_on_write
        s.t = {"synapsys.context": {}, "synapsys.service": {}}
        for k in range(ctx_rows): s.t["synapsys.context"][1 + k] = {"code": "CTX-SS", "v19_id": 1}
        s.t["synapsys.context"][90] = {"code": "CTX-BASIN", "v19_id": 9}
        for vid, v19, code in L.MAPPING: s.t["synapsys.service"][vid] = {"code": code, "v19_id": v19, "context_id": None, "method_id": None}
        n = 100
        while len(s.t["synapsys.service"]) < 49:
            s.t["synapsys.service"][n] = {"code": "X%d" % n, "v19_id": n, "context_id": None, "method_id": None}; n += 1
        for k, v in (drift or {}).items(): s.t["synapsys.service"][k].update(v)


class FakeLock:
    def __init__(s, busy=False): s.busy, s.held = busy, False
    def acquire(s):
        if s.busy: return False
        s.held = True; return True
    def release(s): s.held = False


class FV(K.Verifier):
    """Stands in for a D007 destination-bound verifier. PINNED only inside tests."""
    VID = "fake-dest-verifier"
    def __init__(s):
        s.receipts, s.scopes, s.consumed = {}, {}, set()
        s.now = datetime(2026, 11, 28, 0, 0, tzinfo=timezone.utc)
        s.pins = {"commit": "5b45d09", "state": "d2de2edb"}
        s.actor = {"actor": "exec1", "can_write": True}
        s.exec, s.d009 = {}, {}
        s.issuer, s.status = "D007", "RELEASED"
    def identity(s): return s.VID
    def fetch_receipt(s, rid):
        r = s.receipts.get(rid)
        return {"bytes": r, "issuer": s.issuer, "status": s.status} if r is not None else None
    def scope_bytes(s, ref): return s.scopes.get(ref)
    def now_utc(s): return s.now
    def is_consumed(s, rid): return rid in s.consumed
    def current_pins(s): return dict(s.pins)
    def actor_permission(s, env, model, fields): return s.actor
    def executor_state(s, rid): return s.exec.get(rid)
    def d009_challenge(s, rid): return s.d009.get(rid)
    def consume(s, rid): s.consumed.add(rid)


def sha(b): return hashlib.sha256(b).hexdigest()

def base_effect(**k):
    scope = {"env": "odoo_v20", "model": "synapsys.service", "fields": ["context_id"], "target_ids": [1, 2], "work_object": "WO", "ctx": "CTX-SS"}
    e = {"env": "odoo_v20", "model": "synapsys.service", "effect_class": "protected_change", "mutates": True, "offerings_services_chains": True,
         "builder_may_be_decider": True, "builder_provider": "anthropic", "work_object": "WO", "context": "CTX-SS", "fields": ["context_id"],
         "target_ids": [1, 2], "scope": scope, "pins": {"commit": "5b45d09", "state": "d2de2edb"}}
    e.update(k); return e

def make_release(v, effect, body_over=None, exec_over=None, d009_over="default", rid="R1", scope_override=None):
    sc = scope_override if scope_override is not None else effect["scope"]
    body = {"receipt_id": rid, "seat": "D007", "scope_ref": "S", "scope_digest": K.scope_digest(effect["scope"]), "work_object": effect["work_object"],
            "context": effect["context"], "env": effect["env"], "model": effect["model"], "fields": effect["fields"], "target_ids": effect["target_ids"],
            "actor_id": "exec1", "not_before": "2026-11-27T00:00:00Z", "expires": "2026-12-31T00:00:00Z", "chg": "CHG-1"}
    body.update(body_over or {})
    b = K.canon(body)
    v.receipts[rid] = b; v.scopes["S"] = K.canon(sc)
    v.exec[rid] = {"admitted": True, "route": K.resolve_route(effect["env"], effect["model"])["route"], "actor": "exec1", "current_release_id": rid,
                   "backup_restore_verified": True, "run_lock_held": True, "dry_run_ok": True, "rollback_ready": True}
    v.exec[rid].update(exec_over or {})
    if d009_over == "default":
        cb = b"challenge-pass"; v.d009[rid] = {"provider": "google", "verdict": "PASS", "bytes": cb, "sha256": sha(cb)}
    elif d009_over is not None:
        v.d009[rid] = d009_over
    return {"receipt_id": rid, "sha256": sha(b)}

def tmp_journal():
    d = tempfile.mkdtemp(prefix="kdaj_")
    return L.DurableJournal(os.path.join(d, "journal.jsonl"))

def loader_release(db, v, **kw):
    env = Env(db); ctx = L.resolve_context(env); scope = L.frozen_scope(env, ctx, "WO")
    eff = {"env": "odoo_v20", "model": "synapsys.service", "effect_class": "protected_change", "mutates": True, "work_object": "WO", "context": "CTX-SS",
           "fields": ["context_id"], "target_ids": scope["target_ids"], "scope": scope}
    return make_release(v, eff, **kw)
