"""The one screen renderer (RC06a, source-only candidate).

Builds the fixed frame (header, answer, trust line, movement) and the depth sections from a screen model produced by
screen_decl.project. There is no per-screen rendering code: every slot is built by one generic function, in declared order.
Pure: every dynamic value is escaped; no scripts, no inline event handlers, no external URLs. Presentation only: it changes no
data, kind, PPV, approval or right.
"""
import re
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
         '.syn-sc .tt td:first-child>div{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.syn-sc .tt td:not(:first-child)>div{white-space:normal;overflow-wrap:anywhere}.syn-sc .tt details>div{white-space:normal}'
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


def strip_status_prefix(answer, status):
    """R6 (RC06h): an answer that opens with its own status word and a colon drops that prefix; the chip already carries the status."""
    a = str(answer or '')
    if status:
        m = re.match(r'\s*' + re.escape(str(status)) + r'\s*:\s*', a, re.I)
        if m and a[m.end():]:
            return a[m.end():]
    return answer


def _slot_answer(m, lead=True):
    lead = m['frame'].get('answer_lead') if lead else None
    lead_html = ('<strong class="lead">%s:</strong> ' % _e(str(lead))) if lead else ''
    return '<p class="an" data-slot="answer">%s%s</p>' % (lead_html, _t(strip_status_prefix(m['frame']['answer'], m['frame']['header'].get('status'))))


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


def render_enable_panel(m, binding_status=None):
    """Read-only Enable panel for a menu's native view (RC06g): the four frame slots of the screen model (header, answer, trust line, movement)
    and nothing else, with the status of the binding as the Navigator's spec states it. No back link, no depth sections, no script."""
    if not isinstance(m, dict) or m.get('result') != 'OK' or 'frame' not in m:
        return ''
    h = STYLE + '<div class="syn-sc syn-pn" data-panel="enable" data-screen="%s">' % _e(str(m.get('screen', '')))
    for slot in ('header', 'answer', 'trust', 'movement'):
        h += SLOT_BUILDERS[slot](m)
    if binding_status:
        h += '<p class="nt" data-slot="binding">Binding: %s</p>' % _e(str(binding_status))
    return h + '<p class="nt">Presentation only: this view changes no data, kind, PPV, approval or right.</p></div>'



# --- RC06i: menu pages (all) and the Service 1-3-1 projection -------------------------------------------------------------------------------------
# Placement (probe on dev, RC06g installed): body.o_web_client is a viewport-height flex column: navbar, .o_action_manager (flexible, overflow hidden), then
# .o-main-components-container, which holds the panel. While a page is on screen the container is ordered above the action manager and the whole
# web client grows to its content, so the page scrolls as ONE page (no scroll container inside the panel) and the native view keeps a full-height area
# below the Records heading instead of being squeezed. All rules exist only while a page is on screen (:has(.syn-pg)); the style block travels with the html.
PAGE_STYLE = (
    '<style>'
    '.o_web_client:has(.syn-pg){height:auto;min-height:100vh;overflow-y:auto}'
    '.o_web_client:has(.syn-pg)>.o-main-components-container,.o_web_client:has(.syn-pg)>.syn-enable-panel{order:1;flex:0 0 auto}'
    '.o_web_client:has(.syn-pg)>.o_action_manager{order:2;flex:0 0 auto;height:calc(100vh - 46px);min-height:24rem}'
    '.syn-sc.syn-pg{padding-bottom:0}.syn-pg .syn-records{margin:10px 0 0;padding-top:8px;padding-bottom:6px;border-top:1px solid #e4e7eb}'
    # R5: wrap, never clip, on every menu page; at 600 px and below the trust table becomes stacked rows that keep Source
    '.syn-sc.syn-pg table.tt td>div{white-space:normal;overflow:visible;text-overflow:clip;overflow-wrap:anywhere}'
    '.syn-sc.syn-pg summary{display:flex;align-items:center;min-height:44px}'
    '@media (max-width:600px){.syn-sc.syn-pg table.tt{table-layout:auto}.syn-sc.syn-pg .tt thead{display:none}'
    '.syn-sc.syn-pg .tt,.syn-sc.syn-pg .tt tbody,.syn-sc.syn-pg .tt tr,.syn-sc.syn-pg .tt td{display:block;width:100%}'
    '.syn-sc.syn-pg .tt tr{border-top:1px solid #e4e7eb;padding:6px 0}.syn-sc.syn-pg .tt td,.syn-sc.syn-pg .tt td:nth-child(3){display:block;border-top:0;padding:2px 8px}'
    '.syn-sc.syn-pg .tt td::before{display:block;color:#7b8794;font-size:10px}'
    '.syn-sc.syn-pg .tt td:nth-child(1)::before{content:"Claim"}.syn-sc.syn-pg .tt td:nth-child(2)::before{content:"Status"}'
    '.syn-sc.syn-pg .tt td:nth-child(3)::before{content:"Source"}.syn-sc.syn-pg .tt td:nth-child(4)::before{content:"Open question"}}'
    # R1: the one Detail control (44 px targets, visible keyboard focus)
    '.syn-detail{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:10px 0 0}.syn-detail .syn-detail-l{color:#52606d;margin-right:4px}'
    '.syn-detail button{min-height:44px;min-width:44px;padding:0 14px;border:1px solid #9aa5b1;border-radius:6px;background:#fff;color:#1f2933;cursor:pointer;font:inherit}'
    '.syn-detail button[aria-pressed="true"]{background:#714b67;color:#fff;border-color:#714b67}'
    '.syn-detail button:focus-visible{outline:3px solid #1d4ed8;outline-offset:2px}'
    '</style>')

