"""Offline generator for the exact Q capability; never connects to PostgreSQL.

SQL framing is expanded inline, without adding a codec/helper capability.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V043__create_governed_offline_field_proof_capability_composition.sql'
SPEC = ROOT / 'docs/specifications/SPEC-0090-governed-offline-field-proof-exclusive-capability-composition.md'
PREFIX = 'FLOOOW/OFFLINE-FIELD-PROOF/'


def literal(value):
    return "'" + value.replace("'", "''") + "'"


def raw(value):
    return "pg_catalog.convert_to(" + value + ",'UTF8')"


def blob(hex_value):
    return "'\\x" + hex_value + "'::pg_catalog.bytea"


def u4(value):
    return 'pg_catalog.substring(pg_catalog.int8send((' + value + ')::pg_catalog.int8),5,4)'


def u1(value):
    return 'pg_catalog.substring(pg_catalog.int4send((' + value + ')::pg_catalog.int4),4,1)'


def boolean(value):
    return '(' + "CASE WHEN (" + value + ") THEN " + blob('01') + ' ELSE ' + blob('00') + ' END)'


def present(value):
    return '(' + blob('01') + '||(' + value + '))'


def nullable(value):
    return '(CASE WHEN (' + value + ') IS NULL THEN ' + blob('00') + ' ELSE ' + present(value) + ' END)'


def role(value):
    return '(CASE WHEN (' + value + ')=0 THEN ' + blob('00') + ' ELSE ' + blob('01') + '||' + u4('pg_catalog.octet_length(' + raw('role_names[pg_catalog.array_position(role_oids,(' + value + ')::pg_catalog.oid)]') + ')') + '||' + raw('role_names[pg_catalog.array_position(role_oids,(' + value + ')::pg_catalog.oid)]') + ' END)'


def collection(query, ordered=False):
    order = 'ordinal' if ordered else 'element'
    return '(SELECT ' + u4('pg_catalog.count(*)') + "||COALESCE(pg_catalog.string_agg(" + u4('pg_catalog.octet_length(element)') + '||element,' + blob('') + ' ORDER BY ' + order + '),' + blob('') + ') FROM (' + query + ') encoded_elements)'


def frame(kind, fields):
    domain = raw(literal(PREFIX + kind + '/V1'))
    encoded = []
    for tag, field in enumerate(fields, 1):
        encoded.append(blob(tag.to_bytes(2, 'big').hex()) + '||' + u4('pg_catalog.octet_length(' + field + ')') + '||' + field)
    return '(' + u4('pg_catalog.octet_length(' + domain + ')') + '||' + domain + '||' + blob(len(fields).to_bytes(2, 'big').hex()) + '||' + '||'.join(encoded) + ')'


def row(kind, fields):
    return frame(kind, [nullable(f) for f in fields])


def deny(condition):
    return '    IF ' + condition + " THEN\n        RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';\n    END IF;\n"


def text_list(expression):
    return collection('SELECT ' + raw('v') + ' AS element,ordinal FROM pg_catalog.unnest(' + expression + ') WITH ORDINALITY x(v,ordinal)', True)


def privilege_rows(kind, object_oid, owner, acl, privileges, column=None):
    # Named effective checks include PUBLIC, inherited paths and superuser rights.
    # PUBLIC is evaluated by ACL expansion, never treated as an actual role OID.
    check = {'FUNCTION': 'function', 'RELATION': 'table', 'SCHEMA': 'schema', 'DATABASE': 'database'}[kind]
    if column:
        check = 'column'
    object_args = 'g.oid,' + object_oid + (',' + column if column else '')
    args = object_args + ',p.name'
    direct = "EXISTS(SELECT 1 FROM pg_catalog.aclexplode(" + acl + ") a WHERE a.grantee=g.oid AND a.privilege_type=p.name)"
    public = "EXISTS(SELECT 1 FROM pg_catalog.aclexplode(" + acl + ") a WHERE a.grantee=0 AND a.privilege_type=p.name)"
    effective = '(CASE WHEN g.oid=0 THEN ' + public + ' ELSE pg_catalog.has_' + check + '_privilege(' + args + ') END)'
    grantable = '(g.oid=' + owner + ' OR CASE WHEN g.oid=0 THEN EXISTS(SELECT 1 FROM pg_catalog.aclexplode(' + acl + ") a WHERE a.grantee=0 AND a.privilege_type=p.name AND a.is_grantable) ELSE pg_catalog.has_" + check + '_privilege(' + object_args + ",p.name||' WITH GRANT OPTION') END)"
    return direct, effective, grantable, '(g.oid=' + owner + ')'


def build(source, spec):
    p = source.split('AS $offline_p$', 1)[1].split('$offline_p$;', 1)[0]
    declarations = p.split('BEGIN', 1)[0]
    for name in ('attempt_record', 'execution_record', 'pointer_record'):
        declarations = declarations.replace('    ' + name + ' record;\n', '')
    declarations = declarations.replace('    principal_found pg_catalog.uuid;\n', '')
    guard = '    SELECT h.binding_id' + p.split('    SELECT h.binding_id', 1)[1].split('    -- C:', 1)[0]
    start, end = guard.index('    SELECT h.binding_id'), guard.index('      INTO header_record')
    guard = guard[:start] + '''    SELECT h.binding_id,h.deployment_id,h.deployment_incarnation_id,h.identity_slots,
           h.offline_surface_version,h.deadline_policy_version,h.deadline_policy_digest,
           h.plan_fingerprint,h.valid_from,h.expires_at
''' + guard[end:]
    guard = guard.replace('''        IF slot_number=3 AND slot_name <> SESSION_USER THEN
            RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
        END IF;
''', '')
    # Route is derived only after every bound slot OID/name/attribute is validated.
    at = guard.index('    SELECT p.policy_version')
    guard = guard[:at] + '''    IF SESSION_USER=slot_names[4] THEN
        auditor_route := true;
        IF pg_catalog.octet_length($8)<>0
           OR pg_catalog.current_setting('transaction_isolation')<>'repeatable read'
           OR pg_catalog.current_setting('transaction_read_only')<>'on' THEN
            RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
        END IF;
    ELSIF SESSION_USER=slot_names[3] THEN
        auditor_route := false;
        IF pg_catalog.octet_length($8)=0
           OR pg_catalog.current_setting('transaction_isolation')<>'read committed'
           OR pg_catalog.current_setting('transaction_read_only')<>'off' THEN
            RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
        END IF;
    ELSE
        RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
    END IF;
''' + guard[at:]
    guard = guard.replace('r.watchdog_checked_at,r.watchdog_healthy INTO ready_record',
        'r.watchdog_checked_at,r.watchdog_healthy,r.active_key_version,r.history_manifest,r.acl_manifest INTO ready_record')
    extra = '''    auditor_route pg_catalog.bool;
    key_record record;
    history_record record;
    live_history pg_catalog.bytea;
    history_elements pg_catalog.bytea := '\\x'::pg_catalog.bytea;
    history_count pg_catalog.int8 := 0;
    last_rank pg_catalog.int4 := 0;
    receipt_frame pg_catalog.bytea;
    receipt_mac pg_catalog.bytea;
    receipt_fields pg_catalog.bytea[] := ARRAY[]::pg_catalog.bytea[];
    issued_us pg_catalog.numeric;
    expires_us pg_catalog.numeric;
    now_us pg_catalog.numeric;
    decoded_value pg_catalog.numeric;
    mac_version pg_catalog.int8;
    payload pg_catalog.bytea;
    role_oids pg_catalog.oid[];
    role_names pg_catalog.text[];
    protected_oids pg_catalog.oid[];
    type_oids pg_catalog.oid[];
    type_names pg_catalog.text[];
    acl_collections pg_catalog.bytea[] := ARRAY[]::pg_catalog.bytea[];
    live_acl pg_catalog.bytea;
    catalog_record record;
    function_oids pg_catalog.oid[];
    relation_oids pg_catalog.oid[];
    creator_oids pg_catalog.oid[];
    universe_oids pg_catalog.oid[];
    all_types pg_catalog.oid[];
    all_modes pg_catalog.text[];
    all_names pg_catalog.text[];
    input_names pg_catalog.text[];
    argument_names pg_catalog.text[];
    argument_modes pg_catalog.bytea[];
    output_elements pg_catalog.bytea[];
    function_elements pg_catalog.bytea[] := ARRAY[]::pg_catalog.bytea[];
    input_index pg_catalog.int4;
    return_shape pg_catalog.int4;
    config_names pg_catalog.text[];
    config_entry pg_catalog.text;
    config_name pg_catalog.text;
    canonical_type pg_catalog.text;
'''
    initial = '''BEGIN
    IF $1 IS NULL OR $2 IS NULL OR $3 IS NULL OR $4 IS NULL OR $5 IS NULL
       OR $6 IS NULL OR $7 IS NULL OR $8 IS NULL
       OR $1='00000000-0000-0000-0000-000000000000'::pg_catalog.uuid
       OR $3='00000000-0000-0000-0000-000000000000000'::pg_catalog.uuid
       OR pg_catalog.octet_length($2)<>32 OR pg_catalog.octet_length($5)<>32
       OR pg_catalog.octet_length($6)<>32 OR pg_catalog.octet_length($7)<>32 OR $4<>'0090-v1' THEN
        RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
    END IF;
'''.replace('00000000-0000-0000-0000-000000000000000', '00000000-0000-0000-0000-000000000000')
    policy_and_time = deny('policy_record.policy_digest<>$7') + '''    database_now := pg_catalog.clock_timestamp();
    IF NOT pg_catalog.isfinite(database_now) OR NOT pg_catalog.isfinite(policy_record.effective_from)
       OR database_now<policy_record.effective_from
       OR NOT pg_catalog.isfinite(ready_record.watchdog_checked_at)
       OR database_now<ready_record.watchdog_checked_at
       OR EXTRACT(EPOCH FROM(database_now-ready_record.watchdog_checked_at))*1000000>policy_values[23]
       OR EXTRACT(EPOCH FROM(database_now-pg_catalog.transaction_timestamp()))*1000000>
          (CASE WHEN auditor_route THEN policy_values[19] ELSE policy_values[1] END) THEN
        RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
    END IF;
    IF NOT auditor_route AND (
       NOT EXISTS(SELECT 1 FROM public.offline_binding_lifecycle l WHERE l.binding_id=$1 AND l.state='ACTIVE')
       OR NOT EXISTS(SELECT 1 FROM public.offline_attempt_pointer a WHERE a.binding_id=$1 AND a.claim_permitted)
       OR NOT EXISTS(SELECT 1 FROM public.offline_ceremony_result c WHERE c.binding_id=$1 AND c.result='NONE')
       OR NOT pg_catalog.isfinite(header_record.valid_from) OR NOT pg_catalog.isfinite(header_record.expires_at)
       OR database_now<header_record.valid_from OR database_now>=header_record.expires_at) THEN
        RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
    END IF;
    SELECT k.incarnation_id,k.lineage_id,k.key_version,k.key_state,k.key_material INTO STRICT key_record
      FROM public.offline_preflight_key k WHERE k.incarnation_id=$3 AND k.key_state='ACTIVE';
    IF key_record.key_version<>ready_record.active_key_version
       OR key_record.key_version<=0 OR key_record.key_version>4294967295
       OR key_record.lineage_id='00000000-0000-0000-0000-000000000000'::pg_catalog.uuid
       OR key_record.key_material IS NULL OR pg_catalog.octet_length(key_record.key_material)<>32 THEN
        RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
    END IF;
'''
    parse_receipt = '''    IF NOT auditor_route THEN
        -- Exact frame boundary; nine required fields followed by exactly32 MAC bytes.
        domain_length := 0;
        FOR byte_number IN 0..3 LOOP
            domain_length := domain_length*256+pg_catalog.get_byte($8,byte_number);
        END LOOP;
        IF domain_length<>pg_catalog.octet_length(pg_catalog.convert_to('FLOOOW/OFFLINE-FIELD-PROOF/PREFLIGHT/V1','UTF8'))
           OR pg_catalog.substring($8,5,domain_length::pg_catalog.int4)<>
              pg_catalog.convert_to('FLOOOW/OFFLINE-FIELD-PROOF/PREFLIGHT/V1','UTF8') THEN
            RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
        END IF;
        cursor_position := domain_length::pg_catalog.int4+4;
        IF pg_catalog.get_byte($8,cursor_position)<>0 OR pg_catalog.get_byte($8,cursor_position+1)<>9 THEN
            RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
        END IF;
        cursor_position := cursor_position+2;
        FOR field_tag IN 1..9 LOOP
            IF pg_catalog.get_byte($8,cursor_position)<>0
               OR pg_catalog.get_byte($8,cursor_position+1)<>field_tag THEN
                RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
            END IF;
            payload_length := 0;
            FOR byte_number IN 0..3 LOOP
                payload_length := payload_length*256+pg_catalog.get_byte($8,cursor_position+2+byte_number);
            END LOOP;
            IF payload_length<=1 OR payload_length>pg_catalog.octet_length($8)-cursor_position-6-32
               OR pg_catalog.get_byte($8,cursor_position+6)<>1 THEN
                RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
            END IF;
            payload := pg_catalog.substring($8,cursor_position+8,(payload_length-1)::pg_catalog.int4);
            IF pg_catalog.octet_length(payload)<>(CASE field_tag WHEN 1 THEN 16 WHEN 2 THEN 32
               WHEN 3 THEN pg_catalog.octet_length(pg_catalog.convert_to($4,'UTF8'))
               WHEN 4 THEN 32 WHEN 5 THEN 32 WHEN 6 THEN 32 WHEN 7 THEN 8 WHEN 8 THEN 8 WHEN 9 THEN 4 END) THEN
                RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
            END IF;
            receipt_fields := pg_catalog.array_append(receipt_fields,payload);
            cursor_position := cursor_position+6+payload_length::pg_catalog.int4;
        END LOOP;
        IF cursor_position<>pg_catalog.octet_length($8)-32 THEN
            RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
        END IF;
        mac_version := 0;
        FOR byte_number IN 0..3 LOOP
            mac_version := mac_version*256+pg_catalog.get_byte(receipt_fields[9],byte_number);
        END LOOP;
        IF mac_version<>key_record.key_version THEN
            RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
        END IF;
        receipt_frame := pg_catalog.substring($8,1,cursor_position);
        receipt_mac := offline_crypto.hmac(receipt_frame::pg_catalog.bytea,key_record.key_material::pg_catalog.bytea,'sha256'::pg_catalog.text);
        IF pg_catalog.octet_length(receipt_mac)<>32 OR offline_crypto.timing_safe_equal32(
            receipt_mac::pg_catalog.bytea,pg_catalog.substring($8,cursor_position+1,32)::pg_catalog.bytea) IS NOT TRUE THEN
            RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
        END IF;
        IF receipt_fields[1]<>pg_catalog.uuid_send($3) OR receipt_fields[2]<>$2
           OR receipt_fields[3]<>pg_catalog.convert_to($4,'UTF8') OR receipt_fields[4]<>$5
           OR receipt_fields[5]<>$6 OR receipt_fields[6]<>$7 THEN
            RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
        END IF;
        FOR field_tag IN 7..8 LOOP
            decoded_value := 0;
            FOR byte_number IN 0..7 LOOP
                decoded_value := decoded_value*256+pg_catalog.get_byte(receipt_fields[field_tag],byte_number);
            END LOOP;
            IF decoded_value>=9223372036854775808 THEN decoded_value := decoded_value-18446744073709551616; END IF;
            IF field_tag=7 THEN issued_us := decoded_value; ELSE expires_us := decoded_value; END IF;
        END LOOP;
        now_us := EXTRACT(EPOCH FROM pg_catalog.clock_timestamp())*1000000;
        IF issued_us+policy_values[27]<>expires_us OR expires_us<=issued_us
           OR issued_us<-210866803200000000 OR expires_us>9223372036854775807
           OR issued_us>now_us OR now_us>=expires_us THEN
            RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
        END IF;
    END IF;
'''
    history_fields = ['pg_catalog.int4send(history_record.installed_rank)',
        raw('history_record.version'), raw('history_record.type'), raw('history_record.script'),
        'pg_catalog.int4send(history_record.checksum)', boolean('history_record.success')]
    history = '''    -- Full history, without a version cap or adoption of unexpected rows.
    FOR history_record IN SELECT h.installed_rank,h.version,h.type,h.script,h.checksum,h.success
        FROM public.flyway_schema_history h ORDER BY h.installed_rank LOOP
        IF history_record.installed_rank<=last_rank OR history_record.version IS NULL
           OR history_record.checksum IS NULL OR NOT history_record.success
           OR history_record.version IS NOT NFC NORMALIZED OR history_record.type IS NOT NFC NORMALIZED
           OR history_record.script IS NOT NFC NORMALIZED THEN
            RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
        END IF;
        payload := ''' + row('HISTORY-ROW', history_fields) + ''';
        history_elements := history_elements||''' + u4('pg_catalog.octet_length(payload)') + '''||payload;
        history_count := history_count+1; last_rank := history_record.installed_rank;
    END LOOP;
    live_history := ''' + row('HISTORY', [u4('history_count') + '||history_elements']) + ''';
''' + deny('history_count=0 OR live_history<>ready_record.history_manifest OR pg_catalog.sha256(live_history)<>$5')
    # Remaining catalog code is generated separately, preserving a single Q body.
    catalog = build_catalog(spec)
    issuance_fields = ['pg_catalog.uuid_send($3)', '$2', raw('$4'), '$5', '$6', '$7',
        'pg_catalog.int8send(issued_us::pg_catalog.int8)', 'pg_catalog.int8send(expires_us::pg_catalog.int8)', u4('key_record.key_version')]
    finish = '''    -- Validate fresh time again after live catalog/history work.
    now_us := EXTRACT(EPOCH FROM pg_catalog.clock_timestamp())*1000000;
    IF NOT auditor_route THEN
        IF issued_us>now_us OR now_us>=expires_us THEN
            RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
        END IF;
        RETURN $8;
    END IF;
    issued_us := now_us;
    expires_us := issued_us+policy_values[27];
    IF issued_us<>pg_catalog.trunc(issued_us) OR issued_us<-9223372036854775808
       OR expires_us>9223372036854775807 OR expires_us<=issued_us
       OR issued_us<-210866803200000000 OR expires_us>=9224318016000000000 THEN
        RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
    END IF;
    receipt_frame := ''' + row('PREFLIGHT', issuance_fields) + ''';
    receipt_mac := offline_crypto.hmac(receipt_frame::pg_catalog.bytea,key_record.key_material::pg_catalog.bytea,'sha256'::pg_catalog.text);
    IF receipt_mac IS NULL OR pg_catalog.octet_length(receipt_mac)<>32 THEN
        RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
    END IF;
    RETURN receipt_frame||receipt_mac;
EXCEPTION WHEN OTHERS THEN
    -- Never forward parser, key, foreign object, cast, constraint or crypto diagnostics.
    RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
END;
'''
    signature = ','.join('pg_catalog.' + t for t in ('uuid','bytea','uuid','text','bytea','bytea','bytea','bytea'))
    return '''-- Internal Q: bound readiness/receipt issuance and validation only; no writes/locks.
CREATE FUNCTION public.offline_internal_readiness(
    binding_id pg_catalog.uuid,plan_fingerprint pg_catalog.bytea,
    expected_incarnation_id pg_catalog.uuid,surface_version pg_catalog.text,
    expected_history_digest pg_catalog.bytea,expected_acl_digest pg_catalog.bytea,
    expected_policy_digest pg_catalog.bytea,preflight_receipt pg_catalog.bytea
) RETURNS pg_catalog.bytea
LANGUAGE plpgsql STABLE SECURITY DEFINER CALLED ON NULL INPUT
SET search_path=pg_catalog,pg_temp
AS $offline_q$
''' + declarations + extra + initial + guard + policy_and_time + parse_receipt + history + catalog + finish + '''$offline_q$;
ALTER FUNCTION public.offline_internal_readiness(''' + signature + ''') OWNER TO flooow_offline_readiness_owner;
REVOKE ALL PRIVILEGES ON FUNCTION public.offline_internal_readiness(''' + signature + ''') FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.offline_internal_readiness(''' + signature + ''') TO flooow_offline_audit_owner;
GRANT EXECUTE ON FUNCTION public.offline_internal_readiness(''' + signature + ''') TO flooow_offline_execution_owner;
GRANT USAGE ON SCHEMA public TO flooow_offline_readiness_owner;
GRANT USAGE ON SCHEMA public TO flooow_offline_audit_owner;
GRANT USAGE ON SCHEMA public TO flooow_offline_execution_owner;
'''


def build_catalog(spec):
    owners = ['flooow_offline_' + s + '_owner' for s in (
        'verification','issuance','execution','audit','principal_lock','readiness','intent_audit','control')]
    identities = 'slot_names||ARRAY[' + ','.join(literal(n) for n in owners) + ']::pg_catalog.text[]'
    public_functions = set(re.findall(r'public\.(offline_[a-z_]+)\(', spec))
    dependencies = set(re.findall(r'`public\.([a-z_][a-z0-9_]*)\(',
        spec.split('Exact existing dependency signatures',1)[1].split('### 21.8',1)[0]))
    function_names = sorted(public_functions | dependencies)
    columns = set()
    allowed_privileges = set()
    privilege_mapping = {'READ_PRIVILEGE':'SELECT','LOCK_ENABLING_UPDATE_PRIVILEGE':'UPDATE',
                         'BOOKKEEPING_INSERT':'INSERT','BOOKKEEPING_UPDATE':'UPDATE'}
    role_mapping = dict(zip(('V','I','E','A','P','Q','Z'), owners))
    for line in spec.splitlines():
        cells = [c.strip() for c in line.split('|')]
        if len(cells)>5 and cells[1] in ('V','I','E','A','P','Q','Z') and cells[2].startswith('public.'):
            columns.add((cells[2].split('.',1)[1],cells[3]))
            if cells[4] in privilege_mapping:
                allowed_privileges.add((role_mapping[cells[1]],cells[2].split('.',1)[1],cells[3],privilege_mapping[cells[4]]))
    relations = sorted({r for r,c in columns})
    column_values = ',\n'.join('(' + literal(r) + ',' + literal(c) + ')' for r,c in sorted(columns))
    privilege_values = ',\n'.join('('+','.join(literal(v) for v in item)+')' for item in sorted(allowed_privileges))
    code = '''    -- Live roles, not caller/GUC role selectors. Every protected identity is exact.
    SELECT pg_catalog.array_agg(r.oid ORDER BY r.oid),pg_catalog.array_agg(r.rolname::pg_catalog.text ORDER BY r.oid)
      INTO role_oids,role_names FROM pg_catalog.pg_roles r;
    SELECT pg_catalog.array_agg(r.oid ORDER BY x.purpose) INTO protected_oids
      FROM pg_catalog.unnest(''' + identities + ''') WITH ORDINALITY x(name,purpose)
      JOIN pg_catalog.pg_roles r ON r.rolname=x.name;
    IF pg_catalog.cardinality(protected_oids)<>12 OR
       EXISTS(SELECT 1 FROM pg_catalog.pg_auth_members m WHERE m.member=ANY(protected_oids) OR m.roleid=ANY(protected_oids))
       OR EXISTS(SELECT 1 FROM pg_catalog.pg_roles r WHERE r.oid=ANY(protected_oids) AND (
          r.rolsuper OR r.rolcreaterole OR r.rolcreatedb OR r.rolreplication OR r.rolbypassrls
          OR r.rolcanlogin IS DISTINCT FROM (pg_catalog.array_position(protected_oids,r.oid)<=4)
          OR r.rolinherit IS DISTINCT FROM (pg_catalog.array_position(protected_oids,r.oid)=12))) THEN
        RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
    END IF;
    -- Fixed named inventories; reachable application extras are included, never hidden.
    SELECT pg_catalog.array_agg(p.oid ORDER BY p.oid) INTO function_oids
      FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid=p.pronamespace
     WHERE (n.nspname='public' AND p.proname=ANY(ARRAY[''' + ','.join(literal(n) for n in function_names) + ''']::pg_catalog.text[]))
        OR (n.nspname='offline_crypto' AND p.proname IN ('hmac','timing_safe_equal32','canonical_spki_ed25519_verify'))
        OR (n.nspname!~'^pg_' AND n.nspname<>'information_schema' AND
            EXISTS(SELECT 1 FROM pg_catalog.unnest(protected_oids[1:11]) q(oid)
                   WHERE pg_catalog.has_function_privilege(q.oid,p.oid,'EXECUTE')));
    SELECT pg_catalog.array_agg(c.oid ORDER BY c.oid) INTO relation_oids
      FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
     WHERE n.nspname='public' AND c.relname=ANY(ARRAY[''' + ','.join(literal(n) for n in relations) + ''']::pg_catalog.text[]);
    IF pg_catalog.cardinality(relation_oids)<>''' + str(len(relations)) + ''' THEN
        RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
    END IF;
    SELECT pg_catalog.array_agg(DISTINCT x.oid ORDER BY x.oid) INTO creator_oids FROM (
        SELECT p.proowner AS oid FROM pg_catalog.pg_proc p WHERE p.oid=ANY(function_oids)
        UNION SELECT c.relowner FROM pg_catalog.pg_class c WHERE c.oid=ANY(relation_oids)
        UNION SELECT r.oid FROM pg_catalog.pg_roles r WHERE r.rolname='postgres'
        UNION SELECT q.oid FROM pg_catalog.unnest(protected_oids[5:12]) q(oid)) x;
    WITH RECURSIVE seed(oid) AS (
        SELECT q.oid FROM pg_catalog.unnest(protected_oids||creator_oids) q(oid)
        UNION SELECT a.grantee FROM pg_catalog.pg_proc p CROSS JOIN LATERAL
            pg_catalog.aclexplode(COALESCE(p.proacl,pg_catalog.acldefault('f',p.proowner))) a WHERE p.oid=ANY(function_oids)
        UNION SELECT c.relowner FROM pg_catalog.pg_class c WHERE c.oid=ANY(relation_oids)
        UNION SELECT a.grantee FROM pg_catalog.pg_class c CROSS JOIN LATERAL
            pg_catalog.aclexplode(COALESCE(c.relacl,pg_catalog.acldefault('r',c.relowner))) a WHERE c.oid=ANY(relation_oids)
        UNION SELECT a.grantee FROM pg_catalog.pg_attribute t CROSS JOIN LATERAL pg_catalog.aclexplode(t.attacl) a
            WHERE t.attrelid=ANY(relation_oids) AND t.attnum>0 AND NOT t.attisdropped
        UNION SELECT n.nspowner FROM pg_catalog.pg_namespace n WHERE n.nspname!~'^pg_' AND n.nspname<>'information_schema'
        UNION SELECT a.grantee FROM pg_catalog.pg_namespace n CROSS JOIN LATERAL
            pg_catalog.aclexplode(COALESCE(n.nspacl,pg_catalog.acldefault('n',n.nspowner))) a
            WHERE n.nspname!~'^pg_' AND n.nspname<>'information_schema'
        UNION SELECT d.datdba FROM pg_catalog.pg_database d WHERE d.datname=pg_catalog.current_database()
        UNION SELECT a.grantee FROM pg_catalog.pg_database d CROSS JOIN LATERAL
            pg_catalog.aclexplode(COALESCE(d.datacl,pg_catalog.acldefault('d',d.datdba))) a
            WHERE d.datname=pg_catalog.current_database()
        UNION SELECT a.grantee FROM pg_catalog.pg_default_acl d CROSS JOIN LATERAL pg_catalog.aclexplode(d.defaclacl) a
            WHERE d.defaclrole=ANY(creator_oids)
        UNION SELECT 0::pg_catalog.oid), reachable(oid) AS (
        SELECT s.oid FROM seed s UNION SELECT m.roleid FROM pg_catalog.pg_auth_members m JOIN reachable r ON m.member=r.oid)
    SELECT pg_catalog.array_agg(r.oid ORDER BY r.oid) INTO universe_oids FROM reachable r;
    IF EXISTS(SELECT 1 FROM pg_catalog.unnest(universe_oids) u(oid)
               WHERE u.oid<>0 AND NOT u.oid=ANY(role_oids)) THEN
        RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
    END IF;
    IF EXISTS(SELECT 1 FROM pg_catalog.pg_roles r WHERE r.oid=ANY(universe_oids) AND r.rolname IS NOT NFC NORMALIZED)
       OR EXISTS(SELECT 1 FROM pg_catalog.pg_namespace n WHERE n.nspname!~'^pg_' AND n.nspname<>'information_schema'
          AND n.nspname IS NOT NFC NORMALIZED)
       OR EXISTS(SELECT 1 FROM pg_catalog.pg_class c WHERE c.oid=ANY(relation_oids) AND c.relname IS NOT NFC NORMALIZED)
       OR EXISTS(SELECT 1 FROM pg_catalog.pg_attribute a WHERE a.attrelid=ANY(relation_oids)
          AND a.attnum>0 AND NOT a.attisdropped AND a.attname IS NOT NFC NORMALIZED)
       OR EXISTS(SELECT 1 FROM pg_catalog.pg_database d WHERE d.datname=pg_catalog.current_database()
          AND d.datname IS NOT NFC NORMALIZED) THEN
        RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
    END IF;
    -- Independently reject broad and unlisted effective relation/column/sequence access.
    IF EXISTS(SELECT 1 FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
        CROSS JOIN pg_catalog.unnest(protected_oids[1:11]) g(oid)
        WHERE n.nspname!~'^pg_' AND n.nspname<>'information_schema' AND (
          c.relowner=g.oid OR (c.relkind='S' AND pg_catalog.has_sequence_privilege(g.oid,c.oid,'USAGE,SELECT,UPDATE'))
          OR (c.relkind IN ('r','v','m','f','p') AND pg_catalog.has_table_privilege(g.oid,c.oid,
             'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER,MAINTAIN'))))
       OR EXISTS(SELECT 1 FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
        JOIN pg_catalog.pg_attribute a ON a.attrelid=c.oid AND a.attnum>0 AND NOT a.attisdropped
        CROSS JOIN pg_catalog.unnest(protected_oids[1:11]) g(oid)
        CROSS JOIN (VALUES ('SELECT'),('INSERT'),('UPDATE'),('REFERENCES')) privilege(name)
        WHERE n.nspname!~'^pg_' AND n.nspname<>'information_schema' AND c.relkind IN ('r','v','m','f','p')
          AND pg_catalog.has_column_privilege(g.oid,c.oid,a.attnum,privilege.name)
          AND NOT EXISTS(SELECT 1 FROM (VALUES ''' + privilege_values + ''') approved(role_name,relation,column_name,privilege)
            WHERE approved.role_name=role_names[pg_catalog.array_position(role_oids,g.oid)]
              AND n.nspname='public' AND approved.relation=c.relname AND approved.column_name=a.attname
              AND approved.privilege=privilege.name)) THEN
        RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
    END IF;
    IF EXISTS(SELECT 1 FROM pg_catalog.pg_default_acl d WHERE d.defaclrole=ANY(creator_oids)
        AND (d.defaclobjtype NOT IN ('r','S','f','T','n','L') OR EXISTS(
          SELECT 1 FROM pg_catalog.aclexplode(d.defaclacl) a WHERE a.privilege_type NOT IN
          ('EXECUTE','USAGE','CREATE','SELECT','INSERT','UPDATE','DELETE','TRUNCATE','REFERENCES','TRIGGER','MAINTAIN')))) THEN
        RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
    END IF;
    -- Global no-entry means hard-wired defaults, not an empty safe ACL.
    IF EXISTS(SELECT 1 FROM pg_catalog.unnest(creator_oids) creator(oid)
        CROSS JOIN (VALUES ('r'),('S'),('f'),('T'),('n'),('L')) kind(type)
        CROSS JOIN LATERAL pg_catalog.aclexplode(COALESCE(
          (SELECT d.defaclacl FROM pg_catalog.pg_default_acl d WHERE d.defaclrole=creator.oid
            AND d.defaclnamespace=0 AND d.defaclobjtype=kind.type::pg_catalog."char"),
          pg_catalog.acldefault(CASE WHEN kind.type='S' THEN 's'::pg_catalog."char" ELSE kind.type::pg_catalog."char" END,creator.oid))) a
        WHERE a.grantee<>creator.oid)
       OR EXISTS(SELECT 1 FROM pg_catalog.pg_default_acl d CROSS JOIN LATERAL pg_catalog.aclexplode(d.defaclacl) a
          WHERE d.defaclrole=ANY(creator_oids) AND a.grantee<>d.defaclrole) THEN
        RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
    END IF;
    -- Canonical qualified type names, reciprocal arrays; no regtype/display aliases.
    SELECT pg_catalog.array_agg(t.oid ORDER BY t.oid),pg_catalog.array_agg(
        CASE WHEN e.typarray=t.oid THEN
           CASE WHEN en.nspname~'^[a-z_][a-z0-9_]*$' THEN en.nspname ELSE '"'||pg_catalog.replace(en.nspname,'"','""')||'"' END||'.'||
           CASE WHEN e.typname~'^[a-z_][a-z0-9_]*$' THEN e.typname ELSE '"'||pg_catalog.replace(e.typname,'"','""')||'"' END||'[]'
        ELSE CASE WHEN n.nspname~'^[a-z_][a-z0-9_]*$' THEN n.nspname ELSE '"'||pg_catalog.replace(n.nspname,'"','""')||'"' END||'.'||
           CASE WHEN t.typname~'^[a-z_][a-z0-9_]*$' THEN t.typname ELSE '"'||pg_catalog.replace(t.typname,'"','""')||'"' END END ORDER BY t.oid)
      INTO type_oids,type_names FROM pg_catalog.pg_type t JOIN pg_catalog.pg_namespace n ON n.oid=t.typnamespace
      LEFT JOIN pg_catalog.pg_type e ON e.oid=t.typelem LEFT JOIN pg_catalog.pg_namespace en ON en.oid=e.typnamespace
     WHERE t.typname IS NFC NORMALIZED AND n.nspname IS NFC NORMALIZED
       AND (e.typarray IS DISTINCT FROM t.oid OR (e.typname IS NFC NORMALIZED AND en.nspname IS NFC NORMALIZED AND e.typelem=0));
'''
    identity = row('ACL-IDENTITY', [u4('x.purpose'), u4('r.oid'), role('r.oid'),
        *[boolean('r.'+n) for n in ('rolcanlogin','rolinherit','rolsuper','rolcreaterole','rolcreatedb','rolreplication','rolbypassrls')]])
    code += '    acl_collections := pg_catalog.array_append(acl_collections,' + collection('SELECT ' + identity +
        ' AS element FROM pg_catalog.unnest(protected_oids) WITH ORDINALITY x(oid,purpose) JOIN pg_catalog.pg_roles r ON r.oid=x.oid') + ');\n'
    # Function projection validates catalog cardinalities before encoding.
    code += '''    FOR catalog_record IN SELECT p.oid,p.proname,n.nspname,p.proowner,p.prokind,p.prosecdef,
        p.proisstrict,p.proretset,p.provolatile,p.pronargs,p.pronargdefaults,p.prorettype,
        p.proargtypes,p.proallargtypes,p.proargmodes,p.proargnames,p.provariadic,p.proconfig,p.proacl,t.typtype
        FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid=p.pronamespace
        JOIN pg_catalog.pg_type t ON t.oid=p.prorettype WHERE p.oid=ANY(function_oids) LOOP
        IF catalog_record.prokind<>'f' OR catalog_record.proname IS NOT NFC NORMALIZED
           OR catalog_record.nspname IS NOT NFC NORMALIZED OR catalog_record.pronargdefaults<0
           OR catalog_record.pronargdefaults>catalog_record.pronargs THEN
            RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
        END IF;
        all_types := ARRAY[]::pg_catalog.oid[]; all_modes := ARRAY[]::pg_catalog.text[];
        input_names := ARRAY[]::pg_catalog.text[];
        IF catalog_record.pronargs>0 THEN
            FOR input_index IN 0..catalog_record.pronargs-1 LOOP
                canonical_type := type_names[pg_catalog.array_position(type_oids,catalog_record.proargtypes[input_index])];
                IF canonical_type IS NULL THEN RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED'; END IF;
                input_names := pg_catalog.array_append(input_names,canonical_type);
                all_types := pg_catalog.array_append(all_types,catalog_record.proargtypes[input_index]);
                all_modes := pg_catalog.array_append(all_modes,'i');
            END LOOP;
        END IF;
        IF catalog_record.proallargtypes IS NULL THEN
            IF catalog_record.proargmodes IS NOT NULL THEN RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED'; END IF;
        ELSE
            all_types := catalog_record.proallargtypes; all_modes := catalog_record.proargmodes::pg_catalog.text[];
            IF all_modes IS NULL OR pg_catalog.cardinality(all_types)<>pg_catalog.cardinality(all_modes) THEN
                RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
            END IF;
        END IF;
        all_names := catalog_record.proargnames::pg_catalog.text[];
        IF all_names IS NOT NULL AND pg_catalog.cardinality(all_names)<>pg_catalog.cardinality(all_types) THEN
            RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
        END IF;
        argument_names := ARRAY[]::pg_catalog.text[]; argument_modes := ARRAY[]::pg_catalog.bytea[];
        output_elements := ARRAY[]::pg_catalog.bytea[]; input_index := 1;
        IF pg_catalog.cardinality(all_types)>0 THEN
            FOR field_tag IN 1..pg_catalog.cardinality(all_types) LOOP
                canonical_type := type_names[pg_catalog.array_position(type_oids,all_types[field_tag])];
                IF canonical_type IS NULL OR all_modes[field_tag] NOT IN ('i','o','b','v','t')
                   OR (all_names[field_tag] IS NOT NULL AND all_names[field_tag] IS NOT NFC NORMALIZED) THEN
                    RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
                END IF;
                argument_names := pg_catalog.array_append(argument_names,canonical_type);
                argument_modes := pg_catalog.array_append(argument_modes,'''+u1("CASE all_modes[field_tag] WHEN 'i' THEN 1 WHEN 'o' THEN 2 WHEN 'b' THEN 3 WHEN 'v' THEN 4 WHEN 't' THEN 5 END")+''');
                IF all_modes[field_tag] IN ('i','b','v') THEN
                    IF input_names[input_index] IS DISTINCT FROM canonical_type THEN
                        RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
                    END IF;
                    IF all_modes[field_tag]='v' AND (input_index<>catalog_record.pronargs OR catalog_record.provariadic=0) THEN
                        RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
                    END IF;
                    input_index := input_index+1;
                END IF;
                IF all_modes[field_tag] IN ('o','b','t') THEN
                    output_elements := pg_catalog.array_append(output_elements,'''+row('ACL-OUTPUT',[
                        raw("NULLIF(all_names[field_tag],'')"),'pg_catalog.convert_to(canonical_type,\'UTF8\')','argument_modes[field_tag]'])+''');
                END IF;
            END LOOP;
        END IF;
        IF input_index<>catalog_record.pronargs+1 OR
           (catalog_record.provariadic=0 AND 'v'=ANY(all_modes)) OR
           (catalog_record.provariadic<>0 AND NOT 'v'=ANY(all_modes)) THEN
            RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
        END IF;
        canonical_type := type_names[pg_catalog.array_position(type_oids,catalog_record.prorettype)];
        IF canonical_type IS NULL THEN RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED'; END IF;
        return_shape := CASE WHEN 't'=ANY(all_modes) THEN 2 WHEN canonical_type='pg_catalog.void' THEN 3
          WHEN catalog_record.typtype='c' THEN CASE WHEN catalog_record.proretset THEN 5 ELSE 6 END
          WHEN canonical_type='pg_catalog.record' THEN CASE WHEN catalog_record.proretset THEN 2 ELSE 7 END
          ELSE CASE WHEN catalog_record.proretset THEN 4 ELSE 1 END END;
        IF ('t'=ANY(all_modes) AND NOT catalog_record.proretset)
           OR (return_shape=3 AND catalog_record.proretset)
           OR (canonical_type='pg_catalog.record' AND pg_catalog.cardinality(output_elements)=0) THEN
            RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
        END IF;
        config_names := ARRAY[]::pg_catalog.text[];
        IF catalog_record.proconfig IS NOT NULL THEN
            FOREACH config_entry IN ARRAY catalog_record.proconfig LOOP
                config_name := pg_catalog.split_part(config_entry,'=',1);
                IF config_entry IS NULL OR config_entry IS NOT NFC NORMALIZED
                   OR pg_catalog.strpos(config_entry,'=')<2 OR config_name=ANY(config_names)
                   OR config_name<>'search_path' THEN
                    RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
                END IF;
                config_names := pg_catalog.array_append(config_names,config_name);
            END LOOP;
        END IF;
        IF catalog_record.proname~'^offline_' AND catalog_record.nspname='public' AND
           (NOT catalog_record.prosecdef OR catalog_record.pronargdefaults<>0 OR catalog_record.provariadic<>0
            OR catalog_record.proconfig IS NULL OR pg_catalog.cardinality(catalog_record.proconfig)<>1
            OR catalog_record.proconfig[1]!~'^search_path=pg_catalog, *pg_temp$') THEN
            RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
        END IF;
'''
    func_acl = "COALESCE(catalog_record.proacl,pg_catalog.acldefault('f',catalog_record.proowner))"
    direct,effective,grantable,owned = privilege_rows('FUNCTION','catalog_record.oid','catalog_record.proowner',func_acl,[])
    execute = collection('SELECT ' + row('ACL-EXECUTE',[role('g.oid'),u1('1'),boolean(effective),boolean(grantable),boolean(owned)]) +
        " AS element FROM pg_catalog.unnest(universe_oids) g(oid) CROSS JOIN (VALUES ('EXECUTE'::pg_catalog.text)) p(name)")
    function = row('ACL-FUNCTION', [raw('catalog_record.nspname'),raw('catalog_record.proname'),text_list('input_names'),
        text_list('argument_names'),collection('SELECT v AS element,ordinal FROM pg_catalog.unnest(argument_modes) WITH ORDINALITY x(v,ordinal)',True),
        collection("SELECT CASE WHEN NULLIF(all_names[x.ordinal],'') IS NULL THEN " + blob('00') + ' ELSE '+present(raw('all_names[x.ordinal]'))+
            ' END AS element,x.ordinal FROM pg_catalog.unnest(all_types) WITH ORDINALITY x(v,ordinal)',True),u1('return_shape'),
        raw('canonical_type'),collection('SELECT v AS element,ordinal FROM pg_catalog.unnest(output_elements) WITH ORDINALITY x(v,ordinal)',True),
        u1("CASE catalog_record.provolatile WHEN 'i' THEN 1 WHEN 's' THEN 2 WHEN 'v' THEN 3 END"),boolean('catalog_record.prosecdef'),
        role('catalog_record.proowner'),'(CASE WHEN catalog_record.proconfig IS NULL THEN NULL::pg_catalog.bytea ELSE '+text_list('catalog_record.proconfig')+' END)',
        'pg_catalog.int4send(catalog_record.pronargdefaults)',raw('type_names[pg_catalog.array_position(type_oids,catalog_record.provariadic)]'),
        boolean('catalog_record.proisstrict'),execute])
    code += '        function_elements := pg_catalog.array_append(function_elements,' + function + ');\n    END LOOP;\n'
    code += '    acl_collections := pg_catalog.array_append(acl_collections,' + collection('SELECT v AS element FROM pg_catalog.unnest(function_elements) x(v)')+');\n'
    membership = row('ACL-MEMBERSHIP',[role('m.member'),role('m.roleid'),boolean('pg_catalog.bool_or(m.admin_option)'),
        boolean('pg_catalog.bool_or(m.inherit_option)'),boolean('pg_catalog.bool_or(m.set_option)')])
    code += '    acl_collections := pg_catalog.array_append(acl_collections,'+collection('SELECT '+membership+
        ' AS element FROM pg_catalog.pg_auth_members m WHERE m.member=ANY(protected_oids) OR m.roleid=ANY(protected_oids) GROUP BY m.member,m.roleid')+');\n'
    # Whole-relation/column ACLs are separately represented, including false rows.
    rel_acl="COALESCE(c.relacl,pg_catalog.acldefault('r',c.relowner))"
    direct,effective,grantable,owned=privilege_rows('RELATION','c.oid','c.relowner',rel_acl,[])
    whole=row('ACL-RELATION',[raw('n.nspname'),raw('c.relname'),blob('00'),role('c.relowner'),role('g.oid'),u1('p.code'),
        *[boolean(x) for x in (direct,effective,grantable,owned)]])
    rel_priv="(VALUES ('SELECT',4),('INSERT',5),('UPDATE',6),('DELETE',7),('TRUNCATE',8),('REFERENCES',9),('TRIGGER',10),('MAINTAIN',12)) p(name,code)"
    rel_query='SELECT '+whole+' AS element FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace CROSS JOIN pg_catalog.unnest(universe_oids) g(oid) CROSS JOIN '+rel_priv+' WHERE c.oid=ANY(relation_oids)'
    direct,effective,grantable,owned=privilege_rows('RELATION','c.oid','c.relowner',"COALESCE(t.attacl,ARRAY[]::pg_catalog.aclitem[])",[],column='t.attnum')
    # PUBLIC column effective includes the separately expanded whole-relation ACL.
    table_public="EXISTS(SELECT 1 FROM pg_catalog.aclexplode("+rel_acl+") a WHERE a.grantee=0 AND a.privilege_type=p.name)"
    effective='('+effective+' OR (g.oid=0 AND '+table_public+'))'
    table_public_grant="EXISTS(SELECT 1 FROM pg_catalog.aclexplode("+rel_acl+") a WHERE a.grantee=0 AND a.privilege_type=p.name AND a.is_grantable)"
    grantable='('+grantable+' OR (g.oid=0 AND '+table_public_grant+'))'
    col=row('ACL-RELATION',[raw('n.nspname'),raw('c.relname'),blob('01')+'||'+u4('pg_catalog.octet_length('+raw('t.attname')+')')+'||'+raw('t.attname'),role('c.relowner'),role('g.oid'),u1('p.code'),
        *[boolean(x) for x in (direct,effective,grantable,owned)]])
    rel_query+=' UNION ALL SELECT '+col+' AS element FROM (VALUES '+column_values+') inventory(relation,column_name) JOIN pg_catalog.pg_class c ON c.relname=inventory.relation JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace AND n.nspname=\'public\' JOIN pg_catalog.pg_attribute t ON t.attrelid=c.oid AND t.attname=inventory.column_name AND t.attnum>0 AND NOT t.attisdropped CROSS JOIN pg_catalog.unnest(universe_oids) g(oid) CROSS JOIN (VALUES (\'SELECT\',4),(\'INSERT\',5),(\'UPDATE\',6),(\'REFERENCES\',9)) p(name,code)'
    code+='    acl_collections := pg_catalog.array_append(acl_collections,'+collection(rel_query)+');\n'
    schema_acl="COALESCE(n.nspacl,pg_catalog.acldefault('n',n.nspowner))"
    direct,effective,grantable,owned=privilege_rows('SCHEMA','n.oid','n.nspowner',schema_acl,[])
    schema_row=row('ACL-SCHEMA',[u1('1'),raw('n.nspname'),role('n.nspowner'),role('g.oid'),u1('p.code'),*[boolean(x) for x in (direct,effective,grantable,owned)]])
    schema_query='SELECT '+schema_row+" AS element FROM pg_catalog.pg_namespace n CROSS JOIN pg_catalog.unnest(universe_oids) g(oid) CROSS JOIN (VALUES ('USAGE',2),('CREATE',3)) p(name,code) WHERE n.nspname!~'^pg_' AND n.nspname<>'information_schema'"
    db_acl="COALESCE(d.datacl,pg_catalog.acldefault('d',d.datdba))"
    direct,effective,grantable,owned=privilege_rows('DATABASE','d.oid','d.datdba',db_acl,[])
    db_row=row('ACL-SCHEMA',[u1('2'),raw('d.datname'),role('d.datdba'),role('g.oid'),u1('p.code'),*[boolean(x) for x in (direct,effective,grantable,owned)]])
    schema_query+=' UNION ALL SELECT '+db_row+" AS element FROM pg_catalog.pg_database d CROSS JOIN pg_catalog.unnest(universe_oids) g(oid) CROSS JOIN (VALUES ('CONNECT',11),('CREATE',3)) p(name,code) WHERE d.datname=pg_catalog.current_database()"
    code+='    acl_collections := pg_catalog.array_append(acl_collections,'+collection(schema_query)+');\n'
    default_row=row('ACL-DEFAULT',[role('creator.oid'),raw('scope.name'),u1('kind.code'),boolean('d.defaclrole IS NOT NULL'),
        role('COALESCE(a.grantee,0)'),u1("CASE a.privilege_type WHEN 'EXECUTE' THEN 1 WHEN 'USAGE' THEN 2 WHEN 'CREATE' THEN 3 WHEN 'SELECT' THEN 4 WHEN 'INSERT' THEN 5 WHEN 'UPDATE' THEN 6 WHEN 'DELETE' THEN 7 WHEN 'TRUNCATE' THEN 8 WHEN 'REFERENCES' THEN 9 WHEN 'TRIGGER' THEN 10 WHEN 'CONNECT' THEN 11 WHEN 'MAINTAIN' THEN 12 ELSE 0 END"),boolean('COALESCE(pg_catalog.bool_or(a.is_grantable),false)')])
    defaults_query='SELECT '+default_row+''' AS element FROM pg_catalog.unnest(creator_oids) creator(oid)
        CROSS JOIN (VALUES ('r',1),('S',2),('f',3),('T',4),('n',5),('L',6)) kind(type,code)
        CROSS JOIN LATERAL (SELECT 0::pg_catalog.oid AS oid,NULL::pg_catalog.text AS name
            UNION SELECT n.oid,n.nspname FROM pg_catalog.pg_namespace n WHERE n.nspname IN ('public','offline_crypto')
                OR EXISTS(SELECT 1 FROM pg_catalog.pg_default_acl extra WHERE extra.defaclrole=creator.oid AND extra.defaclnamespace=n.oid)) scope
        LEFT JOIN pg_catalog.pg_default_acl d ON d.defaclrole=creator.oid AND d.defaclnamespace=scope.oid AND d.defaclobjtype=kind.type::pg_catalog."char"
        LEFT JOIN LATERAL pg_catalog.aclexplode(d.defaclacl) a ON true
        GROUP BY creator.oid,scope.name,kind.code,d.defaclrole,a.grantee,a.privilege_type'''
    code+='    acl_collections := pg_catalog.array_append(acl_collections,'+collection(defaults_query)+');\n'
    code+='    live_acl := '+row('ACL',['acl_collections['+str(n)+']' for n in range(1,7)])+';\n'
    code+=deny('live_acl IS NULL OR live_acl<>ready_record.acl_manifest OR pg_catalog.sha256(live_acl)<>$6')
    return code


if __name__ == '__main__':
    source = SOURCE.read_text(encoding='utf-8-sig')
    generated = build(source, SPEC.read_text(encoding='utf-8-sig'))
    source = source.split('-- Internal Q: bound readiness/receipt', 1)[0].rstrip() + '\n\n' + generated
    SOURCE.write_text(source, encoding='utf-8')
