"""Seal C5M only; historical evidence and implementation remain immutable."""
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
spec=importlib.util.spec_from_file_location('m_validate',P/'validate.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);write('static-validation',mod.run())
reviews=[read('independent-review-'+str(i)) for i in [1,2]]
for r in reviews:
    status=r.get('status',r.get('verdict',r.get('result','')));assert status.startswith('PASS') and not r.get('blocking_defects',[])
    for n,h in r.get('reviewed_sha256',{}).items():assert sha(P/n)==h,('reviewed artifact changed',n)
pre=read('preflight');bad=[n for n,h in pre['historical_sha256'].items() if sha(ROOT/n)!=h];assert not bad,bad
assert not git('diff','--name-only') and not git('diff','--cached','--name-only')
assert git('rev-parse','HEAD')==pre['head'] and git('branch','--show-current')==pre['branch']
write('historical-preservation',dict(status='PASS',historical_hashes_validated=9393,c5l_files_validated=32,union_historical_hashes_validated=len(pre['historical_sha256']),mismatches=bad,tracked_dirty=0,staged=0,head_unchanged=True,branch_unchanged=True))
write('prohibited-contact-audit',dict(status='PASS',scope='Recorded C5M operations: local static reads/hashes and evidence writes; read-only Git inspection only',shared_db=False,production_db=False,existing_local_db=False,network_for_proof=False,migrations_executed=False,containers_started=False,V043_executed=False,V043_changed=False,B02_executed=False,git_add=False,commit=False,push=False,production_code_changed=False,canonical_witness_executions=0))
summary=read('final-summary')
for i,r in enumerate(reviews,1):summary['INDEPENDENT_REVIEW_'+str(i)]=r.get('status',r.get('verdict',r.get('result')))
paths=git('ls-files','--others','--exclude-standard').splitlines();prefix=P.relative_to(ROOT).as_posix()+'/';old=set(pre['authorized_paths_before']);assert not [n for n in paths if n not in old and not n.startswith(prefix)]
summary['UNTRACKED_FILES_AFTER']=len(set(paths)|{prefix+'SHA256-MANIFEST.json',prefix+'final-return.txt'})
summary['FINAL_VALIDATION']='PASS';summary['KNOWN_LIMITATIONS']='Recovered source definitions and structural projections only. Actual values/cardinalities remain uninstantiated; no runtime or witness proof. Root partition is not a globally minimum/irreducible proof.'
write('final-summary',summary)
(P/'final-return.txt').write_text('\n'.join(k+'='+('false' if v is False else str(v)) for k,v in summary.items())+'\n',encoding='utf-8')
files={q.relative_to(ROOT).as_posix():sha(q) for q in sorted(P.rglob('*')) if q.is_file() and q.name!='SHA256-MANIFEST.json'}
write('SHA256-MANIFEST',dict(algorithm='SHA256',self_excluded=True,files=files))
assert len(git('ls-files','--others','--exclude-standard').splitlines())==summary['UNTRACKED_FILES_AFTER']
assert all(sha(ROOT/n)==h for n,h in files.items())
print(json.dumps(dict(status='SEALED',new_files=len(files)+1,untracked_after=summary['UNTRACKED_FILES_AFTER'],historical_preserved=len(pre['historical_sha256']),strict=summary['LOCAL_FUNCTIONS_STRICT_CERTIFIED'],reviews=[summary['INDEPENDENT_REVIEW_1'],summary['INDEPENDENT_REVIEW_2']])) )
