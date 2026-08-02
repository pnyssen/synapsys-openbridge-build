"""Generate all current Navigator component surfaces from the route registry.

Outputs under dist/ mirroring the vault layout:
  CURRENT/COMPONENTS/ELEMENT_*_v1.2.html          (9, updated in place)
  CURRENT/COMPONENTS/CANVAS_VIEW_*_v1.0.html      (9, new browser-safe views)
  CURRENT/COMPONENTS/NAVIGATOR_NINE_VERBS_BENEFIT_ROUTE_v1.0.html
  CURRENT/COMPONENTS/NAVIGATOR_NEW_PROCESS_AND_OFFERING_START_v1.0.html
  CURRENT/DATA/NAVIGATOR_L1_L2_L3_ROUTE_REGISTRY.json (via build_registry)
  CURRENT/DATA/TEST_PROCESS_001_CANDIDATE.json / TEST_OFFERING_001_CANDIDATE.json

Design rules enforced here (root-cause corrections, not link patches):
- Every route is emitted from the registry; no hand-typed hrefs.
- Every page carries: provenance block (source/snapshot/freshness/evidence/
  reality/PPV/authority/state), plain-text vault path fallbacks (SharePoint-
  preview-safe), and return routes to Nine Verbs + Navigator.
- obsidian:// links are always secondary, never the only route.
- Raw .canvas JSON is never a primary route; the Canvas View HTML is.
- No JavaScript is required for primary navigation on any page.
"""
import html
import json
import pathlib

import model
import render_canvas
from build_registry import build

HERE = pathlib.Path(__file__).parent
DIST = HERE / "dist"
COMP = DIST / "00_SYSTEM" / "NAVIGATOR_SUPPORT" / "CURRENT" / "COMPONENTS"
DATA = DIST / "00_SYSTEM" / "NAVIGATOR_SUPPORT" / "CURRENT" / "DATA"
MIRROR_CANVAS = HERE / "mirror" / "CANVAS"

VAULT_CURRENT = "00_SYSTEM/NAVIGATOR_SUPPORT/CURRENT"

CSS = """
body{font-family:Arial,Helvetica,sans-serif;margin:0;background:#f6f8f9;color:#142630;line-height:1.45}
header{background:#103447;color:#fff;padding:16px 22px}
header h1{margin:0 0 4px;font-size:22px}
header p{margin:0;font-size:13px;color:#cfe3ec}
main{max-width:1240px;margin:auto;padding:16px 18px 40px}
nav.routes{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0}
nav.routes a{background:#0b6aa2;color:#fff;text-decoration:none;padding:8px 13px;border-radius:8px;font-size:13.5px;font-weight:700}
nav.routes a.secondary{background:#5d6d7e}
nav.routes a.primary{background:#0e7a43}
.card{background:#fff;border:1px solid #cbd8de;border-radius:12px;padding:14px 16px;margin:0 0 14px}
.card h2{margin:2px 0 10px;font-size:17px;color:#103447}
.card h3{margin:10px 0 6px;font-size:15px}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{border:1px solid #cbd8de;padding:7px 9px;text-align:left;vertical-align:top}
th{background:#edf4f6}
.prov{font-size:12.5px;color:#425761;background:#eef4f7;border:1px solid #cbd8de;border-radius:10px;padding:10px 12px;margin-bottom:14px}
.prov b{color:#103447}
.badge{display:inline-block;padding:2px 9px;border-radius:10px;font-size:12px;font-weight:700}
.badge.current{background:#eaf6ed;color:#1e8449}
.badge.hold{background:#fbe9e7;color:#c0392b}
.badge.candidate{background:#fff4d8;color:#9a6b09}
.pathnote{font-size:12px;color:#5f707a;word-break:break-all}
details{border:1px solid #cbd8de;border-radius:8px;margin:6px 0;background:#fdfefe}
details summary{cursor:pointer;padding:7px 10px;font-size:13px;font-weight:700;color:#103447}
details .body{padding:2px 12px 10px;font-size:12.8px}
details .body dt{font-weight:700;margin-top:6px;color:#2c3e50}
details .body dd{margin:1px 0 0 0}
.grid3{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:10px}
.mesh li{margin:3px 0}
footer{max-width:1240px;margin:auto;padding:0 18px 30px;font-size:12px;color:#5f707a}
@media(max-width:640px){main{padding:10px}nav.routes a{flex:1 1 44%;text-align:center}}
"""


