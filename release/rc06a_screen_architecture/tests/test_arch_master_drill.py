"""Offline tests for the Master drill-down (arch_master_drill.py), the fail-closed context builder (arch_master_ctx.py) and the per-record evidence.
Fake env only. Proves: three-way separation (definition / effective / actual), rights-first links, uniform NOT_AVAILABLE for every bad or hidden
identifier, reuse of the existing scaffold and lens renderers, authority and Realisation boundaries. NOT Odoo, NOT a role session, NOT V20."""
import ast, copy, importlib.util, json, os, re, subprocess, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, ".."))
ADDON = os.path.join(ROOT, "addon", "synapsys")
sys.path.insert(0, ADDON); sys.path.insert(0, HERE)
import arch_graph as G, arch_master as A, arch_master_views as V, arch_master_drill as DR, arch_master_ctx as CX, master_render as R, lens_contract as LC
import test_arch_master as T
import test_arch_master_views as TV

D = TV.D
MENU = {m["menu_id"]: m for m in D["menus"]}
M_STRATEGY = next(m["menu_id"] for m in D["menus"] if m["path"].endswith("Architecture/Form/Strategy"))
M_ASSET = next(m["menu_id"] for m in D["menus"] if m["path"].endswith("Evolve/Asset"))
M_FORM = next(m["menu_id"] for m in D["menus"] if m["path"] == "SynapSys/Architecture/Form")
M_ARCH = next(m["menu_id"] for m in D["menus"] if m["path"] == "SynapSys/Architecture")


def aid(mid): return int(MENU[mid]["action_ref"].split(",")[1])


def good_effective():
    acts, flds = {}, {}
    for m in D["menus"]:
        if m["kind"] == "ACT_WINDOW": acts[aid(m["menu_id"])] = {"res_model": m["model"], "domain": m["domain"] or "", "view_mode": m["view_mode"]}
        if m["kind"] == "CLIENT_ACTION": acts[aid(m["menu_id"])] = {"tag": m["client_tag"], "res_model": None}
        if m.get("model"):
            for e in m["edges"]: flds.setdefault(m["model"], {})[e["field"]] = {"type": "many2one" if e["cardinality"] == "one" else "many2many", "relation": e["target_model"]}
    return {"actions": acts, "fields": flds}


def mkctx(**kw):
    ctx = {"visible_menu_ids": {m["menu_id"] for m in D["menus"]}, "readable_models": {m["model"] for m in D["menus"] if m.get("model")}, "effective": good_effective(), "bindings": None,
           "screen_html": lambda mid, a, depth: {"result": "OK", "html": "<p class='fake-scaffold'>SCAFFOLD:%s:%s:%s</p>" % (mid, a, depth), "binding_status": "FAKE"},
           "record_screen_html": lambda sid, rid, depth: {"result": "OK", "html": "<p class='fake-record'>RECORD:%s:%s</p>" % (sid, rid)}}
    ctx.update(kw); return ctx


def drill(path, depth="enable", ctx="default", world=None, ov="", **kw):
    g, a, n = TV.parts(world, **kw)
    return DR.drill(D, g, a, n, path, mkctx() if ctx == "default" else ctx, depth, ov)


def same_but_level(x): return json.dumps({k: v for k, v in x.items() if k != "level"}, sort_keys=True)


class Paths(unittest.TestCase):
    def test_valid_paths_parse(self):
        self.assertEqual(DR.parse_path("app"), ("app",)); self.assertEqual(DR.parse_path("grp:183"), ("grp", 183)); self.assertEqual(DR.parse_path("fld:186:context_id"), ("fld", 186, "context_id"))
        self.assertEqual(DR.parse_path("rec:synapsys.asset:90"), ("rec", "synapsys.asset", 90))

    def test_malformed_paths_are_rejected(self):
        bad = ["", "APP", "app ", "app:1", "grp", "grp:", "grp:-1", "grp:1.5", "grp:123456", "scr:1;drop", "fld:186:Context_id", "fld:186:", "fld:186:1abc", "fld:186:" + "a" * 60, "data:186",
               "rec:synapsys.context:1", "rec:synapsys.asset:-1", "rec:synapsys.asset:12345678901", "rec:res.partner:1", "rec:synapsys.asset", "../../etc/passwd", "scr:186\n", "<script>", None, 186, ["app"], {"a": 1}]
        for b in bad:
            with self.assertRaises(ValueError, msg=repr(b)): DR.parse_path(b)

    def test_bad_paths_give_the_uniform_answer(self):
        for b in ["", "grp:-1", "<script>", "scr:99999", "rec:synapsys.context:1", None, 5, "fld:186:Bad"]:
            o = drill(b); self.assertEqual((o["state"], o["writes"]), ("NOT_AVAILABLE", 0)); self.assertEqual(o["reason"], DR.NOT_AVAILABLE["reason"])


