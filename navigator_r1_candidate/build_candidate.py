"""Build the isolated R1 bounded-correction candidate from source_mirror/.

Applies exactly the seven corrections C1-C7 from
HUB_NAVIGATOR_R1_CURRENT_V1_5_BOUNDED_CORRECTION_WORK_OBJECT_v1.0.md.
Writes only to candidate/ - never touches source_mirror/ (the live-current
snapshot) or any real current path.
"""
import json
import pathlib
import re

HERE = pathlib.Path(__file__).parent
SRC = HERE / "source_mirror"
CAND = HERE / "candidate"
CAND.mkdir(exist_ok=True)
(CAND / "COMPONENTS").mkdir(exist_ok=True)
(CAND / "DATA").mkdir(exist_ok=True)

NAV = "SYNAPSYS_NAVIGATOR_MVP_ARCHITECTURE_v1.5.html"
FLAGGED_ELEMENTS = [
    ("ELEMENT_MESH_CONTROL_GATES_v1.3.html", "Mesh & Control Gates"),
    ("ELEMENT_BENEFITS_ASSETS_v1.3.html", "Benefits & Assets"),
    ("ELEMENT_CURRENT_WORK_OBJECT_QUEUE_v1.3.html", "Current Work Object & Queue"),
    ("ELEMENT_CONTEXT_MEMBRANE_v1.3.html", "Context & Membrane"),
    ("ELEMENT_AGENT_RUNTIME_ROUTING_v1.3.html", "Agent & Runtime Routing"),
]

log = []


def note(step, detail):
    log.append((step, detail))
    print(f"[{step}] {detail}")


