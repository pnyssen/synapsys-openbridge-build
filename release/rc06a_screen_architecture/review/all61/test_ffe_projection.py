"""Governed incoming/member FFE projection and the independent projection audit. Offline fixtures only: logic proof, not a V20 read."""
import copy, json, os, sys, unittest
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import arch_graph as G
from test_all61 import fixture

def ends(r): return {(e["from"][0], e["from"][1], e["field"], e["to"][0], e["to"][1]) for e in r["edges"]}

def legacy_project(graph, actor, model, rid, perspective):
    """The pre-change algorithm (outgoing only), kept here ONLY to prove the audit rejects it."""
    if not G._visible(actor, model, rid) or G._rec(graph, model, rid) is None:
        return {"state": "DENIED_REDACTED", "perspective": perspective, "nodes": [], "edges": []}
    nodes, edges, frontier, seen = {(model, rid)}, [], [(model, rid)], set()
    while frontier:
        cm, cid = frontier.pop()
        if (cm, cid) in seen: continue
        seen.add((cm, cid))
        for (fm, field, typ, tm, p, ev) in G.edges_for(perspective):
            rec = G._rec(graph, cm, cid)
            if fm == cm and rec is not None:
                for t in G._targets(rec, field):
                    if G._visible(actor, tm, t) and G._rec(graph, tm, t) is not None:
                        edges.append({"from": [cm, cid], "field": field, "type": typ, "to": [tm, t], "direction": "out"}); nodes.add((tm, t)); frontier.append((tm, t))
    return {"state": "PROJECTED", "perspective": perspective, "nodes": sorted(map(list, nodes)), "edges": sorted(edges, key=json.dumps)}

class Source(unittest.TestCase):
    def test_context_and_service_instances_audit_clean(self):
        g, a = fixture()
        for m, i in (("synapsys.context", 1), ("synapsys.context", 2), ("synapsys.service", 30), ("synapsys.strategy", 20), ("synapsys.asset", 90)):
            self.assertEqual(G.projection_audit(g, a, m, i), {"ok": True, "findings": []}, (m, i))
    def test_context_three_perspectives_distinct_and_source_backed(self):
        g, a = fixture(); p = {k: G.project(g, a, "synapsys.context", 1, k) for k in G.PERSPECTIVES}
        self.assertEqual(len({json.dumps([v["nodes"], v["edges"]], sort_keys=True) for v in p.values()}), 3)
        self.assertTrue(all(p[k]["edges"] for k in G.PERSPECTIVES))
    def test_service_three_perspectives_distinct(self):
        g, a = fixture(); p = {k: G.project(g, a, "synapsys.service", 30, k) for k in G.PERSPECTIVES}
        self.assertEqual(len({json.dumps([v["nodes"], v["edges"]], sort_keys=True) for v in p.values()}), 3)
    def test_direction_is_relative_to_the_projected_element(self):
        g, a = fixture()
        for k in G.PERSPECTIVES:
            for e in G.project(g, a, "synapsys.context", 1, k)["edges"]:
                self.assertEqual(e["direction"], "out" if e["from"] == ["synapsys.context", 1] else "in" if e["to"] == ["synapsys.context", 1] else "via")
    def test_directions_recorded(self):
        g, a = fixture(); r = G.project(g, a, "synapsys.service", 30, "Flow")
        self.assertEqual({e["direction"] for e in r["edges"]}, {"in", "out"})
    def test_empty_when_source_has_nothing_is_not_a_defect_and_not_invented(self):
        g, a = fixture(); r = G.project(g, a, "synapsys.context", 2, "Flow")
        self.assertEqual((r["edges"], G.projection_audit(g, a, "synapsys.context", 2)["ok"]), ([], True))
    def test_dangling_target_never_invented(self):
        g, a = fixture(); g["records"]["synapsys.strategy"][20]["service_ids"] = [30, 999]
        self.assertTrue(all(e["to"] != ["synapsys.service", 999] for e in G.project(g, a, "synapsys.strategy", 20, "Flow")["edges"]))
        self.assertTrue(G.projection_audit(g, a, "synapsys.strategy", 20)["ok"])
    def test_cross_context_association_flagged_not_dropped_or_adopted(self):
        g, a = fixture(); g["records"]["synapsys.service"][31] = dict(context_id=2, method_id=None); g["records"]["synapsys.strategy"][20]["service_ids"] = [30, 31]
        g["records"]["synapsys.work.object"][51] = dict(strategy_id=20, service_id=31, method_id=None, gate_ids=[], progress_outcome_id=None); a["visible"]["synapsys.work.object"].add(51)
        a["visible"]["synapsys.service"].add(31); r = G.project(g, a, "synapsys.context", 1, "Flow")
        x = [e for e in r["edges"] if e["to"] == ["synapsys.service", 31]]
        self.assertTrue(x and all(e.get("cross_context") for e in x)); self.assertTrue(G.projection_audit(g, a, "synapsys.context", 1)["ok"])

