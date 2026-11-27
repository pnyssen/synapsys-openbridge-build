"""RC06f offline tests: compact 'made of' and 'linked peers' lists (layout only) and the S12 and S13 placeholder notes.
Offline only: no Odoo, no network, no render (a browser render at 390 px is NOT possible offline; the wrap rule is checked statically in the CSS)."""
import ast, copy, hashlib, html, json, os, re, subprocess, sys, unittest

import fakes as F
import pages_all
from fakes import sl, sd, sr, sw, sv

HERE = os.path.dirname(os.path.abspath(__file__))
DECLS, META = sd.load_declarations()
BASE = json.load(open(os.path.join(HERE, "golden", "rc06e_baseline.json"), encoding="utf-8"))["screens"]
PAGES = pages_all.all_pages(sd, sw, sv, DECLS)
SRC, SRC_SHA = sd.load_sources(sd.DEFAULT_SOURCES_PATH)
OLD_SRC = json.load(open(os.path.join(HERE, "golden", "screen_sources_batch3_rc06e.json"), encoding="utf-8"))
NOTE = "placeholder compiled by the chat lane; replace with sourced text"
S13_OLD = "proposal, Steward decision 3 unruled"
CONTRACT_SHA = "f874250aa16a9ceef2c2dd9c3f89deef9baa6b10a6430db5da65797105f23ce8"
SHOW_S12 = {"SCR.STRATEGIES.MENU"}
SHOW_S13 = {"SCR.NAVIGATOR_PROGRESS.MENU", "SCR.NAVIGATOR_INBOX.MENU", "SCR.NAVIGATOR_LEARNING.MENU"}
STYLE_BLOCK = re.compile(r"<style>.*?</style>", re.S)


def visible(h):
    """Visible text: the style block and tags removed, whitespace collapsed; the two RC06f-stated normalisations (see tools/gen_rc06e_baseline.py)."""
    t = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", STYLE_BLOCK.sub("", h)))).strip()
    t = re.sub(r"Source table fingerprint [0-9a-f]{12}", "", t)
    t = t.replace(" (%s)" % NOTE, "").replace(" %s" % NOTE, "")  # the placeholder note replaces S13's old note and adds one to S12: removed from the new text
    return re.sub(r"\s+", " ", t).strip()


def markup(h):
    return STYLE_BLOCK.sub("", h)


def sha(x):
    return hashlib.sha256(x.encode()).hexdigest()


def slot(h, name):
    m = re.search(r'<(div|p|details)[^>]*data-slot="%s".*?(?=<(?:div|p|details)[^>]*data-slot="|<div class="cd" data-slot="not_applicable"|<p class="nt">)' % name, h, re.S)
    return m.group(0) if m else ""


class F1_TextUnchanged(unittest.TestCase):
    def test_all_46_screens_at_all_three_depths_have_the_visible_text_of_rc06e(self):
        self.assertEqual(len(PAGES), 46)
        self.assertEqual(set(PAGES), set(BASE))
        n = 0
        for sid, ds in PAGES.items():
            for depth, h in ds.items():
                self.assertEqual(sha(visible(h)), BASE[sid][depth]["text_sha"], (sid, depth))
                n += 1
        self.assertEqual(n, 138)

    def test_the_markup_differs_only_by_the_compact_class_on_the_two_lists_for_every_screen_not_showing_s12_or_s13(self):
        for sid, ds in PAGES.items():
            if sid in SHOW_S12 | SHOW_S13:
                continue
            for depth, h in ds.items():
                if SRC_SHA and sid in META["sources_of"]:
                    continue  # batch 3 and 4 menu pages print their source-table fingerprint: covered by the text test above
                m = markup(h).replace('class="cd cp"', 'class="cd"')
                self.assertEqual(sha(m), BASE[sid][depth]["markup_sha"], (sid, depth))

    def test_batch_4_menu_pages_are_unchanged_apart_from_the_class_and_style(self):
        for sid in [s for s in PAGES if s.startswith("SCR.ACTION.")]:
            for depth, h in PAGES[sid].items():
                self.assertEqual(sha(markup(h).replace('class="cd cp"', 'class="cd"')), BASE[sid][depth]["markup_sha"], (sid, depth))

    def test_context_visible_text_is_identical_to_the_rc06e_golden_and_the_route_json_is_untouched(self):
        for depth in sl.DEPTHS:
            old = open(os.path.join(HERE, "golden", "rc06e_context_noun_view_%s.html" % depth), encoding="utf-8").read()
            new = open(os.path.join(HERE, "golden", "rc06a_context_noun_view_%s.html" % depth), encoding="utf-8").read()
            self.assertEqual(visible(new), visible(old), depth)
            self.assertEqual(new, PAGES["SCR.CONTEXT.NOUN"][depth])
            o = sw.scaffold_context(F.Env([F.STEW]), depth, "1")
            self.assertEqual(json.dumps(o, sort_keys=True, indent=1), open(os.path.join(HERE, "golden", "rc06a_context_noun_route_%s.json" % depth), encoding="utf-8").read())
            self.assertEqual(o["declaration_sha"], "2aa425778fe3a7e2f20d242440c907161484318d3ea91a51120b5a8e31144fe0")  # declaration_sha unchanged

    def test_context_golden_diff_is_the_style_block_and_two_class_names_only(self):
        for depth, classes in (("enable", 0), ("enhance", 2), ("enrich", 2)):
            old = open(os.path.join(HERE, "golden", "rc06e_context_noun_view_%s.html" % depth), encoding="utf-8").read()
            new = open(os.path.join(HERE, "golden", "rc06a_context_noun_view_%s.html" % depth), encoding="utf-8").read()
            self.assertEqual(new.count('class="cd cp"'), classes)
            self.assertEqual(markup(new).replace('class="cd cp"', 'class="cd"'), markup(old), depth)  # everything outside the style block differs by those class names only
            added = STYLE_BLOCK.search(new).group(0).replace(STYLE_BLOCK.search(old).group(0)[:-len("</style>")][:300], "")
            self.assertIn(".syn-sc .cp{max-width:44rem}", STYLE_BLOCK.search(new).group(0))
            self.assertNotIn(".syn-sc .cp", STYLE_BLOCK.search(old).group(0))


