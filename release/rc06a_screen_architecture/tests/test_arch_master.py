"""Offline tests for the Master Architecture builder (arch_master.py). Fake env only: proves logic, rights-first honesty and the FFE / verb /
depth rules; NOT Odoo ACL behaviour and NOT any role on V20 (ROLE_TESTED stays NOT_TESTED)."""
import copy, hashlib, importlib.util, json, os, subprocess, sys, unittest
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, ".."))
ADDON = os.path.join(ROOT, "addon", "synapsys")
sys.path.insert(0, ADDON)
import arch_graph as G
spec = importlib.util.spec_from_file_location("arch_master", os.path.join(ADDON, "arch_master.py")); A = importlib.util.module_from_spec(spec); spec.loader.exec_module(A)
D = A.load_definition()


class AccessError(Exception): pass


class Model:
    def __init__(s, rows, fields, restricted=False): s.rows, s._fields, s.restricted = rows, set(fields), restricted
    def search_read(s, dom, fields, limit=None):
        assert dom == [], "Master must read with no caller-supplied domain"
        if s.restricted: raise AccessError("denied")
        out = [dict({"id": i}, **{f: r.get(f) for f in fields}) for i, r in sorted(s.rows.items())]
        return out[:limit] if limit else out
    def sudo(s, *a, **k): raise AssertionError("sudo is forbidden")
    with_user = with_context = sudo
    def write(s, *a, **k): raise AssertionError("write is forbidden")
    create = unlink = write


class Env:
    def __init__(s, models, denied=()): s.m, s.denied = models, set(denied)
    def __getitem__(s, k):
        if k in s.denied: raise AccessError("no model access")
        return s.m[k]
    def sudo(s, *a, **k): raise AssertionError("sudo is forbidden")
    with_user = sudo


def p(i): return [i, "x"]


def world():
    return {
        "synapsys.context": {1: dict(code="CTX-SS", name="SS", kind="K-6", kind_ruling="R", purpose_id=p(10)), 2: dict(code="CTX-B", name="B", kind="K-4", kind_ruling=None, purpose_id=p(10)),
                             3: dict(code="CTX-C", name="C", kind="K-12", kind_ruling="R", purpose_id=p(10))},
        "synapsys.purpose": {10: dict(name="P")},
        "synapsys.strategy": {20: dict(code="S", name="s", context_id=p(1), purpose_id=p(10), service_ids=[30])},
        "synapsys.service": {30: dict(code="A", name="a", context_id=False, method_id=p(40))},
        "synapsys.method": {40: dict(code="M", name="m", context_id=p(1), canon_id=False)},
        "synapsys.work.object": {50: dict(strategy_id=p(20), service_id=p(30), method_id=p(40), gate_ids=[], progress_outcome_id=False, progress_benefit_id=False, progress_asset_id=False)},
        "synapsys.asset": {90: dict(name="a", context_id=p(1), rights_holder_id=False), 367: dict(name="b", context_id=p(2), rights_holder_id=False)},
    }


def env_for(data, restricted=(), denied=(), hidden=None, absent=None):
    ms = {}
    for model in A._models(D):
        rows = {i: r for i, r in data.get(model, {}).items() if i not in (hidden or {}).get(model, ())}
        f = (set(A._wanted_fields(D, model)) | {"id"}) - set((absent or {}).get(model, ()))
        ms[model] = Model(rows, f, restricted=model in restricted)
    return Env(ms, denied)


def master(env, persp="Form", depth="enable", cid=None):
    g, a, n = A.collect(env, AccessError, D); return A.build_master(D, g, a, n, persp, depth, cid), (g, a, n)


def edge(o, mid, field):
    return [e for m in o["menus"] if m["menu_id"] == mid for e in m["edges"] if e["field"] == field][0]


def menu_with(field, persp):
    return [m["menu_id"] for m in D["menus"] if m["model"] and any(e["field"] == field for e in m["edges"])][0]