SERVICE_STYLE = (
    '<style>'
    # R4: the adopted 14 / 12 / 10 px hierarchy, Service projection only (every size set explicitly; nothing else in the page changes)
    '.syn-sc.syn-sv,.syn-sc.syn-sv h1,.syn-sc.syn-sv h2,.syn-sc.syn-sv .an,.syn-sc.syn-sv .tl,.syn-sc.syn-sv .mv,.syn-sc.syn-sv .sb,.syn-sc.syn-sv p,.syn-sc.syn-sv li{font-size:14px;line-height:1.45}'
    '.syn-sc.syn-sv h1,.syn-sc.syn-sv h2{font-weight:600;margin:0 0 4px}'
    '.syn-sc.syn-sv .tg,.syn-sc.syn-sv .lb,.syn-sc.syn-sv .kv,.syn-sc.syn-sv table.tt,.syn-sc.syn-sv .tt td,.syn-sc.syn-sv .tt th,.syn-sc.syn-sv summary,.syn-sc.syn-sv button,.syn-sc.syn-sv .syn-detail-l,.syn-sc.syn-sv .sv-chain li{font-size:12px}'
    '.syn-sc.syn-sv .tt td>div,.syn-sc.syn-sv .tt td div>*,.syn-sc.syn-sv .kv span,.syn-sc.syn-sv .kv li,.syn-sc.syn-sv .tt li,.syn-sc.syn-sv .cd p,.syn-sc.syn-sv .cd li{font-size:12px}'
    '.syn-sc.syn-sv .nt,.syn-sc.syn-sv .sv-cap,.syn-sc.syn-sv .tt td::before{font-size:10px}'
    '.syn-sv .sv-band,.syn-sv .sv-ap{border:1px solid #e4e7eb;border-radius:10px;padding:12px 14px;background:#fff}'
    '.syn-sv .sv-answer h1{display:inline;margin-right:8px}.syn-sv .sv-ap .cd{border:0;padding:0;margin:0}'
    '.syn-sv .sv-apertures{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:12px 0}'
    '.syn-sv .sv-apertures>.sv-ap[data-aperture="evolve"].sv-wide{grid-column:1/-1}'
    '.syn-sv .sv-ap p{margin:6px 0}.syn-sv .sv-cap{color:#7b8794;margin:0 0 4px}'
    '.syn-sv .sv-value{background:#f8fafc;border-color:#cbd2d9}.syn-sv .sv-chain{list-style:none;margin:6px 0;padding:0;display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:8px}'
    '.syn-sv .sv-chain li{border:1px dashed #9aa5b1;border-radius:8px;padding:6px 8px;overflow-wrap:anywhere}'
    '@media (max-width:700px){.syn-sv .sv-apertures{grid-template-columns:minmax(0,1fr);gap:6px;margin:6px 0}.syn-sv .sv-band,.syn-sv .sv-ap{padding:8px 10px}'
    '.syn-sv .sv-chain{display:flex;flex-wrap:wrap;gap:6px}.syn-sv .sv-chain li{padding:4px 8px}.syn-sv .sv-ap p{margin:2px 0}.syn-sv .syn-detail{margin-top:6px}}'
    '</style>')

