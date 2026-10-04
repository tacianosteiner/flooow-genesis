"""Generate S02's frozen accepted predicate with an independent original input."""
import re
import package_0090_source_gate as gate
from build_package_0090_read_source import guard, wrapper
from build_package_0090_expected_attestation_source import canonical
from build_package_0090_q_source import frame, present, nullable, raw, boolean

NAME='offline_inspect'
MARKER='-- Public S02: independent original signed input, frozen accepted semantics.'
END='-- End public S02.'

def framed(values):
    return '||'.join(f'pg_catalog.int4send(pg_catalog.octet_length({v}))||{v}' for v in values)

def text(value): return f"pg_catalog.convert_to(({value})::pg_catalog.text,'UTF8')"

def accepted_block():
    frozen=(gate.ROOT/'applications/command-authority-ceremony/src/main/kotlin/io/flooow/ceremony/PostgresOfflineFieldProofSupport.kt').read_text(encoding='utf-8')
    query=frozen.split('SELECT a.* FROM public.s2a_accepted_attestation a',1)[1].split('"""',1)[0]
    for value in ('manifest_fields[12]::pg_catalog.uuid','header_record.organization_id','header_record.manifest_id'):
        query=query.replace('?',value,1)
    accepted_columns=sorted(c for o,r,c,p in gate.expected_column_grants((gate.ROOT/gate.SPEC).read_text(encoding='utf-8')) if o==gate.OWNERS['A'] and r=='public.s2a_accepted_attestation' and p=='select')
    query='SELECT '+','.join('a.'+c for c in accepted_columns)+' INTO STRICT accepted_record FROM public.s2a_accepted_attestation a'+query
    preimage=framed([text("'FLOOOW:S2A:APPROVAL-SIGNATURE:1'"),text('expected_record.algorithm_id'),text('expected_record.signer_key_id'),text('expected_record.signer_key_fingerprint'),text('expected_record.manifest_digest')])
    instant="pg_catalog.to_char(accepted_record.verified_at AT TIME ZONE 'UTC','YYYY-MM-DD\"T\"HH24:MI:SS.US\"Z\"')"
    proof=framed([text("'FLOOOW:S2A:ACCEPTED-ATTESTATION-PROOF:1'"),text('accepted_record.artifact_version'),text('accepted_record.canonicalization_version'),'accepted_record.canonical_manifest_bytes',text('accepted_record.manifest_digest'),'accepted_record.canonical_signature_preimage_bytes',text('accepted_record.algorithm_id'),text('accepted_record.signer_key_id'),text('accepted_record.signer_key_revision'),text('accepted_record.signer_key_fingerprint'),text('accepted_record.signer_key_lineage_fingerprint'),'accepted_record.subject_public_key_info_der','accepted_record.signature_bytes',text('accepted_record.signer_authority_id'),text('accepted_record.signer_authority_revision'),text('accepted_record.signer_authority_fingerprint'),text(instant)])
    return '''    -- Frozen accepted(): any predicate/parse/crypto failure becomes false.
    accepted_ok := false;
    BEGIN
        SELECT e.binding_id,e.manifest_digest,e.algorithm_id,e.signer_key_id,
               e.signer_key_fingerprint,e.signature_bytes,e.canonical_expected_attestation,e.commitment_digest
          INTO STRICT expected_record FROM public.offline_expected_signed_attestation e WHERE e.binding_id=$1;
        expected_bytes := '''+canonical('expected_record')+''';
        IF expected_record.algorithm_id<>'Ed25519'
           OR expected_record.signer_key_id='00000000-0000-0000-0000-000000000000'::pg_catalog.uuid
           OR expected_record.manifest_digest !~ '^[0-9a-f]{64}$'
           OR expected_record.signer_key_fingerprint !~ '^[0-9a-f]{64}$'
           OR pg_catalog.octet_length(expected_record.signature_bytes)<>64
           OR expected_record.canonical_expected_attestation IS DISTINCT FROM expected_bytes
           OR expected_record.commitment_digest IS DISTINCT FROM pg_catalog.sha256(expected_bytes)
           OR expected_record.manifest_digest IS DISTINCT FROM pg_catalog.encode(header_record.manifest_digest,'hex')
           OR header_record.manifest_digest IS DISTINCT FROM pg_catalog.sha256(header_record.canonical_manifest_bytes)
           OR accepted_count<>1 THEN
            RAISE EXCEPTION USING ERRCODE='22023',MESSAGE='Rejected expected input';
        END IF;
        -- Decode all 23 length-prefixed manifest texts; no alternate framing.
        manifest_fields := ARRAY[]::pg_catalog.text[];
        manifest_cursor := 0;
        FOR manifest_index IN 1..23 LOOP
            IF manifest_cursor+4>pg_catalog.octet_length(header_record.canonical_manifest_bytes) THEN
                RAISE EXCEPTION USING ERRCODE='22023',MESSAGE='Truncated manifest';
            END IF;
            manifest_size := pg_catalog.get_byte(header_record.canonical_manifest_bytes,manifest_cursor)::pg_catalog.int8*16777216
                +pg_catalog.get_byte(header_record.canonical_manifest_bytes,manifest_cursor+1)::pg_catalog.int8*65536
                +pg_catalog.get_byte(header_record.canonical_manifest_bytes,manifest_cursor+2)::pg_catalog.int8*256
                +pg_catalog.get_byte(header_record.canonical_manifest_bytes,manifest_cursor+3);
            manifest_cursor := manifest_cursor+4;
            IF manifest_size<1 OR manifest_size>4096 OR manifest_cursor+manifest_size>pg_catalog.octet_length(header_record.canonical_manifest_bytes) THEN
                RAISE EXCEPTION USING ERRCODE='22023',MESSAGE='Invalid manifest frame';
            END IF;
            manifest_value := pg_catalog.convert_from(pg_catalog.substring(header_record.canonical_manifest_bytes,manifest_cursor+1,manifest_size::pg_catalog.int4),'UTF8');
            IF manifest_value ~ '[[:cntrl:]]' OR manifest_value ~ '^[[:space:]]|[[:space:]]$'
               OR NOT pg_catalog.is_normalized(manifest_value,'NFC') THEN
                RAISE EXCEPTION USING ERRCODE='22023',MESSAGE='Noncanonical manifest text';
            END IF;
            manifest_fields := pg_catalog.array_append(manifest_fields,manifest_value);
            manifest_cursor := manifest_cursor+manifest_size::pg_catalog.int4;
        END LOOP;
        IF manifest_cursor<>pg_catalog.octet_length(header_record.canonical_manifest_bytes)
           OR manifest_fields[1]<>'FLOOOW:S2A:APPROVAL-MANIFEST:1' OR manifest_fields[2]<>'1'
           OR manifest_fields[3]<>header_record.manifest_id::pg_catalog.text
           OR manifest_fields[4]<>header_record.organization_id::pg_catalog.text
           OR manifest_fields[5]<>header_record.mercado_livre_connection_id::pg_catalog.text
           OR manifest_fields[6]<>header_record.omie_connection_id::pg_catalog.text
           OR manifest_fields[7]<>header_record.source_order_reference
           OR manifest_fields[8]<>header_record.integration_reference
           OR manifest_fields[9]<>header_record.marketplace_order_id::pg_catalog.text
           OR manifest_fields[10]<>header_record.permission
           OR manifest_fields[17]<>'PROTECTED_TTY_ONE_TIME'
           OR manifest_fields[19]<>'SEPARATE_APPROVAL_REQUIRED'
           OR manifest_fields[23] !~ '^[0-9a-f]{64}$'
           OR manifest_fields[20]<>header_record.reason OR manifest_fields[21]<>header_record.provenance
           OR manifest_fields[22]<>header_record.correlation_id::pg_catalog.text THEN
            RAISE EXCEPTION USING ERRCODE='22023',MESSAGE='Manifest binding mismatch';
        END IF;
        FOR manifest_index IN SELECT pg_catalog.unnest(ARRAY[3,4,5,6,9,11,12,15,16,18,22]) LOOP
            IF manifest_fields[manifest_index]<>(manifest_fields[manifest_index]::pg_catalog.uuid)::pg_catalog.text
               OR manifest_fields[manifest_index]='00000000-0000-0000-0000-000000000000' THEN
                RAISE EXCEPTION USING ERRCODE='22023',MESSAGE='Noncanonical manifest UUID';
            END IF;
        END LOOP;
        window_start := manifest_fields[13]::pg_catalog.timestamptz;
        window_end := manifest_fields[14]::pg_catalog.timestamptz;
        IF NOT pg_catalog.isfinite(window_start) OR NOT pg_catalog.isfinite(window_end) OR window_start>=window_end
           OR manifest_fields[13]<>pg_catalog.to_char(window_start AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"')
           OR manifest_fields[14]<>pg_catalog.to_char(window_end AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"') THEN
            RAISE EXCEPTION USING ERRCODE='22023',MESSAGE='Noncanonical manifest window';
        END IF;
        '''+query.strip()+''';
        expected_preimage := '''+preimage+''';
        accepted_ok := accepted_record.artifact_version=1 AND accepted_record.canonicalization_version=1
            AND accepted_record.schema_version=1
            AND pg_catalog.octet_length(accepted_record.canonical_manifest_bytes) BETWEEN 1 AND 4096
            AND accepted_record.canonical_manifest_bytes=header_record.canonical_manifest_bytes
            AND accepted_record.manifest_digest=expected_record.manifest_digest
            AND accepted_record.algorithm_id=expected_record.algorithm_id
            AND accepted_record.signer_key_id=expected_record.signer_key_id
            AND accepted_record.signer_key_fingerprint=expected_record.signer_key_fingerprint
            AND accepted_record.signature_bytes=expected_record.signature_bytes
            AND accepted_record.canonical_signature_preimage_bytes=expected_preimage
            AND pg_catalog.octet_length(expected_preimage)=222
            AND accepted_record.signer_key_revision>0 AND accepted_record.signer_authority_revision>0
            AND accepted_record.signer_key_lineage_fingerprint ~ '^[0-9a-f]{64}$'
            AND accepted_record.signer_authority_fingerprint ~ '^[0-9a-f]{64}$'
            AND accepted_record.verified_at>=window_start AND accepted_record.verified_at<window_end
            AND accepted_record.recorded_at=accepted_record.verified_at
            AND pg_catalog.encode(pg_catalog.sha256(accepted_record.subject_public_key_info_der),'hex')=expected_record.signer_key_fingerprint
            AND accepted_record.accepted_proof_fingerprint=pg_catalog.encode(pg_catalog.sha256('''+proof+'''),'hex')
            AND public.offline_internal_canonical_spki_ed25519_verify(
                accepted_record.subject_public_key_info_der,expected_preimage,accepted_record.signature_bytes);
        accepted_ok := accepted_ok IS TRUE;
    EXCEPTION WHEN OTHERS THEN
        accepted_ok := false;
    END;
'''

