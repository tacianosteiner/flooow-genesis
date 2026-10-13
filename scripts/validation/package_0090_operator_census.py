"""Reproducible operator census of the frozen 68-function reachable source corpus.

Enumerates original SQL AST paths once per statement, not duplicated control AST.
No operator occurrence, lock ordering or authority predicate is marked proven.
"""
import argparse
import collections
import hashlib
import gzip
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / 'docs/evidence/package-0090-g3f4-typed-binding-dml/continuation-05'


def walk(node, path=()):
    if isinstance(node, dict):
        for k, v in node.items():
            yield k, v, path + (k,)
            yield from walk(v, path + (k,))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk(v, path + (i,))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', required=True)
    args = ap.parse_args()
    files = sorted(p for p in CORPUS.iterdir() if re.fullmatch('[0-9a-f]{24}\\.json', p.name))
    assert len(files) == 68
    sites, inputs, signatures = [], {}, []
    kinds = collections.Counter()
    for p in files:
        b = p.read_bytes()
        inputs[p.relative_to(ROOT).as_posix()] = hashlib.sha256(b).hexdigest()
        f = json.loads(b)
        signatures.append(f['function']['signature'])
        for s in f['statements']:
            for k, v, path in walk(s['ast']):
                if k != 'A_Expr':
                    continue
                spelling = '.'.join(x['String']['sval'] for x in v.get('name', []) if 'String' in x)
                kind = v['kind']
                kinds[kind] += 1
                sites.append({'function': f['function']['signature'], 'source': f['function']['source'],
                              'statement_ordinal': s['ordinal'], 'query_sha256': s.get('query_sha256'),
                              'ast_path': list(path), 'kind': kind, 'spelling': spelling,
                              'left_node_kind': list(v.get('lexpr', {})), 'right_node_kind': list(v.get('rexpr', {})),
                              'exact_operator_binding_proven': False})
    assert len(set(signatures)) == 68
    groups = collections.Counter((s['kind'], s['spelling']) for s in sites)
    result = {'scope': '68_FUNCTION_REACHABLE_SOURCE_AST_NOT_COMPLETE_IMPLICIT_OPERATOR_DENOMINATOR',
              'input_hashes': inputs, 'function_n': len(files), 'A_Expr_site_n': len(sites),
              'kinds': dict(sorted(kinds.items())),
              'spelling_groups': [{'kind': k, 'spelling': n, 'sites': c} for (k, n), c in sorted(groups.items())],
              'operator_semantics_proven_n': 0,
              'full_operator_denominator': 'UNKNOWN_IMPLICIT_CAST_DDL_CHECK_INDEX_AND_RUNTIME_OPERATOR_PATHS_OPEN',
              'site_ledger_sha256': hashlib.sha256(json.dumps(sites, sort_keys=True, separators=(',', ':')).encode()).hexdigest()}
    out = Path(args.output)
    ledger = out.with_name(out.stem + '-sites.json.gz')
    ledger.write_bytes(gzip.compress(json.dumps(sites, sort_keys=True, separators=(',', ':')).encode(), mtime=0))
    result['site_ledger_file'] = ledger.name
    result['compressed_ledger_sha256'] = hashlib.sha256(ledger.read_bytes()).hexdigest()
    out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: result[k] for k in ['function_n', 'A_Expr_site_n', 'kinds', 'full_operator_denominator']}))


if __name__ == '__main__':
    main()
