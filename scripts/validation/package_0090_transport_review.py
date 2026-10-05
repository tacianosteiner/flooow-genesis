"""One-shot isolated transport diagnosis. No policy/ACL/adapter changes.

The existing explicit authorization permits PASSWORD ONLY on postgres and the
four existing governed logins. Snapshot export/import observes MVCC without
granting the AUDITOR raw readiness SELECT or installing a helper.
"""
import ctypes, datetime, hashlib, json, os, secrets, statistics, subprocess, sys, time
from pathlib import Path
import package_0090_timing_qualification2 as env
import package_0090_timing_forensics as forensic

ROOT=env.ROOT
BASELINE='27103cfd2bfb5b33cec0017cf789a613497363db'
NAMES=['TRANSPORT-MODEL-REVIEW.md','WATCHDOG-VISIBILITY.json','RR-SNAPSHOT-PLACEMENT.json','ELIGIBLE-S01-TIMING.json']
WORK='transport-model-review'

def command(args,timeout=30):
    r=subprocess.run(args,capture_output=True,timeout=timeout)
    if r.returncode:raise RuntimeError(r.stderr.decode(errors='replace') if args[0]=='javac' else 'Tool failed: '+args[0])
    return r.stdout

def measure():
    command(['git','fetch','origin'])
    for ref in ('HEAD','origin/checkpoint/package-0090-cloud-handoff'):
        if command(['git','rev-parse',ref]).decode().strip()!=BASELINE:raise RuntimeError('Baseline mismatch')
    allowed={'scripts/validation/Package0090TransportReview.java','scripts/validation/package_0090_transport_review.py'}|{'docs/evidence/PACKAGE-0090-G3F-4-'+n for n in NAMES}
    if any(r[3:].replace('\\','/') not in allowed for r in command(['git','status','--porcelain']).decode().splitlines()):raise RuntimeError('Unexpected worktree changes')
    target,private,old=env.identity()
    if target['State']['Running']:raise RuntimeError('Expected stopped disposable')
    work=private/WORK;work.mkdir(exist_ok=True)
    if (work/'record.json').exists():raise RuntimeError('Do not overwrite accepted diagnostic')
    # Every tracked historical file is protected; only these two new tools exist initially.
    tracked=command(['git','ls-files','-z']).decode().split('\0')
    hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in tracked if p and (ROOT/p).is_file()}
    jars=sorted((Path.home()/'.gradle/caches/modules-2/files-2.1').rglob('*.jar'))
    cp=os.pathsep.join([str(ROOT/'applications/command-authority-ceremony/build/classes/kotlin/main')]+list(map(str,jars)))
    sources=['Package0090TransportReview.java','Package0090TimingForensics.java','Package0090RehearsalAdapter.java','Package0090RehearsalEndpoint.java']
    args='-cp\n"'+cp.replace('\\','/')+'"\n-d\n"'+work.as_posix()+'"\n'+''.join('"'+(ROOT/'scripts/validation'/n).as_posix()+'"\n' for n in sources)
    (work/'javac.args').write_text(args,encoding='utf-8');command(['javac','@'+str(work/'javac.args')],60)
    roles={'ADMIN':'postgres',**{s:'g3f4_'+s.lower()+'_cc2941797db3' for s in ['AUDITOR','VERIFIER','ISSUER','EXECUTOR']}}
    creds={s:secrets.token_hex(32) for s in roles}
    rec={'baseline':BASELINE,'diagnosis_only':True,'protected_database_connection':'NO','protected_volume_mount':'NO','production_secret_use':'NO','historical_hashes_before':hashes,'new_policy_values':False,'fixture2_installed':False,'fixture3_created':False}
    def save():(work/'record.json').write_text(json.dumps(rec,indent=2)+'\n',encoding='utf-8',newline='\n')
    def sql(statement):
        env.identity()
        r=subprocess.run(['docker','exec','-i',env.CONTAINER,'psql','-X','-U','postgres','-d','g3f4','-At','-v','ON_ERROR_STOP=1'],input=statement,text=True,capture_output=True,timeout=30)
        if r.returncode:raise RuntimeError('Administrative SQL failed; no potentially secret error output emitted')
        return r.stdout.strip()
    password_file=private/'postgres-password';password_file.write_text(creds['ADMIN'],encoding='ascii')
    started=False;settings=None;marker=None;awake=False
    authority_query=forensic.authority_snapshot_sql(roles.values())
    marker_query="SELECT row_to_json(x) FROM (SELECT deployment_id,incarnation_id,state,watchdog_healthy,watchdog_checked_at,policy_version,encode(policy_digest,'hex') AS policy_digest,encode(sha256(history_manifest),'hex') AS history_sha,encode(sha256(acl_manifest),'hex') AS acl_sha,active_key_version FROM public.offline_readiness) x;"
    try:
        command(['docker','start',env.CONTAINER]);started=True
        for _ in range(200):
            if subprocess.run(['docker','exec',env.CONTAINER,'pg_isready','-U','postgres','-d','g3f4'],capture_output=True).returncode==0:break
            time.sleep(.2)
        else:raise RuntimeError('PostgreSQL startup timeout')
        target,_,_=env.identity();ports=target['NetworkSettings']['Ports']['5432/tcp']
        if len(ports)!=1 or ports[0]['HostIp']!='127.0.0.1':raise RuntimeError('Localhost endpoint mismatch')
        rec['port']=int(ports[0]['HostPort'])
        if sql("SELECT current_setting('server_version_num');")!='180004':raise RuntimeError('Expected PostgreSQL18.4')
        rec['authority_pre']=json.loads(sql(authority_query));rec['authority_fingerprint_pre']=forensic.fingerprint(rec['authority_pre'])
        if len(rec['authority_pre']['roles'])!=5 or {r['rolname'] for r in rec['authority_pre']['roles']}!=set(roles.values()):raise RuntimeError('Exact five existing roles required')
        marker=json.loads(sql(marker_query));rec['marker_before']=marker
        if marker['state']!='NOT_READY' or marker['watchdog_healthy'] is not False or marker['policy_version']!='fixture-1' or marker['incarnation_id']!=old['timing_fixture']['incarnation']:raise RuntimeError('Unchanged fixture1/NOT_READY marker required')
        save()
        sql('\n'.join("ALTER ROLE "+roles[s]+" PASSWORD '"+creds[s]+"';" for s in roles))
        rec['authority_post_rotation']=json.loads(sql(authority_query));rec['authority_fingerprint_post']=forensic.fingerprint(rec['authority_post_rotation'])
        if rec['authority_pre']!=rec['authority_post_rotation']:raise RuntimeError('Non-secret authority drift')
        rec['password_rotation']='PASS';rec['rotated_role_count']=5;rec['password_rotation_scope']='EXACT_AUTHORIZED_FIVE_ROLES'
        settings=json.loads(sql("SELECT json_agg(json_build_object('name',name,'setting',setting,'sourcefile',sourcefile) ORDER BY name) FROM pg_settings WHERE name IN ('log_statement','log_parameter_max_length','log_parameter_max_length_on_error','log_min_error_statement','log_line_prefix');"))
        rec['logging_before']=settings
        for k,v in {'log_statement':'all','log_parameter_max_length':'0','log_parameter_max_length_on_error':'0','log_min_error_statement':'panic','log_line_prefix':'%m [%p] %e '}.items():sql("ALTER SYSTEM SET "+k+" = '"+v+"';")
        sql('SELECT pg_reload_conf();')
        conf=f'url=jdbc:postgresql://127.0.0.1:{rec["port"]}/g3f4\nproject={env.PROJECT}\nvolume={env.VOLUME}\ncontainer={env.CONTAINER}\nincarnation={marker["incarnation_id"]}\n'
        for s,n in roles.items():conf+=f'{s}.name={n}\n{s}.password={creds[s]}\n'
        (work/'jdbc.properties').write_text(conf,encoding='ascii')
        args='-cp\n"'+(str(work)+os.pathsep+cp).replace('\\','/')+'"\nPackage0090TransportReview\n"'+(work/'jdbc.properties').as_posix()+'"\n"'+(work/'measurements.json').as_posix()+'"\n'
        (work/'java.args').write_text(args,encoding='utf-8')
        awake=bool(ctypes.windll.kernel32.SetThreadExecutionState(0x80000001));rec['awake_controlled_dataset']=awake
        rec['start_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();save()
        q=subprocess.run(['java','@'+str(work/'java.args')],cwd=work,timeout=500,capture_output=True)
        (work/'java.stdout').write_bytes(q.stdout);(work/'java.stderr').write_bytes(q.stderr)
        rec['java_exit_code']=q.returncode;rec['end_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();save()
        if q.returncode:raise RuntimeError('Java diagnostic failed; private non-secret exception chain retained')
        rec['study_completed']=True
    finally:
        try:
            if started and marker:
                sql("UPDATE public.offline_readiness SET watchdog_checked_at='"+marker['watchdog_checked_at']+"'::timestamptz WHERE incarnation_id='"+marker['incarnation_id']+"'::uuid;")
                rec['marker_after']=json.loads(sql(marker_query));rec['marker_restored']=rec['marker_after']==marker
                rec['authority_end']=json.loads(sql(authority_query));rec['authority_fingerprint_end']=forensic.fingerprint(rec['authority_end']);rec['role_state_pre_post_equal']=rec['authority_pre']==rec['authority_end']
            if started and settings:
                for s in settings:
                    if (s['sourcefile'] or '').endswith('postgresql.auto.conf'):sql("ALTER SYSTEM SET "+s['name']+" = '"+s['setting'].replace("'","''")+"';")
                    else:sql('ALTER SYSTEM RESET '+s['name']+';')
                sql('SELECT pg_reload_conf();');rec['logging_restored']=True
            if started and 'start_utc' in rec:
                logged=subprocess.run(['docker','logs','--timestamps','--since',rec['start_utc'],env.CONTAINER],capture_output=True,timeout=30)
                if logged.returncode:raise RuntimeError('Docker log capture failed')
                (work/'server.log').write_bytes(logged.stdout+logged.stderr)
        finally:
            try:
                if started:command(['docker','stop',env.CONTAINER],40)
            finally:
                for p in [password_file,work/'jdbc.properties']:
                    if p.exists():p.unlink()
                if awake:ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
                rec['plaintext_credential_files_erased']=True;rec['container_stopped']=not env.identity()[0]['State']['Running']
                rec['historical_hashes_after']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in hashes}
                rec['historical_unchanged']=rec['historical_hashes_after']==hashes;save()
    if not all(rec.get(k) for k in ['study_completed','marker_restored','role_state_pre_post_equal','logging_restored','container_stopped','plaintext_credential_files_erased','historical_unchanged']):raise RuntimeError('Diagnostic integrity failure')
    print('TRANSPORT_DIAGNOSTIC_COMPLETE')

def publish():
    if any(command(['git','rev-parse',ref]).decode().strip()!=BASELINE for ref in ('HEAD','origin/checkpoint/package-0090-cloud-handoff')):raise RuntimeError('Refuse to rewrite accepted evidence beyond this baseline')
    _,private,_=env.identity();work=private/WORK
    rec=json.loads((work/'record.json').read_text());study=json.loads((work/'measurements.json').read_text())
    if env.identity()[0]['State']['Running'] or (private/'postgres-password').exists() or (work/'jdbc.properties').exists():raise RuntimeError('Cleanup incomplete')
    if not all(rec.get(k) for k in ['study_completed','marker_restored','role_state_pre_post_equal','logging_restored','container_stopped','plaintext_credential_files_erased','historical_unchanged']):raise RuntimeError('Integrity incomplete')
    if any(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h for p,h in rec['historical_hashes_before'].items()):raise RuntimeError('Historical drift')
    expected={'frozen':1000,**{'continuous_'+str(n)+'ms':1000 for n in [5,10,25,50]}}
    if {k:len(v) for k,v in study['populations'].items()}!=expected or not study.get('completed') or study.get('failure'):raise RuntimeError('Incomplete population')
    def dist(values):return env.distribution([{'age_us':v} for v in values])
    def parse(t):return datetime.datetime.fromisoformat(t).astimezone(datetime.timezone.utc)
    def stats(samples):
        ages=[s['visible']['visible_age_us'] for s in samples];connect=[s['auditor_trace']['connection_us'] for s in samples]
        return {'count':len(samples),'surrogate_visible_age_us':dist(ages),'connection_us':dist(connect),
            'snapshot_clock_upper_bound_age_us':dist([(parse(s['snapshot']['snapshot_db_timestamp_upper_bound'])-parse(s['visible']['visible_heartbeat'])).total_seconds()*1e6 for s in samples]),
            'pearson_connection_vs_surrogate_age':statistics.correlation(connect,ages),
            'newer_visible_marker_than_preconnect_ack_count':sum(int(s['visible']['visible_tuple_xmin'])>int(s['marker_before_connect']['xmin']) for s in samples),
            'connection_at_least_50ms_count':sum(c>=50000 for c in connect),
            'connection_at_least_50ms_and_newer_visible_marker_count':sum(s['auditor_trace']['connection_us']>=50000 and int(s['visible']['visible_tuple_xmin'])>int(s['marker_before_connect']['xmin']) for s in samples)}
    profiles={k:stats(v) for k,v in study['populations'].items()}
    continuous=[s for k,v in study['populations'].items() if k.startswith('continuous') for s in v]
    aggregate=stats(continuous)
    writer_by_xmin={w['xmin']:w for w in study['writer_commits']}
    for population,samples in study['populations'].items():
        for s in samples:
            visible=writer_by_xmin[s['visible']['visible_tuple_xmin']]
            if parse(visible['heartbeat'])!=parse(s['visible']['visible_heartbeat']):raise RuntimeError('Tuple/timestamp mismatch')
            age=round((parse(s['visible']['db_now_at_surrogate_predicate'])-parse(s['visible']['visible_heartbeat'])).total_seconds()*1e6)
            if age!=s['visible']['visible_age_us']:raise RuntimeError('DB-clock age mismatch')
            _,xmax,in_progress=s['snapshot']['snapshot_identity'].split(':')
            xid=s['visible']['visible_tuple_xmin']
            if int(xid)>=int(xmax) or xid in in_progress.split(','):raise RuntimeError('Tuple not visible in recorded snapshot')
            if [e['method'] for e in s['auditor_trace']['events']][:3]!=['setAutoCommit','setTransactionIsolation','setReadOnly']:raise RuntimeError('Actual Kotlin configuration order changed')
            s['visible']['external_diagnostic_sequence']=visible['sequence']
            if population=='frozen' and s['visible']['visible_tuple_xmin']!=s['marker_before_connect']['xmin']:raise RuntimeError('Frozen marker mismatch')
            if s['snapshot']['isolation']!='repeatable read' or s['snapshot']['read_only']!='on' or s['s01_unbound_denial']['sqlstate']!='P0017':raise RuntimeError('Adapter/snapshot/denial mismatch')
    examples=[s for s in continuous if s['auditor_trace']['connection_us']>=50000 and int(s['visible']['visible_tuple_xmin'])>int(s['marker_before_connect']['xmin'])]
    examples=sorted(examples,key=lambda s:s['auditor_trace']['connection_us']-s['visible']['visible_age_us'],reverse=True)[:5]
    migration='applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V043__create_governed_offline_field_proof_capability_composition.sql'
    lines=(ROOT/migration).read_text().splitlines();function='';predicates={};declarations=[]
    for num,line in enumerate(lines,1):
        if line.startswith('CREATE FUNCTION '):function=line;declarations.append({'line':num,'function':line})
        if 'watchdog_checked_at' in line and ('EXTRACT' in line or 'ready_record.state' in line):predicates.setdefault(function,[]).append(num)
    evidence_paths=command(['git','ls-files','-z']).decode().split('\0')
    candidates=[p for p in evidence_paths if p and not p.startswith('docs/evidence/') and '/build/' not in p and (p.startswith(('applications/','scripts/operations/','.github/')) or p=='compose.yaml') and Path(p).suffix in ['.kt','.java','.py','.ps1','.sh','.yaml','.yml']]
    matches=[]
    for path in candidates:
        for num,line in enumerate((ROOT/path).read_text(encoding='utf-8-sig').splitlines(),1):
            if any(term in line.lower() for term in ['watchdog','pg_cancel_backend','pg_terminate_backend']):matches.append({'path':path,'line':num,'text':line})
    inventory={'method':'All tracked application, operations-script, GitHub workflow and compose source candidates; diagnostics excluded from writer inference',
        'searched_paths':candidates,'matches':matches,'source_hashes':{p:rec['historical_hashes_before'][p] for p in candidates},
        'sql_writer_scan':'No UPDATE/INSERT readiness writer and no watchdog writer function in V043; protected relation plus readers only',
        'canonical_function_health_predicate_lines':predicates,
        'authority_sources':{'ADR81':'Trusted deployment watchdog across external JCA gap','ADR133':'Watchdog packaging remains representation/work to resolve before readiness','SPEC18_line245':'OID/incarnation whitelist; independent finite enforcement; failure blocks new claims/effect admission and triggers drain; no READY without watchdog','SPEC21_2_line586':'Finite policy pairs; unchanged section18 watchdog semantics','SPEC21_3_lines604_612':'Q NOLOGIN/read-only; S01 issuance and S13 independent current readiness','SPEC25_line2210':'Direct existing postgres administrative provisioning; control owner remains NOLOGIN','SPEC25_line2217':'Policy activation does not automatically establish deployment READY'}}
    result={
        'WATCHDOG_MARKER_RELATION':'public.offline_readiness','WATCHDOG_MARKER_COLUMNS':['watchdog_checked_at','watchdog_healthy','state'],
        'WATCHDOG_WRITER_ROLE':'postgres (approved disposable ADMIN); production watchdog login binding not specified',
        'WATCHDOG_WRITER_FUNCTION':'NONE; direct administrative UPDATE, not Q or a service wrapper',
        'WATCHDOG_WRITER_PRIVILEGE':'Existing trusted postgres administrative DML; control-owner table ownership is NOLOGIN; no service write capability',
        'WATCHDOG_WRITER_EXISTS_IN_SQL':'NO_DEDICATED_WRITER; STORAGE_AND_READ_GUARDS_EXIST',
        'WATCHDOG_WRITER_EXISTS_IN_APPLICATION':'NO','WATCHDOG_WRITER_EXISTS_IN_DEPLOYMENT_PACKAGE':'NO',
        'WATCHDOG_DEPLOYMENT_IMPLEMENTATION':'MISSING','REHEARSAL_WATCHDOG_NEW_AUTHORITY_REQUIRED':'NO',
        'AUDITOR_SNAPSHOT_ESTABLISHMENT_POINT':'FIRST_NON_TRANSACTION_CONTROL_SQL_STATEMENT; S01-first query in normal launcher',
        'FROZEN_VISIBLE_AGE_MAX_US':profiles['frozen']['surrogate_visible_age_us']['max_us'],
        'CONTINUOUS_WATCHDOG_VISIBLE_AGE_MAX_US':aggregate['surrogate_visible_age_us']['max_us'],
        'CONTINUOUS_WATCHDOG_VISIBLE_AGE_P99_US':aggregate['surrogate_visible_age_us']['p99_us'],
        'CONTINUOUS_WATCHDOG_VISIBLE_AGE_P999_US':aggregate['surrogate_visible_age_us']['p99_9_us'],
        'CONNECTION_MAX_US':max(p['connection_us']['max_us'] for p in profiles.values()),
        'REAL_S01_FIRST_CHECK_AGE_MAX_US':None,'REAL_Q_CHECK_AGE_MAX_US':None,'REAL_S01_TOTAL_MAX_US':None,
        'RR_VISIBILITY_BEFORE_SNAPSHOT':'VISIBLE','RR_VISIBILITY_AFTER_SNAPSHOT':'NOT_VISIBLE_IN_EXISTING_TRANSACTION','RR_VISIBILITY_NEW_TRANSACTION':'VISIBLE',
        'CONNECT_LATENCY_CORRELATES_WITH_VISIBLE_AGE_FROZEN':'YES_OBSERVED; Pearson r='+str(profiles['frozen']['pearson_connection_vs_surrogate_age']),
        'CONNECT_LATENCY_CORRELATES_WITH_VISIBLE_AGE_CONTINUOUS':'YES_OBSERVED_WEAKER_WITHIN_EACH_CADENCE; not proof that startup fixes marker or causal attribution',
        'QUALIFIED_TRANSPORT_MODEL':'MODEL_C1','TRANSPORT_QUALIFICATION_SCOPE':'Snapshot mechanism only; eligible S01/Q and operational watchdog unqualified',
        'POOL_NEW_AUTHORITY_REQUIRED':'NO_FOR_OPERATIONAL_PER_SLOT_POOL_WITH_UNCHANGED_SESSION_IDENTITY_AND_ISOLATION',
        'WATCHDOG_FAILURE_ENFORCEMENT':'SQL readiness/health/age guards exist; external OID/incarnation monitor and cancel/terminate enforcement missing from reviewed package',
        'WATCHDOG_DRAIN_SEMANTICS':'Required independent cancel/drain plus governed ADMIN stale/abort/recovery recording; heartbeat expiry does not persist drain or release ownership',
        'H01_PRIMARY_CAUSE':'MULTIPLE_CAUSES','H01_CAN_PROCEED_TO_NUMERIC_BOUND_REVIEW':'NO','G3F4_H01':'OPEN',
        'JDBC_08006_ROOT_CAUSE':'UNKNOWN','08006_AS_BOUNDARY_BLOCKER':'NO_WITH_FAIL_CLOSED_RECOVERY_REQUIREMENT',
        'FIXTURE_1_MUTATED':'NO','FIXTURE_2_INSTALLED':'NO','FIXTURE_3_CREATED':'NO',
        'BLOCKER_COUNT':0,'HIGH_COUNT':2,'MEDIUM_COUNT':0,'LOW_COUNT':0,
        'PROTECTED_DATABASE_CONNECTION':'NO','PROTECTED_VOLUME_MOUNT':'NO','PRODUCTION_SECRET_USE':'NO',
        'PASSWORD_ROTATION':'PASS','ROTATED_ROLE_COUNT':5,'ROLE_STATE_PRE_POST_EQUAL':'YES','PASSWORD_ROTATION_SCOPE':'EXACT_AUTHORIZED_FIVE_ROLES',
        **{k:'YES' for k in ['ROLE_IDENTITY_UNCHANGED','ROLE_ATTRIBUTES_UNCHANGED','ROLE_MEMBERSHIPS_UNCHANGED','OBJECT_OWNERSHIP_UNCHANGED','ACL_UNCHANGED','DEFAULT_ACL_UNCHANGED','POLICY_UNCHANGED','MIGRATION_STATE_UNCHANGED']},
        'NON_SECRET_AUTHORITY_FINGERPRINT_PRE':rec['authority_fingerprint_pre'],'NON_SECRET_AUTHORITY_FINGERPRINT_POST':rec['authority_fingerprint_post'],
        'PLAINTEXT_CREDENTIAL_FILES_ERASED':'YES','DISPOSABLE_CONTAINER_STOPPED':'YES',
        'NEXT_GATE':'G3F_4_WATCHDOG_DEPLOYMENT_CLOSURE'}
    common={'baseline':BASELINE,'branch':'checkpoint/package-0090-cloud-handoff','G3F_4_ISOLATED_POSTGRES18_REHEARSAL':'HOLD','result':result,
        'validation':{'all_5000_tuple_timestamp_db_age_snapshot_visibility_checks':'PASS','actual_kotlin_configuration_order_and_p0017_denial_checks':'PASS','pre_post_end_non_secret_authority_equality':'PASS','all_tracked_baseline_files_byte_identity':'PASS','original_readiness_marker_contents_restored':'PASS','cleanup_and_stopped_endpoint_identity':'PASS'},
        'findings':[{'id':'G3F4-H01','severity':'HIGH','status':'OPEN','scope':'Unqualified runtime freshness; synthetic frozen-marker transport sensitivity, real connection jitter and RR marker aging; eligible S01/Q placement unmeasured. Historical outlier and 08006 mechanisms remain unknown.'},
                    {'id':'G3F4-WATCHDOG-DEPLOYMENT-GAP','severity':'HIGH','status':'OPEN','scope':'SPEC18 requires operational OID/incarnation watchdog/cancel/drain; no reviewed executable/package provides it. Separate deployment gap, not duplicate of unqualified numeric timing.'}],
        'unchanged_policy':'Only existing immutable fixture-1; all tracked baseline files byte-identical; NOT_READY/unhealthy retained; original marker content restored.',
        'measurement_limitations':['Raw readiness is read only by existing postgres in an imported AUDITOR snapshot, never by service SELECT. Three physical sessions: writer, actual Kotlin AUDITOR adapter, ADMIN observer.',
          'Visibility probes explicitly export a snapshot before the unbound S01 denial. They do not instrument or execute eligible S01/Q health checks. Normal S01-first probes are separate.',
          'Surrogate predicate DB clock runs after snapshot export/import roundtrips; ages include observer overhead. Snapshot-acquisition exact timestamp is unavailable; first-statement DB timestamp is an upper bound, not an engine callback.',
          'Groups run frozen then 5/10/25/50ms, not randomized; fixed-delay diagnostic cadence plus database update/commit latency is not a policy interval or assured scheduler rate. Writer commit traces preserve actual gaps.',
          'Transient host awake request, connection/socket diagnostic timeouts, snapshot export/import and full statement logging affect runtime. Descriptive data, no qualification/SLO/tail guarantee.',
          'Continuous aggregate mixes diagnostic cadences; per-cadence distributions/correlations must accompany it; no new temporal number chosen.'],
        'diagnostic_window':{'start_utc':rec['start_utc'],'end_utc':rec['end_utc'],'awake_controlled':rec['awake_controlled_dataset']}}
    def write(name,data):(ROOT/'docs/evidence'/('PACKAGE-0090-G3F-4-'+name)).write_text(json.dumps(data,indent=2,ensure_ascii=True)+'\n',encoding='utf-8',newline='\n')
    write('WATCHDOG-VISIBILITY.json',{**common,'source_inventory':inventory,'profiles':profiles,'continuous_aggregate':aggregate,'connection_over_50ms_newer_marker_examples':examples,'raw_study':study,
        'authority_and_cleanup_record_gzip_base64':forensic.packed_log(work/'record.json')})
    logs=(work/'server.log').read_text().splitlines()
    ids={p['trace']['auditor_backend_pid'] for p in study['production_s01_first_probes']}|{study['rr_edge']['trace']['auditor_backend_pid'],study['rr_edge']['case_C_trace']['auditor_backend_pid']}
    selected=[line for line in logs if any('['+str(pid)+']' in line for pid in ids)]
    write('RR-SNAPSHOT-PLACEMENT.json',{**common,'rr_edge':study['rr_edge'],'normal_s01_first_probes':study['production_s01_first_probes'],
        'server_log_for_selected_backends':selected,'full_server_log_gzip_base64':forensic.packed_log(work/'server.log'),
        'conclusion':'backend_xmin NULL and xact_start NULL after JDBC configuration; explicit BEGIN makes xact_start non-null but backend_xmin stays NULL; first export SELECT establishes snapshot/backend_xmin. Imported ADMIN reads prove A visible, B invisible, C visible.',
        'snapshot_timestamp':'Client SQL start/end and first-statement DB clock upper bound only; exact engine timestamp unavailable',
        'normal_s01_first':'Real adapter sends driver BEGIN READ ONLY then S01 SELECT. Failing unbound S01 establishes statement snapshot but aborts before heartbeat/Q; no internal predicate timestamps claimed.',
        'official_primary_sources':['https://www.postgresql.org/docs/18/transaction-iso.html#XACT-REPEATABLE-READ','https://www.postgresql.org/docs/18/functions-admin.html#FUNCTIONS-SNAPSHOT-SYNCHRONIZATION']})
    write('ELIGIBLE-S01-TIMING.json',{**common,'status':'NOT_EXECUTABLE_WITH_CURRENT_FIXTURE','eligible_s01_sample_count':0,'private_q_sample_count':0,
        'reason':'Existing fixture has zero binding headers, NOT_READY/unhealthy marker and placeholder expected manifests. Independently enforced watchdog is mandatory for READY, but missing from executable deployment package. ADMIN timestamp updates do not fulfill enforcement/drain prerequisite; no synthetic READY/binding activation was performed.',
        'required_authority_change':'NONE_IDENTIFIED_FOR_ADMIN_MEASUREMENT; no new grant proposed; deployment prerequisite closure is required before READY construction',
        'unbound_actual_adapter_s01_denial_count':5010,'unbound_denials_do_not_measure_eligible_health_check':True,
        'measurements':{k:None for k in ['snapshot_to_s01_start_us','s01_start_to_first_heartbeat_check_us','first_heartbeat_age_us','q_start_to_q_heartbeat_check_us','q_heartbeat_age_us','eligible_total_s01_duration_us']},
        'source_placement':{'S01_first_clock_line':6925,'S01_first_age_line':6929,'Q_first_clock_line':4990,'Q_first_age_line':4995,'Q_final_clock_line':6656,'Q_final_clock_is_heartbeat_recheck':False,'Q_final_clock_purpose':'Original EXECUTOR receipt expiry or AUDITOR issuance after live catalog/history'},
        'failure_path_execution':'NOT_EXECUTABLE_WITH_CURRENT_ELIGIBLE_STATE; unbound denial is not watchdog-failure or positive-path evidence'})
    table=['| Diagnostic population | N | Visible age p99 us | p99.9 us | Max us | Connection max us | Pearson r |','|---|---:|---:|---:|---:|---:|---:|']
    for name,p in profiles.items():
        age=p['surrogate_visible_age_us'];table.append(f'| {name} | {p["count"]} | {age["p99_us"]:.0f} | {age["p99_9_us"]:.0f} | {age["max_us"]:.0f} | {p["connection_us"]["max_us"]:.1f} | {p["pearson_connection_vs_surrogate_age"]:.6f} |')
    body='''# Package 0090 - governed watchdog and transport model review

STATUS: G3F.4 HOLD. H01 OPEN/HIGH. A separate required watchdog deployment gap is HIGH. No policy, production adapter, SQL authority, fixture or temporal bound changed.

DECISION: MODEL_C1 is proven for connection/snapshot placement, not eligible S01/Q or operational timing. Numeric-bound review cannot proceed. NEXT_GATE=G3F_4_WATCHDOG_DEPLOYMENT_CLOSURE.

The fetched local/remote baseline was 27103cfd2bfb5b33cec0017cf789a613497363db on checkpoint/package-0090-cloud-handoff; the worktree was clean before these diagnostic files. All baseline tracked files retain their byte hashes, including every historical HOLD report, V001-V043, ADR/SPEC, policy fixtures and production Kotlin sources.

The marker is public.offline_readiness.watchdog_checked_at/watchdog_healthy, with state controlling READY. V043 creates storage owned by flooow_offline_control_owner (NOLOGIN) and read guards; it contains no heartbeat writer function or watchdog UPDATE. Q is a NOLOGIN/read-only readiness capability, not a writer. Existing directly authenticated postgres ADMIN can perform bounded disposable diagnostic DML under the previously approved rehearsal administrative authority; no new authority was required. SPEC25 identifies exact postgres for administrative provisioning; it does not assign a production watchdog login or turn that provisioning into a implemented monitor.

ADR81/SPEC18 line245 require a trusted independent host/database watchdog targeting exact OID/incarnation, enforcing maximum transaction/idle durations through cancel/terminate, blocking claims/effect admission and triggering drain on failure. ADR133 and SPEC line274 leave packaging as implementation work. No executable watchdog was found in tracked application sources, compose, operations scripts or GitHub workflows. The compose PostgreSQL healthcheck only runs pg_isready. Out-of-process trust is intentional, but delivery of that component is unproven; classifying this package as MISSING/HIGH is appropriate. Actual unrelated external deployments remain UNKNOWN. Administrative timestamp emulation cannot close this gap or establish READY.

The actual compiled Kotlin GovernedSources.transaction and four distinct authenticated DataSources were used. Diagnostic DataSource/Connection delegates forward every call to the real PG driver and record timestamps; no mock/frozen JDBC execution or production edit. Configuration order is setAutoCommit(false), setTransactionIsolation(REPEATABLE_READ), setReadOnly(true). Existing postgres observer saw idle/xact_start NULL/backend_xmin NULL after configuration. Explicit BEGIN produced idle-in-transaction/xact_start but no backend_xmin. The first non-transaction-control SELECT established backend_xmin and an exported snapshot. Importing that exact snapshot in a third administrative session proved: A committed before snapshot is visible; B committed after it remains invisible; a new AUDITOR transaction sees B. Read-only AUDITOR xid is unassigned (NULL), not fabricated zero. Exact engine snapshot-acquisition timestamp is unavailable; SQL start/end and first SQL DB-clock upper bound are retained.

Normal S01-first transactions are recorded separately: driver BEGIN READ ONLY precedes the real S01 SELECT. Their nonexistent binding fails P0017 before heartbeat/Q. Population probes intentionally export a snapshot before S01; ADMIN imports it to read only non-secret marker/timestamp/xmin. AUDITOR receives no table grant or private data projection. This proves the same RR MVCC visibility mechanism, not a real S01 heartbeat predicate. All 5000 population S01 calls plus 10 S01-first probes denied safely.

1000 frozen observations and 1000 at each measurement-only 5/10/25/50ms fixed-delay cadence completed. The writer logs actual acknowledged commits, external sequences and tuple xmin without schema changes. Imported observer DB-clock age includes snapshot/export/import/query overhead; it must not be relabeled S01/Q health-check age. Groups were sequential, not randomized; statement logging and shared JVM/platform scheduling affect these descriptive measurements. Aggregate continuous statistics mix four cadences. Cadences are neither fixture values nor approved enforcement intervals.

'''+ '\n'.join(table)+f'''

Continuous combined N4000: max={aggregate['surrogate_visible_age_us']['max_us']:.0f}, p99={aggregate['surrogate_visible_age_us']['p99_us']:.0f}, p99.9={aggregate['surrogate_visible_age_us']['p99_9_us']:.0f} us (surrogate age only). Physical connection overall max={result['CONNECTION_MAX_US']:.1f} us. Continuous connections >=50ms numbered {aggregate['connection_at_least_50ms_count']}; {aggregate['connection_at_least_50ms_and_newer_visible_marker_count']} observed a heartbeat tuple newer than the pre-connect acknowledged tuple. Selected examples and all raw records are retained. This directly refutes an invariably frozen-before-connect marker. Moderate positive within-cadence correlations remain (r={profiles['continuous_5ms']['pearson_connection_vs_surrogate_age']:.6f}/{profiles['continuous_10ms']['pearson_connection_vs_surrogate_age']:.6f}/{profiles['continuous_25ms']['pearson_connection_vs_surrogate_age']:.6f}/{profiles['continuous_50ms']['pearson_connection_vs_surrogate_age']:.6f}); do not claim zero coupling or infer causality from correlation. Common scheduling/commit delays and work after snapshot can age the visible row even under MODEL_C1.

Eligible S01/Q: NOT_EXECUTABLE_WITH_CURRENT_FIXTURE. Binding header count is zero; fixture-1 remains the approved immutable policy with 100us health/interval actual and 200us maximum, NOT_READY/unhealthy and placeholder manifests. No independently enforcing watchdog exists in the reviewed package. The contract forbids readiness without it. No synthetic READY activation, new binding, manifest adoption, F2 installation or F3 creation was performed. All three requested real eligible timing maxima remain NULL/unmeasured, not zero. Source placement remains S01 clock6925/age6929, Q clock4990/age4995 before heavy live ACL/history; final Q clock6656 concerns receipt expiry/issuance, not another heartbeat-age check. These source points do not provide executed eligible timings.

Failure/drain: missing or NOT_READY/unhealthy/stale protected marker denies wrapper eligibility through existing readiness guards. A writer must explicitly update unhealthy/NOT_READY; a stopped writer merely lets its timestamp age. SQL freshness failures do not persist a drain or automatically release ownership. Mandatory external OID/incarnation monitor/cancel/terminate is absent, so its failure path was not executed. An old RR AUDITOR snapshot cannot see a newly committed health-state change; it can retain the old marker, while each fresh clock predicate can still expire its age. This is not new effect authority: S13/Q independently recheck readiness before claim, and READ_COMMITTED/VOLATILE mutation paths reload readiness/fresh clocks on entry and final/post-effect fences; failure rolls tentative effects back. Full exact function/line inventory is in WATCHDOG-VISIBILITY. Stale ownership/generation advance, recovery and recorded result remain governed ADMIN drain/reconciliation actions. No emergency cancel/drain implementation or positive-stage test is claimed.

PGSimpleDataSource physically connects per transaction. Correctness depends on identity/isolation/readiness checks, not pooling; connection startup occurs before the RR snapshot. Performance incurs repeated auth/setup; availability/jitter can affect connection, writer scheduling and later read age. Security currently benefits from separate slot authentication and fresh physical-session teardown. A purely operational pool needs no new database authority if four separate slot/deployment identities, incarnation eviction, transaction rollback/reset, read-only/isolation restoration, no cross-slot reuse and failure disposal are preserved. No pool was implemented or performance gain promised.

H01 PRIMARY_CAUSE=MULTIPLE_CAUSES summarizes demonstrated frozen-marker transport sensitivity, physical connection jitter and RR visibility limitations plus the independent deployment prerequisite gap; it does not identify the historical 428349us/08006 mechanisms. H01 remains OPEN. Separate G3F4-WATCHDOG-DEPLOYMENT-GAP is HIGH because safe operation requires an undelivered component; it does not double count the numeric qualification gap. Counts now BLOCKER0/HIGH2/MEDIUM0/LOW0.

JDBC_08006_ROOT_CAUSE=UNKNOWN. No 08006 was observed here; historical evidence is unchanged. 08006_AS_BOUNDARY_BLOCKER=NO_WITH_FAIL_CLOSED_RECOVERY_REQUIREMENT: GovernedSources propagates the primary failure, attempts rollback without masking it and closes the connection. A failed audit yields no new receipt. Mutation COMMIT uncertainty requires durable reconciliation and existing recovery/drain rules; disconnect never implies rollback confirmation, effect absence, ownership release or permission to replay. This is a handling classification, not executed fault-injection certification.

Password-only authorization was reused on exactly five existing roles. Identity/attributes/memberships/ownership/ACL/defaults/policies/migration state pre/post/end remain equal. Fingerprint={rec['authority_fingerprint_pre']}. No credential/verifier value was queried or preserved. Complete non-secret snapshots and baseline hashes are retained losslessly in the authority/cleanup record. Original readiness contents and logging settings were restored. Plaintext files erased; exact disposable container stopped. No protected database/volume or production secret was used.

Scope: two diagnostic tools plus the four required new evidence artifacts. Baseline production behavior/history stays unchanged. Next technically determined action is bounded watchdog deployment closure under the existing OID/incarnation/fail-closed contract; this gate creates neither that component nor new temporal numbers. Numeric review follows only after eligible S01/Q placement and watchdog prerequisites are proven.

PostgreSQL primary references: [Repeatable Read snapshot semantics](https://www.postgresql.org/docs/18/transaction-iso.html#XACT-REPEATABLE-READ), [snapshot export/import](https://www.postgresql.org/docs/18/functions-admin.html#FUNCTIONS-SNAPSHOT-SYNCHRONIZATION). Executed PG18.4 evidence supports those semantics locally.

Exact requested return fields (checkpoint HEAD/remote/clean proof is supplied after committing this report):

```text
'''+''.join(k+'='+('NOT_EXECUTABLE_WITH_CURRENT_FIXTURE' if v is None else str(v))+'\n' for k,v in result.items())+'```\n'
    (ROOT/'docs/evidence/PACKAGE-0090-G3F-4-TRANSPORT-MODEL-REVIEW.md').write_text(body,encoding='utf-8',newline='\n')
    print(json.dumps({'result':result},indent=2))

if __name__=='__main__':
    if sys.argv[1:] == ['--publish']:publish()
    elif sys.argv[1:]:raise SystemExit('Use no arguments to measure or --publish to preserve completed evidence')
    else:measure()
