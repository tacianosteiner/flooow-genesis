"""Read-only decomposition/set/counterfactual audit; no binding recomputation or closure."""
import collections,hashlib,itertools,json,pathlib
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2]
def read(n):return json.loads((P/(n+'.json')).read_text(encoding='utf-8'))
def original(n):return json.loads((P.parent/'package-0090-B01-v2-native-static-closure-r5n2a5-3c5o'/(n+'.json')).read_text(encoding='utf-8'))
def resolve(r):
    q=ROOT/r['path'];data=q.read_bytes();assert hashlib.sha256(data).hexdigest()==r['sha256']
    if not r['pointer']:return data
    x=json.loads(data.decode('utf-8-sig'))
    for piece in r['pointer'].lstrip('/').split('/'):
        key=piece.replace('~1','/').replace('~0','~');x=x[int(key)] if isinstance(x,list) else x[key]
    return x
def run():
    old=original('minimum-blocker-frontier')['blockers'];registry=read('three-blocker-registry')['blockers'];assert len(old)==len(registry)==3
    assert [r['BLOCKER_ID'] for r in registry]==[r['BLOCKER_ID'] for r in old]
    for r,b in zip(registry,old):
        assert set(r['AFFECTED_INPUT_BINDINGS']+r['AFFECTED_OUTPUT_BINDINGS']+r['AFFECTED_COMPOSITION_EDGES'])==set(b['AFFECTED_BINDINGS'])
        assert set(r['AFFECTED_QUALIFICATION_IDS'])==set(b['AFFECTED_QUALIFICATIONS'])
    classes=read('blocker-classification')['classifications'];assert [r['PRIMARY_CLASS'] for r in classes]==['CANONICAL_BINDING_RULE_REQUIRED','STATIC_SOURCE_ABSENT_AFTER_EXHAUSTION','CANONICAL_COMPOSITION_RULE_REQUIRED']
    assert all(r['CLASSIFICATION_UNRESOLVED']=='NO' and len(r['NONDOMINATED_CLASSES'])==1 for r in classes)
    mapping=read('exhausted-17-mapping');assert mapping['MAPPED_TO_FRONTIER']==17 and mapping['UNMAPPED']==mapping['MULTI_MAPPED']==0 and mapping['FRONTIER_COMPLETENESS']=='PASS'
    expected={q['QUALIFICATION_ID'] for q in original('qualification-terminal-results')['records'] if q['TERMINAL_CLASS']=='STATIC_SOURCE_EXHAUSTED_NOT_ESTABLISHED'};assert {r['QUALIFICATION_ID'] for r in mapping['records']}==expected and len(mapping['records'])==17
    assert sorted(collections.Counter(r['BLOCKER_IDS'][0] for r in mapping['records']).values())==[2,3,12]
    rels=read('causal-dependency-graph')['relations'];ids=[r['BLOCKER_ID'] for r in registry]
    assert {(r['UPSTREAM_BLOCKER'],r['DOWNSTREAM_BLOCKER']) for r in rels}==set(itertools.permutations(ids,2)) and len(rels)==6
    assert all(r['IF_A_RESOLVED_DOES_B_REMAIN_INDEPENDENT']=='PROVEN_YES' and r['SEMANTIC_BLOCKER_INDEPENDENCE']=='PROVEN_YES' and r['COUNTERMODEL'] for r in rels)
    partial=[r for r in rels if r['RELATION']=='A_PARTIALLY_CAUSES_B'];assert len(partial)==2 and sorted(len(r['AFFECTED_DOWNSTREAM_EDGE_IDS']) for r in partial)==[21,49] and all(r['DOWNSTREAM_BLOCKER']==ids[2] for r in partial)
    minset=read('minimum-independent-blocker-set');assert minset['MINIMUM_INDEPENDENT_BLOCKERS']==3 and minset['CAUSALLY_REDUNDANT_BLOCKERS']==minset['SHARED_UPSTREAM_CAUSES']==0 and minset['global_atomic_minimum']=='NOT_ESTABLISHED'
    impacts=read('structural-counterfactual-impact')['records'];assert [(r['INPUT_BINDINGS_POTENTIALLY_UNLOCKED'],r['OUTPUT_BINDINGS_POTENTIALLY_UNLOCKED'],r['FUNCTIONS_POTENTIALLY_CERTIFIABLE'],r['COMPOSITION_EDGES_POTENTIALLY_UNLOCKED']) for r in impacts]==[(168,49,7,49),(42,21,3,21),(0,0,0,280)]
    assert impacts[2]['COMPOSITION_EDGES_CONDITIONALLY_UNLOCKABLE']==350 and all(r['ACTUAL_BINDINGS_CHANGED']==0 and not r['OTHER_BLOCKERS_ELIMINATED'] for r in impacts)
    em={e['EDGE_ID']:e for e in original('composition-recomputation')['edges']};assert all(em[e]['SOURCE_BINDING_STATUS']=='COMPLETE' for e in impacts[2]['COMPOSITION_EDGE_IDS'])
    assert read('minimum-decision-dossier')['DECISIONS_REQUIRED_TOTAL']==0 and read('runtime-necessity-analysis')['RUNTIME_BLOCKERS']==0
    order=read('resolution-order');assert not order['arbitrary_total_order_selected'] and len(order['rule_definition_order'])==3 and all(r['relation']=='CAN_RUN_IN_PARALLEL' for r in order['rule_definition_order'])
    assert sorted(int(r['scope'].split()[0]) for r in order['application_order'])==[21,49]
    coverage=read('coverage-accounting');os=original('final-summary')
    for k,v in coverage['counts'].items():assert v==os[k]
    assert not coverage['full_binding_recomputation_executed'] and not coverage['closure_simulated'] and not coverage['witness_executed']
    assert [coverage['counts'][k] for k in ['LOCAL_FUNCTIONS_STRICT_CERTIFIED','CANONICAL_INPUT_BINDINGS_COMPLETE','CANONICAL_OUTPUT_BINDINGS_COMPLETE','COMPOSITION_EDGES_COMPLETE','COMPLETE_CANONICAL_DECISION_EVALUATORS','UNKNOWN']]==[39,1316,280,294,0,350]
    refs={json.dumps(r,sort_keys=True):r for x in registry for k in ['SOURCE_EVIDENCE','AUTHORITY_EVIDENCE'] for r in x[k]}
    for r in refs.values():resolve(r)
    assert read('primary-result')['selected_outcome']=='H_MIXED_CAUSAL_FRONTIER'
    return dict(status='PASS',exact_original_blockers=3,exhausted_qualification_ids_mapped=17,ordered_countermodels=6,partial_readiness_edges=[49,21],minimum_scope='Original three C5O bundles, atomic minimum not established',counterfactual_edges_ready=280,counterfactual_edges_conditional=350,source_refs_checked=len(refs),new_rule_definitions=0,actual_closures=0,full_binding_recomputations=0,witness_executions=0)
if __name__=='__main__':print(json.dumps(run()))
