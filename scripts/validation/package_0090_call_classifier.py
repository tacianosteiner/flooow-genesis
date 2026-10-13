"""Bounded successor to continuation-13; preserves all historical artifacts.

Corrects only the four mechanically identified NULLIF(text,'') argument sites.
All remaining argument classifications remain candidates, not authoritative types.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import package_0090_source_closure as q


def classify():
    p = q.ROOT / 'docs/evidence/package-0090-g3f4-typed-binding-dml/continuation-09/SCOPED-CALL-CANDIDATES.json'
    calls = json.loads(p.read_text(encoding='utf-8'))
    source = q.git('show', 'HEAD:' + q.V043.relative_to(q.ROOT).as_posix())
    q.require(q.sha(source) == q.SOURCE_HASH, 'Exact V043 source required')
    q.require(b'all_names pg_catalog.text[];' in source, 'Source text-array declaration required')
    changes = []
    for c in calls:
        if c['callee_spelling'] != 'pg_catalog.convert_to' or c['argument_types'] != ['bool', 'unknown_literal']:
            continue
        a = c['argument_asts'][0].get('A_Expr', {})
        left = a.get('lexpr', {}).get('A_Indirection', {})
        fields = left.get('arg', {}).get('ColumnRef', {}).get('fields', [])
        q.require(a.get('kind') == 'AEXPR_NULLIF' and fields == [{'String': {'sval': 'all_names'}}], 'Unexpected candidate; do not infer correction')
        q.require(a.get('rexpr', {}).get('A_Const', {}).get('sval', {}).get('sval') == '', 'Exact empty-string NULLIF comparator required')
        changes.append({'caller': c['caller'], 'control_path': c['control_path'], 'ast_path': c['ast_path'], 'original_source': c['original_source'],
                        'old_type': 'bool', 'corrected_type': 'text', 'basis': 'Declared text[] element; NULLIF result is first-argument text, not comparison bool'})
        c['argument_types'][0] = 'text'
    q.require(len(changes) == 4, 'Exact four-site correction boundary required')
    grouped = collections.defaultdict(list)
    for c in calls:
        grouped[(c['callee_spelling'], tuple(c['argument_types']), c['explicit_variadic'])].append(c)
    groups = [{'callee_spelling': n, 'argument_types': list(t), 'explicit_variadic': v, 'source_site_n': len(s),
               'source_callers': dict(sorted(collections.Counter(x['caller'] for x in s).items())),
               'example_source': s[0]['original_source'], 'full_execution_binding_complete': False}
              for (n, t, v), s in sorted(grouped.items())]
    return groups, {'input_sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'source_sha256': q.SOURCE_HASH,
                    'call_sites': len(calls), 'historical_call_shapes': 175, 'corrected_call_shapes': len(groups),
                    'bound_call_shapes': 0, 'unbound_call_shapes': len(groups), 'corrections': changes,
                    'boundary': 'Only four NULLIF argument classifications corrected; no other type or authority inferred'}


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--output-directory', required=True)
    args = ap.parse_args()
    groups, status = classify()
    out = Path(args.output_directory)
    out.mkdir(parents=True, exist_ok=True)
    for name, value in [('call-shapes.json', groups), ('call-classification.json', status)]:
        (out / name).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in status.items() if k != 'corrections'}))
