"""Observe pending login independently and require no usable SELECT escape."""
import subprocess,time,json
def run(q):
    active=subprocess.Popen(['docker','exec','--user','postgres',q.NAME,'psql','-X','-h','/tmp/pgsock','-d','native_fixture','-U','test_executor','-At','-c','SELECT pg_sleep(60);'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    time.sleep(1);q.case('census','known_backend_active',active.poll() is None,q.snapshot())
    q.ex('touch','/run/flooow-watchdog/pre-transfer-pause')
    pending=subprocess.Popen(['docker','exec','--user','postgres',q.NAME,'psql','-X','-h','/tmp/pgsock','-d','native_fixture','-U','test_verifier','-At','-c',"SELECT 'USABLE_GOVERNED_ESCAPE';"],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    pending_out,pending_err=pending.communicate(timeout=25);pending_out=pending_out.decode('utf-8');pending_err=pending_err.decode('utf-8');end=time.monotonic()+20
    while active.poll() is None and time.monotonic()<end:time.sleep(.1)
    logs=q.ex('cat','/tmp/full.log',ok=False).stdout
    q.case('census','pending_server_backend_independently_discovered','BACKEND_NOT_REGISTERED' in logs,{'logs':logs[-16000:]})
    q.case('census','pre_scm_no_usable_governed_work',pending.returncode!=0 and 'USABLE_GOVERNED_ESCAPE' not in pending_out,{'stdout':pending_out,'stderr':pending_err,'exit':pending.returncode})
    q.case('census','unregistered_forces_coarse_generation_drain',active.poll() is not None and 'census_quarantine_generation' in logs,'Retained postmaster anchor selects owned generation; no numeric PID acquisition')
    if active.poll() is None:active.kill();active.wait()
    q.record['cases'].append({'group':'census','name':'all_birth_death_duplicate_generation_races','result':'NOT_RUN','detail':'Pending enrollment witness is bounded; exhaustive race schedules and separate census worker independence remain unqualified'})
