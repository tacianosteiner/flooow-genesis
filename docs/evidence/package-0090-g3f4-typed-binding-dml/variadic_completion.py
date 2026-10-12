"""Finish the 17 currently known variadic source sites, not implicit scope."""
import collections,hashlib,json
from source_binding import read,walk,strings,BASE,ROOT,OUT
from identifier_rebinding import Resolver,RESULT
from catalog_metadata import records

def main():
    old=ROOT/'docs/evidence/package-0090-g3f4-authority-boundary-typed'
    sites=[x for x in read(BASE/'CALL-EDGE-REVIEW.json')['calls_without_cached_source_target'] if x['source_spelling'] in ['num_nonnulls','pg_catalog.num_nonnulls']]
    functions={read(p)['signature']:read(p) for p in (old/'functions').glob('*.json')}
    wanted={s['caller'] for s in sites};grouped=collections.defaultdict(list)
    for ref in sorted((old/'final-03/statements').glob('*.reference.json')):
        r=read(ref);data=(ROOT/r['artifact']).read_bytes();assert hashlib.sha256(data).hexdigest()==r['sha256']
        for s in json.loads(data):
            if s['SQL_OBJECT'] in wanted:grouped[s['SQL_OBJECT']].append(s)
    builtin=next(x for x in records((OUT/'pg18.4/pg_proc.dat').read_text()) if x.get('proname')=='num_nonnulls')
    resolvers={}
    for sig in wanted:
        r=Resolver(functions[sig]);r.discover_records(grouped[sig]);resolvers[sig]=r
    resolved=[]
    for site in sites:
        f=functions[site['caller']];r=resolvers[site['caller']];ordinal=int(site['statement_id'].rsplit(':S',1)[1])
        r.use_path=tuple(f['expressions'][ordinal]['ast_path'])
        s=next(x for x in grouped[site['caller']] if x['SQL_STATEMENT_ID']==site['statement_id']);node=s['ast']
        for step in site['ast_path']:node=node[step]
        types=[r.typ(arg,[]) for arg in node['args']]
        explicit=bool(node.get('func_variadic'));complete='UNRESOLVED' not in types and not explicit
        resolved.append({'CALL_SITE_ID':hashlib.sha256((site['statement_id']+str(site['ast_path'])).encode()).hexdigest()[:24],
                         'CALLER':site['caller'],'CALLEE':'pg_catalog.num_nonnulls(VARIADIC any)',
                         'ARGUMENT_COUNT':len(types),'FIXED_ARGUMENT_N':0,'VARIADIC_ARGUMENT_N':len(types),
                         'ARGUMENT_TYPES':types,'PARAMETER_TYPES':['any'],'EXPANSION_RULE':'VARIADIC any accepts mixed scalar argument types without a homogeneous-array coercion; count null flags.',
                         'OVERLOAD_RESOLUTION':'Exact pg_catalog qualification; unique REL_18_4 num_nonnulls declaration.',
                         'CASTS':'No function-required common scalar cast; explicit casts inside argument expressions remain part of caller.',
                         'NULLABILITY':'Accept NULL arguments; result is count of non-NULL inputs; absent explicit VARIADIC array here.',
                         'ARRAY_EXPANSION_IF_ANY':'NO' if not explicit else 'UNRESOLVED_EXPLICIT_ARRAY_CASE',
                         'SOURCE_SPAN':{'file':f['source'],'object':site['caller'],'statement_ordinal':ordinal,
                                        'statement_sha256':hashlib.sha256(s['query'].encode()).hexdigest(),'object_hash':f['definition_sha256']},
                         'CALLEE_SPAN':{'file':'continuation-02/pg18.4/pg_proc.dat','start_offset':builtin['_source_start'],'end_offset':builtin['_source_end'],
                                        'declaration_sha256':hashlib.sha256(builtin['_raw'].encode()).hexdigest()},
                         'SUCCESSOR_HASH':'6ad78ba61d70e803d2a878034aa7988b69b6374568f96949b2ef6c8defc7a8c7',
                         'SEMANTIC_EFFECT':'Integer null-cardinality guard; do not treat participant presence as completed work.',
                         'AUTHORITY_RELEVANT':True,'RESOLUTION_STATUS':'PROVEN_FROZEN_SOURCE_VARIADIC_BINDING' if complete else 'REAL_UNRESOLVED_GAP'})
    earlier=read(OUT/'VARIADIC-BINDINGS.json')['sites'];combined=earlier+resolved
    summary={'VARIADIC_CALL_SITE_N':len(combined),'VARIADIC_RESOLVED_N':sum(x['RESOLUTION_STATUS']=='PROVEN_FROZEN_SOURCE_VARIADIC_BINDING' for x in combined),
             'VARIADIC_UNRESOLVED_N':sum(x['RESOLUTION_STATUS']!='PROVEN_FROZEN_SOURCE_VARIADIC_BINDING' for x in combined),
             'scope':'CURRENT_54_CACHED_FUNCTIONS; trigger/default/FK expansion can add further sites',
             'complete_execution_reachability':False,'sites':combined}
    (RESULT/'VARIADIC-CURRENT-SCOPE.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='sites'}))

if __name__=='__main__':main()
