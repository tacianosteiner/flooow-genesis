"""Actual I/E wrapper execution on disposable, network-free PG18.

Mock domain tables and frozen transport stubs are explicit. Pure identity hash,
intent and decision helpers are copied unchanged from V035. No V043 execution.
"""
import hashlib
import json
import os
import re
import struct
import uuid
from datetime import datetime,timezone,timedelta
import package_0090_source_gate as gate
import package_0090_verification_isolated_review as verification
import build_package_0090_issuance_source as issuance
import build_package_0090_executor_control_source as control
import build_package_0090_decision_source as decision
from package_0090_typed_transport_source import frozen_tuple
from package_0090_evidence_fixture import frame,present,decode_frame
from package_0090_s02_isolated_review import quote

def identity_hash(values):
    return hashlib.sha256(''.join(str(len(v.encode()))+':'+v for v in values).encode()).hexdigest()

def encode_fields(domain,fields,values):
    payload=[]
    for n,t in fields:
        v=values[n]
        if v is None:payload.append(b'\x00');continue
        if t=='int8':data=struct.pack('>q',int(v))
        elif t=='timestamp':
            delta=datetime.fromisoformat(v)-datetime(1970,1,1);data=struct.pack('>q',delta.days*86400000000+delta.seconds*1000000+delta.microseconds)
        elif t=='bpchar':data=v.encode()
        else:data=verification.scalar(v,t)
        payload.append(present(data))
    return frame('FLOOOW/OFFLINE-FIELD-PROOF/'+domain+'/V1',payload)

def domain_tables():
    import pglast
    from pglast import ast
    from pglast.stream import RawStream
    tables={}
    for path in sorted((gate.ROOT/gate.MIGRATIONS).glob('V0*.sql')):
        if path.name.startswith('V043'):continue
        for raw_stmt in pglast.parse_sql(path.read_text(encoding='utf-8-sig')):
            stmt=raw_stmt.stmt
            if isinstance(stmt,ast.CreateStmt):
                tables[stmt.relation.relname]={c.colname:RawStream()(c.typeName) for c in stmt.tableElts or () if isinstance(c,ast.ColumnDef)}
            elif isinstance(stmt,ast.AlterTableStmt) and stmt.relation.relname in tables:
                for cmd in stmt.cmds:
                    if isinstance(cmd.def_,ast.ColumnDef):tables[stmt.relation.relname][cmd.def_.colname]=RawStream()(cmd.def_.typeName)
    return tables

