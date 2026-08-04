# R1 candidate build notes (scratch, not filed)

Work Object: WO-NAV-R1-V1.5-VISUAL-ROLE-CORRECTION-001
Parent: WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001
Authority: candidate-build only. NO current-path mutation, NO Odoo/N8N/runtime mutation.

## Seven required corrections
- C1 cold-start position: remove default #operate auto-select + auto-scroll on load
- C2 mobile priority/element layout: fix @media(max-width:1180px) override that
  breaks the single-column mobile rule
- C3 persistent operating identity header: role/context/plane/WO/PPV/authority/
  source-freshness/STOP-HOLD, static, no live ACL simulation
- C4 non-Steward fail-closed disclosure: governance/project/benefit owner = internal
  governed; collaborator/client = NOT available via this surface, fail-closed
- C5 one current next action: single "Current next action" field, others labelled
  supporting/held
- C6 direct return continuity: add Navigator/Home return to the 5 v1.3 element pages
  that lack it (Mesh & Control Gates, Benefits & Assets, Current Work Object & Queue,
  Context & Membrane, Agent & Runtime Routing) - confirm other 4 already have it
- C7 route registry lineage (candidate copy only): 9/9 element refs -> v1.3 filenames

## Acceptance ceiling
CANDIDATE_PATCH_TESTED__READY_FOR_HUB_REVIEW__NO_CURRENT_MUTATION
(never: accepted / current / deployed / final-locked / Round-2-ready)

## Deliverables (exactly)
1. NAVIGATOR_R1_CURRENT_V1_5_BOUNDED_CORRECTION_CANDIDATE_v1.0.zip
   - candidate files only
   - MANIFEST_SHA256.csv
   - unified diff (source -> candidate) per file
   - browser test evidence (desktop+mobile+route, screenshots + JSON)
2. NAVIGATOR_R1_CURRENT_V1_5_BOUNDED_CORRECTION_RETURN_v1.0.md
   (MULTI_LANE_MM3CCC_RETURN_PROFILE)

File to:
05_AI_RETURNS_HASHED/WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001/
NAVIGATOR_ROUND1_BASELINE_ROLE_MEMBRANE_LOCK_v1.0/
NAVIGATOR_R1_CURRENT_V1_5_BOUNDED_CORRECTION_CANDIDATE_v1.0/

## Escalation triggers (STOP, return to Hub, don't build further) — none of these
apply based on the WO text; all 7 corrections are presentation/lineage bounded.
