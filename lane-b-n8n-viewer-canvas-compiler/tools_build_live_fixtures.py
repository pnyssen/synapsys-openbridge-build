"""
Builds fixtures/n8n_topology_overview.json, fixtures/d007_workflow_topology.json,
and fixtures/odoo_menu_govern.json from data captured directly via live
`mcp__synapsys-n8n-readonly-code__*` and `mcp__synapsys-odoo-readonly-code__*`
tool calls in this session (see LANE_B return packet for exact call/timestamp
provenance). This script is the reproducible record of how raw tool output
was mapped into the graph_schema.json adapter contract shape — re-run it
against a fresh capture to refresh the fixtures; do not hand-edit the
generated JSON files directly.

Every classification below (group, lifecycle_state, supersession edge) is
derived from a field that was actually present in the live response
(active/isArchived flags, name text, updatedAt/createdAt ordering, or the
workflow's own self-declared "[RETIRED — superseded by X]" annotation) — none
of it is invented.
"""
import json
import pathlib

SNAPSHOT = "2026-08-02T02:15:00Z"  # this session's live-read window (UTC)
OUT = pathlib.Path(__file__).resolve().parent / "fixtures"

# --- raw capture: mcp__synapsys-n8n-readonly-code__list_workflows(limit=50) ---
WORKFLOWS = [
    {"id": "2CNI1RusyxvmOneX", "name": "W6 — Partner Authority Validation (D005 Agreement Check)", "active": True, "isArchived": False},
    {"id": "3K9itPD5Ehuw83en", "name": "W4 — Benefits Tracking KPI Update (Scheduled/Event)", "active": True, "isArchived": False},
    {"id": "3OXOZg6QRJlaBPVJ", "name": "W10 — Change Request Lifecycle (Webhook + Scheduled)", "active": True, "isArchived": False},
    {"id": "5GoMaZUrYmBaoJg0", "name": "W5 — Compliance Routing (Regulated Programme Trigger)", "active": True, "isArchived": False},
    {"id": "7L5tLWOPTeqRzw3r", "name": "D007 — Navigator Static Adoption Production", "active": True, "isArchived": False},
    {"id": "7N5mIIiAbGWoFsS2", "name": "WM_TO_GEMINI_SUBSTRATE_BUNDLE", "active": False, "isArchived": False},
    {"id": "8zrvRkMXpCqk5HqS", "name": "verify · dispatch validation & gate (W15-CR1)", "active": True, "isArchived": False},
    {"id": "96UoiUGM6VGfdK8M", "name": "JQ003 CGPT Odoo Read-Only Facade", "active": False, "isArchived": False},
    {"id": "9YZ6CxMSunZukz2D", "name": "MCP Hub", "active": False, "isArchived": True},
    {"id": "9jK9XPNLo6sgJOyQ", "name": "W16 — SIAS Asset Spine Creation (Webhook from Asset Register)", "active": True, "isArchived": False},
    {"id": "AUnXWh43u0d4QSSW", "name": "QIDIP-RuleE-LinkageIntegrity Trigger", "active": True, "isArchived": False},
    {"id": "CmGOUh4shpeI6PM0", "name": "H1_CGPT_N8N_Action_Facade_v2 copy", "active": False, "isArchived": False},
    {"id": "EhCDmEgWQuqHvNQt", "name": "W1 - ITC Opportunity Intake v3.1.2 [RETIRED — superseded by rFiQbaLGVSqNHxzJ, CHG-2026-444]", "active": False, "isArchived": False},
    {"id": "GbSaoOuhfc2bZugL", "name": "W2 — Programme Activation (Odoo CRM → Programme Register)", "active": True, "isArchived": False},
    {"id": "KepYeU9sRGGVej9M", "name": "D007 — Working Memory Static Release & Obsidian Adoption v2", "active": False, "isArchived": False},
    {"id": "KpjCoiFNrjTNbbat", "name": "W7 — ITC Exception Handling v2", "active": True, "isArchived": False},
    {"id": "L3uMe5mNd1UZVY1V", "name": "BIND_TOOL_VALIDATION_THROWAWAY_DO_NOT_ACTIVATE", "active": False, "isArchived": False},
    {"id": "L6ZKFeA4eoKeTebx", "name": "MCP_CREATE_WORKFLOW_CAPABILITY_TEST_DO_NOT_ACTIVATE", "active": False, "isArchived": False},
    {"id": "LUcJA7dPgr5VxsGa", "name": "W13 — Service Linkage Enforcement (Weekly Scan)", "active": True, "isArchived": False},
    {"id": "MQT2Nt7G2dZcQ7xI", "name": "W12 — Configuration Register Sync (Scheduled/Webhook)", "active": True, "isArchived": False},
    {"id": "Mn0mBl3whA0xgVB3", "name": "W14 — Intelligence Signal Processing (Webhook)", "active": True, "isArchived": False},
    {"id": "O99dGEBtgmph7qWb", "name": "NAV_OBS_FND_04_ZLIB_PROBE_v0.1", "active": False, "isArchived": False},
    {"id": "OfE27WyEcHTOP6eb", "name": "W11 — Release Validation & Deployment (Webhook)", "active": True, "isArchived": False},
    {"id": "Q7dCfsw0t9DAbhFD", "name": "route · dispatch routing (W15-CR2)", "active": True, "isArchived": False},
    {"id": "RpZLHVrPu2WrGf3h", "name": "W17 - AI-to-AI Structured Handoff Workflow", "active": False, "isArchived": False},
    {"id": "SYTkLSvDiHIHINnB", "name": "W3 — Benefit Event Capture (Milestone → Benefits Register)", "active": True, "isArchived": False},
    {"id": "U0DhJ3bqad1wZ1rc", "name": "D007 — Working Memory Static Release & Obsidian Adoption", "active": False, "isArchived": False},
    {"id": "Yv1GKWf11RF4I2MH", "name": "W8 — Exception Escalation (To D007 Platform Lead)", "active": True, "isArchived": False},
    {"id": "aRwXxftzB2K1JhPP", "name": "sandbox_workflow", "active": False, "isArchived": False},
    {"id": "aUX0Ca07HSgzsdSJ", "name": "W9 — Service Catalogue Validation (Webhook)", "active": True, "isArchived": False},
    {"id": "aqDmGinCTRutOr4Q", "name": "H1_CGPT_N8N_Action_Facade_v2", "active": True, "isArchived": False},
    {"id": "bcLCmdjwVl1wUpU8", "name": "H1_CGPT_N8N_Action_Facade", "active": False, "isArchived": False},
    {"id": "cRSti9FpTZ998FKu", "name": "D007 — Working Memory Static Release & Obsidian Adoption v3", "active": False, "isArchived": False},
    {"id": "cum6pn5hVGmp8Prd", "name": "DISPATCHER-V4 — Live Executor Pattern (10-Component Membrane)", "active": True, "isArchived": False},
    {"id": "iKG5vp2Grpt2qNT2", "name": "W7 — ITC Exception Handling v2", "active": False, "isArchived": True},
    {"id": "lCYsb4MMKkpEBKeq", "name": "D007 — Working Memory Static Release & Obsidian Adoption FINAL", "active": False, "isArchived": False},
    {"id": "nnLmPirbJO8FD7Ow", "name": "sense · dispatch read path (CR-4)", "active": True, "isArchived": False},
    {"id": "nsOD1Khga9xwNUBX", "name": "JQ003 Authenticated Self-Test — INACTIVE", "active": False, "isArchived": False},
    {"id": "oUvOkSi0lvBkoUoH", "name": "W-portal-intake", "active": True, "isArchived": False},
    {"id": "rFiQbaLGVSqNHxzJ", "name": "W1 — Opportunity Intake (AVA Portal → Odoo CRM)", "active": True, "isArchived": False},
    {"id": "te2vI1VSDXb24fFA", "name": "W-CODEX-READINESS-PING", "active": False, "isArchived": False},
    {"id": "u036lOwnO8KGPZRa", "name": "STG-WM-WRITE-GATEWAY", "active": False, "isArchived": False},
    {"id": "uO5vYklSMooXMLpF", "name": "W-lms-launch", "active": True, "isArchived": False},
    {"id": "upZOd9q78pjivkd8", "name": "W2A — Value Module Initialisation", "active": True, "isArchived": False},
    {"id": "vKnnSxKIqJR9Qix7", "name": "Test_CR-A_JSONRPC_RO_v0.1", "active": False, "isArchived": False},
]

