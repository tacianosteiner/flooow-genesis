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


def check(statements, expected_columns):
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
