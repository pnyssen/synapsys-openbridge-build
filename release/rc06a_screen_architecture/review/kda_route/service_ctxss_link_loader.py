"""Guarded 19-row synapsys.service.context_id loader v3 (source-only candidate; NOT run on any host). Fixes P0-R1..R4 of
NAV_RETURN_DEFECTS_KDA_LOADER_ATOMIC_RECOVERY_AND_ADMISSION (06ca92f8...).

Runs inside `odoo shell` on the destination. Writes ONE field, context_id, on exactly the 19 frozen rows, all-or-nothing.

RECOVERY PROTOCOL (an external receipt and an Odoo commit can NOT be made atomic; this is the explicit protocol instead):
  admit():  decide APPLY_ADMITTED -> fresh unique journal -> RUN_LOCK -> journal BEGIN -> verifier.reserve(receipt, run_id)   [revocable]
  run():    revalidate(pre_write) -> plan (ANY conflict => abort, zero writes) -> per row: journal ROW (write-ahead) then write inside the
            DB transaction -> typed readback inside the transaction -> revalidate(pre_commit) -> journal PREPARED -> cr.commit()
            -> journal COMMITTED -> verifier.finalize_consume(receipt, run_id) [irreversible, only AFTER commit] -> journal FINALIZED
  Failure matrix (journal state / DB / receipt / lock):
    before commit        ABORTED       rolled back   reservation released   lock released   Hold
    commit raised        classify the DB by reading it: not committed -> as above; committed -> continue; unreadable/mixed -> COMMIT_UNKNOWN
    after commit, finalize fails  COMMITTED_UNCONSUMED   committed   reservation KEPT (nobody can replay it)   lock released   ReconcilePending
  reconcile(): re-reads the journal and the DB under RUN_LOCK, then finalizes the receipt (idempotent for the same run_id),
            or aborts + releases when the DB is provably not committed, or escalates to D007 when the state is mixed. It never writes rows.
The journal is unique per execution (O_EXCL, 0600, no symlink, inode-pinned, hash-chained). Authority is revalidated against the
authoritative release and executor rights at the write boundary; a Python object is never the authority.
"""
import hashlib, json, os, uuid
import kda_router as K

CTX_CODE, CTX_V19 = "CTX-SS", 1
MAPPING = [(1, 1, "SC-01"), (2, 2, "SC-02"), (48, 3, "SC-03"), (3, 4, "SC-04"), (4, 5, "SB-01"), (5, 6, "SB-02"),
           (6, 7, "SB-03"), (7, 8, "SB-04"), (8, 9, "SA-01"), (9, 10, "SA-02"), (10, 11, "SC-05"), (11, 12, "SB-05"),
           (12, 13, "SA-03"), (49, 14, "SA-04"), (13, 15, "SA-05"), (14, 16, "SA-06"), (32, 35, "GV-TEC-001"),
           (33, 36, "GV-TEC-002"), (43, 61, "GV-GOV-005")]
WRITE_FIELDS = ("context_id",)
TERMINAL = ("FINALIZED", "ABORTED", "NOOP")


class Hold(Exception):
    pass


class ReconcilePending(Hold):
    """The effect or the receipt is in a recorded, recoverable, NOT-final state. Run reconcile(); do not re-apply."""
    def __init__(self, state, run_id, detail=""):
        super().__init__("%s run=%s %s" % (state, run_id, detail)); self.state, self.run_id, self.detail = state, run_id, detail


def _canon(o):
    return json.dumps(o, sort_keys=True, separators=(",", ":"))