# group classification, derived purely from the name text pattern observed above
def classify(name: str) -> str:
    if name.startswith("D007"):
        return "d007_static_release_lineage"
    if any(k in name for k in ("dispatch", "W15-CR", "CR-4", "DISPATCHER-V4")):
        return "dispatch_membrane"
    if name.startswith("H1_CGPT"):
        return "cgpt_facade"
    if name.startswith("W-portal") or name.startswith("W-lms"):
        return "portal_launch"
    if name.startswith(("W1", "W2", "W3", "W4", "W5", "W6", "W7", "W8", "W9", "W10", "W11", "W12", "W13", "W14", "W16", "W17")):
        return "core_wave_w1_w17"
    if any(k in name for k in ("THROWAWAY", "TEST", "PROBE", "sandbox", "READINESS-PING", "Self-Test")):
        return "test_and_throwaway"
    return "utility_and_infra"


def lifecycle_of(wf: dict) -> str:
    if "RETIRED" in wf["name"] or wf["isArchived"]:
        return "retired"
    if wf["id"] in {"U0DhJ3bqad1wZ1rc", "KepYeU9sRGGVej9M", "cRSti9FpTZ998FKu", "lCYsb4MMKkpEBKeq"}:
        return "superseded"
    if "THROWAWAY" in wf["name"] or "DO_NOT_ACTIVATE" in wf["name"]:
        return "held"
    if wf["active"]:
        return "active"
    return "held"


