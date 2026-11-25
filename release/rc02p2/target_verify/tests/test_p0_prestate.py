"""Tests p0_prestate_receipt.sh (v2) against a docker SHIM: in-container python calls run the REAL python3 on the host against a fixture
'container' (conf + cmdline files, addons dirs). Checks discovery, fail-closed codes, view conflict, secrets hygiene and read-only call discipline."""
import json, os, re, shutil, subprocess, sys, tempfile
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.dirname(here); P0 = os.path.join(root, 'p0_prestate_receipt.sh')
SRC_BASE = sys.argv[1]
SHIM = r'''#!/usr/bin/env bash
args=("$@"); idx=-1; for i in "${!args[@]}"; do [ "${args[$i]}" = python3 ] && idx=$i; done
if [ "$idx" -ge 0 ]; then
  ctr=${args[$((idx-1))]}; fl=""; [ "${args[0]}" = exec ] && [ "${args[1]}" = -i ] && fl="-i "
  echo "exec ${fl}${ctr} python3 -I -c <code> ${args[*]:$((idx+4))}" >> "$SHIM_LOG"
  exec python3 "${args[@]:$((idx+1))}"
fi
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
def mk(conf_extra='', cmdline=None, tweak=None, extra_path_dirs=(), mounts_override=None, conf_addons=None, conf=True):
    w = tempfile.mkdtemp(); a = os.path.join(w, 'addons1'); shutil.copytree(SRC_BASE, a)
    if tweak: tweak(a)
    others = []
    for i, name in enumerate(extra_path_dirs):
        d = os.path.join(w, name); shutil.copytree(SRC_BASE, d); others.append(d)
    paths = conf_addons if conf_addons is not None else [a] + others
    cf = os.path.join(w, 'odoo.conf')
    if conf: open(cf, 'w').write('[options]\naddons_path = %s\nadmin_passwd = SECRETADMIN\ndb_password = SECRETPW\ndb_host = db\n%s\n' % (','.join(paths), conf_extra))
    cl = os.path.join(w, 'cmdline'); open(cl, 'wb').write(('\0'.join(['odoo', '--db_password=SECRETCLI'] + (cmdline or [])) + '\0').encode())
    mounts = mounts_override if mounts_override is not None else [{'Source': p, 'Destination': p, 'Type': 'bind'} for p in paths]
    mj = os.path.join(w, 'mounts.json'); json.dump(mounts, open(mj, 'w'))
    sb = os.path.join(w, 'bin'); os.mkdir(sb); d = os.path.join(sb, 'docker'); open(d, 'w').write(SHIM); os.chmod(d, 0o755)
    nb = os.path.join(w, 'nodocker'); os.mkdir(nb)
    for c in ['bash', 'python3', 'sha256sum', 'cut', 'grep', 'tr', 'head', 'sed', 'date', 'mkdir', 'cat', 'dirname', 'wc', 'sort', 'printf']:
        p = shutil.which(c); os.symlink(p, os.path.join(nb, c)) if p else None
    return dict(w=w, a=a, others=others, cf=cf, cl=cl, mj=mj, sb=sb, nb=nb)
def run(m, path_dir=None, env_extra=None):
    out = os.path.join(m['w'], 'out'); log = os.path.join(m['w'], 'docker.log')
    env = {'PATH': (path_dir or m['sb']) + (os.pathsep + os.environ['PATH'] if (path_dir or m['sb']).endswith('bin') else ''), 'SHIM_LOG': log, 'SHIM_MOUNTS': m['mj'], 'OUT': out, 'HOME': m['w'],
           'ODOO_CONF_PATH': m['cf'], 'ODOO_CMDLINE_PATH': m['cl'], 'COMPOSE': os.path.join(m['w'], 'docker-compose.yml')}
    open(env['COMPOSE'], 'w').write('services: {}\n'); env.update(env_extra or {})
    r = subprocess.run(['/bin/bash', P0], capture_output=True, text=True, env=env)
    rec = json.load(open(os.path.join(out, 'p0_receipt.json'))) if os.path.exists(os.path.join(out, 'p0_receipt.json')) else {}
    return r.returncode, r.stdout, r.stderr, out, (open(log).read() if os.path.exists(log) else ''), rec
ALLOWED = re.compile(r'^(inspect -f \S+.* \S+|exec \S+ printenv POSTGRES_USER|exec \S+ python3 -I -c <code> \S+ \S+|exec -i \S+ python3 -I -c <code> --addons-path \S+ --manifest - --manifest-sha256 \S+ --only \S+|exec -i -e PGOPTIONS=-c default_transaction_read_only=on \S+ psql .*)$')
m = mk(); rc, so, se, out, log, rec = run(m)
chk('P1 happy path: Odoo config read in-container, addons verified in-container AND on the host mount -> P0_MATCH_ALL exit 0', rc == 0 and 'P0_VERDICT=P0_MATCH_ALL' in so and rec['container_view']['verdict'] == 'MATCH_ALL' and rec['host_view']['verdict'] == 'MATCH_ALL' and rec['database_uuid'] == 'TEST-UUID-1234' and rec['evidence_class'] == 'TWO_VIEW' and rec['qualifies_as_two_view_gate_evidence'] is True and 'EVIDENCE_CLASS=TWO_VIEW' in so, 'rc=%d se=%s' % (rc, se[-120:]))
lines = [l for l in log.splitlines() if l]
chk('P2 read-only discipline: only inspect / printenv / in-container python3 over stdin / psql with a read-only session; no cp/run/rm/restart/compose/stop/write verbs', lines and all(ALLOWED.match(l) for l in lines) and 'RO_VIOLATION' not in log and not re.search(r'\b(cp|run|rm|restart|stop|start|up|down|compose|kill|commit|update|create|tee)\b', ' '.join(l.split(' ')[0] for l in lines)) and any('exec -i' in l and '--manifest -' in l for l in lines), '%d calls' % len(lines))
chk('P3 receipt carries DB facts incl. the F5 fact, compose hash, and the whitelisted Odoo config (source recorded)', any(f.startswith('ir_ui_view.visibility.default=') for f in rec['db_facts']) and rec['compose_sha256'] and rec['odoo_config_whitelist']['addons_path_source'] == 'conf')
def drift(a): p = os.path.join(a, 'synapsys', 'controllers', 'arch_map.py'); b = bytearray(open(p, 'rb').read()); b[100] ^= 1; open(p, 'wb').write(bytes(b))
m = mk(tweak=drift); rc, so, se, out, log, rec = run(m)
chk('P4 NEG on-disk single-bit drift -> P0_DIFF exit 3; changed file named', rc == 3 and rec['verdict'] == 'P0_DIFF' and rec['container_view']['addons']['synapsys']['changed'] == ['controllers/arch_map.py'])
m = mk(); rc, so, se, out, log, rec = run(m, path_dir=m['nb']); chk('P5 NEG docker not installed -> refuse exit 2', rc == 2 and 'prerequisite missing: docker' in se)
m = mk(); rc, so, se, out, log, rec = run(m, env_extra={'SHIM_DOWN': 'odoo20-db-1'}); chk('P6 NEG DB container not running -> exit 4', rc == 4 and 'not running' in se)
m = mk(extra_path_dirs=['addons2']); rc, so, se, out, log, rec = run(m)
chk('P7 NEG the same addon exists in two Odoo addons_path entries -> SHADOWED, P0_DIFF exit 3 (shadowing proven, not assumed)', rc == 3 and rec['container_view']['addons']['synapsys']['status'] == 'SHADOWED_MULTIPLE_LOCATIONS')
m = mk(conf=False, cmdline=[]); rc, so, se, out, log, rec = run(m); chk('P8 NEG no addons_path in config or command line -> exit 4', rc == 4 and 'no addons_path' in se, 'rc=%d se=%s' % (rc, se[-200:].replace(chr(10), ' | ')))
m = mk(conf_addons=['/definitely/not/here'], cmdline=['--addons-path=PLACEHOLDER']); open(m['cl'], 'wb').write(('\0'.join(['odoo', '--db_password=SECRETCLI', '--addons-path=' + m['a']]) + '\0').encode())
m['mj'] and json.dump([{'Source': m['a'], 'Destination': m['a']}], open(m['mj'], 'w')); rc, so, se, out, log, rec = run(m)
chk('P9 command-line --addons-path overrides the config file (as Odoo does) -> uses cmdline, exit 0', rc == 0 and rec['odoo_config_whitelist']['addons_path_source'] == 'cmdline')
m = mk(); rc, so, se, out, log, rec = run(m, env_extra={'MSHA': '0' * 64}); chk('P10 NEG manifest hash differs from expected -> exit 3 BEFORE any docker call', rc == 3 and log == '' and 'P0_VERDICT=REFUSE_3' in so)
m = mk(); rc, so, se, out, log, rec = run(m, env_extra={'SHIM_UUID': ''}); chk('P11 NEG empty database.uuid -> exit 5 (no prestate claim without it)', rc == 5 and 'P0_DB_FACTS_UNAVAILABLE' in so)
m = mk(); rc, so, se, out, log, rec = run(m, env_extra={'SHIM_PSQL_FAIL': '1'}); chk('P12 NEG psql failure -> exit 5', rc == 5)
m = mk(); od = os.path.join(m['a'], 'receipts'); rc, so, se, out, log, rec = run(m, env_extra={'OUT': od}); chk('P13 NEG OUT inside the addons dir -> refuse exit 2 and NOTHING written there', rc == 2 and not os.path.exists(od))
m = mk(); before = sorted((dp, f) for dp, dn, fn in os.walk(m['a']) for f in fn); rc, so, se, out, log, rec = run(m); after = sorted((dp, f) for dp, dn, fn in os.walk(m['a']) for f in fn)
chk('P14 addons tree unchanged by a P0 run', rc == 0 and before == after, '%d files' % len(before))
def linkdir(a): o = tempfile.mkdtemp(); os.symlink(o, os.path.join(a, 'synapsys', 'linked_dir'))
m = mk(tweak=linkdir); rc, so, se, out, log, rec = run(m); chk('P15 NEG symlinked directory inside an addon -> P0_DIFF exit 3 (the reported verifier defect, now through the whole P0 path)', rc == 3 and {'path': 'linked_dir', 'kind': 'SYMLINK_DIR'} in rec['container_view']['addons']['synapsys']['unexpected_links_or_special'])
m = mk(conf_extra='db_name = some_other_db'); rc, so, se, out, log, rec = run(m); chk('P16 NEG Odoo is configured for a different database than the one checked -> exit 4', rc == 4 and 'some_other_db' in se)
m = mk(); host = os.path.join(m['w'], 'hostcopy'); shutil.copytree(m['a'], host); drift(host); json.dump([{'Source': host, 'Destination': m['a']}], open(m['mj'], 'w')); rc, so, se, out, log, rec = run(m)
chk('P17 NEG container view matches but the host mount source differs -> P0_VIEW_CONFLICT exit 3', rc == 3 and rec['verdict'] == 'P0_VIEW_CONFLICT' and 'HOST_VIEW=DIFF' in so)
m = mk(mounts_override=[]); rc, so, se, out, log, rec = run(m)
chk('P18 host mount mapping unavailable -> NOT a full pass: P0_CONTAINER_VERIFIED_HOST_UNAVAILABLE, exit 6, evidence_class CONTAINER_ONLY, not gate evidence', rc == 6 and 'P0_VERDICT=P0_CONTAINER_VERIFIED_HOST_UNAVAILABLE' in so and rec['evidence_class'] == 'CONTAINER_ONLY' and rec['qualifies_as_two_view_gate_evidence'] is False and rec['host_view'] == 'UNAVAILABLE' and 'Do not treat this as full verification' in so and rec['container_view']['verdict'] == 'MATCH_ALL')
m = mk(mounts_override=[]); alt = os.path.join(m['w'], 'altcopy'); shutil.copytree(m['a'], alt); rc, so, se, out, log, rec = run(m, env_extra={'ADDONS': alt})
chk('P18b NEG an ADDONS override that is NOT the mount source cannot corroborate -> still exit 6 CONTAINER_ONLY with the reason recorded', rc == 6 and rec['evidence_class'] == 'CONTAINER_ONLY' and 'NOT_THE_MOUNT_SOURCE' in rec['host_view_note'])
m = mk(); rc, so, se, out, log, rec = run(m, env_extra={'ADDONS': m['a']}); chk('P18c ADDONS override equal to the mount source of the single addons_path entry -> TWO_VIEW exit 0', rc == 0 and rec['evidence_class'] == 'TWO_VIEW')
m = mk(extra_path_dirs=['addons2']); rc, so, se, out, log, rec = run(m, env_extra={'ADDONS': m['a']}); chk('P18d NEG override with SEVERAL addons_path entries cannot stand in for the mapping -> exit 6 or 3, never 0', rc in (3, 6) and rc != 0)
m = mk(); rc, so, se, out, log, rec = run(m); blob = so + se + ''.join(open(os.path.join(dp, f), errors='replace').read() for dp, dn, fn in os.walk(out) for f in fn)
chk('P19 NEG secrets hygiene: db_password / admin_passwd / --db_password never appear in stdout, stderr or any file in OUT', rc == 0 and not re.search('SECRETPW|SECRETADMIN|SECRETCLI', blob), '%d chars scanned' % len(blob))
m = mk(); lk = os.path.join(m['w'], 'link_addons'); os.symlink(m['a'], lk); open(m['cf'], 'w').write('[options]\naddons_path = %s\n' % lk); json.dump([{'Source': m['a'], 'Destination': lk}], open(m['mj'], 'w')); rc, so, se, out, log, rec = run(m)
chk('P20 NEG an addons_path ENTRY that is a symlink -> refused, exit 3', rc == 3 and rec['container_view']['path_entries'][0]['status'] == 'ADDONS_PATH_ENTRY_SYMLINK')
print('SUMMARY pass=%d fail=%d' % (sum(res), len(res) - sum(res))); sys.exit(0 if all(res) else 1)
