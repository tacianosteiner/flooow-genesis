"""Complete retained TEST ONLY evidence and reference codec. No SQL execution."""
import copy
import hashlib
import json
from pathlib import Path
import struct
import unicodedata
import uuid

import package_0090_policy_fixture as policy

ROOT = policy.ROOT
OUTPUT = ROOT / 'docs/evidence/PACKAGE-0090-G3F-3B-EVIDENCE-FIXTURE-001.json'
GOLDENS = ROOT / 'docs/evidence/PACKAGE-0090-G3F-3B-CODEC-GOLDENS.json'
ML = 'marketplace-economic.order-source'
OMIE = 'marketplace-economic.omie-transaction-evidence.reacquisition-v3'
INSTANT = '1970-01-01T00:00:00.000001Z'
LOCAL = '1970-01-01T00:00:00.000001'


def uid(n):
    return str(uuid.UUID(int=n))


def text(value):
    if not isinstance(value, str) or unicodedata.normalize('NFC', value) != value:
        raise ValueError('Text must already be NFC')
    return value.encode('utf-8', errors='strict')


def frozen_text(value):
    raw = text(value)
    return struct.pack('>I', len(raw)) + raw


def nullable_frozen_text(value):
    return (frozen_text('NULL') + struct.pack('>I', 0) if value is None else
            frozen_text('PRESENT') + frozen_text(value))


def frame(domain, values):
    raw = text(domain)
    return (struct.pack('>I', len(raw)) + raw + struct.pack('>H', len(values)) +
            b''.join(struct.pack('>HI', tag, len(payload)) + payload
                     for tag, payload in enumerate(values, 1)))


def present(raw):
    return b'\x01' + raw


def decode_frame(data, domain, count):
    pos = 0
    def take(n):
        nonlocal pos
        if n > len(data)-pos: raise ValueError('Truncated frame')
        value = data[pos:pos+n]; pos += n; return value
    def number(fmt): return struct.unpack(fmt, take(struct.calcsize(fmt)))[0]
    if take(number('>I')) != text(domain) or number('>H') != count:
        raise ValueError('Domain/count mismatch')
    values = []
    for tag in range(1,count+1):
        if number('>H') != tag: raise ValueError('Tag/order mismatch')
        payload = take(number('>I'))
        if not payload or payload[0] != 1: raise ValueError('Required field null')
        values.append(payload[1:])
    if pos != len(data): raise ValueError('Trailing frame bytes')
    return values


def validate_binding(raw, manifest, expected_policy):
    """Fixture semantic checks are separate from raw encoder-only mutation tests."""
    values = decode_frame(raw, 'FLOOOW/OFFLINE-FIELD-PROOF/BINDING/V1', 38)
    uuid_tags = (2,3,4,5,6,8,9,13,14,15,21,22,23,24,25,26,27,28)
    for tag in uuid_tags:
        if len(values[tag-1]) != 16 or not any(values[tag-1]): raise ValueError('Invalid UUID')
    if len({values[t-1] for t in uuid_tags}) != len(uuid_tags): raise ValueError('Duplicate fixture identity')
    for tag in (1,7,12):
        if values[tag-1] != struct.pack('>I',1): raise ValueError('Unsupported fixture version')
    for tag in (10,11,35):
        if len(values[tag-1]) != 32: raise ValueError('Invalid digest width')
    digest = hashlib.sha256(manifest).digest()
    if values[9] != digest or values[10] != digest or values[34] != hashlib.sha256(expected_policy).digest():
        raise ValueError('Retained manifest/policy hash mismatch')
    fields = []; pos = 0
    while pos < len(manifest):
        if len(manifest)-pos < 4: raise ValueError('Frozen manifest truncated')
        length = struct.unpack('>I',manifest[pos:pos+4])[0]; pos += 4
        if length > len(manifest)-pos: raise ValueError('Frozen manifest length')
        value = manifest[pos:pos+length].decode('utf-8',errors='strict'); pos += length
        if not value or text(value) != manifest[pos-length:pos]: raise ValueError('Frozen text malformed')
        fields.append(value)
    if len(fields) != 23 or fields.pop(0) != 'FLOOOW:S2A:APPROVAL-MANIFEST:1':
        raise ValueError('Frozen manifest schema')
    for binding_tag, manifest_index in ((9,1),(8,2),(13,3),(14,4),(15,7),(25,20)):
        if values[binding_tag-1] != uuid.UUID(fields[manifest_index]).bytes:
            raise ValueError('Manifest/header identity mismatch')
    for binding_tag, manifest_index in ((16,5),(17,6),(18,8),(19,18),(20,19)):
        if values[binding_tag-1] != text(fields[manifest_index]): raise ValueError('Manifest/header text mismatch')
    for tag in (16,17,18,19,20,33,34,36,37,38):
        decoded = values[tag-1].decode('utf-8',errors='strict')
        if not decoded or text(decoded) != values[tag-1]: raise ValueError('Malformed header text')
    if [values[t-1] for t in (33,34,36,37,38)] != [text(s) for s in ('0090-v1','fixture-1','1','1','1')]:
        raise ValueError('Unexpected fixture contract')
    if [values[t-1] for t in (29,30,31)] != [struct.pack('>q',n) for n in (1,1,1000001)]:
        raise ValueError('Invalid fixture window')
    if values[31] != slots([(1,101,'v'),(2,102,'i'),(3,103,'e'),(4,104,'a')]):
        raise ValueError('Invalid fixture slots')
    return fields


