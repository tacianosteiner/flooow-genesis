"""Strictly disposable G3F.4 bootstrap. Never uses repository database configuration.

Stops on any migration failure; does not repair history or installation state.
Private scratch contains rehearsal-only credentials and is never an evidence input.
"""
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import tempfile
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_HEAD = '40a4b489da5013d89814552980dbe6f80ebc9a23'
FROZEN = '19131bb9cd655312252c8c83f0f78e7c0742274f'
IMAGE = 'sha256:07fc165de5bb569d822460e2df645c5489f99220fc2cb16c86596d39db394561'
BINARY = '5aeedcdb693442b7738b6f33604e059094f584af29d1879bf35482ca06ef63b5'
MIGRATIONS = ROOT / 'applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration'

def run(args, **kwargs):
    result = subprocess.run(args, capture_output=True, **kwargs)
    if result.returncode:
        raise RuntimeError(f'Command failed ({result.returncode}): {args[0]}')
    return result.stdout

def sha(data):
    return hashlib.sha256(data).hexdigest()

def bootstrap():
    run(['git','fetch','origin'])
    for ref in ('HEAD','origin/checkpoint/package-0090-cloud-handoff'):
        if run(['git','rev-parse',ref]).decode().strip() != EXPECTED_HEAD:
            raise RuntimeError('Baseline mismatch')
    # Tooling itself is authorized; reject all other working-tree changes.
    changed = run(['git','status','--porcelain']).decode().splitlines()
    allowed = ('scripts/validation/package_0090_g3f4_rehearsal.py',
               'scripts/validation/Package0090RehearsalFlyway.java',
               'scripts/validation/Package0090RehearsalAdapter.java',
               'scripts/validation/Package0090RehearsalTiming.java',
               'scripts/validation/Package0090RehearsalEndpoint.java',
               'scripts/validation/package_0090_g3f4_catalog.py',
               'scripts/validation/package_0090_g3f4_runtime.py',
               'scripts/validation/package_0090_g3f4_evidence.py',
               'scripts/validation/package_0090_g3f4_timing.py')
    if any(line[3:].replace('\\','/') not in allowed for line in changed):
        raise RuntimeError('Unexpected worktree changes')
    review=json.loads((ROOT/'docs/evidence/PACKAGE-0090-G3F-3B-POST-H02-SECURITY-REVIEW.json').read_text(encoding='utf-8-sig'))
    if review.get('G3F_3B_IMPLEMENTATION_SECURITY_REVIEW')!='PASS' or any(
        review.get(k)!=0 for k in ('BLOCKER_COUNT','HIGH_COUNT','REQUIRED_PRE_REHEARSAL_MEDIUM_COUNT')):
        raise RuntimeError('Source review does not authorize rehearsal')
    work = Path(tempfile.mkdtemp(prefix='flooow-0090-g3f4-'))
    project = 'flooow-0090-g3f4-' + uuid.uuid4().hex[:12]
    volume, container = project + '-data', project + '-postgres'
    record = dict(disposable_project=project, disposable_volume=volume,
        postgres_image_digest=IMAGE, protected_database_connection='NO',
        protected_volume_mount='NO', production_secret_use='NO', baseline=EXPECTED_HEAD,
        initial_worktree='CLEAN_BEFORE_AUTHORIZED_TOOLING', stages={})
    record['committed_source_review']=review
    def save():
        (work/'record.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    save()
    print('PRIVATE_SCRATCH=' + str(work), flush=True)
    frozen = work/'migrations'; frozen.mkdir()
    inventory=[]
    for path in sorted(MIGRATIONS.glob('V*.sql')):
        version=int(path.name.split('__')[0][1:])
        if version>42: continue
        relative=path.relative_to(ROOT).as_posix()
        accepted=run(['git','show',FROZEN+':'+relative])
        current=run(['git','show','HEAD:'+relative])
        if current!=accepted or path.read_bytes().replace(b'\r\n',b'\n')!=accepted:
            raise RuntimeError('Frozen migration changed: '+path.name)
        (frozen/path.name).write_bytes(accepted)
        inventory.append(dict(name=path.name,git_content_sha256=sha(accepted),working_bytes_sha256=sha(path.read_bytes())))
    if len(inventory)!=42: raise RuntimeError('Expected 42 frozen migrations')
    record['frozen_migrations']=inventory
    canonical=next(MIGRATIONS.glob('V043__*.sql')); original=canonical.read_bytes()
    newline=b'\r\n' if b'\r\n' in original else b'\n'
    fence=newline.join([b'DO $$',b'BEGIN',b"    RAISE EXCEPTION USING ERRCODE = '55000',",b"        MESSAGE = 'Package 0090 V043 implementation closure is incomplete; execution denied';",b'END;',b'$$;'])
    if original.count(fence)!=1: raise RuntimeError('Fence identity mismatch')
    offset=original.index(fence); candidate=original[:offset]+original[offset+len(fence):]
    if candidate[:offset]+fence+candidate[offset:]!=original: raise RuntimeError('Unauthorized byte change')
    (frozen/canonical.name).write_bytes(candidate)
    record['v043']=dict(canonical_sha256=sha(original),rehearsal_sha256=sha(candidate),diff='ONLY_AUTHORIZED_INTERLOCK_REMOVAL',removed_offset=offset,removed_length=len(fence))
    native=ROOT/'applications/marketplace-operations-persistence-postgres/native/flooow_offline_mac32'
    shutil.copytree(native,work/'native')
    inspected=json.loads(run(['docker','image','inspect',IMAGE]))[0]
    if inspected['Id']!=IMAGE or inspected['Architecture']!='amd64' or inspected['Os']!='linux':
        raise RuntimeError('Pinned image mismatch')
    record['image']=dict(id=inspected['Id'],repo_digests=inspected['RepoDigests'],architecture=inspected['Architecture'],os=inspected['Os'])
    build='set -eu; cd /review/native; make with_llvm=no >/review/build.txt 2>&1; pg_config --version; openssl version'
    versions=run(['docker','run','--rm','--network','none','--mount',f'type=bind,source={work},target=/review','--entrypoint','sh',IMAGE,'-c',build]).decode().splitlines()
    actual=sha((work/'native/flooow_offline_mac32.so').read_bytes())
    record['native_build']=dict(sha256=actual,expected_sha256=BINARY,versions=versions)
    save()
    if actual!=BINARY: raise RuntimeError('STOP: binary SHA256 mismatch; not installed')
    seed=secrets.token_bytes(32)
    password=hashlib.sha256(seed+b'postgres-rehearsal-only').hexdigest()
    (work/'postgres-password').write_text(password,encoding='ascii')
    # New objects only; never enumerate or inspect existing databases/volumes.
    run(['docker','volume','create','--label','com.docker.compose.project='+project,volume])
    run(['docker','network','create','--label','com.docker.compose.project='+project,project])
    run(['docker','run','-d','--name',container,'--label','com.docker.compose.project='+project,
         '--network',project,'-p','127.0.0.1::5432','--mount',f'type=volume,source={volume},target=/var/lib/postgresql',
         '--mount',f'type=bind,source={work},target=/review,readonly',
         '-e','POSTGRES_PASSWORD_FILE=/review/postgres-password','-e','POSTGRES_DB=g3f4',
         '-e','POSTGRES_INITDB_ARGS=--encoding=UTF8 --locale=en_US.utf8',
         '--entrypoint','/usr/local/bin/docker-entrypoint.sh',IMAGE,'postgres'])
    details=json.loads(run(['docker','inspect',container]))[0]
    mounts=details['Mounts']
    if len(mounts)!=2 or {m.get('Name') for m in mounts if m['Type']=='volume'}!={volume}:
        raise RuntimeError('Unexpected mount; no connection authorized')
    record['mounts']=[dict(type=m['Type'],name=m.get('Name'),destination=m['Destination']) for m in mounts]
    port=details['NetworkSettings']['Ports']['5432/tcp'][0]['HostPort']
    record['container']=container; record['port']=int(port)
    save()
    for _ in range(60):
        r=subprocess.run(['docker','exec',container,'pg_isready','-U','postgres','-d','g3f4'],capture_output=True)
        if r.returncode==0: break
        time.sleep(1)
    else: raise RuntimeError('New disposable server unavailable')
    def sql(statement):
        return run(['docker','exec','-i',container,'psql','-X','-U','postgres','-d','g3f4','-v','ON_ERROR_STOP=1','-At'],input=statement.encode()).decode()
    record['server']=json.loads(sql("SELECT json_build_object('version',current_setting('server_version'),'version_num',current_setting('server_version_num'),'encoding',current_setting('server_encoding'),'locale',datcollate,'ctype',datctype) FROM pg_database WHERE datname=current_database();"))
    cache=Path.home()/'.gradle/caches/modules-2/files-2.1'
    jars=sorted(cache.rglob('*.jar'))
    cp=os.pathsep.join(map(str,jars))
    compile_args=work/'javac.args'
    compile_args.write_text('-cp\n"'+cp.replace('\\','/')+'"\n-d\n"'+str(work).replace('\\','/')+'"\n"'+str(ROOT/'scripts/validation/Package0090RehearsalFlyway.java').replace('\\','/')+'"\n',encoding='utf-8')
    with compile_args.open('a',encoding='utf-8') as f:f.write('"'+(ROOT/'scripts/validation/Package0090RehearsalEndpoint.java').as_posix()+'"\n')
    run(['javac','@'+str(compile_args)])
    def migrate(target):
        (work/'flyway.properties').write_text(f'url=jdbc:postgresql://127.0.0.1:{port}/g3f4\npassword={password}\nmigrations={frozen.as_posix()}\ntarget={target}\n',encoding='ascii')
        with (work/'flyway.properties').open('a',encoding='ascii') as f:f.write(f'project={project}\nvolume={volume}\ncontainer={container}\n')
        argfile=work/'java.args'
        argfile.write_text('-cp\n"'+(str(work)+os.pathsep+cp).replace('\\','/')+'"\nPackage0090RehearsalFlyway\n"'+str(work/'flyway.properties').replace('\\','/')+'"\n',encoding='utf-8')
        start=time.time()
        result=subprocess.run(['java','@'+str(argfile)],capture_output=True,text=True)
        log=(result.stdout+result.stderr).replace(password,'[REDACTED]')
        (work/f'flyway-{target}.txt').write_text(log,encoding='utf-8')
        record['stages'][f'flyway_{target}']=dict(exit_code=result.returncode,start_epoch=start,end_epoch=time.time(),log=log)
        record['flyway_history']=json.loads(sql("SELECT coalesce(json_agg(row_to_json(h)), '[]') FROM public.flyway_schema_history h;"))
        save()
        if result.returncode: raise RuntimeError('STOP: Flyway migration failed; no repair performed')
    migrate('042')
    print('V001_V042=PASS_FLYWAY_042',flush=True)
    # Separately governed defaults and native dependencies; no service authority added.
    owners=['control','verification','issuance','execution','audit','readiness','principal_lock','intent_audit']
    statements=[]
    for owner in owners:
        name='flooow_offline_'+owner+'_owner'
        statements.append(f'CREATE ROLE {name} NOLOGIN '+('INHERIT' if owner=='control' else 'NOINHERIT')+' NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;')
    for name in ['postgres']+['flooow_offline_'+o+'_owner' for o in owners]:
        for kind in ['TABLES','SEQUENCES','FUNCTIONS','TYPES','SCHEMAS','LARGE OBJECTS']:
            statements.append(f'ALTER DEFAULT PRIVILEGES FOR ROLE {name} REVOKE ALL ON {kind} FROM PUBLIC;')
    statements.append('GRANT USAGE ON SCHEMA public TO flooow_offline_control_owner;')
    sql('\n'.join(statements))
    install='set -eu; cp /review/native/flooow_offline_mac32.so "$(pg_config --pkglibdir)/"; cp /review/native/flooow_offline_mac32.control /review/native/flooow_offline_mac32--1.0.sql "$(pg_config --sharedir)/extension/"'
    run(['docker','exec',container,'sh','-c',install])
    sql('CREATE SCHEMA offline_crypto AUTHORIZATION postgres; CREATE EXTENSION pgcrypto VERSION \'1.4\' SCHEMA offline_crypto; CREATE EXTENSION flooow_offline_mac32 VERSION \'1.0\'; REVOKE ALL ON SCHEMA offline_crypto FROM PUBLIC; REVOKE ALL ON ALL FUNCTIONS IN SCHEMA offline_crypto FROM PUBLIC; GRANT USAGE ON SCHEMA offline_crypto TO flooow_offline_readiness_owner; GRANT EXECUTE ON FUNCTION offline_crypto.hmac(bytea,bytea,text), offline_crypto.timing_safe_equal32(bytea,bytea) TO flooow_offline_readiness_owner;')
    record['native_catalog']=json.loads(sql("SELECT json_agg(json_build_object('name',p.proname,'identity',pg_get_function_identity_arguments(p.oid),'owner',pg_get_userbyid(p.proowner),'volatility',p.provolatile,'strict',p.proisstrict,'parallel',p.proparallel,'security_definer',p.prosecdef,'acl',p.proacl::text,'symbol',p.prosrc,'library',p.probin)) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='offline_crypto';"))
    record['native_mac32_runtime']=sql("SELECT offline_crypto.timing_safe_equal32(decode(repeat('01',32),'hex'),decode(repeat('01',32),'hex')),offline_crypto.timing_safe_equal32(decode(repeat('01',32),'hex'),decode(repeat('02',32),'hex')); ").strip()
    save()
    print('NATIVE_RUNTIME_LOAD=PASS; MAC32=t|f',flush=True)
    migrate('043')
    print('V043_REHEARSAL_MIGRATION=PASS',flush=True)
    save()

if __name__=='__main__':
    bootstrap()
