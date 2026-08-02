"""SynapSys Navigator L1/L2/L3 single-source model.

This module is the ONE place where Elements, Verbs, Mesh stages, Benefits,
routes and Level-3 semantics are defined. Everything else (the route
registry JSON, every generated HTML surface, and the test harness) derives
from it, so route definitions can no longer drift between files.

WO: WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001
Authority: Obsidian Navigator interface + Working Memory filing only.
PPV: Potential. No Odoo/N8N/runtime mutation is expressed or implied here.
"""

SNAPSHOT = "2026-08-03T09:00:00+10:00"
WORK_OBJECT = "WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001"
PPV = "Potential"
AUTHORITY = ("Obsidian interface + Working Memory filing only; "
             "Odoo/N8N/runtime/canon/Service/Method/Pattern/Asset/PPV mutation HELD")
OWNER_LANE = "claude_code (interface projection); Steward (acceptance)"
REPLAY = "PRESERVED"

# Vault-relative folder depths
#   Obsidian/00_SYSTEM/NAVIGATOR_SUPPORT/CURRENT/            <- navigator + index
#   Obsidian/00_SYSTEM/NAVIGATOR_SUPPORT/CURRENT/COMPONENTS/ <- element pages, canvas views, verbs
#   Obsidian/00_SYSTEM/NAVIGATOR_SUPPORT/CURRENT/DATA/       <- registry + projections
#   Obsidian/10_WORKSPACES/NAVIGATOR_MVP_v0.2/               <- .canvas sources
NAVIGATOR_FILE = "SYNAPSYS_NAVIGATOR_MVP_ARCHITECTURE_v1.5.html"
VERBS_FILE = "NAVIGATOR_NINE_VERBS_BENEFIT_ROUTE_v1.0.html"
START_FILE = "NAVIGATOR_NEW_PROCESS_AND_OFFERING_START_v1.0.html"
REGISTRY_FILE = "NAVIGATOR_L1_L2_L3_ROUTE_REGISTRY.json"
CANVAS_DIR_FROM_COMPONENTS = "../../../../10_WORKSPACES/NAVIGATOR_MVP_v0.2/"
OBSIDIAN_CANVAS_PREFIX = ("obsidian://open?vault=Obsidian&file="
                          "10_WORKSPACES%2FNAVIGATOR_MVP_v0.2%2F")

MESH_STAGES = [
    "Signal", "Interpretation", "Structuring", "Validation", "Action",
    "Observation", "Learning", "Asset Conversion", "Feedback",
]

BENEFITS = {
    "B1": {"name": "Decision clarity",
           "meaning": "The Steward can see current state, objective and next valid action without reconstruction.",
           "evidence": "Cold-start walkthrough receipt; priority projection freshness stamp.",
           "realisation": "A cold-start user reaches the correct next action from Home in under five clicks, verified by replay receipt."},
    "B2": {"name": "Delivery speed",
           "meaning": "New Processes and Offerings move from idea to governed candidate without manual re-architecture.",
           "evidence": "Candidate packet completeness check against the registry template; routing trace through the nine verbs.",
           "realisation": "A complete candidate packet is produced through the start surface with all required fields and a verb-routing trace, no manual reconstruction."},
    "B3": {"name": "Assurance confidence",
           "meaning": "Claims about state are evidence-bound; validation gates precede action.",
           "evidence": "Test-matrix results filed with SHA-256 receipts; independent re-verification entries.",
           "realisation": "All applicable automated assertions pass and are filed; disputed claims recorded as conflicts, not accepted."},
    "B4": {"name": "Asset compounding",
           "meaning": "Qualified outcomes convert into reusable Patterns, Methods and Canonical objects instead of one-off narratives.",
           "evidence": "Asset-qualification conditions recorded per candidate; Steward qualification decision reference.",
           "realisation": "An outcome is only labelled an Asset after meeting written qualification conditions under Steward authority; until then it is recorded as candidate evidence."},
    "B5": {"name": "Governance integrity",
           "meaning": "Authority boundaries, STOP/HOLD states and PPV discipline remain visible and enforced on every route.",
           "evidence": "Authority and HOLD blocks rendered on every surface; registry authority fields; held-item register.",
           "realisation": "No surface implies an unauthorised mutation; every held action is labelled HOLD with the holding authority named."},
}

