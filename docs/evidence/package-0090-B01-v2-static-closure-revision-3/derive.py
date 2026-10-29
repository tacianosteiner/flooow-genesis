"""R3 offline source derivation, never a mutation dispatcher or runtime harness.

Normalized records expand deterministically to per-target/per-form obligations.
Known obligation counts are deliberately distinct from a COMPLETE denominator.
All database/native sources below are read as bytes, never imported/executed.
"""
import argparse
import collections
import functools
import hashlib
import itertools
import json
from pathlib import Path
import re
import subprocess
import zlib

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
BASE = 'c086a15640bf281defb829cb3d8c24f10272136d'
BRANCH = 'checkpoint/package-0090-cloud-handoff'
SRC = 'docs/evidence/package-0090-full-reachable-expectation-closure-v2/'
R2 = 'docs/evidence/package-0090-B01-v2-static-closure-revision-2/'
PROVIDER = SRC + 'provider/'
V043 = 'applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V043__create_governed_offline_field_proof_capability_composition.sql'
VHASH = '007ab786c417c41e2b1702ebf3852cb70ff5c142fa3fde195385e04c6dde8b4a'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def sha(value):
    return hashlib.sha256(value).hexdigest()


def canon(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


def save(name, value):
    with (OUT/name).open('w', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, indent=2, ensure_ascii=False)
        f.write('\n')


@functools.lru_cache(None)
def tree():
    result = {}
    for row in git('ls-tree', '-r', '-z', BASE).split(b'\0'):
        if row:
            meta, path = row.split(b'\t', 1)
            result[path.decode()] = meta.decode().split()[2]
    return result


@functools.lru_cache(None)
def blob(path):
    return git('show', BASE + ':' + path)


@functools.lru_cache(None)
def js(path):
    return json.loads(blob(path).decode('utf-8-sig'))


@functools.lru_cache(None)
def file_sha(path):
    return sha(blob(path))


def pointer(path, ptr='/'):
    return {'path': path, 'git_blob_oid': tree()[path], 'git_sha256': file_sha(path), 'pointer': ptr}


def lineptr(path, text):
    content = blob(path).decode('utf-8-sig')
    pos = content.find(text)
    assert pos >= 0, (path, text)
    return {'path': path, 'git_blob_oid': tree()[path], 'git_sha256':file_sha(path),
            'line':content[:pos].count('\n')+1, 'anchor':text}


def resolve(doc, ptr):
    for s in ptr.strip('/').split('/') if ptr != '/' else []:
        s=s.replace('~1','/').replace('~0','~')
        doc=doc[int(s)] if isinstance(doc,list) else doc[s]
    return doc


def initial_input_paths():
    ext={'.c','.h','.py','.java','.kt','.kts','.sql','.rs','.go','.sh','.cpp','.cc','.js','.ts'}
    return [p for p in tree() if Path(p).suffix in ext or p.startswith(R2) or
           p.startswith(SRC) and '/target-' not in p and '/development-' not in p and '/qualification-prototype-' not in p or
           p.startswith('docs/evidence/package-0090-B01-v2-expanded-capability-mediation/') or
           p in ['AGENTS.md','docs/evidence/PACKAGE-0090-B01-v2-static-closure-revision-2.md'] or
           p.startswith('docs/specifications/') or p.startswith('docs/adr/') or
           p.startswith('docs/evidence/package-0090-g3f4-executable-handoff-native-health/')]


def freeze():
    assert git('branch','--show-current').decode().strip()==BRANCH
    assert git('rev-parse','HEAD').decode().strip()==BASE
    assert git('rev-parse','origin/'+BRANCH).decode().strip()==BASE
    for s in git('status','--porcelain','--untracked-files=all').decode().splitlines():
        assert s[3:].replace('\\','/').startswith(OUT.relative_to(ROOT).as_posix()+'/'),s
    assert not git('diff','--cached','--name-only').strip()
    ext={'.c','.h','.py','.java','.kt','.kts','.sql','.rs','.go','.sh','.cpp','.cc','.js','.ts'}
    paths=initial_input_paths()
    # Batch byte retrieval avoids per-file process overhead and pins all source inputs.
    oids=list(dict.fromkeys(tree()[p] for p in paths))
    payload=subprocess.check_output(['git','cat-file','--batch'],input=('\n'.join(oids)+'\n').encode(),cwd=ROOT)
    by_oid={};pos=0
    for expected in oids:
        end=payload.index(b'\n',pos); header=payload[pos:end].decode().split();size=int(header[2]);pos=end+1
        assert header[0]==expected and header[1]=='blob'
        by_oid[expected]=payload[pos:pos+size];pos+=size+1
    hashes={p:sha(by_oid[tree()[p]]) for p in sorted(paths)}
    vb=by_oid[tree()[V043]]
    assert sha(vb)==VHASH
    crc=zlib.crc32(''.join(vb.decode('utf-8-sig').splitlines()).encode());crc=crc if crc<2**31 else crc-2**32
    assert crc==1279591798
    assert vb.index(b"RAISE EXCEPTION USING ERRCODE = '55000'")<vb.index(b'SET LOCAL search_path')
    protected={}
    for ref in js(R2+'source-integrity.json')['protected_refs']:
        r=subprocess.run(['git','rev-parse','--verify',ref],cwd=ROOT,capture_output=True)
        protected[ref]=r.stdout.decode().strip() if r.returncode==0 else 'REF_ABSENT_AT_BASELINE'
    save('baseline-freeze.json',{'branch':BRANCH,'baseline_head':BASE,'origin_head_after_fetch':BASE,
        'worktree_clean_before_evidence':True,'staged_changes_before_evidence':0,
        'baseline_tree':git('rev-parse',BASE+'^{tree}').decode().strip(),
        'repository_tracked_paths':len(tree()),'input_count':len(hashes),'input_git_sha256':hashes,
        'source_like_paths':sum(Path(p).suffix in ext for p in tree()),'protected_refs':protected,
        'CURRENT_V043_GIT_LF_SHA256':sha(vb),'FLYWAY_SIGNED_CRC32':crc,'V043_FENCE_PRESENT':True,
        'fetch_performed':True,'read_only_R2_verifier_passed':True})


def constraint_analysis():
    cs=js(SRC+'constraint-v2.json')['constraints']
    cols=js(SRC+'column-v2.json')['columns']
    pk={};fk=[]
    def strings(items):return [x['String']['sval'] for x in items]
    for i,c in enumerate(cs):
        s=c['source'];typ=s['contype']
        if typ=='CONSTR_PRIMARY':pk.setdefault(c['relation'],set()).update(strings(s['keys']))
        if typ=='CONSTR_FOREIGN':
            rv=s['pktable'];fk.append({'constraint_index':i,'from':c['relation'],
                'to':rv.get('schemaname','public')+'.'+rv['relname'],
                'from_columns':strings(s['fk_attrs']),'to_columns':strings(s.get('pk_attrs',[]))})
    results=[]
    for i,c in enumerate(cs):
        s=c['source'];typ=s['contype'];rel=c['relation'];keys=strings(s.get('keys',[]))
        physical={'database':'g3f4','catalog':'pg_constraint','relation':rel,'name':s['conname'],
                  'dynamic_oid_rule':'Resolve exact relation + conname + contype under pinned source; never guess OID'}
        external=[f for f in fk if f['to']==rel and f['to_columns']==keys] if typ in ['CONSTR_PRIMARY','CONSTR_UNIQUE'] else []
        drop='NOT_PROVEN';reason=[]
        if typ=='CONSTR_NOTNULL':
            column=keys[0];physical['column']=column
            if column in pk.get(rel,set()):
                drop='STRUCTURALLY_DENIED_UNDER_FROZEN_PK';reason.append('dropconstraint_internal refuses primary-key member, before catalog mutation')
            col=next((x for x in cols if x['relation']==rel and x['name']==column),None)
            if col and col['identity']:
                drop='STRUCTURALLY_DENIED_UNDER_IDENTITY';reason.append('identity attribute rejects DROP NOT NULL')
            effects=['Remove exact pg_constraint contype n row when represented; pg_attribute.attnotnull=false',
                     'Remove recorded dependencies; retain PK prohibition, replica identity, inherited/partition and system-catalog restrictions']
        elif typ in ['CONSTR_PRIMARY','CONSTR_UNIQUE']:
            if external:drop='RESTRICT_DENIED_WITH_FROZEN_EXTERNAL_FK';reason.append('Referenced key has external FK dependency; RESTRICT cannot silently cascade')
            effects=['Exact constraint removal','Backing pg_class index, pg_index and index dependencies removed',
                     'CASCADE would remove dependent FK constraints/internal triggers and is NOT authorized by this record',
                     'NOT NULL attributes/constraints must be observed independently, never assumed removed with PK']
        elif typ=='CONSTR_FOREIGN':effects=['Remove exact FK pg_constraint row','Dependent internal RI triggers and pg_depend entries removed; referenced relation retained']
        else:effects=['Remove exact CHECK pg_constraint row','Expression type/function/operator dependency links removed; target data unchanged by DROP']
        validate='ELIGIBLE_TYPE_BUT_VALIDATED_SOURCE_NOOP_OR_LIVE_PRECONDITION_UNKNOWN' if typ in ['CONSTR_CHECK','CONSTR_FOREIGN','CONSTR_NOTNULL'] else 'NOT_APPLICABLE_PK_UNIQUE'
        forms=['ADD','DROP_RESTRICT','DROP_CASCADE','DROP_ADD_REPLACE','RENAME','OWNER_AUTHORITY_CHANGE','SCHEMA_AUTHORITY_CHANGE','BOOTSTRAP_CATALOG_WRITE']
        if typ in ['CONSTR_CHECK','CONSTR_FOREIGN','CONSTR_NOTNULL']:forms+=['ADD_NOT_VALID','VALIDATE','ALTER_ENFORCEMENT']
        if typ=='CONSTR_NOTNULL':forms+=['SET_NOT_NULL','DROP_NOT_NULL','ALTER_NO_INHERIT','PG_ATTRIBUTE_AND_PG_CONSTRAINT_COUPLING']
        if typ in ['CONSTR_PRIMARY','CONSTR_UNIQUE','CONSTR_FOREIGN']:forms+=['ALTER_DEFERRABILITY']
        if typ in ['CONSTR_PRIMARY','CONSTR_UNIQUE']:forms+=['ADD_USING_INDEX','BACKING_INDEX_REPLACEMENT','EXTERNAL_FK_DEPENDENCY_CHANGE']
        results.append({'id':'C'+str(i),'source':pointer(SRC+'constraint-v2.json','/constraints/'+str(i)),
            'PHYSICAL_TARGET':physical,'subtype':typ,'forms':forms,'key_columns':keys,
            'external_fk_dependencies':external,'drop_restrict_applicability':drop,'denial_reasons':reason,
            'validate_applicability':validate,'expected_effect_rules':effects,
            'authority':'Exact relation owner and schema/role prerequisites; system catalog protections remain; superuser bootstrap outside sealed only',
            'data_scan_and_existing_rows':'NOT_PROVEN: ADD/VALIDATE/SET NOT NULL need frozen data/lock/inheritance/replica identity preconditions, absent from source-only candidate',
            'exact_generated_dependency_OID_set':'NOT_PROVEN','complete':False})
    save('constraint-applicability-v3.json',{'status':'SOURCE_GROUNDED_PARTIAL',
        'records':results,'source_counts':dict(collections.Counter(c['source']['contype'] for c in cs)),
        'structurally_denied_drop_not_null':sum(r['drop_restrict_applicability']=='STRUCTURALLY_DENIED_UNDER_FROZEN_PK' for r in results),
        'restrict_drop_blocked_by_frozen_fk':sum(r['drop_restrict_applicability']=='RESTRICT_DENIED_WITH_FROZEN_EXTERNAL_FK' for r in results),
        'applicability_proof_sources':[lineptr(PROVIDER+'tablecmds.c','dropconstraint_internal(Relation rel, HeapTuple constraintTup'),
            lineptr(PROVIDER+'tablecmds.c','ATExecDropNotNull(Relation rel, const char *colName, bool recurse,'),
            lineptr(PROVIDER+'tablecmds.c','ATExecValidateConstraint(List **wqueue,'),
            lineptr(PROVIDER+'pg_constraint.c','CreateConstraintEntry(const char *constraintName,')],
        'semantics_not_an_execution_permission':True})
    return results


# Independent physical object resolution; R2 capability IDs never enter this model.
def target(kind,n,row):
    ident=n['id'].split(':',1)[1]
    base={'database':'g3f4'}
    cat={'builtin_function':'pg_proc','function_candidate_signature':'pg_proc','builtin_type':'pg_type',
         'candidate_type_metadata':'pg_type','collation':'pg_collation'}
    if kind in cat:return dict(base,catalog=cat[kind],oid=row['oid'])
    if kind.startswith('catalog_'):return dict(base,catalog=kind[8:],oid=row.get('oid'),aggfnoid=row.get('aggfnoid'))
    if kind=='source_native_function':return dict(base,catalog='pg_proc',signature=ident)
    if kind=='relation':return dict(base,catalog='pg_class',relation=row['name'])
    if kind=='column':return dict(base,catalog='pg_attribute',relation=row['relation'],column=row['name'],attnum=row['attnum'])
    if kind=='constraint':return dict(base,catalog='pg_constraint',relation=row['relation'],name=row['source']['conname'])
    if kind=='index':return dict(base,catalog='pg_index+pg_class',relation=row['relation'],index=row['name'])
    if kind=='trigger':return dict(base,catalog='pg_trigger',relation=row['relation'],name=row['source']['trigname'])
    if kind=='default_expression':return dict(base,catalog='pg_attrdef+pg_attribute',relation=row['relation'],column=row['column'],presence='source expression or expected absence')
    if kind=='role':return dict(base,catalog='pg_authid',name=row['name'])
    if kind=='effective_acl':
        return dict(base,catalog={'column':'pg_attribute.attacl + pg_class.relacl','table':'pg_class.relacl',
            'function':'pg_proc.proacl','type':'pg_type.typacl','schema':'pg_namespace.nspacl','database':'pg_database.datacl'}[row['kind']],
            object=row.get('binding') or row['object'],column=row.get('column'),grantee=row['role'],privilege=row['privilege'])
    if kind=='future_default_acl':
        creator,obj=ident.rsplit(':',1)
        return dict(base,catalog='pg_default_acl',creator=creator,object_kind=obj,
            scope='global plus source-reachable schema entries; additional schemas unresolved')
    if kind in ['generated_composite','generated_array']:
        return dict(base,catalog='pg_type',factory='ROWTYPE_OF' if kind=='generated_composite' else 'ROWARRAY_OF',parent=ident)
    if kind in ['storage_binding','toast_factory']:
        return dict(base,catalog='pg_class+pg_depend+pg_attribute+pg_index',factory='TOAST_OF',parent=ident)
    if kind in ['native_ELF','native_locale','native_module']:return {'host':'owned TEST Linux target','path':row['path'],'expected_sha256':row['sha256']}
    if kind=='database_environment':return dict(base,catalog='pg_database',datname='g3f4')
    if kind=='role_superuser':return dict(base,catalog='pg_authid+pg_database',role='postgres',bootstrap_oid=10,implicit_role='pg_database_owner')
    if kind=='membership_absence':return dict(base,catalog='pg_auth_members',touching_roles=[r['name'] for r in row['roles']],implicit_database_owner_separate=True)
    if kind=='inheritance_absence':return dict(base,catalog='pg_inherits+pg_class.relpartbound',relations=[r['name'] for r in row['relations']])
    if kind=='sequence_absence':return dict(base,catalog='pg_class+pg_sequence+pg_depend+pg_attrdef+pg_attribute',scope='no reachable identity/default_nextval/owned sequence in frozen source',exact_source=pointer(SRC+'sequence-v2.json'))
    if kind=='view_expansion':return dict(base,catalog='pg_rewrite+pg_class',view='pg_catalog.pg_roles')
    if kind=='return_consumer':return dict(base,objects=['public.offline_read_history(uuid,bytea,uuid,text)','public.flyway_schema_history'],catalogs=['pg_proc','pg_attribute'])
    if kind=='expression':return dict(base,source_function=row['SOURCE_LOCATION']['canonical_function'],source_site=row['SITE_ID'],ast_location=row['SOURCE_LOCATION'],resolution_catalogs=['pg_proc','pg_operator','pg_cast','pg_type','pg_namespace','pg_collation'])
    if kind=='expected_release':return {'release_root':pointer(SRC+'expected-currentness-manifest-v6.json'),'component_hash_set':'manifest.components'}
    if kind=='provider_ABI':return {'image_and_provider_bindings':pointer(SRC+'native-provider-identities.json'),'physical_loaded_module_ledger':'NOT_PROVEN'}
    # Rules and labels are not physical journals/handles/session identities.
    return None


def profiles():
    """Distinct operation forms; no equivalence or representative adequacy inferred."""
    m={}
    def put(k,forms,src,anchor):m[k]={'forms':forms.split('|'),'source':lineptr(src,anchor)}
    put('constraint','SUBTYPE_APPLICABILITY_TABLE',PROVIDER+'tablecmds.c','dropconstraint_internal(Relation rel, HeapTuple constraintTup')
    put('relation','CREATE|DROP_RESTRICT|DROP_CASCADE|RENAME|SET_SCHEMA|OWNER_CHANGE|ENABLE_DISABLE_RLS|FORCE_NO_FORCE_RLS|CREATE_ALTER_DROP_POLICY|PERSISTENCE|VIEW_REWRITE|VIEW_SECURITY_INVOKER|CATALOG_WRITE',PROVIDER+'tablecmds.c','ATExecCmd(')
    put('column','ADD|DROP|RENAME|ALTER_TYPE_TYPMOD_COLLATION|SET_DROP_NOT_NULL|SET_DROP_DEFAULT|ADD_SET_DROP_IDENTITY|SET_DROP_GENERATION|COLUMN_GRANT|COLUMN_REVOKE|INHERITANCE|CATALOG_WRITE',PROVIDER+'tablecmds.c','ATExecCmd(')
    put('default_expression','SET_DEFAULT|DROP_DEFAULT|ALTER_COLUMN_TYPE_COERCION|REPLACE_COLUMN|PROVIDER_RESOLUTION_DRIFT|CATALOG_WRITE',PROVIDER+'tablecmds.c','ATExecColumnDefault(')
    put('effective_acl','DIRECT_GRANT|DIRECT_REVOKE|WITH_GRANT_OPTION|REVOKE_GRANT_OPTION_RESTRICT|REVOKE_GRANT_OPTION_CASCADE|PUBLIC_GRANT_REVOKE|OWNER_CHANGE|OWNER_MEMBERSHIP_INHERIT|MEMBERSHIP_SET_ROLE|MEMBERSHIP_ADMIN_OPTION|INDIRECT_MEMBERSHIP_CHAIN|ROLE_SUPERUSER|CREATOR_DEFAULT_THEN_CREATE|SCHEMA_USAGE_CREATE|DATABASE_CONNECT_CREATE|SECURITY_DEFINER_CONTEXT',PROVIDER+'aclchk.c','ExecGrant_common(')
    put('future_default_acl','GLOBAL_GRANT|GLOBAL_REVOKE|SCHEMA_GRANT|SCHEMA_REVOKE|GRANT_OPTION|REVOKE_GRANT_OPTION|CREATOR_IDENTITY|OBJECT_CREATION_ACL_MERGE|OWNER_DEFAULT_PRIVILEGES',PROVIDER+'aclchk.c','SetDefaultACL(InternalDefaultACL *iacls)')
    put('membership_absence','GRANT_MEMBERSHIP|REVOKE_MEMBERSHIP|ADMIN_OPTION|INHERIT_OPTION|SET_OPTION|INDIRECT_CHAIN|ROLE_RECREATE|IMPLICIT_DATABASE_OWNER',PROVIDER+'acl.c','roles_is_member_of(')
    put('role','LOGIN_NOLOGIN|SUPERUSER_NOSUPERUSER|BYPASSRLS_NOBYPASSRLS|INHERIT_NOINHERIT|CREATEROLE_NOCREATEROLE|CREATEDB_NOCREATEDB|REPLICATION_NOREPLICATION|RENAME|DROP_CREATE',PROVIDER+'pg_authid.h','CATALOG(pg_authid')
    put('role_superuser','BOOTSTRAP_SUPERUSER_ATTRIBUTE|LOGIN_NOLOGIN|DATABASE_OWNER_IMPLICIT_ROLE',PROVIDER+'aclchk.c','superuser_arg(roleid)')
    put('database_environment','CREATE_REPLACE_DATABASE|OWNER_CHANGE|COLLATION_VERSION_REFRESH|LOCALE_PROVIDER_REPLACEMENT|ENCODING_REPLACEMENT|CATALOG_WRITE',SRC+'provider/initdb.c','setup_privileges(')
    for k in ['builtin_function','source_native_function','function_candidate_signature']:
        put(k,'CREATE|CREATE_OR_REPLACE_BODY|DROP_RESTRICT|DROP_CASCADE|OWNER_CHANGE|FUNCTION_GRANT|FUNCTION_REVOKE|SECURITY_DEFINER_INVOKER|VOLATILITY|PARALLEL|LEAKPROOF|STRICT|SEARCH_PATH_PROCONFIG|ARGUMENT_DEFAULTS|ARGUMENT_RETURN_TYPE_DROP_CREATE|PROVIDER_MODULE_BINDING|PLANNER_SUPPORT|SCHEMA_RESOLUTION|CATALOG_WRITE',PROVIDER+'pg_proc.h','CATALOG(pg_proc')
    for k in ['builtin_type','candidate_type_metadata','generated_array','generated_composite']:
        put(k,'CREATE|DROP|RENAME|OWNER_CHANGE|TYPE_GRANT_REVOKE|SCHEMA_CHANGE|PROVIDER_IO_BINDING|BASE_ELEMENT_ARRAY_BINDING|DEFAULT|COLLATION|COMPOSITE_ATTRIBUTE_CHANGE|CATALOG_WRITE',PROVIDER+'typecmds.c','DefineType(')
    for k in ['catalog_pg_operator','catalog_pg_cast','catalog_pg_aggregate','catalog_pg_am','catalog_pg_amop','catalog_pg_amproc','catalog_pg_opclass','catalog_pg_opfamily']:
        put(k,'CREATE|DROP_RESTRICT|DROP_CASCADE|REPLACE_PROVIDER_DEPENDENCY|OWNER_OR_SCHEMA_CHANGE_WHERE_SUPPORTED|RESOLUTION_PATH_CHANGE|CATALOG_WRITE',PROVIDER+('parse_oper.c' if k=='catalog_pg_operator' else 'parse_coerce.c'),'oper(' if k=='catalog_pg_operator' else 'find_coercion_pathway(')
    put('index','CREATE|DROP|REINDEX|REPLACE_CONSTRAINT_BACKING_INDEX|ALTER_KEY_OPCLASS_COLLATION|RENAME|PREDICATE_REPLACEMENT|METHOD_REPLACEMENT|CATALOG_WRITE',PROVIDER+'indexcmds.c','DefineIndex(')
    put('trigger','CREATE|CREATE_OR_REPLACE|DROP|ENABLE_DISABLE|RENAME|FUNCTION_PROVIDER_REPLACEMENT|INTERNAL_FK_DEPENDENCY|CATALOG_WRITE',PROVIDER+'ri_triggers.c','RI_FKey_check(')
    put('view_expansion','CREATE_OR_REPLACE_VIEW|DROP_CREATE|OWNER_CHANGE|SECURITY_INVOKER|SECURITY_BARRIER|UNDERLYING_OBJECT_OR_ACL_CHANGE|SCHEMA_RESOLUTION',PROVIDER+'system_views.sql','CREATE VIEW pg_roles')
    put('collation','CREATE|DROP|OWNER_CHANGE|RENAME_SCHEMA|REFRESH_VERSION|LOCALE_PROVIDER_REPLACEMENT|CATALOG_WRITE',PROVIDER+'parse_collate.c','assign_expr_collations(')
    put('expression','BODY_REPLACEMENT|FUNCTION_CANDIDATE_CHANGE|OPERATOR_RESOLUTION|CAST_RESOLUTION|TYPE_METADATA|SEARCH_PATH|COLLATION|SECURITY_CONTEXT|DEFAULT_ARGUMENT_CHANGE',PROVIDER+'parse_func.c','ParseFuncOrColumn(')
    put('inheritance_absence','INHERIT|NO_INHERIT|ATTACH_PARTITION|DETACH_PARTITION|PARTITION_BOUND_REPLACEMENT|CATALOG_WRITE',PROVIDER+'tablecmds.c','ATExecCmd(')
    put('sequence_absence','CREATE_DROP_SEQUENCE|ADD_DROP_IDENTITY|SET_DROP_NEXTVAL_DEFAULT|OWNED_BY_DEPENDENCY|SEQUENCE_GRANT_REVOKE|SEQUENCE_OWNER_CHANGE',PROVIDER+'tablecmds.c','ATExecAddIdentity(')
    for k in ['storage_binding','toast_factory']:
        put(k,'RELATION_REWRITE|TOAST_CREATE_DROP|STORAGE_COMPRESSION_CHANGE|TOAST_INDEX_CHANGE|OWNER_PROPAGATION|PARENT_DEPENDENCY_CHANGE|CATALOG_WRITE',PROVIDER+'toasting.c','NewRelationCreateToastTable(')
    for k in ['native_ELF','native_locale','native_module','provider_ABI','expected_release']:
        put(k,'REPLACE_BYTES|RENAME_SYMLINK_MOUNT_BINDING|OWNER_MODE_CHANGE|DEPENDENCY_LOADER_CHANGE|IMAGE_RELEASE_REPLACEMENT|LOADED_PROVIDER_EPOCH_CHANGE',SRC+'native-provider-identities.json','"custom_module"')
    for k in ['native_participant','native_binding','native_anchor']:
        put(k,'SPAWN_EXIT_RESTART|REPLACE_MODULE|PROCESS_PIDFD_PARENT_CHANGE|FUNCTIONAL_WORK_RESULT|DEPENDENCY_CATALOG_CHANGE|ENROLLMENT_CHANNEL_CHANGE|GENERATION_EPOCH_CHANGE|FRESHNESS_LOSS|GUARD_DECISION_CHANGE',SRC+'native-proof-v6.json','"participants"')
    put('session_environment','AUTHENTICATED_IDENTITY_RECONNECT|SET_RESET_ROLE|SET_RESET_ENCODING|SET_RESET_SEARCH_PATH|SET_RESET_TIMEZONE|SET_RESET_STANDARD_CONFORMING_STRINGS|SET_TRANSACTION_ISOLATION|SESSION_DEFAULT_ROLE_DATABASE_SETTINGS',R2+'consumer-session-contract-v2.json','"continuity"')
    put('audit_binding','APPEND_PREPARED|APPEND_TERMINAL|RECONCILE_UNKNOWN|IDENTITY_CONTEXT_CHANGE|TRUSTED_TIP_CHANGE|LOSS_TRUNCATION|GENERATION_INVALIDATION',SRC+'audit-v6.json','"rules"')
    put('policy_readiness_binding','POLICY_PUBLISH_REVOKE|BINDING_HEADER_REPLACE|LIFECYCLE_TRANSITION|READINESS_GUARD_CHANGE|GENERATION_VECTOR_CHANGE|AUDIT_TIP_BINDING_CHANGE',SRC+'policy-readiness-v3.json','"rules"')
    put('return_consumer','FUNCTION_RETURN_SIGNATURE|PROJECTED_TUPLE_BODY|HISTORY_INSERT|HISTORY_UPDATE|HISTORY_DELETE_TRUNCATE|WRAPPER_EXECUTE_ACL|RAW_HISTORY_ACL|DEPENDENT_TYPE_CHANGE',SRC+'return-consumer-edge.json','"declared_tuple"')
    return m


def mechanism_model():
    cs=js(SRC+'mutation-class-denominator-v3.json')['classes'];graph=js(SRC+'s04-reachability-graph-v3.json');ns={n['id']:n for n in graph['nodes']}
    prof=profiles();assert set(prof)=={c['OBJECT_CLASS'] for c in cs}
    cons=json.loads((OUT/'constraint-applicability-v3.json').read_text())['records']
    records=[];class_rows=[];count=0;nulls=0;h=hashlib.sha256()
    for c in cs:
        kind=c['OBJECT_CLASS'];group=[];c_count=0;c_null=0
        for obj in c['GRAPH_OBJECTS']:
            n=ns[obj];row=resolve(js(SRC+n['component']),n['pointer']);physical=target(kind,n,row)
            if kind=='constraint':
                ci=int(n['pointer'].split('/')[-1]);forms=cons[ci]['forms'];dependency={'constraint_analysis':'constraint-applicability-v3.json#/records/'+str(ci)}
            else:forms=prof[kind]['forms'];dependency={'source_graph_edges':SRC+'s04-reachability-graph-v3.json','source_node':obj,'exact_delta_complete':False}
            group.append({'object_id':obj,'source_pointer':n['component']+'#'+n['pointer'],'physical_target':physical,
                          'forms_override':forms if kind=='constraint' else None})
            for form in forms:
                mid='R3/'+kind+'/'+sha(canon([obj,form]))[:20]
                record={'CLASS_ID':c['CLASS_ID'],'MECHANISM_ID':mid,'SOURCE_POINTER':pointer(SRC+n['component'],n['pointer']),
                    'PHYSICAL_TARGET':physical,'TARGET_KIND':kind,'MUTATION_FORM':form,'DEPENDENCIES':dependency,
                    'PRECONDITIONS':'Exact current identity, source, ownership and data/dependency preconditions; unresolved denies',
                    'AUTHORITY_REQUIRED':'source operation profile; exact actor/credential confinement NOT_PROVEN',
                    'OBSERVED_DELTA':'source fields '+','.join(n['fields'])+'; dependent catalog delta requires separate proof',
                    'OBSERVER_REQUIRED':'independent exact catalog/session/native observer; entitlement NOT_PROVEN',
                    'EQUIVALENCE_GROUP':'NONE','EQUIVALENCE_PROOF_POINTER':'NOT_APPLICABLE_NO_COLLAPSE',
                    'REPRESENTATIVE_ALLOWED':'NO','REPRESENTATIVE_PROOF_POINTER':'NOT_PROVEN','STATIC_STATUS':'NOT_PROVEN'}
                h.update(canon(record)+b'\n');count+=1;c_count+=1
                if physical is None:nulls+=1;c_null+=1
                # Do not write expanded, repetitive records; regenerate from frozen selectors.
        records.append({'class_id':c['CLASS_ID'],'operation_profile':kind,
            'target_selector':pointer(SRC+'mutation-class-denominator-v3.json','/classes/'+str(cs.index(c))+'/GRAPH_OBJECTS'),
            'target_count':len(group),'physical_target_resolver':'derive.py::target (closed source-kind dispatch, no request inputs)',
            'constraint_form_overrides':'constraint-applicability-v3.json#/records' if kind=='constraint' else None})
        class_rows.append({'CLASS_ID':c['CLASS_ID'],'source':pointer(SRC+'mutation-class-denominator-v3.json','/classes/'+str(cs.index(c))),
            'source_objects':len(group),'enumerated_form_obligations':c_count,'unresolved_physical_target_obligations':c_null,
            'fully_partitioned':False,'reason':'Source-indexed operation form coverage is not an exhaustive physical reachability/applicability/authority proof; unresolved prerequisites and fields remain.'})
    save('class-mechanism-partitions-v3.json',{'status':'SOURCE_GROUNDED_PARTIAL','normal_form':{'operation_profiles':prof,'target_groups':records},
        'expansion':'derive.py expand_mechanisms emits records in source class/object/form order; no equivalence, representatives or complete denominator claimed',
        'expanded_record_fields':['CLASS_ID','MECHANISM_ID','SOURCE_POINTER','PHYSICAL_TARGET','TARGET_KIND','MUTATION_FORM','DEPENDENCIES','PRECONDITIONS','AUTHORITY_REQUIRED','OBSERVED_DELTA','OBSERVER_REQUIRED','EQUIVALENCE_GROUP','EQUIVALENCE_PROOF_POINTER','REPRESENTATIVE_ALLOWED','REPRESENTATIVE_PROOF_POINTER','STATIC_STATUS'],
        'classes':class_rows})
    save('mechanism-denominator.json',{'CLASSES_REQUIRED':len(cs),'CLASSES_FULLY_PARTITIONED':0,
        'MECHANISMS_TOTAL':None,'NULL_PHYSICAL_TARGETS':None,'UNJUSTIFIED_REPRESENTATIVE_COLLAPSES':None,'UNCLASSIFIED_MECHANISMS':None,
        'enumerated_form_obligations':count,'enumerated_form_obligations_with_null_target':nulls,
        'expanded_records_sha256':h.hexdigest(),'representative_collapses_performed':0,
        'scope':'Known source-node/operation-form obligations, NOT a complete physical mutation denominator. Forms include inapplicable/conditional operations explicitly denied until proven.',
        'denominator_blockers':['Semantic external audit/policy/native records and actual consumer session lack physical identities',
            'No approved bounded actor/executor universe for closed-epoch bootstrap; source itself admits privileged direct catalog/provider replacement',
            'Complete exact constraint applicability and dependency deltas absent for data/replica-identity/partition/provider conditions',
            'Effective ACL rows do not uniquely identify grantor, direct grant chains, membership closure or owner paths',
            'New candidate schemas/roles/objects change resolution/default/membership observations; no source-approved finite representative equivalence proof'],
        'capability_derivation_allowed':False})


def expand_mechanisms():
    # Export to stdout for audit only. This is data, never SQL or a command API.
    d=json.loads((OUT/'class-mechanism-partitions-v3.json').read_text())
    ns={n['id']:n for n in js(SRC+'s04-reachability-graph-v3.json')['nodes']}
    ca=json.loads((OUT/'constraint-applicability-v3.json').read_text())['records']
    for g in d['normal_form']['target_groups']:
        kind=g['operation_profile'];p=d['normal_form']['operation_profiles'][kind]
        for object_id in resolve(js(g['target_selector']['path']),g['target_selector']['pointer']):
            n=ns[object_id];component=n['component'];ptr=n['pointer'];row=resolve(js(SRC+component),ptr)
            physical=target(kind,n,row);forms=ca[int(ptr.split('/')[-1])]['forms'] if kind=='constraint' else p['forms']
            for form in forms:
                dependency={'constraint_analysis':'constraint-applicability-v3.json#/records/'+ptr.split('/')[-1]} if kind=='constraint' else {'source_graph_edges':SRC+'s04-reachability-graph-v3.json','source_node':object_id,'exact_delta_complete':False}
                yield {'CLASS_ID':g['class_id'],'MECHANISM_ID':'R3/'+kind+'/'+sha(canon([object_id,form]))[:20],
                    'SOURCE_POINTER':pointer(SRC+component,ptr),'PHYSICAL_TARGET':physical,'TARGET_KIND':kind,'MUTATION_FORM':form,'DEPENDENCIES':dependency,
                    'PRECONDITIONS':'Exact current identity, source, ownership and data/dependency preconditions; unresolved denies',
                    'AUTHORITY_REQUIRED':'source operation profile; exact actor/credential confinement NOT_PROVEN',
                    'OBSERVED_DELTA':'source fields '+','.join(n['fields'])+'; dependent catalog delta requires separate proof',
                    'OBSERVER_REQUIRED':'independent exact catalog/session/native observer; entitlement NOT_PROVEN',
                    'EQUIVALENCE_GROUP':'NONE','EQUIVALENCE_PROOF_POINTER':'NOT_APPLICABLE_NO_COLLAPSE',
                    'REPRESENTATIVE_ALLOWED':'NO','REPRESENTATIVE_PROOF_POINTER':'NOT_PROVEN','STATIC_STATUS':'NOT_PROVEN'}


def sql_statements(text):
    """Lexical splitting for source provenance only; not an SQL interpreter."""
    i=0;start=0;quote=None;block=0;line_comment=False
    while i<len(text):
        if line_comment:
            if text[i]=='\n':line_comment=False
            i+=1;continue
        if block:
            if text[i:i+2]=='/*':block+=1;i+=2
            elif text[i:i+2]=='*/':block-=1;i+=2
            else:i+=1
            continue
        if quote:
            if text.startswith(quote,i):
                if len(quote)==1 and text[i:i+2]==quote*2:i+=2;continue
                i+=len(quote);quote=None
            else:i+=1
            continue
        if text[i:i+2]=='--':line_comment=True;i+=2;continue
        if text[i:i+2]=='/*':block=1;i+=2;continue
        if text[i] in ['"',"'"]:quote=text[i];i+=1;continue
        if text[i]=='$':
            match=re.match(r'\$[A-Za-z_0-9]*\$',text[i:])
            if match:quote=match.group();i+=len(quote);continue
        if text[i]==';':
            yield start,i+1,text[start:i+1]
            start=i+1
        i+=1
    assert not quote and not block
    if text[start:].strip():yield start,len(text),text[start:]


def source_provenance():
    text=blob(V043).decode('utf-8-sig');entries=[];constraint_names={};table_names=[]
    for a,b,s in sql_statements(text):
        clean=re.sub(r'/\*.*?\*/|--[^\n]*',' ',s,flags=re.S).strip()
        if re.match(r'(GRANT|REVOKE|ALTER\s+DEFAULT\s+PRIVILEGES)\b',clean,re.I) or re.match(r'ALTER\s+(TABLE|FUNCTION|TYPE|SCHEMA|DATABASE)\b.*\bOWNER\s+TO\b',clean,re.I|re.S):
            first=clean.split()[0].upper();family='DEFAULT_PRIVILEGE' if re.match(r'ALTER\s+DEFAULT',clean,re.I) else 'OWNER_CHANGE' if 'OWNER TO' in clean.upper() else 'DIRECT_ACL_OR_MEMBERSHIP'
            entries.append({'id':'ACL-SOURCE-'+str(len(entries)),'family':family,'operation':first,
                'source':{'path':V043,'git_sha256':file_sha(V043),'start_line':text[:a].count('\n')+1,'end_line':text[:b].count('\n')+1},
                'statement':clean,'statement_sha256':sha(clean.encode()),'runtime_execution':False})
        if re.match(r'CREATE\s+TABLE\b',clean,re.I):
            table=re.search(r'CREATE\s+TABLE\s+([A-Za-z_0-9.]+)',clean,re.I).group(1)
            table_names.append(table)
        for match in re.finditer(r'\bCONSTRAINT\s+([A-Za-z_0-9]+)\s+(PRIMARY\s+KEY|UNIQUE|FOREIGN\s+KEY|CHECK)',clean,re.I):
            # Only DDL CREATE/ALTER statements; ignore constraint words inside function bodies.
            if not re.match(r'(CREATE\s+TABLE|ALTER\s+TABLE)',clean,re.I):continue
            name=match.group(1)
            constraint_names[name]={'path':V043,'git_sha256':file_sha(V043),'line':text[:a].count('\n')+1,
                'subtype':re.sub(r'\s+',' ',match.group(2).upper()),'statement_sha256':sha(clean.encode())}
    expected=js(SRC+'constraint-v2.json')['constraints'];app=[c for c in expected if c['relation'] in js(SRC+'source-ddl-closure.json')['app_relations'] and c['source']['contype']!='CONSTR_NOTNULL']
    matches=[{'constraint':c['source']['conname'],'relation':c['relation'],'source':constraint_names.get(c['source']['conname']),
              'match':c['source']['conname'] in constraint_names} for c in app]
    role_source='scripts/validation/package_0090_active_foundation.py'
    aclsource='scripts/validation/package_0090_reachable_v2_privileges.py'
    save('acl-origin-ledger-v3.json',{'status':'SOURCE_GROUNDED_PARTIAL','canonical_acl_owner_statements':entries,
        'canonical_statement_count':len(entries),'canonical_create_table_count':len(table_names),
        'reachable_named_non_notnull_constraint_provenance':matches,
        'canonical_name_presence_is_not_full_AST_equivalence':True,
        'source_direct_function_grants':js(SRC+'effective-acl-v6.json')['source_function_direct_grants'],
        'security_definer_edges':js(SRC+'effective-acl-v6.json')['security_definer_edges'],
        'effective_row_kinds':dict(collections.Counter(e['kind'] for e in js(SRC+'effective-acl-v6.json')['entries'])),
        'ownership_implicit_privilege_is_not_direct_ACL':True,'equal_effective_booleans_never_coalesced':True,
        'membership_paths':{'expected_explicit_edges':js(SRC+'role-graph-v2.json')['memberships_touching_these_roles'],
            'implicit_database_owner':'g3f4 owner -> pg_database_owner, not an invented pg_auth_members row',
            'transitive_SET_INHERIT_ADMIN_must_be_separate':True,'runtime_actor_reachability':'NOT_PROVEN'},
        'default_privilege_dimensions':['creator','global/schema','object_kind','grantee','privilege','grant_option'],
        'default_scope_source':lineptr(PROVIDER+'aclchk.c','SetDefaultACL(InternalDefaultACL *iacls)'),
        'schema_scoped_defaults_not_supported_for':['SCHEMAS','LARGE OBJECTS'],
        'schema_scoped_default_denial_source':lineptr(PROVIDER+'aclchk.c','cannot use IN SCHEMA clause'),
        'creator_default_source':lineptr(role_source,"for role in ['postgres']"),
        'fixture_function_wrapper_source':lineptr(aclsource,"source_acls['public.offline_read_history']['test_0090_audit']"),
        'no_sequence_rows':'sequence-v2.json states absence; sequence creation/identity/default/owned dependencies/ACL are retained as separate potential mechanisms, never inferred irrelevant',
        'role_connection_limit':'Not in role class frozen FIELDS; not silently added as observed. pg_roles view expansion may observe more fields and therefore remains an unresolved cross-class dependency.',
        'raw_provenance_gaps':['grantor and grant-chain provenance for all effective ACL records','full creator/schema object-creation actor domain',
            'complete indirect membership actor paths','concrete SECURITY DEFINER context mutation actors and dependent entitlement routes'],
        'not_an_exhaustive_mechanism_denominator':True})


def capability_closure():
    d=json.loads((OUT/'mechanism-denominator.json').read_text())
    assert not d['capability_derivation_allowed']
    common={'status':'NOT_DERIVED_DENOMINATOR_INCOMPLETE','required_typed_capabilities':None,
        'derivation_order':'46 classes -> physical mechanisms -> proven equivalence/representatives -> minimal fixed capabilities',
        'reason':'User forbids deriving required capability set before complete physical mechanism denominator; no new executable capability is proposed from the R2 243 row designs.',
        'prior_partial_designs_authorized_as_capabilities':False,'production_carryover':'FORBIDDEN'}
    save('typed-capability-catalog-v3.json',dict(common,capabilities=[],
        empty_list_means='No capabilities derived/authorized in R3; never means zero required capabilities',
        representative_adequacy='NOT_PROVEN',minimality='NOT_PROVEN'))
    for name,key in [('fixed-operation-templates-v3.json','templates'),('capability-principal-bindings-v3.json','bindings'),
                     ('capability-outcome-bindings-v3.json','bindings'),('capability-observer-bindings-v3.json','bindings')]:
        save(name,dict(common,**{key:[]},count=None))
    p='scripts/validation/package_0090_sealed_service.py';q='scripts/validation/package_0090_sealed_boundary.py'
    raw=[{'id':'REJECTED-V1-OWNER-CREDENTIAL','source':lineptr(q,'GRANT flooow_offline_control_owner TO test_0090_broker'),
        'authority':'private control-owner SET membership','why_rejected':'Violates frozen fixture correction decision and exposes owner authority beyond the fixed RLS operation',
        'broker_reachability':lineptr(p,'self.credential = config.pop'), 'R3_adopted':False},
        {'id':'REJECTED-V2-BOOTSTRAP-LABEL','source':pointer(R2+'capability-principal-bindings.json','/bindings/0'),
         'authority':'postgres credential + numeric UID without immutable executor/process/transport confinement','why_rejected':'Exact SQL literal/role label cannot narrow superuser credential', 'R3_adopted':False},
        {'id':'REJECTED-BROAD-CREATEROLE','source':pointer('docs/evidence/package-0090-B01-v2-expanded-capability-mediation/role-admin-special-case.json','/experiments'),
         'authority':'CREATEROLE + target ADMIN OPTION','why_rejected':'Prior experiment created an outside-target role. No new execution or broad role-admin principal is authorized.', 'R3_adopted':False}]
    fields=['request','dispatcher','capability','executor','credential','principal','target','operation','outcome','observer','audit_receipt','revocation']
    save('executor-confinement-v3.json',{'status':'NOT_PROVEN','authority_path_required':fields,
        'requirements':{'request':'Exact tagged operation ID and contract digest only; reject unknown/extra fields before dispatch',
            'dispatcher':'Read-only allowlist binds operation ID to a single installed worker artifact + exact fixed transport',
            'executor':'Immutable entrypoint and dependency closure; no generic interpreter/psql/shell/identifier/SQL API, no writable import/loader path; no second credential channel',
            'credential':'One operation and closed epoch only; no broker custody, inherited descriptor, environment disclosure or steady-state superuser connection',
            'observer':'Separate anchored principal and read entitlement; worker cannot forge outcome/audit/extinction evidence',
            'revocation':'Destroy capability/credential/session/process/descendants before reseal; old tuple never revived'},
        'frozen_implementation_satisfying_all_requirements':None,'rejected_raw_candidate_paths':raw,
        'RAW_AUTHORITY_SURFACES':None,'known_rejected_raw_candidate_paths':len(raw),
        'known_rejected_paths_are_not_a_complete_denominator':True,
        'no_broker_arbitrary_superuser_invocation_can_be_hidden_as_trust_boundary':True,
        'no_new_worker_code_installed_or_authored':True})


def epoch_model():
    # Authored independently, then compare R2 state labels, not its safety claims.
    states=['SEALED','UNSEAL_REQUESTED','UNSEALED','CAPABILITY_ACTIVATING','ACTIVE','MUTATION_IN_FLIGHT',
        'MUTATION_COMMITTED','MUTATION_UNKNOWN','RECONCILING','CAPABILITY_REVOKING','WORKER_EXTINCTION_PENDING','RESEAL_PENDING','SEALED_NEW_EPOCH','BLOCKED']
    guards=['old_capability_revoked','old_worker_extinct','mutation_outcome_known','audit_durable','generation_advanced','new_expected_state_bound','new_observer_contract_bound']
    edges=[('SEALED','UNSEAL_REQUESTED'),('UNSEAL_REQUESTED','UNSEALED'),('UNSEALED','CAPABILITY_ACTIVATING'),
        ('CAPABILITY_ACTIVATING','ACTIVE'),('ACTIVE','MUTATION_IN_FLIGHT'),('MUTATION_IN_FLIGHT','MUTATION_COMMITTED'),
        ('MUTATION_IN_FLIGHT','MUTATION_UNKNOWN'),('MUTATION_UNKNOWN','RECONCILING'),('RECONCILING','MUTATION_COMMITTED'),
        ('RECONCILING','CAPABILITY_REVOKING'),('MUTATION_COMMITTED','CAPABILITY_REVOKING'),('CAPABILITY_REVOKING','WORKER_EXTINCTION_PENDING'),
        ('WORKER_EXTINCTION_PENDING','RESEAL_PENDING'),('RESEAL_PENDING','SEALED_NEW_EPOCH'),('SEALED_NEW_EPOCH','UNSEAL_REQUESTED'),('BLOCKED','RECONCILING')]
    edges += [(s,'BLOCKED') for s in states if s!='BLOCKED']
    transitions=[]
    for i,(a,b) in enumerate(edges):
        req=guards[:] if b=='SEALED_NEW_EPOCH' else ['exact_epoch_generation_revision','exclusive_lease','durable_transition_audit']
        if b=='UNSEALED':req+=['all_old_eligibility_endpoints_deny','old_consumers_drained']
        if b=='ACTIVE':req+=['exact_worker_artifact_and_anchor','credential_operation_confinement']
        if b=='MUTATION_COMMITTED':req+=['independent_commit_outcome','exact_poststate_and_dependency_delta']
        if a=='RECONCILING' and b=='CAPABILITY_REVOKING':req+=['independently_known_no_commit','exact_prestate']
        if b=='WORKER_EXTINCTION_PENDING':req+=['all_capability_handles_credentials_backend_sessions_revoked']
        if b=='RESEAL_PENDING':req+=['independent_descendant_backend_descriptor_extinction','no_pending_prepared_transactions','mutation_outcome_known']
        if b=='BLOCKED':req=['any_failure_missing_unknown_stale_or_conflicting_evidence']
        transitions.append({'id':'R3/T/'+str(i),'from':a,'to':b,'required_known_true':req,
            'authority':'Independent verifier + coordinator CAS; bootstrap only where exact unsealed operation requires it',
            'audit_event':'R3_'+a+'_TO_'+b,'physical_authority_binding':'NOT_PROVEN',
            'epoch_generation':'New unique epoch/monotonic generation reserved durably before activation; no reuse or rollback',
            'currentness':'Deny during transition/UNKNOWN/BLOCKED; reseal is TEST contract state only, never READY',
            'recovery':'Last independently durable revision; unknown SQL outcome retained and reconciled; worker death never implies abort'})
    model={'status':'DESIGNED_ABSTRACT_ONLY','states':states,'transitions':transitions,'reseal_invariants':guards,
        'impossible_transitions':[[a,b] for a in states for b in states if (a,b) not in edges],
        'R2_state_labels_independently_reproduced':set(states)==set(js(R2+'closed-epoch-state-machine.json')['states']),
        'all_guards_require_independently_known_true':True,'runtime_authority':False}
    save('closed-epoch-state-machine-v3.json',model)
    p='scripts/validation/package_0090_sealed_service.py'
    specs=[
        ('V1/BROKER_PROCESS','Broker.__init__','broker Python process uid10001','Broker(config)',None),
        ('V1/BROKER_SQL_CREDENTIAL','self.credential = config.pop','broker-held SQL credential','self.credential',None),
        ('V1/DB_WORKER_PROCESS','def db_worker():','fixed Python db_worker child','worker = subprocess.Popen',None),
        ('V1/DB_WORKER_STDIN_PIPE',"request = json.loads(sys.stdin.readline())",'worker stdin pipe carrying credential/host/enable/fault','worker.stdin.write',None),
        ('V1/PSQL_CHILD_AND_BACKEND',"p = subprocess.Popen(['psql'",'worker psql child and SQL backend session','p.wait(timeout=15)',None),
        ('V1/WORKER_XID',"SELECT pg_current_xact_id()",'SQL transaction identity printed by worker','self.pending',None),
        ('V1/WORKER_PERMIT_PIPE',"!= 'PERMIT'",'worker permit on stdin','PERMIT',None),
        ('V1/READ_OBSERVER_SQL_SESSION','def query(self, sql):','broker query session uses same SQL credential','db(sql, self.credential',None),
        ('V1/OUTCOME_READ_SQL_SESSION','SELECT pg_xact_status','broker transaction-outcome query shares mutation credential','self.query',None),
        ('V1/NATIVE_TOKEN','self.token = config','native HMAC token','hmac.compare_digest',None),
        ('V1/NATIVE_REPLACE_HTTP','def native(self, message):','broker-to-native HTTP POST with HMAC','urllib.request.urlopen',None),
        ('V1/NATIVE_PROCESS','class Native:','native Python delegate uid10002','Native(config)',None),
        ('V1/NATIVE_PARTICIPANT_CHILD','self.child = subprocess.Popen','single historical TEST participant child','self.child.wait(timeout=5)',None),
        ('V1/NATIVE_CHILD_STDIN','def ask_child(self, message):','native child stdin/stdout pipes','self.child.stdout.readline',None),
        ('V1/BOOTSTRAP_FIFO',"fifo = Path('/private/inbox')",'exact bootstrap FIFO /private/inbox','fifo.unlink()',None),
        ('V1/BROKER_HTTP_REQUEST','class Handler(BaseHTTPRequestHandler):','POST / on broker HTTPServer :8080','self.rfile.read',None),
        ('V1/EPOCH_FILE',"self.write_file('epoch'",'private /state/epoch file','/state/epoch',None),
        ('V1/GENERATION_FILE',"self.write_file('generation'",'private /state/generation file','/state/generation',None),
        ('V1/AUDIT_JOURNAL',"(STATE / 'journal').open('ab')",'private /state/journal written by same broker','os.fsync',None),
        ('V1/PENDING_RESERVATION','self.records = []; self.pending = None','in-memory pending operation + journal copy','self.pending',None),
        ('V1/TUPLE_VALIDATION',"request['op'] == 'validate_tuple'",'broker validate_tuple request endpoint','snapshot',None),
    ]
    endpoints=[]
    for eid,anchor,identity,revoke,_ in specs:
        if eid=='V1/BROKER_PROCESS':anchor='class Broker:'
        endpoints.append({'ENDPOINT_ID':eid,'SOURCE_POINTER':lineptr(p,anchor),'PHYSICAL_SOURCE_IDENTITY':identity,
            'CREATION_AUTHORITY':'Existing V1 TEST bootstrap/parent process only; not approved as R3 worker authority',
            'ACTIVE_STATES':'Historical V1 lifecycle; mapping to R3 states NOT_PROVEN',
            'REVOCATION_ACTION':revoke,'REVOCATION_AUTHORITY':'NOT_PROVEN_FOR_R3',
            'REVOCATION_RECEIPT':None,'EXTINCTION_OBSERVER':None,'EXTINCTION_RECEIPT':None,
            'UNKNOWN_BEHAVIOR':'Retain durable operation tuple; evidence missing/contradictory -> deny and reconcile',
            'REPLAY_BEHAVIOR':'No new activation from old tuple; exact terminal receipt only; conflicting digest deny',
            'RESEAL_REQUIREMENT':'Independent complete revocation/extinction receipt required; historical candidate cannot satisfy by label',
            'FULLY_BOUND':False,'ADOPTED_FOR_R3':False})
    save('endpoint-inventory-v3.json',{'status':'SOURCE_GROUNDED_PARTIAL','endpoints':endpoints,
        'known_exact_source_endpoints':len(endpoints),'ENDPOINTS_TOTAL':None,'ENDPOINTS_FULLY_BOUND':0,'UNBOUND_ENDPOINTS':None,
        'known_source_endpoints_unbound':len(endpoints),'scope':'Concrete V1 source endpoints, not an exhaustive R3 transition inventory',
        'additional_endpoint_gaps':['separate privileged transition worker credential transport/OS sandbox','independent audit writer/outcome reader',
            'exact actual final consumer session/PID/start identity','native 7 participant handle/observer/generation registry','worker descendant descriptors/sockets/prepared xacts',
            'durable cross-crash reservation authority and lease/CAS ownership']})
    identities={key:{'identity_kind':key,
        'binding_rule':'sha256(canonical(domain=FLOOOW/B01V2/R3, identity_kind='+key+', frozen_authorization, epoch, generation, operation_id, capability_digest, target_digest, precondition_digest, kind_specific_fields))',
        'kind_specific_fields':{'reservation':['lease_revision'], 'operation':['reservation_digest'],
            'transaction_outcome':['operation_digest','database_identity','full_transaction_identity','known_outcome'],
            'audit':['operation_digest','previous_tip','outcome_receipt_digest','writer_identity'],
            'epoch':['previous_epoch_tombstone','authority_revision'], 'generation':['slot','prior_generation_tombstone'],
            'capability':['mechanism_set_digest','executor_digest','revocation_policy_digest'],
            'target':['database_deployment_identity','exact_object_selector','source_digest'],
            'observer_decision':['operation_digest','observer_identity','observed_revision','decision','outcome_receipt_digest']}[key],
        'physical_storage_or_anchor':None,'creation_authority':None,'status':'DESIGNED_NOT_PHYSICALLY_BOUND'} for key in
        ['reservation','operation','transaction_outcome','audit','epoch','generation','capability','target','observer_decision']}
    save('closed-epoch-physical-bindings-v3.json',{'status':'NOT_PROVEN','durable_identities':identities,
        'endpoint_inventory':'endpoint-inventory-v3.json','RESEAL_INVARIANTS_TOTAL':len(guards),
        'RESEAL_INVARIANTS_PHYSICALLY_BOUND':0,'invariants':[{'id':g,'exact_attestor':None,'exact_receipt':None,'binding':'NOT_PROVEN'} for g in guards],
        'ROLE_ADMIN_CLOSED_EPOCH_CONTRACT_COMPLETE':'NOT_PROVEN','bootstrap_containment':'executor-confinement-v3.json',
        'macro_state_mapping':{'SEALED_OLD':['SEALED'],'OPENING':['UNSEAL_REQUESTED','UNSEALED','CAPABILITY_ACTIVATING'],
            'ACTIVE':['ACTIVE','MUTATION_IN_FLIGHT','MUTATION_COMMITTED'],'DRAINING':['CAPABILITY_REVOKING','WORKER_EXTINCTION_PENDING'],
            'OUTCOME_RECONCILIATION':['MUTATION_UNKNOWN','RECONCILING'],'RESEAL_PENDING':['RESEAL_PENDING'],'SEALED_NEW_EPOCH':['SEALED_NEW_EPOCH']}})
    save('unknown-outcome-contract-v3.json',{'status':'DESIGNED_NOT_PHYSICALLY_BOUND',
        'UNKNOWN_OUTCOME_PATHS_TOTAL':None,'UNKNOWN_OUTCOME_PATHS_BOUND':0,
        'abstract_crash_cuts':[{'state':s,'before_durable_effect':'BLOCKED until durable lineage and no-start/no-commit independently established',
            'after_effect_before_ACK':'MUTATION_UNKNOWN; retain reservation, independently reconcile exact transaction/state/audit; no blind replay'} for s in states],
        'reservation':'Durable unique tuple before authority delivery; cannot reserve a second operation to escape unresolved outcome',
        'replay':'Same tuple and exact digest returns retained terminal receipt without execution. Same identity/different digest conflicts. Unknown never retries blindly.',
        'commit_unknown':'Independent SQL outcome + expected data/catalog/dependency delta + durable independent audit; timeout, missing row, process death and ACK loss never imply rollback',
        'reconnect':'Discard connection-local handles only; retain durable pending tuple; reconcile before new epoch enrollment; never adopt helper connection',
        'revocation_unknown':'Partial revocation/extinction cannot reseal; preserve tombstones and deny old/new eligibility',
        'unknown_receipt':'Versioned immutable PENDING with exact tuple, reason, last durable revision and independent reconciliation identity; physical writer authority NOT_PROVEN',
        'direct_UNKNOWN_reseal':False,'state_model':'closed-epoch-state-machine-v3.json'})


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('phase',choices=['freeze','mechanisms','contracts','expand']);args=ap.parse_args()
    if args.phase=='freeze':freeze()
    elif args.phase=='mechanisms':constraint_analysis();mechanism_model()
    elif args.phase=='contracts':source_provenance();capability_closure();epoch_model()
    else:
        for row in expand_mechanisms():print(canon(row).decode())
