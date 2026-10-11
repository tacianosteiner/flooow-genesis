"""Read-only final scope/whitespace/non-secret artifact review, including untracked files."""
from pathlib import Path
import subprocess,json,tempfile,re,hashlib
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'docs/evidence/package-0090-g3f4-census-heartbeat-domain-parity'
paths=[ROOT/'scripts/validation/package_0090_census_qualification',OUT]
def git(*args):return subprocess.run(['git',*args],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
checks=[]
with tempfile.TemporaryDirectory(prefix='flooow-0090-empty-scope-') as empty:
    assert Path(empty).resolve().parent==Path(tempfile.gettempdir()).resolve()
    for path in paths:
        r=git('-c','core.autocrlf=false','-c','core.safecrlf=false','-c','core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','diff','--no-index','--check','--',empty,str(path))
        checks.append({'target':str(path.relative_to(ROOT)),'exit':r.returncode,'stdout':r.stdout[:4096],'stdout_bytes':len(r.stdout.encode('utf-8')),'stderr':r.stderr[:4096],'PASS':r.returncode in [0,1] and not r.stdout.strip() and not r.stderr.strip()})
files=[p for root in paths for p in root.rglob('*') if p.is_file() and '__pycache__' not in str(p)]
private=[str(p.relative_to(ROOT)) for p in files if re.search(rb'-----BEGIN (?:ED25519 |RSA |EC |OPENSSH )?PRIVATE KEY-----[\r\n]',p.read_bytes())]
status=git('status','--porcelain','--untracked-files=all').stdout.splitlines()
unexpected=[s for s in status if s[3:].replace('\\','/').split('/')[0] not in ['docs','scripts'] or not (s[3:].replace('\\','/').startswith('docs/evidence/package-0090-g3f4-census-heartbeat-domain-parity/') or s[3:].replace('\\','/').startswith('scripts/validation/package_0090_census_qualification/'))]
result={'branch':git('branch','--show-current').stdout.strip(),'HEAD':git('rev-parse','HEAD').stdout.strip(),'REMOTE_HEAD':git('rev-parse','origin/checkpoint/package-0090-cloud-handoff').stdout.strip(),'tracked_diff':git('diff','--name-only','HEAD').stdout.splitlines(),'staged':git('diff','--cached','--name-only').stdout.splitlines(),'untracked_count':sum(s.startswith('??') for s in status),'unexpected_scope_entries':unexpected,'whitespace_checks':checks,'non_secret_files_scanned':len(files),'private_key_artifact_files':private,'commit_created':False,'push_performed':False,'WORKTREE_CLEAN':not status}
(OUT/'FINAL-SCOPE-AUDIT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print('SCOPE',not unexpected and not result['tracked_diff'] and not result['staged'],'WHITESPACE',all(c['PASS'] for c in checks),'PRIVATE_KEY_ARTIFACTS',len(private),'UNTRACKED',result['untracked_count'])
