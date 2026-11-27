"""RC06e batch 4 offline tests: the nine action screens (menu type) sourced from document rows. Offline only; no Odoo, no network, no writes.
Acceptance checks 1 to 17 already run over EVERY declaration in test_screen_arch.py (46 declarations now); this file adds the action-screen tests:
each screen has exactly its own A row and its plane row, no other action's A row, status follows the row, the two fixed open questions on all nine,
UNSOURCED on all nine, no verb bound, no wording outside the source rows and the fixed contract text, and the generators."""
import rc06h_compat
import ast, copy, hashlib, html, json, os, re, subprocess, sys, unittest

import fakes as F
from fakes import sl, sd, sr, sw, sv

HERE = os.path.dirname(os.path.abspath(__file__))
DECLS, META = sd.load_declarations()
NAMES = ["ORIENT", "CANONICALISE", "STRUCTURE", "ASSURE", "NAVIGATE", "COMPOSE", "ACTIVATE", "TRANSFORM", "PROJECT"]
ACTIONS = {"SCR.ACTION.%s" % n: DECLS["SCR.ACTION.%s" % n] for n in NAMES}
SRC_PATH = os.path.join(F.ADDON, "data", "screen_sources_batch4.json")
SRC, SRC_SHA = sd.load_sources(SRC_PATH)
CONTRACT = os.path.join(HERE, "fixtures", "BUILD_CONTRACT_ENABLE_ACTION_SCREENS_BATCH4_RC06E_20261127_v1.md")
CONTRACT_SHA = "743e92bb0eb588a3a28b4fddf6f0d52211e7485e6dcbbc10e7c4c5a7e481b9d6"
DEFINITION = "Definition: UNSOURCED. No project document states what this action means."
PINNED = {"screen_declarations.json": "2aa425778fe3a7e2f20d242440c907161484318d3ea91a51120b5a8e31144fe0",
          "screen_declarations_batch1.json": "2e278bc8c73f1bd20ddcd0c5549a40c037c1749f37f7a680b26047c7593290ff",
          "screen_declarations_batch2.json": "19aef83e13c26a6b5e8062a7df9114eb085bb34a5d305e5332b2b43ee9d117b5",
          "screen_declarations_batch3.json": "200d26ffedde56eace0191438f8cad5449812c87dee749bbe9918955d7954b70"}
