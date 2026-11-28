"""Static integration contracts for the Master Architecture release candidate (no Odoo, no browser). Verifies the manifest delta, the asset and template
contracts against the EXISTING shipped client action (home.js), and that the candidate is self-consistent. Does NOT prove native Odoo execution."""
import ast, hashlib, os, re, shutil, subprocess, sys, tempfile, unittest, xml.etree.ElementTree as ET
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, ".."))
ADDON = os.path.join(ROOT, "addon", "synapsys")
MAN_REL = "release/rc06a_screen_architecture/addon/synapsys/__manifest__.py"
PATCH = os.path.join(ADDON, "candidates", "MASTER_MANIFEST_DELTA.patch")


def apply_delta():
    tmp = tempfile.mkdtemp(); dst = os.path.join(tmp, MAN_REL); os.makedirs(os.path.dirname(dst))
    shutil.copy(os.path.join(ADDON, "__manifest__.py"), dst)
    r = subprocess.run(["patch", "-p1", "--dry-run", "-i", PATCH], cwd=tmp, capture_output=True, text=True)
    ok = r.returncode == 0
    if ok: subprocess.run(["patch", "-p1", "-s", "-i", PATCH], cwd=tmp, check=True)
    return ok, r.stdout + r.stderr, ast.literal_eval(open(dst, encoding="utf-8").read()), open(dst, encoding="utf-8").read()


class ManifestDelta(unittest.TestCase):
    def test_delta_file_is_reproducible(self):
        self.assertEqual(subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "gen_master_manifest_delta.py"), "--check"], capture_output=True).returncode, 0)

    def test_delta_applies_cleanly_and_only_adds(self):
        ok, msg, new, text = apply_delta(); self.assertTrue(ok, msg)
        old = ast.literal_eval(open(os.path.join(ADDON, "__manifest__.py"), encoding="utf-8").read())
        added = [l for l in open(PATCH, encoding="utf-8").read().splitlines() if l.startswith("+") and not l.startswith("+++")]
        removed = [l for l in open(PATCH, encoding="utf-8").read().splitlines() if l.startswith("-") and not l.startswith("---")]
        self.assertEqual(len(added), 2); self.assertEqual(len(removed), 1)                                  # one data line added; the one assets line is rewritten longer
        self.assertEqual({k: v for k, v in new.items() if k not in ("data", "assets")}, {k: v for k, v in old.items() if k not in ("data", "assets")})   # nothing else changes
        self.assertEqual(new["data"], old["data"] + ["candidates/synapsys_master_menu_candidate.xml"])
        a_old, a_new = old["assets"]["web.assets_backend"], new["assets"]["web.assets_backend"]
        self.assertEqual(a_new[:len(a_old)], a_old); self.assertEqual(a_new[len(a_old):], ["synapsys/static/src/master/master_nav.js", "synapsys/static/src/master/master.js", "synapsys/static/src/master/master.xml"])
        self.assertEqual(set(new["assets"]), {"web.assets_backend"})

    def test_every_listed_file_exists_and_nothing_is_listed_twice(self):
        _, _, new, _ = apply_delta()
        for f in new["data"]: self.assertTrue(os.path.exists(os.path.join(ADDON, f)), f)
        for f in new["assets"]["web.assets_backend"]: self.assertTrue(os.path.exists(os.path.join(ROOT, "addon", f)), f)
        self.assertEqual(len(new["data"]), len(set(new["data"]))); self.assertEqual(len(new["assets"]["web.assets_backend"]), len(set(new["assets"]["web.assets_backend"])))

    def test_manifest_itself_is_untouched_in_this_candidate(self):
        self.assertEqual(hashlib.sha256(open(os.path.join(ADDON, "__manifest__.py"), "rb").read()).hexdigest(), "d845bc081eed4423ecaa5f91647c868d003a21e5087f0b56a0d11bac2973ba3b")

    def test_menu_xml_dependencies_exist_in_data_loaded_before_it(self):
        _, _, new, _ = apply_delta(); order = new["data"]; idx = order.index("candidates/synapsys_master_menu_candidate.xml")
        loaded = "".join(open(os.path.join(ADDON, f), encoding="utf-8").read() for f in order[:idx] if f.endswith(".xml"))
        self.assertIn('id="menu_config"', loaded)
        root = ET.parse(os.path.join(ADDON, "candidates", "synapsys_master_menu_candidate.xml")).getroot(); mi = root.find("menuitem")
        self.assertEqual(mi.get("parent"), "menu_config"); self.assertNotIn('id="action_master_architecture"', loaded); self.assertNotIn('id="menu_arch_master"', loaded)
        self.assertEqual(loaded.count("synapsys_master_architecture"), 0)

    def test_candidate_action_tag_is_new_and_unique(self):
        used = [t for f in os.listdir(os.path.join(ADDON, "views")) for t in re.findall(r'name="tag">([^<]+)<', open(os.path.join(ADDON, "views", f), encoding="utf-8").read())]
        self.assertNotIn("synapsys_master_architecture", used); self.assertEqual(len(used), len(set(used)))


