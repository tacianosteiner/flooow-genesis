"""TEST_ONLY broad tuple observer and controlled observation-to-decision races.

Observed tuples are NEVER used as independent expected eligibility values.
No readiness, policy activation, binding registration or S04 invocation.
"""
import json
import sys
import time
from pathlib import Path
import package_0090_source_closure as q

BASELINE = 'e98fccc4f21b937e7fd2841cf533c89f9a935500'
OUT = q.ROOT / 'docs/evidence/package-0090-complete-currentness-concurrent-100us'
CATALOGS = {
    'database': "SELECT oid,datname,datdba,encoding,datlocprovider,datistemplate,datallowconn,datconnlimit,datcollate,datctype,datlocale,datcollversion,datacl FROM pg_database WHERE datname=current_database()",
    'schemas': "SELECT oid,nspname,nspowner,nspacl FROM pg_namespace WHERE nspname NOT LIKE 'pg_temp_%' AND nspname NOT LIKE 'pg_toast_temp_%'",
    'roles': "SELECT oid,rolname,rolsuper,rolinherit,rolcreaterole,rolcreatedb,rolcanlogin,rolreplication,rolbypassrls,rolconnlimit,rolvaliduntil,rolconfig FROM pg_roles",
    'memberships': 'SELECT roleid,member,grantor,admin_option,inherit_option,set_option FROM pg_auth_members',
    'functions': 'SELECT oid,proname,pronamespace,proowner,prolang,procost,prorows,provariadic,prosupport,prokind,prosecdef,proleakproof,proisstrict,proretset,provolatile,proparallel,pronargs,pronargdefaults,prorettype,proargtypes,proallargtypes,proargmodes,proargnames,proargdefaults,protrftypes,prosrc,probin,prosqlbody,proconfig,proacl FROM pg_proc',
    'relations': "SELECT oid,relname,relnamespace,reltype,reloftype,relowner,relam,reltablespace,reltoastrelid,relhasindex,relisshared,relpersistence,relkind,relnatts,relchecks,relhasrules,relhastriggers,relhassubclass,relrowsecurity,relforcerowsecurity,relispartition,relrewrite,relacl,reloptions,relpartbound FROM pg_class WHERE relnamespace IN (SELECT oid FROM pg_namespace WHERE nspname IN ('public','offline_crypto'))",
    'columns': "SELECT attrelid,attname,atttypid,attstattarget,attlen,attnum,attndims,atttypmod,attbyval,attalign,attstorage,attcompression,attnotnull,atthasdef,atthasmissing,attidentity,attgenerated,attisdropped,attislocal,attinhcount,attcollation,attacl,attoptions,attfdwoptions,attmissingval FROM pg_attribute WHERE attrelid IN (SELECT oid FROM pg_class WHERE relnamespace IN (SELECT oid FROM pg_namespace WHERE nspname IN ('public','offline_crypto')))",
    'constraints': 'SELECT * FROM pg_constraint',
    'triggers': 'SELECT * FROM pg_trigger',
    'defaults': 'SELECT * FROM pg_attrdef',
    'default_ACLs': 'SELECT * FROM pg_default_acl',
    'RLS_policies': 'SELECT * FROM pg_policy',
    'view_rules': 'SELECT * FROM pg_rewrite',
    'indexes': 'SELECT * FROM pg_index',
    'inheritance': 'SELECT * FROM pg_inherits',
    'types': 'SELECT * FROM pg_type',
    'casts': 'SELECT * FROM pg_cast',
    'operators': 'SELECT * FROM pg_operator',
    'languages': 'SELECT * FROM pg_language',
    'extensions': 'SELECT * FROM pg_extension',
    'dependencies': 'SELECT * FROM pg_depend',
    'shared_dependencies': 'SELECT * FROM pg_shdepend',
    'database_role_settings': 'SELECT * FROM pg_db_role_setting',
    'collations': 'SELECT * FROM pg_collation',
    'history': 'SELECT installed_rank,version,type,script,checksum,success FROM public.flyway_schema_history',
    'policy': 'SELECT * FROM public.offline_deadline_policy',
    'readiness': 'SELECT * FROM public.offline_readiness',
    'header': 'SELECT * FROM public.offline_binding_header',
    'original': 'SELECT * FROM public.offline_expected_signed_attestation',
    'lifecycle': 'SELECT * FROM public.offline_binding_lifecycle',
}
ACL_DEFAULTS={'database':('datacl',"acldefault('d',t.datdba)"),'schemas':('nspacl',"acldefault('n',t.nspowner)"),'functions':('proacl',"acldefault('f',t.proowner)"),'relations':('relacl',"CASE WHEN t.relkind='S' THEN acldefault('s',t.relowner) WHEN t.relkind IN ('r','v','m','f','p') THEN acldefault('r',t.relowner) ELSE NULL::aclitem[] END"),'columns':('attacl',"ARRAY[]::aclitem[]"),'types':('typacl',"acldefault('T',t.typowner)")}
def projection(name):
    if name not in ACL_DEFAULTS: return 'to_jsonb(t)'
    column,default=ACL_DEFAULTS[name]
    return "to_jsonb(t)||jsonb_build_object('%s',coalesce(to_jsonb(t.%s),to_jsonb(%s)))"%(column,column,default)
