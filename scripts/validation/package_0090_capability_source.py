"""Bounded internal-P source review, never an implementation/runtime certificate."""
import json
import re

P_NAME = 'offline_lock_bound_principal'
P_TYPES = ('uuid','bytea','uuid','text','uuid','int8','uuid','uuid','bytea')
P_NAMES = ('binding_id','plan_fingerprint','expected_incarnation_id','surface_version',
           'attempt_id','generation','execution_id','instance_id','possession_secret')
P_OWNER = 'flooow_offline_principal_lock_owner'
E_OWNER = 'flooow_offline_execution_owner'
EXECUTE = {('public',P_NAME,P_TYPES,E_OWNER),
           ('public','command_authorization_organization_lock',('uuid',),P_OWNER)}
BUILTINS = {'octet_length','current_setting','substring','get_byte','convert_from',
            'array_append','sha256','convert_to','clock_timestamp','isfinite',
            'transaction_timestamp','extract','is_normalized'}


def check(statements, expected_columns):
    import package_0090_z_source as z
    import package_0090_q_source as q
    definitions = [s['CreateFunctionStmt'] for s in statements if 'CreateFunctionStmt' in s]
    by_name = {strings(f['funcname']): f for f in definitions}
    if len(by_name) != len(definitions) or set(by_name) - {('public',P_NAME), ('public',z.NAME),('public',q.NAME)}:
        raise ValueError('Unreviewed or duplicate capability definition')
    expected_execute = EXECUTE | (z.GRANTS if ('public',z.NAME) in by_name else set()) | (q.GRANTS if ('public',q.NAME) in by_name else set())
    grants = set(); revokes = set(); owners = {}
    p_statements = []
    for statement in statements:
        if 'CreateFunctionStmt' in statement:
            if strings(statement['CreateFunctionStmt']['funcname']) == ('public',P_NAME):
                p_statements.append(statement)
        elif 'AlterOwnerStmt' in statement:
            owner = statement['AlterOwnerStmt']
            obj = owner.get('object',{}).get('ObjectWithArgs',{})
            name = strings(obj.get('objname',[]))
            vector = tuple(strings(t['TypeName']['names']) for t in obj.get('objargs',[]))
            if owner['objectType']!='OBJECT_FUNCTION' or name not in by_name or name in owners:
                raise ValueError('Unapproved or duplicate ownership change')
            expected_types = P_TYPES if name==('public',P_NAME) else q.TYPES if name==('public',q.NAME) else z.TYPES
            expected_owner = P_OWNER if name==('public',P_NAME) else q.OWNER if name==('public',q.NAME) else z.OWNER
            if vector!=tuple(('pg_catalog',t) for t in expected_types) or owner['newowner'].get('rolename')!=expected_owner:
                raise ValueError('Capability ownership/signature mismatch')
            owners[name] = expected_owner
            if name==('public',P_NAME): p_statements.append(statement)
        elif 'GrantStmt' in statement and statement['GrantStmt']['objtype']=='OBJECT_FUNCTION':
            grant = statement['GrantStmt']
            if grant.get('grant_option') or (grant.get('is_grant') and not grant.get('privileges')) or any(
                    p['AccessPriv']['priv_name']!='execute' for p in grant.get('privileges',[])):
                raise ValueError('Unapproved function grant privilege')
            p_only = True
            for obj in grant['objects']:
                fn = obj['ObjectWithArgs']; name = strings(fn['objname'])
                types = tuple(strings(t['TypeName']['names']) for t in fn.get('objargs',[]))
                if any(len(t)!=2 or t[0]!='pg_catalog' for t in types):
                    raise ValueError('Unqualified function grant type')
                vector = tuple(t[1] for t in types)
                for recipient in grant['grantees']:
                    role = recipient['RoleSpec']; item = (*name,vector,role.get('rolename'))
                    if grant.get('is_grant'):
                        if item in grants: raise ValueError('Duplicate capability grant')
                        grants.add(item); p_only &= item in EXECUTE
                    else:
                        key = (*name,vector)
                        if role['roletype']!='ROLESPEC_PUBLIC' or key in revokes:
                            raise ValueError('Unapproved/duplicate function revoke')
                        revokes.add(key); p_only &= key==('public',P_NAME,P_TYPES)
            if p_only: p_statements.append(statement)
    expected_revokes = {('public',P_NAME,P_TYPES)} if ('public',P_NAME) in by_name else set()
    if ('public',z.NAME) in by_name: expected_revokes.add(('public',z.NAME,z.TYPES))
    if ('public',q.NAME) in by_name: expected_revokes.add(('public',q.NAME,q.TYPES))
    if grants!=expected_execute or revokes!=expected_revokes or set(owners)!=set(by_name):
        raise ValueError('Exact capability EXECUTE/ownership closure mismatch')
    result = check_p(p_statements,expected_columns)
    if ('public',z.NAME) in by_name: result.update(z.check(by_name[('public',z.NAME)],expected_columns))
    if ('public',q.NAME) in by_name: result.update(q.check(by_name[('public',q.NAME)],expected_columns))
    return result


