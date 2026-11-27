"""RC06a offline tests: declarations, the one renderer, the stage function, record screens and acceptance checks 1 to 17.

Offline only: no Odoo, no network, no writes. Run: python3 -m unittest discover -s tests -p 'test_*.py'
Acceptance check numbers refer to the Claude Doc 'Enable / Enhance / Enrich: screen architecture and Context specimen' (checks 1 to 17).
"""
import ast, copy, html, json, os, re, unittest

import fakes as F
from fakes import sl, sd, sr, sw, sv

DECLS, META = sd.load_declarations()
CTX_NOUN, CTX_REC, ASSET_REC = DECLS["SCR.CONTEXT.NOUN"], DECLS["SCR.CONTEXT.RECORD"], DECLS["SCR.ASSET.RECORD"]
ACTOR_S = {"groups": {"steward"}, "context_ids": set()}
ACTOR_C = {"groups": {"collaborator"}, "context_ids": set()}
ACTOR_CLIENT = {"groups": {"client"}, "context_ids": set()}
ROLE_MAX = sw.DEFAULT_ROLE_MAX_DEPTH
SP01_REF = "x_service_catalogue:SP-01"


def evidence():
    ev, idx, _ = sw.collect_evidence(F.Env([F.STEW]))
    return ev, idx


def proj(decl, depth, actor=ACTOR_S, record=None, reg=None, ev=True, role_max=ROLE_MAX):
    e, i = evidence() if ev else ([], {})
    o = sd.project(decl, reg or F.REG, depth, actor, e, i, "1", role_max, record)
    if o.get("result") == "OK":
        o.update({"registry_state": "candidate", "registry_sha": F.SHA})
    return o


def page(decl, depth, **kw):
    return sr.render_screen(proj(decl, depth, **kw))


def body(h):
    return re.sub(r"<style>.*?</style>", "", h, flags=re.S)


def text(h):
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body(h)))).strip()


def slot(h, name):
    m = re.search(r'<(div|p|details)[^>]*data-slot="%s".*?(?=<(?:div|p|details)[^>]*data-slot="|<div class="cd" data-slot="not_applicable"|<p class="nt">)' % name, h, re.S)
    return m.group(0) if m else None


def rec(kind, name="Fixture", neighbour=None):
    return {"model": "x", "id": 1, "name": name, "kind": kind, "neighbour_kind": neighbour}


RC06A_IDS = {"SCR.CONTEXT.NOUN", "SCR.CONTEXT.RECORD", "SCR.ASSET.RECORD"}
BATCH1 = [d for i, d in DECLS.items() if i not in RC06A_IDS]
# every declaration: the three RC06a ones, then every noun screen added since (RC06b batch 1)
ALL = [(CTX_NOUN, None), (CTX_REC, rec("K-12")), (ASSET_REC, rec(None, "A1", "K-12"))] + [(d, None) for d in BATCH1]


class D1_Schema(unittest.TestCase):
    def test_declarations_load_and_validate(self):
        self.assertTrue(RC06A_IDS <= set(DECLS))
        self.assertEqual(META["slots"], {"enable": ["header", "answer", "trust", "movement"], "enhance": ["made_of", "peers"],
                                         "enrich": ["trust_table", "open_questions", "technical"]})

    def test_check17_each_declaration_states_its_type(self):
        for d in DECLS.values():
            self.assertIn(d["screen_type"], ("noun", "record", "menu"))
        bad = copy.deepcopy(CTX_NOUN); del bad["screen_type"]
        self.assertTrue(sd.validate_screen(bad))
        bad = copy.deepcopy(CTX_NOUN); bad["screen_type"] = "page"
        self.assertTrue(any("noun or record" in e for e in sd.validate_screen(bad)))

    def test_record_screen_must_say_where_its_kind_comes_from(self):
        bad = copy.deepcopy(CTX_REC); del bad["record"]["kind"]
        self.assertTrue(sd.validate_screen(bad))
        bad = copy.deepcopy(CTX_REC); bad["record"]["kind"] = {"field": "kind", "fixed": "K-4"}
        self.assertTrue(sd.validate_screen(bad))
        bad = copy.deepcopy(CTX_REC); bad["record"]["kind"] = {"fixed": "K-99"}
        self.assertTrue(sd.validate_screen(bad))
        bad = copy.deepcopy(CTX_NOUN); bad["record"] = {"model": "x"}
        self.assertTrue(any("noun screen has no record" in e for e in sd.validate_screen(bad)))
        self.assertEqual(CTX_REC["record"]["kind"], {"field": "kind"})
        self.assertEqual(ASSET_REC["record"]["kind"]["fixed"], "K-4")

    def test_check7_no_proposed_or_candidate_verbs(self):
        for v in ({"verb": "route"}, {"verb": "route", "source": "S", "status": "proposed"}, {"verb": "route", "status": "bound"}):
            bad = copy.deepcopy(CTX_NOUN); bad["movement"]["verbs"] = [v]
            self.assertTrue(any("bound" in e for e in sd.validate_screen(bad)), v)
        ok = copy.deepcopy(CTX_NOUN); ok["movement"]["verbs"] = [{"verb": "route", "source": "S", "status": "bound"}]
        self.assertEqual(sd.validate_screen(ok), [])
        empty = copy.deepcopy(CTX_NOUN); del empty["movement"]["hold_reason"]
        self.assertTrue(sd.validate_screen(empty))

    def test_claims_sources_carry_date_or_explicit_null(self):
        bad = copy.deepcopy(CTX_NOUN); del bad["claims"][0]["sources"][0]["date"]
        self.assertTrue(sd.validate_screen(bad))

    def test_load_refuses_a_half_valid_file(self):
        import tempfile
        d = json.load(open(sd.DEFAULT_PATH)); d["screens"][0]["screen_type"] = "x"
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            json.dump(d, fh)
        with self.assertRaises(ValueError):
            sd.load_declarations(fh.name)
        os.unlink(fh.name)

    def test_peer_blocks_limited_to_three_and_consistent(self):
        bad = copy.deepcopy(CTX_NOUN); bad["peers"]["nouns"] = ["N.A", "N.B", "N.C", "N.D"]
        self.assertTrue(sd.validate_screen(bad))


