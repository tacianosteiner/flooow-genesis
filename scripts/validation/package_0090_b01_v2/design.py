"""B01 V2 design derivation. Candidate mechanisms are not runtime proofs."""
import collections
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import package_0090_source_closure as q

OUT=q.ROOT/'docs/evidence/package-0090-B01-v2-expanded-capability-mediation'
OLD=q.ROOT/'docs/evidence/package-0090-full-reachable-expectation-closure-v2'
BASELINE='671cc948b4802f3b44c5888756cd6cce032e0b4a'

def read(folder,name):return json.loads((folder/name).read_text())
def save(name,data):(OUT/name).write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
def digest(value):return q.sha(json.dumps(value,sort_keys=True,separators=(',',':')).encode())

# Explicit semantic partitions. Compound definition fields remain whole frozen
# objects; subtype partitions are separately retained for constraints and ACLs.
GROUPS={
 'audit_binding':{'AUDIT_IDENTITY':['decision_id','approval_id','change_id','actor','source_context','activation_recipe'],'AUDIT_CONTEXT':['deployment_incarnation','policy_version_digest','effective_from'],'AUDIT_TRANSACTION':['transaction_identity','PREPARED','terminal_outcome'],'AUDIT_TIP':['trusted_tip','hash_chain','future_currentness_link']},
 'column':{'COLUMN_IDENTITY':['relation','attnum','name','is_local','inheritance_count','dropped'],'COLUMN_TYPE':['type','typmod','collation'],'COLUMN_NULLABILITY':['not_null'],'COLUMN_GENERATION':['generated','identity'],'COLUMN_DEFAULT':['default'],'COLUMN_ACL':['column_acl']},
 'constraint':{'CONSTRAINT_DEFINITION':['relation','source'],'CONSTRAINT_REACHABILITY':['classification','runtime_READ_does_not_fire']},
 'database_environment':{'DATABASE_ENCODING':['encoding'],'DATABASE_COLLATION':['locale_provider','collate','ctype','locale_version'],'DATABASE_OWNER':['owner']},
 'default_expression':{'COLUMN_DEFAULT':['relation','column','expression'],'DEFAULT_REACHABILITY':['classification','runtime_read']},
 'effective_acl':{'EFFECTIVE_ACL':['role','kind','object','column','privilege','allowed','grantable','binding']},
 'expected_release':{'EXPECTED_RELEASE_IDENTITY':['source_hash','recipe_hashes','provider_hashes','component_hashes','manifest_identity']},
 'expression':{'SOURCE_EXPRESSION':['SITE_ID','SOURCE_LOCATION','SOURCE_EXPRESSION','source_site_sha256'],'EXPRESSION_RESOLUTION':['EXPRESSION_KIND','STATIC_INPUT_TYPES','EXPECTED_OUTPUT_TYPE','EXPECTED_PROVIDER','EXPECTED_CAST_PATH','EXPECTED_COLLATION','EXPECTED_RESOLUTION_STATUS','analysis'],'EXPRESSION_CONTEXT':['CONTROL_PATH','EXPECTED_SECURITY_CONTEXT','EXPECTED_ERROR_NULL_RELEVANCE']},
 'future_default_acl':{'DEFAULT_PRIVILEGE':['PUBLIC','creator','extra_grantees','object_kind','owner','schema']},
 'index':{'INDEX_IDENTITY':['name','relation'],'INDEX_DEFINITION':['keys','method','nulls_not_distinct','predicate','primary','source','unique']},
 'inheritance_absence':{'INHERITANCE_ABSENCE':['inhrelid','inhparent','partition_bounds']},
 'membership_absence':{'ROLE_MEMBERSHIP':['roleid','member','grantor','admin_option','inherit_option','set_option']},
 'native_ELF':{'PROVIDER_ELF':['path','sha256','owner_rule']},
 'native_anchor':{'NATIVE_ANCHOR':['root_assumption','rule']},
 'native_binding':{'NATIVE_ENROLLMENT':['binary_native_identity','channel','enrollment','epoch','generation','nonce','process_pidfd'],'NATIVE_WORK':['counter','dependency_catalog','functional_work'],'NATIVE_GUARD':['freshness','guard_decision','guard_proof','future_T9_T10']},
 'native_locale':{'PROVIDER_LOCALE':['path','sha256']},
 'native_module':{'NATIVE_MODULE_IDENTITY':['path','sha256','source_files','build']},
 'native_participant':{'NATIVE_PROCESS_IDENTITY':['PARTICIPANT_NAME','IDENTITY_SOURCE','IDENTITY_BINDING'],'NATIVE_GENERATION':['GENERATION_SOURCE','GENERATION_BINDING','GENERATION_CREATED_WHEN','GENERATION_INVALIDATED_WHEN','GENERATION_STORED_WHERE','GENERATION_OBSERVED_BY','STALE_GENERATION_DENIAL','RESTART_BEHAVIOR'],'NATIVE_WORK':['LIVENESS_SOURCE','PROGRESS_SOURCE','COMPLETED_WORK_WITNESS','INDEPENDENT_OBSERVER','FAIL_CLOSED_ACTION']},
 'policy_readiness_binding':{'POLICY_STATE':['policy_version','policy_digest','effective_from','activation_decision'],'BINDING_STATE':['binding_header','deployment','incarnation','lifecycle_state'],'READINESS_MODEL_STATE':['eligibility','currentness_manifest','history_expectation','original_attestation','native_health_proof','participant_generation_vector','guard_proof','trusted_audit_terminal','effective_ACL']},
 'provider_ABI':{'PROVIDER_ABI':['immutable_image','full_bootstrap_catalog','extension_versions','loaded_library_epoch']},
 'relation':{'RELATION_IDENTITY':['name','kind','persistence'],'RELATION_OWNER':['owner'],'RELATION_RLS':['RLS','force_RLS'],'VIEW_DEFINITION':['expansion','security_invoker']},
 'return_consumer':{'RETURN_CONSUMER_SHAPE':['declared_tuple','projected_tuple'],'HISTORY_CONTENT':['ordered42rows','exact_content']},
 'role':{'ROLE_ATTRIBUTE':['name','login','inherit','superuser','create_role','create_db','replication','bypass_rls']},
 'role_superuser':{'BOOTSTRAP_ROLE_ATTRIBUTE':['rolsuper','rolcanlogin'],'DATABASE_OWNER':['implicit_database_owner']},
 'sequence_absence':{'SEQUENCE_ABSENCE':['column_identity','default_nextval','owned_sequence_dependency']},
 'session_environment':{'CONSUMER_SESSION_IDENTITY':['session_user'],'CONSUMER_EFFECTIVE_ROLE':['effective_role'],'CONSUMER_SESSION_SETTINGS':['encoding','search_path','timezone','standard_conforming_strings'],'CONSUMER_TRANSACTION_ISOLATION':['transaction_isolation']},
 'storage_binding':{'CATALOG_STORAGE_BINDING':['owner','parent','required','rule']},
 'toast_factory':{'TOAST_IDENTITY':['namespace','kind','persistence','rowtype_oid','recursive_toast_oid'],'TOAST_STORAGE':['attcompression','attnotnull','attstorage','RLS'],'TOAST_INDEX':['index_method','index_opclasses','index_options','index_primary','index_unique']},
 'trigger':{'TRIGGER_DEFINITION':['relation','source'],'TRIGGER_REACHABILITY':['classification','proof','runtime_reachable']},
 'view_expansion':{'VIEW_DEFINITION':['full_view_query','owner','security_barrier','security_invoker','ordered_output']},
}

