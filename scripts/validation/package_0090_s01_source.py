"""Bounded S01 SQL/PLpgSQL authority review; never a runtime certificate."""
import json
import re
from build_package_0090_s01_source import NAMES, TYPES, build, bound_target
from package_0090_capability_source import strings

NAME='offline_preflight'
OWNER='flooow_offline_audit_owner'


def check(fn, expected_columns, source):
    import pglast
    from pglast.parser import parse_sql_json
    params=[p['FunctionParameter'] for p in fn['parameters']]
    if fn.get('replace') or len(params)!=7 or any(p.get('defexpr') or p['mode']!='FUNC_PARAM_DEFAULT'
        or p['name']!=n or strings(p['argType']['names'])!=('pg_catalog',t)
        for p,n,t in zip(params,NAMES,TYPES)):
        raise ValueError('S01 exact mandatory seven-argument signature')
    if strings(fn['returnType']['names'])!=('pg_catalog','bytea') or fn['returnType'].get('setof'):
        raise ValueError('S01 exact scalar bytea return')
    opts={o['DefElem']['defname']:o['DefElem']['arg'] for o in fn['options']}
    if set(opts)!={'language','volatility','security','strict','set','as'} or any(opts[k]!=v for k,v in {
        'language':{'String':{'sval':'plpgsql'}},'volatility':{'String':{'sval':'stable'}},
        'security':{'Boolean':{'boolval':True}},'strict':{'Boolean':{'boolval':False}}}.items()):
        raise ValueError('S01 STABLE/definer/null-call properties')
    setting=opts['set']['VariableSetStmt']
    if setting['name']!='search_path' or [a['A_Const']['sval']['sval'] for a in setting['args']]!=['pg_catalog','pg_temp']:
        raise ValueError('S01 fixed search_path')
    body=opts['as']['List']['items'][0]['String']['sval']
    # Rebuild from reviewed P guard and current frozen producer. This checks the
    # complete guard/predicate/denial/Q return sequence, beyond token presence.
    expected=build(source).split('AS $offline_s01$',1)[1].split('$offline_s01$;',1)[0]
    if body!=expected: raise ValueError('S01 exact guard/predicate/Q dataflow changed')
    pl=pglast.parse_plpgsql('CREATE FUNCTION public.'+NAME+'('+','.join(n+' pg_catalog.'+t for n,t in zip(NAMES,TYPES))+') RETURNS pg_catalog.bytea LANGUAGE plpgsql AS $b$'+body+'$b$;')
    expressions=[];returns=[]
    def walk(node):
        if isinstance(node,list):
            for child in node:walk(child)
        elif isinstance(node,dict):
            if any(k in node for k in ('PLpgSQL_stmt_dynexecute','PLpgSQL_stmt_commit','PLpgSQL_stmt_rollback','PLpgSQL_stmt_return_query','PLpgSQL_stmt_return_next')):
                raise ValueError('S01 dynamic SQL/transaction/set return forbidden')
            if 'PLpgSQL_expr' in node: expressions.append(node['PLpgSQL_expr']['query'])
            if 'PLpgSQL_stmt_return' in node and 'expr' in node['PLpgSQL_stmt_return']:returns.append(node['PLpgSQL_stmt_return']['expr']['PLpgSQL_expr']['query'])
            for child in node.values():walk(child)
    walk(pl)
    from package_0090_s01_readiness import Q_SENTINEL_SQL, target_columns
    if returns!=[Q_SENTINEL_SQL]:raise ValueError('S01 sole Q sentinel return')
    allowed={(r,c) for o,r,c,p in expected_columns if o==OWNER and p=='select'}
    observed=set(); calls=set()
    from package_0090_q_source import BUILTINS
    builtins=BUILTINS|{'bool_and'}
    def review(node, inherited=None):
        if isinstance(node,list):
            for child in node:review(child,inherited)
        elif isinstance(node,dict):
            aliases=dict(inherited or {})
            if 'SelectStmt' in node:
                stmt=node['SelectStmt']
                if stmt.get('lockingClause') or stmt.get('intoClause'):raise ValueError('S01 write locks/relation creation forbidden')
                def bind(v):
                    if isinstance(v,list):
                        for c in v:bind(c)
                    elif isinstance(v,dict):
                        if 'RangeVar' in v:
                            r=v['RangeVar']; schema=r.get('schemaname')
                            if schema not in ('public','pg_catalog'):raise ValueError('S01 unqualified relation')
                            aliases[r.get('alias',{}).get('aliasname',r['relname'])]=schema+'.'+r['relname']
                        elif 'RangeSubselect' not in v:
                            for c in v.values():bind(c)
                bind(stmt.get('fromClause',[]))
            if 'ColumnRef' in node:
                fields=node['ColumnRef']['fields']
                if any('A_Star' in f for f in fields):return
                f=strings(fields)
                if len(f)==2 and f[0] in aliases:
                    item=(aliases[f[0]],f[1]);observed.add(item)
                    if item[0].startswith('public.') and item not in allowed:raise ValueError('S01 unapproved column '+repr(item))
            if 'JoinExpr' in node:
                for f in node['JoinExpr'].get('usingClause',[]):
                    for r in ('public.integration_omie_transaction_evidence','public.integration_omie_transaction_evidence_v3'):
                        item=(r,f['String']['sval']); observed.add(item)
                        if item not in allowed:raise ValueError('S01 unapproved USING read')
            if 'FuncCall' in node:
                name=strings(node['FuncCall']['funcname']);calls.add(name)
                if name not in {('pg_catalog',n) for n in builtins}|{('public','offline_internal_readiness')}:
                    raise ValueError('S01 unapproved callable '+repr(name))
            for child in node.values():review(child,aliases)
    for expression in expressions:
        expression=re.sub(r'^\s*[a-z_][a-z0-9_]*(?:\[[^]]+\])?\s*:=\s*','',expression,flags=re.I)
        query=expression if expression.lstrip().upper().startswith('SELECT') else 'SELECT '+expression
        for raw in json.loads(parse_sql_json(query))['stmts']:
            if set(raw['stmt'])!={'SelectStmt'}:raise ValueError('S01 DML/DDL forbidden')
            review(raw['stmt'])
    if not target_columns()<=observed:raise ValueError('S01 frozen target column closure missing')
    return dict(s01_source='BOUNDED_STATIC_PASS_NOT_RUNTIME_PROOF',s01_target_predicate='EXACT_FROZEN_JOIN',
                s01_read_columns=len(observed),s01_q_sentinel_delegation=True,s01_no_write_locks=True)