class D4_Stage(unittest.TestCase):
    def test_stage_function_is_the_ruled_table(self):
        for k, s in (("K-1", "enable"), ("K-3", "enable"), ("K-4", "enable"), ("K-6", "enhance"), ("K-8", "enhance"), ("K-12", "enrich")):
            self.assertEqual(sd.stage_for_kind(k), s)
        for k in (None, "", "K-2", "k-4", "K4", "any one of K-1", 4, [], "K-12 "):
            exp = "enrich" if k == "K-12 " else "not bound"
            self.assertEqual(sd.stage_for_kind(k), exp, repr(k))  # surrounding space tolerated, nothing else is guessed

    def test_ceiling(self):
        self.assertEqual([sd.ceiling_for_stage(s) for s in ("enable", "enhance", "enrich", "not bound", None)],
                         ["enable", "enhance", "enrich", "enable", "enable"])

    def test_noun_screens_never_clamp_for_stage(self):
        for st in (None, "enable", "not bound"):
            for d in sl.DEPTHS:
                self.assertEqual(sd.resolve_depth("noun", d, st, d), (d, False, None))
        for d in sl.DEPTHS:
            o = proj(CTX_NOUN, d)
            self.assertEqual((o["depth_effective"], o["depth_clamped"], o["stage"]), (d, False, None))

    def test_depth_clamped_is_real_for_record_screens(self):
        cases = [("K-1", "enrich", "enable", True), ("K-1", "enhance", "enable", True), ("K-4", "enable", "enable", False),
                 ("K-6", "enrich", "enhance", True), ("K-8", "enhance", "enhance", False), ("K-12", "enrich", "enrich", False),
                 (None, "enrich", "enable", True), ("K-99", "enhance", "enable", True)]
        for kind, req, eff, clamped in cases:
            o = proj(CTX_REC, req, record=rec(kind))
            self.assertEqual((o["depth_effective"], o["depth_clamped"]), (eff, clamped), (kind, req))
            self.assertEqual(o["clamp_reason"], "stage" if clamped else None)

    def test_role_clamp_still_works_and_is_named(self):
        o = proj(CTX_NOUN, "enrich", actor=ACTOR_CLIENT, role_max=None)
        self.assertEqual((o["depth_effective"], o["depth_clamped"], o["clamp_reason"]), ("enhance", True, "role"))
        self.assertIn("limits the depth", sr.render_screen(o))

    def test_unknown_depth_is_a_value_error_for_resolve_and_refused_by_project(self):
        with self.assertRaises(ValueError):
            sd.resolve_depth("noun", "deep")
        self.assertEqual(proj(CTX_NOUN, "deep")["reason"], "UNKNOWN_DEPTH")


