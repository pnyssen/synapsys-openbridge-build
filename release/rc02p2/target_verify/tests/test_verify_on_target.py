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
rc, r = run(t7, RC); chk('V12 NEG symlinked FILE inside addon -> flagged SYMLINK_FILE, exit 3', rc == 3 and {'path': 'link.txt', 'kind': 'SYMLINK_FILE'} in r['addons']['synapsys']['unexpected_links_or_special'])
def snap(d):
    out = {}
    for dp, dn, fn in os.walk(d):
        for f in fn:
            q = os.path.join(dp, f); st = os.lstat(q); out[q] = (st.st_size, st.st_mtime_ns, hashlib.sha256(open(q, 'rb').read()).hexdigest() if not os.path.islink(q) else 'L')
        out.update({os.path.join(dp, x): ('D',) for x in dn})
    return out
t8 = fresh(SRC_RC); s0 = snap(t8); rc, r = run(t8, RC, extra=['--receipt', os.path.join(tempfile.mkdtemp(), 'r.json')]); s1 = snap(t8)
chk('V13 verifier is read-only: target tree (files, sizes, mtimes, hashes, dirs) identical before and after a run; receipt written elsewhere', rc == 0 and s0 == s1 and len(s0) > 100, '%d entries' % len(s0))

# ---- v2 controls (V14 reproduces the independently reported false MATCH_ALL on v1)
def runx(args, stdin=None, code=None):
    c = ([sys.executable, '-I', '-c', open(os.path.join(root, 'verify_on_target.py')).read()] if code else V) + args
    r = subprocess.run(c, capture_output=True, text=True, input=stdin); 
    try: j = json.loads(r.stdout)
    except Exception: j = {}
    return r.returncode, j