class Levels(unittest.TestCase):
    def test_every_level_answers_ok_with_breadcrumb(self):
        for p in ("app", "grp:%d" % M_FORM, "scr:%d" % M_STRATEGY, "view:%d" % M_STRATEGY, "fld:%d:context_id" % M_STRATEGY, "data:%d:context_id" % M_STRATEGY, "rec:synapsys.asset:90"):
            o = drill(p, "enhance"); self.assertEqual(o["state"], "OK", p); self.assertEqual(o["breadcrumb"][0]["drill"], "app"); self.assertEqual(o["breadcrumb"][-1]["drill"], p if not p.startswith("grp") else p)

    def test_application_lists_the_root_children(self):
        o = drill("app"); root = [m for m in D["menus"] if m["parent_id"] is None][0]
        self.assertEqual(o["root"]["menu_id"], root["menu_id"]); self.assertEqual({c["menu_id"] for c in o["children"]}, {m["menu_id"] for m in D["menus"] if m["parent_id"] == root["menu_id"]})

    def test_group_lists_its_screens_and_only_containers_are_groups(self):
        o = drill("grp:%d" % M_FORM); self.assertEqual({c["menu_id"] for c in o["children"]}, {m["menu_id"] for m in D["menus"] if m["parent_id"] == M_FORM})
        self.assertEqual(drill("grp:%d" % M_STRATEGY)["state"], "NOT_AVAILABLE")                  # a screen is not a group
        self.assertEqual(drill("scr:%d" % M_FORM)["state"], "NOT_AVAILABLE")                      # a container is not a screen
        self.assertEqual(drill("view:%d" % M_FORM)["state"], "NOT_AVAILABLE")

    def test_breadcrumb_follows_the_menu_tree(self):
        labels = [c["label"] for c in drill("scr:%d" % M_STRATEGY)["breadcrumb"]]; self.assertEqual(labels, ["Application", "Architecture", "Form", "Strategy"])
        labels = [c["level"] for c in drill("data:%d:context_id" % M_STRATEGY)["breadcrumb"]]; self.assertEqual(labels, ["app", "grp", "grp", "scr", "view", "fld", "data"])

    def test_field_and_data_only_for_declared_edges(self):
        self.assertEqual(drill("fld:%d:not_a_field" % M_STRATEGY)["state"], "NOT_AVAILABLE"); self.assertEqual(drill("data:%d:not_a_field" % M_STRATEGY)["state"], "NOT_AVAILABLE")
        self.assertEqual(drill("fld:%d:context_id" % M_FORM)["state"], "NOT_AVAILABLE")

    def test_screen_children_are_its_view_and_edges(self):
        o = drill("scr:%d" % M_STRATEGY); self.assertEqual(o["children"][0]["drill"], "view:%d" % M_STRATEGY); self.assertEqual({c["label"] for c in o["children"][1:]}, {e["field"] for e in MENU[M_STRATEGY]["edges"]})


class ThreeWaySeparation(unittest.TestCase):
    def test_three_distinct_blocks_at_every_screen_level(self):
        for p in ("scr:%d" % M_STRATEGY, "view:%d" % M_STRATEGY, "app", "grp:%d" % M_FORM):
            o = drill(p); self.assertTrue({"canonical", "effective", "actual"} <= set(o), p)

    def test_unread_effective_configuration_is_unverified_never_copied_from_the_definition(self):
        for ctx in (mkctx(effective=None), mkctx(effective={"actions": None, "fields": None})):
            o = drill("scr:%d" % M_STRATEGY, ctx=ctx); self.assertEqual(o["effective"]["state"], "SOURCE_UNVERIFIED"); self.assertNotIn("effective", o["effective"])
            f = drill("fld:%d:context_id" % M_STRATEGY, ctx=ctx)["field"]["effective"]; self.assertEqual(f["state"], "SOURCE_UNVERIFIED"); self.assertNotIn("effective", f)
        o = drill("scr:%d" % M_STRATEGY, ctx={}); self.assertEqual(o["effective"]["state"], "SOURCE_UNVERIFIED")

    def test_unreadable_action_is_unverified_not_a_match(self):
        e = good_effective(); e["actions"][aid(M_STRATEGY)] = "UNREADABLE"
        self.assertEqual(drill("scr:%d" % M_STRATEGY, ctx=mkctx(effective=e))["effective"]["state"], "SOURCE_UNVERIFIED")
        e = good_effective(); del e["actions"][aid(M_STRATEGY)]; self.assertEqual(drill("scr:%d" % M_STRATEGY, ctx=mkctx(effective=e))["effective"]["state"], "SOURCE_UNVERIFIED")

    def test_matching_and_each_kind_of_drift_is_reported(self):
        self.assertEqual(drill("scr:%d" % M_STRATEGY)["effective"]["state"], "MATCHES_DEFINITION")
        for fact, mut in (("model", lambda a: a.update(res_model="res.partner")), ("domain", lambda a: a.update(domain="[('x','=',1)]")), ("view_mode", lambda a: a.update(view_mode="kanban"))):
            e = good_effective(); mut(e["actions"][aid(M_STRATEGY)]); o = drill("scr:%d" % M_STRATEGY, ctx=mkctx(effective=e))["effective"]
            self.assertEqual(o["state"], "DRIFT"); self.assertIn(fact, [x["fact"] for x in o["differences"]])
        cm = next(m["menu_id"] for m in D["menus"] if m["kind"] == "CLIENT_ACTION" and m["client_tag"] == "synapsys_lenses")
        e = good_effective(); e["actions"][aid(cm)]["tag"] = "other"; o = drill("scr:%d" % cm, ctx=mkctx(effective=e))["effective"]; self.assertIn("client_tag", [x["fact"] for x in o["differences"]])

    def test_field_effective_drift_both_facts(self):
        e = good_effective(); e["fields"]["synapsys.strategy"]["context_id"] = {"type": "many2many", "relation": "res.partner"}
        o = drill("fld:%d:context_id" % M_STRATEGY, ctx=mkctx(effective=e))["field"]["effective"]; self.assertEqual(o["state"], "DRIFT"); self.assertEqual({x["fact"] for x in o["differences"]}, {"target_model", "cardinality"})
        e = good_effective(); del e["fields"]["synapsys.strategy"]["context_id"]; self.assertEqual(drill("fld:%d:context_id" % M_STRATEGY, ctx=mkctx(effective=e))["field"]["effective"]["state"], "FIELD_NOT_PRESENT")
        e = good_effective(); e["fields"]["synapsys.strategy"] = "UNREADABLE"; self.assertEqual(drill("fld:%d:context_id" % M_STRATEGY, ctx=mkctx(effective=e))["field"]["effective"]["state"], "SOURCE_UNVERIFIED")
        self.assertEqual(drill("fld:%d:context_id" % M_STRATEGY)["field"]["effective"]["state"], "MATCHES_DEFINITION")

    def test_view_architecture_is_never_claimed_read(self):
        v = drill("view:%d" % M_STRATEGY)["view"]; self.assertEqual(v["view_architecture"]["state"], "SOURCE_UNVERIFIED")
        self.assertEqual(v["definition_modes"], DR.A_modes(MENU[M_STRATEGY]["view_mode"])); self.assertEqual(v["effective_modes"], DR.A_modes(MENU[M_STRATEGY]["view_mode"]))
        self.assertIsNone(drill("view:%d" % M_STRATEGY, ctx={})["view"]["effective_modes"])

    def test_actual_block_is_rights_first(self):
        o = drill("scr:%d" % M_STRATEGY); self.assertEqual((o["actual"]["state"], o["actual"]["readable_count"]), ("REAL_ACTOR_VISIBLE", 5))
        o = drill("scr:%d" % M_STRATEGY, restricted={"synapsys.strategy"}); self.assertEqual(o["actual"]["state"], "RESTRICTED")
        o = drill("scr:%d" % M_STRATEGY, world={}); self.assertEqual(o["actual"]["state"], "NONE_VISIBLE_TO_ACTOR")