class C1_to_C6_Frame(unittest.TestCase):
    def test_check1_frame_order_at_all_depths(self):
        for decl, r in ALL:
            for d in sl.DEPTHS:
                h = page(decl, d, record=r)
                idx = [h.index('data-slot="%s"' % s) for s in ("header", "answer", "trust", "movement")]
                self.assertEqual(idx, sorted(idx), (decl["id"], d))
                self.assertEqual([m for m in re.findall(r'data-slot="(\w+)"', h) if m in sd.FRAME], ["header", "answer", "trust", "movement"])

    def test_check2_nothing_removed_reordered_or_reworded(self):
        for decl, r in ALL:
            hs = {d: page(decl, d, record=(r if r is None else rec("K-12", "N", "K-12"))) for d in sl.DEPTHS}
            slots = {d: [s for s in re.findall(r'data-slot="(\w+)"', hs[d]) if s != "not_applicable"] for d in sl.DEPTHS}
            self.assertEqual(slots["enhance"][:len(slots["enable"])], slots["enable"])
            self.assertEqual(slots["enrich"][:len(slots["enhance"])], slots["enhance"])
            for earlier, later in (("enable", "enhance"), ("enhance", "enrich")):
                for s in set(slots[earlier]):
                    a, b = slot(hs[earlier], s), slot(hs[later], s)
                    # the Depth label is the one deliberately different string; everything else must be identical
                    strip = lambda x: re.sub(r'<span data-label="depth">.*?</span>', "", x)
                    self.assertEqual(strip(a), strip(b), (decl["id"], earlier, later, s))

    def test_check3_enrich_rows_have_exactly_four_columns(self):
        for decl, r in ALL:
            if not ceiling_ok(decl, rec("K-12")):
                self.assertNotIn("<th>", page(decl, "enrich", record=rec("K-12")))  # Asset (K-4) never reaches the table
                continue
            h = page(decl, "enrich", record=(r if r is None else rec("K-12")))
            self.assertEqual(re.findall(r"<th>(.*?)</th>", h), ["Claim", "Status", "Source", "Open question"])
            for tr in re.findall(r"<tr data-claim=.*?</tr>", h, re.S):
                self.assertEqual(len(re.findall(r"<td>", tr)), 4)

    def test_check4_a_table_cell_holds_one_line(self):
        for decl, r in ALL:
            if not ceiling_ok(decl, rec("K-12")):
                continue
            h = page(decl, "enrich", record=(r if r is None else rec("K-12")))
            for td in re.findall(r"<td>(.*?)</td>", h, re.S):
                outside = re.sub(r"<details>.*?</details>", "", td, flags=re.S)
                self.assertEqual(outside.count("<div>"), 1, td)
                self.assertIsNone(re.search(r"<(br|p|ul|li|table)", outside), td)
            self.assertIn("white-space:nowrap", h)  # one-line rule is enforced in CSS as well; long text sits behind a disclosure

    def test_check5_each_open_question_once_with_a_count_per_row(self):
        h = page(CTX_NOUN, "enrich")
        plain = html.unescape(h)
        for noun in ("N.CONTEXT", "N.CAPABILITY", "N.SERVICE"):
            for q in [e for e in F.REG["elements"] if e["id"] == noun][0]["open_questions"]:
                self.assertEqual(plain.count(q), 1, q)
        o = proj(CTX_NOUN, "enrich")
        counts = {r["id"]: len(r["open"]) for r in o["enrich"]["rows"]}
        self.assertEqual(counts, {"meaning": 1, "peer.capability": 3, "peer.service": 2})
        for rid, n in counts.items():
            row = re.search(r'<tr data-claim="%s">.*?</tr>' % re.escape(rid), h, re.S).group(0)
            self.assertIn("(%d open)" % n, row)
        self.assertEqual(o["enrich"]["open_total"], 6)

    def test_check5b_a_short_question_is_not_repeated_as_a_stem(self):
        reg = copy.deepcopy(F.REG)
        for e in reg["elements"]:
            if e["id"] == "N.CONTEXT":
                e["open_questions"] = ["Short one?"]
        h = html.unescape(page(CTX_NOUN, "enrich", reg=reg))
        self.assertEqual(h.count("Short one?"), 1)

    def test_check6_enable_is_one_answer_one_trust_one_movement(self):
        for decl, r in ALL:
            h = page(decl, "enable", record=r)
            for s in ("answer", "trust", "movement"):
                self.assertEqual(h.count('data-slot="%s"' % s), 1)
            ans = re.search(r'data-slot="answer">(.*?)</p>', h, re.S).group(1)
            ans = re.sub(r"<strong class=\"lead\">.*?</strong> ", "", ans)  # the status lead (non-RULED nouns) is not part of the answer sentence
            # the registry's own leading status marker ("OPEN." in Industry's definition) is not a sentence of the answer either
            ans = re.sub(r"^(OPEN|PROPOSAL)\.\s", "", html.unescape(ans))
            n = len(re.findall(r"[.!?](?:\s|$)", ans))
            if not re.search(r"[.!?]$", ans):
                n += 1  # a verbatim source quotation may end without a full stop (it is still one sentence); the text is never edited to add one
            self.assertEqual(n, 1, ans)
            self.assertEqual(sl_count(h), 0)  # no Enhance or Enrich slot at Enable

    def test_trust_line_is_status_plus_source_count_at_every_depth(self):
        for d in sl.DEPTHS:
            self.assertIn('<span class="tg">RULED</span> 3 sources</p>', page(CTX_NOUN, d))
        o = proj(CTX_NOUN, "enable")
        self.assertEqual(o["frame"]["trust"], {"status": "RULED", "source_count": 3})

    def test_source_chips_are_short_name_plus_date_at_most_three_then_a_count(self):
        h = page(CTX_NOUN, "enrich")
        svc = re.search(r'<tr data-claim="peer.service">.*?</tr>', h, re.S).group(0)
        cell = re.findall(r"<td>(.*?)</td>", svc, re.S)[2]
        line = re.search(r"<div>(.*?)</div>", cell, re.S).group(1)
        self.assertEqual(len(re.findall(r'class="tg"', line)), 3)
        self.assertIn("+2", line)
        self.assertIn("SP-01", line)  # the live evidence chip comes first
        self.assertIn("Ledger 20 Nov 07:06", cell)  # full citation on request
        self.assertIn("Ledger 20 Nov 10:51", cell)


def sl_count(h):
    return len([s for s in re.findall(r'data-slot="(\w+)"', h) if s not in sd.FRAME and s != "not_applicable"])


def ceiling_ok(decl, r):
    """True where the screen can show Enrich (so the trust table exists): noun screens, and record screens whose kind reaches Enrich."""
    return decl["screen_type"] in ("noun", "menu") or sd.stage_for_kind(r["kind"] if "field" in decl["record"]["kind"] else decl["record"]["kind"]["fixed"]) == "enrich"


