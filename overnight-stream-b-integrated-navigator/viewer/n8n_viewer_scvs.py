#!/usr/bin/env python3
"""
SCVS-integrated read-only N8N viewer for the overnight candidate build.

Reuses the exact live-sourced snapshot data Lane B's correction return
already produced and filed (lane-b-n8n-viewer-canvas-compiler/fixtures/
n8n_viewer_snapshot.json — read here, never modified) and re-renders it with
the SCVS v0.2.1 grammar: lifecycle border-style classes, chip-line encoding
(E:/PPV:/AUTH:), source corner tags, and the STOP/HOLD frame for the known
webhook-authentication gap. No new N8N/Odoo call is made by this module —
same no-mutation boundary as Lane B's original viewer.
"""
from __future__ import annotations

import html
import json
import pathlib
import sys
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
LANE_B_ROOT = ROOT.parent / "lane-b-n8n-viewer-canvas-compiler"
SNAPSHOT_PATH = LANE_B_ROOT / "fixtures" / "n8n_viewer_snapshot.json"
OUT_PATH = ROOT / "generated" / "N8N_VIEWER_CANDIDATE.html"

BUILD_SNAPSHOT = "2026-08-01T16:48:19Z"  # this build's own real capture time, same as build_overnight_candidate.py

ROUTE_PATH = (
    "05_AI_RETURNS_HASHED/WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001/"
    "WAVE_INTEGRATED_NAVIGATOR_MVP_20260802/OVERNIGHT_STREAM_B_OUTPUT_v0.1/"
    "SYNAPSYS_NAVIGATOR_MVP_ARCHITECTURE_v1.3_CANDIDATE.html"
)
_SP_WM_BASE = "https://synapsysgroup.sharepoint.com/sites/SynapSys/Shared%20Documents/SynapSys-Control/11_WORKING_MEMORY"
ROUTE_HREF = _SP_WM_BASE + "/" + urllib.parse.quote(ROUTE_PATH)

# SCVS v0.2.1 CSS, carried over from LANE_C_SCVS_2D_SPECIMEN_v0.2.1.html /
# SET_B verbatim (same class names, same colours) so this viewer visually
# matches the consumed Lane C standard rather than inventing a parallel one.
SCVS_CSS = """
html,body{background:#ffffff;color:#18202a}
body{font-family:system-ui,-apple-system,sans-serif;margin:0;line-height:1.45}
.banner{background:#fff4d6;border-left:6px solid #a56c00;padding:12px 20px;font-weight:600}
.banner code{font-weight:400;background:#f4f6f8;padding:1px 4px}
header{padding:20px 24px;border-bottom:2px solid #17385c}
header h1{margin:0 0 6px;font-size:22px}
header p{margin:0;color:#4b5661;font-size:14px}
main{max-width:1400px;margin:auto;padding:24px}
section{margin-bottom:36px}
h2{border-bottom:1px solid #ccd2d8;padding-bottom:6px}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{border:1px solid #d5dbe1;padding:6px 8px;text-align:left;vertical-align:top}
th{background:#e9edf1}
tr.flag td{background:#fff4d6}
.card{background:#fff;border:1px solid #6b7684;border-radius:6px;padding:10px 12px;position:relative;margin-bottom:8px}
.card.lc-active{border-style:solid}
.card.lc-held{border-style:dashed}
.card.lc-candidate{border-style:dashed}
.card.lc-superseded,.card.lc-retired{border-color:#9aa7b4;color:#6b7684}
.card.lc-superseded h3,.card.lc-retired h3{text-decoration:line-through}
.card.lc-failed{border:2px solid #a52a1a}
.srctag{position:absolute;top:6px;right:8px;font-size:10px;letter-spacing:.06em;color:#4b5661;border:1px solid #9aa7b4;border-radius:3px;padding:1px 5px;background:#f4f6f8}
.chips{margin-top:6px;display:flex;flex-wrap:wrap;gap:6px}
.chip{font-size:11px;border:1px solid #6b7684;border-radius:10px;padding:2px 8px;background:#fff}
.chip.ppv-potential{border-style:dashed}
.chip.ppv-probable{background:#e9edf1}
.chip.ppv-verified{background:#17385c;color:#fff;border-color:#17385c}
.chip.warn{background:#fff4d6;border-color:#a56c00}
.controlblock{border:2px solid #17385c;border-radius:6px;padding:14px;background:#f4f6f8;font-size:13px}
.nextaction{border:2px solid #17385c;border-left:10px solid #17385c;border-radius:6px;padding:14px;background:#fff;margin-top:12px}
.nextaction h3{margin:0 0 4px}
footer{padding:20px 24px;color:#4b5661;border-top:1px solid #ccd2d8;font-size:13px}
a{color:#0645ad}
code{background:#f2f2f2;padding:1px 5px;border-radius:3px;font-size:12px}
"""

