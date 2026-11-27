"""Service Catalogue adoption loader: V19 x_service_catalogue extract -> V20 synapsys.service through the 15-slot map (RC07, source-only candidate).

Why a standalone script and not an addon tool: it must never run on module upgrade, must not change the addon tree installed on dev, and must be reviewable and
removable on its own. It lives outside addon/synapsys and is run, by hand, from `odoo-bin shell` AFTER a backup and a reviewed dry-run:

    # inside `odoo-bin shell -d <db> --no-http`   (nothing below runs on upgrade; the caller commits)
    import sys; sys.path.insert(0, '<path>/loader'); import service_catalogue_load as L
    L.run(env, extract='<path>/V19_SERVICE_CATALOGUE_EXTRACT_20261127.json')            # DRY-RUN: prints the diff, writes nothing
    L.run(env, extract='...', apply=True); env.cr.commit()                              # only after the diff is reviewed
    L.rollback(env, apply=True); env.cr.commit()                                        # removes only rows and the Standard this loader created

Offline plan without a database (relations are NOT checked): python3 service_catalogue_load.py --extract FILE --no-lookup [--report OUT.json]

Rules (contract BUILD_CONTRACT_SERVICE_CATALOGUE_ADOPTION_V19_TO_V20_20261127_v1): dry-run by default; idempotent on the key v19_id (a second apply changes 0 rows);
nothing is guessed (an unresolved relation is left empty and reported; an undecided name is HELD); perspective stays empty; PPV, Benefit and Asset state are never
written; no field is added to any model; V19 is never contacted: this module has no V19 connection and writes only synapsys.service, synapsys.service.standard and the
external ids that mark what it created.
"""
import argparse
import collections
import hashlib
import json
import re
import sys

EXTRACT_SHA256 = '87bdc258f65dc57175cbed5f6fdeebce6658a3868e495dd2dec7b107aa58f887'
EXTRACT_SCHEMA = 'synapsys.source.v19.x_service_catalogue.extract/1'
XML_MODULE = '__synapsys_v19_load__'  # Odoo's own import convention ('__import__'): a pseudo-module that module upgrade never cleans up
XML_SERVICE = 'service_v19_%d'
XML_STANDARD = 'service_standard_v19'
STANDARD_NAME = 'Service Standard (V19 catalogue load)'
SHARED_MIN = 10  # the most common text of a standard field becomes a shared paragraph when at least this many rows carry exactly it (contract: 15 / 30 / 15 / 29)

# R4 (PROPOSED, pending the Steward ruling S3 on merging the four status fields)
LIFECYCLE_MAP = {'active': 'active', 'draft': 'draft', 'future_scoped': 'candidate', 'deprecated': 'retired'}
LIFECYCLE_PROPOSED = True

# synapsys.service text fields that can carry a shared (Standard) paragraph, in paragraph order; the last one has no field on synapsys.service
STANDARD_FIELDS = (('x_authority_gate_schema', 'authority_gate_schema'), ('x_adaptability_envelope', 'adaptability_envelope'),
                   ('x_observation_learning_contract', 'observation_learning_contract'), ('x_provider_fallback_policy', 'provider_fallback_policy'))
OWN_TEXT = (('x_description', 'description'), ('x_client_outcome', 'client_outcome'), ('x_ffe_participation_contract', 'ffe_participation_contract'),
            ('x_execution_input_contract', 'execution_input_contract'), ('x_execution_outcome_schema', 'execution_outcome_schema'),
            ('x_return_acceptance_schema', 'return_acceptance_schema'))
NO_TARGET_FIELD = {'provider_fallback_policy'}  # shared text is carried by the Standard; a row whose text differs has no field to keep it in (held, in the extract)