class Definition(unittest.TestCase):
    def test_counts_61_52_9_27(self):
        self.assertEqual((D["counts"]["menus"], D["counts"]["actions"], D["counts"]["containers"], D["counts"]["verbs"]), (61, 52, 9, 27))
        self.assertEqual(len({m["menu_id"] for m in D["menus"]}), 61)
    def test_nine_actions_three_verbs_each_27_unique(self):
        self.assertEqual(len(D["action_verbs"]), 9); self.assertTrue(all(len(v) == 3 for v in D["action_verbs"].values()))
        self.assertEqual(len({i for v in D["action_verbs"].values() for i in v}), 27)
        self.assertEqual({g: list(a) for g, a in D["action_groups"].items()}, {k: list(v) for k, v in G.ACTION_GROUPS.items()})
    def test_six_modes_and_cut_b(self):
        self.assertEqual(sorted(D["modes"]), ["K-1", "K-12", "K-3", "K-4", "K-6", "K-8"]); self.assertEqual(D["cut_b"], G.CUT_B)
    def test_candidate_grammar_status_not_promoted(self):
        self.assertEqual({v["grammar_status"] for v in D["verbs"]}, {"candidate"})
    def test_open_and_candidate_sources_not_invented(self):
        for m in D["menus"]:
            if m["source_status"] in ("OPEN", "DECLARATION_CANDIDATE", "PROPOSAL"): self.assertNotEqual(m["definition_state"], "RULED_DEFINITION", m["path"])
    def test_client_tags_pinned(self):
        self.assertEqual({m["menu_id"]: m["client_tag"] for m in D["menus"] if m["kind"] == "CLIENT_ACTION"}, {177: "synapsys_home", 215: "synapsys_architecture_map", 237: "synapsys_lenses"})
    def test_file_is_reproducible_and_pinned(self):
        r = subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "gen_arch_master_definition.py"), "--check"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(D["source_pins"]["contract_sha256"], "445df39b809ba8785b0c17da2dfb1e60696c3a75358f33922f4e7f1b899e33c1")
    def test_no_strategy_asset_edge_in_definition(self):
        self.assertTrue(all((e["from_model"], e["to_model"]) != ("synapsys.strategy", "synapsys.asset") for e in D["typed_edges"]))
        self.assertEqual(D["forbidden_pairs"], [["synapsys.strategy", "synapsys.asset"]])
    def test_definition_missing_is_stated(self):
        self.assertEqual(A.build_master(None, {}, {}, {})["state"], "DEFINITION_NOT_LOADED"); self.assertIsNone(A.load_definition("/nonexistent.json"))


