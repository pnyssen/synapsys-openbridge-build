"""RC06g offline tests: the 43 menu bindings (Enable panel on the native view) from the Navigator's N1 spec. Offline only; no Odoo, no network, no writes.
What offline tests CANNOT show: the effective read right on a real database, how the panel is placed and looks in a browser at 390 and 1024 px, whether the
web client mounts the panel as intended, and Collaborator or Client behaviour. Those need the Steward-gated dev install and live tests."""
import rc06h_compat
import copy, hashlib, html, json, os, re, shutil, subprocess, sys, tempfile, unittest

import fakes as F
import fakes_core as F0
from fakes import sl, sd, sr, sw, sv

HERE = os.path.dirname(os.path.abspath(__file__))
N1_PATH = os.path.join(HERE, "fixtures", "NAV_N1_RC06_BATCH5_LIVE_MENU_DECLARATION_BINDING_20261127_v1.json")
N1_SHA = "9e316030d709896390c99cf845848d17c2d87e678a08344d0c6da54b43d695ee"
N1 = json.load(open(N1_PATH, encoding="utf-8"))
N1_ROWS = N1["rows"]
DECLS, META = sd.load_declarations()
BIND_PATH = os.path.join(F.ADDON, "data", "screen_bindings_batch5.json")
BDOC = json.load(open(BIND_PATH, encoding="utf-8"))
BROWS = BDOC["rows"]
ROWS, BY_ACTION, BY_MENU = sw.bindings()
MANIFEST = json.load(open(os.path.join(HERE, "golden", "rc06f_tree_manifest.json"), encoding="utf-8"))["files"]
NONE_NOS = [17, 18, 34, 35, 36, 37, 38, 42]
NEW_FILES = {"data/screen_bindings_batch5.json", "screen_binding.py", "controllers/menu_binding.py", "static/src/enable_panel.js", "static/src/enable_panel.xml"}
CHANGED_FILES = {"__manifest__.py", "controllers/__init__.py", "scaffold_wire.py", "screen_render.py"}


class Access(Exception):
    pass


Access.__name__ = "AccessError"


class Rec:
    def __init__(self, id, name="x", **kw):
        self.id, self._name = id, name
        self.kw = kw

    def __bool__(self):
        return True

    def __getitem__(self, k):
        return self.kw[k]


class Native:
    """A native model: check_access('read') raises AccessError unless the actor may read it. Counts every call; any write fails the test."""
    def __init__(self, model, may_read, log):
        self.model, self.may, self.log = model, may_read, log

    def check_access(self, op):
        self.log.append(("check_access", self.model, op))
        if op != "read" or not self.may:
            raise Access("no read")

    def sudo(self):
        raise AssertionError("sudo must never be called")

    def create(self, *a, **k):
        raise AssertionError("no writes")

    write = unlink = create


class Menus:
    def __init__(self, log, visible=True, action_for=None):
        self.log, self.visible, self.action_for = log, visible, action_for or {}

    def search(self, domain, limit=None):
        self.log.append(("menu_search", tuple(map(tuple, domain))))
        if not self.visible:
            return []
        mid = domain[0][2]
        act = self.action_for.get(mid, BY_MENU[mid]["action_id"] if mid in BY_MENU else None)
        return Rec(mid, "ir.ui.menu", action=Rec(act, "ir.actions.act_window") if act else None)

    def sudo(self):
        raise AssertionError("sudo must never be called")


class E5(F0.Env):
    """The RC06 fake environment plus the models a menu binding touches: ir.ui.menu, the native models and env.ref. Reads are logged; writes fail."""
    def __init__(self, groups, readable=True, menu_visible=True, menu_action=None, ref_ids=None, **kw):
        super().__init__(groups, **kw)
        self.readable, self.menu_visible, self.menu_action = readable, menu_visible, menu_action or {}
        self.ref_ids = ref_ids if ref_ids is not None else {r["action_xmlid"]: r["action_id"] for r in ROWS if r.get("action_xmlid")}

    def __getitem__(self, k):
        if k == "ir.ui.menu":
            return Menus(self.log, self.menu_visible, self.menu_action)
        if k in ("synapsys.mesh.registry", "x_service_catalogue"):
            return super().__getitem__(k)
        may = self.readable(k) if callable(self.readable) else self.readable
        return Native(k, may, self.log)

    def ref(self, xmlid, raise_if_not_found=True):
        self.log.append(("ref", xmlid))
        return Rec(self.ref_ids[xmlid], "ir.actions.act_window") if xmlid in self.ref_ids else None


def ok(menu_row, **kw):
    return sw.menu_enable(E5([F0.STEW], **kw), menu_row["action_id"])


def text(h):
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", re.sub(r"<style>.*?</style>", "", h, flags=re.S)))).strip()


BOUND = [r for r in BROWS if r["bind_decision"] == "BIND_ENABLE_OVERLAY_PRESERVE_NATIVE_ACTION"]
UNBOUND = [r for r in BROWS if r["bind_decision"] == "NONE_KEEP_EXISTING_NATIVE"]


