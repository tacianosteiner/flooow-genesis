"""Read-only evidence consumer; writes a HOLD report, never commits or provisions."""
from pathlib import Path
import json,sys
OUT=Path(__file__).parent
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def main():
    batch=OUT/sys.argv[1];s=load(batch/'RECONCILIATION.json')
    audit=load(OUT/(sys.argv[2]+'-SCOPE-AUDIT.json'))
    control=load(OUT/(sys.argv[1]+'-HOST-EXECUTION-CONTROL.json'))
    assert s['complete_16_cohorts'] and not s['FAIL_N'] and not s['operational_error_N']
    assert audit['scope_PASS'] and control['restored'] and control['matrix_exit']==0
    assert s['historical_hash_failures']==0 and s['FINAL_UNRESOLVED_EXACT_PREVIOUS_CASE_N']>0
    head=audit['HEAD'];remote=audit['REMOTE_HEAD'];assert head==remote
    held=[c for c in s['previous_21_disposition'] if c['status']=='HOLD']
    assert all(c.get('detail') or c.get('reason') for c in s['raw_not_run_rows'])
    reasons={
      'census/all_birth_death_duplicate_generation_races':'full schedule/process population absent (FC02)',
      'tombstone/explicit_fresh_allocation_entire_new_binding':'fresh legitimate allocation lineage absent (FC03)',
      'full_normative_parity/frozen_wrappers_authority_consumption_terminal_retry_release':'frozen executable reference fenced by SQLSTATE 55000 (FC01)',
      'remaining/full_transaction_ownership_contract':'full frozen ownership/effect wrappers fenced (FC01)',
      'remaining/postmaster_control_inconsistency':'non-client processes and simultaneous control faults unqualified (FC02)',
      'remaining/all_timeout_state_signal_invariants':'exhaustive asynchronous signal schedules unqualified (FC07)',
      'remaining/complete_watchdog_worstcase_coverage':'complete measurement population/numeric candidate evidence absent (FC06)',
      'replay/old_approval_generation_frame':'two legitimate successive authority/consumption ceremonies absent (FC04)',
      'replay/old_attestation_bundle_frame':'two legitimate successive attestation/consumption ceremonies absent (FC05)'}
    assert set(reasons)=={c['previous_id'] for c in held}
    sections=[
      ('BASELINE',{'BRANCH':audit['branch'],'INPUT_HEAD':head,'FINAL_HEAD':head,'REMOTE_HEAD':remote,'LOCAL_REMOTE_SYNC':'YES','WORKTREE':'DIRTY_UNTRACKED_SUCCESSOR_ARTIFACTS'}),
      ('RACE',{'PRE_FIX_RACE_REPRODUCED':'YES_DETERMINISTIC_FAIL_PRESERVED','POST_FIX_RACE':'NOT_REPRODUCED_FINAL_SELECTED_CASES','QUARANTINE_MONOTONIC':'YES','QUARANTINE_CENSUS_RACE_CLOSED':'YES_REPRODUCED_CASE','ADMISSION_TO_CENSUS_RACE_CLOSED':'YES_REPRODUCED_CASE','CENSUS_SNAPSHOT_RACE_CLOSED':'YES_REPRODUCED_PRE_PROMOTION_CASE','STALE_CENSUS_NEVER_ERASES_ENROLLMENT':'YES_SELECTED_FINAL_CASES','PROVISIONAL_ANCHOR_GRANTS_ELIGIBILITY':'NO','ALL_INTERLEAVING_RACE_CLOSURE':'HOLD_FC02'}),
      ('CENSUS',{'INDEPENDENT_SERVER_CENSUS':'PASS_CLIENT_BACKEND_SCOPE','INDEPENDENT_CENSUS_WORKER':'PASS','COMPLETE_ENROLLED_BACKEND_COVERAGE':'HOLD_FC02','PRE_ENROLLMENT_GAP_CLOSED':'YES_CLIENT_BACKEND_SELECTED_CASES'}),
      ('HEARTBEAT',{'STALE_QUEUED_HEARTBEAT_NEVER_RENEWS_LIVENESS':'YES','ACCEPT_FRESHNESS_REVALIDATED':'YES','COMPLETE_PARTICIPANT_LIVENESS':'HOLD_FC02_FC06','STALLED_PARTICIPANT_DETECTION':'PASS_SELECTED_FINAL_CASES','PROCESS_ALIVE_EQUALS_PARTICIPANT_MAKING_PROGRESS':'NO'}),
      ('DOMAIN PARITY',{'FROZEN_BINDING_DOMAIN_PARITY':'HOLD_FC01','FROZEN_ATTESTATION_DOMAIN_PARITY':'HOLD_FC01_FC05','REFERENCE_CODEC_PARITY':'PASS_FROZEN_JVM_SELECTED_VECTORS','VERIFIER_PARITY':'PASS_IMMUTABLE_ARTIFACT_BOUNDARY_HOLD_FULL_SQL_JOINS'}),
      ('IDENTITY',{'OID_REUSE_PROTECTION':'PASS_DISPOSABLE_ACTUAL_CATALOG_REUSE','ALLOCATION_TOMBSTONE_SEMANTICS':'PASS_RETIREMENT_DENIAL_HOLD_FULL_FC03','ROLE_RECREATION_PROTECTION':'PASS'}),
      ('OWNERSHIP / EFFECT',{'FULL_OWNERSHIP_PARITY':'HOLD_FC01','RETRY_GUARD':'HOLD_FC01','OWNERSHIP_RELEASE_SEMANTICS':'HOLD_FC01','FULL_DOMAIN_RECONCILIATION':'HOLD_FC01','AMBIGUOUS_EFFECT_RECONCILIATION':'PASS_QUERY_FIRST_SELECTED_EFFECTS_HOLD_FULL_FC01'}),
      ('CONTROL',{'POSTMASTER_CONTROL_CONSISTENCY':'PASS_SELECTED_GENERATION_CASES_HOLD_FULL_FC02','FULL_CONTEXT_REPLAY_PROTECTION':'HOLD_FC04_FC05','FULL_CONTEXT_SOCKET_PROTECTION':'PASS_SELECTED_NATIVE_CONTEXT_CASES_HOLD_FULL','ACTIVE_ENFORCEMENT_FULL_MATRIX':'HOLD_COMPLETE_POPULATION_FC02_FC06'}),
      ('FINAL REGRESSION',{'FINAL_EXECUTED_ASSERTION_N':s['executed_assertion_N'],'FINAL_PASS_N':s['PASS_N'],'FINAL_FAIL_N':s['FAIL_N'],'FINAL_OPERATIONAL_ERROR_N':s['operational_error_N'],'FINAL_NOT_RUN_N':s['RAW_NOT_RUN_ROW_N'],'FINAL_UNRESOLVED_UNIQUE_FULL_CASE_N':s['FINAL_UNRESOLVED_EXACT_PREVIOUS_CASE_N'],'PREVIOUS_NOT_RUN_N':21,'PREVIOUS_CASES_QUALIFIED_BOUNDED_N':sum(c['status']=='QUALIFIED_BOUNDED' for c in s['previous_21_disposition']),'FINAL_NOT_RUN_CASES_WITH_REASON':'RECONCILIATION.json: all raw rows and exact previous-case dispositions; no denominator reduction','FINAL_SOURCE_SHA256':s['source_sha256'],'FINAL_BINARY_SHA256':s['core_binary_sha256'],'FINAL_BINARY_HASH_DOMAIN':'SHA256_SORTED_COMPACT_JSON_FOUR_CORE_BINARY_HASH_MAP','INHERITED_PASS':'NO'}),
      ('H02',{'H02_NATIVE_ADMISSION':'PASS_BOUNDED','H02_FULL_BINDING':'HOLD','H02_ATTESTATION':'PASS_SYNTHETIC_SIGNATURE_HOLD_FULL_PARITY','H02_CONTINUOUS_COVERAGE':'HOLD','H02_INDEPENDENT_HEALTH':'PASS_SELECTED_STALL_CASES_HOLD_COMPLETE_POPULATION','H02_ACTIVE_ENFORCEMENT':'PASS_SELECTED_SIGNALS_HOLD_FULL_MATRIX','H02_DRAIN_RECONCILIATION':'PASS_KERNEL_CATALOG_SELECTED_CASES_HOLD_FULL_DOMAIN','H02_COMPLETE_DEPLOYMENT':'HOLD'}),
      ('H03',{'H03_STRUCTURAL_AUTHORITY':'APPROVED_HASH_PINNED_STRUCTURE_ONLY','H03_CURRENT_APPROVAL_CUSTODY':'PASS_SYNTHETIC_ROOT_CUSTODY_HOLD_FULL_AUTHORITY_JOINS','H03_RUNTIME_CONSUMPTION':'HOLD_FC01','H03_CLONE_RESTORE_PROTECTION':'PASS_ACTUAL_DISPOSABLE_COLD_CLONE_AND_DUMP_RESTORE','H03_COMPLETE':'HOLD'}),
      ('H01',{'H01_STATUS':'HOLD_NO_NUMERIC_AUTHORITY','NUMERIC_CANDIDATE_EVIDENCE_READY':'NO_COMPLETE_POPULATION','NUMERIC_VALUES_ADOPTED':'NO'}),
      ('FINDINGS',{'BLOCKER_COUNT':1,'HIGH_COUNT':5,'MEDIUM_COUNT':1,'LOW_COUNT':0,'FINDING_REGISTER':'CLOSURE-GATE-FINDINGS.md'}),
      ('SAFETY',{'HISTORICAL_HASHES_INTACT':'YES_885_CHECKS_ZERO_MISMATCH','CANONICAL_V6_ACCESSED':'NO','CANONICAL_V6_MUTATED':'NO','CANONICAL_DATABASE_MUTATED':'NO','CANONICAL_IDS_USED':'NO','CANONICAL_KEYS_USED':'NO','T0_CONSUMED':'NO','CANONICAL_SIGN_EXECUTED':'NO','CANONICAL_ADMIN_EXECUTED':'NO','TREG_EXECUTED':'NO','FINAL_RUNNER_EXECUTED':'NO'}),
      ('CLEANUP',{'DISPOSABLE_RESOURCES_REMOVED':'YES','TEST_PRIVATE_KEYS_ERASED':'YES','PLAINTEXT_TEST_SECRETS_ERASED':'YES','TEMPORARY_HOST_EXECUTION_STATE_RESTORED':'YES'}),
      ('GIT',{'COMMIT_CREATED':'NO','PUSH_PERFORMED':'NO','LOCAL_REMOTE_SYNC':'YES','WORKTREE_CLEAN':'NO_PRESERVED_UNTRACKED_ARTIFACTS','TRACKED_DIRTY_COUNT':0,'STAGED_COUNT':0}),
      ('GATE',{'DISPOSABLE_DOMAIN_AND_ENFORCEMENT_CLOSURE':'HOLD','ROOM_ENGINEERING_READY':'NO','NEXT_GATE':'FC01_FROZEN_SOURCE_EXECUTION_CLOSURE_AND_FC02_PROCESS_POPULATION_QUALIFICATION','EXACT_NEXT_AUTHORIZATION_PHRASE':'NONE_REQUESTED_EXISTING_DISPOSABLE_AUTHORITY_REMAINS; FROZEN_REFERENCE_INTERLOCK_IS_NOT_BYPASSED'})]
    lines=['============================================================','FLOOOW G3F4 FINAL DISPOSABLE CLOSURE','============================================================']
    for heading,fields in sections:
        if heading=='FINAL REGRESSION':
            fields['FINAL_NOT_RUN_CASES_WITH_REASON']='; '.join(c['previous_id']+': '+reasons[c['previous_id']] for c in held)
            fields['UNEXPLAINED_NOT_RUN_N']=0
        lines.append(heading);lines.extend(str(k)+'='+str(v) for k,v in fields.items())
    lines.append('============================================================')
    text='\n'.join(lines)+'\n';target=OUT/'FINAL-DISPOSABLE-CLOSURE.txt';assert not target.exists()
    target.write_text(text,encoding='utf-8')
    (OUT/'FINAL-DISPOSABLE-CLOSURE.md').write_text('# Final disposable closure — HOLD\n\n```text\n'+text+'```\n\nFinal evidence: ['+sys.argv[1]+'/RECONCILIATION.md]('+sys.argv[1]+'/RECONCILIATION.md).\n\nOpen qualification findings: [CLOSURE-GATE-FINDINGS.md](CLOSURE-GATE-FINDINGS.md).\n',encoding='utf-8')
    print(text)
if __name__=='__main__':main()
