# OBSERVATION: RC05 scaffold route called by a real Steward session on dev V20 (26 Nov 2026)
Work Object WO-SYNAPSYS-CANONICAL-REFERENCE-ARCHITECTURE-001 | CTX-SS | Status: OBSERVED (Steward path only). Not D007, not D009, not Steward acceptance. Costs: no user created.

## What was run
The Steward, logged in as themselves at https://odoo20.srv1536619.hstgr.cloud/odoo/action-332, ran two fetch() POSTs from the Chrome DevTools Console against /synapsys/scaffold/context (installed per RECEIPT_CC_RC05_DEV_INSTALL_20261126_v1.md, sha256 740114124072cd79c75acf34753cbeb349bc48fda7ef07388140943438d8c9b8). Output was pasted into chat by the Steward (first output truncated by the Steward's 3,500-character slice; the registry_sha and state fields fell outside it).

## Observed
1. depth=enrich, context_id=1: result OK; registry_version 0.3.5; noun N.CONTEXT (RULED); depth_requested enrich, depth_effective enrich, depth_clamped false; writes 0. Seven H.CTX roles from cluster MC-390147223f2d in order: context (required), purpose (required), rights_holder (required), then intersects+, portfolio+, shape, strategy+, each with its bound noun and status (Purpose and Partner PROPOSAL, Chain PROPOSAL, Portfolio/Shape/Strategy/Context RULED). Peers: N.CAPABILITY PROPOSAL and N.SERVICE RULED, both operating_source NO_OPERATING_SOURCE, hold true, evidence [], rejected_evidence []; open_questions present (3 and 2 items); definitions and definition_source present.
2. depth=deep: result REFUSED, reason UNKNOWN_DEPTH.

## Compared with the offline expectation (same registry body, Claude Code run)
Role ids, required/many flags, bound ids, bound statuses, ordering, peer statuses, hold flags, empty evidence and open-question counts (3, 2) all equal. No difference found in the fields compared.

## What this establishes, and what it does not
Established: on dev V20 the route is registered, runs under a real Steward session with the caller's own rights, reads the 0.3.5 registry, and returns the expected read-only projection and refusal. Not established: Collaborator or portal behaviour (Option A: portal users are not served and are expected to be refused; untested), the no-read-right path in a real Odoo, the registry hash match in a live call (outside the slice), any UI, 390px/1024px, navigation. The existing /synapsys/lenses/data route remains open to any logged-in user (D6); this work does not change it.

## ONE NEXT
Steward decision on what to build on this: the screen (Architecture > Lenses N.CONTEXT view, needs lens_render.py and home.js from the box) or a library/evidence source (name the registered SC-04 or GV-NAV-002 Method and one authoritative library record). Remove the SSH key in hPanel when done.
