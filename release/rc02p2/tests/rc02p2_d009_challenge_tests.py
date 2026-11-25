#!/usr/bin/env python3
"""D009 T3 challenges, executed: (a) invalid object_id / trail handling, (b) hostile registry text through the real renderer.
Pure-python modules (journey, journey_ui, arch_check) are imported from the rebuilt tree; Odoo is stubbed ONLY for arch_map.py imports.
usage: rc02p2_d009_challenge_tests.py <tree dir containing synapsys/ and synapsys_mesh/>"""
import sys, os, json, types, importlib.util, copy
tree = sys.argv[1]; sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(tree, 'synapsys_mesh'))
import journey, journey_ui, arch_check                                  # noqa: E402
# --- minimal odoo stub (only what arch_map.py imports at module level)
odoo = types.ModuleType('odoo'); http = types.ModuleType('odoo.http')
class Controller: pass
http.Controller = Controller; http.route = lambda *a, **k: (lambda f: f); http.request = types.SimpleNamespace()
odoo.http = http; sys.modules.update({'odoo': odoo, 'odoo.http': http})
spec = importlib.util.spec_from_file_location('arch_map', os.path.join(tree, 'synapsys/controllers/arch_map.py'))
am = importlib.util.module_from_spec(spec); spec.loader.exec_module(am)
if '--mutate-no-escape' in sys.argv:   # negative control: proves the hostile-text test can fail
    journey_ui.html.escape = lambda s, quote=True: s; am.escape = lambda s, quote=True: s
body = open(os.path.join(tree, 'synapsys_mesh/data/mesh_registry_v0_3.json'), encoding='utf-8').read()
res = []; chk = lambda n, c, d='': (res.append(c), print(('PASS ' if c else 'FAIL ') + n + (' :: ' + d if d else '')))
def page(text, oid, trail=''):
    g = journey.Graph(text)
    ids = [t for t in (trail or '').split(',') if t]
    j = journey.journey(g, oid or am.ROOT, ids, None, None, None, arch_check.check(text))
    return am._noun_review_index(g, expanded=(not oid or oid == am.ROOT)) + am._noun_shape_review(g, oid or am.ROOT) + journey_ui.render(j)
g0 = journey.Graph(body); nouns = [e for e in g0.els.values() if e.get('cls') == 'N']
chk('baseline: registry loads; 28 nouns', len(nouns) == 28, 'nouns=%d' % len(nouns))
base = page(body, None); chk('baseline root page renders', isinstance(base, str) and len(base) > 1000, 'bytes=%d' % len(base))
# (a) invalid object ids and trails: must return a bounded string, never raise, never reflect raw markup
bad_ids = ['', 'N.NOPE', 'x' * 100000, '<script>alert(1)</script>', '"><img src=x onerror=alert(1)>', '../../etc/passwd', '\x00', '\U0001F642', "'; DROP TABLE x;--", ' ', 'N.CONTEXT,N.CONTEXT']
bad_trails = ['', ',', ',,,', 'N.NOPE', '<b>,N.NOPE', 'a,' * 3000, '\x00,\n', nouns[0]['id'] + ',' + nouns[1]['id']]
exc = []; reflected = []
for oid in bad_ids:
    for tr in bad_trails:
        try:
            out = page(body, oid, tr)
            assert isinstance(out, str)
            for marker in ('<script>alert(1)</script>', '<img src=x onerror=alert(1)>'):
                if marker in out: reflected.append((oid[:30], tr[:20], marker))
        except Exception as e: exc.append((oid[:30], tr[:20], type(e).__name__, str(e)[:80]))
chk('(a) %d invalid object_id x trail combinations: no exception' % (len(bad_ids) * len(bad_trails)), not exc, str(exc[:3]))
chk('(a) no raw hostile markup reflected from object_id/trail into the page', not reflected, str(reflected[:3]))
# (b) hostile registry text through the real renderer
P = '<img src=x onerror=alert(1)>"\'><script>alert(2)</script>&amp;'
hostile = json.loads(body)
keep = {'id', 'cls', 'menu', 'status', 'members', 'from', 'to'}
for e in hostile['elements']:
    for k, v in list(e.items()):
        if k in keep: continue
        if isinstance(v, str): e[k] = P
        elif isinstance(v, list) and v and all(isinstance(x, str) for x in v): e[k] = [P for _ in v]
h = json.dumps(hostile, sort_keys=True)
raw_markers = ['<img src=x', '<script>alert(2)', 'onerror=alert(1)>']
targets = [None] + [n['id'] for n in nouns[:6]]
leaks = []
for oid in targets:
    for tr in ('', nouns[0]['id']):
        try: out = page(h, oid, tr)
        except Exception as e: leaks.append(('EXC', oid, type(e).__name__, str(e)[:60])); continue
        for m in raw_markers:
            if m in out: leaks.append((oid, tr[:12], m))
chk('(b) hostile registry strings across %d pages: no raw tag/handler survives rendering' % (len(targets) * 2), not leaks, str(leaks[:4]))
sys.exit(0 if all(res) else 3)
