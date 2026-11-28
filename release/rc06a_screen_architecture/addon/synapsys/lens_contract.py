"""Recursive lens contract: ONE reusable presentation-depth renderer (Enable, Enhance, Enrich).

PRESENTATION ONLY. A mode decides how much of an element is shown. It never reads or writes a record, never derives or
changes a K-kind, PPV, approval, Context or right, and never grants authority. Every value comes from the element
dictionary the caller built from its source; a missing value is shown as UNSOURCED, never guessed.
Same contract serves any surface (Architecture lenses, Architecture map nouns, later menus, screens, Services, Methods).
Builder candidate, not released, not assured.
"""
from html import escape as _e

MODES = ('enable', 'enhance', 'enrich')
LABEL = {'enable': 'Enable', 'enhance': 'Enhance', 'enrich': 'Enrich'}
DEPTH = {'enable': 'Summary', 'enhance': 'Relationships and actions', 'enrich': 'Provenance, source, evidence, controls'}
UNSOURCED = 'UNSOURCED'
_SAFE = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._:-')


STYLE = ('<style>.syn-el{display:block;background:#fff;border:1px solid #e4e7eb;border-radius:10px;padding:14px 16px;margin:14px 0;'
         'max-width:1100px;color:#1f2933}.syn-el h3{margin:4px 0;font-size:17px}'
         '.syn-el .kv{display:flex;justify-content:space-between;gap:12px;font-size:13px;padding:4px 0;border-top:1px solid #f0f2f5}'
         '.syn-el .kv span:first-child{color:#7b8794;min-width:35%}.syn-el .kv span:last-child{text-align:right;overflow-wrap:anywhere}'
         '.syn-el .kv ul{margin:0;padding-left:16px;text-align:left}'
         '.syn-el .tg{display:inline-block;font-size:12px;padding:1px 8px;border-radius:6px;background:#f0f4ff;color:#3e4c59;margin-right:4px;cursor:pointer}'
         '.syn-el .nt{margin-top:8px}@media (max-width:600px){.syn-el .kv{flex-direction:column;gap:2px}.syn-el .kv span:last-child{text-align:left}}</style>')


def normalise(mode):
    return mode if mode in MODES else 'enable'


def parse_overrides(text):
    """'id@mode;id@mode' -> {id: mode}. Unknown modes and unsafe ids are dropped, never guessed."""
    out = {}
    for part in (text or '').split(';')[:50]:
        eid, _, m = part.rpartition('@')
        if eid and m in MODES and set(eid) <= _SAFE and len(eid) <= 80:
            out[eid] = m
    return out


def element(eid, label, **kw):
    """Element contract. Keys other than id/label are optional: ancestors (source-record lineage, nearest first), noun, verbs, ffe, kind, kind_via, service, method,
    oba, source, definition, status, evidence, relationships [(label, direction, other_id, other_label)], open_questions."""
    d = {'id': eid, 'label': label}
    d.update(kw)
    return d


def _v(x):
    if x is None or x == '' or x == [] or x == () or x == {}:
        return UNSOURCED
    if isinstance(x, (list, tuple)):
        return ', '.join(str(i) for i in x)
    return str(x)


def _row(k, v):
    return '<div class="kv"><span>%s</span><span>%s</span></div>' % (_e(k), _e(_v(v)))


def mode_for(eid, mode, overrides, ancestors=()):
    """Effective depth. Exact override on this element wins; else the CLOSEST ancestor override; else the global mode.
    `ancestors` is source-record lineage supplied by the caller, nearest first (e.g. the Context record a Service record
    belongs to). It is never derived from a name or id prefix. Clearing an override falls back to the parent, then global."""
    ov = overrides or {}
    if eid in ov:
        return normalise(ov[eid])
    for a in (ancestors or ()):
        if a in ov:
            return normalise(ov[a])
    return normalise(mode)


