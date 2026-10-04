"""S17/S18 inline private writer derivation and unchanged snapshot commitment.

Generates source only. Does not execute V043 or provision any operational role.
"""
import json
import re
from functools import lru_cache
import package_0090_source_gate as gate
import build_package_0090_executor_control_source as control
from build_package_0090_q_source import deny,frame,nullable,raw
from build_package_0090_verification_source import final_guard
from build_package_0090_s02_source import accepted_block
from package_0090_typed_transport_source import decode,encode,declarations,DECLARATIONS,frozen_tuple

OWNER=control.OWNER
MARKER='-- Public S17-S18: private decision facts and original unchanged snapshot.'
END='-- End public S17-S18.'
WRAPPERS={'S17':'offline_prepare_attested_decision','S18':'offline_apply_attested_decision'}
TYPES={s:control.BASE_TYPES+('uuid','bytea') for s in WRAPPERS}
NAMES=control.BASE_NAMES+('admission_id','decision_request')
FROZEN={'BEGIN':'s2a_v042_begin_attested_decision_verification','APPLY':'s2a_v042_apply_attested_decision',**control.FROZEN,'PROGRESS':'transaction_identity_progress_lock','INTENT':'transaction_identity_intent','SEMANTIC':'transaction_identity_fingerprint'}
REQUEST=[('decision_id','uuid'),('source_order_reference','text'),('marketplace_order_id','uuid'),('kind','text'),('reason','text'),('provenance','text'),('correlation_id','uuid'),('supersedes_decision_id','uuid')]
REQUEST_BOUNDS={'source_order_reference':(1,256),'kind':(9,9),'reason':(21,21),'provenance':(1,1024)}
SNAPSHOT=[('artifact_version','int4'),('schema_version','int4'),('canonicalization_version','int4'),('canonical_manifest_bytes','bytea'),('manifest_digest','text'),('signature_preimage_bytes','bytea'),('algorithm_id','text'),('signer_subject_id','uuid'),('signer_key_id','uuid'),('signer_key_revision','int4'),('signer_key_fingerprint','text'),('signer_key_lineage_fingerprint','text'),('subject_public_key_info_der','bytea'),('signature_bytes','bytea'),('signer_authority_id','uuid'),('signer_authority_revision','int4'),('signer_authority_fingerprint','text'),('verified_at','timestamptz'),('accepted_proof_fingerprint','text'),('signed_evidence_binding_fingerprint','text')]
SNAPSHOT_BOUNDS={'algorithm_id':(7,7),'signature_bytes':(64,64)}

@lru_cache(maxsize=8)
def frozen_signature(name):
    from pglast.parser import parse_sql_json
    source=(gate.ROOT/'applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V042__create_s2a_attestation_consumption_and_attested_command_authority.sql').read_text()
    for stmt in json.loads(parse_sql_json(source))['stmts']:
        fn=stmt['stmt'].get('CreateFunctionStmt')
        if fn and fn['funcname'][-1]['String']['sval']==name:
            inputs=[];outputs=[]
            for item in fn['parameters']:
                p=item['FunctionParameter'];kind=p['argType']['names'][-1]['String']['sval']
                (outputs if p.get('mode')=='FUNC_PARAM_TABLE' else inputs).append((p['name'],kind))
            return inputs,outputs
    raise ValueError('Frozen signature absent: '+name)

def grants(spec):
    return {('public',FROZEN['BEGIN'],tuple(t for n,t in frozen_signature(FROZEN['BEGIN'])[0]),OWNER),('public',FROZEN['APPLY'],tuple(t for n,t in frozen_tuple(spec,'S18','INPUT')),OWNER),('public',FROZEN['PROGRESS'],('uuid','uuid'),OWNER),('public',FROZEN['INTENT'],('public.marketplace_transaction_identity_decision',),OWNER),('public',FROZEN['SEMANTIC'],('public.marketplace_transaction_identity_decision',),OWNER)}

