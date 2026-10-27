"""Freeze name-resolution candidates, including nonselected overload signatures.

Candidate metadata is not a claim that nonselected function bodies execute.
"""
import json,sys
from pathlib import Path
import package_0090_source_closure as q
from package_0090_reachable_v2 import OUT,save

def prepare(r):
 selected=json.loads((OUT/'function-identity-v6.json').read_text())['provider_functions'];names={p['proname'] for p in selected};fields=['oid','proname','pronamespace','proowner','prolang','prokind','provariadic','pronargs','pronargdefaults','proargtypes','proallargtypes','proargmodes','proargnames','prorettype','proretset']
 rows=[{k:p[k] for k in fields} for p in r.procs if p['pronamespace']=='11' and p['proname'] in names]
 overrides=[]
 for raw in json.loads(r.parser((OUT/'provider/system_functions.sql').read_text()))['stmts']:
  f=raw['stmt'].get('CreateFunctionStmt')
  if not f:continue
  name=f['funcname'][-1]['String']['sval'];params=[p['FunctionParameter'] for p in f.get('parameters',[])];args=[r.typename(p['argType']) for p in params if p.get('mode') not in ['FUNC_PARAM_OUT','FUNC_PARAM_TABLE']]
  matches=[p for p in rows if p['proname']==name and [r.by_oid[x] for x in p['proargtypes'].split()]==args]
  if not matches:continue
  q.require(len(matches)==1,'Candidate bootstrap override ambiguity');matches[0]['pronargdefaults']=str(sum('defexpr' in p for p in params));overrides.append(dict(name=name,args=args,default_count=matches[0]['pronargdefaults']))
 type_fields=['oid','typname','typnamespace','typtype','typcategory','typispreferred','typisdefined','typelem','typarray','typbasetype','typcollation']
 types=[{k:t[k] for k in type_fields} for t in r.rows['pg_type']]
 save('function-resolution-candidates-v2.json',dict(functions=rows,function_name_scope=sorted(names),types=types,bootstrap_overrides=overrides,independent=True,absence_rule='No added/missing pg_catalog overload for any selected function name, even if nonselected today; all builtin type selection categories/preference/domain/array metadata frozen. No unselected candidate body/provider I/O expansion implied. Additional user types matter only through changed candidate/operator/cast surfaces already frozen.',future_invalidation='Any overload signature/default/variadic/namespace/type selection change or addition requires new qualification generation and proven final T10 invalidation; selected-call tests alone cannot substitute'))

def qualify(sql,run,container,folder,record,fixture,runtime_work):
 record['recipe_hashes'][Path(__file__).name]=q.sha(Path(__file__).read_bytes());model=json.loads((OUT/'function-resolution-candidates-v2.json').read_text());cases=[];observed={}
 def case(name,ok,details):
  row=dict(name=name,passed=bool(ok),details=details,group='FUNCTION_IDENTITY');cases.append(row);record['cases'].append(row)
  (folder/'function-candidates-runtime.json').write_text(json.dumps(dict(cases=cases,observed=observed),indent=2)+'\n');q.require(ok,name)
 for table,key,where in [('pg_proc','functions',"pronamespace=11 AND proname IN ("+','.join("'"+n.replace("'","''")+"'" for n in model['function_name_scope'])+')'),('pg_type','types','oid IN ('+','.join(t['oid'] for t in model['types'])+')')]:
  rows=model[key];parts=[]
  for f in rows[0]:parts.extend(["'"+f+"'",'p.'+f+'::text'])
  actual=json.loads(sql('SELECT jsonb_agg(jsonb_build_object('+','.join(parts)+') ORDER BY p.oid) FROM '+table+' p WHERE '+where+';').stdout);observed[key]=actual
  case('resolution_candidate_'+table+'_denominator',len(actual)==len(rows),dict(expected=len(rows),observed=len(actual)));byoid={p['oid']:p for p in actual}
  for expected in rows:
   want={k:(None if v=='_null_' else 'true' if k in ['proretset','typispreferred','typisdefined'] and v=='t' else 'false' if k in ['proretset','typispreferred','typisdefined'] and v=='f' else v) for k,v in expected.items()};a=byoid.get(expected['oid'],{});mismatches={k:[v,a.get(k)] for k,v in want.items() if a.get(k)!=v};case('resolution_candidate_'+table+'_'+expected['oid'],not mismatches,mismatches)
