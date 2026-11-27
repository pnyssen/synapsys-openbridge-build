"""Recovery protocol, journal isolation, write-boundary revalidation and all-or-nothing, on the corrected loader (new API).
Offline fakes only: proves the protocol's logic and failure matrix, NOT Odoo/Postgres behaviour and NOT a real external verifier."""
import json, os, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import kda_router as K, service_ctxss_link_loader as L
from fakes import DB, Env, FV, FakeLock, loader_release, tmp_journal, base_effect, make_release
K.PINNED_VERIFIER_IDS = frozenset({FV.VID})

def fresh(db=None, rid="R1", **mk):
    db = db or DB(); v = FV(); ref = loader_release(db, v, rid=rid, **mk); j = tmp_journal(); lock = FakeLock()
    return db, v, ref, j, lock
def admitted(**kw):
    db, v, ref, j, lock = fresh(**kw); return db, v, ref, j, lock, L.admit(Env(db), v, ref, lock, j, "WO")
def committed_linked(db, ctx=1): return sum(1 for m in L.MAPPING if db._snap["synapsys.service"][m[0]].get("context_id") == ctx)
def working_linked(db, ctx=1): return sum(1 for m in L.MAPPING if db.t["synapsys.service"][m[0]].get("context_id") == ctx)

class FailureMatrix(unittest.TestCase):
    def test_happy_path_order_and_terminal_state(self):
        db, v, ref, j, lock, a = admitted(); o = L.run(Env(db), "apply", admission=a)
        self.assertEqual(o["state"], "FINALIZED"); self.assertEqual(committed_linked(db), 19); self.assertFalse(lock.held)
        self.assertEqual([e["t"] for e in j.entries()][:1] + [e["t"] for e in j.entries()][-3:], ["BEGIN", "PREPARED", "COMMITTED", "FINALIZED"])
        self.assertEqual(v.receipt_state("R1"), ("CONSUMED", j.run_id))
    def test_reserve_refused_at_admit_nothing_held(self):
        db, v, ref, j, lock = fresh(); v.fail_reserve = True
        with self.assertRaises(L.Hold): L.admit(Env(db), v, ref, lock, j, "WO")
        self.assertFalse(lock.held); self.assertEqual(v.receipt_state("R1"), ("AVAILABLE", None)); self.assertEqual(db.writes, []); self.assertEqual(j.state(), "ABORTED")
    def test_reserved_by_other_run_refused(self):
        db, v, ref, j, lock = fresh(); v.reserved["R1"] = "someone-else"
        with self.assertRaises(L.Hold): L.admit(Env(db), v, ref, lock, j, "WO")
        self.assertFalse(lock.held)
    def test_write_failure_rolls_back_releases_reservation_and_lock(self):
        db, v, ref, j, lock, a = admitted(db=DB(fail_on_write=48))
        with self.assertRaises(L.Hold): L.run(Env(db), "apply", admission=a)
        self.assertEqual(working_linked(db), 0); self.assertEqual(committed_linked(db), 0); self.assertFalse(lock.held)
        self.assertEqual(v.receipt_state("R1"), ("AVAILABLE", None)); self.assertEqual(j.state(), "ABORTED")
    def test_db_commit_refused_not_applied_aborts_cleanly_and_receipt_reusable(self):
        db, v, ref, j, lock, a = admitted(db=DB(fail_on_commit=True))
        with self.assertRaises(L.Hold) as c: L.run(Env(db), "apply", admission=a)
        self.assertNotIsInstance(c.exception, L.ReconcilePending)
        self.assertEqual((working_linked(db), committed_linked(db)), (0, 0)); self.assertEqual(v.receipt_state("R1"), ("AVAILABLE", None)); self.assertFalse(lock.held); self.assertEqual(j.state(), "ABORTED")
    def test_db_commit_ambiguous_but_applied_is_detected_and_finalised(self):
        db, v, ref, j, lock, a = admitted(db=DB(commit_ambiguous=True)); o = L.run(Env(db), "apply", admission=a)
        self.assertEqual(o["state"], "FINALIZED"); self.assertEqual(committed_linked(db), 19); self.assertEqual(v.receipt_state("R1")[0], "CONSUMED")
    def test_consume_fails_after_commit_is_recorded_and_reconciles(self):
        db, v, ref, j, lock, a = admitted(); v.fail_consume = True
        with self.assertRaises(L.ReconcilePending) as c: L.run(Env(db), "apply", admission=a)
        self.assertEqual(c.exception.state, "COMMITTED_UNCONSUMED"); self.assertEqual(j.state(), "COMMITTED_UNCONSUMED"); self.assertFalse(lock.held)
        self.assertEqual(committed_linked(db), 19); self.assertEqual(v.receipt_state("R1"), ("RESERVED", j.run_id))     # not reusable by anyone else
        with self.assertRaises(L.Hold): L.admit(Env(db), v, ref, FakeLock(), tmp_journal(), "WO")                        # replay blocked
        self.assertEqual(L.reconcile(Env(db), v, j, FakeLock()), {"state": "FINALIZED", "action": "finalized_receipt"}) if not setattr(v, "fail_consume", False) else None
        self.assertEqual(v.receipt_state("R1"), ("CONSUMED", j.run_id)); self.assertEqual(j.state(), "FINALIZED")
        self.assertEqual(L.reconcile(Env(db), v, j, FakeLock())["state"], "FINALIZED")                                  # idempotent
    def test_reconcile_while_verifier_still_down_stays_pending_and_does_not_lose_state(self):
        db, v, ref, j, lock, a = admitted(); v.fail_consume = True
        with self.assertRaises(L.ReconcilePending): L.run(Env(db), "apply", admission=a)
        lk = FakeLock()
        with self.assertRaises(Exception): L.reconcile(Env(db), v, j, lk)
        self.assertFalse(lk.held); self.assertEqual(j.state(), "COMMITTED_UNCONSUMED"); self.assertEqual(committed_linked(db), 19)
    def test_other_run_cannot_finalise_this_receipt(self):
        db, v, ref, j, lock, a = admitted(); v.fail_consume = True
        with self.assertRaises(L.ReconcilePending): L.run(Env(db), "apply", admission=a)
        v.fail_consume = False
        with self.assertRaises(Exception): v.finalize_consume("R1", "other-run")
    def test_commit_ambiguous_and_consume_down_then_reconcile(self):
        db, v, ref, j, lock, a = admitted(db=DB(commit_ambiguous=True)); v.fail_consume = True
        with self.assertRaises(L.ReconcilePending): L.run(Env(db), "apply", admission=a)
        v.fail_consume = False; self.assertEqual(L.reconcile(Env(db), v, j, FakeLock())["state"], "FINALIZED"); self.assertEqual(committed_linked(db), 19)
    def test_crash_after_prepared_db_committed_reconcile_finalises(self):
        db, v, ref, j, lock, a = admitted(); env = Env(db)
        for e in (1,): pass
        # simulate a crash: journal BEGIN + ROWs + PREPARED, DB committed, process died before COMMITTED/FINALIZED
        for vid, v19, code in L.MAPPING: j.append("ROW", id=vid, prior=False, new=1); db.t["synapsys.service"][vid]["context_id"] = 1
        j.append("PREPARED", written=[m[0] for m in L.MAPPING]); db.cr.commit(); lock.release()
        self.assertEqual(L.reconcile(env, v, j, FakeLock())["action"], "finalized_receipt"); self.assertEqual(v.receipt_state("R1")[0], "CONSUMED")
    def test_crash_after_prepared_db_not_committed_reconcile_aborts_and_releases(self):
        db, v, ref, j, lock, a = admitted(); env = Env(db)
        for vid, v19, code in L.MAPPING: j.append("ROW", id=vid, prior=False, new=1); db.t["synapsys.service"][vid]["context_id"] = 1   # uncommitted
        j.append("PREPARED", written=[m[0] for m in L.MAPPING]); lock.release()
        r = L.reconcile(env, v, j, FakeLock()); self.assertEqual(r["state"], "ABORTED"); self.assertEqual(committed_linked(db), 0); self.assertEqual(working_linked(db), 0)
        self.assertEqual(v.receipt_state("R1"), ("AVAILABLE", None))
    def test_crash_mixed_state_escalates_and_keeps_reservation(self):
        db, v, ref, j, lock, a = admitted(); env = Env(db)
        for vid, v19, code in L.MAPPING: j.append("ROW", id=vid, prior=False, new=1)
        for vid in (1, 2, 3): db.t["synapsys.service"][vid]["context_id"] = 1
        db.cr.commit(); j.append("PREPARED", written=[]); lock.release()
        with self.assertRaises(L.Hold) as c: L.reconcile(env, v, j, FakeLock())
        self.assertIn("ESCALATE", str(c.exception)); self.assertEqual(j.state(), "ESCALATED_MIXED"); self.assertEqual(v.receipt_state("R1"), ("RESERVED", j.run_id))
    def test_crash_before_any_write_reconcile_releases(self):
        db, v, ref, j, lock, a = admitted(); lock.release()
        self.assertEqual(L.reconcile(Env(db), v, j, FakeLock())["state"], "ABORTED"); self.assertEqual(v.receipt_state("R1"), ("AVAILABLE", None))
    def test_release_failure_is_reported_not_hidden(self):
        db, v, ref, j, lock, a = admitted(db=DB(fail_on_write=48)); v.fail_release = True
        with self.assertRaises(L.ReconcilePending) as c: L.run(Env(db), "apply", admission=a)
        self.assertEqual(c.exception.state, "ABORTED_WITH_RECOVERY_ERRORS"); self.assertFalse(lock.held); self.assertEqual(committed_linked(db), 0)
        v.fail_release = False; self.assertEqual(L.reconcile(Env(db), v, j, FakeLock())["action"], "released_reservation"); self.assertEqual(v.receipt_state("R1"), ("AVAILABLE", None))
    def test_noop_run_releases_reservation_does_not_consume(self):
        db, v, ref, j, lock, a = admitted(db=DB(drift={m[0]: {"context_id": 1} for m in L.MAPPING})); o = L.run(Env(db), "apply", admission=a)
        self.assertEqual((o["state"], o["written"]), ("NOOP", [])); self.assertEqual(v.receipt_state("R1"), ("AVAILABLE", None)); self.assertFalse(lock.held)
    def test_no_transaction_control_refuses(self):
        class NoCr:
            def __init__(s, e): s.e = e
            def __getitem__(s, m): return s.e[m]
        db, v, ref, j, lock = fresh()
        with self.assertRaises(L.Hold): L.admit(NoCr(Env(db)), v, ref, lock, j, "WO")

