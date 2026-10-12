"""Bounded source effects for every expanded write and row lock; no SQL runs."""
import collections
import hashlib
import json

from source_binding import BASE, read, strings, walk

SOURCE = BASE / 'continuation-05'
INPUT = BASE / 'continuation-08'
OUTPUT = BASE / 'continuation-12'


def parse_key_constraints(table):
    result = []
    for constraint in table['constraints']:
        value = constraint['Constraint']
        if value['contype'] in ['CONSTR_PRIMARY', 'CONSTR_UNIQUE']:
            result.append({'kind': value['contype'], 'keys': strings(value.get('keys', [])), 'source_ast': constraint})
    return result


def conjuncts(node):
    if 'BoolExpr' in node:
        expression = node['BoolExpr']
        if expression['boolop'] == 'AND_EXPR':
            return [leaf for child in expression['args'] for leaf in conjuncts(child)]
    return [node]


def static_key_bound(where, alias, key_columns):
    values = {}
    for leaf in conjuncts(where):
        operation = leaf.get('A_Expr', {})
        if operation.get('kind') != 'AEXPR_OP' or strings(operation.get('name', [])) != ['=']:
            continue
        for left, right in [('lexpr', 'rexpr'), ('rexpr', 'lexpr')]:
            names = strings(operation.get(left, {}).get('ColumnRef', {}).get('fields', []))
            if names not in ([alias, names[-1]] if names else [], [names[-1]] if names else []):
                continue
            rhs = operation.get(right, {})
            if any(kind in ['FuncCall', 'SubLink'] for kind, _, _ in walk(rhs)):
                continue
            if any(kind == 'ColumnRef' and (
                len(refs := strings(node.get('fields', []))) == 1 or refs[0] == alias
            ) for kind, node, _ in walk(rhs)):
                continue
            values[names[-1]] = rhs
    return next((key for key in key_columns if all(field in values for field in key)), None)