class Projection(unittest.TestCase):
    def test_nothing_visible_never_empty_never_connected(self):
        o, _ = master(env_for({})); s = json.dumps(o)
        self.assertNotIn("CONNECTED", s.replace("NOT_CONNECTED", "")); self.assertNotIn("EMPTY", s.replace("NONE_VISIBLE", ""))
        self.assertEqual(o["edge_totals"]["instance_edges"], 0)
        self.assertTrue(all(e["state"] == "NONE_VISIBLE_TO_ACTOR" for m in o["menus"] for e in m["edges"]))
    def test_full_actor_sees_connected_edges_with_counts(self):
        o, _ = master(env_for(world())); self.assertEqual(edge(o, menu_with("purpose_id", "Form"), "purpose_id")["state"], "CONNECTED")
        self.assertGreaterEqual(o["edge_totals"]["instance_edges"], 4)
        sc = [e for m in o["menus"] for e in m["edges"] if e["field"] == "context_id" and m["model"] == "synapsys.strategy"][0]; self.assertEqual(sc["instance_edges"], 1)
    def test_form_flow_evolve_are_materially_different(self):
        e = env_for(world()); outs = {q: master(e, q)[0] for q in G.PERSPECTIVES}
        sig = {q: json.dumps([[(m["menu_id"], [(x["field"], x["state"], x["instance_edges"]) for x in m["edges"]]) for m in o["menus"]], o["edge_totals"]], sort_keys=True) for q, o in outs.items()}
        self.assertEqual(len(set(sig.values())), 3)
        self.assertEqual(len({outs[q]["edge_totals"]["typed_edges"] for q in G.PERSPECTIVES}), 3)
    def test_audit_clean_on_full_and_sparse_and_restricted(self):
        for env in (env_for(world()), env_for({}), env_for(world(), restricted={"synapsys.strategy"})):
            g, a, n = A.collect(env, AccessError, D); self.assertEqual(A.master_audit(D, g, a, n), {"ok": True, "findings": []})
    def test_caption_only_master_fails_the_audit(self):
        """Regression: Master v1 changed only the caption. Such an implementation MUST FAIL."""
        g, a, n = A.collect(env_for(world()), AccessError, D); real = A.build_master; form = real(D, g, a, n, "Form")
        def caption_only(d, gr, ac, no, perspective="Form", depth="enable", context_id=None):
            o = copy.deepcopy(form); o["perspective"] = perspective; return o
        A.build_master = caption_only
        try: r = A.master_audit(D, g, a, n)
        finally: A.build_master = real
        self.assertFalse(r["ok"]); self.assertIn("CAPTION_ONLY", {f["finding"] for f in r["findings"]})
    def test_restricted_model_reported_not_exposed(self):
        o, _ = master(env_for(world(), restricted={"synapsys.strategy"}))
        self.assertEqual([e["state"] for m in o["menus"] if m["model"] == "synapsys.strategy" for e in m["edges"]][0], "RESTRICTED")
        self.assertEqual([m["record_state"]["state"] for m in o["menus"] if m["model"] == "synapsys.strategy"][0], "RESTRICTED")
    def test_model_access_denied_at_env_level_is_restricted(self):
        o, (g, a, n) = master(env_for(world(), denied={"synapsys.asset"})); self.assertIn("synapsys.asset", n["restricted"])
    def test_hidden_rows_not_counted_or_named(self):
        full, _ = master(env_for(world())); hid, _ = master(env_for(world(), hidden={"synapsys.asset": {90}}))
        self.assertLess(hid["edge_totals"]["instance_edges"], full["edge_totals"]["instance_edges"])
        am = lambda o: [m for m in o["menus"] if m["model"] == "synapsys.asset"][0]
        self.assertEqual((am(full)["record_state"]["readable_count"], am(hid)["record_state"]["readable_count"]), (2, 1))   # the hidden row is not counted
        self.assertNotIn("record_ids", json.dumps(hid)); self.assertNotIn('"ids"', json.dumps(hid))                          # and no record identity is ever emitted
    def test_field_absent_is_stated_not_invented(self):
        o, (g, a, n) = master(env_for(world(), absent={"synapsys.strategy": {"service_ids"}}), "Flow")
        self.assertEqual(n["field_absent"], {"synapsys.strategy": ["service_ids"]})
        self.assertEqual([e["state"] for m in o["menus"] if m["model"] == "synapsys.strategy" for e in m["edges"] if e["field"] == "service_ids"][0], "FIELD_NOT_PRESENT")
    def test_model_not_installed_is_stated(self):
        e = env_for(world()); del e.m["synapsys.benefit"]; g, a, n = A.collect(e, AccessError, D); self.assertIn("synapsys.benefit", n["model_absent"])
        o = A.build_master(D, g, a, n, "Evolve"); self.assertTrue(any(x["state"] == "MODEL_NOT_INSTALLED" for m in o["menus"] for x in m["edges"]))
    def test_strategy_service_needs_readable_work(self):
        a = master(env_for(world()), "Flow")[0]; b = master(env_for(world(), hidden={"synapsys.work.object": {50}}), "Flow")[0]
        f = lambda o: [e for m in o["menus"] if m["model"] == "synapsys.strategy" for e in m["edges"] if e["field"] == "service_ids"][0]
        self.assertEqual((f(a)["state"], f(a)["instance_edges"]), ("CONNECTED", 1)); self.assertEqual((f(b)["state"], f(b)["instance_edges"]), ("DEFINED_NO_READABLE_INSTANCE", 0))
    def test_foreign_asset_not_a_strategy_edge(self):
        for q in G.PERSPECTIVES:
            o, _ = master(env_for(world()), q); self.assertFalse([1 for m in o["menus"] for e in m["edges"] if m["model"] == "synapsys.strategy" and e["target_model"] == "synapsys.asset"])
    def test_containers_not_applicable_and_honest_holds_carried(self):
        o, _ = master(env_for(world())); cont = [m for m in o["menus"] if m["kind"] == "CONTAINER"]
        self.assertEqual((len(cont), {m["record_state"]["state"] for m in cont}), (9, {"NOT_APPLICABLE"}))
        holds = [m for m in o["menus"] if m["matrix_status"] == "HONEST_HOLD"]; self.assertEqual(len(holds), 12); self.assertTrue(all(m["hold"] and m["hold"]["reason"] for m in holds))
    def test_all_61_rows_present_in_every_perspective(self):
        for q in G.PERSPECTIVES: self.assertEqual(len(master(env_for(world()), q)[0]["menus"]), 61)
    def test_invalid_perspective_and_depth_rejected(self):
        g, a, n = A.collect(env_for(world()), AccessError, D)
        with self.assertRaises(ValueError): A.build_master(D, g, a, n, "Caption")
        with self.assertRaises(ValueError): A.build_master(D, g, a, n, "Form", "enrichest")
    def test_zero_write_zero_sudo_deterministic(self):
        e = env_for(world()); a1 = json.dumps(master(e, "Flow")[0], sort_keys=True); a2 = json.dumps(master(e, "Flow")[0], sort_keys=True); self.assertEqual(a1, a2)
    def test_truncation_reported(self):
        d = world(); d["synapsys.asset"] = {i: dict(name="x", context_id=p(1), rights_holder_id=False) for i in range(1, 12)}
        g, a, n = A.collect(env_for(d), AccessError, D, limit=5); self.assertIn("synapsys.asset", n["truncated"]); self.assertEqual(len(g["records"]["synapsys.asset"]), 5)


