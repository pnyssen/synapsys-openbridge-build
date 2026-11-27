"""RC06h offline tests: bound menu pages use the lens template (three Depth tabs, definition on top, Records heading, wrapping table, answer prefix).
Offline only: no Odoo, no network, no writes. What these tests CANNOT show: how the page looks and where it sits in Odoo 20 at 390 and 1024 px (the
placement rests on CSS flex order of the web client's own containers, which is unverified here), and role behaviour on a real database."""
import copy, html, json, os, re, unittest

import fakes as F
import fakes_core as F0
import rc06h_compat
from fakes import sl, sd, sr, sw
from test_batch5 import E5, BOUND, UNBOUND, BY_MENU, DECLS, text

PAGE_DEPTHS = ("enable", "enhance", "enrich")


def page(b, depth, groups=None, **kw):
    return sw.menu_enable(E5(groups or [F0.STEW], **kw), b["action_id"], b["menu_id"], b["screen_id"], depth)


class H1_ThreeTabsAndDepths(unittest.TestCase):
    def test_every_bound_menu_serves_enable_enhance_and_enrich_as_the_same_page_frame(self):
        for b in BOUND:
            for d in PAGE_DEPTHS:
                r = page(b, d)
                self.assertEqual(r["result"], "OK", (b["menu_name"], d))
                self.assertEqual(r["depth"], d)
                h = r["html"]
                self.assertEqual(re.findall(r'data-slot="(header|answer|trust|movement)"', h), ["header", "answer", "trust", "movement"], (b["menu_name"], d))
                self.assertIn('data-depth="%s"' % d, h)
                if b["screen_id"] != "SCR.SERVICE.NOUN":  # RC06i: the Service projection states depth in its Detail control only
                    self.assertIn("Depth: %s" % d.capitalize(), h)
                self.assertEqual(h.count('data-slot="records"'), 1); self.assertTrue(h.rstrip().endswith('Records</h2></div>'))
                self.assertNotIn("<script", h); self.assertNotIn('class="bk"', h)

    def test_enable_has_only_the_frame_enhance_adds_made_of_and_peers_enrich_adds_trust_table_open_questions_technical(self):
        for b in BOUND:
            got = {d: re.findall(r'data-slot="(\w+)"', page(b, d)["html"]) for d in PAGE_DEPTHS}
            if b["screen_id"] == "SCR.SERVICE.NOUN":  # RC06i: Form holds made_of, Flow holds movement and peers, Evolve holds the trust material, the Value band always
                self.assertEqual(got["enable"], ["header", "answer", "trust", "movement", "value_definition", "value_records", "binding", "records"])
                self.assertEqual(got["enhance"], ["header", "answer", "trust", "made_of", "movement", "peers", "value_definition", "value_records", "binding", "records"])
                self.assertEqual(got["enrich"], ["header", "answer", "trust", "made_of", "movement", "peers", "open_questions", "trust_table", "technical", "value_definition", "value_records", "binding", "records"])
                continue
            extra = ["measures_scope"] if b["screen_id"] == "SCR.MESH_MEASURES.MENU" else []
            self.assertEqual(got["enable"], ["header", "answer", "trust", "movement"] + extra + ["binding", "records"], b["menu_name"])
            self.assertEqual(got["enhance"], ["header", "answer", "trust", "movement"] + extra + ["made_of", "peers", "binding", "records"], b["menu_name"])
            self.assertEqual(got["enrich"], ["header", "answer", "trust", "movement"] + extra + ["made_of", "peers", "trust_table", "open_questions", "technical", "binding", "records"], b["menu_name"])

    def test_enhance_and_enrich_show_the_declarations_own_content_and_say_plainly_when_it_has_none(self):
        plain_made, plain_peers = [], []
        for b in BOUND:
            d = DECLS[b["screen_id"]]
            enh = page(b, "enhance")["html"]
            if d.get("made_of"):
                self.assertNotIn(sr.NO_ROLES, enh, b["menu_name"])
            else:
                self.assertIn(sr.NO_ROLES, enh, b["menu_name"]); plain_made.append(b["screen_id"])
            if d.get("peers"):
                self.assertNotIn("No linked peers are declared for this screen.", enh, b["menu_name"])
            else:
                self.assertIn("No linked peers are declared for this screen.", enh, b["menu_name"]); plain_peers.append(b["screen_id"])
            if d["screen_type"] == "menu" and d.get("made_of"):
                src = sd._menu_sources(d)
                for r in d["made_of"]["rows"]:
                    self.assertIn(html.escape(src[r]["display"], quote=True), enh.replace("&#x27;", "&#x27;"), (b["menu_name"], r))  # the row's own words, not invented
            en = page(b, "enrich")["html"]
            for c in d["claims"]:
                self.assertIn('data-claim="%s"' % c["id"], en, (b["menu_name"], c["id"]))
            self.assertEqual(len(re.findall(r'<tr data-claim=', en)), len(d["claims"]), b["menu_name"])
        self.assertTrue(plain_made or plain_peers)  # at least some screens carry none, and they say so

    def test_context_menu_page_is_the_context_specimen_content_with_the_made_of_and_peers_of_the_declaration(self):
        b = BY_MENU[188]
        enh = page(b, "enhance")["html"]
        for role in ("Purpose", "Rights holder", "Strategies"):
            self.assertIn(role, enh)
        self.assertIn("Linked peers", enh)

    def test_page_is_the_same_visible_text_as_the_screen_itself_at_each_depth_apart_from_chrome(self):
        for b in BOUND:
            d = DECLS[b["screen_id"]]
            for depth in PAGE_DEPTHS:
                r = page(b, depth)
                direct = (sw.scaffold_menu(F.Env([F.STEW]), b["screen_id"], depth) if d["screen_type"] == "menu" else
                          (sw.scaffold_context(F.Env([F.STEW]), depth, "") if b["screen_id"] == "SCR.CONTEXT.NOUN" else sw.scaffold_noun(F.Env([F.STEW]), b["screen_id"], depth, "")))
                self.assertEqual(r["status"], direct["status"], (b["menu_name"], depth))
                for slot in direct["slots"]:
                    if slot in ("made_of", "peers", "trust_table", "open_questions"):
                        self.assertIn('data-slot="%s"' % slot, r["html"], (b["menu_name"], depth, slot))


