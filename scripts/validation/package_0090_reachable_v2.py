"""Independent REL18.4 provider/type resolver for the frozen S04 expression ledger.

No runtime target observations enter expected type/provider selection.
Unsupported nodes or ambiguous provider choices fail closed.
"""
import json,re,shlex
from pathlib import Path
import package_0090_source_closure as q

OUT=q.ROOT/'docs/evidence/package-0090-full-reachable-expectation-closure-v2'
ADD=q.ROOT/'docs/evidence/package-0090-test-activation-native-health-first-positive/s04-source-addendum.json'

def save(name,data): (OUT/name).write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
def walk(v):
 if isinstance(v,dict):
  for k,x in v.items():
   yield k,x
   yield from walk(x)
 elif isinstance(v,list):
  for x in v: yield from walk(x)
def bki():
 rows={};defs={};name=None;reading=False
 for line in (OUT/'provider/postgres.bki').read_text().splitlines():
  if line.startswith('create '):
   name=line.split()[1];rows.setdefault(name,[]);defs[name]=[];reading=True
  elif reading and re.match(r'\s*\w+\s*= ',line):
   parts=line.strip().split();defs[name].append(dict(name=parts[0],type=parts[2]))
  elif line.strip()==')':reading=False
  elif line.startswith('open '):name=line.split()[1]
  elif line.startswith('insert ( '):
   values=shlex.split(line[len('insert ( '):-2]);q.require(len(values)==len(defs[name]),'BKI token mismatch '+name)
   rows[name].append(dict(zip([x['name'] for x in defs[name]],values)))
 return rows,defs

