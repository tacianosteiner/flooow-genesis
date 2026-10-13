"""Package-only, disposable source gate. Never executes canonical V043 as a migration.

The only permitted transformation deletes the exact first execution interlock.
Candidate bytes stay in private temporary scratch, outside migration resources.
Every failed prerequisite stops the campaign; no catalog/history repair occurs.
"""
import argparse
import collections
import hashlib
import hmac
import json
import os
import re
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
import zlib

ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS = ROOT / 'applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration'
V043 = next(MIGRATIONS.glob('V043__*.sql'))
SOURCE_HASH = 'b0ea86b6ba355fdf25fe09836bd4b75e4a4a2ad88ab7ef0e4724ca0d5a013e7d'
IMAGE = 'sha256:07fc165de5bb569d822460e2df645c5489f99220fc2cb16c86596d39db394561'
FROZEN = '19131bb9cd655312252c8c83f0f78e7c0742274f'
FENCE = b"DO $$\nBEGIN\n    RAISE EXCEPTION USING ERRCODE = '55000',\n        MESSAGE = 'Package 0090 V043 implementation closure is incomplete; execution denied';\nEND;\n$$;"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def command(args, data=None, check=True, timeout=120):
    r = subprocess.run(args, input=data, capture_output=True, timeout=timeout)
    if check and r.returncode:
        raise RuntimeError(f'{args[0]} failed: ' + r.stderr.decode(errors='replace')[-2400:])
    return r


def git(*args):
    return command(['git', '-C', str(ROOT), *args]).stdout


