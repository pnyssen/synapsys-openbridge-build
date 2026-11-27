"""The one screen renderer (RC06a, source-only candidate).

Builds the fixed frame (header, answer, trust line, movement) and the depth sections from a screen model produced by
screen_decl.project. There is no per-screen rendering code: every slot is built by one generic function, in declared order.
Pure: every dynamic value is escaped; no scripts, no inline event handlers, no external URLs. Presentation only: it changes no
data, kind, PPV, approval or right.
"""
from html import escape as _e

STYLE = ('<style>.syn-sc{max-width:1100px;margin:0 auto;padding:16px 16px 48px;color:#1f2933;box-sizing:border-box}'
         '.syn-sc *{box-sizing:border-box}.syn-sc h1{font-size:24px;margin:0 0 4px}.syn-sc h2{font-size:17px;margin:20px 0 8px}'
         '.syn-sc .sb{color:#52606d;font-size:14px;margin:0 0 12px;overflow-wrap:anywhere}'
         '.syn-sc .lb{font-size:13px;color:#52606d;margin:0 0 8px}.syn-sc .lb span{margin-right:12px}'
         '.syn-sc .an{font-size:15px;margin:0 0 8px;overflow-wrap:anywhere}.syn-sc .tl,.syn-sc .mv{font-size:14px;margin:0 0 8px;overflow-wrap:anywhere}'
         '.syn-sc a.bk{display:inline-block;min-height:44px;line-height:44px;padding:0 14px;margin:0 0 8px -14px;color:#714b67;cursor:pointer}'
         '.syn-sc .cd{background:#fff;border:1px solid #e4e7eb;border-radius:10px;padding:14px 16px;margin:0 0 14px}'
         '.syn-sc .kv{display:flex;justify-content:space-between;gap:12px;font-size:13px;padding:6px 0;border-top:1px solid #f0f2f5}'
         '.syn-sc .kv span:first-child{color:#7b8794;min-width:30%}.syn-sc .kv span:last-child{text-align:right;overflow-wrap:anywhere}'
         '.syn-sc .tg{display:inline-block;font-size:12px;padding:1px 8px;border-radius:6px;background:#f0f4ff;color:#3e4c59;margin-right:4px}'
         '.syn-sc .hold{background:#fff4e5;color:#7a4b00}.syn-sc .req{background:#e6f4ea;color:#14532d}'
         '.syn-sc ul{margin:4px 0;padding-left:18px}.syn-sc .kv ul{margin:0;text-align:left}.syn-sc li{overflow-wrap:anywhere}.syn-sc .nt{font-size:12px;color:#7b8794;margin-top:14px}'
         '.syn-sc table.tt{width:100%;border-collapse:collapse;font-size:13px;table-layout:fixed}.syn-sc .tt th,.syn-sc .tt td{text-align:left;vertical-align:top;padding:6px 8px;border-top:1px solid #f0f2f5;overflow-wrap:anywhere}'
         '.syn-sc .tt td>div{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.syn-sc .tt details>div{white-space:normal}'
         '.syn-sc details summary{cursor:pointer;color:#714b67;font-size:12px}'
         '.syn-sc .cp{max-width:44rem}.syn-sc .cp .kv{justify-content:flex-start;flex-wrap:wrap;gap:4px 14px}'
         '.syn-sc .cp .kv span:first-child{flex:0 0 12rem;min-width:0}.syn-sc .cp .kv span:last-child{flex:1 1 12rem;text-align:left}'
         '@media (max-width:600px){.syn-sc .kv{flex-direction:column;gap:2px}.syn-sc .kv span:last-child{text-align:left}.syn-sc .tt th:nth-child(3),.syn-sc .tt td:nth-child(3){display:none}'
         '.syn-sc .cp .kv{gap:2px}.syn-sc .cp .kv span:first-child,.syn-sc .cp .kv span:last-child{flex:0 1 auto}}</style>')

BACK = '<a class="bk" data-lv="1" data-g="">&larr; Lenses</a>'
DEPTH_NOTE = {'enable': 'Enable: what this is, and what to do next. Switch Depth to Enhance for what it is made of and connects to, Enrich for trust and what is open.',
              'enhance': 'Enhance: what it is made of, and what it connects to.',
              'enrich': 'Enrich: why to trust it, and what is still open.'}
