"""Offline tests for the Master Architecture VIEWS and RENDERER (arch_master_views.py, master_render.py) and the unreleased interface candidates.
Fake env only: proves projection, rights-first honesty, escaping, navigation and the 'candidate, not installed' boundary. NOT Odoo ACL behaviour,
NOT a signed-in role test, NOT a V20 render (the real-browser test is separate and renders fixture HTML, not Odoo)."""
import ast, hashlib, importlib.util, json, os, re, subprocess, sys, tempfile, unittest, xml.etree.ElementTree as ET
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, ".."))
ADDON = os.path.join(ROOT, "addon", "synapsys")
sys.path.insert(0, ADDON); sys.path.insert(0, HERE)
import arch_graph as G
import arch_master as A
import arch_master_views as V
import master_render as R
import test_arch_master as T

D = A.load_definition()
GROUPS = {"STR-SS-001": "build", "STR-SS-S4": "live", "STR-SS-S7": "adapt", "STR-" + "UNBREAKABLE" * 16: "build"}


def world2():
    w = T.world()
    p = T.p
    w["synapsys.strategy"] = {20: dict(code="STR-SS-001", name="s1", context_id=p(1), purpose_id=p(10), service_ids=[30, 31], lifecycle="draft"),
                              21: dict(code="STR-SS-S4", name="s4", context_id=p(1), purpose_id=p(10), service_ids=[], lifecycle="draft"),
                              22: dict(code="STR-SS-S7", name="s7", context_id=p(3), purpose_id=p(10), service_ids=[], lifecycle="draft"),
                              23: dict(code="STR-OTHER", name="x", context_id=p(3), purpose_id=p(10), service_ids=[], lifecycle="draft"),
                              24: dict(code="STR-" + "UNBREAKABLE" * 16, name="long", context_id=p(3), purpose_id=p(10), service_ids=[], lifecycle="draft")}
    w["synapsys.service"] = {30: dict(code="A", name="a", context_id=False, method_id=p(40)), 31: dict(code="B", name="b", context_id=p(2), method_id=False)}
    w["synapsys.work.object"] = {50: dict(strategy_id=p(20), service_id=p(30), method_id=p(40), gate_ids=[], progress_outcome_id=p(60), progress_benefit_id=False, progress_asset_id=False),
                                 51: dict(strategy_id=p(20), service_id=p(31), method_id=False, gate_ids=[], progress_outcome_id=False, progress_benefit_id=False, progress_asset_id=False)}
    w["synapsys.outcome"] = {60: dict(name="o", baseline_observed=True, measure="m", observed_date=False, benefit_ids=[70])}
    w["synapsys.benefit"] = {70: dict(code="B1", name="b", ppv="candidate", position=False, lifecycle="x", service_id=p(30))}
    w["synapsys.oba.link"] = {80: dict(benefit_id=p(70), asset_id=p(90), type="x", ppv="candidate")}
    w["synapsys.asset"] = {90: dict(name="a90", context_id=p(1), rights_holder_id=p(5), qualifies=False, qualified_benefit_count=0, rights_confirmed=False, lifecycle="x", ppv="candidate"),
                           367: dict(name="a367", context_id=p(2), rights_holder_id=False, qualifies=False, qualified_benefit_count=0, rights_confirmed=False, lifecycle="x", ppv="candidate")}
    w["synapsys.signal"] = {1: dict(name="s", source="x", state="new"), 2: dict(name="t", source="y", state="new")}
    w["synapsys.fractal"] = {1: dict(code="F1", name="f", context_id=p(1), realisation="observed", ffe_position="form", evidence_state="e", admission="a", gate_level="g")}
    return w


def parts(world=None, **kw):
    return A.collect(T.env_for(world2() if world is None else world, **kw), T.AccessError, D)


def page(section="overview", persp="Form", depth="enable", req="steward", role="steward", world=None, **kw):
    g, a, n = parts(world, **kw)
    d = V.assemble(D, g, a, n, role, section, persp, depth, req, GROUPS, roles=A.load_roles())
    return d, R.render_page(d)


def sig(d, sec): return json.dumps(d[sec], sort_keys=True)


