"""Deterministic unknown pending anchor: no usable work, monotonic quarantine."""
import subprocess,time,json
def run(q):
    active=subprocess.Popen(['docker','exec','--user','postgres',q.NAME,'psql','-X','-h','/tmp/pgsock','-d','native_fixture','-U','test_executor','-At','-c','SELECT pg_sleep(60);'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    deadline=time.monotonic()+10
    while time.monotonic()<deadline:
        if q.sql("SELECT count(*) FROM pg_stat_activity WHERE usename='test_executor' AND wait_event='PgSleep';").stdout.strip()=='1':break
        time.sleep(.05)
    q.case('quarantine','active_backend_ready',active.poll() is None,'Retained observed anchor; no fixture preparation inferred usable')
    q.ex('touch','/run/flooow-watchdog/pre-observer-pause','/run/flooow-watchdog/skip-auth-observation')
    pending=subprocess.Popen(['docker','exec','--user','postgres',q.NAME,'psql','-X','-h','/tmp/pgsock','-d','native_fixture','-U','test_verifier','-At','-c',"SELECT 'USABLE_GOVERNED_ESCAPE';"],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    out,err=pending.communicate(timeout=20);aout,aerr=active.communicate(timeout=20)
    q.ex('rm','-f','/run/flooow-watchdog/pre-observer-pause','/run/flooow-watchdog/skip-auth-observation')
    logs=q.ex('cat','/tmp/full.log').stdout
    events=[]
    for line in logs.splitlines():
        try:events.append(json.loads(line))
        except json.JSONDecodeError:pass
    classifications=[e.get('classification') for e in events]
    q.case('quarantine','independent_unknown_discovery','BACKEND_NOT_REGISTERED' in classifications,{'events':events,'selector':'retained anchors only'})
    q.case('quarantine','no_pending_usable_escape',pending.returncode!=0 and b'USABLE_GOVERNED_ESCAPE' not in out,{'exit':pending.returncode,'stderr':err.decode()})
    q.case('quarantine','known_workload_stopped',active.returncode!=0,{'exit':active.returncode,'stderr':aerr.decode()})
    q.case('quarantine','catalog_remains_observable',q.sql('SELECT 1;',ok=False).returncode==0,'ADMIN observation allowed, governed admission latched DENY')
    q.case('quarantine','capture_before_enforcement_before_confirmation',all(c in classifications for c in ['QUARANTINED_PENDING_RECONCILIATION','QUARANTINE_CATALOG_CAPTURE_COMPLETE','QUARANTINE_KERNEL_CATALOG_OUTCOME_CONFIRMED']) and classifications.index('QUARANTINED_PENDING_RECONCILIATION')<classifications.index('QUARANTINE_CATALOG_CAPTURE_COMPLETE')<classifications.index('QUARANTINE_KERNEL_CATALOG_OUTCOME_CONFIRMED'),classifications)
    q.case('quarantine','kernel_and_catalog_outcome',q.sql("SELECT count(*) FROM pg_stat_activity WHERE usename IN ('test_verifier','test_executor');").stdout.strip()=='0','Neither process signal success nor empty unavailable catalog inferred absence')
    with q.health_lock:assert q.observer_once()
    for name in ['current_approval_restoration','late_heartbeat','late_catalog_response','late_receiver_response']:
        time.sleep(.15);q.denial('quarantine_monotonic',name)
    q.ex('touch','/run/flooow-watchdog/kill-receiver');deadline=time.monotonic()+20
    gone=False
    while time.monotonic()<deadline:
        gone=q.ex('test','!','-e','/tmp/pgdata/postmaster.pid',ok=False).returncode==0
        if gone:break
        time.sleep(.1)
    q.case('quarantine','receiver_loss_after_confirmed_outcome_tears_down',gone,'Independent observer retains completed witness and tears down the lost generation')
    if not gone:raise RuntimeError('Confirmed-outcome generation has not torn down')
    time.sleep(.3);q.boot()
    with q.health_lock:assert q.observer_once()
    q.case('quarantine','fresh_generation_requalification',q.sql('SELECT 1;','test_verifier',ok=False).returncode==0,'Only new sealed epoch/shared quarantine state can recover')
    q.ex('touch','/run/flooow-watchdog/stall-observer');deadline=time.monotonic()+22
    while time.monotonic()<deadline:
        if 'observer_progress_lost' in q.ex('tail','-n','100','/tmp/full.log').stdout:break
        time.sleep(.2)
    q.case('observer_health','stalled_alive_participant_detected','observer_progress_lost' in q.ex('cat','/tmp/full.log').stdout,'Kernel alive is not participant progress; independent supervisor witness')
    q.case('observer_health','stale_observer_denies_admission',q.sql('SELECT 1;','test_verifier',ok=False).returncode!=0,'No stale census may create eligibility')
