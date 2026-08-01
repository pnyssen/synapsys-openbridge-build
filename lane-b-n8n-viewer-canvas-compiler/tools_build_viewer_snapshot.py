"""
Builds fixtures/n8n_viewer_snapshot.json — the one data file viewer/n8n_viewer.py
renders. Reuses the same WORKFLOWS/D007_NODES/D007_EDGES captured in
tools_build_live_fixtures.py (same live capture, same session) so the viewer
and the compiled canvases never disagree about the underlying facts.

Executions and the security-surface summary come from two more live captures
this session:
  - mcp__synapsys-n8n-readonly-code__list_executions(workflow_id=7L5tLWOPTeqRzw3r)
  - the D007 workflow validation return already filed in Working Memory:
    05_AI_RETURNS_HASHED/WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001/
    NAVIGATOR_MVP_CLAUDE_CODE_D007_WORKFLOW_VALIDATION_RETURN_v0.1.md
"""
import json
import pathlib

import tools_build_live_fixtures as live

OUT = pathlib.Path(__file__).resolve().parent / "fixtures" / "n8n_viewer_snapshot.json"
SNAPSHOT = live.SNAPSHOT

snapshot = {
    "snapshot": SNAPSHOT,
    "source": "mcp__synapsys-n8n-readonly-code__{list_workflows,get_workflow,list_executions} — live SynapSys N8N instance",
    "evidence": "LIVE_VERIFIED",
    "work_object_id": "WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001",
    "wave": "W-NAV-INT-MVP-20260802-01",
    "ppv": "Potential",
    "authority": "Read-only viewer; no N8N mutation call made to build this snapshot",
    "workflows": [
        {
            "id": o["id"],
            "name": o["label"],
            "lifecycle_state": o["lifecycle_state"],
            "group": o["group"],
            "detail": o["detail"],
        }
        for o in live.n8n_topology_overview["objects"]
    ],
    "workflow_detail": {
        "id": "7L5tLWOPTeqRzw3r",
        "name": "D007 — Navigator Static Adoption Production",
        "active": True,
        "versionCounter": 4,
        "trigger_path": "POST /webhook/d007-navigator-static-adoption-prod-8a21c4",
        "nodes": live.d007_workflow_topology["objects"],
        "edges": live.D007_EDGES,
    },
    "executions": [
        {
            "id": "1392",
            "workflowId": "7L5tLWOPTeqRzw3r",
            "status": "success",
            "mode": "webhook",
            "startedAt": "2026-08-01T14:21:23.044Z",
            "stoppedAt": "2026-08-01T14:21:28.490Z",
            "note": "legitimate adoption run; all 6 verification gates passed; 65/65 files uploaded",
        },
        {
            "id": "1393",
            "workflowId": "7L5tLWOPTeqRzw3r",
            "status": "error",
            "mode": "webhook",
            "startedAt": "2026-08-01T14:49:50.736Z",
            "stoppedAt": "2026-08-01T14:49:50.748Z",
            "note": "replay/retry attempt correctly rejected (ROOT_HASH_DRIFT gate fires once the root pointer has already changed) — fails safe, not a defect",
        },
    ],
    "security": {
        "summary": (
            "Node-by-node review confirms an exact-match request allowlist, dual authority check "
            "(hash + required substring), destination-empty precondition, root-hash-drift concurrency "
            "guard, path-traversal rejection, and exact-count upload assertions — all read directly "
            "from the live workflow JSON, not assumed."
        ),
        "findings": [
            "GAP: the trigger webhook (node p01) has no transport-level authentication (no header-auth/basic-auth credential) — "
            "the only gate is exact-value matching against fields including payload/authority SHA-256, which are filed openly "
            "in Working Memory receipts. Recommended fix: add N8N header-auth or basic-auth to the webhook trigger node.",
            "OBSERVATION: the workflow is single-use by construction (hardcoded authority_sha256/payload_sha256/payload_size/"
            "expected root hash) — safe-refuses rather than misfires on any future v0.3 adoption, but its generic name could "
            "invite a mistaken 'reusable' assumption.",
            "OBSERVATION: no automated cleanup on a mid-upload partial failure — fails safe (blocks retry via the "
            "destination-empty precondition) rather than fails dangerous.",
        ],
        "validation_return": "05_AI_RETURNS_HASHED/WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001/NAVIGATOR_MVP_CLAUDE_CODE_D007_WORKFLOW_VALIDATION_RETURN_v0.1.md",
        "verdict": "PASS_WITH_CONDITIONS",
    },
    "receipts": [
        {"name": "Adoption receipt", "path": "Obsidian/10_WORKSPACES/NAVIGATOR_MVP_v0.2/../.../NAVIGATOR_MVP_STATIC_OBSIDIAN_ADOPTION_RECEIPT_v0.2.1.md", "note": "filed by execution 1392; workspace_files=62, rollback_files=3"},
        {"name": "D007 — Working Memory Static Release & Obsidian Adoption", "path": "U0DhJ3bqad1wZ1rc", "note": "superseded_by v2 (KepYeU9sRGGVej9M)"},
        {"name": "D007 — Working Memory Static Release & Obsidian Adoption v2", "path": "KepYeU9sRGGVej9M", "note": "superseded_by v3 (cRSti9FpTZ998FKu)"},
        {"name": "D007 — Working Memory Static Release & Obsidian Adoption v3", "path": "cRSti9FpTZ998FKu", "note": "superseded_by FINAL (lCYsb4MMKkpEBKeq)"},
        {"name": "D007 — Working Memory Static Release & Obsidian Adoption FINAL", "path": "lCYsb4MMKkpEBKeq", "note": "superseded_by production cutover (7L5tLWOPTeqRzw3r)"},
        {"name": "W1 - ITC Opportunity Intake v3.1.2", "path": "EhCDmEgWQuqHvNQt", "note": "RETIRED per CHG-2026-444, superseded_by rFiQbaLGVSqNHxzJ (per its own self-declared name)"},
        {"name": "W7 — ITC Exception Handling v2 (archived copy)", "path": "iKG5vp2Grpt2qNT2", "note": "isArchived=true, superseded_by the active KpjCoiFNrjTNbbat of the same name"},
    ],
}

if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(snapshot, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    print(f"wrote {OUT}")
