"""R5 offline verifier/entry point. No database, Docker, build or native calls.

--generate invokes only the adjacent evidence generator; --record writes test
evidence; --seal writes manifest; default verifies frozen inputs/contracts,
independent reviews, report and manifest. No changes outside R5 evidence/report.
"""
import sys
sys.dont_write_bytecode=True
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import subprocess
import zlib

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
PREFIX=OUT.relative_to(ROOT).as_posix()+'/'
BASE='cbc284f62d9bd09b7169b55c8d66a3c51a68c6cb'
REPORT='docs/evidence/PACKAGE-0090-B01-v2-static-closure-revision-5.md'
R4='docs/evidence/package-0090-B01-v2-static-closure-revision-4/'
R3='docs/evidence/package-0090-B01-v2-static-closure-revision-3/'
V043='applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V043__create_governed_offline_field_proof_capability_composition.sql'

def sha(b):return hashlib.sha256(b).hexdigest()
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def read(n):return json.loads((OUT/n).read_text(encoding='utf-8-sig'))
def save(n,x):(OUT/n).write_bytes(json.dumps(x,indent=2,ensure_ascii=False).encode()+b'\n')
def git(*a):return subprocess.check_output(['git',*a],cwd=ROOT)
def filehash(p):
    b=(ROOT/p).read_bytes();return sha(b.replace(b'\r\n',b'\n') if p==REPORT else b)
