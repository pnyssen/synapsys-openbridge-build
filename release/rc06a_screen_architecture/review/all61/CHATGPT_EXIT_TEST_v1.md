# ChatGPT Navigator consumption exit test (v1) - source candidate, not installed

Producer self-test is NOT acceptance. Acceptance is the ChatGPT-side run of the steps below, by D009/Navigator, with fresh read-only reads.

## Frozen inputs (verify hashes first; a mismatch is HOLD, not a warning)
- GitHub: pnyssen/synapsys-openbridge-build, branch claude/synapsys-v20-release-service-tvjpyn, the commit named in the filed return.
- Contract: release/rc06a_screen_architecture/review/all61/navigator_integration_contract.json (schema synapsys.navigator.integration-contract.v1).
- Reconciler: review/all61/navigator_contract.py (functions reconcile, correction_request). Tests: review/all61/test_navigator_contract.py.

## Interface (no endpoint; a document + a pure function)
reconcile(contract, live, pins, actor) -> {menus:{id:{verdict,defects,holds,evidence}}, summary, total}
live = {menus:{id:{name_path,parent,action,model,domain}}, fields:{model:{field:{relation,type}}}, verbs:[names]}   (RC-1, RC-2 reads)
actor = {name, role, visible_menu_ids, leaked_ids}  (RC-4; absent => every menu HOLD ACTOR_READ_NOT_SUPPLIED)
Verdicts: ACCEPT | RETURN_DEFECTS | HOLD. HOLD is never promoted to ACCEPT. ACCEPT means source and live agree for that menu; it is not installation, role-test or Outcome acceptance.

## Steps
1. Fetch the 61 live menus (49 window, 3 client, 9 container) and the 52 action routes via V20 MCP odoo20_search_read (ir.ui.menu, ir.actions.act_window, ir.actions.client); fields via odoo20_fields_get for each model in the contract.
2. Resolve each menu by menu_id + name_path + action_ref in the contract; confirm counts 61/49/3/9 and 27 verbs.
3. Compare live vs contract per menu; add the actor read if available (Steward/Collaborator/Client reads are a MISSING contract, RC-4).
4. Positive: with unmodified reads expect 0 RETURN_DEFECTS where live equals source; sparse/restricted/not-tested menus stay HOLD.
5. Negative (fixture defect): alter ONE copy of the live bundle (e.g. change menu 179 name_path, delete synapsys.work.object.service_id, or drop a verb). The run MUST return RETURN_DEFECTS for that menu with a named code and owner. If it does not, the consumer has failed the test.
6. Produce per-menu ACCEPT / RETURN_DEFECTS / HOLD with evidence and owner, then correction_request(...): ONE non-mutating D007 request (mutating=false, executes=false, executor_claimed=false).

## Missing read contracts (named, not active): RC-3 ir.rule/ir.model.access; RC-4 per-role counts/visibility; RC-5 privileged census. Owner: D007 connector read scope, on Steward word.