class G1_Bindings(unittest.TestCase):
    def test_n1_copy_is_the_navigators_spec_and_the_generator_reproduces_the_binding_file_byte_for_byte(self):
        self.assertEqual(hashlib.sha256(open(N1_PATH, "rb").read()).hexdigest(), N1_SHA)
        p = subprocess.run([sys.executable, os.path.join(HERE, "..", "tools", "gen_batch5_bindings.py"), N1_PATH], capture_output=True, text=True, timeout=60)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout, open(BIND_PATH, encoding="utf-8").read())

    def test_51_rows_43_bound_8_none_and_each_row_equals_its_n1_row(self):
        self.assertEqual((len(N1_ROWS), len(BROWS), len(BOUND), len(UNBOUND)), (51, 51, 43, 8))
        self.assertEqual([r["screen_no"] for r in UNBOUND], NONE_NOS)
        for n, b in zip(N1_ROWS, BROWS):
            self.assertEqual((b["screen_no"], b["menu_id"], b["menu_name"], b["action_id"], b["action_xmlid"], b["action_type"]), (n["screen_no"], n["menu_id"], n["menu_name"], n["action_id"], n["action_xmlid"], n["action_type"]))
            self.assertEqual(b["screen_id"], n["declaration_screen_id"])  # the exact immutable id, never derived from a label
            self.assertEqual(b["bind_decision"], n["bind_decision"])
            self.assertEqual(b["binding_status"], n["source_status"])
            self.assertEqual(b["menu_groups"], {"root": n["acl_current"]["root_menu_groups"], "leaf": n["acl_current"]["leaf_menu_groups"]})

    def test_each_binding_screen_exists_is_unique_and_is_a_noun_or_menu_screen(self):
        ids = [b["screen_id"] for b in BOUND]
        self.assertEqual(len(ids), len(set(ids)))
        for sid in ids:
            self.assertIn(sid, DECLS)
            self.assertIn(DECLS[sid]["screen_type"], ("noun", "menu"))
        self.assertEqual(len({b["menu_id"] for b in BROWS}), 51)
        self.assertEqual(len({b["action_id"] for b in BOUND}), 43)
        self.assertEqual({r["declaration_type"] for r in BOUND}, {"noun", "menu"})
        self.assertEqual(sum(1 for r in BOUND if r["declaration_type"] == "noun"), 27)

    def test_the_three_unused_declarations_are_exactly_the_record_views_and_the_generic_mesh_noun(self):
        unused = set(DECLS) - {b["screen_id"] for b in BOUND}
        self.assertEqual(unused, {"SCR.CONTEXT.RECORD", "SCR.ASSET.RECORD", "SCR.MESH.NOUN"})
        self.assertEqual(set(N1["qa"]["unused_declarations"]), unused)
        mesh_menus = {"Registry", "Elements", "Clusters", "Verbs", "Benefit–Asset links", "Door receipts", "Measures", "Map"}
        for b in BROWS:
            if b["menu_name"] in mesh_menus:
                self.assertNotEqual(b["screen_id"], "SCR.MESH.NOUN")  # it must not stand in for the Mesh specialist menus
        for b in BOUND:
            self.assertNotIn("RECORD", b["screen_id"])

    def test_the_8_none_rows_are_unbound_with_a_reason_and_are_the_ones_n1_names(self):
        names = [r["menu_name"] for r in UNBOUND]
        self.assertEqual(names, ["Architecture register", "Lexicon", "Map", "Registry", "Elements", "Clusters", "Verbs", "Lenses"])
        for r in UNBOUND:
            self.assertIsNone(r["screen_id"]); self.assertTrue(r["none_reason"])
        self.assertEqual([r["menu_groups"]["leaf"] for r in UNBOUND if r["menu_name"] in ("Architecture register", "Lexicon")], [[35], [35]])  # Steward-only references keep leaf 35

    def test_placement_defaults_are_kept_learning_under_navigator_inbox_as_signal_intake_register_and_lexicon_steward_only(self):
        by = {r["menu_name"]: r for r in BROWS}
        self.assertEqual(by["Learning"]["parent_id"], by["Progress"]["parent_id"])
        self.assertEqual(by["Learning"]["current_menu_path"], "Navigator > Learning")
        self.assertEqual(by["Inbox"]["current_menu_path"], "Navigator > Inbox")
        self.assertIn("Signals intake", by["Inbox"]["navigator_placement_default"])
        self.assertTrue(N1["qa"]["kept_learning"] and N1["qa"]["kept_inbox"] and N1["qa"]["steward_only"])
        for n in ("Architecture register", "Lexicon"):
            self.assertIn("Architecture > Form >", by[n]["current_menu_path"]); self.assertEqual(by[n]["menu_groups"]["leaf"], [35])
        self.assertTrue(all(r["menu_groups"]["root"] == [34] for r in BROWS))  # root 34 on every row

    def test_the_binding_table_is_validated_and_bad_tables_are_refused(self):
        import screen_binding as sb
        base = json.load(open(BIND_PATH))
        self.assertEqual(sb.validate(base, DECLS), [])
        def mut(f):
            d = copy.deepcopy(base); f(d); return sb.validate(d, DECLS)
        self.assertTrue(mut(lambda d: d["rows"][0].update(screen_id="SCR.NOPE.MENU")))
        self.assertTrue(mut(lambda d: d["rows"][1].update(screen_id=d["rows"][0]["screen_id"])))  # one screen bound twice
        self.assertTrue(mut(lambda d: d["rows"][0].update(screen_id="SCR.CONTEXT.RECORD")))
        self.assertTrue(mut(lambda d: d["rows"][0].update(screen_id="SCR.MESH.NOUN")))
        self.assertTrue(mut(lambda d: d["rows"][16].update(screen_id="SCR.PURPOSE.NOUN")))  # an unbound row may not carry a screen
        self.assertTrue(mut(lambda d: d["rows"][1].update(menu_id=d["rows"][0]["menu_id"])))
        self.assertTrue(mut(lambda d: d["rows"][0]["native"].pop("model")))
        self.assertTrue(sb.validate({"schema": "x", "rows": []}, DECLS))


