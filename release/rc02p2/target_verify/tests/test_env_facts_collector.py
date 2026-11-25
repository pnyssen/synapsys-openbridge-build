"""Tests env_facts_collector.sh against a docker SHIM. Core properties: no secret ever reaches any output file/stdout/stderr; only read-only docker calls; refuses to write inside a mounted source."""
import json, os, re, shutil, subprocess, sys, tempfile
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.dirname(here); SCRIPT = os.path.join(root, 'env_facts_collector.sh')
SHIM = r'''#!/usr/bin/env bash
args=("$@"); idx=-1; for i in "${!args[@]}"; do [ "${args[$i]}" = python3 ] && idx=$i; done
if [ "$idx" -ge 0 ]; then
  fl=""; [ "${args[1]}" = -i ] && fl="-i "; echo "exec ${fl}python3 -I -c <code>" >> "$SHIM_LOG"; exec python3 "${args[@]:$((idx+1))}"
fi
echo "$*" >> "$SHIM_LOG"
case "$1" in
 inspect)
   if [ "$2" = "-f" ]; then case "$3" in
        '{{.State.Running}}') echo true;;
        '{{json .Mounts}}') python3 -c "import json,os;print(json.dumps(json.load(open(os.environ['SHIM_INSPECT']))[0]['Mounts']))";;
      esac
   else cat "$SHIM_INSPECT"; fi;;
 ps) echo "odoo20-odoo-1|odoo:20.0-20261112|Up 2 days"; echo "ss_test_i3d-db-1|postgres:16|Exited (0) 2 days ago";;
 network) echo "odoo20_default|bridge";;
 volume) echo "odoo20_filestore|local";;
 system) echo "TYPE TOTAL ACTIVE SIZE"; echo "Images 5 3 4.2GB";;
 exec) if [ "$2" = "-i" ]; then
         case "$*" in *default_transaction_read_only=on*) ;; *) echo RO_VIOLATION >> "$SHIM_LOG";; esac
         cat >/dev/null; echo "pg_version=PostgreSQL 16.4"; echo "db_size_bytes=123456789"; echo "db_encoding=UTF8|collate=en_US.UTF-8"; echo "attachments_db=0"; echo "attachments_fs=43"; echo "active_connections=3"; echo "extensions=plpgsql,unaccent"
       elif [ "$3" = "printenv" ]; then echo odoo
       elif [ "$3" = "odoo" ]; then echo "Odoo Server 20.0-20261112"; fi;;
esac
'''
def inspect_json(w, compose):
    a = os.path.join(w, 'addons'); os.makedirs(os.path.join(a, 'synapsys')); open(os.path.join(a, 'synapsys', '__manifest__.py'), 'w').write('{}')
    one = lambda name, svc: {'Name': '/' + name, 'Image': 'sha256:abc', 'Config': {'Image': 'odoo:20.0-20261112', 'Entrypoint': ['/entrypoint.sh'], 'Cmd': ['odoo', '--db_password=SECRETCLI', '--db_user=odoo', '--admin-passwd', 'SECRETSEP', '-d', 'synapsys_v20'],
        'Env': ['POSTGRES_PASSWORD=SECRETENV', 'PASSWORD=SECRETENV2', 'HOST=db'], 'Labels': {'com.docker.compose.project': 'odoo20', 'com.docker.compose.project.config_files': compose, 'com.docker.compose.service': svc}},
        'HostConfig': {'NetworkMode': 'odoo20_default', 'RestartPolicy': {'Name': 'unless-stopped'}, 'Memory': 0, 'NanoCpus': 0}, 'NetworkSettings': {'Networks': {'odoo20_default': {}}},
        'Mounts': [{'Type': 'bind', 'Source': a, 'Destination': '/mnt/extra-addons', 'RW': False}, {'Type': 'volume', 'Name': 'odoo20_filestore', 'Source': os.path.join(w, 'vol'), 'Destination': '/var/lib/odoo', 'RW': True}],
        'State': {'Status': 'running', 'Running': True, 'StartedAt': '2026-11-22T00:53:41Z', 'Health': None}}
    p = os.path.join(w, 'inspect.json'); json.dump([one('odoo20-odoo-1', 'odoo')], open(p, 'w')); return p, a
def mk():
    w = tempfile.mkdtemp(); os.makedirs(os.path.join(w, 'vol')); compose = os.path.join(w, 'docker-compose.yml')
    open(compose, 'w').write('services:\n  db:\n    image: postgres:16\n    environment:\n      POSTGRES_PASSWORD: SECRETCOMPOSE\n      POSTGRES_USER: odoo\n  odoo:\n    image: odoo:20.0-20261112\n    environment:\n      - PASSWORD=SECRETCOMPOSE2\n      - HOST=db\n    command: ["--db_password=SECRETCOMPOSE3"]\n')
    ip, addons = inspect_json(w, compose)
    cf = os.path.join(w, 'odoo.conf'); open(cf, 'w').write('[options]\naddons_path = /mnt/extra-addons\nadmin_passwd = SECRETADMIN\ndb_password = SECRETPW\ndb_user = odoo\ndb_host = db\nworkers = 2\ndata_dir = /var/lib/odoo\n')
    cl = os.path.join(w, 'cmdline'); open(cl, 'wb').write(b'odoo\0--db_password=SECRETCLI\0--admin-passwd\0SECRETSEP\0')
    sb = os.path.join(w, 'bin'); os.mkdir(sb); d = os.path.join(sb, 'docker'); open(d, 'w').write(SHIM); os.chmod(d, 0o755)
    return dict(w=w, ip=ip, cf=cf, cl=cl, sb=sb, addons=addons)
