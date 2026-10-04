"""Closed S13-S16 control wrappers; no production execution/provisioning."""
import re
import package_0090_source_gate as gate
from build_package_0090_verification_source import guard as v_guard,final_guard
from build_package_0090_q_source import deny
from package_0090_typed_transport_source import decode,encode,declarations,DECLARATIONS,frozen_tuple

OWNER='flooow_offline_execution_owner'
MARKER='-- Public S13-S16: exclusive claim, delivery and durable admission.'
END='-- End public S13-S16.'
BASE_TYPES=('uuid','bytea','uuid','text','uuid','int8','uuid','uuid','bytea')
BASE_NAMES=('binding_id','plan_fingerprint','expected_incarnation_id','surface_version','attempt_id','generation','execution_id','instance_id','possession_secret')
TYPES={'S13':('uuid','bytea','uuid','text','int8','uuid','uuid','bytea','bytea'),'S14':BASE_TYPES+('uuid','uuid','uuid'),'S15':BASE_TYPES+('uuid','text','timestamptz','text'),'S16':BASE_TYPES+('uuid','int4','bytea')}
NAMES={'S13':('binding_id','plan_fingerprint','expected_incarnation_id','surface_version','expected_generation','execution_id','instance_id','possession_secret','preflight_receipt'),'S14':BASE_NAMES+('credential_id','initial_operation_id','fresh_applied_receipt_id'),'S15':BASE_NAMES+('delivery_receipt_id','delivery_outcome','delivery_observed_at','delivery_observation_code'),'S16':BASE_NAMES+('credential_id','credential_revision','derived_credential_proof')}
WRAPPERS={'S13':'offline_claim_attempt','S14':'offline_claim_attempt','S15':'offline_claim_attempt','S16':'offline_authenticate_command'}
FROZEN={'P':'offline_lock_bound_principal','Q':'offline_internal_readiness','FP':'transaction_identity_grant_fingerprint','HASH':'transaction_identity_hash'}
GRANTS={('public','transaction_identity_grant_fingerprint',('uuid','uuid'),OWNER),('public','transaction_identity_hash',('text[]',),OWNER)}
PF_FIELDS=[('incarnation','uuid'),('binding_fingerprint','bytea'),('surface','text'),('history_digest','bytea'),('acl_digest','bytea'),('policy_digest','bytea'),('issued_at','timestamptz'),('expires_at','timestamptz'),('key_version','u32')]

def outputs(spec,stage):
    section=spec.split('WRAPPER='+stage+' ',1)[1].split('WRAPPER=',1)[0].split('S13 acknowledgment retry',1)[0]
    rows=re.findall(r'^\| (\d+) \| ([a-z_]+) \| pg_catalog\.([a-z0-9]+) \|',section,re.M)
    expected={'S13':8,'S14':9,'S15':5,'S16':8}[stage]
    if len(rows)!=expected:raise ValueError('Closed '+stage+' output matrix')
    return [(name,kind) for tag,name,kind in rows]

def initial(types):
    cond=[]
    for i,t in enumerate(types,1):
        cond.append('$'+str(i)+' IS NULL')
        if t=='uuid':cond.append('$'+str(i)+"='00000000-0000-0000-0000-000000000000'::pg_catalog.uuid")
        if t in ('int4','int8'):cond.append('$'+str(i)+'<=0')
        if t=='timestamptz':cond.append('NOT pg_catalog.isfinite($'+str(i)+')')
    cond += ["$4<>'0090-v1'","pg_catalog.octet_length($2)<>32","pg_catalog.current_setting('transaction_isolation')<>'read committed'","pg_catalog.current_setting('transaction_read_only')<>'off'"]
    return 'BEGIN\n'+deny(' OR '.join(cond))

def mutable_guard(source,types=BASE_TYPES):
    decl,body=v_guard(source);body=body.split('    IF EXISTS(SELECT 1 FROM public.offline_stage_receipt',1)[0]
    body=body[body.index('    SELECT h.binding_schema_version'):].replace('slot_number=1','slot_number=3').replace("attempt_record.state NOT IN ('CLAIMED','EFFECTS_IN_PROGRESS')","attempt_record.state<>'EFFECTS_IN_PROGRESS'")
    return decl,initial(types)+deny('pg_catalog.octet_length($9)<>32')+body

