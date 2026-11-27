"""RC06c batch 2 offline tests: the 10 PROPOSAL and 2 OPEN noun declarations. Offline only; no Odoo, no network, no writes.
Acceptance checks 1 to 17 already run over EVERY declaration in test_screen_arch.py (ALL includes these 12 nouns); this file adds the
status-honesty tests (a PROPOSAL or OPEN noun says so, in the same positions and form as a RULED noun, and its answer never reads as
settled), per-noun provenance, the made-of rule, the wire and the Context consistency evidence (item 3 of the contract)."""
import copy, hashlib, html, json, os, re, subprocess, sys, unittest

import fakes as F
from fakes import sl, sd, sr, sw, sv

HERE = os.path.dirname(os.path.abspath(__file__))
DECLS, META = sd.load_declarations()
PROPOSAL = ["PURPOSE", "CAPABILITY", "CHAIN", "PARTNER", "METHOD", "WORK", "PATTERN", "SIGNAL", "CHANGE", "MARKET"]
OPEN = ["INDUSTRY", "PRODUCT"]
B2 = {"SCR.%s.NOUN" % n: DECLS["SCR.%s.NOUN" % n] for n in PROPOSAL + OPEN}
B1_SAMPLE = DECLS["SCR.SERVICE.NOUN"]  # a RULED noun, for form comparison
EL = sl.index_registry(F.REG)
ACTOR_S = {"groups": {"steward"}, "context_ids": set()}
B1_FILE_SHA = "2e278bc8c73f1bd20ddcd0c5549a40c037c1749f37f7a680b26047c7593290ff"
PRIMARY_SHA = "2aa425778fe3a7e2f20d242440c907161484318d3ea91a51120b5a8e31144fe0"


def project(decl, depth, reg=None, actor=ACTOR_S):
    ev, idx, _ = sw.collect_evidence(F.Env([F.STEW]))
    o = sd.project(decl, reg or F.REG, depth, actor, ev, idx, "1", sw.DEFAULT_ROLE_MAX_DEPTH)
    o.update({"registry_state": "candidate", "registry_sha": F.SHA})
    return o


def page(decl, depth, reg=None):
    return sr.render_screen(project(decl, depth, reg))


def text(h):
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", re.sub(r"<style>.*?</style>", "", h, flags=re.S)))).strip()


def expected_status(sid):
    return "OPEN" if sid.split(".")[1] in OPEN else "PROPOSAL"


def regstatus(reg, noun, status):
    reg = copy.deepcopy(reg)
    for e in reg["elements"]:
        if e["id"] == noun:
            if status is None:
                e.pop("status", None)
            else:
                e["status"] = status
    return reg


class B2_Set(unittest.TestCase):
    def test_exactly_the_twelve_nouns_the_registry_holds_as_proposal_or_open(self):
        non_ruled = {e["id"]: e["status"] for e in F.REG["elements"] if e["cls"] == "N" and e.get("status") != "RULED"}
        self.assertEqual(non_ruled, {"N." + n: expected_status("SCR.%s.NOUN" % n) for n in PROPOSAL + OPEN})
        self.assertEqual(len(B2), 12)
        for sid, d in B2.items():
            self.assertEqual((d["screen_type"], d["noun"], d["peers"], d["movement"]["verbs"]), ("noun", "N." + sid.split(".")[1], None, []))
            self.assertNotIn("record", d)
            self.assertEqual(len(d["claims"]), 1)

    def test_sibling_file_and_earlier_files_are_untouched(self):
        self.assertEqual(META["files"]["screen_declarations.json"], PRIMARY_SHA)
        self.assertEqual(META["files"]["screen_declarations_batch1.json"], B1_FILE_SHA)
        for sid in B2:
            self.assertEqual(META["file_of"][sid], META["files"]["screen_declarations_batch2.json"])
        self.assertTrue({d for d in DECLS if d.endswith('.NOUN') or d.endswith('.RECORD')} >= set(B2) | {'SCR.CONTEXT.NOUN', 'SCR.CONTEXT.RECORD', 'SCR.ASSET.RECORD'})
        self.assertEqual(len([d for d in DECLS.values() if d['screen_type'] != 'menu']), 3 + 15 + 12)

    def test_generator_is_reproducible_byte_for_byte(self):
        p = subprocess.run([sys.executable, os.path.join(HERE, "..", "tools", "gen_batch2_declarations.py"), F.FIXTURE], capture_output=True, text=True, timeout=60)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout, open(os.path.join(F.ADDON, "data", "screen_declarations_batch2.json"), encoding="utf-8").read())

    def test_registry_is_unchanged_and_pinned(self):
        self.assertEqual(hashlib.sha256(open(F.FIXTURE, "rb").read()).hexdigest(), F.REG_SHA)


