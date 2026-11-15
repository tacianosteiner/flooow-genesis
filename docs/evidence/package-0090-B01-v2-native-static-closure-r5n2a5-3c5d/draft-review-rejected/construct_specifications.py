"""C5D documentation constructor. Writes symbolic specifications; never evaluates them."""
import collections
import hashlib
import itertools
import json
import pathlib
import subprocess

ROOT=pathlib.Path(__file__).resolve().parents[3]
HERE=pathlib.Path(__file__).resolve().parent
E=ROOT/'docs/evidence'
P='package-0090-B01-v2-native-static-closure-'
N=E/(P+'r5n');N1=E/(P+'r5n1');N2=E/(P+'r5n2')
A3=E/(P+'r5n2a3');A42=E/(P+'r5n2a4-2');A4D=E/(P+'r5n2a4-1d')
C5C=E/(P+'r5n2a5-3c5c')


def rd(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(ROOT).as_posix()
def put(n,v):(HERE/n).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def canonical(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()


def select(v,ptr):
    for k in ptr.strip('/').split('/') if ptr not in ('','/') else []:
        k=k.replace('~1','/').replace('~0','~');v=v[int(k)] if isinstance(v,list) else v[k]
    return v


SOURCES={}
def source(path,ptr,proposition):
    value=select(rd(path),ptr)
    s={'path':rel(path),'sha256':sha(path),'pointer':ptr,'canonical_fact_sha256':canonical(value),
       'proposition':proposition,'authority_class':'FROZEN_ACCEPTED_STATIC_CONTRACT','direct_or_derived':'DIRECT_SELECTION'}
    SOURCES[(s['path'],ptr)]=s
    return s


def schema_library():
    codec=rd(N/'native-identity-codec.json');abi=rd(N/'native-message-abi.json');registry=rd(N/'native-registry-generation.json')
    schemas={}
    for k,v in codec['schemas'].items():schemas['IDENTITY/'+k]={'fields':v,'source':source(N/'native-identity-codec.json','/schemas/'+k,'Exact typed identity tuple; source/binary identities remain distinct')}
    for k in ['bootstrap_context_schema','dependency_node_schema','dependency_edge_schema','work_revision_schema']:
        schemas[k]={'fields':codec[k],'source':source(N/'native-identity-codec.json','/'+k,'Exact nested tuple/set element schema')}
    for i,f in enumerate(abi['frames']):schemas['FRAME/'+f['id']]={'fields':f['field_order'],'sender':f['sender'],'recipient':f['recipient'],'message_type':f['message_type'],'source':source(N/'native-message-abi.json','/frames/'+str(i),'Exact subject/emitter separation, required field order and message purpose')}
    for i,r in enumerate(registry['records']):schemas['REGISTRY/'+r['type']]={'fields':r['canonical_tuple'],'source':source(N/'native-registry-generation.json','/records/'+str(i),'Exact entity identity/revision/state/receipt fields and monotonicity')}
    for i,c in enumerate(rd(N1/'catalog-projection.json')['sources']):
        schemas['CATALOG/'+c['SOURCE_ID']]={'fields':c['EXACT_PROJECTED_FIELDS'],'natural_key':c['EXACT_JOIN_KEYS'],'source':source(N1/'catalog-projection.json','/sources/'+str(i),'Full declared projection, source scope and missing/duplicate/UNKNOWN semantics')}
    model_types={
        'PrincipalRef':{'representation':'Opaque typed reference to qualified OS birth/UID or to a separately identified SQL role, discriminated by kind; never a generated physical UID','fields':['kind:{OS_SUBJECT,SQL_ROLE,OBSERVER,SOURCE_MEMBRANE}','source_anchor:typed_identity_ref','generation:u64']},
        'PrivateResourceRef':{'representation':'Symbolic custody/use reference, never secret bytes','fields':['class_id:source-class-id','generation:u64','subject_birth:bytes32','holder_birth:bytes32','purpose:source-enum','handle_or_key_ref:opaque-source-identity']},
        'WorkUse':{'fields':['challenge_id:bytes32','work_id:bytes32','input_digest:bytes32','publication_record:REGISTRY/COMPLETED_WORK_PUBLICATION','requested_effect:{READ_ORIGINAL_RECEIPT,NEW_AUTHORITY}']},
        'SnapshotHeader':{'fields':['reader_principal:PrincipalRef','reader_backend_pid:u32','reader_backend_start:i64','MVCC_snapshot_identity:source-typed-ref','native_barrier_revision:u64','boot_id:uuid','time_namespace:u64','captured_boottime:u64','source_generation:u64','source_collection_ids:complete-source-id-map']},
        'MembershipRow':{'source_schema':'CATALOG/pg_catalog.pg_auth_members','all_fields_from_source_schema':True},
        'ACLRow':{'fields':['grantor:oid','grantee:oid(0=PUBLIC)','privilege:exact-source-enum','is_grantable:bool'],'encoding_source':source(N1/'catalog-encoding.json','/ACL','Exploded grantor/grantee/privilege/grant-option; NULL ACL and empty ACL remain distinct')},
        'AuthorityClaim':{'representation':'Design-only relation projection, NOT a new protocol field or grant','fields':['subject:PrincipalRef','source_attestation:REGISTRY/PARTICIPANT_REGISTRY','claimed_target_generation:u64','target_qualification_receipts:set-of-exact-source-input-lineages']},
        'OperationClaim':{'representation':'Design-only authority-query tuple, NOT an arbitrary SQL/native API','fields':['caller:PrincipalRef','operation:fixed-source-operation-or-forbidden-effect-enum','target:source-bound-natural-key','authority_origin:typed-edge-path','phase:{PRE_ENROLLMENT,ACTIVE}']},
    }
    put('schema-library.json',{'schemas':schemas,'design_only_model_types':model_types,
        'encoding':abi['encoding'],'codec_encoding':codec['encoding'],
        'nested_schema_sources':[source(N/'native-message-abi.json','/input_record_schema','No invented native input tags'),source(N/'native-message-abi.json','/result_record_schemas','Exact nested per-role result schemas')],
        'not_new_wire_protocol':True,'no_values_or_secrets_materialized':True})
    return codec,abi,registry


def baseline_models(abi):
    roles=abi['actor_enum'];models={}
    for participant in list(roles)[:7]:
        frames=[f for f in abi['frames'] if f['participant']==participant]
        i=list(roles).index(participant)
        actor_blocks={}
        for actor,enum in roles.items():
            actor_blocks[actor]={'enum':enum,'principal_symbol':'OS('+actor+')','birth_symbol':'BIRTH('+actor+')',
                'current_enrollment_symbol':'ENROL('+actor+',G)','key_or_endpoint_symbol':'ENDPOINT(POSTMASTER,G)' if actor=='POSTMASTER' else 'CREDENTIAL('+actor+',PURPOSE,G)',
                'no_numeric_UID_or_private_key_value':True}
        declaration={
            'model_id':'BASELINE/'+participant+'/V1','kind':'FULLY_DECLARED_PARAMETRIC_STATIC_MODEL_NOT_A_CAPTURED_OBSERVATION',
            'participant_enum':roles[participant],
            'actual_challenge_sender':frames[0]['sender'],'actual_response_sender':frames[1]['sender'],
            'actual_response_recipient':frames[1]['recipient'],'subject':participant,
            'actor_blocks':actor_blocks,
            'required_typed_parameters':{
                'G':{'type':'u64','constraint':'2 <= G <= 2^64-2'},'G_SOURCE':{'type':'u64','definition':'G-1'},
                'context':{'schema':'bootstrap_context_schema','field_binding':'Each declared field is a separately typed immutable parameter; exact shared-field equalities follow the source construction order, not a boolean valid-context flag.'},
                'identity_tuples':{'schemas':'ALL IDENTITY/* in schema-library.json','field_binding':'For each subject/emitter and each declared field: symbol (model_id,actor,schema_id,field_name) with that exact source type; digest references equal the canonical hash of the complete bound tuple.'},
                'frames':{'schemas':['FRAME/'+f['id'] for f in frames],'field_binding':'Every exact field_order entry has a typed symbol. Subject fields bind the participant; sender_* fields bind actual sender, never subject-by-default. input_record/result_record use exact source nested schemas.'},
                'registry':{'schemas':['REGISTRY/PARTICIPANT_REGISTRY','REGISTRY/GENERATION_LEDGER','REGISTRY/GENERATION_TOMBSTONE','REGISTRY/COMPLETED_WORK_PUBLICATION'],
                    'field_binding':'Every declared canonical field has a typed symbol; entity keys, predecessor digests and independent observed journal tip must match their referenced complete tuples.'},
                'principals':{'type':'map actor->PrincipalRef','constraint':'All frozen concurrent MUST_BE_DISTINCT pairs have unequal OS subject/birth references; auxiliary writer/observer/source identities remain separately constrained.'},
                'private_resource':{'type':'PrivateResourceRef','class_binding':source(N1/'credential-custody.json','/credentials/'+str(i),'Exact slot/purpose/generation custody restrictions'),
                    'POSTMASTER_form':'Private endpoint-subject/retained nontransferable-use context from A3; HOST-held expected public endpoint manifest is a separate readonly value, never an Ed25519 POSTMASTER message key.' if participant=='POSTMASTER' else 'Private non-exportable slot/purpose/generation credential reference, never actual secret bytes.'},
                'work':{'type':'WorkUse','binding':'Challenge/work/input/result identities bind their exact canonical publication tuple; fresh and terminal history rows are separate typed values.'},
                'snapshot':{'type':'SnapshotHeader','sources':'ALL CATALOG/* complete row collections with exact projected columns and natural keys; typed OIDs are injectively bound to natural-key identities, never native OS enums.'},
                'source_membrane':{'type':'fixed-operation capability model','binding':source(A42/'forbidden-capability-negative-proof.json','/source_capability','Closed source membrane, not raw SQL/table authority')},
                'source_effect_and_ACL_model':{'binding':source(A42/'effective-acl-ledger.json','','All accepted effective-ACL entries and conditions, not assumed installed PostgreSQL grants')},
                'roles_for_graph_fixture':{'type':'complete typed CATALOG/pg_catalog.pg_roles rows','bindings':'R=the source-authenticated Reader SQL role; A=existing deployment/owner SQL role; M=a distinct non-native symbolic intermediate catalog role. All fields are declared source types. R is not any native participant OS identity.'},
                'graph_fixture_objects':{'type':'complete rows of exact relevant CATALOG schema','bindings':'Object/schema/function/default-ACL IDs are typed symbolic natural-key references, with owner, ACL, body/config/effect manifest and source version independently bound. No object is created or installed.'},
                'policy':{'type':'immutable source-policy parameters','constraint':'Version-bound positive finite max age/deadline/lease, declared count/byte limits, no numeric production TTL invented; captured time and arithmetic constrained to source integer ranges.'},
            },
            'baseline_constraints':[
                'expected and candidate identity tuples are initially equal field-by-field; every digest references its full canonical tuple rather than replacing proof with a file hash',
                'candidate actual emitter identity/enrollment/credential/purpose and kernel birth anchor bind the actual source ABI sender; POSTMASTER type201 is emitted by CENSUS_OBSERVER',
                'current ledger high-water=G; current registry enrollment revision is independently witnessed; retired-generation set contains G_SOURCE and excludes G',
                'current subject enrollment is ENROLLED and operational phase ACTIVE for ordinary current-generation cases; new-qualification/UNKNOWN variants explicitly override only their named state components',
                'Reader source context is its own bound session/process and fixed operation; S03 uses its independent authenticated LOGIN bridge and is not substituted for S01',
                'all exact source collections share one snapshot/backend/barrier identity before mutation; complete typed row multisets preserve duplicates for validation',
                'all7 concurrent subject principals and the required auxiliary custodians remain independently distinct; no equality of SQL roles and OS subjects',
                'R has no ownership, memberships, superuser, CREATEROLE or BYPASSRLS. Invocation is fixed-source INVOKER-only, no caller-provided identifiers, callback, generic SQL or raw descriptor export',
                'M/A are typed test-model catalog principals, not created roles; candidate membership/ACL/call effects have complete source fields and explicit edge kinds, never merged authority booleans',
            ],
            'source_basis':[source(N/'native-message-abi.json','/sender_vs_subject','Actual emitter and subject are independent'),source(N/'native-message-abi.json','/POSTMASTER_transport','No fabricated POSTMASTER signature'),source(N1/'independence-matrix.json','','Concurrent principal and auxiliary separation'),source(N1/'snapshot-consistency.json','','Exact snapshot/session/barrier/currentness rules')],
            'future_binding_rule':'A future static fixture instantiation must supply EVERY typed parameter and verify all source equalities/constraints. Missing/inconsistent parameters => NOT_EVALUABLE, never assumed true. No such binding is instantiated in C5D.',
            'constraint_application':'This is a reusable declaration library. Only the case-selected views and explicit variant state below apply; a T8 or pending-qualification case does not also require the ordinary ACTIVE/ENROLLED target-state assumption.',
            'information_flow':'Raw source config/body values, internal source descriptor and source snapshot rows belong only to the trusted membrane model. Reader receives only approved sanitized projections/digests. No model signature, body hash or public endpoint manifest grants source authority.',
        }
        models[declaration['model_id']]=declaration
    put('baseline-models.json',{'models':models,'completeness_scope':'Specification of all parameter domains and relations, not existence/proof of their future values','no_predicates_evaluated':True})


def change(path,before,after,condition,output='REJECT',extra=None):
    return {'operation':'REPLACE_EXACT_MODEL_COMPONENT','selector':path,'before':before,'after':after,
            'unchanged':'Every other explicitly declared component unless a named dependent digest/encoding must be recomputed by its source canonical rule',
            'violation_predicate':condition,'source_decision':output,'additional_baseline':extra or []}


def family_descriptors():
    d={
      'wrong_binary':change('candidate.subject.binary_module_identity.complete_file_sha256','APPROVED_BINARY_SHA','OTHER_BINARY_SHA:bytes32 != APPROVED_BINARY_SHA','NE(observed.executable_digest,expected.executable_digest)'),
      'wrong_module':change('candidate.subject.selected_module_identity.complete_file_sha256','APPROVED_MODULE_SHA','OTHER_MODULE_SHA:bytes32 != APPROVED_MODULE_SHA','NE(observed.selected_module_digest,expected.selected_module_digest)'),
      'wrong_dependency':change('candidate.subject.dependency_set_identity.dependency_nodes','NODES_EXPECTED','SORT(NODES_EXPECTED UNION {X}) where X:dependency_node_schema, digest(X) notin NODES_EXPECTED; len(NODES_EXPECTED)<4096','NE(candidate.closed_dependency_graph,approved.closed_dependency_graph)'),
      'wrong_loader':change('candidate.subject.loader_identity.complete_loader_file_sha256','LOADER_SHA','OTHER_LOADER_SHA:bytes32 != LOADER_SHA','NE(candidate.loader_identity,expected.loader_identity)'),
      'wrong_parent':change('candidate.subject.parent_identity.kernel_start_ticks','PARENT_START','PARENT_START+1, PARENT_START<2^64-1','NE(candidate.retained_parent_tuple,expected.retained_parent_tuple)'),
      'wrong_process_instance':change('candidate.subject.process_instance_identity.child_kernel_start_ticks','SUBJECT_START','SUBJECT_START+1, SUBJECT_START<2^64-1','NE(candidate.subject_process_tuple,independent_expected_subject_process_tuple)'),
      'wrong_generation':change('candidate.subject.generation','G','G+1 (current independent ledger remains G)','NE(supplied_generation,current_independent_high_water)'),
      'stale_generation':change('candidate.subject.generation','G','G_SOURCE=G-1 (retired, not current)','NE(supplied_generation,current_independent_high_water)'),
      'wrong_enrollment':change('candidate.subject.enrollment_identity','HASH(current_complete_enrollment_tuple)','H_OTHER:bytes32 != HASH(current_complete_enrollment_tuple)','NE(message_subject_enrollment,current_enrollment)'),
      'wrong_credential':change('candidate.subject.credential_identity.credential_certificate_or_endpoint_manifest_digest','TRUSTED_PURPOSE_GENERATION_REF','OTHER_REF:bytes32 != TRUSTED_PURPOSE_GENERATION_REF','NE(candidate.subject_credential_ref,trusted_expected_subject_credential_or_endpoint_ref)'),
      'reused_credential':change('work_use_for_subject_generation','UNUSED authorization for pending WORK_NEW','CONSUMED exact source publication tuple for WORK_OLD; WORK_NEW!=WORK_OLD; request asks NEW_AUTHORITY, not READ_ORIGINAL_RECEIPT','AND(authorization_consumed,request_requires_new_authority)','REJECT_NEW_AUTHORITY_ORIGINAL_TERMINAL_RECEIPT_READ_ONLY',[
          'WORK_OLD and WORK_NEW are separately typed work/challenge/input tuples; terminal old receipt is exact independently witnessed tuple, not a second new authorization']),
      'wrong_channel':change('candidate.subject.authenticated_channel_identity.socket_or_server_endpoint_manifest_digest','EXPECTED_CHANNEL_REF','OTHER_CHANNEL_REF:bytes32 != EXPECTED_CHANNEL_REF','NE(candidate.channel_inventory,current_enrolled_channel_inventory)'),
      'transferred_channel':change('kernel_observation.actual_emitter_birth','BIRTH(actual_response_sender)','BIRTH(Q) != BIRTH(actual_response_sender); socket/channel_ref and claimed sender fields unchanged','NE(actual_kernel_emitter_birth,current_enrolled_emitter_birth)'),
      'replayed_challenge':change('request.sequence','LAST_ACCEPTED_SEQUENCE+1','LAST_ACCEPTED_SEQUENCE; same challenge/work authorization already consumed','OR(sequence<=last_accepted,challenge_work_consumed)'),
      'replayed_response':change('candidate.response.work_id','WORK_NEW','WORK_OLD with terminal consumed result; input/result tuple remains bound to WORK_NEW, WORK_NEW!=WORK_OLD','NE(response.work_input_result_binding,current_requested_work_binding)'),
      'replayed_completed_work_receipt':change('candidate.publication_receipt','current receipt for WORK_NEW/G/current revision','exact terminal receipt for WORK_OLD with another challenge/input; NEW_AUTHORITY requested','NE(receipt.entity_revision_generation_context_work,expected_current_publication_tuple)'),
      'stale_registry_revision':change('candidate.registry_revision.generation_registry_revision','R_CURRENT','R_CURRENT-1, R_CURRENT>=2','NE(supplied_generation_revision,independently_current_generation_revision)'),
      'registry_rollback':change('candidate.journal_tip','independently durable TIP(sequence=S)','previous TIP(sequence=S-1); trusted durable high-water remains S','LT(candidate.journal_sequence,independently_durable_sequence)'),
      'tombstoned_generation':change('candidate.subject.generation','G (not retired)','G_SOURCE in irreversible retired_generation_set','IN(supplied_generation,irreversible_retired_generation_set)'),
      'restart_substitution':change('candidate_new_qualification_subject','old process birth/enrollment','proposed fresh birth B_NEW!=B_OLD claims old enrollment E_OLD while old exact work publication state UNKNOWN','AND(old_work_state=UNKNOWN,attempt_to_adopt_old_enrollment_with_new_birth)','UNKNOWN_FAIL_CLOSED',[
          'This is an attempted/pending qualification, not a compliant completed restart. No process is spawned and no ACTIVE/bootstrap transition is asserted']),
      'reconnect_substitution':change('candidate_new_channel_enrollment','old bound channel C_OLD','proposed new channel C_NEW!=C_OLD attached to old pending work whose exact outcome is UNKNOWN','AND(old_work_state=UNKNOWN,attempt_new_channel_admission)','UNKNOWN_FAIL_CLOSED'),
      'participant_role_substitution':change('candidate.subject.participant_id','enum(P)','enum(Q) != enum(P), where Q is another exact frozen native role; expected slot and message purpose remain P','NE(candidate.participant_role_message_binding,independently_expected_role_binding)'),
      'producer_consumer_substitution':change('observed_role_bundle.APPROVAL_PRODUCER.credential_ref','CREDENTIAL(APPROVAL_PRODUCER,purpose,G)','CREDENTIAL(APPROVAL_CONSUMER,purpose,G); subject P is unchanged; actual role/purpose remains producer','EQ(observed_producer_credential_ref,observed_consumer_credential_ref)',extra=[
          'Complete producer, consumer, enforcer and guard credential-purpose/UID/birth records are present and independently distinct before mutation. This is a credential alias attempt, not a substitution of a numeric enum alone']),
      'observer_writer_substitution':change('candidate_registry_write.authenticated_writer','NATIVE_REGISTRY_WRITER own enrolled actor/credential/birth','HEALTH_GUARD observer actor/credential/birth while operation is still registry-write and independent observer receipt stays separate','NE(actual_registry_writer_actor,expected_NativeRegistryWriter)'),
      'credential_theft':change('observed_private_resource.holder_birth','authorized private subject/custodian birth','BIRTH(Q) of an unauthorized distinct actor at ACTIVE; private resource identity/purpose/generation unchanged','NE(actual_private_resource_holder,authorized_holder)',extra=[
          'For POSTMASTER the target is its private endpoint-subject/nontransferable-use context. Its public expected endpoint manifest is not stolen secret material and no POSTMASTER message key is invented']),
      'credential_transfer':change('candidate.private_resource_use','authorized holder uses own exact private resource','Q presents P-bound private use capability in ACTIVE, outside protected pre-enrollment delivery; same resource provenance retained','AND(phase=ACTIVE,NE(presenter,authorized_holder),NOT(explicit_bootstrap_delivery))'),
      'credential_inheritance':change('candidate.target_authority_claim','target authority not established merely from source attestation','AuthorityClaim(source_attestation.generation=G_SOURCE,claimed_target_generation=G,target_qualification_receipts=EMPTY); source grant not rebound; target private material/endpoint remains independently fresh where required','AND(NE(source_attestation.generation,claimed_target_generation),target_qualification_receipts=EMPTY)'),
      'wrong_custodian':change('observed_private_resource.custodian_birth','exact authorized custodian from source class','BIRTH(Q) != authorized_custodian; public expected endpoint manifest holder is unchanged','NE(observed_private_custodian,source_required_private_custodian)'),
      'wrong_reader':change('source_operation.S01.authenticated_caller_principal','R5N1_READ_PROXY_LOGICAL_PRINCIPAL and owned bound session','different PrincipalRef Q, outside S03 existing LOGIN bridge; operation remains S01','NE(actual_source_caller,enrolled_reader_source_caller)'),
      'catalog_row_omission':change('observed_snapshot.pg_catalog.pg_roles row multiset','complete declared roster including exact Reader natural key r','DELETE_ONE_EXACT_ROW(r); retain complete capture/other-source identities; no query failure is fabricated','MISSING(expected_reader_identity_row)','UNKNOWN'),
      'catalog_row_injection':change('observed_snapshot.pg_catalog.pg_roles row multiset','complete declared exact roster R','INSERT full typed pg_roles row X with fresh nonalias OID/name outside protected expected roster; rolsuper=FALSE,rolcreaterole=FALSE,other fields explicitly schema-bound','NOT(BIJECTION(observed_protected_role_roster,expected_role_roster))'),
      'catalog_duplication':change('observed_snapshot.pg_catalog.pg_roles row multiset','one row with natural key r','APPEND exact duplicate row r at a second position; do not deduplicate before validation','EXISTS_DUPLICATE_NATURAL_KEY(observed_rows)'),
      'catalog_stale_snapshot':change('snapshot.captured_boottime','T_NOW-MAX_AGE within immutable approved bound','T_NOW-MAX_AGE-1 with T_NOW>MAX_AGE+1; same boot/timens, no clock-domain mixing','GT(T_NOW-captured_boottime,MAX_AGE)','UNKNOWN'),
      'mixed_snapshot':change('snapshot.source_collection[pg_catalog.pg_auth_members].snapshot_identity','SID_A shared by every declared collection','SID_B != SID_A while pg_roles and other sources remain SID_A','NOT(ALL_EQ(source_collection_snapshot_identities))','UNKNOWN'),
      'wrong_role':change('source_reader.pg_stat_activity.(usesysid,usename)','exact Reader SQL(role_oid,rolname)','different existing SQL role (oid_Q,name_Q) with proper types; native subject OS identity is unchanged','NOT(IS_EXPECTED_ROLE(actual_authenticated_SQL_role,expected_Reader_role))'),
      'transitive_SET_ROLE':change('catalog_membership_rows','R has no memberships; M/A typed distinct SQL roles','INSERT two full pg_auth_members rows R->M and M->A, set_option=TRUE,inherit_option=FALSE,admin_option=FALSE, grantor explicit','REACHABLE(SET,R,A)'),
      'transitive_INHERIT':change('catalog_membership_rows','R has no memberships; M/A typed distinct SQL roles','INSERT two full pg_auth_members rows R->M and M->A, inherit_option=TRUE,set_option=FALSE,admin_option=FALSE,grantor explicit; rolinherit alone is not used','REACHABLE(INHERIT,R,A)'),
      'ADMIN_option_escalation':change('catalog_membership_rows','no R->A membership/admin path','INSERT one full pg_auth_members R->A row admin_option=TRUE,inherit_option=FALSE,set_option=FALSE,explicit grantor; R!=A','HAS_ADMIN_OPTION(R,A)'),
      'ownership_escalation':change('catalog.pg_class[pg_catalog.pg_roles].relowner','independently expected deployment owner O != R','R.oid; all other relation identity fields retained','IS_OBJECT_OWNER(R,protected_catalog_relation)'),
      'PUBLIC_path':change('catalog.pg_auth_members observed relacl','baseline exploded ACL preserves owner rights and public origins separately','INSERT exact ACLRow(grantor=O,grantee=0,privilege=UPDATE,is_grantable=FALSE); claim raw UPDATE authority through PUBLIC for Reader R','HAS_PUBLIC_PRIVILEGE(R,target,UPDATE) AND NOT FIXED_SOURCE_OPERATION_ALLOWS(UPDATE)'),
      'default_privilege_path':change('future_creation_authority_claim','no future default-derived raw Reader source authority','Claim = exact GLOBAL/SCHEMA_DEFAULT constructor (actual_creator=O,schema=N,kind=FUNCTION,grantee=R,privilege=EXECUTE,grant_option=FALSE) on prospective function F_NEW outside fixed source allowlist; do not apply it to an existing object ACL','EXISTS_EFFECTIVE_CREATOR_DEFAULT(O,N,FUNCTION,R,EXECUTE) AND NOT FIXED_SOURCE_ALLOWS(F_NEW)',extra=[
          'Complete creator/schema/object-kind/grantee/default ACL rows and future object creation tuple are bound; existing current-object ACL remains untouched. This tests an attempted source-authority claim from a future default, not an assertion of current active grant']),
      'SECURITY_DEFINER_path':change('source_callable.definition.prosecdef','FALSE / INVOKER, exact caller EXECUTE and schema USAGE, complete verified owner/body/effect context','TRUE / DEFINER with same callable identity, owner and source-bound effect manifest','HAS_SECURITY_DEFINER_PATH(callable) AND source_capability.execution_semantics=INVOKER_ONLY'),
      'search_path_substitution':change('source_capability.resolution_expression','EXACT_FROZEN_IDENTITY(pg_catalog.pg_roles)','CALLER_CONTROLLED_LOOKUP(unqualified_name,caller_namespace_or_callback); actual resolution identity is now replaceable','NOT(EXACT_FROZEN_RESOLUTION_IDENTITY(resolution_expression))',extra=[
          'Changing an ignored ambient search_path is not the mutation. This substitutes actual trusted-resolution behavior; no invalid extra native TLV is added']),
      'CREATEROLE_path':change('catalog.pg_roles[R].rolcreaterole','FALSE','TRUE; other typed role fields unchanged','HAS_CREATEROLE(R)'),
      'superuser_path':change('catalog.pg_roles[R].rolsuper','FALSE','TRUE; other typed role fields unchanged','IS_SUPERUSER(R)'),
      'bootstrap_path':change('operational_authority_claim','fixed read-only source operation by R in ACTIVE','OperationClaim(caller=R,operation=PRE_ENROLLMENT_PROVISION,target=P,authority_origin=HOST_ROOT,phase=ACTIVE)','EXISTS_CALLABLE_EDGE_TO(HOST_ROOT) AND phase=ACTIVE AND caller!=authorized_pre_enrollment_provisioner'),
      'reader_mutation':change('bound_source_effect_manifest[fixed source operation]','exact READ-only projection effect tree','same source operation claims WRITE_RESOURCE(pg_catalog.pg_auth_members); expected authenticated effect manifest remains READ-only','HAS_UNEXPECTED_WRITE_PATH(R,WRITE_RESOURCE)'),
      'reader_privilege_escalation':change('catalog.pg_roles[R].rolbypassrls','FALSE','TRUE; no native participant SQL role is introduced','HAS_BYPASSRLS(R)'),
      'snapshot_reconnect':change('incoming_collection.reader_backend_identity','(PID_A,START_A) of old independently bound pending snapshot','(PID_B,START_B)!=(PID_A,START_A), while old pending snapshot/session identity remains A','NE(incoming_backend_identity,pending_snapshot_backend_identity)','UNKNOWN'),
      'snapshot_restart':change('incoming_collection.native_observation_subject_generation','old pending (BIRTH_A,G_SOURCE,barrier_A)','new (BIRTH_B,G,barrier_B), old pending observation/tip retained and not reconciled','NE(incoming_native_lineage,pending_snapshot_native_lineage)','UNKNOWN'),
    }
    assert len(d)==50
    # Complete source formula bindings are recorded, not implemented/evaluated here.
    for name,s in d.items():
        s['family']=name;s['new_C5D_design_not_historical_fixture']=True
        s['before_after_relation_is_symbolic_specification_only']=True
    put('family-descriptors.json',{'families':d,'count':50,'model_operator_semantics':{
        'EQ_NE_LT_GT_IN':'Ordinary exact typed equality/inequality/order/set membership, no fuzzy comparison or implicit coercion',
        'MISSING':'Expected required identity absent from complete or partial input => source UNKNOWN; never infer a false/zero identity',
        'REACHABLE':'Separate edge-type least fixed point using catalog-security-predicates.role_edge_rules; SET/INHERIT/ADMIN/OWNER/PUBLIC/default/SD never merged',
        'source_predicates':'Exact expressions in authority-chain source catalog-security-predicates and independently closed source_capability; not invented opaque pass flags',
        'new_op_claims':'Logical authority queries in a static model, not exposed runtime APIs or arbitrary SQL builders',
        'recompute_derived_digests':'Apply exact frozen canonical encoding/digest definition to changed model tuple when later instantiated; no forged runtime observation is asserted'},
        'no_mutation_applied_to_fixture':True})
    return d


def family_sources(family,pindex):
    base=[source(N/'native-identity-codec.json','','Exact typed identity/nested schemas and encoding'),source(N/'native-message-abi.json','','Exact actual emitter, subject, context, framing and one-use purpose'),source(N/'native-registry-generation.json','','Enrollment/currentness/publication/UNKNOWN and retired-generation rules')]
    if family in ['credential_theft','credential_transfer','credential_inheritance','wrong_custodian','wrong_credential','reused_credential']:
        base += [source(N1/'credential-custody.json','/credentials/'+str(pindex),'Exact per-slot private custody/nontransferability/currentness/replay rules'),source(A3/'credential-class-manifest.json','/classes','Endpoint versus native private credentials; explicit protected bootstrap exception')]
    if family=='credential_inheritance':base.append(source(C5C/'prospective-authority-record.json','','Prospective POSTMASTER T8 rule; other slots use their independent existing generation/no-adoption rules, not an extended T8 designation'))
    if family in ['producer_consumer_substitution','observer_writer_substitution','transferred_channel']:
        base.append(source(N1/'independence-matrix.json','','Exact credential/UID/birth/writer/observer/role separation; a mutation is still required and is explicitly specified'))
    if family.startswith('catalog_') or family in ['mixed_snapshot','snapshot_reconnect','snapshot_restart','wrong_reader','wrong_role']:
        base += [source(N1/'catalog-projection.json','','Full source field/natural-key/duplicate/missing semantics'),source(N1/'snapshot-consistency.json','','Exact snapshot session/barrier/time/lineage applicability')]
    if family not in OLD_FAMILIES or family=='producer_consumer_substitution':
        base += [source(N1/'catalog-security-predicates.json','','Exact typed three-valued predicates and separate authority edge rules'),source(A42/'forbidden-capability-negative-proof.json','/source_capability','Independently closed fixed source capability, no generic/raw/mutation/role/SD/ambient lookup authority'),source(A42/'forbidden-capability-negative-proof.json','/principal_decisions','Closed Reader principal choices, invoker-only and S03-specific exception'),source(A42/'effective-acl-ledger.json','','Closed effective ACL contracts, not raw source data promoted to active grants')]
    return base


OLD_FAMILIES=set()
def case_baseline(participant,family,spec):
    view='CURRENT_SUBJECT_IDENTITY'
    if family in ['reused_credential','replayed_challenge','replayed_response','replayed_completed_work_receipt']:view='CURRENT_WORK_ONE_USE'
    if family in ['credential_theft','credential_transfer','wrong_custodian']:view='PRIVATE_RESOURCE_CUSTODY'
    if family=='credential_inheritance':view='GENERATION_AUTHORITY_CLAIM'
    if family in ['restart_substitution','reconnect_substitution']:view='PENDING_NEW_QUALIFICATION'
    if family.startswith('catalog_') or family in ['mixed_snapshot','snapshot_reconnect','snapshot_restart']:view='SNAPSHOT_APPLICABILITY'
    if family not in OLD_FAMILIES and view=='CURRENT_SUBJECT_IDENTITY':view='CLOSED_READER_AUTHORITY_MODEL'
    variants={
        'CURRENT_SUBJECT_IDENTITY':{'trusted_generation':'G','trusted_enrollment':'ENROLLED current exact entity','phase':'ACTIVE','candidate':'Initial exact typed identity equals trusted expected counterpart; only descriptor selector is replaced.'},
        'CURRENT_WORK_ONE_USE':{'trusted_generation':'G','trusted_enrollment':'ENROLLED','phase':'ACTIVE','work_binding':'Current request, terminal history and consumption state are separate complete publication tuples. WORK_OLD!=WORK_NEW; read-only duplicate and new-authority requests are discriminated.'},
        'PRIVATE_RESOURCE_CUSTODY':{'trusted_generation':'G','phase':'ACTIVE','private_holder_before':'BIRTH('+participant+')','private_custodian_before':'BIRTH('+participant+')',
            'private_class':'POSTMASTER_SERVER_ENDPOINT' if participant=='POSTMASTER' else 'GENERATION_TRANSPORT',
            'private_facet':'For POSTMASTER this is endpoint subject private/nontransferable use context, not the public expected manifest. For other actors, private signing-key use/custody context.',
            'public_endpoint_manifest_holder':'HOST_PLATFORM; remains independent and unchanged; copying this public value alone is not theft',
            'Q':'One other independently enrolled actor with birth/UID distinct from the permitted private holder, exact same typed roster, not a new invented principal'},
        'GENERATION_AUTHORITY_CLAIM':{'source_generation':'G_SOURCE=G-1','source_ledger_state':'TOMBSTONED; source attestation is historical provenance, never a live restored grant',
            'target_generation':'G','target_ledger_state':'NEW_GENERATION after checked succession','target_enrollment':'PROVISIONAL, not qualified','target_qualification_receipts':'EMPTY as an explicit model fact, not a query failure',
            'private_material':'Target required material/endpoint is a separate fresh symbolic instance where independently required; the attack copies an authority attestation, not private key bytes.',
            'evaluation_domain':'Logical authority-claim check using complete historical/current ledger records. No claim that a native target RESPONSE frame already exists or is qualified at this cut; ABI schemas are declaration references only here.'},
        'PENDING_NEW_QUALIFICATION':{'current_generation':'G','old_subject_enrollment':'Existing exact E_OLD in G; work outcome UNKNOWN, no completed fresh enrollment is asserted',
            'pending_work':'Complete typed old publication state UNKNOWN, no independent outcome reconciliation receipt',
            'candidate_new_subject_or_channel':'Proposed B_NEW/C_NEW, not an actual spawned/qualified replacement; claims E_OLD. Trusted old state is not rewritten.',
            'target_generation':'Only a proposed next generation if restart; reconnect remains in the old pending context. No new eligible ledger high-water or ACTIVE subject is created.'},
        'SNAPSHOT_APPLICABILITY':{'reader':'S01/S02/S04/S05 exact fixed Reader R session and owned backend; no substitution by S03 LOGIN bridge',
            'source_rows':'All19 declared source collections are fully typed symbolic multisets, one natural-key occurrence before mutation, exact source count/order/bounds/field and null semantics',
            'coherence':'One SID_A/backend_A/native barrier_A/current generation before mutation; original pending attempt retained for reconnect/restart. Known stale or inconsistent applicability remains UNKNOWN.',
            'role_omission_anchor':'Exact source pg_roles natural key for expected Reader SQL role R; no invented SQL role for native subject P',
            'injection_row':'Every pg_roles field explicitly bound by its declared type; fresh OID/name distinct from every expected protected role; non-superuser/non-CREATEROLE/no-BYPASSRLS.'},
        'CLOSED_READER_AUTHORITY_MODEL':{'reader':'R5N1_READ_PROXY_LOGICAL_PRINCIPAL plus its independently bound SQL role/session, not the native subject',
            'fixed_source_operation':'S01 for caller/session substitutions; other graph cases name the source capability/effect rather than adding native TLVs or SQL text',
            'role_rows':'R,A,M complete pg_roles typed rows, pairwise distinct OID/name. R superuser/CREATEROLE/BYPASSRLS FALSE; zero memberships and ownership before mutation. A is a separate deployment/owner model role; M is intermediate catalog role, not a new native actor.',
            'row_constructor':'Any inserted membership row binds ALL pg_auth_members projected fields (oid,roleid,member,grantor,admin_option,inherit_option,set_option); fresh row OID and explicit grantor; option dimensions independent.',
            'object_constructor':'Exact source pg_class/pg_namespace/pg_proc/default_acl and exploded ACL field schemas bind full object identity, owner, schema usage, grants and verified body/effect inputs wherever the selected predicate requires them.',
            'default_constructor':'Future object creation tuple includes actual creator, namespace, object kind, grantee and privilege; current-object ACL never rewritten by a default. The forbidden claim is to obtain a source callable outside the exact fixed allowlist.',
            'source_effects':'Closed A4.2 source capability/ACL model only; observed source/ACL data cannot mint active Reader authority. Negative paths are authority-claim attempts, not grants or successful SQL executions.'},
    }
    return {'stable_id':'BASELINE/'+participant+'/'+family+'/V1','library_model_id':'BASELINE/'+participant+'/V1','library':'baseline-models.json',
            'selected_view':view,'exact_variant_state':variants[view],
            'tuple_binding_rule':'For each selected view, every relevant source-schema field has a typed named symbol and every referenced hash equals its complete tuple canonical hash. Nonselected declarations are not secretly assumed TRUE.',
            'family_variant_constraints':spec['additional_baseline'],'complete_parameter_schema':True,'instantiated_values_present':False}


def registry(families,abi):
    global OLD_FAMILIES
    n1=rd(N1/'substitution-matrix.json');cases=rd(N2/'substitution-witnesses.json')['cases']
    old={r['id']:(i,r) for i,r in enumerate(n1['preserved_cases'])};new={r['id']:(i,r) for i,r in enumerate(n1['new_cases'])}
    OLD_FAMILIES={r['attack'] for r in n1['preserved_cases']}
    assert len(old)==168 and len(new)==182 and len(cases)==350 and set(old)|set(new)=={c['ATTACK_ID'] for c in cases}
    rows=[];binding=[];reconstruction=[]
    for i,c in enumerate(cases):
        ident=c['ATTACK_ID'];participant,family=ident.split('/',1);pindex=list(abi['actor_enum']).index(participant)
        origin,indexed=(('preserved_cases',old[ident]) if ident in old else ('new_cases',new[ident]))
        n1index,r=indexed;structured=c['STATIC_WITNESS_COMPLETE'];spec=families[family]
        expected=r.get('expected',r.get('required_outcome'))
        src=[source(N2/'substitution-witnesses.json','/cases/'+str(i),'Stable original case payload; structured completeness flag is not witness proof'),source(N1/'substitution-matrix.json','/'+origin+'/'+str(n1index),'Original exact per-case predicate/outcome; preserved cases override N2 generic REJECT wording')]
        src += family_sources(family,pindex)
        complete=family!='catalog_row_omission'
        gap=[] if complete else [
            {'kind':'CASE_DECISION_AUTHORITY','source_case_required_outcome':expected,'source_missing_identity_decision':'UNKNOWN',
             'exact_gap':'For the bounded expected-reader-row omission, catalog-projection explicitly prescribes UNKNOWN; the generic canonical case line says REJECT. No case-specific authority says whether REJECT is a broad deny label, a strict result enum, or a different omission variant. Do not silently equate the two or rewrite history.',
             'affected_dimension':'Exact canonical decision/expected-output mapping, not context/internal-universe architecture.'}]
        sources={k:src for k in ['AUTHORITY_FOR_BASELINE','AUTHORITY_FOR_MUTATION','AUTHORITY_FOR_DECISION']}
        pred={
            'input_model':'BASELINE/'+participant+'/V1 after the exact family descriptor substitution',
            'native_violation_expression':spec['violation_predicate'],'source_native_decision':spec['source_decision'],
            'canonical_case_required_outcome_preserved':expected,
            'original_case_predicate_text':r.get('exact_predicate',r.get('predicate')),
            'PASS':'Only after future evaluation: all typed fixture parameters and source constraints are bound; exact intended violation is demonstrated; calculated native authority decision satisfies the source-specific required outcome and no new authority/work/publication is granted.',
            'FAIL':'Only after future evaluation with complete inputs: the witness proposition is false or new unauthorized authority/work/publication is granted, or the calculated decision disagrees with the exact resolved canonical expected decision.',
            'UNKNOWN_NOT_EVALUABLE':'Any missing/unbound required parameter, invalid source/binding, unresolved canonical outcome mapping or incomplete specification => NOT_EVALUABLE. Never infer PASS from a known expected string.',
            'terminal_duplicate_rule':'Returning only the identical original terminal receipt without new work is not a new authority acceptance. Work/challenge-mismatch variants still deny the new claim; no general replay permission is created.',
            'no_predicate_executed':True,'decision_spec_complete':complete,
        }
        if family in ['restart_substitution','reconnect_substitution']:
            pred['source_priority']='Preserve original N1 UNKNOWN_FAIL_CLOSED pending/reconciliation contract; do not replace it with N2 generic unequal→REJECT. Proposed fresh subject/channel is not claimed to be a successfully qualified restart.'
        if family=='reused_credential':pred['source_priority']='REJECT concerns NEW_AUTHORITY; an exact original terminal readonly receipt is a separate permitted response and cannot prove new work.'
        record={
            'WITNESS_ID':ident,'SOURCE_PROVENANCE':src,
            'SOURCE_GENERATION':{'symbol':'G_SOURCE' if family in ['credential_inheritance','snapshot_restart'] else 'G','meaning':'Authority provenance only; no live retired grant restored'},
            'TARGET_GENERATION':{'symbol':'G+1 (CLAIM_ONLY)' if family in ['wrong_generation','restart_substitution'] else 'G_SOURCE (STALE_CLAIM_ONLY)' if family in ['stale_generation','tombstoned_generation'] else 'G','meaning':'Actual/proposed context is distinguished in the exact baseline variant. A changed claimed field never updates trusted high-water. Not every case performs T8.'},
            'PARTICIPANT_CONTEXT':{'subject':participant,'enum':abi['actor_enum'][participant],'baseline_id':'BASELINE/'+participant+'/V1','actor_binding':'Exact source frame sender/recipient, not implicit subject=emitter'},
            'PRINCIPAL_CONTEXT':{'native_OS_subject':'OS('+participant+')','actual_response_sender':next(f['sender'] for f in abi['frames'] if f['id']==participant+'/RESPONSE'),
                'Reader_graph_principal':'R5N1_READ_PROXY_LOGICAL_PRINCIPAL; distinct SQL/native identities; S03 bridge exception retained','I13':'Full concurrent seven-slot/21-pair plus auxiliary separation preserved'},
            'CREDENTIAL_CONTEXT':{'class_source':source(N1/'credential-custody.json','/credentials/'+str(pindex),'Exact credential/endpoint class for this slot'),
                'material_vs_authority':'Distinct typed components. No automatic rotation, substitution necessity/sufficiency or public-manifest secrecy inferred. Existing scoped renewal requirements remain.',
                'POSTMASTER_special':'No fabricated POSTMASTER signing key; CENSUS response signer and HOST public expected endpoint reference remain separate from the private endpoint-subject capability.'},
            'BASELINE_STATE':case_baseline(participant,family,spec),
            'MUTATION':{'descriptor_id':'FAMILY/'+family,'definition':spec,'model_only_no_fixture_materialized':True},
            'EXPECTED_DECISION_PREDICATE':pred,**sources,
            'STATIC_EVALUABILITY':'SPECIFICATION_READY_REQUIRES_TYPED_FIXTURE_BINDING_AND_LATER_STATIC_EVALUATION' if complete else 'NOT_EVALUABLE_UNRESOLVED_CANONICAL_OUTCOME_MAPPING',
            'MISSING_AUTHORITY':gap,
            'MISSING_ARTIFACT':(['Case-specific decision authority resolution for the row-omission variant'] if not complete else [])+[
                'Future concrete or mechanically bound symbolic STATIC fixture instance for every declared typed parameter; no live production values are required to define this model',
                'Later calculated predicate result and complete witness proof trace; C5D performs neither'],
            'STATUS':'SPEC_COMPLETE_NOT_EVALUATED' if complete else 'SPEC_INCOMPLETE',
            'INPUT_STRUCTURED_CANDIDATE':structured,
            'BASELINE_COMPLETE':True,'MUTATION_COMPLETE':True,'DECISION_PREDICATE_COMPLETE':complete,'AUTHORITY_CHAIN_COMPLETE':complete,
            'ARCHITECTURAL_DEPENDENCY':None,'EVALUATED':False,'PROVEN':False,
            'mapping_nature':'NEW_C5D_BOUNDED_SYMBOLIC_SPECIFICATION_DERIVED_FROM_FROZEN_RULE_NOT_RECOVERED_HISTORICAL_FIXTURE',
            'T8_compatibility':'POSTMASTER/credential_inheritance uses prospective no-unqualified-source-authority-adoption rule. Other slots use independently existing currentness/custody rules. No designation extension or automatic material/principal change.',
        }
        rows.append(record)
        if structured:
            binding.append({'canonical_id':ident,'source_index':i,'binding':'UNIQUE_EXACT_ID_AND_PARTICIPANT','structured_source':src[0],'original_predicate_source':src[1],
                'baseline_verified':'Exact typed parameter model declared, not a runtime capture','mutation_verified':'Case-specific family descriptor; special consumed-work, role-bundle and UNKNOWN-pending semantics retained',
                'predicate_verified':pred,'T8_compatible':True,'I13_preserved':True,'not_a_relation_count_disguised_as_witness':True,'spec_status':record['STATUS']})
        else:
            reconstruction.append({'canonical_id':ident,'source_index':i,'family':family,'source_provenance':src,
                'baseline_id':record['BASELINE_STATE']['stable_id'],'exact_mutation':spec,'predicate':pred,
                'specific_mapping_complete':complete,'remaining_gap':gap,'scope':'Symbolic static design, not observed or evaluated case'})
    assert len(binding)==133 and len(reconstruction)==217
    put('canonical-350-registry.json',{'case_records':rows,'total':350,'identity_policy':'Original ATTACK_ID retained byte-for-byte; no merge, deletion, duplicate or replacement by pair counts','symbolic_design_not_proof':True})
    put('structured-133-binding.json',{'total':133,'bound_uniquely':133,'ambiguous':0,'rejected':0,'records':binding,'identity_binding_is_not_full_witness_proof':True})
    put('unmapped-217-reconstruction.json',{'input_total':217,'mapped_this_gate':sum(x['specific_mapping_complete'] for x in reconstruction),'still_unmapped':sum(not x['specific_mapping_complete'] for x in reconstruction),'records':reconstruction})
    for name,keys in [
        ('baseline-matrix.json',['BASELINE_STATE','BASELINE_COMPLETE','PARTICIPANT_CONTEXT','SOURCE_GENERATION','TARGET_GENERATION']),
        ('mutation-matrix.json',['MUTATION','MUTATION_COMPLETE']),
        ('decision-predicate-matrix.json',['EXPECTED_DECISION_PREDICATE','DECISION_PREDICATE_COMPLETE','MISSING_AUTHORITY']),
        ('authority-chain-matrix.json',['AUTHORITY_FOR_BASELINE','AUTHORITY_FOR_MUTATION','AUTHORITY_FOR_DECISION','AUTHORITY_CHAIN_COMPLETE','MISSING_AUTHORITY']),
    ]:put(name,{'rows':[{'WITNESS_ID':r['WITNESS_ID'],**{k:r[k] for k in keys}} for r in rows],'total':350})
    return rows


def artifacts(rows):
    put('artifact-specification.json',{
        'case_packages':[{'WITNESS_ID':r['WITNESS_ID'],'fixture_identity':'FIXTURE/C5D/'+r['WITNESS_ID']+'/V1','baseline_schema_ref':r['BASELINE_STATE'],
            'mutation_descriptor_ref':r['MUTATION']['descriptor_id'],'expected_predicate_ref':{'file':'canonical-350-registry.json','case':r['WITNESS_ID'],'field':'EXPECTED_DECISION_PREDICATE'},
            'required_inputs':'All exact typed bindings/relations in the referenced baseline model and source schemas, plus named family variant constraints; no substituted all-valid boolean',
            'output_schema':{'WITNESS_ID':'exact canonical string','spec_version':'C5D/V1','source_hashes':'complete reference/hash list','fixture_binding_digest':'bytes32','mutation_descriptor_digest':'bytes32','calculated_native_decision':'source decision enum, not prefilled','proof_classification':'STATICALLY_PROVEN/STATICALLY_DISPROVEN/UNKNOWN_NOT_EVALUABLE','evaluation_trace':'complete typed predicate/input provenance'},
            'integrity_plan':'Hash canonical schema and descriptor bytes separately. Later bind expected source manifest and input values before calculation. Do not treat a descriptor hash as proof or actual executable/binary identity.',
            'future_proof_needed':r['MISSING_ARTIFACT'],'current_status':r['STATUS'],'no_fixture_run_or_instantiated':True} for r in rows],
        'operators_are_specifications_not_implementations':True,'no_executable_adapter_SQL_or_native_fixture_generated':True})


def summary(rows):
    statuses=collections.Counter(r['STATUS'] for r in rows)
    counts={'CANONICAL_CASES_TOTAL':350,'CASE_RECORDS_TOTAL':len(rows),'STRUCTURED_CANDIDATES_TOTAL':133,'STRUCTURED_BOUND_UNIQUELY':133,'STRUCTURED_AMBIGUOUS':0,'STRUCTURED_REJECTED':0,'UNMAPPED_INPUT_TOTAL':217,
        'MAPPED_THIS_GATE':sum(r['DECISION_PREDICATE_COMPLETE'] for r in rows if not r['INPUT_STRUCTURED_CANDIDATE']),
        'STILL_UNMAPPED':7,
        **{k:statuses[k] for k in ['STATICALLY_PROVEN','STATICALLY_DISPROVEN','SPEC_COMPLETE_NOT_EVALUATED','SPEC_INCOMPLETE','CONTRADICTED']},
        **{stem+'_'+suffix:sum(r[stem+'_COMPLETE']==value for r in rows) for stem in ['BASELINE','MUTATION','DECISION_PREDICATE','AUTHORITY_CHAIN'] for suffix,value in [('COMPLETE',True),('INCOMPLETE',False)]},
        'SUBSTITUTION_WITNESSES_REQUIRED':350,'SUBSTITUTION_WITNESSES_PROVEN':0,'SUBSTITUTION_WITNESSES_UNKNOWN':350,
        'ATTACKS_MATERIALIZED_THIS_GATE':0,'ATTACKS_EVALUATED_THIS_GATE':0,'DENOMINATOR_CHANGED':'NO'}
    assert sum(counts[k] for k in ['STATICALLY_PROVEN','STATICALLY_DISPROVEN','SPEC_COMPLETE_NOT_EVALUATED','SPEC_INCOMPLETE','CONTRADICTED'])==350
    assert counts['MAPPED_THIS_GATE']==210
    put('coverage-accounting.json',counts)
    missing=[r['WITNESS_ID'] for r in rows if r['STATUS']=='SPEC_INCOMPLETE']
    put('bounded-gaps.json',{'affected_ids':missing,'gap':'Resolve source-native UNKNOWN for missing expected catalog identity versus generic canonical REJECT label, or authorize another precisely defined omission variant. No widening of scope, no rewrite of the old result and no automatic REJECT=UNKNOWN normalization.',
        'source_missing_row_rule':source(N1/'catalog-projection.json','/sources/0/MISSING_ROW_SEMANTICS','Expected identity/source row missing => UNKNOWN; explicit source semantics'),
        'architectural_dependency_proven':False,'registry_identity_contradiction':False,
        'reason_not_classified_CONTRADICTED':'The original generic family does not specify which exact omission variant or result-normalization layer it means. This new bounded variant reveals a missing canonical decision mapping, not proof the 350 stable identities are incoherent.'})
    put('authority-provenance.json',{'source_selections':list(SOURCES.values()),'new_witness_design_authority':{'path':rel(HERE/'project-authority-input.txt'),'sha256':sha(HERE/'project-authority-input.txt'),'section':'§§3,8–13: explicit symbolic static fixture/mutation/predicate specification authority'},'authority_limit':'C5D may instantiate bounded rule-derived TEST model specifications, not change normative rules, accept a runtime grant or claim a prior historical fixture existed.','source_membrane_is_closed_A42_not_old_partial_graph':True})
    put('primary-result.json',{'SELECTED_OUTCOME':'B','status':'BOUNDED_SPECIFICATION_INCOMPLETE','case_records':350,'spec_complete_not_evaluated':counts['SPEC_COMPLETE_NOT_EVALUATED'],'spec_incomplete':counts['SPEC_INCOMPLETE'],'exact_gaps':missing,
        'why_not_A':'Seven omission variants lack an exact canonical decision mapping; do not manufacture completion.',
        'why_not_C':'All350 original IDs support one coherent registry. No merge/duplicate or impossible identity was found; local decision ambiguity is preserved.',
        'why_not_D':'No separate frozen context/scope/atomic/universe decision is proved necessary to resolve the seven result-mapping gaps.',
        'N1_SUBSTITUTION_STATIC_WITNESSES':'OPEN','N1_DECISIONS_CLOSED':11,'N1_DECISIONS_OPEN':1,'V2_NATIVE_STATIC_DESIGN_PROOF':'FAIL','V2_NATIVE_STATUS':'BLOCKED','NEXT_EXECUTED':False,'NEXT_GATE':'BOUNDED_STATIC_WITNESS_GAP_CLOSURE'})


def report():
    text='''# Package0090 C5D — bounded static witness authority and artifact specification

Primary outcome B: BOUNDED_SPECIFICATION_INCOMPLETE. Exactly350 stable canonical case records exist.343 are proposed complete symbolic specifications, not evaluated witnesses; seven catalog-row-omission variants retain an unresolved canonical decision mapping. Zero witnesses are proved, disproved or executed. N1 remains11/12 and V2 BLOCKED.

## Preflight and boundaries

Branch checkpoint/package-0090-cloud-handoff, documentary HEAD451265ff5b3d286eb4d27c4b3817c2f558f30123; frozen implementation baselinecbc284f62d9bd09b7169b55c8d66a3c51a68c6cb remains ancestor. Exactly73 prior authorized paths are reconciled:7 C5A STOP,24 C5A resumption,24 C5B,18 C5C. Four manifests and all9,172 preexisting file hashes are preserved. V043 unchanged; parallel post-MVP bytes are hash-only inputs with no decision authority. No old file is repaired or normalized.

This gate authors new bounded STATIC TEST model specifications from accepted rules. It does not claim that the exact fixtures existed historically, does not instantiate any model values, and does not evaluate the specified attack predicates. Builder execution validates JSON structure, identity uniqueness, counts and source hashes only. These operations are not attack materialization/evaluation or native runtime execution.

## Registry and typed fixture specification

Original350 ATTACK_ID strings and order are retained byte-for-byte: no duplicate, merge, deletion or denominator substitution. Every case independently contains provenance, source/proposed target generation, participant/principal/credential context, stable baseline reference, exact before/after descriptor, decision/authority mapping, future evaluability, missing elements and proof classification.

The schema library embeds the exact source identity, frame, registry and catalog field declarations. Seven reusable baseline declaration libraries plus350 case-specific stable variant IDs specify typed symbolic fields, source anchors, digest constructions, actor separation and context/state relations. Parameters are not measured facts or boolean all-valid shortcuts. Future binding must supply every selected typed value and verify every constraint; missing/inconsistent inputs are NOT_EVALUABLE. A T8 pending-target authority case does not also assume an ordinary current ACTIVE qualified target exists. Raw source config/body/descriptor inputs remain in the trusted membrane model; Reader sees only its approved interface.

POSTMASTER remains the observed server subject; CENSUS_OBSERVER is the type201 response emitter, with its own signing identity. No POSTMASTER message key or SQL role is invented. Public expected endpoint manifests remain independent from private endpoint-subject custody/use capabilities. Principal, material, authority, generation, revocation and qualification are separately represented.

Every mutation is design data naming an exact component selector, before/after relation, invariant components and source predicate. No descriptor is applied to a fixture. Graph cases use the closed A4.2 Reader capability and separate SQL principal R; native participant OS identities are not SQL roles. SET, INHERIT, ADMIN, ownership, PUBLIC, default-ACL and SECURITY DEFINER effects retain separate source semantics. Default ACL applies only to an exact future creator/schema/kind event, not retroactively to an existing ACL. Search-path substitution changes actual trusted resolution, not an ignored ambient setting. No generic SQL/native API or invalid extra TLV is generated.

##133 structured candidates and217 former generic entries

All133 structured candidates bind uniquely by original participant/case identity. Binding is not proof. Exact N1 predicates govern case interpretation rather than N2’s blanket unequal→REJECT template: reused credentials include consumed work and readonly terminal duplicates; restart/reconnect preserve UNKNOWN_FAIL_CLOSED; producer/consumer substitution includes actual role/purpose/credential/birth separation rather than a numeric enum flip. Observer/writer identities stay distinct.

The217 generic inputs are each represented explicitly.210 receive a complete proposed bounded mapping: the35 formerly generic preserved cases plus175 new-family cases. Seven omission cases retain a specific source-native decision ambiguity. New-family specifications use actual accepted custody, currentness, roster, snapshot, reader and typed capability rules; names or generic N1 predicate text alone are not treated as authority.

## Exact remaining gap

Affected IDs: POSTMASTER/catalog_row_omission; SUPERVISOR/catalog_row_omission; RECEIVER/catalog_row_omission; CENSUS_OBSERVER/catalog_row_omission; APPROVAL_PRODUCER/catalog_row_omission; APPROVAL_CONSUMER/catalog_row_omission; ENFORCEMENT_WORKER/catalog_row_omission.

The bounded mutation deletes the exact expected Reader identity row from the observed pg_roles collection. `catalog-projection.json#/sources/0/MISSING_ROW_SEMANTICS` explicitly requires UNKNOWN for a missing expected identity/source row. The generic canonical `new_cases` line requires REJECT. No source states whether that label means broad authority denial, a strict result enum, or a different omission variant. C5D does not silently normalize REJECT to UNKNOWN or rewrite either record. Exact canonical decision/output authority must be supplied, or a differently justified omission variant must be explicitly bound.

This does not prevent a coherent350-identity registry, so it is not an identity contradiction Outcome C. No particular separately frozen context/scope/atomic/universe decision has been proved necessary for this result-mapping gap, so Outcome D is not asserted.

## Coverage and retained status

Records350; structured binding133 unique; generic mapping210/217. Baseline specification350 complete, mutation descriptor350 complete, decision predicate/authority chain343 complete and7 incomplete. Classification sum:0 STATICALLY_PROVEN +0 STATICALLY_DISPROVEN +343 SPEC_COMPLETE_NOT_EVALUATED +7 SPEC_INCOMPLETE +0 CONTRADICTED =350. Complete here means a parameterized design, not a materialized fixture, successful evaluation or physical proof.

T8 remains prospectively designated and resolved within its approved bounded no-automatic-authority-transfer rule. Material/principal continuity does not establish authority. Other participants retain their independent currentness/no-adoption rules; T8 designation is not extended to them. Conditional allowed continuity does not waive existing scoped fresh-key, endpoint, retained-parent, retirement or requalification rules. Full external I13 remains independently mandatory. No substitution necessity/sufficiency is invented.

All350 witness proofs remain UNKNOWN. N1 substitution OPEN,12decisions=11closed+1open; V2 proof FAIL/status BLOCKED. POSTMASTER context binding, internal scope, atomic boundary and internal universe/total remain unresolved. Candidate108/ambiguity105/attack350 unchanged. Zero attacks materialized/evaluated. No implementation/build/native runtime/SQL/database/V043/B02/git add/commit/push; only C5D evidence files written. Independent reviews validate specification quality and fail-closed accounting, not authority by agreement or witness closure.

NEXT_GATE=BOUNDED_STATIC_WITNESS_GAP_CLOSURE. NEXT_EXECUTED=false. Stop after C5D.
'''
    (E/'PACKAGE-0090-B01-v2-native-static-closure-r5n2a5-3c5d.md').write_text(text,encoding='utf-8')


def validate():
    rows=rd(HERE/'canonical-350-registry.json')['case_records'];original=rd(N2/'substitution-witnesses.json')['cases']
    assert len(rows)==350 and [r['WITNESS_ID'] for r in rows]==[r['ATTACK_ID'] for r in original]
    assert len(set(r['WITNESS_ID'] for r in rows))==350
    assert all(not r['EVALUATED'] and not r['PROVEN'] for r in rows)
    assert all(r['STATUS'] in ['SPEC_COMPLETE_NOT_EVALUATED','SPEC_INCOMPLETE'] for r in rows)
    pre=rd(HERE/'preflight.json');assert all(sha(ROOT/k)==v for k,v in pre['preexisting_sha256'].items())
    for r in rd(HERE/'authority-provenance.json')['source_selections']:
        assert sha(ROOT/r['path'])==r['sha256'];assert canonical(select(rd(ROOT/r['path']),r['pointer']))==r['canonical_fact_sha256']
    assert subprocess.check_output(['git','diff','--name-only'],cwd=ROOT)==b''
    assert subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT)==b''
    return len(pre['preexisting_sha256'])


if __name__=='__main__':
    assert ROOT==pathlib.Path('C:/Projects/flooow-genesis-git')
    _,abi,_=schema_library();baseline_models(abi);families=family_descriptors();rows=registry(families,abi);artifacts(rows);summary(rows);report()
    print('C5D_DRAFT_CONSTRUCTED; CASES=350; SPEC_COMPLETE_NOT_EVALUATED=343; SPEC_INCOMPLETE=7; PRESERVED_HASHES='+str(validate()))
