"""S03 bound reconciliation: S02 alone consumes expected-original private data."""
import re
import package_0090_source_gate as gate
from build_package_0090_read_source import guard,wrapper,TYPES,OWNER
from build_package_0090_q_source import frame,nullable,present,raw,boolean
from build_package_0090_s02_source import framed,text

NAME='offline_reconcile'
MARKER='-- Public S03: bound full typed reconciliation snapshots.'
END='-- End public S03.'
GRANTS={('public',n,('marketplace_transaction_identity_decision',),OWNER) for n in ('transaction_identity_intent','transaction_identity_fingerprint')}

def schema(table):
    spec=(gate.ROOT/gate.SPEC).read_text(encoding='utf-8')
    section=spec.split('### 21.7',1)[1].split('### 21.8',1)[0]
    line=next(l for l in section.splitlines() if l.startswith('- public.'+table+':'))
    return re.findall(r'`(\w+) ([^`]+)`',line)

def encode(value,kind):
    kind=kind.lower()
    if kind=='uuid':return 'pg_catalog.uuid_send('+value+')'
    if kind=='bytea':return value
    if kind in ('integer','int4'):return 'pg_catalog.int4send('+value+')'
    if kind in ('bigint','int8'):return 'pg_catalog.int8send('+value+')'
    if kind.startswith('timestamptz'):return 'pg_catalog.int8send((EXTRACT(EPOCH FROM '+value+')*1000000)::pg_catalog.int8)'
    if kind=='timestamp without time zone':return "pg_catalog.int8send((EXTRACT(EPOCH FROM ("+value+"-TIMESTAMP '1970-01-01 00:00:00'))*1000000)::pg_catalog.int8)"
    if kind in ('text','char(3)','char(64)'):return raw(value+'::pg_catalog.text')
    raise ValueError('Unclosed snapshot type '+kind)

def decode_frame(variable,kind,count,array):
    domain='FLOOOW/OFFLINE-FIELD-PROOF/'+kind+'/V1'
    return f'''    frame_cursor := 0;
    frame_size := 0;
    FOR frame_byte IN 0..3 LOOP
        frame_size := frame_size*256+pg_catalog.get_byte({variable},frame_byte);
    END LOOP;
    IF frame_size<>pg_catalog.octet_length(pg_catalog.convert_to('{domain}','UTF8'))
       OR pg_catalog.substring({variable},5,frame_size::pg_catalog.int4)<>pg_catalog.convert_to('{domain}','UTF8')
       OR pg_catalog.get_byte({variable},frame_size::pg_catalog.int4+4)<>0
       OR pg_catalog.get_byte({variable},frame_size::pg_catalog.int4+5)<>{count} THEN
        RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
    END IF;
    frame_cursor := frame_size::pg_catalog.int4+6;
    {array} := ARRAY[]::pg_catalog.bytea[];
    FOR frame_tag IN 1..{count} LOOP
        IF pg_catalog.get_byte({variable},frame_cursor)<>0 OR pg_catalog.get_byte({variable},frame_cursor+1)<>frame_tag THEN
            RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
        END IF;
        frame_size := 0;
        FOR frame_byte IN 2..5 LOOP
            frame_size := frame_size*256+pg_catalog.get_byte({variable},frame_cursor+frame_byte);
        END LOOP;
        frame_cursor := frame_cursor+6;
        IF frame_size<1 OR frame_size>pg_catalog.octet_length({variable})-frame_cursor
           OR pg_catalog.get_byte({variable},frame_cursor) NOT IN (0,1)
           OR (pg_catalog.get_byte({variable},frame_cursor)=0 AND frame_size<>1) THEN
            RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
        END IF;
        {array} := pg_catalog.array_append({array},pg_catalog.substring({variable},frame_cursor+1,frame_size::pg_catalog.int4));
        frame_cursor := frame_cursor+frame_size::pg_catalog.int4;
    END LOOP;
    IF frame_cursor<>pg_catalog.octet_length({variable}) THEN
        RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
    END IF;
'''