class Views(unittest.TestCase):
    def test_every_section_assembles_and_renders_for_full_sparse_and_restricted(self):
        for kw in ({}, {"world": {}}, {"restricted": {"synapsys.strategy", "synapsys.context", "synapsys.fractal"}}):
            for s in V.SECTIONS:
                d, h = page(s, **kw); self.assertEqual((d["read_only"], d["writes"]), (True, 0)); self.assertIn('data-section="%s"' % s, h)

    def test_value_groups_come_only_from_declared_mapping(self):
        d, _ = page("value", depth="enhance"); g = d["value"]["strategies"]["groups"]
        self.assertEqual({k: v["count"] for k, v in g.items()}, {"live": 1, "build": 2, "adapt": 1}); self.assertEqual(d["value"]["strategies"]["ungrouped_count"], 1)
        self.assertIn("STR-SS-001", [i["label"] for i in g["build"]["items"]]); self.assertEqual(len(g["build"]["items"]), 2)

    def test_value_depth_changes_detail_not_data(self):
        a, _ = page("value", depth="enable"); b, _ = page("value", depth="enrich")
        self.assertEqual(a["value"]["strategies"]["count"], b["value"]["strategies"]["count"]); self.assertEqual(a["value"]["edges"], b["value"]["edges"])
        self.assertEqual(a["value"]["assets"]["items"], []); self.assertTrue(b["value"]["assets"]["items"])

    def test_no_strategy_asset_edge_anywhere(self):
        for s in V.SECTIONS:
            d, h = page(s); self.assertTrue(d.get("value", {"no_strategy_to_asset_edge": True})["no_strategy_to_asset_edge"])
        d, _ = page("perspectives", "Form"); self.assertFalse([1 for r in d["perspectives"]["Form"]["rows"] for x in r["edges"] if r["model"] == "synapsys.strategy" and x["target_model"] == "synapsys.asset"])

    def test_kinematics_nine_actions_27_verbs_ruling_and_hold(self):
        d, _ = page("kinematics", depth="enhance"); k = d["kinematics"]
        self.assertEqual((len(k["actions"]), sum(len(a["verbs"]) for a in k["actions"]), k["execution_authorised"]), (9, 27, False)); self.assertTrue(all(len(a["verbs"]) == 3 for a in k["actions"]))
        by = {c["context_id"]: c for c in k["contexts"]}
        self.assertEqual((by[1]["kind_state"], by[1]["stage"]), ("RULED", "Enhance")); self.assertEqual((by[2]["kind_state"], by[2]["stage"], by[2]["kind"]), ("UNRULED_HOLD", None, None))
        self.assertTrue(by[1]["eligible_names"]); self.assertEqual(by[2]["eligible_names"], [])
        g, a, n = parts(); lo = V.kinematics_view(D, g, a, n, "enable"); self.assertTrue(all(c["eligible_names"] == [] for c in lo["contexts"]))       # names only from enhance up
        self.assertTrue(any(c["eligible"]["verb_ids"] for c in lo["contexts"]))
        self.assertEqual({k2: sorted(v) for k2, v in k["cut_b"].items()}, {"Enable": ["K-1", "K-3", "K-4"], "Enhance": ["K-6", "K-8"], "Enrich": ["K-12"]})

    def test_kinematics_human_only_never_eligible(self):
        d2 = json.loads(json.dumps(D)); d2["verbs"][0]["human_only"] = True; hid = d2["verbs"][0]["id"]
        g, a, n = parts(); k = V.kinematics_view(d2, g, a, n, "enhance")
        self.assertTrue(all(hid not in c["eligible"]["verb_ids"] for c in k["contexts"])); self.assertIn(hid, k["human_only_ids"])

    def test_fractals_tree_is_fk_only_and_loop_safe(self):
        d, _ = page("fractals"); ids = json.dumps(d["fractals"]["tree"])
        self.assertIn("pur:10", ids); self.assertIn("ctx:1", ids); self.assertIn("str:20", ids); self.assertIn("svc:31", ids); self.assertNotIn("svc:30", ids)      # 31 has a direct Context FK; 30 is Work-mediated only: not lineage
        real = A.lineage_parents; A.lineage_parents = lambda g, a: {"a": "b", "b": "a", "c": "r"}
        try: g, a, n = parts(); f = V.fractals_view(D, g, a, n)
        finally: A.lineage_parents = real
        self.assertEqual([x["id"] for x in f["tree"]], ["r"])

    def test_form_flow_evolve_are_materially_different(self):
        d, _ = page("overview"); ps = d["perspectives"]
        self.assertEqual(len({json.dumps([ps[p]["typed_edges"], ps[p]["instance_edges"], [(r["menu_id"], [(x["field"], x["instance_edges"]) for x in r["edges"]]) for r in ps[p]["rows"]]]) for p in G.PERSPECTIVES}), 3)
        self.assertEqual({p: ps[p]["perspective"] for p in ps}, {p: p for p in G.PERSPECTIVES})

    def test_single_perspective_section_renders_only_that_perspective(self):
        d, _ = page("perspectives", "Flow"); self.assertEqual(list(d["perspectives"]), ["Flow"])

    def test_effects_show_source_values_and_never_promote(self):
        d, _ = page("effects"); f = d["effects"]
        self.assertEqual(f["signal"]["records"]["by_value"], {"new": 2}); self.assertEqual(f["benefits"]["records"]["by_value"], {"candidate": 1})
        self.assertEqual(f["realisation"]["source_values"]["by_value"], {"observed": 1}); self.assertEqual(f["realisation"]["state"], "SOURCE_VALUES_SHOWN_NOT_VERIFIED")
        self.assertEqual((f["realisation"]["ai_promotion"], f["realisation"]["ppv_movement"]), (False, False))
        self.assertEqual(f["benefits"]["qualified_assets"]["by_value"], {"False": 2})

    def test_realisation_unobserved_without_source_and_never_zero_when_restricted(self):
        d, _ = page("effects", world={}); self.assertEqual(d["effects"]["realisation"]["state"], "UNOBSERVED"); self.assertEqual(d["effects"]["signal"]["records"]["state"], "NONE_VISIBLE_TO_ACTOR")
        d, _ = page("effects", restricted={"synapsys.signal"}); self.assertEqual((d["effects"]["signal"]["records"]["state"], d["effects"]["signal"]["records"]["total"]), ("RESTRICTED", None))

    def test_absent_evidence_field_stated_not_zeroed(self):
        d, _ = page("effects", absent={"synapsys.signal": {"state"}}); self.assertEqual(d["effects"]["signal"]["records"]["state"], "FIELD_NOT_PRESENT")

    def test_mesh_scaffold_membrane_external(self):
        d, _ = page("mesh"); m = d["mesh"]; sc = {r["context_id"]: r for r in m["scaffold"]}
        self.assertEqual((sc[1]["strategies"], sc[1]["assets"], sc[1]["methods"]), (2, 1, 1)); self.assertIsNone(sc[1]["services_direct_fk"])
        self.assertTrue(any(x["edge"] == "synapsys.strategy.service_ids" and (x["from_context"], x["to_context"]) == (1, 2) for x in m["membrane"]))
        self.assertTrue(m["membrane"] and all(x["from_context"] != x["to_context"] for x in m["membrane"]))      # same-Context edges are never membrane cases
        self.assertTrue(all(x["ruling"] == "UNRULED_NOT_ACCEPTED" for x in m["membrane"]))
        self.assertEqual(m["external"]["asset_rights_holder"]["by_value"], {"(unset)": 1, "5": 1})

    def test_membrane_hides_what_the_actor_cannot_read(self):
        d, _ = page("mesh", hidden={"synapsys.service": {31}}); self.assertFalse(any(x["to_context"] == 2 and x["edge"].endswith("service_ids") for x in d["mesh"]["membrane"]))
        d, _ = page("mesh", hidden={"synapsys.work.object": {51}}); self.assertFalse(any(x["edge"].endswith("service_ids") for x in d["mesh"]["membrane"]))

    def test_actor_perspective_never_widens_data(self):
        base = None
        for role in ("steward", "collaborator"):
            sigs = set()
            for req in V.ACTORS:
                d, _ = page("overview", req=req, role=role); sigs.add(json.dumps({k: d[k] for k in ("value", "kinematics", "fractals", "perspectives", "effects", "mesh", "evidence")}, sort_keys=True))
            self.assertEqual(len(sigs), 1, role)                         # the requested perspective changes NOTHING in the data, only the label

    def test_client_is_hold_and_collaborator_is_source_group_not_tested(self):
        for req in ("collaborator", "client"):
            a = page("actors", req=req, role="steward")[0]["actors"]
            self.assertEqual((a["data_view"], a["perspectives"]["collaborator"]["state"], a["perspectives"]["client"]["state"]), ("DEFINITION_ONLY_NOT_TESTED", "GROUP_IN_SOURCE_NOT_TESTED", "HOLD:H02"))
        a = page("actors", req="steward", role="collaborator")[0]["actors"]; self.assertEqual(a["data_view"], "DEFINITION_ONLY_NOT_TESTED"); self.assertEqual(a["perspectives"]["steward"]["state"], "NOT_YOUR_ACCOUNT")
        a = page("actors", req="collaborator", role="collaborator")[0]["actors"]; self.assertEqual((a["data_view"], a["perspectives"]["collaborator"]["state"]), ("ACTUAL_ACCOUNT", "ACTUAL_ACCOUNT"))
        a = page("actors", req="steward", role="steward")[0]["actors"]; self.assertEqual(a["data_view"], "ACTUAL_ACCOUNT")
        self.assertEqual(len(a["steward_only_menu_ids"]), sum(1 for m in D["menus"] if m["steward_only"])); self.assertGreater(len(a["steward_only_menu_ids"]), 0)
        a = page("actors", req="client", role="other")[0]["actors"]; self.assertEqual(a["data_view"], "DEFINITION_ONLY_NOT_TESTED")

    def test_existing_role_definitions_are_read_from_source_not_created(self):
        r = A.load_roles(); self.assertEqual(sorted(r["groups"]), ["synapsys.group_synapsys_steward", "synapsys.group_synapsys_user"])
        self.assertEqual(r["groups"]["synapsys.group_synapsys_user"]["display_name"], "Collaborator"); self.assertEqual(r["groups"]["synapsys.group_synapsys_steward"]["display_name"], "Steward")
        self.assertEqual(r["groups"]["synapsys.group_synapsys_steward"]["implies"], ["synapsys.group_synapsys_user"]); self.assertIsNone(r["client_group"])
        self.assertTrue(all("client" not in g.lower() for g in r["groups"])); self.assertTrue(all("client" not in k.lower() for a in r["access"].values() for k in a))
        x = subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "gen_arch_master_roles.py"), "--check"], capture_output=True, text=True); self.assertEqual(x.returncode, 0, x.stderr)
        sec = os.path.join(ADDON, "security")
        self.assertEqual(r["source_pins"]["ir_access_csv_sha256"], hashlib.sha256(open(os.path.join(sec, "ir.access.csv"), "rb").read()).hexdigest())

    def test_role_definitions_in_the_actors_view(self):
        rd = page("actors")[0]["actors"]["role_definitions"]; self.assertEqual(rd["state"], "LOADED"); self.assertEqual(rd["client"], "HOLD:H02"); self.assertIsNone(rd["entitled_menus"]["client"])
        self.assertGreater(rd["entitled_menus"]["collaborator"], 0); self.assertGreaterEqual(rd["entitled_menus"]["steward"], rd["entitled_menus"]["collaborator"])
        bm = rd["by_model"]; self.assertEqual(bm["synapsys.architecture"]["steward"]["operations"], "NO_ROW_IN_THIS_ADDON")            # governed by another addon: stated, not guessed
        self.assertIn("c", bm["synapsys.strategy"]["steward"]["operations"]); self.assertIn("r", bm["synapsys.strategy"]["collaborator"]["operations"])
        self.assertTrue(any(v["collaborator"]["row_scoped"] for v in bm.values())); self.assertFalse(any(v["steward"]["row_scoped"] for v in bm.values() if v["steward"]["operations"] not in (None, "NO_ROW_IN_THIS_ADDON") and "c" in v["steward"]["operations"]))
        self.assertEqual(V.actors_view(D, "steward", "steward", None)["role_definitions"]["state"], "ROLES_NOT_LOADED")

    def test_evidence_goes_beyond_counts_and_depth_controls_detail(self):
        e1, _ = page("evidence", depth="enable"); e3, _ = page("evidence", depth="enrich")
        c1 = {c["context_id"]: c for c in e1["evidence"]["chains"]}[1]; c3 = {c["context_id"]: c for c in e3["evidence"]["chains"]}[1]
        self.assertEqual([s["step"] for s in c1["steps"]], [s["step"] for s in c3["steps"]])
        svc = [s for s in c3["steps"] if s["step"] == "Service"]
        if svc: self.assertIn("supporting_work_ids", svc[0]); self.assertNotIn("supporting_work_ids", [s for s in c1["steps"] if s["step"] == "Service"][0])
        self.assertEqual(e3["evidence"]["installed"], False); self.assertEqual(e3["evidence"]["role_tests"], "NOT_TESTED")

    def test_evidence_chain_is_rights_first(self):
        d, _ = page("evidence", depth="enrich", hidden={"synapsys.work.object": {50, 51}})
        c = {c["context_id"]: c for c in d["evidence"]["chains"]}[1]; self.assertEqual((c["stopped_at"], c["reason"]), ("Service", "UNOBSERVED_TO_ACTOR")); self.assertNotIn("50", json.dumps(c))

    def test_unknown_inputs_are_rejected_not_defaulted(self):
        g, a, n = parts()
        for bad in (dict(section="x"), dict(perspective="x"), dict(depth="x")):
            with self.assertRaises(ValueError): V.assemble(D, g, a, n, "steward", **{**dict(section="overview", perspective="Form", depth="enable"), **bad})
        with self.assertRaises(ValueError): V.actors_view(D, "steward", "everyone")

    def test_holds_are_explicit_and_complete(self):
        d, h = page("holds"); ids = [x["id"] for x in d["holds"]]; self.assertEqual(ids, ["H%02d" % i for i in range(1, 11)])
        for i in ids: self.assertIn(i, h)
        self.assertTrue(all(x["state"] and x["text"] for x in d["holds"]))

    def test_every_page_declares_candidate_and_not_installed(self):
        for s in V.SECTIONS:
            d, h = page(s); self.assertEqual(d["status"], "SOURCE_READY_NOT_INSTALLED"); self.assertIn("Candidate · not installed · read-only", h)


