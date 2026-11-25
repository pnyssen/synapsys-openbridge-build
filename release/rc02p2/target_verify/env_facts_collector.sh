#!/usr/bin/env bash
# ENV FACTS COLLECTOR v1 - READ-ONLY. Collects the non-secret environment facts needed to build the backup/restore/rehearsal stage (G2) for the Hostinger Odoo 20 instance.
# Exit: 0 collected | 2 prerequisite missing/unsafe | 4 containers not found/not running
# Secrets: never printed. Env values are NOT collected (names only); command-line/compose values matching password/secret/token/key patterns are masked; db_password/admin_passwd are never read.
# Uses only: docker inspect/ps/network ls/volume ls/system df, docker exec (python3 reading config, read-only psql SELECTs, odoo --version), df, free, sha256sum, python3. Writes ONLY into $OUT.
set -u -o pipefail
ODOO_CTR=${ODOO_CTR:-odoo20-odoo-1}; DB_CTR=${DB_CTR:-odoo20-db-1}; DBNAME=${DBNAME:-synapsys_v20}
ODOO_CONF_PATH=${ODOO_CONF_PATH:-/etc/odoo/odoo.conf}; ODOO_CMDLINE_PATH=${ODOO_CMDLINE_PATH:-/proc/1/cmdline}
OUT=${OUT:-./env_facts_$(date -u +%Y%m%dT%H%M%SZ)}
say(){ printf '%s\n' "$*" >&2; }; die(){ code=$1; shift; say "ENV_FACTS_REFUSE[$code]: $*"; echo "ENV_FACTS_VERDICT=REFUSE_$code"; exit "$code"; }
for c in docker python3 sha256sum; do command -v "$c" >/dev/null 2>&1 || die 2 "prerequisite missing: $c"; done
[[ "$DBNAME" =~ ^[A-Za-z0-9_.-]+$ ]] || die 2 "DBNAME has unexpected characters"
for c in "$ODOO_CTR" "$DB_CTR"; do [ "$(docker inspect -f '{{.State.Running}}' "$c" 2>/dev/null)" = "true" ] || die 4 "container not running or not found: $c"; done
MOUNTS_JSON=$(docker inspect -f '{{json .Mounts}}' "$ODOO_CTR" 2>/dev/null) || die 4 "mount inspect failed"
MOUNTS_JSON="$MOUNTS_JSON" python3 -I - "$OUT" <<'PY' || die 2 "OUT must not be inside a mounted source dir (nothing was written)"
import json, os, sys
out = os.path.realpath(sys.argv[1])
for m in json.loads(os.environ['MOUNTS_JSON']):
    s = m.get('Source')
    if s:
        s = os.path.realpath(s)
        if out == s or out.startswith(s.rstrip(os.sep) + os.sep): sys.exit(1)