objects = []
for wf in WORKFLOWS:
    objects.append(
        {
            "id": wf["id"],
            "label": wf["name"],
            "kind": "n8n_workflow",
            "lifecycle_state": lifecycle_of(wf),
            "authority": "N8N_INSTANCE_READ_ONLY_SCOPE (owner confirmed personal-project phil@synapsys.com.au for D007 lineage only, via get_workflow)",
            "detail": f"active={wf['active']} isArchived={wf['isArchived']}",
            "group": classify(wf["name"]),
        }
    )

relationships = [
    {"id": "r_d007_v1_v2", "from": "U0DhJ3bqad1wZ1rc", "to": "KepYeU9sRGGVej9M", "verb": "superseded_by", "lifecycle_state": "superseded"},
    {"id": "r_d007_v2_v3", "from": "KepYeU9sRGGVej9M", "to": "cRSti9FpTZ998FKu", "verb": "superseded_by", "lifecycle_state": "superseded"},
    {"id": "r_d007_v3_final", "from": "cRSti9FpTZ998FKu", "to": "lCYsb4MMKkpEBKeq", "verb": "superseded_by", "lifecycle_state": "superseded"},
    {"id": "r_d007_final_prod", "from": "lCYsb4MMKkpEBKeq", "to": "7L5tLWOPTeqRzw3r", "verb": "superseded_by", "lifecycle_state": "superseded"},
    {"id": "r_w1_retired", "from": "EhCDmEgWQuqHvNQt", "to": "rFiQbaLGVSqNHxzJ", "verb": "superseded_by", "lifecycle_state": "retired"},
    {"id": "r_w7_archived", "from": "iKG5vp2Grpt2qNT2", "to": "KpjCoiFNrjTNbbat", "verb": "superseded_by", "lifecycle_state": "retired"},
]

