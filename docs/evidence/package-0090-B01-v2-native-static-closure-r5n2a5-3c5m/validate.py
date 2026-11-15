"""Independent structural reconciliation and adversarial source-contract controls."""
import collections
import copy
import hashlib
import json
import pathlib
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2]
def read(n):return json.loads((P/(n+'.json')).read_text(encoding='utf-8'))
def prior(g,n):return json.loads((P.parent/('package-0090-B01-v2-native-static-closure-r5n2a5-3c5'+g)/(n+'.json')).read_text(encoding='utf-8-sig'))
def resolve(ref):
    file=ROOT/ref['path'];assert hashlib.sha256(file.read_bytes()).hexdigest()==ref['sha256']
    x=json.loads(file.read_text(encoding='utf-8-sig'))
    for part in ref['pointer'].lstrip('/').split('/') if ref['pointer'] else []:
        key=part.replace('~1','/').replace('~0','~');x=x[int(key)] if isinstance(x,list) else x[key]
    return x
def run():
    b=read('binding-recomputation');old=prior('l','canonical-input-binding-registry')['bindings'];inputs=b['inputs'];outputs=b['outputs'];comp=read('composition-recomputation');cert=read('all-49-certification-recomputation')['functions'];reqs=read('source-requirement-registry')['requirements'];roots=read('root-cause-registry')['roots']
    assert len(inputs)==1526 and {x['BINDING_ID'] for x in inputs}=={x['BINDING_ID'] for x in old}
    assert collections.Counter(x['STATUS'] for x in inputs)==dict(COMPLETE=441,MISSING=644,AMBIGUOUS=441)
    oldmap={x['BINDING_ID']:x for x in old};trans=collections.Counter((oldmap[x['BINDING_ID']]['STATUS'],x['STATUS']) for x in inputs)
    assert trans[('COMPLETE','COMPLETE')]==294 and trans[('AMBIGUOUS','COMPLETE')]==70 and trans[('MISSING','COMPLETE')]==77
    start={x['BINDING_ID'] for x in old if x['STATUS']!='COMPLETE'}|{'OUTPUT/'+x['WITNESS_ID'] for x in prior('l','output-binding-closure')['records'] if x['STATUS']!='COMPLETE'}|{x['EDGE_ID'] for x in prior('l','composition-edge-recomputation')['edges'] if x['STATUS']!='COMPLETE'}
    assert len(start)==2156
    members=[m for r in reqs for m in r['AFFECTED_BINDING_IDS']];assert set(members)==start and len(members)==len(start)
    members=[m for r in roots for k in ['AFFECTED_INPUT_BINDINGS','AFFECTED_OUTPUT_BINDINGS','AFFECTED_COMPOSITION_EDGES'] for m in r[k]];assert set(members)==start and len(members)==len(start)
    required=['SOURCE_REQUIREMENT_ID','AFFECTED_BINDING_IDS','SEMANTIC_OBJECT','DOMAIN','STAGE','REQUIRED_TYPE','REQUIRED_IDENTITY','REQUIRED_CARDINALITY','REQUIRED_AUTHORITY_CLASS','EXPECTED_SOURCE_KIND','KNOWN_CANDIDATE_SOURCES','SOURCE_PRESENT','SOURCE_REGISTERED','SOURCE_DERIVABLE','SOURCE_AMBIGUOUS','CARDINALITY_RESOLVED','AUTHORITY_SUFFICIENT','ROOT_CAUSE_ID']
    assert all(k in r for r in reqs for k in required)
    sources=read('recovered-source-registry')['entries'];assert len(sources)==len({s['CANONICAL_SOURCE_ID'] for s in sources})==21
    for s in sources:
        assert s['QUALIFICATION_STATUS']=='QUALIFIED' and s['SOURCE_DEFINITION_ESTABLISHED'] and not s['VALUE_ESTABLISHED']
        assert resolve(s['SOURCE_PATH_OR_EVIDENCE_ID'])==s['DECLARATION']
        for r in s['SOURCE_PROVENANCE']:resolve(r)
    plans=read('source-projection-contracts')['records'];assert len(plans)==77
    sm={s['CANONICAL_SOURCE_ID']:s for s in sources}
    def valid(plan):
        s=sm.get(plan['SOURCE_ID'])
        if not s or plan['MODEL_ID']!=s['IDENTITY']['model_id'] or plan['SOURCE_VALUES_INSTANTIATED'] or plan['EXPECTED_RESULT_CONSUMED']:return False
        if plan['PROOF_SCOPE']!='STRUCTURAL_PARAMETRIC_BINDING_ONLY':return False
        if s['SEMANTIC_OBJECT']=='APPROVED_COMPLETE_KEYED_MODULE_MAP':
            return 'nonempty finite map' in plan['PROJECTION_RULE'] and 'COMPLETE(load_name,absolute_path)' in plan['PROJECTION_RULE'] and 'lexicographic' in plan['PROJECTION_RULE'] and plan['OUTPUT_TYPE']=='bytes32 (exact32)'
        if s['SEMANTIC_OBJECT']=='AUTHENTICATED_READER_SQL_ROLE_ANCHOR':return plan['INPUT_ID']=='R' and 'SQL oid' in plan['OUTPUT_TYPE'] and 'not native participant enum' in plan['OUTPUT_TYPE']
        return s['SEMANTIC_OBJECT']=='TAGGED_SOURCE_RESOLUTION_AND_EXPECTED_OID' and plan['INPUT_ID'] in ['candidate_resolution','candidate_resolution.kind','frozen_object_oids']
    assert all(valid(p) for p in plans)
    controls=[]
    n=copy.deepcopy(plans[0]);n['MODEL_ID']='BASELINE/WRONG_SUBJECT/V1';controls.append(('wrong model identity rejected',not valid(n)))
    n=copy.deepcopy(next(p for p in plans if sm[p['SOURCE_ID']]['SEMANTIC_OBJECT']=='APPROVED_COMPLETE_KEYED_MODULE_MAP'));n['PROJECTION_RULE']=n['PROJECTION_RULE'].replace('COMPLETE(load_name,absolute_path)','load_name_only');controls.append(('partial module key rejected',not valid(n)))
    n=copy.deepcopy(next(p for p in plans if p['INPUT_ID']=='R'));n['OUTPUT_TYPE']='native actor enum:u16';controls.append(('native actor substituted for SQL role rejected',not valid(n)))
    n=copy.deepcopy(plans[0]);n['EXPECTED_RESULT_CONSUMED']=True;controls.append(('expected result as source rejected',not valid(n)))
    n=copy.deepcopy(plans[0]);n['SOURCE_VALUES_INSTANTIATED']=True;controls.append(('unestablished actual value rejected',not valid(n)))
    assert all(ok for _,ok in controls)
    assert read('derived-source-registry')['count']==0
    assert len(outputs)==350 and sum(o['STATUS']=='COMPLETE' for o in outputs)==77
    assert len(cert)==49 and sum(f['STRICT_CERTIFIED'] for f in cert)==10
    strict={f['FUNCTION_ID']:f['STRICT_CERTIFIED'] for f in cert}
    for f in cert:assert f['STRICT_CERTIFIED']==all(v is True for v in f['PROPERTIES'].values())
    for x in inputs+outputs:assert x['FUNCTION_STRICTLY_CERTIFIED']==strict[x['FUNCTION_ID']]
    for x in inputs:
        if 'C5M_SOURCE_ID' in x:assert x['CANONICAL_SOURCE_FACT']==[x['C5M_SOURCE_ID']] and x['C5M_SOURCE_ID'] in sm
    assert len(comp['edges'])==714 and sum(e['STATUS']=='COMPLETE' for e in comp['edges'])==91
    order={n:i for i,n in enumerate(comp['topological_order'])};assert len(order)==763
    for e in comp['edges']:
        assert order[e['SOURCE_FUNCTION']]<order[e['TARGET_FUNCTION']]
        if e['STATUS']=='COMPLETE':
            assert e['BLOCKER'] is None and e['SOURCE_BINDING_STATUS']==e['TARGET_BINDING_STATUS']=='COMPLETE'
            assert all(e[k]=='ESTABLISHED' for k in ['SEMANTIC_COMPATIBILITY','TYPE_COMPATIBILITY','STAGE_COMPATIBILITY'])
    cov=read('coverage-accounting');assert [cov[k] for k in ['STATICALLY_PROVEN','STATICALLY_DISPROVEN','UNKNOWN','CONTRADICTED']]==[0,0,350,0]
    assert read('canonical-evaluator-analysis')['complete']==0
    return dict(status='PASS',frozen_ids_checked=1526,starting_obligation_partition=2156,source_contracts=21,source_projection_contracts=77,all49_recertified=True,all714_edges_reconciled=True,cycles=0,adversarial_controls=[dict(control=n,passed=v) for n,v in controls],canonical_witness_executions=0,validation_scope='Static contracts and conditional parametric binding, not runtime data or behavior')
if __name__=='__main__':print(json.dumps(run()))
