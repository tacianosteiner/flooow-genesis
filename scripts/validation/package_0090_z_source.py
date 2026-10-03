"""Bounded static Z review. No installed/runtime safety claim or database I/O."""
import json
import re

from package_0090_capability_source import BUILTINS, strings

NAME = 'offline_internal_verify_authority_intent'
OWNER = 'flooow_offline_intent_audit_owner'
TYPES = ('uuid', 'bytea', 'uuid', 'text')
NAMES = ('binding_id', 'plan_fingerprint', 'expected_incarnation_id', 'surface_version')
GRANTS = {
    ('public', NAME, TYPES, 'flooow_offline_audit_owner'),
    ('public', 's2a_v042_authority_intent',
     ('text','uuid','uuid','uuid','uuid','uuid','uuid','bytea','uuid','text','text','uuid','uuid','text','text'), OWNER),
    ('public', 's2a_v042_authority_receipt', ('text','text','uuid','uuid','int4','uuid','int4','text','text'), OWNER),
    ('public', 's2a_v042_frame', ('bytea',), OWNER),
    ('public', 's2a_v042_text', ('text',), OWNER),
    ('public', 's2a_v042_instant', ('timestamptz',), OWNER),
}


def check(fn, expected_columns):
    from pglast.parser import parse_sql_json
    import pglast
    if fn.get('replace') or strings(fn['funcname']) != ('public', NAME):
        raise ValueError('Z exact definition identity')
    params = [p['FunctionParameter'] for p in fn['parameters']]
    expected = list(zip(NAMES, TYPES, ['FUNC_PARAM_DEFAULT']*4)) + [
        ('intent_matches','bool','FUNC_PARAM_TABLE'), ('receipt_matches','bool','FUNC_PARAM_TABLE')]
    if len(params) != 6 or any(p.get('defexpr') or
            (p['name'], strings(p['argType']['names']), p['mode']) != (n, ('pg_catalog', t), m)
            for p, (n, t, m) in zip(params, expected)):
        raise ValueError('Z exact input/output manifest')
    if strings(fn['returnType']['names']) != ('pg_catalog','record') or not fn['returnType'].get('setof'):
        raise ValueError('Z two-column TABLE result required')
    options = {o['DefElem']['defname']:o['DefElem']['arg'] for o in fn['options']}
    if (set(options) != {'language','volatility','security','strict','set','as'} or
        options['language'] != {'String':{'sval':'plpgsql'}} or
        options['volatility'] != {'String':{'sval':'stable'}} or
        options['security'] != {'Boolean':{'boolval':True}} or
        options['strict'] != {'Boolean':{'boolval':False}}):
        raise ValueError('Z security/volatility/null-call mismatch')
    setting = options['set']['VariableSetStmt']
    if setting['name'] != 'search_path' or [a['A_Const']['sval']['sval'] for a in setting['args']] != ['pg_catalog','pg_temp']:
        raise ValueError('Z fixed search path mismatch')
    body = options['as']['List']['items'][0]['String']['sval']
    pl = pglast.parse_plpgsql('CREATE FUNCTION public.'+NAME+'('+','.join(
        n+' pg_catalog.'+t for n,t in zip(NAMES,TYPES))+') RETURNS TABLE(intent_matches pg_catalog.bool,receipt_matches pg_catalog.bool) LANGUAGE plpgsql AS $body$'+body+'$body$;')
    expressions = []
    returns = []
    def walk(node):
        if isinstance(node, list):
            for child in node: walk(child)
        elif isinstance(node, dict):
            if any(k in node for k in ('PLpgSQL_stmt_dynexecute','PLpgSQL_stmt_commit','PLpgSQL_stmt_rollback','PLpgSQL_stmt_return_next')):
                raise ValueError('Z dynamic SQL/transaction control/extra return forbidden')
            if 'PLpgSQL_stmt_execsql' in node:
                query = node['PLpgSQL_stmt_execsql']['sqlstmt']['PLpgSQL_expr']['query']
                if not query.lstrip().upper().startswith('SELECT'):
                    raise ValueError('Z semantic DML/DDL forbidden')
            if 'PLpgSQL_expr' in node: expressions.append(node['PLpgSQL_expr']['query'])
            if 'PLpgSQL_stmt_return_query' in node: returns.append(node['PLpgSQL_stmt_return_query'])
            for child in node.values(): walk(child)
    walk(pl)
    if len(returns) != 1: raise ValueError('Z exact single aggregate return required')
    if not re.search(r'RETURN QUERY\s+SELECT pg_catalog.count\(\*\)=3 AND pg_catalog.bool_and\(x.intent_ok\) IS TRUE,\s*'
                     r'pg_catalog.count\(\*\)=3 AND pg_catalog.bool_and\(x.receipt_ok\) IS TRUE\s+FROM', body):
        raise ValueError('Z output must contain only aggregate match booleans')
    if body.count('c.principal_id=header_record.principal_id') != 2:
        raise ValueError('Z credential principal scope required in both canonical branches')
    allowed = {(relation, column) for owner, relation, column, privilege in expected_columns
               if owner == OWNER and privilege == 'select'}
    observed = set()
    calls = set()
    def scan(node, aliases):
        if isinstance(node, list):
            for child in node: scan(child, aliases)
        elif isinstance(node, dict):
            if 'RangeVar' in node:
                r = node['RangeVar']
                if r.get('schemaname') not in ('public','pg_catalog'):
                    raise ValueError('Z unqualified relation')
                aliases[r.get('alias',{}).get('aliasname', r['relname'])] = r['schemaname']+'.'+r['relname']
            for child in node.values(): scan(child, aliases)
    def review(node, aliases):
        if isinstance(node, list):
            for child in node: review(child, aliases)
        elif isinstance(node, dict):
            if 'ColumnRef' in node:
                fields = node['ColumnRef']['fields']
                if any('A_Star' in f for f in fields): raise ValueError('Z wildcard column projection')
                f = strings(fields)
                if len(f)==2 and f[0] in aliases:
                    item = (aliases[f[0]],f[1])
                    if item[0].startswith('public.') and item not in allowed:
                        raise ValueError('Z unapproved column: '+repr(item))
                    observed.add(item)
            if 'FuncCall' in node:
                name = strings(node['FuncCall']['funcname']); calls.add(name)
                if name not in {('public','s2a_v042_authority_intent'),('public','s2a_v042_authority_receipt')} and (
                        len(name)!=2 or name[0]!='pg_catalog' or name[1] not in BUILTINS | {'count','bool_and'}):
                    raise ValueError('Z unapproved function: '+repr(name))
                if name==('pg_catalog','current_setting'):
                    args = node['FuncCall'].get('args',[])
                    if len(args)!=1 or args[0].get('A_Const',{}).get('sval',{}).get('sval') not in ('transaction_isolation','transaction_read_only'):
                        raise ValueError('Z setting cannot supply authority/policy')
            if 'SelectStmt' in node and (node['SelectStmt'].get('lockingClause') or node['SelectStmt'].get('intoClause')):
                raise ValueError('Z write locks/relation creation forbidden')
            for child in node.values(): review(child, aliases)
    for expression in expressions:
        expression = re.sub(r'^\s*[a-z_][a-z0-9_]*(?:\[[^]]+\])?\s*:=\s*','',expression,flags=re.I)
        query = expression if expression.lstrip().upper().startswith('SELECT') else 'SELECT '+expression
        for raw in json.loads(parse_sql_json(query))['stmts']:
            if set(raw['stmt']) != {'SelectStmt'}: raise ValueError('Z semantic DML/DDL forbidden')
            aliases = {}; scan(raw['stmt'],aliases); review(raw['stmt'],aliases)
    if not {('public','s2a_v042_authority_intent'),('public','s2a_v042_authority_receipt')} <= calls:
        raise ValueError('Z frozen canonical comparisons missing')
    for required in ("slot_number=4 AND slot_name <> SESSION_USER", "FOR field_tag IN 1..29 LOOP",
                     "c.principal_id=header_record.principal_id", "g.principal_id=header_record.principal_id",
                     "pg_catalog.count(*)=3", "RETURN QUERY", "policy_values[19]",
                     "MESSAGE='INDETERMINATE'"):
        if required not in body: raise ValueError('Z required guard/comparison missing: '+required)
    return {'internal_z_source':'BOUNDED_STATIC_PASS_NOT_RUNTIME_PROOF', 'internal_z_read_columns':len(observed)}