LABEL = {'enable': 'Enable', 'enhance': 'Enhance', 'enrich': 'Enrich'}
NO_ROLES = 'No roles are declared for this screen.'


def _t(v):
    return _e(str(v)) if v not in (None, '', [], ()) else 'UNSOURCED'


def _kv(k, v):
    return '<div class="kv"><span>%s</span><span>%s</span></div>' % (_e(str(k)), v)


def _pill(text, cls=''):
    return '<span class="tg%s">%s</span>' % ((' ' + cls) if cls else '', _e(str(text)))


def _plural(n, word):
    return '%d %s' % (n, word if n == 1 else word + 's')


def _chip_text(c):
    return ('%s %s' % (c['name'], c['date'])) if c.get('date') else c['name']


# ------------------------------------------------------------------------------------------------ frame slots
def _slot_header(m):
    h = m['frame']['header']
    title = h['noun'] if not h.get('record_name') else '%s: %s' % (h['noun'], h['record_name'])
    if m['screen_type'] == 'noun':
        stage = 'Stage: none (a noun screen has no stage)'
    elif m['screen_type'] == 'menu':
        stage = 'Stage: none (a menu screen has no stage)'
    elif m['stage'] == 'not bound':
        stage = 'Stage: not bound'
    else:
        stage = 'Stage: %s' % LABEL[m['stage']]
    s = '<div data-slot="header"><h1>%s %s</h1>' % (_e(title), _pill(h.get('status') or 'UNSOURCED'))
    s += '<p class="lb"><span data-label="stage">%s</span><span data-label="depth">Depth: %s</span>' % (_e(stage), _e(LABEL[m['depth_effective']]))
    if h.get('neighbour_kind'):
        s += '<span data-label="neighbour">Neighbour: its Context is kind %s (shown, never used for stage)</span>' % _e(str(h['neighbour_kind']))
    s += '</p>'
    if m['screen_type'] == 'record' and m['stage'] == 'not bound':
        s += '<p class="sb" data-slot-note="stage">Stage not bound: %s.</p>' % _e(str(m.get('stage_reason') or 'kind not bound'))
    return s + '</div>'


def _slot_answer(m):
    lead = m['frame'].get('answer_lead')
    lead_html = ('<strong class="lead">%s:</strong> ' % _e(str(lead))) if lead else ''
    return '<p class="an" data-slot="answer">%s%s</p>' % (lead_html, _t(m['frame']['answer']))


def _slot_trust(m):
    t = m['frame']['trust']
    return '<p class="tl" data-slot="trust">%s %s</p>' % (_pill(t['status'] or 'UNSOURCED'), _e(_plural(t['source_count'], 'source')))


def _slot_movement(m):
    mv = m['frame']['movement']
    if mv['state'] == 'HOLD':
        return '<p class="mv" data-slot="movement">%s %s. Reason: %s.</p>' % (_pill('HOLD', 'hold'), _e(mv['text']), _e(mv['reason']))
    return '<p class="mv" data-slot="movement">%s</p>' % _e('Next: ' + mv['verbs'][0])


# ---------------------------------------------------------------------------------------------- enhance slots
def _menu_items(mo):
    rows = ''
    for it in mo['items']:
        note = (' ' + _e(it['note'])) if it.get('note') else ''
        rows += '<div class="kv"><span>%s%s</span><span>%s %s</span></div>' % (_pill(it['status']), note, _e(it['text']), _pill(_chip_text(it['chip'])))
    body = '<div class="cd cp">%s</div>' % rows if rows else ''
    if mo.get('note'):
        body += '<p class="sb">%s</p>' % _e(mo['note'])
    return body


def _slot_made_of(m):
    mo = m['enhance']['made_of']
    if mo and mo.get('items') is not None:
        return '<div data-slot="made_of"><h2>%s</h2>%s</div>' % (_e(mo.get('heading') or 'Made of'), _menu_items(mo))
    if not mo:
        return '<div data-slot="made_of"><h2>Made of</h2><p class="sb">%s</p></div>' % _e(NO_ROLES)
    if not mo['rows']:
        body = '<p class="sb">No roles returned.</p>'
    else:
        rows = ''
        for r in mo['rows']:
            req = _pill('required', 'req') if r['required'] else _pill('optional')
            many = _pill('one or more') if r['many'] else ''
            rows += _kv(r['name'], '%s%s%s %s' % (req, many, _e(str(r['bound_label'])), _pill(r['bound_status'] or 'UNSOURCED')))
        body = '<div class="cd cp">%s</div>' % rows
    return '<div data-slot="made_of"><h2>%s</h2>%s</div>' % (_e(mo['heading']), body)


