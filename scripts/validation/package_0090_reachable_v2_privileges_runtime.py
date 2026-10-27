"""Effective ACL/default/role verification; no governed wrapper is invoked."""
import json
from pathlib import Path
import package_0090_source_closure as q
from package_0090_reachable_v2 import OUT

def quote(value):return "'"+str(value).replace("'","''")+"'"
def address(entry):
 if entry.get('binding'):
  b=entry['binding'];column='reltoastrelid' if b['kind']=='TOAST_OF' else 'reltype';base='(SELECT '+column+' FROM pg_class WHERE oid='+quote(b['parent'])+'::regclass)'
  return '(SELECT typarray FROM pg_type WHERE oid='+base+')' if b['kind']=='ROWARRAY_OF' else base
 return quote(entry['object'])
def public(entry,grant=False):
 kind=entry['kind'];obj=address(entry);priv=quote(entry['privilege']);go=' AND a.is_grantable' if grant else ''
 if kind=='column':
  col=quote(entry['column']);base=public({**entry,'kind':'table'},grant);suffix='' if entry.get('binding') else '::regclass';return '('+base+" OR EXISTS(SELECT 1 FROM pg_attribute c CROSS JOIN LATERAL aclexplode(c.attacl) a WHERE c.attrelid="+obj+suffix+" AND c.attname="+col+" AND a.grantee=0 AND upper(a.privilege_type)="+priv+go+'))'
 tables={'database':('pg_database','datname','datacl','datdba','d'), 'schema':('pg_namespace','nspname','nspacl','nspowner','n'),'function':('pg_proc','oid','proacl','proowner','f'),'table':('pg_class','oid','relacl','relowner','r'),'type':('pg_type','oid','typacl','typowner','T')}
 table,key,acl,owner,default=tables[kind];object_address=obj+('' if entry.get('binding') else {'function':'::regprocedure','table':'::regclass','type':'::regtype'}.get(kind,''))
 return 'EXISTS(SELECT 1 FROM '+table+' c CROSS JOIN LATERAL aclexplode(COALESCE(c.'+acl+',acldefault('+quote(default)+',c.'+owner+'))) a WHERE c.'+key+'='+object_address+' AND a.grantee=0 AND upper(a.privilege_type)='+priv+go+')'
def expression(entry,grant=False):
 if entry['role']=='PUBLIC':return public(entry,grant)
 privilege=entry['privilege']+(' WITH GRANT OPTION' if grant else '');args=[quote(entry['role']),address(entry)]
 if entry['kind']=='column':args.append(quote(entry['column']))
 args.append(quote(privilege));function={'table':'table','column':'column','type':'type','function':'function','schema':'schema','database':'database'}[entry['kind']]
 return 'pg_catalog.has_'+function+'_privilege('+','.join(args)+')'

def qualify(sql,run,container,folder,record,fixture,runtime_work):
 record['recipe_hashes'][Path(__file__).name]=q.sha(Path(__file__).read_bytes());expected=json.loads((OUT/'effective-acl-v6.json').read_text());entries=expected['entries'];results=[]
 def case(name,passed,details,group):
  row=dict(name=name,passed=bool(passed),details=details,group=group);results.append(row);record['cases'].append(row);q.require(passed,name)
 # Batch bounded sets; the SQL result is only verification of pre-frozen values.
 observed=[]
 for start in range(0,len(entries),256):
  block=entries[start:start+256];query="SELECT jsonb_build_object('allow',ARRAY["+','.join(expression(e) for e in block)+"],'grant',ARRAY["+','.join(expression(e,True) for e in block)+']);';result=json.loads(sql(query).stdout.decode().splitlines()[-1]);observed.extend(zip(result['allow'],result['grant']))
 for i,(entry,(allowed,grantable)) in enumerate(zip(entries,observed)):
  case('effective_acl_'+str(i),allowed==entry['allowed'] and grantable==entry['grantable'],dict(role=entry['role'],kind=entry['kind'],object=entry['object'],column=entry.get('column'),privilege=entry['privilege'],expected=[entry['allowed'],entry['grantable']],observed=[allowed,grantable]),'ACL')
 roles=json.loads((OUT/'role-graph-v2.json').read_text());names=','.join(quote(x['name']) for x in roles['roles']);query="SELECT jsonb_agg(jsonb_build_object('name',rolname,'login',rolcanlogin,'inherit',rolinherit,'superuser',rolsuper,'create_role',rolcreaterole,'create_db',rolcreatedb,'replication',rolreplication,'bypass_rls',rolbypassrls) ORDER BY rolname) FROM pg_roles WHERE rolname IN ("+names+");";actual=json.loads(sql(query).stdout);byname={x['name']:x for x in actual}
 for row in roles['roles']:case('role_'+row['name'],row==byname.get(row['name']),dict(expected=row,observed=byname.get(row['name'])),'ACL')
 memberships=sql('SELECT count(*) FROM pg_auth_members WHERE member IN (SELECT oid FROM pg_roles WHERE rolname IN ('+names+')) OR roleid IN (SELECT oid FROM pg_roles WHERE rolname IN ('+names+'));').stdout.strip();case('role_relevant_memberships_absent',memberships==b'0',dict(observed=memberships.decode(),source='Canonical and approved bootstrap contain no memberships for package identities'),'ACL')
 defaults=json.loads((OUT/'default-bootstrap-v2.json').read_text())
 for creator in defaults['creators']:
  for kind in defaults['object_kinds']:
   # No schema-local or extra-grantee default rows may silently add authority.
   query="SELECT jsonb_build_object('public',(SELECT count(*) FROM pg_roles r CROSS JOIN LATERAL aclexplode(COALESCE((SELECT d.defaclacl FROM pg_default_acl d WHERE d.defaclrole=r.oid AND d.defaclnamespace=0 AND d.defaclobjtype="+quote(kind)+"),acldefault("+quote(kind)+"::\"char\",r.oid))) a WHERE r.rolname="+quote(creator)+" AND a.grantee=0),'extra',(SELECT count(*) FROM pg_default_acl d JOIN pg_roles r ON r.oid=d.defaclrole CROSS JOIN LATERAL aclexplode(d.defaclacl) a WHERE r.rolname="+quote(creator)+" AND d.defaclobjtype="+quote(kind)+" AND (d.defaclnamespace<>0 OR a.grantee NOT IN (0,r.oid))));";a=json.loads(sql(query).stdout);case('default_'+creator+'_'+kind,a==dict(public=0,extra=0),a,'ACL')
 (folder/'effective-acl-runtime.json').write_text(json.dumps(dict(cases=results,total_entries=len(entries),observed_allow_and_grant=list(observed),role_observations=actual),indent=2)+'\n')
