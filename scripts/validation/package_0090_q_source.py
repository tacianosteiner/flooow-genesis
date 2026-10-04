"""Bounded Q source review. SQL parsing/negative checks are not runtime proof."""
import json
import re
from package_0090_capability_source import strings

NAME = 'offline_internal_readiness'
OWNER = 'flooow_offline_readiness_owner'
TYPES = ('uuid','bytea','uuid','text','bytea','bytea','bytea','bytea')
NAMES = ('binding_id','plan_fingerprint','expected_incarnation_id','surface_version',
         'expected_history_digest','expected_acl_digest','expected_policy_digest','preflight_receipt')
GRANTS = {('public',NAME,TYPES,r) for r in ('flooow_offline_audit_owner','flooow_offline_execution_owner')}
USAGE = {'flooow_offline_readiness_owner','flooow_offline_audit_owner','flooow_offline_execution_owner','flooow_offline_principal_lock_owner','flooow_offline_intent_audit_owner'}
BUILTINS = {'octet_length','current_setting','substring','get_byte','convert_from','array_append',
    'sha256','convert_to','clock_timestamp','isfinite','transaction_timestamp','extract','is_normalized',
    'cardinality','array_agg','unnest','aclexplode','acldefault','has_function_privilege',
    'current_database','array_position','has_sequence_privilege','has_table_privilege','has_column_privilege',
    'has_schema_privilege','has_database_privilege','replace','int4send','int8send','uuid_send',
    'count','string_agg','bool_or','split_part','strpos','trunc'}


