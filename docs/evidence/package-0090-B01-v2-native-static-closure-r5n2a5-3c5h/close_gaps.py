"""C5H evidence-only decomposition, source-literal recovery and predicate work.

Never imports historical generators. Never runs SQL, native code or a network API.
"""
import ast
import collections
import copy
import functools
import hashlib
import json
import pathlib
import subprocess
import sys
sys.dont_write_bytecode=True
from static_evaluator import parse, observe, inputs_for, operators_for, dependencies_for

P=pathlib.Path(__file__).resolve().parent
R=P.parents[2]
G=P.with_name(P.name[:-1]+'g')
F=P.with_name(P.name[:-1]+'f')
D=P.with_name(P.name[:-1]+'d')
N=R/'docs/evidence/package-0090-B01-v2-native-static-closure-r5n'
N1=N.with_name(N.name+'1')
def read(p):return json.loads(p.read_text(encoding='utf-8'))
@functools.lru_cache(maxsize=None)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def rel(p):return p.relative_to(R).as_posix()
def write(n,x):(P/n).write_text(json.dumps(x,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True).strip()
def ref(p,pointer):return {'path':rel(p),'sha256':sha(p),'pointer':pointer}

# C5H files already created are excluded from preexisting authorized accounting.
old=read(G/'preflight.json')['historical_sha256']
old.update(read(G/'SHA256-MANIFEST.json')['files'])
old[rel(G/'SHA256-MANIFEST.json')]=sha(G/'SHA256-MANIFEST.json')
assert len(old)==9270
assert all(sha(R/p)==h for p,h in old.items())
prior=set(read(G/'resumption-reconciliation.json')['paths'])
prior.update(read(G/'SHA256-MANIFEST.json')['files'])
prior.add(rel(G/'SHA256-MANIFEST.json'))
assert len(prior)==171
untracked=set(git('ls-files','--others','--exclude-standard').splitlines())
assert not prior-untracked
assert all(p.startswith(rel(P)+'/') for p in untracked-prior)
assert git('rev-parse','--show-toplevel').lower()==R.as_posix().lower()
assert git('branch','--show-current')=='checkpoint/package-0090-cloud-handoff'
assert git('rev-parse','HEAD')=='451265ff5b3d286eb4d27c4b3817c2f558f30123'
assert not git('diff','--name-only') and not git('diff','--cached','--name-only')
assert subprocess.run(['git','merge-base','--is-ancestor','cbc284f62d9bd09b7169b55c8d66a3c51a68c6cb','HEAD'],cwd=R).returncode==0
summary_g=read(G/'final-summary.json')
assert summary_g['UNKNOWN']==350 and summary_g['UNTRACKED_FILES_AFTER']==171
assert summary_g['SELECTED_OUTCOME']=='C_STATIC_WITNESS_GAPS_REMAIN'
packets=read(G/'canonical-350-proof-packet-registry.json')['packets']
assert len(packets)==350 and len({p['WITNESS_ID'] for p in packets})==350
source=read(F/'derived-canonical-350-registry.json')['case_records']
assert all(p['AVAILABLE_INPUTS']['canonical_record']==s for p,s in zip(packets,source))
write('preflight.json',{'status':'PASS','repository':str(R),'branch':git('branch','--show-current'),'head':git('rev-parse','HEAD'),'baseline':'cbc284f62d9bd09b7169b55c8d66a3c51a68c6cb','baseline_ancestor':True,'authorized_untracked_before':171,'authorized_paths':sorted(prior),'historical_sha256':old,'tracked_dirty':0,'staged':0,'V043_sha256':read(G/'preflight.json')['V043_sha256'],'no_historical_repair':True})
write('c5g-input-integrity.json',{'status':'PASS','manifest':ref(G/'SHA256-MANIFEST.json',''),'manifest_entries_verified':22,'historical_hashes_verified':9270,'packets':350,'unique_ids':350,'packet_hashes':{p['WITNESS_ID']:canon(p) for p in packets},'required_C5G_artifacts':[ref(G/n,'') for n in ['final-summary.json','primary-result.json','canonical-350-proof-packet-registry.json','static-evaluation-results.json','runtime-required-contracts.json']]})

library=read(D/'schema-library.json');schemas=library['schemas'];models=read(D/'baseline-models.json')['models']
families=read(D/'family-descriptors.json')['families']
abi=read(N/'native-message-abi.json')
codec=read(N/'native-identity-codec.json')
security=read(N1/'catalog-security-predicates.json')
catalog={k for k in schemas if k.startswith('CATALOG/')}
identities={k for k in schemas if k.startswith('IDENTITY/')}
registries={k for k in schemas if k.startswith('REGISTRY/')}
native_views={'CURRENT_SUBJECT_IDENTITY','CURRENT_WORK_ONE_USE','PRIVATE_RESOURCE_CUSTODY','PENDING_NEW_QUALIFICATION','GENERATION_AUTHORITY_CLAIM'}

def schema_fields(schema_id):
    return schemas[schema_id]['fields']

def choose_schemas(view,family,participant):
    chosen=set()
    if view in native_views:
        chosen|=identities|registries|{'bootstrap_context_schema','dependency_node_schema','dependency_edge_schema','work_revision_schema'}
        if view!='GENERATION_AUTHORITY_CLAIM':chosen|={f'FRAME/{participant}/CHALLENGE',f'FRAME/{participant}/RESPONSE'}
    if view=='SNAPSHOT_APPLICABILITY':chosen|=catalog|{'bootstrap_context_schema'}
    if view=='CLOSED_READER_AUTHORITY_MODEL':
        names={'pg_roles'}
        if family in {'transitive_SET_ROLE','transitive_INHERIT','ADMIN_option_escalation','SECURITY_DEFINER_path'}:names|={'pg_auth_members','pg_database'}
        if family in {'ownership_escalation','PUBLIC_path','search_path_substitution','reader_mutation','SECURITY_DEFINER_path'}:names|={'pg_namespace','pg_class'}
        if family in {'default_privilege_path','SECURITY_DEFINER_path'}:names|={'pg_namespace','pg_proc','pg_default_acl','pg_depend'}
        chosen|={'CATALOG/pg_catalog.'+n for n in names}
    return sorted(chosen)

# Predicate IDs deliberately identify native violation templates, not full
# canonical proof/qualification pipelines. Full proof additionally needs fixture
# constraints, source decision and no-new-authority observations.
blocked_ops={'REACHABLE','HAS_ADMIN_OPTION','EXISTS_EFFECTIVE_CREATOR_DEFAULT','HAS_SECURITY_DEFINER_PATH','HAS_UNEXPECTED_WRITE_PATH'}
predicates={};for_family={}
for family,descriptor in families.items():
    expression=descriptor['violation_predicate'];tree=parse(expression)
    pid='PREDICATE/'+canon({'native_violation_expression':expression})[:20]
    for_family[family]=pid
    item=predicates.setdefault(pid,{'PREDICATE_ID':pid,'expression':expression,'program':tree,'families':[],'source':ref(D/'family-descriptors.json','/families/'+family+'/violation_predicate'),'INPUT_SCHEMA':{'explicit_operands':inputs_for(tree),'all_required_operands_and_structured_dependencies':dependencies_for(tree),'structured_operator_dependencies':'See evaluator-authority-analysis.json; no opaque all-valid or witness-pass operand.'},'operators':operators_for(tree),'scope':'Native violation subpredicate; not a complete canonical witness decision evaluator.'})
    item['families'].append(family)
    unsupported=sorted(set(item['operators'])&blocked_ops)
    item['status']='OTHER_BLOCKED' if unsupported else 'DERIVED_C5H'
    item['unimplemented_full_source_operations']=unsupported
    item['EVALUATOR_ID']='EVALUATOR/'+pid.split('/')[1]
    item['EVALUATOR_SOURCE']=ref(P/'static_evaluator.py','')
    item['DETERMINISTIC_RULE']=tree
    item['RULE_AUTHORITY_SOURCE']=[ref(D/'family-descriptors.json','/model_operator_semantics'),ref(N1/'catalog-security-predicates.json','/predicates')]
    item['RULE_AUTHORITY_HASH']=[sha(D/'family-descriptors.json'),sha(N1/'catalog-security-predicates.json')]
    item.update({'EXPECTED_RESULT_NOT_CONSUMED':'YES','SIDE_EFFECT_FREE':'YES','DATABASE_ACCESS':'NO','NETWORK_ACCESS':'NO'})
assert len(predicates)==49

# Validate actual generic code independently of any canonical expected outcome.
# Test scalars/labels are interpreter unit vectors, never canonical fixture IDs.
unit=[]
def test(name,expression,inputs,expected):
    observed=observe(parse(expression),inputs)
    assert observed['availability']=='AVAILABLE' and observed['value']==expected,(name,observed)
    unit.append({'name':name,'expression':expression,'inputs':inputs,'observed':observed,'scope':'Generic interpreter unit vector, not canonical witness/attack fixture'})
test('typed NE true','NE(a,b)',{'a':3,'b':4},True)
test('typed NE false','NE(a,b)',{'a':3,'b':3},False)
test('exact nested tuple equality','EQ(a,b)',{'a':{'x':[1,2]},'b':{'x':[1,2]}},True)
test('ordinary boolean precedence','FALSE AND FALSE OR TRUE',{},True)
test('prefix NOT','TRUE AND NOT FALSE',{},True)
test('integer subtraction and threshold','GT(now-captured,limit)',{'now':9,'captured':4,'limit':3},True)
test('bijection retains duplicates','BIJECTION(a,b)',{'a':[1,1],'b':[1,2]},False)
test('natural key duplicate','EXISTS_DUPLICATE_NATURAL_KEY(rows)',{'rows':{'key_fields':['k'],'rows':[{'k':1},{'k':1}]}},True)
test('natural key missing','MISSING(row)',{'row':{'expected_key':[1],'key_fields':['k'],'rows':[{'k':2}]}},True)
test('PUBLIC infix NOT parse','HAS_PUBLIC_PRIVILEGE(r,REL(pg_catalog.pg_auth_members),UPDATE) AND NOT FIXED_SOURCE_OPERATION_ALLOWS(UPDATE)',{'r':2,'object_acls':{'pg_catalog.pg_auth_members':[{'grantee':0,'privilege':'UPDATE'}]},'fixed_source_operation_allowlist':[]},True)
for expression,inputs in [('NE(a,b)',{'a':True,'b':1}),('NE(a,b)',{'a':1}),('AND(a,b)',{'a':False})]:
    observed=observe(parse(expression),inputs);assert observed['availability']=='UNAVAILABLE'
    unit.append({'name':'missing/type mismatch does not become result','expression':expression,'observed':observed})
write('evaluator-verification.json',{'status':'PASS','tests':unit,'canonical_witnesses_evaluated':0,'canonical_attacks_materialized':0,'canonical_attacks_evaluated':0})

fixture_registry=[];field_inventory=[];gaps=[];evaluations=[];observations=[];binding_candidates=[]
all_before=0;all_derived=0;all_missing=0
for index,packet in enumerate(packets):
    witness=packet['WITNESS_ID'];participant,family=witness.split('/',1)
    record=packet['AVAILABLE_INPUTS']['canonical_record'];baseline=record['BASELINE_STATE'];model=models[baseline['library_model_id']]
    view=baseline['selected_view'];descriptor=families[family];pid=for_family[family];predicate=predicates[pid]
    entries=[]
    operand_bindings={}
    def add(name,type_name,definition_source,value=None,state='MISSING',rule=None,value_source=None):
        existing=next((e for e in entries if e['FIELD_NAME']==name),None)
        if existing:
            assert existing['FIELD_VALUE']==value and existing['TYPE']==type_name,(witness,name)
            existing.setdefault('additional_source_selections',[]).append(definition_source)
            return
        entries.append({'FIELD_NAME':name,'TYPE':type_name,'FIELD_VALUE':value,'state':state,'FIELD_SOURCE':value_source or definition_source,'FIELD_SOURCE_HASH':(value_source or definition_source)['sha256'],'DEFINITION_SOURCE':definition_source,'DERIVATION_RULE':rule or ('Direct frozen literal selection' if state=='AVAILABLE_BEFORE' else None),'DERIVATION_RULE_SOURCE':definition_source,'POSSIBLE_SOURCE':None if state!='MISSING' else {'immutable_source':definition_source,'requirement':'A complete source-bound concrete value OR mechanically checked symbolic binding/constraint trace; declaration/string/hash alone is insufficient. No live DB/process observation required or authorized.'}})
    mref=ref(D/'baseline-models.json','/models/'+baseline['library_model_id'].replace('/','~1'))
    bref=ref(F/'derived-canonical-350-registry.json',f'/case_records/{index}/BASELINE_STATE')
    def operand(name,value,source_ref,rule):
        if name not in dependencies_for(predicate['program']):return
        operand_bindings[name]={'value':value,'source':source_ref,'derivation_rule':rule,'scope':'Frozen static model fragment, not a measured live-system fact'}
        add('predicate_operand/'+name,'exact frozen model operand',source_ref,value,'DERIVED_C5H',rule)
    if baseline['exact_variant_state'].get('phase')=='ACTIVE':
        operand('phase','ACTIVE',bref,'Select exact structured phase literal; do not fabricate an enrollment record')
    if family=='credential_inheritance':
        assert baseline['exact_variant_state']['target_qualification_receipts'].startswith('EMPTY as an explicit model fact')
        operand('target_qualification_receipts',[],bref,'Recover explicitly empty qualification-receipt model set, not a failed query')
    if family=='reused_credential':
        assert descriptor['after'].startswith('CONSUMED') and 'NEW_AUTHORITY' in descriptor['after']
        sr=ref(D/'family-descriptors.json','/families/'+family+'/after')
        operand('authorization_consumed',True,sr,'Interpret exact CONSUMED work-use state after specified model replacement')
        operand('request_requires_new_authority',True,sr,'Interpret explicit NEW_AUTHORITY request; do not infer a publication or grant')
    if family=='bootstrap_path':
        assert 'operation=PRE_ENROLLMENT_PROVISION' in descriptor['after'] and 'authority_origin=HOST_ROOT,phase=ACTIVE' in descriptor['after']
        sr=ref(D/'family-descriptors.json','/families/'+family+'/after')
        for k,v in [('claim.phase','ACTIVE'),('claim.operation','PRE_ENROLLMENT_PROVISION'),('claim.authority_origin','HOST_ROOT')]:operand(k,v,sr,'Parse explicit OperationClaim field literal from exact replacement expression; caller identity remains unbound')
    if family=='search_path_substitution':
        assert descriptor['after'].startswith('NAMESPACE_NAME_LOOKUP(')
        operand('candidate_resolution.kind','NAMESPACE_NAME_LOOKUP',ref(D/'family-descriptors.json','/families/'+family+'/after'),'Recover explicit tagged resolution variant; do not choose namespace/relation OIDs')
    # Structured literals already present in C5G, never OS/principal identities.
    add('subject.participant_enum','u16',mref,model['participant_enum'],'AVAILABLE_BEFORE',value_source=ref(N/'native-message-abi.json','/actor_enum/'+participant))
    for actor,a in model['actor_blocks'].items():
        add('actor_enum.'+actor,'u16',mref,a['enum'],'AVAILABLE_BEFORE',value_source=ref(N/'native-message-abi.json','/actor_enum/'+actor))
    add('current_generation','u64 bounded [2,2^64-2]',mref)
    if family=='credential_inheritance':add('source_generation','u64=current_generation-1',mref)
    # Expand relevant source-schema leaves. [] denotes a quantified collection
    # slot; it does NOT claim a known row count or complete instantiated rows.
    chosen=choose_schemas(view,family,participant)
    for sid in chosen:
        s=schemas[sid];source_ref=s['source']
        if sid.startswith('IDENTITY/'):
            actors=sorted({participant,model['actual_response_sender'],model['actual_challenge_sender']})
            prefixes=[f'identity[{a}]/{sid}' for a in actors]
        elif sid.startswith('CATALOG/'):
            prefixes=['catalog_rows[]/'+sid]
            add('cardinality/'+sid,'exact collection cardinality',source_ref)
        else:prefixes=[sid]
        for prefix in prefixes:
            for fi,field in enumerate(s['fields']):
                fieldname=field.get('name',field.get('projected_name'))
                source_field_ref=ref(D/'schema-library.json','/schemas/'+sid.replace('/','~1')+'/fields/'+str(fi))
                value=None;state='MISSING';value_source=None
                if fieldname=='participant_id' and not sid.startswith('CATALOG/'):
                    actor=prefix.split(']')[0][9:] if prefix.startswith('identity[') else participant
                    value=abi['actor_enum'][actor];state='DERIVED_C5H';value_source=ref(N/'native-message-abi.json','/actor_enum/'+actor)
                add(prefix+'/'+fieldname,field['type'],source_field_ref,value,state,'Project exact source actor enum; not an OS subject/SQL OID or credential' if state=='DERIVED_C5H' else None,value_source)
        # Expanded digest preimages are tracked separately from digest fields.
        if sid.startswith('IDENTITY/'):
            add('codec_trace/'+sid,'complete canonical tagged encoding/hash derivation',ref(N/'native-identity-codec.json','/encoding'))
    # Include exact nested native records, not merely parent digest/record tags.
    if any(sid.startswith('FRAME/') for sid in chosen):
        nested=[('input_record_schema',abi['input_record_schema']),('result_record_schemas/'+participant,abi['result_record_schemas'][participant])]
        for label,definition in nested:
            fields=definition.get('fields',definition.get('field_order',[])) if isinstance(definition,dict) else definition
            for fi,field in enumerate(fields):
                if isinstance(field,str):name=field;ty='exact nested source field'
                else:name=field.get('name',field.get('field'));ty=field.get('type','exact nested source type')
                add('NESTED/'+label+'/'+str(name),ty,ref(N/'native-message-abi.json','/'+label+'/'+str(fi)))
    # Source-declared design projections have actual typed leaves too. Expand
    # them explicitly instead of counting an entire PrincipalRef/snapshot/work
    # group as one available value.
    design_types={'PrincipalRef'}
    if view=='CURRENT_SUBJECT_IDENTITY':design_types.add('ModuleMapEntry')
    if view=='PRIVATE_RESOURCE_CUSTODY':design_types.add('PrivateResourceRef')
    if view in {'CURRENT_WORK_ONE_USE','PENDING_NEW_QUALIFICATION'}:design_types.add('WorkUse')
    if view=='GENERATION_AUTHORITY_CLAIM':design_types.add('AuthorityClaim')
    if view=='SNAPSHOT_APPLICABILITY':design_types.add('SnapshotHeader')
    if family=='search_path_substitution':design_types.add('ResolutionExpression')
    if family=='reader_mutation':design_types.add('EffectLeaf')
    if family=='bootstrap_path':design_types.add('OperationClaim')
    if family in {'PUBLIC_path','default_privilege_path','SECURITY_DEFINER_path'}:design_types.add('ACLRow')
    for dtype in sorted(design_types):
        definition=library['design_only_model_types'][dtype]
        for fi,spec in enumerate(definition.get('fields',[])):
            for component in spec.split(' and '):
                name,_,ty=component.partition(':')
                add('DESIGN/'+dtype+'/'+name,ty or 'exact source design field',ref(D/'schema-library.json','/design_only_model_types/'+dtype+'/fields/'+str(fi)))
        for variant,fields in definition.get('variants',{}).items():
            for name,ty in fields.items():
                add('DESIGN/'+dtype+'/'+variant+'/'+name,ty,ref(D/'schema-library.json','/design_only_model_types/'+dtype+'/variants/'+variant+'/'+name))
    # Preserve all named selected-view constraints as obligations, not TRUE flags.
    for ci,constraint in enumerate(model['baseline_constraints']):
        add('source_constraint_trace/'+str(ci),'mechanical applicability/constraint derivation',ref(D/'baseline-models.json',mref['pointer']+'/baseline_constraints/'+str(ci)))
    for name,definition in model['required_typed_parameters'].items():
        # Record whether the parameter group applies; no silent full-universe
        # assertion. Non-selected frame groups do not create target enrollments.
        if name in {'policy','principals'} or (view in {'SNAPSHOT_APPLICABILITY','CLOSED_READER_AUTHORITY_MODEL'} and name in {'source_membrane','source_effect_and_ACL_model','roles_for_graph_fixture','graph_fixture_objects'}):
            add('binding_trace/'+name,'complete applicable parameter binding proof',mref)
    add('mutation.source_bound_post_state','exact transformed state and dependent canonical digests',ref(D/'family-descriptors.json','/families/'+family))
    add('observation.no_new_authority','independently calculated pre/post authority/work/publication delta',bref)
    if view=='CLOSED_READER_AUTHORITY_MODEL':
        # These exact role attributes are explicit frozen baseline model facts.
        for flag in ['rolsuper','rolcreaterole','rolbypassrls']:
            add('baseline.catalog.pg_roles[R].'+flag,'bool',bref,False,'DERIVED_C5H','Extract explicit R flags FALSE from exact_variant_state.role_rows; R remains the source symbolic SQL role, never a native participant identity')
    if descriptor['before']=='FALSE' and descriptor['after'].startswith('TRUE;'):
        add('baseline.'+descriptor['selector'],'bool',ref(D/'family-descriptors.json','/families/'+family+'/before'),False,'DERIVED_C5H','Parse the exact frozen FALSE literal')
        add('post.'+descriptor['selector'],'bool',ref(D/'family-descriptors.json','/families/'+family+'/after'),True,'DERIVED_C5H','Apply exact FALSE->TRUE replacement in an isolated field fragment; no complete catalog row or runtime grant inferred')
        flag=descriptor['selector'].split('.')[-1]
        fragment=observe({'op':'EQ','args':[{'input':'actual_flag'},{'literal':True}]},{'actual_flag':True})
        observations.append({'WITNESS_ID':witness,'scope':'Independent field-fragment observation, not full canonical predicate or witness proof','BASELINE_FIELD':False,'MUTATION':'replace with frozen TRUE literal','POST_MUTATION_FIELD':True,'OBSERVED_RESULT':fragment,'EXPECTED_RESULT_CONSUMED':False,'unbound_row_identity':True,'full_fixture_complete':False})
    # Generation arithmetic can be established without choosing an actual G.
    if family in {'wrong_generation','stale_generation'}:
        delta=1 if family=='wrong_generation' else -1
        add('mutation.generation_delta','integer',ref(D/'family-descriptors.json','/families/'+family+'/after'),delta,'DERIVED_C5H','Parse frozen G+1 / G-1 affine transformation; do not choose G')
        add('source_bound.generation_range','closed u64 interval',mref,[2,2**64-2],'DERIVED_C5H','Parse exact frozen 2 <= G <= 2^64-2')
        # Independent bounded-integer algebra: shifted term differs iff delta !=0.
        result=observe(parse('NE(delta,zero)'),{'delta':delta,'zero':0})
        observations.append({'WITNESS_ID':witness,'scope':'Bounded affine subpredicate only; no concrete/successor generation identity invented','OBSERVED_RESULT':result,'DERIVATION':'For integer G in frozen range, (G+d)-G=d; both G+d and G are u64 and d !=0','full_fixture_complete':False,'EXPECTED_RESULT_CONSUMED':False})
    names=[e['FIELD_NAME'] for e in entries];assert len(names)==len(set(names)),witness
    before=[e for e in entries if e['state']=='AVAILABLE_BEFORE'];derived=[e for e in entries if e['state']=='DERIVED_C5H'];missing=[e for e in entries if e['state']=='MISSING']
    assert len(before)+len(derived)+len(missing)==len(entries)
    all_before+=len(before);all_derived+=len(derived);all_missing+=len(missing)
    # Generate deterministic source-named binding candidates, without asserting
    # that declaring a term discharges its range/reference/encoding constraints.
    candidates=[{'FIELD_NAME':e['FIELD_NAME'],'typed_symbol':[baseline['library_model_id'],participant,e['FIELD_NAME']],'type':e['TYPE'],'source_rule':mref,'status':'CANDIDATE_NOT_VALIDATED_NOT_ACCEPTED_AS_FIELD_VALUE'} for e in missing if not e['FIELD_NAME'].startswith(('cardinality/','source_constraint_trace/','codec_trace/','binding_trace/','mutation.','observation.'))]
    binding_candidates.append({'WITNESS_ID':witness,'symbolic_candidates':candidates,'reason_not_fixture_completion':'Exact typed symbol names recoverable. Constraint, collection cardinality/row and full encoding/hash bindings remain independently unestablished; do not infer valid state from naming terms.'})
    fixture={'WITNESS_ID':witness,'C5G_PACKET_HASH':canon(packet),'FIXTURE_COMPLETE':'NO','FIELD_ACCOUNTING_UNIT':'Declared schema-leaf/binding obligations; [] is quantified, not a claimed actual row count','available_before':before,'materialized_fields_C5H':derived,'still_missing':missing,'applicable_source_schemas':chosen,'selected_view':view,'predicate_operand_bindings':operand_bindings,'complete_native_decision_evaluator_available':False}
    fixture['C5H_FIXTURE_HASH']=canon(fixture)
    fixture_registry.append(fixture)
    field_inventory.append({'WITNESS_ID':witness,'required':entries,'required_count':len(entries),'available_before':len(before),'derived_C5H':len(derived),'missing':len(missing)})
    # Exact operands are inventoried separately from normative predicate text.
    operands=dependencies_for(predicate['program'])
    available_operands=sorted(operand_bindings)
    evaluator_ready=predicate['status']=='DERIVED_C5H'
    subpredicate_observation=observe(predicate['program'],{k:v['value'] for k,v in operand_bindings.items()}) if evaluator_ready else {'availability':'UNAVAILABLE','value':None,'reason':'Full source operator engineering incomplete'}
    gap={'WITNESS_ID':witness,'C5G_PROOF_PACKET_HASH':canon(packet),'REQUIRED_FIXTURE_FIELDS':names,'AVAILABLE_FIXTURE_FIELDS':[e['FIELD_NAME'] for e in before+derived],'MISSING_FIXTURE_FIELDS':[e['FIELD_NAME'] for e in missing],'MISSING_FIXTURE_FIELD_COUNT':len(missing),'FIXTURE_SOURCE_FOR_EACH_AVAILABLE_FIELD':{e['FIELD_NAME']:e['FIELD_SOURCE'] for e in before+derived},'POSSIBLE_SOURCE_FOR_EACH_MISSING_FIELD':{e['FIELD_NAME']:e['POSSIBLE_SOURCE'] for e in missing},'PREDICATE_ID':pid,'PREDICATE_DEFINITION_SOURCE':predicate['source'],'PREDICATE_INPUTS_REQUIRED':operands,'PREDICATE_INPUTS_AVAILABLE':available_operands,'PREDICATE_INPUTS_MISSING':sorted(set(operands)-set(available_operands)),'INDEPENDENT_EVALUATOR_EXISTS':'YES_SUBPREDICATE_ONLY' if evaluator_ready else 'NO_FULL_SOURCE_OPERATOR_IMPLEMENTATION','INDEPENDENT_EVALUATOR_SOURCE':predicate['EVALUATOR_SOURCE'],'EVALUATOR_CONSTRUCTION_POSSIBLE':'YES_FROM_FROZEN_SEMANTICS','EVALUATOR_CONSTRUCTION_AUTHORITY_SOURCE':predicate['RULE_AUTHORITY_SOURCE'],'RUNTIME_OBSERVATION_REQUIRED':'NOT_ESTABLISHED','RUNTIME_OBSERVATION_REASON':'Missing bound values/trace does not prove runtime necessity; static or checked symbolic binding remains authorized. No live system conformance claim is attempted.','AUTHORITY_GAP_EXISTS':'NO','AUTHORITY_GAP_DESCRIPTION':'No missing normative decision identified; missing field bindings, source constraints and mechanical evaluator work are evidence/engineering gaps. Frozen architectural questions are not resolved.','FINAL_GAP_CLASS':'COMPOUND_GAP','compound_components':[{'class':'MISSING_STATIC_FIELD_BINDINGS','fields':len(missing),'reason':'No complete source-bound concrete or validated symbolic instance in supplied packet'}, {'class':'MISSING_INDEPENDENT_CONSTRAINT_AND_DECISION_TRACE','reason':'Complete baseline/mutation/digest/non-grant trace absent; normative propositions are not observations'}]+([] if evaluator_ready else [{'class':'EVALUATOR_ENGINEERING_INCOMPLETE','operators':predicate['unimplemented_full_source_operations'],'authority_gap':False}]),'ARCHITECTURAL_DEPENDENCY':record['ARCHITECTURAL_DEPENDENCY'],'T8':record.get('T8_compatibility'),'I13':record['PRINCIPAL_CONTEXT']['I13']}
    gaps.append(gap)
    evaluations.append({'WITNESS_ID':witness,'FIXTURE_HASH':fixture['C5H_FIXTURE_HASH'],'EVALUATOR_HASH':sha(P/'static_evaluator.py'),'OBSERVED_RESULT':None,'NATIVE_SUBPREDICATE_OBSERVATION':subpredicate_observation,'EXPECTED_RESULT':packet['EXPECTED_RESULT'],'MATCH_STATUS':'NOT_EVALUABLE_INCOMPLETE_FIXTURE','PROOF_STATUS':'UNKNOWN','canonical_evaluation_executed':False,'input_gate_reason':{'missing_fields':len(missing),'native_predicate_interpreter':predicate['status'],'full_canonical_decision_evaluator':'NOT_COMPLETE'},'expected_source':packet['EXPECTED_RESULT_SOURCE']})

assert len(gaps)==len(fixture_registry)==len(evaluations)==350
ready=sum(p['status']=='DERIVED_C5H' for p in predicates.values())
write('350-gap-decomposition.json',{'total':350,'gaps':gaps,'all_compound_is_recomputed_not_assumed':True,'classification_rule':'Each record independently has missing typed-value/row bindings AND independent constraint/decision observations. The enum has no standalone nonrecoverable-yet-static-evidence gap class. COMPOUND_GAP does not assert authority or runtime necessity.'})
write('fixture-field-inventory.json',{'accounting_unit':'Per-witness declared source-schema-leaf and binding/trace obligations; quantified [] slots count once, not per unknown row. Actual instantiated field cardinality remains NOT_ESTABLISHED. Counts are not a claim of a complete finite row roster.','required_total':all_before+all_derived+all_missing,'available_before':all_before,'derived_C5H':all_derived,'still_missing':all_missing,'records':field_inventory})
write('fixture-source-provenance.json',{'records':[{'WITNESS_ID':f['WITNESS_ID'],'fields':f['available_before']+f['materialized_fields_C5H']} for f in fixture_registry],'recovery_search':{'scope':'Exact C5G packet AVAILABLE_INPUTS canonical/model/schema/artifact references, frozen D/F semantic libraries and their pinned source references; no unrelated live state/DB searched','concrete_native_values_source':ref(N/'native-identity-codec.json','/actual_values'),'concrete_native_values_declaration':codec['actual_values'],'symbolic_binding_rule':ref(D/'baseline-models.json','/models'),'historical_values_not_regenerated':True}})
write('derived-fixture-registry.json',{'total':350,'complete':0,'incomplete':350,'fixtures':fixture_registry})
write('symbolic-binding-attempts.json',{'total':350,'attempts':binding_candidates,'not_a_proof':'These are deterministic proposed term bindings, never asserted to be measured identities or verified whole fixtures.'})
write('unique-predicate-registry.json',{'total':49,'identity_policy':'SHA256 of exact native_violation_expression template; wrong/stale-generation share one expression. Role/case identity is retained separately. These are subpredicates, NOT49 complete canonical witness proof pipelines; seven scoped output mapping cases retain a separate typed policy.','predicates':list(predicates.values()),'seven_case_typed_output_policy':ref(F/'seven-artifact-overrides.json','/overrides')})
write('evaluator-inventory.json',{'UNIQUE_PREDICATES_TOTAL':49,'EVALUATORS_EXISTING':0,'EVALUATORS_DERIVED_C5H':ready,'EVALUATORS_AUTHORITY_BLOCKED':0,'EVALUATORS_RUNTIME_BLOCKED':0,'EVALUATORS_OTHER_BLOCKED':49-ready,'scope':'Native violation subpredicates only. Complete canonical decision/no-new-authority evaluators:0. Derived guard code does not close a canonical witness.','evaluators':list(predicates.values())})
write('evaluator-authority-analysis.json',{'new_normative_decisions':0,'expected_result_isolation':'static_evaluator.py receives program AST and normalized operand data only. It has no access to packets/expected outcomes or witness identities. The report layer retains expected result after evaluation eligibility is decided.','source_authority':[ref(D/'family-descriptors.json','/model_operator_semantics'),ref(N1/'catalog-security-predicates.json','/role_edge_rules'),ref(N1/'catalog-security-predicates.json','/predicates'),ref(N/'native-identity-codec.json','/encoding')],'operator_dependencies':{'EQ_NE_LT_GT_IN':'All exact typed operands; no coerce/unknown-to-zero conversion','MISSING':'Expected natural key, key-field list and actual row multiset','BIJECTION':'Both complete protected rosters; duplicates retained','role_flags':'Exactly one matched full source role row and bound role OID','HAS_PUBLIC_PRIVILEGE':'Fully normalized object ACL with PUBLIC oid0; null/default expansion provenance remains fixture requirement','REACHABLE_ADMIN':'Requires implicit database-owner edge composition as well as separately typed explicit options; blocked rather than approximated','DEFAULT':'Requires full source default ACL and actual creator/schema/future object semantics; blocked','SECURITY_DEFINER':'Requires execute/schema access, owner and independently verified body/effect closure; blocked','WRITE_PATH':'Requires full source-expanded effect reachability/admission; blocked'},'complete_canonical_decision_evaluators':0,'construction_limits':'Ready subpredicate evaluators are not full decision/non-grant traces. Missing other implementations are technical work; no project authority invented.'})
write('independent-static-evaluation.json',{'canonical_cases':evaluations,'canonical_evaluations_executed':0,'eligible_complete_fixtures':0,'field_fragment_observations':observations,'field_fragment_observations_total':len(observations),'any_fragment_promoted_to_proven':False,'maximum_evaluation_statement':'All fixtures tested for eligibility after per-field recovery and symbolic binding attempts. No complete canonical fixture exists in this derived registry; therefore none eligible under section9. This is not a claim that further technical static fixture/evaluator work is impossible.'})
write('authority-gap-registry.json',{'total':0,'gaps':[],'no_gap_fabricated':'No minimum missing normative decision demonstrated. Missing approved artifacts/source facts and unimplemented mechanical checks do not become project-authority requests.','unresolved_architecture_preserved':['POSTMASTER_CONTEXT_BINDING','INTERNAL_SCOPE','ATOMIC_BOUNDARY','CANONICAL_INTERNAL_OBLIGATION_UNIVERSE'],'new_architectural_answers':0})
write('runtime-necessity-analysis.json',{'positively_demonstrated_runtime_required':0,'runtime_executed':False,'cases':[{'WITNESS_ID':p['WITNESS_ID'],'RUNTIME_OBSERVATION_REQUIRED':'NOT_ESTABLISHED','STATIC_EVALUATION_INSUFFICIENT':'NOT_PROVEN','reason':'Unbound static source facts/checks do not establish runtime necessity; authorized mechanically checked symbolic fixtures remain a possible technical route.'} for p in packets]})
summary={'BRANCH':git('branch','--show-current'),'BASELINE_HEAD':'cbc284f62d9bd09b7169b55c8d66a3c51a68c6cb','CURRENT_HEAD':git('rev-parse','HEAD'),'TRACKED_DIRTY_COUNT':0,'STAGED_COUNT':0,'AUTHORIZED_UNTRACKED_FILES_BEFORE':171,'UNAUTHORIZED_UNTRACKED_COUNT':0,'C5G_INPUT_INTEGRITY':'PASS','CANONICAL_CASES_TOTAL':350,'PROOF_PACKETS_CONSUMED':350,'FIXTURES_TOTAL':350,'FIXTURES_ALREADY_COMPLETE':0,'FIXTURES_COMPLETED_C5H':0,'FIXTURES_STILL_INCOMPLETE':350,'FIXTURE_FIELDS_REQUIRED_TOTAL':all_before+all_derived+all_missing,'FIXTURE_FIELDS_AVAILABLE_BEFORE':all_before,'FIXTURE_FIELDS_DERIVED_C5H':all_derived,'FIXTURE_FIELDS_STILL_MISSING':all_missing,'FIXTURE_FIELD_COUNT_UNIT':'DECLARED_SCHEMA_LEAF_AND_BINDING_OBLIGATIONS_NOT_UNKNOWN_ROW_INSTANCES','UNIQUE_PREDICATES_TOTAL':49,'EVALUATORS_EXISTING':0,'EVALUATORS_DERIVED_C5H':ready,'EVALUATORS_AUTHORITY_BLOCKED':0,'EVALUATORS_RUNTIME_BLOCKED':0,'EVALUATORS_OTHER_BLOCKED':49-ready,'EVALUATOR_COUNT_SCOPE':'NATIVE_VIOLATION_SUBPREDICATES_ONLY','COMPLETE_CANONICAL_DECISION_EVALUATORS':0,'NO_GAP_STATICALLY_EVALUABLE':0,'FIXTURE_DERIVABLE_FROM_FROZEN_AUTHORITY':0,'FIXTURE_RECOVERABLE_FROM_IMMUTABLE_ARTIFACT':0,'EVALUATOR_DERIVABLE_FROM_FROZEN_SEMANTICS':0,'AUTHORITY_GAP':0,'RUNTIME_OBSERVATION_REQUIRED':0,'COMPOUND_GAP':350,'CONTRADICTION':0,'STATICALLY_PROVEN':0,'STATICALLY_DISPROVEN':0,'UNKNOWN':350,'CONTRADICTED':0,'SUBSTITUTION_WITNESSES_REQUIRED':350,'SUBSTITUTION_WITNESSES_PROVEN':0,'SUBSTITUTION_WITNESSES_UNKNOWN':350,'N1_SUBSTITUTION_STATIC_WITNESSES':'OPEN','N1_DECISIONS_REQUIRED':12,'N1_DECISIONS_CLOSED':11,'N1_DECISIONS_OPEN':1,'V2_NATIVE_STATIC_DESIGN_PROOF':'FAIL','V2_NATIVE_STATUS':'BLOCKED','PROJECT_AUTHORITY_TRANSITION':'T8','TRANSITION_RESOLVED':'YES','POSTMASTER_CONTEXT_BINDING_RESOLVED':'NO','INTERNAL_SCOPE_RESOLVED':'NO','ATOMIC_BOUNDARY_RESOLVED':'NO','CANONICAL_INTERNAL_OBLIGATION_UNIVERSE_ESTABLISHED':'NO','ATOMIC_NORMATIVE_CANDIDATES_TOTAL':108,'AMBIGUOUS_CANDIDATES_PRESERVED':105,'CANONICAL_ATTACK_DENOMINATOR':350,'DENOMINATOR_CHANGED':'NO','ATTACKS_MATERIALIZED_THIS_GATE':0,'ATTACKS_EVALUATED_THIS_GATE':0,'SHARED_DB_CONTACTED':'NO','PRODUCTION_CONTACTED':'NO','EXISTING_LOCAL_DB_CONTACTED':'NO','NETWORK_CONTACT_FOR_PROOF':'NO','V043_EXECUTED':'NO','V043_CHANGED':'NO','B02_EXECUTED':'NO','GIT_ADD':'NO','COMMIT':'NO','PUSH':'NO','SELECTED_OUTCOME':'OUTCOME_NOT_REPRESENTED','NEXT_EXECUTED':False,'NEXT_GATE':'BOUNDED_STATIC_FIXTURE_BINDING_AND_CANONICAL_EVALUATOR_COMPLETION'}
write('coverage-accounting.json',summary)
write('primary-result.json',{'selected_outcome':'OUTCOME_NOT_REPRESENTED','reason':'A requires350 proven; B requires some proven; C requires a missing normative decision; D requires demonstrated runtime necessity; E requires contradiction/disproof; F requires preflight failure. None is established. Do not fabricate authority/runtime or a proof to force an outcome.','scope_completed':'350 source-pinned gap records and incomplete fixture inventories; deterministic field recovery, symbolic term-binding attempts and independent field-fragment observations; native subpredicate evaluator construction/limitations inventoried.','scope_not_completed':'No full typed canonical fixture or full qualification/non-grant evaluator completed. No canonical witness proven or evaluated. Full closure objective remains unmet.','next_gate':summary['NEXT_GATE'],'next_gate_is_technical_not_project_authority':True})
write('final-summary.json',summary)
print(json.dumps({'fixtures':350,'required_field_obligations':all_before+all_derived+all_missing,'derived_fields':all_derived,'predicates':49,'native_subpredicate_evaluators_derived':ready,'full_canonical_proofs':0}))
