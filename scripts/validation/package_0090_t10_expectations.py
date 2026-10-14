"""Independent direct S04 access submanifest, never full-path eligibility authority."""
import json
from pathlib import Path
import package_0090_source_closure as q
import package_0090_semantic_ledger as ledger

BASELINE='357e980e65eaedbaf305d20f4d663c12a28a92cc'
OUT=q.ROOT/'docs/evidence/package-0090-t10-governed-currentness-closure'
SERVICE=['test_0090_'+x for x in ['verification','issuance','execution','audit']]
OWNERS=['flooow_offline_'+x+'_owner' for x in ['control','verification','issuance','execution','audit','readiness','principal_lock','intent_audit']]
PRINCIPALS=['PUBLIC']+SERVICE+OWNERS
TABLES=['public.flyway_schema_history','public.offline_binding_header','public.offline_deadline_policy','public.offline_readiness']
PRIVS=['SELECT','INSERT','UPDATE','DELETE','TRUNCATE','REFERENCES','TRIGGER','MAINTAIN']


def save(name,value): (OUT/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


def expected(parser):
    """Compute access from DDL/GRANT AST, never catalog rows or target digest."""
    source=q.git('show',BASELINE+':'+q.V043.relative_to(q.ROOT).as_posix())
    q.require(q.sha(source)==q.SOURCE_HASH,'Canonical source differs')
    tree=json.loads(parser(source.decode()))['stmts']
    columns={'public.flyway_schema_history':['installed_rank','version','description','type','script','checksum','installed_by','installed_on','execution_time','success']}
    owners={'public.flyway_schema_history':'postgres'}; grants={}; function=None
    for ordinal,raw in enumerate(tree):
        node=raw['stmt']
        if 'CreateStmt' in node:
            s=node['CreateStmt']; r=s['relation']; name=r.get('schemaname','public')+'.'+r['relname']
            if name in TABLES:
                columns[name]=[x['ColumnDef']['colname'] for x in s.get('tableElts',[]) if 'ColumnDef' in x]
        if 'AlterOwnerStmt' in node:
            s=node['AlterOwnerStmt']
            if 'relation' in s:
                r=s['relation']; name=r.get('schemaname','public')+'.'+r['relname']
                if name in TABLES: owners[name]=s['newowner']['rolename']
        if 'AlterTableStmt' in node:
            s=node['AlterTableStmt']; r=s['relation']; name=r.get('schemaname','public')+'.'+r['relname']
            for command in s.get('cmds',[]):
                command=command['AlterTableCmd']
                if name in TABLES and command['subtype']=='AT_ChangeOwner': owners[name]=command['newowner']['rolename']
        if 'CreateFunctionStmt' in node and ledger.signature(node['CreateFunctionStmt'])=='public.offline_read_history(uuid,bytea,uuid,text)':
            f=node['CreateFunctionStmt']; opts={x['DefElem']['defname']:x['DefElem'].get('arg') for x in f['options']}
            body=opts['as']['List']['items'][0]['String']['sval']
            function=dict(signature=ledger.signature(f),owner='flooow_offline_audit_owner',language='plpgsql',security_definer=True,volatility='s',strict=False,parallel='u',search_path=['search_path=pg_catalog, pg_temp'],body_sha256=q.sha(body.encode()),source_statement_ordinal=ordinal)
        if 'GrantStmt' not in node: continue
        g=node['GrantStmt']
        if g['objtype']!='OBJECT_TABLE' or g.get('targtype') not in [None,'ACL_TARGET_OBJECT']: continue
        for obj in g.get('objects',[]):
            if 'RangeVar' not in obj: continue
            rv=obj['RangeVar']; table=rv.get('schemaname','public')+'.'+rv['relname']
            if table not in TABLES: continue
            for role in g['grantees']:
                role=role['RoleSpec'].get('rolename','PUBLIC')
                ps=g.get('privileges') or [{'AccessPriv':{'priv_name':x.lower()}} for x in PRIVS]
                for p in ps:
                    p=p['AccessPriv']; targets=[x['String']['sval'] for x in p.get('cols',[])] or [None]
                    for col in targets:
                        key=(role,table,col,p['priv_name'].upper())
                        if g.get('is_grant'): grants[key]=bool(g.get('grant_option'))
                        else: grants.pop(key,None)
    q.require(function is not None and set(owners)==set(TABLES),'Source object extraction incomplete')
    entries=[]
    for role in PRINCIPALS:
        # PG18 bootstrap semantics and approved foundation recipe are named
        # separately from canonical grants. Unknown wider bootstrap objects stop gate.
        for privilege in ['CONNECT','TEMPORARY','CREATE']:
            entries.append(dict(role=role,kind='database',object='g3f4',privilege=privilege,allowed=privilege!='CREATE',grantable=False,provenance='Pinned PG18 fresh CREATE DATABASE bootstrap: PUBLIC CONNECT/TEMP; postgres owner; no memberships'))
        for schema in ['public','pg_catalog']:
            for privilege in ['USAGE','CREATE']:
                entries.append(dict(role=role,kind='schema',object=schema,privilege=privilege,allowed=privilege=='USAGE',grantable=False,provenance='Pinned PG18 bootstrap plus source/test schema USAGE grants; no relevant schema-owner membership'))
        entries.append(dict(role=role,kind='function',object=function['signature'],privilege='EXECUTE',allowed=role in ['test_0090_audit','flooow_offline_audit_owner'],grantable=role=='flooow_offline_audit_owner',provenance='Canonical S04 owner/PUBLIC revoke; frozen foundation direct LOGIN wrapper grant'))
        for table in TABLES:
            for column in [None]+columns[table]:
                for priv in PRIVS if column is None else ['SELECT','INSERT','UPDATE','REFERENCES']:
                    owner=role==owners[table]
                    keys=[(r,table,c,priv) for r in [role,'PUBLIC'] for c in ([None] if column is None else [None,column])]
                    allowed=owner or any(k in grants for k in keys)
                    grantable=owner or any(grants.get(k,False) for k in keys)
                    entries.append(dict(role=role,kind='table' if column is None else 'column',object=table,column=column,privilege=priv,allowed=allowed,grantable=grantable,provenance='Canonical V043 GRANT/REVOKE/OWNER AST; Flyway-owned history default has no PUBLIC grants; zero relevant memberships'))
    return dict(scope='DIRECT_S04_ACCESS_SUBMANIFEST_NOT_COMPLETE_FIRST_PATH',complete=False,entries=entries,source_owners=owners,source_columns=columns,function=function,role_memberships_expected=[],uncovered=['Reachable pg_catalog operator/cast/function effective privileges and exact identities','All wider readiness/currentness observer dependencies','Sequences outside direct S04 relation graph','Full default privilege and bootstrap schema/catalog expectation closure'],expected_derived_from_target=False)


def qualify(sql,run,container,folder,record,fixture,runtime_work):
    manifest=json.loads((OUT/'effective-acl-expectation.json').read_text())
    entries=manifest['entries']; observed=[]; cases=[]
    def case(name,passed,details):
        item=dict(name=name,passed=bool(passed),details=details,group='EXPECTATION')
        cases.append(item); record['cases'].append(item); q.require(passed,name)
    # PUBLIC effective privilege means rights common through the actual PUBLIC
    # ACL, not a fabricated LOGIN named PUBLIC. Inspect aclexplode directly.
    for role in PRINCIPALS:
        own=[x for x in entries if x['role']==role]
        expressions=[]
        for e in own:
            obj=e['object'].replace("'","''"); priv=e['privilege']
            if role=='PUBLIC':
                if e['kind']=='column':
                    base="EXISTS(SELECT 1 FROM pg_class c JOIN pg_attribute a ON a.attrelid=c.oid CROSS JOIN LATERAL aclexplode(a.attacl) x WHERE c.oid='%s'::regclass AND a.attname='%s' AND x.grantee=0 AND upper(x.privilege_type)='%s' %%s)"%(obj,e['column'],priv)
                    table="EXISTS(SELECT 1 FROM pg_class c CROSS JOIN LATERAL aclexplode(coalesce(c.relacl,acldefault('r',c.relowner))) x WHERE c.oid='%s'::regclass AND x.grantee=0 AND upper(x.privilege_type)='%s' %%s)"%(obj,priv)
                    pair=[ '('+(base%extra)+' OR '+(table%extra)+')' for extra in ['', 'AND x.is_grantable'] ]
                else:
                    rel,key,acl,owner,code,cast={'database':('pg_database','datname','datacl','datdba','d',None),'schema':('pg_namespace','nspname','nspacl','nspowner','n',None),'function':('pg_proc','oid','proacl','proowner','f','regprocedure'),'table':('pg_class','oid','relacl','relowner','r','regclass')}[e['kind']]
                    identity="t.%s='%s'"%(key,obj)+(('::'+cast) if cast else '')
                    base="EXISTS(SELECT 1 FROM %s t CROSS JOIN LATERAL aclexplode(coalesce(t.%s,acldefault('%s',t.%s))) x WHERE %s AND x.grantee=0 AND upper(x.privilege_type)='%s' %%s)"%(rel,acl,code,owner,identity,priv)
                    pair=[base%extra for extra in ['', 'AND x.is_grantable']]
            else:
                fun={'database':'has_database_privilege','schema':'has_schema_privilege','function':'has_function_privilege','table':'has_table_privilege','column':'has_column_privilege'}[e['kind']]
                args="'%s','%s',"%(role,obj)+("'%s',"%e['column'] if e['kind']=='column' else '')
                pair=[fun+'('+args+"'%s')"%p for p in [priv,priv+' WITH GRANT OPTION']]
            expressions.append('json_build_array('+','.join(pair)+')')
        rows=[]
        for start in range(0,len(expressions),50):
            rows.extend(json.loads(sql('SELECT json_build_array('+','.join(expressions[start:start+50])+');').stdout))
        mismatches=[]
        for e,r in zip(own,rows):
            observed.append(dict(expected=e,observed_allowed=r[0],observed_grantable=r[1]))
            if [e['allowed'],e['grantable']]!=r: mismatches.append(dict(entry=e,observed=r))
        case('direct_S04_effective_access_'+role,not mismatches,mismatches)
    for role in SERVICE+OWNERS:
        expected_attrs=dict(rolcanlogin=role in SERVICE,rolinherit=role==OWNERS[0],rolsuper=False,rolcreatedb=False,rolcreaterole=False,rolreplication=False,rolbypassrls=False)
        actual=json.loads(sql("SELECT row_to_json(r) FROM (SELECT oid,rolname,rolcanlogin,rolinherit,rolsuper,rolcreatedb,rolcreaterole,rolreplication,rolbypassrls,rolvaliduntil FROM pg_roles WHERE rolname='%s') r;"%role).stdout)
        memberships=int(sql("SELECT count(*) FROM pg_auth_members WHERE member=%s OR roleid=%s;"%(actual['oid'],actual['oid'])).stdout)
        case('restricted_role_graph_'+role,all(actual[k]==v for k,v in expected_attrs.items()) and memberships==0 and actual['rolvaliduntil'] is None,dict(observed=actual,membership_count=memberships,oid_rule='Unique runtime OID observed under trusted bootstrap; no deterministic OID or enrolled slot claim'))
    f=manifest['function']
    actual=json.loads(sql("SELECT json_build_object('owner',pg_get_userbyid(p.proowner),'language',l.lanname,'security_definer',p.prosecdef,'volatility',p.provolatile,'strict',p.proisstrict,'parallel',p.proparallel,'search_path',p.proconfig,'body_sha256',encode(sha256(convert_to(p.prosrc,'UTF8')),'hex')) FROM pg_proc p JOIN pg_language l ON l.oid=p.prolang WHERE p.oid='%s'::regprocedure;"%f['signature']).stdout)
    case('direct_S04_function_identity',all(actual[k]==f[k] for k in actual),actual)
    (folder/'expectation-runtime.json').write_text(json.dumps(dict(cases=cases,entries=observed,effective_entries=len(entries),submanifest_match=True,complete_first_path_manifest=False,canonical_executed=False),indent=2)+'\n')
