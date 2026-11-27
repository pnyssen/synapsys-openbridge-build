"""Work Object, Gate decision, UIQ ordering and the nine-strategy frame (V20 first journey, 19 Nov 2026).

Released by the Steward's dev-site release (MESH_QUEUE/RETURNS/RETURN_D007_V20_323_R4_DEV_SITE_RELEASE_BY_STEWARD_
20261119_v1.md, sha256 600f0be2...96c7). Field names follow the V19 register x_ss_work_object_register so its data can
map one to one later. UIQ ranks and never permits: eligible first, then Urgency, Importance, weaker Quality.
"""
from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError

from .synapsys import FFE

GROUPS = [('live', 'Live'), ('build', 'Build'), ('adapt', 'Adapt')]
WO_STATUS = [('draft', 'Draft'), ('open', 'Open'), ('at_gate', 'At Gate'), ('held', 'Held'), ('done', 'Done')]
DECISION = [('pending', 'Pending'), ('approved', 'Approved'), ('held', 'Held'), ('rejected', 'Rejected')]
UIQ = [('1', '1 low'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5 high')]
STEWARD = 'synapsys.group_synapsys_steward'

# The nine-strategy frame (Steward rulings 19 Nov 13:34, 13:39, 13:44). V19 holds only the three Build strategies;
# the six Live and Adapt strategies load as drafts sourced to the Steward's rulings, PPV empty, never as V19 rows.
# Crosswalk (governed, both kept): user-facing title <-> registered strategy name in the 27-verb register
# (synapsys.verb.strategy, reference.json). Neither side overwrites the other.
BUILD_FROM_V19 = {'STR-SS-001': (1, 'Capture Profitable Markets Repeatedly', 'Capture Valuable Markets'),
                  'STR-SS-002': (2, 'Compound Innovation', 'Compound Innovation'),
                  'STR-SS-003': (3, 'Integrate Sustainable Supply Chains', 'Integrate Value Networks')}
DRAFTS = [('STR-SS-S4', 4, 'live', 'Balanced Life', 'Quality of life and wellbeing', 'Balanced Lives'),
          ('STR-SS-S5', 5, 'live', 'Design Collaboration', 'Relationships that create value together',
           'Synergistic Collaboration'),
          ('STR-SS-S6', 6, 'live', 'Enduring Wealth', 'Wealth and capability that endure', 'Enduring Wealth'),
          ('STR-SS-S7', 7, 'adapt', 'Renew', 'Regenerate and improve', 'Renewal'),
          ('STR-SS-S8', 8, 'adapt', 'Prioritise', 'Focus on what matters most', 'Prioritisation'),
          ('STR-SS-S9', 9, 'adapt', 'Stewardship', 'Protect integrity and lasting value', 'Stewardship')]
DRAFT_SOURCE = ('DRAFT from Steward rulings (13 Nov nine-strategy description; 19 Nov 13:34/13:39/13:44 Live/Build/Adapt, '
                'strategy 6 = Enduring Wealth). Not a V19 row. PPV empty.')


class SynapsysStrategyGroupLabel(models.Model):
    """Audience labels for the three fixed strategy groups (19 Nov 13:39: labels depend on the audience).
    Changing a label never changes a Strategy, a link or a meaning."""
    _name = 'synapsys.strategy.group.label'
    _description = 'Strategy group label (per audience)'
    _order = 'audience, sequence'
    audience = fields.Char(required=True, default='steward')
    group = fields.Selection(GROUPS, required=True)
    sequence = fields.Integer(default=10)
    label = fields.Char(required=True)
    subtitle = fields.Char(help='Proposal unless the Steward has confirmed the wording.')


class SynapsysStrategyNine(models.Model):
    _inherit = 'synapsys.strategy'
    _order = 'sequence_no, code'

    group = fields.Selection(GROUPS, string='Strategy group', index=True,
                             help='Fixed key (live, build, adapt). Labels per audience live in Strategy group labels.')
    group_label = fields.Char(compute='_compute_group_label', string='Group (label)')
    sequence_no = fields.Integer(string='No.', help='Stable number 1-9 (Build 1-3, Live 4-6, Adapt 7-9).')
    display_title = fields.Char(string='Strategy (user-facing)',
                                help='User-facing name; the source name stays in Name (governed crosswalk).')
    source_basis = fields.Char(string='Source basis')
    lens_only = fields.Boolean(string='Lens only (no enterprise Strategy yet)',
                               help='True for the six Live/Adapt lenses loaded as drafts from Steward rulings. They are '
                                    'lenses, not new enterprise Strategy records; the V19 enterprise Strategies are the '
                                    'three Build rows.')
    source_type = fields.Char(string='V19 strategy type (source)')
    priority_weight = fields.Integer(string='Priority weight (source)')
    success_metric = fields.Text(string='Success metric')
    target_value = fields.Char(string='Target value')
    current_value = fields.Char(string='Current value')
    next_valid_step = fields.Text(string='Next valid step (source)')
    evidence_required = fields.Text(string='Evidence required')
    transition_trigger = fields.Text(string='Transition trigger')
    review_trigger = fields.Text(string='Review trigger')
    register_name = fields.Char(string='Registered strategy (verb register)',
                                help='Name of this strategy in the 27-verb register; the crosswalk to the title.')
    verb_ids = fields.Many2many('synapsys.verb', compute='_compute_verbs', string='Governed verbs (3)')
    work_object_ids = fields.One2many('synapsys.work.object', 'strategy_id', string='Work Objects')
    service_ids = fields.Many2many('synapsys.service', compute='_compute_reach', string='Services (via Work Objects)')
    work_object_count = fields.Integer(compute='_compute_reach')

    @api.depends_context('synapsys_audience')
    def _compute_group_label(self):
        audience = self.env.context.get('synapsys_audience', 'steward')
        Label = self.env['synapsys.strategy.group.label'].sudo()
        labels = {l.group: l.label for l in Label.search([('audience', '=', audience)])}
        names = dict(GROUPS)
        for rec in self:
            rec.group_label = labels.get(rec.group) or names.get(rec.group) or False

    @api.depends('register_name')
    def _compute_verbs(self):
        Verb = self.env['synapsys.verb']
        for rec in self:
            rec.verb_ids = Verb.search([('strategy', '=', rec.register_name)]) if rec.register_name else Verb

    @api.depends('work_object_ids.service_id')
    def _compute_reach(self):
        for rec in self:
            rec.service_ids = rec.work_object_ids.mapped('service_id')
            rec.work_object_count = len(rec.work_object_ids)

    @api.model
    def apply_nine_strategy_frame(self):
        """Idempotent. Sets the Build key, number and user-facing title on the three V19 strategies (source name kept),
        and creates the six Live/Adapt drafts if missing. Returns a count receipt."""
        if not (self.env.su or self.env.user.has_group(STEWARD)):
            raise AccessError('Only a Steward applies the nine-strategy frame.')
        ctx = self.env['synapsys.context'].search([('code', '=', 'CTX-SS')], limit=1)
        out = {'build_set': 0, 'drafts_created': 0, 'drafts_existing': 0}
        for code, (no, title, reg) in BUILD_FROM_V19.items():
            s = self.search([('code', '=', code)], limit=1)
            if s:
                s.write({'group': 'build', 'sequence_no': no, 'display_title': title, 'register_name': reg,
                         'source_basis': 'V19 source row (x_strategy) %s' % code})
                out['build_set'] += 1
        for code, no, grp, title, objective, reg in DRAFTS:
            if self.search_count([('code', '=', code)]):
                out['drafts_existing'] += 1
                continue
            self.create({'code': code, 'name': title, 'display_title': title, 'objective': objective, 'group': grp,
                         'sequence_no': no, 'lifecycle': 'draft', 'source_basis': DRAFT_SOURCE, 'register_name': reg,
                         'lens_only': True,
                         'context_id': ctx.id or False})
            out['drafts_created'] += 1
        return out


class SynapsysContextSteward(models.Model):
    _inherit = 'synapsys.context'

    steward_user_id = fields.Many2one('res.users', string='Steward (V20 user)', tracking=True,
                                      help='The person who stewards this Context in V20 (Steward binding).')
    member_ids = fields.Many2many('res.users', 'synapsys_context_member_rel', 'context_id', 'user_id',
                                  string='Members (may read this Context\'s Work Objects)')
    work_object_ids = fields.One2many('synapsys.work.object', 'context_id', string='Work Objects')


class SynapsysWorkObject(models.Model):
    _name = 'synapsys.work.object'
    _description = 'Work Object (governed unit of work)'
    _inherit = ['synapsys.cell']
    _order = 'eligible desc, urgency desc, importance desc, quality asc, id'
    _gap_fields = ['strategy_id', 'service_id', 'method_id', 'owner_id']

    code = fields.Char(string='Work Object code', help='V19 x_work_object_code', index=True)
    name = fields.Char(string='Work Object', required=True, help='V19 x_work_object_name / x_name')
    purpose_id = fields.Many2one('synapsys.purpose', related='strategy_id.purpose_id', store=True, string='Purpose')
    strategy_id = fields.Many2one('synapsys.strategy', string='Strategy', index=True)
    strategy_group = fields.Selection(related='strategy_id.group', store=True, string='Strategy group')
    service_id = fields.Many2one('synapsys.service', string='Service (executes)', help='V19 x_service_catalogue_id')
    method_id = fields.Many2one('synapsys.method', string='Method', help='V19 x_method_id')
    owner_id = fields.Many2one('res.users', string='Owner', default=lambda self: self.env.user,
                               help='V19 x_owner_user_id')
    status = fields.Selection(WO_STATUS, default='draft', required=True, string='Status', help='V19 x_status')
    controlling_verb_id = fields.Many2one('synapsys.verb', string='Controlling verb', help='V19 x_controlling_verb')
    ffe_move = fields.Selection(FFE, string='FFE move', help='V19 x_ffe_move')
    gate_level = fields.Char(string='Gate level', help='V19 x_gate_level, as written in source')
    current_gate = fields.Char(string='Current gate', help='V19 x_current_mesh_gate')
    evidence_ref = fields.Text(string='Evidence', help='V19 x_evidence_ref')
    expected_return = fields.Char(string='Expected return', help='V19 x_expected_return_ref')
    due_date = fields.Date(help='V19 x_due_date')
    parent_id = fields.Many2one('synapsys.work.object', string='Parent Work Object')
    urgency = fields.Selection(UIQ, string='U Urgency')
    importance = fields.Selection(UIQ, string='I Importance')
    quality = fields.Selection(UIQ, string='Q Quality of evidence', help='Weaker Quality ranks first.')
    eligible = fields.Boolean(compute='_compute_eligible', store=True,
                              help='Eligible = Open or At Gate. UIQ ranks; it never permits.')
    uiq = fields.Char(compute='_compute_uiq', string='UIQ')
    gate_ids = fields.One2many('synapsys.gate.decision', 'work_object_id', string='Gate decisions')
    last_decision = fields.Selection(DECISION, compute='_compute_last_decision', string='Last gate decision')
    # Navigator lenses (20 Nov 07:33): OBA = value, UIQ = prioritisation, KDA = approvals. Read-only, not stored.
    oba_outcomes = fields.Integer(related='context_id.outcome_count', string='O')
    oba_benefits = fields.Integer(related='context_id.benefit_count', string='B')
    oba_assets = fields.Integer(related='context_id.asset_count', string='A')
    oba_qualified = fields.Integer(related='context_id.qualified_asset_count', string='A qualified')
    kda_state = fields.Selection([('ready', 'Ready'), ('awaiting', 'Awaiting approval'), ('held', 'Held'),
                                  ('not_eligible', 'Not eligible')], compute='_compute_kda_state', string='KDA')
    kda_missing = fields.Char(compute='_compute_kda_state', string='KDA missing')

    @api.depends('status', 'gate_ids.decision', 'strategy_id', 'service_id', 'owner_id', 'context_id')
    def _compute_kda_state(self):
        for rec in self:
            missing = [label for f, label in (('context_id', 'Context'), ('strategy_id', 'Strategy'),
                                              ('service_id', 'Service'), ('owner_id', 'Owner')) if not rec[f]]
            rec.kda_missing = ', '.join(missing) or False
            if not rec.eligible or missing:
                rec.kda_state = 'not_eligible'
            elif rec.last_decision in ('held', 'rejected'):
                rec.kda_state = 'held'
            elif rec.last_decision == 'pending' or rec.status == 'at_gate':
                rec.kda_state = 'awaiting'
            else:
                rec.kda_state = 'ready'

    @api.depends('status')
    def _compute_eligible(self):
        for rec in self:
            rec.eligible = rec.status in ('open', 'at_gate')

    @api.depends('urgency', 'importance', 'quality')
    def _compute_uiq(self):
        for rec in self:
            rec.uiq = '%s / %s / %s' % (rec.urgency or '-', rec.importance or '-', rec.quality or '-')

    def _compute_last_decision(self):
        for rec in self:
            rec.last_decision = rec.gate_ids.sorted('id')[-1:].decision or False

    def _thread(self):
        return {'Purpose': self.purpose_id, 'Strategy': self.strategy_id}

    def action_request_gate(self):
        """Any reader with write access may ask for a Gate; only a Steward decides it."""
        for rec in self:
            if rec.status in ('done',):
                raise UserError('A Done Work Object cannot request a Gate.')
            self.env['synapsys.gate.decision'].create({
                'work_object_id': rec.id, 'gate_level': rec.gate_level, 'controlling_verb_id': rec.controlling_verb_id.id,
                'ffe_move': rec.ffe_move, 'evidence': rec.evidence_ref})
            rec.status = 'at_gate'
        return True


class SynapsysGateDecision(models.Model):
    """One governed Gate decision on a Work Object. Created pending; decided only by a Steward through the decide
    actions (the decision fields cannot be written directly). A decision writes Fractal evidence and the next action."""
    _name = 'synapsys.gate.decision'
    _description = 'Gate decision'
    _order = 'id desc'

    work_object_id = fields.Many2one('synapsys.work.object', required=True, ondelete='cascade', index=True)
    context_id = fields.Many2one(related='work_object_id.context_id', store=True)
    gate_level = fields.Char()
    controlling_verb_id = fields.Many2one('synapsys.verb', string='Controlling verb')
    ffe_move = fields.Selection(FFE, string='FFE move')
    evidence = fields.Text()
    requested_by = fields.Many2one('res.users', default=lambda self: self.env.user, readonly=True)
    requested_at = fields.Datetime(default=fields.Datetime.now, readonly=True)
    decision = fields.Selection(DECISION, default='pending', required=True, readonly=True)
    decided_by = fields.Many2one('res.users', readonly=True)
    decided_at = fields.Datetime(readonly=True)
    decision_note = fields.Text(string='Decision note')
    fractal_id = fields.Many2one('synapsys.fractal', string='Evidence record', readonly=True)

    _DECIDED = frozenset({'decision', 'decided_by', 'decided_at', 'fractal_id'})

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if self._DECIDED.intersection(k for k, v in vals.items() if v and v != 'pending'):
                raise UserError('A Gate decision is created pending; only the decide actions set the decision.')
        ctx_defaults = {k[len('default_'):] for k, v in self.env.context.items() if k.startswith('default_') and v}
        if self._DECIDED.intersection(ctx_defaults):
            raise UserError('A Gate decision cannot be pre-decided through defaults.')
        return super().create(vals_list)

    def write(self, vals):
        if self._DECIDED.intersection(vals):
            raise UserError('Use Approve, Hold or Reject; the decision is not written directly.')
        if any(r.decision != 'pending' for r in self):
            raise UserError('A decided Gate is evidence and cannot be changed.')
        return super().write(vals)

    def copy(self, default=None):
        raise UserError('Gate decisions are not copied.')

    def _decide(self, decision, next_status):
        if not self.env.user.has_group(STEWARD):
            raise AccessError('Only a Steward decides a Gate.')
        for rec in self:
            if rec.decision != 'pending':
                raise UserError('This Gate is already decided (%s).' % rec.decision)
            wo = rec.work_object_id
            fractal = self.env['synapsys.fractal'].create({
                'name': 'Gate %s: %s' % (decision, wo.name), 'context_id': wo.context_id.id,
                'res_model': wo._name, 'res_id': wo.id, 'ffe_position': rec.ffe_move or 'flow',
                'signal': 'Gate decision on Work Object %s' % (wo.code or wo.id),
                'expression': 'Steward %s: %s' % (decision, rec.decision_note or 'no note'),
                'evidence': rec.evidence or wo.evidence_ref or False, 'evidence_state': 'observed',
                'admission': 'steward_gate', 'gate_level': rec.gate_level, 'edge': 'SUPPORTS' if decision == 'approved'
                else 'CHALLENGES'})
            models.Model.write(rec, {'decision': decision, 'decided_by': self.env.uid,
                                     'decided_at': fields.Datetime.now(), 'fractal_id': fractal.id})
            wo.write({'status': next_status,
                      'next_action': {'approved': 'Execute the approved step and record its evidence',
                                      'held': 'Supply the missing evidence, then request the Gate again',
                                      'rejected': 'Revise the Work Object or close it'}[decision]})
        return True

    def action_approve(self):
        return self._decide('approved', 'open')

    def action_hold(self):
        return self._decide('held', 'held')

    def action_reject(self):
        return self._decide('rejected', 'held')