def retained_fixture(source='order-1'):
    org = uid(6)
    progress = []
    pages = []
    for conn, capability, marker in ((uid(8), ML, 8), (uid(9), OMIE, 9)):
        progress.append(dict(organization_id=org, connection_id=conn, capability=capability,
                             progress_version=2, progress_envelope=None, exhausted=True,
                             last_observed_at=INSTANT, updated_at=INSTANT))
        pages.append(dict(organization_id=org, connection_id=conn, capability=capability,
                          input_progress_version=1, page_commit_key=f'{marker:064x}', record_count=1,
                          exhausted=True, observed_at=INSTANT, committed_at=INSTANT))
    key = dict(organization_id=org, connection_id=uid(9), capability=OMIE,
               input_progress_version=1, record_ordinal=0)
    v3 = {**key, **dict.fromkeys((
        'source_order_origin', 'provider_modified_local', 'source_cancelled', 'source_cancelled_local',
        'source_invoiced', 'source_invoiced_local', 'source_authorized', 'source_denied', 'source_returned',
        'source_partially_returned', 'order_ended', 'order_ended_reason', 'order_ended_local',
        'order_discount_type', 'order_discount_percent', 'order_discount_amount', 'merchandise_amount',
        'discount_amount', 'deduction_amount', 'freight_amount', 'insurance_amount', 'other_expense_amount',
        'marketplace_fee_amount', 'marketplace_shipping_amount')),
        'provider_created_local': LOCAL, 'additional_order_totals': {},
        'semantic_fingerprint_version': 1, 'source_evidence_semantic_fingerprint': f'{1:064x}'}
    return {
        'fixture_id': 'PACKAGE-0090-G3F-3B-EVIDENCE-FIXTURE-001',
        'scope': 'TEST_GOLDEN_REHEARSAL_ONLY', 'production_data': False, 'protected_data': False,
        'live_data_retrieval': False,
        'provenance': 'FLOOOW_TECHNICAL_RETAINED_EVIDENCE_FIXTURE_2026-10-03',
        'source_semantic_hash_claim': 'SYNTHETIC_TOKEN_ONLY_NOT_PROVIDER_SEMANTIC_PROOF',
        'tables': {
            'integration_organization': [dict(organization_id=org, status='ACTIVE', created_at=INSTANT, updated_at=INSTANT)],
            'integration_connection': [dict(organization_id=org, connection_id=uid(n),
                provider_key=provider, credential_kind=kind, status='ACTIVE', binding_version=1,
                created_at=INSTANT, updated_at=INSTANT) for n, provider, kind in
                ((8, 'mercado-livre', 'OAUTH2_AUTHORIZATION_CODE'), (9, 'omie', 'STATIC_API_CREDENTIAL'))],
            'integration_connector_progress': progress, 'integration_connector_page_commit': pages,
            'integration_mercado_livre_order_source_observation': [dict(organization_id=org,
                connection_id=uid(8), capability=ML, input_progress_version=1, record_ordinal=0,
                external_order_ref='order-1', provider_status='paid', date_created=INSTANT,
                date_last_updated=INSTANT, date_closed=None, currency='BRL', total_amount='1.000000',
                paid_amount=None, pack_ref=None, shipping_ref=None, observed_at=INSTANT)],
            'marketplace_order_identity_registry': [dict(organization_id=org, marketplace_key='mercado-livre',
                external_order_id='order-1', marketplace_order_id=uid(10), currency='BRL', allocated_at=INSTANT,
                first_source_connection_id=uid(8), first_source_capability=ML,
                first_source_input_progress_version=1, first_source_record_ordinal=0)],
            'marketplace_order_occurrence_source_promotion': [dict(organization_id=org, source_connection_id=uid(8),
                source_capability=ML, source_input_progress_version=1, source_record_ordinal=0,
                marketplace_order_id=uid(10), outcome='PROMOTED', promoted_at=INSTANT)],
            'integration_omie_transaction_evidence': [{**key, 'source_order_ref': source,
                'source_integration_ref': 'integration-1', 'source_customer_order_ref': None, 'occurred_at': None,
                'source_status': None, 'currency': 'BRL', 'total_amount': None, 'product_refs': [],
                'observed_at': INSTANT, 'source_fingerprint': 'fixture-source-1'}],
            'integration_omie_transaction_evidence_v3': [v3],
        },
    }


