"""Owned disposable native experiment only. Never connects to canonical V6.

Prepared containers use network=none, tmpfs data/run and scoped seccomp clone3.
Experimental 5-second abort, 128 registry slots and 20ms fixture polling are
harness controls, not selected/approved ACK, resource or watchdog policy.
"""
from pathlib import Path
import hashlib,json,subprocess,struct,time,math,traceback,sys,concurrent.futures
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'docs/evidence/package-0090-g3f4-disposable-native-qualification'
PRIVATE=Path(r'C:\Users\xmz_r\AppData\Local\Temp\flooow-native-qualification')
NAME='flooow-0090-native-qual-bd84005-v1'
CONTROL='flooow-0090-native-qual-bd84005'
IMAGE='sha256:07fc165de5bb569d822460e2df645c5489f99220fc2cb16c86596d39db394561'
SCOPE='0090-disposable-native-qualification'
record={'scope':'DISPOSABLE_NATIVE_MECHANISM_ONLY_NOT_PRODUCTION_OR_FULL_WATCHDOG_PASS','input_head':'bd840059f5a78d8e28a09a0ccc6463f3d5098663','canonical_access':False,'canonical_mutation':False,'numeric_policy_adoption':False,'experimental_controls':{'abort_us':5000000,'registry_entries':128,'death_poll_ms':20,'delay_fault_seconds':6},'tests':[],'samples':[],'limitations':[]}
MEASURE='--measure' in sys.argv
ROUND3='--round3' in sys.argv
ROUND2='--round2' in sys.argv or ROUND3
if ROUND2:
    OUT=OUT/('round3' if ROUND3 else 'round2'); NAME='flooow-0090-native-qual-bd84005-r3' if ROUND3 else 'flooow-0090-native-qual-bd84005-r2'
if MEASURE:
    OUT=ROOT/'docs/evidence/package-0090-g3f4-disposable-native-qualification/measurement';NAME='flooow-0090-native-qual-bd84005-measure'
if '--evidence-output' in sys.argv:
    OUT=Path(sys.argv[sys.argv.index('--evidence-output')+1]).resolve()
def cmd(args,data=None,ok=True,timeout=30):
    r=subprocess.run(args,input=data,text=True,capture_output=True,timeout=timeout)
    if ok and r.returncode:raise RuntimeError(' '.join(args[:5])+' '+r.stderr[-1500:])
    return r
def ex(*args,ok=True,user='postgres',data=None,timeout=30):return cmd(['docker','exec','--user',user,'-i',NAME,*args],data,ok,timeout)
def sql(s,role='postgres',ok=True):return ex('psql','-X','-w','-h','/tmp/pgsock','-U',role,'-d','native_fixture','-At','-v','ON_ERROR_STOP=1',data=s,ok=ok)
def case(name,passed,detail):
    record['tests'].append({'name':name,'result':'PASS' if passed else 'FAIL','detail':detail})
    print(name+': '+('PASS' if passed else 'FAIL'),flush=True)
def await_pg(limit=20):
    end=time.monotonic()+limit
    while time.monotonic()<end:
        r=ex('pg_isready','-h','/tmp/pgsock','-U','postgres',ok=False)
        if r.returncode==0:return
        time.sleep(.1)
    raise RuntimeError('PostgreSQL startup timeout: '+ex('cat','/tmp/native.log',ok=False).stdout[-3000:])
def fixture(*args):return ex(*args)
def launch():
    ex('rm','-f','/run/flooow-watchdog/enrollment-v1.sock') # exact owned fixture endpoint
    ex('sh','-c','/usr/local/bin/flooow-test-supervisor > /tmp/native.log 2>&1 &',timeout=10)
    await_pg()
def denied(name,s='SELECT 1;',role='test_verifier'):
    start=time.monotonic_ns();r=sql(s,role,ok=False)
    case(name,r.returncode!=0,{'exit':r.returncode,'stderr':r.stderr,'elapsed_us':(time.monotonic_ns()-start)/1000})
def stop_pg():
    return ex('pg_ctl','-D','/tmp/pgdata','-m','fast','-w','stop',ok=False)
