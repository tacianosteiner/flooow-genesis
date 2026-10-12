"""Recompute structural bindings from the frozen 68-function source expansion.
No SQL execution and no promotion of identifier counts into semantic closure.
"""
import collections, hashlib, json, sys
from source_binding import BASE,ROOT,read,walk,strings,typename
import identifier_rebinding as binding
OUT=BASE/'continuation-07'
INPUT=BASE/'continuation-05'
def dump(name,data):
    (OUT/name).write_text(json.dumps(data,separators=(',',':'),sort_keys=True)+'\n',encoding='utf-8',newline='\n')
class ExpandedResolver(binding.Resolver):
    def __init__(self,f):
        super().__init__(f);self.calls=[]
    def references(self,node,scopes,path=()):
        if isinstance(node,dict) and 'FuncCall' in node:
            c=node['FuncCall'];name='.'.join(strings(c['funcname']))
            if name in ['transaction_identity_hash','public.transaction_identity_hash','pg_catalog.num_nonnulls']:
                self.calls.append({'path':list(path),'callee_spelling':name,'actual_types':[self.typ(x,scopes) for x in c.get('args',[])],
                                   'explicit_variadic_array':bool(c.get('func_variadic')),'argument_ast':c.get('args',[])})
        yield from super().references(node,scopes,path)

