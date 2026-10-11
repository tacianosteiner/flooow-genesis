"""Current-head audit and complete unchanged native regression; no promotion."""
from pathlib import Path
import ctypes,hashlib,json,subprocess,sys,time,importlib.util
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).parent
HERE=ROOT/'scripts/validation/package_0090_native_health_qualification'
BASE='4e3df82a9ed2bfc28ab869a2fadf56608ddcf726'
MODULES=['binding_encoding_probe','census_probe','quarantine_probe','drain_probe','progress_probe','schedule_probe','replay_probe','oid_probe','domain_probe','scenarios','supplement','restart_probe','crypto_material_probe','storage_probe','socket_probe','participant_dead_probe','frozen_execution_probe','process_population_probe','finite_schedule_probe','compound_probe','successive_ceremony_probe','extended_fault_probe']
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_bytes((json.dumps(v,indent=2)+'\n').encode())
def git(*a):return subprocess.run(['git',*a],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip()
def audit():
    spec=importlib.util.spec_from_file_location('preservation',ROOT/'scripts/validation/package_0090_population_qualification/mission.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    a=m.audit();published=json.loads((ROOT/'docs/evidence/package-0090-g3f4-fc01-fc02-closure/SHA256-FINAL-PUBLICATION.json').read_text())
    additional=[{'path':n,'expected':v,'actual':digest(ROOT/n),'equal':digest(ROOT/n)==v,'domain':'PUBLISHED_2582_EXACT_BYTES'} for n,v in published['files'].items()]
    a['checks']+=additional;a['N']+=len(additional);a['failures']+=sum(not x['equal'] for x in additional)
    return a
def inventory():return {p.name:digest(p) for p in HERE.iterdir() if p.is_file()}
def main():
    batch=OUT/sys.argv[1];assert not batch.exists();batch.mkdir()
    a=audit();save(batch/'BASELINE.json',a)
    assert a['head']==a['remote']==BASE and not a['failures'] and not a['tracked_dirty'] and not a['staged']
    assert a['branch']=='checkpoint/package-0090-cloud-handoff'
    files=inventory();native=hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    frozen_inputs={str(p.relative_to(ROOT)).replace('\\','/'):digest(p) for p in OUT.iterdir() if p.is_file()}
    frozen_inputs.update({str((HERE/n).relative_to(ROOT)).replace('\\','/'):v for n,v in files.items()})
    source=hashlib.sha256(json.dumps(frozen_inputs,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    save(batch/'IMMUTABLE-INPUTS.json',{'files':frozen_inputs,'source_sha256':source,'native_source_sha256':native,'native_files':files,'actual_execution_head':BASE,'legacy_fixture_origin_constant':'0078290f79c8e6bcdc7b124ca0ae24963a915e2d','legacy_constant_is_not_actual_execution_head':True,'executable_successor':'NOT_CREATED_CURRENT_PROMOTION_HOLD'})
    api=ctypes.windll.kernel32.SetThreadExecutionState;api.argtypes=[ctypes.c_uint];api.restype=ctypes.c_uint
    original=api(0x80000001);assert original
    result={'actual_execution_head':BASE,'source_sha256':source,'native_source_sha256':native,'rounds':[],'complete':False,'inherited_PASS':False,'host_harness_control':'PER_THREAD_ES_SYSTEM_REQUIRED_ONLY','numeric_authority':'NONE','host_control_restored':False}
    try:
        for i,module in enumerate(MODULES,1):
            assert inventory()==files and all(digest(ROOT/n)==v for n,v in frozen_inputs.items())
            assert git('rev-parse','HEAD')==BASE
            folder=batch/(str(i).zfill(2)+'-'+module);print('START '+module,flush=True)
            with (batch/(str(i).zfill(2)+'-'+module+'.console.log')).open('w',encoding='utf-8') as log:
                r=subprocess.run([sys.executable,str(HERE/'build.py'),'--output',str(folder),'--scenario-module',module],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
            assert inventory()==files and all(digest(ROOT/n)==v for n,v in frozen_inputs.items())
            raw=json.loads((folder/'RAW-QUALIFICATION.json').read_text()) if (folder/'RAW-QUALIFICATION.json').exists() else {'cases':[],'errors':['BUILD_OR_SETUP_FAILURE']}
            row={'module':module,'directory':str(folder.relative_to(ROOT)),'exit':r.returncode,'executed':sum(not c['result'].startswith('NOT_RUN') for c in raw['cases']),'FAIL':sum(c['result']=='FAIL' for c in raw['cases']),'NOT_RUN':sum(c['result'].startswith('NOT_RUN') for c in raw['cases']),'errors':raw['errors']}
            result['rounds'].append(row);save(batch/'MATRIX.json',result);print('END '+module+' '+json.dumps(row),flush=True)
        result['complete']=True;result['final_preservation']=audit()
    finally:
        result['host_control_restored']=bool(api(original));save(batch/'MATRIX.json',result)
    return int(any(r['FAIL'] or r['errors'] for r in result['rounds']))
if __name__=='__main__':raise SystemExit(main())