class VerbsAndDepth(unittest.TestCase):
    def ctx(self, o, cid): return [c for c in o["verbs"]["contexts"] if c["context_id"] == cid][0]
    def test_27_verbs_9_actions_never_authorised(self):
        o, _ = master(env_for(world())); v = o["verbs"]
        self.assertEqual((v["governed_verbs"], len(v["actions"]), v["execution_authorised"]), (27, 9, False)); self.assertTrue(all(c["eligible"]["execution_authorised"] is False for c in v["contexts"]))
    def test_ruled_kind_gets_modes_unruled_is_hold(self):
        o, _ = master(env_for(world()))
        self.assertEqual((self.ctx(o, 1)["eligible"]["state"], self.ctx(o, 1)["stage"]), ("ELIGIBLE_LIST", "Enhance"))
        self.assertEqual((self.ctx(o, 2)["eligible"]["state"], self.ctx(o, 2)["stage"], self.ctx(o, 2)["eligible"]["verb_ids"]), ("UNKNOWN_HOLD", None, []))
    def test_k12_is_enrich_and_eligible_list_comes_from_modes(self):
        o, _ = master(env_for(world())); c = self.ctx(o, 3); self.assertEqual(c["stage"], "Enrich"); self.assertEqual(c["eligible"]["verb_ids"], sorted(D["modes"]["K-12"]))
    def test_human_only_never_eligible(self):
        d = copy.deepcopy(D); d["verbs"][0]["human_only"] = True; hid = d["verbs"][0]["id"]
        g, a, n = A.collect(env_for(world()), AccessError, d); o = A.build_master(d, g, a, n)
        self.assertTrue(all(hid not in c["eligible"]["verb_ids"] for c in o["verbs"]["contexts"])); self.assertIn(hid, o["verbs"]["human_only_ids"])
    def test_display_enrich_on_non_k12_confers_no_stage(self):
        o, _ = master(env_for(world()), "Form", "enrich"); s = o["stage_by_context"]
        self.assertEqual((s["1"]["display_depth"], s["1"]["stage"]), ("enrich", "Enhance")); self.assertEqual((s["2"]["display_depth"], s["2"]["stage"]), ("enrich", None))
    def test_depth_does_not_change_edges_or_rights(self):
        e = env_for(world()); a = master(e, "Flow", "enable")[0]; b = master(e, "Flow", "enrich")[0]
        self.assertEqual(json.dumps(a["menus"], sort_keys=True), json.dumps(b["menus"], sort_keys=True))
    def test_unseen_context_has_no_verbs_listed(self):
        o, _ = master(env_for(world(), hidden={"synapsys.context": {1}})); self.assertEqual([c["context_id"] for c in o["verbs"]["contexts"]], [2, 3])
    def test_context_filter(self):
        o, _ = master(env_for(world()), cid=3); self.assertEqual([c["context_id"] for c in o["verbs"]["contexts"]], [3])


