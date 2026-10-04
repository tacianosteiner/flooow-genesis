"""S05/S06 guarded static V041 composition. Source only; no migration execution."""
import re
import package_0090_source_gate as gate
from build_package_0090_q_source import row, raw, deny, literal
from package_0090_typed_transport_source import frozen_tuple, decode, encode, declarations, DECLARATIONS
from build_package_0090_original_match_source import NAME as MATCH

MARKER='-- Public S05/S06: guarded original-bound frozen verification.'
END='-- End public S05/S06.'
OWNER='flooow_offline_verification_owner'
TYPES=('uuid','bytea','uuid','text','uuid','int8','uuid','uuid','bytea','bytea')
BASE_NAMES=('binding_id','plan_fingerprint','expected_incarnation_id','surface_version','attempt_id','generation','execution_id','instance_id','possession_secret')
NAMES={'S05':BASE_NAMES+('envelope',),'S06':BASE_NAMES+('verified_envelope',)}
WRAPPERS={'S05':'offline_begin_verification','S06':'offline_persist_verification'}
FROZEN={'S05':'s2a_begin_attestation_verification','S06':'s2a_persist_attestation_verification_result'}

def instant(value):return 'pg_catalog.int8send((EXTRACT(EPOCH FROM '+value+')*1000000)::pg_catalog.int8)'

def header_fields(source):
    block=source.split('CREATE TABLE public.offline_binding_header (',1)[1].split('\n);',1)[0]
    fields=re.findall(r'^    ([a-z_]+) pg_catalog\.([a-z0-9]+)',block,re.M)
    if len(fields)!=40:raise ValueError('Full immutable header shape')
    return fields

def header_fingerprint(fields):
    payloads=[]
    for name,kind in fields[:38]:
        val='header_record.'+name
        payloads.append('pg_catalog.uuid_send('+val+')' if kind=='uuid' else 'pg_catalog.int4send('+val+')' if kind=='int4' else instant(val) if kind=='timestamptz' else raw(val) if kind=='text' else val)
    return row('BINDING',payloads)

def guard(source):
    p=source.split('AS $offline_p$',1)[1].split('$offline_p$;',1)[0]
    declaration=p.split('BEGIN',1)[0].replace('    principal_found pg_catalog.uuid;\n','')
    body=p.split('BEGIN',1)[1].split('    IF NOT public.command_authorization_organization_lock',1)[0]
    body=body.replace('slot_number=3','slot_number=1')
    body=body.replace("attempt_record.state <> 'EFFECTS_IN_PROGRESS'","attempt_record.state NOT IN ('CLAIMED','EFFECTS_IN_PROGRESS')")
    delivery_start=body.index('    PERFORM d.binding_id FROM public.offline_delivery')
    delivery_end=body.index('    PERFORM r.binding_id FROM public.offline_reconciliation',delivery_start)
    body=body[:delivery_start]+body[delivery_end:]
    body=body.replace("OR pg_catalog.current_setting('transaction_isolation') <> 'read committed' THEN", "OR pg_catalog.current_setting('transaction_isolation') <> 'read committed'\n       OR pg_catalog.current_setting('transaction_read_only') <> 'off' OR $10 IS NULL THEN")
    start=body.index('    SELECT h.binding_id');end=body.index('      INTO header_record',start)
    fields=header_fields(source)
    body=body[:start]+'    SELECT '+','.join('h.'+name for name,kind in fields)+'\n'+body[end:]
    point=body.index('    -- Decode exact canonical slots;')
    body=body[:point]+deny('header_record.plan_fingerprint<>pg_catalog.sha256('+header_fingerprint(fields)+') OR pg_catalog.sha256(header_record.canonical_manifest_bytes)<>header_record.manifest_digest OR header_record.canonical_manifest_hash<>header_record.manifest_digest')+body[point:]
    body+=deny('NOT pg_catalog.isfinite(header_record.issued_at) OR NOT pg_catalog.isfinite(header_record.valid_from) OR NOT pg_catalog.isfinite(header_record.expires_at) OR header_record.valid_from<header_record.issued_at OR header_record.expires_at<=header_record.valid_from OR NOT pg_catalog.isfinite(attempt_record.claimed_at) OR NOT pg_catalog.isfinite(attempt_record.expires_at) OR attempt_record.expires_at<=attempt_record.claimed_at OR attempt_record.claimed_at<header_record.valid_from OR attempt_record.expires_at>header_record.expires_at OR NOT pg_catalog.isfinite(execution_record.claimed_at) OR NOT pg_catalog.isfinite(execution_record.expires_at) OR execution_record.claimed_at<attempt_record.claimed_at OR execution_record.expires_at<=execution_record.claimed_at OR execution_record.expires_at>attempt_record.expires_at OR EXTRACT(EPOCH FROM(attempt_record.expires_at-attempt_record.claimed_at))*1000000>policy_values[9] OR EXTRACT(EPOCH FROM(execution_record.expires_at-execution_record.claimed_at))*1000000>policy_values[11] OR EXTRACT(EPOCH FROM(header_record.expires_at-header_record.valid_from))*1000000>policy_values[13]')
    body+=deny("EXISTS(SELECT 1 FROM public.offline_stage_receipt s WHERE s.binding_id=$1 AND s.attempt_id=$5 AND s.generation=$6 AND s.stage IN ('INITIAL_CREDENTIAL_APPLIED','GRANT_APPLIED','IDENTITY_DECISION_APPLIED'))")
    return declaration,'BEGIN'+body