def select_evidence(fixture, source='order-1'):
    """Closed one-row rehearsal projection of every V041 selection/integrity check."""
    tables = fixture['tables']
    expected_counts = {name: (2 if name in ('integration_connection', 'integration_connector_progress',
                                          'integration_connector_page_commit') else 1) for name in tables}
    expected_tables = set(retained_fixture()['tables'])
    if set(tables) != expected_tables or any(len(tables[n]) != expected_counts[n] for n in tables):
        raise ValueError('Unexpected, absent, competing or duplicate rows')
    def single(name, **keys):
        found = [r for r in tables[name] if all(r.get(k) == v for k, v in keys.items())]
        if len(found) != 1:
            raise ValueError('Missing/ambiguous joined row: ' + name)
        return found[0]
    org, ml_conn, omie_conn, order = uid(6), uid(8), uid(9), uid(10)
    single('integration_organization', organization_id=org)
    for conn in (ml_conn, omie_conn):
        single('integration_connection', organization_id=org, connection_id=conn)
    p = single('marketplace_order_occurrence_source_promotion', organization_id=org,
               marketplace_order_id=order, source_connection_id=ml_conn, source_capability=ML)
    if p['outcome'] not in ('PROMOTED', 'DUPLICATE'):
        raise ValueError('No admissible promotion')
    ml = single('integration_mercado_livre_order_source_observation', organization_id=org, connection_id=ml_conn,
                capability=ML, input_progress_version=p['source_input_progress_version'],
                record_ordinal=p['source_record_ordinal'])
    registry = single('marketplace_order_identity_registry', organization_id=org, marketplace_order_id=order)
    if (registry['marketplace_key'] != 'mercado-livre' or ml['external_order_ref'] != registry['external_order_id']
            or ml['currency'] != registry['currency']):
        raise ValueError('ML integrity failure')
    if (registry['first_source_connection_id'], registry['first_source_capability'],
        registry['first_source_input_progress_version'], registry['first_source_record_ordinal']) != (
            ml_conn, ML, ml['input_progress_version'], ml['record_ordinal']):
        raise ValueError('Frozen registry-source trigger mismatch')
    b = single('integration_omie_transaction_evidence', organization_id=org, connection_id=omie_conn,
               capability=OMIE, source_order_ref=source)
    key = {k: b[k] for k in ('organization_id', 'connection_id', 'capability', 'input_progress_version', 'record_ordinal')}
    v3 = single('integration_omie_transaction_evidence_v3', **key)
    for row, capability in ((ml, ML), (b, OMIE)):
        page_key = {k: row[k] for k in ('organization_id', 'connection_id', 'input_progress_version')}
        page = single('integration_connector_page_commit', capability=capability, **page_key)
        progress = single('integration_connector_progress', organization_id=org,
                          connection_id=row['connection_id'], capability=capability)
        if not (0 <= row['record_ordinal'] < page['record_count'] == 1 and
                row['input_progress_version'] < progress['progress_version']):
            raise ValueError('Count/ordinal/progress failure')
        if not (progress['progress_version'] > 0 and progress['exhausted'] is True and
                progress['progress_envelope'] is None and progress['last_observed_at'] is not None):
            raise ValueError('Frozen progress shape failure')
        if len(bytes.fromhex(page['page_commit_key'])) != 32:
            raise ValueError('Frozen page key shape failure')
    import re
    if (v3['semantic_fingerprint_version'] != 1 or
            not re.fullmatch('[0-9a-f]{64}', v3['source_evidence_semantic_fingerprint']) or
            (v3['provider_created_local'] is None and v3['provider_modified_local'] is None) or
            (v3['provider_created_local'] is not None and v3['provider_modified_local'] is not None and
             v3['provider_modified_local'] < v3['provider_created_local'])):
        raise ValueError('V3 fingerprint/revision integrity failure')
    if b['source_integration_ref'] != 'integration-1' or (b['currency'] is not None and b['currency'] != ml['currency']):
        raise ValueError('Omie scope/currency mismatch')
    revision = v3['provider_modified_local'] or v3['provider_created_local']
    return p, registry, b, v3, revision


