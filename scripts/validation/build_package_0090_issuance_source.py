"""S07-S12 exact bound V042 issuance composition, inline codecs only."""
import package_0090_source_gate as gate
from build_package_0090_q_source import deny
from build_package_0090_verification_source import guard,final_guard,original_manifest
from package_0090_typed_transport_source import frozen_tuple,decode,encode,declarations,DECLARATIONS

MARKER='-- Public S07-S12: guarded durable verification lineage and frozen issuance.'
END='-- End public S07-S12.'
OWNER='flooow_offline_issuance_owner'
TYPES=('uuid','bytea','uuid','text','uuid','int8','uuid','uuid','bytea','bytea')
NAMES=('binding_id','plan_fingerprint','expected_incarnation_id','surface_version','attempt_id','generation','execution_id','instance_id','possession_secret','envelope')
WRAPPERS={'S07':'offline_begin_principal','S08':'offline_apply_principal','S09':'offline_begin_initial_credential','S10':'offline_apply_initial_credential','S11':'offline_begin_permission_grant','S12':'offline_apply_permission_grant'}
FROZEN={'S07':'s2a_v042_begin_attested_principal_verification','S08':'s2a_v042_apply_attested_principal','S09':'s2a_v042_begin_attested_initial_credential_verification','S10':'s2a_v042_apply_attested_initial_credential','S11':'s2a_v042_begin_attested_grant_verification','S12':'s2a_v042_apply_attested_grant'}
STAGES={'S07':'PRINCIPAL_APPLIED','S08':'PRINCIPAL_APPLIED','S09':'INITIAL_CREDENTIAL_APPLIED','S10':'INITIAL_CREDENTIAL_APPLIED','S11':'GRANT_APPLIED','S12':'GRANT_APPLIED'}

def grants(spec):return {('public',FROZEN[s],tuple(t for n,t in frozen_tuple(spec,s,'INPUT')),OWNER) for s in WRAPPERS}