# Section 3 (mapped) and Section 4 (unmapped) of the contract; together they must equal the 85 extract fields
MAPPED = ('id', 'x_service_code', 'x_service_name', 'x_name', 'x_description', 'x_service_status', 'x_lifecycle_gate', 'x_validation_status', 'x_validation_timestamp', 'x_active',
          'x_ffe_state', 'x_context_id', 'x_service_class', 'x_offering_layer', 'x_service_role', 'x_method_role', 'x_platform_role', 'x_membrane_role', 'x_method_id',
          'x_canonical_library_ids', 'x_pattern_ids', 'x_primary_governing_domain', 'x_service_owner_id', 'x_delivery_lead_id', 'x_escalation_group_id', 'x_steward_contact_id',
          'x_entry_point', 'x_input_class', 'x_execution_input_contract', 'x_authority_gate_schema', 'x_authority_reference', 'x_service_activation_requires_decision',
          'x_execution_outcome_schema', 'x_return_acceptance_schema', 'x_client_outcome', 'x_sla_metric', 'x_sla_metric_text', 'x_sla_metric_unit', 'x_sla_metric_value',
          'x_sla_measurement_type', 'x_observation_learning_contract', 'x_itil_csi_log', 'x_adaptability_envelope', 'x_provider_fallback_policy', 'x_ffe_participation_contract')
UNMAPPED_GROUPS = collections.OrderedDict([
    ('Authority/proof states (PPV)', ('x_service_ppv_entry', 'x_service_ppv_ceiling', 'x_productisation_status', 'x_processability_state', 'x_fpv_acceptance')),
    ('ITIL description set', ('x_itil_service_description', 'x_itil_utility', 'x_itil_warranty', 'x_itil_service_level_target', 'x_itil_support_model', 'x_itil_service_owner_role',
                              'x_warranty_commitment_type', 'x_warranty_commitment_text')),
    ('Execution and capability requirements', ('x_ai_capability_requirements', 'x_human_role_requirements', 'x_deterministic_tech_requirements', 'x_operator_trace',
                                                'x_operations_pattern', 'x_default_workflow_phase', 'x_named_consumer', 'x_gsa_role', 'x_cost_risk_transfer', 'x_fallback_flag')),
    ('Collaborator and client access', ('x_collab_ai_access_mode', 'x_collab_ai_allowed_intents', 'x_collab_ai_scope', 'x_client_contact_visible', 'x_channel_ids')),
    ('Context binding and summary', ('x_context_binding_required', 'x_context_binding_notes', 'x_haion_summary')),
    ('Provenance and links', ('x_source_document', 'x_source_version', 'x_dim_trigger_linkage', 'x_producible_lens_ids', 'x_prerequisite_edge_ids', 'x_requires_edge_ids')),
    ('System', ('x_company_id', 'create_date', 'write_date')),
])
UNMAPPED = tuple(f for g in UNMAPPED_GROUPS.values() for f in g)
# fields written to NO live field even though the contract maps them (reported separately from the 40 unmapped)
PERSPECTIVE_SOURCES = ('x_service_class', 'x_offering_layer', 'x_service_role', 'x_method_role', 'x_platform_role', 'x_membrane_role')  # R5: perspective stays EMPTY
PROTECTED_NEVER_WRITTEN = ('perspective', 'ppv', 'kind', 'kind_proposed', 'shape', 'verb_id', 'answer', 'answer_accepted', 'rhythm_tier', 'obligations')
MANAGED = ('v19_id', 'code', 'name', 'description', 'lifecycle', 'validation_status_v19', 'ffe_state_v19', 'context_id', 'domain_id', 'method_id', 'canon_ids', 'pattern_ids',
           'pattern_codes', 'owner_name', 'delivery_lead', 'escalation', 'entry_point', 'input_class', 'approval_category', 'sla_text', 'sla_value', 'sla_unit', 'client_outcome',
           'adaptability_envelope', 'ffe_participation_contract', 'authority_gate_schema', 'execution_input_contract', 'execution_outcome_schema', 'return_acceptance_schema',
           'observation_learning_contract', 'standard_id', 'standard_refs', 'source_hash')
RELATION_FIELDS = ('context_id', 'domain_id', 'method_id', 'canon_ids', 'pattern_ids')
M2M = ('canon_ids', 'pattern_ids')
AMBIGUOUS = 'AMBIGUOUS'


