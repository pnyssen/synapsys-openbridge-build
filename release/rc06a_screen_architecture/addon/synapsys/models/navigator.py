"""Navigator around Potential / Probable / Verified (Steward 20 Nov 10:03-10:05). CANDIDATE, local only.

- Every Work Object names the Outcome, Benefit or Asset it moves and the PPV step; Probable->Verified ranks
  first, then Potential->Probable, then the rest; no value link is shown last and flagged, never hidden.
- Intelligent Inbox: proposal fields for value and approval (written by an AI lane or a person as a
  proposal); only a person routes a Signal into a Work Object. Nothing here grades PPV.
- Learning: every approval decision records the PPV step, why, the evidence and what was missing.
"""
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

PPV_STEP = [('1_p2v', 'Probable → Verified'), ('2_pot2prob', 'Potential → Probable'),
            ('3_verified', 'Verified (held)'), ('9_none', 'No value link')]
APPROVAL_NEED = [('none', 'None'), ('gate', 'Gate decision'), ('steward', 'Steward ruling'), ('release', 'D007 release')]


def _step(ppv):
    return {'probable': '1_p2v', 'verified': '3_verified'}.get(ppv, '2_pot2prob')


class WorkObjectNavigator(models.Model):
    _inherit = 'synapsys.work.object'
    _order = 'ppv_step, eligible desc, urgency desc, importance desc, quality asc, id'

    progress_outcome_id = fields.Many2one('synapsys.outcome', string='Moves Outcome', index=True)
    progress_benefit_id = fields.Many2one('synapsys.benefit', string='Moves Benefit', index=True)
    progress_asset_id = fields.Many2one('synapsys.asset', string='Moves Asset', index=True)
    ppv_from = fields.Selection([('potential', 'Potential'), ('probable', 'Probable'), ('verified', 'Verified')],
                                compute='_compute_ppv_step', store=True, string='PPV now')
    ppv_step = fields.Selection(PPV_STEP, compute='_compute_ppv_step', store=True, string='PPV step', index=True)

    @api.depends('progress_outcome_id.ppv', 'progress_benefit_id.ppv', 'progress_asset_id.ppv')
    def _compute_ppv_step(self):
        for rec in self:
            target = rec.progress_asset_id or rec.progress_benefit_id or rec.progress_outcome_id
            rec.ppv_from = target.ppv if target else False
            rec.ppv_step = _step(target.ppv) if target else '9_none'

    @api.constrains('progress_outcome_id', 'progress_benefit_id', 'progress_asset_id')
    def _one_value_link(self):
        for rec in self:
            if len([x for x in (rec.progress_outcome_id, rec.progress_benefit_id, rec.progress_asset_id) if x]) > 1:
                raise ValidationError('A Work Object moves one Outcome, Benefit or Asset at a time.')


class SignalInbox(models.Model):
    _inherit = 'synapsys.signal'

    proposed_strategy_id = fields.Many2one('synapsys.strategy', string='Value: Strategy (KPI)')
    proposed_outcome_id = fields.Many2one('synapsys.outcome', string='Value: Outcome')
    proposed_benefit_id = fields.Many2one('synapsys.benefit', string='Value: Benefit')
    proposed_asset_id = fields.Many2one('synapsys.asset', string='Value: Asset')
    approval_need = fields.Selection(APPROVAL_NEED, string='Approval needed')
    proposal_note = fields.Text(string='Why (proposal)')
    proposed_by = fields.Char(string='Proposed by', help='AI lane or person that wrote the proposal; a proposal never routes itself.')
    routed_work_object_id = fields.Many2one('synapsys.work.object', string='Routed to', readonly=True)
    routed_by = fields.Many2one('res.users', readonly=True)

    def action_route(self):
        """A person routes the Signal into a Work Object in the Navigator. The proposal is carried, not graded."""
        Wo = self.env['synapsys.work.object']
        for sig in self:
            if sig.state != 'new':
                raise UserError('Only a new Signal can be routed.')
            if not sig.context_id:
                raise UserError('Name the Context first: no Context, no Work Object.')
            wo = Wo.create({
                'name': sig.name, 'context_id': sig.context_id.id, 'strategy_id': sig.proposed_strategy_id.id or False,
                'progress_outcome_id': sig.proposed_outcome_id.id or False,
                'progress_benefit_id': sig.proposed_benefit_id.id or False,
                'progress_asset_id': sig.proposed_asset_id.id or False,
                'status': 'at_gate' if sig.approval_need in ('gate', 'steward', 'release') else 'open',
                'owner_id': self.env.uid,
            })
            sig.write({'state': 'routed', 'routed_work_object_id': wo.id, 'routed_by': self.env.uid})
        return {'type': 'ir.actions.act_window', 'res_model': 'synapsys.work.object', 'res_id': wo.id,
                'view_mode': 'form'} if len(self) == 1 else True


class GateDecisionLearning(models.Model):
    _inherit = 'synapsys.gate.decision'

    def _decide(self, decision, next_status):
        """Learning on every approval decision: the PPV step, why, the evidence, and what was missing."""
        before = {rec.id: (rec.work_object_id.ppv_step, rec.work_object_id.kda_missing) for rec in self}
        res = super()._decide(decision, next_status)
        labels = dict(PPV_STEP)
        for rec in self:
            step, missing = before[rec.id]
            target = (rec.work_object_id.progress_asset_id or rec.work_object_id.progress_benefit_id
                      or rec.work_object_id.progress_outcome_id)
            rec.fractal_id.write({
                'ffe_position': 'evolve',
                'canonical': 'Approval (KDA) on PPV step: %s%s' % (labels.get(step, step),
                                                                 ' of %s' % target.display_name if target else ''),
                'measurement': 'Missing at decision: %s' % (missing or 'nothing'),
                'notes': 'Learning record: why = decision note; evidence = evidence field. AI does not grade.',
            })
        return res
