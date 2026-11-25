#!/usr/bin/env bash
# P0 PRESTATE RECEIPT v4 for the Hostinger Odoo 20 instance. READ-ONLY. Run as root at the host console.
# What it proves (and what it does NOT - see 'not_covered' in the receipt): (1) the files Odoo is CONFIGURED TO LOAD (effective addons_path read from the running container, resolved first-match like Odoo,
#   duplicates refused, symlinks refused) equal the baseline manifest, byte for byte, as seen INSIDE the container;
#   (2) the host-side mount source agrees (second view; refuses on conflict); (3) database.uuid, module versions and the F5 visibility-default fact from the DB (read-only session).
# Exit: 0 P0_MATCH_ALL (TWO agreeing views: in-container AND host mount source) | 2 prerequisite missing/unsafe | 3 manifest hash refused, DIFF or view conflict | 4 discovery failed / config mismatch
#       5 database facts unavailable | 6 P0_CONTAINER_VERIFIED_HOST_UNAVAILABLE (container view only: NOT full verification, not a release-gate pass)
# Inputs are PINNED constants (verifier, expected state, baseline manifest) and are hash-checked before any docker call or file creation; none can be overridden by the environment.
# Writes ONLY into $OUT. Uses only: docker inspect, docker exec (printenv, python3 read-only checks fed over stdin, psql SELECTs), sha256sum, python3. Never prints passwords (whitelisted keys only).
set -u -o pipefail
ODOO_CTR=${ODOO_CTR:-odoo20-odoo-1}; DB_CTR=${DB_CTR:-odoo20-db-1}; DBNAME=${DBNAME:-synapsys_v20}; COMPOSE=${COMPOSE:-/opt/odoo20/docker-compose.yml}
ODOO_CONF_PATH=${ODOO_CONF_PATH:-/etc/odoo/odoo.conf}; ODOO_CMDLINE_PATH=${ODOO_CMDLINE_PATH:-/proc/1/cmdline}
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# PINNED INPUTS - constants on purpose (no environment override): the files this check trusts must be exactly the approved bytes.
PIN_VERIFIER=0e1ebe20b289d513b5241efec04d2b576aeca0eb57fbeb5877c0ecf1bd34106d      # verify_on_target.py
PIN_EXPECTED=9a85c43a5500c0e4ee03dbc50506f584d73675870ca882fcc3ec2f1c53b607c5      # expected_prestate.json
PIN_MANIFEST=699abf48f806ab2238423f78f3922f72f9b84c28335ca159d9eecefb2b2239e3      # manifests/BASELINE_v20-dev_7278898.manifest.json
VERIFIER=$HERE/verify_on_target.py; EXPECTED=$HERE/expected_prestate.json; MANIFEST=$HERE/manifests/BASELINE_v20-dev_7278898.manifest.json; MSHA=$PIN_MANIFEST
ONLY=synapsys,synapsys_benefit_asset_link,synapsys_closure_stubs,synapsys_context_portal,synapsys_mesh,synapsys_migration_load,synapsys_portal_scaffold,synapsys_registers,synapsys_registers_base,synapsys_service_governance,synapsys_v19_reference,synapsys_value_preview_gateway
OUT=${OUT:-./p0_receipt_$(date -u +%Y%m%dT%H%M%SZ)}
say(){ printf '%s\n' "$*" >&2; }; die(){ code=$1; shift; say "P0_REFUSE[$code]: $*"; echo "P0_VERDICT=REFUSE_$code"; exit "$code"; }
for c in docker python3 sha256sum; do command -v "$c" >/dev/null 2>&1 || die 2 "prerequisite missing: $c"; done
[[ "$DBNAME" =~ ^[A-Za-z0-9_.-]+$ ]] || die 2 "DBNAME has unexpected characters"
case "$HERE" in *:*) die 2 "the script directory path contains ':' (pin parsing would be ambiguous)";; esac

for pin in "VERIFIER:$VERIFIER:$PIN_VERIFIER" "EXPECTED_PRESTATE:$EXPECTED:$PIN_EXPECTED" "BASELINE_MANIFEST:$MANIFEST:$PIN_MANIFEST"; do
  IFS=: read -r pname pfile pwant <<<"$pin"
  [ -f "$pfile" ] || die 2 "pinned input not found: $pname ($pfile)"
  pgot=$(sha256sum "$pfile" | cut -d' ' -f1)
  [ "$pgot" = "$pwant" ] || die 3 "pinned input $pname differs from the approved bytes (expected $pwant, observed $pgot) - nothing examined, no docker call made"
