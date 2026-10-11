"""Additional compound and stalled-critical-participant schedules; disposable only."""
import subprocess,time,json,copy,concurrent.futures
def run(q):
    def log():return q.ex('cat','/tmp/full.log',ok=False).stdout
    def reset():
        q.paused.clear();q.ex('rm','-f','/run/flooow-watchdog/replay-original-heartbeat','/run/flooow-watchdog/positive-reply-pause','/run/flooow-watchdog/force-quarantine')
        with q.health_lock:q.rootfile('/run/flooow-external/status.json',json.dumps(q.expected_status));assert q.observer_once()
        q.ex('pg_ctl','-D','/tmp/pgdata','-m','immediate','-w','stop',ok=False);q.boot()
        with q.health_lock:assert q.observer_once()
    def active(role='test_executor'):
        p=subprocess.Popen(['docker','exec','--user','postgres',q.NAME,'psql','-X','-w','-h','/tmp/pgsock','-U',role,'-d','native_fixture','-At','-c','SELECT pg_sleep(60);'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        end=time.monotonic()+8;pid=None
        while time.monotonic()<end:
            s=q.sql("SELECT pid FROM pg_stat_activity WHERE usename='"+role+"' AND wait_event='PgSleep';").stdout.strip()
            if s:pid=int(s);break
            time.sleep(.05)
        assert pid and p.poll() is None;return p,pid
    # Actual original emitted Supervisor heartbeat, replayed by same kernel sender.
    p,pid=active();time.sleep(11);before=log();q.paused.set()
    with q.health_lock:
        revoked=copy.deepcopy(q.expected_status);revoked['state']='REVOKED';q.rootfile('/run/flooow-external/status.json',json.dumps(revoked));assert not q.observer_once()
    q.ex('touch','/run/flooow-watchdog/replay-original-heartbeat')
    end=time.monotonic()+20
    while time.monotonic()<end and 'test_original_heartbeat_replayed' not in log()[len(before):]:time.sleep(.1)
    events=log()[len(before):]
    q.case('compound','approval_revoked_plus_actual_stale_heartbeat', 'test_original_heartbeat_replayed' in events and 'supervisor_progress_lost' in events,{'events':events,'same_actual_sender':True,'original_emission_stamp':True,'fabricated_timestamp':False,'numeric_policy_authority':'NONE'})
    q.case('compound','stale_heartbeat_never_restores_revoked_admission',q.ex('env','PGCONNECT_TIMEOUT=2','psql','-X','-w','-h','/tmp/pgsock','-U','test_verifier','-d','native_fixture','-At','-c','SELECT 42;',ok=False,timeout=8).returncode!=0,'Fresh shared loop progress cannot mask invalid old wire heartbeat or revoked custody')
    if p.poll() is None:p.kill()
    p.communicate(timeout=5);reset()
    # Global quarantine occurs after a positive response is prepared, before send.
    q.ex('touch','/run/flooow-watchdog/positive-reply-pause');before=log()
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        pending=pool.submit(q.sql,"SELECT 'QUARANTINE_LATE_ACCEPT_ESCAPE';",'test_verifier',False)
        end=time.monotonic()+5;prepared=False
        while time.monotonic()<end:
            prepared='test_positive_reply_prepared' in log()[len(before):]
            if prepared:break
            time.sleep(.025)
        q.ex('touch','/run/flooow-watchdog/force-quarantine');r=pending.result(timeout=15)
    q.case('compound','quarantine_between_prepared_ACCEPT_and_send',prepared and r.returncode!=0 and 'QUARANTINE_LATE_ACCEPT_ESCAPE' not in r.stdout,{'stdout':r.stdout,'stderr':r.stderr,'events':log()[len(before):],'experimental_reply_pause_s':2,'numeric_policy_authority':'NONE'})
    q.ex('rm','-f','/run/flooow-watchdog/positive-reply-pause')
    with q.health_lock:assert q.observer_once()
    q.denial('compound','approval_restore_never_clears_same_generation_quarantine');reset()
    # PM is alive but stops accepting new catalog connections; known work freezes.
    p,pid=active();stat_before=q.ex('cat','/proc/'+str(pid)+'/stat',user='0').stdout;before=log()
    q.ex('touch','/run/flooow-watchdog/stall-postmaster');end=time.monotonic()+12;stopped=False
    while time.monotonic()<end:
        state=q.ex('cat','/proc/'+str(pid)+'/stat',user='0',ok=False).stdout
        stopped=bool(state) and state.split(') ',1)[1].split()[0] in ['T','t']
        if stopped and 'test_postmaster_stopped_alive' in log()[len(before):]:break
        time.sleep(.1)
    q.case('participant_liveness','postmaster_alive_stalled_catalog_unreachable',stopped and 'test_postmaster_stopped_alive' in log()[len(before):],{'backend_stat_before':stat_before,'backend_stat_after':state,'signals_selected_only_retained_pm_anchor':True,'known_backend_frozen':stopped,'outcome':'UNKNOWN_REQUIRES_RECONCILIATION'})
    q.case('participant_liveness','healthy_receiver_cannot_mask_stalled_postmaster',q.ex('env','PGCONNECT_TIMEOUT=2','psql','-X','-w','-h','/tmp/pgsock','-U','test_verifier','-d','native_fixture','-At','-c','SELECT 42;',ok=False,timeout=8).returncode!=0,'No catalog absence/effect zero inferred from unreachable parent')
    q.ex('touch','/run/flooow-watchdog/resume-postmaster');end=time.monotonic()+15
    while p.poll() is None and time.monotonic()<end:time.sleep(.1)
    if p.poll() is None:p.kill()
    p.communicate(timeout=5);reset()
    # Host approval consumer thread remains alive while publication is paused.
    p,pid=active()
    with q.health_lock:assert q.observer_once()
    q.paused.set();alive=q.observer_thread.is_alive();before=log();end=time.monotonic()+28
    while p.poll() is None and time.monotonic()<end:time.sleep(.1)
    drained=p.poll() is not None
    q.case('participant_liveness','approval_consumer_alive_but_no_progress_denies',alive and q.observer_thread.is_alive() and drained,{'thread_alive':alive,'native_retained_consumer_identity':'NOT_QUALIFIED_HOST_THREAD','experimental_gate_lease_only':True,'events':log()[len(before):],'numeric_policy_authority':'NONE'})
    q.case('participant_liveness','stale_approval_consumer_denies_new',q.sql('SELECT 42;','test_verifier',ok=False).returncode!=0,'Healthy native heartbeat cannot renew external approval-consumer progress')
    if p.poll() is None:p.kill()
    p.communicate(timeout=5);reset()
