"""Reclassify exact source AST consumers without promoting rule facts to safety.

The historical NULL candidate file remains unchanged. No SQL is executed.
"""
from pathlib import Path
import collections
import hashlib
import json

from source_binding import BASE, read, strings, walk

SOURCE = BASE / 'continuation-05'
PREVIOUS = BASE / 'continuation-06' / 'NULL-CONSUMER-RULES.json'
OUTPUT = BASE / 'continuation-11'


def actual_consumer(sql_path, control_path):
    contexts = []
    if 'whereClause' in sql_path:
        contexts.append('WHERE_TRUE_ONLY')
    if 'quals' in sql_path:
        contexts.append('JOIN_TRUE_ONLY; OUTER_NULL_EXTENSION_REVIEW')
    if 'havingClause' in sql_path:
        contexts.append('HAVING_TRUE_ONLY')
    if 'CaseWhen' in sql_path and 'expr' in sql_path:
        contexts.append('CASE_WHEN_TRUE_ONLY')
    if len(control_path) >= 2 and control_path[-2] == 'cond':
        if 'PLpgSQL_stmt_if' in control_path or 'PLpgSQL_if_elsif' in control_path:
            contexts.append('PLPGSQL_IF_TRUE_ONLY; FALSE_AND_UNKNOWN_FALLTHROUGH')
    if not contexts:
        contexts.append('VALUE_OR_RETURN; NULLABILITY_AND_CONSUMER_PENDING')
    return contexts