def run(m, env_extra=None):
    out = os.path.join(m['w'], 'out'); log = os.path.join(m['w'], 'docker.log')
    env = {'PATH': m['sb'] + os.pathsep + os.environ['PATH'], 'SHIM_LOG': log, 'SHIM_INSPECT': m['ip'], 'OUT': out, 'HOME': m['w'], 'ODOO_CONF_PATH': m['cf'], 'ODOO_CMDLINE_PATH': m['cl']}; env.update(env_extra or {})
    r = subprocess.run(['/bin/bash', SCRIPT], capture_output=True, text=True, env=env)
    return r.returncode, r.stdout, r.stderr, out, (open(log).read() if os.path.exists(log) else '')
res = []
def chk(n, c, d=''): c = bool(c); res.append(c); print(('PASS ' if c else 'FAIL ') + n + (' :: ' + d if d else ''))
m = mk(); rc, so, se, out, log = run(m)
chk('F1 collects: exit 0, COLLECTED, an INDEX with hashes of every output file', rc == 0 and 'ENV_FACTS_VERDICT=COLLECTED' in so and len(json.load(open(os.path.join(out, 'INDEX.json')))['files_sha256']) >= 8, se[-150:])
blob = so + se + ''.join(open(os.path.join(dp, f), errors='replace').read() for dp, dn, fn in os.walk(out) for f in fn)
leaks = [s for s in ('SECRETCLI', 'SECRETSEP', 'SECRETENV', 'SECRETENV2', 'SECRETCOMPOSE', 'SECRETCOMPOSE2', 'SECRETCOMPOSE3', 'SECRETADMIN', 'SECRETPW') if s in blob]
chk('F2 NEG secrets hygiene: no secret from env values, command line (inline AND separate-token), compose file, or odoo.conf appears in any output', not leaks, 'leaked=%s over %d chars' % (leaks, len(blob)))
oc = json.load(open(os.path.join(out, 'odoo_container.json')))
chk('F3 container facts kept: mounts (source/destination/type), networks, image, compose project/files, env NAMES only', {x['Destination'] for x in oc['Mounts']} == {'/mnt/extra-addons', '/var/lib/odoo'} and oc['Networks'] == ['odoo20_default'] and oc['ComposeProject'] == 'odoo20' and 'POSTGRES_PASSWORD' in oc['EnvNamesOnly'] and not any('=' in e for e in oc['EnvNamesOnly']))
cfgw = json.load(open(os.path.join(out, 'odoo_config_whitelist.json')))
chk('F4 Odoo config whitelist carries addons_path, data_dir, workers, db_user, db_host; never db_password/admin_passwd', cfgw['conf_whitelisted'].get('addons_path') == '/mnt/extra-addons' and cfgw['conf_whitelisted'].get('workers') == '2' and 'db_password' not in cfgw['conf_whitelisted'] and 'admin_passwd' not in cfgw['conf_whitelisted'] and '--admin-passwd' in cfgw['cmdline_masked'] and 'SECRETSEP' not in json.dumps(cfgw))
chk('F5 DB sizing facts and host capacity recorded (db_size_bytes, attachments, disk/mem)', 'db_size_bytes=123456789' in open(os.path.join(out, 'db_facts.txt')).read() and os.path.exists(os.path.join(out, 'host_capacity.txt')) and 'Mem' in open(os.path.join(out, 'host_capacity.txt')).read())
cj = json.load(open(os.path.join(out, 'compose_files.json'))); masked = [f for f in os.listdir(out) if f.endswith('.masked.yml')]
chk('F6 compose file hashed and kept only in MASKED form (secret values replaced, structure kept)', cj and cj[0].get('sha256') and masked and 'image: postgres:16' in open(os.path.join(out, masked[0])).read() and 'MASKED' in open(os.path.join(out, masked[0])).read())
lines = [l for l in log.splitlines() if l]
ALLOWED = re.compile(r'^(inspect( -f \S+.*)? \S+|inspect \S+|ps -a --format .*|network ls --format .*|volume ls --format .*|system df|exec \S+ printenv POSTGRES_USER|exec \S+ odoo --version|exec python3 -I -c <code>|exec -i python3 -I -c <code>|exec -i -e PGOPTIONS=-c default_transaction_read_only=on \S+ psql .*)$')
chk('F7 call discipline: only inspect / ps / network ls / volume ls / system df / printenv / odoo --version / in-container python reading config / read-only psql', lines and all(ALLOWED.match(l) for l in lines) and 'RO_VIOLATION' not in log and not re.search(r'\b(run|rm|restart|stop|start|cp|commit|create|kill|prune|pull|build|compose)\b', ' '.join(l.split(' ')[0] for l in lines)), '%d calls' % len(lines))
m = mk(); od = os.path.join(m['addons'], 'facts'); rc, so, se, out, log = run(m, {'OUT': od}); chk('F8 NEG OUT inside a mounted source dir -> refused exit 2, nothing written', rc == 2 and not os.path.exists(od))
m = mk(); rc, so, se, out, log = run(m, {'DBNAME': 'x;rm -rf /'}); chk('F9 NEG DBNAME with shell metacharacters -> refused exit 2 before any docker call', rc == 2 and log == '')
print('SUMMARY pass=%d fail=%d' % (sum(res), len(res) - sum(res))); sys.exit(0 if all(res) else 1)