class G2_NativeUntouched(unittest.TestCase):
    def test_native_action_fields_are_unchanged_for_all_51_menus(self):
        for n, b in zip(N1_ROWS, BROWS):
            self.assertEqual(b["native"], {"model": n["model"], "view_type": n["view_type"], "action_view_refs": n["action_view_refs"], "action_context": n["action_context"],
                                           "action_domain": n["action_domain"], "client_tag": n["client_tag"]}, b["screen_no"])

    def test_the_actions_defined_in_this_addon_still_say_what_n1_says_model_view_modes_and_domain(self):
        xml = "\n".join(open(os.path.join(F.ADDON, "views", f), encoding="utf-8").read() for f in sorted(os.listdir(os.path.join(F.ADDON, "views"))))
        checked = 0
        for b in BROWS:
            x = b["action_xmlid"]
            if not x or not x.startswith("synapsys."):
                continue
            ms = re.findall(r'<record id="%s" model="ir\.actions\.act_window">(.*?)</record>' % re.escape(x.split(".", 1)[1]), xml, re.S)
            self.assertTrue(ms, x)
            body = "\n".join(ms)  # a window action may be declared in two records (the second only adds a search view)
            self.assertEqual(re.search(r'name="res_model">([^<]+)<', body).group(1), b["native"]["model"], x)
            self.assertEqual(re.search(r'name="view_mode">([^<]+)<', body).group(1), b["native"]["view_type"], x)
            d = re.search(r'name="domain">([^<]*)<', body)
            if d:
                self.assertEqual(re.sub(r"\s+", "", html.unescape(d.group(1))), re.sub(r"\s+", "", str(b["native"]["action_domain"])), x)
            checked += 1
        self.assertEqual(checked, 39)  # the other 10 window actions belong to other modules (synapsys_mesh, synapsys_v19_reference) and are not in this tree; no file of theirs is touched

    def test_file_level_diff_against_rc06f_only_the_expected_files_changed_or_were_added(self):
        now = {}
        for root, _d, fs in os.walk(F.ADDON):
            for f in fs:
                if "__pycache__" in root or f.endswith(".pyc"):
                    continue
                p = os.path.join(root, f)
                now[os.path.relpath(p, F.ADDON)] = hashlib.sha256(open(p, "rb").read()).hexdigest()
        import slice_overlay; now = slice_overlay.strip(now, F.ADDON)   # declared slice overlay only; see test_arch_slice
        added = set(now) - set(MANIFEST)
        removed = set(MANIFEST) - set(now)
        changed = {k for k in MANIFEST if k in now and now[k] != MANIFEST[k]}
        self.assertEqual(removed, set())
        self.assertEqual(added, NEW_FILES)
        self.assertEqual(changed, CHANGED_FILES)
        self.assertEqual(len(now), 69)

    def test_no_new_menu_model_action_acl_group_or_record_rule_anywhere_in_the_tree(self):
        for rel in ("views/synapsys_menus.xml", "views/synapsys_views.xml", "views/synapsys_screens.xml", "views/synapsys_enable_peers.xml", "security/synapsys_security.xml", "security/ir.access.csv"):
            self.assertEqual(hashlib.sha256(open(os.path.join(F.ADDON, rel), "rb").read()).hexdigest(), MANIFEST[rel], rel)  # byte-identical: no menuitem, action, ACL, group or rule added
        for rel in [r for r in MANIFEST if r.startswith(("models/", "migrations/"))] + ["hooks.py", "__init__.py"]:
            self.assertEqual(hashlib.sha256(open(os.path.join(F.ADDON, rel), "rb").read()).hexdigest(), MANIFEST[rel], rel)  # no new model or hook
        for rel in NEW_FILES - {"data/screen_bindings_batch5.json"}:
            code = re.sub(r'""".*?"""', "", open(os.path.join(F.ADDON, rel), encoding="utf-8").read(), flags=re.S)
            for bad in ("<menuitem", "res.groups", "ir.model.access", "ir.rule", "_inherit =", "models.Model", "fields.", "ir.actions.client"):
                self.assertNotIn(bad, code, (rel, bad))
        wire = open(os.path.join(F.ADDON, "scaffold_wire.py"), encoding="utf-8").read()
        self.assertNotIn("models.Model", wire); self.assertNotIn("<menuitem", wire)
        man = open(os.path.join(F.ADDON, "__manifest__.py"), encoding="utf-8").read()
        self.assertEqual(re.findall(r"'data': \[(.*?)\]", man, re.S), re.findall(r"'data': \[(.*?)\]", "'data': [\n        'security/synapsys_security.xml',\n        'security/ir.access.csv',\n        'views/synapsys_views.xml',\n        'views/synapsys_screens.xml',\n        'views/synapsys_menus.xml',\n        'views/synapsys_enable_peers.xml',\n    ]", re.S))  # the data list is unchanged
        self.assertEqual(man.count("enable_panel"), 2)  # the only manifest change: two web assets

    def test_earlier_declaration_files_sources_and_goldens_are_byte_identical_to_rc06f(self):
        for rel in [r for r in MANIFEST if r.startswith("data/")]:
            self.assertEqual(hashlib.sha256(open(os.path.join(F.ADDON, rel), "rb").read()).hexdigest(), MANIFEST[rel], rel)
        for d in sl.DEPTHS:
            o = sw.scaffold_context(F.Env([F.STEW]), d, "1")
            self.assertEqual(rc06h_compat.undo_r5(sv.render(o, d)), open(os.path.join(HERE, "golden", "rc06a_context_noun_view_%s.html" % d), encoding="utf-8").read())
            self.assertEqual(json.dumps(o, sort_keys=True, indent=1), open(os.path.join(HERE, "golden", "rc06a_context_noun_route_%s.json" % d), encoding="utf-8").read())
        golden = {"rc06a_context_noun_view_enable.html": "2517b7891df4b19f9be715d812f37bd98408686f5f7bf137a7d428b39067fc34",
                  "rc06a_context_noun_view_enhance.html": "0e5b1c5f48d9fa6285a541568d0cc297aa080a3fd0169acf70cd8ace7dd05c45",
                  "rc06a_context_noun_view_enrich.html": "aa2501cbf357d432ee2953699c9dfaa408882d283ddc4d9beae4ab0bf08991e3"}
        for f, sha in golden.items():
            self.assertEqual(hashlib.sha256(open(os.path.join(HERE, "golden", f), "rb").read()).hexdigest(), sha, f)  # the RC06f golden bytes, unchanged
        self.assertEqual(len(DECLS), 46)


