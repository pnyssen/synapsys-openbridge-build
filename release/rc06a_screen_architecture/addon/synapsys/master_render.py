"""Master Architecture renderer (source-only candidate; NOT installed). Pure: dict in, escaped HTML string out. No Odoo import.

Every dynamic value is escaped. The page is responsive without a script (CSS grid auto-fit, scrolling table wrappers, three breakpoints) and is
keyboard-operable: navigation is real <button> elements carrying data-* attributes that the client action reads (static/src/master_nav.js).
It displays; it never writes, promotes or authorises.
"""
from html import escape as _e

try:
    from . import arch_master_views as V
except ImportError:                       # offline tests load this file by path, outside a package
    import arch_master_views as V

SEC_LABEL = {"overview": "Overview", "value": "Value", "kinematics": "Kinematics", "fractals": "Fractals", "perspectives": "Form / Flow / Evolve",
             "effects": "Signal · Benefits · Realisation", "mesh": "Scaffold · Membrane · External", "drill": "Drill-down", "actors": "Perspectives of people",
             "evidence": "Evidence", "holds": "Open rulings (HOLD)"}
SEC_HINT = {"overview": "One architecture, every doorway", "value": "Purpose, Strategies and Assets", "kinematics": "Kinds, stages, nine actions, 27 verbs",
            "fractals": "Recursive lineage from stored links", "perspectives": "The same element seen three ways", "effects": "Enterprise effects, never promoted",
            "mesh": "One Mesh: inside, across, outside", "drill": "Application, group, screen, view, field, data", "actors": "Steward, Collaborator, Client", "evidence": "What the records actually show",
            "holds": "Rules still to be decided"}
STATE_CLASS = {"CONNECTED": "ok", "REAL_ACTOR_VISIBLE": "ok", "ACTUAL_ACCOUNT": "ok", "RESTRICTED": "rs", "NONE_VISIBLE_TO_ACTOR": "nv", "UNOBSERVED": "nv",
               "DEFINED_NO_READABLE_INSTANCE": "nv", "FIELD_NOT_PRESENT": "hd", "MODEL_NOT_INSTALLED": "hd", "NOT_APPLICABLE": "na", "UNRULED_HOLD": "hd",
               "UNKNOWN_HOLD": "hd", "UNOBSERVED_TO_ACTOR": "nv", "GROUP_IN_SOURCE_NOT_TESTED": "hd", "NOT_YOUR_ACCOUNT": "nv"}

