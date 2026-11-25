"""Tests p0_prestate_receipt.sh against a docker SHIM (no real docker): discovery, fail-closed codes, read-only call discipline."""
import json, os, re, shutil, stat, subprocess, sys, tempfile
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.dirname(here); P0 = os.path.join(root, 'p0_prestate_receipt.sh')
SRC_BASE = sys.argv[1]
SHIM = r'''#!/usr/bin/env bash
echo "$*" >> "$SHIM_LOG"
case "$1" in
 inspect) fmt="$3"; name="$4"
   case "$fmt" in
    '{{.State.Running}}') [ "$name" = "${SHIM_DOWN:-}" ] && echo false || echo true;;
    '{{json .Mounts}}') cat "$SHIM_MOUNTS";;
    '{{.Image}} {{.Config.Image}} {{.State.StartedAt}}') echo "sha256:abc odoo:20.0-20261112 2026-11-23T00:00:00Z";;
   esac;;
 exec) if [ "$2" = "-i" ]; then
         case "$*" in *default_transaction_read_only=on*) ;; *) echo RO_VIOLATION >> "$SHIM_LOG";; esac
         cat >/dev/null; [ "${SHIM_PSQL_FAIL:-0}" = 1 ] && { echo "psql: error" >&2; exit 2; }
         echo "database.uuid=${SHIM_UUID-TEST-UUID-1234}"; echo "module=synapsys|installed|20.0.2.4.0"
         echo "ir_ui_view.visibility.default='public'::character varying"; echo "ir_ui_view.visibility.exists=1"
       else echo odoo; fi;;
esac
'''
res = []
def chk(n, c, d=''): c = bool(c); res.append(c); print(('PASS ' if c else 'FAIL ') + n + (' :: ' + d if d else ''))
def mk(extra_dirs=0, tweak=None, no_mount=False):
    w = tempfile.mkdtemp(); a = os.path.join(w, 'addons1'); shutil.copytree(SRC_BASE, a)
    if tweak: tweak(a)
    mounts = [] if no_mount else [{'Source': a, 'Destination': '/mnt/extra-addons'}]
    for i in range(extra_dirs):
        b = os.path.join(w, 'addons%d' % (i + 2)); shutil.copytree(SRC_BASE, b); mounts.append({'Source': b, 'Destination': '/x%d' % i})
    mj = os.path.join(w, 'mounts.json'); json.dump(mounts, open(mj, 'w'))
    sb = os.path.join(w, 'bin'); os.mkdir(sb); d = os.path.join(sb, 'docker'); open(d, 'w').write(SHIM); os.chmod(d, 0o755)
    nb = os.path.join(w, 'nodocker'); os.mkdir(nb)
    for c in ['bash', 'python3', 'sha256sum', 'cut', 'grep', 'tr', 'head', 'sed', 'date', 'mkdir', 'cat', 'dirname', 'wc', 'sort']:
        p = shutil.which(c); os.symlink(p, os.path.join(nb, c)) if p else None
    return w, a, mj, sb, nb
def run(w, mj, path_dir, env_extra=None):
    out = os.path.join(w, 'out'); log = os.path.join(w, 'docker.log')
    env = {'PATH': path_dir + os.pathsep + os.environ['PATH'] if path_dir.endswith('bin') else path_dir, 'SHIM_LOG': log, 'SHIM_MOUNTS': mj, 'OUT': out, 'HOME': w}
    env.update(env_extra or {})
    r = subprocess.run(['/bin/bash', P0], capture_output=True, text=True, env=env)
    return r.returncode, r.stdout, r.stderr, out, (open(log).read() if os.path.exists(log) else '')
