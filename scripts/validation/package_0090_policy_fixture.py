"""TEST/REHEARSAL ONLY. Offline approved fixture codec; never provisions SQL."""
import hashlib
import json
from pathlib import Path
import struct
import unicodedata

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / 'docs/evidence/PACKAGE-0090-G3F-3B-FIXTURE-001.json'
DOMAIN = b'FLOOOW/OFFLINE-FIELD-PROOF/DEADLINE-POLICY/V1'
NAMES = ('TRANSACTION_TIMEOUT', 'STATEMENT_TIMEOUT', 'IDLE_IN_TRANSACTION_TIMEOUT',
         'LOCK_TIMEOUT', 'ATTEMPT_VALIDITY', 'EXECUTION_VALIDITY', 'BINDING_VALIDITY',
         'ADMISSION_VALIDITY', 'DELIVERY_OPERATION_WINDOW', 'READ_TRANSACTION_TIMEOUT',
         'WATCHDOG_ENFORCEMENT_INTERVAL', 'WATCHDOG_HEALTH_MAX_AGE',
         'DELIVERY_LOCAL_SAFETY_MARGIN', 'PREFLIGHT_RECEIPT_TTL')


def validate(version, values):
    if (not isinstance(version, str) or not version or
            unicodedata.normalize('NFC', version) != version or
            any(ord(c) < 32 or ord(c) == 127 for c in version)):
        raise ValueError('Invalid version')
    version.encode('utf-8', errors='strict')
    if len(values) != 28 or any(type(v) is not int or not 0 < v <= 2**63-1 for v in values):
        raise ValueError('Expected 28 positive int8 microsecond values')
    if any(values[i] > values[i+1] for i in range(0, 28, 2)):
        raise ValueError('Actual exceeds approved maximum')
    actual = values[::2]
    # SPEC18 duration constraints; live canonical windows remain runtime guards.
    if not (all(actual[i] <= values[1] for i in (1, 2, 3))
            and actual[4] <= actual[6] and actual[5] <= actual[6]
            and actual[7] <= min(actual[4], actual[5], actual[6])
            and actual[8] <= min(actual[5], actual[6]) and actual[12] < actual[8]):
        raise ValueError('Invalid deadline nesting or delivery margin')


def encode(version, values):
    validate(version, values)
    payloads = [b'\x01' + version.encode('utf-8')]
    payloads += [b'\x01' + struct.pack('>q', v) for v in values]
    return (struct.pack('>I', len(DOMAIN)) + DOMAIN + struct.pack('>H', 29) +
            b''.join(struct.pack('>HI', tag, len(p)) + p
                     for tag, p in enumerate(payloads, 1)))


def decode(data):
    pos = 0
    def take(n):
        nonlocal pos
        if n > len(data) - pos:
            raise ValueError('Truncated frame')
        value = data[pos:pos+n]
        pos += n
        return value
    def number(fmt):
        return struct.unpack(fmt, take(struct.calcsize(fmt)))[0]
    if take(number('>I')) != DOMAIN or number('>H') != 29:
        raise ValueError('Wrong domain or field count')
    fields = []
    for expected in range(1, 30):
        if number('>H') != expected:
            raise ValueError('Unknown, omitted, duplicate or reordered tag')
        payload = take(number('>I'))
        if not payload or payload[0] != 1:
            raise ValueError('Required field absent')
        fields.append(payload[1:])
    if pos != len(data) or any(len(p) != 8 for p in fields[1:]):
        raise ValueError('Trailing bytes or invalid int8 width')
    version = fields[0].decode('utf-8', errors='strict')
    values = [struct.unpack('>q', p)[0] for p in fields[1:]]
    validate(version, values)
    if encode(version, values) != data:
        raise ValueError('Noncanonical frame')
    return version, values


def approved_fixture():
    values = [n for name in NAMES for n in
              ((1, 2) if name == 'DELIVERY_LOCAL_SAFETY_MARGIN' else
               (100, 200) if name.startswith('WATCHDOG_') else (1000000, 2000000))]
    encoded = encode('fixture-1', values)
    return {
        'fixture_id': 'PACKAGE-0090-G3F-3B-FIXTURE-001',
        'scope': 'TEST_GOLDEN_REHEARSAL_ONLY',
        'production_policy_approval': False, 'production_policy_provisioning': False,
        'approval_provenance': 'FLOOOW_TECHNICAL_FIXTURE_APPROVAL_2026-10-03',
        'policy_version': 'fixture-1', 'canonical_policy_field_count': 29,
        'fields': [{'tag': 1, 'name': 'policy_version', 'type': 'text', 'value': 'fixture-1'}] +
                  [{'tag': 2 + i, 'name': NAMES[i//2] + ('_ACTUAL_US' if i%2 == 0 else '_APPROVED_MAX_US'),
                    'type': 'int8_microseconds', 'value': v} for i, v in enumerate(values)],
        'canonical_policy_hex': encoded.hex(),
        'canonical_policy_sha256': hashlib.sha256(encoded).hexdigest(),
        'dependent_binding_manifest_receipt_goldens': 'HOLD_NOT_GENERATED',
        'signature_or_production_acceptance_proof': False,
    }


if __name__ == '__main__':
    fixture = approved_fixture()
    FIXTURE.write_text(json.dumps(fixture, indent=2) + '\n', encoding='utf-8')
    print('TEST_ONLY_POLICY_SHA256=' + fixture['canonical_policy_sha256'])