class DurableJournal:
    """Unique, protected, append-only, hash-chained journal for ONE execution. Built only by create()/open_existing()."""
    def __init__(self, path, run_id=None):
        self.path, self.run_id = path, run_id
        self._ident, self._seq, self._prev, self._created = None, 0, "0" * 64, False

    @classmethod
    def create(cls, directory):
        run_id = uuid.uuid4().hex
        path = os.path.join(directory, "kda_journal_%s.jsonl" % run_id)
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
        dfd = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
        st = os.lstat(path)
        j = cls(path, run_id); j._ident, j._created = (st.st_dev, st.st_ino), True
        return j

    @classmethod
    def open_existing(cls, path):
        """Recovery only: re-open a journal, verify its whole chain, adopt its run_id. Appends are allowed (terminal records)."""
        j = cls(path); st = os.lstat(path); j._ident, j._created = (st.st_dev, st.st_ino), True
        recs = j.entries()
        if not recs:
            raise Hold("JOURNAL_EMPTY")
        j.run_id = recs[0]["run_id"]
        return j

    def _check(self):
        try:
            st = os.lstat(self.path)
        except OSError:
            raise Hold("JOURNAL_MISSING")
        import stat
        if not self._created or not stat.S_ISREG(st.st_mode) or (st.st_dev, st.st_ino) != self._ident or st.st_nlink != 1 \
                or (st.st_mode & 0o077) or st.st_uid != os.getuid():
            raise Hold("JOURNAL_NOT_UNIQUE_PROTECTED")

    def ready(self):
        try:
            self._check(); return True
        except (Hold, OSError):
            return False

    def entries(self):
        if not os.path.exists(self.path):
            return []
        out, prev = [], "0" * 64
        with open(self.path) as f:
            for i, line in enumerate(l for l in f if l.strip()):
                r = json.loads(line); h = r.pop("h", None)
                if r.get("prev") != prev or r.get("seq") != i + 1 or hashlib.sha256(_canon(r).encode()).hexdigest() != h or \
                        (self.run_id and r.get("run_id") != self.run_id):
                    raise Hold("JOURNAL_CHAIN_BROKEN_AT_%d" % (i + 1))
                r["h"] = h; out.append(r); prev = h
        return out

    def append(self, t, **body):
        self._check()
        if self._seq == 0 and self._prev == "0" * 64 and os.path.getsize(self.path):   # re-opened: resume the chain
            recs = self.entries(); self._seq, self._prev = len(recs), recs[-1]["h"]
        r = {"run_id": self.run_id, "seq": self._seq + 1, "prev": self._prev, "t": t}; r.update(body)
        h = hashlib.sha256(_canon(r).encode()).hexdigest(); r["h"] = h
        fd = os.open(self.path, os.O_WRONLY | os.O_APPEND | os.O_NOFOLLOW)
        try:
            os.write(fd, (json.dumps(r, sort_keys=True) + "\n").encode()); os.fsync(fd)
        finally:
            os.close(fd)
        self._seq, self._prev = r["seq"], h

    def state(self):
        e = self.entries(); return e[-1]["t"] if e else None

    def rows(self):
        return [e for e in self.entries() if e["t"] == "ROW"]


class Admission:
    """Not constructible from outside admit(). Even a minted/forged one is only a handle: run() revalidates against the verifier."""
    def __init__(self, *a, **k):
        raise Hold("ADMISSION_ONLY_VIA_admit()")


def _mint(**kw):
    a = object.__new__(Admission); a.__dict__.update(kw); return a


def _need_cr(env):
    cr = getattr(env, "cr", None)
    if cr is None or not callable(getattr(cr, "commit", None)) or not callable(getattr(cr, "rollback", None)):
        raise Hold("NO_EXPLICIT_DB_TRANSACTION_CONTROL")
    return cr


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


def _effect(scope, work_object, builder_provider, pins):
    return {"env": "odoo_v20", "model": "synapsys.service", "effect_class": "protected_change", "mutates": True, "offerings_services_chains": True,
            "builder_may_be_decider": True, "builder_provider": builder_provider, "work_object": work_object, "context": CTX_CODE,
            "fields": list(WRITE_FIELDS), "target_ids": scope["target_ids"], "scope": scope, "pins": pins}


def admit(env, verifier, release_ref, lock, journal, work_object, builder_provider="anthropic"):
    """Executor-local admission. Any failure raises Hold and leaves no reservation, no lock, no write."""
    _need_cr(env)
    ctx = resolve_context(env)
    scope = frozen_scope(env, ctx, work_object)
    effect = _effect(scope, work_object, builder_provider, verifier.current_pins() if K.trusted(verifier) else None)
    d = K.decide(effect, rel=release_ref, verifier=verifier)
    if d["disposition"] != "APPLY_ADMITTED":
        raise Hold("NOT_ADMITTED:" + ",".join(d.get("blockers") or [d["disposition"]]))
    if not isinstance(journal, DurableJournal) or not journal.ready() or journal.entries():
        raise Hold("JOURNAL_NOT_FRESH_UNIQUE_PROTECTED")
    if not (hasattr(lock, "acquire") and lock.acquire() is True):
        raise Hold("RUN_LOCK_NOT_HELD")
    rid = release_ref["receipt_id"]
    try:
        journal.append("BEGIN", receipt_id=rid, ctx_id=ctx.id, prestate=scope["prestate_digest"], targets=scope["target_ids"],
                       scope_digest=K.scope_digest(scope))
        if verifier.reserve(rid, journal.run_id) is not True:
            raise Hold("RECEIPT_RESERVATION_REFUSED")
    except Exception as e:
        try:
            journal.append("ABORTED", reason="ADMIT_FAILED:%s" % type(e).__name__)
        except Exception:
            pass
        lock.release()
        raise Hold("ADMIT_FAILED:%s" % e)
    return _mint(ctx_id=ctx.id, prestate=scope["prestate_digest"], verifier=verifier, release_ref=release_ref, lock=lock, journal=journal,
                 effect=effect, run_id=journal.run_id, work_object=work_object, rid=rid)


