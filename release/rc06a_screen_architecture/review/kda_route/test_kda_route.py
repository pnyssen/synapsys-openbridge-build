"""Original 29-test suite, preserved behaviour, fixtures reworked for the trusted-verifier model (the old fake-'a'*64 receipt was the defect).
Offline: fake ORM + fake destination verifier prove the tool's LOGIC, not Odoo behaviour. The verifier id is pinned for tests only."""
import os, sys, unittest
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import kda_router as K, service_ctxss_link_loader as L
from fakes import DB, Env, FV, FakeLock, base_effect, make_release, tmp_journal, loader_release

K.PINNED_VERIFIER_IDS = frozenset({FV.VID})   # TEST-ONLY pin; production default is empty (nothing admissible until D007 pins a verifier)
MCP = {"write_scope": ["x_ss_*"]}

def eff(**k):
    return base_effect(**k)
def flo(**k):
    e = {"env": "odoo_v20", "model": "synapsys.service", "effect_class": "protected_change", "mutates": True}; e.update(k); return e

def admitted(e=None, connector=MCP, **mk):
    """Genuine path: pinned verifier + authoritative receipt + admitted executor + independent D009."""
    v = FV(); e = e or eff(); ref = make_release(v, e, **mk)
    return K.decide(e, rel=ref, connector=connector, verifier=v), v, ref

class Floors(unittest.TestCase):
    def test_R5_f0_no_bureaucracy(self):
        d = K.decide({"env": "sharepoint", "model": "wm", "effect_class": "read_only", "mutates": False})
        self.assertEqual((d["floor"], d["gpc"], d["disposition"]), ("F0", 3, "PROCEED_F0"))
    def test_floor_ladder(self):
        for ex, f in (({}, "F1"), ({"data_migration": True}, "F2"), ({"rights_change": True}, "F2"), ({"interfaces": 2}, "F3"), ({"platform_cutover": True}, "F4")):
            self.assertEqual(K.floor_for(flo(**ex))[0], f, ex)
    def test_highest_floor_wins_and_f5_never_lowers(self):
        self.assertEqual(K.floor_for(flo(interfaces=3, context_kind="K-12", cross_context=True))[0], "F3")
        self.assertEqual(K.floor_for(flo(context_kind="K-12", cross_context=True))[1], 6)
    def test_F4_seats_all_twelve_not_a_fixed_seven(self):
        self.assertEqual(len(K.decide(eff(platform_cutover=True))["seats"]), 12)
        self.assertNotEqual(len(K.decide(eff())["seats"]), 7)
    def test_19link_case_floor4_seated6(self):
        d = K.decide(eff()); self.assertEqual((d["floor"], d["gpc"], d["seats_required"]), ("F1", 4, 6)); self.assertIn("D004", d["seats"]); self.assertIn("D009", d["seats"])
    def test_seats_cumulative_and_reps_separate(self):
        d = K.decide(eff(client_data=True, regulation_applies=True, transport_changes=True, collaborator_context_k8=True))
        for s in ("D006", "D008", "D009", "D011", "D007"): self.assertIn(s, d["seats"])
        self.assertEqual(set(d["stakeholder_reps"]), {"client representative", "collaborator representative"})
        self.assertTrue(set(d["stakeholder_reps"]).isdisjoint(d["seats"]))

