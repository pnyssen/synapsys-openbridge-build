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
    from . import screen_decl as sd
    from . import screen_binding as sb
    from . import screen_render as sr
    from . import service_health as sh
except ImportError:  # offline tests load the module by path
    import scaffold_lens as sl
    import screen_decl as sd
    import screen_binding as sb
    import screen_render as sr
    import service_health as sh

GROUPS = (('synapsys.group_synapsys_steward', 'steward'), ('synapsys.group_synapsys_user', 'collaborator'))
DEFAULT_ROLE_MAX_DEPTH = {'steward': 'enrich', 'collaborator': 'enrich'}
NOUN = 'N.CONTEXT'
NOUN_SCREEN = 'SCR.CONTEXT.NOUN'
_DECLS = {}
_BINDINGS = {}

# Evidence bindings (PROPOSED by Claude Code from the record's name and domain, 27 Nov 2026; the Steward may change this table).
# A binding says: this Service Catalogue record is the source-bound library relationship for this peer noun. It is pinned by a
# hash of the record's meaningful fields, so any edit of the record shows as SOURCE_HASH_MISMATCH until re-pinned by a patch.
SOURCE_FIELDS = ('x_service_code', 'x_service_name', 'x_service_status', 'x_lifecycle_gate', 'x_validation_status',
                 'x_source_document', 'x_source_version', 'x_primary_governing_domain', 'x_processability_state')
# Native V20 Service record (synapsys.service), bound by stable Service code. Source-specific fields only; Context and Method are
# reported as binding STATE (UNBOUND when absent), never invented and never part of the pin. Historical V19 ids are not V20 identities.
NATIVE_SERVICE_FIELDS = ('code', 'name', 'lifecycle', 'validation_status_v19', 'ffe_state_v19')
EVIDENCE_BINDINGS = {
    'N.SERVICE': [{'model': 'x_service_catalogue', 'code_field': 'x_service_code', 'code': 'SP-01',
                   'pinned_sha256': '608938cd399ef7b5694658dc6e34db063f9317d950439de537be0f5d663fe17c'},
                  {'model': 'synapsys.service', 'code_field': 'code', 'code': 'SB-02', 'fields': NATIVE_SERVICE_FIELDS,
                   'state_fields': ('context_id', 'method_id', 'plug_in_ready'),
                   'pinned_sha256': 'e489d825e505089a761aa8c12c3794203a08385736251a59f6be04f116e2e0e3'}],
}


def _rid(x):
    return getattr(x, 'id', x)


def _entitled(rec, uid):
    """Belt and braces on top of the record rule: the Context must name this user as steward or member in the record itself."""
    if _rid(getattr(rec, 'steward_user_id', None)) == uid:
        return True
    return uid in [_rid(m) for m in (getattr(rec, 'member_ids', None) or ())]


def actor_context_ids(env, uid):
    """Context ids this actor may act in, from the native ORM with the CALLER'S OWN rights (no sudo). Fail closed: no access,
    no model, or no membership means no Context ids, never a guess."""
    try:
        recs = env['synapsys.context'].search(['|', ('steward_user_id', '=', uid), ('member_ids', 'in', uid)])
        return set(_rid(r) for r in recs if _entitled(r, uid))
    except KeyError:
        return set()
    except Exception as exc:  # noqa: BLE001
        if _is_access_error(exc) or exc.__class__.__name__ == 'MissingError':
            return set()
        raise


def actor_from_env(env):
    groups = set(role for xmlid, role in GROUPS if env.user.has_group(xmlid))
    uid = env.user.id
    return {'uid': uid, 'groups': groups, 'context_ids': actor_context_ids(env, uid) if groups else set()}


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


