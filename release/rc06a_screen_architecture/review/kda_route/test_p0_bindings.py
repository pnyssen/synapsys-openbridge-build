"""T2/T3/T4/T5/T6/T7/T8/T10 on the corrected source. Offline fixtures only: logic proof, not Odoo behaviour, not a host run."""
import json, os, sys, unittest
from datetime import datetime, timezone, timedelta
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import kda_router as K, service_ctxss_link_loader as L, gvgov004_crosswalk as C
from fakes import DB, Env, FV, FakeLock, base_effect, make_release, tmp_journal, loader_release, sha
K.PINNED_VERIFIER_IDS = frozenset({FV.VID})

def dec(e=None, connector=None, **mk):
    e = e or base_effect(); v = mk.pop("v", None) or FV(); ref = make_release(v, e, **mk); return K.decide(e, rel=ref, connector=connector, verifier=v), v, ref

class T2Bindings(unittest.TestCase):
    def refused(self, **mk):
        d, v, r = dec(**mk); self.assertEqual(d["disposition"], "HOLD_APPLY_ONLY", mk); return d
    def test_baseline_admits(self): self.assertEqual(dec()[0]["disposition"], "APPLY_ADMITTED")
    def test_wrong_issuer(self):
        v = FV(); v.issuer = "D009"; self.refused(v=v)
    def test_unreleased_status(self):
        v = FV(); v.status = "DRAFT"; self.refused(v=v)
    def test_scope_bytes_differ_from_digest(self):
        self.refused(scope_override={"env": "odoo_v20", "model": "synapsys.service", "fields": ["context_id"], "target_ids": [1, 2, 3], "work_object": "WO", "ctx": "CTX-SS"})
    def test_each_bound_field(self):
        for k, val in (("target_ids", [1]), ("fields", ["method_id"]), ("env", "odoo_v19"), ("model", "x_ss_a"), ("context", "CTX-BASIN"), ("work_object", "OTHER"), ("actor_id", "someone")):
            self.refused(body_over={k: val})
    def test_hash_mismatch(self):
        e = base_effect(); v = FV(); ref = make_release(v, e); ref["sha256"] = "b" * 64
        self.assertEqual(K.decide(e, rel=ref, verifier=v)["disposition"], "HOLD_APPLY_ONLY")
    def test_unknown_receipt(self):
        e = base_effect(); v = FV(); make_release(v, e)
        self.assertEqual(K.decide(e, rel={"receipt_id": "NOPE", "sha256": "a" * 64}, verifier=v)["disposition"], "HOLD_APPLY_ONLY")
    def test_expiry_not_before_and_malformed_dates(self):
        self.refused(body_over={"expires": "2020-01-01T00:00:00Z"}); self.refused(body_over={"not_before": "2999-01-01T00:00:00Z"})
        self.refused(body_over={"expires": "not-a-date"}); self.refused(body_over={"expires": 12345})
    def test_trusted_clock_drives_expiry_not_constant(self):
        e = base_effect(); v = FV(); ref = make_release(v, e, body_over={"expires": "2027-01-01T00:00:00Z"})
        self.assertEqual(K.decide(e, rel=ref, verifier=v)["disposition"], "APPLY_ADMITTED")
        v.now = datetime(2027, 6, 1, tzinfo=timezone.utc)
        self.assertEqual(K.decide(e, rel=ref, verifier=v)["disposition"], "HOLD_APPLY_ONLY")
        v.now = datetime(2027, 6, 1)   # naive clock is untrustworthy
        self.assertEqual(K.decide(e, rel=ref, verifier=v)["disposition"], "HOLD_APPLY_ONLY")
    def test_replay_and_cross_work_object(self):
        e = base_effect(); v = FV(); ref = make_release(v, e); v.consumed.add("R1")
        self.assertEqual(K.decide(e, rel=ref, verifier=v)["disposition"], "HOLD_APPLY_ONLY")
        e2 = base_effect(work_object="OTHER-WO"); e2["scope"] = dict(e2["scope"], work_object="OTHER-WO")
        v2 = FV(); ref2 = make_release(v2, base_effect())
        self.assertEqual(K.decide(e2, rel=ref2, verifier=v2)["disposition"], "HOLD_APPLY_ONLY")
    def test_pins_drift(self):
        e = base_effect(); v = FV(); ref = make_release(v, e); v.pins["commit"] = "moved"
        self.assertEqual(K.decide(e, rel=ref, verifier=v)["disposition"], "HOLD_APPLY_ONLY")
    def test_unpinned_verifier_cannot_admit(self):
        saved = K.PINNED_VERIFIER_IDS; K.PINNED_VERIFIER_IDS = frozenset()
        try: self.assertEqual(dec()[0]["statuses"]["seat_release"], "NO_TRUSTED_VERIFIER"); self.assertEqual(dec()[0]["disposition"], "HOLD_APPLY_ONLY")
        finally: K.PINNED_VERIFIER_IDS = saved
    def test_caller_trusted_boolean_is_ignored(self):
        e = base_effect(trusted=True, verifier_trusted=True); v = FV(); ref = make_release(v, e)
        class Liar(FV):
            def identity(s): return "liar"
        l = Liar(); l.receipts, l.scopes, l.exec, l.d009 = v.receipts, v.scopes, v.exec, v.d009
        self.assertEqual(K.decide(e, rel=ref, verifier=l)["disposition"], "HOLD_APPLY_ONLY")
    def test_verifier_exception_holds(self):
        class Boom(FV):
            def fetch_receipt(s, r): raise RuntimeError("down")
        e = base_effect(); v = Boom(); ref = make_release(v, e)
        self.assertEqual(K.decide(e, rel=ref, verifier=v)["disposition"], "HOLD_APPLY_ONLY")

