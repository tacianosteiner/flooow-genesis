"""Explicitly authorized disposable TEST activation and native-health campaign.

No readiness or wrapper invocation is permitted without the complete measured
health gate. Audit is external to PostgreSQL and operational actors cannot
access the authoritative store. Exported records are non-secret proof copies.
"""
import copy
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import uuid
import package_0090_source_closure as q
from package_0090_first_positive import save

ROOT = q.ROOT
BASELINE = 'caef8dd8a964a9eb173deda40f85449b43b970dd'
DECISION = 'TEST_ONLY/0090/activation-and-native-health/s04/v1'
RECIPE = 'TEST_ONLY/0090/activation/db-clock-in-transaction/v1'
OUT = ROOT / 'docs/evidence/package-0090-authorized-test-activation-native-health-s04'
NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, 'https://flooow.test/qualification/package0090')
AUTHORIZATION_FILE = Path('C:/Users/xmz_r/.codex/attachments/a47c5f1e-dfcb-4b80-8384-300be7a580c8/Pasted text.txt')
PSYCOPG = Path.home() / 'AppData/Local/Temp/flooow-0090-authorized-psycopg'


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


def identities():
    return {'decision_id': DECISION, 'approval_id': str(uuid.uuid5(NAMESPACE, DECISION + '/approval')),
            'change_id': str(uuid.uuid5(NAMESPACE, DECISION + '/change')),
            'approving_actor': 'TEST_ONLY_USER_APPROVAL/' + str(uuid.uuid5(NAMESPACE, DECISION + '/actor')),
            'scope': 'TEST_ONLY_DISPOSABLE_S04', 'baseline_head': BASELINE, 'source_sha256': q.SOURCE_HASH,
            'activation_recipe': RECIPE, 'policy_version': 'fixture-1',
            'policy_digest': json.loads((ROOT / 'docs/evidence/PACKAGE-0090-G3F-3B-FIXTURE-001.json').read_text())['canonical_policy_sha256']}


class Denied(ValueError):
    pass


def ensure(condition, message):
    if not condition:
        raise Denied(message)


class Audit:
    def __init__(self, path):
        self.path = path
        self.records = []
        self.tip = '0' * 64
        self.fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_APPEND, 0o600)

    def append(self, binding, status, database_outcome_timestamp=None):
        record = {**binding, 'sequence': len(self.records) + 1, 'previous_hash': self.tip,
                  'status': status, 'audit_timestamp_utc': dt.datetime.now(dt.timezone.utc).isoformat(timespec='microseconds')}
        if database_outcome_timestamp is not None:
            record['database_outcome_timestamp'] = database_outcome_timestamp
        record['record_hash'] = q.sha(canonical(record))
        encoded = canonical(record) + b'\n'
        ensure(os.write(self.fd, encoded) == len(encoded), 'Short audit append')
        os.fsync(self.fd)
        self.records.append(record); self.tip = record['record_hash']
        return record

    def close(self):
        os.close(self.fd)


def validate_audit(records, tip, binding):
    ensure(records, 'Missing PREPARED')
    previous = '0' * 64
    prepared = None
    for sequence, row in enumerate(records, 1):
        ensure(row['sequence'] == sequence and row['previous_hash'] == previous, 'Sequence/previous hash')
        payload = {k: v for k, v in row.items() if k != 'record_hash'}
        ensure(q.sha(canonical(payload)) == row['record_hash'], 'Tampered record')
        ensure(all(row.get(k) == v for k, v in binding.items()), 'Divergent binding')
        if row['status'] == 'PREPARED':
            ensure(prepared is None and sequence == 1, 'Duplicate/divergent preparation')
            prepared = row
        elif row['status'] == 'COMMITTED':
            ensure(prepared is not None and sequence == 2, 'Commit without preparation')
        elif row['status'] in ('UNKNOWN', 'ROLLED_BACK'):
            raise Denied('Non-committed outcome')
        else:
            raise Denied('Unknown audit status')
        previous = row['record_hash']
    ensure(previous == tip, 'Trusted external tip mismatch')
    ensure(records[-1]['status'] == 'COMMITTED', 'Missing final reconciliation')
    return True


def validate_approval(candidate, expected):
    ensure(candidate == expected, 'Exact immutable approved identity/context required')


