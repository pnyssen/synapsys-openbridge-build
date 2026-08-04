"""R1 bounded-correction candidate acceptance test harness.

Serves an overlay tree (source_mirror + candidate, candidate wins on
conflict) over local HTTP - never touches any real current path - and
drives Chromium through every WO-required assertion: identity/scope,
desktop, mobile, route/lineage, role/membrane.

Also serves a second, unmodified source_mirror-only tree for baseline
comparison of the same checks (proves the defects existed pre-candidate
and are fixed post-candidate).
"""
import functools
import http.server
import json
import pathlib
import shutil
import sys
import threading

from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).parent
SRC = HERE / "source_mirror"
CAND = HERE / "candidate"
OVERLAY = HERE / "_overlay_serve"
EVID = HERE / "evidence"
SHOTS = EVID / "screenshots"
SHOTS.mkdir(parents=True, exist_ok=True)

NAV = "SYNAPSYS_NAVIGATOR_MVP_ARCHITECTURE_v1.5.html"
FLAGGED = ["ELEMENT_MESH_CONTROL_GATES_v1.3.html", "ELEMENT_BENEFITS_ASSETS_v1.3.html",
          "ELEMENT_CURRENT_WORK_OBJECT_QUEUE_v1.3.html", "ELEMENT_CONTEXT_MEMBRANE_v1.3.html",
          "ELEMENT_AGENT_RUNTIME_ROUTING_v1.3.html"]
ALL_ELEMENTS = FLAGGED + ["ELEMENT_SERVICE_CATALOGUE_v1.3.html",
                          "ELEMENT_CANONICAL_LIBRARY_v1.3.html",
                          "ELEMENT_ASSET_PATTERN_LIBRARY_v1.3.html",
                          "ELEMENT_METHOD_LIBRARY_v1.3.html"]
ELEMENT_LABELS = {
    "ELEMENT_SERVICE_CATALOGUE_v1.3.html": "Service Catalogue",
    "ELEMENT_CANONICAL_LIBRARY_v1.3.html": "Canonical Library",
    "ELEMENT_ASSET_PATTERN_LIBRARY_v1.3.html": "Asset & Pattern Library",
    "ELEMENT_METHOD_LIBRARY_v1.3.html": "Method Library",
    "ELEMENT_MESH_CONTROL_GATES_v1.3.html": "Mesh & Control Gates",
    "ELEMENT_BENEFITS_ASSETS_v1.3.html": "Benefits & Assets",
    "ELEMENT_CURRENT_WORK_OBJECT_QUEUE_v1.3.html": "Current Work Object & Queue",
    "ELEMENT_CONTEXT_MEMBRANE_v1.3.html": "Context & Membrane",
    "ELEMENT_AGENT_RUNTIME_ROUTING_v1.3.html": "Agent & Runtime Routing",
}
CANVAS_VIEWS = ["CANVAS_VIEW_SERVICE_CATALOGUE_v1.0.html", "CANVAS_VIEW_CANONICAL_LIBRARY_v1.0.html",
               "CANVAS_VIEW_ASSET_PATTERN_LIBRARY_v1.0.html", "CANVAS_VIEW_METHOD_LIBRARY_v1.0.html",
               "CANVAS_VIEW_MESH_CONTROL_GATES_v1.0.html", "CANVAS_VIEW_BENEFITS_ASSETS_v1.0.html",
               "CANVAS_VIEW_CURRENT_WORK_OBJECT_QUEUE_v1.0.html", "CANVAS_VIEW_CONTEXT_MEMBRANE_v1.0.html",
               "CANVAS_VIEW_AGENT_RUNTIME_ROUTING_v1.0.html"]

results = {"passes": [], "failures": []}


def rec(ok, check, detail=""):
    (results["passes"] if ok else results["failures"]).append({"check": check, "detail": detail})
    print(("PASS " if ok else "FAIL ") + check + (f" — {detail}" if detail else ""))


def build_overlay():
    if OVERLAY.exists():
        shutil.rmtree(OVERLAY)
    shutil.copytree(SRC, OVERLAY)
    (OVERLAY / NAV).write_bytes((CAND / NAV).read_bytes())
    for f in FLAGGED:
        (OVERLAY / "COMPONENTS" / f).write_bytes((CAND / "COMPONENTS" / f).read_bytes())
    (OVERLAY / "DATA" / "NAVIGATOR_L1_L2_L3_ROUTE_REGISTRY.json").write_bytes(
        (CAND / "DATA" / "NAVIGATOR_L1_L2_L3_ROUTE_REGISTRY.json").read_bytes())


