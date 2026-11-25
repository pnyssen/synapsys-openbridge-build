#!/usr/bin/env bash
# P0 PRESTATE RECEIPT v2 for the Hostinger Odoo 20 instance. READ-ONLY. Run as root at the host console.
# What it proves: (1) the files Odoo is CONFIGURED TO LOAD (effective addons_path read from the running container, resolved first-match like Odoo,
#   duplicates refused, symlinks refused) equal the baseline manifest, byte for byte, as seen INSIDE the container;
#   (2) the host-side mount source agrees (second view; refuses on conflict); (3) database.uuid, module versions and the F5 visibility-default fact from the DB (read-only session).
# Exit: 0 P0_MATCH_ALL | 2 prerequisite missing/unsafe | 3 manifest hash refused, DIFF or view conflict | 4 discovery failed / config mismatch | 5 database facts unavailable
# Writes ONLY into $OUT. Uses only: docker inspect, docker exec (printenv, python3 read-only checks fed over stdin, psql SELECTs), sha256sum, python3. Never prints passwords (whitelisted keys only).
set -u -o pipefail
ODOO_CTR=${ODOO_CTR:-odoo20-odoo-1}; DB_CTR=${DB_CTR:-odoo20-db-1}; DBNAME=${DBNAME:-synapsys_v20}; COMPOSE=${COMPOSE:-/opt/odoo20/docker-compose.yml}
ODOO_CONF_PATH=${ODOO_CONF_PATH:-/etc/odoo/odoo.conf}; ODOO_CMDLINE_PATH=${ODOO_CMDLINE_PATH:-/proc/1/cmdline}
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
MANIFEST=${MANIFEST:-$HERE/manifests/BASELINE_v20-dev_7278898.manifest.json}
MSHA=${MSHA:-699abf48f806ab2238423f78f3922f72f9b84c28335ca159d9eecefb2b2239e3}
ONLY=${ONLY:-synapsys,synapsys_benefit_asset_link,synapsys_closure_stubs,synapsys_context_portal,synapsys_mesh,synapsys_migration_load,synapsys_portal_scaffold,synapsys_registers,synapsys_registers_base,synapsys_service_governance,synapsys_v19_reference,synapsys_value_preview_gateway}
OUT=${OUT:-./p0_receipt_$(date -u +%Y%m%dT%H%M%SZ)}
say(){ printf '%s\n' "$*" >&2; }; die(){ code=$1; shift; say "P0_REFUSE[$code]: $*"; echo "P0_VERDICT=REFUSE_$code"; exit "$code"; }
for c in docker python3 sha256sum; do command -v "$c" >/dev/null 2>&1 || die 2 "prerequisite missing: $c"; done
[ -f "$MANIFEST" ] || die 2 "manifest not found: $MANIFEST"
[ -f "$HERE/verify_on_target.py" ] || die 2 "verify_on_target.py not found next to this script"
[ "$(sha256sum "$MANIFEST" | cut -d' ' -f1)" = "$MSHA" ] || die 3 "manifest sha256 differs from the expected $MSHA (nothing examined)"
for c in "$ODOO_CTR" "$DB_CTR"; do [ "$(docker inspect -f '{{.State.Running}}' "$c" 2>/dev/null)" = "true" ] || die 4 "container not running or not found: $c"; done
MOUNTS_JSON=$(docker inspect -f '{{json .Mounts}}' "$ODOO_CTR" 2>/dev/null) || die 4 "mount inspect failed"
# refuse BEFORE creating anything if OUT would land inside any mounted source tree or the ADDONS override
MOUNTS_JSON="$MOUNTS_JSON" python3 -I - "$OUT" "${ADDONS:-}" <<'PY' || die 2 "OUT must not be inside an addons/mount source dir (nothing was written)"
import json, os, sys
out = os.path.realpath(sys.argv[1]); srcs = [m.get('Source') for m in json.loads(os.environ['MOUNTS_JSON']) if m.get('Source')] + ([sys.argv[2]] if sys.argv[2] else [])
for s in srcs:
    s = os.path.realpath(s)
    if out == s or out.startswith(s.rstrip(os.sep) + os.sep): sys.exit(1)
