"""Bind grouped case CFG obligations to exact frozen source paths, without PASS."""
from pathlib import Path
import collections
import hashlib
import json

from source_binding import BASE, read

OUTPUT = BASE / 'continuation-11'


def main():
    OUTPUT.mkdir(exist_ok=True)
    cases = read(BASE / 'continuation-06/CASE-CONTROL-FLOW.json')['cases']
    graph_root = BASE / 'continuation-06'
    cfgs = {}
    for path in graph_root.glob('*.json'):
        if len(path.stem) == 24:
            graph = read(path)
            cfgs[graph['signature']] = graph
    source = read(BASE / 'continuation-05/EXPANDED-SOURCE-GRAPH.json')
    functions = {f['signature']: f for f in source['functions']}
    dml = read(BASE / 'continuation-08/EXPANDED-DML-DEPENDENCIES.json')
    dml_by_function = collections.defaultdict(list)
    for item in dml:
        dml_by_function[item['function']].append(item)
    nulls = read(OUTPUT / 'NULL-EXACT-CONSUMERS.json')
    null_by_function = collections.Counter(x['SOURCE_OBJECT'] for x in nulls)
    rows = []
    for case in cases:
        members = case['transitive_functions']
        assert all(member in cfgs and member in functions for member in members)
        controls = []
        case_writes = []
        case_locks = []
        for member in members:
            cfg = cfgs[member]
            node_kinds = collections.Counter(n['kind'] for n in cfg['nodes'])
            controls.append({
                'SOURCE_OBJECT': member, 'SOURCE_PROVENANCE': functions[member]['source'],
                'CFG_ENTRY': cfg['entry'], 'CFG_NODE_N': len(cfg['nodes']),
                'CFG_EDGE_N': len(cfg['edges']), 'NODE_KIND_COUNTS': dict(node_kinds),
                'GUARD_TRUE_FALSE_UNKNOWN_GROUPING': 'SOURCE_AST_RETAINED; ACCEPTANCE_DATAFLOW_OPEN',
                'TERMINAL_RETURN_EDGES': [e for e in cfg['edges'] if e['to'] == 'FUNCTION_RETURN'],
                'RAISE_OR_SQL_ERROR_EDGE_N': sum(e['to'] == 'PROPAGATE_SQL_EXCEPTION_TO_CALLER' for e in cfg['edges']),
                'EXCEPTION_DISPATCH_GAPS': [g for g in cfg['semantic_gaps'] if 'EXCEPTION_SQLSTATE' in g.get('reason', '')],
                'LOOP_BOUND_GAP_N': sum('LOOP_INPUT' in g.get('reason', '') for g in cfg['semantic_gaps']),
                'NULL_SENSITIVE_AST_CANDIDATE_N': null_by_function[member],
                'FULL_CONTROL_SEMANTICS_COMPLETE': False,
            })
            for item in dml_by_function[member]:
                dependency = {
                    'ID': item['id'], 'SOURCE_OBJECT': member,
                    'STATEMENT_ORDINAL': item['statement_ordinal'],
                    'CONTROL_PATH': item['control_path'], 'KIND': item['kind'],
                    'SOURCE_PROVENANCE': item['original_source'],
                    'GROUPED_PREDICATE_AST': item.get('where_grouped_ast'),
                    'SEMANTICS_COMPLETE': False,
                }
                (case_locks if item['kind'] == 'LockingClause' else case_writes).append(dependency)
        row = {
            'CASE_ID': case['case_id'], 'ENTRY': case['entry_signatures'],
            'GROUPED_FUNCTION_CONTROL_GRAPHS': controls,
            'NULL_SENSITIVE_BRANCH_CANDIDATE_N': sum(null_by_function[x] for x in members),
            'WRITE_EDGES': case_writes, 'LOCK_EDGES': case_locks,
            'AUTHORITY_CHECK_EDGES': 'UNRESOLVED_29_KNOWN_CANDIDATES_REQUIRE_EXACT_PATH_BINDING',
            'ROWCOUNT_BRANCH_EDGES': 'BOUNDED_UPDATE_SUBPROOFS_ONLY; ALL_EFFECTS_PENDING',
            'RETRY_EDGES': 'OFFLINE_PERSIST_VERIFICATION_RETRY_AND_OTHER_PATHS_PENDING',
            'RECONCILIATION_EDGES': 'EXACT_SQL_STATE_AND_RUNTIME_CORROBORATION_PENDING',
            'EXIT': 'RETURN_OR_PROPAGATED_EXCEPTION; COMPLETE_ACCEPTANCE_PENDING',
            'ABSENT_PLPGSQL_CONTROL_KINDS_IN_EXPANDED_SOURCE': ['EXIT', 'CONTINUE', 'GET DIAGNOSTICS'],
            'STRUCTURAL_CFG_AVAILABLE': True, 'SEMANTIC_CFG_COMPLETE': False,
            'REMAINING': [
                'Exact guarded authority plus NULL acceptance and source operator bindings',
                'DML/lock rowcount, constraint/trigger/isolation and SQLSTATE effects',
                'Complete exception dispatch, loop input cardinality and retries',
                'Independent external witness and generation-bound runtime corroboration',
            ],
        }
        rows.append(row)
    assert len(rows) == 13
    status = {
        'STRUCTURAL_CFG_N': len(rows), 'SEMANTIC_CFG_COMPLETE_N': 0,
        'SEMANTIC_CFG_INCOMPLETE_N': len(rows), 'CASES': rows,
        'source_scope': '68 candidate functions reached from 13 frozen cases; structural graph is an overapproximation',
    }
    (OUTPUT / 'GROUPED-CASE-SEMANTIC-CFG.json').write_text(
        json.dumps(status, separators=(',', ':'), sort_keys=True) + '\n', encoding='utf-8', newline='\n'
    )
    print(json.dumps({'STRUCTURAL_CFG_N': 13, 'SEMANTIC_CFG_COMPLETE_N': 0}))


if __name__ == '__main__':
    main()
