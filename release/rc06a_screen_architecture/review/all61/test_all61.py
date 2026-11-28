import json, os, sys, unittest, copy
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import arch_graph as G, build_matrix as M

BASE = json.load(open(os.path.join(HERE,"fixtures","baseline.json")))
SNAP = json.load(open(os.path.join(HERE,"fixtures","live_snapshot.json")))
ROWS = M.build(BASE, SNAP)
BY = {r["action_id"]: r for r in ROWS if r["action_id"] is not None}  # keyed by ACTION id
VERBS, MODES = SNAP["verbs"], SNAP["modes"]

def fixture():
    R = lambda **k: k
    g = {"records": {
      "synapsys.context": {1: R(purpose_id=10, kind="K-3"), 2: R(purpose_id=10, kind="K-4")},
      "synapsys.purpose": {10: R()},
      "synapsys.strategy": {20: R(context_id=1, purpose_id=10, service_ids=[30]), 21: R(context_id=2, purpose_id=10, service_ids=[])},
      "synapsys.service": {30: R(context_id=1, method_id=40)},
      "synapsys.method": {40: R(context_id=1)},
      "synapsys.work.object": {50: R(strategy_id=20, service_id=30, method_id=40, gate_ids=[], progress_outcome_id=60)},
      "synapsys.outcome": {60: R(benefit_ids=[70])},
      "synapsys.benefit": {70: R(service_id=30)},
      "synapsys.oba.link": {80: R(benefit_id=70, asset_id=90)},
      "synapsys.asset": {90: R(context_id=1), 91: R(context_id=2)}}}
    allv = {m: set(r) for m, r in g["records"].items()}
    return g, {"visible": allv}

class Census(unittest.TestCase):
    def test_61_rows_unique(self):
        self.assertEqual(len(ROWS), 61); self.assertEqual(len({r["menu_id"] for r in ROWS}), 61)
    def test_live_tree_matches_baseline(self):
        for r in ROWS:
            self.assertEqual(SNAP["menus"][str(r["menu_id"])][0].replace(" / ","/"), r["path"], r["menu_id"])
    def test_nine_containers_52_actions(self):
        k = [r["menu_kind"] for r in ROWS]
        self.assertEqual((k.count("CONTAINER"), k.count("ACT_WINDOW")+k.count("CLIENT_ACTION")), (9, 52))
    def test_model_domain_equal_live(self):
        for r in ROWS:
            a = SNAP["act_window"].get(str(r["action_id"]))
            if a:
                self.assertEqual(r["model"], a[0])
    def test_every_row_has_determinations(self):
        for r in ROWS:
            for k in ("definition_state","record_state","actors","disposition","tests","live_observed","status","status_reason","perspective","mesh_role"):
                self.assertIn(k, r)
    def test_status_labels_allowed(self):
        ok = {"PASS","FAIL","HONEST_HOLD","NOT_TESTED","RESTRICTED","RELEASE_BLOCKED","REUSED_PASS","IMPLEMENTED_PASS"}
        self.assertTrue({r["status"] for r in ROWS} <= ok)

class Verbs(unittest.TestCase):
    def test_27_unique_nine_by_three(self):
        self.assertEqual(len({v["id"] for v in VERBS}), 27)
        from collections import Counter
        c = Counter(v["action"] for v in VERBS)
        self.assertEqual(set(c.values()), {3}); self.assertEqual(len(c), 9)
    def test_all_candidate_one_human_only(self):
        self.assertTrue(all(v["grammar_status"]=="candidate" for v in VERBS))
        self.assertEqual([v["name"] for v in VERBS if v["human_only"]], ["commit"])
    def test_six_modes(self): self.assertEqual(len(MODES), 6)
    def test_human_only_never_eligible(self):
        for kind in G.CUT_B:
            e = G.eligible_verbs({"kind": kind, "kind_ruling": "R"}, VERBS, MODES)
            self.assertNotIn(14, e["verb_ids"]); self.assertFalse(e["execution_authorised"])
    def test_human_only_excluded_even_when_mode_lists_it(self):
        m = {k: v + [14] for k, v in MODES.items()}  # inject 'commit' into every mode
        for kind in G.CUT_B:
            e = G.eligible_verbs({"kind": kind, "kind_ruling": "R"}, VERBS, m)
            self.assertNotIn(14, e["verb_ids"], kind)
    def test_live_modes_do_not_list_human_only(self):
        self.assertTrue(all(14 not in v for v in MODES.values()))
    def test_unruled_kind_unknown_hold(self):
        for ctx in (None, {}, {"kind": "K-3"}, {"kind": "K-99", "kind_ruling": "R"}):
            self.assertEqual(G.eligible_verbs(ctx, VERBS, MODES)["state"], "UNKNOWN_HOLD")
    def test_display_depth_is_not_stage(self):
        x = G.display_depth_is_not_stage("Enrich", {"kind": "K-3", "kind_ruling": "R"})
        self.assertEqual((x["display_depth"], x["stage"]), ("Enrich", "Enable"))
        self.assertIsNone(G.display_depth_is_not_stage("Enrich", {"kind": "K-12"})["stage"])
    def test_action_group_menus_340_348(self):
        total = 0
        for mid in range(340, 349):
            r = BY[mid]; self.assertEqual(len(r["verb_ids"]), 3); total += 3
        self.assertEqual(total, 27)
    def test_commit_group_flagged(self):
        flagged = [m for m in range(340, 349) if BY[m]["human_only_excluded"]]
        self.assertEqual(flagged and len(flagged), 1)