class Rendering(unittest.TestCase):
    def test_all_dynamic_values_are_escaped(self):
        w = world2(); evil = '<img src=x onerror=alert(1)>"\'&'
        w["synapsys.context"][1]["code"] = evil; w["synapsys.strategy"][20]["code"] = evil; w["synapsys.asset"][90]["name"] = evil; w["synapsys.purpose"][10]["name"] = evil
        for s in V.SECTIONS:
            for depth in V.DEPTHS:
                _, h = page(s, depth=depth, world=w); body = h.split("</style>", 1)[1]
                self.assertNotIn("<img", body, (s, depth));
                self.assertNotRegex(body, r"<[a-zA-Z][^>]*\sonerror\s*=")

    def test_no_script_tag_or_inline_handler_in_any_page(self):
        for s in V.SECTIONS:
            body = page(s)[1].split("</style>", 1)[1]; self.assertNotRegex(body, r"<script|javascript:|\son[a-z]+\s*="); self.assertNotIn("<iframe", body)

    def test_navigation_controls_are_real_buttons_with_state(self):
        for s in V.SECTIONS:
            _, h = page(s, "Flow", "enhance", "client")
            self.assertEqual(len(re.findall(r'<button type="button" class="sm-b" data-section="[a-z]+" aria-current="page">', h)), 1, s)
            for key, val in (("persp", "Flow"), ("depth", "enhance"), ("actor", "client")):
                self.assertEqual(len(re.findall(r'data-%s="%s" aria-pressed="true"' % (key, val), h)), 1, (s, key))
                self.assertEqual(len(re.findall(r'data-%s="[A-Za-z]+" aria-pressed="true"' % key, h)), 1, (s, key, "exactly one pressed"))
            self.assertNotIn("<a href", h); self.assertEqual(h.count("<button"), h.count("</button>"))

    def test_sections_nav_has_all_eleven_and_labelled(self):
        _, h = page("value"); nav = h.split('<nav class="sm-nav"', 1)[1].split("</nav>", 1)[0]
        self.assertEqual(sorted(re.findall(r'data-section="([a-z]+)"', nav)), sorted(V.SECTIONS)); self.assertEqual(nav.count("<button"), 11)
        self.assertIn('aria-label="Master Architecture sections"', h); self.assertIn('id="sm-main"', h); self.assertIn('aria-live="polite"', h)

    def test_responsive_css_is_declared(self):
        css = R.CSS
        for needle in ("@media (max-width:600px)", "@media (min-width:601px) and (max-width:1024px)", "@media (min-width:1025px)", "min-width:0", "overflow-x:auto",
                       "focus-visible", "prefers-reduced-motion", "minmax(min(100%,260px),1fr)", "position:sticky", "overflow-wrap:anywhere"):
            self.assertIn(needle, css, needle)
        props = re.sub(r"@media[^{]*", "", css)                                  # media CONDITIONS are allowed; fixed widths as PROPERTIES are not
        self.assertIsNone(re.search(r"(?<![a-z-])width:\s*\d{3,}px", props)); self.assertIsNone(re.search(r"min-width:\s*[1-9]\d{2,}px", props))
        self.assertIn("min-height:44px", css)                                   # touch targets on narrow screens
        self.assertNotRegex(css.split("@media")[0], r"\.sm-bar\{[^}]*position:sticky")      # the three-row control bar must not pin itself over a phone screen
        self.assertRegex(css, r"@media \(min-width:601px\)\{\.syn-master \.sm-bar\{position:sticky")

    def test_tables_scroll_inside_their_own_region_and_are_keyboard_reachable(self):
        _, h = page("perspectives"); self.assertEqual(h.count("<table"), h.count('class="sm-scroll" tabindex="0" role="region"'))

    def test_hidden_rows_never_appear_in_html(self):
        w = world2(); w["synapsys.asset"][367]["name"] = "SECRET-ASSET-367"; w["synapsys.context"][2]["code"] = "SECRET-CTX-B"
        for s in V.SECTIONS:
            for depth in V.DEPTHS:
                _, h = page(s, depth=depth, world=w, hidden={"synapsys.asset": {367}, "synapsys.context": {2}}); self.assertNotIn("SECRET-ASSET-367", h); self.assertNotIn("SECRET-CTX-B", h)

    def test_depth_changes_detail_on_the_page(self):
        a = page("value", depth="enable")[1]; b = page("value", depth="enrich")[1]; self.assertNotEqual(a, b); self.assertIn("a90", b); self.assertNotIn("a90", a)

    def test_perspective_changes_content_on_the_page(self):
        pages = {p: page("perspectives", p)[1].split("</style>", 1)[1] for p in G.PERSPECTIVES}
        self.assertEqual(len({re.sub(r'data-perspective="[A-Za-z]+"|aria-pressed="[a-z]+"', "", v) for v in pages.values()}), 3)

    def test_deterministic_pages(self):
        self.assertEqual(page("overview")[1], page("overview")[1])

    def test_renderer_has_no_write_primitive_or_odoo_import(self):
        for f in ("arch_master_views.py", "master_render.py"):
            src = open(os.path.join(ADDON, f), encoding="utf-8").read(); self.assertEqual(T.forbidden_calls(src), [], f); self.assertNotIn("from odoo", src); self.assertNotIn("import odoo", src)


