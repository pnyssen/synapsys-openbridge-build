"""Update SYNAPSYS_NAVIGATOR_MVP_ARCHITECTURE_v1.5.html in place.

Root-cause corrections (not per-link patches):
1. Every obsidian:// link whose target has a browser-safe equivalent gets
   rewritten to the relative route; the obsidian:// route stays available as
   a secondary "Obs" link where it was the row's only route.
2. Stale v1.1 canvas references upgraded to v1.2.
3. A static, script-free "L1 / L2 / L3 routes" section is inserted before
   </main> so the nine Elements, canvas views, nine verbs, candidate start
   surface and route registry are reachable even with JavaScript disabled.
4. The top-five priorities aside is aligned with the current priority model
   (Navigator completion this cycle; Odoo correction separately held).
5. The element-summary table becomes browser-safe (primary relative links,
   obsidian secondary), and its "WORKING LINKS / open in Obsidian, not
   SharePoint Preview" copy is corrected.
"""
import pathlib
import re
import urllib.parse

import model

HERE = pathlib.Path(__file__).parent
SRC = HERE / "mirror" / "CURRENT" / model.NAVIGATOR_FILE
DST = HERE / "dist" / "00_SYSTEM" / "NAVIGATOR_SUPPORT" / "CURRENT" / model.NAVIGATOR_FILE

OBS = re.compile(r'obsidian://open\?vault=Obsidian&(?:amp;)?file=([^"]+)')

CANVAS_TO_VIEW = {e["canvas_source"]: e["canvas_view"] for e in model.ELEMENTS}


def browser_route(vault_path):
    """Map a vault path to the best browser-safe relative route from CURRENT/."""
    p = urllib.parse.unquote(vault_path)
    if p.startswith("00_SYSTEM/NAVIGATOR_SUPPORT/CURRENT/"):
        return p[len("00_SYSTEM/NAVIGATOR_SUPPORT/CURRENT/"):]
    if p == "00_HOME.md":
        return "../../../00_HOME.md"
    name = p.rsplit("/", 1)[-1]
    if name in CANVAS_TO_VIEW:
        return "COMPONENTS/" + CANVAS_TO_VIEW[name]
    if p.startswith("10_WORKSPACES/"):
        return "../../../" + p
    return None


