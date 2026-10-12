"""Expand only FC01 source/implicit dependencies, including structured SQL.

Indexes declarations for lookup; parses bodies only when reached. No SQL runs.
"""
from pathlib import Path
import collections,hashlib,json,subprocess,sys
from source_binding import BASE,ROOT,OUT,read,walk,strings,typename,SOURCE_HEAD,SUCCESSOR

RESULT=BASE/'continuation-05'
def sha(b):return hashlib.sha256(b).hexdigest()
def canon(o):return json.dumps(o,sort_keys=True,separators=(',',':')).encode()
def dump(n,o):(RESULT/n).write_text(json.dumps(o,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')

def main(parser_path):
    sys.path.insert(0,parser_path)
    from pglast.parser import parse_sql_json,parse_plpgsql_json,scan
    RESULT.mkdir(exist_ok=True)
    index=read(OUT/'SOURCE-DECLARATION-INDEX.json');declarations={};byname=collections.defaultdict(list)
    for p,source in index['sources'].items():
        data=(ROOT/p).read_bytes() if source['source_head']=='HASH_BOUND_SUCCESSOR' else subprocess.check_output(['git','show',SOURCE_HEAD+':'+p],cwd=ROOT)
        assert sha(data)==source['sha256']
        for ordinal,raw in enumerate(json.loads(parse_sql_json(data.decode()))['stmts']):
            if 'CreateFunctionStmt' not in raw['stmt']:continue
            f=raw['stmt']['CreateFunctionStmt'];name='.'.join(strings(f['funcname']));name=name if '.' in name else 'public.'+name
            inputs=[x['FunctionParameter'] for x in f.get('parameters',[]) if x['FunctionParameter'].get('mode') not in ['FUNC_PARAM_OUT','FUNC_PARAM_TABLE']]
            sig=name+'('+','.join(typename(x['argType']) for x in inputs)+')';start=raw.get('stmt_location',0);end=start+raw['stmt_len'] if raw.get('stmt_len') else len(data)
            opts={x['DefElem']['defname']:x['DefElem'].get('arg') for x in f['options']};lang=opts.get('language',{}).get('String',{}).get('sval')
            declarations[sig]={'name':name,'signature':sig,'language':lang,'parameters':inputs,'definition':f,'definition_text':data[start:end].decode(),
                               'source':{'file':p,'statement_ordinal':ordinal,'statement_sha256':sha(data[start:end]),'source_hash':sha(data),'start_line':data[:start].count(b'\n')+1,'end_line':data[:end].count(b'\n')+1,'successor_hash':SUCCESSOR}}
    for sig,f in declarations.items():byname[f['name']].append(sig)
    active_triggers={}
    ordered=sorted(index['implicit_ddl'],key=lambda x:(int(Path(x['provenance']['SOURCE_FILE']).name.split('__')[0][1:]),x['provenance']['SOURCE_STATEMENT_ORDINAL']))
    for entry in ordered:
        t=entry['ast'].get('CreateTrigStmt')
        if t:
            r=t['relation'];rel=r.get('schemaname','public')+'.'+r['relname'];active_triggers[(rel,t['trigname'])]=entry
        d=entry['ast'].get('DropStmt')
        if d and d['removeType']=='OBJECT_TRIGGER':
            for obj in d['objects']:
                names=strings(obj['List']['items']);rel='.'.join(names[:-1]);rel=rel if '.' in rel else 'public.'+rel;active_triggers.pop((rel,names[-1]),None)
    cases=read(ROOT/'docs/evidence/package-0090-g3f4-full-domain-fixture-contract/POSITIVE-CASE-PRECONDITIONS.json')
    roots={w['signature'].replace('pg_catalog.','') for c in cases for w in c['WRAPPERS']};queue=list(sorted(roots));seen=set();edges=[];functions=[];errors=[]
    old=ROOT/'docs/evidence/package-0090-g3f4-authority-boundary-typed'
    cached={read(p)['signature']:read(p) for p in (old/'functions').glob('*.json')}
    def candidates(name,n):
        name=name if '.' in name else 'public.'+name
        options=[]
        for sig in byname.get(name,[]):
            params=declarations[sig]['parameters'];variadic=bool(params and params[-1].get('mode')=='FUNC_PARAM_VARIADIC')
            required=sum(not p.get('defexpr') for p in params)-int(variadic)
            if n>=required and (variadic or n<=len(params)):options.append(sig)
        return options
    while queue:
        sig=queue.pop()
        if sig in seen:continue
        seen.add(sig)
        if sig not in declarations:errors.append({'signature':sig,'error':'SOURCE_DECLARATION_MISSING'});continue
        f=declarations[sig];node=f['definition'];trees=[];normalized=[];pl=None
        if node.get('sql_body'):
            trees=[{'ordinal':0,'ast':node['sql_body'],'provenance_kind':'ORIGINAL_STRUCTURED_SQL_BODY'}]
        elif f['language']=='plpgsql':
            if sig in cached and cached[sig].get('plpgsql_ast'):
                pl=cached[sig]['plpgsql_ast'];normalized=cached[sig].get('analysis_normalizations',[])
            else:
                try:pl=json.loads(parse_plpgsql_json(f['definition_text']))[0]['PLpgSQL_function']
                except Exception as error:errors.append({'signature':sig,'error':str(error),'scope':'IMPLICIT_TRIGGER_BODY_PARSE_GAP'})
            if pl:
                for ordinal,(kind,expr,path) in enumerate((x for x in walk(pl['action']) if x[0]=='PLpgSQL_expr')):
                    query=expr['query'];mode=expr.get('parseMode',0);q=query
                    if mode==2:q='SELECT '+query
                    elif mode in [3,4,5]:
                        tok=next((t for t in scan(query) if t.name in ['COLON_EQUALS','EQUALS'] or query[t.start:t.end+1] in [':=','=']),None)
                        if tok is None:errors.append({'signature':sig,'ordinal':ordinal,'error':'ASSIGNMENT_PARSE_OFFSET_MISSING'});continue
                        q='SELECT '+query[tok.end+1:]
                    try:tree=json.loads(parse_sql_json(q))
                    except Exception as error:errors.append({'signature':sig,'ordinal':ordinal,'error':str(error)});continue
                    trees.append({'ordinal':ordinal,'ast':tree,'query_sha256':sha(query.encode()),'control_ast_path':list(path),'provenance_kind':'HASH_BOUND_SOURCE_EXTRACTED_SQL'})
        elif f['language']=='sql':
            body=next((x['DefElem'].get('arg',{}).get('List',{}).get('items',[{}])[0].get('String',{}).get('sval') for x in node['options'] if x['DefElem']['defname']=='as'),None)
            if body is not None:trees=[{'ordinal':0,'ast':json.loads(parse_sql_json(body)),'query_sha256':sha(body.encode()),'provenance_kind':'ORIGINAL_SQL_AS_BODY'}]
            else:errors.append({'signature':sig,'error':'SQL_BODY_NOT_EXTRACTED'})
        else:errors.append({'signature':sig,'error':'EXTERNAL_LANGUAGE_IMPLEMENTATION_BOUNDARY','language':f['language']})
        functions.append({'signature':sig,'source':f['source'],'language':f['language'],'statement_ast_n':len(trees),'plpgsql_ast_present':pl is not None,'parser_only_normalizations':normalized})
        for statement in trees:
            for kind,value,path in walk(statement['ast']):
                if kind=='FuncCall':
                    name='.'.join(strings(value['funcname']));targets=candidates(name,len(value.get('args',[])))
                    edge={'caller':sig,'kind':'FUNCTION_CALL','callee_spelling':name,'argument_n':len(value.get('args',[])),'candidate_targets':targets,
                          'source':f['source'],'statement_ordinal':statement['ordinal'],'ast_path':list(path),
                          'classification':'REAL_UNRESOLVED_GAP','smallest_missing_fact':'Exact argument coercion/overload and namespace proof' if targets else 'Builtin/extension catalog and implementation boundary proof'}
                    edges.append(edge)
                    queue.extend(targets)
                elif kind in ['InsertStmt','UpdateStmt','DeleteStmt','MergeStmt']:
                    r=value['relation'];rel=r.get('schemaname','public')+'.'+r['relname'];event={'InsertStmt':4,'UpdateStmt':16,'DeleteStmt':8,'MergeStmt':28}[kind]
                    if (value.get('onConflictClause') or {}).get('action')=='ONCONFLICT_UPDATE':event|=16
                    for (target,name),entry in active_triggers.items():
                        if target!=rel or not entry['ast']['CreateTrigStmt']['events']&event:continue
                        trigger=entry['ast']['CreateTrigStmt'];callee='.'.join(strings(trigger['funcname']));targets=candidates(callee,0)
                        edges.append({'caller':sig,'kind':'IMPLICIT_TRIGGER','target_relation':rel,'trigger':name,'candidate_targets':targets,'source':entry['provenance'],
                                      'classification':'REAL_UNRESOLVED_GAP','smallest_missing_fact':'Trigger WHEN/transition/rowcount semantics plus body-call binding'})
                        queue.extend(targets)
        # Persist only reached original/control trees; no unrelated AST dump.
        key=sha(sig.encode())[:24]
        dump(key+'.json',{'function':functions[-1],'original_definition':node,'statements':trees,'control_ast':pl.get('action') if pl else None})
    dump('EXPANDED-SOURCE-GRAPH.json',{'positive_case_n':len(cases),'entry_signature_n':len(roots),'candidate_reachable_function_n':len(seen),
                                     'functions':functions,'edges':edges,'unresolved_source_parse_or_implementation_boundaries':errors,
                                     'closure_complete':False,'candidate_not_proven':True,
                                     'scope':'Source/default-arity/variadic/trigger expansion; FK/default/check/RLS/operator closure still separate'})
    print(json.dumps({'expanded_candidate_functions':len(seen),'explicit_implicit_edges':len(edges),'parse_or_external_boundary_gaps':len(errors),'full_closure':False}))

if __name__=='__main__':main(sys.argv[1])
