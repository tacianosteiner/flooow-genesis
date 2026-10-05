"""Expanded rehearsal-only timing; fixture definition is not activation.
Historical reports/fixture-1 are immutable. Failed timing stops before provisioning.
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
BASELINE='33bc82b4e2417aef7394dd0fe4557d3e9285b7f1'
PROJECT='flooow-0090-g3f4-cc2941797db3'
VOLUME=PROJECT+'-data'
CONTAINER=PROJECT+'-postgres'
IMAGE='sha256:07fc165de5bb569d822460e2df645c5489f99220fc2cb16c86596d39db394561'
HISTORICAL=[p for p in (ROOT/'docs/evidence').glob('PACKAGE-0090-G3F-4-*') if p.name!='PACKAGE-0090-G3F-4-FIXTURE-002.json' and not any(t in p.name for t in ('TEMPORAL-BOUNDS-REVIEW','TIMING-QUALIFICATION-2','POSITIVE-READINESS','E2E-RUNTIME','CONCURRENCY-2','RECOVERY-2','FINAL-REHEARSAL'))]
FIXTURE1=ROOT/'docs/evidence/PACKAGE-0090-G3F-3B-FIXTURE-001.json'
ALLOWED={'scripts/validation/package_0090_timing_qualification2.py','scripts/validation/Package0090TimingQualification2.java','docs/evidence/PACKAGE-0090-G3F-4-FIXTURE-002.json','docs/evidence/PACKAGE-0090-G3F-4-TEMPORAL-BOUNDS-REVIEW.md'}
EXPECTED_COUNTS={'idle_warm':5000,'cold_reconnect':500,'load4':2000,'load8':2000,'positive_realistic':1000}

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
    return dict(count=len(values),min_us=values[0],p50_us=quantile(.5),p90_us=quantile(.9),p95_us=quantile(.95),p99_us=quantile(.99),p99_9_us=quantile(.999),max_us=values[-1],mean_us=statistics.mean(values),sample_standard_deviation_us=statistics.stdev(values) if len(values)>1 else 0,quantile_method='NEAREST_RANK',p99_9_resolution_warning='N<1000 implies empirical p99.9 equals maximum; not a population tail guarantee')

def measure():
    command(['git','fetch','origin'])
    if any(command(['git','rev-parse',ref]).decode().strip()!=BASELINE for ref in ('HEAD','origin/checkpoint/package-0090-cloud-handoff')):
        raise RuntimeError('STOP: baseline mismatch')
    changed=command(['git','status','--porcelain']).decode().splitlines()
    if any(row[3:].replace('\\','/') not in ALLOWED for row in changed):raise RuntimeError('STOP: unexpected working changes')
    frozen=list((ROOT/'applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration').glob('V*.sql'))
    protected=HISTORICAL+[FIXTURE1]+frozen+[ROOT/'docs/adr/ADR-0090-governed-offline-field-proof-exclusive-capability-composition.md',ROOT/'docs/specifications/SPEC-0090-governed-offline-field-proof-exclusive-capability-composition.md']
    historical={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
    prior=json.loads((ROOT/'docs/evidence/PACKAGE-0090-G3F-4-RUNTIME-TESTS.json').read_text())
    if not any(f['id']=='G3F4-H01' and f['severity']=='HIGH' for f in prior['findings']):raise RuntimeError('Expected HIGH H01 missing')
    import package_0090_policy_fixture as codec
    fixture2=json.loads((ROOT/'docs/evidence/PACKAGE-0090-G3F-4-FIXTURE-002.json').read_text())
    values=[x['value'] for x in fixture2['fields'][1:]]
    if values[20:24]!=[50000,250000,400000,500000] or values[26:28]!=[1000000,2000000] or codec.encode('fixture-2',values).hex()!=fixture2['canonical_policy_hex'] or hashlib.sha256(bytes.fromhex(fixture2['canonical_policy_hex'])).hexdigest()!=fixture2['canonical_policy_sha256']:
        raise RuntimeError('STOP: authorized fixture-2 bytes or bounds mismatch')
    if fixture2.get('fixture_2_qualification')=='FAIL':raise RuntimeError('STOP: failed candidate requires fresh bounded authorization; do not repeat')
    d,private,old=identity()
    work=private/('timing-qualification2-'+uuid.uuid4().hex[:12]);work.mkdir()
    record=dict(baseline=BASELINE,initial_local_equals_remote=True,initial_worktree='CLEAN_BEFORE_AUTHORIZED_TOOLING',disposable_project=PROJECT,disposable_volume=VOLUME,postgres_image_digest=IMAGE,protected_database_connection='NO',protected_volume_mount='NO',production_secret_use='NO',identity='EXACT_LABEL_IMAGE_VOLUME_AND_PRIVATE_READONLY_MOUNT_PROVEN',historical_hashes_before=historical,container_constraints={k:d['HostConfig'][k] for k in ('NanoCpus','CpuQuota','CpuPeriod','CpusetCpus','CpuShares','Memory','MemorySwap','MemoryReservation')},candidate=dict(watchdog_interval_us=50000,watchdog_max_us=250000,health_window_us=400000,health_window_max_us=500000,preflight_ttl_us=1000000,preflight_max_ttl_us=2000000),safety_margin_rule='Predeclared: watchdog_max >= 2 * measured population maximum; health_window >= watchdog_interval + 2 * measured maximum; measured maximum < watchdog_max. This empirical factor is not a confidence bound or production SLO.',credential_handling='Fresh seed-derived rehearsal-only ADMIN/four service passwords; private files only; no role/ACL/owner changes; erase private plaintext after measurement.')
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
          'role_memberships',(SELECT json_agg(row_to_json(m)) FROM pg_auth_members m),
          'schema_acls',(SELECT json_agg(json_build_object('name',nspname,'owner',nspowner,'acl',nspacl) ORDER BY nspname) FROM pg_namespace WHERE nspname IN ('public','offline_crypto')),
          'table_acls',(SELECT json_agg(json_build_object('oid',c.oid,'owner',c.relowner,'acl',c.relacl) ORDER BY c.oid) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname IN ('public','offline_crypto')),
          'column_acls',(SELECT json_agg(json_build_object('oid',a.attrelid,'num',a.attnum,'acl',a.attacl) ORDER BY a.attrelid,a.attnum) FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname IN ('public','offline_crypto') AND a.attacl IS NOT NULL),
          'default_acls',(SELECT json_agg(row_to_json(x) ORDER BY oid) FROM pg_default_acl x),
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
        native=json.loads((ROOT/'docs/evidence/PACKAGE-0090-ED25519-NATIVE-REVIEW.json').read_text())
        vector=next(v for v in native['vectors'] if v['native']=='true')
        native_sql="offline_crypto.canonical_spki_ed25519_verify("+','.join("decode('"+vector[k]+"','hex')" for k in ('spki_hex','message_hex','signature_hex'))+")"
        u="(SELECT u FROM params)"
        intent="public.s2a_v042_authority_intent('GRANT',"+','.join([u]*6)+",decode('01','hex'),"+u+",'rehearsal','rehearsal',"+u+","+u+",'proof','manifest')"
        receipt="public.s2a_v042_authority_receipt("+intent+",'GRANT',"+u+",NULL,NULL,"+u+",1,'TRANSACTION_IDENTITY_DECISION_WRITE','ACTIVE')"
        native_sql=native_sql.replace("decode('"+vector['message_hex']+"','hex')", "(SELECT message FROM params)")
        positive_sql="""WITH params AS MATERIALIZED (SELECT ?::uuid u, ?::bytea message), functions AS MATERIALIZED (SELECT p.oid, p.proname,p.proacl,p.prosrc,pg_get_function_identity_arguments(p.oid) args FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname IN ('public','offline_crypto')),
          columns AS MATERIALIZED (SELECT a.attrelid,a.attnum,a.attname,a.attacl FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND a.attnum>0 AND NOT a.attisdropped),
          projection AS (SELECT encode(sha256(convert_to((SELECT string_agg(oid::text||':'||proname||':'||args||':'||coalesce(proacl::text,'NULL')||':'||prosrc,'|' ORDER BY oid) FROM functions)||(SELECT string_agg(attrelid::text||':'||attnum||':'||attname||':'||coalesce(attacl::text,'NULL'),'|' ORDER BY attrelid,attnum) FROM columns),'UTF8')),'hex') digest)
          SELECT """+native_sql+",(SELECT count(*) FROM functions),(SELECT count(*) FROM columns),octet_length(public.s2a_v041_signature_preimage('Ed25519',"+u+",'key','manifest')),octet_length(public.s2a_v042_text("+u+"::text)),length("+intent+"),length("+receipt+"),(SELECT digest FROM projection)"
        (work/'positive.sql').write_text(positive_sql,encoding='utf-8')
        record['positive_workload_sql']=positive_sql
        record['positive_workload_native_vector']=vector['name']
        config+='positive.sql='+(work/'positive.sql').as_posix()+'\npositive.message='+vector['message_hex']+'\n'
        (work/'jdbc.properties').write_text(config,encoding='ascii')
        jars=sorted((Path.home()/'.gradle/caches/modules-2/files-2.1').rglob('*.jar'))
        cp=os.pathsep.join([str(ROOT/'applications/command-authority-ceremony/build/classes/kotlin/main')]+list(map(str,jars)))
        sources=['Package0090TimingQualification2.java','Package0090RehearsalAdapter.java','Package0090RehearsalEndpoint.java']
        args='-cp\n"'+cp.replace('\\','/')+'"\n-d\n"'+work.as_posix()+'"\n'+''.join('"'+(ROOT/'scripts/validation'/name).as_posix()+'"\n' for name in sources)
        (work/'javac.args').write_text(args,encoding='utf-8');command(['javac','@'+str(work/'javac.args')])
        args='-cp\n"'+(str(work)+os.pathsep+cp).replace('\\','/')+'"\nPackage0090TimingQualification2\n"'+(work/'jdbc.properties').as_posix()+'"\n"'+(work/'measurements.json').as_posix()+'"\n'
        (work/'java.args').write_text(args,encoding='utf-8')
        # Inherit only sanitized population progress; never print the private config.
        identity();started_at=time.time()
        executed=subprocess.run(['java','@'+str(work/'java.args')],timeout=360)
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
        record['candidate_evaluation']=dict(measured_worst_case_us=worst,watchdog_max_margin_us=250000-worst,watchdog_max_margin_ratio=(250000-worst)/worst if worst else None,watchdog_max_to_observed_max_ratio=250000/worst if worst else None,health_budget_requirement_us=50000+2*worst,health_cadence_ratio=400000/50000,health_window_fraction_of_preflight_ttl=.4,minimum_watchdog_max_for_predeclared_2x_margin_us=math.ceil(2*worst),measured_requirement_is_not_authorized=True)
        qualified=complete and worst<250000 and 250000>=2*worst and 400000>=50000+2*worst
        record['transport_populations_complete']=complete;record['candidate_timing_qualified']=qualified
        record['timing_gate']='ELIGIBLE_FOR_POSITIVE_READINESS_PHASE_NOT_H01_CLOSURE' if qualified else ('HOLD_CANDIDATE_NOT_QUALIFIED' if complete else 'HOLD_INCOMPLETE_MEASUREMENT_WITH_OBSERVED_BOUND_FAILURE' if worst>=250000 or 250000<2*worst or 400000<50000+2*worst else 'HOLD_INCOMPLETE_MEASUREMENT')
        record['G3F4_H01']='OPEN';record['fixture2_created']=True;record['fixture2_database_installed']=False
        print(json.dumps({'distributions':distributions,'candidate_evaluation':record['candidate_evaluation'],'timing_gate':record['timing_gate']},indent=2),flush=True)
    except BaseException as failure:
        record['stop_reason_class']=type(failure).__name__;record['stop_reason']=str(failure) if isinstance(failure,RuntimeError) else 'Measurement tooling failure; inspect private logs without exposing credentials'
        record['timing_gate']='HOLD_EXECUTION_STOP';record['G3F4_H01']='OPEN';record['fixture2_created']=True;record['fixture2_database_installed']=False
        save();raise
    finally:
        if started:command(['docker','stop',CONTAINER])
        for name in ['jdbc.properties']:
            path=work/name
            if path.exists():path.unlink()
        if password_file.exists():password_file.unlink()
        historical_after={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
        record['historical_hashes_after']=historical_after;record['historical_reports_unchanged']=historical==historical_after
        record['disposable_end_state']='STOPPED';record['private_plaintext_credentials_erased']=True;save()
    return work


def publish_hold(work):
    """Preserve partial runtime evidence; never convert incomplete data to PASS."""
    record=json.loads((Path(work)/'record.json').read_text())
    c=record['candidate_evaluation'];worst=c['measured_worst_case_us']
    if not (worst>=250000 or 250000<2*worst or 400000<50000+2*worst):
        raise RuntimeError('Observed explicit bound failure is required for this STOP writer')
    if not record['historical_reports_unchanged'] or record['administrative_snapshot_before']!=record['administrative_snapshot_after']:
        raise RuntimeError('Historical or administrative integrity evidence missing')
    if identity()[0]['State']['Running']:raise RuntimeError('Disposable must be stopped')
    evidence=ROOT/'docs/evidence'
    populations=record['study']['populations']
    counts={name:len(populations.get(name,{}).get('samples',[])) for name in EXPECTED_COUNTS}
    distributions={name:distribution(populations.get(name,{}).get('samples',[])) for name in EXPECTED_COUNTS}
    evaluation=dict(measured_max_us=worst,maximum_limit_us=250000,strict_maximum_pass=worst<250000,
      ratio=250000/worst,required_ratio=2.0,ratio_pass=250000/worst>=2,
      two_times_requirement_us=2*worst,two_times_headroom_us=250000-2*worst,
      health_requirement_us=50000+2*worst,health_limit_us=400000,
      health_headroom_us=400000-(50000+2*worst),health_pass=400000>=50000+2*worst,
      absolute_maximum_headroom_us=250000-worst,all_populations_complete=counts==EXPECTED_COUNTS)
    complete=evaluation['all_populations_complete']
    common=dict(baseline=BASELINE,branch='checkpoint/package-0090-cloud-handoff',scope='REHEARSAL_ONLY',
      G3F_4_TEMPORAL_BOUNDS_REVIEW='PASS',FIXTURE_2_QUALIFICATION='FAIL',G3F4_H01='OPEN',
      G3F_4_ISOLATED_POSTGRES18_REHEARSAL='HOLD',counts=dict(BLOCKER=0,HIGH=1,MEDIUM=0,LOW=0),
      NEXT_GATE='G3F_4_REHEARSAL_TIMING_FAILURE_AND_08006_DIAGNOSIS',
      disposable_project=PROJECT,disposable_volume=VOLUME,postgres_image_digest=IMAGE,
      production_policy_changed=False,fixture_1_mutated=False,sql_authority_changed=False,
      acl_changed=False,wrapper_semantics_changed=False,protected_database_connection='NO',
      protected_volume_mount='NO',production_secret_use='NO',G3G_executed=False,
      main_merged=False,container_end_state='STOPPED',plaintext_credentials_erased=True)
    findings=[dict(id='G3F4-H01',severity='HIGH',status='OPEN',
      reason='Observed cold reconnect maximum exceeds both absolute limit and final 2x margin; load4 JDBC SQLSTATE08006 additionally interrupted expanded measurement. No SQL authorization defect or network root cause is inferred.',
      observed_max_us=worst,transport_failure_sqlstate=record['study'].get('failure_sqlstate'),
      required_before='G3F_FINAL',classification='FIXTURE_TIMING_AND_RUNTIME_EVIDENCE_GAP')]
    fixture_path=evidence/'PACKAGE-0090-G3F-4-FIXTURE-002.json'
    fixture=json.loads(fixture_path.read_text())
    canonical={k:fixture[k] for k in ('fixture_id','policy_version','canonical_policy_hex','canonical_policy_sha256','fields')}
    fixture.update(fixture_2_qualification='FAIL',database_installed=False,qualification_evidence='PACKAGE-0090-G3F-4-TIMING-QUALIFICATION-2.json',qualification_evaluation=evaluation,dependent_binding_manifest_receipt_goldens='NOT_GENERATED_TIMING_GATE_STOP')
    assert canonical=={k:fixture[k] for k in canonical}
    study=record['study']
    timing=common|dict(fixture=canonical,authorized_parameters=record['candidate'],
      requested_sample_counts=EXPECTED_COUNTS,successful_sample_counts=counts,
      total_successful_samples=sum(counts.values()),expanded_dataset_complete=complete,
      distributions=distributions,aggregate_distribution=record['aggregate_distribution'],
      acceptance=evaluation,findings=findings,record=record,
      corrected_disposition='FAIL_OBSERVED_REQUIRED_BOUNDS_WITH_INCOMPLETE_EXPANDED_DATASET',
      clock_authority='Heartbeat and observation timestamps originate from the same PostgreSQL clock. Client monotonic time is only descriptive duration.',
      negative_clock_ages_in_successful_samples=sum(x['age_us']<0 for v in populations.values() for x in v['samples']),
      reported_transport_failure_count=1,transport_failure_sqlstate=study.get('failure_sqlstate'),
      transport_failure_root_cause='UNRESOLVED; JDBC08006 is a connection failure category, not proof of database crash or SQL authorization failure',
      positive_realistic_workload_executed=False,
      tooling_validation='Measurement driver compiled and ran; corrected positive prepared-input path compiles but was not reached or runtime-validated after explicit STOP.',
      limitations=['Incomplete expanded dataset: load4 interrupted; load8 and positive-realistic unexecuted',
        'Nearest-rank p99.9 at cold N=500 is the observed maximum, not a population tail estimate',
        'Large tail and JDBC connection failure have no proven causal attribution',
        'No fixture-2 provisioning, S01 eligibility, boundary, complete ceremony, concurrency or durable-effect recovery proof',
        'Recorded pre/post snapshot covers policy bytes/activation, roles, readiness posture, binding count and function ACL digest. Broader schema/default/membership/column ACL snapshots are added to the corrected tooling but were not collected in this stopped run.'])
    pending=common|dict(status='NOT_EXECUTED_TIMING_GATE_STOP',prerequisite='FIXTURE_2_QUALIFICATION_PASS',findings=findings)
    readiness=pending|dict(actual_S01_positive_cycles_executed=0,required_positive_cycles=200,
      positive_readiness_pass_count=0,positive_readiness_failure_count=None,
      negatives={k:'NOT_EXECUTED' for k in ['missing_heartbeat','future_heartbeat','age399999','age400000','age400001','health_max500000','health_max500001','wrong_incarnation','wrong_deployment','policy_drift','expired_receipt','expiry_equality']},
      source_only_boundary_observation='Age > policy health actual denies; equality is not a stale-age rejection. Health approved maximum validates policy, not a runtime grace period. Expiry equality is expired. No runtime proof asserted.')
    e2e=pending|dict(complete_actual_ceremonies=0,required_complete_ceremonies=1,
      actual_wrapper_positive_coverage={f'S{i:02d}':'NOT_EXECUTED' for i in range(1,19)},
      current_task_full_runtime_phases_executed=0,
      pending=['S01-S18 complete actual Kotlin/JDBC/native/frozen041/042 ceremony','A/B isolation AA AB BA BB audit/mutation','Cold S13 claim','All18 positive and negative coverage','Rollback and ambiguous commit','Normal/offline and watchdog barrier'],
      historical_prerequisite_evidence='Historical adapter denials/native51/catalog ACL are retained as historical evidence only; not promoted to a complete ceremony.',
      privileged_helpers_used_in_end_to_end=None)
    concurrency=pending|dict(executed_cases=0,deadlock_count=None,double_effect_count=None,
      lost_update_count=None,unauthorized_renewal_count=None,
      required_barriers=['concurrent_bindings','shared_principal','S13','S14','S17_S18','normal_offline','watchdog'],
      no_zero_inferred_from_unexecuted_cases=True)
    recovery=pending|dict(restarts_after_real_durable_effects=0,preserved_identifiers=None,
      preserved_original_deadlines=None,receipt_renewal_count=None,
      historical_prerequisite_restart_is_not_full_recovery=True)
    for name,content in [('PACKAGE-0090-G3F-4-FIXTURE-002.json',fixture),('PACKAGE-0090-G3F-4-TIMING-QUALIFICATION-2.json',timing),('PACKAGE-0090-G3F-4-POSITIVE-READINESS.json',readiness),('PACKAGE-0090-G3F-4-E2E-RUNTIME.json',e2e),('PACKAGE-0090-G3F-4-CONCURRENCY-2.json',concurrency),('PACKAGE-0090-G3F-4-RECOVERY-2.json',recovery)]:
        with (evidence/name).open('w',encoding='utf-8',newline='\n') as f:json.dump(content,f,indent=2);f.write('\n')
    lines=['# Package 0090 - final isolated rehearsal disposition','',
      '**STATUS: HOLD. Temporal contract review PASS; fixture-2 qualification FAIL; G3F4-H01 OPEN/HIGH.**','',
      f'Observed maximum {worst:.0f} us exceeds authorized 250000 us. Ratio 250000/MAX={evaluation["ratio"]:.9f}, below 2.0. Required 2x={2*worst:.0f} us; headroom={evaluation["two_times_headroom_us"]:.0f} us. Required health 50000+2xMAX={evaluation["health_requirement_us"]:.0f} us exceeds 400000 by {-evaluation["health_headroom_us"]:.0f} us. The explicit user Section 5 STOP applies. No larger bounds are selected or approved.','',
      f'The dataset is incomplete: {sum(counts.values())} successful DB-clock observations; load4 interrupted with JDBC SQLSTATE08006. This is not a complete expanded qualification or a claimed positive workload. A failed observed bound is already sufficient to reject this candidate, while incomplete data independently prevents PASS. The connection failure root cause is unresolved. No production latency, SQL authorization defect or crash is inferred.','',
      '| Population | Successful / required | Min | p50 | p90 | p95 | p99 | p99.9 | Max | Mean | Sample SD |','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for name,n in EXPECTED_COUNTS.items():
        d=distributions[name]
        vals=[d.get(k) for k in ('min_us','p50_us','p90_us','p95_us','p99_us','p99_9_us','max_us','mean_us','sample_standard_deviation_us')]
        lines.append('| '+name+' | '+str(counts[name])+'/'+str(n)+' | '+' | '.join('NOT MEASURED' if v is None else f'{v:.3f}' for v in vals)+' |')
    lines+=['','All figures are microseconds. Percentiles use nearest rank; SD uses N-1. At cold N=500 the p99.9 equals the maximum and has inadequate extreme-tail resolution. Load4 figures describe only the partial 1029-sample population. Raw samples and environment metadata are in TIMING-QUALIFICATION-2.json. No missing population is treated as zero latency.','',
      'Fixture-2 was defined with the approved 29-field codec after contract review PASS; SHA256 28dd69e044c7646d51dd563ea85db96febe4024c816ba8a35b8b1703b65f9084. The canonical definition is retained with qualification FAIL and database_installed=false. Prior rejected disposition is preserved by baseline commit/hash reference. Fixture-1, historical HOLD evidence, V001-V042, canonical fenced V043, ADR/SPEC, wrappers and ACL authority are unchanged. Pre/post database snapshots match for the collected policy/role/readiness/function-ACL scope. Broader catalog snapshot tooling is compiled but not claimed as executed.','',
      'Only the proven exact disposable project/container/volume was contacted. PostgreSQL 18.4 and UTF8 were checked, with actual distinct ADMIN/AUDITOR JDBC sessions and fresh DB-clock ages. New rehearsal-only passwords were rotated only for existing postgres/four service roles; permissions/owners were not changed. The container is STOPPED and private plaintext password/properties files are erased. No protected database/volume, production secret, production policy, G3G, main merge or production deployment was used.','',
      'Required downstream artifacts record NOT_EXECUTED_TIMING_GATE_STOP: 200 positive S01 cycles; temporal negatives; fullS01-S18 ceremony; A/B matrix; rollback/ambiguous commit; barriers/concurrency; recovery after durable effects. Actual complete ceremonies=0. Deadlock/double-effect/lost-update/unauthorized-renewal recovery counts remain unknown, not fabricated zeros. Historical native/denial/prerequisite restart proofs do not replace these gates.','',
      'BLOCKER=0; HIGH=1; MEDIUM=0; LOW=0. Risk remains incomplete runtime evidence and an unqualified timing envelope, with unresolved 08006 under load. Final PASS and H01 closure are forbidden.','',
      'NEXT_GATE=G3F_4_REHEARSAL_TIMING_FAILURE_AND_08006_DIAGNOSIS. Next technically determined action is a bounded diagnostic design for the observed tail and connection failure, under new explicit execution authorization because Section 5 orders STOP. Preserve exact values and raw evidence; do not silently rerun/enlarge bounds, install policy or resume dependent runtime. Only after a newly authorized successful qualification and complete runtime proof can G3F_FINAL be reauthorized.','',
      'Validation: javac compiled the final driver; Python syntax compilation passed; canonical fixture decode/re-encode and SHA256 passed; raw counts/statistics and distinct physical backend checks passed; all evidence JSON parsed; prior disposition Git blob hash matched; historical byte hashes and collected pre/post snapshots matched; stopped container and erased credential files were verified. No positive-path runtime validation is claimed.', '',
      'Branch: checkpoint/package-0090-cloud-handoff. Evidence baseline: 33bc82b4e2417aef7394dd0fe4557d3e9285b7f1. The final commit is reported by Git after committing these artifacts; no self-referential commit hash is invented.']
    with (evidence/'PACKAGE-0090-G3F-4-FINAL-REHEARSAL.md').open('w',encoding='utf-8',newline='\n') as f:f.write('\n'.join(lines)+'\n')
    print(json.dumps(dict(status='HOLD',counts=counts,acceptance=evaluation,H01='OPEN',fixture2_installed=False),indent=2))

if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--publish-hold',type=Path)
    args=parser.parse_args()
    if args.publish_hold:publish_hold(args.publish_hold)
    else:measure()
