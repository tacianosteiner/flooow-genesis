"""Isolated function and coercion consumer parse witnesses, never canonical S04."""
import json,re
from pathlib import Path
import package_0090_source_closure as q
import package_0090_reachable_v2 as e
from package_0090_reachable_v2_runtime import render,sqltype,literal
OUT=e.OUT

def prepare(r):
 calls=json.loads((OUT/'function-reachability-v2.json').read_text())['call_contexts'];rows=[]
 for i,c in enumerate(calls):
  source=c['source'];r.env(source['statement_ordinal']);node={'FuncCall':dict(funcname=[{'String':{'sval':x}} for x in source['callee'].split('.')],args=source['argument_asts'])};a=r.infer(node)
  rows.append(dict(id='call_%03d'%i,sql=render(r,node),expected=a,group='POLYMORPHIC' if a['mechanism']=='POLYMORPHIC_INSTANTIATION' else 'EXPRESSION_TYPING'))
 coercions=json.loads((OUT/'cast-resolution-v3.json').read_text())['consumer_edges']
 for i,c in enumerate(coercions):
  r.env(c['statement_ordinal']);tree=r.statements[c['statement_ordinal']]['ast']['stmts'][0]['stmt'];tree=next(iter(tree.values()))
  if c['AST_path'][:1]==['assignment']:node=tree['targetList'][0]['ResTarget']['val']
  else:
   node=tree
   for key in c['AST_path']:
    while isinstance(node,dict) and key not in node and len(node)==1:node=next(iter(node.values()))
    node=node[key]
  rows.append(dict(id='coerce_%03d'%i,sql=render(r,node),coercion=c,target_oid=r.types[c['target']]['oid'],group='CAST'))
 e.save('consumer-parse-witnesses.json',dict(probes=rows,call_instances=len(calls),coercion_edges=len(coercions),scope='Original call resolution plus isolated exact-signature coercion consumers. These assignment source/target pairs also have implicit casts; exact function argument witnesses corroborate those provider paths. Source analyze.c supplies PL assignment context; no execution of canonical S04 and no SEMANTIC_BOUND claim.'))

def qualify(sql,run,container,folder,record,fixture,runtime_work):
 record['recipe_hashes'][Path(__file__).name]=q.sha(Path(__file__).read_bytes());probes=json.loads((OUT/'consumer-parse-witnesses.json').read_text())['probes'];commands=['SET search_path=pg_catalog,pg_temp;'];cases=[]
 for p in probes:
  name=p['id'];c=p.get('coercion')
  if c:
   typ=sqltype(c['target']);helper='pg_temp.consume_'+name
   # Function arguments request implicit coercion; explicit and assignment
   # contexts are checked separately with the source-prescribed cast form.
   commands.append('CREATE FUNCTION '+helper+'(x '+typ+') RETURNS '+typ+' LANGUAGE SQL AS '+literal('SELECT x')+';')
   value=p['sql'];value='('+value+')::'+typ if c['context']=='EXPLICIT' else value
   commands.append('CREATE TEMP VIEW '+name+' AS SELECT '+helper+'('+value+') AS value;')
  else:commands.append('CREATE TEMP VIEW '+name+' AS SELECT '+p['sql']+' AS value;')
 query="SELECT jsonb_agg(jsonb_build_object('name',c.relname,'type',t.typname,'type_oid',t.oid::text,'tree',r.ev_action::text) ORDER BY c.relname) FROM pg_class c JOIN pg_attribute a ON a.attrelid=c.oid AND a.attnum=1 JOIN pg_type t ON t.oid=a.atttypid JOIN pg_rewrite r ON r.ev_class=c.oid AND r.rulename='_RETURN' WHERE c.relnamespace=pg_my_temp_schema() AND (c.relname LIKE 'call_%' OR c.relname LIKE 'coerce_%');"
 actual=json.loads(sql('\n'.join(commands)+query).stdout.decode().splitlines()[-1]);keyed={x['name']:x for x in actual};q.require(len(actual)==len(probes),'Consumer witness denominator')
 for p in probes:
  a=keyed[p['id']];root=a['tree'].split(':targetList ({TARGETENTRY :expr ',1)[1];c=p.get('coercion')
  if c:
   ok=a['type_oid']==p['target_oid'];method=c['method']
   if method=='FUNCTION_CAST':ok=ok and ('{FUNCEXPR :funcid '+c['provider_oid']+' ') in root
   elif method=='RELABELTYPE':ok=ok and '{RELABELTYPE ' in root
   elif method=='OTHER_EXACT_POSTGRES_NODE':ok=ok and '{ARRAYEXPR ' in root
   elif method=='UNKNOWN_COERCION':ok=ok and ('{CONST :consttype '+p['target_oid']+' ') in root
   details=dict(method=method,target=p['target_oid'],observed_type=a['type_oid'],isolated_consumer=True)
  else:
   want=p['expected'];ok=a['type']==want['type'] and root.startswith('{FUNCEXPR :funcid '+want['provider_oid']+' ');details=dict(expected_function=want['provider_oid'],expected_type=want['type'],actual_type=a['type'])
  row=dict(name='consumer_'+p['id'],passed=bool(ok),details=details,group=p['group']);cases.append(row);record['cases'].append(row)
  (folder/'consumer-runtime.json').write_text(json.dumps(dict(cases=cases,observed=actual),indent=2)+'\n');q.require(ok,row['name'])