class B2_Provenance(unittest.TestCase):
    def test_every_chip_quote_and_date_is_in_the_registry_text(self):
        for sid, d in B2.items():
            src = EL[d["noun"]]["definition_source"]
            for s in d["claims"][0]["sources"]:
                self.assertIn(s["quote"], src, (sid, s))
                if s["date"]:
                    self.assertIn(s["date"], src, (sid, s))

    def test_no_chip_is_dropped_on_the_real_registry(self):
        for sid, d in B2.items():
            o = project(d, "enrich")
            self.assertEqual(o["notes"], [], sid)
            self.assertEqual(o["frame"]["trust"]["source_count"], len(d["claims"][0]["sources"]), sid)

    def test_a_missing_quote_drops_and_notes_the_chip_and_the_screen_says_none_recorded(self):
        for sid, d in B2.items():
            reg = copy.deepcopy(F.REG)
            for e in reg["elements"]:
                if e["id"] == d["noun"]:
                    e["definition_source"] = "unrelated text"
            o = project(d, "enrich", reg)
            self.assertEqual((o["frame"]["trust"]["source_count"], len(o["notes"])), (0, len(d["claims"][0]["sources"])), sid)
            self.assertIn("None recorded", text(sr.render_screen(o)))

    def test_answer_citation_and_open_questions_are_the_registry_text_verbatim(self):
        for sid, d in B2.items():
            e = EL[d["noun"]]
            o = project(d, "enrich")
            self.assertEqual(o["frame"]["answer"], e["definition"])
            self.assertEqual(o["enrich"]["rows"][0]["full_citation"], e["definition_source"])
            self.assertEqual([q["text"] for q in o["enrich"]["rows"][0]["open"]], e.get("open_questions", []))
            h = html.unescape(page(d, "enrich"))
            for q in e.get("open_questions", []):
                self.assertEqual(h.count(q), 1, (sid, q))

    def test_chips_at_most_three_then_a_count(self):
        for sid, d in B2.items():
            n = len(d["claims"][0]["sources"])
            h = page(d, "enrich")
            cell = re.findall(r"<td>(.*?)</td>", re.search(r'<tr data-claim="meaning">.*?</tr>', h, re.S).group(0), re.S)[2]
            line = re.search(r"<div>(.*?)</div>", cell, re.S).group(1)
            self.assertEqual(len(re.findall(r'class="tg"', line)), min(3, n), sid)
            self.assertEqual("+%d" % (n - 3) in line, n > 3, sid)


