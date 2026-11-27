import os, sys, unittest, copy
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import kda_router as K, service_ctxss_link_loader as L

# ---------- fake ORM (offline fixture; proves the tool's logic, NOT Odoo behaviour) ----------
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
        s._db.writes.append((s._m, s.id, dict(v))); s._db.t[s._m][s.id].update(v)
class Set(list):
    pass
class Model:
    def __init__(s, db, m): s.db, s.m = db, m
    def browse(s, i): return Rec(s.db, s.m, i)
    def search(s, dom):
        out = Set()
        for i, r in s.db.t[s.m].items():
            if all(r.get(f) == v for f, op, v in dom): out.append(Rec(s.db, s.m, i))
        return out
class Env:
    def __init__(s, db): s.db = db
    def __getitem__(s, m): return Model(s.db, m)
class DB:
    def __init__(s, ctx_rows=1, drift=None):
        s.writes = []
        s.t = {"synapsys.context": {}, "synapsys.service": {}}
        for k in range(ctx_rows): s.t["synapsys.context"][1 + k] = {"code": "CTX-SS", "v19_id": 1}
        s.t["synapsys.context"][90] = {"code": "CTX-BASIN", "v19_id": 9}
        for vid, v19, code in L.MAPPING: s.t["synapsys.service"][vid] = {"code": code, "v19_id": v19, "context_id": None, "method_id": None}
        n = 100
        while len(s.t["synapsys.service"]) < 49:
            s.t["synapsys.service"][n] = {"code": "X%d" % n, "v19_id": n, "context_id": None, "method_id": None}; n += 1
        for k, v in (drift or {}).items(): s.t["synapsys.service"][k].update(v)

H = "a" * 64
def eff(**k):
    e = {"env": "odoo_v20", "model": "synapsys.service", "mutates": True, "protected": True, "offerings_services_chains": True,
         "builder_may_be_decider": True, "work_object": "WO", "context": "CTX-SS", "scope_hash": "S1", "builder_provider": "anthropic"}
    e.update(k); return e
def rel(**k):
    r = {"seat": "D007", "receipt_sha256": H, "scope_hash": "S1", "work_object": "WO", "context": "CTX-SS", "expires": "2027-01-01T00:00:00Z"}
    r.update(k); return r
GOOD_EX = {"admitted": True, "current_release_id": H, "backup_restore_evidence": True, "run_lock": True, "dry_run_ok": True, "rollback_ready": True}
MCP = {"write_scope": ["x_ss_*"]}