CSS = (
    ".syn-master{--ink:#1f2933;--mut:#52606d;--line:#e4e7eb;--bg:#fff;--soft:#f5f7fa;--acc:#2f4f8f;font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;"
    "color:var(--ink);background:var(--bg);box-sizing:border-box;max-width:100%;overflow-x:hidden}"
    ".syn-master *{box-sizing:border-box;min-width:0}"
    ".syn-master .sm-head{padding:14px clamp(12px,3vw,28px) 6px}.syn-master h1{font-size:clamp(1.15rem,3.5vw,1.6rem);margin:0 0 2px}"
    ".syn-master h2{font-size:1.15rem;margin:18px 0 6px}.syn-master h3{font-size:1rem;margin:0 0 4px}"
    ".syn-master .sm-sub{color:var(--mut);font-size:.875rem;margin:0}"
    ".syn-master .sm-status{display:inline-block;font-size:.75rem;padding:2px 8px;border-radius:999px;background:#fff4e5;color:#7a4b00;border:1px solid #f0d9b5;margin:6px 6px 0 0}"
    ".syn-master .sm-bar{background:var(--bg);border-bottom:1px solid var(--line);padding:6px clamp(12px,3vw,28px)}"
    ".syn-master .sm-row{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:4px 0}"
    ".syn-master .sm-lab{font-size:.8125rem;color:var(--mut);margin-right:2px}"
    ".syn-master button.sm-b{font:inherit;font-size:.875rem;min-height:36px;padding:4px 12px;border:1px solid #c5ccd6;border-radius:8px;background:#fff;color:var(--ink);cursor:pointer}"
    ".syn-master button.sm-b[aria-pressed=true],.syn-master button.sm-b[aria-current=page]{background:var(--acc);border-color:var(--acc);color:#fff}"
    ".syn-master button.sm-b:focus-visible,.syn-master a:focus-visible{outline:3px solid #f5a623;outline-offset:2px}"
    ".syn-master .sm-nav{display:flex;gap:6px;overflow-x:auto;padding-bottom:4px;-webkit-overflow-scrolling:touch}.syn-master .sm-nav button{flex:0 0 auto}"
    ".syn-master main{padding:6px clamp(12px,3vw,28px) 28px;max-width:1400px}"
    ".syn-master .sm-grid{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(min(100%,260px),1fr))}"
    ".syn-master .sm-card{border:1px solid var(--line);border-radius:10px;padding:12px 14px;background:var(--bg)}"
    ".syn-master .sm-card.soft{background:var(--soft)}.syn-master .sm-card,.syn-master li,.syn-master .sm-note,.syn-master p{overflow-wrap:anywhere}"
    ".syn-master .sm-scroll{overflow-x:auto;max-width:100%;border:1px solid var(--line);border-radius:8px}"
    ".syn-master table{border-collapse:collapse;width:100%;font-size:.8125rem}"
    ".syn-master th,.syn-master td{text-align:left;padding:6px 8px;border-bottom:1px solid var(--line);vertical-align:top;overflow-wrap:anywhere}"
    ".syn-master th{background:var(--soft);font-weight:600}"
    ".syn-master .st{display:inline-block;font-size:.72rem;padding:1px 7px;border-radius:6px;background:#eef1f5;color:#3e4c59;overflow-wrap:anywhere}"
    ".syn-master .st.ok{background:#e3f6ea;color:#14532d}.syn-master .st.rs{background:#fde8e8;color:#7f1d1d}.syn-master .st.nv{background:#eef1f5;color:#3e4c59}"
    ".syn-master .st.hd{background:#fff4e5;color:#7a4b00}.syn-master .st.na{background:#f5f5f5;color:#6b7280}"
    ".syn-master .sm-note{font-size:.8125rem;color:var(--mut);margin:6px 0}"
    ".syn-master details{margin:6px 0}.syn-master summary{cursor:pointer;min-height:32px}"
    ".syn-master ul{margin:4px 0;padding-left:1.1rem}.syn-master code{font-size:.8em;overflow-wrap:anywhere}"
    ".syn-master .sm-tree ul{list-style:none;padding-left:.9rem;border-left:1px dashed var(--line)}"
    ".syn-master .sm-embed{overflow-x:auto;max-width:100%;border:1px solid var(--line);border-radius:10px;padding:4px 8px;margin:8px 0}"
    ".syn-master .sm-crumbs{display:flex;flex-wrap:wrap;gap:4px;align-items:center;margin:4px 0 10px}.syn-master .sm-crumbs span{color:var(--mut)}"
    ".syn-master a.sm-link{display:inline-block;min-height:32px;padding:4px 10px;border:1px solid var(--acc);border-radius:8px;color:var(--acc);text-decoration:none;overflow-wrap:anywhere}"
    ".syn-master a.sm-link:hover{background:#eef3fb}"
    "@media (max-width:600px){.syn-master{font-size:14px}.syn-master button.sm-b{min-height:44px;padding:6px 12px}.syn-master .sm-grid{grid-template-columns:1fr}"
    ".syn-master th,.syn-master td{padding:5px 6px}}"
    "@media (min-width:601px){.syn-master .sm-bar{position:sticky;top:0;z-index:3}}"
    "@media (min-width:601px) and (max-width:1024px){.syn-master .sm-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}"
    "@media (min-width:1025px){.syn-master .sm-grid{grid-template-columns:repeat(3,minmax(0,1fr))}}"
    "@media (prefers-reduced-motion:reduce){.syn-master *{animation:none!important;transition:none!important}}"
)


def e(x):
    return _e("" if x is None else str(x), quote=True)


def st(state):
    s = str(state)
    return '<span class="st %s">%s</span>' % (STATE_CLASS.get(s.split(":")[0], "hd" if s.startswith("HOLD") else ""), e(s))


def btn(label, pressed=None, current=None, **data):
    attrs = "".join(' data-%s="%s"' % (k.replace("_", "-"), e(v)) for k, v in data.items())
    extra = ""
    if pressed is not None:
        extra += ' aria-pressed="%s"' % ("true" if pressed else "false")
    if current:
        extra += ' aria-current="page"'
    return '<button type="button" class="sm-b"%s%s>%s</button>' % (attrs, extra, e(label))