class B2_StatusHonesty(unittest.TestCase):
    def test_status_text_equals_the_registrys_in_header_trust_line_and_status_cell(self):
        for sid, d in B2.items():
            st = EL[d["noun"]]["status"]
            self.assertEqual(st, expected_status(sid))
            for depth in sl.DEPTHS:
                o = project(d, depth)
                self.assertEqual((o["status"], o["frame"]["header"]["status"], o["frame"]["trust"]["status"]), (st, st, st), (sid, depth))
            h = page(d, "enrich")
            self.assertIn('<span class="tg">%s</span> %d source' % (st, len(d["claims"][0]["sources"])), h)
            self.assertEqual(project(d, "enrich")["enrich"]["rows"][0]["status"], st)
            cell = re.findall(r"<td>(.*?)</td>", re.search(r'<tr data-claim="meaning">.*?</tr>', h, re.S).group(0), re.S)[1]
            self.assertTrue(cell.startswith('<div><span class="tg">%s</span>' % st), (sid, cell[:80]))

    def test_same_position_and_form_as_a_ruled_noun(self):
        def form(x, status):  # the status word, digits and the noun's own wording blanked: only position and markup remain
            return re.sub(r"\d+", "n", x.replace(status, "STATUS"))
        ruled = page(B1_SAMPLE, "enrich")
        r_trust = re.search(r'<p class="tl" data-slot="trust">.*?</p>', ruled, re.S).group(0)
        r_cell = re.findall(r"<td>(.*?)</td>", re.search(r'<tr data-claim="meaning">.*?</tr>', ruled, re.S).group(0), re.S)[1]
        r_pill = re.search(r"<h1>.*?(<span class=\"tg\">RULED</span>)</h1>", ruled, re.S).group(1)
        for sid, d in B2.items():
            h = page(d, "enrich")
            st = expected_status(sid)
            trust = re.search(r'<p class="tl" data-slot="trust">.*?</p>', h, re.S).group(0)
            cell = re.findall(r"<td>(.*?)</td>", re.search(r'<tr data-claim="meaning">.*?</tr>', h, re.S).group(0), re.S)[1]
            self.assertEqual(form(trust, st), form(r_trust, "RULED"), sid)  # trust line: identical markup, only the status word differs
            self.assertTrue(form(cell, st).startswith(form(r_cell, "RULED")[:len('<div><span class="tg">STATUS</span>')]), sid)
            self.assertIn(r_pill.replace("RULED", st), re.search(r"<h1>.*?</h1>", h, re.S).group(0), sid)  # header pill: same class and place
            self.assertEqual(re.findall(r'data-slot="(\w+)"', h), re.findall(r'data-slot="(\w+)"', ruled), sid)  # same slots, same order, every depth
            self.assertEqual(h.count('class="tg">%s</span>' % st) >= 3, True)

    def test_no_screen_displays_a_ruled_looking_pill_for_the_noun_itself(self):
        for sid, d in B2.items():
            for depth in sl.DEPTHS:
                h = page(d, depth)
                outside_made_of = re.sub(r'<div data-slot="made_of">.*?(?=<div data-slot="peers">)', "", h, flags=re.S)
                self.assertNotIn("RULED", text(outside_made_of), (sid, depth))  # roles in Made of show OTHER nouns' own registry statuses
                if not d["made_of"]:
                    self.assertNotIn("RULED", text(h), (sid, depth))
                self.assertNotIn('class="tg req">RULED', h)

    def test_the_answer_line_leads_with_the_registry_status_and_never_reads_as_settled(self):
        for sid, d in B2.items():
            e = EL[d["noun"]]
            st = e["status"]
            for depth in sl.DEPTHS:
                h = page(d, depth)
                ans = re.search(r'data-slot="answer">(.*?)</p>', h, re.S).group(1)
                plain = html.unescape(re.sub(r"<[^>]+>", "", ans))
                self.assertTrue(plain.upper().startswith(st), (sid, depth, plain[:60]))
                self.assertTrue(plain.endswith(e["definition"]))
                lead = project(d, depth)["frame"].get("answer_lead")
                already = e["definition"].upper().startswith(st)
                self.assertEqual(lead, None if already else st, (sid, lead))
        self.assertTrue(EL["N.INDUSTRY"]["definition"].startswith("OPEN.") and EL["N.PRODUCT"]["definition"].startswith("OPEN:"))  # no "OPEN: OPEN." doubling

    def test_a_ruled_noun_gets_no_lead_and_the_status_is_read_not_assumed(self):
        for sid, d in B2.items():
            o = project(d, "enrich", regstatus(F.REG, d["noun"], "RULED"))
            self.assertEqual((o["frame"]["trust"]["status"], "answer_lead" in o["frame"]), ("RULED", False), sid)
            for st in ("PROPOSAL", "OPEN"):
                o = project(d, "enrich", regstatus(F.REG, d["noun"], st))
                self.assertEqual(o["frame"]["trust"]["status"], st)
                self.assertEqual(o["enrich"]["rows"][0]["status"], st)
            o = project(d, "enrich", regstatus(F.REG, d["noun"], None))
            self.assertEqual((o["frame"]["trust"]["status"], o["frame"]["answer_lead"]), (None, "UNSOURCED"), sid)
            self.assertIn("UNSOURCED", sr.render_screen(o))

    def test_the_lead_is_escaped_and_presentation_only(self):
        reg = regstatus(F.REG, "N.PURPOSE", "<script>x</script>")
        h = page(B2["SCR.PURPOSE.NOUN"], "enable", reg)
        self.assertNotIn("<script>x", h); self.assertIn("&lt;script&gt;x", h)

    def test_ruled_screens_are_unchanged_by_the_lead_rule(self):
        for sid, d in DECLS.items():
            if sid in B2 or d["screen_type"] != "noun":
                continue
            self.assertNotIn("answer_lead", project(d, "enable")["frame"], sid)
        for depth in sl.DEPTHS:
            o = sw.scaffold_context(F.Env([F.STEW]), depth, "1")
            self.assertEqual(sv.render(o, depth), open(os.path.join(HERE, "golden", "rc06a_context_noun_view_%s.html" % depth), encoding="utf-8").read())
            self.assertEqual(json.dumps(o, sort_keys=True, indent=1), open(os.path.join(HERE, "golden", "rc06a_context_noun_route_%s.json" % depth), encoding="utf-8").read())