QUERY = 'SELECT jsonb_build_object(' + ','.join("'%s',(SELECT coalesce(jsonb_agg(%s ORDER BY (%s)::text),'[]'::jsonb) FROM (%s) t)" % (name,projection(name),projection(name),sql) for name, sql in CATALOGS.items()) + ')'


def canonical(value): return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
def digest(value): return q.sha(canonical(value))


def qualify(sql, run, container, folder, record, fixture, runtime_work):
    sys.path.insert(0, str(Path.home() / 'AppData/Local/Temp/flooow-0090-authorized-psycopg'))
    import psycopg
    d = json.loads(run(['docker','inspect',container]))[0]
    q.require(d['Image'] == q.IMAGE and d['Config']['Labels']['com.docker.compose.project'] == record['isolation']['project'], 'Foreign target')
    port = d['NetworkSettings']['Ports']['5432/tcp']
    q.require(len(port) == 1 and port[0]['HostIp'] == '127.0.0.1', 'Nonloopback target')
    kwargs = dict(host='127.0.0.1', port=int(port[0]['HostPort']), dbname='g3f4', user='postgres', password=(Path(runtime_work)/'postgres-password').read_text(), autocommit=True)
    cases=[]; mutations=[]; races=[]; measurements=[]
    def case(name, passed, details, group):
        row=dict(name=name,passed=bool(passed),details=details,group=group)
        cases.append(row); record['cases'].append(row); q.require(passed, name)
    with psycopg.connect(**kwargs) as observer, psycopg.connect(**kwargs) as writer:
        def observe():
            start=time.perf_counter_ns(); value=observer.execute(QUERY).fetchone()[0]
            measurements.append(time.perf_counter_ns()-start); return value
        initial=observe()
        (folder/'observed-currentness-manifest.json').write_text(json.dumps(dict(scope='OBSERVED_ONLY_NOT_EXPECTED', tuples=initial,sha256=digest(initial),query=QUERY,query_sha256=q.sha(QUERY.encode()),database_target=record['isolation']),indent=2)+'\n')
        def mutate(name, change, undo, prepare=None, finish=None):
            if prepare: writer.execute(prepare)
            before=observe(); writer.execute(change)
            try:
                after=observe(); changed=[k for k in before if before[k]!=after[k]]
                case(name, digest(before)!=digest(after) and bool(changed), changed, 'MUTATION_DETECTION')
                mutations.append(dict(name=name,sql=change,changed_classes=changed,before_digest=digest(before),after_digest=digest(after),detected=True))
            finally: writer.execute(undo)
            case(name+'_restored', digest(before)==digest(observe()), 'Normalized observation restored; not an expected-validity assertion', 'CURRENTNESS')
            if finish: writer.execute(finish)
        mutate('history_write_GRANT', 'GRANT UPDATE ON public.flyway_schema_history TO test_0090_audit','REVOKE UPDATE ON public.flyway_schema_history FROM test_0090_audit')
        mutate('history_write_REVOKE','REVOKE UPDATE ON public.flyway_schema_history FROM test_0090_audit','GRANT UPDATE ON public.flyway_schema_history TO test_0090_audit',prepare='GRANT UPDATE ON public.flyway_schema_history TO test_0090_audit',finish='REVOKE UPDATE ON public.flyway_schema_history FROM test_0090_audit')
        mutate('table_SELECT','GRANT SELECT ON public.flyway_schema_history TO test_0090_audit','REVOKE SELECT ON public.flyway_schema_history FROM test_0090_audit')
        mutate('column_grant_option','GRANT SELECT(checksum) ON public.flyway_schema_history TO test_0090_audit WITH GRANT OPTION','REVOKE SELECT(checksum) ON public.flyway_schema_history FROM test_0090_audit')
        mutate('function_EXECUTE','REVOKE EXECUTE ON FUNCTION public.offline_read_history(uuid,bytea,uuid,text) FROM test_0090_audit','GRANT EXECUTE ON FUNCTION public.offline_read_history(uuid,bytea,uuid,text) TO test_0090_audit')
        mutate('function_owner','ALTER FUNCTION public.offline_read_history(uuid,bytea,uuid,text) OWNER TO postgres','ALTER FUNCTION public.offline_read_history(uuid,bytea,uuid,text) OWNER TO flooow_offline_audit_owner')
        owner=writer.execute("SELECT pg_get_userbyid(relowner) FROM pg_class WHERE oid='public.flyway_schema_history'::regclass").fetchone()[0]
        q.require(owner=='postgres', 'Unexpected bootstrap history owner')
        mutate('table_owner','ALTER TABLE public.flyway_schema_history OWNER TO flooow_offline_control_owner','ALTER TABLE public.flyway_schema_history OWNER TO postgres')
        schema_owner=writer.execute("SELECT pg_get_userbyid(nspowner) FROM pg_namespace WHERE nspname='offline_crypto'").fetchone()[0]
        q.require(schema_owner=='postgres', 'Unexpected bootstrap crypto owner')
        mutate('schema_owner','ALTER SCHEMA offline_crypto OWNER TO flooow_offline_control_owner','ALTER SCHEMA offline_crypto OWNER TO postgres')
        mutate('membership_add','GRANT flooow_offline_control_owner TO test_0090_audit WITH ADMIN OPTION','REVOKE flooow_offline_control_owner FROM test_0090_audit')
        # Membership OIDs are deliberately not semantic tuple keys. Grantor/options are.
        mutate('membership_remove','REVOKE flooow_offline_control_owner FROM test_0090_audit','GRANT flooow_offline_control_owner TO test_0090_audit',prepare='GRANT flooow_offline_control_owner TO test_0090_audit',finish='REVOKE flooow_offline_control_owner FROM test_0090_audit')
        mutate('role_attribute','ALTER ROLE test_0090_audit INHERIT','ALTER ROLE test_0090_audit NOINHERIT')
        before=observe(); writer.execute('BEGIN')
        try:
            writer.execute("ALTER ROLE test_0090_audit VALID UNTIL '2000-01-01 UTC'")
            changed=writer.execute(QUERY).fetchone()[0]
            case('role_valid_until_transactional',before['roles']!=changed['roles'],'Real SQL mutation visible in writer transaction; rolled back to preserve original NULL','MUTATION_DETECTION')
            mutations.append(dict(name='role_valid_until_transactional',changed_classes=['roles'],detected=True,committed=False))
        finally: writer.execute('ROLLBACK')
        case('role_valid_until_restored',digest(before)==digest(observe()),'Exact rollback restoration','CURRENTNESS')
        mutate('function_search_path',"ALTER FUNCTION public.offline_read_history(uuid,bytea,uuid,text) SET search_path=public",'ALTER FUNCTION public.offline_read_history(uuid,bytea,uuid,text) SET search_path=pg_catalog,pg_temp')
        mutate('function_security','ALTER FUNCTION public.offline_read_history(uuid,bytea,uuid,text) SECURITY INVOKER','ALTER FUNCTION public.offline_read_history(uuid,bytea,uuid,text) SECURITY DEFINER')
        mutate('schema_CREATE','GRANT CREATE ON SCHEMA offline_crypto TO test_0090_audit','REVOKE CREATE ON SCHEMA offline_crypto FROM test_0090_audit')
        mutate('database_CONNECT','REVOKE CONNECT ON DATABASE g3f4 FROM PUBLIC','GRANT CONNECT ON DATABASE g3f4 TO PUBLIC')
        mutate('trigger_disable','ALTER TABLE public.offline_binding_header DISABLE TRIGGER USER','ALTER TABLE public.offline_binding_header ENABLE TRIGGER USER')
        mutate('constraint_change','ALTER TABLE public.flyway_schema_history ADD CONSTRAINT test_only_0090_checksum CHECK(checksum IS NULL OR checksum<>-2147483648) NOT VALID','ALTER TABLE public.flyway_schema_history DROP CONSTRAINT test_only_0090_checksum')
        checksum=writer.execute('SELECT checksum FROM public.flyway_schema_history WHERE installed_rank=1').fetchone()[0]
        mutate('history_data','UPDATE public.flyway_schema_history SET checksum=checksum+1 WHERE installed_rank=1',f'UPDATE public.flyway_schema_history SET checksum={checksum} WHERE installed_rank=1')
        # Never INSERT policy or readiness. BEFORE/AFTER divergence is evaluated on
        # observation copies; live authority/state validation stays explicitly unproven.
        copied=json.loads(json.dumps(initial)); copied['readiness']=[{'state':'TEST_ONLY_TAMPER_NOT_READY'}]
        case('observation_copy_readiness_divergence',digest(copied)!=digest(initial),'COPY_ONLY; no SQL READY row, not live readiness proof','CURRENTNESS')
        copied=json.loads(json.dumps(initial)); copied['policy']=[{'policy_digest':'TEST_ONLY_WRONG'}]
        case('observation_copy_policy_divergence',digest(copied)!=digest(initial),'COPY_ONLY; no activation, not live policy proof','CURRENTNESS')
        # Controlled committed-before-decision interleavings, not a performance race.
        for phase in ['before_first_observation','during_work','during_guard','before_final_observation','after_final_observation_before_T10','after_T10']:
            before=observe(); final=before
            if phase=='before_first_observation':
                writer.execute('ALTER ROLE test_0090_audit INHERIT'); final=observe()
            elif phase in ['during_work','during_guard','before_final_observation']:
                writer.execute('ALTER ROLE test_0090_audit INHERIT'); final=observe()
            elif phase=='after_final_observation_before_T10':
                final=observe(); writer.execute('ALTER ROLE test_0090_audit INHERIT')
            # A decision using a retained observation without invalidation is unsafe.
            decision_accepts_retained = digest(final)==digest(before)
            decision=time.perf_counter_ns()
            if phase=='after_T10': writer.execute('ALTER ROLE test_0090_audit INHERIT')
            actual=observe(); invalid_now=digest(actual)!=digest(before)
            expected_deny=(phase!='after_T10')
            safe=(not decision_accepts_retained) if expected_deny else decision_accepts_retained
            case('race_characterization_'+phase, invalid_now and (safe if phase!='after_final_observation_before_T10' else not safe),'Counterexample characterization; unsafe case is NOT a T10 gate pass','TOCTOU_CHARACTERIZATION')
            races.append(dict(phase=phase,mutation_committed_before_T10=expected_deny,retained_observation_accepts=decision_accepts_retained,required_deny=expected_deny,meets_required_boundary=safe,decision_host_perf_counter_ns=decision,native_T10_implemented=False))
            writer.execute('ALTER ROLE test_0090_audit NOINHERIT')
        observer.execute('BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY'); before=observe()
        writer.execute(f'UPDATE public.flyway_schema_history SET checksum={checksum}+1 WHERE installed_rank=1')
        try:
            retained=observe(); writer_current=writer.execute('SELECT checksum FROM public.flyway_schema_history WHERE installed_rank=1').fetchone()[0]
            case('RR_is_not_currentness',retained['history']==before['history'] and writer_current==checksum+1,'One retained data snapshot is stale after committed writer update','CURRENTNESS')
        finally:
            observer.execute('ROLLBACK'); writer.execute(f'UPDATE public.flyway_schema_history SET checksum={checksum} WHERE installed_rank=1')
        # Real protection experiment: SHARE blocks DML; advisory does not bind ADMIN.
        observer.execute('BEGIN'); observer.execute('LOCK TABLE public.flyway_schema_history IN SHARE MODE'); writer.execute("SET lock_timeout='50ms'")
        blocked=False
        try: writer.execute('UPDATE public.flyway_schema_history SET checksum=checksum WHERE installed_rank=1')
        except psycopg.errors.LockNotAvailable: blocked=True
        case('SHARE_blocks_history_DML',blocked,'Actual 55P03','CURRENTNESS')
        writer.execute('ALTER ROLE test_0090_audit INHERIT'); writer.execute('ALTER ROLE test_0090_audit NOINHERIT'); observer.execute('ROLLBACK')
        case('SHARE_does_not_block_role_admin',True,'Actual ALTER ROLE completed while history locked','CURRENTNESS')
        observer.execute('SELECT pg_advisory_lock(9000090)'); writer.execute('ALTER ROLE test_0090_audit INHERIT'); writer.execute('ALTER ROLE test_0090_audit NOINHERIT'); observer.execute('SELECT pg_advisory_unlock(9000090)')
        case('advisory_lock_not_admin_fence',True,'Actual ADMIN ALTER ROLE ignores advisory lock','CURRENTNESS')
        # Inspect service powers independently; denial tests exercise direct LOGIN paths.
        for role in ['verification','issuance','execution','audit']:
            denied=sql('ALTER ROLE test_0090_audit INHERIT;',role='test_0090_'+role,check=False)
            case('operational_role_cannot_ALTER_ROLE_'+role,denied.returncode!=0 and '42501' in denied.stderr.decode(),'Direct SESSION_USER; no SET ROLE','CURRENTNESS')
        final=observe()
        differences=[k for k in initial if initial[k]!=final[k]]
        case('all_catalog_mutations_restored',not differences,differences,'CURRENTNESS')
        case('no_eligibility_material',not final['readiness'] and not final['header'] and not final['original'] and not final['policy'],'No READY/policy/binding material created','CURRENTNESS')
        (folder/'runtime-results.json').write_text(json.dumps(dict(cases=cases,mutations=mutations,races=races,observation_query=QUERY,observation_measurements_ns=measurements,final_changed_classes=differences,full_currentness_gate_pass=False,live_policy_readiness_mutation_proven=False,native_currentness_proven=False),indent=2)+'\n')