ELEMENTS = [
    {
        "id": "E1", "key": "service_catalogue", "name": "Service Catalogue",
        "html": "ELEMENT_SERVICE_CATALOGUE_v1.2.html",
        "canvas_view": "CANVAS_VIEW_SERVICE_CATALOGUE_v1.0.html",
        "canvas_source": "07_SERVICE_CATALOGUE_INTEGRATED_v1.2.canvas",
        "role": "the governed register of what SynapSys offers: Services, their scoping fields, PPV state and catalogue lineage",
        "purpose": "Hold one governed, non-duplicated definition of every Service the ecosystem can offer.",
        "strategy": "Grow the catalogue only through governed candidates that pass scoping, assurance and Steward acceptance.",
        "assets": "Service definitions, scoping templates and the MECE coverage model are the reusable assets this Element accumulates.",
        "signal_in": "New Service ideas, Offering demands, coverage gaps and scoping defects arriving from any lane.",
        "interprets": "Whether a demand maps to an existing Service, a variant, or a genuine catalogue gap.",
        "structures": "Six-field scoped Service records and their MECE placement in the catalogue.",
        "validated_by": "Scoping validator checks, MECE coverage review and Steward catalogue acceptance.",
        "action": "Publish or amend catalogue entries as governed candidates; route Offering composition to Compose.",
        "observes": "Usage of Services in Offerings and the coverage gaps candidates reveal.",
        "learns": "Which scoping patterns survive assurance and which recur as defects.",
        "asset_conversion": "Stable Service definitions and scoping patterns qualify toward the Pattern and Method libraries.",
        "feedback_to": "Coverage and defect findings feed back to Orient as new Signals for the next catalogue cycle.",
    },
    {
        "id": "E2", "key": "canonical_library", "name": "Canonical Library",
        "html": "ELEMENT_CANONICAL_LIBRARY_v1.2.html",
        "canvas_view": "CANVAS_VIEW_CANONICAL_LIBRARY_v1.0.html",
        "canvas_source": "10_CANONICAL_STATE_v1.2.canvas",
        "role": "the single agreed vocabulary and object model: canonical terms, definitions and their adoption state",
        "purpose": "Keep one agreed meaning per term so lanes cannot diverge on vocabulary.",
        "strategy": "Canonicalise only after collision-checks against the existing corpus; never merge referents silently.",
        "assets": "Canonical definitions, the object index and collision-resolution records.",
        "signal_in": "New terms, contested meanings and vocabulary collisions surfaced by any artefact.",
        "interprets": "Whether a term is new, a synonym, a collision, or a candidate canonical object.",
        "structures": "Canonical entries with state (candidate/adopted/deprecated) and lineage.",
        "validated_by": "Coherence checks against the corpus and Steward adoption decisions.",
        "action": "Record candidate canonical entries; publish adopted vocabulary to all surfaces.",
        "observes": "Where artefacts drift from canonical vocabulary in practice.",
        "learns": "Which definitions hold under use and which keep producing collisions.",
        "asset_conversion": "Adopted definitions become durable Canonical objects cited by every other Element.",
        "feedback_to": "Drift observations return to Canonicalise as correction Signals.",
    },
    {
        "id": "E3", "key": "asset_pattern_library", "name": "Asset & Pattern Library",
        "html": "ELEMENT_ASSET_PATTERN_LIBRARY_v1.2.html",
        "canvas_view": "CANVAS_VIEW_ASSET_PATTERN_LIBRARY_v1.0.html",
        "canvas_source": "09_ASSET_PATTERN_LIBRARY_v1.2.canvas",
        "role": "the register of reusable Patterns and qualified Assets, with explicit qualification state",
        "purpose": "Accumulate reusable Patterns and Assets under explicit qualification discipline.",
        "strategy": "One successful cycle is evidence, not a Pattern; qualification requires repetition, written conditions and Steward authority.",
        "assets": "Qualified Patterns, Asset records and their qualification condition sets.",
        "signal_in": "Candidate patterns and asset claims arriving from completed work.",
        "interprets": "Whether a claim is narrative, candidate evidence, or meets qualification conditions.",
        "structures": "Pattern records with qualification state, conditions and lineage.",
        "validated_by": "Qualification condition checks and Steward qualification decisions.",
        "action": "Register candidates; publish qualified Patterns for reuse by Compose.",
        "observes": "Reuse outcomes: where Patterns hold, where they fail.",
        "learns": "Which qualification conditions predict successful reuse.",
        "asset_conversion": "This Element IS the conversion gate: candidates become Assets only here, under authority.",
        "feedback_to": "Failed reuse returns to Transform as a re-design Signal.",
    },
    {
        "id": "E4", "key": "method_library", "name": "Method Library",
        "html": "ELEMENT_METHOD_LIBRARY_v1.2.html",
        "canvas_view": "CANVAS_VIEW_METHOD_LIBRARY_v1.0.html",
        "canvas_source": "09B_METHOD_LIBRARY_v1.2.canvas",
        "role": "the register of governed Methods: how work is done, step by step, with authority and evidence requirements",
        "purpose": "Hold the agreed way each class of work is executed.",
        "strategy": "Methods enter as candidates from demonstrated practice and are promoted only with evidence.",
        "assets": "Method definitions, their step structures and comparison matrices.",
        "signal_in": "Demonstrated working practices, method gaps and execution defects.",
        "interprets": "Whether a practice is a one-off, a variant of an existing Method, or a candidate Method.",
        "structures": "Stepwise Method records with inputs, outputs, evidence points and authority boundaries.",
        "validated_by": "Method comparison review and assurance of demonstrated runs.",
        "action": "Register and publish Methods for routing by Navigate and use by Compose.",
        "observes": "Method adherence and deviation during delivery.",
        "learns": "Which steps are load-bearing and which are ceremony.",
        "asset_conversion": "Proven Methods qualify as reusable Assets referenced by Services and Offerings.",
        "feedback_to": "Deviations feed back to Structure as method-refinement Signals.",
    },
    {
        "id": "E5", "key": "mesh_control_gates", "name": "Mesh & Control Gates",
        "html": "ELEMENT_MESH_CONTROL_GATES_v1.2.html",
        "canvas_view": "CANVAS_VIEW_MESH_CONTROL_GATES_v1.0.html",
        "canvas_source": "05_MESH_LIFECYCLE_GATES_v1.2.canvas",
        "role": "the operating Mesh itself: the nine-stage loop and the control gates that govern movement between stages",
        "purpose": "Make every piece of work traverse Signal through Feedback under visible gates.",
        "strategy": "Gates block by default; movement requires evidence and named authority, never assumption.",
        "assets": "Gate definitions, gate-decision records and the Mesh stage map.",
        "signal_in": "All work entering the ecosystem: every Signal crosses this Element first.",
        "interprets": "Which Mesh stage a work item is genuinely at, versus where it claims to be.",
        "structures": "Stage assignments and gate conditions for each work object.",
        "validated_by": "Gate condition checks; Assure verbs run here before any Action gate opens.",
        "action": "Open or hold gates; route work to the verb that owns its next stage.",
        "observes": "Gate outcomes, blocked items and recurring gate failures.",
        "learns": "Which gate conditions actually predict safe progression.",
        "asset_conversion": "Stable gate designs qualify as governance Patterns.",
        "feedback_to": "Gate statistics return to Orient to reprioritise systemic fixes.",
    },
    {
        "id": "E6", "key": "benefits_assets", "name": "Benefits & Assets",
        "html": "ELEMENT_BENEFITS_ASSETS_v1.2.html",
        "canvas_view": "CANVAS_VIEW_BENEFITS_ASSETS_v1.0.html",
        "canvas_source": "11_BENEFIT_ASSET_REALISATION_v1.2.canvas",
        "role": "the Benefit model and realisation ledger: what value each verb and Element claims, with evidence and realisation state",
        "purpose": "Bind every claimed Benefit to evidence and an explicit realisation condition.",
        "strategy": "Technical output is never labelled Benefit realisation; realisation is declared only when its written condition is met under authority.",
        "assets": "The Benefit model (B1-B5), realisation conditions and the realisation ledger.",
        "signal_in": "Benefit claims and realisation evidence arriving from completed verb cycles.",
        "interprets": "Whether a claim is output, contribution, or realised Benefit.",
        "structures": "Benefit entries with baseline, target, evidence source and realisation test.",
        "validated_by": "Evidence-binding checks; realisation declarations remain HELD to Steward authority.",
        "action": "Record contributions; stage realisation candidates for Steward declaration.",
        "observes": "Whether declared conditions are approached over successive cycles.",
        "learns": "Which Benefit definitions are measurable and which need redesign.",
        "asset_conversion": "Realised, repeatable Benefits with stable evidence chains qualify toward Assets.",
        "feedback_to": "Realisation gaps feed back to Project as objective-setting Signals.",
    },
    {
        "id": "E7", "key": "work_object_queue", "name": "Current Work Object & Queue",
        "html": "ELEMENT_CURRENT_WORK_OBJECT_QUEUE_v1.2.html",
        "canvas_view": "CANVAS_VIEW_CURRENT_WORK_OBJECT_QUEUE_v1.0.html",
        "canvas_source": "14_CURRENT_WORK_OBJECT_QUEUE_v1.2.canvas",
        "role": "the single current Work Object, the delivery queue behind it, and stream state including completed Stream A",
        "purpose": "Keep exactly one current Work Object visible with its queue, so focus cannot silently fork.",
        "strategy": "Work enters the queue as scoped objects; streams complete and are retired as evidence, never silently reactivated.",
        "assets": "Work Object contracts, queue projections and stream completion records.",
        "signal_in": "New work requests, priority changes and stream completion events.",
        "interprets": "Whether new work belongs to the current object, the queue, or a held stream.",
        "structures": "The 15-field Work Object contract and ordered queue entries.",
        "validated_by": "Queue-state consistency checks; Stream A remains ASSURED_STREAM_A_COMPLETE, never re-queued.",
        "action": "Advance the current Work Object; admit or defer queue entries.",
        "observes": "Throughput, blocked items and queue ageing.",
        "learns": "Which queue disciplines keep exactly-one-current true in practice.",
        "asset_conversion": "The Work Object contract format itself is a qualified reusable Asset.",
        "feedback_to": "Completion evidence returns to Benefits & Assets and to Orient for the next objective.",
    },
    {
        "id": "E8", "key": "context_membrane", "name": "Context & Membrane",
        "html": "ELEMENT_CONTEXT_MEMBRANE_v1.2.html",
        "canvas_view": "CANVAS_VIEW_CONTEXT_MEMBRANE_v1.0.html",
        "canvas_source": "12_CONTEXT_MEMBRANE_v1.2.canvas",
        "role": "the boundary layer: which Context work runs in, what crosses between contexts, and what the membrane holds out",
        "purpose": "Keep every work item bound to its correct Context and stop unauthorised crossings.",
        "strategy": "Everything crossing the membrane is inspected, labelled and receipted; nothing crosses by assumption.",
        "assets": "Context definitions, membrane rules and crossing receipts.",
        "signal_in": "Inbound artefacts, claims and instructions from other lanes and external sources.",
        "interprets": "Which Context an item belongs to and whether it may cross.",
        "structures": "Context labels, crossing records and quarantine states.",
        "validated_by": "Identity restatement and hash verification of crossing artefacts.",
        "action": "Admit, quarantine or reject crossings; bind admitted items to Context.",
        "observes": "Crossing volumes and quarantine outcomes.",
        "learns": "Which sources and shapes of claim need hardened verification.",
        "asset_conversion": "Stable membrane rules qualify as governance Patterns.",
        "feedback_to": "Verification failures return to Assure as systemic Signals.",
    },
    {
        "id": "E9", "key": "agent_runtime_routing", "name": "Agent & Runtime Routing",
        "html": "ELEMENT_AGENT_RUNTIME_ROUTING_v1.2.html",
        "canvas_view": "CANVAS_VIEW_AGENT_RUNTIME_ROUTING_v1.0.html",
        "canvas_source": "13_AI_AGENT_ROUTING_v1.2.canvas",
        "role": "the lane and runtime map: which AI lane or runtime executes which class of work, under which demonstrated capability",
        "purpose": "Route each task to the lane whose demonstrated capability matches it.",
        "strategy": "Route by demonstrated capability, never assumption; runtime activation stays HELD to its own authority.",
        "assets": "The lane capability register and routing decision records.",
        "signal_in": "Work needing execution, lane capability changes and routing failures.",
        "interprets": "Which lane/runtime is capable and authorised for a task.",
        "structures": "Routing entries binding task class to lane with authority notes.",
        "validated_by": "Capability evidence checks; no route asserts access a lane has not demonstrated.",
        "action": "Dispatch work to lanes; record handoffs with packets.",
        "observes": "Handoff outcomes, lane failures and capability drift.",
        "learns": "Where routing assumptions failed and which need re-verification.",
        "asset_conversion": "Proven routing rules qualify toward the Method library.",
        "feedback_to": "Routing outcomes return to Orient and the Work Object queue.",
    },
]

