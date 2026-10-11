"""Experimental kernel-anchored stall injection, no numeric policy authority."""
import time,subprocess,json
def run(q):
    def logs():return q.ex('cat','/tmp/full.log',ok=False).stdout
    def participants():
        events=[json.loads(x) for x in logs().splitlines() if x.startswith('{')]
        return next(e for e in reversed(events) if e.get('event')=='supervisor_started')
    # Parent injector uses existing retained anchors, never pidfd_open(foreign PID).
    for participant in ['receiver','supervisor']:
        event=participants()
        active=subprocess.Popen(['docker','exec','--user','postgres',q.NAME,'psql','-X','-h','/tmp/pgsock','-d','native_fixture','-U','test_executor','-At','-c','SELECT pg_sleep(60);'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        time.sleep(1)
        q.case('heartbeat',participant+'_active_before_stall',active.poll() is None,q.snapshot())
        before=time.monotonic_ns();q.ex('touch','/run/flooow-watchdog/stall-'+participant)
        end=time.monotonic()+25
        while active.poll() is None and time.monotonic()<end:time.sleep(.1)
        elapsed=(time.monotonic_ns()-before)/1000
        q.case('heartbeat',participant+'_stall_drains',active.poll() is not None,{'elapsed_us':elapsed,'experimental_observation_limit_s':25,'logs':logs()[-9000:]})
        q.case('heartbeat',participant+'_stall_deny_new',q.sql('SELECT 42;','test_verifier',ok=False).returncode!=0,'Stalled required participant cannot preserve admission')
        if active.poll() is None:active.kill();active.wait()
        # Resume exact anchors via the retained supervising participant before rebootstrap.
        q.ex('rm','-f','/run/flooow-watchdog/stall-'+participant)
        q.ex('touch','/run/flooow-watchdog/resume-'+participant)
        time.sleep(1)
        q.ex('pg_ctl','-D','/tmp/pgdata','-m','immediate','-w','stop',ok=False)
        q.boot();q.observer_once()
        q.case('heartbeat',participant+'_fresh_generation_recovers',q.sql('SELECT 42;','test_verifier',ok=False).returncode==0,event)
