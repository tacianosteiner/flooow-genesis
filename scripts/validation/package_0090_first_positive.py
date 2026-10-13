"""Original TEST_ONLY signed input preparation and first-path precheck.

Native vector success never fabricates participant health, READY or ACTIVE.
The selected authentic wrapper is not called unless its governed precheck passes.
"""
import hashlib
import json
from pathlib import Path
import struct
import uuid
import zlib
import package_0090_source_closure as q
from package_0090_active_foundation import quote

ROOT = q.ROOT
DOMAIN = b'FLOOOW/OFFLINE-FIELD-PROOF/EXPECTED-SIGNED-ATTESTATION/V1'


def frame(domain, values):
    data = struct.pack('>I', len(domain)) + domain + struct.pack('>H', len(values))
    for tag, value in enumerate(values, 1):
        payload = b'\x01' + value
        data += struct.pack('>HI', tag, len(payload)) + payload
    return data


def frozen(values):
    return b''.join(struct.pack('>I', len(v.encode())) + v.encode() for v in values)


def decode_binding(data):
    from importlib.util import spec_from_file_location, module_from_spec
    path = ROOT / 'scripts/validation/package_0090_full_qualification/codec.py'
    spec = spec_from_file_location('approved_binding_codec', path); codec = module_from_spec(spec); spec.loader.exec_module(codec)
    offset = 4 + int.from_bytes(data[:4], 'big') + 2
    values = {}
    for tag, name in enumerate(codec.FIELDS, 1):
        actual, length = struct.unpack('>HI', data[offset:offset + 6]); offset += 6
        q.require(actual == tag and data[offset] == 1, 'Exact golden binding tags required')
        v = data[offset + 1:offset + length]; offset += length
        if name in codec.HASH or name == 'identity_slots':
            values[name] = '\\x' + v.hex()
        elif name in codec.VERSIONS:
            values[name] = int.from_bytes(v, 'big')
        elif name in codec.TIMES:
            micros = int.from_bytes(v, 'big', signed=True)
            import datetime
            values[name] = (datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc) + datetime.timedelta(microseconds=micros)).isoformat(timespec='microseconds').replace('+00:00', 'Z')
        elif name.endswith('_id'):
            values[name] = str(uuid.UUID(bytes=v))
        else:
            values[name] = v.decode('utf-8')
    q.require(offset == len(data), 'No trailing binding bytes')
    return values, codec


def exact_fingerprint(header, codec):
    import datetime
    values = []
    for name in codec.FIELDS:
        if name in codec.TIMES:
            instant = datetime.datetime.fromisoformat(header[name].replace('Z', '+00:00'))
            delta = instant - datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)
            micros = delta.days * 86400000000 + delta.seconds * 1000000 + delta.microseconds
            values.append(struct.pack('>q', micros))
        else:
            values.append(codec.typed(name, header[name]))
    return q.sha(frame(b'FLOOOW/OFFLINE-FIELD-PROOF/BINDING/V1', values))


def save(folder, name, data):
    (folder / name).write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')