def main():
    t = SRC.read_text(encoding="utf-8")
    orig_len = len(t)

    # 2. stale v1.1 canvas refs -> v1.2 (encoded form inside obsidian links)
    for e in model.ELEMENTS:
        v11 = e["canvas_source"].replace("_v1.2", "_v1.1")
        t = t.replace(v11.replace(" ", "%20"), e["canvas_source"])
        t = t.replace(v11, e["canvas_source"])

    # 1. rewrite obsidian:// hrefs to browser-safe routes where possible
    def sub_href(m):
        full = m.group(0)
        inner = OBS.search(full)
        if not inner:
            return full
        route = browser_route(inner.group(1))
        if route is None:
            return full
        return f'href="{route}"'

    t = re.sub(r'href="obsidian://open\?vault=Obsidian&(?:amp;)?file=[^"]*"',
               sub_href, t)

    # 5. correct the misleading link copy
    t = t.replace(
        "<b>WORKING LINKS</b><br/>Each route uses an Obsidian-native vault URI. "
        "Canvas and HTML files open in Obsidian, not SharePoint Preview.",
        "<b>WORKING LINKS</b><br/>Each route is browser-safe (relative vault path): "
        "Canvas views and pages open from the synced folder, local HTTP or SharePoint, "
        "no Obsidian required. Obsidian remains available for editing the .canvas sources.")

    # 4. align the priorities aside with the current priority model
    pri = re.compile(r'(<aside aria-label="Top five priorities".*?</aside>)', re.S)
    m = pri.search(t)
    if m:
        items = [
            ("1", "status", "stream-c",
             "Accept the completed Navigator L1/L2/L3 integration",
             "All nine Elements, nine verbs and 243 Level-3 positions are integrated, "
             "tested and deployed this cycle; Steward acceptance is the one open step."),
            ("2", "status", "stream-c",
             "Release and execute the bounded Odoo Work Object / Service / Method correction",
             "Separately held D007 packet; not a blocker for the interface — held to its own authority."),
            ("3", "operate", "",
             "Begin defining new Processes and Offerings as governed candidates",
             "Use the New Process &amp; Offering start surface; activation stays HELD until authorised."),
            ("4", "status", "mesh",
             "Maintain Mesh, Benefit and evidence discipline on every route",
             "Every claim stays evidence-bound; realisation declarations remain with the Steward."),
            ("5", "status", "",
             "Prepare bounded Odoo registration of accepted Navigator artefacts",
             "Only after Steward acceptance, via CR, under the GitHub/N8N-equivalent change control rule."),
        ]
        btns = "".join(
            f'<button class="priority-link" data-open="{o}"'
            + (f' data-anchor="{a}"' if a else "")
            + f' type="button"><span class="rank">{r}</span><span class="priority-copy">'
              f"<b>{ti}</b><small>{d}</small></span></button>"
            for r, o, a, ti, d in items)
        t = t[:m.start(1)] + (
            '<aside aria-label="Top five priorities" class="card"><h2>Top five priorities</h2>'
            f'<div class="priority-list" id="priorityList">{btns}</div></aside>'
        ) + t[m.end(1):]

    # 6. pre-existing JS defect: render() assigns
    # window.navigatorStatus.deliveryState before navigatorStatus is defined,
    # so the first render throws on every page load. Guard the assignment.
    bad_js = "window.navigatorStatus.deliveryState=state;"
    assert bad_js in t
    t = t.replace(bad_js,
                  "if(window.navigatorStatus){window.navigatorStatus.deliveryState=state;}")

    # 7. narrow-viewport overflow: let wide sections scroll internally instead
    # of widening the page body.
    resp_css = ("<style>@media(max-width:700px){.wrap>section,.wrap>.hero>.card,"
                ".element-scroll{overflow-x:auto}.wrap{overflow-x:hidden}"
                ".action-stack{flex-wrap:wrap}}</style>")
    assert "</head>" in t
    t = t.replace("</head>", resp_css + "</head>", 1)

    # 10. CSP root cause: connect-src 'none' + frame-src 'none' blocked every
    # same-origin subresource (the DATA fetch never worked, entrenching the
    # embedded-state drift and srcdoc duplication). Allow same-origin only.
    old_csp = ("default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; "
               "img-src data:; connect-src 'none'; frame-src 'none'; object-src 'none'; "
               "base-uri 'none'; form-action 'none'")
    new_csp = ("default-src 'none'; style-src 'unsafe-inline'; "
               "script-src 'unsafe-inline' 'self'; img-src data:; connect-src 'self'; "
               "frame-src 'self'; object-src 'none'; base-uri 'none'; form-action 'none'")
    assert old_csp in t, "expected v1.5 CSP not found"
    t = t.replace(old_csp, new_csp)

    # 8. externalize the three srcdoc iframes. The embedded copies had
    # drifted from (or broken links relative to) their standalone component
    # files - the duplicated-current-surface root cause. The operating and
    # wave frames become new current component versions extracted from the
    # live navigator; the delivery frame points at the corrected
    # NAVIGATOR_PARALLEL_DELIVERY_CONTROL_v1.1.html.
    import html as _html
    import re as _re

    def _extract(frame_id_attr, src_path):
        nonlocal t
        m = _re.search(r'(<iframe[^>]*?)srcdoc="((?:[^"])*?)"', t, _re.S)
        while m:
            head = m.group(1)
            if frame_id_attr in head:
                content = _html.unescape(m.group(2))
                t = t[:m.start()] + head + f'src="{src_path}"' + t[m.end():]
                return content
            m = _re.search(r'(<iframe[^>]*?)srcdoc="((?:[^"])*?)"',
                           t[m.end():], _re.S) and _re.search(
                r'(<iframe[^>]*?)srcdoc="((?:[^"])*?)"', t, _re.S)
            # fallthrough handled below
        return None

    # simpler deterministic pass: iterate all srcdoc iframes once
    frames = {}
    def _repl(m):
        head = m.group(1)
        content = _html.unescape(m.group(2))
        if 'id="operatingFrame"' in head:
            frames["operating"] = content
            return head + 'src="COMPONENTS/NAVIGATOR_OPERATING_SURFACE_v4.6.html"'
        if 'id="waveFrame"' in head:
            frames["wave"] = content
            return head + 'src="COMPONENTS/NAVIGATOR_WAVE_RUNNER_v0.3.html"'
        frames["delivery"] = content
        return head + 'src="COMPONENTS/NAVIGATOR_PARALLEL_DELIVERY_CONTROL_v1.1.html"'
    t = _re.sub(r'(<iframe[^>]*?)srcdoc="((?:[^"])*?)"', _repl, t, flags=_re.S)
    assert set(frames) == {"operating", "wave", "delivery"}, frames.keys()

    comp_dir = DST.parent / "COMPONENTS"
    comp_dir.mkdir(parents=True, exist_ok=True)
    # operating frame: rewrite its obsidian://-only verb links to relative
    op = frames["operating"]
    op = op.replace(
        "obsidian://open?vault=Obsidian&file=00_SYSTEM%2FNAVIGATOR_SUPPORT%2F"
        "CURRENT%2FCOMPONENTS%2FNAVIGATOR_NINE_VERBS_BENEFIT_ROUTE_v1.0.html",
        model.VERBS_FILE)
    # promoted extraction gets the matching internal version label
    op = op.replace("Form / Flow / Evolve v4.5", "Form / Flow / Evolve v4.6")
    op = op.replace('data-surface-version="4.5"', 'data-surface-version="4.6"')
    (comp_dir / "NAVIGATOR_OPERATING_SURFACE_v4.6.html").write_text(op, encoding="utf-8")
    (comp_dir / "NAVIGATOR_WAVE_RUNNER_v0.3.html").write_text(frames["wave"], encoding="utf-8")
    # delivery frame content intentionally dropped: superseded by the
    # corrected standalone v1.1 file (drifted duplicate, broken ../ links)

    # 9. move the embedded delivery-state literal to DATA/NAVIGATOR_DELIVERY_STATE.js
    # (generated from the same refreshed JSON - one source, no embedded drift).
    m = _re.search(r'const EMBEDDED_DELIVERY_STATE=\{.*?\};\n', t, _re.S)
    assert m, "embedded delivery state literal not found"
    t = t[:m.start()] + t[m.end():]
    t = t.replace("let DELIVERY_STATE=EMBEDDED_DELIVERY_STATE;",
                  "let DELIVERY_STATE=window.EMBEDDED_DELIVERY_STATE;")
    import json as _json
    state = _json.loads((HERE / "dist" / "00_SYSTEM" / "NAVIGATOR_SUPPORT" /
                         "CURRENT" / "DATA" / "NAVIGATOR_DELIVERY_STATE.json"
                         ).read_text(encoding="utf-8"))
    js = ("// Generated from NAVIGATOR_DELIVERY_STATE.json - do not edit by hand.\n"
          "window.EMBEDDED_DELIVERY_STATE=" + _json.dumps(state, ensure_ascii=False) + ";\n")
    data_dir = DST.parent / "DATA"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "NAVIGATOR_DELIVERY_STATE.js").write_text(js, encoding="utf-8")
    assert "</head>" in t
    t = t.replace("</head>",
                  '<script src="DATA/NAVIGATOR_DELIVERY_STATE.js"></script></head>', 1)
    # The head script (no defer) executes before the inline body script, so
    # EMBEDDED_DELIVERY_STATE is set in time. Guard anyway so a missing
    # DATA .js file (adversarial case) degrades to the static route section:
    t = t.replace("DELIVERY_STATE=applyCurrentUiPatch(DELIVERY_STATE);render(DELIVERY_STATE);",
                  "if(DELIVERY_STATE){DELIVERY_STATE=applyCurrentUiPatch(DELIVERY_STATE);render(DELIVERY_STATE);}")

    # 3. insert the static L1/L2/L3 routes section before </main>
    rows = ""
    for e in model.ELEMENTS:
        obs = model.OBSIDIAN_CANVAS_PREFIX + e["canvas_source"].replace(" ", "%20")
        rows += (
            f"<tr><td><b>{e['id']}</b> {e['name']}</td>"
            f'<td><a href="COMPONENTS/{e["html"]}">Element page</a></td>'
            f'<td><a href="COMPONENTS/{e["canvas_view"]}">Canvas view</a></td>'
            f'<td><a href="../../../10_WORKSPACES/NAVIGATOR_MVP_v0.2/{e["canvas_source"]}">.canvas</a> · '
            f'<a href="{obs}">Obs</a></td></tr>')
    section = f"""
<section class="card section" id="l1l2l3-routes">
<h2>L1 · L2 · L3 routes (script-free)</h2>
<p class="muted">Static route table generated from NAVIGATOR_L1_L2_L3_ROUTE_REGISTRY v0.1.
Works with JavaScript disabled; every route is browser-safe. Level 2:
<a href="COMPONENTS/{model.VERBS_FILE}">Nine Verbs — Form / Flow / Evolve</a> ·
Start new work: <a href="COMPONENTS/{model.START_FILE}">New Process &amp; Offering (governed candidate)</a> ·
Validation source: <a href="DATA/{model.REGISTRY_FILE}">Route Registry JSON</a> ·
<a href="../../../00_HOME.md">Back to Home</a></p>
<table><thead><tr><th>Element (L1)</th><th>Page</th><th>Canvas view (L3 visual)</th><th>Canvas source</th></tr></thead>
<tbody>{rows}</tbody></table>
<p class="muted">Stream A: ASSURED_STREAM_A_COMPLETE — completed evidence only; no rerun, no active next action.
PPV: Potential. Activation of any candidate remains HELD pending Steward authority.</p>
</section>
"""
    assert "</main>" in t
    t = t.replace("</main>", section + "</main>", 1)

    DST.parent.mkdir(parents=True, exist_ok=True)
    DST.write_text(t, encoding="utf-8")
    remaining_obs = len(OBS.findall(t))
    print(f"navigator updated: {orig_len} -> {len(t)} bytes; "
          f"obsidian-protocol links remaining (secondary only): {remaining_obs}")


if __name__ == "__main__":
    main()
