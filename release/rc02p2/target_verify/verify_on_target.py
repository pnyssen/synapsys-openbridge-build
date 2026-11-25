#!/usr/bin/env python3
"""Destination-side byte verification of Odoo addon directories against a release manifest (stdlib only; read-only).
Run where the files LIVE (the Hostinger host console, or inside the Odoo container) - whatever transport delivered them.
  python3 verify_on_target.py --addons-dir /path/to/addons --manifest M.json --manifest-sha256 <expected> [--only a,b] [--receipt out.json]
Fails closed: exit 0 only if the manifest hash equals --manifest-sha256 AND every selected addon matches exactly
(no missing, no changed, no extra file; __pycache__/.pyc ignored). Exit 3 otherwise. It never writes inside --addons-dir."""
import argparse, hashlib, json, os, platform, socket, sys, datetime
def walk(d):
    out = {}
    for dp, dn, fn in os.walk(d):
        dn[:] = sorted(x for x in dn if x != '__pycache__')
        for f in sorted(fn):
            if f.endswith('.pyc'): continue
            p = os.path.join(dp, f)
            if os.path.islink(p): out[os.path.relpath(p, d).replace(os.sep, '/')] = {'sha256': 'SYMLINK', 'bytes': -1}; continue
            b = open(p, 'rb').read(); out[os.path.relpath(p, d).replace(os.sep, '/')] = {'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b)}
    return out
def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--addons-dir', required=True); ap.add_argument('--manifest', required=True)
    ap.add_argument('--manifest-sha256', required=True); ap.add_argument('--only'); ap.add_argument('--receipt')
    a = ap.parse_args()
    raw = open(a.manifest, 'rb').read(); msha = hashlib.sha256(raw).hexdigest()
    rec = {'verifier': 'verify_on_target/1', 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'host': socket.gethostname(), 'python': platform.python_version(),
           'addons_dir': os.path.abspath(a.addons_dir), 'manifest_sha256_observed': msha, 'manifest_sha256_expected': a.manifest_sha256.lower(), 'addons': {}}
    if msha != a.manifest_sha256.lower():
        rec['verdict'] = 'REFUSE_MANIFEST_HASH_MISMATCH'; return finish(rec, a, 3)
    m = json.loads(raw.decode('utf-8')); rec['release_label'] = m.get('label'); rec['git_commit'] = m.get('git_commit')
    names = a.only.split(',') if a.only else sorted(m['addons'])
    ok = True
    for n in names:
        if n not in m['addons']: rec['addons'][n] = {'status': 'NOT_IN_MANIFEST'}; ok = False; continue
        d = os.path.join(a.addons_dir, n)
        if not os.path.isdir(d): rec['addons'][n] = {'status': 'ADDON_DIR_MISSING'}; ok = False; continue
        want = m['addons'][n]['files']; have = walk(d)
        missing = sorted(set(want) - set(have)); extra = sorted(set(have) - set(want))
        changed = sorted(r for r in set(want) & set(have) if want[r] != have[r])
        good = not (missing or extra or changed); ok &= good
        rec['addons'][n] = {'status': 'MATCH' if good else 'DIFF', 'files_expected': len(want), 'files_found': len(have), 'missing': missing, 'extra': extra, 'changed': changed}
    rec['verdict'] = 'MATCH_ALL' if ok else 'DIFF'
    return finish(rec, a, 0 if ok else 3)
def finish(rec, a, code):
    s = json.dumps(rec, indent=1, sort_keys=True); print(s)
    if a.receipt: open(a.receipt, 'w', encoding='utf-8').write(s + '\n')
    sys.exit(code)
main()
