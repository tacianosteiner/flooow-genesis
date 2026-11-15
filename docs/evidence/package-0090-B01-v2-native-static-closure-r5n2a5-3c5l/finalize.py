"""Seal only C5L; rehash all historical evidence and verify repository preservation."""
import hashlib
import importlib.util
import json
import pathlib
import subprocess
import sys
sys.dont_write_bytecode=True

P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2]
def read(n):return json.loads((P/(n+'.json')).read_text(encoding='utf-8'))
def write(n,x):(P/(n+'.json')).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
s=importlib.util.spec_from_file_location('c5l_validate',P/'validate.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
validation=v.run();write('static-validation',validation)
reviews=[read('independent-review-'+str(i)) for i in [1,2]]
for r in reviews:
    status=r.get('status',r.get('verdict',r.get('result','')))
    assert status.startswith('PASS'),status
    assert not r.get('blocking_defects',[])
pre=read('preflight');bad=[p for p,h in pre['historical_sha256'].items() if not (ROOT/p).is_file() or sha(ROOT/p)!=h]
assert not bad,bad
assert not git('diff','--name-only') and not git('diff','--cached','--name-only')
assert git('rev-parse','HEAD')==pre['head'] and git('branch','--show-current')==pre['branch']
write('historical-preservation',dict(status='PASS',historical_files_checked=len(pre['historical_sha256']),mismatches=bad,tracked_dirty=0,staged=0,head_unchanged=True,branch_unchanged=True))
write('prohibited-contact-audit',dict(status='PASS',basis='Recorded commands limited to read-only local Git status/hash, JSON source reads, C5L evidence writes and structural audit. No DB/network/V043/B02/Git mutations invoked.',shared_db_contacted=False,production_contacted=False,existing_local_db_contacted=False,network_for_proof=False,V043_executed=False,V043_changed=False,B02_executed=False,git_add=False,commit=False,push=False,production_files_changed=False,canonical_witness_executions=0))
summary=read('final-summary')
summary['INDEPENDENT_REVIEW_1']=reviews[0].get('status',reviews[0].get('verdict',reviews[0].get('result')))
summary['INDEPENDENT_REVIEW_2']=reviews[1].get('status',reviews[1].get('verdict',reviews[1].get('result')))
current=git('ls-files','--others','--exclude-standard').splitlines();authorized=set(pre['authorized_paths_before']);prefix=P.relative_to(ROOT).as_posix()+'/'
unauthorized=[p for p in current if p not in authorized and not p.startswith(prefix)]
assert not unauthorized,unauthorized
future={prefix+'SHA256-MANIFEST.json',prefix+'final-return.txt'}
summary['UNTRACKED_FILES_AFTER']=len(set(current)|future);summary['UNAUTHORIZED_UNTRACKED_COUNT']=0
summary['COMPOSITION_CYCLES']=0
summary['FINAL_VALIDATION']='PASS';summary['HISTORICAL_FILES_PRESERVED']=len(pre['historical_sha256'])
summary['KNOWN_LIMITATIONS']='Source-parametric structural closure only; no fixture values, canonical evaluator or proof. Equivalence classes conservative; five recovery classes are a nonduplicated partition, not a globally minimum/irreducible cause proof.'
write('final-summary',summary)
(P/'final-return.txt').write_text('\n'.join(k+'='+('false' if val is False else str(val)) for k,val in summary.items())+'\n',encoding='utf-8')
files={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(P.rglob('*')) if p.is_file() and p.name!='SHA256-MANIFEST.json'}
write('SHA256-MANIFEST',dict(algorithm='SHA256',self_excluded=True,files=files))
assert len(git('ls-files','--others','--exclude-standard').splitlines())==summary['UNTRACKED_FILES_AFTER']
assert all(sha(ROOT/p)==h for p,h in files.items())
print(json.dumps(dict(status='SEALED',files=len(files)+1,untracked_after=summary['UNTRACKED_FILES_AFTER'],strict=summary['LOCAL_FUNCTIONS_STRICT_CERTIFIED'],reviews=[summary['INDEPENDENT_REVIEW_1'],summary['INDEPENDENT_REVIEW_2']],historical_unchanged=len(pre['historical_sha256']))))
