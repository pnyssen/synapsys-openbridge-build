"""Integration test: the REAL controller code and the REAL client component, with the Odoo platform stubbed.

* Controller: addon/synapsys/controllers/arch_master.py is imported under a stubbed `odoo` package (http.Controller, route, request, AccessError) and called with a fake environment.
  The existing scaffold modules (scaffold_wire, scaffold_view, screen_render, lens_contract...) are the REAL ones; the environment is the existing RC06 fake plus the Master world.
* Client: static/src/master/master.js and master.xml run under REAL OWL 3 (npm @odoo/owl 3.0.0-beta.1) in Chromium. Only the web-client services are stubbed:
  registry (a Map) and rpc (a fetch to the Python server above).

This proves the integration contracts and the whole request path. It is NOT native Odoo execution: no web client, no asset bundler, no ORM, no real roles.
Skips (never fails) when OWL or a browser is unavailable. Set SHOT_DIR to keep screenshots; OWL_ES_JS to point at owl.es.js."""
import ast, http.server, importlib, json, os, shutil, socketserver, subprocess, sys, threading, types, unittest, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, ".."))
ADDON = os.path.join(ROOT, "addon", "synapsys")
sys.path.insert(0, ADDON); sys.path.insert(0, HERE)
import test_arch_master as T
import test_arch_master_views as TV
import test_arch_master_drill as TD
import test_batch5 as T5

VIEWPORTS = [(390, 844), (1024, 768), (1440, 900)]


def find_owl():
    cands = [os.environ.get("OWL_ES_JS"), os.path.expanduser("~/.cache/synapsys-owl/node_modules/@odoo/owl/dist/owl.es.js"), "/tmp/owl/node_modules/@odoo/owl/dist/owl.es.js"]
    for c in cands:
        if c and os.path.exists(c): return c
    cache = os.path.expanduser("~/.cache/synapsys-owl"); os.makedirs(cache, exist_ok=True)
    try:
        subprocess.run(["npm", "install", "--silent", "--no-audit", "--no-fund", "@odoo/owl@3.0.0-beta.1"], cwd=cache, capture_output=True, timeout=180, check=True)
    except Exception:
        return None
    p = os.path.join(cache, "node_modules", "@odoo", "owl", "dist", "owl.es.js")
    return p if os.path.exists(p) else None


# ---------------------------------------------------------------------------------------------------------------- stubbed odoo package + real controller
def install_stub_odoo():
    for name in [n for n in sys.modules if n == "odoo" or n.startswith("odoo.")]: del sys.modules[name]
    odoo = types.ModuleType("odoo"); odoo.__path__ = []
    http = types.ModuleType("odoo.http")
    class Controller: pass
    http.Controller = Controller
    def route(path, **kw):
        def deco(f): f._route = (path, kw); return f
        return deco
    http.route = route; http.request = types.SimpleNamespace(env=None)
    exc = types.ModuleType("odoo.exceptions"); exc.AccessError = T.AccessError
    odoo.http, odoo.exceptions = http, exc
    addons = types.ModuleType("odoo.addons"); addons.__path__ = []
    syn = types.ModuleType("odoo.addons.synapsys"); syn.__path__ = [ADDON]
    ctl = types.ModuleType("odoo.addons.synapsys.controllers"); ctl.__path__ = [os.path.join(ADDON, "controllers")]
    models = types.ModuleType("odoo.addons.synapsys.models"); models.__path__ = []
    work = types.ModuleType("odoo.addons.synapsys.models.work")
    tree = ast.parse(open(os.path.join(ADDON, "models", "work.py"), encoding="utf-8").read())
    for node in tree.body:                                   # the REAL declared strategy groups, read as literals (the model file itself needs Odoo)
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") in ("BUILD_FROM_V19", "DRAFTS"):
            setattr(work, node.targets[0].id, ast.literal_eval(node.value))
    for n, m in (("odoo", odoo), ("odoo.http", http), ("odoo.exceptions", exc), ("odoo.addons", addons), ("odoo.addons.synapsys", syn), ("odoo.addons.synapsys.controllers", ctl),
                 ("odoo.addons.synapsys.models", models), ("odoo.addons.synapsys.models.work", work)):
        sys.modules[n] = m
    addons.synapsys = syn; odoo.addons = addons; syn.controllers = ctl; syn.models = models; models.work = work
    mod = importlib.import_module("odoo.addons.synapsys.controllers.arch_master")
    return mod, http