def table(head, rows):
    h = "".join("<th scope=\"col\">%s</th>" % e(c) for c in head)
    b = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % c for c in r) for r in rows)
    return '<div class="sm-scroll" tabindex="0" role="region" aria-label="table"><table><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (h, b)


def count(c):
    return "none visible to you" if c is None else e(c)


# ------------------------------------------------------------------------------------------------------------------------ sections
def r_value(v):
    p, s, a, ed = v["purposes"], v["strategies"], v["assets"], v["edges"]
    groups = "".join('<li><b>%s</b> %s %s</li>' % (e(g.title()), count(d["count"]), "".join("<br><span class=\"sm-note\">%s</span>" % e(i["label"]) for i in d["items"])) for g, d in s["groups"].items())
    cards = ('<div class="sm-card"><h3>Purpose</h3>%s<p>%s</p>%s</div>' % (st(p["state"]), count(p["count"]), "".join("<div class=\"sm-note\">%s</div>" % e(i["label"]) for i in p["items"])) +
             '<div class="sm-card"><h3>Strategies</h3>%s<p>%s</p><ul>%s</ul><p class="sm-note">Live / Build / Adapt from %s. Ungrouped: %s.</p></div>' % (st(s["state"]), count(s["count"]), groups, e(s["group_source"]), count(s["ungrouped_count"])) +
             '<div class="sm-card"><h3>Assets</h3>%s<p>%s</p>%s</div>' % (st(a["state"]), count(a["count"]), "".join("<div class=\"sm-note\">%s (Context %s)</div>" % (e(i["label"]), e(i["context_id"])) for i in a["items"])))
    rel = table(["Relationship (stored field)", "State", "Readable instance edges"],
                [[e(k.replace("_", " ")), st(d["state"]), e(d["instance_edges"])] for k, d in ed.items()])
    return ('<h2>Value: Purpose, Strategies, Assets</h2><div class="sm-grid">%s</div><h3 style="margin-top:14px">Typed relationships</h3>%s'
            '<p class="sm-note">There is no Strategy to Asset field. Assets belong to a Context; nothing here infers a Strategy to Asset link (HOLD H09).</p>' % (cards, rel))


def r_kin(k):
    cut = "".join('<div class="sm-card soft"><h3>%s</h3><div>%s</div></div>' % (e(stage), e(", ".join(kinds))) for stage, kinds in k["cut_b"].items())
    modes = table(["K-kind", "Allowed verb ids (ruled Context Mode)"], [[e(kk), e(", ".join(map(str, ids)))] for kk, ids in k["modes"].items()])
    acts = table(["Perspective", "Action", "Verbs (3)", "Grammar"],
                 [[e(a["perspective"]), e(a["action"]), e(", ".join("%s%s" % (v["name"], " (human only)" if v["human_only"] else "") for v in a["verbs"])),
                   e(", ".join(sorted({v["grammar_status"] for v in a["verbs"]})))] for a in k["actions"]])
    ctx = table(["Context", "Kind", "Stage", "Eligible verbs", "Executable"],
                [[e(c["label"]), st(c["kind"] or c["kind_state"]), e(c["stage"] or "not shown (unruled)"), e(c["eligible"]["state"] + (": " + ", ".join(c["eligible_names"]) if c["eligible_names"] else "")),
                  st("NO: eligibility is not authority")] for c in k["contexts"]]) if k["contexts"] else '<p class="sm-note">No Context is visible to your account. That can mean restricted or absent; it is not shown as empty.</p>'
    return ('<h2>Kinematics</h2><h3>Cut B: stage comes from the ruled K-kind</h3><div class="sm-grid">%s</div>%s<h3 style="margin-top:14px">Nine actions, 27 verbs</h3>%s'
            '<h3 style="margin-top:14px">Your Contexts</h3>%s<p class="sm-note">Display depth never confers a K-kind or stage (HOLD H01). Human-only verbs are never eligible for automated action.</p>'
            % (cut, table(["K-kind", "Allowed verb ids (ruled Context Mode)"], [[e(kk), e(", ".join(map(str, ids)))] for kk, ids in k["modes"].items()]), acts, ctx))