def main(parser_path):
    sys.path.insert(0,parser_path)
    from pglast.parser import parse_plpgsql_json
    OUT.mkdir(exist_ok=True)
    old=ROOT/'docs/evidence/package-0090-g3f4-authority-boundary-typed/functions'
    cached={read(p)['signature']:read(p) for p in old.glob('*.json')}
    expanded={read(p)['function']['signature']:read(p) for p in INPUT.glob('*.json') if p.name!='EXPANDED-SOURCE-GRAPH.json'}
    graph=read(INPUT/'EXPANDED-SOURCE-GRAPH.json')
    expanded_byname=collections.defaultdict(list)
    for sig,item in expanded.items():
        d=item['original_definition'];params=[x['FunctionParameter'] for x in d.get('parameters',[]) if x['FunctionParameter'].get('mode') not in ['FUNC_PARAM_OUT','FUNC_PARAM_TABLE']]
        meta={'name':sig.split('(')[0],'parameters':params,'return_type':typename(d['returnType']),
              'output_fields':{x['FunctionParameter']['name']:typename(x['FunctionParameter']['argType']) for x in d.get('parameters',[]) if x['FunctionParameter'].get('mode') in ['FUNC_PARAM_OUT','FUNC_PARAM_TABLE','FUNC_PARAM_INOUT']}}
        expanded_byname[meta['name']].append(meta)
    for name,options in expanded_byname.items():binding.BYNAME[name]=options
    records=[];variadics=[];functions={};resolvers={};grouped={}
    for sig,item in expanded.items():
        d=item['original_definition'];params=[x['FunctionParameter'] for x in d.get('parameters',[]) if x['FunctionParameter'].get('mode') not in ['FUNC_PARAM_OUT','FUNC_PARAM_TABLE']]
        f=cached.get(sig)
        if f is None:
            # New PL bodies are parsed directly from their original definition;
            # the declaration text is recovered from exact original source bytes.
            f={'signature':sig,'language':item['function']['language'],'parameter_names':[x.get('name') for x in params],'parameter_types':[typename(x['argType']) for x in params]}
            if f['language']=='plpgsql':
                src=item['function']['source'];import subprocess
                data=subprocess.check_output(['git','show','526bc9840854f91b9c78ba2c204344e608a6cbf3:'+src['file']],cwd=ROOT)
                from pglast.parser import parse_sql_json
                raw=json.loads(parse_sql_json(data.decode()))['stmts'][src['statement_ordinal']];start=raw.get('stmt_location',0);end=start+raw['stmt_len'] if raw.get('stmt_len') else len(data)
                assert hashlib.sha256(data[start:end]).hexdigest()==src['statement_sha256']
                f['plpgsql_ast']=json.loads(parse_plpgsql_json(data[start:end].decode()))[0]['PLpgSQL_function']
        f=dict(f)
        f['expressions']=[{'ast_path':s.get('control_ast_path',[])[:-1] if s.get('control_ast_path',[])[-1:]==['PLpgSQL_expr'] else s.get('control_ast_path',[])} for s in item['statements']]
        r=ExpandedResolver(f)
        if f['language']=='plpgsql' and typename(d['returnType'])=='trigger':
            relations={e['target_relation'] for e in graph['edges'] if e['kind']=='IMPLICIT_TRIGGER' and sig in e['candidate_targets']}
            if len(relations)==1:
                rel=next(iter(relations));shape={k:v['type'] for k,v in binding.TABLES[rel]['columns'].items()}
                r.records.update({'new':shape,'old':shape});r.vars.update({'tg_op':'text','tg_table_name':'name','tg_table_schema':'name'})
        statements=[]
        queries={tuple(path):x['query'] for k,x,path in walk((f.get('plpgsql_ast') or {}).get('action',{})) if k=='PLpgSQL_expr'}
        for s in item['statements']:
            query=queries.get(tuple(s.get('control_ast_path',[])), '')
            statements.append({'SQL_STATEMENT_ID':sig+':S'+str(s['ordinal']),'query':query,'ast':s['ast']})
        r.discover_records(statements)
        for s in item['statements']:
            r.use_path=tuple(s.get('control_ast_path',[])[:-1] if s.get('control_ast_path',[])[-1:]==['PLpgSQL_expr'] else s.get('control_ast_path',[]))
            r.calls=[]
            for rec in r.references(s['ast'],[]):
                records.append({'function':sig,'statement_ordinal':s['ordinal'],'source':item['function']['source'],**rec})
            for call in r.calls:
                types=call['actual_types'];hashcall=call['callee_spelling'].split('.')[-1]=='transaction_identity_hash'
                resolved=not call['explicit_variadic_array'] and 'UNRESOLVED' not in types and (not hashcall or all(t in ['text','varchar','bpchar','unknown_literal','NULL_LITERAL'] for t in types))
                variadics.append({'caller':sig,'source':item['function']['source'],'statement_ordinal':s['ordinal'],**call,
                    'status':'PROVEN_FROZEN_SOURCE_VARIADIC_BINDING' if resolved else 'REAL_UNRESOLVED_GAP',
                    'fixed_argument_n':0,'variadic_argument_n':len(types),'declared_types':['text[]'] if hashcall else ['any'],
                    'implicit_casts':[{'argument_index':i,'from':t,'to':'text','source':'REL_18_4 pg_cast.dat implicit cast; bpchar padding removal retained'} for i,t in enumerate(types) if hashcall and t in ['bpchar','varchar']],
                    'overload_rule':'Unique frozen public variadic text[] declaration in declared search_path; scalar arguments expanded into text array' if hashcall else 'Explicit pg_catalog unique REL_18_4 num_nonnulls VARIADIC any; mixed scalar inputs accepted',
                    'NULL_behavior':'Non-strict hash function; NULL elements elided by string_agg, caller nullability proof still required' if hashcall else 'Non-strict function counts non-NULL arguments; no homogeneous-array coercion',
                    'semantic_effect':'Identity serialization hash, not completion/authority proof' if hashcall else 'Null-cardinality guard, not completed-work evidence'})
        functions[sig]=f;resolvers[sig]=r;grouped[sig]=statements
    dump('EXPANDED-VARIADIC-BINDINGS.json',{'VARIADIC_CALL_SITE_N':len(variadics),'VARIADIC_RESOLVED_N':sum(x['status']=='PROVEN_FROZEN_SOURCE_VARIADIC_BINDING' for x in variadics),'VARIADIC_UNRESOLVED_N':sum(x['status']!='PROVEN_FROZEN_SOURCE_VARIADIC_BINDING' for x in variadics),'scope':'68 candidate functions, rebuilt from exact frozen source; implicit DDL expressions separately pending','sites':variadics})
    dump('EXPANDED-IDENTIFIER-BINDINGS.json',records)
    unresolved=[x for x in records if x['status']=='REAL_UNRESOLVED_GAP']
    summary={'PREVIOUS_IDENTIFIER_SCOPE_N':31451,'EXPANDED_IDENTIFIER_SCOPE_N':len(records),'EXPANDED_SOURCE_FIELD_TYPE_RESOLVED_N':len(records)-len(unresolved),'EXPANDED_SOURCE_FIELD_TYPE_UNRESOLVED_N':len(unresolved),'EXPANDED_EXECUTION_RELEVANT_IDENTIFIER_N':'UNKNOWN_UNTIL_SEMANTIC_GRAPH_CLOSED','runtime_catalog_verified':False,'semantic_closure':False,'reason_counts':dict(collections.Counter(x['binding_origin'] for x in unresolved))}
    dump('EXPANDED-IDENTIFIER-SUMMARY.json',summary);dump('EXPANDED-IDENTIFIER-GAPS.json',unresolved)
    print(json.dumps(summary))
if __name__=='__main__':main(sys.argv[1])