PY
mkdir -p "$OUT" || die 2 "cannot create $OUT"; OUT=$(cd "$OUT" && pwd)
printf '%s\n' "$MOUNTS_JSON" > "$OUT/odoo_mounts.json"
docker inspect -f '{{.Image}} {{.Config.Image}} {{.State.StartedAt}}' "$ODOO_CTR" > "$OUT/odoo_container.txt" 2>/dev/null || die 4 "inspect failed: $ODOO_CTR"
CFG_SNIPPET=$(cat <<'PY'
import json, sys
conf_path, cmd_path = sys.argv[1], sys.argv[2]
out = {'conf_found': False, 'cmdline_found': False, 'addons_path_source': None, 'addons_path': [], 'db_name_conf': None, 'db_name_cmdline': None}
conf = {}
try:
    for line in open(conf_path, encoding='utf-8', errors='replace').read().splitlines():
        line = line.strip()
        if line and line[0] not in '#;[' and '=' in line:
            k, v = line.split('=', 1); conf[k.strip()] = v.strip()
    out['conf_found'] = True
except OSError: pass
args = []
try: args = [x for x in open(cmd_path, 'rb').read().decode('utf-8', 'replace').split('\0') if x]; out['cmdline_found'] = True
except OSError: pass
ap = None; src = None; dbc = None; i = 0
while i < len(args):
    a = args[i]
    if a.startswith('--addons-path='): ap = a.split('=', 1)[1]; src = 'cmdline'
    elif a == '--addons-path' and i + 1 < len(args): ap = args[i + 1]; src = 'cmdline'; i += 1
    elif a.startswith('--database='): dbc = a.split('=', 1)[1]
    elif a in ('-d', '--database') and i + 1 < len(args): dbc = args[i + 1]; i += 1
    i += 1
if ap is None and conf.get('addons_path'): ap = conf['addons_path']; src = 'conf'
out['addons_path_source'] = src; out['addons_path'] = [p.strip() for p in (ap or '').split(',') if p.strip()]
dbn = conf.get('db_name'); out['db_name_conf'] = None if dbn in (None, '', 'False', 'false') else dbn; out['db_name_cmdline'] = dbc
print(json.dumps(out, sort_keys=True))   # whitelisted keys only: no passwords, no full command line
PY
)
docker exec "$ODOO_CTR" python3 -I -c "$CFG_SNIPPET" "$ODOO_CONF_PATH" "$ODOO_CMDLINE_PATH" > "$OUT/odoo_config_whitelist.json" 2>"$OUT/odoo_config.err" || die 4 "could not read Odoo configuration inside $ODOO_CTR"
read -r APATH DBN_EFF < <(python3 -I - "$OUT/odoo_config_whitelist.json" <<'PY'
import json, sys
c = json.load(open(sys.argv[1])); print(':'.join(c['addons_path']) or '-', c['db_name_cmdline'] or c['db_name_conf'] or '-')
PY
)
{ [ -n "${APATH:-}" ] && [ "$APATH" != "-" ]; } || die 4 "no addons_path found in Odoo config or command line (conf_found/cmdline_found in $OUT/odoo_config_whitelist.json)"
if [ "${DBN_EFF:--}" != "-" ] && [ "$DBN_EFF" != "$DBNAME" ]; then die 4 "Odoo is configured for database '$DBN_EFF' but this check targets '$DBNAME'"; fi
# (1) AUTHORITATIVE VIEW: the verifier runs inside the container over the paths Odoo loads; script and manifest arrive on argv/stdin, nothing is copied or written there.
docker exec -i "$ODOO_CTR" python3 -I -c "$(cat "$HERE/verify_on_target.py")" --addons-path "$APATH" --manifest - --manifest-sha256 "$MSHA" --only "$ONLY" < "$MANIFEST" > "$OUT/verify_container.json" 2>"$OUT/verify_container.err"; CRC=$?
# (2) SECOND VIEW: map each addons_path entry to its host mount source (or use ADDONS=<host dir> as an override) and verify there, outside the container.
HOSTARGS=$(python3 -I - "$OUT/odoo_config_whitelist.json" "$OUT/odoo_mounts.json" "${ADDONS:-}" <<'PY'
import json, sys
cfg = json.load(open(sys.argv[1])); mounts = json.load(open(sys.argv[2])); override = sys.argv[3]
if override: print('--addons-dir ' + override); sys.exit(0)
dest = {m.get('Destination'): m.get('Source') for m in mounts}
srcs = [dest.get(p) for p in cfg['addons_path']]
print('' if not srcs or any(s is None for s in srcs) else '--addons-path ' + ':'.join(srcs))
PY
)
HRC=NA
if [ -n "$HOSTARGS" ]; then
  # shellcheck disable=SC2086
  python3 -I "$HERE/verify_on_target.py" $HOSTARGS --manifest "$MANIFEST" --manifest-sha256 "$MSHA" --only "$ONLY" > "$OUT/verify_host.json" 2>"$OUT/verify_host.err"; HRC=$?
