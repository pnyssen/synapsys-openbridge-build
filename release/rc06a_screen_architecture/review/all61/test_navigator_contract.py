import copy, json, os, sys, unittest
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import build_contract as B, navigator_contract as N

C = json.load(open(os.path.join(HERE, 'navigator_integration_contract.json')))
SNAP = json.load(open(os.path.join(HERE, 'fixtures', 'live_snapshot.json')))


def clean_live():
    """FIXTURE bundle shaped like fresh V20 reads (RC-1/RC-2), derived from the contract. A real run supplies fresh MCP reads instead."""
    menus, fields = {}, {}
    for mid, c in C['menus'].items():
        i = c['identity']
        menus[mid] = {'name_path': i['name_path'], 'parent': i['parent_id'], 'action': i['action_ref'], 'model': c['view']['model'], 'domain': c['view']['domain'],
                      'view_mode': c['view']['view_mode'], 'client_tag': N.PINNED_CLIENT_TAGS.get(i['action_id']) if i['kind'] == 'CLIENT_ACTION' else None}
        if c['view']['model']:
            fl = fields.setdefault(c['view']['model'], {})
            for e in c['relationships']:
                fl[e['field']] = {'relation': e['target_model'], 'type': 'many2many' if e['cardinality'] == 'many' else 'many2one'}
    return {'menus': menus, 'fields': fields, 'verbs': list(C['verbs'])}


ACTOR_OK = {'name': 'collab', 'role': 'collaborator', 'visible_menu_ids': [], 'leaked_ids': []}


def codes(res, mid): return {d['code'] for d in res['menus'][mid]['defects']}


class Contract(unittest.TestCase):
    def test_shape_and_counts(self):
        self.assertEqual(C['schema'], N.SCHEMA); self.assertEqual(C['counts'], {'menus': 61, 'act_window': 49, 'client': 3, 'container': 9, 'verbs': 27})
        self.assertEqual(len(C['menus']), 61); self.assertEqual(len(C['verbs']), 27)
        for c in C['menus'].values():
            for k in ('identity', 'view', 'fields', 'source', 'relationships', 'rights', 'ffe', 'verbs', 'operating', 'evidence_maturity', 'exceptions', 'qualification'):
                self.assertIn(k, c)
            for e in c['relationships']:
                self.assertIn(e['cardinality'], ('one', 'many')); self.assertEqual(e['direction'], 'out')

    def test_reproducible_byte_for_byte(self):
        import tempfile
        p = os.path.join(tempfile.mkdtemp(), 'c.json'); B.main(p)
        self.assertEqual(open(p, 'rb').read(), open(os.path.join(HERE, 'navigator_integration_contract.json'), 'rb').read())

    def test_no_invented_maturity_or_endpoint(self):
        self.assertEqual(C['status'], 'SOURCE_READY_NOT_INSTALLED')
        for c in C['menus'].values():
            self.assertEqual(c['evidence_maturity']['installed'], 'NOT_ASSERTED'); self.assertEqual(c['qualification']['operating'], 'NOT_VERIFIED')
            self.assertEqual(c['verbs']['applicable'], 'UNBOUND_NO_SOURCE_MAPPING')
        miss = {r['id'] for r in C['read_contracts'] if r['state'] == 'MISSING_READ_CONTRACT'}
        self.assertEqual(miss, {'RC-3', 'RC-4', 'RC-5'})
        for r in C['read_contracts']:
            if r['state'] == 'MISSING_READ_CONTRACT': self.assertTrue(r['owner'])

    def test_same_object_menus_share_model(self):
        self.assertEqual(C['menus']['179']['view']['model'], 'synapsys.work.object')     # NEG-SAMEOBJ: Navigator>Progress