class MoreFailureMatrix(unittest.TestCase):
    def test_commit_violating_atomicity_is_unknown_not_assumed_committed(self):
        db, v, ref, j, lock, a = admitted(db=DB(commit_partial_ids={1, 2, 3}))
        with self.assertRaises(L.ReconcilePending) as c: L.run(Env(db), "apply", admission=a)
        self.assertEqual(c.exception.state, "COMMIT_UNKNOWN"); self.assertEqual(j.state(), "COMMIT_UNKNOWN"); self.assertFalse(lock.held)
        self.assertEqual(v.receipt_state("R1"), ("RESERVED", j.run_id)); self.assertEqual(v.receipt_state("R1")[0], "RESERVED")      # not consumed, not released
        with self.assertRaises(L.Hold) as c2: L.reconcile(Env(db), v, j, FakeLock())
        self.assertIn("ESCALATE", str(c2.exception))

class JournalIsolation(unittest.TestCase):
    def test_create_cannot_clobber_an_existing_journal(self):
        import uuid
        d = tempfile.mkdtemp(); fixed = uuid.UUID(int=7); real = uuid.uuid4; uuid.uuid4 = lambda: fixed
        try:
            L.DurableJournal.create(d)
            with self.assertRaises(FileExistsError): L.DurableJournal.create(d)
        finally: uuid.uuid4 = real
    def test_record_from_another_run_inside_a_valid_chain_is_rejected(self):
        import hashlib
        j = tmp_journal(); j.append("BEGIN", receipt_id="R1"); recs = [json.loads(l) for l in open(j.path)]
        r = recs[0]; r.pop("h"); r["run_id"] = "another-run"; r["h"] = hashlib.sha256(L._canon(r).encode()).hexdigest()
        open(j.path, "w").write(json.dumps(r, sort_keys=True) + "\n"); os.chmod(j.path, 0o600)
        with self.assertRaises(L.Hold): j.entries()
    def test_unique_per_execution_and_protected(self):
        a, b = tmp_journal(), tmp_journal(); self.assertNotEqual(a.path, b.path); self.assertNotEqual(a.run_id, b.run_id)
        self.assertEqual(os.stat(a.path).st_mode & 0o777, 0o600); self.assertTrue(a.ready())
    def test_exclusive_create_refuses_existing_path(self):
        j = tmp_journal(); fd = None
        with self.assertRaises(FileExistsError): os.close(os.open(j.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600))
    def test_symlink_and_foreign_inode_refused(self):
        j = tmp_journal(); d = os.path.dirname(j.path); os.rename(j.path, j.path + ".real"); os.symlink(j.path + ".real", j.path)
        self.assertFalse(j.ready())
        with self.assertRaises(L.Hold): j.append("X")
    def test_permissive_mode_refused(self):
        j = tmp_journal(); os.chmod(j.path, 0o644); self.assertFalse(j.ready())
    def test_nonempty_or_closed_journal_cannot_be_admitted_again(self):
        db, v, ref, j, lock, a = admitted(); L.run(Env(db), "apply", admission=a)
        v2 = FV(); ref2 = loader_release(db, v2, rid="R2")
        with self.assertRaises(L.Hold): L.admit(Env(db), v2, ref2, FakeLock(), j, "WO")           # same journal, new receipt
    def test_chain_tamper_and_truncation_detected(self):
        db, v, ref, j, lock, a = admitted(); L.run(Env(db), "apply", admission=a)
        lines = open(j.path).read().splitlines(); 
        for bad in (lines[:3] + lines[4:], [lines[0].replace('"R1"', '"RX"')] + lines[1:], lines[1:]):
            open(j.path, "w").write("\n".join(bad) + "\n"); os.chmod(j.path, 0o600)
            with self.assertRaises(L.Hold): j.entries()
    def test_rollback_restores_only_this_runs_rows(self):
        db, v, ref, j, lock, a = admitted(db=DB(drift={1: {"context_id": 1}})); o = L.run(Env(db), "apply", admission=a)      # row 1 belongs to an "earlier run"
        self.assertEqual(L.rollback(Env(db), j, 1), 18); self.assertEqual(db.t["synapsys.service"][1]["context_id"], 1)
    def test_rollback_needs_protected_journal(self):
        with self.assertRaises(L.Hold): L.rollback(Env(DB()), [], 1)
        with self.assertRaises(L.Hold): L.rollback(Env(DB()), L.DurableJournal("/x/y"), 1)