def _tree(nodes):
    if not nodes:
        return ""
    return "<ul>%s</ul>" % "".join("<li><code>%s</code>%s%s</li>" % (e(n["id"]), " (cycle cut)" if n.get("cycle") else "", _tree(n.get("children"))) for n in nodes)


def r_frac(f):
    tree = '<div class="sm-tree">%s</div>' % _tree(f["tree"]) if f["tree"] else '<p class="sm-note">No readable stored link yet; nothing is inferred.</p>'
    rec = table(["Fractal evidence field", "State", "Readable rows", "Values"],
                [[e(k), st(d["state"]), count(d["total"]), e(", ".join("%s: %s" % kv for kv in d["by_value"].items()))] for k, d in f["fractal_records"].items()])
    return '<h2>Fractals</h2><p class="sm-note">%s.</p><h3>Lineage</h3>%s<h3>Fractal evidence records</h3>%s<p class="sm-note">%s.</p>' % (e(f["lineage_basis"]), tree, rec, e(f["recursion"]))


def r_persp(ps):
    out = ['<h2>Form, Flow and Evolve: different projections of the same source</h2>']
    for p, d in ps.items():
        rows = [[e(r["path"]), e(r["model"]), st(r["record_state"]), "".join("<div><code>%s</code> %s %s %s edges</div>" % (e(x["field"]), e(x["cardinality"]), st(x["state"]), e(x["instance_edges"])) for x in r["edges"])] for r in d["rows"]]
        out.append('<h3>%s: %s typed edges, %s readable instance edges, %s of %s menus carry an edge</h3>%s' % (e(p), e(d["typed_edges"]), e(d["instance_edges"]), e(d["menus_with_edges"]), e(d["menus_total"]),
                                                                                                         table(["Menu", "Model", "Record state", "Typed edges (direction out)"], rows)))
    out.append('<p class="sm-note">Switching perspective changes the edges and counts, not only the caption. A perspective with no edge for a menu simply lists no row for it.</p>')
    return "".join(out)


def r_effects(f):
    s, b, r = f["signal"]["records"], f["benefits"], f["realisation"]
    def tally(d): return "%s, %s%s" % (st(d["state"]), count(d["total"]), "".join(" · %s: %s" % kv for kv in d["by_value"].items()))
    return ('<h2>Enterprise Signal, Benefits, Realisation</h2><p class="sm-note">Enterprise effects, not data levels. They are not forced into a nine-cell symmetry.</p><div class="sm-grid">'
            '<div class="sm-card"><h3>Signal</h3><p>%s</p></div>'
            '<div class="sm-card"><h3>Benefits</h3><p>PPV values: %s</p><p>Outcomes with observed baseline: %s</p><p>Qualified Assets: %s</p><p>Benefit-Asset links: %s</p></div>'
            '<div class="sm-card"><h3>Realisation</h3><p>%s</p><p>Source values: %s</p><p class="sm-note">%s. No AI promotion, no PPV movement (HOLD H07).</p></div></div>'
            % (tally(s), tally(b["records"]), tally(b["outcomes_baseline_observed"]), tally(b["qualified_assets"]), count(b["benefit_asset_links"]["count"]), st(r["state"]), tally(r["source_values"]), e(r["rule"])))


def r_mesh(m):
    sc = table(["Context", "Strategies", "Services (direct FK)", "Methods", "Assets"], [[e(r["label"]), e(r["strategies"] if isinstance(r["strategies"], str) else count(r["strategies"])), e(r["services_direct_fk"] if isinstance(r["services_direct_fk"], str) else count(r["services_direct_fk"])),
                                                                                          e(r["methods"] if isinstance(r["methods"], str) else count(r["methods"])), e(r["assets"] if isinstance(r["assets"], str) else count(r["assets"]))] for r in m["scaffold"]]) if m["scaffold"] else '<p class="sm-note">No Context readable by your account.</p>'
    mem = table(["Relationship", "From Context", "To Context", "Ruling"], [[e(x["edge"]), e(x["from_context"]), e(x["to_context"]), st(x["ruling"])] for x in m["membrane"]]) if m["membrane"] else '<p class="sm-note">No readable cross-Context relationship.</p>'
    ex = table(["External signal", "State", "Readable rows", "Values"], [[e(k), st(d["state"]), count(d["total"]), e(", ".join("%s: %s" % kv for kv in d["by_value"].items()))] for k, d in m["external"].items()])
    return ('<h2>One Mesh: Scaffold, Membrane, External</h2><h3>Scaffold (a Context and its direct members)</h3>%s<h3>Membrane (readable relationships across Contexts)</h3>%s<p class="sm-note">%s.</p>'
            '<h3>External (rights holders and partners)</h3>%s' % (sc, mem, e(m["membrane_rule"]), ex))


