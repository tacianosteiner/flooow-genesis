"""Independent logical-schema review; no frames sent and no runtime witness.

Checks structure from published design, not the previous producer verifier.
Actual observation provenance, atomic ledgers and native wire proof stay open.
"""
from pathlib import Path
import hashlib
import json

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
SOURCE = ROOT / 'docs/evidence/package-0090-g3f4-sql-runtime-witness/final-02'
TYPES = {'enrollment', 'identity_proof', 'generation_proof', 'heartbeat', 'progress',
         'completed_work_witness', 'approval_state', 'enforcement_state', 'quarantine', 'drain', 'recovery_observation'}

def validate(value, schema):
    if 'const' in schema:
        return type(value) is type(schema['const']) and value == schema['const']
    kind = schema['type']
    if kind == 'object':
        if type(value) is not dict or not set(schema.get('required', [])) <= value.keys():
            return False
        if schema.get('additionalProperties') is False and not value.keys() <= schema['properties'].keys():
            return False
        return all(validate(v, schema['properties'][k]) for k, v in value.items() if k in schema['properties'])
    if kind == 'integer':
        return type(value) is int and schema.get('minimum', value) <= value <= schema.get('maximum', value)
    if kind == 'boolean':
        return type(value) is bool
    if kind == 'string':
        return type(value) is str and len(value) >= schema.get('minLength', 0) and ('enum' not in schema or value in schema['enum'])
    raise ValueError('Unhandled schema type: ' + kind)

def sample(schema):
    if 'const' in schema:
        return schema['const']
    if schema['type'] == 'object':
        return {key: sample(schema['properties'][key]) for key in schema['required']}
    if schema['type'] == 'integer':
        return schema.get('minimum', 0)
    if schema['type'] == 'boolean':
        return False
    if schema['type'] == 'string':
        return schema.get('enum', ['TEST_ONLY_NONCANONICAL'])[0]
    raise ValueError('Unhandled schema type')

def main():
    files = ['FRAME-SCHEMA.json', 'PAYLOAD-SCHEMAS.json', 'RUNTIME-FRAME-CONTRACT.json']
    data = {name: (SOURCE / name).read_bytes() for name in files}
    envelope = json.loads(data['FRAME-SCHEMA.json'])
    payloads = json.loads(data['PAYLOAD-SCHEMAS.json'])
    frames = json.loads(data['RUNTIME-FRAME-CONTRACT.json'])['frames']
    assert set(payloads) == TYPES == {f['FRAME_TYPE'] for f in frames}
    results = []
    for frame in frames:
        name = frame['FRAME_TYPE']
        schema = payloads[name]
        assert set(frame['PAYLOAD_REQUIRED_FIELDS']) == set(schema['required'])
        assert set(frame['REQUIRED_FIELDS']) == set(envelope['required'])
        assert schema['additionalProperties'] is False and envelope['additionalProperties'] is False
        obj = sample(schema)
        assert validate(obj, schema)
        controls = []
        for field in schema['required']:
            missing = dict(obj)
            del missing[field]
            assert not validate(missing, schema)
            controls.append({'case': 'missing_required_field', 'field': field, 'denied': True})
        assert not validate({**obj, 'UNDECLARED': 'forbidden'}, schema)
        for field, field_schema in schema['properties'].items():
            if field_schema.get('type') == 'integer':
                assert not validate({**obj, field: True}, schema)
                controls.append({'case': 'boolean_is_not_integer', 'field': field, 'denied': True})
        results.append({'frame_type': name, 'producer': frame['PRODUCER'], 'consumer': frame['CONSUMER'],
                        'independent_verifier': frame['INDEPENDENT_VERIFIER'],
                        'envelope_field_types': {k: v.get('type', 'CONSTANT_'+type(v.get('const')).__name__) for k, v in envelope['properties'].items()},
                        'payload_field_types': {k: v.get('type', 'CONSTANT_'+type(v.get('const')).__name__) for k, v in schema['properties'].items()},
                        'required_field_structure_review': 'PASS_SCHEMA_ONLY', 'negative_structure_controls': controls,
                        'corroboration_obligation': frame['CORROBORATION_REQUIRED'],
                        'independent_runtime_verifier_complete': False,
                        'canonical_encoding_complete': False,
                        'open_encoding_obligations': ['Unicode normalization/rejection', 'surrogate rejection', 'duplicate-key rejection',
                                                     'bounded integer and string encoding', 'logical envelope/payload composition',
                                                     'unknown-version and frame-type denial', 'exact receipt/challenge channel binding'],
                        'runtime_frames_executed': False})
    output = {'scope': 'INDEPENDENT_DESIGN_STRUCTURE_REVIEW_NOT_RUNTIME_VERIFICATION',
              'source_hashes': {n: hashlib.sha256(b).hexdigest() for n, b in data.items()},
              'frame_type_n': 11, 'frame_required_structure_complete_n': 11,
              'frame_full_schema_encoding_complete_n': 0, 'frame_independent_runtime_verifier_complete_n': 0,
              'witness_field_mapping': 'PARTIAL_DESIGN_CONTEXT_ONLY_SQL_CLOSURE_BINDINGS_PENDING',
              'witness_corroboration': 'DESIGN_OBLIGATION_DEFINED_NO_RUNTIME_PROOF', 'results': results}
    (BASE / 'semantic-checkpoint/WITNESS-DESIGN-REVIEW.json').write_text(json.dumps(output, indent=2, sort_keys=True) + '\n', encoding='utf-8', newline='\n')
    print('FRAME_STRUCTURE=11/11; FULL_ENCODING_AND_RUNTIME_VERIFICATION=OPEN; NO_RUNTIME_EXECUTION')

if __name__ == '__main__':
    main()
