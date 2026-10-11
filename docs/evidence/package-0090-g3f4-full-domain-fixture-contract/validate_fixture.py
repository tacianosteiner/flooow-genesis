"""Independent fail-closed design validator. No generator imports or SQL execution."""
from pathlib import Path
import json,hashlib,datetime,uuid,re
HERE=Path(__file__).parent
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def validate(r):
    flags={k:False for k in ['FIXTURE_STRUCTURALLY_COMPLETE','FIXTURE_AUTHORITY_COMPLETE','FIXTURE_GENERATION_COMPLETE','FIXTURE_POLICY_COMPLETE','FIXTURE_READINESS_COMPLETE','FIXTURE_TIME_VALID','FIXTURE_SUCCESSOR_BOUND','MODEL_GENERATION_COMPLETE','MODEL_POLICY_VALID','MODEL_TIME_VALID']};errors=[]
    try:
        schema=json.loads((HERE/'FIXTURE-SCHEMA.json').read_text());cases=json.loads((HERE/'POSITIVE-CASE-PRECONDITIONS.json').read_text());joins=json.loads((HERE/'AUTHORITY-JOIN-GRAPH.json').read_text())
        expected={'fixture_id','fixture_version','source_head','successor_sha256','fixture_manifest_sha256','organization_id','case_id','order_id','trace_id','deployment_id','incarnation_id','service_identity','service_role_oid','allocation_id','binding_id','binding_generation','policy_id','policy_revision','policy_hash','approval_id','approval_generation','approval_hash','attestation_id','attestation_generation','attestation_hash','receipt_id','receipt_generation','execution_id','attempt_id','execution_generation','ownership_state','effect_state','terminal_state','reconciliation_state','issued_at','valid_from','expires_at','readiness_state','watchdog_state','census_state','context','registry','model_rows','runtime_evidence'}
        if set(r)!=expected:raise ValueError('Missing/extra schema fields')
        for k in schema['x-uuid-fields']:
            if not isinstance(r[k],str) or str(uuid.UUID(r[k]))!=r[k] or uuid.UUID(r[k]).int==0:raise ValueError('UUID '+k)
        for k in schema['x-generation-fields']+['service_role_oid','fixture_version']:
            if type(r[k]) is not int or r[k]<=0:raise ValueError('Positive integer '+k)
        for k in schema['x-hash-fields']:
            if not isinstance(r[k],str) or not re.fullmatch('[0-9a-f]{64}',r[k]):raise ValueError('Hash '+k)
        if r['source_head']!='c19644fc77ce930eeae7f83c2d219d8d5e07433f' or r['successor_sha256']!='6ad78ba61d70e803d2a878034aa7988b69b6374568f96949b2ef6c8defc7a8c7':raise ValueError('Current successor provenance')
        c=r['context']
        if set(c)!={'seed','evaluation_time','receipt_expires_at','marker','POLICY_FIXTURE_AUTHORITY','NUMERIC_POLICY_ADOPTED','PRODUCTION_POLICY_ELIGIBLE','ROOM_OPERATIONAL','role_oid_source','scope','generator_sha256','schema_sha256','contract_version'}:raise ValueError('Context field omission/extension')
        for key,value in {'marker':'TEST_ONLY_NONAUTHORITATIVE','POLICY_FIXTURE_AUTHORITY':'TEST_ONLY','NUMERIC_POLICY_ADOPTED':'NO','PRODUCTION_POLICY_ELIGIBLE':'NO','ROOM_OPERATIONAL':'NO','scope':'NONEXECUTING_DESIGN'}.items():
            if c.get(key)!=value:raise ValueError('Safety '+key)
        if c.get('schema_sha256')!=hashlib.sha256((HERE/'FIXTURE-SCHEMA.json').read_bytes()).hexdigest() or c.get('generator_sha256')!=hashlib.sha256((HERE/'generate_fixture.py').read_bytes()).hexdigest():raise ValueError('Generator/schema provenance')
        actual=hashlib.sha256(canonical({k:v for k,v in r.items() if k!='fixture_manifest_sha256'})).hexdigest()
        if r['fixture_manifest_sha256']!=actual:raise ValueError('Manifest digest')
        case=next((v for v in cases if v['CASE_ID']==r['case_id']),None)
        if case is None:raise ValueError('Unknown case')
        for field,required in [('ownership_state','REQUIRED_OWNERSHIP_STATE'),('effect_state','REQUIRED_EFFECT_STATE'),('terminal_state','REQUIRED_TERMINAL_STATE'),('reconciliation_state','REQUIRED_RECONCILIATION_STATE')]:
            if r[field]!=case[required]:raise ValueError('Case state '+field)
        for k in r['registry']:
            if k not in r or r[k]!=r['registry'][k]:raise ValueError('Registry identity/revision mismatch '+k)
        if set(r['registry'])!=expected-{'context','registry','model_rows','runtime_evidence','fixture_manifest_sha256'}:raise ValueError('Registry omission')
        flags['FIXTURE_SUCCESSOR_BOUND']=True;flags['MODEL_GENERATION_COMPLETE']=True
        expected_rows={}
        for j in joins:
            for relation,key in [(j['SOURCE_RELATION'],j['SOURCE_KEY']),(j['TARGET_RELATION'],j['TARGET_KEY'])]:expected_rows.setdefault(relation,set()).add(key)
        if set(r['model_rows'])!=set(expected_rows) or any(set(r['model_rows'][n])!=keys for n,keys in expected_rows.items()):raise ValueError('Model row omission/extension')
        for j in joins:
            a=r['model_rows'][j['SOURCE_RELATION']][j['SOURCE_KEY']];b=r['model_rows'][j['TARGET_RELATION']][j['TARGET_KEY']]
            if a is None or b is None or a!=b:raise ValueError('Exact model join '+j['JOIN_ID'])
            for field in [j['SOURCE_KEY'],j['TARGET_KEY']]:
                if field in r and a!=r[field]:raise ValueError('Unbound model join '+j['JOIN_ID'])
        policy=json.loads((HERE/'POLICY-TEST-VALUES.json').read_text());values=[]
        for f in policy['fields']:
            if set(f)!={'NAME','VALUE','UNIT','WHY_REQUIRED','TEST_SCOPE','NOT_PRODUCTION_POLICY'} or f['UNIT']!='microseconds' or f['NOT_PRODUCTION_POLICY']!='YES' or f['TEST_SCOPE']!='DISPOSABLE_DESIGN_ONLY' or type(f['VALUE']) is not int or not 0<f['VALUE']<2**63:raise ValueError('Policy marker/value')
            values.append(f['VALUE'])
        if len(values)!=28 or any(values[i]>values[i+1] for i in range(0,28,2)):raise ValueError('Policy shape')
        v=values[::2]
        if not (all(v[i]<=values[1] for i in [1,2,3]) and v[4]<=v[6] and v[5]<=v[6] and v[7]<=min(v[4:7]) and v[8]<=min(v[5:7]) and v[12]<v[8]):raise ValueError('Frozen policy nesting')
        if r['policy_hash']!=hashlib.sha256(canonical(policy)).hexdigest():raise ValueError('Policy hash')
        flags['MODEL_POLICY_VALID']=True
        def instant(s):
            if not isinstance(s,str) or not re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{6}Z',s):raise ValueError('Time encoding')
            return datetime.datetime.fromisoformat(s.replace('Z','+00:00'))
        now=instant(c['evaluation_time']);issued=instant(r['issued_at']);valid=instant(r['valid_from']);expires=instant(r['expires_at']);receipt=instant(c['receipt_expires_at'])
        if not issued<=valid<=now<expires or not now<receipt<=expires or (expires-valid).total_seconds()*1000000>v[6] or (receipt-now).total_seconds()*1000000>v[13]:raise ValueError('Expired/unbound/non-nested model time')
        flags['MODEL_TIME_VALID']=True
        if r['readiness_state']!='ELIGIBLE_FOR_TEST' or r['watchdog_state']!='SYMBOLIC_ONLY' or r['census_state']!='SYMBOLIC_ONLY' or c['role_oid_source']!='MODEL_ONLY_NOT_PG_ROLES':raise ValueError('Design readiness confused with runtime')
        flags['FIXTURE_STRUCTURALLY_COMPLETE']=True
        if set(r['runtime_evidence'])!={'catalog_roles','installed_history','live_acl','frozen_binding_frame','original_signed_attestation','accepted_consumption','actual_stage_receipts','reconciliation_recomputation','isolated_target_identity','authority_sql_join_coverage'}:raise ValueError('Runtime proof omission/extension')
        # Model equality and JSON booleans cannot independently prove SQL joins,
        # original signatures, committed receipts, catalog identity or health.
        errors.append('RUNTIME_AUTHORITY_AND_READINESS_EVIDENCE_NOT_VALIDATED_BY_THIS_DESIGN_ONLY_VALIDATOR')
    except (ValueError,KeyError,TypeError,OverflowError) as e:
        flags['FIXTURE_STRUCTURALLY_COMPLETE']=False;errors.append(str(e))
    return {**flags,'MODEL_VALID':flags['FIXTURE_STRUCTURALLY_COMPLETE'],'POSITIVE_EXECUTION_ELIGIBLE':False,'errors':errors,'ROOM_OPERATIONAL':'NO'}
