"""Meaningful boundary checks: immutable corpus, exact denominator, no circular promotion."""
import hashlib,json,pathlib,subprocess
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2]
def read(n):return json.loads((P/(n+'.json')).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run():
    pre=read('preflight');assert len(pre['historical_sha256'])==9671
    for n,h in pre['historical_sha256'].items():assert sha(ROOT/n)==h,n
    reg=read('exact-four-input-registry');items=reg['items'];ids=[x['INPUT_ID'] for x in items]
    assert len(set(ids))==4 and sum(x['C5S_TERMINAL_CLASS']=='MISSING_STATIC_INPUT' for x in items)==3
    assert sum(x['C5S_TERMINAL_CLASS']=='AUTHENTICATION_MATERIAL_REQUIRED' for x in items)==1
    fields=['INPUT_ID','C5S_TERMINAL_CLASS','INPUT_ROLE','SEMANTIC_OBJECT','DOMAIN','STAGE','IDENTITY_REQUIREMENT','TYPE_REQUIREMENT','CARDINALITY_REQUIREMENT','AUTHORITY_REQUIREMENT','PROVENANCE_REQUIREMENT','AUTHENTICATION_REQUIREMENT','ADMISSION_REQUIREMENT','TEMPORAL_REQUIREMENT','EXACT_MISSING_FACT_OR_MATERIAL','WHY_REQUIRED_FOR_ARTIFACT','AFFECTED_ARTIFACT_FIELDS','AFFECTED_DOWNSTREAM_BINDINGS','AFFECTED_FUNCTIONS','AFFECTED_EDGES','AFFECTED_WITNESSES']
    for i in items:assert all(f in i for f in fields)
    # Verify every explicit evidence reference, including hashes and JSON pointers.
    refs=0
    def walk(obj):
        nonlocal refs
        if isinstance(obj,dict):
            if {'path','sha256','pointer'}<=obj.keys():
                p=ROOT/obj['path'];assert sha(p)==obj['sha256'],obj['path'];refs+=1
                if obj['pointer']:
                    value=json.loads(p.read_text(encoding='utf-8-sig'))
                    for key in obj['pointer'].lstrip('/').split('/'):
                        key=key.replace('~1','/').replace('~0','~')
                        value=value[int(key)] if isinstance(value,list) else value[key]
            for v in obj.values():walk(v)
        elif isinstance(obj,list):
            for v in obj:walk(v)
    for p in P.glob('*.json'):
        if p.stem not in ['SHA256-MANIFEST','static-validation'] and not p.stem.startswith('independent-review'):walk(json.loads(p.read_text(encoding='utf-8-sig')))
    dag=read('input-frontier-dependency-dag');remaining=set(dag['necessary_phase_nodes']);order=[]
    while remaining:
        ready=sorted(n for n in remaining if not any(e['target']==n and e['source'] in remaining for e in dag['necessary_phase_edges']))
        assert ready,'Necessary validation phase cycle';order+=ready;remaining.difference_update(ready)
    assert dag['INPUT_FRONTIER_DAG_STATUS']=='INCOMPLETE_ORDER_UNRESOLVED'
    assert all(dag['RESOLUTION_STEP_'+str(i)] is None for i in range(1,5))
    frontier=read('minimum-independent-input-frontier');assert frontier['MINIMUM_INDEPENDENT_INPUT_BLOCKERS'] is None and frontier['retained_count']==4
    assert {x['AFFECTED_INPUT_IDS'][0] for x in frontier['retained_obligations']}==set(ids)
    attacks=read('self-certification-adversarial-analysis');assert len(attacks['records'])==8
    assert all(not x['shortcut_accepted'] for x in attacks['records'])
    for record in attacks['records']:
        assert len(record['isolated_missing_fact_mutations'])==5
        for mutation in record['isolated_missing_fact_mutations']:
            assert sum(v is False for v in mutation['facts'].values())==1
            assert mutation['facts'][mutation['missing_fact']] is False
            assert not all(mutation['facts'].values()) and not mutation['necessary_facts_gate_passed']
    assert all(attacks['positive_control']['facts'].values())
    assert not attacks['positive_control']['authentication_or_admission_established']
    assert not read('bounded-creation-plans')['plans']
    summary=read('final-summary');coverage=read('coverage-accounting')
    for k,v in coverage['preserved'].items():assert summary[k]==v,(k,v)
    assert summary['SELECTED_OUTCOME']=='H_FRONTIER_DECOMPOSITION_INCOMPLETE' and summary['NEXT_GATE']=='STOP_FAIL_CLOSED' and summary['NEXT_EXECUTED'] is False
    assert summary['CONSTRUCTION_INPUTS_ESTABLISHED_TOTAL']==0 and summary['ARTIFACT_EXISTS']=='NO'
    assert summary['ARTIFACT_AUTHENTICATION_KNOWLEDGE']=='NOT_ESTABLISHED' and summary['ARTIFACT_ADMISSION_KNOWLEDGE']=='NOT_ESTABLISHED'
    assert coverage['T8_I13_UNKNOWN_REJECT']['UNKNOWN_REJECT']['exact_seven_catalog_row_omission_mapping_only']
    for k,v in coverage['T8_I13_UNKNOWN_REJECT']['architecture_flags'].items():assert summary[k]==v
    return dict(status='PASS',historical_hashes_verified=9671,exact_four_inputs_preserved=True,evidence_references_verified=refs,necessary_phase_topology=order,operational_creation_dag_proved=False,self_certification_models_rejected=8,canonical_attacks_executed=0,domain_witnesses_executed=0)
if __name__=='__main__':print(json.dumps(run()))