ALLOWED = re.compile(r'^(inspect -f \S+.* \S+|exec \S+ printenv POSTGRES_USER|exec -i -e PGOPTIONS=-c default_transaction_read_only=on \S+ psql .*)$')
w, a, mj, sb, nb = mk(); rc, so, se, out, log = run(w, mj, sb)
rec = json.load(open(os.path.join(out, 'p0_receipt.json'))) if os.path.exists(os.path.join(out, 'p0_receipt.json')) else {}
chk('P1 happy path: discovery finds the one addons mount; baseline on disk -> P0_MATCH_ALL exit 0', rc == 0 and 'P0_VERDICT=P0_MATCH_ALL' in so and rec.get('database_uuid') == 'TEST-UUID-1234' and rec['verifier']['verdict'] == 'MATCH_ALL', 'rc=%d' % rc)
lines = [l for l in log.splitlines() if l]
chk('P2 read-only discipline: every docker call is inspect / printenv / psql with read-only session; no cp/run/rm/restart/compose/stop', lines and all(ALLOWED.match(l) for l in lines) and 'RO_VIOLATION' not in log and not re.search(r'\b(cp|run|rm|restart|stop|start|up|down|compose|kill|commit|update|create)\b', ' '.join(l.split(' ', 1)[0] for l in lines)), '%d calls' % len(lines))
chk('P3 receipt carries DB facts incl. the F5 fact (ir_ui_view.visibility default) and compose hash line', any(f.startswith('ir_ui_view.visibility.default=') for f in rec.get('db_facts', [])) and rec.get('compose_sha256'))
def tw(a): p = os.path.join(a, 'synapsys', 'controllers', 'arch_map.py'); b = bytearray(open(p, 'rb').read()); b[100] ^= 1; open(p, 'wb').write(bytes(b))
w, a, mj, sb, nb = mk(tweak=tw); rc, so, se, out, log = run(w, mj, sb)
rec = json.load(open(os.path.join(out, 'p0_receipt.json')))
chk('P4 NEG on-disk single-bit drift vs baseline -> P0_DIFF exit 3, changed file named in receipt', rc == 3 and rec['verdict'] == 'P0_DIFF' and rec['verifier']['addons']['synapsys']['changed'] == ['controllers/arch_map.py'])
w, a, mj, sb, nb = mk(); rc, so, se, out, log = run(w, mj, nb)
chk('P5 NEG docker not installed -> refuse exit 2 with explicit reason', rc == 2 and 'prerequisite missing: docker' in se and 'P0_VERDICT=REFUSE_2' in so)
w, a, mj, sb, nb = mk(); rc, so, se, out, log = run(w, mj, sb, {'SHIM_DOWN': 'odoo20-db-1'})
chk('P6 NEG DB container not running -> exit 4', rc == 4 and 'not running' in se)
w, a, mj, sb, nb = mk(extra_dirs=1); rc, so, se, out, log = run(w, mj, sb)
chk('P7 NEG two candidate addon mounts -> exit 4 (ambiguous), mounts printed for the operator', rc == 4 and 'found 2 candidates' in se)
rc, so, se, out, log = run(w, mj, sb, {'ADDONS': a, 'OUT': os.path.join(w, 'out2')})
chk('P8 explicit ADDONS override resolves the ambiguity -> exit 0', rc == 0)
w, a, mj, sb, nb = mk(no_mount=True); rc, so, se, out, log = run(w, mj, sb)
chk('P9 NEG no mount contains synapsys -> exit 4', rc == 4 and 'found 0 candidates' in se)
w, a, mj, sb, nb = mk(); rc, so, se, out, log = run(w, mj, sb, {'MSHA': '0' * 64})
chk('P10 NEG manifest hash differs from the expected -> exit 3 BEFORE any docker call', rc == 3 and log == '' and 'P0_VERDICT=REFUSE_3' in so)
w, a, mj, sb, nb = mk(); rc, so, se, out, log = run(w, mj, sb, {'SHIM_UUID': ''})
chk('P11 NEG empty database.uuid -> exit 5 P0_DB_FACTS_UNAVAILABLE (cannot claim a prestate without it)', rc == 5 and 'P0_DB_FACTS_UNAVAILABLE' in so)
w, a, mj, sb, nb = mk(); rc, so, se, out, log = run(w, mj, sb, {'SHIM_PSQL_FAIL': '1'})
chk('P12 NEG psql failure -> exit 5', rc == 5)
w, a, mj, sb, nb = mk(); rc, so, se, out, log = run(w, mj, sb, {'OUT': os.path.join(a, 'receipts')})
chk('P13 NEG OUT inside the addons dir -> refuse exit 2 (receipt must never touch the addon tree)', rc == 2 and 'OUT must not be inside' in se)
w, a, mj, sb, nb = mk(); before = sorted((dp, f) for dp, dn, fn in os.walk(a) for f in fn); rc, so, se, out, log = run(w, mj, sb); after = sorted((dp, f) for dp, dn, fn in os.walk(a) for f in fn)
chk('P14 addons tree unchanged by a P0 run (file set identical)', rc == 0 and before == after, '%d files' % len(before))
print('SUMMARY pass=%d fail=%d' % (sum(res), len(res) - sum(res))); sys.exit(0 if all(res) else 1)
