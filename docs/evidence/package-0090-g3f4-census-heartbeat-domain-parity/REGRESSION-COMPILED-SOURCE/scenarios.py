"""Bounded real native/SQL/crypto faults; missing coverage stays explicit."""
import json,copy,time,threading,concurrent.futures,subprocess,uuid,base64
def run(q):
    # Service privileges: SQL services cannot author custody, approval or health.
    for object_ in ['offline_binding_header','offline_binding_lifecycle','offline_attempt_pointer','flooow_test_binding']:
        r=q.sql('UPDATE '+object_+' SET '+('slot=1' if object_=='flooow_test_binding' else "binding_id=binding_id")+';','test_verifier',ok=False)
        q.case('health','service_cannot_author_'+object_,r.returncode!=0 and 'permission denied' in r.stderr,{'stderr':r.stderr})
    for path in ['status.json','approval.json','attestation.json','gate.bin']:
        r=q.ex('sh','-c','echo x >> "$1"','sh','/run/flooow-external/'+path,ok=False)
        q.case('custody','postgres_os_cannot_write_'+path,r.returncode!=0,{'stderr':r.stderr})
    # All required custody failures consume external status before accepting a session.
    for state in ['REVOKED','RETIRED','STALE','MISSING','AMBIGUOUS']:
        st=copy.deepcopy(q.expected_status);st['state']=state
        q.mutate_external('/run/flooow-external/status.json',st,state)
    for name,field in [('DIGEST_MISMATCH','artifact_digest'),('TARGET_MISMATCH','deployment_id'),('COPIED_TO_CLONE','incarnation_id')]:
        st=copy.deepcopy(q.expected_status);st[field]='different-synthetic-context'
        q.mutate_external('/run/flooow-external/status.json',st,name)
    q.mutate_external('/run/flooow-external/status.json',{},'MISSING_CURRENT_STATUS')
    # Exact independent original commitment plus signer/authority/window checks.
    edits={'wrong_manifest':('manifest_digest','0'*64),'wrong_signer':('key_id',str(uuid.uuid4())),'wrong_domain':('signature_domain','WRONG_DOMAIN'),'wrong_policy_digest':('manifest_hex','00'),'tampered_payload':('signature_hex','00'),'stale_key':('key_state','RETIRED'),'revoked_key':('key_state','REVOKED'),'stale_attestation':('window_end','2000-01-01T00:00:00.000000Z')}
    for name,(field,value) in edits.items():
        b=copy.deepcopy(q.expected_bundle);b[field]=value;q.mutate_external('/run/flooow-external/attestation.json',b,name,'attestation')
    for name,field,value in [('wrong_signer_authority','permission','WRONG_PERMISSION'),('revoked_signer_authority','state','DISABLED'),('wrong_organization','organization_id',str(uuid.uuid4()))]:
        b=copy.deepcopy(q.expected_bundle);b['authority'][field]=value;q.mutate_external('/run/flooow-external/attestation.json',b,name,'attestation')
    q.mutate_external('/run/flooow-external/attestation.json',{},'missing_attestation','attestation')
    # Tamper exact signature preimage while metadata remains correct: real crypto must fail.
    q.paused.set()
    with q.health_lock:
        b=base64.b64decode(q.ex('base64','-w','0','/run/flooow-external/preimage.bin',user='0').stdout);tampered=bytes([b[0]^1])+b[1:]
        q.rootfile('/run/flooow-external/preimage.bin',tampered);q.observer_once();q.denial('attestation','cryptographic_tamper_with_matching_metadata');q.rootfile('/run/flooow-external/preimage.bin',b);assert q.observer_once()
    q.paused.clear()
    # Exact full38 header mutation: constraints reject or independent consumer denies.
    quote=lambda v:str(v) if isinstance(v,int) else "'"+str(v).replace("'","''")+"'"
    for field in q.codec.FIELDS:
        old=q.expected_header[field]
        if field in q.codec.VERSIONS:value=old+1
        elif field in q.codec.HASH:value='\\x'+'01'*32
        elif field in q.codec.TIMES:value='2020-01-01T00:00:00Z'
        elif field=='identity_slots':value='\\x00'
        elif field.endswith('_id'):value=str(uuid.uuid4())
        else:value='SYNTHETIC_MUTATION'
        q.paused.set()
        with q.health_lock:
            r=q.sql(f'UPDATE offline_binding_header SET {field}={quote(value)};',ok=False)
            if r.returncode:q.case('binding','field_'+field,True,{'constraint_denied':True,'stderr':r.stderr})
            else:
                q.observer_once();q.denial('binding','field_'+field);q.sql(f'UPDATE offline_binding_header SET {field}={quote(old)};');assert q.observer_once()
        q.paused.clear()
    for name,mutate,restore in [
        ('duplicate_slot','INSERT INTO flooow_test_binding SELECT * FROM flooow_test_binding WHERE slot=1;','DELETE FROM flooow_test_binding WHERE ctid IN (SELECT ctid FROM flooow_test_binding WHERE slot=1 OFFSET 1);'),
        ('zero_binding','DELETE FROM flooow_test_binding WHERE slot=1;',"INSERT INTO flooow_test_binding SELECT 1,oid,rolname FROM pg_roles WHERE rolname='test_verifier';"),
        ('role_rename','ALTER ROLE test_verifier RENAME TO renamed_verifier;','ALTER ROLE renamed_verifier RENAME TO test_verifier;'),
        ('attributes','ALTER ROLE test_verifier INHERIT;','ALTER ROLE test_verifier NOINHERIT;'),
        ('membership','GRANT test_membership TO test_verifier;','REVOKE test_membership FROM test_verifier;')]:
        q.sql(mutate)
        if name=='role_rename':
            r=q.sql('SELECT 1;','renamed_verifier',ok=False);q.case('admission',name,r.returncode!=0 and 'FLOOOW_TEST_ENROLLMENT_DENIED' in r.stderr,{'stderr':r.stderr})
        else:q.denial('admission',name)
        q.sql(restore)
    # Timeout setting remains caller-selected; custom USER_TIMEOUT does not overwrite it.
    for ms in [0,120,900]:
        r=q.ex('env',f'PGOPTIONS=-c statement_timeout={ms}','psql','-X','-w','-h','/tmp/pgsock','-U','test_verifier','-d','native_fixture','-At','-v','ON_ERROR_STOP=1','-c','SHOW statement_timeout;',ok=False)
        q.case('timeout','caller_setting_'+str(ms),r.returncode==0 and r.stdout.strip() in [str(ms),str(ms)+'ms','0'],{'stdout':r.stdout,'stderr':r.stderr})
    r=q.ex('env','PGOPTIONS=-c statement_timeout=120','psql','-X','-w','-h','/tmp/pgsock','-U','test_verifier','-d','native_fixture','-At','-c','SELECT pg_sleep(0.4);',ok=False)
    q.case('timeout','post_login_caller_timer_operates',r.returncode!=0 and 'statement timeout' in r.stderr,{'stderr':r.stderr})
    for flag in ['partial-frame','drop-ack','delay-ack','catalog-stall']:
        q.ex('touch','/run/flooow-watchdog/'+flag);q.denial('protocol',flag);q.ex('rm','-f','/run/flooow-watchdog/'+flag)
        q.case('timeout','recovery_after_'+flag,q.sql('SELECT 1;','test_verifier',ok=False).returncode==0,'fresh backend accepted after denied/timeout backend exit')
    # Active retained-anchor targeting; independent unmanaged session remains available.
    def activefault(name,inject,restore):
        r=q.sql('SELECT pg_backend_pid();','test_unmanaged');unmanaged=int(r.stdout.strip())
        # Persistent unrelated session for actual target-isolation witness.
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            foreign=pool.submit(q.sql,'SELECT pg_sleep(3),42;','test_unmanaged',False)
            victim=pool.submit(q.sql,'SELECT pg_sleep(20);','test_verifier',False)
            end=time.monotonic()+5;pid=None
            while time.monotonic()<end:
                s=q.sql("SELECT pid FROM pg_stat_activity WHERE usename='test_verifier' AND query LIKE 'SELECT pg_sleep(20)%';").stdout.strip()
                if s:pid=int(s);break
                time.sleep(.05)
            t=time.monotonic_ns();inject();result=victim.result(timeout=15)
            disappearance=q.sql('SELECT count(*) FROM pg_stat_activity WHERE pid='+str(pid or 0)+';').stdout.strip()=='0'
            unrelated=foreign.result(timeout=10)
            q.case('enforcement',name,pid is not None and result.returncode!=0 and disappearance and unrelated.returncode==0,{'pid':pid,'unmanaged_initial_pid':unmanaged,'catalog_disappeared':disappearance,'victim_stderr':result.stderr,'unrelated_stdout':unrelated.stdout,'elapsed_us':(time.monotonic_ns()-t)/1000,'signal_alone_not_proof':True})
            restore()
    def externalrevoke():
        q.paused.set()
        with q.health_lock:
            x=dict(q.expected_status);x['state']='REVOKED';q.rootfile('/run/flooow-external/status.json',json.dumps(x));q.observer_once()
    def externalrestore():
        with q.health_lock:q.rootfile('/run/flooow-external/status.json',json.dumps(q.expected_status));assert q.observer_once()
        q.paused.clear()
    activefault('approval_revoked',externalrevoke,externalrestore)
    activefault('independent_observer_unavailable',lambda:q.paused.set(),lambda:(q.observer_once(),q.paused.clear()))
    activefault('cancel_failure_then_terminate',lambda:(q.ex('touch','/run/flooow-watchdog/cancel-failure'),externalrevoke()),lambda:(q.ex('rm','-f','/run/flooow-watchdog/cancel-failure'),externalrestore()))
    # Explicit ambiguity with durable query-first; no ownership release/replay.
    q.sql('CREATE TABLE test_effect(op text PRIMARY KEY,value int); CREATE TABLE test_owner(id int PRIMARY KEY,state text); INSERT INTO test_owner VALUES(1,\'OWNED\'); GRANT INSERT,SELECT ON test_effect TO test_verifier;')
    q.sql('BEGIN; INSERT INTO test_effect VALUES(\'precommit\',1); ROLLBACK;','test_verifier')
    count=q.sql("SELECT count(*) FROM test_effect WHERE op='precommit';").stdout.strip()
    q.case('effect','known_no_effect_after_authoritative_query',count=='0',{'classification':'KNOWN_NO_EFFECT','query_count':count,'disconnect_inference':False})
    q.sql("INSERT INTO test_effect VALUES('committed',1);",'test_verifier')
    count=q.sql("SELECT count(*) FROM test_effect WHERE op='committed';").stdout.strip()
    q.case('effect','known_committed_query_first',count=='1',{'classification':'KNOWN_COMMITTED','query_count':count,'automatic_replay':False})
    # Lost response: process is killed by its own harness after writing COMMIT into stdin.
    args=['docker','exec','--user','postgres','-i',q.NAME,'psql','-X','-w','-h','/tmp/pgsock','-U','test_verifier','-d','native_fixture','-At']
    p=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    p.stdin.write("BEGIN; INSERT INTO test_effect VALUES('ambiguous',1); COMMIT; SELECT pg_sleep(10);\n");p.stdin.flush();time.sleep(.8);p.kill();p.communicate(timeout=10)
    count=q.sql("SELECT count(*) FROM test_effect WHERE op='ambiguous';").stdout.strip()
    owner=q.sql('SELECT state FROM test_owner WHERE id=1;').stdout.strip()
    q.case('effect','commit_response_lost_query_first',owner=='OWNED' and count in ['0','1'],{'initial_classification':'UNKNOWN_REQUIRES_RECONCILIATION','after_query':'KNOWN_COMMITTED' if count=='1' else 'KNOWN_NO_EFFECT','query_count':count,'ownership':owner,'new_attempt':False,'automatic_replay':False,'limitation':'Docker client response deliberately discarded; transport-loss point relative to COMMIT not forced'})
    # Load overlap proven by independent active marker throughout measured requests.
    for label,body in [('CPU','while test ! -e /tmp/load.stop; do openssl speed -seconds 1 sha256 >/dev/null 2>&1; done'),('IO','while test ! -e /tmp/load.stop; do dd if=/dev/zero of=/tmp/load.io bs=1M count=8 conv=fsync >/dev/null 2>&1; done')]:
        q.ex('rm','-f','/tmp/load.stop','/tmp/load.active');loadstart=time.monotonic_ns()
        q.ex('sh','-c','touch /tmp/load.active; '+body+'; rm -f /tmp/load.active; touch /tmp/load.ended',timeout=20) if False else None
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            load=pool.submit(q.ex,'sh','-c','touch /tmp/load.active; '+body+'; rm -f /tmp/load.active; touch /tmp/load.ended',timeout=30)
            while q.ex('test','-e','/tmp/load.active',ok=False).returncode:time.sleep(.02)
            confirmed=time.monotonic_ns();cohort=[]
            try:
                for i in range(4):
                    before=q.ex('test','-e','/tmp/load.active',ok=False).returncode==0;a=time.monotonic_ns();r=q.sql('SELECT 1;','test_verifier',ok=False);b=time.monotonic_ns();after=q.ex('test','-e','/tmp/load.active',ok=False).returncode==0
                    cohort.append({'request_start_ns':a,'request_end_ns':b,'load_active_before':before,'load_active_after':after,'exit':r.returncode,'elapsed_us':(b-a)/1000})
            finally:q.ex('touch','/tmp/load.stop');result=load.result(timeout=10)
        ended=time.monotonic_ns();q.case('load',label+'_overlap',result.returncode==0 and all(s['load_active_before'] and s['load_active_after'] and s['exit']==0 for s in cohort),{'LOAD_START':loadstart,'LOAD_CONFIRMED_ACTIVE':confirmed,'LOAD_END':ended,'requests':cohort,'scope':'one owned container cpu quota1/memory768MiB; bounded 8MiB tmpfsIO; no disk-tail proof'})
    # Full copied database/header/attestation is insufficient if external incarnation differs.
    for name in ['logical_restore_context','physical_clone_context','copied_header','copied_attestation','copied_approval']:
        x=copy.deepcopy(q.expected_approval);x['incarnation_id']=str(uuid.uuid4());q.mutate_external('/run/flooow-external/approval.json',x,name,'clone')
    # Restarts preserve synthetic deployment/incarnation and ownership; epoch must rotate.
    for name,flag in [('receiver_restart','kill-receiver'),('supervisor_restart','crash-supervisor')]:
        q.ex('touch','/run/flooow-watchdog/'+flag)
        end=time.monotonic()+10
        while time.monotonic()<end and q.ex('pg_isready','-h','/tmp/pgsock','-U','postgres',ok=False).returncode==0:time.sleep(.1)
        gone=q.ex('pg_isready','-h','/tmp/pgsock','-U','postgres',ok=False).returncode!=0
        q.boot()
        with q.health_lock:good=q.observer_once()
        accepted=q.sql('SELECT 1;','test_verifier',ok=False).returncode==0
        q.case('restart',name,gone and good and accepted,{'old_postmaster_stopped':gone,'fresh_admission':accepted,'identity_survival':'deployment/incarnation/header unchanged; ephemeral joint epoch fresh from getrandom; old retained anchors dead','ownership':q.sql('SELECT state FROM test_owner;').stdout.strip()})
    # Enumerate gaps instead of inflating mechanism coverage.
    for name,reason in {
        'forced_oid_reuse':'No safe supported PostgreSQL catalog operation to force allocator OID reuse; no system-catalog corruption injected.',
        'full_physical_clone':'Copied external-context rejection tested; separate physical PGDATA clone/restore stack not run.',
        'full_logical_restore':'Copied-context rejection tested; actual dump/restore stack not run.',
        'terminate_failure':'Recovery/quarantine persistence with both cancel and terminate suppressed not yet qualified.',
        'full_transaction_ownership_contract':'Synthetic ownership retained; actual V043 claim/attempt/effect/domain wrapper execution not run.',
        'postmaster_control_inconsistency':'Prior postmaster restart retained; full successor generation-inconsistency injection not run.',
        'all_timeout_state_signal_invariants':'Custom USER_TIMEOUT avoids caller timer mutation; no independent complete signal/alarm snapshot yet.',
        'complete_watchdog_worstcase_coverage':'Serial receiver catalog validation can block observation during catalog stalls; no universal observation bound.',
        'independent_JVM_reference_binding_vectors':'Reference framing plus source-derived SQL constraints exercised; full independent JVM vector parity pending.',
    }.items():q.record['cases'].append({'group':'remaining','name':name,'result':'NOT_RUN_WITH_REASON','reason':reason})