class OriginalFailure(unittest.TestCase):
    def test_R1_R3_restricted_mcp_does_not_narrow_scope_or_block_route(self):
        d = K.decide(eff(), connector=MCP)
        self.assertEqual(d["statuses"]["applicability"], "APPLIES")
        self.assertTrue(d["statuses"]["actor_permission"].startswith("CONNECTOR_CANNOT_WRITE_USE_ROUTE_HOSTINGER"))
        self.assertEqual(d["route"]["route"], "HOSTINGER_ODOO_SHELL_FAST_PATH")
        self.assertFalse(d["needs_steward"]); self.assertNotIn("actor_permission", d["blockers"])
        self.assertTrue(d["applies_to_this_effect_only"])
    def test_R1_distinct_change_types_use_one_router(self):
        for env, model in (("odoo_v20", "synapsys.service"), ("odoo_v20", "x_ss_thing"), ("github", "source"), ("n8n", "workflow"), ("odoo_v19", "x_context")):
            d = K.decide(eff(env=env, model=model, rights_change=(env == "odoo_v19")), connector=MCP)
            self.assertEqual(d["statuses"]["applicability"], "APPLIES"); self.assertIn("route", d)
        self.assertEqual(K.decide(eff(env="odoo_v19", model="x_context", rights_change=True))["floor"], "F2")
    def test_R3_xss_uses_mcp_synapsys_does_not(self):
        self.assertEqual(K.resolve_route("odoo_v20", "x_ss_a")["route"], "V20_MCP_GATED_WRITE")
        self.assertEqual(K.resolve_route("odoo_v20", "synapsys.service")["route"], "HOSTINGER_ODOO_SHELL_FAST_PATH")
    def test_never_repoint_v19_or_second_env(self):
        self.assertEqual(K.resolve_route("odoo_v19", "x_a")["route"], "V19_ROUTE_UNCHANGED")
        self.assertEqual(K.resolve_route("odoo_sh", "x")["route"], "NO_ROUTE_FOUND")
    def test_R2_hold_only_this_effect(self):
        a, v, ref = admitted()
        b = K.decide(eff(model="x_ss_a"), connector=MCP)
        self.assertEqual(a["disposition"], "APPLY_ADMITTED"); self.assertEqual(b["statuses"]["applicability"], "APPLIES")
        other = eff(); other["scope"] = dict(other["scope"], target_ids=[9])
        self.assertEqual(K.decide(other, rel=ref, verifier=v)["disposition"], "HOLD_APPLY_ONLY")
    def test_R4_unverified_route_returns_exact_blocker_no_proceed(self):
        e = eff(); v = FV(); ref = make_release(v, e, exec_over={"admitted": False})
        d = K.decide(e, rel=ref, connector=MCP, verifier=v)
        self.assertEqual(d["statuses"]["executor_admission"], "EXECUTOR_ROUTE_UNVERIFIED"); self.assertEqual(d["disposition"], "HOLD_APPLY_ONLY")
        self.assertEqual(d["blockers"], ["executor_admission"])
    def test_R4_previous_backup_or_release_cannot_be_replayed(self):
        for over in ({"current_release_id": "OTHER"}, {"backup_restore_verified": False}, {"run_lock_held": False}, {"dry_run_ok": False},
                     {"rollback_ready": False}, {"admitted": False}):
            e = eff(); v = FV(); ref = make_release(v, e, exec_over=over)
            self.assertEqual(K.decide(e, rel=ref, verifier=v)["disposition"], "HOLD_APPLY_ONLY", over)
    def test_R6_fail_closed(self):
        e = eff(); cases = {
            "FORGED_SEAT": {"body_over": {"seat": "D006"}}, "WRONG_ISSUER": None, "WORK_OBJECT": {"body_over": {"work_object": "OTHER"}},
            "CONTEXT": {"body_over": {"context": "CTX-BASIN"}}, "STALE": {"body_over": {"expires": "2020-01-01T00:00:00Z"}},
            "SCOPE_DIGEST": {"body_over": {"scope_digest": "0" * 64}}}
        for k, kw in cases.items():
            v = FV()
            if kw is None: ref = make_release(v, e); v.issuer = "D001"
            else: ref = make_release(v, e, **kw)
            self.assertEqual(K.decide(e, rel=ref, verifier=v)["disposition"], "HOLD_APPLY_ONLY", k)
        v = FV(); make_release(v, e)
        self.assertEqual(K.decide(e, rel=None, verifier=v)["disposition"], "HOLD_APPLY_ONLY")
    def test_R6_fabricated_chat_words_are_not_a_seat_return(self):
        v = FV()
        self.assertNotEqual(K.verify_release({"steward_words": "Steward approves KDA 7"}, eff(), v)[0], "VERIFIED")
    def test_R6_same_provider_self_d009_rejected(self):
        e = eff(); v = FV(); ref = make_release(v, e, d009_over={"provider": "anthropic", "verdict": "PASS", "bytes": b"x", "sha256": K.hashlib.sha256(b"x").hexdigest()})
        d = K.decide(e, rel=ref, verifier=v)
        self.assertEqual(d["statuses"]["pre_effect_assurance"], "SAME_PROVIDER_SELF_ASSURANCE_REJECTED"); self.assertEqual(d["disposition"], "HOLD_APPLY_ONLY")
        d2, _, _ = admitted()
        self.assertEqual(d2["statuses"]["pre_effect_assurance"], "VERIFIED")
    def test_R6_one_genuine_effect_proceeds(self):
        d, v, ref = admitted(); self.assertEqual(d["disposition"], "APPLY_ADMITTED")
        self.assertEqual(d["statuses"]["post_effect_verification"], "PENDING_AFTER_EFFECT")   # post-effect stays distinct, not required before the effect
    def test_six_statuses_always_present(self):
        self.assertEqual(set(K.decide(eff())["statuses"]), set(K.STATUSES))

def admit_fresh(db=None, journal=None, rid="R1", **mk):
    db = db or DB(); v = FV(); ref = loader_release(db, v, rid=rid, **mk); j = journal or tmp_journal(); lock = FakeLock()
    return db, v, ref, j, lock, L.admit(Env(db), v, ref, lock, j, "WO")

