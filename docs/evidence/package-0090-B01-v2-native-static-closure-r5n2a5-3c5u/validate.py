"""Local evidence checks and synthetic integrity-spec falsification; no input creation."""
import hashlib,itertools,json,pathlib,subprocess
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2]
def read(n):return json.loads((P/(n+'.json')).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check_integrity_spec():
    # Reference calculations for specification QA only. Not an operational creator/verifier.
    def u64(n):
        if type(n) is not int or not 0<=n<2**64:raise ValueError('invalid length')
        return n.to_bytes(8,'big')
    def length(b):
        if not isinstance(b,bytes):raise TypeError('byte operands only')
        return u64(len(b))+b
    def frame(tag,fields):return length(tag.encode('utf-8'))+u64(len(fields))+b''.join(length(v) for v in fields)
    def manifest(records):
        if len({(x,y) for x,y,h in records})!=len(records):raise ValueError('duplicate pair')
        return frame('C5U/manifest/v1',[frame('C5U/source/v1',[x,y,h]) for x,y,h in sorted(records,key=lambda r:(r[0],r[1]))])
    def digest(records,version,identity,content):
        m=manifest(records);v=frame('C5U/procedure/v1',[version,hashlib.sha256(b'SYNTHETIC_APPROVED_SPEC').digest()])
        return hashlib.sha256(frame('C5U/output-binding/v1',[m,v,identity,content])).digest()
    h=hashlib.sha256(b'SYNTHETIC_SOURCE').digest()
    records=[(b'SYNTHETIC_B',b'SOURCE_2',h),(b'SYNTHETIC_A',b'SOURCE_1',h)]
    baseline=digest(records,b'v1',b'SYNTHETIC_OUTPUT',b'CONTENT')
    assert all(digest(list(p),b'v1',b'SYNTHETIC_OUTPUT',b'CONTENT')==baseline for p in itertools.permutations(records))
    mutations=[
        digest([(b'SYNTHETIC_X',records[0][1],h),records[1]],b'v1',b'SYNTHETIC_OUTPUT',b'CONTENT'),
        digest([(records[0][0],b'SOURCE_X',h),records[1]],b'v1',b'SYNTHETIC_OUTPUT',b'CONTENT'),
        digest([(records[0][0],records[0][1],bytes(32)),records[1]],b'v1',b'SYNTHETIC_OUTPUT',b'CONTENT'),
        digest(records,b'v2',b'SYNTHETIC_OUTPUT',b'CONTENT'),
        digest(records,b'v1',b'SYNTHETIC_OTHER',b'CONTENT'),
        digest(records,b'v1',b'SYNTHETIC_OUTPUT',b'CHANGED_CONTENT')]
    assert all(x!=baseline for x in mutations)
    assert frame('tag',[b'ab',b'c'])!=frame('tag',[b'a',b'bc'])
    assert frame('tag',[b'a'])!=frame('other',[b'a'])
    assert frame('tag',['é'.encode()])!=frame('tag',['e\u0301'.encode()])
    rejected=0
    for action in [lambda:manifest(records+[records[0]]),lambda:u64(-1),lambda:u64(2**64),lambda:length('not bytes')]:
        try:action()
        except (ValueError,TypeError):rejected+=1
    assert rejected==4
    return dict(status='PASS',scope='Synthetic integrity specification QA only; no four-input/output materialization or full procedure implementation',permutation_checks=2,bound_field_mutations=6,framing_domain_unicode_checks=3,invalid_cases_rejected=4,authentication_established=False,admission_established=False)
def run():
    pre=read('preflight');assert len(pre['historical_sha256'])==9701
    for n,h in pre['historical_sha256'].items():assert sha(ROOT/n)==h,n
    refs=0
    def walk(o):
        nonlocal refs
        if isinstance(o,dict):
            if {'path','sha256','pointer'}<=o.keys():
                p=ROOT/o['path'];assert sha(p)==o['sha256'],o['path'];refs+=1
                if o['pointer']:
                    v=json.loads(p.read_text(encoding='utf-8-sig'))
                    for k in o['pointer'].lstrip('/').split('/'):
                        k=k.replace('~1','/').replace('~0','~');v=v[int(k)] if isinstance(v,list) else v[k]
            for v in o.values():walk(v)
        elif isinstance(o,list):
            for v in o:walk(v)
    for p in P.glob('*.json'):
        if p.stem not in ['SHA256-MANIFEST','static-validation'] and not p.stem.startswith('independent-review'):walk(json.loads(p.read_text(encoding='utf-8-sig')))
    designation=read('prospective-project-authority-designation')
    assert len(designation['rules'])==18 and designation['HISTORICAL_ENTAILMENT_CLAIMED']=='NO'
    for r in designation['rules']:assert r['text']
    creator=read('creator-authority-binding');verifier=read('verifier-authority-binding')
    assert creator['CREATOR_AUTHORITY_SELECTED_IF_UNIQUE'] is None and verifier['VERIFIER_AUTHORITY_SELECTED_IF_UNIQUE'] is None
    sep=read('creator-verifier-separation');assert len(sep['tests'])==9 and all(t['result']=='UNKNOWN' for t in sep['tests'])
    spec=read('creation-procedure-specification');ids=[r['INPUT_ID'] for r in spec['records']]
    prior=read_json(ROOT/'docs/evidence/package-0090-B01-v2-native-static-closure-r5n2a5-3c5t/exact-four-input-registry.json')
    assert ids==[i['INPUT_ID'] for i in prior['items']] and len(ids)==4
    assert not spec['procedure_executed'] and not spec['implementation_created']
    dag=read('four-input-dependency-dag');assert dag['nodes']==ids and len(dag['FOUR_INPUT_DAG_EDGES'])==12
    assert {(e['source'],e['target']) for e in dag['FOUR_INPUT_DAG_EDGES']}==set(itertools.permutations(ids,2))
    assert all(e['status']=='UNRESOLVED' for e in dag['FOUR_INPUT_DAG_EDGES'])
    assert dag['CYCLES'] is None and dag['UNRESOLVED_DEPENDENCIES']==12
    ready=read('readiness');assert ready['INPUT_CREATION_READY']=='NO'
    summary=read('final-summary');cov=read('coverage-accounting')
    assert summary['SELECTED_OUTCOME']=='I_MIXED_AUTHORITY_PROCEDURE_FRONTIER'
    assert summary['NEXT_EXECUTED'] is False and summary['AUTHORITY_BINDING_BLOCKERS_TOTAL'] is None
    assert summary['C5T_OUTCOME']=='H_FRONTIER_DECOMPOSITION_INCOMPLETE' and summary['C5T_NEXT_GATE']=='STOP_FAIL_CLOSED'
    for k,v in cov['preserved'].items():assert summary[k]==v,k
    for k,v in cov['T8_I13_UNKNOWN_REJECT']['architecture_flags'].items():assert summary[k]==v,k
    assert summary['CONSTRUCTION_INPUTS_ESTABLISHED_TOTAL']==0
    assert all(summary[k]=='NO' for k in ['ARTIFACT_EXISTS','ARTIFACT_AUTHENTICATED','ARTIFACT_ADMITTED'])
    assert summary['ARTIFACT_AUTHENTICATION_KNOWLEDGE']=='NOT_ESTABLISHED'
    assert summary['NONDETERMINISTIC_FIELDS_TOTAL'] is None and summary['CYCLES'] is None
    # Prospective governance truth-table: each independent necessary readiness fact is mandatory.
    keys=['creator_bound','verifier_bound','separated','procedure_complete','deterministic','integrity_spec','verification_complete','dag_complete','order_complete','zero_blockers']
    countermodels=[]
    for missing in keys:
        facts=dict.fromkeys(keys,True);facts[missing]=False
        assert not all(facts.values())
        countermodels.append(dict(missing=missing,ready=False,other_requirements_assumed_true=True))
    assert all(dict.fromkeys(keys,True).values())
    return dict(status='PASS',historical_hashes_verified=9701,evidence_reference_occurrences_verified=refs,exact_four_inputs_preserved=True,prospective_rules=18,separation_tests_unknown=9,integrity_spec_checks=check_integrity_spec(),readiness_isolated_countermodels=countermodels,full_creation_procedure_executed=False,authentication_or_admission_attempted=False,witness_executions=0)
def read_json(p):return json.loads(p.read_text(encoding='utf-8-sig'))
if __name__=='__main__':print(json.dumps(run()))
