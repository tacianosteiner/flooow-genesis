"""Measure the explicitly authorized existing disposable G3F.4 environment.

Never authorizes a policy from measurements alone. Fixture-1 and historical
reports are immutable; a failed candidate ends qualification before fixture-2.
"""
import hashlib
import hmac
import json
import math
import os
from pathlib import Path
import secrets
import statistics
import subprocess
import time
import uuid

ROOT=Path(__file__).resolve().parents[2]
BASELINE='bd50ae1a21a9df85b5bdfb1da44766d22d11f21d'
PROJECT='flooow-0090-g3f4-cc2941797db3'
VOLUME=PROJECT+'-data'
CONTAINER=PROJECT+'-postgres'
IMAGE='sha256:07fc165de5bb569d822460e2df645c5489f99220fc2cb16c86596d39db394561'
HISTORICAL=list((ROOT/'docs/evidence').glob('PACKAGE-0090-G3F-4-*'))
FIXTURE1=ROOT/'docs/evidence/PACKAGE-0090-G3F-3B-FIXTURE-001.json'
ALLOWED={'scripts/validation/package_0090_timing_qualification.py','scripts/validation/Package0090TimingQualification.java'}
EXPECTED_COUNTS={'idle_warm':1000,'cold_reconnect':100,'load4':1000,'load8':1000}

def command(args):
    result=subprocess.run(args,capture_output=True)
    if result.returncode:raise RuntimeError('Tool failed: '+args[0])
    return result.stdout

def identity():
    d=json.loads(command(['docker','inspect',CONTAINER]))[0]
    v=json.loads(command(['docker','volume','inspect',VOLUME]))[0]
    if d['Config']['Labels'].get('com.docker.compose.project')!=PROJECT or v['Labels'].get('com.docker.compose.project')!=PROJECT or d['Image']!=IMAGE:
        raise RuntimeError('STOP: disposable identity mismatch')
    if len(d['Mounts'])!=2 or {m.get('Name') for m in d['Mounts'] if m['Type']=='volume'}!={VOLUME}:
        raise RuntimeError('STOP: unapproved volume/mount')
    binds=[m for m in d['Mounts'] if m['Type']=='bind']
    private=Path.home()/'AppData/Local/Temp/flooow-0090-g3f4-kui1oqwb'
    desktop='/run/desktop/mnt/host/c'+private.as_posix()[2:]
    if len(binds)!=1 or binds[0]['Destination']!='/review' or binds[0]['RW'] or binds[0]['Source'].replace('\\','/') not in (private.as_posix(),desktop):
        raise RuntimeError('STOP: private scratch mount mismatch')
    old=json.loads((private/'record.json').read_text())
    if old['disposable_project']!=PROJECT or old['disposable_volume']!=VOLUME:
        raise RuntimeError('STOP: retained disposable record mismatch')
    return d,private,old

def distribution(samples):
    values=sorted(float(x['age_us']) for x in samples)
    if not values:return {'count':0}
    def quantile(p):return values[max(0,math.ceil(p*len(values))-1)]
    return dict(count=len(values),min_us=values[0],p50_us=quantile(.5),p90_us=quantile(.9),p95_us=quantile(.95),p99_us=quantile(.99),p99_9_us=quantile(.999) if len(values)>=1000 else None,max_us=values[-1],mean_us=statistics.mean(values),sample_standard_deviation_us=statistics.stdev(values) if len(values)>1 else 0,quantile_method='NEAREST_RANK',p99_9_null_means='INSUFFICIENT_SAMPLE_SIZE_NOT_ZERO')

