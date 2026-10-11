"""Emit honest final HOLD block; publication is forbidden while findings remain."""
from pathlib import Path
import json,subprocess,hashlib
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'docs/evidence/package-0090-g3f4-census-heartbeat-domain-parity'
reg=json.loads((OUT/'POST-ATTEMPT10-FULL-REGRESSION.json').read_text())
safety=json.loads((OUT/'CANONICAL-NON-MUTATION-PROOF.json').read_text())
scope=json.loads((OUT/'FINAL-SCOPE-AUDIT.json').read_text())
all_final=all(r['final_runtime_bytes_equal'] and r['extra_compiled_components_equal'] for r in reg['rounds'])
selected=reg['FAIL']==0 and not any(r['errors'] for r in reg['rounds']) and all_final
pass_selected='PASS_SELECTED_FINAL_DISPOSABLE' if selected else 'HOLD_FINAL_EXECUTED_REGRESSION'
def bounded(*modules):
    rows=[r for r in reg['rounds'] if r['module'] in modules]
    return 'PASS_SELECTED_FINAL_DISPOSABLE' if len(rows)==len(modules) and all(r['exit']==0 and not r['errors'] and not r['FAIL'] and r['final_runtime_bytes_equal'] and r['extra_compiled_components_equal'] for r in rows) else 'HOLD_FINAL_EXECUTED_REGRESSION'
