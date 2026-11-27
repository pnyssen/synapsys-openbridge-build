from odoo import http
from odoo.http import request
from odoo.addons.synapsys import scaffold_wire as sw


class SynapsysMenuBinding(http.Controller):
    """Read-only (RC06g). Uses the caller's own environment: no sudo, no writes. A refusal is a reason code and nothing else."""

    @http.route('/synapsys/menu/enable', type='jsonrpc', auth='user')
    def menu_enable(self, action_id=None, menu_id=None, screen_id='', depth='enable'):
        return sw.menu_enable(request.env, action_id, menu_id, screen_id, depth)