class Reconcile(unittest.TestCase):
    def run_(self, live=None, actor=ACTOR_OK, pins=None):
        return N.reconcile(C, live or clean_live(), pins, actor)

    def test_clean_has_no_defects_and_holds_stay_holds(self):
        r = self.run_()
        self.assertEqual(r['total'], 61); self.assertEqual(r['summary']['RETURN_DEFECTS'], 0)
        self.assertGreater(r['summary']['HOLD'], 0)
        for m, x in r['menus'].items():                                       # sparse / restricted / not-tested are never ACCEPT
            if C['menus'][m]['operating']['record_state'] == 'UNOBSERVED_ZERO_VISIBLE': self.assertEqual(x['verdict'], 'HOLD')
            self.assertNotEqual(x['verdict'], 'ACCEPT') if x['holds'] else None

    def test_deterministic(self):
        self.assertEqual(json.dumps(self.run_(), sort_keys=True), json.dumps(self.run_(), sort_keys=True))

    def test_injected_fixture_defects_are_each_detected(self):
        live = clean_live(); mid = '179'
        live['menus'][mid]['name_path'] = 'SynapSys/Navigator/Progress2'
        live['menus']['181']['action'] = 'ir.actions.act_window,999'
        live['menus']['180']['domain'] = "[('x','=',1)]"
        live['menus']['185']['model'] = 'res.partner'
        del live['fields']['synapsys.work.object']['service_id']
        live['fields']['synapsys.work.object']['method_id']['relation'] = 'synapsys.service'
        del live['menus']['178']
        r = self.run_(live)
        self.assertIn('IDENTITY_PATH_DRIFT', codes(r, '179')); self.assertIn('ACTION_DRIFT', codes(r, '181'))
        self.assertIn('DOMAIN_DRIFT', codes(r, '180')); self.assertIn('MODEL_DRIFT', codes(r, '185'))
        self.assertIn('FIELD_MISSING_LIVE', codes(r, '179')); self.assertIn('RELATION_TARGET_DRIFT', codes(r, '179'))
        self.assertIn('MENU_MISSING_LIVE', codes(r, '178'))
        self.assertEqual(r['menus']['179']['verdict'], 'RETURN_DEFECTS')
        req = N.correction_request(r, C['contract_sha256_over_menus'])
        self.assertFalse(req['mutating']); self.assertFalse(req['executes']); self.assertFalse(req['executor_claimed'])
        self.assertIn('179', [i['menu_id'] for i in req['items']])

    def test_verb_drift_and_source_drift(self):
        live = clean_live(); live['verbs'] = live['verbs'][:26]
        self.assertIn('VERB_SET_DRIFT', codes(self.run_(live), '179'))
        self.assertIn('SOURCE_DRIFT', codes(self.run_(pins={'contract_sha256_over_menus': 'deadbeef'}), '179'))

    def test_negative_permission_and_redaction(self):
        steward_only = [m for m, c in C['menus'].items() if c['rights']['steward_only']]
        a = dict(ACTOR_OK, visible_menu_ids=steward_only[:1], leaked_ids=[steward_only[0]]) if steward_only else None
        if a: 
            r = self.run_(actor=a)
            self.assertIn('NEGATIVE_PERMISSION_BREACH', codes(r, steward_only[0])); self.assertIn('REDACTION_LEAK', codes(r, steward_only[0]))
        r = self.run_(actor=dict(ACTOR_OK, leaked_ids=['179']))
        self.assertIn('REDACTION_LEAK', codes(r, '179'))

    def test_without_actor_read_nothing_is_accepted(self):
        r = self.run_(actor=None)
        self.assertEqual(r['summary']['ACCEPT'], 0)
        self.assertTrue(all(any(h['code'] == 'ACTOR_READ_NOT_SUPPLIED' for h in x['holds']) for x in r['menus'].values()))

    def test_fields_not_read_is_hold_not_pass(self):
        live = clean_live(); live['fields'] = {}
        r = self.run_(live)
        self.assertTrue(any(h['code'] == 'FIELDS_NOT_READ' for h in r['menus']['179']['holds']))

    def test_cross_menu_same_object_reported(self):
        r = self.run_()
        same = [m for m, x in r['menus'].items() if 'cross_menu' in x and x['cross_menu']['model'] == 'synapsys.work.object']
        self.assertGreaterEqual(len(same), 2)


