"""Semantic source/deparser comparison for the bounded metadata expressions.

Provider/type decisions come from the independent resolver, never the target.
"""
import json
from package_0090_reachable_v2 import walk

def normalize(r,node,target=None):
 k,n=next(iter(node.items()))
 if k=='TypeCast':
  typ=r.typename(n['typeName'])
  if 'A_Const'in n['arg']:return normalize(r,n['arg'],typ)
  return ['cast',typ,normalize(r,n['arg'])]
 if k=='A_Const':
  if 'sval'in n:value=n['sval']['sval']
  elif 'ival'in n:value=n['ival'].get('ival',0)
  elif 'fval'in n:value=n['fval']['fval']
  elif 'boolval'in n:value=n['boolval'].get('boolval',False)
  elif n.get('isnull'):value=None
  else:raise RuntimeError('Unclosed metadata literal')
  typ=r.infer(node)['type'];return ['const',target if typ=='unknown' or target else typ,value]
 if k=='ColumnRef':return ['column','.'.join(x['String']['sval'] for x in n['fields']),r.infer(node)['type']]
 if k=='A_Expr' and n['kind']=='AEXPR_BETWEEN':
  values=n['rexpr']['List']['items'];return normalize(r,{'BoolExpr':dict(boolop='AND_EXPR',args=[{'A_Expr':dict(kind='AEXPR_OP',name=[{'String':{'sval':op}}],lexpr=n['lexpr'],rexpr=v)} for op,v in zip(['>=','<='],values)])})
 if k=='A_Expr' and n['kind']=='AEXPR_IN':
  return ['in' if n['name'][-1]['String']['sval']=='=' else 'not_in',normalize(r,n['lexpr']),[normalize(r,x,r.infer(n['lexpr'])['type']) for x in n['rexpr']['List']['items']]]
 if k=='A_Expr' and n['kind'] in ['AEXPR_OP_ANY','AEXPR_OP_ALL']:
  arr=n['rexpr'];values=arr.get('A_ArrayExpr',{}).get('elements')
  if values is None:raise RuntimeError('Unclosed cooked array constant')
  symbol=n['name'][-1]['String']['sval'];qkind=n['kind']
  if (symbol,qkind) not in [('=','AEXPR_OP_ANY'),('<>','AEXPR_OP_ALL')]:raise RuntimeError('Unclosed scalar-array semantic equivalence')
  return ['in' if qkind=='AEXPR_OP_ANY' else 'not_in',normalize(r,n['lexpr']),[normalize(r,x,r.infer(n['lexpr'])['type']) for x in values]]
 if k=='A_Expr':
  a=r.infer(node);wanted=a['details']['selected_argument_types'];return ['operator',n['kind'],a['details']['operator']['oid'],normalize(r,n['lexpr'],wanted[0]),normalize(r,n['rexpr'],wanted[1])]
 if k=='BoolExpr':
  children=[]
  for child in n['args']:
   item=normalize(r,child)
   if item[:1]==[n['boolop']]:children.extend(item[1:])
   else:children.append(item)
  return [n['boolop']]+children
 if k=='FuncCall':
  a=r.infer(node);p=r.proc_by_oid[a['provider_oid']];types=r.args(p);return ['function',p['oid']]+[normalize(r,x,t) for x,t in zip(n.get('args',[]),types)]
 if k=='NullTest':return ['null',n['nulltesttype'],normalize(r,n['arg'])]
 raise RuntimeError('Unclosed metadata node '+k)

def parse_expression(r,text):return json.loads(r.parser('SELECT '+text))['stmts'][0]['stmt']['SelectStmt']['targetList'][0]['ResTarget']['val']