def exact_rule(kind, node):
    if kind == 'BoolExpr':
        op = node.get('boolop')
        return {
            'AND_EXPR': ('AND_3VL', 'TRUE iff every operand TRUE', 'FALSE iff any operand FALSE', 'UNKNOWN otherwise'),
            'OR_EXPR': ('OR_3VL', 'TRUE iff any operand TRUE', 'FALSE iff every operand FALSE', 'UNKNOWN otherwise'),
            'NOT_EXPR': ('NOT_3VL', 'TRUE when operand FALSE', 'FALSE when operand TRUE', 'UNKNOWN when operand UNKNOWN'),
        }.get(op, ('UNRESOLVED_BOOL_FORM', 'UNRESOLVED', 'UNRESOLVED', 'UNRESOLVED'))
    if kind == 'NullTest':
        op = node['nulltesttype']
        return (op + '_SCALAR_OR_ROW_REVIEW',
                'Scalar: TRUE for NULL' if op == 'IS_NULL' else 'Scalar: TRUE for non-NULL',
                'Scalar: FALSE for non-NULL' if op == 'IS_NULL' else 'Scalar: FALSE for NULL',
                'Never UNKNOWN; a composite with mixed NULL fields can make both IS NULL and IS NOT NULL false')
    if kind == 'BooleanTest':
        op = node['booltesttype']
        return (op, 'Explicit boolean test has a two-valued TRUE result by its named input case',
                'Other input cases are FALSE', 'Never UNKNOWN')
    if kind == 'CaseExpr':
        return ('SEARCHED_OR_SIMPLE_CASE', 'First matching WHEN TRUE selects branch',
                'FALSE selects later WHEN/ELSE', 'UNKNOWN selects later WHEN/ELSE; result may itself be NULL')
    if kind == 'CoalesceExpr':
        return ('COALESCE_VALUE', 'Returns first non-NULL value', 'No non-NULL operand yields NULL',
                'Predicate TRUE/FALSE/UNKNOWN depends on result type and enclosing consumer')
    if kind == 'SubLink':
        op = node['subLinkType']
        if op == 'EXISTS_SUBLINK':
            return ('EXISTS', 'TRUE if subquery has at least one row, even if projected value NULL',
                    'FALSE for no rows', 'Never UNKNOWN; NOT EXISTS is enclosing NOT, not scalar-subquery behavior')
        if op == 'EXPR_SUBLINK':
            return ('SCALAR_SUBQUERY', 'One row returns its projected value, which may be TRUE',
                    'One row may return FALSE; more than one row errors',
                    'Zero rows yields NULL; one projected NULL yields NULL; downstream predicate may be UNKNOWN')
        return (op, 'Depends on exact operator, row count and quantified comparison',
                'Empty ANY is FALSE; empty ALL is TRUE when this sublink kind applies',
                'NULL array/row/element behavior requires exact operator strictness')
    if kind == 'A_Expr':
        op = node.get('kind')
        names = strings(node.get('name', []))
        if op in ('AEXPR_DISTINCT', 'AEXPR_NOT_DISTINCT'):
            return (op, 'Null-safe comparison; equality of two NULLs follows distinct/not-distinct polarity',
                    'Null against non-NULL follows opposite polarity', 'Never UNKNOWN, including row-valued null-safe comparison')
        if op == 'AEXPR_IN':
            if names == ['<>']:
                return ('NOT_IN', 'TRUE if no equality match and no UNKNOWN comparison; empty NOT IN is TRUE',
                        'FALSE if any equality match', 'UNKNOWN if no match but a NULL/UNKNOWN comparison occurs')
            if names == ['=']:
                return ('IN', 'TRUE if any equality match',
                        'FALSE if no match and no UNKNOWN comparison; empty IN is FALSE',
                        'UNKNOWN if no match but a NULL/UNKNOWN comparison occurs')
            return ('UNRESOLVED_IN_OPERATOR:' + '.'.join(names), 'UNRESOLVED', 'UNRESOLVED', 'UNRESOLVED')
        if op in ('AEXPR_OP_ANY', 'AEXPR_OP_ALL'):
            return (op, 'ANY TRUE on any TRUE comparison; ALL TRUE only if all TRUE or empty',
                    'ANY FALSE on all FALSE or empty; ALL FALSE on any FALSE',
                    'Otherwise UNKNOWN, including NULL array; exact operator strictness remains separate')
        if op in ('AEXPR_BETWEEN', 'AEXPR_NOT_BETWEEN'):
            return (op, 'BETWEEN combines >= and <= with AND; NOT BETWEEN negates that grouped result',
                    'FALSE follows the grouped comparisons', 'UNKNOWN follows three-valued grouped comparisons')
        if op == 'AEXPR_NULLIF':
            return ('NULLIF_VALUE', 'Returns first input if equality is not TRUE',
                    'Returns NULL if equality TRUE', 'Equality UNKNOWN returns first input; result NULLability follows input')
        return (op + ':' + '.'.join(names),
                'Comparison TRUE depends on exact operator and non-NULL operand values',
                'Comparison FALSE depends on exact operator and non-NULL operand values',
                'Strict comparison with NULL operand is UNKNOWN; operator strictness/overload still requires proof')
    raise ValueError(kind)


