"""Observe pending login independently and require no usable SELECT escape."""
import subprocess,time,json
def run(q):
    active=subprocess.Popen(['docker','exec','--user','postgres',q.NAME,'psql','-X','-h','/tmp/pgsock','-d','native_fixture','-U','test_executor','-At','-c','SELECT pg_sleep(10);'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    time.sleep(1);q.case('census','known_backend_active',active.poll() is None,q.snapshot())
    prior=q.ex('cat','/tmp/full.log').stdout;q.ex('touch','/run/flooow-watchdog/pre-transfer-pause')
    pending=subprocess.Popen(['docker','exec','--user','postgres',q.NAME,'psql','-X','-h','/tmp/pgsock','-d','native_fixture','-U','test_verifier','-At','-c',"SELECT 'USABLE_GOVERNED_ESCAPE';"],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    pending_out,pending_err=pending.communicate(timeout=25);pending_out=pending_out.decode('utf-8');pending_err=pending_err.decode('utf-8');q.ex('rm','-f','/run/flooow-watchdog/pre-transfer-pause')
    logs=q.ex('cat','/tmp/full.log',ok=False).stdout[len(prior):]
    q.case('census','pre_scm_native_birth_retained','PENDING_AUTH_ANCHOR_ONLY' in logs and 'PENDING_RETAINED_ANCHOR' in logs,logs)
    q.case('census','pending_server_backend_independently_discovered','MATCHED' in logs,{'logs':logs[-16000:]})
    q.case('census','pre_scm_no_usable_governed_work',pending.returncode!=0 and 'USABLE_GOVERNED_ESCAPE' not in pending_out,{'stdout':pending_out,'stderr':pending_err,'exit':pending.returncode})
    aout,aerr=active.communicate(timeout=20)
    q.case('census','covered_pending_does_not_invent_inconsistency',active.returncode==0 and 'quarantine_frozen_anchor_set' not in logs,{'active_stderr':aerr.decode(),'scope':'Early strong pending anchor is observation only; no unknown identity assumed'})
    q.case('census','independent_worker_final_catalog',q.sql("SELECT count(*) FROM pg_stat_activity WHERE usename IN ('test_verifier','test_executor');").stdout.strip()=='0','Server-derived census after kernel exit; no missing catalog zero inference')