class G3_Route(unittest.TestCase):
    def test_all_43_bound_menus_return_their_own_screens_enable_panel(self):
        for b in BOUND:
            e = E5([F0.STEW])
            r = sw.menu_enable(e, b["action_id"], b["menu_id"], b["screen_id"])
            self.assertEqual(r["result"], "OK", b["menu_name"])
            self.assertEqual(set(r), {"result", "screen_id", "menu_id", "action_id", "status", "binding_status", "depth", "html", "writes"})  # RC06h adds depth
            self.assertEqual((r["screen_id"], r["menu_id"], r["action_id"], r["writes"], r["binding_status"]), (b["screen_id"], b["menu_id"], b["action_id"], 0, "CANDIDATE_NOT_ADOPTED"))
            self.assertIn('data-page="menu"', r["html"]); self.assertIn('data-screen="%s"' % b["screen_id"], r["html"])  # RC06h: the page, not the RC06g panel
            self.assertNotIn('class="bk"', r["html"])  # no back link: this is a panel on the native view, not a screen
            self.assertNotIn("<script", r["html"])
            # same text as the screen itself at Enable
            d = DECLS[b["screen_id"]]
            direct = sw.scaffold_menu(F.Env([F.STEW]), b["screen_id"], "enable") if d["screen_type"] == "menu" else (sw.scaffold_context(F.Env([F.STEW]), "enable", "") if b["screen_id"] == "SCR.CONTEXT.NOUN" else sw.scaffold_noun(F.Env([F.STEW]), b["screen_id"], "enable", ""))
            self.assertIn(html.escape(sr.strip_status_prefix(direct["frame"]["answer"], direct["frame"]["header"].get("status")), quote=True), r["html"])
            self.assertEqual(r["status"], direct["status"])
            self.assertEqual(all(x[0] != "write" for x in e.log), True)

    def test_the_page_holds_the_frame_the_binding_line_and_the_records_heading_and_one_depth_control(self):
        for b in BOUND:
            h = ok(b)["html"]
            slots = re.findall(r'data-slot="(\w+)"', h)
            if b["screen_id"] == "SCR.SERVICE.NOUN":  # RC06i: the Service 1-3-1 projection
                self.assertEqual(slots, ["header", "answer", "trust", "movement", "value_definition", "value_records", "binding", "records"], b["menu_name"])
            elif b["screen_id"] == "SCR.MESH_MEASURES.MENU":  # RC06i R7: what the page does not know
                self.assertEqual(slots, ["header", "answer", "trust", "movement", "measures_scope", "binding", "records"], b["menu_name"])
            else:
                self.assertEqual(slots, ["header", "answer", "trust", "movement", "binding", "records"], b["menu_name"])
            self.assertEqual(h.count('data-control="detail"'), 1, b["menu_name"])  # exactly one depth control, rendered by the server
            self.assertIn("Depth: Enable", h) if b["screen_id"] != "SCR.SERVICE.NOUN" else None
            self.assertNotIn("Depth: Enhance", h); self.assertNotIn("Depth: Enrich", h)
            self.assertNotIn('data-slot="trust_table"', h)

    def test_context_menu_188_is_served_by_its_noun_screen_and_the_goldens_are_not_involved(self):
        b = BY_MENU[188]
        self.assertEqual(b["screen_id"], "SCR.CONTEXT.NOUN")
        r = ok(b)
        self.assertIn("A bounded setting that contains everything else", r["html"])
        self.assertEqual(sw.menu_enable(E5([F0.STEW]), b["action_id"], 188, "SCR.CONTEXT.RECORD")["reason"], "SCREEN_NOT_BOUND_TO_MENU")  # record views are conditional, never the menu default
        for mid in (220, 221, 222):
            self.assertNotEqual(BY_MENU[mid]["screen_id"], "SCR.MESH.NOUN")
            self.assertEqual(sw.menu_enable(E5([F0.STEW]), BY_MENU[mid]["action_id"], mid, "SCR.MESH.NOUN")["reason"], "SCREEN_NOT_BOUND_TO_MENU")

    def test_the_8_unbound_menus_are_not_routed_to_any_declaration(self):
        for r in UNBOUND:
            e = E5([F0.STEW])
            self.assertEqual(sw.menu_enable(e, r["action_id"], r["menu_id"]), {"result": "REFUSED", "reason": "MENU_NOT_BOUND"}, r["menu_name"])
            self.assertEqual([x for x in e.log if x[0] != "check_access"], [])  # nothing read for them
        for aid in (None, "", "abc", 0, -1, 10 ** 9):
            self.assertEqual(sw.menu_enable(E5([F0.STEW]), aid)["reason"], "MENU_NOT_BOUND")

    def test_refusals_return_a_reason_code_and_nothing_else_and_no_content_anywhere(self):
        b = BY_MENU[200]  # Service
        leak = [DECLS[b["screen_id"]]["title"], SRC_TEXT("Service"), b["screen_id"], b["menu_name"], b["action_xmlid"], "CANDIDATE", "RULED", "html"]
        cases = [
            ("NO_RECOGNISED_ROLE", sw.menu_enable(E5([]), b["action_id"], b["menu_id"], b["screen_id"])),
            ("NO_READ_RIGHT", sw.menu_enable(E5([F0.STEW], readable=False), b["action_id"], b["menu_id"], b["screen_id"])),
            ("NO_READ_RIGHT", sw.menu_enable(E5([F0.COLL], readable=False), b["action_id"], b["menu_id"], "SCR.WRONG.NOUN")),  # no oracle on the screen id before entitlement
            ("UNKNOWN_SCREEN", sw.menu_enable(E5([F0.STEW]), b["action_id"], b["menu_id"], "SCR.NOPE.NOUN")),
            ("SCREEN_NOT_BOUND_TO_MENU", sw.menu_enable(E5([F0.STEW]), b["action_id"], b["menu_id"], "SCR.PROJECT.NOUN")),
            ("MENU_NOT_BOUND", sw.menu_enable(E5([F0.STEW]), 999999, b["menu_id"], b["screen_id"])),
            ("MENU_NOT_BOUND", sw.menu_enable(E5([F0.STEW]), BY_MENU[235 if 235 in BY_MENU else 200]["action_id"] + 0 if False else [r for r in UNBOUND if r["menu_name"] == "Lexicon"][0]["action_id"])),
            ("ANCHOR_MISMATCH", sw.menu_enable(E5([F0.STEW]), b["action_id"], 999, b["screen_id"])),
            ("ANCHOR_MISMATCH", sw.menu_enable(E5([F0.STEW], ref_ids={b["action_xmlid"]: 1}), b["action_id"], b["menu_id"])),
            ("ANCHOR_MISMATCH", sw.menu_enable(E5([F0.STEW], ref_ids={}), b["action_id"], b["menu_id"])),
            ("ANCHOR_MISMATCH", sw.menu_enable(E5([F0.STEW], menu_action={b["menu_id"]: 1}), b["action_id"], b["menu_id"])),
            ("MENU_NOT_VISIBLE", sw.menu_enable(E5([F0.STEW], menu_visible=False), b["action_id"], b["menu_id"])),
            ("DEPTH_NOT_SUPPORTED", sw.menu_enable(E5([F0.STEW]), b["action_id"], b["menu_id"], depth="enrichh")),  # RC06h: enhance and enrich are served, an unknown depth is refused
        ]
        for reason, r in cases:
            self.assertEqual(r, {"result": "REFUSED", "reason": reason}, reason)
            blob = json.dumps(r)
            for s in leak:
                self.assertNotIn(s, blob.replace('"result": "REFUSED"', "").replace(reason, ""), (reason, s))

    def test_an_unentitled_actor_gets_no_content_and_nothing_is_read_beyond_the_check(self):
        for b in BOUND:
            e = E5([F0.STEW], readable=False)
            r = sw.menu_enable(e, b["action_id"], b["menu_id"], b["screen_id"])
            self.assertEqual(r, {"result": "REFUSED", "reason": "NO_READ_RIGHT"}, b["menu_name"])
            self.assertEqual([x[0] for x in e.log], ["check_access"], b["menu_name"])  # no registry, catalogue, menu or declaration read happened
        e = E5([])
        self.assertEqual(sw.menu_enable(e, 290, 179)["reason"], "NO_RECOGNISED_ROLE"); self.assertEqual(e.log, [])  # a Client or portal actor: nothing read at all

    def test_the_actors_real_read_right_is_per_model_not_per_menu_group(self):
        deny = {"synapsys.work.object"}
        for b in BOUND:
            r = sw.menu_enable(E5([F0.STEW], readable=lambda m: m not in deny), b["action_id"], b["menu_id"])
            self.assertEqual(r["result"] == "OK", b["native"]["model"] not in deny, b["menu_name"])
        self.assertEqual(sum(1 for b in BOUND if b["native"]["model"] in deny), 2)  # Progress and Work both sit on synapsys.work.object

    def test_a_wrong_screen_id_is_checked_only_after_entitlement_and_the_menu_given_must_match(self):
        b = BY_MENU[179]
        self.assertEqual(sw.menu_enable(E5([F0.STEW]), b["action_id"], 180)["reason"], "ANCHOR_MISMATCH")  # menu 180 (Inbox) is not the menu of this action
        self.assertEqual(sw.menu_enable(E5([F0.STEW]), b["action_id"], b["menu_id"], "SCR.NAVIGATOR_INBOX.MENU")["reason"], "SCREEN_NOT_BOUND_TO_MENU")
        self.assertEqual(sw.menu_enable(E5([F0.STEW]), b["action_id"], b["menu_id"], b["screen_id"])["result"], "OK")
        self.assertEqual(sw.menu_enable(E5([F0.STEW]), str(b["action_id"]), str(b["menu_id"]) if False else b["menu_id"])["result"], "OK")  # an id sent as a string is the same id

    def test_no_write_no_sudo_no_raw_sql_and_every_environment_call_is_a_read(self):
        for b in BOUND:
            e = E5([F0.STEW])
            sw.menu_enable(e, b["action_id"], b["menu_id"], b["screen_id"])
            for call in e.log:
                self.assertIn(call[0], ("check_access", "ref", "menu_search", "search", "search_cat"), call)
        for f in ("controllers/menu_binding.py", "screen_binding.py", "scaffold_wire.py", "screen_render.py"):
            code = re.sub(r'""".*?"""', "", open(os.path.join(F.ADDON, f), encoding="utf-8").read(), flags=re.S)
            code = "\n".join(l.split("#")[0] for l in code.splitlines())
            for bad in (r"\bsudo\b", r"with_user", r"\.write\(", r"\.create\(", r"\.unlink\(", r"cr\.execute", r"\bexecute\(", r"<script", r"\son[a-z]+=", r"https?://"):
                self.assertIsNone(re.search(bad, code), (f, bad))

    def test_catalogue_and_registry_are_not_read_for_menu_screens_and_catalogue_only_for_the_one_screen_with_peers(self):
        menu_b = [b for b in BOUND if DECLS[b["screen_id"]]["screen_type"] == "menu"]
        self.assertEqual(len(menu_b), 16)
        for b in menu_b:
            e = E5([F0.STEW]); sw.menu_enable(e, b["action_id"], b["menu_id"])
            self.assertEqual({x[0] for x in e.log} & {"search", "search_cat"}, set(), b["menu_name"])
        for b in BOUND:
            if DECLS[b["screen_id"]]["screen_type"] != "noun":
                continue
            e = E5([F0.STEW]); sw.menu_enable(e, b["action_id"], b["menu_id"])
            self.assertEqual(any(x[0] == "search_cat" for x in e.log), b["screen_id"] == "SCR.CONTEXT.NOUN", b["menu_name"])

    def test_the_route_is_user_authenticated_and_one_new_route_only(self):
        c = open(os.path.join(F.ADDON, "controllers", "menu_binding.py"), encoding="utf-8").read()
        self.assertIn("auth='user'", c); self.assertIn("request.env", c); self.assertEqual(c.count("@http.route"), 1); self.assertNotIn("auth='public'", c); self.assertNotIn("auth='none'", c)
        self.assertEqual(open(os.path.join(F.ADDON, "controllers", "scaffold.py"), encoding="utf-8").read().count("@http.route"), 2)
        self.assertIn("from . import menu_binding", open(os.path.join(F.ADDON, "controllers", "__init__.py"), encoding="utf-8").read())