class Resolver:
 def __init__(self,parser):
  self.parser=parser;self.rows,self.defs=bki();self.types={t['typname']:t for t in self.rows['pg_type']};self.by_oid={t['oid']:t['typname'] for t in self.rows['pg_type']};self.procs=self.rows['pg_proc'];self.proc_by_oid={p['oid']:p for p in self.procs};self.ops=self.rows['pg_operator'];self.casts={(self.by_oid[c['castsource']],self.by_oid[c['casttarget']]):c for c in self.rows['pg_cast']};self.log=[];self.context={};self.calls=[];self.providers_seen=set()
  self.source=q.git('show','HEAD:'+q.V043.relative_to(q.ROOT).as_posix()).decode();q.require(q.sha(self.source.encode())==q.SOURCE_HASH,'Canonical drift')
  self.tree=json.loads(parser(self.source))['stmts'];self.relations={}
  for stmt in self.tree:
   c=stmt['stmt'].get('CreateStmt')
   if c:
    rv=c['relation'];name=rv.get('schemaname','public')+'.'+rv['relname'];self.relations[name]={x['ColumnDef']['colname']:self.typename(x['ColumnDef']['typeName']) for x in c.get('tableElts',[]) if 'ColumnDef' in x}
  for name,fields in self.defs.items(): self.relations['pg_catalog.'+name]={f['name']:f['type'] for f in fields}
  self.relations['pg_catalog.pg_roles']={**self.relations['pg_catalog.pg_authid'],'rolconfig':'_text'}
  self.relations['public.flyway_schema_history']={x['name']:x['type'] for x in json.loads((OUT.parent/'package-0090-full-reachable-expectation-closure/return-tuple-expectation.json').read_text())['independent_Flyway_projection']}
  f=(OUT/'S04-CORRECTED-FUNCTION.sql').read_text();decl=f.split('DECLARE',1)[1].split('BEGIN',1)[0]
  self.locals={n:self.norm(t+arr) for n,t,arr in re.findall(r'^\s*(\w+)\s+pg_catalog\.(\w+)(\[\])?',decl,re.M)}
  self.locals['found']='bool';self.params={1:'uuid',2:'bytea',3:'uuid',4:'text'}
  for rec,rel in [('header_record','public.offline_binding_header'),('policy_record','public.offline_deadline_policy'),('ready_record','public.offline_readiness'),('caller_record','pg_catalog.pg_roles')]:
   for col,typ in self.relations[rel].items():self.locals[rec+'.'+col]=typ
  self.statements={x['ordinal']:x for x in json.loads(ADD.read_text())['statements']}
 def norm(self,t):return '_'+t[:-2] if t.endswith('[]') else t
 def typename(self,t):return self.norm(t['names'][-1]['String']['sval']+('[]' if t.get('arrayBounds') else ''))
 def args(self,p):return [self.by_oid[x] for x in p['proargtypes'].split()]
 def convertible(self,a,b):return a==b or a=='unknown' or (a,b) in self.casts and self.casts[a,b]['castcontext']=='i'
 def select(self,candidates,args,operator=False):
  original=list(candidates);exact=[(p,w) for p,w in candidates if w==args]
  if len(exact)==1:return exact[0],'EXACT',original
  if operator and len(args)==2 and args.count('unknown')==1:
   known=next(x for x in args if x!='unknown');exact=[(p,w) for p,w in candidates if w==[known,known]]
   if len(exact)==1:return exact[0],'UNKNOWN_AS_OTHER_EXACT',original
  candidates=[(p,w) for p,w in candidates if all(self.convertible(a,b) for a,b in zip(args,w))]
  q.require(bool(candidates),'No provider '+str(args))
  if len(candidates)==1:return candidates[0],'ONLY_IMPLICIT_COMPATIBLE',original
  count=lambda w:sum(a==b for a,b in zip(args,w));m=max(count(w) for _,w in candidates);candidates=[(p,w) for p,w in candidates if count(w)==m]
  if len(candidates)==1:return candidates[0],'MOST_EXACT',original
  count=lambda w:sum(a!=b and a!='unknown' and self.types[a]['typcategory']==self.types[b]['typcategory'] and self.types[b]['typispreferred']=='t' for a,b in zip(args,w))
  m=max(count(w) for _,w in candidates);candidates=[(p,w) for p,w in candidates if count(w)==m]
  if len(candidates)==1:return candidates[0],'PREFERRED_CATEGORY',original
  for i,a in enumerate(args):
   if a!='unknown':continue
   cats={self.types[w[i]]['typcategory'] for _,w in candidates};cat='S' if 'S' in cats else next(iter(cats)) if len(cats)==1 else None
   q.require(cat is not None,'Unknown category ambiguity')
   candidates=[(p,w) for p,w in candidates if self.types[w[i]]['typcategory']==cat]
   if any(self.types[w[i]]['typispreferred']=='t' for _,w in candidates):candidates=[(p,w) for p,w in candidates if self.types[w[i]]['typispreferred']=='t']
  q.require(len(candidates)==1,'Ambiguous provider '+str(args)+' '+str([(p.get('proname',p.get('oprname')),w) for p,w in candidates]))
  return candidates[0],'UNKNOWN_CATEGORY_PREFERRED',original
 def coercion(self,source,target,context='IMPLICIT'):
  if source==target:return dict(source=source,target=target,context=context,method='EXACT_IDENTITY')
  if source=='unknown':method='UNKNOWN_COERCION';provider=self.types[target]['typinput']
  elif source=='empty_array' and target.startswith('_'):method='OTHER_EXACT_POSTGRES_NODE';provider=None
  else:
   c=self.casts.get((source,target));q.require(c is not None,'Cast not derived '+str((source,target)))
   q.require(context=='EXPLICIT' or context=='ASSIGNMENT' and c['castcontext'] in ['i','a'] or c['castcontext']=='i','Illegal cast context')
   method={'b':'RELABELTYPE','f':'FUNCTION_CAST','i':'IO_CAST'}[c['castmethod']];provider=c['castfunc']
  return dict(source=source,target=target,context=context,method=method,provider_oid=provider)
 def env(self,ordinal):
  self.context={}
  for kind,n in walk(self.statements[ordinal]['ast']):
   if kind=='RangeVar':
    name=n.get('schemaname','pg_catalog')+'.'+n['relname'];alias=n.get('alias',{}).get('aliasname',n['relname'])
    if name in self.relations:
     for col,t in self.relations[name].items(): self.context[alias+'.'+col]=t
 def infer(self,node):
  q.require(len(node)==1,'Expression wrapper differs')
  kind,n=next(iter(node.items()));inputs=[];provider=None;casts=[];mechanism=kind;detail={}
  if kind=='ColumnRef':
   name='.'.join(x['String']['sval'] for x in n['fields']);q.require(name in self.locals or name in self.context,'Unresolved column '+name);result=self.locals.get(name,self.context.get(name))
  elif kind=='ParamRef':result=self.params[n['number']]
  elif kind=='A_Const':
   if 'ival' in n:result='int4'
   elif 'sval' in n or n.get('isnull'):result='unknown'
   elif 'boolval' in n:result='bool'
   elif 'fval' in n:
    text=n['fval']['fval'];result='int8' if re.fullmatch(r'\d+',text) and int(text)<=9223372036854775807 else 'numeric'
   else:raise RuntimeError('Unknown constant '+str(n))
  elif kind=='A_ArrayExpr':
   elements=[self.infer(x)['type'] for x in n.get('elements',[])];known=set(elements)-{'unknown'}
   q.require(len(known)<=1,'Unclosed heterogeneous array common type')
   result='_'+(next(iter(known)) if known else 'text') if elements else 'empty_array'
  elif kind=='TypeCast':
   inputs=[self.infer(n['arg'])['type']];result=self.typename(n['typeName']);casts=[self.coercion(inputs[0],result,'EXPLICIT')];mechanism='ArrayExpr' if inputs[0]=='empty_array' else casts[0]['method']
  elif kind=='FuncCall':
   name=n['funcname'][-1]['String']['sval'];inputs=[self.infer(a)['type'] for a in n.get('args',[])]
   if name=='array_append':
    q.require(inputs[0].startswith('_') and inputs[0][1:]==inputs[1],'Polymorphic instantiation conflict')
    choices=[p for p in self.procs if p['proname']==name and self.args(p)==['anycompatiblearray','anycompatible']];q.require(len(choices)==1,'Polymorphic provider not unique');provider=choices[0];result=inputs[0];mechanism='POLYMORPHIC_INSTANTIATION';detail=dict(declared=['anycompatiblearray','anycompatible'],element=inputs[1],container=result)
   else:
    candidates=[(p,self.args(p)) for p in self.procs if p['proname']==name and int(p['pronargs'])==len(inputs) and p['pronamespace']=='11'];(provider,wanted),rule,all_candidates=self.select(candidates,inputs);result=self.by_oid[provider['prorettype']];casts=[self.coercion(a,b) for a,b in zip(inputs,wanted)];detail=dict(resolution_rule=rule)
   self.calls.append(dict(name=name,inputs=inputs,result=result,provider=provider['oid'],mechanism=mechanism,details=detail))
  elif kind=='A_Expr' and n['kind'] in ['AEXPR_IN','AEXPR_BETWEEN']:
   inputs=[self.infer(n['lexpr'])['type']];result='bool';mechanism='ScalarArrayOpExpr' if n['kind']=='AEXPR_IN' else 'BoolExpr';detail=dict(metadata_expansion=n['kind'])
   for index,value in enumerate(n['rexpr']['List']['items']):
    symbol=n['name'][-1]['String']['sval'] if n['kind']=='AEXPR_IN' else '>=' if index==0 else '<='
    self.infer({'A_Expr':dict(kind='AEXPR_OP',name=[{'String':{'sval':symbol}}],lexpr=n['lexpr'],rexpr=value)})
  elif kind=='A_Expr':
   inputs=[self.infer(n['lexpr'])['type'],self.infer(n['rexpr'])['type']];args=inputs[:]
   if n['kind'] in ['AEXPR_OP_ANY','AEXPR_OP_ALL']:q.require(args[1].startswith('_'),'Scalar array operand');args[1]=args[1][1:];mechanism='ScalarArrayOpExpr'
   symbol=n['name'][-1]['String']['sval'];candidates=[(p,[self.by_oid[p['oprleft']],self.by_oid[p['oprright']]]) for p in self.ops if p['oprname']==symbol and p['oprleft']!='0' and p['oprright']!='0' and p['oprnamespace']=='11']
   (op,wanted),rule,all_candidates=self.select(candidates,args,True);result=self.by_oid[op['oprresult']];provider=self.proc_by_oid[op['oprcode']];casts=[self.coercion(a,b) for a,b in zip(args,wanted)];detail=dict(operator=op,candidate_oids=[p['oid'] for p,_ in all_candidates],resolution_rule=rule,selected_argument_types=wanted,scalar_array=n['kind']=='AEXPR_OP_ANY')
  elif kind=='BoolExpr':
   inputs=[self.infer(a)['type'] for a in n['args']];q.require(set(inputs)=={'bool'},'Nonboolean boolean input');result='bool'
  elif kind=='NullTest':inputs=[self.infer(n['arg'])['type']];result='bool';detail=dict(nulltest=n['nulltesttype'])
  elif kind=='A_Indirection':
   a=self.infer(n['arg'])['type'];q.require(a.startswith('_'),'Nonarray subscript');inputs=[a];result=a[1:];mechanism='SubscriptingRef'
   for index in n['indirection']:q.require(self.infer(index['A_Indices']['uidx'])['type']=='int4','Array index coercion')
   detail=dict(subscript_handler=self.types[a]['typsubscript'])
  elif kind=='MinMaxExpr':
   inputs=[self.infer(a)['type'] for a in n['args']];q.require(len(set(inputs))==1,'MinMax common type needed');result=inputs[0];detail=dict(comparison_family_required=True,ordering_type=result)
  elif kind=='SQLValueFunction':q.require(n['op']=='SVFOP_SESSION_USER','Unexpected SQLValueFunction');result='name';detail=dict(session_identity=True)
  elif kind=='SubLink':q.require(n['subLinkType']=='EXISTS_SUBLINK','Unexpected SubLink');result='bool';detail=dict(query=n['subselect'])
  elif kind=='SortBy':inputs=[self.infer(n['node'])['type']];result=inputs[0];detail=dict(default_btree_order=True,ordering_type=result)
  else:raise RuntimeError('Unsupported node '+kind)
  collation=self.types.get(result,{}).get('typcollation','0');collation=collation if collation not in ['-',None] else '0'
  children=[]
  if kind=='FuncCall':children=n.get('args',[])
  elif kind=='A_Expr' and n['kind'] in ['AEXPR_OP','AEXPR_OP_ANY']:children=[n['lexpr'],n['rexpr']]
  elif kind=='TypeCast':children=[n['arg']]
  elif kind=='MinMaxExpr':children=n['args']
  elif kind=='A_Indirection':children=[n['arg']]
  elif kind=='SortBy':children=[n['node']]
  child_collations=[self.infer(x)['collation_oid'] for x in children]
  # Unknown literal coercion supplies target type collation before assignment.
  for index,cast in enumerate(casts):
   if index<len(child_collations) and cast['source']=='unknown':child_collations[index]=self.types[cast['target']]['typcollation']
  nondefault={c for c in child_collations if c not in ['0','100']}
  q.require(len(nondefault)<=1,'Conflicting implicit collations')
  inputcollation=next(iter(nondefault)) if nondefault else '100' if '100' in child_collations else '0'
  if collation!='0' and children:collation=inputcollation if inputcollation!='0' else collation
  if provider:self.providers_seen.add(provider['oid'])
  for cast in casts:
   if cast.get('provider_oid') not in [None,'0','-']:self.providers_seen.add(cast['provider_oid'])
  return dict(type=result,collation_oid=collation,input_collation_oid=inputcollation,input_types=inputs,provider_oid=provider['oid'] if provider else None,casts=casts,mechanism=mechanism,details=detail)

