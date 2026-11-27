import re

from odoo import http
from odoo.http import request
from odoo.addons.synapsys import lens_render as lr, lens_contract as lc


# D16 ruling (Steward, 27 Nov 2026): the level line states position only, with no stage word, because Depth applies to element views.
_CRUMB = re.compile(r'(<div class="cr">(?:(?!</div>).)*?)(?:, (?:Enable|Enhance)| / Enrich)</div>')
_LIST_NOTE = '<p class="nt">Depth applies when you open a lens or element.</p>'


class SynapsysLenses(http.Controller):

    @http.route('/synapsys/lenses/data', type='jsonrpc', auth='user')
    def lenses_data(self, level=1, group='', sec='', mode='enable', ov=''):
        env = request.env
        live = env['synapsys.mesh.entry'].search_count([('cls', '=', 'L')])
        verbs = {}
        for stage, groups in lr.STAGES.items():
            for g in groups:
                verbs[g] = env['synapsys.verb'].search([('action', '=', g)], order='sequence').mapped('name')
        html = lr.render(int(level or 1), group, sec, live, verbs)
        if int(level or 1) == 3:
            ovs = lc.parse_overrides(ov)
            html += '<div class="lv">%s</div>' % ''.join(lc.render_element(lc.from_lens(l), mode, ovs) for l in lr.lenses_for(group, sec))
        lv = int(level or 1)
        html = _CRUMB.sub(r'\1</div>', html)
        extra = _LIST_NOTE if lv in (1, 2) else ''
        if lv == 1 and env.user.has_group('synapsys.group_synapsys_steward'):
            extra += ('<div style="margin-top:14px"><a class="cd" data-scaffold="1">'
                      '<h3>Context scaffold (read-only)</h3>'
                      '<div class="sb">Context, its roles, and the linked Capability and Service, with their evidence state.</div></a></div>')
        if extra:
            if html.endswith('</div>'):
                html = html[:-len('</div>')] + extra + '</div>'
            else:
                html += '<div class="lv">' + extra + '</div>'
        return html