MS = sh(RC); base_args = lambda d, extra=(): ['--addons-dir', d, '--manifest', RC, '--manifest-sha256', MS, '--only', 'synapsys'] + list(extra)
t9 = fresh(SRC_RC); out_dir = tempfile.mkdtemp(); open(os.path.join(out_dir, 'evil.py'), 'w').write('x'); os.symlink(out_dir, os.path.join(t9, 'synapsys', 'linked_dir'))
rc, r = runx(base_args(t9)); pk = r['addons']['synapsys']['unexpected_links_or_special']
chk('V14 NEG (reported defect) unexpected SYMLINKED DIRECTORY in an otherwise matching addon -> DIFF exit 3, SYMLINK_DIR named', rc == 3 and r['verdict'] == 'DIFF' and {'path': 'linked_dir', 'kind': 'SYMLINK_DIR'} in pk, str(pk))
t10 = fresh(SRC_RC); os.symlink(os.path.join(t10, 'synapsys', 'models'), os.path.join(t10, 'synapsys', 'models_alias'))
rc, r = runx(base_args(t10)); chk('V15 NEG symlink directory pointing INSIDE the tree is still refused', rc == 3 and any(x['kind'] == 'SYMLINK_DIR' for x in r['addons']['synapsys']['unexpected_links_or_special']))
t11 = fresh(SRC_RC); os.symlink('/nonexistent/target', os.path.join(t11, 'synapsys', 'dangling'))
rc, r = runx(base_args(t11)); chk('V16 NEG dangling symlink -> SYMLINK_BROKEN, exit 3', rc == 3 and {'path': 'dangling', 'kind': 'SYMLINK_BROKEN'} in r['addons']['synapsys']['unexpected_links_or_special'])
t12 = fresh(SRC_RC); real = os.path.join(os.path.dirname(t12), 'real_synapsys'); shutil.move(os.path.join(t12, 'synapsys'), real); os.symlink(real, os.path.join(t12, 'synapsys'))
rc, r = runx(base_args(t12)); chk('V17 NEG addon ROOT is a symlink -> ADDON_ROOT_SYMLINK exit 3 (resolved target reported)', rc == 3 and r['addons']['synapsys']['status'] == 'ADDON_ROOT_SYMLINK' and r['addons']['synapsys']['resolves_to'] == os.path.realpath(real))
t13 = fresh(SRC_RC); rp = os.path.join(t13, 'synapsys', 'receipt.json'); rc, r = runx(base_args(t13, ['--receipt', rp]))
chk('V18 NEG receipt destination inside an addon tree -> refused exit 2, nothing written', rc == 2 and r.get('verdict') == 'REFUSE_RECEIPT_INSIDE_EXAMINED_TREE' and not os.path.exists(rp))
rp2 = os.path.join(t13, 'receipt_at_root.json'); rc, r = runx(base_args(t13, ['--receipt', rp2])); chk('V19 NEG receipt destination in the addons root directory -> refused exit 2', rc == 2 and not os.path.exists(rp2))
rp3 = os.path.join(tempfile.mkdtemp(), 'ok.json'); rc, r = runx(base_args(t13, ['--receipt', rp3])); chk('V19b receipt outside every examined tree is written', rc == 0 and os.path.exists(rp3))
t14 = fresh(SRC_RC); os.makedirs(os.path.join(t14, 'synapsys', 'empty_extra_dir'))
rc, r = runx(base_args(t14)); chk('V20 NEG unexpected (empty) directory -> DIFF unexpected_dirs', rc == 3 and r['addons']['synapsys']['unexpected_dirs'] == ['empty_extra_dir'])
t15 = fresh(SRC_RC); os.mkfifo(os.path.join(t15, 'synapsys', 'pipe'))
rc, r = runx(base_args(t15)); chk('V21 NEG FIFO/special file -> SPECIAL_FILE, exit 3', rc == 3 and {'path': 'pipe', 'kind': 'SPECIAL_FILE'} in r['addons']['synapsys']['unexpected_links_or_special'])
t16 = fresh(SRC_RC); man_bytes = open(RC, 'rb').read().decode()
rc, r = runx(['--addons-dir', t16, '--manifest', '-', '--manifest-sha256', MS, '--only', 'synapsys'], stdin=man_bytes); chk('V22 manifest on stdin (--manifest -) with the right hash -> MATCH_ALL', rc == 0 and r['verdict'] == 'MATCH_ALL')
rc, r = runx(['--addons-dir', t16, '--manifest', '-', '--manifest-sha256', '0' * 64, '--only', 'synapsys'], stdin=man_bytes); chk('V22b NEG manifest on stdin with the wrong hash -> refuse', rc == 3 and r['verdict'] == 'REFUSE_MANIFEST_HASH_MISMATCH')
rc, r = runx(['--addons-dir', t16, '--manifest', '-', '--manifest-sha256', MS, '--only', 'synapsys'], stdin=man_bytes, code=True); chk('V23 the exact in-container invocation form (python3 -I -c "<script>" ... < manifest) -> MATCH_ALL', rc == 0 and r['verdict'] == 'MATCH_ALL')
A = fresh(SRC_RC); B = tempfile.mkdtemp(); shutil.move(os.path.join(A, 'synapsys_v19_reference'), os.path.join(B, 'synapsys_v19_reference'))
ap = lambda *ps: os.pathsep.join(ps); pa = lambda path, only='synapsys,synapsys_v19_reference': ['--addons-path', path, '--manifest', RC, '--manifest-sha256', MS, '--only', only]
rc, r = runx(pa(ap(A, B))); chk('V24 addons-path: each addon resolved in the FIRST path that holds it (synapsys in A, v19_reference in B) -> MATCH_ALL', rc == 0 and r['addons']['synapsys_v19_reference']['location'].startswith(B))
C = tempfile.mkdtemp(); shutil.copytree(SRC_RC + '/synapsys', os.path.join(C, 'synapsys'))
rc, r = runx(pa(ap(A, B, C))); chk('V25 NEG same addon in two addons-path entries -> SHADOWED_MULTIPLE_LOCATIONS, exit 3 (even if identical)', rc == 3 and r['addons']['synapsys']['status'] == 'SHADOWED_MULTIPLE_LOCATIONS')
L = os.path.join(tempfile.mkdtemp(), 'linkpath'); os.symlink(A, L)
rc, r = runx(pa(ap(L, B))); chk('V26 NEG an addons-path ENTRY that is a symlink -> refused', rc == 3 and r['path_entries'][0]['status'] == 'ADDONS_PATH_ENTRY_SYMLINK')
rc, r = runx(pa(ap(A, '/no/such/dir', B))); chk('V27 NEG addons-path entry that is not a directory -> refused', rc == 3 and r['path_entries'][1]['status'] == 'ADDONS_PATH_ENTRY_NOT_A_DIR')
rc, r = runx(pa(ap(A), 'synapsys_v19_reference')); chk('V28 NEG addon absent from every addons-path entry -> ADDON_DIR_MISSING', rc == 3 and r['addons']['synapsys_v19_reference']['status'] == 'ADDON_DIR_MISSING')