class Governance(unittest.TestCase):
    def test_hidden_incoming_source_not_exposed(self):
        g, a = fixture(); a["visible"]["synapsys.work.object"].discard(50); r = G.project(g, a, "synapsys.service", 30, "Flow")
        self.assertNotIn(["synapsys.work.object", 50], r["nodes"]); self.assertNotIn("synapsys.work.object", json.dumps(r["edges"]))
    def test_restricted_model_never_exposed_and_reported_at_catalogue_level_only(self):
        g, a = fixture(); a["restricted_models"] = {"synapsys.strategy"}; r = G.project(g, a, "synapsys.context", 1, "Flow")
        self.assertNotIn("synapsys.strategy", json.dumps(r["nodes"]) + json.dumps(r["edges"]))
        cov = G.project(g, a, "synapsys.context", 1, "Form")["coverage"]
        self.assertIn({"edge": "synapsys.strategy.context_id", "direction": "in", "state": "SOURCE_MODEL_RESTRICTED"}, cov)
    def test_actor_with_only_root_visible_gets_root_only_and_no_ids(self):
        g, a = fixture(); a["visible"] = {"synapsys.context": {1}}; r = G.project(g, a, "synapsys.context", 1, "Flow")
        self.assertEqual((r["nodes"], r["edges"]), ([["synapsys.context", 1]], []))
        self.assertTrue(all(c["state"] in ("NONE_VISIBLE_TO_ACTOR", "SOURCE_MODEL_RESTRICTED") for c in r["coverage"]))
    def test_zero_visible_never_reported_as_empty_state(self):
        g, a = fixture(); a["visible"] = {"synapsys.context": {1}}; blob = json.dumps(G.project(g, a, "synapsys.context", 1, "Form"))
        self.assertNotIn("EMPTY", blob.replace("EMPTY_WHERE", ""))
    def test_unseen_root_redacted_with_no_coverage_leak(self):
        g, a = fixture(); a["visible"]["synapsys.service"].discard(30); r = G.project(g, a, "synapsys.service", 30, "Flow")
        self.assertEqual((r["state"], r["nodes"], r["edges"], r["coverage"]), ("DENIED_REDACTED", [], [], []))
    def test_restricted_root_redacted(self):
        g, a = fixture(); a["restricted_models"] = {"synapsys.service"}
        self.assertEqual(G.project(g, a, "synapsys.service", 30, "Flow")["state"], "DENIED_REDACTED")
    def test_projection_is_read_only_and_deterministic(self):
        g, a = fixture(); before = json.dumps(g, sort_keys=True) + json.dumps({k: sorted(v) for k, v in a["visible"].items()}, sort_keys=True)
        r1 = G.project(g, a, "synapsys.context", 1, "Flow"); r2 = G.project(g, a, "synapsys.context", 1, "Flow"); G.projection_audit(g, a, "synapsys.context", 1)
        self.assertEqual(G.digest(r1), G.digest(r2)); self.assertEqual(before, json.dumps(g, sort_keys=True) + json.dumps({k: sorted(v) for k, v in a["visible"].items()}, sort_keys=True))
    def test_no_strategy_asset_edge_even_through_context_membership(self):
        g, a = fixture()
        for k in G.PERSPECTIVES:
            for e in G.project(g, a, "synapsys.context", 1, k)["edges"]: self.assertNotEqual((e["from"][0], e["to"][0]), ("synapsys.strategy", "synapsys.asset"))

    def test_no_duplicate_edges_in_any_projection(self):
        g, a = fixture()
        for m, i in (("synapsys.context", 1), ("synapsys.context", 2), ("synapsys.service", 30), ("synapsys.strategy", 20)):
            for k in G.PERSPECTIVES:
                es = [(tuple(e["from"]), e["field"], tuple(e["to"])) for e in G.project(g, a, m, i, k)["edges"]]; self.assertEqual(len(es), len(set(es)), (m, i, k))