class WriteBoundaryRevalidation(unittest.TestCase):
    def test_admission_cannot_be_constructed_directly(self):
        with self.assertRaises(L.Hold): L.Admission(object(), ctx_id=1)
        self.assertFalse(hasattr(L, "_TOKEN"))
    def test_minted_forgery_with_no_authoritative_receipt_cannot_write(self):
        db = DB(); v = FV(); lock = FakeLock(); lock.acquire(); j = tmp_journal(); env = Env(db); ctx = L.resolve_context(env); scope = L.frozen_scope(env, ctx, "WO")
        eff = L._effect(scope, "WO", "anthropic", v.current_pins())
        a = L._mint(ctx_id=ctx.id, prestate=scope["prestate_digest"], verifier=v, release_ref={"receipt_id": "R9", "sha256": "0" * 64}, lock=lock, journal=j, effect=eff, run_id=j.run_id, work_object="WO", rid="R9")
        with self.assertRaises(L.Hold): L.run(env, "apply", admission=a)
        self.assertEqual(db.writes, [])
    def test_forgery_with_someone_elses_valid_receipt_cannot_write(self):
        db, v, ref, j, lock, a = admitted(); other = tmp_journal(); lock2 = FakeLock(); lock2.acquire()
        forged = L._mint(**dict(a.__dict__, journal=other, run_id=other.run_id, lock=lock2))
        with self.assertRaises(L.Hold): L.run(Env(db), "apply", admission=forged)        # receipt is RESERVED by a.run_id, not forged.run_id
        self.assertEqual(db.writes, [])
    def test_verifier_not_pinned_at_boundary(self):
        db, v, ref, j, lock, a = admitted(); saved = K.PINNED_VERIFIER_IDS; K.PINNED_VERIFIER_IDS = frozenset()
        try:
            with self.assertRaises(L.Hold): L.run(Env(db), "apply", admission=a)
        finally: K.PINNED_VERIFIER_IDS = saved
        self.assertEqual(db.writes, [])
    def test_executor_rights_revoked_between_admit_and_write(self):
        db, v, ref, j, lock, a = admitted(); v.exec["R1"]["admitted"] = False
        with self.assertRaises(L.Hold) as c: L.run(Env(db), "apply", admission=a)
        self.assertIn("REVALIDATION_FAILED", str(c.exception)); self.assertEqual(db.writes, []); self.assertEqual(v.receipt_state("R1"), ("AVAILABLE", None))
    def test_release_status_changed_between_admit_and_write(self):
        db, v, ref, j, lock, a = admitted(); v.status = "REVOKED"
        with self.assertRaises(L.Hold): L.run(Env(db), "apply", admission=a)
        self.assertEqual(db.writes, [])
    def test_release_expired_between_admit_and_write(self):
        from datetime import datetime, timezone
        db, v, ref, j, lock, a = admitted(); v.now = datetime(2027, 6, 1, tzinfo=timezone.utc)
        with self.assertRaises(L.Hold): L.run(Env(db), "apply", admission=a)
        self.assertEqual(db.writes, [])
    def test_pins_drift_between_admit_and_write(self):
        db, v, ref, j, lock, a = admitted(); v.pins["commit"] = "moved"
        with self.assertRaises(L.Hold): L.run(Env(db), "apply", admission=a)
        self.assertEqual(db.writes, [])
    def test_rights_revoked_after_rows_written_before_commit_rolls_back(self):
        db, v, ref, j, lock = fresh(); a = L.admit(Env(db), v, ref, lock, j, "WO"); v.exec_calls = 0; v.revoke_exec_at = 2     # pre_write call 1 ok; pre_commit call 2 revoked
        with self.assertRaises(L.Hold) as c: L.run(Env(db), "apply", admission=a)
        self.assertIn("REVALIDATION_FAILED", str(c.exception)); self.assertGreater(len(db.writes), 0)
        self.assertEqual((working_linked(db), committed_linked(db)), (0, 0)); self.assertEqual(v.receipt_state("R1"), ("AVAILABLE", None)); self.assertFalse(lock.held)
    def test_independent_d009_withdrawn_before_write(self):
        db, v, ref, j, lock, a = admitted(); v.d009["R1"] = None
        with self.assertRaises(L.Hold): L.run(Env(db), "apply", admission=a)
        self.assertEqual(db.writes, [])