def r_actors(a):
    rows = [[e(k.title()), st(v["state"]), e(v["entitled_menus"] if v.get("entitled_menus") is not None else "not available")] for k, v in a["perspectives"].items()]
    rd = a["role_definitions"]
    if rd["state"] == "LOADED":
        grp = table(["Group (installed source)", "Display name", "Implies"], [[e(k), e(v["display_name"]), e(", ".join(v["implies"]))] for k, v in rd["groups"].items()] + [["(none)", "Client", st("HOLD:H02")]])
        mod = table(["Model", "Steward operations", "Collaborator operations", "Collaborator row-scoped"],
                    [[e(m), e(v["steward"]["operations"]), e(v["collaborator"]["operations"]), e("yes" if v["collaborator"]["row_scoped"] else "no")] for m, v in rd["by_model"].items()])
        roles = '<h3>Existing role definitions</h3>%s<p class="sm-note">%s. Row scoping is shown, never evaluated here; the real rule is the server\'s record rule. %s.</p>%s' % (grp, e(rd["entitled_basis"]), e(rd["client_note"]), mod)
    else:
        roles = '<p class="sm-note">Role definitions: %s.</p>' % st(rd["state"])
    return ('<h2>Steward, Collaborator, Client</h2><p>Your actual role on this server: <b>%s</b>. Data shown is always your own account\'s rights. You are viewing: <b>%s</b> (%s).</p>%s'
            '<p class="sm-note">Steward-only menus in the definition: %s of %s. Choosing another perspective never widens what you can see. The Collaborator group exists in the installed source but no real Collaborator account has been tested; Client has no group in the source (HOLD H02).</p>%s'
            % (e(a["actual_role"]), e(a["requested"]), e(a["data_view"]), table(["Perspective", "State", "Entitled menus"], rows), e(len(a["steward_only_menu_ids"])), e(a["menus_total"]), roles))


def r_evid(v):
    ch = "".join('<details><summary>%s: %s%s</summary>%s</details>' % (e(c["label"]), "connected end to end" if c["stopped_at"] is None else "stops at " + e(c["stopped_at"]) + " (" + e(c["reason"]) + ")", "",
                                                                    table(["Hop", "State", "Detail"], [[e(s["step"]), st(s["state"]), e(", ".join("%s=%s" % (k, s[k]) for k in s if k not in ("step", "state")))] for s in c["steps"]])) for c in v["chains"]) or '<p class="sm-note">No Context readable by your account.</p>'
    acc = v["acceptance"]
    return ('<h2>Evidence</h2><h3>Context to Asset chains (what the records show)</h3>%s<h3>Definition</h3>%s<p class="sm-note">Pins: contract %s, baseline %s. Matrix statuses are source facts from one read-only actor, not role tests. Role tests: %s. Browser tests in V20: %s. Installed: %s.</p><p>Acceptance matrix: %s</p>'
            % (ch, table(["Menu status", "Count"], [[e(k), e(n)] for k, n in v["menu_status_counts"].items()]), e(v["pins"]["contract_sha256"][:12]), e(v["pins"]["baseline_sha256"][:12]), e(v["role_tests"]), e(v["browser_tests"]), e(v["installed"]), st(acc.get("state", "NOT_LOADED"))))


def kv_table(d):
    return table(["Fact", "Value"], [[e(k), e("(none)" if v in (None, "") else v)] for k, v in d.items()])


def _link(href, label):
    return '<a class="sm-link" href="%s">%s</a>' % (e(href), e(label)) if href else ""


def _ov_anchors(html):
    """The existing lens renderer emits depth-override controls as bare anchors (not keyboard reachable). Make them operable in the Master without touching that renderer."""
    return html.replace('<a class="tg" data-ovel=', '<a class="tg" role="button" tabindex="0" href="#" data-ovel=')


