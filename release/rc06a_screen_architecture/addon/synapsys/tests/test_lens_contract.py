import copy
import importlib.util
import os
import unittest

try:
    from odoo.addons.synapsys import lens_contract as lc, lens_render as lr
except Exception:  # offline: load the pure modules by path
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    def _load(n):
        spec = importlib.util.spec_from_file_location(n, os.path.join(base, n + '.py'))
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
    lc = _load('lens_contract'); lr = _load('lens_render')


EL = lc.element('N.SERVICE', 'Service', noun='Service', status='RULED', definition='A governed way to deliver',
                source='registry 0.3.5', kind='K-6', kind_via='Context CTX-SS', verbs=['route', 'execute'], ffe='Flow',
                relationships=[('delivers', 'out', 'N.OUTCOME', 'Outcome <b>x</b>')], oba='Outcome',
                service='GV-TEC-001', method='D002-WRB', evidence='none filed', open_questions=2)


class LensContract(unittest.TestCase):
    def test_depth_is_cumulative(self):
        a, b, c = (lc.render_element(EL, m) for m in lc.MODES)
        self.assertNotIn('Relationships', a)
        self.assertIn('Relationships', b); self.assertNotIn('Provenance', b); self.assertNotIn('Stable id', b)
        self.assertIn('Stable id', c); self.assertIn('GV-TEC-001 / D002-WRB', c); self.assertIn('Context CTX-SS', c)
        for frag in ('A governed way to deliver', 'RULED'):
            self.assertTrue(all(frag in x for x in (a, b, c)))

    def test_mode_never_changes_identity_or_kind(self):
        outs = [lc.render_element(EL, m) for m in lc.MODES]
        self.assertTrue(all('data-element="N.SERVICE"' in o for o in outs))
        self.assertIn('K-6', outs[2]); self.assertNotIn('K-6', outs[0]); self.assertNotIn('K-6', outs[1])  # shown only at Enrich, same value

    def test_input_not_mutated(self):
        before = copy.deepcopy(EL)
        for m in lc.MODES:
            lc.render_element(EL, m, {'N.SERVICE': 'enrich'})
        self.assertEqual(before, EL)

    def test_missing_is_unsourced_and_kind_unbound(self):
        e = lc.element('X', 'X')
        out = lc.render_element(e, 'enrich')
        self.assertIn('UNSOURCED', out); self.assertIn('UNBOUND', out); self.assertNotIn('K-', out)

    def test_unknown_mode_falls_back_to_enable(self):
        self.assertEqual(lc.normalise('admin'), 'enable'); self.assertEqual(lc.normalise(None), 'enable')
        self.assertIn('data-mode="enable"', lc.render_element(EL, '<script>'))

    def test_override_is_local_and_justified(self):
        out = lc.render_element(EL, 'enable', {'N.SERVICE': 'enrich'})
        self.assertIn('data-mode="enrich"', out); self.assertIn('data-global="enable"', out)
        self.assertIn('data-override="yes"', out); self.assertIn('Reset to global', out)
        other = lc.render_element(lc.element('OTHER', 'Other'), 'enable', {'N.SERVICE': 'enrich'})
        self.assertIn('data-mode="enable"', other)

    def test_override_parsing_rejects_unsafe(self):
        self.assertEqual(lc.parse_overrides('lens:Form@enrich;bad id@enrich;x@nope;<s>@enable'), {'lens:Form': 'enrich'})
        self.assertEqual(lc.parse_overrides(None), {})

    def test_escaping(self):
        out = lc.render_element(EL, 'enhance', obj_link=True)
        self.assertNotIn('<b>x</b>', out); self.assertIn('&lt;b&gt;x&lt;/b&gt;', out)

    def test_lens_elements_from_register(self):
        for grp, sec in (('movement', 'm0'), ('nav', 'n2'), ('other', 'k4')):
            ls = lr.lenses_for(grp, sec)
            self.assertTrue(ls)
            for l in ls:
                a = lc.render_element(lc.from_lens(l), 'enable'); c = lc.render_element(lc.from_lens(l), 'enrich')
                self.assertIn(l[1].replace('&', '&amp;'), a); self.assertIn('Stable id', c)
        self.assertEqual(lr.lenses_for('movement', 'm9'), []); self.assertEqual(lr.lenses_for('pattern', 'e0'), [])

    def test_fragment_carries_its_own_style(self):
        # the Architecture map page has no lens stylesheet, so the contract must style itself
        out = lc.render_element(EL, 'enhance')
        self.assertTrue(out.startswith('<style>')); self.assertIn('.syn-el .kv', out)

    def test_two_surfaces_share_one_contract(self):
        # same renderer, same markers, for a lens (Architecture > Lenses) and a noun (Architecture map)
        lens = lc.render_element(lc.from_lens(lr.LENSES[0]), 'enhance')
        noun = lc.render_element(EL, 'enhance')
        for marker in ('syn-el', 'data-mode="enhance"', 'data-global="enhance"'):
            self.assertIn(marker, lens); self.assertIn(marker, noun)

    def test_every_registry_noun_renders_in_three_modes(self):
        import json, sys
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(os.path.dirname(base), 'synapsys_mesh', 'data', 'mesh_registry_v0_3.json')
        if not os.path.exists(path):
            self.skipTest('registry data not beside the addon')
        try:
            from odoo.addons.synapsys_mesh import journey
        except Exception:
            spec = importlib.util.spec_from_file_location('journey', os.path.join(os.path.dirname(path), '..', 'journey.py'))
            journey = importlib.util.module_from_spec(spec); sys.modules['journey'] = journey; spec.loader.exec_module(journey)
        g = journey.Graph(open(path).read())
        nouns = [i for i, e in g.els.items() if e.get('cls') == 'N']
        self.assertEqual(len(nouns), 28)
        for n in nouns:
            el = lc.from_noun(g, n)
            outs = [lc.render_element(el, m, obj_link=True) for m in lc.MODES]
            self.assertTrue(all('data-element="%s"' % n in o for o in outs))
            self.assertTrue(len(outs[0]) <= len(outs[1]) <= len(outs[2]))


if __name__ == '__main__':
    unittest.main()
