"""RC06d batch 3 offline tests: the seven menu screens sourced from project documents. Offline only; no Odoo, no network, no writes.
Acceptance checks 1 to 17 already run over EVERY declaration in test_screen_arch.py (ALL includes these seven); this file adds the
document-source tests: provenance against the shipped source table, source status, conflicts shown and never resolved, no verbs, no wording
outside the source table, and the wire."""
import rc06h_compat
import ast, copy, hashlib, html, json, os, re, subprocess, sys, tempfile, unittest

import fakes as F
from fakes import sl, sd, sr, sw, sv

HERE = os.path.dirname(os.path.abspath(__file__))
DECLS, META = sd.load_declarations()
SRC, SRC_SHA = sd.load_sources(sd.DEFAULT_SOURCES_PATH)
IDS = ["STRATEGIES", "NAVIGATOR_PROGRESS", "NAVIGATOR_INBOX", "NAVIGATOR_LEARNING", "MESH_BENEFIT_ASSET_LINKS", "MESH_DOOR_RECEIPTS", "MESH_MEASURES"]
MENUS = {"SCR.%s.MENU" % n: DECLS["SCR.%s.MENU" % n] for n in IDS}
CONTRACT = os.path.join(HERE, "fixtures", "BUILD_CONTRACT_ENABLE_DOC_SOURCED_SCREENS_BATCH3_RC06D_20261127_v1.md")
CONTRACT_SHA = "85d9e13712bafa656e542ac564d0f9b877d57373c3508325e29941cf621b4b9c"
PINNED = {"screen_declarations.json": "2aa425778fe3a7e2f20d242440c907161484318d3ea91a51120b5a8e31144fe0",
          "screen_declarations_batch1.json": "2e278bc8c73f1bd20ddcd0c5549a40c037c1749f37f7a680b26047c7593290ff",
          "screen_declarations_batch2.json": "19aef83e13c26a6b5e8062a7df9114eb085bb34a5d305e5332b2b43ee9d117b5"}
ACTOR = {"groups": {"steward"}, "context_ids": set()}
USED_ROWS = {sid: sorted({r for c in d["claims"] for r in c["rows"]} | set(d["made_of"]["rows"]) | {d["answer"]["row"]} | {r for o in d["open"] for r in o["rows"]}, key=lambda x: int(x[1:]))
             for sid, d in MENUS.items()}


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


def with_row(row_id, **changes):
    s = copy.deepcopy(SRC)
    s[row_id].update(changes)
    return s


class B3_Set(unittest.TestCase):
    def test_exactly_the_seven_menu_screens_no_noun_no_record_no_peers_no_verbs(self):
        self.assertEqual(len(MENUS), 7)
        for sid, d in MENUS.items():
            self.assertEqual(d["screen_type"], "menu")
            self.assertTrue(not ({"noun", "record"} & set(d)) and d["peers"] is None and d["movement"]["verbs"] == [], sid)
            self.assertTrue(all(c["type"] == "doc" for c in d["claims"]))
            self.assertEqual(META["file_of"][sid], META["files"]["screen_declarations_batch3.json"])
            self.assertEqual(META["sources_of"][sid], SRC_SHA)

    def test_earlier_declaration_files_are_byte_identical_and_goldens_still_pass(self):
        for name, sha in PINNED.items():
            self.assertEqual(META["files"][name], sha, name)
        for depth in sl.DEPTHS:
            o = sw.scaffold_context(F.Env([F.STEW]), depth, "1")
            self.assertEqual(rc06h_compat.undo_r5(sv.render(o, depth)), open(os.path.join(HERE, "golden", "rc06a_context_noun_view_%s.html" % depth), encoding="utf-8").read())
            self.assertEqual(json.dumps(o, sort_keys=True, indent=1), open(os.path.join(HERE, "golden", "rc06a_context_noun_route_%s.json" % depth), encoding="utf-8").read())
        self.assertEqual(len([d for d in DECLS if not d.startswith('SCR.ACTION.')]), 3 + 15 + 12 + 7)  # RC06e adds the nine action screens

    def test_the_contract_copy_is_the_contract_and_the_generators_reproduce_both_files_byte_for_byte(self):
        self.assertEqual(hashlib.sha256(open(CONTRACT, "rb").read()).hexdigest(), CONTRACT_SHA)
        a = subprocess.run([sys.executable, os.path.join(HERE, "..", "tools", "gen_batch3_sources.py"), CONTRACT, os.path.join(HERE, "..", "tools", "overrides_batch3_sources_rc06f.json")], capture_output=True, text=True, timeout=60)  # RC06f: the S12 and S13 note override
        self.assertEqual(a.returncode, 0, a.stderr)
        self.assertEqual(a.stdout, open(sd.DEFAULT_SOURCES_PATH, encoding="utf-8").read())
        b = subprocess.run([sys.executable, os.path.join(HERE, "..", "tools", "gen_batch3_declarations.py"), sd.DEFAULT_SOURCES_PATH], capture_output=True, text=True, timeout=60)
        self.assertEqual(b.returncode, 0, b.stderr)
        self.assertEqual(b.stdout, open(os.path.join(F.ADDON, "data", "screen_declarations_batch3.json"), encoding="utf-8").read())

    def test_registry_is_unchanged_and_pinned(self):
        self.assertEqual(hashlib.sha256(open(F.FIXTURE, "rb").read()).hexdigest(), F.REG_SHA)

    def test_the_source_table_has_nineteen_rows_and_row_s8_is_used_by_no_screen(self):
        self.assertEqual(sorted(SRC, key=lambda x: int(x[1:])), ["S%d" % i for i in range(1, 20)])
        used = {r for rs in USED_ROWS.values() for r in rs}
        self.assertEqual(set(SRC) - used, {"S8"})  # the contract's per-screen lists never name S8 (OPEN: align Progress, Inbox and Learning to the Adapt strategies)


