"""Check all source/native constraint, index and trigger identities."""
import json,re,sys
from pathlib import Path
import package_0090_source_closure as q
import package_0090_reachable_v2 as e
from package_0090_reachable_v2_metadata_semantics import normalize,parse_expression
OUT=e.OUT

def quote(s):return "'"+s.replace("'","''")+"'"
def qualify(sql,run,container,folder,record,fixture,runtime_work):
 record['recipe_hashes'][Path(__file__).name]=q.sha(Path(__file__).read_bytes());sys.path.insert(0,str(Path.home()/'.codex/tmp/package0090-pglast-8.5'));from pglast.parser import parse_sql_json
 r=e.Resolver(parse_sql_json);cases=[];observed={}
 def last(result):return json.loads(result.stdout.decode().splitlines()[-1])
 def case(name,passed,details,group):
  c=dict(name=name,passed=bool(passed),details=details,group=group);cases.append(c);record['cases'].append(c)
  (folder/'integrity-runtime.json').write_text(json.dumps(dict(cases=cases,observed=observed),indent=2)+'\n');q.require(passed,name)
 cols=json.loads((OUT/'column-v2.json').read_text())['columns'];rels=sorted({c['relation'] for c in cols});objects=','.join(quote(x)+'::regclass' for x in rels);columns={(c['relation'],c['name']):c for c in cols}
 source=json.loads((OUT/'constraint-v2.json').read_text())['constraints'];indexes=json.loads((OUT/'index-v2.json').read_text())['indexes']
 actual=last(sql("SELECT jsonb_agg(jsonb_build_object('relation',n.nspname||'.'||t.relname,'name',c.conname,'type',c.contype,'validated',c.convalidated,'enforced',c.conenforced,'deferrable',c.condeferrable,'deferred',c.condeferred,'keys',c.conkey,'parent',CASE WHEN c.confrelid=0 THEN NULL ELSE rn.nspname||'.'||rt.relname END,'parent_keys',c.confkey,'match',c.confmatchtype,'update',c.confupdtype,'delete',c.confdeltype,'index',ix.relname,'expression',pg_get_expr(c.conbin,c.conrelid)) ORDER BY n.nspname,t.relname,c.conname) FROM pg_constraint c JOIN pg_class t ON t.oid=c.conrelid JOIN pg_namespace n ON n.oid=t.relnamespace LEFT JOIN pg_class rt ON rt.oid=c.confrelid LEFT JOIN pg_namespace rn ON rn.oid=rt.relnamespace LEFT JOIN pg_class ix ON ix.oid=c.conindid WHERE c.conrelid IN ("+objects+");"));observed['constraints']=actual;case('constraint_denominator',len(actual)==len(source),dict(expected=len(source),observed=len(actual)),'CONSTRAINT_TRIGGER');bykey={(x['relation'],x['name']):x for x in actual}
 kinds={'CONSTR_PRIMARY':'p','CONSTR_UNIQUE':'u','CONSTR_FOREIGN':'f','CONSTR_CHECK':'c','CONSTR_EXCLUSION':'x','CONSTR_NOTNULL':'n'}
 for item in source:
  con=item['source'];table=item['relation'];a=bykey.get((table,con['conname']),{});kind=con['contype'];want=dict(relation=table,name=con['conname'],type=kinds[kind],validated=True,enforced=True,deferrable=bool(con.get('deferrable')),deferred=bool(con.get('initdeferred')))
  if kind in ['CONSTR_PRIMARY','CONSTR_UNIQUE','CONSTR_NOTNULL']:want['keys']=[columns[table,key['String']['sval']]['attnum'] for key in con['keys']]
  if kind in ['CONSTR_PRIMARY','CONSTR_UNIQUE']:want['index']=con.get('indexname') or con['conname']
  if kind=='CONSTR_FOREIGN':
   parent=con['pktable'].get('schemaname','public')+'.'+con['pktable']['relname'];pk=[key['String']['sval'] for key in con.get('pk_attrs',[])];eligible=[i for i in indexes if i['relation']==parent and i['unique'] and (not pk or i['keys']==pk)];q.require(len(eligible)==1,'Parent unique index not independent/unique');pk=eligible[0]['keys'];want.update(keys=[columns[table,key['String']['sval']]['attnum'] for key in con['fk_attrs']],parent=parent,parent_keys=[columns[parent,key]['attnum'] for key in pk],match=con.get('fk_matchtype','s'),update=con.get('fk_upd_action','a'),delete=con.get('fk_del_action','a'),index=eligible[0]['name'])
  mismatches={k:[v,a.get(k)] for k,v in want.items() if a.get(k)!=v};case('constraint_'+table+'.'+con['conname'],not mismatches,mismatches,'CONSTRAINT_TRIGGER')
  if kind=='CONSTR_CHECK':
   r.locals={c['name']:c['type'] for c in cols if c['relation']==table};r.context={};expected_expr=normalize(r,con['raw_expr']);actual_expr=normalize(r,parse_expression(r,a['expression']));case('constraint_expression_'+table+'.'+con['conname'],expected_expr==actual_expr,dict(expected=expected_expr,observed=actual_expr),'CONSTRAINT_TRIGGER')
 # Index identities include constraint and native bootstrap indexes. Catalog
 # primary promotion is represented by system_constraints.sql, never guessed.
 actual=last(sql("SELECT jsonb_agg(jsonb_build_object('relation',n.nspname||'.'||t.relname,'name',ix.relname,'owner',pg_get_userbyid(ix.relowner),'method',am.amname,'unique',i.indisunique,'primary',i.indisprimary,'valid',i.indisvalid,'ready',i.indisready,'live',i.indislive,'nulls_not_distinct',i.indnullsnotdistinct,'keys',(SELECT array_agg(a.attname::text ORDER BY k.ord) FROM unnest(i.indkey) WITH ORDINALITY k(num,ord) JOIN pg_attribute a ON a.attrelid=t.oid AND a.attnum=k.num),'opclasses',(SELECT array_agg(op.opcname::text ORDER BY k.ord) FROM unnest(i.indclass) WITH ORDINALITY k(oid,ord) JOIN pg_opclass op ON op.oid=k.oid),'options',i.indoption::text,'predicate',pg_get_expr(i.indpred,i.indrelid)) ORDER BY n.nspname,t.relname,ix.relname) FROM pg_index i JOIN pg_class t ON t.oid=i.indrelid JOIN pg_namespace n ON n.oid=t.relnamespace JOIN pg_class ix ON ix.oid=i.indexrelid JOIN pg_am am ON am.oid=ix.relam WHERE i.indrelid IN ("+objects+");"));observed['indexes']=actual;case('index_denominator',len(actual)==len(indexes),dict(expected=len(indexes),observed=len(actual)),'PLANNER_SUPPORT');keyed={(x['relation'],x['name']):x for x in actual};owners={x['name']:x['owner'] for x in json.loads((OUT/'relation-view-v2.json').read_text())['relations']}
 for x in indexes:
  a=keyed.get((x['relation'],x['name']),{});opclasses=[]
  for key in x['keys']:
   typ=columns[x['relation'],key]['type'];choices=[p for p in r.rows['pg_opclass'] if p['opcmethod']=='403' and p['opcdefault']=='t' and p['opcintype']==r.types[typ]['oid']];q.require(len(choices)==1,'Default opclass ambiguity');opclasses.append(choices[0]['opcname'])
  want={k:x[k] for k in ['relation','name','keys','method','unique','primary','nulls_not_distinct']};want.update(owner=owners[x['relation']],valid=True,ready=True,live=True,opclasses=opclasses,options=' '.join('0' for _ in x['keys']));mismatch={k:[v,a.get(k)] for k,v in want.items() if a.get(k)!=v};case('index_'+x['relation']+'.'+x['name'],not mismatch,mismatch,'PLANNER_SUPPORT')
  if x['predicate'] is not None:
   r.locals={c['name']:c['type'] for c in cols if c['relation']==x['relation']};r.context={};want=normalize(r,x['predicate']);got=normalize(r,parse_expression(r,a['predicate']));case('index_predicate_'+x['name'],want==got,dict(expected=want,observed=got),'PLANNER_SUPPORT')
  else:case('index_no_predicate_'+x['name'],a['predicate'] is None,a.get('predicate'),'PLANNER_SUPPORT')
 actual=last(sql("SELECT COALESCE(jsonb_agg(jsonb_build_object('relation',n.nspname||'.'||t.relname,'name',tr.tgname,'internal',tr.tgisinternal,'type',tr.tgtype,'enabled',tr.tgenabled,'function',pn.nspname||'.'||p.proname,'constraint',co.conname,'constraint_relation',CASE WHEN co.oid IS NULL THEN NULL ELSE cn.nspname||'.'||ct.relname END,'deferrable',tr.tgdeferrable,'deferred',tr.tginitdeferred,'when',pg_get_expr(tr.tgqual,tr.tgrelid),'old_table',tr.tgoldtable,'new_table',tr.tgnewtable,'nargs',tr.tgnargs,'columns',tr.tgattr::text) ORDER BY t.oid,tr.tgname),'[]'::jsonb) FROM pg_trigger tr JOIN pg_class t ON t.oid=tr.tgrelid JOIN pg_namespace n ON n.oid=t.relnamespace JOIN pg_proc p ON p.oid=tr.tgfoid JOIN pg_namespace pn ON pn.oid=p.pronamespace LEFT JOIN pg_constraint co ON co.oid=tr.tgconstraint LEFT JOIN pg_class ct ON ct.oid=co.conrelid LEFT JOIN pg_namespace cn ON cn.oid=ct.relnamespace WHERE tr.tgrelid IN ("+objects+");"));observed['triggers']=actual;expected_triggers=json.loads((OUT/'trigger-v2.json').read_text());fks=[x for x in source if x['source']['contype']=='CONSTR_FOREIGN'];case('trigger_denominator',len(actual)==len(expected_triggers['triggers'])+4*len(fks),dict(expected=len(expected_triggers['triggers'])+4*len(fks),observed=len(actual)),'CONSTRAINT_TRIGGER')
 for item in expected_triggers['triggers']:
  x=item['source'];found=[a for a in actual if a['relation']==item['relation'] and a['name']==x['trigname']];want=dict(internal=False,type=x['timing']+x['events']+(1 if x.get('row') else 0),enabled='O',function='.'.join(v['String']['sval'] for v in x['funcname']),deferrable=False,deferred=False,when=None,old_table=None,new_table=None,nargs=0,columns='');a=found[0] if len(found)==1 else {};mismatch={k:[v,a.get(k)] for k,v in want.items() if a.get(k)!=v};case('trigger_'+x['trigname'],len(found)==1 and not mismatch,mismatch,'CONSTRAINT_TRIGGER')
 for fk in fks:
  c=fk['source'];found=[a for a in actual if a['internal'] and a['constraint']==c['conname'] and a['constraint_relation']==fk['relation']];want_functions={'pg_catalog.RI_FKey_check_ins':5,'pg_catalog.RI_FKey_check_upd':17,'pg_catalog.RI_FKey_noaction_del':9,'pg_catalog.RI_FKey_noaction_upd':17};case('RI_trigger_set_'+c['conname'],len(found)==4 and {a['function'] for a in found}==set(want_functions),found,'CONSTRAINT_TRIGGER')
  for a in found:
   passed=a['type']==want_functions[a['function']] and a['enabled']=='O' and a['deferrable']==bool(c.get('deferrable')) and a['deferred']==bool(c.get('initdeferred')) and a['when'] is None and a['nargs']==0 and a['old_table'] is None and a['new_table'] is None and a['columns']=='' and re.fullmatch(r'RI_ConstraintTrigger_[ac]_\d+',a['name']) is not None;case('RI_trigger_'+c['conname']+'_'+a['function'],passed,a,'CONSTRAINT_TRIGGER')
 # Adding a descendant would change non-ONLY SELECT semantics; source/factory
 # says there are no inheritance or partition edges for these exact roots.
 inh=sql('SELECT count(*) FROM pg_inherits WHERE inhrelid IN ('+objects+') OR inhparent IN ('+objects+');').stdout.strip();case('inheritance_graph_empty',inh==b'0',inh.decode(),'RELATION_VIEW')
 (folder/'integrity-runtime.json').write_text(json.dumps(dict(cases=cases,observed=observed),indent=2)+'\n')