def canonical_hash(values, fields=SOURCE_FIELDS):
    c = json.dumps({k: (values.get(k) or None) for k in fields}, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
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


def _opt(rec, f):
    """Read an optional health field; an absent field is None (never invented, never an error)."""
    try:
        return rec[f]
    except (KeyError, AttributeError):
        return None


def native_state(state):
    """Truthful binding state for a native Service: UNBOUND/HOLD when Context or Method is absent. Never inferred."""
    ctx, mth = bool(state.get('context_id')), bool(state.get('method_id'))
    return {'context': 'BOUND' if ctx else 'UNBOUND', 'method': 'BOUND' if mth else 'UNBOUND',
            'plug_in_ready': bool(state.get('plug_in_ready')), 'status': 'BOUND' if (ctx and mth) else 'UNBOUND/HOLD'}


def native_qualifiers(state):
    q = ['native Service record: existence is not operation']
    if not state.get('context_id'):
        q.append('not bound to a Context (UNBOUND/HOLD)')
    if not state.get('method_id'):
        q.append('no Method anchored (UNBOUND/HOLD)')
    if not state.get('plug_in_ready'):
        q.append('plug_in_ready is false')
    return q


def collect_evidence(env):
    """Read each bound catalogue record with the CALLER'S rights. Returns (evidence, library_index, notes)."""
    evidence, index, notes = [], {}, []
    for noun, bindings in EVIDENCE_BINDINGS.items():
        for b in bindings:
            ref = '%s:%s' % (b['model'], b['code'])
            flds = b.get('fields') or SOURCE_FIELDS
            try:
                rec = env[b['model']].search([(b['code_field'], '=', b['code'])], limit=1)
                if not rec:
                    if not b.get('fields'):          # native bindings: an absent or invisible record is simply not evidence (no new note)
                        notes.append('%s: record not found' % ref)
                    continue
                values = {f: rec[f] for f in flds}
                state = {f: rec[f] for f in b.get('state_fields', ())}
                if b.get('fields') and state.get('context_id') and _rid(state['context_id']) not in actor_context_ids(env, env.user.id):
                    continue                          # native record bound to a Context this actor is not entitled to: withheld, and
                                                      # indistinguishable from not-found (no note, no id, no hash, no count)
            except KeyError:
                notes.append('%s: model not present in this database' % ref)
                continue
            except Exception as exc:  # noqa: BLE001
                if _is_access_error(exc):
                    notes.append('%s: not readable with your rights' % ref)
                    continue
                raise
            if b.get('fields'):
                label = '%s %s' % (values.get('code'), values.get('name'))
                quals = native_qualifiers(state)
                hv = {f: _opt(rec, f) for f in sh.HEALTH_DEPENDS + ('pattern_ids', 'answer_accepted')}
                health = sh.project(hv, actor_context_ids(env, env.user.id), answer_accepted_flag=hv.get('answer_accepted'))
                quals.append('relationship coverage: %s (per-edge states in detail)' % health['relationships']['summary'])
                quals.append('operating qualification: %s (slots, plug_in_ready and answer_accepted are not operating evidence)'
                             % health['operating']['state'])
                detail = {'fields': {k: (values.get(k) or None) for k in flds}, 'binding_state': native_state(state), 'qualifiers': quals,
                          'health': health}
            else:
                label = '%s %s' % (values.get('x_service_code'), values.get('x_service_name'))
                detail = {'fields': {k: (values.get(k) or None) for k in SOURCE_FIELDS}, 'qualifiers': qualifiers(values)}
            index[ref] = {'sha256': canonical_hash(values, flds), 'label': label, 'detail': detail}
            evidence.append({'id': 'EV:%s' % ref, 'noun_id': noun, 'scope': 'catalogue', 'kind': 'library',
                             'source_ref': ref, 'sha256': b['pinned_sha256']})
    return evidence, index, notes


def declarations():
    """Screen declarations, loaded once and validated. Raises ValueError if any declaration is invalid."""
    if not _DECLS:
        _DECLS['v'] = sd.load_declarations()
    return _DECLS['v']


def _project(env, decl, depth, context_id, record=None, version=None, need_evidence=True):
    actor = actor_from_env(env)
    if not actor['groups']:
        return {'result': 'REFUSED', 'reason': 'NO_RECOGNISED_ROLE'}
    reg, prov, err = load_registry(env, version)
    if err:
        return {'result': 'REFUSED', 'reason': err}
    evidence, index, notes = collect_evidence(env) if need_evidence else ([], {}, [])
    out = sd.project(decl, reg, depth, actor, evidence, index, str(context_id or ''), DEFAULT_ROLE_MAX_DEPTH, record)
    if out.get('result') == 'OK':
        out.update(prov)
        out['declaration_sha'] = declarations()[1]['file_of'][decl['id']]
        out['evidence_notes'] = notes
    return out


def scaffold_context(env, depth='enable', context_id='', version=None):
    """Noun screen for Context. The route's context_id is carried through to the evidence gate only; it does not select a
    record (an empty or non-existent id returns the same screen: OPEN item for the Steward, not decided here)."""
    if depth not in sl.DEPTHS:
        return {'result': 'REFUSED', 'reason': 'UNKNOWN_DEPTH'}
    try:
        decl = declarations()[0][NOUN_SCREEN]
    except ValueError:
        return {'result': 'REFUSED', 'reason': 'DECLARATION_INVALID'}
    return _project(env, decl, depth, context_id, None, version)


def scaffold_noun(env, screen_id, depth='enable', context_id=''):
    """Any declared NOUN screen (RC06b batch 1), read with the caller's own rights. Not routed: no menu, route or install here."""
    if depth not in sl.DEPTHS:
        return {'result': 'REFUSED', 'reason': 'UNKNOWN_DEPTH'}
    try:
        decl = declarations()[0].get(screen_id)
    except ValueError:
        return {'result': 'REFUSED', 'reason': 'DECLARATION_INVALID'}
    if not decl or decl['screen_type'] != 'noun':
        return {'result': 'REFUSED', 'reason': 'UNKNOWN_SCREEN'}
    return _project(env, decl, depth, context_id)


def scaffold_menu(env, screen_id, depth='enable'):
    """Any declared MENU screen (RC06d): built from its document source rows, no registry read, no catalogue read, no write. Not routed."""
    if depth not in sl.DEPTHS:
        return {'result': 'REFUSED', 'reason': 'UNKNOWN_DEPTH'}
    try:
        decls, meta = declarations()
    except ValueError:
        return {'result': 'REFUSED', 'reason': 'DECLARATION_INVALID'}
    decl = decls.get(screen_id)
    if not decl or decl['screen_type'] != 'menu':
        return {'result': 'REFUSED', 'reason': 'UNKNOWN_SCREEN'}
    actor = actor_from_env(env)
    if not actor['groups']:
        return {'result': 'REFUSED', 'reason': 'NO_RECOGNISED_ROLE'}
    out = sd.project_menu(decl, depth, actor, DEFAULT_ROLE_MAX_DEPTH)
    if out.get('result') == 'OK':
        out['declaration_sha'] = meta['file_of'][decl['id']]
        out['sources_sha'] = meta['sources_of'][decl['id']]
    return out


def _field(rec, name):
    v = rec[name]
    return getattr(v, 'id', v)


def screen_record(env, screen_id, record_id, depth='enable'):
    """Record screen for one record, read with the CALLER'S rights (no sudo). Not routed in RC06a: there is no controller
    route for it and dev holds no operating records; it is exercised by tests with rolled-back fixtures."""
    if depth not in sl.DEPTHS:
        return {'result': 'REFUSED', 'reason': 'UNKNOWN_DEPTH'}
    try:
        decl = declarations()[0].get(screen_id)
    except ValueError:
        return {'result': 'REFUSED', 'reason': 'DECLARATION_INVALID'}
    if not decl or decl['screen_type'] != 'record':
        return {'result': 'REFUSED', 'reason': 'UNKNOWN_SCREEN'}
    rd = decl['record']
    try:
        rid = int(record_id)
    except (TypeError, ValueError):
        return {'result': 'REFUSED', 'reason': 'RECORD_NOT_FOUND'}
    try:
        rec = env[rd['model']].search([('id', '=', rid)], limit=1)
        if not rec:
            return {'result': 'REFUSED', 'reason': 'RECORD_NOT_FOUND'}
        record = {'model': rd['model'], 'id': rid, 'name': rec[rd['name_field']] or None,
                  'kind': _field(rec, rd['kind']['field']) if 'field' in rd['kind'] else None,
                  'neighbour_kind': _field(rec, rd['neighbour_kind_field']) if rd.get('neighbour_kind_field') else None}
        ctx = str(_field(rec, rd['context_field']) or '') if rd.get('context_field') else ''
    except Exception as exc:  # noqa: BLE001 - classify, never leak details
        if _is_access_error(exc):
            return {'result': 'REFUSED', 'reason': 'NO_RECORD_READ_RIGHT'}
        raise
    return _project(env, decl, depth, ctx, record)


def bindings():
    """The menu bindings, loaded once and validated against the declarations: (rows, by action id, by menu id)."""
    if not _BINDINGS:
        _BINDINGS['v'] = sb.load(None, declarations()[0])
    return _BINDINGS['v']


def _refused(reason):
    return {'result': 'REFUSED', 'reason': reason}  # a reason code and nothing else: no declaration, source or binding content


def _can_read(env, model):
    """The actor's REAL read right on the native model, enforced server-side (never inferred from menu groups). Fail closed."""
    try:
        m = env[model]
    except Exception:  # noqa: BLE001 - an unknown model is a refusal, not a leak
        return False
    try:
        if hasattr(m, 'check_access'):
            m.check_access('read')
            return True
        return bool(m.check_access_rights('read', raise_exception=False))
    except Exception as exc:  # noqa: BLE001
        if _is_access_error(exc):
            return False
        raise


def menu_enable(env, action_id, menu_id=None, screen_id='', depth='enable'):
    """Page for a bound menu's native view (RC06g Enable panel; RC06h: all three depths, in the lens template). Read-only; the native action, view and rights are not touched.

    Order is fail-closed and leaks nothing before entitlement: recognised role, then the binding for this action, then the actor's real read
    right on the native model, and only then the anchors, the screen id and the content. A refusal is a reason code only."""
    if depth not in ('enable', 'enhance', 'enrich'):
        return _refused('DEPTH_NOT_SUPPORTED')
    try:
        _rows, by_action, _by_menu = bindings()
    except ValueError:
        return _refused('BINDING_INVALID')
    if not actor_from_env(env)['groups']:
        return _refused('NO_RECOGNISED_ROLE')
    try:
        aid = int(action_id)
    except (TypeError, ValueError):
        return _refused('MENU_NOT_BOUND')
    b = by_action.get(aid)
    if not b:
        return _refused('MENU_NOT_BOUND')  # includes the 8 unbound menus and any action that is not a bound one
    if not _can_read(env, b['native']['model']):
        return _refused('NO_READ_RIGHT')
    if menu_id not in (None, '', b['menu_id']):
        return _refused('ANCHOR_MISMATCH')
    try:
        act = env.ref(b['action_xmlid'], raise_if_not_found=False)
        menu = env['ir.ui.menu'].search([('id', '=', b['menu_id'])], limit=1)
    except Exception as exc:  # noqa: BLE001
        if _is_access_error(exc):
            return _refused('NO_READ_RIGHT')
        raise
    if not menu:
        return _refused('MENU_NOT_VISIBLE')
    macts = menu['action']
    if not act or act.id != b['action_id'] or not macts or macts.id != b['action_id']:
        return _refused('ANCHOR_MISMATCH')
    decls = declarations()[0]
    if screen_id:
        if screen_id not in decls:
            return _refused('UNKNOWN_SCREEN')
        if screen_id != b['screen_id']:
            return _refused('SCREEN_NOT_BOUND_TO_MENU')
    decl = decls[b['screen_id']]
    if decl['screen_type'] == 'menu':
        out = sd.project_menu(decl, depth, actor_from_env(env), DEFAULT_ROLE_MAX_DEPTH)
        if out.get('result') == 'OK':
            out['sources_sha'] = declarations()[1]['sources_of'][decl['id']]
    else:
        out = _project(env, decl, depth, '', need_evidence=depth != 'enable' or bool(decl.get('peers')))
    if out.get('result') != 'OK':
        return _refused(out.get('reason', 'NOT_AVAILABLE'))
    if out.get('screen') != b['screen_id']:
        return _refused('ANCHOR_MISMATCH')
    return {'result': 'OK', 'screen_id': b['screen_id'], 'menu_id': b['menu_id'], 'action_id': b['action_id'], 'status': out.get('status'),
            'binding_status': b['binding_status'], 'depth': out.get('depth_effective'), 'html': sr.render_menu_page(out, b['binding_status']), 'writes': 0}

