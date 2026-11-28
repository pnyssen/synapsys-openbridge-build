"""Read-only Master Architecture endpoint (source-only candidate; NOT installed, no menu).

Runs under the CALLER'S OWN environment: no sudo(), no with_user(), no write, no new model, no menu. Odoo's ACL and record rules decide
what is visible, so a role that cannot read a model receives RESTRICTED for it and nothing else. A Master menu needs its own release.
Definition, projection, FFE, verb eligibility and honesty rules live in arch_master.py / arch_graph.py.
"""
from odoo import http
from odoo.exceptions import AccessError
from odoo.http import request

from .. import arch_graph, arch_master, arch_master_ctx, arch_master_drill, arch_master_views, arch_slice, master_render, scaffold_view, scaffold_wire


class ArchitectureMaster(http.Controller):

    @http.route('/synapsys/architecture/master', type='jsonrpc', auth='user', methods=['POST'])
    def master(self, perspective='Form', depth='enable', context_id=None):
        if perspective not in arch_graph.PERSPECTIVES:
            return {'error': 'perspective must be one of %s' % ', '.join(arch_graph.PERSPECTIVES), 'writes': 0}
        if depth not in arch_master.DEPTHS:
            return {'error': 'depth must be one of %s' % ', '.join(arch_master.DEPTHS), 'writes': 0}
        if context_id is not None and not (isinstance(context_id, int) and not isinstance(context_id, bool)):
            return {'error': 'context_id must be an integer', 'writes': 0}
        defn = arch_master.load_definition()
        if defn is None:
            return {'state': 'DEFINITION_NOT_LOADED', 'writes': 0}
        graph, actor, notes = arch_master.collect(request.env, AccessError, defn)
        return arch_master.build_master(defn, graph, actor, notes, perspective, depth, context_id)

    @http.route('/synapsys/architecture/master/page', type='jsonrpc', auth='user', methods=['POST'])
    def page(self, section='overview', perspective='Form', depth='enable', actor='steward', context_id=None, drill='app', ov=''):
        """ONE navigation state rendered as escaped HTML for the (unreleased) client action. Same engine, same rights as /master."""
        if section not in arch_master_views.SECTIONS:
            return {'error': 'unknown section', 'writes': 0}
        if perspective not in arch_graph.PERSPECTIVES:
            return {'error': 'unknown perspective', 'writes': 0}
        if depth not in arch_master.DEPTHS:
            return {'error': 'unknown depth', 'writes': 0}
        if actor not in arch_master_views.ACTORS:
            return {'error': 'unknown actor perspective', 'writes': 0}
        if context_id is not None and not (isinstance(context_id, int) and not isinstance(context_id, bool)):
            return {'error': 'context_id must be an integer', 'writes': 0}
        if not isinstance(drill, str) or not isinstance(ov, str) or len(ov) > 4000:
            return {'error': 'unknown drill path', 'writes': 0}
        defn = arch_master.load_definition()
        if defn is None:
            return {'state': 'DEFINITION_NOT_LOADED', 'writes': 0}
        user = request.env.user
        role = 'steward' if user.has_group('synapsys.group_synapsys_steward') else 'collaborator' if user.has_group('synapsys.group_synapsys_user') else 'other'
        from odoo.addons.synapsys.models.work import BUILD_FROM_V19, DRAFTS
        groups = {code: 'build' for code in BUILD_FROM_V19}
        groups.update({code: grp for (code, _n, grp, _t, _d, _r) in DRAFTS})
        graph, actor_rights, notes = arch_master.collect(request.env, AccessError, defn)
        ctx = arch_master_ctx.build_ctx(request.env, defn, AccessError, scaffold_wire, scaffold_view) if section == 'drill' else None
        data = arch_master_views.assemble(defn, graph, actor_rights, notes, role, section, perspective, depth, actor, groups, context_id, arch_slice.acceptance_view(),
                                          arch_master.load_roles(), drill, ctx, ov)
        return {'html': master_render.render_page(data), 'writes': 0, 'role': role}
