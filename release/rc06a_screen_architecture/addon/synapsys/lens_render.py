"""Architecture > Lenses. Pure renderer (offline-testable). Lens list: live from the V20 registry (class L).
Constructs, nouns and verbs per lens: SNAPSHOT of claude/lens-register-v0.1-and-baseline-2026-11-20.md (not stored in V20).
The Enable/Enhance/Enrich pattern is a BUILDER PROPOSAL over ruled facts (R-1512-1, R-1752-3). Nothing here grants authority."""
from html import escape as e

SNAP = 'Source: lens register v0.1, 20 Nov 2026 (snapshot; constructs are not yet stored in V20)'
# kind, lens, constructs and nouns, verbs, status
LENSES = [
 ('Movement', 'Form', 'define the value, every noun', '', 'RULED'),
 ('Movement', 'Flow', 'deliver the value, every noun', '', 'RULED'),
 ('Movement', 'Evolve', 'measure and adapt, every noun', '', 'RULED'),
 ('Governance', 'Domains D000-D011', 'home domain of each noun, every noun', '', 'RULED'),
 ('Perspective', 'Steward / Collaborator / Client', 'rights and role on every edge', '', 'RULED'),
 ('Context', 'Context lens (per Context)', 'everything inside the boundary and its rights', '', 'RULED'),
 ('Value chain', 'Value-chain lens (per chain)', 'stages: Chain; what moves along it: Programme, Outcome, Benefit, Asset, Offering, Industry, Market, Partner', '', 'RULED'),
 ('Navigation', 'Priorities', 'what comes first: Work, Signal, Strategy', 'filter', 'RULED'),
 ('Navigation', 'Delivery', 'Programme, Project, Service, Workflow, Work, Outcome', 'execute', 'RULED'),
 ('Navigation', 'Assets', 'Asset, Portfolio, Benefit', 'compound', 'RULED'),
 ('Navigation', 'Ecosystem', 'Partner, Industry, Market, Offering, Chain', 'balance', 'RULED'),
 ('Navigation', 'Contexts', 'Context, Purpose, Strategy', 'join', 'RULED'),
 ('Navigation', 'Learning', 'Fractal, Pattern, Change, Method', 'transform', 'RULED'),
 ('Discipline', 'PMBOK', 'Portfolio, Strategy, Programme, Benefit, Project, Outcome, Work, Partner', '', 'REGISTERED'),
 ('Discipline', 'PRINCE2', 'Benefit, Strategy, Project, Outcome, Work, Change, Pattern, Method', '', 'REGISTERED'),
 ('Discipline', 'ITIL', 'Service, Offering, Product, Workflow, Method, Change, Signal, Work, Partner, Benefit, Capability', 'supersedes', 'REGISTERED'),
 ('Discipline', 'TOGAF', 'Capability, Chain, Workflow, Canonical, Pattern, Change', '', 'REGISTERED'),
 ('Discipline', 'MSP', 'Programme, Project, Capability, Outcome, Benefit, Strategy, Purpose, Partner', '', 'REGISTERED'),
 ('Discipline', 'COBIT', 'Domain, Canonical, Portfolio, Benefit, Change, Partner, Fractal', 'validates, verify', 'REGISTERED'),
 ('Discipline', 'ISO 31000', 'Outcome, Benefit, Asset, Signal, Change, Canonical', 'challenge', 'REGISTERED'),
 ('Discipline', 'Regulatory', 'Canonical, Partner, Domain', '', 'REGISTERED, no V19 construct'),
 ('Asset', 'Matter', 'Asset', '', 'IN SCOPE, pairing open'),
 ('Asset', 'Currency', 'Asset', '', 'IN SCOPE, pairing open'),
 ('Asset', 'Tools and Artefacts', 'Asset', '', 'IN SCOPE, pairing open'),
 ('Asset', 'Know-how', 'Asset, Method, Pattern', '', 'IN SCOPE, pairing open'),
 ('Asset', 'Warm Data', 'Asset, Signal', '', 'IN SCOPE, pairing open'),
 ('Asset', 'Wealth and Wellbeing', 'Asset, Benefit', '', 'IN SCOPE, pairing open'),
 ('Mesh', 'Shape', 'structure: Shape, Context, Canonical, Domain', 'map', 'IN SCOPE, verb proposed'),
 ('Mesh', 'Memory', 'before, now, next: Change, Pattern, Canonical', 'supersedes', 'IN SCOPE, verb proposed'),
 ('Mesh', 'Mesh', 'connection and rights: Workflow, Work, Signal, Partner', 'route', 'IN SCOPE, verb proposed'),
 ('Mesh', 'Value', 'value and attestation: Outcome, Benefit, Asset, Chain', 'evidences', 'IN SCOPE, verb proposed'),
 ('Mesh', 'Tension', 'what holds, what breaks: Fractal, Canonical, Partner', 'challenge', 'IN SCOPE, verb proposed'),
 ('Mesh', 'Test', 'how we know it works: Fractal, Change, Method', 'verify', 'IN SCOPE, verb proposed'),
]
OTHER_KINDS = ['Governance', 'Perspective', 'Context', 'Value chain', 'Discipline', 'Asset', 'Mesh']
STAGES = {'Form': ('Orient', 'Canonicalise', 'Structure'), 'Flow': ('Assure', 'Navigate', 'Compose'),
          'Evolve': ('Activate', 'Transform', 'Project')}