class Links(unittest.TestCase):
    def test_no_link_unless_the_menu_is_known_visible(self):
        self.assertIsNone(drill("scr:%d" % M_STRATEGY, ctx=mkctx(visible_menu_ids=None))["menu"]["native_link"])
        self.assertIsNone(drill("scr:%d" % M_STRATEGY, ctx=mkctx(visible_menu_ids=set()))["menu"]["native_link"])
        self.assertIsNone(drill("scr:%d" % M_STRATEGY, ctx={})["menu"]["native_link"])
        self.assertEqual(drill("scr:%d" % M_STRATEGY)["menu"]["native_link"], "/odoo/action-%d" % aid(M_STRATEGY))

    def test_containers_carry_no_action_so_they_can_never_be_linked(self):
        conts = [m for m in D["menus"] if m["kind"] == "CONTAINER"]; self.assertEqual(len(conts), 9)
        self.assertTrue(all(DR._action_id(m) is None for m in conts)); self.assertTrue(all(DR.menu_link(m, mkctx()) is None for m in conts))

    def test_containers_never_get_a_link_and_rows_carry_their_own(self):
        o = drill("grp:%d" % M_ARCH); self.assertTrue(all((c["native_link"] is None) == (c["kind"] == "CONTAINER") for c in o["children"]))
        vis = {M_STRATEGY}; o = drill("grp:%d" % M_FORM, ctx=mkctx(visible_menu_ids=vis)); self.assertEqual([c["menu_id"] for c in o["children"] if c["native_link"]], [M_STRATEGY])

    def test_link_ids_are_integers_from_the_definition_only(self):
        for m in D["menus"]:
            l = DR.menu_link(m, mkctx())
            if l: self.assertRegex(l, r"^/odoo/action-\d+$")

    def test_record_link_needs_menu_model_and_row(self):
        g, a, n = TV.parts(); m = MENU[M_ASSET]
        self.assertEqual(DR.record_link(m, 90, g, a, mkctx()), "/odoo/action-%d/90" % aid(M_ASSET))
        self.assertIsNone(DR.record_link(m, 90, g, a, mkctx(readable_models=set())))                  # no real read right on the model
        self.assertIsNone(DR.record_link(m, 90, g, a, mkctx(readable_models=None)))
        self.assertIsNone(DR.record_link(m, 90, g, a, mkctx(visible_menu_ids=set())))                 # menu not visible
        self.assertIsNone(DR.record_link(m, 5551, g, a, mkctx()))                                     # not in the graph
        a["visible"]["synapsys.asset"].discard(90); self.assertIsNone(DR.record_link(m, 90, g, a, mkctx()))   # row hidden from this actor
        for bad in ("90", 90.0, True, None, -1): self.assertIsNone(DR.record_link(m, bad, g, a, mkctx()))
        self.assertIsNone(DR.record_link(MENU[M_FORM], 1, g, a, mkctx()))                             # container

    def test_data_links_only_for_readable_rows(self):
        o = drill("data:%d:context_id" % M_ASSET, "enhance"); p = {x["from"]["id"]: x for x in o["data"]["pairs"]}
        self.assertEqual(p[90]["from"]["link"], "/odoo/action-%d/90" % aid(M_ASSET)); self.assertEqual(p[90]["from"]["rec"], "rec:synapsys.asset:90"); self.assertIsNone(p[90]["to"]["rec"])
        o = drill("data:%d:context_id" % M_ASSET, "enhance", hidden={"synapsys.asset": {367}}); self.assertEqual([x["from"]["id"] for x in o["data"]["pairs"]], [90])


class Uniform(unittest.TestCase):
    def test_hidden_absent_foreign_and_malformed_records_are_indistinguishable(self):
        base = drill("rec:synapsys.asset:5551")                                                      # does not exist
        hidden = drill("rec:synapsys.asset:367", hidden={"synapsys.asset": {367}})                    # exists, hidden from this actor
        foreign = drill("rec:synapsys.asset:367", hidden={"synapsys.context": {2}, "synapsys.asset": {367}})
        restricted = drill("rec:synapsys.asset:90", restricted={"synapsys.asset"})
        self.assertEqual(len({same_but_level(x) for x in (base, hidden, foreign, restricted)}), 1)
        for x in (base, hidden, foreign, restricted): self.assertEqual(x["state"], "NOT_AVAILABLE"); self.assertNotIn("367", json.dumps(x)); self.assertNotIn("asset", x["reason"])

    def test_non_evidence_model_is_not_available_even_if_readable(self):
        self.assertEqual(drill("rec:synapsys.strategy:20")["state"], "NOT_AVAILABLE")
        g, a, n = TV.parts(); self.assertEqual(DR.record_evidence(D, g, a, n, "synapsys.context", 1)["state"], "NOT_AVAILABLE")

    def test_record_identifier_types(self):
        g, a, n = TV.parts()
        for bad in ("90", 90.0, True, None, -1, 10 ** 12): self.assertEqual(DR.record_evidence(D, g, a, n, "synapsys.asset", bad)["state"], "NOT_AVAILABLE", repr(bad))

    def test_no_hidden_row_appears_anywhere_in_a_page(self):
        w = TV.world2(); w["synapsys.asset"][367]["name"] = "SECRET-367"; w["synapsys.outcome"][60]["name"] = "SECRET-OUTCOME"
        for path in ("app", "grp:%d" % M_FORM, "scr:%d" % M_ASSET, "view:%d" % M_ASSET, "fld:%d:context_id" % M_ASSET, "data:%d:context_id" % M_ASSET, "rec:synapsys.asset:367", "rec:synapsys.outcome:60"):
            for depth in V.DEPTHS:
                g, a, n = TV.parts(w, hidden={"synapsys.asset": {367}, "synapsys.outcome": {60}}); d = V.assemble(D, g, a, n, "collaborator", "drill", "Form", depth, "steward", TV.GROUPS, drill=path, ctx=mkctx())
                h = R.render_page(d); self.assertNotIn("SECRET-367", h, (path, depth)); self.assertNotIn("SECRET-OUTCOME", h, (path, depth))


