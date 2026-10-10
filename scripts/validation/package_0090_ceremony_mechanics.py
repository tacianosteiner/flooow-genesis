"""Disposable mechanical profile, not a ceremony runner or policy authorization.

Actual V001..V042 migrations and V040 append functions; extracted V043 table,
FK and signed-input trigger definitions. Never executes the fenced migration.
NO service wrappers/ACL qualification, host health, provider/domain effects or V6 IDs.
"""
from pathlib import Path
import csv
import hashlib
import io
import json
import math
import os
import re
import subprocess
import tempfile
import time
import uuid
from package_0090_policy_fixture import approved_fixture

ROOT=Path(__file__).resolve().parents[2]
BASE='f9dc0c9abddfc23f33a795f50c45472f06e02b2a'
IMAGE='sha256:07fc165de5bb569d822460e2df645c5489f99220fc2cb16c86596d39db394561'
MIGRATIONS=ROOT/'applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration'
V043=MIGRATIONS/'V043__create_governed_offline_field_proof_capability_composition.sql'
NATIVE=ROOT/'applications/marketplace-operations-persistence-postgres/native/flooow_offline_mac32'

def call(args,data=None,timeout=60):
    r=subprocess.run(args,input=data,text=True,capture_output=True,timeout=timeout)
    if r.returncode:
        # This harness has no secret arguments/parameters. Preserve diagnostics privately.
        raise RuntimeError(f'{args[0]} failed: '+r.stderr[-2000:])
    return r.stdout

