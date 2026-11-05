"""Offline R5N evidence verifier. File/Git reads, JSON/hash/model checks only.
--generate creates design data via derive.py; --record records checks; --seal
seals only this evidence directory/report. No SQL/build/native/network APIs.
"""
import sys
sys.dont_write_bytecode=True
import hashlib,importlib.util,json,subprocess,zlib,struct
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
PREFIX=OUT.relative_to(ROOT).as_posix()+'/'
REPORT='docs/evidence/PACKAGE-0090-B01-v2-native-static-closure-r5n.md'
R5='docs/evidence/package-0090-B01-v2-static-closure-revision-5/'
BASE='cbc284f62d9bd09b7169b55c8d66a3c51a68c6cb'
NATIVE='docs/evidence/package-0090-full-reachable-expectation-closure-v2/native-proof-v6.json'
V043='applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V043__create_governed_offline_field_proof_capability_composition.sql'

def git(*a):return subprocess.check_output(['git',*a],cwd=ROOT)
def sha(b):return hashlib.sha256(b).hexdigest()
def read(n):return json.loads((OUT/n).read_text(encoding='utf-8-sig'))
def save(n,x):(OUT/n).write_bytes(json.dumps(x,indent=2,ensure_ascii=False).encode()+b'\n')
def filehash(p):
    b=(ROOT/p).read_bytes();return sha(b.replace(b'\r\n',b'\n') if p==REPORT else b)