def render_element(el, mode='enable', overrides=None, obj_link=False):
    """Return an HTML fragment for ONE element at the effective mode. Pure; does not mutate el."""
    eid = el['id']
    glob = normalise(mode)
    anc = tuple(el.get('ancestors') or ())
    eff = mode_for(eid, glob, overrides, anc)
    exact = eid in (overrides or {})
    local = exact and eff != glob
    inherited = (not exact) and eff != glob
    rows = [_row('Noun', el.get('noun')), _row('Source state', el.get('status')),
            _row('Definition', el.get('definition'))]
    if eff in ('enhance', 'enrich'):
        rels = el.get('relationships') or []
        if rels:
            items = ''.join('<li>%s %s <a data-obj="%s" data-trail="">%s</a></li>' % (
                _e(str(r[0])), _e('to' if r[1] == 'out' else 'from'), _e(str(r[2]), quote=True), _e(str(r[3]))) if obj_link
                else '<li>%s %s %s</li>' % (_e(str(r[0])), _e('to' if r[1] == 'out' else 'from'), _e(str(r[3])))
                for r in rels[:12])
            more = '' if len(rels) <= 12 else '<li>and %d more</li>' % (len(rels) - 12)
            rows.append('<div class="kv"><span>Relationships</span><span><ul>%s%s</ul></span></div>' % (items, more))
        else:
            rows.append(_row('Relationships', None))
        rows += [_row('Governed verbs', el.get('verbs')), _row('Form / Flow / Evolve', el.get('ffe'))]
    if eff == 'enrich':
        rows += [_row('Kind (bound to element and Context)', (_v(el.get('kind')) if el.get('kind') else 'UNBOUND')
                      + ((' via ' + str(el['kind_via'])) if el.get('kind_via') else '')),
                 _row('Service / Method', ' / '.join(x for x in (el.get('service'), el.get('method')) if x) or None),
                 _row('Intended Outcome, Benefit, Asset', el.get('oba')),
                 _row('Source', el.get('source')), _row('Evidence', el.get('evidence')),
                 _row('Open questions', el.get('open_questions')),
                 _row('Controls', 'Presentation only. This view changes no data, kind, PPV, approval or right.'),
                 _row('Stable id', eid)]
    btn = ''
    if eff != 'enrich':
        nxt = MODES[MODES.index(eff) + 1]
        btn += '<a class="tg" data-ovel="%s" data-ovmode="%s">Show %s here only</a>' % (_e(eid, quote=True), nxt, LABEL[nxt])
    if local:
        btn += '<a class="tg" data-ovel="%s" data-ovmode="">Reset to global</a>' % _e(eid, quote=True)
    return (STYLE + '<div class="cd bx syn-el" data-element="%s" data-mode="%s" data-global="%s" data-override="%s">'
            '<span class="tg">%s</span><span class="tg">%s</span><h3>%s</h3>%s<div class="nt">%s</div></div>' % (
                _e(eid, quote=True), eff, glob, 'yes' if local else 'inherited' if inherited else 'no', _e(LABEL[eff]), _e(DEPTH[eff]),
                _e(str(el.get('label') or eid)), ''.join(rows), btn))


def from_lens(lens):
    k, n, c, v, st = lens
    return element('lens:%s' % n.replace(' ', '_'), n, noun=c, status=st, definition='Lens kind: %s' % k,
                   verbs=v or None, source='Lens register v0.1 snapshot, 20 Nov 2026 (not stored in V20)',
                   ffe=n if k == 'Movement' else None)


def from_noun(graph, noun_id):
    """Build an element from the live candidate registry graph (synapsys_mesh.journey.Graph). Nothing is invented."""
    e = graph.els.get(noun_id)
    if not e:
        return None
    rels = []
    for r in graph.rels:
        if r['from'] == noun_id:
            rels.append((r['label'] or r['id'], 'out', r['to'], graph.label(r['to'])))
        elif r['to'] == noun_id:
            rels.append((r['label'] or r['id'], 'in', r['from'], graph.label(r['from'])))
    roles = dict()
    for role, x in graph.roles.get(noun_id, []):
        roles.setdefault(role, []).append(graph.label(x))
    return element(noun_id, e.get('label') or noun_id, noun=e.get('label') or noun_id, status=e.get('status'),
                   definition=e.get('definition'), source=e.get('definition_source'),
                   kind=e.get('kind') or None, kind_via=', '.join(roles.get('kind_via', [])) or None,
                   relationships=rels, ffe=e.get('menu'), open_questions=len(e.get('open_questions') or ()) or None,
                   verbs=None, evidence=None, oba=None, service=None, method=None)