fi
sha256sum "$COMPOSE" > "$OUT/compose.sha256" 2>/dev/null || echo "COMPOSE_UNREADABLE $COMPOSE" > "$OUT/compose.sha256"
PGU=$(docker exec "$DB_CTR" printenv POSTGRES_USER 2>/dev/null | tr -d '\r\n'); PGU=${PGU:-odoo}
SQL="select 'database.uuid='||coalesce((select value from ir_config_parameter where key='database.uuid'),'');
select 'module='||name||'|'||state||'|'||coalesce(latest_version,'') from ir_module_module where name like 'synapsys%' or name='website' order by name;
select 'ir_ui_view.visibility.default='||coalesce((select column_default from information_schema.columns where table_name='ir_ui_view' and column_name='visibility'),'<none>');
select 'ir_ui_view.visibility.exists='||(select count(*) from information_schema.columns where table_name='ir_ui_view' and column_name='visibility');"
printf '%s\n' "$SQL" | docker exec -i -e PGOPTIONS='-c default_transaction_read_only=on' "$DB_CTR" psql -v ON_ERROR_STOP=1 -U "$PGU" -d "$DBNAME" -Atq > "$OUT/db_facts.txt" 2>"$OUT/db_facts.err"; DRC=$?
python3 -I - "$OUT" "$CRC" "$HRC" "$DRC" "$ODOO_CTR" "$DB_CTR" "$DBNAME" "$MSHA" <<'PY'
import json, sys, hashlib, os, datetime, socket
out, crc, hrc, drc, oc, dc, db, msha = sys.argv[1:9]; crc = int(crc); drc = int(drc)
def r(n): p = os.path.join(out, n); return open(p, encoding='utf-8', errors='replace').read() if os.path.exists(p) else ''
def j(n):
    try: return json.loads(r(n))
    except Exception: return {}
facts = [l for l in r('db_facts.txt').splitlines() if l]; uuid = next((l.split('=', 1)[1] for l in facts if l.startswith('database.uuid=')), '')
rec = {'receipt': 'p0_prestate/2', 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'host': socket.gethostname(), 'odoo_container': oc, 'db_container': dc, 'database': db,
       'baseline_manifest_sha256': msha, 'odoo_container_inspect': r('odoo_container.txt').strip(), 'compose_sha256': r('compose.sha256').strip(), 'odoo_config_whitelist': j('odoo_config_whitelist.json'),
       'database_uuid': uuid, 'db_facts': facts, 'container_view_exit': crc, 'container_view': j('verify_container.json'), 'host_view_exit': hrc, 'host_view': ('UNAVAILABLE' if hrc == 'NA' else j('verify_host.json'))}
host_bad = hrc not in ('NA', '0')
if drc != 0 or not uuid: v, code = 'P0_DB_FACTS_UNAVAILABLE', 5
elif crc != 0: v, code = 'P0_DIFF', 3
elif host_bad: v, code = 'P0_VIEW_CONFLICT', 3
else: v, code = 'P0_MATCH_ALL', 0
rec['verdict'] = v; s = json.dumps(rec, indent=1, sort_keys=True) + '\n'; open(os.path.join(out, 'p0_receipt.json'), 'w').write(s)
print('P0_VERDICT=' + v); print('HOST_VIEW=' + ('UNAVAILABLE' if hrc == 'NA' else ('MATCH' if hrc == '0' else 'DIFF'))); print('RECEIPT=' + os.path.join(out, 'p0_receipt.json')); print('RECEIPT_SHA256=' + hashlib.sha256(s.encode()).hexdigest()); sys.exit(code)
PY