n8n_topology_overview = {
    "view_id": "n8n_topology",
    "title": "N8N Workflow Overview — All Workflows (live)",
    "snapshot": SNAPSHOT,
    "source": "mcp__synapsys-n8n-readonly-code__list_workflows(limit=50) — live SynapSys N8N instance",
    "evidence": "LIVE_VERIFIED",
    "reality": "IMPLEMENTED — reflects the live N8N instance's workflow set at snapshot time, not a design intent",
    "ppv": "Potential — this projection does not itself promote or activate anything",
    "authority": "Read-only viewer projection; no activation/deactivation/update authority exercised",
    "return_route": "Obsidian/00_HOME.md -> NAVIGATOR_MVP_v0.2/NAVIGATOR_MVP_PRIMARY_HOME_CANDIDATE_v0.2.md",
    "objects": objects,
    "relationships": relationships,
}

# --- raw capture: mcp__synapsys-n8n-readonly-code__get_workflow(id="7L5tLWOPTeqRzw3r") ---
D007_NODES = [
    ("p01", "Webhook — Navigator Adoption", "n8n-nodes-base.webhook", "no_transport_auth_configured (see D007 validation return finding)"),
    ("p02", "Validate Request and Build Routes", "n8n-nodes-base.code", "no_credential (pure code node)"),
    ("p03", "Fetch Authority", "n8n-nodes-base.httpRequest", "credential:W18_SP_WorkingMemory_Audit_Read (read scope)"),
    ("p04", "Hash Authority", "n8n-nodes-base.crypto", "no_credential (pure code node)"),
    ("p05", "Validate Authority", "n8n-nodes-base.code", "no_credential (pure code node)"),
    ("p06", "Inspect Destination", "n8n-nodes-base.httpRequest", "credential:W18_SP_WorkingMemory_Audit_Read (read scope)"),
    ("p07", "Validate Destination", "n8n-nodes-base.code", "no_credential (pure code node)"),
    ("p08", "Fetch Current Root", "n8n-nodes-base.httpRequest", "credential:W18_SP_WorkingMemory_Audit_Read (read scope)"),
    ("p09", "Hash Current Root", "n8n-nodes-base.crypto", "no_credential (pure code node)"),
    ("p10", "Validate Current Root", "n8n-nodes-base.code", "no_credential (pure code node); enforces ROOT_HASH_DRIFT gate"),
    ("p11", "Provision Date Folder", "n8n-nodes-base.httpRequest", "credential:W17_SP_WorkingMemory_Filing_Write (write scope)"),
    ("p12", "Provision Rollback Folder", "n8n-nodes-base.httpRequest", "credential:W17_SP_WorkingMemory_Filing_Write (write scope)"),
    ("p13", "Provision Destination Folder", "n8n-nodes-base.httpRequest", "credential:W17_SP_WorkingMemory_Filing_Write (write scope)"),
    ("p14", "Validate Folder Provisioning", "n8n-nodes-base.code", "no_credential (pure code node)"),
    ("p15", "Fetch Adoption ZIP", "n8n-nodes-base.httpRequest", "credential:W18_SP_WorkingMemory_Audit_Read (read scope)"),
    ("p16", "Set ZIP Metadata", "n8n-nodes-base.code", "no_credential (pure code node)"),
    ("p17", "Hash ZIP", "n8n-nodes-base.crypto", "no_credential (pure code node)"),
    ("p18", "Validate ZIP Hash", "n8n-nodes-base.code", "no_credential (pure code node); enforces PAYLOAD_HASH_MISMATCH gate"),
    ("p19", "Decompress ZIP", "n8n-nodes-base.compression", "no_credential (pure code node)"),
    ("p20", "Split Archive Files", "n8n-nodes-base.code", "no_credential (pure code node); enforces ARCHIVE_COUNT_MISMATCH gate + path-traversal rejection"),
    ("p21", "Upload Deployment Files", "n8n-nodes-base.httpRequest", "credential:W17_SP_WorkingMemory_Filing_Write (write scope); overwrite=false"),
    ("p22", "Validate Uploads", "n8n-nodes-base.code", "no_credential (pure code node); enforces UPLOAD_COUNT_MISMATCH / UPLOAD_FAILURES gate"),
    ("p23", "Cut Over Root Pointer Last", "n8n-nodes-base.httpRequest", "credential:W17_SP_WorkingMemory_Filing_Write (write scope); overwrite=true"),
    ("p24", "Build Receipt", "n8n-nodes-base.code", "no_credential (pure code node)"),
    ("p25", "Write Receipt", "n8n-nodes-base.httpRequest", "credential:W17_SP_WorkingMemory_Filing_Write (write scope); overwrite=true"),
    ("p26", "Respond Success", "n8n-nodes-base.respondToWebhook", "no_credential (pure code node)"),
]
D007_EDGES = [
    ("p01", "p02"), ("p02", "p03"), ("p03", "p04"), ("p04", "p05"), ("p05", "p06"),
    ("p06", "p07"), ("p07", "p08"), ("p08", "p09"), ("p09", "p10"), ("p10", "p11"),
    ("p11", "p12"), ("p12", "p13"), ("p13", "p14"), ("p14", "p15"), ("p15", "p16"),
    ("p16", "p17"), ("p17", "p18"), ("p18", "p19"), ("p19", "p20"), ("p20", "p21"),
    ("p21", "p22"), ("p22", "p23"), ("p23", "p24"), ("p24", "p25"), ("p25", "p26"),
]