def augment(sql,ctx):
    source,spec=ctx['source'],ctx['spec'];row=ctx['row'];request=dict(ctx['request']);header=ctx['header']
    binding,attempt,execution,instance,secret=(ctx[n] for n in ('binding','attempt','execution','instance','secret'))
    sql+="UPDATE public.test_frozen_fault SET enabled=false;\n"
    sql+='CREATE ROLE '+issuance.OWNER+' NOLOGIN NOINHERIT;\nCREATE ROLE '+control.OWNER+' NOLOGIN NOINHERIT;\n'
    tables=dict(ctx['tables'])
    for table in ['offline_delivery','offline_admission']:
        block=source.split('CREATE TABLE public.'+table+' (',1)[1].split('\n);',1)[0]
        fields=re.findall(r'^    ([a-z_]+) pg_catalog\.([a-z0-9]+)',block,re.M);tables[table]=fields
        sql+='CREATE TABLE public.'+table+'('+','.join(n+' pg_catalog.'+t for n,t in fields)+');\nALTER TABLE public.'+table+' OWNER TO flooow_offline_control_owner;\n'
    for o,r,c,p in sorted(gate.expected_column_grants(spec)):
        if o in (issuance.OWNER,control.OWNER) and r.removeprefix('public.') in tables:sql+='GRANT '+p.upper()+'('+c+') ON '+r+' TO '+o+';\n'
    domains=domain_tables();required={r.removeprefix('public.') for o,r,c,p in gate.expected_column_grants(spec) if o==control.OWNER and not r.startswith(('public.offline_','pg_catalog.'))}
    for table in sorted(required):
        sql+='CREATE TABLE public.'+table+'('+','.join(n+' '+t for n,t in domains[table].items())+');\n'
    for o,r,c,p in sorted(gate.expected_column_grants(spec)):
        if o==control.OWNER and r.removeprefix('public.') in required:sql+='GRANT '+p.upper()+'('+c+') ON '+r+' TO '+o+';\n'
    # Binding remains immutable. These IDs were already initialized in the header.
    ids={n:str(uuid.UUID(int=1000+i)) for i,(n,t) in enumerate(ctx['tables']['offline_binding_header']) if t=='uuid'}
    for n in ['organization_id','manifest_id','mercado_livre_connection_id','omie_connection_id','marketplace_order_id','correlation_id']:ids[n]=request['p_'+n]
    request.update(p_principal_id=ids['principal_id'],p_credential_id=ids['credential_id'],p_grant_id=ids['grant_id'],p_secret_verifier='04'*32,p_expected_signature_preimage_bytes=row['canonical_signature_preimage_bytes'],p_expected_signer_subject_id=str(uuid.UUID(int=300)),p_expected_signed_evidence_binding_fingerprint=ctx['manifest'][22])
    # Every immutable expected field comes from the exported accepted snapshot.
    accepted={n:row.get(n,row.get('canonical_signature_preimage_bytes') if n=='signature_preimage_bytes' else str(uuid.UUID(int=300)) if n=='signer_subject_id' else ctx['manifest'][22] if n=='signed_evidence_binding_fingerprint' else None) for n,t in decision.SNAPSHOT}
    expected_map={'p_expected_'+n:v for n,v in accepted.items() if n!='schema_version'};expected_map['p_expected_evidence_binding_fingerprint']=accepted['signed_evidence_binding_fingerprint'];request.update(expected_map)
    goldens={}
    for stage,name in issuance.FROZEN.items():
        category='principal' if stage in ('S07','S08') else 'credential' if stage in ('S09','S10') else 'grant'
        ins=frozen_tuple(spec,stage,'INPUT');outs=frozen_tuple(spec,stage,'OUTPUT')
        values=dict(request,p_operation_id=ids[category+'_operation_id'],p_claim_manifest_id=request['p_manifest_id'],p_claim_organization_id=request['p_organization_id'])
        for n,t in ins:
            if n not in values:raise ValueError('Missing isolated issuance field '+n)
        out={n:None for n,t in outs};out.update(outcome='READY' if int(stage[1:])%2 else 'APPLIED',result_operation_id=values['p_operation_id'],result_intent_fingerprint='11'*32,result_receipt_fingerprint='12'*32,result_effect_time=row['verified_at'])
        for n,v in accepted.items():
            if 'result_'+n in out:out['result_'+n]=v
        sql+='CREATE FUNCTION public.'+name+'('+','.join(n+' pg_catalog.'+t for n,t in ins)+') RETURNS TABLE('+','.join(n+' pg_catalog.'+t for n,t in outs)+') LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $stub$ SELECT '+','.join('NULL::pg_catalog.'+t if out[n] is None else verification.sql_value(out[n],t) for n,t in outs)+' $stub$;\nREVOKE ALL ON FUNCTION public.'+name+'('+','.join('pg_catalog.'+t for n,t in ins)+') FROM PUBLIC;\n'
        golden_input=encode_fields(stage+'/INPUT',ins,values);golden_output=encode_fields(stage+'/OUTPUT',outs,out)
        goldens[stage]={'input_hex':golden_input.hex(),'output_hex':golden_output.hex()}
    sql+=issuance.build(source,spec)
    def entry(stage,name,types,extras):
        arguments="h.binding_id,h.plan_fingerprint,h.deployment_incarnation_id,h.offline_surface_version,"+quote(attempt)+',1,'+quote(execution)+','+quote(instance)+",decode("+quote(secret)+",'hex')"
        sql_types=','.join('pg_catalog.'+t for t in extras)
        call=arguments+(' ,'+','.join('$'+str(i) for i in range(1,len(extras)+1)) if extras else '')
        return 'CREATE FUNCTION public.test_'+stage.lower()+'('+sql_types+') RETURNS bytea LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $entry$ SELECT public.'+name+'('+call+') FROM public.offline_binding_header h $entry$;\nREVOKE ALL ON FUNCTION public.test_'+stage.lower()+'('+sql_types+') FROM PUBLIC;\nGRANT EXECUTE ON FUNCTION public.test_'+stage.lower()+'('+sql_types+') TO test_issuer,test_executor,test_auditor;\n'
    def assert_call(call,expected=None,denied=False):
        if denied:return "DO $negative$ BEGIN BEGIN PERFORM "+call+"; RAISE EXCEPTION 'DENIAL_MISSING'; EXCEPTION WHEN SQLSTATE 'P0017' THEN IF SQLERRM<>'ACCESS_DENIED' THEN RAISE EXCEPTION 'UNSANITIZED'; END IF; END; END $negative$;\n"
        if expected is None:return 'SELECT '+call+';\n'
        return 'DO $golden$ BEGIN IF '+call+' IS DISTINCT FROM decode('+quote(expected.hex())+",'hex') THEN RAISE EXCEPTION 'TRANSPORT_GOLDEN_MISMATCH'; END IF; END $golden$;\n"
    sql+='INSERT INTO public.offline_delivery(binding_id,generation,state,lock_token) VALUES('+quote(binding)+",1,'NOT_CREATED',0);\n"
    for stage,name in issuance.WRAPPERS.items():sql+=entry(stage,name,issuance.TYPES,('bytea',))
    for stage in ('S07','S08','S09','S10'):
        data=bytes.fromhex(goldens[stage]['input_hex']);call='public.test_'+stage.lower()+'(decode('+quote(data.hex())+",'hex'))"
        sql+='SET SESSION AUTHORIZATION test_issuer;\n'+assert_call(call,bytes.fromhex(goldens[stage]['output_hex']))+assert_call('public.test_'+stage.lower()+'(decode('+quote((data+b'\x00').hex())+",'hex'))",denied=True)+'RESET SESSION AUTHORIZATION;\n'
    sql+="DO $origin$ BEGIN IF (SELECT count(*) FROM public.offline_stage_receipt)<>3 OR (SELECT state FROM public.offline_delivery)<>'CREATED_NOT_DELIVERABLE' THEN RAISE EXCEPTION 'ISSUANCE_ORIGIN_MISSING'; END IF; END $origin$;\n"
    # P/Q are transport stubs here; their complete source/native evidence is separate.
    for name,types,body in [('offline_lock_bound_principal',control.BASE_TYPES,'SELECT true'),('offline_internal_readiness',('uuid','bytea','uuid','text','bytea','bytea','bytea','bytea'),'SELECT $8')]:
        sql+='CREATE FUNCTION public.'+name+'('+','.join('pg_catalog.'+t for t in types)+') RETURNS '+('boolean' if name.endswith('principal') else 'bytea')+' LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $stub$ '+body+' $stub$;\nREVOKE ALL ON FUNCTION public.'+name+'('+','.join('pg_catalog.'+t for t in types)+') FROM PUBLIC;\nGRANT EXECUTE ON FUNCTION public.'+name+'('+','.join('pg_catalog.'+t for t in types)+') TO '+control.OWNER+';\n'
    v035=next((gate.ROOT/gate.MIGRATIONS).glob('V035__*.sql')).read_text()
    for name in ['transaction_identity_hash','transaction_identity_grant_fingerprint','transaction_identity_intent','transaction_identity_fingerprint']:
        block=v035.split('CREATE FUNCTION '+name+'(',1)[1].split('$$;',1)[0]
        sql+='CREATE FUNCTION public.'+name+'('+block+'$$;\n'
    sql+=control.build(source,spec)
    for stage in ('S14','S15','S16'):sql+=entry(stage,control.WRAPPERS[stage],control.TYPES[stage],control.TYPES[stage][9:])
    sql+='CREATE TABLE public.test_delivery_bytes(data bytea); CREATE TABLE public.test_admission_bytes(data bytea);\nGRANT INSERT(data) ON public.test_delivery_bytes,public.test_admission_bytes TO test_executor;\n'
    sql+='UPDATE public.offline_execution SET claim_receipt_id='+quote(str(uuid.UUID(int=606)))+';\n'
    instant=datetime.now(timezone.utc)
    pf_values=dict(incarnation=ctx['incarnation'],binding_fingerprint=None,surface='0090-v1',history_digest='01'*32,acl_digest='01'*32,policy_digest=ctx['digest'],issued_at=instant.isoformat().replace('+00:00','Z'),expires_at=(instant+timedelta(seconds=15)).isoformat().replace('+00:00','Z'),key_version='4294967295')
    # Header fingerprint is dynamic; only its fixed32 payload is replaced in SQL.
    pf_values['binding_fingerprint']='01'*32
    pf_payload=[]
    for n,t in control.PF_FIELDS:
        pf_payload.append(present(struct.pack('>I',int(pf_values[n])) if t=='u32' else verification.scalar(pf_values[n],t)))
    pf_bytes=frame('FLOOOW/OFFLINE-FIELD-PROOF/PREFLIGHT/V1',pf_payload)+bytes(32)
    cursor=6+len('FLOOOW/OFFLINE-FIELD-PROOF/PREFLIGHT/V1');parts=[];last=0
    replacements={2:'h.plan_fingerprint',7:'int8send((EXTRACT(EPOCH FROM h.issued_at)*1000000)::bigint)',8:'int8send((EXTRACT(EPOCH FROM h.expires_at)*1000000)::bigint)'}
    for tag in range(1,10):
        length=int.from_bytes(pf_bytes[cursor+2:cursor+6],'big')
        if tag in replacements:
            start=cursor+7;parts+=['decode('+quote(pf_bytes[last:start].hex())+",'hex')",replacements[tag]];last=start+length-1
        cursor+=6+length
    parts+=['decode('+quote(pf_bytes[last:].hex())+",'hex')"];receipt_sql='||'.join(parts)
    sql+='CREATE FUNCTION public.test_claim() RETURNS bytea LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $entry$ SELECT public.offline_claim_attempt(h.binding_id,h.plan_fingerprint,h.deployment_incarnation_id,h.offline_surface_version,1::bigint,'+quote(execution)+'::uuid,'+quote(instance)+"::uuid,decode("+quote(secret)+",'hex'),"+receipt_sql+') FROM public.offline_binding_header h $entry$; GRANT EXECUTE ON FUNCTION public.test_claim() TO test_executor;\n'
    sql+="CREATE TABLE public.test_claim_bytes(data bytea); DO $claim$ DECLARE first bytea;again bytea; BEGIN SET SESSION AUTHORIZATION test_executor; first:=public.test_claim(); again:=public.test_claim(); RESET SESSION AUTHORIZATION; IF first IS DISTINCT FROM again THEN RAISE EXCEPTION 'CLAIM_RENEWED'; END IF; INSERT INTO public.test_claim_bytes VALUES(first); END $claim$;\n"
    # The test entry privately supplies the durable fresh receipt (no service SELECT).
    sql+='CREATE FUNCTION public.test_delivery() RETURNS bytea LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $entry$ SELECT public.test_s14('+quote(ids['credential_id'])+','+quote(ids['credential_operation_id'])+",s.receipt_id) FROM public.offline_stage_receipt s WHERE s.stage='INITIAL_CREDENTIAL_APPLIED' $entry$; GRANT EXECUTE ON FUNCTION public.test_delivery() TO test_executor;\n"
    sql+='SET SESSION AUTHORIZATION test_executor;\nINSERT INTO public.test_delivery_bytes SELECT public.test_delivery();\nRESET SESSION AUTHORIZATION;\n'
    sql+="DO $once$ DECLARE first bytea;again bytea;BEGIN SELECT data INTO first FROM public.test_delivery_bytes; SET SESSION AUTHORIZATION test_executor; again:=public.test_delivery(); RESET SESSION AUTHORIZATION; IF substring(first,1,octet_length(first)-1)<>substring(again,1,octet_length(again)-1) OR get_byte(first,octet_length(first)-1)<>1 OR get_byte(again,octet_length(again)-1)<>0 THEN RAISE EXCEPTION 'DELIVERY_PERMISSION_RENEWED'; END IF; END $once$;\n"
    sql+='CREATE FUNCTION public.test_report() RETURNS bytea LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $entry$ SELECT public.test_s15(d.delivery_receipt_id,\'DELIVERY_ACKNOWLEDGED\',d.attempted_at,\'COMPLETE\') FROM public.offline_delivery d $entry$; GRANT EXECUTE ON FUNCTION public.test_report() TO test_executor;\nCREATE TABLE public.test_report_bytes(data bytea); DO $report$ DECLARE first bytea;again bytea; BEGIN SET SESSION AUTHORIZATION test_executor; first:=public.test_report(); again:=public.test_report(); RESET SESSION AUTHORIZATION; IF first IS DISTINCT FROM again THEN RAISE EXCEPTION \'REPORT_RECORDED_CLOCK_RENEWED\'; END IF; INSERT INTO public.test_report_bytes VALUES(first); END $report$;\n'
    for stage in ('S11','S12'):
        sql+='SET SESSION AUTHORIZATION test_issuer;\n'+assert_call('public.test_'+stage.lower()+'(decode('+quote(goldens[stage]['input_hex'])+",'hex'))",bytes.fromhex(goldens[stage]['output_hex']))+'RESET SESSION AUTHORIZATION;\n'
    sql+='INSERT INTO public.integration_organization(organization_id,status) VALUES('+quote(ids['organization_id'])+",'ACTIVE');\n"
    sql+='INSERT INTO public.command_principal(organization_id,principal_id,mercado_livre_connection_id,omie_connection_id) VALUES('+','.join(quote(ids[n]) for n in ['organization_id','principal_id','mercado_livre_connection_id','omie_connection_id'])+');\n'
    sql+='INSERT INTO public.command_credential_revision(organization_id,principal_id,credential_id,revision,state,secret_verifier) VALUES('+','.join(quote(ids[n]) for n in ['organization_id','principal_id','credential_id'])+",1,'ENABLED',decode('"+'04'*32+"','hex'));\n"
    sql+='INSERT INTO public.command_permission_grant(organization_id,principal_id,grant_id,revision,permission,state,reason,provenance,correlation_id,decided_at) VALUES('+','.join(quote(ids[n]) for n in ['organization_id','principal_id','grant_id'])+",1,"+quote(request['p_permission'])+",'ENABLED','fixture-grant','isolated',"+quote(ids['correlation_id'])+','+quote(row['verified_at'])+');\n'
    sql+='SET SESSION AUTHORIZATION test_executor; INSERT INTO public.test_admission_bytes SELECT public.test_s16('+quote(ids['credential_id'])+",1,decode('"+'04'*32+"','hex')); RESET SESSION AUTHORIZATION;\n"
    sql+="DO $admission$ DECLARE first bytea;again bytea; BEGIN SELECT data INTO first FROM public.test_admission_bytes; SET SESSION AUTHORIZATION test_executor; again:=public.test_s16("+quote(ids['credential_id'])+",1,decode('"+'04'*32+"','hex')); RESET SESSION AUTHORIZATION; IF first IS DISTINCT FROM again THEN RAISE EXCEPTION 'ADMISSION_RENEWED'; END IF; END $admission$;\n"
    # Actual E decision bodies are installed below after private evidence seeding.
    ctx['mutation_goldens']=goldens
    sql+=decision_fixture(ctx,ids,accepted,request,entry,assert_call)
    return sql

