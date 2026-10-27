"""Independent effective privilege and relevant role/default-privilege matrix."""
import json
import package_0090_source_closure as q
import package_0090_reachable_v2 as e
import package_0090_t10_expectations as direct
OUT=e.OUT

def quote(name):return chr(34)+name.replace(chr(34),chr(34)*2)+chr(34)

def prepare(r):
 prior=json.loads((OUT/'effective-acl-v6.json').read_text());entries=list(prior.get('direct_source_entries',[x for x in prior.get('entries',[]) if x['object'] in ['g3f4','public','pg_catalog','public.offline_read_history(uuid,bytea,uuid,text)'] or x['object'] in direct.TABLES]));principals=direct.PRINCIPALS+['postgres'];functions=json.loads((OUT/'function-identity-v6.json').read_text());types=json.loads((OUT/'type-reachability-v2.json').read_text())['types'];rels=json.loads((OUT/'relation-view-v2.json').read_text())['relations'];cols=json.loads((OUT/'column-v2.json').read_text())['columns']
 def add(role,kind,obj,priv,allowed,grantable=False,column=None,derivation='PUBLIC'):
  entries.append(dict(role=role,kind=kind,object=obj,privilege=priv,allowed=allowed,grantable=grantable,column=column,derivation=derivation))
 # Source function grants are processed independently of observed ACL arrays.
 source_acls={x['signature'].split('(')[0]:{} for x in functions['canonical_functions']}
 for raw in r.tree:
  g=raw['stmt'].get('GrantStmt')
  if not g or g['objtype']!='OBJECT_FUNCTION':continue
  for obj in g.get('objects',[]):
   obj=obj.get('ObjectWithArgs',{});name='.'.join(x['String']['sval'] for x in obj.get('objname',[]));name='public.'+name if '.'not in name else name
   if name not in source_acls:continue
   for grantee in g['grantees']:
    role=grantee['RoleSpec'].get('rolename','PUBLIC')
    if g.get('is_grant'):source_acls[name][role]=bool(g.get('grant_option'))
    else:source_acls[name].pop(role,None)
 # Approved foundation grants the audit wrapper family to its fresh LOGIN.
 source_acls['public.offline_read_history']['test_0090_audit']=False
 # Exclude bootstrap SQL privilege overrides by exact signature, not by name.
 signatures={(p['proname'],tuple(r.args(p))) for p in functions['provider_functions']}
 for raw in json.loads(r.parser((OUT/'provider/system_functions.sql').read_text()))['stmts']:
  g=raw['stmt'].get('GrantStmt')
  if not g or g['objtype']!='OBJECT_FUNCTION':continue
  for obj in g.get('objects',[]):
   obj=obj.get('ObjectWithArgs',{});name='.'.join(x['String']['sval'] for x in obj.get('objname',[]));name='pg_catalog.'+name if '.'not in name else name;sig=name+'('+','.join(r.typename(t['TypeName']) for t in obj.get('objargs',[]))+')'
   q.require((name.split('.')[-1],tuple(r.typename(t['TypeName']) for t in obj.get('objargs',[]))) not in signatures,'Unimplemented bootstrap function ACL override '+sig)
 for role in principals:
  superuser=role=='postgres'
  for native in functions['native_functions']:
   schema=native['signature'].split('.')[0];name=native['signature'].split('(')[0].split('.')[-1]
   allowed=superuser or schema=='pg_catalog' or role=='flooow_offline_readiness_owner' and name in ['hmac','timing_safe_equal32'] or role=='flooow_offline_verification_owner' and name=='canonical_spki_ed25519_verify'
   add(role,'function',native['signature'],'EXECUTE',allowed,superuser,derivation='plpgsql bootstrap PUBLIC default; explicit approved crypto/native grants and canonical verification grant')
  for privilege in ['USAGE','CREATE']:
   allowed=superuser or privilege=='USAGE' and role in ['flooow_offline_readiness_owner','flooow_offline_verification_owner']
   add(role,'schema','offline_crypto',privilege,allowed,superuser,derivation='Approved TEST bootstrap plus canonical schema usage grant')
  for p in functions['provider_functions']:add(role,'function','pg_catalog.'+quote(p['proname'])+'('+','.join('pg_catalog.'+quote(a) for a in r.args(p))+')','EXECUTE',True,superuser,derivation='PUBLIC + OWNERSHIP/SUPERUSER')
  for p in functions['canonical_functions']:
   name=p['signature'].split('(')[0];owner=role==p['owner'];grants=source_acls[name];add(role,'function',p['signature'],'EXECUTE',superuser or owner or role in grants or 'PUBLIC'in grants,superuser or owner or bool(grants.get(role)) or bool(grants.get('PUBLIC')),derivation='DIRECT + OWNERSHIP + SECURITY_DEFINER_CONTEXT')
  for typ in types:add(role,'type','pg_catalog.'+quote(typ['typname']),'USAGE',True,superuser,derivation='PG acldefault TYPE PUBLIC USAGE; bootstrap core types predate TEST future-default revokes')
  # These relations include the definer-expanded pg_roles inputs. pg_authid
  # PUBLIC SELECT was independently revoked by initdb setup_auth.
  for rel in rels:
   name=rel['name']
   if name.startswith('pg_catalog.'):
    public_read=name!='pg_catalog.pg_authid'
    for priv in direct.PRIVS:add(role,'table',name,priv,superuser or public_read and priv=='SELECT',superuser,derivation='initdb setup_privileges/setup_auth; pg_roles view owner is postgres')
    for col in [x for x in cols if x['relation']==name]:
     for priv in ['SELECT','INSERT','UPDATE','REFERENCES']:add(role,'column',name,priv,superuser or public_read and priv=='SELECT',superuser,column=col['name'],derivation='Inherited relation ACL; no catalog column grants')
  for rel in rels:
   table=rel['name']
   if not table.startswith('public.') or table in direct.TABLES:continue
   table_grants={}
   for raw in r.tree:
    g=raw['stmt'].get('GrantStmt')
    if not g or g['objtype']!='OBJECT_TABLE':continue
    for obj in g.get('objects',[]):
     rv=obj.get('RangeVar')
     if not rv or rv.get('schemaname','public')+'.'+rv['relname']!=table:continue
     privileges=g.get('privileges') or [{'AccessPriv':{'priv_name':p}} for p in direct.PRIVS]
     for item in privileges:
      p=item['AccessPriv']
      if p.get('cols'):continue
      for target in g['grantees']:
       grantee=target['RoleSpec'].get('rolename','PUBLIC');key=(grantee,p['priv_name'].upper())
       if g.get('is_grant'):table_grants[key]=bool(g.get('grant_option'))
       else:table_grants.pop(key,None)
   owner=role==rel['owner']
   for privilege in direct.PRIVS:
    allowed=superuser or owner or any((grantee,privilege) in table_grants for grantee in [role,'PUBLIC']);grantable=superuser or owner or any(table_grants.get((grantee,privilege),False) for grantee in [role,'PUBLIC']);add(role,'table',table,privilege,allowed,grantable,derivation='Canonical FK closure table GRANT/REVOKE/OWNER')
   for column in [c for c in cols if c['relation']==table]:
    for privilege in ['SELECT','INSERT','UPDATE','REFERENCES']:
     grants=column['column_acl'] or [];allowed=superuser or owner or any((grantee,privilege) in table_grants for grantee in [role,'PUBLIC']) or any(g['grantee'] in [role,'PUBLIC'] and g['privilege']==privilege for g in grants);grantable=superuser or owner or any(table_grants.get((grantee,privilege),False) for grantee in [role,'PUBLIC']) or any(g['grantee']in [role,'PUBLIC'] and g['privilege']==privilege and g['grantable'] for g in grants);add(role,'column',table,privilege,allowed,grantable,column=column['name'],derivation='Canonical column ACL plus effective relation privilege')
  if superuser:
   for entry in prior.get('direct_source_entries',[x for x in prior.get('entries',[]) if x['object'] in ['g3f4','public','pg_catalog','public.offline_read_history(uuid,bytea,uuid,text)'] or x['object'] in direct.TABLES]):
    if entry['role']=='PUBLIC':entries.append({**entry,'role':'postgres','allowed':True,'grantable':True,'derivation':'SUPERUSER/OWNERSHIP'})
 storage=json.loads((OUT/'storage-dependency-v2.json').read_text())
 for role in principals:
  for privilege in ['USAGE','CREATE']:add(role,'schema','pg_toast',privilege,role=='postgres',role=='postgres',derivation='Bootstrap pg_toast namespace owner is postgres; no PUBLIC grants')
  for parent in storage['parents']:
   if not parent['required']:continue
   allowed=role in ['postgres',parent['owner']];object_name='${TOAST_OF:'+parent['parent']+'}'
   for privilege in direct.PRIVS:
    effective=allowed and (role=='postgres' or privilege not in ['INSERT','UPDATE','DELETE','TRUNCATE'])
    add(role,'table',object_name,privilege,effective,allowed,derivation='Native TOAST owner follows parent; pg_class_aclmask system-class modification mask denies non-superuser INSERT/UPDATE/DELETE/TRUNCATE; owner grant option remains distinct');entries[-1]['binding']=dict(kind='TOAST_OF',parent=parent['parent'])
   for column in ['chunk_id','chunk_seq','chunk_data']:
    for privilege in ['SELECT','INSERT','UPDATE','REFERENCES']:
     effective=allowed and (role=='postgres' or privilege not in ['INSERT','UPDATE'])
     add(role,'column',object_name,privilege,effective,allowed,column=column,derivation='Native TOAST parent owner; relation system-class modification mask; no additional column ACL');entries[-1]['binding']=dict(kind='TOAST_OF',parent=parent['parent'])
 # De-duplicate only identical privilege queries, never distinct expression sites.
 keyed={}
 for x in entries:
  key=(x['role'],x['kind'],x['object'],x.get('column'),x['privilege'])
  if key in keyed:q.require((x['allowed'],x['grantable'])==(keyed[key]['allowed'],keyed[key]['grantable']),'Independent ACL derivations conflict '+str(key))
  keyed[key]=x
 for relation in json.loads((OUT/'relation-view-v2.json').read_text())['relations']:
  for kind in ['ROWTYPE_OF','ROWARRAY_OF']:
   for role in principals:
    entry=dict(role=role,kind='type',object='${'+kind+':'+relation['name']+'}',privilege='USAGE',allowed=True,grantable=role in ['postgres',relation['owner']],column=None,derivation='PG TypeCreate dependent relation/array types have NULL ACL, acldefault gives PUBLIC USAGE; owner/superuser grant option remains distinct',binding=dict(kind=kind,parent=relation['name']))
    keyed[(role,'type',entry['object'],None,'USAGE')]=entry
 e.save('effective-acl-v6.json',dict(entries=list(keyed.values()),total=len(keyed),principals=principals,independent=True,complete=False,source_function_direct_grants=source_acls,derivation_sources=['canonical GRANT/REVOKE/OWNER AST','approved TEST bootstrap without memberships','PG18 initdb/system_functions bootstrap','PG acldefault and ownership/superuser semantics'],security_definer_edges=[dict(function='public.offline_read_history(uuid,bytea,uuid,text)',effective_identity='flooow_offline_audit_owner'),dict(view='pg_catalog.pg_roles',underlying_identity='postgres')]))
 owners=direct.OWNERS
 e.save('role-graph-v2.json',dict(roles=[dict(name=x,login=False,inherit=x=='flooow_offline_control_owner',superuser=False,create_role=False,create_db=False,replication=False,bypass_rls=False) for x in owners]+[dict(name=x,login=True,inherit=False,superuser=False,create_role=False,create_db=False,replication=False,bypass_rls=False) for x in direct.SERVICE],memberships_touching_these_roles=[],additional_identity=dict(name='postgres',bootstrap_OID_rule='BKI superuser OID 10',superuser=True,pg_database_owner='implicit membership for g3f4 owner; no fabricated pg_auth_members edge'),dynamic_OID_rule='Fresh role OIDs are bound by unique exact names and validated attributes; never predicted or used as expected provider truth',independent=True))
 e.save('default-bootstrap-v2.json',dict(creators=['postgres']+owners,object_kinds=['r','S','f','T','n','L'],expected_PUBLIC_privileges=[],expected_extra_grantees=[],owner_default_rule='PG acldefault object-kind owner rights; raw owner grant-option bits false, effective grant option follows ownership',scope='Future object defaults are separate from current object privileges and bootstrap-created catalog ACLs',bootstrap_sources=['foundation approved six-kind default revocation','initdb setup_privileges/setup_auth','system_views pg_roles security-definer expansion'],independent=True))
 print('ACL entries',len(keyed))
if __name__=='__main__':
 import sys
 from pathlib import Path
 sys.path.insert(0,str(Path.home()/'.codex/tmp/package0090-pglast-8.5'));from pglast.parser import parse_sql_json
 r=e.Resolver(parse_sql_json);prepare(r)
