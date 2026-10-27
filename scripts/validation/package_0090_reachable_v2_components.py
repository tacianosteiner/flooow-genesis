"""Build independently sourced reachable provider and metadata components."""
import json,re
from pathlib import Path
import package_0090_source_closure as q
import package_0090_reachable_v2 as e
import package_0090_t10_expectations as access
import package_0090_semantic_ledger as ledger
OUT=e.OUT
APP=['public.offline_binding_header','public.offline_deadline_policy','public.offline_readiness']
CAT=['pg_auth_members','pg_authid','pg_db_role_setting']

def prepare(r,sites):
 global APP
 from package_0090_reachable_v2_ddl import DDL
 model=DDL(r);APP=model.app;model.emit()
 constraints=[];triggers=[];relations=[];columns=[];defaults=[];index_types=set();type_roots=set(r.locals.values())|set(r.params.values());functions=set();contexts=[]
 for site in sites:
  a=site['analysis'];type_roots.update([a['type']]+a['input_types'])
  if a['provider_oid']:functions.add(a['provider_oid'])
  for c in a['casts']:
   if c.get('provider_oid') not in [None,'0','-']:functions.add(c['provider_oid'])
 for c in json.loads(e.ADD.read_text())['call_sites']:
  r.env(c['statement_ordinal']);node={'FuncCall':dict(funcname=[{'String':{'sval':x}} for x in c['callee'].split('.')],args=c['argument_asts'])};a=r.infer(node);contexts.append(dict(source=c,analysis=a));functions.add(a['provider_oid']);type_roots.update(a['input_types']+[a['type']])
 # Complete local/record/source-column type roots. pg_roles is expanded from the
 # independently frozen system_views.sql, including both underlying catalogs.
 for name in APP+['pg_catalog.'+x for x in CAT]+['pg_catalog.pg_roles','public.flyway_schema_history']:
  type_roots.update(r.relations[name].values())
  relations.append(dict(name=name,kind='v' if name=='pg_catalog.pg_roles' else 'r',owner='postgres',RLS=False,force_RLS=False,persistence='p',expansion=['pg_catalog.pg_authid','pg_catalog.pg_db_role_setting'] if name=='pg_catalog.pg_roles' else [],security_invoker=False if name=='pg_catalog.pg_roles' else None))
 # Ownership is derived from chronological canonical ALTER statements; role
 # purpose or writer identity never substitutes for object ownership.
 relation_by_name={x['name']:x for x in relations}
 for raw in r.tree:
  n=raw['stmt']
  if 'AlterTableStmt'in n:
   a=n['AlterTableStmt'];rv=a['relation'];name=rv.get('schemaname','public')+'.'+rv['relname']
   for command in a.get('cmds',[]):
    c=command['AlterTableCmd']
    if name in relation_by_name and c['subtype']=='AT_ChangeOwner':relation_by_name[name]['owner']=c['newowner']['rolename']
  if 'AlterOwnerStmt'in n:
   a=n['AlterOwnerStmt']
   if 'relation'in a:
    rv=a['relation'];name=rv.get('schemaname','public')+'.'+rv['relname']
    if name in relation_by_name:relation_by_name[name]['owner']=a['newowner']['rolename']
 for raw in r.tree:
  n=raw['stmt'];c=n.get('CreateStmt')
  if c:
   rv=c['relation'];name=rv.get('schemaname','public')+'.'+rv['relname']
   if name in APP:
    for num,col in enumerate([x['ColumnDef'] for x in c['tableElts'] if 'ColumnDef'in x],1):
     cs=[x['Constraint'] for x in col.get('constraints',[])];typ=r.typename(col['typeName']);tm=col['typeName'].get('typmods',[]);typmod=tm[0]['A_Const']['ival']['ival'] if tm else -1
     default=next((z.get('raw_expr') for z in cs if z['contype']=='CONSTR_DEFAULT'),None)
     columns.append(dict(relation=name,attnum=num,name=col['colname'],type=typ,typmod=typmod,not_null=any(z['contype']=='CONSTR_NOTNULL' for z in cs),collation=int(r.types[typ]['typcollation']),generated='',identity='',dropped=False,inheritance_count=0,is_local=True,default=default,column_acl=None))
     defaults.append(dict(relation=name,column=col['colname'],expression=default,classification='CURRENTNESS_METADATA' if default else 'PROVEN_IRRELEVANT',runtime_read='S04 reads existing rows; no INSERT/UPDATE/default evaluation'))
    r.context={};oldlocals=r.locals.copy();r.locals.update(r.relations[name])
    for x in c['tableElts']:
     if 'Constraint' not in x:continue
     con=x['Constraint'];analysis=r.infer(con['raw_expr']) if 'raw_expr'in con else None;constraints.append(dict(relation=name,source=ledger.strip_positions(con),analysis=analysis,classification='CURRENTNESS_INTEGRITY_RELEVANT',runtime_READ_does_not_fire=True))
     for key in con.get('keys',[]):index_types.add(r.relations[name][key['String']['sval']])
    r.locals=oldlocals
  if 'CreateTrigStmt'in n:
   t=n['CreateTrigStmt'];name=t['relation'].get('schemaname','public')+'.'+t['relation']['relname']
   if name in APP:triggers.append(dict(relation=name,source=ledger.strip_positions(t),classification='CURRENTNESS_INTEGRITY_RELEVANT',runtime_reachable=False,proof='S04 body contains SELECT/RETURN QUERY and transaction_read_only guard; DML/TRUNCATE trigger cannot execute on this path'))
 # Inline and ALTER constraints are part of the same source graph. The
 # chronological DDL model also follows FK parents to a fixed point.
 constraints=model.constraints;triggers=model.triggers
 for con in constraints:
  c=con['source'];oldlocals=r.locals.copy();r.locals.update(r.relations[con['relation']]);r.context={}
  con['analysis']=r.infer(c['raw_expr']) if c.get('raw_expr') else None
  r.locals=oldlocals
 for proc in r.procs:
  if proc['proname'] in ['RI_FKey_check_ins','RI_FKey_check_upd','RI_FKey_noaction_del','RI_FKey_noaction_upd']:functions.add(proc['oid'])
 # Reference-observer SQL is a separately named metadata root, not an
 # addition to the historical S04 expression/call denominators.
 observer_signatures=[('jsonb_build_object',['any']),('json_build_object',['any']),('jsonb_agg',['anyelement']),('json_agg',['anyelement']),('array_agg',['anynonarray']),('bool_and',['bool']),('count',[]),('count',['any']),('to_jsonb',['anyelement']),('aclexplode',['_aclitem']),('acldefault',['char','oid']),('pg_get_userbyid',['oid']),('upper',['text']),('pg_get_expr',['pg_node_tree','oid']),('pg_get_constraintdef',['oid','bool']),('pg_get_viewdef',['oid','bool']),('pg_get_indexdef',['oid']),('pg_typeof',['any']),('to_regclass',['text']),('to_regprocedure',['text']),('to_regtype',['text']),('current_database',[]),('unnest',['anyarray']),('pg_my_temp_schema',[]),('array_position',['anycompatiblearray','anycompatible'])]
 observer_signatures += [(name,['name','text','text']) for name in ['has_function_privilege','has_schema_privilege','has_table_privilege','has_database_privilege','has_type_privilege','has_language_privilege']]+[('has_column_privilege',['name','text','text','text']),('has_table_privilege',['name','oid','text']),('has_column_privilege',['name','oid','text','text'])]
 observer_oids=[]
 for name,args in observer_signatures:
  candidates=[p for p in r.procs if p['proname']==name and r.args(p)==args];q.require(len(candidates)==1,'Observer provider signature not unique '+str((name,args)));functions.add(candidates[0]['oid']);observer_oids.append(candidates[0]['oid'])
 aggregates=[a for a in r.rows['pg_aggregate'] if a['aggfnoid'] in functions]
 for aggregate in aggregates:
  for field in ['aggtransfn','aggfinalfn','aggcombinefn','aggserialfn','aggdeserialfn','aggmtransfn','aggminvtransfn','aggmfinalfn']:
   oid=aggregate[field]
   if oid not in ['0','-']:functions.add(oid)
 e.save('observer-provider-v2.json',dict(function_oids=observer_oids,aggregates=aggregates,scope='Reference qualification observer providers; opaque PostgreSQL C internals bind to image/native/library identity rather than unrelated global SQL expansion',catalog_ABI_source='Pinned postgres.bki and system_constraints.sql; privileged provider-ABI changes require full provider requalification and future invalidation',independent=True))
 access_methods=[a for a in r.rows['pg_am'] if a['amname'] in ['heap','btree']]
 for method in access_methods:functions.add(method['amhandler'])
 e.save('access-method-v2.json',dict(methods=access_methods,source='BKI heap/btree providers; their handler functions and native identity are transitive graph nodes',independent=True))
 # All functions discovered in constraint expressions are separate metadata edges.
 for call in r.calls: functions.add(call['provider'])
 functions.update(r.providers_seen)
 # Flyway provider constructor: source-derived ten columns, not observed schema.
 constructor=(OUT.parent/'package-0090-full-reachable-expectation-closure/flyway-history-constructor-template.txt').read_text()
 history_sql=constructor[:constructor.index(')\x01;')+1].replace('\x01','public.flyway_schema_history')+';'
 history=json.loads(r.parser(history_sql))['stmts'][0]['stmt']['CreateStmt']
 for num,c in enumerate([x['ColumnDef'] for x in history['tableElts'] if 'ColumnDef'in x],1):
  typ=r.typename(c['typeName']);mods=c['typeName'].get('typmods',[]);tm=mods[0]['A_Const']['ival']['ival']+4 if mods else -1;cs=[x['Constraint'] for x in c.get('constraints',[])];default=next((z.get('raw_expr') for z in cs if z['contype']=='CONSTR_DEFAULT'),None)
  columns.append(dict(relation='public.flyway_schema_history',attnum=num,name=c['colname'],type=typ,typmod=tm,not_null=any(z['contype']=='CONSTR_NOTNULL' for z in cs),collation=int(r.types[typ]['typcollation']),generated='',identity='',dropped=False,inheritance_count=0,is_local=True,default=default,column_acl=None));type_roots.add(typ)
  defaults.append(dict(relation='public.flyway_schema_history',column=c['colname'],expression=default,classification='CURRENTNESS_METADATA' if default else 'PROVEN_IRRELEVANT'))
  if default:
   a=r.infer(default);functions.add(a['provider_oid']);coerce=r.casts[a['type'],typ];functions.add(coerce['castfunc'])
 # Bootstrap catalog column rules from bootstrap.c DefineAttr, including NAME's
 # special C collation and FORCE [NOT] NULL annotations.
 bki_text=(OUT/'provider/postgres.bki').read_text()
 for name in CAT:
  prefix_fixed=True;block=bki_text.split('create '+name+' ',1)[1].split('\n )',1)[0]
  for num,c in enumerate(r.defs[name],1):
   typ=c['type'];length=r.types[typ]['typlen'];fixed=length=='NAMEDATALEN' or int(length)>0;line=next(x for x in block.splitlines() if re.match(r'\s*'+c['name']+r' = ',x));nn=True if 'FORCE NOT NULL'in line else False if 'FORCE NULL'in line else prefix_fixed and fixed;prefix_fixed=prefix_fixed and fixed and nn
   columns.append(dict(relation='pg_catalog.'+name,attnum=num,name=c['name'],type=typ,typmod=-1,not_null=nn,collation=950 if int(r.types[typ]['typcollation']) else 0,generated='',identity='',dropped=False,inheritance_count=0,is_local=True,default=None,column_acl=None))
 # View output nullability is not inherited; system_views source selects these
 # exact fields, with masked password and nullable LEFT JOIN role settings.
 view=(OUT/'provider/system_views.sql').read_text().split('CREATE VIEW pg_roles AS',1)[1].split(';',1)[0]
 view_ast=json.loads(r.parser('SELECT'+view.split('SELECT',1)[1]))['stmts'][0]['stmt']['SelectStmt']
 fields=['rolname','rolsuper','rolinherit','rolcreaterole','rolcreatedb','rolcanlogin','rolreplication','rolconnlimit','rolpassword','rolvaliduntil','rolbypassrls','rolconfig','oid']
 q.require(len(fields)==len(view_ast['targetList']),'View expansion denominator')
 for num,name in enumerate(fields,1):
  typ=r.relations['pg_catalog.pg_roles'][name];columns.append(dict(relation='pg_catalog.pg_roles',attnum=num,name=name,type='text' if name=='rolpassword' else typ,typmod=-1,not_null=False,collation=100 if name=='rolpassword' else 950 if int(r.types[typ]['typcollation']) else 0,generated='',identity='',dropped=False,inheritance_count=0,is_local=True,default=None,column_acl=None))
 # Planner index/ordering paths: independently frozen default btree families.
 index_types.update(['int4','int8','uuid','text','name','oid','bool'])
 families={p['opcfamily'] for p in r.rows['pg_opclass'] if p['opcmethod']=='403' and p['opcdefault']=='t' and r.by_oid[p['opcintype']] in index_types}
 support=[]
 for p in r.rows['pg_amproc']:
  if p['amprocfamily'] in families:functions.add(p['amproc']);support.append(p)
 for p in r.rows['pg_amop']:
  if p['amopfamily'] in families:
   op=next(o for o in r.ops if o['oid']==p['amopopr']);functions.add(op['oprcode'])
 # Planner may commute/negate operators, and invokes selectivity providers.
 operator_by_oid={op['oid']:op for op in r.ops}
 selected_operator_oids={x['analysis']['details']['operator']['oid'] for x in sites if x['EXPRESSION_KIND']=='A_Expr'}
 selected_operator_oids.update(p['amopopr'] for p in r.rows['pg_amop'] if p['amopfamily'] in families)
 # Constraint-only operators are independently typed metadata dependencies.
 for con in constraints:
  for kind,node in e.walk(con['source'].get('raw_expr',{})):
   if kind=='A_Expr' and node['kind']=='AEXPR_OP':
    # Selection context is the containing relation's own columns.
    old=r.locals.copy();r.locals.update(r.relations[con['relation']]);a=r.infer({'A_Expr':node});r.locals=old;selected_operator_oids.add(a['details']['operator']['oid'])
 seen_operators=set()
 while selected_operator_oids-seen_operators:
  for oid in sorted(selected_operator_oids-seen_operators,key=int):
   op=operator_by_oid[oid];seen_operators.add(oid)
   for field in ['oprcode','oprrest','oprjoin']:
    if op[field] not in ['0','-']:functions.add(op[field])
   for field in ['oprcom','oprnegate']:
    if op[field] not in ['0','-']:selected_operator_oids.add(op[field])
 e.save('selected-operator-provider-graph.json',dict(operators=[operator_by_oid[x] for x in sorted(selected_operator_oids,key=int)],reason='Direct selected operators, default btree paths and planner commutator/negator/selectivity closure',independent=True))
 symbols={op['oprname'] for op in [operator_by_oid[x] for x in selected_operator_oids]}
 candidates=[op for op in r.ops if op['oprnamespace']=='11' and op['oprname'] in symbols]
 candidate_types={op[f] for op in candidates for f in ['oprleft','oprright'] if op[f]!='0'}
 e.save('resolution-candidate-metadata.json',dict(operators=candidates,types=[r.types[r.by_oid[x]] for x in sorted(candidate_types,key=int)],casts=r.rows['pg_cast'],absence_rule='No added/missing candidate operator signatures or cast catalog entries; unselected candidate providers remain proven unreachable under the frozen resolution rules, and do not trigger unrelated I/O expansion',independent=True))
 type_roots.update(['record','trigger','language_handler','void'])
 type_roots.discard('unknown');type_roots.discard('empty_array');types=set();seen_funcs=set();edges=[]
 while functions-seen_funcs or type_roots-types:
  for typ in sorted(type_roots-types):
   q.require(typ in r.types,'Missing independent type '+typ);types.add(typ);t=r.types[typ]
   for field in ['typelem','typarray','typbasetype']:
    oid=t[field]
    if oid not in ['0','-']:type_roots.add(r.by_oid[oid]);edges.append([typ,field,r.by_oid[oid]])
   for field in ['typinput','typoutput','typreceive','typsend','typmodin','typmodout','typanalyze','typsubscript']:
    oid=t[field]
    if oid not in ['0','-']:functions.add(oid);edges.append([typ,field,oid])
  for oid in sorted(functions-seen_funcs,key=int):
   q.require(oid in r.proc_by_oid,'Missing independent function '+oid);seen_funcs.add(oid);p=r.proc_by_oid[oid];type_roots.update(r.args(p));type_roots.add(r.by_oid[p['prorettype']])
   if p['prosupport'] not in ['0','-']:functions.add(p['prosupport']);edges.append([oid,'prosupport',p['prosupport']])
 # Freeze source function identities, including the write-only trigger guard.
 names=['offline_read_history','offline_internal_expected_attestation_guard'];source_functions=[];owners={}
 for raw in r.tree:
  n=raw['stmt'];a=n.get('AlterOwnerStmt')
  if a and a['objectType']=='OBJECT_FUNCTION':
   obj=a['object']['ObjectWithArgs'];owners[obj['objname'][-1]['String']['sval']]=a['newowner']['rolename']
 for raw in r.tree:
  f=raw['stmt'].get('CreateFunctionStmt')
  if f and f['funcname'][-1]['String']['sval'] in names:
   opts={x['DefElem']['defname']:x['DefElem'].get('arg') for x in f['options']};name=f['funcname'][-1]['String']['sval'];source_functions.append(dict(signature=ledger.signature(f),owner=owners[name],source_AST=ledger.strip_positions(f),body=opts['as']['List']['items'][0]['String']['sval'],metadata_only=name!='offline_read_history'))
 access.BASELINE=q.git('rev-parse','HEAD').decode().strip();acl=access.expected(r.parser)
 e.save('relation-view-v2.json',dict(relations=relations,total=len(relations),tables=len(relations)-1,views=1,matviews=0,inheritance_edges=[],source_view_SQL=view,independent=True))
 owner_by_relation={x['name']:x['owner'] for x in relations}
 column_grants={}
 for raw in r.tree:
  g=raw['stmt'].get('GrantStmt')
  if not g or g['objtype']!='OBJECT_TABLE':continue
  for obj in g.get('objects',[]):
   if 'RangeVar' not in obj:continue
   rv=obj['RangeVar'];name=rv.get('schemaname','public')+'.'+rv['relname']
   if name not in owner_by_relation:continue
   for privilege in g.get('privileges',[]):
    p=privilege['AccessPriv']
    for col in p.get('cols',[]):
     for role in g['grantees']:
      grantee=role['RoleSpec'].get('rolename','PUBLIC');key=(name,col['String']['sval'],grantee,p['priv_name'].upper())
      if g.get('is_grant'):column_grants[key]=dict(grantee=grantee,privilege=p['priv_name'].upper(),grantable=bool(g.get('grant_option')),grantor=owner_by_relation[name])
      else:column_grants.pop(key,None)
 for column in columns:
  entries=[v for (rel,col,grantee,priv),v in column_grants.items() if rel==column['relation'] and col==column['name']]
  column['column_acl']=sorted(entries,key=lambda x:(x['grantee'],x['privilege'])) or None
 e.save('column-v2.json',dict(columns=columns,independent=True,ACL_source='Canonical GRANT/REVOKE column AST; bootstrap has no column grants; superuser grantor selected as object owner under PG select_best_grantor semantics'))
 e.save('constraint-v2.json',dict(constraints=constraints,SQL_not_null_constraints=model.not_null,history_primary_key=dict(name='flyway_schema_history_pk',column='installed_rank'),catalog_constraints='Bootstrap unique indexes and not-null metadata from BKI/header declarations; no user SQL CHECK/FK/EXCLUSION additions',independent=True))
 e.save('trigger-v2.json',dict(triggers=triggers,internal_RI_rule='Four internal triggers per FK: referencing AFTER ROW INSERT/UPDATE checks; referenced AFTER ROW DELETE/UPDATE NO ACTION checks; OIDs/names bind through pg_constraint, source factory rules determine deferrability',foreign_keys=[c for c in constraints if c['source']['contype']=='CONSTR_FOREIGN'],independent=True))
 e.save('default-expression-v2.json',dict(defaults=defaults,local_initializers=[s for s in sites if s['SOURCE_LOCATION']['statement_ordinal'] in [0,1,2]],independent=True))
 e.save('sequence-v2.json',dict(sequences=[],proof='All reachable columns from canonical DDL, Flyway constructor and BKI have no SERIAL/IDENTITY/nextval default; all current runtime reads enumerated; no sequence RangeVar',independent=True))
 e.save('type-reachability-v2.json',dict(types=[r.types[t] for t in sorted(types)],edges=edges,composite_binding_rule='For each relation: dynamic rowtype OID bound by pg_type.typrelid=relation.oid; ordered fields equal column component; composite array relationship checked by typelem/typarray; no guessed OIDs',roots=sorted(type_roots),independent=True))
 e.save('planner-support-v2.json',dict(index_type_roots=sorted(index_types),btree_families=sorted(families),btree_support=support,function_support=[dict(supported=p['oid'],support=p['prosupport']) for p in [r.proc_by_oid[o] for o in sorted(functions,key=int)] if p['prosupport']not in ['0','-']],independent=True))
 provider_functions=[dict(r.proc_by_oid[o]) for o in sorted(functions,key=int)]
 overrides=[]
 for raw in json.loads(r.parser((OUT/'provider/system_functions.sql').read_text()))['stmts']:
  definition=raw['stmt'].get('CreateFunctionStmt')
  if not definition:continue
  name=definition['funcname'][-1]['String']['sval'];args=[r.typename(p['FunctionParameter']['argType']) for p in definition.get('parameters',[])]
  matching=[p for p in provider_functions if p['proname']==name and r.args(p)==args]
  if not matching:continue
  q.require(name=='is_normalized' and args==['text','text'],'Unimplemented independent bootstrap override')
  p=matching[0];p['pronargdefaults']='1';p['expected_defaults_SQL']="'NFC'::text";p['proargdefaults']='INDEPENDENT_BOOTSTRAP_DEFAULT';overrides.append(ledger.strip_positions(definition))
 # Language dispatch and SQL-visible native interfaces are explicit graph
 # edges. Their OIDs bind by signature, not by catalog observations.
 native_functions=[]
 native_sources=[('provider/plpgsql--1.0.sql','pg_catalog','$libdir/plpgsql'),('provider/pgcrypto--1.3.sql','offline_crypto','$libdir/pgcrypto')]
 custom=q.ROOT/'applications/marketplace-operations-persistence-postgres/native/flooow_offline_mac32/flooow_offline_mac32--1.0.sql'
 native_texts=[((OUT/name).read_text(),schema,library) for name,schema,library in native_sources]+[(custom.read_text(),'offline_crypto','$libdir/flooow_offline_mac32')]
 for text,schema,library in native_texts:
  text='\n'.join(line for line in text.replace('@extowner@','postgres').splitlines() if not line.startswith('\\'))
  for raw in json.loads(r.parser(text))['stmts']:
   f=raw['stmt'].get('CreateFunctionStmt')
   if not f:continue
   name=f['funcname'][-1]['String']['sval'];args=[r.typename(p['FunctionParameter']['argType']) for p in f.get('parameters',[])]
   if schema=='offline_crypto' and name not in ['hmac','timing_safe_equal32','canonical_spki_ed25519_verify']:continue
   if name=='hmac' and args!=['bytea','bytea','text']:continue
   opts={x['DefElem']['defname']:x['DefElem'].get('arg') for x in f['options']};items=opts['as']['List']['items'];symbol=items[1]['String']['sval'] if len(items)>1 else name
   native_functions.append(dict(signature=schema+'.'+name+'('+','.join(args)+')',owner='postgres',source_AST=ledger.strip_positions(f),native_library=library,symbol=symbol,language='c',metadata_only=name not in ['plpgsql_call_handler','hmac','timing_safe_equal32']))
 e.save('function-identity-v6.json',dict(provider_functions=provider_functions,canonical_functions=source_functions,native_functions=native_functions,bootstrap_overrides=overrides,independent=True,provider_source='Pinned PG18.4 bootstrap/extension artifacts plus exact system_functions.sql replacements and REL_18_4 source; never observed target'))
 e.save('function-reachability-v2.json',dict(provider_function_oids=sorted(functions,key=int),source_functions=[f['signature'] for f in source_functions],call_contexts=contexts,edges=edges,total=len(functions)+len(source_functions)+len(native_functions),native_functions=[x['signature'] for x in native_functions],native_boundary='Internal/C provider implementations are opaque compiled provider bodies bound to immutable image/library and source identity; SQL-visible support/type/cast edges expanded',independent=True))
 e.save('effective-acl-v6.json',dict(direct_source_entries=acl['entries'],provider_rule='All reachable bootstrap functions: PUBLIC EXECUTE default plus owner grant option; PG18 initdb revokes must be independently excluded before complete gate. Builtin types PUBLIC USAGE default; postgres superuser true; no role memberships. View pg_roles executes underlying catalogs as postgres owner; invoker table SELECT required.',principals=access.PRINCIPALS+['postgres'],independent=True,complete=False))
 e.save('polymorphic-resolution-v2.json',dict(instantiations=[x for x in contexts if x['analysis']['mechanism']=='POLYMORPHIC_INSTANTIATION'],independent=True))
 unknown=json.loads((OUT/'unknown-literal-resolution-v2.json').read_text());unknown.update(contexts=[x for x in contexts if any(c['source']=='unknown' for c in x['analysis']['casts'])],expression_coercions=[dict(site=s['SITE_ID'],coercions=s['analysis']['casts']) for s in sites if any(c['source']=='unknown' for c in s['analysis']['casts'])]);e.save('unknown-literal-resolution-v2.json',unknown)
 e.save('collation-v2.json',dict(expressions=[dict(site=s['SITE_ID'],result=s['analysis']['collation_oid'],input=s['analysis']['input_collation_oid']) for s in sites],providers=[x for x in r.rows['pg_collation'] if x['oid']in ['100','950']],database_bootstrap=dict(encoding='UTF8',locale='en_US.utf8'),rules='REL_18_4 parse_collate.c: non-default implicit collation wins over default; conflicts deny; PLpgSQL variables carry declared type collation; runtime witness result collation must match independently derived values',independent=True))
 print(json.dumps(dict(relations=len(relations),columns=len(columns),types=len(types),functions=len(functions)+len(source_functions),constraints=len(constraints),triggers=len(triggers))))
if __name__=='__main__':
 import sys
 sys.path.insert(0,str(Path.home()/'.codex/tmp/package0090-pglast-8.5'));from pglast.parser import parse_sql_json
 r,sites=e.prepare(parse_sql_json);prepare(r,sites)
