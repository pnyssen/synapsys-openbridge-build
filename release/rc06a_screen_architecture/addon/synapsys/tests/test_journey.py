"""First-journey tests (19 Nov 2026): nine-strategy frame, Work Object -> Gate -> evidence -> next action,
Steward-only decisions and Context-scoped reading. Positive and negative cases together."""
from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install', 'synapsys')
class TestFirstJourney(TransactionCase):

    def setUp(self):
        super().setUp()
        C = self.env['synapsys.context']
        self.ss = C.search([('code', '=', 'CTX-SS')], limit=1) or C.create({'code': 'CTX-SS', 'name': 'SynapSys'})
        self.other = C.create({'code': 'CTX-OTHER-T', 'name': 'Other'})
        self.pur = self.env['synapsys.purpose'].create({'code': 'PRP-T', 'name': 'Purpose T'})
        S = self.env['synapsys.strategy']
        for code in ('STR-SS-001', 'STR-SS-002', 'STR-SS-003'):
            if not S.search_count([('code', '=', code)]):
                S.create({'code': code, 'name': 'Source ' + code, 'context_id': self.ss.id, 'purpose_id': self.pur.id})
        self.steward = new_test_user(self.env, 'jsteward', groups='synapsys.group_synapsys_steward')
        self.collab = new_test_user(self.env, 'jcollab', groups='synapsys.group_synapsys_user')
        self.outsider = new_test_user(self.env, 'joutsider', groups='synapsys.group_synapsys_user')
        self.plain = new_test_user(self.env, 'jplain', groups='base.group_user')
        self.ss.write({'steward_user_id': self.steward.id, 'member_ids': [(4, self.collab.id)]})
        self.svc = self.env['synapsys.service'].create({'code': 'SVC-T', 'name': 'Service T', 'context_id': self.ss.id})

    def test_frame_nine_strategies_idempotent_and_crosswalked(self):
        S = self.env['synapsys.strategy']
        r1 = S.with_user(self.steward).apply_nine_strategy_frame()
        r2 = S.with_user(self.steward).apply_nine_strategy_frame()
        # works on an empty or an already-loaded database: six drafts in total, none duplicated on re-run
        self.assertEqual(r1['build_set'], 3)
        self.assertEqual(r1['drafts_created'] + r1['drafts_existing'], 6)
        self.assertEqual((r2['drafts_created'], r2['drafts_existing']), (0, 6))
        nine = S.search([('sequence_no', 'in', list(range(1, 10)))])
        self.assertEqual(sorted(nine.mapped('sequence_no')), list(range(1, 10)))
        by = {g: nine.filtered(lambda s: s.group == g) for g in ('live', 'build', 'adapt')}
        self.assertEqual({g: len(r) for g, r in by.items()}, {'live': 3, 'build': 3, 'adapt': 3})
        s1 = S.search([('code', '=', 'STR-SS-001')])
        self.assertEqual(s1.display_title, 'Capture Profitable Markets Repeatedly')
        self.assertEqual(sorted(s1.verb_ids.mapped('name')), ['capture', 'map', 'sense'])
        six = S.search([('code', '=', 'STR-SS-S6')])
        self.assertEqual((six.display_title, six.lifecycle, six.group), ('Enduring Wealth', 'draft', 'live'))
        self.assertIn('Not a V19 row', six.source_basis)
        self.assertTrue(six.lens_only and not s1.lens_only)              # lenses are not enterprise Strategies
        self.assertEqual(len(six.verb_ids), 3)
        # labels per audience never change data
        self.assertEqual(s1.with_context(synapsys_audience='deliver').group_label, 'Deliver')
        self.assertEqual(s1.with_context(synapsys_audience='steward').group_label, 'Build')

    def test_frame_refused_for_non_steward(self):
        with self.assertRaises(AccessError):
            self.env['synapsys.strategy'].with_user(self.collab).apply_nine_strategy_frame()

    def test_journey_gate_evidence_next(self):
        S = self.env['synapsys.strategy']
        S.with_user(self.steward).apply_nine_strategy_frame()
        strat = S.search([('code', '=', 'STR-SS-003')])
        wo = self.env['synapsys.work.object'].with_user(self.collab).create({
            'name': 'First value-chain proof', 'context_id': self.ss.id, 'strategy_id': strat.id,
            'service_id': self.svc.id, 'status': 'open', 'urgency': '4', 'importance': '5', 'quality': '2',
            'evidence_ref': 'source note'})
        self.assertTrue(wo.purpose_id)                                  # Navigator -> Strategy -> Purpose thread
        self.assertEqual(wo.purpose_id, strat.purpose_id)
        self.assertIn(wo, strat.work_object_ids)
        self.assertIn(self.svc, strat.service_ids)                      # Strategy reaches the Service
        wo.action_request_gate()
        self.assertEqual(wo.status, 'at_gate')
        gate = wo.gate_ids
        self.assertEqual((len(gate), gate.decision), (1, 'pending'))
        with self.assertRaises(AccessError):                            # a Collaborator cannot decide
            gate.with_user(self.collab).action_approve()
        with self.assertRaises(UserError):                              # the decision is never written directly
            gate.with_user(self.steward).write({'decision': 'approved'})
        gate.with_user(self.steward).write({'decision_note': 'evidence sufficient'})
        gate.with_user(self.steward).action_approve()
        self.assertEqual((gate.decision, gate.decided_by), ('approved', self.steward))
        self.assertTrue(gate.fractal_id and gate.fractal_id.res_id == wo.id)   # evidence recorded
        self.assertEqual(wo.status, 'open')
        self.assertTrue(wo.next_action)                                 # next valid movement shown
        self.assertEqual(wo.fractal_count, 1)
        with self.assertRaises(UserError):                              # a decided Gate is evidence
            gate.with_user(self.steward).write({'decision_note': 'changed'})
        with self.assertRaises(UserError):
            gate.with_user(self.steward).action_reject()

    def test_gate_cannot_be_created_decided(self):
        wo = self.env['synapsys.work.object'].create({'name': 'w', 'context_id': self.ss.id})
        G = self.env['synapsys.gate.decision']
        with self.assertRaises(UserError):
            G.create({'work_object_id': wo.id, 'decision': 'approved'})
        with self.assertRaises(UserError):
            G.with_context(default_decision='approved').create({'work_object_id': wo.id})
        with self.assertRaises(UserError):
            G.create({'work_object_id': wo.id}).copy()

    def test_uiq_orders_eligible_then_urgency_importance_weaker_quality(self):
        W = self.env['synapsys.work.object']
        a = W.create({'name': 'a', 'context_id': self.ss.id, 'status': 'open', 'urgency': '3', 'importance': '3', 'quality': '4'})
        b = W.create({'name': 'b', 'context_id': self.ss.id, 'status': 'open', 'urgency': '3', 'importance': '3', 'quality': '1'})
        c = W.create({'name': 'c', 'context_id': self.ss.id, 'status': 'open', 'urgency': '5', 'importance': '1', 'quality': '5'})
        d = W.create({'name': 'd', 'context_id': self.ss.id, 'status': 'draft', 'urgency': '5', 'importance': '5', 'quality': '1'})
        got = W.search([('id', 'in', (a | b | c | d).ids)])
        self.assertEqual(got.ids, [c.id, b.id, a.id, d.id])

    def test_context_scoped_reading_negative_and_positive(self):
        W = self.env['synapsys.work.object']
        mine = W.create({'name': 'ss work', 'context_id': self.ss.id, 'owner_id': self.steward.id})
        theirs = W.create({'name': 'other work', 'context_id': self.other.id, 'owner_id': self.steward.id})
        seen_member = W.with_user(self.collab).search([('id', 'in', (mine | theirs).ids)])
        self.assertEqual(seen_member, mine)                             # member sees own Context only
        self.assertFalse(W.with_user(self.outsider).search([('id', 'in', (mine | theirs).ids)]))
        with self.assertRaises(AccessError):                            # direct read of another Context refused
            theirs.with_user(self.collab).read(['name'])
        with self.assertRaises(AccessError):                            # no SynapSys group: no Strategy read
            self.env['synapsys.strategy'].with_user(self.plain).search([])
        steward_seen = W.with_user(self.steward).search([('id', 'in', (mine | theirs).ids)])
        self.assertEqual(steward_seen, mine | theirs)