class BlindSpots(unittest.TestCase):
    """RC00 step 4: view_mode, client_tag and cardinality were never compared. Each injected defect must be detected; unread data is HOLD."""
    def run_(self, live): return N.reconcile(C, live, pins=None, actor=ACTOR_OK)
    def test_clean_fixture_has_no_new_defects_or_holds(self):
        r = self.run_(clean_live())
        self.assertEqual(r['summary']['RETURN_DEFECTS'], 0)
        for x in r['menus'].values():
            for h in x['holds']: self.assertNotIn(h['code'], ('VIEW_MODE_NOT_READ', 'CLIENT_TAG_NOT_READ', 'FIELD_TYPE_NOT_READ', 'CLIENT_TAG_UNPINNED'))
    def test_view_mode_drift_detected(self):
        live = clean_live(); mid = [m for m, c in C['menus'].items() if c['view']['view_mode']][0]
        live['menus'][mid]['view_mode'] = 'kanban'
        self.assertIn('VIEW_MODE_DRIFT', codes(self.run_(live), mid))
    def test_view_mode_order_matters_spacing_does_not(self):
        live = clean_live(); mid = [m for m, c in C['menus'].items() if c['view']['view_mode'] and ',' in c['view']['view_mode']][0]
        modes = [x.strip() for x in C['menus'][mid]['view']['view_mode'].split(',')]
        live['menus'][mid]['view_mode'] = ' , '.join(modes); self.assertNotIn('VIEW_MODE_DRIFT', codes(self.run_(live), mid))
        live['menus'][mid]['view_mode'] = ','.join(reversed(modes)); self.assertIn('VIEW_MODE_DRIFT', codes(self.run_(live), mid))
    def test_view_mode_unread_is_hold_not_pass(self):
        live = clean_live(); mid = [m for m, c in C['menus'].items() if c['view']['view_mode']][0]; del live['menus'][mid]['view_mode']
        r = self.run_(live); self.assertIn('VIEW_MODE_NOT_READ', [h['code'] for h in r['menus'][mid]['holds']]); self.assertNotEqual(r['menus'][mid]['verdict'], 'ACCEPT')
    def test_client_tag_pins_and_drift(self):
        self.assertEqual(N.PINNED_CLIENT_TAGS, {331: 'synapsys_home', 332: 'synapsys_architecture_map', 358: 'synapsys_lenses'})
        for mid, tag in (('177', 'synapsys_home'), ('215', 'synapsys_architecture_map'), ('237', 'synapsys_lenses')):
            live = clean_live(); self.assertEqual(live['menus'][mid]['client_tag'], tag); self.assertNotIn('CLIENT_TAG_DRIFT', codes(self.run_(live), mid))
            live['menus'][mid]['client_tag'] = 'synapsys_other'; self.assertIn('CLIENT_TAG_DRIFT', codes(self.run_(live), mid))
    def test_client_tag_unread_is_hold(self):
        live = clean_live(); live['menus']['177']['client_tag'] = None
        self.assertIn('CLIENT_TAG_NOT_READ', [h['code'] for h in self.run_(live)['menus']['177']['holds']])
    def test_swapped_client_tags_between_menus_detected(self):
        live = clean_live(); live['menus']['215']['client_tag'], live['menus']['237']['client_tag'] = live['menus']['237']['client_tag'], live['menus']['215']['client_tag']
        r = self.run_(live); self.assertIn('CLIENT_TAG_DRIFT', codes(r, '215')); self.assertIn('CLIENT_TAG_DRIFT', codes(r, '237'))
    def test_cardinality_drift_both_directions(self):
        live = clean_live(); one = next((m, e['field']) for m, c in C['menus'].items() for e in c['relationships'] if e['cardinality'] == 'one' and c['view']['model'])
        many = next((m, e['field']) for m, c in C['menus'].items() for e in c['relationships'] if e['cardinality'] == 'many' and c['view']['model'])
        for (mid, field), bad in ((one, 'many2many'), (many, 'many2one')):
            live = clean_live(); live['fields'][C['menus'][mid]['view']['model']][field]['type'] = bad
            self.assertIn('CARDINALITY_DRIFT', codes(self.run_(live), mid), (mid, field))
    def test_one2many_counts_as_many(self):
        live = clean_live(); mid, field = next((m, e['field']) for m, c in C['menus'].items() for e in c['relationships'] if e['cardinality'] == 'many' and c['view']['model'])
        live['fields'][C['menus'][mid]['view']['model']][field]['type'] = 'one2many'; self.assertNotIn('CARDINALITY_DRIFT', codes(self.run_(live), mid))
    def test_field_type_unread_is_hold(self):
        live = clean_live(); mid, field = next((m, e['field']) for m, c in C['menus'].items() for e in c['relationships'] if c['view']['model'])
        del live['fields'][C['menus'][mid]['view']['model']][field]['type']
        self.assertIn('FIELD_TYPE_NOT_READ', [h['code'] for h in self.run_(live)['menus'][mid]['holds']])
    def test_unpinned_client_action_is_hold_never_invented_pin_or_drift(self):
        c2 = copy.deepcopy(C); c2['menus']['177']['identity']['action_id'] = 999; c2['menus']['177']['identity']['action_ref'] = 'ir.actions.client,999'
        live = clean_live(); live['menus']['177']['action'] = 'ir.actions.client,999'; live['menus']['177']['client_tag'] = 'some_new_tag'
        r = N.reconcile(c2, live, pins=None, actor=ACTOR_OK)['menus']['177']
        self.assertEqual([d for d in r['defects'] if d['code'].startswith('CLIENT_TAG')], [])
        self.assertIn('CLIENT_TAG_UNPINNED', [h['code'] for h in r['holds']]); self.assertNotEqual(r['verdict'], 'ACCEPT')
    def test_contract_bytes_unchanged_by_reconciler_fix(self):
        import hashlib; self.assertEqual(hashlib.sha256(open(os.path.join(HERE, 'navigator_integration_contract.json'), 'rb').read()).hexdigest(), '445df39b809ba8785b0c17da2dfb1e60696c3a75358f33922f4e7f1b899e33c1')


