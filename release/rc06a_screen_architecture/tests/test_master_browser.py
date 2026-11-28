"""REAL-BROWSER test of the Master Architecture interface (Chromium via Playwright) at 390, 768, 1024 and 1440 px.

What this IS: the real Python engine + renderer produce each page from fixture records; the real navigation module (static/src/master/master_nav.js)
decides every state change; a real browser lays the real CSS out and handles real clicks and key presses.
What this is NOT: Odoo, the OWL client action, a signed-in role session, or a V20 render. Those stay NOT_TESTED until a D007 release and real accounts.
Skips (never fails) when no browser can be launched. Set SHOT_DIR to keep screenshots."""
import hashlib, http.server, json, os, re, shutil, socketserver, sys, tempfile, threading, unittest, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, ".."))
ADDON = os.path.join(ROOT, "addon", "synapsys")
sys.path.insert(0, ADDON); sys.path.insert(0, HERE)
import test_arch_master_views as TV
import arch_master_views as V, master_render as R

VIEWPORTS = [(390, 844), (768, 1024), (1024, 768), (1440, 900)]
STATE = ("section", "perspective", "depth", "actor")
HARNESS = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Master harness</title>
<style>body{margin:0;font-family:system-ui}</style></head><body><div id="host"></div>
<script type="module">
import { initialState, nextState, controlFrom } from "/master_nav.js";
let state = initialState();
async function load() {
  const q = new URLSearchParams(state).toString();
  const r = await fetch("/page?" + q); const j = await r.json();
  document.getElementById("host").innerHTML = j.html;          // harness only: the shipped component uses owl markup() of the same server HTML
  window.__ready = (window.__ready || 0) + 1;
}
document.addEventListener("click", async (ev) => { const n = nextState(state, controlFrom(ev.target)); if (!n) return; state = n; await load(); const m = document.getElementById("sm-main"); if (m) m.focus({preventScroll:true}); });
await load();
</script></body></html>"""


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        if u.path == "/":
            return self._send(200, "text/html", HARNESS.encode())
        if u.path == "/master_nav.js":
            return self._send(200, "text/javascript", open(os.path.join(ADDON, "static", "src", "master", "master_nav.js"), "rb").read())
        if u.path == "/page":
            q = {k: v[0] for k, v in urllib.parse.parse_qs(u.query).items()}
            g, a, n = TV.parts()
            d = V.assemble(TV.D, g, a, n, "steward", q["section"], q["perspective"], q["depth"], q["actor"], TV.GROUPS)
            return self._send(200, "application/json", json.dumps({"html": R.render_page(d)}).encode())
        self._send(404, "text/plain", b"no")
    def _send(self, code, ctype, body):
        self.send_response(code); self.send_header("Content-Type", ctype); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)


def browser_ctx():
    try:
        from playwright.sync_api import sync_playwright
    except Exception as ex:
        raise unittest.SkipTest("playwright not importable: %s" % ex)
    pw = sync_playwright().start()
    try:
        b = pw.chromium.launch()
    except Exception as ex:
        pw.stop(); raise unittest.SkipTest("no launchable browser: %s" % str(ex)[:120])
    return pw, b


class Browser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pw, cls.browser = browser_ctx()
        cls.srv = socketserver.ThreadingTCPServer(("127.0.0.1", 0), Handler); cls.srv.daemon_threads = True
        cls.port = cls.srv.server_address[1]; threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.shots = os.environ.get("SHOT_DIR"); cls.results = []
        if cls.shots: os.makedirs(cls.shots, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown(); cls.browser.close(); cls.pw.stop()

    def open(self, w, h):
        ctx = self.browser.new_context(viewport={"width": w, "height": h}, has_touch=(w < 600)); page = ctx.new_page(); errs = []
        page.on("console", lambda m: errs.append(("console", m.text)) if m.type == "error" else None); page.on("pageerror", lambda e: errs.append(("pageerror", str(e))))
        page.goto("http://127.0.0.1:%d/" % self.port); page.wait_for_selector(".syn-master"); return ctx, page, errs

    def go(self, page, **ds):
        sel = "button.sm-b" + "".join('[data-%s="%s"]' % (k, v) for k, v in ds.items())
        active = page.evaluate("(s) => { const b = document.querySelector(s); return !!b && (b.getAttribute('aria-pressed') === 'true' || b.getAttribute('aria-current') === 'page'); }", sel)
        before = page.evaluate("window.__ready"); page.click(sel)
        if active:                                                  # pressing the already-active control is a no-op by design: no reload, state unchanged
            page.wait_for_timeout(150); self.assertEqual(page.evaluate("window.__ready"), before); return
        page.wait_for_function("n => window.__ready > n", arg=before, timeout=10000)

    def overflow(self, page, w):
        return page.evaluate("""(w) => { const bad = []; const de = document.documentElement;
            if (de.scrollWidth > w + 1) bad.push('document ' + de.scrollWidth);
            const root = document.querySelector('.syn-master'); if (root.scrollWidth > w + 1) bad.push('root ' + root.scrollWidth);
            for (const el of root.querySelectorAll('*')) { if (el.closest('.sm-scroll, .sm-nav')) continue; const r = el.getBoundingClientRect();
              if (r.width > 0 && (r.right > w + 1 || r.left < -1)) { bad.push(el.tagName + '.' + el.className + ' ' + Math.round(r.right)); if (bad.length > 5) break; } }
            return bad; }""", w)

    def test_every_section_at_every_viewport_has_no_overflow_and_no_js_error(self):
        for w, h in VIEWPORTS:
            ctx, page, errs = self.open(w, h)
            try:
                for s in V.SECTIONS:
                    self.go(page, section=s); self.assertEqual(page.get_attribute(".syn-master", "data-section"), s)
                    self.assertEqual(self.overflow(page, w), [], (w, s))
                    if self.shots and s in ("overview", "value", "kinematics", "perspectives", "effects", "mesh", "holds"):
                        p = os.path.join(self.shots, "master_%s_%d.png" % (s, w)); page.screenshot(path=p, full_page=False)
                        self.__class__.results.append((os.path.basename(p), hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]))
                self.assertEqual(errs, [], w)
            finally: ctx.close()

    def test_form_flow_evolve_content_differs_in_the_browser(self):
        for w, h in VIEWPORTS:
            ctx, page, errs = self.open(w, h)
            try:
                self.go(page, section="perspectives"); texts = {}
                for p in ("Form", "Flow", "Evolve"):
                    self.go(page, persp=p); self.assertEqual(page.get_attribute(".syn-master", "data-perspective"), p); texts[p] = page.inner_text("#sm-main")
                    self.assertEqual(self.overflow(page, w), [], (w, p))
                self.assertEqual(len(set(texts.values())), 3, w); self.assertEqual(errs, [])
            finally: ctx.close()

    def test_depth_adds_detail_not_data(self):
        for w, h in VIEWPORTS:
            ctx, page, errs = self.open(w, h)
            try:
                self.go(page, section="value"); lens = []
                for d in ("enable", "enhance", "enrich"):
                    self.go(page, depth=d); self.assertEqual(page.get_attribute(".syn-master", "data-depth"), d); lens.append(len(page.inner_text("#sm-main")))
                self.assertLess(lens[0], lens[1]); self.assertEqual(self.overflow(page, w), []); self.assertEqual(errs, [])
            finally: ctx.close()

    def test_actor_perspective_changes_label_not_data(self):
        ctx, page, errs = self.open(390, 844)
        try:
            self.go(page, section="kinematics"); base = page.inner_text("#sm-main")
            for a in ("collaborator", "client", "steward"):
                self.go(page, actor=a); self.assertEqual(page.inner_text("#sm-main"), base)
            self.go(page, section="actors"); self.go(page, actor="client"); t = page.inner_text("#sm-main"); self.assertIn("HOLD H02", t); self.assertIn("DEFINITION_ONLY_NOT_TESTED", t)
            self.assertEqual(errs, [])
        finally: ctx.close()

    def test_keyboard_navigation_and_focus(self):
        ctx, page, errs = self.open(1024, 768)
        try:
            page.keyboard.press("Tab"); tag = page.evaluate("document.activeElement.tagName"); self.assertEqual(tag, "BUTTON")
            self.assertTrue(page.evaluate("document.activeElement.closest('.syn-master') !== null"))
            before = page.evaluate("window.__ready"); page.focus('button.sm-b[data-section="kinematics"]'); page.keyboard.press("Enter")
            page.wait_for_function("n => window.__ready > n", arg=before); self.assertEqual(page.get_attribute(".syn-master", "data-section"), "kinematics")
            self.assertEqual(page.evaluate("document.activeElement.id"), "sm-main")                  # focus moves to the content after navigation
            ol = page.evaluate("(() => { const b = document.querySelector('button.sm-b'); b.focus(); const s = getComputedStyle(b); return s.outlineStyle + ' ' + s.outlineWidth; })()")
            self.assertNotIn("none", ol.split()[0]); self.assertEqual(errs, [])
        finally: ctx.close()

    def test_touch_targets_and_tables_scroll_inside_their_region(self):
        for w, h in VIEWPORTS:
            ctx, page, errs = self.open(w, h)
            try:
                self.go(page, section="perspectives")
                small = page.evaluate("[...document.querySelectorAll('button.sm-b')].map(b => b.getBoundingClientRect().height).filter(x => x < %d).length" % (44 if w < 600 else 34))
                self.assertEqual(small, 0, w)
                regions = page.evaluate("[...document.querySelectorAll('.sm-scroll')].every(r => getComputedStyle(r).overflowX === 'auto')"); self.assertTrue(regions)
                self.assertEqual(self.overflow(page, w), [])
            finally: ctx.close()

    def test_control_bar_does_not_cover_a_phone_screen_but_stays_reachable_on_larger_ones(self):
        for w, h, want in ((390, 844, "static"), (768, 1024, "sticky"), (1440, 900, "sticky")):
            ctx, page, errs = self.open(w, h)
            try:
                self.go(page, section="kinematics"); pos = page.evaluate("getComputedStyle(document.querySelector('.sm-bar')).position"); self.assertEqual(pos, want, w)
                if want == "static":
                    self.assertGreater(page.evaluate("document.querySelector('#sm-main').getBoundingClientRect().top"), 0)
                    page.evaluate("document.querySelector('#sm-main').scrollIntoView()"); self.assertLess(page.evaluate("document.querySelector('.sm-bar').getBoundingClientRect().bottom"), 1)
            finally: ctx.close()

    def test_nav_bar_scrolls_sideways_on_a_phone_without_breaking_the_page(self):
        ctx, page, errs = self.open(390, 844)
        try:
            nav = page.evaluate("(() => { const n = document.querySelector('.sm-nav'); return [n.scrollWidth > n.clientWidth, getComputedStyle(n).overflowX]; })()")
            self.assertEqual(nav, [True, "auto"]); self.assertEqual(self.overflow(page, 390), [])
        finally: ctx.close()

    def test_no_script_or_inline_handler_survives_in_the_rendered_dom(self):
        ctx, page, errs = self.open(1024, 768)
        try:
            for s in V.SECTIONS:
                self.go(page, section=s); n = page.evaluate("document.querySelector('#host').querySelectorAll('script,iframe,[onclick],[onerror],[onload]').length"); self.assertEqual(n, 0, s)
        finally: ctx.close()


if __name__ == "__main__":
    unittest.main()
