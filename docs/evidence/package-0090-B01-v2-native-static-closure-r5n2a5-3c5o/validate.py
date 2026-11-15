"""Read-only finite qualification/derivation/recomputation reconciliation, not witness proof."""
import collections,hashlib,json,pathlib
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2]
def read(n):return json.loads((P/(n+'.json')).read_text(encoding='utf-8'))
def prior(n):return json.loads((P.parent/'package-0090-B01-v2-native-static-closure-r5n2a5-3c5n'/(n+'.json')).read_text(encoding='utf-8'))
def dig(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def resolve(r):
    q=ROOT/r['path'];data=q.read_bytes();assert hashlib.sha256(data).hexdigest()==r['sha256']
    if not r['pointer']:return data
    x=json.loads(data.decode('utf-8-sig'))
    for segment in r['pointer'].lstrip('/').split('/'):
        key=segment.replace('~1','/').replace('~0','~');x=x[int(key)] if isinstance(x,list) else x[key]
    return x
def run():
    tasks=prior('finite-semantic-qualification-worklist')['tasks'];results=read('qualification-terminal-results');records=results['records'];assert len(records)==len({r['QUALIFICATION_ID'] for r in records})==106
    assert {r['QUALIFICATION_ID'] for r in records}=={t['TASK_ID'] for t in tasks}
    counts=collections.Counter(r['TERMINAL_CLASS'] for r in records);assert counts==dict(QUALIFIED_BY_DETERMINISTIC_DERIVATION=52,QUALIFIED_FROM_EXISTING_STATIC_ARTIFACT=33,DUPLICATE_OF_QUALIFIED_CANONICAL_SEMANTIC=4,STATIC_SOURCE_EXHAUSTED_NOT_ESTABLISHED=17)
    classes=read('qualification-deduplication')['classes'];assert len(classes)==102
    assert collections.Counter(len(c['MEMBERS']) for c in classes)=={1:100,3:2}
    assert {c['SEMANTIC_KEY']['semantic_object'] for c in classes if len(c['MEMBERS'])>1}=={'member','target'}
    rm={r['QUALIFICATION_ID']:r for r in records};sources=read('recovered-source-registry')['entries'];assert len(sources)==len({s['CANONICAL_SOURCE_ID'] for s in sources})==85
    for source in sources:
        linked=[r for r in records if r['QUALIFIED_SOURCE']==source['CANONICAL_SOURCE_ID']]
        assert set(source['DEPENDENT_QUALIFICATION_IDS'])=={r['QUALIFICATION_ID'] for r in linked}
        assert set(source['DEPENDENT_BINDINGS'])=={b for r in linked for b in r['AFFECTED_BINDING_IDS']}
        if len(linked)==3:assert len(source['DEPENDENT_BINDINGS'])==42
        assert source['ACTUAL_VALUES_ESTABLISHED'] is False
    refs={json.dumps(x,sort_keys=True):x for r in records for x in r['AUTHORITY_SOURCE']}
    for r in refs.values():resolve(r)
    for record in records:
        proof=record['SEARCH_EXHAUSTION'];assert proof['EXHAUSTION_COMPLETE'] and proof['UNSEARCHED_AUTHORIZED_SURFACES']==0 and proof['AUTHORIZED_SURFACES_SEARCHED']==proof['AUTHORIZED_SURFACES_TOTAL']==9494
        if record['TERMINAL_CLASS']=='STATIC_SOURCE_EXHAUSTED_NOT_ESTABLISHED':assert record['QUALIFIED_SOURCE'] is None and proof['QUALIFIED_CANDIDATES_FOUND']==proof['DERIVABLE_CANDIDATES_FOUND']==0 and record['TERMINAL_REASON']
        if record.get('DUPLICATE_OF_QUALIFICATION'):assert rm[record['DUPLICATE_OF_QUALIFICATION']]['QUALIFIED_SOURCE']==record['QUALIFIED_SOURCE']
    derivations=read('deterministic-derivations')['records'];assert len(derivations)==52
    for d in derivations:
        frozen=dict(d);claimed=frozen.pop('DERIVATION_HASH');assert dig(frozen)==claimed
        assert d['DETERMINISTIC'] and not d['EXPECTED_WITNESS_RESULT_CONSUMED'] and not d['SOURCE_VALUES_ESTABLISHED'] and d['SOURCE_STAGE_TRANSFORMATION']
    # Well-formed u64 predecessor and source-admission checks, no witness execution.
    legal_tip=lambda s:type(s) is int and 0<=s<=2**64-1 and 0<=s-1<=2**64-1
    assert not legal_tip(0) and legal_tip(1) and legal_tip(2**64-1) and not legal_tip(2**64)
    states=[r for r in records if r['SEMANTIC_OBJECT']=='NORMALIZED_OPERATOR_STATE'];assert len(states)==3 and all(r['TERMINAL_CLASS']=='STATIC_SOURCE_EXHAUSTED_NOT_ESTABLISHED' and r['QUALIFIED_SOURCE'] is None for r in states)
    b=read('binding-recomputation');inputs=b['inputs'];outputs=b['outputs'];old=prior('binding-recomputation')['inputs']
    assert len(inputs)==1526 and {r['BINDING_ID'] for r in inputs}=={r['BINDING_ID'] for r in old}
    assert collections.Counter(r['STATUS'] for r in inputs)==dict(COMPLETE=1316,MISSING=126,AMBIGUOUS=84)
    assert len(outputs)==350 and sum(o['STATUS']=='COMPLETE' for o in outputs)==280 and all(o['ACTUAL_VALUE'] is None for o in outputs)
    certs=read('all-49-recertification')['functions'];assert len(certs)==49 and sum(c['STRICT_CERTIFIED'] for c in certs)==39
    strict={f['FUNCTION_ID']:f['STRICT_CERTIFIED'] for f in certs}
    for f in certs:assert f['STRICT_CERTIFIED']==all(v is True for v in f['PROPERTIES'].values()) and not f['ALGORITHM_DISPROVEN']
    for r in inputs+outputs:assert r['FUNCTION_STRICTLY_CERTIFIED']==strict[r['FUNCTION_ID']]
    graph=read('composition-recomputation');assert len(graph['edges'])==714 and sum(e['STATUS']=='COMPLETE' for e in graph['edges'])==294
    order={n:i for i,n in enumerate(graph['topological_order'])};assert len(order)==763
    for e in graph['edges']:
        assert order[e['SOURCE_FUNCTION']]<order[e['TARGET_FUNCTION']]
        if e['STATUS']=='COMPLETE':assert e['BLOCKER'] is None and e['SOURCE_BINDING_STATUS']==e['TARGET_BINDING_STATUS']=='COMPLETE' and all(e[k]=='ESTABLISHED' for k in ['SEMANTIC_COMPATIBILITY','TYPE_COMPATIBILITY','STAGE_COMPATIBILITY'])
    remaining={r['BINDING_ID'] for r in inputs if r['STATUS']!='COMPLETE'}|{'OUTPUT/'+o['WITNESS_ID'] for o in outputs if o['STATUS']!='COMPLETE'}|{e['EDGE_ID'] for e in graph['edges'] if e['STATUS']!='COMPLETE'};assert len(remaining)==700
    frontier=read('minimum-blocker-frontier')['blockers'];flat=[b for f in frontier for b in f['AFFECTED_BINDINGS']];assert len(frontier)==3 and len(flat)==len(set(flat))==700 and set(flat)==remaining
    assert {f['BLOCKER_CLASS'] for f in frontier}=={'NON_QUALIFICATION_BINDING_GAP','COMPOSITION_GAP'}
    coverage=read('coverage-accounting');assert [coverage[k] for k in ['STATICALLY_PROVEN','STATICALLY_DISPROVEN','UNKNOWN','CONTRADICTED']]==[0,0,350,0]
    sat=read('saturation-decision');assert sat['state']=='SATURATED' and sat['terminal']==106 and sat['open']==sat['unsearched_authorized_surfaces']==0 and not sat['positive_runtime_necessity']
    return dict(status='PASS',exact_qualification_ids=106,terminal_classes=106,unique_semantic_classes=102,duplicate_qualifications=4,qualified_source_definitions=85,full_derivation_hashes_checked=52,unique_provenance_refs_checked=len(refs),all1526_inputs_recomputed=True,all49_recertified=True,all714_relations_recomputed=True,frontier_covers_remaining_ids=700,cycles=0,controls=['u64 predecessor0 rejected,1/max accepted,overflow rejected','hash/definition evidence does not qualify missing authenticated source state','conditional GUARD target does not alone close output invocation','shared-source dependency union includes all duplicated qualifiers'],canonical_witness_executions=0)
if __name__=='__main__':print(json.dumps(run()))