class T3Gating(unittest.TestCase):
    def test_actor_cannot_write(self):
        v = FV(); v.actor = {"actor": "exec1", "can_write": False}; self.assertEqual(dec(v=v)[0]["disposition"], "HOLD_APPLY_ONLY")
    def test_actor_not_released_actor(self):
        v = FV(); v.actor = {"actor": "intruder", "can_write": True}; self.assertEqual(dec(v=v)[0]["disposition"], "HOLD_APPLY_ONLY")
    def test_rejected_or_missing_independent_challenge(self):
        cb = b"c"
        for ch in ({"provider": "google", "verdict": "REJECT", "bytes": cb, "sha256": sha(cb)}, {"provider": "google", "verdict": "PASS", "bytes": cb, "sha256": "0" * 64}, None):
            d = dec(d009_over=ch)[0]; self.assertEqual(d["disposition"], "HOLD_APPLY_ONLY"); self.assertNotEqual(d["statuses"]["pre_effect_assurance"], "VERIFIED")
    def test_same_provider_and_unknown_builder_hold(self):
        cb = b"c"; self.assertEqual(dec(d009_over={"provider": "anthropic", "verdict": "PASS", "bytes": cb, "sha256": sha(cb)})[0]["disposition"], "HOLD_APPLY_ONLY")
        self.assertEqual(dec(e=base_effect(builder_provider=""))[0]["disposition"], "HOLD_APPLY_ONLY")
    def test_post_effect_not_required_before_apply(self):
        d = dec()[0]; self.assertEqual(d["disposition"], "APPLY_ADMITTED"); self.assertEqual(d["statuses"]["post_effect_verification"], "PENDING_AFTER_EFFECT")
    def test_ok_requires_every_gate(self):
        d = dec()[0]
        for g in K.GATES: self.assertIn(d["statuses"][g], ("VERIFIED", "NOT_REQUIRED"), g)

class T4Routes(unittest.TestCase):
    MCP = {"write_scope": ["x_ss_*"]}
    def xss(self, **k): return base_effect(model="x_ss_thing", **k)
    def test_xss_needs_allowlist(self):
        e = self.xss(); self.assertEqual(dec(e)[0]["disposition"], "HOLD_APPLY_ONLY")                          # no connector declared
        self.assertEqual(dec(e, connector={"write_scope": ["other_*"]})[0]["disposition"], "HOLD_APPLY_ONLY")
    def test_xss_needs_chg(self):
        e = self.xss(); self.assertEqual(dec(e, connector=self.MCP, body_over={"chg": ""})[0]["disposition"], "HOLD_APPLY_ONLY")
    def test_xss_needs_real_actor(self):
        e = self.xss(); v = FV(); v.actor = {"actor": None, "can_write": True}; self.assertEqual(dec(e, connector=self.MCP, v=v)[0]["disposition"], "HOLD_APPLY_ONLY")
    def test_xss_all_conditions_admits(self):
        self.assertEqual(dec(self.xss(), connector=self.MCP)[0]["disposition"], "APPLY_ADMITTED")
    def test_native_synapsys_refuses_jq_keeps_hostinger_candidate_not_admitted(self):
        d = K.decide(base_effect(), connector=self.MCP)
        self.assertEqual(d["route"]["route"], "HOSTINGER_ODOO_SHELL_FAST_PATH"); self.assertEqual(d["disposition"], "HOLD_APPLY_ONLY")
    def test_git_and_sharepoint_not_auto_admitted(self):
        for env in ("github", "sharepoint"):
            d = K.decide(base_effect(env=env, model="m"), connector=self.MCP); self.assertEqual(d["disposition"], "HOLD_APPLY_ONLY", env)
            self.assertTrue(d["route"]["needs_executor_admission"])