class F2_CompactLists(unittest.TestCase):
    def test_both_lists_carry_the_compact_class_on_every_screen_that_has_them(self):
        n_made = n_peers = 0
        for sid, ds in PAGES.items():
            for depth in ("enhance", "enrich"):
                h = ds[depth]
                made, peers = slot(h, "made_of"), slot(h, "peers")
                if '<div class="cd' in made:
                    self.assertIn('<div class="cd cp">', made, (sid, depth)); n_made += 1
                if '<div class="cd' in peers:
                    self.assertIn('<div class="cd cp">', peers, (sid, depth)); n_peers += 1
        self.assertGreater(n_made, 40); self.assertEqual(n_peers, 4)  # only the Context noun and Context record declare peers: Enhance and Enrich each
        for sid, ds in PAGES.items():
            self.assertNotIn("cp", slot(ds["enable"], "header") + slot(ds["enable"], "answer"))

    def test_nothing_else_is_compacted_trust_table_header_answer_trust_movement_open_questions_technical(self):
        for sid, ds in PAGES.items():
            h = ds["enrich"]
            for name in ("header", "answer", "trust", "movement", "trust_table", "open_questions", "technical"):
                self.assertNotIn(" cp", slot(h, name), (sid, name))
            lists = sum(1 for n in ("made_of", "peers") if '<div class="cd' in slot(h, n))
            self.assertEqual(h.count('class="cd cp"'), lists, sid)  # the class appears on those lists and nowhere else on the page

    def test_the_css_rule_is_compact_and_wraps_at_390px_static_check_only(self):
        css = sr.STYLE
        self.assertIn(".syn-sc .cp{max-width:44rem}", css)
        w = float(re.search(r"\.syn-sc \.cp\{max-width:([\d.]+)rem\}", css).group(1))
        self.assertTrue(40 <= w <= 48, w)  # about 40 to 48 rem
        rule = re.search(r"\.syn-sc \.cp \.kv\{([^}]*)\}", css).group(1)
        self.assertIn("flex-wrap:wrap", rule); self.assertIn("justify-content:flex-start", rule)  # label and chips adjacent, wrapping within the list
        self.assertIn(".syn-sc .cp .kv span:first-child{flex:0 0 12rem;min-width:0}", css)  # fixed, modest label column
        media = re.search(r"@media \(max-width:600px\)\{(.*)\}</style>", css, re.S).group(1)
        self.assertIn(".syn-sc .kv{flex-direction:column", media)  # at 390 px the row stacks, as before
        self.assertIn(".syn-sc .cp .kv span:first-child,.syn-sc .cp .kv span:last-child{flex:0 1 auto}", media)  # the 12rem basis must not become a height in a column
        self.assertIsNone(re.search(r"(?<![-\w])width:\d+px", css.replace("max-width:1100px", "")))  # no fixed pixel widths that could overflow 390 px
        self.assertNotIn("min-width:3", css.replace("min-width:30%", ""))
        # a browser render at 390 px and 1024 px is NOT possible offline: this is a check of the rule, not of a render

    def test_the_trust_table_rule_and_the_other_rules_are_untouched(self):
        old = open(os.path.join(HERE, "golden", "rc06e_context_noun_view_enable.html"), encoding="utf-8").read()
        old_css = STYLE_BLOCK.search(old).group(0)
        new_css = sr.STYLE
        for needle in (".syn-sc table.tt{width:100%;border-collapse:collapse;font-size:13px;table-layout:fixed}", ".syn-sc .tt td>div{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}",
                       ".syn-sc .kv{display:flex;justify-content:space-between;gap:12px;font-size:13px;padding:6px 0;border-top:1px solid #f0f2f5}", ".syn-sc .an{font-size:15px"):
            self.assertIn(needle, old_css); self.assertIn(needle, new_css)
        removed = [r for r in re.split(r"(?<=\})", old_css) if r not in new_css]
        self.assertEqual([r for r in removed if r.strip() and not r.startswith("@media")], [])  # only the closing media rule is re-written (extended)

    def test_no_script_no_handler_and_the_same_text_on_every_page(self):
        for sid, ds in PAGES.items():
            for depth, h in ds.items():
                self.assertIsNone(re.search(r"<script|\son[a-z]+=|javascript:", markup(h) + STYLE_BLOCK.search(h).group(0), re.I), (sid, depth))

    def test_the_declarations_and_the_renderer_changes_are_layout_only(self):
        for name, sha_ in (("screen_declarations.json", "2aa425778fe3a7e2f20d242440c907161484318d3ea91a51120b5a8e31144fe0"), ("screen_declarations_batch1.json", "2e278bc8c73f1bd20ddcd0c5549a40c037c1749f37f7a680b26047c7593290ff"),
                           ("screen_declarations_batch2.json", "19aef83e13c26a6b5e8062a7df9114eb085bb34a5d305e5332b2b43ee9d117b5"), ("screen_declarations_batch3.json", "200d26ffedde56eace0191438f8cad5449812c87dee749bbe9918955d7954b70"),
                           ("screen_declarations_batch4.json", "ab487f8647114cd3eeb434793112a50d28f835d95b1d5f7bda858e63c07fd387")):
            self.assertEqual(META["files"][name], sha_, name)  # declaration texts and Context's declaration file untouched
        self.assertEqual(hashlib.sha256(open(F.FIXTURE, "rb").read()).hexdigest(), F.REG_SHA)
        self.assertEqual(sd.load_sources(os.path.join(F.ADDON, "data", "screen_sources_batch4.json"))[1], "3957e18430502fe57a1e27904145907e5c3c95b9e93524d7f06ad1b6263b4425")


