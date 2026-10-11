"""Active transaction under each owned native generation death; no PID lookup kill."""
import subprocess,time,json
def run(q):
    q.sql("CREATE TABLE test_death_effect(op text PRIMARY KEY); GRANT INSERT ON test_death_effect TO test_executor; CREATE TABLE test_death_owner(state text); INSERT INTO test_death_owner VALUES('OWNED');")
    for participant in ['receiver','supervisor','postmaster']:
        writer=subprocess.Popen(['docker','exec','--user','postgres',q.NAME,'psql','-X','-w','-h','/tmp/pgsock','-d','native_fixture','-U','test_executor','-At','-c',"BEGIN; INSERT INTO test_death_effect VALUES('"+participant+"'); SELECT pg_sleep(60); COMMIT;"],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        ready=time.monotonic()+5;identity=''
        while time.monotonic()<ready:
            identity=q.sql("SELECT json_build_object('pid',pid,'backend_start',backend_start,'postmaster_start',pg_postmaster_start_time(),'wait_event',wait_event) FROM pg_stat_activity WHERE usename='test_executor' AND state='active' AND wait_event='PgSleep';",ok=False).stdout.strip()
            if identity:break
            time.sleep(.05)
        q.case('active_death',participant+'_active_transaction',bool(identity) and writer.poll() is None,{'server_identity':identity,'process_selection':'retained child anchor or self-exit; no pidfd_open(foreign PID)'})
        start=time.monotonic_ns()
        if participant=='postmaster':
            q.ex('pg_ctl','-D','/tmp/pgdata','-m','immediate','-w','stop',ok=False)
        else:q.ex('touch','/run/flooow-watchdog/'+('kill-receiver' if participant=='receiver' else 'crash-supervisor'))
        deadline=time.monotonic()+20
        while writer.poll() is None and time.monotonic()<deadline:time.sleep(.05)
        stopped=writer.poll() is not None
        if not stopped:writer.kill()
        stdout,stderr=writer.communicate(timeout=5)
        q.case('active_death',participant+'_active_writer_stops',stopped and writer.returncode!=0,{'elapsed_us':(time.monotonic_ns()-start)/1000,'exit':writer.returncode,'stderr':stderr.decode(errors='replace'),'stdout':stdout.decode(errors='replace'),'exact_backend_pidfd_death_independent_enforcer':'NOT_QUALIFIED'})
        q.case('active_death',participant+'_deny_new',q.sql('SELECT 42;','test_verifier',ok=False).returncode!=0,'Generation loss denies usable service session')
        # Wait for owned PG teardown before starting another preparation fixture.
        gone=False
        while time.monotonic()<deadline:
            gone=q.ex('test','!','-e','/tmp/pgdata/postmaster.pid',ok=False).returncode==0
            if gone:break
            time.sleep(.05)
        if not gone:raise RuntimeError('Owned prior postmaster has not finished teardown; refuse rebootstrap')
        q.boot()
        with q.health_lock:assert q.observer_once()
        count=q.sql("SELECT count(*) FROM test_death_effect WHERE op='"+participant+"';").stdout.strip()
        owner=q.sql('SELECT state FROM test_death_owner;').stdout.strip()
        q.case('active_death',participant+'_authoritative_query_first',count=='0' and owner=='OWNED',{'writer_quiescent':stopped,'authoritative_count':count,'after_query':'KNOWN_NO_EFFECT','initial_state':'UNKNOWN_REQUIRES_RECONCILIATION','ownership':owner,'automatic_replay':False,'full_frozen_domain_wrapper':False})
        q.case('active_death',participant+'_fresh_generation_recovers',q.sql('SELECT 1;','test_verifier',ok=False).returncode==0,'Fresh sealed epoch and retained participant anchors; same synthetic binding/custody')
