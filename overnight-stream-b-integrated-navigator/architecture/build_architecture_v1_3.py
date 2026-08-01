#!/usr/bin/env python3
"""
Derives the candidate Architecture v1.3 shell from the v1.2 reference
capture via a fixed, deterministic set of string substitutions — not a
hand-authored rewrite. Every substitution is applied exactly once against a
known original substring; the script raises if an expected substring is
missing (fail closed on template drift), so this cannot silently produce a
divergent shell if v1.2 changes shape.

This candidate:
  - keeps every existing tab/panel/section from v1.2 (Current Priority stays
    the default panel; Home/Architecture, Nine Verbs, Wave, Form/Flow/Evolve,
    Services, Canonical/Assets/Spine, Contexts, Evidence/MVP Readiness are
    all unchanged in structure);
  - never claims to be "implemented" or "current" anywhere (the one place
    v1.2 says `class="state implemented"` for its own version row is
    replaced with an explicit CANDIDATE state, never re-used for this file);
  - carries a temporary-candidate banner + explicit return route back to the
    real current v1.2, per the same convention used in the N8N viewer and
    the SCVS specimens;
  - adds one new tab, "Integrated Candidate (Overnight)", presenting what
    THIS build produced (15 candidate canvases, 11 candidate profiles, the
    SCVS-integrated N8N viewer) as plain text-linked WM paths — no iframe to
    another file this HTML's eventual host may not be able to resolve, and
    no claim that any of it is implemented/promoted;
  - does not create a second Home, dashboard, or wave-control page — it is
    one shell tab added to the SAME architecture page, not a new surface.
"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW_V12_PATH = pathlib.Path(__file__).resolve().parent / "architecture_v1_2_raw_capture.html"
OUT_PATH = ROOT / "generated" / "SYNAPSYS_NAVIGATOR_MVP_ARCHITECTURE_v1.3_CANDIDATE.html"

V13_ROUTE_PATH = (
    "05_AI_RETURNS_HASHED/WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001/"
    "WAVE_INTEGRATED_NAVIGATOR_MVP_20260802/OVERNIGHT_STREAM_B_OUTPUT_v0.1/"
    "SYNAPSYS_NAVIGATOR_MVP_ARCHITECTURE_v1.3_CANDIDATE.html"
)
V12_STABLE_ROUTE = (
    "https://synapsysgroup.sharepoint.com/sites/SynapSys/Shared%20Documents/SynapSys-Control/"
    "11_WORKING_MEMORY/Obsidian/00_SYSTEM/NAVIGATOR_SUPPORT/CURRENT/"
    "SYNAPSYS_NAVIGATOR_MVP_ARCHITECTURE_v1.2.html"
)
BUILD_SNAPSHOT = "2026-08-01T16:48:19Z"


def _replace_once(html: str, old: str, new: str) -> str:
    count = html.count(old)
    if count != 1:
        raise ValueError(f"expected exactly 1 occurrence of substring (found {count}): {old[:80]!r}...")
    return html.replace(old, new, 1)


NEW_TAB_BUTTON = (
    '<button class="tab" role="tab" aria-selected="false" aria-controls="overnight" '
    'data-panel="overnight">Integrated Candidate (Overnight)</button>\n'
)

OVERNIGHT_PANEL = """
<section id="overnight" role="tabpanel" tabindex="0" class="panel"><div class="card">
<h2>Overnight Stream B — Integrated Candidate (this build)</h2>
<p class="muted">CANDIDATE ONLY — nothing on this panel is implemented or promoted. Produced by combining the consumed
Lane B deterministic Canvas compiler, the consumed Lane C SCVS v0.2.1 visual standard, this Architecture v1.2 shell,
the accepted Canvas suite and current read-only N8N/Odoo evidence, per
<code>OVERNIGHT_STREAM_B_CLAUDE_CODE_INTEGRATED_COMPILER_DISPATCH_v0.1.md</code>
(SHA-256 <code>6bb0415d2faa2b512b5d72d85025b03e186f580ad9205917ba736bf6447c60ac</code>, verified before execution).</p>
<div class="grid3">
<div class="plane"><b>15 candidate canvases</b>Every accepted canvas (01–15) regenerated through the one SCVS-integrated
compiler. Originals at <code>Obsidian/10_WORKSPACES/NAVIGATOR_MVP_v0.2/*.canvas</code> are UNCHANGED.</div>
<div class="plane"><b>11 candidate profiles</b>Lane B's enterprise/PSA/3x3x3/nine-verbs/Mesh/Signal-to-Asset/
Service-Pattern-Method-Canonical/Work-Object-queue/N8N-topology/N8N-workflow-detail/Odoo-menu profiles, re-derived
with SCVS chip-line grammar and this candidate's return route.</div>
<div class="plane"><b>N8N viewer (SCVS-integrated)</b>Same live-sourced facts as Lane B's corrected viewer, re-rendered
with SCVS lifecycle borders, chip lines and STOP/HOLD framing for the known webhook-auth gap.</div>
</div>
<div class="notice"><b>Filed at:</b> <code>05_AI_RETURNS_HASHED/WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001/
WAVE_INTEGRATED_NAVIGATOR_MVP_20260802/OVERNIGHT_STREAM_B_OUTPUT_v0.1/</code> — Working Memory only. Nothing here
touches this Architecture v1.2 file, the accepted canvas suite, Odoo, or N8N.</div>
<div class="notice"><b>Stream A substitution boundary:</b> 8 of the 11 profiles and all Odoo-family content beyond the
Govern menu subtree remain on explicitly labelled fixtures or adapted-canvas evidence — never presented as live —
because Stream A (Codex) has not returned (state <code>TOOL_BLOCKED / HELD_WM_TO_CODEX_TRANSPORT</code>, verified
against <code>NAVIGATOR_INTEGRATED_MVP_DISPATCH_MANIFEST_v0.7.md</code> this session). The <code>StreamAAdapter</code>
contract is built and ready to receive Stream A's real payload without redesigning any of the above.</div>
</div></section>
"""


def build() -> str:
    html = RAW_V12_PATH.read_text(encoding="utf-8")
    # strip the build-input-only leading HTML comment before templating (not part of v1.2 or v1.3)
    if html.startswith("<!--"):
        html = html[html.index("-->") + 3:].lstrip("\n")

    html = _replace_once(
        html,
        "<title>SynapSys Navigator MVP Architecture v1.2</title>",
        "<title>SynapSys Navigator MVP Architecture v1.3 — CANDIDATE, not current</title>",
    )
    html = _replace_once(
        html,
        "<header class=\"top\"><h1>SynapSys Navigator MVP Architecture v1.2</h1>"
        "<p>Primary Steward interface: architecture, current priority, governed work, wave entry and "
        "evidence in one stable surface. Context: CTX-SS.</p></header>",
        "<header class=\"top\"><h1>SynapSys Navigator MVP Architecture v1.3 — CANDIDATE</h1>"
        "<p>CANDIDATE shell only, not the current Steward interface. Preserves the same architecture, tabs and "
        "governed-work structure as the current v1.2 interface. Context: CTX-SS.</p></header>",
    )
    banner = (
        '<div style="background:#fff4d6;border-left:6px solid #a56c00;padding:12px 20px;font-weight:600;'
        'color:#18202a">TEMPORARY CANDIDATE — this is NOT the current Navigator control surface. Current Steward '
        f'control surface: <a href="{V12_STABLE_ROUTE}">SYNAPSYS_NAVIGATOR_MVP_ARCHITECTURE_v1.2.html</a> '
        "(unchanged by this build). This candidate's own filed location: "
        f'<code>{V13_ROUTE_PATH}</code></div>\n'
    )
    html = _replace_once(html, '<a class="skip" href="#main">Skip to main content</a>\n',
                          '<a class="skip" href="#main">Skip to main content</a>\n' + banner)

    # The one place v1.2 marks itself "implemented" for its own version row — v1.3 must never claim this.
    html = _replace_once(
        html,
        '<div class="row"><span>Primary interface</span><span class="state implemented">Architecture v1.2</span></div>',
        '<div class="row"><span>Primary interface</span><span class="state">Architecture v1.2 (current, unchanged) '
        '&middot; this file: v1.3 CANDIDATE, not current</span></div>',
    )
    html = _replace_once(
        html,
        '<div class="row"><span>Last refreshed</span><span class="state">2026-08-02 02:23 AEST</span></div>',
        '<div class="row"><span>Last refreshed</span><span class="state">2026-08-02 02:23 AEST '
        f'(v1.2, unchanged) &middot; this candidate built {BUILD_SNAPSHOT}</span></div>',
    )

    html = _replace_once(
        html,
        '<div class="verdict">Current priority: establish verified WM-to-Codex transport for Stream A</div>'
        '<p class="muted">Lanes B and C are consumed as the current integration basis. Stream A is the single '
        'remaining blocker and stays held until a verified runtime fetches, hash-checks, mounts and reads the exact '
        'Working Memory bundle.</p>',
        '<div class="verdict">Current priority (unchanged by this candidate): establish verified WM-to-Codex '
        'transport for Stream A</div><p class="muted">Lanes B and C are consumed as the current integration basis. '
        'Stream A is the single remaining blocker and stays held until a verified runtime fetches, hash-checks, '
        'mounts and reads the exact Working Memory bundle. This candidate (Overnight Stream B) extends B\'s '
        'compiler/viewer into an integrated candidate set while A remains held — see the new tab below.</p>',
    )

    html = _replace_once(
        html,
        '<button class="tab" role="tab" aria-selected="false" aria-controls="readiness" '
        'data-panel="readiness">Evidence / MVP Readiness</button>\n</nav>',
        '<button class="tab" role="tab" aria-selected="false" aria-controls="readiness" '
        'data-panel="readiness">Evidence / MVP Readiness</button>\n' + NEW_TAB_BUTTON + '</nav>',
    )

    html = _replace_once(
        html,
        '<div class="footer">Static MVP interface. No Odoo, N8N, schema, ACL, credential, PPV or canon mutation '
        'route. Primary interface refreshed 2026-08-02. Lane C v0.2.1 is consumed. Stream A remains transport-held '
        'and Lane B remains filing-reconciliation-held. Current Priority remains the active situational-awareness '
        'panel.</div>\n</main>',
        OVERNIGHT_PANEL +
        '<div class="footer">CANDIDATE shell — not the current Navigator. No Odoo, N8N, schema, ACL, credential, '
        'PPV or canon mutation route. Current interface remains Architecture v1.2, unchanged by this build. Stream A '
        'remains transport-held. This candidate\'s Integrated Candidate (Overnight) tab reflects Overnight Stream '
        f'B, built {BUILD_SNAPSHOT}.</div>\n</main>',
    )

    # The one relative link v1.2 carries only makes sense from inside the Obsidian
    # vault where v1.2 lives. This candidate is filed to Working Memory only, so a
    # relative "../../../10_WORKSPACES/..." link here would resolve to nowhere
    # (an ambiguous/broken route) — replace with the equivalent stable SharePoint URL.
    v13_current_delivery_href = (
        "https://synapsysgroup.sharepoint.com/sites/SynapSys/Shared%20Documents/SynapSys-Control/"
        "11_WORKING_MEMORY/Obsidian/10_WORKSPACES/NAVIGATOR_MVP_v0.2/CURRENT_DELIVERY.md"
    )
    html = _replace_once(
        html,
        '<a class="btn alt" href="../../../10_WORKSPACES/NAVIGATOR_MVP_v0.2/CURRENT_DELIVERY.md">'
        "Open detailed current delivery</a>",
        f'<a class="btn alt" href="{v13_current_delivery_href}">Open detailed current delivery (stable path)</a>',
    )

    return html


def main() -> int:
    html = build()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(html, encoding="utf-8")
    print(f"wrote {OUT_PATH} ({len(html.encode('utf-8'))} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