# ----------------------------------------------------------------------------------------------------------------------- source
def sha256_file(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()


def load_extract(path, expected_sha=EXTRACT_SHA256):
    """Reads the extract after checking its hash; the extract stays the lossless source and is never modified."""
    got = sha256_file(path)
    if expected_sha and got != expected_sha:
        raise ValueError('extract sha256 %s != expected %s' % (got, expected_sha))
    doc = json.load(open(path, encoding='utf-8'))
    if doc.get('schema') != EXTRACT_SCHEMA:
        raise ValueError('unknown extract schema %r' % (doc.get('schema'),))
    rows = doc['rows']
    ids = [r['id'] for r in rows]
    if len(set(ids)) != len(ids):
        raise ValueError('duplicate v19 id in the extract')
    codes = [r['x_service_code'] for r in rows]
    if len(set(codes)) != len(codes):
        raise ValueError('a V19 service code appears more than once')
    return doc, got


def empty(v):
    return v is False or v is None or v == '' or v == [] or v == 0.0


def txt(v):
    return None if empty(v) or not isinstance(v, str) else v


def rel_id_name(v):
    return (v[0], v[1]) if isinstance(v, list) and len(v) == 2 else None


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def _strip_code(name, code):
    n = (name or '').strip()
    m = re.match(r'^' + re.escape(code) + r'\s*[-–—:]*\s*', n)
    return n[m.end():].strip() if m else n


def _norm(s):
    return re.sub(r'\s+', ' ', (s or '').strip()).casefold()


def name_check(row):
    """R8: x_name (the 'CODE name' display composite in V19) versus x_service_name. Equal after removing a leading code and dash from both; otherwise HOLD."""
    code, a, b = row['x_service_code'], row.get('x_name') or '', row.get('x_service_name') or ''
    same = _norm(_strip_code(a, code)) == _norm(_strip_code(b, code)) and bool(_strip_code(b, code))
    return {'equal': same, 'name': _strip_code(b, code), 'code_prefix_stripped': same and _strip_code(b, code) != b.strip(), 'x_name': a, 'x_service_name': b}


# ----------------------------------------------------------------------------------------------------------------------- plan
class NoLookup(object):
    """Offline planning: relations are not looked up (nothing is claimed resolved)."""
    offline = True

    def resolve(self, kind, v19_id=None, code=None):
        return None


def shared_texts(rows, min_rows=SHARED_MIN):
    """Per standard field: the most common exact text, when at least `min_rows` rows carry it. Returns {src_field: text} and counts."""
    out, counts = collections.OrderedDict(), {}
    for src, _dst in STANDARD_FIELDS:
        c = collections.Counter(r[src] for r in rows if txt(r.get(src)))
        if not c:
            continue
        top, n = c.most_common(1)[0]
        counts[src] = {'filled': sum(c.values()), 'distinct': len(c), 'top_count': n, 'second_count': (c.most_common(2)[1][1] if len(c) > 1 else 0)}
        if n >= min_rows:
            out[src] = top
    return out, counts


def lifecycle_of(row):
    s = row.get('x_service_status')
    lc = LIFECYCLE_MAP.get(s)
    if lc is None:
        return None
    if row.get('x_active') is False and lc != 'retired':
        lc = 'retired'  # an archived row is retired whatever its status word (none occur in the 27 Nov extract)
    return lc


def history_label(row):
    """R4: the original V19 status and validation values kept as one history label (not a live field)."""
    bits = []
    for k, v in (('status', row.get('x_service_status')), ('gate', row.get('x_lifecycle_gate')), ('validation', row.get('x_validation_status')), ('validated_at', row.get('x_validation_timestamp'))):
        if not empty(v):
            bits.append('%s=%s' % (k, v))
    if row.get('x_active') is not None:
        bits.append('active=%s' % ('true' if row['x_active'] else 'false'))
    return '; '.join(bits) or None


def plan_row(row, lookup, standard_texts, name_rulings, std_index):
    """One row: desired live values, links to the Standard, unresolved relations, held items."""
    vals, unresolved, holds, notes = {}, [], [], []
    vals['v19_id'] = row['id']
    vals['code'] = row['x_service_code']
    nc = name_check(row)
    name = None
    if str(row['id']) in name_rulings:
        name = name_rulings[str(row['id'])]
        notes.append('name ruled by the Steward file')
    elif nc['equal']:
        name = nc['name']
        if nc['code_prefix_stripped']:
            notes.append('leading code removed from x_service_name')
    else:
        holds.append({'item': 'name', 'reason': 'x_name and x_service_name differ', 'x_name': nc['x_name'], 'x_service_name': nc['x_service_name']})
    vals['name'] = name
    vals['description'] = txt(row.get('x_description'))
    vals['lifecycle'] = lifecycle_of(row)
    vals['validation_status_v19'] = history_label(row)
    vals['ffe_state_v19'] = txt(row.get('x_ffe_state'))
    # relations: resolve, never guess, never create a stub parent
    ctx = rel_id_name(row.get('x_context_id'))
    vals['context_id'] = None
    if ctx:
        r = lookup.resolve('context', v19_id=ctx[0], code=ctx[1])
        if r in (None, AMBIGUOUS):
            if not getattr(lookup, 'offline', False):
                unresolved.append({'field': 'context_id', 'v19': ctx[0], 'ref': ctx[1], 'why': 'ambiguous' if r == AMBIGUOUS else 'not found'})
        else:
            vals['context_id'] = r
    dom = txt(row.get('x_primary_governing_domain'))
    vals['domain_id'] = None
    if dom:
        r = lookup.resolve('domain', code=dom)
        if r in (None, AMBIGUOUS):
            if not getattr(lookup, 'offline', False):
                unresolved.append({'field': 'domain_id', 'v19': None, 'ref': dom, 'why': 'ambiguous' if r == AMBIGUOUS else 'not found'})
        else:
            vals['domain_id'] = r
    me = rel_id_name(row.get('x_method_id'))
    vals['method_id'] = None
    if me:
        r = lookup.resolve('method', v19_id=me[0])
        if r in (None, AMBIGUOUS):
            if not getattr(lookup, 'offline', False):
                unresolved.append({'field': 'method_id', 'v19': me[0], 'ref': me[1], 'why': 'ambiguous' if r == AMBIGUOUS else 'not found'})
        else:
            vals['method_id'] = r
    for fld, src, kind in (('canon_ids', 'x_canonical_library_ids', 'canon'), ('pattern_ids', 'x_pattern_ids', 'pattern')):
        got = []
        for vid in row.get(src) or []:
            r = lookup.resolve(kind, v19_id=vid)
            if r in (None, AMBIGUOUS):
                if not getattr(lookup, 'offline', False):
                    unresolved.append({'field': fld, 'v19': vid, 'ref': vid, 'why': 'ambiguous' if r == AMBIGUOUS else 'not found'})
            else:
                got.append(r)
        vals[fld] = sorted(set(got))
    vals['pattern_codes'] = ','.join(str(x) for x in (row.get('x_pattern_ids') or [])) or None  # the V19 ids as written in the source (field is labelled 'v19 ids')
    # slot 5 owner: char (users are not migrated)
    o, e, dl = rel_id_name(row.get('x_service_owner_id')), rel_id_name(row.get('x_escalation_group_id')), rel_id_name(row.get('x_delivery_lead_id'))
    vals['owner_name'] = o[1] if o else None
    vals['escalation'] = e[1] if e else None
    vals['delivery_lead'] = dl[1] if dl else None
    vals['entry_point'] = txt(row.get('x_entry_point'))
    vals['input_class'] = txt(row.get('x_input_class'))
    ref, flag = txt(row.get('x_authority_reference')), row.get('x_service_activation_requires_decision') is True
    vals['approval_category'] = ((ref or '') + (' | activation_requires_decision' if flag else '')).strip(' |') or None
    st = txt(row.get('x_sla_metric_text')) or txt(row.get('x_sla_metric'))
    mt = txt(row.get('x_sla_measurement_type'))
    vals['sla_text'] = ((st or '') + (' [measurement: %s]' % mt if mt else '')).strip() or None
    vals['sla_unit'] = txt(row.get('x_sla_metric_unit'))
    v = row.get('x_sla_metric_value')
    vals['sla_value'] = float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) and v != 0 else None
    # contract text: own override, or linked to the shared paragraph with no own copy
    refs, hashes = {}, {}
    for src, dst in OWN_TEXT:
        t = txt(row.get(src))
        vals[dst] = t
        if t:
            hashes[dst] = digest(t)
    for src, dst in STANDARD_FIELDS:
        t = txt(row.get(src))
        if t:
            hashes[dst] = digest(t)
        shared = standard_texts.get(src)
        if t and shared is not None and t == shared:
            refs[dst] = [std_index[src]]
            if dst not in NO_TARGET_FIELD:
                vals[dst] = None
        elif t:
            if dst in NO_TARGET_FIELD:
                holds.append({'item': dst, 'reason': 'text differs from the shared paragraph and synapsys.service has no field for it (kept in the extract)'})
            else:
                vals[dst] = t
        elif dst not in NO_TARGET_FIELD:
            vals[dst] = None
    vals['standard_refs'] = json.dumps(refs, sort_keys=True) if refs else None
    vals['source_hash'] = json.dumps(hashes, sort_keys=True) if hashes else None
    vals['_has_standard'] = bool(refs)
    return {'v19_id': row['id'], 'code': row['x_service_code'], 'values': vals, 'unresolved': unresolved, 'holds': holds, 'notes': notes, 'archived': row.get('x_active') is False}