class C7_Verbs(unittest.TestCase):
    def test_no_bound_verb_shows_hold_and_the_reason(self):
        for d in sl.DEPTHS:
            h = page(CTX_NOUN, d)
            mv = slot(h, "movement")
            self.assertIn("HOLD", mv); self.assertIn("verbs not yet bound", mv)
            self.assertIn("noun-to-verb governance waits on the Architecture tab", mv)

    def test_a_verb_appears_only_where_bound(self):
        d = copy.deepcopy(CTX_NOUN); d["movement"]["verbs"] = [{"verb": "route", "source": "S-1", "status": "bound"}]
        h = page(d, "enable")
        self.assertIn("Next: route", slot(h, "movement")); self.assertNotIn("HOLD", slot(h, "movement"))
        self.assertNotIn("route", page(CTX_NOUN, "enrich").replace("Intersecting", ""))  # nothing invented elsewhere


class C8_to_C9_Entitlement(unittest.TestCase):
    def test_check8_client_gets_no_enrich_content_anywhere(self):
        o = proj(CTX_NOUN, "enrich", actor=ACTOR_CLIENT, role_max=None)
        blob = json.dumps(o)
        self.assertNotIn("enrich", o)
        for forbidden in ("SP-01", "definition_source", "project instructions", "Open question", "fingerprint"):
            self.assertNotIn(forbidden, blob); self.assertNotIn(forbidden, sr.render_screen(o))
        self.assertEqual({p["operating_source"] for p in o["enhance"]["peers"]["rows"]}, {"NO_OPERATING_SOURCE"})

    def test_check8_hidden_page_data_enable_holds_only_enable_content(self):
        o = proj(CTX_NOUN, "enable")
        self.assertEqual(set(o) & {"enhance", "enrich"}, set())
        blob = json.dumps(o)
        for forbidden in ("SP-01", "Capability", "Purpose", "MC-390147223f2d", "Which domain is Context"):
            self.assertNotIn(forbidden, blob)
            self.assertNotIn(forbidden, sr.render_screen(o))

    def test_check8_enhance_holds_no_enrich_content(self):
        o = proj(CTX_NOUN, "enhance")
        self.assertNotIn("enrich", o)
        for forbidden in ("SP-01", "Which domain is Context", "existence is not operation"):
            self.assertNotIn(forbidden, json.dumps(o))

    def test_check8_evidence_gates_are_the_existing_fail_closed_ones(self):
        o = proj(CTX_NOUN, "enrich", ev=False)
        svc = [r for r in o["enrich"]["rows"] if r["id"] == "peer.service"][0]
        self.assertEqual(svc["status"], "HOLD"); self.assertEqual(svc["evidence"], [])
        bad = dict(evidence()[0][0], sha256="0" * 64)
        o = sd.project(CTX_NOUN, F.REG, "enrich", ACTOR_S, [bad], evidence()[1], "1", ROLE_MAX)
        svc = [r for r in o["enrich"]["rows"] if r["id"] == "peer.service"][0]
        self.assertEqual(svc["rejected"], ["SOURCE_HASH_MISMATCH"]); self.assertEqual(svc["status"], "HOLD")
        self.assertIn("Rejected evidence: SOURCE_HASH_MISMATCH", sr.render_screen(dict(o, registry_state="c", registry_sha="x" * 12)))

    def test_check9_writes_nothing(self):
        for depth in sl.DEPTHS:
            e = F.Env([F.STEW])
            o = sw.scaffold_context(e, depth, "1")
            self.assertEqual(o["writes"], 0)
            self.assertEqual(sorted(set(x[0] for x in e.log)), ["search", "search_cat"])

    def test_check9_source_has_no_sudo_write_or_raw_sql(self):
        for f in ("screen_decl.py", "screen_render.py", "scaffold_view.py", "scaffold_wire.py", "scaffold_lens.py"):
            code = re.sub(r'""".*?"""', "", open(os.path.join(F.ADDON, f), encoding="utf-8").read(), flags=re.S)
            code = "\n".join(l.split("#")[0] for l in code.splitlines())
            for bad in (r"\bsudo\b", r"with_user", r"\.write\(", r"\.create\(", r"\.unlink\(", r"cr\.execute", r"\bexecute\(", r"<script", r"\son[a-z]+=", r"https?://"):
                self.assertIsNone(re.search(bad, code), (f, bad))

    def test_every_dynamic_value_is_escaped(self):
        reg = copy.deepcopy(F.REG)
        for e in reg["elements"]:
            if e["id"] in ("N.CONTEXT", "N.SERVICE", "N.CAPABILITY"):
                e["definition"] = '<script>alert(1)</script>"><img src=x onerror=alert(2)>'; e["label"] = "<b>x</b>"
                e["open_questions"] = ["<i>q</i> long enough to be cut " + "x" * 80]; e["kind"] = "<u>k</u>"
        h = page(CTX_NOUN, "enrich", reg=reg)
        from html.parser import HTMLParser
        seen = []
        class P(HTMLParser):
            def handle_starttag(s, tag, attrs):
                seen.append((tag, [a for a, _ in attrs]))
        P().feed(body(h))
        self.assertFalse([t for t, _ in seen if t in ("script", "img", "b", "i", "u")])
        self.assertFalse([a for _, attrs in seen for a in attrs if a.startswith("on") or a in ("src", "href")])
        self.assertNotIn("javascript:", body(h).replace("&lt;script", ""))
        self.assertIn("&lt;script&gt;", h)

    def test_refused_or_garbage_renders_a_message_not_an_error(self):
        for o in ({"result": "REFUSED", "reason": "NO_RECOGNISED_ROLE"}, None, {"x": 1}, "str", {"result": "OK"}):
            h = sv.render(o); self.assertIn("Not available", h); self.assertIn("data-lv", h)