def _peer_state(p):
    if p.get('operating_source') == 'SOURCED':
        return '%s existence only, not operation' % _pill('CATALOGUE RECORD FOUND', 'req')
    return _pill('NO OPERATING SOURCE: HOLD', 'hold')


def _slot_peers(m):
    pe = m['enhance'].get('peers')
    if not pe:
        return '<div data-slot="peers"><h2>Linked peers</h2><p class="sb">No linked peers are declared for this screen.</p></div>'
    rows = ''
    for p in pe['rows']:
        more = '<details><summary>what it is</summary><div>%s</div></details>' % _t(p.get('definition'))
        rows += _kv(p['label'], '%s %s %s' % (_pill(p['status'] or 'UNSOURCED'), _peer_state(p), more))
    return '<div data-slot="peers"><h2>%s</h2><div class="cd cp">%s</div></div>' % (_e(pe['heading']), rows)


# ----------------------------------------------------------------------------------------------- enrich slots
def _chips_cell(r):
    shown, rest = r['chips'][:3], r['chips'][3:]
    if not r['chips']:
        line = 'None recorded'
    else:
        line = ' '.join(_pill(_chip_text(c)) for c in shown)
        if rest:
            line += _e(' +%d' % len(rest))
    full = ''
    if r.get('evidence') or r.get('full_citation') or r['chips']:
        items = ''.join('<li>%s</li>' % _e(_chip_text(c)) for c in r['chips'])
        ev = ''.join('<li>Evidence: %s</li>' % _e(str(e.get('label') or e.get('source_ref'))) for e in r.get('evidence') or [])
        fc = ('<p class="sb">%s: %s</p>' % (_e(r.get('citation_label') or 'Definition source'), _e(str(r['full_citation'])))) if r.get('full_citation') else ''
        full = '<details><summary>full citation</summary><div><ul>%s%s</ul>%s</div></details>' % (items, ev, fc)
    return '<div>%s</div>%s' % (line, full)


def _status_cell(r):
    """One line: status pill, then the one-line qualifier. Anything longer is behind a disclosure."""
    cls = 'hold' if r['status'] == 'HOLD' else ('req' if r['status'] == 'CATALOGUE RECORD FOUND' else '')
    line = _pill(r['status'] or 'UNSOURCED', cls)
    q = r.get('qualifier')
    if q and q.get('first'):
        line += ' ' + _e(str(q['first']))
    if r.get('rejected'):
        line += ' ' + _e('Rejected evidence: ' + ', '.join(r['rejected']))
    s = '<div>%s</div>' % line
    if q and q.get('first'):
        full = q.get('full')
        if isinstance(full, list) and len(full) > 1:
            s += '<details><summary>%s</summary><div><ul>%s</ul></div></details>' % (
                _e('+%d more' % (len(full) - 1)), ''.join('<li>%s</li>' % _e(str(x)) for x in full[1:]))
        elif isinstance(full, str) and full != str(q['first'])[len('Kind: '):]:
            s += '<details><summary>full kind</summary><div>%s</div></details>' % _e(full)
    return s


def _open_cell(r):
    n = len(r['open'])
    if not n:
        return '<div>none recorded</div>'
    first = r['open'][0]
    stem = _e(first['stem'] + '…') + ' ' if first['truncated'] else ''
    return '<div>%s%s</div>' % (stem, _e('(%d open)' % n))


def _slot_trust_table(m):
    def claim_cell(r):  # one line; a long claim (a document quotation) keeps its full text behind a disclosure
        more = '<details><summary>full text</summary><div>%s</div></details>' % _e(r['label']) if len(r['label']) > 60 else ''
        return '<div>%s</div>%s' % (_e(r['label']), more)
    rows = ''.join('<tr data-claim="%s"><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (
        _e(r['id']), claim_cell(r), _status_cell(r), _chips_cell(r), _open_cell(r)) for r in m['enrich']['rows'])
    return ('<div data-slot="trust_table"><h2>Why to trust it</h2><div class="cd"><table class="tt"><thead><tr><th>Claim</th><th>Status</th>'
            '<th>Source</th><th>Open question</th></tr></thead><tbody>%s</tbody></table></div></div>' % rows)