def decision_fixture(ctx,ids,accepted,request,entry,assert_call):
    # Kept separate so private derivation can be tested with independently known facts.
    source,spec,row=ctx['source'],ctx['spec'],ctx['row'];sql=''
    omie_cap='marketplace-economic.omie-transaction-evidence.reacquisition-v3';ml_cap='marketplace-economic.order-source'
    org,ml,omie,market=(quote(ids[n]) for n in ['organization_id','mercado_livre_connection_id','omie_connection_id','marketplace_order_id'])
    external=quote(request['p_integration_reference']);source_ref=quote(request['p_source_order_reference']);sem='13'*32;civil='2026-10-03T11:12:13.123456'
    sql+='INSERT INTO public.marketplace_order_identity_registry(organization_id,marketplace_order_id,marketplace_key,external_order_id,currency) VALUES('+org+','+market+",'mercado-livre',"+external+",'BRL');\n"
    sql+='INSERT INTO public.marketplace_order_occurrence_source_promotion(organization_id,marketplace_order_id,source_connection_id,source_capability,source_input_progress_version,source_record_ordinal,outcome) VALUES('+org+','+market+','+ml+','+quote(ml_cap)+",1,0,'PROMOTED');\n"
    sql+='INSERT INTO public.integration_mercado_livre_order_source_observation(organization_id,connection_id,capability,input_progress_version,record_ordinal,external_order_ref,currency) VALUES('+org+','+ml+','+quote(ml_cap)+',1,0,'+external+",'BRL');\n"
    sql+='INSERT INTO public.integration_omie_transaction_evidence(organization_id,connection_id,capability,input_progress_version,record_ordinal,source_order_ref,source_integration_ref,currency) VALUES('+org+','+omie+','+quote(omie_cap)+',1,0,'+source_ref+','+external+",'BRL');\n"
    sql+='INSERT INTO public.integration_omie_transaction_evidence_v3(organization_id,connection_id,capability,input_progress_version,record_ordinal,provider_created_local,provider_modified_local,source_evidence_semantic_fingerprint,semantic_fingerprint_version) VALUES('+org+','+omie+','+quote(omie_cap)+',1,0,'+quote(civil)+',NULL,'+quote(sem)+',1);\n'
    sql+='INSERT INTO public.integration_connector_page_commit(organization_id,connection_id,capability,input_progress_version,record_count) VALUES('+org+','+omie+','+quote(omie_cap)+',1,1);\nINSERT INTO public.integration_connector_progress(organization_id,connection_id,capability,progress_version) VALUES('+org+','+omie+','+quote(omie_cap)+',2);\n'
    sql+='CREATE FUNCTION public.transaction_identity_progress_lock(uuid,uuid) RETURNS boolean LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $stub$ SELECT true $stub$; REVOKE ALL ON FUNCTION public.transaction_identity_progress_lock(uuid,uuid) FROM PUBLIC;\n'
    grant_fp=identity_hash(['command-authorization/1',ids['organization_id'],ids['principal_id'],ids['mercado_livre_connection_id'],ids['omie_connection_id'],ids['grant_id'],'1',request['p_permission'],'ENABLED','','fixture-grant','isolated',ids['correlation_id'],row['verified_at']])
    intent=identity_hash(['transaction-identity-intent/1',ids['organization_id'],ids['principal_id'],ids['mercado_livre_connection_id'],ids['omie_connection_id'],request['p_source_order_reference'],ids['marketplace_order_id'],'CONFIRMED','EXPLICIT_CONFIRMATION',request['p_provenance'],''])
    semantic=identity_hash(['transaction-identity/1',intent,ids['mercado_livre_connection_id'],ml_cap,'1','0',request['p_integration_reference'],'BRL',omie_cap,'1',sem,civil,ids['grant_id'],'1',request['p_permission'],'command-authorization/1',grant_fp])
    fields=frozen_tuple(spec,'S18','INPUT');fields=[(n,'timestamp' if n=='p_provider_revision_local' else t) for n,t in fields]
    values=[ids['organization_id'],ids['decision_id'],ids['omie_connection_id'],request['p_source_order_reference'],ids['marketplace_order_id'],'CONFIRMED','EXPLICIT_CONFIRMATION','1',None,ids['mercado_livre_connection_id'],ml_cap,'1','0',request['p_integration_reference'],'BRL',omie_cap,'1','0',sem,civil,ids['principal_id'],ids['credential_id'],'1',ids['grant_id'],'1',request['p_permission'],'command-authorization/1',grant_fp,intent,semantic,request['p_provenance'],ids['correlation_id']]+ctx['manifest'][1:]
    facts=dict(zip((n for n,t in fields[:54]),values));facts.update({'p_expected_'+n:v for n,v in accepted.items() if n!='schema_version'});facts['p_expected_evidence_binding_fingerprint']=accepted['signed_evidence_binding_fingerprint']
    # Actual current Kotlin writer + actual immutable snapshot/JCA, with mock
    # JDBC rows matching this same isolated fixture. Compare every APPLY value.
    work=ctx['work'];expected_vector=[facts[n] for n,t in fields]
    (work/'decision-facts.properties').write_text(''.join('ARG_'+str(i)+'='+('NULL' if v is None else str(v))+'\n' for i,v in enumerate(expected_vector,1)),encoding='utf-8',newline='\n')
    driver=list((verification.Path.home()/'.gradle/caches/modules-2/files-2.1/org.postgresql/postgresql').glob('*/*/*.jar'))
    if not driver:raise ValueError('Actual writer witness PostgreSQL driver unavailable')
    cp=str(work)+os.pathsep+ctx['cp']+os.pathsep+str(driver[-1])
    witness=gate.ROOT/'scripts/validation/Package0090DecisionWriterWitness.java'
    verification.run(['javac','-cp',cp,'-d',str(work),str(witness)])
    verification.run(['java','-cp',cp,'Package0090DecisionWriterWitness',str(work/'test.input'),str(work/'decision-facts.properties'),str(work/'writer-vector.properties')])
    actual=dict(line.split('=',1) for line in (work/'writer-vector.properties').read_text().splitlines())
    for i,((name,kind),value) in enumerate(zip(fields,expected_vector),1):
        observed=actual['ARG_'+str(i)];expected='NULL' if value is None else str(value)
        equal=verification.micros(observed)==verification.micros(expected) if kind=='timestamptz' else observed==expected
        if not equal:raise ValueError('Actual current writer argument mismatch '+str(i))
    ctx['actual_writer_oracle']={'argument_count':73,'private_fact_count':54,'expected_snapshot_count':19,'jca':'ACTUAL_IMMUTABLE_ACCEPTED_ATTESTATION_VERIFIER','jdbc':'MOCK_DETERMINISTIC_DOMAIN_ROWS','vector_sha256':hashlib.sha256((work/'writer-vector.properties').read_bytes()).hexdigest()}
    begin_in,begin_out=decision.frozen_signature(decision.FROZEN['BEGIN']);outputs={n:None for n,t in begin_out};outputs.update(outcome='READY',result_decision_id=ids['decision_id'],result_manifest_id=ids['manifest_id'])
    for n,v in accepted.items():outputs['result_'+n]=v
    sql+='CREATE FUNCTION public.'+decision.FROZEN['BEGIN']+'('+','.join(n+' pg_catalog.'+t for n,t in begin_in)+') RETURNS TABLE('+','.join(n+' pg_catalog.'+t for n,t in begin_out)+') LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $stub$ SELECT '+','.join('NULL::pg_catalog.'+t if outputs[n] is None else verification.sql_value(outputs[n],t) for n,t in begin_out)+' $stub$; REVOKE ALL ON FUNCTION public.'+decision.FROZEN['BEGIN']+'('+','.join('pg_catalog.'+t for n,t in begin_in)+') FROM PUBLIC;\n'
    outputs18=frozen_tuple(spec,'S18','OUTPUT');out18=dict(outcome='APPLIED',result_decision_id=ids['decision_id'],result_decision_semantic_fingerprint=semantic,result_decided_at=row['verified_at'])
    sql+='CREATE TABLE public.test_private_apply(counter integer); INSERT INTO public.test_private_apply VALUES(0);\n'
    checks=' OR '.join(n+' IS DISTINCT FROM '+('NULL::pg_catalog.'+t if facts[n] is None else verification.sql_value(facts[n],t)) for n,t in fields)
    sql+='CREATE FUNCTION public.'+decision.FROZEN['APPLY']+'('+','.join(n+' pg_catalog.'+t for n,t in fields)+') RETURNS TABLE('+','.join(n+' pg_catalog.'+t for n,t in outputs18)+') LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $stub$ BEGIN IF '+checks+" THEN RAISE EXCEPTION 'PRIVATE_WRITER_ORACLE_MISMATCH'; END IF; UPDATE public.test_private_apply SET counter=counter+1; IF (SELECT enabled FROM public.test_frozen_fault) THEN UPDATE public.offline_execution SET expires_at=clock_timestamp()-interval '1 second'; END IF; RETURN QUERY SELECT "+','.join(verification.sql_value(out18[n],t) for n,t in outputs18)+'; END $stub$; REVOKE ALL ON FUNCTION public.'+decision.FROZEN['APPLY']+'('+','.join('pg_catalog.'+t for n,t in fields)+') FROM PUBLIC;\n'
    sql+=decision.build(source,spec)
    for stage,name in decision.WRAPPERS.items():sql+=entry(stage,name,decision.TYPES[stage],('uuid','bytea'))
    caller=dict(decision_id=ids['decision_id'],source_order_reference=request['p_source_order_reference'],marketplace_order_id=ids['marketplace_order_id'],kind='CONFIRMED',reason='EXPLICIT_CONFIRMATION',provenance=request['p_provenance'],correlation_id=ids['correlation_id'],supersedes_decision_id=None)
    caller_bytes=encode_fields('S17/INPUT',decision.REQUEST,caller);snapshot_bytes=encode_fields('DECISION-ACCEPTED',decision.SNAPSHOT,accepted)
    ctx['decision_oracle']={'caller_request':caller_bytes,'accepted_snapshot':snapshot_bytes,'server_facts':encode_fields('DECISION-SERVER-FACTS',fields[:54],facts),'output18':encode_fields('S18/OUTPUT',outputs18,out18)}
    sql+='CREATE TABLE public.test_preparation(data bytea); GRANT INSERT(data) ON public.test_preparation TO test_executor; CREATE FUNCTION public.test_prepare() RETURNS bytea LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $entry$ SELECT public.test_s17(a.admission_id,decode('+quote(caller_bytes.hex())+",'hex')) FROM public.offline_admission a $entry$; GRANT EXECUTE ON FUNCTION public.test_prepare() TO test_executor; BEGIN; SET SESSION AUTHORIZATION test_executor; INSERT INTO public.test_preparation SELECT public.test_prepare(); RESET SESSION AUTHORIZATION;\n"
    sql+="SAVEPOINT replay_test; INSERT INTO public.marketplace_transaction_identity_decision(organization_id,decision_id) VALUES("+org+','+quote(ids['decision_id'])+"); SET SESSION AUTHORIZATION test_executor; DO $replay$ BEGIN BEGIN PERFORM public.test_prepare(); RAISE EXCEPTION 'REPLAY_ROUTE_MISSING'; EXCEPTION WHEN SQLSTATE 'P0017' THEN IF SQLERRM<>'REPLAY_INSPECTION_REQUIRED' THEN RAISE EXCEPTION 'REPLAY_ROUTE_UNSANITIZED'; END IF; END; END $replay$; RESET SESSION AUTHORIZATION; ROLLBACK TO SAVEPOINT replay_test; RELEASE SAVEPOINT replay_test;\n"
    sql+='CREATE FUNCTION public.test_apply(bytea) RETURNS bytea LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $entry$ SELECT public.test_s18(a.admission_id,$1) FROM public.offline_admission a $entry$; GRANT EXECUTE ON FUNCTION public.test_apply(bytea) TO test_executor;\n'
    sql+="DO $mutated$ DECLARE original bytea;BEGIN SELECT data INTO original FROM public.test_preparation; SET SESSION AUTHORIZATION test_executor; BEGIN PERFORM public.test_apply(original||decode('00','hex')); RAISE EXCEPTION 'DENIAL_MISSING'; EXCEPTION WHEN SQLSTATE 'P0017' THEN NULL; END; RESET SESSION AUTHORIZATION; IF (SELECT counter FROM public.test_private_apply)<>0 THEN RAISE EXCEPTION 'ALTERED_ENVELOPE_EFFECT'; END IF; END $mutated$;\n"
    for change in ["UPDATE public.command_permission_grant SET state='DISABLED'", "UPDATE public.integration_omie_transaction_evidence_v3 SET source_evidence_semantic_fingerprint=repeat('14',32)"]:
        sql+='SAVEPOINT drift_test; '+change+"; DO $drift$ DECLARE original bytea;BEGIN SELECT data INTO original FROM public.test_preparation; SET SESSION AUTHORIZATION test_executor; BEGIN PERFORM public.test_apply(original); RAISE EXCEPTION 'DRIFT_NOT_DENIED'; EXCEPTION WHEN SQLSTATE 'P0017' THEN IF SQLERRM<>'ACCESS_DENIED' THEN RAISE EXCEPTION 'UNSANITIZED_DRIFT'; END IF; END; RESET SESSION AUTHORIZATION; IF (SELECT counter FROM public.test_private_apply)<>0 THEN RAISE EXCEPTION 'DRIFT_EFFECT'; END IF; END $drift$; ROLLBACK TO SAVEPOINT drift_test; RELEASE SAVEPOINT drift_test;\n"
    sql+="UPDATE public.test_frozen_fault SET enabled=true; DO $late$ DECLARE original bytea;BEGIN SELECT data INTO original FROM public.test_preparation; SET SESSION AUTHORIZATION test_executor; BEGIN PERFORM public.test_apply(original); RAISE EXCEPTION 'LATE_EXPIRY_NOT_DENIED'; EXCEPTION WHEN SQLSTATE 'P0017' THEN NULL; END; RESET SESSION AUTHORIZATION; IF (SELECT counter FROM public.test_private_apply)<>0 OR (SELECT durable_state FROM public.offline_admission)<>'ISSUED' OR (SELECT expires_at FROM public.offline_execution)<=clock_timestamp() OR (SELECT state FROM public.offline_attempt)<>'EFFECTS_IN_PROGRESS' THEN RAISE EXCEPTION 'TENTATIVE_COMPLETION_NOT_ROLLED_BACK'; END IF; END $late$; UPDATE public.test_frozen_fault SET enabled=false;\n"
    sql+="DO $applied$ DECLARE original bytea;actual bytea;BEGIN SELECT data INTO original FROM public.test_preparation; SET SESSION AUTHORIZATION test_executor; actual:=public.test_apply(original); RESET SESSION AUTHORIZATION; IF actual IS DISTINCT FROM decode("+quote(encode_fields('S18/OUTPUT',outputs18,out18).hex())+",'hex') THEN RAISE EXCEPTION 'S18_GOLDEN_MISMATCH'; END IF; END $applied$;\n"
    for stage,table in [('S13','test_claim_bytes'),('S14','test_delivery_bytes'),('S15','test_report_bytes'),('S16','test_admission_bytes'),('S17','test_preparation')]:sql+="SELECT 'MUTATION_GOLDEN_"+stage+"='||encode(data,'hex') FROM public."+table+';\n'
    sql+="SELECT 'MUTATION_BINDING='||encode(h.plan_fingerprint,'hex')||':'||a.admission_id::text FROM public.offline_binding_header h JOIN public.offline_admission a ON a.binding_id=h.binding_id;\n"
    sql+="DO $complete$ BEGIN IF (SELECT counter FROM public.test_private_apply)<>1 OR (SELECT durable_state FROM public.offline_admission)<>'CONSUMED' OR (SELECT state FROM public.offline_attempt)<>'EFFECTS_COMPLETE' OR (SELECT state FROM public.offline_execution)<>'RELEASED' OR (SELECT state FROM public.offline_reconciliation)<>'REQUIRED' OR (SELECT result FROM public.offline_ceremony_result)<>'NONE' OR (SELECT count(*) FROM public.offline_stage_receipt)<>5 THEN RAISE EXCEPTION 'ATOMIC_COMPLETION_MISSING'; END IF; END $complete$;\nCOMMIT;\nSELECT 'MUTATION_ISOLATED_PASS';\n"
    return sql