GATE_NODE_IDS = {"p05", "p07", "p10", "p18", "p20", "p22"}
WRITE_NODE_IDS = {"p11", "p12", "p13", "p21", "p23", "p25"}


def d007_group(node_id: str) -> str:
    if node_id == "p01":
        return "0_trigger"
    if node_id in GATE_NODE_IDS:
        return "2_verification_gate"
    if node_id in WRITE_NODE_IDS:
        return "3_write_action"
    return "1_prepare_fetch"


d007_objects = [
    {
        "id": nid,
        "label": label,
        "kind": ntype.replace("n8n-nodes-base.", ""),
        "lifecycle_state": "active",
        "authority": auth,
        "group": d007_group(nid),
    }
    for nid, label, ntype, auth in D007_NODES
]
d007_relationships = [
    {"id": f"r_{a}_{b}", "from": a, "to": b, "verb": "flows_to"} for a, b in D007_EDGES
]

d007_workflow_topology = {
    "view_id": "n8n_workflow_detail",
    "title": "D007 — Navigator Static Adoption Production (workflow 7L5tLWOPTeqRzw3r, live)",
    "snapshot": SNAPSHOT,
    "source": "mcp__synapsys-n8n-readonly-code__get_workflow(id=7L5tLWOPTeqRzw3r) — live, active=true, versionCounter=4",
    "evidence": "LIVE_VERIFIED",
    "reality": "IMPLEMENTED — active production workflow; execution 1392 succeeded 2026-08-01T14:21Z, execution 1393 errored 2026-08-01T14:49Z (replay correctly rejected by the ROOT_HASH_DRIFT gate at node p10)",
    "ppv": "Potential — this projection is read-only; no workflow mutation performed to produce it",
    "authority": "Read-only viewer projection of a workflow this lane independently validated (NAVIGATOR_MVP_CLAUDE_CODE_D007_WORKFLOW_VALIDATION_RETURN_v0.1.md, verdict PASS_WITH_CONDITIONS)",
    "return_route": "Obsidian/00_HOME.md -> NAVIGATOR_MVP_v0.2/NAVIGATOR_MVP_PRIMARY_HOME_CANDIDATE_v0.2.md",
    "objects": d007_objects,
    "relationships": d007_relationships,
}

