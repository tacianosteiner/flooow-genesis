CREATE FUNCTION public.offline_read_history(
    binding_id pg_catalog.uuid,
    plan_fingerprint pg_catalog.bytea,
    expected_incarnation_id pg_catalog.uuid,
    surface_version pg_catalog.text) RETURNS TABLE(installed_rank pg_catalog.int4,version pg_catalog.text,type pg_catalog.text,script pg_catalog.text,checksum pg_catalog.int4,success pg_catalog.bool)
LANGUAGE plpgsql STABLE SECURITY DEFINER CALLED ON NULL INPUT
SET search_path=pg_catalog,pg_temp
AS $offline_s04$


DECLARE
    header_record record;
    ready_record record;
    policy_record record;
    caller_record record;
    slot_cursor pg_catalog.int4;
    slot_length pg_catalog.int8;
    slot_oid pg_catalog.int8;
    slot_name_length pg_catalog.int8;
    slot_name pg_catalog.text;
    slot_oids pg_catalog.int8[] := ARRAY[]::pg_catalog.int8[];
    slot_names pg_catalog.text[] := ARRAY[]::pg_catalog.text[];
    slot_number pg_catalog.int4;
    field_tag pg_catalog.int4;
    byte_number pg_catalog.int4;
    cursor_position pg_catalog.int4;
    payload_length pg_catalog.int8;
    domain_length pg_catalog.int8;
    field_value pg_catalog.numeric;
    policy_values pg_catalog.int8[] := ARRAY[]::pg_catalog.int8[];
    database_now pg_catalog.timestamptz;