def claim_guard(source):
    decl,body=v_guard(source)
    body=body[body.index('    SELECT h.binding_schema_version'):].split('    -- C:',1)[0].replace('slot_number=1','slot_number=3')
    return decl,initial(TYPES['S13'])+deny('pg_catalog.octet_length($8)<>32 OR pg_catalog.octet_length($9)<=32')+body

EXTRA='''    result record;
    delivery_record record;
    admission_record record;
    credential_record record;
    grant_record record;
    fresh_receipt record;
    final_execution_record record;
    final_attempt_record record;
    server_attempt_id pg_catalog.uuid;
    server_receipt_id pg_catalog.uuid;
    permission_to_attempt pg_catalog.bool;
    authorization_fingerprint pg_catalog.bytea;
    new_claim pg_catalog.bool;
    new_admission pg_catalog.bool;
'''

DELIVERY_COLUMNS=('binding_id','attempt_id','generation','execution_id','instance_id','credential_id','initial_operation_id','fresh_applied_receipt_id','state','delivery_receipt_id','attempted_at','operation_deadline','observed_at','observation_code','recorded_at')
ADMISSION_COLUMNS=('admission_id','deployment_id','incarnation_id','binding_id','attempt_id','generation','execution_id','instance_id','executor_oid','credential_id','credential_revision','principal_id','organization_id','grant_id','grant_revision','authorization_fingerprint','permission','authenticated_at','expires_at','durable_state','consumed_decision_id','consumed_at')

def delivery_lock():return '    SELECT '+','.join('d.'+c for c in DELIVERY_COLUMNS)+' INTO STRICT delivery_record FROM public.offline_delivery d WHERE d.binding_id=$1 FOR UPDATE;\n'

def delivery_origin():return deny("delivery_record.attempt_id IS DISTINCT FROM $5 OR delivery_record.generation<>$6 OR delivery_record.execution_id IS DISTINCT FROM $7 OR delivery_record.instance_id IS DISTINCT FROM $8 OR delivery_record.credential_id IS DISTINCT FROM header_record.credential_id OR delivery_record.initial_operation_id IS DISTINCT FROM header_record.credential_operation_id")

def current_authority(proof=False,lock=True,check_head=True):
    code=('''    IF public.offline_lock_bound_principal($1,$2,$3,$4,$5,$6,$7,$8,$9) IS NOT TRUE THEN
        RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
    END IF;
''' if lock else '')+'''    SELECT c.organization_id,c.principal_id,c.credential_id,c.revision,c.state'''+(',c.secret_verifier' if proof else '')+''' INTO STRICT credential_record
      FROM public.command_credential_revision c JOIN public.command_principal p
        ON p.organization_id=c.organization_id AND p.principal_id=c.principal_id
     WHERE c.organization_id=header_record.organization_id AND c.principal_id=header_record.principal_id
       AND c.credential_id=header_record.credential_id AND c.revision=1 AND c.state='ENABLED'
       AND p.mercado_livre_connection_id=header_record.mercado_livre_connection_id AND p.omie_connection_id=header_record.omie_connection_id
       AND NOT EXISTS(SELECT 1 FROM public.command_credential_revision n WHERE n.organization_id=c.organization_id AND n.credential_id=c.credential_id AND n.revision>c.revision);
    SELECT g.organization_id,g.principal_id,g.grant_id,g.revision,g.permission,g.state INTO STRICT grant_record
      FROM public.command_permission_grant g WHERE g.organization_id=header_record.organization_id AND g.principal_id=header_record.principal_id
       AND g.grant_id=header_record.grant_id AND g.revision=1 AND g.permission=header_record.permission AND g.state='ENABLED'
       AND NOT EXISTS(SELECT 1 FROM public.command_permission_grant n WHERE n.organization_id=g.organization_id AND n.principal_id=g.principal_id AND n.permission=g.permission AND (n.revision>g.revision OR n.grant_id<>g.grant_id));
    authorization_fingerprint := pg_catalog.decode(public.transaction_identity_grant_fingerprint(header_record.organization_id,header_record.grant_id),'hex');
'''
    if proof:code+=deny('credential_record.credential_id IS DISTINCT FROM $10 OR credential_record.revision<>$11 OR pg_catalog.octet_length(credential_record.secret_verifier)<>32 OR credential_record.secret_verifier IS DISTINCT FROM $12')
    code+=deny("NOT EXISTS(SELECT 1 FROM public.integration_organization o WHERE o.organization_id=header_record.organization_id AND o.status='ACTIVE')")
    if check_head:code+=deny("EXISTS(SELECT 1 FROM public.marketplace_transaction_identity_decision d WHERE d.organization_id=header_record.organization_id AND d.decision_id=header_record.decision_id) OR EXISTS(SELECT 1 FROM public.marketplace_transaction_identity_head h WHERE h.organization_id=header_record.organization_id AND h.omie_connection_id=header_record.omie_connection_id AND h.source_order_reference=header_record.source_order_reference AND h.marketplace_order_id=header_record.marketplace_order_id)")
    return code+deny('pg_catalog.octet_length(authorization_fingerprint)<>32')