class DataLevel(unittest.TestCase):
    def test_enable_shows_counts_only_enhance_shows_pairs(self):
        a = drill("data:%d:context_id" % M_STRATEGY, "enable")["data"]; b = drill("data:%d:context_id" % M_STRATEGY, "enhance")["data"]
        self.assertEqual((a["pairs"], a["total_readable"]), ([], b["total_readable"])); self.assertTrue(b["pairs"])

    def test_cap_and_truncation_flag(self):
        w = TV.world2(); w["synapsys.asset"] = {i: dict(name="a%d" % i, context_id=T.p(1), rights_holder_id=False, qualifies=False, qualified_benefit_count=0, rights_confirmed=False, lifecycle="x", ppv="candidate") for i in range(1, 61)}
        d = drill("data:%d:context_id" % M_ASSET, "enhance", world=w)["data"]; self.assertEqual((d["shown"], d["total_readable"], d["truncated"]), (50, 60, True))

    def test_restricted_and_empty_states_are_stated(self):
        self.assertEqual(drill("data:%d:context_id" % M_ASSET, "enhance", restricted={"synapsys.asset"})["data"]["state"], "RESTRICTED")
        d = drill("data:%d:context_id" % M_ASSET, "enhance", world={})["data"]; self.assertEqual((d["state"], d["pairs"]), ("NONE_VISIBLE_TO_ACTOR", []))

    def test_computed_relation_needs_a_readable_work_object(self):
        sid = next(m["menu_id"] for m in D["menus"] if m.get("model") == "synapsys.strategy" and any(e["field"] == "service_ids" for e in m["edges"]))
        self.assertEqual(drill("data:%d:service_ids" % sid, "enhance")["data"]["total_readable"], 2)
        self.assertEqual(drill("data:%d:service_ids" % sid, "enhance", hidden={"synapsys.work.object": {50, 51}})["data"]["total_readable"], 0)


class ReusedRenderers(unittest.TestCase):
    def test_existing_scaffold_screen_is_embedded_through_the_provider(self):
        called = []
        def prov(mid, a, depth): called.append((mid, a, depth)); return {"result": "OK", "html": "<p>EXISTING-SCAFFOLD</p>", "binding_status": "X"}
        o = drill("scr:%d" % M_STRATEGY, "enrich", ctx=mkctx(screen_html=prov)); self.assertEqual(called, [(M_STRATEGY, aid(M_STRATEGY), "enrich")]); self.assertEqual(o["screen"]["html"], "<p>EXISTING-SCAFFOLD</p>")
        self.assertIn("EXISTING-SCAFFOLD", R.render_page(V.assemble(D, *TV.parts(), "steward", "drill", drill="scr:%d" % M_STRATEGY, ctx=mkctx(screen_html=prov), requested_actor="steward", strategy_groups=TV.GROUPS)))

    def test_provider_refusal_is_a_reason_code_only(self):
        for r in ({"result": "REFUSED", "reason": "NO_READ_RIGHT"}, {"result": "REFUSED", "reason": "secret detail: SELECT * FROM x"}, None, {"result": "OK"}):
            o = drill("scr:%d" % M_STRATEGY, ctx=mkctx(screen_html=lambda *a, r=r: r))["screen"]; self.assertNotEqual(o["state"], "OK"); self.assertIsNone(o["html"]); self.assertNotIn("SELECT", json.dumps(o))
        self.assertEqual(drill("scr:%d" % M_STRATEGY, ctx=mkctx(screen_html=lambda *a: {"result": "REFUSED", "reason": "NO_READ_RIGHT"}))["screen"]["reason"], "NO_READ_RIGHT")
        self.assertEqual(drill("scr:%d" % M_STRATEGY, ctx={})["screen"]["state"], "SOURCE_UNVERIFIED")

    def test_unsafe_markup_from_an_embedded_renderer_is_refused(self):
        for bad in ("<script>alert(1)</script>", '<img src=x onerror=alert(1)>', '<a href="javascript:alert(1)">x</a>', "<iframe src=x></iframe>"):
            o = drill("scr:%d" % M_STRATEGY, ctx=mkctx(screen_html=lambda *a, b=bad: {"result": "OK", "html": b}))["screen"]; self.assertEqual((o["state"], o["html"]), ("EMBED_REFUSED_UNSAFE_MARKUP", None))

    def test_existing_lens_renderer_is_used_with_its_override_rules(self):
        o = drill("scr:%d" % M_STRATEGY, "enable"); self.assertIn("syn-el", o["lens"]); self.assertIn('data-element="menu:%d"' % M_STRATEGY, o["lens"]); self.assertIn('data-mode="enable"', o["lens"])
        o = drill("scr:%d" % M_STRATEGY, "enable", ov="menu:%d@enrich" % M_STRATEGY); self.assertIn('data-mode="enrich"', o["lens"]); self.assertIn('data-override="yes"', o["lens"])
        parent = [m for m in D["menus"] if m["menu_id"] == MENU[M_STRATEGY]["parent_id"]][0]["menu_id"]
        o = drill("scr:%d" % M_STRATEGY, "enable", ov="menu:%d@enrich" % parent); self.assertIn('data-mode="enrich"', o["lens"]); self.assertIn('data-override="inherited"', o["lens"])    # recursive: the ancestor's override cascades
        o = drill("scr:%d" % M_STRATEGY, "enable", ov="menu:%d@enrich;menu:%d@enhance" % (parent, M_STRATEGY)); self.assertIn('data-mode="enhance"', o["lens"])                           # local override wins
        o = drill("scr:%d" % M_STRATEGY, "enable", ov="<script>@enrich;a@bogus"); self.assertIn('data-mode="enable"', o["lens"])                                                          # unsafe or unknown dropped

    def test_lens_style_block_is_not_repeated(self):
        for p in ("scr:%d" % M_STRATEGY, "fld:%d:context_id" % M_STRATEGY, "rec:synapsys.asset:90"):
            lens = drill(p, "enrich")["lens"]; self.assertEqual(lens.count(LC.STYLE), 1, p); self.assertEqual(lens.count("<style>"), 1, p)
        self.assertEqual(DR._strip_repeat_style(LC.STYLE + "<a/>" + LC.STYLE + "<b/>"), LC.STYLE + "<a/><b/>")

    def test_no_second_relationship_engine_in_the_drill_module(self):
        src = open(os.path.join(ADDON, "arch_master_drill.py"), encoding="utf-8").read(); tree = ast.parse(src)
        names = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
        self.assertFalse([n for n in names if re.search(r"walk|project|resolve|closure|traverse", n)])
        for must in ("A._instance_edges", "A._edge_state", "G._readable", "G._edge_supported", "LC.render_element", "A.lineage_parents", "LC.lineage"): self.assertIn(must, src, must)
        self.assertNotIn("graph[\"records\"][fm]", src.replace('graph["records"].get(fm, {})', ""))      # no private edge scan outside the shared helpers' contract
        self.assertEqual(T.forbidden_calls(src), []); self.assertNotIn("from odoo", src)

    def test_reused_renderer_modules_are_byte_identical_to_the_remote_head(self):
        """Reuse, not a fork: the five existing modules this interface embeds are pinned to their sha256 at remote HEAD 1a00dce."""
        pins = {"scaffold_wire.py": "b8f3dd01ef3bbf0322aa7a82151f464765f46e477bcf6289e6b1382ecdada25d", "scaffold_view.py": "ad15b1620a7df39572ff1e96bf35705489c22557e3a949a1b53684dae8182c2a",
                "lens_contract.py": "ec6557ec203f5ea423f6fba3882a52c92401cc1f408629cb34aa76ba47ebbd05", "lens_render.py": "70b4c9e9c76862a629d37f769520e2f1f6af9fecee54aa6f15a886dd8f57334f",
                "screen_render.py": "60312b8624a77da99a97fafbbee84e87bfee8bcf789c70d308fb6b8cb3fc4252"}
        import hashlib
        for f, h in pins.items(): self.assertEqual(hashlib.sha256(open(os.path.join(ADDON, f), "rb").read()).hexdigest(), h, f)


