"""Independent read-only checks; no canonical witness execution."""
import collections,copy,hashlib,json,pathlib
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2]
def read(n):return json.loads((P/(n+'.json')).read_text(encoding='utf-8'))
def old(n):return json.loads((P.parent/'package-0090-B01-v2-native-static-closure-r5n2a5-3c5m'/(n+'.json')).read_text(encoding='utf-8'))
def resolve(r):
    p=ROOT/r['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256'];x=json.loads(p.read_text(encoding='utf-8-sig'))
    for segment in r['pointer'].lstrip('/').split('/') if r['pointer'] else []:
        key=segment.replace('~1','/').replace('~0','~');x=x[int(key)] if isinstance(x,list) else x[key]
    return x
def run():
    binding=read('binding-recomputation');inputs=binding['inputs'];outputs=binding['outputs'];certs=read('strict-certification-recomputation')['functions'];graph=read('composition-recomputation');universe=read('remaining-source-universe')['requirements'];frontier=read('minimum-blocker-frontier')['blockers']
    prior=old('binding-recomputation');assert {b['BINDING_ID'] for b in inputs}=={b['BINDING_ID'] for b in prior['inputs']} and len(inputs)==1526
    assert collections.Counter(b['STATUS'] for b in inputs)==dict(COMPLETE=567,MISSING=581,AMBIGUOUS=378)
    assert len(outputs)==350 and sum(o['STATUS']=='COMPLETE' for o in outputs)==119
    assert len(certs)==49 and sum(c['STRICT_CERTIFIED'] for c in certs)==16
    strict={f['FUNCTION_ID']:f['STRICT_CERTIFIED'] for f in certs}
    for f in certs:assert f['STRICT_CERTIFIED']==all(v is True for v in f['PROPERTIES'].values()) and not f['ALGORITHM_DISPROVEN']
    for b in inputs+outputs:assert b['FUNCTION_STRICTLY_CERTIFIED']==strict[b['FUNCTION_ID']]
    sources=read('newly-recovered-sources')['entries'];assert len(sources)==28 and len({s['CANONICAL_SOURCE_ID'] for s in sources})==28
    previous={s['CANONICAL_SOURCE_ID'] for s in old('recovered-source-registry')['entries']};assert not previous&{s['CANONICAL_SOURCE_ID'] for s in sources}
    for s in sources:
        assert s['QUALIFICATION_STATUS']=='QUALIFIED' and s['VALUES_ESTABLISHED'] is False
        for r in s['PROVENANCE']:resolve(r)
    plans=read('source-projection-contracts')['records'];assert len(plans)==63
    for plan in plans:assert not plan['SOURCE_VALUES_ESTABLISHED'] and not plan['EXPECTED_RESULT_CONSUMED']
    dup=next(p for p in plans if p['WITNESS_ID'].endswith('/catalog_duplication'));assert 'rows:B+[r]' in dup['RULE'] and 'ALL other rows' in dup['RULE'] and 'n->n+1' in dup['RULE']
    # Adversarial source-shape controls, no witness algorithm is run.
    def valid_duplicate(plan):return all(x in plan['RULE'] for x in ['rows:B+[r]','ALL other rows','ALL9 columns','n->n+1',"key_fields:['oid']"])
    bad=copy.deepcopy(dup);bad['RULE']=bad['RULE'].replace('rows:B+[r]','rows:[r,r]');assert not valid_duplicate(bad)
    bad2=copy.deepcopy(dup);bad2['RULE']=bad2['RULE'].replace("key_fields:['oid']","key_fields:['rolname']");assert not valid_duplicate(bad2)
    assert len(graph['edges'])==714 and sum(e['STATUS']=='COMPLETE' for e in graph['edges'])==133
    order={n:i for i,n in enumerate(graph['topological_order'])};assert len(order)==763
    for e in graph['edges']:
        assert order[e['SOURCE_FUNCTION']]<order[e['TARGET_FUNCTION']]
        if e['STATUS']=='COMPLETE':assert e['BLOCKER'] is None and e['SOURCE_BINDING_STATUS']==e['TARGET_BINDING_STATUS']=='COMPLETE' and all(e[k]=='ESTABLISHED' for k in ['SEMANTIC_COMPATIBILITY','TYPE_COMPATIBILITY','STAGE_COMPATIBILITY'])
    remaining={b['BINDING_ID'] for b in inputs if b['STATUS']!='COMPLETE'}|{'OUTPUT/'+o['WITNESS_ID'] for o in outputs if o['STATUS']!='COMPLETE'}|{e['EDGE_ID'] for e in graph['edges'] if e['STATUS']!='COMPLETE'};assert len(remaining)==1771
    members=[b for u in universe for b in u['REMAINING_BINDINGS']];assert set(members)==remaining and len(members)==len(remaining)
    fm=[b for f in frontier for k in ['AFFECTED_INPUT_BINDINGS','AFFECTED_OUTPUT_BINDINGS','AFFECTED_COMPOSITION_EDGES'] for b in f[k]];assert set(fm)==remaining and len(fm)==len(remaining)
    assert len(frontier)==4 and len(universe)==121 and sum(bool(u['REMAINING_BINDINGS']) for u in universe)==106
    sat=read('saturation-analysis');assert sat['STATIC_RECOVERY_STATE']=='PRODUCTIVE' and not sat['saturation_claim'] and not sat['semantic_search_exhaustive'] and sat['STATIC_SOURCE_REQUIREMENTS_WITH_QUALIFIED_CANDIDATES']==0
    for u in universe:
        assert u['PRIMARY_STATUS_COUNT']==1
        if u['REMAINING_BINDINGS']:assert not u['RUNTIME_REQUIRED'] and not u['ABSENT_AFTER_EXHAUSTIVE_STATIC_SEARCH'] and not u['ARCHITECTURAL_BLOCKED']
    surfaces=read('static-search-surface-registry')['surfaces']
    for s in surfaces:assert s['REJECTED_RESULT_COUNT']==0 and s['UNQUALIFIED_DISCOVERY_COUNT']==s['RESULT_COUNT'] and s['SEARCH_COMPLETE']
    cov=read('coverage-accounting');assert [cov[k] for k in ['STATICALLY_PROVEN','STATICALLY_DISPROVEN','UNKNOWN','CONTRADICTED']]==[0,0,350,0]
    return dict(status='PASS',input_ids=1526,source_definitions=28,source_projections=len(plans),remaining_obligation_partition=1771,frontier_partition=4,all49_recertified=True,all714_relations_recomputed=True,cycles=0,adversarial_controls=['reject total two-row shortcut','reject changed natural key'],canonical_witness_executions=0,scope='Structural source contracts and consistency; no semantic exhaustion or actual-value proof')
if __name__=='__main__':print(json.dumps(run()))
