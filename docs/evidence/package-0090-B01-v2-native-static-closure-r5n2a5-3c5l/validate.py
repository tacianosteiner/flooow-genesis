"""Read-only structural and adversarial audit; never runs a canonical witness."""
import collections
import copy
import json
import pathlib

P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2]
def read(n):return json.loads((P/(n+'.json')).read_text(encoding='utf-8'))
def prior(g,n):return json.loads((P.parent/('package-0090-B01-v2-native-static-closure-r5n2a5-3c5'+g)/(n+'.json')).read_text(encoding='utf-8-sig'))
def run():
    plans=read('source-parametric-projection-proofs')['plans'];schemas=prior('d','schema-library')['schemas'];facts={f['FACT_ID']:f for f in prior('i','canonical-fact-registry')['facts']}
    full={'wrong_loader','wrong_parent','wrong_process_instance'}
    scalar={'wrong_binary':'complete_file_sha256','wrong_credential':'credential_certificate_or_endpoint_manifest_digest','stale_registry_revision':'generation_registry_revision'}
    def valid(p):
        family=p['witness'].split('/')[1];schema=schemas[p['schema']]
        expected=schema['fields'] if family in full else [f for f in schema['fields'] if f['name']==scalar[family]]
        if p['field_vector']!=expected or len(p['baseline_fact_ids'])!=len(expected):return False
        for fid,field in zip(p['baseline_fact_ids'],expected):
            f=facts.get(fid)
            if not f or f['VALUE_TYPE']!=field['type']:return False
            key=f['CANONICAL_KEY']
            if field['name']=='participant_id':
                if key!=['FROZEN_ENUM_VALUE','NATIVE_ACTOR_ENUM',p['actor']]:return False
            elif key!=['SOURCE_SCOPED_BINDING',dict(model_id=p['model_id'],selected_view=p['selected_view'],exact_variant_hash=p['exact_variant_hash'],state_side='BASELINE_OR_PARAMETER'),'identity['+p['actor']+']/'+p['schema']+'/'+field['name'],field['type']]:return False
        if p['values_instantiated'] or p['fixture_complete']:return False
        if not p['preserved_baseline_constraints'] or not p['future_instantiation_rule']:return False
        return p['side'] in ['INDEPENDENT_APPROVED_BASELINE','TAGGED_CANDIDATE_AFTER_EXACT_MUTATION']
    assert all(valid(p) for p in plans)
    controls=[]
    p=copy.deepcopy(plans[0]);p['actor']='NOT_THE_SOURCE_SUBJECT';controls.append(('reject cross actor identity',not valid(p)))
    p=copy.deepcopy(next(p for p in plans if p['witness'].endswith('/wrong_loader')));p['field_vector']=p['field_vector'][:1];p['baseline_fact_ids']=p['baseline_fact_ids'][:1];controls.append(('reject partial loader tuple',not valid(p)))
    p=copy.deepcopy(plans[0]);p['field_vector'][0]['type']='boolean';controls.append(('reject wrong source type',not valid(p)))
    p=copy.deepcopy(plans[0]);p['exact_variant_hash']='0'*64;controls.append(('reject mismatched exact variant',not valid(p)))
    p=copy.deepcopy(plans[0]);p['side']='EXPECTED_WITNESS_PASS';controls.append(('reject proof status as source stage',not valid(p)))
    assert all(ok for _,ok in controls)
    ins=read('canonical-input-binding-registry')['bindings'];old=prior('k','canonical-input-binding-registry')['bindings']
    assert {b['BINDING_ID'] for b in ins}=={b['BINDING_ID'] for b in old} and len(ins)==1526
    assert collections.Counter(b['STATUS'] for b in ins)==dict(COMPLETE=294,MISSING=721,AMBIGUOUS=511)
    amb=read('ambiguous-input-resolution')['records'];missing=read('missing-input-source-recovery')['records']
    assert len(amb)==595 and len(missing)==805
    assert {b['BINDING_ID'] for b in amb}=={b['BINDING_ID'] for b in old if b['STATUS']=='AMBIGUOUS'}
    assert {b['BINDING_ID'] for b in missing}=={b['BINDING_ID'] for b in old if b['STATUS']=='MISSING'}
    for b in amb:
        assert len(b['CANDIDATES'])==b['CANDIDATE_COUNT']
        for c in b['CANDIDATES']:
            assert all(k in c for k in ['SEMANTIC_OBJECT_MATCH','DOMAIN_MATCH','STAGE_MATCH','IDENTITY_MATCH','CARDINALITY_MATCH','AUTHORITY_MATCH','TYPE_MATCH','PROVENANCE_MATCH'])
    out=read('output-binding-closure')['records'];assert len(out)==350 and sum(o['STATUS']=='COMPLETE' for o in out)==63
    cert=read('all-49-certification-recomputation')['functions'];assert len(cert)==49 and sum(c['STRICT_CERTIFIED'] for c in cert)==8
    for c in cert:
        assert c['STRICT_CERTIFIED']==all(v is True for v in c['PROPERTIES'].values())
        if c['STRICT_CERTIFIED']:assert all(b['STATUS']=='COMPLETE' for b in ins if b['FUNCTION_ID']==c['FUNCTION_ID'])
    graph=read('composition-edge-recomputation');assert len(graph['edges'])==714 and len(set(graph['topological_order']))==763 and graph['cycles']==0
    oldedges=prior('k','composition-graph')['edges']
    assert [(e['SOURCE_FUNCTION'],e['TARGET_FUNCTION']) for e in graph['edges']]==[(e['SOURCE_FUNCTION'],e['TARGET_FUNCTION']) for e in oldedges]
    order={n:i for i,n in enumerate(graph['topological_order'])};assert all(order[e['SOURCE_FUNCTION']]<order[e['TARGET_FUNCTION']] for e in graph['edges'])
    coverage=read('coverage-accounting');assert [coverage[k] for k in ['STATICALLY_PROVEN','STATICALLY_DISPROVEN','UNKNOWN','CONTRADICTED']]==[0,0,350,0]
    for n,denom in [('input-binding-equivalence-classes',1526),('output-binding-equivalence-classes',350),('composition-equivalence-classes',714)]:
        x=read(n);assert sum(c['MEMBER_COUNT'] for c in x['classes'])==denom
        assert all(k in c for c in x['classes'] for k in ['BINDING_CLASS_ID','SEMANTIC_OBJECT','DOMAIN','STAGE','SOURCE_TYPE','SOURCE_IDENTITY_RULE','TARGET_FUNCTION_CLASS','TARGET_INPUT_ROLE','TRANSFORMATION','CARDINALITY','AUTHORITY_SOURCE','MEMBER_BINDINGS','MEMBER_COUNT','CLOSURE_STATUS'])
    return dict(status='PASS',source_parametric_plans_checked=len(plans),adversarial_controls=[dict(control=n,pass_=v) for n,v in controls],frozen_denominators=[1526,350,714,49],canonical_witness_executions=0,scope='Structural source identity/type/completeness and record reconciliation; existing frozen calculation implementations not changed or rerun')
if __name__=='__main__':print(json.dumps(run()))