def declarations():
    return '''    expected_record record;
    accepted_record record;
    expected_bytes pg_catalog.bytea;
    expected_preimage pg_catalog.bytea;
    accepted_ok pg_catalog.bool;
    accepted_count pg_catalog.int8;
    manifest_fields pg_catalog.text[];
    manifest_cursor pg_catalog.int4;
    manifest_index pg_catalog.int4;
    manifest_size pg_catalog.int8;
    manifest_value pg_catalog.text;
    window_start pg_catalog.timestamptz;
    window_end pg_catalog.timestamptz;
'''

def authority_counts():
    """Transcribe the frozen count predicates, including broad mixed-lineage counts."""
    return '''    SELECT pg_catalog.count(*) INTO accepted_count FROM public.s2a_accepted_attestation a
      WHERE a.organization_id=header_record.organization_id AND a.manifest_id=header_record.manifest_id;
    SELECT pg_catalog.count(*) INTO consumption_count FROM public.s2a_attestation_consumption c
      WHERE c.organization_id=header_record.organization_id AND c.manifest_id=header_record.manifest_id;
    SELECT pg_catalog.count(*) INTO principal_count FROM public.command_principal p
      WHERE p.organization_id=header_record.organization_id AND p.principal_id=header_record.principal_id;
    SELECT pg_catalog.count(*) INTO credential_count FROM public.command_credential_revision c
      WHERE c.organization_id=header_record.organization_id AND (c.credential_id=header_record.credential_id OR c.principal_id=header_record.principal_id);
    SELECT pg_catalog.count(*) INTO grant_count FROM public.command_permission_grant g
      WHERE g.organization_id=header_record.organization_id AND (g.grant_id=header_record.grant_id OR g.principal_id=header_record.principal_id);
    SELECT pg_catalog.count(*) INTO operation_count FROM public.command_authority_operation o
      WHERE o.organization_id=header_record.organization_id AND (o.principal_id=header_record.principal_id
        OR o.attestation_manifest_id=header_record.manifest_id OR o.operation_id IN(header_record.principal_operation_id,header_record.credential_operation_id,header_record.grant_operation_id));
    SELECT pg_catalog.count(*) INTO decision_count FROM public.marketplace_transaction_identity_decision d
      WHERE d.organization_id=header_record.organization_id AND d.decision_id=header_record.decision_id;
    SELECT pg_catalog.count(*) INTO head_count FROM public.marketplace_transaction_identity_head h
      WHERE h.organization_id=header_record.organization_id AND h.decision_id=header_record.decision_id;
    SELECT pg_catalog.count(*) INTO exact_principal_count FROM public.command_principal p
      WHERE p.organization_id=header_record.organization_id AND p.principal_id=header_record.principal_id
        AND p.mercado_livre_connection_id=header_record.mercado_livre_connection_id AND p.omie_connection_id=header_record.omie_connection_id
        AND p.reason=header_record.reason AND p.provenance=header_record.provenance AND p.correlation_id=header_record.correlation_id;
    SELECT pg_catalog.count(*) INTO exact_credential_count FROM public.command_credential_revision c
      WHERE c.organization_id=header_record.organization_id AND c.principal_id=header_record.principal_id
        AND c.credential_id=header_record.credential_id AND c.revision=1 AND c.supersedes_revision IS NULL AND c.state='ENABLED'
        AND c.reason=header_record.reason AND c.provenance=header_record.provenance AND c.correlation_id=header_record.correlation_id;
    SELECT pg_catalog.count(*) INTO exact_grant_count FROM public.command_permission_grant g
      WHERE g.organization_id=header_record.organization_id AND g.principal_id=header_record.principal_id
        AND g.grant_id=header_record.grant_id AND g.revision=1 AND g.supersedes_grant_id IS NULL
        AND g.permission='TRANSACTION_IDENTITY_DECISION_WRITE' AND g.state='ENABLED'
        AND g.reason=header_record.reason AND g.provenance=header_record.provenance AND g.correlation_id=header_record.correlation_id;
    SELECT pg_catalog.count(*) INTO principal_operation_count FROM public.command_authority_operation o
      WHERE o.organization_id=header_record.organization_id AND o.operation_id=header_record.principal_operation_id
        AND o.operation='PRINCIPAL' AND o.principal_id=header_record.principal_id
        AND o.credential_id IS NULL AND o.credential_revision IS NULL AND o.grant_id IS NULL AND o.grant_revision IS NULL
        AND o.permission IS NULL AND o.state IS NULL AND o.correlation_id=header_record.correlation_id AND o.attestation_manifest_id=header_record.manifest_id;
    SELECT pg_catalog.count(*) INTO credential_operation_count FROM public.command_authority_operation o
      WHERE o.organization_id=header_record.organization_id AND o.operation_id=header_record.credential_operation_id
        AND o.operation='INITIAL_CREDENTIAL' AND o.principal_id=header_record.principal_id
        AND o.credential_id=header_record.credential_id AND o.credential_revision=1 AND o.grant_id IS NULL AND o.grant_revision IS NULL
        AND o.permission IS NULL AND o.state='ENABLED' AND o.correlation_id=header_record.correlation_id AND o.attestation_manifest_id=header_record.manifest_id;
    SELECT pg_catalog.count(*) INTO grant_operation_count FROM public.command_authority_operation o
      WHERE o.organization_id=header_record.organization_id AND o.operation_id=header_record.grant_operation_id
        AND o.operation='GRANT' AND o.principal_id=header_record.principal_id
        AND o.credential_id IS NULL AND o.credential_revision IS NULL AND o.grant_id=header_record.grant_id AND o.grant_revision=1
        AND o.permission='TRANSACTION_IDENTITY_DECISION_WRITE' AND o.state='ENABLED'
        AND o.correlation_id=header_record.correlation_id AND o.attestation_manifest_id=header_record.manifest_id;
    exact_operation_count := principal_operation_count+credential_operation_count+grant_operation_count;
    lineage_ok := principal_operation_count BETWEEN 0 AND 1 AND credential_operation_count BETWEEN 0 AND 1 AND grant_operation_count BETWEEN 0 AND 1
      AND principal_count=exact_principal_count AND credential_count=exact_credential_count AND grant_count=exact_grant_count
      AND operation_count=exact_operation_count AND decision_count BETWEEN 0 AND 1 AND head_count BETWEEN 0 AND 1
      AND decision_count=head_count AND (decision_count=0 OR operation_count=3)
      AND CASE exact_operation_count
        WHEN 0 THEN exact_principal_count=0 AND exact_credential_count=0 AND exact_grant_count=0
        WHEN 1 THEN exact_principal_count=1 AND exact_credential_count=0 AND exact_grant_count=0 AND principal_operation_count=1
        WHEN 2 THEN exact_principal_count=1 AND exact_credential_count=1 AND exact_grant_count=0 AND principal_operation_count=1 AND credential_operation_count=1
        WHEN 3 THEN exact_principal_count=1 AND exact_credential_count=1 AND exact_grant_count=1 AND principal_operation_count=1 AND credential_operation_count=1 AND grant_operation_count=1
        ELSE false END;
'''