def measure():
    command(['git','fetch','origin'])
    if any(command(['git','rev-parse',ref]).decode().strip()!=BASELINE for ref in ('HEAD','origin/checkpoint/package-0090-cloud-handoff')):
        raise RuntimeError('STOP: baseline mismatch')
    changed=command(['git','status','--porcelain']).decode().splitlines()
    if any(row[3:].replace('\\','/') not in ALLOWED for row in changed):raise RuntimeError('STOP: unexpected working changes')
    historical={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in HISTORICAL+[FIXTURE1]}
    prior=json.loads((ROOT/'docs/evidence/PACKAGE-0090-G3F-4-RUNTIME-TESTS.json').read_text())
    if not any(f['id']=='G3F4-H01' and f['severity']=='HIGH' for f in prior['findings']):raise RuntimeError('Expected HIGH H01 missing')
    d,private,old=identity()
    work=private/('timing-qualification-'+uuid.uuid4().hex[:12]);work.mkdir()
    record=dict(baseline=BASELINE,initial_local_equals_remote=True,initial_worktree='CLEAN_BEFORE_AUTHORIZED_TOOLING',disposable_project=PROJECT,disposable_volume=VOLUME,postgres_image_digest=IMAGE,protected_database_connection='NO',protected_volume_mount='NO',production_secret_use='NO',identity='EXACT_LABEL_IMAGE_VOLUME_AND_PRIVATE_READONLY_MOUNT_PROVEN',historical_hashes_before=historical,container_constraints={k:d['HostConfig'][k] for k in ('NanoCpus','CpuQuota','CpuPeriod','CpusetCpus','CpuShares','Memory','MemorySwap','MemoryReservation')},candidate=dict(watchdog_interval_us=10000,watchdog_max_us=20000,health_window_us=150000,health_window_max_us=200000,preflight_ttl_us=1000000,preflight_max_ttl_us=2000000),safety_margin_rule='Predeclared: watchdog_max >= 2 * measured population maximum; health_window >= watchdog_interval + 2 * measured maximum; measured maximum < watchdog_max. This empirical factor is not a confidence bound or production SLO.',credential_handling='Fresh seed-derived rehearsal-only ADMIN/four service passwords; private files only; no role/ACL/owner changes; erase private plaintext after measurement.')
    def save():
        with (work/'record.json').open('w',encoding='utf-8',newline='\n') as f:json.dump(record,f,indent=2);f.write('\n')
    print('PRIVATE_MEASUREMENT_DIRECTORY='+str(work),flush=True);save()
    seed=secrets.token_bytes(32)
    credentials={slot:(name,hmac.new(seed,('G3F4-TIMING/'+slot).encode(),hashlib.sha256).hexdigest()) for slot,name in prior['adapter_negative_prerequisites'].get('service_roles',{}).items()}
    if not credentials:
        acl=json.loads((ROOT/'docs/evidence/PACKAGE-0090-G3F-4-INSTALLED-ACL.json').read_text())
        credentials={slot:(name,hmac.new(seed,('G3F4-TIMING/'+slot).encode(),hashlib.sha256).hexdigest()) for slot,name in acl['service_roles'].items()}
    if set(credentials)!={'AUDITOR','VERIFIER','ISSUER','EXECUTOR'}:raise RuntimeError('Four identified services required')
    for slot,(name,pw) in credentials.items():
        if name!='g3f4_'+slot.lower()+'_cc2941797db3':raise RuntimeError('Unexpected rehearsal login')
    credentials['ADMIN']=('postgres',hmac.new(seed,b'G3F4-TIMING/ADMIN',hashlib.sha256).hexdigest())
    password_file=private/'postgres-password';password_file.write_text(credentials['ADMIN'][1],encoding='ascii')
    started=False
    try:
        command(['docker','start',CONTAINER]);started=True
        deadline=time.monotonic()+45
        while time.monotonic()<deadline:
            ready=subprocess.run(['docker','exec',CONTAINER,'pg_isready','-U','postgres','-d','g3f4'],capture_output=True)
            if ready.returncode==0:break
            time.sleep(.2)
        else:raise RuntimeError('STOP: disposable PostgreSQL startup timeout')
        d,_,_=identity()
        ports=d['NetworkSettings']['Ports']['5432/tcp']
        if len(ports)!=1 or ports[0]['HostIp']!='127.0.0.1':raise RuntimeError('STOP: localhost mapping mismatch')
        port=int(ports[0]['HostPort']);record['localhost_port']=port
        def sql(statement):
            identity()
            q=subprocess.run(['docker','exec','-i',CONTAINER,'psql','-X','-U','postgres','-d','g3f4','-At','-v','ON_ERROR_STOP=1'],input=statement,text=True,capture_output=True)
            if q.returncode:raise RuntimeError('STOP: disposable administrative SQL failed (details remain private)')
            return q.stdout.strip()
        server=json.loads(sql("SELECT json_build_object('version',current_setting('server_version'),'version_num',current_setting('server_version_num'),'encoding',current_setting('server_encoding'),'locale',datcollate,'ctype',datctype) FROM pg_database WHERE datname=current_database();"))
        if not server['version'].startswith('18.4 ') or server['version_num']!='180004' or server['encoding']!='UTF8':raise RuntimeError('STOP: PG18.4 UTF8 mismatch')
        record['server']=server
        record['docker_version']=json.loads(command(['docker','version','--format','{{json .}}']))
        snapshot_sql="""SELECT json_build_object(
          'policies',(SELECT json_agg(json_build_object('version',policy_version,'digest',encode(policy_digest,'hex'),'canonical',encode(canonical_policy,'hex'),'effective_from',effective_from) ORDER BY policy_version) FROM offline_deadline_policy),
          'roles',(SELECT json_agg(json_build_object('name',rolname,'login',rolcanlogin,'inherit',rolinherit,'superuser',rolsuper,'createdb',rolcreatedb,'createrole',rolcreaterole,'replication',rolreplication,'bypassrls',rolbypassrls) ORDER BY rolname) FROM pg_roles WHERE rolname LIKE 'g3f4_%' OR rolname LIKE 'flooow_offline_%'),
          'readiness',(SELECT json_agg(json_build_object('incarnation',incarnation_id,'state',state,'healthy',watchdog_healthy,'policy_version',policy_version,'policy_digest',encode(policy_digest,'hex'))) FROM offline_readiness),
          'bindings',(SELECT count(*) FROM offline_binding_header),
          'function_acl_digest',(SELECT encode(sha256(convert_to(string_agg(p.oid::text||':'||coalesce(p.proacl::text,'NULL'),'|' ORDER BY p.oid),'UTF8')),'hex') FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname IN ('public','offline_crypto')));"""
        before=json.loads(sql(snapshot_sql));record['administrative_snapshot_before']=before
        if before['bindings']!=0 or any(row['state']!='NOT_READY' or row['healthy'] for row in before['readiness']):raise RuntimeError('STOP: timing-only NOT_READY posture required')
        fixture=json.loads(FIXTURE1.read_text())
        if len(before['policies'])!=1 or before['policies'][0]['version']!='fixture-1' or before['policies'][0]['canonical']!=fixture['canonical_policy_hex'] or before['policies'][0]['digest']!=fixture['canonical_policy_sha256']:raise RuntimeError('STOP: historical policy mismatch')
        sql('\n'.join("ALTER ROLE "+name+" PASSWORD '"+pw+"';" for name,pw in credentials.values()))
        config=f'url=jdbc:postgresql://127.0.0.1:{port}/g3f4\nproject={PROJECT}\nvolume={VOLUME}\ncontainer={CONTAINER}\nincarnation={old["timing_fixture"]["incarnation"]}\n'
        for slot,(name,pw) in credentials.items():config+=f'{slot}.name={name}\n{slot}.password={pw}\n'
        (work/'jdbc.properties').write_text(config,encoding='ascii')
        jars=sorted((Path.home()/'.gradle/caches/modules-2/files-2.1').rglob('*.jar'))
        cp=os.pathsep.join([str(ROOT/'applications/command-authority-ceremony/build/classes/kotlin/main')]+list(map(str,jars)))
        sources=['Package0090TimingQualification.java','Package0090RehearsalAdapter.java','Package0090RehearsalEndpoint.java']
        args='-cp\n"'+cp.replace('\\','/')+'"\n-d\n"'+work.as_posix()+'"\n'+''.join('"'+(ROOT/'scripts/validation'/name).as_posix()+'"\n' for name in sources)
        (work/'javac.args').write_text(args,encoding='utf-8');command(['javac','@'+str(work/'javac.args')])
        args='-cp\n"'+(str(work)+os.pathsep+cp).replace('\\','/')+'"\nPackage0090TimingQualification\n"'+(work/'jdbc.properties').as_posix()+'"\n"'+(work/'measurements.json').as_posix()+'"\n'
        (work/'java.args').write_text(args,encoding='utf-8')
        # Inherit only sanitized population progress; never print the private config.
        identity();started_at=time.time()
        executed=subprocess.run(['java','@'+str(work/'java.args')],timeout=180)
        record['measurement_start_epoch']=started_at;record['measurement_end_epoch']=time.time();record['java_exit_code']=executed.returncode
        study=json.loads((work/'measurements.json').read_text());record['study']=study
        after=json.loads(sql(snapshot_sql));record['administrative_snapshot_after']=after
        if before!=after:raise RuntimeError('STOP: immutable policy, role authority or readiness posture changed')
        record['fixture1_immutable_database_snapshot']='PASS_IDENTICAL';record['source_sql_and_acl_changed']=False
        distributions={name:distribution(pop.get('samples',[])) for name,pop in study.get('populations',{}).items()}
        record['distributions']=distributions
        successful=[x for pop in study.get('populations',{}).values() for x in pop.get('samples',[])]
        record['aggregate_distribution']=distribution(successful)
        complete=executed.returncode==0 and all(distributions.get(name,{}).get('count')==count for name,count in EXPECTED_COUNTS.items())
        worst=max((d.get('max_us',0) for d in distributions.values()),default=0)
        record['candidate_evaluation']=dict(measured_worst_case_us=worst,watchdog_max_margin_us=20000-worst,watchdog_max_margin_ratio=(20000-worst)/worst if worst else None,watchdog_max_to_observed_max_ratio=20000/worst if worst else None,health_budget_requirement_us=10000+2*worst,health_cadence_ratio=150000/10000,health_window_fraction_of_preflight_ttl=.15,minimum_watchdog_max_for_predeclared_2x_margin_us=math.ceil(2*worst),measured_requirement_is_not_authorized=True)
        qualified=complete and worst<20000 and 20000>=2*worst and 150000>=10000+2*worst
        record['transport_populations_complete']=complete;record['candidate_timing_qualified']=qualified
        record['timing_gate']='ELIGIBLE_FOR_POSITIVE_READINESS_PHASE_NOT_H01_CLOSURE' if qualified else 'HOLD_CANDIDATE_NOT_QUALIFIED'
        record['G3F4_H01']='OPEN';record['fixture2_created']=False
        print(json.dumps({'distributions':distributions,'candidate_evaluation':record['candidate_evaluation'],'timing_gate':record['timing_gate']},indent=2),flush=True)
    except BaseException as failure:
        record['stop_reason_class']=type(failure).__name__;record['stop_reason']=str(failure) if isinstance(failure,RuntimeError) else 'Measurement tooling failure; inspect private logs without exposing credentials'
        record['timing_gate']='HOLD_EXECUTION_STOP';record['G3F4_H01']='OPEN';record['fixture2_created']=False
        save();raise
    finally:
        if started:command(['docker','stop',CONTAINER])
        for name in ['jdbc.properties']:
            path=work/name
            if path.exists():path.unlink()
        if password_file.exists():password_file.unlink()
        historical_after={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in HISTORICAL+[FIXTURE1]}
        record['historical_hashes_after']=historical_after;record['historical_reports_unchanged']=historical==historical_after
        record['disposable_end_state']='STOPPED';record['private_plaintext_credentials_erased']=True;save()
    return work