def strings(names): return tuple(n['String']['sval'] for n in names)


def function_grants(statements):
    actual=set();revoke=set()
    for statement in statements:
        grant=statement.get('GrantStmt')
        if not grant or grant['objtype']!='OBJECT_FUNCTION':continue
        if grant.get('grant_option') or any(p['AccessPriv']['priv_name']!='execute' for p in grant.get('privileges',[])):
            raise ValueError('Unapproved function grant privilege')
        if grant.get('is_grant') and not grant.get('privileges'):raise ValueError('Function ALL grant forbidden')
        for obj in grant['objects']:
            fn=obj['ObjectWithArgs'];schema,name=strings(fn['objname'])
            types=[]
            for arg in fn['objargs']:
                names=strings(arg['TypeName']['names'])
                if len(names)!=2 or names[0]!='pg_catalog':raise ValueError('Unqualified function grant type')
                types.append(names[1])
            for grantee in grant['grantees']:
                role=grantee['RoleSpec'];recipient=role.get('rolename')
                item=(schema,name,tuple(types),recipient)
                if grant.get('is_grant'):
                    if item in actual:raise ValueError('Duplicate capability grant')
                    actual.add(item)
                else:
                    if role['roletype']!='ROLESPEC_PUBLIC' or (schema,name,tuple(types))!=('public',P_NAME,P_TYPES):
                        raise ValueError('Unapproved function revoke')
                    revoke.add((schema,name,tuple(types)))
    if actual!=EXECUTE or revoke!={('public',P_NAME,P_TYPES)}:
        raise ValueError('P exact function EXECUTE manifest mismatch')


