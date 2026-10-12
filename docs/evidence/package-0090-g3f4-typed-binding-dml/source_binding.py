"""Frozen declaration index and FC01 variadic source-binding review only.

No PostgreSQL server, canonical resources or runtime execution. DDL is indexed
for referenced declarations; unrelated function bodies are not analyzed.
"""
from pathlib import Path
import collections, hashlib, json, subprocess, sys

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
OUT = BASE / 'continuation-02'
SOURCE_HEAD = '526bc9840854f91b9c78ba2c204344e608a6cbf3'
SUCCESSOR = '6ad78ba61d70e803d2a878034aa7988b69b6374568f96949b2ef6c8defc7a8c7'

def sha(data): return hashlib.sha256(data).hexdigest()
def read(path): return json.loads(path.read_text(encoding='utf-8-sig'))
def dump(name, obj): (OUT/name).write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False)+'\n', encoding='utf-8', newline='\n')
def strings(a): return [x['String']['sval'] for x in a if 'String' in x]
def typename(n): return '.'.join(strings(n['names'])).removeprefix('pg_catalog.') + ('[]' if n.get('arrayBounds') else '')
def walk(n, path=()):
    if isinstance(n,dict):
        for k,v in n.items():
            yield k,v,path+(k,)
            yield from walk(v,path+(k,))
    elif isinstance(n,list):
        for i,v in enumerate(n): yield from walk(v,path+(i,))

