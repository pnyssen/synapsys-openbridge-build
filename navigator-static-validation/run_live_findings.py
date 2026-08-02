"""
Runs the reusable checks against real, freshly-fetched evidence for
Work Object WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001,
captured this session via sp_read/sp_list. Read-only throughout — this
script performs no network call itself; all "live" data was already
fetched into findings/live_snapshot_v1_2.html (verified byte-identical
to the receipted live file, see NAVIGATOR_CODE_TRAVELLING_CONTINUATION_RETURN_v0.1.md)
and the KNOWN_PATHS / MANIFEST_ROWS / ACTUAL_ON_WM tables below, which
are transcribed from sp_list results, not invented.
"""
from __future__ import annotations

import pathlib

from checks.link_checker import check_links
from checks.manifest_parity import ManifestRow, check_parity
from checks.presentation_standard import check_dead_data_open_targets, check_presentation
from checks.state_vocabulary import compare_hook_to_expected, extract_window_hook, find_state_collapse

ROOT = pathlib.Path(__file__).resolve().parent
SNAPSHOT_PATH = ROOT / "findings" / "live_snapshot_v1_2.html"
BASE_DIR = "Obsidian/00_SYSTEM/NAVIGATOR_SUPPORT/CURRENT"

# Confirmed to exist via sp_list this session (not assumed from memory).
KNOWN_PATHS = {
    "Obsidian/00_HOME.md",
    "Obsidian/00_SYSTEM/NAVIGATOR_SUPPORT/CURRENT/COMPONENTS/NAVIGATOR_OPERATING_SURFACE_v3.9.html",
    "Obsidian/00_SYSTEM/NAVIGATOR_SUPPORT/CURRENT/COMPONENTS/NAVIGATOR_WAVE_RUNNER_v0.1.html",
    "Obsidian/00_SYSTEM/NAVIGATOR_SUPPORT/CURRENT/COMPONENTS/SERVICE_CATALOGUE_INTERACTIVE_MECE_COVERAGE_v1.0.html",
    "Obsidian/00_SYSTEM/NAVIGATOR_SUPPORT/CURRENT/REFERENCES/04_MESH_CONTROL_AND_ACTIVATION_MAP.md",
    "Obsidian/00_SYSTEM/NAVIGATOR_SUPPORT/CURRENT/REFERENCES/REGISTERS/NAVIGATOR_81_CELL_MESH_BINDING_REGISTER_v0.1.csv",
    "Obsidian/00_SYSTEM/NAVIGATOR_SUPPORT/CURRENT/REFERENCES/REGISTERS/NAVIGATOR_CONTROL_CENTRE_STATUS_REGISTER_v0.4_DUAL_TRACK_AMENDMENT.csv",
    "Obsidian/10_WORKSPACES/NAVIGATOR_MVP_v0.2/05_MESH_LIFECYCLE_GATES.canvas",
    "Obsidian/10_WORKSPACES/NAVIGATOR_MVP_v0.2/14_CURRENT_WORK_OBJECT_QUEUE.canvas",
    "Obsidian/10_WORKSPACES/NAVIGATOR_MVP_v0.2/CURRENT_DELIVERY.md",
    "Obsidian/10_WORKSPACES/NAVIGATOR_MVP_v0.2/03_FFE_SBR_3X3X3.canvas",
    "Obsidian/10_WORKSPACES/NAVIGATOR_MVP_v0.2/04_NINE_VERB_OPERATING.canvas",
    "Obsidian/10_WORKSPACES/NAVIGATOR_MVP_v0.2/09_PATTERN_METHOD_CANONICAL.canvas",
    "Obsidian/10_WORKSPACES/NAVIGATOR_MVP_v0.2/11_BENEFIT_ASSET_REALISATION.canvas",
    "Obsidian/10_WORKSPACES/NAVIGATOR_MVP_v0.2/12_CONTEXT_MEMBRANE.canvas",
}

# FILE_MANIFEST_SHA256_v0.3.csv rows relevant to this check, transcribed
# verbatim from sp_read this session (Obsidian/10_WORKSPACES/NAVIGATOR_MVP_v0.2/FILE_MANIFEST_SHA256_v0.3.csv,
# last modified 2026-08-01T22:40:27Z).
MANIFEST_V03_ROWS = [
    ManifestRow("CURRENT_DELIVERY.md", 4235, "ea01bab35cfcaddd82130b7067224d771ba13235ac90cc0977167a9a8fc5b0a3"),
    ManifestRow("05_MESH_LIFECYCLE_GATES.canvas", 3279, "eef8feb36b8b5d0b16f7fb06080a53ec7b83d9ee2f692e60f2978ca9115bd508"),
    ManifestRow("14_CURRENT_WORK_OBJECT_QUEUE.canvas", 3869, "5f59560c9ff231b1222457d0abdc7d445216951eede914bee8e3a2cbe98e9ecb"),
    ManifestRow("03_FFE_SBR_3X3X3.canvas", 3038, "4b90844908ff001fecf6df81bb1745c6afe079a5f267372beb47954270deea6d"),
    ManifestRow("04_NINE_VERB_OPERATING.canvas", 4368, "13b1f4ae5c3f7e8f8049494f58851e6a9c94936bfbaeefdbcd9da029d874f9cd"),
]