class RecordEvidence(unittest.TestCase):
    def rec(self, model, rid, **kw): 
        g, a, n = TV.parts(**kw); return DR.record_evidence(D, g, a, n, model, rid, mkctx(), "enrich")

    def test_outcome_benefit_asset_show_stored_values_only(self):
        o = self.rec("synapsys.outcome", 60); f = {x["field"]: x for x in o["fields"]}
        self.assertEqual((o["state"], f["measure"]["value"], f["baseline_observed"]["value"], f["observed_date"]["value"]), ("OK", "m", "True", "(unset)"))
        b = self.rec("synapsys.benefit", 70); self.assertEqual({x["field"]: x["value"] for x in b["fields"]}["ppv"], "candidate"); self.assertEqual(b["evidence_maturity"]["ppv"], "candidate")
        a = self.rec("synapsys.asset", 90); self.assertEqual({x["field"]: x["value"] for x in a["fields"]}["qualifies"], "False"); self.assertEqual({x["field"]: x["value"] for x in a["fields"]}["rights_confirmed"], "False")

    def test_relationships_are_readable_only_and_navigable(self):
        o = self.rec("synapsys.outcome", 60); rel = {(r["direction"], r["field"], r["id"]) for r in o["relationships"]}
        self.assertIn(("out", "benefit_ids", 70), rel); self.assertIn(("in", "progress_outcome_id", 50), rel)
        self.assertEqual({r["rec"] for r in o["relationships"] if r["field"] == "benefit_ids"}, {"rec:synapsys.benefit:70"})
        o = self.rec("synapsys.outcome", 60, hidden={"synapsys.benefit": {70}}); self.assertNotIn(("out", "benefit_ids", 70), {(r["direction"], r["field"], r["id"]) for r in o["relationships"]})
        a = self.rec("synapsys.asset", 90); self.assertIn(("in", "asset_id", 80), {(r["direction"], r["field"], r["id"]) for r in a["relationships"]})

    def test_authority_ppv_and_ai_promotion_boundaries(self):
        for m, i in (("synapsys.outcome", 60), ("synapsys.benefit", 70), ("synapsys.asset", 90)):
            o = self.rec(m, i); self.assertEqual((o["authority"]["ppv_movement"], o["authority"]["ai_promotion"]), (False, False)); self.assertIn("Steward", o["authority"]["acceptance"]); self.assertIn("promotes none", o["authority"]["acceptance"])

    def test_realisation_is_unobserved_without_linked_evidence_and_shown_as_stored_with_it(self):
        self.assertEqual(self.rec("synapsys.benefit", 70)["realisation"]["state"], "UNOBSERVED_BY_THIS_INTERFACE")
        w = TV.world2(); w["synapsys.fractal"][1].update(res_model="synapsys.benefit", res_id=70, realisation="observed")
        g, a, n = TV.parts(w); o = DR.record_evidence(D, g, a, n, "synapsys.benefit", 70, mkctx(), "enrich")
        self.assertEqual((o["realisation"]["state"], o["linked_fractal_evidence"][0]["realisation"]), ("SOURCE_VALUES_SHOWN_NOT_VERIFIED", "observed"))
        o2 = DR.record_evidence(D, g, a, n, "synapsys.benefit", 70, mkctx(), "enrich"); self.assertEqual(self.rec("synapsys.outcome", 60)["linked_fractal_evidence"], [])
        g, a, n = TV.parts(w, hidden={"synapsys.fractal": {1}}); self.assertEqual(DR.record_evidence(D, g, a, n, "synapsys.benefit", 70, mkctx())["linked_fractal_evidence"], [])
        g, a, n = TV.parts(w); a["visible"]["synapsys.fractal"].discard(1)                    # public function: a row in the graph but not readable by this actor must not appear
        o = DR.record_evidence(D, g, a, n, "synapsys.benefit", 70, mkctx()); self.assertEqual((o["linked_fractal_evidence"], o["realisation"]["state"]), ([], "UNOBSERVED_BY_THIS_INTERFACE"))

    def test_asset_qualification_flag_inconsistent_with_the_rule_is_flagged_never_corrected(self):
        w = TV.world2(); w["synapsys.asset"][90].update(qualifies=True, qualified_benefit_count=2, rights_confirmed=True)
        g, a, n = TV.parts(w); o = DR.record_evidence(D, g, a, n, "synapsys.asset", 90, mkctx()); self.assertEqual(o["evidence_maturity"]["qualification_flag_check"], "FLAG_INCONSISTENT_WITH_RULE_FOR_STEWARD_REVIEW")
        self.assertEqual({x["field"]: x["value"] for x in o["fields"]}["qualifies"], "True")                         # the stored flag is shown as stored
        w["synapsys.asset"][90].update(qualified_benefit_count=3); g, a, n = TV.parts(w); self.assertEqual(DR.record_evidence(D, g, a, n, "synapsys.asset", 90, mkctx())["evidence_maturity"]["qualification_flag_check"], "NOT_ASSESSED_BY_THIS_INTERFACE")
        w["synapsys.asset"][90].update(rights_confirmed=False); g, a, n = TV.parts(w); self.assertIn("INCONSISTENT", DR.record_evidence(D, g, a, n, "synapsys.asset", 90, mkctx())["evidence_maturity"]["qualification_flag_check"])
        self.assertEqual(self.rec("synapsys.benefit", 70)["evidence_maturity"]["qualification_flag_check"], "NOT_ASSESSED_BY_THIS_INTERFACE")

    def test_absent_field_is_stated_and_long_text_is_shortened(self):
        w = TV.world2(); w["synapsys.outcome"][60]["acceptance_condition"] = "x" * 900
        g, a, n = TV.parts(w); o = DR.record_evidence(D, g, a, n, "synapsys.outcome", 60, mkctx()); f = {x["field"]: x for x in o["fields"]}
        self.assertEqual((len(f["acceptance_condition"]["value"]), f["acceptance_condition"]["truncated"]), (400, True))
        g, a, n = TV.parts(w, absent={"synapsys.outcome": {"measure"}}); o = DR.record_evidence(D, g, a, n, "synapsys.outcome", 60, mkctx()); self.assertEqual({x["field"]: x["state"] for x in o["fields"]}["measure"], "FIELD_NOT_PRESENT")

    def test_asset_embeds_the_existing_record_screen_only_for_assets(self):
        a = self.rec("synapsys.asset", 90); self.assertEqual(a["record_screen"]["state"], "OK"); self.assertIn("RECORD:SCR.ASSET.RECORD:90", a["record_screen"]["html"])
        self.assertNotIn("record_screen", self.rec("synapsys.outcome", 60)); g, an, n = TV.parts()
        o = DR.record_evidence(D, g, an, n, "synapsys.asset", 90, mkctx(record_screen_html=lambda *x: {"result": "OK", "html": "<script>x</script>"})); self.assertEqual(o["record_screen"]["state"], "REFUSED")
        o = DR.record_evidence(D, g, an, n, "synapsys.asset", 90, {}); self.assertNotIn("record_screen", o)

    def test_lineage_ancestors_come_from_stored_links(self):
        o = self.rec("synapsys.asset", 90); self.assertIn('data-element="synapsys.asset:90"', o["lens"])
        g, a, n = TV.parts(); self.assertEqual(A.lineage_parents(g, a)["ast:90"], "ctx:1")
        ov = LC.parse_overrides("ctx:1@enrich"); el = LC.element("synapsys.asset:90", "x", ancestors=list(LC.lineage(A.lineage_parents(g, a), "ast:90")))
        self.assertIn("ctx:1", el["ancestors"]); self.assertEqual(LC.mode_for("ast:90", "enable", ov, el["ancestors"]), "enrich")