done
SELF_SHA=$(sha256sum "${BASH_SOURCE[0]}" | cut -d' ' -f1)
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
out = {'conf_found': False, 'cmdline_found': False, 'addons_path_source': None, 'addons_path': [], 'db_name_conf': None, 'db_name_cmdline': None, 'data_dir': None}
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
ap = None; src = None; dbc = None; ddir = None; i = 0
while i < len(args):
    a = args[i]
    if a.startswith('--addons-path='): ap = a.split('=', 1)[1]; src = 'cmdline'
    elif a == '--addons-path' and i + 1 < len(args): ap = args[i + 1]; src = 'cmdline'; i += 1
    elif a.startswith('--database='): dbc = a.split('=', 1)[1]
    elif a.startswith('--data-dir='): ddir = a.split('=', 1)[1]
    elif a == '--data-dir' and i + 1 < len(args): ddir = args[i + 1]; i += 1
    elif a in ('-d', '--database') and i + 1 < len(args): dbc = args[i + 1]; i += 1
    i += 1
if ap is None and conf.get('addons_path'): ap = conf['addons_path']; src = 'conf'
out['addons_path_source'] = src; out['addons_path'] = [p.strip() for p in (ap or '').split(',') if p.strip()]
dbn = conf.get('db_name'); out['db_name_conf'] = None if dbn in (None, '', 'False', 'false') else dbn; out['db_name_cmdline'] = dbc; out['data_dir'] = ddir or conf.get('data_dir') or None
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
docker exec -i "$ODOO_CTR" python3 -I -c "$(cat "$VERIFIER")" --addons-path "$APATH" --manifest - --manifest-sha256 "$MSHA" --only "$ONLY" < "$MANIFEST" > "$OUT/verify_container.json" 2>"$OUT/verify_container.err"; CRC=$?
# (2) SECOND VIEW: resolve where Odoo actually found OUR addons (container receipt locations) through Docker's mounts (longest-prefix, so parent-directory mounts work),
#     then verify those exact host paths outside the container. Entries not under any mount are classified IMAGE_NATIVE_NOT_HOST_MOUNTED and never presented as host files.
HOSTARGS=$(python3 -I - "$OUT/odoo_config_whitelist.json" "$OUT/odoo_mounts.json" "$OUT/verify_container.json" "${ADDONS:-}" "$OUT/host_view_note.txt" "$OUT/mount_mapping.json" <<'PY'
import json, os, sys
cfg = json.load(open(sys.argv[1])); mounts = json.load(open(sys.argv[2])); override = sys.argv[4]; note = sys.argv[5]; mapout = sys.argv[6]
try: cv = json.load(open(sys.argv[3]))
except Exception: cv = {}
def host_of(path):
    best = None
    for m in mounts:
        d, s = m.get('Destination'), m.get('Source')
        if not d or not s: continue
        d = os.path.normpath(d)
        if path == d or path.startswith(d.rstrip('/') + '/'):
            if best is None or len(d) > len(best[0]): best = (d, s, m.get('Type'))
    if not best: return None
    d, s, t = best
    return (s if path == d else os.path.normpath(os.path.join(s, os.path.relpath(path, d))), d, t)
supply = {}
for n, a in (cv.get('addons') or {}).items():
    if a.get('location'): supply.setdefault(os.path.dirname(a['location']), []).append(n)
rows = []
for e in [os.path.normpath(p) for p in cfg['addons_path']]:
    h = host_of(e)
    rows.append({'container_path': e, 'supplies_release_addons': sorted(supply.get(e, [])), 'classification': 'MOUNTED' if h else 'IMAGE_NATIVE_NOT_HOST_MOUNTED',
                 'host_path': h[0] if h else None, 'mount_destination': h[1] if h else None, 'mount_type': h[2] if h else None})
json.dump(rows, open(mapout, 'w'), indent=1, sort_keys=True)
need = [r for r in rows if r['supplies_release_addons']]
def stop(msg): open(note, 'w').write(msg + '\n'); print(''); sys.exit(0)
if not need: stop('NO_CONTAINER_ADDON_LOCATIONS_TO_CORROBORATE')
bad = [r for r in need if r['classification'] != 'MOUNTED']
if bad: stop('RELEASE_ADDONS_SUPPLIED_FROM_A_PATH_THAT_IS_NOT_HOST_MOUNTED: ' + ', '.join(r['container_path'] for r in bad))
if override:
    if len(need) == 1 and os.path.realpath(override) == os.path.realpath(need[0]['host_path']): print('--addons-dir ' + override); sys.exit(0)
    stop('ADDONS_OVERRIDE_IS_NOT_THE_HOST_PATH_OF_THE_ENTRY_THAT_SUPPLIES_THE_RELEASE_ADDONS')
print('--addons-path ' + ':'.join(r['host_path'] for r in need))
PY
)
HRC=NA
if [ -n "$HOSTARGS" ]; then
  # shellcheck disable=SC2086
  python3 -I "$VERIFIER" $HOSTARGS --manifest "$MANIFEST" --manifest-sha256 "$MSHA" --only "$ONLY" > "$OUT/verify_host.json" 2>"$OUT/verify_host.err"; HRC=$?