class AuditAndRights(unittest.TestCase):
    """build_master/master_audit are public and take (graph, actor): they must hold the line themselves, not rely on collect() having filtered."""
    def parts(self):
        return A.collect(env_for(world()), AccessError, D)
    def test_rows_outside_actor_visibility_are_not_counted_or_connected(self):
        g, a, n = self.parts(); full = A.build_master(D, g, a, n, "Form")
        a["visible"]["synapsys.asset"].discard(90); a["visible"]["synapsys.purpose"].discard(10)          # in the graph, NOT readable by this actor
        o = A.build_master(D, g, a, n, "Form")
        am = [m for m in o["menus"] if m["model"] == "synapsys.asset"][0]; self.assertEqual(am["record_state"]["readable_count"], 1)
        self.assertLess(o["edge_totals"]["instance_edges"], full["edge_totals"]["instance_edges"])
        pe = [e for m in o["menus"] if m["model"] == "synapsys.context" for e in m["edges"] if e["field"] == "purpose_id"][0]
        self.assertEqual((pe["state"], pe["instance_edges"]), ("DEFINED_NO_READABLE_INSTANCE", 0))             # target unreadable: edge not shown as connected
        self.assertEqual(A.master_audit(D, g, a, n), {"ok": True, "findings": []})
    def test_container_reason_is_stated_not_modelled(self):
        o, _ = master(env_for(world())); c = [m for m in o["menus"] if m["kind"] == "CONTAINER"][0]
        self.assertIn("container", c["record_state"]["reason"]); self.assertEqual(c["model"], None)
    def test_read_only_and_no_writes_stated(self):
        o, _ = master(env_for(world())); self.assertEqual((o["read_only"], o["writes"], o["master_menu"], o["status"], o["role_tests"]), (True, 0, "NOT_INSTALLED_RELEASE_REQUIRED", "SOURCE_READY_NOT_INSTALLED", "NOT_TESTED"))
    def test_audit_flags_verb_count_drift(self):
        d = copy.deepcopy(D); d["verbs"] = d["verbs"][:26]; g, a, n = A.collect(env_for(world()), AccessError, d)
        self.assertIn("VERB_COUNT_DRIFT", {f["finding"] for f in A.master_audit(d, g, a, n)["findings"]})
    def test_audit_flags_inflated_and_deflated_counts(self):
        g, a, n = self.parts(); real = A.build_master
        for delta, want in ((+1, "LEAKED_COUNT"), (-1, "INVENTED_EDGE")):
            def skewed(d, gr, ac, no, perspective="Form", depth="enable", context_id=None, _d=delta):
                o = real(d, gr, ac, no, perspective, depth, context_id)
                for m in o["menus"]:
                    for e in m["edges"]:
                        if e["instance_edges"] + _d >= 0: e["instance_edges"] += _d; return o
                return o
            A.build_master = skewed
            try: found = {f["finding"] for f in A.master_audit(D, g, a, n)["findings"]}
            finally: A.build_master = real
            self.assertIn(want, found)


lspec = importlib.util.spec_from_file_location("lens_contract", os.path.join(ADDON, "lens_contract.py")); LC = importlib.util.module_from_spec(lspec); lspec.loader.exec_module(LC)