class BoundaryDetails(unittest.TestCase):
    def test_non_conflicting_prestate_drift_after_admit_blocks(self):
        db, v, ref, j, lock, a = admitted(); db.t["synapsys.service"][100]["context_id"] = 90          # a NON-target row: plan stays clean, digest changes
        with self.assertRaises(L.Hold) as c: L.run(Env(db), "apply", admission=a)
        self.assertIn("PRESTATE_DRIFT", str(c.exception)); self.assertEqual(db.writes, [])
    def test_lock_lost_after_rows_written_blocks_commit(self):
        db, v, ref, j, lock, a = admitted(); real = L._typed_readback
        def lose(*x, **k): lock.held = False; return real(*x, **k)
        L._typed_readback = lose
        try:
            with self.assertRaises(L.Hold): L.run(Env(db), "apply", admission=a)
        finally: L._typed_readback = real
        self.assertEqual((working_linked(db), committed_linked(db)), (0, 0))
    def test_reservation_lost_externally_blocks_write(self):
        db, v, ref, j, lock, a = admitted(); v.reserved.pop("R1")
        with self.assertRaises(L.Hold): L.run(Env(db), "apply", admission=a)
        self.assertEqual(db.writes, [])
    def test_swapped_in_valid_but_foreign_journal_blocks_write(self):
        db, v, ref, j, lock, a = admitted(); a.journal = tmp_journal()
        with self.assertRaises(L.Hold): L.run(Env(db), "apply", admission=a)
        self.assertEqual(db.writes, [])