fi
# (3) filestore presence/size inside the Odoo container (read-only walk; recorded, not enforced)
FS_SNIPPET=$(cat <<'PY'
import json, os, sys
d, db = sys.argv[1], sys.argv[2]; p = os.path.join(d, 'filestore', db); o = {'path': p, 'exists': os.path.isdir(p), 'files': 0, 'bytes': 0, 'truncated': False}
if o['exists']:
    for dp, dn, fn in os.walk(p):
        for f in fn:
            o['files'] += 1
            try: o['bytes'] += os.lstat(os.path.join(dp, f)).st_size
            except OSError: pass
            if o['files'] >= 500000: o['truncated'] = True; break
        if o['truncated']: break
print(json.dumps(o, sort_keys=True))
PY
)
DATA_DIR=$(python3 -I -c "import json,sys;print(json.load(open(sys.argv[1])).get('data_dir') or '/var/lib/odoo')" "$OUT/odoo_config_whitelist.json")
docker exec "$ODOO_CTR" python3 -I -c "$FS_SNIPPET" "$DATA_DIR" "$DBNAME" > "$OUT/filestore.json" 2>"$OUT/filestore.err" || echo '{"error":"filestore probe failed"}' > "$OUT/filestore.json"
sha256sum "$COMPOSE" > "$OUT/compose.sha256" 2>/dev/null || echo "COMPOSE_UNREADABLE $COMPOSE" > "$OUT/compose.sha256"
PGU=$(docker exec "$DB_CTR" printenv POSTGRES_USER 2>/dev/null | tr -d '\r\n'); PGU=${PGU:-odoo}
SQL="select 'database.uuid='||coalesce((select value from ir_config_parameter where key='database.uuid'),'');
select 'module='||name||'|'||state||'|'||coalesce(latest_version,'') from ir_module_module where name like 'synapsys%' or name='website' order by name;
select 'ir_ui_view.visibility.default='||coalesce((select column_default from information_schema.columns where table_name='ir_ui_view' and column_name='visibility'),'<none>');
select 'ir_ui_view.visibility.exists='||(select count(*) from information_schema.columns where table_name='ir_ui_view' and column_name='visibility');
select 'company='||id||'|'||name from res_company order by id;"
printf '%s\n' "$SQL" | docker exec -i -e PGOPTIONS='-c default_transaction_read_only=on' "$DB_CTR" psql -v ON_ERROR_STOP=1 -U "$PGU" -d "$DBNAME" -Atq > "$OUT/db_facts.txt" 2>"$OUT/db_facts.err"; DRC=$?
python3 -I - "$OUT" "$CRC" "$HRC" "$DRC" "$ODOO_CTR" "$DB_CTR" "$DBNAME" "$MSHA" "$EXPECTED" "$SELF_SHA" "$PIN_VERIFIER" "$PIN_EXPECTED" "$PIN_MANIFEST" <<'PY'
import json, sys, hashlib, os, datetime, socket
out, crc, hrc, drc, oc, dc, db, msha, expf, selfsha, pv, pe, pm = sys.argv[1:14]; crc = int(crc); drc = int(drc)
def r(n): p = os.path.join(out, n); return open(p, encoding='utf-8', errors='replace').read() if os.path.exists(p) else ''
def j(n):
    try: return json.loads(r(n))
    except Exception: return {}
