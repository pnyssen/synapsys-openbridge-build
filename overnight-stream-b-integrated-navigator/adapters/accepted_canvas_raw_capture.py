"""
Raw, byte-faithful capture of the 15 accepted canvases at
Obsidian/10_WORKSPACES/NAVIGATOR_MVP_v0.2/*.canvas, read live via `sp_read`
this session (2026-08-01, this build). Each entry is the exact JSON text
returned by the live read, parsed with json.loads() — not hand-transcribed
into Python dict syntax, specifically to avoid transcription drift. This
module performs NO transformation; existing_canvas_adapter.py does that.

This file exists so the 15-canvas -> graph_schema_v0.2 conversion in
existing_canvas_adapter.py is reproducible from a fixed, inspectable input
rather than re-reading Working Memory on every run (consistent with "do not
restart discovery").
"""
import json

RAW_CANVAS_JSON = {
    "01_ENTERPRISE_INTEGRATED.canvas": r'''{
	"nodes":[
		{"id":"n1","type":"text","text":"Purpose\nGovern, deliver and realise value repeatedly.","x":0,"y":0,"width":320,"height":160},
		{"id":"n2","type":"text","text":"Strategy\nCapture profitable markets; innovate incrementally; integrate sustainable supply chains.","x":360,"y":0,"width":320,"height":160},
		{"id":"n3","type":"text","text":"Assets\nPersistent financial, strategic, institutional and intergenerational value.","x":720,"y":0,"width":320,"height":160},
		{"id":"n4","type":"text","text":"Current Work Object\nWO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001","x":1080,"y":0,"width":320,"height":160},
		{"id":"n5","type":"text","text":"Operational truth\nOdoo registers","x":0,"y":220,"width":320,"height":160},
		{"id":"n6","type":"text","text":"Evidence\nSharePoint Working Memory","x":360,"y":220,"width":320,"height":160},
		{"id":"n7","type":"text","text":"Human interface\nObsidian candidate projection","x":720,"y":220,"width":320,"height":160},
		{"id":"n8","type":"text","text":"Runtime\nN8N held until release","x":1080,"y":220,"width":320,"height":160},
		{"id":"control_v02","type":"text","text":"NAVIGATOR CONTROL / RETURN\nSnapshot: 2026-08-01T23:17:00+10:00\nProjection source: Odoo read-only registers + SharePoint Working Memory + v0.2 correction evidence\nFreshness: Odoo Canonical Library refreshed 2026-08-01; other register counts inherited from verified v0.1 snapshot\nEvidence: SUFFICIENT_FOR_CANDIDATE_REASSURANCE; live-vault route and independent cold-start remain open\nPPV: Potential\nAuthority: HELD — no adoption, runtime, register, canon, Service, Pattern, Method, asset or PPV mutation\nStatus: candidate / static / not current\nReplay-validity: PRESERVED_WITH_CONDITIONS\nReturn: [[NAVIGATOR_MVP_PRIMARY_HOME_CANDIDATE_v0.2]]","x":0,"y":460,"width":760,"height":340}
	],
	"edges":[
		{"id":"e1","fromNode":"n1","toNode":"n2","fromSide":"right","toSide":"left","label":"directs"},
		{"id":"e2","fromNode":"n2","toNode":"n3","fromSide":"right","toSide":"left","label":"builds"},
		{"id":"e3","fromNode":"n4","toNode":"n1","fromSide":"right","toSide":"left","label":"serves"},
		{"id":"e4","fromNode":"n5","toNode":"n7","fromSide":"right","toSide":"left","label":"projects"},
		{"id":"e5","fromNode":"n6","toNode":"n7","fromSide":"right","toSide":"left","label":"evidences"},
		{"id":"e6","fromNode":"n7","toNode":"n8","fromSide":"right","toSide":"left","label":"does not authorise"}
	],
	"metadata":{"title":"Enterprise Integrated View","snapshot":"2026-08-01T23:17:00+10:00","work_object_id":"WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001","status":"candidate_not_current","authority":"HELD","source":"Odoo read-only + Working Memory","projection_source":"Odoo read-only registers + SharePoint Working Memory + v0.2 correction evidence","freshness":"2026-08-01 snapshot-bound","evidence":"SUFFICIENT_FOR_CANDIDATE_REASSURANCE; LIVE_VAULT_AND_FRESH_REVIEW_OPEN","ppv":"Potential","replay_validity":"PRESERVED_WITH_CONDITIONS","return_route":"NAVIGATOR_MVP_PRIMARY_HOME_CANDIDATE_v0.2.md"}
}''',
    "02_PURPOSE_STRATEGY_ASSETS.canvas": r'''{
  "nodes": [
    {"id": "n1","type": "text","text": "Purpose\nWhy SynapSys exists","x": 0,"y": 0,"width": 320,"height": 160},
    {"id": "n2","type": "text","text": "Strategy\nHow value is captured and compounded","x": 360,"y": 0,"width": 320,"height": 160},
    {"id": "n3","type": "text","text": "Assets\nWhat persists and differentiates","x": 720,"y": 0,"width": 320,"height": 160},
    {"id": "n4","type": "text","text": "Signal\nWhat changed or matters","x": 1080,"y": 0,"width": 320,"height": 160},
    {"id": "n5","type": "text","text": "Benefit\nWhat beneficial effect is expected or observed","x": 0,"y": 220,"width": 320,"height": 160},
    {"id": "n6","type": "text","text": "Realisation\nWhat is accepted as realised","x": 360,"y": 220,"width": 320,"height": 160},
    {"id": "control_v02","type": "text","text": "NAVIGATOR CONTROL / RETURN\nSnapshot: 2026-08-01T23:17:00+10:00\nProjection source: Odoo read-only registers + SharePoint Working Memory + v0.2 correction evidence\nFreshness: Odoo Canonical Library refreshed 2026-08-01; other register counts inherited from verified v0.1 snapshot\nEvidence: SUFFICIENT_FOR_CANDIDATE_REASSURANCE; live-vault route and independent cold-start remain open\nPPV: Potential\nAuthority: HELD — no adoption, runtime, register, canon, Service, Pattern, Method, asset or PPV mutation\nStatus: candidate / static / not current\nReplay-validity: PRESERVED_WITH_CONDITIONS\nReturn: [[NAVIGATOR_MVP_PRIMARY_HOME_CANDIDATE_v0.2]]","x": 0,"y": 460,"width": 760,"height": 340}
  ],
  "edges": [
    {"id": "e1","fromNode": "n1","toNode": "n2","fromSide": "right","toSide": "left","label": "constrains"},
    {"id": "e2","fromNode": "n2","toNode": "n3","fromSide": "right","toSide": "left","label": "produces"},
    {"id": "e3","fromNode": "n4","toNode": "n2","fromSide": "right","toSide": "left","label": "informs"},
    {"id": "e4","fromNode": "n3","toNode": "n5","fromSide": "right","toSide": "left","label": "enables"},
    {"id": "e5","fromNode": "n5","toNode": "n6","fromSide": "right","toSide": "left","label": "evidence gate"}
  ],
  "metadata": {"title": "Purpose Strategy Assets","snapshot": "2026-08-01T23:17:00+10:00","work_object_id": "WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001","status": "candidate_not_current","authority": "HELD","source": "Odoo read-only + Working Memory","projection_source": "Odoo read-only registers + SharePoint Working Memory + v0.2 correction evidence","freshness": "2026-08-01 snapshot-bound","evidence": "SUFFICIENT_FOR_CANDIDATE_REASSURANCE; LIVE_VAULT_AND_FRESH_REVIEW_OPEN","ppv": "Potential","replay_validity": "PRESERVED_WITH_CONDITIONS","return_route": "NAVIGATOR_MVP_PRIMARY_HOME_CANDIDATE_v0.2.md"}
}''',
    "03_FFE_SBR_3X3X3.canvas": r'''{
	"nodes":[
		{"id":"n1","type":"text","text":"FORM x SIGNAL\nOrient and describe","x":0,"y":0,"width":320,"height":160},
		{"id":"n2","type":"text","text":"FORM x BENEFITS\nDefine intended effects","x":360,"y":0,"width":320,"height":160},
		{"id":"n3","type":"text","text":"FORM x REALISATION\nDefine acceptance","x":720,"y":0,"width":320,"height":160},
		{"id":"n4","type":"text","text":"FLOW x SIGNAL\nRoute and prioritise","x":1080,"y":0,"width":320,"height":160},
		{"id":"n5","type":"text","text":"FLOW x BENEFITS\nDeliver and observe","x":0,"y":220,"width":320,"height":160},
		{"id":"n6","type":"text","text":"FLOW x REALISATION\nValidate and accept","x":360,"y":220,"width":320,"height":160},
		{"id":"n7","type":"text","text":"EVOLVE x SIGNAL\nLearn from change","x":720,"y":220,"width":320,"height":160},
		{"id":"n8","type":"text","text":"EVOLVE x BENEFITS\nImprove effect pathways","x":1080,"y":220,"width":320,"height":160},
		{"id":"n9","type":"text","text":"EVOLVE x REALISATION\nConvert learning to assets","x":0,"y":440,"width":320,"height":160},
		{"id":"control_v02","type":"text","text":"NAVIGATOR CONTROL / RETURN\nSnapshot: 2026-08-01T23:17:00+10:00\nProjection source: Odoo read-only registers + SharePoint Working Memory + v0.2 correction evidence\nFreshness: Odoo Canonical Library refreshed 2026-08-01; other register counts inherited from verified v0.1 snapshot\nEvidence: SUFFICIENT_FOR_CANDIDATE_REASSURANCE; live-vault route and independent cold-start remain open\nPPV: Potential\nAuthority: HELD — no adoption, runtime, register, canon, Service, Pattern, Method, asset or PPV mutation\nStatus: candidate / static / not current\nReplay-validity: PRESERVED_WITH_CONDITIONS\nReturn: [[NAVIGATOR_MVP_PRIMARY_HOME_CANDIDATE_v0.2]]","x":0,"y":680,"width":760,"height":340}
	],
	"edges":[
		{"id":"e1","fromNode":"n1","toNode":"n4","fromSide":"right","toSide":"left","label":"activate"},
		{"id":"e2","fromNode":"n4","toNode":"n7","fromSide":"right","toSide":"left","label":"learn"},
		{"id":"e3","fromNode":"n2","toNode":"n5","fromSide":"right","toSide":"left","label":"deliver"},
		{"id":"e4","fromNode":"n5","toNode":"n8","fromSide":"right","toSide":"left","label":"improve"},
		{"id":"e5","fromNode":"n3","toNode":"n6","fromSide":"right","toSide":"left","label":"assure"},
		{"id":"e6","fromNode":"n6","toNode":"n9","fromSide":"right","toSide":"left","label":"convert"}
	],
	"metadata":{"title":"Form Flow Evolve x Signal Benefits Realisation","snapshot":"2026-08-01T23:17:00+10:00","work_object_id":"WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001","status":"candidate_not_current","authority":"HELD","source":"Odoo read-only + Working Memory","projection_source":"Odoo read-only registers + SharePoint Working Memory + v0.2 correction evidence","freshness":"2026-08-01 snapshot-bound","evidence":"SUFFICIENT_FOR_CANDIDATE_REASSURANCE; LIVE_VAULT_AND_FRESH_REVIEW_OPEN","ppv":"Potential","replay_validity":"PRESERVED_WITH_CONDITIONS","return_route":"NAVIGATOR_MVP_PRIMARY_HOME_CANDIDATE_v0.2.md"}
}''',
    "04_NINE_VERB_OPERATING.canvas": r'''{
  "nodes": [
    {"id": "n1","type": "text","text": "1 Orient\nLocate context, source and purpose","x": 0,"y": 0,"width": 320,"height": 160},
    {"id": "n2","type": "text","text": "2 Canonicalise\nResolve authoritative references","x": 360,"y": 0,"width": 320,"height": 160},
    {"id": "n3","type": "text","text": "3 Structure\nCreate usable relationships","x": 720,"y": 0,"width": 320,"height": 160},
    {"id": "n4","type": "text","text": "4 Assure\nTest evidence, risk and authority","x": 1080,"y": 0,"width": 320,"height": 160},
    {"id": "n5","type": "text","text": "5 Navigate\nSelect the next valid move","x": 0,"y": 220,"width": 320,"height": 160},
    {"id": "n6","type": "text","text": "6 Compose\nAssemble bounded outputs","x": 360,"y": 220,"width": 320,"height": 160},
    {"id": "n7","type": "text","text": "7 Activate\nRelease governed action","x": 720,"y": 220,"width": 320,"height": 160},
    {"id": "n8","type": "text","text": "8 Transform\nChange capability or state","x": 1080,"y": 220,"width": 320,"height": 160},
    {"id": "n9","type": "text","text": "9 Project\nExpose current human-facing state","x": 0,"y": 440,"width": 320,"height": 160},
    {"id": "control_v02","type": "text","text": "NAVIGATOR CONTROL / RETURN\nSnapshot: 2026-08-01T23:17:00+10:00\nProjection source: Odoo read-only registers + SharePoint Working Memory + v0.2 correction evidence\nFreshness: Odoo Canonical Library refreshed 2026-08-01; other register counts inherited from verified v0.1 snapshot\nEvidence: SUFFICIENT_FOR_CANDIDATE_REASSURANCE; live-vault route and independent cold-start remain open\nPPV: Potential\nAuthority: HELD — no adoption, runtime, register, canon, Service, Pattern, Method, asset or PPV mutation\nStatus: candidate / static / not current\nReplay-validity: PRESERVED_WITH_CONDITIONS\nReturn: [[NAVIGATOR_MVP_PRIMARY_HOME_CANDIDATE_v0.2]]","x": 0,"y": 680,"width": 760,"height": 340}
  ],
  "edges": [
    {"id": "e1","fromNode": "n1","toNode": "n2","fromSide": "right","toSide": "left"},
    {"id": "e2","fromNode": "n2","toNode": "n3","fromSide": "right","toSide": "left"},
    {"id": "e3","fromNode": "n3","toNode": "n4","fromSide": "right","toSide": "left"},
    {"id": "e4","fromNode": "n4","toNode": "n5","fromSide": "right","toSide": "left"},
    {"id": "e5","fromNode": "n5","toNode": "n6","fromSide": "right","toSide": "left"},
    {"id": "e6","fromNode": "n6","toNode": "n7","fromSide": "right","toSide": "left","label": "authority gate"},
    {"id": "e7","fromNode": "n7","toNode": "n8","fromSide": "right","toSide": "left"},
    {"id": "e8","fromNode": "n8","toNode": "n9","fromSide": "right","toSide": "left"},
    {"id": "e9","fromNode": "n9","toNode": "n1","fromSide": "right","toSide": "left","label": "feedback"}
  ],
  "metadata": {"title": "Nine Verb Operating View","snapshot": "2026-08-01T23:17:00+10:00","work_object_id": "WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001","status": "candidate_not_current","authority": "HELD","source": "Odoo read-only + Working Memory","projection_source": "Odoo read-only registers + SharePoint Working Memory + v0.2 correction evidence","freshness": "2026-08-01 snapshot-bound","evidence": "SUFFICIENT_FOR_CANDIDATE_REASSURANCE; LIVE_VAULT_AND_FRESH_REVIEW_OPEN","ppv": "Potential","replay_validity": "PRESERVED_WITH_CONDITIONS","return_route": "NAVIGATOR_MVP_PRIMARY_HOME_CANDIDATE_v0.2.md"}
}''',
    "05_MESH_LIFECYCLE_GATES.canvas": r'''{
	"nodes":[
		{"id":"n1","type":"text","text":"Signal","x":0,"y":0,"width":320,"height":160},
		{"id":"n2","type":"text","text":"Interpretation","x":360,"y":0,"width":320,"height":160},
		{"id":"n3","type":"text","text":"Structuring","x":720,"y":0,"width":320,"height":160},
		{"id":"n4","type":"text","text":"Validation","x":1080,"y":0,"width":320,"height":160},
		{"id":"n5","type":"text","text":"Action","x":0,"y":220,"width":320,"height":160},
		{"id":"n6","type":"text","text":"Observation","x":360,"y":220,"width":320,"height":160},
		{"id":"n7","type":"text","text":"Learning","x":720,"y":220,"width":320,"height":160},
		{"id":"n8","type":"text","text":"Asset Conversion","x":1080,"y":220,"width":320,"height":160},
		{"id":"n9","type":"text","text":"Feedback","x":0,"y":440,"width":320,"height":160},
		{"id":"n10","type":"text","text":"Gates\nEvidence | PPV | Authority | Risk | STOP/HOLD","x":360,"y":440,"width":320,"height":160},
		{"id":"control_v02","type":"text","text":"NAVIGATOR CONTROL / RETURN\nSnapshot: 2026-08-01T23:17:00+10:00\nProjection source: Odoo read-only registers + SharePoint Working Memory + v0.2 correction evidence\nFreshness: Odoo Canonical Library refreshed 2026-08-01; other register counts inherited from verified v0.1 snapshot\nEvidence: SUFFICIENT_FOR_CANDIDATE_REASSURANCE; live-vault route and independent cold-start remain open\nPPV: Potential\nAuthority: HELD — no adoption, runtime, register, canon, Service, Pattern, Method, asset or PPV mutation\nStatus: candidate / static / not current\nReplay-validity: PRESERVED_WITH_CONDITIONS\nReturn: [[NAVIGATOR_MVP_PRIMARY_HOME_CANDIDATE_v0.2]]","x":0,"y":680,"width":760,"height":340}
	],
	"edges":[
		{"id":"e1","fromNode":"n1","toNode":"n2","fromSide":"right","toSide":"left"},
		{"id":"e2","fromNode":"n2","toNode":"n3","fromSide":"right","toSide":"left"},
		{"id":"e3","fromNode":"n3","toNode":"n4","fromSide":"right","toSide":"left"},
		{"id":"e4","fromNode":"n4","toNode":"n5","fromSide":"right","toSide":"left","label":"D001/D007 where required"},
		{"id":"e5","fromNode":"n5","toNode":"n6","fromSide":"right","toSide":"left"},
		{"id":"e6","fromNode":"n6","toNode":"n7","fromSide":"right","toSide":"left"},
		{"id":"e7","fromNode":"n7","toNode":"n8","fromSide":"right","toSide":"left","label":"AQG"},
		{"id":"e8","fromNode":"n8","toNode":"n9","fromSide":"right","toSide":"left"},
		{"id":"e9","fromNode":"n9","toNode":"n1","fromSide":"right","toSide":"left"},
		{"id":"e10","fromNode":"n10","toNode":"n4","fromSide":"right","toSide":"left","label":"controls"},
		{"id":"e11","fromNode":"n10","toNode":"n5","fromSide":"right","toSide":"left","label":"controls"}
	],
	"metadata":{"title":"Mesh Lifecycle and Gates","snapshot":"2026-08-01T23:17:00+10:00","work_object_id":"WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001","status":"candidate_not_current","authority":"HELD","source":"Odoo read-only + Working Memory","projection_source":"Odoo read-only registers + SharePoint Working Memory + v0.2 correction evidence","freshness":"2026-08-01 snapshot-bound","evidence":"SUFFICIENT_FOR_CANDIDATE_REASSURANCE; LIVE_VAULT_AND_FRESH_REVIEW_OPEN","ppv":"Potential","replay_validity":"PRESERVED_WITH_CONDITIONS","return_route":"NAVIGATOR_MVP_PRIMARY_HOME_CANDIDATE_v0.2.md"}
}''',
    "06_SIGNAL_TO_ASSET_RELATIONSHIP.canvas": r'''{
  "nodes": [
    {"id": "n1","type": "text","text": "Signal\nProjection drift: Pattern count mismatch","x": 0,"y": 0,"width": 320,"height": 160},
    {"id": "n2","type": "text","text": "Context\nCTX-SS","x": 360,"y": 0,"width": 320,"height": 160},
    {"id": "n3","type": "text","text": "Service\nSC-05 Assurance Audit and Learning","x": 720,"y": 0,"width": 320,"height": 160},
    {"id": "n4","type": "text","text": "Method\nD002-XOT Cross-Object Trace Evidence","x": 1080,"y": 0,"width": 320,"height": 160},
    {"id": "n5","type": "text","text": "Pattern candidate\nPAT-A02 Implementation Trace Evidence","x": 0,"y": 220,"width": 320,"height": 160},
    {"id": "n6","type": "text","text": "Canonical references\nData-lake evidence index; ESA catalogue index","x": 360,"y": 220,"width": 320,"height": 160},
    {"id": "n7","type": "text","text": "Work Object\nWO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001","x": 720,"y": 220,"width": 320,"height": 160},
    {"id": "n8","type": "text","text": "Benefit\nFresher, safer navigation","x": 1080,"y": 220,"width": 320,"height": 160},
    {"id": "n9","type": "text","text": "Asset candidate\nReusable projection-control pattern (HELD)","x": 0,"y": 440,"width": 320,"height": 160},
    {"id": "control_v02","type": "text","text": "NAVIGATOR CONTROL / RETURN\nSnapshot: 2026-08-01T23:17:00+10:00\nProjection source: Odoo read-only registers + SharePoint Working Memory + v0.2 correction evidence\nFreshness: Odoo Canonical Library refreshed 2026-08-01; other register counts inherited from verified v0.1 snapshot\nEvidence: SUFFICIENT_FOR_CANDIDATE_REASSURANCE; live-vault route and independent cold-start remain open\nPPV: Potential\nAuthority: HELD — no adoption, runtime, register, canon, Service, Pattern, Method, asset or PPV mutation\nStatus: candidate / static / not current\nReplay-validity: PRESERVED_WITH_CONDITIONS\nReturn: [[NAVIGATOR_MVP_PRIMARY_HOME_CANDIDATE_v0.2]]","x": 0,"y": 680,"width": 760,"height": 340}
  ],
  "edges": [
    {"id": "e1","fromNode": "n1","toNode": "n2","fromSide": "right","toSide": "left"},
    {"id": "e2","fromNode": "n2","toNode": "n3","fromSide": "right","toSide": "left","label": "match"},
    {"id": "e3","fromNode": "n3","toNode": "n4","fromSide": "right","toSide": "left","label": "uses"},
    {"id": "e4","fromNode": "n4","toNode": "n5","fromSide": "right","toSide": "left","label": "candidate form"},
    {"id": "e5","fromNode": "n5","toNode": "n6","fromSide": "right","toSide": "left","label": "supported by"},
    {"id": "e6","fromNode": "n6","toNode": "n7","fromSide": "right","toSide": "left","label": "evidence"},
    {"id": "e7","fromNode": "n7","toNode": "n8","fromSide": "right","toSide": "left","label": "targets"},
    {"id": "e8","fromNode": "n8","toNode": "n9","fromSide": "right","toSide": "left","label": "qualification required"}
  ],
  "metadata": {"title": "Signal to Asset Relationship","snapshot": "2026-08-01T23:17:00+10:00","work_object_id": "WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001","status": "candidate_not_current","authority": "HELD","source": "Odoo read-only + Working Memory","projection_source": "Odoo read-only registers + SharePoint Working Memory + v0.2 correction evidence","freshness": "2026-08-01 snapshot-bound","evidence": "SUFFICIENT_FOR_CANDIDATE_REASSURANCE; LIVE_VAULT_AND_FRESH_REVIEW_OPEN","ppv": "Potential","replay_validity": "PRESERVED_WITH_CONDITIONS","return_route": "NAVIGATOR_MVP_PRIMARY_HOME_CANDIDATE_v0.2.md"}
}''',
    "07_SERVICE_CATALOGUE_INTEGRATED.canvas": r'''{
	"nodes":[
		{"id":"n1","type":"text","text":"Active Services\n18\nOperational core","x":0,"y":0,"width":320,"height":160},
		{"id":"n2","type":"text","text":"Future scoped\n1\nSC-06 reference-only","x":360,"y":0,"width":320,"height":160},
		{"id":"n3","type":"text","text":"Deprecated\n16\nVisible lineage; not deleted","x":720,"y":0,"width":320,"height":160},
		{"id":"n4","type":"text","text":"Active completeness\nContext + Method + membrane + validation: 18/18","x":1080,"y":0,"width":320,"height":160},
		{"id":"n5","type":"text","text":"Open gaps\n5 canonical links\n2 PPV fields\n1 invalid PPV ordering","x":0,"y":220,"width":320,"height":160},
		{"id":"n6","type":"text","text":"Projection\n[[SERVICE_CATALOGUE_PROJECTION_v0.2]]","x":360,"y":220,"width":320,"height":160},
		{"id":"control_v02","type":"text","text":"NAVIGATOR CONTROL / RETURN\nSnapshot: 2026-08-01T23:17:00+10:00\nProjection source: Odoo read-only registers + SharePoint Working Memory + v0.2 correction evidence\nFreshness: Odoo Canonical Library refreshed 2026-08-01; other register counts inherited from verified v0.1 snapshot\nEvidence: SUFFICIENT_FOR_CANDIDATE_REASSURANCE; live-vault route and independent cold-start remain open\nPPV: Potential\nAuthority: HELD — no adoption, runtime, register, canon, Service, Pattern, Method, asset or PPV mutation\nStatus: candidate / static / not current\nReplay-validity: PRESERVED_WITH_CONDITIONS\nReturn: [[NAVIGATOR_MVP_PRIMARY_HOME_CANDIDATE_v0.2]]","x":0,"y":460,"width":760,"height":340}
	],
	"edges":[
		{"id":"e1","fromNode":"n1","toNode":"n4","fromSide":"right","toSide":"left"},
		{"id":"e2","fromNode":"n1","toNode":"n5","fromSide":"right","toSide":"left"},
		{"id":"e3","fromNode":"n2","toNode":"n5","fromSide":"right","toSide":"left"},
		{"id":"e4","fromNode":"n3","toNode":"n6","fromSide":"right","toSide":"left","label":"separate"},
		{"id":"e5","fromNode":"n4","toNode":"n6","fromSide":"right","toSide":"left"},
		{"id":"e6","fromNode":"n5","toNode":"n6","fromSide":"right","toSide":"left","label":"visible"}
	],
	"metadata":{"title":"Service Catalogue Integrated View","snapshot":"2026-08-01T23:17:00+10:00","work_object_id":"WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001","status":"candidate_not_current","authority":"HELD","source":"Odoo read-only + Working Memory","projection_source":"Odoo read-only registers + SharePoint Working Memory + v0.2 correction evidence","freshness":"2026-08-01 snapshot-bound","evidence":"SUFFICIENT_FOR_CANDIDATE_REASSURANCE; LIVE_VAULT_AND_FRESH_REVIEW_OPEN","ppv":"Potential","replay_validity":"PRESERVED_WITH_CONDITIONS","return_route":"NAVIGATOR_MVP_PRIMARY_HOME_CANDIDATE_v0.2.md"}
}''',
    "08_SERVICE_STATUS_PPV.canvas": r'''{
  "nodes": [
    {"id": "n1","type": "text","text": "Potential\nCandidate value; evidence incomplete","x": 0,"y": 0,"width": 320,"height": 160},
    {"id": "n2","type": "text","text": "Probable\nBounded evidence supports repeatability","x": 360,"y": 0,"width": 320,"height": 160},
    {"id": "n3","type": "text","text": "Verified\nGoverned validation and outcome trace","x": 720,"y": 0,"width": 320,"height": 160},
    {"id": "n4","type": "text","text": "SA-06 defect\nEntry Verified > ceiling Probable\nCorrection held","x": 1080,"y": 0,"width": 320,"height": 160},
    {"id": "n5","type": "text","text": "GV-TEC-001 / 002\nPPV fields missing\nProposed Potential to Probable ceiling","x": 0,"y": 220,"width": 320,"height": 160},
    {"id": "n6","type": "text","text": "No colour-only semantics\nState labels are explicit","x": 360,"y": 220,"width": 320,"height": 160},
    {"id": "control_v02","type": "text","text": "NAVIGATOR CONTROL / RETURN\nSnapshot: 2026-08-01T23:17:00+10:00\nProjection source: Odoo read-only registers + SharePoint Working Memory + v0.2 correction evidence\nFreshness: Odoo Canonical Library refreshed 2026-08-01; other register counts inherited from verified v0.1 snapshot\nEvidence: SUFFICIENT_FOR_CANDIDATE_REASSURANCE; live-vault route and independent cold-start remain open\nPPV: Potential\nAuthority: HELD — no adoption, runtime, register, canon, Service, Pattern, Method, asset or PPV mutation\nStatus: candidate / static / not current\nReplay-validity: PRESERVED_WITH_CONDITIONS\nReturn: [[NAVIGATOR_MVP_PRIMARY_HOME_CANDIDATE_v0.2]]","x": 0,"y": 460,"width": 760,"height": 340}
  ],
  "edges": [
    {"id": "e1","fromNode": "n1","toNode": "n2","fromSide": "right","toSide": "left","label": "evidence"},
    {"id": "e2","fromNode": "n2","toNode": "n3","fromSide": "right","toSide": "left","label": "validation"},
    {"id": "e3","fromNode": "n4","toNode": "n2","fromSide": "right","toSide": "left","label": "conservative proposal"},
    {"id": "e4","fromNode": "n5","toNode": "n1","fromSide": "right","toSide": "left","label": "entry proposal"},
    {"id": "e5","fromNode": "n6","toNode": "n1","fromSide": "right","toSide": "left","label": "display rule"}
  ],
  "metadata": {"title": "Service Status and PPV","snapshot": "2026-08-01T23:17:00+10:00","work_object_id": "WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001","status": "candidate_not_current","authority": "HELD","source": "Odoo read-only + Working Memory","projection_source": "Odoo read-only registers + SharePoint Working Memory + v0.2 correction evidence","freshness": "2026-08-01 snapshot-bound","evidence": "SUFFICIENT_FOR_CANDIDATE_REASSURANCE; LIVE_VAULT_AND_FRESH_REVIEW_OPEN","ppv": "Potential","replay_validity": "PRESERVED_WITH_CONDITIONS","return_route": "NAVIGATOR_MVP_PRIMARY_HOME_CANDIDATE_v0.2.md"}
}''',
    "09_PATTERN_METHOD_CANONICAL.canvas": r'''{
  "nodes": [
    {"id": "n1","type": "text","text": "Patterns\n15 total; 1 evidenced pilot; 14 candidates","x": 0,"y": 0,"width": 320,"height": 160},
    {"id": "n2","type": "text","text": "Methods\n12 total; 10 active","x": 360,"y": 0,"width": 320,"height": 160},
    {"id": "n3","type": "text","text": "Canonical Library\n56 total; 5 promoted","x": 720,"y": 0,"width": 320,"height": 160},
    {"id": "n4","type": "text","text": "Concentration risk\nPAT-A05 links most Methods","x": 1080,"y": 0,"width": 320,"height": 160},
    {"id": "n5","type": "text","text": "Qualification gaps\nContext, tests, authority, replay, observed effect","x": 0,"y": 220,"width": 320,"height": 160},
    {"id": "n6","type": "text","text": "No projection promotion\nCandidate remains candidate","x": 360,"y": 220,"width": 320,"height": 160},
    {"id": "control_v02","type": "text","text": "NAVIGATOR CONTROL / RETURN\nSnapshot: 2026-08-01T23:17:00+10:00\nProjection source: Odoo read-only registers + SharePoint Working Memory + v0.2 correction evidence\nFreshness: Odoo Canonical Library refreshed 2026-08-01; other register counts inherited from verified v0.1 snapshot\nEvidence: SUFFICIENT_FOR_CANDIDATE_REASSURANCE; live-vault route and independent cold-start remain open\nPPV: Potential\nAuthority: HELD — no adoption, runtime, register, canon, Service, Pattern, Method, asset or PPV mutation\nStatus: candidate / static / not current\nReplay-validity: PRESERVED_WITH_CONDITIONS\nReturn: [[NAVIGATOR_MVP_PRIMARY_HOME_CANDIDATE_v0.2]]","x": 0,"y": 460,"width": 760,"height": 340}
  ],
  "edges": [
    {"id": "e1","fromNode": "n1","toNode": "n2","fromSide": "right","toSide": "left","label": "guides"},
    {"id": "e2","fromNode": "n2","toNode": "n3","fromSide": "right","toSide": "left","label": "references"},
    {"id": "e3","fromNode": "n4","toNode": "n1","fromSide": "right","toSide": "left","label": "weak differentiation"},
    {"id": "e4","fromNode": "n5","toNode": "n1","fromSide": "right","toSide": "left","label": "blocks admission"},
    {"id": "e5","fromNode": "n6","toNode": "n3","fromSide": "right","toSide": "left","label": "authority rule"}
  ],
  "metadata": {"title": "Pattern Method Canonical Relationship","snapshot": "2026-08-01T23:17:00+10:00","work_object_id": "WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001","status": "candidate_not_current","authority": "HELD","source": "Odoo read-only + Working Memory","projection_source": "Odoo read-only registers + SharePoint Working Memory + v0.2 correction evidence","freshness": "2026-08-01 snapshot-bound","evidence": "SUFFICIENT_FOR_CANDIDATE_REASSURANCE; LIVE_VAULT_AND_FRESH_REVIEW_OPEN","ppv": "Potential","replay_validity": "PRESERVED_WITH_CONDITIONS","return_route": "NAVIGATOR_MVP_PRIMARY_HOME_CANDIDATE_v0.2.md"}
}''',
    "10_CANONICAL_STATE.canvas": r'''{
  "nodes": [
    {"id": "n1","type": "text","text": "Canon promoted\n5","x": 0,"y": 0,"width": 320,"height": 160},
    {"id": "n2","type": "text","text": "Candidate\n40","x": 360,"y": 0,"width": 320,"height": 160},
    {"id": "n3","type": "text","text": "Not promoted\n11","x": 720,"y": 0,"width": 320,"height": 160},
    {"id": "n4","type": "text","text": "Evidence conflicted\n4","x": 1080,"y": 0,"width": 320,"height": 160},
    {"id": "n5","type": "text","text": "Evidence insufficient\n1","x": 0,"y": 220,"width": 320,"height": 160},
    {"id": "n6","type": "text","text": "Authority rule\nStorage does not equal canon","x": 360,"y": 220,"width": 320,"height": 160},
    {"id": "control_v02","type": "text","text": "NAVIGATOR CONTROL / RETURN\nSnapshot: 2026-08-01T23:17:00+10:00\nProjection source: Odoo read-only registers + SharePoint Working Memory + v0.2 correction evidence\nFreshness: Odoo Canonical Library refreshed 2026-08-01; other register counts inherited from verified v0.1 snapshot\nEvidence: SUFFICIENT_FOR_CANDIDATE_REASSURANCE; live-vault route and independent cold-start remain open\nPPV: Potential\nAuthority: HELD — no adoption, runtime, register, canon, Service, Pattern, Method, asset or PPV mutation\nStatus: candidate / static / not current\nReplay-validity: PRESERVED_WITH_CONDITIONS\nReturn: [[NAVIGATOR_MVP_PRIMARY_HOME_CANDIDATE_v0.2]]","x": 0,"y": 460,"width": 760,"height": 340}
  ],
  "edges": [
    {"id": "e1","fromNode": "n2","toNode": "n1","fromSide": "right","toSide": "left","label": "Steward/D001 only"},
    {"id": "e2","fromNode": "n3","toNode": "n2","fromSide": "right","toSide": "left","label": "candidate path"},
    {"id": "e3","fromNode": "n4","toNode": "n2","fromSide": "right","toSide": "left","label": "resolve evidence"},
    {"id": "e4","fromNode": "n5","toNode": "n2","fromSide": "right","toSide": "left","label": "recover evidence"},
    {"id": "e5","fromNode": "n6","toNode": "n1","fromSide": "right","toSide": "left","label": "controls"}
  ],
  "metadata": {"title": "Canonical State View","snapshot": "2026-08-01T23:17:00+10:00","work_object_id": "WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001","status": "candidate_not_current","authority": "HELD","source": "Odoo read-only + Working Memory","projection_source": "Odoo read-only registers + SharePoint Working Memory + v0.2 correction evidence","freshness": "2026-08-01 snapshot-bound","evidence": "SUFFICIENT_FOR_CANDIDATE_REASSURANCE; LIVE_VAULT_AND_FRESH_REVIEW_OPEN","ppv": "Potential","replay_validity": "PRESERVED_WITH_CONDITIONS","return_route": "NAVIGATOR_MVP_PRIMARY_HOME_CANDIDATE_v0.2.md"}
}''',
    "11_BENEFIT_ASSET_REALISATION.canvas": r'''{
  "nodes": [
    {"id": "n1","type": "text","text": "Output\nCandidate Navigator suite","x": 0,"y": 0,"width": 320,"height": 160},
    {"id": "n2","type": "text","text": "Outcome\nSimpler access to integrated state","x": 360,"y": 0,"width": 320,"height": 160},
    {"id": "n3","type": "text","text": "Expected benefit\nFaster, safer Steward decisions","x": 720,"y": 0,"width": 320,"height": 160},
    {"id": "n4","type": "text","text": "Observed benefit\nStatic tests pass; surfaces navigable","x": 1080,"y": 0,"width": 320,"height": 160},
    {"id": "n5","type": "text","text": "Realised benefit\nHELD pending use and acceptance","x": 0,"y": 220,"width": 320,"height": 160},
    {"id": "n6","type": "text","text": "Asset effect\nReusable interface pattern","x": 360,"y": 220,"width": 320,"height": 160},
    {"id": "n7","type": "text","text": "Qualified asset\nHELD pending AQG, reuse and authority","x": 720,"y": 220,"width": 320,"height": 160},
    {"id": "control_v02","type": "text","text": "NAVIGATOR CONTROL / RETURN\nSnapshot: 2026-08-01T23:17:00+10:00\nProjection source: Odoo read-only registers + SharePoint Working Memory + v0.2 correction evidence\nFreshness: Odoo Canonical Library refreshed 2026-08-01; other register counts inherited from verified v0.1 snapshot\nEvidence: SUFFICIENT_FOR_CANDIDATE_REASSURANCE; live-vault route and independent cold-start remain open\nPPV: Potential\nAuthority: HELD — no adoption, runtime, register, canon, Service, Pattern, Method, asset or PPV mutation\nStatus: candidate / static / not current\nReplay-validity: PRESERVED_WITH_CONDITIONS\nReturn: [[NAVIGATOR_MVP_PRIMARY_HOME_CANDIDATE_v0.2]]","x": 0,"y": 460,"width": 760,"height": 340}
  ],
  "edges": [
    {"id": "e1","fromNode": "n1","toNode": "n2","fromSide": "right","toSide": "left"},
    {"id": "e2","fromNode": "n2","toNode": "n3","fromSide": "right","toSide": "left"},
    {"id": "e3","fromNode": "n3","toNode": "n4","fromSide": "right","toSide": "left","label": "observe"},
    {"id": "e4","fromNode": "n4","toNode": "n5","fromSide": "right","toSide": "left","label": "acceptance gate"},
    {"id": "e5","fromNode": "n4","toNode": "n6","fromSide": "right","toSide": "left","label": "possible"},
    {"id": "e6","fromNode": "n6","toNode": "n7","fromSide": "right","toSide": "left","label": "AQG"}
  ],
  "metadata": {"title": "Benefit and Asset Realisation","snapshot": "2026-08-01T23:17:00+10:00","work_object_id": "WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001","status": "candidate_not_current","authority": "HELD","source": "Odoo read-only + Working Memory","projection_source": "Odoo read-only registers + SharePoint Working Memory + v0.2 correction evidence","freshness": "2026-08-01 snapshot-bound","evidence": "SUFFICIENT_FOR_CANDIDATE_REASSURANCE; LIVE_VAULT_AND_FRESH_REVIEW_OPEN","ppv": "Potential","replay_validity": "PRESERVED_WITH_CONDITIONS","return_route": "NAVIGATOR_MVP_PRIMARY_HOME_CANDIDATE_v0.2.md"}
}''',
    "12_CONTEXT_MEMBRANE.canvas": r'''{
  "nodes": [
    {"id": "n1","type": "text","text": "External signals\nMarkets, clients, partners, regulation","x": 0,"y": 0,"width": 320,"height": 160},
    {"id": "n2","type": "text","text": "Context membrane\nIdentity, authority, evidence, privacy, scope","x": 360,"y": 0,"width": 320,"height": 160},
    {"id": "n3","type": "text","text": "CTX-SS\nCurrent operating context","x": 720,"y": 0,"width": 320,"height": 160},
    {"id": "n4","type": "text","text": "Services\nTranslate across the membrane","x": 1080,"y": 0,"width": 320,"height": 160},
    {"id": "n5","type": "text","text": "Internal registers\nOdoo operational truth","x": 0,"y": 220,"width": 320,"height": 160},
    {"id": "n6","type": "text","text": "Projection\nObsidian human interface","x": 360,"y": 220,"width": 320,"height": 160},
    {"id": "control_v02","type": "text","text": "NAVIGATOR CONTROL / RETURN\nSnapshot: 2026-08-01T23:17:00+10:00\nProjection source: Odoo read-only registers + SharePoint Working Memory + v0.2 correction evidence\nFreshness: Odoo Canonical Library refreshed 2026-08-01; other register counts inherited from verified v0.1 snapshot\nEvidence: SUFFICIENT_FOR_CANDIDATE_REASSURANCE; live-vault route and independent cold-start remain open\nPPV: Potential\nAuthority: HELD — no adoption, runtime, register, canon, Service, Pattern, Method, asset or PPV mutation\nStatus: candidate / static / not current\nReplay-validity: PRESERVED_WITH_CONDITIONS\nReturn: [[NAVIGATOR_MVP_PRIMARY_HOME_CANDIDATE_v0.2]]","x": 0,"y": 460,"width": 760,"height": 340}
  ],
  "edges": [
    {"id": "e1","fromNode": "n1","toNode": "n2","fromSide": "right","toSide": "left","label": "enter"},
    {"id": "e2","fromNode": "n2","toNode": "n3","fromSide": "right","toSide": "left","label": "bind"},
    {"id": "e3","fromNode": "n3","toNode": "n4","fromSide": "right","toSide": "left","label": "select"},
    {"id": "e4","fromNode": "n4","toNode": "n5","fromSide": "right","toSide": "left","label": "record"},
    {"id": "e5","fromNode": "n5","toNode": "n6","fromSide": "right","toSide": "left","label": "project"},
    {"id": "e6","fromNode": "n6","toNode": "n2","fromSide": "right","toSide": "left","label": "feedback"}
  ],
  "metadata": {"title": "Context and Membrane","snapshot": "2026-08-01T23:17:00+10:00","work_object_id": "WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001","status": "candidate_not_current","authority": "HELD","source": "Odoo read-only + Working Memory","projection_source": "Odoo read-only registers + SharePoint Working Memory + v0.2 correction evidence","freshness": "2026-08-01 snapshot-bound","evidence": "SUFFICIENT_FOR_CANDIDATE_REASSURANCE; LIVE_VAULT_AND_FRESH_REVIEW_OPEN","ppv": "Potential","replay_validity": "PRESERVED_WITH_CONDITIONS","return_route": "NAVIGATOR_MVP_PRIMARY_HOME_CANDIDATE_v0.2.md"}
}''',
    "13_AI_AGENT_ROUTING.canvas": r'''{
  "nodes": [
    {"id": "hub","type": "text","text": "Navigator / ChatGPT Hub\nController: priority, Work Object, manifest, arbitration and CURRENT_DELIVERY","x": 360,"y": 0,"width": 360,"height": 180},
    {"id": "a","type": "text","text": "STREAM A — CODEX\nTarget: Codex code mode\nModel: highest available Codex agentic coding model\nGoal: runtime truth + integration graph\nState: READY_TO_SEND","x": 0,"y": 240,"width": 360,"height": 220},
    {"id": "b","type": "text","text": "STREAM B — CLAUDE CODE\nTarget: Claude Code\nModel: strongest tool-enabled coding model\nGoal: N8N viewer + Canvas compiler\nState: READY_TO_SEND","x": 400,"y": 240,"width": 360,"height": 220},
    {"id": "c","type": "text","text": "STREAM C — CLAUDE COWORK / FABLE\nTarget: Claude CoWork\nModel: strongest interface-synthesis model; Fable only where beneficial\nGoal: unified visual system + Odoo skin + 2D→3D path\nState: READY_TO_SEND","x": 800,"y": 240,"width": 400,"height": 220},
    {"id": "d009","type": "text","text": "D009\nIndependent integrated assurance after A–C returns are consumed\nState: HELD_PENDING_INTEGRATED_CANDIDATE","x": 1240,"y": 240,"width": 360,"height": 220},
    {"id": "d001","type": "text","text": "D001 / Steward\nDecision and authority","x": 1240,"y": 0,"width": 360,"height": 180},
    {"id": "d007","type": "text","text": "D007\nReleased implementation and mutation only","x": 800,"y": 0,"width": 360,"height": 180},
    {"id": "runtime","type": "text","text": "N8N / Odoo / Working Memory / Obsidian\nRuntime, operational truth, evidence and current projection","x": 0,"y": 0,"width": 320,"height": 180},
    {"id": "control","type": "text","text": "NAVIGATOR CONTROL / RETURN\nSnapshot: 2026-08-02T00:45:00+10:00\nCurrent surface: [[CURRENT_DELIVERY]]\nEvidence: SUFFICIENT_FOR_CONTROLLED_LAUNCH_PREPARATION\nReality: Navigator implemented; A–C ready to send; not yet initiated\nPPV: Potential\nAuthority: bounded preparation active; production mutation held\nPresentation: white-background HTML only\nReplay-validity: PRESERVED\nReturn: [[NAVIGATOR_MVP_PRIMARY_HOME_CANDIDATE_v0.2]]","x": 0,"y": 520,"width": 900,"height": 360}
  ],
  "edges": [
    {"id": "e1","fromNode": "runtime","toNode": "hub","fromSide": "right","toSide": "left","label": "evidence/state"},
    {"id": "e2","fromNode": "hub","toNode": "a","fromSide": "bottom","toSide": "top","label": "dispatch"},
    {"id": "e3","fromNode": "hub","toNode": "b","fromSide": "bottom","toSide": "top","label": "dispatch"},
    {"id": "e4","fromNode": "hub","toNode": "c","fromSide": "bottom","toSide": "top","label": "dispatch"},
    {"id": "e5","fromNode": "a","toNode": "hub","fromSide": "top","toSide": "bottom","label": "filed return"},
    {"id": "e6","fromNode": "b","toNode": "hub","fromSide": "top","toSide": "bottom","label": "filed return"},
    {"id": "e7","fromNode": "c","toNode": "hub","fromSide": "top","toSide": "bottom","label": "filed return"},
    {"id": "e8","fromNode": "hub","toNode": "d009","fromSide": "right","toSide": "left","label": "integrated assurance"},
    {"id": "e9","fromNode": "d009","toNode": "d001","fromSide": "top","toSide": "bottom","label": "decision surface"},
    {"id": "e10","fromNode": "d001","toNode": "d007","fromSide": "left","toSide": "right","label": "release"},
    {"id": "e11","fromNode": "d007","toNode": "runtime","fromSide": "left","toSide": "right","label": "execute"}
  ],
  "metadata": {"title": "AI Family and Agent Routing — Current Three-Stream Wave","snapshot": "2026-08-02T00:45:00+10:00","work_object_id": "WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001","status": "current_ready_to_send","authority": "BOUNDED_PREPARATION_ACTIVE_PRODUCTION_HELD","source": "Current Navigator + Working Memory wave controller","projection_source": "Accepted Navigator and wave v0.2 control assets","freshness": "2026-08-02T00:45:00+10:00","evidence": "SUFFICIENT_FOR_CONTROLLED_LAUNCH_PREPARATION","ppv": "Potential","replay_validity": "PRESERVED","return_route": "NAVIGATOR_MVP_PRIMARY_HOME_CANDIDATE_v0.2.md","current_delivery": "CURRENT_DELIVERY.md"}
}''',
    "14_CURRENT_WORK_OBJECT_QUEUE.canvas": r'''{
  "nodes": [
    {"id": "q","type": "text","text": "Queue item\nLaunch and reconcile the controlled three-stream integrated Navigator MVP wave.","x": 0,"y": 0,"width": 360,"height": 180},
    {"id": "wo","type": "text","text": "Work Object\nWO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001","x": 400,"y": 0,"width": 360,"height": 180},
    {"id": "delivery","type": "text","text": "Current control surface\n[[CURRENT_DELIVERY]]\nNo standalone status HTML","x": 800,"y": 0,"width": 360,"height": 180},
    {"id": "state","type": "text","text": "Reality\nNavigator implemented\nStreams A–C READY_TO_SEND\nExecution not yet started","x": 1200,"y": 0,"width": 360,"height": 180},
    {"id": "evidence","type": "text","text": "Evidence\nSUFFICIENT_FOR_CONTROLLED_LAUNCH_PREPARATION","x": 0,"y": 240,"width": 360,"height": 180},
    {"id": "ppv","type": "text","text": "PPV\nPotential","x": 400,"y": 240,"width": 360,"height": 180},
    {"id": "authority","type": "text","text": "Authority\nBounded preparation active\nProduction mutation HELD","x": 800,"y": 240,"width": 360,"height": 180},
    {"id": "next","type": "text","text": "Exactly one next action\nOpen the three correct tool-enabled sessions and paste the v0.2 packets; then mark SENT_REPORTED.","x": 1200,"y": 240,"width": 360,"height": 180},
    {"id": "control","type": "text","text": "NAVIGATOR CONTROL / RETURN\nSnapshot: 2026-08-02T00:45:00+10:00\nThree production lanes only; D009 later\nWhite-background HTML regression enforced\nInstalled skill controls updated\nReturn: [[NAVIGATOR_MVP_PRIMARY_HOME_CANDIDATE_v0.2]]\nReplay-validity: PRESERVED","x": 0,"y": 500,"width": 900,"height": 300}
  ],
  "edges": [
    {"id": "e1","fromNode": "q","toNode": "wo","fromSide": "right","toSide": "left","label": "bound"},
    {"id": "e2","fromNode": "wo","toNode": "delivery","fromSide": "right","toSide": "left","label": "controlled through"},
    {"id": "e3","fromNode": "delivery","toNode": "state","fromSide": "right","toSide": "left"},
    {"id": "e4","fromNode": "state","toNode": "evidence","fromSide": "left","toSide": "right"},
    {"id": "e5","fromNode": "evidence","toNode": "ppv","fromSide": "right","toSide": "left"},
    {"id": "e6","fromNode": "ppv","toNode": "authority","fromSide": "right","toSide": "left"},
    {"id": "e7","fromNode": "authority","toNode": "next","fromSide": "right","toSide": "left","label": "route only"}
  ],
  "metadata": {"title": "Current Work Object and Queue — Three-Stream Wave","snapshot": "2026-08-02T00:45:00+10:00","work_object_id": "WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001","status": "current_ready_to_send","authority": "BOUNDED_PREPARATION_ACTIVE_PRODUCTION_HELD","source": "Working Memory controller + accepted Navigator","freshness": "2026-08-02T00:45:00+10:00","evidence": "SUFFICIENT_FOR_CONTROLLED_LAUNCH_PREPARATION","ppv": "Potential","replay_validity": "PRESERVED","return_route": "NAVIGATOR_MVP_PRIMARY_HOME_CANDIDATE_v0.2.md","current_delivery": "CURRENT_DELIVERY.md"}
}''',
    "15_INTEGRATED_DRILLDOWN_RETURN.canvas": r'''{
  "nodes": [
    {"id": "n1","type": "text","text": "Navigator Home\n[[NAVIGATOR_MVP_PRIMARY_HOME_CANDIDATE_v0.2]]","x": 0,"y": 0,"width": 320,"height": 160},
    {"id": "n2","type": "text","text": "Services\n[[SERVICE_CATALOGUE_PROJECTION_v0.2]]","x": 360,"y": 0,"width": 320,"height": 160},
    {"id": "n3","type": "text","text": "Patterns\n[[PATTERN_LIBRARY_PROJECTION_v0.1]]","x": 720,"y": 0,"width": 320,"height": 160},
    {"id": "n4","type": "text","text": "Methods\n[[METHOD_LIBRARY_PROJECTION_v0.2]]","x": 1080,"y": 0,"width": 320,"height": 160},
    {"id": "n5","type": "text","text": "Canonical\n[[CANONICAL_LIBRARY_PROJECTION_v0.2]]","x": 0,"y": 220,"width": 320,"height": 160},
    {"id": "n6","type": "text","text": "Benefits / Assets\n[[BENEFIT_ASSET_PROJECTION_v0.1]]","x": 360,"y": 220,"width": 320,"height": 160},
    {"id": "n7","type": "text","text": "Context / Work Object\n[[CONTEXT_WORK_OBJECT_PROJECTION_v0.1]]","x": 720,"y": 220,"width": 320,"height": 160},
    {"id": "n8","type": "text","text": "Dashboard\nNAVIGATOR_MVP_PRIMARY_DASHBOARD_CANDIDATE_v0.2.html","x": 1080,"y": 220,"width": 320,"height": 160},
    {"id": "control_v02","type": "text","text": "NAVIGATOR CONTROL / RETURN\nSnapshot: 2026-08-01T23:17:00+10:00\nProjection source: Odoo read-only registers + SharePoint Working Memory + v0.2 correction evidence\nFreshness: Odoo Canonical Library refreshed 2026-08-01; other register counts inherited from verified v0.1 snapshot\nEvidence: SUFFICIENT_FOR_CANDIDATE_REASSURANCE; live-vault route and independent cold-start remain open\nPPV: Potential\nAuthority: HELD — no adoption, runtime, register, canon, Service, Pattern, Method, asset or PPV mutation\nStatus: candidate / static / not current\nReplay-validity: PRESERVED_WITH_CONDITIONS\nReturn: [[NAVIGATOR_MVP_PRIMARY_HOME_CANDIDATE_v0.2]]","x": 0,"y": 460,"width": 760,"height": 340}
  ],
  "edges": [
    {"id": "e1","fromNode": "n1","toNode": "n2","fromSide": "right","toSide": "left","label": "drill"},
    {"id": "e2","fromNode": "n1","toNode": "n3","fromSide": "right","toSide": "left","label": "drill"},
    {"id": "e3","fromNode": "n1","toNode": "n4","fromSide": "right","toSide": "left","label": "drill"},
    {"id": "e4","fromNode": "n1","toNode": "n5","fromSide": "right","toSide": "left","label": "drill"},
    {"id": "e5","fromNode": "n1","toNode": "n6","fromSide": "right","toSide": "left","label": "drill"},
    {"id": "e6","fromNode": "n1","toNode": "n7","fromSide": "right","toSide": "left","label": "drill"},
    {"id": "e7","fromNode": "n1","toNode": "n8","fromSide": "right","toSide": "left","label": "open"},
    {"id": "e8","fromNode": "n2","toNode": "n1","fromSide": "right","toSide": "left","label": "return"},
    {"id": "e9","fromNode": "n3","toNode": "n1","fromSide": "right","toSide": "left","label": "return"},
    {"id": "e10","fromNode": "n4","toNode": "n1","fromSide": "right","toSide": "left","label": "return"},
    {"id": "e11","fromNode": "n5","toNode": "n1","fromSide": "right","toSide": "left","label": "return"},
    {"id": "e12","fromNode": "n6","toNode": "n1","fromSide": "right","toSide": "left","label": "return"},
    {"id": "e13","fromNode": "n7","toNode": "n1","fromSide": "right","toSide": "left","label": "return"}
  ],
  "metadata": {"title": "Integrated Drill-down and Return","snapshot": "2026-08-01T23:17:00+10:00","work_object_id": "WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001","status": "candidate_not_current","authority": "HELD","source": "Odoo read-only + Working Memory","projection_source": "Odoo read-only registers + SharePoint Working Memory + v0.2 correction evidence","freshness": "2026-08-01 snapshot-bound","evidence": "SUFFICIENT_FOR_CANDIDATE_REASSURANCE; LIVE_VAULT_AND_FRESH_REVIEW_OPEN","ppv": "Potential","replay_validity": "PRESERVED_WITH_CONDITIONS","return_route": "NAVIGATOR_MVP_PRIMARY_HOME_CANDIDATE_v0.2.md"}
}''',
}


def parsed() -> dict:
    """Return {filename: parsed_dict} for all 15 accepted canvases."""
    return {name: json.loads(text) for name, text in RAW_CANVAS_JSON.items()}
