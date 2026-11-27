"""Original-failure regressions. Written to run against BOTH commit 5b45d09 (must FAIL) and corrected source (must PASS).
Uses only the call shapes that exist in both versions, with fabricated inputs a caller could supply."""
import inspect, os, sys, unittest
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import kda_router as K, service_ctxss_link_loader as L
from fakes import DB, Env

H = "a" * 64
OLD_EFFECT = {"env": "odoo_v20", "model": "synapsys.service", "mutates": True, "protected": True, "offerings_services_chains": True,
              "builder_may_be_decider": True, "work_object": "WO", "context": "CTX-SS", "scope_hash": "S1", "builder_provider": "anthropic"}
FAKE_REL = {"seat": "D007", "receipt_sha256": H, "scope_hash": "S1", "work_object": "WO", "context": "CTX-SS", "expires": "2999-01-01T00:00:00Z"}
SELF_EXEC = {"admitted": True, "current_release_id": H, "backup_restore_evidence": True, "run_lock": True, "dry_run_ok": True, "rollback_ready": True}
GOOGLE = {"provider": "google", "receipt_sha256": H}

class P0Router(unittest.TestCase):
    def test_T1_fabricated_hash_and_seat_metadata_never_admits(self):
        d = K.decide(dict(OLD_EFFECT), rel=dict(FAKE_REL), executor=dict(SELF_EXEC), d009=dict(GOOGLE))
        self.assertNotEqual(d["disposition"], "APPLY_ADMITTED")
    def test_T3_same_provider_d009_must_hold(self):
        d = K.decide(dict(OLD_EFFECT), rel=dict(FAKE_REL), executor=dict(SELF_EXEC), d009={"provider": "anthropic", "receipt_sha256": H})
        self.assertNotEqual(d["disposition"], "APPLY_ADMITTED")
    def test_T3_connector_cannot_write_must_not_apply(self):
        d = K.decide(dict(OLD_EFFECT), rel=dict(FAKE_REL), executor=dict(SELF_EXEC), connector={"write_scope": ["x_ss_*"]}, d009=dict(GOOGLE))
        self.assertNotEqual(d["disposition"], "APPLY_ADMITTED")
    def test_T4_xss_route_cannot_be_admitted_by_default_flag(self):
        e = dict(OLD_EFFECT, model="x_ss_thing")
        d = K.decide(e, rel=dict(FAKE_REL), executor=None, d009=dict(GOOGLE))
        self.assertNotEqual(d["disposition"], "APPLY_ADMITTED")
    def test_T5_sensitive_read_is_not_f0(self):
        d = K.decide({"env": "sharepoint", "model": "wm", "mutates": False, "client_data": True})
        self.assertNotEqual(d.get("floor"), "F0"); self.assertNotEqual(d["disposition"], "PROCEED_F0")
    def test_T5_unclassified_protected_request_holds_not_crashes(self):
        try:
            d = K.decide({"env": "odoo_v20", "model": "synapsys.service", "mutates": True, "protected": False})
        except Exception as e:
            self.fail("crashed instead of declared HOLD: %r" % e)
        self.assertNotEqual(d["disposition"], "PROCEED_F0"); self.assertNotEqual(d["disposition"], "APPLY_ADMITTED")
    def test_T5_no_constant_clock_default(self):
        self.assertIsNone(inspect.signature(K.decide).parameters["now_iso"].default)

class P0Loader(unittest.TestCase):
    def test_T6_arbitrary_release_id_cannot_write(self):
        db = DB()
        with self.assertRaises(L.Hold): L.run(Env(db), "apply", release_id="arbitrary")
        self.assertEqual(db.writes, [])
    def test_T6_release_id_plus_list_journal_cannot_write(self):
        db = DB()
        with self.assertRaises(L.Hold): L.run(Env(db), "apply", release_id="fake", journal=[])
        self.assertEqual(db.writes, [])
    def test_dry_run_still_writes_nothing(self):
        db = DB(); o = L.run(Env(db), "dry"); self.assertEqual(db.writes, []); self.assertEqual(o["counts"]["UPDATE_CANDIDATE"], 19)

if __name__ == "__main__": unittest.main()
