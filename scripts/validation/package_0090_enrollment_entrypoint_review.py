"""Read-only authority/configuration evidence for the enrollment-entrypoint gate.

No native prototype: its complete design/canonical-binding prerequisite is open.
No SQL function, role/grant, policy/fixture or application mutation.
"""
import hashlib
import json
import secrets
import subprocess
import time
import package_0090_timing_qualification2 as env
import package_0090_timing_forensics as forensic

BASELINE = '401a5e313efbec9a4100af8b6b6e237fffb4ca38'
WORK_NAME = 'governed-enrollment-entrypoint-review'
SCOPE_SQL = """SELECT json_build_object(
 'bindings',(SELECT json_agg(json_build_object('binding_id',binding_id,'deployment_id',deployment_id,'incarnation_id',deployment_incarnation_id,'identity_slots_hex',encode(identity_slots,'hex'),'fingerprint_hex',encode(plan_fingerprint,'hex')) ORDER BY binding_id) FROM public.offline_binding_header),
 'binding_header_count',(SELECT count(*) FROM public.offline_binding_header),
 'readiness',(SELECT json_agg(row_to_json(r) ORDER BY incarnation_id) FROM (SELECT deployment_id,incarnation_id,state,policy_version,encode(policy_digest,'hex') policy_digest,watchdog_checked_at,watchdog_healthy FROM public.offline_readiness) r),
 'preload_configuration',(SELECT json_agg(json_build_object('name',name,'setting',setting,'context',context,'source',source) ORDER BY name) FROM pg_settings WHERE name IN ('shared_preload_libraries','session_preload_libraries','local_preload_libraries')),
 'parameter_acl',(SELECT json_agg(json_build_object('name',parname,'acl',paracl) ORDER BY parname) FROM pg_parameter_acl),
 'control_system',(SELECT json_build_object('system_identifier',system_identifier,'pg_control_version',pg_control_version,'catalog_version_no',catalog_version_no) FROM pg_control_system())
);"""

def run(args, timeout=30):
    result = subprocess.run(args, capture_output=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError('Evidence tool failed: ' + args[0])
    return result.stdout

def main():
    for revision in ['HEAD', 'origin/checkpoint/package-0090-cloud-handoff']:
        if run(['git', 'rev-parse', revision]).decode().strip() != BASELINE:
            raise RuntimeError('Baseline mismatch')
    container, private, _ = env.identity()
    work = private / WORK_NAME
    inventory = json.loads((work / 'prior-inventory.json').read_text(encoding='utf-8'))
    if container['State']['Running'] or (work / 'record.json').exists():
        raise RuntimeError('Refuse running container or overwritten review')
    allowed = {item['path'] for item in inventory} | {'scripts/validation/package_0090_enrollment_entrypoint_review.py'}
    if len(inventory) != 14 or any(line[3:] not in allowed or not line.startswith('?? ') for line in run(['git', 'status', '--porcelain']).decode().splitlines()):
        raise RuntimeError('Unexpected worktree')
    if any(hashlib.sha256((env.ROOT/item['path']).read_bytes()).hexdigest() != item['sha256'] for item in inventory):
        raise RuntimeError('Prior artifact changed')
    tracked = run(['git', 'ls-files', '-z']).decode().split('\0')
    hashes = {name:hashlib.sha256((env.ROOT/name).read_bytes()).hexdigest() for name in tracked if name and (env.ROOT/name).is_file()}
    record = {'baseline':BASELINE,'scope':'READ_ONLY_REVIEW_NO_PROTOTYPE','prior_inventory':inventory,'unrelated_file_count':0,'tracked_hashes_before':hashes,'destructive_signal_count':0,'native_prototype_installed':False,'new_service_EXECUTE':False}
    def save():
        (work/'record.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n')
    def sql(statement):
        env.identity()
        result = subprocess.run(['docker','exec','-i',env.CONTAINER,'psql','-X','-U','postgres','-d','g3f4','-At','-v','ON_ERROR_STOP=1'],input=statement,text=True,capture_output=True,timeout=20)
        if result.returncode:
            raise RuntimeError('Read-only ADMIN SQL failed')
        return result.stdout.strip()
    roles = ['postgres']+['g3f4_'+name+'_cc2941797db3' for name in ['auditor','verifier','issuer','executor']]
    authority = forensic.authority_snapshot_sql(roles)
    password = private/'postgres-password'
    if password.exists():
        raise RuntimeError('Unexpected startup file')
    password.write_text(secrets.token_hex(32),encoding='ascii')
    started = False
    try:
        run(['docker','start',env.CONTAINER]); started = True
        deadline = time.monotonic()+40
        while time.monotonic()<deadline:
            if subprocess.run(['docker','exec',env.CONTAINER,'pg_isready','-U','postgres','-d','g3f4'],capture_output=True).returncode==0:
                break
            time.sleep(.1)
        else:
            raise RuntimeError('Startup timeout')
        record['server'] = json.loads(sql("SELECT json_build_object('version',version(),'version_num',current_setting('server_version_num'),'database',current_database(),'postmaster_start',pg_postmaster_start_time(),'clock',clock_timestamp());"))
        if record['server']['version_num']!='180004':
            raise RuntimeError('Expected PG18.4')
        record['authority_pre'] = json.loads(sql(authority)); record['fingerprint_pre'] = forensic.fingerprint(record['authority_pre'])
        record['scope_pre'] = json.loads(sql(SCOPE_SQL))
        record['scope_post'] = json.loads(sql(SCOPE_SQL))
        record['authority_post'] = json.loads(sql(authority)); record['fingerprint_post'] = forensic.fingerprint(record['authority_post'])
        record['authority_equal'] = record['authority_pre']==record['authority_post']
        record['scope_equal'] = record['scope_pre']==record['scope_post']
    finally:
        try:
            if started:
                run(['docker','stop',env.CONTAINER],40)
        finally:
            password.unlink(missing_ok=True)
            record['container_stopped'] = not env.identity()[0]['State']['Running']
            record['plaintext_credential_files_erased'] = not password.exists()
            record['prior_files_unchanged'] = all(hashlib.sha256((env.ROOT/item['path']).read_bytes()).hexdigest()==item['sha256'] for item in inventory)
            record['tracked_unchanged'] = all(hashlib.sha256((env.ROOT/name).read_bytes()).hexdigest()==value for name,value in hashes.items())
            save()
    if not all(record.get(key) for key in ['authority_equal','scope_equal','container_stopped','plaintext_credential_files_erased','prior_files_unchanged','tracked_unchanged']):
        raise RuntimeError('Integrity incomplete')
    print(json.dumps({'scope':record['scope_post'],'fingerprint_pre':record['fingerprint_pre'],'fingerprint_post':record['fingerprint_post'],'container_stopped':True},indent=2))

if __name__=='__main__':
    main()
