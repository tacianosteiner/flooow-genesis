"""Static partial effect graph. Fail closed BEFORE Reader ACL if required effects unknown."""
import sys
sys.dont_write_bytecode=True
import hashlib,json,subprocess
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[2]
P='docs/evidence/package-0090-B01-v2-native-static-closure-r5n2a3/'
N='docs/evidence/package-0090-B01-v2-native-static-closure-r5n/'
A='docs/evidence/package-0090-B01-v2-native-static-closure-r5n1/'
B='docs/evidence/package-0090-B01-v2-native-static-closure-r5n2/'
PG='docs/evidence/package-0090-full-reachable-expectation-closure-v2/provider/'
BASE='cbc284f62d9bd09b7169b55c8d66a3c51a68c6cb'
def sha(b):return hashlib.sha256(b).hexdigest()
def rd(p):return json.loads((R/p).read_text(encoding='utf-8-sig'))
def wr(n,x):(O/n).write_bytes(json.dumps(x,indent=2,ensure_ascii=False).encode()+b'\n')
def doc(n,**x):wr(n+'.json',dict(scope='R5N2A4_STATIC_EFFECT_GRAPH_ONLY',implementation_performed=False,runtime_evidence_created=False,**x))
def git(*a):return subprocess.check_output(['git',*a],cwd=R).decode().strip()
def ref(p,ptr='/'):
    q=Path(p);q=q if q.is_absolute() else R/q
    return dict(path=q.relative_to(R).as_posix(),sha256=sha(q.read_bytes()),pointer=ptr)