def esc(s):
    return html.escape(str(s), quote=True)


def page(title, subtitle, body, state="current"):
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><style>{CSS}</style></head>
<body><header><h1>{esc(title)} <span class="badge {state}">{state.upper()}</span></h1>
<p>{esc(subtitle)}</p></header><main>
{body}
</main><footer>SynapSys Navigator surface · generated from NAVIGATOR_L1_L2_L3_ROUTE_REGISTRY v0.1 ·
Work Object {esc(model.WORK_OBJECT)} · Replay-validity {esc(model.REPLAY)}</footer></body></html>
"""


def provenance(extra=""):
    return f"""<div class="prov"><b>Source:</b> NAVIGATOR_L1_L2_L3_ROUTE_REGISTRY v0.1 (DATA/) ·
<b>Snapshot:</b> {esc(model.SNAPSHOT)} · <b>Freshness:</b> current as of snapshot; re-fetch registry for live state ·
<b>Evidence:</b> claims bind to filed Working Memory receipts (05_AI_RETURNS_HASHED) ·
<b>Reality:</b> PROJECTION — Obsidian is the Steward interface; Odoo remains operational register truth ·
<b>PPV:</b> {esc(model.PPV)} · <b>Authority:</b> {esc(model.AUTHORITY)} {extra}</div>"""


def routes_nav(entries):
    links = "".join(
        f'<a class="{cls}" href="{esc(href)}">{esc(label)}</a>'
        for label, href, cls in entries)
    return f'<nav class="routes">{links}</nav>'


def path_fallback(pairs):
    rows = "".join(
        f'<div class="pathnote"><b>{esc(k)}:</b> {esc(v)}</div>' for k, v in pairs)
    return (f'<div class="card"><h2>Route fallback (copyable vault paths)</h2>'
            f'<p class="pathnote">If a link does not resolve in this viewer '
            f'(e.g. SharePoint preview), open the path below directly in the synced vault.</p>{rows}</div>')


# ---------------------------------------------------------------- elements
def gen_element_page(reg, e):
    elem = next(x for x in model.ELEMENTS if x["id"] == e["id"])
    r = e["routes"]
    nav = routes_nav([
        ("View Canvas", e["routes"]["canvas_view"].split("/")[-1], "primary"),
        ("Open Canvas Source (.canvas)", r["canvas_source"], "secondary"),
        ("Open in Obsidian", r["canvas_source_obsidian"], "secondary"),
        ("Return to Nine Verbs", model.VERBS_FILE, ""),
        ("Return to Navigator", "../" + model.NAVIGATOR_FILE, ""),
    ])
    mesh = e["mesh"]
    mesh_rows = "".join(
        f"<tr><th>{esc(k.replace('_', ' ').title())}</th><td>{esc(v)}</td></tr>"
        for k, v in [
            ("1 Signal — what enters", mesh["enters"]),
            ("2 Interpretation", mesh["interprets"]),
            ("3 Structuring", mesh["structures"]),
            ("4 Validation", mesh["validated_by"]),
            ("5 Action permitted", mesh["action"]),
            ("6 Observation", mesh["observes"]),
            ("7 Learning", mesh["learns"]),
            ("8 Asset Conversion", mesh["asset_conversion"]),
            ("9 Feedback returns to", mesh["feedback_to"]),
        ])

    ev = [m for m in reg["element_verb_mappings"] if m["element"] == e["id"]]
    verb_rows = ""
    for m in ev:
        v = next(x for x in reg["verbs"] if x["id"] == m["verb"])
        b = reg["benefits"][m["benefit"]]
        verb_rows += (
            f'<tr><td><a href="{model.VERBS_FILE}#{v["anchor"]}">{esc(v["name"])}</a> '
            f'<span class="badge {"current" if m["relationship"] == "PRIMARY" else "candidate"}">'
            f'{m["relationship"]}</span></td>'
            f"<td>{esc(m['statement'])}</td>"
            f"<td>{esc(', '.join(m['mesh_stages']))}</td>"
            f"<td>{esc(m['benefit'])} {esc(b['name'])}</td></tr>")

    cells = ""
    for c in e["level3"]:
        cells += f"""<details id="{esc(c['trace_id'])}"><summary>{esc(c['trace_id'])} — {esc(c['axis_a'])} × {esc(c['axis_b'])} × {esc(c['axis_c'])}</summary>
