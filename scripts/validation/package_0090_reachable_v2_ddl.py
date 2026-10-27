"""Chronological source DDL graph, including inline/ALTER constraints and FK edges."""
import copy,re,json
import package_0090_source_closure as q
import package_0090_semantic_ledger as ledger
import package_0090_reachable_v2 as e

def name(rv):return rv.get('schemaname','public')+'.'+rv['relname']
def generated(table,column,label):
 q.require(table.isascii() and (column is None or column.isascii()),'Unsupported multibyte generated identifier')
 a=len(table);b=len(column or '');available=63-len(label)-1-(1 if column else 0)
 while a+b>available:
  if a>b:a-=1
  else:b-=1
 return table[:a]+('_'+column[:b] if column else '')+'_'+label

class DDL:
 def __init__(self,r):
  self.r=r;self.tables={};self.constraints=[];self.indexes=[];self.triggers=[]
  for raw in r.tree:
   s=raw['stmt'].get('CreateStmt')
   if s:self.tables[name(s['relation'])]=s
  edges=[]
  for raw in r.tree:
   n=raw['stmt'];rv=n.get('CreateStmt',{}).get('relation') or n.get('AlterTableStmt',{}).get('relation')
   if rv:
    for kind,con in e.walk(n):
     if kind=='Constraint' and con['contype']=='CONSTR_FOREIGN':edges.append((name(rv),name(con['pktable'])))
  roots={'public.offline_binding_header','public.offline_readiness','public.offline_deadline_policy'}
  while True:
   nxt=roots|{b for a,b in edges if a in roots}|{a for a,b in edges if b in roots}
   if nxt==roots:break
   roots=nxt
  q.require(roots<=set(self.tables),'Referenced table absent from canonical definitions');self.app=sorted(roots);self.owners={t:'postgres' for t in sorted(roots)};self.columns={};self.used={t:set() for t in roots}
  for raw in r.tree:
   node=raw['stmt']
   if 'CreateStmt'in node:
    s=node['CreateStmt'];table=name(s['relation'])
    if table not in roots:continue
    cols=[]
    for item in s['tableElts']:
     if 'ColumnDef'not in item:continue
     col=item['ColumnDef'];cs=[x['Constraint'] for x in col.get('constraints',[])];typ=r.typename(col['typeName']);mods=col['typeName'].get('typmods',[]);tm=mods[0]['A_Const']['ival']['ival'] if mods else -1
     if mods and typ in ['varchar','bpchar']:tm+=4
     default=next((x.get('raw_expr') for x in cs if x['contype']=='CONSTR_DEFAULT'),None)
     cols.append(dict(relation=table,attnum=len(cols)+1,name=col['colname'],type=typ,typmod=tm,not_null=any(x['contype']in ['CONSTR_NOTNULL','CONSTR_PRIMARY'] for x in cs),collation=int(r.types[typ]['typcollation']),generated='',identity='',dropped=False,inheritance_count=0,is_local=True,default=default,column_acl=None))
     for con in cs:
      if con['contype'] not in ['CONSTR_NULL','CONSTR_NOTNULL','CONSTR_DEFAULT']:self.add_constraint(table,con,col['colname'])
    self.columns[table]=cols
    for item in s['tableElts']:
     if 'Constraint'in item:self.add_constraint(table,item['Constraint'])
   if 'AlterTableStmt'in node:
    s=node['AlterTableStmt'];table=name(s['relation'])
    if table not in roots:continue
    for item in s['cmds']:
     c=item['AlterTableCmd'];kind=c['subtype']
     if kind=='AT_ChangeOwner':self.owners[table]=c['newowner']['rolename']
     elif kind=='AT_AddConstraint':self.add_constraint(table,c['def']['Constraint'])
     else:raise RuntimeError('Unimplemented reachable ALTER TABLE '+kind)
   if 'CreateTrigStmt'in node:
    s=node['CreateTrigStmt'];table=name(s['relation'])
    if table in roots:self.triggers.append(dict(relation=table,source=ledger.strip_positions(s),classification='CURRENTNESS_INTEGRITY_RELEVANT',runtime_reachable=False,proof='Read-only S04 path cannot fire DML/TRUNCATE triggers; definitions remain mutable currentness inputs'))
   if 'IndexStmt'in node:
    s=node['IndexStmt'];table=name(s['relation'])
    if table in roots:self.indexes.append(dict(relation=table,source=ledger.strip_positions(s),classification='PLANNER_AND_CURRENTNESS_METADATA'))
  for con in self.constraints:
   c=con['source'];table=con['relation']
   if c['contype']=='CONSTR_PRIMARY':
    for column in c['keys']:
     next(x for x in self.columns[table] if x['name']==column['String']['sval'])['not_null']=True
  # SQL CREATE emits one NOT NULL constraint per not-null column. Bootstrap
  # catalogs are different: DefineAttr sets the flag directly, without these
  # SQL-level n constraints; catalog PK/UNIQUE entries come from system_constraints.sql.
  self.not_null=[dict(relation=t,column=c['name'],conname=generated(t.split('.')[-1],c['name'],'not_null'),attnum=c['attnum']) for t in self.app for c in self.columns[t] if c['not_null']]
 def add_constraint(self,table,original,column=None):
  con=copy.deepcopy(original);kind=con['contype']
  q.require(kind in ['CONSTR_PRIMARY','CONSTR_UNIQUE','CONSTR_FOREIGN','CONSTR_CHECK','CONSTR_EXCLUSION'],'Unknown reachable constraint '+kind)
  if column and kind in ['CONSTR_PRIMARY','CONSTR_UNIQUE']:con['keys']=[{'String':{'sval':column}}]
  if column and kind=='CONSTR_FOREIGN':con['fk_attrs']=[{'String':{'sval':column}}]
  if not con.get('conname'):
   if kind=='CONSTR_CHECK':
    refs={'.'.join(x['String']['sval'] for x in node['fields']) for tag,node in e.walk(con.get('raw_expr',{})) if tag=='ColumnRef'}
    column=next(iter(refs)).split('.')[-1] if len(refs)==1 else None
   label={'CONSTR_PRIMARY':'pkey','CONSTR_UNIQUE':'key','CONSTR_FOREIGN':'fkey','CONSTR_CHECK':'check','CONSTR_EXCLUSION':'excl'}[kind];base=label;index=0
   while True:
    candidate=generated(table.split('.')[-1],None if kind=='CONSTR_PRIMARY' else column,label)
    if candidate not in self.used[table]:break
    index+=1;label=base+str(index)
   con['conname']=candidate
  q.require(con['conname'] not in self.used[table],'Constraint name collision');self.used[table].add(con['conname']);self.constraints.append(dict(relation=table,source=ledger.strip_positions(con),classification='CURRENTNESS_INTEGRITY_RELEVANT',runtime_READ_does_not_fire=True))
 def emit(self):
  e.save('source-ddl-closure.json',dict(app_relations=self.app,owners=self.owners,columns=self.columns,constraints=self.constraints,SQL_not_null_constraints=self.not_null,indexes=self.indexes,triggers=self.triggers,independent=True,source='Canonical CREATE/ALTER and exact PG18 generated-name/factory rules'))
