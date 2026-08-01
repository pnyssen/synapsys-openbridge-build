#!/usr/bin/env python3
"""
Read-only N8N viewer. Renders one static HTML report from a snapshot JSON
file captured via the live synapsys-n8n-readonly-code MCP tools (never from
this script directly — the viewer itself makes no N8N calls, has no
credential, and cannot mutate anything; it only formats what a snapshot file
already contains).

Sections match the dispatch's N8N viewer requirements: overview (identity/
state/version, triggers, target systems for every workflow), a single-
workflow topology (D007), an execution trace (recent executions incl. the
failed replay), a security/authority surface (webhook auth gap + credential
scopes), and a return-to-Navigator link. All facts are labelled with their
source and snapshot timestamp so nothing here can be mistaken for live state
without a fresh capture.

Presentation rule (NAVIGATOR_PRESENTATION_AND_CONTROL_SURFACE_STANDARD_v0.1,
item 6): explicit white html/body background, dark text, no dark-mode CSS.
This is a temporary specimen, not the current Navigator control surface —
the page says so and links back to Navigator Home.
"""
from __future__ import annotations

import html
import json
import pathlib
import sys
import urllib.parse

SNAPSHOT_PATH = pathlib.Path(__file__).resolve().parent.parent / "fixtures" / "n8n_viewer_snapshot.json"
OUT_PATH = pathlib.Path(__file__).resolve().parent.parent / "generated" / "N8N_VIEWER.html"

# CORRECTION v0.1 (2026-08-01): the original RETURN_ROUTE was two path segments
# joined by " -> " (a leftover from how the compiler's plain-text canvas node
# formats a route for human reading) and was reused verbatim as an <a href="...">
# value below — producing an invalid link containing a literal arrow and a space.
# Fixed two ways: (1) ROUTE_PATH is now a single clean WM-relative path, matching
# tools_build_live_fixtures.RETURN_ROUTE exactly (same primary-interface route
# applied to the canvases' metadata/return nodes, per the correction); (2) the
# HTML anchors use ROUTE_HREF, a stable absolute SharePoint URL *derived* from
# ROUTE_PATH (not a second hand-typed duplicate), built the same way sp_write's
# own webUrl responses are shaped (".../Shared%20Documents/SynapSys-Control/
# 11_WORKING_MEMORY/..."), so the two never drift apart again. Verified live via
# sp_list(Obsidian/00_SYSTEM/NAVIGATOR_SUPPORT/CURRENT) immediately before this
# correction: SYNAPSYS_NAVIGATOR_MVP_ARCHITECTURE_v1.2.html exists.
ROUTE_PATH = "Obsidian/00_SYSTEM/NAVIGATOR_SUPPORT/CURRENT/SYNAPSYS_NAVIGATOR_MVP_ARCHITECTURE_v1.2.html"
_SP_WM_BASE = "https://synapsysgroup.sharepoint.com/sites/SynapSys/Shared%20Documents/SynapSys-Control/11_WORKING_MEMORY"
ROUTE_HREF = _SP_WM_BASE + "/" + urllib.parse.quote(ROUTE_PATH)

CSS = """
html, body { background: #ffffff !important; color: #111111 !important; font-family: -apple-system, Segoe UI, Helvetica, Arial, sans-serif; margin: 0; padding: 0; }
.wrap { max-width: 1100px; margin: 0 auto; padding: 24px 28px 64px; }
h1, h2, h3 { color: #111111; }
h1 { font-size: 22px; border-bottom: 2px solid #333; padding-bottom: 8px; }
h2 { font-size: 17px; margin-top: 36px; border-bottom: 1px solid #ccc; padding-bottom: 4px; }
.banner { background: #fff8e1; border: 1px solid #d8b400; color: #5a4600; padding: 10px 14px; border-radius: 4px; font-size: 13px; margin-bottom: 18px; }
table { border-collapse: collapse; width: 100%; margin: 10px 0 22px; font-size: 13px; }
th, td { border: 1px solid #ddd; padding: 6px 8px; text-align: left; vertical-align: top; }
th { background: #f2f2f2; color: #111; }
tr:nth-child(even) { background: #fafafa; }
.tag { display: inline-block; padding: 1px 7px; border-radius: 10px; font-size: 11px; font-weight: 600; color: #fff; }
.tag-active { background: #2e7d32; }
.tag-held { background: #b8860b; }
.tag-superseded { background: #6a1b9a; }
.tag-retired { background: #6a1b9a; }
.tag-failed { background: #c62828; }
.tag-success { background: #2e7d32; }
.tag-error { background: #c62828; }
code { background: #f2f2f2; padding: 1px 5px; border-radius: 3px; font-size: 12px; }
footer { margin-top: 40px; padding-top: 12px; border-top: 1px solid #ccc; font-size: 12px; color: #444; }
a { color: #0645ad; }
"""

LIFECYCLE_TAG = {
    "active": "tag-active",
    "held": "tag-held",
    "superseded": "tag-superseded",
    "retired": "tag-retired",
    "failed": "tag-failed",
}


def esc(s) -> str:
    return html.escape(str(s), quote=True)


def tag(state: str) -> str:
    cls = LIFECYCLE_TAG.get(state, "tag-held")
    return f'<span class="tag {cls}">{esc(state)}</span>'


def render_overview(snapshot: dict) -> str:
    rows = []
    for wf in snapshot["workflows"]:
        rows.append(
            "<tr>"
            f"<td><code>{esc(wf['id'])}</code></td>"
            f"<td>{esc(wf['name'])}</td>"
            f"<td>{tag(wf['lifecycle_state'])}</td>"
            f"<td>{esc(wf['group'])}</td>"
            f"<td>{esc(wf['detail'])}</td>"
            "</tr>"
        )
    return (
        "<h2>Overview — all workflows (live, read-only)</h2>"
        f"<p>Source: {esc(snapshot['source'])} &middot; snapshot: <code>{esc(snapshot['snapshot'])}</code></p>"
        "<table><tr><th>ID</th><th>Name</th><th>State</th><th>Group</th><th>Detail</th></tr>"
        + "".join(rows)
        + "</table>"
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
        status_cls = "tag-success" if e["status"] == "success" else "tag-error"
        rows.append(
            "<tr>"
            f"<td><code>{esc(e['id'])}</code></td>"
            f"<td><code>{esc(e['workflowId'])}</code></td>"
            f"<td><span class='tag {status_cls}'>{esc(e['status'])}</span></td>"
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
<html><head><meta charset="utf-8"><title>N8N Viewer (candidate, read-only) — Lane B</title>
<style>{CSS}</style></head>
<body><div class="wrap">
<div class="banner">This is a temporary candidate specimen. It is NOT the current Navigator control surface.
Return to <a href="{esc(ROUTE_HREF)}">Navigator Home / current delivery</a>. Read-only: no workflow create,
update, activate, deactivate, or credential-bind call was made to produce or by this page.</div>
<h1>N8N Viewer — candidate (read-only)</h1>
<p>Snapshot: <code>{esc(snapshot['snapshot'])}</code> &middot; Source: {esc(snapshot['source'])} &middot;
Evidence: <strong>{esc(snapshot['evidence'])}</strong></p>
{''.join(sections)}
<footer>Work Object <code>{esc(snapshot['work_object_id'])}</code> &middot; Wave <code>{esc(snapshot['wave'])}</code>
&middot; PPV: {esc(snapshot['ppv'])} &middot; Authority: {esc(snapshot['authority'])}
&middot; Return: <a href="{esc(ROUTE_HREF)}">{esc(ROUTE_PATH)}</a></footer>
</div></body></html>
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