def prepare(sql, run, container, folder, record, fixture):
    golden_file = ROOT / 'docs/evidence/PACKAGE-0090-G3F-3B-CODEC-GOLDENS.json'
    golden = json.loads(golden_file.read_text())['vectors'][0]
    header, codec = decode_binding(bytes.fromhex(golden['binding']['hex']))
    q.require(exact_fingerprint(header, codec) == golden['binding']['sha256'], 'Independent binding decoder/encoder parity')
    roles = [(int(x['role']['oid']), x['role']['rolname']) for x in record['service_identities']]
    header['identity_slots'] = '\\x' + codec.slots(roles).hex()
    header['plan_fingerprint'] = '\\x' + exact_fingerprint(header, codec)
    manifest = bytes.fromhex(golden['manifest']['hex'])
    q.require(q.sha(manifest) == golden['manifest']['sha256'], 'Original approved manifest bytes required')
    header['canonical_manifest_bytes'] = '\\x' + manifest.hex()
    expected_history = []
    for rank, path in enumerate(sorted(p for p in q.MIGRATIONS.glob('V*.sql') if int(p.name.split('__')[0][1:]) <= 42), 1):
        b = q.git('show', 'HEAD:' + path.relative_to(ROOT).as_posix()); crc = 0
        for line in b.decode('utf-8-sig').splitlines():
            crc = zlib.crc32(line.encode(), crc)
        if crc >= 2**31:
            crc -= 2**32
        expected_history.append({'installed_rank': rank, 'version': path.name.split('__')[0][1:], 'type': 'SQL', 'script': path.name, 'checksum': crc, 'success': True})
    expectation = {'wrapper': 'public.offline_read_history(uuid,bytea,uuid,text)', 'caller': 'test_0090_audit',
                   'transaction': 'REPEATABLE READ READ ONLY', 'return_type': 'TABLE(installed_rank int4,version text,type text,script text,checksum int4,success bool)',
                   'output_rows': expected_history, 'durable_effects': [], 'audit_writes': [], 'version_increments': [], 'consumption': 'NONE',
                   'selection': 'Smallest auditor R boundary; complete history read, no later effect/admission/possession authority',
                   'required': ['immutable header and original tuple', 'authentic four live slots', 'approved effective policy', 'validated READY/functional watchdog', 'exact path ACL'],
                   'provenance': ['SPEC-0090 sections3,14,21.1,25', 'canonical V043 offline_read_history body']}
    save(folder, 'first-positive-expectation.json', expectation)
    private = '/run/test-only-0090-first-positive'
    try:
        run(['docker', 'exec', '--user', '0', container, 'mkdir', '-m', '0700', private])
        for name in ['original', 'wrong']:
            run(['docker', 'exec', '--user', '0', container, 'openssl', 'genpkey', '-algorithm', 'ED25519', '-out', private + '/' + name + '.pem'])
            run(['docker', 'exec', '--user', '0', container, 'chmod', '0600', private + '/' + name + '.pem'])
            run(['docker', 'exec', '--user', '0', container, 'openssl', 'pkey', '-in', private + '/' + name + '.pem', '-pubout', '-outform', 'DER', '-out', private + '/' + name + '.der'])
        spki = run(['docker', 'exec', '--user', '0', container, 'cat', private + '/original.der'])
        wrong_spki = run(['docker', 'exec', '--user', '0', container, 'cat', private + '/wrong.der'])
        # Explicit typed TEST identity, deterministic recipe derivation; not an
        # inference that a governance UUID denotes a signer key.
        key_id = str(uuid.uuid5(uuid.UUID(header['deployment_id']),
            'TEST_ONLY_FIRST_POSITIVE_SIGNER|a82bb8ccf352ba89510f52b3d9c3f1ecc3dee7d8|'
            + q.SOURCE_HASH + '|' + q.sha(Path(__file__).read_bytes())))
        preimage = frozen(['FLOOOW:S2A:APPROVAL-SIGNATURE:1', 'Ed25519', key_id, q.sha(spki), q.sha(manifest)])
        run(['docker', 'exec', '--user', '0', '-i', container, 'sh', '-c', 'umask 077; cat > "$1"', 'sh', private + '/preimage.bin'], data=preimage)
        run(['docker', 'exec', '--user', '0', container, 'openssl', 'pkeyutl', '-sign', '-inkey', private + '/original.pem', '-rawin', '-in', private + '/preimage.bin', '-out', private + '/signature.bin'])
        sig = run(['docker', 'exec', '--user', '0', container, 'cat', private + '/signature.bin'])
        commitment = frame(DOMAIN, [uuid.UUID(header['binding_id']).bytes, q.sha(manifest).encode(), b'Ed25519', uuid.UUID(key_id).bytes, q.sha(spki).encode(), sig])
        original = {'binding_id': header['binding_id'], 'manifest_digest': q.sha(manifest), 'algorithm_id': 'Ed25519', 'signer_key_id': key_id,
                    'signer_key_fingerprint': q.sha(spki), 'signature_bytes': '\\x' + sig.hex(), 'canonical_expected_attestation': '\\x' + commitment.hex(), 'commitment_digest': '\\x' + q.sha(commitment)}
        # Freeze public inputs/expectation before any crypto validation or registration.
        save(folder, 'registered-fixture-manifest.json', {'scope': 'TEST_ONLY_PREPARED_UNREGISTERED', 'production_authority': False,
             'source_hash': q.SOURCE_HASH, 'golden_git_source': golden_file.relative_to(ROOT).as_posix(), 'golden_working_sha256': q.sha(golden_file.read_bytes()),
             'header': header, 'original_expected_tuple': original, 'spki_hex': spki.hex(), 'signature_preimage_hex': preimage.hex(),
             'key_id_derivation': 'UUIDv5(deployment UUID, typed TEST case + fixed input HEAD + V043 hash + generator hash); private material remains random',
             'time_boundary': 'Original 1970 golden window preserved, not extended or treated as current authorization', 'fixture_private_material': 'NOT_EXPORTED'})
        def case(name, passed, details, group='FIRST_PATH_PREPARATION'):
            record['cases'].append({'name': name, 'passed': passed, 'details': details, 'group': group})
            q.require(passed, 'First path preparation failed: ' + name)
        for name, public, signature_, expected in [('original_signature_valid', spki, sig, 't'),
                                                  ('signature_bit_flip_denied', spki, bytes([sig[0]^1]) + sig[1:], 'f'),
                                                  ('wrong_key_denied', wrong_spki, sig, 'f')]:
            result = sql("SELECT offline_crypto.canonical_spki_ed25519_verify(decode('" + public.hex() + "','hex'),decode('" + preimage.hex() + "','hex'),decode('" + signature_.hex() + "','hex'));").stdout.decode().strip()
            case(name, result == expected, {'expected': expected, 'observed': result}, 'ORIGINAL_CRYPTO')
        case('signature_NULL_preserved', sql("SELECT offline_crypto.canonical_spki_ed25519_verify(NULL,''::bytea,NULL) IS NULL;").stdout.strip() == b't', 'SQL NULL, not FALSE', 'ORIGINAL_CRYPTO')
        permissions = run(['docker', 'exec', '--user', '0', container, 'stat', '-c', '%u:%a', private + '/original.pem', private + '/wrong.pem']).decode().splitlines()
        case('private_custody_root_only', permissions == ['0:600', '0:600'], permissions, 'KEY_CUSTODY')
        denied_key = q.command(['docker', 'exec', '--user', 'postgres', container, 'cat', private + '/original.pem'], check=False)
        case('backend_OS_user_cannot_read_private', denied_key.returncode != 0 and not denied_key.stdout,
             {'denied': denied_key.returncode != 0, 'private_bytes_returned': bool(denied_key.stdout)}, 'KEY_CUSTODY')
        # Header + independently supplied original tuple register atomically; no ACTIVE promotion.
        registration = sql('BEGIN; INSERT INTO public.offline_binding_header(' + ','.join(header) + ') VALUES(' + ','.join(quote(v) for v in header.values()) + ');'
            + 'INSERT INTO public.offline_expected_signed_attestation(' + ','.join(original) + ') VALUES(' + ','.join(quote(v) for v in original.values()) + ');'
            + 'INSERT INTO public.offline_binding_lifecycle(binding_id,state,lock_token) VALUES(' + quote(header['binding_id']) + ",'REGISTERED',0); COMMIT;", check=False)
        # Readiness FK is a real prerequisite. Do not fill NOT_READY/READY rows
        # with unapproved activation metadata merely to make registration pass.
        case('registration_denied_without_readiness', registration.returncode != 0 and '23503' in registration.stderr.decode()
             and 'offline_binding_header_fk1' in registration.stderr.decode(), registration.stderr.decode())
        observed = json.loads(sql("SELECT json_build_object('header_count',(SELECT count(*) FROM offline_binding_header),'original_count',(SELECT count(*) FROM offline_expected_signed_attestation),'lifecycle_count',(SELECT count(*) FROM offline_binding_lifecycle));").stdout)
        case('registration_failure_atomic_zero_rows', all(value == 0 for value in observed.values()), observed)
        clock = json.loads(sql("SELECT json_build_object('database_now',clock_timestamp(),'finite',isfinite(clock_timestamp()),'policy_rows',(SELECT count(*) FROM offline_deadline_policy),'readiness_rows',(SELECT count(*) FROM offline_readiness));").stdout)
        save(folder, 'active-fixture-runtime.json', {'registration_state_observation': observed, 'database_clock': clock,
            'policy_activation': 'NOT_PROVISIONED_NO_INDEPENDENT_ACTIVATION_APPROVAL', 'native_health': 'NOT_PROVEN', 'scope': 'TEST_ONLY_NOT_ACTIVE'})
        precheck = {'status': 'FAIL', 'immutable_header_and_original': False, 'authentic_login_prepared': True,
            'policy_active': False, 'native_functional_participant_health': False, 'ready': False,
            'reasons': ['SPEC25 requires independently approved activation instant and durable ADMIN audit; golden approval does not supply them',
                        'Native health design still specifies seven managed participants plus guard/root; actual complete enrollment/progress evidence absent'],
            'wrapper_invoked': False}
        save(folder, 'first-positive-observation.json', {'precheck': precheck, 'executed': False, 'pass': False, 'expectation_frozen': True})
        record['first_positive'] = {'selected': expectation['wrapper'], 'precheck': 'FAIL', 'executed': False, 'pass': False}
        case('failed_precheck_prevents_wrapper', not precheck['wrapper_invoked'] and clock['readiness_rows'] == 0, precheck)
    finally:
        # Names are fixed paths beneath the newly created private directory; no external target.
        run(['docker', 'exec', '--user', '0', container, 'rm', '-f', private + '/original.pem', private + '/wrong.pem', private + '/original.der', private + '/wrong.der', private + '/preimage.bin', private + '/signature.bin'])
        erased = q.command(['docker', 'exec', '--user', '0', container, 'sh', '-c', 'test ! -e "$1/original.pem" && test ! -e "$1/wrong.pem"', 'sh', private], check=False).returncode == 0
        save(folder, 'key-custody.json', {'owner': 'container root', 'directory_mode': '0700', 'private_key_mode': '0600',
             'processes_seeing_private': ['trusted OpenSSL generation/signing process'], 'PostgreSQL_sees_private': False,
             'private_material_exported': False, 'erasure_verified': erased, 'production_custody_claim': False,
             'scope': 'TEST_ONLY_ED25519_CUSTODY_NOT_COMPLETE_PREFLIGHT_MAC_KEY_LIFECYCLE'})
        q.require(erased, 'Private fixture key erasure failed')
