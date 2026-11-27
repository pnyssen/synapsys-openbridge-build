from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase, tagged, new_test_user


@tagged('post_install', '-at_install', 'synapsys')
class TestIntelligenceAccess(TransactionCase):
    """Negative test (KDA P3): personal Intelligence is Steward-only; collaborators cannot see or write it."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        I = cls.env['synapsys.intelligence']
        cls.personal = I.create({'name': 'Named person (test)', 'personal_data': True})
        cls.general = I.create({'name': 'Market signal (test)', 'personal_data': False})
        cls.collab = new_test_user(cls.env, login='collab_p3', groups='synapsys.group_synapsys_user')
        cls.steward = new_test_user(cls.env, login='steward_p3', groups='synapsys.group_synapsys_steward')

    def test_collaborator_cannot_find_personal_record(self):
        found = self.env['synapsys.intelligence'].with_user(self.collab).search([('name', 'like', '(test)')])
        self.assertIn(self.general, found)
        self.assertNotIn(self.personal, found)

    def test_collaborator_cannot_read_personal_record_by_id(self):
        with self.assertRaises(AccessError):
            self.personal.with_user(self.collab).read(['name'])

    def test_collaborator_cannot_write_or_create(self):
        with self.assertRaises(AccessError):
            self.general.with_user(self.collab).write({'name': 'x'})
        with self.assertRaises(AccessError):
            self.env['synapsys.intelligence'].with_user(self.collab).create({'name': 'y', 'personal_data': True})

    def test_steward_sees_both(self):
        found = self.env['synapsys.intelligence'].with_user(self.steward).search([('name', 'like', '(test)')])
        self.assertEqual(found, self.personal | self.general)