class B3_Provenance(unittest.TestCase):
    def test_every_shown_text_is_a_source_row_verbatim(self):
        for sid, d in MENUS.items():
            o = project(d, "enrich")
            ans = SRC[d["answer"]["row"]]
            self.assertEqual(o["frame"]["answer"], ans["display"], sid)
            for c, row in zip(d["claims"], o["enrich"]["rows"]):
                self.assertEqual(row["label"], SRC[c["rows"][0]]["display"], sid)
                self.assertEqual([ch["row"] for ch in row["chips"]], c["rows"])
                for ch, r in zip(row["chips"], c["rows"]):
                    self.assertEqual((ch["name"], ch["date"]), (SRC[r]["source_name"], SRC[r]["when"]), (sid, r))  # the date is the row's own, never inferred
                for r in c["rows"]:
                    self.assertIn(SRC[r]["display"] if SRC[r].get("builder_instruction") else SRC[r]["quote"], row["full_citation"])  # the builder's own instruction is never part of a citation
            for it in o["enhance"]["made_of"]["items"]:
                self.assertEqual(it["text"], SRC[it["id"]]["display"])

    def test_display_text_is_the_quotation_with_only_the_stated_mechanical_edits(self):
        for rid, r in SRC.items():
            if rid == "S10":
                self.assertEqual(r["display"], r["quote"].replace("*", ""))
                self.assertIn("Strategy groups are", r["display"]); self.assertIn("Live / Build / Adapt", r["display"])
            elif rid in ("S12", "S13"):
                self.assertTrue(r["quote"].startswith(r["display"]) and r["quote"][len(r["display"]):].strip() == r["builder_instruction"], rid)
                self.assertFalse(r["is_quotation"])
            else:
                self.assertEqual(r["display"], r["quote"], rid)
                self.assertTrue(r["is_quotation"])

    def test_each_quote_is_found_verbatim_in_the_contract_table(self):
        table = open(CONTRACT, encoding="utf-8").read()
        for rid, r in SRC.items():
            self.assertIn(r["quote"], table, rid)
            self.assertIn("%s | " % rid, table)

    def test_a_changed_source_row_changes_the_screen_and_a_missing_row_refuses_the_declaration(self):
        d = MENUS["SCR.MESH_MEASURES.MENU"]
        s = with_row("S19", display="A measure stored elsewhere")
        self.assertIn("A measure stored elsewhere", page(d, "enable", s))
        s2 = {k: v for k, v in SRC.items() if k != "S17"}
        self.assertTrue(any("S17" in e or "rows" in e for e in sd.validate_screen(d, s2)))

    def test_no_wording_outside_the_source_table(self):
        contract_text = json.load(open(sd.DEFAULT_PATHS[3], encoding="utf-8"))["contract_text"]
        chrome = set()
        for f in ("screen_render.py", "screen_decl.py"):  # the renderer's own strings, plus the model's fixed movement wording
            tree = ast.parse(open(os.path.join(F.ADDON, f), encoding="utf-8").read())
            chrome |= {w.lower() for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str) for w in re.findall(r"[A-Za-z]+", n.value)}
        for sid, d in MENUS.items():
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
                residual = {w.lower() for w in re.findall(r"[A-Za-z]+", t)}
                self.assertEqual(residual - chrome, set(), (sid, depth))  # every remaining word is the renderer's own wording (labels, headings, notes)

    def test_chips_are_one_per_source_row_with_the_rows_own_date_and_at_most_three_then_a_count(self):
        for sid, d in MENUS.items():
            h = page(d, "enrich")
            for c in d["claims"]:
                row = re.search(r'<tr data-claim="%s">.*?</tr>' % re.escape(c["id"]), h, re.S).group(0)
                cell = re.findall(r"<td>(.*?)</td>", row, re.S)[2]
                line = re.search(r"<div>(.*?)</div>", cell, re.S).group(1)
                self.assertEqual(len(re.findall(r'class="tg"', line)), min(3, len(c["rows"])))
                for r in c["rows"]:
                    self.assertIn(html.escape("%s %s" % (SRC[r]["source_name"], SRC[r]["when"])), line)


