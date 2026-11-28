"""Offline tests for the read-only Context -> Strategy -> Service slice. Fake env only: proves logic and access-honesty, NOT Odoo ACL/record-rule
behaviour and NOT any role on V20 (ROLE_TESTED stays NOT_TESTED until real actors run the prerequisites)."""
import hashlib, importlib.util, json, os, re, sys, unittest
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, ".."))
ADDON = os.path.join(ROOT, "addon", "synapsys")
sys.path.insert(0, ADDON); sys.path.insert(0, HERE)
import arch_graph as G
spec = importlib.util.spec_from_file_location("arch_slice", os.path.join(ADDON, "arch_slice.py")); S = importlib.util.module_from_spec(spec); spec.loader.exec_module(S)
sys.path.insert(0, os.path.join(ROOT, "tools")); import gen_arch_slice_acceptance as GEN

class AccessError(Exception): pass

class Model:
    def __init__(s, rows, fields, restricted=False): s.rows, s._fields, s.restricted = rows, set(fields), restricted
    def search_read(s, dom, fields, limit=None):
        assert dom == [], "slice must read with no caller-supplied domain"
        if s.restricted: raise AccessError("denied")
        out = [dict({"id": i}, **{f: r.get(f) for f in fields}) for i, r in sorted(s.rows.items())]
        return out[:limit] if limit else out
    def sudo(s, *a, **k): raise AssertionError("sudo is forbidden")
    with_user = with_context = sudo
    def write(s, *a, **k): raise AssertionError("write is forbidden")
    create = unlink = write
class Env:
    def __init__(s, models): s.m = models
    def __getitem__(s, k): return s.m[k]
    def sudo(s, *a, **k): raise AssertionError("sudo is forbidden")
    with_user = sudo

def pair(i, name): return [i, name]
FIELDS = {m: set(f) | {"id"} for m, f in S.SLICE_MODELS.items()}
def world(steward=True):
    ctx = {1: dict(code="CTX-SS", name="SS", kind="K-3", kind_ruling="R", purpose_id=pair(10, "p")), 2: dict(code="CTX-BASIN", name="B", kind="K-4", kind_ruling=None, purpose_id=pair(10, "p"))}
    strat = {20: dict(code="S20", name="s", context_id=pair(1, "c"), purpose_id=pair(10, "p"), service_ids=[30, 31, 32]),
             21: dict(code="S21", name="s", context_id=pair(2, "c"), purpose_id=pair(10, "p"), service_ids=[])}
    svc = {30: dict(code="A", name="a", context_id=pair(1, "c"), method_id=False), 31: dict(code="B", name="b", context_id=False, method_id=False),
           32: dict(code="C", name="c", context_id=pair(2, "c"), method_id=False)}
    return {"synapsys.context": ctx, "synapsys.strategy": strat, "synapsys.service": svc, "synapsys.purpose": {10: dict(code="P", name="p")},
            "synapsys.method": {}, "synapsys.asset": {}, "synapsys.work.object": {}, "synapsys.benefit": {}}
def env_for(data, restricted=(), absent=None, hidden=None):
    ms = {}
    for m, rows in data.items():
        rows = {i: r for i, r in rows.items() if i not in (hidden or {}).get(m, ())}
        f = set(FIELDS[m]) - set((absent or {}).get(m, ()))
        ms[m] = Model(rows, f, restricted=m in restricted)
    return Env(ms)
def run(env, context_id=None):
    g, a, n = S.collect(env, AccessError); return S.build_slice(g, a, n, context_id)

