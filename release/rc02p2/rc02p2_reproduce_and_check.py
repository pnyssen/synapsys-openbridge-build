#!/usr/bin/env python3
"""RC02-P2 source reproduction + static qualification (offline; NO Odoo runtime => runtime behaviour UNVERIFIED).
Subcommands:
  rebuild --repo <clone with baseline commit> --patch <frozen patch> --out <empty dir> [--apply <delta.patch>]
  check   --tree <dir containing synapsys/ ...> [--expect-identity <sha256>]
Exit 0 only if every check passes; 3 otherwise (fail closed)."""
import argparse, ast, hashlib, os, re, subprocess, sys, tempfile
from xml.dom import minidom
BASE = '7278898fb49d4eff5cdc27d37864fed0bdc0f8dc'
PATCH_SHA = '6b37c5e9dfded209716f14d3330cb91202355c0d0bcf548b769865d222d715e1'
FROZEN_ID = 'd066f56080681a4e07806479bc6d43bb0032f725cd2168d74e45c8879d7f15c2'
def sha(b): return hashlib.sha256(b).hexdigest()
def identity(tree):
    rows = []
    root = os.path.join(tree, 'synapsys')
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d != '__pycache__']
        for f in fn:
            p = os.path.join(dp, f); b = open(p, 'rb').read()
            rows.append(('synapsys/' + os.path.relpath(p, root).replace(os.sep, '/'), sha(b), len(b)))
    rows.sort()
    return sha(''.join('%s\t%s\t%d\n' % r for r in rows).encode()), len(rows), sum(r[2] for r in rows)
def die(m): print('REFUSE:', m); sys.exit(3)
def rebuild(a):
    patch = open(a.patch, 'rb').read()
    if sha(patch) != PATCH_SHA: die('patch hash differs from frozen %s' % PATCH_SHA)
    if os.path.exists(a.out) and os.listdir(a.out): die('output dir not empty')
    os.makedirs(a.out, exist_ok=True)
    ar = subprocess.run('git -C %s archive %s | tar -x -C %s' % (a.repo, BASE, a.out), shell=True)
    if ar.returncode: die('baseline commit %s not in repo' % BASE)
    for p in [a.patch] + ([a.apply] if a.apply else []):
        for args in (['--check'], []):
            r = subprocess.run(['git', 'apply'] + args + [os.path.abspath(p)], cwd=a.out)
            if r.returncode: die('git apply %s failed for %s' % (args, p))
    print('rebuilt ->', a.out)
def check(a):
    t = a.tree; fails = []; ok = lambda n, c, d='': (print(('PASS ' if c else 'FAIL ') + n + (' :: ' + d if d else '')), (None if c else fails.append(n)))
    ident, n, tot = identity(t)
    if a.expect_identity: ok('identity == expected', ident == a.expect_identity, '%s files=%d bytes=%d' % (ident, n, tot))
    else: print('INFO identity', ident, 'files', n, 'bytes', tot)
    pyn = bad = 0
    for dp, dn, fn in os.walk(t):
        for f in fn:
            p = os.path.join(dp, f)
            if f.endswith('.py'):
                pyn += 1
                try: compile(open(p, encoding='utf-8').read(), p, 'exec')
                except Exception as e: bad += 1; print('  py error', p, e)
            if f.endswith('.xml'):
                try: minidom.parse(p)
                except Exception as e: bad += 1; print('  xml error', p, e)
    ok('all python compiles and all XML parses', bad == 0, '%d python files' % pyn)
    man = lambda m: ast.literal_eval(open(os.path.join(t, m, '__manifest__.py'), encoding='utf-8').read())
    mods = [m for m in os.listdir(t) if os.path.exists(os.path.join(t, m, '__manifest__.py'))]
    mf = {m: man(m) for m in mods}
    def closure(m, seen=None):
        seen = seen or set()
        for d in mf.get(m, {}).get('depends', []):
            if d not in seen: seen.add(d); closure(d, seen)
        return seen
    defined = {}
    for m in mods:
        for dp, _, fn in os.walk(os.path.join(t, m)):
            for f in fn:
                if f.endswith('.py'):
                    for mm in re.finditer(r"_name\s*=\s*'([\w.]+)'", open(os.path.join(dp, f), encoding='utf-8').read()): defined.setdefault(mm.group(1), set()).add(m)
    # F1: every synapsys.* res_model used by an addon's data must be defined by that addon or its transitive dependencies
    for m in mods:
        deps = closure(m) | {m}
        for f in mf[m].get('data', []):
            if not f.endswith('.xml'): continue
            doc = minidom.parse(os.path.join(t, m, f))
            for el in doc.getElementsByTagName('field'):
                if el.getAttribute('name') == 'res_model' and el.firstChild:
                    rm = el.firstChild.data.strip()
                    if rm.startswith('synapsys.'):
                        ok('F1 %s/%s res_model %s is defined in addon or its dependencies' % (m, f, rm), bool(defined.get(rm, set()) & deps), 'defined in %s' % sorted(defined.get(rm, ['?'])))
    # F5: a version that adds ir.ui.view records needs a pre-migrate setting ir_ui_view.visibility default for its own version
    m = 'synapsys'; ver = mf[m]['version']
    adds_views = any(re.search(r'model="ir\.ui\.view"', open(os.path.join(t, m, f), encoding='utf-8').read()) for f in mf[m]['data'] if f.endswith('.xml') and 'enable_peers' in f)
    pm = os.path.join(t, m, 'migrations', ver, 'pre-migrate.py')
    good = os.path.exists(pm) and 'visibility' in open(pm).read() and "SET DEFAULT 'public'" in open(pm).read()
    ok('F5 version %s adds ir.ui.view => pre-migrate sets ir_ui_view.visibility default for THIS version' % ver, (not adds_views) or good)
    ok('manifest version of synapsys is 20.0.2.4.2', ver == '20.0.2.4.2')
    sys.exit(3 if fails else 0)
ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest='cmd', required=True)
r = sp.add_parser('rebuild'); r.add_argument('--repo', required=True); r.add_argument('--patch', required=True); r.add_argument('--out', required=True); r.add_argument('--apply')
c = sp.add_parser('check'); c.add_argument('--tree', required=True); c.add_argument('--expect-identity')
a = ap.parse_args(); rebuild(a) if a.cmd == 'rebuild' else check(a)