def durable_lineage(spec):
    """E consumes V/I receipts, never the original-input relation or verifier."""
    decl=declarations(frozen_tuple(spec,'S06','OUTPUT'),'verified_')+'    lineage_receipt record;\n'
    columns='s.binding_id,s.attempt_id,s.generation,s.execution_id,s.instance_id,s.stage,s.receipt_id,s.operation_id,s.frozen_receipt,s.effect_time'
    code=''
    for stage,operation in [('ATTESTATION_VERIFIED',None),('PRINCIPAL_APPLIED','principal_operation_id'),('INITIAL_CREDENTIAL_APPLIED','credential_operation_id'),('GRANT_APPLIED','grant_operation_id')]:
        code+='    SELECT '+columns+" INTO STRICT lineage_receipt FROM public.offline_stage_receipt s WHERE s.binding_id=$1 AND s.attempt_id=$5 AND s.generation=$6 AND s.stage='"+stage+"';\n"
        code+=deny('lineage_receipt.execution_id IS DISTINCT FROM $7 OR lineage_receipt.instance_id IS DISTINCT FROM $8 OR '+('lineage_receipt.operation_id IS NOT NULL' if operation is None else 'lineage_receipt.operation_id IS DISTINCT FROM header_record.'+operation))
        if operation is None:
            code+=decode('lineage_receipt.frozen_receipt','S06',frozen_tuple(spec,'S06','OUTPUT'),'verified_',direction='OUTPUT')
            code+=deny("verified_outcome NOT IN ('ACCEPTED','ALREADY_ACCEPTED') OR verified_result_organization_id IS DISTINCT FROM header_record.organization_id OR verified_result_manifest_id IS DISTINCT FROM header_record.manifest_id OR verified_result_manifest_digest IS DISTINCT FROM pg_catalog.encode(header_record.manifest_digest,'hex') OR verified_result_verified_at IS DISTINCT FROM verified_result_recorded_at OR lineage_receipt.effect_time IS DISTINCT FROM verified_result_verified_at")
        elif stage=='INITIAL_CREDENTIAL_APPLIED':
            code+=deny('lineage_receipt.receipt_id IS DISTINCT FROM delivery_record.fresh_applied_receipt_id')
    return decl,code