class H2_Entitlement(unittest.TestCase):
    def test_enhance_and_enrich_are_refused_without_a_role_or_without_the_real_read_right_and_read_nothing_else_first(self):
        for b in BOUND:
            for depth in ("enhance", "enrich"):
                e = E5([], readable=True)
                self.assertEqual(sw.menu_enable(e, b["action_id"], b["menu_id"], b["screen_id"], depth), {"result": "REFUSED", "reason": "NO_RECOGNISED_ROLE"})
                self.assertEqual(e.log, [])
                e = E5([F0.STEW], readable=False)
                self.assertEqual(sw.menu_enable(e, b["action_id"], b["menu_id"], b["screen_id"], depth), {"result": "REFUSED", "reason": "NO_READ_RIGHT"}, (b["menu_name"], depth))
                self.assertEqual([x[0] for x in e.log], ["check_access"])  # no registry, catalogue, menu or declaration read before entitlement

    def test_anchor_refusals_hold_at_every_depth_and_the_8_unbound_menus_are_untouched(self):
        b = BY_MENU[200]
        for depth in PAGE_DEPTHS:
            self.assertEqual(sw.menu_enable(E5([F0.STEW]), b["action_id"], 999, b["screen_id"], depth)["reason"], "ANCHOR_MISMATCH")
            self.assertEqual(sw.menu_enable(E5([F0.STEW], menu_visible=False), b["action_id"], b["menu_id"], b["screen_id"], depth)["reason"], "MENU_NOT_VISIBLE")
            self.assertEqual(sw.menu_enable(E5([F0.STEW]), b["action_id"], b["menu_id"], "SCR.PROJECT.NOUN", depth)["reason"], "SCREEN_NOT_BOUND_TO_MENU")
            for r in UNBOUND:
                e = E5([F0.STEW])
                self.assertEqual(sw.menu_enable(e, r["action_id"], r["menu_id"], "", depth), {"result": "REFUSED", "reason": "MENU_NOT_BOUND"}, r["menu_name"])
                self.assertEqual([x for x in e.log if x[0] != "check_access"], [])
        self.assertEqual(len(UNBOUND), 8)

    def test_the_role_depth_cap_applies_on_the_page_and_the_page_says_so(self):
        b = BY_MENU[200]
        old = dict(sw.DEFAULT_ROLE_MAX_DEPTH)
        try:
            sw.DEFAULT_ROLE_MAX_DEPTH['collaborator'] = 'enable'
            r = page(b, "enrich", [F0.COLL])
            self.assertEqual(r["depth"], "enable")
            self.assertIn("Your role limits the depth to Enable.", r["html"]); self.assertNotIn('data-slot="trust_table"', r["html"])
            r = page(b, "enrich", [F0.STEW]); self.assertEqual(r["depth"], "enrich")  # the steward cap is untouched
        finally:
            sw.DEFAULT_ROLE_MAX_DEPTH.clear(); sw.DEFAULT_ROLE_MAX_DEPTH.update(old)
        self.assertEqual(sw.DEFAULT_ROLE_MAX_DEPTH, {'steward': 'enrich', 'collaborator': 'enrich'})
        self.assertEqual(page(b, "enrich", [F0.COLL])["depth"], "enrich")  # as installed

    def test_no_writes_and_only_reads_at_every_depth(self):
        for b in BOUND:
            for d in PAGE_DEPTHS:
                e = E5([F0.STEW]); sw.menu_enable(e, b["action_id"], b["menu_id"], b["screen_id"], d)
                for call in e.log:
                    self.assertIn(call[0], ("check_access", "ref", "menu_search", "search", "search_cat"), call)