def build_plan(doc, lookup, name_rulings=None, min_shared=SHARED_MIN):
    rows = doc['rows']
    name_rulings = name_rulings or {}
    standard_texts, std_counts = shared_texts(rows, min_shared)
    std_index = {src: i for i, src in enumerate(standard_texts)}
    paragraphs = [standard_texts[src] for src in standard_texts]
    planned = [plan_row(r, lookup, standard_texts, name_rulings, std_index) for r in rows]
    report = build_report(doc, rows, planned, standard_texts, std_counts, std_index)
    return {'rows': planned, 'standard': {'name': STANDARD_NAME, 'paragraphs': paragraphs, 'fields': list(standard_texts)}, 'report': report}


def build_report(doc, rows, planned, standard_texts, std_counts, std_index):
    mapped, unmapped = set(MAPPED), set(UNMAPPED)
    allf = set(rows[0].keys())
    cov = {'extract_fields': len(allf), 'mapped': len(mapped), 'unmapped': len(unmapped), 'overlap': sorted(mapped & unmapped), 'neither': sorted(allf - mapped - unmapped), 'absent_from_extract': sorted((mapped | unmapped) - allf)}
    filled = lambda f: sum(1 for r in rows if not empty(r.get(f)))
    lc = collections.Counter(p['values']['lifecycle'] for p in planned)
    rep = {
        'extract': {'rows': len(rows), 'live': sum(1 for r in rows if r.get('x_active') is True), 'archived': sum(1 for r in rows if r.get('x_active') is False), 'fields': len(allf), 'read_at': doc.get('read_at')},
        'coverage': cov,
        'unmapped_fields': [{'group': g, 'field': f, 'filled': filled(f)} for g, fs in UNMAPPED_GROUPS.items() for f in fs],
        'held_mapped': [
            {'field': 'x_lifecycle_gate', 'filled': filled('x_lifecycle_gate'), 'treatment': 'history only, inside validation_status_v19'},
            {'field': 'x_steward_contact_id', 'filled': filled('x_steward_contact_id'), 'treatment': 'not written: target (owner_name or escalation) is ambiguous; equals the owner on every row that has both (checked)',
             'owner_empty_and_contact_present': sum(1 for r in rows if empty(r.get('x_service_owner_id')) and not empty(r.get('x_steward_contact_id'))),
             'differs_from_owner': sum(1 for r in rows if not empty(r.get('x_service_owner_id')) and not empty(r.get('x_steward_contact_id')) and r['x_service_owner_id'] != r['x_steward_contact_id'])},
            {'field': 'x_itil_csi_log', 'filled': filled('x_itil_csi_log'), 'treatment': 'HOLD: needs a Service link on learning records (ruling S2)'},
        ] + [{'field': f, 'filled': filled(f), 'treatment': 'HELD (R5): perspective is not ruled and stays empty; source values counted below'} for f in PERSPECTIVE_SOURCES],
        'perspective_source_counts': {f: dict(collections.Counter(('(distinct text)' if f == 'x_membrane_role' and not empty(r.get(f)) else (r.get(f) if not empty(r.get(f)) else '(empty)')) for r in rows)) for f in PERSPECTIVE_SOURCES},
        'lifecycle_counts': {'proposed': LIFECYCLE_PROPOSED, 'counts': dict(lc), 'source_status_counts': dict(collections.Counter(r.get('x_service_status') for r in rows))},
        'standard': {'paragraphs': len(standard_texts), 'min_shared_rows': SHARED_MIN, 'per_field': {STANDARD_FIELDS_DST[s]: dict(std_counts.get(s, {}), shared=s in standard_texts, index=std_index.get(s),
                     linked_rows=sum(1 for p in planned if STANDARD_FIELDS_DST[s] in json.loads(p['values']['standard_refs'] or '{}'))) for s in STANDARD_FIELDS_DST},
                     'provider_fallback_overrides_held': sum(1 for p in planned for h in p['holds'] if h['item'] == 'provider_fallback_policy')},
        'name_holds': [dict(v19_id=p['v19_id'], code=p['code'], **h) for p in planned for h in p['holds'] if h['item'] == 'name'],
        'name_notes': [{'v19_id': p['v19_id'], 'code': p['code'], 'note': n} for p in planned for n in p['notes']],
        'unresolved_relations': [dict(v19_id=p['v19_id'], code=p['code'], **u) for p in planned for u in p['unresolved']],
        'v19_writes': 0,
    }
    return rep


