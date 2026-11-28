const p=$input.first().json?.body||$input.first().json||{};
const req=['work_object_id','state_revision','authority_source','authority_reference','scope','requested_action','rollback','expected_return'];
const missing=req.filter(k=>p[k]===undefined||p[k]===null||p[k]==='');
const authoritySource=String(p.authority_source||'').toUpperCase();
const forbidden=['D007','D008','D009','AI','AGENT','COWORK','CODEX','GEMINI','CLAUDE'];
const selfAuth=forbidden.includes(authoritySource);
const decision=missing.length?'HOLD_MISSING_AUTHORITY_FIELDS':selfAuth?'HOLD_INVALID_AUTHORITY_SOURCE':'AUTHORITY_PACKET_VALID';
const activation=decision==='AUTHORITY_PACKET_VALID'?{
 D007:{role:'RELEASE_AND_BOUNDED_IMPLEMENTATION',decision_authority:false,instruction:'Validate authority identity/scope, rollback, replay and current state; execute only the authorised mutation envelope; return implementation/readback evidence; never expand scope or create authority.'},
 D008:{role:'INTELLIGENCE_AND_INTERPRETATION',decision_authority:false,instruction:'Provide evidence-backed intelligence, interpretation and options requested by Navigator; do not approve, release, mutate or decide go/no-go.'},
 D009:{role:'INDEPENDENT_ASSURANCE',decision_authority:false,instruction:'Return PASS, PASS_WITH_CONDITIONS or HOLD with evidence and conditions; do not authorise implementation. Navigator routes the result under the pre-existing authority envelope.'},
 Navigator:{role:'CONTROLLER',decision_authority:false,instruction:'Consume authority plus lane returns, preserve state/Goal Anchor, continue eligible work automatically, and return to authority source only for genuinely new or exceeded authority.'}
}:null;
return [{json:{control_marker:'SYNAPSYS_AUTHORITY_TO_ACTIVATION_ROUTER_V1',status:decision,missing_fields:missing,authority_source:p.authority_source||null,authority_reference:p.authority_reference||null,work_object_id:p.work_object_id||null,state_revision:p.state_revision||null,scope:p.scope||null,requested_action:p.requested_action||null,rollback:p.rollback||null,expected_return:p.expected_return||null,activation_layers:activation,authority_created:false,ppv_movement:false,canon_movement:false,replay_validity:decision==='AUTHORITY_PACKET_VALID'?'AUTHORITY_EXTERNAL__ACTIVATION_LAYERS_NON_AUTHORISING__FAIL_CLOSED':'HOLD__NO_ACTIVATION'}}];
