import copy, json, os, subprocess, sys, tempfile
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.dirname(here); repo = os.path.dirname(os.path.dirname(root))
CHK = os.path.join(root, 'check_service_candidate.py')
CAND = json.load(open(os.path.join(root, 'GV-TEC-001_V20_release_service_upgrade_v1_2_CANDIDATE.json'))); REG = json.load(open(os.path.join(root, 'ERROR_CLASS_REGISTRY.json')))
LOGS = [os.path.join(repo, p) for p in ('n8n/domain-lane-runner-v1_1/tests/TEST_LOG.txt', 'release/rc02p2/target_verify/tests/TEST_LOG_verify_on_target.txt', 'release/rc02p2/target_verify/tests/TEST_LOG_p0_prestate.txt',
                                          'release/rc02p2/tests/D009_T3_CHALLENGE_TEST_LOG.txt', 'release/rc02p2/tests/RC03b_STATIC_LOG.txt')]
LIVE = {f: 'EXISTING LIVE CONTRACT TEXT for %s. Retained verbatim.' % f for f in CAND['append']}
LIVE['x_ai_capability_requirements'] = json.dumps(['code_and_configuration_analysis', 'schema_and_workflow_analysis', 'authenticated_browser_runtime'])
res = []
def run(live=None, cand=None, reg=None, logs=None):
    d = tempfile.mkdtemp(); paths = {}
    for k, v in (('live', live or LIVE), ('cand', cand or CAND), ('reg', reg or REG)): paths[k] = os.path.join(d, k + '.json'); json.dump(v, open(paths[k], 'w'))
    c = [sys.executable, '-I', CHK, '--live', paths['live'], '--candidate', paths['cand'], '--registry', paths['reg']]
    for l in (LOGS if logs is None else logs): c += ['--log', l]
    r = subprocess.run(c, capture_output=True, text=True); return r.returncode, r.stdout
def chk(n, c, d=''): c = bool(c); res.append(c); print(('PASS ' if c else 'FAIL ') + n + (' :: ' + d if d else ''))
rc, out = run(); chk('K1 happy path against a synthetic live record and the REAL logs -> exit 0, no FAIL line', rc == 0 and 'FAIL ' not in out, out.splitlines()[-1])
l = dict(LIVE); f0 = sorted(CAND['append'])[0]; l[f0] = l[f0] + CAND['separator'] + CAND['append'][f0]; rc, out = run(live=l)
chk('K2 NEG already applied (idempotency: no double append) -> exit 3', rc == 3 and 'FAIL C2' in out)
l = dict(LIVE); del l[f0]; rc, out = run(live=l); chk('K3 NEG target field missing on live -> exit 3', rc == 3 and 'FAIL C1' in out)
l = dict(LIVE); l['x_ai_capability_requirements'] = json.dumps(['raw_byte_source_integrity', 'x']); rc, out = run(live=l); chk('K4 NEG live already holds an addition -> duplicate refused', rc == 3 and 'FAIL C5' in out)
l = dict(LIVE); l['x_ai_capability_requirements'] = 'not json'; rc, out = run(live=l); chk('K5 NEG live capability field not a JSON array -> exit 3', rc == 3 and 'FAIL C4' in out)
c = copy.deepcopy(CAND); c['append']['x_service_status'] = 'x'; l = dict(LIVE); l['x_service_status'] = 'active'; rc, out = run(live=l, cand=c); chk('K6 NEG candidate touches a forbidden automatic field -> exit 3', rc == 3 and 'FAIL C3' in out)
r = copy.deepcopy(REG); r['classes'][0]['tests'] = r['classes'][0]['tests'] + ['T999']; rc, out = run(reg=r); chk('K7 NEG registry claims a test id that is not in any log -> exit 3', rc == 3 and 'FAIL R1' in out)
mut = os.path.join(repo, 'release/rc02p2/tests/D009_T3_MUTATION_CONTROL_LOG.txt'); rc, out = run(logs=[l for l in LOGS if 'D009_T3_CHALLENGE' not in l] + [mut]); chk('K8 NEG evidence log containing a FAIL for a claimed test -> exit 3 (FAIL evidence is not passing evidence)', rc == 3 and 'FAIL R1 class RENDER_INJECTION' in out)
c = copy.deepcopy(CAND); c['append'][f0] += ' Deliver the tree with SSH to the host.'; rc, out = run(cand=c); chk('K9 NEG unmarked claim of an SSH route -> exit 3', rc == 3 and 'FAIL C7' in out)
c = copy.deepcopy(CAND); c['maturity_claim']['passed_offline'] += 1; rc, out = run(cand=c); chk('K10 NEG maturity numbers inflated vs registry -> exit 3', rc == 3 and 'FAIL R4' in out)
r = copy.deepcopy(REG); nr = [x for x in r['classes'] if x['status'] == 'NOT_RUN'][0]; nr['tests'] = ['T01']; rc, out = run(reg=r); chk('K11 NEG NOT_RUN class half-claimed with a test -> exit 3', rc == 3 and 'FAIL R2' in out)
rc, out = run(logs=[]); chk('K12 NEG no evidence logs supplied -> every PASSED_OFFLINE claim refused, exit 3', rc == 3 and out.count('FAIL R1') == sum(1 for x in REG['classes'] if x['status'] == 'PASSED_OFFLINE'))
c = copy.deepcopy(CAND); c['maturity_claim']['enforced'] = True; rc, out = run(cand=c); chk('K13 NEG candidate claims ENFORCED while classes are NOT_RUN -> exit 3', rc == 3 and 'FAIL C8' in out)
print('SUMMARY pass=%d fail=%d' % (sum(res), len(res) - sum(res))); sys.exit(0 if all(res) else 1)
