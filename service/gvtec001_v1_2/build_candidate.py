#!/usr/bin/env python3
"""Generate the GV-TEC-001 v1.2 candidate (append-only contract delta) and the ERROR_CLASS_REGISTRY. Deterministic. Writes nothing to any Catalogue."""
import json, hashlib, pathlib
root = pathlib.Path(__file__).resolve().parent
TAG = '[HOSTINGER-V20-RELEASE-QUALIFICATION-v1.2-CANDIDATE]'
# status PASSED_OFFLINE needs test ids that appear as PASS lines in the supplied logs; NOT_RUN is an honest open item (owner shown)
E = [
 ('SRC_TRANSFORMED_IN_TRANSPORT', 'pinned digest computed over parsed/re-serialised content', 'PASSED_OFFLINE', ['T01', 'T01b', 'T02', 'T03', 'T11', 'T16a', 'T16b'], 'n8n harness (mock)'),
 ('SRC_TAMPERED_SAME_LENGTH', 'single-bit change, same length', 'PASSED_OFFLINE', ['T07', 'T07b', 'V5'], ''),
 ('SRC_TRUNCATED_OR_PARTIAL', 'short body / missing file after transfer', 'PASSED_OFFLINE', ['T08', 'V6'], ''),
 ('SRC_HTTP_ERROR_BODY', 'error body hashed as if it were the source', 'PASSED_OFFLINE', ['T09', 'T10', 'T10b'], ''),
 ('HASH_ROUTINE_LENGTH_BOUNDARY', 'SHA-256 padding wrong at length = 55 mod 64', 'PASSED_OFFLINE', ['T05', 'T05c', 'T05d', 'T05e'], ''),
 ('DEST_STALE_OR_EXTRA_FILE', 'overlay/stale file at the destination', 'PASSED_OFFLINE', ['V7', 'V12'], ''),
 ('DEST_MANIFEST_SUBSTITUTED', 'manifest differs from the pinned hash', 'PASSED_OFFLINE', ['V4', 'P10'], ''),
 ('DEST_ADDON_MISSING', 'whole addon absent at the destination', 'PASSED_OFFLINE', ['V9', 'V11', 'V28'], ''),
 ('DEST_VERIFIER_NOT_READ_ONLY', 'verifier or prestate script writes to the target', 'PASSED_OFFLINE', ['V13', 'P2', 'P14'], ''),
 ('PRESTATE_DRIFT', 'live addon tree differs from the recorded baseline', 'PASSED_OFFLINE', ['P4'], ''),
 ('PRESTATE_PREREQUISITE_OR_DISCOVERY', 'tool, container or Odoo addons_path missing', 'PASSED_OFFLINE', ['P5', 'P6', 'P8', 'P9'], 'shim only'),
 ('PRESTATE_DB_FACTS_UNAVAILABLE', 'database.uuid or DB facts unavailable', 'PASSED_OFFLINE', ['P11', 'P12'], ''),
 ('SRC_UNDECLARED_REVERSE_DEPENDENCY', 'data references a model only a dependent addon defines', 'PASSED_OFFLINE', ['STATIC_F1'], 'static check only; Odoo runtime NOT_RUN'),
 ('MIGRATION_MISSING_FOR_NEW_VIEW', 'new ir.ui.view without a visibility-default pre-migrate', 'PASSED_OFFLINE', ['STATIC_F5'], 'static check only; Odoo runtime NOT_RUN'),
 ('RENDER_INJECTION_OR_BAD_INPUT', 'hostile registry text / invalid object id / trail', 'PASSED_OFFLINE', ['D009_T3_A_NO_EXCEPTION', 'D009_T3_A_NO_REFLECTION', 'D009_T3_B_HOSTILE_REGISTRY'], 'bundled registry v0.3; Odoo stubbed'),
 ('DEST_SYMLINK_OR_SPECIAL_ENTRY', 'symlink (file, directory, dangling, addon root, addons_path entry), FIFO or device in the addon tree', 'PASSED_OFFLINE', ['V12', 'V14', 'V15', 'V16', 'V17', 'V21', 'V26', 'P15', 'P20'], 'V14 reproduces the externally reported false MATCH_ALL; mutation control re-introduces it and fails V14-V16,P15'),
 ('DEST_UNEXPECTED_DIRECTORY', 'empty or extra directory not implied by the manifest', 'PASSED_OFFLINE', ['V20'], ''),
 ('DEST_RECEIPT_INSIDE_TREE', 'receipt or output written inside an examined addon tree', 'PASSED_OFFLINE', ['V18', 'V19', 'P13'], ''),
 ('DEST_ADDON_SHADOWED', 'same addon in two addons_path entries', 'PASSED_OFFLINE', ['V25', 'P7'], 'Odoo implicit core path not examined'),
 ('VERIFIED_DIR_NOT_THE_DIR_ODOO_LOADS', 'verifying a directory other than the addons_path Odoo loads; container vs host mount disagree', 'PASSED_OFFLINE', ['V23', 'V24', 'P1', 'P9', 'P17', 'P18'], 'shim only: in-container call form and /proc/1/cmdline semantics NOT yet seen on the real host'),
 ('SECRET_LEAK_IN_RECEIPT', 'password or raw command line captured in a receipt', 'PASSED_OFFLINE', ['P19'], 'mutation control leaks the command line and fails P19'),
 ('ODOO_DB_TARGET_MISMATCH', 'check aimed at a different database than Odoo is configured for', 'PASSED_OFFLINE', ['P16'], ''),
 ('FABRICATED_APPROVAL', 'syntactically valid but unattributable approval', 'NOT_RUN', [], 'D007 executor not built; earlier C02 false-GO is the original failure to retest'),
 ('APPROVAL_WRONG_SCOPE_OR_EXPIRED', 'valid approval for another scope or past expiry', 'NOT_RUN', [], 'D007'),
 ('TARGET_IDENTITY_MISMATCH', 'wrong host, database or database.uuid', 'NOT_RUN', [], 'needs the console P0 receipt; script tested only against a shim'),
 ('RUN_LOCK_MISSING_OR_STALE', 'no lock, stale lock, or second writer', 'NOT_RUN', [], 'D007'),
 ('RECOVERY_PAIR_MISSING_OR_INCONSISTENT', 'no consistent DB+filestore backup, or restore fails', 'NOT_RUN', [], 'D007; VM-level backups are stale and VM-wide'),
 ('UPGRADE_FAILS_MIDWAY', 'module upgrade fails; recovery by rehearsed restore', 'NOT_RUN', [], 'D007 isolated rehearsal'),
 ('WRONG_VERSION_OR_MISSING_UI_AFTER_RUN', 'runtime success but wrong version or no UI', 'NOT_RUN', [], 'post-install acceptance'),
 ('ROLE_OR_CONTEXT_LEAK', 'collaborator denied/over-granted; cross-Context or sudo disclosure', 'NOT_RUN', [], 'runtime role tests; static reading only'),
 ('BUILDER_SELF_ASSURANCE', 'builder supplies its own independent assurance', 'NOT_RUN', [], 'D009 independence gate not exercised'),
 ('RECEIPT_EXPIRED_OR_ROUTE_REVOKED', 'capability receipt expired or route revoked', 'NOT_RUN', [], 'handshake endpoint not built'),
 ('REQUEST_REPLAYED_TWICE', 'same request twice must not double-write', 'NOT_RUN', [], 'read path idempotent only (T04); no protected write exists to test'),
 ('CALLER_CAPABILITY_CLAIM_FAILS', 'AI claims a tool that fails on use', 'NOT_RUN', [], 'handshake endpoint not built'),
 ('P0_ON_REAL_HOST', 'P0 receipt produced on the real Hostinger host (python3 -I -c in the real Odoo image, real /proc/1/cmdline, real mounts)', 'NOT_RUN', [], 'D007 console; only a shim has run'),
 ('DIRECT_ACTION_ACCESS_BYPASS', 'user without the menu opens the verb catalogue action by id/URL/RPC', 'NOT_RUN', [], 'F3 acceptance (runtime, per role)'),
 ('BACKEND_ACL_WRITE_ATTEMPT_BY_COLLABORATOR', 'collaborator create/write/unlink on synapsys.verb via RPC despite read-only XML views', 'NOT_RUN', [], 'F3 acceptance: XML read-only is UI-only'),
 ('CROSS_CONTEXT_READ_THROUGH_NEW_MENUS', 'collaborator in one Context reads another Context through the new menus or journey', 'NOT_RUN', [], 'F3/F4 acceptance'),
]
reg = {'schema': 'synapsys.error-class-registry/1', 'rule': 'A class may be PASSED_OFFLINE only if every listed test id appears as a PASS line in the supplied logs. Service maturity is ENFORCED only when no class is NOT_RUN.',
       'classes': [{'code': c, 'description': d, 'status': s, 'tests': t, 'note': n} for c, d, s, t, n in E]}
