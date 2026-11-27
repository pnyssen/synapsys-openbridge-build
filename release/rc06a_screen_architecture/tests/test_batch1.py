"""RC06b batch 1 offline tests: the 15 RULED noun declarations. Offline only; no Odoo, no network, no writes.
Acceptance checks 1 to 17 already run over EVERY declaration in test_screen_arch.py (ALL now includes the 15 nouns); this file adds the
batch-specific tests: per-noun provenance, status, Context byte-identity, the Mesh shared declaration, the sibling-file loader and the
generator's reproducibility."""
import copy, hashlib, html, json, os, re, subprocess, sys, unittest

import fakes as F
from fakes import sl, sd, sr, sw, sv

HERE = os.path.dirname(os.path.abspath(__file__))
DECLS, META = sd.load_declarations()
NOUNS = ["STRATEGY", "PORTFOLIO", "OFFERING", "SHAPE", "DOMAIN", "CANONICAL", "PROGRAMME", "PROJECT", "SERVICE", "WORKFLOW", "OUTCOME", "BENEFIT", "ASSET", "FRACTAL", "MESH"]
BATCH = {"SCR.%s.NOUN" % n: DECLS["SCR.%s.NOUN" % n] for n in NOUNS}
EL = sl.index_registry(F.REG)
RC06A_PRIMARY_SHA = "2aa425778fe3a7e2f20d242440c907161484318d3ea91a51120b5a8e31144fe0"
ACTOR_S = {"groups": {"steward"}, "context_ids": set()}


def project(decl, depth, reg=None, actor=ACTOR_S):
    ev, idx, _ = sw.collect_evidence(F.Env([F.STEW]))
    o = sd.project(decl, reg or F.REG, depth, actor, ev, idx, "1", sw.DEFAULT_ROLE_MAX_DEPTH)
    o.update({"registry_state": "candidate", "registry_sha": F.SHA})
    return o


def page(decl, depth, reg=None):
    return sr.render_screen(project(decl, depth, reg))


def text(h):
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", re.sub(r"<style>.*?</style>", "", h, flags=re.S)))).strip()


class Batch_Set(unittest.TestCase):
    def test_exactly_the_fifteen_nouns_as_noun_screens(self):
        self.assertEqual(len(BATCH), 15)
        for sid, d in BATCH.items():
            self.assertEqual((d["screen_type"], d["noun"]), ("noun", "N." + sid.split(".")[1]))
            self.assertNotIn("record", d)  # a noun screen has no stage and no record block
            self.assertEqual(len(d["claims"]), 1)
            self.assertTrue(all(c["type"] == "element" for c in d["claims"]))

    def test_the_rc06a_file_is_byte_identical_and_batch1_is_a_sibling_file(self):
        self.assertEqual(META["sha256"], RC06A_PRIMARY_SHA)
        self.assertEqual(sorted(META["files"]), ["screen_declarations.json", "screen_declarations_batch1.json"])
        self.assertEqual(META["files"]["screen_declarations.json"], RC06A_PRIMARY_SHA)
        for sid in BATCH:
            self.assertEqual(META["file_of"][sid], META["files"]["screen_declarations_batch1.json"])
        for sid in ("SCR.CONTEXT.NOUN", "SCR.CONTEXT.RECORD", "SCR.ASSET.RECORD"):
            self.assertEqual(META["file_of"][sid], RC06A_PRIMARY_SHA)

    def test_every_batch_noun_exists_in_registry_0_3_5_as_a_RULED_noun_with_text(self):
        for d in BATCH.values():
            e = EL[d["noun"]]
            self.assertEqual((e["cls"], e.get("status")), ("N", "RULED"))
            self.assertTrue(e.get("definition") and e.get("definition_source"))

    def test_generator_is_reproducible_byte_for_byte(self):
        p = subprocess.run([sys.executable, os.path.join(HERE, "..", "tools", "gen_batch1_declarations.py"), F.FIXTURE], capture_output=True, text=True, timeout=60)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout, open(os.path.join(F.ADDON, "data", "screen_declarations_batch1.json"), encoding="utf-8").read())

    def test_registry_0_3_5_is_unchanged_and_pinned(self):
        self.assertEqual(hashlib.sha256(open(F.FIXTURE, "rb").read()).hexdigest(), "7c31aa1de4c97e8e062c5ae9e2f907b4c67ea0949bf143235499c32b1a30f423")