class Exhaustive(unittest.TestCase):
    """RC00 step 4: every one of 61 rows, 27 verbs and 32 known relationships is individually perturbed and must be detected."""
    def run_(self, live): return N.reconcile(C, live, pins=None, actor=ACTOR_OK)
    def test_all_61_rows_each_detect_path_drift_and_missing(self):
        n = 0
        for mid in C['menus']:
            live = clean_live(); live['menus'][mid]['name_path'] += '_x'; self.assertIn('IDENTITY_PATH_DRIFT', codes(self.run_(live), mid))
            live = clean_live(); del live['menus'][mid]; self.assertIn('MENU_MISSING_LIVE', codes(self.run_(live), mid)); n += 1
        self.assertEqual(n, 61)
    def test_every_27_verb_removal_detected(self):
        self.assertEqual(len(C['verbs']), 27)
        for v in C['verbs']:
            live = clean_live(); live['verbs'] = [x for x in live['verbs'] if x != v]
            self.assertTrue(any('VERB_SET_DRIFT' in codes(self.run_(live), m) for m in C['menus']), v)
    def test_every_one_of_32_relationships_detects_cardinality_target_and_missing_field(self):
        seen = 0
        for mid, c in C['menus'].items():
            m = c['view']['model']
            for e in c['relationships']:
                if not m: continue
                live = clean_live(); live['fields'][m][e['field']]['type'] = 'many2one' if e['cardinality'] == 'many' else 'many2many'
                self.assertIn('CARDINALITY_DRIFT', codes(self.run_(live), mid), (mid, e['field']))
                live = clean_live(); live['fields'][m][e['field']]['relation'] = 'res.users' if e['target_model'] == 'res.partner' else 'res.partner'  # always a DIFFERENT target
                self.assertIn('RELATION_TARGET_DRIFT', codes(self.run_(live), mid), (mid, e['field']))
                live = clean_live(); del live['fields'][m][e['field']]
                self.assertIn('FIELD_MISSING_LIVE', codes(self.run_(live), mid), (mid, e['field'])); seen += 1
        self.assertEqual(seen, 32)
    def test_every_view_mode_bearing_row_detects_drift(self):
        k = 0
        for mid, c in C['menus'].items():
            if c['view']['view_mode']:
                live = clean_live(); live['menus'][mid]['view_mode'] = 'graph'; self.assertIn('VIEW_MODE_DRIFT', codes(self.run_(live), mid)); k += 1
        self.assertGreater(k, 0)

if __name__ == '__main__':
    unittest.main()