passed = sum(1 for x in E if x[2] == 'PASSED_OFFLINE'); total = len(E)
APP = {
 'x_execution_input_contract': TAG + ' Release input binds, by value: Work Object and state revision/hash; Git commit and per-addon release manifest sha256; verifier and prestate-script sha256; target identity (host, container image id, database name, database.uuid taken from the P0 receipt); the scoped CHG id and D007 effect-release id; recorded Steward decisions; the non-Claude D009 assessment of the same commit; recovery-pair ids; RUN_LOCK id; invocation id and idempotency key (sha256 over the preceding bindings) with an expiry. A file format, archive or transfer method is never a release identity.',
 'x_deterministic_tech_requirements': TAG + ' (1) Source is a Git-pinned commit reproducible from baseline plus patch, with static dependency and migration checks. (2) Every reader of a pinned source verifies raw received bytes before decoding; a transformed copy never redefines a pinned digest; every SHA-256 routine passes the length-boundary conformance test. (3) Transfer may use any QUALIFIED route; success is the destination verifier returning MATCH_ALL, not the transport exit status. The verifier is read-only and fail-closed, runs INSIDE the Odoo container over the addons_path Odoo is configured to load (first-match resolution, duplicates refused), cross-checks the host mount, refuses every symlink (file, directory, dangling, addon root, path entry), special files, unexpected directories and receipts inside the examined tree, and never records passwords. (4) A read-only P0 prestate receipt (addon-tree match to baseline, database.uuid, image id, compose hash, DB facts) precedes any write. (5) Installation requires a consistent DB+filestore recovery pair, a throwaway restore, a rehearsed upgrade with injected failure, one RUN_LOCK holder. A VM-wide backup is not a rollback for one addon.',
 'x_execution_outcome_schema': TAG + ' Return per stage: status in NOT_RUN | PASSED | FAILED | HELD with an error-class code from ERROR_CLASS_REGISTRY; p0 receipt (verdict and sha256), staging receipt, rehearsal log hashes, install log hashes, post-install readback. Never label an untested stage PASSED. Report registry maturity as passed/total error classes and list every NOT_RUN class.',
 'x_execution_profile_requirements': TAG + ' Stage progression: source -> transfer -> prestate -> rehearsal -> authority -> install -> accept/recover, each with exact release id and truthful state. A later stage starts when its own prerequisites hold; post-install acceptance is never a prerequisite for starting an authorised install. After two failures in the same transport class, change the failure mechanism or the qualified route rather than repeat. Independent source work continues while a protected effect is held.',
 'x_authority_gate_schema': TAG + ' The executor reads an attributable CHG and bounded D007 release from authoritative services and verifies scope, target identity, tree identity, validity, state and the non-Claude assessment. Caller-supplied strings, local matching hashes, design-only CHGs, catalogue status, chat approvals and builder self-assurance are not authority. A direct Steward decision is recorded by id and still needs its CHG/D007 effect release.',
 'x_provider_fallback_policy': TAG + ' Select the transport from OBSERVED capability, not assumption. Qualified today: the Steward/D007 console route. SSH/rsync from an AI runtime and Hostinger-API compose delivery are UNINSTALLED until qualified; each needs the same identity, rights, destination verification and negative tests. A missing qualified route is HOLD, not a reason to weaken a check.',
 'x_return_acceptance_schema': TAG + ' Reject a result lacking: destination MATCH_ALL receipt for the frozen manifest; P0 receipt MATCH_ALL with a non-empty database.uuid; recovery proof; the D009 assessment of the same commit; the D007 effect release; or reporting any NOT_RUN error class as passed.',
 'x_observation_learning_contract': TAG + ' Anti-fragility loop: every failure or near-miss yields (1) the failure mechanism, (2) a regression test that reproduces the original failure, (3) a control proving that test can fail, (4) a versioned append to this contract, (5) a recurrence check in the next comparable cycle. Measure recurrence, time-to-detect and NOT_RUN count. No claim of improvement without a second comparable cycle.',
}
CAP_ADD = ['release_native_actor_probe', 'independent_assurer_probe', 'destination_hash_verification_any_transport', 'read_only_prestate_receipt', 'isolated_restore_rehearsal',
           'raw_byte_source_integrity', 'approved_effect_and_authority_resolver', 'capability_complement_routing', 'original_failure_adversarial_retest', 'mutation_controlled_test_authoring', 'role_browser_mobile_acceptance']