def validate_activation_metadata(candidate, captured, encoded_us):
    ensure(candidate.get('effective_from') == captured.isoformat(timespec='microseconds'), 'Activation instant differs from the single approved DB capture')
    ensure(candidate.get('effective_from_epoch_us') == encoded_us, 'Activation integer encoding differs')
    ensure(candidate.get('activation_recipe') == RECIPE, 'Activation recipe differs')


def qualify(sql, run, container, folder, record, fixture, runtime_work):
    accepted = json.loads((OUT / 'accepted-test-decision.json').read_text())
    ensure(accepted['status'] == 'APPROVED_TEST_ONLY' and accepted['decision_id'] == DECISION,
           'Explicit accepted TEST decision missing')
    expected = identities()
    ensure(accepted['identities'] == expected, 'Accepted identity drift')
    ensure(q.sha(AUTHORIZATION_FILE.read_bytes()) == accepted['user_request_sha256'], 'User authorization source drift')
    details = json.loads(run(['docker', 'inspect', container]))[0]
    ensure(details['Image'] == q.IMAGE and details['Config']['Labels']['com.docker.compose.project'] == record['isolation']['project'], 'Foreign runtime')
    review = next(m['Source'] for m in details['Mounts'] if m['Destination'] == '/review')
    normalized = review.replace('\\', '/').lower()
    expected_work = Path(runtime_work).as_posix().lower()
    docker_work = '/run/desktop/mnt/host/' + expected_work[0] + expected_work[2:]
    ensure(normalized in (expected_work, docker_work), 'Private working directory mount mismatch')
    sys.path.insert(0, str(PSYCOPG)); import psycopg
    password = (Path(runtime_work) / 'postgres-password').read_text()
    port = details['NetworkSettings']['Ports']['5432/tcp'][0]
    ensure(port['HostIp'] == '127.0.0.1', 'Nonloopback target')
    connection = psycopg.connect(host='127.0.0.1', port=int(port['HostPort']), dbname='g3f4', user='postgres', password=password, autocommit=True)
    policy_bytes = bytes.fromhex(fixture['canonical_policy_hex'])
    ensure(q.sha(policy_bytes) == expected['policy_digest'], 'Exact29-field approved policy required')
    target = {'deployment_id': str(uuid.uuid5(NAMESPACE, details['Id'] + '/deployment')),
              'incarnation_id': str(uuid.uuid5(NAMESPACE, details['Id'] + '/incarnation'))}
    audit_dir = Path(tempfile.mkdtemp(prefix='flooow-0090-test-admin-audit-'))
    audit = Audit(audit_dir / 'administrative.jsonl')
    case_rows = []

    def case(name, passed, detail, group):
        row = {'name': name, 'passed': bool(passed), 'details': detail, 'group': group}
        record['cases'].append(row); case_rows.append(row)
        ensure(passed, 'Authorized campaign assertion: ' + name)

    activation = None
    try:
        # These are executable denials at the trusted loader boundary, before DML.
        for field in ['approval_id', 'change_id', 'approving_actor', 'decision_id', 'policy_digest', 'policy_version']:
            for mutation in ['missing', 'wrong']:
                candidate = copy.deepcopy(expected)
                if mutation == 'missing': candidate.pop(field)
                else: candidate[field] = 'TEST_ONLY_WRONG'
                denied = False
                try: validate_approval(candidate, expected)
                except Denied: denied = True
                case(mutation + '_' + field, denied, 'Trusted loader rejects before SQL; canonical schema is not claimed to enforce external approval', 'ACTIVATION')
        validate_approval(expected, accepted['identities'])
        connection.execute('BEGIN')
        instant, micros, transaction = connection.execute("WITH captured AS MATERIALIZED (SELECT pg_catalog.clock_timestamp()::timestamptz(6) AS instant) SELECT instant,(extract(epoch FROM instant)*1000000)::bigint,pg_catalog.pg_current_xact_id()::text FROM captured").fetchone()
        delta = instant - dt.datetime(1970, 1, 1, tzinfo=dt.timezone.utc)
        encoded_us = delta.days * 86400000000 + delta.seconds * 1000000 + delta.microseconds
        ensure(encoded_us == micros, 'Exact timestamp integer encoding')
        ensure(connection.execute("SELECT 'epoch'::timestamptz + (%s::text||' microseconds')::interval = %s::timestamptz", (micros, instant)).fetchone()[0], 'DB microsecond roundtrip')
        binding = {**expected, **target, 'actor': expected['approving_actor'],
                   'canonical_policy_hex': policy_bytes.hex(), 'effective_from': instant.isoformat(timespec='microseconds'),
                   'effective_from_epoch_us': micros, 'transaction_identity': transaction,
                   'database_capture': 'clock_timestamp() exactly once in MATERIALIZED capture; timestamptz(6); zero offset',
                   'affected_binding_ids': [], 'validation_outcome': 'EXACT_APPROVED_29_FIELDS_DIGEST_VERSION_TARGET_AND_RECIPE'}
        validate_activation_metadata(binding, instant, micros)
        audit.append(binding, 'PREPARED')
        connection.execute('INSERT INTO public.offline_deadline_policy(policy_version,policy_digest,canonical_policy,effective_from) VALUES(%s,%s,%s,%s)', ('fixture-1', bytes.fromhex(expected['policy_digest']), policy_bytes, instant))
        connection.execute('COMMIT')
        actual = connection.execute("WITH observed AS MATERIALIZED (SELECT clock_timestamp() AS instant) SELECT policy_version,encode(policy_digest,'hex'),encode(canonical_policy,'hex'),effective_from,observed.instant>=effective_from,observed.instant FROM public.offline_deadline_policy CROSS JOIN observed").fetchone()
        ensure(actual[:3] == ('fixture-1', expected['policy_digest'], policy_bytes.hex()) and actual[3] == instant and actual[4], 'Independent committed policy reconciliation')
        audit.append(binding, 'COMMITTED', database_outcome_timestamp=actual[5].isoformat(timespec='microseconds'))
        on_disk = [json.loads(line) for line in audit.path.read_text().splitlines()]
        validate_audit(on_disk, audit.tip, binding)
        case('valid_registration_roundtrip_committed_ACTIVE', True, {'timestamp': binding['effective_from'], 'integer_us': micros, 'transaction': transaction, 'audit_tip': audit.tip}, 'ACTIVATION')
        # An exact replay reconciles original metadata. It never recaptures a clock.
        case('exact_replay_original_instant_reconciled', actual[3] == instant and validate_audit(on_disk, audit.tip, binding), 'No second INSERT/upsert/new effective_from', 'ACTIVATION')
        try:
            connection.execute('INSERT INTO public.offline_deadline_policy(policy_version,policy_digest,canonical_policy,effective_from) VALUES(%s,%s,%s,%s)', ('fixture-1', bytes.fromhex(expected['policy_digest']), policy_bytes, instant))
            duplicate = False
        except psycopg.errors.UniqueViolation:
            duplicate = True
        case('duplicate_registration_SQL_denied', duplicate, '23505; plain INSERT, no upsert', 'ACTIVATION')
        for name, value in [('future_mismatched_activation', instant + dt.timedelta(seconds=1)), ('NULL_activation', None), ('divergent_replay', instant + dt.timedelta(microseconds=1))]:
            candidate = copy.deepcopy(binding)
            candidate['effective_from'] = value.isoformat(timespec='microseconds') if value is not None else None
            denied = False
            try: validate_activation_metadata(candidate, instant, micros)
            except Denied: denied = True
            case(name, denied, 'Actual loader metadata validator rejects before DML; captured instant is not renewed', 'ACTIVATION')
        attacks = [
            ('missing_PREPARED', lambda rows: rows.pop(0)),
            ('bad_previous_hash', lambda rows: rows[1].update(previous_hash='f'*64)),
            ('modified_record', lambda rows: rows[0].update(actor='TEST_ONLY_WRONG')),
            ('duplicate_sequence', lambda rows: rows[1].update(sequence=1)),
            ('divergent_record', lambda rows: rows[1].update(effective_from_epoch_us=micros+1)),
            ('COMMITTED_without_PREPARED', lambda rows: rows[0].update(status='COMMITTED')),
            ('wrong_decision_id', lambda rows: rows[0].update(decision_id='TEST_ONLY_WRONG')),
            ('wrong_target', lambda rows: rows[0].update(deployment_id=str(uuid.uuid4()))),
            ('wrong_policy_digest', lambda rows: rows[0].update(policy_digest='f'*64)),
            ('UNKNOWN_outcome', lambda rows: rows[1].update(status='UNKNOWN')),
            ('missing_final_reconciliation', lambda rows: rows.pop())]
        for name, mutate in attacks:
            rows = copy.deepcopy(on_disk); mutate(rows); denied = False
            try: validate_audit(rows, audit.tip, binding)
            except Denied: denied = True
            case('audit_' + name, denied, 'Actual committed proof copy mutation denied by authoritative chain/tip validator', 'ADMIN_AUDIT')
        activation = {'approved': True, 'proven': True, 'audit_contract_ready': True, 'tamper_evident': True,
                      'effective_from_source': 'ADMIN_TRANSACTION_CLOCK_TIMESTAMP_ONCE_TIMESTAMPTZ6_ZERO_OFFSET',
                      'binding': binding, 'audit_trusted_tip': audit.tip, 'audit_authoritative_store': str(audit.path),
                      'replay_proven': True, 'production_policy': False}
        save(folder, 'test-admin-audit-chain.json', {'records': on_disk, 'trusted_tip': audit.tip,
             'authoritative_path': str(audit.path), 'append_only_writer': 'O_EXCL creation; O_APPEND only; fsync every record; no update/rewrite method',
             'tip_anchor': 'Trusted qualification writer plus independently retained manifest; chain cannot establish trust in a caller-supplied replacement tip',
             'operational_access': 'Not mounted into container; no Package table/API; no service access',
             'distributed_atomicity_claim': False, 'commit_reconciled_before_eligibility': True})
        save(folder, 'test-policy-activation.json', activation)
        case('audit_chain_external_committed_valid', validate_audit(on_disk, audit.tip, binding), 'Full chain and frozen target validated', 'ADMIN_AUDIT')
        # Native implementation runs only within the already verified owned Linux runtime.
        native_source = ROOT / 'scripts/validation/package_0090_s04_native_health.c'
        private = '/run/test-only-0090-health'
        run(['docker', 'exec', '--user', '0', container, 'mkdir', '-m', '0700', private])
        context_path = folder / 'native-context.json'
        native_context = {'decision': accepted, 'policy_activation': activation, 'target': target,
                          'history_source_sha256': record['frozen_inputs'],
                          'expected_column_acl_manifest_sha256': q.sha((folder / 'expected-acl-manifest.json').read_bytes()),
                          'native_library_sha256': record['binary_sha256'], 'container': details['Id']}
        context_path.write_bytes(canonical(native_context))
        run(['docker', 'cp', str(context_path), container + ':' + private + '/context.json'])
        run(['docker', 'cp', str(native_source), container + ':' + private + '/health.c'])
        compile_result = q.command(['docker', 'exec', container, 'cc', '-O2', '-Wall', '-Wextra', private + '/health.c', '-o', private + '/health', '-lcrypto'], check=False)
        save(folder, 'native-build.json', {'source_sha256': q.sha(native_source.read_bytes()), 'exit': compile_result.returncode,
              'stdout': compile_result.stdout.decode(), 'stderr': compile_result.stderr.decode()})
        ensure(compile_result.returncode == 0, 'Native health harness build failed')
        binary = run(['docker', 'exec', container, 'sha256sum', private + '/health']).decode().split()[0]
        result = q.command(['docker', 'exec', '--user', '0', container, private + '/health'], check=False)
        (folder / 'native-health-raw.json').write_bytes(result.stdout)
        (folder / 'native-health-stderr.txt').write_bytes(result.stderr)
        ensure(result.returncode == 0, 'Native independent identity/work assertions failed')
        health = json.loads(result.stdout)
        ensure(health['context_sha256'] == q.sha(context_path.read_bytes()), 'Native target/decision context binding differs')
        ledger_bytes = run(['docker', 'exec', container, 'cat', private + '/generation-ledger.jsonl'])
        (folder / 'native-generation-ledger.jsonl').write_bytes(ledger_bytes)
        health.update({'harness_binary_sha256': binary, 'harness_source_sha256': q.sha(native_source.read_bytes()),
                       'container_identity': details['Id'], 'deployment_incarnation': target,
                       'accepted_decision': DECISION, 'full_package_health_ready': False,
                       'contract_complete': False,
                       'limits': ['Original BOOTTIME observations must all satisfy the unchanged100us window; stale work cannot authorize READY',
                                  'TEST components qualify individual work mechanisms; full generation replacement/enrollment/negative campaigns remain unclosed',
                                  'Producer signs a generation challenge; no claim of full canonical V041 original-attestation lineage closure']})
        for participant in health['participants']:
            case('native_' + participant['participant'] + '_independent_work', participant['functional_work_independently_verified'] and participant['SCM_CREDENTIALS_verified'], participant, 'NATIVE_WORK')
        case('native_freshness_denies_stale_observations', not health['native_health_ready'] and any(p['age_ns'] > 100000 for p in health['participants']),
             {'window_ns': 100000, 'observed_ages_ns': [p['age_ns'] for p in health['participants']]}, 'NATIVE_FRESHNESS')
        save(folder, 'native-health-runtime.json', health)
        # Do not manufacture current health, renew emission timestamps, or insert READY.
        unchanged = connection.execute('SELECT (SELECT count(*) FROM offline_readiness),(SELECT count(*) FROM offline_binding_header),(SELECT count(*) FROM offline_expected_signed_attestation)').fetchone()
        case('failed_health_prevents_READY_header_and_wrapper', unchanged == (0,0,0), {'counts': list(unchanged), 'wrapper_invoked': False}, 'READINESS_INTERLOCK')
        blocked = {'status': 'NOT_EXECUTED_FAILED_NATIVE_HEALTH_PRECHECK', 'decision_authorized': True,
                   'policy_activation_proven': True, 'audit_chain_proven': True, 'first_path_health_ready': False,
                   'readiness_created': False, 'header_registered': False, 'original_registered': False,
                   'positive_executed': False, 'positive_pass': False, 'actual_rows': None,
                   'precheck': 'FAIL_NATIVE_FRESHNESS_AND_INCOMPLETE_CONTRACT_CAMPAIGN',
                   'counts': list(unchanged), 'production_authority': False}
        for name in ['readiness-runtime.json','header-original-registration.json','auditor-slot-runtime.json','s04-runtime.json',
                     's04-negative-runtime.json','s04-search-path-runtime.json','s04-semantic-runtime.json','s04-null-runtime.json','s04-acl-runtime.json']:
            save(folder, name, {**blocked, 'artifact': name, 'closure_complete': False})
        save(folder, 'native-health-negative-campaign.json', {'status': 'NOT_EXECUTED_NO_VALID_FRESH_CONTROL',
            'planned': 'participant_missing wrong_participant wrong_generation not_enrolled stale_observation future_observation replayed_observation wrong_binary_process wrong_host wrong_dependency wrong_catalog unauthenticated_channel failed_work heartbeat_only cross_participant observer_unavailable host_root_mismatch'.split(),
            'reason': 'An already stale control cannot prove independent sibling denials; no fabricated fresh evidence is substituted'})
        save(folder, 'qualification-cases.json', {'cases': case_rows, 'failures': sum(not c['passed'] for c in case_rows),
             'runtime_goal_achieved': False, 'not_attempted_cases_not_counted': True})
        record['authorized_s04'] = {**blocked, 'native_health_evidence': True, 'policy_activation_proven': True}
    except Exception:
        if connection.info.transaction_status.name != 'IDLE':
            connection.execute('ROLLBACK')
        if audit.records and audit.records[-1]['status'] == 'PREPARED':
            audit.append({k:v for k,v in audit.records[0].items() if k not in ['record_hash','sequence','previous_hash','status','audit_timestamp_utc']}, 'UNKNOWN')
        save(folder, 'test-admin-audit-chain-development.json', {'records': audit.records, 'trusted_tip': audit.tip})
        raise
    finally:
        audit.close(); connection.close(); password = None


