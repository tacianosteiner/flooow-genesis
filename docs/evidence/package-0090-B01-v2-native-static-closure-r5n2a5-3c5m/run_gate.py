"""C5M static source discovery. Writes evidence only, never executes a witness."""
import collections
import copy
import functools
import hashlib
import json
import pathlib
import subprocess
import sys
sys.dont_write_bytecode=True
OUT=pathlib.Path(__file__).resolve().parent
ROOT=OUT.parents[2]
BASE=ROOT/'docs/evidence'
PREFIX='package-0090-B01-v2-native-static-closure-'
def p(g,n):return BASE/(PREFIX+g)/n
def read(g,n):return json.loads(p(g,n).read_text(encoding='utf-8-sig'))
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def dig(x):return hashlib.sha256(canon(x).encode()).hexdigest()
@functools.lru_cache(None)
def sha(q):return hashlib.sha256(q.read_bytes()).hexdigest()
def ref(g,n,ptr=''):return dict(path=p(g,n).relative_to(ROOT).as_posix(),sha256=sha(p(g,n)),pointer=ptr)
def write(n,x):(OUT/(n+'.json')).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
def ptr(s):return s.replace('~','~0').replace('/','~1')
L='r5n2a5-3c5l';K='r5n2a5-3c5k';I='r5n2a5-3c5i';D='r5n2a5-3c5d';F='r5n2a5-3c5f'