class B2_Sections(unittest.TestCase):
    EXPECT = {"PURPOSE": "H.CTX", "CAPABILITY": "H.SVC", "WORK": "H.WRK", "PATTERN": "H.LRN", "SIGNAL": "H.SIG"}

    def test_made_of_is_declared_only_where_the_registry_names_the_noun_a_required_subject(self):
        got = {sid.split(".")[1]: (d["made_of"] or {}).get("relationship") for sid, d in B2.items()}
        self.assertEqual({k: v for k, v in got.items() if v}, self.EXPECT)
        for n in PROPOSAL + OPEN:  # independent re-derivation, not the generator's code
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
            self.assertEqual((self.EXPECT.get(n) if len(rels) == 1 else None), got[n], n)
            if len(rels) > 1:
                self.assertEqual((n, sorted(rels)), ("CHAIN", ["H.BEN", "H.PRG"]))  # the one ambiguous noun: none chosen

    def test_made_of_rows_are_registry_roles_without_codes(self):
        for sid, d in B2.items():
            if not d["made_of"]:
                self.assertIn("No roles are declared for this screen.", page(d, "enhance"), sid)
                continue
            h = page(d, "enhance")
            made = h[h.index('data-slot="made_of"'):h.index('data-slot="peers"')].split(">", 1)[1]
            self.assertEqual(len(project(d, "enhance")["enhance"]["made_of"]["rows"]), len(sl.roles_for(F.REG, EL, d["made_of"]["relationship"])))
            self.assertIsNone(re.search(r"R\.[A-Z]+_|H\.[A-Z]{3}|MC-[0-9a-f]{6}|_|\+", text(made)), (sid, text(made)[:160]))

    def test_no_peers_no_verbs_no_stage_full_ladder(self):
        for sid, d in B2.items():
            self.assertIn("No linked peers are declared for this screen.", page(d, "enhance"))
            self.assertNotIn("SP-01", page(d, "enrich"))
            for depth in sl.DEPTHS:
                o = project(d, depth)
                self.assertEqual((o["depth_effective"], o["depth_clamped"], o["stage"]), (depth, False, None))
                self.assertIn("HOLD", text(page(d, depth))); self.assertIn("verbs not yet bound", page(d, depth))

    def test_none_recorded_sections_follow_the_registry(self):
        for sid, d in B2.items():
            n = len(EL[d["noun"]].get("open_questions", []))
            h = page(d, "enrich")
            self.assertEqual("none recorded" in h, n == 0, sid)
            self.assertEqual("(%d open)" % n in h, n > 0, sid)

    def test_noun_screens_say_nothing_about_records_beyond_the_registrys_own_text(self):
        # Capability, Product, Change (and Workflow in batch 1) have no V20 record model: remove every registry-derived string, then no mention of "record" may remain
        for n in ("CAPABILITY", "PRODUCT", "CHANGE"):
            d = DECLS["SCR.%s.NOUN" % n]; e = EL["N." + n]
            h = text(page(d, "enrich"))
            for s in sorted([e["definition"], e["definition_source"], e.get("kind", "")] + list(e.get("open_questions", [])), key=len, reverse=True):
                h = h.replace(html.unescape(s), "")
            if d["made_of"]:
                for r in sl.roles_for(F.REG, EL, d["made_of"]["relationship"]):
                    h = h.replace(r["bound_label"], "")
            self.assertNotIn("record", h.lower(), n)

    def test_enable_holds_nothing_from_deeper_depths_and_client_gets_no_enrich(self):
        for sid, d in B2.items():
            o = project(d, "enable")
            self.assertEqual(set(o) & {"enhance", "enrich"}, set())
            self.assertNotIn(EL[d["noun"]]["definition_source"], json.dumps(o))
            c = sd.project(d, F.REG, "enrich", {"groups": {"client"}, "context_ids": set()}, [], {}, "1", None)
            self.assertEqual((c["depth_effective"], c["clamp_reason"], "enrich" in c), ("enhance", "role", False))


