"""Offline R4 evidence verifier. Never runs SQL, native code or fixture tools.

--record writes only R4 tests.json and test counts after independent reviews.
Default verifies the final manifest and is read-only. --seal writes only the
R4 SHA256 manifest, with an explicit self exclusion (no circular hash).
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
BASE='fad53f6241724ea01e3ae552ebf6fe1e09794ea5'
PREFIX=OUT.relative_to(ROOT).as_posix()+'/'
REPORT='docs/evidence/PACKAGE-0090-B01-v2-static-closure-revision-4.md'
R3='docs/evidence/package-0090-B01-v2-static-closure-revision-3/'
R2='docs/evidence/package-0090-B01-v2-static-closure-revision-2/'
V043='applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V043__create_governed_offline_field_proof_capability_composition.sql'
VHASH='007ab786c417c41e2b1702ebf3852cb70ff5c142fa3fde195385e04c6dde8b4a'

def sha(b):return hashlib.sha256(b).hexdigest()
def read(f):return json.loads((OUT/f).read_text(encoding='utf-8-sig'))
def write(f,x):(OUT/f).write_bytes(json.dumps(x,indent=2,ensure_ascii=False).encode()+b'\n')
def git(*a):return subprocess.check_output(['git',*a],cwd=ROOT)
def datahash(p):
    b=(ROOT/p).read_bytes()
    return sha(b.replace(b'\r\n',b'\n') if p==REPORT else b)

def verify():
    checks=[]
    def check(name,pred,detail=None):
        checks.append(dict(id=name,passed=bool(pred),detail=detail))
        assert pred,name
    gate=read('STATIC-GATE.json');freeze=read('baseline-freeze.json')
    check('branch',git('branch','--show-current').decode().strip()==freeze['branch'])
    check('baseline_ancestor',git('merge-base',BASE,'HEAD').decode().strip()==BASE)
    check('baseline_exact',freeze['baseline_head']==freeze['origin_head_after_fetch']==BASE)
    check('initial_clean_assertions',freeze['worktree_clean_before_evidence'] and freeze['index_clean_before_evidence'])
    tree={}
    for row in git('ls-tree','-r','-z',BASE).split(b'\0'):
        if row:
            meta,p=row.split(b'\t',1);tree[p.decode()]=meta.decode().split()[2]
    ids=list(dict.fromkeys(tree[p] for p in freeze['input_git_sha256']))
    batch=subprocess.check_output(['git','cat-file','--batch'],input=('\n'.join(ids)+'\n').encode(),cwd=ROOT)
    raw={};pos=0
    for oid in ids:
        end=batch.index(b'\n',pos);h=batch[pos:end].decode().split();n=int(h[2]);pos=end+1
        assert h[:2]==[oid,'blob'];raw[oid]=batch[pos:pos+n];pos+=n+1
    check('all_frozen_source_hashes',all(sha(raw[tree[p]])==h for p,h in freeze['input_git_sha256'].items()),len(freeze['input_git_sha256']))
    check('all_frozen_checkout_bytes',all((ROOT/p).read_bytes().replace(b'\r\n',b'\n')==raw[tree[p]].replace(b'\r\n',b'\n') for p in freeze['input_git_sha256']))
    check('source_inventory_covers_prior_evidence',all(p in freeze['input_git_sha256'] for p in tree if p.startswith((R2,R3))))
    v=raw[tree[V043]];check('V043_exact_Git_LF_hash',sha(v)==VHASH)
    crc=zlib.crc32(''.join(v.decode('utf-8-sig').splitlines()).encode());crc=crc if crc<2**31 else crc-2**32
    check('Flyway_signed_CRC32',crc==1279591798)
    check('executable_fence_order',v.index(b"RAISE EXCEPTION USING ERRCODE = '55000'")<v.index(b'SET LOCAL search_path'))
    for r,h in freeze['protected_refs'].items():check('protected_ref_'+r,git('rev-parse',r).decode().strip()==h)
    changed=git('diff','--name-only',BASE,'HEAD').decode().splitlines()
    changed+=git('diff','--name-only').decode().splitlines()+git('diff','--cached','--name-only').decode().splitlines()
    changed += [x[3:] for x in git('status','--porcelain=v1','--untracked-files=all').decode().splitlines() if x.startswith('?? ')]
    check('only_R4_scope',all(p.startswith(PREFIX) or p==REPORT for p in changed),len(changed))
    for prefix in (R2,R3):
        m=json.loads(raw[tree[prefix+'SHA256-MANIFEST.json']])
        check('prior_manifest_'+prefix,all(sha(raw[tree[p]].replace(b'\r\n',b'\n'))==h or sha(raw[tree[p]])==h for p,h in m['files'].items()))
    spec=importlib.util.spec_from_file_location('r3_verified_offline_derivation',ROOT/R3/'derive.py')
    d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
    digest=hashlib.sha256();count=0;missing={}
    for record in d.expand_mechanisms():
        count+=1;digest.update(d.canon(record)+b'\n')
        if record['PHYSICAL_TARGET'] is None:missing[record['MECHANISM_ID']]=record
    part=read('class-mechanism-partitions-v4.json');rows=part['individual_missing_target_obligations']
    check('445136_individual_form_reproduction',count==445136 and digest.hexdigest()==part['expanded_records_sha256'])
    check('all_422_unique_obligations_indexed',len(rows)==len(missing)==422 and set(missing)=={r['id'] for r in rows})
    check('422_identity_form_source_preserved',all(r['operation_form']==missing[r['id']]['MUTATION_FORM'] and r['source_authority']==missing[r['id']]['SOURCE_POINTER'] for r in rows))
    check('422_not_fabricated_as_resolved',all(r['unresolved_count']==1 and r['physical_target'] is None and r['individual_resolution']=='UNRESOLVED_NOT_COLLAPSED' for r in rows))
    check('all_46_class_ids_preserved',part['classes']==json.loads(raw[tree[R3+'class-mechanism-partitions-v3.json']])['classes'] and len(part['classes'])==46)
    check('no_complete_mechanism_denominator',read('mechanism-denominator-v4.json')['MECHANISMS_TOTAL'] is None and not read('mechanism-denominator-v4.json')['denominator_complete'])
    native=read('native-seven-participant-contract-v4.json')['participants']
    check('seven_unique_native_design_rows',len(native)==7 and len({n['participant'] for n in native})==7)
    check('no_threads_or_harness_as_independence',all(n['independent_process_required'] and not n['threads_are_independence'] for n in native))
    check('unbuilt_binary_hash_not_invented',all(n['binary_identity']['expected_sha256'] is None and not n['fully_designed'] for n in native))
    for n in native:
        for a in n['source_authority']:
            p=a['path'];check('native_anchor_'+n['participant']+'_'+str(a['line']),sha(raw[tree[p]])==a['git_lf_sha256'])
    endpoints=read('endpoint-custody-v4.json')['endpoints']
    check('custody_actor_separation',len({e['holder'] for e in endpoints if e['kind'] in ('CREDENTIAL','AUDIT_RECORD','OUTCOME_RECORD')})==3)
    actor_ids={a['id'] for a in read('qualification-universe-v4.json')['identities']}
    check('custody_actors_explicit_in_universe',all(e[k] in actor_ids for e in endpoints for k in ['creator','holder','consumer','extinction_observer']))
    check('all_endpoint_types_custody_fields',all(all(e.get(k) for k in ['creator','holder','consumer','allowed_operation','forbidden_operation','lifecycle','durable_identity','revocation_mechanism','revocation_authority','extinction_observer','extinction_evidence','UNKNOWN','reseal_dependency']) for e in endpoints))
    check('endpoint_design_not_live_inventory',read('endpoint-inventory-v4.json')['ENDPOINTS_TOTAL'] is None and all(not e['fully_bound'] for e in endpoints))
    state=read('closed-epoch-state-machine-v4.json');old=json.loads(raw[tree[R3+'closed-epoch-state-machine-v3.json']])
    check('14_frozen_states_unchanged',state['states']==old['states'] and len(state['states'])==14)
    check('abstract_transition_relation_unchanged',state['transitions']==old['transitions'])
    inv=read('closed-epoch-reseal-invariants-v4.json')['invariants']
    required={r['id'] for r in inv}
    check('seven_conjunctive_reseal_guards',len(inv)==7 and all(set(t['required_known_true'])==required and t['from']=='RESEAL_PENDING' for t in state['transitions'] if t['to']=='SEALED_NEW_EPOCH'))
    # Three-valued validation of the declared conjunction, not runtime proof.
    allowed=[v for v in itertools.product((False,True,None),repeat=7) if all(x is True for x in v)]
    check('UNKNOWN_is_not_TRUE_2187_valuations',allowed==[(True,)*7])
    check('no_false_physical_reseal_PASS',all(not i['physical_binding_proven'] for i in inv) and gate['RESEAL_INVARIANTS_PHYSICALLY_BOUND']==0)
    check('durable_UNKNOWN_across_reconnect',read('unknown-outcome-contract-v4.json')['UNKNOWN_survives_reconnect'] and not read('unknown-outcome-contract-v4.json')['new_enrollment_allowed_while_UNKNOWN'])
    check('crash_ACK_loss_not_rollback',all(not c['process_death_means_abort'] and not c['reconnect_clears_pending'] for c in read('closed-epoch-crash-matrix-v4.json')['cases']))
    check('final_consumer_no_helper_session',not read('consumer-session-contract-v4.json')['helper_session_allowed'])
    check('capability_derivation_deferred',read('typed-capability-catalog-v4.json')['required_typed_capabilities'] is None and not read('typed-capability-catalog-v4.json')['derived_records'])
    check('authority_graph_not_false_zero',read('authority-graph-v4.json')['AUTHORITY_EDGES_TOTAL'] is None and read('authority-graph-v4.json')['UNMEDIATED_ACTIVE_MUTATION_EDGES'] is None)
    fix=read('fixture-correction-revalidation-v4.json')
    check('frozen_fixture_decision_no_overlay',fix['MANIFEST_COMPATIBILITY_DECISION']=='C. B01_FIXTURE_MUST_CHANGE' and not fix['overlay_created'] and not fix['fixture_implemented'])
    check('frozen_four_blocker_IDs',{x['ID'] for x in read('findings.json')['blockers']}=={'V2-PARTITIONS','V2-TEMPLATES','V2-EPOCH','V2-NATIVE'})
    for name,key in [('least-privilege-review-v4.json','LEAST_PRIVILEGE_REVIEW'),('static-adversarial-review-v4.json','STATIC_ADVERSARIAL_REVIEW')]:
        r=read(name)
        check('independent_review_'+name,r['independent_review'] is True and r['result']=='FAIL')
        check('review_exact_artifact_hashes_'+name,all(datahash(p)==h for p,h in r['reviewed_files_sha256'].items()))
        check('review_exact_source_hashes_'+name,all(sha(raw[tree[p]])==h for p,h in r['inspected_source_git_sha256'].items()))
    check('gate_remains_BLOCKED',gate['STATIC_GATE']=='BLOCKED' and gate['BLOCKER_COUNT']==4)
    check('no_live_followup',gate['CURRENTNESS_MUTATION_CLASSES_PROVEN']==0 and gate['CURRENTNESS_MUTATION_CLASSES_UNPROVEN']==46 and gate['B02_CURRENTNESS_INTEGRATION_GATE']=='NOT_RERUN' and gate['COMPLETE_CURRENTNESS_GATE']=='FAIL_NOT_RERUN' and gate['NEXT_EXECUTED'] is False)
    check('no_DB_native_execution_recorded',read('source-integrity.json')['runtime_commands']==[])
    check('distinct_test_IDs',len({c['id'] for c in checks})==len(checks))
    return checks

def main():
    if '--seal' in sys.argv:
        files={p.relative_to(ROOT).as_posix() for p in OUT.iterdir() if p.is_file() and p.name!='SHA256-MANIFEST.json'}|{REPORT}
        write('SHA256-MANIFEST.json',dict(algorithm='SHA256',self_excluded=True,report_LF_normalized=True,files={p:datahash(p) for p in sorted(files)}))
        print('SEALED');return
    checks=verify()
    if '--record' in sys.argv:
        write('tests.json',dict(TESTS_DISTINCT=len(checks),TEST_FAILURES=0,checks=checks,
            test_scope='Offline source/evidence consistency only; no design/runtime success inferred'))
        g=read('STATIC-GATE.json');g.update(TESTS_DISTINCT=len(checks),TEST_FAILURES=0);write('STATIC-GATE.json',g)
    else:
        m=read('SHA256-MANIFEST.json')
        actual={p.relative_to(ROOT).as_posix() for p in OUT.iterdir() if p.is_file() and p.name!='SHA256-MANIFEST.json'}|{REPORT}
        assert actual==set(m['files'])
        assert all(datahash(p)==h for p,h in m['files'].items())
        tests=read('tests.json');assert tests['TESTS_DISTINCT']==len(checks) and tests['TEST_FAILURES']==0
        assert read('STATIC-GATE.json')['TESTS_DISTINCT']==len(checks)
    print(json.dumps(dict(evidence_verified=True,STATIC_GATE='BLOCKED',TESTS_DISTINCT=len(checks),TEST_FAILURES=0,
        runtime_executed=False,known_obligations=445136,individually_unresolved_targets=422)))

if __name__=='__main__':main()
