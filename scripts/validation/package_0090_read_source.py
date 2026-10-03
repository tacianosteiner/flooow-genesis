"""Auditor public wrapper source checks. Static proof only."""
import json
import re
from build_package_0090_read_source import TYPES,NAMES,OWNER,build
from package_0090_capability_source import strings


def check(fn,expected_columns,source):
    import pglast
    from pglast.parser import parse_sql_json
    generated=build(source)
    # Independently parse signature/properties/output vectors, then enforce
    # complete guard/projection dataflow against the frozen generated surface.
    reference=json.loads(parse_sql_json(generated))['stmts'][0]['stmt']['CreateFunctionStmt']
    def clean(node):
        if isinstance(node,list):return [clean(v) for v in node]
        if isinstance(node,dict):return {k:clean(v) for k,v in node.items() if k!='location'}
        return node
    if clean(fn)!=clean(reference):raise ValueError('S04 exact signature/guard/projection changed')
    body=next(o['DefElem']['arg']['List']['items'][0]['String']['sval'] for o in fn['options'] if o['DefElem']['defname']=='as')
    pl=pglast.parse_plpgsql(generated)
    expressions=[];queries=[]
    def walk(node):
        if isinstance(node,list):
            for child in node:walk(child)
        elif isinstance(node,dict):
            if any(k in node for k in ('PLpgSQL_stmt_dynexecute','PLpgSQL_stmt_commit','PLpgSQL_stmt_rollback','PLpgSQL_stmt_return_next')):
                raise ValueError('S04 dynamic SQL/transaction forbidden')
            if 'PLpgSQL_expr' in node:expressions.append(node['PLpgSQL_expr']['query'])
            if 'PLpgSQL_stmt_return_query' in node:
                r=node['PLpgSQL_stmt_return_query']
                if r.get('dynquery'):raise ValueError('S04 dynamic return forbidden')
                queries.append(r['query']['PLpgSQL_expr']['query'])
            for child in node.values():walk(child)
    walk(pl)
    if len(queries)!=1 or queries[0].strip()!='SELECT h.installed_rank,h.version,h.type,h.script,h.checksum,h.success\n      FROM public.flyway_schema_history h ORDER BY h.installed_rank':
        raise ValueError('S04 complete ordered history projection required')
    allowed={(r,c) for o,r,c,p in expected_columns if o==OWNER and p=='select'}
    observed=set()
    from package_0090_q_source import BUILTINS
    def review(node, inherited=None):
        if isinstance(node,list):
            for child in node:review(child,inherited)
        elif isinstance(node,dict):
            aliases=dict(inherited or {})
            if 'SelectStmt' in node:
                stmt=node['SelectStmt']
                if stmt.get('lockingClause') or stmt.get('intoClause'):raise ValueError('S04 write locks/creation forbidden')
                for entry in stmt.get('fromClause',[]):
                    if 'RangeVar' in entry:
                        r=entry['RangeVar'];schema=r.get('schemaname')
                        if schema not in ('public','pg_catalog'):raise ValueError('S04 unqualified relation')
                        aliases[r.get('alias',{}).get('aliasname',r['relname'])]=schema+'.'+r['relname']
            if 'ColumnRef' in node:
                f=strings(node['ColumnRef']['fields'])
                if len(f)==2 and f[0] in aliases:
                    item=(aliases[f[0]],f[1]);observed.add(item)
                    if item[0].startswith('public.') and item not in allowed:raise ValueError('S04 unapproved read '+repr(item))
            if 'FuncCall' in node:
                name=strings(node['FuncCall']['funcname'])
                if name not in {('pg_catalog',n) for n in BUILTINS}:raise ValueError('S04 unapproved callable '+repr(name))
            for child in node.values():review(child,aliases)
    for expression in expressions:
        expression=re.sub(r'^\s*[a-z_][a-z0-9_]*(?:\[[^]]+\])?\s*:=\s*','',expression,flags=re.I)
        query=expression if expression.lstrip().upper().startswith('SELECT') else 'SELECT '+expression
        for raw in json.loads(parse_sql_json(query))['stmts']:
            if set(raw['stmt'])!={'SelectStmt'}:raise ValueError('S04 DML/DDL forbidden')
            review(raw['stmt'])
    return dict(s04_source='BOUNDED_STATIC_PASS_NOT_RUNTIME_PROOF',s04_complete_ordered_history=True,s04_no_write_locks=True)