# ---------------------------------------------------------------- navigator
def build_navigator():
    t = (SRC / NAV).read_text(encoding="utf-8")
    orig_len = len(t)

    # C1 — cold-start position: don't let a hash-less load select/scroll to
    # #operate. Root cause is browser-native anchor scroll (or async restore)
    # triggered by the URL fragment ending up as '#operate' on init; the JS
    # itself only calls scrollIntoView when an explicit anchor is passed
    # (which it isn't on cold start). Fix: only run the routing/history
    # side effect when a real incoming hash exists; on a genuine cold start,
    # apply the default panel state directly (no history.replaceState, no
    # URL fragment), and force scroll position back to the very top,
    # defeating any native or async scroll-restoration regardless of cause.
    old_init = ("const route=(location.hash||'#operate').slice(1).split('/');"
                "openPanel(['operate','wave','status'].includes(route[0])?route[0]:'operate',false,route[1]||null);")
    assert old_init in t, "C1: expected init routing line not found"
    new_init = (
        "history.scrollRestoration&&(history.scrollRestoration='manual');"
        "const initialHash=location.hash;"
        "const route=(initialHash||'#operate').slice(1).split('/');"
        "const initialPanel=['operate','wave','status'].includes(route[0])?route[0]:'operate';"
        "if(initialHash){openPanel(initialPanel,false,route[1]||null);}"
        "else{panels.forEach(p=>p.classList.toggle('active',p.id===initialPanel));"
        "primary.forEach(b=>b.classList.toggle('active',b.dataset.open===initialPanel));}"
        "const _r1c1Top=()=>window.scrollTo(0,0);_r1c1Top();"
        "requestAnimationFrame(_r1c1Top);setTimeout(_r1c1Top,0);"
    )
    t = t.replace(old_init, new_init)
    note("C1", "cold-start no-scroll: init routing no longer writes #operate to "
              "history/URL on a hash-less load; explicit scroll-to-top (sync + rAF "
              "+ timeout) defeats any native/async scroll-restoration; deep links "
              "with an explicit hash still route+anchor-scroll as before")

    # C2 — mobile priority/element layout: the @media(max-width:1400px) hero
    # 3-column rule sits AFTER the @media(max-width:820px) 1-column rule in
    # source order, so at mobile widths (< 820px, which also matches
    # < 1400px) the later, wider-range rule wins the cascade and reintroduces
    # the 3-column layout. Fix: scope the 1400px rule to min-width:821px so
    # it only applies in the tablet/small-desktop band it was meant for,
    # without touching its intended behaviour there.
    old_hero_1400 = "@media(max-width:1400px){.hero{grid-template-columns:.9fr 1.28fr 1fr}.priority-copy b{font-size:12px}}"
    assert old_hero_1400 in t, "C2: expected 1400px hero rule not found"
    new_hero_1400 = "@media(min-width:821px) and (max-width:1400px){.hero{grid-template-columns:.9fr 1.28fr 1fr}.priority-copy b{font-size:12px}}"
    t = t.replace(old_hero_1400, new_hero_1400)
    note("C2", "mobile layout: scoped the .hero 3-column @media(max-width:1400px) "
              "rule to min-width:821px so it can no longer win the cascade below "
              "the 820px single-column breakpoint; no other rule touched")

    # C3 — persistent operating identity header. Static (no live ACL
    # simulation), sourced from the same values already shown elsewhere on
    # this exact page (WO id, PPV, authority summary) so it carries no new
    # claim. Placed in the page <header>, above the hero, so it's visible
    # pre-scroll on both desktop and mobile without JS.
    old_header = ('<header class="top"><h1>SynapSys Navigator</h1>'
                 '<p>Primary Steward operating surface v1.5 — nine-element 3×3 / 3×3×3 '
                 'integration package, priorities and governed delivery.</p></header>')
    assert old_header in t, "C3: expected header block not found"
    id_header = (
        '<header class="top"><h1>SynapSys Navigator</h1>'
        '<p>Primary Steward operating surface v1.5 — nine-element 3×3 / 3×3×3 '
        'integration package, priorities and governed delivery.</p>'
        '<div id="r1c3-identity" role="note" aria-label="Persistent operating identity" '
        'style="margin-top:8px;padding:7px 10px;background:rgba(255,255,255,.08);'
        'border:1px solid rgba(255,255,255,.25);border-radius:8px;font-size:11.5px;'
        'line-height:1.5;display:flex;flex-wrap:wrap;gap:6px 14px">'
        '<span><b>Role:</b> Steward / D001 — internal</span>'
        '<span><b>Context/membrane:</b> CTX-SS (internal Steward projection)</span>'
        '<span><b>Plane:</b> Form / Flow / Evolve (selectable below)</span>'
        '<span><b>Work Object:</b> WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001</span>'
        '<span><b>PPV:</b> Potential</span>'
        '<span><b>Authority:</b> HELD — projection/link scope only</span>'
        '<span><b>Source/freshness:</b> Obsidian projection; see Status/Mesh for snapshot</span>'
        '<span><b>STOP/HOLD:</b> no live ACL, Odoo, N8N or runtime action from this page</span>'
        '</div></header>'
    )
    t = t.replace(old_header, id_header)
    note("C3", "persistent operating identity header added to <header>: role, "
              "Context/membrane, plane, Work Object, PPV, authority, "
              "source/freshness, STOP/HOLD - static, no live ACL simulated")

    # C4 — non-Steward role fail-closed disclosure. Placed directly under the
    # identity header content, inside the hero card (first thing in main
    # content), so it's visible without reconstruction.
    old_truth = ('<div class="truth"><b>MECE interaction rule:</b> the three buttons '
                'are where work happens; Top Five Priorities state what to do; '
                'MVP Elements show what exists, its integrity and where to inspect it. '
                'No second control strip is used. The Mesh/DIM antifragile challenge '
                'is mandatory before any gate opening, activation or promotion.</div>')
    assert old_truth in t, "C4/C5 anchor: expected truth notice not found"
    disclosure = (
        old_truth +
        '<div id="r1c4-role-boundary" class="truth" style="margin-top:8px">'
        '<b>Role boundary (fail-closed):</b> governance member, Project-owner and '
        'Benefit-owner routes on this surface are internal governed routes, bounded '
        'by assigned Context and authority. Collaborator/partner and client sponsor '
        'access is <b>not available</b> through this Steward surface — external '
        'access remains fail-closed and separately held. No control on this page '
        'implies live authentication, ACL enforcement or a permission grant; '
        'changing a label or selection here changes nothing outside this projection.'
        '</div>'
    )
    t = t.replace(old_truth, disclosure)
    note("C4", "fail-closed role-boundary disclosure added directly under the "
              "primary-actions notice: internal-governed vs external-unavailable "
              "stated explicitly; no control implies live ACL/authentication")

    # C5 — one current next action. The page currently exposes two different
    # next-action texts: a static "Steward reminders" cell ("Run the filed
    # cold-start resolution prompt...") and a static status-panel metric
    # ("Identify the named LCC sponsor..."), with no top-level field telling
    # the Steward which one is current. Fix: add one clearly labelled
    # "Current next action" field in the hero (visible pre-scroll) carrying
    # the queue-constraint text (copied verbatim from the existing
    # authoritative status-panel metric, so no new claim is introduced), and
    # relabel the steward-reminders cell as a supporting/held item so it no
    # longer reads as a second, competing current action.
    old_objective = ('<p class="objective"><b>Current objective:</b> Operate the '
                     'accepted Navigator through real Mesh/DIM challenge and close '
                     'the evidence and authority constraint on CAND-OFF-20260803-02 '
                     'without premature activation.</p>')
    assert old_objective in t, "C5: expected objective paragraph not found"
    next_action_text = ("Identify the named LCC sponsor or decision recipient and "
                        "resolve evidence references 5b6a61f0 and 59b2e98e; then "
                        "complete the bounded orientation/baseline brief or return "
                        "CAND-OFF-20260803-02 to Signal/Monitor. V7 remains HOLD.")
    assert next_action_text in t, "C5: expected authoritative next-action text not found"
    current_action_block = (
        old_objective +
        f'<p id="r1c5-current-next-action" class="objective" style="margin-top:6px">'
        f'<b>Current next action:</b> {next_action_text}</p>'
    )
    t = t.replace(old_objective, current_action_block)
    note("C5a", "added a single top-level 'Current next action' field in the hero "
               "(visible pre-scroll), text taken verbatim from the existing "
               "authoritative status-panel metric — no new claim introduced")

    old_reminder_label = '<div class="reminder-cell"><b>Next action</b><span>Run the filed cold-start resolution prompt; return five resolution artefacts and the final decision receipt.</span></div>'
    assert old_reminder_label in t, "C5: expected steward-reminder cell not found"
    new_reminder_label = old_reminder_label.replace(
        "<b>Next action</b>", "<b>Supporting action (steward reminder, held)</b>")
    t = t.replace(old_reminder_label, new_reminder_label)
    note("C5b", "relabelled the Steward-reminders 'Next action' cell to "
               "'Supporting action (steward reminder, held)' so it no longer "
               "competes with the single current-next-action field")

    # C6 — direct return continuity: fix element hrefs (v1.5 already links
    # to v1.3 pages; nothing to change here — this correction lives in the
    # element pages themselves, see build_element_pages()). No v1.0/v0.2
    # target exists in v1.5's own links (verified below).
    assert not re.search(r'ELEMENT_[A-Z_]+_v1\.[02]\.html', t), \
        "C6: v1.5 unexpectedly links a v1.0/v0.2 element page"
    note("C6", "v1.5's own element links already point to v1.3 (verified no "
              "v1.0/v0.2 element target present); the 5 missing return links "
              "are added on the element pages themselves")

    out = CAND / NAV
    out.write_text(t, encoding="utf-8")
    note("navigator", f"{orig_len} -> {len(t)} bytes")
    return out