def module(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def verify():
    checks=[]
    def check(name,truth,details=None):
        checks.append(dict(id=name,passed=bool(truth),details=details));assert truth,name
    f=read('baseline-freeze.json');g=read('STATIC-GATE.json')
    check('branch_exact',git('branch','--show-current').decode().strip()==f['branch']=='checkpoint/package-0090-cloud-handoff')
    check('HEAD_unchanged_no_commit',git('rev-parse','HEAD').decode().strip()==BASE==f['baseline_head'])
    check('remote_tracking_ref_unchanged',git('rev-parse','origin/'+f['branch']).decode().strip()==BASE)
    check('no_staged_changes',git('diff','--cached','--name-only')==b'')
    check('no_tracked_changes',git('diff','--name-only')==b'')
    status=git('status','--porcelain=v1','--untracked-files=all').decode().splitlines()
    check('untracked_scope_only',all(x.startswith('?? ') and (x[3:].startswith(PREFIX) or x[3:]==REPORT) for x in status))
    check('preflight_counts_exact',f['tracked_dirty_before']==f['staged_before']==f['untracked_before']==0)
    # Hash from Git objects, then independently compare checkout LF bytes.
    paths=f['input_blob_oid'];ids=list(dict.fromkeys(paths.values()))
    buf=subprocess.check_output(['git','cat-file','--batch'],input=('\n'.join(ids)+'\n').encode(),cwd=ROOT)
    raw={};pos=0
    for oid in ids:
        end=buf.index(b'\n',pos);h=buf[pos:end].decode().split();n=int(h[2]);pos=end+1
        assert h[:2]==[oid,'blob'];raw[oid]=buf[pos:pos+n];pos+=n+1
    blobs={p:raw[o] for p,o in paths.items()}
    check('frozen_git_SHA256_all',all(sha(blobs[p])==h for p,h in f['input_git_sha256'].items()),len(blobs))
    check('frozen_checkout_bytes_all',all((ROOT/p).read_bytes().replace(b'\r\n',b'\n')==b.replace(b'\r\n',b'\n') for p,b in blobs.items()))
    check('complete_R4_frozen_input_set',all(p in blobs for p in json.loads(blobs[R4+'baseline-freeze.json'])['input_git_sha256']))
    r4m=json.loads(blobs[R4+'SHA256-MANIFEST.json'])
    check('complete_R4_manifest_inventory',all(p in blobs for p in r4m['files']))
    check('complete_R4_manifest_hashes',all(sha(blobs[p].replace(b'\r\n',b'\n') if p.endswith('.md') else blobs[p])==h for p,h in r4m['files'].items()))
    check('frozen_all_ADR_SPEC_sources',all(p in blobs for p in git('ls-tree','-r','--name-only',BASE).decode().splitlines() if p.startswith(('docs/adr/','docs/specifications/'))))
    for ref,h in f['protected_refs'].items():check('protected_ref_'+ref,git('rev-parse',ref).decode().strip()==h)
    v=blobs[V043]
    check('canonical_V043_hash',sha(v)==f['CURRENT_V043_GIT_LF_SHA256']=='007ab786c417c41e2b1702ebf3852cb70ff5c142fa3fde195385e04c6dde8b4a')
    crc=zlib.crc32(''.join(v.decode('utf-8-sig').splitlines()).encode());crc=crc if crc<2**31 else crc-2**32
    check('canonical_Flyway_CRC32',crc==1279591798==f['FLYWAY_SIGNED_CRC32'])
    check('executable_fence_precedes_work',v.index(b"RAISE EXCEPTION USING ERRCODE = '55000'")<v.index(b'SET LOCAL search_path'))
    contracts={p.name:json.loads(p.read_text()) for p in OUT.glob('*-v5.json') if p.name not in ['least-privilege-review-v5.json','static-adversarial-review-v5.json']}
    check('all_contract_envelopes',all(x['revision']==5 and x['scope']=='TEST_ONLY_STATIC_DESIGN' and not x['implementation_authorized'] and not x['physical_instantiation_performed'] and not x['runtime_proven'] for x in contracts.values()))
    required_names='native-seven-participant-contract native-work-anchor-map native-generation-contract native-independent-witness-topology native-extinction-contract native-message-abi native-registry-protocol native-loader-dependency-contract native-confinement-contract endpoint-inventory endpoint-custody closed-epoch-state-machine closed-epoch-physical-bindings closed-epoch-crash-matrix closed-epoch-reseal-invariants durable-reservation-contract durable-outcome-contract durable-audit-contract durable-ledger-protocol extinction-proof-contract consumer-session-contract revocation-graph unknown-outcome-contract qualification-universe mechanism-denominator class-mechanism-partitions constraint-applicability dependency-effect-ledger acl-origin-ledger authority-graph physical-target-bindings typed-capability-catalog fixed-operation-templates capability-principal-bindings capability-outcome-bindings capability-observer-bindings executor-confinement fixture-correction-revalidation'.split()
    check('all_required_contract_artifacts',set(contracts)=={n+'-v5.json' for n in required_names},len(contracts))
    native=contracts['native-seven-participant-contract-v5.json']['participants'];abi=contracts['native-message-abi-v5.json'];frames=abi['frames']
    required_participants={'POSTMASTER','SUPERVISOR','RECEIVER','CENSUS_OBSERVER','APPROVAL_PRODUCER','APPROVAL_CONSUMER','ENFORCEMENT_WORKER'}
    check('seven_participants_exact',len(native)==7 and {n['participant'] for n in native}==required_participants)
    for n in native:
        check('matrix_37_unique_'+n['participant'],len(n['closure_matrix'])==37 and len({r['REQUIREMENT'] for r in n['closure_matrix']})==37)
        check('matrix_fields_'+n['participant'],all(all(k in r for k in ['REQUIREMENT','SOURCE_EVIDENCE','DESIGN_BINDING','INDEPENDENT_OBSERVER','FAIL_CLOSED_BEHAVIOR','STATIC_STATUS']) for r in n['closure_matrix']))
        check('future_binary_not_fabricated_'+n['participant'],n['actual_binary_hash'] is None and n['actual_process_handle'] is None and n['PHYSICAL_INSTANTIATION_REQUIRED_LATER'])
        for a in n['closure_matrix'][1]['DESIGN_BINDING']:
            check('native_source_'+n['participant']+'_'+str(a['line']),sha(blobs[a['path']])==a['git_lf_sha256'])
    check('14_typed_ABI_frames',len(frames)==14 and len({r['message_type'] for r in frames})==14)
    check('ABI_distinct_sender_recipient',all(r['sender']!=r['recipient'] for r in frames))
    check('ABI_nullable_pair_closed',all({f['name'] for f in r['fields'] if f['nullable']}=={'backend_pid','backend_start_epoch_us'} for r in frames))
    check('ABI_field_names_unique',all(len({f['name'] for f in r['fields']})==len(r['fields']) for r in frames))
    check('ABI_no_caller_operation_target_selector',abi['no_caller_selected_operation_or_target'])
    check('inherited_peer_not_current_sender',all('creation-time peer' in n['closure_matrix'][13]['DESIGN_BINDING']['bootstrap_peer'] and 'SCM_PIDFD' in n['closure_matrix'][13]['DESIGN_BINDING']['current_sender'] for n in native))
    check('binary_instantiation_separate_from_recipe',contracts['native-loader-dependency-contract-v5.json']['contract']['DESIGN_BINDING_COMPLETE'] and contracts['native-loader-dependency-contract-v5.json']['contract']['actual_binary_sha256'] is None)
    stores=contracts['durable-ledger-protocol-v5.json']['stores']
    check('seven_separate_store_schemas',len(stores)==7 and len({s['store_id'] for s in stores})==len({s['writer'] for s in stores})==7)
    check('store_observer_is_not_writer',all(s['writer']!=s['observer'] and s['writer_credential']!=s['observer_credential'] for s in stores))
    check('store_fields_have_exact_types_nullability',all(len({f['name'] for f in s['field_order']})==len(s['field_order']) and all(set(f)=={'name','type','nullable'} for f in s['field_order']) for s in stores))
    check('store_entity_key_fields_exist',all(set(s['logical_entity_key'])<={f['name'] for f in s['field_order']} for s in stores))
    check('store_entity_CAS_not_only_operation_ID',all({'entity_key_digest','entity_revision','prior_entity_record'}<={f['name'] for f in s['field_order']} and 'expected entity revision' in s['CAS_predicate'] and 'never resets existing entity' in s['CAS_predicate'] for s in stores))
    check('registry_entity_key_excludes_operation_ID',next(s['logical_entity_key'] for s in stores if s['store']=='participant_registry')==['qualification_id','epoch','participant_slot','participant_generation'])
    check('ledger_genesis_has_no_unknown_absence_fallback','Unknown/missing/corrupt chain never authorizes genesis' in contracts['durable-ledger-protocol-v5.json']['genesis'])
    check('stores_have_CAS_atomicity_durability_replay_UNKNOWN',all(all(s.get(k) for k in ['identity_key','generation_key','CAS_predicate','atomicity','durability','replay','corruption','UNKNOWN']) for s in stores))
    endpoints=contracts['endpoint-inventory-v5.json']['endpoints']
    check('endpoint_IDs_unique',len({e['ENDPOINT_ID'] for e in endpoints})==len(endpoints))
    fields=['ENDPOINT_ID','TYPE','CREATOR','OWNER','HOLDER','REQUESTER','TRANSFER_PATH','AUTHORITY','CREDENTIAL','GENERATION','REVOCATION_TRIGGER','REVOCATION_ACTOR','EXTINCTION_OBSERVER','DURABLE_RECEIPT','UNKNOWN_RULE']
    check('endpoint_all_requested_fields',all(all(e.get(k) for k in fields) for e in endpoints))
    check('endpoint_custody_inventory_exact',endpoints==contracts['endpoint-custody-v5.json']['endpoints'])
    check('endpoint_physical_total_not_type_count',g['ENDPOINTS_TOTAL'] is None and contracts['endpoint-inventory-v5.json']['ENDPOINTS_TOTAL'] is None)
    actor_ids={a['id'] for a in contracts['qualification-universe-v5.json']['identities']}
    check('endpoint_actors_explicit',all(e[k] in actor_ids for e in endpoints for k in ['CREATOR','OWNER','HOLDER','REQUESTER','REVOCATION_ACTOR','EXTINCTION_OBSERVER']))
    check('revocation_edges_one_per_known_class',{e['endpoint'] for e in contracts['revocation-graph-v5.json']['edges']}=={e['ENDPOINT_ID'] for e in endpoints})
    state=contracts['closed-epoch-state-machine-v5.json'];old=json.loads(blobs[R4+'closed-epoch-state-machine-v4.json'])
    check('14_state_relation_preserved_exactly',state['states']==old['states'] and state['transitions']==old['transitions'] and len(state['states'])==14)
    check('frozen_state_machine_preserved_byte_for_byte',(OUT/'frozen-state-machine-v4.json').read_bytes()==blobs[R4+'closed-epoch-state-machine-v4.json'])
    check('preserved_relation_canonical_SHA256',sha(canon(dict(states=state['states'],transitions=state['transitions'])))==state['preserved_relation_sha256'])
    inv=contracts['closed-epoch-reseal-invariants-v5.json']['invariants'];ids={x['id'] for x in inv}
    check('seven_invariants_exact',len(ids)==len(inv)==7 and all(set(t['required_known_true'])==ids for t in state['transitions'] if t['to']=='SEALED_NEW_EPOCH'))
    check('UNKNOWN_2187_truth_valuations',[v for v in itertools.product((True,False,None),repeat=7) if all(x is True for x in v)]==[(True,)*7])
    check('no_physical_reseal_proof_from_schema',g['RESEAL_INVARIANTS_PHYSICALLY_BOUND']==0 and not any(x['STATIC_DESIGN_BOUND'] for x in inv))
    u=contracts['unknown-outcome-contract-v5.json'];consumer=contracts['consumer-session-contract-v5.json']
    check('UNKNOWN_restart_reconnect_persistent',u['survives_restart'] and u['survives_reconnect'] and not u['new_enrollment_while_UNKNOWN'])
    check('no_helper_session',consumer['helper_session_allowed'] is False and consumer['physical_values_not_the_reason_for_BLOCKED'])
    rows=contracts['physical-target-bindings-v5.json']['obligations'];r4rows=json.loads(blobs[R4+'class-mechanism-partitions-v4.json'])['individual_missing_target_obligations'];byid={r['id']:r for r in r4rows}
    check('all_422_unique_ids',len(rows)==len({r['OBLIGATION_ID'] for r in rows})==422 and {r['OBLIGATION_ID'] for r in rows}==set(byid))
    required='OBLIGATION_ID SOURCE_NODE OPERATION_FORM APPLICABILITY PHYSICAL_TARGET TARGET_IDENTITY_RULE ACTOR ACTOR_AUTHORITY CREDENTIAL DEPENDENCY_EFFECTS OBSERVER OUTCOME_BINDING REVOCATION_BINDING UNKNOWN_BEHAVIOR SOURCE_PROOF STATIC_STATUS'.split()
    check('422_all_required_fields',all(all(k in r for k in required) for r in rows))
    check('422_source_form_exact',all(r['SOURCE_PROOF']==byid[r['OBLIGATION_ID']]['source_authority'] and r['OPERATION_FORM']==byid[r['OBLIGATION_ID']]['operation_form'] and r['SOURCE_NODE']==byid[r['OBLIGATION_ID']]['dependency_effect']['source_node'] for r in rows))
    check('422_not_resolved_by_type_label',all(r['PHYSICAL_TARGET'] is None and r['STATIC_STATUS']=='NOT_PROVEN' and not r['representative_collapse'] for r in rows))
    classes=contracts['class-mechanism-partitions-v5.json']
    check('46_classes_exact',len(classes['classes'])==46 and classes['classes']==json.loads(blobs[R4+'class-mechanism-partitions-v4.json'])['classes'])
    check('class_obligation_partition_no_missing_or_collapse',sorted(x for ids in classes['per_class_obligation_ids'].values() for x in ids)==sorted(byid))
    # Independent frozen source-form expansion, not R5 generator counters.
    d=module(ROOT/R3/'derive.py','r3_expansion_readonly');count=0;missing=set();digest=hashlib.sha256()
    for r in d.expand_mechanisms():
        count+=1;digest.update(d.canon(r)+b'\n')
        if r['PHYSICAL_TARGET'] is None:missing.add(r['MECHANISM_ID'])
    check('445136_frozen_forms_reproduced',count==445136 and digest.hexdigest()=='a55beb57cdca0a36be5e4b9016eea6fadb3964d6ce732cd5e5c4852b7c672d25')
    check('422_rederived_not_only_R4_claim',missing==set(byid))
    check('mechanism_denominator_unknown_not_zero',g['MECHANISMS_TOTAL'] is None and not contracts['mechanism-denominator-v5.json']['denominator_complete'])
    check('no_AST_claim_from_lexical_scan',contracts['constraint-applicability-v5.json']['lexical_scan_does_not_prove_AST'])
    ag=contracts['authority-graph-v5.json']
    check('all_inherited_open_edges_UNKNOWN',len(ag['inherited_unresolved_edges'])==422 and all(e['classification']=='UNKNOWN' for e in ag['inherited_unresolved_edges']))
    check('authority_denominators_unknown_not_zero',g['AUTHORITY_EDGES_TOTAL'] is None and g['UNCLASSIFIED_MUTATION_EDGES'] is None and g['UNMEDIATED_ACTIVE_MUTATION_EDGES'] is None)
    cap=contracts['typed-capability-catalog-v5.json']
    check('capabilities_not_derived_before_denominator',cap['required_typed_capabilities'] is None and cap['derived_records']==[] and cap['RAW_AUTHORITY_SURFACE']=='NOT_PROVEN')
    check('manifest_fixture_decision_preserved',contracts['fixture-correction-revalidation-v5.json']['MANIFEST_COMPATIBILITY_DECISION']=='C. B01_FIXTURE_MUST_CHANGE' and not contracts['fixture-correction-revalidation-v5.json']['implemented'] and not contracts['fixture-correction-revalidation-v5.json']['canonical_overlay'])
    findings=read('findings.json')
    check('four_frozen_blocker_IDs',{b['ID'] for b in findings['blockers']}=={'V2-NATIVE','V2-EPOCH','V2-PARTITIONS','V2-TEMPLATES'})
    check('residual_static_vs_physical_boundary',all(all(k in b for k in ['EXACT_MISSING_PROOF','WHY_STATIC_CLOSURE_FAILED','MINIMUM_NEXT_ACTION','WHETHER_IMPLEMENTATION_IS_REQUIRED','WHETHER_BUILD_EVIDENCE_IS_REQUIRED','WHETHER_RUNTIME_EVIDENCE_IS_REQUIRED','WHETHER_LIVE_DB_IS_REQUIRED']) for b in findings['blockers']))
    for name,kind in [('least-privilege-review-v5.json','LEAST_PRIVILEGE_REVIEW'),('static-adversarial-review-v5.json','STATIC_ADVERSARIAL_REVIEW')]:
        rev=read(name)
        check('independent_'+kind,rev['independent_review'] is True and rev['result']=='FAIL' and g[kind]=='FAIL')
        check('review_all_exact_contract_hashes_'+kind,set(rev['reviewed_files_sha256'])=={PREFIX+n for n in contracts} and all(filehash(p)==h for p,h in rev['reviewed_files_sha256'].items()))
        check('review_exact_frozen_source_hashes_'+kind,all(p in blobs and sha(blobs[p])==h for p,h in rev['inspected_source_git_sha256'].items()))
    lp=read('least-privilege-review-v5.json');ad=read('static-adversarial-review-v5.json')
    check('distinct_independent_reviewers',lp['reviewer']!=ad['reviewer'])
    check('LP_assertion_counts_preserved',lp['assertion_count']==len(lp['checks']) and lp['assertion_failures']==sum(not c['passed'] for c in lp['checks']) and len({c['id'] for c in lp['checks']})==len(lp['checks']))
    check('LP_design_failures_not_hidden',lp['integrity_assertion_failures']==0 and lp['design_assertion_failures']==lp['assertion_failures']==497)
    expected_blockers={'V2-NATIVE','V2-EPOCH','V2-PARTITIONS','V2-TEMPLATES'}
    check('both_review_blocker_IDs_agree',all({x.get('ID',x.get('id')) for x in r['findings']}==expected_blockers for r in (lp,ad)))
    check('forty_static_attacks',len(ad['attacks'])>=40 and len({a['id'] for a in ad['attacks']})>=40)
    check('blocked_not_pass',g['STATIC_GATE']=='BLOCKED' and g['BLOCKER_COUNT']==4)
    check('no_live_next_gate',g['CURRENTNESS_MUTATION_CLASSES_PROVEN']==0 and g['CURRENTNESS_MUTATION_CLASSES_UNPROVEN']==46 and g['B02_CURRENTNESS_INTEGRATION_GATE']=='NOT_RERUN' and g['COMPLETE_CURRENTNESS_GATE']=='FAIL_NOT_RERUN' and g['NEXT_EXECUTED'] is False)
    check('no_runtime_network_commands_recorded',read('source-integrity.json')['runtime_commands']==read('source-integrity.json')['network_calls']==[])
    report=(ROOT/REPORT).read_text(encoding='utf-8-sig')
    check('report_gate_and_counts_consistent',all(s in report for s in ['STATIC_GATE=BLOCKED','422','four blockers','37','14','seven','No commit','No push']))
    check('distinct_assertion_IDs',len({c['id'] for c in checks})==len(checks))
    return checks

def main():
    if '--generate' in sys.argv:
        module(OUT/'derive.py','r5_design_only').generate();return
    if '--seal' in sys.argv:
        files={p.relative_to(ROOT).as_posix() for p in OUT.iterdir() if p.is_file() and p.name!='SHA256-MANIFEST.json'}|{REPORT}
        save('SHA256-MANIFEST.json',dict(algorithm='SHA256',self_excluded=True,report_LF_normalized=True,files={p:filehash(p) for p in sorted(files)}));print('SEALED');return
    checks=verify()
    if '--record' in sys.argv:
        lp=read('least-privilege-review-v5.json')
        save('tests.json',dict(TESTS_DISTINCT=len(checks),TEST_FAILURES=0,checks=checks,
            independent_least_privilege_review_assertions=lp['assertion_count'],independent_least_privilege_design_failures=lp['design_assertion_failures'],
            independent_least_privilege_integrity_failures=lp['integrity_assertion_failures'],independent_adversarial_static_attacks=len(read('static-adversarial-review-v5.json')['attacks']),
            scope='TESTS_DISTINCT/TEST_FAILURES count verifier consistency assertions only. Independent design assertion failures497 and 40 static attacks are separate, retained negative design evidence; no design PASS inferred'))
        g=read('STATIC-GATE.json');g.update(TESTS_DISTINCT=len(checks),TEST_FAILURES=0);save('STATIC-GATE.json',g)
    else:
        m=read('SHA256-MANIFEST.json');files={p.relative_to(ROOT).as_posix() for p in OUT.iterdir() if p.is_file() and p.name!='SHA256-MANIFEST.json'}|{REPORT}
        assert files==set(m['files']) and all(filehash(p)==h for p,h in m['files'].items())
        assert read('tests.json')['TESTS_DISTINCT']==len(checks) and read('tests.json')['TEST_FAILURES']==0 and read('STATIC-GATE.json')['TESTS_DISTINCT']==len(checks)
    print(json.dumps(dict(evidence_verified=True,STATIC_GATE='BLOCKED',TESTS_DISTINCT=len(checks),TEST_FAILURES=0,NEXT_EXECUTED=False)))

if __name__=='__main__':main()