def evidence_preimage(fixture, source='order-1'):
    p, registry, b, v3, revision = select_evidence(fixture, source)
    # Exact V041 concatenation: nullable text has TWO frozen frames.
    parts = ['FLOOOW:S2A:EVIDENCE-BINDING:1', uid(6), uid(10), uid(8), ML,
             str(p['source_input_progress_version']), str(p['source_record_ordinal']),
             registry['marketplace_key'], registry['external_order_id'], registry['currency'], p['outcome'],
             uid(9), OMIE, str(b['input_progress_version']), str(b['record_ordinal']), source]
    return (b''.join(frozen_text(v) for v in parts) + nullable_frozen_text(b['source_integration_ref']) +
            nullable_frozen_text(b['currency']) + frozen_text(str(v3['semantic_fingerprint_version'])) +
            frozen_text(v3['source_evidence_semantic_fingerprint']) + frozen_text(revision))


def manifest_fields(evidence_digest, source='order-1', correlation=15):
    return ['1', uid(7), uid(6), uid(8), uid(9), source, 'integration-1', uid(10),
            'TRANSACTION_IDENTITY_DECISION_WRITE', uid(19), uid(20), INSTANT,
            '1970-01-01T00:00:01.000001Z', uid(21), uid(22), 'PROTECTED_TTY_ONE_TIME',
            uid(23), 'SEPARATE_APPROVAL_REQUIRED', 'reason', 'fixture', uid(correlation), evidence_digest]


def slots(records):
    if (len(records) != 4 or sorted(r[0] for r in records) != [1, 2, 3, 4] or
            len({r[1] for r in records}) != 4 or len({r[2] for r in records}) != 4 or
            any(type(r[1]) is not int or not 0 < r[1] < 2**32 or not r[2] for r in records)):
        raise ValueError('Invalid slot set')
    values = [struct.pack('>BI', purpose, oid) + struct.pack('>I', len(text(name))) + text(name)
              for purpose, oid, name in sorted(records)]
    return struct.pack('>I', 4) + b''.join(struct.pack('>I', len(v)) + v for v in values)