VERBS = [
    {"id": "V1", "key": "orient", "name": "Orient", "group": "FORM",
     "question": "Where are we, and what matters now?",
     "purpose": "Establish current state, objective and priorities before any structuring or action.",
     "inputs": "Fresh state projections, priority model, inbound Signals, completed-work evidence.",
     "outputs": "A current objective, top-five priorities and the next valid action.",
     "mesh": ["Signal", "Interpretation"],
     "benefit": "B1",
     "asset_implication": "Priority and state projections become reusable orientation surfaces.",
     "elements_primary": ["E7", "E5"],
     "evidence": "Priority projection freshness stamp and source reference on every orientation surface."},
    {"id": "V2", "key": "canonicalise", "name": "Canonicalise", "group": "FORM",
     "question": "What does this mean, in the one agreed vocabulary?",
     "purpose": "Resolve every term and object to its single canonical meaning before structure is built on it.",
     "inputs": "New terms, contested meanings, collision reports.",
     "outputs": "Canonical entries with state and lineage; collision resolutions.",
     "mesh": ["Interpretation", "Structuring"],
     "benefit": "B5",
     "asset_implication": "Adopted canonical definitions are durable Assets cited everywhere.",
     "elements_primary": ["E2"],
     "evidence": "Coherence-check record against the corpus for every new canonical entry."},
    {"id": "V3", "key": "structure", "name": "Structure", "group": "FORM",
     "question": "What shape must this take to be governable?",
     "purpose": "Give work its governed shape: records, contracts, schemas, queues and packets.",
     "inputs": "Canonicalised meaning, method requirements, contract templates.",
     "outputs": "Structured records and packets that gates can evaluate.",
     "mesh": ["Structuring"],
     "benefit": "B2",
     "asset_implication": "Contract and packet formats become reusable structural Assets.",
     "elements_primary": ["E4", "E7"],
     "evidence": "Structured record validates against its registry template."},
    {"id": "V4", "key": "assure", "name": "Assure", "group": "FLOW",
     "question": "Is this claim true, and how do we know?",
     "purpose": "Independently verify claims, recompute hashes, and bind every assertion to evidence before gates open.",
     "inputs": "Claims, artefacts, hashes, test results.",
     "outputs": "Verified evidence records, or recorded conflicts where verification fails.",
     "mesh": ["Validation"],
     "benefit": "B3",
     "asset_implication": "Test harnesses and verification receipts are reusable assurance Assets.",
     "elements_primary": ["E5", "E8"],
     "evidence": "Independent recomputation record (hash, test output) filed with receipt."},
    {"id": "V5", "key": "navigate", "name": "Navigate", "group": "FLOW",
     "question": "What is the route from here to the objective?",
     "purpose": "Move through the system without losing context: route work and people to the right surface, lane and next action.",
     "inputs": "Route registry, lane capability map, current Work Object.",
     "outputs": "Working routes, drill-downs and returns; correct lane dispatch.",
     "mesh": ["Action", "Observation"],
     "benefit": "B1",
     "asset_implication": "The route registry itself is the navigational Asset.",
     "elements_primary": ["E9", "E7"],
     "evidence": "Route resolution test results across all registered routes."},
    {"id": "V6", "key": "compose", "name": "Compose", "group": "FLOW",
     "question": "What do we assemble from governed parts?",
     "purpose": "Assemble Offerings, packets and deliverables from catalogued Services, Methods and Patterns.",
     "inputs": "Service Catalogue entries, qualified Patterns, Methods, candidate fields.",
     "outputs": "Composed candidates: Offerings, Processes, packets.",
     "mesh": ["Action"],
     "benefit": "B2",
     "asset_implication": "Compositions that repeat successfully become Pattern candidates.",
     "elements_primary": ["E1", "E3"],
     "evidence": "Composition trace listing every governed part used, with registry references."},
    {"id": "V7", "key": "activate", "name": "Activate", "group": "EVOLVE",
     "question": "May this run, and under whose authority?",
     "purpose": "Move a governed candidate into operation - only under explicit authority; activation is HELD in this cycle.",
     "inputs": "Assured candidates, authority decisions, CR references.",
     "outputs": "Activation records where authorised; explicit HOLD records otherwise.",
     "mesh": ["Action", "Observation"],
     "benefit": "B5",
     "asset_implication": "Activation checklists become governance Assets.",
     "elements_primary": ["E5", "E9"],
     "evidence": "Named authority reference (CR / Steward decision) on every activation; HOLD label otherwise."},
    {"id": "V8", "key": "transform", "name": "Transform", "group": "EVOLVE",
     "question": "What did we learn, and what should change shape?",
     "purpose": "Convert observation into structural change: refine Methods, redesign gates, evolve candidates.",
     "inputs": "Observations, defect logs, realisation gaps.",
     "outputs": "Revised structures and qualified learning records.",
     "mesh": ["Learning", "Asset Conversion"],
     "benefit": "B4",
     "asset_implication": "This verb feeds the Asset conversion gate: learning becomes candidate Assets.",
     "elements_primary": ["E3", "E4"],
     "evidence": "Before/after structural diff plus the observation records that motivated it."},
    {"id": "V9", "key": "project", "name": "Project", "group": "EVOLVE",
     "question": "What does the system say about itself, forward?",
     "purpose": "Publish current-state and forward projections so every lane and the Steward see the same reality.",
     "inputs": "State data, realisation ledger, queue state.",
     "outputs": "Projections: Navigator surfaces, state JSON, receipts, forward objectives.",
     "mesh": ["Feedback", "Observation"],
     "benefit": "B1",
     "asset_implication": "Projection formats and surfaces are reusable Assets.",
     "elements_primary": ["E6", "E7"],
     "evidence": "Every projection carries source, snapshot timestamp and freshness state."},
]