codec=bounded('binding_encoding_probe');heartbeat=bounded('binding_encoding_probe','progress_probe');census=bounded('census_probe');identity=bounded('oid_probe');control=bounded('restart_probe');custody=bounded('scenarios');clones=bounded('supplement');domain=bounded('domain_probe','participant_dead_probe')
head=scope['HEAD'];remote=scope['REMOTE_HEAD'];sync='YES' if head==remote else 'NO'
lines=[]
def section(name):lines.extend(['',name])
def values(**kwargs):lines.extend(k+'='+str(v) for k,v in kwargs.items())
lines.extend(['============================================================','FLOOOW G3F4 CENSUS + HEARTBEAT + DOMAIN PARITY','============================================================'])
section('BASELINE');values(BRANCH=scope['branch'],INPUT_HEAD='0078290f79c8e6bcdc7b124ca0ae24963a915e2d',FINAL_HEAD=head,REMOTE_HEAD=remote,LOCAL_REMOTE_SYNC=sync,WORKTREE='UNTRACKED_SUCCESSOR_ARTIFACTS')
section('DOMAIN PARITY');values(FROZEN_BINDING_DOMAIN_PARITY='PASS_SELECTED_BYTE_VECTORS; HOLD_FULL_SEMANTICS',FROZEN_ATTESTATION_DOMAIN_PARITY='PASS_PUBLIC_PRIMITIVES; HOLD_FULL_DOMAIN',REFERENCE_CODEC_PARITY=codec,VERIFIER_PARITY='HOLD_FROZEN_SEMANTIC_PARITY',POST_ATTEMPT10_FULL_REGRESSION='HOLD_REQUIRED_CASES_NOT_RUN',FINAL_EXECUTED_CASE_N=reg['N_EXECUTED_ASSERTIONS'],FINAL_EXECUTED_CASE_FAIL=reg['FAIL'],FINAL_NOT_RUN_CASE_N=reg['NOT_RUN'],FINAL_ROUND_ERRORS=sum(bool(r['errors']) for r in reg['rounds']),RETAINED_FINAL_BYTE_OPEN_RACE_COUNT=len(reg['retained_final_byte_open_races']),FINAL_RUNTIME_SOURCE_EQUAL='YES' if all_final else 'NO')
section('CENSUS');values(INDEPENDENT_SERVER_CENSUS=census+'; HOLD_SEPARATE_WORKER',COMPLETE_ENROLLED_BACKEND_COVERAGE='HOLD',PRE_ENROLLMENT_GAP_CLOSED=census+'; HOLD_EXHAUSTIVE_SCHEDULES',ADMISSION_TO_CENSUS_RACE_CLOSED='HOLD_KNOWN_QUARANTINE_PENDING_ADMISSION_RACE')
section('HEARTBEAT');values(COMPLETE_PARTICIPANT_LIVENESS='HOLD_COMPLETE_PARTICIPANT_MATRIX',INDEPENDENT_HEALTH_SOURCE=custody+'; HOLD_COMPLETE_INDEPENDENCE',STALLED_PARTICIPANT_DETECTION=heartbeat,STALE_QUEUED_HEARTBEAT_NEVER_RENEWS_LIVENESS=heartbeat,ACCEPT_FRESHNESS_REVALIDATED='YES_AFTER_WRITABILITY_WAIT',PROCESS_ALIVE_IS_NOT_PARTICIPANT_MAKING_PROGRESS='YES',CONTROL_HUP_RETAINED_POSTMASTER_DRAIN=control,CONTINUOUS_COVERAGE='HOLD',CONTINUOUS_ENFORCEMENT='HOLD')
section('IDENTITY');values(OID_REUSE_PROTECTION=identity+'; OLD_BINDING_TOMBSTONE_SCOPE',ALLOCATION_TOMBSTONE_SEMANTICS='HOLD_FRESH_ALLOCATION_LINEAGE',ROLE_RECREATION_PROTECTION=identity)
section('OWNERSHIP / EFFECT');values(FULL_OWNERSHIP_PARITY='HOLD_FROZEN_WRAPPERS',RETRY_GUARD='HOLD_FROZEN_WRAPPERS',OWNERSHIP_RELEASE_SEMANTICS='HOLD_FULL_CONTRACT; SELECTED_OWNED_RETENTION',FULL_DOMAIN_RECONCILIATION='HOLD_COMPLETE_COMMIT_AMBIGUITY_MATRIX',AMBIGUOUS_EFFECT_RECONCILIATION=domain+'; HOLD_FULL_DOMAIN_MATRIX')
section('CONTROL / REPLAY');values(POSTMASTER_CONTROL_CONSISTENCY=control+'; HOLD_FULL_GENERATION_MATRIX',FULL_CONTEXT_REPLAY_PROTECTION='HOLD_COMPLETE_REPLAY_MATRIX',FULL_CONTEXT_SOCKET_PROTECTION=bounded('socket_probe')+'; HOLD_FULL_NAMESPACE_MATRIX',ACTIVE_ENFORCEMENT_FULL_MATRIX='HOLD_COMPLETE_PARTICIPANT_AND_COMPOUND_FAULTS')
section('NUMERIC');values(NUMERIC_CANDIDATE_EVIDENCE_READY='NO',NUMERIC_DECISION_PACKAGE_CREATED='YES',NUMERIC_DECISION_STATUS='PROPOSAL_ONLY_NOT_AUTHORIZED',NUMERIC_VALUES_ADOPTED='NO')
section('H02');values(H02_NATIVE_ADMISSION=codec,H02_FULL_BINDING='HOLD_FULL_SEMANTIC_PARITY',H02_ATTESTATION='HOLD_FULL_VERIFIER_PARITY',H02_CONTINUOUS_COVERAGE='HOLD',H02_INDEPENDENT_HEALTH='HOLD',H02_ACTIVE_ENFORCEMENT='HOLD_COMPLETE_MATRIX',H02_DRAIN_RECONCILIATION='HOLD_FULL_DOMAIN',H02_COMPLETE_DEPLOYMENT='HOLD')
section('H03');values(H03_STRUCTURAL_AUTHORITY='PASS',H03_CURRENT_APPROVAL_CUSTODY=custody,H03_RUNTIME_CONSUMPTION='HOLD_FULL_FROZEN_CONSUMPTION_PARITY',H03_CLONE_RESTORE_PROTECTION=clones,H03_COMPLETE='HOLD')
section('H01');values(H01_STATUS='OPEN')
section('FINDINGS');values(FINDINGS_SCOPE='DISPOSABLE_SUCCESSOR_REVIEW',BLOCKER_COUNT=0,HIGH_COUNT=4,MEDIUM_COUNT=2,LOW_COUNT=0,ROOM_FROZEN_FINDINGS_UNCHANGED='B0/H3/M0/L0')
section('CANONICAL SAFETY');values(HISTORICAL_HASHES_INTACT='YES' if safety['HISTORICAL_HASHES_INTACT'] else 'NO',CANONICAL_V6_ACCESSED='NO',CANONICAL_V6_MUTATED='NO',CANONICAL_DATABASE_MUTATED='NO',CANONICAL_IDS_USED='NO',CANONICAL_KEYS_USED='NO',T0_CONSUMED='NO',CANONICAL_SIGN_EXECUTED='NO',CANONICAL_ADMIN_EXECUTED='NO',TREG_EXECUTED='NO',FINAL_RUNNER_EXECUTED='NO')
section('CLEANUP');values(DISPOSABLE_RESOURCES_REMOVED='YES' if safety['DISPOSABLE_RESOURCES_REMOVED'] else 'NO',TEST_PRIVATE_KEYS_ERASED='YES' if safety['TEST_PRIVATE_KEYS_ERASED'] else 'NO',PLAINTEXT_TEST_SECRETS_ERASED='YES' if safety['DISPOSABLE_RESOURCES_REMOVED'] and not scope['private_key_artifact_files'] else 'NO')
section('GIT');values(COMMIT_CREATED='NO',PUSH_PERFORMED='NO',LOCAL_REMOTE_SYNC=sync,WORKTREE_CLEAN='NO')
section('GATE');values(DISPOSABLE_DOMAIN_AND_ENFORCEMENT_CLOSURE='HOLD',ROOM_ENGINEERING_READY='NO',NEXT_GATE='DISPOSABLE_INDEPENDENT_CENSUS_ENFORCER_AND_FULL_FROZEN_DOMAIN_REPLAY_CONTROL_COMMIT_MATRIX',EXACT_NEXT_AUTHORIZATION_PHRASE='NONE_REQUIRED_FOR_CONTINUATION_WITHIN_EXISTING_DISPOSABLE_AUTHORITY')
lines.extend(['','============================================================'])
block='\n'.join(lines)+'\n';(OUT/'FINAL-RETURN.txt').write_text(block,encoding='utf-8')
summary=f"# Final gate — HOLD\n\nNo commit or push. Input/local/origin remain `{head}`. Selected final executed assertions: N={reg['N_EXECUTED_ASSERTIONS']}, FAIL={reg['FAIL']}; additional NOT_RUN rows={reg['NOT_RUN']}; total matrix rows={reg['N']}; round errors={sum(bool(r['errors']) for r in reg['rounds'])}; exact final compiler-copy/runtime source equality={all_final}. No historical runtime PASS is inherited.\n\nThe heartbeat queue and control-HUP corrections are measured on final hashes. The final drain witness remains FAIL: pending pre-enrollment census during live quarantine triggers coarse generation shutdown and makes the old catalog unavailable. Its original error and completed failed retry are retained; disconnect never proves effect zero. Full frozen semantic/ownership parity, independent complete census/enforcer health, replay/control/COMMIT schedules, fresh allocation lineage and numeric qualification remain HOLD. See REQUIRED-COVERAGE-REVIEW.md and all raw rounds. Room's frozen B0/H3/M0/L0 remains unchanged.\n\nHistorical hashes are preserved; canonical resources and numeric policy authority are untouched. Cleanup and scope review are recorded in CANONICAL-NON-MUTATION-PROOF.json and FINAL-SCOPE-AUDIT.json. Working tree intentionally retains uncommitted successor evidence.\n\n```text\n"+block+'```\n'
(OUT/'FINAL-GATE.md').write_text(summary,encoding='utf-8')
print('FINAL_GATE=HOLD','FINAL_SELECTED_PASS=',selected,'COMMIT=NO PUSH=NO')
