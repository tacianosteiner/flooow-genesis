"""Deterministic non-executing symbolic fixture; creates no SQL/key/role/resource."""
from pathlib import Path
import json,hashlib,uuid,datetime,sys
HERE=Path(__file__).parent
def canonical(r):return json.dumps(r,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def digest(b):return hashlib.sha256(b).hexdigest()
def generate(seed,case_id):
    schema=json.loads((HERE/'FIXTURE-SCHEMA.json').read_text());cases=json.loads((HERE/'POSITIVE-CASE-PRECONDITIONS.json').read_text());case=next(c for c in cases if c['CASE_ID']==case_id)
    def ident(field):return str(uuid.UUID(bytes=hashlib.sha256((seed+':'+case_id+':'+field).encode()).digest()[:16],version=5))
    r={k:ident(k) for k in schema['x-uuid-fields']};r.update({k:1 for k in schema['x-generation-fields']})
    policy=json.loads((HERE/'POLICY-TEST-VALUES.json').read_text());policy_hash=digest(canonical(policy))
    r.update(fixture_version=1,source_head=schema['x-input-head'],successor_sha256=schema['x-successor-sha256'],case_id=case_id,service_identity='test_only_executor_'+seed,service_role_oid=20001,policy_hash=policy_hash,approval_hash=digest(canonical({'id':r['approval_id'],'generation':1,'organization_id':r['organization_id']})),attestation_hash=digest(canonical({'id':r['attestation_id'],'generation':1,'approval_hash':digest(canonical({'id':r['approval_id'],'generation':1,'organization_id':r['organization_id']}))})),ownership_state=case['REQUIRED_OWNERSHIP_STATE'],effect_state=case['REQUIRED_EFFECT_STATE'],terminal_state=case['REQUIRED_TERMINAL_STATE'],reconciliation_state=case['REQUIRED_RECONCILIATION_STATE'],issued_at='2026-10-11T00:00:00.000000Z',valid_from='2026-10-11T00:00:00.000000Z',expires_at='2026-10-11T00:00:08.000000Z',readiness_state='ELIGIBLE_FOR_TEST',watchdog_state='SYMBOLIC_ONLY',census_state='SYMBOLIC_ONLY')
    r['context']={'seed':seed,'evaluation_time':'2026-10-11T00:00:02.000000Z','receipt_expires_at':'2026-10-11T00:00:02.100000Z','marker':'TEST_ONLY_NONAUTHORITATIVE','POLICY_FIXTURE_AUTHORITY':'TEST_ONLY','NUMERIC_POLICY_ADOPTED':'NO','PRODUCTION_POLICY_ELIGIBLE':'NO','ROOM_OPERATIONAL':'NO','role_oid_source':'MODEL_ONLY_NOT_PG_ROLES','scope':'NONEXECUTING_DESIGN','generator_sha256':digest(Path(__file__).read_bytes()),'schema_sha256':digest((HERE/'FIXTURE-SCHEMA.json').read_bytes()),'contract_version':1}
    registry={k:r[k] for k in r if k not in ['context']};r['registry']=registry
    rows={}
    for j in json.loads((HERE/'AUTHORITY-JOIN-GRAPH.json').read_text()):
        source,key=j['SOURCE_RELATION'],j['SOURCE_KEY'];value=r.get(key,rows.get(source,{}).get(key,ident(key) if key.endswith('_id') else 1))
        rows.setdefault(source,{})[key]=value
        rows.setdefault(j['TARGET_RELATION'],{})[j['TARGET_KEY']]=value
    r['model_rows']=rows
    r['runtime_evidence']={'catalog_roles':None,'installed_history':None,'live_acl':None,'frozen_binding_frame':None,'original_signed_attestation':None,'accepted_consumption':None,'actual_stage_receipts':None,'reconciliation_recomputation':None,'isolated_target_identity':None,'authority_sql_join_coverage':None}
    r['fixture_manifest_sha256']=digest(canonical({k:v for k,v in r.items() if k!='fixture_manifest_sha256'}))
    return r
if __name__=='__main__':
    target=Path(sys.argv[3]);assert not target.exists();target.write_bytes(canonical(generate(sys.argv[1],sys.argv[2]))+b'\n')
