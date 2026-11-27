from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase, tagged, new_test_user


@tagged('post_install', '-at_install', 'synapsys')
class TestContextRowScope(TransactionCase):
    """Negative test: a Collaborator sees a Context, its Strategies, Assets and Purpose only when they steward it or are a member. A Steward sees all."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        cls.collab = new_test_user(env, login='collab_rs', groups='synapsys.group_synapsys_user')
        cls.steward = new_test_user(env, login='steward_rs', groups='synapsys.group_synapsys_steward')
        cls.p_own = env['synapsys.purpose'].create({'code': 'RS-P-OWN', 'name': 'own purpose'})
        cls.p_other = env['synapsys.purpose'].create({'code': 'RS-P-OTHER', 'name': 'other purpose'})
        cls.c_own = env['synapsys.context'].create({'code': 'RS-OWN', 'purpose_id': cls.p_own.id, 'member_ids': [(4, cls.collab.id)]})
        cls.c_other = env['synapsys.context'].create({'code': 'RS-OTHER', 'purpose_id': cls.p_other.id})
        cls.s_own = env['synapsys.strategy'].create({'name': 'RS-S-OWN', 'code': 'RS-S-OWN', 'context_id': cls.c_own.id, 'purpose_id': cls.p_own.id})
        cls.s_other = env['synapsys.strategy'].create({'name': 'RS-S-OTHER', 'code': 'RS-S-OTHER', 'context_id': cls.c_other.id, 'purpose_id': cls.p_other.id})
        cls.a_own = env['synapsys.asset'].create({'name': 'RS-A-OWN', 'context_id': cls.c_own.id})
        cls.a_other = env['synapsys.asset'].create({'name': 'RS-A-OTHER', 'context_id': cls.c_other.id})

    def _seen(self, model, user, key, prefix):
        return self.env[model].with_user(user).search([(key, 'like', prefix)])

    def test_collaborator_sees_only_own_context_chain(self):
        self.assertEqual(self._seen('synapsys.context', self.collab, 'code', 'RS-'), self.c_own)
        self.assertEqual(self._seen('synapsys.strategy', self.collab, 'code', 'RS-S-'), self.s_own)
        self.assertEqual(self._seen('synapsys.asset', self.collab, 'name', 'RS-A-'), self.a_own)
        self.assertEqual(self._seen('synapsys.purpose', self.collab, 'code', 'RS-P-'), self.p_own)

    def test_collaborator_cannot_read_other_context_by_id(self):
        for rec in (self.c_other, self.s_other, self.a_other, self.p_other):
            with self.assertRaises(AccessError):
                rec.with_user(self.collab).read(['display_name'])

    def test_stewarding_a_context_grants_sight(self):
        self.c_other.steward_user_id = self.collab
        self.assertIn(self.c_other, self._seen('synapsys.context', self.collab, 'code', 'RS-'))

    def test_steward_sees_all(self):
        self.assertEqual(self._seen('synapsys.context', self.steward, 'code', 'RS-'), self.c_own | self.c_other)
        self.assertEqual(self._seen('synapsys.asset', self.steward, 'name', 'RS-A-'), self.a_own | self.a_other)
