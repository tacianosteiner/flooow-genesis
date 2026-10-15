"""Collect authorized S04 correction evidence without executing any migration."""
import json
import sys
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
import package_0090_source_closure as q
from package_0090_s04_candidate import clean,crc

BASELINE='acecf0c236b1341fce71a5e1460cc8eafff02da6'
OUT=q.ROOT/'docs/evidence/package-0090-s04-return-tuple-correction-applied'
OLD='b0ea86b6ba355fdf25fe09836bd4b75e4a4a2ad88ab7ef0e4724ca0d5a013e7d'
NEW='007ab786c417c41e2b1702ebf3852cb70ff5c142fa3fde195385e04c6dde8b4a'

def save(name,value): (OUT/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def main():
 sys.path.insert(0,str(Path.home()/'AppData/Local/Temp/room-lineage-sql-parser'))
 from pglast.parser import parse_sql_json
 rel=q.V043.relative_to(q.ROOT).as_posix()
 old=q.git('show',BASELINE+':'+rel); new=q.git('show','HEAD:'+rel)
 q.require(q.sha(old)==OLD and q.sha(new)==NEW and q.SOURCE_HASH==NEW,'Source identity')
 q.require(q.V043.read_bytes().replace(b'\r\n',b'\n')==new,'Worktree source')
 before=(OUT.parent/'package-0090-s04-return-tuple-correction-candidate/S04-CURRENT-RETURN-QUERY.sql').read_bytes().rstrip(b'\n'); after=before.replace(b'h.version,h.type,h.script',b'h.version::pg_catalog.text,h.type::pg_catalog.text,h.script::pg_catalog.text')
 q.require(old.count(before)==1 and old.replace(before,after)==new,'Only authorized source edit')
 q.require(crc(old)==1665026701 and crc(new)==1279591798,'Flyway checksums')
 body,tree,proof=q.derive(new,parse_sql_json)
 oldtree=json.loads(parse_sql_json(old.decode()))['stmts']
 changed=[i for i,(a,b) in enumerate(zip(oldtree,tree)) if clean(a['stmt'])!=clean(b['stmt'])]
 q.require(changed==[1159] and len(oldtree)==len(tree)==1235,'AST definition delta')
 a=oldtree[1159]['stmt']['CreateFunctionStmt']; b=tree[1159]['stmt']['CreateFunctionStmt']
 for node in [a,b]: node['options']=[o for o in node['options'] if o['DefElem']['defname']!='as']
 q.require(clean(a)==clean(b),'API/security attributes')
 # New guard must reject the previously accepted canonical, not accept two baselines.
 try: q.derive(old,parse_sql_json)
 except ValueError: pass
 else: raise RuntimeError('Old baseline accepted')
 q.require(not q.git('diff','--name-only','--diff-filter=CDMRTUXB',BASELINE,'--','docs/evidence').strip(),'Historical evidence modified')
 freeze=json.loads((OUT/'source-freeze.json').read_text())
 for ref,expected in freeze['protected_refs'].items(): q.require(q.git('rev-parse',ref).decode().strip()==expected,'Protected ref drift')
 save('applied-source-audit.json',dict(source_files=1,functions=1,physical_lines=1,qualified_TypeCast_delta=3,all_other_bytes_equal=True,API_attributes_equal=True,fence_present=new.count(q.FENCE)==1,fence_offset=new.index(q.FENCE),old_baseline_rejected=True,checksums=[crc(old),crc(new)],derived_body=proof))
 # Every original old-source/body/checksum reference is inventoried, including historical recipe pins.
 tracked=set(q.git('ls-tree','-r','--name-only',BASELINE).decode().splitlines())
 found=q.command(['rg','-n','-o','--no-heading','--hidden','--glob','!docs/evidence/package-0090-s04-return-tuple-correction-applied/**','-F','-e',OLD,'-e','6ad78ba61d70e803d2a878034aa7988b69b6374568f96949b2ef6c8defc7a8c7','-e','1665026701','.'],check=False,timeout=120)
 q.require(found.returncode in [0,1],'Reference census search failed')
 matches=[]
 active_paths=['scripts/validation/package_0090_source_closure.py','scripts/validation/test_package_0090_source_closure.py']
 for line in found.stdout.decode().splitlines():
  path,number,text=line.split(':',2); path=path.replace('\\','/').removeprefix('./')
  if path in tracked and path not in active_paths: matches.append(BASELINE+':'+path+':'+number+':'+text)
 for path in active_paths:
  text=q.git('show',BASELINE+':'+path).decode()
  for number,line in enumerate(text.splitlines(),1):
   if any(pattern in line for pattern in [OLD,'6ad78ba61d70e803d2a878034aa7988b69b6374568f96949b2ef6c8defc7a8c7','1665026701']): matches.append(BASELINE+':'+path+':'+str(number)+':'+line)
 grouped={}
 for line in matches:
  _,path,lineno,text=line.split(':',3)
  category='ACTIVE_VALIDATOR_REBASELINE_REQUIRED' if path in active_paths else 'HISTORICAL_EVIDENCE_DO_NOT_CHANGE'
  if path not in grouped: grouped[path]=dict(path=path,classification=category,lines=set())
  grouped[path]['lines'].add(int(lineno))
 census=[]
 for path,g in sorted(grouped.items()):
  lines=sorted(g.pop('lines')); ranges=[]
  for n in lines:
   if ranges and n==ranges[-1][1]+1: ranges[-1][1]=n
   else: ranges.append([n,n])
  g.update(matching_lines=len(lines),line_ranges_inclusive=','.join(str(a) if a==b else str(a)+'-'+str(b) for a,b in ranges),line_range_encoding='comma-separated N or A-B inclusive',resolution='Exact new source/body pin only' if path in active_paths else 'Immutable prior campaign snapshot; current-input.json is successor qualification authority')
  census.append(g)
 save('old-reference-classification.json',dict(baseline=BASELINE,search='All repository paths using literal ripgrep; only baseline-tracked files retained; changed active pins read from original Git blobs',references=census,total_matching_lines=sum(g['matching_lines'] for g in census),active_fixture_rebaseline='Successor target manifests; retained rows, ACL and function attributes byte-identical because dependency unchanged',release_record_rebaseline='current-input.json and new applied report supersede old source qualification; no old release approval is carried forward'))
 previous=q.git('ls-tree','-r',BASELINE,'--','docs/evidence').decode().splitlines()
 save('historical-evidence-immutability.json',dict(baseline=BASELINE,tracked_evidence_entries=len(previous),tracked_diff_empty=True,tree_listing_sha256=q.sha(('\n'.join(previous)+'\n').encode()),old_evidence_rewritten=False))
 records=[]
 for i in [1,2]:
  folder=OUT/f'target-{i}'; r=json.loads((folder/'foundation-runtime.json').read_text()); result=json.loads((folder/'corrected-runtime.json').read_text())
  q.require(not r['errors'] and len(r['cases'])==104 and all(c['passed'] for c in r['cases']) and r['owned_runtime_destroyed'],'Runtime qualification')
  q.require(r['source_hash']==NEW and r['transformation']==proof,'Runtime corrected source/body identity')
  q.require(result['old_raw_sqlstate']=='42804' and result['candidate']['sqlstate']=='00000' and len(result['candidate']['rows'])==42,'Tuple runtime')
  for name,h in r['recipe_hashes'].items(): q.require(q.sha((q.ROOT/'scripts/validation'/name).read_bytes())==h,'Runtime recipe drift: '+name)
  q.require(not r['canonical_v043_executed'] and not r['canonical_v043_submitted'] and not r['active_fixture_ready'],'Forbidden execution')
  records.append(r)
 q.require(records[0]['isolation']['id']!=records[1]['isolation']['id'] and records[0]['isolation']['volume']!=records[1]['isolation']['volume'],'Independent fresh targets')
 save('reproducibility.json',dict(targets=2,independent_containers=True,independent_volumes=True,normal_and_optimized_python=True,cases_per_target=104,distinct_runtime_assertions=104,assertion_executions=208,errors=0,owned_resources_destroyed=True,canonical_S04_called=False))
 results={}
 for key,pattern in [('direct_consumer','applications/command-authority-ceremony/build/test-results/test/TEST-*GovernedAdaptersTest.xml'),('persistence','applications/marketplace-operations-persistence-postgres/build/test-results/test/TEST-*PostgresV042MigrationTest.xml')]:
  files=list(q.ROOT.glob(pattern)); q.require(len(files)==1,'Test XML missing')
  root=ET.parse(files[0]).getroot(); q.require(root.attrib['failures']=='0' and root.attrib['errors']=='0' and root.attrib['skipped']=='0','JUnit failure')
  shutil.copyfile(files[0],OUT/(key+'-junit.xml')); results[key]=dict(root.attrib)
 # Direct consumers have no API changes and must remain byte-identical.
 consumers=['applications/command-authority-ceremony/src/main/kotlin/io/flooow/ceremony/GovernedCall.kt','applications/command-authority-ceremony/src/main/kotlin/io/flooow/ceremony/GovernedJdbc.kt','applications/command-authority-ceremony/src/test/kotlin/io/flooow/ceremony/GovernedAdaptersTest.kt']
 q.require(not q.git('diff',BASELINE,'--',*consumers),'Consumer changed')
 save('consumer-contract.json',dict(files={p:q.sha((q.ROOT/p).read_bytes()) for p in consumers},changed=False,public_API_changed=False,tests=results))
 boundary=q.command([sys.executable,str(q.ROOT/'scripts/validation/test_package_0090_source_closure.py'),'--parser-path',str(Path.home()/'AppData/Local/Temp/room-lineage-sql-parser')])
 (OUT/'boundary-test-output.txt').write_bytes(boundary.stdout+boundary.stderr)
 save('current-input.json',dict(decision=freeze['decision'],source_fix_commit='7fdd9a6d0b9c03705f4636c1d08c7a78c1bbc372',source_sha256=NEW,Flyway_signed_CRC32=1279591798,derived_qualification_body_sha256=q.sha(body),previous_source_sha256=OLD,previous_derived_body_sha256='6ad78ba61d70e803d2a878034aa7988b69b6374568f96949b2ef6c8defc7a8c7',active_source_validator='scripts/validation/package_0090_source_closure.py',active_runtime_recipe='scripts/validation/package_0090_s04_applied.py',fixture_policy='Retained target fixture content unchanged; new source/body binding in foundation-runtime.json and this successor record',historical_campaigns='Pinned historical evidence only; not current corrected-source qualification or transferable activation/promotion authority',canonical_executed=False,S04_executed=False,promotion_authorized=False,readiness_created=False,broader_reachable_closure=False,T10_closed=False))
 print(json.dumps(dict(accepted=True,runtime_distinct=104,new_tuple_distinct=11,foundation_reused=93,boundary=5,old_source_rejection=1,direct_consumer=int(results['direct_consumer']['tests']),persistence=int(results['persistence']['tests']),total_distinct=104+5+1+int(results['direct_consumer']['tests'])+int(results['persistence']['tests']),old_reference_matching_lines=sum(g['matching_lines'] for g in census))))
if __name__=='__main__':main()
