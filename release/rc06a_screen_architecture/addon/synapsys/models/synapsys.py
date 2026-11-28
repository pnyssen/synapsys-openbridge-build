import hashlib
# -*- coding: utf-8 -*-
"""SynapSys kinematic Mesh, v20.

Rules carried in code (rulings ledger, claude/synapsys-core-definitions-and-rulings-ledger.md):
- Context contains all; Portfolio holds Assets; Programmes and Services deliver Benefits; Projects deliver Outcomes.
- A Benefit correlates to a value chain (15 Nov 22:30): chain and stage live on the Benefit.
- Asset qualifies only with >=3 distinct same-chain DIRECT links whose link and Benefit are Probable or above,
  plus rights holder and basis, not a component, no rights still required (S7, S8, load set counts_require).
- Official kind stays empty unless ruled; a proposed kind is held with its source (C1).
- Nothing is promoted by load or by a non-Steward (no AI promotion).
- Missing source values are shown as GAP, never filled in.
"""
import json
from markupsafe import Markup, escape
from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

KINDS = [('K-1', 'Purpose (K-1)'), ('K-3', 'Strategy (K-3)'), ('K-4', 'Asset (K-4)'),
         ('K-6', 'Offering (K-6)'), ('K-8', 'Collaboration (K-8)'), ('K-12', 'Platform (K-12)')]
FFE = [('form', 'Form'), ('flow', 'Flow'), ('evolve', 'Evolve')]
PPV = [('potential', 'Potential'), ('probable', 'Probable'), ('verified', 'Verified')]
PPV_RANK = {False: 0, 'potential': 1, 'probable': 2, 'verified': 3}
PERSPECTIVE = [('internal', 'Internal'), ('membrane', 'Membrane'), ('external', 'External')]
THREAD = ['Purpose', 'Strategy', 'Portfolio', 'Programme', 'Project', 'Outcome', 'Benefit', 'Asset']
PROTECTED = {'ppv', 'observed', 'answer_accepted', 'rights_confirmed', 'baseline_observed', 'kind'}


class SynapsysGuard(models.AbstractModel):
    """Promotion guard: protected fields change only by a Steward (and, with synapsys_approvals, only through an approved request)."""
    _name = 'synapsys.guard'
    _description = 'SynapSys promotion guard'
    _protected = PROTECTED

    def _check_promotion_rights(self, vals):
        touched = set(self._protected).intersection(vals)
        if touched and not self.env.su and not self.env.user.has_group('synapsys.group_synapsys_steward'):
            raise AccessError('Only a Steward can change %s.' % ', '.join(sorted(touched)))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._check_promotion_rights({k: v for k, v in vals.items() if v and v != 'potential'})
        return super().create(vals_list)

    def write(self, vals):
        self._check_promotion_rights(vals)
        return super().write(vals)


SHAPES = [('1', '1'), ('3', '3'), ('4', '4'), ('6', '6'), ('8', '8'), ('12', '12')]
CONTRACT_SCHEMA = 'synapsys.kinematic.contract/1'


class SynapsysKinematic(models.AbstractModel):
    """Universal Kinematic Contract (task 197, P1/P6): one typed projection of a record, used by the card,
    the drill-down, the workflow and the AI view alike. Eligible verbs come only from the ruled kind of the
    record's Context (never from the proposed kind); kind, shape and approval floor are kept apart.
    The projection grants nothing and has no write path; it reads with the caller's own rights (no sudo)."""
    _name = 'synapsys.kinematic'
    _description = 'SynapSys Kinematic Contract'

    eligible_verb_ids = fields.Many2many('synapsys.verb', compute='_compute_eligible_verbs',
                                         string='Eligible verbs (ruled kind)')
    eligible_verb_count = fields.Integer(compute='_compute_eligible_verbs', string='Eligible verbs')

    def _kinematic_context(self):
        return self['context_id'] if 'context_id' in self._fields else self.env['synapsys.context']

    def _compute_eligible_verbs(self):
        Mode = self.env['synapsys.mode']
        for rec in self:
            kind = rec._kinematic_context().kind
            verbs = Mode.search([('code', '=', kind)], limit=1).verb_ids if kind else self.env['synapsys.verb']
            verbs = verbs.filtered(lambda v: not v.human_only)
            rec.eligible_verb_ids = verbs
            rec.eligible_verb_count = len(verbs)

    def _kinematic_contract(self):
        """The contract for one readable record. Absent values are reported as GAP, never filled in."""
        self.ensure_one()
        cx = self._kinematic_context()
        Verb = self.env['synapsys.verb']
        moded = self.env['synapsys.mode'].search([]).verb_ids
        f = self._fields

        def val(name):
            return (self[name] or None) if name in f else None
        return {
            'schema': CONTRACT_SCHEMA,
            'visibility': 'VISIBLE',
            'model': self._name,
            'id': self.id,
            'name': self.display_name,
            'context': {'code': cx.code, 'kind_ruled': cx.kind or 'GAP', 'kind_proposed': cx.kind_proposed or None}
            if cx else 'GAP',
            'shape': (val('shape') or 'GAP') if 'shape' in f else 'NOT_CARRIED',
            'perspective': val('perspective'),
            'ffe': {k: val(k + '_note') for k in ('form', 'flow', 'evolve')},
            'eligible_verbs': self.eligible_verb_ids.sorted('sequence').mapped('name'),
            'verbs_mode_not_ruled': (Verb.search([]) - moded).filtered(lambda v: not v.human_only)
                                    .sorted('sequence').mapped('name'),
            'gap_count': val('gap_count') or 0,
            'next_action': val('next_action'),
            'ppv': val('ppv'),
            'authority': 'none: this projection grants nothing',
        }

    def kinematic_contract_json(self):
        """Read-only AI projection: the same contract the screen uses. Records the caller cannot read are
        returned as NOT_VISIBLE with no other detail. No sudo, no write."""
        out = []
        for rec in self:
            try:
                rec.check_access('read')
            except AccessError:
                out.append({'schema': CONTRACT_SCHEMA, 'visibility': 'NOT_VISIBLE'})
                continue
            out.append(rec._kinematic_contract())
        return json.dumps(out, ensure_ascii=False, default=str)


