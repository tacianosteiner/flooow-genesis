"""Independent catalog resolution/planner surface and its corroboration."""
import json
from pathlib import Path
import package_0090_source_closure as q
from package_0090_reachable_v2 import OUT,save

def prepare(r):
 candidates=json.loads((OUT/'resolution-candidate-metadata.json').read_text());families=json.loads((OUT/'planner-support-v2.json').read_text())['btree_families'];observer=json.loads((OUT/'observer-provider-v2.json').read_text())
 tables={
 'pg_operator':dict(rows=candidates['operators'],where="oprnamespace=11 AND oprname IN ("+','.join("'"+s.replace("'","''")+"'" for s in sorted({x['oprname'] for x in candidates['operators']}))+')'),
 'pg_cast':dict(rows=r.rows['pg_cast'],where='true'),
 'pg_opfamily':dict(rows=[x for x in r.rows['pg_opfamily'] if x['oid'] in families],where='oid IN ('+','.join(families)+')'),
 'pg_opclass':dict(rows=[x for x in r.rows['pg_opclass'] if x['opcfamily'] in families],where='opcfamily IN ('+','.join(families)+')'),
 'pg_amop':dict(rows=[x for x in r.rows['pg_amop'] if x['amopfamily'] in families],where='amopfamily IN ('+','.join(families)+')'),
 'pg_amproc':dict(rows=[x for x in r.rows['pg_amproc'] if x['amprocfamily'] in families],where='amprocfamily IN ('+','.join(families)+')'),
 'pg_am':dict(rows=[x for x in r.rows['pg_am'] if x['amname'] in ['heap','btree']],where="amname IN ('heap','btree')"),
 'pg_aggregate':dict(rows=observer['aggregates'],where='aggfnoid IN ('+','.join(x['aggfnoid'] for x in observer['aggregates'])+')')}
 for name,entry in tables.items():entry['fields']=[x for x in r.defs[name] if x['name'] in entry['rows'][0]]
 save('catalog-resolution-surface-v2.json',dict(tables=tables,independent=True,scope='Complete operator candidate signatures and cast surface; reachable default btree families/access methods; selected qualification observer aggregates. Nonselected operator bodies are unreachable under frozen typed resolution, not silently executed.'))

def qualify(sql,run,container,folder,record,fixture,runtime_work):
 record['recipe_hashes'][Path(__file__).name]=q.sha(Path(__file__).read_bytes());cases=[];observed={}
 def case(name,passed,details):
  c=dict(name=name,passed=bool(passed),details=details,group='PLANNER_SUPPORT');cases.append(c);record['cases'].append(c)
  (folder/'catalog-surface-runtime.json').write_text(json.dumps(dict(cases=cases,observed=observed),indent=2)+'\n');q.require(passed,name)
 model=json.loads((OUT/'catalog-resolution-surface-v2.json').read_text())
 for table,entry in model['tables'].items():
  parts=[]
  for field in entry['fields']:
   name=field['name'];cast='::oid' if field['type'] in ['regproc','regprocedure','regoper','regoperator','regclass','regtype'] else ''
   parts.extend(["'"+name+"'",'c.'+name+cast+'::text'])
  actual=json.loads(sql('SELECT COALESCE(jsonb_agg(jsonb_build_object('+','.join(parts)+")),'[]'::jsonb) FROM pg_catalog."+table+' c WHERE '+entry['where']+';').stdout)
  observed[table]=actual;case(table+'_denominator',len(actual)==len(entry['rows']),dict(expected=len(entry['rows']),observed=len(actual)))
  keyfields=['oid'] if 'oid' in entry['rows'][0] else ['aggfnoid']
  keyed={tuple(x[k] for k in keyfields):x for x in actual}
  for row in entry['rows']:
   want={f['name']:(None if row[f['name']]=='_null_' else 'true' if row[f['name']]=='t' and f['type']=='bool' else 'false' if row[f['name']]=='f' and f['type']=='bool' else '0' if row[f['name']]=='-' and f['type'].startswith('reg') else row[f['name']]) for f in entry['fields']};a=keyed.get(tuple(row[k] for k in keyfields),{});mismatch={k:[v,a.get(k)] for k,v in want.items() if a.get(k)!=v};case(table+'_'+'_'.join(row[k] for k in keyfields),not mismatch,mismatch)