facts = [l for l in r('db_facts.txt').splitlines() if l]; uuid = next((l.split('=', 1)[1] for l in facts if l.startswith('database.uuid=')), '')
exp = json.load(open(expf)); expected = set(exp['modules']); got = {l.split('=', 1)[1] for l in facts if l.startswith('module=')}
got_mods = {x for x in got if x.split('|')[0].startswith('synapsys') or x.startswith('website|')}
mod_check = {'status': 'MATCH' if got_mods == expected else 'MISMATCH', 'missing_or_changed_expected': sorted(expected - got_mods), 'unexpected_or_changed_observed': sorted(got_mods - expected), 'expected_file_sha256': hashlib.sha256(open(expf, 'rb').read()).hexdigest()}
company = [l.split('=', 1)[1] for l in facts if l.startswith('company=')]; fs = j('filestore.json')
rec = {'receipt': 'p0_prestate/3', 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'host': socket.gethostname(), 'odoo_container': oc, 'db_container': dc, 'database': db,
       'baseline_manifest_sha256': msha, 'odoo_container_inspect': r('odoo_container.txt').strip(), 'compose_sha256': r('compose.sha256').strip(), 'odoo_config_whitelist': j('odoo_config_whitelist.json'),
       'database_uuid': uuid, 'db_facts': facts, 'container_view_exit': crc, 'container_view': j('verify_container.json'), 'host_view_exit': hrc, 'host_view': ('UNAVAILABLE' if hrc == 'NA' else j('verify_host.json')),
       'p0_script_sha256': selfsha, 'pinned_inputs': {'verify_on_target.py': {'sha256': pv, 'status': 'MATCH'}, 'expected_prestate.json': {'sha256': pe, 'status': 'MATCH'}, 'baseline_manifest': {'sha256': pm, 'status': 'MATCH'}}, 'scope_addons': 'fixed 12 installed synapsys addons (not overridable)',
       'mount_mapping': j('mount_mapping.json'), 'module_prestate_check': mod_check, 'company_facts': company, 'filestore': fs}
host_bad = hrc not in ('NA', '0')
if drc != 0 or not uuid: v, code = 'P0_DB_FACTS_UNAVAILABLE', 5
elif crc != 0: v, code = 'P0_DIFF', 3
elif host_bad: v, code = 'P0_VIEW_CONFLICT', 3
elif mod_check['status'] != 'MATCH': v, code = 'P0_PRESTATE_MISMATCH', 3
elif hrc == 'NA': v, code = 'P0_CONTAINER_VERIFIED_HOST_UNAVAILABLE', 6
else: v, code = 'P0_MATCH_ALL', 0
ev = 'TWO_VIEW' if v == 'P0_MATCH_ALL' else ('CONTAINER_ONLY' if v == 'P0_CONTAINER_VERIFIED_HOST_UNAVAILABLE' else 'NONE')
rec['evidence_class'] = ev; rec['qualifies_as_two_view_gate_evidence'] = (ev == 'TWO_VIEW'); rec['host_view_note'] = r('host_view_note.txt').strip()
rec['release_prestate_conditions'] = {'addon_file_identity_container_view': 'ENFORCED', 'addon_file_identity_host_view': 'ENFORCED_WHEN_MOUNTED', 'database_uuid_present': 'ENFORCED', 'module_versions_and_states': 'ENFORCED',
    'company_identity': 'RECORDED_NOT_ENFORCED' if company else 'MISSING', 'filestore_presence_and_size': ('RECORDED_NOT_ENFORCED' if fs.get('exists') else 'MISSING_OR_UNREADABLE'),
    'ir_ui_view_visibility_default': 'RECORDED_NOT_ENFORCED'}
rec['not_covered'] = ['restore/recovery pair and throwaway-restore proof', 'adequacy of company identity and filestore for the release (recorded only; D007 reconciles)', 'scope-specific CHG and D007 effect release', 'non-Claude D009 assessment',
    'RUN_LOCK', 'runtime role/ACL/direct-action/cross-Context tests', 'Odoo core/implicit addons path (not examined)']
rec['verdict'] = v; s = json.dumps(rec, indent=1, sort_keys=True) + '\n'; open(os.path.join(out, 'p0_receipt.json'), 'w').write(s)
print('P0_VERDICT=' + v); print('EVIDENCE_CLASS=' + ev); print('HOST_VIEW=' + ('UNAVAILABLE' if hrc == 'NA' else ('MATCH' if hrc == '0' else 'DIFF'))); print('MODULE_PRESTATE=' + mod_check['status'])
print('RECEIPT=' + os.path.join(out, 'p0_receipt.json')); print('RECEIPT_SHA256=' + hashlib.sha256(s.encode()).hexdigest())
if code == 6: print('NOTE: container view only (' + rec['host_view_note'] + '). Not full verification. See mount_mapping in the receipt.')
if v == 'P0_MATCH_ALL': print('NOTE: P0_MATCH_ALL = file identity (two views) + database.uuid + module versions. It does NOT cover recovery, company/filestore adequacy, authority or D009: see not_covered in the receipt.')
sys.exit(code)
PY