def admission_valid():
    return deny("admission_record.deployment_id IS DISTINCT FROM header_record.deployment_id OR admission_record.incarnation_id IS DISTINCT FROM $3 OR admission_record.binding_id IS DISTINCT FROM $1 OR admission_record.attempt_id IS DISTINCT FROM $5 OR admission_record.generation<>$6 OR admission_record.execution_id IS DISTINCT FROM $7 OR admission_record.instance_id IS DISTINCT FROM $8 OR admission_record.executor_oid<>slot_oids[3] OR admission_record.credential_id IS DISTINCT FROM header_record.credential_id OR admission_record.credential_revision<>credential_record.revision OR admission_record.principal_id IS DISTINCT FROM header_record.principal_id OR admission_record.organization_id IS DISTINCT FROM header_record.organization_id OR admission_record.grant_id IS DISTINCT FROM header_record.grant_id OR admission_record.grant_revision<>grant_record.revision OR admission_record.authorization_fingerprint IS DISTINCT FROM authorization_fingerprint OR admission_record.permission IS DISTINCT FROM header_record.permission OR admission_record.durable_state<>'ISSUED' OR admission_record.consumed_decision_id IS NOT NULL OR admission_record.consumed_at IS NOT NULL OR NOT pg_catalog.isfinite(admission_record.authenticated_at) OR NOT pg_catalog.isfinite(admission_record.expires_at) OR admission_record.authenticated_at>database_now OR admission_record.expires_at<=database_now OR admission_record.expires_at>LEAST(header_record.expires_at,attempt_record.expires_at,execution_record.expires_at)")

def q_claim():return 'public.offline_internal_readiness($1,$2,$3,$4,receipt_history_digest,receipt_acl_digest,receipt_policy_digest,$9)'

