"""Fresh raw evidence reconciliation. No historical PASS imports."""
from pathlib import Path
import hashlib,json,sys,importlib.util
B=Path(__file__).parent;OUT=B.parent;ROOT=OUT.parents[2]
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v):(B/n).write_bytes((json.dumps(v,indent=2)+'\n').encode())
def main():
    matrix=load(B/'MATRIX.json');assert matrix['complete'] and matrix['host_control_restored'] and not matrix['inherited_PASS']
    frozen=load(B/'IMMUTABLE-INPUTS.json');expected=frozen['native_files']
    assert all(sha(ROOT/n)==v for n,v in frozen['files'].items())
    assert matrix['final_preservation']['failures']==0
    cohorts=list(matrix['rounds']);cases=[];audits=[];binary_sets=[]
    for r in matrix['rounds']:
        raw=load(ROOT/r['directory']/'RAW-QUALIFICATION.json')
        for key in ['nested_namespace_evidence','nested_ceremony_evidence']:
            if raw.get(key):cohorts.append({'module':key,'directory':str(Path(r['directory'])/raw[key]['directory']),'nested':True})
    for r in cohorts:
        folder=ROOT/r['directory'];raw=load(folder/'RAW-QUALIFICATION.json')
        assert load(folder/'BUILD-INPUT-SHA256.json')['files']==expected and raw['source_hashes']==expected
        compiler={}
        for command in load(folder/'BUILD.json'):
            if command['command'][-1]=='sha256sum /usr/local/src-full/*.c /usr/local/src-full/*.h':
                for line in command['stdout'].splitlines():
                    digest,name=line.split(maxsplit=1);compiler[Path(name).name]=digest
        assert compiler and all(n in compiler for n in expected if n.endswith(('.c','.h')))
        for n,v in compiler.items():assert v==(expected[n] if n!='libpq-fe.h' else '499d984421f5490be016f7d49a8599e7f8be120f0cf80c200e872265064be7c0')
        binaries={Path(n).name:v for v,n in (line.split(maxsplit=1) for line in raw['binary_hashes'].splitlines())}
        assert len(binaries)==4;binary_sets.append(binaries)
        assert raw['owned_container_removed'] and raw['private_key_erasure'] and raw['private_key_absent']
        assert not raw['canonical_access'] and not raw['canonical_mutation'] and not raw['errors']
        assert raw['experimental_controls']['policy_authority']=='NONE'
        assert 'NO_FROZEN_SQL_EXTRACTION' in raw['fixture_schema']
        audits.append({'directory':r['directory'],'binaries':binaries,'compiler_source_exact':True,'keys_erased':True,'container_removed':True})
        if not r.get('nested'):
            cases.extend({'module':r['module'],'raw_path':str((folder/'RAW-QUALIFICATION.json').relative_to(ROOT)),**c} for c in raw['cases'])
    assert len(matrix['rounds'])==22 and len(cohorts)==24 and all(b==binary_sets[0] for b in binary_sets)
    passes=[c for c in cases if c['result'].startswith('PASS')];fails=[c for c in cases if c['result']=='FAIL'];nr=[c for c in cases if c['result'].startswith('NOT_RUN')]
    assert len(passes)+len(fails)+len(nr)==len(cases),'Unknown result classification'
    assert not fails and not any(r['exit'] or r['errors'] for r in matrix['rounds'])
    spec=importlib.util.spec_from_file_location('health',OUT/'health_contract.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    obligations=m.register()
    modules={'POSTMASTER':['schedule_probe','participant_dead_probe','extended_fault_probe'],'SUPERVISOR':['progress_probe','participant_dead_probe','extended_fault_probe'],'RECEIVER':['progress_probe','participant_dead_probe','quarantine_probe'],'CENSUS_OBSERVER':['census_probe','quarantine_probe','finite_schedule_probe','compound_probe'],'APPROVAL_CONSUMER':['extended_fault_probe','successive_ceremony_probe','crypto_material_probe'],'ENFORCEMENT_WORKER':['drain_probe','supplement','compound_probe']}
    missing={'POSTMASTER':'Independent postmaster original-emission heartbeat plus semantic progress/channel generation witness; retained existence alone is insufficient.','SUPERVISOR':'Independently checked completed supervisory work, separate from loop tick and heartbeat; independently replaceable generation contract is absent.','RECEIVER':'Independently checked completed receiver work, separate from fresh heartbeat and reachable socket; independently replaceable generation contract is absent.','CENSUS_OBSERVER':'Completed successful census progress independent from tick emitted before census; complete independent channel/heartbeat contract.','APPROVAL_CONSUMER':'Native producer pidfd identity, generation-bound channel, original heartbeat and completed authority-consumption progress; host publication thread is insufficient.','ENFORCEMENT_WORKER':'Independently anchored enforcement participant, generation/channel and completed cancel/terminate/reconciliation progress; co-location is insufficient.'}
    for o in obligations:
        participant,state=o['CASE'].split('/')
        relevant=modules.get(participant,list(set(n for names in modules.values() for n in names)))
        o['fresh_related_cohort_assertions_not_full_state_coverage']=[{'module':c['module'],'case':c['group']+'/'+c['name'],'result':c['result'],'raw_path':c['raw_path']} for c in passes if c['module'] in relevant]
        o['WHAT_AUTHORITY_OR_ARTIFACT_MISSING']=missing.get(participant,'Complete six-participant independent identity/generation/semantic-progress protocol and matching compound fault producer.')
        o['WHY_NOT_EXECUTABLE']='Full '+state+' obligation requires all nine declared dimensions. Fresh bounded evidence below executes applicable existing controls, but cannot instantiate the missing independent witness contract; it does not close this full obligation.'
    save('FULL-HEALTH-NOT-RUN.json',{'denominator':62,'single_state_N':54,'compound_N':8,'PASS_N':0,'NOT_RUN_N':62,'cases':obligations})
    raw_nr=[]
    for c in nr:
        assert c.get('reason') or c.get('detail'),c
        raw_nr.append({'CASE':c['module']+'/'+c['group']+'/'+c['name'],'BLOCKING_FINDING':c['result'],'WHY_NOT_EXECUTABLE':c.get('reason') or c.get('detail') or c['result'],'WHAT_AUTHORITY_OR_ARTIFACT_MISSING':'Current executable frozen promotion/full positive domain fixture, or independently anchored six-participant semantic-progress protocol, as described in raw evidence. No canonical/numeric authority requested.','raw_path':c['raw_path']})
    save('RAW-NOT-RUN.json',raw_nr)
    measurements=[]
    for a in audits:
        raw=load(ROOT/a['directory']/'RAW-QUALIFICATION.json')
        measurements.append({'raw_path':a['directory']+'/RAW-QUALIFICATION.json','experimental_controls':raw.get('experimental_controls'),'observations':raw.get('observations',[]),'case_details':[{k:c[k] for k in ['group','name','detail'] if k in c} for c in raw['cases']],'clock_domain':'Host monotonic_ns and each independent container BOOTTIME_us are separate; no cross-domain subtraction; case timing/details and native event logs retained verbatim.'})
        for k,v in raw.items():
            if any(s in k.lower() for s in ['latency','measurement','timing']):measurements.append({'raw_path':a['directory']+'/RAW-QUALIFICATION.json','field':k,'value':v,'clock_domain':'AS_DECLARED_IN_RAW; NO_CROSS_CLOCK_SUBTRACTION'})
    save('MEASUREMENTS.json',{'samples':measurements,'worstcase_population_complete':False,'numeric_candidate_ready':False,'numeric_values_adopted':False,'missing_populations':['complete participant detection/quarantine/deny/drain initiation/replacement/recovery','current promoted frozen positive runtime joins']})
    report={'status':'HOLD','actual_execution_head':matrix['actual_execution_head'],'legacy_input_head_is_fixture_origin_only':True,'complete_primary_cohorts':22,'actual_cold_builds':24,'PASS_N':len(passes),'FAIL_N':len(fails),'operational_error_N':0,'raw_NOT_RUN_N':len(nr),'full_health_NOT_RUN_N':62,'total_NOT_RUN_N':len(nr)+62,'unexplained_NOT_RUN_N':0,'source_sha256':frozen['source_sha256'],'native_source_sha256':frozen['native_source_sha256'],'native_binary_sha256':hashlib.sha256(json.dumps(binary_sets[0],sort_keys=True,separators=(',',':')).encode()).hexdigest(),'executable_successor_sha256':'NOT_CREATED_CURRENT_PROMOTION_HOLD','historical_checks':matrix['final_preservation']['N'],'historical_failures':0,'inherited_PASS':False,'cases':cases,'audits':audits,'FC01':'OPEN','FC02':'PARTIAL','FC03':'OPEN','FC04':'PARTIAL','FC05':'PARTIAL','FC06':'PARTIAL','FC07':'PARTIAL','findings':{'BLOCKER':1,'HIGH':3,'MEDIUM':3,'LOW':0}}
    save('RECONCILIATION.json',report);print(json.dumps({k:v for k,v in report.items() if k not in ['cases','audits']}))
if __name__=='__main__':main()