class B3_Status(unittest.TestCase):
    def test_the_status_cell_equals_the_source_rows_status_and_its_note_is_the_rows_own(self):
        for sid, d in MENUS.items():
            h = page(d, "enrich")
            for c in d["claims"]:
                first = SRC[c["rows"][0]]
                row = re.search(r'<tr data-claim="%s">.*?</tr>' % re.escape(c["id"]), h, re.S).group(0)
                cell = re.findall(r"<td>(.*?)</td>", row, re.S)[1]
                self.assertTrue(cell.startswith('<div><span class="tg">%s</span>' % first["status_word"]), (sid, c["id"], cell[:60]))
                if first["status_note"]:
                    self.assertIn(html.escape(first["status_note"]), cell)
                else:
                    self.assertEqual(re.sub(r"<[^>]+>", "", re.search(r"<div>(.*?)</div>", cell, re.S).group(1)).strip(), first["status_word"])

    def test_nothing_is_shown_ruled_unless_its_row_says_ruled(self):
        for sid, d in MENUS.items():
            rows = USED_ROWS[sid]
            for depth in sl.DEPTHS:
                h = page(d, depth)
                shown_ruled = h.count('<span class="tg">RULED</span>')
                allowed = sum(1 for r in rows if SRC[r]["status_word"] == "RULED")
                self.assertTrue(shown_ruled <= (allowed + 4), (sid, depth))  # header, trust line, status cell and made-of pills, at most
                if allowed == 0:
                    self.assertNotIn("RULED", text(h), (sid, depth))
        for sid in ("SCR.MESH_BENEFIT_ASSET_LINKS.MENU", "SCR.MESH_DOOR_RECEIPTS.MENU", "SCR.MESH_MEASURES.MENU"):
            self.assertTrue(all(SRC[r]["status_word"] == "CANDIDATE" for r in USED_ROWS[sid]))

    def test_status_follows_the_source_row_not_an_assumption(self):
        for sid, d in MENUS.items():
            for word in ("RULED", "CANDIDATE", "OPEN"):
                first = d["answer"]["row"]
                s = copy.deepcopy(SRC)
                for r in [x for c in d["claims"] if c["id"] == d["trust_claim"] for x in c["rows"]]:
                    s[r]["status_word"] = word
                o = project(d, "enrich", sources=s)
                self.assertEqual((o["status"], o["frame"]["trust"]["status"], o["enrich"]["rows"][0]["status"]), (word, word, word), (sid, word))
                self.assertEqual("answer_lead" in o["frame"], word != "RULED" and not s[first]["display"].upper().startswith(word))

    def test_a_non_ruled_answer_leads_with_its_status_word(self):
        for sid in ("SCR.MESH_BENEFIT_ASSET_LINKS.MENU", "SCR.MESH_DOOR_RECEIPTS.MENU", "SCR.MESH_MEASURES.MENU"):
            o = project(MENUS[sid], "enable")
            self.assertEqual(o["frame"]["answer_lead"], "CANDIDATE")
            self.assertIn('<strong class="lead">CANDIDATE:</strong>', sr.render_screen(o))
        for sid in ("SCR.STRATEGIES.MENU", "SCR.NAVIGATOR_PROGRESS.MENU", "SCR.NAVIGATOR_INBOX.MENU", "SCR.NAVIGATOR_LEARNING.MENU"):
            self.assertNotIn("answer_lead", project(MENUS[sid], "enable")["frame"])  # their answer rows are RULED

    def test_trust_line_header_and_table_agree_at_every_depth(self):
        for sid, d in MENUS.items():
            st = SRC[d["answer"]["row"]]["status_word"]
            n = len(next(c for c in d["claims"] if c["id"] == d["trust_claim"])["rows"])
            for depth in sl.DEPTHS:
                h = page(d, depth)
                self.assertIn('<span class="tg">%s</span> %d source' % (st, n), slot(h, "trust"))
                self.assertIn('<span class="tg">%s</span></h1>' % st, h)