class Batch_Provenance(unittest.TestCase):
    def test_every_chip_quote_is_in_the_registry_text_and_no_date_is_invented(self):
        for sid, d in BATCH.items():
            src = EL[d["noun"]]["definition_source"]
            for s in d["claims"][0]["sources"]:
                self.assertIn(s["quote"], src, (sid, s))
                if s["date"]:
                    self.assertIn(s["date"], src, (sid, s))  # the date is written in the registry text, never inherited or inferred
                    self.assertTrue(re.search(r"\d{2}:\d{2}|\d{1,2} Nov", s["date"]), s)

    def test_no_chip_is_dropped_on_the_real_registry_and_the_count_is_what_the_screen_says(self):
        for sid, d in BATCH.items():
            o = project(d, "enrich")
            self.assertEqual(o["notes"], [], sid)
            self.assertEqual(o["frame"]["trust"]["source_count"], len(d["claims"][0]["sources"]), sid)
            self.assertEqual(o["enrich"]["rows"][0]["source_count"], len(d["claims"][0]["sources"]))

    def test_a_chip_whose_quote_is_missing_is_dropped_and_noted_for_every_noun(self):
        for sid, d in BATCH.items():
            reg = copy.deepcopy(F.REG)
            for e in reg["elements"]:
                if e["id"] == d["noun"]:
                    e["definition_source"] = "unrelated text"
            o = project(d, "enrich", reg)
            self.assertEqual(o["frame"]["trust"]["source_count"], 0, sid)
            self.assertEqual(len(o["notes"]), len(d["claims"][0]["sources"]), sid)
            self.assertIn("None recorded", text(sr.render_screen(o)), sid)

    def test_chips_show_at_most_three_then_a_count_and_the_full_list_is_on_request(self):
        for sid, d in BATCH.items():
            n = len(d["claims"][0]["sources"])
            h = page(d, "enrich")
            row = re.search(r'<tr data-claim="meaning">.*?</tr>', h, re.S).group(0)
            cell = re.findall(r"<td>(.*?)</td>", row, re.S)[2]
            line = re.search(r"<div>(.*?)</div>", cell, re.S).group(1)
            self.assertEqual(len(re.findall(r'class="tg"', line)), min(3, n), sid)
            self.assertEqual("+%d" % (n - 3) in line, n > 3, sid)
            self.assertIn("full citation", cell)
            for s in d["claims"][0]["sources"]:
                self.assertIn(html.escape(s["name"] + ((" " + s["date"]) if s["date"] else "")), cell, (sid, s))

    def test_the_answer_and_the_full_citation_are_the_registry_text_verbatim(self):
        for sid, d in BATCH.items():
            e = EL[d["noun"]]
            o = project(d, "enrich")
            self.assertEqual(o["frame"]["answer"], e["definition"])
            self.assertEqual(o["enrich"]["rows"][0]["full_citation"], e["definition_source"])
            self.assertEqual([q["text"] for q in o["enrich"]["rows"][0]["open"]], e.get("open_questions", []))
            self.assertIn(html.escape(e["definition_source"], quote=True), page(d, "enrich"))