def main():
    if OUT.exists():raise RuntimeError('Refuse to overwrite evidence')
    OUT.mkdir(parents=True)
    try:
        for n in ([NAME] if ROUND2 or MEASURE else [NAME,CONTROL]):
            info=json.loads(cmd(['docker','inspect',n]).stdout)[0]
            assert info['Image']==IMAGE and info['Config']['Labels'].get('flooow.scope')==SCOPE
            assert info['HostConfig']['NetworkMode']=='none' and not info['Mounts']
            record.setdefault('container_inspections',[]).append({'name':n,'id':info['Id'],'image':info['Image'],'network':info['HostConfig']['NetworkMode'],'mounts':info['Mounts'],'tmpfs':info['HostConfig']['Tmpfs'],'security_opt':info['HostConfig']['SecurityOpt']})
        record['seccomp']=json.loads((PRIVATE/'seccomp-evidence.json').read_text())
        record['libpq_header_sha256']=hashlib.sha256((PRIVATE/'libpq-fe.h').read_bytes()).hexdigest()
        record['kernel']=ex('uname','-r').stdout.strip()
        record['clone3_default']=('Prior preserved R1 default-profile errno38' if ROUND2 or MEASURE else cmd(['docker','exec','--user','postgres',CONTROL,'/usr/local/bin/clone3-probe'],ok=False).stdout)
        record['clone3_scoped']=ex('/usr/local/bin/clone3-probe').stdout
        ex('mkdir','-p','/tmp/pgsock')
        ex('mkdir','-p','/run/flooow-watchdog',user='0');ex('chown','999:999','/run/flooow-watchdog',user='0');ex('chmod','0700','/run/flooow-watchdog',user='0')
        ex('initdb','-D','/tmp/pgdata','--auth=trust','--no-locale')
        ex('pg_ctl','-D','/tmp/pgdata','-l','/tmp/setup.log','-o',"-k /tmp/pgsock -c listen_addresses=''",'-w','start')
        ex('createdb','-h','/tmp/pgsock','native_fixture')
        roles=['test_verifier','test_issuer','test_executor','test_auditor']
        for n in roles:sql('CREATE ROLE '+n+' LOGIN NOINHERIT NOSUPERUSER NOCREATEROLE NOCREATEDB NOREPLICATION NOBYPASSRLS;')
        sql('REVOKE CONNECT ON DATABASE postgres FROM PUBLIC; REVOKE CONNECT ON DATABASE template1 FROM PUBLIC;')
        sql('CREATE TABLE public.flooow_test_binding(slot int PRIMARY KEY,role_oid oid UNIQUE NOT NULL,role_name text UNIQUE NOT NULL); REVOKE ALL ON public.flooow_test_binding FROM PUBLIC;')
        oids=[]
        for i,n in enumerate(roles):
            oid=int(sql("SELECT oid FROM pg_catalog.pg_roles WHERE rolname='"+n+"';").stdout.strip());oids.append(oid)
            sql("INSERT INTO public.flooow_test_binding VALUES("+str(i+1)+','+str(oid)+",'"+n+"');")
        dboid=int(sql("SELECT oid FROM pg_catalog.pg_database WHERE datname='native_fixture';").stdout.strip())
        record['synthetic_role_oids']=dict(zip(roles,oids));record['synthetic_database_oid']=dboid
        # Private little-endian native ABI context: not the wire codec or policy.
        binary=struct.pack('<6I64s64s64s64s64s16s16s16s32s32s32sQ',0x00900001,dboid,*oids,b'native_fixture',*[n.encode() for n in roles],b'B'*16,b'D'*16,b'I'*16,b'\0'*32,b'F'*32,b'P'*32,5000000)
        assert len(binary)==496
        (PRIVATE/'fixture-context.bin').write_bytes(binary)
        cmd(['docker','cp',str(PRIVATE/'fixture-context.bin'),NAME+':/usr/local/fixture-context.bin'])
        stop_pg();begin=time.monotonic_ns();launch();record['cold_supervised_startup_us']=(time.monotonic_ns()-begin)/1000
        sql("CREATE FUNCTION public.flooow_test_login() RETURNS event_trigger AS '/usr/local/lib/flooow_test_login','flooow_test_login' LANGUAGE C SECURITY DEFINER SET search_path=pg_catalog; REVOKE ALL ON FUNCTION public.flooow_test_login() FROM PUBLIC; CREATE EVENT TRIGGER flooow_test_login_event ON login EXECUTE FUNCTION public.flooow_test_login(); ALTER EVENT TRIGGER flooow_test_login_event ENABLE ALWAYS;")
        for role in roles:
            r=sql('SELECT current_user,current_database(),pg_backend_pid();',role,ok=False);case('native_login_'+role,r.returncode==0,{'stdout':r.stdout,'stderr':r.stderr})
        if any(t['result']=='FAIL' for t in record['tests']):raise RuntimeError('Positive native admission failed; stop before claiming denial coverage')
        for i in range(20):
            begin=time.monotonic_ns();r=sql('SELECT 1;',roles[i%4],ok=False);record['samples'].append({'sample':i,'role':roles[i%4],'client_process_total_us':(time.monotonic_ns()-begin)/1000,'exit':r.returncode})
        if MEASURE:
            r=ex('env','PGOPTIONS=-c event_triggers=false','psql','-X','-w','-h','/tmp/pgsock','-U','test_verifier','-d','native_fixture','-At','-c','SELECT 1;',ok=False)
            case('service_startup_trigger_bypass_denied',r.returncode!=0 and 'permission denied' in r.stderr,{'exit':r.returncode,'stderr':r.stderr})
            for label,workload in [('CPU_CONTENTION',['sh','-c','i=0; while [ "$i" -lt 300000 ]; do i=$((i+1)); done']),('OVERLAY_IO_CONTENTION',['dd','if=/dev/zero','of=/usr/local/test-io/test.bin','bs=1M','count=16','conv=fsync'])]:
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    load=pool.submit(ex,*workload)
                    for i in range(3):
                        start=time.monotonic_ns();r=sql('SELECT 1;','test_verifier',ok=False);record['samples'].append({'scenario':label,'sample':i,'client_process_total_us':(time.monotonic_ns()-start)/1000,'exit':r.returncode})
                    result=load.result(timeout=20);record.setdefault('load_controls',[]).append({'scenario':label,'exit':result.returncode,'stderr':result.stderr})
            log=ex('cat','/tmp/native.log').stdout;(OUT/'NATIVE-RUNTIME.log').write_bytes(log.encode())
            record['limitations']+=['Three samples per load scenario are exploratory only; overlap/scheduler tails and security margins are not qualified.','No JVM is involved in this native/Python fixture; GC/JVM stalls not measured.','Continuous watchdog observation/freshness/signaling timing, full drain reconciliation and ambiguous COMMIT were not implemented or numerically qualified.']
            return record
        if ROUND2:
            case('pure_frame_parser',True,ex('/usr/local/bin/flooow-test-frame').stdout)
            ex('touch','/run/flooow-watchdog/repeat-anchor');r=sql('SELECT 1;','test_verifier',ok=False);ex('rm','-f','/run/flooow-watchdog/repeat-anchor')
            log=ex('cat','/tmp/native.log').stdout;case('same_anchor_idempotent',r.returncode==0 and '"duplicate":true' in log,{'stderr':r.stderr})
            for flag in ['wrong-deployment','wrong-incarnation','stale-epoch','wrong-database','wrong-slot','bad-version','partial-frame']:
                ex('touch','/run/flooow-watchdog/'+flag);denied(flag);ex('rm','-f','/run/flooow-watchdog/'+flag)
            ex('mv','/run/flooow-watchdog/enrollment-v1.sock','/run/flooow-watchdog/isolated.sock');denied('socket_absent');ex('mv','/run/flooow-watchdog/isolated.sock','/run/flooow-watchdog/enrollment-v1.sock')
            ex('chmod','0777','/run/flooow-watchdog');denied('unsafe_namespace_permissions');ex('chmod','0700','/run/flooow-watchdog')
            if ROUND3:
                ex('mv','/run/flooow-watchdog/enrollment-v1.sock','/run/flooow-watchdog/real.sock')
                ex('sh','-c','/usr/local/bin/flooow-test-fake-receiver > /tmp/fake.log 2>&1 &')
                deadline=time.monotonic()+3
                while time.monotonic()<deadline:
                    if ex('test','-S','/run/flooow-watchdog/enrollment-v1.sock',ok=False).returncode==0:break
                    time.sleep(.05)
                denied('receiver_impersonation_anchor_mismatch');ex('mv','/run/flooow-watchdog/real.sock','/run/flooow-watchdog/enrollment-v1.sock')
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    lock=pool.submit(sql,'BEGIN; LOCK TABLE public.flooow_test_binding IN ACCESS EXCLUSIVE MODE; SELECT pg_sleep(7); ROLLBACK;')
                    deadline=time.monotonic()+3
                    while time.monotonic()<deadline:
                        if sql("SELECT count(*) FROM pg_locks WHERE relation='public.flooow_test_binding'::regclass AND mode='AccessExclusiveLock' AND granted;").stdout.strip()=='1':break
                        time.sleep(.05)
                    start=time.monotonic_ns();r=sql('SELECT 1;','test_verifier',ok=False);elapsed=(time.monotonic_ns()-start)/1000
                    case('SPI_lock_wait_bounded',r.returncode!=0 and 'statement timeout' in r.stderr,{'stderr':r.stderr,'client_elapsed_us':elapsed});lock.result(timeout=10)
                ex('touch','/run/flooow-watchdog/catalog-stall');denied('receiver_catalog_wait_bounded');ex('rm','-f','/run/flooow-watchdog/catalog-stall')
            r=ex('psql','-X','-w','-h','/tmp/pgsock','-U','test_verifier','-d','postgres','-At','-c','SELECT 1;',ok=False);case('unguarded_database_connect_denied',r.returncode!=0,{'stderr':r.stderr})
            # Two simultaneous physical backends in one slot must both enroll.
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                results=list(pool.map(lambda _:sql('SELECT pg_sleep(0.2);','test_verifier',ok=False),range(2)))
            case('distinct_live_anchors_same_slot',all(r.returncode==0 for r in results),{'exits':[r.returncode for r in results]})
            sql('CREATE ROLE test_membership NOLOGIN; GRANT test_membership TO test_verifier;');denied('role_membership_mismatch');sql('REVOKE test_membership FROM test_verifier;')
        denied('no_direct_SQL_enrollment','SELECT public.flooow_test_login();')
        denied('no_service_trigger_disable','SET event_triggers=false;')
        denied('no_service_replication_role_disable',"SET session_replication_role='replica';")
        denied('no_service_header_write','DELETE FROM public.flooow_test_binding;')
        sql('DELETE FROM public.flooow_test_binding WHERE slot=1;');denied('missing_header_login');sql("INSERT INTO public.flooow_test_binding VALUES(1,"+str(oids[0])+",'test_verifier');")
        sql('ALTER ROLE test_verifier RENAME TO renamed_verifier;');denied('role_name_mismatch',role='renamed_verifier');sql('ALTER ROLE renamed_verifier RENAME TO test_verifier;')
        sql('ALTER ROLE test_verifier INHERIT;');denied('role_attribute_mismatch');sql('ALTER ROLE test_verifier NOINHERIT;')
        ex('touch','/run/flooow-watchdog/drop-ack');denied('lost_ACK');ex('rm','-f','/run/flooow-watchdog/drop-ack')
        ex('touch','/run/flooow-watchdog/delay-ack');denied('late_ACK');ex('rm','-f','/run/flooow-watchdog/delay-ack')
        if ROUND2:
            sql('DROP ROLE test_issuer; CREATE ROLE test_issuer LOGIN NOINHERIT NOSUPERUSER NOCREATEROLE NOCREATEDB NOREPLICATION NOBYPASSRLS;');denied('role_recreation_OID_mismatch',role='test_issuer')
        # Native death observation is asserted from actual receiver log, not client close alone.
        log=ex('cat','/tmp/native.log').stdout;case('backend_exit_invalidates_anchor','backend_exit_invalidated' in log,{'event_count':log.count('backend_exit_invalidated')})
        (OUT/'NATIVE-RUNTIME.log').write_bytes(log.encode())
        before=sql('SELECT pg_postmaster_start_time();').stdout.strip();stop_pg()
        # Wait for independent supervisor/receiver generation observation before rebootstrap.
        end=time.monotonic()+5
        while time.monotonic()<end:
            tail=ex('cat','/tmp/native.log',ok=False).stdout
            if 'supervisor_verified_child_drain' in tail:break
            time.sleep(.1)
        case('postmaster_restart_invalidates_generation','supervisor_generation_loss' in tail and 'supervisor_verified_child_drain' in tail,{'log_tail':tail[-1600:]})
        (OUT/'FIRST-GENERATION.log').write_bytes(tail.encode())
        begin=time.monotonic_ns();launch();record['rebootstrap_us']=(time.monotonic_ns()-begin)/1000
        after=sql('SELECT pg_postmaster_start_time();').stdout.strip();r=sql('SELECT 1;','test_verifier',ok=False)
        case('fresh_physical_login_after_rebootstrap',before!=after and r.returncode==0,{'before':before,'after':after,'stderr':r.stderr})
        if ROUND2:
            # Controlled live backend, then kill receiver using supervisor-retained fd.
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                held=pool.submit(sql,'SELECT pg_sleep(20);','test_verifier',False)
                deadline=time.monotonic()+5
                while time.monotonic()<deadline:
                    if sql("SELECT count(*) FROM pg_stat_activity WHERE usename='test_verifier' AND wait_event='PgSleep';").stdout.strip()=='1':break
                    time.sleep(.1)
                ex('touch','/run/flooow-watchdog/kill-receiver');held_result=held.result(timeout=10)
                case('receiver_crash_drains_live_backend',held_result.returncode!=0,{'stderr':held_result.stderr})
            deadline=time.monotonic()+5
            while time.monotonic()<deadline:
                current=ex('cat','/tmp/native.log',ok=False).stdout
                if 'supervisor_verified_child_drain' in current:break
                time.sleep(.1)
            case('receiver_restart_exclusion','supervisor_verified_child_drain' in current,{'tail':current[-1600:]})
            (OUT/'RECEIVER-CRASH.log').write_bytes(current.encode());ex('rm','-f','/run/flooow-watchdog/kill-receiver')
            launch();r=sql('SELECT 1;','test_verifier',ok=False);case('receiver_restart_fresh_rebootstrap',r.returncode==0,{'stderr':r.stderr})
        if ROUND3:
            # Measured load experiments, not operating bound selection.
            for label,workload in [('CPU_CONTENTION',['sh','-c','i=0; while [ "$i" -lt 300000 ]; do i=$((i+1)); done']),('OVERLAY_IO_CONTENTION',['dd','if=/dev/zero','of=/usr/local/test-io.bin','bs=1M','count=16','conv=fsync'])]:
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    load=pool.submit(ex,*workload)
                    for i in range(3):
                        start=time.monotonic_ns();r=sql('SELECT 1;','test_verifier',ok=False);record['samples'].append({'scenario':label,'sample':i,'client_process_total_us':(time.monotonic_ns()-start)/1000,'exit':r.returncode})
                    result=load.result(timeout=20);record.setdefault('load_controls',[]).append({'scenario':label,'exit':result.returncode,'stderr':result.stderr})
        # Receiver kill via retained self-created handle in a controlled tool, never numeric kill.
        record['limitations']+=['Native fixture header is a minimal protected role/slot table, not full V043 registration or original-attestation parity.','General UTF-8 NFC parser qualification pending; prototype conservatively rejects non-ASCII fixture names.','Independent continuing watchdog/freshness, effect/drain reconciliation and current approval custody are NOT qualified by enrollment samples.','Receiver restart/fork/replay/fd-substitution/socket replacement stress remain additional required cases unless separately recorded.','Observed timing uses experimental abort controls only; no numeric policy approved.']
    except Exception as e:
        record['failure']=str(e);record['traceback']=traceback.format_exc();print('QUALIFICATION_FAILURE='+str(e),flush=True)
    finally:
        # Capture logs before deleting only exact labeled owned container IDs.
        for filename,path in [('FINAL-NATIVE.log','/tmp/native.log'),('SETUP.log','/tmp/setup.log')]:
            r=ex('cat',path,ok=False);(OUT/filename).write_bytes((r.stdout+r.stderr).encode())
        record['build_hashes']=ex('sha256sum','/usr/local/lib/flooow_test_login.so','/usr/local/bin/flooow-test-receiver','/usr/local/bin/flooow-test-supervisor',ok=False).stdout
        record['source_hashes']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).parent.iterdir() if p.is_file()}
        record['cleanup']=[]
        for n in ([NAME] if ROUND2 or MEASURE else [NAME,CONTROL]):
            r=cmd(['docker','inspect',n],ok=False)
            if not r.returncode:
                i=json.loads(r.stdout)[0];assert i['Image']==IMAGE and i['Config']['Labels'].get('flooow.scope')==SCOPE
                x=cmd(['docker','rm','-f',i['Id']],ok=False);record['cleanup'].append({'name':n,'id':i['Id'],'removed':x.returncode==0})
        record['plaintext_credentials_created']=False
        record['full_gate']='HOLD'
        (OUT/'QUALIFICATION.json').write_bytes((json.dumps(record,indent=2)+'\n').encode())
    return record
if __name__=='__main__':
    outcome=main()
    raise SystemExit(1 if outcome.get('failure') or any(t['result']!='PASS' for t in outcome['tests']) else 0)
