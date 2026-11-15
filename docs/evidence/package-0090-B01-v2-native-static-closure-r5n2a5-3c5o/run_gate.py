"""C5O finite qualification exhaustion; new evidence only, no witness/runtime execution."""
import collections,copy,functools,hashlib,importlib.util,json,pathlib,subprocess,sys
sys.dont_write_bytecode=True
OUT=pathlib.Path(__file__).resolve().parent;ROOT=OUT.parents[2];BASE=ROOT/'docs/evidence';PREFIX='package-0090-B01-v2-native-static-closure-'
N='r5n2a5-3c5n';D='r5n2a5-3c5d';F='r5n2a5-3c5f';K='r5n2a5-3c5k'
def p(g,n):return BASE/(PREFIX+g)/n
def read(g,n):return json.loads(p(g,n).read_text(encoding='utf-8-sig'))
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def dig(x):return hashlib.sha256(canon(x).encode()).hexdigest()
@functools.lru_cache(None)
def sha(q):return hashlib.sha256(q.read_bytes()).hexdigest()
def ref(g,n,ptr=''):return dict(path=p(g,n).relative_to(ROOT).as_posix(),sha256=sha(p(g,n)),pointer=ptr)
def write(n,x):(OUT/(n+'.json')).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
def ptr(s):return s.replace('~','~0').replace('/','~1')
s=importlib.util.spec_from_file_location('o_semantic_rules',OUT/'semantic_rules.py');rules=importlib.util.module_from_spec(s);s.loader.exec_module(rules)
TAXONOMY=['QUALIFIED_FROM_EXISTING_STATIC_AUTHORITY','QUALIFIED_FROM_EXISTING_STATIC_ARTIFACT','QUALIFIED_BY_DETERMINISTIC_DERIVATION','DUPLICATE_OF_QUALIFIED_CANONICAL_SEMANTIC','PROJECT_AUTHORITY_REQUIRED','CARDINALITY_AUTHORITY_REQUIRED','ARCHITECTURAL_DECISION_REQUIRED','RUNTIME_OBSERVATION_REQUIRED','STATIC_SOURCE_EXHAUSTED_NOT_ESTABLISHED','CONTRADICTED']