AXIS_A = ["Purpose", "Strategy", "Assets"]
AXIS_B = ["Form", "Flow", "Evolve"]
AXIS_C = ["Signal", "Benefits", "Realisation"]

# Verb group -> element field carrying that mode's behaviour
_AXIS_B_FIELD = {
    "Form": ("structures", "how this Element is given governed shape"),
    "Flow": ("action", "how work moves through this Element"),
    "Evolve": ("learns", "how this Element changes shape from learning"),
}
_AXIS_A_FIELD = {
    "Purpose": "purpose", "Strategy": "strategy", "Assets": "assets",
}
_AXIS_C_FIELD = {
    "Signal": ("signal_in", "the incoming Signal lens"),
    "Benefits": ("interprets", "the Benefit-contribution lens"),
    "Realisation": ("validated_by", "the Realisation-condition lens"),
}

_AXIS_C_BENEFIT = {"Signal": "B1", "Benefits": "B3", "Realisation": "B4"}
_AXIS_B_VERBS = {"Form": ["V1", "V2", "V3"], "Flow": ["V4", "V5", "V6"],
                 "Evolve": ["V7", "V8", "V9"]}


def l3_cells(elem):
    """Generate the 27 Level-3 positions for one Element."""
    cells = []
    for a in AXIS_A:
        for b in AXIS_B:
            for c in AXIS_C:
                tid = f"L3-{elem['id']}-{a[:3].upper()}-{b[:3].upper()}-{c[:3].upper()}"
                a_text = elem[_AXIS_A_FIELD[a]]
                b_field, b_gloss = _AXIS_B_FIELD[b]
                c_field, c_gloss = _AXIS_C_FIELD[c]
                benefit_id = _AXIS_C_BENEFIT[c]
                benefit = BENEFITS[benefit_id]
                cells.append({
                    "trace_id": tid,
                    "element": elem["id"],
                    "axis_a": a, "axis_b": b, "axis_c": c,
                    "applicable": True,
                    "decision_served": (
                        f"How the {a} of {elem['name']} is expressed in its {b} mode, "
                        f"read through {c_gloss}."),
                    "incoming_signal": elem["signal_in"],
                    "interpretation": elem["interprets"],
                    "required_structure": elem["structures"],
                    "validation_test": elem["validated_by"],
                    "permitted_action": elem["action"],
                    "axis_a_statement": a_text,
                    "axis_b_statement": f"{b} ({b_gloss}): {elem[b_field]}",
                    "axis_c_statement": f"{c} ({c_gloss}): {elem[c_field]}",
                    "expected_benefit": f"{benefit_id} {benefit['name']}: {benefit['meaning']}",
                    "evidence_requirement": benefit["evidence"],
                    "realisation_condition": benefit["realisation"],
                    "asset_implication": elem["asset_conversion"],
                    "source_system": "Obsidian Navigator projection; Working Memory receipts",
                    "reality": "PROJECTION (interface view of governed state; Odoo remains operational register truth)",
                    "ppv": PPV,
                    "authority": AUTHORITY,
                    "owner": OWNER_LANE,
                    "next_action": ("Steward review of this cell within Navigator acceptance; "
                                    "no operational action permitted from this cell."),
                    "stop_hold": ("HOLD: Odoo/N8N/runtime mutation, promotion, PPV movement, "
                                  "Benefit-realisation declaration."),
                    "replay_validity": REPLAY,
                    "return_path": f"COMPONENTS/{elem['html']}#l3 -> Nine Verbs -> Navigator",
                    "verbs": _AXIS_B_VERBS[b],
                })
    return cells


def element_verb_mappings():
    """81 Element x Verb mappings."""
    maps = []
    for e in ELEMENTS:
        for v in VERBS:
            primary = e["id"] in v["elements_primary"]
            maps.append({
                "element": e["id"], "verb": v["id"],
                "relationship": "PRIMARY" if primary else "PARTICIPATING",
                "statement": (
                    f"{v['name']} at {e['name']}: {v['purpose']} "
                    f"Applied here, it acts on {e['role']}."),
                "mesh_stages": v["mesh"],
                "benefit": v["benefit"],
                "evidence": v["evidence"],
            })
    return maps