# --- raw capture: mcp__synapsys-odoo-readonly-code__search_odoo(model="ir.ui.menu", domain=[["parent_id.name","=","Govern"]]) ---
GOVERN_MENUS = [
    (489, "Context Master", "Govern", "ir.actions.act_window,752"),
    (1009, "Change Requests", "Deliver/Govern", "ir.actions.act_window,764"),
    (1012, "Governance Decisions", "SynapSys/Value/Govern", "ir.actions.act_window,1396"),
    (498, "Service Control", "Govern", False),
    (1010, "Governance Decisions", "Deliver/Govern", "ir.actions.act_window,1396"),
    (1013, "DIM Cycles", "SynapSys/Value/Govern", "ir.actions.act_window,1403"),
    (542, "Governed Entities", "Govern", False),
    (493, "Controls & Exceptions", "Govern", False),
    (1011, "Execution Gates", "Deliver/Govern", "ir.actions.act_window,1400"),
    (1014, "Reviews", "SynapSys/Value/Govern", "ir.actions.act_window,1397"),
    (989, "Risk & Integrity (Lens 2)", "Govern", False),
    (992, "Execution Control (Lens 3)", "Govern", False),
    (1099, "DIM Events", "Govern", "ir.actions.act_window,1504"),
    (981, "Traditional Board (Lens 1)", "Govern", False),
]

odoo_objects = []
parent_groups_seen = set()
for mid, name, parent, action in GOVERN_MENUS:
    group_key = parent.replace("/", "_")
    parent_groups_seen.add((parent, group_key))
    odoo_objects.append(
        {
            "id": f"menu_{mid}",
            "label": name,
            "kind": "odoo_menu_item",
            "lifecycle_state": "active",
            "authority": "odoo_menu_visibility_group (not independently enumerated this session; menu structure only)",
            "detail": f"action={action if action else 'no_action_container_menu'}",
            "group": group_key,
        }
    )
for parent, group_key in sorted(parent_groups_seen):
    odoo_objects.append(
        {
            "id": f"parent_{group_key}",
            "label": parent,
            "kind": "odoo_menu_parent",
            "lifecycle_state": "active",
            "authority": "odoo_menu_visibility_group (not independently enumerated this session; menu structure only)",
            "group": group_key,
        }
    )

odoo_relationships = [
    {"id": f"r_menu_{mid}", "from": f"parent_{parent.replace('/', '_')}", "to": f"menu_{mid}", "verb": "contains"}
    for mid, name, parent, action in GOVERN_MENUS
]

odoo_menu_govern = {
    "view_id": "odoo_app_menu_object",
    "title": "Odoo — Govern Menu Tree (live, x_ss custom governance menus)",
    "snapshot": SNAPSHOT,
    "source": "mcp__synapsys-odoo-readonly-code__search_odoo(model=ir.ui.menu, domain=[parent_id.name=Govern]) — live SynapSys Odoo instance",
    "evidence": "LIVE_VERIFIED",
    "reality": "IMPLEMENTED — reflects live Odoo ir.ui.menu records under the Govern menu tree at snapshot time; not the full app/menu/object surface (partial, scoped to Govern for this candidate pass)",
    "ppv": "Potential — read-only projection; no Odoo record created/written/unlinked to produce it",
    "authority": "Read-only Odoo projection via synapsys-odoo-readonly-code (search_odoo only, no write tool called)",
    "return_route": "Obsidian/00_HOME.md -> NAVIGATOR_MVP_v0.2/NAVIGATOR_MVP_PRIMARY_HOME_CANDIDATE_v0.2.md",
    "objects": odoo_objects,
    "relationships": odoo_relationships,
}

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for name, data in (
        ("n8n_topology_overview", n8n_topology_overview),
        ("d007_workflow_topology", d007_workflow_topology),
        ("odoo_menu_govern", odoo_menu_govern),
    ):
        path = OUT / f"{name}.json"
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, sort_keys=True, ensure_ascii=False)
            fh.write("\n")
        print(f"wrote {path} ({len(data['objects'])} objects, {len(data['relationships'])} relationships)")