class B3_Conflicts(unittest.TestCase):
    def test_learning_shows_both_placements_and_chooses_neither(self):
        d = MENUS["SCR.NAVIGATOR_LEARNING.MENU"]
        o = project(d, "enrich")
        conflict = [q["text"] for r in o["enrich"]["rows"] for q in r["open"] if "versus" in q["text"]]
        self.assertEqual(len(conflict), 1)
        c = conflict[0]
        for r in ("S7", "S4", "S6"):
            self.assertIn(SRC[r]["display"], c)
            self.assertIn(SRC[r]["when"], c)
        self.assertLess(c.index(SRC["S7"]["display"]), c.index("versus")); self.assertLess(c.index("versus"), c.index(SRC["S4"]["display"]))
        self.assertTrue(c.endswith("The live menu follows the later."))
        h = html.unescape(page(d, "enrich"))
        self.assertEqual(h.count(c), 1)  # once, rolled up
        s7 = [r for r in o["enrich"]["rows"] if r["id"] == "c.S7"][0]
        self.assertEqual((s7["status"], s7["qualifier"]["first"]), ("RULED", SRC["S7"]["status_note"]))  # the source's own words: the conflict is in its status
        for word in ("resolved", "superseded", "chosen", "overrid"):
            self.assertNotIn(word, text(h).lower())
        self.assertEqual(SRC["S7"]["when"], "20 Nov 07:35"); self.assertEqual((SRC["S4"]["when"], SRC["S6"]["when"]), ("20 Nov 10:03", "20 Nov 10:05"))

    def test_strategies_shows_both_cuts_and_the_open_decision(self):
        d = MENUS["SCR.STRATEGIES.MENU"]
        h = html.unescape(page(d, "enrich"))
        for r in ("S9", "S10", "S12", "S11"):
            self.assertIn(html.unescape(SRC[r]["display"]), h, r)
        o = project(d, "enrich")
        self.assertEqual([q["text"] for r in o["enrich"]["rows"] for q in r["open"]], [SRC["S11"]["display"]])
        s11 = [r for r in o["enrich"]["rows"] if r["id"] == "c.S11"][0]
        self.assertEqual((s11["status"], s11["qualifier"]["first"]), ("CANDIDATE", "open decision D4"))
        for name in ("Balanced Lives", "Synergistic Collaboration", "Enduring Wealth", "Renewal", "Prioritisation", "Stewardship", "Capture Valuable Markets", "Compound Innovation", "Integrate Value Networks"):
            self.assertIn(name, text(slot(page(d, "enhance"), "made_of")))
        self.assertNotIn("Show names only", h)  # the builder's instruction is not screen text
        self.assertNotIn("**", text(page(d, "enable")))  # the markdown asterisks of S10 are stripped in displayed text
        self.assertIn("Strategy groups are Live / Build / Adapt", h)

    def test_the_unruled_proposal_s13_is_shown_as_an_open_item_with_its_candidate_status_never_as_the_menu(self):
        for sid in ("SCR.NAVIGATOR_PROGRESS.MENU", "SCR.NAVIGATOR_INBOX.MENU", "SCR.NAVIGATOR_LEARNING.MENU"):
            o = project(MENUS[sid], "enrich")
            row = [r for r in o["enrich"]["rows"] if r["id"] == "c.S13"][0]
            self.assertEqual((row["status"], row["qualifier"]["first"], len(row["open"])), ("CANDIDATE", SRC["S13"]["status_note"], 1))
            self.assertEqual(row["open"][0]["text"], SRC["S13"]["display"])
            self.assertNotIn("S13", json.dumps(project(MENUS[sid], "enhance")))  # it is an Enrich item only
        for sid in ("SCR.STRATEGIES.MENU", "SCR.MESH_BENEFIT_ASSET_LINKS.MENU", "SCR.MESH_DOOR_RECEIPTS.MENU", "SCR.MESH_MEASURES.MENU"):
            self.assertNotIn(SRC["S13"]["display"], page(MENUS[sid], "enrich"))

    def test_open_questions_are_only_conflicts_and_unruled_proposals(self):
        expect = {"STRATEGIES": 1, "NAVIGATOR_PROGRESS": 1, "NAVIGATOR_INBOX": 1, "NAVIGATOR_LEARNING": 2, "MESH_BENEFIT_ASSET_LINKS": 0, "MESH_DOOR_RECEIPTS": 0, "MESH_MEASURES": 0}
        for n, k in expect.items():
            o = project(MENUS["SCR.%s.MENU" % n], "enrich")
            self.assertEqual(o["enrich"]["open_total"], k, n)
            self.assertEqual("none recorded" in slot(page(MENUS["SCR.%s.MENU" % n], "enrich"), "open_questions"), k == 0, n)