class ClientContract(unittest.TestCase):
    MJ = open(os.path.join(ADDON, "static", "src", "master", "master.js"), encoding="utf-8").read()
    HJ = open(os.path.join(ADDON, "static", "src", "home.js"), encoding="utf-8").read()

    @staticmethod
    def imports(src):
        return {m.group(2): {x.strip() for x in m.group(1).split(",")} for m in re.finditer(r'import\s*\{([^}]*)\}\s*from\s*"([^"]+)"', src)}

    def test_every_platform_import_is_one_the_shipped_home_action_already_uses(self):
        mine, home = self.imports(self.MJ), self.imports(self.HJ)
        for spec, names in mine.items():
            if spec.startswith("."): continue
            self.assertIn(spec, home, spec); self.assertTrue(names <= home[spec], (spec, names - home[spec]))

    def test_relative_import_resolves_to_a_listed_asset(self):
        rel = [s for s in self.imports(self.MJ) if s.startswith(".")]; self.assertEqual(rel, ["./master_nav"])
        _, _, new, _ = apply_delta(); self.assertIn("synapsys/static/src/master/master_nav.js", new["assets"]["web.assets_backend"])
        self.assertLess(new["assets"]["web.assets_backend"].index("synapsys/static/src/master/master_nav.js"), new["assets"]["web.assets_backend"].index("synapsys/static/src/master/master.js"))

    def test_component_follows_the_shipped_pattern(self):
        for needle in ('static template = "synapsys.', "setup() {", "proxy(", "onWillStart(", "markup(", 'registry.category("actions").add("synapsys_', "await rpc("):
            self.assertIn(needle, self.MJ, needle); self.assertIn(needle, self.HJ, needle)

    def test_template_name_root_and_directives(self):
        xml = open(os.path.join(ADDON, "static", "src", "master", "master.xml"), encoding="utf-8").read(); root = ET.fromstring(xml)
        self.assertEqual([t.get("{http://www.w3.org/XML/1998/namespace}space") for t in [root]], ["preserve"]); self.assertEqual([t.get("t-name") for t in root], ["synapsys.MasterArchitecture"])
        for d in ('t-on-click="this.onClick"', 't-out="this.state.html"', 't-if="this.state.error"'): self.assertIn(d, xml)
        for d in re.findall(r'(t-[a-z-]+)=', xml): self.assertIn(d, ("t-name", "t-on-click", "t-out", "t-if"))
        home = open(os.path.join(ADDON, "static", "src", "home.xml"), encoding="utf-8").read(); self.assertIn('t-on-click="this.onClick"', home); self.assertIn("this.state.html", home)

    def test_rpc_routes_called_by_the_client_exist_on_the_controller(self):
        ctrl = open(os.path.join(ADDON, "controllers", "arch_master.py"), encoding="utf-8").read()
        for route in re.findall(r'rpc\("(/[^"]+)"', self.MJ): self.assertIn("'%s'" % route, ctrl, route)
        sent = set(re.findall(r"(\w+): n\.\w+", self.MJ)); params = re.search(r"def page\(self, ([^)]*)\)", ctrl).group(1)
        for k in sent: self.assertIn(k, params, k)

    def test_navigation_state_keys_match_what_the_server_accepts(self):
        nav = open(os.path.join(ADDON, "static", "src", "master", "master_nav.js"), encoding="utf-8").read()
        sects = re.search(r'SECTIONS = \[([^\]]*)\]', nav).group(1); import_sections = re.findall(r'"([a-z]+)"', sects)
        sys.path.insert(0, ADDON); import arch_master_views as V
        self.assertEqual(import_sections, list(V.SECTIONS))
        for name, py in (("PERSPECTIVES", ("Form", "Flow", "Evolve")), ("DEPTHS", ("enable", "enhance", "enrich")), ("ACTORS", ("steward", "collaborator", "client"))):
            self.assertEqual(tuple(re.findall(r'"([A-Za-z]+)"', re.search(r'%s = \[([^\]]*)\]' % name, nav).group(1))), py, name)
        import arch_master_drill as DR
        js = re.search(r'DRILL_RE = /\^(.*)\$/;', nav).group(1); jsre = re.compile(js.replace("\\d", "[0-9]"))
        probes = ["app", "grp:1", "scr:186", "view:2", "fld:1:a_b", "data:9:x1", "rec:synapsys.asset:3", "rec:synapsys.context:3", "grp:123456", "Fld:1:a", "fld:1:", "scr:1;", "scr:5\n"]
        jsre = re.compile(js.replace("\\d", "[0-9]"))
        for p in probes:
            py_ok = True
            try: DR.parse_path(p)
            except ValueError: py_ok = False
            self.assertEqual(bool(jsre.fullmatch(p)), py_ok, p)

    def test_menu_candidate_has_no_group_or_access_change(self):
        xml = open(os.path.join(ADDON, "candidates", "synapsys_master_menu_candidate.xml"), encoding="utf-8").read()
        for bad in ("res.groups", "ir.model.access", "ir.rule", "groups=", "implied_ids"): self.assertNotIn(bad, xml)

    def test_release_delta_document_names_the_patch_and_gates(self):
        t = open(os.path.join(ADDON, "candidates", "MASTER_RELEASE_DELTA.md"), encoding="utf-8").read()
        for k in ("MASTER_MANIFEST_DELTA.patch", "D007", "RUN_LOCK", "D009", "H03", "SOURCE_UNVERIFIED", "no schema change", "no ACL change", "no new group", "Rollback"): self.assertIn(k.lower(), t.lower(), k)


if __name__ == "__main__":
    unittest.main()