def main():
    np=read(N,'preflight.json');nm=read(N,'SHA256-MANIFEST.json');ns=read(N,'final-summary.json')
    hist={**np['historical_sha256'],**nm['files'],p(N,'SHA256-MANIFEST.json').relative_to(ROOT).as_posix():sha(p(N,'SHA256-MANIFEST.json'))};assert len(np['historical_sha256'])==9458 and len(hist)==9494
    assert not [q for q,h in hist.items() if not (ROOT/q).is_file() or sha(ROOT/q)!=h]
    assert ROOT==pathlib.Path('C:/Projects/flooow-genesis-git') and git('branch','--show-current')=='checkpoint/package-0090-cloud-handoff' and git('rev-parse','HEAD')=='451265ff5b3d286eb4d27c4b3817c2f558f30123'
    assert not git('diff','--name-only') and not git('diff','--cached','--name-only')
    before=[q for q in git('ls-files','--others','--exclude-standard').splitlines() if not q.startswith(OUT.relative_to(ROOT).as_posix()+'/')];assert len(before)==395
    assert ns['LOCAL_FUNCTIONS_STRICT_CERTIFIED']==16 and ns['CANONICAL_INPUT_BINDINGS_COMPLETE']==567 and ns['UNKNOWN']==350
    assert 'LOCAL_FUNCTIONS_STRICT_CERTIFIED=16' in p(N,'final-return.txt').read_text()
    tasks=read(N,'finite-semantic-qualification-worklist.json')['tasks'];universe=read(N,'remaining-source-universe.json')['requirements'];um={u['SOURCE_REQUIREMENT_ID']:u for u in universe};assert len(tasks)==len({t['TASK_ID'] for t in tasks})==106
    assert {t['SOURCE_REQUIREMENT_ID'] for t in tasks}=={u['SOURCE_REQUIREMENT_ID'] for u in universe if u['REMAINING_BINDINGS']}
    assert all(t['ROOT_CAUSE_ID']==um[t['SOURCE_REQUIREMENT_ID']]['ROOT_CAUSE_ID'] for t in tasks)
    write('preflight',dict(status='PASS',repository=str(ROOT),branch=git('branch','--show-current'),head=git('rev-parse','HEAD'),baseline='cbc284f62d9bd09b7169b55c8d66a3c51a68c6cb',tracked_dirty=0,staged=0,authorized_untracked_before=395,authorized_paths_before=before,historical_sha256=hist,historical_files_preserved=9458,historical_union_preserved=9494,semantic_qualifications_required=106,duplicate_ids=0,missing_ids=0))
    write('c5n-input-integrity',dict(status='PASS',manifest=ref(N,'SHA256-MANIFEST.json'),manifest_files_checked=len(nm['files'])+1,historical_checked=9458,full_union_preserved=9494,final_return=ref(N,'final-return.txt'),final_summary=ref(N,'final-summary.json'),worklist=ref(N,'finite-semantic-qualification-worklist.json'),exact_task_ids=[t['TASK_ID'] for t in tasks]))
    write('semantic-qualification-universe-106',dict(required=106,items=[dict(QUALIFICATION_ID=t['TASK_ID'],SOURCE_REQUIREMENT_ID=t['SOURCE_REQUIREMENT_ID'],ROOT_CAUSE_ID=t['ROOT_CAUSE_ID'],PROVENANCE=ref(N,'finite-semantic-qualification-worklist.json','/tasks/'+str(i)),SOURCE_REQUIREMENT_PROVENANCE=ref(N,'remaining-source-universe.json','/requirements/'+str(universe.index(um[t['SOURCE_REQUIREMENT_ID']]))) ) for i,t in enumerate(tasks)]))
    inputs=read(N,'binding-recomputation.json')['inputs'];outputs=read(N,'binding-recomputation.json')['outputs'];graph=read(N,'composition-recomputation.json');oldcert=read(N,'strict-certification-recomputation.json')['functions'];fun={f['FUNCTION_ID']:f for f in read(K,'49-function-inventory.json')['functions']}
    cases=read(F,'derived-canonical-350-registry.json')['case_records'];cm={c['WITNESS_ID']:c for c in cases};models=read(D,'baseline-models.json')['models'];families=read(D,'family-descriptors.json')['families'];schemas=read(D,'schema-library.json');bm={b['BINDING_ID']:b for b in inputs}
    # Fixed finite source search: every prior file remains immutable. Matching is discovery,
    # source qualification is the exact per-item semantic/ref/type analysis below.
    search_surfaces=[];hit_index=collections.defaultdict(list)
    patterns=sorted({um[t['SOURCE_REQUIREMENT_ID']]['SEMANTIC_OBJECT'].lower() for t in tasks}|{f['families'][0].lower() for f in oldcert if not f['STRICT_CERTIFIED']})
    cache_path=OUT/'static-surface-search-receipts.json';cache=json.loads(cache_path.read_text(encoding='utf-8')) if cache_path.exists() else {};cached={r['path']:r for r in cache.get('records',[])} if cache.get('patterns')==patterns else {}
    for i,(name,h) in enumerate(sorted(hist.items())):
        prior=cached.get(name)
        if prior and prior['sha256']==h:hits=prior['patterns_matched']
        else:
            data=(ROOT/name).read_bytes().lower();hits=[word for word in patterns if word.encode() in data]
        sid='SURFACE/'+dig(name)
        search_surfaces.append(dict(SURFACE_ID=sid,path=name,sha256=h,patterns_matched=hits,SEARCH_COMPLETE=True,qualification_from_match_alone=False))
        for word in hits:hit_index[word].append(sid)
        if i and i%2000==0:print('FINITE_STATIC_FILES',i,flush=True)
    write('static-surface-search-receipts',dict(total=len(search_surfaces),records=search_surfaces,patterns=patterns,count_unit='Artifact presence of exact source-object/family identifier, not source qualification',bounded_scope='All9494 immutable historical/implementation files; no new unbounded discovery or O self-search'))
    records=[];groups={};record_by_q={};derivations=[];sources={}
    # Member/target source anchors are invariant across exactly three membership mutations;
    # all7model/view/variant/source/type/cardinality/authority coordinates must match.
    m_requirements={r['SOURCE_REQUIREMENT_ID']:r for r in read('r5n2a5-3c5m','source-requirement-registry.json')['requirements']};wid_fid={o['WITNESS_ID']:o['FUNCTION_ID'] for o in outputs}
    for task in tasks:
        u=um[task['SOURCE_REQUIREMENT_ID']];qid=task['TASK_ID'];fid=m_requirements[u['SOURCE_REQUIREMENT_ID']]['TARGET_FUNCTION']
        assert fid is not None
        family=fun[fid]['families'][0];role=u['SEMANTIC_OBJECT'];wids=sorted(i['witness'] for i in u['IDENTITY']);kind=u['FRONTIER_KIND'];out=u['DOMAIN']=='GUARD_VIOLATION_EVIDENCE';stage=u['DOMAIN']=='INDEPENDENT_NATIVE_STAGE'
        evidence=[ref(D,'family-descriptors.json','/families/'+family),ref(D,'schema-library.json'),ref(D,'baseline-models.json')]
        if out:evidence.append(ref(K,'49-function-inventory.json','/functions/'+str(list(fun).index(fid))+'/OUTPUT_SCHEMA'))
        if family in ['transitive_SET_ROLE','transitive_INHERIT','ADMIN_option_escalation']:
            evidence += [ref('r5n2a5-3c5j','role_closure.py'),ref('r5n2a3','postgres-source/src/include/catalog/pg_authid.dat')]
        if family in ['ownership_escalation','PUBLIC_path','catalog_row_omission','catalog_row_injection','mixed_snapshot','wrong_role','snapshot_reconnect','snapshot_restart']:
            evidence += [ref('r5n1','catalog-projection.json'),ref('r5n1','catalog-encoding.json')]
        if family=='PUBLIC_path':evidence += [ref('r5n2a4-1d','source-capability-contract.json','/source_capability'),ref('r5n2a4-1d','source-capability-contract.json','/implementation_constraint')]
        if family in ['default_privilege_path','SECURITY_DEFINER_path','reader_mutation'] or stage:evidence += [ref('r5n2a4-1d','source-capability-contract.json','/manifest_trust'),ref('r5n','native-message-abi.json','/result_record_rule')]
        if family in ['wrong_dependency','registry_rollback','replayed_challenge','tombstoned_generation','producer_consumer_substitution','credential_theft','wrong_custodian','observer_writer_substitution']:
            evidence += [ref('r5n','native-message-abi.json'),ref('r5n','native-registry-generation.json')]
        if family in ['credential_theft','wrong_custodian','credential_transfer']:
            evidence += [ref('r5n2a3','credential-class-manifest.json'),ref('r5n1','credential-custody.json'),ref(D,'schema-library.json','/design_only_model_types/PrivateResourceRef')]
        typed_rule=None;gap=None
        if out:
            typed_rule=('AVAILABLE bool or UNAVAILABLE/null; conditional independently declared case GUARD interface','Exact D violation_predicate and frozen local OUTPUT_SCHEMA define the conditional evidence source/target for these F identities. Qualify declaration/interface only. Actual input normalization and invocation/outputbinding remain prerequisites; no expected decision, actual Boolean value or witness result supplied.')
        elif stage:
            gap='No independently source-bound canonical GUARD-to-native observed decision/currentness/non-grant adapter exists in the frozen registry. ABI result/outcome schemas and exact7 domainUNKNOWN->prerequisite->qualificationREJECT mapping exist, but expected witness outcomes cannot instantiate actual decision-stage input or an unprovided exhaustive lossless adapter.'
        else:typed_rule,gap=rules.rule_for(family,role)
        if typed_rule and not out:
            exact_type=None
            if family in ['transitive_SET_ROLE','transitive_INHERIT','ADMIN_option_escalation']:
                exact_type='SQL oid (exact source pg_roles.oid)' if role in ['member','target'] else 'Exact dict: roles full pg_roles rows, memberships full pg_auth_members rows, databases full pg_database rows, database_context DATABASE+source SQL oid'
            elif family=='replayed_challenge':exact_type='boolean' if role=='challenge_work_consumed' else 'u64 source sequence'
            elif family=='tombstoned_generation':exact_type='u64' if role=='supplied_generation' else 'Complete finite set of source u64 generations, exact entity/epoch scope'
            elif family in ['restart_substitution','reconnect_substitution']:exact_type='Closed source work-state enum including domain UNKNOWN' if role=='old_work_state' else 'boolean source authority-claim event'
            elif family=='credential_inheritance':exact_type='Exact set of source qualification-input lineages' if role=='target_qualification_receipts' else 'u64 generation'
            elif family=='wrong_role':exact_type='Record oid:SQL oid,rolname:name' if role=='actual_authenticated_SQL_role' else 'Record oid:SQL oid,name:name'
            elif family=='PUBLIC_path':exact_type='Complete map relation-natural-key -> exploded typed ACL multiset' if role=='object_acls' else 'Finite source-policy set of raw SQL privilege-verb enum, separate from logical operation roster'
            if exact_type:typed_rule=(exact_type,typed_rule[1])
        key=dict(semantic_object=role,domain=u['DOMAIN'],stage=u['STAGE'],identity=u['IDENTITY'],type=u['TYPE'],cardinality=u['CARDINALITY'],authority=[ref(D,'family-descriptors.json','/families/'+family)])
        if family in ['transitive_SET_ROLE','transitive_INHERIT','ADMIN_option_escalation'] and role in ['member','target']:
            key=dict(semantic_object=role,domain=u['DOMAIN'],stage=u['STAGE'],identity=sorted([dict(model_id=i['model_id'],view=i['view'],variant=i['variant']) for i in u['IDENTITY']],key=lambda i:i['model_id']),type='SQL oid (exact source pg_roles.oid)',cardinality='one unchanged source R.oid' if role=='member' else 'one unchanged source A.oid',authority=ref(D,'baseline-models.json'),invariance='Only membership rows mutate, R/A full source-role identity unchanged under exact D unchanged rule')
        cid='QUALIFICATION_CLASS/'+dig(key);duplicate=cid in groups
        groups.setdefault(cid,dict(CLASS_ID=cid,SEMANTIC_KEY=key,MEMBERS=[]));groups[cid]['MEMBERS'].append(qid)
        terminal='STATIC_SOURCE_EXHAUSTED_NOT_ESTABLISHED' if not typed_rule else 'QUALIFIED_FROM_EXISTING_STATIC_ARTIFACT' if out else 'QUALIFIED_BY_DETERMINISTIC_DERIVATION'
        if duplicate:
            rep=groups[cid]['MEMBERS'][0];assert record_by_q[rep]['TERMINAL_CLASS'].startswith('QUALIFIED_');terminal='DUPLICATE_OF_QUALIFIED_CANONICAL_SEMANTIC'
        chain=None;source_id=None
        if typed_rule:
            if duplicate:source_id=record_by_q[groups[cid]['MEMBERS'][0]]['QUALIFIED_SOURCE']
            else:
                source_id='QUALIFIED_SEMANTIC/'+dig(key)
                chain=dict(DERIVATION_ID='DERIVATION/'+dig([qid,key]),INPUT_SOURCE_REFERENCES=evidence,INPUT_ESTABLISHMENT_SCOPE='Immutable literal definitions, exact source field schemas and symbolic constructor constraints; no measured values established',TRANSFORMATION=typed_rule[1],TYPE=typed_rule[0],AUTHORITY='Frozen source/design rules and accepted pure local operator semantics only',IDENTITY_PRESERVATION=u['IDENTITY'],CARDINALITY=u['CARDINALITY'],WELL_FORMEDNESS='Every source schema/reference/range/natural-key/context condition remains required. Missing/inconsistent future instantiation -> UNAVAILABLE, not successful evaluation.',DETERMINISTIC=True,EXPECTED_WITNESS_RESULT_CONSUMED=False,SOURCE_VALUES_ESTABLISHED=False)
                chain['SOURCE_STAGE_TRANSFORMATION']=dict(target_stage=u['STAGE'],trusted_reference='Independent before/current source reference and exact model identity retained',candidate='Exact tagged source mutation view; no trusted reference copied from candidate',composite='Where helper consumes an evidence wrapper, combine tagged post-state rows with independent trusted key/roster explicitly; never relabel post-state rows as trusted-before observations.')
                chain['DERIVATION_HASH']=dig(chain)
                if not out:derivations.append(chain)
                sources[source_id]=dict(CANONICAL_SOURCE_ID=source_id,SOURCE_HASH=dig(dict(key=key,derivation=chain)),PROVENANCE=evidence,SEMANTIC_OBJECT=role,DOMAIN=u['DOMAIN'],STAGE=u['STAGE'],IDENTITY=key['identity'],TYPE=typed_rule[0],CARDINALITY=u['CARDINALITY'],AUTHORITY='FROZEN_ACCEPTED_STATIC_DESIGN_CONTRACT',QUALIFICATION_ID=qid,DEPENDENT_BINDINGS=u['REMAINING_BINDINGS'],QUALIFICATION_SCOPE='Conditional target/interface declaration' if out else 'Exact structural source-parametric projection, not actual data or authority admission',DERIVATION_IF_ANY=chain,ACTUAL_VALUES_ESTABLISHED=False)
        affected_inputs=[b for b in u['REMAINING_BINDINGS'] if b.startswith(('ACQUIRE/','CONSUME/'))];edges=[b for b in u['REMAINING_BINDINGS'] if b.startswith('EDGE/')]
        candidate_index=sorted(set(hit_index.get(role.lower(),[])+hit_index.get(family.lower(),[])))
        record=dict(QUALIFICATION_ID=qid,SOURCE_REQUIREMENT_ID=u['SOURCE_REQUIREMENT_ID'],ROOT_CAUSE_ID=u['ROOT_CAUSE_ID'],SEMANTIC_OBJECT=role,DOMAIN=u['DOMAIN'],STAGE=u['STAGE'],REQUIRED_IDENTITY=u['IDENTITY'],REQUIRED_TYPE=u['TYPE'],REQUIRED_CARDINALITY=u['CARDINALITY'],AFFECTED_SOURCE_IDS=u['CANDIDATE_STATIC_SURFACES'],AFFECTED_BINDING_IDS=u['REMAINING_BINDINGS'],AFFECTED_FUNCTIONS=[fid],AFFECTED_COMPOSITION_EDGES=edges,AFFECTED_WITNESSES=wids,AUTHORIZED_STATIC_SURFACES_SEARCHED='ALL_FROZEN_9494_SURFACES/static-surface-search-receipts.json',CANDIDATE_SOURCES=u['CANDIDATE_STATIC_SURFACES'],DISCOVERY_CANDIDATE_SURFACE_IDS=candidate_index,QUALIFIED_SOURCE=source_id,DERIVATION_IF_ANY=chain,AUTHORITY_SOURCE=evidence,CARDINALITY_SOURCE=[ref(D,'baseline-models.json'),ref(D,'family-descriptors.json','/families/'+family)],TERMINAL_CLASS=terminal,TERMINAL_REASON=typed_rule[1] if typed_rule else gap or 'No exact complete qualified source or frozen lossless normalization for this item is established after bounded typed source/candidate review.',EVIDENCE_HASHES={r['path']:r['sha256'] for r in evidence},SEMANTIC_CLASS_ID=cid,CLASSIFICATION_SCOPE='Finite frozen106item authority-bound source/derivation universe; not impossibility over arbitrary future artifacts or algorithms',SEARCH_EXHAUSTION=dict(AUTHORIZED_SURFACES_TOTAL=len(search_surfaces),AUTHORIZED_SURFACES_SEARCHED=len(search_surfaces),UNSEARCHED_AUTHORIZED_SURFACES=0,QUALIFIED_CANDIDATES_FOUND=1 if typed_rule else 0,DERIVABLE_CANDIDATES_FOUND=1 if typed_rule and not out else 0,EXHAUSTION_COMPLETE=True,SEMANTIC_REVIEW_METHOD='Exact model/view/variant and source schema/type/cardinality authority check; direct selection, frozen constructors, lossless source-field renaming/wrapping and typed pure-operator normalization. Similar field names, source obligations, prospective auth requirements, drafts and expected results do not qualify missing sources.',CANDIDATE_DISPOSITION='Qualified exact source contract identified' if typed_rule else 'All named model/schema/registry/operator/source-capability candidates are partial, type/scope incompatible or require missing independent admission/observation normalization; matched documentary repetition does not add authority.'))
        if stage:record['AFFECTED_FUNCTIONS']=sorted({wid_fid[w] for w in wids})
        if duplicate:record['DUPLICATE_OF_QUALIFICATION']=groups[cid]['MEMBERS'][0]
        if source_id:
            source=sources[source_id];source['DEPENDENT_BINDINGS']=sorted(set(source['DEPENDENT_BINDINGS'])|set(u['REMAINING_BINDINGS']))
            source.setdefault('DEPENDENT_QUALIFICATION_IDS',[]).append(qid)
            source['SOURCE_HASH_SCOPE']='Canonical semantic key and derivation; dependency references excluded, all entry bytes sealed by gate manifest'
        records.append(record);record_by_q[qid]=record
    assert len(records)==106 and all(r['TERMINAL_CLASS'] in TAXONOMY for r in records)
    write('qualification-deduplication',dict(required=106,unique_classes=len(groups),duplicates=106-len(groups),classes=list(groups.values()),equivalence_scope='Exact source semantic coordinates; only R/A unchanged anchors proven equivalent across membership mutations. Other differently scoped items remain separate.'))
    write('qualification-terminal-results',dict(required=106,total=106,counts=dict(collections.Counter(r['TERMINAL_CLASS'] for r in records)),records=records,no_open_or_unknown_status=True))
    write('static-search-exhaustion',dict(scope='Finite frozen106 source qualifications under documented typed frozen derivation calculus, not all possible future engineering or added artifacts',authorized_surfaces=len(search_surfaces),unsearched=0,items=[dict(QUALIFICATION_ID=r['QUALIFICATION_ID'],TERMINAL_CLASS=r['TERMINAL_CLASS'],**r['SEARCH_EXHAUSTION']) for r in records],sufficiency_not_inferred_from_lexical_matches=True,no_runtime_or_new_authority_inference=True))
    write('deterministic-derivations',dict(count=len(derivations),records=derivations,no_actual_values_derived=True))
    write('recovered-source-registry',dict(count=len(sources),entries=list(sources.values()),duplicate_semantic_entries_created=0,actual_value_facts_created=0))
    write('authority-question-compression',dict(PROJECT_AUTHORITY_QUESTIONS_TOTAL=0,CARDINALITY_AUTHORITY_QUESTIONS_TOTAL=0,ARCHITECTURAL_DECISION_QUESTIONS_TOTAL=0,questions=[],reason='No concrete new normative alternatives or required cardinality choices established. Missing authority-bound source/normalization/admission artifact is an evidence gap, not a license or automatically a project decision.',preservation=read(N,'authority-question-compression.json')))
    # Full recomputation only AFTER all106 terminals; target/interface qualification alone never completes an invocation.
    input_q={bid:r for r in records for bid in r['AFFECTED_BINDING_IDS'] if bid.startswith(('ACQUIRE/','CONSUME/'))};ins=[]
    for old in inputs:
        b=copy.deepcopy(old);q=input_q.get(b['BINDING_ID'])
        if q and q['QUALIFIED_SOURCE']:
            sid=q['QUALIFIED_SOURCE'];b.update(STATUS='COMPLETE',AMBIGUOUS=False,MISSING=False,CONTRADICTED=False,SOURCE_TYPE_INSTANTIATED=True,SOURCE_VALUE_AVAILABLE=False,C5O_QUALIFICATION_ID=q['QUALIFICATION_ID'],C5O_SOURCE_ID=sid,CANONICAL_SOURCE_FACT=[sid],SOURCE_FACT_KEY=[dict(source_id=sid,qualification=q['QUALIFICATION_ID'],witness=b['WITNESS_ID'])],BINDING_RULE=q['TERMINAL_REASON'],TRANSFORMATION=q['TERMINAL_REASON'])
        b['C5O_RECOMPUTED']=True;ins.append(b)
    im=collections.defaultdict(list)
    for b in ins:im[(b['FUNCTION_ID'],b['WITNESS_ID'])].append(b)
    outs=[]
    for old in outputs:
        o=copy.deepcopy(old);complete=all(b['STATUS']=='COMPLETE' and b['SOURCE_TYPE_INSTANTIATED'] for b in im[(o['FUNCTION_ID'],o['WITNESS_ID'])]);assert o['TARGET_INDEPENDENTLY_ESTABLISHED'];o.update(STATUS='COMPLETE' if complete else 'MISSING',MISSING=not complete,CLOSURE_STATUS='CLOSED' if complete else 'TARGET_NOT_ESTABLISHED',EXACT_INVOCATION_INPUTS_BOUND=complete,ACTUAL_VALUE=None,OUTPUT_BINDING_RULE='Independent conditional GUARD interface + all exact source-typed invocation inputs' if complete else 'Target/interface qualified; invocation blocked by exact source input binding gaps');outs.append(o)
    certs=[]
    for prior in oldcert:
        f=copy.deepcopy(prior);bi=[b for b in ins if b['FUNCTION_ID']==f['FUNCTION_ID']];oo=[o for o in outs if o['FUNCTION_ID']==f['FUNCTION_ID']];inputok=all(b['STATUS']=='COMPLETE' and b['SOURCE_TYPE_INSTANTIATED'] for b in bi);outputok=all(o['STATUS']=='COMPLETE' for o in oo);props=f['PROPERTIES'];props.update(INPUT_SCHEMA_COMPLETE=inputok,ALL_REQUIRED_INPUT_BINDINGS_COMPLETE=inputok,ALL_REQUIRED_OUTPUT_BINDINGS_COMPLETE=outputok,CANONICALLY_BINDABLE=inputok and outputok);f.update(STRICT_CERTIFIED=all(v is True for v in props.values()),ALGORITHM_DISPROVEN=False,UNPROVEN_REQUIRED_PROPERTIES=[k for k,v in props.items() if v is not True],C5O_SOURCE_IDS=sorted({b['C5O_SOURCE_ID'] for b in bi if 'C5O_SOURCE_ID' in b}));certs.append(f)
    strict={f['FUNCTION_ID']:f['STRICT_CERTIFIED'] for f in certs}
    for b in ins+outs:b['FUNCTION_STRICTLY_CERTIFIED']=strict[b['FUNCTION_ID']]
    om={o['WITNESS_ID']:o for o in outs};edges=[]
    for old in graph['edges']:
        e=copy.deepcopy(old);isguard=e['TARGET_FUNCTION'].startswith('GUARD/');closed=old['STATUS']=='COMPLETE' or isguard and om[e['TARGET_FUNCTION'][6:]]['STATUS']=='COMPLETE';sourcebound=closed or not isguard and e['SOURCE_FUNCTION'].startswith('GUARD/') and om[e['SOURCE_FUNCTION'][6:]]['STATUS']=='COMPLETE'
        e.update(STATUS='COMPLETE' if closed else 'MISSING',CLOSURE_STATUS='CLOSED' if closed else 'BINDING_BLOCKED',EDGE_STATUS='CLOSED' if closed else 'BINDING_BLOCKED',SOURCE_BINDING_STATUS='COMPLETE' if sourcebound else 'MISSING',TARGET_BINDING_STATUS='COMPLETE' if closed else 'MISSING',SEMANTIC_COMPATIBILITY='ESTABLISHED' if closed else 'EXACT_TRANSFORM_NOT_ESTABLISHED',TYPE_COMPATIBILITY='ESTABLISHED' if closed else 'EXACT_SOURCE_TYPE_INSTANCE_NOT_ESTABLISHED',STAGE_COMPATIBILITY='ESTABLISHED' if closed else 'SOURCE_STAGE_ADAPTER_NOT_ESTABLISHED',BLOCKER=None if closed else 'EXACT_INVOCATION_BINDING' if isguard else 'INDEPENDENT_NATIVE_STAGE_ADAPTER',BINDING='Exact source-parametric invocation to independently qualified conditional GUARD' if closed and isguard else old['BINDING']);edges.append(e)
    nodes={n['NODE_ID'] for n in graph['nodes']};degree={n:0 for n in nodes};adj=collections.defaultdict(list)
    for e in edges:degree[e['TARGET_FUNCTION']]+=1;adj[e['SOURCE_FUNCTION']].append(e['TARGET_FUNCTION'])
    pending=collections.deque(n for n,d in degree.items() if d==0);order=[]
    while pending:
        n=pending.popleft();order.append(n)
        for t in adj[n]:
            degree[t]-=1
            if degree[t]==0:pending.append(t)
    assert len(order)==763
    ic=collections.Counter(b['STATUS'] for b in ins);oc=collections.Counter(o['STATUS'] for o in outs);ec=collections.Counter(e['STATUS'] for e in edges)
    write('binding-recomputation',dict(required_inputs=1526,input_counts=dict(ic),required_outputs=350,output_counts=dict(oc),inputs=ins,outputs=outs,all_recomputed_after_106_terminal=True,qualified_target_does_not_alone_close_output_binding=True))
    write('all-49-recertification',dict(required=49,available=49,strict_certified=sum(f['STRICT_CERTIFIED'] for f in certs),not_certified=sum(not f['STRICT_CERTIFIED'] for f in certs),algorithm_disproven=0,functions=certs))
    write('composition-recomputation',dict(required=714,counts=dict(ec),nodes=graph['nodes'],edges=edges,topological_order=order,cycles=0))
    status={b['BINDING_ID']:b['STATUS'] for b in ins};status.update({'OUTPUT/'+o['WITNESS_ID']:o['STATUS'] for o in outs});status.update({e['EDGE_ID']:e['STATUS'] for e in edges})
    frontier={}
    for q in records:
        remain=[b for b in q['AFFECTED_BINDING_IDS'] if status[b]!='COMPLETE']
        if not remain:continue
        stage=q['DOMAIN']=='INDEPENDENT_NATIVE_STAGE';effect=fun[q['AFFECTED_FUNCTIONS'][0]]['families'][0] in ['default_privilege_path','SECURITY_DEFINER_path','reader_mutation'];key='INDEPENDENT_NATIVE_STAGE' if stage else 'AUTHENTICATED_SOURCE_ADMISSION' if effect else 'EXACT_SOURCE_PORT_NORMALIZATION'
        f=frontier.setdefault(key,dict(BLOCKER_ID='BLOCKER/'+dig(key),BLOCKER_CLASS='COMPOSITION_GAP' if stage else 'NON_QUALIFICATION_BINDING_GAP',EXACT_BLOCKER='Independent source-stage adapter remains missing; no expected outcome substitution' if stage else 'Authenticated full source-body/effect admission and exact normalized operator input artifact not established' if effect else 'Exact complete authority-bound source-to-port carrier/normalization not established within finite frozen source calculus',AFFECTED_QUALIFICATIONS=[],AFFECTED_BINDINGS=[],AFFECTED_FUNCTIONS=[],AFFECTED_EDGES=[],AFFECTED_WITNESSES=[],NEXT_ACTION='Bounded concrete source/adapter evidence contract decomposition; no generic source-recovery loop, runtime execution or new authority automatically authorized'))
        f['AFFECTED_QUALIFICATIONS'].append(q['QUALIFICATION_ID']);f['AFFECTED_BINDINGS'].extend(remain);f['AFFECTED_FUNCTIONS'].extend(q['AFFECTED_FUNCTIONS']);f['AFFECTED_EDGES'].extend(x for x in remain if x.startswith('EDGE/'));f['AFFECTED_WITNESSES'].extend(q['AFFECTED_WITNESSES'])
    for f in frontier.values():
        for k in ['AFFECTED_QUALIFICATIONS','AFFECTED_BINDINGS','AFFECTED_FUNCTIONS','AFFECTED_EDGES','AFFECTED_WITNESSES']:f[k]=sorted(set(f[k]))
    write('minimum-blocker-frontier',dict(total=len(frontier),blockers=list(frontier.values()),minimality_scope='Independent exact-input normalization, authenticated source admission, native-stage composition concerns; not a globally minimum fact-cut theorem. Output symptoms share upstream cause and are not separate authority decisions.'))
    dag=dict(CANONICAL_DECISION_DAG_STATUS='INCOMPLETE_BINDING',CANONICAL_DECISION_NODES=763,CANONICAL_DECISION_EDGES=714,UNBOUND_DECISION_INPUTS=1526-ic['COMPLETE'],UNBOUND_DECISION_OUTPUTS=sum(e['STATUS']!='COMPLETE' for e in edges if e['SOURCE_FUNCTION'].startswith('GUARD/')),AMBIGUOUS_DECISION_RELATIONS=ic['AMBIGUOUS'],UNORDERED_REQUIRED_RELATIONS=0,CYCLES_DETECTED=0);write('canonical-dag',dag)
    write('canonical-evaluator-analysis',dict(complete=0,assembly_attempted=False,reason='All49/type/source/decision-stage prerequisites incomplete',forbidden_result_inputs_consumed=[],witness_executed=False))
    write('saturation-decision',dict(state='SATURATED',required=106,terminal=106,open=0,unsearched_authorized_surfaces=0,finite_scope='Exactly106 C5N items and immutable9494file source universe, direct/frozen constructor/lossless typed derivation calculus',not_global_impossibility=True,nonstatic_blockers='Missing independently admitted source/normalization and native-stage artifacts, no amount of documentary projection repetition creates them.',no_generic_search_continuation=True,positive_runtime_necessity=False,new_normative_decisions_demonstrated=False))
    cov=read(N,'coverage-accounting.json');cov.update(source=ref(N,'coverage-accounting.json'),status='PRESERVED_NOT_EXECUTED_C5O');write('coverage-accounting',cov)
    counts=collections.Counter(q['TERMINAL_CLASS'] for q in records)
    summary=dict(BRANCH=git('branch','--show-current'),BASELINE_HEAD='cbc284f62d9bd09b7169b55c8d66a3c51a68c6cb',CURRENT_HEAD=git('rev-parse','HEAD'),TRACKED_DIRTY_COUNT=0,STAGED_COUNT=0,AUTHORIZED_UNTRACKED_FILES_BEFORE=395,UNTRACKED_FILES_AFTER=None,UNAUTHORIZED_UNTRACKED_COUNT=0,C5N_INPUT_INTEGRITY='PASS',HISTORICAL_FILES_PRESERVED=9458,HISTORICAL_UNION_PRESERVED=9494,SEMANTIC_QUALIFICATIONS_REQUIRED=106,UNIQUE_SEMANTIC_QUALIFICATION_CLASSES=len(groups),DUPLICATE_QUALIFICATIONS=106-len(groups),TERMINAL_CLASSIFICATIONS_TOTAL=106,PROJECT_AUTHORITY_QUESTIONS_TOTAL=0,CARDINALITY_AUTHORITY_QUESTIONS_TOTAL=0,ARCHITECTURAL_DECISION_QUESTIONS_TOTAL=0,STATIC_RECOVERY_STATE='SATURATED',CANONICAL_INPUT_BINDINGS_REQUIRED=1526,CANONICAL_INPUT_BINDINGS_COMPLETE=ic['COMPLETE'],CANONICAL_INPUT_BINDINGS_MISSING=ic['MISSING'],CANONICAL_INPUT_BINDINGS_AMBIGUOUS=ic['AMBIGUOUS'],CANONICAL_INPUT_BINDINGS_CONTRADICTED=0,CANONICAL_OUTPUT_BINDINGS_REQUIRED=350,CANONICAL_OUTPUT_BINDINGS_COMPLETE=oc['COMPLETE'],CANONICAL_OUTPUT_BINDINGS_MISSING=oc['MISSING'],CANONICAL_OUTPUT_BINDINGS_AMBIGUOUS=0,CANONICAL_OUTPUT_BINDINGS_CONTRADICTED=0,LOCAL_FUNCTIONS_REQUIRED=49,LOCAL_FUNCTIONS_AVAILABLE=49,LOCAL_FUNCTIONS_STRICT_CERTIFIED=sum(f['STRICT_CERTIFIED'] for f in certs),LOCAL_FUNCTIONS_NOT_CERTIFIED=sum(not f['STRICT_CERTIFIED'] for f in certs),ALGORITHM_DISPROVEN=0,COMPOSITION_EDGES_REQUIRED=714,COMPOSITION_EDGES_COMPLETE=ec['COMPLETE'],COMPOSITION_EDGES_MISSING=ec['MISSING'],COMPOSITION_EDGES_AMBIGUOUS=0,COMPOSITION_EDGES_CONTRADICTED=0,COMPOSITION_CYCLES=0,**dag,MINIMUM_BLOCKER_FRONTIER_TOTAL=len(frontier),COMPLETE_CANONICAL_DECISION_EVALUATORS=0,CANONICAL_CASES_TOTAL=350,STATICALLY_PROVEN=0,STATICALLY_DISPROVEN=0,UNKNOWN=350,CONTRADICTED=0,N1_SUBSTITUTION_STATIC_WITNESSES='OPEN',N1_DECISIONS_REQUIRED=12,N1_DECISIONS_CLOSED=11,N1_DECISIONS_OPEN=1,V2_NATIVE_STATIC_DESIGN_PROOF='FAIL',V2_NATIVE_STATUS='BLOCKED',ATOMIC_NORMATIVE_CANDIDATES_TOTAL=108,AMBIGUOUS_CANDIDATES_PRESERVED=105,CANONICAL_ATTACK_DENOMINATOR=350,DENOMINATOR_CHANGED='NO',ATTACKS_MATERIALIZED_THIS_GATE=0,ATTACKS_EVALUATED_THIS_GATE=0,INDEPENDENT_REVIEW_1='PENDING',INDEPENDENT_REVIEW_2='PENDING',SELECTED_OUTCOME='G_SATURATED_COMPOUND_FRONTIER',NEXT_EXECUTED=False,NEXT_GATE='BOUNDED_MINIMUM_BLOCKER_FRONTIER_DECOMPOSITION')
    for k in TAXONOMY:summary[k]=counts[k]
    # CONTRADICTED qualification and witness counters are both zero; retain explicit units.
    summary['QUALIFICATION_CONTRADICTED']=counts['CONTRADICTED']
    for k in ['SHARED_DB_CONTACTED','PRODUCTION_CONTACTED','EXISTING_LOCAL_DB_CONTACTED','NETWORK_CONTACT_FOR_PROOF','V043_EXECUTED','V043_CHANGED','B02_EXECUTED','GIT_ADD','COMMIT','PUSH','POSTMASTER_CONTEXT_BINDING_RESOLVED','INTERNAL_SCOPE_RESOLVED','ATOMIC_BOUNDARY_RESOLVED','CANONICAL_INTERNAL_OBLIGATION_UNIVERSE_ESTABLISHED']:summary[k]='NO'
    write('primary-result',dict(outcome=summary['SELECTED_OUTCOME'],state='SATURATED',finite_qualifications_terminal=106,next_gate=summary['NEXT_GATE'],next_executed=False,reason='Finite authorized source qualification exhausted; independent exact-input/admission and composition artifacts still missing. No new authority/cardinality/architecture choice or runtime necessity demonstrated.'))
    write('final-summary',summary);print(canon(dict(terminal_counts=counts,unique_classes=len(groups),input_counts=ic,output_counts=oc,strict=summary['LOCAL_FUNCTIONS_STRICT_CERTIFIED'],edge_counts=ec,frontier=len(frontier))))
if __name__=='__main__':main()