class ContextBuilder(unittest.TestCase):
    class AErr(Exception): pass
    class Rec:
        def __init__(s, **k): s.__dict__.update(k)
    class RS(list):
        @property
        def ids(s): return [r.id for r in s]
    def env(self, menus=None, act=None, cli=None, fields=None, deny=()):
        AE = self.AErr; outer = self
        class Model:
            def __init__(m, name): m.name = name
            def search(m, dom):
                if m.name in deny: raise AE("denied")
                ids = dom[0][2]
                if m.name == "ir.ui.menu": return outer.RS(outer.Rec(id=i) for i in ids if menus is None or i in menus)
                if m.name == "ir.actions.act_window": return outer.RS(outer.Rec(id=i, **(act or {}).get(i, {})) for i in ids if act is not None and i in act)
                if m.name == "ir.actions.client": return outer.RS(outer.Rec(id=i, **(cli or {}).get(i, {})) for i in ids if cli is not None and i in cli)
            def fields_get(m, f, attrs):
                if m.name in deny or fields is None or m.name not in fields: raise AE("denied")
                return {k: v for k, v in fields[m.name].items() if k in f}
            def sudo(m, *a, **k): raise AssertionError("sudo is forbidden")
            with_user = sudo
        class Env:
            def __getitem__(e, k): return Model(k)
            sudo = Model.sudo; with_user = Model.sudo
        return Env()
    class SW:
        def __init__(s, ok=("synapsys.strategy",), boom=False, bind=None): s.ok, s.boom, s.bind = set(ok), boom, bind
        def _can_read(s, env, model):
            if s.boom: raise RuntimeError("x")
            return model in s.ok
        def bindings(s):
            if s.bind is None: raise ValueError("bad")
            return ([], {}, s.bind)
        def menu_enable(s, env, action_id, menu_id, sid, depth): return {"result": "OK", "html": "<p>x</p>"}
        def screen_record(s, env, sid, rid, depth): return {"result": "OK"}
    class SV:
        @staticmethod
        def render(out, depth): return "<p>rec</p>"

    def test_visible_menus_come_from_the_callers_env_and_fail_closed(self):
        self.assertEqual(CX.visible_menu_ids(self.env(menus={M_STRATEGY, M_FORM}), D, self.AErr), {M_STRATEGY, M_FORM})
        self.assertIsNone(CX.visible_menu_ids(self.env(deny={"ir.ui.menu"}), D, self.AErr))

    def test_readable_models_use_the_existing_fail_closed_helper(self):
        self.assertEqual(CX.readable_models(self.env(), D, self.AErr, self.SW(ok=("synapsys.strategy", "synapsys.asset"))), {"synapsys.strategy", "synapsys.asset"})
        self.assertIsNone(CX.readable_models(self.env(), D, self.AErr, self.SW(boom=True)))

    def test_effective_actions_unreadable_and_failed_probe(self):
        e = good_effective()
        act = {a: {"res_model": v.get("res_model"), "domain": v.get("domain"), "view_mode": v.get("view_mode")} for a, v in e["actions"].items() if "view_mode" in v}
        cli = {a: {"tag": v["tag"]} for a, v in e["actions"].items() if "tag" in v}
        got = CX.effective_actions(self.env(act=act, cli=cli), D, self.AErr); self.assertEqual(got[aid(M_STRATEGY)]["res_model"], "synapsys.strategy")
        act.pop(aid(M_STRATEGY)); got = CX.effective_actions(self.env(act=act, cli=cli), D, self.AErr); self.assertEqual(got[aid(M_STRATEGY)], "UNREADABLE")
        self.assertIsNone(CX.effective_actions(self.env(deny={"ir.actions.act_window"}), D, self.AErr))

    def test_effective_fields_per_model_fail_closed(self):
        e = good_effective()["fields"]; got = CX.effective_fields(self.env(fields=e), D, self.AErr)
        self.assertEqual(got["synapsys.strategy"]["context_id"], {"type": "many2one", "relation": "synapsys.context"})
        e2 = dict(e); e2.pop("synapsys.asset"); got = CX.effective_fields(self.env(fields=e2), D, self.AErr); self.assertEqual(got["synapsys.asset"], "UNREADABLE")

    def test_bindings_and_build_ctx_never_raise(self):
        self.assertIsNone(CX.bindings_by_menu(self.SW(bind=None))); self.assertEqual(CX.bindings_by_menu(self.SW(bind={1: {}})), {1: {}})
        ctx = CX.build_ctx(self.env(deny={"ir.ui.menu", "ir.actions.act_window"}), D, self.AErr, self.SW(boom=True), self.SV)
        self.assertEqual((ctx["visible_menu_ids"], ctx["readable_models"], ctx["effective"]["actions"], ctx["bindings"]), (None, None, None, None))
        self.assertEqual(ctx["screen_html"](1, 2, "enable")["result"], "OK")
        class Bad(self.SW):
            def menu_enable(s, *a): raise RuntimeError("x")
            def screen_record(s, *a): raise RuntimeError("x")
        c2 = CX.build_ctx(self.env(), D, self.AErr, Bad(), self.SV); self.assertEqual(c2["screen_html"](1, 2, "enable"), {"result": "REFUSED", "reason": "NOT_AVAILABLE"}); self.assertEqual(c2["record_screen_html"]("S", 1, "enable"), {"result": "REFUSED", "html": None})
        self.assertEqual(ctx["record_screen_html"]("S", 1, "enable")["html"], "<p>rec</p>")

    def test_no_write_no_elevation_in_the_builder(self):
        src = open(os.path.join(ADDON, "arch_master_ctx.py"), encoding="utf-8").read(); self.assertEqual(T.forbidden_calls(src), []); self.assertNotIn("from odoo", src)
        CX.build_ctx(self.env(), D, self.AErr, self.SW(), self.SV)           # the fake env raises AssertionError on sudo / with_user