def consumed_block():
    return '''    SELECT consumption_count=1 AND pg_catalog.count(*)=1 INTO consumption_ok
      FROM public.s2a_attestation_consumption c
      JOIN public.s2a_accepted_attestation a ON a.organization_id=c.organization_id AND a.manifest_id=c.manifest_id
      JOIN public.command_principal p ON p.organization_id=c.organization_id AND p.principal_id=c.principal_id
      JOIN public.command_authority_operation o ON o.organization_id=c.organization_id AND o.attestation_manifest_id=c.manifest_id AND o.principal_id=c.principal_id
      WHERE c.organization_id=header_record.organization_id AND c.manifest_id=header_record.manifest_id
        AND c.manifest_digest=pg_catalog.encode(header_record.manifest_digest,'hex') AND c.manifest_digest=a.manifest_digest
        AND c.principal_id=header_record.principal_id AND c.correlation_id=header_record.correlation_id
        AND o.operation_id=header_record.principal_operation_id AND o.operation='PRINCIPAL'
        AND o.correlation_id=c.correlation_id AND p.correlation_id=c.correlation_id
        AND c.consumed_at=o.decided_at AND p.decided_at=o.decided_at;
'''

def control_block():
    spec=(gate.ROOT/gate.SPEC).read_text(encoding='utf-8')
    grants=gate.expected_column_grants(spec)
    def select(relation,alias,record,where,strict=False):
        columns=sorted(c for o,r,c,p in grants if o==gate.OWNERS['A'] and r=='public.'+relation and p=='select')
        return '    SELECT '+','.join(alias+'.'+c for c in columns)+' INTO '+('STRICT ' if strict else '')+record+' FROM public.'+relation+' '+alias+' WHERE '+where+';\n'
    result=select('offline_binding_lifecycle','l','lifecycle_record','l.binding_id=$1',True)
    result+=select('offline_attempt_pointer','p','pointer_record','p.binding_id=$1',True)
    result+=select('offline_attempt','t','attempt_record','t.binding_id=$1 AND t.attempt_id=pointer_record.current_attempt_id')
    result+=select('offline_execution','x','execution_record','x.binding_id=$1 AND x.attempt_id=pointer_record.current_attempt_id AND x.generation=pointer_record.generation')
    for relation,alias,record in [('offline_delivery','d','delivery_record'),('offline_reconciliation','r','reconciliation_record'),('offline_ceremony_result','c','ceremony_record')]:
        result+=select(relation,alias,record,alias+'.binding_id=$1',True)
    result+='''    IF (pointer_record.current_attempt_id IS NOT NULL AND (attempt_record.attempt_id IS NULL OR attempt_record.generation<>pointer_record.generation))
       OR (execution_record.execution_id IS NOT NULL AND (execution_record.attempt_id<>attempt_record.attempt_id
           OR execution_record.generation<>pointer_record.generation OR execution_record.executor_oid<>slot_oids[3])) THEN
        RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
    END IF;
    SELECT pg_catalog.count(*) INTO admission_count FROM public.offline_admission a
      WHERE a.binding_id=$1 AND a.attempt_id=pointer_record.current_attempt_id AND a.generation=pointer_record.generation;
    IF admission_count>1 THEN
        RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
    END IF;
'''
    result+=select('offline_admission','a','admission_record','a.binding_id=$1 AND a.attempt_id=pointer_record.current_attempt_id AND a.generation=pointer_record.generation')
    result+='''    IF admission_count=1 AND (admission_record.deployment_id<>header_record.deployment_id
        OR admission_record.incarnation_id<>header_record.deployment_incarnation_id
        OR admission_record.organization_id<>header_record.organization_id OR admission_record.principal_id<>header_record.principal_id
        OR admission_record.credential_id<>header_record.credential_id OR admission_record.grant_id<>header_record.grant_id
        OR admission_record.permission<>header_record.permission OR admission_record.executor_oid<>slot_oids[3]
        OR admission_record.execution_id IS DISTINCT FROM execution_record.execution_id
        OR admission_record.instance_id IS DISTINCT FROM execution_record.instance_id) THEN
        RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
    END IF;
    admission_valid := admission_count=1 AND admission_record.durable_state='ISSUED'
      AND admission_record.consumed_decision_id IS NULL AND admission_record.consumed_at IS NULL
      AND admission_record.credential_revision=1 AND admission_record.grant_revision=1
      AND lifecycle_record.state='ACTIVE' AND attempt_record.state='EFFECTS_IN_PROGRESS' AND execution_record.state='OWNED'
      AND database_now>=header_record.valid_from AND database_now<header_record.expires_at
      AND database_now>=attempt_record.claimed_at AND database_now<attempt_record.expires_at
      AND database_now>=execution_record.claimed_at AND database_now<execution_record.expires_at
      AND database_now>=window_start AND database_now<window_end
      AND database_now>=admission_record.authenticated_at AND database_now<admission_record.expires_at
      AND admission_record.authenticated_at>=header_record.valid_from AND admission_record.authenticated_at>=attempt_record.claimed_at
      AND admission_record.authenticated_at>=execution_record.claimed_at AND admission_record.authenticated_at>=window_start
      AND admission_record.expires_at<=header_record.expires_at AND admission_record.expires_at<=attempt_record.expires_at
      AND admission_record.expires_at<=execution_record.expires_at AND admission_record.expires_at<=window_end
      AND accepted_ok AND consumption_ok AND lineage_ok AND principal_count=1 AND credential_count=1 AND grant_count=1 AND operation_count=3
      AND decision_count=0 AND head_count=0
      AND admission_record.authorization_fingerprint=pg_catalog.decode(public.transaction_identity_grant_fingerprint(header_record.organization_id,header_record.grant_id),'hex');
    admission_valid := admission_valid IS TRUE;
'''
    return result