def _child_rows(ch):
    rows = []
    for c in ch:
        if "menu_id" in c:
            rows.append([btn(c["label"], drill=c["drill"]), e(c["kind"]), e(c["model"] or "(navigation)"), st(c["record_state"]), st(c["matrix_status"]) + (" " + st("HOLD") if c["hold"] else ""), _link(c["native_link"], "Open native screen")])
        else:
            rows.append([btn(c["label"], drill=c["drill"]), "", "", "", "", ""])
    return table(["Open", "Kind", "Model", "Records you can read", "Status", "Native"], rows) if rows and "menu_id" in ch[0] else \
        '<div class="sm-row">%s</div>' % "".join(btn(c["label"], drill=c["drill"]) for c in ch)


def _three(d):
    c, ef, ac = d["canonical"], d["effective"], d["actual"]
    cdef = {k: c[k] for k in ("path", "kind", "action_ref", "model", "domain", "view_mode", "client_tag", "source_status", "definition_state", "steward_only", "matrix_status") if k in c}
    if c.get("definition"): cdef["definition"] = c["definition"]
    if c.get("definition_gap"): cdef["definition_gap"] = c["definition_gap"]
    if c.get("hold_reason"): cdef["hold"] = c["hold_reason"]
    eff = '<p>%s</p>%s' % (st(ef["state"]), e(ef.get("reason", ""))) + ("".join('<div class="sm-note">%s: definition <code>%s</code>, platform <code>%s</code></div>' % (e(x["fact"]), e(x["definition"]), e(x["effective"])) for x in ef.get("differences", [])))
    if ef.get("effective"): eff += kv_table(ef["effective"])
    act = '<p>%s</p>' % st(ac["state"]) + (e("readable rows: %s" % ac["readable_count"]) if ac.get("readable_count") else e(ac.get("reason", "")))
    return ('<div class="sm-grid"><div class="sm-card"><h3>Canonical definition</h3><p class="sm-note">the versioned definition file</p>%s</div>'
            '<div class="sm-card"><h3>Effective platform configuration</h3><p class="sm-note">read under your rights; SOURCE_UNVERIFIED when not read</p>%s</div>'
            '<div class="sm-card"><h3>Actual operational records</h3><p class="sm-note">rows you can read</p>%s</div></div>' % (kv_table(cdef), eff, act))


def r_rec(d):
    f = table(["Field", "State", "Value"], [[e(x["field"]), st(x["state"]), e(x["value"]) + (" (shortened)" if x.get("truncated") else "")] for x in d["fields"]])
    rl = table(["Direction", "Field", "Record", "Open"], [[e(x["direction"]), e(x["field"]), e(x["label"]), btn("Open", drill=x["rec"]) if x["rec"] else e(x["model"])] for x in d["relationships"]]) if d["relationships"] else '<p class="sm-note">No readable related record.</p>'
    fr = table(["Fractal evidence", "Realisation", "Evidence state", "Admission", "Gate"], [[e(x["label"]), e(x["realisation"]), e(x["evidence_state"]), e(x["admission"]), e(x["gate_level"])] for x in d["linked_fractal_evidence"]]) if d["linked_fractal_evidence"] else '<p class="sm-note">No readable fractal evidence is linked to this record.</p>'
    em, au, re_ = d["evidence_maturity"], d["authority"], d["realisation"]
    emb = '<div class="sm-embed">%s</div>' % d["record_screen"]["html"] if d.get("record_screen") and d["record_screen"].get("html") else ""
    return ('<h3>%s</h3><p>%s</p><h3>Source values</h3>%s<h3>Related records you can read (%s)</h3>%s<h3>Linked fractal evidence</h3>%s'
            '<div class="sm-grid"><div class="sm-card"><h3>Evidence maturity</h3><p class="sm-note">%s</p><p>PPV as stored: %s</p><p>Qualification flag check: %s</p></div>'
            '<div class="sm-card"><h3>Authority</h3><p>%s</p><p>PPV movement: %s. AI promotion: %s.</p></div>'
            '<div class="sm-card"><h3>Realisation</h3><p>%s</p><p class="sm-note">%s</p></div></div>%s<div class="sm-embed">%s</div>%s'
            % (e(d["label"]), e(d["model"]), f, e(d["relationships_total"]), rl, fr, e(em["basis"]), e(em["ppv"]), st(em["qualification_flag_check"]), e(au["acceptance"]), e(au["ppv_movement"]), e(au["ai_promotion"]),
               st(re_["state"]), e(re_["rule"]), _link(d["native_link"], "Open native record"), _ov_anchors(d["lens"]), emb))