def groups(row):
    kind=row['OBJECT_CLASS'];fields=set(row['FIELDS'])
    if kind in GROUPS:return GROUPS[kind]
    if kind.startswith('catalog_'):
        owner=[f for f in row['FIELDS'] if f.endswith('owner')]
        return {'CATALOG_PROVIDER_DEFINITION':[f for f in row['FIELDS'] if f not in owner],**({'CATALOG_PROVIDER_OWNER':owner} if owner else {})}
    if kind in ['builtin_function','source_native_function','function_candidate_signature']:
        result=collections.defaultdict(list)
        for field in row['FIELDS']:
            if field in ['proowner','owner']:mechanism='FUNCTION_OWNER'
            elif field in ['proacl','raw_acl']:mechanism='FUNCTION_ACL'
            elif field in ['proconfig','config']:mechanism='FUNCTION_CONFIG'
            elif field in ['prosrc','prosqlbody','source','probin','library']:mechanism='FUNCTION_BODY_PROVIDER'
            elif field in ['proargdefaults','expected_defaults_SQL','defaults_SQL']:mechanism='FUNCTION_DEFAULTS'
            elif field in ['oid','proname','pronamespace','signature']:mechanism='FUNCTION_IDENTITY'
            else:mechanism='FUNCTION_SIGNATURE_METADATA'
            result[mechanism].append(field)
        return dict(result)
    if kind in ['builtin_type','candidate_type_metadata','generated_array','generated_composite']:
        result=collections.defaultdict(list)
        for field in row['FIELDS']:
            if field=='typowner':m='TYPE_OWNER'
            elif field=='typacl':m='TYPE_ACL'
            elif field in ['typdefault','typdefaultbin']:m='TYPE_DEFAULT'
            elif field in ['typinput','typoutput','typreceive','typsend','typmodin','typmodout','typsubscript','typanalyze']:m='TYPE_PROVIDER'
            else:m='TYPE_METADATA'
            result[m].append(field)
        return dict(result)
    if kind=='collation':return {'COLLATION_OWNER':[f for f in row['FIELDS'] if f=='collowner'],'COLLATION_METADATA':[f for f in row['FIELDS'] if f!='collowner']}
    raise RuntimeError('No explicit mechanism assignment for '+kind)