class Candidates(unittest.TestCase):
    MAN = open(os.path.join(ADDON, "__manifest__.py"), encoding="utf-8").read()

    def test_manifest_is_unchanged_so_nothing_is_installed(self):
        self.assertEqual(hashlib.sha256(self.MAN.encode()).hexdigest(), "d845bc081eed4423ecaa5f91647c868d003a21e5087f0b56a0d11bac2973ba3b")   # byte-identical to remote HEAD 1a00dce
        for needle in ("master", "candidates", "arch_master"): self.assertNotIn(needle, self.MAN.lower().replace("synapsys_mesh", ""))

    def test_candidate_menu_xml_is_one_client_action_and_one_menu(self):
        root = ET.parse(os.path.join(ADDON, "candidates", "synapsys_master_menu_candidate.xml")).getroot()
        recs = root.findall("record"); items = root.findall("menuitem")
        self.assertEqual((len(recs), len(items)), (1, 1)); self.assertEqual(recs[0].get("model"), "ir.actions.client")
        self.assertEqual({f.get("name"): f.text for f in recs[0].findall("field")}, {"name": "Master Architecture", "tag": "synapsys_master_architecture"})
        self.assertEqual((items[0].get("parent"), items[0].get("action")), ("menu_config", "action_master_architecture"))
        self.assertNotIn("groups", items[0].attrib)                          # no group is created or widened here

    def test_candidate_not_in_any_data_file_and_not_in_views_dir(self):
        for f in os.listdir(os.path.join(ADDON, "views")): self.assertNotIn("synapsys_master_architecture", open(os.path.join(ADDON, "views", f), encoding="utf-8").read())

    def test_client_action_tag_template_and_route_agree(self):
        js = open(os.path.join(ADDON, "static", "src", "master", "master.js"), encoding="utf-8").read(); xml = open(os.path.join(ADDON, "static", "src", "master", "master.xml"), encoding="utf-8").read()
        self.assertIn('registry.category("actions").add("synapsys_master_architecture"', js); self.assertIn('static template = "synapsys.MasterArchitecture"', js); self.assertIn('t-name="synapsys.MasterArchitecture"', xml)
        self.assertIn('"/synapsys/architecture/master/page"', js); ET.fromstring(xml)
        ctrl = open(os.path.join(ADDON, "controllers", "arch_master.py"), encoding="utf-8").read(); self.assertIn("'/synapsys/architecture/master/page'", ctrl)

    def test_client_js_has_no_dangerous_primitive_and_no_storage(self):
        for f in ("master.js", "master_nav.js"):
            src = open(os.path.join(ADDON, "static", "src", "master", f), encoding="utf-8").read()
            for bad in ("innerHTML", "outerHTML", "eval(", "new Function", "localStorage", "sessionStorage", "document.write", "XMLHttpRequest", "fetch("): self.assertNotIn(bad, src, (f, bad))
        self.assertNotIn("import ", open(os.path.join(ADDON, "static", "src", "master", "master_nav.js"), encoding="utf-8").read())      # pure module

    def test_page_controller_validates_before_reading_and_is_read_only(self):
        src = open(os.path.join(ADDON, "controllers", "arch_master.py"), encoding="utf-8").read(); self.assertEqual(T.forbidden_calls(src), [])
        body = src.split("def page(", 1)[1]; i = body.index("arch_master.collect")
        for k in ("unknown section", "unknown perspective", "unknown depth", "unknown actor perspective", "context_id must be an integer"): self.assertLess(body.index(k), i, k)
        self.assertIn("has_group('synapsys.group_synapsys_steward')", body); self.assertIn("request.env", body)

    def test_release_delta_names_the_exact_gates(self):
        t = open(os.path.join(ADDON, "candidates", "MASTER_RELEASE_DELTA.md"), encoding="utf-8").read()
        for k in ("UNRELEASED", "D007", "RUN_LOCK", "rollback", "No schema change", "No ACL change", "D009", "H03"): self.assertIn(k.lower(), t.lower(), k)

    def test_node_navigation_rules(self):
        js = os.path.join(ADDON, "static", "src", "master", "master_nav.js"); tmp = tempfile.mkdtemp(); mod = os.path.join(tmp, "nav.mjs"); open(mod, "w").write(open(js).read())
        test = os.path.join(tmp, "t.mjs"); open(test, "w").write('''
import { nextState, initialState, controlFrom, SECTIONS, DRILL_RE, parseOv, composeOv } from "./nav.mjs";
import assert from "node:assert/strict";
const s0 = initialState(); assert.deepEqual(s0, {section:"overview",perspective:"Form",depth:"enable",actor:"steward",drill:"app",ov:""});
assert.equal(SECTIONS.length, 11); assert.ok(SECTIONS.includes("drill"));
assert.deepEqual(nextState(s0, {section:"value"}).section, "value");
assert.equal(nextState(s0, {section:"overview"}), null);                       // no-op does not reload
assert.equal(nextState(s0, {section:"admin"}), null);                          // invalid value rejected
assert.equal(nextState(s0, {persp:"Caption"}), null); assert.equal(nextState(s0, {depth:"enrichest"}), null); assert.equal(nextState(s0, {actor:"everyone"}), null);
assert.equal(nextState(s0, {}), null); assert.equal(nextState(s0, undefined), null);
const f = nextState({...s0, section:"value"}, {persp:"Flow"}); assert.equal(f.perspective, "Flow"); assert.equal(f.section, "perspectives");
assert.equal(nextState(s0, {persp:"Flow"}).section, "overview");
assert.equal(nextState({...s0, section:"perspectives"}, {depth:"enrich"}).section, "perspectives");
assert.equal(nextState(s0, {actor:"client"}).actor, "client");
const both = nextState(s0, {section:"perspectives", persp:"Evolve"}); assert.deepEqual([both.section, both.perspective], ["perspectives","Evolve"]);
assert.equal(nextState(s0, {section:"value", persp:"bogus"}), null);
// drill-down
const d = nextState(s0, {drill:"scr:186"}); assert.deepEqual([d.section, d.drill], ["drill","scr:186"]);       // a drill press always lands on the drill section
for (const ok of ["app","grp:183","scr:186","view:186","fld:186:context_id","data:186:context_id","rec:synapsys.asset:90","rec:synapsys.outcome:1","rec:synapsys.benefit:2"]) assert.ok(DRILL_RE.test(ok), ok);
for (const bad of ["","APP","grp:","grp:-1","grp:123456","scr:186\\n","scr:1;x","fld:186:Bad","fld:186:","rec:synapsys.context:1","rec:res.partner:1","rec:synapsys.asset:-1","<script>","../x"]) { assert.ok(!DRILL_RE.test(bad), JSON.stringify(bad)); assert.equal(nextState(s0, {drill:bad}), null, JSON.stringify(bad)); }
assert.equal(nextState({...s0, section:"drill", drill:"app"}, {drill:"app"}), null);                             // no-op
// lens overrides
const o1 = nextState(s0, {ovel:"menu:186", ovmode:"enrich"}); assert.equal(o1.ov, "menu:186@enrich");
const o2 = nextState(o1, {ovel:"menu:184", ovmode:"enhance"}); assert.equal(o2.ov, "menu:186@enrich;menu:184@enhance");
const o3 = nextState(o2, {ovel:"menu:186", ovmode:""}); assert.equal(o3.ov, "menu:184@enhance");                // reset to global
assert.equal(nextState(s0, {ovel:"<x>", ovmode:"enrich"}), null); assert.equal(nextState(s0, {ovel:"a", ovmode:"bogus"}), null); assert.equal(nextState(s0, {ovel:"a".repeat(81), ovmode:"enrich"}), null);
assert.equal(nextState(o1, {ovel:"menu:186", ovmode:"enrich"}), null);                                         // already set: no-op
assert.deepEqual([...parseOv("a@enrich;b@bogus;;@enable;c@enable")], [["a","enrich"],["c","enable"]]); assert.equal(composeOv(parseOv("a@enrich;c@enable")), "a@enrich;c@enable");
const el = {dataset:{}, parentElement:{dataset:{depth:"enrich"}, parentElement:null}}; assert.equal(controlFrom(el).depth, "enrich");
assert.equal(controlFrom({dataset:{drill:"app"}, parentElement:null}).drill, "app"); assert.equal(controlFrom({dataset:{ovel:"x", ovmode:"enable"}, parentElement:null}).ovel, "x");
assert.equal(controlFrom({dataset:{}, parentElement:null}), null); assert.equal(controlFrom(null), null);
assert.equal(s0.section, "overview"); assert.equal(s0.ov, "");                                                   // never mutates the previous state
console.log("NODE_NAV_OK");
''')
        r = subprocess.run(["node", test], capture_output=True, text=True); self.assertEqual(r.returncode, 0, r.stderr + r.stdout); self.assertIn("NODE_NAV_OK", r.stdout)


if __name__ == "__main__":
    unittest.main()
