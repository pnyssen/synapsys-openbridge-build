import copy, hashlib, importlib.util, json, os, re, sys, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.environ.get("SCAFFOLD_SRC", os.path.join(HERE, "..", "src", "scaffold_lens.py"))
spec = importlib.util.spec_from_file_location("scaffold_lens", SRC)
sl = importlib.util.module_from_spec(spec); spec.loader.exec_module(sl)
REGP = os.path.join(HERE, "..", "fixtures", "mesh_registry_v0_3.json")
RAW = open(REGP, "rb").read()
REG = json.loads(RAW)
CTX = "CTX-A"
LIB = {"LIB:SC04:1": {"sha256": "a" * 64, "label": "SC-04 Capability Encoding and Reuse"}}
GOOD = {"id": "EV1", "noun_id": "N.SERVICE", "context_id": CTX, "kind": "library",
        "source_ref": "LIB:SC04:1", "sha256": "a" * 64}
STEW = {"groups": {"steward"}, "context_ids": {CTX}}
COLL = {"groups": {"collaborator"}, "context_ids": {CTX}}
COLL_OUT = {"groups": {"collaborator"}, "context_ids": {"CTX-B"}}
CLI = {"groups": {"client"}, "context_ids": {CTX}}

def B(noun, depth, actor, ev=(GOOD,), ctx=CTX):
    return sl.build_scaffold(REG, noun, depth, actor, list(ev), LIB, ctx)

