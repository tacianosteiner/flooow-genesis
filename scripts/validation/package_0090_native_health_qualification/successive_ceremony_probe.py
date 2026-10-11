"""A precedes B; actual disposable signatures, current native authority, no canonical."""
import json,os,uuid,subprocess,copy
def run(q):
    import foreign_capture_probe
    foreign_capture_probe.run(q)
    frame=(q.OUT/'TEST_ONLY_NONCANONICAL-VALID-FOREIGN-FRAME.bin').read_bytes()
    q.save('CEREMONY-A-PUBLIC.json',{'scope':'TEST_ONLY_NONCANONICAL','approval':q.expected_approval,'attestation':q.expected_bundle,'frame_hex':frame.hex(),'original_A_actually_admitted':True})
    old=copy.deepcopy(q.expected_status);old['state']='REVOKED'
    q.paused.set()
    with q.health_lock:q.rootfile('/run/flooow-external/status.json',json.dumps(old));assert not q.observer_once()
    q.denial('successive_ceremony','old_A_current_custody_revoked')
    env=os.environ.copy();env['FLOOOW_TEST_NAMESPACE_CONTAINER']='flooow-0090-quarantine-namespace-'+uuid.uuid4().hex[:12];env['FLOOOW_TEST_OLD_CEREMONY_PUBLIC']=str((q.OUT/'CEREMONY-A-PUBLIC.json').resolve())
    child=q.OUT/'ceremony-B'
    with (q.OUT/'CEREMONY-B.console.log').open('w',encoding='utf-8') as stream:
        result=subprocess.run([q.sys.executable,str(q.HERE/'build.py'),'--output',str(child),'--scenario-module','successive_second_probe'],env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=180)
    raw=json.loads((child/'RAW-QUALIFICATION.json').read_text())
    q.record['nested_ceremony_evidence']={'directory':'ceremony-B','scope':'TEST_ONLY_NONCANONICAL','private_exported':False}
    for c in raw['cases']:q.record['cases'].append({**c,'group':'ceremony_B/'+c['group'],'nested_raw_path':'ceremony-B/RAW-QUALIFICATION.json'})
    q.case('successive_ceremony','actual_later_B_bootstrap_cleanup',result.returncode==0 and not raw['errors'] and raw['owned_container_removed'] and raw['private_key_erasure'] and raw['private_key_absent'],{'errors':raw['errors'],'old_A_before_B':True,'private_material_exported':False,'normative_SQL_joins':'NOT_RUN_SQLSTATE_55000'})
