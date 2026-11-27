import importlib.util, json, os, re, shutil, subprocess, sys, tempfile, types, unittest
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
SRC = os.path.join(ROOT, "src"); sys.path.insert(0, SRC)
import scaffold_lens as sl, scaffold_wire as sw
VIEW = os.environ.get("VIEW_SRC", os.path.join(SRC, "scaffold_view.py"))
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m; spec.loader.exec_module(m); return m
sv = load("scaffold_view", VIEW)
HOMEJS = os.environ.get("HOMEJS", os.path.join(ROOT, "patched", "home.js"))
LENSES = os.environ.get("LENSESPY", os.path.join(ROOT, "patched", "lenses.py"))
REG = json.load(open(os.path.join(ROOT, "fixtures", "mesh_registry_v0_3.json"), encoding="utf-8"))
def out(depth, groups=("steward",), tweak=None):
    reg = json.loads(json.dumps(REG))
    if tweak: tweak(reg)
    o = sl.build_scaffold(reg, "N.CONTEXT", depth, {"groups": set(groups)}, [], {}, "1", sw.DEFAULT_ROLE_MAX_DEPTH)
    o["registry_state"] = "candidate"; return o
class V(unittest.TestCase):
    def test_V1_enable_shows_headline_only(self):
        h = sv.render(out("enable"), "enable"); self.assertIn("Context", h); self.assertNotIn("Roles in a Context", h); self.assertNotIn("Linked peers", h)
    def test_V2_enhance_roles_required_first_and_peers_hold(self):
        h = sv.render(out("enhance"), "enhance"); self.assertIn("Roles in a Context", h)
        self.assertLess(h.index("required"), h.index("optional")); self.assertEqual(h.count("NO OPERATING SOURCE: HOLD"), 2)
        self.assertNotIn("Definition source", h)
    def test_V3_enrich_provenance_and_questions(self):
        h = sv.render(out("enrich"), "enrich"); self.assertIn("Provenance", h); self.assertIn("Open questions", h); self.assertIn("Definition source", h)
    def test_V4_every_dynamic_value_is_escaped(self):
        def t(reg):
            for e in reg["elements"]:
                if e["id"] in ("N.CONTEXT", "N.SERVICE"): e["definition"] = '<script>alert(1)</script>"><img src=x onerror=alert(2)>'; e["label"] = "<b>x</b>"
        h = sv.render(out("enrich", tweak=t), "enrich")
        self.assertNotIn("<script", h); self.assertNotIn("<img", h); self.assertNotIn("<b>x", h); self.assertIn("&lt;script&gt;", h)
    def test_V5_no_scripts_handlers_or_external_urls(self):
        h = sv.render(out("enrich"), "enrich")
        self.assertIsNone(re.search(r"<script|\son[a-z]+=|https?://|javascript:", h, re.I))
    def test_V6_refused_and_garbage_render_a_message_not_an_error(self):
        for o in ({"result": "REFUSED", "reason": "NO_RECOGNISED_ROLE"}, None, {"x": 1}, "str"):
            h = sv.render(o); self.assertIn("Not available", h); self.assertIn("data-lv", h)
    def test_V7_mobile_rules_present(self):
        h = sv.render(out("enhance"), "enhance"); self.assertIn("@media (max-width:600px)", h); self.assertIn("min-height:44px", h)
        self.assertNotIn("min-width:3", h.replace("min-width:30%", ""))  # no fixed wide widths besides the 30% label column
    def test_V8_clamp_is_explained(self):
        o = sl.build_scaffold(REG, "N.CONTEXT", "enrich", {"groups": {"client"}}, [], {}, "1"); o["registry_state"] = "candidate"
        self.assertIn("limits the depth", sv.render(o, "enrich"))
    def test_V9_presentation_only_statement_always_present(self):
        for d in sl.DEPTHS: self.assertIn("changes no data", sv.render(out(d), d))
    def test_V11_lists_in_value_column_are_left_aligned(self):
        self.assertIn(".syn-sc .kv ul{margin:0;text-align:left}", sv.render(out("enrich"), "enrich"))
    def test_V10_empty_open_questions_say_none(self):
        def t(reg):
            for e in reg["elements"]:
                if e["id"] == "N.CONTEXT": e["open_questions"] = []
        self.assertIn("none recorded", sv.render(out("enrich", tweak=t), "enrich"))