class Rendering(unittest.TestCase):
    def page(self, path, depth="enhance", ctx="default", world=None, role="steward", **kw):
        g, a, n = TV.parts(world, **kw); d = V.assemble(D, g, a, n, role, "drill", "Form", depth, "steward", TV.GROUPS, roles=A.load_roles(), drill=path, ctx=mkctx() if ctx == "default" else ctx)
        return d, R.render_page(d)

    def test_three_columns_and_embeds_render(self):
        _, h = self.page("scr:%d" % M_STRATEGY)
        for k in ("Canonical definition", "Effective platform configuration", "Actual operational records", "Existing scaffold screen (reused renderer)", "Lens (reused renderer"): self.assertIn(k, h, k)
        self.assertIn("SCAFFOLD:%d:%d:enhance" % (M_STRATEGY, aid(M_STRATEGY)), h); self.assertIn('class="sm-embed"', h)

    def test_only_permitted_native_links_and_override_anchors_are_hrefs(self):
        for path in ("app", "grp:%d" % M_FORM, "scr:%d" % M_STRATEGY, "data:%d:context_id" % M_ASSET, "rec:synapsys.asset:90"):
            _, h = self.page(path); body = h.split("</style>", 1)[1]
            for href in re.findall(r'href="([^"]*)"', body): self.assertTrue(re.fullmatch(r"/odoo/action-\d+(/\d+)?|#", href), (path, href))
        _, h = self.page("scr:%d" % M_STRATEGY, ctx=mkctx(visible_menu_ids=None)); self.assertNotIn('href="/odoo/action-', h)
        _, h = self.page("scr:%d" % M_STRATEGY, ctx={}); self.assertNotIn('href="/odoo/action-', h); self.assertIn("SOURCE_UNVERIFIED", h)
        _, h = self.page("scr:%d" % M_STRATEGY); self.assertIn('href="/odoo/action-%d"' % aid(M_STRATEGY), h)
        self.assertIn("SOURCE_UNVERIFIED when not read", h)                                              # the page tells the reader how an unread configuration is shown

    def test_hostile_record_text_is_escaped_in_every_drill_level(self):
        w = TV.world2(); evil = '<img src=x onerror=alert(1)>"\'&'
        w["synapsys.asset"][90]["name"] = evil; w["synapsys.outcome"][60]["name"] = evil; w["synapsys.outcome"][60]["acceptance_condition"] = evil; w["synapsys.benefit"][70]["code"] = evil; w["synapsys.context"][1]["code"] = evil
        for path in ("app", "grp:%d" % M_FORM, "scr:%d" % M_ASSET, "fld:%d:context_id" % M_ASSET, "data:%d:context_id" % M_ASSET, "rec:synapsys.asset:90", "rec:synapsys.outcome:60", "rec:synapsys.benefit:70"):
            for depth in V.DEPTHS:
                _, h = self.page(path, depth, world=w); body = h.split("</style>", 1)[1]
                self.assertNotRegex(body, r"<img|<script|<[a-zA-Z][^>]*\sonerror\s*=|<a [^>]*href=.javascript:"); self.assertNotIn("<iframe", body)

    def test_breadcrumb_and_children_are_buttons_with_drill_data(self):
        _, h = self.page("scr:%d" % M_STRATEGY); self.assertEqual(len(re.findall(r'<nav class="sm-crumbs"', h)), 1)
        crumbs = h.split('<nav class="sm-crumbs"', 1)[1].split("</nav>", 1)[0]; self.assertEqual(len(re.findall(r'data-drill="[^"]+"', crumbs)), 4); self.assertEqual(crumbs.count('aria-current="page"'), 1)
        _, h = self.page("grp:%d" % M_FORM); self.assertIn('data-drill="scr:%d"' % M_STRATEGY, h)

    def test_not_available_page_discloses_nothing_and_offers_a_way_back(self):
        _, h = self.page("rec:synapsys.asset:5551"); self.assertIn("NOT_AVAILABLE", h); self.assertIn('data-drill="app"', h); self.assertNotIn("5551", h.split("</style>", 1)[1])
        _, h = self.page("scr:99999"); self.assertIn("NOT_AVAILABLE", h)

    def test_override_anchors_are_keyboard_operable(self):
        _, h = self.page("scr:%d" % M_STRATEGY, "enable"); self.assertIn('role="button" tabindex="0" href="#" data-ovel=', h); self.assertNotIn('<a class="tg" data-ovel=', h)

    def test_record_page_states_boundaries(self):
        d, h = self.page("rec:synapsys.benefit:70", "enrich"); body = h.split("</style>", 1)[1]
        for k in ("Evidence maturity", "Authority", "Realisation", "PPV movement: False", "AI promotion: False", "promotes none", "UNOBSERVED_BY_THIS_INTERFACE"): self.assertIn(k, body, k)

    def test_drill_section_is_a_listed_section_and_state_is_exposed(self):
        d, h = self.page("app"); self.assertIn('data-section="drill"', h); self.assertEqual(sum(1 for s in V.SECTIONS), 11)