def build_one(source,spec,stage):
    decl,body=claim_guard(source) if stage=='S13' else mutable_guard(source,TYPES[stage])
    decl+=EXTRA+DECLARATIONS
    if stage=='S13':
        decl+=declarations(PF_FIELDS,'receipt_')
        body+=decode('pg_catalog.substring($9,1,pg_catalog.octet_length($9)-32)','PREFLIGHT',PF_FIELDS,'receipt_',domain_override='FLOOOW/OFFLINE-FIELD-PROOF/PREFLIGHT/V1')
        body+=deny('receipt_incarnation IS DISTINCT FROM $3 OR receipt_binding_fingerprint IS DISTINCT FROM $2 OR receipt_surface IS DISTINCT FROM $4 OR receipt_policy_digest IS DISTINCT FROM header_record.deadline_policy_digest OR receipt_key_version<=0 OR '+q_claim()+' IS DISTINCT FROM $9')
        body+='''    PERFORM l.binding_id FROM public.offline_binding_lifecycle l WHERE l.binding_id=$1 AND l.state='ACTIVE' FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED'; END IF;
    SELECT p.binding_id,p.current_attempt_id,p.generation,p.claim_permitted INTO STRICT pointer_record FROM public.offline_attempt_pointer p WHERE p.binding_id=$1 FOR UPDATE;
'''+deny('pointer_record.generation<>$5')+'''
    new_claim := pointer_record.current_attempt_id IS NULL;
    database_now := pg_catalog.clock_timestamp();
'''+deny("NOT pg_catalog.isfinite(database_now) OR database_now<header_record.valid_from OR database_now>=header_record.expires_at OR database_now<policy_record.effective_from OR receipt_issued_at>database_now OR receipt_expires_at<=database_now OR EXTRACT(EPOCH FROM(database_now-pg_catalog.transaction_timestamp()))*1000000>policy_values[1]")+'''
    IF new_claim THEN
'''+deny('pointer_record.claim_permitted IS NOT TRUE')+'''
        server_attempt_id := pg_catalog.gen_random_uuid(); server_receipt_id := pg_catalog.gen_random_uuid();
        INSERT INTO public.offline_attempt(binding_id,attempt_id,generation,state,claimed_at,expires_at,lock_token)
          VALUES($1,server_attempt_id,$5,'CLAIMED',database_now,LEAST(header_record.expires_at,database_now+(policy_values[9]::pg_catalog.text||' microseconds')::pg_catalog.interval),0);
        INSERT INTO public.offline_execution(binding_id,attempt_id,generation,execution_id,instance_id,executor_oid,state,possession_digest,claimed_at,expires_at,claim_receipt_id,lock_token)
          SELECT $1,server_attempt_id,$5,$6,$7,slot_oids[3],'OWNED',pg_catalog.sha256($8),database_now,LEAST(a.expires_at,database_now+(policy_values[11]::pg_catalog.text||' microseconds')::pg_catalog.interval),server_receipt_id,0 FROM public.offline_attempt a WHERE a.binding_id=$1 AND a.attempt_id=server_attempt_id AND a.generation=$5;
        UPDATE public.offline_attempt_pointer p SET current_attempt_id=server_attempt_id WHERE p.binding_id=$1 AND p.generation=$5 AND p.current_attempt_id IS NULL;
        IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED'; END IF;
    ELSE
        server_attempt_id := pointer_record.current_attempt_id;
    END IF;
    SELECT a.binding_id,a.attempt_id,a.generation,a.state,a.claimed_at,a.expires_at INTO STRICT attempt_record FROM public.offline_attempt a WHERE a.binding_id=$1 AND a.attempt_id=server_attempt_id AND a.generation=$5 FOR UPDATE;
    SELECT e.binding_id,e.attempt_id,e.generation,e.execution_id,e.instance_id,e.executor_oid,e.state,e.possession_digest,e.claimed_at,e.expires_at,e.claim_receipt_id INTO STRICT execution_record FROM public.offline_execution e WHERE e.binding_id=$1 AND e.attempt_id=server_attempt_id AND e.generation=$5 AND e.execution_id=$6 AND e.instance_id=$7 FOR UPDATE;
'''+deny("attempt_record.state NOT IN ('CLAIMED','EFFECTS_IN_PROGRESS') OR execution_record.state<>'OWNED' OR execution_record.executor_oid<>slot_oids[3] OR execution_record.possession_digest IS DISTINCT FROM pg_catalog.sha256($8)")+'''
    PERFORM c.binding_id FROM public.offline_ceremony_result c WHERE c.binding_id=$1 AND c.result='NONE';
    IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED'; END IF;
    PERFORM r.binding_id FROM public.offline_reconciliation r WHERE r.binding_id=$1 AND r.state='NOT_STARTED';
    IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED'; END IF;
'''+deny(q_claim()+' IS DISTINCT FROM $9')+'''
    database_now := pg_catalog.clock_timestamp();
'''+deny('database_now>=header_record.expires_at OR database_now>=attempt_record.expires_at OR database_now>=execution_record.expires_at OR database_now>=receipt_expires_at OR EXTRACT(EPOCH FROM(database_now-pg_catalog.transaction_timestamp()))*1000000>policy_values[1]')+'''
    SELECT server_attempt_id AS attempt_id,$5 AS generation,$6 AS execution_id,$7 AS instance_id,attempt_record.claimed_at AS claimed_at,attempt_record.expires_at AS attempt_expires_at,execution_record.expires_at AS execution_expires_at,execution_record.claim_receipt_id AS claim_receipt_id INTO result;
'''
    elif stage in ('S14','S15'):
        if stage=='S14':body+=deny('$10 IS DISTINCT FROM header_record.credential_id OR $11 IS DISTINCT FROM header_record.credential_operation_id')
        body+=delivery_lock()+delivery_origin()
        if stage=='S14':
            decl+=declarations(frozen_tuple(spec,'S10','OUTPUT'),'fresh_')
            body+='''    SELECT s.binding_id,s.attempt_id,s.generation,s.execution_id,s.instance_id,s.stage,s.receipt_id,s.operation_id,s.frozen_receipt,s.effect_time INTO STRICT fresh_receipt FROM public.offline_stage_receipt s WHERE s.binding_id=$1 AND s.attempt_id=$5 AND s.generation=$6 AND s.stage='INITIAL_CREDENTIAL_APPLIED';
'''+deny('fresh_receipt.execution_id<>$7 OR fresh_receipt.instance_id<>$8 OR fresh_receipt.operation_id IS DISTINCT FROM $11 OR fresh_receipt.receipt_id IS DISTINCT FROM $12 OR delivery_record.fresh_applied_receipt_id IS DISTINCT FROM $12')
            body+=decode('fresh_receipt.frozen_receipt','S10',frozen_tuple(spec,'S10','OUTPUT'),'fresh_',direction='OUTPUT')+deny("fresh_outcome<>'APPLIED' OR fresh_result_operation_id IS DISTINCT FROM $11 OR fresh_result_effect_time IS DISTINCT FROM fresh_receipt.effect_time")
            body+="    permission_to_attempt := delivery_record.state='CREATED_NOT_DELIVERABLE';\n"+deny("delivery_record.state NOT IN ('CREATED_NOT_DELIVERABLE','DELIVERY_ATTEMPTED')")+'''
    IF permission_to_attempt THEN
        database_now := pg_catalog.clock_timestamp();
        UPDATE public.offline_delivery d SET state='DELIVERY_ATTEMPTED',delivery_receipt_id=pg_catalog.gen_random_uuid(),attempted_at=database_now,operation_deadline=LEAST(header_record.expires_at,attempt_record.expires_at,execution_record.expires_at,database_now+(policy_values[17]::pg_catalog.text||' microseconds')::pg_catalog.interval) WHERE d.binding_id=$1 AND d.generation=$6 AND d.state='CREATED_NOT_DELIVERABLE';
        IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED'; END IF;
    END IF;
'''+delivery_lock()+'''
    SELECT delivery_record.delivery_receipt_id AS delivery_receipt_id,delivery_record.credential_id AS credential_id,delivery_record.initial_operation_id AS initial_operation_id,delivery_record.fresh_applied_receipt_id AS fresh_applied_receipt_id,delivery_record.execution_id AS execution_id,delivery_record.instance_id AS instance_id,delivery_record.attempted_at AS attempted_at,delivery_record.operation_deadline AS operation_deadline,permission_to_attempt AS permission_to_attempt INTO result;
'''
        else:
            body+=deny("$10 IS DISTINCT FROM delivery_record.delivery_receipt_id OR $11 NOT IN ('DELIVERY_ACKNOWLEDGED','DELIVERY_FAILED_REVIEW_REQUIRED','DELIVERY_OUTCOME_UNKNOWN') OR $13 NOT IN ('COMPLETE','PARTIAL','IO_FAILURE','PROCESS_UNCERTAINTY')")
            body+='''    IF delivery_record.state='DELIVERY_ATTEMPTED' THEN
        database_now := pg_catalog.clock_timestamp();
'''+deny('delivery_record.operation_deadline IS NULL OR database_now>=delivery_record.operation_deadline')+'''
        UPDATE public.offline_delivery d SET state=$11,observed_at=$12,observation_code=$13,recorded_at=database_now WHERE d.binding_id=$1 AND d.generation=$6 AND d.delivery_receipt_id=$10 AND d.state='DELIVERY_ATTEMPTED';
        IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED'; END IF;
    ELSE
'''+deny('delivery_record.state IS DISTINCT FROM $11 OR delivery_record.observed_at IS DISTINCT FROM $12 OR delivery_record.observation_code IS DISTINCT FROM $13')+'    END IF;\n'+delivery_lock()+'''
    SELECT delivery_record.delivery_receipt_id AS delivery_receipt_id,delivery_record.state AS delivery_state,delivery_record.observed_at AS observed_at,delivery_record.observation_code AS observation_code,delivery_record.recorded_at AS recorded_at INTO result;
'''
        body+=final_guard()
    else:
        body+=deny('$10 IS DISTINCT FROM header_record.credential_id OR $11<>1 OR pg_catalog.octet_length($12)<>32')+delivery_lock()+delivery_origin()+deny("delivery_record.state<>'DELIVERY_ACKNOWLEDGED'")
        lineage_decl,lineage_code=durable_lineage(spec);decl+=lineage_decl;body+=lineage_code
        body+='''    SELECT '''+','.join('a.'+c for c in ADMISSION_COLUMNS)+''' INTO admission_record FROM public.offline_admission a WHERE a.binding_id=$1 AND a.attempt_id=$5 AND a.generation=$6 AND a.execution_id=$7 AND a.instance_id=$8 AND a.credential_id=$10 AND a.credential_revision=$11 AND a.grant_id=header_record.grant_id AND a.grant_revision=1 AND a.permission=header_record.permission FOR UPDATE;
    new_admission := NOT FOUND;
'''+current_authority(proof=True)+'''
    database_now := pg_catalog.clock_timestamp();
    IF new_admission THEN
        INSERT INTO public.offline_admission('''+','.join(ADMISSION_COLUMNS)+''',lock_token) VALUES(pg_catalog.gen_random_uuid(),header_record.deployment_id,$3,$1,$5,$6,$7,$8,slot_oids[3],$10,$11,header_record.principal_id,header_record.organization_id,header_record.grant_id,grant_record.revision,authorization_fingerprint,header_record.permission,database_now,LEAST(header_record.expires_at,attempt_record.expires_at,execution_record.expires_at,database_now+(policy_values[15]::pg_catalog.text||' microseconds')::pg_catalog.interval),'ISSUED',NULL,NULL,0);
        SELECT '''+','.join('a.'+c for c in ADMISSION_COLUMNS)+''' INTO STRICT admission_record FROM public.offline_admission a WHERE a.binding_id=$1 AND a.attempt_id=$5 AND a.generation=$6 AND a.execution_id=$7 AND a.instance_id=$8 AND a.credential_id=$10 AND a.credential_revision=$11 AND a.grant_id=header_record.grant_id AND a.grant_revision=grant_record.revision AND a.permission=header_record.permission;
    END IF;
'''+admission_valid()+final_guard()+admission_valid()+'''
    SELECT admission_record.admission_id AS admission_id,admission_record.credential_revision AS credential_revision,admission_record.grant_id AS grant_id,admission_record.grant_revision AS grant_revision,admission_record.permission AS permission,admission_record.authenticated_at AS authenticated_at,admission_record.expires_at AS expires_at,admission_record.durable_state AS durable_state INTO result;
'''
    body+=deny('pg_catalog.num_nonnulls('+','.join('result.'+n for n,t in outputs(spec,stage))+')<>'+str(len(outputs(spec,stage))))
    body+='    RETURN '+encode(stage,outputs(spec,stage))+';\nEXCEPTION WHEN OTHERS THEN\n    RAISE EXCEPTION USING ERRCODE=\'P0017\',MESSAGE=\'ACCESS_DENIED\';\nEND;\n'
    name=WRAPPERS[stage];signature=','.join('pg_catalog.'+t for t in TYPES[stage])
    return 'CREATE FUNCTION public.'+name+'(\n    '+',\n    '.join(n+' pg_catalog.'+t for n,t in zip(NAMES[stage],TYPES[stage]))+') RETURNS pg_catalog.bytea\nLANGUAGE plpgsql VOLATILE SECURITY DEFINER CALLED ON NULL INPUT\nSET search_path=pg_catalog,pg_temp\nAS $offline_'+stage.lower()+'$\n'+decl+body+'$offline_'+stage.lower()+'$;\nALTER FUNCTION public.'+name+'('+signature+') OWNER TO '+OWNER+';\nREVOKE ALL ON FUNCTION public.'+name+'('+signature+') FROM PUBLIC;\n'

def build(source,spec):
    code=MARKER+'\n'+''.join(build_one(source,spec,s) for s in WRAPPERS)
    for schema,name,types,owner in sorted(GRANTS):code+='GRANT EXECUTE ON FUNCTION public.'+name+'('+','.join('pg_catalog.'+t for t in types)+') TO '+owner+';\n'
    return code+END+'\n'

def install():
    p=gate.ROOT/gate.V043;source=p.read_text();spec=(gate.ROOT/gate.SPEC).read_text()
    if MARKER in source:
        start=source.index(MARKER);end=source.index(END,start)+len(END);source=source[:start]+build(source,spec).rstrip()+source[end:]
    else:source+='\n'+build(source,spec)
    p.write_text(source,encoding='utf-8')

if __name__=='__main__':install()