class T5Classification(unittest.TestCase):
    def test_sensitive_reads_need_f2_and_seats(self):
        for k in ("reads_sensitive", "exports_data", "personal_or_financial_data", "client_data"):
            d = K.decide({"env": "odoo_v20", "model": "res.partner", "effect_class": "read_only", "mutates": False, k: True})
            self.assertEqual(d["floor"], "F2", k); self.assertEqual(d["disposition"], "HOLD_SENSITIVE_ACCESS_NEEDS_SEATS", k); self.assertIn("D001", d["seats"])
    def test_f0_nonsensitive_read(self):
        self.assertEqual(K.decide({"env": "sharepoint", "model": "wm", "effect_class": "read_only", "mutates": False})["disposition"], "PROCEED_F0")
    def test_missing_contradictory_malformed_all_hold_never_raise(self):
        bad = [None, [], "x", {}, {"env": "e"}, {"env": "e", "model": "m"}, {"env": "e", "model": "m", "effect_class": "protected_change"},
               {"env": "e", "model": "m", "effect_class": "protected_change", "mutates": False},
               {"env": "e", "model": "m", "effect_class": "read_only", "mutates": True},
               {"env": "e", "model": "m", "effect_class": "read_only", "mutates": False, "data_migration": True},
               {"env": "e", "model": "m", "effect_class": "filing", "mutates": False, "client_data": True},
               {"env": "e", "model": "m", "effect_class": "protected_change", "mutates": "yes"},
               {"env": "e", "model": "m", "effect_class": "protected_change", "mutates": True, "interfaces": -1},
               {"env": "e", "model": "m", "effect_class": "protected_change", "mutates": True, "interfaces": True},
               {"env": "e", "model": "m", "effect_class": "protected_change", "mutates": True, "client_data": "no"},
               {"env": "e", "model": "m", "effect_class": "bogus", "mutates": True},
               {"env": "e", "model": "m", "effect_class": "protected_change", "mutates": True, "context_kind": "K-99"},
               {"env": "", "model": "m", "effect_class": "protected_change", "mutates": True},
               {"env": "e", "model": "m", "mutates": True, "protected": False}]
        for b in bad:
            d = K.decide(b); self.assertEqual(d["disposition"], "HOLD_UNCLASSIFIED", b)
    def test_legacy_params_are_not_authority(self):
        e = base_effect(); d = K.decide(e, executor={"admitted": True}, d009={"provider": "google"}, now_iso="2026-11-28T00:00:00Z", rel={"seat": "D007", "receipt_sha256": "a" * 64})
        self.assertEqual(d["disposition"], "HOLD_APPLY_ONLY")