class B2_Wire(unittest.TestCase):
    def test_wire_serves_every_batch2_screen_read_only_with_its_own_file_fingerprint(self):
        for sid in B2:
            for depth in sl.DEPTHS:
                e = F.Env([F.STEW])
                o = sw.scaffold_noun(e, sid, depth, "1")
                self.assertEqual((o["result"], o["writes"], o["screen"]), ("OK", 0, sid))
                self.assertEqual(o["declaration_sha"], META["file_of"][sid])
                self.assertEqual(sorted(set(x[0] for x in e.log)), ["search", "search_cat"])

    def test_no_route_menu_or_manifest_change(self):
        c = open(os.path.join(F.ADDON, "controllers", "scaffold.py"), encoding="utf-8").read()
        self.assertEqual(c.count("@http.route"), 2)
        self.assertNotIn("screen_declarations", open(os.path.join(F.ADDON, "__manifest__.py"), encoding="utf-8").read())


class B2_ContextConsistencyEvidence(unittest.TestCase):
    """Contract item 3: report only. These tests pin the CURRENT facts the return reports; Context is not changed in this batch."""

    def test_the_context_service_chip_and_what_the_registry_text_holds(self):
        primary = json.load(open(sd.DEFAULT_PATH, encoding="utf-8"))
        chips = [(s["id"], c["id"], x) for s in primary["screens"] for c in s["claims"] if c["id"] == "peer.service" for x in c["sources"] if x["quote"] == "10:51 (KDA seats"]
        self.assertEqual([(a, b) for a, b, _ in chips], [("SCR.CONTEXT.NOUN", "peer.service"), ("SCR.CONTEXT.RECORD", "peer.service")])
        for _, _, x in chips:
            self.assertEqual((x["name"], x["date"]), ("Ledger", "20 Nov 10:51"))
        src = EL["N.SERVICE"]["definition_source"]
        self.assertIn("ledger 20 Nov 07:06 (Service Catalogue is the key interface), 10:51 (KDA seats", src)
        self.assertNotIn("20 Nov 10:51", src)  # the registry text never writes that date; the chip inherits it from the preceding entry
        b1 = [c for c in DECLS["SCR.SERVICE.NOUN"]["claims"][0]["sources"] if c["quote"] == "10:51 (KDA seats"]
        self.assertEqual((b1[0]["name"], b1[0]["date"]), ("Ledger", "10:51"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