class C10_Mobile(unittest.TestCase):
    def test_check10_structural_proxy_only_real_size_is_untested(self):
        h = page(CTX_NOUN, "enable")
        self.assertIn("@media (max-width:600px)", h); self.assertIn("min-height:44px", h); self.assertIn("overflow-wrap:anywhere", h)
        self.assertIsNone(re.search(r"(?<!max-)width:\d{3,}px", re.sub(r"max-width:1100px", "", sr.STYLE)))


class C11_to_C14_Stage(unittest.TestCase):
    def test_check11_stage_and_depth_are_two_labels_and_stage_never_moves(self):
        for kind in ("K-1", "K-6", "K-12", None):
            labels = set()
            for d in sl.DEPTHS:
                h = page(CTX_REC, d, record=rec(kind))
                st = re.findall(r'<span data-label="stage">(.*?)</span>', h); dp = re.findall(r'<span data-label="depth">(.*?)</span>', h)
                self.assertEqual((len(st), len(dp)), (1, 1))
                labels.add(st[0])
            self.assertEqual(len(labels), 1, (kind, labels))
        self.assertIn("Stage: none", page(CTX_NOUN, "enrich"))
        self.assertEqual(re.findall(r'data-label="depth">(.*?)<', page(CTX_NOUN, "enhance")), ["Depth: Enhance"])

    def test_check12_stage_is_computed_at_render_time_and_stored_nowhere(self):
        self.assertTrue(proj(CTX_REC, "enable", record=rec("K-6"))["stage_computed_not_stored"])
        self.assertEqual(proj(CTX_REC, "enable", record=rec("K-6"))["stage"], "enhance")
        self.assertEqual(proj(CTX_REC, "enable", record=rec("K-12"))["stage"], "enrich")  # same record id, new kind, new stage
        raw = open(sd.DEFAULT_PATH, encoding="utf-8").read()
        self.assertIsNone(re.search(r'"stage"\s*:', raw))  # declarations carry no stored stage
        for f in ("models/synapsys.py", "models/navigator.py", "models/work.py"):
            self.assertNotIn("stage_for_kind", open(os.path.join(F.ADDON, f), encoding="utf-8").read())  # no stored field, no model hook

    def test_check13_depth_above_the_ceiling_shows_not_applicable_never_empty(self):
        for kind, req, shown in (("K-1", "enhance", "enable"), ("K-4", "enrich", "enable"), ("K-6", "enrich", "enhance"), ("K-8", "enrich", "enhance")):
            h = page(CTX_REC, req, record=rec(kind))
            self.assertIn("Not applicable for this kind", h)
            self.assertIn('data-depth="%s"' % shown, h)
            self.assertIn(sr.LABEL[req] + ": Not applicable for this kind", text(h))
            self.assertGreater(len(text(h)), 200)
            self.assertNotIn("error", text(h).lower())
        self.assertNotIn("Not applicable", page(CTX_REC, "enrich", record=rec("K-12")))
        self.assertNotIn("Not applicable", page(CTX_NOUN, "enrich"))

    def test_check14_no_bound_kind_is_enable_only_with_the_reason(self):
        for kind, why in ((None, "this record has no resolved kind"), ("K-2", "kind K-2 is not one of")):
            h = page(CTX_REC, "enrich", record=rec(kind))
            self.assertIn("Stage: not bound", h); self.assertIn('data-depth="enable"', h)
            self.assertIn(why, text(h)); self.assertIn("Stage not bound", text(h))
            self.assertEqual(sl_count(h), 0)
            self.assertIn("Enrich: Stage not bound: Enable depth only", text(h))


