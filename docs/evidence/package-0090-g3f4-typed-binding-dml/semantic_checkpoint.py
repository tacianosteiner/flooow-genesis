"""Offline candidate semantic/DML inventory. Never executes SQL or native code.

Run manually with Python 3; inputs are hash-bound cached ASTs for frozen FC01
paths. No candidate count is a closure denominator or executable proof.
"""
from pathlib import Path
import collections
import hashlib
import json

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
OLD = ROOT / 'docs/evidence/package-0090-g3f4-authority-boundary-typed'
OUT = BASE / 'semantic-checkpoint'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf-8')

def write(name, value):
    (OUT / name).write_bytes(json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False).encode('utf-8') + b'\n')

def walk(value, path=()):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key, child, path + (key,)
            yield from walk(child, path + (key,))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk(child, path + (index,))

def strings(values):
    return [x['String']['sval'] for x in values if 'String' in x]

def relation(value):
    return {'schema': value.get('schemaname', 'UNRESOLVED_SEARCH_PATH'), 'relation': value['relname'],
            'alias': value.get('alias', {}).get('aliasname'), 'catalog_binding': 'UNRESOLVED'}

def main():
    OUT.mkdir(exist_ok=True)
    graph = read(BASE / 'CASE-REACHABILITY-CANDIDATES.json')
    reachable = set(graph['candidate_functions'])
    functions = {}
    for path in (OLD / 'functions').glob('*.json'):
        value = read(path)
        if value['signature'] in reachable:
            functions[value['signature']] = value
    inventory, dml, unresolved = [], [], []
    statement_keys = set()
    identifier_refs = 0
    for reference_path in sorted((OLD / 'final-03/statements').glob('*.reference.json')):
        ref = read(reference_path)
        data = (ROOT / ref['artifact']).read_bytes()
        if digest(data) != ref['sha256']:
            raise ValueError('Cached AST hash mismatch: ' + ref['artifact'])
        for statement in json.loads(data):
            signature = statement['SQL_OBJECT']
            if signature not in reachable:
                continue
            sid = statement['SQL_STATEMENT_ID']
            if sid in statement_keys:
                raise ValueError('Duplicate statement ordinal: ' + sid)
            statement_keys.add(sid)
            f = functions[signature]
            ordinal = int(sid.rsplit(':S', 1)[1])
            if f['expressions'][ordinal]['query'] != statement['query']:
                raise ValueError('Statement ordinal/query mismatch: ' + sid)
            provenance = {'SOURCE_FILE': f['source'], 'SOURCE_OBJECT': signature,
                          'STATEMENT_ORDINAL': ordinal, 'STATEMENT_SHA256': digest(statement['query'].encode()),
                          'OBJECT_HASH': f['definition_sha256'], 'BODY_HASH': digest(f['body'].encode()),
                          'SUCCESSOR_HASH': '6ad78ba61d70e803d2a878034aa7988b69b6374568f96949b2ef6c8defc7a8c7',
                          'AST_ARTIFACT': ref['artifact'], 'AST_ARTIFACT_HASH': ref['sha256'],
                          'PROVENANCE_STATUS': 'EXACT_CACHED_ORDINAL_HASH_ORIGINAL_SOURCE_REBINDING_PENDING'}
            identifiers = [{'ast_path': list(path), 'reference': strings(node['fields']),
                            'binding': 'UNRESOLVED_SCOPE_CATALOG_OR_PL_VARIABLE'}
                           for kind, node, path in walk(statement['ast']) if kind == 'ColumnRef']
            identifier_refs += len(identifiers)
            for kind, node, path in walk(statement['ast']):
                if kind not in {'InsertStmt', 'UpdateStmt', 'DeleteStmt', 'MergeStmt', 'LockingClause'}:
                    continue
                item_id = digest(canonical([sid, path, kind]))[:24]
                target = relation(node['relation']) if 'relation' in node else {'row_lock_targets': node.get('lockedRels', []), 'catalog_binding': 'UNRESOLVED'}
                writes = [x.get('ResTarget', {}).get('name') for x in node.get('cols', node.get('targetList', []))]
                reads = [relation(v) for k, v, _ in walk(node) if k == 'RangeVar']
                record = {'ITEM_ID': item_id, 'STATEMENT_ID': sid, 'NODE_PATH': list(path), 'KIND': kind,
                          'TARGET_RELATION': target, 'WRITE_COLUMNS': writes, 'READ_DEPENDENCIES': reads,
                          'WHERE_JOIN_GROUPED_AST': node.get('whereClause'), 'SET_TARGETS_AST': node.get('targetList'),
                          'RETURNING_AST': node.get('returningList'), 'ON_CONFLICT_AST': node.get('onConflictClause'),
                          'LOCK_AST': node if kind == 'LockingClause' else node.get('lockingClause'),
                          'CONSTRAINT_DEPENDENCIES': 'UNRESOLVED_PK_FK_UNIQUE_CHECK_NOT_NULL_DEFAULT_GENERATED',
                          'TRIGGER_DEPENDENCIES': 'UNRESOLVED', 'RLS_VIEW_DEPENDENCIES': 'UNRESOLVED',
                          'SECURITY_DEFINER_SEARCH_PATH': 'ORIGINAL_DECLARATION_REBINDING_PENDING',
                          'CAS_VERSION': 'GROUPED_PREDICATE_REVIEW_PENDING', 'STATE_TRANSITION': 'UNRESOLVED',
                          'EXPECTED_ROWCOUNT': 'UNRESOLVED', 'ZERO_ROW_BEHAVIOR': 'CONTROL_FLOW_REVIEW_PENDING',
                          'MULTIROW_BEHAVIOR': 'CONTROL_FLOW_REVIEW_PENDING', 'FAILURE_BEHAVIOR': 'EXCEPTION_REVIEW_PENDING',
                          'PROVENANCE': provenance, 'STATUS': 'UNRESOLVED',
                          'PROOF_PATHS': ['STATIC_SOURCE_PROOF', 'CONSTRAINT_FAILURE', 'DML_STATE_TRANSITION', 'EXECUTABLE_SQL_NEGATIVE']}
                dml.append(record)
            # Preserve complete grouped expression/control context. Literal RAISE
            # messages/SQLSTATE options and assignment syntax are not independent
            # governed checks. No nested boolean leaves become separate meanings.
            context = statement['plpgsql_context']
            kinds = {k for k, _, _ in walk(statement['ast'])}
            is_condition = context in {'PLpgSQL_stmt_if', 'PLpgSQL_if_elsif', 'PLpgSQL_stmt_while', 'PLpgSQL_case_when'}
            has_effect = bool(kinds & {'InsertStmt', 'UpdateStmt', 'DeleteStmt', 'MergeStmt', 'LockingClause'})
            if not is_condition and not has_effect:
                continue
            item_id = digest(canonical([sid, context, 'GROUPED_SEMANTIC_CANDIDATE']))[:24]
            inventory.append({'ITEM_ID': item_id, 'STATEMENT_ID': sid, 'CONTROL_CONTEXT': context,
                              'CLASS': 'UNRESOLVED_INDEPENDENT_GOVERNED_MEANING',
                              'CONDITION_GROUPING': 'EXACT_AST_TREE_NOT_FLATTENED',
                              'QUERY_SHA256': provenance['STATEMENT_SHA256'], 'PROVENANCE': provenance,
                              'IDENTIFIERS': identifiers, 'STATUS': 'UNRESOLVED',
                              'PROOF_PATHS': ['STATIC_SOURCE_PROOF', 'EXECUTABLE_SQL_POSITIVE', 'EXECUTABLE_SQL_NEGATIVE']})
    call_review = read(BASE / 'CALL-EDGE-REVIEW.json')
    grouped_edges = {}
    for edge in call_review['candidate_edges']:
        key = (edge['caller'], tuple(edge['candidates']))
        grouped_edges.setdefault(key, {'caller': edge['caller'], 'candidate_targets': edge['candidates'], 'occurrence_n': 0,
                                      'STATUS': 'UNRESOLVED', 'source_link': 'SOURCE_NAME_ARITY_ONLY',
                                      'obligations': ['search_path', 'argument_types', 'overload', 'volatility', 'security_context']})['occurrence_n'] += 1
    # Calls with no source target can be builtins, extension or omitted frozen
    # source functions. None is dropped simply because it looks familiar.
    unbound_names = call_review['unbound_source_names']
    unknown_bundles = [{'edge_type': 'FUNCTION_BINDING', **v} for v in grouped_edges.values()]
    unknown_bundles += [{'edge_type': 'CATALOG_OR_EXTENSION_BINDING', 'source_spelling': name, 'STATUS': 'UNRESOLVED'} for name in unbound_names]
    unknown_bundles += [{'edge_type': 'IMPLICIT_DML_DEPENDENCY_BUNDLE', 'item_id': x['ITEM_ID'], 'STATUS': 'UNRESOLVED'} for x in dml]
    write('SEMANTIC-CANDIDATES.json', inventory)
    write('DML-DEPENDENCY-GRAPH.json', dml)
    write('EDGE-DISPOSITIONS.json', {'edges': unknown_bundles, 'proven_execution_edges_n': 0,
                                  'out_of_scope_execution_edges_n': 0,
                                  'unresolved_known_obligation_bundles_n': len(unknown_bundles),
                                  'exhaustive_execution_edge_n': 'UNKNOWN_IMPLICIT_EXPANSION_OPEN'})
    write('SEMANTIC-STATUS.json', {'positive_case_path_n': 13, 'distinct_entry_signature_n': graph['entry_signature_n'],
                                 'candidate_function_n': len(reachable), 'candidate_grouped_check_or_effect_n': len(inventory),
                                 'candidate_dml_or_row_lock_n': len(dml), 'dml_incomplete_known_n': len(dml),
                                 'identifier_occurrence_n': identifier_refs, 'resolved_identifier_n': 0,
                                 'unresolved_identifier_known_n': identifier_refs,
                                 'ordinal_query_hash_link_verified_n': len(statement_keys),
                                 'closure_denominator_n': 'UNKNOWN', 'typed_closure_item_n': 0,
                                 'untyped_closure_item_n': 'UNKNOWN_DENOMINATOR_NOT_PROVEN',
                                 'missing_provenance_n': 'UNKNOWN_ORIGINAL_SOURCE_REBINDING_OPEN',
                                 'control_flow_complete_13_of_13': False,
                                 'null_semantics_mismatch_n': 'UNKNOWN_NOT_FULLY_REVIEWED',
                                 'full_domain_fixture_contract_ready': False,
                                 'status': 'HOLD_SEMANTIC_BINDING_DML_AND_TWO_LAYER_PROOF',
                                 'candidate_counts_are_not_proven_denominator': True})
    print(json.dumps({'candidate_checks_effects': len(inventory), 'candidate_dml_row_locks': len(dml),
                      'known_unresolved_edge_bundles': len(unknown_bundles), 'ordinal_links_verified': len(statement_keys), 'status': 'HOLD'}))

if __name__ == '__main__':
    main()