def main():
    OUTPUT.mkdir(exist_ok=True)
    nodes = {}
    control_paths = {}
    for path in sorted(SOURCE.glob('*.json')):
        if path.name == 'EXPANDED-SOURCE-GRAPH.json':
            continue
        function = read(path)
        signature = function['function']['signature']
        for statement in function['statements']:
            key = (signature, statement['ordinal'])
            control_paths[key] = statement.get('control_ast_path', [])
            for kind, node, ast_path in walk(statement['ast']):
                if kind in ['BoolExpr', 'NullTest', 'BooleanTest', 'A_Expr', 'SubLink', 'CaseExpr', 'CoalesceExpr']:
                    nodes[(key, tuple(ast_path))] = (kind, node)
    rows = []
    previous = read(PREVIOUS)
    for old in previous:
        signature = old['source_function']
        ordinal = old['statement_ordinal']
        ast_path = tuple(old['ast_path'])
        kind, node = nodes[((signature, ordinal), ast_path)]
        assert kind == old['node_kind']
        rule, true_behavior, false_behavior, unknown_behavior = exact_rule(kind, node)
        control = control_paths[(signature, ordinal)]
        contexts = actual_consumer(ast_path, control)
        item_id = hashlib.sha256(json.dumps([signature, ordinal, ast_path], separators=(',', ':'), default=list).encode()).hexdigest()[:24]
        rows.append({
            'ITEM_ID': item_id, 'SOURCE_OBJECT': signature, 'SOURCE_PROVENANCE': old['source'],
            'STATEMENT_ORDINAL': ordinal, 'AST_PATH': list(ast_path), 'CONTROL_PATH': control,
            'NODE_TYPE': kind, 'OPERATOR_FORM': rule,
            'SUBLINK_TYPE_IF_ANY': node.get('subLinkType') if kind == 'SubLink' else None,
            'TRUE_BEHAVIOR': true_behavior, 'FALSE_BEHAVIOR': false_behavior,
            'UNKNOWN_BEHAVIOR': unknown_behavior, 'EXACT_CONSUMER_CONTEXT': contexts,
            'AUTHORITY_EFFECT': 'PENDING_GROUPED_AUTHORITY_DATAFLOW',
            'STATE_EFFECT': 'PENDING_DML_OR_RETURN_CONSUMER_DATAFLOW',
            'FAIL_CLOSED_EFFECT': 'PENDING_COMPLETE_ACCEPTANCE_PATH_AND_RUNTIME_BOUNDARY',
            'RULE_MAPPING_STATUS': 'EXACT_AST_FORM_MAPPED', 'GOVERNED_SEMANTICS_COMPLETE': False,
            'PROOF_PATHS': ['STATIC_SOURCE_PROOF', 'EXECUTABLE_SQL_NEGATIVE', 'CONSTRAINT_FAILURE'],
        })
    assert len(rows) == len(previous) == 18450
    previous_if = sum('IF_TRUE_BRANCH_FALSE_OR_UNKNOWN_FALLTHROUGH' in r['exact_consumer_contexts'] for r in previous)
    exact_if = sum('PLPGSQL_IF_TRUE_ONLY; FALSE_AND_UNKNOWN_FALLTHROUGH' in r['EXACT_CONSUMER_CONTEXT'] for r in rows)
    assert exact_if <= previous_if
    with (OUTPUT / 'NULL-EXACT-CONSUMERS.json').open('w', encoding='utf-8', newline='\n') as file:
        json.dump(rows, file, sort_keys=True, separators=(',', ':'))
        file.write('\n')
    status = {
        'NULL_SENSITIVE_AST_CANDIDATE_N': len(rows), 'RULE_FORM_MAPPED_N': len(rows),
        'PREVIOUS_IF_CONTEXT_N': previous_if, 'EXACT_IF_CONDITION_CONTEXT_N': exact_if,
        'FALSE_IF_CONTEXT_CLASSIFICATION_REMOVED_N': previous_if - exact_if,
        'SUBLINK_TYPE_COUNTS': dict(collections.Counter(r['SUBLINK_TYPE_IF_ANY'] for r in rows if r['SUBLINK_TYPE_IF_ANY'])),
        'NULL_SENSITIVE_GOVERNED_ITEM_N': 'UNKNOWN_UNTIL_UNIQUE_SEMANTIC_LEDGER',
        'NULL_SEMANTICS_COMPLETE_N': 0, 'NULL_SEMANTICS_UNRESOLVED_N': 'UNKNOWN_GOVERNED_DENOMINATOR',
        'NULL_SEMANTICS_MISMATCH_N': 'UNKNOWN_NOT_ZERO_CLAIM',
        'RULE_MAPPING_IS_NOT_AUTHORITY_OR_STATE_SAFETY': True,
    }
    (OUTPUT / 'NULL-EXACT-STATUS.json').write_text(json.dumps(status, indent=2, sort_keys=True) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(status))


if __name__ == '__main__':
    main()
