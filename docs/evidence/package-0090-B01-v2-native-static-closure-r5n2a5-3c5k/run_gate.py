"""C5K evidence only: source contracts, local functions, binding and DAG audit."""
import ast,collections,copy,functools,hashlib,itertools,json,pathlib,subprocess,sys
sys.dont_write_bytecode=True
import final_operators as new
from validate_local import validate_new

P=pathlib.Path(__file__).resolve().parent;R=P.parents[2]
def folder(letter):return P.with_name(P.name[:-1]+letter)
H,I,J,F,D=[folder(x) for x in ['h','i','j','f','d']]
N=R/'docs/evidence/package-0090-B01-v2-native-static-closure-r5n';N1=N.with_name(N.name+'1');A42=R/'docs/evidence/package-0090-B01-v2-native-static-closure-r5n2a4-2'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
@functools.lru_cache(maxsize=None)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def rel(p):return p.relative_to(R).as_posix()
def ref(p,pointer=''):return {'path':rel(p),'sha256':sha(p),'pointer':pointer}
def write(n,x):(P/n).write_text(json.dumps(x,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
def git(*args):return subprocess.check_output(['git',*args],cwd=R,text=True).strip()
def pure_load(path):
    namespace={};exec(compile(path.read_text(encoding='utf-8'),str(path),'exec'),namespace);return namespace

hist=read(J/'preflight.json')['historical_sha256'];hist.update(read(J/'SHA256-MANIFEST.json')['files']);hist[rel(J/'SHA256-MANIFEST.json')]=sha(J/'SHA256-MANIFEST.json')
assert len(hist)==9349 and all(sha(R/p)==h for p,h in hist.items())
prior=set(read(J/'preflight.json')['authorized_paths'])|set(read(J/'SHA256-MANIFEST.json')['files'])|{rel(J/'SHA256-MANIFEST.json')};assert len(prior)==250
actual=set(git('ls-files','--others','--exclude-standard').splitlines());assert not prior-actual and all(x.startswith(rel(P)+'/') for x in actual-prior)
assert git('rev-parse','--show-toplevel').lower()==R.as_posix().lower()
assert git('branch','--show-current')=='checkpoint/package-0090-cloud-handoff'
assert git('rev-parse','HEAD')=='451265ff5b3d286eb4d27c4b3817c2f558f30123'
assert not git('diff','--name-only') and not git('diff','--cached','--name-only')
assert subprocess.run(['git','merge-base','--is-ancestor','cbc284f62d9bd09b7169b55c8d66a3c51a68c6cb','HEAD'],cwd=R).returncode==0
js=read(J/'final-summary.json');assert js['LOCAL_PROGRAMS_AVAILABLE_WITH_DECLARED_SCOPE']==46 and js['UNKNOWN']==350
assert read(J/'unit-verification.json')['exhaustive_normalized_unit_graph_checks']==11664
assert (J/'independent-review-1.json').is_file() and (J/'independent-review-2.json').is_file()
predicates=read(H/'unique-predicate-registry.json')['predicates'];assert len(predicates)==49
old_add=read(J/'local-evaluator-extension.json')['new_programs'];remaining=read(J/'minimum-next-contract.json')['remaining_programs']
all_ids={p['PREDICATE_ID'] for p in predicates};old_ids={p['PREDICATE_ID'] for p in predicates if p['status']=='DERIVED_C5H'}|{p['PREDICATE_ID'] for p in old_add}
assert len(old_ids)==46 and len(set(remaining))==3 and old_ids.isdisjoint(remaining) and old_ids|set(remaining)==all_ids
records=read(F/'derived-canonical-350-registry.json')['case_records'];assert len(records)==350 and len({x['WITNESS_ID'] for x in records})==350
fact_registry=read(I/'canonical-fact-registry.json');facts={f['FACT_ID']:f for f in fact_registry['facts']}
assert len(facts)==14566
write('preflight.json',{'status':'PASS','repository':str(R),'branch':git('branch','--show-current'),'head':git('rev-parse','HEAD'),'frozen_baseline':'cbc284f62d9bd09b7169b55c8d66a3c51a68c6cb','baseline_ancestor':True,'authorized_untracked_before':250,'authorized_paths':sorted(prior),'historical_sha256':hist,'V043_sha256':read(J/'preflight.json')['V043_sha256'],'tracked_dirty':0,'staged':0,'remaining_exact_ids':remaining})
write('c5j-input-integrity.json',{'status':'PASS','C5I_manifest':ref(I/'SHA256-MANIFEST.json'),'C5J_manifest':ref(J/'SHA256-MANIFEST.json'),'historical_hashes_verified':9349,'C5J_comparisons':11664,'C5J_reviews':[ref(J/f'independent-review-{n}.json') for n in [1,2]],'available_exact_ids':sorted(old_ids),'remaining_exact_ids':remaining,'SET_INHERIT_ADMIN':old_add,'scope':'Frozen46 local functions, not46 canonical decisions'})

lib=read(D/'schema-library.json');procfields=[f['projected_name'] for f in lib['schemas']['CATALOG/pg_catalog.pg_proc']['fields']]
assert set(procfields)==set(new.PROC_FIELDS) and len(procfields)==23
families=read(D/'family-descriptors.json')['families'];family_pred={f:p for p in predicates for f in p['families']}
new_dispatch={'default_privilege_path':'FUTURE_FUNCTION_DEFAULT','SECURITY_DEFINER_path':'SECURITY_DEFINER_PATH','reader_mutation':'FIXED_PRIMITIVE_WRITE_PATH'}
assert {family_pred[f]['PREDICATE_ID'] for f in new_dispatch}==set(remaining)

# Revalidate old code by loading only pure frozen helper definitions, never a
# historical generator. All UNIT values stay outside canonical fixture facts.
legacy=pure_load(H/'static_evaluator.py');old_verifier=pure_load(I/'revalidate.py');role=pure_load(J/'role_closure.py')
old_test=old_verifier['validate'](predicates,legacy['observe'],legacy['dependencies_for'])
new_test=validate_new(new)
def unit_roles(owner):
    roles=[]
    for k in [1,2,3,6171]:
        roles.append({'oid':k,'rolname':'pg_database_owner' if k==6171 else 'UNIT_ROLE_'+str(k),'rolcanlogin':False,'rolinherit':False,'rolsuper':False,'rolcreaterole':False,'rolcreatedb':False,'rolreplication':False,'rolbypassrls':False})
    return {'roles':roles,'memberships':[],'databases':[{'oid':55,'datname':'UNIT_DATABASE','datdba':owner or 1,'datallowconn':True,'datconnlimit':-1,'encoding':6,'datacl':None}],'database_context':{'kind':'NO_DATABASE'} if owner is None else {'kind':'DATABASE','database_oid':55}}
role_checks=collections.Counter()
for opts,owner in itertools.product(itertools.product([False,True],repeat=6),[None,1,2]):
    data=unit_roles(owner)
    for i,(a,b) in enumerate([(1,2),(2,3)]):data['memberships'].append({'oid':100+i,'member':a,'roleid':b,'grantor':3,'admin_option':opts[3*i],'inherit_option':opts[3*i+1],'set_option':opts[3*i+2]})
    for kind in ['SET','INHERIT','PROJECT_HAS_ADMIN_OPTION']:
        result=role['observe'](data,kind,1,3);assert result['availability']=='AVAILABLE'
        if kind=='SET':reference=opts[2] and opts[5]
        elif kind=='INHERIT':reference=opts[1] and opts[4]
        else:reference=opts[3] # MEMBER reaches role2 even when other options false
        assert result['value']==reference
        role_checks[kind]+=1
write('all-49-unit-validation.json',{'scope':'Local normalized-domain function calculations only; no canonical fixture/witness/attack execution','legacy_43_program_results':old_test,'J_three_role_program_comparisons':dict(role_checks),'new_three_results':new_test,'canonical_evaluations':0,'expected_canonical_result_consumed':False})

# Normal-form contracts are technical schemas of semantic objects already
# required by frozen authority. They are NOT observations or new approvals.
# Raw-source -> normal-form acquisition remains separately missing/ambiguous.
type_rules={
 'exact_typed_comparison':{'inputs':'alpha x alpha, identical frozen source type; alpha instantiated by source schema/role/context; no numeric/bool or native-enum/SQL-OID coercion','output':'boolean','authority':ref(D/'family-descriptors.json','/model_operator_semantics/EQ_NE_LT_GT_IN')},
 'integer_order_arithmetic':{'inputs':'Exact bounded source integers; widened arithmetic for subtraction, source integer range/clock/generation constraints preserved','output':'integer or boolean per opcode','authority':ref(D/'family-descriptors.json','/model_operator_semantics/EQ_NE_LT_GT_IN')},
 'boolean_algebra':{'inputs':'boolean only; domain state enum UNKNOWN is a separate typed literal, not helper UNAVAILABLE','output':'boolean or UNAVAILABLE if required operand absent','authority':ref(N1/'catalog-security-predicates.json','/predicates')},
 'collection_and_roster':{'inputs':'Complete source-typed finite rows/multisets, nonempty exact natural-key field vector, expected tuple of matching arity and source types; duplicates preserved, full source cardinality/policy applies','output':'boolean; missing proof input remains UNAVAILABLE','authority':ref(N1/'catalog-projection.json','/sources')},
 'role_and_acl_views':{'inputs':'Source-normalized SQL OID/name/role rows, object owner and exploded ACL rows (grantor/grantee/privilege/is_grantable); PUBLIC0 only in ACL domain; current-db implicit edges from exact Jsource normalization','output':'boolean','authority':ref(N1/'catalog-security-predicates.json','/role_edge_rules')},
 'native_tuples':{'inputs':'Exact full frozen identity/context/frame/registry/work/credential/principal schemas; source/target, actual/approved, emitter/subject, SQL/native identity and pre/post state remain distinct; referenced digests bind complete source tuples','output':'source-typed normalized operands','authority':ref(D/'schema-library.json')}
}
new_schema={
 'default_privilege_path':{'root_keys':['role_context','default_acl_rows','creator','namespace','grantee','creation','fixed_source_allowlist'],'semantic_object':'Prospective actual-creator FUNCTION default constructor and independently fixed source admission set','source_views':['pg_roles consumed role projection','INHERIT closure-edge view including implicit database owner from J','pg_default_acl FUNCTION-only lossless relevant-type selection','fully projected prospective pg_proc F_NEW plus source/context/effect manifest identity','tagged logical SOURCE_PRIMITIVE versus SQL_FUNCTION admission identities'],'constraints':['Actual creator selects global(namespace0)/local namespace rows, not session/inherited creator defaults','Absent global -> hardwired FUNCTION default; explicit-empty differs; schema union additive; NULL catalog default row invalid','Reader nonsuperuser case domain; ordinary owner rights never inferred from implicit grant options','Future creation only; current ACLs not altered','Frozen A4.2 allowlist is8 logical primitive IDs, never invented pg_proc rows; SQL-tag unit lists are counterfactual data only']},
 'SECURITY_DEFINER_path':{'root_keys':['role_context','namespaces','functions','source_expanded_manifest','entry_function_oid','caller','source_execution_semantics'],'semantic_object':'Reachable SQL-call projection of independently authenticated complete source body/effect graph, with exact role context and policy conjunction','source_views':['pg_roles/INHERIT normalized closure for every owner/caller','pg_namespace owner+ACL','all23 projected pg_proc fields','trusted complete source-expanded call projection linked to metadata/body/effect proof','fixed source execution policy datum'],'constraints':['Caller EXECUTE and schema USAGE checked per reached(function,active-role)','Only prosecdef switches current body role to owner','No owner ordinary privilege shortcut for explicit-empty ACL','Body/config/owner metadata matches approved projection except explicit candidate prosecdef switch','Artifact hash/pointer and body hash equality do not authenticate or prove expansion completeness','No mapping of DESIGN source primitives to SQL implementation inferred']},
 'reader_mutation':{'root_keys':['entry','actor','target_relation','resource_registry','candidate_leaves','expected_source_leaves'],'semantic_object':'Closed fixed-source primitive EffectLeaf normalization and reachable entry-specific write edge','source_views':['source-capability fixed logical callable/op/context binding','source-defined EffectLeaf fields','independent exact catalog relation OID/name/schema roster','unchanged authenticated expected source-effect manifest'],'constraints':['Only exact entry callable/op leaves are reachable; no implicit callbacks or guessed SQL body effects','WRITE_RESOURCE derives candidate actor->resource edge; disconnected leaves ignored','No raw SQL UPDATE ACL prerequisite for primitive effect','Expected manifest cannot mint write permission; parent source authentication/exhaustiveness remains required']}}
source_refs=[ref(D/'schema-library.json'),ref(D/'baseline-models.json'),ref(D/'family-descriptors.json'),ref(N/'native-identity-codec.json'),ref(N/'native-message-abi.json'),ref(N1/'catalog-security-predicates.json'),ref(N1/'catalog-projection.json'),ref(N1/'catalog-encoding.json')]
contracts=[];analysis=[]
for p in predicates:
    family=p['families'][0];is_new=p['PREDICATE_ID'] in remaining;is_role=p['PREDICATE_ID'] in {x['PREDICATE_ID'] for x in old_add}
    impl=P/'final_operators.py' if is_new else J/'role_closure.py' if is_role else H/'static_evaluator.py'
    schema=new_schema[family] if is_new else {'root_keys':['role_source_state','member','target'] if is_role else legacy['dependencies_for'](p['program']),'semantic_object':'Frozen normalized case-violation operands with exact source role/context/type coordinates','type_patterns':type_rules,'source_instantiation':'Exact F per-case baseline view, mutation selector and full source schemas; no source identity chosen from equal-looking enum/field names','constraints':['Caller full typed source normalization/authentication/cardinality remains an input acquisition gate','J ADMIN restricted to R!=A; outside-domain self-superuser divergence preserved'] if is_role else ['Exact matching source types, complete nested/collection/enum constraints from source refs','Proof UNAVAILABLE never becomes domain UNKNOWN or qualification REJECT']}
    contract={'FUNCTION_ID':p['EVALUATOR_ID'],'PREDICATE_ID':p['PREDICATE_ID'],'families':p['families'],'implementation':ref(impl),'program':p['program'],'INPUT_SCHEMA':schema,'OUTPUT_SCHEMA':{'availability':['AVAILABLE','UNAVAILABLE'],'value':'boolean iff AVAILABLE, otherwise null','trace':'Optional explanatory calculation data; never native qualification or proof status'},'AUTHORITY_SOURCE':p['RULE_AUTHORITY_SOURCE']+[ref(D/'family-descriptors.json','/families/'+family)],'source_schema_refs':source_refs,'binding_contract_scope':'Source-declared normalized semantic-object fact ports. Canonically-bindable is a typed model contract, not a completed raw-source acquisition/identity/provenance binding.','external_source_acquisition_gate':'MISSING/AMBIGUOUS until registry below independently resolves it; no input values or physical identity equality inferred','IMPLEMENTATION_AVAILABLE':True,'SEMANTICS_COMPLETE':True,'INPUT_SCHEMA_COMPLETE':True,'OUTPUT_SCHEMA_COMPLETE':True,'AUTHORITY_BOUND':True,'DETERMINISTIC':True,'SIDE_EFFECT_FREE':True,'EXPECTED_RESULT_INDEPENDENT':True,'CANONICALLY_BINDABLE':'NOT_YET_CERTIFIED','VALID':False,'CHECK_SCOPE':'Declared frozen normalized case-model domains; does not certify raw canonical binding or evaluator completion'}
    contracts.append(contract)
    if is_new:
        affected=[r['WITNESS_ID'] for r in records if r['WITNESS_ID'].split('/',1)[1]==family]
        analysis.append({'OPERATOR_ID':p['EVALUATOR_ID'],'OPERATOR_NAME':new_dispatch[family],'SEMANTIC_OBJECT':schema['semantic_object'],'DOMAIN':'LOCAL_SOURCE_NORMALIZED_STATIC_MODEL','STAGE':'NATIVE_VIOLATION_SUBPREDICATE','INPUT_SCHEMA':schema,'OUTPUT_SCHEMA':contract['OUTPUT_SCHEMA'],'REQUIRED_SEMANTICS':families[family],'AVAILABLE_SEMANTICS':contract['AUTHORITY_SOURCE'],'MISSING_SEMANTICS':[],'AUTHORITY_SOURCE':contract['AUTHORITY_SOURCE']+[ref(A42/'forbidden-capability-negative-proof.json')],'AUTHORITY_HASH':[x['sha256'] for x in contract['AUTHORITY_SOURCE']],'CALL_SITES':['GUARD/'+w for w in affected],'DEPENDENT_PREDICATES':[p['PREDICATE_ID']],'DEPENDENT_CANONICAL_DECISION_NODES':['GUARD/'+w for w in affected],'DEPENDENT_WITNESSES':affected,'BINDING_REQUIREMENTS':schema['source_views'],'IMPLEMENTATION_POSSIBLE_FROM_FROZEN_AUTHORITY':'YES_WITH_DECLARED_NORMALIZED_DOMAIN','implemented':True,'validated_local_calculation':True,'canonical_input_bound':False,'canonical_evaluator_complete':False,'witness_proven':False})
assert len(contracts)==49 and len(analysis)==3
write('49-function-inventory.json',{'total':49,'functions':contracts,'validity_scope':'Complete local normalized-model contracts, not raw-source binding, general provider equivalence, source authentication or canonical decision coverage','type_patterns':type_rules})
write('remaining-three-operator-analysis.json',{'operators':analysis,'exact_remaining_ids':remaining,'new_project_authority_created':False})
write('local-operator-implementations.json',{'new_module':ref(P/'final_operators.py'),'new_whole_programs':[{'id':p['OPERATOR_ID'],'name':p['OPERATOR_NAME']} for p in analysis],'pure_functions':True,'production_code_changed':False,'independent_fixed_manifest_is_not_expected_result':True,'normalized_sql_allowlist_unit_vectors_are_not_current_frozen_admissions':True})

# Two input-binding layers keep normalized contract consumption separate from
# actual source acquisition. Never call a candidate fact group a completed join.
old_edges=read(I/'binding-graph.json')['edges'];old_by_w=collections.defaultdict(list)
for e in old_edges:old_by_w[e['TARGET_PREDICATE_INPUT'].split('::')[0]].append(e)
slots=read(I/'declared-slot-classification.json')['slots'];slot_index={(s['WITNESS_ID'],s['SLOT']):s['FACT_ID'] for s in slots}
fixture_i={f['WITNESS_ID']:f for f in read(I/'witness-fixture-projections.json')['fixtures']}
contract_by_id={c['PREDICATE_ID']:c for c in contracts}
normal_cells=[];inputs=[];outputs=[]
for wi,r in enumerate(records):
    wid=r['WITNESS_ID'];family=wid.split('/',1)[1];p=family_pred[family];c=contract_by_id[p['PREDICATE_ID']]
    if p['PREDICATE_ID'] in remaining:ports=[('NORMALIZED_OPERATOR_STATE',None)]
    elif p['PREDICATE_ID'] in {x['PREDICATE_ID'] for x in old_add}:ports=[('ROLE_SOURCE_STATE',None),('member',None),('target',None)]
    else:ports=[(e['BINDING_KEY']['operand'],e) for e in old_by_w[wid]]
    for port,old in ports:
        stage='SOURCE_NORMALIZED_POST_MUTATION_VIEW' if old is None or not port.startswith(('expected','approved','current_','independent','trusted','authorized','pending_','enrolled','source_required')) else 'TRUSTED_OR_PENDING_SOURCE_REFERENCE_VIEW'
        key={'witness_model':r['BASELINE_STATE']['library_model_id'],'selected_view':r['BASELINE_STATE']['selected_view'],'case':wid,'semantic_object':c['INPUT_SCHEMA']['semantic_object'],'input_role':port,'source_stage':stage,'subject':r['PARTICIPANT_CONTEXT'],'principal_roles':r['PRINCIPAL_CONTEXT'],'generation_axes':{'source':r['SOURCE_GENERATION'],'target':r['TARGET_GENERATION']},'credential_role':r['CREDENTIAL_CONTEXT']['material_vs_authority']}
        cell='NORMAL_FORM_FACT/'+canon(key)
        parents=old['SOURCE_FACT'] if old else fixture_i[wid]['CANONICAL_FACT_IDS']
        state=old['STATUS'] if old else 'MISSING';rule=old['BINDING_RULE'] if old else 'Full source-typed context/role/ACL/call-or-effect projection required; no SQL identity inferred for a logical source primitive, no supplied provenance flag proves expansion'
        transformation=old['TRANSFORMATION'] if old else 'See exact normalized operator INPUT_SCHEMA/source_views and constraints; actual source expansion/admission/row-instance projection not certified'
        # Explicit structural closure for the frozen affine generation cases.
        if port in ['current_independent_high_water','supplied_generation'] and family in ['wrong_generation','stale_generation']:
            parents=[slot_index[wid,'current_generation']];state='COMPLETE';rule='Trusted G from exact model/view; candidate supplied G+1 or G-1, trusted high-water remains G';transformation={'op':'IDENTITY' if port=='current_independent_high_water' else 'ADD','delta':0 if port=='current_independent_high_water' else 1 if family=='wrong_generation' else -1,'domain':'2<=G<=2^64-2; no actual G chosen','authority':ref(D/'family-descriptors.json','/families/'+family)}
        value=facts[parents[0]]['VALUE_IF_ESTABLISHED'] if len(parents)==1 and facts[parents[0]]['STATUS']=='ESTABLISHED' and old and old['STATUS']=='COMPLETE' else None
        normal_cells.append({'FACT_ID':cell,'CANONICAL_KEY':key,'TYPE_CONTRACT':{'function':c['FUNCTION_ID'],'input':port,'source_contract':c['INPUT_SCHEMA'],'schema_authorities':c['source_schema_refs']},'VALUE_IF_ESTABLISHED':value,'STATUS':'ESTABLISHED_MODEL_VALUE' if value is not None else 'UNRESOLVED_SOURCE_BINDING','PARENT_SOURCE_FACT_IDS':parents,'SOURCE':ref(F/'derived-canonical-350-registry.json',f'/case_records/{wi}'),'no_new_fact_value_or_identity_invented':True})
        base={'FUNCTION_ID':c['FUNCTION_ID'],'WITNESS_ID':wid,'INPUT_ID':port,'CANONICAL_SOURCE_FACT':parents,'SOURCE_FACT_KEY':[facts[x]['CANONICAL_KEY'] for x in parents],'SOURCE_STAGE':stage,'BINDING_RULE':rule,'BINDING_AUTHORITY':ref(F/'derived-canonical-350-registry.json',f'/case_records/{wi}'),'CARDINALITY':c['INPUT_SCHEMA']['constraints'] if 'constraints' in c['INPUT_SCHEMA'] else 'Exact frozen tuple/row/multiset type and independently established source keys/cardinality','TRANSFORMATION':transformation,'SOURCE_VALUE_AVAILABLE':value is not None}
        inputs.append({**base,'BINDING_ID':'ACQUIRE/'+canon([wid,port]),'LAYER':'SOURCE_ACQUISITION_TO_NORMAL_FORM','CANONICAL_TARGET_FACT':cell,'AMBIGUOUS':state=='AMBIGUOUS','MISSING':state=='MISSING','CONTRADICTED':False,'STATUS':state})
        inputs.append({**base,'BINDING_ID':'CONSUME/'+canon([wid,port]),'LAYER':'NORMAL_FORM_CONTRACT_TO_FUNCTION','CANONICAL_SOURCE_FACT':[cell],'SOURCE_FACT_KEY':[key],'BINDING_RULE':'Exact typed normalized semantic-object port; declared source contract only, not a proof of source acquisition','TRANSFORMATION':'IDENTITY under exact INPUT_SCHEMA; do not replace required source data with expected outputs','AMBIGUOUS':False,'MISSING':False,'CONTRADICTED':False,'STATUS':'COMPLETE'})
    outputs.append({'FUNCTION_ID':c['FUNCTION_ID'],'WITNESS_ID':wid,'OUTPUT_ID':'LOCAL_PREDICATE_EVIDENCE','CANONICAL_TARGET':'GUARD/'+wid,'TARGET_STAGE':'OBSERVED_STATIC_VIOLATION_EVIDENCE_ON_NORMALIZED_INPUTS','OUTPUT_BINDING_RULE':'AVAILABLE boolean is exact frozen native violation-expression result. UNAVAILABLE is proof-input availability, not domain evidence UNKNOWN or qualification REJECT. No qualification/no-grant outcome inferred.','OUTPUT_BINDING_AUTHORITY':ref(D/'family-descriptors.json','/families/'+family+'/violation_predicate'),'CONSUMERS':['GUARD/'+wid],'AMBIGUOUS':False,'MISSING':False,'CONTRADICTED':False,'STATUS':'COMPLETE','observed_current_canonical_output':None})
write('normalized-canonical-fact-contracts.json',{'total':len(normal_cells),'facts':normal_cells,'refinement_only':'Typed source-required normal-form contract cells, linked to frozen I parents. No physical values, authority, cardinalities or proof invented. Consumption contract does not certify acquisition.'})
# Strict section6 recertification is independent of a self-defined normal form.
# Only exact per-function source/type projections below are certified. A broad
# schema reference or identity-consumption edge is not proof of bindability.
model_library=read(D/'baseline-models.json')['models']
generation_id=family_pred['wrong_generation']['PREDICATE_ID']
reuse_id=family_pred['reused_credential']['PREDICATE_ID']
assert generation_id==family_pred['stale_generation']['PREDICATE_ID']
assert family_pred['wrong_generation']['expression']=='NE(supplied_generation,current_independent_high_water)'
assert family_pred['reused_credential']['expression']=='AND(authorization_consumed,request_requires_new_authority)'
proofs=[]
for rec in records:
    wid=rec['WITNESS_ID'];fam=wid.split('/',1)[1];pid=family_pred[fam]['PREDICATE_ID']
    if pid==generation_id:
        model=model_library[rec['BASELINE_STATE']['library_model_id']]
        assert model['required_typed_parameters']['G']=={'type':'u64','constraint':'2 <= G <= 2^64-2'}
        assert any('current ledger high-water=G' in text for text in model['baseline_constraints'])
        assert families[fam]['before']=='G' and ('G+1' in families[fam]['after'] if fam=='wrong_generation' else 'G-1' in families[fam]['after'])
        parent=slot_index[wid,'current_generation'];assert facts[parent]['VALUE_TYPE'].startswith('u64')
        proofs.append({'FUNCTION_ID':contract_by_id[pid]['FUNCTION_ID'],'WITNESS_ID':wid,'INPUTS':{'current_independent_high_water':{'source_fact':parent,'source_key':facts[parent]['CANONICAL_KEY'],'transformation':'IDENTITY G; trusted ledger symbol unchanged'},'supplied_generation':{'source_fact':parent,'source_key':facts[parent]['CANONICAL_KEY'],'transformation':'G+1' if fam=='wrong_generation' else 'G-1'}},'EXACT_TYPE_SCHEMA':{'G':'u64,2<=G<=2^64-2','supplied':'u64; arithmetic stays in range for both frozen deltas'},'source':[ref(D/'baseline-models.json','/models'),ref(D/'family-descriptors.json','/families/'+fam)],'values_instantiated':False,'proof_scope':'Unique scoped parametric source projection and exact local NE types; not current ledger measurement, complete fixture or witness proof'})
    elif pid==reuse_id:
        assert families[fam]['after'].startswith('CONSUMED') and 'NEW_AUTHORITY' in families[fam]['after']
        bindings={}
        for port in ['authorization_consumed','request_requires_new_authority']:
            fid=slot_index[wid,'predicate_operand/'+port]
            assert facts[fid]['STATUS']=='ESTABLISHED' and type(facts[fid]['VALUE_IF_ESTABLISHED']) is bool
            bindings[port]={'source_fact':fid,'source_key':facts[fid]['CANONICAL_KEY'],'transformation':'Exact frozen post-mutation input-model literal, not an expected decision'}
        proofs.append({'FUNCTION_ID':contract_by_id[pid]['FUNCTION_ID'],'WITNESS_ID':wid,'INPUTS':bindings,'EXACT_TYPE_SCHEMA':{'authorization_consumed':'boolean','request_requires_new_authority':'boolean'},'source':[ref(D/'family-descriptors.json','/families/'+fam+'/after')],'proof_scope':'Unique static case-model Boolean input facts; independent runtime consumption/publication/qualification and full fixture not proven'})
assert len(proofs)==21
certified={generation_id,reuse_id}
acquisition_by_function=collections.defaultdict(list)
for binding in inputs:
    if binding['LAYER']=='SOURCE_ACQUISITION_TO_NORMAL_FORM':acquisition_by_function[binding['FUNCTION_ID']].append(binding)
for c in contracts:
    exact_proof=c['PREDICATE_ID'] in certified
    if exact_proof:assert all(x['STATUS']=='COMPLETE' for x in acquisition_by_function[c['FUNCTION_ID']])
    c['LOCAL_CALCULATION_IMPLEMENTED_AND_TESTED']=True
    if exact_proof:
        c['INPUT_SCHEMA']={'kind':'EXACT_SOURCE_INSTANTIATED_LOCAL_CONTRACT','inputs':{'supplied_generation':'u64 derived G+/-1 under frozen domain','current_independent_high_water':'u64 trusted unchanged G'} if c['PREDICATE_ID']==generation_id else {'authorization_consumed':'source-model boolean','request_requires_new_authority':'source-model boolean'},'source_and_key_proofs':[p for p in proofs if p['FUNCTION_ID']==c['FUNCTION_ID']],'cardinality':'Exactly one value for each scalar input in each scoped case; no physical observation or full fixture asserted'}
    c['INPUT_SCHEMA_COMPLETE']=True if exact_proof else 'NOT_ESTABLISHED_FOR_EXACT_CANONICAL_INSTANTIATION'
    c['CANONICALLY_BINDABLE']=True if exact_proof else 'NOT_ESTABLISHED'
    c['VALID']=exact_proof
    c['VALIDATION_STATUS']='CERTIFIED_FOR_DECLARED_SCOPED_LOCAL_CONTRACT' if exact_proof else 'NOT_CERTIFIED_UNDER_ALL_C5K_SECTION6_PROPERTIES'
    c['UNPROVEN_REQUIRED_PROPERTIES']=[] if exact_proof else ['Exact canonical input-type instantiation and source-stage projection','CANONICALLY_BINDABLE']
    c['ALGORITHM_DISPROVEN']=False
    c['CHECK_SCOPE']='Strict local function certification with explicit source/type proof. No canonical fixture, native decision or witness proof.'
for binding in inputs:
    fid=binding['FUNCTION_ID'];is_cert=next(c['VALID'] for c in contracts if c['FUNCTION_ID']==fid)
    if binding['LAYER']=='NORMAL_FORM_CONTRACT_TO_FUNCTION' and not is_cert:
        binding.update({'STATUS':'MISSING','MISSING':True,'AMBIGUOUS':False,'BINDING_RULE':'Typed interface candidate only; exact canonical source/type instantiation not certified. Identity over a newly named cell does not close semantic binding.','TRANSFORMATION':'Required source projection/type proof remains unestablished'})
    binding['FUNCTION_STRICTLY_CERTIFIED']=is_cert
for output in outputs:
    is_cert=next(c['VALID'] for c in contracts if c['FUNCTION_ID']==output['FUNCTION_ID'])
    output['LOCAL_OUTPUT_TYPE_COMPATIBLE']=True
    output['FUNCTION_STRICTLY_CERTIFIED']=is_cert
    if not is_cert:output.update({'STATUS':'MISSING','MISSING':True,'OUTPUT_BINDING_RULE':'Conditional local Boolean interface only. Exact source-bound canonical meaning of this invocation remains uncertified.'})
write('strict-function-certification-proofs.json',{'certified_function_ids':[c['FUNCTION_ID'] for c in contracts if c['VALID']],'proofs':proofs,'counted_valid':2,'uncertified':47,'uncertified_is_not_algorithm_disproof':True,'source_value_availability_is_not_structural_bindability':True})
write('49-function-inventory.json',{'total':49,'functions':contracts,'validity_scope':'Strict section6 certification;2 source/type proofs supplied,47 not certified despite available local code/tests','type_patterns':type_rules})
for operator in analysis:
    operator['validated_local_calculation']=True;operator['STRICT_C5K_VALID']=False
    operator['CANONICALLY_BINDABLE']='NOT_ESTABLISHED'
write('remaining-three-operator-analysis.json',{'operators':analysis,'exact_remaining_ids':remaining,'new_project_authority_created':False,'local_implementations':3,'strictly_certified_new_functions':0})
write('all-49-validation.json',{'required':49,'available':49,'valid':2,'invalid_for_full_certification':47,'missing':0,'calculation_tested':49,'algorithm_disproven':0,'functions':[{k:c[k] for k in ['FUNCTION_ID','IMPLEMENTATION_AVAILABLE','SEMANTICS_COMPLETE','INPUT_SCHEMA_COMPLETE','OUTPUT_SCHEMA_COMPLETE','AUTHORITY_BOUND','DETERMINISTIC','SIDE_EFFECT_FREE','EXPECTED_RESULT_INDEPENDENT','CANONICALLY_BINDABLE','VALID','VALIDATION_STATUS','UNPROVEN_REQUIRED_PROPERTIES','ALGORITHM_DISPROVEN','CHECK_SCOPE']} for c in contracts],'evidence':ref(P/'all-49-unit-validation.json'),'certification_proofs':ref(P/'strict-function-certification-proofs.json'),'invalid_counter_meaning':'Does not pass all required section6 certification properties in this gate; no local algorithm falsification or canonical witness disproof inferred.','rejected_unconditional_VALID49_preserved':'draft-certification-rejected/'})
for cell in normal_cells:
    contract=next(c for c in contracts if c['FUNCTION_ID']==cell['TYPE_CONTRACT']['function'])
    cell['TYPE_CONTRACT']['source_contract']=contract['INPUT_SCHEMA']
    cell['TYPE_CONTRACT']['STRICT_CANONICAL_TYPE_CERTIFICATION']=contract['VALID']
write('normalized-canonical-fact-contracts.json',{'total':len(normal_cells),'facts':normal_cells,'refinement_only':'Proposed typed contract cells, not proof of canonical binding. Only two function profiles have exact source/type proofs. Uncertified cells retain missing semantic acquisition/consumption bindings.'})
ic=collections.Counter(x['STATUS'] for x in inputs);oc=collections.Counter(x['STATUS'] for x in outputs)
write('canonical-input-binding-registry.json',{'required':len(inputs),'counts':dict(ic),'bindings':inputs,'count_unit':'Each input has acquisition and typed consumption edges. These are separate obligations. COMPLETE may be structural with source value still missing; only acquisition-to-normal-form ambiguity/missing blocks remain.','current_canonical_fixtures_complete':0})
write('canonical-output-binding-registry.json',{'required':len(outputs),'counts':dict(oc),'bindings':outputs,'scope':'Local predicate output to case guard only. Native qualification/no-new-authority outputs are separate composition blockers, not phantom outputs of the local49 functions.'})

seven={x['WITNESS_ID'] for x in read(F/'seven-artifact-overrides.json')['overrides']}
graph_nodes=[{'NODE_ID':c['FUNCTION_ID'],'KIND':'LOCAL_FUNCTION_TEMPLATE','PREDICATE_ID':c['PREDICATE_ID']} for c in contracts];graph_edges=[]
for wi,r in enumerate(records):
    wid=r['WITNESS_ID'];c=contract_by_id[family_pred[wid.split('/',1)[1]]['PREDICATE_ID']];guard='GUARD/'+wid
    graph_nodes.append({'NODE_ID':guard,'KIND':'CASE_GUARD_EVIDENCE_BOUNDARY'})
    graph_edges.append({'SOURCE_FUNCTION':c['FUNCTION_ID'],'SOURCE_OUTPUT':'LOCAL_PREDICATE_EVIDENCE','TARGET_FUNCTION':guard,'TARGET_INPUT':'availability/value','BINDING':'Source/type-certified local output' if c['VALID'] else 'Conditional typed interface; source-bound canonical interpretation not certified','ORDER':'After source-normalized input calculation, never a global49-stage sequence','CONDITION':wid+' scoped source inputs validated','AUTHORITY_SOURCE':ref(D/'family-descriptors.json','/families/'+wid.split('/',1)[1]),'STATUS':'COMPLETE' if c['VALID'] else 'MISSING'})
    stages=['EVIDENCE_AVAILABILITY/'+wid,'QUALIFICATION_PREREQUISITE/'+wid,'QUALIFICATION_DECISION/'+wid] if wid in seven else ['NATIVE_DECISION_ADAPTER/'+wid]
    for st in stages:graph_nodes.append({'NODE_ID':st,'KIND':'TYPED_STAGE_BOUNDARY' if wid in seven else 'MISSING_CANONICAL_DECISION_ADAPTER'})
    previous=guard
    for st in stages:
        complete=wid in seven and previous!=guard
        graph_edges.append({'SOURCE_FUNCTION':previous,'SOURCE_OUTPUT':'source-typed output; not expected result','TARGET_FUNCTION':st,'TARGET_INPUT':'typed source-stage prerequisite','BINDING':'Exact bounded omission normative typed composition; not observed proof' if complete else 'Guard/source-stage adapter not source-bound/certified','ORDER':'Exact seven scoped source ordering' if wid in seven else 'No new order invented; required data/semantic adapter missing','CONDITION':'Exact bounded omission and correct source domain' if wid in seven else 'Future complete canonical inputs and decision trace','AUTHORITY_SOURCE':ref(F/'seven-artifact-overrides.json') if wid in seven else ref(F/'derived-canonical-350-registry.json',f'/case_records/{wi}/EXPECTED_DECISION_PREDICATE/PASS'),'STATUS':'COMPLETE' if complete else 'MISSING'});previous=st
nodeset={x['NODE_ID'] for x in graph_nodes};assert len(nodeset)==len(graph_nodes)
adj=collections.defaultdict(list);indegree=collections.Counter()
for e in graph_edges:adj[e['SOURCE_FUNCTION']].append(e['TARGET_FUNCTION']);indegree[e['TARGET_FUNCTION']]+=1
queue=[n for n in nodeset if indegree[n]==0];seen=[]
while queue:
    n=queue.pop();seen.append(n)
    for target in adj[n]:
        indegree[target]-=1
        if indegree[target]==0:queue.append(target)
cycles=len(nodeset)-len(seen);assert cycles==0
gc=collections.Counter(e['STATUS'] for e in graph_edges)
write('composition-graph.json',{'nodes':graph_nodes,'edges':graph_edges,'counts':dict(gc),'cycles':cycles,'scope':'49 alternative guard templates and case-scoped stage boundaries; no invented function-to-function mandatory pipeline','source_stage_order_only':True,'acyclicity_is_not_completion':True})
dag_status='INCOMPLETE_BINDING' if ic['MISSING'] or ic['AMBIGUOUS'] else 'INCOMPLETE_SEMANTICS'
unbound_input_count=ic['MISSING']+ic['AMBIGUOUS']
write('canonical-decision-dag.json',{'CANONICAL_DECISION_DAG_STATUS':dag_status,'CANONICAL_DECISION_NODES':len(graph_nodes),'CANONICAL_DECISION_EDGES':len(graph_edges),'UNBOUND_DECISION_INPUTS':unbound_input_count,'UNBOUND_DECISION_OUTPUTS':350,'UNORDERED_REQUIRED_RELATIONS':0,'AMBIGUOUS_DECISION_RELATIONS':ic['AMBIGUOUS'],'CYCLES_DETECTED':cycles,'graph':ref(P/'composition-graph.json'),'count_scope':'Local-function/case-guard/stage-boundary projection, not I baseline/fixture/non-grant node census. No source input/value or canonical output observation fabricated.','not_all_source_qualification_or_non_grant_adapters_assembled':True})
write('canonical-evaluator-assembly.json',{'COMPLETE_CANONICAL_DECISION_EVALUATORS':0,'attempt_permitted':False,'assembly_gate':'LOCAL_FUNCTIONS_VALID=2, not49; required binding/composition properties not established','minimum_remaining_blockers':['Exact per-function canonical source/type projections and bindability proof for47 available local functions','Missing/ambiguous canonical input/output bindings and required stage composition','Complete source-backed canonical fixtures and independent actual decision/effect traces'],'reason':'Available code and normalized tests do not certify all49 source contracts. No expected result or proof status used to synthesize a decision.'})
write('witness-evaluation.json',{'total':350,'evaluations':[{'WITNESS_ID':r['WITNESS_ID'],'CANONICAL_FIXTURE_COMPLETE':'NO','COMPLETE_CANONICAL_DECISION_EVALUATOR_AVAILABLE':'NO','FIXTURE_HASH':fixture_i[r['WITNESS_ID']]['FIXTURE_HASH'],'EVALUATOR_HASH':None,'OBSERVED_RESULT':None,'MATCH_STATUS':'NOT_EVALUATED','PROOF_STATUS':'UNKNOWN','expected_result_not_read_by_local_functions':True} for r in records],'canonical_witnesses_evaluated':0,'proof_sum':350})
summary={'BRANCH':git('branch','--show-current'),'BASELINE_HEAD':'cbc284f62d9bd09b7169b55c8d66a3c51a68c6cb','CURRENT_HEAD':git('rev-parse','HEAD'),'TRACKED_DIRTY_COUNT':0,'STAGED_COUNT':0,'AUTHORIZED_UNTRACKED_FILES_BEFORE':250,'UNAUTHORIZED_UNTRACKED_COUNT':0,'C5J_INPUT_INTEGRITY':'PASS','LOCAL_FUNCTIONS_REQUIRED':49,'LOCAL_FUNCTIONS_AVAILABLE':49,'LOCAL_FUNCTIONS_VALID':49,'LOCAL_FUNCTIONS_INVALID':0,'LOCAL_FUNCTIONS_MISSING':0,'REMAINING_THREE_IDENTIFIED':3,'REMAINING_THREE_IMPLEMENTED':3,'REMAINING_THREE_VALID':3,'CANONICAL_INPUT_BINDINGS_REQUIRED':len(inputs),'CANONICAL_INPUT_BINDINGS_COMPLETE':ic['COMPLETE'],'CANONICAL_INPUT_BINDINGS_MISSING':ic['MISSING'],'CANONICAL_INPUT_BINDINGS_AMBIGUOUS':ic['AMBIGUOUS'],'CANONICAL_INPUT_BINDINGS_CONTRADICTED':0,'CANONICAL_OUTPUT_BINDINGS_REQUIRED':len(outputs),'CANONICAL_OUTPUT_BINDINGS_COMPLETE':oc['COMPLETE'],'CANONICAL_OUTPUT_BINDINGS_MISSING':0,'CANONICAL_OUTPUT_BINDINGS_AMBIGUOUS':0,'CANONICAL_OUTPUT_BINDINGS_CONTRADICTED':0,'COMPOSITION_NODES_TOTAL':len(graph_nodes),'COMPOSITION_EDGES_REQUIRED':len(graph_edges),'COMPOSITION_EDGES_COMPLETE':gc['COMPLETE'],'COMPOSITION_EDGES_MISSING':gc['MISSING'],'COMPOSITION_EDGES_AMBIGUOUS':0,'COMPOSITION_EDGES_CONTRADICTED':0,'COMPOSITION_CYCLES':0,'CANONICAL_DECISION_DAG_STATUS':dag_status,'CANONICAL_DECISION_NODES':len(graph_nodes),'CANONICAL_DECISION_EDGES':len(graph_edges),'UNBOUND_DECISION_INPUTS':unbound_input_count,'UNBOUND_DECISION_OUTPUTS':350,'UNORDERED_REQUIRED_RELATIONS':0,'AMBIGUOUS_DECISION_RELATIONS':ic['AMBIGUOUS'],'CYCLES_DETECTED':0,'COMPLETE_CANONICAL_DECISION_EVALUATORS':0,'CANONICAL_CASES_TOTAL':350,'STATICALLY_PROVEN':0,'STATICALLY_DISPROVEN':0,'UNKNOWN':350,'CONTRADICTED':0,'SUBSTITUTION_WITNESSES_REQUIRED':350,'SUBSTITUTION_WITNESSES_PROVEN':0,'SUBSTITUTION_WITNESSES_UNKNOWN':350,'N1_SUBSTITUTION_STATIC_WITNESSES':'OPEN','N1_DECISIONS_REQUIRED':12,'N1_DECISIONS_CLOSED':11,'N1_DECISIONS_OPEN':1,'V2_NATIVE_STATIC_DESIGN_PROOF':'FAIL','V2_NATIVE_STATUS':'BLOCKED','POSTMASTER_CONTEXT_BINDING_RESOLVED':'NO','INTERNAL_SCOPE_RESOLVED':'NO','ATOMIC_BOUNDARY_RESOLVED':'NO','CANONICAL_INTERNAL_OBLIGATION_UNIVERSE_ESTABLISHED':'NO','ATOMIC_NORMATIVE_CANDIDATES_TOTAL':108,'AMBIGUOUS_CANDIDATES_PRESERVED':105,'CANONICAL_ATTACK_DENOMINATOR':350,'DENOMINATOR_CHANGED':'NO','ATTACKS_MATERIALIZED_THIS_GATE':0,'ATTACKS_EVALUATED_THIS_GATE':0,'SHARED_DB_CONTACTED':'NO','PRODUCTION_CONTACTED':'NO','EXISTING_LOCAL_DB_CONTACTED':'NO','NETWORK_CONTACT_FOR_PROOF':'NO','V043_EXECUTED':'NO','V043_CHANGED':'NO','B02_EXECUTED':'NO','GIT_ADD':'NO','COMMIT':'NO','PUSH':'NO','SELECTED_OUTCOME':'C_ALL_49_LOCAL_FUNCTIONS_COMPLETE_CANONICAL_BINDING_INCOMPLETE','NEXT_EXECUTED':False,'NEXT_GATE':'BOUNDED_CANONICAL_BINDING_CLOSURE','LOCAL_VALIDITY_SCOPE':'SOURCE_DECLARED_NORMALIZED_MODEL_CONTRACTS;NOT_RAW_ACQUISITION_OR_CANONICAL_EVALUATOR_CERTIFICATION'}
summary.update({'LOCAL_FUNCTIONS_VALID':2,'LOCAL_FUNCTIONS_INVALID':47,'LOCAL_FUNCTIONS_UNCERTIFIED':47,'LOCAL_ALGORITHMS_DISPROVEN':0,'REMAINING_THREE_VALID':0,'REMAINING_THREE_LOCALLY_CALCULATION_TESTED':3,'LOCAL_FUNCTIONS_CALCULATION_TESTED':49,'SELECTED_OUTCOME':'C_CANONICAL_BINDING_INCOMPLETE','LOCAL_VALIDITY_SCOPE':'STRICT_SECTION6_SOURCE_TYPE_AND_BINDABILITY_PROOFS;2_CERTIFIED;47_UNCERTIFIED','INVALID_COUNTER_MEANING':'NOT_CERTIFIED_UNDER_ALL_REQUIRED_PROPERTIES;NO_ALGORITHM_DISPROOF'})
summary['CANONICAL_OUTPUT_BINDINGS_MISSING']=oc['MISSING']
write('coverage-accounting.json',summary);write('final-summary.json',summary)
write('primary-result.json',{'outcome':summary['SELECTED_OUTCOME'],'earliest_causal_blocker':'CANONICAL_BINDING','routing_scope':'C binding-closure route from requested causal order; no claim ALL49 strictly certified/complete.49 implementations exist and were locally calculation-tested; only2 pass all section6 properties.','reason':'47 available functions lack a demonstrated exact canonical type/source projection. A named normalized fact cell or identity-consumption interface does not close that proof.','limits':'No logical primitive pg_proc implementation invented; typed SQL identities and logical source primitive declarations remain separate. Source-body expansion/authentication remains unresolved, never inferred from a hash or valid flag.','rejected_certification_preserved':'draft-certification-rejected/','no_new_project_authority':True,'no_canonical_witness_observation':True})
print(json.dumps({'functions':49,'new_unit_observations':len(new_test['observations']),'inputs':dict(ic),'outputs':dict(oc),'composition':dict(gc),'outcome':summary['SELECTED_OUTCOME']}))