class SynapsysCell(models.AbstractModel):
    """Shared cell: header and thread, plain answer (AI draft, sourced), numbers, FFE lens, next action, GAPs."""
    _name = 'synapsys.cell'
    _inherit = ['synapsys.guard', 'synapsys.kinematic']
    _description = 'SynapSys Cell'
    _gap_fields = []

    context_id = fields.Many2one('synapsys.context', string='Context', index=True)
    context_kind = fields.Selection(related='context_id.kind', string='Context kind (ruled)')
    context_kind_proposed = fields.Char(related='context_id.kind_proposed', string='Context kind (proposed)')
    domain_id = fields.Many2one('synapsys.domain', string='Domain', index=True)
    v19_id = fields.Integer(string='v19 id', index=True, help='Source record in v19 (read-only evidence).')
    answer = fields.Text(string='Plain answer (AI draft)')
    answer_source = fields.Char(string='Answer source and date')
    answer_accepted = fields.Boolean(string='Answer accepted by a human', default=False)
    next_action = fields.Char(string='Next authorised action')
    thread_html = fields.Html(string='Thread', compute='_compute_thread_html', sanitize=False)
    gap_html = fields.Html(string='Gaps', compute='_compute_gaps', sanitize=False)
    gap_count = fields.Integer(compute='_compute_gaps', string='Gap count')
    fractal_count = fields.Integer(compute='_compute_fractal_count', string='Fractal records')
    form_note = fields.Text(string='Form (structure / meaning)')
    flow_note = fields.Text(string='Flow (use / journey)')
    evolve_note = fields.Text(string='Evolve (learning / correction)')

    def _thread(self):
        return {}

    def _compute_thread_html(self):
        for rec in self:
            parts = rec._thread()
            out = []
            for label in THREAD:
                r = parts.get(label)
                if r:
                    out.append(Markup('<b>%s</b> %s') % (label, escape(r.display_name)))
                elif label in parts:
                    out.append(Markup('<span class="text-warning">%s GAP</span>') % label)
            rec.thread_html = Markup(' › ').join(out) if out else False

    def _compute_gaps(self):
        for rec in self:
            gaps = []
            for fname in rec._gap_fields:
                if not rec[fname]:
                    gaps.append(rec._fields[fname].string)
            rec.gap_count = len(gaps)
            rec.gap_html = (Markup('<b>GAP</b> (not in source; to be supplied, never inferred): ') +
                            Markup(', ').join(escape(g) for g in gaps)) if gaps else False

    def _compute_fractal_count(self):
        F = self.env['synapsys.fractal']
        for rec in self:
            rec.fractal_count = F.search_count([('res_model', '=', rec._name), ('res_id', '=', rec.id)]) if rec.id else 0

    def action_open_fractal(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_window', 'res_model': 'synapsys.fractal', 'name': 'Fractal records',
                'view_mode': 'list,form', 'domain': [('res_model', '=', self._name), ('res_id', '=', self.id)],
                'context': {'default_res_model': self._name, 'default_res_id': self.id,
                            'default_context_id': self.context_id.id}}

    def _open(self, model, name, domain):
        return {'type': 'ir.actions.act_window', 'res_model': model, 'name': name,
                'view_mode': 'list,form', 'domain': domain}


# ---------------------------------------------------------------- reference

class SynapsysDomain(models.Model):
    _name = 'synapsys.domain'
    _description = 'Governing Domain'
    _order = 'code'
    code = fields.Char(required=True)
    name = fields.Char(required=True)
    canon_ids = fields.One2many('synapsys.canon', 'domain_id', string='Charters and canon')
    intelligence_ids = fields.One2many('synapsys.intelligence', 'domain_id', string='Intelligence')
    learning_ids = fields.One2many('synapsys.learning', 'domain_id', string='Adaptability (learning)')
    # Seat instructions (Steward 20 Nov 2026 11:03, 11:14): each domain's own instructions live here, in the
    # Architecture, beside its charter. Working Memory holds a mirror for other environments, hash-checked.
    instruction_id = fields.Many2one('synapsys.canon', compute='_compute_instructions', string='Own instructions (current)')
    core_instruction_id = fields.Many2one('synapsys.canon', compute='_compute_instructions', string='Core instructions (shared)')
    seat_instruction_text = fields.Text(compute='_compute_instructions', string='Seat instruction set')
    seat_instruction_sha = fields.Char(compute='_compute_instructions', string='Seat instruction set sha256')
    _code_uniq = models.Constraint('UNIQUE(code)', 'Domain code must be unique.')

    def _compute_instructions(self):
        Canon = self.env['synapsys.canon']
        core = Canon.search([('kind', '=', 'instruction'), ('shared', '=', True), ('state', '=', 'adopted')], limit=1)
        for r in self:
            own = Canon.search([('kind', '=', 'instruction'), ('domain_id', '=', r.id), ('shared', '=', False),
                                ('state', '=', 'adopted')], order='id desc', limit=1)
            r.core_instruction_id, r.instruction_id = core, own
            parts = [x.body for x in (core | own) if x.body]
            text = '\n\n---\n\n'.join(parts)
            r.seat_instruction_text = text or False
            r.seat_instruction_sha = hashlib.sha256(text.encode('utf-8')).hexdigest() if text else False

    @api.depends('code', 'name')
    def _compute_display_name(self):
        for r in self:
            r.display_name = '%s %s' % (r.code or '', r.name or '')


class SynapsysVerb(models.Model):
    _name = 'synapsys.verb'
    _description = 'Governed Verb'
    _order = 'sequence'
    name = fields.Char(required=True)
    strategy = fields.Char(required=True)
    sequence = fields.Integer()
    movement = fields.Char()
    movement_group = fields.Char()
    motion = fields.Char()
    # Grammar (candidate source, DEC-D001-2026-021): what the verb means, which way it points, who may use it.
    plane = fields.Char(help='Govern / Deliver / Realise (Steward governance view of the same 27).')
    action = fields.Char()
    direction = fields.Char(help='Source-to-target reading of the canonical verb.')
    aliases = fields.Char(help='Approved derivative forms, same meaning and direction, comma separated.')
    inverse = fields.Char(help='Reverse-navigation form: reads the edge target-to-source; never reverses authority.')
    bidirectionality = fields.Char()
    authority_requirement = fields.Char()
    human_only = fields.Boolean(help='Only an authorised human may use this verb (commit). Never offered to AI or workflow.')
    grammar_status = fields.Char(default='candidate')
    grammar_sha256 = fields.Char(string='Grammar source sha256')
    _name_uniq = models.Constraint('UNIQUE(name)', 'Verb names must be unique.')

    @api.model
    def _resolve(self, word):
        """Normalise a canonical name or an approved derivative to one of the 27.
        Returns (verb, reversed): reversed is True when the word is the inverse form, so the caller swaps the edge ends.
        Unknown words return (empty, False): nothing is invented."""
        w = (word or '').strip().lower()
        if not w:
            return self.browse(), False
        for v in self.search([]):
            if w == v.name:
                return v, False
            if w in [a.strip() for a in (v.aliases or '').split(',') if a.strip()]:
                return v, False
            if v.inverse and w == v.inverse.strip():
                return v, True
        return self.browse(), False


class SynapsysMode(models.Model):
    _name = 'synapsys.mode'
    _description = 'Kinematic Mode'
    _order = 'id'
    code = fields.Selection(KINDS, required=True)
    name = fields.Char(required=True)
    verb_ids = fields.Many2many('synapsys.verb', string='Verbs in this mode')


class SynapsysPurpose(models.Model):
    _name = 'synapsys.purpose'
    _description = 'Purpose'
    code = fields.Char(required=True)
    name = fields.Char(required=True)
    description = fields.Text()