LEVELS = [('Enable', 'K-1, K-3, K-4', 'Purpose, Strategy, Asset: the headline view, at most four items.', 'R-1512-1'),
          ('Enhance', 'K-6, K-8', 'Offering, Collaboration: the working sections, six or eight.', 'R-1512-1'),
          ('Enrich', 'K-12', 'Platform: the full detail behind one section.', 'R-1512-1')]
CSS = ('<style>.lv{max-width:1100px;width:100%;margin:0 auto;padding:24px 28px 60px;color:#1f2933}'
       '.lv .cr{font-size:13px;color:#52606d;margin:0 0 14px}.lv .cr a{color:#714b67;cursor:pointer}'
       '.lv h1{font-size:26px;margin:0 0 4px}.lv .sb{color:#52606d;font-size:14px;margin:0 0 16px}'
       '.lv .gr{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px}'
       '.lv .cd{display:block;background:#fff;border:1px solid #e4e7eb;border-radius:10px;padding:14px 16px;color:inherit}'
       '.lv a.cd{cursor:pointer}.lv a.cd:hover{border-color:#714b67}.lv .cd h3{margin:4px 0;font-size:17px}'
       '.lv .kv{display:flex;justify-content:space-between;gap:12px;font-size:13px;padding:4px 0;border-top:1px solid #f0f2f5}'
       '.lv .kv span:first-child{color:#7b8794;white-space:nowrap}.lv .kv span:last-child{text-align:right}'
       '.lv .tg{display:inline-block;font-size:12px;padding:1px 8px;border-radius:6px;background:#f0f4ff;color:#3e4c59;margin-right:4px}'
       '.lv .nt{font-size:12px;color:#7b8794;margin-top:14px}.lv .bx{margin-bottom:14px}</style>')


def kv(a, b):
    return '<div class="kv"><span>%s</span><span>%s</span></div>' % (e(str(a)), e(str(b)))


def card(lv, g, s, tag, title, sub, rows=''):
    return '<a class="cd" data-lv="%d" data-g="%s" data-s="%s"><span class="tg">%s</span><h3>%s</h3><div class="sb">%s</div>%s</a>' % (
        lv, e(g), e(s), e(tag), e(title), e(sub), rows)


def crumb(level, g='', gname=''):
    h = 'Level %d of 3 · Architecture, Lenses' % level
    if level == 1:
        return '<div class="cr">%s, Enable</div>' % h
    h = '<div class="cr">%s · <a data-lv="1" data-g="">Lenses</a>' % h
    if level == 2:
        return h + ' / %s, Enhance</div>' % e(gname)
    return h + ' / <a data-lv="2" data-g="%s">%s</a> / Enrich</div>' % (e(g), e(gname))


def lens_detail(l, verbs=None):
    k, n, c, v, st = l
    return ('<div class="cd bx"><span class="tg">%s</span><span class="tg">%s</span><h3>%s</h3>' % (e(k), e(st), e(n)) +
            kv('Kind', k) + kv('Views these nouns', c) + kv('Verbs', v or 'none registered') + kv('Status', st) + '</div>')


