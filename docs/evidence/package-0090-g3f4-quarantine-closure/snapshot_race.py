"""Owned isolated unit rehearsal of actual observer code; no database or secrets."""
from pathlib import Path
import hashlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).parent
NAME='flooow-0090-quarantine-unit-0078290';SCOPE='0090-quarantine-unit'
IMAGE='sha256:07fc165de5bb569d822460e2df645c5489f99220fc2cb16c86596d39db394561'
HERE=ROOT/'scripts/validation/package_0090_quarantine_qualification'
def main():
    destination=OUT/sys.argv[1];assert not destination.exists();destination.mkdir()
    calls=[];started=False
    def call(args,ok=True):
        r=subprocess.run(args,capture_output=True,text=True,timeout=40);calls.append({'command':args,'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
        if ok and r.returncode:raise RuntimeError(r.stderr)
        return r
    assert subprocess.run(['docker','inspect',NAME],capture_output=True).returncode!=0
    original={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.iterdir() if p.is_file()}
    result={'scope':'TEST_ONLY_NONCANONICAL_UNIT','source_before':original,'no_database':True,'no_keys':True,'numeric_policy_authority':'NONE'}
    try:
        call(['docker','run','--detach','--name',NAME,'--label','flooow.scope='+SCOPE,'--network','none','--cpus','1','--memory','128m','--security-opt','seccomp='+str(ROOT/'docs/evidence/package-0090-g3f4-disposable-native-qualification/SECCOMP-TEST.json'),'--tmpfs','/tmp','--entrypoint','sleep',IMAGE,'infinity']);started=True
        call(['docker','cp',str(HERE),NAME+':/usr/local/src-full'])
        call(['docker','cp',str(Path.home()/'AppData/Local/Temp/flooow-native-qualification/libpq-fe.h'),NAME+':/usr/local/src-full/libpq-fe.h'])
        unit=HERE/'census_snapshot_tests.c' if '--snapshot-bound' in sys.argv else OUT/'CENSUS-SNAPSHOT-RACE.c'
        call(['docker','cp',str(unit),NAME+':/usr/local/src-full/snapshot-race.c'])
        call(['docker','exec',NAME,'sh','-c','sha256sum /usr/local/src-full/*.c /usr/local/src-full/*.h'])
        flags=['-DFLOOOW_SNAPSHOT_BOUND'] if '--snapshot-bound' in sys.argv else []
        call(['docker','exec',NAME,'gcc','-D_GNU_SOURCE','-std=c11','-Wall','-Wextra','-Werror','-Wno-misleading-indentation',*flags,'-I/usr/include/postgresql/18/server','-I/usr/local/src-full','/usr/local/src-full/snapshot-race.c','-o','/usr/local/bin/snapshot-race','-l:libpq.so.5','-lcrypto','-ldl'])
        r=call(['docker','exec','--user','postgres',NAME,'/usr/local/bin/snapshot-race'],False)
        result.update({'unit_exit':r.returncode,'unit_stdout':r.stdout,'unit_stderr':r.stderr,'snapshot_bound':bool(flags),'expected_pre_fix_FAIL_reproduced':not flags and r.returncode==1 and 'STALE_CENSUS_MUST_NOT_QUARANTINE_NEW_PROMOTION=FAIL' in r.stdout,'post_fix_PASS':bool(flags) and r.returncode==0 and 'STALE_CENSUS_MUST_NOT_QUARANTINE_NEW_PROMOTION=PASS' in r.stdout})
        call(['docker','exec',NAME,'sha256sum','/usr/local/bin/snapshot-race'])
    finally:
        if started:
            info=json.loads(call(['docker','inspect',NAME]).stdout)[0]
            assert info['Image']==IMAGE and info['Config']['Labels'].get('flooow.scope')==SCOPE
            call(['docker','rm','--force',NAME]);result['owned_container_removed']=True
        result['source_after']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.iterdir() if p.is_file()}
        result['source_unchanged']=result['source_before']==result['source_after'];result['calls']=calls
        (destination/'RAW.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ['source_before','source_after','calls']}))
    return 0 if result.get('expected_pre_fix_FAIL_reproduced') or result.get('post_fix_PASS') else 1
if __name__=='__main__':raise SystemExit(main())