STANDARD_FIELDS_DST = collections.OrderedDict(STANDARD_FIELDS)


# ----------------------------------------------------------------------------------------------------------------------- backend (the only code that touches a database)
class OdooBackend(object):
    """Reads and writes through the caller's own environment. Writes ONLY synapsys.service, synapsys.service.standard and ir.model.data rows that mark them."""
    offline = False
    KIND_MODEL = {'context': 'synapsys.context', 'method': 'synapsys.method', 'canon': 'synapsys.canon', 'pattern': 'synapsys.pattern', 'domain': 'synapsys.domain'}

    def __init__(self, env):
        self.env = env

    # -- lookups (read only)
    def resolve(self, kind, v19_id=None, code=None):
        M = self.env[self.KIND_MODEL[kind]]
        hits = set()
        if v19_id is not None and kind != 'domain':
            hits |= set(M.search([('v19_id', '=', v19_id)]).ids)
        if code and kind in ('context', 'domain'):
            c = set(M.search([('code', '=', code)]).ids)
            if kind == 'domain' or not hits:
                hits |= c
            elif c and c != hits:
                return AMBIGUOUS  # the v19 id and the code point at different records
        if len(hits) == 1:
            return next(iter(hits))
        return AMBIGUOUS if hits else None

    def _xml(self, name):
        return self.env['ir.model.data'].search([('module', '=', XML_MODULE), ('name', '=', name)], limit=1)

    def find_service(self, v19_id):
        x = self._xml(XML_SERVICE % v19_id)
        if x:
            rec = self.env['synapsys.service'].browse(x.res_id)
            return {'id': rec.id, 'marked': True, 'values': self._read(rec)} if rec.exists() else {'id': None, 'marked': True, 'values': {}}
        other = self.env['synapsys.service'].search([('v19_id', '=', v19_id)])
        if other:
            return {'id': other[0].id, 'marked': False, 'values': {}}
        return None

    def _read(self, rec):
        out = {}
        for f in MANAGED:
            v = rec[f]
            if f in ('context_id', 'domain_id', 'method_id', 'standard_id'):
                out[f] = v.id or None
            elif f in M2M:
                out[f] = sorted(v.ids)
            else:
                out[f] = v
        return out

    def find_standard(self):
        x = self._xml(XML_STANDARD)
        if not x:
            return None
        rec = self.env['synapsys.service.standard'].browse(x.res_id)
        return {'id': rec.id, 'paragraphs': json.loads(rec.paragraphs or '[]'), 'name': rec.name} if rec.exists() else None

    # -- writes (only called with apply=True)
    def _mark(self, model, rec, name):
        self.env['ir.model.data'].create({'module': XML_MODULE, 'name': name, 'model': model, 'res_id': rec.id, 'noupdate': True})

    def create_standard(self, name, paragraphs):
        rec = self.env['synapsys.service.standard'].create({'name': name, 'paragraphs': json.dumps(paragraphs, ensure_ascii=False)})
        self._mark('synapsys.service.standard', rec, XML_STANDARD)
        return rec.id

    def write_standard(self, sid, name, paragraphs):
        self.env['synapsys.service.standard'].browse(sid).write({'name': name, 'paragraphs': json.dumps(paragraphs, ensure_ascii=False)})

    def create_service(self, v19_id, vals):
        rec = self.env['synapsys.service'].create(self._orm(vals))
        self._mark('synapsys.service', rec, XML_SERVICE % v19_id)
        return rec.id

    def write_service(self, rid, vals):
        self.env['synapsys.service'].browse(rid).write(self._orm(vals))

    @staticmethod
    def _orm(vals):
        return {k: ([(6, 0, v)] if k in M2M else (v if v is not None else False)) for k, v in vals.items()}

    def marked(self):
        """(service ids, standard id or None) created by this loader."""
        xs = self.env['ir.model.data'].search([('module', '=', XML_MODULE)])
        svc = [x.res_id for x in xs if x.model == 'synapsys.service']
        std = [x.res_id for x in xs if x.model == 'synapsys.service.standard']
        return svc, (std[0] if std else None)

    def delete_marked(self, svc_ids, std_id):
        if svc_ids:
            self.env['synapsys.service'].browse(svc_ids).unlink()
        if std_id and not self.env['synapsys.service'].search([('standard_id', '=', std_id)]):
            self.env['synapsys.service.standard'].browse(std_id).unlink()
        self.env['ir.model.data'].search([('module', '=', XML_MODULE)]).unlink()