class F3_PlaceholderNotes(unittest.TestCase):
    def test_only_s12_and_s13_carry_the_placeholder_note_and_their_status_is_still_candidate(self):
        for rid, r in SRC.items():
            if rid in ("S12", "S13"):
                self.assertEqual((r["status_note"], r["status_word"]), (NOTE, "CANDIDATE"), rid)
                self.assertEqual(r["status"], "CANDIDATE (%s)" % NOTE)
            else:
                self.assertNotIn(NOTE, json.dumps(r), rid)
        for sid in PAGES:
            if sid.startswith("SCR.ACTION."):
                self.assertNotIn(NOTE, "".join(PAGES[sid].values()))

    def test_the_rest_of_the_source_table_is_unchanged_from_rc06e(self):
        self.assertEqual(sorted(SRC), sorted(r["id"] for r in OLD_SRC["rows"]))
        for old in OLD_SRC["rows"]:
            new = SRC[old["id"]]
            diff = {k for k in set(old) | set(new) if old.get(k) != new.get(k)}
            if old["id"] in ("S12", "S13"):
                self.assertEqual(diff, {"status_note", "status", "previous_status"}, old["id"])
                self.assertEqual(new["previous_status"], old["status"])  # nothing is lost: the earlier status is kept
                self.assertEqual((new["quote"], new["display"], new["when"], new["file"], new["source_name"]), (old["quote"], old["display"], old["when"], old["file"], old["source_name"]))
            else:
                self.assertEqual(diff, set(), old["id"])
        for k in ("schema", "origin"):
            self.assertEqual(json.load(open(sd.DEFAULT_SOURCES_PATH, encoding="utf-8"))[k], OLD_SRC[k])

    def test_the_note_is_shown_wherever_the_rows_show_a_note(self):
        for sid in SHOW_S12 | SHOW_S13:
            enrich = PAGES[sid]["enrich"]
            claim = "c.S12" if sid in SHOW_S12 else "c.S13"
            tr = re.search(r'<tr data-claim="%s">.*?</tr>' % re.escape(claim), enrich, re.S).group(0)
            cell = re.findall(r"<td>(.*?)</td>", tr, re.S)[1]
            self.assertTrue(cell.startswith('<div><span class="tg">CANDIDATE</span> %s' % NOTE), (sid, cell[:90]))
        # Strategies lists S12 under Made of (Enhance) with its note beside the pill
        made = slot(PAGES["SCR.STRATEGIES.MENU"]["enhance"], "made_of")
        self.assertIn('<span class="tg">CANDIDATE</span> %s' % NOTE, made)
        # S13's old note is gone from every screen, S12's text is unchanged
        for sid in SHOW_S13:
            for h in PAGES[sid].values():
                self.assertNotIn(S13_OLD, h)
        self.assertEqual(SRC["S12"]["display"], OLD_SRC["rows"][11]["display"])
        self.assertEqual(SRC["S13"]["display"], OLD_SRC["rows"][12]["display"])

    def test_the_note_is_shown_nowhere_else_not_on_ruled_rows_or_other_screens(self):
        for sid, ds in PAGES.items():
            for depth, h in ds.items():
                c = text_count(h, NOTE)
                if sid in SHOW_S12 and depth != "enable":
                    self.assertGreaterEqual(c, 1 if depth == "enhance" else 2, (sid, depth))  # Made of item (Enhance); status cell and full citation too (Enrich)
                elif sid in SHOW_S13 and depth == "enrich":
                    self.assertGreaterEqual(c, 2, (sid, depth))  # status cell and full citation of row S13
                else:
                    self.assertEqual(c, 0, (sid, depth))

    def test_the_sources_generator_reproduces_the_file_byte_for_byte_with_the_override(self):
        contract = os.path.join(HERE, "fixtures", "BUILD_CONTRACT_ENABLE_DOC_SOURCED_SCREENS_BATCH3_RC06D_20261127_v1.md")
        ov = os.path.join(HERE, "..", "tools", "overrides_batch3_sources_rc06f.json")
        out = subprocess.run([sys.executable, os.path.join(HERE, "..", "tools", "gen_batch3_sources.py"), contract, ov], capture_output=True, text=True, timeout=60)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(out.stdout, open(sd.DEFAULT_SOURCES_PATH, encoding="utf-8").read())
        self.assertEqual(json.load(open(ov))["rows"], {"S12": {"status_note": NOTE}, "S13": {"status_note": NOTE}})
        self.assertIn(CONTRACT_SHA, json.load(open(ov))["authority"])
        plain = subprocess.run([sys.executable, os.path.join(HERE, "..", "tools", "gen_batch3_sources.py"), contract], capture_output=True, text=True, timeout=60)
        self.assertEqual(json.loads(plain.stdout)["rows"][11]["status_note"], None)  # without the override the generator still gives the RC06e table
        self.assertEqual(plain.stdout, json.dumps(OLD_SRC, indent=2, ensure_ascii=False) + "\n")

    def test_an_override_may_change_a_note_and_nothing_else(self):
        import tempfile
        contract = os.path.join(HERE, "fixtures", "BUILD_CONTRACT_ENABLE_DOC_SOURCED_SCREENS_BATCH3_RC06D_20261127_v1.md")
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            json.dump({"rows": {"S12": {"quote": "x"}}}, fh)
        p = subprocess.run([sys.executable, os.path.join(HERE, "..", "tools", "gen_batch3_sources.py"), contract, fh.name], capture_output=True, text=True, timeout=60)
        os.unlink(fh.name)
        self.assertNotEqual(p.returncode, 0)

    def test_the_unsourced_wording_and_all_contract_text_are_untouched(self):
        self.assertEqual(json.load(open(os.path.join(F.ADDON, "data", "screen_declarations_batch3.json"), encoding="utf-8"))["contract_text"], ["Records: none", "The live menu follows the later.", "Nine strategies by group"])
        self.assertEqual(json.load(open(os.path.join(F.ADDON, "data", "screen_declarations_batch4.json"), encoding="utf-8"))["contract_text"], ["Definition: UNSOURCED. No project document states what this action means."])
        for sid in [s for s in PAGES if s.startswith("SCR.ACTION.")]:
            self.assertIn("Definition: UNSOURCED. No project document states what this action means.", html.unescape(PAGES[sid]["enrich"]))


def text_count(h, s):
    return html.unescape(STYLE_BLOCK.sub("", h)).count(s)


if __name__ == "__main__":
    unittest.main(verbosity=2)
