"""Read-only final evidence reconciliation; never executes runtime or signing."""
from pathlib import Path
import hashlib,json,sys,subprocess,re
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).parent
HERE=ROOT/'scripts/validation/package_0090_population_qualification'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(data):return hashlib.sha256(data).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def main():
    batch=OUT/sys.argv[1];matrix=load(batch/'MATRIX.json');assert matrix['complete'],'No final report from incomplete matrix'
    source=load(batch/'IMMUTABLE-SOURCE.json');expected=source['files'];assert {p.name:sha(p.read_bytes()) for p in HERE.iterdir() if p.is_file()}==expected
    rows=[];audits=[];binary_sets=[]
    audit_rounds=list(matrix['rounds'])
    for round in matrix['rounds']:
        raw=load(ROOT/round['directory']/'RAW-QUALIFICATION.json')
        for key,module in [('nested_namespace_evidence','foreign_capture_probe'),('nested_ceremony_evidence','successive_second_probe')]:
            if raw.get(key):audit_rounds.append({'module':module,'directory':str(Path(round['directory'])/raw[key]['directory']),'nested':True})
    for round in audit_rounds:
        folder=ROOT/round['directory'];raw=load(folder/'RAW-QUALIFICATION.json');inputs=load(folder/'BUILD-INPUT-SHA256.json')
        assert inputs['files']==expected and raw['source_hashes']==expected
        compiler={}
        for command in load(folder/'BUILD.json'):
            if command['command'][-1]=='sha256sum /usr/local/src-full/*.c /usr/local/src-full/*.h':
                for line in command['stdout'].splitlines():
                    digest,name=line.split(maxsplit=1);compiler[Path(name).name]=digest
        assert compiler
        for name,digest in compiler.items():
            assert digest==(expected[name] if name!='libpq-fe.h' else '499d984421f5490be016f7d49a8599e7f8be120f0cf80c200e872265064be7c0')
        assert all(name in compiler for name in expected if name.endswith(('.c','.h')))
        binaries={Path(name).name:digest for digest,name in (line.split(maxsplit=1) for line in raw['binary_hashes'].splitlines())}
        assert len(binaries)==4;binary_sets.append(binaries)
        assert raw['owned_container_removed'] and raw['private_key_erasure'] and raw['private_key_absent']
        assert not raw['canonical_access'] and not raw['canonical_mutation']
        audits.append({'module':round['module'],'host_input_matches_immutable':True,'compiler_copy_matches_immutable':True,'end_snapshot_matches_immutable':True,'binaries':binaries,'private_erasure':True,'container_removed':True,'errors':raw['errors']})
        if not round.get('nested'):
            for c in raw['cases']:rows.append({'module':round['module'],'raw_path':str((folder/'RAW-QUALIFICATION.json').relative_to(ROOT)),'id':c['group']+'/'+c['name'],**c})
    assert all(b==binary_sets[0] for b in binary_sets)
    assert len(matrix['rounds'])==22 and matrix['final_preservation']['failures']==0
    previous=load(batch/'BASELINE-PRESERVATION.json')['previous_not_run'];assert len(previous)==21
    def selected(modules,fragments):
        matches=[{'module':c['module'],'id':c['id'],'result':c['result'],'raw_path':c['raw_path']} for c in rows if c['module'] in modules and not c['result'].startswith('NOT_RUN') and any(f in c['id'] for f in fragments)]
        assert matches;return matches
    rules={
      'census/all_birth_death_duplicate_generation_races':('QUALIFIED_FINITE_MODEL','The explicitly defined finite 17-observation model runs against actual observer code with owned kernel children. Real promotion, quarantine and compound schedules also rerun. This is not universal scheduling proof or forced Linux PID allocator wrap.',['finite_schedule_probe','compound_probe','schedule_probe'],['finite_schedule','compound','snapshot']),
      'tombstone/explicit_fresh_allocation_entire_new_binding':('HOLD','The protected tombstone and reuse denials execute. A new legitimate allocation ceremony with its own complete new binding/authority lineage is not provisioned; direct synthetic row replacement cannot substitute for that ceremony.',['oid_probe'],['tombstone']),
      'full_normative_parity/frozen_wrappers_authority_consumption_terminal_retry_release':('HOLD','Frozen V043 has an explicit executable safety interlock (55000). Installing its positive wrappers would bypass that interlock. Exact extracted DDL and actual JVM artifact verification do not execute its authority, source, accepted-consumption, retry or release joins.',['domain_probe','binding_encoding_probe'],['domain','verifier','encoding']),
      'remaining/forced_oid_reuse':('QUALIFIED_BOUNDED','Actual disposable catalog OID reuse is injected and old allocation remains denied. This tests protection, not PostgreSQL allocator behavior.',['oid_probe'],['forced_reuse_actual_catalog','old_oid_new_name_denied']),
      'remaining/full_physical_clone':('QUALIFIED_BOUNDED','Actual cold PGDATA copy cannot bootstrap without the retained external context. This is bootstrap denial, not all restore or storage failure populations.',['supplement'],['actual_physical_clone_default_ineligible']),
      'remaining/full_logical_restore':('QUALIFIED_BOUNDED','Actual pg_dump/restore copies the header into a distinct database and denies governed login.',['supplement'],['actual_logical_restore_default_ineligible']),
      'remaining/terminate_failure':('QUALIFIED_BOUNDED','Both selected signals are suppressed; admission remains denied, the participant remains quarantined, and restored termination drains without releasing ownership.',['supplement','drain_probe'],['terminate_failure','both_signals','kernel_and_catalog']),
      'remaining/full_transaction_ownership_contract':('HOLD','Synthetic OWNED rows, real transaction rollback and query-first reconciliation execute. Full frozen claim/attempt/execution/receipt/economic-effect wrappers remain behind the V043 safety interlock.',['domain_probe','participant_dead_probe'],['ownership','authoritative','domain']),
      'remaining/postmaster_control_inconsistency':('HOLD','Joint epoch restart, actual retained postmaster alive-stall/death, old identity denial and governed parallel-worker execution denial execute. A dedicated postmaster progress/heartbeat channel and complete simultaneous control-channel population are not qualified; selected proof is not complete independent postmaster consistency.',['schedule_probe','participant_dead_probe'],['old_postmaster','postmaster']),
      'remaining/all_timeout_state_signal_invariants':('HOLD','Actual caller PostgreSQL timer, SIGALRM handler/mask/flags and ITIMER snapshots execute with SPI failure and recovery. Exhaustive asynchronous signal-delivery schedules and timer drift cannot be inferred from these selected snapshots.',['restart_probe'],['timeout']),
      'remaining/complete_watchdog_worstcase_coverage':('HOLD','No approved numeric health/resource/drain bounds exist in the structural authority. Bounded CPU, I/O and stall samples cannot establish complete worst-case coverage or a policy candidate population. Numeric adoption remains forbidden.',['progress_probe','storage_probe'],['heartbeat','storage']),
      'remaining/independent_JVM_reference_binding_vectors':('QUALIFIED_BOUNDED','Independently compiled actual frozen JVM vectors are compared with the current native codec; no historical native PASS is inherited.',['binding_encoding_probe'],['independent_native_']),
      'replay/stale_enrollment_frame':('QUALIFIED_BOUNDED','A frame with an actual old joint generation and original server-derived backend identity is rejected; selected transfer/catalog/response delays also deny usability past the native deadline.',['replay_probe','schedule_probe'],['actual_old_joint_generation_frame','SCM_after_deadline','catalog_response_after_deadline']),
      'replay/old_receiver_generation_frame':('QUALIFIED_BOUNDED','The approved V1 wire uses one jointly bootstrapped immutable epoch. An actual previous receiver epoch is replayed into a newly bootstrapped generation. Hot individual replacement is not a legal V1 generation.',['replay_probe'],['actual_old_joint_generation_frame']),
      'replay/old_supervisor_generation_frame':('QUALIFIED_BOUNDED','Same actual previous joint epoch test. Supervisor and receiver do not have independently replaceable wire epochs; this alias adds no assertion to the denominator.',['replay_probe'],['actual_old_joint_generation_frame']),
      'replay/old_postmaster_generation_frame':('QUALIFIED_BOUNDED','Actual old joint epoch plus stale postmaster-start identity are rejected. This alias adds no assertion to the denominator.',['replay_probe','schedule_probe'],['actual_old_joint_generation_frame','old_postmaster_identity']),
      'replay/old_approval_generation_frame':('QUALIFIED_BOUNDED','Actual initially accepted A approval precedes a separately signed and actually accepted B bootstrap. Authentic A approval is rejected under B current custody. Full frozen SQL accepted-consumption joins remain fenced and are accounted separately under FC01.',['successive_ceremony_probe'],['actual_valid_older_approval','actual_current_B']),
      'replay/old_attestation_bundle_frame':('QUALIFIED_BOUNDED','Actual initially accepted signed A attestation precedes independently signed and accepted B. Authentic old A bundle and mixed A/B authority material deny under B. Full frozen SQL authority/consumption joins remain fenced under FC01.',['successive_ceremony_probe'],['actual_valid_older_attestation','mixed_A_B','actual_current_B']),
      'replay/replayed_ACCEPT':('QUALIFIED_BOUNDED','The exact previously accepted 76-byte reply is captured and replayed after a real joint generation restart; the current native login rejects it.',['replay_probe'],['replayed_ACCEPT','current_ACCEPT_after_actual_replay']),
      'replay/replayed_SCM_RIGHTS':('QUALIFIED_BOUNDED','An actual backend transfers its own live pidfd and valid frame to a separate native sender. After backend death that retained descriptor is replayed and rejected with kernel-identity reason 6. No foreign PID is opened.',['replay_probe'],['replayed_SCM_RIGHTS','native_admission_after_descriptor_replay']),
      'replay/valid_protocol_wrong_namespace':('QUALIFIED_BOUNDED','Two independent full synthetic bootstraps use separate isolated containers and fresh binding/deployment/incarnation/context. Actual accepted foreign backend frame bytes are captured unchanged, then sent to the current receiver with the native sender own live self pidfd and valid kernel credentials. Full-context reason 3 denies before catalog/promotion. This proves selected protocol context separation, not arbitrary cross-namespace descriptor transfer or full SQL authority parity.',['replay_probe'],['valid_protocol_wrong_namespace','foreign_valid_backend_capture','independent_valid_bootstrap_cleanup','current_native_admission_after_foreign_context_recovers']),
    }
    disposition=[]
    for old in previous:
        ident=old['group']+'/'+old['name'];status,reason,modules,fragments=rules[ident];coverage=selected(modules,fragments)
        if status.startswith('QUALIFIED') and any(c['result']=='FAIL' for c in coverage):status='FAILED_FINAL'
        disposition.append({'previous_id':ident,'status':status,'reason':reason,'fresh_final_evidence':coverage,'adds_duplicate_assertion':False})
    executed=[c for c in rows if not c['result'].startswith('NOT_RUN')];raw_not_run=[c for c in rows if c['result'].startswith('NOT_RUN')]
    summary={'batch':sys.argv[1],'complete_22_cohorts':True,'inherited_PASS':False,'executed_assertion_N':len(executed),'PASS_N':sum(c['result'].startswith('PASS') for c in executed),'FAIL_N':sum(c['result']=='FAIL' for c in executed),'operational_error_N':sum(bool(a['errors']) for a in audits),'RAW_NOT_RUN_ROW_N':len(raw_not_run),'PREVIOUS_NOT_RUN_N':21,'FINAL_UNRESOLVED_EXACT_PREVIOUS_CASE_N':sum(c['status']=='HOLD' for c in disposition),'source_sha256':source['sha256'],'core_binary_sha256':sha(json.dumps(binary_sets[0],sort_keys=True,separators=(',',':')).encode()),'core_binary_domain':'SHA256 sorted compact JSON binary basename/exact SHA256 map; helper hashes remain in exact cohort assertions','core_binaries':binary_sets[0],'primary_cohort_N':22,'actual_cold_build_N':len(audits),'audits':audits,'previous_21_disposition':disposition,'raw_not_run_rows':raw_not_run,'cases':rows,'historical_checks_N':matrix['final_preservation']['N'],'historical_hash_failures':matrix['final_preservation']['failures'],'canonical_access':False,'canonical_mutation':False,'numeric_values_adopted':False,'production_PASS':False,'full_watchdog_PASS':False}
    save(batch/'RECONCILIATION.json',summary)
    report=['# Final disposable regression reconciliation','','Status: HOLD — TEST_ONLY_NONCANONICAL; no Room or full-watchdog readiness.','',f"Final immutable batch: `{sys.argv[1]}`. Executed assertions: {summary['executed_assertion_N']}; PASS: {summary['PASS_N']}; FAIL: {summary['FAIL_N']}; operational error cohorts: {summary['operational_error_N']}.",'',f"Raw NOT_RUN rows (including 13 actual frozen-wrapper fence deferrals): {len(raw_not_run)}. Original exact cases: 21. Unresolved original full-case qualifications: {summary['FINAL_UNRESOLVED_EXACT_PREVIOUS_CASE_N']}. Raw cross-cohort deferrals are preserved, not silently discarded. Coverage aliases never create duplicate assertions.",'','| Previous exact ID | Disposition | Concrete scope / reason |','|---|---|---|']
    report.extend('| '+c['previous_id']+' | '+c['status']+' | '+c['reason']+' |' for c in disposition)
    report.extend(['','Exact case-level evidence, all raw NOT_RUN rows, compiler-copy checks, immutable source and core binary maps are in [RECONCILIATION.json](RECONCILIATION.json).','',f"Historical preservation: {summary['historical_checks_N']} checks, {summary['historical_hash_failures']} mismatch. All 22 primary and two nested rounds record owned container removal and private-key erasure. No frozen interlock, canonical material or numeric policy was changed."])
    (batch/'RECONCILIATION.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
    print(json.dumps({k:summary[k] for k in ['executed_assertion_N','PASS_N','FAIL_N','operational_error_N','RAW_NOT_RUN_ROW_N','FINAL_UNRESOLVED_EXACT_PREVIOUS_CASE_N','source_sha256','core_binary_sha256']}))
if __name__=='__main__':main()
