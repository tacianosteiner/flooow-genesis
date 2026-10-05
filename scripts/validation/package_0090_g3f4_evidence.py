"""Publish sanitized G3F.4 prerequisite evidence, preserving every unexecuted gate."""
import json
from pathlib import Path
import sys
import package_0090_source_gate as source

def publish(work):
    r=json.loads((Path(work)/'record.json').read_text())
    if r.get('gate')!='HOLD' or r.get('counts',{}).get('HIGH')!=1:
        raise RuntimeError('This evidence writer is scoped to the recorded timing HOLD')
    common={k:r[k] for k in ('disposable_project','disposable_volume','postgres_image_digest','baseline','image','server','mounts','protected_database_connection','protected_volume_mount','production_secret_use','disposable_end_state')}
    common['source_gate']='PASS_SOURCE_ONLY_M04_RUNTIME_VALIDATION_REQUIRED'
    common['gate']='HOLD';common['counts']=r['counts'];common['findings']=r['findings']
    target=source.ROOT/'docs/evidence'
    def write(suffix,content):
        path=target/('PACKAGE-0090-G3F-4-'+suffix+'.json')
        with path.open('w',encoding='utf-8',newline='\n') as f:
            json.dump(common|content,f,indent=2);f.write('\n')
    write('INSTALLED-CATALOG',dict(catalog=r['installed_catalog'],objects=r['installed_objects'],native_catalog=r['native_catalog'],native_build=r['native_build'],installed_native_sha256=r['native_installed_binary_sha256'],frozen_migrations=r['frozen_migrations'],v043=r['v043'],flyway_history=r['flyway_history']))
    write('INSTALLED-ACL',dict(acl=r['installed_acl'],roles=r['roles'],service_roles=r['service_roles'],service_execute_matrix=r['service_execute_matrix'],service_effective_acl=r['service_effective_acl'],default_acl_probes=r['default_acl_probes'],default_acl_type_diagnostic=r['default_acl_type_diagnostic'],default_acl_effective_type_probe=r['default_acl_effective_type_probe'],default_acl_leak=r['default_acl_gate'],resolved_findings=r['resolved_findings'],service_login_negative_calls=[x for x in r['runtime_negative_prerequisites']['rows'] if x['case'].startswith('WRONG_SLOT')],probes_removed='YES_TRANSACTION_ROLLBACK_AND_EXPLICIT_PUBLIC_PROBE_DROP',native_acl=r['native_catalog']))
    pending=['REAL_ADAPTER_E2E','FROZEN_OPERATIONAL_PARITY','S10_S14_REAL_RUNTIME','S10_REPLAY_NO_RENEWAL','ORIGINAL_INPUT_RUNTIME_PARITY','NATIVE_ACCEPTED_ARTIFACT_RUNTIME_PARITY','S13_COLD_RUNTIME','ALL18_NEGATIVE_MATRIX','REAL_ROLLBACK','AMBIGUOUS_COMMIT_FAIL_CLOSED','CONCURRENCY_SEMANTICS','RESTART_RECOVERY']
    write('RUNTIME-TESTS',dict(migrations=r['stages'],policy=r['policy'],policy_readiness='NOT_READY_NO_OPERATIONAL_ACTIVATION',timing_fixture=r['timing_fixture'],native_runtime_crypto=r['native_runtime_crypto'],adapter_negative_prerequisites=r['runtime_negative_prerequisites'],endpoint_guard_negative=r['endpoint_guard_negative'],watchdog_freshness_probe=r['watchdog_freshness_probe'],restart_prerequisite_probe=r['restart_prerequisite_probe'],tooling_failures=r['tooling_failures'],dependent_gate_results={k:'NOT_QUALIFIED_TIMING_HOLD' for k in pending},recording_jdbc=False,frozen_stubs=False,direct_legacy_service_call_count=0,direct_legacy_scope='EXECUTED_ADAPTER_DENIAL_PROBES_ONLY_NOT_POSITIVE_E2E'))
    write('CONCURRENCY',dict(status='NOT_EXECUTED_TIMING_QUALIFICATION_REQUIRED',deadlock_count=None,double_effect_count=None,lock_order='NOT_QUALIFIED',concurrency_semantics='NOT_QUALIFIED',required_scenarios=['same binding concurrent mutation','same organization/principal','S13 claims','S14 delivery','S17/S18 decisions','normal runtime/offline barrier','watchdog/readiness'],bounded_two_session_timing_experiment=r['watchdog_freshness_probe'],null_counts_mean='NOT_MEASURED_NOT_ZERO'))
    p=r['watchdog_freshness_probe']
    values={
      'DISPOSABLE_PROJECT':r['disposable_project'],'DISPOSABLE_VOLUME':r['disposable_volume'],
      'POSTGRES_VERSION':r['server']['version'],'POSTGRES_IMAGE_DIGEST':r['postgres_image_digest'],
      'V001_V042':'UNCHANGED_42_OF_42; FLYWAY_042_PASS','REHEARSAL_V043_DIFF':'ONLY_AUTHORIZED_INTERLOCK_REMOVAL',
      'V043_REHEARSAL_MIGRATION':'PASS_TRANSACTIONAL; FINAL_VERSION=043; FAILED_ROWS=0',
      'NATIVE_RUNTIME_LOAD':'PASS','NATIVE_RUNTIME_CRYPTO':'PASS_51_INSTALLED_PG_VECTORS',
      'INSTALLED_PUBLIC_WRAPPERS':'18/18','INSTALLED_EXECUTOR_SIGNATURES':'6/6',
      'INSTALLED_COLUMN_ACLS':'1040; MISSING=0; EXTRA=0','INSTALLED_FUNCTION_EXECUTE_ACLS':'32; MISSING=0; EXTRA=0; PLUS_2_Q_PREREQUISITES',
      'INSTALLED_SCHEMA_USAGE_ACLS':'8; MISSING=0; EXTRA=0; PLUS_1_Q_PREREQUISITE','DEFAULT_ACL_LEAK':'NO_OPERATIONAL_LEAK_IN_PROBES; INTRINSIC_TYPES_PRESERVED',
      'REAL_ADAPTER_E2E':'NOT_QUALIFIED; REAL_KOTLIN_DENIAL_PROBES_ONLY',
      'DIRECT_LEGACY_SERVICE_CALL_COUNT':'0_IN_EXECUTED_ADAPTER_PROBES',
      'FROZEN_OPERATIONAL_PARITY':'NOT_EXECUTED','S10_S14_REAL_RUNTIME':'NOT_EXECUTED',
      'ORIGINAL_INPUT_RUNTIME_PARITY':'NOT_EXECUTED','S13_COLD_RUNTIME':'NOT_EXECUTED',
      'ALL18_NEGATIVE_MATRIX':'PARTIAL_274_CALLS; POSITIVES_FOREIGN_BINDING_LIFECYCLE_PENDING',
      'REAL_ROLLBACK':'NOT_EXECUTED','CONCURRENCY_SEMANTICS':'NOT_EXECUTED',
      'RESTART_RECOVERY':'PARTIAL_POLICY_KEY_HISTORY_ONLY; GOVERNED_EFFECT_REPLAY_PENDING',
      'BLOCKER_COUNT':'0','HIGH_COUNT':'1','MEDIUM_COUNT':'0','LOW_COUNT':'0',
      'G3F_4_ISOLATED_POSTGRES18_REHEARSAL':'HOLD',
      'PROTECTED_DATABASE_CONNECTION':'NO','PROTECTED_VOLUME_MOUNT':'NO','PRODUCTION_SECRET_USE':'NO',
      'NEXT_GATE':r['next_gate']}
    lines=['# Package 0090 — G3F.4 isolated PostgreSQL 18.4 rehearsal','',
      '**STATUS: HOLD — one HIGH finding required before G3F final.**','',
      'The approved `fixture-1` policy did not qualify the necessary watchdog freshness predicate on this isolated JDBC transport. '
      f'All 40 measured ADMIN-to-AUDITOR heartbeat handoffs exceeded the actual 100 µs and approved maximum 200 µs: minimum {p["minimum_us"]:.0f} µs, maximum {p["maximum_us"]:.0f} µs. '
      'The experiment used warmed, distinct physical JDBC sessions and the actual PostgreSQL timestamp returned by the administrative update. '
      'It does not establish a full wrapper failure or universal impossibility; it establishes that this tested transport has no qualified positive readiness path under the approved fixture.','',
      'The fixture was not widened. Timing readiness remained NOT_READY with explicitly ineligible placeholder manifests. '
      'No operational binding was activated and no production policy was provisioned. The disposable container is stopped; its uniquely created volume is retained. '
      'G3G and G3F_FINAL_REAUTHORIZATION were not entered.','',
      '## Proven installed prerequisites','',
      'The frozen 42 migrations match the accepted Git baseline byte for byte in canonical LF content; working-tree CRLF hashes are recorded separately. '
      'Real Flyway applied V001–V042 and then the transactional temporary V043; history ends at 043 with zero failed rows. '
      'The temporary V043 is reversible to the canonical file by reinserting one exact first-fence byte span. Canonical V043 remains unchanged and fenced.','',
      'The approved native SHA-256 was reproduced and matched the installed library. PostgreSQL itself executed all 51 reviewed Ed25519 vectors with exact accepted/rejected parity. '
      'Installed catalogs confirm 18 wrappers, six executor signatures, exact owners and function metadata, and the 1040/32/8 V043 ACL sets with no missing or extra grants. '
      'Two Q function grants and one Q schema grant are separately governed prerequisites. Nine owner default-ACL probes showed no PUBLIC schema/table/function grants; temporary probe authority and objects were rolled back together. '
      'The explicit enum diagnostic showed owner-only USAGE. Generated row types reported PUBLIC USAGE, and an enum array reported no effective PUBLIC USAGE despite a NULL ACL. '
      'A targeted public-schema probe with all four actual service logins distinguished caller-supplied type construction from operational access: '
      'constructing (1) never revealed stored value 999; table SELECT/UPDATE and creation of dependencies on the explicit enum all denied with 42501. '
      'SPEC 24.2/24.3 preserves intrinsic associated row types and PostgreSQL creation behavior. The type-probe concern is closed with that limited normative interpretation; no operational default-ACL leak was demonstrated.','',
      'Four real dedicated PostgreSQL logins have no memberships, raw-table authority or private/frozen EXECUTE. '
      'The actual Kotlin adapter exercised 17 nonexistent-scope denial paths; S18 remained confined behind the failed S17 sequence. '
      'Direct installed JDBC calls covered all 18 signatures, every input NULL, malformed bytea and all wrong slots. '
      'The combined 274 calls produced only P0017 or 42501. They do not substitute for positive E2E, original-input A/B, foreign-binding or lifecycle coverage. '
      'Restart preserved policy, key commitments and successful migration history, but no durable effect/receipt replay was available to qualify the full recovery gate.','',
      '## Finding and exact technical handoff','',
      '**G3F4-H01 / HIGH / required before G3F final:** qualify a viable rehearsal-only temporal fixture before claiming positive runtime coverage. '
      'This is a fixture/transport qualification gap, not a demonstrated SQL authorization defect. No SQL authority changes are justified by these measurements.','',
      'Next action: prepare a versioned rehearsal-only fixture amendment for technical contract review; use measured transport bounds and a documented safety margin. '
      'Preserve the explicitly approved preflight TTL 1000000 µs / maximum 2000000 µs. '
      'A candidate to experiment with after that review is watchdog interval 10000 µs / maximum 20000 µs and health window 150000 µs / maximum 200000 µs, '
      'under a new fixture version, never as a mutation of fixture-1 or production policy. These proposed numbers are not authority or acceptance evidence. '
      'Then establish positive installed readiness under fresh heartbeats before resuming S01–S18, frozen semantic parity, A/B original-input verification, rollback, barriers/concurrency and durable restart replay. '
      'Only a completed G3F.4 PASS may lead to G3F_FINAL_REAUTHORIZATION.','',
      'Resolved probe concern M01 is retained in the installed ACL evidence, including the raw catalog expansion and actual service results. '
      'No ACL was changed to suppress intrinsic type behavior.','',
      '## Execution exceptions','',
      'An initial new internal-network bootstrap had no published JDBC port. It made no database connection; only its newly labelled container/network/volume were removed after identity checks. '
      'A default-ACL probe initially received 42501 because the owner correctly lacked database CREATE. '
      'The revised probe used one transaction containing temporary database CREATE, owner-created objects, catalog inspection and rollback. '
      'Neither exception was a migration failure, and no migration/history repair was performed.','',
      'A post-restart type-probe invocation failed with the previously assigned disposable port and produced no probe results. '
      'The current port was rediscovered from the uniquely labelled container before the successful repeat. '
      'Tooling now validates Docker project label, pinned image, exclusive new volume, read-only scratch mount and current localhost port before any Java JDBC connection. '
      'A Windows Go-template argument initially caused local endpoint validation rejection; JSON inspection replaced it. '
      'All 274 denial probes passed again with the final endpoint guard; a stale-port negative test was rejected locally before JDBC.','',
      '## Return fields','', '| Field | Result |','|---|---|']
    lines += [f'| {k} | {v} |' for k,v in values.items()]
    lines += ['', 'Checkpoint branch: `checkpoint/package-0090-cloud-handoff`. The evidence commit and fetched remote equality are verified after committing these artifacts; the commit cannot contain its own SHA.','',
      'Evidence: [installed catalog](PACKAGE-0090-G3F-4-INSTALLED-CATALOG.json), [installed ACL](PACKAGE-0090-G3F-4-INSTALLED-ACL.json), '
      '[runtime tests](PACKAGE-0090-G3F-4-RUNTIME-TESTS.json), [concurrency status](PACKAGE-0090-G3F-4-CONCURRENCY.json).','']
    with (target/'PACKAGE-0090-G3F-4-ISOLATED-POSTGRES18-REHEARSAL.md').open('w',encoding='utf-8',newline='\n') as f:f.write('\n'.join(lines))
    print('FIVE_EVIDENCE_ARTIFACTS_WRITTEN_GATE_HOLD')

if __name__=='__main__': publish(sys.argv[1])