def main():
    assert git('branch','--show-current')=='checkpoint/package-0090-cloud-handoff' and git('rev-parse','HEAD')==BASE
    assert not git('diff','--name-only') and not git('diff','--cached','--name-only')
    old=[p for p in git('ls-files','--others','--exclude-standard').splitlines() if '/package-0090-B01-v2-native-static-closure-r5n2a4/' not in p];assert len(old)==197
    f=rd(P+'baseline-freeze.json');f['source_checkout_sha256'].update({p:sha((R/p).read_bytes()) for p in old});f.update(untracked_before=197,untracked_before_paths=old,REMOTE_NETWORK_VERIFIED='NO');wr('baseline-freeze.json',f)
    pred=rd(P+'SOURCE-IDENTITY-GATE.json');assert pred['R5N2A3_STATUS']=='PASS_SOURCE_IDENTITY_FOUNDATION'
    assert sha((R/P/'postgres-source-manifest.json').read_bytes())=='0c378c960bfb00a6d309a9ebff93650d525068c2f740e1aa7769192cb6ca685a'
    projection=rd(A+'catalog-projection.json');codec=rd(B+'catalog-codec-type-table.json');predicates=rd(A+'catalog-security-predicates.json')['predicates']
    classes=rd(P+'credential-class-manifest.json');symbols=rd(P+'referent-symbol-table.json');stats=rd(P+'stats-field-proof.json');authority=rd(B+'decision-contracts.json')['contracts']['N1-CATALOG-EFFECT-GRAPH']['edges']
    assert len(projection['sources'])==19 and len(codec['fields'])==146 and len(predicates)==26 and len(authority)==12
    # Preserve predecessor authority names. Requested effects are a separate typed namespace, not renamed authorities.
    effects='READ OBSERVE DERIVE FILTER REDACT IDENTIFY AUTHENTICATE AUTHORIZE MUTATE ESCALATE SECRET_ACCESS ARBITRARY_OBJECT_ACCESS'.split()
    nodes={};edges=[]
    def node(key,kind,**kw):nodes.setdefault(key,dict(id=key,kind=kind,**kw));return key
    reader=node('PRINCIPAL/R5N1_READ_PROXY','LOGICAL_PRINCIPAL',identity_source=ref(P+'reader-identity-manifest.json'),not_native_participant=True)
    public=node('PRINCIPAL/PUBLIC','PUBLIC_SENTINEL',role_membership=False)
    producer=node('BOUNDARY/FIXED_SOURCE_PRODUCER','UNRESOLVED_PRODUCER_EXECUTION_BOUNDARY',actual_principal='UNKNOWN',not_new_authority=True)
    domain=node('DOMAIN/NATIVE_CATALOG','NATIVE_QUALIFICATION_AUTHORITY_DOMAIN',global_partitions=False)
    for p in rd(N+'native-participants.json')['participants']:node('PRINCIPAL/'+p['PARTICIPANT_ID'],'NATIVE_PARTICIPANT',source=ref(N+'native-participants.json'))
    for actor in ['HEALTH_GUARD','HOST_PLATFORM','NATIVE_REGISTRY_WRITER']:node('PRINCIPAL/'+actor,'EXISTING_AUXILIARY_AUTHORITY',source=ref(N+'native-registry-generation.json'))
    def edge(src,dst,kind,initiator,effective,origin,evidence,**kw):
        record=dict(source_node=src,target_node=dst,edge_type=kind,initiating_principal=initiator,effective_principal=effective,authority_source=origin,credential_class='READER_BOUND_SESSION_CAPABILITY' if initiator==reader else None,catalog_source_provenance=evidence,security_predicate=[],visibility_condition='Exact frozen source/identity + current relevant ACL and approved context; no authority inferred from name',redaction_null_behavior='NULL distinct from absent row, redaction distinct from noauthority; required unknown fails closed',mutation_possibility='FALSE_FOR_DECLARED_VALUE_READ',role_escalation_possibility='FALSE_FOR_VALUE_EDGE_ONLY',secret_material_possibility='NO_SECRET_FIELD_PROJECTED',arbitrary_object_possibility='NO_CALLER_SELECTOR_IN_DECLARED_INTERFACE',generation_custody_binding='Exact accepted source/session/process/generation/registry/context and private capability custody; actual runtime values FUTURE_MEASURED',static_evidence_reference=evidence,unresolved_status='STATIC_RULE_SUPPORTED_FUTURE_VALUES_PENDING',not_runtime_edge_instance=True,**kw)
        for name in list(record):
            if name.endswith('_override'):
                record[name[:-len('_override')]]=record.pop(name)
        record['id']='EDGE/'+sha(json.dumps(record,sort_keys=True,separators=(',',':')).encode());edges.append(record);return record['id']
    relation_map=[];field_map=[];raw_to_edge={};field_to_edges={};unknown_fields=[]
    for si,s in enumerate(projection['sources']):
        rel=s['SOURCE_ID'];rn=node('REL/'+rel,'FROZEN_SOURCE_RELATION',source=ref(A+'catalog-projection.json','/sources/'+str(si)))
        rid=edge(public,rn,'AUTHORITY/PUBLIC_ACL',reader,reader,'Frozen initdb.c setup_privileges PUBLIC SELECT bootstrap origin, conditional current ACL snapshot; not a new grant',ref(PG+'initdb.c'),effect_kind='READ',applicability='PUBLIC sentinel grant applies to caller, never a membership edge. SELECT on known metadata relation only when current relation/column ACL proves it; revoked privilege yields query failure/UNKNOWN; bootstrap rights alone not assumed current')
        relation_map.append(dict(source=rel,node=rn,edge=rid))
        filtered=node('FILTERED_SOURCE/'+rel,'FIXED_SOURCE_ROW_SET',row_predicate=s['EXACT_ROW_PREDICATE'])
        edge(rn,filtered,'EFFECT/FILTER',reader,reader,'Frozen exact row predicate; fixed source context, no caller-provided source/object selector',ref(A+'catalog-projection.json','/sources/'+str(si)+'/EXACT_ROW_PREDICATE'),effect_kind='FILTER',not_runtime_filter_execution=True)
        identity=node('ROW_IDENTITY/'+rel,'SOURCE_KEY_TUPLE_SCHEMA',keys=s['EXACT_JOIN_KEYS'])
        edge(filtered,identity,'EFFECT/IDENTIFY',reader,reader,'Frozen source key tuple binds metadata identity only, never permission inferred from name/OID alone',ref(A+'catalog-projection.json','/sources/'+str(si)+'/EXACT_JOIN_KEYS'),effect_kind='IDENTIFY',not_a_credential=True)
        for fi,field in enumerate(s['EXACT_PROJECTED_FIELDS']):
            name=field['source_field'];key=rel+'.'+name;fn=node('FIELD/'+key,'PROJECTED_SOURCE_FIELD',field_type=field['pg18_type'],source=ref(A+'catalog-projection.json','/sources/'+str(si)+'/EXACT_PROJECTED_FIELDS/'+str(fi)))
            fact=node('FACT/'+key,'CANONICAL_FIELD_FACT',codec=ref(B+'catalog-codec-type-table.json'))
            source_ref=ref(A+'catalog-projection.json','/sources/'+str(si)+'/EXACT_PROJECTED_FIELDS/'+str(fi))
            raw=edge(reader,fn,'EFFECT/READ',reader,reader,'Applicable relation SELECT or exact column SELECT from source ACL; derived from typed PG ACL, not column spelling',source_ref,effect_kind='READ',relation_authority_edge=rid)
            expr=field['expression']['op'];cfg=name in ['proconfig','setconfig'];hashed=expr=='NULL_PRESERVING_SHA256_UTF8_STORED_BYTES';gap=cfg or hashed
            if gap:
                edges[-1]['secret_material_possibility']='POTENTIAL_RAW_SOURCE_SECRET_VALUE; transformation-before-reader boundary unresolved; not benign credential metadata'
                edges[-1]['id']='EDGE/'+sha(json.dumps({k:v for k,v in edges[-1].items() if k!='id'},sort_keys=True,separators=(',',':')).encode());raw=edges[-1]['id']
            raw_to_edge[key]=raw
            effective='UNKNOWN_SOURCE_ADAPTER_PRINCIPAL' if gap else reader
            transform=edge(fn,fact,'EFFECT/REDACT' if gap else 'EFFECT/DERIVE',reader,effective,'Closed config/codec specifies output transformation; executing principal and fixed producer invocation plan not bound' if gap else 'Closed pure canonical scalar/ACL decoder; never SQL type input/evaluator',ref(B+'catalog-codec-type-table.json'),effect_kind='REDACT' if gap else 'DERIVE',transformation='CONFIG_ASSERTIONS_V2, never raw values' if cfg else expr,
              unresolved_status_override='UNKNOWN_PRODUCER_AUTHORITY_AND_CALLABLE_PLAN' if gap else 'NONE')
            edges[-1]['unresolved_status']='UNKNOWN_PRODUCER_AUTHORITY_AND_CALLABLE_PLAN' if gap else 'STATIC_RULE_SUPPORTED_FUTURE_VALUES_PENDING'
            edges[-1]['secret_material_possibility']='POTENTIAL_RAW_CONFIGURATION_OR_STORED_BODY; must not cross into reader before approved transform' if gap else 'NO_SECRET_FIELD_PROJECTED'
            edges[-1]['mutation_possibility']='UNKNOWN_EXECUTING_CALLABLES; pure intended transform is not effect provenance' if gap else 'FALSE_PURE_DECODER'
            edges[-1]['role_escalation_possibility']='UNKNOWN_PRODUCER_EFFECTIVE_PRINCIPAL' if gap else 'FALSE_PURE_DECODER'
            edges[-1]['arbitrary_object_possibility']='UNKNOWN_SOURCE_INVOCATION_PLAN; no caller selector approved' if gap else 'FALSE_PURE_DECODER'
            # IDs identify immutable final records, not pre-final updates.
            edges[-1]['id']='EDGE/'+sha(json.dumps({k:v for k,v in edges[-1].items() if k!='id'},sort_keys=True,separators=(',',':')).encode());transform=edges[-1]['id']
            field_to_edges[key]=[raw,transform]
            field_map.append(dict(source=rel,field=name,key=key,source_node=fn,fact_node=fact,edges=[raw,transform],direct_field_transformation_supported=not gap,global_producer_effect_proven=False,unresolved_subcondition='G1_SOURCE_TRANSFORMER_PRINCIPAL_AND_EXECUTION_PLAN' if gap else 'G2_PRODUCER_CALL_PATH_GLOBAL_PRECONDITION'))
            if gap:unknown_fields.append(key)
    # Exact accepted statistics source selection remains a separate fact graph; never fill raw PG NULLs.
    stat_edges=[]
    for fact in stats['fields']:
        key='pg_catalog.pg_stat_activity.'+fact['FIELD_ID'];target=node('SELECTED_STATS_FACT/'+fact['FIELD_ID'],'ACCEPTED_SELECTED_SOURCE_FACT',source=ref(P+'stats-field-proof.json'))
        protected=fact['FIELD_ID'] in ['backend_start','backend_type']
        origin=node('SOURCE/LOGIN_BRIDGE_OWN_SESSION' if protected else 'SOURCE/PG_GENERAL_STATS','ACCEPTED_SOURCE',source=ref(P+'stats-field-proof.json'))
        stat_edges.append(edge(origin,target,'EFFECT/OBSERVE',reader,'GOVERNED_CLIENT_OWN_BACKEND' if protected else reader,'Accepted source-specific minimal authority, no stats role/member',ref(P+'stats-field-proof.json'),effect_kind='OBSERVE',visibility_condition_override=fact['VISIBILITY_BRANCH'],raw_column_semantics='Raw protected NULL preserved; selected bridge fact carries distinct provenance. Required absence/zero/unbound receipt=>UNKNOWN'))
    # All12 predecessor authority constructors retained with exact origin semantics, never merged with dataflow effects.
    authority_edges=[]
    for kind,meaning in authority.items():
        src=node('SYMBOLIC_SOURCE/'+kind,'TYPED_FUTURE_CATALOG_NODE',identity='Source row OID/origin, not a runtime observation')
        dst=node('SYMBOLIC_TARGET/'+kind,'TYPED_FUTURE_CATALOG_NODE',identity='Target role/object/OID plus typed scope')
        ek='ESCALATE' if kind in ['HAS_ADMIN_ON','CAN_SET_ROLE_TO','CREATEROLE_EFFECT','SUPERUSER_EFFECT','BYPASSRLS_EFFECT','SECURITY_DEFINER_EXECUTION_PATH'] else 'AUTHORIZE'
        proof=ref(PG+'acl.c') if kind in ['MEMBER_OF','INHERITS_FROM','CAN_SET_ROLE_TO','HAS_ADMIN_ON'] else ref(PG+'aclchk.c')
        status='UNKNOWN_FIXED_PRODUCER_CALLABLE_EFFECT_SET' if kind=='SECURITY_DEFINER_EXECUTION_PATH' else 'STATIC_TYPED_RELATION_RULE; future catalog values are not invented'
        authority_edges.append(edge(src,dst,'AUTHORITY/'+kind,'SOURCE_ROW_GRANTEE_OR_MEMBER','SOURCE_ROW_EFFECTIVE_PRINCIPAL',meaning,proof,effect_kind=ek,unresolved_status_override=status,constructor_only=True,origin_distinctions='Membership/INHERIT/SET/ADMIN/owner/PUBLIC/direct/defaultfuture/SD remain separate; actual row values future measured; owner implicit rights not ordinarygrant; default creator+schema+kind preserved'))
        edges[-1]['unresolved_status']=status
        edges[-1]['mutation_possibility']='CONDITIONAL_ON_PRIVILEGE_KIND_OR_AUTHORITY_TRANSITION; not a read-only assertion'
        edges[-1]['role_escalation_possibility']='CONDITIONAL_TYPED_TRANSITION; INHERIT/SET/ADMIN/owner/SD never conflated' if ek=='ESCALATE' or kind=='OWNS' else 'Depends on exact typed target rights, not authentication'
        edges[-1]['secret_material_possibility']='Depends on exact target/source field and callable effects; not automatically benign metadata'
        edges[-1]['arbitrary_object_possibility']='Only exact source target scope; unresolved callable expansion remainsUNKNOWN'
        edges[-1]['id']='EDGE/'+sha(json.dumps({k:v for k,v in edges[-1].items() if k!='id'},sort_keys=True,separators=(',',':')).encode());authority_edges[-1]=edges[-1]['id']
    # Seven native participant boundaries remain explicit; no auxiliary reader identity is a slot alias.
    for i,profile in enumerate(rd(A+'execution-isolation.json')['profiles']):
        pn='PRINCIPAL/'+profile['PARTICIPANT_ID'];bn=node('NATIVE_BOUNDARY/'+profile['PARTICIPANT_ID'],'ACCEPTED_NATIVE_BOUNDARY',SQL_CREDENTIAL_AUTHORITY='NONE',postmaster_service_exception=profile['PARTICIPANT_ID']=='POSTMASTER')
        edge(pn,bn,'EFFECT/AUTHORIZE',pn,pn,'Accepted native isolation profile explicitly denies direct SQL credentials/sessions/API; POSTMASTER private service storage is not an SQL login grant',ref(A+'execution-isolation.json','/profiles/'+str(i)+'/DATABASE_CONNECTION_POLICY'),effect_kind='AUTHORIZE',direct_SQL_route='NOT_REACHABLE_BY_FIXED_NATIVE_CONTRACT',reader_capability_not_transferred=True,not_a_Reader_ACL_derivation=True)
    # Account every actual credential reference as authentication/custody, never SQL authorization.
    credential_map=[]
    for r in symbols['adjudications']:
        if r['REFERENT_TYPE']!='ACTUAL_CREDENTIAL':continue
        cr=node('CREDENTIAL_REFERENCE/'+r['REFERENCE_ID'],'ACTUAL_CREDENTIAL_REFERENCE',symbol=r['REFERENT_SYMBOL'],class_id=r['CREDENTIAL_CLASS_ID'],not_material_payload=True)
        owner=node('CREDENTIAL_OWNER/'+r['REFERENT_OWNER'],'DECLARED_CUSTODIAN',source=ref(P+'referent-symbol-table.json'))
        eid=edge(cr,owner,'EFFECT/AUTHENTICATE',owner,owner,'Exact accepted class purpose and source-bound custodian; no implied SQL privilege',ref(P+'credential-class-manifest.json'),effect_kind='AUTHENTICATE',credential_reference=r['REFERENCE_ID'],secret_material_possibility_override='Private signer key may be used only internally by custodian; no secret emitted as metadata',no_authn_authz_collapse=True)
        edges[-1]['credential_class']=r['CREDENTIAL_CLASS_ID'];edges[-1]['secret_material_possibility']='PRIVATE_TO_DECLARED_CUSTODIAN_ONLY; not reader metadata';edges[-1]['id']='EDGE/'+sha(json.dumps({k:v for k,v in edges[-1].items() if k!='id'},sort_keys=True,separators=(',',':')).encode());credential_map.append(dict(reference=r['REFERENCE_ID'],class_id=r['CREDENTIAL_CLASS_ID'],edge=edges[-1]['id']))
    # Explicit potential producer surface. An unspecified fixed plan cannot be classified as harmless.
    source_callable=node('SOURCE_OPERATION/PRODUCER_CALLABLE_SET','UNRESOLVED_REQUIRED_STATIC_SET',missing='Exact executable source projection/normalizer/query/type/default-argument plan and authority provenance')
    gap_edge=edge(producer,source_callable,'EFFECT/DERIVE',reader,'UNKNOWN_EFFECTIVE_PRINCIPAL','Frozen requirement for fixed source producer, not a bound invocation/effect manifest',ref(A+'catalog-reader.json'),effect_kind='DERIVE',unresolved_status_override='UNKNOWN_SOURCE_CALLABLE_SET',candidate_effects=['MUTATE','ESCALATE','SECRET_ACCESS','ARBITRARY_OBJECT_ACCESS'],not_an_allow_or_deny=True)
    edges[-1]['unresolved_status']='UNKNOWN_SOURCE_CALLABLE_SET';edges[-1]['mutation_possibility']=edges[-1]['role_escalation_possibility']=edges[-1]['secret_material_possibility']=edges[-1]['arbitrary_object_possibility']='UNKNOWN_REQUIRED_EFFECT_SET';edges[-1]['id']='EDGE/'+sha(json.dumps({k:v for k,v in edges[-1].items() if k!='id'},sort_keys=True,separators=(',',':')).encode());gap_edge=edges[-1]['id']
    # Predicate attachment is metadata only; final qualification inputs/witnesses are NOT evaluated here.
    mappings={
      'IS_EXPECTED_ROLE':['pg_catalog.pg_roles.oid','pg_catalog.pg_roles.rolname'],'HAS_LOGIN':['pg_catalog.pg_roles.rolcanlogin'],'IS_SUPERUSER':['pg_catalog.pg_roles.rolsuper'],'HAS_CREATEROLE':['pg_catalog.pg_roles.rolcreaterole'],'HAS_BYPASSRLS':['pg_catalog.pg_roles.rolbypassrls'],
      'CAN_INHERIT_ROLE':['pg_catalog.pg_auth_members.member','pg_catalog.pg_auth_members.roleid','pg_catalog.pg_auth_members.inherit_option'],'CAN_SET_ROLE':['pg_catalog.pg_auth_members.member','pg_catalog.pg_auth_members.roleid','pg_catalog.pg_auth_members.set_option'],'HAS_ADMIN_OPTION':['pg_catalog.pg_auth_members.member','pg_catalog.pg_auth_members.roleid','pg_catalog.pg_auth_members.admin_option'],
      'IS_OBJECT_OWNER':['pg_catalog.pg_class.relowner','pg_catalog.pg_database.datdba','pg_catalog.pg_type.typowner'],'IS_SCHEMA_OWNER':['pg_catalog.pg_namespace.nspowner'],'IS_FUNCTION_OWNER':['pg_catalog.pg_proc.proowner'],
      'HAS_DIRECT_PRIVILEGE':['pg_catalog.pg_class.relacl','pg_catalog.pg_attribute.attacl','pg_catalog.pg_proc.proacl'],'HAS_GRANT_OPTION':['pg_catalog.pg_class.relacl','pg_catalog.pg_proc.proacl','pg_catalog.pg_auth_members.inherit_option'],'HAS_PUBLIC_PRIVILEGE':['pg_catalog.pg_class.relacl','pg_catalog.pg_proc.proacl'],
      'HAS_DEFAULT_PRIVILEGE_PATH':['pg_catalog.pg_default_acl.defaclrole','pg_catalog.pg_default_acl.defaclnamespace','pg_catalog.pg_default_acl.defaclobjtype','pg_catalog.pg_default_acl.defaclacl'],
      'HAS_SECURITY_DEFINER_PATH':['pg_catalog.pg_proc.prosecdef','pg_catalog.pg_proc.proowner','pg_catalog.pg_proc.proacl','pg_catalog.pg_proc.prosrc','pg_catalog.pg_proc.proconfig'],
      'HAS_TRANSITIVE_MEMBERSHIP_PATH':['pg_catalog.pg_auth_members.member','pg_catalog.pg_auth_members.roleid'],'HAS_BOOTSTRAP_AUTHORITY_PATH':['pg_catalog.pg_roles.rolcreaterole','pg_catalog.pg_roles.rolsuper','pg_catalog.pg_proc.prosrc'],
      'HAS_UNEXPECTED_WRITE_PATH':['pg_catalog.pg_proc.prosrc','pg_catalog.pg_proc.prosecdef','pg_catalog.pg_policy.polqual','pg_catalog.pg_trigger.tgqual','pg_catalog.pg_rewrite.ev_action'],
      'HAS_UNEXPECTED_OBSERVATION_PATH':['pg_catalog.pg_proc.proconfig','pg_catalog.pg_db_role_setting.setconfig','pg_catalog.pg_proc.prosrc'],
      'HAS_UNEXPECTED_CREDENTIAL_PATH':['pg_catalog.pg_proc.prosrc','pg_catalog.pg_proc.proconfig','pg_catalog.pg_db_role_setting.setconfig'],
      'ROLE_ROSTER_EXACT':['pg_catalog.pg_roles.oid','pg_catalog.pg_roles.rolname'],'BACKEND_CENSUS_EXACT':['pg_catalog.pg_stat_activity.datid','pg_catalog.pg_stat_activity.pid','pg_catalog.pg_stat_activity.usesysid','pg_catalog.pg_stat_activity.usename','pg_catalog.pg_stat_activity.backend_start','pg_catalog.pg_stat_activity.backend_type'],
      'FUNCTION_CONFIG_SAFE':['pg_catalog.pg_proc.proconfig','pg_catalog.pg_proc.prosrc','pg_catalog.pg_depend.objid','pg_catalog.pg_depend.refobjid'],
      'SNAPSHOT_COHERENT':list(field_to_edges),'NATIVE_QUALIFIED':list(field_to_edges)}
    unresolved_predicates={'HAS_SECURITY_DEFINER_PATH','HAS_BOOTSTRAP_AUTHORITY_PATH','HAS_UNEXPECTED_WRITE_PATH','HAS_UNEXPECTED_OBSERVATION_PATH','HAS_UNEXPECTED_CREDENTIAL_PATH','FUNCTION_CONFIG_SAFE'}
    predicate_map=[]
    for i,p in enumerate(predicates):
        pn=node('PREDICATE/'+p['id'],'CARRIED_SECURITY_PREDICATE',definition=ref(A+'catalog-security-predicates.json','/predicates/'+str(i)))
        keys=mappings[p['id']];assert keys and all(k in field_to_edges for k in keys)
        assoc=[eid for k in keys for eid in field_to_edges[k]]
        for e in edges:
            if e['id'] in assoc:e['security_predicate'].append(p['id'])
        predicate_map.append(dict(id=p['id'],node=pn,source_fields=keys,affected_edges=assoc,static_effect_semantics='UNKNOWN_SOURCE_PRODUCER_PLAN' if p['id'] in unresolved_predicates else 'CARRIED_SCHEMA_CONSTRAINT_NO_RUNTIME_TRUTH_CLAIM',not_final_qualification_resolution=True))
    # Predicate tags are association indexes, excluded from edge identity preimage to keep IDs stable.
    graph=dict(scope='NATIVE_ONLY_PARTIAL_EFFECT_GRAPH',graph_kind='Static source interaction/authority templates, NOT observed runtime graph',nodes=list(nodes.values()),edges=edges,canonical_authority_edge_types=list(authority),effect_edge_types=effects,edge_type_reconciliation='12 predecessor authority names preserved verbatim in AUTHORITY namespace +12 explicitly requested data-effect names in EFFECT namespace;24 typed names, no authority replacement or privilege creation. effect_kind is a separate annotation on authority edges.',identity_rule='Stable edge source/target/type/principal/authority/evidence preimage; predicate tags are separate coverage index, not authority',not_complete=True)
    wr('effect-graph.json',graph)
    gaps=[dict(ID='G1_SOURCE_TRANSFORMER_PRINCIPAL_AND_EXECUTION_PLAN',BLOCKER_ID='N1-CATALOG-EFFECT-GRAPH',EXACT_MISSING_DECISION='For the ten configured/body fields bind exact source acquisition -> transforming operation -> effective principal -> reader result path, so raw secret-bearing values never reach the reader under an unproved adapter boundary.',AFFECTED_FIELDS=unknown_fields,SOURCE=[ref(A+'catalog-projection.json'),ref(B+'catalog-codec-type-table.json'),ref(P+'reader-identity-manifest.json')],WHY_STATIC='Closed output codec/config policy specifies WHAT may leave, not which authority/path executes acquisition and transformation. This is missing static source-principal/operation plan, not missing future key/OID/binary value.',MINIMUM_NEXT_ACTION='Provide a finite typed source projection/normalization plan with executing principals, exact field transformations and source/effect provenance. Keep existing output restrictions and no role/secret widening.'),
      dict(ID='G2_FIXED_PRODUCER_CALLABLE_EFFECT_UNIVERSE',BLOCKER_ID='N1-CATALOG-EFFECT-GRAPH',EXACT_MISSING_DECISION='Bind all explicit and implicit parser/type/default/routine calls of the fixed producer to source-backed effects or prove those call families unreachable. A body hash alone is not a body-effect proof.',AFFECTED_PREDICATES=sorted(unresolved_predicates),SOURCE=[ref(A+'catalog-security-predicates.json'),ref('docs/evidence/package-0090-B01-v2-native-static-closure-r5n2a2/native-effect-graph.json')],WHY_STATIC='The finite source callable/operation set and effect construction rule must be fixed before an implementation can conform. No physical authentication selection or actual runtime catalog snapshot is demanded.',MINIMUM_NEXT_ACTION='Derive the producer invocation/effect manifest from the typed source plan, preserve creator/default/owner/INHERIT/SET/ADMIN distinctions, and prove unsupported calls fail before effects. Do not assign ALLOW/DENY to a future boundary merely by intention.')]
    doc('graph-completeness',relation_map=relation_map,field_map=field_map,predicate_map=predicate_map,credential_map=credential_map,inventory_coverage=True,semantic_completeness=False,unresolved_fields=unknown_fields,unresolved_predicates=sorted(unresolved_predicates),missing_field_families='NOT_ESTABLISHED_UNTIL_FIXED_PRODUCER_PLAN; default-argument/type-call families require applicability proof, not automatic expansion of146 fields',required_effect_gaps=gaps,graph_status='OPEN',reader_acl_may_begin=False,no_closed_contract_reopened=True)
    # Mandatory user STOP reached. No Reader ACL derivation or independent adversarial review begins.
    doc('reader-effective-acl',STATUS='NOT_DERIVED_GRAPH_PRECONDITION_FALSE',N1_READER_EFFECTIVE_ACL='OPEN',entries=[],unresolved='NOT_EVALUATED_GRAPH_OPEN',section4_executed=False,reason='User §3 STOP and §4 requires graphCLOSED; no ACL invented from desired invariants')
    doc('reader-invariants',STATUS='NOT_DERIVED',invariants={k:dict(conclusion='UNKNOWN',reachable_edge_set='NOT_TRAVERSED_GRAPH_OPEN',authority_provenance='See partialgraph/gaps, no Reader conclusion',credential_interaction='A3 preserved only; no additional rights',counterexample_search='NOT_RUN_SECTION4',contradiction_search='NOT_RUN_SECTION4',evidence=ref(O/'graph-completeness.json')) for k in ['READER_NO_MUTATION_PATH','READER_NO_ROLE_ESCALATION_PATH','READER_NO_CREDENTIAL_SECRET_PATH','READER_NO_GENERIC_SQL_AUTHORITY','READER_NO_ARBITRARY_OBJECT_AUTHORITY']})
    doc('adversarial-review',STATUS='NOT_RUN_PRECONDITION_FALSE',independent_reviewer_invoked=False,reason='User §5 authorizes adversarial review after BOTH blockers appearclosed; graphOPEN triggered mandatedSTOP before Reader ACL. No independent reviewPASS or reviewerFAIL is fabricated.',gate_review_requirement='UNSATISFIED_FAIL_CLOSED')
    doc('preserved-facts',predecessor=ref(P+'SOURCE-IDENTITY-GATE.json'),source_manifest_sha256='0c378c960bfb00a6d309a9ebff93650d525068c2f740e1aa7769192cb6ca685a',accepted_stats=ref(P+'stats-field-proof.json'),accepted_classes=ref(P+'credential-class-manifest.json'),accepted_reader=ref(P+'reader-identity-manifest.json'),closed_contracts_reopened=0,contradictions_discovered=0,deferred_final_two=['N1-QUALIFICATION-INPUT-RESOLUTION','N1-SUBSTITUTION-STATIC-WITNESSES'])
    print(json.dumps(dict(graph='OPEN',relations=len(relation_map),fields=len(field_map),predicates=len(predicate_map),authority_types=len(authority),data_effect_types=len(effects),edges=len(edges),unknown_fields=len(unknown_fields),unknown_predicates=len(unresolved_predicates),reader_acl_started=False,independent_review_started=False)))
if __name__=='__main__':main()
