import re
from markupsafe import escape
from odoo import http
from odoo.http import request
from odoo.addons.synapsys.models.work import BUILD_FROM_V19, DRAFTS

GROUP_TEXT = {
    'live': ('Live', 'How people and partners live and work well together'),
    'build': ('Build', 'How we create and capture value'),
    'adapt': ('Adapt', 'How we renew, focus and protect what matters'),
}
KINDS = [('K-1', 'Purpose', 'why we exist'), ('K-3', 'Strategy', 'where we choose to go'),
         ('K-4', 'Asset', 'what lasts and keeps paying back'), ('K-6', 'Offering', 'what we provide'),
         ('K-8', 'Collaboration', 'who we work with'), ('K-12', 'Platform', 'what it all runs on')]


def _purpose(code, texts):
    """The domain's own stated purpose, read from its rulebook(s) in the library (never invented)."""
    for text in texts:
        for m in re.finditer(r'^\**Purpose\.\**\s*(.+)$', text or '', re.M):
            line = m.group(1).strip()
            if not line.lower().startswith(('purpose, holds', 'unchanged')):
                return line.split('. ')[0].rstrip('.') + '.'
        m = re.search(r'^## %s [^:\n]*:\s*([^\n]+)\n- (.+)$' % re.escape(code), text or '', re.M)
        if m:
            first = m.group(2).split('. ')[0].rstrip('.')
            return '%s: %s.' % (m.group(1).strip().capitalize(), first[0].lower() + first[1:])
    return ''