class H3_LayoutRules(unittest.TestCase):
    CSS = sr.PAGE_STYLE

    def test_the_page_is_ordered_above_the_native_view_and_the_web_client_grows_so_the_page_scrolls_as_one(self):
        # rule text only; the real-browser proof is tests/test_layout_browser.py (the contract says a CSS regex is not a layout test)
        self.assertIn(".o_web_client:has(.syn-pg){height:auto;min-height:100vh;overflow-y:auto}", self.CSS)
        self.assertIn(".o_web_client:has(.syn-pg)>.o-main-components-container,.o_web_client:has(.syn-pg)>.syn-enable-panel{order:1;flex:0 0 auto}", self.CSS)
        self.assertIn(".o_web_client:has(.syn-pg)>.o_action_manager{order:2;flex:0 0 auto;height:calc(100vh - 46px);min-height:24rem}", self.CSS)
        for r in BOUND[:3]:
            self.assertIn(self.CSS, page(r, "enable")["html"])  # the style block travels with the page: no global change
        js = open(os.path.join(F.ADDON, "static", "src", "enable_panel.js"), encoding="utf-8").read()
        xml = open(os.path.join(F.ADDON, "static", "src", "enable_panel.xml"), encoding="utf-8").read()
        for bad in ("t-inherit", "patch(", "registry.category(\"actions\")", "registry.category(\"views\")"):
            self.assertNotIn(bad, js + xml)  # nothing replaces or extends the native action, view or a core template

    def test_there_is_no_scroll_container_rule_in_the_panel_and_no_guessed_empty_state_rule(self):
        self.assertNotIn("max-height:60vh", self.CSS); self.assertNotIn(".syn-enable-panel{max-height", self.CSS)
        self.assertNotIn("o_view_nocontent", self.CSS)  # RC06h guessed Odoo's empty-state class; the real-browser matrix measures the gap instead
        self.assertIn(".syn-sc.syn-pg{padding-bottom:0}", self.CSS)  # no 48 px band between the Records heading and the view

    def test_the_records_heading_closes_the_definition_and_precedes_the_native_view(self):
        for b in BOUND:
            h = page(b, "enrich")["html"]
            self.assertEqual(h.count("<h2 class=\"syn-records\""), 1)
            self.assertLess(h.index('data-slot="header"'), h.index('data-slot="records"'))
            self.assertEqual(text(h.split('data-slot="records">')[1]), "Records")
        self.assertIn(".syn-pg .syn-records{margin:10px 0 0;padding-top:8px;padding-bottom:6px;border-top:1px solid #e4e7eb}", self.CSS)

    def test_trust_table_cells_after_the_claim_wrap_instead_of_clipping(self):
        css = sr.STYLE
        self.assertIn(".syn-sc .tt td:not(:first-child)>div{white-space:normal;overflow-wrap:anywhere}", css)
        self.assertIn(".syn-sc .tt td:first-child>div{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}", css)  # the claim keeps one line and its "full text" expander
        self.assertNotIn(rc06h_compat.OLD_RULE, css)
        self.assertEqual(css.count("text-overflow:ellipsis"), 1)
        self.assertIn(".syn-sc .tt details>div{white-space:normal}", css)
        self.assertIn(".syn-sc .tt th:nth-child(3),.syn-sc .tt td:nth-child(3){display:none}", css)  # the 390 px rule is unchanged
        # Status, Source and Open question are the 2nd, 3rd and 4th cells of a row
        h = page(BY_MENU[200], "enrich")["html"]
        row = re.search(r'<tr data-claim=.*?</tr>', h, re.S).group(0)
        self.assertEqual(len(re.findall(r"<td>", row)), 4)