def r_drill(d):
    if d["state"] != "OK":
        return '<h2>Drill-down</h2><p>%s %s</p>%s' % (st("NOT_AVAILABLE"), e(d["reason"]), btn("Back to Application", drill="app"))
    crumbs = '<nav class="sm-crumbs" aria-label="Drill-down path">%s</nav>' % ' <span aria-hidden="true">›</span> '.join(btn(c["label"], current=(i == len(d["breadcrumb"]) - 1), drill=c["drill"]) for i, c in enumerate(d["breadcrumb"]))
    lv = d["level"]
    head = '<h2>Drill-down: %s</h2>%s' % (e({"app": "Application", "grp": "Menu group", "scr": "Screen", "view": "View", "fld": "Field", "data": "Data", "rec": "Record"}[lv]), crumbs)
    note = '<p class="sm-note">Links open the native Odoo screen and appear only where your account can see the menu and read the record. %s.</p>' % e(d["link_scheme"])
    if lv == "rec":
        return head + r_rec(d)
    body = _three(d)
    if lv in ("app", "grp"):
        body += '<h3>%s</h3>%s' % (e(d["child_label"]), _child_rows(d["children"]))
        if lv == "app" and d["root"]["native_link"]: body += _link(d["root"]["native_link"], "Open native application")
    if lv == "scr":
        sp = d["screen"]
        body += '<h3>Existing scaffold screen (reused renderer)</h3>' + ('<div class="sm-embed">%s</div>' % sp["html"] if sp.get("html") else '<p>%s %s</p>' % (st(sp["state"]), e(sp.get("reason", ""))))
        body += '<h3>Lens (reused renderer, same depth and overrides)</h3><div class="sm-embed">%s</div>' % _ov_anchors(d["lens"]) + _link(d["menu"]["native_link"], "Open native screen")
        body += '<h3>%s</h3><div class="sm-row">%s</div>' % (e(d["child_label"]), "".join(btn(c["label"], drill=c["drill"]) for c in d["children"]))
    if lv == "view":
        v = d["view"]
        body += '<h3>View</h3>' + kv_table({"definition view modes": ", ".join(v["definition_modes"]), "effective view modes": ", ".join(v["effective_modes"]) if v["effective_modes"] else "SOURCE_UNVERIFIED",
                                           "effective state": v["effective_state"], "view architecture (ir.ui.view)": v["view_architecture"]["state"] + ": " + v["view_architecture"]["reason"],
                                           "declared native snapshot": json_s(v["declared_native_snapshot"])})
        body += '<h3>%s</h3><div class="sm-row">%s</div>' % (e(d["child_label"]), "".join(btn(c["label"], drill=c["drill"]) for c in d["children"]))
    if lv in ("fld", "data"):
        f = d["field"]
        body += '<h3>Field %s</h3>' % e(f["field"]) + table(["", "Canonical", "Effective", "Actual"], [[e("target"), e(f["canonical"]["target_model"]), e((f["effective"].get("effective") or {}).get("relation") or f["effective"]["state"]), ""],
                                                                                             [e("cardinality"), e(f["canonical"]["cardinality"]), e((f["effective"].get("effective") or {}).get("type") or f["effective"]["state"]), st(f["actual"]["state"])],
                                                                                             [e("readable instance edges"), "", "", e(f["actual"]["instance_edges"])]])
        body += '<p>%s %s</p>' % (st(f["effective"]["state"]), "".join('<span class="sm-note">%s: definition %s, platform %s. </span>' % (e(x["fact"]), e(x["definition"]), e(x["effective"])) for x in f["effective"].get("differences", [])))
    if lv == "fld":
        body += '<div class="sm-embed">%s</div><div class="sm-row">%s</div>' % (_ov_anchors(d["lens"]), "".join(btn(c["label"], drill=c["drill"]) for c in d["children"]))
    if lv == "data":
        dt = d["data"]
        rows = [[e("%s (%s)" % (x["from"]["label"], x["from"]["id"])), (btn("Open", drill=x["from"]["rec"]) if x["from"]["rec"] else "") + _link(x["from"]["link"], "Native"),
                 e("%s (%s)" % (x["to"]["label"], x["to"]["id"])), (btn("Open", drill=x["to"]["rec"]) if x["to"]["rec"] else "") + _link(x["to"]["link"], "Native")] for x in dt["pairs"]]
        body += '<h3>Data you can read</h3><p>%s %s of %s shown%s. <span class="sm-note">%s.</span></p>' % (st(dt["state"]), e(dt["shown"]) if dt["pairs"] else "counts only at Enable depth: ", e(dt["total_readable"]), " (shortened)" if dt["truncated"] else "", e(dt["rule"]))
        if rows: body += table(["From", "", "To", ""], rows)
    return head + body + note