def final_guard():
    # Control rows stay locked. Fresh catalog/readiness and DB wall clock are
    # re-evaluated after every blocking frozen call, never deadline renewal.
    return '''    SELECT e.binding_id,e.attempt_id,e.generation,e.execution_id,e.instance_id,e.executor_oid,e.state,e.possession_digest,e.claimed_at,e.expires_at INTO STRICT final_execution_record FROM public.offline_execution e WHERE e.binding_id=$1 AND e.attempt_id=$5 AND e.generation=$6 AND e.execution_id=$7 AND e.instance_id=$8;
    SELECT a.binding_id,a.attempt_id,a.generation,a.state,a.claimed_at,a.expires_at INTO STRICT final_attempt_record FROM public.offline_attempt a WHERE a.binding_id=$1 AND a.attempt_id=$5 AND a.generation=$6;
    IF final_execution_record.state<>'OWNED' OR final_execution_record.executor_oid<>slot_oids[3] OR final_execution_record.possession_digest<>pg_catalog.sha256($9) OR final_execution_record.claimed_at IS DISTINCT FROM execution_record.claimed_at OR final_execution_record.expires_at IS DISTINCT FROM execution_record.expires_at OR final_attempt_record.state NOT IN ('CLAIMED','EFFECTS_IN_PROGRESS') OR final_attempt_record.claimed_at IS DISTINCT FROM attempt_record.claimed_at OR final_attempt_record.expires_at IS DISTINCT FROM attempt_record.expires_at OR NOT EXISTS(SELECT 1 FROM public.offline_binding_lifecycle l WHERE l.binding_id=$1 AND l.state='ACTIVE') OR NOT EXISTS(SELECT 1 FROM public.offline_attempt_pointer p WHERE p.binding_id=$1 AND p.current_attempt_id=$5 AND p.generation=$6) THEN
        RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
    END IF;
    SELECT r.deployment_id,r.incarnation_id,r.state,r.policy_version,r.policy_digest,
           r.watchdog_checked_at,r.watchdog_healthy INTO STRICT ready_record
      FROM public.offline_readiness r WHERE r.deployment_id=header_record.deployment_id AND r.incarnation_id=$3;
    database_now := pg_catalog.clock_timestamp();
'''+deny("ready_record.state<>'READY' OR ready_record.policy_version<>policy_record.policy_version OR ready_record.policy_digest<>policy_record.policy_digest OR ready_record.watchdog_healthy IS NOT TRUE OR NOT pg_catalog.isfinite(database_now) OR NOT pg_catalog.isfinite(ready_record.watchdog_checked_at) OR database_now<ready_record.watchdog_checked_at OR database_now>=header_record.expires_at OR database_now>=attempt_record.expires_at OR database_now>=execution_record.expires_at OR EXTRACT(EPOCH FROM(database_now-ready_record.watchdog_checked_at))*1000000>policy_values[23] OR EXTRACT(EPOCH FROM(database_now-pg_catalog.transaction_timestamp()))*1000000>policy_values[1]")

