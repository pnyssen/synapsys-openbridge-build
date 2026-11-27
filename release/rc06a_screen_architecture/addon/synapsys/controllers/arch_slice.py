"""Read-only Context -> Strategy -> Service slice endpoint (source-only candidate; not installed).

Runs under the CALLER'S OWN environment: no sudo(), no with_user(), no write, no new model, no menu. Odoo's ACL and record rules
decide visibility, so a role that cannot read a model receives RESTRICTED for it and nothing else. The Master menu is NOT added here
(it needs its own release). Resolver and honesty rules live in arch_slice.py / arch_graph.py.
"""
from odoo import http
from odoo.exceptions import AccessError
from odoo.http import request

from .. import arch_slice


class ArchitectureSlice(http.Controller):

    @http.route('/synapsys/architecture/slice', type='jsonrpc', auth='user', methods=['POST'])
    def slice(self, context_id=None):
        if context_id is not None and not (isinstance(context_id, int) and not isinstance(context_id, bool)):
            return {'error': 'context_id must be an integer', 'writes': 0}
        graph, actor, notes = arch_slice.collect(request.env, AccessError)
        return arch_slice.build_slice(graph, actor, notes, context_id)
