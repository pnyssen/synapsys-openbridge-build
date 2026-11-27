"""RC06i offline tests (renderer level; the layout proof is tests/test_layout_browser.py, a real browser). No Odoo, no network, no writes."""
import hashlib, html, json, os, re, unittest

import fakes as F
import fakes_core as F0
from fakes import sd, sr, sw
from test_batch5 import E5, BOUND, UNBOUND, BY_MENU, DECLS, text

HERE = os.path.dirname(os.path.abspath(__file__))
D = ("enable", "enhance", "enrich")
SVC = [b for b in BOUND if b["screen_id"] == "SCR.SERVICE.NOUN"][0]
MEA = [b for b in BOUND if b["screen_id"] == "SCR.MESH_MEASURES.MENU"][0]
FIXED = {  # every fixed UI chrome string of RC06i (contract: list them all in the return)
    "Detail", "Enable", "Enhance", "Enrich", "Form", "Flow", "Evolve", "Value", "Records",
    "SynapSys: definition and alignment", "Disciplines: operation and movement", "Mesh: evidence, learning and value realisation",
    "Definition source: registry ", "No registry source is declared for this screen.", "Trust: ",
    "Definition of the value chain, from the Service Catalogue Master Reference v1.3. It is not a record of this Service.",
    "Service performance", "Outcome", "Verified Benefit contribution", "Realisation", "Enduring Asset effect",
    "Benefits and Assets recorded against this Service are not read on this screen.",
    "Observations: not available on this screen. No stored measure is read here; the native list under Records shows what exists.", "Owner: none declared on this screen.",
    "Claim", "Status", "Source", "Open question", "Detail level", "Binding: ", "Presentation only: this view changes no data, kind, PPV, approval or right.",
}


def page(b, d, **kw):
    return sw.menu_enable(E5([F0.STEW], **kw), b["action_id"], b["menu_id"], b["screen_id"], d)


class I1_DetailControl(unittest.TestCase):
    def test_every_bound_page_has_exactly_one_server_rendered_accessible_control_at_every_depth(self):
        for b in BOUND:
            for d in D:
                h = page(b, d)["html"]
                self.assertEqual(h.count('data-control="detail"'), 1, (b["menu_name"], d))
                self.assertIn('role="group" aria-label="Detail level"', h)
                self.assertEqual(re.findall(r'data-mode="(\w+)" aria-pressed="(\w+)"', h), [(x, "true" if x == d else "false") for x in D], (b["menu_name"], d))
                self.assertNotIn("syn-modebar", h)

    def test_the_control_sits_inside_the_answer_band_of_the_service_page_and_after_the_answer_elsewhere(self):
        for d in D:
            h = page(SVC, d)["html"]
            band = re.search(r'<section class="sv-band sv-answer".*?</section>', h, re.S).group(0)
            self.assertIn('data-control="detail"', band); self.assertIn('data-slot="answer"', band)
        for b in BOUND:
            if b is SVC:
                continue
            h = page(b, "enable")["html"]
            self.assertLess(h.index('data-slot="answer"'), h.index('data-control="detail"'))

    def test_the_client_template_no_longer_carries_a_modebar_and_the_service_is_the_only_depth_state(self):
        xml = open(os.path.join(F.ADDON, "static", "src", "enable_panel.xml"), encoding="utf-8").read()
        js = open(os.path.join(F.ADDON, "static", "src", "enable_panel.js"), encoding="utf-8").read()
        self.assertNotIn("modebar", xml); self.assertNotIn("this.state.mode", js); self.assertNotIn("localStorage", js)
        self.assertIn("synapsys_lens_mode", js)  # the one shared depth state