class T6Loader(unittest.TestCase):
    def adm(self, db=None, rid="R1", **mk):
        db = db or DB(); v = FV(); ref = loader_release(db, v, rid=rid, **mk); j = tmp_journal(); lock = FakeLock()
        return db, v, ref, j, lock
    def test_arbitrary_release_with_good_data_refuses(self):
        db = DB()
        for kw in ({"release_id": "arbitrary"}, {"release_id": "a" * 64, "journal": []}, {"release_id": "x", "admission": object()}):
            with self.assertRaises(L.Hold): L.run(Env(db), "apply", **kw)
        self.assertEqual(db.writes, [])
    def test_admission_cannot_be_constructed_directly(self):
        with self.assertRaises(L.Hold): L.Admission(object(), ctx_id=1)
    def test_admit_refusals_write_nothing(self):
        db, v, ref, j, lock = self.adm()
        for name, args in (("no_lock", (Env(db), v, ref, FakeLock(busy=True), j, "WO")), ("bad_journal", (Env(db), v, ref, FakeLock(), L.DurableJournal("/nonexistent_dir/j"), "WO")),
                           ("wrong_wo", (Env(db), v, ref, FakeLock(), j, "OTHER")), ("fake_ref", (Env(db), v, {"receipt_id": "R1", "sha256": "b" * 64}, FakeLock(), j, "WO"))):
            with self.assertRaises(L.Hold, msg=name): L.admit(*args)
        self.assertEqual(db.writes, [])
    def test_unpinned_verifier_cannot_admit(self):
        db, v, ref, j, lock = self.adm(); saved = K.PINNED_VERIFIER_IDS; K.PINNED_VERIFIER_IDS = frozenset()
        try:
            with self.assertRaises(L.Hold): L.admit(Env(db), v, ref, lock, j, "WO")
        finally: K.PINNED_VERIFIER_IDS = saved
    def test_prestate_drift_after_admission_blocks_write(self):
        db, v, ref, j, lock = self.adm(); a = L.admit(Env(db), v, ref, lock, j, "WO"); db.t["synapsys.service"][1]["context_id"] = 90
        with self.assertRaises(L.Hold): L.run(Env(db), "apply", admission=a)
        self.assertEqual(db.writes, [])
    def test_prestate_drift_before_admission_refuses_via_scope_digest(self):
        db, v, ref, j, lock = self.adm(); db.t["synapsys.service"][100]["context_id"] = 90
        with self.assertRaises(L.Hold): L.admit(Env(db), v, ref, lock, j, "WO")
    def test_lock_lost_at_write_boundary(self):
        db, v, ref, j, lock = self.adm(); a = L.admit(Env(db), v, ref, lock, j, "WO"); lock.held = False
        with self.assertRaises(L.Hold): L.run(Env(db), "apply", admission=a)
        self.assertEqual(db.writes, [])
    def test_journal_lost_at_write_boundary(self):
        db, v, ref, j, lock = self.adm(); a = L.admit(Env(db), v, ref, lock, j, "WO"); a.journal = L.DurableJournal("/nonexistent_dir/j")
        with self.assertRaises(L.Hold): L.run(Env(db), "apply", admission=a)
        self.assertEqual(db.writes, [])
    def test_mid_apply_failure_rolls_back_from_durable_journal(self):
        db = DB(fail_on_write=48); _, v, ref, j, lock = self.adm(db=db); a = L.admit(Env(db), v, ref, lock, j, "WO")
        with self.assertRaises(L.Hold): L.run(Env(db), "apply", admission=a)
        self.assertEqual(L.readback(Env(db), 1)["linked_19"], 0); self.assertEqual(lock.held, False); self.assertNotIn("R1", v.consumed)
        self.assertTrue(len(j.entries()) >= 1)
    def test_journal_is_written_before_each_write(self):
        db, v, ref, j, lock = self.adm(); a = L.admit(Env(db), v, ref, lock, j, "WO"); seen = []
        orig = db.t["synapsys.service"]
        import fakes
        w = fakes.Rec.write
        def spy(self_, vals):
            seen.append(len(j.entries())); return w(self_, vals)
        fakes.Rec.write = spy
        try: L.run(Env(db), "apply", admission=a)
        finally: fakes.Rec.write = w
        self.assertEqual(seen, list(range(1, 20)))
    def test_receipt_consumed_once_second_use_refused(self):
        db, v, ref, j, lock = self.adm(); a = L.admit(Env(db), v, ref, lock, j, "WO"); L.run(Env(db), "apply", admission=a)
        with self.assertRaises(L.Hold): L.admit(Env(db), v, ref, FakeLock(), tmp_journal(), "WO")
    def test_dry_run_with_admission_args_still_no_writes(self):
        db = DB(); L.run(Env(db), "dry", release_id="x", journal=[]); self.assertEqual(db.writes, [])
    def test_thirty_unchanged_and_method_untouched(self):
        db, v, ref, j, lock = self.adm(); a = L.admit(Env(db), v, ref, lock, j, "WO"); before = L.snapshot_others(Env(db)); L.run(Env(db), "apply", admission=a)
        self.assertEqual(L.snapshot_others(Env(db)), before); self.assertEqual(L.readback(Env(db), 1)["method_false"], 49)

