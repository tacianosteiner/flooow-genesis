"""Explicitly authorized isolated TEST_ONLY_NONCANONICAL successor experiment.

No canonical resources/credentials/IDs, no installed V043 migration, no numeric
policy authority. Root-owned external synthetic custody is separate from DB.
"""
from pathlib import Path
import subprocess,json,time,struct,hashlib,uuid,threading,copy,traceback,datetime,concurrent.futures,sys,base64
import codec
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).parent
NAME='flooow-0090-full-6800161';SCOPE='0090-full-binding-enforcement'
IMAGE='sha256:07fc165de5bb569d822460e2df645c5489f99220fc2cb16c86596d39db394561'
OUT=ROOT/'docs/evidence/package-0090-g3f4-full-binding-enforcement-qualification'
if '--output' in sys.argv:OUT=Path(sys.argv[sys.argv.index('--output')+1]).resolve()
V043=ROOT/'applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V043__create_governed_offline_field_proof_capability_composition.sql'
BASE='68001610df44dd17afc82a3d5ed575e8a0a59d71'
record={'input_head':BASE,'scope':'TEST_ONLY_NONCANONICAL','cases':[],'observations':[],'errors':[],'experimental_controls':{'abort_us':5000000,'observer_gate_lease_us':5000000,'cancel_to_terminate_us':200000,'registry_capacity':128,'receiver_poll_ms':20,'observer_pause_seconds':.1,'policy_authority':'NONE'},'canonical_access':False,'canonical_mutation':False}
stop=threading.Event();paused=threading.Event();health_lock=threading.Lock();observer_thread=None
def cmd(a,data=None,ok=True,timeout=30):
    r=subprocess.run(a,input=data,capture_output=True,text=True,encoding='utf-8',timeout=timeout)
    if ok and r.returncode:raise RuntimeError(str(a[:5])+': '+r.stderr[-1800:])
    return r
def ex(*a,data=None,user='postgres',ok=True,timeout=30):return cmd(['docker','exec','--user',user,'-i',NAME,*a],data,ok,timeout)
def sql(s,role='postgres',ok=True,timeout=30):return ex('psql','-X','-w','-h','/tmp/pgsock','-U',role,'-d','native_fixture','-At','-v','ON_ERROR_STOP=1',data=s,ok=ok,timeout=timeout)
def rootfile(path,b,mode='0444'):
    payload=base64.b64encode(b if isinstance(b,bytes) else b.encode()).decode()
    ex('sh','-c','base64 -d > "$1.next" && chmod "$2" "$1.next" && mv "$1.next" "$1"','sh',path,mode,user='0',data=payload)
def readjson(path):return json.loads(ex('cat',path,user='0').stdout)
def save(name,obj): (OUT/name).write_bytes((json.dumps(obj,indent=2)+'\n').encode())
def case(group,name,passed,detail):
    record['cases'].append({'group':group,'name':name,'result':'PASS_HANDLED' if passed else 'FAIL','detail':detail});print(group+'/'+name+': '+('PASS' if passed else 'FAIL'),flush=True)
def denial(group,name):
    t=time.monotonic_ns();r=sql('SELECT 1;','test_verifier',ok=False)
    case(group,name,r.returncode!=0 and ('FLOOOW_TEST_ENROLLMENT_DENIED' in r.stderr or 'canceling statement' in r.stderr),{'exit':r.returncode,'stderr':r.stderr,'elapsed_us':(time.monotonic_ns()-t)/1000})
    if record['cases'][-1]['result']!='FAIL':record['cases'][-1]['result']='PASS_DENIED'
def getheader():return json.loads(sql('SELECT to_jsonb(h)::text FROM public.offline_binding_header h;').stdout)
def boot():
    ex('rm','-f','/run/flooow-watchdog/enrollment-v1.sock','/run/flooow-watchdog/crash-supervisor','/run/flooow-watchdog/kill-receiver')
    ex('sh','-c','/usr/local/bin/flooow-test-supervisor >> /tmp/full.log 2>&1 &')
    end=time.monotonic()+20
    while time.monotonic()<end:
        if ex('pg_isready','-h','/tmp/pgsock','-U','postgres',ok=False).returncode==0:return
        time.sleep(.1)
    raise RuntimeError('Startup failed '+ex('tail','-n','20','/tmp/full.log',ok=False).stdout)
def snapshot():
    return sql("SELECT coalesce(json_agg(x),'[]'::json) FROM (SELECT pid,usesysid,datid,backend_start,state FROM pg_stat_activity WHERE usename LIKE 'test_%') x;").stdout