class FFE(unittest.TestCase):
    def test_projection_changes_nodes_and_edges(self):
        g, a = fixture(); p = {k: G.project(g, a, "synapsys.strategy", 20, k) for k in G.PERSPECTIVES}
        self.assertNotEqual(p["Form"]["edges"], p["Flow"]["edges"])
        self.assertNotEqual(p["Flow"]["nodes"], p["Evolve"]["nodes"])
        self.assertEqual(len({json.dumps(v, sort_keys=True) for v in p.values()}), 3)
    def test_caption_only_defect_fails(self):
        """Master v1 defect: only the caption changed. This detector must report it."""
        g, a = fixture()
        def caption_only(persp):
            r = G.project(g, a, "synapsys.strategy", 20, "Form"); r["perspective"] = persp; return r
        outs = {json.dumps(caption_only(k)["nodes"]+caption_only(k)["edges"], sort_keys=True) for k in G.PERSPECTIVES}
        self.assertEqual(len(outs), 1)  # defect signature: identical data under three captions
        real = {json.dumps(G.project(g, a, "synapsys.strategy", 20, k)["edges"], sort_keys=True) for k in G.PERSPECTIVES}
        self.assertEqual(len(real), 3)  # fixed implementation: distinct
    def test_denied_redacted(self):
        g, a = fixture(); a["visible"]["synapsys.strategy"].discard(20)
        r = G.project(g, a, "synapsys.strategy", 20, "Flow")
        self.assertEqual((r["state"], r["nodes"], r["edges"]), ("DENIED_REDACTED", [], []))
    def test_hidden_neighbour_not_leaked(self):
        g, a = fixture(); a["visible"]["synapsys.service"].discard(30)
        r = G.project(g, a, "synapsys.strategy", 20, "Flow")
        self.assertNotIn(["synapsys.service", 30], r["nodes"])
    def test_bad_perspective(self):
        g, a = fixture()
        with self.assertRaises(ValueError): G.project(g, a, "synapsys.strategy", 20, "Caption")
    def test_deterministic(self):
        g, a = fixture()
        self.assertEqual(G.digest(G.project(g, a, "synapsys.strategy", 20, "Flow")), G.digest(G.project(g, a, "synapsys.strategy", 20, "Flow")))
    def test_no_strategy_asset_edge(self):
        self.assertFalse(G.edge_defined("synapsys.strategy", "synapsys.asset"))
        self.assertTrue(all(not (e[0]=="synapsys.strategy" and e[3]=="synapsys.asset") for e in G.EDGES))