class Batch_Status(unittest.TestCase):
    def test_status_is_read_from_the_registry_never_assumed(self):
        for sid, d in BATCH.items():
            for status in ("RULED", "PROPOSAL", "OPEN", None):
                reg = copy.deepcopy(F.REG)
                for e in reg["elements"]:
                    if e["id"] == d["noun"]:
                        if status is None:
                            e.pop("status", None)
                        else:
                            e["status"] = status
                o = project(d, "enrich", reg)
                self.assertEqual(o["frame"]["trust"]["status"], status, (sid, status))
                self.assertEqual(o["enrich"]["rows"][0]["status"], status)
                h = sr.render_screen(o)
                # the noun's own status: header pill, trust line and its trust-table row (roles in Made of show OTHER nouns' own statuses)
                own = re.search(r'data-slot="header">.*?</h1>', h, re.S).group(0) + re.search(r'data-slot="trust">.*?</p>', h, re.S).group(0) \
                    + re.search(r'<tr data-claim="meaning">.*?</tr>', h, re.S).group(0)
                self.assertEqual("RULED" in text(own), status == "RULED", (sid, status))
                if status:
                    self.assertGreaterEqual(own.count('<span class="tg">%s</span>' % status), 3, (sid, status))
                else:
                    self.assertGreaterEqual(own.count("UNSOURCED"), 2)

    def test_ruled_is_shown_on_the_real_registry_for_all_fifteen(self):
        for sid, d in BATCH.items():
            self.assertIn('<span class="tg">RULED</span> %d source' % len(d["claims"][0]["sources"]), page(d, "enable"))


class Batch_Context_Golden(unittest.TestCase):
    def test_context_output_is_byte_identical_to_rc06a(self):
        for depth in sl.DEPTHS:
            o = sw.scaffold_context(F.Env([F.STEW]), depth, "1")
            self.assertEqual(sv.render(o, depth), open(os.path.join(HERE, "golden", "rc06a_context_noun_view_%s.html" % depth), encoding="utf-8").read(), depth)
            self.assertEqual(json.dumps(o, sort_keys=True, indent=1), open(os.path.join(HERE, "golden", "rc06a_context_noun_route_%s.json" % depth), encoding="utf-8").read(), depth)

    def test_the_two_context_record_declarations_are_untouched_too(self):
        primary = json.load(open(sd.DEFAULT_PATH, encoding="utf-8"))
        self.assertEqual([s["id"] for s in primary["screens"]], ["SCR.CONTEXT.NOUN", "SCR.CONTEXT.RECORD", "SCR.ASSET.RECORD"])
        self.assertEqual(hashlib.sha256(open(sd.DEFAULT_PATH, "rb").read()).hexdigest(), RC06A_PRIMARY_SHA)


