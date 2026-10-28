"""Owned disposable sealed-capability experiment; historical recipes stay frozen."""
import argparse
import inspect
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import time
import types
import urllib.error
import urllib.request
import uuid
import package_0090_source_closure as q

OUT = q.ROOT / 'docs/evidence/package-0090-sealed-capability-mediation-boundary'
BASELINE = '08998f48fa56bdf89d0838ea0807699bf721c68d'
UTILITY = 'sha256:09814deedf2c61aa24b5f523e815c367311b75ba33377aef45c8c5ec3458039c'
SERVICE = Path(__file__).with_name('package_0090_sealed_service.py')
ROLES = ['test_0090_' + x for x in ['verification', 'issuance', 'execution', 'audit']]
OWNERS = ['flooow_offline_' + x + '_owner' for x in ['control', 'verification', 'issuance', 'execution', 'audit', 'readiness', 'principal_lock', 'intent_audit']]


def save(folder, name, data):
    (folder / name).write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')


def load(folder, name): return json.loads((folder / name).read_text())


def call(url, request, check=True):
    r = urllib.request.Request(url, data=json.dumps(request).encode(), headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(r, timeout=60) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        result = json.load(exc)
        if check: raise RuntimeError(str(result))
        return result


def prepare(sql, run, container, folder, record, fixture, runtime_work):
    """Runs ONLY in the separate bootstrap process, which exits before seal."""
    work = runtime_work
    details = json.loads(run(['docker', 'inspect', container]))[0]
    project = details['Config']['Labels']['com.docker.compose.project']
    volume = record['isolation']['volume']
    receipt = dict(project=project, container=container, volume=volume, bootstrap_pid=os.getpid(), epoch=str(uuid.uuid4()),
                   utility_image=UTILITY, source_image=q.IMAGE, prepared=False, work=str(work))
    save(folder, 'handoff.json', receipt)
    code = work / 'sealed-code'; code.mkdir(); shutil.copy2(SERVICE, code / SERVICE.name)
    native_token = secrets.token_hex(32); credential = secrets.token_hex(32)
    setup = ["CREATE ROLE test_0090_broker LOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS PASSWORD '" + credential + "';"]
    setup += ['GRANT flooow_offline_control_owner TO test_0090_broker WITH INHERIT FALSE, SET TRUE, ADMIN FALSE;']
    setup += ['GRANT pg_read_all_stats TO test_0090_broker WITH INHERIT TRUE, SET FALSE, ADMIN FALSE;']
    # Campaign roles get no runtime mutation wrappers in this capability-only test.
    for role in ROLES:
        setup.append('REVOKE ALL ON ALL FUNCTIONS IN SCHEMA public FROM ' + role + ';')
    sql('\n'.join(setup))
    pgdata = run(['docker', 'exec', container, 'sh', '-c', 'printf %s "$PGDATA"']).decode()
    receipt['pgdata'] = pgdata
    # A final privileged transaction disables all bootstrap logins and destroys
    # the reusable cluster credential. Its psql process then exits.
    seal_sql = "ALTER ROLE postgres NOLOGIN PASSWORD NULL; SELECT json_build_object('postgres_login',(SELECT rolcanlogin FROM pg_roles WHERE rolname='postgres'),'postgres_password_null',(SELECT rolpassword IS NULL FROM pg_authid WHERE rolname='postgres'),'superuser_sessions_other_than_last_bootstrap',(SELECT count(*) FROM pg_stat_activity a JOIN pg_roles r ON r.oid=a.usesysid WHERE r.rolsuper AND a.backend_type='client backend' AND a.pid<>pg_backend_pid()),'owner_logins',(SELECT count(*) FROM pg_roles WHERE rolname LIKE 'flooow_offline_%_owner' AND rolcanlogin));"
    receipt['last_privileged_receipt'] = json.loads(sql(seal_sql).stdout.decode().splitlines()[-1])
    # No original /review mount, password-file environment, root entrypoint,
    # host DB port, trusted local socket or writable module survives replacement.
    run(['docker', 'stop', '-t', '20', container]); run(['docker', 'rm', container])
    hba = work / 'sealed-pg_hba.conf'
    hba.write_text('local all all reject\n' + ''.join('host g3f4 ' + r + ' 0.0.0.0/0 trust\n' for r in ROLES) + 'host g3f4 test_0090_broker 0.0.0.0/0 scram-sha-256\nhost all all 0.0.0.0/0 reject\n', encoding='utf-8')
    module = work / 'native/flooow_offline_mac32.so'
    common = ['--label', 'com.docker.compose.project=' + project, '--network', project, '--read-only', '--cap-drop=ALL', '--security-opt=no-new-privileges:true']
    mount_module = ['--mount', f'type=bind,source={module},target=/usr/lib/postgresql/18/lib/flooow_offline_mac32.so,readonly']
    run(['docker', 'run', '-d', '--name', container, *common, '--user', '999:999',
         '--tmpfs', '/tmp:rw,nosuid,nodev,noexec,mode=1777', '--mount', f'type=volume,source={volume},target=/var/lib/postgresql',
         *mount_module, '--mount', f'type=bind,source={hba},target=/etc/sealed-pg_hba.conf,readonly', '--entrypoint', '/usr/lib/postgresql/18/bin/postgres', q.IMAGE,
         '-D', pgdata, '-c', 'hba_file=/etc/sealed-pg_hba.conf', '-c', 'unix_socket_directories=/tmp', '-c', 'listen_addresses=*'])
    for _ in range(60):
        if q.command(['docker', 'exec', '--user', '999:999', container, 'pg_isready', '-h', '127.0.0.1'], check=False).returncode == 0: break
        time.sleep(.25)
    else: raise RuntimeError('Sealed DB did not start')
    state_volume = project + '-broker-state'
    run(['docker', 'volume', 'create', '--label', 'com.docker.compose.project=' + project, state_volume])
    # Disposable init process exits before the sealed epoch.
    run(['docker', 'run', '--rm', '--network', 'none', '--mount', f'type=volume,source={state_volume},target=/state', '--entrypoint', 'sh', UTILITY, '-c', 'chown 10001:10001 /state; chmod 700 /state'])
    endpoints = {}
    for kind, uid in [('native', '10002:10002'), ('broker', '10001:10001'), ('campaign', '10004:10004')]:
        name = project + '-' + kind
        args = ['docker', 'run', '-d', '--name', name, *common, '--user', uid,
                '--tmpfs', '/tmp:rw,nosuid,nodev,noexec,mode=1777', '--tmpfs', '/private:rw,nosuid,nodev,noexec,mode=700,uid=' + uid.split(':')[0],
                '--tmpfs', '/var/lib/postgresql:ro,nosuid,nodev,noexec,mode=000',
                '--mount', f'type=bind,source={code},target=/opt/sealed,readonly', *mount_module]
        if kind == 'broker': args += ['--mount', f'type=volume,source={state_volume},target=/state']
        if kind != 'campaign': args += ['-p', '127.0.0.1::8080']
        args += ['--entrypoint', '/usr/bin/python3', UTILITY, '-I', '-B', '/opt/sealed/' + SERVICE.name, kind] if kind != 'campaign' else ['--entrypoint', 'sleep', UTILITY, 'infinity']
        run(args)
        if kind == 'campaign': continue
        config = dict(epoch=receipt['epoch'], native_token=native_token)
        if kind == 'broker': config.update(credential=credential, host=container, native_url='http://' + project + '-native:8080/')
        run(['docker', 'exec', '-i', '--user', uid, name, 'sh', '-c', 'while [ ! -p /private/inbox ]; do sleep 0.1; done; cat > /private/inbox'], data=json.dumps(config).encode())
        d = json.loads(run(['docker', 'inspect', name]))[0]
        endpoints[kind] = 'http://127.0.0.1:' + d['NetworkSettings']['Ports']['8080/tcp'][0]['HostPort'] + '/'
        for _ in range(60):
            try: call(endpoints[kind], dict(op='status')); break
            except Exception: time.sleep(.1)
        else: raise RuntimeError(kind + ' did not accept private provisioning')
    receipt.update(prepared=True, endpoints=endpoints, state_volume=state_volume, immutable_code_sha256=q.sha(SERVICE.read_bytes()),
                   bootstrap_secret_files_unlinked=True)
    (work / 'postgres-password').unlink(missing_ok=True); (work / 'flyway.properties').unlink(missing_ok=True)
    save(folder, 'handoff.json', receipt)
    record['prepared_transfer'] = True


def bootstrap(folder):
    import package_0090_active_foundation as foundation
    sys.modules['package_0090_reachable_v2_runtime'] = types.SimpleNamespace(complete_qualification=prepare)
    # The historical function is unchanged on disk. This exact, recorded adapter
    # skips destruction ONLY on successful transfer. Failure keeps old cleanup.
    source = inspect.getsource(foundation.main)
    start = source.index('        cleanup = []\n', source.index('    finally:'))
    end = source.index('        output.write_text', start)
    block = source[start:end]
    replacement = "        if record.get('prepared_transfer'):\n            record['cleanup'] = []\n            record['owned_runtime_destroyed'] = False\n            record['transferred_resources'] = resources\n        else:\n" + ''.join('    ' + line + '\n' for line in block.splitlines())
    adapted = source[:start] + replacement + source[end:]
    save(folder, 'bootstrap-adapter.json', dict(historical_file_sha256=q.sha(Path(foundation.__file__).read_bytes()),
         original_function_sha256=q.sha(source.encode()), adapted_function_sha256=q.sha(adapted.encode()),
         exact_replacement_original=block, exact_replacement_new=replacement, historical_file_mutated=False))
    exec(compile(adapted, '<recorded-test-only-bootstrap-lifecycle-adapter>', 'exec'), foundation.__dict__)
    sys.argv = [__file__, '--parser-path', 'C:/Users/xmz_r/.codex/tmp/package0090-pglast-8.5', '--directory', str(folder), '--reachable-v2']
    return foundation.main()


def cleanup(project):
    rows = []
    for kind in ['container', 'network', 'volume']:
        listing = ['docker', 'ps', '-aq', '--filter', 'label=com.docker.compose.project=' + project] if kind == 'container' else ['docker', kind, 'ls', '-q', '--filter', 'label=com.docker.compose.project=' + project]
        for name in q.command(listing).stdout.decode().splitlines():
            d = json.loads(q.command(['docker', 'inspect', name] if kind == 'container' else ['docker', kind, 'inspect', name]).stdout)[0]
            labels = d['Config']['Labels'] if kind == 'container' else d['Labels']
            q.require(labels.get('com.docker.compose.project') == project, 'Refuse foreign resource cleanup')
            result = q.command(['docker', 'rm', '-f', '-v', name] if kind == 'container' else ['docker', kind, 'rm', name], check=False)
            rows.append(dict(kind=kind, name=name, removed=result.returncode == 0))
    return rows


def campaign(folder, final_fault):
    cases = []
    save(folder, 'attempt-source.json', dict(driver_sha256=q.sha(Path(__file__).read_bytes()), service_sha256=q.sha(SERVICE.read_bytes()), final_fault=final_fault, utility=UTILITY))
    def case(name, passed, group, details):
        row = dict(name=name, passed=bool(passed), group=group, details=details)
        cases.append(row); save(folder, 'tests.json', cases)
        return bool(passed)
    inputs = q.ROOT / 'docs/evidence/package-0090-semantic-ledger-active-fixture-final'
    for name in ['active-fixture-manifest.json', 'expected-acl-manifest.json', 'source-function-contexts.json']:
        shutil.copy2(inputs / name, folder / name)
    p = subprocess.Popen([sys.executable, str(Path(__file__)), 'bootstrap', '--directory', str(folder)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate(timeout=600)
    save(folder, 'bootstrap-process.json', dict(pid=p.pid, exit=p.returncode, exited_before_seal=True, stdout=stdout.decode(errors='replace'), stderr=stderr.decode(errors='replace')))
    q.require(p.returncode == 0, 'Bootstrap failed; see retained process evidence')
    receipt = load(folder, 'handoff.json'); project = receipt['project']; broker = receipt['endpoints']['broker']; native = receipt['endpoints']['native']
    try:
        case('bootstrap_process_exited_before_seal', p.poll() == 0 and receipt['bootstrap_pid'] == p.pid, 'ROLE_ISOLATION', dict(pid=p.pid, receipt=receipt['last_privileged_receipt']))
        sealed = call(broker, dict(op='seal')); save(folder, 'initial-seal.json', sealed)
        case('fresh_epoch_sealed_only_after_bootstrap_exit', sealed['eligible'], 'MEDIATION_CLOSURE', sealed)
        census = call(broker, dict(op='census')); save(folder, 'database-census.json', census)
        for row in census['ordinary_effective_paths']:
            case('effective_privilege_closure_' + row['role'], not row['owner_set_paths'] and not row['protected_dml'] and not row['source_execute'], 'ROLE_ISOLATION', row)
        roles = {r['rolname']: r for r in census['roles']}
        case('all_eight_owners_nologin', all(not roles[r]['rolcanlogin'] for r in OWNERS), 'ROLE_ISOLATION', [roles[r] for r in OWNERS])
        case('no_active_superuser_sessions', census['superuser_sessions'] == 0, 'ROLE_ISOLATION', census['superuser_sessions'])
        case('postgres_nologin_and_credential_destroyed', not roles['postgres']['rolcanlogin'] and receipt['last_privileged_receipt']['postgres_password_null'], 'ROLE_ISOLATION', receipt['last_privileged_receipt'])
        forbidden = [m for m in census['memberships'] or [] if m['owner'] in OWNERS and m['member'] not in ['test_0090_broker'] + OWNERS]
        case('no_ordinary_owner_membership', not forbidden, 'ROLE_ISOLATION', forbidden)
        case('broker_not_superuser_or_role_admin', not any(roles['test_0090_broker'][k] for k in ['rolsuper', 'rolcreaterole', 'rolcreatedb', 'rolreplication', 'rolbypassrls']), 'ROLE_ISOLATION', roles['test_0090_broker'])
        inspections = {}
        for suffix in ['postgres', 'broker', 'native', 'campaign']:
            name = receipt['container'] if suffix == 'postgres' else project + '-' + suffix
            d = json.loads(q.command(['docker', 'inspect', name]).stdout)[0]
            inspections[suffix] = dict(id=d['Id'], image=d['Image'], user=d['Config']['User'], readonly=d['HostConfig']['ReadonlyRootfs'], cap_drop=d['HostConfig']['CapDrop'], security=d['HostConfig']['SecurityOpt'], mounts=[dict(destination=m['Destination'], type=m['Type'], rw=m['RW']) for m in d['Mounts']], env=d['Config']['Env'], ports=d['NetworkSettings']['Ports'])
            case('sealed_container_' + suffix, d['HostConfig']['ReadonlyRootfs'] and d['HostConfig']['CapDrop'] == ['ALL'] and d['Config']['User'] != '0' and not any('PASSWORD' in x for x in d['Config']['Env']), 'ROLE_ISOLATION', inspections[suffix])
        save(folder, 'container-census.json', inspections)
        case('bootstrap_secret_files_absent', not (Path(receipt['work']) / 'postgres-password').exists() and not (Path(receipt['work']) / 'flyway.properties').exists(), 'ROLE_ISOLATION', dict(files_unlinked=True, bootstrap_process_exited=True, no_original_review_mount=True))
        from package_0090_t10_46_campaign import sql_cases
        reps = sql_cases(); db_rows = []
        campaign_name = project + '-campaign'
        def sql_probe(statement, role):
            return q.command(['docker', 'exec', '-i', '--user', '10004:10004', campaign_name, 'psql', '-X', '-w', '-h', receipt['container'], '-U', role, '-d', 'g3f4', '-At', '-v', 'ON_ERROR_STOP=1', '-v', 'VERBOSITY=verbose'], data=statement.encode(), check=False)
        for role in ROLES:
            identity = sql_probe('SELECT current_user;', role)
            q.require(case('direct_probe_transport_' + role, identity.returncode == 0 and identity.stdout.strip() == role.encode(), 'ROLE_ISOLATION', dict(stdout=identity.stdout.decode(), exit=identity.returncode)), 'SQL probe transport/identity failed')
            for owner in OWNERS:
                r = sql_probe('SET ROLE ' + owner + ';', role)
                case('owner_set_denied_' + role + '_' + owner, r.returncode != 0 and b'42501' in r.stderr, 'ROLE_ISOLATION', dict(exit=r.returncode, stderr=r.stderr.decode()))
            for key, (owner, mutate, restore, observe) in reps.items():
                # The exact historical protected operation, without granting its
                # former owner identity to this ordinary active role.
                statement = mutate.replace('ALTER DEFAULT PRIVILEGES ', 'ALTER DEFAULT PRIVILEGES FOR ROLE postgres ') if key == 'future_default_acl' else mutate
                r = sql_probe(statement + ';', role)
                row = dict(representative=key, role=role, historical_statement=mutate, statement=statement,
                           target_preservation='Historical postgres CURRENT_USER is explicit FOR ROLE postgres for default privileges; object/operation unchanged',
                           exit=r.returncode, stderr=r.stderr.decode(), denied=r.returncode != 0)
                db_rows.append(row)
                case('direct_db_' + role + '_' + key, row['denied'] and (b'42501' in r.stderr or b'0LP01' in r.stderr), 'DIRECT_DB_BYPASS', row)
        for role in ['postgres'] + OWNERS + ['test_0090_broker']:
            r = sql_probe('SELECT current_user;', role)
            case('private_or_disabled_login_' + role, r.returncode != 0, 'ROLE_ISOLATION', dict(exit=r.returncode, stderr=r.stderr.decode()))
        save(folder, 'direct-db-bypass-tests.json', dict(cases=db_rows, succeeded=sum(not r['denied'] for r in db_rows)))
        native_rows = call(native, dict(op='probes'))
        for actor, values in native_rows.items():
            for row in values['cases']:
                case('native_' + actor + '_' + row['operation'], row['denied'] and values['before'] == values['after'], 'NATIVE_BYPASS', row)
        # Campaign identity and original container-root representative, both in
        # the sealed readonly/capability-free mount namespace.
        for actor, name, uid in [('campaign', campaign_name, '10004:10004'), ('broker', project + '-broker', '10001:10001'), ('old_root_representative', project + '-native', '0:0')]:
            r = q.command(['docker', 'exec', '--user', uid, name, '/usr/bin/python3', '-I', '-B', '/opt/sealed/' + SERVICE.name, 'probe'])
            values = json.loads(r.stdout); native_rows[actor] = values
            for row in values['cases']:
                case('native_' + actor + '_' + row['operation'], row['denied'] and values['before'] == values['after'], 'NATIVE_BYPASS', row)
        save(folder, 'native-bypass-tests.json', native_rows)
        for actor, name, uid in [('native', project + '-native', '10002:10002'), ('campaign', campaign_name, '10004:10004'), ('postgres', receipt['container'], '999:999')]:
            for operation in ['decrement', 'reuse', 'overwrite', 'truncate', 'replace']:
                # No state volume is mounted in any of these namespaces.
                python_ops = dict(decrement="p.write_text(str(int(p.read_text())-1))", reuse="p.write_text('1')", overwrite="p.write_text('9999')", truncate="p.open('wb').close()", replace="Path('/tmp/generation').write_text('0'); Path('/tmp/generation').replace(p)")
                code = "from pathlib import Path; p=Path('/state/generation'); " + python_ops[operation]
                if actor == 'postgres':
                    shell_ops = dict(decrement='v=$(cat /state/generation) && printf %s "$((v-1))" > /state/generation', reuse='printf 1 > /state/generation', overwrite='printf 9999 > /state/generation', truncate=': > /state/generation', replace='printf 0 > /tmp/generation && mv /tmp/generation /state/generation')
                    r = q.command(['docker', 'exec', '--user', uid, name, 'sh', '-c', shell_ops[operation]], check=False)
                else:
                    r = q.command(['docker', 'exec', '--user', uid, name, '/usr/bin/python3', '-I', '-B', '-c', code], check=False)
                case('generation_' + actor + '_' + operation, r.returncode != 0, 'GENERATION_TAMPER', dict(exit=r.returncode, stderr=r.stderr.decode()))
        for request in [dict(op='sql', sql='ALTER ROLE postgres LOGIN'), dict(op='db_enable', fault='none', target='other'), dict(op='replace', generation=999), dict(op='initialize')]:
            result = call(broker, request, check=False)
            case('closed_api_' + q.sha(json.dumps(request).encode())[:12], 'error' in result, 'MEDIATION_CLOSURE', result)
        for enable in [True, False]:
            result = call(broker, dict(op='db_enable' if enable else 'db_disable', fault='none'))
            save(folder, 'broker-db-' + str(enable).lower() + '.json', result)
            case('broker_db_' + str(enable), result['snapshot']['eligible'] and result['snapshot']['generation'] > result['before']['generation'] and not result['old_generation_eligible'], 'BROKER_POSITIVE', result)
        previous_native = call(native, dict(op='status'))
        old_tuple = call(broker, dict(op='status'))['qualification_tuple']
        case('current_test_boundary_tuple_matches', call(broker, dict(op='validate_tuple', tuple=old_tuple))['accepted'], 'BROKER_POSITIVE', dict(scope='TEST boundary only'))
        result = call(broker, dict(op='native_replace', fault='none')); save(folder, 'broker-native-positive.json', result)
        case('native_new_identity_and_guard_binding', result['outcome']['new']['pid'] != previous_native['identity']['pid'] and result['outcome']['new']['nonce'] != previous_native['identity']['nonce'] and result['outcome']['new']['generation'] > previous_native['generation'] and not result['old_generation_eligible'], 'BROKER_POSITIVE', result)
        case('old_boundary_tuple_cannot_accept_new_native_identity', not call(broker, dict(op='validate_tuple', tuple=old_tuple))['accepted'] and call(broker, dict(op='validate_tuple', tuple=result['snapshot']['qualification_tuple']))['accepted'], 'BROKER_POSITIVE', dict(old=old_tuple, new=result['snapshot']['qualification_tuple'], scope='Not full operational T10'))
        # A forged/replayed native request cannot trigger replacement directly.
        forged = call(native, dict(op='replace', generation=999), check=False)
        case('native_delegate_requires_private_broker_binding', 'error' in forged, 'MEDIATION_CLOSURE', forged)
        for fault in ['pre', 'post']:
            result = call(broker, dict(op='db_enable', fault=fault)); save(folder, fault + '-mutation-crash.json', result)
            case('actual_mutator_crash_' + fault, result['outcome']['exit'] == (77 if fault == 'pre' else 78) and not result['snapshot']['eligible'] and result['snapshot']['state'] == 'UNKNOWN', 'CRASH', result)
            denied = call(broker, dict(op='seal'), check=False)
            case('unknown_cannot_direct_seal_' + fault, 'error' in denied, 'CRASH', denied)
            reconciliation = call(broker, dict(op='reconcile')); save(folder, fault + '-crash-reconciliation.json', reconciliation)
            case('crash_requires_independent_reconciliation_' + fault, reconciliation['snapshot']['eligible'] and reconciliation['outcome'] == ('NO_MUTATOR_STARTED' if fault == 'pre' else 'committed'), 'CRASH', reconciliation)
        audit = call(broker, dict(op='audit')); save(folder, 'broker-audit-binding.json', audit)
        recensus = call(broker, dict(op='census')); save(folder, 'post-transition-census.json', recensus)
        case('post_transition_role_and_acl_closure', recensus['roles'] == census['roles'] and recensus['memberships'] == census['memberships'] and recensus['ordinary_effective_paths'] == census['ordinary_effective_paths'] and recensus['superuser_sessions'] == 0 and recensus['ready'] == 0, 'MEDIATION_CLOSURE', dict(no_role_or_acl_widening=True, no_ready=True, no_superuser_client_sessions=True))
        invalidations = [r for r in audit['records'] if r['event'] == 'INVALIDATED_BEFORE_MUTATOR']
        case('all_mutations_have_prior_durable_invalidation', len(invalidations) == 5 and all(r['state'] == 'TRANSITIONING' and r['binding']['generation_after'] > r['binding']['generation_before'] for r in invalidations), 'AUDIT_BINDING', invalidations)
        case('audit_writer_distinct_from_db_mutator', all(r['audit_writer_pid'] != r['outcome']['mutation_pid'] for r in audit['records'] if r['event'] == 'DB_OUTCOME'), 'AUDIT_BINDING', dict(writer_pid=audit['snapshot']['pid']))
        if final_fault == 'credential_loss':
            result = call(broker, dict(op='db_disable', fault='credential_loss')); save(folder, 'credential-loss.json', result)
            case('credential_loss_denies_without_rollback_assumption', not result['snapshot']['eligible'] and result['snapshot']['state'] == 'UNKNOWN' and result['outcome']['exit'] == 78, 'CRASH', result)
            denied = call(broker, dict(op='reconcile'), check=False)
            case('credential_loss_cannot_reconcile_without_outcome_evidence', 'error' in denied and not call(broker, dict(op='status'))['eligible'], 'CRASH', denied)
            save(folder, 'credential-loss-reconciliation-attempt.json', denied)
        elif final_fault == 'native_delegate_loss':
            q.command(['docker', 'stop', '-t', '5', project + '-native'])
            result = call(broker, dict(op='native_replace', fault='none'), check=False)
            snapshot = call(broker, dict(op='status'))
            case('unknown_native_request_never_means_not_started', 'error' in result and snapshot['state'] == 'UNKNOWN' and not snapshot['eligible'] and not snapshot['pending']['before_start'], 'CRASH', dict(result=result, snapshot=snapshot))
            denied = call(broker, dict(op='reconcile'), check=False)
            case('unknown_native_outcome_cannot_reseal_from_prestart_receipt', 'error' in denied and not call(broker, dict(op='status'))['eligible'], 'CRASH', denied)
            save(folder, 'native-unknown-outcome.json', dict(result=result, snapshot=snapshot, reconciliation=denied))
        else:
            result = call(broker, dict(op='metadata_fault', fault=final_fault)); save(folder, 'fence-loss.json', result)
            case('fence_' + final_fault + '_noneligible', not result['eligible'] and result['state'] == 'UNKNOWN', 'CRASH', result)
            denied = call(broker, dict(op='seal'), check=False)
            case('fence_' + final_fault + '_cannot_reinitialize', 'error' in denied and not call(broker, dict(op='status'))['eligible'], 'CRASH', denied)
            r = q.command(['docker', 'exec', '--user', '10001:10001', project + '-broker', '/usr/bin/python3', '-I', '-B', '-c', "import sys; sys.path.insert(0,'/opt/sealed'); from package_0090_sealed_service import Broker; Broker({'credential':'INVALID_TEST_VALUE','epoch':'not-a-new-target'})"], check=False)
            case('existing_epoch_' + final_fault + '_refuses_fresh_bootstrap', r.returncode != 0 and b'Existing epoch requires reconciliation' in r.stderr, 'CRASH', dict(exit=r.returncode, stderr=r.stderr.decode()))
        save(folder, 'final-broker-audit.json', call(broker, dict(op='audit')))
        save(folder, 'tests.json', cases)
    finally:
        save(folder, 'cleanup.json', cleanup(project))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('mode', choices=['bootstrap', 'campaign']); ap.add_argument('--directory', required=True)
    ap.add_argument('--final-fault', choices=['credential_loss', 'delete', 'corrupt', 'native_delegate_loss'], default='credential_loss')
    args = ap.parse_args(); folder = Path(args.directory).resolve()
    if args.mode == 'bootstrap': return bootstrap(folder)
    q.require(not (folder / 'bootstrap-process.json').exists(), 'Never overwrite an attempt')
    try:
        campaign(folder, args.final_fault)
    except Exception as exc:
        save(folder, 'campaign-error.json', dict(type=type(exc).__name__, error=str(exc)))
        if (folder / 'handoff.json').exists(): save(folder, 'cleanup-after-error.json', cleanup(load(folder, 'handoff.json')['project']))
        raise
    return 0


if __name__ == '__main__': raise SystemExit(main())