def writer_query(method,values):
    p=gate.ROOT/'applications/marketplace-operations-persistence-postgres/src/main/kotlin/io/flooow/marketplace/persistence/postgres/PostgresTransactionIdentityWriter.kt'
    query=p.read_text().split('private fun '+method+'(',1)[1].split('prepareStatement("""',1)[1].split('"""',1)[0]
    for value in values:query=query.replace('?',value,1)
    for relation in ['marketplace_order_identity_registry','marketplace_order_occurrence_source_promotion','integration_mercado_livre_order_source_observation','integration_omie_transaction_evidence_v3','integration_omie_transaction_evidence','integration_connector_page_commit','integration_connector_progress']:
        query=re.sub(r'(?<![\w.])'+relation+r'\b','public.'+relation,query)
    return re.sub(r'(?<![\w.])count\(', 'pg_catalog.count(',query)

def manifest_claims(fields):
    block=accepted_block().split('        -- Decode all 23',1)[1].split('        SELECT ',1)[0]
    block='    -- Decode all 23'+block
    code=block
    for index,(name,kind) in enumerate(fields[32:54],2):
        code+='    facts_'+name+' := manifest_fields['+str(index)+']::pg_catalog.'+kind+';\n'
    return code

def derive_facts(fields):
    target=writer_query('target',['header_record.organization_id','header_record.marketplace_order_id','header_record.mercado_livre_connection_id'])
    omie=writer_query('omie',['header_record.organization_id','header_record.omie_connection_id',"'transaction-evidence-v3'",'header_record.source_order_reference'])
    # The capability literal is extracted from the existing writer, not guessed.
    writer=(gate.ROOT/'applications/marketplace-operations-persistence-postgres/src/main/kotlin/io/flooow/marketplace/persistence/postgres/PostgresTransactionIdentityWriter.kt').read_text()
    match=re.search(r'const val OMIE_V3\s*=\s*"([^"]+)"',writer)
    if not match:raise ValueError('Frozen Omie capability not resolved')
    omie=omie.replace("'transaction-evidence-v3'","'"+match[1]+"'")
    # AU includes the original organization/principal locks before the ID
    # advisory (SPEC10). The later P call is the writer's reentrant lock route.
    code=control.current_authority(lock=True,check_head=False)+control.admission_valid()+'''
    PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended('transaction-identity/id/1:'||header_record.organization_id::pg_catalog.text||':'||header_record.decision_id::pg_catalog.text,0));
    IF EXISTS(SELECT 1 FROM public.marketplace_transaction_identity_decision d WHERE d.organization_id=header_record.organization_id AND d.decision_id=header_record.decision_id) THEN RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='REPLAY_INSPECTION_REQUIRED'; END IF;
    IF public.offline_lock_bound_principal($1,$2,$3,$4,$5,$6,$7,$8,$9) IS NOT TRUE THEN RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED'; END IF;
    IF public.transaction_identity_progress_lock(header_record.organization_id,header_record.omie_connection_id) IS NOT TRUE THEN RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED'; END IF;
    FOR resource_key IN SELECT pg_catalog.unnest(ARRAY[
      'transaction-identity/subject/1:'||header_record.organization_id::pg_catalog.text||':'||header_record.omie_connection_id::pg_catalog.text||':'||pg_catalog.octet_length(pg_catalog.convert_to(header_record.source_order_reference,'UTF8'))::pg_catalog.text||':'||header_record.source_order_reference,
      'transaction-identity/target/1:'||header_record.organization_id::pg_catalog.text||':'||header_record.marketplace_order_id::pg_catalog.text]) ORDER BY 1 LOOP
        PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(resource_key,0));
    END LOOP;
'''
    # INTO is placed before FROM, leaving the producer's predicates/order intact.
    code+=target.replace('            FROM',' INTO STRICT target_record\n            FROM',1)+';\n'
    code+='    FOR evidence_record IN '+omie+' LOOP\n'
    code+=deny("evidence_record.page_complete IS NOT TRUE OR evidence_record.record_count IS NULL OR evidence_record.record_ordinal>=evidence_record.record_count OR evidence_record.semantic_fingerprint_version IS DISTINCT FROM 1 OR evidence_record.source_evidence_semantic_fingerprint IS NULL OR evidence_record.source_evidence_semantic_fingerprint !~ '^[0-9a-f]{64}$' OR (evidence_record.provider_created_local IS NULL AND evidence_record.provider_modified_local IS NULL) OR (evidence_record.provider_created_local IS NOT NULL AND evidence_record.provider_modified_local IS NOT NULL AND evidence_record.provider_modified_local<evidence_record.provider_created_local) OR NOT pg_catalog.isfinite(COALESCE(evidence_record.provider_modified_local,evidence_record.provider_created_local))")
    code+='    END LOOP;\n'
    code+='    SELECT pg_catalog.max(COALESCE(e.provider_modified_local,e.provider_created_local)) INTO current_revision FROM ('+omie+') e;\n'+deny('current_revision IS NULL')
    code+='    SELECT pg_catalog.count(DISTINCT e.source_evidence_semantic_fingerprint) INTO semantic_count FROM ('+omie+') e WHERE COALESCE(e.provider_modified_local,e.provider_created_local)=current_revision;\n'+deny('semantic_count<>1')
    code+=deny('EXISTS(SELECT 1 FROM ('+omie+') e WHERE COALESCE(e.provider_modified_local,e.provider_created_local)=current_revision AND ((e.source_integration_ref IS NOT NULL AND e.source_integration_ref<>target_record.external_order_id) OR (e.currency IS NOT NULL AND e.currency<>target_record.currency)))')
    code+='    SELECT e.input_progress_version,e.record_ordinal,e.source_evidence_semantic_fingerprint INTO STRICT selected_evidence FROM ('+omie+') e WHERE COALESCE(e.provider_modified_local,e.provider_created_local)=current_revision ORDER BY e.input_progress_version,e.record_ordinal LIMIT 1;\n'
    code+=deny('EXISTS(SELECT 1 FROM public.marketplace_transaction_identity_head h WHERE h.organization_id=header_record.organization_id AND h.omie_connection_id=header_record.omie_connection_id AND h.source_order_reference=header_record.source_order_reference AND h.marketplace_order_id=header_record.marketplace_order_id)')
    code+=control.current_authority(lock=False,check_head=False)+control.admission_valid()
    values=[ 'header_record.organization_id','header_record.decision_id','header_record.omie_connection_id','header_record.source_order_reference','header_record.marketplace_order_id',"'CONFIRMED'","'EXPLICIT_CONFIRMATION'",'1','NULL','header_record.mercado_livre_connection_id',"'marketplace-economic.order-source'",'target_record.source_input_progress_version','target_record.source_record_ordinal','target_record.external_order_id','target_record.currency',"'"+match[1]+"'",'selected_evidence.input_progress_version','selected_evidence.record_ordinal','selected_evidence.source_evidence_semantic_fingerprint','current_revision','header_record.principal_id','header_record.credential_id','credential_record.revision','header_record.grant_id','grant_record.revision','header_record.permission',"'command-authorization/1'","pg_catalog.encode(authorization_fingerprint,'hex')",'NULL','NULL','header_record.provenance','header_record.correlation_id']
    for (name,kind),value in zip(fields[:32],values):code+='    facts_'+name+' := '+value+';\n'
    code+=manifest_claims(fields)
    row=lambda:'ROW('+','.join('facts_'+n for n,t in fields[:32])+',NULL::pg_catalog.timestamptz)::public.marketplace_transaction_identity_decision'
    code+='    facts_p_intent_fingerprint := public.transaction_identity_intent('+row()+');\n'
    code+='    facts_p_decision_semantic_fingerprint := public.transaction_identity_fingerprint('+row()+');\n'
    return code

