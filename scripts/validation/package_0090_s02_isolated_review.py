"""Disposable, network-disabled predicate test. NEVER executes the V043 migration.

Builds mock domain transports from frozen column types, installs the native
candidate only in disposable scratch, and executes the generated accepted block.
ACL/whole-wrapper/guard safety remains separately source-gated, not certified here.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile
import uuid
import package_0090_source_gate as gate
from package_0090_s02_expected_attestation_audit import fixture_input
from build_package_0090_expected_attestation_source import build as commitment_sql, DOMAIN
from build_package_0090_s02_source import accepted_block, declarations
from package_0090_ed25519_review import BUILDER, EXPECTED_BUILDER_ID, NATIVE

def run(args):
    result=subprocess.run(args,capture_output=True,text=True)
    if result.returncode:raise RuntimeError(result.stdout+'\n'+result.stderr)
    return result.stdout

def quote(value):return "'"+str(value).replace("'","''")+"'"

def canonical(values):
    domain=DOMAIN.encode()
    payloads=[uuid.UUID(values['binding_id']).bytes,values['manifest_digest'].encode(),values['algorithm_id'].encode(),
              uuid.UUID(values['signer_key_id']).bytes,values['signer_key_fingerprint'].encode(),bytes.fromhex(values['signature_bytes'])]
    return struct.pack('>I',len(domain))+domain+struct.pack('>H',6)+b''.join(struct.pack('>HI',tag,len(p)+1)+b'\x01'+p for tag,p in enumerate(payloads,1))

def frozen_types():
    result={}
    for name in ('V034','V037','V040','V041','V042'):
        path=next((gate.ROOT/gate.MIGRATIONS).glob(name+'__*.sql'))
        from pglast.parser import parse_sql_json
        statements=[x['stmt'] for x in json.loads(parse_sql_json(path.read_text(encoding='utf-8-sig')))['stmts']]
        for statement in statements:
            if 'AlterTableStmt' in statement:
                alter=statement['AlterTableStmt'];table=alter['relation']['relname']
                for command in alter.get('cmds',[]):
                    column=command.get('AlterTableCmd',{}).get('def',{}).get('ColumnDef')
                    if column and table in result:result[table][column['colname']]=column['typeName']['names'][-1]['String']['sval']
            if 'CreateStmt' not in statement:continue
            table=statement['CreateStmt']; columns={}
            for item in table['tableElts']:
                if 'ColumnDef' not in item:continue
                column=item['ColumnDef'];typename=column['typeName']['names'][-1]['String']['sval']
                columns[column['colname']]=typename
            result[table['relation']['relname']]=columns
    return result

def insert(table,values,types):
    return 'INSERT INTO public.'+table+'('+','.join(values)+') VALUES('+','.join(
        'pg_catalog.decode('+quote(v)+",'hex')" if types[k]=='bytea' else quote(v) for k,v in values.items())+');\n'

def rejection(sql):
    return "DO $negative$ BEGIN BEGIN "+sql+" RAISE EXCEPTION 'NEGATIVE_DID_NOT_REJECT'; EXCEPTION WHEN unique_violation OR check_violation OR foreign_key_violation OR invalid_parameter_value OR object_not_in_prerequisite_state THEN NULL; END; END; $negative$;\n"

def review():
    if run(['docker','image','inspect',BUILDER,'--format','{{.Id}}']).strip()!=EXPECTED_BUILDER_ID:raise ValueError('Builder identity changed')
    types=frozen_types()
    stdlib=list((Path.home()/'.gradle/caches/modules-2/files-2.1/org.jetbrains.kotlin/kotlin-stdlib/2.3.21').glob('*/*.jar'))
    classes=list(gate.ROOT.glob('applications/*/build/classes/kotlin/main'))+list(gate.ROOT.glob('platform/foundation/*/build/classes/kotlin/main'))
    cp=os.pathsep.join(map(str,[*classes,stdlib[0]]))
    with tempfile.TemporaryDirectory(prefix='flooow-0090-s02-isolated-') as scratch:
        work=Path(scratch);(work/'test.input').write_text(fixture_input(),encoding='utf-8',newline='\n')
        run(['javac','-cp',cp,'-d',scratch,str(gate.ROOT/'scripts/validation/Package0090S02ExpectedAttestationWitness.java')])
        witness=run(['java','-cp',scratch+os.pathsep+cp,'Package0090S02ExpectedAttestationWitness',str(work/'test.input'),str(work/'rows.properties')])
        values=dict(line.split('=',1) for line in (work/'rows.properties').read_text().splitlines())
        rows={label:{k.removeprefix('ROW_'+label+'_'):v for k,v in values.items() if k.startswith('ROW_'+label+'_')} for label in ('A','B')}
        originals={label:{k.removeprefix('ORIGINAL_'+label+'_'):v for k,v in values.items() if k.startswith('ORIGINAL_'+label+'_')} for label in ('A','B')}
        manifest=bytes.fromhex(rows['A']['canonical_manifest_bytes']);fields=[];cursor=0
        while cursor<len(manifest):
            size=int.from_bytes(manifest[cursor:cursor+4],'big');cursor+=4;fields.append(manifest[cursor:cursor+size].decode());cursor+=size
        header={'binding_id':str(uuid.UUID(int=999)), 'organization_id':fields[3], 'manifest_id':fields[2],
                'manifest_digest':originals['A']['manifest_digest'],'canonical_manifest_bytes':manifest.hex(),
                'mercado_livre_connection_id':fields[4],'omie_connection_id':fields[5],'source_order_reference':fields[6],
                'integration_reference':fields[7],'marketplace_order_id':fields[8],'permission':fields[9],
                'reason':fields[19],'provenance':fields[20],'correlation_id':fields[21]}
        base_values=dict(line.split('=',1) for line in fixture_input().splitlines())
        for field,plan_field in [('principal_id','principalId'),('credential_id','credentialId'),('grant_id','grantId'),('principal_operation_id','principalOperationId'),('credential_operation_id','initialCredentialOperationId'),('grant_operation_id','grantOperationId')]:
            header[field]=base_values['plan.'+plan_field]
        header_types={k:('bytea' if k in ('manifest_digest','canonical_manifest_bytes') else 'uuid' if k.endswith('_id') else 'text') for k in header}
        sql='CREATE SCHEMA offline_crypto;\nCREATE TABLE public.offline_binding_header('+','.join(k+' pg_catalog.'+t for k,t in header_types.items())+',PRIMARY KEY(binding_id));\n'
        # Mock signer/accepted transports preserve frozen column types, not live roles.
        for table in ('s2a_signer_key_revision','s2a_signer_authority_revision','s2a_accepted_attestation'):
            sql+='CREATE TABLE public.'+table+'('+','.join(k+' pg_catalog.'+t for k,t in types[table].items())+');\n'
        for table in ('command_principal','command_credential_revision','command_permission_grant','command_authority_operation'):
            sql+='CREATE TABLE public.'+table+'('+','.join(k+' pg_catalog.'+t for k,t in types[table].items())+');\n'
        from pglast import parse_sql
        from pglast.stream import RawStream
        frozen=(gate.ROOT/next(p.relative_to(gate.ROOT) for p in (gate.ROOT/gate.MIGRATIONS).glob('V042__*.sql'))).read_text(encoding='utf-8-sig')
        pure={'s2a_v042_frame','s2a_v042_text','s2a_v042_instant','s2a_v042_authority_intent','s2a_v042_authority_receipt'}
        for statement in parse_sql(frozen):
            if type(statement.stmt).__name__=='CreateFunctionStmt' and statement.stmt.funcname[-1].sval in pure:
                sql+=RawStream()(statement.stmt)+';\n'
        sql+="CREATE FUNCTION offline_crypto.canonical_spki_ed25519_verify(bytea,bytea,bytea) RETURNS boolean AS '/work/native/flooow_offline_mac32','canonical_spki_ed25519_verify' LANGUAGE C IMMUTABLE STRICT;\n"
        sql+="CREATE FUNCTION public.offline_internal_canonical_spki_ed25519_verify(bytea,bytea,bytea) RETURNS boolean LANGUAGE sql IMMUTABLE STRICT AS 'SELECT offline_crypto.canonical_spki_ed25519_verify($1,$2,$3)';\n"
        expected=commitment_sql().replace('flooow_offline_control_owner','postgres')
        expected='\n'.join(line for line in expected.splitlines() if not line.startswith('GRANT SELECT'))
        sql+=expected+'\n'
        sql+='CREATE FUNCTION public.test_accepted(binding_id uuid) RETURNS boolean LANGUAGE plpgsql AS $predicate$\nDECLARE\n'+declarations()+'''    header_record record;
BEGIN
    SELECT h.* INTO STRICT header_record FROM public.offline_binding_header h;
    SELECT count(*) INTO accepted_count FROM public.s2a_accepted_attestation;
'''+accepted_block().replace('        accepted_ok := false;\n    END;',"        RAISE NOTICE 'TEST_ONLY_ACCEPTED_EXCEPTION % %',SQLSTATE,SQLERRM;\n        accepted_ok := false;\n    END;")+'    RETURN accepted_ok;\nEND;\n$predicate$;\n'
        sql+='BEGIN;\n'+insert('offline_binding_header',header,header_types)
        original=dict(binding_id=header['binding_id'],**originals['A'])
        expected_types={k:('bytea' if k in ('signature_bytes','canonical_expected_attestation','commitment_digest') else 'uuid' if k.endswith('_id') else 'text') for k in (*original,'canonical_expected_attestation','commitment_digest')}
        def expected_insert(original):
            encoded=canonical(original)
            return insert('offline_expected_signed_attestation',dict(original,canonical_expected_attestation=encoded.hex(),commitment_digest=hashlib.sha256(encoded).hexdigest()),expected_types)
        sql+=expected_insert(original)+'COMMIT;\n'
        for label,row in rows.items():
            row.update(organization_id=header['organization_id'],manifest_id=header['manifest_id'])
            verified=row['verified_at']
            key=dict(organization_id=header['organization_id'],signer_key_id=row['signer_key_id'],revision='1',
                     signer_key_fingerprint=row['signer_key_fingerprint'],lineage_fingerprint=row['signer_key_lineage_fingerprint'],
                     subject_public_key_info_der=row['subject_public_key_info_der'],signer_subject_id=str(uuid.UUID(int=300+(label=='B'))),
                     algorithm_id='Ed25519',state='ACTIVE',valid_from=fields[12],effective_at=fields[12])
            authority=dict(organization_id=header['organization_id'],signer_authority_id=row['signer_authority_id'],revision='1',
                signer_authority_fingerprint=row['signer_authority_fingerprint'],signer_subject_id=key['signer_subject_id'],
                signer_key_id=key['signer_key_id'],signer_key_revision='1',signer_key_fingerprint=key['signer_key_fingerprint'],
                approval_source_id=fields[11],signer_role='S2A_FIELD_PROOF_APPROVER',signer_action='unused',
                approval_action='S2A_FIELD_PROOF_APPROVAL',permission='TRANSACTION_IDENTITY_DECISION_WRITE',state='ENABLED',
                valid_from=fields[12],valid_until=fields[13],decided_at=fields[12])
            authority={k:v for k,v in authority.items() if k in types['s2a_signer_authority_revision']}
            sql+=insert('s2a_signer_key_revision',key,types['s2a_signer_key_revision'])+insert('s2a_signer_authority_revision',authority,types['s2a_signer_authority_revision'])
        def assert_result(wanted,label):
            return 'DO $assert$ BEGIN IF public.test_accepted('+quote(header['binding_id'])+') IS DISTINCT FROM '+str(wanted).lower()+" THEN RAISE EXCEPTION 'FAILED "+label+"'; END IF; END; $assert$;\n"
        # Header/expected are immutable: use rollback-only fixture DDL to switch original.
        for expected_label in ('A','B'):
            for stored_label in ('A','B'):
                sql+='BEGIN;\nALTER TABLE public.offline_expected_signed_attestation DISABLE TRIGGER offline_expected_original_input_guard;\nDELETE FROM public.offline_expected_signed_attestation;\n'+expected_insert(dict(binding_id=header['binding_id'],**originals[expected_label]))
                sql+=insert('s2a_accepted_attestation',rows[stored_label],types['s2a_accepted_attestation'])+assert_result(expected_label==stored_label,expected_label+stored_label)+'ROLLBACK;\n'
        # Test all expected-input integrity failures against a valid stored A.
        sql+=insert('s2a_accepted_attestation',rows['A'],types['s2a_accepted_attestation'])
        from build_package_0090_s03_source import schema,encode
        from build_package_0090_q_source import frame,nullable
        snapshot=frame('RECONCILE-ACCEPTED',[nullable(encode('a.'+n,t)) for n,t in schema('s2a_accepted_attestation')])
        sql+='DO $golden$ BEGIN IF (SELECT '+snapshot+" FROM public.s2a_accepted_attestation a)<>decode("+quote(values['S03_ACCEPTED_A_SNAPSHOT'])+",'hex') THEN RAISE EXCEPTION 'S03_ACCEPTED_SNAPSHOT_GOLDEN'; END IF; END; $golden$;\n"
        negatives={'manifest_digest':"repeat('0',64)",'signer_key_id':quote(str(uuid.UUID(int=77))),
                   'signer_key_fingerprint':"repeat('0',64)",'signature_bytes':"decode(repeat('00',64),'hex')",'algorithm_id':quote('RSA'),
                   'canonical_expected_attestation':"decode('00','hex')",'commitment_digest':"decode(repeat('00',32),'hex')"}
        for field,expression in negatives.items():
            sql+=rejection('UPDATE public.offline_expected_signed_attestation SET '+field+'='+expression+';')
        sql+=rejection('DELETE FROM public.offline_expected_signed_attestation;')
        sql+=rejection('TRUNCATE public.offline_expected_signed_attestation CASCADE;')
        sql+=rejection(expected_insert(original))
        sql+=rejection(expected_insert(dict(original,binding_id=str(uuid.UUID(int=444)))))
        sql+=rejection('UPDATE public.offline_binding_header SET manifest_digest=decode(repeat(\'00\',32),\'hex\');')
        for field,value in [('algorithm_id','RSA'),('signature_bytes','00'*63)]:
            sql+='BEGIN;\nALTER TABLE public.offline_expected_signed_attestation DISABLE TRIGGER offline_expected_original_input_guard;\nDELETE FROM public.offline_expected_signed_attestation;\n'
            sql+=rejection(expected_insert(dict(original,**{field:value})))+'ROLLBACK;\n'
        for field,value in [('manifest_digest','0'*64),('signer_key_id',str(uuid.UUID(int=77))),('signer_key_fingerprint','0'*64),('signature_bytes','00'*64)]:
            sql+='BEGIN;\nALTER TABLE public.offline_expected_signed_attestation DISABLE TRIGGER offline_expected_original_input_guard;\nDELETE FROM public.offline_expected_signed_attestation;\n'
            sql+=expected_insert(dict(original,**{field:value}))+assert_result(False,'expected_'+field)+'ROLLBACK;\n'
        sql+="BEGIN;\nALTER TABLE public.offline_expected_signed_attestation DISABLE TRIGGER offline_expected_original_input_guard;\nUPDATE public.offline_expected_signed_attestation SET canonical_expected_attestation=decode('00','hex'),commitment_digest=sha256(decode('00','hex'));\n"+assert_result(False,'expected_canonical')+'ROLLBACK;\n'
        sql+="DO $foreign$ BEGIN IF public.test_accepted('00000000-0000-0000-0000-000000000444') THEN RAISE EXCEPTION 'FOREIGN_BINDING_ACCEPTED'; END IF; END; $foreign$;\n"
        sql+='BEGIN;\n'+insert('s2a_accepted_attestation',rows['A'],types['s2a_accepted_attestation'])+assert_result(False,'duplicate_stored')+'ROLLBACK;\n'
        # Missing expected row and mismatched accepted signature/preimage/fingerprint.
        sql+='BEGIN;\nALTER TABLE public.offline_expected_signed_attestation DISABLE TRIGGER offline_expected_original_input_guard;\nDELETE FROM public.offline_expected_signed_attestation;\n'+assert_result(False,'missing_expected')+'ROLLBACK;\n'
        for field,expression in {'signature_bytes':"decode(repeat('00',64),'hex')",'canonical_signature_preimage_bytes':"decode('00','hex')",'accepted_proof_fingerprint':"repeat('0',64)"}.items():
            sql+='BEGIN;\nUPDATE public.s2a_accepted_attestation SET '+field+'='+expression+';\n'+assert_result(False,'stored_'+field)+'ROLLBACK;\n'
        # Atomicity: a failed expected insert leaves no header after transaction rollback.
        sql+="DO $atomic$ BEGIN BEGIN INSERT INTO public.offline_binding_header(binding_id,manifest_digest) VALUES ('00000000-0000-0000-0000-000000000888',decode(repeat('00',32),'hex')); INSERT INTO public.offline_expected_signed_attestation(binding_id) VALUES ('00000000-0000-0000-0000-000000000888'); EXCEPTION WHEN not_null_violation OR invalid_parameter_value THEN NULL; END; IF EXISTS(SELECT 1 FROM public.offline_binding_header WHERE binding_id='00000000-0000-0000-0000-000000000888') THEN RAISE EXCEPTION 'PARTIAL_REGISTRATION'; END IF; END; $atomic$;\n"
        sql+="DO $orphan$ BEGIN BEGIN INSERT INTO public.offline_binding_header(binding_id,manifest_digest) VALUES ('00000000-0000-0000-0000-000000000889',decode(repeat('00',32),'hex')); SET CONSTRAINTS offline_header_original_input_required IMMEDIATE; RAISE EXCEPTION 'ORPHAN_DID_NOT_REJECT'; EXCEPTION WHEN foreign_key_violation THEN NULL; END; END; $orphan$;\n"
        sql+='SELECT \'S02_ISOLATED_PREDICATE_PASS\';\n'
        from build_package_0090_z_source import build as z_build
        z_query=z_build((gate.ROOT/gate.V043).read_text()).split('    RETURN QUERY',1)[1].split('EXCEPTION WHEN OTHERS',1)[0]
        sql+='CREATE FUNCTION public.test_z() RETURNS TABLE(intent_matches boolean,receipt_matches boolean) LANGUAGE plpgsql AS $z$ DECLARE header_record record; BEGIN SELECT * INTO header_record FROM public.offline_binding_header; RETURN QUERY '+z_query+' END; $z$;\n'
        common=dict(organization_id=header['organization_id'],principal_id=header['principal_id'],reason=header['reason'],provenance=header['provenance'],correlation_id=header['correlation_id'],decided_at=rows['A']['verified_at'])
        sql+='BEGIN;\n'+insert('command_principal',dict(common,mercado_livre_connection_id=header['mercado_livre_connection_id'],omie_connection_id=header['omie_connection_id']),types['command_principal'])
        sql+=insert('command_credential_revision',dict(common,credential_id=header['credential_id'],revision='1',state='ENABLED',secret_verifier='01'*32),types['command_credential_revision'])
        sql+=insert('command_permission_grant',dict(common,grant_id=header['grant_id'],revision='1',state='ENABLED',permission='TRANSACTION_IDENTITY_DECISION_WRITE'),types['command_permission_grant'])
        for operation,operation_id,extra in [('PRINCIPAL',header['principal_operation_id'],{}),('INITIAL_CREDENTIAL',header['credential_operation_id'],dict(credential_id=header['credential_id'],credential_revision='1',state='ENABLED')),('GRANT',header['grant_operation_id'],dict(grant_id=header['grant_id'],grant_revision='1',permission='TRANSACTION_IDENTITY_DECISION_WRITE',state='ENABLED'))]:
            values_for_op={k:v for k,v in common.items() if k not in ('reason','provenance')}
            values_for_op.update(operation=operation,operation_id=operation_id,attestation_manifest_id=header['manifest_id'],**extra)
            sql+=insert('command_authority_operation',values_for_op,types['command_authority_operation'])
            sql+="UPDATE public.command_authority_operation o SET intent_fingerprint=public.s2a_v042_authority_intent(o.operation,o.operation_id,o.organization_id,o.principal_id,"+quote(header['mercado_livre_connection_id'])+','+quote(header['omie_connection_id'])+",o.credential_id,CASE WHEN o.operation='INITIAL_CREDENTIAL' THEN decode(repeat('01',32),'hex') ELSE NULL END,o.grant_id,"+quote(header['reason'])+','+quote(header['provenance'])+",o.correlation_id,o.attestation_manifest_id,"+quote(rows['A']['accepted_proof_fingerprint'])+','+quote(rows['A']['manifest_digest'])+");\n"
            sql+='UPDATE public.command_authority_operation o SET receipt_fingerprint=public.s2a_v042_authority_receipt(o.intent_fingerprint,o.operation,o.principal_id,o.credential_id,o.credential_revision,o.grant_id,o.grant_revision,o.permission,o.state);\n'
            sql+="DO $z_assert$ DECLARE result record; BEGIN SELECT * INTO result FROM public.test_z(); IF result.intent_matches IS NOT TRUE OR result.receipt_matches IS NOT TRUE THEN RAISE EXCEPTION 'Z_PREFIX_FAILED "+operation+"'; END IF; END; $z_assert$;\n"
        sql+="UPDATE public.command_authority_operation SET receipt_fingerprint=repeat('0',64) WHERE operation='GRANT'; DO $z_bad$ DECLARE result record; BEGIN SELECT * INTO result FROM public.test_z(); IF result.receipt_matches THEN RAISE EXCEPTION 'Z_CORRUPTED_RECEIPT_ACCEPTED'; END IF; END; $z_bad$; ROLLBACK;\nSELECT 'Z_PREFIX_1_2_3_PASS';\n"
        (work/'review.sql').write_text(sql,encoding='utf-8',newline='\n')
        shutil.copytree(NATIVE,work/'native')
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
        if 'S02_ISOLATED_PREDICATE_PASS' not in output:raise ValueError('Missing test completion')
        golden=dict(fixture_id='PACKAGE-0090-S02-ORIGINAL-INPUT-AB-001',scope='ISOLATED_TEST_ONLY',
                    provenance='ACTUAL_KOTLIN_ORIGINAL_SIGNED_INPUT_BEFORE_STORED_ROW',manifest_hex=manifest.hex(),
                    canonical_domain=DOMAIN,canonical_tags=list(range(1,7)),originals={})
        for label,original_tuple in originals.items():
            tuple_with_binding=dict(binding_id=header['binding_id'],**original_tuple)
            encoded=canonical(tuple_with_binding)
            golden['originals'][label]=dict(tuple_with_binding,canonical_expected_attestation=encoded.hex(),commitment_digest=hashlib.sha256(encoded).hexdigest())
        golden['s03_accepted_snapshots']={label:values['S03_ACCEPTED_'+label+'_SNAPSHOT'] for label in ('A','B')}
        (gate.ROOT/'docs/evidence/PACKAGE-0090-S02-ORIGINAL-INPUT-GOLDENS.json').write_text(json.dumps(golden,indent=2)+'\n',encoding='utf-8')
        return dict(gate='G3F.3B_S02_ISOLATED_PREDICATE',status='PASS',builder_id=EXPECTED_BUILDER_ID,
            ab_matrix={'expected_A_stored_A':True,'expected_A_stored_B':False,'expected_B_stored_A':False,'expected_B_stored_B':True},
            frozen_witness=dict(line.split('=',1) for line in witness.splitlines()),
            physical_grants=len(gate.expected_column_grants((gate.ROOT/gate.SPEC).read_text())),
            immutable_negatives=list(negatives)+['DELETE','TRUNCATE','DUPLICATE','FOREIGN_BINDING','HEADER_UPDATE'],
            predicate_negatives=['MISSING_EXPECTED','WRONG_MANIFEST','WRONG_KEY','WRONG_KEY_FINGERPRINT','WRONG_SIGNATURE','ALTERED_CANONICAL_WITH_REHASH','FOREIGN_BINDING','DUPLICATE_ACCEPTED','ALTERED_STORED_PREIMAGE','ALTERED_ACCEPTED_PROOF_FINGERPRINT'],
            registration_negatives=['WRONG_ALGORITHM','SIGNATURE_LENGTH_63','FAILED_EXPECTED_ROLLS_BACK_HEADER','ORPHAN_HEADER_DEFERRED_FK'],atomic_rollback=True,
            s03_accepted_snapshot_golden='PASS_ACTUAL_SQL_VS_INDEPENDENT_JAVA',
            z_prefixes='PASS_REAL_SQL_1_2_3_AND_CORRUPTED_GRANT_RECEIPT',
            sql_sha256=hashlib.sha256(sql.encode()).hexdigest(),v043_executed=False,protected_database_connection=False,
            limitations=['Focused accepted predicate, original-input constraints, Z fingerprints and accepted-snapshot encoding; whole wrapper guard/ACL/state/transport runtime certification pending.'])

if __name__=='__main__':
    report=review();target=gate.ROOT/'docs/evidence/PACKAGE-0090-S02-ISOLATED-PREDICATE-REVIEW.json'
    target.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2))