def build(source):
    extra=('organization_id','manifest_id','manifest_digest','canonical_manifest_bytes','principal_id','credential_id','grant_id',
           'decision_id','principal_operation_id','credential_operation_id','grant_operation_id','mercado_livre_connection_id',
           'omie_connection_id','marketplace_order_id','source_order_reference','integration_reference','permission','reason','provenance','correlation_id','valid_from','expires_at')
    decl,checks=guard(source,extra)
    decl+=declarations()
    for name in ('consumption','principal','credential','grant','operation','decision','head','exact_principal','exact_credential','exact_grant','principal_operation','credential_operation','grant_operation','exact_operation','admission'):
        decl+=f'    {name}_count pg_catalog.int8;\n'
    for name in ('lifecycle','pointer','attempt','execution','delivery','reconciliation','ceremony','admission','fingerprint'):
        decl+=f'    {name}_record record;\n'
    decl+='''    lineage_ok pg_catalog.bool;
    consumption_ok pg_catalog.bool;
    admission_valid pg_catalog.bool;
    domain_projection pg_catalog.text;
    counts_bytes pg_catalog.bytea;
    output_bytes pg_catalog.bytea;
'''
    body=checks+authority_counts()+accepted_block()+consumed_block()+'''    IF operation_count=0 THEN
        lineage_ok := lineage_ok AND consumption_count=0;
    ELSE
        SELECT z.intent_matches,z.receipt_matches INTO STRICT fingerprint_record
          FROM public.offline_internal_verify_authority_intent($1,$2,$3,$4) z;
        lineage_ok := lineage_ok AND accepted_ok AND consumption_ok
          AND fingerprint_record.intent_matches AND fingerprint_record.receipt_matches;
    END IF;
    domain_projection := CASE
      WHEN lineage_ok IS NOT TRUE OR accepted_count>1 OR consumption_count>1 OR (accepted_count=1 AND NOT accepted_ok) THEN 'MISMATCH'
      WHEN operation_count=0 AND accepted_count=0 THEN 'EMPTY'
      WHEN operation_count=0 AND accepted_ok THEN 'ACCEPTED_ONLY'
      WHEN operation_count=1 THEN 'PRINCIPAL_ONLY_EXACT'
      WHEN operation_count=2 THEN 'CREDENTIAL_PRESENT'
      WHEN operation_count=3 AND decision_count=0 THEN 'GRANT_PRESENT'
      WHEN operation_count=3 AND decision_count=1 AND head_count=1 THEN 'DECISION_HEAD_PRESENT'
      ELSE 'UNKNOWN' END;
'''+control_block()
    counts=frame('COUNTS',[present('pg_catalog.int8send('+n+'_count)') for n in ('accepted','consumption','principal','credential','grant','operation')]+[present('pg_catalog.int8send(LEAST(decision_count,head_count))')])
    output=frame('S02/OUTPUT',[present(raw('lifecycle_record.state')),nullable(raw('attempt_record.state')),present('pg_catalog.int8send(pointer_record.generation)'),nullable(raw('execution_record.state')),present(raw('delivery_record.state')),present(raw('reconciliation_record.state')),present(raw('ceremony_record.result')),present(raw('domain_projection')),nullable(raw('admission_record.durable_state')),present(boolean('admission_valid')),present('counts_bytes')])
    body+='    counts_bytes := '+counts+';\n    output_bytes := '+output+''';
    IF EXTRACT(EPOCH FROM(pg_catalog.clock_timestamp()-pg_catalog.transaction_timestamp()))*1000000>policy_values[19] THEN
        RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
    END IF;
    RETURN output_bytes;
'''
    return MARKER+'\n'+wrapper(NAME,'pg_catalog.bytea',decl,body,'s02')+END+'\n'

def install():
    path=gate.ROOT/gate.V043
    source=path.read_text(encoding='utf-8-sig')
    if MARKER in source:
        start=source.index(MARKER);end=source.index(END,start)+len(END)
        source=source[:start]+build(source).rstrip()+source[end:]
    else: source+='\n'+build(source)
    for signature in ('transaction_identity_grant_fingerprint(pg_catalog.uuid,pg_catalog.uuid)','transaction_identity_hash(pg_catalog.text[])'):
        grant='GRANT EXECUTE ON FUNCTION public.'+signature+' TO flooow_offline_audit_owner;'
        if grant not in source:source+='\n'+grant+'\n'
    path.write_text(source,encoding='utf-8')

if __name__=='__main__':install()