B3_SOURCES_SHA = "c6af8087d1265e4cac50d44f4c01cdd2522290378d6d8188521d4177985aa210"  # RC06f: S12 and S13 carry the placeholder note (was 9144a0bc... in RC06e)
ACTOR = {"groups": {"steward"}, "context_ids": set()}
A_OF = {"SCR.ACTION.%s" % n: "A%d" % (i + 1) for i, n in enumerate(NAMES)}
P_OF = {"SCR.ACTION.%s" % n: "P%d" % (i // 3 + 1) for i, n in enumerate(NAMES)}
ROWS_OF = {sid: ["A%d" % (i + 1), P_OF[sid], "C1", "C2", "C3"] for i, sid in enumerate(ACTIONS)}


def project(decl, depth, actor=ACTOR, sources=None):
    o = sd.project_menu(decl, depth, actor, sw.DEFAULT_ROLE_MAX_DEPTH, sources)
    if o.get("result") == "OK":
        o.update({"sources_sha": SRC_SHA, "declaration_sha": META["file_of"][decl["id"]]})
    return o


def page(decl, depth, sources=None):
    return sr.render_screen(project(decl, depth, sources=sources))


def text(h):
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", re.sub(r"<style>.*?</style>", "", h, flags=re.S)))).strip()


def slot(h, name):
    m = re.search(r'<(div|p|details)[^>]*data-slot="%s".*?(?=<(?:div|p|details)[^>]*data-slot="|<div class="cd" data-slot="not_applicable"|<p class="nt">)' % name, h, re.S)
    return m.group(0) if m else ""


def row_cells(h, claim):
    tr = re.search(r'<tr data-claim="%s">.*?</tr>' % re.escape(claim), h, re.S).group(0)
    return re.findall(r"<td>(.*?)</td>", tr, re.S)


class B4_Set(unittest.TestCase):
    def test_nine_action_screens_menu_type_in_a_sibling_file_with_its_own_source_table(self):
        self.assertEqual(len(ACTIONS), 9)
        self.assertEqual(len(DECLS), 46)
        for sid, d in ACTIONS.items():
            self.assertEqual(d["screen_type"], "menu")
            self.assertTrue(not ({"noun", "record"} & set(d)) and d["peers"] is None and d["movement"]["verbs"] == [], sid)
            self.assertEqual(META["file_of"][sid], META["files"]["screen_declarations_batch4.json"])
            self.assertEqual(META["sources_of"][sid], SRC_SHA)
            self.assertEqual(d["title"], SRC[A_OF[sid]]["display"].split(" (")[0])

    def test_earlier_files_goldens_and_sources_are_byte_identical_to_6f5f4d9(self):
        for name, sha in PINNED.items():
            self.assertEqual(META["files"][name], sha, name)
        self.assertEqual(sd.load_sources(sd.DEFAULT_SOURCES_PATH)[1], B3_SOURCES_SHA)
        for depth in sl.DEPTHS:
            o = sw.scaffold_context(F.Env([F.STEW]), depth, "1")
            self.assertEqual(rc06h_compat.undo_r5(sv.render(o, depth)), open(os.path.join(HERE, "golden", "rc06a_context_noun_view_%s.html" % depth), encoding="utf-8").read())
            self.assertEqual(json.dumps(o, sort_keys=True, indent=1), open(os.path.join(HERE, "golden", "rc06a_context_noun_route_%s.json" % depth), encoding="utf-8").read())
        self.assertEqual(hashlib.sha256(open(F.FIXTURE, "rb").read()).hexdigest(), F.REG_SHA)

    def test_the_contract_copy_is_the_contract_and_both_generators_reproduce_their_files_byte_for_byte(self):
        self.assertEqual(hashlib.sha256(open(CONTRACT, "rb").read()).hexdigest(), CONTRACT_SHA)
        a = subprocess.run([sys.executable, os.path.join(HERE, "..", "tools", "gen_batch4_sources.py"), CONTRACT], capture_output=True, text=True, timeout=60)
        self.assertEqual(a.returncode, 0, a.stderr)
        self.assertEqual(a.stdout, open(SRC_PATH, encoding="utf-8").read())
        b = subprocess.run([sys.executable, os.path.join(HERE, "..", "tools", "gen_batch4_declarations.py"), SRC_PATH], capture_output=True, text=True, timeout=60)
        self.assertEqual(b.returncode, 0, b.stderr)
        self.assertEqual(b.stdout, open(os.path.join(F.ADDON, "data", "screen_declarations_batch4.json"), encoding="utf-8").read())

    def test_each_quote_reproduces_from_the_contract_table_byte_for_byte(self):
        table = open(CONTRACT, encoding="utf-8").read()
        self.assertEqual(sorted(SRC), sorted(["A%d" % i for i in range(1, 10)] + ["P1", "P2", "P3", "C1", "C2", "C3"]))
        for rid, r in SRC.items():
            self.assertTrue(re.search(r"^\| %s \| .*? \| %s \| %s \| .*? \| %s \|$" % (rid, re.escape(r["when"]), r["status_word"], re.escape(r["quote"])), table, re.M), rid)
            self.assertEqual(r["display"], r["quote"])  # no mechanical edit at all in this batch
        for rid in ("A%d" % i for i in range(1, 10)):
            self.assertEqual((SRC[rid]["status_word"], SRC[rid]["when"]), ("CANDIDATE", "25 Nov"))
        self.assertEqual((SRC["C2"]["status_word"], SRC["C2"]["when"]), ("OPEN", "13 Nov"))


class B4_Rows(unittest.TestCase):
    def test_each_screen_has_exactly_its_own_a_row_and_its_plane_row(self):
        for sid, d in ACTIONS.items():
            self.assertEqual(d["answer"]["row"], A_OF[sid])
            self.assertEqual([c["rows"] for c in d["claims"]], [[r] for r in ROWS_OF[sid]], sid)
            self.assertEqual(d["made_of"]["rows"], [P_OF[sid]])
            o = project(d, "enhance")
            self.assertEqual([it["id"] for it in o["enhance"]["made_of"]["items"]], [P_OF[sid]])  # Made of lists the plane row and nothing else
            self.assertEqual(o["frame"]["answer"], SRC[A_OF[sid]]["display"])

    def test_no_screen_shows_another_actions_a_row(self):
        for sid, d in ACTIONS.items():
            h = text(page(d, "enrich"))
            for other, a in A_OF.items():
                if other != sid:
                    self.assertNotIn(SRC[a]["display"], h, (sid, other))
                    self.assertNotIn(SRC[a]["display"].split(" (")[0] + " (", h)
            for other, p in P_OF.items():
                if p != P_OF[sid]:
                    self.assertNotIn(SRC[p]["display"], h, (sid, p))  # only its own plane row

    def test_the_planes_are_one_row_for_three_actions_as_the_table_says(self):
        self.assertEqual({sid: P_OF[sid] for sid in ACTIONS}, {"SCR.ACTION.%s" % n: p for n, p in zip(NAMES, ["P1"] * 3 + ["P2"] * 3 + ["P3"] * 3)})
        for p, rng in (("P1", "A1 to A3"), ("P2", "A4 to A6"), ("P3", "A7 to A9")):
            self.assertEqual(SRC[p]["status_note"], "plane of " + rng)

    def test_chips_one_per_row_with_the_rows_own_when_and_at_most_three_then_a_count(self):
        for sid, d in ACTIONS.items():
            h = page(d, "enrich")
            o = project(d, "enrich")
            self.assertEqual(o["frame"]["trust"], {"status": "CANDIDATE", "source_count": 1})
            for c in d["claims"]:
                cell = row_cells(h, c["id"])[2]
                line = re.search(r"<div>(.*?)</div>", cell, re.S).group(1)
                self.assertEqual(len(re.findall(r'class="tg"', line)), 1)
                r = SRC[c["rows"][0]]
                self.assertIn(html.escape("%s %s" % (r["source_name"], r["when"])), line)
            self.assertEqual({ch["date"] for row in o["enrich"]["rows"] for ch in row["chips"]}, {"25 Nov", "13 Nov"})


class B4_StatusAndOpen(unittest.TestCase):
    def test_status_follows_the_row_candidate_with_its_note_and_open_for_c2(self):
        for sid, d in ACTIONS.items():
            h = page(d, "enrich")
            for c in d["claims"]:
                r = SRC[c["rows"][0]]
                cell = row_cells(h, c["id"])[1]
                self.assertTrue(cell.startswith('<div><span class="tg">%s</span> %s' % (r["status_word"], html.escape(r["status_note"]))), (sid, c["id"], cell[:90]))
            self.assertIn('<span class="tg">CANDIDATE</span> read from live V20', row_cells(h, "c." + A_OF[sid])[1])
            self.assertIn('<span class="tg">OPEN</span> relation to the 27 unruled', row_cells(h, "c.C2")[1])
            self.assertEqual(sum(1 for c in d["claims"] if SRC[c["rows"][0]]["status_word"] == "OPEN"), 1)

    def test_nothing_is_shown_ruled_and_the_status_follows_a_changed_row(self):
        for sid, d in ACTIONS.items():
            for depth in sl.DEPTHS:
                self.assertNotIn("RULED", text(page(d, depth)), (sid, depth))
            s = copy.deepcopy(SRC); s[A_OF[sid]]["status_word"] = "RULED"
            o = project(d, "enrich", sources=s)
            self.assertEqual((o["frame"]["trust"]["status"], "answer_lead" in o["frame"]), ("RULED", False), sid)
            s[A_OF[sid]]["status_word"] = "OPEN"
            self.assertEqual(project(d, "enrich", sources=s)["frame"]["trust"]["status"], "OPEN")

    def test_every_candidate_answer_leads_with_its_status_word(self):
        for sid, d in ACTIONS.items():
            o = project(d, "enable")
            self.assertEqual(o["frame"]["answer_lead"], "CANDIDATE")
            self.assertIn('<strong class="lead">CANDIDATE:</strong>', sr.render_screen(o))

    def test_exactly_two_open_questions_on_all_nine_the_fixed_definition_text_and_c2(self):
        for sid, d in ACTIONS.items():
            o = project(d, "enrich")
            texts = [q["text"] for r in o["enrich"]["rows"] for q in r["open"]]
            self.assertEqual(texts, [DEFINITION, SRC["C2"]["display"]], sid)
            self.assertEqual(o["enrich"]["open_total"], 2)
            h = html.unescape(page(d, "enrich"))
            self.assertEqual(h.count(DEFINITION), 1, sid)
            oq_html = html.unescape(slot(page(d, "enrich"), "open_questions"))
            self.assertEqual((oq_html.count("<li>%s</li>" % DEFINITION), oq_html.count("<ul><li>%s</li></ul>" % SRC["C2"]["display"])), (1, 1))  # each question once in the roll-up
            # C2 is both a claim row and an open item, so its text is also the row's label in the roll-up (same as S11 and S13 in batch 3): a finding, not a change
            self.assertIn("UNSOURCED", text(page(d, "enrich")))

    def test_transform_adds_nothing_beyond_c2_and_does_not_resolve_the_word_in_both_sets(self):
        d = ACTIONS["SCR.ACTION.TRANSFORM"]
        o = project(d, "enrich")
        self.assertEqual([c["rows"] for c in d["claims"]], [["A8"], ["P3"], ["C1"], ["C2"], ["C3"]])
        self.assertEqual(SRC["A8"]["display"], "Transform (compound, succeed, transform)")
        self.assertIn('"transform" is in both sets', SRC["C2"]["display"])
        h = text(page(d, "enrich"))
        for word in ("resolved", "duplicate", "same verb", "clash"):
            self.assertNotIn(word, h.lower())
        self.assertEqual(json.dumps(sorted(r["id"] for r in o["enrich"]["rows"])), json.dumps(sorted(["c.A8", "c.P3", "c.C1", "c.C2", "c.C3"])))

    def test_the_fixed_text_must_be_listed_in_contract_text(self):
        import tempfile
        doc = json.load(open(os.path.join(F.ADDON, "data", "screen_declarations_batch4.json"), encoding="utf-8"))
        doc["contract_text"] = []
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "b4.json")
            json.dump(doc, open(p, "w"))
            os.link(SRC_PATH, os.path.join(tmp, "screen_sources_batch4.json"))
            with self.assertRaises(ValueError) as cm:
                sd.load_declarations([p])
            self.assertIn("contract_text", str(cm.exception))

    def test_an_unsourced_item_is_validated(self):
        d = copy.deepcopy(ACTIONS["SCR.ACTION.ORIENT"])
        for bad in ({"text": ""}, {"rows": ["C2"]}, {"claim": "c.nope"}):
            x = copy.deepcopy(d); x["open"][0].update(bad)
            self.assertTrue(sd.validate_screen(x, SRC), bad)
        self.assertEqual(sd.validate_screen(d, SRC), [])


class B4_NoVerbsNoInventedText(unittest.TestCase):
    def test_no_verb_is_bound_selectable_linked_or_counted(self):
        for sid, d in ACTIONS.items():
            self.assertEqual(d["movement"]["verbs"], [])
            for depth in sl.DEPTHS:
                h = page(d, depth)
                mv = slot(h, "movement")
                self.assertIn("HOLD", mv); self.assertIn("verbs not yet bound", mv)
                self.assertIsNone(re.search(r"<a |<button|<input|<select|href=", re.sub(r'<a class="bk".*?</a>', "", h)), (sid, depth))  # the verbs in an A row are text only
        x = copy.deepcopy(ACTIONS["SCR.ACTION.ORIENT"]); x["movement"]["verbs"] = [{"verb": "sense", "source": "A1", "status": "bound"}]
        self.assertTrue(sd.validate_screen(x, SRC))
        self.assertEqual(sw.scaffold_menu(F.Env([F.STEW]), "SCR.ACTION.ORIENT", "enrich")["frame"]["movement"]["verbs"], [])

    def test_no_wording_outside_the_source_rows_and_the_fixed_contract_text(self):
        contract_text = json.load(open(os.path.join(F.ADDON, "data", "screen_declarations_batch4.json"), encoding="utf-8"))["contract_text"]
        chrome = set()
        for f in ("screen_render.py", "screen_decl.py"):
            tree = ast.parse(open(os.path.join(F.ADDON, f), encoding="utf-8").read())
            chrome |= {w.lower() for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str) for w in re.findall(r"[A-Za-z]+", n.value)}
        for sid, d in ACTIONS.items():
            for depth in sl.DEPTHS:
                o = project(d, depth)
                t = text(sr.render_screen(o))
                allowed = [d["title"], sid, o["declaration_sha"][:12], o["sources_sha"][:12], d["movement"]["hold_reason"]] + contract_text
                for x in SRC.values():
                    allowed += [x["display"], x["quote"], x["file"], x["when"], x["status"], x["status_word"], x["source_name"], "“%s” (%s)" % (x["display"], x["when"])] + ([x["status_note"]] if x["status_note"] else [])
                for r in o.get("enrich", {}).get("rows", []):
                    allowed += [q["stem"] + "…" for q in r["open"]] + [q["text"] for q in r["open"]]
                for a in sorted({a for a in allowed if a}, key=len, reverse=True):
                    t = t.replace(a, " ")
                self.assertEqual({w.lower() for w in re.findall(r"[A-Za-z]+", t)} - chrome, set(), (sid, depth))

    def test_definition_purpose_example_what_it_does_and_peer_text_never_appear(self):
        for sid, d in ACTIONS.items():
            h = text(page(d, "enrich")).lower()
            for word in ("purpose", "for example", "what it does", "is used to", "means that", "linked peer:"):
                self.assertNotIn(word, h, (sid, word))
            self.assertIn("No linked peers are declared for this screen.", page(d, "enhance"))
            self.assertEqual(d["peers"], None)
            self.assertEqual(sorted(k for k in d if k in ("definition", "purpose", "example", "description")), [])

    def test_the_three_depths_and_the_entitlements(self):
        for sid, d in ACTIONS.items():
            for depth in sl.DEPTHS:
                o = project(d, depth)
                self.assertEqual((o["depth_effective"], o["depth_clamped"], o["stage"]), (depth, False, None))
            e = project(d, "enable")
            self.assertEqual(set(e) & {"enhance", "enrich"}, set())
            self.assertNotIn(SRC["C2"]["file"], json.dumps(e))
            c = sd.project_menu(d, "enrich", {"groups": {"client"}, "context_ids": set()}, None)
            self.assertEqual((c["depth_effective"], c["clamp_reason"], "enrich" in c), ("enhance", "role", False))

    def test_the_question_of_each_depth_each_depth_adds_only_its_own_slots(self):
        for sid, d in ACTIONS.items():
            hs = {depth: page(d, depth) for depth in sl.DEPTHS}
            self.assertEqual(re.findall(r'data-slot="(\w+)"', hs["enable"]), ["header", "answer", "trust", "movement"])
            self.assertEqual(re.findall(r'data-slot="(\w+)"', hs["enhance"]), ["header", "answer", "trust", "movement", "made_of", "peers"])
            self.assertEqual(re.findall(r'data-slot="(\w+)"', hs["enrich"]), ["header", "answer", "trust", "movement", "made_of", "peers", "trust_table", "open_questions", "technical"])


