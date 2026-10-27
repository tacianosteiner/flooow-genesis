"""Verify independent provider/metadata components against an owned target."""
import json
from pathlib import Path
import package_0090_source_closure as q
from package_0090_reachable_v2 import OUT

def get(name):return json.loads((OUT/name).read_text())
def qualify(sql,run,container,folder,record,fixture,runtime_work):
 record['recipe_hashes'][Path(__file__).name]=q.sha(Path(__file__).read_bytes());results=[];observed={}
 def last(result):return json.loads(result.stdout.decode().splitlines()[-1])
 def case(name,passed,details,group):
  row=dict(name=name,passed=bool(passed),details=details,group=group);results.append(row);record['cases'].append(row)
  (folder/'reachable-metadata-runtime.json').write_text(json.dumps(dict(cases=results,observed=observed),indent=2)+'\n')
  q.require(passed,name)
 manifest=get('function-identity-v6.json');procs=manifest['provider_functions'];record['expected_function_component_sha256']=q.sha((OUT/'function-identity-v6.json').read_bytes())
 fields=[x for x in procs[0] if x not in ['proargdefaults','expected_defaults_SQL']]
 parts=[]
 for field in fields:
  value='p.'+field+('::oid' if field=='prosupport' else '')+'::text';parts.extend(["'"+field+"'",value])
 parts.extend(["'defaults_SQL'","pg_catalog.pg_get_expr(p.proargdefaults,0)"])
 actual=last(sql('SELECT jsonb_agg(jsonb_build_object('+','.join(parts)+') ORDER BY p.oid) FROM pg_catalog.pg_proc p WHERE p.oid IN ('+','.join(p['oid'] for p in procs)+');'))
 q.require(len(actual)==len(procs),'Function identity denominator');observed['provider_functions']=actual
 bools=['prosecdef','proleakproof','proisstrict','proretset']
 for expected,a in zip(procs,actual):
  normalized={k:(None if v=='_null_' else 'true' if v=='t' and k in bools else 'false' if v=='f' and k in bools else v) for k,v in expected.items() if k in fields};mismatch={k:[v,a.get(k)] for k,v in normalized.items() if a.get(k)!=v}
  if a['defaults_SQL']!=expected.get('expected_defaults_SQL'):mismatch['defaults_SQL']=[expected.get('expected_defaults_SQL'),a['defaults_SQL']]
  case('provider_function_'+expected['oid'],not mismatch,dict(identity=expected['proname'],mismatches=mismatch),'FUNCTION_IDENTITY')
 # Dynamic function OIDs bind by exact signatures; all identity fields then
 # match declarations, including source body, defaults, native library and ACL.
 for expected in manifest['source_profiles']:
  signature=expected['signature'];quoted="'"+signature+"'::regprocedure"
  query="SELECT jsonb_build_object('signature',"+"'"+signature+"'"+",'owner',pg_get_userbyid(p.proowner),'language',l.lanname,'args',COALESCE((SELECT array_agg(t.typname::text ORDER BY x.ord) FROM unnest(p.proargtypes) WITH ORDINALITY x(oid,ord) JOIN pg_type t ON t.oid=x.oid),ARRAY[]::text[]),'allargs',(SELECT array_agg(t.typname::text ORDER BY x.ord) FROM unnest(p.proallargtypes) WITH ORDINALITY x(oid,ord) JOIN pg_type t ON t.oid=x.oid),'argmodes',p.proargmodes,'argnames',p.proargnames,'result',rt.typname,'returns_set',p.proretset,'security_definer',p.prosecdef,'strict',p.proisstrict,'volatile',p.provolatile,'parallel',p.proparallel,'leakproof',p.proleakproof,'config',p.proconfig,'source',p.prosrc,'library',p.probin,'support_oid',p.prosupport::oid::int4,'cost',p.procost,'rows',p.prorows,'kind',p.prokind,'defaults_SQL',pg_get_expr(p.proargdefaults,0),'raw_acl',(SELECT jsonb_agg(jsonb_build_object('grantee',CASE WHEN x.grantee=0 THEN 'PUBLIC' ELSE pg_get_userbyid(x.grantee) END,'privilege',upper(x.privilege_type),'grantable',x.is_grantable,'grantor',pg_get_userbyid(x.grantor)) ORDER BY CASE WHEN x.grantee=0 THEN 'PUBLIC' ELSE pg_get_userbyid(x.grantee) END) FROM aclexplode(p.proacl) x)) FROM pg_proc p JOIN pg_language l ON l.oid=p.prolang JOIN pg_type rt ON rt.oid=p.prorettype WHERE p.oid="+quoted+';'
  a=last(sql(query));mismatch={k:[v,a.get(k)] for k,v in expected.items() if a.get(k)!=v};case('source_native_function_'+signature,not mismatch,mismatch,'FUNCTION_IDENTITY')
 # Exact ordered columns, including typmod, collation and nullability. No source
 # values are replaced by observations when a mismatch appears.
 expected=get('column-v2.json')['columns'];relations=sorted({x['relation'] for x in expected});names=','.join("'"+x+"'::regclass" for x in relations)
 actual=last(sql("SELECT jsonb_agg(jsonb_build_object('relation',n.nspname||'.'||c.relname,'attnum',a.attnum,'name',a.attname,'type',t.typname,'typmod',a.atttypmod,'not_null',a.attnotnull,'collation',a.attcollation::int4,'generated',a.attgenerated,'identity',a.attidentity,'dropped',a.attisdropped,'inheritance_count',a.attinhcount,'is_local',a.attislocal,'has_default',a.atthasdef,'column_acl',(SELECT jsonb_agg(jsonb_build_object('grantee',CASE WHEN x.grantee=0 THEN 'PUBLIC' ELSE pg_get_userbyid(x.grantee) END,'privilege',upper(x.privilege_type),'grantable',x.is_grantable,'grantor',pg_get_userbyid(x.grantor)) ORDER BY pg_get_userbyid(x.grantee),x.privilege_type) FROM aclexplode(a.attacl) x)) ORDER BY n.nspname,c.relname,a.attnum) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace JOIN pg_attribute a ON a.attrelid=c.oid JOIN pg_type t ON t.oid=a.atttypid WHERE c.oid IN ("+names+") AND a.attnum>0;"));observed['columns']=actual
 keyed={(x['relation'],x['name']):x for x in actual};case('column_denominator',len(actual)==len(expected),dict(expected=len(expected),observed=len(actual)),'RELATION_VIEW')
 for x in expected:
  a=keyed.get((x['relation'],x['name']),{});want={k:v for k,v in x.items() if k!='default'};want['has_default']=x['default'] is not None;mismatch={k:[v,a.get(k)] for k,v in want.items() if a.get(k)!=v};case('column_'+x['relation']+'.'+x['name'],not mismatch,mismatch,'RELATION_VIEW')
 r_expected=get('relation-view-v2.json')['relations'];actual=last(sql("SELECT jsonb_agg(jsonb_build_object('name',n.nspname||'.'||c.relname,'kind',c.relkind,'owner',pg_get_userbyid(c.relowner),'RLS',c.relrowsecurity,'force_RLS',c.relforcerowsecurity,'persistence',c.relpersistence,'options',c.reloptions) ORDER BY n.nspname,c.relname) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE c.oid IN ("+names+");"));observed['relations']=actual;keyed={x['name']:x for x in actual}
 for x in r_expected:
  a=keyed[x['name']];want={k:x[k] for k in ['name','kind','owner','RLS','force_RLS','persistence']};mismatch={k:[v,a.get(k)] for k,v in want.items() if a.get(k)!=v};case('relation_'+x['name'],not mismatch,mismatch,'RELATION_VIEW')
 # All independently enumerated builtin type attributes. OID links remain OIDs;
 # only compile-time BKI tokens are substituted from frozen image headers.
 expected=get('type-reachability-v2.json')['types'];fields=list(expected[0]);parts=[]
 regproc_fields=['typsubscript','typinput','typoutput','typreceive','typsend','typmodin','typmodout','typanalyze']
 for f in fields:parts.extend(["'"+f+"'",'t.'+f+('::oid' if f in regproc_fields else '')+'::text'])
 actual=last(sql('SELECT jsonb_agg(jsonb_build_object('+','.join(parts)+') ORDER BY t.oid) FROM pg_type t WHERE t.oid IN ('+','.join(x['oid'] for x in expected)+');'));observed['types']=actual;keyed={t['oid']:t for t in actual}
 bools=['typbyval','typispreferred','typisdefined','typnotnull']
 for x in expected:
  want={k:(None if v=='_null_' else '64' if v=='NAMEDATALEN' else '8' if v=='SIZEOF_POINTER' else 'd' if v=='ALIGNOF_POINTER' else 'true' if v=='FLOAT8PASSBYVAL' or v=='t' and k in bools else 'false' if v=='f' and k in bools else '0' if v=='-' and k in regproc_fields else v) for k,v in x.items()};a=keyed[x['oid']];mismatch={k:[v,a.get(k)] for k,v in want.items() if a.get(k)!=v};case('type_'+x['typname'],not mismatch,mismatch,'TYPE')
 (folder/'reachable-metadata-runtime.json').write_text(json.dumps(dict(cases=results,observed=observed),indent=2)+'\n')
