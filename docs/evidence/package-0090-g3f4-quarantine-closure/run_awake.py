"""Experimental host harness: prevent idle sleep only during the owned matrix."""
from pathlib import Path
import ctypes,datetime,json,subprocess,sys,time,hashlib
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).parent
def main():
    batch=sys.argv[1];path=OUT/(batch+'-HOST-EXECUTION-CONTROL.json')
    assert not path.exists() and not (OUT/batch).exists()
    api=ctypes.windll.kernel32.SetThreadExecutionState
    api.argtypes=[ctypes.c_uint];api.restype=ctypes.c_uint
    original=api(0x80000001) # ES_CONTINUOUS | ES_SYSTEM_REQUIRED; no display change.
    if not original:raise RuntimeError('Unable to set temporary per-thread host execution request')
    start=time.monotonic_ns()
    record={'scope':'EXPERIMENTAL_HOST_HARNESS_ONLY','policy_authority':'NONE','numeric_values_adopted':False,'control':'Temporary per-thread ES_SYSTEM_REQUIRED; prevent idle sleep during preparation and tests','changes_OS_power_policy':False,'changes_display_state':False,'does_not_prevent_manual_suspend_or_VM_pause':True,'does_not_establish_cause_of_prior_Docker_timeouts':True,'original_thread_state':original,'start_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'restored':False}
    try:
        path.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
        record['harness_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        if '--module' in sys.argv:
            module=sys.argv[sys.argv.index('--module')+1];assert module in ['schedule_probe','quarantine_probe','drain_probe','progress_probe','replay_probe']
            command=[sys.executable,str(ROOT/'scripts/validation/package_0090_quarantine_qualification/build.py'),'--output',str(OUT/batch),'--scenario-module',module]
            record['prequalification_module']=module
        else:command=[sys.executable,str(ROOT/'scripts/validation/package_0090_quarantine_qualification/mission.py'),batch]
        result=subprocess.run(command,cwd=ROOT)
        record['matrix_exit']=result.returncode
        return result.returncode
    finally:
        restored=api(original)
        record.update({'restored':bool(restored),'end_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'elapsed_monotonic_ns':time.monotonic_ns()-start})
        path.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':raise SystemExit(main())