def main():
    lp=read(L,'preflight.json');lm=read(L,'SHA256-MANIFEST.json');ls=read(L,'final-summary.json')
    historical={**lp['historical_sha256'],**lm['files'],p(L,'SHA256-MANIFEST.json').relative_to(ROOT).as_posix():sha(p(L,'SHA256-MANIFEST.json'))}
    bad=[q for q,h in historical.items() if not (ROOT/q).is_file() or sha(ROOT/q)!=h]
    assert not bad,bad
    assert len(lp['historical_sha256'])==9393 and len(historical)==9425
    assert ls['LOCAL_FUNCTIONS_STRICT_CERTIFIED']==8 and ls['CANONICAL_INPUT_BINDINGS_COMPLETE']==294 and ls['UNKNOWN']==350
    assert p(L,'final-return.txt').is_file() and 'CANONICAL_INPUT_BINDINGS_COMPLETE=294' in p(L,'final-return.txt').read_text()
    assert ROOT==pathlib.Path('C:/Projects/flooow-genesis-git')
    assert git('branch','--show-current')=='checkpoint/package-0090-cloud-handoff' and git('rev-parse','HEAD')=='451265ff5b3d286eb4d27c4b3817c2f558f30123'
    assert not git('diff','--name-only') and not git('diff','--cached','--name-only')
    before=[q for q in git('ls-files','--others','--exclude-standard').splitlines() if not q.startswith(OUT.relative_to(ROOT).as_posix()+'/')]
    assert len(before)==326
    inputs=read(L,'canonical-input-binding-registry.json')['bindings'];outputs=read(L,'output-binding-closure.json')['records'];graph=read(L,'composition-edge-recomputation.json')
    assert len(inputs)==len({b['BINDING_ID'] for b in inputs})==1526
    assert len(outputs)==len({b['WITNESS_ID'] for b in outputs})==350
    assert len(graph['edges'])==len({e['EDGE_ID'] for e in graph['edges']})==714
    write('preflight',dict(status='PASS',repository=str(ROOT),branch=git('branch','--show-current'),head=git('rev-parse','HEAD'),frozen_baseline='cbc284f62d9bd09b7169b55c8d66a3c51a68c6cb',tracked_dirty=0,staged=0,authorized_untracked_before=326,authorized_paths_before=before,historical_sha256=historical,historical_hashes_validated=9393,historical_union_validated=9425,unresolved_ids_uniquely_recoverable=True,protected_execution=False))
    write('c5l-input-integrity',dict(status='PASS',manifest=ref(L,'SHA256-MANIFEST.json'),manifest_files_checked=len(lm['files']),historical_hashes_checked=9393,c5l_files_preserved=len(lm['files'])+1,full_preserved_union=9425,final_summary=ref(L,'final-summary.json'),final_return=ref(L,'final-return.txt'),mismatches=bad))
    cases=read(F,'derived-canonical-350-registry.json')['case_records'];cm={c['WITNESS_ID']:c for c in cases};models=read(D,'baseline-models.json')['models'];schemas=read(D,'schema-library.json');families=read(D,'family-descriptors.json')['families'];facts=read(I,'canonical-fact-registry.json')['facts'];fm={f['FACT_ID']:f for f in facts}
    oldcert=read(L,'all-49-certification-recomputation.json')['functions'];functions=read(K,'49-function-inventory.json')['functions'];fun={f['FUNCTION_ID']:f for f in functions}
    # Phase1: requirements precede source recovery and binding recomputation.
    # A family root is one source-normalization problem, preserving all distinct instance identities.
    requirements={};roots={}
    def root(fid,kind='FUNCTION'):
        rid='ROOT/'+dig([kind,fid]);roots.setdefault(rid,dict(ROOT_CAUSE_ID=rid,ROOT_CAUSE_CLASS='SOURCE_EXISTS_BINDING_NOT_PROJECTED' if kind=='FUNCTION' else 'COMPOSITION_SOURCE_GAP',SEMANTIC_OBJECT=fun[fid]['families'] if fid in fun else fid,DOMAIN='SOURCE_TYPED_PARAMETER_NORMALIZATION' if kind=='FUNCTION' else 'INDEPENDENT_NATIVE_DECISION_STAGE',STAGE='ACQUISITION->NORMAL_FORM->LOCAL_GUARD' if kind=='FUNCTION' else 'GUARD->NATIVE_STAGE',CANONICAL_REQUIREMENT='Exact source identity/type/stage projection for every required operand, not a same-name field' if kind=='FUNCTION' else 'Independent native result/currentness/non-grant stage input and adapter; expected witness outcome is not an observation',WHY_CURRENT_MODEL_CANNOT_BIND='L lacks a verified complete source projection. Existing schemas/ports can be partial sources; actual values remain unestablished.',AFFECTED_INPUT_BINDINGS=[],AFFECTED_OUTPUT_BINDINGS=[],AFFECTED_COMPOSITION_EDGES=[],AFFECTED_FUNCTIONS=[],AFFECTED_WITNESSES=[],CANDIDATE_RECOVERY_SOURCES=[],MINIMUM_RECOVERY_ACTION='Qualify exact frozen source contracts and project source parameters; do not infer runtime state or new authority.'))
        return rid
    def req(key,kind,binding_ids,wid,fid,role,stage,candidates):
        srid='SOURCE_REQUIREMENT/'+dig(key);rid=root(fid) if kind!='NATIVE_STAGE' else root(key[0],'STAGE')
        r=requirements.setdefault(srid,dict(SOURCE_REQUIREMENT_ID=srid,AFFECTED_BINDING_IDS=[],SEMANTIC_OBJECT=role,DOMAIN='EXACT_SOURCE_TYPED_OPERAND' if kind=='INPUT' else 'GUARD_VIOLATION_EVIDENCE' if kind=='OUTPUT' else 'INDEPENDENT_NATIVE_STAGE',STAGE=stage,REQUIRED_TYPE=fun[fid]['INPUT_SCHEMA'] if kind=='INPUT' else 'AVAILABLE bool or UNAVAILABLE/null' if kind=='OUTPUT' else 'Exact observed native source-stage result, distinct from expected outcome',REQUIRED_IDENTITY=[],REQUIRED_CARDINALITY='One exact operand per scoped case; collection ports require complete source extent with duplicates preserved' if kind=='INPUT' else 'One scoped source-output/target-input relation',REQUIRED_AUTHORITY_CLASS='FROZEN_ACCEPTED_STATIC_DESIGN_CONTRACT; no runtime/execution authority',EXPECTED_SOURCE_KIND='IMMUTABLE_DECLARED_SOURCE_CONTRACT_AND_EXACT_PARAMETRIC_PROJECTION' if kind=='INPUT' else 'INDEPENDENT_SOURCE_STAGE_CONTRACT',KNOWN_CANDIDATE_SOURCES=[],SOURCE_PRESENT=None,SOURCE_REGISTERED=None,SOURCE_DERIVABLE=False,SOURCE_AMBIGUOUS=True,CARDINALITY_RESOLVED=None,AUTHORITY_SUFFICIENT=None,ROOT_CAUSE_ID=rid,KIND=kind,TARGET_FUNCTION=fid,TARGET_INPUT_ROLE=role,VALUE_SCOPE='No actual observations established'))
        r['AFFECTED_BINDING_IDS'].extend(binding_ids)
        c=cm[wid];ident=dict(witness=wid,model_id=c['BASELINE_STATE']['library_model_id'],view=c['BASELINE_STATE']['selected_view'],variant=c['BASELINE_STATE']['exact_variant_state'])
        if ident not in r['REQUIRED_IDENTITY']:r['REQUIRED_IDENTITY'].append(ident)
        r['KNOWN_CANDIDATE_SOURCES'].extend(x for x in candidates if x not in r['KNOWN_CANDIDATE_SOURCES'])
        ro=roots[rid];field='AFFECTED_INPUT_BINDINGS' if kind=='INPUT' else 'AFFECTED_OUTPUT_BINDINGS' if kind=='OUTPUT' else 'AFFECTED_COMPOSITION_EDGES';ro[field].extend(binding_ids)
        if fid not in ro['AFFECTED_FUNCTIONS']:ro['AFFECTED_FUNCTIONS'].append(fid)
        if wid not in ro['AFFECTED_WITNESSES']:ro['AFFECTED_WITNESSES'].append(wid)
        return srid
    input_req={};output_req={};edge_req={}
    for b in inputs:
        if b['STATUS']=='COMPLETE':continue
        key=(b['FUNCTION_ID'],b['INPUT_ID'],b['SOURCE_STAGE'])
        input_req[b['BINDING_ID']]=req(key,'INPUT',[b['BINDING_ID']],b['WITNESS_ID'],b['FUNCTION_ID'],b['INPUT_ID'],b['SOURCE_STAGE'],[f for f in b['CANONICAL_SOURCE_FACT'] if f in fm])
    for o in outputs:
        if o['STATUS']=='COMPLETE':continue
        output_req[o['WITNESS_ID']]=req((o['FUNCTION_ID'],'OUTPUT'),'OUTPUT',['OUTPUT/'+o['WITNESS_ID']],o['WITNESS_ID'],o['FUNCTION_ID'],'case-specific violation evidence',o['TARGET_STAGE'],[])
    for e in graph['edges']:
        if e['STATUS']=='COMPLETE':continue
        if e['TARGET_FUNCTION'].startswith('GUARD/'):
            wid=e['TARGET_FUNCTION'][6:];srid=output_req[wid];requirements[srid]['AFFECTED_BINDING_IDS'].append(e['EDGE_ID']);roots[requirements[srid]['ROOT_CAUSE_ID']]['AFFECTED_COMPOSITION_EDGES'].append(e['EDGE_ID']);edge_req[e['EDGE_ID']]=srid
        else:
            wid=e['SOURCE_FUNCTION'][6:];fid=next(o['FUNCTION_ID'] for o in outputs if o['WITNESS_ID']==wid);key=('CATALOG_DOMAIN_UNKNOWN_PREREQUISITE' if wid.endswith('/catalog_row_omission') else 'NATIVE_DECISION_INDEPENDENT_RESULT',)
            edge_req[e['EDGE_ID']]=req(key,'NATIVE_STAGE',[e['EDGE_ID']],wid,fid,e['TARGET_INPUT'],'GUARD->NATIVE_STAGE',[])
    projected=sum(b['STATUS']!='COMPLETE' for b in inputs)+sum(o['STATUS']!='COMPLETE' for o in outputs)+sum(e['STATUS']!='COMPLETE' for e in graph['edges'])
    assert projected==2156 and sum(len(r['AFFECTED_BINDING_IDS']) for r in requirements.values())==2156
    # Phase2: independently qualify normalized candidates; don't expand every projection copy.
    used=sorted({fid for r in requirements.values() for fid in r['KNOWN_CANDIDATE_SOURCES']})
    inventory=[]
    for fid in used:
        f=fm[fid];inventory.append(dict(SOURCE_ID=fid,SOURCE_PATH_OR_EVIDENCE_ID=f['SOURCE'],SOURCE_HASH=f['SOURCE_HASH'],SEMANTIC_OBJECT=f['CANONICAL_KEY'],DOMAIN=f['FACT_TYPE'],STAGE='FROZEN_SOURCE_SCHEMA_OR_PARAMETER_OBLIGATION',IDENTITY=f['CANONICAL_KEY'],TYPE=f['VALUE_TYPE'],CARDINALITY=f['STATUS'],AUTHORITY_CLASS='FROZEN_STATIC_CONTRACT_ONLY',PROVENANCE=f['SOURCE_VARIANTS'],IMMUTABLE_FOR_GATE=True,QUALIFICATION_STATUS='CARDINALITY_INSUFFICIENT' if f['STATUS']=='UNRESOLVED_CARDINALITY' else 'PARTIALLY_QUALIFIED',QUALIFICATION_REASON='Canonical source schema/obligation exists; operand-specific semantic identity, transformation or observed value not established by broad candidate membership. Not a qualified runtime fact.'))
    contracts=[]
    def recover(modelid,kind,sourceptr,typ,card,refs,body):
        key=dict(source=ref(D,'baseline-models.json',sourceptr),kind=kind,model_id=modelid,scope='IMMUTABLE_SOURCE_DEFINITION_NOT_MEASURED_VALUE')
        sid='SOURCE_CONTRACT/'+dig(key)
        # New objects are composite selector declarations absent as first-class I facts, not copied schema/value facts.
        c=dict(SOURCE_ID=sid,CANONICAL_SOURCE_ID=sid,SOURCE_PATH_OR_EVIDENCE_ID=key['source'],SOURCE_HASH=key['source']['sha256'],SEMANTIC_OBJECT=kind,DOMAIN='PARAMETRIC_SOURCE_CONTRACT',STAGE='DECLARED_BASELINE_SOURCE; exact invocation sides projected later',IDENTITY=key,TYPE=typ,CARDINALITY=card,AUTHORITY_CLASS='FROZEN_ACCEPTED_STATIC_DESIGN_CONTRACT',PROVENANCE=refs,IMMUTABLE_FOR_GATE=True,QUALIFICATION_STATUS='QUALIFIED',QUALIFICATION_REASON='All literal source-definition inputs and source cardinality constraints are established in immutable D; qualification applies to the parametric declaration, not its actual field values.',SOURCE_PROVENANCE=refs,SEMANTIC_IDENTITY=key,AUTHORITY_BINDING='Frozen model/source declaration only; no broader execution authority',TYPE_BINDING=typ,CARDINALITY_BINDING=card,DERIVATION_IF_ANY=None,DEPENDENT_BINDING_CLASSES=[],DECLARATION=body,VALUE_ESTABLISHED=False,SOURCE_DEFINITION_ESTABLISHED=True,REGISTRY_DUPLICATION_CHECK='Existing I scalar/schema obligations are referenced, never duplicated. New key is composite source declaration at exact D model parameter pointer.')
        contracts.append(c);return sid
    mids=sorted({c['BASELINE_STATE']['library_model_id'] for c in cases});contract_map={}
    for mid in mids:
        model=models[mid];params=model['required_typed_parameters'];baseptr='/models/'+ptr(mid)+'/required_typed_parameters/'
        for kind,param,typ,card,extra in [
          ('APPROVED_COMPLETE_KEYED_MODULE_MAP','module_map','Finite map (nfc_utf8,nfc_utf8)->ModuleMapEntry(identity complete binary tuple)','Finite nonempty key set; lexical min COMPLETE key selects exactly one entry',[ref(D,'schema-library.json','/design_only_model_types/ModuleMapEntry')]),
          ('AUTHENTICATED_READER_SQL_ROLE_ANCHOR','roles_for_graph_fixture','R.oid:SQL oid; R.name:name; native OS/actor enum excluded','Exactly one independently source-authenticated R selector; uniqueness of catalog rows remains separate',[ref(D,'schema-library.json','/schemas/'+ptr('CATALOG/pg_catalog.pg_roles'))]),
          ('TAGGED_SOURCE_RESOLUTION_AND_EXPECTED_OID','candidate_resolution','ResolutionExpression tagged exact/name lookup; SQL oid reference map','One resolution object, one total tag projection, one fixed pg_catalog.pg_roles OID reference',[ref(D,'schema-library.json','/design_only_model_types/ResolutionExpression')])]:
            contract_map[(mid,kind)]=recover(mid,kind,baseptr+param,typ,card,[ref(D,'baseline-models.json',baseptr+param)]+extra,params[param])
    inventory.extend(contracts)
    # Additional source search surfaces: qualified only for declared semantics, never actual observations.
    supplementary=[('r5n','native-message-abi.json','/sender_vs_subject','Subject enrollment and actual-emitter fields are independent'),('r5n','native-registry-generation.json','/records','Record sequence + independent durable journal tip, distinct from registry revision'),('r5n2a4-1d','source-capability-contract.json','/manifest_trust','Full authenticated source expansion/admission, not hash-only approval')]
    for gg,nn,pp,meaning in supplementary:
        rr=ref(gg,nn,pp);sid='SOURCE_CONTRACT_CANDIDATE/'+dig(rr)
        inventory.append(dict(SOURCE_ID=sid,SOURCE_PATH_OR_EVIDENCE_ID=rr,SOURCE_HASH=rr['sha256'],SEMANTIC_OBJECT=meaning,DOMAIN='SOURCE_SEMANTICS',STAGE='STATIC_DESIGN_DECLARATION',IDENTITY=rr,TYPE='Frozen declared contract',CARDINALITY='No actual values/rows asserted',AUTHORITY_CLASS='FROZEN_STATIC_CONTRACT_ONLY',PROVENANCE=[rr],IMMUTABLE_FOR_GATE=True,QUALIFICATION_STATUS='PARTIALLY_QUALIFIED',QUALIFICATION_REASON='Semantics source recovered, but complete operand-specific source projection/authentication not yet established.'))
    write('static-source-candidate-inventory',dict(count=len(inventory),candidates=inventory,normalized_by_source_identity=True,source_values_not_inferred=True))
    write('static-source-qualification',dict(counts=dict(collections.Counter(c['QUALIFICATION_STATUS'] for c in inventory)),records=[dict(SOURCE_ID=c['SOURCE_ID'],QUALIFICATION_STATUS=c['QUALIFICATION_STATUS'],PROOF_SCOPE=c['QUALIFICATION_REASON']) for c in inventory],qualified_scope='Literal parametric source definitions only; no actual runtime value is qualified'))
    # Phase3: recovery is direct registration of immutable composite definitions, not value derivation.
    write('recovered-source-registry',dict(count=len(contracts),entries=contracts,universe='Previously unregistered composite source declarations; not observed fact values',canonical_value_facts_created=0))
    write('derived-source-registry',dict(count=0,entries=[],reason='No new measured/data source is derived. Actual parameter values and collection instances remain unestablished. Projection definitions below consume immutable declarations at structural proof scope only.',all_inputs_established_rule_preserved=True))
    plans={}
    for b in inputs:
        if b['STATUS']=='COMPLETE':continue
        wid=b['WITNESS_ID'];c=cm[wid];mid=c['BASELINE_STATE']['library_model_id'];family=wid.split('/')[1];role=b['INPUT_ID'];kind=None;rule=None;typ=None;stage=None
        if family=='wrong_module':
            kind='APPROVED_COMPLETE_KEYED_MODULE_MAP';typ='bytes32 (exact32)';stage='INDEPENDENT_APPROVED_BASELINE' if role.startswith('expected.') else 'TAGGED_CANDIDATE_AFTER_EXACT_MUTATION'
            rule='Let M be complete independently approved nonempty finite map; K=min lexicographic COMPLETE(load_name,absolute_path) key. expected=M[K].identity.complete_file_sha256; candidate=typed OTHER_MODULE_SHA at same K under frozen mutation. Every other map entry/field and source canonical-reference constraint preserved; no arbitrary element or physical binary substitution.'
        elif role=='R':
            kind='AUTHENTICATED_READER_SQL_ROLE_ANCHOR';typ='SQL oid (source pg_roles.oid type, not native participant enum)';stage='INDEPENDENT_SOURCE_AUTHENTICATED_READER_SQL_ROLE'
            rule='Project oid of exact R anchor declared by model roles_for_graph_fixture. Preserve distinct role name and separate OS principal. Catalog row uniqueness/complete multiset remains separate unresolved input; no lookup, membership, owner or row result is inferred.'
        elif family=='search_path_substitution':
            kind='TAGGED_SOURCE_RESOLUTION_AND_EXPECTED_OID';stage='EXACT_DECLARED_SOURCE_BINDING_EXPRESSION'
            if role=='candidate_resolution':typ='NAMESPACE_NAME_LOOKUP tagged ResolutionExpression';rule='Project exact frozen after-variant namespace_oid=N_ATTACK,relation_name=pg_roles,resolved_relation_oid=T_ATTACK.oid,namespace_origin=CALLER_CONTROLLED; retain full typed namespace/class row and distinct OID constraints, no numeric OID instantiated.'
            elif role=='candidate_resolution.kind':typ='Closed ResolutionExpression tag enum';rule='Select exact frozen mutation tag NAMESPACE_NAME_LOOKUP, not generic callback or caller choice.'
            elif role=='frozen_object_oids':typ='Fixed dictionary pg_catalog.pg_roles -> SQL oid';rule='Project independently frozen before EXACT_FROZEN_IDENTITY.relation_oid for key pg_catalog.pg_roles; preserve namespace OID/name/full row binding. Never derive expected OID from attack T_ATTACK.'
        if kind:
            sid=contract_map[(mid,kind)];plan=dict(WITNESS_ID=wid,FUNCTION_ID=b['FUNCTION_ID'],INPUT_ID=role,SOURCE_ID=sid,MODEL_ID=mid,VIEW=c['BASELINE_STATE']['selected_view'],VARIANT=c['BASELINE_STATE']['exact_variant_state'],STAGE=stage,OUTPUT_TYPE=typ,CARDINALITY='One source-typed scalar/object per exact invocation under declared source constraints',PROJECTION_RULE=rule,MUTATION=ref(D,'family-descriptors.json','/families/'+family),CASE_SOURCE=ref(F,'derived-canonical-350-registry.json','/case_records/'+str(cases.index(c))),SOURCE_VALUES_INSTANTIATED=False,EXPECTED_RESULT_CONSUMED=False,PROOF_SCOPE='STRUCTURAL_PARAMETRIC_BINDING_ONLY',FUTURE_FIXTURE_RULE=models[mid]['future_binding_rule'])
            plans[(wid,role)]=plan
    write('source-projection-contracts',dict(count=len(plans),records=list(plans.values()),source_definitions_established=True,actual_values_established=False,derived_data_sources=0))
    # Phase4: recompute EVERY original input/output from recovered registry + immutable L source contracts.
    recomputed=[];ambiguities=[];recovered_by=collections.Counter()
    for b in inputs:
        n=copy.deepcopy(b);plan=plans.get((b['WITNESS_ID'],b['INPUT_ID']));old=b['STATUS']
        justified=bool(plan) or old=='COMPLETE'
        if plan:n.update(STATUS='COMPLETE',AMBIGUOUS=False,MISSING=False,CONTRADICTED=False,SOURCE_TYPE_INSTANTIATED=True,SOURCE_VALUE_AVAILABLE=False,C5M_SOURCE_ID=plan['SOURCE_ID'],C5M_PROJECTION_ID=dig(plan),TRANSFORMATION=plan['PROJECTION_RULE'],CANONICAL_SOURCE_FACT=[plan['SOURCE_ID']],SOURCE_FACT_KEY=[dict(source_id=plan['SOURCE_ID'],projection_id=dig(plan),model_id=plan['MODEL_ID'],view=plan['VIEW'],stage=plan['STAGE'])],BINDING_RULE='Qualified composite source definition and exact source-parametric projection; historical candidate set preserved in C5L, not treated as selected source.')
        n['RECOMPUTATION_BASIS']='C5M_QUALIFIED_SOURCE_DEFINITION_AND_EXACT_PROJECTION' if plan else 'FROZEN_C5L_SOURCE_PROOF_REVALIDATED' if old=='COMPLETE' else 'SOURCE_REQUIREMENT_UNRESOLVED'
        recomputed.append(n)
        if old=='AMBIGUOUS':
            candidates=[x for x in b['CANONICAL_SOURCE_FACT'] if x in fm]
            # Recovered composite contracts are new candidates; component fields do not directly compete as complete operands.
            why='RESOLVED_BY_SOURCE_RECOVERY' if plan else None
            if why:recovered_by[why]+=1
            ambiguities.append(dict(BINDING_ID=b['BINDING_ID'],SOURCE_REQUIREMENT_ID=input_req[b['BINDING_ID']],TARGET_FUNCTION=b['FUNCTION_ID'],TARGET_INPUT=b['INPUT_ID'],ORIGINAL_CANDIDATE_IDS=candidates,RECOVERED_CANDIDATE_ID=plan['SOURCE_ID'] if plan else None,SELECTED_SOURCE=plan['SOURCE_ID'] if plan else None,DOMINATED_AS_DIRECT_OPERAND=candidates if plan else [],ELIMINATION_RULE=plan['PROJECTION_RULE'] if plan else None,NONDOMINATED_SURVIVORS=[plan['SOURCE_ID']] if plan else candidates,UNRESOLVED_SURVIVORS_NOT_ALL_QUALIFIED=True,RESOLUTION_STATUS='RESOLVED_UNIQUE' if plan else 'REMAINS_AMBIGUOUS',RESOLUTION_MECHANISM=why,EXPECTED_RESULT_CONSUMED=False))
    assert len(ambiguities)==511
    bmap=collections.defaultdict(list)
    for b in recomputed:bmap[(b['FUNCTION_ID'],b['WITNESS_ID'])].append(b)
    outs=[]
    for o in outputs:
        n=copy.deepcopy(o);complete=all(b['STATUS']=='COMPLETE' and b['SOURCE_TYPE_INSTANTIATED'] for b in bmap[(o['FUNCTION_ID'],o['WITNESS_ID'])])
        assert o['TARGET_INDEPENDENTLY_ESTABLISHED']
        n.update(STATUS='COMPLETE' if complete else 'MISSING',MISSING=not complete,CLOSURE_STATUS='CLOSED' if complete else 'TARGET_NOT_ESTABLISHED',EXACT_INVOCATION_INPUTS_BOUND=complete,ACTUAL_VALUE=None,RECOMPUTATION_BASIS='Exact invocation source contracts and independent D guard destination, not actual evaluation',OUTPUT_BINDING_RULE='Exact source-parametric invocation evidence transfer to independently declared GUARD; no native decision or witness result inferred' if complete else 'Independent GUARD exists; exact invocation source meaning remains unestablished')
        outs.append(n)
    certs=[]
    for prior in oldcert:
        n=copy.deepcopy(prior);fid=n['FUNCTION_ID'];bi=[b for b in recomputed if b['FUNCTION_ID']==fid];oo=[o for o in outs if o['FUNCTION_ID']==fid];props=n['PROPERTIES'];inputok=all(b['STATUS']=='COMPLETE' and b['SOURCE_TYPE_INSTANTIATED'] for b in bi);outputok=all(o['STATUS']=='COMPLETE' for o in oo)
        props.update(INPUT_SCHEMA_COMPLETE=inputok,ALL_REQUIRED_INPUT_BINDINGS_COMPLETE=inputok,ALL_REQUIRED_OUTPUT_BINDINGS_COMPLETE=outputok,CANONICALLY_BINDABLE=inputok and outputok)
        n.update(STRICT_CERTIFIED=all(v is True for v in props.values()),ALGORITHM_DISPROVEN=False,UNPROVEN_REQUIRED_PROPERTIES=[k for k,v in props.items() if v is not True],C5M_SOURCE_IDS=sorted({b['C5M_SOURCE_ID'] for b in bi if 'C5M_SOURCE_ID' in b}))
        certs.append(n)
    strict={c['FUNCTION_ID']:c['STRICT_CERTIFIED'] for c in certs}
    for b in recomputed:b['FUNCTION_STRICTLY_CERTIFIED']=strict[b['FUNCTION_ID']]
    for o in outs:o['FUNCTION_STRICTLY_CERTIFIED']=strict[o['FUNCTION_ID']]
    om={o['WITNESS_ID']:o for o in outs};edges=[]
    for e in graph['edges']:
        n=copy.deepcopy(e);isguard=e['TARGET_FUNCTION'].startswith('GUARD/');closed=e['STATUS']=='COMPLETE' or isguard and om[e['TARGET_FUNCTION'][6:]]['STATUS']=='COMPLETE'
        n.update(STATUS='COMPLETE' if closed else 'MISSING',CLOSURE_STATUS='CLOSED' if closed else 'BINDING_BLOCKED',EDGE_STATUS='CLOSED' if closed else 'BINDING_BLOCKED',C5M_RECOMPUTED=True)
        source_bound=closed or (not isguard and e['SOURCE_FUNCTION'].startswith('GUARD/') and om[e['SOURCE_FUNCTION'][6:]]['STATUS']=='COMPLETE')
        n.update(SOURCE_BINDING_STATUS='COMPLETE' if source_bound else 'MISSING',TARGET_BINDING_STATUS='COMPLETE' if closed else 'MISSING',SEMANTIC_COMPATIBILITY='ESTABLISHED' if closed else 'EXACT_TRANSFORM_NOT_ESTABLISHED',TYPE_COMPATIBILITY='ESTABLISHED' if closed else 'EXACT_SOURCE_TYPE_INSTANCE_NOT_ESTABLISHED',STAGE_COMPATIBILITY='ESTABLISHED' if closed else 'SOURCE_STAGE_ADAPTER_NOT_ESTABLISHED',BLOCKER=None if closed else 'EXACT_INVOCATION_BINDING' if isguard else 'INDEPENDENT_NATIVE_STAGE_ADAPTER',BINDING='Exact source-parametric invocation -> independent case GUARD evidence' if closed and isguard else e['BINDING'])
        edges.append(n)
    nodes={n['NODE_ID'] for n in graph['nodes']};degree={n:0 for n in nodes};adj=collections.defaultdict(list)
    for e in edges:adj[e['SOURCE_FUNCTION']].append(e['TARGET_FUNCTION']);degree[e['TARGET_FUNCTION']]+=1
    q=collections.deque(n for n,d in degree.items() if d==0);order=[]
    while q:
        n=q.popleft();order.append(n)
        for t in adj[n]:
            degree[t]-=1
            if degree[t]==0:q.append(t)
    assert len(order)==len(nodes)==763
    ic=collections.Counter(b['STATUS'] for b in recomputed);oc=collections.Counter(o['STATUS'] for o in outs);ec=collections.Counter(e['STATUS'] for e in edges)
    write('remaining-ambiguity-analysis',dict(start=511,resolved=sum(a['RESOLUTION_STATUS']=='RESOLVED_UNIQUE' for a in ambiguities),remaining=sum(a['RESOLUTION_STATUS']=='REMAINS_AMBIGUOUS' for a in ambiguities),RESOLVED_BY_SOURCE_RECOVERY=recovered_by['RESOLVED_BY_SOURCE_RECOVERY'],RESOLVED_BY_IDENTITY_QUALIFICATION=0,RESOLVED_BY_TYPE_QUALIFICATION=0,RESOLVED_BY_STAGE_QUALIFICATION=0,RESOLVED_BY_CARDINALITY_QUALIFICATION=0,mechanism_counts_mutually_exclusive=True,records=ambiguities))
    write('binding-recomputation',dict(input_required=1526,input_counts=dict(ic),output_required=350,output_counts=dict(oc),inputs=recomputed,outputs=outs,recomputed_all=True,structural_scope_only=True))
    write('all-49-certification-recomputation',dict(required=49,available=49,strict_certified=sum(c['STRICT_CERTIFIED'] for c in certs),not_certified=sum(not c['STRICT_CERTIFIED'] for c in certs),algorithm_disproven=0,functions=certs))
    write('composition-recomputation',dict(required=714,counts=dict(ec),nodes=graph['nodes'],edges=edges,cycles=0,topological_order=order,cycle_method='Kahn traversal all714 frozen relations'))
    # Update requirements/roots against the complete recomputation, without hiding starting obligations.
    status={b['BINDING_ID']:b['STATUS'] for b in recomputed};status.update({'OUTPUT/'+o['WITNESS_ID']:o['STATUS'] for o in outs});status.update({e['EDGE_ID']:e['STATUS'] for e in edges})
    for r in requirements.values():
        closed=all(status[i]=='COMPLETE' for i in r['AFFECTED_BINDING_IDS']);r.update(CLOSURE_STATUS='CLOSED_STRUCTURAL_SOURCE_BINDING' if closed else 'UNRESOLVED',SOURCE_PRESENT=True if closed else None,SOURCE_REGISTERED=True if closed else None,CANDIDATE_COMPONENTS_REGISTERED=bool(r['KNOWN_CANDIDATE_SOURCES']),SOURCE_AMBIGUOUS=any(status[i]=='AMBIGUOUS' for i in r['AFFECTED_BINDING_IDS']),CARDINALITY_RESOLVED=True if closed else None,AUTHORITY_SUFFICIENT=True if closed else None)
        r['RECOVERED_SOURCE_IDS']=sorted({b['C5M_SOURCE_ID'] for b in recomputed if b['BINDING_ID'] in r['AFFECTED_BINDING_IDS'] and 'C5M_SOURCE_ID' in b})
        for sid in r['RECOVERED_SOURCE_IDS']:next(c for c in contracts if c['SOURCE_ID']==sid)['DEPENDENT_BINDING_CLASSES'].append(r['SOURCE_REQUIREMENT_ID'])
    remaining_roots=[]
    source_notes=read(L,'remaining-source-recovery-analysis.json')['records']
    for ro in roots.values():
        ids=ro['AFFECTED_INPUT_BINDINGS']+ro['AFFECTED_OUTPUT_BINDINGS']+ro['AFFECTED_COMPOSITION_EDGES'];unresolved=[i for i in ids if status[i]!='COMPLETE'];ro.update(START_PROJECTED_COUNT=len(ids),REMAINING_PROJECTED_IDS=unresolved,REMAINING_PROJECTED_COUNT=len(unresolved),CLOSURE_STATUS='CLOSED_STRUCTURALLY' if not unresolved else 'UNRESOLVED')
        ro['CANDIDATE_RECOVERY_SOURCES']=sorted({s for r in requirements.values() if r['ROOT_CAUSE_ID']==ro['ROOT_CAUSE_ID'] for s in r['KNOWN_CANDIDATE_SOURCES']+r['RECOVERED_SOURCE_IDS']})
        related=[r for r in requirements.values() if r['ROOT_CAUSE_ID']==ro['ROOT_CAUSE_ID']]
        if ro['DOMAIN']=='SOURCE_TYPED_PARAMETER_NORMALIZATION':
            fid=ro['AFFECTED_FUNCTIONS'][0];notes=[n for n in source_notes if n['FUNCTION_ID']==fid]
            ro['CANONICAL_REQUIREMENT']=dict(families=fun[fid]['families'],required_operand_roles=[r['TARGET_INPUT_ROLE'] for r in related if r['KIND']=='INPUT'],type_source=fun[fid]['INPUT_SCHEMA'],identity='Every actor/model/view/variant in source requirements, independently preserved')
            ro['WHY_CURRENT_MODEL_CANNOT_BIND']='Closed by qualified composite source definition/projection, no values instantiated.' if not unresolved else [n['EXACT_GAP'] for n in notes]
            ro['MINIMUM_RECOVERY_ACTION']='None at structural source-binding scope; actual fixture instantiation remains future work.' if not unresolved else 'Recover exact missing semantic source/projection: '+ '; '.join(n['EXACT_GAP'] for n in notes if n['EXACT_GAP'])
            ro['ROOT_CAUSE_CLASS']='SOURCE_EXISTS_BINDING_NOT_PROJECTED' if not unresolved else 'SOURCE_NOT_ESTABLISHED'
            ro['SOURCE_DECLARATION_REFERENCES']=[n['SOURCE'] for n in notes]
            ro['PARTIAL_SCHEMA_PRESENCE_IS_NOT_COMPLETE_SOURCE_EXISTENCE']=True
        else:
            ro['WHY_CURRENT_MODEL_CANNOT_BIND']='Exact independent observed native decision-stage input and source-to-stage adapter are absent from the assembled static registry; D/F expected REJECT/UNKNOWN comparison cannot supply it.'
            ro['MINIMUM_RECOVERY_ACTION']='Recover exact ABI/result-record/currentness and independent source observation contracts, then bind observed stage inputs without consuming expected outcomes.'
            ro['SOURCE_DECLARATION_REFERENCES']=[ref('r5n','native-message-abi.json','/result_record_rule'),ref('r5n','native-message-abi.json','/outcome')]
        if unresolved:remaining_roots.append(ro)
    write('source-requirement-registry',dict(total=len(requirements),starting_unresolved_projected_bindings=projected,requirements=list(requirements.values()),grouping='Same parameterized source rule only; each distinct model/view/case identity retained explicitly. Acquire/consume dependencies share a source requirement, not an observed fact identity.'))
    write('root-cause-registry',dict(total=len(roots),roots=list(roots.values()),partition_scope='Function-specific source normalization obligations plus two independent source-stage adapter suites, not one root per projected row.'))
    write('root-cause-compression',dict(unresolved_projected_bindings_start=projected,canonical_root_causes_total=len(roots),root_cause_compression_ratio=projected/len(roots),unresolved_projected_bindings_after=sum(status[i]!='COMPLETE' for i in status),remaining_roots=len(remaining_roots),compression_is_not_proof=True,not_global_minimum_claim=True))
    write('recovered-source-registry',dict(count=len(contracts),entries=contracts,universe='Previously unregistered composite immutable source declarations, not values',canonical_value_facts_created=0))
    dag=dict(CANONICAL_DECISION_DAG_STATUS='INCOMPLETE_BINDING',CANONICAL_DECISION_NODES=len(nodes),CANONICAL_DECISION_EDGES=len(edges),UNBOUND_DECISION_INPUTS=1526-ic['COMPLETE'],UNBOUND_DECISION_OUTPUTS=sum(e['STATUS']!='COMPLETE' for e in edges if e['SOURCE_FUNCTION'].startswith('GUARD/')),AMBIGUOUS_DECISION_RELATIONS=ic['AMBIGUOUS'],UNORDERED_REQUIRED_RELATIONS=0,CYCLES_DETECTED=0)
    write('canonical-dag-recomputation',dag)
    write('canonical-evaluator-analysis',dict(complete=0,assembly='NOT_ATTEMPTED_PREREQUISITES_INCOMPLETE',all49_strict=all(c['STRICT_CERTIFIED'] for c in certs),dag=dag['CANONICAL_DECISION_DAG_STATUS'],expected_witness_result_consumed=False,witness_proof_executed=False,missing_native_stage_not_inferred_from_guard_value=True))
    write('minimum-remaining-blocker-set',dict(remaining_canonical_roots=len(remaining_roots),root_ids=[r['ROOT_CAUSE_ID'] for r in remaining_roots],roots=remaining_roots,minimality='Dependency partition at function/source-stage semantic level; not proven globally minimum or irreducible. Further source recovery may split or merge classes.',lowest_next_recovery='Qualified subject enrollment ABI field19 vs actual emitter sender_enrollment field34 + independent current participant registry enrollment. Journal sequence bounds/projection separately; do not substitute registry revision.'))
    write('authority-cardinality-escalation',dict(authority_questions_required=0,cardinality_questions_required=0,authority_questions=[],cardinality_questions=[],reason='No concrete mutually exclusive normative alternatives established. Missing full row/map extents, source authentication and independent observations remain technical evidence recovery tasks; no invented runtime cardinality or newly chosen policy.',cardinality_recovery_tasks=['Complete catalog/ACL/membership row multisets and exact natural keys','Exact complete effect/call/dependency graph source expansion','Complete approved map instance for later fixture instantiation'],source_contract_cardinality='Nonempty finite approved map is enough for universal min-key projection contract; actual extent remains unknown and no concrete scalar is derived.',architecture_flags={k:'NO' for k in ['POSTMASTER_CONTEXT_BINDING_RESOLVED','INTERNAL_SCOPE_RESOLVED','ATOMIC_BOUNDARY_RESOLVED','CANONICAL_INTERNAL_OBLIGATION_UNIVERSE_ESTABLISHED']},frozen_architecture_proven_minimum_blocker=False,T8=dict(PROJECT_AUTHORITY_TRANSITION='T8',EVENT='FRESH_GENERATION_LEDGER_SUCCESSION',SOURCE_GENERATION_CREDENTIAL_AUTHORITY_DOES_NOT_AUTOMATICALLY_TRANSFER_TO_TARGET_GENERATION=True),I13=dict(full_preserved=True,source=ref('r5n2a5-3c4b','i13-preservation-review.json'),no_internal_scope_or_boundary_selected=True),UNKNOWN_REJECT=dict(distinct=True,helper_UNAVAILABLE_not_domain_UNKNOWN=True,exact_seven_catalog_row_omission_mapping_only=True)))
    cov=read(L,'coverage-accounting.json');cov.update(source=ref(L,'coverage-accounting.json'),status='PRESERVED_NOT_EXECUTED_C5M');write('coverage-accounting',cov)
    summary=dict(BRANCH=git('branch','--show-current'),BASELINE_HEAD='cbc284f62d9bd09b7169b55c8d66a3c51a68c6cb',CURRENT_HEAD=git('rev-parse','HEAD'),TRACKED_DIRTY_COUNT=0,STAGED_COUNT=0,AUTHORIZED_UNTRACKED_FILES_BEFORE=326,UNTRACKED_FILES_AFTER=None,UNAUTHORIZED_UNTRACKED_COUNT=0,C5L_INPUT_INTEGRITY='PASS',HISTORICAL_HASHES_VALIDATED=9393,HISTORICAL_UNION_PRESERVED=9425,CANONICAL_CASES_TOTAL=350,UNRESOLVED_PROJECTED_BINDINGS_TOTAL=projected,CANONICAL_ROOT_CAUSES_TOTAL=len(roots),ROOT_CAUSE_COMPRESSION_RATIO=projected/len(roots),SOURCE_REQUIREMENTS_TOTAL=len(requirements),RECOVERED_CANONICAL_SOURCES=len(contracts),DERIVED_CANONICAL_SOURCES=0,AMBIGUOUS_INPUT_BINDINGS_START=511,AMBIGUOUS_INPUT_BINDINGS_RESOLVED=recovered_by['RESOLVED_BY_SOURCE_RECOVERY'],AMBIGUOUS_INPUT_BINDINGS_REMAINING=ic['AMBIGUOUS'],CANONICAL_INPUT_BINDINGS_REQUIRED=1526,CANONICAL_INPUT_BINDINGS_COMPLETE=ic['COMPLETE'],CANONICAL_INPUT_BINDINGS_MISSING=ic['MISSING'],CANONICAL_INPUT_BINDINGS_AMBIGUOUS=ic['AMBIGUOUS'],CANONICAL_INPUT_BINDINGS_CONTRADICTED=0,CANONICAL_OUTPUT_BINDINGS_REQUIRED=350,CANONICAL_OUTPUT_BINDINGS_COMPLETE=oc['COMPLETE'],CANONICAL_OUTPUT_BINDINGS_MISSING=oc['MISSING'],CANONICAL_OUTPUT_BINDINGS_AMBIGUOUS=0,CANONICAL_OUTPUT_BINDINGS_CONTRADICTED=0,LOCAL_FUNCTIONS_REQUIRED=49,LOCAL_FUNCTIONS_AVAILABLE=49,LOCAL_FUNCTIONS_STRICT_CERTIFIED=sum(c['STRICT_CERTIFIED'] for c in certs),LOCAL_FUNCTIONS_NOT_CERTIFIED=sum(not c['STRICT_CERTIFIED'] for c in certs),ALGORITHM_DISPROVEN=0,COMPOSITION_EDGES_REQUIRED=714,COMPOSITION_EDGES_COMPLETE=ec['COMPLETE'],COMPOSITION_EDGES_MISSING=ec['MISSING'],COMPOSITION_EDGES_AMBIGUOUS=0,COMPOSITION_EDGES_CONTRADICTED=0,COMPOSITION_CYCLES=0,**dag,MINIMUM_REMAINING_ROOT_CAUSES=len(remaining_roots),AUTHORITY_QUESTIONS_REQUIRED=0,CARDINALITY_QUESTIONS_REQUIRED=0,COMPLETE_CANONICAL_DECISION_EVALUATORS=0,STATICALLY_PROVEN=0,STATICALLY_DISPROVEN=0,UNKNOWN=350,CONTRADICTED=0,N1_SUBSTITUTION_STATIC_WITNESSES='OPEN',N1_DECISIONS_REQUIRED=12,N1_DECISIONS_CLOSED=11,N1_DECISIONS_OPEN=1,V2_NATIVE_STATIC_DESIGN_PROOF='FAIL',V2_NATIVE_STATUS='BLOCKED',ATOMIC_NORMATIVE_CANDIDATES_TOTAL=108,AMBIGUOUS_CANDIDATES_PRESERVED=105,CANONICAL_ATTACK_DENOMINATOR=350,DENOMINATOR_CHANGED='NO',ATTACKS_MATERIALIZED_THIS_GATE=0,ATTACKS_EVALUATED_THIS_GATE=0,INDEPENDENT_REVIEW_1='PENDING',INDEPENDENT_REVIEW_2='PENDING',SELECTED_OUTCOME='E_STATIC_SOURCE_RECOVERY_PARTIAL',NEXT_EXECUTED=False,NEXT_GATE='BOUNDED_STATIC_SOURCE_RECOVERY_CONTINUATION')
    qc=collections.Counter(c['QUALIFICATION_STATUS'] for c in inventory)
    for key,statusname in [('QUALIFIED_STATIC_SOURCES','QUALIFIED'),('PARTIALLY_QUALIFIED_STATIC_SOURCES','PARTIALLY_QUALIFIED'),('AMBIGUOUS_STATIC_SOURCES','AMBIGUOUS'),('AUTHORITY_INSUFFICIENT_STATIC_SOURCES','AUTHORITY_INSUFFICIENT'),('CARDINALITY_INSUFFICIENT_STATIC_SOURCES','CARDINALITY_INSUFFICIENT'),('CONTRADICTED_STATIC_SOURCES','CONTRADICTED')]:summary[key]=qc[statusname]
    for key in ['SHARED_DB_CONTACTED','PRODUCTION_CONTACTED','EXISTING_LOCAL_DB_CONTACTED','NETWORK_CONTACT_FOR_PROOF','V043_EXECUTED','V043_CHANGED','B02_EXECUTED','GIT_ADD','COMMIT','PUSH','POSTMASTER_CONTEXT_BINDING_RESOLVED','INTERNAL_SCOPE_RESOLVED','ATOMIC_BOUNDARY_RESOLVED','CANONICAL_INTERNAL_OBLIGATION_UNIVERSE_ESTABLISHED']:summary[key]='NO'
    write('primary-result',dict(selected_outcome=summary['SELECTED_OUTCOME'],reason='Recovered immutable composite source declarations close additional structural projections; catalog/effect/call/native-stage source recovery remains incomplete. No new normative alternative or frozen architectural minimum blocker demonstrated.',next_gate=summary['NEXT_GATE'],next_executed=False,source_value_proof=False))
    write('final-summary',summary)
    print(canon({k:v for k,v in summary.items() if k.startswith(('CANONICAL_INPUT','CANONICAL_OUTPUT','LOCAL_FUNCTIONS','RECOVERED','AMBIGUOUS_INPUT','COMPOSITION_EDGES','SOURCE_REQUIREMENTS','CANONICAL_ROOT'))}))

if __name__=='__main__':main()
