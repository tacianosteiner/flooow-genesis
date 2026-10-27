"""Corroborate source-factory storage and default bindings on owned targets."""
import json
from pathlib import Path
import package_0090_source_closure as q
from package_0090_reachable_v2 import OUT
import package_0090_reachable_v2 as e
from package_0090_reachable_v2_metadata_semantics import normalize,parse_expression

def qualify(sql,run,container,folder,record,fixture,runtime_work):
 record['recipe_hashes'][Path(__file__).name]=q.sha(Path(__file__).read_bytes());cases=[];observed={}
 def case(name,passed,details,group='RELATION_VIEW'):
  c=dict(name=name,passed=bool(passed),details=details,group=group);cases.append(c);record['cases'].append(c)
  (folder/'storage-runtime.json').write_text(json.dumps(dict(cases=cases,observed=observed),indent=2)+'\n');q.require(passed,name)
 def last(query):return json.loads(sql(query).stdout.decode().splitlines()[-1])
 def literal(s):return "'"+s.replace("'","''")+"'"
 model=json.loads((OUT/'storage-dependency-v2.json').read_text())
 for parent in model['parents']:
  name=parent['parent'];address=literal(name)+'::regclass'
  a=last("SELECT jsonb_build_object('parent_oid',p.oid::int4,'toast_oid',p.reltoastrelid::int4,'name',c.relname,'schema',n.nspname,'owner',pg_get_userbyid(c.relowner),'kind',c.relkind,'rls',c.relrowsecurity,'force_rls',c.relforcerowsecurity,'persistence',c.relpersistence,'rowtype_oid',c.reltype::int4,'recursive_toast_oid',c.reltoastrelid::int4) FROM pg_class p LEFT JOIN pg_class c ON c.oid=p.reltoastrelid LEFT JOIN pg_namespace n ON n.oid=c.relnamespace WHERE p.oid="+address+';');observed[name]=a
  case('toast_presence_'+name,(a['toast_oid']!=0)==parent['required'],a)
  if not parent['required']:continue
  want=dict(name='pg_toast_'+str(a['parent_oid']),schema='pg_toast',owner=parent['owner'],kind='t',rls=False,force_rls=False,persistence='p',rowtype_oid=0,recursive_toast_oid=0)
  case('toast_identity_'+name,all(a.get(k)==v for k,v in want.items()),dict(expected=want,observed=a))
  columns=last("SELECT jsonb_agg(jsonb_build_object('name',a.attname,'type',t.typname,'number',a.attnum,'not_null',a.attnotnull,'storage',a.attstorage,'compression',a.attcompression,'collation',a.attcollation::int4,'typmod',a.atttypmod,'dropped',a.attisdropped,'acl',a.attacl) ORDER BY a.attnum) FROM pg_attribute a JOIN pg_type t ON t.oid=a.atttypid WHERE a.attrelid="+str(a['toast_oid'])+' AND a.attnum>0;')
  wanted=[dict(x,number=i+1,not_null=False,storage='p',compression='',collation=0,typmod=-1,dropped=False,acl=None) for i,x in enumerate(model['toast_columns'])]
  case('toast_columns_'+name,columns==wanted,dict(expected=wanted,observed=columns),'TYPE')
  ix=last("SELECT jsonb_agg(jsonb_build_object('name',c.relname,'owner',pg_get_userbyid(c.relowner),'method',am.amname,'unique',i.indisunique,'primary',i.indisprimary,'valid',i.indisvalid,'ready',i.indisready,'live',i.indislive,'keys',i.indkey::text,'options',i.indoption::text,'opclasses',(SELECT array_agg(op.opcname::text ORDER BY k.ord) FROM unnest(i.indclass) WITH ORDINALITY k(id,ord) JOIN pg_opclass op ON op.oid=k.id),'predicate',pg_get_expr(i.indpred,i.indrelid),'expression',pg_get_expr(i.indexprs,i.indrelid)) ORDER BY c.relname) FROM pg_index i JOIN pg_class c ON c.oid=i.indexrelid JOIN pg_am am ON am.oid=c.relam WHERE i.indrelid="+str(a['toast_oid'])+';')
  wanted=[dict(name=want['name']+'_index',owner=parent['owner'],method='btree',unique=True,primary=True,valid=True,ready=True,live=True,keys='1 2',options='0 0',opclasses=['oid_ops','int4_ops'],predicate=None,expression=None)]
  case('toast_index_'+name,ix==wanted,dict(expected=wanted,observed=ix),'PLANNER_SUPPORT')
 # Defaults are not evaluated by S04, but their complete presence/absence is
 # currentness input. Compare source expressions rather than target-derived SQL.
 import sys
 sys.path.insert(0,str(Path.home()/'.codex/tmp/package0090-pglast-8.5'))
 from pglast.parser import parse_sql_json
 r=e.Resolver(parse_sql_json);defaults=json.loads((OUT/'default-expression-v2.json').read_text())['defaults']
 for item in defaults:
  name=item['relation'];column=item['column'];a=last("SELECT jsonb_build_object('expression',pg_get_expr(d.adbin,d.adrelid),'identity',a.attidentity,'generated',a.attgenerated) FROM pg_attribute a LEFT JOIN pg_attrdef d ON d.adrelid=a.attrelid AND d.adnum=a.attnum WHERE a.attrelid="+literal(name)+'::regclass AND a.attname='+literal(column)+';')
  expected=item['expression'];ok=a['identity']=='' and a['generated']==''
  if expected is None:ok=ok and a['expression'] is None
  else:
   node=expected if isinstance(expected,dict) else parse_expression(r,expected)
   ok=ok and a['expression'] is not None and normalize(r,node)==normalize(r,parse_expression(r,a['expression']))
  case('default_'+name+'.'+column,ok,dict(expected=expected,observed=a),'DEFAULT_SEQUENCE')
 # No source root has a sequence/default nextval or identity dependency.
 roots=','.join(literal(p['parent'])+'::regclass' for p in model['parents'])
 dependencies=last("SELECT count(*) FROM pg_depend d JOIN pg_class c ON c.oid=d.objid WHERE d.classid='pg_class'::regclass AND d.refclassid='pg_class'::regclass AND d.refobjid IN ("+roots+") AND c.relkind='S';")
 case('reachable_sequence_dependencies_empty',dependencies==0,dependencies,'DEFAULT_SEQUENCE')