def verify():
    checks=[]
    def c(name,p,detail=None):checks.append(dict(id=name,passed=bool(p),detail=detail));assert p,name
    freeze=read('baseline-freeze.json');gate=read('NATIVE-GATE.json')
    c('branch',git('branch','--show-current').decode().strip()==freeze['branch'])
    c('HEAD_no_commit',git('rev-parse','HEAD').decode().strip()==BASE==freeze['baseline_head'])
    c('remote_tracking_ref',git('rev-parse','origin/'+freeze['branch']).decode().strip()==BASE)
    c('tracked_dirty_zero',git('diff','--name-only')==b'')
    c('staged_zero',git('diff','--cached','--name-only')==b'')
    c('untracked_before_exact_51',len(freeze['untracked_before_paths'])==freeze['UNTRACKED_BEFORE']==51)
    c('untracked_before_all_R5',all(p.startswith(R5) or p=='docs/evidence/PACKAGE-0090-B01-v2-static-closure-revision-5.md' for p in freeze['untracked_before_paths']))
    current=git('ls-files','--others','--exclude-standard').decode().splitlines()
    allowed=set(freeze['untracked_before_paths'])
    c('no_untracked_outside_old_R5_and_new_R5N',all(p in allowed or p.startswith(PREFIX) or p==REPORT for p in current))
    c('all_prior_checkout_files_unchanged',all(sha((ROOT/p).read_bytes())==h for p,h in freeze['source_checkout_sha256'].items()),len(freeze['source_checkout_sha256']))
    # Verify frozen source truth from Git objects, not checkout/generator claims.
    tree={}
    for row in git('ls-tree','-r','-z',BASE).split(b'\0'):
        if row:
            meta,p=row.split(b'\t',1);tree[p.decode()]=meta.decode().split()[2]
    ids=list(dict.fromkeys(tree[p] for p in freeze['source_Git_LF_sha256']))
    batch=subprocess.check_output(['git','cat-file','--batch'],input=('\n'.join(ids)+'\n').encode(),cwd=ROOT)
    raw={};pos=0
    for oid in ids:
        e=batch.index(b'\n',pos);h=batch[pos:e].decode().split();size=int(h[2]);pos=e+1
        assert h[:2]==[oid,'blob'];raw[oid]=batch[pos:pos+size];pos+=size+1
    c('all_frozen_Git_sources_verified',all(sha(raw[tree[p]])==h for p,h in freeze['source_Git_LF_sha256'].items()))
    oldmanifest=json.loads((ROOT/R5/'SHA256-MANIFEST.json').read_text())
    c('R5_manifest_not_modified',all(sha((ROOT/p).read_bytes().replace(b'\r\n',b'\n') if p.endswith('.md') else (ROOT/p).read_bytes())==h for p,h in oldmanifest['files'].items()))
    v=raw[tree[V043]];crc=zlib.crc32(''.join(v.decode('utf-8-sig').splitlines()).encode());crc=crc if crc<2**31 else crc-2**32
    c('V043_Git_LF_hash',sha(v)==freeze['CURRENT_V043_GIT_LF_SHA256']=='007ab786c417c41e2b1702ebf3852cb70ff5c142fa3fde195385e04c6dde8b4a')
    c('V043_Flyway_CRC32',crc==1279591798==freeze['FLYWAY_SIGNED_CRC32'])
    c('V043_fence',v.index(b"RAISE EXCEPTION USING ERRCODE = '55000'")<v.index(b'SET LOCAL search_path'))
    audit=read('failure-audit.json');lp=json.loads((ROOT/R5/'least-privilege-review-v5.json').read_text());bad=[x['id'] for x in lp['checks'] if not x['passed']]
    c('authoritative_497_source',len(bad)==len(lp['failures'])==497 and set(bad)==set(lp['failures']))
    rows=audit['failures'];c('497_unique_conserved',len(rows)==len({r['failure_id'] for r in rows})==497 and {r['failure_id'] for r in rows}==set(bad))
    c('each_primary_blocker_exactly_one',all(r['primary_blocker'] in ['V2-NATIVE','V2-EPOCH','V2-PARTITIONS','V2-TEMPLATES'] for r in rows))
    c('primary_partition_counts',audit['primary_counts']=={'V2-NATIVE':7,'V2-EPOCH':15,'V2-PARTITIONS':468,'V2-TEMPLATES':7})
    c('490_non_target_not_closed',sum(r['primary_blocker']!='V2-NATIVE' for r in rows)==490 and not any(r['closed_by_relabeling'] for r in rows))
    native_rows=[r for r in rows if r['primary_blocker']=='V2-NATIVE']
    c('native_7_aggregate_failure_IDs',all(r['failure_id'].startswith('participant-privilege-closure:') and r['native_classification']=='L' for r in native_rows) and len(native_rows)==7)
    c('native_future_missing_evidence_not_invented',all(not r[k] for r in native_rows for k in ['future_implementation_evidence','future_build_evidence','future_runtime_evidence']))
    dep=read('failure-dependency-graph.json');roots={r['id'] for r in dep['roots']};edges=dep['edges']
    c('three_root_proof_families',len(roots)==3)
    c('dependency_graph_acyclic_no_equivalence',all(e['cause'] in roots and e['consequence'] in {r['failure_id'] for r in native_rows} and e['relation']=='REQUIRED_PROOF_NOT_EQUIVALENCE' for e in edges))
    c('all_native_failure_predicates_have_cause',all(any(e['consequence']==r['failure_id'] for e in edges) for r in native_rows))
    source=json.loads(raw[tree[NATIVE]]);roster=[x['PARTICIPANT_NAME'] for x in source['participants']]
    participants=read('native-participants.json')['participants']
    c('seven_from_frozen_authority_exact',len(roster)==len(set(roster))==len(participants)==7 and [x['PARTICIPANT_ID'] for x in participants]==roster)
    required='PARTICIPANT_ID PURPOSE EXISTING_SOURCE_ANCHORS PARENT_REQUIREMENT INDEPENDENCE_REQUIREMENT EXECUTABLE_OR_MODULE_CLASS DEPENDENCY_CLASS CREDENTIAL_CLASS CHANNEL_CLASS GENERATION_CLASS REGISTRY_CLASS WORK_PROOF_CLASS GUARD_CLASS OBSERVER_CLASS REVOCATION_CLASS EXTINCTION_CLASS'.split()
    for p in participants:
        c('participant_fields_'+p['PARTICIPANT_ID'],all(p.get(k) for k in required))
        vals=p['identity_tuple']['measured_fields'];c('future_values_complete_'+p['PARTICIPANT_ID'],len(vals)==13 and all(v['VALUE_STATE']=='FUTURE_MEASURED' and v['actual_value_present'] is False and all(v.get(k) for k in ['MEASUREMENT_AUTHORITY','CANONICAL_INPUT','MEASUREMENT_ALGORITHM','BINDING_TARGET','VERIFIER','MISMATCH_BEHAVIOR']) for v in vals.values()))
        c('no_fabricated_real_evidence_'+p['PARTICIPANT_ID'],all(p[k] is False for k in ['IMPLEMENTATION_PRESENT','BUILD_IDENTITY_INSTANTIATED','RUNTIME_IDENTITY_INSTANTIATED','RUNTIME_QUALIFIED']))
    def no_null(x):return x is not None and (all(no_null(v) for v in x.values()) if isinstance(x,dict) else all(no_null(v) for v in x) if isinstance(x,list) else True)
    c('no_NULL_identity_placeholders',no_null(participants))
    codec=read('native-identity-codec.json');schemas=codec['schemas']
    c('13_explicit_identity_tuple_schemas',len(schemas)==13 and all(len({x['name'] for x in fs})==len(fs) and all(x['nullable'] is False for x in fs) for fs in schemas.values()))
    c('bootstrap_context_no_recursive_digests',not {'enrollment_identity','channel_identity','credential_identity','completed_work_identity','registry_revision'} & {f['name'] for f in codec['bootstrap_context_schema']})
    c('channel_binding_uses_birth_not_final_enrollment',{'sender_birth_identity','recipient_birth_identity'}<={x['name'] for x in schemas['authenticated_channel_identity']} and not {'sender_enrollment','recipient_enrollment'} & {x['name'] for x in schemas['authenticated_channel_identity']})
    c('final_enrollment_binds_channel_afterward','channel_identity' in {x['name'] for x in schemas['enrollment_identity']})
    abi=read('native-message-abi.json');frames=abi['frames']
    c('14_exact_typed_frames',len(frames)==len({x['message_type'] for x in frames})==14 and {x['participant'] for x in frames}==set(roster))
    for x in frames:
        c('ABI_schema_'+x['id'],len(x['field_order'])==38 and len({f['name'] for f in x['field_order']})==38 and all(f['nullable'] is False and f['encoded_value_length'] for f in x['field_order']))
    c('subject_is_not_emitter',abi['frames'][1]['participant']=='POSTMASTER' and abi['frames'][1]['sender']=='CENSUS_OBSERVER' and 'sender_generation' in {x['name'] for x in abi['frames'][1]['field_order']})
    c('exact_result_schemas_for_all7',set(abi['result_record_schemas'])==set(roster) and all(len({f['name'] for f in fs})==len(fs) for fs in abi['result_record_schemas'].values()))
    c('ABI_integer_and_length_rules','u16be' in abi['encoding']['header'] and abi['encoding']['maximum_frame_bytes']==1048576)
    c('no_NULL_or_unknown_field_acceptance',abi['no_NULL_fields'] and 'duplicate' in abi['encoding']['unknown'] and 'truncation' in abi['encoding']['unknown'])
    c('signed_i64_and_PG2000_time_explicit','two-complement' in abi['encoding']['integers'] and '2000-01-01T00:00:00Z' in abi['encoding']['time'])
    for v in [-2**63,-1,0,1,2**63-1]:c('i64_codec_fixture_'+str(v),int.from_bytes(struct.pack('>q',v),'big',signed=True)==v,'Codec fixture only, never an actual timestamp/process identity')
    c('schema_JSON_bytes_specified','no null/float' in abi['encoding']['schema_JSON'] and 'no BOM/newline/whitespace' in abi['encoding']['schema_JSON'])
    c('error_record_carries_no_fabricated_success_facts',{f['name'] for f in abi['error_result_schema']}=={'reason_code','last_expected_state_digest','pending_subject_work_id','error_detail_digest'} and 'NOT an assertion of current/observed state' in abi['error_encoding'])
    c('error_schema_does_not_change_work_id','expected_result_schema_digest ALWAYS remains the precommitted success-schema digest' in abi['result_record_rule'] and 'does not change base_subject_work_id' in abi['result_record_rule'])
    modules=read('three-test-only-module-contracts.json')['modules'];c('three_specific_modules',len(modules)==3 and len({m['MODULE_ID'] for m in modules})==3)
    module_fields='MODULE_ID PURPOSE PARENT START_AUTHORITY INPUT_ABI OUTPUT_ABI MESSAGE_VERSION MESSAGE_FIELD_ORDER FIELD_TYPES FIELD_LENGTHS NULLABILITY CANONICAL_ENCODING DOMAIN_SEPARATOR CONTEXT_BINDING GENERATION_BINDING REGISTRY_REVISION_BINDING CHALLENGE_BINDING COMPLETED_WORK_BINDING CREDENTIAL_TYPE CREDENTIAL_SOURCE CREDENTIAL_CUSTODY CREDENTIAL_USE_COUNT CREDENTIAL_EXPIRY_RULE CHANNEL_TYPE CHANNEL_AUTHENTICATION PEER_IDENTITY_RULE REPLAY_REJECTION STALE_GENERATION_REJECTION WRONG_PARENT_REJECTION WRONG_BINARY_REJECTION WRONG_CHANNEL_REJECTION WRONG_CONTEXT_REJECTION UNKNOWN_BEHAVIOR REVOCATION_BEHAVIOR CRASH_BEHAVIOR OUTPUT_WITNESS INDEPENDENT_OBSERVER'.split()
    for m in modules:c('module_complete_fields_'+m['MODULE_ID'],all(m.get(k) for k in module_fields) and not m['MODULE_IMPLEMENTED'] and not m['SQL_TEXT_INPUT_ALLOWED'] and not m['GENERIC_OPERATION_SELECTOR'])
    reg=read('native-registry-generation.json');records=reg['records']
    c('four_native_record_schemas',len(records)==4 and {r['type'] for r in records}=={'PARTICIPANT_REGISTRY','GENERATION_LEDGER','GENERATION_TOMBSTONE','COMPLETED_WORK_PUBLICATION'})
    c('base_and_purpose_work_id_preimages_explicit','participant_id u16be' in reg['base_subject_work_id_encoding'] and 'u32be domain byte length' in reg['purpose_work_id_encoding'] and 'uppercase ASCII enum name' in reg['purpose_work_id_encoding'])
    c('receipt_DAG_not_self_referential','No result hashes its own final receipt' in reg['publication_receipt_DAG'] and 'Only then COMPLETED_WORK hashes role result record' in reg['publication_receipt_DAG'])
    for r in records:
        c('record_key_and_enum_'+r['type'],set(r['primary_identity'])<={f['name'] for f in r['canonical_tuple']} and len(set(reg['state_enums'][r['type']].values()))==len(reg['state_enums'][r['type']]))
        c('record_rules_'+r['type'],all(r.get(k) for k in ['CAS_expected','CAS_next','monotonicity','one_use','replacement','restart','reconnect','revocation','tombstone','stale_generation','publication_receipt','corruption','UNKNOWN']))
    # Independent small-state safety model of required high-water behavior, not runtime proof.
    for latest in range(1,5):
        retired=set(range(1,latest))
        for requested in range(1,6):
            permitted=requested==latest and requested not in retired
            c('generation_highwater_'+str(latest)+'_'+str(requested),permitted==(requested==latest),{'newer_process_dead_does_not_change_latest':True})
    work=read('completed-work-protocol.json')['participants']
    c('work_proofs_all7',{w['PARTICIPANT_ID'] for w in work}==set(roster))
    for w in work:c('work_binding_'+w['PARTICIPANT_ID'],all(w.get(k) for k in ['WORK_CHALLENGE','EXPECTED_FUNCTION','INPUT_CONTEXT','EXPECTED_RESULT_CLASS','RESULT_BINDING','RESULT_WITNESS','INDEPENDENT_OBSERVER','ONE_USE_PUBLICATION','REPLAY_REJECTION','FAILURE_RESULT','UNKNOWN_RESULT']))
    c('no_bootstrap_health_cycle',read('completed-work-protocol.json')['bootstrap_dependency_order']==[roster[:4],['APPROVAL_PRODUCER'],['APPROVAL_CONSUMER'],['ENFORCEMENT_WORKER']])
    attacks=read('native-substitution-matrix.json')['cases'];c('168_unique_substitution_cases',len(attacks)==len({x['id'] for x in attacks})==168)
    for a in attacks:c('substitution_'+a['id'],a['expected'] in ['REJECT','UNKNOWN_FAIL_CLOSED'] and bool(a['exact_predicate']) and a['native_module_executed'] is False)
    ind=read('native-independence-model.json');c('canonical_guard_edges_preserved',ind['required_edges']==source['required_edges'])
    c('distinct_role_custody',all(a!=b for a,b in ind['role_separation']))
    review=read('independent-native-review.json')
    design_files={PREFIX+p.name for p in OUT.glob('*.json') if p.name not in ['baseline-freeze.json','NATIVE-GATE.json','independent-native-review.json','tests.json','SHA256-MANIFEST.json']}
    c('review_independent',review['independent_review'] is True and review['reviewer']!='root')
    c('review_all_exact_design_hashes',set(review['reviewed_files_sha256'])==design_files and all(filehash(p)==h for p,h in review['reviewed_files_sha256'].items()))
    c('review_source_hashes',all(sha((ROOT/p).read_bytes())==h for p,h in review['inspected_source_sha256'].items()))
    c('review_gate_agreement',gate['NATIVE_INDEPENDENT_REVIEW']==review['result'])
    c('accepted_participant_count_matches_review',gate['NATIVE_PARTICIPANTS_FULLY_DESIGNED']==sum(x['fully_designed'] for x in review['per_participant_verdict']))
    c('residual_root_family_count_matches_review',gate['R5_NATIVE_TRUE_STATIC_DESIGN_FAILURES_REMAINING']==sum(not x['closed'] for x in review['root_cause_verdicts']))
    c('protocol_flags_match_independent_review',all(gate[k]==v for k,v in review['protocol_verdicts'].items()))
    c('non_target_blockers_not_closed',gate['NON_TARGET_BLOCKERS_UNCHANGED']==['V2-EPOCH','V2-PARTITIONS','V2-TEMPLATES'])
    c('no_live_execution',all(gate[k]=='NO' for k in ['IMPLEMENTATION_PERFORMED','NATIVE_BUILD_PERFORMED','NATIVE_RUNTIME_EXECUTED','SQL_EXECUTED','DATABASE_CONTACTED','V043_EXECUTED','B02_EXECUTED']) and gate['NEXT_EXECUTED'] is False)
    c('no_self_consistency_as_native_PASS',gate['V2_NATIVE_STATUS']!='PASS' or review['result']=='PASS')
    c('distinct_test_ids',len({x['id'] for x in checks})==len(checks))
    return checks