def review():
    captured={}
    def extend(sql,ctx):
        result=augment(sql,ctx);captured.update(ctx);return result
    def observe(output):
        if 'MUTATION_ISOLATED_PASS' not in output:raise ValueError('Mutation rehearsal incomplete')
        public={stage:bytes.fromhex(value) for stage,value in re.findall(r'MUTATION_GOLDEN_(S\d+)=(\w+)',output)}
        for stage in ('S13','S14','S15','S16'):
            fields=control.outputs(captured['spec'],stage);values=decode_frame(public[stage],'FLOOOW/OFFLINE-FIELD-PROOF/'+stage+'/OUTPUT/V1',len(fields))
            for (name,kind),value in zip(fields,values):
                size={'uuid':16,'int8':8,'int4':4,'timestamptz':8,'bool':1}.get(kind)
                if size is not None and len(value)!=size:raise ValueError('Typed output length')
                if kind=='bool' and value not in (b'\x00',b'\x01'):raise ValueError('Noncanonical boolean')
        fp,admission=re.search(r'MUTATION_BINDING=(\w+):([0-9a-f-]+)',output).groups();oracle=captured['decision_oracle']
        values=[uuid.UUID(captured['binding']).bytes,bytes.fromhex(fp),uuid.UUID(captured['incarnation']).bytes,b'0090-v1',uuid.UUID(captured['attempt']).bytes,struct.pack('>q',1),uuid.UUID(captured['execution']).bytes,uuid.UUID(captured['instance']).bytes,uuid.UUID(admission).bytes,oracle['caller_request'],oracle['server_facts'],oracle['accepted_snapshot']]
        digest=hashlib.sha256(frame('FLOOOW/OFFLINE-FIELD-PROOF/DECISION-PREPARATION/V1',[present(v) for v in values])).digest()
        expected=frame('FLOOOW/OFFLINE-FIELD-PROOF/S17/OUTPUT/V1',[present(oracle['caller_request']),present(digest),present(oracle['accepted_snapshot'])])
        if public['S17']!=expected:raise ValueError('Independent private preparation commitment golden mismatch')
        goldens=captured['mutation_goldens'];goldens.update({s:{'output_hex':v.hex()} for s,v in public.items()});goldens['S17']['input_hex']=oracle['caller_request'].hex();goldens['S18']={'input_hex':expected.hex(),'output_hex':oracle['output18'].hex()}
        artifact={'scope':'ISOLATED_MOCK_FROZEN_TRANSPORTS','goldens':goldens,'private_test_only':{'server_facts_hex':oracle['server_facts'].hex(),'accepted_snapshot_hex':oracle['accepted_snapshot'].hex(),'preparation_digest_hex':digest.hex()},'output_oracle':'INDEPENDENT_PYTHON_FRAMING_AND_FULL_PRIVATE_PREPARATION_COMMITMENT'}
        (gate.ROOT/'docs/evidence/PACKAGE-0090-S07-S18-TRANSPORT-GOLDENS.json').write_text(json.dumps(artifact,indent=2)+'\n')
    result=verification.review(extension=extend,observer=observe)
    return {'status':'PASS_ACTUAL_S07_S18_WITH_EXPLICIT_STUB_DEPENDENCIES','source_bodies':'ACTUAL_I_E','independent_private_apply_oracle':'ALL_54_FACTS_AND_19_SNAPSHOT_ARGUMENTS','actual_current_writer_oracle':captured['actual_writer_oracle'],'frozen_pure_identity_helpers':'UNCHANGED_V035_SQL','s17_s18_sql_transaction':'SAME_CONNECTION_SAME_READ_COMMITTED_TRANSACTION','v043_source_sha256':hashlib.sha256((gate.ROOT/gate.V043).read_text().encode()).hexdigest(),'v043_executed':False,'protected_database_connection':False,'production_policy':False,'limitations':['Frozen V041/V042 operational transports and P/Q/progress dependencies are stubs; actual writer/JCA uses mock JDBC rows. This is not frozen SQL semantic parity, the new adapter integration or deployed full ACL certification.'],'base_verification':result}

if __name__=='__main__':
    result=review();(gate.ROOT/'docs/evidence/PACKAGE-0090-S07-S18-ISOLATED-REVIEW.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