class B4_Wire(unittest.TestCase):
    def test_wire_serves_all_nine_with_no_environment_read_and_no_write(self):
        for sid in ACTIONS:
            for depth in sl.DEPTHS:
                e = F.Env([F.STEW])
                o = sw.scaffold_menu(e, sid, depth)
                self.assertEqual((o["result"], o["writes"], o["screen"], o["depth_effective"]), ("OK", 0, sid, depth), (sid, depth))
                self.assertEqual(e.log, [])
                self.assertEqual((o["declaration_sha"], o["sources_sha"]), (META["file_of"][sid], SRC_SHA))
                self.assertNotIn("Registry", text(sv.render(o, depth)))
        e = F.Env([F.STEW])
        self.assertEqual(sw.scaffold_noun(e, "SCR.ACTION.ORIENT", "enable")["reason"], "UNKNOWN_SCREEN")
        self.assertEqual(sw.scaffold_menu(e, "SCR.STRATEGIES.MENU", "enable")["result"], "OK")  # batch 3 still served from its own table
        n = F.Env([])
        self.assertEqual(sw.scaffold_menu(n, "SCR.ACTION.ORIENT", "enable")["reason"], "NO_RECOGNISED_ROLE"); self.assertEqual(n.log, [])

    def test_no_route_menu_placement_or_manifest_change(self):
        c = open(os.path.join(F.ADDON, "controllers", "scaffold.py"), encoding="utf-8").read()
        self.assertEqual(c.count("@http.route"), 2)  # where an action screen sits in a menu is not decided here (batch 5, Steward)
        self.assertNotIn("screen_", open(os.path.join(F.ADDON, "__manifest__.py"), encoding="utf-8").read())
        for f in ("views/synapsys_menus.xml", "views/synapsys_screens.xml"):
            self.assertNotIn("SCR.ACTION", open(os.path.join(F.ADDON, f), encoding="utf-8").read())


if __name__ == "__main__":
    unittest.main(verbosity=2)