def observer_once():
    started=time.monotonic_ns();eligible=False;reason='UNKNOWN';headerhash=b'\0'*32
    try:
        joined=ex('sh','-c','for f in status approval attestation; do cat "/run/flooow-external/$f.json"; echo; done',user='0').stdout.splitlines()
        status,artifact,bundle=[json.loads(line) for line in joined]
        # Trusted custody independently supplies current status and exact association.
        if status!=expected_status:raise ValueError('Current custody missing, ambiguous, stale, revoked or target/digest mismatch')
        if artifact!=expected_approval:raise ValueError('External approval artifact differs')
        if bundle!=expected_bundle:raise ValueError('Original signed bundle differs from custody commitment')
        material=ex('sh','-c','openssl pkey -pubin -in /run/flooow-external/public.pem -outform DER | base64 -w 0; echo; base64 -w 0 /run/flooow-external/preimage.bin; echo; base64 -w 0 /run/flooow-external/signature.bin; echo',user='0').stdout.splitlines()
        actual_spki,actual_preimage,actual_signature=[base64.b64decode(value,validate=True) for value in material]
        original_manifest=bytes.fromhex(bundle['manifest_hex'])
        if actual_spki.hex()!=bundle['spki_hex'] or codec.sha(actual_spki)!=bundle['key_fingerprint'] or codec.sha(original_manifest)!=bundle['manifest_digest']:raise ValueError('Actual signer/manifest differs from independently committed original')
        if actual_preimage!=codec.signature_preimage(bundle['key_id'],actual_spki,original_manifest) or actual_signature.hex()!=bundle['signature_hex']:raise ValueError('Actual verification bytes differ from independently committed original')
        wall=datetime.datetime.now(datetime.timezone.utc)
        if not datetime.datetime.fromisoformat(bundle['window_start'].replace('Z','+00:00'))<=wall<datetime.datetime.fromisoformat(bundle['window_end'].replace('Z','+00:00')):raise ValueError('Signed window expired')
        # Actual cryptographic verification; no backend/receiver-authored trust flag.
        verify=ex('openssl','pkeyutl','-verify','-pubin','-inkey','/run/flooow-external/public.pem','-rawin','-in','/run/flooow-external/preimage.bin','-sigfile','/run/flooow-external/signature.bin',user='0',ok=False)
        if verify.returncode:raise ValueError('Ed25519 verification denied')
        fetched=json.loads(sql("SELECT json_build_object('row',to_jsonb(h)::text,'active',(SELECT count(*) FROM offline_binding_lifecycle WHERE state='ACTIVE')) FROM offline_binding_header h;").stdout)
        serialized=fetched['row'];fresh=json.loads(serialized)
        if fresh!=expected_header or codec.fingerprint(fresh)!=fingerprint:raise ValueError('Full header mismatch')
        if fetched['active']!=1:raise ValueError('Lifecycle ineligible')
        headerhash=bytes.fromhex(codec.sha(serialized.encode()));eligible=True;reason='CURRENT_EXACT_EXTERNAL_CUSTODY'
    except Exception as e:reason=str(e)
    # Only root writes; atomic rename prevents torn records. Monotonic lease is experimental.
    now=int(ex('/usr/local/bin/boottime',user='0').stdout)
    gate=struct.pack('<IIQ32s32s',0x00900002,int(eligible),now+5000000,bytes.fromhex(codec.sha(context)),headerhash)
    rootfile('/run/flooow-external/gate.bin',gate)
    record['observations'].append({'start_ns':started,'end_ns':time.monotonic_ns(),'eligible':eligible,'reason':reason,'gate_written_boottime_us':now})
    return eligible
def observer():
    while not stop.is_set():
        if not paused.is_set():
            with health_lock:observer_once()
        stop.wait(.1)
def mutate_external(path,object_,name,group='custody'):
    paused.set()
    with health_lock:
        original=ex('cat',path,user='0').stdout;rootfile(path,json.dumps(object_));observer_once();denial(group,name);rootfile(path,original);assert observer_once()
    paused.clear()