_LIFECYCLE_CLASS = {
    "active": "lc-active",
    "held": "lc-held",
    "candidate": "lc-candidate",
    "superseded": "lc-superseded",
    "retired": "lc-retired",
    "failed": "lc-failed",
}


def esc(s) -> str:
    return html.escape(str(s), quote=True)


def _chip(text: str, cls: str = "") -> str:
    return f'<span class="chip {cls}">{esc(text)}</span>'


def render_overview(snapshot: dict) -> str:
    rows = []
    for wf in snapshot["workflows"]:
        lc_class = _LIFECYCLE_CLASS.get(wf["lifecycle_state"], "lc-held")
        rows.append(
            f'<article class="card {lc_class}"><span class="srctag">N8N</span>'
            f"<h3 style='margin:0;font-size:13px'>{esc(wf['name'])}</h3>"
            f"<div class='chips'>{_chip('id: ' + wf['id'])}{_chip('BORDER: ' + wf['lifecycle_state'])}"
            f"{_chip('GROUP: ' + wf['group'])}{_chip(wf['detail'])}</div></article>"
        )
    return (
        "<h2>Overview — all workflows (live, read-only, SCVS-rendered)</h2>"
        f"<p>Source: {esc(snapshot['source'])} &middot; snapshot: <code>{esc(BUILD_SNAPSHOT)}</code> "
        f"(rebuild time; underlying facts carried unchanged from Lane B's {esc(snapshot['snapshot'])} capture, not re-fetched)</p>"
        f"<div>{''.join(rows)}</div>"
    )


def render_workflow_detail(detail: dict) -> str:
    node_rows = []
    for n in detail["nodes"]:
        node_rows.append(
            "<tr>"
            f"<td><code>{esc(n['id'])}</code></td>"
            f"<td>{esc(n['label'])}</td>"
            f"<td>{esc(n['kind'])}</td>"
            f"<td>{esc(n['group'])}</td>"
            f"<td>{esc(n['authority'])}</td>"
            "</tr>"
        )
    edge_rows = [
        f"<tr><td><code>{esc(a)}</code></td><td>&rarr;</td><td><code>{esc(b)}</code></td></tr>"
        for a, b in detail["edges"]
    ]
    return (
        f"<h2>Single-workflow topology — {esc(detail['name'])}</h2>"
        f"<p>ID: <code>{esc(detail['id'])}</code> &middot; active: {esc(detail['active'])} &middot; "
        f"versionCounter: {esc(detail['versionCounter'])} &middot; trigger: <code>{esc(detail['trigger_path'])}</code></p>"
        "<article class='card lc-failed'><span class='srctag'>N8N</span>"
        "<h3 style='margin:0;font-size:13px'>⚠ STOP/HOLD — webhook trigger (node p01)</h3>"
        "<div class='chips'>" + _chip("no transport-level authentication configured", "warn") + "</div>"
        "<p style='font-size:12px;margin:6px 0 0'>Independent validation return: "
        "<code>NAVIGATOR_MVP_CLAUDE_CODE_D007_WORKFLOW_VALIDATION_RETURN_v0.1.md</code> — verdict "
        "<strong>PASS_WITH_CONDITIONS</strong>.</p></article>"
        "<h3>Nodes / edges</h3>"
        "<table><tr><th>Node ID</th><th>Name</th><th>Type</th><th>Stage</th><th>Authority / credential</th></tr>"
        + "".join(node_rows)
        + "</table>"
        "<table><tr><th colspan='3'>Flow (fromNode &rarr; toNode)</th></tr>"
        + "".join(edge_rows)
        + "</table>"
    )


