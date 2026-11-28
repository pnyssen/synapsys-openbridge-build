"""Independent D009 regressions for Architecture source projection, no Odoo writes."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "addon" / "synapsys"))
import arch_graph as G
import arch_slice as S


def specimen(service_context=2, visible_strategy=True):
    graph = {"records": {
        "synapsys.context": {1: {"code": "CTX-A"}, 2: {"code": "CTX-B"}},
        "synapsys.strategy": {10: {"context_id": 1, "service_ids": [30]}},
        "synapsys.service": {30: {"context_id": service_context}},
    }}
    actor = {"visible": {
        "synapsys.context": {1, 2},
        "synapsys.strategy": {10} if visible_strategy else set(),
        "synapsys.service": {30},
    }, "restricted_models": set()}
    return graph, actor


class CrossContextD009Tests(unittest.TestCase):
    def test_service_root_flags_visible_cross_context_incoming_edge(self):
        graph, actor = specimen(service_context=2)
        edges = G.project(graph, actor, "synapsys.service", 30, "Flow")["edges"]
        link = next(x for x in edges if x["field"] == "service_ids")
        self.assertTrue(link.get("cross_context"), "Service-root cross-Context relation must be flagged")

    def test_service_root_same_context_does_not_false_flag(self):
        graph, actor = specimen(service_context=1)
        edges = G.project(graph, actor, "synapsys.service", 30, "Flow")["edges"]
        link = next(x for x in edges if x["field"] == "service_ids")
        self.assertFalse(link.get("cross_context", False))

    def test_context_root_preserves_existing_cross_context_detection(self):
        graph, actor = specimen(service_context=2)
        edges = G.project(graph, actor, "synapsys.context", 1, "Flow")["edges"]
        link = next(x for x in edges if x["field"] == "service_ids")
        self.assertTrue(link.get("cross_context"))

    def test_hidden_strategy_not_exposed_to_service_root(self):
        graph, actor = specimen(service_context=2, visible_strategy=False)
        out = G.project(graph, actor, "synapsys.service", 30, "Flow")
        self.assertFalse(any(x["field"] == "service_ids" for x in out["edges"]))
        self.assertNotIn(["synapsys.strategy", 10], out["nodes"])

    def test_blank_direct_service_context_keeps_computed_relation(self):
        graph, actor = specimen(service_context=False)
        notes = {"field_absent": {}, "truncated": []}
        out = S.build_slice(graph, actor, notes, context_id=1)
        entry = out["contexts"][0]["strategy_services"][0]["services"]
        self.assertEqual(entry["state"], "REAL_ACTOR_VISIBLE")
        self.assertEqual(entry["items"][0]["link"], "NO_DIRECT_SERVICE_CONTEXT")
        self.assertEqual(entry["items"][0]["relationship_basis"], "STRATEGY_SERVICE_IDS_VIA_WORK_OBJECTS")


if __name__ == "__main__":
    unittest.main()