def main():
    global context,expected_status,expected_approval,expected_bundle,expected_header,fingerprint,observer_thread
    if OUT.exists():raise RuntimeError('Refuse existing evidence directory')
    OUT.mkdir(parents=True)
    try:
        info=json.loads(cmd(['docker','inspect',NAME]).stdout)[0]
        assert info['Image']==IMAGE and info['Config']['Labels'].get('flooow.scope')==SCOPE and info['HostConfig']['NetworkMode']=='none' and not info['Mounts']
        record['isolation']={'id':info['Id'],'image':info['Image'],'network':'none','mounts':[],'tmpfs':info['HostConfig']['Tmpfs'],'nano_cpus':info['HostConfig']['NanoCpus'],'memory':info['HostConfig']['Memory']}
        ex('mkdir','-p','/tmp/pgsock');ex('mkdir','-p','/run/flooow-watchdog',user='0');ex('chown','999:999','/run/flooow-watchdog',user='0');ex('chmod','0700','/run/flooow-watchdog')
        ex('mkdir','-p','/run/flooow-external','/run/test-only-private',user='0');ex('chmod','0755','/run/flooow-external',user='0');ex('chmod','0700','/run/test-only-private',user='0')
        ex('initdb','-D','/tmp/pgdata','--auth=trust','--no-locale','--encoding=UTF8')
        ex('pg_ctl','-D','/tmp/pgdata','-l','/tmp/setup.log','-o',"-k /tmp/pgsock -c listen_addresses=''",'-w','start');ex('createdb','-h','/tmp/pgsock','native_fixture')
        names=['test_verifier','test_issuer','test_executor','test_auditor'];roles=[]
        for name in names:
            sql('CREATE ROLE '+name+' LOGIN NOINHERIT NOSUPERUSER NOCREATEROLE NOCREATEDB NOREPLICATION NOBYPASSRLS;');roles.append((int(sql("SELECT oid FROM pg_roles WHERE rolname='"+name+"';").stdout),name))
        sql('CREATE ROLE test_unmanaged LOGIN; CREATE ROLE test_membership; REVOKE CONNECT ON DATABASE postgres,template1 FROM PUBLIC;')
        # Exact header/lifecycle/attempt-pointer DDL from source; no migration execution.
        source=V043.read_text(encoding='utf-8-sig');tables=['offline_binding_header','offline_binding_lifecycle','offline_attempt_pointer']
        for table in tables:
            ddl=source.split('CREATE TABLE public.'+table+' (',1)[1].split('\n);',1)[0]
            sql('CREATE TABLE public.'+table+' ('+ddl+'\n); REVOKE ALL ON public.'+table+' FROM PUBLIC;')
        sql('CREATE TABLE flooow_test_binding(slot int,role_oid oid,role_name text); REVOKE ALL ON flooow_test_binding FROM PUBLIC;')
        for i,(oid,name) in enumerate(roles,1):sql(f"INSERT INTO flooow_test_binding VALUES({i},{oid},'{name}');")
        ids={name:str(uuid.uuid4()) for name in codec.FIELDS if name.endswith('_id')}
        now=datetime.datetime.now(datetime.timezone.utc);fmt=lambda t:t.isoformat(timespec='microseconds').replace('+00:00','Z')
        start=fmt(now-datetime.timedelta(minutes=2));end=fmt(now+datetime.timedelta(minutes=30))
        # All labels/windows here are synthetic experiment inputs, never numeric policy.
        manifest=codec.frozen_frames(['FLOOOW:S2A:APPROVAL-MANIFEST:1',1,ids['manifest_id'],ids['organization_id'],ids['mercado_livre_connection_id'],ids['omie_connection_id'],'synthetic-order','synthetic-integration',ids['marketplace_order_id'],'TRANSACTION_IDENTITY_DECISION_WRITE',str(uuid.uuid4()),str(uuid.uuid4()),start,end,str(uuid.uuid4()),str(uuid.uuid4()),'PROTECTED_TTY_ONE_TIME',str(uuid.uuid4()),'SEPARATE_APPROVAL_REQUIRED','synthetic qualification','TEST_ONLY_NONCANONICAL',ids['correlation_id'],'a'*64])
        keyid=str(uuid.uuid4());ex('openssl','genpkey','-algorithm','ED25519','-out','/run/test-only-private/TEST_ONLY_NONCANONICAL.pem',user='0');ex('chmod','0600','/run/test-only-private/TEST_ONLY_NONCANONICAL.pem',user='0')
        ex('openssl','pkey','-in','/run/test-only-private/TEST_ONLY_NONCANONICAL.pem','-pubout','-out','/run/flooow-external/public.pem',user='0')
        ex('openssl','pkey','-pubin','-in','/run/flooow-external/public.pem','-outform','DER','-out','/run/flooow-external/public.der',user='0')
        spki=base64.b64decode(ex('base64','-w','0','/run/flooow-external/public.der',user='0').stdout)
        preimage=codec.signature_preimage(keyid,spki,manifest);rootfile('/run/flooow-external/preimage.bin',preimage)
        ex('openssl','pkeyutl','-sign','-inkey','/run/test-only-private/TEST_ONLY_NONCANONICAL.pem','-rawin','-in','/run/flooow-external/preimage.bin','-out','/run/flooow-external/signature.bin',user='0')
        sighex=base64.b64decode(ex('base64','-w','0','/run/flooow-external/signature.bin',user='0').stdout).hex()
        expected_bundle={'scope':'TEST_ONLY_NONCANONICAL','manifest_hex':manifest.hex(),'manifest_digest':codec.sha(manifest),'signature_domain':'FLOOOW:S2A:APPROVAL-SIGNATURE:1','algorithm':'Ed25519','key_id':keyid,'spki_hex':spki.hex(),'key_fingerprint':codec.sha(spki),'signature_hex':sighex,'authority':{'id':str(uuid.uuid4()),'state':'ENABLED','permission':'TRANSACTION_IDENTITY_DECISION_WRITE','organization_id':ids['organization_id'],'revision':1,'window_start':start,'window_end':end},'key_state':'ACTIVE','window_start':start,'window_end':end}
        rootfile('/run/flooow-external/attestation.json',json.dumps(expected_bundle))
        h=dict(ids)
        h.update(binding_schema_version=1,execution_plan_version=1,canonical_manifest_encoding_version=1,manifest_digest='\\x'+codec.sha(manifest),canonical_manifest_hash='\\x'+codec.sha(manifest),source_order_reference='synthetic-order',integration_reference='synthetic-integration',permission='TRANSACTION_IDENTITY_DECISION_WRITE',reason='synthetic qualification',provenance='TEST_ONLY_NONCANONICAL',issued_at=fmt(now),valid_from=start,expires_at=end,identity_slots='\\x'+codec.slots(roles).hex(),offline_surface_version='0090-v1',deadline_policy_version='TEST_ONLY_STRUCTURE_NO_NUMERIC_POLICY',deadline_policy_digest='\\x'+codec.sha(b'TEST_ONLY_NONCANONICAL_POLICY_STRUCTURE_NO_NUMERIC_AUTHORITY'),admission_contract_version='1',delivery_contract_version='1',reconciliation_contract_version='1')
        fingerprint=codec.fingerprint(h);h['plan_fingerprint']='\\x'+fingerprint;h['canonical_manifest_bytes']='\\x'+manifest.hex()
        quote=lambda v:str(v) if isinstance(v,int) else "'"+str(v).replace("'","''")+"'"
        sql('INSERT INTO offline_binding_header('+','.join(h)+') VALUES('+','.join(quote(v) for v in h.values())+');')
        sql(f"INSERT INTO offline_binding_lifecycle VALUES('{ids['binding_id']}','ACTIVE',0); INSERT INTO offline_attempt_pointer VALUES('{ids['binding_id']}',NULL,1,false,0);")
        expected_header=getheader();dboid=int(sql("SELECT oid FROM pg_database WHERE datname='native_fixture';").stdout)
        context=struct.pack('<6I64s64s64s64s64s16s16s16s32s32s32sQ',0x00900001,dboid,*[oid for oid,_ in roles],b'native_fixture',*[n.encode() for n in names],uuid.UUID(ids['binding_id']).bytes,uuid.UUID(ids['deployment_id']).bytes,uuid.UUID(ids['deployment_incarnation_id']).bytes,b'\0'*32,bytes.fromhex(fingerprint),codec.unhex(h['deadline_policy_digest']),5000000)
        rootfile('/usr/local/fixture-context.bin',context)
        expected_approval={'scope':'TEST_ONLY_NONCANONICAL','deployment_id':ids['deployment_id'],'incarnation_id':ids['deployment_incarnation_id'],'binding_id':ids['binding_id'],'database_oid':dboid,'roles':roles,'fingerprint':fingerprint,'policy_digest':h['deadline_policy_digest'],'attestation_sha256':codec.sha(json.dumps(expected_bundle,sort_keys=True).encode()),'custody_reference':'TEST_ONLY_EXTERNAL_ROOT_CUSTODY','revision':1}
        # JSON round-trip tuple/list representation is part of exact comparison.
        expected_approval=json.loads(json.dumps(expected_approval))
        expected_status={'state':'CURRENT','artifact_digest':codec.sha(json.dumps(expected_approval,sort_keys=True).encode()),'deployment_id':ids['deployment_id'],'incarnation_id':ids['deployment_incarnation_id'],'binding_id':ids['binding_id'],'revision':1,'custody_reference':'TEST_ONLY_EXTERNAL_ROOT_CUSTODY'}
        rootfile('/run/flooow-external/approval.json',json.dumps(expected_approval));rootfile('/run/flooow-external/status.json',json.dumps(expected_status))
        save('SYNTHETIC-PUBLIC-CONTEXT.json',{'scope':'TEST_ONLY_NONCANONICAL','header':expected_header,'approval':expected_approval,'status':expected_status,'original_attestation':expected_bundle,'preimage_hex':preimage.hex(),'context_hex':context.hex()})
        save('FULL-SYNTHETIC-BINDING-MATRIX.json',{'source':str(V043.relative_to(ROOT)),'fields':[{'field':k,'classification':'NORMATIVE','tag':codec.FIELDS.index(k)+1 if k in codec.FIELDS else None,'value':v} for k,v in h.items()],'derived':[{'field':'database_oid','classification':'DERIVED','value':dboid},{'field':'role_attributes_and_memberships','classification':'NORMATIVE','source':'live pg_roles/pg_auth_members'},{'field':'health_gate_lease','classification':'SYNTHETIC_TEST_ONLY','numeric_authority':'NONE'}],'full_policy_semantics':'NOT_REQUIRED_FOR_THIS_STRUCTURE_ONLY_EXPERIMENT; numeric qualification remains HOLD','fingerprint':fingerprint})
        assert observer_once();sql('CHECKPOINT;');ex('pg_ctl','-D','/tmp/pgdata','-m','fast','-w','stop')
        boot();assert observer_once();observer_thread=threading.Thread(target=observer,daemon=True);observer_thread.start()
        sql("CREATE FUNCTION flooow_test_login() RETURNS event_trigger AS '/usr/local/lib/flooow_test_login','flooow_test_login' LANGUAGE C SECURITY DEFINER SET search_path=pg_catalog; REVOKE ALL ON FUNCTION flooow_test_login() FROM PUBLIC; CREATE EVENT TRIGGER flooow_test_login_event ON login EXECUTE FUNCTION flooow_test_login(); ALTER EVENT TRIGGER flooow_test_login_event ENABLE ALWAYS;")
        for role in names:case('admission',role,sql('SELECT current_user;',role,ok=False).returncode==0,'native login with full protected header + external current custody')
        case('admission','unmanaged_no_governed_authority',sql('SELECT current_user;','test_unmanaged',ok=False).returncode==0 and sql('SELECT * FROM offline_binding_header;','test_unmanaged',ok=False).returncode!=0,'unmanaged login allowed; binding raw access denied')
        tests()
    except Exception:
        record['errors'].append(traceback.format_exc());print(record['errors'][-1],flush=True)
    finally:
        stop.set()
        if observer_thread:observer_thread.join(timeout=30)
        for path,filename in [('/tmp/full.log','NATIVE-RUNTIME.log'),('/tmp/setup.log','SETUP.log')]:
            r=ex('cat',path,user='0',ok=False);(OUT/filename).write_bytes((r.stdout+r.stderr).encode())
        record['private_key_erasure']=ex('rm','-f','/run/test-only-private/TEST_ONLY_NONCANONICAL.pem','/run/test-only-private/TEST_ONLY_NONCANONICAL-other.pem',user='0',ok=False).returncode==0
        record['private_key_absent']=ex('test','!','-e','/run/test-only-private/TEST_ONLY_NONCANONICAL.pem',user='0',ok=False).returncode==0
        record['binary_hashes']=ex('sha256sum','/usr/local/lib/flooow_test_login.so','/usr/local/bin/flooow-test-receiver','/usr/local/bin/flooow-test-supervisor',ok=False).stdout
        record['source_hashes']={p.name:codec.sha(p.read_bytes()) for p in HERE.iterdir() if p.is_file()}
        save('SOURCE.json',{p.name:p.read_text() for p in HERE.iterdir() if p.is_file()})
        inspected=json.loads(cmd(['docker','inspect',NAME]).stdout)[0];assert inspected['Image']==IMAGE and inspected['Config']['Labels'].get('flooow.scope')==SCOPE
        cmd(['docker','rm','-f',inspected['Id']]);record['owned_container_removed']=True
        save('RAW-QUALIFICATION.json',record)
    return 1 if record['errors'] or any(c['result']=='FAIL' for c in record['cases']) else 0
def tests():
    # Added in successor test module to keep authority/setup and assertions reviewable.
    import importlib
    module=sys.argv[sys.argv.index('--scenario-module')+1] if '--scenario-module' in sys.argv else 'scenarios'
    importlib.import_module(module).run(sys.modules[__name__])
if __name__=='__main__':raise SystemExit(main())