def check(fn, expected_columns):
    import pglast
    from pglast.parser import parse_sql_json
    if fn.get('replace') or strings(fn['funcname']) != ('public',NAME):
        raise ValueError('Q exact definition identity')
    params = [p['FunctionParameter'] for p in fn['parameters']]
    if len(params)!=8 or any(p.get('defexpr') or p['mode']!='FUNC_PARAM_DEFAULT' or
        p['name']!=n or strings(p['argType']['names'])!=('pg_catalog',t)
        for p,n,t in zip(params,NAMES,TYPES)):
        raise ValueError('Q exact mandatory signature')
    if strings(fn['returnType']['names'])!=('pg_catalog','bytea') or fn['returnType'].get('setof'):
        raise ValueError('Q non-set scalar bytea required')
    options={o['DefElem']['defname']:o['DefElem']['arg'] for o in fn['options']}
    if set(options)!={'language','volatility','security','strict','set','as'} or any(
        options[k]!=v for k,v in {'language':{'String':{'sval':'plpgsql'}},
        'volatility':{'String':{'sval':'stable'}},'security':{'Boolean':{'boolval':True}},
        'strict':{'Boolean':{'boolval':False}}}.items()):
        raise ValueError('Q definer/stable/null-call contract')
    setting=options['set']['VariableSetStmt']
    if setting['name']!='search_path' or [a['A_Const']['sval']['sval'] for a in setting['args']]!=['pg_catalog','pg_temp']:
        raise ValueError('Q fixed search_path')
    body=options['as']['List']['items'][0]['String']['sval']
    pl=pglast.parse_plpgsql('CREATE FUNCTION public.'+NAME+'('+','.join(n+' pg_catalog.'+t for n,t in zip(NAMES,TYPES))+') RETURNS pg_catalog.bytea LANGUAGE plpgsql AS $body$'+body+'$body$;')
    expressions=[]; returns=[]
    def walk(node):
        if isinstance(node,list):
            for child in node: walk(child)
        elif isinstance(node,dict):
            if any(k in node for k in ('PLpgSQL_stmt_dynexecute','PLpgSQL_stmt_commit','PLpgSQL_stmt_rollback',
                'PLpgSQL_stmt_return_query','PLpgSQL_stmt_return_next')):
                raise ValueError('Q dynamic SQL/transaction/set return forbidden')
            if 'PLpgSQL_stmt_execsql' in node:
                query=node['PLpgSQL_stmt_execsql']['sqlstmt']['PLpgSQL_expr']['query']
                if not query.lstrip().upper().startswith(('SELECT','WITH')):
                    raise ValueError('Q DML/DDL forbidden')
            if 'PLpgSQL_expr' in node: expressions.append(node['PLpgSQL_expr']['query'])
            if 'PLpgSQL_stmt_return' in node: returns.append(node['PLpgSQL_stmt_return'])
            for child in node.values(): walk(child)
    walk(pl)
    # Only original receipt and nine-field frame+MAC may leave Q.
    if sorted(r['expr']['PLpgSQL_expr']['query'] for r in returns if 'expr' in r)!=['$8','receipt_frame||receipt_mac']:
        raise ValueError('Q exact original/issued receipt return paths')
    calls=set(); relations=set(); observed=set(); deployment_privileges=[]; deployment_columns=[]
    allowed={(r,c) for o,r,c,p in expected_columns if o==OWNER and p=='select'}
    def review(node, inherited=None):
        if isinstance(node,list):
            for child in node: review(child,inherited)
        elif isinstance(node,dict):
            aliases=dict(inherited or {})
            if 'RangeSubselect' in node:
                sub=node['RangeSubselect']; alias=sub.get('alias',{})
                names=strings(alias.get('colnames',[]))
                inventory = None
                if alias.get('aliasname')=='approved' and names==('role_name','relation','column_name','privilege'):
                    inventory=deployment_privileges
                elif alias.get('aliasname')=='inventory' and names==('relation','column_name'):
                    inventory=deployment_columns
                if inventory is not None:
                    values=sub['subquery']['SelectStmt'].get('valuesLists')
                    if values is None: raise ValueError('Q deployment inventory must be static VALUES')
                    for row in values:
                        items=row['List']['items']
                        if any(set(v)!={'A_Const'} or 'sval' not in v['A_Const'] or
                               set(v['A_Const'])-{'sval','location'} for v in items):
                            raise ValueError('Q dynamic deployment ACL inventory')
                        inventory.append(tuple(v['A_Const']['sval']['sval'] for v in items))
            if 'SelectStmt' in node:
                s=node['SelectStmt']
                if s.get('lockingClause') or s.get('intoClause'):
                    raise ValueError('Q write locks/relation creation forbidden')
                def find_from(v):
                    if isinstance(v,list):
                        for c in v:find_from(c)
                    elif isinstance(v,dict):
                        for kind in ('RangeSubselect','RangeFunction'):
                            if kind in v:
                                alias=v[kind].get('alias',{}).get('aliasname')
                                if alias: aliases.pop(alias,None)
                        if 'RangeVar' in v:
                            r=v['RangeVar']; schema=r.get('schemaname')
                            if schema not in ('public','pg_catalog'):
                                # CTE names are unqualified, never actual tables.
                                if r['relname'] not in ('seed','reachable'): raise ValueError('Q unqualified relation')
                                return
                            qualified=schema+'.'+r['relname']; relations.add(qualified)
                            aliases[r.get('alias',{}).get('aliasname',r['relname'])]=qualified
                        elif 'RangeSubselect' not in v:
                            for c in v.values(): find_from(c)
                find_from(s.get('fromClause',[]))
            if 'ColumnRef' in node:
                fields=node['ColumnRef']['fields']
                if not any('A_Star' in f for f in fields):
                    f=strings(fields)
                    if len(f)==2 and f[0] in aliases:
                        item=(aliases[f[0]],f[1]); observed.add(item)
                        if item not in allowed: raise ValueError('Q unapproved read '+repr(item))
            if 'FuncCall' in node:
                name=strings(node['FuncCall']['funcname']); calls.add(name)
                if name not in {('pg_catalog',n) for n in BUILTINS}|{('offline_crypto','hmac'),('offline_crypto','timing_safe_equal32')}:
                    raise ValueError('Q unapproved callable '+repr(name))
                if name==('pg_catalog','current_setting'):
                    args=node['FuncCall'].get('args',[])
                    if len(args)!=1 or args[0].get('A_Const',{}).get('sval',{}).get('sval') not in ('transaction_isolation','transaction_read_only'):
                        raise ValueError('Q GUC policy/authority forbidden')
            for child in node.values(): review(child,aliases)
    for expression in expressions:
        expression=re.sub(r'^\s*[a-z_][a-z0-9_]*(?:\[[^]]+\])?\s*:=\s*','',expression,flags=re.I)
        query=expression if expression.lstrip().upper().startswith(('SELECT','WITH')) else 'SELECT '+expression
        for raw in json.loads(parse_sql_json(query))['stmts']:
            if set(raw['stmt'])!={'SelectStmt'}: raise ValueError('Q non-read SQL expression')
            review(raw['stmt'])
    expected_deployment={(o,r.split('.',1)[1],c,p.upper()) for o,r,c,p in expected_columns if r.startswith('public.')}
    expected_inventory={(r.split('.',1)[1],c) for o,r,c,p in expected_columns if r.startswith('public.')}
    if len(deployment_privileges)!=len(set(deployment_privileges)) or set(deployment_privileges)!=expected_deployment:
        raise ValueError('Q exact deployment column privilege inventory mismatch')
    if len(deployment_columns)!=len(set(deployment_columns)) or set(deployment_columns)!=expected_inventory:
        raise ValueError('Q exact deployment column projection inventory mismatch')
    required=(
        'IF SESSION_USER=slot_names[4] THEN','ELSIF SESSION_USER=slot_names[3] THEN',
        'IF pg_catalog.octet_length($8)<>0','IF pg_catalog.octet_length($8)=0',
        'FOR field_tag IN 1..29 LOOP','policy_record.policy_digest<>$7',
        'pg_catalog.sha256(policy_record.canonical_policy) <> policy_record.policy_digest',
        'live_history<>ready_record.history_manifest OR pg_catalog.sha256(live_history)<>$5',
        'live_acl<>ready_record.acl_manifest OR pg_catalog.sha256(live_acl)<>$6',
        'IF mac_version<>key_record.key_version THEN',
        "WHERE k.incarnation_id=$3 AND k.key_state='ACTIVE'",
        'key_record.key_version<>ready_record.active_key_version',
        'cursor_position<>pg_catalog.octet_length($8)-32',
        'issued_us+policy_values[27]<>expires_us','issued_us>now_us OR now_us>=expires_us',
        'issued_us := now_us;','expires_us := issued_us+policy_values[27];',
        'now_us := EXTRACT(EPOCH FROM pg_catalog.clock_timestamp())*1000000;',
        "'sha256'::pg_catalog.text",'cursor_position+1,32)::pg_catalog.bytea) IS NOT TRUE',
        'receipt_fields[1]<>pg_catalog.uuid_send($3) OR receipt_fields[2]<>$2',
        'receipt_fields[5]<>$6 OR receipt_fields[6]<>$7',
        'protected_oids[1:11]','approved.column_name=a.attname','FOR history_record IN SELECT',
        'EXCEPTION WHEN OTHERS THEN',"MESSAGE='ACCESS_DENIED'")
    for r in required:
        if r not in body: raise ValueError('Q required guard/dataflow absent: '+r)
    if not {('offline_crypto','hmac'),('offline_crypto','timing_safe_equal32')}<=calls:
        raise ValueError('Q crypto path absent')
    if re.search(r'\b(?:COALESCE|GREATEST|LEAST)\s*\(\s*(?:policy_values\[27\]|issued_us|expires_us)',body,re.I):
        raise ValueError('Q TTL/expiry fallback or clamp')
    executor=body.split('IF NOT auditor_route THEN',1)[1].split('    END IF;\n    -- Full history',1)[0]
    if 'issued_us := now_us' in executor:raise ValueError('Q receipt renewal')
    if len(re.findall('expires_us := issued_us\\+policy_values\\[27\\];',body))!=1:
        raise ValueError('Q sole TTL derivation')
    if re.findall(r'now_us\s*:=\s*([^;]+);',body)!=[
        'EXTRACT(EPOCH FROM pg_catalog.clock_timestamp())*1000000']*2:
        raise ValueError('Q every receipt-time read must use fresh DB wall clock')
    return {'internal_q_source':'BOUNDED_STATIC_PASS_NOT_RUNTIME_PROOF',
        'internal_q_read_columns':len(observed),'internal_q_execute_grants':2,
        'internal_q_no_write_locks':True,'internal_q_receipt_renewal':False,
        'internal_q_key_projection':False,'internal_q_acl_collections':6,
        'internal_q_exact_deployment_column_grants':len(deployment_privileges)}
