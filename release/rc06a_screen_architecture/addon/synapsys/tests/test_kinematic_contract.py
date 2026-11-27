"""Task 197: universal Kinematic Contract (P1-P6). Positive T1-T3, negative N1-N7.
T4 (V19 parity of the seeded Contexts) lives in synapsys_seed/tests because it needs the seed data."""
import json

from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged, new_test_user


@tagged('post_install', '-at_install', 'synapsys')
class TestKinematicContract(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Ctx = cls.env['synapsys.context']
        cls.Verb = cls.env['synapsys.verb']
        cls.collab = new_test_user(cls.env, login='kc_collab', groups='synapsys.group_synapsys_user')
        cls.external = new_test_user(cls.env, login='kc_ext', groups='base.group_portal')

    # ------------------------------------------------------------ positive

    def test_t1_eligible_verbs_follow_ruled_kind(self):
        k12 = self.Ctx.create({'code': 'KC-12', 'name': 'k12', 'kind': 'K-12'})
        k1 = self.Ctx.create({'code': 'KC-1', 'name': 'k1', 'kind': 'K-1'})
        self.assertEqual(k12.eligible_verb_count, 12)
        self.assertEqual(k1.eligible_verb_ids.mapped('name'), ['sense'])
        prog = self.env['synapsys.programme'].create({'name': 'P', 'context_id': k12.id})
        self.assertEqual(prog.eligible_verb_ids, k12.eligible_verb_ids, 'a cell inherits its Context eligibility')

    def test_t2_screen_and_ai_projection_are_the_same_contract(self):
        cx = self.Ctx.create({'code': 'KC-T2', 'name': 't2', 'kind': 'K-6', 'next_action': 'collect baseline'})
        prog = self.env['synapsys.programme'].create({'name': 'P2', 'context_id': cx.id})
        for rec in (cx, prog):
            screen = json.loads(json.dumps(rec._kinematic_contract(), default=str))
            ai = json.loads(rec.kinematic_contract_json())
            self.assertEqual(ai, [screen])
            self.assertEqual(screen['eligible_verbs'], rec.eligible_verb_ids.sorted('sequence').mapped('name'))
            self.assertEqual(screen['authority'], 'none: this projection grants nothing')

    def test_t3_counts_are_orm_counts(self):
        cx = self.Ctx.create({'code': 'KC-T3', 'name': 't3', 'kind': 'K-8'})
        for i in range(2):
            self.env['synapsys.programme'].create({'name': 'p%d' % i, 'context_id': cx.id})
        self.assertEqual(cx.programme_count,
                         self.env['synapsys.programme'].search_count([('context_id', '=', cx.id)]))
        self.assertEqual(cx.eligible_verb_count, len(cx.eligible_verb_ids))
        c = cx._kinematic_contract()
        moded = self.env['synapsys.mode'].search([]).verb_ids
        self.assertEqual(set(c['verbs_mode_not_ruled']),
                         set((self.Verb.search([]) - moded).filtered(lambda v: not v.human_only).mapped('name')))

    # ------------------------------------------------------------ negative

    def test_n1_no_kind_no_verbs_and_proposed_kind_never_used(self):
        cx = self.Ctx.create({'code': 'KC-N1', 'name': 'n1', 'kind_proposed': 'K-12'})
        self.assertFalse(cx.eligible_verb_ids)
        c = cx._kinematic_contract()
        self.assertEqual(c['context']['kind_ruled'], 'GAP')
        self.assertEqual(c['eligible_verbs'], [])
        orphan = self.env['synapsys.programme'].create({'name': 'no context'})
        self.assertEqual(orphan._kinematic_contract()['context'], 'GAP')
        self.assertFalse(orphan.eligible_verb_ids)

    def test_n2_commit_is_never_eligible(self):
        commit = self.Verb.search([('name', '=', 'commit')])
        self.assertTrue(commit.human_only)
        k12 = self.env['synapsys.mode'].search([('code', '=', 'K-12')])
        k12.verb_ids = [(4, commit.id)]  # even if someone adds it to a mode
        cx = self.Ctx.create({'code': 'KC-N2', 'name': 'n2', 'kind': 'K-12'})
        self.assertNotIn('commit', cx.eligible_verb_ids.mapped('name'))
        self.assertNotIn('commit', cx._kinematic_contract()['verbs_mode_not_ruled'])

    def test_n3_collaborator_cannot_rule_kind(self):
        cx = self.Ctx.create({'code': 'KC-N3', 'name': 'n3'})
        with self.assertRaises(AccessError):
            cx.with_user(self.collab).write({'kind': 'K-12'})

    def test_n4_rights_filtered_projection(self):
        cx = self.Ctx.create({'code': 'KC-N4', 'name': 'secret name', 'kind': 'K-4'})
        ext = json.loads(cx.with_user(self.external).kinematic_contract_json())
        self.assertEqual(ext, [{'schema': 'synapsys.kinematic.contract/1', 'visibility': 'NOT_VISIBLE'}])
        self.assertNotIn('secret name', cx.with_user(self.external).kinematic_contract_json())
        col = json.loads(cx.with_user(self.collab).kinematic_contract_json())
        self.assertEqual(col[0]['visibility'], 'VISIBLE')
        self.assertEqual(col[0]['context']['code'], 'KC-N4')

    def test_n5_projection_has_no_write_path(self):
        cx = self.Ctx.create({'code': 'KC-N5', 'name': 'n5', 'kind': 'K-3'})
        before = cx.write_date
        # Collaborator has read-only access to Contexts: the projection must still work, so it cannot need write.
        cx.with_user(self.collab).kinematic_contract_json()
        self.assertEqual(cx.write_date, before)
        self.assertFalse(hasattr(type(cx), 'write_kinematic_contract'))

    def test_n6_shape_never_inferred_from_kind(self):
        cx = self.Ctx.create({'code': 'KC-N6', 'name': 'n6', 'kind': 'K-12'})
        svc = self.env['synapsys.service'].create({'code': 'KC-S', 'name': 'svc', 'context_id': cx.id})
        self.assertFalse(svc.shape)
        self.assertEqual(svc._kinematic_contract()['shape'], 'GAP')
        self.assertEqual(cx._kinematic_contract()['shape'], 'NOT_CARRIED')

    def test_n7_derivatives_normalise_to_the_27(self):
        self.assertEqual(self.Verb.search_count([]), 27)
        tokens = {}
        for v in self.Verb.search([]):
            words = [v.name] + [a.strip() for a in (v.aliases or '').split(',') if a.strip()]
            if v.inverse:
                words.append(v.inverse.strip())
            for w in words:
                self.assertNotIn(w, tokens, 'derivative %s collides with %s' % (w, tokens.get(w)))
                tokens[w] = v.name
        for word, canon, rev in (('derives_from', 'derive', False), ('member_of', 'join', False),
                                 ('parent_of', 'parent', False), ('successor_of', 'succeed', False),
                                 ('challenged_by', 'challenge', True), ('challenges', 'challenge', False),
                                 ('architect', 'composes', False), ('composed_by', 'composes', True)):
            v, reversed_ = self.Verb._resolve(word)
            self.assertEqual((v.name, reversed_), (canon, rev), word)
        v, reversed_ = self.Verb._resolve('invented_verb')
        self.assertFalse(v)
        self.assertEqual(self.Verb.search_count([]), 27, 'resolving never creates verbs')
