"""Owned concurrent writes and revoked custody during delayed response."""
import subprocess,time,copy,json,concurrent.futures
def run(q):
    q.sql("CREATE TABLE compound_effect(op text PRIMARY KEY); GRANT INSERT ON compound_effect TO test_executor,test_issuer; CREATE TABLE compound_owner(state text); INSERT INTO compound_owner VALUES('OWNED');")
    writers=[]
    for role in ['test_executor','test_issuer']:
        writers.append(subprocess.Popen(['docker','exec','--user','postgres',q.NAME,'psql','-X','-w','-h','/tmp/pgsock','-U',role,'-d','native_fixture','-At','-c',"BEGIN; INSERT INTO compound_effect VALUES('"+role+"'); SELECT pg_sleep(60); COMMIT;"],stdout=subprocess.PIPE,stderr=subprocess.PIPE))
    try:
        end=time.monotonic()+8;ready=False
        while time.monotonic()<end:
            ready=q.sql("SELECT count(*) FROM pg_stat_activity WHERE usename IN ('test_executor','test_issuer') AND wait_event='PgSleep';").stdout.strip()=='2'
            if ready:break
            time.sleep(.05)
        q.case('compound','two_simultaneous_governed_writers_ready',ready,'Distinct actual server backends and retained self anchors')
        q.ex('touch','/run/flooow-watchdog/stall-receiver');end=time.monotonic()+25
        while any(w.poll() is None for w in writers) and time.monotonic()<end:time.sleep(.1)
        outcomes=[]
        for w in writers:
            stopped=w.poll() is not None
            if not stopped:w.kill()
            stdout,stderr=w.communicate(timeout=5);outcomes.append({'stopped':stopped,'exit':w.returncode,'stderr':stderr.decode()})
        q.case('compound','receiver_stall_stops_both_backends',all(r['stopped'] and r['exit']!=0 for r in outcomes),outcomes)
        q.case('compound','failed_receiver_not_masked_by_live_supervisor',q.sql('SELECT 1;','test_verifier',ok=False).returncode!=0,q.ex('tail','-n','70','/tmp/full.log').stdout)
    finally:
        for w in writers:
            if w.poll() is None:w.kill();w.wait()
        q.ex('touch','/run/flooow-watchdog/resume-receiver');q.ex('rm','-f','/run/flooow-watchdog/stall-receiver')
    q.ex('pg_ctl','-D','/tmp/pgdata','-m','immediate','-w','stop',ok=False);q.boot()
    with q.health_lock:assert q.observer_once()
    q.case('compound','two_backend_query_first_no_effect_owner_retained',q.sql('SELECT count(*) FROM compound_effect;').stdout.strip()=='0' and q.sql('SELECT state FROM compound_owner;').stdout.strip()=='OWNED','No signal success releases ownership; actual rollback queried after fresh bootstrap')
    q.ex('touch','/run/flooow-watchdog/delay-ack')
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        pending=pool.submit(q.sql,"SELECT 'LATE_ACCEPT_ESCAPE';",'test_verifier',False);time.sleep(1)
        q.paused.set()
        with q.health_lock:
            revoked=copy.deepcopy(q.expected_status);revoked['state']='REVOKED';q.rootfile('/run/flooow-external/status.json',json.dumps(revoked));assert not q.observer_once()
        result=pending.result(timeout=15)
    q.ex('rm','-f','/run/flooow-watchdog/delay-ack')
    q.case('compound','approval_revoked_plus_late_ACK_never_usable',result.returncode!=0 and 'LATE_ACCEPT_ESCAPE' not in result.stdout,{'stdout':result.stdout,'stderr':result.stderr,'experimental_ack_delay_only':True})
    with q.health_lock:q.rootfile('/run/flooow-external/status.json',json.dumps(q.expected_status));assert q.observer_once()
    q.paused.clear()
    q.case('compound','current_custody_restore_is_not_old_backend_revival',q.sql('SELECT count(*) FROM pg_stat_activity WHERE usename=\'test_verifier\';').stdout.strip()=='0','No late reply or restored approval reanimates old backend generation')
