"""ONE machine-readable Navigator integration contract over the ALL61 matrix, plus the deterministic reconciler a ChatGPT-side
Navigator runs against FRESH read-only V20 reads (source-only candidate; not installed; not an endpoint; no network, no Odoo, no writes).

build_contract()  -> the contract (schema synapsys.navigator.integration-contract.v1). Derived ONLY from the pinned ALL61 matrix,
                     baseline and live snapshot. It invents no relationship, verb, Method, Work or Outcome; absent = stated absent.
reconcile()       -> per-menu ACCEPT / RETURN_DEFECTS / HOLD with evidence and owner, from a live bundle (same shape the V20 MCP
                     reads produce) compared with the contract. HOLD is never converted to ACCEPT. Structural coverage, relationship
                     coverage and operating qualification stay three separate projections.
"""
import hashlib
import json

SCHEMA = 'synapsys.navigator.integration-contract.v1'
VERDICTS = ('ACCEPT', 'RETURN_DEFECTS', 'HOLD')
REL_STATES = ('BOUND', 'MISSING_REQUIRED', 'NOT_APPLICABLE', 'SOURCE_UNVERIFIED', 'INACCESSIBLE_REDACTED')
OWNERS = {'source': 'Claude Code builder (source) -> D009 challenge', 'live_drift': 'D007 release (correction request) after D001 decision',
          'rights': 'D001/D002 ruling; D007 release', 'semantic': 'D001/D002', 'read_contract': 'D007 (connector read scope) on Steward word'}

# Reads a ChatGPT-side Navigator needs. 'ACTIVE_VERIFIED' only where this session actually used it; the rest are named gaps, not endpoints.
READ_CONTRACTS = [
    {'id': 'RC-1', 'need': 'ir.ui.menu + ir.actions.act_window/client rows (identity, parent, action, model, domain, view_mode)', 'via': 'V20 MCP odoo20_search_read',
     'state': 'ACTIVE_VERIFIED_THIS_SESSION_READONLY', 'owner': None},
    {'id': 'RC-2', 'need': 'ir.model.fields per model (field presence/type/relation/cardinality)', 'via': 'V20 MCP odoo20_fields_get',
     'state': 'ACTIVE_VERIFIED_THIS_SESSION_READONLY', 'owner': None},
    {'id': 'RC-3', 'need': 'ir.rule and ir.model.access rows (actual rights, record rules)', 'via': 'none verified: V20 MCP cannot read them',
     'state': 'MISSING_READ_CONTRACT', 'owner': OWNERS['read_contract']},
    {'id': 'RC-4', 'need': 'actor-specific counts and menu visibility for Steward, Collaborator and Client sessions', 'via': 'none: only jq003.readonly exists; no role sessions',
     'state': 'MISSING_READ_CONTRACT', 'owner': OWNERS['read_contract']},
    {'id': 'RC-5', 'need': 'privileged record census (administrator counts, to tell empty from hidden)', 'via': 'none authorised',
     'state': 'MISSING_READ_CONTRACT', 'owner': OWNERS['read_contract']},
    {'id': 'RC-6', 'need': 'pinned GitHub source at a frozen commit + WM contract/hash', 'via': 'GitHub connector; SharePoint MCP sp_read/sp_read_bytes',
     'state': 'ACTIVE_VERIFIED_THIS_SESSION_READONLY', 'owner': None},
]


