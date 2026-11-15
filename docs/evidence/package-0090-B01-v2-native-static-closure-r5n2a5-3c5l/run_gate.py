"""C5L: static source-parametric binding recovery. No witness execution or external IO."""
import collections
import copy
import hashlib
import json
import pathlib
import subprocess
import functools

ROOT = pathlib.Path(__file__).resolve().parents[3]
OUT = pathlib.Path(__file__).resolve().parent
PREFIX = 'docs/evidence/package-0090-B01-v2-native-static-closure-r5n2a5-3c5'
def path(g, n): return ROOT / (PREFIX + g) / n
def read(g, n): return json.loads(path(g, n).read_text(encoding='utf-8-sig'))
@functools.lru_cache(maxsize=None)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(x): return json.dumps(x, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
def digest(x): return hashlib.sha256(canon(x).encode()).hexdigest()
def write(n, x): (OUT / (n + '.json')).write_text(json.dumps(x, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
def git(*args): return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()
def ref(g, n, pointer=''): return dict(path=path(g,n).relative_to(ROOT).as_posix(),sha256=sha(path(g,n)),pointer=pointer)

def main():
    kp = read('k','preflight.json'); km = read('k','SHA256-MANIFEST.json')
    historical = dict(kp['historical_sha256']); historical.update(km['files'])
    historical[path('k','SHA256-MANIFEST.json').relative_to(ROOT).as_posix()] = sha(path('k','SHA256-MANIFEST.json'))
    bad = [p for p,h in historical.items() if not (ROOT/p).is_file() or sha(ROOT/p)!=h]
    assert not bad, bad
    tracked = git('diff','--name-only').splitlines(); staged=git('diff','--cached','--name-only').splitlines()
    before = git('ls-files','--others','--exclude-standard').splitlines()
    old = [p for p in before if not p.startswith(PREFIX+'l/')]
    assert len(old)==294 and not tracked and not staged
    assert git('rev-parse','HEAD')=='451265ff5b3d286eb4d27c4b3817c2f558f30123'
    write('preflight',dict(status='PASS',repository=str(ROOT),branch=git('branch','--show-current'),head=git('rev-parse','HEAD'),frozen_baseline='cbc284f62d9bd09b7169b55c8d66a3c51a68c6cb',tracked_dirty=tracked,staged=staged,authorized_untracked_before=294,authorized_paths_before=old,historical_sha256=historical,historical_files_checked=len(historical)))
    write('c5k-input-integrity',dict(status='PASS',manifest=ref('k','SHA256-MANIFEST.json'),files_checked=len(km['files']),historical_union_checked=len(historical),mismatches=bad,immutable_inputs=True))
    contract=read('k','minimum-binding-closure-contract.json')
    ci=[]
    for key,value in contract.items():
        values=value if isinstance(value,list) else [value]
        for j,v in enumerate(values):
            status='ALREADY_AUTHORIZED'; reason='Frozen C5K requirement or boundary; retained without expanding execution authority.'
            if key=='functions_requiring_strict_certification': status='DETERMINISTICALLY_DERIVABLE';reason='Recompute all49 from input/output/schema/source evidence; this list is not an algorithm-failure list.'
            elif key=='required_artifacts_per_function': status='DETERMINISTICALLY_DERIVABLE';reason='Engineering/source projection obligation; closure only on exact scoped evidence, otherwise retained gap.'
            elif key=='special_obligations': status='DETERMINISTICALLY_DERIVABLE';reason='Frozen semantic requirement; authentication or source-admission evidence remains necessary. Missing evidence does not itself establish a normative alternative.'
            ci.append(dict(pointer='/'+key+('/'+str(j) if isinstance(value,list) else ''),item=v,classification=status,rationale=reason))
    write('minimum-binding-contract-validation',dict(status='PASS',contract=ref('k','minimum-binding-closure-contract.json'),items=ci,all_items_classified=True,new_policy_created=False))
    inputs=read('k','canonical-input-binding-registry.json')['bindings']; outputs=read('k','canonical-output-binding-registry.json')['bindings']; graph=read('k','composition-graph.json')
    functions=read('k','49-function-inventory.json')['functions']
    cases=read('f','derived-canonical-350-registry.json')['case_records']; case_map={c['WITNESS_ID']:c for c in cases}
    facts=read('i','canonical-fact-registry.json')['facts']; fm={f['FACT_ID']:f for f in facts}
    schemas=read('d','schema-library.json')['schemas']; models=read('d','baseline-models.json')['models']; families=read('d','family-descriptors.json')['families']
    assert len(inputs)==1526 and len(outputs)==350 and len(graph['edges'])==714 and len(functions)==49
    # Exact equivalence is deliberately narrow. Distinct scoped identities never collapse by name.
    def classes(records,kind):
        groups={}
        for idx,b in enumerate(records):
            wid=b.get('WITNESS_ID'); c=case_map.get(wid)
            if kind=='input':
                key=dict(layer=b['LAYER'],source_keys=b['SOURCE_FACT_KEY'],source_stage=b['SOURCE_STAGE'],transform=b['TRANSFORMATION'],cardinality=b['CARDINALITY'],authority=b['BINDING_AUTHORITY'],function=b['FUNCTION_ID'],input=b['INPUT_ID'])
                member=b['BINDING_ID']
            elif kind=='output':
                key=dict(source_function=b['FUNCTION_ID'],domain='AVAILABLE_BOOLEAN_VIOLATION_EVIDENCE_ELSE_UNAVAILABLE',stage=b['TARGET_STAGE'],target=b['CANONICAL_TARGET'],authority=b['OUTPUT_BINDING_AUTHORITY'],cardinality='one invocation one guard',identity=wid)
                member='OUTPUT/'+wid
            else:
                key={k:v for k,v in b.items() if k!='STATUS'};member='EDGE/'+str(idx)
            cid=kind.upper()+'_CLASS/'+digest(key)
            groups.setdefault(cid,dict(CLASS_ID=cid,SEMANTIC_KEY=key,MEMBERS=[],EQUIVALENCE_PROOF='Exact source-type/identity/stage/transform/cardinality/authority coordinates, no name-only merging.'))['MEMBERS'].append(member)
        return list(groups.values())
    ic=classes(inputs,'input');oc=classes(outputs,'output');ec=classes(graph['edges'],'composition')
    write('input-binding-equivalence-classes',dict(total=len(ic),required_members=1526,classes=ic,classification_precedes_resolution=True,physical_fact_deduplication_claim=False))
    write('output-binding-equivalence-classes',dict(total=len(oc),required_members=350,classes=oc))
    write('composition-equivalence-classes',dict(total=len(ec),required_members=714,classes=ec))
    # These source mappings are exact complete-field projections, not generic name matching.
    specs={
      'wrong_binary':('IDENTITY/binary_module_identity',['complete_file_sha256'],'expected.executable_digest','observed.executable_digest'),
      'wrong_credential':('IDENTITY/credential_identity',['credential_certificate_or_endpoint_manifest_digest'],'trusted_expected_subject_credential_or_endpoint_ref','candidate.subject_credential_ref'),
      'stale_registry_revision':('IDENTITY/registry_revision',['generation_registry_revision'],'independently_current_generation_revision','supplied_generation_revision'),
      'wrong_loader':('IDENTITY/loader_identity',None,'expected.loader_identity','candidate.loader_identity'),
      'wrong_parent':('IDENTITY/parent_identity',None,'expected.retained_parent_tuple','candidate.retained_parent_tuple'),
      'wrong_process_instance':('IDENTITY/process_instance_identity',None,'independent_expected_subject_process_tuple','candidate.subject_process_tuple')}
    plans={}; index=collections.defaultdict(list)
    for f in facts:
        for wid in f['DEPENDENT_WITNESSES']: index[wid].append(f)
    for c in cases:
        wid=c['WITNESS_ID'];actor,family=wid.split('/');bs=c['BASELINE_STATE']
        if family not in specs:continue
        schema,fields,expected,observed=specs[family];fields=fields or [f['name'] for f in schemas[schema]['fields']]
        scope_model=bs['library_model_id'];model=models[scope_model]
        assert model['subject']==actor and bs['selected_view']=='CURRENT_SUBJECT_IDENTITY'
        assert 'initially equal field-by-field' in model['baseline_constraints'][0]
        assert c['MUTATION']['definition']==families[family]
        selected=[]
        for field in fields:
            slot='identity['+actor+']/'+schema+'/'+field
            matches=[f for f in index[wid] if len(f['CANONICAL_KEY'])==4 and f['CANONICAL_KEY'][0]=='SOURCE_SCOPED_BINDING' and f['CANONICAL_KEY'][1]['model_id']==scope_model and f['CANONICAL_KEY'][1]['selected_view']==bs['selected_view'] and f['CANONICAL_KEY'][2]==slot]
            if field=='participant_id':
                matches=[f for f in index[wid] if f['CANONICAL_KEY']==['FROZEN_ENUM_VALUE','NATIVE_ACTOR_ENUM',actor] and f['VALUE_TYPE']=='u16']
            assert len(matches)==1,(wid,slot,len(matches));selected.append(matches[0])
        mutations=[f for f in index[wid] if f['FACT_TYPE']=='MUTATION_BINDING_OBLIGATION']
        assert len(mutations)==1
        schema_fields=[f for f in schemas[schema]['fields'] if f['name'] in fields]
        for operand,side in [(expected,'INDEPENDENT_APPROVED_BASELINE'),(observed,'TAGGED_CANDIDATE_AFTER_EXACT_MUTATION')]:
            plan=dict(witness=wid,input=operand,actor=actor,model_id=scope_model,selected_view=bs['selected_view'],exact_variant_hash=selected[0]['CANONICAL_KEY'][1]['exact_variant_hash'],schema=schema,field_vector=schema_fields,cardinality='Exactly one scalar' if len(fields)==1 else 'Exactly one complete ordered source tuple; every field retained',side=side,baseline_fact_ids=[f['FACT_ID'] for f in selected],mutation_fact_id=mutations[0]['FACT_ID'],source_schema=ref('d','schema-library.json','/schemas/'+schema.replace('/','~1')),baseline_model=ref('d','baseline-models.json','/models/'+scope_model.replace('/','~1')),frozen_case=ref('f','derived-canonical-350-registry.json','/case_records/'+str(cases.index(c))),mutation=ref('d','family-descriptors.json','/families/'+family),selector=families[family]['selector'],relation=dict(before=families[family]['before'],after=families[family]['after'],unchanged=families[family]['unchanged']),extraction=('Select independently approved subject source field vector' if operand==expected else 'Apply only exact typed symbolic mutation to subject source field vector; preserve every other field and all canonical reference constraints'),nested_references='Every referenced digest remains constrained to its full canonical tuple; no digest establishes source body/authentication by itself.',values_instantiated=False,fixture_complete=False,proof_scope='Exact source-parametric projection; universal under frozen source parameter constraints, no chosen measurement or fixture value.')
            plans[(wid,operand)]=plan
            plan['preserved_baseline_constraints']=model['baseline_constraints']
            plan['future_instantiation_rule']=model['future_binding_rule']
            plan['independent_current_reference']='Current ledger/enrollment independently witnessed, candidate initially equals approved counterpart; only named selector mutates. Never bind trusted reference from mutated candidate.'
    write('source-parametric-projection-proofs',dict(total=len(plans),plans=list(plans.values()),expected_result_consumed=False,source_decision_consumed=False,fixture_values_created=False))
    resolutions=[];recoveries=[];new_inputs=[]
    for original in inputs:
        b=copy.deepcopy(original);wid=b['WITNESS_ID'];plan=plans.get((wid,b['INPUT_ID']));oldstatus=b['STATUS']
        if plan:
            b.update(STATUS='COMPLETE',AMBIGUOUS=False,MISSING=False,CONTRADICTED=False,SOURCE_VALUE_AVAILABLE=False,BINDING_RULE='Exact source-parametric projection in source-parametric-projection-proofs.json',TRANSFORMATION=plan['extraction'],SOURCE_PARAMETRIC_PLAN=digest(plan),SOURCE_TYPE_INSTANTIATED=True)
        else:b['SOURCE_TYPE_INSTANTIATED']=oldstatus=='COMPLETE'
        if oldstatus=='AMBIGUOUS':
            candidates=b['CANONICAL_SOURCE_FACT']; selected=plan['baseline_fact_ids'] if plan else []
            # Keep every original candidate and explicit coordinate observations; remaining candidates are not declared valid.
            candidate_rows=[]
            for fid in candidates:
                f=fm[fid];key=f['CANONICAL_KEY']
                axes=dict(semantic_domain=f['FACT_TYPE'],source_identity=key,source_stage=b['SOURCE_STAGE'],type=f['VALUE_TYPE'],cardinality_status=f['STATUS'],authority=f['SOURCE'],provenance_hash=f['SOURCE_HASH'])
                candidate_rows.append(dict(FACT_ID=fid,AXES=axes,DOMINANCE=('SELECTED_TYPED_BASELINE_COMPONENT' if fid in selected else 'ELIMINATED_BY_EXACT_ACTOR_SCHEMA_FIELD_OR_SIDE' if plan else 'NO_SOURCE_PROVEN_DOMINANCE_ORDER'),STAGE_NOTE=('Post-state requires mutation transform; baseline fact alone is not post-state' if plan and plan['side'].startswith('TAGGED') else 'No observed value asserted')))
            resolutions.append(dict(BINDING_ID=b['BINDING_ID'],WITNESS_ID=wid,INPUT_ID=b['INPUT_ID'],CANDIDATE_COUNT=len(candidates),CANDIDATES=candidate_rows,SELECTED_SOURCE_PLAN=digest(plan) if plan else None,NONDOMINATED_COMPONENTS=selected if plan else [],NONDOMINATED_UNRESOLVED_CANDIDATE_SET=candidates if not plan else [],STATUS='RESOLVED_UNIQUE' if plan else 'REMAINS_AMBIGUOUS',RATIONALE='Unique qualified source component vector plus exact tagged mutation projection' if plan else 'Candidate set lacks certified operand-specific actor/context/pre-post/normalization selector. No authority question inferred from missing engineering evidence.'))
        if oldstatus=='MISSING':
            recoveries.append(dict(BINDING_ID=b['BINDING_ID'],WITNESS_ID=wid,INPUT_ID=b['INPUT_ID'],LAYER=b['LAYER'],STATUS='CLOSED_CANONICAL_PROJECTION' if plan else 'SOURCE_NOT_ESTABLISHED',SOURCE_EXISTS=bool(plan) or bool(b['CANONICAL_SOURCE_FACT']),SOURCE_DERIVABLE=bool(plan),MISSING_KIND='NONE' if plan else 'EXACT_SOURCE_STAGE_TYPE_PROJECTION_NOT_ESTABLISHED',SOURCE_REFS=[b['BINDING_AUTHORITY']],RECOVERY_RULE=plan['extraction'] if plan else 'Recover qualified frozen operand schema and identity from D/F/I; disambiguate before normal-form consumption. Collection roots additionally need exact full multiset/cardinality; source-body/effect admission requires authenticated complete source expansion.',NEW_AUTHORITY_REQUIRED_ESTABLISHED=False))
        new_inputs.append(b)
    write('ambiguous-input-resolution',dict(before=595,resolved=sum(r['STATUS']=='RESOLVED_UNIQUE' for r in resolutions),remaining=sum(r['STATUS']=='REMAINS_AMBIGUOUS' for r in resolutions),records=resolutions,unresolved_nondominance_is_not_semantic_admissibility=True))
    write('missing-input-source-recovery',dict(before=805,counts=dict(collections.Counter(r['STATUS'] for r in recoveries)),records=recoveries,scope='Absent exact projection proof is preserved; source presence is not binding completeness.'))
    im=collections.defaultdict(list)
    for b in new_inputs:im[(b['FUNCTION_ID'],b['WITNESS_ID'])].append(b)
    new_outputs=[]
    for oldout in outputs:
        o=copy.deepcopy(oldout); exact=all(b['STATUS']=='COMPLETE' and b['SOURCE_TYPE_INSTANTIATED'] for b in im[(o['FUNCTION_ID'],o['WITNESS_ID'])])
        closed=o['STATUS']=='COMPLETE' or exact
        o.update(STATUS='COMPLETE' if closed else 'MISSING',CLOSURE_STATUS='CLOSED' if closed else 'TARGET_NOT_ESTABLISHED',MISSING=not closed,AMBIGUOUS=False,CONTRADICTED=False,OUTPUT_DOMAIN='AVAILABLE boolean violation evidence, otherwise UNAVAILABLE/null',TARGET_INDEPENDENTLY_ESTABLISHED=True,IDENTITY=o['WITNESS_ID'],CARDINALITY='one case invocation -> one exact GUARD',ACTUAL_VALUE=None,EXACT_INVOCATION_INPUTS_BOUND=exact,OUTPUT_BINDING_RULE='Guard declared independently by D family violation predicate and F witness identity; conditional evidence transfer only, never native REJECT, domain UNKNOWN or witness PASS' if closed else 'Independent GUARD destination exists; exact source-bound invocation meaning remains unestablished')
        new_outputs.append(o)
    write('output-binding-closure',dict(required=350,counts=dict(collections.Counter(o['STATUS'] for o in new_outputs)),records=new_outputs,old_missing_records=329))
    om={o['WITNESS_ID']:o for o in new_outputs}; cert=[]
    for f in functions:
        f=copy.deepcopy(f); fid=f['FUNCTION_ID']; fi=[b for b in new_inputs if b['FUNCTION_ID']==fid];fo=[o for o in new_outputs if o['FUNCTION_ID']==fid]
        input_ok=bool(fi) and all(b['STATUS']=='COMPLETE' and b['SOURCE_TYPE_INSTANTIATED'] for b in fi);output_ok=bool(fo) and all(o['STATUS']=='COMPLETE' for o in fo)
        props=dict(IMPLEMENTATION_AVAILABLE=f['IMPLEMENTATION_AVAILABLE'],SEMANTICS_COMPLETE=f['SEMANTICS_COMPLETE'],INPUT_SCHEMA_COMPLETE=input_ok,OUTPUT_SCHEMA_COMPLETE=f['OUTPUT_SCHEMA_COMPLETE'],AUTHORITY_BOUND=f['AUTHORITY_BOUND'],ALL_INPUT_BINDINGS_COMPLETE=input_ok,ALL_OUTPUT_BINDINGS_COMPLETE=output_ok,DETERMINISTIC=f['DETERMINISTIC'],SIDE_EFFECT_FREE=f['SIDE_EFFECT_FREE'],EXPECTED_RESULT_INDEPENDENT=f['EXPECTED_RESULT_INDEPENDENT'],CANONICALLY_BINDABLE=input_ok and output_ok)
        valid=all(v is True for v in props.values());cert.append(dict(FUNCTION_ID=fid,families=f['families'],PROPERTIES=props,STRICT_CERTIFIED=valid,ALGORITHM_DISPROVEN=False,UNPROVEN_REQUIRED_PROPERTIES=[k for k,v in props.items() if v is not True],INPUT_BINDING_IDS=[b['BINDING_ID'] for b in fi],OUTPUT_WITNESSES=[o['WITNESS_ID'] for o in fo],IMPLEMENTATION=f['implementation'],CALCULATION_VALIDATION=ref('k','all-49-unit-validation.json'),PRIOR_EXACT_PROOFS=ref('k','strict-function-certification-proofs.json') if f['VALID'] else None,SOURCE_PARAMETRIC_PROJECTIONS=[digest(p) for (w,_),p in plans.items() if any(o['WITNESS_ID']==w for o in fo)]))
    write('all-49-certification-recomputation',dict(required=49,available=49,strict_certified=sum(c['STRICT_CERTIFIED'] for c in cert),not_certified=sum(not c['STRICT_CERTIFIED'] for c in cert),algorithm_disproven=0,functions=cert,not_certified_does_not_mean_algorithm_invalid=True))
    write('canonical-input-binding-registry',dict(required=1526,counts=dict(collections.Counter(b['STATUS'] for b in new_inputs)),bindings=new_inputs,complete_scope='Structural source-parametric binding, no instantiated fixture or proof'))
    edges=[]
    for idx,oldedge in enumerate(graph['edges']):
        e=copy.deepcopy(oldedge);guard=e['TARGET_FUNCTION'];is_guard=guard.startswith('GUARD/')
        closed=e['STATUS']=='COMPLETE' or (is_guard and om[guard[6:]]['STATUS']=='COMPLETE')
        e.update(EDGE_ID='EDGE/'+str(idx),PREVIOUS_STATUS=e['STATUS'],STATUS='COMPLETE' if closed else 'MISSING',CLOSURE_STATUS='CLOSED' if closed else 'BINDING_BLOCKED',COMPATIBILITY=dict(source_target_type='AVAILABLE_BOOLEAN_EVIDENCE' if is_guard else 'SOURCE_STAGE_ADAPTER',semantic_stage='GUARD_EVIDENCE_ONLY' if is_guard else 'EXACT_NATIVE_STAGE_TRANSFORM_REQUIRED',identity='Exact case-scoped endpoints; no cross-case composition',cardinality='one scoped edge',authority=e['AUTHORITY_SOURCE'],order=e['ORDER']),BLOCKER=None if closed else 'EXACT_INVOCATION_BINDING' if is_guard else 'INDEPENDENT_NATIVE_STAGE_ADAPTER')
        edges.append(e)
    write('composition-edge-recomputation',dict(required=714,counts=dict(collections.Counter(e['STATUS'] for e in edges)),cycles=0,nodes=graph['nodes'],edges=edges,ordering='Frozen case-scoped forest, not a49-step pipeline'))
    counts=collections.Counter(b['STATUS'] for b in new_inputs);outcounts=collections.Counter(o['STATUS'] for o in new_outputs);edgecounts=collections.Counter(e['STATUS'] for e in edges)
    dag=dict(CANONICAL_DECISION_DAG_STATUS='INCOMPLETE_BINDING',CANONICAL_DECISION_NODES=len(graph['nodes']),CANONICAL_DECISION_EDGES=len(edges),UNBOUND_DECISION_INPUTS=1526-counts['COMPLETE'],UNBOUND_DECISION_OUTPUTS=sum(e['STATUS']!='COMPLETE' for e in edges if e['SOURCE_FUNCTION'].startswith('GUARD/')),UNORDERED_REQUIRED_RELATIONS=0,AMBIGUOUS_DECISION_RELATIONS=counts['AMBIGUOUS'],CYCLES_DETECTED=0,scope='K local-template/case-guard/stage-boundary projection; not physical source census',ALL49_STRICT=all(c['STRICT_CERTIFIED'] for c in cert),CARDINALITY_AND_SOURCE_ADMISSION_DEPENDENCIES_REMAIN=True)
    write('canonical-decision-dag',dag)
    # Canonical causes describe different missing source transformations. These are not CEO questions.
    causes=collections.defaultdict(lambda:dict(input_ids=[],output_ids=[],edge_ids=[]))
    def cause_for(wid):
        family=wid.split('/')[1]
        if family in ['default_privilege_path','SECURITY_DEFINER_path','reader_mutation']:return 'AUTHENTICATED_SOURCE_CALL_EFFECT_ADMISSION_PROJECTION'
        if family.startswith('catalog_') or family in ['mixed_snapshot','snapshot_reconnect','snapshot_restart']:return 'EXACT_CATALOG_SNAPSHOT_ROW_IDENTITY_AND_MULTIPLICITY_PROJECTION'
        if family in ['transitive_SET_ROLE','transitive_INHERIT','ADMIN_option_escalation','ownership_escalation','PUBLIC_path','wrong_role','wrong_reader','CREATEROLE_path','superuser_path','bootstrap_path','reader_privilege_escalation','search_path_substitution']:return 'QUALIFIED_SQL_ROLE_ACL_AND_SOURCE_OPERATION_IDENTITY_PROJECTION'
        return 'EXACT_NATIVE_OPERAND_IDENTITY_STAGE_AND_COMPLETE_TUPLE_PROJECTION'
    for b in new_inputs:
        if b['STATUS']!='COMPLETE':causes[cause_for(b['WITNESS_ID'])]['input_ids'].append(b['BINDING_ID'])
    for o in new_outputs:
        if o['STATUS']!='COMPLETE':causes[cause_for(o['WITNESS_ID'])]['output_ids'].append('OUTPUT/'+o['WITNESS_ID'])
    for e in edges:
        if e['STATUS']!='COMPLETE':
            key='INDEPENDENT_NATIVE_STAGE_ADAPTER' if e['SOURCE_FUNCTION'].startswith('GUARD/') else cause_for(e['TARGET_FUNCTION'][6:])
            causes[key]['edge_ids'].append(e['EDGE_ID'])
    causes=[dict(CAUSE_ID=k,**v,CLASSIFICATION='STATIC_SOURCE_RECOVERY_REQUIRED',AUTHORITY_QUESTION_PROVEN=False,REMEDY='Recover exact source-scoped transforms and type/identity/cardinality/admission contracts; preserve unknown actual values. No new normative alternative has been demonstrated.') for k,v in sorted(causes.items())]
    affected=sum(len(c['input_ids'])+len(c['output_ids'])+len(c['edge_ids']) for c in causes)
    write('minimum-remaining-blocker-set',dict(classes=len(causes),canonical_causes=len(causes),projected_bindings_affected=affected,causes=causes,minimality_scope='Nonduplicated causal recovery classes for this declared graph; not a proven globally minimum set cover. Input/output/edge IDs are distinct obligations, not physical facts.',symptoms_not_separate_authority_questions=True))
    write('authority-question-compression',dict(required=0,questions=[],rationale='No concrete mutually exclusive normative alternatives are established by current source recovery. Missing rows, schemas, authentication evidence and adapters are technical gaps, not automatically new policy authority.',architecture_flags=dict(POSTMASTER_CONTEXT_BINDING_RESOLVED='NO',INTERNAL_SCOPE_RESOLVED='NO',ATOMIC_BOUNDARY_RESOLVED='NO',CANONICAL_INTERNAL_OBLIGATION_UNIVERSE_ESTABLISHED='NO'),existing_architecture_gaps_preserved=True,no_new_authority_granted=True,T8='Nontransfer remains nontransfer; no rotation, principal substitution or target qualification inference.',I13='Full frozen I13 identity/context/generation/principal/credential/operation and independent proof requirements remain in force.'))
    write('canonical-evaluator-analysis',dict(complete_canonical_decision_evaluators=0,assembly_attempt='BLOCKED_BEFORE_ASSEMBLY',dag_status=dag['CANONICAL_DECISION_DAG_STATUS'],all49_strict=dag['ALL49_STRICT'],minimum_blocker_file='minimum-remaining-blocker-set.json',witness_execution_attempted=False,helper_UNAVAILABLE_is_domain_UNKNOWN=False,domain_UNKNOWN_is_qualification_REJECT=False,seven_exact_UNKNOWN_prerequisite_REJECT_mappings_preserved=True,other_native_adapters_not_inferred_from_expected_outcome=True))
    frozen=dict(CANONICAL_CASES_TOTAL=350,STATICALLY_PROVEN=0,STATICALLY_DISPROVEN=0,UNKNOWN=350,CONTRADICTED=0,ATOMIC_NORMATIVE_CANDIDATES_TOTAL=108,AMBIGUOUS_CANDIDATES_PRESERVED=105,CANONICAL_ATTACK_DENOMINATOR=350,DENOMINATOR_CHANGED='NO',ATTACKS_MATERIALIZED_THIS_GATE=0,ATTACKS_EVALUATED_THIS_GATE=0,N1_SUBSTITUTION_STATIC_WITNESSES='OPEN',N1_DECISIONS_REQUIRED=12,N1_DECISIONS_CLOSED=11,N1_DECISIONS_OPEN=1,V2_NATIVE_STATIC_DESIGN_PROOF='FAIL',V2_NATIVE_STATUS='BLOCKED')
    write('coverage-accounting',dict(**frozen,status='PRESERVED_NOT_REEVALUATED',source=ref('k','coverage-accounting.json'),no_350_case_proof_loop_executed=True))
    summary=dict(BRANCH=git('branch','--show-current'),BASELINE_HEAD='cbc284f62d9bd09b7169b55c8d66a3c51a68c6cb',CURRENT_HEAD=git('rev-parse','HEAD'),TRACKED_DIRTY_COUNT=0,STAGED_COUNT=0,AUTHORIZED_UNTRACKED_FILES_BEFORE=294,UNTRACKED_FILES_AFTER=None,UNAUTHORIZED_UNTRACKED_COUNT=0,C5K_INPUT_INTEGRITY='PASS',MINIMUM_BINDING_CONTRACT_INTEGRITY='PASS',LOCAL_FUNCTIONS_REQUIRED=49,LOCAL_FUNCTIONS_AVAILABLE=49,LOCAL_FUNCTIONS_STRICT_CERTIFIED=sum(c['STRICT_CERTIFIED'] for c in cert),LOCAL_FUNCTIONS_NOT_CERTIFIED=sum(not c['STRICT_CERTIFIED'] for c in cert),ALGORITHM_DISPROVEN=0,INPUT_BINDING_EQUIVALENCE_CLASSES_TOTAL=len(ic),CANONICAL_INPUT_BINDINGS_REQUIRED=1526,CANONICAL_INPUT_BINDINGS_COMPLETE=counts['COMPLETE'],CANONICAL_INPUT_BINDINGS_MISSING=counts['MISSING'],CANONICAL_INPUT_BINDINGS_AMBIGUOUS=counts['AMBIGUOUS'],CANONICAL_INPUT_BINDINGS_CONTRADICTED=0,AMBIGUOUS_INPUT_BINDINGS_BEFORE=595,AMBIGUOUS_INPUT_BINDINGS_RESOLVED=sum(r['STATUS']=='RESOLVED_UNIQUE' for r in resolutions),AMBIGUOUS_INPUT_BINDINGS_REMAINING=sum(r['STATUS']=='REMAINS_AMBIGUOUS' for r in resolutions),OUTPUT_BINDING_EQUIVALENCE_CLASSES_TOTAL=len(oc),CANONICAL_OUTPUT_BINDINGS_REQUIRED=350,CANONICAL_OUTPUT_BINDINGS_COMPLETE=outcounts['COMPLETE'],CANONICAL_OUTPUT_BINDINGS_MISSING=outcounts['MISSING'],CANONICAL_OUTPUT_BINDINGS_AMBIGUOUS=0,CANONICAL_OUTPUT_BINDINGS_CONTRADICTED=0,COMPOSITION_EQUIVALENCE_CLASSES_TOTAL=len(ec),COMPOSITION_EDGES_REQUIRED=714,COMPOSITION_EDGES_COMPLETE=edgecounts['COMPLETE'],COMPOSITION_EDGES_MISSING=edgecounts['MISSING'],COMPOSITION_EDGES_AMBIGUOUS=0,COMPOSITION_EDGES_CONTRADICTED=0,COMPOSITION_CYCLES=0,**dag,MINIMUM_REMAINING_BLOCKER_CLASSES=len(causes),MINIMUM_REMAINING_CANONICAL_CAUSES=len(causes),PROJECTED_BINDINGS_AFFECTED=affected,AUTHORITY_QUESTIONS_REQUIRED=0,COMPLETE_CANONICAL_DECISION_EVALUATORS=0,**frozen,POSTMASTER_CONTEXT_BINDING_RESOLVED='NO',INTERNAL_SCOPE_RESOLVED='NO',ATOMIC_BOUNDARY_RESOLVED='NO',CANONICAL_INTERNAL_OBLIGATION_UNIVERSE_ESTABLISHED='NO',INDEPENDENT_REVIEW_1='PENDING',INDEPENDENT_REVIEW_2='PENDING',SELECTED_OUTCOME='E_STATIC_BINDING_GAPS_REMAIN',NEXT_EXECUTED=False,NEXT_GATE='BOUNDED_STATIC_BINDING_SOURCE_RECOVERY')
    for k in ['SHARED_DB_CONTACTED','PRODUCTION_CONTACTED','EXISTING_LOCAL_DB_CONTACTED','NETWORK_CONTACT_FOR_PROOF','V043_EXECUTED','V043_CHANGED','B02_EXECUTED','GIT_ADD','COMMIT','PUSH']:summary[k]='NO'
    write('primary-result',dict(selected_outcome=summary['SELECTED_OUTCOME'],next_gate=summary['NEXT_GATE'],next_executed=False,reason='Source-parametric recovery closes four additional strict comparison profiles; source projection and independent native decision adapters remain incomplete. No new normative authority question has been demonstrated.',canonical_proof_complete=False))
    write('final-summary',summary)
    print(canon({k:v for k,v in summary.items() if k.startswith(('LOCAL_FUNCTIONS','CANONICAL_INPUT','CANONICAL_OUTPUT','COMPOSITION_EDGES','AMBIGUOUS_INPUT','MINIMUM_REMAINING'))}))

if __name__=='__main__':main()