def _slot_open_questions(m):
    items = ''
    for r in m['enrich']['rows']:
        if r['open']:
            items += '<li>%s (%s)<ul>%s</ul></li>' % (_e(r['label']), _e('%d open' % len(r['open'])),
                                                      ''.join('<li>%s</li>' % _e(q['text']) for q in r['open']))
    body = '<ul>%s</ul>' % items if items else '<p class="sb">none recorded</p>'
    return '<div data-slot="open_questions"><h2>What is still open</h2><div class="cd">%s</div></div>' % body


def _slot_technical(m):
    t = m['enrich']['technical']
    td = ''
    if m.get('registry_version'):
        td += _kv('Registry', _e('%s, %s, fingerprint %s' % (m.get('registry_version', ''), m.get('registry_state', ''), str(m.get('registry_sha', ''))[:12])))
    for d in t.get('doc_sources') or []:
        td += _kv('Source row', _e('%s, %s, %s' % (d['row'], d['file'], d['when'])))
    if m.get('sources_sha'):
        td += _kv('Source table', _e('fingerprint %s' % str(m['sources_sha'])[:12]))
    if t.get('relationship') and t.get('cluster_id'):
        td += _kv('Roles come from', _e('relationship %s, cluster %s' % (t['relationship'], t['cluster_id'])))
    for e in t.get('evidence_sources') or []:
        td += _kv('Evidence source', _e('%s, fingerprint %s' % (e.get('source_ref', ''), str(e.get('sha256', ''))[:12])))
    td += _kv('Screen declaration', _e('%s, fingerprint %s' % (t.get('screen_id', ''), str(m.get('declaration_sha', ''))[:12])))
    if t.get('kind'):
        td += _kv('Bound kind', _e(str(t['kind'])))
    return '<details class="td" data-slot="technical"><summary>Technical details</summary><div class="cd">%s</div></details>' % td


SLOT_BUILDERS = {
    'header': _slot_header, 'answer': _slot_answer, 'trust': _slot_trust, 'movement': _slot_movement,
    'made_of': _slot_made_of, 'peers': _slot_peers,
    'trust_table': _slot_trust_table, 'open_questions': _slot_open_questions, 'technical': _slot_technical,
}


def render_unavailable(out, title='Screen'):
    why = (out or {}).get('reason', 'UNKNOWN') if isinstance(out, dict) else 'UNKNOWN'
    return STYLE + '<div class="syn-sc">%s<h1>%s</h1><p class="sb">Not available: %s.</p></div>' % (BACK, _e(title), _e(str(why)))


def render_screen(m):
    """One renderer for every screen. Slots are built in the order the model lists them (frame first, then each depth)."""
    if not isinstance(m, dict) or m.get('result') != 'OK' or 'slots' not in m:
        return render_unavailable(m)
    eff = m['depth_effective']
    h = STYLE + '<div class="syn-sc" data-screen="%s" data-screen-type="%s" data-depth="%s">' % (_e(m['screen']), _e(m['screen_type']), _e(eff)) + BACK
    for slot in m['slots']:
        h += SLOT_BUILDERS[slot](m)
    na = m.get('not_applicable')
    if na:
        h += '<div class="cd" data-slot="not_applicable">%s: %s (%s).</div>' % (_e(LABEL[na['requested']]), _e(na['text']), _e(na['reason']))
    note = DEPTH_NOTE.get(eff, '')
    if m.get('depth_clamped') and m.get('clamp_reason') == 'role':
        note += ' (Your role limits the depth to %s.)' % LABEL[eff]
    reg = (' Registry %s, %s.' % (_e(str(m.get('registry_version', ''))), _e(str(m.get('registry_state', ''))))) if m.get('registry_version') else ''
    h += '<p class="nt">%s%s Presentation only: this view changes no data, kind, PPV, approval or right.</p></div>' % (_e(note), reg)
    return h