class WorldModel(T.Model):
    """The Master fake model plus what the real scaffold helper asks of a native model: check_access('read')."""
    def check_access(self, op):
        if op != "read" or self.restricted: raise T.AccessError("no read")
    def search(self, domain, limit=None, order=None):
        return []        # the real helper's own-rights lookups (actor Context ids): this fake database has no memberships, same as the RC06 Native fake
    def fields_get(self, fields, attrs):
        return {f: {"type": "many2one", "relation": None} for f in fields}


class HybridEnv(T5.E5):
    """RC06 fake env (for the real scaffold_wire) + the Master world (for collect) + menu/action probes. Reads only; writes and sudo fail."""
    def __init__(self, groups, world, restricted=(), hidden=None, menus_visible=None, act_ok=True):
        super().__init__(groups, readable=lambda m: m not in restricted)
        self.world, self.restricted_models, self.menus_visible, self.act_ok = world, set(restricted), menus_visible, act_ok
        self.fake = TV.T.env_for(world, restricted=restricted, hidden=hidden)
        self.eff = TD.good_effective()
    def __getitem__(self, k):
        if k == "ir.ui.menu":
            outer = self
            class AllMenus(T5.Menus):
                def search(s, domain, limit=None):
                    if domain and domain[0][1] == "in":
                        ids = [i for i in domain[0][2] if outer.menus_visible is None or i in outer.menus_visible]
                        return types.SimpleNamespace(ids=ids, __iter__=None)
                    return super().search(domain, limit)
            return AllMenus(self.log, True)
        if k in ("ir.actions.act_window", "ir.actions.client"):
            outer = self; kind = k
            class Acts:
                def search(s, domain):
                    if not outer.act_ok: raise T.AccessError("denied")
                    out = []
                    for i in domain[0][2]:
                        a = outer.eff["actions"].get(i)
                        if a is None: continue
                        if kind.endswith("window") and "view_mode" in a: out.append(types.SimpleNamespace(id=i, res_model=a["res_model"], domain=a["domain"], view_mode=a["view_mode"]))
                        if kind.endswith("client") and "tag" in a: out.append(types.SimpleNamespace(id=i, tag=a["tag"]))
                    return out
            return Acts()
        if k in ("synapsys.mesh.registry", "x_service_catalogue"):
            base, world = super().__getitem__(k), (self.fake.m.get(k))
            class Dual:                                   # the Master collect() reads rows (search_read / _fields); the real scaffold helper uses the RC06 registry fake
                def __getattr__(s, name):
                    return getattr(world, name) if world is not None and name in ("search_read", "_fields") else getattr(base, name)
            return Dual()
        if k in self.fake.m:
            m = self.fake.m[k]; w = WorldModel(m.rows, m._fields, restricted=m.restricted)
            fg = self.eff["fields"].get(k)
            if fg is not None: w.fields_get = lambda f, attrs, fg=fg: {x: fg[x] for x in f if x in fg}
            return w
        return super().__getitem__(k)