class Loader(unittest.TestCase):
    def test_mapping_is_19_unique(self):
        self.assertEqual(len(L.MAPPING), 19); self.assertEqual(len({m[0] for m in L.MAPPING}), 19); self.assertEqual(len({m[2] for m in L.MAPPING}), 19)
    def test_dry_run_writes_nothing_and_plans_19(self):
        db = DB(); o = L.run(Env(db), "dry"); self.assertEqual(db.writes, []); self.assertEqual(o["counts"]["UPDATE_CANDIDATE"], 19)
    def test_apply_needs_release_id(self):
        db = DB()
        with self.assertRaises(L.Hold): L.run(Env(db), "apply")
        self.assertEqual(db.writes, [])
    def test_R8_apply_readback_19_and_30_unchanged_method_false(self):
        db, v, ref, j, lock, a = admit_fresh(); o = L.run(Env(db), "apply", admission=a)
        rb = L.readback(Env(db), o["context_id"]); self.assertEqual((rb["linked_19"], rb["others_unlinked"], rb["method_false"], rb["total"]), (19, 30, 49, 49))
        self.assertTrue(all(set(w[2]) == {"context_id"} for w in db.writes)); self.assertEqual(len(db.writes), 19)
        self.assertEqual(len(j.rows()), 19); self.assertIn("R1", v.consumed); self.assertEqual(j.state(), "FINALIZED")
    def test_R8_second_run_unchanged_no_writes(self):
        db, v, ref, j, lock, a = admit_fresh(); L.run(Env(db), "apply", admission=a); db.writes.clear()
        _, _, _, _, _, a2 = admit_fresh(db=db, rid="R2"); o = L.run(Env(db), "apply", admission=a2)
        self.assertEqual((o["counts"]["UNCHANGED"], db.writes), (19, []))
    def test_R8_rollback_restores_prior_only_never_deletes(self):
        db, v, ref, j, lock, a = admit_fresh(); o = L.run(Env(db), "apply", admission=a); n = L.rollback(Env(db), j, o["context_id"])
        self.assertEqual(n, 19); self.assertEqual(len(db.t["synapsys.service"]), 49)
        self.assertEqual(L.readback(Env(db), o["context_id"])["linked_19"], 0)
    def test_rollback_skips_row_changed_since(self):
        db, v, ref, j, lock, a = admit_fresh(); o = L.run(Env(db), "apply", admission=a); db.t["synapsys.service"][1]["context_id"] = 90
        self.assertEqual(L.rollback(Env(db), j, o["context_id"]), 18); self.assertEqual(db.t["synapsys.service"][1]["context_id"], 90)
    # DESIGN CHANGE (defect P0-R4): the 2 old tests below asserted "18 written, 1 held, release consumed". Any conflict now stops the whole 19-row effect.
    def test_wrong_context_row_held_not_overwritten(self):
        db, v, ref, j, lock, a = admit_fresh(db=DB(drift={1: {"context_id": 90}}))
        with self.assertRaises(L.Hold) as c: L.run(Env(db), "apply", admission=a)
        self.assertIn("SCOPE_CONFLICT_ALL_OR_NOTHING", str(c.exception)); self.assertEqual(db.t["synapsys.service"][1]["context_id"], 90)
        self.assertEqual(db.writes, []); self.assertNotIn("R1", v.consumed); self.assertEqual(v.receipt_state("R1"), ("AVAILABLE", None)); self.assertFalse(lock.held)
    def test_stale_identity_held(self):
        db, v, ref, j, lock, a = admit_fresh(db=DB(drift={48: {"code": "SC-99"}}))
        with self.assertRaises(L.Hold) as c: L.run(Env(db), "apply", admission=a)
        self.assertIn("SCOPE_CONFLICT_ALL_OR_NOTHING", str(c.exception)); self.assertEqual(db.writes, []); self.assertNotIn("R1", v.consumed)
    def test_duplicate_or_missing_context_stops_before_write(self):
        for n in (0, 2):
            db = DB(ctx_rows=n); v = FV()
            with self.assertRaises(L.Hold): L.admit(Env(db), v, {"receipt_id": "R1", "sha256": "0" * 64}, FakeLock(), tmp_journal(), "WO")
            with self.assertRaises(L.Hold): L.run(Env(db), "apply")
            self.assertEqual(db.writes, [])
    def test_never_writes_method_or_other_30(self):
        db, v, ref, j, lock, a = admit_fresh(); L.run(Env(db), "apply", admission=a)
        ids = {m[0] for m in L.MAPPING}; self.assertTrue(all(w[1] in ids for w in db.writes)); self.assertEqual(L.WRITE_FIELDS, ("context_id",))
if __name__ == "__main__": unittest.main()