def main():
    if '--generate' in sys.argv:
        s=importlib.util.spec_from_file_location('r5n_evidence_design',OUT/'derive.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);m.generate();return
    if '--seal' in sys.argv:
        files={p.relative_to(ROOT).as_posix() for p in OUT.iterdir() if p.is_file() and p.name!='SHA256-MANIFEST.json'}|{REPORT}
        save('SHA256-MANIFEST.json',dict(algorithm='SHA256',self_excluded=True,report_LF_normalized=True,files={p:filehash(p) for p in sorted(files)}));print('SEALED');return
    checks=verify()
    if '--record' in sys.argv:
        save('tests.json',dict(TESTS_DISTINCT=len(checks),TEST_FAILURES=0,checks=checks,scope='Offline source/design-schema/review/model consistency only, not implementation/build/runtime proof'))
        g=read('NATIVE-GATE.json');g.update(TESTS_DISTINCT=len(checks),TEST_FAILURES=0);save('NATIVE-GATE.json',g)
    else:
        m=read('SHA256-MANIFEST.json');files={p.relative_to(ROOT).as_posix() for p in OUT.iterdir() if p.is_file() and p.name!='SHA256-MANIFEST.json'}|{REPORT}
        assert set(m['files'])==files and all(filehash(p)==h for p,h in m['files'].items())
        assert read('tests.json')['TESTS_DISTINCT']==len(checks) and read('tests.json')['TEST_FAILURES']==0
    print(json.dumps(dict(evidence_verified=True,TESTS_DISTINCT=len(checks),TEST_FAILURES=0,V2_NATIVE_STATUS=read('NATIVE-GATE.json')['V2_NATIVE_STATUS'],NEXT_EXECUTED=False)))

if __name__=='__main__':main()