def _revalidate(env, adm, phase):
    """Write-boundary check against the AUTHORITATIVE release and executor rights. The Admission object proves nothing by itself."""
    v = adm.verifier
    if not K.trusted(v):
        raise Hold("NO_TRUSTED_VERIFIER_AT_WRITE_BOUNDARY")
    if getattr(adm.lock, "held", False) is not True:
        raise Hold("RUN_LOCK_NOT_HELD_AT_WRITE_BOUNDARY")
    if not isinstance(adm.journal, DurableJournal) or not adm.journal.ready() or adm.journal.run_id != adm.run_id:
        raise Hold("DURABLE_JOURNAL_NOT_READY_AT_WRITE_BOUNDARY")
    ctx = resolve_context(env)
    if ctx.id != adm.ctx_id:
        raise Hold("CONTEXT_CHANGED_SINCE_ADMISSION")
    if v.receipt_state(adm.rid) != ("RESERVED", adm.run_id):
        raise Hold("RECEIPT_NOT_RESERVED_BY_THIS_RUN")
    d = K.decide(adm.effect, rel=adm.release_ref, verifier=v, run_id=adm.run_id)
    if d["disposition"] != "APPLY_ADMITTED":
        raise Hold("REVALIDATION_FAILED:" + ",".join(d.get("blockers") or [d["disposition"]]))
    if phase == "pre_write" and prestate_digest(env) != adm.prestate:
        raise Hold("PRESTATE_DRIFT_SINCE_ADMISSION")
    return ctx


def snapshot_others(env):
    ids = {m[0] for m in MAPPING}
    return {r.id: (_ref(r, "context_id"), _ref(r, "method_id")) for r in env["synapsys.service"].search([]) if r.id not in ids}


def _typed_readback(env, ctx_id, total_before, others_before):
    svc = env["synapsys.service"].search([]); ids = {m[0] for m in MAPPING}
    if len(svc) != total_before:
        raise Hold("ROW_COUNT_CHANGED")
    for r in svc:
        if r.id in ids and (type(_ref(r, "context_id")) is not int or _ref(r, "context_id") != ctx_id):
            raise Hold("READBACK_CONTEXT_MISMATCH:%s" % r.id)
        if r.id in ids and _ref(r, "method_id"):
            raise Hold("METHOD_FIELD_TOUCHED:%s" % r.id)
    if snapshot_others(env) != others_before:
        raise Hold("OTHER_30_CHANGED")


def _classify(env, rows):
    """Read the DB and compare to the journalled ROW entries: COMMITTED | NOT_COMMITTED | MIXED."""
    if not rows:
        return "NOT_COMMITTED"
    n_new = n_old = 0
    for e in rows:
        cur = _ref(env["synapsys.service"].browse(e["id"]), "context_id")
        if cur == e["new"]:
            n_new += 1
        elif cur == (e["prior"] or False):
            n_old += 1
    return "COMMITTED" if n_new == len(rows) else "NOT_COMMITTED" if n_old == len(rows) else "MIXED"


def _abort(env, adm, reason):
    errs = []
    try:
        env.cr.rollback()
    except Exception as e:
        errs.append("db_rollback:%s" % type(e).__name__)
    try:
        adm.journal.append("ABORTED", reason=reason)
    except Exception as e:
        errs.append("journal:%s" % type(e).__name__)
    try:
        adm.verifier.release_reservation(adm.rid, adm.run_id)
    except Exception as e:
        errs.append("release_reservation:%s" % type(e).__name__)
    return errs


