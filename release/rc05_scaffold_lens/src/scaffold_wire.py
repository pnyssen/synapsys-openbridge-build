"""Wiring for the read-only scaffold lens: Odoo environment -> scaffold_lens inputs.

RIGHTS: every read uses the CALLER'S OWN environment (request.env). No sudo(), no su, no writes. If the caller lacks the
registry read right Odoo raises AccessError and this module returns REFUSED; it never falls back to elevated reads.
Evidence and library records: no registered SC-04/GV-NAV-002 source exists in V20 yet, so none is passed. Every peer is
therefore shown NO_OPERATING_SOURCE (HOLD), which is the truthful state. Nothing here invents a source.
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


def scaffold_context(env, depth='enable', context_id='', version=None):
    if depth not in sl.DEPTHS:
        return {'result': 'REFUSED', 'reason': 'UNKNOWN_DEPTH'}
    actor = actor_from_env(env)
    if not actor['groups']:
        return {'result': 'REFUSED', 'reason': 'NO_RECOGNISED_ROLE'}
    reg, prov, err = load_registry(env, version)
    if err:
        return {'result': 'REFUSED', 'reason': err}
    out = sl.build_scaffold(reg, NOUN, depth, actor, [], {}, str(context_id or ''), DEFAULT_ROLE_MAX_DEPTH)
    out.update(prov)
    return out