def decision_query():
    columns=schema('marketplace_transaction_identity_decision')
    row='ROW('+','.join('d.'+n for n,t in columns)+')::public.marketplace_transaction_identity_decision'
    return '''    SELECT pg_catalog.count(*) OVER() AS decision_cardinality,'''+','.join('d.'+n for n,t in columns)+''' INTO decision_record
      FROM public.marketplace_transaction_identity_decision d
      WHERE d.organization_id=header_record.organization_id AND d.decision_id=header_record.decision_id;
    IF decision_record.decision_id IS NOT NULL AND (
       decision_record.principal_id<>header_record.principal_id OR decision_record.credential_id<>header_record.credential_id
       OR decision_record.grant_id<>header_record.grant_id OR decision_record.omie_connection_id<>header_record.omie_connection_id
       OR decision_record.ml_connection_id<>header_record.mercado_livre_connection_id
       OR decision_record.source_order_reference<>header_record.source_order_reference
       OR decision_record.marketplace_order_id<>header_record.marketplace_order_id
       OR decision_record.provenance<>header_record.provenance OR decision_record.correlation_id<>header_record.correlation_id) THEN
        RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
    END IF;
    SELECT pg_catalog.count(*)=1 AND pg_catalog.bool_and(
        h.omie_connection_id=d.omie_connection_id AND h.source_order_reference=d.source_order_reference
        AND h.marketplace_order_id=d.marketplace_order_id AND h.kind=d.kind) IS TRUE INTO head_matches
      FROM public.marketplace_transaction_identity_head h
      JOIN public.marketplace_transaction_identity_decision d ON d.organization_id=h.organization_id AND d.decision_id=h.decision_id
      WHERE d.organization_id=header_record.organization_id AND d.decision_id=header_record.decision_id;
    SELECT pg_catalog.count(*)=1 AND pg_catalog.bool_and(
        d.principal_id=header_record.principal_id AND d.credential_id=header_record.credential_id AND d.credential_revision=1
        AND d.grant_id=header_record.grant_id AND d.grant_revision=1 AND d.omie_connection_id=header_record.omie_connection_id
        AND d.ml_connection_id=header_record.mercado_livre_connection_id AND d.source_order_reference=header_record.source_order_reference
        AND d.marketplace_order_id=header_record.marketplace_order_id AND d.kind='CONFIRMED' AND d.reason='EXPLICIT_CONFIRMATION'
        AND d.provenance=header_record.provenance AND d.correlation_id=header_record.correlation_id AND d.supersedes_decision_id IS NULL
        AND d.intent_fingerprint=public.transaction_identity_intent('''+row+''')
        AND d.decision_semantic_fingerprint=public.transaction_identity_fingerprint('''+row+''')
        AND d.authorization_fingerprint=public.transaction_identity_grant_fingerprint(d.organization_id,d.grant_id)) IS TRUE INTO decision_matches
      FROM public.marketplace_transaction_identity_decision d
      WHERE d.organization_id=header_record.organization_id AND d.decision_id=header_record.decision_id;
'''

def evidence_query():
    frozen=(gate.ROOT/'applications/command-authority-ceremony/src/main/kotlin/io/flooow/ceremony/PostgresOfflineFieldProofSupport.kt').read_text(encoding='utf-8')
    sql=frozen.split('SELECT d.*,i.marketplace_key',1)[1].split('"""',1)[0]
    sql='SELECT pg_catalog.count(*) OVER() AS evidence_cardinality,i.marketplace_key'+sql
    for value in ('header_record.organization_id','header_record.decision_id'):sql=sql.replace('?',value,1)
    sql=sql.replace(' AS evidence_revision',' AS evidence_revision INTO evidence_record',1)
    return '    '+sql.strip()+';\n'

