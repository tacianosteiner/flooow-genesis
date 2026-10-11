"""Fresh final design review; no wrapper/native execution or resource creation."""
from pathlib import Path
import json,hashlib,subprocess,copy,sys,importlib.util
from generate_fixture import generate
from validate_fixture import validate
HERE=Path(__file__).parent;ROOT=HERE.parents[2]
def canonical(r):return json.dumps(r,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def sha(b):return hashlib.sha256(b).hexdigest()
def save(p,r):assert not p.exists();p.write_bytes((json.dumps(r,indent=2)+'\n').encode())
def main():
    out=HERE/'final-01';assert not out.exists();out.mkdir()
    files={p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in HERE.iterdir() if p.is_file()};source=sha(canonical(files));save(out/'IMMUTABLE-SOURCE.json',{'files':files,'source_sha256':source,'prior_validation_is_historical_only':True})
    cases=json.loads((HERE/'POSITIVE-CASE-PRECONDITIONS.json').read_text());schema=json.loads((HERE/'FIXTURE-SCHEMA.json').read_text());joins=json.loads((HERE/'AUTHORITY-JOIN-GRAPH.json').read_text());negatives=json.loads((HERE/'NEGATIVE-CONTROL-MATRIX.json').read_text());results=[]
    for case in cases:
        name=case['CASE_ID'];a=generate('public-design-seed-v1',name);b=generate('public-design-seed-v1',name);assert canonical(a)==canonical(b)
        valid=validate(a);assert valid['MODEL_VALID'] and not valid['POSITIVE_EXECUTION_ELIGIBLE'] and not any(valid[k] for k in ['FIXTURE_AUTHORITY_COMPLETE','FIXTURE_GENERATION_COMPLETE','FIXTURE_POLICY_COMPLETE','FIXTURE_READINESS_COMPLETE','FIXTURE_TIME_VALID'])
        mutation_results=[]
        for row in [v for v in negatives if v['CASE_ID']==name]:
            field=row['CHANGED_GOVERNED_DIMENSION'];m=copy.deepcopy(a)
            if field=='receipt_expires_at':m['context'][field]='2026-10-11T00:00:01.000000Z'
            elif type(m[field]) is int:m[field]=m[field]+1 if field=='service_role_oid' else 0
            elif field.endswith('_id'):m[field]='11111111-1111-5111-8111-111111111111'
            elif field=='successor_sha256':m[field]='0'*64
            else:m[field]='WRONG_STATE'
            m['fixture_manifest_sha256']=sha(canonical({k:v for k,v in m.items() if k!='fixture_manifest_sha256'}));r=validate(m);assert not r['MODEL_VALID'] and not r['POSITIVE_EXECUTION_ELIGIBLE'];mutation_results.append(row['NEGATIVE_CONTROL'])
        assert len(mutation_results)==13
        for field in schema['required']:
            m=copy.deepcopy(a);del m[field];assert not validate(m)['MODEL_VALID']
        for j in joins:
            m=copy.deepcopy(a);del m['model_rows'][j['SOURCE_RELATION']][j['SOURCE_KEY']];m['fixture_manifest_sha256']=sha(canonical({k:v for k,v in m.items() if k!='fixture_manifest_sha256'}));assert not validate(m)['MODEL_VALID']
        for dimension in ['context','model_rows','runtime_evidence']:
            m=copy.deepcopy(a);m[dimension]['unknown_authority']=True;m['fixture_manifest_sha256']=sha(canonical({k:v for k,v in m.items() if k!='fixture_manifest_sha256'}));assert not validate(m)['MODEL_VALID']
        m=copy.deepcopy(a);m['runtime_evidence']={k:True for k in m['runtime_evidence']};m['fixture_manifest_sha256']=sha(canonical({k:v for k,v in m.items() if k!='fixture_manifest_sha256'}));assert not validate(m)['POSITIVE_EXECUTION_ELIGIBLE']
        for field in ['organization_id','effect_state','ROOM_OPERATIONAL']:
            m=copy.deepcopy(a)
            if field=='ROOM_OPERATIONAL':m['context'][field]='YES'
            elif field.endswith('_id'):m[field]='11111111-1111-5111-8111-111111111111'
            else:m[field]='FABRICATED_EFFECT'
            m['fixture_manifest_sha256']=sha(canonical({k:v for k,v in m.items() if k!='fixture_manifest_sha256'}));assert not validate(m)['MODEL_VALID']
        results.append({'case':name,'fresh_model_validation':valid,'deterministic':True,'all_13_negative_dimensions_denied':True,'all_required_field_omissions_denied':True,'all_40_join_omissions_denied':True,'unknown_nested_authority_denied':True,'cross_tenant_and_fabricated_effect_denied':True,'room_operational_denied':True,'self_attested_runtime_proof_never_authorizes':True})
    native=json.loads((HERE/'NATIVE-HEALTH-DESIGN.json').read_text());nodes=native['nodes'];edges=native['required_edges'];assert len(nodes)==9 and len(edges)==8 and all(a!=b for a,b in edges)
    indegree={n:0 for n in nodes};children={n:[] for n in nodes}
    for a,b in edges:indegree[b]+=1;children[a].append(b)
    queue=[n for n in nodes if indegree[n]==0];seen=[]
    while queue:
        n=queue.pop();seen.append(n)
        for child in children[n]:
            indegree[child]-=1
            if indegree[child]==0:queue.append(child)
    assert len(seen)==9 and not native['unobserved_critical_participants']
    required='PARTICIPANT_NAME IDENTITY_SOURCE IDENTITY_BINDING GENERATION_SOURCE GENERATION_BINDING LIVENESS_SOURCE PROGRESS_SOURCE COMPLETED_WORK_WITNESS INDEPENDENT_OBSERVER FAIL_CLOSED_ACTION GENERATION_CREATED_WHEN GENERATION_INVALIDATED_WHEN GENERATION_STORED_WHERE GENERATION_OBSERVED_BY STALE_GENERATION_DENIAL RESTART_BEHAVIOR'.split()
    assert len(native['participants'])==7 and all(all(p.get(k) for k in required) for p in native['participants'])
    prior=ROOT/'docs/evidence/package-0090-g3f4-hash-bound-successor/final-02/SHA256-PUBLICATION.json';f=json.loads(prior.read_text())['files'];assert all(sha((ROOT/n).read_bytes())==v for n,v in f.items())
    sys.path.insert(0,str(ROOT/'scripts/validation/package_0090_executable_promotion'));spec=importlib.util.spec_from_file_location('prior_audit',ROOT/'scripts/validation/package_0090_executable_promotion/final_gate.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);preservation=m.preservation();assert not preservation['failures']
    assert all(sha((ROOT/n).read_bytes())==v for n,v in files.items())
    report={'source_sha256':source,'fresh_case_models':results,'native_graph_acyclic':True,'native_participant_fields_complete':True,'FULL_DOMAIN_FIXTURE_CONTRACT_READY':'NO','FIXTURE_SCHEMA_COMPLETE':'NO_RUNTIME_WITNESS_SCHEMA_OPEN','POSITIVE_CASE_PRECONDITIONS_COMPLETE':'NO_FULL_SEMANTIC_GUARD_COVERAGE_OPEN','AUTHORITY_JOIN_GRAPH_COMPLETE':'NO_MODEL_ONLY','FIXTURE_PROVENANCE_COMPLETE':'YES_MODEL_ONLY_RUNTIME_PENDING','FIXTURE_VALIDATOR_FAIL_CLOSED':'YES_NO_POSITIVE_ELIGIBILITY','NEGATIVE_CONTROL_MATRIX_COMPLETE':'YES_13_X_13_MODEL_CONTROLS_ACTUAL_SQL_NOT_RUN','POLICY_FIXTURE_AUTHORITY':'TEST_ONLY','NUMERIC_POLICY_ADOPTED':'NO','TEST_READINESS_STATE_MACHINE':'DEFINED_TEST_ONLY_NO_OPERATIONAL_READY','NATIVE_HEALTH_CONTRACT_READY':'YES_DESIGN_ONLY_NO_IMPLEMENTATION','NATIVE_PROTOCOL_CHANGED':'NO','BLOCKER_COUNT':2,'HIGH_COUNT':0,'MEDIUM_COUNT':0,'LOW_COUNT':0,'FC01_STATUS':'HOLD_FIXTURE_CONTRACT_ONLY','positive_wrapper_execution':0,'canonical_access_or_mutation':False,'numeric_values_adopted':False,'historical_checks':preservation['N']+len(f)+1,'historical_mismatch':0,'owned_resources_created':0,'secrets_or_private_keys_created':0,'cleanup':'COMPLETE_NO_OWNED_RUNTIME_RESOURCES','inherited_PASS':False,'FAIL':0,'next_gate':'Complete exact frozen SQL predicate/overload-to-row/frame witness mapping and independent witness validators under existing design authority; then freeze and validate one full fixture. Do not execute positives yet.'}
    save(out/'FINAL-REVIEW.json',report)
    publication={p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts};save(out/'SHA256-PUBLICATION.json',{'files':publication,'aggregate_sha256':sha(canonical(publication)),'excluded':'This publication manifest only'})
    print(json.dumps({k:v for k,v in report.items() if k!='fresh_case_models'}))
if __name__=='__main__':main()
