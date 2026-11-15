"""Read-only finite input/closure/provenance validation, never artifact construction."""
import collections,hashlib,json,pathlib
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2]
def read(n):return json.loads((P/(n+'.json')).read_text(encoding='utf-8-sig'))
def prior(n):return json.loads((P.parent/'package-0090-B01-v2-native-static-closure-r5n2a5-3c5r'/(n+'.json')).read_text(encoding='utf-8-sig'))
def dig(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def resolve(r):
    p=ROOT/r['path'];data=p.read_bytes();assert hashlib.sha256(data).hexdigest()==r['sha256']
    if not r['pointer']:return data
    x=json.loads(data.decode('utf-8-sig'))
    for segment in r['pointer'].lstrip('/').split('/'):
        key=segment.replace('~1','/').replace('~0','~');x=x[int(key)] if isinstance(x,list) else x[key]
    return x
def run():
    pre=read('preflight');assert pre['status']=='PASS' and len(pre['historical_sha256'])==9640
    original=prior('artifact-construction-analysis')['REQUIRED_INPUTS'];universe=read('construction-input-universe');items=universe['items'];ids=[x['INPUT_ID'] for x in items]
    assert ids==[x['INPUT_ID'] for x in original] and len(ids)==len(set(ids))==4
    assert universe['frozen_before_closure'] and universe['universe_id']=='CONSTRUCTION_INPUT_UNIVERSE/'+dig(items)
    for index,item in enumerate(items):assert resolve(item['SOURCE_CONTRACT'])==original[index] and item['MANDATORY_OR_CONDITIONAL']=='MANDATORY'
    terminals=read('construction-input-terminal-classification');records=terminals['records'];assert [x['INPUT_ID'] for x in records]==ids and terminals['universe_id']==universe['universe_id']
    assert collections.Counter(x['TERMINAL_STATUS'] for x in records)==dict(MISSING_STATIC_INPUT=3,AUTHENTICATION_MATERIAL_REQUIRED=1)
    assert all(x['STATUS_COUNT']==1 and not x['EXACT_INSTANCE_ESTABLISHED'] and x['QUALIFIED_SOURCE'] is None and x['QUALIFIED_DERIVATION'] is None for x in records)
    inventory=read('authorized-surface-inventory');surfaces=inventory['surfaces'];assert len(surfaces)==inventory['total']==9640 and len({s['PATH'] for s in surfaces})==9640
    assert {s['PATH']:s['HASH'] for s in surfaces}==pre['historical_sha256'] and all(s['SEARCH_COMPLETE'] and not s['qualification_from_match_alone'] for s in surfaces)
    known_surface_ids={s['SURFACE_ID'] for s in surfaces}
    for record in records:assert set(record['DISCOVERY_SURFACE_IDS'])<=known_surface_ids
    candidates=read('candidate-input-qualification')['candidates'];assert len(candidates)==11
    for c in candidates:resolve(c['PROVENANCE']);assert not c['QUALIFIED_INPUT_IDS'] and not c['DERIVABLE_COMPLETE_INPUT_IDS']
    exhausted=read('static-exhaustion-analysis')['records'];assert {x['INPUT_ID'] for x in exhausted}=={ids[0],ids[1],ids[3]}
    for x in exhausted:assert x['AUTHORIZED_SURFACES_TOTAL']==x['AUTHORIZED_SURFACES_SEARCHED']==9640 and x['UNSEARCHED_AUTHORIZED_SURFACES']==x['QUALIFIED_CANDIDATES_FOUND']==x['DERIVABLE_CANDIDATES_FOUND']==0 and x['STATIC_EXHAUSTION_COMPLETE']
    assert read('deterministic-derivations')['actual_derived_inputs']==0 and not read('deterministic-derivations')['records']
    auth=read('authentication-input-analysis');admit=read('admission-input-analysis')
    assert auth['INPUT_IDS']==ids[:3] and [auth[k] for k in ['AUTHENTICATION_INPUTS_REQUIRED','AUTHENTICATION_INPUTS_ESTABLISHED','AUTHENTICATION_INPUTS_MISSING']]==[3,0,3]
    assert admit['INPUT_IDS']==ids and [admit[k] for k in ['ADMISSION_INPUTS_REQUIRED','ADMISSION_INPUTS_ESTABLISHED','ADMISSION_INPUTS_MISSING']]==[4,0,4]
    assert auth['AUTHENTICATION_CRITERIA_KNOWN']==admit['ADMISSION_CRITERIA_KNOWN']=='YES'
    assert auth['AUTHENTICATION_MATERIAL_AVAILABLE']==auth['AUTHENTICATION_PREDICATE_SATISFIED']==admit['ADMISSION_EVIDENCE_AVAILABLE']==admit['ADMISSION_PREDICATE_SATISFIED']=='NO'
    assert not auth['authentication_attempted'] and not admit['admission_attempted']
    closure=read('input-closure');assert [closure[k] for k in ['CONSTRUCTION_INPUTS_REQUIRED_TOTAL','CONSTRUCTION_INPUTS_ESTABLISHED_TOTAL','CONSTRUCTION_INPUTS_MISSING_TOTAL','CONSTRUCTION_INPUTS_CONTRADICTED_TOTAL']]==[4,0,4,0] and closure['INPUT_CLOSURE_STATUS']=='INCOMPLETE'
    ready=read('construction-readiness');assert ready['ARTIFACT_CONSTRUCTION_READY']=='NO' and not ready['readiness_evaluation_triggered'] and not ready['artifact_constructed']
    frontier=read('residual-input-frontier');assert frontier['RESIDUAL_INPUT_BLOCKERS_TOTAL']==len(frontier['blockers'])==2
    assert {b['BLOCKER_CLASS'] for b in frontier['blockers']}=={'MISSING_STATIC_EVIDENCE','AUTHENTICATION_MATERIAL'}
    affected=[i for b in frontier['blockers'] for i in b['AFFECTED_CONSTRUCTION_INPUTS']];assert set(affected)==set(ids) and len(affected)==4
    assert read('runtime-necessity-analysis')['runtime_required_inputs']==0 and read('authority-necessity-analysis')['project_authority_required_inputs']==0
    reconciliation=read('artifact-predicate-state-reconciliation');historical=prior('source-admission-reevaluation')
    for k,value in reconciliation['historical_R_seven_state'].items():assert historical[k]==value
    assert reconciliation['AUTHENTICATION_KNOWLEDGE']==reconciliation['ADMISSION_KNOWLEDGE']=='NOT_ESTABLISHED' and not reconciliation['authentication_or_admission_attempted']
    summary=read('final-summary');assert summary['SELECTED_OUTCOME']=='H_MIXED_RESIDUAL_INPUT_FRONTIER' and summary['NEXT_GATE']=='BOUNDED_ARTIFACT_INPUT_FRONTIER_DECOMPOSITION' and summary['NEXT_EXECUTED'] is False
    for k,value in read('coverage-accounting')['preserved'].items():assert summary[k]==value==prior('final-summary')[k]
    assert [summary[k] for k in ['ORIGINAL_BLOCKERS','BLOCKERS_RESOLVED','BLOCKERS_REMAINING','LOCAL_FUNCTIONS_STRICT_CERTIFIED','CANONICAL_INPUT_BINDINGS_COMPLETE','CANONICAL_OUTPUT_BINDINGS_COMPLETE','COMPOSITION_EDGES_COMPLETE','COMPLETE_CANONICAL_DECISION_EVALUATORS','STATICALLY_PROVEN','STATICALLY_DISPROVEN','UNKNOWN','CONTRADICTED']]==[3,0,3,39,1316,280,294,0,0,0,350,0]
    return dict(status='PASS',exact_inherited_inputs=4,terminal_classifications=4,actual_inputs_established=0,missing_inputs=4,contradicted_inputs=0,bounded_static_surfaces=9640,canonical_candidates_checked=11,authentication_roles=[3,0,3],admission_roles=[4,0,4],residual_contract_classes=2,artifact_constructed=False,original_blockers_resolved=0,downstream_recomputation=False,witness_executions=0,history_knowledge_preserved=True)
if __name__=='__main__':print(json.dumps(run()))