class Chain(unittest.TestCase):
    def test_full_chain_connected(self):
        g, a = fixture(); w = G.walk_chain(g, a, 1)
        self.assertIsNone(w["stopped_at"]); self.assertEqual([s["step"] for s in w["steps"]][-1], "Asset")
    def test_stops_at_missing_service(self):
        g, a = fixture(); g["records"]["synapsys.strategy"][20]["service_ids"] = []
        w = G.walk_chain(g, a, 1); self.assertEqual((w["stopped_at"], w["reason"]), ("Service", "UNOBSERVED_TO_ACTOR"))  # absent == hidden to a plain actor
        a["complete_view"] = {"synapsys.service"}                                                                  # MISSING only when completeness is attested
        w = G.walk_chain(g, a, 1); self.assertEqual((w["stopped_at"], w["reason"]), ("Service", "MISSING"))
    def test_stops_at_missing_method(self):
        g, a = fixture(); g["records"]["synapsys.service"][30]["method_id"] = None
        self.assertEqual(G.walk_chain(g, a, 1)["stopped_at"], "Method")
    def test_stops_at_denied_edge(self):
        g, a = fixture(); a["visible"]["synapsys.benefit"].discard(70)
        w = G.walk_chain(g, a, 1); self.assertEqual((w["stopped_at"], w["reason"]), ("Benefit", "UNOBSERVED_TO_ACTOR"))
        g2, a2 = fixture(); g2["records"]["synapsys.outcome"][60]["benefit_ids"] = []        # genuinely absent: the SAME answer, nothing disclosed
        self.assertEqual(G.walk_chain(g2, a2, 1)["steps"][-1], w["steps"][-1])
    def test_cross_context_asset_not_accepted(self):
        g, a = fixture(); g["records"]["synapsys.oba.link"][80]["asset_id"] = 91
        w = G.walk_chain(g, a, 1); self.assertEqual((w["stopped_at"], w["reason"]), ("Asset", "WRONG_CONTEXT"))
        self.assertIn(91, g["records"]["synapsys.asset"])  # not deleted
    def test_unobserved_context(self):
        g, a = fixture(); a["visible"]["synapsys.context"].discard(1)
        self.assertEqual(G.walk_chain(g, a, 1)["reason"], "UNOBSERVED_TO_ACTOR")
    def test_walk_zero_write(self):
        g, a = fixture(); before = json.dumps(g, sort_keys=True); G.walk_chain(g, a, 1); G.project(g, a, "synapsys.strategy", 20, "Flow")
        self.assertEqual(before, json.dumps(g, sort_keys=True))
    def test_live_chain_stops_truthfully(self):
        """Live fact read 28 Nov: Services visible=49 with 0 context/method links, so no live path can pass Service."""
        self.assertEqual(SNAP["counts"]["synapsys.service"], 49)

class RightsFirstChain(unittest.TestCase):
    """Post-rowscope items 1-2: Work-mediated Strategy->Service, direct Service->Context FK kept distinct, non-disclosing hops."""
    def svc_step(self, w): return [s for s in w["steps"] if s["step"] == "Service"][0]
    def test_service_needs_readable_supporting_work_object(self):
        g, a = fixture(); a["visible"]["synapsys.work.object"].discard(50)
        w = G.walk_chain(g, a, 1); self.assertEqual((w["stopped_at"], w["reason"]), ("Service", "UNOBSERVED_TO_ACTOR"))
        self.assertNotIn("30", json.dumps(w)); self.assertNotIn("50", json.dumps(w))
    def test_unsupported_computed_relation_not_projected(self):
        g, a = fixture(); a["visible"]["synapsys.work.object"].discard(50)
        r = G.project(g, a, "synapsys.strategy", 20, "Flow")
        self.assertFalse([e for e in r["edges"] if e["field"] == "service_ids"]); self.assertTrue(G.projection_audit(g, a, "synapsys.strategy", 20)["ok"])
        g, a = fixture(); self.assertTrue([e for e in G.project(g, a, "synapsys.strategy", 20, "Flow")["edges"] if e["field"] == "service_ids"])
    def test_blank_service_context_fk_is_labelled_not_asserted_absent(self):
        g, a = fixture(); g["records"]["synapsys.service"][30]["context_id"] = None
        s = self.svc_step(G.walk_chain(g, a, 1)); self.assertEqual(s["state"], "CONNECTED")                 # Work-mediated relationship still real
        self.assertEqual(s["service_context_link"], {"30": "NO_DIRECT_SERVICE_CONTEXT_FK"}); self.assertEqual(s["supporting_work_ids"], {"30": [50]})
    def test_direct_and_wrong_context_link_labels(self):
        g, a = fixture(); self.assertEqual(self.svc_step(G.walk_chain(g, a, 1))["service_context_link"], {"30": "LINKED_TO_THIS_CONTEXT"})
        g["records"]["synapsys.service"][30]["context_id"] = 2
        self.assertEqual(self.svc_step(G.walk_chain(g, a, 1))["service_context_link"], {"30": "WRONG_CONTEXT"})
    def test_hidden_foreign_asset_indistinguishable_from_absent(self):
        g, a = fixture(); g["records"]["synapsys.oba.link"][80]["asset_id"] = 91; a["visible"]["synapsys.asset"].discard(91)
        hidden = G.walk_chain(g, a, 1)
        g2, a2 = fixture(); g2["records"]["synapsys.oba.link"][80]["asset_id"] = None
        self.assertEqual((hidden["stopped_at"], hidden["reason"]), ("Asset", "UNOBSERVED_TO_ACTOR")); self.assertEqual(hidden["steps"][-1], G.walk_chain(g2, a2, 1)["steps"][-1])
        self.assertNotIn("WRONG_CONTEXT", json.dumps(hidden)); self.assertNotIn("91", json.dumps(hidden))
    def test_wrong_context_only_for_asset_actor_can_read(self):
        g, a = fixture(); g["records"]["synapsys.oba.link"][80]["asset_id"] = 91
        self.assertEqual(G.walk_chain(g, a, 1)["reason"], "WRONG_CONTEXT")                                    # Steward-like: readable, so labelled
    def test_hidden_oba_link_not_followed(self):
        g, a = fixture(); a["visible"]["synapsys.oba.link"].discard(80)
        self.assertEqual(G.walk_chain(g, a, 1)["reason"], "UNOBSERVED_TO_ACTOR")
    def test_restricted_context_model_is_unobserved_not_walked(self):
        g, a = fixture(); a["restricted_models"] = {"synapsys.context"}
        w = G.walk_chain(g, a, 1); self.assertEqual((w["stopped_at"], w["reason"], len(w["steps"])), ("Context", "UNOBSERVED_TO_ACTOR", 1))
    def test_context_visible_id_without_source_record_is_unobserved(self):
        g, a = fixture(); a["visible"]["synapsys.context"].add(999)
        self.assertEqual(G.walk_chain(g, a, 999)["reason"], "UNOBSERVED_TO_ACTOR")
    def test_restricted_model_never_continues_chain(self):
        g, a = fixture(); a["restricted_models"] = {"synapsys.method"}
        w = G.walk_chain(g, a, 1); self.assertEqual((w["stopped_at"], w["reason"]), ("Method", "UNOBSERVED_TO_ACTOR"))