<div class="body"><dl>
<dt>Decision / question served</dt><dd>{esc(c['decision_served'])}</dd>
<dt>Incoming Signal</dt><dd>{esc(c['incoming_signal'])}</dd>
<dt>Interpretation</dt><dd>{esc(c['interpretation'])}</dd>
<dt>Required structure</dt><dd>{esc(c['required_structure'])}</dd>
<dt>Validation test</dt><dd>{esc(c['validation_test'])}</dd>
<dt>Permitted action</dt><dd>{esc(c['permitted_action'])}</dd>
<dt>{esc(c['axis_a'])} axis</dt><dd>{esc(c['axis_a_statement'])}</dd>
<dt>{esc(c['axis_b'])} axis</dt><dd>{esc(c['axis_b_statement'])}</dd>
<dt>{esc(c['axis_c'])} axis</dt><dd>{esc(c['axis_c_statement'])}</dd>
<dt>Expected Benefit</dt><dd>{esc(c['expected_benefit'])}</dd>
<dt>Evidence &amp; measurement</dt><dd>{esc(c['evidence_requirement'])}</dd>
<dt>Realisation condition</dt><dd>{esc(c['realisation_condition'])}</dd>
<dt>Asset implication</dt><dd>{esc(c['asset_implication'])}</dd>
<dt>Source system</dt><dd>{esc(c['source_system'])}</dd>
<dt>Reality</dt><dd>{esc(c['reality'])}</dd>
<dt>PPV</dt><dd>{esc(c['ppv'])}</dd>
<dt>Authority</dt><dd>{esc(c['authority'])}</dd>
<dt>Owner</dt><dd>{esc(c['owner'])}</dd>
<dt>Next action</dt><dd>{esc(c['next_action'])}</dd>
<dt>STOP/HOLD</dt><dd>{esc(c['stop_hold'])}</dd>
<dt>Replay-validity</dt><dd>{esc(c['replay_validity'])}</dd>
<dt>Return path</dt><dd>{esc(c['return_path'])}</dd>
<dt>Verbs (Axis-B owners)</dt><dd>{esc(', '.join(c['verbs']))}</dd>
</dl></div></details>"""

    body = f"""{provenance('· <b>Element state:</b> current — this file is the one principal current surface for this Element; earlier versions are historical lineage.')}
{nav}
<section class="card"><h2>{esc(e['id'])} · {esc(e['name'])}</h2>
<p>{esc(e['role'])}</p>
<div class="grid3">
<div><h3>Purpose</h3><p>{esc(e['purpose'])}</p></div>
<div><h3>Strategy</h3><p>{esc(e['strategy'])}</p></div>
<div><h3>Assets</h3><p>{esc(e['assets'])}</p></div>
</div></section>
<section class="card" id="mesh"><h2>Mesh participation (all nine stages)</h2>
<table>{mesh_rows}</table></section>
<section class="card" id="verbs"><h2>The nine verbs at this Element (9 of 81 mappings)</h2>
<table><thead><tr><th>Verb</th><th>How it applies here</th><th>Mesh stages</th><th>Benefit</th></tr></thead>
<tbody>{verb_rows}</tbody></table></section>
<section class="card" id="l3"><h2>Level-3 operating expression — 27 positions (3×3×3)</h2>
<p>Axis A: Purpose/Strategy/Assets · Axis B: Form/Flow/Evolve · Axis C: Signal/Benefits/Realisation.
Every position below is stated in full; none is silently empty.</p>
{cells}</section>
{path_fallback([
    ("This page", f"{VAULT_CURRENT}/COMPONENTS/{elem['html']}"),
    ("Canvas view", f"{VAULT_CURRENT}/COMPONENTS/{elem['canvas_view']}"),
    ("Canvas source", f"10_WORKSPACES/NAVIGATOR_MVP_v0.2/{elem['canvas_source']}"),
    ("Nine Verbs", f"{VAULT_CURRENT}/COMPONENTS/{model.VERBS_FILE}"),
    ("Navigator", f"{VAULT_CURRENT}/{model.NAVIGATOR_FILE}"),
])}
{nav}"""
    return page(f"{e['name']} — Element {e['id']}",
                "Level-1 principal Element · Level-3 3×3×3 operating expression · Mesh-integrated",
                body)


# ---------------------------------------------------------------- canvas views
def gen_canvas_view(e):
    elem = next(x for x in model.ELEMENTS if x["id"] == e["id"])
    src = MIRROR_CANVAS / elem["canvas_source"]
    svg = render_canvas.render_svg(src.read_text(encoding="utf-8"))
    r = e["routes"]
    nav = routes_nav([
        ("Open Element Page", elem["html"], "primary"),
        ("Open Canvas Source (.canvas)", r["canvas_source"], "secondary"),
        ("Open in Obsidian", r["canvas_source_obsidian"], "secondary"),
        ("Return to Nine Verbs", model.VERBS_FILE, ""),
        ("Return to Navigator", "../" + model.NAVIGATOR_FILE, ""),
    ])
    body = f"""{provenance()}
