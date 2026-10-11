"""Admission remains closed during unresolved retained-anchor drain."""
import concurrent.futures,json,time
def run(q):
    for flag in ['drain-active','quarantine-active']:
        q.ex('touch','/run/flooow-watchdog/'+flag);q.denial('drain',flag);q.ex('rm','-f','/run/flooow-watchdog/'+flag)
        q.case('drain','explicit_fixture_requalification_'+flag,q.sql('SELECT 1;','test_verifier',ok=False).returncode==0,'fixture controller explicitly clears flag; no automatic ownership release')
    q.ex('touch','/run/flooow-watchdog/cancel-failure','/run/flooow-watchdog/terminate-failure')
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        writer=pool.submit(q.sql,'SELECT pg_sleep(20);','test_verifier',False);time.sleep(1);q.paused.set()
        with q.health_lock:
            x=dict(q.expected_status);x['state']='REVOKED';q.rootfile('/run/flooow-external/status.json',json.dumps(x));q.observer_once()
        q.denial('drain','signals_unavailable_no_new_admission')
        with q.health_lock:
            q.rootfile('/run/flooow-external/status.json',json.dumps(q.expected_status));assert q.observer_once()
        # Even fresh eligibility cannot bypass the unresolved existing quarantine.
        q.denial('drain','current_custody_cannot_bypass_live_quarantine')
        q.ex('rm','-f','/run/flooow-watchdog/terminate-failure');result=writer.result(timeout=10);time.sleep(.2)
        observed=q.sql("SELECT count(*) FROM pg_stat_activity WHERE usename='test_verifier';",ok=False)
        absent=observed.returncode==0 and observed.stdout.strip()=='0'
        q.case('drain','kernel_and_catalog_stop_required',result.returncode!=0 and absent,{'backend_exit':result.returncode,'catalog_disappeared':absent if observed.returncode==0 else 'UNKNOWN_CATALOG_UNAVAILABLE','catalog_exit':observed.returncode,'catalog_stderr':observed.stderr,'effects':'UNKNOWN_REQUIRES_RECONCILIATION','ownership_release':False})
        if observed.returncode!=0:
            # Keep the failed same-generation witness; fresh preparation permits
            # remaining tests but cannot retroactively turn that witness PASS.
            deadline=time.monotonic()+15
            while time.monotonic()<deadline and q.ex('test','!','-e','/tmp/pgdata/postmaster.pid',ok=False).returncode:time.sleep(.05)
            if q.ex('test','!','-e','/tmp/pgdata/postmaster.pid',ok=False).returncode:raise RuntimeError('Owned generation teardown unfinished; refuse replacement')
            q.boot()
            with q.health_lock:assert q.observer_once()
            q.case('drain','fresh_preparation_does_not_resolve_prior_census_race',True,{'prior_assertion':'FAIL_RETAINED','no_old_catalog_zero_inference':True,'effects':'UNKNOWN_REQUIRES_RECONCILIATION','scope':'Preparation for remaining cases only'})
        q.ex('rm','-f','/run/flooow-watchdog/cancel-failure');q.paused.clear()
    # Regression must pass on the final receiver variant too.
    q.ex('touch','/run/flooow-watchdog/crash-supervisor')
    end=time.monotonic()+10
    while time.monotonic()<end and q.ex('pg_isready','-h','/tmp/pgsock','-U','postgres',ok=False).returncode==0:time.sleep(.1)
    gone=q.ex('pg_isready','-h','/tmp/pgsock','-U','postgres',ok=False).returncode!=0
    if not gone:raise RuntimeError('Final receiver failed supervisor-loss regression')
    q.boot()
    with q.health_lock:assert q.observer_once()
    q.case('restart','final_receiver_supervisor_restart',q.sql('SELECT 1;','test_verifier',ok=False).returncode==0,'expected parent peer pidfd matches retained supervisor anchor; fresh epoch')
