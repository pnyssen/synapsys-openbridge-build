"""Service Health H04-H07 + dependency + non-disclosing actor rights (offline; pure module, no Odoo)."""
import importlib.util
import os
import re
import unittest

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'addon', 'synapsys')


def _load(n):
    spec = importlib.util.spec_from_file_location(n, os.path.join(BASE, n + '.py'))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


SH = _load('service_health')
FULL = dict(name='S', context_id=1, kind_proposed='K-6', perspective='internal', method_id=5, canon_ids=[1], owner_name='o',
            entry_point='e', approval_category='a', execution_outcome_schema='x', sla_value='1', benefit_ids=[1], asset_ids=[1],
            observation_learning_contract='c', obligations='o')


class Depends(unittest.TestCase):
    def test_compute_health_depends_on_return_acceptance_schema(self):   # original failure: field missing from @api.depends
        src = open(os.path.join(BASE, 'models', 'synapsys.py'), encoding='utf-8').read()
        m = re.search(r"@api\.depends\(([^)]*)\)\s*def _compute_health", src)
        self.assertIsNotNone(m)
        deps = set(re.findall(r"'([a-z_]+)'", m.group(1)))
        self.assertEqual(deps, set(SH.HEALTH_DEPENDS))
        self.assertIn('return_acceptance_schema', deps)


class Structural(unittest.TestCase):
    def test_full_is_15_and_unchanged_meaning(self):
        f, ready, _ = SH.structural_slots(FULL)
        self.assertEqual((f, ready), (15, True))

    def test_slot9_accepts_either_schema(self):
        v = dict(FULL, execution_outcome_schema=False, return_acceptance_schema='r')
        self.assertEqual(SH.structural_slots(v)[0], 15)
        v = dict(FULL, execution_outcome_schema=False)
        self.assertEqual(SH.structural_slots(v)[0], 14)


class Relationships(unittest.TestCase):                                # H04-H06
    def test_h04_full_slots_do_not_imply_bound_edges(self):
        v = dict(FULL, context_id=None, method_id=None, canon_ids=[])
        r = SH.project(v, actor_context_ids={1})
        self.assertEqual(r['relationships']['edges']['context']['state'], 'SOURCE_UNVERIFIED')
        self.assertNotEqual(r['relationships']['summary'], 'COMPLETE_FOR_RULED_EDGES')

    def test_h05_ruled_states(self):
        v = dict(FULL, method_id=None, canon_ids=[], pattern_ids=[])
        e = SH.relationship_coverage(v, {1}, {'method': 'REQUIRED', 'canon': 'NOT_APPLICABLE'})['edges']
        self.assertEqual(e['method']['state'], 'MISSING_REQUIRED')
        self.assertEqual(e['canon']['state'], 'NOT_APPLICABLE')
        self.assertEqual(e['pattern']['state'], 'SOURCE_UNVERIFIED')
        self.assertEqual(e['context']['state'], 'BOUND')

    def test_h06_wrong_context_redacted_no_leak(self):
        v = dict(FULL, context_id=99)
        e = SH.relationship_coverage(v, {1})['edges']['context']
        self.assertEqual(e['state'], 'INACCESSIBLE_REDACTED')
        self.assertNotIn('count', e); self.assertNotIn('99', repr(e))

    def test_h06_fail_closed_when_entitlement_unknown(self):
        self.assertEqual(SH.relationship_coverage(FULL, None)['edges']['context']['state'], 'INACCESSIBLE_REDACTED')

    def test_method_in_foreign_context_redacted(self):
        e = SH.relationship_coverage(FULL, {1}, method_context_id=7)['edges']['method']
        self.assertEqual(e['state'], 'INACCESSIBLE_REDACTED')

    def test_states_closed_set(self):
        for rl in ({}, {'method': 'REQUIRED'}, {'method': 'bogus'}):
            for e in SH.relationship_coverage(dict(FULL, method_id=None), {1}, rl)['edges'].values():
                self.assertIn(e['state'], SH.STATES)


