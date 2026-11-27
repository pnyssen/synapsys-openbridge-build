"""Wiring for the read-only scaffold lens: Odoo environment -> scaffold_lens inputs.

RIGHTS: every read uses the CALLER'S OWN environment (request.env). No sudo(), no su, no writes. If the caller lacks the
registry read right Odoo raises AccessError and this module returns REFUSED; it never falls back to elevated reads.
Evidence: the V20 Service Catalogue holds only SP-01, SC-10, GV-GOV-003 and GV-GOV-004 (checked 27 Nov 2026); SC-04, GV-NAV-002,
GV-TEC-001 and SC-05 are not in V20. One catalogue record (SP-01) is bound to N.SERVICE as a PROPOSED relationship and read with
the caller's own rights; N.CAPABILITY has no record and stays NO_OPERATING_SOURCE (HOLD). Nothing here invents a source.
Depth policy (Steward ruling, 26 Nov 2026, in chat): Steward and Collaborator may both reach Enrich. Context-bound evidence stays
gated by Context membership in scaffold_lens (fail-closed: no recognised Context means no evidence).
"""
import hashlib
import json

try:  # inside Odoo
    from . import scaffold_lens as sl
except ImportError:  # offline tests load the module by path
    import scaffold_lens as sl

GROUPS = (('synapsys.group_synapsys_steward', 'steward'), ('synapsys.group_synapsys_user', 'collaborator'))
DEFAULT_ROLE_MAX_DEPTH = {'steward': 'enrich', 'collaborator': 'enrich'}
NOUN = 'N.CONTEXT'

# Evidence bindings (PROPOSED by Claude Code from the record's name and domain, 27 Nov 2026; the Steward may change this table).
# A binding says: this Service Catalogue record is the source-bound library relationship for this peer noun. It is pinned by a
# hash of the record's meaningful fields, so any edit of the record shows as SOURCE_HASH_MISMATCH until re-pinned by a patch.
SOURCE_FIELDS = ('x_service_code', 'x_service_name', 'x_service_status', 'x_lifecycle_gate', 'x_validation_status',
                 'x_source_document', 'x_source_version', 'x_primary_governing_domain', 'x_processability_state')
EVIDENCE_BINDINGS = {
    'N.SERVICE': [{'model': 'x_service_catalogue', 'code_field': 'x_service_code', 'code': 'SP-01',
                   'pinned_sha256': '608938cd399ef7b5694658dc6e34db063f9317d950439de537be0f5d663fe17c'}],
}


def actor_from_env(env):
    groups = set(role for xmlid, role in GROUPS if env.user.has_group(xmlid))
    return {'uid': env.user.id, 'groups': groups, 'context_ids': set()}


def _is_access_error(exc):
    return exc.__class__.__name__ == 'AccessError'


def load_registry(env, version=None):
    """Return (registry_dict, provenance, error). Uses the caller's own rights."""
    try:
        domain = [('version', '=', version)] if version else []
        rec = env['synapsys.mesh.registry'].search(domain, order='id desc', limit=1)
        if not rec:
            return None, None, 'REGISTRY_NOT_FOUND'
        body = rec.body or ''
        sha = hashlib.sha256(body.encode('utf-8')).hexdigest()
        if sha != rec.sha:
            return None, None, 'REGISTRY_BODY_HASH_MISMATCH'
        reg = json.loads(body)
        reg.setdefault('version', rec.version)
        return reg, {'registry_version': rec.version, 'registry_sha': sha, 'registry_state': rec.state}, None
    except Exception as exc:  # noqa: BLE001 - classify, never leak details
        if _is_access_error(exc):
            return None, None, 'NO_REGISTRY_READ_RIGHT'
        raise


def canonical_hash(values):
    c = json.dumps({k: (values.get(k) or None) for k in SOURCE_FIELDS}, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    return hashlib.sha256(c.encode('utf-8')).hexdigest()


def qualifiers(values):
    """Plain-language gaps so a catalogue record is never read as proof of operation."""
    q = ['catalogue record only: existence is not operation']
    if values.get('x_validation_status') != 'validated':
        q.append('validation: %s' % (values.get('x_validation_status') or 'none recorded'))
    if not values.get('x_source_document'):
        q.append('no source document recorded')
    q.append('not bound to a Context')
    return q


def collect_evidence(env):
    """Read each bound catalogue record with the CALLER'S rights. Returns (evidence, library_index, notes)."""
    evidence, index, notes = [], {}, []
    for noun, bindings in EVIDENCE_BINDINGS.items():
        for b in bindings:
            ref = '%s:%s' % (b['model'], b['code'])
            try:
                rec = env[b['model']].search([(b['code_field'], '=', b['code'])], limit=1)
                if not rec:
                    notes.append('%s: record not found' % ref)
                    continue
                values = {f: rec[f] for f in SOURCE_FIELDS}
            except Exception as exc:  # noqa: BLE001
                if _is_access_error(exc):
                    notes.append('%s: not readable with your rights' % ref)
                    continue
                raise
            index[ref] = {'sha256': canonical_hash(values), 'label': '%s %s' % (values.get('x_service_code'), values.get('x_service_name')),
                          'detail': {'fields': {k: (values.get(k) or None) for k in SOURCE_FIELDS}, 'qualifiers': qualifiers(values)}}
            evidence.append({'id': 'EV:%s' % ref, 'noun_id': noun, 'scope': 'catalogue', 'kind': 'library',
                             'source_ref': ref, 'sha256': b['pinned_sha256']})
    return evidence, index, notes


def scaffold_context(env, depth='enable', context_id='', version=None):
    if depth not in sl.DEPTHS:
        return {'result': 'REFUSED', 'reason': 'UNKNOWN_DEPTH'}
    actor = actor_from_env(env)
    if not actor['groups']:
        return {'result': 'REFUSED', 'reason': 'NO_RECOGNISED_ROLE'}
    reg, prov, err = load_registry(env, version)
    if err:
        return {'result': 'REFUSED', 'reason': err}
    evidence, index, notes = collect_evidence(env)
    out = sl.build_scaffold(reg, NOUN, depth, actor, evidence, index, str(context_id or ''), DEFAULT_ROLE_MAX_DEPTH)
    out.update(prov)
    out['evidence_notes'] = notes
    return out