def make_server(owl_js, mod, http, state):
    ctrl = mod.ArchitectureMaster()
    srv_dir = ADDON
    class H(http_server.BaseHTTPRequestHandler):
        def log_message(s, *a): pass
        def send(s, code, ctype, body):
            s.send_response(code); s.send_header("Content-Type", ctype); s.send_header("Content-Length", str(len(body))); s.end_headers(); s.wfile.write(body)
        def do_GET(s):
            u = urllib.parse.urlparse(s.path); q = urllib.parse.parse_qs(u.query)
            if u.path == "/":
                s.send(200, "text/html", HARNESS.encode())
            elif u.path == "/owl.js": s.send(200, "text/javascript", open(owl_js, "rb").read())
            elif u.path == "/stub/registry.js": s.send(200, "text/javascript", REGISTRY_STUB.encode())
            elif u.path == "/stub/rpc.js": s.send(200, "text/javascript", RPC_STUB.encode())
            elif u.path == "/master/master.js": s.send(200, "text/javascript", open(os.path.join(srv_dir, "static", "src", "master", "master.js"), "rb").read())
            elif u.path == "/master/master_nav": s.send(200, "text/javascript", open(os.path.join(srv_dir, "static", "src", "master", "master_nav.js"), "rb").read())
            elif u.path == "/master/master.xml": s.send(200, "text/xml", open(os.path.join(srv_dir, "static", "src", "master", "master.xml"), "rb").read())
            else: s.send(404, "text/plain", b"no")
        def do_POST(s):
            n = int(s.headers.get("Content-Length", 0)); body = json.loads(s.rfile.read(n) or b"{}"); role = urllib.parse.parse_qs(urllib.parse.urlparse(s.path).query).get("role", ["steward"])[0]
            state["calls"].append(body)
            if state.get("fail"): return s.send(200, "application/json", json.dumps({"error": "unknown section", "writes": 0}).encode())
            groups = {"steward": [T5.F0.STEW], "collaborator": [T5.F0.COLL], "other": []}[role]
            http.request.env = HybridEnv(groups, TV.world2(), restricted=state.get("restricted", ()), hidden=state.get("hidden"), menus_visible=state.get("menus_visible"), act_ok=state.get("act_ok", True))
            route = {"/synapsys/architecture/master/page": ctrl.page, "/synapsys/architecture/master": ctrl.master}[body["url"]]
            s.send(200, "application/json", json.dumps(route(**body["params"])).encode())
    return H