def main(parser_path):
    sys.path.insert(0,parser_path)
    from pglast.parser import parse_sql_json,scan
    OUT.mkdir(exist_ok=True)
    old = ROOT/'docs/evidence/package-0090-g3f4-authority-boundary-typed'
    cached = {read(p)['signature']:read(p) for p in (old/'functions').glob('*.json')}
    named = {f['name'] for f in cached.values()}|{'public.transaction_identity_hash'}
    # Follow only trigger dependencies on already identified FC01 DML targets.
    prior_index=OUT/'SOURCE-DECLARATION-INDEX.json'
    if prior_index.exists():
        targets={x['TARGET_RELATION'].get('relation') for x in read(BASE/'semantic-checkpoint/DML-DEPENDENCY-GRAPH.json')}
        for entry in read(prior_index)['implicit_ddl']:
            trigger=entry['ast'].get('CreateTrigStmt')
            if trigger and trigger['relation']['relname'] in targets:
                name='.'.join(strings(trigger['funcname']));named.add(name if '.' in name else 'public.'+name)
    catalog, tables, sources, ddl = {}, {}, {}, []
    paths = subprocess.check_output(['git','ls-tree','-r','--name-only',SOURCE_HEAD,'--','applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration'],cwd=ROOT,text=True).splitlines()
    paths = [p for p in paths if Path(p).name.startswith('V') and int(Path(p).name.split('__')[0][1:])<=42]
    successor_path='docs/evidence/package-0090-g3f4-hash-bound-successor/envelope-02/V043__TEST_ONLY_NONCANONICAL_executable_successor.sql'
    paths.append(successor_path)
    for p in paths:
        data=(ROOT/p).read_bytes() if p==successor_path else subprocess.check_output(['git','show',SOURCE_HEAD+':'+p],cwd=ROOT)
        if p==successor_path: assert sha(data)==SUCCESSOR
        sources[p]={'sha256':sha(data),'byte_n':len(data),'source_head':SOURCE_HEAD if p!=successor_path else 'HASH_BOUND_SUCCESSOR'}
        tree=json.loads(parse_sql_json(data.decode()))
        for ordinal, raw in enumerate(tree['stmts']):
            start=raw.get('stmt_location',0);end=start+raw['stmt_len'] if raw.get('stmt_len') else len(data)
            objdata=data[start:end];node=raw['stmt']
            prov={'SOURCE_FILE':p,'SOURCE_STATEMENT_ORDINAL':ordinal,'SOURCE_STATEMENT_SHA256':sha(objdata),
                  'SOURCE_HASH':sha(data),'START_LINE':data[:start].count(b'\n')+1,'START_COLUMN':start-data.rfind(b'\n',0,start),
                  'END_LINE':data[:end].count(b'\n')+1,'END_COLUMN':end-data.rfind(b'\n',0,end),
                  'BYTE_START':start,'BYTE_END_EXCLUSIVE':end,'SUCCESSOR_HASH':SUCCESSOR}
            if 'CreateFunctionStmt' in node:
                f=node['CreateFunctionStmt'];name='.'.join(strings(f['funcname']));name=name if '.' in name else 'public.'+name
                if name not in named: continue
                params=[x['FunctionParameter'] for x in f.get('parameters',[]) if x['FunctionParameter'].get('mode') not in ['FUNC_PARAM_OUT','FUNC_PARAM_TABLE']]
                sig=name+'('+','.join(typename(x['argType']) for x in params)+')'
                opts={x['DefElem']['defname']:x['DefElem'].get('arg') for x in f['options']}
                body=opts.get('as',{}).get('List',{}).get('items',[{}])[0].get('String',{}).get('sval')
                cfg=opts.get('set',{}).get('VariableSetStmt')
                set_options=[x['DefElem']['arg']['VariableSetStmt'] for x in f['options'] if x['DefElem']['defname']=='set']
                search=next((v for v in set_options if v['name']=='search_path'),None)
                outputs=[x['FunctionParameter'] for x in f.get('parameters',[]) if x['FunctionParameter'].get('mode') in ['FUNC_PARAM_OUT','FUNC_PARAM_TABLE','FUNC_PARAM_INOUT']]
                catalog[sig]={'name':name,'parameters':[{'name':x.get('name'),'type':typename(x['argType']),'mode':x.get('mode','FUNC_PARAM_IN'),'default':x.get('defexpr')} for x in params],
                              'output_fields':{x['name']:typename(x['argType']) for x in outputs if x.get('name')},
                              'return_type':typename(f['returnType']),'search_path_ast':search,'security_definer':bool(opts.get('security',{}).get('Boolean',{}).get('boolval',False)),
                              'options_ast':opts,'body':body,'body_hash':sha(body.encode()) if body is not None else None,'OBJECT_HASH':sha(objdata),'provenance':prov}
            elif 'CreateStmt' in node:
                t=node['CreateStmt'];r=t['relation'];name=r.get('schemaname','public')+'.'+r['relname']
                cols={};constraints=[]
                for elt in t.get('tableElts',[]):
                    if 'ColumnDef' in elt:
                        c=elt['ColumnDef'];cols[c['colname']]={'type':typename(c['typeName']),'constraints':c.get('constraints',[]),'raw_default':c.get('raw_default'),'generated':c.get('generated'),'identity':c.get('identity')}
                    elif 'Constraint' in elt: constraints.append(elt)
                tables[name]={'columns':cols,'constraints':constraints,'provenance':prov,'create_ast':t,'alterations':[]}
            elif 'AlterTableStmt' in node:
                a=node['AlterTableStmt'];r=a.get('relation',{});name=r.get('schemaname','public')+'.'+r.get('relname','')
                if name in tables: tables[name]['alterations'].append({'ast':a,'provenance':prov})
            elif any(k in node for k in ['CreateTrigStmt','CreatePolicyStmt','AlterPolicyStmt','RuleStmt','IndexStmt','ViewStmt','CreateDomainStmt','CompositeTypeStmt','DropStmt']):
                ddl.append({'ast':node,'provenance':prov})
    dump('SOURCE-DECLARATION-INDEX.json',{'catalog':catalog,'tables':tables,'implicit_ddl':ddl,'sources':sources,
                                        'scope':'DECLARATION_INDEX_ONLY_FUNCTION_BODY_ANALYSIS_LIMITED_TO_FC01_DEPENDENCIES'})
    # Three previously unbound variadic callers; append newly discovered source
    # target without guessing source arity == declared array parameter count.
    call_review=read(BASE/'CALL-EDGE-REVIEW.json')
    sites=[x for x in call_review['calls_without_cached_source_target'] if x['source_spelling']=='transaction_identity_hash']
    target=catalog['public.transaction_identity_hash(text[])']
    assert len(target['parameters'])==1 and target['parameters'][0]['mode']=='FUNC_PARAM_VARIADIC'
    overloads=[s for s,f in catalog.items() if f['name']==target['name']]
    assert overloads==['public.transaction_identity_hash(text[])']
    records=[]
    for site in sites:
        caller=cached[site['caller']];expr=caller['expressions'][int(site['statement_id'].rsplit(':S',1)[1])]
        ast=json.loads(parse_sql_json(expr['query']));cur=ast
        for step in site['ast_path']:cur=cur[step]
        args=cur['args'];aliases={v.get('alias',{}).get('aliasname',v['relname']):v.get('schemaname','public')+'.'+v['relname'] for k,v,_ in walk(ast) if k=='RangeVar'}
        composites={n:t if '.' in t else 'public.'+t for n,t in zip(caller['parameter_names'],caller['parameter_types'])}
        def infer(n):
            if 'TypeCast' in n:return typename(n['TypeCast']['typeName'])
            if 'A_Const' in n:return 'unknown_literal'
            if 'ColumnRef' in n:
                refs=strings(n['ColumnRef']['fields']);rel=aliases.get(refs[0],composites.get(refs[0])) if refs else None
                return tables.get(rel,{}).get('columns',{}).get(refs[-1],{}).get('type','UNRESOLVED') if refs else 'UNRESOLVED'
            if 'CoalesceExpr' in n:
                types={infer(x) for x in n['CoalesceExpr']['args']} - {'unknown_literal'}
                return next(iter(types)) if len(types)==1 else 'UNRESOLVED'
            if 'A_Expr' in n and strings(n['A_Expr'].get('name',[]))==['||']:return 'text' if infer(n['A_Expr']['lexpr']) in ['text','unknown_literal'] and infer(n['A_Expr']['rexpr']) in ['text','unknown_literal'] else 'UNRESOLVED'
            if 'CaseExpr' in n:
                vals=[x['CaseWhen']['result'] for x in n['CaseExpr']['args']]+[n['CaseExpr']['defresult']]
                types={infer(x) for x in vals}-{'unknown_literal'};return 'text' if not types else next(iter(types)) if len(types)==1 else 'UNRESOLVED'
            if 'FuncCall' in n and '.'.join(strings(n['FuncCall']['funcname'])).removeprefix('pg_catalog.') in ['to_char','left','right']:return 'text'
            return 'UNRESOLVED'
        types=[infer(a) for a in args];position=cur['location']
        source_caller=catalog[site['caller']];query_bytes=expr['query'].encode()
        # Exact source declaration and body digest; original parser-normalized
        # expression maps by ordinal/hash as authorized, not fuzzy line search.
        proven_source_body=(sha(caller['body'].encode())==source_caller['body_hash'])
        # PostgreSQL REL_18_4 pg_cast.dat declares bpchar -> text as implicit
        # via text(bpchar). This trims trailing padding; retain that meaning.
        cast_source=(OUT/'pg18.4/pg_cast.dat').read_bytes()
        assert b"castsource => 'bpchar', casttarget => 'text'" in cast_source
        resolved=all(t in ['text','unknown_literal','bpchar','varchar'] for t in types) and proven_source_body and not cur.get('func_variadic',False)
        records.append({'CALL_SITE_ID':sha((site['statement_id']+':VARIADIC').encode())[:24],'CALLER':site['caller'],'CALLEE':'public.transaction_identity_hash(text[])',
                        'ARGUMENT_COUNT':len(args),'FIXED_ARGUMENT_N':0,'VARIADIC_ARGUMENT_N':len(args),'ARGUMENT_TYPES':types,'PARAMETER_TYPES':['text[]'],
                        'EXPANSION_RULE':'Non-VARIADIC call expands text[] element type into N text arguments, then constructs ordered array; unknown string literals coerced to text.',
                        'OVERLOAD_RESOLUTION':'Single frozen source declaration; caller SET search_path pg_catalog,public,pg_temp; stock pg_catalog namespace assumption remains deployment-attestation prerequisite.',
                        'CASTS':'Explicit ::text retained; unknown literals become text; bpchar -> text implicit function cast removes trailing padding; varchar -> text implicit binary cast. No array flattening.',
                        'CAST_SOURCE_SHA256':sha(cast_source),'CAST_SOURCE_URL':'https://raw.githubusercontent.com/postgres/postgres/REL_18_4/src/include/catalog/pg_cast.dat',
                        'NULLABILITY':'Individual values may be NULL. Composite argument itself is not declared STRICT; inner-join row fields and non-NULL constraints need per-caller proof. NULL-elision effect preserved.',
                        'ARRAY_EXPANSION_IF_ANY':'NO explicit VARIADIC array call at this site','SOURCE_SPAN':{'file':source_caller['provenance']['SOURCE_FILE'],'object':site['caller'],'statement_ordinal':int(site['statement_id'].rsplit(':S',1)[1]),'statement_sha256':sha(query_bytes),'object_hash':source_caller['OBJECT_HASH'],'body_hash_matches_original':proven_source_body},
                        'CALLEE_SPAN':target['provenance'],'SUCCESSOR_HASH':SUCCESSOR,'SEMANTIC_EFFECT':'Ordered length-prefixed UTF8 non-NULL argument values; NULL argument positions are omitted by strict concatenation/string_agg. Empty/all-NULL aggregate returns NULL.',
                        'AUTHORITY_RELEVANT':True,'RESOLUTION_STATUS':'PROVEN_FROZEN_SOURCE_VARIADIC_BINDING' if resolved else 'REAL_UNRESOLVED_GAP',
                        'runtime_catalog_or_wrapper_execution':False,'arguments_ast':args})
    dump('VARIADIC-BINDINGS.json',{'VARIADIC_CALL_SITE_N':len(records),'VARIADIC_RESOLVED_N':sum(x['RESOLUTION_STATUS']=='PROVEN_FROZEN_SOURCE_VARIADIC_BINDING' for x in records),
                                 'VARIADIC_UNRESOLVED_N':sum(x['RESOLUTION_STATUS']!='PROVEN_FROZEN_SOURCE_VARIADIC_BINDING' for x in records),
                                 'scope':'CURRENT_CACHED_FC01_CALL_SITES_FROZEN_SOURCE_BINDING_NOT_COMPLETE_IMPLICIT_REACHABILITY','sites':records})
    print(json.dumps({'variadic_sites':len(records),'resolved':sum(x['RESOLUTION_STATUS']=='PROVEN_FROZEN_SOURCE_VARIADIC_BINDING' for x in records),
                      'declaration_functions':len(catalog),'tables_indexed_for_binding':len(tables),'runtime_execution':False}))

if __name__=='__main__': main(sys.argv[1])
