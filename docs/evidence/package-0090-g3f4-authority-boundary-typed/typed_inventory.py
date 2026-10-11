"""PG18 SQL/PLpgSQL AST analysis only. Never executes a database or wrapper."""
from pathlib import Path
import json,hashlib,sys,collections
ROOT=Path(__file__).resolve().parents[3]
HEAD='526bc9840854f91b9c78ba2c204344e608a6cbf3'
SUCCESSOR='6ad78ba61d70e803d2a878034aa7988b69b6374568f96949b2ef6c8defc7a8c7'
def sha(b):return hashlib.sha256(b).hexdigest()
def canon(r):return json.dumps(r,sort_keys=True,separators=(',',':')).encode()
def walk(n,path=()):
    if isinstance(n,dict):
        for k,v in n.items():
            yield k,v,path+(k,)
            yield from walk(v,path+(k,))
    elif isinstance(n,list):
        for i,v in enumerate(n):yield from walk(v,path+(i,))
def strings(items):return [n['String']['sval'] for n in items if 'String' in n]
def typename(n):return '.'.join(strings(n.get('names',[]))).removeprefix('pg_catalog.')+('[]' if n.get('arrayBounds') else '')
def expr_fields(ast):return [r for k,v,p in walk(ast) if k=='ColumnRef' for r in [strings(v['fields'])] if r]
def analyze(parser_path):
    sys.path.insert(0,str(parser_path));import pglast
    from pglast.parser import parse_sql_json,parse_plpgsql_json,get_postgresql_version,scan
    sources=[];functions={};by_name=collections.defaultdict(list);tables={};failures=[];constraints=collections.defaultdict(list)
    files=sorted((ROOT/'applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration').glob('V*.sql'))
    for file in files:
        version=int(file.name.split('__')[0][1:])
        if version>43:continue
        if version==43:file=ROOT/'docs/evidence/package-0090-g3f4-hash-bound-successor/envelope-02/V043__TEST_ONLY_NONCANONICAL_executable_successor.sql';data=file.read_bytes();assert sha(data)==SUCCESSOR
        else:
            import subprocess;data=subprocess.check_output(['git','show',HEAD+':'+file.relative_to(ROOT).as_posix()],cwd=ROOT)
        text=data.decode();tree=json.loads(parse_sql_json(text));sources.append({'path':file.relative_to(ROOT).as_posix(),'sha256':sha(data),'statement_N':len(tree['stmts'])})
        for raw in tree['stmts']:
            stmt=raw['stmt'];start=raw.get('stmt_location',0);length=raw.get('stmt_len',0);end=start+length if length else len(data);definition=data[start:end].decode();line=data[:start].count(b'\n')+1
            if 'CreateStmt' in stmt:
                node=stmt['CreateStmt'];rel=node['relation'];name=rel.get('schemaname','public')+'.'+rel['relname'];columns={}
                for elt in node.get('tableElts',[]):
                    if 'ColumnDef' in elt:
                        col=elt['ColumnDef'];columns[col['colname']]=typename(col['typeName'])
                        for c in col.get('constraints',[]):
                            if c.get('Constraint',{}).get('raw_expr'):constraints[name].append(c['Constraint']['raw_expr'])
                    if elt.get('Constraint',{}).get('raw_expr'):constraints[name].append(elt['Constraint']['raw_expr'])
                tables.setdefault(name,{}).update(columns)
            if 'CreateFunctionStmt' not in stmt:continue
            node=stmt['CreateFunctionStmt'];name='.'.join(strings(node['funcname']));name=name if '.' in name else 'public.'+name;params=[p['FunctionParameter'] for p in node.get('parameters',[]) if p['FunctionParameter'].get('mode','FUNC_PARAM_IN') not in ['FUNC_PARAM_OUT','FUNC_PARAM_TABLE']];types=[typename(p['argType']) for p in params];signature=name+'('+','.join(types)+')';options={o['DefElem']['defname']:o['DefElem'].get('arg') for o in node['options']}
            lang=options.get('language',{}).get('String',{}).get('sval','');body=options.get('as',{}).get('List',{}).get('items',[{}])[0].get('String',{}).get('sval','');body_offset=definition.find(body) if body else -1
            f={'name':name,'signature':signature,'parameter_types':types,'parameter_names':[p.get('name') for p in params],'return_type':typename(node['returnType']),'language':lang,'source':file.relative_to(ROOT).as_posix(),'source_line_range':[line,line+definition.count('\n')],'body':body,'body_first_line':line+definition[:max(0,body_offset)].count('\n'),'definition_sha256':sha(definition.encode()),'expressions':[],'plpgsql_ast':None,'parse_errors':[],'analysis_normalizations':[]}
            if lang=='plpgsql':
                try:f['plpgsql_ast']=json.loads(parse_plpgsql_json(definition))[0]['PLpgSQL_function']
                except Exception as e:
                    original='proposed public.marketplace_transaction_identity_decision%ROWTYPE;'
                    relation='public.marketplace_transaction_identity_decision'
                    if definition.count(original)==1 and tables.get(relation):
                        normalized=definition.replace(original,'proposed record;')
                        try:
                            f['plpgsql_ast']=json.loads(parse_plpgsql_json(normalized))[0]['PLpgSQL_function']
                            f['analysis_normalizations'].append({'original_error':str(e),'original_declaration':original,'analysis_declaration':'proposed record;','record_name':'proposed','original_rowtype_relation':relation,'original_column_types':dict(tables[relation]),'normalized_sha256':sha(normalized.encode()),'scope':'PARSER_ONLY_NOT_EXECUTABLE_NOT_SUCCESSOR_TRANSFORMATION','source_predicates_unchanged':True,'runtime_semantic_equivalence_claim':False})
                        except Exception as retry:f['parse_errors'].append(str(retry))
                    else:f['parse_errors'].append(str(e))
            elif lang=='sql':f['expressions'].append({'query':body,'parseMode':0,'lineno':1,'context':'SQL_LANGUAGE_BODY','ast_path':[],'branch':None})
            if f['plpgsql_ast']:
                def visit(n,path=(),line=1,context='OTHER',branch=None):
                    if isinstance(n,list):
                        for i,v in enumerate(n):visit(v,path+(i,),line,context,branch)
                    elif isinstance(n,dict):
                        if 'PLpgSQL_expr' in n:
                            f['expressions'].append({**n['PLpgSQL_expr'],'lineno':line,'context':context,'ast_path':list(path),'branch':branch});return
                        for k,v in n.items():
                            next_line=v.get('lineno',line) if isinstance(v,dict) else line
                            next_context=k if k.startswith('PLpgSQL_stmt_') else context
                            next_branch=v.get('then_body') if k=='PLpgSQL_stmt_if' else branch
                            visit(v,path+(k,),next_line,next_context,next_branch)
                visit(f['plpgsql_ast']['action'])
            functions[signature]=f
            if signature not in by_name[name]:by_name[name].append(signature)
    # Explicit catalog type facts are analysis inputs, not guessed record fields.
    tables.update({'pg_catalog.pg_roles':{'oid':'oid','rolname':'name',**{n:'bool' for n in ['rolcanlogin','rolinherit','rolsuper','rolcreaterole','rolcreatedb','rolreplication','rolbypassrls']}},'pg_catalog.pg_auth_members':{'roleid':'oid','member':'oid','grantor':'oid','admin_option':'bool','inherit_option':'bool','set_option':'bool'}})
    call_edges=[];predicates=[];statements=[];unknown_calls=[]
    for signature,f in functions.items():
        variables=dict(zip(f['parameter_names'],f['parameter_types']));variables.update({'$'+str(i+1):t for i,t in enumerate(f['parameter_types'])});record_types={n['record_name']:n['original_column_types'] for n in f['analysis_normalizations']}
        if f['plpgsql_ast']:
            for datum in f['plpgsql_ast'].get('datums',[]):
                if 'PLpgSQL_var' in datum:
                    v=datum['PLpgSQL_var'];variables[v['refname']]=v.get('datatype',{}).get('PLpgSQL_type',{}).get('typname','UNKNOWN')
        for i,expression in enumerate(f['expressions']):
            query=expression['query'];mode=expression.get('parseMode',0);parse_query=query;prefix=0
            if mode==2:parse_query='SELECT '+query;prefix=7
            elif mode in [3,4,5]:
                tokens=scan(query);assign=next((t for t in tokens if t.name in ['COLON_EQUALS','EQUALS'] or query[t.start:t.end+1] in [':=','=']),None)
                if assign is None:f['parse_errors'].append('Unresolved assignment SQL expression');continue
                parse_query='SELECT '+query[assign.end+1:];prefix=7
            try:ast=json.loads(parse_sql_json(parse_query))
            except Exception as e:f['parse_errors'].append({'expression':i,'query':query,'error':str(e)});continue
            alias_candidates=collections.defaultdict(set)
            for k,v,p in walk(ast):
                if k=='RangeVar':alias_candidates[v.get('alias',{}).get('aliasname',v['relname'])].add(v.get('schemaname','public')+'.'+v['relname'])
            # Full nested scope/correlation resolution remains pending. Never
            # select the last table when a reused alias has conflicting bindings.
            aliases={a:next(iter(names)) if len(names)==1 else None for a,names in alias_candidates.items()}
            def infer(n):
                if not isinstance(n,dict):return 'UNKNOWN'
                if 'TypeCast' in n:return typename(n['TypeCast']['typeName'])
                if 'ParamRef' in n:return variables.get('$'+str(n['ParamRef']['number']),'UNKNOWN')
                if 'ColumnRef' in n:
                    fields=strings(n['ColumnRef']['fields'])
                    if len(fields)==1:return variables.get(fields[0],'UNKNOWN')
                    if len(fields)==2:return tables.get(aliases.get(fields[0],''),{}).get(fields[1],record_types.get(fields[0],{}).get(fields[1],'UNKNOWN'))
                if any(k in n for k in ['BoolExpr','NullTest','BooleanTest','SubLink']):return 'bool'
                if 'A_Const' in n:
                    c=n['A_Const'];return 'unknown_literal' if 'sval' in c or 'isnull' in c else 'int4' if 'ival' in c else 'bool' if 'boolval' in c else 'UNKNOWN'
                if 'A_Expr' in n:
                    a=n['A_Expr'];op='.'.join(strings(a.get('name',[])));left=infer(a.get('lexpr'));right=infer(a.get('rexpr'))
                    if op in ['=','<>','<','>','<=','>=','~','!~','~*','!~*','~~','!~~','~~*','!~~*'] and left!='UNKNOWN' and right!='UNKNOWN':return 'bool'
                if 'FuncCall' in n:
                    call=n['FuncCall'];name='.'.join(strings(call['funcname']));choices=[functions[s] for s in by_name.get(name,[]) if len(functions[s]['parameter_types'])==len(call.get('args',[]))]
                    if len(choices)==1:return choices[0]['return_type']
                    simple=name.removeprefix('pg_catalog.')
                    if simple in ['isfinite','pg_has_role','has_table_privilege','has_any_column_privilege','has_function_privilege']:return 'bool'
                    if simple in ['get_byte','octet_length','array_length','cardinality']:return 'int4'
                    if simple in ['sha256','uuid_send','int8send','int4send','convert_to','decode']:return 'bytea'
                    if simple in ['clock_timestamp','transaction_timestamp']:return 'timestamptz'
                return 'UNKNOWN'
            for k,v,path in walk(ast):
                if k=='FuncCall':
                    name='.'.join(strings(v['funcname']))
                    if name.startswith('public.'):
                        choices=[s for s in by_name.get(name,[]) if len(functions[s]['parameter_types'])==len(v.get('args',[]))]
                        edge={'source':signature,'name':name,'arguments_N':len(v.get('args',[])),'targets':choices,'exact_target':len(choices)==1}
                        call_edges.append(edge)
                        if len(choices)!=1:unknown_calls.append(edge)
            # Bind SELECT INTO record fields through actual AST target expressions.
            if f['plpgsql_ast']:
                parent=f['plpgsql_ast']['action']
                for step in expression['ast_path'][:-1]:parent=parent[step]
                # Full ancestry search avoids inventing a record table relation.
                for key,value,path in walk(f['plpgsql_ast']['action']):
                    if key=='PLpgSQL_stmt_execsql' and value.get('sqlstmt',{}).get('PLpgSQL_expr',{}).get('query')==query and value.get('target',{}).get('PLpgSQL_rec'):
                        rec=value['target']['PLpgSQL_rec']['refname'];types={}
                        for key2,res,path2 in walk(ast):
                            if key2=='ResTarget':
                                refs=expr_fields(res.get('val',{}));col=res.get('name') or (refs[0][-1] if refs else None)
                                if col:types[col]=infer(res.get('val',{}))
                        record_types[rec]=types
            sid=signature+':S'+str(i);statements.append({'SQL_STATEMENT_ID':sid,'SQL_OBJECT':signature,'query':query,'ast':ast,'plpgsql_context':expression['context'],'source_file':f['source'],'source_line_range':f['source_line_range'],'exact_predicate_location':False})
            branch_error=None
            branch=expression.get('branch') or []
            if branch and 'PLpgSQL_stmt_raise' in branch[0]:
                raise_stmt=branch[0]['PLpgSQL_stmt_raise']
                if raise_stmt.get('elog_level')==21:
                    branch_error='P0001_DEFAULT_RAISE'
                    for opt in raise_stmt.get('options',[]):
                        option=opt.get('PLpgSQL_raise_option',{})
                        if option.get('opt_type')==0:
                            q=option.get('expr',{}).get('PLpgSQL_expr',{}).get('query','')
                            try:
                                err_ast=json.loads(parse_sql_json('SELECT '+q));constants=[v for k,v,p in walk(err_ast) if k=='A_Const']
                                if len(constants)==1 and constants[0].get('sval',{}).get('sval'):branch_error=constants[0]['sval']['sval']
                            except Exception:branch_error='DYNAMIC_SQLSTATE_UNRESOLVED'
            for key,node,path in walk(ast):
                predicate=key in ['BoolExpr','NullTest','BooleanTest'] or key=='A_Expr' and ('.'.join(strings(node.get('name',[]))) in ['=','<>','<','>','<=','>=','~','!~','~*','!~*','~~','!~~','~~*','!~~*'] or node.get('kind') in ['AEXPR_IN','AEXPR_BETWEEN','AEXPR_NOT_BETWEEN','AEXPR_DISTINCT','AEXPR_NOT_DISTINCT','AEXPR_OP_ANY','AEXPR_OP_ALL','AEXPR_LIKE','AEXPR_ILIKE','AEXPR_SIMILAR']) or key=='SubLink' and node.get('subLinkType')=='EXISTS_SUBLINK' or key=='FuncCall' and infer({key:node})=='bool'
                if not predicate:continue
                wrapped={key:node};refs=expr_fields(wrapped);bound=[{'reference':r,'relation':aliases.get(r[0]) if len(r)>1 else None,'column':r[-1] if r else None,'type':infer({'ColumnRef':{'fields':[{'String':{'sval':s}} for s in r]}})} for r in refs]
                typ=infer(wrapped);unresolved=typ!='bool' or any(r['type']=='UNKNOWN' for r in bound)
                fields={r['column'] for r in bound};relations={r['relation'] for r in bound if r['relation']}
                dimension='UNCLASSIFIED';kind='UNCLASSIFIED'
                if not unresolved:
                    if fields & {'organization_id'}:kind='SQL_SCOPE_GUARD';dimension='ORGANIZATION'
                    elif fields & {'deployment_id','deployment_incarnation_id','incarnation_id'}:kind='SQL_SCOPE_GUARD';dimension='DEPLOYMENT_INCARNATION'
                    elif fields & {'generation','enrollment_revision','registry_revision'}:kind='SQL_GENERATION_GUARD';dimension='GENERATION'
                    elif fields & {'revision','credential_revision','grant_revision','signer_authority_revision','signer_key_revision'}:kind='SQL_REVISION_GUARD';dimension='REVISION'
                    elif fields & {'state','durable_state','result'}:kind='SQL_STATE_GUARD';dimension='STATE'
                    elif any(r['type'] in ['timestamptz','timestamp','interval'] for r in bound):kind='SQL_TIME_GUARD';dimension='TIME'
                    elif relations & set(tables) and fields & {'oid','rolname','binding_id','attempt_id','execution_id','principal_id','credential_id','grant_id','attestation_id','policy_digest','deadline_policy_digest'}:kind='SQL_AUTHORITY_PREDICATE';dimension='IDENTITY_AUTHORITY'
                    elif branch_error=='P0017':kind='SQL_AUTHORITY_PREDICATE';dimension='EXACT_SOURCE_ACCESS_DENIAL_GUARD'
                    elif len(relations)>1:kind='SQL_JOIN_PREDICATE';dimension='EXACT_JOIN'
                    elif 'CaseWhen' in path and key=='NullTest':kind='NON_AUTHORITY_SQL_CONDITION';dimension='EXPLICIT_CASE_NULL_DISCRIMINATOR_NOT_AUTHORITY_JOIN'
                    else:kind='UNCLASSIFIED';dimension='TYPED_BOOLEAN_SEMANTIC_PURPOSE_REVIEW_REQUIRED'
                pid=sha(canon({'object':signature,'statement':sid,'path':path}))[:24]
                predicates.append({'PREDICATE_ID':pid,'WRAPPER_NAME':[],'SQL_OBJECT':signature,'SQL_STATEMENT_ID':sid,'SOURCE_RELATION':bound[0]['relation'] if bound else None,'SOURCE_COLUMN':bound[0]['column'] if bound else None,'TARGET_RELATION_IF_ANY':bound[1]['relation'] if len(bound)>1 else None,'TARGET_COLUMN_IF_ANY':bound[1]['column'] if len(bound)>1 else None,'OPERATOR':node.get('boolop') or node.get('nulltesttype') or node.get('booltesttype') or node.get('subLinkType') or '.'.join(strings(node.get('name',[]))),'PREDICATE_CLASS':kind,'SEMANTIC_DIMENSION':dimension,'NULL_BEHAVIOR':'Exact SQL AST retained: AND/OR/NOT and NULL/EXISTS/CASE context; WHERE accepts TRUE only, PLpgSQL IF takes TRUE branch only. No grouping flattened.','TRUE_BEHAVIOR':'Atomic TRUE feeds retained grouping; '+('full source IF TRUE raises '+branch_error if branch_error else 'exact AST branch/query outcome mapping pending'),'FALSE_BEHAVIOR':'Atomic FALSE/UNKNOWN feeds retained AND/OR/NOT tree; not independently equated with acceptance or numeric zero','SQLSTATE_OR_DENIAL':branch_error or 'PENDING_CONTROL_FLOW_BRANCH_MAPPING_NOT_INFERRED','ORGANIZATION_BOUND':'organization_id' in fields,'DEPLOYMENT_BOUND':'deployment_id' in fields,'INCARNATION_BOUND':bool(fields & {'incarnation_id','deployment_incarnation_id'}),'GENERATION_BOUND':'generation' in fields,'REVISION_BOUND':bool(fields & {'revision','credential_revision','grant_revision'}),'TIME_BOUND':kind=='SQL_TIME_GUARD','STATUS_BOUND':kind=='SQL_STATE_GUARD','SUCCESSOR_SHA256':SUCCESSOR,'SOURCE_FILE':f['source'],'SOURCE_LINE_RANGE':f['source_line_range'],'source_location_precision':'EXACT_SQL_OBJECT_RANGE_PREDICATE_SPAN_PENDING','ast_path':list(path),'ast_node':wrapped,'column_bindings':bound,'boolean_type_inferred':typ,'unresolved_type_or_binding':unresolved})
    return {'sources':sources,'tables':tables,'functions':functions,'call_edges':call_edges,'unknown_calls':unknown_calls,'predicates':predicates,'statements':statements,'constraints':dict(constraints),'parser':{'version':pglast.__version__,'postgresql_grammar':get_postgresql_version(),'pyd_inventory':{p.name:sha(p.read_bytes()) for p in Path(parser_path).rglob('*.pyd')},'runtime_execution':False,'limitation':'Raw AST plus declared-type analysis is not PostgreSQL catalog/operator resolution or PG18.4 execution proof.'}}
