"""Additional bounded faults without repeating predecessor mechanisms."""
import json,time,concurrent.futures,copy,uuid,base64
def run(q):
    # Non-ASCII NFC valid role is a distinct fixture name; exact original roster denies
    # alias equivalence. Pure frame test exercises the NFC-positive codec separately.
    q.sql('CREATE ROLE "caf\u00e9" LOGIN NOINHERIT;')
    r=q.sql('SELECT current_user;','caf\u00e9',ok=False)
    q.case('encoding','NFC_unmanaged_does_not_inherit_governed_authority',r.returncode==0,'unmanaged Unicode name cannot resolve any allocated slot')
    # Actual logical dump/restore with copied header and accepted external bundle.
    q.ex('sh','-c','pg_dump -h /tmp/pgsock -U postgres native_fixture > /tmp/TEST_ONLY_NONCANONICAL.dump')
    q.ex('createdb','-h','/tmp/pgsock','logical_clone')
    restored=q.ex('sh','-c','psql -X -h /tmp/pgsock -U postgres -d logical_clone -v ON_ERROR_STOP=1 < /tmp/TEST_ONLY_NONCANONICAL.dump',ok=False)
    r=q.ex('psql','-X','-w','-h','/tmp/pgsock','-U','test_verifier','-d','logical_clone','-At','-c','SELECT 1;',ok=False)
    q.case('clone','actual_logical_restore_default_ineligible',restored.returncode==0 and r.returncode!=0 and 'FLOOOW_TEST_ENROLLMENT_DENIED' in r.stderr,{'restore_exit':restored.returncode,'restore_stderr':restored.stderr,'login_stderr':r.stderr,'external_original_context_copied':False,'original_custody_not_clone_authority':True})
    # Active write aborted before COMMIT: verify actual durable absence after death.
    q.sql('CREATE TABLE test_effect(op text PRIMARY KEY,value int); GRANT INSERT,SELECT ON test_effect TO test_verifier; CREATE TABLE test_owner(id int PRIMARY KEY,state text); INSERT INTO test_owner VALUES(1,\'OWNED\');')
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        writer=pool.submit(q.sql,"BEGIN; INSERT INTO test_effect VALUES('during_transaction',1); SELECT pg_sleep(20); COMMIT;",'test_verifier',False)
        end=time.monotonic()+8;pid=None
        while time.monotonic()<end:
            ids=q.sql("SELECT pid FROM pg_stat_activity WHERE usename='test_verifier' AND state='active' AND query LIKE 'SELECT pg_sleep(20)%';").stdout.strip()
            if ids:pid=int(ids);break
            time.sleep(.05)
        q.paused.set()
        with q.health_lock:
            st=dict(q.expected_status);st['state']='REVOKED';q.rootfile('/run/flooow-external/status.json',json.dumps(st));q.observer_once()
        result=writer.result(timeout=15)
        count=q.sql("SELECT count(*) FROM test_effect WHERE op='during_transaction';").stdout.strip()
        owner=q.sql('SELECT state FROM test_owner;').stdout.strip()
        q.case('effect','revocation_during_write_before_commit',pid is not None and result.returncode!=0 and count=='0' and owner=='OWNED',{'classification_after_query':'KNOWN_NO_EFFECT','initial_classification':'UNKNOWN_REQUIRES_RECONCILIATION','query_count':count,'ownership':owner,'writer_stderr':result.stderr,'automatic_replay':False})
        with q.health_lock:q.rootfile('/run/flooow-external/status.json',json.dumps(q.expected_status));assert q.observer_once()
        q.paused.clear()
    # Both signals suppressed: backend remains in quarantine; restoring signaling must drain.
    q.ex('touch','/run/flooow-watchdog/cancel-failure','/run/flooow-watchdog/terminate-failure')
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        victim=pool.submit(q.sql,'SELECT pg_sleep(20);','test_verifier',False)
        time.sleep(1);q.paused.set()
        with q.health_lock:
            st=dict(q.expected_status);st['state']='REVOKED';q.rootfile('/run/flooow-external/status.json',json.dumps(st));q.observer_once()
        q.denial('enforcement','both_signals_fail_still_deny_new')
        held=q.sql("SELECT count(*) FROM pg_stat_activity WHERE usename='test_verifier' AND state='active';").stdout.strip()=='1'
        q.ex('rm','-f','/run/flooow-watchdog/terminate-failure')
        result=victim.result(timeout=10)
        q.case('enforcement','terminate_failure_quarantine_retained_until_recovery',held and result.returncode!=0,{'live_when_signals_suppressed':held,'after_recovery_exit':result.returncode,'ownership_release':False,'risk':'No bounded completion while signaling unavailable'})
        q.ex('rm','-f','/run/flooow-watchdog/cancel-failure')
        with q.health_lock:q.rootfile('/run/flooow-external/status.json',json.dumps(q.expected_status));assert q.observer_once()
        q.paused.clear()
    # Physical cold copy retains database bytes but cannot bootstrap on its own.
    q.paused.set()
    with q.health_lock:
        q.ex('pg_ctl','-D','/tmp/pgdata','-m','fast','-w','stop')
        time.sleep(.5)
        q.ex('cp','-a','/tmp/pgdata','/tmp/TEST_ONLY_NONCANONICAL.physical-clone')
        q.ex('mkdir','-p','/tmp/clone-socket')
        r=q.ex('/usr/lib/postgresql/18/bin/postgres','-D','/tmp/TEST_ONLY_NONCANONICAL.physical-clone','-c','shared_preload_libraries=/usr/local/lib/flooow_test_login','-c','unix_socket_directories=/tmp/clone-socket','-c','listen_addresses=',ok=False,timeout=10)
        q.case('clone','actual_physical_clone_default_ineligible',r.returncode!=0 and 'inherited context absent' in r.stderr,{'stderr':r.stderr,'copied_header_preserved':True,'mandatory_external_bootstrap_missing':True})
        q.boot();assert q.observer_once()
    q.paused.clear()
    q.case('restart','postmaster_database_stack_rebootstrap',q.sql('SELECT 1;','test_verifier',ok=False).returncode==0,'new atomic receiver/postmaster pair; same deployment/incarnation; fresh ephemeral epoch')
    # Receiver gone: no usable service session; generation loss requires whole pair restart.
    q.ex('touch','/run/flooow-watchdog/kill-receiver');time.sleep(.5)
    r=q.sql('SELECT 1;','test_verifier',ok=False)
    q.case('admission','receiver_unavailable_denies_before_usable_session',r.returncode!=0,{'stderr':r.stderr,'transport_unavailability_is_not_effect_rollback':True})
    q.boot()
    with q.health_lock:assert q.observer_once()
    # Original role recreated: same exact name cannot convert OID mismatch into unmanaged login.
    q.sql('REVOKE INSERT,SELECT ON test_effect FROM test_verifier; DROP ROLE test_verifier; CREATE ROLE test_verifier LOGIN NOINHERIT NOSUPERUSER NOCREATEROLE NOCREATEDB NOREPLICATION NOBYPASSRLS;')
    oid=q.sql("SELECT oid FROM pg_roles WHERE rolname='test_verifier';").stdout.strip();r=q.sql('SELECT 1;','test_verifier',ok=False)
    q.case('admission','role_recreation_exact_name_wrong_oid',r.returncode!=0 and 'allocated identity mismatch' in r.stderr,{'new_oid':oid,'original_oid':q.expected_approval['roles'][0][0],'stderr':r.stderr})
