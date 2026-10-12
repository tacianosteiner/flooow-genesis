"""Exact scoped argument-type candidates, preserving catalog ambiguity.
Reuses the published expanded resolver; never rewrites its frozen artifacts.
"""
import collections,hashlib,json,sys
import expanded_bindings as engine
import identifier_rebinding as binding
from source_binding import BASE,read,walk,strings,typename
OUT=BASE/'continuation-09'
CALLS=[]
class AllCalls(engine.ExpandedResolver):
    def typ(self,node,scopes):
        value=super().typ(node,scopes)
        if value!='UNRESOLVED' or not isinstance(node,dict):return value
        if 'A_Indirection' in node:
            a=node['A_Indirection'];t=self.typ(a['arg'],scopes);indices=[x['A_Indices'] for x in a.get('indirection',[]) if 'A_Indices' in x]
            if t=='oidvector' and indices and not any(i.get('is_slice') for i in indices):return 'oid'  # REL_18_4 typelem/array_subscript_handler
        if 'MinMaxExpr' in node:return binding.common([self.typ(a,scopes) for a in node['MinMaxExpr']['args']])
        if 'A_Expr' in node:
            a=node['A_Expr'];types=[self.typ(a.get(k),scopes) for k in ['lexpr','rexpr']]
            if strings(a.get('name',[]))==['||'] and all(t not in ['UNRESOLVED','bytea'] and not t.endswith('[]') for t in types) and any(t in ['text','unknown_literal'] for t in types):
                return 'text'  # REL_18_4 textanycat/anytextcat; exact operator remains separate.
        if 'FuncCall' in node:
            c=node['FuncCall'];name='.'.join(strings(c['funcname']));args=[self.typ(a,scopes) for a in c.get('args',[])]
            if 'UNRESOLVED' in args:return 'UNRESOLVED'
            name=name.removeprefix('pg_catalog.');returns=set()
            for candidate in binding.BUILTINS.get(name,[]):
                formal=candidate.get('proargtypes','').split()
                if len(formal)!=len(args):continue
                if all(a in ['unknown_literal','NULL_LITERAL'] or a==t or (a,t) in binding.IMPLICIT or t in ['anyarray','anycompatiblearray'] and a.endswith('[]') or t in ['anyelement','anycompatible','anynonarray'] and not a.endswith('[]') for a,t in zip(args,formal)):
                    r=candidate.get('prorettype','UNRESOLVED')
                    if r in ['anyarray','anycompatiblearray'] and args:
                        r=args[0] if args[0].endswith('[]') else args[0]+'[]'
                    elif r in ['anyelement','anycompatible'] and args:r=args[0][:-2] if args[0].endswith('[]') else args[0]
                    returns.add(binding.ARRAY_NAMES.get(r,r))
            if len(returns)==1:return next(iter(returns))
        return value
    def references(self,node,scopes,path=()):
        if isinstance(node,dict) and 'FuncCall' in node:
            c=node['FuncCall'];CALLS.append({'caller':self.f['signature'],'control_path':list(self.use_path),'ast_path':list(path),
                'callee_spelling':'.'.join(strings(c['funcname'])),'argument_types':[self.typ(a,scopes) for a in c.get('args',[])],
                'argument_asts':c.get('args',[]),'explicit_variadic':bool(c.get('func_variadic'))})
        yield from super().references(node,scopes,path)
def main(parser_path):
    sys.setrecursionlimit(10000)  # Analysis AST traversal control; no runtime policy.
    OUT.mkdir(exist_ok=True);engine.OUT=OUT;engine.dump=lambda *args:None;engine.ExpandedResolver=AllCalls
    engine.main(parser_path)
    graph=read(BASE/'continuation-05/EXPANDED-SOURCE-GRAPH.json');sources={x['signature']:x['source'] for x in graph['functions']}
    definitions={read(p)['function']['signature']:read(p)['original_definition'] for p in (BASE/'continuation-05').glob('*.json') if p.name!='EXPANDED-SOURCE-GRAPH.json'}
    byname=collections.defaultdict(list)
    for sig,n in definitions.items():
        params=[x['FunctionParameter'] for x in n.get('parameters',[]) if x['FunctionParameter'].get('mode') not in ['FUNC_PARAM_OUT','FUNC_PARAM_TABLE']]
        byname[sig.split('(')[0]].append({'signature':sig,'types':[typename(x['argType']) for x in params],
            'variadic':bool(params and params[-1].get('mode')=='FUNC_PARAM_VARIADIC'),'required':sum(not p.get('defexpr') for p in params)})
    for item in CALLS:
        name=item['callee_spelling'];args=item['argument_types'];qualified=name if '.' in name else 'public.'+name;options=[]
        for cand in byname.get(qualified,[]):
            types=cand['types'];var=cand['variadic'];required=cand['required']-int(var)
            if len(args)<required or not var and len(args)>len(types):continue
            expected=types[:-1]+[types[-1][:-2]]*(len(args)-len(types)+1) if var and not item['explicit_variadic'] else types[:len(args)]
            if len(expected)!=len(args):continue
            casts=[];ok=True
            for i,(a,t) in enumerate(zip(args,expected)):
                if a in ['unknown_literal','NULL_LITERAL']:casts.append({'index':i,'from':a,'to':t,'kind':'CONTEXTUAL_LITERAL'} )
                elif a==t:continue
                elif (a,t) in binding.IMPLICIT:casts.append({'index':i,'from':a,'to':t,'kind':'REL_18_4_IMPLICIT_CAST'})
                else:ok=False
            if ok:options.append({**cand,'required_casts':casts})
        item['original_source']=sources[item['caller']];item['source_target_candidates']=options
        item['source_call_binding_status']='UNIQUE_SOURCE_TYPE_COMPATIBLE_TARGET' if len(options)==1 else 'SOURCE_OVERLOAD_AMBIGUITY' if options else 'BUILTIN_EXTENSION_OR_TYPE_GAP'
        item['classification']='REAL_UNRESOLVED_GAP'
        item['remaining']='Namespace/ACL/security context, exact overload ranking and callee/operator effects; compatible candidate is not final execution proof'
        item['proof_paths']=['STATIC_SOURCE_PROOF','EXECUTABLE_SQL_NEGATIVE','EXECUTABLE_SQL_POSITIVE']
    summary={'CALL_OCCURRENCE_N':len(CALLS),'SOURCE_TYPE_COMPATIBLE_UNIQUE_N':sum(x['source_call_binding_status']=='UNIQUE_SOURCE_TYPE_COMPATIBLE_TARGET' for x in CALLS),
             'SOURCE_OVERLOAD_AMBIGUITY_N':sum(x['source_call_binding_status']=='SOURCE_OVERLOAD_AMBIGUITY' for x in CALLS),
             'UNRESOLVED_ARGUMENT_TYPE_N':sum('UNRESOLVED' in x['argument_types'] for x in CALLS),'FINAL_EXECUTION_DEPENDENCY_PROVEN_N':0,'semantic_denominator':'UNKNOWN'}
    (OUT/'SCOPED-CALL-CANDIDATES.json').write_text(json.dumps(CALLS,separators=(',',':'),sort_keys=True)+'\n',encoding='utf-8',newline='\n')
    (OUT/'CALL-BINDING-STATUS.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n');print(json.dumps(summary))
if __name__=='__main__':main(sys.argv[1])