class Batch_Sections(unittest.TestCase):
    def test_no_peers_are_declared_and_none_are_invented(self):
        for sid, d in BATCH.items():
            self.assertIsNone(d["peers"], sid)
            self.assertIn("No linked peers are declared for this screen.", page(d, "enhance"))
            self.assertNotIn("SP-01", page(d, "enrich"), sid)  # no catalogue evidence leaks into a screen that declares no peer
            self.assertNotIn("CATALOGUE RECORD FOUND", page(d, "enrich"), sid)

    def test_made_of_is_declared_only_where_the_registry_names_the_noun_as_a_required_subject(self):
        expect = {"OFFERING": "H.OFR", "PROGRAMME": "H.PRG", "SERVICE": "H.SVC", "OUTCOME": "H.OUT", "BENEFIT": "H.BEN", "ASSET": "H.AST", "FRACTAL": "H.FRC"}
        got = {sid.split(".")[1]: (d["made_of"] or {}).get("relationship") for sid, d in BATCH.items()}
        self.assertEqual({k: v for k, v in got.items() if v}, expect)
        # independent re-derivation from the registry (not the generator's code)
        for n in NOUNS:
            noun = "N." + n
            rels = set()
            for c in F.REG["clusters"]:
                rel = [ref for role, ref in c["members"] if role == "relationship"]
                if not rel or any((EL.get(ref) or {}).get("cls") == "V" for role, ref in c["members"]):
                    continue
                for role, ref in c["members"]:
                    r = EL.get(role) or {}
                    if role != "relationship" and ref == noun and r.get("required") and str(r.get("label", "")).rstrip("+") == EL[noun]["label"].lower():
                        rels.add(rel[0])
            self.assertEqual((expect.get(n) if len(rels) == 1 else None), got[n], n)
        self.assertEqual({n for n in NOUNS if got[n] is None and n not in ("PORTFOLIO", "DOMAIN", "SHAPE")}, {"STRATEGY", "CANONICAL", "PROJECT", "WORKFLOW", "MESH"})

    def test_made_of_rows_are_the_registry_roles_with_plain_names_and_no_codes(self):
        for sid, d in BATCH.items():
            if not d["made_of"]:
                self.assertIn("No roles are declared for this screen.", page(d, "enhance"), sid)
                continue
            o = project(d, "enhance")
            rows = o["enhance"]["made_of"]["rows"]
            self.assertEqual(len(rows), len(sl.roles_for(F.REG, EL, d["made_of"]["relationship"])), sid)
            h = page(d, "enhance")
            made = h[h.index('data-slot="made_of"'):h.index('data-slot="peers"')].split(">", 1)[1]
            self.assertIsNone(re.search(r"R\.[A-Z]+_|H\.[A-Z]{3}|MC-[0-9a-f]{6}|_|\+", text(made)), (sid, text(made)[:200]))
            self.assertLess(made.index("required"), made.index("optional") if "optional" in made else 10**9)

    def test_sections_that_say_none_recorded(self):
        outcome = page(BATCH["SCR.OUTCOME.NOUN"], "enrich")
        self.assertIn("none recorded", outcome)  # the registry holds no open question for Outcome
        self.assertNotIn("(0 open)", outcome)
        for sid, d in BATCH.items():
            n = len(EL[d["noun"]].get("open_questions", []))
            h = page(d, "enrich")
            self.assertEqual("none recorded" in h, n == 0, sid)
            self.assertEqual("(%d open)" % n in h, n > 0, sid)

    def test_each_open_question_appears_once_on_each_screen(self):
        for sid, d in BATCH.items():
            h = html.unescape(page(d, "enrich"))
            for q in EL[d["noun"]].get("open_questions", []):
                self.assertEqual(h.count(q), 1, (sid, q))

    def test_the_depth_ladder_is_full_and_there_is_no_stage_or_not_applicable_notice(self):
        for sid, d in BATCH.items():
            for depth in sl.DEPTHS:
                o = project(d, depth)
                self.assertEqual((o["depth_effective"], o["depth_clamped"], o["stage"]), (depth, False, None), (sid, depth))
                h = sr.render_screen(o)
                self.assertIn("Stage: none (a noun screen has no stage)", h)
                self.assertNotIn("Not applicable", h)

    def test_enable_holds_nothing_from_deeper_depths(self):
        for sid, d in BATCH.items():
            o = project(d, "enable")
            self.assertEqual(set(o) & {"enhance", "enrich"}, set())
            blob = json.dumps(o)
            self.assertNotIn(EL[d["noun"]]["definition_source"], blob)
            for q in EL[d["noun"]].get("open_questions", []):
                self.assertNotIn(q, blob)

    def test_client_role_never_gets_enrich_content(self):
        for sid, d in BATCH.items():
            o = sd.project(d, F.REG, "enrich", {"groups": {"client"}, "context_ids": set()}, [], {}, "1", None)
            self.assertEqual((o["depth_effective"], o["clamp_reason"]), ("enhance", "role"), sid)
            self.assertNotIn("enrich", o)
            self.assertNotIn(EL[d["noun"]]["definition_source"], json.dumps(o))


class Batch_Mesh(unittest.TestCase):
    def test_mesh_is_one_declaration_shared_by_four_screens_with_no_verbs(self):
        m = DECLS["SCR.MESH.NOUN"]
        self.assertEqual(m["serves"], ["Registry", "Elements", "Clusters", "Verbs"])
        self.assertEqual(m["movement"]["verbs"], [])
        self.assertEqual([i for i, d in DECLS.items() if d.get("serves")], ["SCR.MESH.NOUN"])
        for depth in sl.DEPTHS:
            mv = re.search(r'data-slot="movement">(.*?)</p>', page(m, depth), re.S).group(1)
            self.assertIn("HOLD", mv); self.assertIn("verbs not yet bound", mv)

    def test_no_declaration_in_the_batch_binds_a_verb(self):
        for sid, d in BATCH.items():
            self.assertEqual(d["movement"]["verbs"], [], sid)
            self.assertIn("verbs not yet bound", page(d, "enable"), sid)

    def test_serves_is_validated(self):
        for bad in ([], "Registry", [""], [1]):
            m = copy.deepcopy(DECLS["SCR.MESH.NOUN"]); m["serves"] = bad
            self.assertTrue(any("serves" in e for e in sd.validate_screen(m)), bad)