EPOCH={'ROLE_ATTRIBUTE','BOOTSTRAP_ROLE_ATTRIBUTE','ROLE_MEMBERSHIP','DATABASE_OWNER','RELATION_IDENTITY','RELATION_OWNER','RELATION_RLS','COLUMN_IDENTITY','COLUMN_TYPE','COLUMN_NULLABILITY','COLUMN_GENERATION','COLUMN_DEFAULT','COLUMN_ACL','CONSTRAINT_DEFINITION','CONSTRAINT_REACHABILITY','DEFAULT_REACHABILITY','EFFECTIVE_ACL','DEFAULT_PRIVILEGE','INDEX_IDENTITY','INDEX_DEFINITION','INHERITANCE_ABSENCE','DATABASE_ENCODING','DATABASE_COLLATION','FUNCTION_OWNER','FUNCTION_ACL','FUNCTION_CONFIG','FUNCTION_BODY_PROVIDER','FUNCTION_DEFAULTS','FUNCTION_IDENTITY','FUNCTION_SIGNATURE_METADATA','TYPE_OWNER','TYPE_ACL','TYPE_DEFAULT','TYPE_PROVIDER','TYPE_METADATA','COLLATION_OWNER','COLLATION_METADATA','CATALOG_PROVIDER_DEFINITION','CATALOG_PROVIDER_OWNER','CATALOG_STORAGE_BINDING','TOAST_IDENTITY','TOAST_STORAGE','TOAST_INDEX','TRIGGER_DEFINITION','TRIGGER_REACHABILITY','VIEW_DEFINITION','SEQUENCE_ABSENCE','RETURN_CONSUMER_SHAPE','HISTORY_CONTENT','SOURCE_EXPRESSION','EXPRESSION_RESOLUTION','EXPRESSION_CONTEXT'}