class Slice(unittest.TestCase):
    def test_full_actor_sees_context_strategy_service(self):
        o = run(env_for(world())); self.assertEqual((o["read_only"], o["writes"]), (True, 0))
        c = [r for r in o["contexts"] if r["context"]["id"] == 1][0]
        self.assertEqual(c["strategies"]["ids"], [20]); items = {i["id"]: i["link"] for i in c["strategy_services"][0]["services"]["items"]}
        self.assertEqual(items, {30: "LINKED_TO_THIS_CONTEXT", 31: "NO_DIRECT_SERVICE_CONTEXT", 32: "WRONG_CONTEXT"})
    def test_projections_are_distinct_and_audited(self):
        c = [r for r in run(env_for(world()))["contexts"] if r["context"]["id"] == 1][0]
        self.assertEqual(c["audit"], {"ok": True, "findings": []}); self.assertEqual(len({json.dumps([c["projection"][p]["nodes"], c["projection"][p]["edges"]], sort_keys=True) for p in G.PERSPECTIVES}), 3)
    def test_live_readonly_shape_stops_at_context_never_empty(self):
        d = world(); d["synapsys.context"] = {}; o = run(env_for(d))      # live read: 0 contexts visible, 49 services visible
        self.assertEqual((o["stopped_at"], o["reason"], o["contexts"]), ("Context", "NONE_VISIBLE_TO_ACTOR", [])); self.assertNotIn("EMPTY", json.dumps(o).replace("NONE_VISIBLE", ""))
        self.assertNotIn('"id": 30', json.dumps(o))
    def test_restricted_strategy_model_reported_not_exposed(self):
        c = [r for r in run(env_for(world(), restricted={"synapsys.strategy"}))["contexts"] if r["context"]["id"] == 1][0]
        self.assertEqual(c["strategies"], {"state": "RESTRICTED", "ids": []}); self.assertEqual(c["strategy_services"], [])
    def test_restricted_context_model_stops_at_context(self):
        o = run(env_for(world(), restricted={"synapsys.context"})); self.assertEqual((o["stopped_at"], o["reason"]), ("Context", "RESTRICTED"))
    def test_all_models_restricted_no_group_actor(self):
        o = run(env_for(world(), restricted=set(world()))); self.assertEqual((o["context"]["state"], o["contexts"]), ("RESTRICTED", []))
    def test_hidden_service_not_listed_or_counted(self):
        o = run(env_for(world(), hidden={"synapsys.service": {31, 32}})); c = [r for r in o["contexts"] if r["context"]["id"] == 1][0]
        self.assertEqual([i["id"] for i in c["strategy_services"][0]["services"]["items"]], [30]); self.assertNotIn("31", json.dumps(c["strategy_services"]))
    def test_strategy_service_field_absent_is_stated_not_invented(self):
        o = run(env_for(world(), absent={"synapsys.strategy": {"service_ids"}})); c = [r for r in o["contexts"] if r["context"]["id"] == 1][0]
        self.assertEqual(c["strategy_services"][0]["services"], {"state": "FIELD_NOT_PRESENT", "ids": []}); self.assertEqual(o["notes"]["field_absent"], {"synapsys.strategy": ["service_ids"]})
    def test_context_filter_returns_only_that_context(self):
        o = run(env_for(world()), 2); self.assertEqual([r["context"]["id"] for r in o["contexts"]], [2])
    def test_context_filter_for_unseen_context_reveals_nothing(self):
        o = run(env_for(world(), hidden={"synapsys.context": {2}}), 2); self.assertEqual((o["stopped_at"], o["reason"], o["contexts"]), ("Context", "NONE_VISIBLE_TO_ACTOR", []))
    def test_unruled_kind_is_not_presented_as_ruled(self):
        c2 = [r for r in run(env_for(world()))["contexts"] if r["context"]["id"] == 2][0]; self.assertFalse(c2["context"]["kind_ruled"])
    def test_truncation_reported(self):
        d = world(); d["synapsys.service"] = {i: dict(code=str(i), name="x", context_id=False, method_id=False) for i in range(1, 12)}
        g, a, n = S.collect(env_for(d), AccessError, limit=5); self.assertIn("synapsys.service", n["truncated"]); self.assertEqual(len(g["records"]["synapsys.service"]), 5)
    def test_no_write_no_sudo_zero_effect_fake_would_raise(self):
        run(env_for(world()))                                              # any sudo/write/create/unlink on the fake raises AssertionError
    def test_deterministic(self):
        e = env_for(world()); self.assertEqual(json.dumps(run(e), sort_keys=True), json.dumps(run(e), sort_keys=True))
    def test_no_strategy_asset_edge_in_output(self):
        d = world(); d["synapsys.asset"] = {90: dict(name="a", context_id=pair(1, "c"))}
        for r in run(env_for(d))["contexts"]:
            for p in G.PERSPECTIVES:
                for e in r["projection"][p]["edges"]: self.assertNotEqual((e["from"][0], e["to"][0]), ("synapsys.strategy", "synapsys.asset"))