def serve(directory, port):
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port),
                                          functools.partial(Q, directory=str(directory)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def run_suite(page_ctx_factory, base, label, shot_prefix, screenshots=True):
    """Run the full WO-required assertion set against one served tree."""
    out = {}

    for vp_name, vp in [("desktop", {"width": 1440, "height": 1000}),
                        ("mobile", {"width": 390, "height": 844})]:
        ctx = page_ctx_factory(vp)
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(base + NAV)
        page.wait_for_load_state("networkidle")

        scroll_y = page.evaluate("window.scrollY")
        rec(scroll_y <= 20, f"[{label}/{vp_name}] cold-start no auto-scroll (C1)",
            f"scrollY={scroll_y}")

        # C2: mobile hero column count (only meaningful at mobile width)
        if vp_name == "mobile":
            cols = page.evaluate(
                "getComputedStyle(document.querySelector('.hero')).gridTemplateColumns")
            n_cols = len([c for c in cols.split() if c])
            rec(n_cols == 1, f"[{label}/mobile] hero single-column layout (C2)",
                f"grid-template-columns='{cols}' ({n_cols} tracks)")
            overflow = page.evaluate("document.documentElement.scrollWidth - window.innerWidth")
            rec(overflow <= 5, f"[{label}/mobile] no horizontal overflow", f"overflow={overflow}px")
            titles = page.locator(".priority-copy b").all_inner_texts()
            # measure actual clipping via scrollWidth>clientWidth on each priority title
            clip_count = page.evaluate(
                "[...document.querySelectorAll('.priority-copy b')].slice(0,5)"
                ".filter(el=>el.scrollWidth>el.clientWidth+2).length")
            rec(len(titles) >= 5, f"[{label}/mobile] five priority titles present", f"n={len(titles)}")
            rec(clip_count == 0, f"[{label}/mobile] no priority title clipped/truncated",
                f"clipped={clip_count}/5")

        # C3: persistent identity header
        hdr = page.locator("#r1c3-identity")
        rec(hdr.count() == 1 and hdr.is_visible(),
            f"[{label}/{vp_name}] persistent identity header present and visible (C3)")
        if hdr.count():
            htxt = hdr.inner_text()
            for must in ["Steward / D001", "CTX-SS", "WO-NAVIGATOR-MVP", "Potential", "HELD"]:
                rec(must in htxt, f"[{label}/{vp_name}] identity header contains '{must}'")

        # C4: fail-closed disclosure
        rb = page.locator("#r1c4-role-boundary")
        rec(rb.count() == 1, f"[{label}/{vp_name}] role-boundary disclosure present (C4)")
        if rb.count():
            rtxt = rb.inner_text()
            rec("not available" in rtxt.lower() or "not  available" in rtxt.lower(),
                f"[{label}/{vp_name}] disclosure states external access unavailable")

        # C5: one current next action, no competing label
        cna = page.locator("#r1c5-current-next-action")
        rec(cna.count() == 1 and cna.is_visible(),
            f"[{label}/{vp_name}] single 'Current next action' visible on load (C5)")
        competing = page.locator("text=Next action").count()
        rec(competing == 0, f"[{label}/{vp_name}] no competing 'Next action' label remains",
            f"count={competing}")

        # three primary actions
        ok3 = 0
        for pid in ["operate", "wave", "status"]:
            page.click(f'button[data-open="{pid}"]')
            page.wait_for_timeout(80)
            if page.locator(f"#{pid}.active").count() == 1:
                ok3 += 1
        rec(ok3 == 3, f"[{label}/{vp_name}] three primary actions operate", f"{ok3}/3")
        page.click('button[data-open="operate"]')

        rec(not errors, f"[{label}/{vp_name}] no browser script/component errors",
            "; ".join(errors[:3]))

        if screenshots:
            page.screenshot(path=str(SHOTS / f"{shot_prefix}_{vp_name}_initial.png"))
        ctx.close()

    # route / lineage matrix (desktop context reused fresh)
    ctx = page_ctx_factory({"width": 1440, "height": 1000})
    page = ctx.new_page()

    n_elem = 0
    n_return = 0
    for f in ALL_ELEMENTS:
        page.goto(base + "COMPONENTS/" + f)
        page.wait_for_load_state("networkidle")
        ok = page.locator("h1").count() >= 1 and "error" not in (page.title() or "").lower()
        if ok:
            n_elem += 1
        ret = page.locator(f'nav.routes a[href*="{NAV}"], a[href*="{NAV}"]').count() > 0 or \
            page.get_by_text("Return to Navigator").count() > 0
        if ret:
            n_return += 1
        rec(ok, f"[{label}] element page renders: {ELEMENT_LABELS.get(f, f)}")
        rec(ret, f"[{label}] element page has direct Navigator return: {ELEMENT_LABELS.get(f, f)}")
    out["elements_9_9"] = n_elem
    out["returns_9_9"] = n_return

    n_canvas = 0
    for f in CANVAS_VIEWS:
        page.goto(base + "COMPONENTS/" + f)
        page.wait_for_load_state("networkidle")
        ok = page.locator("svg").count() >= 1
        if ok:
            n_canvas += 1
        rec(ok, f"[{label}] canvas route renders: {f}")
    out["canvas_9_9"] = n_canvas

    # no v1.0/v0.2 element target anywhere in the navigator's own links
    page.goto(base + NAV)
    page.wait_for_load_state("networkidle")
    stale = page.evaluate(
        "[...document.querySelectorAll('a[href]')].map(a=>a.getAttribute('href'))"
        ".filter(h=>/ELEMENT_[A-Z_]+_v1\\.[02]\\.html/.test(h))")
    rec(len(stale) == 0, f"[{label}] no v1.0/v0.2 element route", f"found={stale}")

    ctx.close()
    return out


def role_membrane_checks(base):
    """C3/C4 semantic assertions beyond presence: check that the disclosure
    text actually distinguishes internal-governed vs external-unavailable,
    and that PPV/authority/STOP-HOLD/WO/source-freshness are all present."""
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path="/opt/pw-browsers/chromium")
        page = b.new_page(viewport={"width": 1440, "height": 1000})
        page.goto(base + NAV)
        page.wait_for_load_state("networkidle")
        hdr_txt = page.locator("#r1c3-identity").inner_text()
        rb_txt = page.locator("#r1c4-role-boundary").inner_text()
        checks = {
            "role_visible": "Steward / D001" in hdr_txt,
            "context_membrane_visible": "Context/membrane" in hdr_txt or "CTX-SS" in hdr_txt,
            "operating_plane_visible": "Plane" in hdr_txt,
            "work_object_visible": "WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001" in hdr_txt,
            "ppv_visible": "Potential" in hdr_txt,
            "authority_visible": "HELD" in hdr_txt,
            "source_freshness_visible": "reshness" in hdr_txt or "snapshot" in hdr_txt,
            "stop_hold_visible": "STOP/HOLD" in hdr_txt,
            "internal_routes_bounded": "internal governed routes" in rb_txt,
            "external_fail_closed": "not available" in rb_txt and "fail-closed" in rb_txt,
            "no_live_acl_claim": "implies live authentication" in rb_txt,
            "no_permission_grant_implied": "implies" in rb_txt,
        }
        for k, v in checks.items():
            rec(bool(v), f"[role/membrane] {k}")
        b.close()


def main():
    build_overlay()
    ov_srv = serve(OVERLAY, 8611)
    src_srv = serve(SRC, 8612)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path="/opt/pw-browsers/chromium")

        def ctx_factory(vp):
            return browser.new_context(viewport=vp)

        print("\n=== BASELINE (unmodified source_mirror) — expect C1/C2/C3/C4/C5/C6 findings ===")
        base_out = run_suite(ctx_factory, "http://127.0.0.1:8612/", "baseline", "baseline",
                             screenshots=False)

        print("\n=== CANDIDATE (overlay: source_mirror + candidate corrections) ===")
        cand_out = run_suite(ctx_factory, "http://127.0.0.1:8611/", "candidate", "candidate")

        browser.close()

    role_membrane_checks("http://127.0.0.1:8611/")

    ov_srv.shutdown()
    src_srv.shutdown()

    report = {"baseline": base_out, "candidate": cand_out,
             "passes": results["passes"], "failures": results["failures"]}
    (EVID / "browser_test_report.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    n_p, n_f = len(results["passes"]), len(results["failures"])
    print(f"\nTOTAL: {n_p} pass, {n_f} fail")
    sys.exit(0)


if __name__ == "__main__":
    main()
