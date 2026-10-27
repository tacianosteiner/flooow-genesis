"""Prepare and compare typed parse witnesses; canonical S04 is never invoked."""
import json,re
from pathlib import Path
import package_0090_source_closure as q
import package_0090_reachable_v2 as e
OUT=e.OUT

def sqltype(t):return 'pg_catalog.'+(t[1:]+'[]' if t.startswith('_') else t)
def literal(s):return "'"+s.replace("'","''")+"'"
def render(r,node):
 k,n=next(iter(node.items()))
 if k in ['ColumnRef','ParamRef']:return 'NULL::'+sqltype(r.infer(node)['type'])
 if k=='A_Const':
  if 'ival'in n:return str(n['ival'].get('ival',0))
  if 'fval'in n:return n['fval']['fval']
  if 'sval'in n:return literal(n['sval']['sval'])
  if 'boolval'in n:return 'TRUE' if n['boolval'].get('boolval') else 'FALSE'
  if n.get('isnull'):return 'NULL'
 if k=='A_ArrayExpr':return 'ARRAY[]'
 if k=='TypeCast':return '('+render(r,n['arg'])+')::'+sqltype(r.typename(n['typeName']))
 if k=='FuncCall':return '.'.join(x['String']['sval'] for x in n['funcname'])+'('+','.join(render(r,a) for a in n.get('args',[]))+')'
 if k=='A_Expr':
  op=n['name'][-1]['String']['sval'];left=render(r,n['lexpr']);right=render(r,n['rexpr']);return '('+left+' '+op+' '+('ANY('+right+')' if n['kind']=='AEXPR_OP_ANY' else right)+')'
 if k=='BoolExpr':
  values=[render(r,x) for x in n['args']];return '(NOT '+values[0]+')' if n['boolop']=='NOT_EXPR' else '('+(' OR ' if n['boolop']=='OR_EXPR' else ' AND ').join(values)+')'
 if k=='NullTest':return '('+render(r,n['arg'])+(' IS NULL)' if n['nulltesttype']=='IS_NULL' else ' IS NOT NULL)')
 if k=='A_Indirection':return '('+render(r,n['arg'])+')'+''.join('['+render(r,x['A_Indices']['uidx'])+']' for x in n['indirection'])
 if k=='MinMaxExpr':return 'LEAST('+','.join(render(r,a) for a in n['args'])+')'
 if k=='SQLValueFunction':return 'SESSION_USER'
 if k=='SubLink':return 'EXISTS(SELECT 1 FROM pg_catalog.pg_auth_members m WHERE NULL::pg_catalog.oid=NULL::pg_catalog.oid OR NULL::pg_catalog.oid=NULL::pg_catalog.oid)'
 if k=='SortBy':return render(r,n['node'])
 raise RuntimeError('Unrendered expression '+k)

def prepare(r,sites):
 rows=[];original=json.loads(e.ADD.read_text())['operator_and_implicit_expression_sites']
 for expected,source in zip(sites,original):
  r.env(source['statement_ordinal']);expression=render(r,{source['kind']:source['ast']});rows.append(dict(site_id=expected['SITE_ID'],sql=expression,expected=expected['analysis'],kind=source['kind']))
 e.save('typed-parse-witnesses.json',dict(source_sha=q.SOURCE_HASH,expected_before_target=True,probes=rows))