def render_executions(executions: list) -> str:
    rows = []
    for e in executions:
        lc_class = "lc-active" if e["status"] == "success" else "lc-failed"
        rows.append(
            f"<tr class='{'flag' if e['status'] != 'success' else ''}'>"
            f"<td><code>{esc(e['id'])}</code></td>"
            f"<td><code>{esc(e['workflowId'])}</code></td>"
            f"<td>{_chip(e['status'], 'ppv-verified' if e['status'] == 'success' else 'warn')}</td>"
            f"<td>{esc(e['mode'])}</td>"
            f"<td>{esc(e['startedAt'])}</td>"
            f"<td>{esc(e['stoppedAt'])}</td>"
            f"<td>{esc(e.get('note', ''))}</td>"
            "</tr>"
        )
    return (
        "<h2>Execution trace (recent, live)</h2>"
        "<table><tr><th>Exec ID</th><th>Workflow</th><th>Status</th><th>Mode</th><th>Started</th><th>Stopped</th><th>Note</th></tr>"
        + "".join(rows)
        + "</table>"
    )


def render_security(security: dict) -> str:
    findings = "".join(f"<li>{esc(f)}</li>" for f in security["findings"])
    return (
        "<h2>Security / authority surface</h2>"
        f"<p>{esc(security['summary'])}</p>"
        f"<ul>{findings}</ul>"
        f"<p>Independent validation return: <code>{esc(security['validation_return'])}</code> &mdash; verdict "
        f"<strong>{esc(security['verdict'])}</strong>.</p>"
    )


def render_receipts(receipts: list) -> str:
    rows = "".join(
        f"<tr><td>{esc(r['name'])}</td><td><code>{esc(r['path'])}</code></td><td>{esc(r['note'])}</td></tr>"
        for r in receipts
    )
    return (
        "<h2>Receipts and superseded workflows</h2>"
        "<table><tr><th>Name</th><th>Path / ID</th><th>Note</th></tr>" + rows + "</table>"
    )


def build_html(snapshot: dict) -> str:
    sections = [
        render_overview(snapshot),
        render_workflow_detail(snapshot["workflow_detail"]),
        render_executions(snapshot["executions"]),
        render_security(snapshot["security"]),
        render_receipts(snapshot["receipts"]),
    ]
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>N8N Viewer CANDIDATE (SCVS-integrated, read-only) — Overnight Stream B</title>
<style>{SCVS_CSS}</style></head>
<body>
<div class="banner">TEMPORARY CANDIDATE SPECIMEN — this is NOT the current Navigator control surface.
Current Steward control surface: <code>Obsidian/00_SYSTEM/NAVIGATOR_SUPPORT/CURRENT/SYNAPSYS_NAVIGATOR_MVP_ARCHITECTURE_v1.2.html</code>
(untouched by this build). This candidate's own return route: <a href="{esc(ROUTE_HREF)}">{esc(ROUTE_PATH)}</a>.
Read-only: no workflow create, update, activate, deactivate, or credential-bind call was made to produce or by this page.</div>
<header><h1>N8N Viewer — CANDIDATE (SCVS-integrated, read-only)</h1>
<p>Snapshot: <code>{esc(BUILD_SNAPSHOT)}</code> &middot; Source: {esc(snapshot['source'])} &middot;
Evidence: <strong>{esc(snapshot['evidence'])}</strong> &middot; SCVS v0.2.1 chip/border grammar applied</p></header>
<main>
{''.join(sections)}
<div class="nextaction"><h3>Exactly one next action</h3>
<p style="margin:0;font-size:13px">Reconcile this candidate viewer against Stream A's integration graph once returned; until then it remains a candidate, not the current viewer.</p></div>
</main>
<footer>Work Object <code>{esc(snapshot['work_object_id'])}</code> &middot; Wave <code>{esc(snapshot['wave'])}</code>
&middot; PPV: {esc(snapshot['ppv'])} &middot; Authority: {esc(snapshot['authority'])}
&middot; Return: <a href="{esc(ROUTE_HREF)}">{esc(ROUTE_PATH)}</a></footer>
</body></html>
"""


def main() -> int:
    with open(SNAPSHOT_PATH, "r", encoding="utf-8") as fh:
        snapshot = json.load(fh)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(build_html(snapshot), encoding="utf-8")
    print(f"wrote {OUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
