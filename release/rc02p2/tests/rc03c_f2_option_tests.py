"""Compares the controller behaviour of RC03b (F2 as approved: non-Steward gets a notice) with RC03c (narrow F2: non-Steward gets the BASELINE journey, new panels Steward-only).
Odoo is stubbed ONLY for imports/env; journey, journey_ui, arch_check run for real. usage: rc03c_f2_option_tests.py <RC03b tree> <RC03c tree>"""
import importlib.util, json, os, sys, types
sys.dont_write_bytecode = True
tb, tc = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.join(tc, 'synapsys_mesh'))
import journey, journey_ui, arch_check                                  # real, from the tree
body = open(os.path.join(tc, 'synapsys_mesh/data/mesh_registry_v0_3.json'), encoding='utf-8').read()
class User:
    def __init__(s, groups): s.groups = groups
    def has_group(s, g): return g in s.groups
class Reg:
    def __init__(s): s.body, s.version, s.state, s.ppv, s.release_ref = body, '0.3', 'candidate', 'potential', 'x'
class Env(dict):
    user = None
class RegModel:
    def sudo(s): return s
    def search(s, domain, limit=None, order=None): return Reg()
def load(tree, name):
    odoo = types.ModuleType('odoo'); http = types.ModuleType('odoo.http'); addons = types.ModuleType('odoo.addons'); mesh = types.ModuleType('odoo.addons.synapsys_mesh')
    class Controller: pass
    http.Controller = Controller; http.route = lambda *a, **k: (lambda f: f); http.request = types.SimpleNamespace(env=Env({'synapsys.mesh.registry': RegModel()}))
    mesh.__path__ = [os.path.join(tree, 'synapsys_mesh')]; mesh.arch_check, mesh.journey, mesh.journey_ui = arch_check, journey, journey_ui
    import binding as _b; mesh.binding = _b
    odoo.http = http; odoo.addons = addons; addons.synapsys_mesh = mesh
    sys.modules.update({'odoo': odoo, 'odoo.http': http, 'odoo.addons': addons, 'odoo.addons.synapsys_mesh': mesh})
    spec = importlib.util.spec_from_file_location(name, os.path.join(tree, 'synapsys/controllers/arch_map.py')); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m, http.request
res = []; chk = lambda n, c, d='': (res.append(bool(c)), print(('PASS ' if c else 'FAIL ') + n + (' :: ' + d if d else '')))
def call(mod_req, groups, oid=None, trail=None):
    m, req = mod_req; req.env.user = User(groups); return m.ArchitectureMap().map_data(oid, trail)
B, C = load(tb, 'am_b'), load(tc, 'am_c')
STEW, COLLAB = ['synapsys.group_synapsys_steward'], ['synapsys.group_synapsys_user']
# independent baseline: what the ORIGINAL controller returned for any logged-in user = journey_ui.render(j) over the same inputs
g = journey.Graph(body, {'version': '0.3', 'state': 'candidate', 'ppv': 'potential', 'release_ref': 'x'})
baseline = lambda oid, trail: journey_ui.render(journey.journey(g, oid or 'N.CONTEXT', [t for t in (trail or '').split(',') if t], None, None, None, arch_check.check(body)))
nb = call(B, COLLAB); chk('C1 RC03b (F2 as approved): collaborator gets only the notice, no journey', 'limited to the Steward' in nb and 'noun-review-index' not in nb and len(nb) < 400, '%d bytes' % len(nb))
nc = call(C, COLLAB); chk('C2 RC03c: collaborator gets EXACTLY the baseline journey (byte-identical to the original controller output)', nc == baseline(None, None) and len(nc) > 1000, '%d bytes' % len(nc))
chk('C3 RC03c: collaborator sees none of the NEW panels (no noun-review-index, no noun-shape-review)', 'noun-review-index' not in nc and 'noun-shape-review' not in nc)
sb = call(B, STEW); sc = call(C, STEW); chk('C4 Steward output identical in RC03b and RC03c (F2-narrow changes nobody else)', sb == sc and 'noun-review-index' in sc)
n28 = journey.Graph(body); nid = [e['id'] for e in n28.els.values() if e.get('cls') == 'N'][3]
chk('C5 RC03c collaborator on a specific object + trail == baseline for that object', call(C, COLLAB, nid, 'N.CONTEXT') == baseline(nid, 'N.CONTEXT'))
chk('C6 RC03c collaborator: no new panel even for a specific object (shape review stays Steward-only)', 'noun-shape-review' not in call(C, COLLAB, nid) and 'noun-shape-review' in call(C, STEW, nid))
sysu = call(C, ['base.group_system']); chk('C7 RC03c system administrator treated as privileged', 'noun-review-index' in sysu)
chk('C8 RC03c: R1 is NOT fixed - the registry is still read with sudo() (disclosure to any logged-in user is the baseline, unchanged)', "request.env['synapsys.mesh.registry'].sudo()" in open(os.path.join(tc, 'synapsys/controllers/arch_map.py')).read())
print('SUMMARY pass=%d fail=%d' % (sum(res), len(res) - sum(res))); sys.exit(0 if all(res) else 1)
