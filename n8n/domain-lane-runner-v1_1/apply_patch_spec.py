#!/usr/bin/env python3
"""Apply NODE_PATCH_SPEC to a workflow JSON file (offline). Fails closed (exit 3) on any precondition/anchor miss.
usage: apply_patch_spec.py <workflow.json> <spec.json> <out.json>"""
import json, sys, copy
wf = json.load(open(sys.argv[1])); spec = json.load(open(sys.argv[2]))
def die(m): print('REFUSE:', m, file=sys.stderr); sys.exit(3)
t = spec['target_workflow']
if wf.get('id') != t['id']: die('workflow id mismatch')
if wf.get('versionId') != t['precondition_versionId']: die('versionId drifted: %s != %s' % (wf.get('versionId'), t['precondition_versionId']))
if t.get('precondition_active') and not wf.get('active'): die('workflow not active (precondition)')
out = copy.deepcopy(wf); nodes = {n['name']: n for n in out['nodes']}
for op in spec['http_response_option_replacements']:
    n = nodes.get(op['node']) or die('node missing ' + op['node'])
    n['parameters']['options']['response']['response'] = op['replace_with']
for op in spec['node_code_full_replacements']:
    n = nodes.get(op['node']) or die('node missing ' + op['node']); n['parameters']['jsCode'] = op['jsCode']
for op in spec['node_code_replacements']:
    n = nodes.get(op['node']) or die('node missing ' + op['node']); c = n['parameters']['jsCode']
    if c.count(op['find']) != op['expect_count']: die('anchor count %d != %d in %s' % (c.count(op['find']), op['expect_count'], op['node']))
    n['parameters']['jsCode'] = c.replace(op['find'], op['replace'])
json.dump(out, open(sys.argv[3], 'w'), indent=2, sort_keys=True)
print('applied OK ->', sys.argv[3])