def derive():
    baseline=read(OUT,'baseline-freeze.json')
    for path,sha in baseline['input_hashes'].items():q.require(q.sha((q.ROOT/path).read_bytes())==sha,'Frozen input drift: '+path)
    denominator=read(OLD,'mutation-class-denominator-v3.json');partitions=[];missing=[]
    for row in denominator['classes']:
        mapping=groups(row);covered=set().union(*(set(fs) for fs in mapping.values()))
        if covered!=set(row['FIELDS']):missing.append(dict(CLASS_ID=row['CLASS_ID'],unassigned=sorted(set(row['FIELDS'])-covered),unexpected=sorted(covered-set(row['FIELDS']))))
        for mechanism,fields in mapping.items():
            q.require(bool(fields),'Empty mechanism partition')
            if mechanism in EPOCH:route='BOOTSTRAP_ONLY_CAPABILITY';path='EPOCH_REPLACEMENT_MUTATION'
            elif mechanism.startswith('CONSUMER_'):route='SESSION_SELF_MUTATION';path='IDENTIFIED_SAME_CONNECTION_WITH_IMMUTABLE_SESSION_USER_PARTITION'
            elif mechanism.startswith(('PROVIDER_','EXPECTED_RELEASE')):route='TRUST_BOUNDARY_ONLY';path='IMMUTABLE_DURING_SEALED_OR_APPROVED_EPOCH_REPLACEMENT'
            elif mechanism.startswith(('AUDIT_','POLICY_','BINDING_','READINESS_')):route='NEW_TYPED_AUDIT_CAPABILITY';path='TYPED_EXTERNAL_QUALIFICATION_EVENT'
            elif mechanism.startswith('NATIVE_'):route='NEW_TYPED_NATIVE_CAPABILITY';path='TYPED_IDENTIFIED_NATIVE_TRANSITION'
            else:raise RuntimeError('Unassigned capability route '+mechanism)
            partitions.append(dict(PARTITION_ID=row['CLASS_ID']+'/'+mechanism,CLASS_ID=row['CLASS_ID'],OBJECT_CLASS=row['OBJECT_CLASS'],MECHANISM_ID=mechanism,FIELDS=fields,GRAPH_OBJECTS=row['GRAPH_OBJECTS'],REQUIRED_MUTATION_SEMANTICS='Exact frozen '+mechanism+' definition/state mutation; structural immutability requires its own proof, not a substituted mutable fixture',CAPABILITY_CLASS=route,PROPOSED_PATH=path,implementation_status='CANDIDATE_NOT_QUALIFIED',representative_adequacy_proven=False))
    save('class-mechanism-partitions.json',dict(denominator_sha256=q.sha((OLD/'mutation-class-denominator-v3.json').read_bytes()),class_count=len(denominator['classes']),partition_count=len(partitions),all_top_level_fields_assigned=not missing,unassigned=missing,partitions=partitions,CLASS_MECHANISM_PARTITION_COMPLETE=False,qualification_caveat='Top-level field coverage is a necessary inventory, not proof that compound AST/ACL/native work partitions are adequate. Nested mechanism and runtime target coverage require independent closure.'))
    capabilities=[]
    for mechanism in sorted({p['MECHANISM_ID'] for p in partitions}):
        ps=[p for p in partitions if p['MECHANISM_ID']==mechanism];route=ps[0]['CAPABILITY_CLASS']
        capabilities.append(dict(CAPABILITY_ID='0090/B01V2/'+mechanism,AUTHORIZED_CLASS_IDS=sorted({p['CLASS_ID'] for p in ps}),AUTHORIZED_MECHANISMS=[mechanism],AUTHORIZED_TARGETS=sorted({g for p in ps for g in p['GRAPH_OBJECTS']}),FIXED_OPERATION='CANDIDATE_'+mechanism,REQUIRED_DB_ROLE_PATH='Exited out-of-epoch deployment bootstrap; no owner SET or admin capability during SEALED' if route=='BOOTSTRAP_ONLY_CAPABILITY' else 'Separate non-superuser fixed worker; no campaign credential',REVERSIBILITY='Independent exact semantic reversal or discard owned target; never assume rollback',OUTCOME_PROOF='Independent protected projection plus transaction/process/ledger outcome as applicable; not a command ACK',CAPABILITY_CLASS=route,INPUT_SCHEMA=dict(operation_id='exact enum',class_id='exact authorized enum',target_id='exact frozen enum',expected_precondition='exact frozen contract digest'),FIXED_IMPLEMENTATION=None,DB_OS_PRINCIPAL=None,LIFECYCLE='Capability delivered only after durable invalidation; bootstrap only after epoch CLOSED',PRECONDITIONS='Exact source/provider/target identity, no pending transition',TRANSITION_REQUIREMENT='Exclusive lease, PREPARED fsync, non-SEALED and incremented generation before visibility',GENERATION_RULE='Never reuse/decrement; missing state denies',RECONCILIATION_RULE='Independent known outcome required; UNKNOWN cannot directly reseal',AUDIT_BINDING=['epoch','transition','class','mechanism','target','actor','capability','generation_before','generation_after','outcome','reconciliation','terminal_tip'],REVERSAL_TEARDOWN='Worker/session/credential gone before reseal; exact whole protected-state projection comparison',SEALED_AVAILABILITY='No bootstrap/admin worker; immutable closed coordinator only',qualified=False))
    save('typed-capability-catalog.json',dict(candidate=True,PROPOSED_TYPED_CAPABILITIES_TOTAL=len(capabilities),capabilities=capabilities,executable_templates_complete=False,typed_catalog_not_execution_authority=True))
    save('minimal-capability-derivation.json',dict(proposed_routes=dict(collections.Counter(p['CAPABILITY_CLASS'] for p in partitions)),NEW_CAPABILITY_TYPES_REQUIRED=len({p['CAPABILITY_CLASS'] for p in partitions}-{'EXISTING_B01_CAPABILITY'}),no_SU_or_owner_membership_proposed_during_SEALED=True,role_admin='CREATEROLE plus target ADMIN OPTION still cannot mutate superuser roles; use closed-epoch bootstrap instead of broad live administration',not_a_runtime_proof=True))
    print(json.dumps(dict(classes=46,partitions=len(partitions),top_level_unassigned=missing,candidate_capabilities=len(capabilities))))

if __name__=='__main__':derive()