def main():
    call(['git','merge-base','--is-ancestor',BASE,'HEAD'])
    source=V043.read_text(encoding='utf-8-sig')
    original=call(['git','show',BASE+':'+str(V043.relative_to(ROOT)).replace('\\','/')])
    assert source==original,'FROZEN_V043_CHANGED'
    name='flooow-0090-mechanics-'+uuid.uuid4().hex[:12]
    work=Path(tempfile.mkdtemp(prefix='flooow-0090-mechanics-'))
    print('PRIVATE_EVIDENCE='+str(work),flush=True)
    started=False
    try:
        # No canonical volume, no persisted PostgreSQL data, loopback port only.
        call(['docker','run','--detach','--name',name,'--label','flooow.scope=package0090-mechanics-only',
              '--tmpfs','/tmp','--tmpfs','/var/lib/postgresql','--mount',f'type=bind,source={NATIVE},target=/native-source,readonly',
              '-e','PGDATA=/tmp/pgdata','-e','POSTGRES_DB=benchmark_0090',
              '-e','POSTGRES_HOST_AUTH_METHOD=trust','-p','127.0.0.1::5432',
              '--entrypoint','docker-entrypoint.sh',IMAGE,'postgres'])
        started=True
        def sql(text):
            return call(['docker','exec','-i',name,'psql','-X','-w','-U','postgres','-d','benchmark_0090','-At','-v','ON_ERROR_STOP=1'],text)
        for _ in range(80):
            ready=subprocess.run(['docker','exec',name,'pg_isready','-U','postgres','-d','benchmark_0090'],capture_output=True)
            if ready.returncode==0:break
            time.sleep(.25)
        details=json.loads(call(['docker','inspect',name]))[0]
        assert details['Image']==IMAGE
        assert details['Config']['Labels']['flooow.scope']=='package0090-mechanics-only'
        assert not any(m['Type']=='volume' for m in details['Mounts'])
        ports=details['NetworkSettings']['Ports']['5432/tcp'];assert len(ports)==1 and ports[0]['HostIp']=='127.0.0.1'
        url='jdbc:postgresql://127.0.0.1:'+ports[0]['HostPort']+'/benchmark_0090'
        system=sql('SELECT system_identifier::text FROM pg_control_system();').strip()
        # Resolve the existing build's exact dependency closure offline. No old
        # private environment/classpath files or credential files are required.
        init=work/'mechanics-classpath.gradle'
        init.write_text("allprojects { afterEvaluate { if (path == ':applications:command-authority-ceremony') { tasks.register('package0090MechanicsClasspath') { doLast { println(configurations.testRuntimeClasspath.asPath) } } } } }\n",encoding='utf8',newline='\n')
        resolved=call([str(ROOT/'gradlew.bat'),'--offline','--no-configuration-cache','-q','-I',str(init),':applications:command-authority-ceremony:package0090MechanicsClasspath'],timeout=180)
        candidates=[line.strip() for line in resolved.splitlines() if 'flyway-core-13.2.0.jar' in line and 'postgresql-42.7.12.jar' in line]
        assert len(candidates)==1,'EXACT_BUILD_CLASSPATH_REQUIRED'
        classpath=candidates[0].replace('\\','/')
        args=work/'compile.args';java_source=ROOT/'scripts/validation/Package0090CeremonyMechanics.java'
        args.write_text('-cp\n"'+classpath+'"\n-d\n"'+str(work).replace('\\','/')+'"\n"'+str(java_source).replace('\\','/')+'"\n',encoding='utf8',newline='\n')
        call(['javac','@'+str(args)])
        def java(mode,*params):
            (work/'run.args').write_text('-cp\n"'+str(work).replace('\\','/')+os.pathsep+classpath+'"\nPackage0090CeremonyMechanics\n'+mode+'\n'+url+'\n'+system+'\n'+'\n'.join('"'+str(p).replace('\\','/')+'"' for p in params)+'\n',encoding='utf8',newline='\n')
            return call(['java','@'+str(work/'run.args')],timeout=180)
        (work/'migration.log').write_text(java('migrate',MIGRATIONS),encoding='utf8')
        assert sql('SELECT max(version::int) FROM flyway_schema_history WHERE success;').strip()=='42'
        # Table/constraint mechanics only. Do not remove or execute V043's interlock.
        ddl=re.findall(r'CREATE TABLE public\.offline_[a-z_]+ \(.*?\n\);',source,re.S)
        assert len(ddl)==15,len(ddl)
        fks=re.findall(r'ALTER TABLE public\.offline_[a-z_]+\s+ADD CONSTRAINT .*?;',source,re.S)
        expected=source[source.index('CREATE FUNCTION public.offline_internal_expected_attestation_guard()'):source.index('GRANT SELECT (binding_id) ON TABLE public.offline_expected_signed_attestation')]
        expected=re.sub(r'ALTER FUNCTION .*?;\n','',expected)
        fixture_sql='\n'.join(ddl+fks)+'\n'+expected+'\n'+''.join(f'CREATE ROLE bench_slot_{i} NOLOGIN;\n' for i in range(1,5))
        sql(fixture_sql)
        # Compile/install the existing native primitive inside this disposable only.
        call(['docker','exec','-u','0',name,'sh','-c','mkdir /tmp/native-build && cp /native-source/* /tmp/native-build/ && make -s -C /tmp/native-build with_llvm=no && make -s -C /tmp/native-build with_llvm=no install'],timeout=120)
        sql("CREATE FUNCTION bench_canonical_spki_ed25519_verify(bytea,bytea,bytea) RETURNS boolean AS '$libdir/flooow_offline_mac32','canonical_spki_ed25519_verify' LANGUAGE C IMMUTABLE STRICT PARALLEL SAFE;")
        policy=bytes.fromhex(approved_fixture()['canonical_policy_hex']);(work/'policy.bin').write_bytes(policy)
        samples=java('bench',work/'policy.bin',100)
        (work/'samples.csv').write_text(samples,encoding='utf8',newline='\n')
        rows=list(csv.DictReader(io.StringIO(samples)));measured=[r for r in rows if int(r['iteration'])>=0]
        assert len(rows)==110 and len(measured)==100
        def stats(values):
            ordered=sorted(values)
            return {f'p{p}_us':ordered[math.ceil(len(ordered)*p/100)-1] for p in (50,95,99)}|{'maximum_observed_us':ordered[-1]}
        summary={'scope':'DISPOSABLE_MECHANICS_NOT_ELIGIBLE_CEREMONY','baseline':BASE,'iterations':100,'warmup_iterations':10,
          'percentile_method':'nearest-rank; empirical sample, no tail bound','image':IMAGE,'pg_version':'18.4',
          'java_version':subprocess.run(['java','-version'],capture_output=True,text=True).stderr.splitlines()[0],
          'source_sha256':{str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in [java_source,Path(__file__),V043,MIGRATIONS/'V040__create_s2a_approval_governance.sql']},
          'fixture_ddl_sha256':hashlib.sha256(fixture_sql.encode()).hexdigest(),'fixture_policy_sha256':hashlib.sha256(policy).hexdigest(),
          'components':{k:stats([float(r[k]) for r in measured]) for k in measured[0] if k!='iteration'},
          'cold_first_iteration_total_us':float(rows[0]['total_us']),
          'limitations':['V043 extracted structures/FKs/trigger, not full migration/wrapper/ACL qualification',
             'Guard timings measure approval-expiry predicates only; full policy/host eligibility remains HOLD',
             'Fresh synthetic domain UUIDs; no real canonical domain evidence; four NOLOGIN slot fixtures',
             'No adversarial contention, runtime stall, supervision, ambiguous COMMIT or restart distribution',
             'Warm physical writer/JVM; query-first opens a fresh JDBC connection; connection startup outside measured transaction_setup'],
          'canonical_runtime_access':'NONE','production_authority':False,'policy_change_authority':False,'private_key_export':False}
        (work/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf8',newline='\n')
        print(json.dumps(summary['components']['total_us']),flush=True)
    finally:
        if started:call(['docker','rm','--force','--volumes',name])
    print('DISPOSABLE_REMOVED=YES',flush=True)

if __name__=='__main__':main()