def build_one(source,spec,stage):
    fields=frozen_tuple(spec,'S18','INPUT');fields=[(n,'timestamp' if n=='p_provider_revision_local' else t) for n,t in fields]
    begin_inputs,begin_outputs=frozen_signature(FROZEN['BEGIN'])
    decl,body=control.mutable_guard(source,TYPES[stage]);lineage_decl,lineage_code=control.durable_lineage(spec)
    decl+=control.EXTRA+DECLARATIONS+lineage_decl+declarations(REQUEST,'request_')+declarations(fields[:54],'facts_')+declarations(SNAPSHOT,'accepted_')+'''
    caller_request pg_catalog.bytea;
    accepted_snapshot pg_catalog.bytea;
    preparation_digest pg_catalog.bytea;
    server_facts pg_catalog.bytea;
    snapshot record;
    target_record record;
    evidence_record record;
    selected_evidence record;
    current_revision pg_catalog.timestamp;
    semantic_count pg_catalog.int8;
    resource_key pg_catalog.text;
    manifest_fields pg_catalog.text[];
    manifest_cursor pg_catalog.int4;
    manifest_index pg_catalog.int4;
    manifest_size pg_catalog.int8;
    manifest_value pg_catalog.text;
    window_start pg_catalog.timestamptz;
    window_end pg_catalog.timestamptz;
    output_bytes pg_catalog.bytea;
'''
    body+=control.delivery_lock()+control.delivery_origin()+deny("delivery_record.state<>'DELIVERY_ACKNOWLEDGED'")
    body+='    SELECT '+','.join('a.'+n for n in control.ADMISSION_COLUMNS)+' INTO STRICT admission_record FROM public.offline_admission a WHERE a.admission_id=$10 AND a.binding_id=$1 AND a.attempt_id=$5 AND a.generation=$6 AND a.execution_id=$7 AND a.instance_id=$8 FOR UPDATE;\n'+lineage_code
    if stage=='S17':body+='    caller_request := $11;\n'
    else:
        envelope=[('caller_request','bytea'),('preparation_digest','bytea'),('accepted_snapshot','bytea')]
        # Maximums derive from the complete request/snapshot field matrices.
        from package_0090_typed_transport_source import bound
        request_max=6+len('FLOOOW/OFFLINE-FIELD-PROOF/S17/INPUT/V1')+sum(7+(REQUEST_BOUNDS.get(n) or bound(n,t))[1] for n,t in REQUEST)
        snapshot_max=6+len('FLOOOW/OFFLINE-FIELD-PROOF/DECISION-ACCEPTED/V1')+sum(7+(SNAPSHOT_BOUNDS.get(n) or bound(n,t))[1] for n,t in SNAPSHOT)
        body+=decode('$11','S17',envelope,'',direction='OUTPUT',bounds={'caller_request':(1,request_max),'preparation_digest':(32,32),'accepted_snapshot':(1,snapshot_max)})
        body+=decode('accepted_snapshot','DECISION-ACCEPTED',SNAPSHOT,'accepted_',domain_override='FLOOOW/OFFLINE-FIELD-PROOF/DECISION-ACCEPTED/V1',bounds=SNAPSHOT_BOUNDS)
    body+=decode('caller_request','S17',REQUEST,'request_',bounds=REQUEST_BOUNDS,nullable_fields=('supersedes_decision_id',))
    body+=deny("request_decision_id IS DISTINCT FROM header_record.decision_id OR request_source_order_reference IS DISTINCT FROM header_record.source_order_reference OR request_marketplace_order_id IS DISTINCT FROM header_record.marketplace_order_id OR request_kind<>'CONFIRMED' OR request_reason<>'EXPLICIT_CONFIRMATION' OR request_provenance IS DISTINCT FROM header_record.provenance OR request_correlation_id IS DISTINCT FROM header_record.correlation_id OR request_supersedes_decision_id IS NOT NULL")
    body+=derive_facts(fields)
    body+='    server_facts := '+encode('',fields[:54],'facts_',domain_kind='DECISION-SERVER-FACTS')+';\n'
    begin_values=['facts_p_organization_id','facts_p_principal_id','facts_p_grant_id','facts_p_grant_revision','facts_p_decision_id','facts_p_decision_omie_connection_id','facts_p_decision_source_order_reference','facts_p_decision_marketplace_order_id']+['facts_'+n for n,t in fields[32:54]]
    body+='    SELECT '+','.join('v.'+n for n,t in begin_outputs)+' INTO STRICT snapshot FROM public.'+FROZEN['BEGIN']+'('+','.join(begin_values)+') v;\n'
    body+="    IF snapshot.outcome='ALREADY_APPLIED' THEN RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='REPLAY_INSPECTION_REQUIRED'; END IF;\n"
    body+=deny("snapshot.outcome IS DISTINCT FROM 'READY' OR snapshot.result_decision_id IS DISTINCT FROM header_record.decision_id OR snapshot.result_manifest_id IS DISTINCT FROM header_record.manifest_id OR snapshot.result_canonical_manifest_bytes IS DISTINCT FROM header_record.canonical_manifest_bytes OR snapshot.result_accepted_proof_fingerprint IS DISTINCT FROM verified_result_accepted_proof_fingerprint OR snapshot.result_verified_at IS DISTINCT FROM verified_result_verified_at")
    body+=deny('pg_catalog.num_nonnulls('+','.join('snapshot.result_'+n for n,t in SNAPSHOT)+')<>20')
    if stage=='S17':
        for n,t in SNAPSHOT:body+='    accepted_'+n+' := snapshot.result_'+n+';\n'
        body+='    accepted_snapshot := '+encode('',SNAPSHOT,'accepted_',domain_kind='DECISION-ACCEPTED')+';\n'
    else:
        body+=deny('accepted_snapshot IS DISTINCT FROM '+encode('',[(n,t) for n,t in SNAPSHOT],'snapshot.result_',domain_kind='DECISION-ACCEPTED'))
    digest_values=['pg_catalog.uuid_send($1)','$2','pg_catalog.uuid_send($3)',raw('$4'),'pg_catalog.uuid_send($5)','pg_catalog.int8send($6)','pg_catalog.uuid_send($7)','pg_catalog.uuid_send($8)','pg_catalog.uuid_send($10)','caller_request','server_facts','accepted_snapshot']
    digest='pg_catalog.sha256('+frame('DECISION-PREPARATION',[nullable(v) for v in digest_values])+')'
    body+=final_guard()+control.admission_valid()
    if stage=='S17':
        body+='    preparation_digest := '+digest+';\n    RETURN '+encode('S17',[('caller_request','bytea'),('preparation_digest','bytea'),('accepted_snapshot','bytea')],'')+';\n'
    else:
        body+=deny('preparation_digest IS DISTINCT FROM '+digest)
        expected=lambda n:'accepted_'+n[len('p_expected_'):] if n!='p_expected_evidence_binding_fingerprint' else 'accepted_signed_evidence_binding_fingerprint'
        outputs=frozen_tuple(spec,'S18','OUTPUT')
        body+='    SELECT '+','.join('v.'+n for n,t in outputs)+' INTO STRICT result FROM public.'+FROZEN['APPLY']+'('+','.join(['facts_'+n for n,t in fields[:54]]+[expected(n) for n,t in fields[54:]])+') v;\n'
        body+=deny("result.outcome IS DISTINCT FROM 'APPLIED' OR result.result_decision_id IS DISTINCT FROM header_record.decision_id OR result.result_decision_semantic_fingerprint IS DISTINCT FROM facts_p_decision_semantic_fingerprint OR pg_catalog.num_nonnulls("+','.join('result.'+n for n,t in outputs)+')<>4')+final_guard()+control.admission_valid()
        body+='    output_bytes := '+encode('S18',outputs)+';\n'
        body+='''    INSERT INTO public.offline_stage_receipt(binding_id,attempt_id,generation,execution_id,instance_id,stage,receipt_id,operation_id,frozen_receipt,effect_time)
      VALUES($1,$5,$6,$7,$8,'IDENTITY_DECISION_APPLIED',pg_catalog.gen_random_uuid(),NULL,output_bytes,result.result_decided_at);
    UPDATE public.offline_admission a SET durable_state='CONSUMED',consumed_decision_id=header_record.decision_id,consumed_at=database_now WHERE a.admission_id=$10 AND a.durable_state='ISSUED';
    IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED'; END IF;
    UPDATE public.offline_attempt a SET state='EFFECTS_COMPLETE' WHERE a.binding_id=$1 AND a.attempt_id=$5 AND a.generation=$6 AND a.state='EFFECTS_IN_PROGRESS';
    IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED'; END IF;
    UPDATE public.offline_execution e SET state='RELEASED' WHERE e.binding_id=$1 AND e.attempt_id=$5 AND e.generation=$6 AND e.execution_id=$7 AND e.instance_id=$8 AND e.state='OWNED';
    IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED'; END IF;
    UPDATE public.offline_reconciliation r SET state='REQUIRED' WHERE r.binding_id=$1 AND r.state='NOT_STARTED';
    IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED'; END IF;
    database_now := pg_catalog.clock_timestamp();
'''+deny('database_now>=LEAST(header_record.expires_at,attempt_record.expires_at,execution_record.expires_at,admission_record.expires_at) OR EXTRACT(EPOCH FROM(database_now-pg_catalog.transaction_timestamp()))*1000000>policy_values[1]')+'    RETURN output_bytes;\n'
    body+="EXCEPTION WHEN OTHERS THEN\n    IF SQLSTATE='P0017' AND SQLERRM='REPLAY_INSPECTION_REQUIRED' THEN RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='REPLAY_INSPECTION_REQUIRED'; END IF;\n    RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';\nEND;\n"
    signature=','.join('pg_catalog.'+t for t in TYPES[stage]);name=WRAPPERS[stage]
    return 'CREATE FUNCTION public.'+name+'(\n    '+',\n    '.join(n+' pg_catalog.'+t for n,t in zip(NAMES,TYPES[stage]))+') RETURNS pg_catalog.bytea\nLANGUAGE plpgsql VOLATILE SECURITY DEFINER CALLED ON NULL INPUT\nSET search_path=pg_catalog,pg_temp\nAS $offline_'+stage.lower()+'$\n'+decl+body+'$offline_'+stage.lower()+'$;\nALTER FUNCTION public.'+name+'('+signature+') OWNER TO '+OWNER+';\nREVOKE ALL ON FUNCTION public.'+name+'('+signature+') FROM PUBLIC;\n'

def build(source,spec):
    code=MARKER+'\n'+''.join(build_one(source,spec,s) for s in WRAPPERS)
    for schema,name,types,owner in sorted(grants(spec)):
        code+='GRANT EXECUTE ON FUNCTION public.'+name+'('+','.join(t if '.' in t else 'pg_catalog.'+t for t in types)+') TO '+owner+';\n'
    return code+END+'\n'

def install():
    p=gate.ROOT/gate.V043;source=p.read_text();spec=(gate.ROOT/gate.SPEC).read_text()
    if MARKER in source:
        start=source.index(MARKER);end=source.index(END,start)+len(END);source=source[:start]+build(source,spec).rstrip()+source[end:]
    else:source+='\n'+build(source,spec)
    p.write_text(source,encoding='utf-8',newline='\n')

if __name__=='__main__':install()
