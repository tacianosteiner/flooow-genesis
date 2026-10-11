"""Read-only final report from exact final regression; no authority or runtime."""
from pathlib import Path
import json,hashlib,sys
OUT=Path(__file__).parent
def main():
    batch=OUT/sys.argv[1];r=json.loads((batch/'RECONCILIATION.json').read_text())
    assert r['complete_22_cohorts'] and not r['FAIL_N'] and not r['operational_error_N'] and not r['historical_hash_failures']
    rows=r['cases']
    def refs(module,parts):
        found=[{'module':x['module'],'id':x['id'],'result':x['result'],'raw_path':x['raw_path']} for x in rows if x['module']==module and any(p in x['id'] for p in parts)]
        assert found and all(x['result'].startswith('PASS') for x in found),(module,parts)
        return found
    specifications=[
      ('receiver stall + backend active','progress_probe',['receiver_active_before_stall','receiver_stall_drains'],'ACTUAL_RUNTIME'),
      ('supervisor stall + receiver alive','progress_probe',['supervisor_active_before_stall','supervisor_stall_drains'],'ACTUAL_RUNTIME'),
      ('observer stall + receiver alive','quarantine_probe',['stalled_alive_participant_detected','stale_observer_denies_admission'],'ACTUAL_RUNTIME'),
      ('postmaster restart + stale receiver generation','schedule_probe',['old_joint_receiver_supervisor_generation','old_postmaster_identity'],'ACTUAL_JOINT_RESTART_AND_STALE_IDENTITY; NOT_HOT_INDIVIDUAL_EPOCH_REPLACEMENT'),
      ('approval revoked + stale heartbeat','extended_fault_probe',['approval_revoked_plus_actual_stale_heartbeat','stale_heartbeat_never_restores'],'ACTUAL_ORIGINAL_EMISSION_SAME_KERNEL_SENDER'),
      ('PID reuse + delayed census','finite_schedule_probe',['finite_schedule'],'CONTROLLED_PID_TUPLE_REUSE_IN_ACTUAL_OBSERVER_MODEL; NOT_FORCED_LINUX_PID_ALLOCATOR_WRAP'),
      ('quarantine + late ACCEPT','extended_fault_probe',['quarantine_between_prepared_ACCEPT_and_send'],'ACTUAL_PRE_SEND_REVALIDATION'),
      ('quarantine + approval restore','extended_fault_probe',['approval_restore_never_clears'],'ACTUAL_RUNTIME'),
      ('backend death + retained pidfd','replay_probe',['replayed_SCM_RIGHTS'],'ACTUAL_RETAINED_KERNEL_DESCRIPTOR'),
      ('receiver loss after confirmed result','quarantine_probe',['receiver_loss_after_confirmed_outcome'],'ACTUAL_RUNTIME'),
      ('census capacity overflow + later empty catalog','binding_encoding_probe',['overflow'],'CONTROLLED_RESULT_POPULATION_IN_ACTUAL_OBSERVER_CODE'),
      ('two simultaneous governed backend failures','compound_probe',['two_simultaneous_governed_writers_ready','receiver_stall_stops_both','two_backend_query_first'],'TWO_ACTUAL_WRITERS_COMMON_RECEIVER_FAILURE')]
    compound=[{'requested':name,'scope':scope,'evidence':refs(module,parts),'adds_assertion_to_denominator':False} for name,module,parts,scope in specifications]
    (batch/'COMPOUND-COVERAGE.json').write_text(json.dumps({'requested_population_N':12,'unmapped_N':0,'universal_proof':False,'full_native_participant_matrix':False,'cases':compound},indent=2)+'\n')
    measurements=[]
    root=OUT.parents[2]
    for audit in r['audits']:
        # Primary cohort paths come from authoritative case records, not aliases.
        paths={x['raw_path'] for x in rows if x['module']==audit['module']}
        for path in sorted(paths):
            raw=json.loads((root/path).read_text())
            observations=[{'start_host_monotonic_ns':x['start_ns'],'end_host_monotonic_ns':x['end_ns'],'elapsed_host_ns':x['end_ns']-x['start_ns'],'eligible':x['eligible'],'reason':x['reason'],'gate_written_container_boottime_us':x['gate_written_boottime_us']} for x in raw['observations']]
            measurements.append({'module':audit['module'],'raw_path':path,'raw_sha256':hashlib.sha256((root/path).read_bytes()).hexdigest(),'experimental_controls':raw['experimental_controls'],'observer_population':observations,'case_timings_preserved_in_raw_details':True,'container_event_times_preserved_in_runtime_log':True})
    (batch/'NUMERIC-MEASUREMENT-POPULATION.json').write_text(json.dumps({'status':'MEASUREMENTS_ONLY_NOT_NUMERIC_AUTHORITY','numeric_candidate_evidence_ready':False,'numeric_values_adopted':False,'clock_domains':'Host monotonic_ns and each independent container BOOTTIME_us remain separate; do not subtract across domains or independent bootstraps','worstcase_coverage':'HOLD_INCOMPLETE_CRITICAL_HEALTH_RESOURCE_DRAIN_POPULATION','source_sha256':r['source_sha256'],'core_binary_sha256':r['core_binary_sha256'],'cohorts':measurements},indent=2)+'\n')
    nr=r['raw_not_run_rows']
    assert all(x.get('reason') or x.get('detail') for x in nr)
    (batch/'NOT-RUN-REGISTER.md').write_text('# Exact final NOT_RUN register\n\nEvery raw row is preserved. Scope-qualified historical aliases are reconciled separately; they add no assertions. Full frozen positive wrappers remain fenced.\n\n| Module | Exact ID | Reason |\n|---|---|---|\n'+'\n'.join('| '+x['module']+' | '+x['id']+' | '+str(x.get('reason') or x.get('detail')).replace('|','/').replace('\n',' ')+' |' for x in nr)+'\n')
    block=[]
    def section(name,**values):
        block.extend(['',name]);block.extend(k+'='+str(v) for k,v in values.items())
    bounded='PASS_BOUNDED_FINAL_DISPOSABLE'
    hold='HOLD_FROZEN_POSITIVE_WRAPPERS_FENCED'
    block.extend(['============================================================','FLOOOW G3F4 FC01 + FC02 CLOSURE','============================================================'])
    section('BASELINE',BRANCH='checkpoint/package-0090-cloud-handoff',INPUT_HEAD='0078290f79c8e6bcdc7b124ca0ae24963a915e2d',FINAL_HEAD='SEE_POST_PUBLICATION_RECEIPT',REMOTE_HEAD='SEE_POST_PUBLICATION_RECEIPT',LOCAL_REMOTE_SYNC='SEE_POST_PUBLICATION_RECEIPT',WORKTREE='SEE_POST_PUBLICATION_RECEIPT')
    section('FC01',FROZEN_SOURCE_EXECUTION='PASS_ACTUAL_UNCHANGED_SOURCE_INTERLOCK_TEST; POSITIVE_EXECUTION_HOLD',FROZEN_WRAPPER_EXECUTION=hold,SQLSTATE_55000_ROOT_CAUSE='UNCONDITIONAL_FIRST_DO_RAISE; EXACT_SOURCE_SECURITY_REVIEW_PASS_BUT_EXECUTABLE_FENCE_RETAINED',FULL_AUTHORITY_JOIN_PARITY=hold,FULL_RUNTIME_CONSUMPTION_PARITY=hold,FULL_OWNERSHIP_PARITY=hold,RETRY_GUARD=hold,OWNERSHIP_RELEASE_SEMANTICS=hold,FULL_DOMAIN_RECONCILIATION=hold)
    section('FC02',PROCESS_POPULATION_CONTRACT='DEFINED_PINNED_FRESH_PRIMARY; FULL_TYPES_CLASSIFIED; GOV_PARALLEL_DENIED',COMPLETE_ENROLLED_BACKEND_COVERAGE='PASS_FINITE_ALLOCATED_CLIENT_CONTRACT; HOLD_FULL_CRITICAL_POPULATION',ALL_INTERLEAVING_RACE_CLOSURE='PASS_FINITE_17_OBSERVATION_MODEL_AND_SELECTED_RUNTIME; NOT_UNIVERSAL',COMPLETE_PARTICIPANT_LIVENESS='HOLD_HOST_CONSUMER_NOT_NATIVE_ANCHORED_AND_ENFORCER_COLOCATED',ACTIVE_ENFORCEMENT_FULL_MATRIX='PASS_SELECTED_AND_COMPOUND; HOLD_FULL_NATIVE_PARTICIPANT_MATRIX',COMPOUND_FAULT_MATRIX='PASS_DEFINED_12_CASE_POPULATION; PID_REUSE_AND_OVERFLOW_MODEL_SCOPE_EXPLICIT')
    section('FC03',ALLOCATION_TOMBSTONE_SEMANTICS='PASS_REUSE_DENIAL; HOLD_FULL_FRESH_ALLOCATION_JOIN_LINEAGE')
    section('FC04_FC05',FULL_CONTEXT_REPLAY_PROTECTION='PASS_ACTUAL_SUCCESSIVE_A_B_NATIVE_BOUNDARY; HOLD_FULL_SQL_CONSUMPTION',OLD_APPROVAL_GENERATION_REPLAY=bounded,OLD_ATTESTATION_BUNDLE_REPLAY=bounded)
    section('FC06',COMPLETE_WATCHDOG_WORSTCASE_COVERAGE='HOLD_FULL_HEALTH_RESOURCE_DRAIN_POPULATION')
    section('FC07',ASYNC_TIMEOUT_SIGNAL_INVARIANTS='PASS_SELECTED_CURRENT_CODE; HOLD_COMPLETE_COMBINED_STATE_RESTORATION')
    section('NUMERIC',NUMERIC_CANDIDATE_EVIDENCE_READY='NO',NUMERIC_VALUES_ADOPTED='NO')
    section('FINAL REGRESSION',FINAL_EXECUTED_ASSERTION_N=r['executed_assertion_N'],FINAL_PASS_N=r['PASS_N'],FINAL_FAIL_N=r['FAIL_N'],FINAL_OPERATIONAL_ERROR_N=r['operational_error_N'],FINAL_NOT_RUN_N=len(nr),UNEXPLAINED_NOT_RUN_N=0,FINAL_SOURCE_SHA256=r['source_sha256'],FINAL_BINARY_SHA256=r['core_binary_sha256'])
    section('FINDINGS',FC01_STATUS='OPEN_BLOCKER',FC02_STATUS='PARTIAL_HIGH',FC03_STATUS='OPEN_HIGH',FC04_STATUS='PARTIAL_MEDIUM',FC05_STATUS='PARTIAL_MEDIUM',FC06_STATUS='PARTIAL_HIGH',FC07_STATUS='PARTIAL_MEDIUM',BLOCKER_COUNT=1,HIGH_COUNT=3,MEDIUM_COUNT=3,LOW_COUNT=0)
    section('H02',H02_NATIVE_ADMISSION=bounded,H02_FULL_BINDING=hold,H02_ATTESTATION='PASS_ORIGINAL_SIGNED_MATERIAL_AND_JVM_PUBLIC_PARITY; HOLD_FULL_DOMAIN',H02_CONTINUOUS_COVERAGE='HOLD_COMPLETE_PARTICIPANT_POPULATION',H02_INDEPENDENT_HEALTH='HOLD_COMPLETE_NATIVE_IDENTITY',H02_ACTIVE_ENFORCEMENT='PASS_SELECTED; HOLD_FULL_MATRIX',H02_DRAIN_RECONCILIATION=hold,H02_COMPLETE_DEPLOYMENT='HOLD')
    section('H03',H03_STRUCTURAL_AUTHORITY='PRESERVED_APPROVED_STRUCTURE_ONLY',H03_CURRENT_APPROVAL_CUSTODY=bounded,H03_RUNTIME_CONSUMPTION=hold,H03_CLONE_RESTORE_PROTECTION=bounded,H03_COMPLETE='HOLD')
    section('H01',H01_STATUS='OPEN')
    section('SAFETY',HISTORICAL_HASHES_INTACT='YES_2096_CHECKS',CANONICAL_V6_ACCESSED='NO',CANONICAL_V6_MUTATED='NO',CANONICAL_DATABASE_MUTATED='NO',CANONICAL_IDS_USED='NO',CANONICAL_KEYS_USED='NO',T0_CONSUMED='NO',CANONICAL_SIGN_EXECUTED='NO',CANONICAL_ADMIN_EXECUTED='NO',TREG_EXECUTED='NO',FINAL_RUNNER_EXECUTED='NO')
    section('CLEANUP',DISPOSABLE_RESOURCES_REMOVED='YES_ALL_24_COLD_BUILDS',TEST_PRIVATE_KEYS_ERASED='YES',PLAINTEXT_TEST_SECRETS_ERASED='YES',QUARANTINE_MONOTONIC='YES',STALE_HEARTBEAT_NEVER_RENEWS='YES',PROVISIONAL_ANCHOR_GRANTS_ELIGIBILITY='NO')
    section('GIT',COMMIT_CREATED='SEE_POST_PUBLICATION_RECEIPT',PUSH_PERFORMED='SEE_POST_PUBLICATION_RECEIPT',LOCAL_REMOTE_SYNC='SEE_POST_PUBLICATION_RECEIPT',WORKTREE_CLEAN='SEE_POST_PUBLICATION_RECEIPT')
    section('GATE',ROOM_ENGINEERING_READY='NO',NEXT_GATE='EXECUTABLE_FROZEN_HANDOFF_WITHOUT_BYPASS_AND_COMPLETE_NATIVE_PARTICIPANT_HEALTH',EXACT_NEXT_AUTHORIZATION_PHRASE='NONE_REQUIRED_FOR_EXISTING_DISPOSABLE_SCOPE; NO_CANONICAL_OR_NUMERIC_AUTHORITY_REQUESTED')
    block.extend(['','============================================================'])
    (OUT/'FINAL-RETURN.txt').write_text('\n'.join(block)+'\n')
    (OUT/'FINAL-GATE.md').write_text('# Final disposable closure: HOLD\n\nThe final source set executes '+str(r['PASS_N'])+' assertions with zero FAIL or operational error. All 22 primary and two nested cold builds use identical source and four core binary hashes. The 34 raw NOT_RUN rows have exact reasons; no historical PASS enters the denominator.\n\nThe census snapshot and stale heartbeat races are closed in the defined finite contract. The unsupported governed parallel-worker defect is reproduced, denied by the final native guard, and followed by supported-client recovery. Twelve compound requirements are mapped explicitly, including controlled model scope rather than inferred Linux PID allocator behavior.\n\nThe frozen source has a matching PASS security review, but its unchanged first statement unconditionally raises SQLSTATE 55000. Positive full wrapper execution remains blocked; no prerequisite fixture can satisfy an unconditional raise. Full participant qualification also remains incomplete because the approval consumer is a host thread and enforcement is co-located. Numeric candidate readiness and Room readiness remain NO. A fully characterized residual HOLD is publishable under the latest mission instructions after scope and cleanup checks.\n\nSee [final reconciliation]('+sys.argv[1]+'/RECONCILIATION.md), [exact deferred cases]('+sys.argv[1]+'/NOT-RUN-REGISTER.md), [compound mapping]('+sys.argv[1]+'/COMPOUND-COVERAGE.json), [finding reassessment](FINDING-REASSESSMENT.md), and [full return block](FINAL-RETURN.txt). Git publication metadata is reported after commit because the immutable evidence cannot contain its own enclosing commit hash.\n')
    print('REPORT=HOLD; UNEXPLAINED_NOT_RUN_N=0; COMPOUND_MAPPING_N=12')
if __name__=='__main__':main()
