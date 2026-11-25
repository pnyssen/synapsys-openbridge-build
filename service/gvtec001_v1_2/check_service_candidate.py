#!/usr/bin/env python3
"""Offline pre-write checker for the GV-TEC-001 append-only candidate. Reads files only; writes nothing; never touches a Catalogue.
usage: check_service_candidate.py --live live_record.json --candidate cand.json --registry reg.json --log a.txt [--log b.txt ...]
 live_record.json: a JSON object of the live x_service_catalogue fields (exported by whoever applies the change, immediately before the write).
Exit 0 only if EVERY check passes; 3 otherwise (prints each failure)."""
import argparse, json, re, sys
ap = argparse.ArgumentParser(); ap.add_argument('--live', required=True); ap.add_argument('--candidate', required=True); ap.add_argument('--registry', required=True); ap.add_argument('--log', action='append', default=[])
a = ap.parse_args()
live = json.load(open(a.live, encoding='utf-8')); cand = json.load(open(a.candidate, encoding='utf-8')); reg = json.load(open(a.registry, encoding='utf-8'))
bad = []; ok = lambda n, c, d='': (print(('PASS ' if c else 'FAIL ') + n + (' :: ' + str(d) if d else '')), (None if c else bad.append(n)))
sep = cand['separator']
# 1. every target field exists on the live record and is a non-empty string; the new text is live text + separator + append (prefix property)
for f, add in sorted(cand['append'].items()):
    cur = live.get(f)
    ok('C1 field %s exists live as non-empty text' % f, isinstance(cur, str) and cur.strip() != '')
    if isinstance(cur, str):
        new = cur + sep + add
        ok('C2 %s: result = live text + append (live text preserved byte-for-byte as prefix)' % f, new.startswith(cur) and new[len(cur):] == sep + add and add not in cur, 'already_applied' if add in cur else '')
# 2. no forbidden field is touched by this candidate
touched = set(cand['append']) | {'x_ai_capability_requirements'}
ok('C3 no forbidden/automatic field is modified', not (touched & set(cand['forbidden_automatic_changes'])), sorted(touched & set(cand['forbidden_automatic_changes'])))
# 3. AI capability array: live values all preserved, additions unique and not already present
raw = live.get('x_ai_capability_requirements')
try: arr = json.loads(raw) if isinstance(raw, str) else raw
except Exception: arr = None
ok('C4 live x_ai_capability_requirements parses as a JSON array of strings', isinstance(arr, list) and all(isinstance(x, str) for x in arr or []))
if isinstance(arr, list):
    add = cand['capability_add_values']
    ok('C5 additions are unique and do not duplicate live values', len(set(add)) == len(add) and not (set(add) & set(arr)), sorted(set(add) & set(arr)))
    merged = arr + [x for x in add if x not in arr]
    ok('C6 merged array preserves every live value in original order', merged[:len(arr)] == arr and len(merged) == len(arr) + len(add))
# 4. claims honesty: transport words may appear only inside a statement marking them UNINSTALLED / not qualified
for f, add in cand['append'].items():
    for m in re.finditer(r'(?i)\b(ssh|rsync|sftp)\b', add):
        ctx = add[max(0, m.start() - 160): m.end() + 160]
        ok('C7 %s: mention of %s is marked UNINSTALLED/unqualified' % (f, m.group(0)), bool(re.search(r'UNINSTALLED|not qualified|until qualified|Qualified today', ctx)))
ok('C8 candidate says the maturity is not enforced while any class is NOT_RUN', cand['maturity_claim']['enforced'] is False or all(c['status'] != 'NOT_RUN' for c in reg['classes']))
# 5. registry <-> evidence: a class may be PASSED_OFFLINE only if every listed test id is a PASS in the supplied logs and never a FAIL
seen = {}
for p in a.log:
    for line in open(p, encoding='utf-8', errors='replace'):
        m = re.match(r'^(PASS|FAIL) (\S+)', line)
        if m: seen.setdefault(m.group(2), []).append(m.group(1))
def tid(t): return t[len('STATIC_'):] if t.startswith('STATIC_') else t
for c in reg['classes']:
    if c['status'] == 'PASSED_OFFLINE':
        good = bool(c['tests']) and all(seen.get(tid(t)) and set(seen[tid(t)]) == {'PASS'} for t in c['tests'])
        ok('R1 class %s claimed PASSED_OFFLINE has passing evidence for %s' % (c['code'], c['tests']), good, [t for t in c['tests'] if not (seen.get(tid(t)) and set(seen[tid(t)]) == {'PASS'})])
    elif c['status'] == 'NOT_RUN':
        ok('R2 class %s NOT_RUN lists no tests (cannot be half-claimed)' % c['code'], not c['tests'])
    else: ok('R3 class %s has a known status' % c['code'], False, c['status'])
tot = len(reg['classes']); pas = sum(1 for c in reg['classes'] if c['status'] == 'PASSED_OFFLINE')
mc = cand['maturity_claim']; ok('R4 candidate maturity numbers equal the registry (%d/%d)' % (pas, tot), mc['error_classes_total'] == tot and mc['passed_offline'] == pas and mc['not_run'] == tot - pas)
print('SUMMARY failures=%d' % len(bad)); sys.exit(3 if bad else 0)
