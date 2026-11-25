#!/usr/bin/env python3
"""Destination-side byte verification of Odoo addon directories against a release manifest (stdlib only; READ-ONLY; fails closed). v2.
Modes (exactly one):  --addons-dir DIR            examine DIR/<addon> for each addon
                      --addons-path P1:P2:...     resolve each addon the way Odoo does (first path containing <addon>/__manifest__.py);
                                                  an addon present in more than one path is refused (SHADOWED) - run this INSIDE the Odoo container
                                                  so the paths are the ones Odoo actually loads.
Manifest: --manifest FILE | --manifest -  (JSON on stdin; use with: docker exec -i CTR python3 -I -c "$(cat verify_on_target.py)" ... < manifest.json)
Required: --manifest-sha256 HEX.   Optional: --only a,b   --receipt FILE (refused if it lies inside any examined tree)
Refuses (never 'MATCH'): symlinks of ANY kind (file, directory, broken, addon root, addons-path entry), sockets/FIFOs/devices, unexpected directories,
missing/extra/changed files, shadowed addons, manifest hash mismatch. __pycache__ and .pyc are ignored. Exit 0 only on MATCH_ALL, else 3 (2 = unsafe receipt location: inside any examined tree, a symlink, or a directory - checked before anything is read or written, on every path including refusals).
Limit: a point-in-time read; it does not stop concurrent modification."""
import argparse, datetime, hashlib, json, os, platform, socket, stat, sys
def scan(root):
    """Return (files{rel:{sha256,bytes}}, dirs{rel}, problems[{path,kind}]). Never follows symlinks."""
    files, dirs, problems = {}, set(), []
    def rec(d, rel):
        try: entries = sorted(os.scandir(d), key=lambda e: e.name)
        except OSError as e: problems.append({'path': rel or '.', 'kind': 'UNREADABLE_DIR:' + e.__class__.__name__}); return
        for e in entries:
            r = (rel + '/' + e.name) if rel else e.name
            if e.is_symlink(): problems.append({'path': r, 'kind': 'SYMLINK_DIR' if e.is_dir() else ('SYMLINK_FILE' if e.is_file() else 'SYMLINK_BROKEN')}); continue
            if e.is_dir(follow_symlinks=False):
                if e.name == '__pycache__': continue
                dirs.add(r); rec(e.path, r)
            elif e.is_file(follow_symlinks=False):
                if e.name.endswith('.pyc'): continue
                try: b = open(e.path, 'rb').read()
                except OSError as ex: problems.append({'path': r, 'kind': 'UNREADABLE_FILE:' + ex.__class__.__name__}); continue
                files[r] = {'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b)}
            else: problems.append({'path': r, 'kind': 'SPECIAL_FILE'})
    rec(root, ''); return files, dirs, problems
def expected_dirs(files):
    s = set()
    for r in files:
        parts = r.split('/')[:-1]
        for i in range(1, len(parts) + 1): s.add('/'.join(parts[:i]))
    return s
def inside(path, trees):
    p = os.path.realpath(path)
    return any(p == t or p.startswith(t.rstrip(os.sep) + os.sep) for t in trees)
def protected_trees(roots):
    """realpath of each root plus every symlinked child of a root (their targets are examined/loaded trees too)."""
    t = set()
    for r in roots:
        t.add(os.path.realpath(r))
        try:
            for e in os.scandir(r):
                if e.is_symlink(): t.add(os.path.realpath(e.path))
        except OSError: pass
    return sorted(t)
def receipt_problem(receipt, roots):
    """Return a refusal reason or None. Checked BEFORE the manifest is read and before any output, so no failure path can write inside a tree."""
    if not receipt: return None
    ap = os.path.abspath(receipt)
    if os.path.islink(ap): return 'RECEIPT_PATH_IS_A_SYMLINK'
    if os.path.isdir(ap): return 'RECEIPT_PATH_IS_A_DIRECTORY'
    if inside(os.path.dirname(ap) or '.', protected_trees(roots)) or inside(ap, protected_trees(roots)): return 'RECEIPT_INSIDE_EXAMINED_TREE'
    return None
def main():
    ap = argparse.ArgumentParser(); g = ap.add_mutually_exclusive_group(required=True); g.add_argument('--addons-dir'); g.add_argument('--addons-path')
    ap.add_argument('--manifest', required=True); ap.add_argument('--manifest-sha256', required=True); ap.add_argument('--only'); ap.add_argument('--receipt')
    a = ap.parse_args()
    roots = [os.path.abspath(a.addons_dir)] if a.addons_dir else [os.path.abspath(p) for p in a.addons_path.split(os.pathsep) if p]
    why = receipt_problem(a.receipt, roots)
    if why: print(json.dumps({'verifier': 'verify_on_target/2', 'verdict': 'REFUSE_' + why, 'receipt': a.receipt}, indent=1, sort_keys=True)); sys.exit(2)
    raw = sys.stdin.buffer.read() if a.manifest == '-' else open(a.manifest, 'rb').read(); msha = hashlib.sha256(raw).hexdigest()
    rec = {'verifier': 'verify_on_target/2', 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'host': socket.gethostname(), 'python': platform.python_version(),
           'mode': 'addons-dir' if a.addons_dir else 'addons-path', 'manifest_sha256_observed': msha, 'manifest_sha256_expected': a.manifest_sha256.lower(), 'addons': {}, 'path_entries': []}
    if msha != a.manifest_sha256.lower(): rec['verdict'] = 'REFUSE_MANIFEST_HASH_MISMATCH'; return finish(rec, a, 3, roots)
    m = json.loads(raw.decode('utf-8')); rec['release_label'] = m.get('label'); rec['git_commit'] = m.get('git_commit')
    names = a.only.split(',') if a.only else sorted(m['addons'])
    ok = True
    for p in roots:
        info = {'path': p, 'is_symlink': os.path.islink(p), 'realpath': os.path.realpath(p), 'is_dir': os.path.isdir(p)}
        if info['is_symlink'] or not info['is_dir']: ok = False; info['status'] = 'ADDONS_PATH_ENTRY_SYMLINK' if info['is_symlink'] else 'ADDONS_PATH_ENTRY_NOT_A_DIR'
        else: info['status'] = 'OK'
        rec['path_entries'].append(info)
    examined = []
    for n in names:
        if n not in m['addons']: rec['addons'][n] = {'status': 'NOT_IN_MANIFEST'}; ok = False; continue
        locs = [os.path.join(p, n) for p in roots if os.path.lexists(os.path.join(p, n))]
        if not locs: rec['addons'][n] = {'status': 'ADDON_DIR_MISSING', 'searched': roots}; ok = False; continue
        if len(locs) > 1: rec['addons'][n] = {'status': 'SHADOWED_MULTIPLE_LOCATIONS', 'locations': locs}; ok = False; continue
        d = locs[0]
        if os.path.islink(d): rec['addons'][n] = {'status': 'ADDON_ROOT_SYMLINK', 'location': d, 'resolves_to': os.path.realpath(d)}; ok = False; continue
        if not os.path.isdir(d): rec['addons'][n] = {'status': 'ADDON_NOT_A_DIR', 'location': d}; ok = False; continue
        examined.append(os.path.realpath(d))
        want = m['addons'][n]['files']; have, hdirs, problems = scan(d)
        missing = sorted(set(want) - set(have)); extra = sorted(set(have) - set(want))
        changed = sorted(r for r in set(want) & set(have) if want[r] != have[r])
        unexpected_dirs = sorted(hdirs - expected_dirs(want))
        good = not (missing or extra or changed or problems or unexpected_dirs); ok &= good
        rec['addons'][n] = {'status': 'MATCH' if good else 'DIFF', 'location': d, 'files_expected': len(want), 'files_found': len(have), 'missing': missing, 'extra': extra, 'changed': changed,
                            'unexpected_links_or_special': problems, 'unexpected_dirs': unexpected_dirs}
    rec['verdict'] = 'MATCH_ALL' if ok else 'DIFF'
    return finish(rec, a, 0 if ok else 3, examined + [os.path.realpath(r) for r in roots])
def finish(rec, a, code, trees):
    why = receipt_problem(a.receipt, trees)
    if why: rec['verdict'] = 'REFUSE_' + why; print(json.dumps(rec, indent=1, sort_keys=True)); sys.exit(2)
    s = json.dumps(rec, indent=1, sort_keys=True); print(s)
    if a.receipt: open(a.receipt, 'w', encoding='utf-8').write(s + '\n')
    sys.exit(code)
main()