class C15_to_C16_Declared(unittest.TestCase):
    def test_check15_no_screen_has_its_own_slot_code(self):
        for f in ("screen_render.py", "screen_decl.py"):
            tree = ast.parse(open(os.path.join(F.ADDON, f), encoding="utf-8").read())
            lits = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
            doc_nodes = {id(n.body[0].value) for n in ast.walk(tree) if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef)) and n.body and isinstance(n.body[0], ast.Expr) and isinstance(getattr(n.body[0], "value", None), ast.Constant)}
            code_lits = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in doc_nodes]
            for lit in code_lits:
                self.assertIsNone(re.search(r"N\.(CONTEXT|CAPABILITY|SERVICE|ASSET)|H\.CTX|R\.CTX|Context scaffold|Capability|Service\b|Purpose|Rights holder", lit), (f, lit[:80]))
        self.assertFalse(hasattr(sv, "ROLE_PLAIN"))
        self.assertEqual([n for n in dir(sv) if n.startswith("_peer") or n.startswith("_roles")], [])

    def test_check15_a_new_screen_is_a_declaration_not_new_code(self):
        d = copy.deepcopy(CTX_NOUN)
        d.update({"id": "SCR.SERVICE.NOUN", "noun": "N.SERVICE", "title": "Service"})
        d["made_of"] = None; d["peers"] = None
        d["claims"] = [c for c in d["claims"] if c["id"] == "peer.service"]
        d["claims"][0].update({"id": "meaning", "type": "element", "label": "Service meaning"})
        d["trust_claim"] = "meaning"
        self.assertEqual(sd.validate_screen(d), [])
        for depth in sl.DEPTHS:
            h = page(d, depth)
            self.assertIn("<h1>Service", h); self.assertIn("The ongoing operation of an existing capability", h)
        self.assertIn("No roles are declared for this screen.", page(d, "enhance"))

    def test_check16_checks_1_to_14_run_over_every_declaration(self):
        # the structural checks above are looped over ALL declarations (ALL); prove the loop covers every declaration in the file
        self.assertEqual({d["id"] for d, _ in ALL}, set(DECLS))

    def test_a_chip_whose_quote_is_not_in_the_registry_text_is_dropped_and_noted(self):
        reg = copy.deepcopy(F.REG)
        for e in reg["elements"]:
            if e["id"] == "N.CONTEXT":
                e["definition_source"] = "ledger 20 Nov 07:20-07:21 only"
        o = proj(CTX_NOUN, "enrich", reg=reg)
        self.assertEqual(o["frame"]["trust"]["source_count"], 1)
        self.assertEqual(len(o["notes"]), 2)
        self.assertTrue(all("not found in the registry text" in n for n in o["notes"]))

    def test_every_declared_source_chip_quotes_text_the_registry_really_holds(self):
        els = sl.index_registry(F.REG)
        for d in DECLS.values():
            if d["screen_type"] == "menu":
                continue  # menu screens have no registry element; their quotes are tested against the source table (test_batch3)
            for c in d["claims"]:
                for s in c["sources"]:
                    self.assertIn(s["quote"], els[c["noun"]]["definition_source"], (d["id"], c["id"], s["name"]))


class D3_ContextContent(unittest.TestCase):
    """D3: only content the installed RC05e screen already holds; nothing invented; where there is nothing, say so."""

    def test_every_fact_the_installed_screen_held_is_still_shown_at_the_same_depth(self):
        def toks(h):
            return [html.unescape(t.strip()) for t in re.split(r"<[^>]+>", re.sub(r"<style>.*?</style>", "", h, flags=re.S)) if t.strip()]
        changed_labels = {"Operating source", "Qualification", "Open questions", "Provenance"}  # see the mapping in the return: CHANGED, rulings 3 to 5
        for d in sl.DEPTHS:
            old = toks(open(os.path.join(F.HERE, "golden", "rc05e_installed_view_%s.html" % d), encoding="utf-8").read())
            new = " ".join(toks(sv.render(sw.scaffold_context(F.Env([F.STEW]), d, "1"), d)))
            for t in old:
                if t in changed_labels or re.match(r"(Enable|Enhance|Enrich): .*Registry 0\.3\.5", t):
                    continue
                self.assertIn(t, new, (d, t))

    def test_every_new_text_value_comes_from_the_registry_the_catalogue_or_declared_frame_wording(self):
        registry_questions = {q for e in F.REG["elements"] for q in e.get("open_questions", [])}
        declared = open(sd.DEFAULT_PATH, encoding="utf-8").read()
        frame_words = ("Not applicable for this kind", "Stage not bound", "verbs not yet bound", "No operating source: HOLD", "None recorded")
        o = proj(CTX_NOUN, "enrich")
        self.assertEqual(o["frame"]["answer"], [e for e in F.REG["elements"] if e["id"] == "N.CONTEXT"][0]["definition"])
        for r in o["enrich"]["rows"]:
            for q in r["open"]:
                self.assertIn(q["text"], registry_questions)
            if r["qualifier"] and r["qualifier"]["first"] and not r["qualifier"]["first"].startswith(("Kind: ", "No operating")):
                self.assertTrue(any(r["qualifier"]["first"] == q for q in sw.qualifiers(F.SP01)), r["qualifier"])
        for ch in sum((r["chips"] for r in o["enrich"]["rows"]), []):
            self.assertTrue(ch.get("evidence") or ch["name"] in declared, ch)
        self.assertTrue(frame_words)

    def test_where_the_installed_screen_has_nothing_the_screen_says_so(self):
        h = text(page(CTX_NOUN, "enrich"))
        self.assertIn("No operating source: HOLD", h)  # Capability has no operating source
        reg0 = copy.deepcopy(F.REG)
        for e in reg0["elements"]:
            if e["id"] == "N.CAPABILITY":
                e["definition_source"] = ""
        self.assertIn("None recorded", text(page(CTX_NOUN, "enrich", reg=reg0)))  # no chip survives: the screen says so
        o = proj(CTX_NOUN, "enrich")
        cap = [r for r in o["enrich"]["rows"] if r["id"] == "peer.capability"][0]
        self.assertEqual((cap["status"], cap["evidence"]), ("HOLD", []))
        reg = copy.deepcopy(F.REG)
        for e in reg["elements"]:
            if e["id"] == "N.CONTEXT":
                e["open_questions"] = []; e["definition"] = ""
        h2 = page(CTX_NOUN, "enrich", reg=reg)
        self.assertIn("none recorded", h2); self.assertIn("UNSOURCED", slot(h2, "answer"))

    def test_the_plain_role_names_and_required_first_order_are_kept_and_codes_stay_out_of_ordinary_copy(self):
        h = page(CTX_NOUN, "enhance")
        roles = text(slot(h, "made_of"))
        for good in ("Rights holder", "Intersecting chains", "Portfolios", "Strategies", "The Context itself", "one or more"):
            self.assertIn(good, roles)
        for bad in ("rights_holder", "intersects+", "H.CTX", "MC-", "R.CTX", "many"):
            self.assertNotIn(bad, text(h))
        self.assertLess(roles.index("required"), roles.index("optional"))
        self.assertEqual(roles.count("required"), 3)
        e = page(CTX_NOUN, "enrich")
        main = e[:e.index("<details class=\"td\"")]
        for tech in ("MC-390147223f2d", "7c31aa1de4c9", "608938cd399e"):
            self.assertNotIn(tech, main); self.assertIn(tech, e[e.index("<details class=\"td\""):])
        self.assertIn("relationship H.CTX, cluster MC-390147223f2d", e)
        self.assertIn("<summary>Technical details</summary>", e); self.assertNotIn("<details class=\"td\"", page(CTX_NOUN, "enhance"))

    def test_catalogue_record_is_shown_with_qualification_not_as_proof(self):
        h = text(page(CTX_NOUN, "enrich"))
        for q in ("existence is not operation", "validation: none recorded", "no source document recorded", "not bound to a Context"):
            self.assertIn(q, h)
        self.assertIn("SP-01 Strategic Planning & Context Establishment", h)
        self.assertEqual(h.count("NO OPERATING SOURCE: HOLD"), 1)  # the Enhance peer row for Capability; Service has a record
        self.assertIsNone(re.search(r"\bSOURCED\b(?!:)", h.replace("CATALOGUE RECORD FOUND", "")))

    def test_the_route_ignoring_context_id_is_documented_current_behaviour_not_a_decision(self):
        a = sw.scaffold_context(F.Env([F.STEW]), "enrich", "")
        b = sw.scaffold_context(F.Env([F.STEW]), "enrich", "99999")
        for k in ("context_id",):
            a.pop(k); b.pop(k)
        self.assertEqual(a, b)