def main():
    OUTPUT.mkdir(exist_ok=True)
    dml = read(INPUT / 'EXPANDED-DML-DEPENDENCIES.json')
    tables = read(BASE / 'continuation-02/EFFECTIVE-TABLE-CATALOG.json')
    functions = {}
    for path in SOURCE.glob('*.json'):
        if path.name != 'EXPANDED-SOURCE-GRAPH.json':
            function = read(path)
            functions[function['function']['signature']] = function
    write_rows, lock_rows = [], []
    for item in dml:
        signature = item['function']
        if item['kind'] == 'LockingClause':
            statement = functions[signature]['statements'][item['statement_ordinal']]
            node = statement['ast']
            enclosing_select = None
            for part in item['node_path'][:-3]:
                node = node[part]
            enclosing_select = node['SelectStmt'] if 'SelectStmt' in node else node
            relations = item['candidate_relations']
            assert len(relations) == 1 and not item['explicit_lock_targets']
            relation_ast = relations[0]
            relation = relation_ast.get('schemaname', 'public') + '.' + relation_ast['relname']
            assert relation in tables
            lock_rows.append({
                'LOCK_ID': item['id'], 'SOURCE_OBJECT': signature,
                'SOURCE_PROVENANCE': item['original_source'], 'STATEMENT_ORDINAL': item['statement_ordinal'],
                'CONTROL_PATH': item['control_path'], 'TARGET_RELATION': relation,
                'RELATION_DECLARATION': tables[relation]['provenance'], 'RELATION_ALIAS': relation_ast.get('alias'),
                'SELECTION_PREDICATE_GROUPED_AST': enclosing_select.get('whereClause'),
                'SOURCE_FROM_CLAUSE': enclosing_select.get('fromClause'),
                'LOCK_STRENGTH': item['lock_mode'], 'WAIT_POLICY': item['wait_policy'],
                'NO_OF_CLAUSE': True, 'SOURCE_PREDICATE_AND_TARGET_BOUND': True,
                'TRANSACTION_SCOPE_RULE': 'Row locks normally persist until transaction end; exception/subtransaction and caller boundary require proof',
                'ZERO_ROW_MEANING': 'No selected row lock; cannot infer authorization, identity or protected progress',
                'SOURCE_ORDINAL_ONLY_NOT_RUNTIME_LOCK_ORDER': True,
                'SUBSEQUENT_DML_BINDING': 'CONTROL_PATH_AND_CASE_CFG_REVIEW_PENDING',
                'ISOLATION_AND_DEADLOCK_ORDER_PROVEN': False, 'AUTHORITY_RELEVANCE_PROVEN': False,
                'COMPLETE': False,
                'REMAINING': ['Exact grouped predicate/operator/NULL acceptance', 'Function and cross-function lock order',
                              'Caller transaction/isolation and concurrent update behavior', 'Deadlock and zero-row control effect'],
                'PROOF_PATHS': ['STATIC_SOURCE_PROOF', 'LOCK_BEHAVIOR_PROOF', 'EXECUTABLE_SQL_NEGATIVE'],
            })
            continue
        node = item['exact_ast']
        target = item['target_relation']
        table = tables[target]
        columns = table['columns']
        constraints = []
        for column, declaration in columns.items():
            constraints.extend({'column': column, 'ast': value, 'source': declaration.get('provenance', table['provenance'])}
                               for value in declaration.get('constraints', []))
        constraints.extend({'column': None, 'ast': value, 'source': table['provenance']}
                           for value in table['constraints'])
        keys = parse_key_constraints(table)
        foreign_keys = []
        for constraint in constraints:
            value = constraint['ast']['Constraint']
            if value['contype'] == 'CONSTR_FOREIGN':
                ref = value['pktable']
                name = ref.get('schemaname', 'public') + '.' + ref['relname']
                foreign_keys.append({'source_ast': value, 'referenced_relation': name,
                                     'referenced_declaration': tables.get(name, {}).get('provenance')})
        defaults = [{'column': name, 'raw_default': declaration.get('raw_default'),
                     'generated': declaration.get('generated'), 'identity': declaration.get('identity')}
                    for name, declaration in columns.items()
                    if declaration.get('raw_default') or declaration.get('generated') or declaration.get('identity')]
        source_shape = None
        bounded_insert_select = None
        if item['kind'] == 'InsertStmt':
            select = node['selectStmt']['SelectStmt']
            if len(select.get('valuesLists', [])) == 1 and not select.get('fromClause'):
                source_shape = 'ONE_VALUES_ROW_BEFORE_CONSTRAINTS_AND_TRIGGERS'
            else:
                source_shape = 'SELECT_ROWSET_REQUIRES_GROUPED_PREDICATE_AND_CARDINALITY'
                if len(select.get('fromClause', [])) == 1 and 'RangeVar' in select['fromClause'][0]:
                    source_relation_ast = select['fromClause'][0]['RangeVar']
                    source_relation = source_relation_ast.get('schemaname', 'public') + '.' + source_relation_ast['relname']
                    source_table = tables.get(source_relation)
                    if source_table:
                        alias = source_relation_ast.get('alias', {}).get('aliasname', source_relation_ast['relname'])
                        source_keys = [entry['keys'] for entry in parse_key_constraints(source_table)]
                        key = static_key_bound(select.get('whereClause', {}), alias, source_keys)
                        bounded_insert_select = {'source_relation': source_relation, 'source_primary_or_unique_key': key,
                                                 'at_most_one_source_row': bool(key),
                                                 'grouped_where_ast': select.get('whereClause')}
            assert node.get('onConflictClause') is None
        write_rows.append({
            'WRITE_ID': item['id'], 'SOURCE_OBJECT': signature, 'SOURCE_PROVENANCE': item['original_source'],
            'STATEMENT_ORDINAL': item['statement_ordinal'], 'CONTROL_PATH': item['control_path'],
            'KIND': item['kind'], 'TARGET_RELATION': target, 'TARGET_DECLARATION': table['provenance'],
            'SOURCE_VALUES_OR_SELECT_AST': node.get('selectStmt') if item['kind'] == 'InsertStmt' else node.get('targetList'),
            'WHERE_GROUPED_AST': node.get('whereClause'), 'RETURNING_AST': node.get('returningList'),
            'SOURCE_SHAPE': source_shape, 'BOUNDED_INSERT_SELECT': bounded_insert_select,
            'TARGET_KEYS': keys, 'CONSTRAINTS': constraints, 'FOREIGN_KEYS': foreign_keys,
            'DEFAULTS_AND_GENERATED': defaults, 'SOURCE_TRIGGER_CANDIDATES': item['source_trigger_candidates'],
            'SECURITY_OPTIONS_AST': item['security_options_ast'],
            'ON_CONFLICT_AST': node.get('onConflictClause'),
            'CONFLICT_BEHAVIOR': 'No ON CONFLICT clause in source; uniqueness violation is an error, not an idempotent success'
                                 if item['kind'] == 'InsertStmt' else 'UPDATE; no INSERT conflict clause',
            'SOURCE_AT_MOST_ONE_INPUT_ROW': source_shape == 'ONE_VALUES_ROW_BEFORE_CONSTRAINTS_AND_TRIGGERS'
                                            or bool(bounded_insert_select and bounded_insert_select['at_most_one_source_row'])
                                            if item['kind'] == 'InsertStmt' else None,
            'ZERO_AND_MULTIROW_BEHAVIOR_COMPLETE': False,
            'STATE_TRANSITION_COMPLETE': False, 'AUTHORITY_PRECONDITIONS_COMPLETE': False,
            'IMPLICIT_DEPENDENCIES_COMPLETE': False, 'COMPLETE': False,
            'REMAINING': ['Grouped WHERE/SET/VALUES and authority source-to-target proof',
                          'Zero/multirow and retry acceptance path', 'FK/CHECK/UNIQUE/NOT NULL/default/generated effects',
                          'Event-specific trigger and exception propagation', 'RLS/catalog, isolation and ownership corroboration'],
            'PROOF_PATHS': ['STATIC_SOURCE_PROOF', 'CONSTRAINT_FAILURE', 'DML_STATE_TRANSITION', 'EXECUTABLE_SQL_NEGATIVE'],
        })
    assert len(write_rows) == 28 and len(lock_rows) == 109
    assert sum(x['KIND'] == 'InsertStmt' for x in write_rows) == 18
    assert sum(x['SOURCE_AT_MOST_ONE_INPUT_ROW'] for x in write_rows if x['KIND'] == 'InsertStmt') == 18
    assert all(x['SOURCE_PREDICATE_AND_TARGET_BOUND'] for x in lock_rows)
    status = {
        'WRITE_STATEMENT_N': len(write_rows), 'WRITE_COMPLETE_N': 0, 'WRITE_INCOMPLETE_N': len(write_rows),
        'INSERT_STATEMENT_N': 18, 'INSERT_SOURCE_AT_MOST_ONE_INPUT_ROW_N': 18,
        'INSERT_VALUES_ONE_ROW_N': sum(x['SOURCE_SHAPE'] == 'ONE_VALUES_ROW_BEFORE_CONSTRAINTS_AND_TRIGGERS' for x in write_rows),
        'LOCK_CLAUSE_N': len(lock_rows), 'LOCK_TARGET_AND_GROUPED_PREDICATE_SOURCE_BOUND_N': len(lock_rows),
        'LOCK_COMPLETE_N': 0, 'LOCK_INCOMPLETE_N': len(lock_rows),
        'LOCK_STRENGTH_COUNTS': dict(collections.Counter(x['LOCK_STRENGTH'] for x in lock_rows)),
        'SOURCE_CATALOG_IMPLICIT_DEPENDENCIES_ATTACHED_N': len(write_rows),
        'DML_DEPENDENCY_COMPLETE_N': 0, 'DML_DEPENDENCY_INCOMPLETE_N': len(write_rows),
        'no_runtime_or_concurrency_proof': True,
    }
    for name, value in [('WRITE-SOURCE-EFFECTS.json', write_rows), ('LOCK-SOURCE-EFFECTS.json', lock_rows),
                        ('DML-LOCK-STATUS.json', status)]:
        (OUTPUT / name).write_text(json.dumps(value, separators=(',', ':'), sort_keys=True) + '\n',
                                   encoding='utf-8', newline='\n')
    print(json.dumps(status))


if __name__ == '__main__':
    main()
