#!/usr/bin/env python3
"""Compute the RC03b release identity record from files on disk (deterministic). Run from the repo root. Writes RC03b_RELEASE_IDENTITY_v1.json beside this script."""
import hashlib, json, pathlib
root = pathlib.Path(__file__).resolve().parents[3]
def h(p): b = (root / p).read_bytes(); return {'path': p, 'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b)}
man = json.load(open(root / 'release/rc02p2/target_verify/manifests/RC03b_360a2b4f.manifest.json'))
rec = {
 'schema': 'synapsys.release-identity/1', 'label': 'RC03b', 'work_object': 'WO-SYNAPSYS-CANONICAL-REFERENCE-ARCHITECTURE-001', 'context': 'CTX-SS',
 'status': 'FROZEN_FOR_D009_ASSESSMENT_AND_ISOLATED_REHEARSAL__NOT_APPROVED_FOR_INSTALL__NOT_INSTALLED',
 'source': {'repo': 'pnyssen/synapsys-odoo', 'branch': 'claude/synapsys-v20-release-service-tvjpyn', 'commit': '360a2b4fd51521f58ebb355806d90797226870a5', 'root_tree': 'f7312d7723cb96861409fc6ad1764fe3c3c1409d',
            'parent_commit_rc02p2': 'b1fbe6648095942b2e51f6e1e397eb68149ddb3e', 'baseline_commit': '7278898fb49d4eff5cdc27d37864fed0bdc0f8dc', 'frozen_patch_sha256': '6b37c5e9dfded209716f14d3330cb91202355c0d0bcf548b769865d222d715e1',
            'changed_addons': {'synapsys': {'version': '20.0.2.4.2', 'git_tree': 'cb1516a05b26f046dcf379abebe888f07b540bf1', 'identity_sha256': man['addons']['synapsys']['identity'], 'files': man['addons']['synapsys']['file_count']},
                               'synapsys_v19_reference': {'version': '20.0.0.4.0', 'git_tree': '9a2ffb5629698c48363c35190096cb880e181fc1', 'identity_sha256': man['addons']['synapsys_v19_reference']['identity'], 'files': man['addons']['synapsys_v19_reference']['file_count']}},
            'upgrade_order': ['synapsys', 'synapsys_v19_reference'], 'rc02p2_reproduced_synapsys_identity': 'd066f56080681a4e07806479bc6d43bb0032f725cd2168d74e45c8879d7f15c2'},
 'tooling': [h(p) for p in ['release/rc02p2/target_verify/verify_on_target.py', 'release/rc02p2/target_verify/p0_prestate_receipt.sh', 'release/rc02p2/target_verify/release_manifest.py',
             'release/rc02p2/target_verify/manifests/BASELINE_v20-dev_7278898.manifest.json', 'release/rc02p2/target_verify/manifests/RC03b_360a2b4f.manifest.json', 'release/rc02p2/rc02p2_reproduce_and_check.py',
             'service/gvtec001_v1_2/check_service_candidate.py', 'service/gvtec001_v1_2/ERROR_CLASS_REGISTRY.json', 'service/gvtec001_v1_2/GV-TEC-001_V20_release_service_upgrade_v1_2_CANDIDATE.json',
             'n8n/domain-lane-runner-v1_1/NODE_PATCH_SPEC_v1_1.json']],
 'steward_decisions': [{'id': 'STEWARD-F2-F3-20261125', 'recorded_by': 'claude_code from the session owner\'s direct in-thread words', 'words': 'As steward, I provide approval for D007\'s release of F2 and F3. I agree with them both and approve those.',
     'items': {'F2': 'Users who are neither Steward nor system do not get the Architecture journey view (baseline served it to any logged-in user).', 'F3': 'Collaborators see the 27 governed verbs read-only through the nine peer menus (UI-read-only; backend ACL unchanged).'},
     'effect': 'Accepts F2 and F3 as intended behaviour of RC03b for D007 release purposes.',
     'does_not_confer': ['scope-specific CHG', 'D007 effect release', 'non-Claude D009 assessment', 'RUN_LOCK', 'recovery proof', 'any install', 'resolution of F4 (sudo() registry read, R1)']}],
 'open_before_install': ['P0 console prestate receipt MATCH_ALL with database.uuid', 'isolated restore + two-addon upgrade rehearsal incl. injected-failure rollback', 'non-Claude D009 assessment of commit 360a2b4f', 'scope-specific CHG + D007 effect release', 'RUN_LOCK + recovery pair', 'post-install acceptance incl. role/mobile tests'],
 'runtime_unverified': 'No Odoo runtime was available to this lane: module load, upgrade, ORM view validation, ACL/record rules, OWL render and 390 px are NOT_RUN.'}
out = pathlib.Path(__file__).resolve().parent / 'RC03b_RELEASE_IDENTITY_v1.json'
out.write_text(json.dumps(rec, indent=1, sort_keys=True) + '\n'); b = out.read_bytes(); print(out.name, len(b), hashlib.sha256(b).hexdigest())
