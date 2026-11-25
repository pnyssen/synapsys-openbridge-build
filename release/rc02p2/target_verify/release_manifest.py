#!/usr/bin/env python3
"""Write a release manifest for the addon directories under <tree> (stdlib only).
usage: release_manifest.py <tree> <out.json> --commit <sha> --label <text> [--addons a,b,...]
Per-addon identity = sha256 over sorted lines '<addon>/<relpath>\\t<sha256>\\t<bytes>\\n' (same rule as rc02p2_reproduce_and_check.py)."""
import argparse, hashlib, json, os, sys
def walk(addon_dir):
    """Hash files; REFUSE on any symlink (file or directory), special file, or symlinked addon root. Never follows links."""
    if os.path.islink(addon_dir): raise SystemExit('REFUSE: addon root is a symlink: ' + addon_dir)
    out = {}
    def rec(d, rel):
        for e in sorted(os.scandir(d), key=lambda e: e.name):
            r = (rel + '/' + e.name) if rel else e.name
            if e.is_symlink(): raise SystemExit('REFUSE: symlink in addon tree: ' + e.path)
            if e.is_dir(follow_symlinks=False):
                if e.name != '__pycache__': rec(e.path, r)
            elif e.is_file(follow_symlinks=False):
                if e.name.endswith('.pyc'): continue
                b = open(e.path, 'rb').read(); out[r] = {'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b)}
            else: raise SystemExit('REFUSE: special file in addon tree: ' + e.path)
    rec(addon_dir, ''); return out
def identity(name, files):
    return hashlib.sha256(''.join('%s/%s\t%s\t%d\n' % (name, r, v['sha256'], v['bytes']) for r, v in sorted(files.items())).encode()).hexdigest()
def build(tree, addons=None):
    names = addons or sorted(d for d in os.listdir(tree) if os.path.exists(os.path.join(tree, d, '__manifest__.py')))
    res = {}
    for n in names:
        files = walk(os.path.join(tree, n)); res[n] = {'identity': identity(n, files), 'file_count': len(files), 'files': files}
    return res
if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('tree'); ap.add_argument('out'); ap.add_argument('--commit', required=True); ap.add_argument('--label', required=True); ap.add_argument('--addons')
    a = ap.parse_args()
    m = {'schema': 'synapsys.release-manifest/1', 'label': a.label, 'git_commit': a.commit, 'addons': build(a.tree, a.addons.split(',') if a.addons else None)}
    open(a.out, 'w', encoding='utf-8').write(json.dumps(m, indent=1, sort_keys=True) + '\n')
    print(a.out, hashlib.sha256(open(a.out, 'rb').read()).hexdigest(), {k: v['identity'][:12] for k, v in m['addons'].items()})