class SourceGuards(unittest.TestCase):
    def rd(self, *p): return open(os.path.join(ROOT, *p), encoding="utf-8").read()
    def test_vendored_resolver_is_byte_identical_to_review_source(self):
        a = open(os.path.join(ADDON, "arch_graph.py"), "rb").read(); b = open(os.path.join(ROOT, "review", "all61", "arch_graph.py"), "rb").read()
        self.assertEqual(hashlib.sha256(a).hexdigest(), hashlib.sha256(b).hexdigest())
    def test_no_write_or_elevation_in_slice_sources(self):
        for f in ("addon/synapsys/arch_slice.py", "addon/synapsys/controllers/arch_slice.py", "addon/synapsys/arch_graph.py"):
            code = re.sub(r'"""[\s\S]*?"""', "", self.rd(f)); code = re.sub(r"#.*", "", code)
            for bad in (".sudo(", "with_user(", ".write(", ".create(", ".unlink(", "execute(", "cr.commit", "env.cr", "requests.", "subprocess"): self.assertNotIn(bad, code, (f, bad))
    def test_controller_is_user_auth_post_only_and_registered(self):
        c = self.rd("addon/synapsys/controllers/arch_slice.py"); self.assertIn("auth='user'", c); self.assertIn("methods=['POST']", c); self.assertNotIn("auth='public'", c)
        self.assertIn("from . import arch_slice", self.rd("addon/synapsys/controllers/__init__.py"))
    def test_no_master_menu_view_acl_or_manifest_change(self):
        for f in ("views/synapsys_menus.xml", "views/synapsys_views.xml", "views/synapsys_screens.xml", "views/synapsys_enable_peers.xml"):
            self.assertNotIn("architecture/slice", self.rd("addon/synapsys/" + f))
        man = self.rd("addon/synapsys/__manifest__.py"); self.assertIn("20.0.2.4.9", man); self.assertNotIn("arch_slice", man)
        self.assertNotIn("arch_slice", self.rd("addon/synapsys/security/ir.access.csv"))
    def test_acceptance_subset_equals_generator_output_from_the_61_matrix(self):
        self.assertEqual(json.load(open(os.path.join(ADDON, "data", "arch_slice_acceptance.json"))), GEN.build())
    def test_acceptance_rows_cover_slice_menus_and_keep_honest_status(self):
        a = {r["menu_id"]: r for r in GEN.build()["rows"]}; self.assertEqual(set(a), {182, 186, 188, 189, 200}); self.assertEqual(a[200]["status"], "RELEASE_BLOCKED")
        self.assertTrue(all(r["status"] != "PASS" for r in a.values()))
    def test_acceptance_view_never_claims_role_tests(self):
        v = S.acceptance_view(); self.assertEqual((v["state"], v["role_tests"]), ("LOADED", "NOT_TESTED"))
    def test_overlay_is_exactly_the_declared_files_and_one_import_line(self):
        import slice_overlay as O
        base = json.load(open(os.path.join(HERE, "golden", "rc06h_tree_manifest.json"), encoding="utf-8"))["files"]
        now = {}
        for root, _d, fs in os.walk(ADDON):
            for f in fs:
                if "__pycache__" in root or f.endswith(".pyc"): continue
                now[os.path.relpath(os.path.join(root, f), ADDON)] = hashlib.sha256(open(os.path.join(root, f), "rb").read()).hexdigest()
        self.assertEqual(set(now) - set(base), O.SLICE_ADDED | O.ROWSCOPE_ADDED)
        stripped = O.strip(now, ADDON)
        self.assertEqual(stripped[O.CTRL_INIT], base[O.CTRL_INIT])           # the only controllers/__init__.py difference is the one import line
    def test_a_stray_extra_file_is_not_discounted_by_the_overlay(self):
        import slice_overlay as O
        out = O.strip({"a.py": "1", "stray.py": "2", "arch_slice.py": "3", "controllers/arch_slice.py": "4"}, ADDON)
        self.assertEqual(set(out) - {O.CTRL_INIT}, {"a.py", "stray.py"})
    def test_matrix_row_count_still_61(self): self.assertEqual(GEN.build()["row_count_source"], 61)
if __name__ == "__main__": unittest.main()