cand = {'schema': 'synapsys.gv-tec-001.release-service-upgrade/1.2-CANDIDATE', 'status': 'CANDIDATE_NOT_APPLIED__NO_SERVICE_WRITE_AUTHORISED', 'supersedes_candidate': 'v1_1 sha256 c553c4f99968cd15adbccd2eaf7197f0db36b8914cd5b9fa44a442b7fa540e7e',
        'target': {'model': 'x_service_catalogue', 'record_id': 35, 'service_code': 'GV-TEC-001', 'method': 'D002-WRB'},
        'operation': 'APPEND_ONLY_WITH_PREFIX_CHECK__READ_LIVE_BEFORE_WRITE', 'separator': '\n\n', 'append': APP, 'capability_add_values': CAP_ADD,
        'removed_from_v1_1': ['ssh_rsync_target_identity_and_hash (SSH/rsync is not a qualified route; replaced by destination_hash_verification_any_transport)'],
        'forbidden_automatic_changes': ['x_service_status', 'x_processability_state', 'x_validation_status', 'x_method_id', 'x_canonical_status', 'x_service_ppv_ceiling', 'x_lifecycle_gate', 'x_active'],
        'maturity_claim': {'error_classes_total': total, 'passed_offline': passed, 'not_run': total - passed, 'enforced': False, 'registry': 'ERROR_CLASS_REGISTRY.json'},
        'requires_before_write': ['read live record and run check_service_candidate.py (exit 0)', 'D001 + D004 material-scope decision', 'attributable CHG + D007 effect release', 'non-Claude D009 assessment of this exact candidate', 'readback after write']}
(root / 'ERROR_CLASS_REGISTRY.json').write_text(json.dumps(reg, indent=1, sort_keys=True) + '\n')
(root / 'GV-TEC-001_V20_release_service_upgrade_v1_2_CANDIDATE.json').write_text(json.dumps(cand, indent=1, sort_keys=True) + '\n')
for f in ('ERROR_CLASS_REGISTRY.json', 'GV-TEC-001_V20_release_service_upgrade_v1_2_CANDIDATE.json'):
    b = (root / f).read_bytes(); print(f, len(b), hashlib.sha256(b).hexdigest())
print('classes total=%d passed_offline=%d not_run=%d' % (total, passed, total - passed))
