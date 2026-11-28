// Candidate: fail-closed authority validation. Order: missing fields -> existing D007/AI denylist (unchanged, first) -> register checks (a)-(e).
const FWD = 'HOLD_UNKNOWN_OR_UNATTESTED_AUTHORITY';
// Payload comes from the webhook node, NOT from $input (in this wiring $input is the register-lookup output).
const p=$('Authority Packet In').first().json?.body||$('Authority Packet In').first().json||{};
const req=['work_object_id','state_revision','authority_source','authority_reference','scope','requested_action','rollback','expected_return'];
const missing=req.filter(k=>p[k]===undefined||p[k]===null||p[k]==='');
const authoritySource=String(p.authority_source||'').toUpperCase();
const forbidden=['D007','D008','D009','AI','AGENT','COWORK','CODEX','GEMINI','CLAUDE'];
const selfAuth=forbidden.includes(authoritySource);

// ---- authoritative register check: Odoo x_ss_change_request, looked up by x_reference == authority_reference ----
// Seat map: the approval route that makes a signatory the holder of a seat. Anything unmapped fails closed.
const SEAT_BY_ROUTE = { d001_steward: 'STEWARD' };
function marker(text, key) {            // machine-readable binding line, e.g. "PERMITTED_ACTIONS: A, B"
  const m = String(text || '').match(new RegExp('^\\s*' + key + '\\s*:\\s*(.+)$', 'mi'));
  return m ? m[1].split(',').map(s => s.trim()).filter(Boolean) : null;
}
function evaluateRegister() {
  let L;
  try { L = $('Look Up Authority Record').first().json; } catch (e) { return 'LOOKUP_UNAVAILABLE'; }
  if (!L || L.error || L.__lookup_error) return 'LOOKUP_ERROR';
  let rows = L.result;
  if (rows === undefined && Array.isArray(L.records)) rows = L.records;
  if (!Array.isArray(rows)) return 'LOOKUP_BAD_SHAPE';
  if (rows.length === 0) return 'NO_MATCH';
  if (rows.length !== 1) return 'AMBIGUOUS';
  const r = rows[0];
  if (String(r.x_reference || '') !== String(p.authority_reference)) return 'REFERENCE_MISMATCH';   // (a) exact, never fuzzy
  if (r.x_approval_status !== 'approved' || r.x_active === false) return 'NOT_APPROVED_OR_REVOKED';  // (b)(d)
  if (!r.x_approved_by) return 'NO_ATTRIBUTABLE_SIGNATORY';                                          // (b)
  const seat = SEAT_BY_ROUTE[r.x_approval_route];
  if (!seat || seat !== authoritySource) return 'SEAT_MISMATCH';                                      // (b)
  const ctxField = Array.isArray(r.x_context_id) ? r.x_context_id[1] : r.x_context_id;
  const payloadCtx = p.context_id || p.domain_context;
  if (!payloadCtx || String(ctxField) !== String(payloadCtx)) return 'CONTEXT_MISMATCH';              // (c) payload must state its Context
  const text = String(r.x_execution_brief || '') + '\n' + String(r.x_description || '');
  const actions = marker(text, 'PERMITTED_ACTIONS'), targets = marker(text, 'PERMITTED_TARGETS'), until = marker(text, 'VALID_UNTIL');
  if (!actions || !actions.includes(String(p.requested_action))) return 'ACTION_OUT_OF_SCOPE';        // (c)
  if (!targets || !targets.includes(String(p.work_object_id))) return 'TARGET_OUT_OF_SCOPE';          // (c)
  if (!until) return 'NO_EXPIRY_BOUND';                                                               // (d) unbounded approval is not accepted
  const t = Date.parse(until[0]);
  if (!Number.isFinite(t) || new Date().getTime() > t) return 'EXPIRED';                              // (d)
  const rev = marker(text, 'STATE_REVISION');
  if (rev && String(rev[0]) !== String(p.state_revision)) return 'STATE_REVISION_MISMATCH';          // (d) only where bound
  return 'OK';
}
let regReason = null;
let decision;
if (missing.length) decision = 'HOLD_MISSING_AUTHORITY_FIELDS';
else if (selfAuth) decision = 'HOLD_INVALID_AUTHORITY_SOURCE';
else {
  try { regReason = evaluateRegister(); } catch (e) { regReason = 'EVALUATION_ERROR'; }              // (e) any error fails closed
  decision = regReason === 'OK' ? 'AUTHORITY_PACKET_VALID' : FWD;
}
const valid = decision === 'AUTHORITY_PACKET_VALID';
const activation = valid ? {
 D007:{role:'RELEASE_AND_BOUNDED_IMPLEMENTATION',decision_authority:false,instruction:'Validate authority identity/scope, rollback, replay and current state; execute only the authorised mutation envelope; return implementation/readback evidence; never expand scope or create authority.'},
 D008:{role:'INTELLIGENCE_AND_INTERPRETATION',decision_authority:false,instruction:'Provide evidence-backed intelligence, interpretation and options requested by Navigator; do not approve, release, mutate or decide go/no-go.'},
 D009:{role:'INDEPENDENT_ASSURANCE',decision_authority:false,instruction:'Return PASS, PASS_WITH_CONDITIONS or HOLD with evidence and conditions; do not authorise implementation. Navigator routes the result under the pre-existing authority envelope.'},
 Navigator:{role:'CONTROLLER',decision_authority:false,instruction:'Consume authority plus lane returns, preserve state/Goal Anchor, continue eligible work automatically, and return to authority source only for genuinely new or exceeded authority.'}
} : null;
return [{json:{control_marker:'SYNAPSYS_AUTHORITY_TO_ACTIVATION_ROUTER_V1',status:decision,hold_reason:valid?null:(regReason||null),missing_fields:missing,authority_source:p.authority_source||null,authority_reference:p.authority_reference||null,work_object_id:p.work_object_id||null,state_revision:p.state_revision||null,scope:p.scope||null,requested_action:p.requested_action||null,rollback:p.rollback||null,expected_return:p.expected_return||null,activation_layers:activation,authority_created:false,ppv_movement:false,canon_movement:false,replay_validity:valid?'AUTHORITY_REGISTER_RESOLVED__ACTIVATION_LAYERS_NON_AUTHORISING__FAIL_CLOSED':'HOLD__NO_ACTIVATION'}}];