# ----------------------------------------------------------------------------------------------------------------------- diff and apply
def _norm_val(f, v):
    if f in M2M:
        return sorted(v or [])
    if f == 'sla_value':
        return float(v) if v else None
    return v if v not in (False, '') else None


def diff_row(planned, found):
    """create / update / unchanged / conflict / held, with the field-level diff for an update."""
    want = {k: v for k, v in planned['values'].items() if k in MANAGED}
    if any(h['item'] == 'name' for h in planned['holds']):
        return {'action': 'HOLD_NAME', 'fields': {}}
    if found is None:
        return {'action': 'CREATE', 'fields': {k: v for k, v in want.items() if _norm_val(k, v) not in (None, [])}}
    if not found['marked']:
        return {'action': 'CONFLICT_UNMARKED', 'fields': {}}  # a row with this v19_id exists that this loader did not create: never touched
    have = found['values']
    ch = {k: (_norm_val(k, have.get(k)), _norm_val(k, v)) for k, v in want.items() if k != 'standard_id' and _norm_val(k, have.get(k)) != _norm_val(k, v)}
    return {'action': 'UPDATE' if ch else 'UNCHANGED', 'fields': ch}


def run(env=None, extract=None, apply=False, name_rulings=None, backend=None, out=None, expected_sha=EXTRACT_SHA256):
    """DRY-RUN unless apply=True. Returns the result dict; prints a readable diff. The caller commits (never this function)."""
    out = out or sys.stdout
    backend = backend or OdooBackend(env)
    doc, sha = load_extract(extract, expected_sha)
    plan = build_plan(doc, backend, name_rulings)
    std_found = backend.find_standard()
    std_action = 'CREATE' if not std_found else ('UPDATE' if std_found['paragraphs'] != plan['standard']['paragraphs'] else 'UNCHANGED')
    diffs = []
    for p in plan['rows']:
        found = backend.find_service(p['v19_id'])
        d = diff_row(p, found)
        d.update(v19_id=p['v19_id'], code=p['code'], found=found, planned=p)
        diffs.append(d)
    counts = collections.Counter(d['action'] for d in diffs)
    result = {'mode': 'APPLY' if apply else 'DRY-RUN', 'extract_sha256': sha, 'standard': std_action, 'counts': dict(counts), 'report': plan['report'], 'writes': {'created': 0, 'updated': 0, 'standard': 0}}
    if apply:
        sid = std_found['id'] if std_found else None
        if std_action == 'CREATE':
            sid = backend.create_standard(plan['standard']['name'], plan['standard']['paragraphs']); result['writes']['standard'] = 1
        elif std_action == 'UPDATE':
            backend.write_standard(sid, plan['standard']['name'], plan['standard']['paragraphs']); result['writes']['standard'] = 1
        for d in diffs:
            vals = dict(d['planned']['values']); vals.pop('_has_standard', None)
            vals['standard_id'] = sid if d['planned']['values'].get('_has_standard') else None
            if d['action'] == 'CREATE':
                backend.create_service(d['v19_id'], {k: v for k, v in vals.items() if _norm_val(k, v) not in (None, [])})
                result['writes']['created'] += 1
            elif d['action'] == 'UPDATE':
                have_std = d['found']['values'].get('standard_id')
                ch = {k: vals[k] for k in d['fields']}
                if (have_std or None) != (vals['standard_id'] or None):
                    ch['standard_id'] = vals['standard_id']
                backend.write_service(d['found']['id'], ch)
                result['writes']['updated'] += 1
            elif d['action'] == 'UNCHANGED' and (d['found']['values'].get('standard_id') or None) != (vals['standard_id'] or None):
                backend.write_service(d['found']['id'], {'standard_id': vals['standard_id']})
                result['writes']['updated'] += 1
    _print(result, diffs, out)
    result['diffs'] = [{k: v for k, v in d.items() if k not in ('found', 'planned')} for d in diffs]
    return result


