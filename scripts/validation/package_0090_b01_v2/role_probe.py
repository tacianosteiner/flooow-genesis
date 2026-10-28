"""Unsealed disposable PG18 minimum-capability experiments, not V2 qualification."""
import json
from pathlib import Path
import sys
import types
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import package_0090_source_closure as q
import package_0090_active_foundation as foundation
from design import OUT,save


def qualify(sql,run,container,folder,record,fixture,runtime_work):
    cases=[]
    def case(name,passed,details):
        row=dict(name=name,passed=bool(passed),details=details);cases.append(row)
        (folder/'role-experiments.json').write_text(json.dumps(dict(scope='UNSEALED_OWNED_DISPOSABLE_MINIMUM_CAPABILITY_EXPERIMENT',cases=cases),indent=2)+'\n')
        q.require(passed,name)
    sql('CREATE ROLE test_v2_role_admin LOGIN NOINHERIT NOSUPERUSER NOCREATEDB CREATEROLE NOREPLICATION NOBYPASSRLS; CREATE ROLE test_v2_role_target NOLOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS; GRANT test_v2_role_target TO test_v2_role_admin WITH ADMIN TRUE, INHERIT FALSE, SET FALSE;')
    r=sql('ALTER ROLE test_v2_role_target INHERIT;',role='test_v2_role_admin',check=False)
    value=sql("SELECT rolinherit FROM pg_roles WHERE rolname='test_v2_role_target';").stdout.strip()
    case('CREATEROLE_ADMIN_can_change_fixed_nonsuperuser_target',r.returncode==0 and value==b't',dict(exit=r.returncode,observed=value.decode()))
    r=sql('CREATE ROLE test_v2_outside_target NOLOGIN NOSUPERUSER;',role='test_v2_role_admin',check=False)
    count=sql("SELECT count(*) FROM pg_roles WHERE rolname='test_v2_outside_target';").stdout.strip()
    case('CREATEROLE_is_not_target_scoped_and_can_create_unapproved_role',r.returncode==0 and count==b'1',dict(exit=r.returncode,outside_target_created=True,interpretation='Counterexample to using CREATEROLE as a bounded live SQL privilege; not a V2 bypass result'))
    r=sql('ALTER ROLE postgres INHERIT;',role='test_v2_role_admin',check=False)
    case('CREATEROLE_cannot_administer_superuser',r.returncode!=0 and b'42501' in r.stderr,dict(exit=r.returncode,stderr=r.stderr.decode()))
    r=sql('ALTER ROLE test_0090_audit INHERIT;',role='test_v2_role_admin',check=False)
    case('CREATEROLE_requires_ADMIN_on_existing_target',r.returncode!=0 and b'42501' in r.stderr,dict(exit=r.returncode,stderr=r.stderr.decode()))
    r=sql('SET ROLE test_v2_role_target;',role='test_v2_role_admin',check=False)
    case('ADMIN_option_does_not_supply_SET_when_SET_false',r.returncode!=0 and b'42501' in r.stderr,dict(exit=r.returncode,stderr=r.stderr.decode()))
    r=sql('SET SESSION AUTHORIZATION test_0090_verification;',role='test_0090_audit',check=False)
    case('ordinary_consumer_cannot_change_session_user',r.returncode!=0 and b'42501' in r.stderr,dict(exit=r.returncode,stderr=r.stderr.decode(),capability_treatment='session_user immutable for ordinary authenticated connection; reconnect creates new identified session/epoch, never a helper-session substitute'))
    r=sql("SELECT json_build_object('phase','before','pid',pg_backend_pid(),'session_user',session_user,'current_user',current_user,'timezone',current_setting('TimeZone')); SET TIME ZONE 'UTC'; SELECT json_build_object('phase','after','pid',pg_backend_pid(),'session_user',session_user,'current_user',current_user,'timezone',current_setting('TimeZone'));",role='test_0090_audit')
    rows=[json.loads(line) for line in r.stdout.decode().splitlines() if line.startswith('{')]
    case('session_setting_mutates_exact_same_consumer_connection',len(rows)==2 and rows[0]['pid']==rows[1]['pid'] and rows[0]['session_user']==rows[1]['session_user']=='test_0090_audit' and rows[1]['timezone']=='UTC',rows)
    baseline=json.loads(sql("SELECT json_build_object('audit_execute',has_function_privilege('test_0090_audit','public.offline_read_history(uuid,bytea,uuid,text)','EXECUTE'),'owner_memberships',(SELECT count(*) FROM pg_auth_members m JOIN pg_roles r ON r.oid=m.roleid WHERE r.rolname LIKE 'flooow_offline_%_owner'),'readiness',(SELECT count(*) FROM public.offline_readiness));").stdout)
    case('normative_fixture_has_auditor_EXECUTE_and_zero_owner_edges',baseline==dict(audit_execute=True,owner_memberships=0,readiness=0),baseline)
    r=sql('SELECT count(*) FROM public.flyway_schema_history;',role='test_0090_audit',check=False)
    case('wrapper_EXECUTE_does_not_grant_raw_history_SELECT',r.returncode!=0 and b'42501' in r.stderr,dict(exit=r.returncode,stderr=r.stderr.decode()))
    r=sql('ALTER DATABASE g3f4 OWNER TO test_v2_role_target;',role='test_v2_role_admin',check=False)
    case('role_admin_is_not_database_owner_capability',r.returncode!=0 and b'42501' in r.stderr,dict(exit=r.returncode,stderr=r.stderr.decode()))
    sql('DROP ROLE test_v2_outside_target; REVOKE test_v2_role_target FROM test_v2_role_admin; DROP ROLE test_v2_role_target; DROP ROLE test_v2_role_admin;')
    case('experimental_admin_and_targets_removed',sql("SELECT count(*) FROM pg_roles WHERE rolname LIKE 'test_v2_%';").stdout.strip()==b'0',dict(no_experimental_admin_retained=True))


if __name__=='__main__':
    folder=OUT/'role-special-case-runtime';q.require(not folder.exists(),'Never overwrite experiment');folder.mkdir()
    source=q.ROOT/'docs/evidence/package-0090-semantic-ledger-active-fixture-final'
    import shutil
    for name in ['active-fixture-manifest.json','expected-acl-manifest.json','source-function-contexts.json']:shutil.copy2(source/name,folder/name)
    sys.modules['package_0090_reachable_v2_runtime']=types.SimpleNamespace(complete_qualification=qualify)
    sys.argv=[__file__,'--parser-path','C:/Users/xmz_r/.codex/tmp/package0090-pglast-8.5','--directory',str(folder),'--reachable-v2']
    raise SystemExit(foundation.main())