import http.server as http_server
HARNESS = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>OWL harness</title>
<script type="importmap">{"imports":{"@odoo/owl":"/owl.js","@web/core/registry":"/stub/registry.js","@web/core/network/rpc":"/stub/rpc.js"}}</script>
<style>body{margin:0;font-family:system-ui}</style></head><body><div id="host"></div>
<script type="module">
import { mount } from "@odoo/owl"; import { registry } from "@web/core/registry"; import "/master/master.js";
const Comp = registry.category("actions").get("synapsys_master_architecture");
const xml = await (await fetch("/master/master.xml")).text();
window.__comp = Comp; window.__app = await mount(Comp, document.getElementById("host"), { templates: xml }); window.__mounted = true;
</script></body></html>"""
REGISTRY_STUB = """const cats = {}; export const registry = { category(n) { return cats[n] || (cats[n] = { m: new Map(), add(k, v) { this.m.set(k, v); return this; }, get(k) { return this.m.get(k); } }); } };"""
RPC_STUB = """window.__rpc = []; export async function rpc(url, params) { window.__rpc.push({ url, params }); const r = await fetch("/rpc" + location.search, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ url, params }) }); return await r.json(); }"""


class Controller(unittest.TestCase):
    """The real controller functions under the stubbed odoo package, driven through the hybrid fake environment."""
    @classmethod
    def setUpClass(cls):
        cls.mod, cls.http = install_stub_odoo()
        cls.c = cls.mod.ArchitectureMaster()

    def call(self, name, groups=None, **kw):
        self.http.request.env = HybridEnv(groups if groups is not None else [T5.F0.STEW], TV.world2(), **{k: kw.pop(k) for k in list(kw) if k in ("restricted", "hidden", "menus_visible", "act_ok")})
        return getattr(self.c, name)(**kw)

    def test_routes_are_registered_post_jsonrpc_user_auth(self):
        for fn, path in ((self.c.master, "/synapsys/architecture/master"), (self.c.page, "/synapsys/architecture/master/page")):
            self.assertEqual(fn._route[0], path); self.assertEqual((fn._route[1]["type"], fn._route[1]["auth"], fn._route[1]["methods"]), ("jsonrpc", "user", ["POST"]))

    def test_every_section_renders_through_the_real_controller(self):
        for role, groups in (("steward", [T5.F0.STEW]), ("collaborator", [T5.F0.COLL]), ("other", [])):
            for sec in TV.V.SECTIONS:
                r = self.call("page", groups, section=sec, depth="enhance"); self.assertIn("html", r, (role, sec)); self.assertEqual((r["writes"], r["role"]), (0, role)); self.assertIn('data-section="%s"' % sec, r["html"])

    def test_invalid_inputs_are_rejected_before_any_read(self):
        env_calls = []
        for kw in (dict(section="x"), dict(perspective="x"), dict(depth="x"), dict(actor="x"), dict(context_id="1"), dict(context_id=True), dict(drill=5), dict(ov=5), dict(ov="a" * 4001)):
            r = self.call("page", **kw); self.assertIn("error", r, kw); self.assertEqual(r["writes"], 0); self.assertNotIn("html", r)

    def test_bad_or_hidden_drill_paths_get_the_uniform_page_not_an_error(self):
        pages = {self.call("page", section="drill", drill=d)["html"].split("</style>", 1)[1] for d in ("scr:99999", "rec:synapsys.asset:5551", "fld:186:Bad", "grp:1;x", "scr:186\n", "rec:synapsys.context:1")}
        self.assertEqual(len(pages), 1); self.assertIn("NOT_AVAILABLE", pages.pop())

    def test_drill_context_is_built_only_for_the_drill_section(self):
        self.assertNotIn("Canonical definition", self.call("page", section="value")["html"])
        h = self.call("page", section="drill", drill="scr:%d" % TD.M_STRATEGY, depth="enhance")["html"]
        for k in ("Canonical definition", "Effective platform configuration", "MATCHES_DEFINITION", "href=\"/odoo/action-%d\"" % TD.aid(TD.M_STRATEGY)): self.assertIn(k, h, k)

    def test_effective_configuration_is_unverified_when_the_platform_read_fails(self):
        h = self.call("page", section="drill", drill="scr:%d" % TD.M_STRATEGY, act_ok=False)["html"]; self.assertIn("SOURCE_UNVERIFIED", h); self.assertNotIn("MATCHES_DEFINITION", h)

    def test_no_link_for_a_menu_the_caller_cannot_see(self):
        h = self.call("page", section="drill", drill="scr:%d" % TD.M_STRATEGY, menus_visible=set())["html"]; self.assertNotIn('href="/odoo/action-', h)
        h = self.call("page", section="drill", drill="scr:%d" % TD.M_STRATEGY, menus_visible={TD.M_STRATEGY})["html"]; self.assertIn('href="/odoo/action-', h)

    def test_hidden_and_restricted_rows_never_reach_the_page(self):
        w = TV.world2(); w["synapsys.asset"][367]["name"] = "SECRET-367"
        self.http.request.env = HybridEnv([T5.F0.COLL], w, hidden={"synapsys.asset": {367}})
        for d in ("data:%d:context_id" % TD.M_ASSET, "rec:synapsys.asset:367", "app"):
            self.assertNotIn("SECRET-367", self.c.page(section="drill", drill=d, depth="enrich")["html"])
        r = self.call("page", section="drill", drill="rec:synapsys.asset:90", restricted={"synapsys.asset"}); self.assertIn("NOT_AVAILABLE", r["html"])

    def test_real_existing_scaffold_screen_is_embedded_for_a_bound_menu(self):
        b = T5.BOUND[0]; r = self.call("page", section="drill", drill="scr:%d" % b["menu_id"], depth="enhance")
        self.assertIn("Existing scaffold screen (reused renderer)", r["html"]); self.assertIn('class="sm-embed"', r["html"])
        env = HybridEnv([T5.F0.STEW], TV.world2()); real = T5.sw.menu_enable(env, b["action_id"], b["menu_id"], "", "enhance")
        self.assertEqual(real["result"], "OK", real); self.assertIn(real["html"], r["html"])                       # the genuine renderer's output, byte for byte
        self.assertNotIn("REFUSED", r["html"].split("Existing scaffold screen", 1)[1].split("Lens (reused", 1)[0])

    def test_every_bound_menu_embeds_the_real_screen_through_the_whole_controller_path(self):
        for b in T5.BOUND:
            r = self.call("page", section="drill", drill="scr:%d" % b["menu_id"], depth="enrich")
            seg = r["html"].split("Existing scaffold screen", 1)[1].split("Lens (reused", 1)[0]; self.assertNotIn("REFUSED", seg, b["menu_id"]); self.assertIn('class="sm-embed"', seg, b["menu_id"])
        for u in T5.UNBOUND:
            if u["menu_id"] in TD.MENU and TD.MENU[u["menu_id"]]["kind"] != "CONTAINER":
                seg = self.call("page", section="drill", drill="scr:%d" % u["menu_id"])["html"].split("Existing scaffold screen", 1)[1].split("Lens (reused", 1)[0]; self.assertIn("MENU_NOT_BOUND", seg, u["menu_id"])

    def test_a_role_without_a_recognised_group_gets_the_existing_refusal_not_a_screen(self):
        b = T5.BOUND[0]; seg = self.call("page", [], section="drill", drill="scr:%d" % b["menu_id"])["html"].split("Existing scaffold screen", 1)[1].split("Lens (reused", 1)[0]; self.assertIn("NO_RECOGNISED_ROLE", seg)

    def test_roles_map_to_the_installed_groups(self):
        self.assertEqual(self.call("page", [T5.F0.STEW], section="actors")["role"], "steward"); self.assertEqual(self.call("page", [T5.F0.COLL], section="actors")["role"], "collaborator")
        self.assertEqual(self.call("page", [], section="actors")["role"], "other")

    def test_json_endpoint_still_answers(self):
        r = self.call("master", perspective="Flow"); self.assertEqual((r["perspective"], r["writes"]), ("Flow", 0))


class OwlBrowser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.owl = find_owl()
        if not cls.owl: raise unittest.SkipTest("OWL 3 is not available (no network for npm)")
        try:
            from playwright.sync_api import sync_playwright
        except Exception as ex: raise unittest.SkipTest("playwright not importable: %s" % ex)
        cls.pw = sync_playwright().start()
        try: cls.browser = cls.pw.chromium.launch()
        except Exception as ex:
            cls.pw.stop(); raise unittest.SkipTest("no launchable browser: %s" % str(ex)[:100])
        cls.mod, cls.http = install_stub_odoo(); cls.state = {"calls": []}
        cls.srv = socketserver.ThreadingTCPServer(("127.0.0.1", 0), make_server(cls.owl, cls.mod, cls.http, cls.state)); cls.srv.daemon_threads = True
        cls.port = cls.srv.server_address[1]; threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.shots = os.environ.get("SHOT_DIR")
        if cls.shots: os.makedirs(cls.shots, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "srv"): cls.srv.shutdown()
        if hasattr(cls, "browser"): cls.browser.close()
        if hasattr(cls, "pw"): cls.pw.stop()

    def open(self, w=1024, h=768, role="steward", ready=".syn-master", **state):
        self.state.clear(); self.state.update({"calls": []}); self.state.update(state)
        ctx = self.browser.new_context(viewport={"width": w, "height": h}); page = ctx.new_page(); errs = []
        page.on("console", lambda m: errs.append(("console", m.text)) if m.type == "error" else None); page.on("pageerror", lambda e: errs.append(("pageerror", str(e))))
        page.goto("http://127.0.0.1:%d/?role=%s" % (self.port, role)); page.wait_for_function("window.__mounted === true", timeout=20000); page.wait_for_selector(ready); return ctx, page, errs

    def press(self, page, **ds):
        sel = "button.sm-b" + "".join('[data-%s="%s"]' % (k, v) for k, v in ds.items()); n = page.evaluate("window.__rpc.length")
        page.click(sel); page.wait_for_function("n => window.__rpc.length > n", arg=n, timeout=10000); page.wait_for_timeout(120)

    def last(self, page): return page.evaluate("window.__rpc[window.__rpc.length-1]")

    def direct(self, page, drill):
        """Direct navigation to a drill path that no visible control links to: a button carrying the same data attribute, as a crafted or stale link would."""
        n = page.evaluate("window.__rpc.length")
        page.evaluate("""(d) => { const b = document.createElement('button'); b.id = 'direct-nav'; b.dataset.drill = d; b.textContent = 'x'; document.querySelector('.syn-master main').appendChild(b); }""", drill)
        page.click("#direct-nav"); page.wait_for_function("n => window.__rpc.length > n", arg=n, timeout=10000); page.wait_for_timeout(150)

    def test_component_mounts_under_real_owl_and_first_request_is_the_initial_state(self):
        ctx, page, errs = self.open()
        try:
            self.assertEqual(page.evaluate("window.__rpc.length"), 1); r = page.evaluate("window.__rpc[0]")
            self.assertEqual(r["url"], "/synapsys/architecture/master/page"); self.assertEqual(r["params"], {"section": "overview", "perspective": "Form", "depth": "enable", "actor": "steward", "drill": "app", "ov": ""})
            self.assertEqual(page.get_attribute(".syn-master", "data-section"), "overview"); self.assertEqual(errs, [])
        finally: ctx.close()

    def test_navigation_sends_exactly_the_new_state_and_moves_focus(self):
        ctx, page, errs = self.open()
        try:
            self.press(page, section="value"); self.assertEqual(self.last(page)["params"]["section"], "value"); self.assertEqual(page.get_attribute(".syn-master", "data-section"), "value")
            self.assertEqual(page.evaluate("document.activeElement.id"), "sm-main")
            self.press(page, persp="Flow"); p = self.last(page)["params"]; self.assertEqual((p["section"], p["perspective"]), ("perspectives", "Flow"))
            self.press(page, depth="enrich"); self.assertEqual(self.last(page)["params"]["depth"], "enrich"); self.assertEqual(page.get_attribute(".syn-master", "data-depth"), "enrich")
            self.press(page, actor="client"); self.assertEqual(self.last(page)["params"]["actor"], "client")
            self.assertEqual(errs, [])
        finally: ctx.close()

    def test_a_noop_press_and_an_invalid_control_send_nothing(self):
        ctx, page, errs = self.open()
        try:
            n = page.evaluate("window.__rpc.length"); page.click('button.sm-b[data-section="overview"]'); page.wait_for_timeout(250); self.assertEqual(page.evaluate("window.__rpc.length"), n)
            page.evaluate("""() => { const host = document.querySelector('.syn-master main'); for (const [k, v] of [['drill', 'scr:1;x'], ['section', 'admin'], ['depth', 'enrichest'], ['actor', 'root'], ['persp', 'Caption']]) { const b = document.createElement('button'); b.className = 'evil'; b.dataset[k] = v; b.textContent = 'x'; host.appendChild(b); } }""")
            for el in page.query_selector_all("button.evil"): el.click()
            page.wait_for_timeout(250); self.assertEqual(page.evaluate("window.__rpc.length"), n); self.assertEqual(errs, [])
        finally: ctx.close()

    def test_full_drill_down_application_to_data_and_back(self):
        ctx, page, errs = self.open()
        try:
            self.press(page, section="drill"); self.assertEqual(self.last(page)["params"]["drill"], "app")
            path = ["grp:%d" % TD.M_ARCH, "grp:%d" % TD.M_FORM, "scr:%d" % TD.M_STRATEGY, "view:%d" % TD.M_STRATEGY, "fld:%d:context_id" % TD.M_STRATEGY, "data:%d:context_id" % TD.M_STRATEGY]
            for d in path:
                self.press(page, drill=d); self.assertEqual(self.last(page)["params"]["drill"], d); self.assertEqual(self.last(page)["params"]["section"], "drill")
                self.assertIn("Drill-down", page.inner_text("#sm-main"))
            self.press(page, depth="enhance"); self.assertEqual(self.last(page)["params"]["drill"], path[-1])                   # depth change keeps the drill position
            self.assertIn("From", page.inner_text("#sm-main"))
            page.click('nav.sm-crumbs button[data-drill="app"]'); page.wait_for_function("n => window.__rpc.length > n", arg=page.evaluate("window.__rpc.length") - 1); page.wait_for_timeout(150)
            self.assertEqual(self.last(page)["params"]["drill"], "app"); self.assertEqual(errs, [])
        finally: ctx.close()

    def test_lens_override_control_works_through_the_real_component(self):
        ctx, page, errs = self.open()
        try:
            self.press(page, section="drill"); self.press(page, drill="grp:%d" % TD.M_ARCH); self.press(page, drill="grp:%d" % TD.M_FORM); self.press(page, drill="scr:%d" % TD.M_STRATEGY)
            self.assertEqual(page.get_attribute('.syn-el[data-element="menu:%d"]' % TD.M_STRATEGY, "data-mode"), "enable")
            n = page.evaluate("window.__rpc.length"); page.click('a.tg[data-ovel="menu:%d"]' % TD.M_STRATEGY); page.wait_for_function("n => window.__rpc.length > n", arg=n); page.wait_for_timeout(150)
            self.assertEqual(self.last(page)["params"]["ov"], "menu:%d@enhance" % TD.M_STRATEGY)
            self.assertEqual(page.get_attribute('.syn-el[data-element="menu:%d"]' % TD.M_STRATEGY, "data-mode"), "enhance"); self.assertEqual(page.get_attribute('.syn-el[data-element="menu:%d"]' % TD.M_STRATEGY, "data-override"), "yes")
            self.assertEqual(errs, [])
        finally: ctx.close()

    def test_a_server_error_is_shown_not_swallowed_and_nothing_else_breaks(self):
        ctx, page, errs = self.open(ready=".alert", fail=True)
        try:
            self.assertIn("Master Architecture is not available", page.inner_text(".alert")); self.assertEqual(page.locator(".syn-master").count(), 0); self.assertEqual(errs, [])
        finally: ctx.close()

    def test_role_is_the_servers_decision(self):
        for role in ("steward", "collaborator", "other"):
            ctx, page, errs = self.open(role=role)
            try:
                self.press(page, section="actors"); t = page.inner_text("#sm-main"); self.assertIn("Your actual role on this server: " + role, t)
                self.press(page, actor="client"); self.assertIn("DEFINITION_ONLY_NOT_TESTED", page.inner_text("#sm-main")); self.assertEqual(errs, [])
            finally: ctx.close()

    def test_drill_pages_have_no_overflow_and_no_errors_at_each_viewport(self):
        for w, h in VIEWPORTS:
            ctx, page, errs = self.open(w, h)
            try:
                self.press(page, section="drill")
                for d in ["grp:%d" % TD.M_ARCH, "grp:%d" % TD.M_FORM, "scr:%d" % TD.M_STRATEGY, "view:%d" % TD.M_STRATEGY, "fld:%d:context_id" % TD.M_STRATEGY, "data:%d:context_id" % TD.M_ASSET]:
                    if page.locator('button.sm-b[data-drill="%s"]' % d).count(): self.press(page, drill=d)
                    else: self.direct(page, d)                                                          # no visible control leads here: direct navigation
                    bad = page.evaluate("""(w) => { const bad = []; const de = document.documentElement; if (de.scrollWidth > w + 1) bad.push('document ' + de.scrollWidth);
                        for (const el of document.querySelectorAll('.syn-master *')) { if (el.closest('.sm-scroll, .sm-nav, .sm-embed')) continue; const r = el.getBoundingClientRect(); if (r.width > 0 && (r.right > w + 1 || r.left < -1)) { bad.push(el.tagName + '.' + el.className); if (bad.length > 4) break; } } return bad; }""", w)
                    self.assertEqual(bad, [], (w, d))
                    if self.shots and d.startswith(("scr", "data")): page.screenshot(path=os.path.join(self.shots, "owl_drill_%s_%d.png" % (d.split(":")[0], w)))
                if page.locator('button.sm-b[data-drill="rec:synapsys.asset:90"]').count(): self.press(page, drill="rec:synapsys.asset:90")
                else: self.direct(page, "rec:synapsys.asset:90")
                self.assertIn("Authority", page.inner_text("#sm-main"))
                if self.shots and w in (390, 1440): page.screenshot(path=os.path.join(self.shots, "owl_record_asset_%d.png" % w))
                self.assertEqual(errs, [], w)
            finally: ctx.close()

    def test_hidden_record_in_the_browser_is_the_uniform_page(self):
        ctx, page, errs = self.open(role="collaborator", hidden={"synapsys.asset": {367}})
        try:
            self.press(page, section="drill"); self.direct(page, "rec:synapsys.asset:367"); a = page.inner_text("#sm-main")
            self.direct(page, "rec:synapsys.asset:5551"); b = page.inner_text("#sm-main"); self.assertEqual(a, b); self.assertIn("NOT_AVAILABLE", a); self.assertNotIn("367", a); self.assertNotIn("5551", a)
            self.direct(page, "rec:synapsys.asset:90"); self.assertIn("Authority", page.inner_text("#sm-main"))                 # a readable record opens by direct navigation too
            self.assertEqual(errs, [])
        finally: ctx.close()


if __name__ == "__main__":
    unittest.main()