def binding_payloads(manifest_hash, policy_hash, source='order-1', correlation=15, slot_order=None):
    u32 = lambda n: struct.pack('>I', n)
    ident = lambda n: uuid.UUID(int=n).bytes
    raw = [u32(1)] + [ident(n) for n in range(1, 6)] + [u32(1), ident(6), ident(7),
           manifest_hash, manifest_hash, u32(1), ident(8), ident(9), ident(10), text(source),
           text('integration-1'), text('TRANSACTION_IDENTITY_DECISION_WRITE'), text('reason'), text('fixture')]
    raw += [ident(n) for n in (11, 12, 13, 14, correlation, 16, 17, 18)]
    records = [(1, 101, 'v'), (2, 102, 'i'), (3, 103, 'e'), (4, 104, 'a')]
    if slot_order:
        records = [records[i-1] for i in slot_order]
    raw += [struct.pack('>q', n) for n in (1, 1, 1000001)]
    raw += [slots(records), text('0090-v1'), text('fixture-1'), policy_hash] + [text('1')]*3
    assert len(raw) == 38
    return [present(v) for v in raw]


def digest_record(raw):
    return {'hex': raw.hex(), 'sha256': hashlib.sha256(raw).hexdigest(), 'byte_count': len(raw)}


def derive(vector, source='order-1', correlation=15):
    fixture = retained_fixture(source)
    preimage = evidence_preimage(fixture, source)
    evidence = hashlib.sha256(preimage).hexdigest()
    fields = manifest_fields(evidence, source, correlation)
    manifest = frozen_text('FLOOOW:S2A:APPROVAL-MANIFEST:1') + b''.join(frozen_text(f) for f in fields)
    manifest_hash = hashlib.sha256(manifest).digest()
    pol = bytes.fromhex(policy.approved_fixture()['canonical_policy_hex'])
    payloads = binding_payloads(manifest_hash, hashlib.sha256(pol).digest(), source, correlation,
                                [4, 2, 1, 3] if vector == 'VECTOR_2' else None)
    binding = frame('FLOOOW/OFFLINE-FIELD-PROOF/BINDING/V1', payloads)
    result = dict(vector=vector, scope='TEST_GOLDEN_REHEARSAL_ONLY', signed_acceptance_proof=False,
                  retained_evidence=fixture, evidence_preimage=digest_record(preimage),
                  evidence_fingerprint=evidence, manifest_fields=fields,
                  manifest=digest_record(manifest), binding=digest_record(binding))
    if vector == 'VECTOR_3':
        # Encoder-only mutation is distinct from the semantically coherent alternate.
        original = derive('VECTOR_1')
        original_manifest = bytes.fromhex(original['manifest']['sha256'])
        mutated = frame('FLOOOW/OFFLINE-FIELD-PROOF/BINDING/V1',
                        binding_payloads(original_manifest, hashlib.sha256(pol).digest(), correlation=999))
        result['encoder_only_mutation'] = digest_record(mutated)
        result['encoder_only_semantic_validation'] = 'REJECT_UNCHANGED_MANIFEST_CORRELATION'
        result['alternate_signature'] = 'NOT_CREATED_NOT_SIGNATURE_PROOF'
    return result


def goldens():
    return dict(scope='TEST_GOLDEN_REHEARSAL_ONLY', production_data=False, protected_data=False,
                sql_execution_parity='HOLD_NOT_EXECUTED',
                policy=policy.approved_fixture(),
                vectors=[derive('VECTOR_1'), derive('VECTOR_2', source='caf\u00e9'),
                         derive('VECTOR_3', correlation=999)])


if __name__ == '__main__':
    OUTPUT.write_text(json.dumps(retained_fixture(), indent=2) + '\n', encoding='utf-8')
    data = goldens()
    GOLDENS.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    for vector in data['vectors']:
        print(vector['vector'] + '_BINDING_SHA256=' + vector['binding']['sha256'])