class RealScaffoldRendererReuse(unittest.TestCase):
    """The GENUINE existing renderer (scaffold_wire.menu_enable, driven by the existing RC06 fake environment) flows through the drill-down unchanged."""
    @classmethod
    def setUpClass(cls):
        import test_batch5 as T5
        cls.T5, cls.sw, cls.F0 = T5, T5.sw, T5.F0

    def prov(self, mid, a, depth): return self.sw.menu_enable(self.T5.E5([self.F0.STEW]), a, mid, "", depth)

    def test_all_43_bound_menus_at_three_depths_embed_without_refusal(self):
        for b in self.T5.BOUND:
            for depth in V.DEPTHS:
                o = drill("scr:%d" % b["menu_id"], depth, ctx=mkctx(screen_html=self.prov))["screen"]
                self.assertEqual(o["state"], "OK", (b["menu_id"], depth)); self.assertTrue(o["html"]); self.assertNotRegex(o["html"], r"<\s*script|\son[a-z]+\s*=")
                self.assertEqual(o["binding_status"], self.sw.bindings()[2][b["menu_id"]]["binding_status"])

    def test_the_8_unbound_menus_are_refused_by_the_existing_code_with_its_reason(self):
        self.assertEqual(len(self.T5.UNBOUND), 8)
        for u in self.T5.UNBOUND:
            if u["menu_id"] not in MENU or MENU[u["menu_id"]]["kind"] == "CONTAINER": continue
            o = drill("scr:%d" % u["menu_id"], ctx=mkctx(screen_html=self.prov))["screen"]; self.assertEqual((o["state"], o["reason"], o["html"]), ("REFUSED", "MENU_NOT_BOUND", None))

    def test_a_role_without_read_right_gets_the_existing_refusal(self):
        b = self.T5.BOUND[0]; prov = lambda mid, a, depth: self.sw.menu_enable(self.T5.E5([self.F0.STEW], readable=False), a, mid, "", depth)
        o = drill("scr:%d" % b["menu_id"], ctx=mkctx(screen_html=prov))["screen"]; self.assertEqual((o["state"], o["reason"], o["html"]), ("REFUSED", "NO_READ_RIGHT", None))

    def test_the_page_contains_the_real_renderers_text(self):
        b = self.T5.BOUND[0]; g, a, n = TV.parts(); d = V.assemble(D, g, a, n, "steward", "drill", "Form", "enhance", "steward", TV.GROUPS, drill="scr:%d" % b["menu_id"], ctx=mkctx(screen_html=self.prov))
        real = self.prov(b["menu_id"], b["action_id"], "enhance")["html"]; self.assertIn(real, R.render_page(d))


class Controller(unittest.TestCase):
    SRC = open(os.path.join(ADDON, "controllers", "arch_master.py"), encoding="utf-8").read()
    def test_validates_drill_inputs_before_any_read_and_builds_ctx_only_for_the_drill_section(self):
        body = self.SRC.split("def page(", 1)[1]; i = body.index("arch_master.collect")
        for k in ("unknown drill path", "len(ov) > 4000"): self.assertLess(body.index(k), i, k)
        self.assertIn("if section == 'drill' else None", body); self.assertEqual(T.forbidden_calls(self.SRC), [])
        self.assertIn("arch_master_ctx.build_ctx(request.env", body); self.assertIn("scaffold_wire, scaffold_view", body)


if __name__ == "__main__":
    unittest.main()