def publish_hold(work):
    record=json.loads((Path(work)/'record.json').read_text())
    if record.get('timing_gate')!='HOLD_CANDIDATE_NOT_QUALIFIED' or record.get('candidate_timing_qualified') is not False or not record.get('transport_populations_complete'):
        raise RuntimeError('This disposition writer requires a recorded candidate rejection')
    if not record.get('historical_reports_unchanged') or record['administrative_snapshot_before']!=record['administrative_snapshot_after']:
        raise RuntimeError('Historical policy/report integrity not proven')
    evidence=ROOT/'docs/evidence';common={k:record[k] for k in ('baseline','disposable_project','disposable_volume','postgres_image_digest','identity','protected_database_connection','protected_volume_mount','production_secret_use','disposable_end_state','private_plaintext_credentials_erased')}
    common.update(scope='REHEARSAL_ONLY_MEASUREMENT_AND_CANDIDATE_REJECTION',G3F_4_REHEARSAL_FIXTURE_TIMING_QUALIFICATION='HOLD',G3F4_H01='OPEN',counts=dict(BLOCKER=0,HIGH=1,MEDIUM=0,LOW=0),NEXT_GATE='G3F_4_REHEARSAL_TEMPORAL_BOUNDS_REVIEW')
    classifications=[
      dict(category='A_SECURITY_AUTHORITY_INVARIANT',values='Database clock, finite positive checked int8 durations, actual<=approved maximum, deadline nesting, exact immutable approved policy version/digest, current readiness and mandatory watchdog, no future heartbeat acceptance, authenticated receipt issue/expiry and no renewal',changed=False,normative_basis='ADR expiry/concurrency and SPEC18/21.2/21.3/25'),
      dict(category='B_LIVENESS_FRESHNESS_ENGINEERING_PARAMETERS_WITH_SECURITY_RELEVANCE',values='Numeric watchdog enforcement interval and its maximum; health maximum age and its approved maximum',meaning='Numbers are separately approved bounded parameters. They affect the stale-authority/revocation envelope and cannot be freely widened. Guard meaning, mandatory enforcement and approved-bound checks remain category A.',normative_basis='ADR representation/design work; SPEC18 and 21.2'),
      dict(category='C_FIXTURE_ONLY_TEST_VALUES',values='Historical fixture-1 100/200 us watchdog pairs and proposed rehearsal-only 10000/20000 us interval,150000/200000 us health pairs',status='Historical pair stays NOT QUALIFIED; candidate rejected; no fixture-2 canonical bytes/digest or policy row created'),
      dict(category='A_FIXED_FOR_THIS_AUTHORIZATION',values='Preflight actual TTL 1000000 us; approved maximum TTL 2000000 us; immutable fixture-1; no production or SQL authority/ACL/wrapper changes',changed=False),
    ]
    c=record['candidate_evaluation'];d=record['distributions'];a=record['aggregate_distribution']
    findings=[dict(id='G3F4-H01',severity='HIGH',classification='REQUIRED_BEFORE_G3F_FINAL',status='OPEN',reason=f'Candidate watchdog maximum 20000 us is less than measured worst case {c["measured_worst_case_us"]:.0f} us; predeclared 2x safety margin is also not met. Even warmed/idle maximum {d["idle_warm"]["max_us"]:.0f} us independently exceeds the candidate maximum. This is a fixture/transport qualification gap, not evidence of SQL authorization failure.')]
    samples=common|dict(record=record,temporal_contract_classification=classifications,findings=findings,clock_authority='Both heartbeat timestamp and observation clock are generated by the same PostgreSQL cluster; no subtraction of unrelated client clocks',clock_anomaly_count=0,observed_transport_failure_count=0,measurement_successful_sample_count=a['count'],statistical_limitations=['One bounded sequential run; no confidence bound or production latency guarantee','Nearest-rank p99.9 is reported only at N>=1000; sparse extreme tail remains uncertain','Loaded traffic uses real Kotlin governed wrapper denials, not positive full catalog/frozen-domain workload','Load4/load8 mean additional governed sessions beside the ADMIN/AUDITOR measurement pair; total physical sessions 6/10','Fixed-delay background cadence regulates expected guard traffic; it is not a benchmark or authority expiry assertion'])
    disposition=common|dict(artifact_purpose='REJECTED_CANDIDATE_DISPOSITION_NOT_A_POLICY_FIXTURE',fixture_definition_created=False,fixture_id=None,policy_version=None,canonical_fields=None,canonical_policy_hex=None,canonical_policy_sha256=None,candidate_name='fixture-2',candidate=record['candidate'],candidate_evaluation=record['candidate_evaluation'],authorization='NONE_CANDIDATE_FAILED_USER_SECTION_6_STOP',production_policy_changed=False,fixture_1_mutated=False,sql_authority_changed=False,acl_changed=False,wrapper_semantics_changed=False,preflight_ttl_us=1000000,preflight_max_ttl_us=2000000,positive_readiness='NOT_EXECUTED_CANDIDATE_STOP',stale_readiness='NOT_EXECUTED_CANDIDATE_STOP',boundary_semantics='NOT_EXECUTED_CANDIDATE_STOP')
    for name,content in [('PACKAGE-0090-G3F-4-TIMING-SAMPLES.json',samples),('PACKAGE-0090-G3F-4-FIXTURE-002.json',disposition)]:
        with (evidence/name).open('w',encoding='utf-8',newline='\n') as output:json.dump(content,output,indent=2);output.write('\n')
    d=record['distributions'];a=record['aggregate_distribution'];c=record['candidate_evaluation'];config=record['study']['configuration']
    lines=['# Package 0090 — G3F.4 rehearsal fixture timing qualification','',
      '**STATUS: HOLD. G3F4-H01 remains OPEN/HIGH. Fixture-2 was not created or authorized.**','',
      'The candidate fails the explicit prerequisite MEASURED_WORST_CASE_US < WATCHDOG_MAX_US. '
      f'The largest observed DB-clock heartbeat handoff was {c["measured_worst_case_us"]:.0f} us against a candidate maximum of 20000 us. '
      f'Even the warmed idle population reached {d["idle_warm"]["max_us"]:.0f} us, so rejecting the candidate does not depend solely on reconnection cost. '
      f'No transport failure or negative DB-clock interval was observed in {a["count"]} successful samples. These observations do not demonstrate a SQL authorization defect.','',
      'User authorization section6 requires reporting the measured requirement and stopping for review when the candidate lacks adequate margin. '
      'Qualification therefore stops before fixture-2 creation, policy provisioning, positive S01 readiness and all dependent runtime gates. '
      'Historical HOLD reports and fixture-1 remain byte-identical; the disposable container is stopped and private plaintext credential files were erased.','',
      '## Distributions — microseconds','',
      '| Population | N | Min | p50 | p90 | p95 | p99 | p99.9 | Max | Mean | Sample SD |',
      '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for name in ('idle_warm','cold_reconnect','load4','load8'):
        row=d[name];values=[row[k] for k in ('count','min_us','p50_us','p90_us','p95_us','p99_us','p99_9_us','max_us','mean_us','sample_standard_deviation_us')]
        lines.append('| '+name+' | '+' | '.join('N/A (N<1000)' if value is None else (str(value) if isinstance(value,int) else f'{value:.3f}') for value in values)+' |')
    lines += ['', 'Percentiles use nearest rank. Standard deviation is the sample estimate (N−1). '
      'The p99.9 values at N=1000 are empirical order statistics with sparse-tail uncertainty. '
      'Combined statistics in the return fields are descriptive across intentionally different populations, not a single homogeneous latency model. '
      'Population order was idle/warm, cold/reconnect, load4, load8; no causal claim that load improves latency is made.','',
      '## Measurement and environment','',
      f'Baseline `{BASELINE}` was fetched, local=remote and clean before authorized tooling. '
      f'Exact reused project `{PROJECT}`, volume `{VOLUME}`, image `{IMAGE}` and private read-only `/review` mount were proven before contact. '
      'No other container/database/volume was selected. The endpoint was rediscovered after restart and verified again by the Java Docker identity guard before JDBC. '
      'Fresh seed-derived rehearsal ADMIN/service passwords were delivered only through private files; password rotation changed no role attributes, memberships or ACLs.','',
      f'PostgreSQL {config["postgres_version"]}; JDBC {config["jdbc_driver_version"]}; Microsoft JVM {config["jvm_version"]}; '
      f'{config["host_os"]} {config["host_os_version"]} ({config["host_architecture"]}); Docker client/server {record["docker_version"]["Client"]["Version"]}/{record["docker_version"]["Server"]["Version"]}. '
      'The previously pinned Linux/amd64 image is unchanged. CPU/memory controls are recorded verbatim in samples evidence; all numeric container quotas/limits are zero, meaning no explicit container-level quota. Enclosing Docker Desktop/host scheduling is not a guaranteed bound.','',
      'PGSimpleDataSource has no application pool in this experiment. Warm/load populations hold distinct physical ADMIN and AUDITOR connections, warmed by ten excluded handoffs. '
      'Each cold sample uses fresh ADMIN and AUDITOR backends; AUDITOR reconnection/setup deliberately occurs after the DB heartbeat update. '
      'ADMIN is autocommit READ_COMMITTED; AUDITOR is read-only REPEATABLE_READ with explicit rollback after each sample. '
      'Physical backend IDs are retained for every sample and were checked distinct. '
      'Authoritative age is EXTRACT(EPOCH FROM(clock_timestamp()-DB_RETURNED_HEARTBEAT))*1000000 inside PostgreSQL. '
      'Java monotonic clocks measure population durations; start/end client epoch metadata records overall audit elapsed time. Neither is used for authorization freshness.','',
      'Load4/load8 add four/eight persistent governed JDBC sessions to the two measuring sessions (total six/ten). '
      'The actual Kotlin GovernedTransaction invokes S02/S05/S07/S13 through the four real service identities on nonexistent scope and receives expected P0017 denials. '
      f'Completed background calls: load4={record["study"]["populations"]["load4"]["background_wrapper_calls"]}, load8={record["study"]["populations"]["load8"]["background_wrapper_calls"]}. '
      'A 10 ms fixed delay after each completed call regulates traffic without catch-up queues; this is not an expiry assertion or throughput stress test. '
      'Positive catalog/crypto/frozen-domain workload was not simulated or claimed. The tested lighter guard traffic already suffices to reject this candidate. '
      f'Total bounded measurement audit elapsed time: {record["measurement_end_epoch"]-record["measurement_start_epoch"]:.3f} s; Java monotonic population durations are also retained independently.','',
      '## Temporal classification and preserved invariants','',
      'ADR0090 leaves approved numeric policy values and watchdog packaging to governed engineering work. SPEC18/21.2/21.3/25 fixes the security meaning. '
      'Category A includes DB time, finite positive actual/max bounds, checked arithmetic, deadline nesting, mandatory trusted watchdog, canonical version/digest binding, no future heartbeat, receipt MAC and non-renewal. '
      'Category B consists of separately approved watchdog enforcement cadence/max and health freshness/max; these are engineering parameters with security relevance to stale/revoke bounds, never free configuration. '
      'Category C consists of historical fixture-1 test numbers and the explicitly experimental candidate. The authorized preflight TTL 1000000/max2000000 us is fixed for this task.','',
      'A newly qualified immutable version would still deny age beyond its actual health window and future timestamps; no optional flag, grace, fallback, receipt renewal, privilege or SQL change is proposed. '
      'Source health checks deny age > actual window (equality is not denied by that predicate); authenticated preflight validity is issued_at <= now < expires_at (equality at receipt expiry is expired). '
      'These source rules are recorded for future boundary tests and are not represented as runtime boundary proof. '
      'The candidate health window is 15 watchdog cadences and 15% of the fixed actual preflight TTL. Those ratios alone do not qualify it, and no stale heartbeat under new bounds was accepted.','',
      '## Candidate rejection and exact review handoff','',
      'The safety rule was recorded before measurement: watchdog maximum >= 2× observed maximum, observed maximum strictly below watchdog maximum, and health window >= cadence + 2× observed maximum. '
      'This factor is an empirical rehearsal safety margin, not a statistical confidence guarantee or new policy authority.','',
      '| Check | Result |','|---|---|',
      '| Candidate watchdog interval / maximum | 10000 / 20000 us |',
      f'| Measured maximum | {c["measured_worst_case_us"]:.0f} us |',
      f'| Maximum minus measured maximum | {c["watchdog_max_margin_us"]:.0f} us |',
      f'| Headroom ratio (max−observed)/observed | {c["watchdog_max_margin_ratio"]:.10f} ({100*c["watchdog_max_margin_ratio"]:.4f}%) |',
      f'| Candidate max / observed max | {c["watchdog_max_to_observed_max_ratio"]:.10f} |',
      f'| Minimum max required by declared 2× rule | {c["minimum_watchdog_max_for_predeclared_2x_margin_us"]} us; NOT AUTHORIZED |',
      '| Candidate health window / maximum | 150000 / 200000 us |',
      f'| Cadence + 2× observed maximum | {c["health_budget_requirement_us"]:.0f} us; exceeds candidate actual window |','',
      'NEXT_GATE=G3F_4_REHEARSAL_TEMPORAL_BOUNDS_REVIEW. Review the measured lower requirements above against SPEC18 enforcement/revocation/deadline bounds, then govern a revised experimental candidate explicitly. '
      'No larger number was installed or adopted. A revised experiment must qualify transport and then prove at least 100 actual S01 positive cycles plus stale/future/missing/incarnation/policy/receipt boundaries before closing H01. '
      'Full positive frozen/catalog/crypto workload and scheduler tails remain required; passing this necessary transport predicate alone would never close H01.','',
      'The requested FIXTURE-002 JSON is a rejection/disposition artifact, not a fixture definition. Its fixture ID/version/canonical fields/bytes/digest are null. '
      'Database policy inventory still contains only the exact fixture-1 row with unchanged canonical bytes, digest and effective_from. '
      'The timing readiness row remains NOT_READY/unhealthy with ineligible placeholder manifests, zero bindings, unchanged operational role attributes and identical function ACL digest.','',
      '## Return fields','', '| Field | Result |','|---|---|']
    fields=dict(BASELINE=BASELINE,DISPOSABLE_ENVIRONMENT_IDENTITY='EXACT_PASS',TIMING_SAMPLE_COUNT_WARM=1000,TIMING_SAMPLE_COUNT_COLD=100,TIMING_SAMPLE_COUNT_LOAD4=1000,TIMING_SAMPLE_COUNT_LOAD8=1000,TIMING_MIN_US=a['min_us'],TIMING_P50_US=a['p50_us'],TIMING_P95_US=a['p95_us'],TIMING_P99_US=a['p99_us'],TIMING_MAX_US=a['max_us'],TEMPORAL_CONTRACT_CLASSIFICATION='A_INVARIANTS_PRESERVED; B_GOVERNED_ENGINEERING_PARAMETERS; C_REHEARSAL_TEST_VALUES',CANDIDATE_WATCHDOG_INTERVAL_US=10000,CANDIDATE_WATCHDOG_MAX_US=20000,WATCHDOG_MAX_MARGIN_US=c['watchdog_max_margin_us'],WATCHDOG_MAX_MARGIN_RATIO=c['watchdog_max_margin_ratio'],CANDIDATE_HEALTH_WINDOW_US=150000,CANDIDATE_HEALTH_WINDOW_MAX_US=200000,PREFLIGHT_TTL_US=1000000,PREFLIGHT_MAX_TTL_US=2000000,FIXTURE_1_MUTATED='NO',FIXTURE_2_CREATED='NO_REJECTION_ARTIFACT_ONLY',POSITIVE_READINESS='NOT_EXECUTED_CANDIDATE_STOP',STALE_READINESS='NOT_EXECUTED_CANDIDATE_STOP',BOUNDARY_SEMANTICS='NOT_EXECUTED_CANDIDATE_STOP',G3F4_H01='OPEN',BLOCKER_COUNT=0,HIGH_COUNT=1,MEDIUM_COUNT=0,LOW_COUNT=0)
    for name in ('REAL_ADAPTER_E2E','FROZEN_OPERATIONAL_PARITY','S10_S14_REAL_RUNTIME','ORIGINAL_INPUT_RUNTIME_PARITY','S13_COLD_RUNTIME','ALL18_NEGATIVE_MATRIX','REAL_ROLLBACK','CONCURRENCY_SEMANTICS','RESTART_RECOVERY'):
        fields[name]='NOT_RESUMED_H01_OPEN; PRIOR_PARTIAL_EVIDENCE_PRESERVED'
    fields.update(G3F_4_ISOLATED_POSTGRES18_REHEARSAL='HOLD',PROTECTED_DATABASE_CONNECTION='NO',PROTECTED_VOLUME_MOUNT='NO',PRODUCTION_SECRET_USE='NO',NEXT_GATE=common['NEXT_GATE'])
    lines += [f'| {key} | {value} |' for key,value in fields.items()]
    lines += ['', 'Checkpoint branch: `checkpoint/package-0090-cloud-handoff`; commit local/remote equality and clean worktree are checked after this evidence commit. The artifact cannot contain its own final SHA.', '',
      'Evidence: [raw samples and metadata](PACKAGE-0090-G3F-4-TIMING-SAMPLES.json), [candidate rejection, no fixture](PACKAGE-0090-G3F-4-FIXTURE-002.json).','']
    with (evidence/'PACKAGE-0090-G3F-4-TIMING-QUALIFICATION.md').open('w',encoding='utf-8',newline='\n') as output:output.write('\n'.join(lines))
    print('TIMING_EVIDENCE_CREATED; FIXTURE_2_NOT_CREATED; HISTORICAL_REPORTS_PRESERVED')

if __name__=='__main__':
    import argparse
    cli=argparse.ArgumentParser();cli.add_argument('--publish-hold',type=Path);options=cli.parse_args()
    if options.publish_hold:publish_hold(options.publish_hold)
    else:measure()