def original_manifest(fields):
    values=[literal('FLOOOW:S2A:APPROVAL-MANIFEST:1')]
    for name,kind in fields[:22]:
        value='input_'+name
        if kind=='timestamptz':value="pg_catalog.to_char("+value+" AT TIME ZONE 'UTC','YYYY-MM-DD\"T\"HH24:MI:SS.US\"Z\"')"
        elif kind!='text':value+='::pg_catalog.text'
        values.append(value)
    return '||'.join('pg_catalog.int4send(pg_catalog.octet_length('+raw(value)+'))||'+raw(value) for value in values)

def grants(spec):
    return {('public',FROZEN[stage],tuple(t for n,t in frozen_tuple(spec,stage,'INPUT')),OWNER) for stage in ('S05','S06')}

def build_one(source,spec,stage):
    inputs=frozen_tuple(spec,stage,'INPUT');outputs=frozen_tuple(spec,stage,'OUTPUT')
    decl,body=guard(source)
    decl+=DECLARATIONS+declarations(inputs)+'''    snapshot record;
    result record;
    prior_receipt record;
    final_execution_record record;
    final_attempt_record record;
    output_bytes pg_catalog.bytea;
    original_match pg_catalog.bool;
'''
    body+=decode('$10',stage,inputs)
    bound={'p_schema_version':'1','p_canonicalization_version':'1','p_canonical_manifest_bytes':'header_record.canonical_manifest_bytes','p_manifest_digest':"pg_catalog.encode(header_record.manifest_digest,'hex')"}
    for field in ['manifest_id','organization_id','mercado_livre_connection_id','omie_connection_id','marketplace_order_id','source_order_reference','integration_reference','permission','reason','provenance','correlation_id']:bound['p_'+field]='header_record.'+field
    body+=deny(' OR '.join('input_'+name+' IS DISTINCT FROM '+value for name,value in bound.items()))
    body+=deny(original_manifest(inputs)+'<>header_record.canonical_manifest_bytes')
    body+='    original_match := public.'+MATCH+'($1,$2,$3,$4,input_p_manifest_digest,input_p_algorithm_id,input_p_signer_key_id,input_p_signer_key_fingerprint,input_p_signature_bytes);\n'+deny('original_match IS NOT TRUE')
    args=lambda fields:','.join('input_'+n+'::pg_catalog.'+t for n,t in fields)
    begin_outputs=frozen_tuple(spec,'S05','OUTPUT')
    body+='    SELECT '+','.join('v.'+n for n,t in begin_outputs)+' INTO STRICT snapshot FROM public.s2a_begin_attestation_verification('+args(inputs[:29])+') v;\n'
    body+=deny('pg_catalog.num_nonnulls('+','.join('snapshot.'+n for n,t in begin_outputs)+')<>'+str(len(begin_outputs)))
    body+=deny("snapshot.outcome NOT IN ('VERIFY_NEW','VERIFY_REPLAY') OR snapshot.result_canonical_manifest_bytes<>header_record.canonical_manifest_bytes OR snapshot.result_manifest_digest<>input_p_manifest_digest OR snapshot.result_signer_key_id<>input_p_signer_key_id OR snapshot.result_signer_key_fingerprint<>input_p_signer_key_fingerprint OR public.offline_internal_canonical_spki_ed25519_verify(snapshot.result_subject_public_key_info_der,snapshot.result_canonical_signature_preimage_bytes,input_p_signature_bytes) IS NOT TRUE")
    body+=final_guard()
    if stage=='S05':
        body+='    SELECT '+','.join('snapshot.'+n for n,t in outputs)+' INTO result;\n'
    else:
        body+='    SELECT '+','.join('v.'+n for n,t in outputs)+' INTO STRICT result FROM public.'+FROZEN[stage]+'('+args(inputs)+') v;\n'
        body+=deny('pg_catalog.num_nonnulls('+','.join('result.'+n for n,t in outputs)+')<>'+str(len(outputs)))
        body+=deny("result.outcome NOT IN ('ACCEPTED','ALREADY_ACCEPTED') OR result.result_organization_id<>header_record.organization_id OR result.result_manifest_id<>header_record.manifest_id OR result.result_manifest_digest<>input_p_manifest_digest")
        body+=final_guard()
    body+='    output_bytes := '+encode(stage,outputs)+';\n'
    if stage=='S06':
        # Original successful receipt identity and time survive a live replay;
        # outcome is a frozen classification, not part of immutable stage identity.
        accepted=encode('S06',outputs).replace('pg_catalog.convert_to(result.outcome,',"pg_catalog.convert_to('ACCEPTED',")
        replay=encode('S06',outputs).replace('pg_catalog.convert_to(result.outcome,',"pg_catalog.convert_to('ALREADY_ACCEPTED',")
        body+='''    SELECT s.binding_id,s.attempt_id,s.generation,s.execution_id,s.instance_id,s.stage,
               s.receipt_id,s.operation_id,s.frozen_receipt,s.effect_time INTO prior_receipt
          FROM public.offline_stage_receipt s WHERE s.binding_id=$1 AND s.attempt_id=$5 AND s.generation=$6 AND s.stage='ATTESTATION_VERIFIED';
    IF FOUND THEN
'''+deny('prior_receipt.execution_id<>$7 OR prior_receipt.instance_id<>$8 OR prior_receipt.operation_id IS NOT NULL OR (prior_receipt.frozen_receipt<>'+accepted+' AND prior_receipt.frozen_receipt<>'+replay+') OR prior_receipt.effect_time<>result.result_verified_at')+'''    ELSE
        INSERT INTO public.offline_stage_receipt(binding_id,attempt_id,generation,execution_id,instance_id,stage,receipt_id,operation_id,frozen_receipt,effect_time)
          VALUES($1,$5,$6,$7,$8,'ATTESTATION_VERIFIED',pg_catalog.gen_random_uuid(),NULL,output_bytes,result.result_verified_at);
    END IF;
    UPDATE public.offline_attempt a SET state='EFFECTS_IN_PROGRESS'
     WHERE a.binding_id=$1 AND a.attempt_id=$5 AND a.generation=$6 AND a.state='CLAIMED';
'''
    body+=final_guard()+'    RETURN output_bytes;\n'
    body+="EXCEPTION WHEN OTHERS THEN\n    RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';\nEND;\n"
    signature=','.join('pg_catalog.'+t for t in TYPES);name=WRAPPERS[stage]
    return 'CREATE FUNCTION public.'+name+'(\n    '+',\n    '.join(n+' pg_catalog.'+t for n,t in zip(NAMES[stage],TYPES))+'''
) RETURNS pg_catalog.bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER CALLED ON NULL INPUT
SET search_path=pg_catalog,pg_temp
AS $offline_'''+stage.lower()+'$\n'+decl+body+'$offline_'+stage.lower()+'$;\nALTER FUNCTION public.'+name+'('+signature+') OWNER TO '+OWNER+';\nREVOKE ALL ON FUNCTION public.'+name+'('+signature+') FROM PUBLIC;\n'

def build(source,spec):
    sql=MARKER+'\n'+''.join(build_one(source,spec,stage) for stage in ('S05','S06'))
    for schema,name,types,owner in sorted(grants(spec)):
        sql+='GRANT EXECUTE ON FUNCTION '+schema+'.'+name+'('+','.join('pg_catalog.'+t for t in types)+') TO '+owner+';\n'
    return sql+END+'\n'

def install():
    path=gate.ROOT/gate.V043;source=path.read_text(encoding='utf-8-sig');spec=(gate.ROOT/gate.SPEC).read_text(encoding='utf-8-sig')
    if MARKER in source:
        start=source.index(MARKER);end=source.index(END,start)+len(END)
        source=source[:start]+build(source,spec).rstrip()+source[end:]
    else:source+='\n'+build(source,spec)
    path.write_text(source,encoding='utf-8')

if __name__=='__main__':install()