def SRC_TEXT(noun):
    return [e for e in F.REG["elements"] if e["id"] == "N." + noun.upper()][0]["definition"]


class G4_Status(unittest.TestCase):
    def test_source_status_shown_follows_the_screens_own_word_never_ruled_by_default(self):
        ruled_screens = {"SCR.%s.NOUN" % n for n in ("STRATEGY", "PORTFOLIO", "OFFERING", "SHAPE", "DOMAIN", "CANONICAL", "PROGRAMME", "PROJECT", "SERVICE", "WORKFLOW", "OUTCOME", "BENEFIT", "ASSET", "FRACTAL", "CONTEXT")}
        for b in BOUND:
            r = ok(b)
            h = r["html"]
            pill = re.search(r"<h1>.*?<span class=\"tg\">(.*?)</span></h1>", h, re.S).group(1)
            self.assertEqual(pill, r["status"], b["menu_name"])
            self.assertEqual(r["status"] == "RULED", b["screen_id"] in ruled_screens or b["screen_id"] in ("SCR.NAVIGATOR_PROGRESS.MENU", "SCR.NAVIGATOR_INBOX.MENU", "SCR.NAVIGATOR_LEARNING.MENU", "SCR.STRATEGIES.MENU"), b["menu_name"])
            if r["status"] != "RULED":
                self.assertNotIn("RULED", text(h).replace("CANDIDATE", ""), b["menu_name"])
                self.assertIn(r["status"], text(h))  # the non-ruled word is stated in the panel
        for b in BOUND:
            if b["screen_id"].startswith(("SCR.ACTION.", "SCR.MESH_")):
                self.assertEqual(ok(b)["status"], "CANDIDATE", b["menu_name"])

    def test_a_changed_source_status_changes_the_panel_and_nothing_defaults_to_ruled(self):
        b = BY_MENU[222]  # Measures
        s = copy.deepcopy(sd.load_sources(os.path.join(F.ADDON, "data", "screen_sources_batch3.json"))[0])
        s["S19"]["status_word"] = "OPEN"
        o = sd.project_menu(DECLS[b["screen_id"]], "enable", {"groups": {"steward"}, "context_ids": set()}, sw.DEFAULT_ROLE_MAX_DEPTH, s)
        self.assertEqual(o["status"], "OPEN")
        self.assertIn(">OPEN<", sr.render_enable_panel(o, "x"))
        reg = copy.deepcopy(F.REG)
        for e in reg["elements"]:
            if e["id"] == "N.PROJECT":
                e["status"] = "PROPOSAL"
        ev, idx, _ = sw.collect_evidence(F.Env([F.STEW]))
        o2 = sd.project(DECLS["SCR.PROJECT.NOUN"], reg, "enable", {"groups": {"steward"}, "context_ids": set()}, ev, idx, "", sw.DEFAULT_ROLE_MAX_DEPTH)
        self.assertEqual(o2["status"], "PROPOSAL"); self.assertNotIn(">RULED<", sr.render_enable_panel(o2, "x"))

    def test_the_panel_renderer_returns_nothing_for_a_refusal_or_garbage(self):
        for bad in (None, {}, {"result": "REFUSED"}, {"result": "OK"}, "x"):
            self.assertEqual(sr.render_enable_panel(bad), "")