def build(source):
    decl,checks=guard(source,('organization_id','manifest_id','manifest_digest','canonical_manifest_bytes','principal_id','credential_id','grant_id','decision_id','mercado_livre_connection_id','omie_connection_id','source_order_reference','marketplace_order_id','provenance','correlation_id'))
    decl+='''    inspect_bytes pg_catalog.bytea;
    inspect_fields pg_catalog.bytea[];
    count_fields pg_catalog.bytea[];
    counts_bytes pg_catalog.bytea;
    count_values pg_catalog.int8[];
    domain_projection pg_catalog.text;
    frame_cursor pg_catalog.int4;
    frame_size pg_catalog.int8;
    frame_byte pg_catalog.int4;
    frame_tag pg_catalog.int4;
    number_value pg_catalog.int8;
    accepted_record record;
    decision_record record;
    evidence_record record;
    fingerprint_record record;
    accepted_snapshot pg_catalog.bytea;
    decision_snapshot pg_catalog.bytea;
    evidence_snapshot pg_catalog.bytea;
    outcome pg_catalog.text;
    diagnostic_code pg_catalog.text;
    head_matches pg_catalog.bool;
    decision_matches pg_catalog.bool;
    evidence_matches pg_catalog.bool;
    manifest_cursor pg_catalog.int4;
    manifest_size pg_catalog.int8;
    manifest_index pg_catalog.int4;
    manifest_fields pg_catalog.text[];
    evidence_bytes pg_catalog.bytea;
'''
    body=checks+'''    -- A owns S02; it remains the ONLY expected-original-input consumer.
    inspect_bytes := public.offline_inspect($1,$2,$3,$4);
'''+decode_frame('inspect_bytes','S02/OUTPUT',11,'inspect_fields')+'''    IF pg_catalog.get_byte(inspect_fields[8],0)<>1 OR pg_catalog.get_byte(inspect_fields[11],0)<>1 THEN
        RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
    END IF;
    domain_projection := pg_catalog.convert_from(pg_catalog.substring(inspect_fields[8],2),'UTF8');
    counts_bytes := pg_catalog.substring(inspect_fields[11],2);
'''+decode_frame('counts_bytes','COUNTS',7,'count_fields')+'''    count_values := ARRAY[]::pg_catalog.int8[];
    FOR frame_tag IN 1..7 LOOP
        IF pg_catalog.octet_length(count_fields[frame_tag])<>9 OR pg_catalog.get_byte(count_fields[frame_tag],0)<>1
           OR pg_catalog.get_byte(count_fields[frame_tag],1)>127 THEN
            RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
        END IF;
        number_value := 0;
        FOR frame_byte IN 1..8 LOOP
            number_value := number_value*256+pg_catalog.get_byte(count_fields[frame_tag],frame_byte);
        END LOOP;
        count_values := pg_catalog.array_append(count_values,number_value);
    END LOOP;
    SELECT z.intent_matches,z.receipt_matches INTO STRICT fingerprint_record FROM public.offline_internal_verify_authority_intent($1,$2,$3,$4) z;
'''
    accepted_columns=schema('s2a_accepted_attestation')
    body+='    SELECT '+','.join('a.'+n for n,t in accepted_columns)+' INTO accepted_record FROM public.s2a_accepted_attestation a WHERE a.organization_id=header_record.organization_id AND a.manifest_id=header_record.manifest_id;\n'
    body+='''    IF count_values[1]=1 AND domain_projection IN ('ACCEPTED_ONLY','PRINCIPAL_ONLY_EXACT','CREDENTIAL_PRESENT','GRANT_PRESENT','DECISION_HEAD_PRESENT') THEN
        accepted_snapshot := '''+frame('RECONCILE-ACCEPTED',[nullable(encode('accepted_record.'+n,t)) for n,t in accepted_columns])+''';
    END IF;
'''+decision_query()+evidence_query()
    body+='''    evidence_matches := false;
    IF evidence_record.evidence_cardinality=1 AND evidence_record.marketplace_key IS NOT NULL AND evidence_record.evidence_revision IS NOT NULL THEN
        manifest_fields := ARRAY[]::pg_catalog.text[]; manifest_cursor := 0;
        FOR manifest_index IN 1..23 LOOP
            manifest_size := 0;
            FOR frame_byte IN 0..3 LOOP
                manifest_size := manifest_size*256+pg_catalog.get_byte(header_record.canonical_manifest_bytes,manifest_cursor+frame_byte);
            END LOOP;
            manifest_cursor := manifest_cursor+4;
            IF manifest_size<1 OR manifest_size>4096 OR manifest_size>pg_catalog.octet_length(header_record.canonical_manifest_bytes)-manifest_cursor THEN
                RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
            END IF;
            manifest_fields := pg_catalog.array_append(manifest_fields,pg_catalog.convert_from(pg_catalog.substring(header_record.canonical_manifest_bytes,manifest_cursor+1,manifest_size::pg_catalog.int4),'UTF8'));
            manifest_cursor := manifest_cursor+manifest_size::pg_catalog.int4;
        END LOOP;
        IF manifest_cursor<>pg_catalog.octet_length(header_record.canonical_manifest_bytes) THEN
            RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
        END IF;
'''
    values=[text("'FLOOOW:S2A:EVIDENCE-BINDING:1'"),text('header_record.organization_id'),text('header_record.marketplace_order_id'),text('header_record.mercado_livre_connection_id'),text('decision_record.ml_capability'),text('decision_record.ml_progress_version'),text('decision_record.ml_record_ordinal'),text('evidence_record.marketplace_key'),text('decision_record.external_order_id'),text('decision_record.currency'),text('evidence_record.outcome'),text('header_record.omie_connection_id'),text('decision_record.omie_capability'),text('decision_record.omie_progress_version'),text('decision_record.omie_record_ordinal'),text('decision_record.source_order_reference')]
    evidence=framed(values)
    for value in ('evidence_record.source_integration_ref','evidence_record.omie_currency'):
        evidence+="||(CASE WHEN "+value+" IS NULL THEN "+framed([text("'NULL'"),"pg_catalog.decode('','hex')"])+" ELSE "+framed([text("'PRESENT'"),text(value)])+' END)'
    evidence+='||'+framed([text('evidence_record.semantic_fingerprint_version'),text('evidence_record.source_evidence_semantic_fingerprint'),text("pg_catalog.to_char(evidence_record.evidence_revision,'YYYY-MM-DD\"T\"HH24:MI:SS.US')")])
    body+='        evidence_bytes := '+evidence+''';
        evidence_matches := evidence_record.evidence_revision IS NOT DISTINCT FROM decision_record.provider_revision_local
            AND decision_record.omie_semantic_fingerprint=evidence_record.source_evidence_semantic_fingerprint
            AND pg_catalog.encode(pg_catalog.sha256(evidence_bytes),'hex')=manifest_fields[23];
    END IF;
    IF decision_record.decision_cardinality=1 AND decision_record.decision_id IS NOT NULL THEN
        decision_snapshot := '''+frame('RECONCILE-DECISION',[nullable(encode('decision_record.'+n,t)) for n,t in schema('marketplace_transaction_identity_decision')])+''';
    END IF;
    IF evidence_record.evidence_cardinality=1 AND evidence_record.marketplace_key IS NOT NULL THEN
        evidence_snapshot := '''+frame('RECONCILE-EVIDENCE',[nullable(encode('evidence_record.'+n,t)) for n,t in [('marketplace_key','text'),('outcome','text'),('source_integration_ref','text'),('omie_currency','text'),('semantic_fingerprint_version','integer'),('source_evidence_semantic_fingerprint','text'),('evidence_revision','timestamp without time zone')]])+''';
    END IF;
    outcome := CASE
        WHEN domain_projection='MISMATCH' OR decision_record.decision_cardinality>1 OR evidence_record.evidence_cardinality>1 THEN 'MISMATCH'
        WHEN accepted_snapshot IS NULL OR decision_snapshot IS NULL OR evidence_snapshot IS NULL THEN 'INDETERMINATE'
        WHEN count_values=ARRAY[1,1,1,1,1,3,1]::pg_catalog.int8[] AND domain_projection='DECISION_HEAD_PRESENT'
          AND fingerprint_record.intent_matches AND fingerprint_record.receipt_matches
          AND head_matches AND decision_matches AND evidence_matches IS TRUE THEN 'EXACT'
        ELSE 'MISMATCH' END;
    diagnostic_code := CASE outcome WHEN 'EXACT' THEN 'STRUCTURAL_EXACT_REQUIRES_ADAPTER_JCA'
        WHEN 'MISMATCH' THEN 'RECONCILIATION_MISMATCH' ELSE 'ESSENTIAL_PROJECTION_MISSING' END;
    IF EXTRACT(EPOCH FROM(pg_catalog.clock_timestamp()-pg_catalog.transaction_timestamp()))*1000000>policy_values[19] THEN
        RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
    END IF;
    RETURN '''+frame('S03/OUTPUT',[present(raw('outcome')),present('counts_bytes'),present(boolean('fingerprint_record.intent_matches')),present(boolean('fingerprint_record.receipt_matches')),nullable('accepted_snapshot'),nullable('decision_snapshot'),nullable('evidence_snapshot'),present(boolean('head_matches')),present(raw('diagnostic_code'))])+''';
'''
    result=MARKER+'\n'+wrapper(NAME,'pg_catalog.bytea',decl,body,'s03')
    for name in ('transaction_identity_intent','transaction_identity_fingerprint'):
        result+='GRANT EXECUTE ON FUNCTION public.'+name+'(public.marketplace_transaction_identity_decision) TO '+OWNER+';\n'
    return result+END+'\n'

if __name__=='__main__':
    path=gate.ROOT/gate.V043;source=path.read_text(encoding='utf-8-sig')
    if MARKER in source:
        start=source.index(MARKER);end=source.index(END,start)+len(END);source=source[:start]+build(source).rstrip()+source[end:]
    else:source+='\n'+build(source)
    path.write_text(source,encoding='utf-8')
