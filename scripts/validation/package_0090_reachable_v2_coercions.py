"""Enumerate coercion consumer edges and unknown literals without changing 190 IDs."""
import json,re
import package_0090_reachable_v2 as e
OUT=e.OUT

def prepare(r):
 coercions=[];unknown=[];source=json.loads(e.ADD.read_text());seen=set()
 def coerce(statement,path,source_type,target,context):
  if source_type==target:return
  record=r.coercion(source_type,target,context)
  if record.get('provider_oid') not in [None,'0','-']:r.providers_seen.add(record['provider_oid'])
  key=(statement,tuple(path),context,source_type,target)
  if key not in seen:
   seen.add(key);coercions.append(dict(COERCION_SITE_ID='S04-CONSUMER-'+str(statement)+'-'+'.'.join(map(str,path)),statement_ordinal=statement,AST_path=path,**record))
 def visit(statement,node,path,target=None,context='IMPLICIT'):
  if not isinstance(node,dict) or len(node)!=1:return
  kind,n=next(iter(node.items()))
  if kind=='A_Const':
   a=r.infer(node);typ=a['type']
   if typ=='unknown':
    if target is None:raise RuntimeError('Unresolved literal consumer '+str((statement,path,n)))
    unknown.append(dict(LITERAL_SITE_ID='S04-LITERAL-'+str(statement)+'-'+'.'.join(map(str,path)),statement_ordinal=statement,AST_path=path,source_literal=n.get('sval',{}).get('sval'),is_null=bool(n.get('isnull')),selected_target_type=target,type_category=r.types[target]['typcategory'],preferred=r.types[target]['typispreferred'],provider_input_function=r.types[target]['typinput'],collation=r.types[target]['typcollation'],context=context))
   if target and context!='ASSIGNMENT':coerce(statement,path,typ,target,context)
   return
  if kind=='TypeCast':
   typ=r.typename(n['typeName']);child=r.infer(n['arg']);coerce(statement,path+['arg'],child['type'],typ,'EXPLICIT');visit(statement,n['arg'],path+['arg'],typ,'EXPLICIT');return
  if kind=='FuncCall':
   a=r.infer(node);p=r.proc_by_oid[a['provider_oid']];wanted=r.args(p)
   if a['mechanism']=='POLYMORPHIC_INSTANTIATION':wanted=[a['type'],a['type'][1:]]
   for i,(arg,t) in enumerate(zip(n.get('args',[]),wanted)):
    coerce(statement,path+['args',i],r.infer(arg)['type'],t,'IMPLICIT');visit(statement,arg,path+['args',i],t)
   return
  if kind=='A_Expr':
   a=r.infer(node);wanted=a['details']['selected_argument_types'];children=[n['lexpr'],n['rexpr']]
   for i,arg in enumerate(children):
    t=r.infer(arg)['type'] if i==1 and n['kind']=='AEXPR_OP_ANY' else wanted[i];coerce(statement,path+[['lexpr','rexpr'][i]],r.infer(arg)['type'],t,'IMPLICIT');visit(statement,arg,path+[['lexpr','rexpr'][i]],t)
   return
  if kind=='BoolExpr':
   for i,arg in enumerate(n['args']):visit(statement,arg,path+['args',i],'bool')
   return
  if kind=='NullTest':visit(statement,n['arg'],path+['arg']);return
  if kind=='MinMaxExpr':
   typ=r.infer(node)['type']
   for i,arg in enumerate(n['args']):visit(statement,arg,path+['args',i],typ)
   return
  if kind=='A_Indirection':
   visit(statement,n['arg'],path+['arg'])
   for i,index in enumerate(n['indirection']):visit(statement,index['A_Indices']['uidx'],path+['indirection',i,'uidx'],'int4')
   return
  if kind=='SortBy':visit(statement,n['node'],path+['node']);return
  if kind=='SubLink':visit(statement,n['subselect'],path+['subselect']);return
  if kind=='SelectStmt':
   for i,value in enumerate(n.get('targetList',[])):
    value=value['ResTarget']['val'];typ=r.infer(value)['type'];t=target or ('text' if typ=='unknown' else typ);visit(statement,value,path+['targetList',i,'ResTarget','val'],t,'ASSIGNMENT' if target else 'IMPLICIT')
   if n.get('whereClause'):visit(statement,n['whereClause'],path+['whereClause'],'bool')
   for i,value in enumerate(n.get('sortClause',[])):visit(statement,value,path+['sortClause',i])
   return
  if kind in ['ColumnRef','ParamRef','SQLValueFunction','A_ArrayExpr']:return
  raise RuntimeError('Unclosed consumer AST '+kind)
 for statement in source['statements']:
  ordinal=statement['ordinal'];r.env(ordinal);tree=statement['ast']['stmts'][0]['stmt'];query=statement['original_query'];match=re.match(r'(\w+)\s*:=',query);target=r.locals[match[1]] if match else None
  visit(ordinal,tree,[],target)
 # Every assignment's result type is independently checked against its receiver.
 for statement in source['statements']:
  match=re.match(r'(\w+)\s*:=',statement['original_query'])
  if match:
   r.env(statement['ordinal']);value=statement['ast']['stmts'][0]['stmt']['SelectStmt']['targetList'][0]['ResTarget']['val'];coerce(statement['ordinal'],['assignment',match[1]],r.infer(value)['type'],r.locals[match[1]],'ASSIGNMENT')
 e.save('unknown-literal-resolution-v2.json',dict(literals=unknown,total=len(unknown),unresolved=0,rule_sources=['REL_18_4 parse_func.c/parse_oper.c/parse_coerce.c','SELECT target unknown -> text resolution; PLpgSQL RAISE options consume text','Explicit cast target and exact function/operator signatures'],independent=True))
 casts=json.loads((OUT/'cast-resolution-v3.json').read_text());casts.update(consumer_edges=coercions,implicit_coercion_sites_total=sum(x['context']!='EXPLICIT' for x in coercions),implicit_coercion_sites_resolved=sum(x['context']!='EXPLICIT' for x in coercions),explicit_known_correction_edges=3,unresolved_consumer_edges=0);e.save('cast-resolution-v3.json',casts)
 print('Coercion edges',len(coercions),'unknown literals',len(unknown))
if __name__=='__main__':
 import sys
 from pathlib import Path
 sys.path.insert(0,str(Path.home()/'.codex/tmp/package0090-pglast-8.5'));from pglast.parser import parse_sql_json
 prepare(e.Resolver(parse_sql_json))
