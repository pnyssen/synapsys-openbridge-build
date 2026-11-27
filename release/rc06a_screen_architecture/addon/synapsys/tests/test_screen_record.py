"""RC06a record-screen tests against real Odoo models, in a TransactionCase (every record created here is rolled back).

SOURCE ONLY, NOT RUN: this build had no Odoo. It is written to run in the module's test suite on a disposable database, never on
dev data: it creates its own Context and Asset records inside the test transaction and nothing persists. Dev holds no operating
records (synapsys.context and synapsys.asset count 0), so the record-screen path has no live data to read; these tests are what
exercises it. The offline equivalents (fake env, same code path) are in release/rc06a_screen_architecture/tests/test_screen_arch.py.
"""
from odoo.tests import TransactionCase, new_test_user, tagged

from odoo.addons.synapsys import scaffold_wire as sw, screen_render as sr


@tagged('post_install', '-at_install', 'synapsys')
class TestScreenRecord(TransactionCase):

    def setUp(self):
        super().setUp()
        self.steward = new_test_user(self.env, 'rc06steward', groups='synapsys.group_synapsys_steward')
        self.env_s = self.env(user=self.steward)
        if not self.env['synapsys.mesh.registry'].search([], limit=1):
            self.skipTest('no Mesh registry installed on this database')

    def _context(self, kind, code):
        return self.env['synapsys.context'].create({'code': code, 'name': 'Fixture ' + code, 'kind': kind})

    def test_context_record_ceiling_follows_its_own_kind(self):
        for kind, eff in (('K-1', 'enable'), ('K-6', 'enhance'), ('K-12', 'enrich')):
            ctx = self._context(kind, 'CTX-RC06-' + kind)
            out = sw.screen_record(self.env_s, 'SCR.CONTEXT.RECORD', ctx.id, 'enrich')
            self.assertEqual(out['result'], 'OK')
            self.assertEqual((out['stage'], out['depth_effective']), (eff, eff), kind)
            self.assertEqual(out['depth_clamped'], eff != 'enrich')
            self.assertIn('Fixture CTX-RC06-' + kind, sr.render_screen(out))

    def test_context_record_without_a_kind_is_stage_not_bound(self):
        ctx = self.env['synapsys.context'].create({'code': 'CTX-RC06-NOKIND', 'name': 'No kind'})
        out = sw.screen_record(self.env_s, 'SCR.CONTEXT.RECORD', ctx.id, 'enrich')
        self.assertEqual((out['stage'], out['depth_effective']), ('not bound', 'enable'))

    def test_asset_record_stage_is_its_own_noun_kind_k4_with_its_context_kind_as_neighbour(self):
        ctx = self._context('K-12', 'CTX-RC06-A')
        asset = self.env['synapsys.asset'].create({'name': 'Fixture asset', 'context_id': ctx.id})
        out = sw.screen_record(self.env_s, 'SCR.ASSET.RECORD', asset.id, 'enrich')
        self.assertEqual((out['stage'], out['depth_effective'], out['depth_clamped']), ('enable', 'enable', True))
        self.assertIn('Neighbour: its Context is kind K-12', sr.render_screen(out))

    def test_a_missing_record_is_refused_not_an_error(self):
        out = sw.screen_record(self.env_s, 'SCR.CONTEXT.RECORD', 0, 'enable')
        self.assertEqual(out['reason'], 'RECORD_NOT_FOUND')