class Batch_Loader(unittest.TestCase):
    def write(self, tmp, name, screens):
        p = os.path.join(tmp, name)
        json.dump({"schema": "synapsys.screen.declaration/1", "slots": {k: list(v) for k, v in sd.KNOWN_SLOTS.items()}, "screens": screens}, open(p, "w"))
        return p

    def test_a_screen_id_may_not_be_declared_twice_across_files(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            a = self.write(tmp, "a.json", [BATCH["SCR.MESH.NOUN"]])
            b = self.write(tmp, "b.json", [BATCH["SCR.MESH.NOUN"]])
            with self.assertRaises(ValueError) as cm:
                sd.load_declarations([a, b])
            self.assertIn("declared twice", str(cm.exception))

    def test_each_screen_reports_the_hash_of_its_own_file_and_one_bad_file_refuses_all(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            a = self.write(tmp, "a.json", [BATCH["SCR.MESH.NOUN"]])
            b = self.write(tmp, "b.json", [BATCH["SCR.ASSET.NOUN"]])
            decls, meta = sd.load_declarations([a, b])
            self.assertEqual(meta["file_of"]["SCR.MESH.NOUN"], hashlib.sha256(open(a, "rb").read()).hexdigest())
            self.assertEqual(meta["file_of"]["SCR.ASSET.NOUN"], hashlib.sha256(open(b, "rb").read()).hexdigest())
            bad = copy.deepcopy(BATCH["SCR.ASSET.NOUN"]); bad["screen_type"] = "page"
            c = self.write(tmp, "c.json", [bad])
            with self.assertRaises(ValueError):
                sd.load_declarations([a, c])

    def test_wire_serves_every_noun_screen_at_all_depths_read_only(self):
        for sid in BATCH:
            for depth in sl.DEPTHS:
                e = F.Env([F.STEW])
                o = sw.scaffold_noun(e, sid, depth, "1")
                self.assertEqual((o["result"], o["writes"], o["screen"], o["depth_effective"]), ("OK", 0, sid, depth), (sid, depth))
                self.assertEqual(o["declaration_sha"], META["file_of"][sid])
                self.assertEqual(sorted(set(x[0] for x in e.log)), ["search", "search_cat"])
                self.assertIn("Presentation only", sv.render(o, depth))

    def test_wire_refuses_record_screens_unknown_ids_bad_depth_and_no_role(self):
        e = F.Env([F.STEW])
        self.assertEqual(sw.scaffold_noun(e, "SCR.CONTEXT.RECORD", "enable")["reason"], "UNKNOWN_SCREEN")
        self.assertEqual(sw.scaffold_noun(e, "SCR.NOPE.NOUN", "enable")["reason"], "UNKNOWN_SCREEN")
        self.assertEqual(sw.scaffold_noun(e, "SCR.MESH.NOUN", "deep")["reason"], "UNKNOWN_DEPTH")
        n = F.Env([])
        self.assertEqual(sw.scaffold_noun(n, "SCR.MESH.NOUN", "enable")["reason"], "NO_RECOGNISED_ROLE"); self.assertEqual(n.log, [])

    def test_no_route_menu_or_manifest_change(self):
        c = open(os.path.join(F.ADDON, "controllers", "scaffold.py"), encoding="utf-8").read()
        self.assertEqual(c.count("@http.route"), 2)
        self.assertNotIn("screen_declarations", open(os.path.join(F.ADDON, "__manifest__.py"), encoding="utf-8").read())
        for f in ("views/synapsys_menus.xml", "views/synapsys_screens.xml"):
            self.assertNotIn("scaffold_noun", open(os.path.join(F.ADDON, f), encoding="utf-8").read())


if __name__ == "__main__":
    unittest.main(verbosity=2)
