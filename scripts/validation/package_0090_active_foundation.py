"""Fresh TEST_ONLY foundation: exact baseline/body, approved retained rows and ACLs.

Never submits canonical V043. Never writes fabricated READY/ACTIVE binding,
watchdog flags, attestation, downstream effects or receipts to obtain a positive.
"""
import argparse
import json
import os
from pathlib import Path
import secrets
import shutil
import sys
import tempfile
import time
import uuid
import package_0090_source_closure as q


def quote(value):
    if value is None:
        return 'NULL'
    if isinstance(value, bool):
        return 'TRUE' if value else 'FALSE'
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, (list, dict)):
        value = json.dumps(value, ensure_ascii=False, separators=(',', ':'))
    return "'" + str(value).replace("'", "''") + "'"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--parser-path', required=True); ap.add_argument('--directory', required=True)
    ap.add_argument('--first-positive-preparation', action='store_true')
    ap.add_argument('--authorized-s04', action='store_true')
    ap.add_argument('--native-100us', action='store_true')
    ap.add_argument('--concurrent-currentness', action='store_true')
    ap.add_argument('--complete-currentness', action='store_true')
    ap.add_argument('--t10-expectations', action='store_true')
    ap.add_argument('--t10-audit-expectations', action='store_true')
    ap.add_argument('--reachable-expectations', action='store_true')
    ap.add_argument('--full-reachable', action='store_true')
    ap.add_argument('--s04-candidate', action='store_true')
    args = ap.parse_args(); sys.path.insert(0, args.parser_path)
    from pglast.parser import parse_sql_json
    folder = Path(args.directory).resolve()
    output = folder / 'foundation-runtime.json'
    q.require(not output.exists(), 'Refuse existing runtime evidence')
    source = q.git('show', 'HEAD:' + q.V043.relative_to(q.ROOT).as_posix())
    body, _, proof = q.derive(source, parse_sql_json)
    fixture = json.loads((folder / 'active-fixture-manifest.json').read_text())
    acl = json.loads((folder / 'expected-acl-manifest.json').read_text())
    context = json.loads((folder / 'source-function-contexts.json').read_text())
    for name, digest in fixture['input_hashes'].items():
        q.require(q.sha((q.ROOT / 'docs/evidence' / name).read_bytes()) == digest, 'Approved fixture input drift')
    work = Path(tempfile.mkdtemp(prefix='flooow-0090-ledger-foundation-'))
    project = 'flooow-0090-g3f4-' + uuid.uuid4().hex[:12]
    volume, container = project + '-data', project + '-postgres'
    resources = []
    record = {'scope': 'TEST_ONLY_FOUNDATION_NOT_ACTIVE', 'source_hash': q.SOURCE_HASH,
              'canonical_v043_submitted': False, 'canonical_v043_executed': False,
              'transformation': proof, 'cases': [], 'errors': [], 'active_fixture_ready': False,
              'input_hashes': {name: q.sha((folder / name).read_bytes()) for name in ['active-fixture-manifest.json', 'expected-acl-manifest.json', 'source-function-contexts.json']},
              'recipe_hashes': {p.name: q.sha(p.read_bytes()) for p in [Path(__file__), q.ROOT / 'scripts/validation/Package0090SourceClosureFlyway.java', q.ROOT / 'scripts/validation/package_0090_source_closure.py']}}
    def run(a, **kw):
        return q.command(a, **kw).stdout
    def sql(s, role='postgres', check=True):
        return q.command(['docker', 'exec', '-i', container, 'psql', '-X', '-w', '-U', role, '-d', 'g3f4', '-At', '-v', 'ON_ERROR_STOP=1', '-v', 'VERBOSITY=verbose'], s.encode(), check=check)
    def case(name, passed, details, group):
        record['cases'].append({'name': name, 'passed': passed, 'details': details, 'group': group})
        q.require(passed, 'Foundation assertion failed: ' + name)
    try:
        frozen = work / 'migrations'; frozen.mkdir()
        record['frozen_inputs'] = {}
        for p in sorted(q.MIGRATIONS.glob('V*.sql')):
            if int(p.name.split('__')[0][1:]) > 42:
                continue
            rel = p.relative_to(q.ROOT).as_posix(); b = q.git('show', 'HEAD:' + rel)
            q.require(b == q.git('show', q.FROZEN + ':' + rel), 'Frozen baseline drift')
            (frozen / p.name).write_bytes(b); record['frozen_inputs'][p.name] = q.sha(b)
        q.require(len(record['frozen_inputs']) == 42, 'Exact baseline required')
        native = q.ROOT / 'applications/marketplace-operations-persistence-postgres/native/flooow_offline_mac32'
        shutil.copytree(native, work / 'native')
        build = run(['docker', 'run', '--rm', '--network', 'none', '--mount', f'type=bind,source={work},target=/review', '--entrypoint', 'sh', q.IMAGE, '-c', 'set -eu; cd /review/native; make with_llvm=no >/review/build.log 2>&1; pg_config --version; openssl version'])
        record['build_versions'] = build.decode(); record['binary_sha256'] = q.sha((work / 'native/flooow_offline_mac32.so').read_bytes())
        q.require(record['binary_sha256'] == '5aeedcdb693442b7738b6f33604e059094f584af29d1879bf35482ca06ef63b5', 'Pinned binary differs')
        password = secrets.token_hex(32); (work / 'postgres-password').write_text(password)
        for kind, name in [('volume', volume), ('network', project)]:
            run(['docker', kind, 'create', '--label', 'com.docker.compose.project=' + project, name]); resources.append((kind, name))
        run(['docker', 'run', '-d', '--name', container, '--label', 'com.docker.compose.project=' + project, '--network', project,
             '-p', '127.0.0.1::5432', '--mount', f'type=volume,source={volume},target=/var/lib/postgresql', '--mount', f'type=bind,source={work},target=/review,readonly',
             '-e', 'POSTGRES_PASSWORD_FILE=/review/postgres-password', '-e', 'POSTGRES_DB=g3f4', '-e', 'POSTGRES_INITDB_ARGS=--encoding=UTF8 --locale=en_US.utf8',
             '--entrypoint', '/usr/local/bin/docker-entrypoint.sh', q.IMAGE, 'postgres']); resources.append(('container', container))
        details = json.loads(run(['docker', 'inspect', container]))[0]
        binding = details['NetworkSettings']['Ports']['5432/tcp']
        q.require(len(binding) == 1 and binding[0]['HostIp'] == '127.0.0.1' and details['Image'] == q.IMAGE, 'Unapproved target binding/image')
        record['isolation'] = {'container': container, 'id': details['Id'], 'bindings': binding, 'project': project, 'volume': volume}
        for _ in range(60):
            if q.command(['docker', 'exec', container, 'pg_isready', '-U', 'postgres'], check=False).returncode == 0:
                break
            time.sleep(.5)
        else:
            raise RuntimeError('New disposable database unavailable')
        cache = Path.home() / '.gradle/caches/modules-2/files-2.1'; jars = sorted(cache.rglob('*.jar'))
        cp = os.pathsep.join(map(str, jars)); record['jvm_input_hashes'] = {p.relative_to(cache).as_posix(): q.sha(p.read_bytes()) for p in jars}
        helper = q.ROOT / 'scripts/validation/Package0090SourceClosureFlyway.java'
        (work / 'compile.args').write_text('-cp\n"' + cp.replace('\\', '/') + '"\n-d\n"' + work.as_posix() + '"\n"' + helper.as_posix() + '"\n')
        run(['javac', '@' + str(work / 'compile.args')])
        (work / 'flyway.properties').write_text(f'url=jdbc:postgresql://127.0.0.1:{binding[0]["HostPort"]}/g3f4\npassword={password}\nmigrations={frozen.as_posix()}\ntarget=042\nproject={project}\nvolume={volume}\ncontainer={container}\n')
        (work / 'java.args').write_text('-cp\n"' + (str(work) + os.pathsep + cp).replace('\\', '/') + '"\nPackage0090SourceClosureFlyway\n"' + (work / 'flyway.properties').as_posix() + '"\n')
        result = q.command(['java', '@' + str(work / 'java.args')], check=False)
        (folder / 'foundation-flyway-042.txt').write_bytes((result.stdout + result.stderr).replace(password.encode(), b'[REDACTED]'))
        q.require(result.returncode == 0, 'Baseline migration failed; no repair')
        owners = ['control', 'verification', 'issuance', 'execution', 'audit', 'readiness', 'principal_lock', 'intent_audit']
        setup = [f'CREATE ROLE flooow_offline_{o}_owner NOLOGIN ' + ('INHERIT' if o == 'control' else 'NOINHERIT') + ' NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;' for o in owners]
        for role in ['postgres'] + ['flooow_offline_' + o + '_owner' for o in owners]:
            setup.extend(f'ALTER DEFAULT PRIVILEGES FOR ROLE {role} REVOKE ALL ON {kind} FROM PUBLIC;' for kind in ['TABLES', 'SEQUENCES', 'FUNCTIONS', 'TYPES', 'SCHEMAS', 'LARGE OBJECTS'])
        sql('\n'.join(setup) + '\nGRANT USAGE ON SCHEMA public TO flooow_offline_control_owner;')
        run(['docker', 'exec', container, 'sh', '-c', 'set -eu; cp /review/native/flooow_offline_mac32.so "$(pg_config --pkglibdir)/"; cp /review/native/flooow_offline_mac32.control /review/native/flooow_offline_mac32--1.0.sql "$(pg_config --sharedir)/extension/"'])
        sql("BEGIN; CREATE SCHEMA offline_crypto AUTHORIZATION postgres; CREATE EXTENSION pgcrypto VERSION '1.4' SCHEMA offline_crypto; CREATE EXTENSION flooow_offline_mac32 VERSION '1.0'; REVOKE ALL ON SCHEMA offline_crypto FROM PUBLIC; REVOKE ALL ON ALL FUNCTIONS IN SCHEMA offline_crypto FROM PUBLIC; GRANT USAGE ON SCHEMA offline_crypto TO flooow_offline_readiness_owner; GRANT EXECUTE ON FUNCTION offline_crypto.hmac(bytea,bytea,text),offline_crypto.timing_safe_equal32(bytea,bytea) TO flooow_offline_readiness_owner; COMMIT;")
        sql('BEGIN;\n' + body.decode() + '\nCOMMIT;')
        record['postgres_version'] = sql('SELECT version();').stdout.decode().strip()
        actual = json.loads(sql("SELECT coalesce(json_agg(json_build_object('role',pg_get_userbyid(x.grantee),'relation',n.nspname||'.'||c.relname,'column',a.attname,'privilege',lower(x.privilege_type))), '[]') FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid JOIN pg_namespace n ON n.oid=c.relnamespace CROSS JOIN LATERAL aclexplode(a.attacl) x WHERE pg_get_userbyid(x.grantee) IN ('flooow_offline_verification_owner','flooow_offline_issuance_owner','flooow_offline_execution_owner','flooow_offline_audit_owner','flooow_offline_principal_lock_owner','flooow_offline_readiness_owner','flooow_offline_intent_audit_owner');").stdout)
        keys = lambda rows: {tuple(x[k] for k in ['role', 'relation', 'column', 'privilege']) for x in rows}
        case('source_SPEC_column_ACL_exact', keys(actual) == keys(acl['column_grants']), {'expected': len(acl['column_grants']), 'actual': len(actual)}, 'ACL')
        record['actual_column_acl'] = actual
        signature_aliases = {'int4': 'integer', 'int8': 'bigint', 'bool': 'boolean', 'timestamptz': 'timestamp with time zone', 'bpchar': 'character'}
        actual_contexts = []
        for expected in context:
            sig = expected['signature'].replace("'", "''")
            row = json.loads(sql("SELECT json_build_object('signature',p.oid::regprocedure::text,'oid',p.oid,'owner',pg_get_userbyid(p.proowner),'definer',p.prosecdef,'strict',p.proisstrict,'volatile',p.provolatile,'config',p.proconfig,'acl',p.proacl::text) FROM pg_proc p WHERE p.oid=to_regprocedure('" + sig + "');").stdout)
            actual_contexts.append(row)
            v = {'volatile': 'v', 'stable': 's', 'immutable': 'i'}[expected['volatility']]
            path = ['search_path=' + ', '.join(expected['search_path'])] if expected['search_path'] else None
            passed = row['owner'] == expected['owner'] and row['definer'] == (expected['security_mode'] == 'DEFINER') and row['strict'] == expected['strict'] and row['volatile'] == v and row['config'] == path
            case('function_context_' + expected['signature'], passed, row, 'SECURITY_CONTEXT')
        record['actual_function_contexts'] = actual_contexts
        record['service_identities'] = []
        for family in ['verification', 'issuance', 'execution', 'audit']:
            role = 'test_0090_' + family
            sql(f'CREATE ROLE {role} LOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS; GRANT USAGE ON SCHEMA public TO {role};')
            for c in context:
                name = c['signature'].split('(')[0].split('.')[-1]
                if name.startswith('offline_') and not name.startswith('offline_internal_') and name != 'offline_lock_bound_principal' and c['owner'] == 'flooow_offline_' + family + '_owner':
                    sql('GRANT EXECUTE ON FUNCTION ' + c['signature'] + ' TO ' + role + ';')
            row = json.loads(sql("SELECT json_build_object('session_user',SESSION_USER,'current_user',CURRENT_USER,'role',row_to_json(r),'membership_count',(SELECT count(*) FROM pg_auth_members WHERE member=r.oid OR roleid=r.oid)) FROM (SELECT oid,rolname,rolcanlogin,rolinherit,rolsuper,rolcreatedb,rolcreaterole,rolreplication,rolbypassrls FROM pg_roles WHERE rolname=SESSION_USER) r;", role=role).stdout)
            attrs = row['role']
            passed = row['session_user'] == role and row['current_user'] == role and row['membership_count'] == 0 and attrs['rolcanlogin'] and not any(attrs[k] for k in ['rolinherit', 'rolsuper', 'rolcreatedb', 'rolcreaterole', 'rolreplication', 'rolbypassrls'])
            case('independent_LOGIN_' + role, passed, row, 'CALLER_IDENTITY')
            record['service_identities'].append(row)
            denied = sql('SET ROLE flooow_offline_control_owner;', role=role, check=False)
            case('owner_impersonation_denied_' + role, denied.returncode != 0 and '42501' in denied.stderr.decode(), denied.stderr.decode(), 'ACL')
            denied = sql('SELECT * FROM public.offline_binding_header;', role=role, check=False)
            case('raw_binding_read_denied_' + role, denied.returncode != 0 and '42501' in denied.stderr.decode(), denied.stderr.decode(), 'ACL')
        # Independently encode/load retained approved source rows as one transaction.
        retained = json.loads((q.ROOT / 'docs/evidence/PACKAGE-0090-G3F-3B-EVIDENCE-FIXTURE-001.json').read_text())
        statements = []
        for table, rows in retained['tables'].items():
            for row in rows:
                values = []
                for column, value in row.items():
                    if table == 'integration_connector_page_commit' and column == 'page_commit_key':
                        q.require(isinstance(value, str) and len(value) == 64 and all(c in '0123456789abcdef' for c in value), 'Approved hash32 hex required')
                        values.append('decode(' + quote(value) + ",'hex')")
                    else:
                        values.append(quote(value))
                statements.append('INSERT INTO public.' + table + '(' + ','.join(row) + ') VALUES(' + ','.join(values) + ');')
        record['retained_loader_sql_sha256'] = q.sha('\n'.join(statements).encode())
        result = sql('BEGIN;\n' + '\n'.join(statements) + '\nCOMMIT;', check=False)
        record['retained_loader'] = {'exit': result.returncode, 'stderr': result.stderr.decode()}
        if result.returncode:
            record['fixture_load_blocked'] = True
        else:
            for table, rows in retained['tables'].items():
                count = int(sql('SELECT count(*) FROM public.' + table + ';').stdout)
                case('retained_rows_' + table, count == len(rows), {'expected': len(rows), 'actual': count}, 'FIXTURE')
        # No policy ACTIVE row is silently provisioned without explicit activation instant/audit.
        case('no_fabricated_READY', sql('SELECT count(*) FROM public.offline_readiness;').stdout.strip() == b'0', 'No health/READY state fabricated', 'FIXTURE')
        record['positive_wrapper_results'] = {'expected': 18, 'proven': 0, 'blocked': 18, 'reason': 'Live ACTIVE binding/readiness/native health/original attestation manifest not proven'}
        q.require(sum([args.first_positive_preparation, args.authorized_s04, args.native_100us, args.concurrent_currentness, args.complete_currentness, args.t10_expectations, args.t10_audit_expectations, args.reachable_expectations, args.full_reachable, args.s04_candidate]) <= 1, 'One qualification recipe per owned runtime')
        if args.s04_candidate:
            import package_0090_s04_candidate as candidate
            record['recipe_hashes'][Path(candidate.__file__).name] = q.sha(Path(candidate.__file__).read_bytes())
            candidate.qualify(sql, run, container, folder, record, fixture, runtime_work=work)
        if args.full_reachable:
            import package_0090_full_reachable as full
            record['recipe_hashes'][Path(full.__file__).name] = q.sha(Path(full.__file__).read_bytes())
            full.qualify(sql, run, container, folder, record, fixture, runtime_work=work)
        if args.reachable_expectations:
            import package_0090_reachable_expectations as reachable
            record['recipe_hashes'][Path(reachable.__file__).name] = q.sha(Path(reachable.__file__).read_bytes())
            reachable.qualify(sql, run, container, folder, record, fixture, runtime_work=work)
        if args.t10_audit_expectations:
            import package_0090_t10_audit_expectations as audit_expectations
            record['recipe_hashes'][Path(audit_expectations.__file__).name] = q.sha(Path(audit_expectations.__file__).read_bytes())
            audit_expectations.qualify(sql, run, container, folder, record, fixture, runtime_work=work)
        if args.t10_expectations:
            import package_0090_t10_expectations as t10
            record['recipe_hashes'][Path(t10.__file__).name] = q.sha(Path(t10.__file__).read_bytes())
            t10.qualify(sql, run, container, folder, record, fixture, runtime_work=work)
        if args.complete_currentness:
            import package_0090_complete_currentness as complete
            record['recipe_hashes'][Path(complete.__file__).name] = q.sha(Path(complete.__file__).read_bytes())
            complete.qualify(sql, run, container, folder, record, fixture, runtime_work=work)
        if args.concurrent_currentness:
            import package_0090_concurrent_currentness as currentness
            record['recipe_hashes'][Path(currentness.__file__).name] = q.sha(Path(currentness.__file__).read_bytes())
            currentness.qualify(sql, run, container, folder, record, fixture, runtime_work=work)
        if args.first_positive_preparation:
            import package_0090_first_positive as extension
            record['recipe_hashes'][Path(extension.__file__).name] = q.sha(Path(extension.__file__).read_bytes())
            extension.prepare(sql, run, container, folder, record, fixture)
        if args.authorized_s04:
            q.require(not args.first_positive_preparation, 'Do not mix historical preparation with authorized campaign')
            import package_0090_authorized_s04 as authorized
            record['recipe_hashes'][Path(authorized.__file__).name] = q.sha(Path(authorized.__file__).read_bytes())
            authorized.qualify(sql, run, container, folder, record, fixture, runtime_work=work)
        if args.native_100us:
            q.require(not args.authorized_s04 and not args.first_positive_preparation, 'Separate qualification recipes')
            import package_0090_native_100us as measured
            record['recipe_hashes'][Path(measured.__file__).name] = q.sha(Path(measured.__file__).read_bytes())
            measured.qualify(sql, run, container, folder, record, fixture, runtime_work=work)
    except Exception as e:
        record['errors'].append(type(e).__name__ + ': ' + str(e))
    finally:
        cleanup = []
        for kind, name in reversed(resources):
            d = json.loads(run(['docker', 'inspect', name] if kind == 'container' else ['docker', kind, 'inspect', name]))[0]
            labels = d['Config']['Labels'] if kind == 'container' else d['Labels']
            q.require(labels.get('com.docker.compose.project') == project, 'Refuse unrelated cleanup')
            a = ['docker', 'rm', '-f', d['Id']] if kind == 'container' else ['docker', kind, 'rm', name]
            cleanup.append({'kind': kind, 'name': name, 'removed': q.command(a, check=False).returncode == 0})
        (work / 'postgres-password').unlink(missing_ok=True); (work / 'flyway.properties').unlink(missing_ok=True)
        record['cleanup'] = cleanup; record['owned_runtime_destroyed'] = bool(resources) and all(x['removed'] for x in cleanup)
        output.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'cases': len(record['cases']), 'errors': record['errors'], 'active_fixture_ready': False, 'cleanup': record.get('owned_runtime_destroyed')}))
    return int(bool(record['errors']))


if __name__ == '__main__':
    raise SystemExit(main())