class T7Crosswalk(unittest.TestCase):
    V19 = {"id": 40, "x_service_code": "GV-GOV-004", "x_context_id": False, "x_method_id": [23, "D002-CGE — Common Gate Evaluation & Fractal Configuration v1.0"]}
    SVC = {"id": 35, "code": "GV-GOV-004", "v19_id": 40}
    RUL = {"context_code": "CTX-SS", "ruling_sha256": "c" * 64}
    def test_live_facts_give_truthful_hold(self):
        o = C.crosswalk(self.V19, self.SVC, [], 0); self.assertEqual(o["context"]["state"], "UNRULED_HOLD"); self.assertEqual(o["method"]["state"], "UNOBSERVED_HOLD")
        self.assertEqual(o["binding_effect"], "HOLD"); self.assertEqual(o["writes"], []); self.assertEqual(o["method"]["wanted"], {"code": "D002-CGE", "v19_id": 23})
    def test_context_never_invented_from_nothing(self):
        for r in (None, {}, {"context_code": "CTX-SS"}, {"context_code": "CTX-SS", "ruling_sha256": "short"}):
            self.assertEqual(C.crosswalk(self.V19, self.SVC, [{"id": 7, "code": "D002-CGE", "v19_id": 23}], 5, r)["context"]["state"], "UNRULED_HOLD")
    def test_method_resolved_by_code_not_integer(self):
        m = [{"id": 23, "code": "OTHER", "v19_id": 99}]
        self.assertEqual(C.crosswalk(self.V19, self.SVC, m, 1, self.RUL)["method"]["state"], "ABSENT_HOLD")     # V19 integer 23 reused as V20 id is not a match
        m = [{"id": 777, "code": "D002-CGE", "v19_id": 23}]; o = C.crosswalk(self.V19, self.SVC, m, 1, self.RUL)
        self.assertEqual((o["method"]["state"], o["method"]["v20_id"]), ("RESOLVED", 777)); self.assertEqual(o["binding_effect"], "SEPARATE_PROTECTED_EFFECT_NEEDS_OWN_RELEASE")
    def test_duplicate_methods_conflict(self):
        m = [{"id": 1, "code": "D002-CGE", "v19_id": 23}, {"id": 2, "code": "D002-CGE", "v19_id": 23}]
        self.assertEqual(C.crosswalk(self.V19, self.SVC, m, 2, self.RUL)["method"]["state"], "CONFLICT_HOLD")
    def test_service_identity_mismatch_holds(self):
        o = C.crosswalk(self.V19, {"id": 35, "code": "GV-GOV-004", "v19_id": 41}, [{"id": 7, "code": "D002-CGE", "v19_id": 23}], 1, self.RUL)
        self.assertEqual(o["service"]["state"], "IDENTITY_MISMATCH"); self.assertEqual(o["binding_effect"], "HOLD")
    def test_loader_does_not_include_gvgov004(self):
        self.assertNotIn("GV-GOV-004", [m[2] for m in L.MAPPING]); self.assertEqual(len(L.MAPPING), 19)

class T8AcrossEnvironments(unittest.TestCase):
    def test_every_environment_routes_and_holds_without_release(self):
        for env, route in (("odoo_v20", "HOSTINGER_ODOO_SHELL_FAST_PATH"), ("odoo_v19", "V19_ROUTE_UNCHANGED"), ("github", "GIT_OWN_RELEASE"), ("n8n", "N8N_VERIFIED_WORKFLOW_ROUTE"),
                           ("sharepoint", "WM_CREATE_ONLY"), ("new_project", "NO_ROUTE_FOUND"), ("other_ai_lane", "NO_ROUTE_FOUND")):
            d = K.decide(base_effect(env=env, model="synapsys.x" if env == "odoo_v20" else "m")); self.assertEqual(d["route"]["route"], route, env)
            self.assertEqual(d["statuses"]["applicability"], "APPLIES", env); self.assertEqual(d["disposition"], "HOLD_APPLY_ONLY", env)
    def test_r7_text_copy_is_not_activation(self):
        v = FV(); self.assertEqual(K.activation_status("codex_t1", {"receipt_id": "A1", "sha256": "0" * 64}, v), "TEXT_ONLY_NOT_ACTIVATED")
        good = K.canon({"lane": "codex_t1", "routing_decision_changed": True, "native_control": True}); v.receipts["A1"] = good
        self.assertEqual(K.activation_status("codex_t1", {"receipt_id": "A1", "sha256": sha(good)}, v), "ACTIVATED")
        self.assertEqual(K.activation_status("gemini", {"receipt_id": "A1", "sha256": sha(good)}, v), "TEXT_ONLY_NOT_ACTIVATED")
        txt = K.canon({"lane": "codex_t1", "routing_decision_changed": False, "native_control": True}); v.receipts["A2"] = txt
        self.assertEqual(K.activation_status("codex_t1", {"receipt_id": "A2", "sha256": sha(txt)}, v), "TEXT_ONLY_NOT_ACTIVATED")
    def test_f4_whole_mesh_all_seats(self):
        self.assertEqual(len(K.decide(base_effect(platform_cutover=True))["seats"]), 12)

if __name__ == "__main__": unittest.main()
