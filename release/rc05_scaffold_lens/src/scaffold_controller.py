from odoo import http
from odoo.http import request
from odoo.addons.synapsys import scaffold_wire as sw, scaffold_view as sv


class SynapsysScaffold(http.Controller):
    """Read-only. Uses the caller's own environment: no sudo, no writes."""

    @http.route('/synapsys/scaffold/context', type='jsonrpc', auth='user')
    def scaffold_context(self, depth='enable', context_id=''):
        return sw.scaffold_context(request.env, depth, context_id)

    @http.route('/synapsys/scaffold/view', type='jsonrpc', auth='user')
    def scaffold_view(self, depth='enable', context_id=''):
        return sv.render(sw.scaffold_context(request.env, depth, context_id), depth)
