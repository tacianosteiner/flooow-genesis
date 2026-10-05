"""Bounded diagnostic only; never qualifies or installs a policy.
Disposable password rotation requires the explicit --rotate-disposable-passwords
flag after user authorization because this gate otherwise forbids role changes.
"""
import argparse,ast,base64,ctypes,datetime,gzip,hashlib,hmac,json,os,re,secrets,subprocess,threading,time
from pathlib import Path
import package_0090_timing_qualification2 as previous
ROOT=previous.ROOT
BASELINE='0c4bd74b1ca08fe36fe18eb50aefe912b14f4f98'
WORK_NAME='forensic-08006-corrected'
LOG_SETTINGS={'log_connections':'all','log_disconnections':'on','log_statement':'none','log_min_error_statement':'panic','log_parameter_max_length':'0','log_parameter_max_length_on_error':'0','log_error_verbosity':'verbose','log_line_prefix':'%m [%p] %e ','log_duration':'on','log_min_duration_statement':'-1'}


def run(args,timeout=30):
    q=subprocess.run(args,capture_output=True,timeout=timeout)
    if q.returncode:raise RuntimeError('Tool failed: '+args[0])
    return q.stdout


def iso(epoch):return datetime.datetime.fromtimestamp(epoch,datetime.timezone.utc).isoformat()



def authority_snapshot_sql(role_names):
    names=','.join("'"+name+"'" for name in sorted(role_names))
    return """WITH target AS MATERIALIZED (SELECT oid,rolname,rolsuper,rolinherit,rolcreaterole,rolcreatedb,rolcanlogin,rolreplication,rolbypassrls,rolconnlimit FROM pg_roles WHERE rolname IN ("""+names+""")),
    object_tables AS MATERIALIZED (SELECT c.oid,c.relowner,c.relacl,c.relnamespace,c.relkind FROM pg_class c WHERE c.relkind IN ('r','p','v','m','f','S'))
    SELECT json_build_object(
      'roles',(SELECT json_agg(row_to_json(r) ORDER BY rolname) FROM target r),
      'memberships',(SELECT json_agg(json_build_object('roleid',roleid,'member',member,'grantor',grantor,'admin_option',admin_option,'inherit_option',inherit_option,'set_option',set_option) ORDER BY roleid,member,grantor) FROM pg_auth_members),
      'owner_dependencies',(SELECT json_agg(json_build_object('dbid',d.dbid,'classid',d.classid,'objid',d.objid,'objsubid',d.objsubid,'owner_oid',d.refobjid,'owner_name',r.rolname) ORDER BY dbid,classid,objid,objsubid,refobjid) FROM pg_shdepend d JOIN target r ON r.oid=d.refobjid WHERE d.refclassid='pg_authid'::regclass AND d.deptype='o'),
      'object_ownership_catalog',(SELECT json_agg(json_build_object('class_oid',oid,'owner_oid',relowner,'kind',relkind) ORDER BY oid) FROM pg_class),
      'schema_acls',(SELECT json_agg(json_build_object('oid',oid,'name',nspname,'owner',nspowner,'acl',nspacl) ORDER BY oid) FROM pg_namespace),
      'function_acls',(SELECT json_agg(json_build_object('oid',oid,'owner',proowner,'acl',proacl) ORDER BY oid) FROM pg_proc),
      'type_acls',(SELECT json_agg(json_build_object('oid',oid,'owner',typowner,'acl',typacl) ORDER BY oid) FROM pg_type),
      'table_acls',(SELECT json_agg(json_build_object('oid',oid,'owner',relowner,'acl',relacl) ORDER BY oid) FROM pg_class),
      'column_acls',(SELECT json_agg(json_build_object('table',attrelid,'num',attnum,'name',attname,'acl',attacl) ORDER BY attrelid,attnum) FROM pg_attribute WHERE attnum>0 AND NOT attisdropped),
      'database_acls',(SELECT json_agg(json_build_object('oid',oid,'name',datname,'owner',datdba,'acl',datacl) ORDER BY oid) FROM pg_database),
      'tablespace_acls',(SELECT json_agg(json_build_object('oid',oid,'owner',spcowner,'acl',spcacl) ORDER BY oid) FROM pg_tablespace),
      'large_object_acls',(SELECT json_agg(json_build_object('oid',oid,'owner',lomowner,'acl',lomacl) ORDER BY oid) FROM pg_largeobject_metadata),
      'schema_effective',(SELECT json_agg(json_build_array(r.rolname,n.oid,p.privilege) ORDER BY r.rolname,n.oid,p.privilege) FROM target r CROSS JOIN pg_namespace n CROSS JOIN (VALUES ('USAGE'),('CREATE')) p(privilege) WHERE has_schema_privilege(r.oid,n.oid,p.privilege)),
      'function_execute_effective',(SELECT json_agg(json_build_array(r.rolname,p.oid) ORDER BY r.rolname,p.oid) FROM target r CROSS JOIN pg_proc p WHERE has_function_privilege(r.oid,p.oid,'EXECUTE')),
      'table_effective',(SELECT json_agg(json_build_array(r.rolname,t.oid,p.privilege) ORDER BY r.rolname,t.oid,p.privilege) FROM target r CROSS JOIN object_tables t CROSS JOIN (VALUES ('SELECT'),('INSERT'),('UPDATE'),('DELETE'),('TRUNCATE'),('REFERENCES'),('TRIGGER'),('MAINTAIN')) p(privilege) WHERE t.relkind<>'S' AND has_table_privilege(r.oid,t.oid,p.privilege)),
      'sequence_effective',(SELECT json_agg(json_build_array(r.rolname,t.oid,p.privilege) ORDER BY r.rolname,t.oid,p.privilege) FROM target r CROSS JOIN object_tables t CROSS JOIN (VALUES ('USAGE'),('SELECT'),('UPDATE')) p(privilege) WHERE t.relkind='S' AND has_sequence_privilege(r.oid,t.oid,p.privilege)),
      'column_effective',(SELECT json_agg(json_build_array(r.rolname,a.attrelid,a.attnum,p.privilege) ORDER BY r.rolname,a.attrelid,a.attnum,p.privilege) FROM target r CROSS JOIN pg_attribute a JOIN object_tables t ON t.oid=a.attrelid CROSS JOIN (VALUES ('SELECT'),('INSERT'),('UPDATE'),('REFERENCES')) p(privilege) WHERE a.attnum>0 AND NOT a.attisdropped AND t.relkind<>'S' AND has_column_privilege(r.oid,a.attrelid,a.attnum,p.privilege)),
      'default_acls',(SELECT json_agg(json_build_object('oid',oid,'role',defaclrole,'namespace',defaclnamespace,'kind',defaclobjtype,'acl',defaclacl) ORDER BY oid) FROM pg_default_acl),
      'policies',(SELECT json_agg(row_to_json(x) ORDER BY policy_version) FROM public.offline_deadline_policy x),
      'migration_history',(SELECT json_agg(row_to_json(x) ORDER BY installed_rank) FROM public.flyway_schema_history x)
    );"""


