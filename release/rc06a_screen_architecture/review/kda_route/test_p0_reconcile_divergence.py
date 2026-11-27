"""Gap 1 regression: reconcile() when the journal says COMMITTED / COMMITTED_UNCONSUMED but the current DB rows have diverged.
Must refuse finalisation and keep the receipt reserved for D007. Fails on e4d9431d (it finalises on journal state alone); passes on the corrected loader.
Offline fakes only: logic proof, not Odoo/Postgres behaviour."""
import os, sys, unittest
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import kda_router as K, service_ctxss_link_loader as L
from fakes import DB, Env, FV, FakeLock, loader_release, tmp_journal
K.PINNED_VERIFIER_IDS = frozenset({FV.VID})

def pending():
    db = DB(); v = FV(); ref = loader_release(db, v); j = tmp_journal(); lock = FakeLock()
    a = L.admit(Env(db), v, ref, lock, j, "WO"); v.fail_consume = True
    try: L.run(Env(db), "apply", admission=a)
    except L.ReconcilePending: pass
    v.fail_consume = False
    assert j.state() == "COMMITTED_UNCONSUMED" and v.receipt_state("R1") == ("RESERVED", j.run_id)
    return db, v, j

def diverge(db, vid, **vals):
    db.t["synapsys.service"][vid].update(vals); db._snap["synapsys.service"][vid].update(vals)   # a committed change after this run

class ReconcileDivergence(unittest.TestCase):
    def refused(self, db, v, j, why):
        lk = FakeLock(); n = len(db.writes)
        with self.assertRaises(L.Hold) as c: L.reconcile(Env(db), v, j, lk)
        self.assertNotIsInstance(c.exception, L.ReconcilePending)
        self.assertIn("DIVERGED", str(c.exception), why)
        self.assertEqual(v.receipt_state("R1"), ("RESERVED", j.run_id), "receipt must stay reserved for D007")
        self.assertEqual(len(db.writes), n, "reconcile must never write rows"); self.assertFalse(lk.held)
        self.assertEqual(j.state(), "ESCALATED_DIVERGED"); self.assertEqual(v.consumed_by.get("R1") if hasattr(v, "consumed_by") else None, None)
    def test_one_committed_row_changed_to_foreign_context(self):
        db, v, j = pending(); diverge(db, 7, context_id=90); self.refused(db, v, j, "foreign ctx")
    def test_one_committed_row_reverted_to_prior(self):
        db, v, j = pending(); diverge(db, 3, context_id=None); self.refused(db, v, j, "reverted")
    def test_all_rows_reverted_journal_says_committed(self):
        db, v, j = pending()
        for vid, _, _ in L.MAPPING: diverge(db, vid, context_id=None)
        self.refused(db, v, j, "all reverted")
    def test_one_row_deleted(self):
        db, v, j = pending(); del db.t["synapsys.service"][5]; del db._snap["synapsys.service"][5]; self.refused(db, v, j, "deleted")
    def test_journal_committed_record_present_crash_before_finalise(self):
        db, v, j = pending(); diverge(db, 12, context_id=90); self.refused(db, v, j, "diverged after COMMITTED record")
    def test_second_reconcile_stays_refused_and_still_does_not_consume(self):
        db, v, j = pending(); diverge(db, 7, context_id=90); self.refused(db, v, j, "first")
        with self.assertRaises(L.Hold): L.reconcile(Env(db), v, j, FakeLock())
        self.assertEqual(v.receipt_state("R1"), ("RESERVED", j.run_id))
    def test_undiverged_still_finalises(self):
        db, v, j = pending(); self.assertEqual(L.reconcile(Env(db), v, j, FakeLock()), {"state": "FINALIZED", "action": "finalized_receipt"})
        self.assertEqual(v.receipt_state("R1"), ("CONSUMED", j.run_id))
    def test_uncommitted_dirty_state_is_not_mistaken_for_commit(self):
        db, v, j = pending(); db.t["synapsys.service"][9]["context_id"] = 90      # dirty, uncommitted on this connection
        self.assertEqual(L.reconcile(Env(db), v, j, FakeLock())["state"], "FINALIZED")   # reconcile rolls back first; committed rows are intact
    def test_restoring_rows_after_escalation_does_not_auto_finalise(self):
        db, v, j = pending(); diverge(db, 7, context_id=90); self.refused(db, v, j, "first")
        diverge(db, 7, context_id=1)                                  # DB now matches the journal again; still D007's call, never automatic
        with self.assertRaises(L.Hold) as c: L.reconcile(Env(db), v, j, FakeLock())
        self.assertIn("D007", str(c.exception)); self.assertEqual(v.receipt_state("R1"), ("RESERVED", j.run_id)); self.assertEqual(j.state(), "ESCALATED_DIVERGED")
    def test_single_journalled_row_deleted_is_not_read_as_not_committed(self):
        db = DB(); v = FV(); ref = loader_release(db, v); j = tmp_journal(); lock = FakeLock(); a = L.admit(Env(db), v, ref, lock, j, "WO"); lock.release()
        j.append("ROW", id=3, prior=False, new=1); j.append("PREPARED", written=[3]); del db.t["synapsys.service"][3]; del db._snap["synapsys.service"][3]
        with self.assertRaises(L.Hold): L.reconcile(Env(db), v, j, FakeLock())
        self.assertEqual(v.receipt_state("R1"), ("RESERVED", j.run_id)); self.assertEqual(j.state(), "ESCALATED_MIXED")
if __name__ == "__main__": unittest.main()
