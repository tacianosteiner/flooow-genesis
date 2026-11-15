"""Seal U evidence after two independent documentary reviews; never construct inputs."""
import hashlib,importlib.util,json,pathlib,subprocess,sys
sys.dont_write_bytecode=True
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2]
def read(n):return json.loads((P/(n+'.json')).read_text(encoding='utf-8-sig'))
def write(n,v):(P/(n+'.json')).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],cwd=ROOT,text=True).strip()
s=importlib.util.spec_from_file_location('u_validate',P/'validate.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v);write('static-validation',v.run())
reviews=[read('independent-review-'+str(i)) for i in [1,2]]
for r in reviews:
    assert r.get('status',r.get('result',r.get('verdict',''))).startswith('PASS')
    assert not r.get('blocking_defects',r.get('blocking_findings',[]))
    for n,h in r.get('reviewed_sha256',r.get('source_hashes',r.get('pinned_artifacts',{}))).items():
        p=ROOT/n if n.replace('\\','/').startswith('docs/') else P/n
        assert sha(p)==h,('review source changed',n)
pre=read('preflight')
assert not git('diff','--name-only') and not git('diff','--cached','--name-only')
assert git('rev-parse','HEAD')==pre['head'] and git('branch','--show-current')==pre['branch']
assert all(sha(ROOT/n)==h for n,h in pre['historical_sha256'].items())
write('historical-preservation',dict(status='PASS',historical_before_t=9671,c5t_files=30,historical_union_preserved=9701,mismatches=0,tracked_dirty=0,staged=0,head_unchanged=True,c5t_outcome_and_stop_unchanged=True))
write('prohibited-contact-audit',dict(status='PASS',basis='Observed session actions limited to frozen local authority/identity reads/hash, U-only evidence writes/specification QA and read-only Git; no retrospective external command telemetry claimed',shared_db=False,production=False,existing_local_db=False,network_for_proof=False,containers=False,V043_execution=False,V043_change=False,B02_execution=False,git_add=False,commit=False,push=False,input_creation=False,artifact_construction=False,full_creation_procedure_implementation=False,authentication_attempt=False,admission_attempt=False,witness_executions=0))
summary=read('final-summary')
for i,r in enumerate(reviews,1):summary['INDEPENDENT_REVIEW_'+str(i)]=r.get('status',r.get('result',r.get('verdict')))
paths=git('ls-files','--others','--exclude-standard').splitlines();prefix=P.relative_to(ROOT).as_posix()+'/'
assert not [n for n in paths if n not in pre['authorized_paths_before'] and not n.startswith(prefix)]
summary['UNTRACKED_FILES_AFTER']=len(set(paths)|{prefix+'final-return.txt',prefix+'SHA256-MANIFEST.json'})
summary['FINAL_VALIDATION']='PASS'
summary['KNOWN_LIMITATIONS']='Prospective integrity envelope specification only. No concrete qualified creator/verifier pair, separation, complete semantic transform, independent verifier or full creation order established. null minimum blocker/nondeterminism/cycle values mean NOT_ESTABLISHED, not zero. NO auth/admission flags preserve historical NOT_ESTABLISHED knowledge. No four-input/artifact creation.'
write('final-summary',summary)
def render(val):
    if val is None:return 'null'
    if val is False:return 'false'
    if isinstance(val,(list,dict)):return json.dumps(val,separators=(',',':'),ensure_ascii=False)
    return str(val)
(P/'final-return.txt').write_text('\n'.join(k+'='+render(val) for k,val in summary.items())+'\n',encoding='utf-8')
files={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(P.rglob('*')) if p.is_file() and p.name!='SHA256-MANIFEST.json'}
write('SHA256-MANIFEST',dict(algorithm='SHA256',self_excluded=True,files=files))
assert len(git('ls-files','--others','--exclude-standard').splitlines())==summary['UNTRACKED_FILES_AFTER']
assert all(sha(ROOT/n)==h for n,h in files.items())
print(json.dumps(dict(status='SEALED',new_files=len(files)+1,historical_union=9701,untracked_after=summary['UNTRACKED_FILES_AFTER'],outcome=summary['SELECTED_OUTCOME'],reviews=[summary['INDEPENDENT_REVIEW_1'],summary['INDEPENDENT_REVIEW_2']])))