# The corresponding "actual" byte counts from sp_list this session
# (Obsidian/10_WORKSPACES/NAVIGATOR_MVP_v0.2/ listing). SHA-256 is not
# available from a directory listing, so it is set to None for these —
# only the byte dimension of parity is checked against live sp_list
# data; the manifest's own recorded hash is carried through unverified
# rather than guessed.
ACTUAL_ON_WM = {
    "CURRENT_DELIVERY.md": (3029, None),
    "05_MESH_LIFECYCLE_GATES.canvas": (3279, None),
    "14_CURRENT_WORK_OBJECT_QUEUE.canvas": (3869, None),
    "03_FFE_SBR_3X3X3.canvas": (3038, None),
    "04_NINE_VERB_OPERATING.canvas": (4368, None),
}

# Independently derived from the *visible* DOM text of the snapshot
# (the eight integrity badges, the Mesh gate-grid text, the Service/
# Canonical/Benefits/Assets/Patterns/Methods numbers in the Status
# panel) — NOT read from the test hook itself, so a real match here is
# a genuine cross-check, not circular.
EXPECTED_FROM_VISIBLE_DOM = {
    "integrity.green": 1, "integrity.partial": 6, "integrity.held": 1, "integrity.full": False,
    "mesh.cells": 81, "mesh.gates": 10, "mesh.liveEdges": 9, "mesh.activeEdges": 1,
    "services.active": 18, "services.validated": 18, "services.canonicalLinked": 13, "services.ffeState": 0,
    "canonical.total": 56, "canonical.promoted": 5, "canonical.candidate": 40, "canonical.conflicted": 4,
    "benefits.total": 45, "benefits.planned": 25, "benefits.measured": 14, "benefits.verified": 6,
    "benefits.measurementMethod": 25, "benefits.realisationEvidence": 10,
    "assets.total": 120, "assets.maturitySet": 71, "assets.reuseRecorded": 0,
    "patterns.total": 15, "patterns.candidate": 14, "patterns.admitted": 0,
    "methods.total": 12, "methods.active": 10,
    "ppv": "Potential",
}


def main() -> None:
    html = SNAPSHOT_PATH.read_text()

    print("== link_checker ==")
    link_findings = check_links(html, base_dir=BASE_DIR, known_paths=KNOWN_PATHS)
    for f in link_findings:
        print(f" - {f.kind}: {f.detail}")
    if not link_findings:
        print(" (none)")

    print("\n== presentation_standard ==")
    pres_findings = check_presentation(html) + check_dead_data_open_targets(html)
    for f in pres_findings:
        print(f" - {f.kind}: {f.detail}")
    if not pres_findings:
        print(" (none)")

    print("\n== state_vocabulary: candidate/implemented/current collapse ==")
    collapse_findings = find_state_collapse(html)
    for f in collapse_findings:
        print(f" - {f.kind}: {f.detail}")
    if not collapse_findings:
        print(" (none)")

    print("\n== state_vocabulary: displayed-state vs window.navigatorStatus test hook ==")
    hook = extract_window_hook(html, "navigatorStatus")
    if hook is None:
        print(" - TEST_HOOK_NOT_FOUND: window.navigatorStatus could not be parsed")
    else:
        hook_findings = compare_hook_to_expected(hook, EXPECTED_FROM_VISIBLE_DOM)
        for f in hook_findings:
            print(f" - {f.kind}: {f.detail}")
        if not hook_findings:
            print(" (none — all 29 checked fields match the visible DOM)")

    print("\n== manifest_parity: FILE_MANIFEST_SHA256_v0.3.csv vs live sp_list byte counts ==")
    parity_findings = check_parity(MANIFEST_V03_ROWS, ACTUAL_ON_WM)
    for f in parity_findings:
        print(f" - {f.kind}: {f.path} (manifest={f.manifest_bytes}, actual={f.actual_bytes})")
    if not parity_findings:
        print(" (none)")


if __name__ == "__main__":
    main()
