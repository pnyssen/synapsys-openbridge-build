import hashlib, json, os, shutil, subprocess, sys, tempfile
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.dirname(here)
V = [sys.executable, '-I', os.path.join(root, 'verify_on_target.py')]
BASE = os.path.join(root, 'manifests', 'BASELINE_v20-dev_7278898.manifest.json'); RC = os.path.join(root, 'manifests', 'RC03b_360a2b4f.manifest.json')
SRC_BASE, SRC_RC = sys.argv[1], sys.argv[2]            # extracted trees: baseline commit, RC03b commit
sh = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
res = []
def run(target, man, only=None, msha=None, extra=()):
    c = V + ['--addons-dir', target, '--manifest', man, '--manifest-sha256', msha or sh(man)] + (['--only', only] if only else []) + list(extra)
    r = subprocess.run(c, capture_output=True, text=True); return r.returncode, (json.loads(r.stdout) if r.stdout.strip() else {})
def chk(n, c, d=''): res.append(c); print(('PASS ' if c else 'FAIL ') + n + (' :: ' + d if d else ''))
def fresh(src):
    d = tempfile.mkdtemp(); shutil.copytree(src, os.path.join(d, 'addons')); return os.path.join(d, 'addons')
t = fresh(SRC_BASE)
rc, r = run(t, BASE); chk('V1 prestate: target == baseline manifest -> MATCH_ALL, exit 0', rc == 0 and r['verdict'] == 'MATCH_ALL', '%d addons' % len(r['addons']))
rc, r = run(t, RC)
sy, rf = r['addons']['synapsys'], r['addons']['synapsys_v19_reference']
chk('V2 baseline target vs RC03b manifest -> DIFF exit 3 with exact delta', rc == 3 and r['verdict'] == 'DIFF'
    and sy['changed'] == ['__manifest__.py', 'controllers/arch_map.py', 'static/src/home.xml'] and sorted(sy['missing']) == ['migrations/20.0.2.4.2/pre-migrate.py', 'views/synapsys_enable_peers.xml']
    and rf['changed'] == ['__manifest__.py'] and rf['missing'] == ['views/register_homes.xml'], 'synapsys=%s v19=%s' % (sy['status'], rf['status']))
t2 = fresh(SRC_RC); rc, r = run(t2, RC); chk('V3 RC03b delivered intact -> MATCH_ALL exit 0 (post-staging receipt)', rc == 0 and r['verdict'] == 'MATCH_ALL')
rc, r = run(t2, RC, msha='0' * 64); chk('V4 NEG wrong --manifest-sha256 -> REFUSE, exit 3, no addon examined', rc == 3 and r['verdict'] == 'REFUSE_MANIFEST_HASH_MISMATCH' and r['addons'] == {})
p = os.path.join(t2, 'synapsys', 'controllers', 'arch_map.py'); b = bytearray(open(p, 'rb').read()); b[200] ^= 1; open(p, 'wb').write(bytes(b))
rc, r = run(t2, RC); chk('V5 NEG single-bit corruption, same size -> DIFF changed=[controllers/arch_map.py]', rc == 3 and r['addons']['synapsys']['changed'] == ['controllers/arch_map.py'])
t3 = fresh(SRC_RC); os.remove(os.path.join(t3, 'synapsys', 'views', 'synapsys_enable_peers.xml'))
rc, r = run(t3, RC); chk('V6 NEG partial transfer (file missing) -> DIFF missing', rc == 3 and r['addons']['synapsys']['missing'] == ['views/synapsys_enable_peers.xml'])
t4 = fresh(SRC_RC); open(os.path.join(t4, 'synapsys', 'views', 'stray.xml'), 'w').write('<odoo/>')
rc, r = run(t4, RC); chk('V7 NEG unexpected extra file -> DIFF extra (stale/overlay file not allowed)', rc == 3 and r['addons']['synapsys']['extra'] == ['views/stray.xml'])
t5 = fresh(SRC_RC); os.makedirs(os.path.join(t5, 'synapsys', '__pycache__')); open(os.path.join(t5, 'synapsys', '__pycache__', 'x.cpython-312.pyc'), 'wb').write(b'x'); open(os.path.join(t5, 'synapsys', 'models', 'y.pyc'), 'wb').write(b'x')
rc, r = run(t5, RC); chk('V8 __pycache__ and .pyc ignored -> still MATCH_ALL', rc == 0)
t6 = fresh(SRC_RC); shutil.rmtree(os.path.join(t6, 'synapsys_mesh'))
rc, r = run(t6, RC); chk('V9 NEG whole addon missing -> ADDON_DIR_MISSING exit 3', rc == 3 and r['addons']['synapsys_mesh']['status'] == 'ADDON_DIR_MISSING')
rc, r = run(t6, RC, only='synapsys,synapsys_v19_reference'); chk('V10 --only scopes the check to the two changed addons -> MATCH_ALL despite synapsys_mesh absent', rc == 0 and sorted(r['addons']) == ['synapsys', 'synapsys_v19_reference'])
rc, r = run(t2, RC, only='no_such_addon'); chk('V11 NEG addon not in manifest -> NOT_IN_MANIFEST exit 3', rc == 3 and r['addons']['no_such_addon']['status'] == 'NOT_IN_MANIFEST')
t7 = fresh(SRC_RC); os.symlink('/etc/hostname', os.path.join(t7, 'synapsys', 'link.txt'))
rc, r = run(t7, RC); chk('V12 NEG symlink inside addon -> flagged (extra), exit 3', rc == 3 and 'link.txt' in r['addons']['synapsys']['extra'])
def snap(d):
    out = {}
    for dp, dn, fn in os.walk(d):
        for f in fn:
            q = os.path.join(dp, f); st = os.lstat(q); out[q] = (st.st_size, st.st_mtime_ns, hashlib.sha256(open(q, 'rb').read()).hexdigest() if not os.path.islink(q) else 'L')
        out.update({os.path.join(dp, x): ('D',) for x in dn})
    return out
t8 = fresh(SRC_RC); s0 = snap(t8); rc, r = run(t8, RC, extra=['--receipt', os.path.join(tempfile.mkdtemp(), 'r.json')]); s1 = snap(t8)
chk('V13 verifier is read-only: target tree (files, sizes, mtimes, hashes, dirs) identical before and after a run; receipt written elsewhere', rc == 0 and s0 == s1 and len(s0) > 100, '%d entries' % len(s0))
ok = all(res); print('SUMMARY pass=%d fail=%d' % (sum(res), len(res) - sum(res))); sys.exit(0 if ok else 1)