class G5_ClientJs(unittest.TestCase):
    """Runs static/src/enable_panel.js under node with stubs. This proves the component's own logic (what it asks, when it shows, that it fails closed),
    NOT that Odoo 20's web client mounts it where intended: that needs the dev install."""
    HARNESS = r"""
const fs = require('fs');
let src = fs.readFileSync(process.argv[2], 'utf8').replace(/^import .*$/mg, '').replace(/^export /mg, '');
const added = []; const calls = []; let lmMode = 'enable'; const lmSubs = [];
const registry = { category: (c) => ({ add: (k, v) => added.push([c, k, v]) }) };
let reply = { result: 'OK', html: '<b>x</b>' };
const rpc = async (u, p) => { calls.push([u, JSON.parse(JSON.stringify(p))]); if (reply instanceof Error) throw reply; return reply; };
class Component {}
const proxy = (x) => x, markup = (x) => 'M:' + x;
let bus = []; const useBus = (b, ev, f) => bus.push([ev, f]); const onWillDestroy = (f) => { r0.destroy = f; }; const r0 = {};
let ctrl = { action: { type: 'ir.actions.act_window', id: 290 } };
const lm = { get mode() { return lmMode; }, setMode(m) { lmMode = m; lmSubs.forEach(f => f()); }, subscribe(f) { lmSubs.push(f); return () => { lmSubs.length = 0; }; } };
const useService = (n) => n === 'synapsys_lens_mode' ? lm : ({ get currentController() { return ctrl; } });
const body = src + '\nreturn { SynapsysEnablePanel };';
const { SynapsysEnablePanel } = new Function('registry','rpc','Component','proxy','markup','onWillDestroy','useBus','useService', body)(registry, rpc, Component, proxy, markup, onWillDestroy, useBus, useService);
const mk = () => { const c = new SynapsysEnablePanel(); c.env = { bus: {} }; c.setup(); return c; };
const tick = () => new Promise(r => setTimeout(r, 5));
(async () => {
  const r = {};
  r.registered = added.map(a => [a[0], a[1]]);
  let c = mk(); await tick();
  r.first = { calls: calls.slice(), html: c.state.html, bus: bus.map(b => b[0]) };
  calls.length = 0; reply = { result: 'REFUSED', reason: 'NO_READ_RIGHT' }; ctrl = { action: { type: 'ir.actions.act_window', id: 291 } };
  await bus[0][1](); await tick(); r.refused = { calls: calls.slice(), html: c.state.html };
  calls.length = 0; reply = new Error('boom'); ctrl = { action: { type: 'ir.actions.act_window', id: 292 } };
  await bus[0][1](); await tick(); r.error = { calls: calls.slice(), html: c.state.html };
  calls.length = 0; reply = { result: 'OK', html: '<i>y</i>' }; ctrl = { action: { type: 'ir.actions.client', tag: 'x' } };
  await bus[0][1](); await tick(); r.client = { calls: calls.slice(), html: c.state.html };
  calls.length = 0; ctrl = { action: { type: 'ir.actions.act_window', id: 290 } };
  await bus[0][1](); await tick(); r.back = { calls: calls.slice(), html: c.state.html };
  calls.length = 0; await bus[0][1](); await tick(); r.same = { calls: calls.slice() };
  calls.length = 0; ctrl = null; await bus[0][1](); await tick(); r.none = { calls: calls.slice(), html: c.state.html };
  ctrl = { action: { type: 'ir.actions.act_window', id: 290 } }; reply = { result: 'OK', html: '<b>z</b>' }; calls.length = 0; await bus[0][1](); await tick();
  calls.length = 0; lm.setMode('enrich'); await tick(); r.mode = { calls: calls.slice(), html: c.state.html };
  calls.length = 0; lmMode = 'bogus'; lm.setMode('enhance'); await tick(); r.mode2 = { calls: calls.slice() };
  calls.length = 0; lmMode = 'enable'; c.onClick({ target: { closest: (sel) => ({ dataset: { mode: 'enhance' }, sel }) } }); await tick(); r.click = { mode: lmMode, calls: calls.slice() };
  c.onClick({ target: { closest: () => ({ dataset: { mode: 'evil' } }) } }); c.onClick({ target: { closest: () => null } }); c.onClick({ target: {} }); r.clickBad = lmMode;
  r.destroyed = typeof r0.destroy === 'function'; r0.destroy(); r.unsub = lmSubs.length;
  console.log(JSON.stringify(r));
})();
"""

    @classmethod
    def setUpClass(cls):
        if not shutil.which("node"):
            raise unittest.SkipTest("node not available")
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
            f.write(cls.HARNESS)
        p = subprocess.run(["node", f.name, os.path.join(F.ADDON, "static", "src", "enable_panel.js")], capture_output=True, text=True, timeout=30)
        os.unlink(f.name)
        assert p.returncode == 0, p.stderr
        cls.r = json.loads(p.stdout)

    def test_it_is_a_main_component_and_listens_for_action_changes(self):
        self.assertEqual(self.r["registered"], [["main_components", "synapsys_enable_panel"]])
        self.assertEqual(self.r["first"]["bus"], ["ACTION_MANAGER:UI-UPDATED"])

    def test_it_asks_one_read_only_route_by_action_id_only_and_shows_the_servers_html(self):
        self.assertEqual(self.r["first"]["calls"], [["/synapsys/menu/enable", {"action_id": 290, "depth": "enable"}]])  # action id and the shared depth only: no screen id, no menu id, no label derived on the client
        self.assertEqual(self.r["first"]["html"], "M:<b>x</b>")
        self.assertEqual(self.r["back"]["calls"], [["/synapsys/menu/enable", {"action_id": 290, "depth": "enable"}]])
        self.assertEqual(self.r["same"]["calls"], [])  # no repeat call for the same action

    def test_the_shared_depth_tabs_drive_the_page_and_the_subscription_is_released(self):
        self.assertEqual(self.r["mode"]["calls"], [["/synapsys/menu/enable", {"action_id": 290, "depth": "enrich"}]])
        self.assertEqual(self.r["mode2"]["calls"], [["/synapsys/menu/enable", {"action_id": 290, "depth": "enhance"}]])
        self.assertTrue(self.r["destroyed"]); self.assertEqual(self.r["unsub"], 0)

    def test_a_click_on_a_detail_button_goes_to_the_shared_service_and_anything_else_is_ignored(self):
        self.assertEqual(self.r["click"]["mode"], "enhance")
        self.assertEqual(self.r["clickBad"], "enhance")  # an unknown mode, no button, or a target without closest changes nothing

    def test_the_detail_control_is_server_rendered_once_and_the_client_has_one_delegated_handler(self):
        xml = open(os.path.join(F.ADDON, "static", "src", "enable_panel.xml"), encoding="utf-8").read()
        js = open(os.path.join(F.ADDON, "static", "src", "enable_panel.js"), encoding="utf-8").read()
        self.assertIn('const MODES = ["enable", "enhance", "enrich"];', js)
        self.assertIn('useService("synapsys_lens_mode")', js)
        self.assertNotIn("syn-modebar", xml); self.assertNotIn("t-foreach", xml)  # RC06i R1: the duplicate modebar markup is gone from the client template
        self.assertEqual(xml.count("t-on-click"), 1); self.assertEqual(js.count("this.lm.setMode("), 1)
        lens = open(os.path.join(F.ADDON, "static", "src", "lens_mode.js"), encoding="utf-8").read()
        self.assertIn('let mode = "enable";', lens)  # Enable is the default of the one shared mode

    def test_it_fails_closed_a_refusal_an_error_or_a_non_window_action_leaves_no_panel(self):
        self.assertEqual((self.r["refused"]["html"], len(self.r["refused"]["calls"])), ("", 1))
        self.assertEqual((self.r["error"]["html"], len(self.r["error"]["calls"])), ("", 1))
        self.assertEqual((self.r["client"]["html"], self.r["client"]["calls"]), ("", []))  # a client action is never asked about
        self.assertEqual((self.r["none"]["html"], self.r["none"]["calls"]), ("", []))

    def test_the_client_code_writes_nothing_and_touches_no_native_view(self):
        js = open(os.path.join(F.ADDON, "static", "src", "enable_panel.js"), encoding="utf-8").read()
        code = "\n".join(l.split("//")[0] for l in js.splitlines())
        for bad in ("localStorage", "document.", "innerHTML", "eval(", "orm.", "write", "create(", "unlink", "patch(", "t-inherit"):
            self.assertNotIn(bad, code)
        self.assertEqual(js.count("rpc("), 1)
        xml = open(os.path.join(F.ADDON, "static", "src", "enable_panel.xml"), encoding="utf-8").read()
        self.assertNotIn("t-inherit", xml); self.assertEqual(xml.count("t-name="), 1)  # a template of its own: no core template is extended


class G6_AcceptanceChecksOverAllDeclarations(unittest.TestCase):
    def test_checks_1_to_17_still_run_over_all_46_declarations(self):
        import test_screen_arch as T
        self.assertEqual(len(T.ALL), 46)
        self.assertEqual({d["id"] for d, _ in T.ALL}, set(DECLS))


if __name__ == "__main__":
    unittest.main(verbosity=2)