PY
mkdir -p "$OUT" || die 2 "cannot create $OUT"; OUT=$(cd "$OUT" && pwd)
MASK_PY=$(cat <<'PY'
import json, re, sys
SECRET = re.compile(r'(?i)(pass(word|wd)?|pwd|secret|token|api[_-]?key|private[_-]?key|credential)')
def mask_text(t):
    out = []
    for line in t.splitlines():
        m = re.match(r'^(\s*[-\w."\']*?)(\s*[:=]\s*)(.*)$', line)
        if m and SECRET.search(m.group(1)) and m.group(3).strip(): out.append(m.group(1) + m.group(2) + '***MASKED***')
        elif SECRET.search(line) and re.search(r'[:=]\s*\S', line): out.append(re.sub(r'([:=]\s*)\S.*$', r'\1***MASKED***', line))
        else: out.append(line)
    return '\n'.join(out) + '\n'
def mask_args(a):
    out, skip = [], False
    for x in (a or []):
        if skip: out.append('***MASKED***'); skip = False; continue
        if x.startswith('-') and SECRET.search(x):
            if '=' in x: out.append(x.split('=', 1)[0] + '=***MASKED***')
            else: out.append(x); skip = True                    # secret passed as the NEXT token
        else: out.append(x)
    return out
def slim(c):
    cfg = c.get('Config', {}); hc = c.get('HostConfig', {}); ns = c.get('NetworkSettings', {})
    return {'Name': c.get('Name'), 'Image': c.get('Image'), 'ConfigImage': cfg.get('Image'), 'Entrypoint': mask_args(cfg.get('Entrypoint')), 'Cmd': mask_args(cfg.get('Cmd')),
            'EnvNamesOnly': sorted(e.split('=', 1)[0] for e in (cfg.get('Env') or [])), 'WorkingDir': cfg.get('WorkingDir'), 'User': cfg.get('User'),
            'ComposeProject': (cfg.get('Labels') or {}).get('com.docker.compose.project'), 'ComposeConfigFiles': (cfg.get('Labels') or {}).get('com.docker.compose.project.config_files'),
            'ComposeWorkingDir': (cfg.get('Labels') or {}).get('com.docker.compose.project.working_dir'), 'ComposeService': (cfg.get('Labels') or {}).get('com.docker.compose.service'),
            'Mounts': [{'Type': m.get('Type'), 'Source': m.get('Source'), 'Destination': m.get('Destination'), 'RW': m.get('RW'), 'Name': m.get('Name')} for m in c.get('Mounts', [])],
            'NetworkMode': hc.get('NetworkMode'), 'Networks': sorted((ns.get('Networks') or {}).keys()), 'RestartPolicy': hc.get('RestartPolicy'), 'MemoryBytes': hc.get('Memory'), 'NanoCpus': hc.get('NanoCpus'),
            'State': {k: (c.get('State') or {}).get(k) for k in ('Status', 'Running', 'StartedAt', 'Health')}}
PY
)
for pair in "odoo:$ODOO_CTR" "db:$DB_CTR"; do
  tag=${pair%%:*}; name=${pair#*:}
  docker inspect "$name" 2>/dev/null | python3 -I -c "$MASK_PY
import json, sys
d = json.load(sys.stdin); print(json.dumps(slim(d[0]), indent=1, sort_keys=True))" > "$OUT/${tag}_container.json" || die 4 "inspect failed: $name"
done
docker ps -a --format '{{.Names}}|{{.Image}}|{{.Status}}' > "$OUT/all_containers.txt" 2>/dev/null || echo "UNAVAILABLE" > "$OUT/all_containers.txt"
docker network ls --format '{{.Name}}|{{.Driver}}' > "$OUT/networks.txt" 2>/dev/null || echo "UNAVAILABLE" > "$OUT/networks.txt"
docker volume ls --format '{{.Name}}|{{.Driver}}' > "$OUT/volumes.txt" 2>/dev/null || echo "UNAVAILABLE" > "$OUT/volumes.txt"
docker system df > "$OUT/docker_system_df.txt" 2>/dev/null || echo "UNAVAILABLE" > "$OUT/docker_system_df.txt"
{ echo "## df -P / /var/lib/docker /root"; df -P / /var/lib/docker /root 2>&1; echo "## free -m"; free -m 2>&1; echo "## nproc"; nproc 2>&1; } > "$OUT/host_capacity.txt"
CFG_SNIPPET=$(cat <<'PY'
import json, sys
conf_path, cmd_path = sys.argv[1], sys.argv[2]
KEEP = ('addons_path', 'data_dir', 'db_host', 'db_port', 'db_name', 'db_user', 'dbfilter', 'workers', 'proxy_mode', 'list_db', 'server_wide_modules', 'limit_time_cpu', 'limit_time_real', 'limit_memory_soft', 'limit_memory_hard', 'max_cron_threads', 'http_port', 'gevent_port', 'logfile', 'log_level')
conf = {}
try:
    for line in open(conf_path, encoding='utf-8', errors='replace').read().splitlines():
        line = line.strip()
        if line and line[0] not in '#;[' and '=' in line:
            k, v = line.split('=', 1)
            if k.strip() in KEEP: conf[k.strip()] = v.strip()
except OSError: pass
args = []
try: args = [x for x in open(cmd_path, 'rb').read().decode('utf-8', 'replace').split('\0') if x]
except OSError: pass
import re
SECRETISH = re.compile(r'(?i)(pass(word|wd)?|pwd|secret|token|api[_-]?key|private[_-]?key|credential)')
safe = []; skip = False
for a in args:
    if skip: safe.append('***MASKED***'); skip = False; continue
    if a.startswith('-'):
        key = a.lstrip('-').split('=', 1)[0].lower().replace('-', '_')
        if key in KEEP or key in ('d', 'i', 'u', 'c'): safe.append(a)
        else:
            safe.append(('--' + key + '=***MASKED***') if '=' in a else a)
            if '=' not in a and SECRETISH.search(key): skip = True      # the NEXT token is the secret value
    else: safe.append(a)
print(json.dumps({'conf_whitelisted': conf, 'cmdline_masked': safe}, sort_keys=True))
PY
)
docker exec "$ODOO_CTR" python3 -I -c "$CFG_SNIPPET" "$ODOO_CONF_PATH" "$ODOO_CMDLINE_PATH" > "$OUT/odoo_config_whitelist.json" 2>"$OUT/odoo_config.err" || echo '{"error":"config probe failed"}' > "$OUT/odoo_config_whitelist.json"
docker exec "$ODOO_CTR" odoo --version > "$OUT/odoo_version.txt" 2>&1 || echo "UNAVAILABLE" > "$OUT/odoo_version.txt"
PGU=$(docker exec "$DB_CTR" printenv POSTGRES_USER 2>/dev/null | tr -d '\r\n'); PGU=${PGU:-odoo}
printf '%s\n' "select 'pg_version='||version();" "select 'db_size_bytes='||pg_database_size(current_database());" "select 'db_encoding='||pg_encoding_to_char(encoding)||'|collate='||datcollate from pg_database where datname=current_database();" "select 'attachments_db='||count(*) from ir_attachment where store_fname is null and db_datas is not null;" "select 'attachments_fs='||count(*) from ir_attachment where store_fname is not null;" "select 'active_connections='||count(*) from pg_stat_activity where datname=current_database();" "select 'extensions='||string_agg(extname,',' order by extname) from pg_extension;" | docker exec -i -e PGOPTIONS='-c default_transaction_read_only=on' "$DB_CTR" psql -v ON_ERROR_STOP=1 -U "$PGU" -d "$DBNAME" -Atq > "$OUT/db_facts.txt" 2>"$OUT/db_facts.err" || echo "DB_FACTS_UNAVAILABLE" >> "$OUT/db_facts.txt"
python3 -I - "$OUT" <<'PY'
import json, os, sys, hashlib, re
out = sys.argv[1]
SECRET = re.compile(r'(?i)(pass(word|wd)?|pwd|secret|token|api[_-]?key|private[_-]?key|credential)')
def mask_text(t):
    res = []
    for line in t.splitlines():
        if SECRET.search(line) and re.search(r'[:=]\s*\S', line): res.append(re.sub(r'([:=]\s*)\S.*$', r'\1***MASKED***', line))
        else: res.append(line)
    return '\n'.join(res) + '\n'
files = []
for n in ('odoo_container.json', 'db_container.json'):
    c = json.load(open(os.path.join(out, n)))
    for f in (c.get('ComposeConfigFiles') or '').split(','):
        f = f.strip()
        if f and f not in files: files.append(f)
rows = []
for f in files:
    try: raw = open(f, 'rb').read(); rows.append({'path': f, 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}); open(os.path.join(out, 'compose_' + re.sub(r'[^A-Za-z0-9_.-]', '_', f.strip('/')) + '.masked.yml'), 'w').write(mask_text(raw.decode('utf-8', 'replace')))
    except OSError as e: rows.append({'path': f, 'error': e.__class__.__name__})
json.dump(rows, open(os.path.join(out, 'compose_files.json'), 'w'), indent=1)
# addons mount listing: names only, one level
mounts = json.load(open(os.path.join(out, 'odoo_container.json')))['Mounts']; listing = {}
for m in mounts:
    s = m.get('Source')
    try: listing[m['Destination']] = {'source': s, 'entries': sorted(os.listdir(s))[:200]} if s and os.path.isdir(s) else {'source': s, 'entries': None}
    except OSError: listing[m['Destination']] = {'source': s, 'entries': 'UNREADABLE'}
json.dump(listing, open(os.path.join(out, 'mount_listing.json'), 'w'), indent=1, sort_keys=True)
index = {n: hashlib.sha256(open(os.path.join(out, n), 'rb').read()).hexdigest() for n in sorted(os.listdir(out)) if os.path.isfile(os.path.join(out, n))}
json.dump({'collector': 'env_facts/1', 'files_sha256': index}, open(os.path.join(out, 'INDEX.json'), 'w'), indent=1, sort_keys=True)
print('ENV_FACTS_VERDICT=COLLECTED'); print('OUT=' + out); print('INDEX_SHA256=' + hashlib.sha256(open(os.path.join(out, 'INDEX.json'), 'rb').read()).hexdigest())
PY