class SynapsysCanon(models.Model):
    _name = 'synapsys.canon'
    _description = 'Canonical Library entry'
    _order = 'tier, name'
    name = fields.Char(required=True)
    tier = fields.Selection([('tier_1_canonical_core', 'Tier 1 canonical core'),
                             ('tier_2_governance', 'Tier 2 governance'), ('tier_3_corpus', 'Tier 3 corpus'),
                             ('candidate', 'Candidate')])
    domain_id = fields.Many2one('synapsys.domain')
    v19_id = fields.Integer(index=True)
    # V19 source links (typed so they navigate; source of truth stays the immutable envelope)
    context_id = fields.Many2one('synapsys.context', string='Context (source)', readonly=True, help='V19 source link, written only by the released source load.')
    supersedes_id = fields.Many2one('synapsys.canon', string='Supersedes (source)', readonly=True, help='V19 source link, written only by the released source load.')
    # Content held in the Architecture (Steward 20 Nov 11:14): text, version, hash and state, so the library is
    # read here rather than chased across stores. The hash is computed from the text and must match it.
    kind = fields.Selection([('charter', 'Charter'), ('instruction', 'Seat instructions'), ('reference', 'Reference')],
                            default='reference', index=True)
    shared = fields.Boolean(help='Read by every domain seat (the core D000/D001/D002 profile).')
    version = fields.Char()
    state = fields.Selection([('candidate', 'Candidate'), ('adopted', 'Adopted'), ('canon_promoted', 'Canon promoted'),
                              ('superseded', 'Superseded')], default='candidate', index=True)
    body = fields.Text(string='Text')
    sha256 = fields.Char(string='sha256 of the text')
    mirror_path = fields.Char(string='Working Memory mirror', help='Copy for other environments; must hash the same.')
    adopted_note = fields.Char(string='Adoption record')
    replaces_id = fields.Many2one('synapsys.canon', string='Replaces', help='Earlier version this one supersedes.')

    source_sha256 = fields.Char(string='sha256 of the source file', help='e.g. the charter .docx the text was extracted from.')

    @api.model
    def extract_docx_text(self, data):
        """Plain text of a .docx (paragraphs in order). Standard library only; nothing is interpreted."""
        import io, re, zipfile
        from xml.etree import ElementTree as ET
        ns = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            root = ET.fromstring(z.read('word/document.xml'))
        paras = []
        for p in root.iter(ns + 'p'):
            t = ''.join(x.text or '' for x in p.iter(ns + 't'))
            if t.strip():
                paras.append(t)
        return re.sub(r'\n{3,}', '\n\n', '\n\n'.join(paras)) + '\n'

    @api.model
    def hold_charter_extract(self, domain_code, name, version, data, expected_source_sha256, state='candidate'):
        """Hold a charter's text in the library, bound to its domain and to the hash of the source file.
        Refuses (zero writes) if the bytes do not hash to the expected value, e.g. the V19 library row's x_sha256."""
        got = hashlib.sha256(data).hexdigest()
        if got != expected_source_sha256:
            raise UserError('Charter %s: source file hashes to %s, not the expected %s. Nothing held.'
                            % (name, got[:12], (expected_source_sha256 or '')[:12]))
        dom = self.env['synapsys.domain'].search([('code', '=', domain_code)], limit=1)
        if not dom:
            raise UserError('Charter %s: domain %s not found.' % (name, domain_code))
        text = self.extract_docx_text(data)
        return self.create({'name': name, 'kind': 'charter', 'tier': 'tier_2_governance', 'domain_id': dom.id,
                            'version': version, 'state': state, 'body': text,
                            'sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(), 'source_sha256': got})

    def link_charters_to_domains(self):
        """Attach charter rows to their domain by the code at the start of the name (\"D004 — ...\").
        Rows already linked, or with no domain code, are left alone; returns the rows linked."""
        import re
        doms = {d.code: d for d in self.env['synapsys.domain'].search([])}
        linked = self.browse()
        for r in (self or self.search([('domain_id', '=', False)])):
            m = re.match(r'^(D0\d\d)\b', r.name or '')
            if m and not r.domain_id and m.group(1) in doms and 'charter' in (r.name or '').lower():
                models.Model.write(r, {'domain_id': doms[m.group(1)].id, 'kind': 'charter'})
                linked |= r
        return linked

    @api.constrains('body', 'sha256')
    def _check_body_hash(self):
        for r in self:
            if r.body and r.sha256 != hashlib.sha256(r.body.encode('utf-8')).hexdigest():
                raise ValidationError('Canonical text and its sha256 do not match: %s' % r.name)

    def write(self, vals):
        if {'body', 'sha256'} & set(vals) and any(r.body for r in self):
            raise UserError('Canonical text is immutable once held. Create a new version that replaces it.')
        return super().write(vals)


class SynapsysIntelligence(models.Model):
    """Intelligence part of the one library (IAC Goal Anchor 21 Sep 2026: V19 x_ss_intelligence_asset).
    Held here so Canonical, Intelligence and Adaptability are read in one place. Source records that name
    people are personal data: not loaded without a Steward decision (20 Nov 2026)."""
    _name = 'synapsys.intelligence'
    _description = 'Intelligence (library)'
    _order = 'id'
    name = fields.Char(required=True)
    intelligence_type = fields.Char()
    asset_class = fields.Char()
    summary = fields.Text()
    evidence_reference = fields.Char()
    context_id = fields.Many2one('synapsys.context')
    domain_id = fields.Many2one('synapsys.domain')
    validation_status = fields.Char(help='V19 verbatim.')
    source_ppv_state = fields.Char(help='V19 verbatim evidence; not the protected V20 PPV.')
    human_review_required = fields.Boolean()
    created_from_ai = fields.Boolean()
    visibility_scope = fields.Char()
    personal_data = fields.Boolean(help='Names or describes a person: held only under a Steward decision.')
    next_valid_step = fields.Text()
    review_trigger = fields.Char()
    v19_id = fields.Integer(index=True)


class SynapsysLearning(models.Model):
    """Adaptability part of the one library (V19 x_ss_method_learning): what was observed, what it implies,
    and what may change. Canon changes only by release; learning is held here, not promoted by AI."""
    _name = 'synapsys.learning'
    _description = 'Adaptability: method learning (library)'
    _order = 'id desc'
    name = fields.Char(required=True)
    method_id = fields.Many2one('synapsys.method')
    context_id = fields.Many2one('synapsys.context')
    domain_id = fields.Many2one('synapsys.domain')
    observation = fields.Text()
    implication = fields.Text()
    root_cause = fields.Text()
    evidence_anchor = fields.Text()
    next_valid_step = fields.Text()
    learning_category = fields.Char()
    learning_theme = fields.Char()
    learning_priority = fields.Char()
    review_status = fields.Char(help='V19 verbatim.')
    governance_action = fields.Char(help='V19 verbatim.')
    trigger_type = fields.Char()
    asset_conversion_candidate = fields.Boolean()
    v19_id = fields.Integer(index=True)


class SynapsysMethod(models.Model):
    _name = 'synapsys.method'
    _description = 'Registered Method'
    _order = 'code'
    code = fields.Char(required=True)
    name = fields.Char(required=True)
    lifecycle = fields.Selection([('active', 'Active'), ('draft', 'Draft'), ('registered', 'Registered')],
                                 help='v19 x_canonical_status, unchanged.')
    v19_id = fields.Integer(index=True)
    service_ids = fields.One2many('synapsys.service', 'method_id')
    context_id = fields.Many2one('synapsys.context', string='Context (source)', readonly=True, help='V19 source link, written only by the released source load.')
    canon_id = fields.Many2one('synapsys.canon', string='Governing canon (source)', readonly=True, help='V19 source link, written only by the released source load.')
    supporting_canon_ids = fields.Many2many('synapsys.canon', 'synapsys_method_canon_support_rel', 'method_id',
                                            'canon_id', string='Supporting canon (source)', readonly=True, help='V19 source link, written only by the released source load.')
    pattern_ids = fields.Many2many('synapsys.pattern', 'synapsys_method_pattern_rel', 'method_id', 'pattern_id',
                                   string='Patterns (source, Method side)', readonly=True, help='V19 source link, written only by the released source load.')
    related_method_ids = fields.Many2many('synapsys.method', 'synapsys_method_related_rel', 'method_id',
                                          'related_id', string='Related Methods (source)', readonly=True, help='V19 source link, written only by the released source load.')


class SynapsysPattern(models.Model):
    _name = 'synapsys.pattern'
    _description = 'Pattern'
    _order = 'code'
    code = fields.Char(required=True)
    name = fields.Char()
    value_category = fields.Char()
    ppv = fields.Selection(PPV, string='PPV')
    v19_id = fields.Integer()
    context_id = fields.Many2one('synapsys.context', string='Context (source)', readonly=True, help='V19 source link, written only by the released source load.')
    applicable_context_id = fields.Many2one('synapsys.context', string='Applicable Context (source)', readonly=True, help='V19 source link, written only by the released source load.')
    parent_id = fields.Many2one('synapsys.pattern', string='Parent Pattern (source)', readonly=True, help='V19 source link, written only by the released source load.')
    canon_ids = fields.Many2many('synapsys.canon', 'synapsys_pattern_canon_rel', 'pattern_id', 'canon_id',
                                 string='Canon (source)', readonly=True, help='V19 source link, written only by the released source load.')
    # Inverse views of the Service-side and Method-side source links (one source of truth per pair; the
    # Pattern-side V19 lists stay in the envelope so any asymmetry in V19 is preserved, not merged).
    service_ids = fields.Many2many('synapsys.service', 'synapsys_service_pattern_rel', 'pattern_id', 'service_id',
                                   string='Services (via Service side)', readonly=True)
    method_ids = fields.Many2many('synapsys.method', 'synapsys_method_pattern_rel', 'pattern_id', 'method_id',
                                  string='Methods (via Method side)', readonly=True)


# ---------------------------------------------------------------- Context

class SynapsysContext(models.Model):
    _name = 'synapsys.context'
    _protected = {'kind'}
    _description = 'Context'
    _inherit = ['mail.thread', 'synapsys.guard', 'synapsys.kinematic']
    _order = 'code'
    code = fields.Char(required=True, tracking=True)
    name = fields.Char(tracking=True)
    v19_id = fields.Integer(index=True)
    kind = fields.Selection(KINDS, string='Kinematic kind (ruled)', tracking=True)
    kind_ruling = fields.Char(string='Kind ruling')
    kind_proposed = fields.Char(string='Kind (proposed)')
    kind_proposed_source = fields.Char(string='Proposed kind source')
    partner_id = fields.Many2one('res.partner', string='Owner (rights holder)')
    parent_id = fields.Many2one('synapsys.context', string='Parent Context')
    child_ids = fields.One2many('synapsys.context', 'parent_id', string='Child Contexts')
    purpose_id = fields.Many2one('synapsys.purpose')
    domain_id = fields.Many2one('synapsys.domain')
    answer = fields.Text(string='Plain answer (AI draft)')
    answer_source = fields.Char(string='Answer source and date')
    next_action = fields.Char(string='Next authorised action')
    exception_state = fields.Char(string='Exception')
    exception_ruling = fields.Char()
    exception_reason = fields.Text()
    exception_scope = fields.Text()
    exception_decided_by = fields.Char()
    exception_decided_at = fields.Char()
    exception_expires = fields.Date(string='Exception expires')
    exception_reviewer = fields.Char()
    exception_on_expiry = fields.Text()
    exception_expired = fields.Boolean(compute='_compute_exception_expired')
    intersection_ids = fields.One2many('synapsys.intersection', 'context_id', string='Intersections')
    strategy_ids = fields.One2many('synapsys.strategy', 'context_id')
    portfolio_ids = fields.One2many('synapsys.portfolio', 'context_id')
    programme_ids = fields.One2many('synapsys.programme', 'context_id')
    outcome_ids = fields.One2many('synapsys.outcome', 'context_id')
    benefit_ids = fields.One2many('synapsys.benefit', 'context_id')
    asset_ids = fields.One2many('synapsys.asset', 'context_id')
    strategy_count = fields.Integer(compute='_compute_counts')
    programme_count = fields.Integer(compute='_compute_counts')
    outcome_count = fields.Integer(compute='_compute_counts')
    benefit_count = fields.Integer(compute='_compute_counts')
    asset_count = fields.Integer(compute='_compute_counts')
    qualified_asset_count = fields.Integer(compute='_compute_counts', string='Qualified Assets')
    gap_html = fields.Html(compute='_compute_gaps', sanitize=False)
    gap_count = fields.Integer(compute='_compute_gaps', string='Gap count')
    portal_published = fields.Boolean(string='Show on portal', default=False)
    _code_uniq = models.Constraint('UNIQUE(code)', 'Context code must be unique.')

    @api.depends('code', 'name')
    def _compute_display_name(self):
        for r in self:
            r.display_name = r.name or r.code

    def _kinematic_context(self):
        return self

    def _compute_exception_expired(self):
        today = fields.Date.context_today(self)
        for r in self:
            r.exception_expired = bool(r.exception_expires and r.exception_expires < today)

    @api.depends('strategy_ids', 'programme_ids', 'outcome_ids', 'benefit_ids', 'asset_ids', 'asset_ids.qualifies')
    def _compute_counts(self):
        for r in self:
            r.strategy_count = len(r.strategy_ids)
            r.programme_count = len(r.programme_ids)
            r.outcome_count = len(r.outcome_ids)
            r.benefit_count = len(r.benefit_ids)
            r.asset_count = len(r.asset_ids)
            r.qualified_asset_count = len(r.asset_ids.filtered('qualifies'))

    def _compute_gaps(self):
        for r in self:
            gaps = []
            if not r.name:
                gaps.append('Name')
            if not r.kind:
                gaps.append('Kinematic kind (Steward to rule%s)' % (
                    '; proposed %s' % r.kind_proposed if r.kind_proposed else ''))
            if not r.purpose_id:
                gaps.append('Purpose')
            if not r.domain_id:
                gaps.append('Domain')
            r.gap_count = len(gaps)
            r.gap_html = (Markup('<b>GAP</b>: ') + Markup(', ').join(escape(g) for g in gaps)) if gaps else False

    def _o(self, model, name):
        self.ensure_one()
        return {'type': 'ir.actions.act_window', 'res_model': model, 'name': name, 'view_mode': 'list,form',
                'domain': [('context_id', '=', self.id)], 'context': {'default_context_id': self.id}}

    def action_strategies(self): return self._o('synapsys.strategy', 'Strategies')
    def action_programmes(self): return self._o('synapsys.programme', 'Programmes')
    def action_outcomes(self): return self._o('synapsys.outcome', 'Outcomes')
    def action_benefits(self): return self._o('synapsys.benefit', 'Benefits')
    def action_assets(self): return self._o('synapsys.asset', 'Assets')


class SynapsysIntersection(models.Model):
    _name = 'synapsys.intersection'
    _description = 'Context intersection (INTERSECTS; own measures, never summed into the parent)'
    context_id = fields.Many2one('synapsys.context', required=True, ondelete='cascade')
    type = fields.Char(default='INTERSECTS')
    to_chain_id = fields.Many2one('synapsys.value.chain', string='Chain')
    to_context_id = fields.Many2one('synapsys.context', string='Intersecting Context')
    to_industry = fields.Char(string='Industry offering')
    measures = fields.Text()


class SynapsysIndustryOffering(models.Model):
    _name = 'synapsys.industry.offering'
    _description = 'Industry offering (target dataset and chains; not a Context, not a lead)'
    key = fields.Char(required=True)
    name = fields.Char()
    v19_id = fields.Integer()
    drawn_on_by = fields.Char()
    attribute_model = fields.Text()
    target_dataset = fields.Text()
    ruling = fields.Char()


# ---------------------------------------------------------------- value chains

class SynapsysValueChain(models.Model):
    _name = 'synapsys.value.chain'
    _description = 'Value Chain'
    _order = 'code'
    code = fields.Char(required=True)
    scope = fields.Char()
    type = fields.Char()
    industry = fields.Char()
    owner_service = fields.Char(string='Owner Service (code)')
    is_pattern = fields.Boolean()
    source = fields.Text()
    source_grade = fields.Char()
    source_stages = fields.Char(string='Source stages (catalogue)')
    stage_ids = fields.One2many('synapsys.value.chain.stage', 'chain_id', string='Stages (3/4/6/8 view)')
    stage_count = fields.Integer(compute='_compute_stage_count', store=True)
    benefit_ids = fields.One2many('synapsys.benefit', 'chain_id')
    _code_uniq = models.Constraint('UNIQUE(code)', 'Value chain code must be unique.')

    @api.depends('code')
    def _compute_display_name(self):
        for r in self:
            r.display_name = r.code

    @api.depends('stage_ids')
    def _compute_stage_count(self):
        for r in self:
            r.stage_count = len(r.stage_ids)

    @api.constrains('stage_ids')
    def _check_stage_shape(self):
        for r in self:
            if r.stage_ids and len(r.stage_ids) not in (3, 4, 6, 8):
                raise ValidationError('A value chain has 3, 4, 6 or 8 stages (ruled 17 Nov 00:48). %s has %d.'
                                      % (r.code, len(r.stage_ids)))


class SynapsysValueChainStage(models.Model):
    _name = 'synapsys.value.chain.stage'
    _description = 'Value Chain Stage'
    _order = 'chain_id, sequence'
    chain_id = fields.Many2one('synapsys.value.chain', required=True, ondelete='cascade')
    sequence = fields.Integer()
    name = fields.Char(required=True)
    origin = fields.Selection([('SOURCE', 'Source'), ('STEWARD_DEFINED', 'Steward defined')],
                              required=True, default='SOURCE')
    source_stages = fields.Char(help='Catalogue stages this view stage carries.')
    source_verbs = fields.Char()
    basis = fields.Text(help='Why a non-source stage exists, and whether the choice is still pending.')


# ---------------------------------------------------------------- Strategy, Portfolio, Programme

class SynapsysStrategy(models.Model):
    _name = 'synapsys.strategy'
    _description = 'Strategy'
    _inherit = ['synapsys.cell']
    _gap_fields = ['code', 'purpose_id', 'domain_id']
    code = fields.Char()
    name = fields.Char(required=True)
    objective = fields.Text()
    purpose_id = fields.Many2one('synapsys.purpose')
    lifecycle = fields.Selection([('draft', 'Draft'), ('active', 'Active'), ('retired', 'Retired')])
    portfolio_ids = fields.One2many('synapsys.portfolio', 'strategy_id', string='Portfolios (source link)')

    def _thread(self):
        return {'Purpose': self.purpose_id, 'Strategy': self}


class SynapsysPortfolio(models.Model):
    _name = 'synapsys.portfolio'
    _description = 'Portfolio (holds enduring Assets)'
    _inherit = ['synapsys.cell']
    _gap_fields = ['strategy_id', 'domain_id']
    name = fields.Char(required=True)
    strategy_id = fields.Many2one('synapsys.strategy', string='Strategy (source link)')
    programme_ids = fields.One2many('synapsys.programme', 'portfolio_id')
    asset_ids = fields.One2many('synapsys.asset', 'portfolio_id')

    def _thread(self):
        return {'Purpose': self.strategy_id.purpose_id, 'Strategy': self.strategy_id, 'Portfolio': self}


class SynapsysProgramme(models.Model):
    """Programme package P1-P12 (15 Nov 22:30 ruling, 5B design): investment + governance + value chain +
    engagement to deliver Benefits; exists because new capability is needed."""
    _name = 'synapsys.programme'
    _description = 'Programme'
    _inherit = ['synapsys.cell']
    _gap_fields = ['value_chain_id', 'analytic_account_ref', 'sponsor', 'owner_id', 'partner_ids', 'service_ids']
    code = fields.Char()
    name = fields.Char(required=True)
    lifecycle = fields.Selection([('draft', 'Draft'), ('structured', 'Structured'), ('active', 'Active'),
                                  ('closed', 'Closed')], help='v19 x_program_status, unchanged.')
    portfolio_id = fields.Many2one('synapsys.portfolio')
    strategy_id = fields.Many2one('synapsys.strategy')
    # Commit
    benefit_ids = fields.One2many('synapsys.benefit', 'programme_id', string='P1 Benefits committed')
    value_chain_id = fields.Many2one('synapsys.value.chain', string='P2 Value chain')
    benefit_chain_codes = fields.Char(compute='_compute_package', string='Chains of its Benefits')
    # Package
    analytic_account_ref = fields.Char(string='P4 Investment (analytic account / budget)')
    sponsor = fields.Char(string='P5 Sponsor')
    owner_id = fields.Many2one('res.users', string='P5 Owner')
    partner_ids = fields.Many2many('res.partner', string='P6 Engagement (value-chain parties)')
    # Build
    capability_delta = fields.Text(string='P7 New capabilities (target delta)')
    handover_service_id = fields.Many2one('synapsys.service', string='P7 Hands over to Service')
    project_ids = fields.One2many('project.project', 'synapsys_programme_id', string='P8 Projects')
    service_ids = fields.Many2many('synapsys.service', string='P9 Services engaged')
    # Realise
    benefit_realised_count = fields.Integer(compute='_compute_package', string='P10 Benefits at Verified')
    asset_ids = fields.Many2many('synapsys.asset', compute='_compute_package', string='P11 Assets strengthened')
    health = fields.Integer(compute='_compute_package', string='P12 Package completeness (of 12)')

    @api.depends('benefit_ids', 'benefit_ids.ppv', 'benefit_ids.chain_id', 'benefit_ids.link_ids')
    def _compute_package(self):
        for r in self:
            r.benefit_chain_codes = ', '.join(sorted(set(r.benefit_ids.mapped('chain_id.code'))))
            r.benefit_realised_count = len(r.benefit_ids.filtered(lambda b: b.ppv == 'verified'))
            r.asset_ids = r.benefit_ids.mapped('link_ids').filtered(lambda l: l.type == 'DIRECT').mapped('asset_id')
            slots = [r.benefit_ids, r.value_chain_id, r.context_id, r.analytic_account_ref, r.sponsor or r.owner_id,
                     r.partner_ids, r.capability_delta, r.project_ids, r.service_ids, r.benefit_realised_count,
                     r.asset_ids, True]
            r.health = sum(1 for s in slots if s)

    def _thread(self):
        return {'Purpose': self.strategy_id.purpose_id or self.context_id.purpose_id,
                'Strategy': self.strategy_id or self.portfolio_id.strategy_id,
                'Portfolio': self.portfolio_id, 'Programme': self}


class ProjectProject(models.Model):
    _inherit = 'project.project'
    synapsys_context_id = fields.Many2one('synapsys.context', string='SynapSys Context')
    synapsys_programme_id = fields.Many2one('synapsys.programme', string='Programme')
    synapsys_outcome_ids = fields.One2many('synapsys.outcome', 'project_id', string='Outcomes')


class ProjectMilestone(models.Model):
    _inherit = 'project.milestone'
    synapsys_outcome_id = fields.Many2one('synapsys.outcome', string='Outcome accepted at this milestone',
                                          help='Ledger L3: one optional acceptance milestone per Outcome.')


# ---------------------------------------------------------------- Outcome, Benefit, Asset, links

class SynapsysOutcome(models.Model):
    _name = 'synapsys.outcome'
    _description = 'Outcome (delivered by Projects)'
    _inherit = ['synapsys.cell']
    _gap_fields = ['project_id', 'baseline', 'domain_id']
    name = fields.Char(required=True)
    v19_model = fields.Char()
    definition = fields.Text()
    measure = fields.Char()
    method = fields.Text()
    target = fields.Text()
    acceptance_condition = fields.Text()
    baseline = fields.Text()
    baseline_observed = fields.Boolean(default=False)
    position = fields.Char()
    target_date = fields.Date()
    evidence_link = fields.Char()
    chain_id = fields.Many2one('synapsys.value.chain')
    stage = fields.Char()
    pattern_id = fields.Many2one('synapsys.pattern')
    note = fields.Text()
    observed_date = fields.Char()
    kind_proposed = fields.Char()
    lifecycle = fields.Char(help='Source lifecycle value, unchanged.')
    programme_id = fields.Many2one('synapsys.programme', help='Only where the source links it.')
    project_id = fields.Many2one('project.project')
    milestone_ids = fields.One2many('project.milestone', 'synapsys_outcome_id', string='Acceptance milestone')
    benefit_ids = fields.Many2many('synapsys.benefit', 'synapsys_outcome_benefit_rel', 'outcome_id', 'benefit_id')
    ppv = fields.Selection(PPV, string='PPV')
    observed = fields.Boolean(string='Observed by a human', default=False)

    def _thread(self):
        b = self.benefit_ids[:1]
        a = b.link_ids.filtered(lambda l: l.type == 'DIRECT')[:1].asset_id
        p = self.programme_id or b.programme_id
        return {'Programme': p, 'Project': self.project_id, 'Outcome': self, 'Benefit': b, 'Asset': a}


class SynapsysBenefit(models.Model):
    _name = 'synapsys.benefit'
    _description = 'Benefit (net change for a named beneficiary, tied to a value chain)'
    _inherit = ['synapsys.cell']
    _order = 'context_id, name'
    _gap_fields = ['chain_id', 'stage_id', 'measure', 'target', 'baseline', 'owner_id', 'beneficiary_id',
                   'acceptance_party_id', 'acceptance_condition']
    code = fields.Char()
    v19_code = fields.Char()
    name = fields.Char(required=True)
    long_name = fields.Text()
    active = fields.Boolean(default=True)
    moved_from = fields.Char()
    chain_id = fields.Many2one('synapsys.value.chain', string='Value chain')
    stage_id = fields.Many2one('synapsys.value.chain.stage', string='Stage', domain="[('chain_id', '=', chain_id)]")
    stage_source = fields.Char(string='Stage (source wording)')
    pattern_id = fields.Many2one('synapsys.pattern')
    value_category = fields.Char()
    value_category_basis = fields.Char()
    position = fields.Selection(PERSPECTIVE)
    kind_proposed = fields.Char()
    kind_basis = fields.Char()
    measure = fields.Char()
    unit = fields.Char()
    method = fields.Text()
    target = fields.Text()
    direction = fields.Char()
    baseline = fields.Text(string='Baseline (observed)')
    baseline_rule = fields.Char()
    baseline_v19 = fields.Text(string='Baseline text (v19)')
    acceptance_condition = fields.Text()
    beneficiary_id = fields.Many2one('res.partner')
    acceptance_party_id = fields.Many2one('res.partner')
    owner_id = fields.Many2one('res.users', string='Owner')
    owner_rule = fields.Char()
    contributors = fields.Text()
    realisation_evidence = fields.Text()
    status_note = fields.Text()
    lifecycle = fields.Char(help='v19 x_benefit_status, unchanged (expected, planned, superseded ...).')
    ppv = fields.Selection(PPV, string='PPV')
    ppv_v19 = fields.Char()
    programme_id = fields.Many2one('synapsys.programme', help='Only where v19 links it.')
    service_id = fields.Many2one('synapsys.service', string='Service (v19 Benefit side)')
    outcome_ids = fields.Many2many('synapsys.outcome', 'synapsys_outcome_benefit_rel', 'benefit_id', 'outcome_id')
    outcome_count = fields.Integer(compute='_compute_outcome_count', store=True)
    outcome_flag = fields.Boolean(compute='_compute_outcome_count', store=True,
                                  string='Fewer than 3 Outcomes (candidate rule, flag only)')
    link_ids = fields.One2many('synapsys.oba.link', 'benefit_id', string='Links to Assets')

    @api.depends('outcome_ids')
    def _compute_outcome_count(self):
        for r in self:
            r.outcome_count = len(r.outcome_ids)
            r.outcome_flag = r.outcome_count < 3

    def _thread(self):
        o = self.outcome_ids[:1]
        p = self.programme_id or o.programme_id
        a = self.link_ids.filtered(lambda l: l.type == 'DIRECT')[:1].asset_id
        return {'Strategy': p.strategy_id, 'Portfolio': p.portfolio_id, 'Programme': p,
                'Project': o.project_id, 'Outcome': o, 'Benefit': self, 'Asset': a}


class SynapsysAsset(models.Model):
    _name = 'synapsys.asset'
    _description = 'Asset (>=3 qualified Benefits plus rights)'
    _inherit = ['synapsys.cell']
    _order = 'context_id, name'
    _gap_fields = ['chain_id', 'asset_class', 'rights_holder_id', 'rights_basis', 'portfolio_id']
    key = fields.Char()
    v19_code = fields.Char()
    name = fields.Char(required=True)
    label_short = fields.Char()
    description = fields.Text()
    note = fields.Text()
    source = fields.Text()
    new_record = fields.Boolean()
    chain_id = fields.Many2one('synapsys.value.chain')
    asset_class = fields.Char(string='Class')
    class_basis = fields.Text()
    class_status = fields.Char()
    class_target = fields.Char()
    reclass_when = fields.Text()
    composition = fields.Char()
    parent_id = fields.Many2one('synapsys.asset', string='Parent Asset')
    child_ids = fields.One2many('synapsys.asset', 'parent_id', string='Components')
    components_proposed = fields.Text()
    portfolio_id = fields.Many2one('synapsys.portfolio')
    rights_holder_id = fields.Many2one('res.partner', string='Rights holder')
    rights_basis = fields.Text()
    rights_required = fields.Boolean()
    rights_split_required = fields.Boolean()
    rights_confirmed = fields.Boolean(default=False, help='Steward only.')
    counts_require = fields.Text(string='Qualification rule (source)')
    kind_proposed = fields.Char()
    kind_basis = fields.Char()
    lifecycle = fields.Char(help='v19 x_asset_status, unchanged.')
    acceptance_criteria = fields.Text()
    retained_value = fields.Text()
    reuse_pathway = fields.Text()
    risk_assumptions = fields.Text()
    service_id = fields.Many2one('synapsys.service', string='Service (v19)')
    method_id = fields.Many2one('synapsys.method', string='Method (v19)')
    ppv = fields.Selection(PPV, string='PPV')
    ppv_v19 = fields.Char()
    link_ids = fields.One2many('synapsys.oba.link', 'asset_id', string='Benefit links')
    benefit_count = fields.Integer(compute='_compute_qualification', store=True, string='Direct Benefit links')
    qualified_benefit_count = fields.Integer(compute='_compute_qualification', store=True, string='Qualifying links')
    qualifies = fields.Boolean(compute='_compute_qualification', store=True,
                               help='>=3 distinct same-chain DIRECT links with link and Benefit PPV >= Probable, '
                                    'rights holder and basis, no rights still required, not a component.')

    @api.depends('link_ids', 'link_ids.ppv', 'link_ids.type', 'link_ids.benefit_id.ppv', 'chain_id',
                 'rights_holder_id', 'rights_basis', 'rights_required', 'rights_split_required', 'parent_id')
    def _compute_qualification(self):
        for r in self:
            direct = r.link_ids.filtered(lambda l: l.type == 'DIRECT')
            r.benefit_count = len(direct.mapped('benefit_id'))
            q = direct.filtered(lambda l: l.chain_id == r.chain_id and PPV_RANK[l.ppv] >= 2
                                and PPV_RANK[l.benefit_id.ppv] >= 2).mapped('benefit_id')
            r.qualified_benefit_count = len(q)
            r.qualifies = bool(len(q) >= 3 and r.rights_holder_id and r.rights_basis and not r.rights_required
                               and not r.rights_split_required and not r.parent_id)

    def _thread(self):
        b = self.link_ids.filtered(lambda l: l.type == 'DIRECT')[:1].benefit_id
        return {'Portfolio': self.portfolio_id, 'Programme': b.programme_id, 'Outcome': b.outcome_ids[:1],
                'Benefit': b, 'Asset': self}


class SynapsysObaLink(models.Model):
    _name = 'synapsys.oba.link'
    _inherit = ['synapsys.guard']
    _protected = {'ppv', 'type'}
    _description = 'Benefit to Asset link (DIRECT counts; INFLUENCES is a signal only)'
    benefit_id = fields.Many2one('synapsys.benefit', required=True, ondelete='cascade')
    asset_id = fields.Many2one('synapsys.asset', required=True, ondelete='cascade')
    type = fields.Selection([('DIRECT', 'Direct'), ('INFLUENCES', 'Influences (signal, never counted)')],
                            required=True)
    chain_id = fields.Many2one('synapsys.value.chain')
    stage = fields.Char()
    kinematic_mapping = fields.Char(string='Verb')
    ppv = fields.Selection(PPV, string='Link PPV')
    owner_side = fields.Char()
    reason = fields.Text()
    ruling = fields.Char()


class SynapsysValuation(models.Model):
    _name = 'synapsys.valuation'
    _description = 'Asset valuation or attribution rule (reclassified from a v19 Benefit)'
    kind = fields.Selection([('valuation', 'Valuation'), ('attribution', 'Attribution rule')], required=True)
    name = fields.Char(required=True)
    long_name = fields.Text()
    context_id = fields.Many2one('synapsys.context')
    chain_id = fields.Many2one('synapsys.value.chain')
    stage = fields.Char()
    asset_id = fields.Many2one('synapsys.asset')
    applies_to_benefit_id = fields.Many2one('synapsys.benefit')
    approach = fields.Text()
    basis = fields.Text()
    standard = fields.Char()
    state = fields.Char()
    valuer = fields.Char()
    method = fields.Text()
    target = fields.Text()
    note = fields.Text()
    ppv = fields.Selection(PPV, string='PPV')
    v19_id = fields.Integer()


# ---------------------------------------------------------------- Services (15-slot package)

class SynapsysServiceStandard(models.Model):
    _name = 'synapsys.service.standard'
    _description = 'Service Standard (shared contract paragraphs, held once and inherited)'
    name = fields.Char(required=True)
    paragraphs = fields.Text(help='JSON list of shared paragraphs; Services reference them by index.')
    paragraph_count = fields.Integer(compute='_compute_paragraph_count')

    def _compute_paragraph_count(self):
        for r in self:
            r.paragraph_count = len(json.loads(r.paragraphs or '[]'))


CONTRACT = ['description', 'client_outcome', 'adaptability_envelope', 'ffe_participation_contract',
            'authority_gate_schema', 'execution_input_contract', 'execution_outcome_schema',
            'return_acceptance_schema', 'observation_learning_contract']


class SynapsysService(models.Model):
    """15-slot Service package (ruled 15 Nov 22:13). Common capability inherited from the Service Standard;
    each Service stores only its own text (override) and which standard paragraphs it carries."""
    _name = 'synapsys.service'
    _description = 'Service (operates existing capability, delivers Benefits)'
    _inherit = ['synapsys.cell']
    _order = 'code'
    _gap_fields = ['kind_proposed', 'perspective', 'owner_name', 'delivery_lead', 'entry_point', 'input_class',
                   'approval_category', 'sla_value', 'rhythm_tier', 'obligations']
    code = fields.Char(required=True)
    name = fields.Char(required=True)
    lifecycle = fields.Char(help='One status (v19 x_service_status), unchanged.')
    validation_status_v19 = fields.Char(string='v19 validation label (history)')
    ffe_state_v19 = fields.Char(string='v19 FFE state (single value, history)')
    standard_id = fields.Many2one('synapsys.service.standard')
    standard_refs = fields.Text(help='JSON: contract field -> list of Standard paragraph indexes it carries.')
    source_hash = fields.Text(help='JSON: contract field -> sha256 of the v19 text.')
    # 1 Identity
    verb_id = fields.Many2one('synapsys.verb', string='Primary verb')
    verb_source = fields.Char(string='Verb as written in source')
    shape = fields.Selection(SHAPES, string='Kinematic shape (instance)',
                             help='Shape of the capability this Service operates. Separate from the Context kind; empty = GAP.')
    shape_version = fields.Integer(string='Shape version')
    # 2 Context and kind
    kind_proposed = fields.Char(string='2 Kind (proposed)')
    # 3 Perspective
    perspective = fields.Selection(PERSPECTIVE, string='3 Perspective')
    # 4 Canon
    method_id = fields.Many2one('synapsys.method', string='4 Method anchor')
    canon_ids = fields.Many2many('synapsys.canon', string='4 Canon links')
    pattern_ids = fields.Many2many('synapsys.pattern', 'synapsys_service_pattern_rel', 'service_id', 'pattern_id',
                                   string='4 Patterns (source)', readonly=True, help='V19 source link, written only by the released source load.')
    prerequisite_ids = fields.Many2many('synapsys.service', 'synapsys_service_prereq_rel', 'service_id',
                                        'prerequisite_id', string='Prerequisite Services (source)', readonly=True, help='V19 source link, written only by the released source load.')
    requires_ids = fields.Many2many('synapsys.service', 'synapsys_service_requires_rel', 'service_id',
                                    'required_id', string='Required Services (source)', readonly=True, help='V19 source link, written only by the released source load.')
    pattern_codes = fields.Char(string='4 Patterns (v19 ids)')
    # 5 Owner
    owner_name = fields.Char(string='5 Owner (v19)')
    delivery_lead = fields.Char(string='5 Delivery lead')
    escalation = fields.Char(string='5 Escalation')
    # 6 Door
    entry_point = fields.Char(string='6 Entry point (Door)')
    input_class = fields.Char(string='6 Input class')
    # 7 Gate
    approval_category = fields.Char(string='7 Approval profile')
    # 8 Work (computed)
    programme_ids = fields.Many2many('synapsys.programme', compute='_compute_work', string='8 Programmes')
    project_count = fields.Integer(compute='_compute_work', string='8 Projects')
    # 10 Service level
    sla_text = fields.Text(string='10 Service level (v19 text)')
    sla_value = fields.Float(string='10 SLA value')
    sla_unit = fields.Char(string='10 SLA unit')
    rhythm_tier = fields.Char(string='10 Rhythm tier')
    # 11 Benefits, 12 Assets
    benefit_ids = fields.One2many('synapsys.benefit', 'service_id', string='11 Benefits')
    benefit_v19_service_side = fields.Char(string='11 Benefits listed on v19 Service side (ids)')
    asset_ids = fields.One2many('synapsys.asset', 'service_id', string='12 Assets')
    # 13 Learning, 14 Obligations
    obligations = fields.Text(string='14 Obligations and gates passed')
    requires_v19 = fields.Char(string='Requires (v19 edge ids)')
    # 15 Health
    slots_filled = fields.Integer(compute='_compute_health', string='15 Slots filled (of 15)')
    plug_in_ready = fields.Boolean(compute='_compute_health', string='15 Plug-in ready')
    # contract text: own override per field + inherited full text
    description = fields.Text(string='1 Description (own)')
    client_outcome = fields.Text(string='9 Client outcome (own)')
    adaptability_envelope = fields.Text(string='Adaptability envelope (own)')
    ffe_participation_contract = fields.Text(string='FFE participation (own)')
    authority_gate_schema = fields.Text(string='7 Gate schema (own)')
    execution_input_contract = fields.Text(string='6 Input contract (own)')
    execution_outcome_schema = fields.Text(string='9 Outcome schema (own)')
    return_acceptance_schema = fields.Text(string='9 Acceptance (own)')
    observation_learning_contract = fields.Text(string='13 Learning contract (own)')
    inherited_html = fields.Html(compute='_compute_inherited', sanitize=True, string='Inherited from the Standard')

    @api.depends('code', 'name')
    def _compute_display_name(self):
        for r in self:
            r.display_name = '%s %s' % (r.code or '', r.name or '')

    def _compute_work(self):
        P = self.env['synapsys.programme']
        for r in self:
            progs = P.search([('service_ids', 'in', r.id)]) if r.id else P
            r.programme_ids = progs
            r.project_count = len(progs.mapped('project_ids'))

    def _compute_inherited(self):
        for r in self:
            paras = json.loads(r.standard_id.paragraphs or '[]') if r.standard_id else []
            refs = json.loads(r.standard_refs or '{}')
            out = []
            for f in CONTRACT:
                idx = refs.get(f) or []
                if idx:
                    out.append(Markup('<p><b>%s</b>: %d shared paragraph(s)</p>') % (r._fields[f].string, len(idx)))
                    for i in idx:
                        if i < len(paras):
                            out.append(Markup('<blockquote class="small text-muted">%s</blockquote>') % paras[i])
            r.inherited_html = Markup('').join(out) if out else False

    @api.depends('context_id', 'kind_proposed', 'perspective', 'method_id', 'canon_ids', 'owner_name',
                 'entry_point', 'approval_category', 'execution_outcome_schema', 'return_acceptance_schema',
                 'sla_value', 'benefit_ids',
                 'asset_ids', 'observation_learning_contract', 'obligations', 'name')
    def _compute_health(self):
        for r in self:
            slots = [r.name, r.context_id and r.kind_proposed, r.perspective, r.method_id or r.canon_ids,
                     r.owner_name, r.entry_point, r.approval_category, True,
                     r.execution_outcome_schema or r.return_acceptance_schema, r.sla_value, r.benefit_ids,
                     r.asset_ids, r.observation_learning_contract, r.obligations, True]
            r.slots_filled = sum(1 for s in slots if s)
            r.plug_in_ready = r.slots_filled == 15


# ---------------------------------------------------------------- evidence, inbox, events

class SynapsysFractal(models.Model):
    _name = 'synapsys.fractal'
    _description = 'Fractal Record (Signal -> CIA -> L5)'
    _order = 'id desc'
    code = fields.Char()
    name = fields.Char(required=True)
    v19_id = fields.Integer()
    context_id = fields.Many2one('synapsys.context')
    strategy_id = fields.Many2one('synapsys.strategy', string='Strategy (source)', readonly=True, help='V19 source link, written only by the released source load.')
    purpose_id = fields.Many2one('synapsys.purpose', string='Purpose (source)', readonly=True, help='V19 source link, written only by the released source load.')
    res_model = fields.Char(string='Subject model', index=True)
    res_id = fields.Integer(string='Subject id', index=True)
    ffe_position = fields.Selection(FFE, required=True, string='FFE position')
    signal = fields.Text(string='Signal (observed / empirical / perturbation)')
    canonical = fields.Text(string='Canonical attribute')
    intelligence = fields.Text(string='Intelligence attribute')
    adaptability = fields.Text(string='Adaptability attribute')
    expression = fields.Text(string='L5 Expression')
    measurement = fields.Text(string='L5 Measurement')
    realisation = fields.Selection([('unobserved', 'Unobserved'), ('outcome', 'Observed Outcome'),
                                    ('benefit', 'Accepted net Benefit'), ('asset', 'Qualified Asset')],
                                   default='unobserved', string='L5 Realisation')
    evidence = fields.Text()
    evidence_state = fields.Char()
    admission = fields.Char()
    gate_level = fields.Char()
    notes = fields.Text()
    edge = fields.Selection([('SUPPORTS', 'Supports'), ('CHALLENGES', 'Challenges'),
                             ('NON_DISCRIMINATING', 'Non-discriminating'), ('DEPENDS_ON', 'Depends on')])
    parent_id = fields.Many2one('synapsys.fractal', string='Parent evidence')
    benefit_link_ids = fields.One2many('synapsys.fractal.benefit', 'fractal_id')


class SynapsysFractalBenefit(models.Model):
    _name = 'synapsys.fractal.benefit'
    _description = 'Fractal to Benefit link (carried live with targets, X3/S5)'
    name = fields.Char()
    v19_id = fields.Integer()
    fractal_id = fields.Many2one('synapsys.fractal', required=True, ondelete='cascade')
    benefit_id = fields.Many2one('synapsys.benefit', required=True, ondelete='cascade')
    syntropic_domain = fields.Char()
    effect_pattern_id = fields.Many2one('synapsys.pattern')
    contribution_role = fields.Char()
    effect_direction = fields.Char()
    baseline = fields.Float()


class SynapsysSignal(models.Model):
    _name = 'synapsys.signal'
    _description = 'Inbox signal'
    _inherit = ['synapsys.cell', 'mail.thread']
    _order = 'id desc'
    name = fields.Char(required=True)
    source = fields.Char()
    state = fields.Selection([('new', 'New'), ('routed', 'Routed'), ('closed', 'Closed')], default='new')


class SynapsysPtwEvent(models.Model):
    _name = 'synapsys.ptw.event'
    _description = 'Playing to Win Event'
    _inherit = ['synapsys.cell']
    _order = 'date desc'
    name = fields.Char(required=True)
    date = fields.Date()
    strategy_id = fields.Many2one('synapsys.strategy')
    description = fields.Text()


class MeshEntryDomain(models.Model):
    """One domain list (Steward 20 Nov 11:14): a registry domain element points at the Architecture domain."""
    _inherit = 'synapsys.mesh.entry'
    domain_id = fields.Many2one('synapsys.domain', compute='_compute_domain_id', string='Architecture domain')

    def _compute_domain_id(self):
        doms = {d.name: d for d in self.env['synapsys.domain'].search([])}
        for r in self:
            r.domain_id = doms.get(r.label) if r.cls == 'D' else False