# ---------------------------------------------------------------- elements
def build_flagged_elements():
    css_add = (
        'nav.routes{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 14px}'
        'nav.routes a{background:#0b6aa2;color:#fff;text-decoration:none;'
        'padding:8px 13px;border-radius:8px;font-size:13.5px;font-weight:700}'
    )
    for fname, label in FLAGGED_ELEMENTS:
        t = (SRC / "COMPONENTS" / fname).read_text(encoding="utf-8")
        orig_len = len(t)
        assert "</style>" in t, f"C6: no </style> in {fname}"
        t = t.replace("</style>", css_add + "</style>", 1)
        assert "<main>" in t, f"C6: no <main> in {fname}"
        nav_html = ('<main>\n<nav class="routes">'
                   f'<a href="../{NAV}">Return to Navigator</a></nav>')
        t = t.replace("<main>", nav_html, 1)
        out = CAND / "COMPONENTS" / fname
        out.write_text(t, encoding="utf-8")
        note("C6", f"{fname} ({label}): added Return-to-Navigator nav "
                  f"({orig_len} -> {len(t)} bytes)")


# ---------------------------------------------------------------- registry
def build_registry():
    src_path = SRC / "DATA" / "NAVIGATOR_L1_L2_L3_ROUTE_REGISTRY.json"
    d = json.loads(src_path.read_text(encoding="utf-8"))
    changed = []
    for e in d["elements"]:
        old = e["routes"]["html"]
        new = old.replace("_v1.2.html", "_v1.3.html")
        assert new != old, f"C7: expected _v1.2.html in {old}"
        e["routes"]["html"] = new
        changed.append((e["id"], old, new))
    out_text = json.dumps(d, separators=(",", ":"), ensure_ascii=False) + "\n"
    out = CAND / "DATA" / "NAVIGATOR_L1_L2_L3_ROUTE_REGISTRY.json"
    out.write_text(out_text, encoding="utf-8")
    for eid, old, new in changed:
        note("C7", f"{eid}: routes.html {old} -> {new}")
    note("C7", f"registry snapshot field left as-is (candidate lineage note: source "
              f"registry snapshot={d.get('snapshot')!r}); 9/9 element html refs now "
              f"name v1.3 pages; canvas_source (.canvas) fields untouched — those are "
              f"real historical v1.2 canvas source filenames, not stale references")
    return out


if __name__ == "__main__":
    nav_out = build_navigator()
    build_flagged_elements()
    reg_out = build_registry()
    print("\ncandidate build complete:", CAND)
