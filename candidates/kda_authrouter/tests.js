const { runNode } = require('./harness.js'); const fs = require('fs');
const BASE = process.argv[2] || 'base_code.js', CAND = process.argv[3] || 'candidate_code.js';
const NOW = '2026-11-29T00:00:00Z';
const WO = 'WO-SYNAPSYS-CANONICAL-REFERENCE-ARCHITECTURE-001';
const exact448037 = {work_object_id:WO,state_revision:56,rollback:'NO_OP__ROUTER_READ_ONLY',expected_return:'NONE__DIAGNOSTIC_RESPONSE_ONLY',requested_action:'LOCAL_KDA_TRANSPORT_CONFORMANCE_NONMUTATING',authority_source:'STEWARD',authority_reference:'TEST_ONLY_NO_SUCH_APPROVAL_20261128',scope:'TEST_A__INVALID_REFERENCE_MUST_NOT_GRANT_AUTHORITY'};
const exact448038 = Object.assign({}, exact448037, {authority_source:'D007'});
const REC = (o={}) => Object.assign({id:9001,x_reference:'TEST_ONLY_CHG_FIXTURE_P1',x_approval_status:'approved',x_active:true,x_approved_by:[5,'Fixture Signatory'],x_approval_route:'d001_steward',x_context_id:[1,'CTX-SS'],
  x_execution_brief:'TEST_ONLY FIXTURE - NOT A REAL APPROVAL\nPERMITTED_ACTIONS: LOCAL_KDA_TRANSPORT_CONFORMANCE_NONMUTATING\nPERMITTED_TARGETS: '+WO+'\nVALID_UNTIL: 2026-12-31T00:00:00Z\nSTATE_REVISION: 56',x_description:''}, o);