def build_one(source,spec,stage):
    inputs=frozen_tuple(spec,stage,'INPUT');outputs=frozen_tuple(spec,stage,'OUTPUT')
    begin_stage='S'+format(int(stage[1:])-1,'02d') if int(stage[1:])%2==0 else stage
    apply=int(stage[1:])%2==0
    category='PRINCIPAL' if stage in ('S07','S08') else 'INITIAL_CREDENTIAL' if stage in ('S09','S10') else 'GRANT'
    operation={'PRINCIPAL':'principal_operation_id','INITIAL_CREDENTIAL':'credential_operation_id','GRANT':'grant_operation_id'}[category]
    decl,body=guard(source)
    body=body.split('    IF EXISTS(SELECT 1 FROM public.offline_stage_receipt',1)[0]
    body=body.replace('slot_number=1','slot_number=2').replace("attempt_record.state NOT IN ('CLAIMED','EFFECTS_IN_PROGRESS')","attempt_record.state<>'EFFECTS_IN_PROGRESS'")
    decl+=DECLARATIONS+declarations(inputs)+declarations(frozen_tuple(spec,'S06','OUTPUT'),'verified_')+'''    verification_receipt record;
    dependency_receipt record;
    delivery_record record;
    snapshot record;
    result record;
    prior_receipt record;
    final_execution_record record;
    final_attempt_record record;
    output_bytes pg_catalog.bytea;
    stage_receipt_id pg_catalog.uuid;
'''
    stage_columns='s.binding_id,s.attempt_id,s.generation,s.execution_id,s.instance_id,s.stage,s.receipt_id,s.operation_id,s.frozen_receipt,s.effect_time'
    body+='    SELECT '+stage_columns+" INTO STRICT verification_receipt FROM public.offline_stage_receipt s WHERE s.binding_id=$1 AND s.attempt_id=$5 AND s.generation=$6 AND s.stage='ATTESTATION_VERIFIED';\n"
    body+=deny('verification_receipt.execution_id<>$7 OR verification_receipt.instance_id<>$8 OR verification_receipt.operation_id IS NOT NULL')
    body+=decode('verification_receipt.frozen_receipt','S06',frozen_tuple(spec,'S06','OUTPUT'),'verified_',direction='OUTPUT')
    body+=deny("verified_outcome NOT IN ('ACCEPTED','ALREADY_ACCEPTED') OR verified_result_organization_id<>header_record.organization_id OR verified_result_manifest_id<>header_record.manifest_id OR verified_result_manifest_digest<>pg_catalog.encode(header_record.manifest_digest,'hex') OR verified_result_verified_at<>verified_result_recorded_at OR verification_receipt.effect_time<>verified_result_verified_at")
    required=['PRINCIPAL_APPLIED'] if category=='INITIAL_CREDENTIAL' else ['PRINCIPAL_APPLIED','INITIAL_CREDENTIAL_APPLIED'] if category=='GRANT' else []
    for needed in required:
        op='principal_operation_id' if needed=='PRINCIPAL_APPLIED' else 'credential_operation_id'
        body+='    SELECT '+stage_columns+' INTO STRICT dependency_receipt FROM public.offline_stage_receipt s WHERE s.binding_id=$1 AND s.attempt_id=$5 AND s.generation=$6 AND s.stage=\''+needed+"';\n"+deny('dependency_receipt.execution_id<>$7 OR dependency_receipt.instance_id<>$8 OR dependency_receipt.operation_id IS DISTINCT FROM header_record.'+op)
    if category!='PRINCIPAL':
        body+='''    SELECT d.binding_id,d.attempt_id,d.generation,d.execution_id,d.instance_id,d.credential_id,d.initial_operation_id,d.fresh_applied_receipt_id,d.state
      INTO STRICT delivery_record FROM public.offline_delivery d WHERE d.binding_id=$1 FOR UPDATE;
'''
        if category=='GRANT':
            body+=deny("delivery_record.state<>'DELIVERY_ACKNOWLEDGED' OR delivery_record.attempt_id IS DISTINCT FROM $5 OR delivery_record.generation<>$6 OR delivery_record.execution_id IS DISTINCT FROM $7 OR delivery_record.instance_id IS DISTINCT FROM $8 OR delivery_record.credential_id IS DISTINCT FROM header_record.credential_id OR delivery_record.initial_operation_id IS DISTINCT FROM header_record.credential_operation_id OR delivery_record.fresh_applied_receipt_id IS DISTINCT FROM dependency_receipt.receipt_id")
        else:
            body+=deny("delivery_record.generation<>$6 OR delivery_record.state NOT IN ('NOT_CREATED','CREATED_NOT_DELIVERABLE') OR (delivery_record.state='CREATED_NOT_DELIVERABLE' AND (delivery_record.attempt_id IS DISTINCT FROM $5 OR delivery_record.execution_id IS DISTINCT FROM $7 OR delivery_record.instance_id IS DISTINCT FROM $8 OR delivery_record.credential_id IS DISTINCT FROM header_record.credential_id OR delivery_record.initial_operation_id IS DISTINCT FROM header_record.credential_operation_id))")
    forbidden=['INITIAL_CREDENTIAL_APPLIED','GRANT_APPLIED','IDENTITY_DECISION_APPLIED'] if category=='PRINCIPAL' else ['GRANT_APPLIED','IDENTITY_DECISION_APPLIED'] if category=='INITIAL_CREDENTIAL' else ['IDENTITY_DECISION_APPLIED']
    body+=deny("EXISTS(SELECT 1 FROM public.offline_stage_receipt s WHERE s.binding_id=$1 AND s.attempt_id=$5 AND s.generation=$6 AND s.stage IN ("+','.join("'"+s+"'" for s in forbidden)+'))')
    body+=decode('$10',stage,inputs)
    bound={}
    for field in ['organization_id','manifest_id','principal_id','mercado_livre_connection_id','omie_connection_id','source_order_reference','integration_reference','marketplace_order_id','permission','reason','provenance','correlation_id','credential_id','grant_id']:
        if any(n=='p_'+field for n,t in inputs):bound['p_'+field]='header_record.'+field
    bound.update(p_operation_id='header_record.'+operation,p_claim_manifest_id='header_record.manifest_id',p_claim_organization_id='header_record.organization_id',p_schema_version='1')
    body+=deny(' OR '.join('input_'+n+' IS DISTINCT FROM '+v for n,v in bound.items()))
    body+=deny(original_manifest(frozen_tuple(spec,'S05','INPUT'))+'<>header_record.canonical_manifest_bytes')
    begin_inputs=frozen_tuple(spec,begin_stage,'INPUT');begin_outputs=frozen_tuple(spec,begin_stage,'OUTPUT')
    args=lambda fields:','.join('input_'+n for n,t in fields)
    body+='    SELECT '+','.join('v.'+n for n,t in begin_outputs)+' INTO STRICT snapshot FROM public.'+FROZEN[begin_stage]+'('+args(begin_inputs)+') v;\n'
    body+=deny("snapshot.outcome NOT IN ('READY','ALREADY_APPLIED') OR snapshot.result_operation_id IS DISTINCT FROM header_record."+operation+' OR snapshot.result_manifest_digest IS DISTINCT FROM verified_result_manifest_digest OR snapshot.result_accepted_proof_fingerprint IS DISTINCT FROM verified_result_accepted_proof_fingerprint OR snapshot.result_verified_at IS DISTINCT FROM verified_result_verified_at OR snapshot.result_canonical_manifest_bytes IS DISTINCT FROM header_record.canonical_manifest_bytes')
    body+=final_guard()
    if apply:
        body+='    SELECT '+','.join('v.'+n for n,t in outputs)+' INTO STRICT result FROM public.'+FROZEN[stage]+'('+args(inputs)+') v;\n'
        body+=deny("result.outcome NOT IN ('APPLIED','ALREADY_APPLIED') OR result.result_operation_id IS DISTINCT FROM header_record."+operation+' OR pg_catalog.num_nonnulls('+','.join('result.'+n for n,t in outputs)+')<>'+str(len(outputs)))+final_guard()
    else:body+='    SELECT '+','.join('snapshot.'+n for n,t in outputs)+' INTO result;\n'
    body+='    output_bytes := '+encode(stage,outputs)+';\n'
    if apply:
        body+='    SELECT '+stage_columns+' INTO prior_receipt FROM public.offline_stage_receipt s WHERE s.binding_id=$1 AND s.attempt_id=$5 AND s.generation=$6 AND s.stage=\''+STAGES[stage]+"';\n    IF FOUND THEN\n"
        applied=encode(stage,outputs).replace('pg_catalog.convert_to(result.outcome,',"pg_catalog.convert_to('APPLIED',")
        replay=encode(stage,outputs).replace('pg_catalog.convert_to(result.outcome,',"pg_catalog.convert_to('ALREADY_APPLIED',")
        body+=deny('prior_receipt.execution_id<>$7 OR prior_receipt.instance_id<>$8 OR prior_receipt.operation_id IS DISTINCT FROM header_record.'+operation+' OR (prior_receipt.frozen_receipt<>'+applied+' AND prior_receipt.frozen_receipt<>'+replay+') OR prior_receipt.effect_time IS DISTINCT FROM result.result_effect_time')
        body+='    stage_receipt_id := prior_receipt.receipt_id;\n    ELSE\n'
        if stage=='S10':body+=deny("result.outcome<>'APPLIED' OR delivery_record.state<>'NOT_CREATED'")
        body+='    stage_receipt_id := pg_catalog.gen_random_uuid();\n    INSERT INTO public.offline_stage_receipt(binding_id,attempt_id,generation,execution_id,instance_id,stage,receipt_id,operation_id,frozen_receipt,effect_time) VALUES($1,$5,$6,$7,$8,\''+STAGES[stage]+"',stage_receipt_id,header_record."+operation+',output_bytes,result.result_effect_time);\n    END IF;\n'
        if stage=='S10':
            body+='''    IF delivery_record.state='NOT_CREATED' THEN
'''+deny("result.outcome<>'APPLIED'")+'''        UPDATE public.offline_delivery d SET attempt_id=$5,execution_id=$7,instance_id=$8,credential_id=header_record.credential_id,initial_operation_id=header_record.credential_operation_id,fresh_applied_receipt_id=stage_receipt_id,state='CREATED_NOT_DELIVERABLE' WHERE d.binding_id=$1 AND d.generation=$6 AND d.state='NOT_CREATED';
        IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED'; END IF;
    ELSE
'''+deny('delivery_record.fresh_applied_receipt_id IS DISTINCT FROM stage_receipt_id')+'    END IF;\n'
    body+=final_guard()+'    RETURN output_bytes;\nEXCEPTION WHEN OTHERS THEN\n    RAISE EXCEPTION USING ERRCODE=\'P0017\',MESSAGE=\'ACCESS_DENIED\';\nEND;\n'
    name=WRAPPERS[stage];signature=','.join('pg_catalog.'+t for t in TYPES)
    return 'CREATE FUNCTION public.'+name+'(\n    '+',\n    '.join(n+' pg_catalog.'+t for n,t in zip(NAMES,TYPES))+') RETURNS pg_catalog.bytea\nLANGUAGE plpgsql VOLATILE SECURITY DEFINER CALLED ON NULL INPUT\nSET search_path=pg_catalog,pg_temp\nAS $offline_'+stage.lower()+'$\n'+decl+body+'$offline_'+stage.lower()+'$;\nALTER FUNCTION public.'+name+'('+signature+') OWNER TO '+OWNER+';\nREVOKE ALL ON FUNCTION public.'+name+'('+signature+') FROM PUBLIC;\n'

def build(source,spec):
    code=MARKER+'\n'+''.join(build_one(source,spec,s) for s in WRAPPERS)
    for schema,name,types,owner in sorted(grants(spec)):code+='GRANT EXECUTE ON FUNCTION public.'+name+'('+','.join('pg_catalog.'+t for t in types)+') TO '+owner+';\n'
    return code+'GRANT USAGE ON SCHEMA public TO '+OWNER+';\n'+END+'\n'

def install():
    p=gate.ROOT/gate.V043;source=p.read_text();spec=(gate.ROOT/gate.SPEC).read_text()
    if MARKER in source:
        start=source.index(MARKER);end=source.index(END,start)+len(END);source=source[:start]+build(source,spec).rstrip()+source[end:]
    else:source+='\n'+build(source,spec)
    p.write_text(source,encoding='utf-8')

if __name__=='__main__':install()
