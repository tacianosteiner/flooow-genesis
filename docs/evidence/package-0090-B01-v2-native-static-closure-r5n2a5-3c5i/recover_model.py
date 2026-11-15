"""C5I: source-scoped fact factorization and partial decision-model recovery.

Evidence only. All writes stay in C5I. No DB/network/native/attack execution.
"""
import ast
import collections
import functools
import hashlib
import json
import pathlib
import subprocess
import sys
sys.dont_write_bytecode=True
from revalidate import validate

P=pathlib.Path(__file__).resolve().parent
R=P.parents[2]
H=P.with_name(P.name[:-1]+'h')
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
def ref(p,pointer=''):return {'path':rel(p),'sha256':sha(p),'pointer':pointer}
def write(n,x):(P/n).write_text(json.dumps(x,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True).strip()

# Frozen provenance before any structural recovery.
hist=read(H/'preflight.json')['historical_sha256']
hist.update(read(H/'SHA256-MANIFEST.json')['files']);hist[rel(H/'SHA256-MANIFEST.json')]=sha(H/'SHA256-MANIFEST.json')
assert len(hist)==9298 and all(sha(R/p)==h for p,h in hist.items())
prior=set(read(H/'preflight.json')['authorized_paths'])|set(read(H/'SHA256-MANIFEST.json')['files'])|{rel(H/'SHA256-MANIFEST.json')}
assert len(prior)==199
u=set(git('ls-files','--others','--exclude-standard').splitlines())
assert not prior-u and all(x.startswith(rel(P)+'/') for x in u-prior)
assert git('rev-parse','--show-toplevel').lower()==R.as_posix().lower()
assert git('branch','--show-current')=='checkpoint/package-0090-cloud-handoff'
assert git('rev-parse','HEAD')=='451265ff5b3d286eb4d27c4b3817c2f558f30123'
assert not git('diff','--name-only') and not git('diff','--cached','--name-only')
assert subprocess.run(['git','merge-base','--is-ancestor','cbc284f62d9bd09b7169b55c8d66a3c51a68c6cb','HEAD'],cwd=R).returncode==0
hs=read(H/'final-summary.json');ret=(H/'final-return.txt').read_text(encoding='utf-8').splitlines()
assert hs['UNTRACKED_FILES_AFTER']==199 and hs['FIXTURE_FIELDS_REQUIRED_TOTAL']==93316
assert all(f'{k}={str(v).lower() if isinstance(v,bool) else v}' in ret for k,v in hs.items())
packets=read(G/'canonical-350-proof-packet-registry.json')['packets']
records=read(F/'derived-canonical-350-registry.json')['case_records']
assert len(packets)==len(records)==350 and len({r['WITNESS_ID'] for r in records})==350
assert all(p['AVAILABLE_INPUTS']['canonical_record']==r for p,r in zip(packets,records))
write('preflight.json',{'status':'PASS','repository':str(R),'branch':git('branch','--show-current'),'head':git('rev-parse','HEAD'),'frozen_baseline':'cbc284f62d9bd09b7169b55c8d66a3c51a68c6cb','baseline_ancestor':True,'tracked_dirty':0,'staged':0,'authorized_untracked_before':199,'authorized_paths':sorted(prior),'historical_sha256':hist,'V043_sha256':read(H/'preflight.json')['V043_sha256'],'historical_repair':False})
preds=read(H/'unique-predicate-registry.json')['predicates'];pred_by_id={p['PREDICATE_ID']:p for p in preds}
assert len(preds)==49 and sum(p['status']=='DERIVED_C5H' for p in preds)==43
assert sum(p['status']=='OTHER_BLOCKED' for p in preds)==6
write('c5h-input-integrity.json',{'status':'PASS','final_summary':ref(H/'final-summary.json'),'final_return':ref(H/'final-return.txt'),'manifest':ref(H/'SHA256-MANIFEST.json'),'manifest_entries':27,'historical_hashes_verified':9298,'unique_witnesses':350,'packets_recoverable':350,'fixture_inventory':ref(H/'fixture-field-inventory.json'),'derived_evaluators':43,'blocked_exact_ids':[p['PREDICATE_ID'] for p in preds if p['status']=='OTHER_BLOCKED'],'OUTCOME_NOT_REPRESENTED_is_not_integrity_failure':True})

library=read(D/'schema-library.json');schemas=library['schemas'];design=library['design_only_model_types']
models=read(D/'baseline-models.json')['models'];families=read(D/'family-descriptors.json')['families']
abi=read(N/'native-message-abi.json');codec=read(N/'native-identity-codec.json');registry=read(N/'native-registry-generation.json')
security=read(N1/'catalog-security-predicates.json');projection=read(N1/'catalog-projection.json')
source_catalog={s['SOURCE_ID']:s for s in projection['sources']}
context_names={f['name'] for f in codec['bootstrap_context_schema']}

# First recover components from actual frozen schemas, not from slot names.
components=[];row_models=[]
for sid,s in schemas.items():
    is_catalog=sid.startswith('CATALOG/');is_registry=sid.startswith('REGISTRY/')
    is_frame=sid.startswith('FRAME/');is_identity=sid.startswith('IDENTITY/')
    shape='MULTISET' if is_catalog or is_registry else ('ORDERED_SET' if sid in {'dependency_node_schema','dependency_edge_schema','work_revision_schema'} else 'SCALAR')
    fields=[{'name':f.get('name',f.get('projected_name')),'type':f['type'],'nullable':f.get('nullable')} for f in s['fields']]
    natural=s.get('natural_key')
    src=s['source'];min_count=None;max_count=None
    if is_catalog:
        original=source_catalog[sid.split('/',1)[1]];natural=s['natural_key'];min_count=0
        ordering=original['ORDERING_RULE'];duplicates=original['DUPLICATE_SEMANTICS'];absence=original['MISSING_ROW_SEMANTICS']
        scope='(model_id, selected_view, exact_variant, snapshot/backend/generation context); no cross-case actual row identity inferred'
    elif is_registry:
        record=next(x for x in registry['records'] if x['type']==sid.split('/',1)[1]);natural=record['primary_identity'];min_count=0
        ordering='Preserve raw journal/stream order and duplicate occurrences before validation; validate record_sequence and independently verified predecessor/entity revisions; only then derive keyed relation'
        duplicates='Exact duplicate operation/terminal receipt handled by source protocol; not a new grant and never drop conflicting payload'
        absence='Missing current/entity/publication proof remains unqualified/UNKNOWN; never zero or identity inference'
        scope='Required keyed qualification/incarnation/epoch/slot/generation/entity/work references plus their authenticated predecessor/tip closure only; source/target/history distinct; no global registry row census'
    elif shape=='ORDERED_SET':
        natural='Complete source canonical element bytes';min_count=0;max_count=4096
        ordering=codec['set_encoding'];duplicates='Reject duplicate complete elements; preserve raw evidence until checked';absence='Empty allowed only when source family/root constraints permit; no absent-to-empty conversion'
        scope='Owning exact identity/work tuple; root/node/edge references independently checked'
    else:
        natural='Owning qualified tuple instance and exact source schema';ordering='Exact frozen field/tag order';duplicates='Not a collection; no implicit repeated-instance equality';absence='Required non-null source fields; optionality only where source explicitly declares it'
        scope='Source-scoped model/actor and selected context; sender, subject, principal and credential roles are separate'
    component={'COMPONENT_ID':sid,'SEMANTIC_OBJECT':sid,'DOMAIN':'CATALOG_EVIDENCE' if is_catalog else 'REGISTRY_AUTHORITY' if is_registry else 'MESSAGE_ABI' if is_frame else 'TYPED_IDENTITY','STAGE':'EVIDENCE_COLLECTION' if is_catalog else 'JOURNAL_ENTITY_RESOLUTION' if is_registry else 'TYPED_INPUT_CONSTRUCTION','FIELD_SET':fields,'IDENTITY_KEY':natural,'CARDINALITY_RULE':{'representation':shape,'exact_instance_count':'UNRESOLVED_CARDINALITY' if shape!='SCALAR' else 'One tuple per required bound reference; number of references is context-specific','minimum':min_count,'maximum_if_established':max_count},'OPTIONALITY_RULE':absence,'SOURCE_AUTHORITY':src,'SOURCE_ARTIFACT':ref(D/'schema-library.json','/schemas/'+sid.replace('/','~1')),'DERIVATION_RULE':'Use exact source fields, typed encoding and source-backed context keys. No field introduced from a C5H trace slot.','SHARED_ACROSS_WITNESSES':'SCHEMA_YES_VALUES_ONLY_WHEN_PROVEN_EQUIVALENT','WITNESS_SPECIFIC':'INSTANCE_BINDINGS','GENERATION_SPECIFIC':'CONTEXT_QUALIFIED','PARTICIPANT_SPECIFIC':is_frame or is_identity,'PRINCIPAL_SPECIFIC':is_catalog or is_registry or is_frame,'CREDENTIAL_SPECIFIC':'credential' in sid.lower() or 'channel' in sid.lower(),'CATALOG_SPECIFIC':is_catalog,'QUALIFICATION_SPECIFIC':True,'REVOCATION_SPECIFIC':'TOMBSTONE' in sid or 'enrollment' in sid,'binding_scope':scope}
    components.append(component)
    if shape!='SCALAR':
        row_models.append({'COMPONENT_ID':sid,'REPRESENTATION':shape,'VALIDATED_VIEW':'RELATION_AFTER_DUPLICATE_AND_SEQUENCE_VALIDATION' if is_catalog or is_registry else 'SOURCE_ORDERED_SET_AFTER_DUPLICATE_VALIDATION','ROW_IDENTITY':natural,'PARENT_IDENTITY':scope,'UNIQUENESS_RULE':'Validation condition, never erase duplicate raw inputs','MIN_CARDINALITY':min_count,'MAX_CARDINALITY_IF_ESTABLISHED':max_count,'EXACT_CARDINALITY':'UNRESOLVED_CARDINALITY','EXHAUSTIVENESS_REQUIRED':'YES_FOR_COMPLETE_REQUIRED_SOURCE_SCOPE','ORDERING_SEMANTICS':ordering,'DUPLICATE_SEMANTICS':duplicates,'ABSENCE_SEMANTICS':absence,'SOURCE_AUTHORITY':src,'conditional_cardinality_constraints':{'SNAPSHOT_APPLICABILITY':'Exactly one expected Reader identity match before omission; full collection size not established','CLOSED_READER_AUTHORITY_MODEL':'R/A/M role references distinct; at least3 role rows for the full role model. Zero memberships for R does not mean empty global pg_auth_members.','GENERATION_AUTHORITY_CLAIM':'Distinct complete source historical and current target references; no total registry row count established'} if is_catalog or is_registry else {'root_presence':'Source family/root constraints apply; no universal rootless empty graph assumed'}})
for name,d in design.items():
    if name=='MembershipRow':continue # Exact alias of existing pg_auth_members, no new fact/field.
    components.append({'COMPONENT_ID':'DESIGN/'+name,'SEMANTIC_OBJECT':name,'DOMAIN':'SOURCE_DECLARED_STATIC_MODEL_PROJECTION','STAGE':'BINDING_OR_NORMALIZATION','FIELD_SET':d.get('fields',d.get('variants')),'IDENTITY_KEY':'Exact owning source model, tagged variant and qualified actor/resource reference','CARDINALITY_RULE':{'representation':'MAP' if name=='ModuleMapEntry' else 'SCALAR','rule':'Per required source reference; actual instance count not invented'},'OPTIONALITY_RULE':'Source tagged variants/conditional OS versus SQL fields; no flattening into an always-present principal','SOURCE_AUTHORITY':ref(D/'schema-library.json','/design_only_model_types/'+name),'SOURCE_ARTIFACT':d.get('source',ref(D/'schema-library.json')),'DERIVATION_RULE':d.get('binding',d.get('normalization','Exact source-declared projection; no new wire/API/state')),'SHARED_ACROSS_WITNESSES':'DECLARATION_ONLY','WITNESS_SPECIFIC':'BOUND_INSTANCE','GENERATION_SPECIFIC':True,'PARTICIPANT_SPECIFIC':'AS_SOURCE_REQUIRES','PRINCIPAL_SPECIFIC':True,'CREDENTIAL_SPECIFIC':name=='PrivateResourceRef','CATALOG_SPECIFIC':name in {'ResolutionExpression','EffectLeaf','ACLRow','OperationClaim','SnapshotHeader'},'QUALIFICATION_SPECIFIC':True,'REVOCATION_SPECIFIC':name=='AuthorityClaim'})
    if name=='ModuleMapEntry':row_models.append({'COMPONENT_ID':'DESIGN/ModuleMapEntry','REPRESENTATION':'MAP','ROW_IDENTITY':['load_name','absolute_path'],'PARENT_IDENTITY':'Exact approved per-role module map','UNIQUENESS_RULE':'Exact complete canonical key, MODULE_KEY=lexicographically first key of independently approved map','MIN_CARDINALITY':1,'MAX_CARDINALITY_IF_ESTABLISHED':None,'EXACT_CARDINALITY':'UNRESOLVED_CARDINALITY','EXHAUSTIVENESS_REQUIRED':'YES','ORDERING_SEMANTICS':'Complete canonical key order','DUPLICATE_SEMANTICS':'No silently overwritten duplicate key','ABSENCE_SEMANTICS':'Missing approved map/key is not an empty valid map','SOURCE_AUTHORITY':ref(D/'baseline-models.json','/models')})
for label,fields in [('input_record_schema',abi['input_record_schema'])]+[('result_record_schemas/'+p,fs) for p,fs in abi['result_record_schemas'].items()]:
    components.append({'COMPONENT_ID':'NESTED/'+label,'SEMANTIC_OBJECT':label,'DOMAIN':'NATIVE_NESTED_RECORD','STAGE':'NESTED_CANONICAL_ENCODING','FIELD_SET':fields,'IDENTITY_KEY':'Exact parent frame, purpose and qualified role/result type','CARDINALITY_RULE':{'representation':'SCALAR','rule':'One nested value per exact corresponding field; no captured record asserted'},'OPTIONALITY_RULE':'Exact source schema presence','SOURCE_AUTHORITY':ref(N/'native-message-abi.json','/'+label),'SOURCE_ARTIFACT':ref(N/'native-message-abi.json'),'DERIVATION_RULE':abi['nested_record_encoding'],'SHARED_ACROSS_WITNESSES':'SCHEMA_ONLY','WITNESS_SPECIFIC':True,'GENERATION_SPECIFIC':True,'PARTICIPANT_SPECIFIC':True,'PRINCIPAL_SPECIFIC':True,'CREDENTIAL_SPECIFIC':False,'CATALOG_SPECIFIC':False,'QUALIFICATION_SPECIFIC':True,'REVOCATION_SPECIFIC':False})
graph_path=R/'docs/evidence/package-0090-B01-v2-native-static-closure-r5n2a4-1b/catalog-effect-graph.json'
graph_source=read(graph_path)
for collection,shape in [('nodes','GRAPH_NODE'),('edges','GRAPH_EDGE')]:
    field_names=sorted({k for row in graph_source[collection] for k in row})
    cid='DERIVED/SOURCE_AUTHORITY_GRAPH_'+collection.upper()
    components.append({'COMPONENT_ID':cid,'SEMANTIC_OBJECT':'Source-expanded typed authority/effect '+collection,'DOMAIN':'AUTHORITY_EFFECT_GRAPH','STAGE':'SOURCE_NORMALIZATION_AND_REACHABILITY','FIELD_SET':{'source_variant_field_names':field_names,'closed_typed_normalizer_schema':'NOT_COMPLETED; source variants/conditions must remain explicit'},'IDENTITY_KEY':graph_source['identity_rule'],'CARDINALITY_RULE':{'representation':shape,'exact_fixture_count':'UNRESOLVED_CARDINALITY'},'OPTIONALITY_RULE':'Exact source node/edge tagged variants and required provenance; no unknown edge type silently dropped','SOURCE_AUTHORITY':[ref(graph_path),ref(N1/'catalog-security-predicates.json','/edge_types')],'SOURCE_ARTIFACT':ref(graph_path),'DERIVATION_RULE':'Separate typed authority/effect edge normalization and least fixed point; immutable design graph alone is not a current ACL/credential/role instance','SHARED_ACROSS_WITNESSES':'RULES_ONLY_UNLESS_BINDING_PROVEN','WITNESS_SPECIFIC':'CANDIDATE_GRAPH_TRANSFORMATION','GENERATION_SPECIFIC':True,'PARTICIPANT_SPECIFIC':'AS_SOURCE_REQUIRES','PRINCIPAL_SPECIFIC':True,'CREDENTIAL_SPECIFIC':True,'CATALOG_SPECIFIC':True,'QUALIFICATION_SPECIFIC':True,'REVOCATION_SPECIFIC':'SOURCE_EDGE_SPECIFIC'})
    row_models.append({'COMPONENT_ID':cid,'REPRESENTATION':shape,'ROW_IDENTITY':graph_source['identity_rule'],'PARENT_IDENTITY':'Exact source-expanded graph + authenticated baseline/candidate context','UNIQUENESS_RULE':'Source identity reconciliation; preserve parallel typed edges/provenance, never merge edge classes','MIN_CARDINALITY':0,'MAX_CARDINALITY_IF_ESTABLISHED':None,'EXACT_CARDINALITY':'UNRESOLVED_CARDINALITY','EXHAUSTIVENESS_REQUIRED':'YES_FOR_REQUIRED_EFFECT_AND_AUTHORITY_CLOSURE','ORDERING_SEMANTICS':'Traversal least fixed point independent of insertion order; provenance/order of source collections retained','DUPLICATE_SEMANTICS':'Retain raw duplicate/parallel evidence until source identity/type reconciliation','ABSENCE_SEMANTICS':'Missing effect/type/endpoint proof is unknown, not a safe negative edge','SOURCE_AUTHORITY':ref(N1/'catalog-security-predicates.json','/traversal'),'immutable_design_artifact_row_count':len(graph_source[collection]),'artifact_count_is_not_fixture_cardinality':True})
write('canonical-fixture-schema.json',{'components':components,'scope':'Source-schema cover of recovered component types; not a proof of globally minimum physical instances or complete fixture rows. C5H traces/obligations are not new fixture fields. Graph normalization variants remain explicit blockers.','redundant_aliases':{'DESIGN/MembershipRow':'CATALOG/pg_catalog.pg_auth_members'},'scalars_and_branches':'Raw primitive values, optional tagged fields, contextual tuple instances and derived views remain distinct. No implicit SQL-role/native-principal alias.'})
write('row-cardinality-model.json',{'components':row_models,'raw_catalog_representation':'MULTISET until duplicate checking; validated keyed relations are separate derived views','cardinality_status':'Type/key/multiplicity semantics recovered; actual exhaustive instance counts unresolved','no_catalog_max4096_inference':True,'source_policy_bounds':ref(N1/'catalog-encoding.json','/bounds')})

# Canonical fact factorization. Equivalence is proved for a scoped obligation or
# frozen literal, not for arbitrary equal-looking live state across witnesses.
field_data=read(H/'fixture-field-inventory.json')
assert len(field_data['records'])==350 and field_data['required_total']==93316
facts={};projections=[];by_witness={};slot_meta={};classes=collections.Counter()
record_by_id={r['WITNESS_ID']:r for r in records}
family_to_pred={f:p['PREDICATE_ID'] for p in preds for f in p['families']}
def semantic_key(wid,e):
    rec=record_by_id[wid];participant,family=wid.split('/',1);base=rec['BASELINE_STATE'];model_id=base['library_model_id'];view=base['selected_view']
    field=e['FIELD_NAME'];value=e['FIELD_VALUE'];source=e['FIELD_SOURCE']
    if e['state']!='MISSING' and source['path']==rel(N/'native-message-abi.json') and source['pointer'].startswith('/actor_enum/'):
        actor=source['pointer'].split('/')[-1];assert value==abi['actor_enum'][actor]
        return ['FROZEN_ENUM_VALUE','NATIVE_ACTOR_ENUM',actor], 'VALUE_FACT','DERIVED_FACT' if e['state']=='DERIVED_C5H' else 'UNIQUE_CANONICAL_FACT','Exact source actor-enum projection, not an OS UID, SQL OID or credential identity'
    scope={'model_id':model_id,'selected_view':view,'exact_variant_hash':canon(base['exact_variant_state']),'state_side':'POST_MUTATION' if field.startswith(('post.','predicate_operand/')) else 'BASELINE_OR_PARAMETER'}
    if field=='mutation.generation_delta':return ['FROZEN_TRANSFORMATION_LITERAL',family,'GENERATION_DELTA'],'VALUE_FACT','DERIVED_FACT','Exact frozen affine mutation literal; generation identity not chosen'
    if field=='source_bound.generation_range':return ['FROZEN_DOMAIN_BOUND',model_id,'G'],'VALUE_FACT','DERIVED_FACT','Same source-scoped G domain, not a chosen generation value'
    if field.startswith(('post.','predicate_operand/','mutation.','observation.')):
        scope['witness_id']=wid
    # Only source-declared bootstrap/frame shared fields receive this alias.
    if field.startswith(('bootstrap_context_schema/','FRAME/')) and field.rsplit('/',1)[-1] in context_names:
        field='SHARED_BOOTSTRAP_CONTEXT/'+field.rsplit('/',1)[-1]
        return ['TYPED_BINDING_OBLIGATION',scope,field,e['TYPE']],'TYPED_BINDING_OBLIGATION','RELATIONAL_BINDING','Frozen model context/shared-field equality and exact frame construction order; scoped to same model/view/variant'
    if e['FIELD_NAME'].startswith('cardinality/'):
        return ['COLLECTION_CARDINALITY',scope,field],'COLLECTION_CARDINALITY_OBLIGATION','UNRESOLVED_CARDINALITY_PLACEHOLDER','One collection cardinality root per exact scoped source, not a count per projected row field'
    if e['FIELD_NAME'].startswith('catalog_rows[]/'):
        return ['QUANTIFIED_ROW_FIELD_BINDING',scope,field,e['TYPE']],'QUANTIFIED_ROW_FIELD_BINDING','COLLECTION_MEMBER','Source-typed quantified field obligation only; row identities and row count unresolved, no physical row equality inferred'
    if field.startswith(('codec_trace/','binding_trace/','source_constraint_trace/')):
        return ['FROZEN_RULE_OBSERVATION_OBLIGATION',scope,field,e['DEFINITION_SOURCE']['pointer']],'FROZEN_RULE_OBSERVATION_OBLIGATION','AUTHORITY_OBLIGATION','Obligation under already frozen authority; not a new normative authority decision'
    if field=='source_generation':
        return ['AFFINE_DERIVATION_BINDING',scope,'G_SOURCE=G-1'],'DERIVED_BINDING_OBLIGATION','DERIVED_FACT','Frozen arithmetic law; actual G binding still required'
    if field.startswith('mutation.'):
        return ['MUTATION_STATE_BINDING',scope,field],'MUTATION_BINDING_OBLIGATION','RELATIONAL_BINDING','Exact witness-specific mutation and dependent digest normalization'
    return ['SOURCE_SCOPED_BINDING',scope,field,e['TYPE']],'VALUE_FACT' if e['state']!='MISSING' else 'TYPED_BINDING_OBLIGATION','DERIVED_FACT' if e['state']=='DERIVED_C5H' else 'RELATIONAL_BINDING','Same qualified source binding obligation; never infer equality of independently instantiated physical state'

for inventory in field_data['records']:
    wid=inventory['WITNESS_ID'];rec=record_by_id[wid];pid=family_to_pred[wid.split('/',1)[1]];by_witness[wid]=set();slot_meta[wid]={}
    for ordinal,e in enumerate(inventory['required']):
        key,kind,category,rule=semantic_key(wid,e);fid='FACT/'+canon(key)
        status='ESTABLISHED' if e['state']!='MISSING' else 'UNRESOLVED_CARDINALITY' if kind=='COLLECTION_CARDINALITY_OBLIGATION' else 'UNRESOLVED_BINDING'
        f=facts.setdefault(fid,{'FACT_ID':fid,'FACT_TYPE':kind,'CANONICAL_KEY':key,'VALUE_TYPE':e['TYPE'],'VALUE_IF_ESTABLISHED':e['FIELD_VALUE'] if status=='ESTABLISHED' else None,'SOURCE':e['FIELD_SOURCE'],'SOURCE_HASH':e['FIELD_SOURCE_HASH'],'SOURCE_VARIANTS':{},'DERIVATION':e['DERIVATION_RULE'] or rule,'DERIVATION_AUTHORITY':e['DERIVATION_RULE_SOURCE'],'DEPENDENT_WITNESSES':set(),'DEPENDENT_PREDICATES':set(),'PROJECTION_COUNT':0,'STATUS':status,'fact_scope':'Frozen model literal or scoped binding/proof obligation, not an observed runtime state','equivalence_rule':rule})
        assert f['VALUE_TYPE']==e['TYPE'] and f['STATUS']==status,(wid,e['FIELD_NAME'],fid)
        if status=='ESTABLISHED':assert f['VALUE_IF_ESTABLISHED']==e['FIELD_VALUE'],(wid,e['FIELD_NAME'])
        f['SOURCE_VARIANTS'][canon(e['FIELD_SOURCE'])]=e['FIELD_SOURCE'];f['DEPENDENT_WITNESSES'].add(wid);f['DEPENDENT_PREDICATES'].add(pid);f['PROJECTION_COUNT']+=1
        if category=='UNIQUE_CANONICAL_FACT' and f['PROJECTION_COUNT']>1:category='REPEATED_PROJECTION_OF_SHARED_FACT'
        projections.append({'WITNESS_ID':wid,'C5H_SLOT_ORDINAL':ordinal,'SLOT':e['FIELD_NAME'],'FACT_ID':fid,'SLOT_CLASS':category,'REPEATED_PROJECTION':f['PROJECTION_COUNT']>1,'EQUIVALENCE_RULE':rule})
        by_witness[wid].add(fid);slot_meta[wid][e['FIELD_NAME']]={'fact':fid,'source':e['FIELD_SOURCE'],'definition':e['DEFINITION_SOURCE'],'state':e['state'],'value':e['FIELD_VALUE']}
        classes[category]+=1
    assert len(inventory['required'])==inventory['required_count']
del field_data
assert len(projections)==93316 and sum(f['PROJECTION_COUNT'] for f in facts.values())==93316
primary_fact_count=len(facts)
# Recover collection cardinality roots from the source structure even when H
# did not project a dedicated cardinality slot. These are no new fixture fields
# or invented row counts. They have zero primary slot multiplicity.
supplemental_cardinality=[]
row_by_component={m['COMPONENT_ID']:m for m in row_models}
native_views={'CURRENT_SUBJECT_IDENTITY','CURRENT_WORK_ONE_USE','PRIVATE_RESOURCE_CUSTODY','PENDING_NEW_QUALIFICATION','GENERATION_AUTHORITY_CLAIM'}
for rec in records:
    wid=rec['WITNESS_ID'];base=rec['BASELINE_STATE'];view=base['selected_view'];family=wid.split('/',1)[1]
    needed=[]
    if view in native_views:
        needed += [k for k in row_by_component if k.startswith('REGISTRY/') or k in {'dependency_node_schema','dependency_edge_schema','work_revision_schema'}]
    if view=='CURRENT_SUBJECT_IDENTITY':needed.append('DESIGN/ModuleMapEntry')
    if any(family in p['families'] and p['status']=='OTHER_BLOCKED' for p in preds):
        needed += [k for k in row_by_component if k.startswith('DERIVED/SOURCE_AUTHORITY_GRAPH_')]
    for cid in needed:
        model=row_by_component[cid]
        key=['SOURCE_REQUIRED_COLLECTION_CARDINALITY',{'model_id':base['library_model_id'],'selected_view':view,'exact_variant_hash':canon(base['exact_variant_state']),'state_side':'BASELINE_REQUIRED_SOURCE_COLLECTION'},cid]
        fid='FACT/'+canon(key)
        fact=facts.setdefault(fid,{'FACT_ID':fid,'FACT_TYPE':'SOURCE_REQUIRED_CARDINALITY_OBLIGATION','CANONICAL_KEY':key,'VALUE_TYPE':'Required keyed reference/lineage closure cardinality (registry) or exact required collection cardinality; never a global row census/new wire field','VALUE_IF_ESTABLISHED':None,'SOURCE':model['SOURCE_AUTHORITY'],'SOURCE_HASH':model['SOURCE_AUTHORITY']['sha256'],'SOURCE_VARIANTS':{},'DERIVATION':'Derive exact required parent-context instance roster and count after source key/lineage/exhaustiveness binding. Registry scope is referenced current/source/history keys and authenticated predecessor/tip closure, not unrelated global records. No row or graph count borrowed from an artifact.','DERIVATION_AUTHORITY':ref(D/'baseline-models.json','/models'),'DEPENDENT_WITNESSES':set(),'DEPENDENT_PREDICATES':set(),'PROJECTION_COUNT':0,'STATUS':'UNRESOLVED_CARDINALITY','fact_scope':'Required source context collection/closure root; supplemental to declared Hslot projections','equivalence_rule':'Same model/view/variant and exact source collection requirement, not shared physical instances'})
        fact['DEPENDENT_WITNESSES'].add(wid);fact['DEPENDENT_PREDICATES'].add(family_to_pred[family]);fact['SOURCE_VARIANTS'][canon(model['SOURCE_AUTHORITY'])]=model['SOURCE_AUTHORITY'];by_witness[wid].add(fid)
        supplemental_cardinality.append({'WITNESS_ID':wid,'COMPONENT_ID':cid,'FACT_ID':fid,'source':model['SOURCE_AUTHORITY'],'parent_scope':key[1]})
write('source-required-cardinality-roots.json',{'unique_supplemental_facts':len(facts)-primary_fact_count,'primary_slot_projection_count':0,'roots':supplemental_cardinality,'purpose':'Expose source-required collection roots omitted as dedicated slots in H. No individual row, value or exhaustive size inferred.'})
for f in facts.values():
    f['DEPENDENT_WITNESSES']=sorted(f['DEPENDENT_WITNESSES']);f['DEPENDENT_PREDICATES']=sorted(f['DEPENDENT_PREDICATES']);f['SOURCE_VARIANTS']=list(f['SOURCE_VARIANTS'].values())
status_counts=collections.Counter(f['STATUS'] for f in facts.values())
write('declared-slot-classification.json',{'total':93316,'class_counts':dict(classes),'slots':projections,'note':'Collection slots and rule/trace obligations are classified; no new physical fixture field is minted from a trace name.'})
write('canonical-fact-registry.json',{'total':len(facts),'primary_slot_facts':primary_fact_count,'supplemental_source_cardinality_facts':len(facts)-primary_fact_count,'status_counts':dict(status_counts),'facts':list(facts.values()),'fact_universe':'Finite source-scoped binding/value/derivation obligations covering all93316 slots plus source-required collection roots. Not a finite census of unbound catalog rows. Shared obligations do not assert shared physical identities.','DERIVABLE_semantics':'Reserved for source derivations with established required value dependencies but calculation pending. Algorithm/rule availability alone does not resolve a concrete trace or G_SOURCE value; those remain UNRESOLVED_BINDING here.','minimality':'Deduplicated under the explicitly recorded source-supported equivalence relation. Further equivalence or a globally smallest concrete fact universe is not established.'})
write('projection-deduplication.json',{'DECLARED_FIXTURE_SLOTS_TOTAL':93316,'CANONICAL_FACTS_TOTAL':len(facts),'PRIMARY_SLOT_FACTS_TOTAL':primary_fact_count,'SUPPLEMENTAL_SOURCE_CARDINALITY_FACTS':len(facts)-primary_fact_count,'PROJECTION_MULTIPLICITY_TOTAL':93316,'DEDUPLICATED_SLOT_COUNT':93316-primary_fact_count,'deduplication_formula':'Declared slots minus distinct facts represented by those slots; supplemental source-required roots have zero projection multiplicity and do not change slot denominator.','all_slots_mapped_once':True,'all_primary_facts_have_projection':sum(f['PROJECTION_COUNT']>0 for f in facts.values())==primary_fact_count,'equivalence_policy':'Native enums globally by exact actor/source; frame/bootstrap aliases only under frozen shared-context rule. Other roots retain model/view/variant, actor/schema field, and mutation/observation witness scope. No merge by equal spelling/hash alone.','counterexample_guards':'Different participant IDs and opposite generation deltas cannot merge; source/target and baseline/post-mutation coordinates remain distinct.'})

# Functional revalidation executes the pinned side-effect-free interpreter only.
interpreter_source=(H/'static_evaluator.py').read_text(encoding='utf-8')
tree=ast.parse(interpreter_source)
assert all((not isinstance(n,(ast.Import,ast.ImportFrom))) or ast.unparse(n) in ['import collections','import re'] for n in tree.body)
frozen={};exec(compile(interpreter_source,str(H/'static_evaluator.py'),'exec'),frozen)
unit_rows=validate(preds,frozen['observe'],frozen['dependencies_for'])
write('subpredicate-unit-revalidation.json',{'scope':'Generic deterministic normalized-operand interpreter tests, not canonical fixtures/witnesses/attacks','interpreter':ref(H/'static_evaluator.py'),'evaluator_programs':ref(H/'unique-predicate-registry.json'),'total':43,'results':unit_rows,'expected_canonical_result_consumed':False})
revalid=[]
for p in preds:
    if p['status']!='DERIVED_C5H':continue
    revalid.append({'EVALUATOR_ID':p['EVALUATOR_ID'],'PREDICATE_ID':p['PREDICATE_ID'],'INPUT_SCHEMA':p['INPUT_SCHEMA'],'OUTPUT_SCHEMA':{'availability':['AVAILABLE','UNAVAILABLE'],'value':'boolean iff AVAILABLE; otherwise null; UNAVAILABLE is not domain UNKNOWN'},'DETERMINISTIC_RULE':p['program'],'AUTHORITY_SOURCE':p['RULE_AUTHORITY_SOURCE'],'EXPECTED_RESULT_CONSUMED':'NO','SIDE_EFFECT_FREE':'YES','DATABASE_ACCESS':'NO','NETWORK_ACCESS':'NO','INDEPENDENTLY_EXECUTABLE':'YES_ON_SOURCE_NORMALIZED_TYPED_OPERANDS','VALID':True,'COMPOSABLE':'NO_COMPLETE_CANONICAL_COMPOSITION_CERTIFIED','local_typed_function_composable_conditionally':True,'composability_blockers':['Required operand bindings/normalization not complete','No full per-case native-decision/no-new-authority adapter certified','Availability/domain evidence/qualification outputs require separate sourced types'],'source_input_validation_scope':'Caller must validate complete source schema/types/ranges and normalization. Interpreter is not a full fixture validator.','functional_evidence':'subpredicate-unit-revalidation.json: both boolean branches and missing input observed for this exact program'})
write('subpredicate-evaluator-revalidation.json',{'total':43,'valid':43,'invalid':0,'composable_into_complete_canonical_evaluator_now':0,'noncomposable_into_complete_canonical_evaluator_now':43,'evaluators':revalid,'distinction':'Local pure typed-function validity/conditional interface compatibility is separate from certified canonical composition.'})

# Six exact blocked programs: facts/bindings plus known source semantics and
# still-unimplemented normalization/composition; not new project authority.
blocked=[]
for p in preds:
    if p['status']!='OTHER_BLOCKED':continue
    affected=[r['WITNESS_ID'] for r in records if r['WITNESS_ID'].split('/',1)[1] in p['families']]
    ids=sorted({fid for w in affected for fid in by_witness[w]})
    missing=[f for f in ids if facts[f]['STATUS']!='ESTABLISHED']
    cardinal=[f for f in ids if facts[f]['STATUS']=='UNRESOLVED_CARDINALITY']
    if 'REACHABLE' in p['operators'] or 'HAS_ADMIN_OPTION' in p['operators']:
        closure='Bind exact role identities, every pg_auth_members option and complete database-owner implicit edges; construct independent typed least-fixed-point MEMBER/SET/INHERIT paths and ADMIN self/superuser exceptions without merging edge kinds.'
    elif 'EXISTS_EFFECTIVE_CREATOR_DEFAULT' in p['operators']:
        closure='Bind actual creator/namespace/kind and full pg_default_acl row identity; distinguish global/schema semantic grouping from row OID; preserve absent/NULL/explicit-empty ACL, source hardwired defaults, owner implicit rights and future creation semantics.'
    elif 'HAS_SECURITY_DEFINER_PATH' in p['operators']:
        closure='Bind caller execute/schema usage and independently verified function owner/body/effect closure; compute reachable SECURITY_DEFINER effects, not a prosecdef-only flag.'
    else:
        closure='Bind complete source-expanded effect graph and allowlist, normalize the exact candidate EffectLeaf, then evaluate reachable write effects with principal/resource/type admission; a direct leaf scan is insufficient.'
    blocked.append({'BLOCKED_EVALUATOR_ID':p['EVALUATOR_ID'],'PREDICATE_ID':p['PREDICATE_ID'],'families':p['families'],'AFFECTED_WITNESSES':affected,'REQUIRED_INPUTS':frozen['dependencies_for'](p['program']),'AVAILABLE_INPUTS':{'frozen_rule':p['RULE_AUTHORITY_SOURCE'],'established_fact_ids':[f for f in ids if facts[f]['STATUS']=='ESTABLISHED']},'MISSING_INPUTS':missing,'MISSING_BINDINGS':'Exact source-identity/row/ACL/effect normalization to structured interpreter operands; see binding-graph.json','MISSING_CARDINALITY':cardinal,'MISSING_SEMANTICS':[],'AUTHORITY_GAP':'NO_MINIMUM_NEW_NORMATIVE_DECISION_DEMONSTRATED','RUNTIME_GAP':'NOT_ESTABLISHED','COMPOSITION_GAP':closure,'MINIMUM_CLOSURE_REQUIREMENT':closure,'CLASSIFICATION':'COMPOUND','classification_components':['SOURCE_BINDINGS','EXHAUSTIVE_COLLECTION_BINDINGS','NORMALIZATION_AND_COMPOSITION_ENGINEERING'],'source':p['source'],'no_stub_promoted_to_derived':True})
assert len(blocked)==6
write('blocked-evaluator-analysis.json',{'total':6,'classes':blocked,'class_count_unit':'Six exact predicate programs (including separate SET and INHERIT cases), not five primitive operator names','no_new_authority':True,'no_runtime_necessity_inferred':True})

# Semantic dependency hints are rooted in frozen operator/schema definitions.
# Where exact row/actor/reference mapping is not independently established the
# edge stays AMBIGUOUS or MISSING; candidate names never become a complete join.
def input_sources(wid,operand,p):
    slots=slot_meta[wid]
    exact=slots.get('predicate_operand/'+operand)
    if exact:return [exact['fact']],'COMPLETE','Exact source literal selected and independently normalized in C5H; no canonical expected classification consumed',exact['definition']
    op=set(p['operators']);candidates=[];source=p['source'];rule='No complete source-semantic adapter/row-instance selection established'
    if operand in {'catalog.pg_roles','R','actual_authenticated_SQL_role','expected_Reader_role','enrolled_reader_source_caller','actual_source_caller','authorized_HOST_PLATFORM_pre_enrollment_provisioner','claim.caller'}:
        candidates=[v['fact'] for k,v in slots.items() if k.startswith('catalog_rows[]/CATALOG/pg_catalog.pg_roles/') or k.startswith('DESIGN/PrincipalRef/')]
        rule='Source SQL role/expected Reader/caller identity must be selected by exact authenticated OID/name and context; native actor enums cannot supply it'
        source=ref(N1/'catalog-security-predicates.json','/predicates')
    elif operand in {'catalog.pg_auth_members','normalized_implicit_database_owner_edges','catalog.pg_database'} or 'REACHABLE' in op or 'HAS_ADMIN_OPTION' in op:
        candidates=[v['fact'] for k,v in slots.items() if any(k.startswith('catalog_rows[]/CATALOG/pg_catalog.'+n+'/') for n in ['pg_auth_members','pg_database','pg_roles'])]
        rule='Exact source memberships and database-owner implicit edges normalized with independent option dimensions; no R-row/session alias from name equality'
        source=ref(N1/'catalog-security-predicates.json','/role_edge_rules')
    elif operand in {'expected_reader_identity_row','observed_protected_rows_selected_by_expected_OID_OR_NAME','expected_protected_OID_name_roster','observed_rows','source_collection_snapshot_identities','incoming_backend_identity','pending_snapshot_backend_identity','incoming_native_lineage','pending_snapshot_native_lineage'}:
        candidates=[v['fact'] for k,v in slots.items() if k.startswith(('catalog_rows[]/','DESIGN/SnapshotHeader/','binding_trace/source_membrane'))]
        rule='Complete scoped snapshot/header and expected natural-key roster required; preserve row multiset, observation/backend/generation identity and absence-vs-query-failure distinction'
        source=ref(N1/'catalog-projection.json','/sources')
    elif operand in {'object_acls','protected_catalog_relation','fixed_source_operation_allowlist','fixed_source_callable_allowlist','frozen_object_oids','candidate_resolution','candidate_resolution.kind','catalog.pg_default_acl','source_hardwired_defaults','catalog.pg_proc','catalog.pg_namespace','verified_call_effect_graph','full_caller_execute_schema_usage_owner_proof','verified_source_expanded_effect_graph','expected_effect_allowlist','effect_reachability_and_admission_proof','candidate_effect_tree'}:
        candidates=[v['fact'] for k,v in slots.items() if k.startswith(('catalog_rows[]/','DESIGN/ACLRow/','DESIGN/EffectLeaf/','DESIGN/ResolutionExpression/','binding_trace/source_effect_and_ACL_model','binding_trace/source_membrane'))]
        rule='Frozen catalog/operator semantics define dependency domains, but exact source-expanded ACL/effect/object/allowlist normalization and reference identity remain unbound'
        source=ref(N1/'catalog-security-predicates.json','/predicates')
    elif operand in {'supplied_generation','current_independent_high_water','source_attestation.generation','claimed_target_generation','irreversible_retired_generation_set'}:
        candidates=[v['fact'] for k,v in slots.items() if k in {'current_generation','source_generation','mutation.source_bound_post_state'} or k.startswith(('REGISTRY/GENERATION','DESIGN/AuthorityClaim/'))]
        rule='Bind independent current ledger and separate source/target/retired claims; candidate claimed field does not update trusted high-water'
        source=ref(N/'native-registry-generation.json','/records')
    else:
        # A normalized scalar/tuple port may depend on native records, but the
        # unresolved actual/expected/post-mutation lineage cannot be guessed.
        candidates=[v['fact'] for k,v in slots.items() if k.startswith(('identity[','FRAME/','REGISTRY/','NESTED/','DESIGN/PrivateResourceRef/','DESIGN/WorkUse/')) or k=='mutation.source_bound_post_state']
        rule='Source case requires exact independent actual/expected or pre/post typed lineage; candidate components and trusted reference are not automatically the same instance'
        source=ref(F/'derived-canonical-350-registry.json',f"/case_records/{list(record_by_id).index(wid)}/AUTHORITY_FOR_BASELINE")
    candidates=sorted(set(candidates))
    return candidates,'AMBIGUOUS' if candidates else 'MISSING',rule,source

edges=[];ports={};bindings_per_witness=collections.defaultdict(list)
for rec in records:
    wid=rec['WITNESS_ID'];p=pred_by_id[family_to_pred[wid.split('/',1)[1]]]
    for operand in frozen['dependencies_for'](p['program']):
        port=wid+'::'+p['PREDICATE_ID']+'::'+operand
        source_facts,state,rule,authority=input_sources(wid,operand,p)
        # A candidate source group is not itself a complete semantic binding.
        edge={'BINDING_ID':'BINDING/'+canon([wid,p['PREDICATE_ID'],operand]),'SOURCE_FACT':source_facts,'TARGET_PREDICATE_INPUT':port,'BINDING_KEY':{'model_id':rec['BASELINE_STATE']['library_model_id'],'selected_view':rec['BASELINE_STATE']['selected_view'],'participant':rec['PARTICIPANT_CONTEXT']['subject'],'actor_or_row_role':'UNBOUND_UNLESS_SOURCE_NORMALIZATION_ESTABLISHES_IT','operand':operand},'BINDING_RULE':rule,'AUTHORITY_SOURCE':authority,'CARDINALITY':'Exact scalar/tuple or exhaustive keyed collection as source operator requires; instance count unresolved','TRANSFORMATION':'Identity/literal selection' if state=='COMPLETE' else 'Required typed source normalization/reference resolution not certified','LOSSLESS':'YES' if state=='COMPLETE' else 'NO','losslessness_status':'ESTABLISHED' if state=='COMPLETE' else 'NOT_ESTABLISHED','AMBIGUOUS':'YES' if state=='AMBIGUOUS' else 'NO','MISSING':'NO' if state=='COMPLETE' else 'YES','STATUS':state,'missing_actual_row_or_actor_binding':state!='COMPLETE','syntactic_match_accepted_as_semantic_binding':False}
        edge['CONTEXT_CARDINALITY_FACT_PREREQUISITES']=sorted(f for f in by_witness[wid] if facts[f]['STATUS']=='UNRESOLVED_CARDINALITY')
        edge['cardinality_prerequisite_scope']='Whole canonical case context validity; these are not asserted to be direct values of this operand or to invalidate a separately known literal projection'
        edges.append(edge);ports[port]=edge;bindings_per_witness[wid].append(edge['BINDING_ID'])
binding_counts=collections.Counter(e['STATUS'] for e in edges)
write('binding-graph.json',{'edges':edges,'total':len(edges),'status_counts':dict(binding_counts),'status_partition':'COMPLETE/MISSING/AMBIGUOUS/CONTRADICTED are exclusive; ambiguous edges also truthfully set MISSING=YES because no complete binding exists. Aggregate MISSING counter counts only exclusive MISSING status.','nodes':{'witnesses':350,'predicate_templates':49,'derived_evaluators':43,'blocked_evaluator_programs':6,'canonical_facts':len(facts)},'graph_links':'Witness fixture projection->fact IDs; each edge identifies guard template/instance port; evaluator mapping is the frozen one-to-one EVALUATOR_ID/PREDICATE_ID registry.','no_name_only_join':True})

# Recover only source-authorized partial dataflow, never a global49-guard order.
nodes=[];dag_edges=[]
def node(nid,pid,inputs,output,predecessors,source,kind,unknown='UNAVAILABLE proof input is not a domain UNKNOWN or qualification REJECT'):
    nodes.append({'NODE_ID':nid,'PREDICATE_ID':pid,'INPUTS':inputs,'OUTPUT':output,'PREDECESSORS':predecessors,'SUCCESSORS':[],'SHORT_CIRCUIT_RULE':'NOT_ESTABLISHED except exact sourced conditional below; no new early-accept/deny order','UNKNOWN_PROPAGATION_RULE':unknown,'REJECT_PROPAGATION_RULE':'Only within the exact typed qualification stage/source scope; no global propagation inferred','AUTHORITY_SOURCE':source,'NODE_KIND':kind})
def dag_edge(a,b,binding,source,condition='Exact case and validated source bindings'):
    dag_edges.append({'SOURCE_NODE':a,'TARGET_NODE':b,'OUTPUT_TO_INPUT_BINDING':binding,'ORDER_AUTHORITY':source,'CONDITIONALITY':condition})
seven={x['WITNESS_ID']:x for x in read(F/'seven-artifact-overrides.json')['overrides']}
for i,rec in enumerate(records):
    wid=rec['WITNESS_ID'];pid=family_to_pred[wid.split('/',1)[1]];source=ref(F/'derived-canonical-350-registry.json',f'/case_records/{i}')
    a='FIXTURE/'+wid;b='MUTATION/'+wid;c='GUARD/'+wid
    baseline_ids=sorted({v['fact'] for k,v in slot_meta[wid].items() if not k.startswith(('post.','predicate_operand/','mutation.','observation.'))})
    baseline_ids=sorted(set(baseline_ids)|{f for f in by_witness[wid] if facts[f]['FACT_TYPE']=='SOURCE_REQUIRED_CARDINALITY_OBLIGATION'})
    node(a,None,baseline_ids,'Source-bound canonical baseline inputs only; post-state/observation obligations excluded; currently incomplete',[],source,'BASELINE_PROJECTION')
    node(b,None,[a,rec['MUTATION']['descriptor_id']],'Exact post-mutation typed state and dependent digest trace',[a],source,'MUTATION_DATAFLOW')
    node(c,pid,[x['TARGET_PREDICATE_INPUT'] for x in edges if x['TARGET_PREDICATE_INPUT'].startswith(wid+'::')],{'availability':'AVAILABLE/UNAVAILABLE','value':'boolean/null'},[b],source,'ALTERNATIVE_CASE_GUARD')
    dag_edge(a,b,'Full baseline -> exact source descriptor input; missing facts prevent execution',source)
    dag_edge(b,c,'Post-state -> independently normalized guard operands; missing/ambiguous mappings recorded in binding-graph',source)
    node('NON_GRANT/'+wid,None,['actual_pre_authority_work_publication_state','actual_post_authority_work_publication_state'],'Independent no-new-authority delta (not evaluated)',[],ref(F/'derived-canonical-350-registry.json',f'/case_records/{i}/EXPECTED_DECISION_PREDICATE/PASS'),'REQUIRED_PROOF_OBSERVATION')
    if wid in seven:
        stage1='EVIDENCE_AVAILABILITY/'+wid;pre='QUALIFICATION_PREREQUISITE/'+wid;stage2='QUALIFICATION_DECISION/'+wid
        src=ref(F/'seven-artifact-overrides.json',f"/overrides/{list(seven).index(wid)}")
        node(stage1,pid,[c,'exact required Reader row identity and validated bounded omission state'],{'object':'REQUIRED_CATALOG_IDENTITY_ROW_EVIDENCE','domain':'EVIDENCE_AVAILABILITY','bounded_omission_result':'UNKNOWN'},[c],src,'SCOPED_EVIDENCE_RESOLUTION','UNKNOWN is a domain evidence-availability value, not interpreter UNAVAILABLE')
        node(pre,None,[stage1],'Positive target qualification prerequisite unsatisfied for exact seven omissions',[stage1],src,'SCOPED_ORDERED_MAPPING')
        node(stage2,None,[pre],{'object':'TARGET_GENERATION_CREDENTIAL_AUTHORITY_QUALIFICATION','domain':'QUALIFICATION_DECISION','result':'REJECT'},[pre],src,'SCOPED_QUALIFICATION_DECISION','Normative mapping only for these exact seven, not observed proof')
        dag_edge(c,stage1,'Only independently established exact bounded omission -> domain evidence UNKNOWN',src,'All source baseline and exact row/key evidence valid; not mere missing proof inputs')
        dag_edge(stage1,pre,'Typed UNKNOWN availability -> prerequisite unsatisfied',src,'Exact seven scoped cases only')
        dag_edge(pre,stage2,'Unsatisfied prerequisite -> typed qualification REJECT',src,'Exact prospective authority; no wire-code selection')
qualification=read(N1/'participant-qualification.json')
for i,q in enumerate(qualification['matrix']):
    name=q['PARTICIPANT_ID'];required=[x['args'][0] for x in q['qualification']['args']]
    node('NATIVE_QUALIFICATION_TEMPLATE/'+name,None,required,{'rule':'ALL_KNOWN_TRUE','unknown':'NOT_QUALIFIED; no UNKNOWN=REJECT equivalence or wire conversion'},[],ref(N1/'participant-qualification.json',f'/matrix/{i}/qualification'),'POSITIVE_QUALIFICATION_TEMPLATE','Unknown prerequisite remains NOT_QUALIFIED; exact domain/stage retained')
node('I13_CROSS_CUTTING',None,['seven concurrent subject principal pairs','required auxiliary separation'],'Full independent I13 predicate; no new principal assignments',[],ref(N1/'independence-matrix.json'),'INDEPENDENT_INVARIANT')
index={n['NODE_ID']:n for n in nodes}
for e in dag_edges:index[e['SOURCE_NODE']]['SUCCESSORS'].append(e['TARGET_NODE'])
incoming=collections.Counter(e['TARGET_NODE'] for e in dag_edges);queue=[k for k in index if incoming[k]==0];visited=[]
while queue:
    n=queue.pop();visited.append(n)
    for s in index[n]['SUCCESSORS']:
        incoming[s]-=1
        if incoming[s]==0:queue.append(s)
cycles=len(index)-len(visited)
assert cycles==0
unbound_ports=[k for k,e in ports.items() if e['STATUS']!='COMPLETE']
extra_unbound=[n['NODE_ID']+'::'+str(i) for n in nodes if n['NODE_KIND'] in {'POSITIVE_QUALIFICATION_TEMPLATE','REQUIRED_PROOF_OBSERVATION','INDEPENDENT_INVARIANT'} for i in n['INPUTS']]
extra_unbound += [n['NODE_ID']+'::EXACT_BOUNDED_OMISSION_BINDING' for n in nodes if n['NODE_KIND']=='SCOPED_EVIDENCE_RESOLUTION']
write('canonical-decision-dag.json',{'status':'INCOMPLETE_CASE_SCOPED_FOREST','nodes':nodes,'edges':dag_edges,'CANONICAL_DECISION_NODES':len(nodes),'CANONICAL_DECISION_EDGES':len(dag_edges),'UNBOUND_DECISION_INPUTS':len(unbound_ports)+len(extra_unbound),'unbound_input_count_boundary':'Normalized guard and decision/invariant raw input ports, including seven bounded-omission identity/validity ports. Upstream baseline fact obligations are counted in fact registry, not counted again as decision ports. Structurally bound predecessor output ports are separate from whether an observed value exists.','unbound_normalized_guard_ports':unbound_ports,'unbound_other_required_inputs':extra_unbound,'UNORDERED_REQUIRED_RELATIONS':0,'unordered_relation_semantics':'No unestablished ordering has been declared required. Independent guards are alternatives, not an unordered mandatory49-stage chain. Missing per-case decision/non-grant adapters remain composition gaps, not invented ordering decisions.','CYCLES_DETECTED':cycles,'predicate_relationships':'50 mutation families use49 alternative guard templates; wrong/stale generation share one NE template.350 case instances remain distinct. Seven scoped typed omission chains are sourced. Positive qualification templates are separate and are not implemented by ANDing the negative case guards.','source_prerequisite_preservation':{'registry_replacement':ref(N/'native-registry-generation.json','/records'),'note':'Source replacement/revocation/reconciliation/extinction/tombstone prerequisites preserved as binding obligations; no serial order among independent prerequisites invented.'},'full_canonical_decision_recovered':False})

projections_by_witness=collections.defaultdict(list)
for pr in projections:projections_by_witness[pr['WITNESS_ID']].append(pr)
fixture_projections=[];results=[]
for rec in records:
    wid=rec['WITNESS_ID'];ids=sorted(by_witness[wid]);missing=[x for x in ids if facts[x]['STATUS']!='ESTABLISHED'];card=[x for x in missing if facts[x]['STATUS']=='UNRESOLVED_CARDINALITY'];bids=[e['BINDING_ID'] for e in edges if e['TARGET_PREDICATE_INPUT'].startswith(wid+'::') and e['STATUS']!='COMPLETE']
    fixture={'WITNESS_ID':wid,'CANONICAL_FACT_IDS':ids,'PROJECTION_RULE':'Exact C5H slot ordinals -> source-scoped primary fact IDs in declared-slot-classification; select value only if ESTABLISHED. Repeated projections do not become independently invented values. No expansion of unresolved row[] cardinality.','FIXTURE_COMPLETE':'NO','MISSING_CANONICAL_FACT_IDS':missing,'MISSING_BINDING_IDS':bids,'MISSING_CARDINALITY_IDS':card,'canonical_fact_values_hash':canon({x:facts[x]['VALUE_IF_ESTABLISHED'] for x in ids if facts[x]['STATUS']=='ESTABLISHED'}),'source_packet_hash':canon(packets[list(record_by_id).index(wid)])}
    fixture['FIXTURE_HASH']=canon(fixture);fixture_projections.append(fixture)
    results.append({'WITNESS_ID':wid,'FIXTURE_HASH':fixture['FIXTURE_HASH'],'canonical_evaluator_available':False,'canonical_evaluation_executed':False,'OBSERVED_RESULT':None,'PROOF_STATUS':'UNKNOWN','reason':'Incomplete canonical value/cardinality/semantic binding plus uncertified full decision/no-grant composition. No expected outcome consumed or manufactured.'})
assert len(fixture_projections)==len(results)==350
write('witness-fixture-projections.json',{'total':350,'complete':0,'incomplete':350,'fixtures':fixture_projections,'no_unresolved_values_filled':True})
write('static-evaluation-results.json',{'total':350,'eligible_complete_fixtures':0,'complete_canonical_evaluators':0,'canonical_evaluations_executed':0,'results':results,'interpreter_tests_are_not_canonical_proofs':True})
write('canonical-evaluator-analysis.json',{'COMPLETE_CANONICAL_DECISION_EVALUATORS':0,'requirements':{'canonical_source_component_schema':'RECOVERED_WITH_TAGGED_OPTIONALITY_AND_SCOPE','actual_row_cardinality_and_exhaustiveness':'NOT_BOUND','all_required_inputs':'MISSING_OR_AMBIGUOUS','49_guard_semantics':'FROZEN;43_LOCAL_FUNCTIONS_VALID;6_FULL_NORMALIZATIONS_NOT_IMPLEMENTED','decision_DAG':'SOURCE_AUTHORIZED_PARTIAL_FOREST_ONLY','unknown_reject_propagation':'EXACT_SEVEN_SCOPED_COMPOSITION_RECOVERED;NO_GLOBAL_EQUIVALENCE','required_order':'NO49_STAGE_ORDER_REQUIRED_OR_INVENTED','expected_result_dependency':'NONE','production_implementation_executed':'NO'},'minimum_blockers':['Bind source-scoped values and validated symbolic/concrete row instances with full collection boundaries','Complete exact normalized SQL role/ACL/implicit-owner/effect adapters and six blocked source transformations','Assemble source-typed per-case guard-to-decision and independent no-new-authority trace; do not conflate guard boolean, UNAVAILABLE, evidence UNKNOWN, NOT_QUALIFIED and qualification REJECT'],'new_project_authority_required':'NOT_DEMONSTRATED','runtime_necessity':'NOT_DEMONSTRATED','why_no_full_evaluator_created':'Section14 preconditions not established; a wrapper that copies prescribed decisions or boolean outputs would be circular/incomplete.'})

summary={'BRANCH':git('branch','--show-current'),'BASELINE_HEAD':'cbc284f62d9bd09b7169b55c8d66a3c51a68c6cb','CURRENT_HEAD':git('rev-parse','HEAD'),'TRACKED_DIRTY_COUNT':0,'STAGED_COUNT':0,'AUTHORIZED_UNTRACKED_FILES_BEFORE':199,'UNAUTHORIZED_UNTRACKED_COUNT':0,'C5H_INPUT_INTEGRITY':'PASS','CANONICAL_CASES_TOTAL':350,'DECLARED_FIXTURE_SLOTS_TOTAL':93316,'CANONICAL_FACTS_TOTAL':len(facts),'ESTABLISHED_CANONICAL_FACTS':status_counts['ESTABLISHED'],'DERIVABLE_CANONICAL_FACTS':status_counts['DERIVABLE'],'UNRESOLVED_BINDING_FACTS':status_counts['UNRESOLVED_BINDING'],'UNRESOLVED_CARDINALITY_FACTS':status_counts['UNRESOLVED_CARDINALITY'],'AUTHORITY_REQUIRED_FACTS':0,'RUNTIME_REQUIRED_FACTS':0,'CONTRADICTED_FACTS':0,'PROJECTION_MULTIPLICITY_TOTAL':93316,'DEDUPLICATED_SLOT_COUNT':93316-len(facts),'BINDING_EDGES_TOTAL':len(edges),'BINDING_EDGES_COMPLETE':binding_counts['COMPLETE'],'BINDING_EDGES_MISSING':binding_counts['MISSING'],'BINDING_EDGES_AMBIGUOUS':binding_counts['AMBIGUOUS'],'BINDING_EDGES_CONTRADICTED':0,'UNIQUE_PREDICATES_TOTAL':49,'SUBPREDICATE_EVALUATORS_TOTAL':43,'SUBPREDICATE_EVALUATORS_VALID':43,'SUBPREDICATE_EVALUATORS_INVALID':0,'SUBPREDICATE_EVALUATORS_COMPOSABLE':0,'SUBPREDICATE_EVALUATORS_NONCOMPOSABLE':43,'BLOCKED_EVALUATOR_CLASSES_TOTAL':6,'CANONICAL_DECISION_DAG_STATUS':'INCOMPLETE_CASE_SCOPED_FOREST','CANONICAL_DECISION_NODES':len(nodes),'CANONICAL_DECISION_EDGES':len(dag_edges),'UNBOUND_DECISION_INPUTS':len(unbound_ports)+len(extra_unbound),'UNORDERED_REQUIRED_RELATIONS':0,'CYCLES_DETECTED':0,'COMPLETE_CANONICAL_DECISION_EVALUATORS':0,'FIXTURES_TOTAL':350,'FIXTURES_COMPLETE':0,'FIXTURES_INCOMPLETE':350,'STATICALLY_PROVEN':0,'STATICALLY_DISPROVEN':0,'UNKNOWN':350,'CONTRADICTED':0,'SUBSTITUTION_WITNESSES_REQUIRED':350,'SUBSTITUTION_WITNESSES_PROVEN':0,'SUBSTITUTION_WITNESSES_UNKNOWN':350,'N1_SUBSTITUTION_STATIC_WITNESSES':'OPEN','N1_DECISIONS_REQUIRED':12,'N1_DECISIONS_CLOSED':11,'N1_DECISIONS_OPEN':1,'V2_NATIVE_STATIC_DESIGN_PROOF':'FAIL','V2_NATIVE_STATUS':'BLOCKED','PROJECT_AUTHORITY_TRANSITION':'T8','TRANSITION_RESOLVED':'YES','POSTMASTER_CONTEXT_BINDING_RESOLVED':'NO','INTERNAL_SCOPE_RESOLVED':'NO','ATOMIC_BOUNDARY_RESOLVED':'NO','CANONICAL_INTERNAL_OBLIGATION_UNIVERSE_ESTABLISHED':'NO','ATOMIC_NORMATIVE_CANDIDATES_TOTAL':108,'AMBIGUOUS_CANDIDATES_PRESERVED':105,'CANONICAL_ATTACK_DENOMINATOR':350,'DENOMINATOR_CHANGED':'NO','ATTACKS_MATERIALIZED_THIS_GATE':0,'ATTACKS_EVALUATED_THIS_GATE':0,'SHARED_DB_CONTACTED':'NO','PRODUCTION_CONTACTED':'NO','EXISTING_LOCAL_DB_CONTACTED':'NO','NETWORK_CONTACT_FOR_PROOF':'NO','V043_EXECUTED':'NO','V043_CHANGED':'NO','B02_EXECUTED':'NO','GIT_ADD':'NO','COMMIT':'NO','PUSH':'NO','SELECTED_OUTCOME':'H_COMPOUND_STATIC_GAPS_REMAIN','NEXT_EXECUTED':False,'NEXT_GATE':'BOUNDED_COMPOUND_STATIC_GAP_DECOMPOSITION'}
assert sum(status_counts.values())==len(facts)
summary['DEDUPLICATED_SLOT_COUNT']=93316-primary_fact_count
summary['PRIMARY_SLOT_FACTS_TOTAL']=primary_fact_count
summary['SUPPLEMENTAL_SOURCE_CARDINALITY_FACTS']=len(facts)-primary_fact_count
write('coverage-accounting.json',summary);write('final-summary.json',summary)
write('primary-result.json',{'outcome':summary['SELECTED_OUTCOME'],'reason':'Source value/reference bindings, exhaustive row-instance cardinality and complete decision/effect composition remain independent necessary blockers. No evidence establishes one as the sole/dominant cause; resolving any one alone leaves the others.','taxonomy_routing':'H -> BOUNDED_COMPOUND_STATIC_GAP_DECOMPOSITION','technical_progress':'All93316 projections reconciled into source-scoped fact equivalence classes; raw collection semantics recovered;43 local guard evaluators exercised on both boolean branches; six exact blocked normalizations separated; only authorized partial dataflow/scoped omission ordering recovered.','limits':'Factorization covers scoped binding obligations, not a complete census or globally minimal physical fact universe. No full canonical fixture/evaluator or witness proof is claimed. Unknown inputs are preserved.','next_executed':False})
print(json.dumps({'facts':len(facts),'statuses':dict(status_counts),'slot_projections':len(projections),'bindings':dict(binding_counts),'guard_evaluators_validated':len(unit_rows),'dag_nodes':len(nodes),'dag_edges':len(dag_edges),'outcome':summary['SELECTED_OUTCOME']}))
