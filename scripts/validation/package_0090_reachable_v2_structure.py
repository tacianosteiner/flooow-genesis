"""View expansion and generated composite/array identity bindings."""
import json,sys
from pathlib import Path
import package_0090_source_closure as q
from package_0090_reachable_v2 import OUT,save

def view_ast(parser,text):
 tree=json.loads(parser(text))['stmts'][0]['stmt']
 def visit(x):
  if isinstance(x,list):return [visit(v) for v in x]
  if not isinstance(x,dict):return x
  if 'ColumnRef'in x:
   fields=x['ColumnRef']['fields'];names=[f['String']['sval'] for f in fields];col=names[-1];alias='s' if col in ['setrole','setdatabase','setconfig'] else 'pg_authid'
   return {'ColumnRef':dict(fields=[{'String':{'sval':alias}},{'String':{'sval':col}}])}
  result={k:visit(v) for k,v in x.items() if k not in ['location','stmt_location','stmt_len']}
  if 'A_Expr' in result:
   n=result['A_Expr'];left=n.get('lexpr',{});right=n.get('rexpr',{})
   # Source setdatabase=0 selects oid equality through implicit int4->oid;
   # deparser emits the same typed constant explicitly. Normalize only that
   # independently identified source edge, never arbitrary casts away.
   if left.get('ColumnRef',{}).get('fields',[])[-1:]==[{'String':{'sval':'setdatabase'}}] and right.get('A_Const',{}).get('ival')=={}:
    n['rexpr']={'TypeCast':dict(arg=right,typeName=dict(names=[{'String':{'sval':'oid'}}],typemod=-1))}
  if 'RangeVar'in result:result['RangeVar']['schemaname']='pg_catalog'
  if 'TypeName'in result:result['TypeName']['names']=[result['TypeName']['names'][-1]]
  return result
 return visit(tree)

def prepare(r):
 rels=json.loads((OUT/'relation-view-v2.json').read_text());source='SELECT '+rels['source_view_SQL'].strip().removeprefix('SELECT').strip()
 save('view-composite-bindings-v2.json',dict(pg_roles_source_SQL=source,expected_view_AST=view_ast(r.parser,source),composite_roots=rels['relations'],composite_factory='REL_18_4 heap.c AddNewRelationType/TypeCreate: dynamic rowtype and companion array bind through relation OID; generated names are not predicted OIDs',expected_composite=dict(type_kind='c',defined=True,not_null=False,base_oid=0,typmod=-1,collation_oid=0),array_rule='Companion array typelem equals relation rowtype and rowtype typarray equals companion; same owner/namespace. Ordered fields independently checked in column-v2.',independent=True))
 model=json.loads((OUT/'view-composite-bindings-v2.json').read_text());common=dict(typlen=-1,typbyval=False,typispreferred=False,typisdefined=True,typdelim=',',typmodin=0,typmodout=0,typalign='d',typstorage='x',typnotnull=False,typbasetype=0,typtypmod=-1,typndims=0,typcollation=0,typdefault=None,typdefaultbin=None,typacl=None)
 for kind,prefix,category in [('composite','record','C'),('array','array','A')]:
  profile=dict(common,typtype='c' if kind=='composite' else 'b',typcategory=category)
  for attr,suffix in [('typinput','in'),('typoutput','out'),('typreceive','recv'),('typsend','send')]:
   choices=[p for p in r.procs if p['proname']==prefix+'_'+suffix];q.require(len(choices)==1,'Generated type provider ambiguity');profile[attr]=int(choices[0]['oid'])
  profile['typanalyze']=int(next(p['oid'] for p in r.procs if p['proname']=='array_typanalyze')) if kind=='array' else 0
  profile['typsubscript']=int(next(p['oid'] for p in r.procs if p['proname']=='array_subscript_handler')) if kind=='array' else 0
  model[kind+'_profile']=profile
 save('view-composite-bindings-v2.json',model)

def qualify(sql,run,container,folder,record,fixture,runtime_work):
 record['recipe_hashes'][Path(__file__).name]=q.sha(Path(__file__).read_bytes());sys.path.insert(0,str(Path.home()/'.codex/tmp/package0090-pglast-8.5'));from pglast.parser import parse_sql_json
 model=json.loads((OUT/'view-composite-bindings-v2.json').read_text());cases=[];observed={}
 def case(name,ok,details):
  row=dict(name=name,passed=bool(ok),details=details,group='RELATION_VIEW');cases.append(row);record['cases'].append(row)
  (folder/'view-composite-runtime.json').write_text(json.dumps(dict(cases=cases,observed=observed),indent=2)+'\n');q.require(ok,name)
 definition=sql("SELECT pg_get_viewdef('pg_catalog.pg_roles'::regclass,true);").stdout.decode().strip();observed['view_SQL']=definition;actual=view_ast(parse_sql_json,definition)
 case('pg_roles_complete_view_AST',actual==model['expected_view_AST'],dict(expected=model['expected_view_AST'],observed=actual))
 for rel in model['composite_roots']:
  name=rel['name'];a=json.loads(sql("SELECT jsonb_build_object('name',t.typname,'owner',pg_get_userbyid(t.typowner),'schema',n.nspname,'type_kind',t.typtype,'defined',t.typisdefined,'not_null',t.typnotnull,'base_oid',t.typbasetype::int4,'typmod',t.typtypmod,'collation_oid',t.typcollation::int4,'relation_matches',t.typrelid=c.oid,'array_exists',arr.oid IS NOT NULL,'array_kind',arr.typtype,'array_element_matches',arr.typelem=t.oid,'array_owner_matches',arr.typowner=t.typowner,'array_schema_matches',arr.typnamespace=t.typnamespace) FROM pg_class c JOIN pg_type t ON t.oid=c.reltype JOIN pg_namespace n ON n.oid=t.typnamespace LEFT JOIN pg_type arr ON arr.oid=t.typarray WHERE c.oid='"+name+"'::regclass;").stdout)
  want=dict(model['expected_composite'],name=name.split('.')[-1],owner=rel['owner'],schema=name.split('.')[0],relation_matches=True,array_exists=True,array_kind='b',array_element_matches=True,array_owner_matches=True,array_schema_matches=True);observed[name]=a
  case('composite_binding_'+name,a==want,dict(expected=want,observed=a))
  for kind in ['composite','array']:
   expected=model[kind+'_profile'];parts=[]
   numeric={'typinput','typoutput','typreceive','typsend','typmodin','typmodout','typanalyze','typsubscript','typbasetype','typcollation'}
   for field in expected:parts.extend(["'"+field+"'",'t.'+field+('::oid::int4' if field in numeric else '::text' if field=='typdefaultbin' else '')])
   address="(SELECT reltype FROM pg_class WHERE oid='"+name+"'::regclass)" if kind=='composite' else "(SELECT typarray FROM pg_type WHERE oid=(SELECT reltype FROM pg_class WHERE oid='"+name+"'::regclass))"
   actual=json.loads(sql('SELECT jsonb_build_object('+','.join(parts)+') FROM pg_type t WHERE t.oid='+address+';').stdout)
   case('generated_type_profile_'+kind+'_'+name,actual==expected,dict(expected=expected,observed=actual))
