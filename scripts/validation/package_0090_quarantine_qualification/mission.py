"""Preserve predecessor; execute final matrix on one immutable source inventory."""
from pathlib import Path
import json,hashlib,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).parent
OUT=ROOT/'docs/evidence/package-0090-g3f4-quarantine-closure'
BASE='0078290f79c8e6bcdc7b124ca0ae24963a915e2d'
def sha(p,lf=False):
    data=p.read_bytes();return hashlib.sha256(data.replace(b'\r\n',b'\n') if lf else data).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def git(*args):return subprocess.run(['git',*args],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip()
def audit():
    old=ROOT/'docs/evidence/package-0090-g3f4-census-heartbeat-domain-parity'
    checks=[]
    manifest=json.loads((old/'SHA256-WORKTREE.json').read_text())
    for name,value in manifest['files'].items():checks.append({'path':name,'expected':value,'actual':sha(ROOT/name),'equal':sha(ROOT/name)==value,'domain':'PREVIOUS_548_EXACT_WORKTREE'})
    for folder in ['package-0090-g3f4-full-binding-enforcement-qualification','package-0090-g3f4-disposable-native-qualification']:
        m=json.loads((ROOT/'docs/evidence'/folder/'SHA256.json').read_text(encoding='utf-8-sig'))
        for name,value in m['files'].items():checks.append({'path':name,'expected':value,'actual':sha(ROOT/name,True),'equal':sha(ROOT/name,True)==value,'domain':'HISTORICAL_GIT_LF'})
    m=json.loads((ROOT/'docs/evidence/package-0090-g3f4-current-contract-reconciliation/CONTRACT-LINEAGE.json').read_text(encoding='utf-8-sig'))
    for name,value in m['source_worktree_sha256'].items():checks.append({'path':name,'expected':value,'actual':sha(ROOT/name),'equal':sha(ROOT/name)==value,'domain':'HISTORICAL_EXACT_SOURCE'})
    oldcases=json.loads((old/'POST-ATTEMPT10-FULL-REGRESSION.json').read_text())['cases']
    previous=[c for c in oldcases if c['result'].startswith('NOT_RUN')];assert len(previous)==21
    return {'checks':checks,'N':len(checks),'failures':sum(not c['equal'] for c in checks),'previous_not_run':previous,'PREVIOUS_NOT_RUN_N':21,'branch':git('branch','--show-current'),'head':git('rev-parse','HEAD'),'remote':git('rev-parse','origin/checkpoint/package-0090-cloud-handoff'),'origin_main':git('rev-parse','origin/main'),'tracked_dirty':git('diff','--name-only','HEAD').splitlines(),'staged':git('diff','--cached','--name-only').splitlines()}
def inventory():return {p.name:sha(p) for p in HERE.iterdir() if p.is_file()}
def main():
    batch=sys.argv[1];dest=OUT/batch
    if dest.exists():raise RuntimeError('Refuse existing matrix evidence')
    dest.mkdir();a=audit();save(dest/'BASELINE-PRESERVATION.json',a)
    assert not a['failures'] and not a['tracked_dirty'] and not a['staged'] and a['head']==a['remote']==BASE and a['branch']=='checkpoint/package-0090-cloud-handoff'
    sources=inventory();source_digest=hashlib.sha256(json.dumps(sources,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    save(dest/'IMMUTABLE-SOURCE.json',{'domain':'SHA256 sorted compact JSON filename/exact byte SHA256 mapping','sha256':source_digest,'files':sources})
    modules=['binding_encoding_probe','census_probe','quarantine_probe','drain_probe','progress_probe','schedule_probe','replay_probe','oid_probe','domain_probe','scenarios','supplement','restart_probe','crypto_material_probe','storage_probe','socket_probe','participant_dead_probe']
    matrix={'source_sha256':source_digest,'rounds':[],'complete':False,'inherited_PASS':False,'canonical_access':False,'numeric_values_adopted':False}
    for index,module in enumerate(modules,1):
        assert inventory()==sources,'Source changed after freeze; refuse mixed final denominator'
        output=dest/(str(index).zfill(2)+'-'+module);begin=time.monotonic_ns();print('START '+module,flush=True)
        with (dest/(str(index).zfill(2)+'-'+module+'.console.log')).open('w',encoding='utf-8') as stream:
            result=subprocess.run([sys.executable,str(HERE/'build.py'),'--output',str(output),'--scenario-module',module],stdout=stream,stderr=subprocess.STDOUT)
        assert inventory()==sources,'Source changed while compiling/executing'
        raw=json.loads((output/'RAW-QUALIFICATION.json').read_text()) if (output/'RAW-QUALIFICATION.json').exists() else {'cases':[],'errors':['BUILD_OR_SETUP_FAILED']}
        row={'module':module,'directory':str(output.relative_to(ROOT)),'exit':result.returncode,'begin_ns':begin,'end_ns':time.monotonic_ns(),'assertions':sum(not c['result'].startswith('NOT_RUN') for c in raw['cases']),'FAIL':sum(c['result']=='FAIL' for c in raw['cases']),'NOT_RUN':sum(c['result'].startswith('NOT_RUN') for c in raw['cases']),'errors':raw['errors'],'binary_hashes':raw.get('binary_hashes')}
        matrix['rounds'].append(row);save(dest/'MATRIX.json',matrix);print('END '+module+' '+json.dumps({k:row[k] for k in ['exit','assertions','FAIL','NOT_RUN','errors']}),flush=True)
    matrix['complete']=True;matrix['final_preservation']=audit();save(dest/'MATRIX.json',matrix)
    return int(any(r['FAIL'] or r['errors'] for r in matrix['rounds']))
if __name__=='__main__':raise SystemExit(main())