def qualify(sql,run,container,folder,record,fixture,runtime_work):
 record['recipe_hashes'][Path(__file__).name]=q.sha(Path(__file__).read_bytes())
 record['expected_typed_witness_sha256']=q.sha((OUT/'typed-parse-witnesses.json').read_bytes())
 probes=json.loads((OUT/'typed-parse-witnesses.json').read_text())['probes'];cases=[]
 def case(name,passed,detail,group):
  c=dict(name=name,passed=bool(passed),details=detail,group=group);cases.append(c);record['cases'].append(c);q.require(passed,name)
 commands=['SET search_path=pg_catalog,pg_temp;']
 for i,p in enumerate(probes):commands.append('CREATE TEMP VIEW probe_%03d AS SELECT '%i+p['sql']+' AS value'+(' ORDER BY value' if p['kind']=='SortBy' else '')+';')
 query="SELECT pg_catalog.jsonb_agg(pg_catalog.jsonb_build_object('name',c.relname,'type',t.typname,'collation',a.attcollation,'tree',r.ev_action::pg_catalog.text) ORDER BY c.relname) FROM pg_catalog.pg_class c JOIN pg_catalog.pg_attribute a ON a.attrelid=c.oid AND a.attnum=1 JOIN pg_catalog.pg_type t ON t.oid=a.atttypid JOIN pg_catalog.pg_rewrite r ON r.ev_class=c.oid AND r.rulename='_RETURN' WHERE c.relnamespace=pg_catalog.pg_my_temp_schema() AND c.relname LIKE 'probe_%';"
 result=sql('\n'.join(commands)+query);actual=json.loads(result.stdout.decode().splitlines()[-1]);q.require(len(actual)==190,'Parse witness denominator')
 for p,a in zip(probes,actual):
  expected=p['expected'];case('typed_'+p['site_id'],a['type']==expected['type'] and str(a['collation'])==expected['collation_oid'],dict(expected=expected['type'],actual=a['type'],expected_collation=expected['collation_oid'],actual_collation=a['collation'],helper_view_only=True),'EXPRESSION_TYPING')
  root=a['tree'].split(':targetList ({TARGETENTRY :expr ',1)[1]
  if p['kind']=='A_Expr':
   match=re.match(r'\{(?:OPEXPR|SCALARARRAYOPEXPR) :opno (\d+) :opfuncid (\d+)',root);op=expected['details']['operator'];case('operator_'+p['site_id'],bool(match) and list(match.groups())==[op['oid'],op['oprcode']],dict(expected_operator=op['oid'],expected_function=op['oprcode'],root=root[:180]),'OPERATOR')
  if p['kind']=='TypeCast':
   cast=expected['casts'][0];method=cast['method'];passed=a['type']==expected['type']
   if method=='FUNCTION_CAST':passed=passed and root.startswith('{FUNCEXPR :funcid '+cast['provider_oid']+' ')
   elif method=='RELABELTYPE':passed=passed and root.startswith('{RELABELTYPE ')
   elif method=='OTHER_EXACT_POSTGRES_NODE':passed=passed and root.startswith('{ARRAYEXPR ')
   elif method=='UNKNOWN_COERCION':passed=passed and root.startswith('{CONST :consttype ')
   case('cast_'+p['site_id'],passed,dict(method=method,root=root[:180]),'CAST')
 epath=folder/'typed-expression-runtime.json';epath.write_text(json.dumps(dict(cases=cases,actual_parse_witnesses=actual,canonical_S04_executed=False),indent=2)+'\n')


def complete_qualification(sql,run,container,folder,record,fixture,runtime_work):
 from package_0090_reachable_v2_release import verify_lock,MANIFEST
 locked=(OUT/MANIFEST).exists()
 if locked:record['expected_manifest_sha256_before']=verify_lock()
 qualify(sql,run,container,folder,record,fixture,runtime_work)
 import package_0090_reachable_v2_consumers as consumers
 consumers.qualify(sql,run,container,folder,record,fixture,runtime_work)
 import package_0090_reachable_v2_candidates as candidates
 candidates.qualify(sql,run,container,folder,record,fixture,runtime_work)
 import package_0090_reachable_v2_metadata_runtime as metadata
 metadata.qualify(sql,run,container,folder,record,fixture,runtime_work)
 import package_0090_reachable_v2_structure as structure
 structure.qualify(sql,run,container,folder,record,fixture,runtime_work)
 import package_0090_reachable_v2_integrity_runtime as integrity
 integrity.qualify(sql,run,container,folder,record,fixture,runtime_work)
 import package_0090_reachable_v2_storage_runtime as storage
 storage.qualify(sql,run,container,folder,record,fixture,runtime_work)
 import package_0090_reachable_v2_catalog as catalog
 catalog.qualify(sql,run,container,folder,record,fixture,runtime_work)
 import package_0090_reachable_v2_privileges_runtime as privileges
 privileges.qualify(sql,run,container,folder,record,fixture,runtime_work)
 import package_0090_reachable_v2_native_runtime as native
 native.qualify(sql,run,container,folder,record,fixture,runtime_work)
 import package_0090_reachable_v2_contracts as contracts
 contracts.qualify(sql,run,container,folder,record,fixture,runtime_work)
 import package_0090_reachable_v2_attacks as attacks
 attacks.qualify(sql,run,container,folder,record,fixture,runtime_work)
 if locked:
  record['expected_manifest_sha256_after']=verify_lock()
  q.require(record['expected_manifest_sha256_before']==record['expected_manifest_sha256_after'],'Expected input drift during runtime match')
