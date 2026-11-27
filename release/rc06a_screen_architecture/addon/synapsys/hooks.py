import json
from odoo.modules.module import get_module_path
from odoo.exceptions import UserError


def post_init_hook(env):
    """Reference configuration only (domains, 27 verbs, 6 modes). Fail closed on any count mismatch."""
    with open(get_module_path('synapsys') + '/data/reference.json', encoding='utf-8') as f:
        d = json.load(f)
    Dom = env['synapsys.domain']
    for code, name in d['domains']:
        Dom.create({'code': code, 'name': name})
    Verb = env['synapsys.verb']
    vmap = {}
    for v in d['verbs']:
        vmap[v['name']] = Verb.create({'name': v['name'], 'strategy': v['strategy'], 'sequence': v['sequence'],
                                       'movement': v['movement'] or False, 'movement_group': v['group'] or False,
                                       'motion': v['motion'] or False})
    # Grammar and approved derivative forms (DEC-D001-2026-021). Every one of the 27 must have a row: fail closed.
    src = d.get('grammar_source', {})
    grammar = d.get('grammar', {})
    if set(grammar) != set(vmap):
        raise UserError('SynapSys grammar load failed closed: grammar names differ from the 27 verbs.')
    for name, g in grammar.items():
        vmap[name].write({'plane': g['plane'], 'action': g['action'], 'direction': g['direction'],
                          'aliases': g['aliases'] or False, 'inverse': g['inverse'] or False,
                          'bidirectionality': g['bidirectionality'], 'authority_requirement': g['authority'],
                          'human_only': g['bidirectionality'] == 'PROHIBITED_REVERSE',
                          'grammar_status': src.get('status', 'candidate'), 'grammar_sha256': src.get('sha256')})
    for code, name, verbs in d['modes']:
        env['synapsys.mode'].create({'code': code, 'name': name, 'verb_ids': [(6, 0, [vmap[x].id for x in verbs])]})
    got = (Dom.search_count([]), Verb.search_count([]), env['synapsys.mode'].search_count([]))
    if got != (12, 27, 6):
        raise UserError('SynapSys reference load failed closed: got %s, expected (12, 27, 6)' % (got,))
    load_domain_instructions(env)


def load_domain_instructions(env):
    """Seat instructions into the Architecture (Steward 20 Nov 2026 11:14). Fail closed on any hash mismatch:
    the bytes held here must equal the Working Memory mirror they were read from."""
    import hashlib, os
    base = get_module_path('synapsys') + '/data/domain_instructions'
    with open(base + '/instructions.json', encoding='utf-8') as f:
        spec = json.load(f)['instructions']
    Canon, Dom = env['synapsys.canon'], env['synapsys.domain']
    made = {}
    for it in spec:
        raw = open(os.path.join(base, it['file']), 'rb').read()
        if hashlib.sha256(raw).hexdigest() != it['sha256']:
            raise UserError('Seat instruction load failed closed: %s does not match its recorded sha256.' % it['file'])
        held = Canon.search([('kind', '=', 'instruction'), ('sha256', '=', it['sha256'])], limit=1)
        if held:  # idempotent: the upgrade path (migration) may run this on a database that already holds it
            made[it['file']] = held
            continue
        dom = Dom.search([('code', '=', it['domain'])], limit=1) if it['domain'] else Dom.browse()
        if it['domain'] and not dom:
            raise UserError('Seat instruction load failed closed: domain %s not found.' % it['domain'])
        made[it['file']] = Canon.create({
            'name': it['file'].replace('.md', '').replace('_', ' '), 'kind': 'instruction', 'tier': 'tier_2_governance',
            'domain_id': dom.id or False, 'shared': it['shared'], 'version': it['version'], 'state': it['state'],
            'body': raw.decode('utf-8'), 'sha256': it['sha256'], 'mirror_path': it['mirror_path'],
            'adopted_note': it['adopted_note'],
            'replaces_id': made[it['replaces']].id if it.get('replaces') else False})
    missing = [d.code for d in Dom.search([]) if not d.seat_instruction_text]
    if missing:
        raise UserError('Seat instruction load failed closed: no instruction set for %s.' % ', '.join(missing))