def prepare(parser):
 r=Resolver(parser);denom=json.loads((OUT.parent/'package-0090-full-reachable-expectation-closure/expression-site-denominator.json').read_text());q.require(denom['total']==190,'Denominator drift');sites=json.loads(ADD.read_text())['operator_and_implicit_expression_sites'];resolved=[]
 for frozen,site in zip(denom['sites'],sites):
  r.env(site['statement_ordinal']);item=r.infer({site['kind']:site['ast']});resolved.append({**frozen,'STATIC_INPUT_TYPES':item['input_types'],'EXPECTED_OUTPUT_TYPE':item['type'],'EXPECTED_PROVIDER':item['provider_oid'],'EXPECTED_CAST_PATH':item['casts'],'analysis':item,'EXPECTED_RESOLUTION_STATUS':'INDEPENDENT_STATIC_DERIVATION','EXPECTED_SECURITY_CONTEXT':'SECURITY DEFINER flooow_offline_audit_owner; pg_catalog,pg_temp','EXPECTED_ERROR_NULL_RELEVANCE':'PLpgSQL WHEN OTHERS wraps reached error P0017; IF NULL is not TRUE; provider strictness retained separately'})
 save('expression-site-v3.json',dict(total=190,typed=len(resolved),untyped=0,stable_site_ids=True,source_sha=q.SOURCE_HASH,sites=resolved,separately_governed_correction=dict(decision='PACKAGE0090/S04/return-tuple-correction/v1',casts=3,historical_denominator_unchanged=True)))
 save('operator-resolution-v3.json',dict(total=110,resolved=sum(x['EXPRESSION_KIND']=='A_Expr' for x in resolved),sites=[x for x in resolved if x['EXPRESSION_KIND']=='A_Expr']))
 save('cast-resolution-v3.json',dict(explicit_total=14,explicit_sites=[x for x in resolved if x['EXPRESSION_KIND']=='TypeCast'],other_sites=[x for x in resolved if x['EXPRESSION_KIND'] not in ['TypeCast','A_Expr']]))
 save('resolved-call-instances.json',r.calls)
 print(json.dumps(dict(typed=len(resolved),operator_sites=sum(x['EXPRESSION_KIND']=='A_Expr' for x in resolved))))
 return r,resolved
if __name__=='__main__':
 import sys
 sys.path.insert(0,str(Path.home()/'.codex/tmp/package0090-pglast-8.5'))
 from pglast.parser import parse_sql_json
 prepare(parse_sql_json)
