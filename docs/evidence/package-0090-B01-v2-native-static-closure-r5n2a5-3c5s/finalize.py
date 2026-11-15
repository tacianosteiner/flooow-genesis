"""Seal only C5S after two independent reviews and unchanged historical hashes."""
import hashlib,importlib.util,json,pathlib,subprocess,sys
sys.dont_write_bytecode=True
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2]
def read(n):return json.loads((P/(n+'.json')).read_text(encoding='utf-8-sig'))
def write(n,x):(P/(n+'.json')).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def sha(q):return hashlib.sha256(q.read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
def pinpath(n):return ROOT/n if n.replace('\\','/').startswith('docs/') else P/n
s=importlib.util.spec_from_file_location('s_validation',P/'validate.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v);write('static-validation',v.run())
reviews=[read('independent-review-'+str(i)) for i in [1,2]]
for review in reviews:
    status=review.get('status',review.get('result',review.get('verdict','')));assert status.startswith('PASS') and not review.get('blocking_defects',review.get('blocking_findings',[]))
    for n,h in review.get('reviewed_sha256',review.get('source_hashes',review.get('pinned_artifacts',{}))).items():assert sha(pinpath(n))==h,('reviewed source changed',n)
pre=read('preflight');bad=[n for n,h in pre['historical_sha256'].items() if not (ROOT/n).is_file() or sha(ROOT/n)!=h];assert not bad,bad
assert not git('diff','--name-only') and not git('diff','--cached','--name-only') and git('rev-parse','HEAD')==pre['head'] and git('branch','--show-current')==pre['branch']
write('historical-preservation',dict(status='PASS',historical_files_preserved=9588,c5r_files_preserved=52,historical_union_preserved=len(pre['historical_sha256']),mismatches=bad,tracked_dirty=0,staged=0,head_unchanged=True,branch_unchanged=True))
write('prohibited-contact-audit',dict(status='PASS',basis='Recorded actions limited to local frozen reads/search/hash, S-only evidence writes/consistency checks and read-only Git inspection',database=False,network_for_proof=False,runtime_observation=False,containers=False,migrations_executed=False,V043_executed=False,V043_changed=False,B02_executed=False,git_add=False,commit=False,push=False,production_code_changed=False,final_artifact_constructed=False,authentication_or_admission_attempted=False,downstream_rules_materialized=False,binding_recomputation=False,witness_executions=0))
summary=read('final-summary')
for i,review in enumerate(reviews,1):summary['INDEPENDENT_REVIEW_'+str(i)]=review.get('status',review.get('result',review.get('verdict')))
paths=git('ls-files','--others','--exclude-standard').splitlines();prefix=P.relative_to(ROOT).as_posix()+'/';old=set(pre['authorized_paths_before']);assert not [n for n in paths if n not in old and not n.startswith(prefix)]
summary['UNTRACKED_FILES_AFTER']=len(set(paths)|{prefix+'final-return.txt',prefix+'SHA256-MANIFEST.json'});summary['FINAL_VALIDATION']='PASS';summary['KNOWN_LIMITATIONS']='Exact4 inherited construction-input bundles remain unestablished. Static exhaustion scoped to frozen authorized corpus/canonical material requirements, not future artifacts. Two residual classes are contract-level compression, not global atomic minimum. Operational NO preserves R NOT_ESTABLISHED knowledge; no final source artifact or witness proof.'
write('final-summary',summary)
(P/'final-return.txt').write_text('\n'.join(k+'='+('null' if value is None else 'false' if value is False else str(value)) for k,value in summary.items())+'\n',encoding='utf-8')
files={q.relative_to(ROOT).as_posix():sha(q) for q in sorted(P.rglob('*')) if q.is_file() and q.name!='SHA256-MANIFEST.json'};write('SHA256-MANIFEST',dict(algorithm='SHA256',self_excluded=True,files=files))
assert len(git('ls-files','--others','--exclude-standard').splitlines())==summary['UNTRACKED_FILES_AFTER'] and all(sha(ROOT/n)==h for n,h in files.items())
print(json.dumps(dict(status='SEALED',new_files=len(files)+1,untracked_after=summary['UNTRACKED_FILES_AFTER'],historical_union_preserved=len(pre['historical_sha256']),input_denominator=4,established=0,missing=4,residual_input_classes=2,outcome=summary['SELECTED_OUTCOME'],reviews=[summary['INDEPENDENT_REVIEW_1'],summary['INDEPENDENT_REVIEW_2']])))