class SynapsysHome(http.Controller):

    @http.route('/synapsys/home/data', type='jsonrpc', auth='user')
    def home_data(self):
        env = request.env
        e = escape
        doms = env['synapsys.domain'].search([], order='code')
        Verb = env['synapsys.verb']
        Canon = env['synapsys.canon']

        def count(model, dom=()):
            try:
                return env[model].search_count(list(dom))
            except Exception:
                return None

        strategies = [(n, 'build', title, reg) for (n, title, reg) in BUILD_FROM_V19.values()]
        strategies += [(n, grp, title, reg) for (_c, n, grp, title, _d, reg) in DRAFTS]
        cols = []
        for grp in ('live', 'build', 'adapt'):
            label, sub = GROUP_TEXT[grp]
            cards = ''
            for n, g, title, reg in sorted(strategies):
                if g != grp:
                    continue
                verbs = ', '.join(Verb.search([('strategy', '=', reg)], order='sequence').mapped('name'))
                cards += '<div class="ss-strat"><b>%s</b><span>%s</span></div>' % (e(title), e(verbs))
            cols.append('<div class="ss-col"><h3>%s</h3><p class="ss-sub">%s</p>%s</div>' % (e(label), e(sub), cards))

        dcards = ''
        for d in doms:
            text = d.seat_instruction_text if 'seat_instruction_text' in d._fields else ''
            rows = Canon.search([('kind', '=', 'instruction'), '|', ('domain_id', '=', d.id), ('shared', '=', True)],
                                order='shared, id desc')
            has = bool(text)
            p = _purpose(d.code, rows.mapped('body')) or ('Purpose not stated in its rulebook.' if has else 'No rulebook yet.')
            dcards += ('<a class="ss-dom" href="/odoo/action-synapsys.action_governance/%d">'
                       '<div class="ss-code">%s</div><div class="ss-name">%s</div><div class="ss-purpose">%s</div>'
                       '<div class="ss-flag %s">%s</div></a>') % (
                d.id, e(d.code), e(d.name), e(p), 'ok' if has else 'no', 'Rulebook in place' if has else 'No rulebook yet')

        kinds = ''.join('<div class="ss-kind"><b>%s</b> %s<span>%s</span></div>' % (e(k), e(n), e(w)) for k, n, w in KINDS)

        n_rules = count('synapsys.canon', [('kind', '=', 'instruction')])
        n_chart = count('synapsys.canon', [('kind', '=', 'charter')])
        n_canon = count('synapsys.canon')
        n_wait = count('synapsys.signal', [('state', '=', 'new')])
        n_work = count('synapsys.work.object', [('status', 'in', ('open', 'at_gate', 'held'))])
        n_ctx = count('synapsys.context')
        n_verbs = Verb.search_count([])

        def num(v):
            return '–' if v is None else str(v)

        waiting = ('Nothing is waiting for you.' if not (n_wait or n_work) else
                   '%s new item(s) in your Inbox and %s piece(s) of work in progress.' % (num(n_wait), num(n_work)))

        return """
<div class="ss-home">
<style>
.ss-home{font-family:inherit;color:#1f2933;max-width:1180px;margin:0 auto;padding:28px 32px 60px}
.ss-home h1{font-size:30px;margin:0 0 6px;font-weight:600}
.ss-home h2{font-size:19px;margin:34px 0 4px;font-weight:600}
.ss-home .ss-lead{font-size:16px;color:#52606d;margin:0 0 4px;max-width:820px}
.ss-sub{color:#7b8794;font-size:13px;margin:0 0 10px}
.ss-wait{background:#f0f4ff;border-left:4px solid #714b67;padding:14px 18px;border-radius:6px;margin-top:22px;font-size:15px}
.ss-stats{display:flex;gap:14px;flex-wrap:wrap;margin-top:16px}
.ss-stat{background:#fff;border:1px solid #e4e7eb;border-radius:8px;padding:12px 16px;min-width:130px}
.ss-stat b{display:block;font-size:24px;color:#714b67}.ss-stat span{font-size:13px;color:#52606d}
.ss-cols{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
.ss-col{background:#fff;border:1px solid #e4e7eb;border-radius:10px;padding:14px 16px}
.ss-col h3{margin:0;font-size:17px;color:#714b67}
.ss-strat{padding:9px 0;border-top:1px solid #f0f2f5}.ss-strat b{display:block;font-size:14px}
.ss-strat span{font-size:12px;color:#7b8794}
.ss-doms{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:14px}
.ss-dom{display:block;background:#fff;border:1px solid #e4e7eb;border-radius:10px;padding:14px 16px;color:inherit;text-decoration:none}
.ss-dom:hover{border-color:#714b67;box-shadow:0 2px 8px rgba(0,0,0,.06)}
.ss-code{font-size:12px;color:#7b8794}.ss-name{font-size:16px;font-weight:600;margin:2px 0 6px}
.ss-purpose{font-size:13px;color:#3e4c59;min-height:36px}
.ss-flag{font-size:12px;margin-top:8px}.ss-flag.ok{color:#2f855a}.ss-flag.no{color:#b7791f}
.ss-kinds{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.ss-kind{background:#fff;border:1px solid #e4e7eb;border-radius:8px;padding:10px 14px;font-size:14px}
.ss-kind span{display:block;color:#7b8794;font-size:12px}
</style>
<h1>SynapSys</h1>
<p class="ss-lead">How SynapSys turns purpose into lasting value: nine strategies set the direction, twelve domains each look after one part of the business by their own rulebook, and every piece of work is checked against those rulebooks before it moves.</p>
<div class="ss-wait">%(waiting)s</div>
<div class="ss-stats">
 <div class="ss-stat"><b>9</b><span>strategies</span></div>
 <div class="ss-stat"><b>%(ndom)s</b><span>domains</span></div>
 <div class="ss-stat"><b>%(nrules)s</b><span>domain rulebooks</span></div>
 <div class="ss-stat"><b>%(nverbs)s</b><span>actions (verbs)</span></div>
 <div class="ss-stat"><b>%(ncanon)s</b><span>library documents</span></div>
 <div class="ss-stat"><b>%(nctx)s</b><span>contexts</span></div>
</div>
<h2>Direction: nine strategies</h2>
<p class="ss-sub">Three groups of three. Under each strategy, the three actions it uses.</p>
<div class="ss-cols">%(cols)s</div>
<h2>Who looks after what: twelve domains</h2>
<p class="ss-sub">Each domain has its own rulebook. Open one to read it.</p>
<div class="ss-doms">%(dcards)s</div>
<h2>Six kinds of context</h2>
<p class="ss-sub">Every piece of work belongs to one, from purpose down to the platform.</p>
<div class="ss-kinds">%(kinds)s</div>
</div>""" % dict(waiting=e(waiting), ndom=len(doms), nrules=num(n_rules), nverbs=n_verbs, ncanon=num(n_canon),
                 nctx=num(n_ctx), cols=''.join(cols), dcards=dcards, kinds=kinds)