def _finalize(adm, extra=None):
    try:
        adm.verifier.finalize_consume(adm.rid, adm.run_id)
    except Exception as e:
        try:
            adm.journal.append("COMMITTED_UNCONSUMED", error=type(e).__name__)
        except Exception:
            pass
        raise ReconcilePending("COMMITTED_UNCONSUMED", adm.run_id, "receipt reservation kept; run reconcile()")
    adm.journal.append("FINALIZED")


def run(env, mode="dry", release_id=None, journal=None, admission=None):
    """`release_id` and `journal` are ignored by design: a string is not a release, and a caller path is not a journal."""
    if mode not in ("dry", "apply"):
        raise Hold("BAD_MODE")
    if mode == "dry":
        ctx = resolve_context(env); rows = plan(env, ctx)
        return {"mode": "dry", "context_id": ctx.id, "all_or_nothing_ready": not any(r["state"] == "ROW_HOLD_CONFLICT" for r in rows),
                "counts": {s: sum(1 for r in rows if r["state"] == s) for s in ("UPDATE_CANDIDATE", "UNCHANGED", "ROW_HOLD_CONFLICT")}, "rows": rows}
    if not isinstance(admission, Admission):
        raise Hold("APPLY_REQUIRES_ADMISSION")
    _need_cr(env)
    adm, noop = admission, False
    try:
        try:
            ctx = _revalidate(env, adm, "pre_write")
            rows = plan(env, ctx)
            conflicts = [r for r in rows if r["state"] == "ROW_HOLD_CONFLICT"]
            if conflicts:
                raise Hold("SCOPE_CONFLICT_ALL_OR_NOTHING:%s" % ",".join(str(c["id"]) for c in conflicts))
            todo = [r for r in rows if r["state"] == "UPDATE_CANDIDATE"]
            adm.journal.append("PLAN", todo=[r["id"] for r in todo], unchanged=[r["id"] for r in rows if r["state"] == "UNCHANGED"])
            out = {"mode": "apply", "context_id": ctx.id, "rows": rows,
                   "counts": {s: sum(1 for r in rows if r["state"] == s) for s in ("UPDATE_CANDIDATE", "UNCHANGED", "ROW_HOLD_CONFLICT")}}
            if not todo:
                adm.journal.append("NOOP"); noop = True
                total_before = others_before = written = None
            else:
                total_before, others_before = len(env["synapsys.service"].search([])), snapshot_others(env)
                written = []
            for r in (todo if not noop else []):
                if getattr(adm.lock, "held", False) is not True or not adm.journal.ready():
                    raise Hold("GUARD_LOST_DURING_WRITE")
                adm.journal.append("ROW", id=r["id"], prior=r["prior"] or False, new=ctx.id)   # write-ahead
                env["synapsys.service"].browse(r["id"]).write({"context_id": ctx.id}); written.append(r["id"])
            if not noop:
                _typed_readback(env, ctx.id, total_before, others_before)
                _revalidate(env, adm, "pre_commit")
                adm.journal.append("PREPARED", written=written)
        except Hold as h:
            errs = _abort(env, adm, str(h)[:200])
            if errs:
                raise ReconcilePending("ABORTED_WITH_RECOVERY_ERRORS", adm.run_id, ";".join(errs))
            raise
        except Exception as e:
            errs = _abort(env, adm, "UNEXPECTED:%s" % type(e).__name__)
            raise ReconcilePending("ABORTED_WITH_RECOVERY_ERRORS", adm.run_id, ";".join(errs)) if errs else Hold("APPLY_FAILED_ROLLED_BACK:%s" % e)
        if noop:
            try:
                adm.verifier.release_reservation(adm.rid, adm.run_id)
            except Exception as e:
                raise ReconcilePending("NOOP_RESERVATION_HELD", adm.run_id, type(e).__name__)
            out["written"] = []; out["state"] = "NOOP"; return out
        # ---- commit boundary: from here the DB may be committed even if an exception is raised ----
        row_entries = adm.journal.rows()
        try:
            env.cr.commit()
        except Exception as ce:
            try:
                env.cr.rollback()
            except Exception:
                pass
            try:
                cls = _classify(env, row_entries)
            except Exception:
                cls = "UNKNOWN"
            if cls == "NOT_COMMITTED":
                errs = _abort(env, adm, "COMMIT_FAILED:%s" % type(ce).__name__)
                if errs:
                    raise ReconcilePending("ABORTED_WITH_RECOVERY_ERRORS", adm.run_id, ";".join(errs))
                raise Hold("COMMIT_FAILED_ROLLED_BACK:%s" % ce)
            if cls != "COMMITTED":
                try:
                    adm.journal.append("COMMIT_UNKNOWN", classification=cls)
                except Exception:
                    pass
                raise ReconcilePending("COMMIT_UNKNOWN", adm.run_id, "DB state %s; reservation kept; run reconcile()" % cls)
        try:
            adm.journal.append("COMMITTED")
        except Exception:
            raise ReconcilePending("COMMITTED_JOURNAL_GAP", adm.run_id, "DB committed; reservation kept; run reconcile()")
        _finalize(adm)
        out["written"] = written; out["state"] = "FINALIZED"
        return out
    finally:
        try:
            adm.lock.release()
        except Exception:
            pass


