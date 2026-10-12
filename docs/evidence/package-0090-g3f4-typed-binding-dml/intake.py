"""Read-only FC01 gate intake; never executes SQL, wrappers or native code.

Cached AST hashes are independently checked. This produces candidate source-call
reachability, not PostgreSQL overload/operator/catalog semantic closure.
"""
from pathlib import Path
import collections
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
EXPECTED = '406b446d0b00abf1a45d86c7c8baeee640bc9d4d'
OLD = ROOT / 'docs/evidence/package-0090-g3f4-authority-boundary-typed'

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def emit(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n', encoding='utf-8', newline='\n')

def walk(value, path=()):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key, child, path + (key,)
            yield from walk(child, path + (key,))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk(child, path + (index,))

def strings(items):
    return [item['String']['sval'] for item in items if 'String' in item]

def main():
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    remote = subprocess.check_output(['git', 'rev-parse', 'origin/checkpoint/package-0090-cloud-handoff'], cwd=ROOT, text=True).strip()
    assert head == remote == EXPECTED
    publication = read(OLD / 'final-03/SHA256-PUBLICATION.json')
    mismatches = []
    for name, expected in publication['files'].items():
        if sha(ROOT / name) != expected:
            mismatches.append(name)
    assert not mismatches, mismatches
    emit('BASELINE.json', {'branch': 'checkpoint/package-0090-cloud-handoff', 'input_head': head, 'remote_head': remote,
         'historical_publication_files_rehashed': len(publication['files']), 'historical_mismatch_n': len(mismatches),
         'entry_tracked_dirty_n': 0, 'entry_staged_n': 0,
         'authorization': 'COMPLETE_TYPED_BINDINGS_SOURCE_SPANS_IMPLICIT_DML_AND_TWO_LAYER_WITNESS_VALIDATION',
         'positive_execution': False, 'native_implementation': False, 'canonical_access': False, 'numeric_policy_adoption': False})
    functions = {}
    for path in sorted((OLD / 'functions').glob('*.json')):
        obj = read(path)
        functions[obj['signature']] = obj
    by_name = collections.defaultdict(list)
    for signature, obj in functions.items():
        by_name[obj['name']].append(signature)
    cases = read(ROOT / 'docs/evidence/package-0090-g3f4-full-domain-fixture-contract/POSITIVE-CASE-PRECONDITIONS.json')
    assert len(cases) == 13
    roots = {w['signature'].replace('pg_catalog.', '') for case in cases for w in case['WRAPPERS']}
    assert roots <= functions.keys(), roots - functions.keys()
    old_graph = read(OLD / 'final-03/CALL-GRAPH.json')
    old_pairs = {(x['source'], target) for x in old_graph['edges'] for target in x['targets']}
    edges = []
    unbound_calls = []
    per_object = collections.defaultdict(list)
    ast_n = 0
    stmt_n = 0
    for ref_path in sorted((OLD / 'final-03/statements').glob('*.reference.json')):
        reference = read(ref_path)
        artifact = ROOT / reference['artifact']
        assert sha(artifact) == reference['sha256']
        for statement in read(artifact):
            stmt_n += 1
            object_name = statement['SQL_OBJECT']
            per_object[object_name].append(statement['SQL_STATEMENT_ID'])
            for kind, node, path in walk(statement['ast']):
                if isinstance(node, dict):
                    ast_n += 1
                if kind != 'FuncCall':
                    continue
                spelling = '.'.join(strings(node['funcname']))
                candidate_name = spelling if '.' in spelling else 'public.' + spelling
                targets = [sig for sig in by_name.get(candidate_name, [])
                           if len(functions[sig]['parameter_types']) == len(node.get('args', []))]
                if not targets:
                    unbound_calls.append({'caller': object_name, 'statement_id': statement['SQL_STATEMENT_ID'],
                                          'ast_path': list(path), 'source_spelling': spelling,
                                          'argument_n': len(node.get('args', [])),
                                          'status': 'BUILTIN_OR_USER_FUNCTION_CATALOG_BINDING_NOT_PROVEN'})
                    continue
                edges.append({'caller': object_name, 'statement_id': statement['SQL_STATEMENT_ID'],
                              'ast_path': list(path), 'source_spelling': spelling, 'candidates': targets,
                              'resolution': 'SOURCE_NAME_ARITY_CANDIDATE_ONLY_NOT_OVERLOAD_CATALOG_PROOF',
                              'unqualified': '.' not in spelling,
                              'prior_edge_present': all((object_name, target) in old_pairs for target in targets)})
    adjacency = collections.defaultdict(set)
    for edge in edges:
        adjacency[edge['caller']].update(edge['candidates'])
    def reach(entrypoints):
        visited = set()
        todo = list(entrypoints)
        while todo:
            signature = todo.pop()
            if signature in visited:
                continue
            visited.add(signature)
            todo.extend(adjacency[signature] - visited)
        return visited
    reachable = reach(roots)
    relevant = [edge for edge in edges if edge['caller'] in reachable]
    missed = [edge for edge in relevant if edge['unqualified'] and not edge['prior_edge_present']]
    case_graphs = [{'case_id': case['CASE_ID'], 'entrypoints': sorted({w['signature'].replace('pg_catalog.', '') for w in case['WRAPPERS']}),
                   'candidate_function_objects': sorted(reach({w['signature'].replace('pg_catalog.', '') for w in case['WRAPPERS']})),
                   'complete': False, 'reason': 'Unqualified/overload/search_path/catalog and implicit DML dependencies not closed'} for case in cases]
    emit('CASE-REACHABILITY-CANDIDATES.json', {'positive_case_n': len(cases), 'entry_signature_n': len(roots),
         'cases': case_graphs, 'candidate_function_n': len(reachable), 'candidate_functions': sorted(reachable),
         'cached_statement_n': stmt_n, 'cached_dict_node_n': ast_n,
         'count_domain': 'Cached statement AST dictionary nodes only; excludes PL control AST and implicit dependencies; NOT total closure denominator',
         'all_counts_are_candidate_inventory_not_semantic_closure': True})
    emit('CALL-EDGE-REVIEW.json', {'candidate_edges': relevant, 'unqualified_edges_absent_from_prior_graph': missed,
         'missed_unqualified_call_occurrence_n': len(missed),
         'calls_without_cached_source_target': [x for x in unbound_calls if x['caller'] in reachable],
         'unbound_source_names': sorted({x['source_spelling'] for x in unbound_calls if x['caller'] in reachable}),
         'finding': 'Public-prefix prior inventory does not prove all catalog/builtin/unqualified/overload resolution. No absent cached-target unqualified edge was demonstrated by this intake.',
         'severity': 'REVIEW_REQUIRED',
         'exact_call_binding_complete': False})
    emit('INTAKE-STATUS.json', {'status': 'HOLD_TYPED_BINDINGS_DML_CLOSURE_IN_PROGRESS',
         'historical_hashes_intact': True, 'positive_case_n': len(cases), 'positive_wrapper_execution': False,
         'closure_denominator_n': 'UNKNOWN', 'fc01_unclassified_ast_node_n': 'UNKNOWN_NOT_ALL_REACHABILITY_PROVEN',
         'source_span_closure': False, 'identifier_binding_closure': False, 'implicit_dml_closure': False,
         'fixture_contract_ready': False, 'runtime_or_native_changed': False,
         'next_action': 'Resolve exact search_path-aware source call targets, then expand implicit DML catalog dependencies before denominator typing'})
    print(json.dumps({'historical_files_rehashed': len(publication['files']), 'historical_mismatches': len(mismatches),
                      'cases': len(cases), 'entry_signatures': len(roots), 'candidate_functions': len(reachable),
                      'missed_unqualified_call_occurrences': len(missed), 'status': 'HOLD'}))

if __name__ == '__main__':
    main()
