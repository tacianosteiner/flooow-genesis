"""Fail-closed integrity and semantic closure validator; structural PASS != B01 closure."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path


def validate(ledger, occurrences, contexts, traces, closure=False, runtime_evidence=None):
    issues = []
    records = ledger['records']
    signatures = {x['signature'] for x in contexts}
    expected_sites = {x['occurrence_id'] for x in occurrences}
    assigned, shapes = [], set()
    runtime_evidence = runtime_evidence or {}
    for r in records:
        sid = r['shape_id']
        if sid in shapes:
            issues.append('DUPLICATE_SHAPE:' + sid)
        shapes.add(sid)
        if not r['occurrence_ids'] or r['call_count'] != len(r['occurrence_ids']):
            issues.append('SOURCE_OCCURRENCES_MISSING:' + sid)
        assigned.extend(r['occurrence_ids'])
        if any(s not in signatures for s in r['source_functions']):
            issues.append('UNKNOWN_FUNCTION_SIGNATURE:' + sid)
        if set(r['consumer_trace_ids']) != set(r['occurrence_ids']) or any(s not in traces for s in r['consumer_trace_ids']):
            issues.append('CONSUMER_TRACE_MISSING:' + sid)
        if r['semantic_status'] == 'BOUND':
            mandatory = ['callee_signature', 'callee_runtime_identity', 'resolved_argument_types', 'cast_chain', 'required_schema_usage',
                         'required_execute', 'required_table_reads', 'required_helper_calls', 'null_input_contract', 'null_internal_contract',
                         'missing_row_contract', 'duplicate_row_contract', 'result_sql_type', 'result_semantic_states', 'authority_meaning', 'consumer_truth_mapping']
            if any(r.get(k) is None or r.get(k) == 'UNPROVEN' for k in mandatory):
                issues.append('BOUND_DIMENSION_MISSING:' + sid)
            if not r.get('grouping_equivalence_proven') or r['runtime_resolution_status'] != 'PROVEN':
                issues.append('BOUND_RESOLUTION_OR_GROUPING_UNPROVEN:' + sid)
            if not all(traces.get(s, {}).get('semantic_proven') for s in r['consumer_trace_ids']):
                issues.append('BOUND_CONSUMER_UNPROVEN:' + sid)
            if not r.get('required_state_coverage_complete') or not r.get('verified_runtime_evidence_ids'):
                issues.append('BOUND_NULL_OR_EVIDENCE_UNPROVEN:' + sid)
            for eid in r.get('verified_runtime_evidence_ids', []):
                e = runtime_evidence.get(eid)
                if not e or not e.get('pass') or e.get('kind') != 'SEMANTIC_CALL' or e.get('shape_id') != sid or e.get('callee_signature') != r['callee_signature']:
                    issues.append('BOUND_RUNTIME_EVIDENCE_INVALID:' + sid)
        elif closure:
            issues.append('UNBOUND:' + sid)
    if set(assigned) != expected_sites:
        issues.append('OCCURRENCE_COVERAGE_MISMATCH')
    if len(assigned) != len(set(assigned)):
        issues.append('OCCURRENCE_ASSIGNED_MULTIPLE_TIMES')
    if len(expected_sites) != len(occurrences):
        issues.append('DUPLICATE_SOURCE_OCCURRENCE')
    return {'mode': 'SEMANTIC_CLOSURE' if closure else 'STRUCTURAL_INTEGRITY', 'pass': not issues,
            'call_sites': len(occurrences), 'call_shapes': len(records),
            'bound': sum(r['semantic_status'] == 'BOUND' for r in records),
            'unbound': sum(r['semantic_status'] != 'BOUND' for r in records),
            'issues': issues}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--directory', required=True); ap.add_argument('--closure', action='store_true'); ap.add_argument('--output')
    args = ap.parse_args(); d = Path(args.directory)
    ledger = json.loads((d / 'semantic-ledger.json').read_text())
    occurrences = json.loads(gzip.decompress((d / 'source-occurrences.json.gz').read_bytes()))
    contexts = json.loads((d / 'source-function-contexts.json').read_text())
    encoded = gzip.decompress((d / 'consumer-traces.json.gz').read_bytes())
    reference = json.loads((d / 'consumer-traces.json').read_text())
    if hashlib.sha256(encoded).hexdigest() != reference['sha256']:
        raise ValueError('Consumer trace hash mismatch')
    traces = json.loads(encoded)
    # This foundation has no verified source-context semantic executions.
    # Foundation/catalog observations cannot be substituted for SEMANTIC_CALL evidence.
    result = validate(ledger, occurrences, contexts, traces, args.closure, runtime_evidence={})
    fixture = json.loads((d / 'active-fixture-manifest.json').read_text())
    acl = json.loads((d / 'expected-acl-manifest.json').read_text())
    if not acl.get('provenance'):
        result['issues'].append('ACL_EXPECTATION_LACKS_PROVENANCE')
    if args.closure and not fixture['active_fixture_contract_ready']:
        result['issues'].append('ACTIVE_FIXTURE_UNPROVEN')
    if args.closure and not acl.get('complete_effective_manifest_ready'):
        result['issues'].append('COMPLETE_EXPECTED_EFFECTIVE_ACL_UNPROVEN')
    positives = json.loads((d / 'positive-wrapper-results.json').read_text())
    if args.closure and positives['authentic_positive_wrappers_unproven']:
        result['issues'].append('AUTHENTIC_POSITIVE_WRAPPERS_UNPROVEN')
    result['pass'] = not result['issues']
    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'issues'} | {'issue_n': len(result['issues'])}))
    return int(not result['pass'])


if __name__ == '__main__':
    raise SystemExit(main())