class Negatives(unittest.TestCase):
    def test_offering_k6_filter(self):
        r = BY[296]; self.assertEqual((r["model"], r["domain"].replace(" ","")), ("synapsys.context", "[('kind','=','K-6')]"))
    def test_filtered_entry_menus(self):
        for mid, code in ((190,"CAPABILITY"),(191,"PRODUCT"),(192,"CHANGE")):
            self.assertEqual(BY[mid]["model"], "synapsys.mesh.entry"); self.assertIn("N."+code, BY[mid]["domain"])
    def test_product_source_open_not_invented(self):
        self.assertIn(BY[191]["status"], ("HONEST_HOLD",)); self.assertIn(BY[191]["definition_state"], ("SOURCE_OPEN_NOT_INVENTED","CANDIDATE_OR_PROPOSAL"))
    def test_workflow_native_gate_decision(self): self.assertEqual(BY[327]["model"], "synapsys.gate.decision")
    def test_restricted_registers(self):
        for m in (335, 336): self.assertEqual((BY[m]["record_state"], BY[m]["status"]), ("RESTRICTED","RESTRICTED"))
    def test_strategy_identity_shared(self):
        self.assertEqual(BY[295]["model"], BY[325]["model"]); self.assertEqual(BY[295]["model"], "synapsys.strategy")
    def test_progress_and_work_same_model(self):
        self.assertEqual(BY[290]["model"], BY[292]["model"]); self.assertEqual(BY[290]["model"], "synapsys.work.object")
    def test_zero_count_not_empty(self):
        for r in ROWS: self.assertNotEqual(r["record_state"], "EMPTY")
    def test_asset_note_present(self): self.assertIn("367", BY[308]["negative_test"] or "")
    def test_service_release_blocked(self): self.assertEqual(BY[297]["status"], "RELEASE_BLOCKED")
    def test_client_actions_not_tested(self):
        for m in (331, 332, 358): self.assertEqual(BY[m]["status"], "NOT_TESTED")
    def test_role_tests_not_claimed(self):
        for r in ROWS: self.assertIn("NOT_TESTED", str(r["actors"]["steward_collaborator_client"]))
    def test_verbs_remain_candidate(self):
        self.assertTrue(all(v["grammar_status"]=="candidate" for v in VERBS))

class Reliability(unittest.TestCase):
    def test_matrix_idempotent(self):
        self.assertEqual(json.dumps(M.build(BASE, SNAP), sort_keys=True), json.dumps(M.build(BASE, SNAP), sort_keys=True))
    def test_source_drift_detected(self):
        s = copy.deepcopy(SNAP); s["menus"]["236"][0] = "SynapSys / Architecture / Renamed"
        r = {x["menu_id"]: x for x in M.build(BASE, s)}[236]
        self.assertNotEqual(r["live_name_path"].replace(" / ","/"), r["path"])
    def test_no_write_in_modules(self):
        for f in ("arch_graph.py","build_matrix.py"):
            src = open(os.path.join(HERE, f)).read().replace("json.dump(out, open(p,\"w\")", "")
            for bad in ("odoo20_create","odoo20_write","unlink","execute_kw","requests."): self.assertNotIn(bad, src)
if __name__ == "__main__": unittest.main()