class B3_NoVerbsNoRecords(unittest.TestCase):
    def test_verbs_hold_at_every_depth_and_a_verb_cannot_be_declared(self):
        for sid, d in MENUS.items():
            for depth in sl.DEPTHS:
                mv = slot(page(d, depth), "movement")
                self.assertIn("HOLD", mv); self.assertIn("verbs not yet bound", mv)
        bad = copy.deepcopy(MENUS["SCR.STRATEGIES.MENU"]); bad["movement"]["verbs"] = [{"verb": "x", "source": "s", "status": "bound"}]
        self.assertTrue(sd.validate_screen(bad, SRC))

    def test_records_none_is_said_only_where_the_contract_says_it(self):
        for n in IDS:
            h = text(page(MENUS["SCR.%s.MENU" % n], "enhance"))
            self.assertEqual("Records: none" in h, n in ("STRATEGIES", "MESH_BENEFIT_ASSET_LINKS"), n)
        for n in IDS:
            h = text(page(MENUS["SCR.%s.MENU" % n], "enrich")).lower()
            for word in ("promotion", "promote", "human act"):
                self.assertNotIn(word, h, n)  # no source row says promotion is a human act, so no screen says it

    def test_text_outside_the_source_rows_must_be_listed_in_contract_text(self):
        doc = json.load(open(sd.DEFAULT_PATHS[3], encoding="utf-8"))
        doc["contract_text"] = []
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "b3.json")
            json.dump(doc, open(p, "w"))
            os.link(sd.DEFAULT_SOURCES_PATH, os.path.join(tmp, "screen_sources_batch3.json")) if hasattr(os, "link") else None
            with self.assertRaises(ValueError) as cm:
                sd.load_declarations([p])
            self.assertIn("contract_text", str(cm.exception))


class B3_Validator(unittest.TestCase):
    def test_menu_schema_is_enforced(self):
        d = MENUS["SCR.NAVIGATOR_LEARNING.MENU"]
        cases = []
        x = copy.deepcopy(d); x["noun"] = "N.CONTEXT"; cases.append(("noun", x))
        x = copy.deepcopy(d); x["record"] = {}; cases.append(("record", x))
        x = copy.deepcopy(d); x["peers"] = {"heading": "p", "nouns": []}; cases.append(("peers", x))
        x = copy.deepcopy(d); x["claims"][0]["rows"] = ["S99"]; cases.append(("row", x))
        x = copy.deepcopy(d); x["claims"][0]["rows"] = ["S6", "S13"]; cases.append(("mixed status", x))
        x = copy.deepcopy(d); x["open"][0]["kind"] = "invented"; cases.append(("open kind", x))
        x = copy.deepcopy(d); x["open"][0]["rows"] = ["S7"]; cases.append(("conflict of one", x))
        x = copy.deepcopy(d); x["answer"] = {"from": "element.definition"}; cases.append(("answer", x))
        x = copy.deepcopy(d); x["trust_claim"] = "c.S4"; cases.append(("trust claim must start with the answer row", x))
        x = copy.deepcopy(d); x["movement"]["hold_reason"] = ""; cases.append(("hold", x))
        for name, bad in cases:
            self.assertTrue(sd.validate_screen(bad, SRC), name)
        self.assertEqual(sd.validate_screen(d, SRC), [])
        self.assertTrue(sd.validate_screen(d, None))  # a menu screen without a source table is refused

    def test_registry_screens_still_demand_a_registry_element(self):
        bad = copy.deepcopy(DECLS["SCR.SERVICE.NOUN"]); bad["claims"][0]["type"] = "doc"
        self.assertTrue(sd.validate_screen(bad))
        for sid, d in DECLS.items():
            if d["screen_type"] != "menu":
                self.assertEqual(sd.validate_screen(d), [], sid)


