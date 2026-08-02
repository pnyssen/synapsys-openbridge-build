"""Visual interaction test for the Navigator deployment.

Serves dist/ over local HTTP and drives Chromium through the cold-start
route: Navigator -> 9 canvas views (visible SVG) -> 9 element pages ->
nine verbs (all anchors) -> element links from verbs -> process/offering
start -> return routes. Desktop and narrow viewports; plus a JS-disabled
pass and a file:// pass on key pages. Captures screenshots and a
structured DOM-evidence JSON.
"""
import json
import pathlib
import sys
import threading
import functools
import http.server

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import model
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).parent
DIST = HERE / "dist"
SHOTS = HERE / "evidence" / "screenshots"
SHOTS.mkdir(parents=True, exist_ok=True)
PORT = 8471
BASE = f"http://127.0.0.1:{PORT}/00_SYSTEM/NAVIGATOR_SUPPORT/CURRENT/"

evidence = {"passes": [], "failures": []}


def note(ok, what, detail=""):
    (evidence["passes"] if ok else evidence["failures"]).append(
        {"check": what, "detail": detail})
    print(("PASS " if ok else "FAIL ") + what + (f" — {detail}" if detail else ""))



def click_and_wait(page, selector, url_suffix, note_fn=None):
    """Click a link and wait for navigation, retrying once if the click
    was swallowed (observed flake under heavy page load)."""
    import time
    for attempt in range(2):
        page.locator(selector).first.click()
        for _ in range(60):
            if page.url.split("#")[0].endswith(url_suffix):
                page.wait_for_load_state("domcontentloaded")
                return True
            time.sleep(0.25)
    return False

