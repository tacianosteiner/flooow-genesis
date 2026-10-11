"""Scope, exact-byte freeze and index audit; never commits or pushes."""
from pathlib import Path
import json,hashlib,subprocess,re,sys,tempfile
B=Path(__file__).parent;OUT=B.parent;ROOT=OUT.parents[2];PREFIX=OUT.relative_to(ROOT).as_posix()+'/'
CODE=ROOT/'scripts/validation/package_0090_native_health_qualification';CODEPREFIX=CODE.relative_to(ROOT).as_posix()+'/'
def git(*args,binary=False,input=None):
    return subprocess.run(['git',*args],cwd=ROOT,input=input,capture_output=True,text=not binary,check=True).stdout
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v):
    target=B/n
    if target.exists():raise RuntimeError('Refuse overwrite of audit/freeze evidence: '+n)
    target.write_bytes((json.dumps(v,indent=2)+'\n').encode())
def audit():
    r=json.loads((B/'RECONCILIATION.json').read_text());assert r['PASS_N'] and not r['FAIL_N'] and not r['operational_error_N']
    assert git('branch','--show-current').strip()=='checkpoint/package-0090-cloud-handoff'
    assert git('rev-parse','HEAD').strip()==r['actual_execution_head']
    assert not git('diff','--name-only','HEAD').strip() and not git('diff','--cached','--name-only').strip()
    statuses=git('status','--porcelain','--untracked-files=all').splitlines()
    assert all(s.startswith('?? '+PREFIX) or s.startswith('?? '+CODEPREFIX) for s in statuses),statuses
    files=[p for directory in [OUT,CODE] for p in directory.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    private=[p.relative_to(ROOT).as_posix() for p in files if re.search(rb'-----BEGIN (?:ED25519 |RSA |EC |OPENSSH )?PRIVATE KEY-----[\r\n]',p.read_bytes())]
    assert not private
    resources=[]
    for label in ['0090-population-closure','0090-quarantine-closure','0090-quarantine-unit','0090-quarantine-namespace']:
        resources+=subprocess.run(['docker','ps','--all','--filter','label=flooow.scope='+label,'--format','{{.Names}}'],capture_output=True,text=True,check=True).stdout.splitlines()
    assert not resources
    check=git('diff','--check');assert not check
    with tempfile.TemporaryDirectory(prefix='flooow-handoff-whitespace-') as empty:
        for directory in [OUT,CODE]:
            check=subprocess.run(['git','-c','core.autocrlf=false','-c','core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','diff','--no-index','--check','--',empty,str(directory)],cwd=ROOT,capture_output=True,text=True)
            assert check.returncode in [0,1] and not check.stdout.strip() and not check.stderr.strip(),check.stdout
    save('SCOPE-FINAL-AUDIT.json',{'scope_PASS':True,'prefixes':[PREFIX,CODEPREFIX],'files_scanned':len(files),'private_material_files':private,'owned_containers_remaining':resources,'historical_checks':r['historical_checks'],'historical_failures':0,'canonical_access':False,'numeric_adoption':False,'origin_main':git('rev-parse','origin/main').strip(),'scope':'NEW_EVIDENCE_AND_DISPOSABLE_HARNESS_SUCCESSOR_ONLY; native C/H unchanged; no application/migration/dependency/frozen artifact changes','diff_check':'PASS'})
def freeze():
    target=B/'SHA256-PUBLICATION.json';assert not target.exists()
    files={p.relative_to(ROOT).as_posix():digest(p) for directory in [OUT,CODE] for p in sorted(directory.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p!=target}
    save(target.name,{'files':files,'aggregate_sha256':hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'excluded':['self','generated __pycache__'],'exact_byte_domain':'worktree; stage with core.autocrlf=false'})
    print('FROZEN_FILES='+str(len(files))+' MANIFEST_SHA256='+digest(target))
def verify():
    target=B/'SHA256-PUBLICATION.json';files=json.loads(target.read_text())['files'];files[target.relative_to(ROOT).as_posix()]=digest(target)
    staged=git('diff','--cached','--name-only','-z').split('\0');assert set(filter(None,staged))==set(files)
    assert all(digest(ROOT/n)==v for n,v in files.items())
    names=sorted(files);blob=git('cat-file','--batch',binary=True,input=''.join(':'+n+'\n' for n in names).encode());cursor=0
    for n in names:
        end=blob.index(b'\n',cursor);header=blob[cursor:end].split();assert header[1]==b'blob';size=int(header[2]);cursor=end+1
        assert hashlib.sha256(blob[cursor:cursor+size]).hexdigest()==files[n],n;cursor+=size;assert blob[cursor:cursor+1]==b'\n';cursor+=1
    assert cursor==len(blob)
    assert not git('-c','core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','diff','--cached','--check')
    print('INDEX_EXACT_BYTE_CHECK=PASS FILE_N='+str(len(names)))
if __name__=='__main__':globals()[sys.argv[1]]()
