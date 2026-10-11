"""Regress descriptor lifetime failure and instrumented timeout recovery."""
import concurrent.futures,time,json
def run(q):
    for ms in [0,120,900]:
        r=q.ex('env',f'PGOPTIONS=-c statement_timeout={ms}','psql','-X','-w','-h','/tmp/pgsock','-U','test_verifier','-d','native_fixture','-At','-c','SHOW statement_timeout;',ok=False)
        q.case('timeout','instrumented_caller_setting_'+str(ms),r.returncode==0 and r.stdout.strip() in [str(ms),str(ms)+'ms','0'],{'stdout':r.stdout,'stderr':r.stderr})
    for flag in ['partial-frame','drop-ack','delay-ack','catalog-stall']:
        q.ex('touch','/run/flooow-watchdog/'+flag);q.denial('timeout','instrumented_'+flag);q.ex('rm','-f','/run/flooow-watchdog/'+flag)
        q.case('timeout','instrumented_recovery_'+flag,q.sql('SELECT 1;','test_verifier',ok=False).returncode==0,'fresh backend recovery; accepted path independently snapshots SIGALRM/ITIMER_REAL and caller statement timer')
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        lock=pool.submit(q.sql,'BEGIN; LOCK flooow_test_binding IN ACCESS EXCLUSIVE MODE; SELECT pg_sleep(7); COMMIT;')
        end=time.monotonic()+4
        while time.monotonic()<end:
            if q.sql("SELECT count(*) FROM pg_locks WHERE relation='flooow_test_binding'::regclass AND mode='AccessExclusiveLock' AND granted;").stdout.strip()=='1':break
            time.sleep(.05)
        q.denial('timeout','instrumented_SPI_lock_stall');lock.result(timeout=10)
        q.case('timeout','instrumented_SPI_error_recovery',q.sql('SELECT 1;','test_verifier',ok=False).returncode==0,'user timeout cleanup through PG_CATCH; backend cancellation did not change later sessions')
    # Supervisor self-pidfd survives exec and is checked against socketpair peer pidfd.
    q.ex('touch','/run/flooow-watchdog/crash-supervisor')
    end=time.monotonic()+12
    while time.monotonic()<end and q.ex('pg_isready','-h','/tmp/pgsock','-U','postgres',ok=False).returncode==0:time.sleep(.1)
    gone=q.ex('pg_isready','-h','/tmp/pgsock','-U','postgres',ok=False).returncode!=0
    r=q.sql('SELECT 1;','test_verifier',ok=False)
    q.case('restart','supervisor_loss_blocks_usable_session',gone and r.returncode!=0,{'postmaster_stopped':gone,'stderr':r.stderr})
    if not gone:raise RuntimeError('Supervisor-loss regression remains open; refuse replacement postmaster')
    q.boot()
    with q.health_lock:assert q.observer_once()
    q.case('restart','supervisor_restart_regression',q.sql('SELECT 1;','test_verifier',ok=False).returncode==0,'fresh kernel anchors and epoch; prior descriptor-reuse failure retained')
    q.ex('touch','/run/flooow-watchdog/delay-ack')
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        pending=pool.submit(q.sql,'SELECT 42;','test_verifier',False);time.sleep(1);q.ex('touch','/run/flooow-watchdog/kill-receiver');r=pending.result(timeout=12)
    q.case('timeout','receiver_crash_during_login',r.returncode!=0 and '42' not in r.stdout,{'stderr':r.stderr,'stdout':r.stdout,'usable_statement_executed':False})
    q.ex('rm','-f','/run/flooow-watchdog/delay-ack');time.sleep(1);q.boot()
    with q.health_lock:assert q.observer_once()
    q.case('restart','full_stack_after_pending_receiver_crash',q.sql('SELECT 1;','test_verifier',ok=False).returncode==0,'fresh bootstrap after loss')