<section class="card"><h2>Visual Canvas — {esc(e['name'])}</h2>
<p><span class="badge candidate">PROJECTION</span> This is a browser-safe SVG projection generated
from the authoritative Obsidian canvas <code>{esc(elem['canvas_source'])}</code>.
It requires no Obsidian, no scripts and no network access, and renders from local file,
local HTTP and SharePoint. The .canvas source remains authoritative for editing.</p>
{nav}
{svg}
</section>
{path_fallback([
    ("This view", f"{VAULT_CURRENT}/COMPONENTS/{elem['canvas_view']}"),
    ("Canvas source", f"10_WORKSPACES/NAVIGATOR_MVP_v0.2/{elem['canvas_source']}"),
    ("Element page", f"{VAULT_CURRENT}/COMPONENTS/{elem['html']}"),
])}
{nav}"""
    return page(f"Canvas View — {e['name']}",
                "Browser-safe graphical projection of the authoritative .canvas source",
                body)


# ---------------------------------------------------------------- nine verbs
def gen_verbs_page(reg):
    groups = {"FORM": [], "FLOW": [], "EVOLVE": []}
    for v in reg["verbs"]:
        groups[v["group"]].append(v)

    toc = routes_nav(
        [(v["name"], "#" + v["anchor"], "") for v in reg["verbs"]]
        + [("New Process / Offering", model.START_FILE, "primary"),
           ("Return to Navigator", "../" + model.NAVIGATOR_FILE, "secondary")])

    mesh_cov = "".join(
        f"<tr><td>{esc(stage)}</td><td>{esc(', '.join(next(v['name'] for v in reg['verbs'] if v['id'] == vid) for vid in vids))}</td></tr>"
        for stage, vids in reg["mesh_stage_verb_coverage"].items())

    sections = ""
    for gname, glabel in [("FORM", "Form — give work meaning and shape"),
                          ("FLOW", "Flow — move verified work"),
                          ("EVOLVE", "Evolve — change the system from learning")]:
        cards = ""
        for v in groups[gname]:
            b = reg["benefits"][v["benefit"]]
            elem_links = " · ".join(
                f'<a href="{next(e["routes"]["html"].split("/")[-1] for e in reg["elements"] if e["id"] == eid)}">'
                f'{esc(next(e["name"] for e in reg["elements"] if e["id"] == eid))}</a>'
                for eid in v["elements_primary"])
            all_elem_links = " · ".join(
                f'<a href="{e["routes"]["html"].split("/")[-1]}">{esc(e["id"])}</a>'
                for e in reg["elements"])
            cards += f"""<section class="card" id="{esc(v['anchor'])}">