def rollback(env=None, apply=False, backend=None, out=None):
    """Removes only the services and the Standard this loader created (marked by external id). Dry-run unless apply=True."""
    out = out or sys.stdout
    backend = backend or OdooBackend(env)
    svc, std = backend.marked()
    out.write('%s rollback: %d service row(s) and %s Standard record created by this loader\n' % ('APPLY' if apply else 'DRY-RUN', len(svc), 'the' if std else 'no'))
    if apply:
        backend.delete_marked(svc, std)
    return {'mode': 'APPLY' if apply else 'DRY-RUN', 'services': len(svc), 'standard': bool(std)}


def _print(result, diffs, out):
    r = result['report']
    w = out.write
    w('%s  extract sha256 %s\n' % (result['mode'], result['extract_sha256']))
    w('rows: %s   standard: %s   (create/update/unchanged/held/conflict) %s\n' % (r['extract']['rows'], result['standard'], result['counts']))
    for d in diffs:
        if d['action'] in ('CREATE', 'UPDATE', 'HOLD_NAME', 'CONFLICT_UNMARKED'):
            w('  %-18s v19 %-3s %-10s %s\n' % (d['action'], d['v19_id'], d['code'], ('fields: ' + ', '.join(sorted(d['fields']))) if d['fields'] else ''))
    w('lifecycle (PROPOSED, pending ruling S3): %s\n' % r['lifecycle_counts']['counts'])
    w('names held: %s\n' % [(h['v19_id'], h['code']) for h in r['name_holds']])
    w('relations unresolved: %d\n' % len(r['unresolved_relations']))
    w('unmapped fields reported: %d   v19 writes: %d\n' % (len(r['unmapped_fields']), r['v19_writes']))
    if result['mode'] == 'DRY-RUN':
        w('DRY-RUN: nothing was written. Use apply=True only after review.\n')


def main(argv=None):
    ap = argparse.ArgumentParser(description='Offline plan of the V19 -> V20 Service Catalogue load (no database; relations are not checked).')
    ap.add_argument('--extract', required=True)
    ap.add_argument('--no-lookup', action='store_true', required=True, help='plan without a database (the only mode of this command line; apply needs an Odoo shell)')
    ap.add_argument('--name-ruling', help='JSON {"<v19 id>": "<name>"} recording a Steward ruling for a held name')
    ap.add_argument('--report', help='write the report JSON here')
    a = ap.parse_args(argv)
    doc, sha = load_extract(a.extract)
    plan = build_plan(doc, NoLookup(), json.load(open(a.name_ruling)) if a.name_ruling else None)
    rep = dict(plan['report'], extract_sha256=sha, mode='OFFLINE PLAN (nothing written, relations not checked)')
    if a.report:
        json.dump(rep, open(a.report, 'w'), indent=1, sort_keys=True)
    print(json.dumps({k: rep[k] for k in ('mode', 'extract', 'lifecycle_counts', 'name_holds')}, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main())