def reconcile(env, verifier, journal, lock):
    """Recovery for a run that did not reach a terminal state. Never writes rows. Needs the pinned verifier and RUN_LOCK."""
    _need_cr(env)
    if not K.trusted(verifier):
        raise Hold("NO_TRUSTED_VERIFIER")
    if not isinstance(journal, DurableJournal) or not journal.ready():
        raise Hold("JOURNAL_NOT_PROTECTED")
    if not (hasattr(lock, "acquire") and lock.acquire() is True):
        raise Hold("RUN_LOCK_NOT_HELD")
    try:
        env.cr.rollback()          # classify COMMITTED data only: discard anything this connection left uncommitted (reconcile never writes rows)
        recs = journal.entries()
        if not recs or recs[0]["t"] != "BEGIN":
            raise Hold("JOURNAL_HAS_NO_BEGIN")
        rid, run_id, st = recs[0]["receipt_id"], journal.run_id, recs[-1]["t"]
        if st in ("FINALIZED", "NOOP", "ABORTED"):
            held = verifier.receipt_state(rid) == ("RESERVED", run_id)
            if held and st != "FINALIZED":
                verifier.release_reservation(rid, run_id)
            return {"state": st, "action": "released_reservation" if held and st != "FINALIZED" else "none"}
        cls = _classify(env, [e for e in recs if e["t"] == "ROW"]) if st not in ("COMMITTED", "COMMITTED_UNCONSUMED") else "COMMITTED"
        if cls == "NOT_COMMITTED":
            journal.append("ABORTED", reason="RECONCILED_NOT_COMMITTED"); verifier.release_reservation(rid, run_id)
            return {"state": "ABORTED", "action": "released_reservation"}
        if cls == "MIXED":
            journal.append("ESCALATED_MIXED")
            raise Hold("MIXED_STATE_ESCALATE_TO_D007")
        if st not in ("COMMITTED", "COMMITTED_UNCONSUMED"):
            journal.append("COMMITTED", via="reconcile")
        verifier.finalize_consume(rid, run_id)      # idempotent for the same run_id; raises for any other holder
        journal.append("FINALIZED", via="reconcile")
        return {"state": "FINALIZED", "action": "finalized_receipt"}
    finally:
        try:
            lock.release()
        except Exception:
            pass


def readback(env, ctx_id):
    ids = {m[0] for m in MAPPING}
    svc = env["synapsys.service"].search([])
    return {"total": len(svc), "linked_19": sum(1 for r in svc if r.id in ids and _ref(r, "context_id") == ctx_id),
            "others_unlinked": sum(1 for r in svc if r.id not in ids and not _ref(r, "context_id")),
            "method_false": sum(1 for r in svc if not _ref(r, "method_id"))}


def rollback(env, journal, ctx_id):
    """Compensating restore of ONLY this execution's journalled rows, only where the row still holds this run's value.
    Unique journal => entries of any other run cannot be present; the run_id filter is a second guard. Caller commits."""
    if not isinstance(journal, DurableJournal) or not journal.ready():
        raise Hold("ROLLBACK_NEEDS_PROTECTED_JOURNAL")
    n = 0
    for j in journal.rows():
        if j["run_id"] != journal.run_id:
            continue
        r = env["synapsys.service"].browse(j["id"])
        if r.exists() and _ref(r, "context_id") == ctx_id:
            r.write({"context_id": j["prior"] or False}); n += 1
    return n