DEPTH_ORDER = ('enable', 'enhance', 'enrich')
SERVICE_SCREEN = 'SCR.SERVICE.NOUN'
MEASURES_SCREEN = 'SCR.MESH_MEASURES.MENU'
VALUE_CHAIN = ('Service performance', 'Outcome', 'Verified Benefit contribution', 'Realisation', 'Enduring Asset effect')  # v1.3 section 1


def detail_control(depth):
    """R1: the ONE depth control of a menu page, rendered here and nowhere else. Pressed state is the depth that was served; a click is handled by the
    client's single delegated handler and goes to the shared lens-mode service."""
    b = ''.join('<button type="button" data-mode="%s" aria-pressed="%s">%s</button>' % (d, 'true' if d == depth else 'false', LABEL[d]) for d in DEPTH_ORDER)
    return '<div class="syn-detail" role="group" aria-label="Detail level" data-control="detail"><span class="syn-detail-l">Detail</span>%s</div>' % b


def _page_open(m, extra_cls=''):
    return '<div class="syn-sc syn-pg%s" data-page="menu" data-screen="%s" data-screen-type="%s" data-depth="%s">' % (
        extra_cls, _e(str(m['screen'])), _e(str(m['screen_type'])), _e(m['depth_effective']))


def _page_foot(m, binding_status, compact=False):
    eff = m['depth_effective']
    note = '' if compact else DEPTH_NOTE.get(eff, '')  # the Service projection states depth in its own Detail control; the long how-to sentence is dropped there
    if m.get('depth_clamped') and m.get('clamp_reason') == 'role':
        note += ' (Your role limits the depth to %s.)' % LABEL[eff]
    if compact:
        b = ('Binding: %s. ' % _e(str(binding_status))) if binding_status else ''
        return '<p class="nt" data-slot="binding">%s%sPresentation only: this view changes no data, kind, PPV, approval or right.</p><h2 class="syn-records" data-slot="records">Records</h2></div>' % (b, _e(note.strip() + ' ' if note.strip() else ''))
    h = ''
    if binding_status:
        h += '<p class="nt" data-slot="binding">Binding: %s</p>' % _e(str(binding_status))
    h += '<p class="nt">%s Presentation only: this view changes no data, kind, PPV, approval or right.</p>' % _e(note)
    return h + '<h2 class="syn-records" data-slot="records">Records</h2></div>'


def _measures_scope(m):
    """R7: what this page does and does not know about Measures. No read, no count, no chart; the native list under Records is the only view of stored measures."""
    return ('<div class="cd" data-slot="measures_scope"><p>Observations: not available on this screen. No stored measure is read here; the native list under Records shows what exists.</p>'
            '<p>Owner: none declared on this screen.</p></div>')


def render_menu_page(m, binding_status=None):
    """A bound menu's page in the lens template. Service gets its 1-3-1 projection; every other menu page keeps the generic frame. In both, the page
    definition comes first, the Detail control is inside the answer area, and the Records heading closes the page above the untouched native view."""
    if not isinstance(m, dict) or m.get('result') != 'OK' or 'slots' not in m:
        return ''
    if m.get('screen') == SERVICE_SCREEN:
        return render_service_page(m, binding_status)
    eff = m['depth_effective']
    h = STYLE + PAGE_STYLE + _page_open(m)
    for slot in m['slots']:
        if slot == 'answer':
            h += _slot_answer(m, lead=False)  # the chip beside the title carries the status: no lead
            h += detail_control(eff)
        else:
            h += SLOT_BUILDERS[slot](m)
        if slot == 'movement' and m.get('screen') == MEASURES_SCREEN:
            h += _measures_scope(m)
    na = m.get('not_applicable')
    if na:
        h += '<div class="cd" data-slot="not_applicable">%s: %s (%s).</div>' % (_e(LABEL[na['requested']]), _e(na['text']), _e(na['reason']))
    return h + _page_foot(m, binding_status)