HARNESS = r"""
const fs = require('fs');
let src = fs.readFileSync(process.argv[2], 'utf8');
src = src.replace(/^import .*$/mg, '').replace(/^export /mg, '');
const calls = [];
const registry = { category: () => ({ add: () => {} }) };
const rpc = async (u, p) => { calls.push([u, JSON.parse(JSON.stringify(p))]); return '<p>' + u + '</p>'; };
class Component {}
const onWillStart = () => {}, onWillDestroy = () => {}, proxy = (x) => x, markup = (x) => x;
let subs = [];
const lm = { mode: 'enhance', overrides: '', subscribe: (f) => { subs.push(f); return () => {}; }, setMode(m) { this.mode = m; subs.forEach(f => f()); }, setOverride() {} };
const useService = () => lm;
const body = src + '\nreturn { SynapsysLenses };';
const { SynapsysLenses } = new Function('registry','rpc','Component','onWillStart','onWillDestroy','proxy','markup','useService', body)(registry, rpc, Component, onWillStart, onWillDestroy, proxy, markup, useService);
const c = new SynapsysLenses(); c.setup();
const el = (attrs, dataset) => ({ target: { closest: (sel) => (attrs.includes(sel) ? { dataset } : null) }, preventDefault() { this.p = true; } });
(async () => {
  const r = {};
  const ev1 = el(['[data-scaffold]'], {}); c.onClick(ev1); await new Promise(r => setTimeout(r, 5));
  r.scaffold_click = calls.slice(); r.prevented = ev1.p === true; r.state1 = c.state.html;
  lm.setMode('enrich'); await new Promise(r => setTimeout(r, 5)); r.after_depth = calls.slice(-1)[0];
  const ev2 = el(['[data-lv]'], { lv: '1', g: '' }); c.onClick(ev2); await new Promise(r => setTimeout(r, 5)); r.back = calls.slice(-1)[0];
  lm.setMode('enable'); await new Promise(r => setTimeout(r, 5)); r.after_back_depth = calls.slice(-1)[0];
  const ev3 = el(['[data-lv]'], { lv: '2', g: 'pattern', s: '' }); c.onClick(ev3); await new Promise(r => setTimeout(r, 5)); r.level2 = calls.slice(-1)[0];
  const ev4 = el([], {}); c.onClick(ev4); r.noop = ev4.p !== true;
  console.log(JSON.stringify(r));
})();
"""
class J(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        f = tempfile.NamedTemporaryFile("w", suffix=".js", delete=False); f.write(HARNESS); f.close()
        p = subprocess.run(["node", f.name, HOMEJS], capture_output=True, text=True, timeout=30)
        os.unlink(f.name); assert p.returncode == 0, p.stderr; cls.r = json.loads(p.stdout)
    def test_J1_click_loads_scaffold_view_with_current_depth(self):
        self.assertEqual(self.r["scaffold_click"][-1], ["/synapsys/scaffold/view", {"depth": "enhance"}]); self.assertTrue(self.r["prevented"])
    def test_J2_depth_change_reloads_the_scaffold_view(self):
        self.assertEqual(self.r["after_depth"], ["/synapsys/scaffold/view", {"depth": "enrich"}])
    def test_J3_back_link_returns_to_the_normal_lenses_data(self):
        self.assertEqual(self.r["back"][0], "/synapsys/lenses/data"); self.assertEqual(self.r["back"][1]["level"], 1)
    def test_J4_after_back_depth_change_stays_on_lenses(self):
        self.assertEqual(self.r["after_back_depth"][0], "/synapsys/lenses/data")
    def test_J5_existing_level2_navigation_unchanged(self):
        self.assertEqual(self.r["level2"][0], "/synapsys/lenses/data"); self.assertEqual((self.r["level2"][1]["level"], self.r["level2"][1]["group"]), (2, "pattern"))
    def test_J6_unrelated_click_is_ignored(self):
        self.assertTrue(self.r["noop"])

class L(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        odoo = types.ModuleType("odoo"); h = types.ModuleType("odoo.http")
        class Controller: pass
        h.Controller = Controller; h.route = lambda *a, **k: (lambda f: f)
        class Req: env = None
        h.request = Req; odoo.http = h
        addons = types.ModuleType("odoo.addons"); syn = types.ModuleType("odoo.addons.synapsys")
        lr = types.ModuleType("odoo.addons.synapsys.lens_render"); lc = types.ModuleType("odoo.addons.synapsys.lens_contract")
        lr.STAGES = {"Form": ("a",)}; lr.render = lambda level, g, s, live, verbs: "<div>L%d</div>" % level; lr.lenses_for = lambda g, s: []
        lc.parse_overrides = lambda ov: {}; lc.render_element = lambda *a: ""; lc.from_lens = lambda l: {}
        syn.lens_render = lr; syn.lens_contract = lc; odoo.addons = addons; addons.synapsys = syn
        for k, v in {"odoo": odoo, "odoo.http": h, "odoo.addons": addons, "odoo.addons.synapsys": syn,
                     "odoo.addons.synapsys.lens_render": lr, "odoo.addons.synapsys.lens_contract": lc}.items(): sys.modules[k] = v
        cls.m = load("lenses_ctl", LENSES); cls.Req = Req
    def env(self, steward):
        class Rs:
            def search_count(s, d): return 1
            def search(s, d, order=None):
                class X:
                    def mapped(s2, f): return ["v"]
                return X()
        class U:
            def has_group(s, x): return steward and x == "synapsys.group_synapsys_steward"
        class E(dict):
            user = U()
        e = E(); e["synapsys.mesh.entry"] = Rs(); e["synapsys.verb"] = Rs(); return e
    def call(self, steward, level):
        self.Req.env = self.env(steward); return self.m.SynapsysLenses().lenses_data(level=level)
    def test_L1_steward_sees_scaffold_link_at_level1(self): self.assertIn('data-scaffold="1"', self.call(True, 1))
    def test_L5_link_card_has_no_extra_page_padding(self): self.assertIn("padding-top:0", self.call(True, 1))
    def test_L2_non_steward_never_sees_it(self): self.assertNotIn("data-scaffold", self.call(False, 1))
    def test_L3_other_levels_unchanged(self):
        for lv in (2, 3): self.assertNotIn("data-scaffold", self.call(True, lv))
    def test_L4_no_sudo_or_write_in_patched_lenses(self):
        code = open(LENSES, encoding="utf-8").read(); self.assertIsNone(re.search(r"sudo|\.write\(|\.create\(|\.unlink\(", code))
if __name__ == "__main__": unittest.main(verbosity=2)
