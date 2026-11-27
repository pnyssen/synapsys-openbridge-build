"""Original-failure regressions for the FFE projection. Uses only G.project(...) so the SAME file runs on the pre-change arch_graph (must FAIL)
and on the corrected one (must PASS). Fixtures are offline source-shaped data; nothing here observes V20."""
import os, sys, unittest
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import arch_graph as G
from test_all61 import fixture

def ends(r): return {(e["from"][0], e["from"][1], e["field"], e["to"][0], e["to"][1]) for e in r["edges"]}

class OriginalFailures(unittest.TestCase):
    def test_F1_context_form_exposes_incoming_members(self):
        g, a = fixture(); e = ends(G.project(g, a, "synapsys.context", 1, "Form"))
        for want in (("synapsys.strategy", 20, "context_id", "synapsys.context", 1), ("synapsys.service", 30, "context_id", "synapsys.context", 1),
                     ("synapsys.method", 40, "context_id", "synapsys.context", 1), ("synapsys.asset", 90, "context_id", "synapsys.context", 1)):
            self.assertIn(want, e, "source-backed incoming Form edge missing: %r" % (want,))
    def test_F2_context_flow_not_empty_when_source_has_flow(self):
        g, a = fixture(); e = ends(G.project(g, a, "synapsys.context", 1, "Flow"))
        self.assertIn(("synapsys.strategy", 20, "service_ids", "synapsys.service", 30), e)
    def test_F3_context_evolve_not_empty_when_source_has_evolve(self):
        g, a = fixture(); e = ends(G.project(g, a, "synapsys.context", 1, "Evolve"))
        self.assertIn(("synapsys.benefit", 70, "service_id", "synapsys.service", 30), e)
    def test_F4_service_flow_exposes_incoming_strategy_and_work_object(self):
        g, a = fixture(); e = ends(G.project(g, a, "synapsys.service", 30, "Flow"))
        self.assertIn(("synapsys.strategy", 20, "service_ids", "synapsys.service", 30), e)
        self.assertIn(("synapsys.work.object", 50, "service_id", "synapsys.service", 30), e)
    def test_F5_service_evolve_exposes_incoming_benefit(self):
        g, a = fixture(); self.assertIn(("synapsys.benefit", 70, "service_id", "synapsys.service", 30), ends(G.project(g, a, "synapsys.service", 30, "Evolve")))
if __name__ == "__main__": unittest.main()
