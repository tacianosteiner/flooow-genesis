"""Source-factory TOAST dependencies, without predicting assigned OIDs."""
import json,re
import package_0090_source_closure as q
from package_0090_reachable_v2 import OUT,save

def prepare(r):
 relations=json.loads((OUT/'relation-view-v2.json').read_text())['relations'];columns=json.loads((OUT/'column-v2.json').read_text())['columns'];bki=(OUT/'provider/postgres.bki').read_text();parents=[]
 for rel in relations:
  name=rel['name'];required=False;rule='View/fixed-width root has no TOAST relation'
  if name.startswith('pg_catalog.'):
   required=re.search(r'declare toast \d+ \d+ on '+re.escape(name.split('.')[-1])+r'\b',bki) is not None;rule='Exact BKI declare-toast directive, not a user-table heuristic'
  elif rel['kind']=='r':
   cols=[c for c in columns if c['relation']==name];unbounded=any(r.types[c['type']]['typlen']=='-1' and r.types[c['type']]['typstorage']!='p' and c['typmod']==-1 for c in cols);long_varchar=any(c['type']in ['varchar','bpchar'] and c['typmod']>0 and 4+(c['typmod']-4)*4>2032 for c in cols);required=unbounded or long_varchar;rule='PG heap needs_toast_table: unbounded toastable attribute or UTF8 varchar maximum already exceeds tuple threshold; all other root columns fixed-width'
  parents.append(dict(parent=name,required=required,owner=rel['owner'],rule=rule))
 save('storage-dependency-v2.json',dict(parents=parents,toast_tables=sum(x['required'] for x in parents),dynamic_binding='parent.pg_class.reltoastrelid; toast name pg_toast_<parent_oid>, index pg_toast_<parent_oid>_index; bind generated IDs through the parent, never predict them',toast_columns=[dict(name='chunk_id',type='oid'),dict(name='chunk_seq',type='int4'),dict(name='chunk_data',type='bytea')],factory_flags=dict(kind='t',namespace='pg_toast',RLS=False,persistence='p',rowtype_oid=0,recursive_toast_oid=0,attnotnull=False,attstorage='p',attcompression='',index_unique=True,index_primary=True,index_method='btree',index_options='0 0',index_opclasses=['oid_ops','int4_ops']),independent=True,source='REL_18_4 toasting.c, BKI declare-toast and heap factory sizing; no SQL-visible new authority'))
 print('TOAST roots',sum(x['required'] for x in parents))
if __name__=='__main__':
 import sys
 from pathlib import Path
 sys.path.insert(0,str(Path.home()/'.codex/tmp/package0090-pglast-8.5'));from pglast.parser import parse_sql_json
 import package_0090_reachable_v2 as e
 prepare(e.Resolver(parse_sql_json))