# ---- receipt-location safeguard on EVERY path (external finding 2) + symlinked receipt targets (found while fixing)
BAD = ['--manifest-sha256', '0' * 64]
def args_bad(d, extra=()): return ['--addons-dir', d, '--manifest', RC] + BAD + ['--only', 'synapsys'] + list(extra)
t20 = fresh(SRC_RC); rp = os.path.join(t20, 'synapsys', 'diag.json'); rc, r = runx(args_bad(t20, ['--receipt', rp]))
chk('V29 NEG (original regression) WRONG manifest hash + receipt inside an addon dir -> refused exit 2, NOTHING written', rc == 2 and r.get('verdict') == 'REFUSE_RECEIPT_INSIDE_EXAMINED_TREE' and not os.path.exists(rp))
ok_dir = tempfile.mkdtemp(); rp = os.path.join(ok_dir, 'diag.json'); rc, r = runx(args_bad(t20, ['--receipt', rp]))
chk('V30 manifest-hash refusal with a SAFE receipt location still writes its diagnostic (exit 3)', rc == 3 and r['verdict'] == 'REFUSE_MANIFEST_HASH_MISMATCH' and json.load(open(rp))['verdict'] == 'REFUSE_MANIFEST_HASH_MISMATCH')
t21 = fresh(SRC_RC); victim = os.path.join(t21, 'synapsys', '__manifest__.py'); before = sh(victim); rd = tempfile.mkdtemp(); os.symlink(victim, os.path.join(rd, 'r.json'))
rc, r = runx(base_args(t21, ['--receipt', os.path.join(rd, 'r.json')])); chk('V31 NEG receipt path is a SYMLINK to an addon source file -> refused exit 2, addon file byte-identical', rc == 2 and r['verdict'] == 'REFUSE_RECEIPT_PATH_IS_A_SYMLINK' and sh(victim) == before)
outside = os.path.join(tempfile.mkdtemp(), 'x.json'); open(outside, 'w').write('x'); rd = tempfile.mkdtemp(); os.symlink(outside, os.path.join(rd, 'r.json'))
rc, r = runx(base_args(t21, ['--receipt', os.path.join(rd, 'r.json')])); chk('V32 NEG receipt path is any symlink (even to a harmless file) -> refused exit 2', rc == 2 and open(outside).read() == 'x')
t22 = fresh(SRC_RC); ld = os.path.join(tempfile.mkdtemp(), 'linkdir'); os.symlink(os.path.join(t22, 'synapsys'), ld)
rc, r = runx(base_args(t22, ['--receipt', os.path.join(ld, 'r.json')])); chk('V33 NEG receipt inside a symlinked DIRECTORY that resolves into the tree -> refused exit 2', rc == 2 and not os.path.exists(os.path.join(t22, 'synapsys', 'r.json')))
t23 = fresh(SRC_RC); real = os.path.join(tempfile.mkdtemp(), 'real_synapsys'); shutil.move(os.path.join(t23, 'synapsys'), real); os.symlink(real, os.path.join(t23, 'synapsys'))
rc, r = runx(base_args(t23, ['--receipt', os.path.join(real, 'r.json')])); chk('V34 NEG addon root is a symlink and the receipt is inside ITS TARGET tree -> refused exit 2', rc == 2 and not os.path.exists(os.path.join(real, 'r.json')))
t24 = fresh(SRC_RC); rc, r = runx(base_args(t24, ['--receipt', tempfile.mkdtemp()])); chk('V35 NEG receipt path is an existing directory -> refused exit 2', rc == 2 and r['verdict'] == 'REFUSE_RECEIPT_PATH_IS_A_DIRECTORY')
t25 = fresh(SRC_RC); rp = os.path.join(t25, 'synapsys', 'd.json'); c = [sys.executable, '-I', os.path.join(root, 'verify_on_target.py'), '--addons-dir', t25, '--manifest', '/nonexistent/manifest.json', '--manifest-sha256', '0' * 64, '--receipt', rp]
r = subprocess.run(c, capture_output=True, text=True); chk('V36 NEG refusal happens BEFORE the manifest is read: missing manifest + receipt inside tree -> exit 2, not a crash', r.returncode == 2 and not os.path.exists(rp) and 'Traceback' not in r.stderr)
t26 = fresh(SRC_RC); rp = os.path.join(t26, 'synapsys', 'd.json'); rc, r = runx(['--addons-dir', t26, '--manifest', '-', '--manifest-sha256', '0' * 64, '--only', 'synapsys', '--receipt', rp], stdin='{}')
chk('V37 NEG stdin manifest with wrong hash + receipt inside tree -> exit 2, nothing written', rc == 2 and not os.path.exists(rp))

ok = all(res); print('SUMMARY pass=%d fail=%d' % (sum(res), len(res) - sum(res))); sys.exit(0 if ok else 1)