class I2_ServiceProjection(unittest.TestCase):
    def test_only_the_service_screen_gets_the_projection(self):
        for b in BOUND:
            h = page(b, "enable")["html"]
            self.assertEqual('data-projection="service-1-3-1"' in h, b is SVC, b["menu_name"])
            self.assertEqual('data-band="value"' in h, b is SVC, b["menu_name"])
        self.assertEqual((SVC["menu_id"], SVC["action_id"]), (200, 297))

    def test_answer_band_apertures_value_band_records_in_that_order_at_every_depth(self):
        for d in D:
            h = page(SVC, d)["html"]
            body = h[h.index('<div class="syn-sc syn-pg'):]  # after the style block
            pos = [body.index(x) for x in ('data-band="answer"', 'data-aperture="form"', 'data-aperture="flow"', 'data-aperture="evolve"', 'data-band="value"', 'data-slot="records"')]
            self.assertEqual(pos, sorted(pos), d)
            self.assertEqual(h.count("<h1>"), 1)

    def test_depth_adds_slots_only_inside_the_apertures_and_the_value_band_is_always_there(self):
        got = {d: page(SVC, d)["html"] for d in D}
        for d in D:
            self.assertIn('data-band="value"', got[d])
        self.assertNotIn('data-slot="made_of"', got["enable"]); self.assertIn('data-slot="made_of"', got["enhance"])
        form = re.search(r'data-aperture="form".*?</section>', got["enhance"], re.S).group(0); self.assertIn('data-slot="made_of"', form)
        flow = re.search(r'data-aperture="flow".*?</section>', got["enhance"], re.S).group(0); self.assertIn('data-slot="peers"', flow); self.assertIn('data-slot="movement"', flow)
        ev = re.search(r'data-aperture="evolve".*?</section>\s*</div>', got["enrich"], re.S).group(0)
        for s in ("open_questions", "trust_table", "technical"):
            self.assertIn('data-slot="%s"' % s, ev)
            self.assertNotIn('data-slot="%s"' % s, got["enhance"])

    def test_ffe_is_a_perspective_grouping_nothing_is_inferred_as_a_stage_or_state(self):
        for d in D:
            h = page(SVC, d)["html"]
            self.assertNotIn("x_ffe_state", h); self.assertNotIn("Stage:", h)
            self.assertEqual(re.findall(r"<h2>(Form|Flow|Evolve|Value)</h2>", h), ["Form", "Flow", "Evolve", "Value"])

    def test_a_slot_without_a_source_says_so_and_nothing_is_filled(self):
        h = page(SVC, "enhance")["html"]
        self.assertIn("No linked peers are declared for this screen.", h)
        o = sw.menu_enable(E5([F0.STEW], ref_ids=None), SVC["action_id"], 200, "", "enable")
        m = copy_model = None
        out = {"result": "OK", "screen": "SCR.SERVICE.NOUN", "screen_type": "noun", "depth_effective": "enable", "slots": ["header", "answer", "trust", "movement"],
               "frame": {"header": {"noun": "Service", "status": "RULED"}, "answer": "x", "trust": {"status": "RULED", "source_count": 1}, "movement": {"state": "HOLD", "text": "t", "reason": "r", "verbs": []}}}
        self.assertIn("No registry source is declared for this screen.", sr.render_menu_page(out))  # no registry on the model: stated, not invented

    def test_value_band_is_a_labelled_definition_and_one_honest_statement_with_no_numbers(self):
        for d in D:
            h = page(SVC, d)["html"]
            band = re.search(r'<section class="sv-band sv-value".*?</section>', h, re.S).group(0)
            t = text(band)
            self.assertIn("Definition of the value chain, from the Service Catalogue Master Reference v1.3", t)
            self.assertEqual(re.findall(r"<li>(.*?)</li>", band), ["Service performance", "Outcome", "Verified Benefit contribution", "Realisation", "Enduring Asset effect"])
            self.assertEqual(t.count("not read on this screen"), 1)       # one statement, not five repeated placeholders
            self.assertIsNone(re.search(r"\d", re.sub(r"v1\.3", "", t)), t)  # no counts, no V19 numbers (34 / 29)
            self.assertNotIn("No source declared", t); self.assertNotIn("none exist", t)  # and no claim that the world has none
            self.assertNotRegex(t, r"\b(34|29)\b")


class I3_TypographyAndWrap(unittest.TestCase):
    def test_service_style_sets_only_14_12_10_and_the_old_specimen_sizes_are_gone(self):
        css = sr.SERVICE_STYLE
        sizes = set(re.findall(r"font-size:(\d+)px", css))
        self.assertEqual(sizes, {"14", "12", "10"})
        for old in ("22px", "15px", "17px"):
            self.assertNotIn("font-size:" + old, css)

    def test_other_screens_keep_their_type_and_context_css_is_untouched(self):
        self.assertNotIn("SERVICE_STYLE", sr.render_screen.__code__.co_names)
        h = page(MEA, "enable")["html"]; self.assertNotIn(".syn-sv", h)  # the 14 / 12 / 10 rules travel with the Service page only
        self.assertIn(".syn-sc h1{font-size:24px", sr.STYLE)

    def test_wrap_rules_apply_to_every_menu_page_and_the_trust_table_is_stacked_with_source_on_a_phone(self):
        css = sr.PAGE_STYLE
        self.assertIn(".syn-sc.syn-pg table.tt td>div{white-space:normal;overflow:visible;text-overflow:clip;overflow-wrap:anywhere}", css)
        self.assertIn('.syn-sc.syn-pg .tt td:nth-child(3)::before{content:"Source"}', css)
        self.assertIn(".syn-sc.syn-pg .tt td,.syn-sc.syn-pg .tt td:nth-child(3){display:block;border-top:0;padding:2px 8px}", css)  # Source is shown, not hidden, at 600 px and below
        for b in BOUND:
            self.assertIn(css, page(b, "enrich")["html"], b["menu_name"])