class AuditRejectsDefects(unittest.TestCase):
    def kinds(self, proj, m="synapsys.context", i=1):
        g, a = fixture(); return {f["finding"] for f in G.projection_audit(g, a, m, i, projector=proj)["findings"]}
    def test_legacy_outgoing_only_rejected_for_context_and_service(self):
        self.assertTrue(self.kinds(legacy_project, "synapsys.context", 1) & {"EMPTY_WHERE_SOURCE_BACKED", "MISSING_SOURCE_BACKED_EDGE"})
        self.assertTrue(self.kinds(legacy_project, "synapsys.service", 30) & {"EMPTY_WHERE_SOURCE_BACKED", "MISSING_SOURCE_BACKED_EDGE"})
    def test_caption_only_rejected(self):
        def cap(g, a, m, i, p): r = G.project(g, a, m, i, "Form"); r = dict(r); r["perspective"] = p; return r
        self.assertIn("CAPTION_ONLY", self.kinds(cap))
    def test_empty_by_design_rejected(self):
        def empty(g, a, m, i, p): return {"state": "PROJECTED", "perspective": p, "nodes": [[m, i]], "edges": []}
        self.assertIn("EMPTY_WHERE_SOURCE_BACKED", self.kinds(empty))
    def test_invented_edge_rejected(self):
        def inv(g, a, m, i, p):
            r = copy.deepcopy(G.project(g, a, m, i, p)); r["edges"].append({"from": [m, i], "field": "service_ids", "type": "many2many", "to": ["synapsys.service", 31], "direction": "out"}); return r
        self.assertIn("INVENTED_EDGE", self.kinds(inv, "synapsys.strategy", 20))
    def test_leaking_projector_rejected(self):
        g, a = fixture(); a["visible"]["synapsys.service"].discard(30)
        def leak(g_, a_, m, i, p):
            r = copy.deepcopy(G.project(g_, a_, m, i, p)); r["nodes"].append(["synapsys.service", 30]); return r
        self.assertIn("LEAKED_NODE", {f["finding"] for f in G.projection_audit(g, a, "synapsys.strategy", 20, projector=leak)["findings"]})
    def test_dropping_incoming_edges_rejected(self):
        def drop(g, a, m, i, p):
            r = copy.deepcopy(G.project(g, a, m, i, p)); r["edges"] = [e for e in r["edges"] if e["direction"] != "in"]; return r
        self.assertTrue(self.kinds(drop, "synapsys.service", 30) & {"MISSING_SOURCE_BACKED_EDGE", "EMPTY_WHERE_SOURCE_BACKED"})
    def test_real_projector_passes_the_same_audit(self):
        self.assertEqual(self.kinds(G.project), set())
if __name__ == "__main__": unittest.main()
