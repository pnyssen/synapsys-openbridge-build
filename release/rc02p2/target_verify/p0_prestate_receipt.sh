#!/usr/bin/env bash
# P0 PRESTATE RECEIPT for the Hostinger Odoo 20 instance. READ-ONLY. Run as root at the host console.
# Exit codes: 0 P0_MATCH_ALL | 2 prerequisite missing/unsafe | 3 manifest hash refused or on-disk DIFF | 4 discovery failed/ambiguous | 5 database facts unavailable
# Writes ONLY into $OUT (refused if inside the addons dir). Uses only: docker inspect, docker exec (printenv, psql SELECTs with a read-only session), sha256sum, python3.
set -u -o pipefail
ODOO_CTR=${ODOO_CTR:-odoo20-odoo-1}; DB_CTR=${DB_CTR:-odoo20-db-1}; DBNAME=${DBNAME:-synapsys_v20}; COMPOSE=${COMPOSE:-/opt/odoo20/docker-compose.yml}
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
MANIFEST=${MANIFEST:-$HERE/manifests/BASELINE_v20-dev_7278898.manifest.json}
MSHA=${MSHA:-699abf48f806ab2238423f78f3922f72f9b84c28335ca159d9eecefb2b2239e3}
ONLY=${ONLY:-synapsys,synapsys_benefit_asset_link,synapsys_closure_stubs,synapsys_context_portal,synapsys_mesh,synapsys_migration_load,synapsys_portal_scaffold,synapsys_registers,synapsys_registers_base,synapsys_service_governance,synapsys_v19_reference,synapsys_value_preview_gateway}
OUT=${OUT:-./p0_receipt_$(date -u +%Y%m%dT%H%M%SZ)}
say(){ printf '%s\n' "$*" >&2; }; die(){ code=$1; shift; say "P0_REFUSE[$code]: $*"; echo "P0_VERDICT=REFUSE_$code"; exit "$code"; }
for c in docker python3 sha256sum; do command -v "$c" >/dev/null 2>&1 || die 2 "prerequisite missing: $c"; done
[ -f "$MANIFEST" ] || die 2 "manifest not found: $MANIFEST"
[ "$(sha256sum "$MANIFEST" | cut -d' ' -f1)" = "$MSHA" ] || die 3 "manifest sha256 differs from the expected $MSHA (nothing examined)"
mkdir -p "$OUT" || die 2 "cannot create $OUT"; OUT=$(cd "$OUT" && pwd)
for c in "$ODOO_CTR" "$DB_CTR"; do [ "$(docker inspect -f '{{.State.Running}}' "$c" 2>/dev/null)" = "true" ] || die 4 "container not running or not found: $c"; done
docker inspect -f '{{.Image}} {{.Config.Image}} {{.State.StartedAt}}' "$ODOO_CTR" > "$OUT/odoo_container.txt" 2>/dev/null || die 4 "inspect failed: $ODOO_CTR"
if [ -z "${ADDONS:-}" ]; then
  docker inspect -f '{{json .Mounts}}' "$ODOO_CTR" > "$OUT/odoo_mounts.json" 2>/dev/null || die 4 "mount inspect failed"
  CAND=$(python3 - "$OUT/odoo_mounts.json" <<'PY'
import json,os,sys
c=[]
for m in json.load(open(sys.argv[1])):
    s=m.get('Source') or ''
    if os.path.isfile(os.path.join(s,'synapsys','__manifest__.py')): c.append(s)
print('\n'.join(sorted(set(c))))
PY
)
  N=$(printf '%s' "$CAND" | grep -c . || true)
  [ "$N" = "1" ] || { say "mount sources:"; cat "$OUT/odoo_mounts.json" >&2; die 4 "addons dir discovery found $N candidates (need exactly 1). Re-run with ADDONS=<host path> after reading the mounts above."; }
  ADDONS=$CAND
fi
ADDONS=$(cd "$ADDONS" 2>/dev/null && pwd) || die 4 "addons dir not accessible: $ADDONS"
case "$OUT/" in "$ADDONS"/*) die 2 "OUT must not be inside the addons dir";; esac
sha256sum "$COMPOSE" > "$OUT/compose.sha256" 2>/dev/null || echo "COMPOSE_UNREADABLE $COMPOSE" > "$OUT/compose.sha256"
python3 -I "$HERE/verify_on_target.py" --addons-dir "$ADDONS" --manifest "$MANIFEST" --manifest-sha256 "$MSHA" --only "$ONLY" --receipt "$OUT/verify_receipt.json" > "$OUT/verify_stdout.json"; VRC=$?
PGU=$(docker exec "$DB_CTR" printenv POSTGRES_USER 2>/dev/null | tr -d '\r\n'); PGU=${PGU:-odoo}
SQL="select 'database.uuid='||coalesce((select value from ir_config_parameter where key='database.uuid'),'');
select 'module='||name||'|'||state||'|'||coalesce(latest_version,'') from ir_module_module where name like 'synapsys%' or name='website' order by name;
select 'ir_ui_view.visibility.default='||coalesce((select column_default from information_schema.columns where table_name='ir_ui_view' and column_name='visibility'),'<none>');
select 'ir_ui_view.visibility.exists='||(select count(*) from information_schema.columns where table_name='ir_ui_view' and column_name='visibility');"
printf '%s\n' "$SQL" | docker exec -i -e PGOPTIONS='-c default_transaction_read_only=on' "$DB_CTR" psql -v ON_ERROR_STOP=1 -U "$PGU" -d "$DBNAME" -Atq > "$OUT/db_facts.txt" 2>"$OUT/db_facts.err"; DRC=$?
UUID=$(sed -n 's/^database.uuid=//p' "$OUT/db_facts.txt" | head -1)
python3 -I - "$OUT" "$VRC" "$DRC" "$ADDONS" "$ODOO_CTR" "$DB_CTR" "$DBNAME" "$MSHA" <<'PY'
import json,sys,hashlib,os,datetime,socket
out,vrc,drc,addons,oc,dc,db,msha=sys.argv[1:9]; vrc=int(vrc); drc=int(drc)
r=lambda n: open(os.path.join(out,n),encoding='utf-8',errors='replace').read() if os.path.exists(os.path.join(out,n)) else ''
facts=[l for l in r('db_facts.txt').splitlines() if l]
uuid=next((l.split('=',1)[1] for l in facts if l.startswith('database.uuid=')),'')
rec={'receipt':'p0_prestate/1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'host':socket.gethostname(),'odoo_container':oc,'db_container':dc,'database':db,
 'addons_dir':addons,'baseline_manifest_sha256':msha,'odoo_container_inspect':r('odoo_container.txt').strip(),'compose_sha256':r('compose.sha256').strip(),
 'database_uuid':uuid,'db_facts':facts,'verifier_exit':vrc,'verifier':json.loads(r('verify_stdout.json') or '{}')}
if drc!=0 or not uuid: v,code='P0_DB_FACTS_UNAVAILABLE',5
elif vrc!=0: v,code='P0_DIFF',3
else: v,code='P0_MATCH_ALL',0
rec['verdict']=v; s=json.dumps(rec,indent=1,sort_keys=True); open(os.path.join(out,'p0_receipt.json'),'w').write(s+'\n')
print('P0_VERDICT='+v); print('RECEIPT='+os.path.join(out,'p0_receipt.json')); print('RECEIPT_SHA256='+hashlib.sha256((s+'\n').encode()).hexdigest()); sys.exit(code)
PY
