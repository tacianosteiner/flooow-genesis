"""Phase-A standalone kernel/socket proof in exact stopped disposable PG image.

No PostgreSQL extension installation, grants, role changes or destructive signals.
Capture non-secret authority before/after; preserve all nine prior artifacts.
"""
import hashlib
import json
import secrets
import subprocess
import time
from pathlib import Path
import package_0090_timing_qualification2 as env
import package_0090_timing_forensics as forensic

BASELINE = '401a5e313efbec9a4100af8b6b6e237fffb4ca38'

def run(args, timeout=30):
    result = subprocess.run(args, capture_output=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError('Read-only proof tool failed: ' + args[0] + ': ' + result.stderr.decode(errors='replace'))
    return result.stdout

def main():
    for revision in ['HEAD', 'origin/checkpoint/package-0090-cloud-handoff']:
        if run(['git', 'rev-parse', revision]).decode().strip() != BASELINE:
            raise RuntimeError('Baseline mismatch')
    container, private, old = env.identity()
    work = private / 'self-enrolled-anchor-proof'
    inventory = json.loads((work / 'prior-inventory.json').read_text(encoding='utf-8'))
    if container['State']['Running'] or (work / 'record.json').exists():
        raise RuntimeError('Refuse running container/overwriting proof')
    if any(hashlib.sha256((env.ROOT / item['path']).read_bytes()).hexdigest() != item['sha256'] for item in inventory):
        raise RuntimeError('Prior evidence changed')
    allowed = {item['path'] for item in inventory} | {'scripts/validation/package_0090_self_enrolled_pidfd_probe.c', 'scripts/validation/package_0090_self_enrolled_pidfd_proof.py'}
    if any(line[3:] not in allowed or not line.startswith('?? ') for line in run(['git', 'status', '--porcelain']).decode().splitlines()):
        raise RuntimeError('Unrelated file detected')
    tracked = run(['git', 'ls-files', '-z']).decode().split('\0')
    hashes = {name: hashlib.sha256((env.ROOT / name).read_bytes()).hexdigest() for name in tracked if name and (env.ROOT / name).is_file()}
    record = {'baseline': BASELINE, 'prior_inventory': inventory, 'unrelated_count': 0,
        'destructive_signal_count': 0, 'signal_numbers_used': [0],
        'tracked_hashes_before': hashes, 'postgres_prototype_installed': False,
        'phase': 'STANDALONE_KERNEL_SOCKET_PROOF_ONLY'}
    def save():
        (work / 'record.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')
    def sql(statement):
        env.identity()
        result = subprocess.run(['docker', 'exec', '-i', env.CONTAINER, 'psql', '-X', '-U', 'postgres', '-d', 'g3f4', '-At', '-v', 'ON_ERROR_STOP=1'], input=statement, text=True, capture_output=True, timeout=20)
        if result.returncode:
            raise RuntimeError('Read-only SQL failed')
        return result.stdout.strip()
    roles = ['postgres'] + ['g3f4_' + name + '_cc2941797db3' for name in ['auditor', 'verifier', 'issuer', 'executor']]
    authority = forensic.authority_snapshot_sql(roles)
    state_sql = "SELECT json_build_object('binding_header_count',(SELECT count(*) FROM public.offline_binding_header),'readiness',(SELECT json_agg(row_to_json(r) ORDER BY incarnation_id) FROM (SELECT deployment_id,incarnation_id,state,policy_version,encode(policy_digest,'hex') policy_digest,watchdog_checked_at,watchdog_healthy FROM public.offline_readiness) r));"
    password = private / 'postgres-password'
    if password.exists():
        raise RuntimeError('Unexpected startup secret file')
    password.write_text(secrets.token_hex(32), encoding='ascii')
    started = False
    try:
        run(['docker', 'start', env.CONTAINER]); started = True
        deadline = time.monotonic() + 40
        while time.monotonic() < deadline:
            if subprocess.run(['docker', 'exec', env.CONTAINER, 'pg_isready', '-U', 'postgres', '-d', 'g3f4'], capture_output=True).returncode == 0:
                break
            time.sleep(.1)
        else:
            raise RuntimeError('Startup timeout')
        record['server'] = json.loads(sql("SELECT json_build_object('version',version(),'version_num',current_setting('server_version_num'),'postmaster_start',pg_postmaster_start_time(),'database',current_database(),'clock',clock_timestamp());"))
        if record['server']['version_num'] != '180004':
            raise RuntimeError('PG18.4 required')
        record['authority_pre'] = json.loads(sql(authority)); record['fingerprint_pre'] = forensic.fingerprint(record['authority_pre'])
        record['scope_pre'] = json.loads(sql(state_sql))
        source = env.ROOT / 'scripts/validation/package_0090_self_enrolled_pidfd_probe.c'
        (work / 'probe.c').write_bytes(source.read_bytes())
        record['source_sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
        record['compiler'] = run(['docker', 'exec', env.CONTAINER, 'gcc', '--version']).decode().splitlines()[0]
        run(['docker', 'exec', env.CONTAINER, 'gcc', '-std=c11', '-Wall', '-Wextra', '-Werror', '-O2', '-o', '/tmp/0090-self-enrolled-probe', '/review/self-enrolled-anchor-proof/probe.c'])
        record['binary_sha256'] = run(['docker', 'exec', env.CONTAINER, 'sha256sum', '/tmp/0090-self-enrolled-probe']).decode().split()[0]
        output = run(['docker', 'exec', '--user', 'postgres', env.CONTAINER, '/tmp/0090-self-enrolled-probe'], 45)
        (work / 'probe-output.jsonl').write_bytes(output)
        record['probe'] = [json.loads(line) for line in output.decode().splitlines()]
        record['process_security'] = run(['docker', 'exec', '--user', 'postgres', env.CONTAINER, 'sh', '-c', 'cat /proc/self/status']).decode()
        record['container_security'] = {key: container['HostConfig'][key] for key in ['Privileged', 'CapAdd', 'CapDrop', 'SecurityOpt', 'PidMode']}
        record['authority_post'] = json.loads(sql(authority)); record['fingerprint_post'] = forensic.fingerprint(record['authority_post'])
        record['scope_post'] = json.loads(sql(state_sql))
        record['authority_equal'] = record['authority_pre'] == record['authority_post']
        record['scope_equal'] = record['scope_pre'] == record['scope_post']
        run(['docker', 'cp', env.CONTAINER + ':/tmp/0090-self-enrolled-probe', str(work / 'probe.bin')])
        run(['docker', 'exec', env.CONTAINER, 'objdump', '-d', '/tmp/0090-self-enrolled-probe'])
        (work / 'probe-disassembly.txt').write_bytes(run(['docker', 'exec', env.CONTAINER, 'objdump', '-d', '/tmp/0090-self-enrolled-probe']))
    finally:
        try:
            if started:
                run(['docker', 'stop', env.CONTAINER], 40)
        finally:
            password.unlink(missing_ok=True)
            record['container_stopped'] = not env.identity()[0]['State']['Running']
            record['plaintext_credential_files_erased'] = not password.exists()
            record['prior_files_unchanged'] = all(hashlib.sha256((env.ROOT / item['path']).read_bytes()).hexdigest() == item['sha256'] for item in inventory)
            record['tracked_unchanged'] = all(hashlib.sha256((env.ROOT / name).read_bytes()).hexdigest() == value for name,value in hashes.items())
            save()
    if not all(record.get(key) for key in ['authority_equal', 'scope_equal', 'container_stopped', 'plaintext_credential_files_erased', 'prior_files_unchanged', 'tracked_unchanged']):
        raise RuntimeError('Integrity incomplete')
    print(json.dumps({'probe': record['probe'], 'fingerprint_pre': record['fingerprint_pre'], 'fingerprint_post': record['fingerprint_post'], 'scope': record['scope_post'], 'container_stopped': True}, indent=2))

if __name__ == '__main__':
    main()