def main():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler,
                                directory=str(DIST))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path="/opt/pw-browsers/chromium"
                                     if pathlib.Path("/opt/pw-browsers/chromium").is_file()
                                     else None)

        for vp_name, vp in [("desktop", {"width": 1440, "height": 900}),
                            ("narrow", {"width": 390, "height": 780})]:
            ctx = browser.new_context(viewport=vp)
            page = ctx.new_page()
            console_errors = []
            page.on("pageerror", lambda e: console_errors.append(str(e)))

            # Navigator
            page.goto(BASE + model.NAVIGATOR_FILE)
            note("SynapSys Navigator" in page.title() or
                 page.locator("h1").first.inner_text().strip() != "",
                 f"[{vp_name}] navigator renders")
            note(page.locator("#l1l2l3-routes").count() == 1,
                 f"[{vp_name}] L1L2L3 static route section present")
            note("ASSURED_STREAM_A_COMPLETE" in page.content(),
                 f"[{vp_name}] Stream A completion visible")
            note(page.locator("#priorityList .priority-link").count() == 5,
                 f"[{vp_name}] top five priorities visible")
            page.screenshot(path=str(SHOTS / f"navigator_{vp_name}.png"),
                            full_page=False)

            body_w = page.evaluate("document.body.scrollWidth")
            note(body_w <= vp["width"] + 20,
                 f"[{vp_name}] no gross horizontal overflow", f"scrollWidth={body_w}")

            # 9 canvas views + element pages
            for e in model.ELEMENTS:
                page.goto(BASE + "COMPONENTS/" + e["canvas_view"])
                svg = page.locator("svg")
                note(svg.count() >= 1 and page.locator("svg text").count() >= 3,
                     f"[{vp_name}] {e['id']} canvas view shows graphical SVG",
                     f"texts={page.locator('svg text').count()}")
                if vp_name == "desktop":
                    page.screenshot(path=str(SHOTS / f"canvas_{e['key']}.png"))
                # element page via its 'Open Element Page' primary link
                ok = click_and_wait(page, "nav.routes a.primary", e["html"])
                note(ok and e["name"].split(" ")[0] in page.content(),
                     f"[{vp_name}] {e['id']} element page opens from canvas view")
                note(page.locator("details").count() == 27,
                     f"[{vp_name}] {e['id']} shows 27 L3 cells")
                # return route to navigator
                ok = click_and_wait(page, f'a[href="../{model.NAVIGATOR_FILE}"]',
                                    model.NAVIGATOR_FILE)
                note(ok,
                     f"[{vp_name}] {e['id']} one-click return to Navigator")

            # nine verbs
            page.goto(BASE + "COMPONENTS/" + model.VERBS_FILE)
            for v in model.VERBS:
                page.click(f'a[href="#{v["key"]}"]')
                vis = page.locator(f"#{v['key']}").is_visible()
                note(vis, f"[{vp_name}] verb {v['name']} anchor navigates")
            if vp_name == "desktop":
                page.screenshot(path=str(SHOTS / "nine_verbs.png"), full_page=False)
            # every primary element link from verbs page resolves
            for e in model.ELEMENTS:
                n = page.locator(f'a[href="{e["html"]}"]').count()
                note(n >= 1, f"[{vp_name}] verbs page links element {e['id']}")

            # process/offering start
            page.goto(BASE + "COMPONENTS/" + model.START_FILE)
            note("governed candidate" in page.content().lower(),
                 f"[{vp_name}] start surface explains governed candidate")
            note("HOLD" in page.content(),
                 f"[{vp_name}] activation HOLD visible on start surface")
            note(page.locator("#fixtures").count() == 1,
                 f"[{vp_name}] fixtures section present")
            if vp_name == "desktop":
                page.screenshot(path=str(SHOTS / "start_surface.png"), full_page=False)
            ok = click_and_wait(page, f'a[href="../{model.NAVIGATOR_FILE}"]',
                                model.NAVIGATOR_FILE)
            note(ok,
                 f"[{vp_name}] start surface returns to Navigator")

            note(not console_errors, f"[{vp_name}] no page JS errors",
                 "; ".join(console_errors[:3]))
            ctx.close()

        # JS-disabled pass: primary path must stay usable
        ctx = browser.new_context(java_script_enabled=False,
                                  viewport={"width": 1280, "height": 800})
        page = ctx.new_page()
        page.goto(BASE + model.NAVIGATOR_FILE)
        note(page.locator("#l1l2l3-routes a").count() >= 30,
             "[nojs] static route table reachable without JavaScript")
        page.click(f'#l1l2l3-routes a[href="COMPONENTS/{model.ELEMENTS[0]["canvas_view"]}"]')
        note(page.locator("svg").count() >= 1, "[nojs] canvas view SVG renders")
        page.goto(BASE + "COMPONENTS/" + model.VERBS_FILE)
        note(page.locator("#orient").count() == 1, "[nojs] verbs page usable")
        ctx.close()

        # file:// pass on key pages
        ctx = browser.new_context()
        page = ctx.new_page()
        cur = DIST / "00_SYSTEM" / "NAVIGATOR_SUPPORT" / "CURRENT"
        page.goto((cur / "COMPONENTS" / model.ELEMENTS[0]["canvas_view"]).as_uri())
        note(page.locator("svg").count() >= 1, "[file://] canvas view renders")
        page.goto((cur / model.NAVIGATOR_FILE).as_uri())
        note(page.locator("#l1l2l3-routes").count() == 1, "[file://] navigator renders")
        # direct element entry without opening navigator first (stale-anchor sim)
        page.goto((cur / "COMPONENTS" / model.ELEMENTS[4]["html"]).as_uri() + "#nonexistent-anchor")
        note(page.locator("details").count() == 27,
             "[file://] direct element entry with stale anchor still renders")
        ctx.close()
        browser.close()

    srv.shutdown()
    (HERE / "evidence" / "BROWSER_TEST_EVIDENCE.json").write_text(
        json.dumps(evidence, indent=1), encoding="utf-8")
    print(f"\nTOTAL: {len(evidence['passes'])} pass, {len(evidence['failures'])} fail")
    sys.exit(1 if evidence["failures"] else 0)


if __name__ == "__main__":
    main()