def _service_header(m):
    hd = m['frame']['header']
    return '<div data-slot="header"><h1>%s %s</h1></div>' % (_e(hd['noun']), _pill(hd.get('status') or 'UNSOURCED'))


def _form_line(m):
    ver = m.get('registry_version')
    if ver:
        return '<p class="sv-line" data-line="form">Definition source: registry %s, %s.</p>' % (_e(str(ver)), _e(str(m.get('registry_state') or 'state not given')))
    return '<p class="sv-line" data-line="form">No registry source is declared for this screen.</p>'


def _evolve_line(m):
    t = m['frame']['trust']
    return '<p class="sv-line" data-line="evolve">Trust: %s %s.</p>' % (_pill(t['status'] or 'UNSOURCED'), _e(_plural(t['source_count'], 'source')))


def render_service_page(m, binding_status=None):
    """RC06i: the Service page in the adopted 1-3-1 layout (Service Catalogue Master Reference v1.3 s1): one full-width Answer band, three operating
    apertures Form / Flow / Evolve, one always-visible Value band. Built only from the slots the projection already returns; nothing is inferred
    (Form / Flow / Evolve here group what is shown, they are not x_ffe_state). A slot with no source says so."""
    eff = m['depth_effective']
    ix = DEPTH_ORDER.index(eff)
    h = STYLE + PAGE_STYLE + SERVICE_STYLE + _page_open(m, ' syn-sv').replace('data-page="menu"', 'data-page="menu" data-projection="service-1-3-1"')
    h += '<section class="sv-band sv-answer" data-band="answer">' + _service_header(m) + _slot_answer(m, lead=False) + SLOT_BUILDERS['trust'](m) + detail_control(eff) + '</section>'
    wide = ' sv-wide' if ix == 2 else ''
    form = '<section class="sv-ap" data-aperture="form"><h2>Form</h2><p class="sv-cap">SynapSys: definition and alignment</p>' + _form_line(m)
    flow = '<section class="sv-ap" data-aperture="flow"><h2>Flow</h2><p class="sv-cap">Disciplines: operation and movement</p>' + SLOT_BUILDERS['movement'](m)
    evolve = '<section class="sv-ap%s" data-aperture="evolve"><h2>Evolve</h2><p class="sv-cap">Mesh: evidence, learning and value realisation</p>' % wide + _evolve_line(m)
    if ix >= 1:
        form += SLOT_BUILDERS['made_of'](m)
        flow += SLOT_BUILDERS['peers'](m)
    if ix >= 2:
        evolve += SLOT_BUILDERS['open_questions'](m) + SLOT_BUILDERS['trust_table'](m) + SLOT_BUILDERS['technical'](m)
    h += '<div class="sv-apertures" data-band="apertures">' + form + '</section>' + flow + '</section>' + evolve + '</section></div>'
    h += ('<section class="sv-band sv-value" data-band="value"><h2>Value</h2>'
          '<p class="sv-cap" data-slot="value_definition">Definition of the value chain, from the Service Catalogue Master Reference v1.3. It is not a record of this Service.</p>'
          '<ol class="sv-chain">%s</ol>'
          '<p data-slot="value_records">Benefits and Assets recorded against this Service are not read on this screen.</p></section>') % ''.join('<li>%s</li>' % _e(v) for v in VALUE_CHAIN)
    na = m.get('not_applicable')
    if na:
        h += '<div class="cd" data-slot="not_applicable">%s: %s (%s).</div>' % (_e(LABEL[na['requested']]), _e(na['text']), _e(na['reason']))
    return h + _page_foot(m, binding_status, compact=True)