class I4_Measures(unittest.TestCase):
    def test_measures_states_its_purpose_that_observations_are_not_here_the_owner_hold_and_status(self):
        for d in D:
            h = page(MEA, d)["html"]
            t = text(h)
            self.assertIn("A measure stored by Mesh address", t)                      # technical purpose: the source row's own words
            self.assertIn("Observations: not available on this screen.", t)
            self.assertIn("Owner: none declared on this screen.", t)
            self.assertIn("HOLD", t); self.assertIn("noun-to-verb governance waits on the Architecture tab", t)  # the declared route
            self.assertIn('<span class="tg">CANDIDATE</span>', h); self.assertNotIn('class="lead"', h)
            self.assertNotRegex(re.sub(r"v1\.3", "", re.sub(r"<style>.*?</style>", "", h, flags=re.S)).split('data-slot="measures_scope"')[1].split("</div>")[0], r"\d")  # no count, no figure
            self.assertNotIn("<svg", h); self.assertNotIn("<canvas", h)                # no chart

    def test_measures_native_model_and_action_are_preserved(self):
        self.assertEqual(MEA["native"]["model"], "synapsys.mesh.measure"); self.assertEqual(MEA["action_id"], 189)


class I5_NoNewReadRouteSchemaOrMenu(unittest.TestCase):
    def test_file_level_diff_against_rc06h_only_the_renderer_and_the_client_panel_changed(self):
        base = json.load(open(os.path.join(HERE, "golden", "rc06h_tree_manifest.json"), encoding="utf-8"))["files"]
        now = {}
        for root, _d, fs in os.walk(F.ADDON):
            for f in fs:
                if "__pycache__" in root or f.endswith(".pyc"):
                    continue
                p = os.path.join(root, f)
                now[os.path.relpath(p, F.ADDON)] = hashlib.sha256(open(p, "rb").read()).hexdigest()
        self.assertEqual((set(now) - set(base), set(base) - set(now)), (set(), set()))
        changed = {k for k in base if now[k] != base[k]}
        self.assertEqual(changed, {"screen_render.py", "static/src/enable_panel.js", "static/src/enable_panel.xml"})
        for rel in ("scaffold_wire.py", "controllers/menu_binding.py", "controllers/__init__.py", "screen_binding.py", "__manifest__.py", "views/synapsys_menus.xml",
                    "views/synapsys_views.xml", "security/ir.access.csv", "data/screen_bindings_batch5.json", "data/screen_declarations.json"):
            self.assertEqual(now[rel], base[rel], rel)  # no new read (the wire is byte-identical), route, schema, menu, ACL or declaration
        self.assertEqual(len(now), 69)

    def test_the_service_and_measures_pages_make_only_the_reads_the_rc06h_pages_made(self):
        for b in (SVC, MEA):
            for d in D:
                e = E5([F0.STEW]); sw.menu_enable(e, b["action_id"], b["menu_id"], b["screen_id"], d)
                for call in e.log:
                    self.assertIn(call[0], ("check_access", "ref", "menu_search", "search", "search_cat"), call)
        e = E5([F0.STEW]); sw.menu_enable(e, MEA["action_id"], MEA["menu_id"], MEA["screen_id"], "enrich")
        self.assertEqual([c for c in e.log if c[0] in ("search", "search_cat")], [])  # Measures: neither registry nor catalogue nor any count

    def test_refusals_unchanged_and_the_8_unbound_menus_untouched(self):
        self.assertEqual(sw.menu_enable(E5([]), 297, 200, "", "enable"), {"result": "REFUSED", "reason": "NO_RECOGNISED_ROLE"})
        self.assertEqual(sw.menu_enable(E5([F0.STEW], readable=False), 297, 200, "", "enrich"), {"result": "REFUSED", "reason": "NO_READ_RIGHT"})
        self.assertEqual(sw.menu_enable(E5([F0.STEW]), 297, 999, "", "enable"), {"result": "REFUSED", "reason": "ANCHOR_MISMATCH"})
        for r in UNBOUND:
            self.assertEqual(sw.menu_enable(E5([F0.STEW]), r["action_id"], r["menu_id"], "", "enable"), {"result": "REFUSED", "reason": "MENU_NOT_BOUND"})
        self.assertEqual((len(BOUND), len(UNBOUND)), (43, 8))


class I6_FixedStrings(unittest.TestCase):
    def test_every_fixed_ui_string_is_in_the_documented_list_and_no_other_service_prose_exists(self):
        import ast
        tree = ast.parse(open(os.path.join(F.ADDON, "screen_render.py"), encoding="utf-8").read())
        fn = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name in ("render_service_page", "_form_line", "_evolve_line", "_service_header", "_measures_scope", "detail_control")]
        docs = {id(f.body[0].value) for f in fn if isinstance(f.body[0], ast.Expr)}
        lits = {c.value for f in fn for c in ast.walk(f) if isinstance(c, ast.Constant) and isinstance(c.value, str) and id(c) not in docs}
        prose = {l for l in lits if len(l) > 24 and not l.startswith("<") and "data-" not in l and "%" not in l[:3]}
        for l in prose:
            self.assertTrue(any(l.startswith(f) or f in l for f in FIXED), l)
        chain = [x for x in sr.VALUE_CHAIN]
        self.assertEqual(chain, ["Service performance", "Outcome", "Verified Benefit contribution", "Realisation", "Enduring Asset effect"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