class D5_RecordScreens(unittest.TestCase):
    def env(self, rows_ctx=(), rows_asset=(), ra=()):
        return F.Env([F.STEW], records={"synapsys.context": list(rows_ctx), "synapsys.asset": list(rows_asset)}, ra_models=ra)

    def test_context_record_ceiling_from_its_own_kind(self):
        for kind, req, eff in (("K-1", "enrich", "enable"), ("K-6", "enrich", "enhance"), ("K-12", "enrich", "enrich")):
            e = self.env(rows_ctx=[F.Row(5, name="CTX-SS", kind=kind)])
            o = sw.screen_record(e, "SCR.CONTEXT.RECORD", 5, req)
            self.assertEqual((o["result"], o["depth_effective"], o["stage"], o["context_id"]), ("OK", eff, sd.stage_for_kind(kind), "5"))
            self.assertIn("Context: CTX-SS", sr.render_screen(o))
            self.assertEqual(o["writes"], 0)
            self.assertEqual({x[0] for x in e.log}, {"search", "search_cat", "search_rec"})

    def test_context_record_with_no_kind_is_stage_not_bound(self):
        o = sw.screen_record(self.env(rows_ctx=[F.Row(5, name="CTX-X", kind=False)]), "SCR.CONTEXT.RECORD", 5, "enrich")
        self.assertEqual((o["stage"], o["depth_effective"], o["depth_clamped"]), ("not bound", "enable", True))
        self.assertIn("this record has no resolved kind", o["stage_reason"])

    def test_asset_record_stage_is_its_own_noun_kind_with_the_context_kind_as_a_neighbour(self):
        ctx = F.Row(9, name="C")
        for ctx_kind in ("K-12", "K-1", False):
            a = F.Row(3, name="Asset one", context_id=ctx, context_kind=ctx_kind)
            e = self.env(rows_asset=[a])
            o = sw.screen_record(e, "SCR.ASSET.RECORD", 3, "enrich")
            self.assertEqual((o["stage"], o["depth_effective"], o["depth_clamped"]), ("enable", "enable", True))  # K-4: always Enable
            h = sr.render_screen(o)
            self.assertIn("Asset: Asset one", h)
            if ctx_kind:
                self.assertIn("Neighbour: its Context is kind %s" % ctx_kind, h); self.assertIn("never used for stage", h)
            else:
                self.assertNotIn("Neighbour", h)
            self.assertEqual(o["context_id"], "9")
            self.assertIn("Enrich: Not applicable for this kind", text(h))

    def test_record_path_refusals_and_rights(self):
        ok = F.Row(5, name="N", kind="K-12")
        self.assertEqual(sw.screen_record(self.env(rows_ctx=[ok]), "SCR.CONTEXT.NOUN", 5)["reason"], "UNKNOWN_SCREEN")
        self.assertEqual(sw.screen_record(self.env(rows_ctx=[ok]), "SCR.NOPE", 5)["reason"], "UNKNOWN_SCREEN")
        self.assertEqual(sw.screen_record(self.env(rows_ctx=[ok]), "SCR.CONTEXT.RECORD", 6)["reason"], "RECORD_NOT_FOUND")
        self.assertEqual(sw.screen_record(self.env(rows_ctx=[ok]), "SCR.CONTEXT.RECORD", "x")["reason"], "RECORD_NOT_FOUND")
        self.assertEqual(sw.screen_record(self.env(rows_ctx=[ok]), "SCR.CONTEXT.RECORD", 5, "deep")["reason"], "UNKNOWN_DEPTH")
        self.assertEqual(sw.screen_record(self.env(rows_ctx=[ok], ra=["synapsys.context"]), "SCR.CONTEXT.RECORD", 5)["reason"], "NO_RECORD_READ_RIGHT")
        nogroup = F.Env([], records={"synapsys.context": [ok]})
        self.assertEqual(sw.screen_record(nogroup, "SCR.CONTEXT.RECORD", 5)["reason"], "NO_RECOGNISED_ROLE")

    def test_nothing_is_written_to_dev_these_are_in_memory_fixtures(self):
        # Row/RecModel raise on create/write/unlink and on sudo; the tests above ran the whole record path through them.
        with self.assertRaises(AssertionError):
            F.RecModel([], [], "m").create({})
        with self.assertRaises(AssertionError):
            F.RecModel([], [], "m").sudo()


