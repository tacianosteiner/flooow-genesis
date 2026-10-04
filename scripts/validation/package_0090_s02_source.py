"""S02 exact source/data-authority review; never claims database execution."""
import json
import re
from build_package_0090_s02_source import NAME, build
from build_package_0090_read_source import TYPES, OWNER
from package_0090_capability_source import strings

GRANTS={('public','transaction_identity_grant_fingerprint',('uuid','uuid'),OWNER),
        ('public','transaction_identity_hash',('text[]',),OWNER)}

def check(fn,expected_columns,source, generator=build, additional_calls=frozenset()):
    import pglast
    from pglast.parser import parse_sql_json
    def clean(v):
        if isinstance(v,list):return [clean(x) for x in v]
        if isinstance(v,dict):return {k:clean(x) for k,x in v.items() if k!='location'}
        return v
    reference=json.loads(parse_sql_json(generator(source)))['stmts'][0]['stmt']['CreateFunctionStmt']
    if clean(fn)!=clean(reference):raise ValueError('S02 exact independent-input/frozen-predicate/guard/output changed')
    expressions=[]
    def walk(v):
        if isinstance(v,list):
            for x in v:walk(x)
        elif isinstance(v,dict):
            if any(k in v for k in ('PLpgSQL_stmt_dynexecute','PLpgSQL_stmt_commit','PLpgSQL_stmt_rollback','PLpgSQL_stmt_return_query','PLpgSQL_stmt_return_next')):
                raise ValueError('S02 dynamic SQL/mutation/set return forbidden')
            if 'PLpgSQL_expr' in v:expressions.append(v['PLpgSQL_expr']['query'])
            for x in v.values():walk(x)
    walk(pglast.parse_plpgsql(generator(source)))
    allowed={(r,c) for o,r,c,p in expected_columns if o==OWNER and p=='select'}
    observed=set()
    from package_0090_q_source import BUILTINS
    builtins=BUILTINS|{'int2send','decode','encode','to_char','bool_and','timezone'}
    calls={('public','offline_internal_readiness'),('public','offline_internal_verify_authority_intent'),
           ('public','offline_internal_canonical_spki_ed25519_verify'),('public','transaction_identity_grant_fingerprint')}
    calls |= additional_calls
    def aliases_in(v,aliases):
        if isinstance(v,list):
            for x in v:aliases_in(x,aliases)
        elif isinstance(v,dict):
            if 'RangeVar' in v:
                r=v['RangeVar'];schema=r.get('schemaname')
                if schema not in ('public','pg_catalog'):raise ValueError('S02 unqualified relation')
                aliases[r.get('alias',{}).get('aliasname',r['relname'])]=schema+'.'+r['relname']
            if 'JoinExpr' in v:aliases_in(v['JoinExpr'],aliases)
            for k in ('larg','rarg'): 
                if k in v:aliases_in(v[k],aliases)
    def review(v,inherited=None):
        if isinstance(v,list):
            for x in v:review(x,inherited)
        elif isinstance(v,dict):
            aliases=dict(inherited or {})
            if 'SelectStmt' in v:
                stmt=v['SelectStmt']
                if stmt.get('lockingClause') or stmt.get('intoClause'):raise ValueError('S02 write lock/creation forbidden')
                aliases_in(stmt.get('fromClause',[]),aliases)
            if 'ColumnRef' in v:
                f=strings(v['ColumnRef']['fields'])
                if len(f)==2 and f[0] in aliases:
                    item=(aliases[f[0]],f[1]);observed.add(item)
                    if item[0].startswith('public.') and item not in allowed:raise ValueError('S02 unapproved read '+repr(item))
            if 'FuncCall' in v:
                name=strings(v['FuncCall']['funcname'])
                if name not in calls and name not in {('pg_catalog',n) for n in builtins}:raise ValueError('S02 unapproved call '+repr(name))
            for x in v.values():review(x,aliases)
    for expression in expressions:
        query=re.sub(r'^\s*[a-z_][a-z0-9_]*(?:\[[^]]+\])?\s*:=\s*','',expression,flags=re.I)
        query=query if query.lstrip().upper().startswith(('SELECT','WITH')) else 'SELECT '+query
        for item in json.loads(parse_sql_json(query))['stmts']:
            if set(item['stmt'])!={'SelectStmt'}:raise ValueError('S02 DML/DDL forbidden')
            review(item['stmt'])
    return {'s02_source':'BOUNDED_STATIC_PASS_NOT_RUNTIME_PROOF','s02_read_columns':len(observed),
            's02_expected_original_input':'EXACT_COMPARISONS','s02_signature_changed':False,'s02_output_changed':False}
