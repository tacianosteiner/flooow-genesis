"""S05/S06 actual bodies and ACLs, native crypto, stub frozen transports in scratch.

Frozen stubs are explicitly NOT V041 semantic certification. Never runs V043.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import tempfile
import uuid
from datetime import datetime
import package_0090_source_gate as gate
from package_0090_ed25519_review import BUILDER, EXPECTED_BUILDER_ID,NATIVE
from package_0090_s02_isolated_review import run,quote,canonical
from package_0090_s02_expected_attestation_audit import fixture_input
from build_package_0090_original_match_source import build as match_build
from build_package_0090_expected_attestation_source import build as expected_build
from build_package_0090_verification_source import build as verification_build,header_fields,header_fingerprint,WRAPPERS,TYPES
from package_0090_typed_transport_source import frozen_tuple
from package_0090_evidence_fixture import frame,present
from package_0090_policy_fixture import encode as policy_encode

def micros(value):
    d=datetime.fromisoformat(value.replace('Z','+00:00'));epoch=datetime.fromisoformat('1970-01-01T00:00:00+00:00')
    delta=d-epoch;return delta.days*86400000000+delta.seconds*1000000+delta.microseconds

def scalar(value,kind):
    if kind=='uuid':return uuid.UUID(value).bytes
    if kind=='int4':return struct.pack('>i',int(value))
    if kind=='timestamptz':return struct.pack('>q',micros(value))
    if kind=='bytea':return bytes.fromhex(value)
    if kind=='text':return value.encode()
    raise ValueError(kind)

def sql_value(value,kind):
    if kind=='bytea':return 'decode('+quote(value)+",'hex')"
    return quote(value)+'::pg_catalog.'+kind

def review():
    if run(['docker','image','inspect',BUILDER,'--format','{{.Id}}']).strip()!=EXPECTED_BUILDER_ID:raise ValueError('Builder changed')
    source=(gate.ROOT/gate.V043).read_text();spec=(gate.ROOT/gate.SPEC).read_text()
    with tempfile.TemporaryDirectory(prefix='flooow-0090-verification-') as scratch:
        work=Path(scratch);stdlib=list((Path.home()/'.gradle/caches/modules-2/files-2.1/org.jetbrains.kotlin/kotlin-stdlib/2.3.21').glob('*/*.jar'))[0]
        classes=list(gate.ROOT.glob('applications/*/build/classes/kotlin/main'))+list(gate.ROOT.glob('platform/foundation/*/build/classes/kotlin/main'))
        cp=os.pathsep.join(map(str,[*classes,stdlib]));(work/'test.input').write_text(fixture_input(),encoding='utf-8',newline='\n')
        run(['javac','-cp',cp,'-d',scratch,str(gate.ROOT/'scripts/validation/Package0090S02ExpectedAttestationWitness.java')])
        run(['java','-cp',scratch+os.pathsep+cp,'Package0090S02ExpectedAttestationWitness',str(work/'test.input'),str(work/'rows.properties')])
        values=dict(line.split('=',1) for line in (work/'rows.properties').read_text().splitlines())
        row={k.removeprefix('ROW_A_'):v for k,v in values.items() if k.startswith('ROW_A_')}
        original={k.removeprefix('ORIGINAL_A_'):v for k,v in values.items() if k.startswith('ORIGINAL_A_')}
        data=bytes.fromhex(row['canonical_manifest_bytes']);manifest=[];cursor=0
        while cursor<len(data):
            length=int.from_bytes(data[cursor:cursor+4],'big');cursor+=4;manifest.append(data[cursor:cursor+length].decode());cursor+=length
        inputs=frozen_tuple(spec,'S05','INPUT');request={n:manifest[i+1] for i,(n,t) in enumerate(inputs[:22])}
        request.update(p_canonicalization_version='1',p_canonical_manifest_bytes=data.hex(),p_manifest_digest=original['manifest_digest'],p_algorithm_id=original['algorithm_id'],p_signer_key_id=original['signer_key_id'],p_signer_key_fingerprint=original['signer_key_fingerprint'],p_signature_bytes=original['signature_bytes'])
        request.update(p_expected_canonical_signature_preimage_bytes=row['canonical_signature_preimage_bytes'],p_expected_signer_subject_id=str(uuid.UUID(int=300)),p_expected_signer_key_revision=row['signer_key_revision'],p_expected_signer_key_lineage_fingerprint=row['signer_key_lineage_fingerprint'],p_expected_subject_public_key_info_der=row['subject_public_key_info_der'],p_expected_signer_authority_id=row['signer_authority_id'],p_expected_signer_authority_revision=row['signer_authority_revision'],p_expected_signer_authority_fingerprint=row['signer_authority_fingerprint'],p_expected_accepted_proof_fingerprint=row['accepted_proof_fingerprint'])
        encoded={s:frame('FLOOOW/OFFLINE-FIELD-PROOF/'+s+'/INPUT/V1',[present(scalar(request[n],t)) for n,t in frozen_tuple(spec,s,'INPUT')]) for s in ('S05','S06')}
        outputs05={n:row[n.removeprefix('result_')] for n,t in frozen_tuple(spec,'S05','OUTPUT') if n not in ('outcome','result_signer_subject_id')}
        outputs05.update(outcome='VERIFY_REPLAY',result_signer_subject_id=str(uuid.UUID(int=300)))
        outputs06=dict(outcome='ALREADY_ACCEPTED',result_organization_id=request['p_organization_id'],result_manifest_id=request['p_manifest_id'],result_manifest_digest=row['manifest_digest'],result_accepted_proof_fingerprint=row['accepted_proof_fingerprint'],result_verified_at=row['verified_at'],result_recorded_at=row['recorded_at'])
        expected_outputs={s:frame('FLOOOW/OFFLINE-FIELD-PROOF/'+s+'/OUTPUT/V1',[present(scalar((outputs05 if s=='S05' else outputs06)[n],t)) for n,t in frozen_tuple(spec,s,'OUTPUT')]) for s in ('S05','S06')}
        roles=['test_verifier','test_issuer','test_executor','test_auditor']
        sql=''.join('CREATE ROLE '+r+' LOGIN NOINHERIT;\n' for r in roles)+''.join('CREATE ROLE '+r+' NOLOGIN '+('INHERIT' if r.endswith('control_owner') else 'NOINHERIT')+';\n' for r in ['flooow_offline_control_owner','flooow_offline_verification_owner','flooow_offline_audit_owner'])
        tables={'offline_binding_header':header_fields(source)}
        for table in ['offline_binding_lifecycle','offline_attempt_pointer','offline_attempt','offline_execution','offline_stage_receipt','offline_reconciliation','offline_ceremony_result','offline_readiness','offline_deadline_policy']:
            import re
            block=source.split('CREATE TABLE public.'+table+' (',1)[1].split('\n);',1)[0]
            tables[table]=re.findall(r'^    ([a-z_]+) pg_catalog\.([a-z0-9]+)',block,re.M)
        for table,fields in tables.items():
            sql+='CREATE TABLE public.'+table+'('+','.join(n+' pg_catalog.'+t for n,t in fields)+(',PRIMARY KEY(binding_id)' if table=='offline_binding_header' else '')+');\nALTER TABLE public.'+table+' OWNER TO flooow_offline_control_owner;\n'
        # Exact source column ACLs for V on only the mock controls in this test.
        for o,r,c,p in sorted(gate.expected_column_grants(spec)):
            if o=='flooow_offline_verification_owner' and r.removeprefix('public.') in tables:sql+='GRANT '+p.upper()+'('+c+') ON '+r+' TO '+o+';\n'
        binding=str(uuid.UUID(int=999));incarnation=str(uuid.UUID(int=333));attempt=str(uuid.UUID(int=600));execution=str(uuid.UUID(int=601));instance=str(uuid.UUID(int=602));secret='03'*32
        header={n:(quote(str(uuid.UUID(int=1000+i))) if t=='uuid' else "'1'" if t=='text' else "decode(repeat('01',32),'hex')" if t=='bytea' else '1' if t=='int4' else "clock_timestamp()-interval '1 second'") for i,(n,t) in enumerate(tables['offline_binding_header'])}
        header.update(binding_id=quote(binding),deployment_incarnation_id=quote(incarnation),offline_surface_version="'0090-v1'",deadline_policy_version="'TEST-RUNTIME-ONLY'",expires_at="clock_timestamp()+interval '30 seconds'",canonical_manifest_bytes="decode("+quote(data.hex())+",'hex')",manifest_digest="decode("+quote(row['manifest_digest'])+",'hex')",canonical_manifest_hash="decode("+quote(row['manifest_digest'])+",'hex')")
        for name in ['organization_id','manifest_id','mercado_livre_connection_id','omie_connection_id','marketplace_order_id','source_order_reference','integration_reference','permission','reason','provenance','correlation_id']:header[name]=quote(request['p_'+name])
        slots="int4send(4)||(SELECT string_agg(int4send(9+octet_length(convert_to(r.rolname,'UTF8')))||decode(lpad(to_hex(x.slot),2,'0'),'hex')||oidsend(r.oid)||int4send(octet_length(convert_to(r.rolname,'UTF8')))||convert_to(r.rolname,'UTF8'),''::bytea ORDER BY x.slot) FROM (VALUES "+','.join('('+str(i)+','+quote(r)+')' for i,r in enumerate(roles,1))+') x(slot,name) JOIN pg_roles r ON r.rolname=x.name)'
        header['identity_slots']=slots
        # Isolated test duration vector, never production provisioning/approval.
        policy=policy_encode('TEST-RUNTIME-ONLY',[v for i in range(14) for v in ((1000000,2000000) if i==12 else (60000000,120000000))])
        digest=hashlib.sha256(policy).hexdigest();header['deadline_policy_digest']="decode("+quote(digest)+",'hex')"
        sql+='INSERT INTO public.offline_binding_header('+','.join(header)+') VALUES('+','.join(header.values())+');\n'
        sql+='DO $fingerprint$ DECLARE header_record record; BEGIN SELECT * INTO header_record FROM public.offline_binding_header; UPDATE public.offline_binding_header SET plan_fingerprint=sha256('+header_fingerprint(tables['offline_binding_header'])+'); END; $fingerprint$;\n'
        sql+='INSERT INTO public.offline_binding_lifecycle(binding_id,state,lock_token) VALUES('+quote(binding)+",'ACTIVE',0);\n"
        sql+='INSERT INTO public.offline_attempt_pointer(binding_id,current_attempt_id,generation,claim_permitted,lock_token) VALUES('+quote(binding)+','+quote(attempt)+',1,true,0);\n'
        sql+='INSERT INTO public.offline_attempt(binding_id,attempt_id,generation,state,claimed_at,expires_at,lock_token) VALUES('+quote(binding)+','+quote(attempt)+",1,'CLAIMED',clock_timestamp()-interval '1 second',(SELECT expires_at FROM public.offline_binding_header),0);\n"
        sql+='INSERT INTO public.offline_execution(binding_id,attempt_id,generation,execution_id,instance_id,executor_oid,state,possession_digest,claimed_at,expires_at,lock_token) VALUES('+quote(binding)+','+quote(attempt)+',1,'+quote(execution)+','+quote(instance)+",(SELECT oid FROM pg_roles WHERE rolname='test_executor'),'OWNED',sha256(decode("+quote(secret)+",'hex')),(SELECT claimed_at FROM public.offline_attempt),(SELECT expires_at FROM public.offline_attempt),0);\n"
        sql+='INSERT INTO public.offline_reconciliation(binding_id,state) VALUES('+quote(binding)+",'NOT_STARTED');\nINSERT INTO public.offline_ceremony_result(binding_id,result) VALUES("+quote(binding)+",'NONE');\n"
        sql+='INSERT INTO public.offline_deadline_policy(policy_version,policy_digest,canonical_policy,effective_from) VALUES(\'TEST-RUNTIME-ONLY\',decode('+quote(digest)+",'hex'),decode("+quote(policy.hex())+",'hex'),clock_timestamp()-interval '1 second');\n"
        sql+="INSERT INTO public.offline_readiness(deployment_id,incarnation_id,state,policy_version,policy_digest,watchdog_checked_at,watchdog_healthy) SELECT deployment_id,deployment_incarnation_id,'READY',deadline_policy_version,deadline_policy_digest,clock_timestamp(),true FROM public.offline_binding_header;\n"
        commitment=expected_build()
        reverse=commitment[commitment.index('ALTER TABLE public.offline_binding_header ADD CONSTRAINT'):commitment.index('CREATE FUNCTION public.offline_internal_expected_attestation_guard')]
        sql+=commitment.replace(reverse,'')
        original=dict(binding_id=binding,**original);original.update(canonical_expected_attestation=canonical(original).hex(),commitment_digest=hashlib.sha256(canonical(original)).hexdigest())
        sql+='INSERT INTO public.offline_expected_signed_attestation('+','.join(original)+') VALUES('+','.join(sql_value(v,'bytea' if n in ['signature_bytes','canonical_expected_attestation','commitment_digest'] else 'uuid' if n in ['binding_id','signer_key_id'] else 'text') for n,v in original.items())+');\n'+reverse+match_build(source)
        sql+='CREATE SCHEMA offline_crypto;\nCREATE FUNCTION offline_crypto.canonical_spki_ed25519_verify(bytea,bytea,bytea) RETURNS boolean AS \'/work/native/flooow_offline_mac32\',\'canonical_spki_ed25519_verify\' LANGUAGE C IMMUTABLE STRICT;\nREVOKE ALL ON FUNCTION offline_crypto.canonical_spki_ed25519_verify(bytea,bytea,bytea) FROM PUBLIC;\nGRANT USAGE ON SCHEMA offline_crypto TO flooow_offline_verification_owner;\nGRANT EXECUTE ON FUNCTION offline_crypto.canonical_spki_ed25519_verify(bytea,bytea,bytea) TO flooow_offline_verification_owner;\n'
        sql+='CREATE FUNCTION public.offline_internal_canonical_spki_ed25519_verify(bytea,bytea,bytea) RETURNS boolean LANGUAGE sql IMMUTABLE STRICT SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $v$ SELECT offline_crypto.canonical_spki_ed25519_verify($1,$2,$3) $v$;\nALTER FUNCTION public.offline_internal_canonical_spki_ed25519_verify(bytea,bytea,bytea) OWNER TO flooow_offline_verification_owner;\nREVOKE ALL ON FUNCTION public.offline_internal_canonical_spki_ed25519_verify(bytea,bytea,bytea) FROM PUBLIC;\n'
        sql+='CREATE TABLE public.test_frozen_effects(counter integer); INSERT INTO public.test_frozen_effects VALUES(0); CREATE TABLE public.test_frozen_fault(enabled boolean); INSERT INTO public.test_frozen_fault VALUES(false);\n'
        for stage,name in [('S05','s2a_begin_attestation_verification'),('S06','s2a_persist_attestation_verification_result')]:
            ins=frozen_tuple(spec,stage,'INPUT');outs=frozen_tuple(spec,stage,'OUTPUT');result=outputs05 if stage=='S05' else outputs06
            effects=''
            if stage=='S06':
                effects="IF "+' OR '.join(n+' IS DISTINCT FROM '+sql_value(request[n],t) for n,t in ins[29:])+" THEN RAISE EXCEPTION USING ERRCODE='P0018',MESSAGE='STUB_SNAPSHOT_MISMATCH'; END IF; UPDATE public.test_frozen_effects SET counter=counter+1; IF (SELECT enabled FROM public.test_frozen_fault) THEN UPDATE public.offline_execution SET expires_at=clock_timestamp()-interval '1 second'; END IF; "
            sql+='CREATE FUNCTION public.'+name+'('+','.join(n+' pg_catalog.'+t for n,t in ins)+') RETURNS TABLE('+','.join(n+' pg_catalog.'+t for n,t in outs)+') LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $stub$ BEGIN '+effects+'RETURN QUERY SELECT '+','.join(sql_value(result[n],t) for n,t in outs)+'; END; $stub$;\nREVOKE ALL ON FUNCTION public.'+name+'('+','.join('pg_catalog.'+t for n,t in ins)+') FROM PUBLIC;\n'
        sql+=verification_build(source,spec)
        for name in WRAPPERS.values():sql+='GRANT EXECUTE ON FUNCTION public.'+name+'('+','.join('pg_catalog.'+t for t in TYPES)+') TO test_verifier;\n'
        # Test-only minimal header-read entry supplies public arguments without
        # granting header SELECT to the operational login.
        for stage,name in WRAPPERS.items():
            sql+='CREATE FUNCTION public.test_'+stage.lower()+'(bytea) RETURNS bytea LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $entry$ SELECT public.'+name+'(h.binding_id,h.plan_fingerprint,h.deployment_incarnation_id,h.offline_surface_version,'+quote(attempt)+',1,'+quote(execution)+','+quote(instance)+",decode("+quote(secret)+",'hex'),$1) FROM public.offline_binding_header h $entry$;\nREVOKE ALL ON FUNCTION public.test_"+stage.lower()+'(bytea) FROM PUBLIC;\nGRANT EXECUTE ON FUNCTION public.test_'+stage.lower()+'(bytea) TO '+','.join(roles)+';\n'
        def assertion(stage,data,deny=False):
            call='public.test_'+stage.lower()+"(decode("+quote(data.hex())+",'hex'))"
            if deny:return "DO $deny$ BEGIN BEGIN PERFORM "+call+"; RAISE EXCEPTION 'DENIAL_MISSING'; EXCEPTION WHEN SQLSTATE 'P0017' THEN IF SQLERRM<>'ACCESS_DENIED' THEN RAISE EXCEPTION 'UNSANITIZED'; END IF; END; END; $deny$;\n"
            return "DO $assert$ BEGIN IF "+call+' IS DISTINCT FROM decode('+quote(expected_outputs[stage].hex())+",'hex') THEN RAISE EXCEPTION 'OUTPUT_GOLDEN_MISMATCH'; END IF; END; $assert$;\n"
        sql+='SET SESSION AUTHORIZATION test_verifier;\n'+assertion('S05',encoded['S05'])+assertion('S06',encoded['S06'])+assertion('S06',encoded['S06'])+'RESET SESSION AUTHORIZATION;\n'
        sql+="DO $effects$ BEGIN IF (SELECT count(*) FROM public.offline_stage_receipt)<>1 OR (SELECT state FROM public.offline_attempt)<>'EFFECTS_IN_PROGRESS' THEN RAISE EXCEPTION 'STAGE_REPLAY_DUPLICATED'; END IF; END; $effects$;\n"
        negatives=[]
        for stage in ('S05','S06'):
            for changed,label in [(encoded[stage]+b'\x00','TRAILING'),(encoded[stage][:-1],'TRUNCATED'),(bytes(len(encoded[stage])),'WRONG_DOMAIN')]:
                sql+='SET SESSION AUTHORIZATION test_verifier;\n'+assertion(stage,changed,True)+'RESET SESSION AUTHORIZATION;\n';negatives.append(stage+'_'+label)
            sql+='SET SESSION AUTHORIZATION test_issuer;\n'+assertion(stage,encoded[stage],True)+'RESET SESSION AUTHORIZATION;\n';negatives.append(stage+'_WRONG_SESSION')
        sql+="BEGIN; UPDATE public.offline_execution SET expires_at=clock_timestamp()-interval '1 second'; SET SESSION AUTHORIZATION test_verifier;\n"+assertion('S06',encoded['S06'],True)+'RESET SESSION AUTHORIZATION; ROLLBACK;\n'
        sql+="UPDATE public.test_frozen_fault SET enabled=true; SET SESSION AUTHORIZATION test_verifier;\n"+assertion('S06',encoded['S06'],True)+"RESET SESSION AUTHORIZATION; DO $rollback$ BEGIN IF (SELECT counter FROM public.test_frozen_effects)<>2 OR (SELECT expires_at FROM public.offline_execution)<=clock_timestamp() THEN RAISE EXCEPTION 'TENTATIVE_EFFECT_NOT_ROLLED_BACK'; END IF; END; $rollback$;\n"
        sql+='SELECT \'VERIFICATION_ISOLATED_PASS\';\n'
        (work/'review.sql').write_text(sql,encoding='utf-8',newline='\n');shutil.copytree(NATIVE,work/'native')
        script='''set -eu
cd /work/native
make with_llvm=no >/work/build.log 2>&1
mkdir /tmp/pgdata /tmp/pgsocket
chown postgres:postgres /tmp/pgdata /tmp/pgsocket
runuser -u postgres -- /usr/lib/postgresql/18/bin/initdb -D /tmp/pgdata -A trust >/work/init.log
runuser -u postgres -- /usr/lib/postgresql/18/bin/pg_ctl -D /tmp/pgdata -l /tmp/pgserver.log -o "-k /tmp/pgsocket -c listen_addresses=''" start >/work/start.log
/usr/lib/postgresql/18/bin/psql -X -v ON_ERROR_STOP=1 -h /tmp/pgsocket -U postgres -d postgres -f /work/review.sql >/work/result.log 2>&1 || { cat /work/result.log; exit 1; }
cat /work/result.log
'''
        (work/'run.sh').write_text(script,encoding='ascii',newline='\n')
        output=run(['docker','run','--rm','--network','none','--entrypoint','sh','--mount',f'type=bind,source={work},target=/work',BUILDER,'/work/run.sh'])
        if 'VERIFICATION_ISOLATED_PASS' not in output:raise ValueError('Incomplete rehearsal')
        golden={s:dict(input_hex=encoded[s].hex(),output_hex=expected_outputs[s].hex()) for s in ('S05','S06')}
        (gate.ROOT/'docs/evidence/PACKAGE-0090-S05-S06-TRANSPORT-GOLDENS.json').write_text(json.dumps(dict(scope='ISOLATED_TEST_ONLY',frozen_transports='STUB_NOT_V041_PARITY',goldens=golden),indent=2)+'\n')
    return dict(status='PASS_ISOLATED_WRAPPERS_STUB_FROZEN_TRANSPORTS',native_crypto='ACTUAL_C',source_bodies='ACTUAL_S05_S06',output_goldens='INDEPENDENT_PYTHON_TYPED_CODEC',negatives=negatives+['EXPIRED_EXECUTION','POST_FROZEN_EXPIRY_ROLLS_BACK_EFFECT'],stage_replay='ONE_UNCHANGED_RECEIPT',sql_sha256=hashlib.sha256(sql.encode()).hexdigest(),v043_executed=False,protected_database_connection=False,production_policy=False,limitations=['V041 BEGIN/PERSIST are stubbed transports; this does not prove frozen semantic parity or complete deployment ACL closure.'])

if __name__=='__main__':
    result=review();(gate.ROOT/'docs/evidence/PACKAGE-0090-S05-S06-ISOLATED-REVIEW.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