class H4_AnswerPrefix(unittest.TestCase):
    def test_the_prefix_rule(self):
        f = sr.strip_status_prefix
        self.assertEqual(f("OPEN: placed at the same level", "OPEN"), "placed at the same level")
        self.assertEqual(f("open :  x", "OPEN"), "x")
        self.assertEqual(f("CANDIDATE: A measure stored by Mesh address", "CANDIDATE"), "A measure stored by Mesh address")
        self.assertEqual(f("OPEN. Builder proposal", "OPEN"), "OPEN. Builder proposal")  # a full stop is not the pattern
        self.assertEqual(f("A measure stored by Mesh address", "CANDIDATE"), "A measure stored by Mesh address")
        self.assertEqual(f("RULED: x", "OPEN"), "RULED: x")  # only the screen's own status word
        self.assertEqual(f("OPEN:", "OPEN"), "OPEN:")  # never leaves an empty answer
        self.assertEqual(f("OPEN: x", None), "OPEN: x")

    def test_the_list_of_declarations_with_the_pattern_is_exactly_product(self):
        hits = []
        for sid, d in DECLS.items():
            if d["screen_type"] == "record":
                continue
            o = (sw.scaffold_menu(F.Env([F.STEW]), sid, "enable") if d["screen_type"] == "menu" else
                 (sw.scaffold_context(F.Env([F.STEW]), "enable", "") if sid == "SCR.CONTEXT.NOUN" else sw.scaffold_noun(F.Env([F.STEW]), sid, "enable", "")))
            a, st = o["frame"]["answer"], o["frame"]["header"].get("status")
            if sr.strip_status_prefix(a, st) != a:
                hits.append(sid)
        self.assertEqual(hits, ["SCR.PRODUCT.NOUN"])

    def test_measures_answer_is_the_row_quote_with_no_status_word_glued_in(self):
        b = [x for x in BOUND if x["screen_id"] == "SCR.MESH_MEASURES.MENU"][0]
        for d in PAGE_DEPTHS:
            h = page(b, d)["html"]
            ans = re.search(r'data-slot="answer">(.*?)</p>', h, re.S).group(1)
            self.assertEqual(ans, "A measure stored by Mesh address")  # no "CANDIDATE:" and no lead markup
            self.assertIn('<span class="tg">CANDIDATE</span>', h)  # the chip carries the status
        # the glue the Steward saw was the RC06c lead word, not part of the quote: the full screen still has it, the page does not
        full = sw.scaffold_menu(F.Env([F.STEW]), b["screen_id"], "enable")
        self.assertEqual(full["frame"]["answer"], "A measure stored by Mesh address"); self.assertEqual(full["frame"].get("answer_lead"), "CANDIDATE")

    def test_no_bound_page_shows_a_lead_word_beside_the_chip_and_product_has_no_double_status(self):
        for b in BOUND:
            h = page(b, "enable")["html"]
            self.assertNotIn('class="lead"', h, b["menu_name"])
        h = page([x for x in BOUND if x["screen_id"] == "SCR.PRODUCT.NOUN"][0], "enable")["html"]
        self.assertNotIn("OPEN: ", re.search(r'data-slot="answer">(.*?)</p>', h, re.S).group(1))

    def test_full_screens_keep_the_lead_rule_for_everything_but_the_prefixed_answer(self):
        o = sw.scaffold_noun(F.Env([F.STEW]), "SCR.INDUSTRY.NOUN", "enable", "")
        h = sr.render_screen(o)
        self.assertTrue(('class="lead"' in h) == bool(o["frame"].get("answer_lead")))