def render(level, group, sec, live_lens_count, verbs):
    """verbs: {action: [verb names]} read live."""
    n_nav = sum(1 for l in LENSES if l[0] == 'Navigation')
    n_other = sum(1 for l in LENSES if l[0] in OTHER_KINDS)
    if level == 1 or group not in ('pattern', 'movement', 'nav', 'other'):
        cards = (card(2, 'pattern', '', 'Pattern', 'The lens pattern', 'Enable, Enhance, Enrich: the repeatable structure') +
                 card(2, 'movement', '', 'Lenses', 'Movement lenses', 'Form, Flow, Evolve and the verbs that activate each', kv('Lenses', 3)) +
                 card(2, 'nav', '', 'Lenses', 'Navigation lenses', 'The six Navigator lenses', kv('Lenses', n_nav)) +
                 card(2, 'other', '', 'Lenses', 'All other lenses', 'Governance, perspective, context, value chain, discipline, asset, mesh',
                      kv('Lenses', n_other)))
        note = 'Registry holds %s lens entries; this page lists %d.' % (live_lens_count, len(LENSES))
        if live_lens_count != len(LENSES):
            note += ' MISMATCH: the snapshot below does not match the registry.'
        return CSS + '<div class="lv">' + crumb(1) + '<h1>Lenses</h1><p class="sb">The ways of looking at the Mesh. Form, Flow and Evolve apply them.</p><div class="gr">%s</div><p class="nt">%s %s</p></div>' % (
            cards, e(note), e(SNAP))
    if level == 2:
        if group == 'pattern':
            cs = ''.join(card(3, 'pattern', 'e%d' % i, 'Level', n, kinds, kv('Context kinds', kinds)) for i, (n, kinds, d, _r) in enumerate(LEVELS))
            body, name, sub = cs, 'The lens pattern', 'Three levels. Ruled: which kinds sit at which level.'
        elif group == 'movement':
            cs = ''.join(card(3, 'movement', 'm%d' % i, 'Lens', st, 'Verbs: ' + ', '.join(gs), kv('Verb groups', len(gs))) for i, (st, gs) in enumerate(STAGES.items()))
            body, name, sub = cs, 'Movement lenses', 'Each stage is activated by its own three verb groups.'
        elif group == 'nav':
            nl = [l for l in LENSES if l[0] == 'Navigation']
            cs = ''.join(card(3, 'nav', 'n%d' % i, 'Lens', l[1], l[2], kv('Verb', l[3])) for i, l in enumerate(nl))
            body, name, sub = cs, 'Navigation lenses', 'Six lenses used by the Navigator.'
        else:
            cs = ''.join(card(3, 'other', 'k%d' % i, 'Kind', k, '%d lenses' % sum(1 for l in LENSES if l[0] == k)) for i, k in enumerate(OTHER_KINDS))
            body, name, sub = cs, 'All other lenses', 'Seven kinds.'
        return CSS + '<div class="lv">' + crumb(2, group, name) + '<h1>%s</h1><p class="sb">%s</p><div class="gr">%s</div><p class="nt">Click one for full detail. %s</p></div>' % (
            e(name), e(sub), body, e(SNAP))
    idx = int(sec[1:]) if sec[1:].isdigit() else -1
    kind = sec[:1]
    names = {'pattern': 'The lens pattern', 'movement': 'Movement lenses', 'nav': 'Navigation lenses', 'other': 'All other lenses'}
    html = ''
    if group == 'pattern' and kind == 'e' and 0 <= idx < 3:
        n, kinds, d, r = LEVELS[idx]
        html = ('<div class="cd bx"><span class="tg">Level</span><h3>%s</h3>' % e(n) + kv('Context kinds', kinds) + kv('Shows', d) +
                kv('Ruling', r) + kv('Grants authority', 'No, a level is descriptive') +
                kv('Open', 'Computed or stored level; how a level applies to a Work Object; lens placement rule') + '</div>')
    elif group == 'movement' and kind == 'm' and 0 <= idx < 3:
        st, gs = list(STAGES.items())[idx]
        l = [x for x in LENSES if x[1] == st][0]
        html = lens_detail(l)
        for g in gs:
            html += '<div class="cd bx"><span class="tg">Verb group</span><h3>%s</h3>%s</div>' % (e(g), kv('Verbs (live)', ', '.join(verbs.get(g, [])) or 'none read'))
    elif group == 'nav' and kind == 'n':
        nl = [l for l in LENSES if l[0] == 'Navigation']
        if 0 <= idx < len(nl):
            html = lens_detail(nl[idx])
    elif group == 'other' and kind == 'k' and 0 <= idx < len(OTHER_KINDS):
        html = ''.join(lens_detail(l) for l in LENSES if l[0] == OTHER_KINDS[idx])
    if not html:
        html = '<p class="sb">Nothing selected.</p>'
    return CSS + '<div class="lv">' + crumb(3, group, names.get(group, '')) + '<h1>%s</h1>%s<p class="nt">%s</p></div>' % (
        e(names.get(group, 'Lenses')), html, e(SNAP))


def lenses_for(group, sec):
    """The lens tuples shown by a level-3 detail (same selection logic as render). Used to attach contract elements."""
    idx = int(sec[1:]) if sec[1:].isdigit() else -1
    kind = sec[:1]
    if group == 'movement' and kind == 'm' and 0 <= idx < 3:
        name = list(STAGES)[idx]
        return [x for x in LENSES if x[1] == name][:1]
    nl = [l for l in LENSES if l[0] == 'Navigation']
    if group == 'nav' and kind == 'n' and 0 <= idx < len(nl):
        return [nl[idx]]
    if group == 'other' and kind == 'k' and 0 <= idx < len(OTHER_KINDS):
        return [l for l in LENSES if l[0] == OTHER_KINDS[idx]]
    return []
