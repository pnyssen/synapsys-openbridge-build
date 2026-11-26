import hashlib, importlib.util, json, os, re, sys, unittest
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.join(HERE, "..", "src")
sys.path.insert(0, SRC)
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m; spec.loader.exec_module(m); return m
sl = load("scaffold_lens", os.path.join(SRC, "scaffold_lens.py"))
WIRE = os.environ.get("WIRE_SRC", os.path.join(SRC, "scaffold_wire.py"))
sw = load("scaffold_wire", WIRE)
RAW = open(os.path.join(HERE, "..", "fixtures", "mesh_registry_v0_3.json"), encoding="utf-8").read()
SHA = hashlib.sha256(RAW.encode()).hexdigest()
class AccessError(Exception): pass
class Rec:
    def __init__(s, body=RAW, sha=SHA, version="0.3.5", state="candidate"): s.body, s.sha, s.version, s.state = body, sha, version, state
    def __bool__(s): return True
class Model:
    def __init__(s, rec, raise_access=False, log=None): s.rec, s.ra, s.log = rec, raise_access, log if log is not None else []
    def search(s, domain, order=None, limit=None):
        s.log.append(("search", tuple(map(tuple, domain)), order, limit))
        if s.ra: raise AccessError("no read")
        return s.rec if s.rec is not None else []
    def sudo(s): raise AssertionError("sudo must never be called")
class User:
    def __init__(s, groups): s.id = 7; s.g = set(groups)
    def has_group(s, x): return x in s.g
class Env:
    def __init__(s, groups, rec=None, ra=False): s.user = User(groups); s.log = []; s.m = Model(rec if rec is not None else Rec(), ra, s.log)
    def __getitem__(s, k): assert k == "synapsys.mesh.registry", k; return s.m
    def sudo(s): raise AssertionError("env.sudo must never be called")
STEW, COLL = "synapsys.group_synapsys_steward", "synapsys.group_synapsys_user"
class T(unittest.TestCase):
    def test_W1_steward_enrich_sees_roles_and_hold_peers(self):
        o = sw.scaffold_context(Env([STEW, COLL]), "enrich", "CTX-A")
        self.assertEqual(o["result"], "OK"); self.assertEqual(o["depth_effective"], "enrich"); self.assertEqual(len(o["roles"]), 7)
        self.assertEqual(o["registry_sha"], SHA); self.assertEqual(o["registry_version"], "0.3.5")
        for p in o["peers"]: self.assertEqual(p["operating_source"], "NO_OPERATING_SOURCE"); self.assertTrue(p["hold"])
    def test_W2_collaborator_capped_at_enhance(self):
        o = sw.scaffold_context(Env([COLL]), "enrich", "CTX-A")
        self.assertEqual((o["depth_effective"], o["depth_clamped"]), ("enhance", True))
        self.assertNotIn("definition_source", o); self.assertNotIn("evidence", o["peers"][0])
    def test_W3_no_group_refused_before_any_read(self):
        e = Env([]); o = sw.scaffold_context(e, "enable"); self.assertEqual(o["reason"], "NO_RECOGNISED_ROLE"); self.assertEqual(e.log, [])
    def test_W4_no_registry_read_right_refused_no_fallback(self):
        o = sw.scaffold_context(Env([COLL], ra=True), "enable"); self.assertEqual(o, {"result": "REFUSED", "reason": "NO_REGISTRY_READ_RIGHT"})
    def test_W5_tampered_body_refused(self):
        o = sw.scaffold_context(Env([STEW], rec=Rec(body=RAW.replace('"Context"', '"Kontext"', 1))), "enable")
        self.assertEqual(o["reason"], "REGISTRY_BODY_HASH_MISMATCH")
    def test_W6_missing_registry(self):
        e = Env([STEW]); e.m.rec = None; self.assertEqual(sw.scaffold_context(e, "enable")["reason"], "REGISTRY_NOT_FOUND")
    def test_W7_bad_depth_refused(self):
        self.assertEqual(sw.scaffold_context(Env([STEW]), "deep")["reason"], "UNKNOWN_DEPTH")
    def test_W8_read_only_calls_only(self):
        e = Env([STEW]); sw.scaffold_context(e, "enhance"); self.assertEqual([x[0] for x in e.log], ["search"])
    def test_W9_source_has_no_sudo_write_or_raw_sql(self):
        for f in ("scaffold_wire.py", "scaffold_controller.py", "scaffold_lens.py"):
            code = re.sub(r'""".*?"""', "", open(os.path.join(SRC, f), encoding="utf-8").read(), flags=re.S)
            code = "\n".join(l.split("#")[0] for l in code.splitlines())
            for bad in (r"\bsudo\b", r"with_user", r"\bsu\s*=", r"\.write\(", r"\.create\(", r"\.unlink\(", r"cr\.execute", r"\bexecute\("):
                self.assertIsNone(re.search(bad, code), (f, bad))
    def test_W10_controller_is_user_authenticated_and_uses_request_env(self):
        c = open(os.path.join(SRC, "scaffold_controller.py"), encoding="utf-8").read()
        self.assertIn("auth='user'", c); self.assertIn("request.env", c); self.assertNotIn("auth='public'", c); self.assertNotIn("auth='none'", c)
    def test_W11_stable_across_calls_no_state(self):
        a = sw.scaffold_context(Env([STEW]), "enrich", "C"); b = sw.scaffold_context(Env([STEW]), "enrich", "C"); self.assertEqual(a, b)
if __name__ == "__main__": unittest.main(verbosity=2)