def sha(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def _card(field):
    return 'many' if field.endswith('_ids') else 'one'


def _edge(spec):
    fld, _, tgt = spec.partition('->')
    return {'field': fld, 'target_model': tgt, 'direction': 'out', 'cardinality': _card(fld)}


def _maturity(row):
    st = row.get('status')
    return {'status': st, 'source': row.get('source_status'), 'definition_state': row.get('definition_state'),
            'level': {'PASS': 'SOURCE_READY', 'REUSED_PASS': 'SOURCE_READY', 'HONEST_HOLD': 'HOLD', 'RESTRICTED': 'RESTRICTED_NOT_OBSERVED',
                      'NOT_TESTED': 'NOT_TESTED', 'RELEASE_BLOCKED': 'RELEASE_BLOCKED'}.get(st, 'UNKNOWN'),
            'installed': 'NOT_ASSERTED', 'role_tested': 'NOT_TESTED', 'operationally_verified': 'NOT_VERIFIED'}


def build_contract(rows, snapshot, baseline_sha256, source_pins):
    """rows: build_matrix.build(...) rows (61). snapshot: live_snapshot. source_pins: {name: sha256/commit}."""
    verbs = [v['name'] for v in snapshot['verbs']]
    restricted = snapshot.get('restricted_models', {})
    menus = {}
    for r in rows:
        mid = r['menu_id']
        edges = [_edge(e) for e in (r.get('edges_out') or [])]
        menus[str(mid)] = {
            'identity': {'menu_id': mid, 'name_path': r['path'], 'parent_id': r.get('parent_id'), 'kind': r['menu_kind'],
                         'action_ref': r.get('live_action'), 'action_id': r.get('action_id'), 'action_type': r.get('action_type'),
                         'client_tag': None if r['menu_kind'] != 'CLIENT_ACTION' else 'UNREAD_FROM_V20_RC1_REQUIRED'},
            'view': {'model': r.get('model'), 'domain': r.get('domain'), 'view_mode': r.get('view_mode')},
            'fields': [e['field'] for e in edges],
            'source': {'status': r.get('source_status'), 'definition_state': r.get('definition_state'), 'source_element_id': r.get('source_element_id'),
                       'definition_gap': r.get('definition_gap'), 'baseline_sha256': baseline_sha256},
            'relationships': edges,
            'relationship_states_default': 'SOURCE_UNVERIFIED' if edges else 'NOT_APPLICABLE',
            'rights': {'steward_only': bool((r.get('actors') or {}).get('steward_only')), 'model_restricted_for_observer':
                       r.get('model') in restricted, 'role_sessions': 'NOT_TESTED', 'redaction': 'counts/ids of invisible rows must not appear'},
            'ffe': r.get('ffe') or {'state': 'NOT_PROJECTED_IN_ROW', 'via': 'arch_graph.project (shared resolver)'},
            'verbs': {'governed_set_size': len(verbs), 'applicable': 'UNBOUND_NO_SOURCE_MAPPING', 'note': 'no per-menu verb mapping is in source; none invented'},
            'operating': {'service_links': [e['field'] for e in edges if e['target_model'] == 'synapsys.service'],
                          'method_links': [e['field'] for e in edges if e['target_model'] == 'synapsys.method'],
                          'work_links': [e['field'] for e in edges if e['target_model'] == 'synapsys.work.object'],
                          'outcome_links': [e['field'] for e in edges if e['target_model'] == 'synapsys.outcome'],
                          'record_state': r.get('record_state')},
            'evidence_maturity': _maturity(r),
            'exceptions': [x for x in (r.get('status_reason'), r.get('definition_gap'), r.get('negative_test')) if x],
            'qualification': {'structural': 'FROM_SOURCE', 'relationship': 'SOURCE_UNVERIFIED' if edges else 'NOT_APPLICABLE', 'operating': 'NOT_VERIFIED'},
            'tests': r.get('tests') or [],
        }
    c = {'schema': SCHEMA, 'status': 'SOURCE_READY_NOT_INSTALLED', 'read_only': True, 'writes': 0,
         'counts': {'menus': len(menus), 'act_window': sum(1 for r in rows if r['menu_kind'] == 'ACT_WINDOW'),
                    'client': sum(1 for r in rows if r['menu_kind'] == 'CLIENT_ACTION'), 'container': sum(1 for r in rows if r['menu_kind'] == 'CONTAINER'),
                    'verbs': len(verbs)},
         'verbs': verbs, 'source_pins': source_pins, 'read_contracts': READ_CONTRACTS, 'menus': menus,
         'not_asserted': ['installation', 'role tests', 'Realisation', 'Outcome acceptance', 'any endpoint named here being active']}
    c['contract_sha256_over_menus'] = sha(menus)
    return c


# ---------------------------------------------------------------------------------------------------------------- reconcile
def _d(code, owner, evidence, label=None):
    return {'code': code, 'owner': OWNERS[owner], 'evidence': evidence, 'label': label or 'DEFECT'}


def reconcile(contract, live, pins=None, actor=None):
    """live = {'menus': {id: {'name_path','parent','action','model','domain','view_mode'}}, 'fields': {model: {field: {'relation','type'}}},
              'verbs': [names]}. actor (optional) = {'name','role','visible_menu_ids':[...],'counts':{menu_id: n}, 'leaked_ids': [...]}.
    Returns {menu_id: {'verdict','defects','holds','evidence'}} and a summary. Deterministic: same inputs, same output."""
    out, verbs_ok = {}, sorted(live.get('verbs') or []) == sorted(contract['verbs'])
    seen_model = {}
    for mid, c in contract['menus'].items():
        L = (live.get('menus') or {}).get(mid)
        defects, holds, ev = [], [], {}
        if L is None:
            defects.append(_d('MENU_MISSING_LIVE', 'live_drift', {'menu_id': mid}))
        else:
            if L.get('name_path') != c['identity']['name_path']:
                defects.append(_d('IDENTITY_PATH_DRIFT', 'live_drift', {'expected': c['identity']['name_path'], 'live': L.get('name_path')}))
            if L.get('parent') != c['identity']['parent_id']:
                defects.append(_d('PARENT_DRIFT', 'live_drift', {'expected': c['identity']['parent_id'], 'live': L.get('parent')}))
            if L.get('action') != c['identity']['action_ref']:
                defects.append(_d('ACTION_DRIFT', 'live_drift', {'expected': c['identity']['action_ref'], 'live': L.get('action')}))
            m = c['view']['model']
            if m:
                if L.get('model') != m:
                    defects.append(_d('MODEL_DRIFT', 'live_drift', {'expected': m, 'live': L.get('model')}))
                if (L.get('domain') or None) != (c['view']['domain'] or None):
                    defects.append(_d('DOMAIN_DRIFT', 'live_drift', {'expected': c['view']['domain'], 'live': L.get('domain')}))
                seen_model.setdefault(m, []).append(mid)
                fl = (live.get('fields') or {}).get(m)
                for e in c['relationships']:
                    if fl is None:
                        holds.append({'code': 'FIELDS_NOT_READ', 'owner': OWNERS['read_contract'], 'evidence': {'model': m}}); break
                    f = fl.get(e['field'])
                    if f is None:
                        defects.append(_d('FIELD_MISSING_LIVE', 'live_drift', {'model': m, 'field': e['field']}))
                    elif f.get('relation') != e['target_model']:
                        defects.append(_d('RELATION_TARGET_DRIFT', 'live_drift', {'field': e['field'], 'expected': e['target_model'], 'live': f.get('relation')}))
        if not verbs_ok:
            defects.append(_d('VERB_SET_DRIFT', 'source', {'expected': len(contract['verbs']), 'live': len(live.get('verbs') or [])}))
        if pins and pins.get('contract_sha256_over_menus') not in (None, contract['contract_sha256_over_menus']):
            defects.append(_d('SOURCE_DRIFT', 'source', {'pinned': pins['contract_sha256_over_menus'], 'actual': contract['contract_sha256_over_menus']}))
        if actor is not None:
            vis = set(str(x) for x in actor.get('visible_menu_ids') or [])
            if c['rights']['steward_only'] and actor.get('role') != 'steward' and mid in vis:
                defects.append(_d('NEGATIVE_PERMISSION_BREACH', 'rights', {'actor': actor.get('name'), 'role': actor.get('role'), 'menu_id': mid}))
            if mid in set(str(x) for x in actor.get('leaked_ids') or []):
                defects.append(_d('REDACTION_LEAK', 'rights', {'menu_id': mid}))
        else:
            holds.append({'code': 'ACTOR_READ_NOT_SUPPLIED', 'owner': OWNERS['read_contract'], 'evidence': {'contract': 'RC-4'}})
        if c['operating']['record_state'] in ('UNOBSERVED_ZERO_VISIBLE', 'UNOBSERVED'):
            holds.append({'code': 'SPARSE_NOT_OBSERVED', 'owner': OWNERS['semantic'], 'evidence': {'record_state': c['operating']['record_state']}})
        if c['evidence_maturity']['level'] in ('HOLD', 'RESTRICTED_NOT_OBSERVED', 'NOT_TESTED', 'RELEASE_BLOCKED'):
            holds.append({'code': 'MATURITY_' + c['evidence_maturity']['level'], 'owner': OWNERS['semantic'], 'evidence': {'status': c['evidence_maturity']['status']}})
        verdict = 'RETURN_DEFECTS' if defects else 'HOLD' if holds else 'ACCEPT'
        out[mid] = {'verdict': verdict, 'defects': defects, 'holds': holds, 'evidence': {'path': c['identity']['name_path'], 'operating': 'NOT_VERIFIED'}}
    for m, ids in seen_model.items():                    # cross-menu identity: menus on one model must resolve to the same object type
        if len(ids) > 1:
            for i in ids:
                out[i].setdefault('cross_menu', {'model': m, 'same_object_as': sorted(x for x in ids if x != i)})
    summary = {v: sum(1 for x in out.values() if x['verdict'] == v) for v in VERDICTS}
    return {'menus': out, 'summary': summary, 'total': len(out)}


def correction_request(result, contract_sha):
    """ONE exact NON-MUTATING D007 correction request (a request document; executes nothing, claims no executor)."""
    items = [{'menu_id': m, 'defects': [d['code'] for d in x['defects']], 'owner': sorted({d['owner'] for d in x['defects']})}
             for m, x in sorted(result['menus'].items(), key=lambda kv: int(kv[0])) if x['verdict'] == 'RETURN_DEFECTS']
    return {'type': 'D007_CORRECTION_REQUEST', 'mutating': False, 'executes': False, 'executor_claimed': False,
            'contract_sha256_over_menus': contract_sha, 'items': items, 'requires': ['D001 decision', 'D007 release', 'RUN_LOCK', 'prestate', 'rollback', 'readback']}
