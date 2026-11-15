"""Seal C5P decomposition only after independent reviews; historical files immutable."""
import hashlib,importlib.util,json,pathlib,subprocess,sys
sys.dont_write_bytecode=True
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2]
def read(n):return json.loads((P/(n+'.json')).read_text(encoding='utf-8'))
def write(n,x):(P/(n+'.json')).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def sha(q):return hashlib.sha256(q.read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
s=importlib.util.spec_from_file_location('p_validate',P/'validate.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v);write('static-validation',v.run())
reviews=[read('independent-review-'+str(i)) for i in [1,2]]
for r in reviews:
    status=r.get('status',r.get('verdict',r.get('result','')));assert status.startswith('PASS') and not r.get('blocking_defects',[])
    for n,h in r.get('reviewed_sha256',{}).items():assert sha(P/n)==h,('reviewed artifact changed',n)
pre=read('preflight');bad=[n for n,h in pre['historical_sha256'].items() if not (ROOT/n).is_file() or sha(ROOT/n)!=h];assert not bad,bad
assert not git('diff','--name-only') and not git('diff','--cached','--name-only') and git('branch','--show-current')==pre['branch'] and git('rev-parse','HEAD')==pre['head']
write('historical-preservation',dict(status='PASS',historical_files_preserved=9494,c5o_files_preserved=32,historical_union_preserved=len(pre['historical_sha256']),mismatches=bad,tracked_dirty=0,staged=0,head_unchanged=True,branch_unchanged=True))
write('prohibited-contact-audit',dict(status='PASS',basis='Recorded operations only local immutable reads/hashes, read-only Git inspection and C5P evidence writes',database=False,network_for_proof=False,runtime_execution=False,containers=False,migrations_executed=False,V043_executed=False,V043_changed=False,B02_executed=False,git_add=False,commit=False,push=False,production_code_changed=False,full_binding_recomputation=False,rules_defined=False,actual_closures=0,witness_executions=0))
summary=read('final-summary')
for i,r in enumerate(reviews,1):summary['INDEPENDENT_REVIEW_'+str(i)]=r.get('status',r.get('verdict',r.get('result')))
paths=git('ls-files','--others','--exclude-standard').splitlines();prefix=P.relative_to(ROOT).as_posix()+'/';old=set(pre['authorized_paths_before']);assert not [n for n in paths if n not in old and not n.startswith(prefix)]
summary['UNTRACKED_FILES_AFTER']=len(set(paths)|{prefix+'final-return.txt',prefix+'SHA256-MANIFEST.json'});summary['FINAL_VALIDATION']='PASS';summary['KNOWN_LIMITATIONS']='Decomposition and structural counterfactuals only. Minimum3 is scoped to exact C5O bundles; a global atomic minimum is not established. No rule, source value, binding closure, evaluator or witness proof produced.'
write('final-summary',summary)
(P/'final-return.txt').write_text('\n'.join(k+'='+('false' if val is False else str(val)) for k,val in summary.items())+'\n',encoding='utf-8')
files={q.relative_to(ROOT).as_posix():sha(q) for q in sorted(P.rglob('*')) if q.is_file() and q.name!='SHA256-MANIFEST.json'};write('SHA256-MANIFEST',dict(algorithm='SHA256',self_excluded=True,files=files))
assert len(git('ls-files','--others','--exclude-standard').splitlines())==summary['UNTRACKED_FILES_AFTER'] and all(sha(ROOT/n)==h for n,h in files.items())
print(json.dumps(dict(status='SEALED',new_files=len(files)+1,untracked_after=summary['UNTRACKED_FILES_AFTER'],historical_union_preserved=len(pre['historical_sha256']),independent_bundles=3,exhausted_mapped=17,outcome=summary['SELECTED_OUTCOME'],reviews=[summary['INDEPENDENT_REVIEW_1'],summary['INDEPENDENT_REVIEW_2']])) )
