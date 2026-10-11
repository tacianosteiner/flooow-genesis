"""Read-only scope/private-material/whitespace audit; preserves historical bytes."""
from pathlib import Path
import subprocess,json,re,tempfile,hashlib,sys,importlib.util
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).parent
PREFIXES=['docs/evidence/package-0090-g3f4-fc01-fc02-closure/','scripts/validation/package_0090_population_qualification/','docs/evidence/package-0090-g3f4-census-heartbeat-domain-parity/','docs/evidence/package-0090-g3f4-quarantine-closure/','scripts/validation/package_0090_census_qualification/','scripts/validation/package_0090_quarantine_qualification/']
def git(*a):return subprocess.run(['git',*a],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
def main():
    stage=sys.argv[1];target=OUT/(stage+'-SCOPE-AUDIT.json');assert not target.exists()
    statuses=git('status','--porcelain','--untracked-files=all').stdout.splitlines()
    unexpected=[s for s in statuses if not any(s[3:].replace('\\','/').startswith(p) for p in PREFIXES)]
    tracked=git('diff','--name-only','HEAD').stdout.splitlines();staged=git('diff','--cached','--name-only').stdout.splitlines()
    files=[p for prefix in PREFIXES for p in (ROOT/prefix).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    private=[]
    for p in files:
        if re.search(rb'-----BEGIN (?:ED25519 |RSA |EC |OPENSSH )?PRIVATE KEY-----[\r\n]',p.read_bytes()):private.append(str(p.relative_to(ROOT)))
    whitespace=[]
    with tempfile.TemporaryDirectory(prefix='flooow-0090-quarantine-empty-') as empty:
        resolved=Path(empty).resolve();assert resolved.parent==Path(tempfile.gettempdir()).resolve() and resolved.name.startswith('flooow-0090-quarantine-empty-')
        for prefix in PREFIXES:
            r=git('-c','core.autocrlf=false','-c','core.safecrlf=false','-c','core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','diff','--no-index','--check','--',empty,str(ROOT/prefix))
            whitespace.append({'prefix':prefix,'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'PASS':r.returncode in [0,1] and not r.stdout.strip() and not r.stderr.strip()})
    module_path=ROOT/'scripts/validation/package_0090_population_qualification/mission.py';spec=importlib.util.spec_from_file_location('quarantine_preservation_audit',module_path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);preservation=module.audit()
    resources=subprocess.run(['docker','ps','--all','--filter','label=flooow.scope=0090-quarantine-closure','--format','{{.Names}}'],capture_output=True,text=True,check=True).stdout.splitlines()
    resources+=subprocess.run(['docker','ps','--all','--filter','label=flooow.scope=0090-population-closure','--format','{{.Names}}'],capture_output=True,text=True,check=True).stdout.splitlines()
    units=subprocess.run(['docker','ps','--all','--filter','label=flooow.scope=0090-quarantine-unit','--format','{{.Names}}'],capture_output=True,text=True,check=True).stdout.splitlines()
    resources+=subprocess.run(['docker','ps','--all','--filter','label=flooow.scope=0090-quarantine-namespace','--format','{{.Names}}'],capture_output=True,text=True,check=True).stdout.splitlines()
    result={'branch':git('branch','--show-current').stdout.strip(),'HEAD':git('rev-parse','HEAD').stdout.strip(),'REMOTE_HEAD':git('rev-parse','origin/checkpoint/package-0090-cloud-handoff').stdout.strip(),'origin_main':git('rev-parse','origin/main').stdout.strip(),'tracked_dirty':tracked,'staged':staged,'untracked_count':sum(s.startswith('??') for s in statuses),'unexpected_scope':unexpected,'whitespace_checks':whitespace,'private_key_artifact_files':private,'non_secret_files_scanned':len(files),'historical_check_N':preservation['N'],'historical_mismatch_N':preservation['failures'],'owned_runtime_containers_remaining':resources,'owned_unit_containers_remaining':units,'commit_created':False,'push_performed':False,'worktree_clean':not statuses,'scope_PASS':not unexpected and not tracked and not staged and not private and not preservation['failures'] and not resources and not units and all(c['PASS'] for c in whitespace)}
    target.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['branch','HEAD','REMOTE_HEAD','untracked_count','non_secret_files_scanned','historical_mismatch_N','owned_runtime_containers_remaining','owned_unit_containers_remaining','scope_PASS']}))
    return 0 if result['scope_PASS'] else 1
if __name__=='__main__':raise SystemExit(main())
