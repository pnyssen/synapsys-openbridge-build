from odoo.exceptions import AccessError, ValidationError
from odoo.tests import TransactionCase, tagged, new_test_user


@tagged('post_install', '-at_install', 'synapsys')
class TestSynapsysCore(TransactionCase):

    def test_01_reference_counts(self):
        self.assertEqual(self.env['synapsys.domain'].search_count([]), 12)
        self.assertEqual(self.env['synapsys.verb'].search_count([]), 27)
        self.assertEqual(self.env['synapsys.mode'].search_count([]), 6)

    def test_02_verbs_nine_by_three_and_movements_once(self):
        V = self.env['synapsys.verb'].search([])
        by = {}
        for v in V:
            by.setdefault(v.strategy, []).append(v)
        self.assertEqual(len(by), 9)
        self.assertTrue(all(len(x) == 3 for x in by.values()))
        mv = [v.movement for v in V if v.movement]
        self.assertEqual(sorted(mv), sorted('M%d' % i for i in range(1, 13)))

    def test_03_chain_five_stages_rejected(self):
        with self.assertRaises(ValidationError):
            self.env['synapsys.value.chain'].create({'code': 'T5', 'stage_ids': [
                (0, 0, {'name': 's%d' % i, 'sequence': i}) for i in range(5)]})

    _n = 0

    def _asset_with_links(self, ppv_link, ppv_ben, n=3, same_chain=True, **asset_vals):
        TestSynapsysCore._n += 1
        k = TestSynapsysCore._n
        ch = self.env['synapsys.value.chain'].create({'code': 'TQ%d' % k, 'stage_ids': [(0, 0, {'name': 'a', 'sequence': i}) for i in range(3)]})
        other = self.env['synapsys.value.chain'].create({'code': 'TQX%d' % k, 'stage_ids': [(0, 0, {'name': 'a', 'sequence': i}) for i in range(3)]})
        holder = self.env['res.partner'].create({'name': 'Holder'})
        a = self.env['synapsys.asset'].create(dict({'name': 'Test asset', 'chain_id': ch.id, 'rights_holder_id': holder.id,
                                                    'rights_basis': 'Context owner (S13)'}, **asset_vals))
        for i in range(n):
            b = self.env['synapsys.benefit'].create({'name': 'b%d' % i, 'ppv': ppv_ben})
            self.env['synapsys.oba.link'].create({'benefit_id': b.id, 'asset_id': a.id, 'type': 'DIRECT',
                                                 'chain_id': (ch if same_chain else other).id, 'ppv': ppv_link})
        return a

    def test_04_asset_qualification_rule(self):
        self.assertTrue(self._asset_with_links('probable', 'probable').qualifies)
        self.assertFalse(self._asset_with_links('potential', 'probable').qualifies, 'link below Probable')
        self.assertFalse(self._asset_with_links('probable', 'potential').qualifies, 'Benefit below Probable')
        self.assertFalse(self._asset_with_links('probable', 'probable', n=2).qualifies, 'fewer than 3')
        self.assertFalse(self._asset_with_links('probable', 'probable', same_chain=False).qualifies, 'cross-chain')
        self.assertFalse(self._asset_with_links('probable', 'probable', rights_required=True).qualifies, 'rights open')

    def test_05_influences_never_counts(self):
        a = self._asset_with_links('probable', 'probable')
        a.link_ids.write({'type': 'INFLUENCES'})
        self.assertEqual(a.benefit_count, 0)
        self.assertFalse(a.qualifies)

    def test_06_promotion_guard(self):
        u = new_test_user(self.env, login='collab_t', groups='synapsys.group_synapsys_user')
        b = self.env['synapsys.benefit'].create({'name': 'guard'})
        with self.assertRaises(AccessError):
            b.with_user(u).write({'ppv': 'probable'})
        with self.assertRaises(AccessError):
            b.with_user(u).write({'answer_accepted': True})
        b.with_user(u).write({'next_action': 'collect baseline'})
        self.assertEqual(b.next_action, 'collect baseline')

    def test_07_gap_shown_not_inferred(self):
        b = self.env['synapsys.benefit'].create({'name': 'gappy'})
        self.assertGreater(b.gap_count, 0)
        self.assertIn('GAP', b.gap_html)

    def test_08_menu_one_tree_design_d(self):
        """Steward 20 Nov 07:35: one tree, no duplicates. Top bar Navigator, Strategies, Architecture;
        Architecture = Form 12, Flow 9, Evolve 6, Mesh (Design D, 20 Nov 00:00)."""
        Menu = self.env['ir.ui.menu']
        root = self.env.ref('synapsys.menu_root')
        top = Menu.search([('parent_id', '=', root.id)])
        self.assertEqual(top.mapped('name'), ['Navigator', 'Strategies', 'Architecture'])
        arch = self.env.ref('synapsys.menu_config')
        self.assertEqual(Menu.search([('parent_id', '=', arch.id)]).mapped('name'), ['Form', 'Flow', 'Evolve', 'Mesh'])
        design_d = {
            'menu_arch_form': ['Purpose', 'Strategy', 'Portfolio', 'Context', 'Offering', 'Capability', 'Chain', 'Shape',
                               'Domain', 'Canonical', 'Industry', 'Partner'],
            'menu_arch_flow': ['Programme', 'Project', 'Service', 'Workflow', 'Method', 'Product', 'Work', 'Outcome', 'Benefit'],
            'menu_arch_evolve': ['Asset', 'Pattern', 'Fractal', 'Signal', 'Change', 'Market'],
        }
        actions = []
        for xid, nouns in design_d.items():
            items = Menu.search([('parent_id', '=', self.env.ref('synapsys.' + xid).id)])
            self.assertEqual(items.mapped('name'), nouns, xid)
            self.assertTrue(all(items.mapped('action')), 'every noun opens something: %s' % xid)
            actions += [str(a) for a in items.mapped('action')]
        self.assertEqual(len(actions), len(set(actions)), 'no two nouns open the same action (no duplicates)')
        everything = Menu.search([('id', 'child_of', root.id)])
        for gone in ('Value / Kinematics / Fractal', 'Value / Kinematics / Fractals', 'Strategy group labels',
                     'Fractal evidence', 'All Fractal Records', 'My Work', 'Gates', 'Regulatory'):
            self.assertNotIn(gone, everything.mapped('name'), gone)
        self.assertFalse(Menu.search_count([('parent_id', '=', self.env.ref('synapsys.menu_strategies').id)]))
        nav = Menu.search([('parent_id', '=', self.env.ref('synapsys.menu_navigator').id)])
        self.assertEqual(nav.mapped('name'), ['Progress', 'Inbox', 'Learning'])
        self.assertEqual(everything.mapped('name').count('Inbox'), 1)
        self.assertEqual(everything.mapped('name').count('Learning'), 1)

    def test_08c_navigator_ppv_inbox_learning(self):
        """Steward 20 Nov 10:03-10:05: Navigator around PPV steps; Inbox proposes, a person routes;
        Learning on every approval decision."""
        cx = self.env['synapsys.context'].create({'code': 'CTX-PPV', 'name': 'PPV test'})
        Ben = self.env['synapsys.benefit']
        b_prob = Ben.create({'name': 'B probable', 'context_id': cx.id, 'ppv': 'probable'})
        b_pot = Ben.create({'name': 'B potential', 'context_id': cx.id, 'ppv': 'potential'})
        Wo = self.env['synapsys.work.object']
        w_none = Wo.create({'name': 'No link', 'context_id': cx.id, 'status': 'open'})
        w_pot = Wo.create({'name': 'To probable', 'context_id': cx.id, 'status': 'open', 'progress_benefit_id': b_pot.id})
        w_p2v = Wo.create({'name': 'To verified', 'context_id': cx.id, 'status': 'open', 'progress_benefit_id': b_prob.id})
        self.assertEqual((w_p2v.ppv_step, w_pot.ppv_step, w_none.ppv_step), ('1_p2v', '2_pot2prob', '9_none'))
        order = Wo.search([('context_id', '=', cx.id)])
        self.assertEqual(order.ids, [w_p2v.id, w_pot.id, w_none.id], 'Probable->Verified first; no value link last, not hidden')
        b_pot.ppv = 'probable'
        self.assertEqual(w_pot.ppv_step, '1_p2v', 'the step follows the element\'s PPV')
        with self.assertRaises(ValidationError):
            Wo.create({'name': 'Two links', 'context_id': cx.id, 'progress_benefit_id': b_pot.id,
                       'progress_outcome_id': self.env['synapsys.outcome'].create({'name': 'O', 'context_id': cx.id}).id})
        sig = self.env['synapsys.signal'].create({'name': 'Client asks for collections data', 'context_id': cx.id,
                                                  'proposed_benefit_id': b_prob.id, 'approval_need': 'gate',
                                                  'proposed_by': 'AI lane (proposal)'})
        self.assertEqual(sig.state, 'new')
        self.assertFalse(sig.routed_work_object_id, 'a proposal never routes itself')
        sig.action_route()
        wo = sig.routed_work_object_id
        self.assertEqual((sig.state, wo.progress_benefit_id, wo.status, wo.ppv_step), ('routed', b_prob, 'at_gate', '1_p2v'))
        self.assertEqual(b_prob.ppv, 'probable', 'routing grades nothing')
        steward = new_test_user(self.env, login='ppv_steward', groups='synapsys.group_synapsys_steward')
        gate = self.env['synapsys.gate.decision'].create({'work_object_id': wo.id, 'evidence': 'collections ledger Oct'})
        gate.decision_note = 'evidence sufficient'
        gate.with_user(steward).action_approve()
        learn = gate.fractal_id
        self.assertEqual(learn.ffe_position, 'evolve')
        self.assertIn('Probable → Verified', learn.canonical)
        self.assertIn('Missing at decision', learn.measurement)
        self.assertIn(learn, self.env['synapsys.fractal'].search(self.env.ref('synapsys.action_nav_learning')._get_eval_domain() if hasattr(self.env.ref('synapsys.action_nav_learning'), '_get_eval_domain') else [('admission', '=', 'steward_gate')]))
        self.assertEqual(b_prob.ppv, 'probable', 'an approval records learning; it does not move PPV by itself')

    def test_08b_navigator_lenses_and_strategy_lens(self):
        nav = self.env.ref('synapsys.action_navigator')
        self.assertEqual(nav.res_model, 'synapsys.work.object')
        search = self.env.ref('synapsys.view_navigator_search').arch
        for lens in ('lens_oba', 'lens_uiq', 'lens_kda'):
            self.assertIn(lens, search)
        cx = self.env['synapsys.context'].create({'code': 'CTX-NAV', 'name': 'Nav test'})
        wo = self.env['synapsys.work.object'].create({'name': 'Nav item', 'context_id': cx.id, 'status': 'open'})
        self.assertEqual(wo.kda_state, 'not_eligible', 'missing Strategy / Service: KDA names them, never ready')
        self.assertIn('Strategy', wo.kda_missing)
        self.assertEqual(wo.oba_outcomes, cx.outcome_count)
        lens = self.env.ref('synapsys.action_strategy_lens')
        self.assertEqual(lens.res_model, 'synapsys.strategy')
        self.assertEqual(self.env.ref('synapsys.view_strategy_lens_kanban').arch.count('default_group_by="group"'), 1)

    def test_09_link_and_kind_guarded(self):
        u = new_test_user(self.env, login='collab_g', groups='synapsys.group_synapsys_user')
        a = self._asset_with_links('potential', 'probable')
        with self.assertRaises(AccessError):
            a.link_ids[:1].with_user(u).write({'ppv': 'verified'})
        with self.assertRaises(AccessError):
            a.link_ids[:1].with_user(u).write({'type': 'DIRECT'})
        cx = self.env['synapsys.context'].create({'code': 'CTX-T', 'name': 'T'})
        with self.assertRaises(AccessError):
            cx.with_user(u).write({'kind': 'K-4'})