def json_s(x):
    import json as _j
    return "SOURCE_UNVERIFIED" if x is None else _j.dumps(x, sort_keys=True)


def r_holds(h):
    return '<h2>Open rulings (HOLD)</h2><p class="sm-note">Unresolved rules and unavailable capabilities are shown, not silently decided.</p>' + table(["Id", "Item", "State", "Detail"], [[e(x["id"]), e(x["title"]), st(x["state"]), e(x["text"])] for x in h])


def r_overview(d):
    cards = [("value", "Value"), ("kinematics", "Kinematics"), ("fractals", "Fractals")]
    c = '<div class="sm-grid">%s</div>' % "".join('<div class="sm-card"><h3>%s</h3><p class="sm-note">%s</p>%s</div>' % (e(SEC_LABEL[k]), e(SEC_HINT[k]), btn("Open " + t, section=k)) for k, t in cards)
    return '<h2>One architecture</h2>' + c + '<h2>Concurrent perspectives</h2><div class="sm-grid">%s</div>' % "".join(
        '<div class="sm-card"><h3>%s</h3><p>%s typed edges, %s readable instance edges</p>%s</div>' % (e(p), e(x["typed_edges"]), e(x["instance_edges"]), btn("Open " + p, section="perspectives", persp=p)) for p, x in d["perspectives"].items()
    ) + '<p class="sm-note">Definition: %s menus (%s actions, %s containers), %s verbs. Nothing on this page is installed or accepted.</p>' % tuple(e(d["definition"]["counts"][k]) for k in ("menus", "actions", "containers", "verbs"))


def render_page(d):
    """The complete page for one navigation state (the dict from arch_master_views.assemble)."""
    sec, persp, depth, req = d["section"], d["perspective"], d["depth"], d["actors"]["requested"]
    nav = "".join(btn(SEC_LABEL[s], current=(s == sec), section=s) for s in V.SECTIONS)
    pbar = "".join(btn(p, pressed=(p == persp), persp=p) for p in ("Form", "Flow", "Evolve"))
    dbar = "".join(btn(m.title(), pressed=(m == depth), depth=m) for m in V.DEPTHS)
    abar = "".join(btn(a.title(), pressed=(a == req), actor=a) for a in V.ACTORS)
    body = {"overview": lambda: r_overview(d), "value": lambda: r_value(d["value"]), "kinematics": lambda: r_kin(d["kinematics"]), "fractals": lambda: r_frac(d["fractals"]),
            "perspectives": lambda: r_persp(d["perspectives"]), "effects": lambda: r_effects(d["effects"]), "mesh": lambda: r_mesh(d["mesh"]), "drill": lambda: r_drill(d["drill"]), "actors": lambda: r_actors(d["actors"]),
            "evidence": lambda: r_evid(d["evidence"]), "holds": lambda: r_holds(d["holds"])}[sec]()
    return ('<style>%s</style><div class="syn-master" data-section="%s" data-perspective="%s" data-depth="%s">'
            '<header class="sm-head"><h1>Master Architecture</h1><p class="sm-sub">%s</p><span class="sm-status">Candidate · not installed · read-only</span><span class="sm-status">Role tests: not tested</span></header>'
            '<div class="sm-bar"><nav class="sm-nav" aria-label="Master Architecture sections">%s</nav>'
            '<div class="sm-row"><span class="sm-lab">Perspective</span>%s<span class="sm-lab">Depth</span>%s<span class="sm-lab">View as</span>%s</div></div>'
            '<main id="sm-main" tabindex="-1" aria-live="polite">%s</main></div>'
            % (CSS, e(sec), e(persp), e(depth), e(SEC_HINT[sec]), nav, pbar, dbar, abar, body))
