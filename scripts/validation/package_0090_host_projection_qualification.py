"""Disposable component qualification; NEVER deployed host/enrollment proof.

Actual Linux self-pidfd probe and peer-authenticated writer/reader ACL tests.
Synthetic context/predicate tests cannot certify PostgreSQL native admission,
continuous enforcement, receiver epoch/ACK or 100us cross-process freshness.
No canonical container access, migrations, ADMIN artifact, T0, keys or SIGN.
"""
from pathlib import Path
import json,hashlib,subprocess,tempfile,time,uuid,math

ROOT=Path(__file__).resolve().parents[2]
BASE='bd7ee39123e6186b6d6ce129eaa61c82e009773a'
IMAGE='sha256:07fc165de5bb569d822460e2df645c5489f99220fc2cb16c86596d39db394561'
PROBE=ROOT/'scripts/validation/package_0090_self_enrolled_pidfd_probe.c'

def call(args,data=None,timeout=60,allow_error=False):
    result=subprocess.run(args,input=data,text=True,capture_output=True,timeout=timeout)
    if result.returncode and not allow_error:raise RuntimeError(args[0]+': '+result.stderr[-1500:])
    return result

def main():
    call(['git','merge-base','--is-ancestor',BASE,'HEAD'])
    work=Path(tempfile.mkdtemp(prefix='flooow-0090-host-components-'))
    print('PRIVATE_EVIDENCE='+str(work),flush=True)
    name='flooow-0090-host-components-'+uuid.uuid4().hex[:12];started=False;containers=[]
    tests=[];record={'scope':'COMPONENTS_ONLY_NOT_NATIVE_POSTGRES_ENROLLMENT_OR_WATCHDOG_PASS',
        'baseline':BASE,'image':IMAGE,'canonical_access':False,'canonical_mutation':False,
        'key_generation':False,'sign':False,'admin_artifact_execution':False,
        'native_probe_source_sha256':hashlib.sha256(PROBE.read_bytes()).hexdigest()}
    try:
        start=time.monotonic_ns()
        call(['docker','run','--detach','--name',name,'--label','flooow.scope=0090-host-components-only',
            '--tmpfs','/tmp','--tmpfs','/var/lib/postgresql','--mount',f'type=bind,source={PROBE},target=/probe.c,readonly',
            '-e','PGDATA=/tmp/pgdata','-e','POSTGRES_DB=host_components_0090',
            '-e','POSTGRES_HOST_AUTH_METHOD=trust','--entrypoint','docker-entrypoint.sh',IMAGE,'postgres'])
        started=True
        containers.append(name)
        for _ in range(100):
            if call(['docker','exec',name,'pg_isready','-U','postgres','-d','host_components_0090'],allow_error=True).returncode==0:break
            time.sleep(.1)
        details=json.loads(call(['docker','inspect',name]).stdout)[0]
        assert details['Image']==IMAGE and not details['NetworkSettings']['Ports']['5432/tcp']
        assert not any(m['Type']=='volume' for m in details['Mounts'])
        assert details['Config']['Labels']['flooow.scope']=='0090-host-components-only'
        record['container_startup_observed_us']=(time.monotonic_ns()-start)/1000
        def sql(statement,role='postgres',user='postgres',error=False):
            return call(['docker','exec','--user',user,'-i',name,'psql','-X','-w','-U',role,'-d','host_components_0090','-At','-v','ON_ERROR_STOP=1'],statement,allow_error=error)
        assert sql("SELECT current_database()||'|'||current_setting('server_version_num');").stdout.strip()=='host_components_0090|180004'
        # tmpfs /tmp is noexec; executable stays in this container's disposable overlay.
        binary='/usr/local/bin/0090-native-component-probe'
        call(['docker','exec','--user','0',name,'gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-o',binary,'/probe.c'])
        call(['docker','exec','--user','0',name,'chmod','0555',binary])
        probe_result=call(['docker','exec','--user','postgres',name,binary],timeout=45,allow_error=True)
        record['native_probe_binary_sha256']=call(['docker','exec',name,'sha256sum',binary]).stdout.split()[0]
        native=probe_result.stdout
        record['native_probe_exit_code']=probe_result.returncode
        record['native_probe_stderr']=probe_result.stderr
        (work/'native-probe.jsonl').write_text(native,encoding='utf8')
        record['native_probe']=[json.loads(line) for line in native.splitlines() if line.startswith('{')]
        record['native_probe_nonjson_lines']=[line for line in native.splitlines() if not line.startswith('{')]
        assert probe_result.returncode==0,'STANDALONE_NATIVE_PROBE_FAILED'
        # Private fixture roles are unrelated to every governed rehearsal login.
        sql('''CREATE ROLE bench_observer LOGIN NOSUPERUSER NOCREATEROLE NOCREATEDB;
CREATE ROLE bench_plan LOGIN NOSUPERUSER NOCREATEROLE NOCREATEDB;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
CREATE TABLE bench_expected(deployment text,incarnation text,generation text,system_id text);
INSERT INTO bench_expected SELECT 'TEST_DEPLOYMENT','TEST_INCARNATION','TEST_GENERATION_1',system_identifier::text FROM pg_control_system();
CREATE TABLE bench_observation(deployment text,incarnation text,generation text,checked_at timestamptz,healthy boolean);
REVOKE ALL ON bench_expected,bench_observation FROM PUBLIC;
GRANT SELECT ON bench_expected,bench_observation TO bench_plan;
GRANT SELECT,INSERT,UPDATE,DELETE ON bench_observation TO bench_observer;
CREATE FUNCTION bench_predicate(d text,i text,g text,checked timestamptz,h boolean,now_at timestamptz)
RETURNS boolean LANGUAGE SQL STABLE SET search_path=pg_catalog AS $$
 SELECT COALESCE((SELECT d=e.deployment AND i=e.incarnation AND g=e.generation
   AND h AND isfinite(checked) AND isfinite(now_at) AND now_at>=checked
   AND now_at-checked<=interval '100 microseconds' FROM public.bench_expected e),false)
$$;
REVOKE ALL ON FUNCTION bench_predicate(text,text,text,timestamptz,boolean,timestamptz) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION bench_predicate(text,text,text,timestamptz,boolean,timestamptz) TO bench_plan;
CREATE FUNCTION bench_consume() RETURNS json LANGUAGE SQL SECURITY DEFINER VOLATILE SET search_path=pg_catalog AS $$
 WITH now_sample AS MATERIALIZED (SELECT clock_timestamp() AS n)
 SELECT json_build_object('eligible',COALESCE((SELECT public.bench_predicate(o.deployment,o.incarnation,o.generation,o.checked_at,o.healthy,n.n)
     AND e.system_id=(SELECT system_identifier::text FROM pg_control_system())
     FROM public.bench_observation o CROSS JOIN public.bench_expected e),false),
     'age_us',(SELECT extract(epoch FROM (n.n-o.checked_at))*1000000 FROM public.bench_observation o)) FROM now_sample n
$$;
REVOKE ALL ON FUNCTION bench_consume() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION bench_consume() TO bench_plan;
CREATE TABLE bench_commit_fixture(id text PRIMARY KEY);
''')
        # Unix-peer authentication prevents the consumer choosing the observer role.
        # No TCP port is published; TCP is rejected and no credentials are created.
        call(['docker','exec','--user','0',name,'sh','-c',
            "printf 'fixture_map postgres postgres\nfixture_map postgres bench_observer\nfixture_map nobody bench_plan\n' > /tmp/pgdata/pg_ident.conf; printf 'local all all peer map=fixture_map\nhost all all all reject\n' > /tmp/pgdata/pg_hba.conf"])
        sql('SELECT pg_reload_conf();')
        def plan(statement,error=False):return sql(statement,'bench_plan','nobody',error)
        def observer(statement):return sql(statement,'bench_observer','postgres')
        def check(label,actual,expected,kind):
            assert actual==expected,(label,actual,expected)
            tests.append({'case':label,'pass':True,'evidence_kind':kind})
        # These deliberately injected instants are SQL predicate tests, not host observations.
        cases=[('correct_deployment_and_incarnation','TEST_DEPLOYMENT','TEST_INCARNATION','TEST_GENERATION_1',0,True,True),
            ('wrong_deployment','WRONG','TEST_INCARNATION','TEST_GENERATION_1',0,True,False),
            ('wrong_incarnation','TEST_DEPLOYMENT','WRONG','TEST_GENERATION_1',0,True,False),
            ('fresh_99us','TEST_DEPLOYMENT','TEST_INCARNATION','TEST_GENERATION_1',99,True,True),
            ('fresh_exact_100us','TEST_DEPLOYMENT','TEST_INCARNATION','TEST_GENERATION_1',100,True,True),
            ('stale_101us','TEST_DEPLOYMENT','TEST_INCARNATION','TEST_GENERATION_1',101,True,False),
            ('future_observation','TEST_DEPLOYMENT','TEST_INCARNATION','TEST_GENERATION_1',-1,True,False),
            ('replayed_receiver_generation','TEST_DEPLOYMENT','TEST_INCARNATION','OLD',0,True,False),
            ('watchdog_false','TEST_DEPLOYMENT','TEST_INCARNATION','TEST_GENERATION_1',0,False,False),
            ('clone_incarnation','TEST_DEPLOYMENT','CLONED','TEST_GENERATION_1',0,True,False)]
        for label,d,i,g,age,h,expected in cases:
            command=f"SELECT bench_predicate('{d}','{i}','{g}',t-interval '{age} microseconds',{str(h).lower()},t) FROM (SELECT timestamptz '2000-01-01 00:00:00+00' t) x;"
            check(label,plan(command).stdout.strip()=='t',expected,'SYNTHETIC_SQL_PREDICATE_NOT_AUTHENTICATED_HOST_PROOF')
        check('missing_projection',json.loads(plan('SELECT bench_consume();').stdout)['eligible'],False,'ACTUAL_PROTECTED_PROJECTION')
        for label,command in [
            ('consumer_cannot_insert',"INSERT INTO bench_observation VALUES ('TEST_DEPLOYMENT','TEST_INCARNATION','TEST_GENERATION_1',clock_timestamp(),true);"),
            ('consumer_cannot_update',"UPDATE bench_observation SET checked_at=clock_timestamp(),healthy=true;"),
            ('consumer_cannot_change_expected_context',"UPDATE bench_expected SET incarnation='WRONG';"),
            ('consumer_cannot_set_observer_role','SET ROLE bench_observer;'),
            ('consumer_cannot_set_observer_session_authorization','SET SESSION AUTHORIZATION bench_observer;'),
            ('consumer_cannot_replace_consumer','CREATE OR REPLACE FUNCTION bench_consume() RETURNS json LANGUAGE SQL AS $$ SELECT NULL::json $$;'),
            ('consumer_cannot_disable_login_event_setting','SET event_triggers=false;')]:
            check(label,plan(command,True).returncode!=0,True,'ACTUAL_PEER_AUTHENTICATED_SQL_ACL_BOUNDARY')
        check('consumer_cannot_authenticate_as_observer',sql('SELECT current_user;','bench_observer','nobody',True).returncode!=0,True,'ACTUAL_PEER_AUTHENTICATION')
        # This row is explicitly a component fixture, never claimed continuously healthy.
        observer("INSERT INTO bench_observation VALUES ('TEST_DEPLOYMENT','TEST_INCARNATION','TEST_GENERATION_1',clock_timestamp(),true);")
        trusted=sql('BEGIN; UPDATE bench_observation SET checked_at=clock_timestamp(),healthy=true; SELECT healthy FROM bench_observation; ROLLBACK;')
        check('trusted_superuser_can_author_projection_outside_threat_model','t' in trusted.stdout.splitlines(),True,'ACTUAL_FIXTURE_COUNTEREXAMPLE_TO_HOSTILE_ADMIN_PROTECTION_ROLLED_BACK')
        ages=[]
        for _ in range(10):
            observer('UPDATE bench_observation SET checked_at=clock_timestamp(),healthy=true;')
            r=json.loads(plan('SELECT bench_consume();').stdout);ages.append(r)
        record['actual_writer_to_consumer_projection_samples']=ages
        observer("UPDATE bench_observation SET checked_at=clock_timestamp()-interval '1 second';")
        check('actual_stale_projection',json.loads(plan('SELECT bench_consume();').stdout)['eligible'],False,'ACTUAL_PROTECTED_PROJECTION')
        sql("UPDATE bench_expected SET generation='TEST_GENERATION_2';")
        check('receiver_restart_old_projection',json.loads(plan('SELECT bench_consume();').stdout)['eligible'],False,'INJECTED_TRUSTED_EXPECTED_GENERATION')
        sql("UPDATE bench_expected SET system_id='NOT_THE_CURRENT_CLUSTER';")
        check('restore_copied_system_context',json.loads(plan('SELECT bench_consume();').stdout)['eligible'],False,'INJECTED_SYSTEM_CONTEXT_NOT_REAL_CLONE')
        # Actual logical restore of only this fixture into a second fresh cluster.
        # This is not a physical clone (which can preserve system_identifier).
        sql("UPDATE bench_expected SET generation='TEST_GENERATION_1',system_id=(SELECT system_identifier::text FROM pg_control_system()); UPDATE bench_observation SET generation='TEST_GENERATION_1',checked_at=clock_timestamp();")
        dump=call(['docker','exec','--user','postgres',name,'pg_dump','-U','postgres','-d','host_components_0090','--clean','--if-exists','--no-owner','--no-acl']).stdout
        restored='flooow-0090-host-components-'+uuid.uuid4().hex[:12]
        call(['docker','run','--detach','--name',restored,'--label','flooow.scope=0090-host-components-only',
            '--tmpfs','/tmp','--tmpfs','/var/lib/postgresql','-e','PGDATA=/tmp/pgdata',
            '-e','POSTGRES_DB=host_components_0090','-e','POSTGRES_HOST_AUTH_METHOD=trust',
            '--entrypoint','docker-entrypoint.sh',IMAGE,'postgres'])
        containers.append(restored)
        for _ in range(100):
            if call(['docker','exec',restored,'pg_isready','-U','postgres','-d','host_components_0090'],allow_error=True).returncode==0:break
            time.sleep(.1)
        restored_details=json.loads(call(['docker','inspect',restored]).stdout)[0]
        assert restored_details['Image']==IMAGE and not restored_details['NetworkSettings']['Ports']['5432/tcp']
        assert not any(m['Type']=='volume' for m in restored_details['Mounts'])
        def restore_sql(statement):return call(['docker','exec','--user','postgres','-i',restored,'psql','-X','-w','-U','postgres','-d','host_components_0090','-At','-v','ON_ERROR_STOP=1'],statement)
        restore_sql(dump)
        mismatch=restore_sql("SELECT system_id<>(SELECT system_identifier::text FROM pg_control_system()) FROM bench_expected;").stdout.strip()
        check('actual_logical_restore_new_system_id',mismatch,'t','ACTUAL_LOGICAL_RESTORE_NOT_PHYSICAL_CLONE')
        check('actual_logical_restore_old_projection_denied',json.loads(restore_sql('SELECT bench_consume();').stdout)['eligible'],False,'ACTUAL_LOGICAL_RESTORE_STALE_AND_WRONG_SYSTEM_CONTEXT')
        # Physical backup/clone stays between two explicitly owned disposable containers.
        # No dump/page files are persisted on the workstation; stream tar bytes directly.
        call(['docker','exec','--user','0',name,'sh','-c',"printf 'local replication postgres peer map=fixture_map\n' >> /tmp/pgdata/pg_hba.conf"])
        sql('SELECT pg_reload_conf();')
        physical='flooow-0090-host-components-'+uuid.uuid4().hex[:12]
        call(['docker','run','--detach','--name',physical,'--label','flooow.scope=0090-host-components-only',
            '--tmpfs','/tmp','--tmpfs','/var/lib/postgresql','--entrypoint','/bin/sh',IMAGE,'-c','sleep 180'])
        containers.append(physical)
        physical_details=json.loads(call(['docker','inspect',physical]).stdout)[0]
        assert physical_details['Image']==IMAGE and not physical_details['NetworkSettings']['Ports'].get('5432/tcp')
        assert not any(m['Type']=='volume' for m in physical_details['Mounts'])
        call(['docker','exec','--user','0',physical,'mkdir','/tmp/pgdata'])
        backup=subprocess.Popen(['docker','exec','--user','postgres',name,'pg_basebackup','-U','postgres','-D','-','-Ft','-X','fetch','-c','fast'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        unpack=subprocess.Popen(['docker','exec','--user','0','-i',physical,'tar','xf','-','-C','/tmp/pgdata'],stdin=backup.stdout,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        backup.stdout.close()
        assert unpack.wait(timeout=45)==0 and backup.wait(timeout=45)==0,'DISPOSABLE_PHYSICAL_COPY_FAILED'
        call(['docker','exec','--user','0',physical,'chown','-R','postgres:postgres','/tmp/pgdata'])
        call(['docker','exec','--user','0',physical,'chmod','0700','/tmp/pgdata'])
        call(['docker','exec','--user','postgres','--detach',physical,'sh','-c','exec postgres -D /tmp/pgdata -k /tmp/pgdata > /tmp/physical-postgres.log 2>&1'])
        for _ in range(100):
            if call(['docker','exec',physical,'pg_isready','-h','/tmp/pgdata','-U','postgres','-d','host_components_0090'],allow_error=True).returncode==0:break
            time.sleep(.1)
        else:raise RuntimeError('PHYSICAL_CLONE_STARTUP: '+call(['docker','exec',physical,'cat','/tmp/physical-postgres.log']).stdout[-1500:])
        physical_result=call(['docker','exec','--user','postgres','-i',physical,'psql','-h','/tmp/pgdata','-X','-w','-U','postgres','-d','host_components_0090','-At','-v','ON_ERROR_STOP=1'],
            "SELECT system_id=(SELECT system_identifier::text FROM pg_control_system()) FROM bench_expected; SELECT bench_consume();").stdout.splitlines()
        check('actual_physical_clone_copies_system_identifier',physical_result[0],'t','ACTUAL_PHYSICAL_CLONE_COUNTEREXAMPLE_TO_SYSTEM_ID_UNIQUENESS')
        check('actual_physical_clone_old_projection_denied',json.loads(physical_result[1])['eligible'],False,'ACTUAL_PHYSICAL_CLONE_OLD_TIMESTAMP_DENIAL_ONLY')
        record['physical_clone_qualification']='COPIED_SYSTEM_ID_AND_STALE_PROJECTION_DENIAL_ONLY_NOT_NATIVE_REINCARNATION_OR_FRESH_REAUTHORSHIP_PROOF'
        # Cold/degraded components only: no new mechanical ceremony/timing profile.
        connections=[]
        for _ in range(10):
            t=time.monotonic_ns();plan('SELECT 1;');connections.append((time.monotonic_ns()-t)/1000)
        record['fresh_psql_connection_plus_docker_ipc_us']=connections
        holder=subprocess.Popen(['docker','exec','--user','postgres',name,'psql','-X','-w','-U','postgres','-d','host_components_0090','-At','-c','SELECT pg_advisory_lock(90001010); SELECT pg_sleep(1.2);'],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        for _ in range(10):
            if sql("SELECT count(*) FROM pg_locks WHERE locktype='advisory' AND objid=90001010 AND granted;").stdout.strip()=='1':break
        else:raise RuntimeError('CONTROLLED_LOCK_NOT_OBSERVED')
        t=time.monotonic_ns();plan('BEGIN; SELECT pg_advisory_xact_lock(90001010); ROLLBACK;')
        record['observed_advisory_contention_us']=(time.monotonic_ns()-t)/1000
        assert holder.wait(timeout=10)==0
        # Deliberately discard psql acknowledgement; join writer, then query fresh.
        # It is NOT a real 08006 or a signed-root recovery qualification.
        identifier='TEST_UNSIGNED_'+uuid.uuid4().hex
        dispatch=subprocess.Popen(['docker','exec','--user','postgres','-i',name,'psql','-X','-w','-U','postgres','-d','host_components_0090','-At','-v','ON_ERROR_STOP=1'],stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
        dispatch.stdin.write(f"BEGIN; INSERT INTO bench_commit_fixture VALUES ('{identifier}'); COMMIT;\n");dispatch.stdin.close()
        assert dispatch.wait(timeout=20)==0
        found=sql(f"SELECT count(*) FROM bench_commit_fixture WHERE id='{identifier}';").stdout.strip()
        check('discarded_ack_join_writer_fresh_query_first',found,'1','ACTUAL_UNSIGNED_COMMIT_ACK_DISCARD_NOT_08006')
        record['tests']=tests;record['test_count']=len(tests)
        record['watchdog_gate']='HOLD_NOT_NATIVE_ADMISSION_OR_CONTINUOUS_ENFORCEMENT'
        record['native_enrollment_implemented']=False
        record['proof_signing']=False
        record['limits']=['SQL positive instants are injected, not live host observations',
            'Private fixture predicate is not an approved new codec/API/lease',
            'Logical restore and physical clone are actual; fresh reauthorship, native reincarnation and epoch bootstrap are not qualified',
            'Peer ACL denies unprivileged consumer; hostile trusted superuser remains outside accepted threat model',
            'Self-pidfd primitive is standalone; no native PostgreSQL login handler is installed',
            'No synchronous governed ACK, complete enrollment roster or continuous supervision/drain is qualified',
            'Cross-process 100us age is measured, never renewed by consumer or widened',
            'CPU/GC/network/checkpoint tails are not bounded by these observations']
    finally:
        for own_container in reversed(containers):call(['docker','rm','--force','--volumes',own_container])
    record['disposable_removed']=True
    record['source_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (work/'evidence.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8',newline='\n')
    print(json.dumps({'test_count':record['test_count'],'gate':record['watchdog_gate'],'disposable_removed':True}),flush=True)

if __name__=='__main__':main()