def adopt():
    OUT.mkdir(parents=True, exist_ok=True)
    accepted = {'status': 'APPROVED_TEST_ONLY', 'decision_id': DECISION,
        'identities': identities(), 'user_request_sha256': q.sha(AUTHORIZATION_FILE.read_bytes()),
        'approval_provenance': 'Explicit user-authorized TEST decision in supplied request; identifier derivation expressly authorized in phase2',
        'namespace': str(NAMESPACE), 'identity_derivation': 'UUIDv5 explicit TEST URL namespace + accepted decision + typed suffix',
        'production_authority': False, 'migration_authority': False, 'field_authority': False,
        'execution_authority': False, 'recovery_authority': False,
        'scope': 'Disposable S04 qualification; seven participants, independent HEALTH_GUARD and HOST_PLATFORM; unchanged fixture-1 timings'}
    save(OUT, 'accepted-test-decision.json', accepted); save(OUT, 'test-identities.json', identities())
    (OUT / 'USER-AUTHORIZATION.txt').write_bytes(AUTHORIZATION_FILE.read_bytes())
    for name in ['ADR-0090-governed-offline-field-proof-exclusive-capability-composition.md', 'SPEC-0090-governed-offline-field-proof-exclusive-capability-composition.md']:
        subdir = 'adr' if name.startswith('ADR') else 'specifications'
        path = ROOT / 'docs' / subdir / name
        text = path.read_text(encoding='utf-8-sig')
        marker = '## Approved TEST-only S04 activation and native-health qualification â€” 2026-10-13'
        ensure(marker not in text, 'Refuse duplicate decision adoption')
        text += '\n\n' + marker + '\n\nDECISION_ID=' + DECISION + '\nSTATUS=APPROVED_TEST_ONLY\n\n'
        text += ('Explicit user approval supplies the bounded authority previously absent. Adopt\n'
                 'TEST_ONLY/0090/activation/db-clock-in-transaction/v1: capture\n'
                 'pg_catalog.clock_timestamp() exactly once inside ADMIN registration, finite\n'
                 'timestamptz(6), zero offset, exact integer-microsecond roundtrip. Freeze\n'
                 'deterministic TEST-only approval/change/actor identities in the accepted\n'
                 'decision. Provision an external append-only tamper-evident TEST administrative\n'
                 'audit with complete25.4 binding and independent commit reconciliation.\n\n'
                 'Authorize a disposable TEST harness for POSTMASTER, SUPERVISOR, RECEIVER,\n'
                 'CENSUS_OBSERVER, APPROVAL_PRODUCER, APPROVAL_CONSUMER and ENFORCEMENT_WORKER,\n'
                 'independent HEALTH_GUARD and trusted HOST_PLATFORM. This includes bounded\n'
                 'TEST generation ledger/enrollment/authenticated channel/pidfd/SCM_RIGHTS,\n'
                 'functional-work/dependency/catalog/freshness/restart qualification only;\n'
                 'production generation implementation remains unauthorized. All seven\n'
                 'requirements remain mandatory. Keep fixture-1 TTL1000000us/max2000000us\n'
                 'and watchdog100us/max200us unchanged. Original VECTOR_1 signed windows\n'
                 'are not renewed. No heartbeat/alive/JSON flag is health evidence.\n\n'
                 'Readiness is allowed only after proven activation, trusted audit, independent\n'
                 'observer and complete fresh functional health. Only then register immutable\n'
                 'header/original atomically, authenticate actual audit LOGIN, require PASS\n'
                 'precheck and invoke S04 repeatable-read/read-only with frozen42-row equality.\n'
                 'Authorize bounded negative/namespace/semantic/ACL campaigns and two fresh\n'
                 'repetitions, not the remaining17 wrappers. Failed prerequisites deny READY\n'
                 'and invocation; authority itself proves no implementation or runtime result.\n\n'
                 'PRODUCTION_AUTHORITY=NO; MIGRATION_AUTHORITY=NO; FIELD_AUTHORITY=NO;\n'
                 'EXECUTION_AUTHORITY=NO; RECOVERY_AUTHORITY=NO. Canonical V043/fence and\n'
                 'V001-V042 remain unchanged; canonical V043 execution/promotion, shared DB,\n'
                 'production contact, production keys/policy and Room activation remain denied.\n\n'
                 'Exact user-authorized scope and provenance: [accepted decision](../evidence/'
                 'package-0090-authorized-test-activation-native-health-s04/accepted-test-decision.json).\n')
        path.write_text(text, encoding='utf-8', newline='\n')


if __name__ == '__main__':
    adopt()