class T(unittest.TestCase):
    def test_S1_registry_identity(self):
        self.assertEqual(hashlib.sha256(RAW).hexdigest(), "7c31aa1de4c97e8e062c5ae9e2f907b4c67ea0949bf143235499c32b1a30f423")
        self.assertEqual((len(REG["elements"]), len(REG["clusters"])), (361, 196))
    def test_S2_hctx_roles_human_readable(self):
        els = sl.index_registry(REG)
        rows = sl.roles_for(REG, els, "H.CTX")
        self.assertEqual(len(rows), 7)
        self.assertTrue(all(r["role_label"] and not r["role_label"].startswith("R.") for r in rows))
        self.assertTrue(all(r["bound_label"] and not r["bound_label"].startswith("N.") for r in rows))
        req = {r["role_label"] for r in rows if r["required"]}
        self.assertEqual(len(req), 3, req)
        self.assertEqual({r["cluster_id"] for r in rows}, {"MC-390147223f2d"})
    def test_S3_enable_is_definition_only(self):
        o = B("N.CONTEXT", "enable", COLL)
        self.assertEqual(o["result"], "OK"); self.assertNotIn("roles", o); self.assertNotIn("peers", o)
        self.assertEqual(o["status"], "RULED")
    def test_S4_enhance_roles_peers_hold_when_no_source(self):
        o = B("N.CONTEXT", "enhance", COLL, ev=())
        peers = {p["id"]: p for p in o["peers"]}
        self.assertEqual(set(peers), {"N.CAPABILITY", "N.SERVICE"})
        self.assertEqual(peers["N.CAPABILITY"]["status"], "PROPOSAL")
        self.assertEqual(peers["N.SERVICE"]["status"], "RULED")
        for p in peers.values():
            self.assertEqual(p["operating_source"], "NO_OPERATING_SOURCE"); self.assertTrue(p["hold"])
        self.assertEqual(len(o["roles"]), 7); self.assertNotIn("evidence", peers["N.SERVICE"])
    def test_S5_enrich_with_valid_library_source(self):
        o = B("N.CONTEXT", "enrich", COLL)
        s = {p["id"]: p for p in o["peers"]}["N.SERVICE"]
        self.assertEqual(s["operating_source"], "SOURCED")
        self.assertEqual(s["evidence"][0]["sha256"], "a" * 64)
        cap = {p["id"]: p for p in o["peers"]}["N.CAPABILITY"]
        self.assertEqual(cap["operating_source"], "NO_OPERATING_SOURCE")
        self.assertTrue(o["open_questions"] is not None and o["definition_source"])
    def test_S6_incorrect_source_hash_rejected(self):
        bad = dict(GOOD, sha256="b" * 64)
        o = B("N.CONTEXT", "enrich", COLL, ev=[bad])
        s = {p["id"]: p for p in o["peers"]}["N.SERVICE"]
        self.assertEqual(s["operating_source"], "NO_OPERATING_SOURCE"); self.assertEqual(s["evidence"], [])
        self.assertEqual(s["rejected_evidence"], [{"reason": "SOURCE_HASH_MISMATCH"}])
        self.assertNotIn("EV1", json.dumps(o))
    def test_S6b_unknown_source_rejected(self):
        o = B("N.CONTEXT", "enrich", COLL, ev=[dict(GOOD, source_ref="LIB:NOPE")])
        s = {p["id"]: p for p in o["peers"]}["N.SERVICE"]
        self.assertEqual(s["rejected_evidence"], [{"reason": "SOURCE_NOT_FOUND"}])
    def test_S7_foreign_context_rejected(self):
        o = B("N.CONTEXT", "enrich", COLL, ev=[dict(GOOD, context_id="CTX-OTHER")])
        s = {p["id"]: p for p in o["peers"]}["N.SERVICE"]
        self.assertEqual(s["evidence"], []); self.assertEqual(s["rejected_evidence"], [{"reason": "FOREIGN_CONTEXT"}])
        self.assertEqual(s["operating_source"], "NO_OPERATING_SOURCE")
    def test_S8_client_clamped_no_evidence(self):
        o = B("N.CONTEXT", "enrich", CLI)
        self.assertEqual(o["depth_effective"], "enhance"); self.assertTrue(o["depth_clamped"])
        s = {p["id"]: p for p in o["peers"]}["N.SERVICE"]
        self.assertNotIn("evidence", s); self.assertNotIn("definition_source", o)
        self.assertEqual(s["operating_source"], "NO_OPERATING_SOURCE")  # client never gets sourced claim
    def test_S9_unknown_actor_refused(self):
        for a in ({}, {"groups": set()}, {"groups": {"portal"}}):
            self.assertEqual(B("N.CONTEXT", "enable", a)["result"], "REFUSED")
    def test_S10_collaborator_outside_context_denied(self):
        o = B("N.CONTEXT", "enrich", COLL_OUT)
        s = {p["id"]: p for p in o["peers"]}["N.SERVICE"]
        self.assertEqual(s["evidence"], []); self.assertEqual(s["rejected_evidence"], [{"reason": "ACTOR_NOT_IN_CONTEXT"}])
    def test_S11_no_mutation_no_writes(self):
        before = copy.deepcopy(REG); o = B("N.CONTEXT", "enrich", STEW)
        self.assertEqual(before, REG); self.assertEqual(o["writes"], 0)
    def test_S12_bad_inputs(self):
        self.assertEqual(B("N.NOPE", "enable", COLL)["reason"], "UNKNOWN_NOUN")
        with self.assertRaises(ValueError): B("N.CONTEXT", "deep", COLL)
    def test_S13_no_privileged_or_write_calls_in_source(self):
        code = re.sub(r'""".*?"""', "", open(SRC).read(), flags=re.S)
        for bad in (r"\bsudo\b", r"\.write\(", r"\.create\(", r"\.unlink\(", r"\bexecute\(", r"import os", r"open\("):
            self.assertIsNone(re.search(bad, code), bad)
    def test_S14_depth_is_cumulative(self):
        a, b, c = (B("N.CONTEXT", d, STEW) for d in sl.DEPTHS)
        self.assertTrue(set(a) <= set(b) <= set(c))
class T2(unittest.TestCase):
    def test_S15_evidence_gate_independent_of_depth_clamp(self):
        shown, rej = sl._evidence_for("N.SERVICE", CLI, [GOOD], LIB, CTX)
        self.assertEqual((shown, rej), ([], []))
if __name__ == "__main__":
    unittest.main(verbosity=2)