class H5_ContextFrozen(unittest.TestCase):
    def test_context_declaration_and_goldens_are_unchanged_and_the_render_differs_by_exactly_the_one_css_rule(self):
        import hashlib
        from fakes import sv
        HERE = os.path.dirname(os.path.abspath(__file__))
        for d in sl.DEPTHS:
            o = sw.scaffold_context(F.Env([F.STEW]), d, "1")
            new = sv.render(o, d)
            old = open(os.path.join(HERE, "golden", "rc06a_context_noun_view_%s.html" % d), encoding="utf-8").read()
            self.assertEqual(rc06h_compat.undo_r5(new), old, d)
            self.assertEqual(json.dumps(o, sort_keys=True, indent=1), open(os.path.join(HERE, "golden", "rc06a_context_noun_route_%s.json" % d), encoding="utf-8").read(), d)
            diff = [i for i in range(min(len(new), len(old))) if new[i] != old[i]]
            self.assertTrue(diff and new.count(rc06h_compat.NEW_RULE) == 1)
        golden = json.load(open(os.path.join(HERE, "golden", "rc06f_tree_manifest.json")))["files"]
        self.assertEqual(hashlib.sha256(open(os.path.join(F.ADDON, "data", "screen_declarations.json"), "rb").read()).hexdigest(), golden["data/screen_declarations.json"])


if __name__ == "__main__":
    unittest.main(verbosity=2)


class H6_FileLevelDiffAgainstRc06g(unittest.TestCase):
    def test_only_the_expected_files_changed_and_nothing_was_added_or_removed(self):
        import hashlib
        HERE = os.path.dirname(os.path.abspath(__file__))
        base = json.load(open(os.path.join(HERE, "golden", "rc06g_tree_manifest.json"), encoding="utf-8"))["files"]
        now = {}
        for root, _d, fs in os.walk(F.ADDON):
            for f in fs:
                if "__pycache__" in root or f.endswith(".pyc"):
                    continue
                p = os.path.join(root, f)
                now[os.path.relpath(p, F.ADDON)] = hashlib.sha256(open(p, "rb").read()).hexdigest()
        self.assertEqual((set(now) - set(base), set(base) - set(now)), (set(), set()))  # no file added or removed: still 69
        changed = {k for k in base if now[k] != base[k]}
        self.assertEqual(changed, {"scaffold_wire.py", "screen_render.py", "static/src/enable_panel.js", "static/src/enable_panel.xml"})
        for rel in base:  # views, security, models, migrations, hooks, controllers, every data file: byte-identical
            if rel not in changed:
                self.assertEqual(now[rel], base[rel], rel)
        for rel in ("views/synapsys_menus.xml", "views/synapsys_views.xml", "security/ir.access.csv", "data/screen_bindings_batch5.json", "data/screen_declarations.json"):
            self.assertEqual(now[rel], base[rel], rel)
