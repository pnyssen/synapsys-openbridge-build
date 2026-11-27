"""Offline fixtures: fake ORM + fake DESTINATION verifier. Proves the tool's logic, NOT Odoo behaviour."""
import copy, hashlib, json, os, sys, tempfile
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
class Cursor:
    """Odoo-like explicit transaction: writes live in db.t until commit(); rollback() restores the last committed snapshot."""
    def __init__(s, db): s.db = db
    def commit(s):
        d = s.db
        if d.fail_on_commit: raise RuntimeError("commit refused (not applied)")
        if d.commit_partial_ids is not None:
            d._snap = copy.deepcopy(d.t)
            for k, row in d._snap["synapsys.service"].items():
                if k not in d.commit_partial_ids: row["context_id"] = None
            raise RuntimeError("connection lost mid-commit (partial)")
        d._snap = copy.deepcopy(d.t); d.commits += 1
        if d.commit_ambiguous: raise RuntimeError("connection lost after commit (applied)")
    def rollback(s):
        s.db.t = copy.deepcopy(s.db._snap); s.db.rollbacks += 1
class Env:
    def __init__(s, db): s.db = db
    @property
    def cr(s): return s.db.cr
    def __getitem__(s, m): return Model(s.db, m)
class DB:
    def __init__(s, ctx_rows=1, drift=None, fail_on_write=None, fail_on_commit=False, commit_ambiguous=False, commit_partial_ids=None):
        s.writes, s.fail_on_write = [], fail_on_write
        s.fail_on_commit, s.commit_ambiguous, s.commits, s.rollbacks = fail_on_commit, commit_ambiguous, 0, 0
        s.commit_partial_ids = commit_partial_ids   # fault: commit persists only these rows' new values then raises (violated atomicity)
        s.t = {"synapsys.context": {}, "synapsys.service": {}}
        for k in range(ctx_rows): s.t["synapsys.context"][1 + k] = {"code": "CTX-SS", "v19_id": 1}
        s.t["synapsys.context"][90] = {"code": "CTX-BASIN", "v19_id": 9}
        for vid, v19, code in L.MAPPING: s.t["synapsys.service"][vid] = {"code": code, "v19_id": v19, "context_id": None, "method_id": None}
        n = 100
        while len(s.t["synapsys.service"]) < 49:
            s.t["synapsys.service"][n] = {"code": "X%d" % n, "v19_id": n, "context_id": None, "method_id": None}; n += 1
        for k, v in (drift or {}).items(): s.t["synapsys.service"][k].update(v)
        s.cr = Cursor(s); s._snap = copy.deepcopy(s.t)


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
        s.reserved, s.consumed_by = {}, {}
        s.fail_reserve = s.fail_consume = s.fail_release = False
        s.exec_calls, s.revoke_exec_at = 0, None
    def identity(s): return s.VID
    def fetch_receipt(s, rid):
        r = s.receipts.get(rid)
        return {"bytes": r, "issuer": s.issuer, "status": s.status} if r is not None else None
    def scope_bytes(s, ref): return s.scopes.get(ref)
    def now_utc(s): return s.now
    def is_consumed(s, rid): return rid in s.consumed
    def current_pins(s): return dict(s.pins)
    def actor_permission(s, env, model, fields): return s.actor
    def executor_state(s, rid):
        s.exec_calls += 1; st = s.exec.get(rid)
        if st is not None and s.revoke_exec_at and s.exec_calls >= s.revoke_exec_at: st = dict(st, admitted=False)
        return st
    def receipt_state(s, rid):
        if rid in s.consumed: return ("CONSUMED", s.consumed_by.get(rid))
        if rid in s.reserved: return ("RESERVED", s.reserved[rid])
        return ("AVAILABLE", None)
    def reserve(s, rid, run):
        if s.fail_reserve: raise RuntimeError("reserve down")
        if rid in s.consumed or (rid in s.reserved and s.reserved[rid] != run): return False
        s.reserved[rid] = run; return True
    def finalize_consume(s, rid, run):
        if s.fail_consume: raise RuntimeError("consume down")
        if rid in s.consumed and s.consumed_by.get(rid) == run: return True        # idempotent for the same run only
        if s.reserved.get(rid) != run: raise RuntimeError("not the holder")
        del s.reserved[rid]; s.consumed.add(rid); s.consumed_by[rid] = run; return True
    def consume(s, rid, run=None):                      # legacy single-step consume (e5160294 loader); honours the same fault flag
        if s.fail_consume: raise RuntimeError("consume down")
        s.consumed.add(rid)
    def release_reservation(s, rid, run):
        if s.fail_release: raise RuntimeError("release down")
        if s.reserved.get(rid) == run: del s.reserved[rid]; return True
        return False
    def d009_challenge(s, rid): return s.d009.get(rid)


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
    if hasattr(L.DurableJournal, "create"): return L.DurableJournal.create(d)       # unique, exclusive, protected
    return L.DurableJournal(os.path.join(d, "journal.jsonl"))                       # e5160294 shape (for old-commit regression runs)

def loader_release(db, v, **kw):
    env = Env(db); ctx = L.resolve_context(env); scope = L.frozen_scope(env, ctx, "WO")
    eff = {"env": "odoo_v20", "model": "synapsys.service", "effect_class": "protected_change", "mutates": True, "work_object": "WO", "context": "CTX-SS",
           "fields": ["context_id"], "target_ids": scope["target_ids"], "scope": scope}
    return make_release(v, eff, **kw)
