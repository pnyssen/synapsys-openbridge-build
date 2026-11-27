from odoo import http
from odoo.http import request
from odoo.addons.synapsys import lens_render as lr, lens_contract as lc


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
        return html