class Lineage(unittest.TestCase):
    """Recursive lens lineage comes only from actual stored FKs the actor can read; the shared lens_contract resolver consumes it unchanged."""
    def lp(self, **kw): g, a, n = A.collect(env_for(world(), **kw), AccessError, D); return A.lineage_parents(g, a)
    def test_direct_fks_only(self):
        lp = self.lp(); self.assertEqual(lp["str:20"], "ctx:1"); self.assertEqual(lp["ctx:1"], "pur:10"); self.assertEqual(lp["ast:90"], "ctx:1"); self.assertEqual(lp["mth:40"], "ctx:1")
    def test_blank_service_context_fk_has_no_parent(self):
        self.assertNotIn("svc:30", self.lp())                                    # Work-mediated Strategy->Service is NOT a lineage edge
    def test_foreign_context_asset_keeps_its_own_context_only(self):
        lp = self.lp(); self.assertEqual(lp["ast:367"], "ctx:2"); self.assertNotEqual(lp["ast:367"], "ctx:1")
    def test_no_strategy_to_asset_lineage(self):
        self.assertTrue(all(not (k.startswith("ast:") and v.startswith("str:")) and not (k.startswith("str:") and v.startswith("ast:")) for k, v in self.lp().items()))
    def test_unreadable_parent_gives_no_parent_and_no_leak(self):
        lp = self.lp(hidden={"synapsys.context": {1}}); self.assertNotIn("str:20", lp); self.assertNotIn("ctx:1", json.dumps(lp))
    def test_restricted_model_contributes_nothing(self):
        self.assertFalse([k for k in self.lp(restricted={"synapsys.asset"}) if k.startswith("ast:")])
    def test_shared_lens_resolver_walks_it_nearest_first_and_cycle_safe(self):
        lp = self.lp(); self.assertEqual(LC.lineage(lp, "str:20"), ("ctx:1", "pur:10"))
        self.assertEqual(LC.lineage({"a": "b", "b": "a"}, "a"), ("b",))
    def test_context_override_cascades_to_directly_bound_children_only(self):
        lp = self.lp(); ov = {"ctx:1": "enrich"}
        self.assertEqual(LC.mode_for("str:20", "enable", ov, list(LC.lineage(lp, "str:20"))), "enrich")
        self.assertEqual(LC.mode_for("svc:30", "enable", ov, list(LC.lineage(lp, "svc:30"))), "enable")        # blank FK: inherits nothing
        self.assertEqual(LC.mode_for("str:20", "enable", {"str:20": "enhance", "ctx:1": "enrich"}, ["ctx:1"]), "enhance")   # local override wins
    def test_master_output_carries_lineage(self):
        o, _ = master(env_for(world())); self.assertEqual(o["lens_lineage"]["str:20"], "ctx:1")


import ast
FORBIDDEN_CALLS = {"sudo", "with_user", "write", "create", "unlink", "execute", "with_context", "browse"}


def forbidden_calls(src):
    """AST-level (docstrings and comments cannot trip or hide it): any call of a write/elevation primitive."""
    return sorted({n.func.attr for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in FORBIDDEN_CALLS}
                  | {n.func.id for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in FORBIDDEN_CALLS})


class Controller(unittest.TestCase):
    """The controller needs Odoo to import; offline we prove it compiles, is read-only, uses the caller's env and is registered exactly once."""
    SRC = open(os.path.join(ADDON, "controllers", "arch_master.py"), encoding="utf-8").read()
    def test_compiles(self): compile(self.SRC, "arch_master_controller.py", "exec")
    def test_read_only_caller_env_no_menu(self):
        self.assertEqual(forbidden_calls(self.SRC), [])
        self.assertNotIn("ir.ui.menu", [n.value for n in ast.walk(ast.parse(self.SRC)) if isinstance(n, ast.Constant) and isinstance(n.value, str)])
        self.assertIn("request.env", self.SRC); self.assertIn("auth='user'", self.SRC); self.assertIn("/synapsys/architecture/master", self.SRC)
    def test_registered_once_after_slice(self):
        init = open(os.path.join(ADDON, "controllers", "__init__.py"), encoding="utf-8").read()
        self.assertEqual(init.count("from . import arch_master\n"), 1); self.assertTrue(init.endswith("from . import arch_slice\nfrom . import arch_master\n"))
    def test_inputs_validated_before_any_read(self):
        i = self.SRC.index("arch_master.collect"); [self.assertLess(self.SRC.index(k), i) for k in ("perspective not in", "depth not in", "context_id must be an integer")]
    def test_module_has_no_odoo_import_or_write_primitive(self):
        src = open(os.path.join(ADDON, "arch_master.py"), encoding="utf-8").read()
        self.assertEqual(forbidden_calls(src), []); self.assertNotIn("import odoo", src); self.assertNotIn("from odoo", src)
    def test_the_guard_itself_detects_a_write(self):
        self.assertEqual(forbidden_calls("def f(env):\n    env.sudo().write({})"), ["sudo", "write"])
        self.assertEqual(forbidden_calls('"""sudo() in a docstring"""\n# .write( in a comment\nx = 1'), [])


if __name__ == "__main__":
    unittest.main()
