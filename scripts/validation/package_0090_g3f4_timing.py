"""Reproduce the necessary watchdog freshness experiment without activating readiness."""
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import uuid
import package_0090_source_gate as source

def probe(work):
    work=Path(work);r=json.loads((work/'record.json').read_text());c=r['container']
    inspected=json.loads(subprocess.check_output(['docker','inspect',c]))[0]
    if inspected['Config']['Labels']['com.docker.compose.project']!=r['disposable_project']:
        raise RuntimeError('Disposable identity mismatch')
    r['port']=int(inspected['NetworkSettings']['Ports']['5432/tcp'][0]['HostPort'])
    credentials=json.loads((work/'service-credentials.json').read_text())
    if not r.get('timing_fixture'):
        incarnation,deployment,lineage=(str(uuid.uuid4()) for _ in range(3))
        key=hashlib.sha256(secrets.token_bytes(32)+b'rehearsal-timing-key').hexdigest();digest=r['policy']['digest']
        statement=f"BEGIN; INSERT INTO public.offline_readiness VALUES ('{deployment}','{incarnation}','NOT_READY',1,'fixture-1',decode('{digest}','hex'),'\\x01','\\x01',clock_timestamp(),false); INSERT INTO public.offline_preflight_key VALUES ('{incarnation}','{lineage}',1,'ACTIVE',decode('{key}','hex'),sha256(decode('{key}','hex'))); COMMIT;"
        subprocess.run(['docker','exec','-i',c,'psql','-X','-U','postgres','-d','g3f4','-At','-v','ON_ERROR_STOP=1'],input=statement,text=True,capture_output=True,check=True)
        r['timing_fixture']=dict(incarnation=incarnation,deployment=deployment,state='NOT_READY',eligible_for_operation=False,placeholder_manifests='NEGATIVE_PREREQUISITE_ONLY_NEVER_ACTIVATED')
    password=(work/'postgres-password').read_text();name,secret=credentials['AUDITOR']
    (work/'timing.properties').write_text(f'url=jdbc:postgresql://127.0.0.1:{r["port"]}/g3f4\npassword={password}\nauditor={name}\nauditor_password={secret}\n',encoding='ascii')
    with (work/'timing.properties').open('a',encoding='ascii') as f:f.write(f'project={r["disposable_project"]}\nvolume={r["disposable_volume"]}\ncontainer={c}\n')
    cp=os.pathsep.join(map(str,sorted((Path.home()/'.gradle/caches/modules-2/files-2.1').rglob('*.jar'))))
    (work/'timing-javac.args').write_text('-cp\n"'+cp.replace('\\','/')+'"\n-d\n"'+work.as_posix()+'"\n"'+(source.ROOT/'scripts/validation/Package0090RehearsalTiming.java').as_posix()+'"\n')
    with (work/'timing-javac.args').open('a',encoding='utf-8') as f:f.write('"'+(source.ROOT/'scripts/validation/Package0090RehearsalEndpoint.java').as_posix()+'"\n')
    subprocess.run(['javac','@'+str(work/'timing-javac.args')],capture_output=True,check=True)
    (work/'timing-java.args').write_text('-cp\n"'+(str(work)+os.pathsep+cp).replace('\\','/')+'"\nPackage0090RehearsalTiming\n"'+(work/'timing.properties').as_posix()+'"\n')
    result=subprocess.run(['java','@'+str(work/'timing-java.args')],capture_output=True,text=True,check=True,timeout=60)
    samples=[dict(age_us=float(line.split('|')[0]),isolation=line.split('|')[1],read_only=line.split('|')[2]) for line in result.stdout.splitlines() if '|' in line]
    if len(samples)!=40:raise RuntimeError('Incomplete timing experiment')
    r['watchdog_freshness_probe']=dict(policy_actual_us=100,policy_approved_max_us=200,samples=samples,sample_count=40,minimum_us=min(x['age_us'] for x in samples),maximum_us=max(x['age_us'] for x in samples),eligible_sample_count=sum(x['age_us']<=100 for x in samples),scope='NECESSARY_FRESHNESS_PREDICATE_ONLY_NOT_FULL_WRAPPER_EXECUTION',connections='REAL_DISTINCT_ADMIN_AND_AUDITOR_JDBC',policy_changed=False)
    (work/'record.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in r['watchdog_freshness_probe'].items() if k!='samples'}))

if __name__=='__main__':probe(sys.argv[1])