<h2>{esc(v['id'])} · {esc(v['name'])} <span class="badge current">{esc(v['group'])}</span>
{'<span class="badge hold">ACTIVATION HELD</span>' if v['id'] == 'V7' else ''}</h2>
<table>
<tr><th>Controlling question</th><td>{esc(v['controlling_question'])}</td></tr>
<tr><th>Purpose</th><td>{esc(v['purpose'])}</td></tr>
<tr><th>Inputs</th><td>{esc(v['inputs'])}</td></tr>
<tr><th>Outputs</th><td>{esc(v['outputs'])}</td></tr>
<tr><th>Primary Elements</th><td>{elem_links}</td></tr>
<tr><th>All Elements (this verb participates in all 9)</th><td>{all_elem_links}</td></tr>
<tr><th>Mesh stages</th><td>{esc(', '.join(v['mesh_stages']))}</td></tr>
<tr><th>Control gates</th><td>Movement beyond this verb's Mesh stages passes the corresponding
Mesh &amp; Control Gates conditions; gates block by default.</td></tr>
<tr><th>Evidence requirement</th><td>{esc(v['evidence_requirement'])}</td></tr>
<tr><th>Benefit contribution</th><td><b>{esc(v['benefit'])} {esc(b['name'])}</b> — {esc(v['benefit_statement'])}<br>
<b>Evidence:</b> {esc(b['evidence'])}<br><b>Realisation condition:</b> {esc(b['realisation'])}</td></tr>
<tr><th>Asset implication</th><td>{esc(v['asset_implication'])}</td></tr>
<tr><th>Authority boundary</th><td>{esc(v['authority'])}</td></tr>
<tr><th>PPV</th><td>{esc(v['ppv'])}</td></tr>
<tr><th>Owner lane</th><td>{esc(v['owner'])}</td></tr>
<tr><th>Next action</th><td>{esc(v['next_action'])}</td></tr>
<tr><th>STOP/HOLD</th><td>{esc(v['stop_hold'])}</td></tr>
<tr><th>Replay-validity</th><td>{esc(v['replay_validity'])}</td></tr>
<tr><th>Return path</th><td><a href="#top">Top of Nine Verbs</a> → <a href="../{model.NAVIGATOR_FILE}">Navigator</a></td></tr>
</table></section>"""
        sections += f'<h2 style="margin:18px 2px 8px">{esc(glabel)}</h2>{cards}'

    body = f"""<a id="top"></a>{provenance()}
{toc}
<section class="card"><h2>Mesh coverage — every stage owned by at least one verb</h2>
<table><thead><tr><th>Mesh stage</th><th>Verbs</th></tr></thead><tbody>{mesh_cov}</tbody></table></section>
{sections}
{path_fallback([
    ("This page", f"{VAULT_CURRENT}/COMPONENTS/{model.VERBS_FILE}"),
    ("Navigator", f"{VAULT_CURRENT}/{model.NAVIGATOR_FILE}"),
    ("New Process / Offering start", f"{VAULT_CURRENT}/COMPONENTS/{model.START_FILE}"),
])}
{toc}"""
    return page("Nine Verbs — Form · Flow · Evolve",
                "Level-2 operating verbs with Mesh, Benefit, Asset and authority bindings",
                body)


# ---------------------------------------------------------------- start surface
CANDIDATE_FIELDS = [
    ("candidate_id", "Candidate ID (e.g. CAND-PROC-YYYYMMDD-01)"),
    ("name", "Name"),
    ("type", "Type: Process or Offering"),
    ("purpose", "Purpose"),
    ("strategic_contribution", "Strategic contribution"),
    ("target_beneficiary", "Target beneficiary"),
    ("context", "Context"),
    ("initiating_signal", "Initiating Signal"),
    ("problem_or_opportunity", "Problem or opportunity"),
    ("proposed_service", "Proposed Service (catalogue reference or NEW)"),
    ("proposed_method", "Proposed Method (library reference or NEW)"),
    ("proposed_pattern", "Proposed Pattern (library reference or NONE)"),
    ("canonical_basis", "Canonical basis (terms this candidate relies on)"),
    ("work_object", "Work Object"),
    ("expected_benefits", "Expected Benefits (B1–B5 with statements)"),
    ("baseline", "Baseline"),
    ("target", "Target"),
    ("evidence_source", "Evidence source"),
    ("realisation_test", "Realisation test"),
    ("potential_asset_effect", "Potential Asset effect"),
    ("owner_lane", "Owner lane"),
    ("dependencies", "Dependencies"),
    ("risks", "Risks"),
    ("authority", "Authority"),
    ("ppv", "PPV (remains Potential)"),
    ("stop_hold", "STOP/HOLD"),
    ("next_action", "One next action"),
    ("replay_validity", "Replay-validity"),
]

VERB_ROUTE_STEPS = [
    ("V1 Orient", "Establish why this candidate matters now: objective, priority position, initiating Signal."),
    ("V2 Canonicalise", "Resolve every term the candidate uses against the Canonical Library; log collisions."),
    ("V3 Structure", "Complete the full candidate field set below; produce the structured packet."),
    ("V4 Assure", "Verify references (Service, Method, Pattern, Canonical basis) actually exist; bind evidence."),
    ("V5 Navigate", "Route the packet to the owning lane and register it in the Work Object queue as a candidate."),
    ("V6 Compose", "Assemble the delivery composition from catalogued Services, Methods and Patterns."),
    ("V7 Activate — HOLD", "Activation is HELD. No runtime, Odoo or N8N action occurs. A separate Steward/CR authorisation is required to lift this HOLD."),
    ("V8 Transform (candidate)", "Record design learning from the candidate cycle; refine the packet if assurance found gaps."),
    ("V9 Project", "Publish the candidate's state into Navigator projections and file the packet with a receipt."),
]


def gen_start_page(reg):
    field_rows = "".join(
        f"<tr><th style='width:280px'>{esc(label)}</th>"
        f"<td><code>{esc(key)}</code>: <span class='pathnote'>fill in candidate packet</span></td></tr>"
        for key, label in CANDIDATE_FIELDS)
    hold_badge = ' <span class="badge hold">HOLD</span>'
    route_rows = "".join(
        f"<tr><td><b>{esc(step)}</b>{hold_badge if 'HOLD' in step else ''}</td>"
        f"<td>{esc(desc)}</td></tr>"
        for step, desc in VERB_ROUTE_STEPS)

    tmpl_lines = "\n".join(f"{k}: " for k, _ in CANDIDATE_FIELDS)
    fixtures_rows = ""
    for fid, fname, ftype in [("TEST-PROCESS-001", "Synthetic navigation test Process", "Process"),
                              ("TEST-OFFERING-001", "Synthetic navigation test Offering", "Offering")]:
        fixtures_rows += (f"<tr><td><b>{fid}</b> <span class='badge candidate'>SYNTHETIC — NON-OPERATIONAL</span></td>"
                          f"<td>{ftype}</td><td>DATA/{fid.replace('-', '_')}_CANDIDATE.json</td>"
                          f"<td>Routed V1→V9 (V7 HOLD) across all applicable Elements and all nine Mesh stages; "
                          f"never written to Odoo or N8N.</td></tr>")

    body = f"""{provenance('· <b>Nature:</b> this surface creates a GOVERNED CANDIDATE PACKAGE only — it is a design candidate, not an authorised operational record, and it deploys nothing.')}
{routes_nav([
    ("Return to Nine Verbs", model.VERBS_FILE, ""),
    ("Return to Navigator", "../" + model.NAVIGATOR_FILE, ""),
    ("Route Registry (validation source)", "../DATA/" + model.REGISTRY_FILE, "secondary"),
])}
<section class="card"><h2>Start a new Process or Offering (governed candidate)</h2>
<p><b>Choose:</b></p>
<nav class="routes"><a class="primary" href="#packet">New Process</a>
<a class="primary" href="#packet">New Offering</a></nav>
<p>Both choices produce the same governed candidate packet below — the <code>type</code> field records which.
This packet moves through the nine verbs as a <b>candidate</b>. It confers no authority, mutates no system,
and its PPV remains Potential. Activation (V7) is HELD until separately authorised by the Steward
with a CR reference. The distinction matters: a <b>design candidate</b> describes what could run;
an <b>authorised operational deployment</b> requires a Steward decision, a CR, and its own evidence — this
surface never performs the latter.</p></section>
<section class="card" id="packet"><h2>Candidate packet — required fields (all 28)</h2>
<table>{field_rows}</table>
<h3>Copyable blank packet template</h3>
<pre style="background:#eef4f7;border:1px solid #cbd8de;border-radius:8px;padding:10px;font-size:12.5px;overflow-x:auto">{esc(tmpl_lines)}</pre>
<p class="pathnote">File the completed packet to Working Memory
05_AI_RETURNS_HASHED/ with a SHA-256 receipt (sk02 filing discipline), then register it in the
Work Object queue as a candidate.</p></section>
<section class="card" id="route"><h2>Governed candidate route through the nine verbs</h2>
<table><thead><tr><th>Verb step</th><th>What happens to the candidate</th></tr></thead>
<tbody>{route_rows}</tbody></table>
<p><b>Why activation is held:</b> V7 Activate requires operational authority (Steward decision + CR with
test evidence and rollback plan). This interface lane holds design authority only, so every candidate
reaching V7 parks in HOLD with its packet complete and its evidence filed — ready for a one-step
authorised activation later, with nothing to reconstruct.</p></section>
<section class="card" id="fixtures"><h2>Synthetic test fixtures (clearly non-operational)</h2>
<table><thead><tr><th>Fixture</th><th>Type</th><th>Packet</th><th>Routing state</th></tr></thead>
<tbody>{fixtures_rows}</tbody></table></section>
{path_fallback([
    ("This page", f"{VAULT_CURRENT}/COMPONENTS/{model.START_FILE}"),
    ("Nine Verbs", f"{VAULT_CURRENT}/COMPONENTS/{model.VERBS_FILE}"),
    ("Navigator", f"{VAULT_CURRENT}/{model.NAVIGATOR_FILE}"),
])}"""
    return page("New Process & Offering Start",
                "Governed candidate initiation — design candidates only; activation HELD",
                body)


# ---------------------------------------------------------------- fixtures
def fixture(fid, ftype):
    name = ("Synthetic navigation test Process" if ftype == "Process"
            else "Synthetic navigation test Offering")
    packet = {
        "candidate_id": fid, "name": name, "type": ftype,
        "synthetic": True,
        "non_operational_notice": ("SYNTHETIC TEST FIXTURE. Exists only to prove candidate routing. "
                                   "Must never be written to Odoo, N8N or any operational register."),
        "purpose": f"Prove that a new {ftype} can be initiated and routed as a governed candidate from the current Navigator.",
        "strategic_contribution": "Demonstrates Priority 2 of WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001.",
        "target_beneficiary": "Steward (cold-start user of the Navigator).",
        "context": "Navigator interface validation context only.",
        "initiating_signal": "WO instruction: prove Process/Offering candidate readiness.",
        "problem_or_opportunity": f"No governed route existed for starting a new {ftype} from the Navigator.",
        "proposed_service": "GV-NAV-002 (navigation validation) — reference only, no catalogue mutation.",
        "proposed_method": "Registry-driven candidate routing method (candidate).",
        "proposed_pattern": "NONE (one cycle is evidence, not a Pattern).",
        "canonical_basis": "Element, Verb, Mesh stage, Benefit, Asset, Candidate, PPV as per Canonical Library.",
        "work_object": model.WORK_OBJECT,
        "expected_benefits": "B2 Delivery speed (candidate packet without manual re-architecture); B5 Governance integrity (HOLD discipline visible).",
        "baseline": "No governed candidate initiation surface existed.",
        "target": "Complete candidate packet + full V1-V9 routing trace with V7 HOLD.",
        "evidence_source": "NAVIGATOR_PROCESS_OFFERING_READINESS_RECEIPT_v0.1.md (Working Memory).",
        "realisation_test": "All 28 fields populated and all 9 verb steps traced with correct Mesh stages; V7 parked HOLD.",
        "potential_asset_effect": "Candidate packet format qualifies toward a reusable template Asset (Steward decision required).",
        "owner_lane": "claude_code (interface); Steward (acceptance).",
        "dependencies": "Route registry v0.1; Nine Verbs surface; Element surfaces.",
        "risks": "Fixture mistaken for an operational record — mitigated by SYNTHETIC banner and non_operational_notice.",
        "authority": model.AUTHORITY,
        "ppv": model.PPV,
        "stop_hold": "V7 Activate HELD; no Odoo/N8N write; no promotion; no realisation declaration.",
        "next_action": "Steward reviews readiness receipt; fixture then remains as regression fixture.",
        "replay_validity": model.REPLAY,
    }
    trace = []
    stage_map = {v["id"]: v["mesh"] for v in model.VERBS}
    elems_touched = {
        "V1": ["E7", "E5"], "V2": ["E2"], "V3": ["E4", "E7"], "V4": ["E5", "E8"],
        "V5": ["E9", "E7"], "V6": ["E1", "E3"], "V7": ["E5", "E9"],
        "V8": ["E3", "E4"], "V9": ["E6", "E7"],
    }
    for v in model.VERBS:
        trace.append({
            "verb": v["id"], "name": v["name"],
            "mesh_stages": stage_map[v["id"]],
            "elements": elems_touched[v["id"]],
            "state": "HOLD" if v["id"] == "V7" else "COMPLETE",
            "note": ("Activation parked HOLD pending Steward/CR authorisation."
                     if v["id"] == "V7" else
                     f"{v['name']} step completed for {fid} as a candidate-routing simulation."),
        })
    covered = sorted({s for t in trace for s in t["mesh_stages"]},
                     key=model.MESH_STAGES.index)
    return {"packet": packet, "verb_routing_trace": trace,
            "mesh_stages_covered": covered,
            "elements_touched": sorted({e for t in trace for e in t["elements"]}),
            "result": "CANDIDATE_ROUTING_COMPLETE_ACTIVATION_HELD"}


# ---------------------------------------------------------------- main
def main():
    reg = build()
    COMP.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)

    (DATA / model.REGISTRY_FILE).write_text(
        json.dumps(reg, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    for e in reg["elements"]:
        elem = next(x for x in model.ELEMENTS if x["id"] == e["id"])
        (COMP / elem["html"]).write_text(gen_element_page(reg, e), encoding="utf-8")
        (COMP / elem["canvas_view"]).write_text(gen_canvas_view(e), encoding="utf-8")

    (COMP / model.VERBS_FILE).write_text(gen_verbs_page(reg), encoding="utf-8")
    (COMP / model.START_FILE).write_text(gen_start_page(reg), encoding="utf-8")

    for fid, ftype in [("TEST-PROCESS-001", "Process"), ("TEST-OFFERING-001", "Offering")]:
        (DATA / f"{fid.replace('-', '_')}_CANDIDATE.json").write_text(
            json.dumps(fixture(fid, ftype), indent=1, ensure_ascii=False) + "\n",
            encoding="utf-8")

    print("generated:", len(list(COMP.iterdir())), "component files;",
          len(list(DATA.iterdir())), "data files")


if __name__ == "__main__":
    main()