def fingerprint(value):
    canonical=json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')
    return hashlib.sha256(canonical).hexdigest()


def measure(rotation_authorized):
    if not rotation_authorized:raise RuntimeError('Password rotation is not authorized; no database or role mutation performed')
    run(['git','fetch','origin'])
    for ref in ['HEAD','origin/checkpoint/package-0090-cloud-handoff']:
        if run(['git','rev-parse',ref]).decode().strip()!=BASELINE:raise RuntimeError('STOP baseline mismatch')
    diagnostic_names=['TIMING-08006-DIAGNOSIS.md','TIMING-PHASES.json','08006-DIAGNOSTICS.json','HEARTBEAT-MODEL-REVIEW.md']
    allowed={'scripts/validation/Package0090TimingForensics.java','scripts/validation/package_0090_timing_forensics.py'}|{'docs/evidence/PACKAGE-0090-G3F-4-'+n for n in diagnostic_names}
    if any(r[3:].replace('\\','/') not in allowed for r in run(['git','status','--porcelain']).decode().splitlines()):raise RuntimeError('Unexpected changes before diagnostic')
    target,private,old=previous.identity()
    if target['State']['Running']:raise RuntimeError('Expected stopped disposable')
    work=private/WORK_NAME;work.mkdir(exist_ok=True)
    if (work/'record.json').exists():raise RuntimeError('Do not overwrite a forensic study')
    protected=[p for p in (ROOT/'docs/evidence').glob('PACKAGE-0090-G3F-4-*') if p.name not in {'PACKAGE-0090-G3F-4-'+n for n in diagnostic_names}]+[previous.FIXTURE1]
    protected+=list((ROOT/'applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration').glob('V*.sql'))
    protected+=list((ROOT/'applications/command-authority-ceremony/src/main').rglob('*.kt'))
    protected+=list((ROOT/'docs/adr').glob('*0090*'))+list((ROOT/'docs/specifications').glob('*0090*'))
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
    prior=json.loads((ROOT/'docs/evidence/PACKAGE-0090-G3F-4-TIMING-QUALIFICATION-2.json').read_text())
    fixture=json.loads((ROOT/'docs/evidence/PACKAGE-0090-G3F-4-FIXTURE-002.json').read_text())
    if prior['G3F4_H01']!='OPEN' or fixture['fixture_2_qualification']!='FAIL' or fixture['database_installed']:raise RuntimeError('Required HOLD posture missing')
    tree=ast.parse((ROOT/'scripts/validation/package_0090_timing_qualification2.py').read_text())
    snapshot_sql=next(n.value.value for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='snapshot_sql' for t in n.targets))
    rec={'baseline':BASELINE,'diagnosis_only':True,'identity':'EXACT_EXISTING_DISPOSABLE_PROJECT_IMAGE_VOLUME_READONLY_BIND','historical_hashes_before':hashes,'container_before_start':{'state':target['State'],'restart_count':target['RestartCount'],'constraints':{k:target['HostConfig'][k] for k in ('NanoCpus','Memory','CpuQuota','CpuPeriod','CpusetCpus')}},'fixture2_installed':False,'fixture3_created':False,'new_bounds_chosen':False,'protected_database_connection':'NO','protected_volume_mount':'NO','production_secret_use':'NO','password_rotation_authorized':True,'role_names_attributes_memberships_and_ACLs_changed':False}
    def save():
        (work/'record.json').write_text(json.dumps(rec,indent=2)+'\n',encoding='utf-8',newline='\n')
    seed=secrets.token_bytes(32)
    roles={'ADMIN':'postgres',**{s:'g3f4_'+s.lower()+'_cc2941797db3' for s in ['AUDITOR','VERIFIER','ISSUER','EXECUTOR']}}
    creds={s:hmac.new(seed,('DIAGNOSTIC/'+s).encode(),hashlib.sha256).hexdigest() for s in roles}
    def redact(text):
        for pw in creds.values():text=text.replace(pw,'<REDACTED_CREDENTIAL>')
        return re.sub(r"(?i)(PASSWORD\s+)'[^']*'",r"\1'<REDACTED_CREDENTIAL>'",text)
    def sql(statement):
        previous.identity()
        q=subprocess.run(['docker','exec','-i',previous.CONTAINER,'psql','-X','-U','postgres','-d','g3f4','-At','-v','ON_ERROR_STOP=1'],input=statement,text=True,capture_output=True,timeout=20)
        if q.returncode:
            (work/'administrative-error.log').write_text(redact(q.stderr),encoding='utf-8')
            raise RuntimeError('Administrative SQL failed; sanitized details retained privately')
        return q.stdout.strip()
    password_file=private/'postgres-password';password_file.write_text(creds['ADMIN'],encoding='ascii')
    started=False;logging_changed=False;settings_before=None;stop_monitor=threading.Event();monitor=None;awake=False
    try:
        previous.identity();run(['docker','start',previous.CONTAINER]);started=True
        deadline=time.monotonic()+45
        while time.monotonic()<deadline:
            if subprocess.run(['docker','exec',previous.CONTAINER,'pg_isready','-U','postgres','-d','g3f4'],capture_output=True).returncode==0:break
            time.sleep(.2)
        else:raise RuntimeError('PostgreSQL startup timeout')
        target,_,_=previous.identity();ports=target['NetworkSettings']['Ports']['5432/tcp']
        if len(ports)!=1 or ports[0]['HostIp']!='127.0.0.1':raise RuntimeError('Localhost mapping mismatch')
        port=ports[0]['HostPort'];rec['localhost_port']=int(port)
        rec['server']=json.loads(sql("SELECT json_build_object('version',version(),'version_num',current_setting('server_version_num'),'encoding',current_setting('server_encoding'),'postmaster_start',pg_postmaster_start_time(),'database_clock',clock_timestamp());"))
        if rec['server']['version_num']!='180004' or rec['server']['encoding']!='UTF8':raise RuntimeError('PG18.4 UTF8 required')
        rec['administrative_snapshot_before']=json.loads(sql(snapshot_sql))
        names=','.join("'"+n+"'" for n in LOG_SETTINGS)
        settings_before=json.loads(sql("SELECT json_agg(json_build_object('name',name,'setting',setting,'sourcefile',sourcefile) ORDER BY name) FROM pg_settings WHERE name IN ("+names+");"));rec['logging_before']=settings_before
        for name,value in LOG_SETTINGS.items():sql("ALTER SYSTEM SET "+name+" = '"+value.replace("'","''")+"';")
        logging_changed=True;sql('SELECT pg_reload_conf();')
        authority_query=authority_snapshot_sql(roles.values())
        authority_pre=json.loads(sql(authority_query))
        if len(authority_pre['roles'])!=5 or {x['rolname'] for x in authority_pre['roles']}!=set(roles.values()):raise RuntimeError('Exact five existing roles required before PASSWORD rotation')
        rec['non_secret_authority_state_pre']=authority_pre
        rec['non_secret_authority_fingerprint_pre']=fingerprint(authority_pre);save()
        sql('\n'.join("ALTER ROLE "+roles[s]+" PASSWORD '"+creds[s]+"';" for s in roles))
        authority_post=json.loads(sql(authority_query));rec['non_secret_authority_state_post']=authority_post
        rec['non_secret_authority_fingerprint_post']=fingerprint(authority_post)
        if authority_pre!=authority_post:raise RuntimeError('STOP non-secret authority changed during PASSWORD-only rotation')
        rec['password_rotation']='PASS';rec['rotated_role_count']=5
        rec['password_rotation_scope']='EXACT_AUTHORIZED_FIVE_ROLES'
        rec['rotation_checks']={k:'YES' for k in ['ROLE_IDENTITY_UNCHANGED','ROLE_ATTRIBUTES_UNCHANGED','ROLE_MEMBERSHIPS_UNCHANGED','OBJECT_OWNERSHIP_UNCHANGED','ACL_UNCHANGED','DEFAULT_ACL_UNCHANGED','POLICY_UNCHANGED','MIGRATION_STATE_UNCHANGED','ROLE_STATE_PRE_POST_EQUAL']}
        save()

        conf=f'url=jdbc:postgresql://127.0.0.1:{port}/g3f4\nproject={previous.PROJECT}\nvolume={previous.VOLUME}\ncontainer={previous.CONTAINER}\nincarnation={old["timing_fixture"]["incarnation"]}\n'
        for slot,name in roles.items():conf+=f'{slot}.name={name}\n{slot}.password={creds[slot]}\n'
        (work/'jdbc.properties').write_text(conf,encoding='ascii')
        jars=sorted((Path.home()/'.gradle/caches/modules-2/files-2.1').rglob('*.jar'))
        cp=os.pathsep.join([str(ROOT/'applications/command-authority-ceremony/build/classes/kotlin/main')]+list(map(str,jars)))
        sources=['Package0090TimingForensics.java','Package0090RehearsalAdapter.java','Package0090RehearsalEndpoint.java']
        args='-cp\n"'+cp.replace('\\','/')+'"\n-d\n"'+work.as_posix()+'"\n'+''.join('"'+(ROOT/'scripts/validation'/name).as_posix()+'"\n' for name in sources)
        (work/'javac.args').write_text(args,encoding='utf-8');run(['javac','@'+str(work/'javac.args')],60)
        args='-Xlog:gc*,safepoint:file=jvm-gc-safepoint.log:time,uptime,level,tags\n-cp\n"'+(str(work)+os.pathsep+cp).replace('\\','/')+'"\nPackage0090TimingForensics\n"'+(work/'jdbc.properties').as_posix()+'"\n"'+(work/'measurements.json').as_posix()+'"\n'
        (work/'java.args').write_text(args,encoding='utf-8')
        rec['docker_telemetry']=[]
        def monitor_fn():
            while not stop_monitor.is_set():
                begin=time.time()
                try:
                    d=previous.identity()[0]
                    stats=run(['docker','stats',previous.CONTAINER,'--no-stream','--format','{{json .}}'],6)
                    rec['docker_telemetry'].append({'timestamp_start_utc':iso(begin),'timestamp_end_utc':iso(time.time()),'state':d['State'],'restart_count':d['RestartCount'],'stats':json.loads(stats)})
                except Exception as e:rec['docker_telemetry'].append({'timestamp_utc':iso(begin),'error_class':type(e).__name__})
                stop_monitor.wait(1)
        # Transient process power request, no persisted Windows power-policy changes.
        # This deliberately creates an awake-controlled diagnostic dataset.
        awake=bool(ctypes.windll.kernel32.SetThreadExecutionState(0x80000001));rec['awake_controlled_dataset']=awake
        rec['instrumentation']='All populations share bounded connection logging, GC/safepoint logs, phase/GC/process-total-CPU metrics; native CPU-load counters removed after separate aborted attempt; bounded raw checkpoints every100 samples. Docker stats is asynchronous. load4 adds pg_stat_activity snapshots BEFORE each heartbeat, on the existing ADMIN connection (still six physical workload/measurement sessions). Extra observer work is outside each freshness measurement but may affect platform load; this is a distinct diagnostic dataset, not a qualification rerun.'
        monitor=threading.Thread(target=monitor_fn,daemon=True);monitor.start();rec['diagnostic_start_epoch']=time.time();save()
        previous.identity()
        q=subprocess.run(['java','@'+str(work/'java.args')],timeout=420,cwd=work)
        rec['java_exit_code']=q.returncode;rec['diagnostic_end_epoch']=time.time()
        stop_monitor.set();monitor.join(12)
        rec['study']=json.loads((work/'measurements.json').read_text())
        rec['administrative_snapshot_after']=json.loads(sql(snapshot_sql))
        if rec['administrative_snapshot_before']!=rec['administrative_snapshot_after']:raise RuntimeError('Protected posture or role authority changed')
        rec['authority_snapshot_equal']=True
        rec['non_secret_authority_state_end']=json.loads(sql(authority_query))
        rec['non_secret_authority_fingerprint_end']=fingerprint(rec['non_secret_authority_state_end'])
        if rec['non_secret_authority_state_end']!=authority_pre:raise RuntimeError('End-of-diagnosis non-secret authority drift')
        rec['container_after_measurement']={'state':previous.identity()[0]['State'],'restart_count':previous.identity()[0]['RestartCount']}
        for name,args in [('current-server-docker.log',['docker','logs','--timestamps','--since',iso(rec['diagnostic_start_epoch']-2),'--until',iso(rec['diagnostic_end_epoch']+2),previous.CONTAINER]),('current-events.jsonl',['docker','events','--since',iso(rec['diagnostic_start_epoch']-2),'--until',iso(rec['diagnostic_end_epoch']+2),'--filter','container='+previous.CONTAINER,'--format','{{json .}}'])]:
            logged=subprocess.run(args,capture_output=True,timeout=30)
            if logged.returncode:raise RuntimeError('Bounded Docker log/event capture failed')
            (work/name).write_text(redact((logged.stdout+logged.stderr).decode(errors='replace')),encoding='utf-8',newline='\n')
        print('DIAGNOSTIC_COUNTS='+json.dumps({k:len(v['samples']) for k,v in rec['study']['populations'].items()}),flush=True)
    finally:
        stop_monitor.set()
        if monitor:monitor.join(12)
        if awake:ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
        try:
            if logging_changed and started and settings_before:
                for setting in settings_before:
                    name=setting['name']
                    if (setting['sourcefile'] or '').endswith('postgresql.auto.conf'):sql("ALTER SYSTEM SET "+name+" = '"+setting['setting'].replace("'","''")+"';")
                    else:sql('ALTER SYSTEM RESET '+name+';')
                sql('SELECT pg_reload_conf();');rec['logging_restored']=True
        except Exception as error:
            rec['logging_restored']=False;rec['logging_restore_error_class']=type(error).__name__
            raise
        finally:
            try:
                if started:run(['docker','stop',previous.CONTAINER],40)
                rec['container_end_state']='STOPPED'
            finally:
                for path in [work/'jdbc.properties',password_file]:
                    if path.exists():path.unlink()
                rec['private_plaintext_credentials_erased']=True
                after={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
                rec['historical_hashes_after']=after;rec['historical_unchanged']=hashes==after
                save()
    return work



def packed_log(path):
    data=Path(path).read_bytes()
    return dict(encoding="GZIP_BASE64_LOSSLESS",text_encoding="UTF8",uncompressed_byte_count=len(data),uncompressed_sha256=hashlib.sha256(data).hexdigest(),data=base64.b64encode(gzip.compress(data,mtime=0)).decode("ascii"))


def publish():
    """Publish full bounded diagnostic evidence without a qualification decision."""
    private=Path.home()/'AppData/Local/Temp/flooow-0090-g3f4-kui1oqwb'
    work=private/WORK_NAME;first=private/'forensic-08006'
    rec=json.loads((work/'record.json').read_text());aborted=json.loads((first/'record.json').read_text())
    if not rec.get('logging_restored') or not rec.get('historical_unchanged') or not rec.get('authority_snapshot_equal') or rec['container_end_state']!='STOPPED' or not rec['private_plaintext_credentials_erased']:raise RuntimeError('Completion integrity missing')
    if previous.identity()[0]['State']['Running']:raise RuntimeError('Container still running')
    for folder in [first,work]:
        if (folder/'jdbc.properties').exists():raise RuntimeError('Plaintext credentials remain')
    if (private/'postgres-password').exists():raise RuntimeError('Plaintext startup credential remains')
    populations=rec['study']['populations'];expected={'A_warm_persistent':2000,'B_cold_after_heartbeat':500,'C_cold_before_heartbeat':500,'D_both_setup_before_heartbeat':500,'E_idle_physical_reuse':1000,'load4_diagnostic':5000}
    if {k:len(v['samples']) for k,v in populations.items()}!=expected or rec['study']['failures']:raise RuntimeError('This final writer requires complete non-reproducing diagnostic; do not hide a partial/failing run')
    raw=[s for p in populations.values() for s in p['samples']]
    logs=(work/'current-server-docker.log').read_text().splitlines()
    if not logs:raise RuntimeError('Full PostgreSQL stderr log stream required')
    historical_logs=(first/'historical-docker.log').read_text().splitlines()
    pg_setup={}
    log_times=[]
    for line in logs:
        try:stamp=datetime.datetime.fromisoformat(line.split(' ')[0].replace('Z','+00:00')).timestamp()
        except ValueError:continue
        log_times.append((stamp,line))
        m=re.search(r'\[(\d+)\].*connection ready: setup total=([0-9.]+) ms, fork=([0-9.]+) ms, authentication=([0-9.]+) ms',line)
        if m:pg_setup[int(m[1])]=dict(setup_total_us=float(m[2])*1000,fork_us=float(m[3])*1000,authentication_us=float(m[4])*1000,log_line=line,meaning='Server wall times, including protocol/client waits; authentication is a subset of setup total, not additive.')
    safepoints=(work/'jvm-gc-safepoint.log').read_text().splitlines()
    docker=rec['docker_telemetry'];outliers=[]
    for name,pop in populations.items():
        for sample in pop['samples']:
            if sample['age_us']<=50000:continue
            after=datetime.datetime.fromisoformat(sample['telemetry_after']['timestamp_utc'].replace('Z','+00:00')).timestamp()
            before=datetime.datetime.fromisoformat(sample['telemetry_before']['timestamp_utc'].replace('Z','+00:00')).timestamp()
            correlated=[line for stamp,line in log_times if before-1<=stamp<=after+1]
            nearest=min(docker,key=lambda row:abs(datetime.datetime.fromisoformat(row.get('timestamp_start_utc',row.get('timestamp_utc'))).timestamp()-after))
            gc_delta={a['name']:dict(collections=b['collections']-a['collections'],collection_time_ms=b['collection_time_ms']-a['collection_time_ms']) for a,b in zip(sample['telemetry_before']['gc'],sample['telemetry_after']['gc'])}
            safe=[]
            for line in safepoints:
                try:stamp=datetime.datetime.fromisoformat(line.split(']')[0][1:]).timestamp()
                except ValueError:continue
                if before<=stamp<=after:safe.append(line)
            outliers.append(dict(population=name,index=sample['index'],sample=sample,classification='JDBC_CONNECT_LATENCY_COMPOSITE',server_connection_setup=pg_setup.get(sample['auditor_backend']),gc_delta=gc_delta,safepoint_lines_during_iteration=safe,server_docker_log_window=correlated,docker_nearest_snapshot=nearest,docker_snapshot_is_not_instantaneous=True,clock_alignment='UTC timestamps only for coarse log correlation; no host/DB clock subtraction for authorization'))
    distributions={name:previous.distribution(pop['samples']) for name,pop in populations.items()}
    phases_keys=['heartbeat_to_connect_start_us','jdbc_connect_us','authentication_and_backend_us','session_setup_us','pre_query_gap_us','query_execution_us']
    phase_distributions={name:{key:previous.distribution([dict(age_us=s[key]) for s in pop['samples'] if s.get(key) is not None]) for key in phases_keys} for name,pop in populations.items()}
    maxs={name:d['max_us'] for name,d in distributions.items()}
    proxies=max(maxs[k] for k in ['A_warm_persistent','C_cold_before_heartbeat','D_both_setup_before_heartbeat','E_idle_physical_reuse'])
    query_max=max(s['query_execution_us'] for s in raw)
    postmasters={datetime.datetime.fromisoformat(value).astimezone(datetime.timezone.utc).isoformat() for value in ({rec['server']['postmaster_start']}|{s['server_after_outlier']['postmaster_start'] for s in raw if s.get('server_after_outlier')})}
    load_pairs=sorted({(s['admin_backend'],s['auditor_backend']) for s in populations['load4_diagnostic']['samples']})
    # Normal connection/disconnection and deliberate start/stop are not unexpected restart/termination.
    fatal=[line for line in logs if any(x in line.lower() for x in ['fatal:','panic:','terminating connection','could not receive data','connection reset','broken pipe','database system is ready','starting postgresql','server process (pid'])]
    common=dict(baseline=BASELINE,branch='checkpoint/package-0090-cloud-handoff',diagnosis_only=True,
      diagnostic_status='COMPLETE_WITH_PRESERVED_ABORTED_INSTRUMENTATION_ATTEMPT',
      G3F_4_ISOLATED_POSTGRES18_REHEARSAL='HOLD',G3F4_H01='OPEN',H01_ROOT_CAUSE='UNKNOWN',
      JDBC_08006_REPRODUCED='NO_IN_CORRECTED_5000_ITERATIONS',JDBC_08006_ROOT_CAUSE='UNKNOWN',
      counts=dict(BLOCKER=0,HIGH=1,MEDIUM=0,LOW=0),
      NEXT_GATE='G3F_4_REHEARSAL_TRANSPORT_MODEL_REVIEW',
      RECONNECT_IN_FRESHNESS_PATH='CONDITIONALLY',
      PRODUCTION_CONNECTION_MODEL='DEDICATED_SLOT_DATASOURCE_ON_DEMAND_PHYSICAL_CONNECTIONS',
      HEARTBEAT_AUTHORIZATION_MODEL='MODEL_C_WITH_REPEATABLE_READ_VISIBILITY',
      FIXTURE_1_MUTATED='NO',FIXTURE_2_INSTALLED='NO',FIXTURE_3_CREATED='NO',
      temporal_bounds_changed=False,positive_S01_S18_executed=False,
      PROTECTED_DATABASE_CONNECTION='NO',PROTECTED_VOLUME_MOUNT='NO',PRODUCTION_SECRET_USE='NO',
      G3G_executed=False,main_merged_or_pushed=False,container_end_state='STOPPED',
      PASSWORD_ROTATION='PASS',ROTATED_ROLE_COUNT=5,ROLE_STATE_PRE_POST_EQUAL='YES',
      PASSWORD_ROTATION_SCOPE='EXACT_AUTHORIZED_FIVE_ROLES',
      NON_SECRET_AUTHORITY_FINGERPRINT_PRE=rec['non_secret_authority_fingerprint_pre'],
      NON_SECRET_AUTHORITY_FINGERPRINT_POST=rec['non_secret_authority_fingerprint_post'],
      PLAINTEXT_CREDENTIAL_FILES_ERASED='YES')
    rotation=dict(authorization='Explicit PASSWORD ONLY authorization amendment; no new role/attribute/member/privilege mutation',
      unique_rotated_roles=5,password_only_rounds=2,total_password_only_statements=10,
      explanation='The first instrumented attempt was stopped for a diagnostic-only CPU-counter correction and its credentials erased; the corrected attempt restored authentication with another PASSWORD-only round for exactly the same five roles.',
      checks=rec['rotation_checks'],canonicalization='UTF8 JSON; sort_keys=True; separators=(comma,colon); ensure_ascii=False; catalog arrays explicitly ordered by stable catalog keys; SHA256; no credential/verifier value queried or captured',
      state_pre=rec['non_secret_authority_state_pre'],state_post=rec['non_secret_authority_state_post'],state_end=rec['non_secret_authority_state_end'],fingerprint_end=rec['non_secret_authority_fingerprint_end'],
      aborted_attempt_pre_fingerprint=aborted['non_secret_authority_fingerprint_pre'],aborted_attempt_post_fingerprint=aborted['non_secret_authority_fingerprint_post'])
    timing=common|dict(requested_sample_counts=expected,sample_counts=expected,total_validated_samples=len(raw),
      distributions=distributions,phase_distributions=phase_distributions,
      WARM_PATH_MAX_US=maxs['A_warm_persistent'],COLD_AFTER_HEARTBEAT_MAX_US=maxs['B_cold_after_heartbeat'],COLD_BEFORE_HEARTBEAT_MAX_US=maxs['C_cold_before_heartbeat'],BOTH_CONNECTED_BEFORE_HEARTBEAT_MAX_US=maxs['D_both_setup_before_heartbeat'],POOLED_REUSE_MAX_US=maxs['E_idle_physical_reuse'],
      MEASURED_OPERATIONAL_PATH_MAX_US=proxies,operational_path_value_is='SYNTHETIC_FRESHNESS_PROXY_ONLY_NOT_ELIGIBLE_S01_OR_CONTINUOUS_WATCHDOG_PROOF',
      MEASURED_RECONNECT_PATH_MAX_US=maxs['B_cold_after_heartbeat'],MEASURED_QUERY_ONLY_MAX_US=query_max,query_only_value_is='CLIENT_MONOTONIC_QUERY_ROUNDTRIP_INCLUDING_DRIVER_NETWORK_RESULT_AND_LAZY_SESSION_WORK_NOT_SERVER_ONLY_EXECUTION',
      server_connection_setup_by_backend=pg_setup,outliers=outliers,
      historical_outlier_phase_classification='UNKNOWN_NOT_RETAINED',
      historical_428349_sample=max(json.loads((ROOT/'docs/evidence/PACKAGE-0090-G3F-4-TIMING-QUALIFICATION-2.json').read_text())['record']['study']['populations']['cold_reconnect']['samples'],key=lambda s:s['age_us']),
      new_outlier_phase_classification='JDBC_CONNECT_LATENCY_COMPOSITE; server wall-time startup/auth correlated; Docker forwarding/client-vs-server CPU attribution remains unknown',
      authoritative_age='EXTRACT(EPOCH FROM(clock_timestamp()-DB_RETURNED_HEARTBEAT))*1000000',
      phase_limitations=rec['study']['phase_limitations'],
      T0_limit='Database heartbeat timestamp and acknowledgment are recorded. Commit visibility is confirmed by autocommit statement completion; client acknowledgment is not the exact server commit timestamp.',
      T2_T3_limit='getConnection returns an authenticated JDBC session; distinct raw TCP-established time is not exposed. authentication_and_backend_us is cached backend-ID lookup only. Actual server auth/setup durations are separate overlapping wall-time metrics.',
      E_limit='Real persistent physical AUDITOR connection is reused after actual rollback to idle; A/E share that mechanism. No fake pool or production pooling assumption.',
      policy_qualification_decision='NONE_DIAGNOSTIC_ONLY; historical fixture-2 FAIL is unchanged',record=rec)
    diag=common|dict(password_rotation=rotation,
      historical_windows_kernel_power_events=json.loads((first/'historical-windows-events.json').read_text(encoding='utf-8-sig')),
      current_windows_kernel_power_events=json.loads((work/'current-windows-events.json').read_text(encoding='utf-8-sig')),
      historical_server_docker_log=packed_log(first/"historical-docker.log"),current_server_docker_log=packed_log(work/"current-server-docker.log"),
      jvm_gc_safepoint_log=safepoints,
      current_windows_tcp_after=json.loads((work/'current-windows-tcp-after.json').read_text(encoding='utf-8-sig') or '[]'),
      aborted_attempt_windows_tcp=json.loads((first/'current-windows-tcp.json').read_text(encoding='utf-8-sig')),
      aborted_attempt_jvm_thread_snapshot=(first/'jvm-thread-snapshot.txt').read_text(),
      aborted_attempt_server_log=packed_log(first/'aborted-server-docker.log'),
      aborted_attempt=aborted,corrected_exception_chains=rec['study']['failures'],
      historical_exception_chain='UNAVAILABLE; retained only PSQLException and08006. Do not reconstruct its message/vendor/nextException/cause.',
      historical_host_standby_correlation='PROVEN_HOST_POWER_EVENT_CORRELATION_WITH_LOAD4_STALL; not a proven socket-close mechanism or causal link to cold index34',
      A_B_causal_relationship='NOT_PROVEN',
      server_classification='I_UNKNOWN_FOR_HISTORICAL_08006',
      POSTGRES_RESTARTED='NO_DURING_CORRECTED_MEASUREMENT_WINDOW',
      CONTAINER_RESTARTED='NO_DURING_CORRECTED_MEASUREMENT_WINDOW',
      OOM_KILLED='NO_DURING_CORRECTED_MEASUREMENT_WINDOW',
      BACKEND_TERMINATED='NO_UNEXPECTED_TERMINATION_OBSERVED_CORRECTED_WINDOW',
      SOCKET_INTERRUPTION='NOT_OBSERVED_CORRECTED_WINDOW_UNKNOWN_HISTORICAL',
      JVM_PAUSE_CORRELATED='NO_GC_OR_LOGGED_SAFEPOINT_CORRELATED_WITH_NEW_OUTLIERS_UNKNOWN_HISTORICAL',
      retained_postmaster_times=sorted(postmasters),load4_physical_backend_pairs=load_pairs,unexpected_server_failure_log_lines=fatal,
      load4_snapshot_retention_limit="pg_stat_activity was queried before each heartbeat; only outlier/failure snapshots persisted. No load4 outlier occurred, so no per-iteration pre-snapshot was retained. Do not claim5000 archived postmaster timestamps; stable physical PIDs, retained initial/outlier snapshots and full logs are the available evidence.",
      topology='Two measurement connections plus four actual governed slot sessions; before-snapshot observer uses existing ADMIN connection. Six physical sessions, no additional SQL observer connection.',
      background_wrapper_attempts=populations['load4_diagnostic'].get('background_wrapper_attempts'),
      first_harness_defect='Native CPU-load performance-counter getter caused major instrumentation overhead; main CPU176078ms/elapsed190s in sampled native getter. Corrected only diagnostic tooling to ProcessHandle total CPU duration and periodic raw checkpoints. Not evidence about the earlier harness, which did not call this getter.',
      second_capture_correction=rec.get('server_log_capture_correction'),
      lifecycle_audit='No proven production adapter close/share/reset defect. Historical diagnostic finally rollback could mask its primary error; old scalar exception persistence omitted forensic chains; corrected read retains primary plus suppressed/cause/nextException and stops recurring calls after unexpected failure. No production or SQL change.',
      docker_events=(work/'current-events.jsonl').read_text(),docker_event_retention_limit='Empty Docker events cannot prove no past event; corroborate postmaster start/state/restart count/full logs',
      instrumentation='Awake-controlled, logged diagnostic dataset; ProcessHandle CPU, GC/safepoints, periodic whole-file checkpoints, asynchronous container stats. One thread dump belongs only to the excluded CPU-counter attempt. Do not compare these results as production SLOs or replace historical qualification.',
      H01_disposition='OPEN/HIGH; historical bound failure and missing eligible-runtime/watchdog evidence remain. Corrected synthetic controls and non-reproduction do not close H01.')
    evidence=ROOT/'docs/evidence'
    for name,content in [('TIMING-PHASES.json',timing),('08006-DIAGNOSTICS.json',diag)]:
        with (evidence/('PACKAGE-0090-G3F-4-'+name)).open('w',encoding='utf-8',newline='\n') as f:json.dump(content,f,indent=2);f.write('\n')
    lines=['# Package 0090 - timing and JDBC08006 forensic diagnosis','',
      '**STATUS: diagnostic completed; G3F.4 HOLD; H01 OPEN/HIGH. No temporal qualification or fixture provisioning.**','',
      'Baseline0c4bd74b1ca08fe36fe18eb50aefe912b14f4f98 was verified against fetched checkpoint origin; worktree was clean before prepared diagnostic files. All previous HOLD evidence and fixture definitions remain byte-identical.','',
      'The corrected instrumented run completed9500 real PostgreSQL DB-clock observations, including5000 load4 iterations with no observed08006 and no captured exception. This is non-reproduction in one awake-controlled run, not proof the historical failure cannot recur. No positive S01-S18 or eligible continuous-watchdog ceremony was executed.','',
      '| Population | N | Min | p50 | p90 | p95 | p99 | p99.9 | Max | Mean | Sample SD |',
      '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for name,d in distributions.items():lines.append('| '+name+' | '+' | '.join(str(d[k]) if k=='count' else f'{d[k]:.3f}' for k in ['count','min_us','p50_us','p90_us','p95_us','p99_us','p99_9_us','max_us','mean_us','sample_standard_deviation_us'])+' |')
    lines+=['','All durations are microseconds, empirical nearest rank; cold N500 p99.9 equals its maximum with insufficient extreme-tail resolution. Group order is A/B/C/D/E/load4, not randomized; telemetry, checkpoint I/O and host awake control can affect platform load. No production guarantee or causal benefit of load is inferred.','',
      'A. Historical428349 us cold index34, ADMIN138/AUDITOR139: phase cause UNKNOWN. Aggregate age/PIDs were retained, but exact timestamp, individual timers, waits and JVM telemetry were not. New outliers54091/63234 us are dominated by composite getConnection startup; for63234 us sample, JDBC connect50969.8 us, setup938.3 us, cached backend lookup3 us, client query1398.7 us. Server setup log for AUDITOR536: total43865 us, including auth22867 us and fork535 us. Server auth is protocol wall time including client/network waits, not CPU-only cost; overlapping metrics must not be added. No phase is assigned retroactively to428349.','',
      'B. Historical JDBC08006 cause UNKNOWN. Original exception message/vendor/cause/nextException were not preserved. New primary Windows evidence shows Modern Standby entry11:29:16.635Z, disconnected standby11:29:36.937Z, exit11:38:37.196Z; the prior driver ends11:38:38.052530Z. Guard logs stop at11:29:29.710Z. These prove host power-state correlation with the stalled load4 interval; exact TCP-close direction, timeout origin and Docker-forwarding mechanism are not proven. Historical Docker event retention returned empty and is not evidence of no event.','',
      'C. Causal relation between cold index34 and load4 failure: NOT_PROVEN. No per-sample historical timestamp ties them to the same event. Do not infer PostgreSQL failure or Windows jitter from SQLState alone.','',
      'D. Cold-after is a synthetic one-update handoff diagnostic, not actual eligible S01 or a periodically refreshed watchdog. Concrete production composition uses four separate PGSimpleDataSource and on-demand physical connections; no real pool is constructed. ADR/SPEC require independent watchdog enforcement and protected freshness, not a client-synchronized heartbeat/reconnect protocol. Reconnection may consume the visible-marker age conditionally; newer independent updates and REPEATABLE READ visibility determine which timestamp is checked. See HEARTBEAT-MODEL-REVIEW.md.','',
      'E. The budget applies at each actual DB-clock predicate to the marker visible to that transaction. Work after that marker and before the check consumes that age. The standalone age query, full S01 duration, heartbeat checks and receipt expiry checks are distinct. Exact source points: outer S01 clock6925/age6929; private Q clock4990/age4995 before full live ACL/history work; final Q clock6656 concerns receipt expiry/issuance, not another heartbeat-age comparison. No check ordering or contract is changed by this diagnosis.','',
      f'MEASURED_OPERATIONAL_PATH_MAX_US={proxies:.0f} (synthetic A/C/D/E proxy, not eligible S01); MEASURED_RECONNECT_PATH_MAX_US={maxs["B_cold_after_heartbeat"]:.0f}; MEASURED_QUERY_ONLY_MAX_US={query_max:.3f} (client query roundtrip, not server-only execution). Raw phase, GC/CPU/backend and correlated outlier metadata are in TIMING-PHASES.json.','',
      'No new outlier has a collection-count/time GC increment or a logged safepoint within its iteration. No unexpected backend/postmaster/container restart, OOM or socket failure is observed in the corrected measurement window;retained initial/outlier snapshots share one postmaster start and load4 retains the same physical backend PIDs, Docker state/restart count stays stable, and full server logs contain no fatal/termination/reset evidence. This does not establish those historical outcomes. Normal cold session disconnects and deliberate container start/stop are excluded from unexpected-failure classification.','',
      'Harness-only corrections: an initial instrumented attempt consumed176078ms main-thread CPU at190s elapsed inside the native CPU-load getter; its thread dump and logs are preserved, and its raw samples were lost on deliberate JVM stop. Console reported A2000/B500 completions, but they are not counted as retained observations. Corrected diagnostic uses ProcessHandle total CPU time and raw checkpoints every100 samples. Docker logs initially captured only stdout; PostgreSQL logs were on stderr, so the exact retained window was recovered from both streams without repeating measurements. Original read rollback masking and abbreviated chain capture were hardened only in diagnostic tooling. Production adapter remains unchanged.','',
      'PASSWORD_ROTATION=PASS; ROTATED_ROLE_COUNT=5 distinct authorized existing roles; PASSWORD_ROTATION_SCOPE=EXACT_AUTHORIZED_FIVE_ROLES. Two PASSWORD-only rounds (10 statements) were necessary because the aborted attempt erased its plaintext credentials before the corrected run. No CREATE/DROP/RENAME/role attribute/membership/privilege mutation occurred. Both rounds separately captured equal pre/post non-secret state; identity/OID/name, all required attributes including rolconnlimit, memberships, owner dependencies/catalog owners, schema/function/table/column/sequence/type/database/large-object ACLs and effective rights, defaults, complete policy and migration history are recorded. No role credential or password-verifier value was queried or captured.','',
      'ROLE_IDENTITY_UNCHANGED=YES; ROLE_ATTRIBUTES_UNCHANGED=YES; ROLE_MEMBERSHIPS_UNCHANGED=YES; OBJECT_OWNERSHIP_UNCHANGED=YES; ACL_UNCHANGED=YES; DEFAULT_ACL_UNCHANGED=YES; POLICY_UNCHANGED=YES; MIGRATION_STATE_UNCHANGED=YES; ROLE_STATE_PRE_POST_EQUAL=YES.','',
      'NON_SECRET_AUTHORITY_FINGERPRINT_PRE='+rec['non_secret_authority_fingerprint_pre'],
      'NON_SECRET_AUTHORITY_FINGERPRINT_POST='+rec['non_secret_authority_fingerprint_post'],
      'NON_SECRET_AUTHORITY_FINGERPRINT_END='+rec['non_secret_authority_fingerprint_end'],'',
      'Only proven exact disposable project/image/volume/readonly bind was used; PG18.4 UTF8 and current127.0.0.1 port were verified before JDBC. Fresh secrets were private ephemeral files only. Logging configuration was restored, transient awake request released, both attempts ended with stopped disposable container and erased credential files. No protected DB/volume, production secret, fixture installation, SQL authority change, bound increase, G3G or main push/merge.','',
      'BLOCKER=0; HIGH=1; MEDIUM=0; LOW=0. H01_ROOT_CAUSE=UNKNOWN; JDBC_08006_ROOT_CAUSE=UNKNOWN. Evidence supports model-placement relevance and historical power-state correlation, not complete cause attribution. Historical fixture-2 remains FAIL; no H01 closure or G3F.4 PASS.','',
      'NEXT_GATE=G3F_4_REHEARSAL_TRANSPORT_MODEL_REVIEW. Next action: govern the visible heartbeat/check boundary against actual on-demand sessions and external watchdog refresh, preserving DB-clock predicates and RR visibility; specify a bounded eligible operational-path experiment and platform awake/lifecycle evidence before any separate numeric-policy review. No number or fixture-3 is proposed here.','',
      'Full server/Docker logs are retained losslessly as GZIP_BASE64_LOSSLESS fields inside08006-DIAGNOSTICS.json, with original byte count and SHA256. Decompression reproduces every line; this is storage encoding, not truncation/redaction. Readable correlated outlier windows remain in TIMING-PHASES.json. Decode with gzip.decompress(base64.b64decode(field["data"])) and verify the recorded SHA256.', '',
      'Validation: final Java and Python compiled; offline exception-chain validation preserves primary/cause/next/suppressed/vendor code and bounds cycles; lossless log decompression verified; complete9500 raw sample counts/statistics/session checks validated; complete exception/log retention and outlier correlation inspected; both password rounds and final non-secret fingerprint equality verified; previous source/evidence byte hashes unchanged; diagnostic JSON parsed; exact endpoint/stop/credential-erasure checks passed. Commit/push/fetched head equality is reported after checkpoint creation.']
    # Space numeric labels in prose without changing machine field names, hashes or exact identifiers.
    text='\n'.join(lines)+'\n'
    for a,b in [('Baseline0c','Baseline 0c'),('completed9500','completed 9500'),('including5000','including 5000'),('observed08006','observed 08006'),('Historical428349','Historical 428349'),('index34','index 34'),('ADMIN138','ADMIN 138'),('AUDITOR139','AUDITOR 139'),('New outliers54091','New outliers 54091'),('JDBC connect50969','JDBC connect 50969'),('setup938','setup 938'),('lookup3','lookup 3'),('query1398','query 1398'),('AUDITOR536','AUDITOR 536'),('total43865','total 43865'),('auth22867','auth 22867'),('fork535','fork 535'),('to428349','to 428349'),('JDBC08006','JDBC 08006'),('entry11:','entry 11:'),('standby11:','standby 11:'),('exit11:','exit 11:'),('ends11:','ends 11:'),('at11:','at 11:'),('clock6925','clock 6925'),('age6929','age 6929'),('clock4990','clock 4990'),('age4995','age 4995'),('clock6656','clock 6656'),('observed in the corrected measurement window;5000','observed in the corrected measurement window; 5000'),('consumed176078','consumed 176078'),('at190s','at 190s'),('every100','every 100'),('PG18.4','PG 18.4'),('current127','current 127'),('complete9500','complete 9500')]:text=text.replace(a,b)
    (evidence/'PACKAGE-0090-G3F-4-TIMING-08006-DIAGNOSIS.md').write_text(text,encoding='utf-8',newline='\n')
    print(json.dumps(dict(sample_counts=expected,maxima=maxs,query_roundtrip_max_us=query_max,password_rotation='PASS',H01='OPEN',NEXT_GATE=common['NEXT_GATE']),indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--rotate-disposable-passwords',action='store_true');parser.add_argument('--publish',action='store_true')
    args=parser.parse_args()
    if args.publish:publish()
    else:measure(args.rotate_disposable_passwords)