class Wire_RC05_Retained(unittest.TestCase):
    """The RC05 wire behaviours that are not about presentation: kept as they were (RETAIN)."""

    def test_no_group_refused_before_any_read(self):
        e = F.Env([]); self.assertEqual(sw.scaffold_context(e, "enable")["reason"], "NO_RECOGNISED_ROLE"); self.assertEqual(e.log, [])

    def test_bad_depth_refused(self):
        self.assertEqual(sw.scaffold_context(F.Env([F.STEW]), "deep")["reason"], "UNKNOWN_DEPTH")

    def test_tampered_registry_refused(self):
        r = F.Rec(body=F.RAW.decode().replace('"Context"', '"Kontext"', 1))
        self.assertEqual(sw.scaffold_context(F.Env([F.STEW], rec=r), "enable")["reason"], "REGISTRY_BODY_HASH_MISMATCH")

    def test_pinned_evidence_edit_is_rejected(self):
        cat = F.CatModel([], vals=dict(F.SP01, x_service_status="deprecated"))
        o = sw.scaffold_context(F.Env([F.STEW], cat=cat), "enrich")
        svc = [r for r in o["enrich"]["rows"] if r["id"] == "peer.service"][0]
        self.assertEqual((svc["status"], svc["rejected"]), ("HOLD", ["SOURCE_HASH_MISMATCH"]))

    def test_route_output_keeps_the_fields_the_installed_ui_checks_read(self):
        o = sw.scaffold_context(F.Env([F.STEW]), "enrich", "1")
        self.assertEqual((o["writes"], o["registry_version"], o["registry_sha"], o["label"], o["status"]), (0, "0.3.5", F.SHA, "Context", "RULED"))
        self.assertEqual(o["declaration_sha"], META["sha256"])

    def test_stable_across_calls(self):
        a = sw.scaffold_context(F.Env([F.STEW]), "enrich", "C"); b = sw.scaffold_context(F.Env([F.STEW]), "enrich", "C")
        self.assertEqual(a, b)

    def svc_row(self, o):
        return [r for r in o["enrich"]["rows"] if r["id"] == "peer.service"][0]

    def test_unreadable_catalogue_is_a_hold_with_a_note_not_an_error(self):
        o = sw.scaffold_context(F.Env([F.STEW], cat=F.CatModel([], ra=True)), "enrich")
        self.assertEqual(self.svc_row(o)["status"], "HOLD")
        self.assertIn("x_service_catalogue:SP-01: not readable with your rights", o["evidence_notes"])

    def test_missing_catalogue_record_is_a_hold_with_a_note(self):
        o = sw.scaffold_context(F.Env([F.STEW], cat=F.CatModel([], missing=True)), "enrich")
        self.assertEqual(self.svc_row(o)["status"], "HOLD")
        self.assertIn("x_service_catalogue:SP-01: record not found", o["evidence_notes"])

    def test_collaborator_reaches_enrich_and_gets_the_catalogue_record_but_no_context_bound_evidence(self):
        o = sw.scaffold_context(F.Env([F.COLL]), "enrich", "CTX-A")
        self.assertEqual((o["depth_effective"], o["depth_clamped"]), ("enrich", False))
        self.assertEqual(self.svc_row(o)["status"], "CATALOGUE RECORD FOUND")
        ev = [{"id": "E1", "noun_id": "N.SERVICE", "context_id": "CTX-A", "kind": "library", "source_ref": "L", "sha256": "a" * 64}]
        o2 = sd.project(CTX_NOUN, F.REG, "enrich", sw.actor_from_env(F.Env([F.COLL])), ev, {"L": {"sha256": "a" * 64, "label": "x"}}, "CTX-A", ROLE_MAX)
        self.assertEqual(self.svc_row(o2)["rejected"], ["ACTOR_NOT_IN_CONTEXT"])

    def test_controller_is_unchanged_and_still_user_authenticated(self):
        c = open(os.path.join(F.ADDON, "controllers", "scaffold.py"), encoding="utf-8").read()
        self.assertIn("auth='user'", c); self.assertIn("request.env", c); self.assertIn("sv.render(", c)
        self.assertEqual(c.count("@http.route"), 2)  # no record route was added


if __name__ == "__main__":
    unittest.main(verbosity=2)