const L = (...rows) => ({result: rows});
const P1in = Object.assign({}, exact448037, {authority_reference:'TEST_ONLY_CHG_FIXTURE_P1', context_id:'CTX-SS', scope:'TEST_ONLY'});
const cases = [];
const add = (id, name, payload, lookup, expect, now=NOW) => cases.push({id,name,payload,lookup,expect,now});
add('N1','invented STEWARD reference (exact 448037 input), no such record', exact448037, L(), r => r.status==='HOLD_UNKNOWN_OR_UNATTESTED_AUTHORITY' && r.activation_layers===null);
add('N2','D007 self-authorisation (exact 448038 input)', exact448038, L(), r => r.status==='HOLD_INVALID_AUTHORITY_SOURCE' && r.activation_layers===null);
add('N3','real approved record, wrong Context', P1in, L(REC({x_context_id:[2,'CTX-BASIN']})), r => r.status==='HOLD_UNKNOWN_OR_UNATTESTED_AUTHORITY' && r.activation_layers===null);
add('N4','real approved record, requested_action out of scope', Object.assign({},P1in,{requested_action:'DEPLOY_WORKFLOW'}), L(REC()), r => r.status==='HOLD_UNKNOWN_OR_UNATTESTED_AUTHORITY' && r.activation_layers===null);
add('N5a','record expired', P1in, L(REC()), r => r.status==='HOLD_UNKNOWN_OR_UNATTESTED_AUTHORITY' && r.activation_layers===null, '2027-01-01T00:00:00Z');
add('N5b','record revoked (x_active=false)', P1in, L(REC({x_active:false})), r => r.status==='HOLD_UNKNOWN_OR_UNATTESTED_AUTHORITY' && r.activation_layers===null);
add('N5c','record no longer approved (rejected)', P1in, L(REC({x_approval_status:'rejected'})), r => r.status==='HOLD_UNKNOWN_OR_UNATTESTED_AUTHORITY' && r.activation_layers===null);
add('N6a','lookup error', P1in, {error:'timeout'}, r => r.status==='HOLD_UNKNOWN_OR_UNATTESTED_AUTHORITY' && r.activation_layers===null);
add('N6b','lookup returns nothing usable', P1in, null, r => r.status==='HOLD_UNKNOWN_OR_UNATTESTED_AUTHORITY' && r.activation_layers===null);
add('N6c','ambiguous: two records', P1in, L(REC(),REC({id:9002})), r => r.status==='HOLD_UNKNOWN_OR_UNATTESTED_AUTHORITY' && r.activation_layers===null);
add('N7','signatory seat mismatch (record route is not Steward)', P1in, L(REC({x_approval_route:'d007_release'})), r => r.status==='HOLD_UNKNOWN_OR_UNATTESTED_AUTHORITY' && r.activation_layers===null);
add('N8','record bound to a different state revision', P1in, L(REC({x_execution_brief:REC().x_execution_brief.replace('STATE_REVISION: 56','STATE_REVISION: 55')})), r => r.status==='HOLD_UNKNOWN_OR_UNATTESTED_AUTHORITY' && r.activation_layers===null);
add('N9','record returned for a different reference (no fuzzy match)', P1in, L(REC({x_reference:'TEST_ONLY_CHG_FIXTURE_OTHER'})), r => r.status==='HOLD_UNKNOWN_OR_UNATTESTED_AUTHORITY' && r.activation_layers===null);
add('N10','no attributable signatory', P1in, L(REC({x_approved_by:false})), r => r.status==='HOLD_UNKNOWN_OR_UNATTESTED_AUTHORITY' && r.activation_layers===null);
add('N11','record with no machine-readable scope or expiry (e.g. a real CHG as written today)', P1in, L(REC({x_execution_brief:'plain prose only'})), r => r.status==='HOLD_UNKNOWN_OR_UNATTESTED_AUTHORITY' && r.activation_layers===null);
add('N12','payload without Context', Object.assign({},P1in,{context_id:undefined}), L(REC()), r => r.status==='HOLD_UNKNOWN_OR_UNATTESTED_AUTHORITY' && r.activation_layers===null);
add('N13','missing field still reported first', Object.assign({},P1in,{rollback:''}), L(REC()), r => r.status==='HOLD_MISSING_AUTHORITY_FIELDS' && r.activation_layers===null);
add('N14','requested target (work_object_id) outside the record scope', P1in, L(REC({x_execution_brief:REC().x_execution_brief.replace(WO,'WO-SOME-OTHER-OBJECT')})), r => r.status==='HOLD_UNKNOWN_OR_UNATTESTED_AUTHORITY' && r.activation_layers===null);
add('N15','scoped record with no VALID_UNTIL bound (unbounded approval not accepted)', P1in, L(REC({x_execution_brief:REC().x_execution_brief.replace(/VALID_UNTIL.*\n?/,'')})), r => r.status==='HOLD_UNKNOWN_OR_UNATTESTED_AUTHORITY' && r.activation_layers===null);
add('N16','malformed lookup row (evaluation throws)', P1in, L(null), r => r.status==='HOLD_UNKNOWN_OR_UNATTESTED_AUTHORITY' && r.activation_layers===null);
add('P1','genuine approved, in-scope, in-date TEST_ONLY fixture', P1in, L(REC()), r => r.status==='AUTHORITY_PACKET_VALID' && r.activation_layers && Object.keys(r.activation_layers).sort().join()==='D007,D008,D009,Navigator' && Object.values(r.activation_layers).every(x=>x.decision_authority===false) && r.authority_created===false);
let fail = 0, detFail = 0;
const out = [];
for (const [label, code] of [['BASE (unpatched b35dbd2c)', BASE], ['CANDIDATE', CAND]]) {
  out.push('== '+label);
  for (const c of cases) {
    let r; try { r = runNode(code, c.payload, c.lookup, c.now); } catch (e) { r = {status:'EXCEPTION:'+e.message, activation_layers:'n/a'}; }
    const ok = !!c.expect(r);
    const isBase = label.startsWith('BASE');
    // On the base, N1/N3-N13 are EXPECTED to fail (that reproduces the original defect); N2 and N13(missing field) must already hold.
    const baseExpectedPass = new Set(['N2','N13','P1']);
    const verdict = isBase ? (ok === baseExpectedPass.has(c.id) ? (ok?'PASS (control: base already behaves this way)':'FAIL AS EXPECTED (defect reproduced)') : 'UNEXPECTED') : (ok?'PASS':'FAIL');
    if (verdict==='UNEXPECTED' || (!isBase && !ok)) fail++;
    out.push(`${c.id.padEnd(4)} ${verdict.padEnd(42)} status=${r.status} reason=${r.hold_reason||'-'} layers=${r.activation_layers? 'NON_NULL':'null'}  :: ${c.name}`);
  }
}
// determinism: two identical runs -> byte-identical output
for (const c of cases) { const a = JSON.stringify(runNode(CAND,c.payload,c.lookup,c.now)), b = JSON.stringify(runNode(CAND,c.payload,c.lookup,c.now)); if (a!==b) { fail++; detFail++; out.push('DETERMINISM FAIL '+c.id); } }
out.push('DETERMINISM: '+cases.length+' cases x2 identical runs -> '+(detFail?'DIFFERENCES FOUND':'byte-identical'));
// fidelity: base transcription reproduces the recorded 448037 live result
const r0 = runNode(BASE, exact448037, null, NOW);
const fid = r0.status==='AUTHORITY_PACKET_VALID' && r0.activation_layers && r0.replay_validity==='AUTHORITY_EXTERNAL__ACTIVATION_LAYERS_NON_AUTHORISING__FAIL_CLOSED' && r0.authority_created===false;
out.push('BASE FIDELITY vs recorded execution 448037 (AUTHORITY_PACKET_VALID, 4 activation layers): '+(fid?'REPRODUCED':'NOT REPRODUCED')); if(!fid) fail++;
out.push(fail? 'RESULT: FAIL ('+fail+')':'RESULT: ALL AS EXPECTED');
console.log(out.join('\n')); process.exit(fail?1:0);