class Operating(unittest.TestCase):                                    # H07
    def _all(self, **kw):
        ev = {k: dict(by='d009', authorised=True, attributable=True, attested=True, produced_by='cc') for k in SH.OPERATING_REQUIRED}
        ev.update(kw); return ev

    def test_h07_answer_accepted_flag_is_not_evidence(self):
        r = SH.operating_qualification({}, answer_accepted_flag=True)
        self.assertEqual(r['state'], 'HELD'); self.assertEqual(r['answer_accepted_flag'], 'FLAG_ONLY_NOT_EVIDENCE')

    def test_15_of_15_still_held(self):
        self.assertEqual(SH.project(FULL, {1})['operating']['state'], 'HELD')

    def test_self_attested_is_not_verified(self):
        ev = self._all(second_cycle=dict(by='cc', authorised=True, attributable=True, attested=True, produced_by='cc'))
        self.assertEqual(SH.operating_qualification(ev)['state'], 'NOT_VERIFIED')

    def test_unauthorised_receipt_ignored(self):
        ev = self._all(recovery_tested=dict(by='x', authorised=False, attributable=True, attested=True, produced_by='cc'))
        r = SH.operating_qualification(ev)
        self.assertEqual(r['state'], 'HELD'); self.assertIn('recovery_tested', r['missing'])

    def test_full_independent_is_verified(self):
        self.assertEqual(SH.operating_qualification(self._all())['state'], 'VERIFIED')


class FakeRec:
    def __init__(s, i, steward=None, members=()): s.id, s.steward_user_id, s.member_ids = i, steward, list(members)


class FakeCtx:
    def __init__(s, recs, err=None): s.recs, s.err = recs, err
    def search(s, dom):
        if s.err: raise s.err
        return s.recs


class AccessError(Exception):
    pass


class ActorCtx(unittest.TestCase):
    def test_entitled_only(self):
        env = {'synapsys.context': FakeCtx([FakeRec(1, 7), FakeRec(2, 9, [7]), FakeRec(3, 9, [8])])}
        self.assertEqual(SH.actor_context_ids(env, 7), {1, 2})

    def test_access_error_fails_closed(self):
        self.assertEqual(SH.actor_context_ids({'synapsys.context': FakeCtx([], AccessError())}, 7), set())

    def test_missing_model_fails_closed(self):
        self.assertEqual(SH.actor_context_ids({}, 7), set())


LC = _load('lens_contract')


class Lineage(unittest.TestCase):                                     # shared inherited-depth resolver on two real source-backed screens
    def test_lineage_is_nearest_first_cycle_safe_and_source_only(self):
        self.assertEqual(LC.lineage({'svc': 'ctx', 'ctx': 'pur'}, 'svc'), ('ctx', 'pur'))
        self.assertEqual(LC.lineage({'a': 'b', 'b': 'a'}, 'a'), ('b',))
        self.assertEqual(LC.lineage({}, 'x'), ())

    def test_context_override_cascades_to_directly_bound_service_only(self):
        ov = {'ctx:1': 'enrich'}
        self.assertEqual(LC.mode_for('svc:5', 'enable', ov, ['ctx:1']), 'enrich')
        self.assertEqual(LC.mode_for('svc:6', 'enable', ov, []), 'enable')          # wrong/missing Context inherits nothing
        self.assertEqual(LC.mode_for('svc:5', 'enable', {'svc:5': 'enhance', 'ctx:1': 'enrich'}, ['ctx:1']), 'enhance')  # exact wins

    def test_slice_screen_carries_lineage_from_source_records(self):
        A = _load('arch_slice')
        graph = {'records': {'synapsys.context': {1: {'code': 'C', 'kind': None, 'kind_ruling': None}},
                             'synapsys.strategy': {10: {'context_id': 1, 'service_ids': [5, 6]}},
                             'synapsys.service': {5: {'context_id': 1}, 6: {'context_id': 2}}}}
        actor = {'visible': {m: set(t) for m, t in graph['records'].items()}, 'restricted_models': set()}
        out = A.build_slice(graph, actor, {'field_absent': {}, 'truncated': [], 'restricted': []})
        items = {i['id']: i for i in out['contexts'][0]['strategy_services'][0]['services']['items']}
        self.assertEqual(items[5]['lens_ancestors'], ['ctx:1'])
        self.assertEqual(items[6]['lens_ancestors'], [])
        self.assertEqual(out['contexts'][0]['context']['lens_element'], 'ctx:1')

    def test_registry_screen_element_gets_declared_parent_lineage(self):
        class G:
            els = {'N.A': {'label': 'A'}, 'N.B': {'label': 'B'}, 'N.C': {'label': 'C'}}
            rels = [{'id': 'r1', 'from': 'N.A', 'to': 'N.B', 'label': 'part_of'}, {'id': 'r2', 'from': 'N.B', 'to': 'N.C', 'label': 'contained_in'},
                    {'id': 'r3', 'from': 'N.A', 'to': 'N.C', 'label': 'relates'}]
            roles = {}
            def label(s, x): return x
        el = LC.from_noun(G(), 'N.A')
        self.assertEqual(el['ancestors'], ['N.B', 'N.C'])
        out = LC.render_element(el, 'enable', {'N.C': 'enrich'})
        self.assertIn('data-mode="enrich"', out); self.assertIn('data-override="inherited"', out)


if __name__ == '__main__':
    unittest.main()