class AllOrNothing(unittest.TestCase):
    def test_each_single_row_conflict_blocks_all(self):
        for vid, _, _ in L.MAPPING:
            db, v, ref, j, lock, a = admitted(db=DB(drift={vid: {"context_id": 90}}))
            with self.assertRaises(L.Hold, msg=vid): L.run(Env(db), "apply", admission=a)
            self.assertEqual(db.writes, [], vid); self.assertEqual(v.receipt_state("R1"), ("AVAILABLE", None))
    def test_two_conflicts_listed(self):
        db, v, ref, j, lock, a = admitted(db=DB(drift={1: {"context_id": 90}, 2: {"code": "ZZ"}}))
        with self.assertRaises(L.Hold) as c: L.run(Env(db), "apply", admission=a)
        self.assertIn("1,2", str(c.exception))
    def test_conflict_appearing_after_admit_is_caught_by_prestate_drift(self):
        db, v, ref, j, lock, a = admitted(); db.t["synapsys.service"][1]["context_id"] = 90
        with self.assertRaises(L.Hold): L.run(Env(db), "apply", admission=a)
        self.assertEqual(db.writes, [])
    def test_dry_run_reports_not_ready_when_conflict(self):
        o = L.run(Env(DB(drift={1: {"context_id": 90}})), "dry"); self.assertFalse(o["all_or_nothing_ready"]); self.assertEqual(o["counts"]["ROW_HOLD_CONFLICT"], 1)
    def test_partially_unchanged_is_not_a_conflict(self):
        db, v, ref, j, lock, a = admitted(db=DB(drift={1: {"context_id": 1}, 2: {"context_id": 1}})); o = L.run(Env(db), "apply", admission=a)
        self.assertEqual((o["counts"]["UNCHANGED"], o["counts"]["UPDATE_CANDIDATE"], o["state"]), (2, 17, "FINALIZED"))
    def test_typed_readback_catches_wrong_value_inside_transaction(self):
        db, v, ref, j, lock, a = admitted(); import fakes; w = fakes.Rec.write
        def bad(self_, vals): return w(self_, {"context_id": 90} if self_.id == 14 else vals)
        fakes.Rec.write = bad
        try:
            with self.assertRaises(L.Hold) as c: L.run(Env(db), "apply", admission=a)
        finally: fakes.Rec.write = w
        self.assertIn("READBACK_CONTEXT_MISMATCH", str(c.exception)); self.assertEqual(committed_linked(db), 0); self.assertEqual(v.receipt_state("R1"), ("AVAILABLE", None))

if __name__ == "__main__": unittest.main()