def check_p(statements, expected_columns):
    from pglast.parser import parse_sql_json
    definitions=[s['CreateFunctionStmt'] for s in statements if 'CreateFunctionStmt' in s]
    if not definitions:return {'internal_p_source':'NOT_IMPLEMENTED'}
    if len(definitions)!=1:raise ValueError('Unreviewed additional capability definition')
    fn=definitions[0]
    if strings(fn['funcname'])!=('public',P_NAME) or fn.get('replace'):raise ValueError('P definition identity/replace forbidden')
    parameters=[p['FunctionParameter'] for p in fn['parameters']]
    if tuple(p['name'] for p in parameters)!=P_NAMES or any(p.get('defexpr') or p['mode']!='FUNC_PARAM_DEFAULT' for p in parameters):
        raise ValueError('P argument contract mismatch')
    if tuple(strings(p['argType']['names']) for p in parameters)!=tuple(('pg_catalog',t) for t in P_TYPES):
        raise ValueError('P input type vector mismatch')
    if strings(fn['returnType']['names'])!=('pg_catalog','bool') or fn['returnType'].get('setof'):
        raise ValueError('P output type mismatch')
    options={o['DefElem']['defname']:o['DefElem']['arg'] for o in fn['options']}
    if (set(options)!={'language','volatility','security','strict','set','as'} or
        options['language']!={'String':{'sval':'plpgsql'}} or options['volatility']!={'String':{'sval':'volatile'}} or
        options['security']!={'Boolean':{'boolval':True}} or options['strict']!={'Boolean':{'boolval':False}}):
        raise ValueError('P security/volatility/null-call options mismatch')
    setting=options['set']['VariableSetStmt']
    if setting['name']!='search_path' or [a['A_Const']['sval']['sval'] for a in setting['args']]!=['pg_catalog','pg_temp']:
        raise ValueError('P fixed search path mismatch')
    body=options['as']['List']['items'][0]['String']['sval']
    import pglast
    pl=pglast.parse_plpgsql('CREATE FUNCTION public.'+P_NAME+'('+','.join(n+' pg_catalog.'+t for n,t in zip(P_NAMES,P_TYPES))+') RETURNS pg_catalog.bool LANGUAGE plpgsql AS $body$'+body+'$body$;')
    expressions=[]
    def walk_pl(node):
        if isinstance(node,list):
            for child in node:walk_pl(child)
        elif isinstance(node,dict):
            if 'PLpgSQL_stmt_dynexecute' in node:raise ValueError('P dynamic SQL forbidden')
            if 'PLpgSQL_stmt_execsql' in node:
                query=node['PLpgSQL_stmt_execsql']['sqlstmt']['PLpgSQL_expr']['query']
                if not query.lstrip().upper().startswith('SELECT'):
                    raise ValueError('P semantic DML/DDL forbidden')
            if 'PLpgSQL_expr' in node:expressions.append(node['PLpgSQL_expr']['query'])
            for child in node.values():walk_pl(child)
    walk_pl(pl)
    allowed_reads={(relation,column) for owner,relation,column,privilege in expected_columns if owner==P_OWNER and privilege=='select'}
    observed=set();locks=[]
    def scan(node,aliases):
        if isinstance(node,list):
            for child in node:scan(child,aliases)
        elif isinstance(node,dict):
            if 'RangeVar' in node:
                r=node['RangeVar'];schema=r.get('schemaname')
                if schema not in ('public','pg_catalog'):raise ValueError('P unqualified/foreign relation')
                alias=r.get('alias',{}).get('aliasname',r['relname']);aliases[alias]=(schema,r['relname'])
            for child in node.values():scan(child,aliases)
    def columns(node,aliases):
        if isinstance(node,list):
            for child in node:columns(child,aliases)
        elif isinstance(node,dict):
            if 'ColumnRef' in node:
                fields=node['ColumnRef']['fields']
                if any('A_Star' in f for f in fields):raise ValueError('P wildcard projection forbidden')
                names=strings(fields)
                if len(names)==2 and names[0] in aliases:
                    schema,relation=aliases[names[0]]
                    if schema=='public':
                        item=(schema+'.'+relation,names[1]);observed.add(item)
                        if item not in allowed_reads:raise ValueError('P read outside normative column allowlist: '+repr(item))
            if 'FuncCall' in node:
                name=strings(node['FuncCall']['funcname'])
                if len(name)!=2 or name[0] not in ('pg_catalog','public'):raise ValueError('P unqualified function')
                if name[0]=='public' and name!=('public','command_authorization_organization_lock'):
                    raise ValueError('P unexpected privileged function')
                if name[0]=='pg_catalog' and name[1] not in BUILTINS:
                    raise ValueError('P unexpected builtin: '+repr(name))
                if name==('pg_catalog','current_setting'):
                    args=node['FuncCall'].get('args',[])
                    if len(args)!=1 or args[0].get('A_Const',{}).get('sval',{}).get('sval')!='transaction_isolation':
                        raise ValueError('P session setting cannot supply policy/authority')
            for child in node.values():columns(child,aliases)
    for expression in expressions:
        # PL/pgSQL expression text is not SQL by itself; statements already start SELECT.
        expression=re.sub(r'^\s*[a-z_][a-z0-9_]*(?:\[[^]]+\])?\s*:=\s*','',expression,flags=re.I)
        query=expression if expression.lstrip().upper().startswith('SELECT') else 'SELECT '+expression
        parsed=json.loads(parse_sql_json(query))['stmts']
        for raw in parsed:
            statement=raw['stmt']
            if set(statement)!={'SelectStmt'}:raise ValueError('P semantic DML/DDL forbidden')
            if statement['SelectStmt'].get('intoClause'):raise ValueError('P relation-creating SELECT forbidden')
            aliases={};scan(statement,aliases);columns(statement,aliases)
            if statement['SelectStmt'].get('lockingClause'):
                relations=[schema+'.'+name for schema,name in aliases.values() if schema=='public']
                locks.extend(relations)
    if locks!=['public.offline_binding_lifecycle','public.offline_attempt_pointer','public.offline_attempt',
               'public.offline_execution','public.command_principal']:
        raise ValueError('P exact lock order mismatch')
    owners=[s['AlterOwnerStmt'] for s in statements if 'AlterOwnerStmt' in s]
    if len(owners)!=1 or owners[0]['newowner'].get('rolename')!=P_OWNER:
        raise ValueError('P exact owner mismatch')
    owner=owners[0]
    object=owner.get('object',{}).get('ObjectWithArgs',{})
    if owner['objectType']!='OBJECT_FUNCTION' or strings(object.get('objname',[]))!=('public',P_NAME) or tuple(
        strings(arg['TypeName']['names']) for arg in object.get('objargs',[]))!=tuple(('pg_catalog',t) for t in P_TYPES):
        raise ValueError('Ownership change outside exact P signature')
    function_grants(statements)
    return {'internal_p_source':'BOUNDED_STATIC_PASS_NOT_RUNTIME_PROOF','internal_p_read_columns':len(observed),
            'internal_p_lock_order':locks,'internal_p_execute_grants':2}
