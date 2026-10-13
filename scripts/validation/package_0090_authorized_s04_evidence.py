"""Collect earned activation evidence; retain a failed first-path gate honestly."""
import collections
import json
from pathlib import Path
import package_0090_authorized_s04 as a
import package_0090_source_closure as q


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def collect():
    root = a.OUT
    records = []; health = []; activations = []; cohorts = []
    for name in ['run-4', 'run-5']:
        folder = root / name
        runtime = read(folder / 'foundation-runtime.json')
        q.require(not runtime['errors'] and runtime['owned_runtime_destroyed'], 'Runtime errors or retained resources')
        q.require(len(runtime['cases']) == 132 and all(c['passed'] for c in runtime['cases']), 'Accepted test cohort differs')
        for filename, digest in runtime['recipe_hashes'].items():
            q.require(q.sha((q.ROOT / 'scripts/validation' / filename).read_bytes()) == digest, 'Final runner drift: ' + filename)
        h = read(folder / 'native-health-runtime.json')
        q.require(h['harness_source_sha256'] == q.sha((q.ROOT / 'scripts/validation/package_0090_s04_native_health.c').read_bytes()), 'Native source drift')
        q.require(len(h['participants']) == 7 and h['identity_and_work_complete'] and not h['native_health_ready'], 'Measured health result differs')
        q.require(all(p['age_ns'] > 100000 and not p['fresh'] for p in h['participants']), 'Expected actual stale observations missing')
        activation = read(folder / 'test-policy-activation.json')
        chain = read(folder / 'test-admin-audit-chain.json')
        actual_store = [json.loads(line) for line in Path(chain['authoritative_path']).read_text().splitlines()]
        q.require(actual_store == chain['records'], 'Authoritative external audit differs from exported proof')
        a.validate_audit(chain['records'], chain['trusted_tip'], activation['binding'])
        q.require(activation['proven'] and activation['replay_proven'], 'Activation proof absent')
        records.append(runtime); health.append(h); activations.append(activation)
        cohorts.append([(c['name'], c['passed'], c['group']) for c in runtime['cases']])
    q.require(cohorts[0] == cohorts[1], 'Semantic assertion cohort differs')
    q.require(records[0]['recipe_hashes'] == records[1]['recipe_hashes'], 'Final recipe mismatch')
    q.require(health[0]['harness_binary_sha256'] == health[1]['harness_binary_sha256'], 'Native binary mismatch')
    q.require(records[0]['isolation']['id'] != records[1]['isolation']['id'] and records[0]['isolation']['volume'] != records[1]['isolation']['volume'], 'Disposable target reused')
    q.require(activations[0]['binding']['incarnation_id'] != activations[1]['binding']['incarnation_id'], 'Incarnation reused')
    units = read(root / 'audit-unit-tests.json')
    q.require(units['tests'] == 6 and units['failures'] == units['errors'] == units['skipped'] == 0, 'Unit tests failed')
    groups = dict(collections.Counter(c['group'] for c in records[0]['cases']))
    result = {'baseline': a.BASELINE, 'branch': 'checkpoint/package-0090-cloud-handoff',
              'decision_adopted': True, 'decision_id': a.DECISION, 'identities': a.identities(),
              'test_admin_audit_contract_ready': True, 'test_admin_audit_tamper_evident': True,
              'test_policy_activation_proven': True, 'test_activation_replay_proven': True,
              'test_activation_effective_from_source': 'ADMIN_TRANSACTION_CLOCK_TIMESTAMP_ONCE_TIMESTAMPTZ6_ZERO_OFFSET',
              'native_seven_work_mechanisms_proven': True, 'native_guard_process_independent': True,
              'native_full_contract_proven': False, 'freshness_proven': False,
              'first_path_native_health_ready': False, 'full_package_native_health_ready': False,
              'readiness_created': False, 'readiness_negative_tests_pass': 'NOT_EXECUTED_NO_VALID_CONTROL',
              'immutable_header_registered': False, 'original_attestation_registered': False,
              'auditor_slot_authentic': False, 'authentic_test_auditor_LOGIN_proven': True,
              'active_fixture_precheck': 'FAIL_NATIVE_FRESHNESS_AND_INCOMPLETE_HEALTH_CONTRACT',
              'first_authentic_positive_executed': False, 'first_authentic_positive_pass': False,
              's04_expected_rows': 42, 's04_actual_rows': None, 's04_exact_history_match': False,
              's04_sibling_attacks_pass': 'NOT_EXECUTED', 's04_search_path_attacks_pass': 'NOT_EXECUTED',
              'base_global_candidate_contexts': 818, 's04_static_call_sites': 45, 's04_static_candidate_contexts': 33,
              's04_final_contexts': 33, 's04_contexts_bound': 0, 's04_contexts_unbound': 33,
              'global_bound_call_shapes': 0, 'global_unbound_call_shapes': 851,
              's04_null_consumer_complete': False, 's04_acl_complete': False,
              'G1': 'PARTIAL', 'G2': 'PARTIAL', 'G3': 'PARTIAL_WORK_MECHANISMS_ONLY', 'G4': 'PARTIAL_ACTIVATION_ONLY',
              'G5': 'PARTIAL', 'G6': 'PARTIAL', 'G7': 'PARTIAL_TEST_ADMIN_PROVENANCE_ONLY', 'G8': 'PARTIAL',
              'active_fixture_foundation_ready': False, 'first_positive_fixture_ready': False, 'full_fixture_ready': False,
              'active_loader_reproducible': False, 'activation_and_stale_gate_reproduced': True,
              'accepted_runs': ['run-4', 'run-5'], 'runtime_assertions_distinct': 132,
              'unit_tests_distinct': 6, 'total_distinct_tests': 138, 'accepted_failures': 0,
              'case_groups': groups, 'activation_tests': 18, 'audit_tests': 18, 'native_health_tests': 8,
              'readiness_tests': 2, 'header_attestation_prerequisite_tests': 9, 'header_attestation_registration_tests': 0,
              'slot_LOGIN_tests': 4, 'canonical_slot_binding_tests': 0, 's04_positive_tests': 0,
              's04_negative_tests': 0, 'search_path_tests': 0, 'semantic_binding_tests': 0, 'acl_tests': 79,
              'B01': 'OPEN', 'B02': 'OPEN', 'B03': 'OPEN', 'B04': 'OPEN', 'B05': 'OPEN', 'B06': 'OPEN', 'B07': 'OPEN', 'B08': 'OPEN',
              'known_blocker_groups_remaining': 8, 'scoped_blocker_count': 1,
              'blocker': 'Complete first-path native-health gate unproven: every independently observed work witness is stale under100us; full original-approval lineage/replacement/negative closure remains unqualified',
              'HIGH': 'UNKNOWN_S04_RUNTIME_REVIEW_NOT_EXECUTED', 'MEDIUM': 'UNKNOWN_S04_RUNTIME_REVIEW_NOT_EXECUTED', 'LOW': 'UNKNOWN_S04_RUNTIME_REVIEW_NOT_EXECUTED',
              'canonical_source_sha256': q.SOURCE_HASH, 'canonical_v043_mutated': False, 'canonical_v043_executed': False,
              'production_policy_created': False, 'production_key_created': False, 'field_authority_granted': False,
              'shared_database_contacted': False, 'production_contacted': False,
              'execution_authority': 'BLOCKED', 'recovery_authority': 'BLOCKED', 'ROOM_OPERATIONAL': False, 'NEXT_EXECUTED': False}
    a.save(root, 'READINESS.json', result)
    a.save(root, 'test-admin-audit-chain.json', {'runs': [read(root / name / 'test-admin-audit-chain.json') for name in result['accepted_runs']],
           'external_audit_not_Package_table': True, 'complete_chain_validated': True})
    a.save(root, 'test-policy-activation.json', {'runs': activations, 'proven': True, 'reproduced': True,
            'absolute_timestamps_differ': True, 'same_zero_offset_recipe': True})
    old_contract = read(q.ROOT / 'docs/evidence/package-0090-test-activation-native-health-first-positive/native-health-contract.json')
    a.save(root, 'native-health-contract.json', {'original_normative_reconstruction': old_contract,
          'superseding_TEST_authority': read(root / 'accepted-test-decision.json'),
          'production_generation_authority': False, 'full_contract_proven': False,
          'time_window_ns': 100000, 'interpretation': 'Conservative all-witness original-emission freshness at independent promotion observation; no alternate window adopted'})
    a.save(root, 'native-health-runtime.json', {'runs': health, 'all_seven_work_mechanisms_observed': True,
          'health_ready': False, 'negative_campaign_complete': False,
          'minimum_age_ns': min(p['age_ns'] for h in health for p in h['participants']),
          'maximum_age_ns': max(p['age_ns'] for h in health for p in h['participants']),
          'global_impossibility_proven': False, 'scope': 'Actual implemented parallel harness; not every possible implementation'})
    for name in ['readiness-runtime.json','header-original-registration.json','auditor-slot-runtime.json','s04-runtime.json',
                 's04-negative-runtime.json','s04-search-path-runtime.json','s04-semantic-runtime.json','s04-null-runtime.json','s04-acl-runtime.json']:
        a.save(root, name, {'runs': [read(root / run / name) for run in result['accepted_runs']],
               'status': 'NOT_EXECUTED_FAILED_HEALTH_PRECHECK', 'closure_complete': False})
    a.save(root, 'reproduction.json', {'runs': result['accepted_runs'], 'fresh_containers_and_volumes': True,
            'fresh_deployments_and_incarnations': True, 'same_semantic_assertion_cohort': True,
            'same_recipe_hashes': records[0]['recipe_hashes'] == records[1]['recipe_hashes'],
            'activation_and_denial_reproduced': True, 'ACTIVE_LOADER_REPRODUCIBLE': False,
            'both_targets_destroyed': True})
    attempts = []
    for name in ['run-1', 'run-2', 'run-3']:
        runtime = read(root / name / 'foundation-runtime.json')
        attempts.append({'run': name, 'classification': 'FAILED_DEVELOPMENT' if runtime['errors'] else 'SUPERSEDED_VALID_PARTIAL_PROOF',
                         'errors': runtime['errors'], 'cases': len(runtime['cases']), 'cleanup': runtime['owned_runtime_destroyed'],
                         'raw_evidence_preserved': True, 'counted_in_accepted_campaign': False})
    a.save(root, 'development-attempts.json', {'attempts': attempts, 'not_silently_discarded': True})
    a.save(root, 'driver-provenance.json', {'package': 'psycopg[binary]', 'version': '3.3.6', 'private_temp_location': str(a.PSYCOPG),
            'sha256_files': {p.relative_to(a.PSYCOPG).as_posix(): q.sha(p.read_bytes()) for p in sorted(a.PSYCOPG.rglob('*'))
                             if p.is_file() and p.suffix in ('.py', '.pyd', '.dll')},
            'not_repository_runtime_dependency': True})
    inputs = [q.ROOT / 'scripts/validation' / name for name in ['package_0090_active_foundation.py', 'package_0090_authorized_s04.py',
               'package_0090_s04_native_health.c', 'test_package_0090_authorized_s04_audit.py', 'package_0090_authorized_s04_evidence.py',
               'package_0090_source_closure.py', 'Package0090SourceClosureFlyway.java']]
    inputs += [q.ROOT / 'docs' / subdir / name for subdir, name in [('adr', 'ADR-0090-governed-offline-field-proof-exclusive-capability-composition.md'),
               ('specifications', 'SPEC-0090-governed-offline-field-proof-exclusive-capability-composition.md'),
               ('evidence', 'PACKAGE-0090-authorized-test-activation-native-health-s04.md')]]
    a.save(root, 'SHA256-MANIFEST.json', {'inputs': {p.relative_to(q.ROOT).as_posix(): q.sha(p.read_bytes()) for p in inputs},
        'outputs': {p.relative_to(root).as_posix(): q.sha(p.read_bytes()) for p in sorted(root.rglob('*')) if p.is_file() and p.name != 'SHA256-MANIFEST.json'},
        'canonical_git_lf_sha256': q.sha(q.git('show', 'HEAD:' + q.V043.relative_to(q.ROOT).as_posix()))})
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    collect()
