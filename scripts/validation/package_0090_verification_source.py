"""Exact V wrappers plus independent per-column/effect/function review."""
import json
import re
import package_0090_source_gate as gate
from build_package_0090_verification_source import WRAPPERS,FROZEN,TYPES,OWNER,build_one,grants
from package_0090_capability_source import strings

def check(fn,expected_columns,source,composition=None):
    from pglast.parser import parse_sql_json
    import pglast
    name=strings(fn['funcname'])[-1]
    wrappers=composition.WRAPPERS if composition else WRAPPERS
    owner=composition.OWNER if composition else OWNER
    generator=composition.build_one if composition else build_one
    stage=next(s for s,n in wrappers.items() if n==name)
    spec=(gate.ROOT/gate.SPEC).read_text(encoding='utf-8-sig')
    reference=json.loads(parse_sql_json(generator(source,spec,stage)))['stmts'][0]['stmt']['CreateFunctionStmt']
    def clean(v):
        if isinstance(v,list):return [clean(x) for x in v]
        if isinstance(v,dict):return {k:clean(x) for k,x in v.items() if k!='location'}
        return v
    if clean(fn)!=clean(reference):raise ValueError('Exact '+stage+' guarded frozen composition changed')
    expressions=[]
    def collect(v):
        if isinstance(v,list):
            for x in v:collect(x)
        elif isinstance(v,dict):
            if any(k in v for k in ['PLpgSQL_stmt_dynexecute','PLpgSQL_stmt_commit','PLpgSQL_stmt_rollback','PLpgSQL_stmt_return_query','PLpgSQL_stmt_return_next']):raise ValueError('V dynamic/transaction/set effect forbidden')
            if 'PLpgSQL_expr' in v:expressions.append(v['PLpgSQL_expr']['query'])
            for x in v.values():collect(x)
    collect(pglast.parse_plpgsql(generator(source,spec,stage)))
    privileges={(r,c,p) for o,r,c,p in expected_columns if o==owner}
    observed=set()
    from package_0090_q_source import BUILTINS
    builtins=BUILTINS|{'int2send','decode','encode','to_char','timezone','gen_random_uuid','num_nonnulls'}
    calls={('public',n) for n in FROZEN.values()}|{('public','offline_internal_matches_original_signed_attestation'),('public','offline_internal_canonical_spki_ed25519_verify')}
    if composition:calls={('public',n) for n in composition.FROZEN.values()}
    def review(v,inherited=None):
        if isinstance(v,list):
            for x in v:review(x,inherited)
        elif isinstance(v,dict):
            aliases=dict(inherited or {})
            if 'SelectStmt' in v:
                stmt=v['SelectStmt']
                if stmt.get('intoClause'):raise ValueError('V SELECT INTO table forbidden')
                for item in stmt.get('fromClause',[]):
                    if 'RangeVar' in item:
                        r=item['RangeVar'];aliases[r.get('alias',{}).get('aliasname',r['relname'])]=r.get('schemaname','')+'.'+r['relname']
            for key,priv in [('InsertStmt','insert'),('UpdateStmt','update')]:
                if key in v:
                    stmt=v[key];r=stmt['relation'];relation=r.get('schemaname','')+'.'+r['relname']
                    mutable=stage in ('S06','S08','S10','S12')
                    allowed_effects={'public.offline_stage_receipt','public.offline_attempt'} | ({'public.offline_delivery'} if stage=='S10' else set())
                    if not mutable or relation not in allowed_effects:raise ValueError('V unapproved semantic effect')
                    targets=stmt.get('cols',stmt.get('targetList',[]))
                    for item in targets:
                        column=item['ResTarget']['name']
                        if (relation,column,priv) not in privileges:raise ValueError('V unapproved column effect')
                    aliases[r.get('alias',{}).get('aliasname',r['relname'])]=relation
            if 'ColumnRef' in v:
                fields=strings(v['ColumnRef']['fields'])
                if len(fields)==2 and fields[0] in aliases:
                    pair=(aliases[fields[0]],fields[1]);observed.add(pair)
                    if pair[0].startswith('public.') and (*pair,'select') not in privileges:raise ValueError('V unapproved read '+repr(pair))
            if 'FuncCall' in v:
                call=strings(v['FuncCall']['funcname'])
                if call not in calls and call not in {('pg_catalog',n) for n in builtins}:raise ValueError('V unapproved function '+repr(call))
            for x in v.values():review(x,aliases)
    for expression in expressions:
        query=re.sub(r'^\s*[a-z_][a-z0-9_]*(?:\[[^]]+\])?\s*:=\s*','',expression,flags=re.I)
        if not query.lstrip().upper().startswith(('SELECT','WITH','INSERT','UPDATE')):query='SELECT '+query
        for item in json.loads(parse_sql_json(query))['stmts']:
            if not set(item['stmt'])<={'SelectStmt','InsertStmt','UpdateStmt'}:raise ValueError('V unsupported SQL effect')
            review(item['stmt'])
    return {stage.lower()+'_source':'BOUNDED_STATIC_PASS_NOT_RUNTIME_PROOF',stage.lower()+'_read_columns':len(observed),stage.lower()+('_verified_v_lineage_before_frozen' if composition else '_original_match_before_frozen'):True}
