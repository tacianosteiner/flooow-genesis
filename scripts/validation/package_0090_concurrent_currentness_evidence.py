"""Collect a deliberately incomplete concurrent gate without invented measurements."""
import json
import base64
from pathlib import Path
import package_0090_source_closure as q
import package_0090_concurrent_currentness as c


def save(name, value):
    (c.OUT / name).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def main():
    baseline = c.BASELINE
    for ref in ['HEAD', 'origin/checkpoint/package-0090-cloud-handoff']:
        q.require(q.command(['git', 'merge-base', '--is-ancestor', baseline, ref], check=False).returncode == 0, 'Expected baseline is not an ancestor: ' + ref)
    q.require(q.git('branch', '--show-current').decode().strip() == 'checkpoint/package-0090-cloud-handoff', 'Wrong branch')
    protected = {'main': '77d482c97a663a527dcacc85036c7577dfc92782', 'feature/room-v2-executive-product-evolution': '22181b5d821e343658928e6feaa06b96838757e2', 'research/global-commerce-signal-intelligence': '27019d7b3093b7a7d9aeb67d0c099756b13e005a'}
    for ref, head in protected.items():
        for actual in [ref, 'origin/' + ref]:
            q.require(q.git('rev-parse', actual).decode().strip() == head, 'Protected ref changed: ' + actual)
    paths = [q.V043.relative_to(q.ROOT).as_posix(),
             'docs/adr/ADR-0090-governed-offline-field-proof-exclusive-capability-composition.md',
             'docs/specifications/SPEC-0090-governed-offline-field-proof-exclusive-capability-composition.md',
             'docs/evidence/package-0090-g3f4-full-domain-fixture-contract/NATIVE-HEALTH-CONTRACT.md',
             'docs/evidence/package-0090-g3f4-full-domain-fixture-contract/NATIVE-HEALTH-DESIGN.json',
             'docs/evidence/package-0090-native-health-100us-feasibility/freshness-contract.json']
    paths += [p.relative_to(q.ROOT).as_posix() for p in (q.ROOT / 'scripts/validation').glob('*0090_native_100us*') if p.is_file()]
    paths += ['scripts/validation/package_0090_s04_native_health.c']
    freeze = {}
    for path in paths:
        data = q.git('show', baseline + ':' + path)
        q.require(data == (q.ROOT / path).read_bytes().replace(b'\r\n', b'\n'), 'Frozen source changed: ' + path)
        freeze[path] = {'git_blob': q.git('rev-parse', baseline + ':' + path).decode().strip(), 'git_lf_sha256': q.sha(data), 'working_bytes_sha256': q.sha((q.ROOT / path).read_bytes())}
    q.require(freeze[paths[0]]['git_lf_sha256'] == q.SOURCE_HASH, 'Canonical hash differs')
    q.require(b'Package 0090 V043 implementation closure is incomplete; execution denied' in q.V043.read_bytes(), 'Fence missing')
    for p in q.MIGRATIONS.glob('V*.sql'):
        if int(p.name.split('__')[0][1:]) <= 42:
            q.require(q.git('show', q.FROZEN + ':' + p.relative_to(q.ROOT).as_posix()) == p.read_bytes().replace(b'\r\n', b'\n'), 'Frozen migration changed')
    save('source-freeze.json', dict(baseline=baseline, initial_local_head=baseline, initial_remote_head=baseline, initial_tracked_dirty=0, initial_staged=0, sources=freeze, protected_refs=protected, frozen_migrations_unchanged=True, canonical_executed=False))
    runs = []
    for name in ['start-1', 'start-2']:
        folder = c.OUT / name
        runtime = json.loads((folder / 'foundation-runtime.json').read_text())
        proof = json.loads((folder / 'currentness-runtime.json').read_text())
        q.require(not runtime['errors'] and runtime['owned_runtime_destroyed'], 'Runtime failure or cleanup incomplete')
        q.require(len(proof['cases']) == 12 and all(x['passed'] for x in proof['cases']), 'Incomplete currentness cases')
        for filename, digest in runtime['recipe_hashes'].items():
            candidate = q.ROOT / 'scripts/validation' / filename
            if filename == Path(c.__file__).name:
                archived = base64.b64decode(json.loads((folder / 'tested-currentness-recipe.json').read_text())['tested_source_bytes'], validate=True)
                q.require(q.sha(archived) == digest, 'Tested recipe archive differs')
                q.require(archived.rstrip() == candidate.read_bytes().rstrip(), 'Archive and current recipe differ beyond trailing whitespace')
                continue
            q.require(candidate.is_file() and q.sha(candidate.read_bytes()) == digest, 'Current runtime recipe drift: ' + filename)
        runs.append(dict(name=name, id=runtime['isolation']['id'], volume=runtime['isolation']['volume'], cases=proof['cases'], destroyed=True))
    q.require(runs[0]['id'] != runs[1]['id'] and runs[0]['volume'] != runs[1]['volume'], 'Reused runtime')
    native = 'docs/evidence/package-0090-g3f4-full-domain-fixture-contract/NATIVE-HEALTH-CONTRACT.md:5,7'
    design = 'docs/evidence/package-0090-g3f4-full-domain-fixture-contract/NATIVE-HEALTH-DESIGN.json'
    spec = 'docs/specifications/SPEC-0090-governed-offline-field-proof-exclusive-capability-composition.md'
    user = 'User concurrent gate phases 1,2,4,14,15; TEST_ONLY authority adopted in ADR/SPEC'
    rows = [
        ('approved_source_expectations', 'IMMUTABLE_PER_DEPLOYMENT', user, 'Before bootstrap; compare against frozen Git/source hashes', 'Expected bytes are constants; their equality is not a runtime observation', 'Different source/fixture/decision bytes'),
        ('postgres_system_identity', 'IMMUTABLE_PER_INCARNATION', native, 'Bootstrap plus retained live exact server anchor through T10', 'Cluster identity alone does not prove the same current process', 'Server restart/replacement/anchor loss/unknown lineage'),
        ('migration_history', 'CURRENT_PER_EPOCH', native, 'Fresh independently observed data; writer invalidation/fence retained through T10', 'Observed admin can change history; RR may retain stale rows', 'INSERT/UPDATE/DELETE/TRUNCATE or replacement'),
        ('role_OIDs_and_attributes', 'CURRENT_PER_EPOCH', native, 'Fresh catalog plus change detection through T10', 'ALTER ROLE remains possible under history lock', 'Role replacement or attribute modification'),
        ('role_memberships', 'CURRENT_PER_EPOCH', spec, 'Fresh full applicable membership reconciliation through T10', 'Zero-membership requirement is absent from legacy query', 'GRANT/REVOKE role membership'),
        ('ACL_catalog_expectations', 'CURRENT_PER_EPOCH', spec, 'Applicable schema/table/column/function/type/default privileges and owners through T10', 'Actual write ACL changed without altering legacy hash', 'GRANT/REVOKE/owner or catalog definition changes'),
        ('function_security_context', 'CURRENT_PER_EPOCH', spec, 'Owner/definer/strict/volatility/search_path/signatures/dependencies through T10', 'S04 owner mutation is invisible to legacy digest', 'ALTER/CREATE/DROP function, owner or resolution changes'),
        ('participant_generation', 'IMMUTABLE_PER_GENERATION', design, 'Enrollment publication plus exact current registry at each event and T10', 'Generation constant is valid only while enrollment is current', 'Replacement/revocation/registry revision/unknown generation'),
        ('process_identity', 'CURRENT_PER_PARTICIPANT_EVENT', native, 'Authenticated event and immediately before consumption', 'PID alone is insufficient', 'Exit/replacement/exec/host or namespace change'),
        ('pidfd_target', 'CURRENT_PER_PARTICIPANT_EVENT', native, 'Setup correlation plus retained pidfd live exact target at event and T10', 'Retained kernel anchor avoids PID reuse but does not prove functional progress', 'Anchor loss/exit/wrong target'),
        ('binary_hash', 'IMMUTABLE_PER_GENERATION', native, 'Proven executable/bootstrap binding plus exec/change invalidation', 'Frozen file hash does not identify every live executable transition', 'Exec or executable/bootstrap binding change'),
        ('native_library_hash', 'IMMUTABLE_PER_GENERATION', spec, 'Proven loaded module identity plus lifecycle invalidation', 'Build hash alone does not prove current loaded module', 'Module replacement/reload/new generation'),
        ('dependency_digest', 'CURRENT_PER_EPOCH', native, 'Fresh authoritative dependencies bound to same epoch and retained through T10', 'A digest value is not its own currentness proof', 'Dependency data/catalog/process/registry revision changes'),
        ('policy_version_digest_activation', 'CURRENT_PER_EPOCH', spec, 'Committed exact approved bytes/version/digest/time/audit through T10', 'Expected immutable approval does not prevent physical ADMIN row changes', 'Policy row/audit/activation change or unknown outcome'),
        ('readiness_dependencies', 'CURRENT_PER_EPOCH', spec, 'No eligibility until fresh full health; revalidate exact scope/current dependencies', 'No legitimate readiness exists in this campaign', 'Health loss/stale proof/policy or incarnation change'),
        ('signature_public_key_expectation', 'IMMUTABLE_PER_GENERATION', design, 'Authenticated enrollment and current publication/key identity each epoch', 'Public key may be a fixed expectation; fresh signature result cannot be cached', 'Key/publication/enrollment/generation replacement'),
        ('signature_and_functional_result', 'CURRENT_PER_PARTICIPANT_EVENT', native, 'Required actual fresh work/signature and independent observation for exact original epoch', 'Heartbeat/existence is not completed work', 'Wrong work/signature/nonce/context or stale emission'),
        ('counter_nonce_catalog_epoch', 'CURRENT_PER_PARTICIPANT_EVENT', user, 'Each message, branch join and authenticated T9/T10 consumer', 'All results must bind same exact epoch/context without replay', 'Counter reuse/nonce mismatch/torn context/replay'),
    ]
    model = [dict(field=f, normative_source=s, currentness_class=cl, revalidation=w, why=why, invalidation=i, prebinding_proven=(f == 'approved_source_expectations')) for f,cl,s,w,why,i in rows]
    save('currentness-model.json', dict(fields=model, numeric_threshold_ns=100000, inclusive=True, original_emission_clock='CLOCK_BOOTTIME', expected_constants_are_not_current_truth=True))
    gaps = ['Legacy fresh digest omits ACLs that permit history writes', 'Legacy fresh digest omits role membership', 'Legacy fresh digest omits function owner/security context', 'RR consistency permits stale committed history', 'No invalidation mechanism spans final DB observation through T10']
    save('prebinding-proof.json', dict(currentness_prebinding_proven=False, prebound_fields=['approved_source_expectations (expected constants only)'], per_epoch_fields=[x['field'] for x in model if x['currentness_class']=='CURRENT_PER_EPOCH'], per_event_fields=[x['field'] for x in model if x['currentness_class']=='CURRENT_PER_PARTICIPANT_EVENT'], incarnation_generation_fields_provisional=[x['field'] for x in model if x['currentness_class'] in ['IMMUTABLE_PER_INCARNATION','IMMUTABLE_PER_GENERATION']], gaps=gaps, runs=runs, distinct_tests=12, case_executions=24, foundation_distinct_cases_reused=93, runtime_recipe_mode=['normal','python -O']))
    save('snapshot-coherence.json', dict(status='NOT_PROVEN', concurrent_validation_snapshot_coherent=False, repeatable_read_consistent_history_but_not_current=True, history_share_lock_blocks_DML=True, history_lock_guards_role_catalog=False, phase_4_concurrent_multi_session_experiment_executed=False, torn_proof_prevention_implemented=False, requirement='Complete applicable catalog/dependency coverage and proven writer/revision invalidation through T10; RR alone insufficient'))
    pending = dict(status='NOT_IMPLEMENTED_NOT_QUALIFIED', reason='Currentness counterexamples require a bounded writer/epoch invalidation implementation before a timing control can qualify', phase_3_onward_complete=False, new_measurement_samples=0, new_benchmark_epochs=0, no_prior_results_relabelled=True)
    for name in ['concurrent-validation-dag.json','kernel-attribution.json','epoch-release-distribution.json','hot-path-v2.json','participant-v2-distributions.json','complete-epoch-v2.json']:
        save(name, pending)
    for name in ['fresh-control-v2.json','native-positive-v2.json','native-negative-v2.json','replacement-restart-v2.json']:
        save(name, dict(status='NOT_EXECUTED', valid_fresh_control=False, first_path_native_health_ready=False, reason='No qualified concurrent control; currentness and concurrent pipeline remain incomplete'))
    save('feasibility-v2.json', dict(status='INCOMPLETE_CURRENTNESS_SUBGATE', feasibility='INCONCLUSIVE', valid_fresh_control=False, new_lower_bound_ns=None, historical_best_complete_epoch_us=381.730, historical_result_is_not_a_v2_measurement=True, timing_amendment_required_for_further_progress=False, remaining_legitimate_avenues=['Bounded writer/revision invalidation with full catalog coverage through T10', 'Contract-preserving nonblocking receive and incremental validation', 'Coherent catalog/crypto overlap', 'Authenticated guard/consumer handoff', 'Unprivileged scheduler/transport attribution'], mission_complete=False, distinct_new_tests=12, new_measurements=0, failures=0, findings_scope='Currentness counterexamples only; full native security review not performed'))
    save('READINESS.json', dict(created=False, header_registered=False, original_attestation_registered=False, auditor_slot_authentic=False, s04_executed=False, s04_actual_rows=None, s04_bound=0, s04_unbound=33, global_bound=0, global_unbound=851, production_contacted=False, shared_db_contacted=False, execution_authority='BLOCKED', recovery_authority='BLOCKED', room_operational=False))
    report = q.ROOT / 'docs/evidence/PACKAGE-0090-native-health-concurrent-100us.md'
    report.write_text('''# Package 0090 concurrent native health 100us gate — currentness subgate\n\nThe requested concurrent gate is **incomplete**. Phases 0–2 produced a source freeze, dependency classification and reproducible counterexamples; the concurrent implementation and 1000-epoch-per-topology campaign have not run. No concurrent timing control, native readiness, negative/restart closure, header/original registration or S04 positive is claimed.\n\nTwo separately created PostgreSQL 18.4 targets each passed 12 currentness assertions and 93 reused foundation assertions, with no runtime errors. The second ran Python with `-O`; both targets and their private credentials were destroyed. This is 12 distinct new tests, 24 currentness executions, zero new measurement samples and zero benchmark epochs. Successful counterexamples are not native health positives.\n\nThe legacy digest misses actual history-write ACL grants, role membership and S04 SECURITY DEFINER owner changes. A repeatable-read observer retained the original history digest while another administrator committed a checksum change visible to a fresh connection. A fresh query also left an unguarded observation-to-consumer interval. An actual SHARE lock denied history UPDATE with 55P03 but permitted ALTER ROLE concurrently. All mutations were reversed before target destruction. These tests establish insufficiency of the tested mechanisms, not impossibility of a valid concurrent design.\n\nOnly independently frozen expected source bytes are proven prebound constants. Current runtime identity, generation applicability, loaded binary/module bindings, ACL/catalog/policy dependencies and final-consumer invalidation remain unqualified. Snapshot consistency must not be substituted for currentness. The model classifies all requested dependencies and records their invalidation requirements.\n\nFeasibility remains INCONCLUSIVE. The previous 381.730us result is historical and is not a new concurrent measurement or physical lower bound. No timing amendment is justified: material implementation avenues remain. The 100000ns inclusive bound and original CLOCK_BOOTTIME emission remain unchanged. No READY row or S04 call occurred. The canonical V043 fence and all V001–V042 files and protected refs remain unchanged. Only the separately derived, hash-verified qualification body was used in disposable databases.\n\nThe next bounded action is to implement and adversarially test complete catalog/dependency coverage plus writer/revision invalidation through T10, then the concurrent DAG and authenticated handoff before measuring both topologies. This successor action was not executed. The full requested mission remains outstanding.\n''', encoding='utf-8')
    inputs = {p.relative_to(q.ROOT).as_posix(): q.sha(p.read_bytes()) for p in [Path(__file__), Path(c.__file__), q.ROOT/'scripts/validation/package_0090_active_foundation.py']}
    outputs = {p.relative_to(q.ROOT).as_posix(): q.sha(p.read_bytes()) for p in sorted(c.OUT.rglob('*')) if p.is_file() and p.name != 'SHA256-MANIFEST.json'}
    outputs[report.relative_to(q.ROOT).as_posix()] = q.sha(report.read_bytes())
    save('SHA256-MANIFEST.json', dict(inputs=inputs, outputs=outputs, baseline=baseline, canonical_git_lf_sha256=q.SOURCE_HASH))
    print(json.dumps(dict(status='INCOMPLETE_CURRENTNESS_SUBGATE', distinct_tests=12, measurement_samples=0, epochs=0, failures=0, targets_destroyed=2)))


if __name__ == '__main__':
    main()