class B3_Entitlement(unittest.TestCase):
    def test_enable_holds_only_the_frame_and_the_answer_row(self):
        for sid, d in MENUS.items():
            o = project(d, "enable")
            self.assertEqual(set(o) & {"enhance", "enrich"}, set())
            blob = json.dumps(o)
            for r in USED_ROWS[sid]:
                if r != d["answer"]["row"]:
                    self.assertNotIn(SRC[r]["display"], blob, (sid, r))
                self.assertNotIn(SRC[r]["file"], blob)

    def test_a_client_is_limited_to_enhance_and_gets_no_enrich_content(self):
        for sid, d in MENUS.items():
            o = sd.project_menu(d, "enrich", {"groups": {"client"}, "context_ids": set()}, None)
            self.assertEqual((o["depth_effective"], o["clamp_reason"], "enrich" in o), ("enhance", "role", False), sid)
            self.assertNotIn(SRC[d["answer"]["row"]]["file"], json.dumps(o))
        self.assertEqual(sd.project_menu(MENUS["SCR.STRATEGIES.MENU"], "enrich", {"groups": set()}, None)["reason"], "NO_RECOGNISED_ROLE")
        self.assertEqual(sd.project_menu(MENUS["SCR.STRATEGIES.MENU"], "deep", ACTOR, None)["reason"], "UNKNOWN_DEPTH")

    def test_no_stage_never_clamps_for_stage_and_the_depth_ladder_is_full(self):
        for sid, d in MENUS.items():
            for depth in sl.DEPTHS:
                o = project(d, depth)
                self.assertEqual((o["depth_effective"], o["depth_clamped"], o["stage"]), (depth, False, None))
                self.assertIn("Stage: none (a menu screen has no stage)", sr.render_screen(o))
                self.assertNotIn("Not applicable", sr.render_screen(o))


class B3_Wire(unittest.TestCase):
    def test_wire_serves_every_menu_screen_with_no_registry_or_catalogue_read_and_no_write(self):
        for sid in MENUS:
            for depth in sl.DEPTHS:
                e = F.Env([F.STEW])
                o = sw.scaffold_menu(e, sid, depth)
                self.assertEqual((o["result"], o["writes"], o["screen"], o["depth_effective"]), ("OK", 0, sid, depth), (sid, depth))
                self.assertEqual(e.log, [])  # nothing at all was read from the environment: the screen is built from its own source table
                self.assertEqual((o["declaration_sha"], o["sources_sha"]), (META["file_of"][sid], SRC_SHA))
                self.assertIn("Presentation only", sv.render(o, depth))
                self.assertNotIn("Registry", text(sv.render(o, depth)))

    def test_refusals_and_the_noun_and_menu_entry_points_do_not_cross(self):
        e = F.Env([F.STEW])
        self.assertEqual(sw.scaffold_menu(e, "SCR.SERVICE.NOUN", "enable")["reason"], "UNKNOWN_SCREEN")
        self.assertEqual(sw.scaffold_menu(e, "SCR.NOPE.MENU", "enable")["reason"], "UNKNOWN_SCREEN")
        self.assertEqual(sw.scaffold_menu(e, "SCR.MESH_MEASURES.MENU", "deep")["reason"], "UNKNOWN_DEPTH")
        self.assertEqual(sw.scaffold_noun(e, "SCR.MESH_MEASURES.MENU", "enable")["reason"], "UNKNOWN_SCREEN")
        n = F.Env([])
        self.assertEqual(sw.scaffold_menu(n, "SCR.MESH_MEASURES.MENU", "enable")["reason"], "NO_RECOGNISED_ROLE"); self.assertEqual(n.log, [])

    def test_no_route_menu_or_manifest_change(self):
        c = open(os.path.join(F.ADDON, "controllers", "scaffold.py"), encoding="utf-8").read()
        self.assertEqual(c.count("@http.route"), 2)
        self.assertNotIn("screen_", open(os.path.join(F.ADDON, "__manifest__.py"), encoding="utf-8").read())
        for f in ("views/synapsys_menus.xml", "views/synapsys_screens.xml"):
            self.assertNotIn("scaffold_menu", open(os.path.join(F.ADDON, f), encoding="utf-8").read())


if __name__ == "__main__":
    unittest.main(verbosity=2)
