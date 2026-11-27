"""T11-T14 original-failure regressions for the loader. Uses ONLY call shapes present in BOTH e5160294 and the corrected source,
so the same file must FAIL on e5160294 and PASS on corrected code. Fixtures are offline fakes (logic proof, not Odoo behaviour)."""
import json, os, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import kda_router as K, service_ctxss_link_loader as L
from fakes import DB, Env, FV, FakeLock, loader_release, tmp_journal
K.PINNED_VERIFIER_IDS = frozenset({FV.VID})

def fresh(db=None, rid="R1", journal=None):
    db = db or DB(); v = FV(); ref = loader_release(db, v, rid=rid); j = journal or tmp_journal(); lock = FakeLock()
    return db, v, ref, j, lock

def linked(db, ctx=1):
    return sum(1 for m in L.MAPPING if db.t["synapsys.service"][m[0]].get("context_id") == ctx)

class T11ConsumeFailureAfterWrites(unittest.TestCase):
    def test_T11_consume_failure_leaves_no_leaked_lock_and_a_recorded_state(self):
        db, v, ref, j, lock = fresh(); a = L.admit(Env(db), v, ref, lock, j, "WO"); v.fail_consume = True
        with self.assertRaises(Exception): L.run(Env(db), "apply", admission=a)
        self.assertFalse(lock.held, "lock leaked")
        state = j.state() if hasattr(j, "state") else None
        self.assertIn(state, ("COMMITTED_UNCONSUMED", "ABORTED"), "no recorded recovery state: %r" % (state,))
    def test_T11_no_untracked_partial_effect(self):
        db, v, ref, j, lock = fresh(); a = L.admit(Env(db), v, ref, lock, j, "WO"); v.fail_consume = True
        try: L.run(Env(db), "apply", admission=a)
        except Exception: pass
        st = j.state() if hasattr(j, "state") else None
        committed = sum(1 for m in L.MAPPING if db._snap["synapsys.service"][m[0]].get("context_id") == 1)
        self.assertEqual(linked(db), committed, "dirty uncommitted rows left in an open transaction (working=%d committed=%d)" % (linked(db), committed))
        # either nothing is committed, or the commit is recorded as COMMITTED_UNCONSUMED with the receipt still held (not reusable)
        self.assertTrue(committed == 0 or (st == "COMMITTED_UNCONSUMED" and v.receipt_state("R1")[0] in ("RESERVED", "CONSUMED")),
                        "committed=%d state=%r" % (committed, st))

class T12StaleJournalReplay(unittest.TestCase):
    def test_T12_reused_journal_path_never_reverts_an_earlier_completed_run(self):
        d = tempfile.mkdtemp(); p = os.path.join(d, "journal.jsonl")
        with open(p, "w") as f:                                    # an earlier, successful run's entries (ids 1 and 2 were linked to ctx 1)
            for i in (1, 2): f.write(json.dumps({"id": i, "prior": False, "ctx": 1}) + "\n")
        os.chmod(p, 0o600)
        db = DB(drift={1: {"context_id": 1}, 2: {"context_id": 1}}, fail_on_write=48)
        v = FV(); ref = loader_release(db, v); lock = FakeLock(); j = L.DurableJournal(p)
        try:
            a = L.admit(Env(db), v, ref, lock, j, "WO"); L.run(Env(db), "apply", admission=a)
        except Exception: pass
        self.assertEqual(db.t["synapsys.service"][1]["context_id"], 1, "earlier run's row 1 was reverted")
        self.assertEqual(db.t["synapsys.service"][2]["context_id"], 1, "earlier run's row 2 was reverted")

class T13ConstructibleToken(unittest.TestCase):
    def test_T13_constructed_admission_without_authoritative_release_cannot_write(self):
        db = DB(); v = FV(); lock = FakeLock(); lock.acquire(); j = tmp_journal(); env = Env(db); ctx = L.resolve_context(env)
        try:
            tok = getattr(L, "_TOKEN", None)
            if tok is None: raise L.Hold("no module token to forge with")
            a = L.Admission(tok, ctx_id=ctx.id, prestate=L.prestate_digest(env), verifier=v, release_ref={"receipt_id": "R9", "sha256": "0" * 64}, lock=lock, journal=j)
            L.run(env, "apply", admission=a)
        except (L.Hold, TypeError, AttributeError): pass
        self.assertEqual(db.writes, [], "a constructed admission wrote %d rows" % len(db.writes))

class T14ConflictBlocksWholeOperation(unittest.TestCase):
    def conflict(self, drift):
        db, v, ref, j, lock = fresh(DB(drift=drift)); a = L.admit(Env(db), v, ref, lock, j, "WO")
        try: L.run(Env(db), "apply", admission=a)
        except L.Hold: pass
        self.assertEqual(db.writes, [], "partial writes: %s" % [w[1] for w in db.writes]); self.assertNotIn("R1", v.consumed, "full release consumed after a conflict")
        self.assertFalse(lock.held)
    def test_T14_foreign_context_on_one_row(self): self.conflict({1: {"context_id": 90}})
    def test_T14_stale_code_on_one_row(self): self.conflict({48: {"code": "SC-99"}})
    def test_T14_stale_v19_id_on_one_row(self): self.conflict({33: {"v19_id": 999}})

if __name__ == "__main__": unittest.main()