class Floors(unittest.TestCase):
    def test_R5_f0_no_bureaucracy(self):
        d = K.decide({"env": "sharepoint", "model": "wm", "mutates": False}); self.assertEqual((d["floor"], d["gpc"], d["disposition"]), ("F0", 3, "PROCEED_F0"))
    def test_floor_ladder(self):
        for ex, f in (({}, "F1"), ({"data_migration": True}, "F2"), ({"rights_change": True}, "F2"), ({"interfaces": 2}, "F3"), ({"platform_cutover": True}, "F4")):
            self.assertEqual(K.floor_for(dict(mutates=True, **ex))[0], f, ex)
    def test_highest_floor_wins_and_f5_never_lowers(self):
        self.assertEqual(K.floor_for(dict(mutates=True, interfaces=3, context_kind="K-12", cross_context=True))[0], "F3")
        self.assertEqual(K.floor_for(dict(mutates=True, context_kind="K-12", cross_context=True))[1], 6)
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
        a = K.decide(eff(), rel=rel(), executor=GOOD_EX, connector=MCP)
        b = K.decide(eff(model="x_ss_a"), connector=MCP)
        self.assertEqual(a["disposition"], "APPLY_ADMITTED"); self.assertEqual(b["statuses"]["applicability"], "APPLIES")
        self.assertEqual(K.decide(eff(scope_hash="OTHER"), rel=rel(), executor=GOOD_EX)["disposition"], "HOLD_APPLY_ONLY")
    def test_R4_unverified_route_returns_exact_blocker_no_proceed(self):
        d = K.decide(eff(), rel=rel(), executor=None, connector=MCP)
        self.assertEqual(d["statuses"]["executor_admission"], "EXECUTOR_ROUTE_UNVERIFIED"); self.assertEqual(d["disposition"], "HOLD_APPLY_ONLY")
        self.assertEqual(d["blockers"], ["executor_admission"])
    def test_R4_previous_backup_or_release_cannot_be_replayed(self):
        old = dict(GOOD_EX, current_release_id="b" * 64)
        self.assertEqual(K.decide(eff(), rel=rel(), executor=old)["disposition"], "HOLD_APPLY_ONLY")
        for missing in ("backup_restore_evidence", "run_lock", "dry_run_ok", "rollback_ready", "admitted"):
            self.assertEqual(K.decide(eff(), rel=rel(), executor=dict(GOOD_EX, **{missing: False}))["disposition"], "HOLD_APPLY_ONLY", missing)
    def test_R6_fail_closed(self):
        cases = {"INACTIVE_SHADOW": rel(kind="kda_shadow"), "FORGED": rel(seat="D006"), "FORGED2": rel(receipt_sha256="x"),
                 "MISMATCH": rel(scope_hash="Z"), "MISMATCH2": rel(work_object="OTHER"), "MISMATCH3": rel(context="CTX-BASIN"), "STALE": rel(expires="2020-01-01T00:00:00Z")}
        for k, r in cases.items():
            d = K.decide(eff(), rel=r, executor=GOOD_EX, now_iso="2026-11-28T00:00:00Z")
            self.assertEqual(d["disposition"], "HOLD_APPLY_ONLY", k)
        self.assertEqual(K.decide(eff(), rel=None, executor=GOOD_EX)["disposition"], "HOLD_APPLY_ONLY")
    def test_R6_fabricated_chat_words_are_not_a_seat_return(self):
        self.assertNotEqual(K.verify_release({"steward_words": "Steward approves KDA 7"}, "S1", "WO", "CTX-SS", "2026-11-28T00:00:00Z"), "VERIFIED")
    def test_R6_same_provider_self_d009_rejected(self):
        d = K.decide(eff(), rel=rel(), executor=GOOD_EX, d009={"provider": "anthropic", "receipt_sha256": H})
        self.assertEqual(d["statuses"]["implementation_assurance"], "SAME_PROVIDER_SELF_ASSURANCE_REJECTED")
        d2 = K.decide(eff(), rel=rel(), executor=GOOD_EX, d009={"provider": "google", "receipt_sha256": H})
        self.assertEqual(d2["statuses"]["implementation_assurance"], "VERIFIED")
    def test_R6_one_genuine_effect_proceeds(self):
        self.assertEqual(K.decide(eff(), rel=rel(), executor=GOOD_EX, connector=MCP)["disposition"], "APPLY_ADMITTED")
    def test_five_statuses_always_present(self):
        self.assertEqual(set(K.decide(eff())["statuses"]), set(K.STATUSES))

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
        db = DB(); j = []; o = L.run(Env(db), "apply", release_id=H, journal=j)
        rb = L.readback(Env(db), o["context_id"]); self.assertEqual((rb["linked_19"], rb["others_unlinked"], rb["method_false"], rb["total"]), (19, 30, 49, 49))
        self.assertTrue(all(set(w[2]) == {"context_id"} for w in db.writes)); self.assertEqual(len(db.writes), 19)
    def test_R8_second_run_unchanged_no_writes(self):
        db = DB(); L.run(Env(db), "apply", release_id=H); db.writes.clear(); o = L.run(Env(db), "apply", release_id=H)
        self.assertEqual((o["counts"]["UNCHANGED"], db.writes), (19, []))
    def test_R8_rollback_restores_prior_only_never_deletes(self):
        db = DB(); j = []; o = L.run(Env(db), "apply", release_id=H, journal=j); n = L.rollback(Env(db), j, o["context_id"])
        self.assertEqual(n, 19); self.assertEqual(len(db.t["synapsys.service"]), 49)
        self.assertEqual(L.readback(Env(db), o["context_id"])["linked_19"], 0)
    def test_rollback_skips_row_changed_since(self):
        db = DB(); j = []; o = L.run(Env(db), "apply", release_id=H, journal=j); db.t["synapsys.service"][1]["context_id"] = 90
        self.assertEqual(L.rollback(Env(db), j, o["context_id"]), 18); self.assertEqual(db.t["synapsys.service"][1]["context_id"], 90)
    def test_wrong_context_row_held_not_overwritten(self):
        db = DB(drift={1: {"context_id": 90}}); o = L.run(Env(db), "apply", release_id=H)
        self.assertEqual(o["counts"]["ROW_HOLD_CONFLICT"], 1); self.assertEqual(db.t["synapsys.service"][1]["context_id"], 90); self.assertEqual(len(db.writes), 18)
    def test_stale_identity_held(self):
        db = DB(drift={48: {"code": "SC-99"}}); o = L.run(Env(db), "apply", release_id=H)
        self.assertEqual(o["counts"]["ROW_HOLD_CONFLICT"], 1); self.assertEqual(len(db.writes), 18)
    def test_duplicate_or_missing_context_stops_before_write(self):
        for n in (0, 2):
            db = DB(ctx_rows=n)
            with self.assertRaises(L.Hold): L.run(Env(db), "apply", release_id=H)
            self.assertEqual(db.writes, [])
    def test_never_writes_method_or_other_30(self):
        db = DB(); L.run(Env(db), "apply", release_id=H)
        ids = {m[0] for m in L.MAPPING}; self.assertTrue(all(w[1] in ids for w in db.writes)); self.assertEqual(L.WRITE_FIELDS, ("context_id",))
if __name__ == "__main__": unittest.main()
