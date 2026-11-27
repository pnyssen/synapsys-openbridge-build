"""Architecture map: one recursive object journey over the existing mesh registry (source-only slice, not released).

Replaces the fixed three-column noun list. The registry (synapsys.mesh.registry) stays the only architecture store; the
journey, binding and rendering are pure functions in synapsys_mesh (journey.py, binding.py, journey_ui.py). This controller
only fetches the registry, computes the read-only source binding from the installed addon sources, and returns ONE
fragment for the requested object. It writes nothing.

UNRESOLVED RIGHT R1 (unchanged from the base, not fixed here): the registry is read with sudo(), so any logged-in user
receives the whole registry whatever their synapsys_mesh read group. Changing that is an access decision for D001/D007.
"""
import json
import os
from html import escape

from odoo import http
from odoo.http import request

ROOT = 'N.CONTEXT'


# REVIEW NAVIGATION ONLY. All noun identities, meaning and maturity come from the ONE live mesh registry.
# No noun is promoted or classified as a new K-kind by this listing.
def _noun_review_index(graph, expanded=True):
    labels = ('Form', 'Flow', 'Evolve', 'Mesh', 'Unmapped')
    rows = {group: [] for group in labels}
    nouns = [e for e in graph.els.values() if e.get('cls') == 'N']
    for element in sorted(nouns, key=lambda e: (labels.index(e.get('menu')) if e.get('menu') in labels else 99,
                                                 e.get('label') or e['id'])):
        group = element.get('menu') if element.get('menu') in ('Form', 'Flow', 'Evolve', 'Mesh') else 'Unmapped'
        state = str(element.get('status') or 'UNRESOLVED')
        noun_id = escape(str(element['id']), quote=True)
        label = escape(str(element.get('label') or element['id']))
        status = escape(state)
        q = len(element.get('open_questions') or ())
        rows[group].append('<li><a href="#" data-obj="%s" data-trail="">%s</a>'
                           ' <span class="sm mut">%s · %d open questions</span></li>'
                           % (noun_id, label, status, q))
    sections = ''.join('<details><summary>%s (%d)</summary><ul>%s</ul></details>' %
                       (escape(group), len(rows[group]), ''.join(rows[group]))
                       for group in labels if rows[group])
    question_count = sum(len(e.get('open_questions') or ()) for e in nouns)
    state_counts = {status: sum(1 for e in nouns if (e.get('status') or 'UNRESOLVED') == status)
                    for status in ('RULED', 'PROPOSAL', 'OPEN', 'UNRESOLVED')}
    state_caption = ', '.join('%s %d' % (status, state_counts[status])
                              for status in state_counts if state_counts[status])
    return ('<div class="aj" data-section="noun-review-index">'
            '<details%s><summary>Review all %d nouns · %d open questions · %s</summary>'
            '<p class="sm mut">Source: one candidate Mesh registry. Each noun opens the same Value, '
            'Kinematics, Fractals and Form / Flow / Evolve review. RULED, PROPOSAL and OPEN '
            'are source states, not approvals. K-kind is Context-bound where unresolved. '
            'No Odoo record instance or accepted Benefit is implied.</p>%s</details></div>'
            % (' open' if expanded else '', len(nouns), question_count, escape(state_caption), sections))


def _noun_shape_review(graph, requested_id):
    """Truthful source-bound review of noun shape; no fabricated kind/size/resolution."""
    e = graph.els.get(requested_id or ROOT)
    if not e or e.get('cls') != 'N':
        return ''
    def val(key):
        value = e.get(key)
        if value is None or value == '' or value == [] or value == {}:
            return 'UNSOURCED'
        return escape(str(value), quote=True)
    label = escape(str(e.get('label') or e.get('id') or requested_id))
    q = len(e.get('open_questions') or ())
    return ('<div class="aj" data-section="noun-shape-review"><section>'
            '<h2>Shape of %s</h2><p class="sm mut">Enable review only. '
            'Values are the current candidate Mesh source, not an accepted operational object.</p>'
            '<ul><li>Definition: %s</li><li>Source: %s</li>'
            '<li>Kind (source description): %s</li><li>Size: %s</li>'
            '<li>Resolution: %s</li><li>Source state: %s</li>'
            '<li>Unresolved questions: %d</li></ul></section></div>'
            % (label, val('definition'), val('definition_source'), val('kind'),
               val('size'), val('resolution'), val('status'), q))


class ArchitectureMap(http.Controller):

    @http.route(['/synapsys/architecture/map/data', '/synapsys/architecture/map/object'], type='jsonrpc', auth='user')
    def map_data(self, object_id=None, trail=None, mode='enable', ov=''):
        # Enable review is explicitly Steward/system-only while rights R1 is unresolved.
        # Keep the existing registry authority source; do not broaden disclosure via the new all-noun index.
        if not (request.env.user.has_group('synapsys.group_synapsys_steward')
                or request.env.user.has_group('base.group_system')):
            return ('<div class="aj"><p>Architecture noun review is limited to the Steward '
                    'until the Collaborator access boundary is independently tested.</p></div>')
        from odoo.addons.synapsys_mesh import arch_check, binding, journey, journey_ui
        Reg = request.env['synapsys.mesh.registry'].sudo()   # R1: restricted at controller boundary for review
        reg = Reg.search([('state', '=', 'active')], limit=1) or Reg.search([], order='id desc', limit=1)
        if not reg:
            return '<div class="aj"><p>No architecture registry is loaded. Nothing is shown and nothing is claimed.</p></div>'
        g = journey.Graph(reg.body, {'version': reg.version, 'state': reg.state, 'ppv': reg.ppv,
                                     'release_ref': reg.release_ref})
        rep = None
        try:
            from odoo.modules.module import get_module_path
            root = os.path.dirname(get_module_path('synapsys_mesh'))
            spec_path = os.path.join(os.path.dirname(os.path.abspath(binding.__file__)), 'data', 'asset_chain_binding_v0_1.json')
            with open(spec_path, encoding='utf-8') as f:
                spec = json.load(f)
            rep = binding.verify(spec, binding.Snapshot.from_tree(root, spec, rev=None))
        except Exception:                                    # unreadable sources are reported as NOT_COMPUTED, never guessed
            rep = None
        ids = [t for t in (trail or '').split(',') if t]
        j = journey.journey(g, object_id or ROOT, ids, rep, None, None, arch_check.check(reg.body))
        from odoo.addons.synapsys import lens_contract as lc
        el = lc.from_noun(g, object_id or ROOT)
        depth = lc.render_element(el, mode, lc.parse_overrides(ov), obj_link=True) if el else ''
        return (_noun_review_index(g, expanded=(not object_id or object_id == ROOT)) + _noun_shape_review(g, object_id or ROOT)
                + '<div class="aj" data-section="lens-depth">%s</div>' % depth + journey_ui.render(j))