def derive(source, parser):
    if sha(source) != SOURCE_HASH:
        raise ValueError('Frozen canonical Git source hash mismatch')
    tree = json.loads(parser(source.decode()))['stmts']
    first = tree[0]
    start = first.get('stmt_location', 0)
    end = start + first['stmt_len']
    # Parser span includes leading comments, and excludes the terminator.
    fence_offset = source.index(FENCE)
    if source.count(FENCE) != 1 or source[end:end + 1] != b';':
        raise ValueError('Fence is not unique/terminated')
    if source[fence_offset:end + 1] != FENCE or list(first['stmt']) != ['DoStmt']:
        raise ValueError('Fence is not the exact first top-level statement')
    if source[start:fence_offset].strip() and any(
            not line.startswith(b'--') for line in source[start:fence_offset].splitlines() if line.strip()):
        raise ValueError('Unexpected source before first fence')
    candidate = source[:fence_offset] + source[fence_offset + len(FENCE):]
    if candidate[:fence_offset] + FENCE + candidate[fence_offset:] != source:
        raise ValueError('Transformation changed other bytes')
    after = json.loads(parser(candidate.decode()))['stmts']
    def without_locations(node):
        if isinstance(node, dict):
            return {k: without_locations(v) for k, v in node.items() if k not in
                    ('location', 'arg_location', 'rexpr_list_start', 'rexpr_list_end')}
        if isinstance(node, list):
            return [without_locations(v) for v in node]
        return node
    if without_locations([x['stmt'] for x in after]) != without_locations([x['stmt'] for x in tree[1:]]):
        raise ValueError('Remaining SQL AST differs')
    return candidate, tree, {'offset': fence_offset, 'length': len(FENCE),
                            'candidate_sha256': sha(candidate), 'ast_equivalence': True}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--parser-path', required=True)
    ap.add_argument('--output', required=True)
    ap.add_argument('--execute-disposable', action='store_true')
    args = ap.parse_args()
    sys.path.insert(0, args.parser_path)
    from pglast.parser import parse_sql_json
    out = Path(args.output).resolve()
    out.mkdir(parents=True, exist_ok=False)
    record = {'scope': 'TEST_ONLY_NONCANONICAL', 'baseline': git('rev-parse', 'HEAD').decode().strip(),
              'cases': [], 'canonical_executed': False, 'canonical_mutated': False,
              'shared_database_contacted': False, 'production_contacted': False}
    original = V043.read_bytes()
    source = git('show', 'HEAD:' + V043.relative_to(ROOT).as_posix())
    if original.replace(b'\r\n', b'\n') != source:
        raise RuntimeError('Working canonical source differs from Git')
    candidate, tree, transformation = derive(source, parse_sql_json)
    counts = collections.Counter(next(iter(s['stmt'])) for s in tree)
    record['source'] = {'path': V043.relative_to(ROOT).as_posix(), 'git_blob': git('rev-parse', 'HEAD:' + V043.relative_to(ROOT).as_posix()).decode().strip(),
                        'sha256_git_lf': sha(source), 'sha256_working': sha(original),
                        'bytes_git_lf': len(source), 'bytes_working': len(original),
                        'lines': source.count(b'\n'), 'statement_counts': dict(counts),
                        'transformation': transformation, 'fence_present': True}
    record['source']['tables'] = [s['stmt']['CreateStmt']['relation']['relname'] for s in tree if 'CreateStmt' in s['stmt']]
    record['source']['role_declarations'] = sorted(set(re.findall(r'CREATE ROLE\s+(flooow_\w+)', source.decode())))
    record['source']['function_definitions'] = []
    for s in tree:
        f = s['stmt'].get('CreateFunctionStmt')
        if f:
            record['source']['function_definitions'].append({
                'name': '.'.join(x['String']['sval'] for x in f['funcname']),
                'inputs': ['.'.join(x['String']['sval'] for x in p['FunctionParameter']['argType']['names']) for p in f.get('parameters', []) if p['FunctionParameter'].get('mode') not in ['FUNC_PARAM_OUT', 'FUNC_PARAM_TABLE']]})
    import pglast
    record['parser'] = {'package_version': pglast.__version__, 'grammar_boundary': 'pglast grammar is static analysis, not PostgreSQL 18.4 execution evidence',
                        'input_file_hashes': {p.relative_to(Path(pglast.__file__).parent).as_posix(): sha(p.read_bytes()) for p in Path(pglast.__file__).parent.rglob('*') if p.is_file() and '__pycache__' not in p.parts}}
    record['recipe_sources'] = {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in [
        ROOT / 'scripts/validation/package_0090_source_closure.py', ROOT / 'scripts/validation/Package0090SourceClosureFlyway.java',
        ROOT / 'scripts/validation/package_0090_call_classifier.py', ROOT / 'scripts/validation/package_0090_operator_census.py',
        ROOT / 'scripts/validation/test_package_0090_source_closure.py']}
    protected = ['main', 'origin/main', 'feature/room-v2-executive-product-evolution',
                 'origin/feature/room-v2-executive-product-evolution', 'research/global-commerce-signal-intelligence',
                 'origin/research/global-commerce-signal-intelligence']
    record['protected_refs'] = {r: git('rev-parse', r).decode().strip() for r in protected}
    def save():
        (out / 'qualification.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    save()
    if args.execute_disposable:
        execute(record, out, source, candidate)
    record['canonical_mutated'] = V043.read_bytes() != original
    record['protected_refs_unchanged'] = all(git('rev-parse', r).decode().strip() == h for r, h in record['protected_refs'].items())
    save()
    print(json.dumps({'stage': record.get('stage', 'STATIC_ONLY'), 'cases': len(record['cases']), 'errors': record.get('errors', []), 'canonical_mutated': record['canonical_mutated']}))
    return int(bool(record.get('errors')) or record['canonical_mutated'] or not record['protected_refs_unchanged'])


def execute(record, out, source, candidate):
    work = Path(tempfile.mkdtemp(prefix='flooow-0090-source-closure-'))
    project = 'flooow-0090-g3f4-' + uuid.uuid4().hex[:12]
    volume, container = project + '-data', project + '-postgres'
    resources = []
    def run(a, **kw):
        return command(a, **kw).stdout
    def sql(s, check=True, role='postgres'):
        return command(['docker', 'exec', '-i', container, 'psql', '-X', '-w', '-U', role, '-d', 'g3f4', '-At', '-v', 'ON_ERROR_STOP=1', '-v', 'VERBOSITY=verbose'], s.encode(), check=check)
    record['errors'] = []
    try:
        image = json.loads(run(['docker', 'image', 'inspect', IMAGE]))[0]
        require(image['Id'] == IMAGE and image['Architecture'] == 'amd64' and image['Os'] == 'linux', 'Pinned image mismatch')
        record['image'] = {k: image.get(k) for k in ['Id', 'RepoDigests', 'Architecture', 'Os']}
        native = ROOT / 'applications/marketplace-operations-persistence-postgres/native/flooow_offline_mac32'
        shutil.copytree(native, work / 'native')
        record['native_sources'] = {p.name: sha(p.read_bytes()) for p in native.iterdir() if p.is_file()}
        build = run(['docker', 'run', '--rm', '--network', 'none', '--mount', f'type=bind,source={work},target=/review', '--entrypoint', 'sh', IMAGE, '-c', 'set -eu; cd /review/native; make with_llvm=no >/review/build.log 2>&1; pg_config --version; openssl version; ldd flooow_offline_mac32.so; sha256sum flooow_offline_mac32.so'])
        (out / 'native-build.txt').write_bytes(build)
        record['native_binary_sha256'] = sha((work / 'native/flooow_offline_mac32.so').read_bytes())
        if record['native_binary_sha256'] != '5aeedcdb693442b7738b6f33604e059094f584af29d1879bf35482ca06ef63b5':
            raise RuntimeError('Pinned approved full native binary differs; do not install')
        frozen = work / 'migrations'
        frozen.mkdir()
        record['frozen_migrations'] = []
        for p in sorted(MIGRATIONS.glob('V*.sql')):
            if int(p.name.split('__')[0][1:]) > 42:
                continue
            rel = p.relative_to(ROOT).as_posix()
            b = git('show', 'HEAD:' + rel)
            if b != git('show', FROZEN + ':' + rel) or p.read_bytes().replace(b'\r\n', b'\n') != b:
                raise RuntimeError('Frozen V001-V042 drift')
            (frozen / p.name).write_bytes(b)
            crc = 0
            for line in b.decode('utf-8-sig').splitlines():
                crc = zlib.crc32(line.encode('utf-8'), crc)
            if crc >= 2 ** 31:
                crc -= 2 ** 32
            record['frozen_migrations'].append({'script': p.name, 'sha256': sha(b), 'flyway_crc32': crc})
        require(len(record['frozen_migrations']) == 42, 'Exact 42 frozen migrations required')
        # This directory contains ONLY exact V001-V042, never candidate V043.
        password = secrets.token_hex(32)
        (work / 'postgres-password').write_text(password, encoding='ascii')
        for kind, name in [('volume', volume), ('network', project)]:
            run(['docker', kind, 'create', '--label', 'com.docker.compose.project=' + project, name])
            resources.append((kind, name))
        run(['docker', 'run', '-d', '--name', container, '--label', 'com.docker.compose.project=' + project,
             '--network', project, '-p', '127.0.0.1::5432', '--mount', f'type=volume,source={volume},target=/var/lib/postgresql',
             '--mount', f'type=bind,source={work},target=/review,readonly', '-e', 'POSTGRES_PASSWORD_FILE=/review/postgres-password',
             '-e', 'POSTGRES_DB=g3f4', '-e', 'POSTGRES_INITDB_ARGS=--encoding=UTF8 --locale=en_US.utf8',
             '--entrypoint', '/usr/local/bin/docker-entrypoint.sh', IMAGE, 'postgres'])
        resources.append(('container', container))
        details = json.loads(run(['docker', 'inspect', container]))[0]
        bindings = details['NetworkSettings']['Ports']['5432/tcp']
        require(len(bindings) == 1 and bindings[0]['HostIp'] == '127.0.0.1', 'Loopback-only binding required')
        require({m.get('Name') for m in details['Mounts'] if m['Type'] == 'volume'} == {volume}, 'Only fresh owned volume allowed')
        record['isolation'] = {'container_id': details['Id'], 'container': container, 'network': project, 'volume': volume, 'bindings': bindings, 'mounts': details['Mounts']}
        for _ in range(60):
            if command(['docker', 'exec', container, 'pg_isready', '-U', 'postgres'], check=False).returncode == 0:
                break
            time.sleep(.5)
        else:
            raise RuntimeError('Disposable PostgreSQL did not start')
        record['postgres_version'] = sql('SELECT version();').stdout.decode().strip()
        cache = Path.home() / '.gradle/caches/modules-2/files-2.1'
        cp = os.pathsep.join(str(p) for p in sorted(cache.rglob('*.jar')))
        record['jvm_dependency_hashes'] = {p.relative_to(cache).as_posix(): sha(p.read_bytes()) for p in sorted(cache.rglob('*.jar'))}
        helpers = [ROOT / 'scripts/validation/Package0090SourceClosureFlyway.java']
        (work / 'javac.args').write_text('-cp\n"' + cp.replace('\\', '/') + '"\n-d\n"' + work.as_posix() + '"\n' + '\n'.join('"' + p.as_posix() + '"' for p in helpers), encoding='utf-8')
        run(['javac', '@' + str(work / 'javac.args')])
        (work / 'flyway.properties').write_text(f'url=jdbc:postgresql://127.0.0.1:{bindings[0]["HostPort"]}/g3f4\npassword={password}\nmigrations={frozen.as_posix()}\ntarget=042\nproject={project}\nvolume={volume}\ncontainer={container}\n', encoding='ascii')
        (work / 'java.args').write_text('-cp\n"' + (str(work) + os.pathsep + cp).replace('\\', '/') + '"\nPackage0090SourceClosureFlyway\n"' + (work / 'flyway.properties').as_posix() + '"\n', encoding='utf-8')
        flyway = command(['java', '@' + str(work / 'java.args')], check=False)
        (out / 'flyway-042.txt').write_bytes((flyway.stdout + flyway.stderr).replace(password.encode(), b'[REDACTED]'))
        if flyway.returncode:
            raise RuntimeError('Exact V001-V042 Flyway baseline failed; no repair')
        history = json.loads(sql('SELECT json_agg(row_to_json(h) ORDER BY installed_rank) FROM public.flyway_schema_history h;').stdout)
        require(len(history) == 42 and all(h['success'] for h in history), 'Exact successful V001-V042 history required')
        for rank, (h, expected) in enumerate(zip(history, record['frozen_migrations']), 1):
            require(h['installed_rank'] == rank and int(h['version']) == rank and h['type'] == 'SQL'
                    and h['script'] == expected['script'] and h['checksum'] == expected['flyway_crc32'],
                    'Independent full ordered Flyway history/script/checksum mismatch')
        record['history_042'] = history
        record['stage'] = 'BASELINE_042_APPLIED'
        owners = ['control', 'verification', 'issuance', 'execution', 'audit', 'readiness', 'principal_lock', 'intent_audit']
        statements = []
        for o in owners:
            n = 'flooow_offline_' + o + '_owner'
            statements.append(f'CREATE ROLE {n} NOLOGIN ' + ('INHERIT' if o == 'control' else 'NOINHERIT') + ' NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;')
        for n in ['postgres'] + ['flooow_offline_' + o + '_owner' for o in owners]:
            for kind in ['TABLES', 'SEQUENCES', 'FUNCTIONS', 'TYPES', 'SCHEMAS', 'LARGE OBJECTS']:
                statements.append(f'ALTER DEFAULT PRIVILEGES FOR ROLE {n} REVOKE ALL ON {kind} FROM PUBLIC;')
        statements.append('GRANT USAGE ON SCHEMA public TO flooow_offline_control_owner;')
        sql('\n'.join(statements))
        run(['docker', 'exec', container, 'sh', '-c', 'set -eu; cp /review/native/flooow_offline_mac32.so "$(pg_config --pkglibdir)/"; cp /review/native/flooow_offline_mac32.control /review/native/flooow_offline_mac32--1.0.sql "$(pg_config --sharedir)/extension/"'])
        sql("BEGIN; CREATE SCHEMA offline_crypto AUTHORIZATION postgres; CREATE EXTENSION pgcrypto VERSION '1.4' SCHEMA offline_crypto; CREATE EXTENSION flooow_offline_mac32 VERSION '1.0'; REVOKE ALL ON SCHEMA offline_crypto FROM PUBLIC; REVOKE ALL ON ALL FUNCTIONS IN SCHEMA offline_crypto FROM PUBLIC; GRANT USAGE ON SCHEMA offline_crypto TO flooow_offline_readiness_owner; GRANT EXECUTE ON FUNCTION offline_crypto.hmac(bytea,bytea,text),offline_crypto.timing_safe_equal32(bytea,bytea) TO flooow_offline_readiness_owner; COMMIT;")
        record['crypto_catalog'] = json.loads(sql("SELECT json_agg(json_build_object('signature',p.oid::regprocedure::text,'owner',pg_get_userbyid(p.proowner),'strict',p.proisstrict,'parallel',p.proparallel,'volatile',p.provolatile,'definer',p.prosecdef,'acl',p.proacl::text,'library',p.probin,'symbol',p.prosrc)) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='offline_crypto';").stdout)
        record['extensions'] = json.loads(sql("SELECT json_agg(json_build_object('name',e.extname,'version',e.extversion,'owner',pg_get_userbyid(e.extowner),'schema',n.nspname)) FROM pg_extension e JOIN pg_namespace n ON n.oid=e.extnamespace;").stdout)
        crypto_cases(record, sql)
        null_primitive_cases(record, sql)
        record['stage'] = 'CRYPTO_PREREQUISITES_INSTALLED'
        # First prove real canonical fence denial/rollback, without Flyway success rows.
        fence = sql('BEGIN;\n' + source.decode() + '\nCOMMIT;', check=False)
        record['fence_denial'] = {'exit': fence.returncode, 'stderr': fence.stderr.decode()}
        require(fence.returncode and '55000' in fence.stderr.decode(), 'Canonical fence must deny before DDL')
        prerequisite_cases(record, sql, candidate)
        # Then exactly-derived body, one transaction, never registered as canonical V043.
        body = sql('BEGIN;\n' + candidate.decode() + '\nCOMMIT;', check=False)
        (out / 'qualification-body.txt').write_bytes(body.stdout + body.stderr)
        record['body_exit'] = body.returncode
        record['body_stderr'] = body.stderr.decode()
        record['body_qualified'] = body.returncode == 0
        record['history_after'] = json.loads(sql('SELECT json_agg(row_to_json(h) ORDER BY installed_rank) FROM public.flyway_schema_history h;').stdout)
        require(record['history_after'] == history, 'Qualification must not alter canonical Flyway history')
        if body.returncode:
            record['stage'] = 'BODY_QUALIFICATION_BLOCKED'
            raise RuntimeError('Derived V043 body failed; transaction rolled back; no repair performed')
        record['stage'] = 'BODY_QUALIFIED_NOT_CANONICAL_EXECUTION'
        record['table_catalog'] = json.loads(sql("SELECT json_agg(json_build_object('name',c.relname,'owner',pg_get_userbyid(c.relowner),'acl',c.relacl::text,'rls',c.relrowsecurity,'force_rls',c.relforcerowsecurity) ORDER BY c.relname) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relname LIKE 'offline_%' AND c.relkind='r';").stdout)
        require(len(record['table_catalog']) == 15 and all(t['owner'] == 'flooow_offline_control_owner' for t in record['table_catalog']), 'Exact 15 ADMIN-owned control tables required')
        record['column_acl_catalog'] = json.loads(sql("SELECT coalesce(json_agg(json_build_object('table',c.relname,'column',a.attname,'acl',a.attacl::text) ORDER BY c.relname,a.attnum),'[]') FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relname LIKE 'offline_%' AND a.attnum>0 AND NOT a.attisdropped AND a.attacl IS NOT NULL;").stdout)
        restricted_campaign(record, sql)
        call_resolution_probes(record, sql)
        snapshot_query = 'SELECT json_build_object(' + ','.join("'" + t['name'] + "',(SELECT count(*) FROM public." + t['name'] + ')' for t in record['table_catalog']) + ');'
        empty = json.loads(sql(snapshot_query).stdout)
        require(all(v == 0 for v in empty.values()), 'Denied bootstrap campaign must emit no control/domain authority')
        record['independent_bootstrap_state_observation'] = empty
        old_start = sql('SELECT pg_postmaster_start_time();').stdout.decode().strip()
        old_system = sql('SELECT system_identifier FROM pg_control_system();').stdout.decode().strip()
        run(['docker', 'restart', container])
        for _ in range(60):
            if command(['docker', 'exec', container, 'pg_isready', '-U', 'postgres'], check=False).returncode == 0:
                break
            time.sleep(.5)
        else:
            raise RuntimeError('Owned container restart unavailable')
        new_start = sql('SELECT pg_postmaster_start_time();').stdout.decode().strip()
        new_system = sql('SELECT system_identifier FROM pg_control_system();').stdout.decode().strip()
        durable_history = json.loads(sql('SELECT json_agg(row_to_json(h) ORDER BY installed_rank) FROM public.flyway_schema_history h;').stdout)
        durable_empty = json.loads(sql(snapshot_query).stdout)
        passed = old_start != new_start and old_system == new_system and durable_history == history and durable_empty == empty
        record['cases'].append({'group': 'RESTART_BOOTSTRAP', 'name': 'same_owned_durable_state_no_activation', 'passed': passed,
                                'old_postmaster_start': old_start, 'new_postmaster_start': new_start, 'system_identifier': new_system})
        require(passed, 'Restart must preserve exact unprovisioned state')
        probe = sql("SELECT public.offline_inspect(NULL::uuid,NULL::bytea,NULL::uuid,NULL::text);", check=False, role='test_0090_audit')
        passed = probe.returncode != 0 and 'P0017' in probe.stderr.decode()
        record['cases'].append({'group': 'RESTART_BOOTSTRAP', 'name': 'new_restricted_session_still_denied', 'passed': passed, 'stderr': probe.stderr.decode()})
        require(passed, 'Restart must not restore unprovisioned authority')
    except Exception as e:
        record['errors'].append(type(e).__name__ + ': ' + str(e))
    finally:
        cleanup = []
        for kind, name in reversed(resources):
            inspect_kind = ['docker', 'inspect', name] if kind == 'container' else ['docker', kind, 'inspect', name]
            detail = json.loads(run(inspect_kind))[0]
            labels = detail['Config']['Labels'] if kind == 'container' else detail['Labels']
            if labels.get('com.docker.compose.project') != project:
                raise RuntimeError('Refuse cleanup outside owned disposable project')
            a = ['docker', 'rm', '-f', detail['Id']] if kind == 'container' else ['docker', kind, 'rm', name]
            r = command(a, check=False)
            cleanup.append({'kind': kind, 'name': name, 'removed': r.returncode == 0})
        # Erase only the private scratch secret; retain non-secret scratch for diagnostics.
        (work / 'postgres-password').unlink(missing_ok=True)
        (work / 'flyway.properties').unlink(missing_ok=True)
        record['cleanup'] = cleanup
        record['owned_runtime_destroyed'] = bool(resources) and all(c['removed'] for c in cleanup)
        record['scratch_secrets_erased'] = True


def crypto_cases(record, sql):
    def case(name, query, expected=None, state=None):
        r = sql(query, check=False)
        actual = r.stdout.decode().strip()
        passed = (r.returncode == 0 and actual == expected) if state is None else (r.returncode != 0 and state in r.stderr.decode())
        record['cases'].append({'group': 'CRYPTO', 'name': name, 'passed': passed, 'actual': actual, 'stderr': r.stderr.decode()})
        if not passed:
            raise RuntimeError('Crypto vector failed: ' + name)
    equal = 'offline_crypto.timing_safe_equal32'
    x = "decode(repeat('01',32),'hex')"
    y = "decode(repeat('02',32),'hex')"
    case('equal32', f'SELECT {equal}({x},{x});', 't')
    case('unequal32', f'SELECT {equal}({x},{y});', 'f')
    case('NULL_left', f"SELECT {equal}(NULL,{x}) IS NULL;", 't')
    case('NULL_right_invalid_length', f"SELECT {equal}(''::bytea,NULL) IS NULL;", 't')
    case('empty_length', f"SELECT {equal}(''::bytea,{x});", state='22023')
    case('short_length', f"SELECT {equal}(decode(repeat('01',31),'hex'),{x});", state='22023')
    case('long_length', f"SELECT {equal}({x},decode(repeat('01',33),'hex'));", state='22023')
    case('rfc4231_hmac', "SELECT encode(offline_crypto.hmac(convert_to('Hi There','UTF8'),decode(repeat('0b',20),'hex'),'sha256'),'hex');", 'b0344c61d8db38535ca8afceaf0bf12b881dc200c9833da726e9376c2e32cff7')
    case('hmac_NULL', "SELECT offline_crypto.hmac(NULL,''::bytea,'sha256') IS NULL;", 't')
    case('hmac_empty', "SELECT encode(offline_crypto.hmac(''::bytea,''::bytea,'sha256'),'hex');", hmac.new(b'', b'', hashlib.sha256).hexdigest())
    case('hmac_wrong_key', "SELECT encode(offline_crypto.hmac('context'::bytea,'wrong-key'::bytea,'sha256'),'hex');", hmac.new(b'wrong-key', b'context', hashlib.sha256).hexdigest())
    case('mac_single_bit_flip', f"SELECT {equal}({x},set_byte({x},0,0));", 'f')
    # RFC 8032 test vector 1, canonical DER SPKI Ed25519, empty message.
    key = '302a300506032b6570032100d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a'
    sig = 'e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b'
    verify = 'offline_crypto.canonical_spki_ed25519_verify'
    case('rfc8032_ed25519_valid', f"SELECT {verify}(decode('{key}','hex'),''::bytea,decode('{sig}','hex'));", 't')
    case('ed25519_bit_flip', f"SELECT {verify}(decode('{key}','hex'),''::bytea,decode('f5{sig[2:]}','hex'));", 'f')
    case('ed25519_wrong_context', f"SELECT {verify}(decode('{key}','hex'),'x'::bytea,decode('{sig}','hex'));", 'f')
    case('ed25519_NULL', f"SELECT {verify}(NULL,''::bytea,decode('{sig}','hex')) IS NULL;", 't')
    case('ed25519_malformed_spki', f"SELECT {verify}(''::bytea,''::bytea,decode('{sig}','hex'));", state='22023')
    case('ed25519_short_signature', f"SELECT {verify}(decode('{key}','hex'),''::bytea,decode('{sig[:-2]}','hex'));", state='22023')
    case('ed25519_wrong_algorithm', f"SELECT {verify}(decode('{key.replace('2b6570','2b6571')}','hex'),''::bytea,decode('{sig}','hex'));", state='22023')
    case('ed25519_noncanonical_trailing_byte', f"SELECT {verify}(decode('{key}00','hex'),''::bytea,decode('{sig}','hex'));", state='22023')


def restricted_campaign(record, sql):
    """Direct LOGIN sessions, no postgres SET ROLE shortcut for service behavior.

    Bootstrap-unprovisioned negative/STRICT cases only; not an ACTIVE fixture.
    """
    catalog = json.loads(sql("SELECT json_agg(json_build_object('oid',p.oid,'signature',p.oid::regprocedure::text,'name',p.proname,'args',ARRAY(SELECT format_type(t,NULL) FROM unnest(p.proargtypes::oid[]) t),'owner',pg_get_userbyid(p.proowner),'strict',p.proisstrict,'setof',p.proretset,'definer',p.prosecdef,'config',p.proconfig,'acl',p.proacl::text,'language',l.lanname,'volatile',p.provolatile,'parallel',p.proparallel) ORDER BY p.oid) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace JOIN pg_language l ON l.oid=p.prolang WHERE n.nspname='public' AND p.proname LIKE 'offline_%';").stdout)
    record['offline_function_catalog'] = catalog
    roles = {o: 'test_0090_' + o for o in ['verification', 'issuance', 'execution', 'audit']}
    for role in list(roles.values()) + ['test_0090_public']:
        sql(f'CREATE ROLE {role} LOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS; GRANT USAGE ON SCHEMA public TO {role};')
    wrappers = [p for p in catalog if p['name'] not in ('offline_lock_bound_principal',) and not p['name'].startswith('offline_internal_')]
    require(len(wrappers) == 18, 'Exact 18 wrapper signatures required')
    def check(group, name, query, role, expected=None, state=None):
        r = sql(query, check=False, role=role)
        passed = (r.returncode == 0 and r.stdout.decode().strip() == expected) if state is None else (r.returncode != 0 and state in r.stderr.decode())
        record['cases'].append({'group': group, 'name': name, 'role': role, 'passed': passed, 'actual': r.stdout.decode().strip(), 'stderr': r.stderr.decode()})
        if not passed:
            raise RuntimeError('Restricted case failed: ' + name)
    for p in wrappers:
        owner = p['owner'].removeprefix('flooow_offline_').removesuffix('_owner')
        caller = roles[owner]
        sql(f"GRANT EXECUTE ON FUNCTION {p['signature']} TO {caller};")
        nulls = ','.join('NULL::' + t for t in p['args'])
        invocation = 'public.' + p['name'] + '(' + nulls + ')'
        require(p['definer'] and p['config'] == ['search_path=pg_catalog, pg_temp'], 'Exact SECURITY DEFINER search_path required')
        query = 'SELECT count(*) FROM ' + invocation + ';' if p['setof'] else 'SELECT ' + invocation + ' IS NULL;'
        if p['strict']:
            check('NULL', 'strict_null_' + p['signature'], query, caller, '0' if p['setof'] else 't')
        else:
            check('NULL', 'explicit_null_denial_' + p['signature'], query, caller, state='P0017')
        check('ACL', 'PUBLIC_denied_' + p['signature'], query, 'test_0090_public', state='42501')
        for wrong in roles.values():
            if wrong != caller:
                check('ACL', 'cross_role_denied_' + wrong + '_' + p['signature'], query, wrong, state='42501')
        values = {'uuid': "'00000000-0000-0000-0000-000000000001'::uuid", 'bytea': "decode(repeat('00',32),'hex')", 'text': "'TEST_ONLY_NONCANONICAL'::text", 'bigint': '1::bigint', 'integer': '1::integer', 'timestamp with time zone': "'2026-10-13T00:00:00Z'::timestamptz"}
        args = ','.join(values[t] for t in p['args'])
        check('CALLER', 'unbound_bootstrap_denied_' + p['signature'], 'SELECT public.' + p['name'] + '(' + args + ');', caller, state='P0017')
    for role in roles.values():
        check('ACL', role + '_cannot_set_admin', 'SET ROLE postgres;', role, state='42501')
        for o in ['control', 'verification', 'issuance', 'execution', 'audit', 'readiness', 'principal_lock', 'intent_audit']:
            check('ACL', role + '_cannot_set_' + o, f'SET ROLE flooow_offline_{o}_owner;', role, state='42501')
        check('ACL', role + '_cannot_read_crypto', "SELECT offline_crypto.hmac(''::bytea,''::bytea,'sha256');", role, state='42501')
        check('ACL', role + '_cannot_read_key', 'SELECT key_material FROM public.offline_preflight_key;', role, state='42501')
        check('ACL', role + '_cannot_direct_DML', 'DELETE FROM public.offline_binding_header;', role, state='42501')
        check('ACL', role + '_cannot_create_public_shadow', 'CREATE FUNCTION public.offline_poison() RETURNS bool LANGUAGE sql AS $$SELECT true$$;', role, state='42501')
        for table in record['table_catalog']:
            check('ACL', role + '_raw_SELECT_denied_' + table['name'], 'SELECT * FROM public.' + table['name'] + ';', role, state='42501')
            if table['name'] != 'offline_binding_header':
                check('ACL', role + '_raw_DELETE_denied_' + table['name'], 'DELETE FROM public.' + table['name'] + ';', role, state='42501')
    record['qualification_roles'] = json.loads(sql("SELECT json_agg(row_to_json(r)) FROM (SELECT rolname,rolcanlogin,rolinherit,rolsuper,rolcreatedb,rolcreaterole,rolreplication,rolbypassrls FROM pg_roles WHERE rolname LIKE 'test_0090_%' OR rolname LIKE 'flooow_offline_%' ORDER BY rolname) r;").stdout)
    record['qualification_memberships'] = json.loads(sql("SELECT coalesce(json_agg(json_build_object('role',pg_get_userbyid(roleid),'member',pg_get_userbyid(member))), '[]') FROM pg_auth_members WHERE pg_get_userbyid(roleid) LIKE 'flooow_offline_%' OR pg_get_userbyid(member) LIKE 'test_0090_%';").stdout)
    require(not record['qualification_memberships'], 'Restricted roles must have zero memberships')
    require(all(not r['rolsuper'] and not r['rolbypassrls'] for r in record['qualification_roles']), 'No runtime superuser/BYPASSRLS')
    record['empty_policy_after_campaign'] = sql('SELECT count(*) FROM public.offline_deadline_policy;').stdout.decode().strip()
    require(record['empty_policy_after_campaign'] == '0', 'No numeric policy provisioned')
    record['restricted_campaign_boundary'] = 'UNPROVISIONED_ONLY; explicit NULL denial and ACL/guard denial are not governed successful operation'


def call_resolution_probes(record, sql):
    """Observe PostgreSQL parser decisions; never equate typed-NULL probes with source semantics."""
    from package_0090_call_classifier import classify
    groups, status = classify()
    record['call_classification'] = status
    observations = []
    for i, g in enumerate(groups):
        args = []
        for t in g['argument_types']:
            if t in ['unknown_literal', 'NULL_LITERAL']:
                args.append('NULL')
            elif t == 'char':
                args.append('NULL::pg_catalog."char"')
            elif t.endswith('%rowtype'):
                args.append('NULL::' + t.removesuffix('%rowtype'))
            else:
                args.append('NULL::' + t)
        require(bool(re.fullmatch(r'[a-zA-Z_][a-zA-Z_0-9.]*', g['callee_spelling'])), 'Unsafe callable spelling')
        view = f'test_0090_call_probe_{i}'
        query = 'BEGIN; SET LOCAL search_path=pg_catalog,pg_temp; CREATE TEMP VIEW ' + view + ' AS SELECT ' + g['callee_spelling'] + '(' + ','.join(args) + ') AS result; SELECT ev_action::text FROM pg_rewrite WHERE ev_class=\'pg_temp.' + view + "'::regclass AND rulename='_RETURN'; ROLLBACK;"
        r = sql(query, check=False)
        observations.append({'shape_index': i, 'name': g['callee_spelling'], 'argument_types': g['argument_types'],
                             'site_count': g['source_site_n'], 'parsed': r.returncode == 0,
                             'function_oids': sorted(set(re.findall(r':(?:funcid|aggfnoid) (\d+)', r.stdout.decode()))),
                             'operator_oids': sorted(set(re.findall(r':opno (\d+)', r.stdout.decode()))),
                             'stderr': r.stderr.decode(), 'full_source_binding_proven': False})
    record['call_resolution_probes'] = observations
    record['call_resolution_probe_input_sha256'] = status['input_sha256']
    record['call_resolution_probe_boundary'] = 'Parser observations under typed NULL and fixed test search_path; original contextual literals, scoped caller ACL and authority meaning NOT proven'


def prerequisite_cases(record, sql, candidate):
    before = sql("SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relname LIKE 'offline_%';").stdout
    for name, attack, diagnostic in [
        ('PUBLIC_schema_CREATE', 'GRANT CREATE ON SCHEMA public TO PUBLIC;', 'PUBLIC-writable'),
        ('unsafe_creator_defaults', 'ALTER DEFAULT PRIVILEGES FOR ROLE postgres GRANT EXECUTE ON FUNCTIONS TO PUBLIC;', 'Unsafe Package 0090 global creator defaults'),
        ('wrong_crypto_owner', 'ALTER SCHEMA offline_crypto OWNER TO flooow_offline_control_owner;', 'crypto schema/identity prerequisite'),
        ('PUBLIC_native_EXECUTE', 'GRANT EXECUTE ON FUNCTION offline_crypto.timing_safe_equal32(bytea,bytea) TO PUBLIC;', 'Unapproved crypto member privilege'),
        ('wrong_crypto_ABI_volatility', 'ALTER FUNCTION offline_crypto.hmac(bytea,bytea,text) VOLATILE;', 'exact crypto function contract')]:
        r = sql('BEGIN; ' + attack + '\n' + candidate.decode() + '\nCOMMIT;', check=False)
        passed = r.returncode != 0 and diagnostic in r.stderr.decode()
        after = sql("SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relname LIKE 'offline_%';").stdout
        passed = passed and before == after
        record['cases'].append({'group': 'POSTGRES_PREFLIGHT', 'name': name, 'passed': passed, 'stderr': r.stderr.decode(), 'catalog_count_unchanged': before == after})
        require(passed, 'Adversarial prerequisite must deny and rollback: ' + name)


def null_primitive_cases(record, sql):
    # Primitive contract observations, not full authority consumer proof.
    for name, query, expected, state in [
        ('NULLIF_text_type', "SELECT pg_typeof(NULLIF((ARRAY['x']::text[])[1],''))::text;", 'text', None),
        ('NULLIF_nonempty_UTF8', "SELECT encode(convert_to(NULLIF((ARRAY['x']::text[])[1],''),'UTF8'),'hex');", '78', None),
        ('NULLIF_empty_NULL', "SELECT convert_to(NULLIF(''::text,''),'UTF8') IS NULL;", 't', None),
        ('NULLIF_NULL_NULL', "SELECT convert_to(NULLIF(NULL::text,''),'UTF8') IS NULL;", 't', None),
        ('boolean_three_values', "SELECT TRUE::text || ',' || FALSE::text || ',' || (NULL::bool IS NULL)::text;", 'true,false,true', None),
        ('NULL_comparison_UNKNOWN', 'SELECT (NULL::uuid=NULL::uuid) IS NULL;', 't', None),
        ('NULL_distinct_is_FALSE', 'SELECT (NULL::uuid IS DISTINCT FROM NULL::uuid)::text;', 'false', None),
        ('NOT_IN_NULL_is_UNKNOWN', 'SELECT (1 NOT IN (2,NULL)) IS NULL;', 't', None),
        ('scalar_missing_is_NULL', 'SELECT (SELECT x FROM (VALUES(1)) t(x) WHERE false) IS NULL;', 't', None),
        ('EXISTS_missing_is_FALSE', 'SELECT EXISTS(SELECT 1 WHERE false)::text;', 'false', None),
        ('scalar_duplicate_denied', 'SELECT (SELECT x FROM (VALUES(1),(2)) t(x));', None, '21000'),
        ('wrong_uuid_cast_denied', "SELECT 'TEST_ONLY_WRONG_TYPE'::uuid;", None, '22P02')]:
        r = sql(query, check=False)
        passed = (r.returncode == 0 and r.stdout.decode().strip() == expected) if state is None else (r.returncode != 0 and state in r.stderr.decode())
        record['cases'].append({'group': 'NULL_PRIMITIVE', 'name': name, 'passed': passed, 'actual': r.stdout.decode().strip(), 'stderr': r.stderr.decode()})
        require(passed, 'Native NULL primitive failed: ' + name)


if __name__ == '__main__':
    raise SystemExit(main())