BEGIN
    IF $1 IS NULL OR $2 IS NULL OR $3 IS NULL OR $4 IS NULL
       OR $1='00000000-0000-0000-0000-000000000000'::pg_catalog.uuid
       OR $3='00000000-0000-0000-0000-000000000000'::pg_catalog.uuid
       OR pg_catalog.octet_length($2)<>32 OR $4<>'0090-v1'
       OR pg_catalog.current_setting('transaction_isolation')<>'repeatable read'
       OR pg_catalog.current_setting('transaction_read_only')<>'on' THEN
        RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
    END IF;
    SELECT h.binding_id,h.deployment_id,h.deployment_incarnation_id,h.identity_slots,
           h.offline_surface_version,h.deadline_policy_version,h.deadline_policy_digest,
           h.plan_fingerprint
      INTO header_record FROM public.offline_binding_header h
     WHERE h.binding_id=$1 AND h.plan_fingerprint=$2
       AND h.deployment_incarnation_id=$3 AND h.offline_surface_version=$4;
    IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED'; END IF;
    -- Decode exact canonical slots; use session_user, never current_user or a caller OID.
    IF pg_catalog.octet_length(header_record.identity_slots) < 4
       OR pg_catalog.substring(header_record.identity_slots,1,4) <> '\x00000004'::pg_catalog.bytea THEN
        RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
    END IF;
    slot_cursor := 4;
    FOR slot_number IN 1..4 LOOP
        slot_length := 0;
        FOR byte_number IN 0..3 LOOP
            slot_length := slot_length*256 + pg_catalog.get_byte(header_record.identity_slots,slot_cursor+byte_number);
        END LOOP;
        slot_cursor := slot_cursor+4;
        IF slot_length < 10 OR slot_length > pg_catalog.octet_length(header_record.identity_slots)-slot_cursor
           OR pg_catalog.get_byte(header_record.identity_slots,slot_cursor) <> slot_number THEN
            RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
        END IF;
        slot_oid := 0; slot_name_length := 0;
        FOR byte_number IN 0..3 LOOP
            slot_oid := slot_oid*256+pg_catalog.get_byte(header_record.identity_slots,slot_cursor+1+byte_number);
            slot_name_length := slot_name_length*256+pg_catalog.get_byte(header_record.identity_slots,slot_cursor+5+byte_number);
        END LOOP;
        IF slot_oid=0 OR slot_name_length <> slot_length-9 OR slot_oid=ANY(slot_oids) THEN
            RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
        END IF;
        slot_name := pg_catalog.convert_from(pg_catalog.substring(header_record.identity_slots,
                      slot_cursor+10,slot_name_length::pg_catalog.int4),'UTF8');
        IF slot_name IS NOT NFC NORMALIZED OR slot_name=ANY(slot_names) THEN
            RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
        END IF;
        SELECT r.oid,r.rolname,r.rolcanlogin,r.rolinherit,r.rolsuper,r.rolcreaterole,
               r.rolcreatedb,r.rolreplication,r.rolbypassrls
          INTO caller_record FROM pg_catalog.pg_roles r WHERE r.oid::pg_catalog.int8=slot_oid AND r.rolname=slot_name;
        IF NOT FOUND OR NOT caller_record.rolcanlogin OR caller_record.rolinherit
           OR caller_record.rolsuper OR caller_record.rolcreaterole OR caller_record.rolcreatedb
           OR caller_record.rolreplication OR caller_record.rolbypassrls
           OR EXISTS(SELECT 1 FROM pg_catalog.pg_auth_members m
                      WHERE m.member=caller_record.oid OR m.roleid=caller_record.oid) THEN
            RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
        END IF;
        IF slot_number=4 AND slot_name <> SESSION_USER THEN
            RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
        END IF;
        slot_oids := pg_catalog.array_append(slot_oids,slot_oid);
        slot_names := pg_catalog.array_append(slot_names,slot_name);
        slot_cursor := slot_cursor+slot_length::pg_catalog.int4;
    END LOOP;
    IF slot_cursor <> pg_catalog.octet_length(header_record.identity_slots) THEN
        RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
    END IF;
    SELECT p.policy_version,p.policy_digest,p.canonical_policy,p.effective_from INTO policy_record
      FROM public.offline_deadline_policy p
     WHERE p.policy_version=header_record.deadline_policy_version AND p.policy_digest=header_record.deadline_policy_digest;
    IF NOT FOUND OR pg_catalog.sha256(policy_record.canonical_policy) <> policy_record.policy_digest THEN
        RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
    END IF;
    -- Full29-field parser, with checked signed-int8 conversion; no TTL/GUC/default source.
    domain_length := 0;
    FOR byte_number IN 0..3 LOOP
        domain_length := domain_length*256+pg_catalog.get_byte(policy_record.canonical_policy,byte_number);
    END LOOP;
    IF domain_length <> pg_catalog.octet_length(pg_catalog.convert_to('FLOOOW/OFFLINE-FIELD-PROOF/DEADLINE-POLICY/V1','UTF8'))
       OR pg_catalog.substring(policy_record.canonical_policy,5,domain_length::pg_catalog.int4)
           <> pg_catalog.convert_to('FLOOOW/OFFLINE-FIELD-PROOF/DEADLINE-POLICY/V1','UTF8') THEN
        RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
    END IF;
    cursor_position := domain_length::pg_catalog.int4+4;
    IF pg_catalog.get_byte(policy_record.canonical_policy,cursor_position) <> 0
       OR pg_catalog.get_byte(policy_record.canonical_policy,cursor_position+1) <> 29 THEN
        RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
    END IF;
    cursor_position := cursor_position+2;
    FOR field_tag IN 1..29 LOOP
        IF pg_catalog.get_byte(policy_record.canonical_policy,cursor_position) <> 0
           OR pg_catalog.get_byte(policy_record.canonical_policy,cursor_position+1) <> field_tag THEN
            RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
        END IF;
        payload_length := 0;
        FOR byte_number IN 0..3 LOOP
            payload_length := payload_length*256+pg_catalog.get_byte(policy_record.canonical_policy,cursor_position+2+byte_number);
        END LOOP;
        IF payload_length <= 1 OR payload_length > pg_catalog.octet_length(policy_record.canonical_policy)-cursor_position-6
           OR pg_catalog.get_byte(policy_record.canonical_policy,cursor_position+6) <> 1 THEN
            RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
        END IF;
        IF field_tag=1 THEN
            IF pg_catalog.substring(policy_record.canonical_policy,cursor_position+8,(payload_length-1)::pg_catalog.int4)
               <> pg_catalog.convert_to(policy_record.policy_version,'UTF8')
               OR policy_record.policy_version='' OR policy_record.policy_version IS NOT NFC NORMALIZED THEN
                RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
            END IF;
        ELSE
            IF payload_length <> 9 THEN RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED'; END IF;
            field_value := 0;
            FOR byte_number IN 0..7 LOOP
                field_value := field_value*256+pg_catalog.get_byte(policy_record.canonical_policy,cursor_position+7+byte_number);
            END LOOP;
            IF field_value <= 0 OR field_value > 9223372036854775807 THEN
                RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
            END IF;
            policy_values := pg_catalog.array_append(policy_values,field_value::pg_catalog.int8);
        END IF;
        cursor_position := cursor_position+6+payload_length::pg_catalog.int4;
    END LOOP;
    IF cursor_position <> pg_catalog.octet_length(policy_record.canonical_policy) THEN
        RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
    END IF;
    FOR field_tag IN 1..14 LOOP
        IF policy_values[field_tag*2-1] > policy_values[field_tag*2] THEN
            RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
        END IF;
    END LOOP;
    IF policy_values[3] > policy_values[2] OR policy_values[5] > policy_values[2]
       OR policy_values[7] > policy_values[2] OR policy_values[9] > policy_values[13]
       OR policy_values[11] > policy_values[13]
       OR policy_values[15] > LEAST(policy_values[9],policy_values[11],policy_values[13])
       OR policy_values[17] > LEAST(policy_values[11],policy_values[13])
       OR policy_values[25] >= policy_values[17] THEN
        RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
    END IF;
    SELECT r.deployment_id,r.incarnation_id,r.state,r.policy_version,r.policy_digest,
           r.watchdog_checked_at,r.watchdog_healthy INTO ready_record
      FROM public.offline_readiness r WHERE r.deployment_id=header_record.deployment_id AND r.incarnation_id=$3;
    IF NOT FOUND OR ready_record.state <> 'READY' OR ready_record.policy_version <> policy_record.policy_version
       OR ready_record.policy_digest <> policy_record.policy_digest OR NOT ready_record.watchdog_healthy THEN
        RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
    END IF;
    database_now := pg_catalog.clock_timestamp();
    IF NOT pg_catalog.isfinite(database_now)
       OR NOT pg_catalog.isfinite(policy_record.effective_from) OR database_now<policy_record.effective_from
       OR NOT pg_catalog.isfinite(ready_record.watchdog_checked_at) OR database_now<ready_record.watchdog_checked_at
       OR EXTRACT(EPOCH FROM(database_now-ready_record.watchdog_checked_at))*1000000>policy_values[23]
       OR EXTRACT(EPOCH FROM(database_now-pg_catalog.transaction_timestamp()))*1000000>policy_values[19] THEN
        RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
    END IF;
    RETURN QUERY SELECT h.installed_rank,h.version,h.type,h.script,h.checksum,h.success
      FROM public.flyway_schema_history h ORDER BY h.installed_rank;
    IF EXTRACT(EPOCH FROM(pg_catalog.clock_timestamp()-pg_catalog.transaction_timestamp()))*1000000>policy_values[19] THEN
        RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
    END IF;
    RETURN;

EXCEPTION WHEN OTHERS THEN
    RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
END;
$offline_s04$;
