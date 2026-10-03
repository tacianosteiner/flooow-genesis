-- FLOOOW PACKAGE 0090 -- G3F.3B INCOMPLETE SOURCE CANDIDATE.
-- MIGRATION_COMPLETE=NO; MIGRATION_EXECUTABLE=NO; MIGRATION_VALIDATED=NO.
-- Do not execute or run Flyway against this incomplete candidate.
-- Normative contract: SPEC-0090 sections 21-25, including the approved amendments.
-- Complete guards/wrappers and independently approved golden evidence remain pending.
-- No wrappers, internal functions, crypto objects, service logins or deployment data.
-- NEW_CANONICAL_DOMAIN_AUTHORITY=NO. Future guards/admin governance enforce
-- cross-table transitions, immutability, permanent slot allocation and tombstones.
-- This draft changes no global schema/default privilege or existing ownership/security.
-- Future execution requires the approved administrative migration identity and
-- a transactional Flyway migration; no transaction/COMMIT is issued by this source.

-- Source-only safety interlock. Remove only at recorded implementation closure.
-- A comment is not an execution fence: an incomplete candidate must fail before DDL.
DO $$
BEGIN
    RAISE EXCEPTION USING ERRCODE = '55000',
        MESSAGE = 'Package 0090 V043 implementation closure is incomplete; execution denied';
END;
$$;

-- Trusted migration transaction only; do not depend on the caller's search path.
SET LOCAL search_path = pg_catalog, pg_temp;

-- SPEC 23.3/24.3: actual creator and ADMIN defaults are separate prerequisites.
-- Missing global defaults mean PostgreSQL hard-wired defaults, not an empty ACL.
-- Schema defaults add privileges; they cannot cancel unsafe global defaults.
-- This block inspects only; it neither provisions identities nor repairs defaults.
DO $$
DECLARE
    creator_oid pg_catalog.oid;
    creator_name pg_catalog.text;
    default_kind pg_catalog."char";
BEGIN
    IF SESSION_USER <> 'postgres' OR CURRENT_USER <> 'postgres'
       OR pg_catalog.current_setting('server_version_num')::pg_catalog.int4 < 180000
       OR pg_catalog.current_setting('server_version_num')::pg_catalog.int4 >= 190000
       OR pg_catalog.current_setting('server_encoding') <> 'UTF8' THEN
        RAISE EXCEPTION 'Package 0090 requires the approved direct postgres deployment identity and PostgreSQL 18 UTF8';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_catalog.pg_roles r
                   WHERE r.rolname = 'postgres' AND r.rolsuper AND r.rolcanlogin) THEN
        RAISE EXCEPTION 'Approved postgres deployment superuser prerequisite is missing';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_catalog.pg_namespace n WHERE n.nspname = 'public')
       OR EXISTS (
        SELECT 1 FROM pg_catalog.pg_namespace n
        CROSS JOIN LATERAL pg_catalog.aclexplode(COALESCE(n.nspacl, pg_catalog.acldefault('n', n.nspowner))) a
        WHERE n.nspname = 'public' AND a.grantee = 0 AND a.privilege_type = 'CREATE'
    ) THEN
        RAISE EXCEPTION 'Missing or PUBLIC-writable Package 0090 public schema prerequisite';
    END IF;
    FOREACH creator_name IN ARRAY ARRAY[
        'postgres', 'flooow_offline_control_owner',
        'flooow_offline_verification_owner', 'flooow_offline_issuance_owner',
        'flooow_offline_execution_owner', 'flooow_offline_audit_owner',
        'flooow_offline_principal_lock_owner', 'flooow_offline_readiness_owner',
        'flooow_offline_intent_audit_owner'
    ]::pg_catalog.text[] LOOP
        SELECT r.oid INTO creator_oid FROM pg_catalog.pg_roles r
        WHERE r.rolname = creator_name;
        IF NOT FOUND THEN
            IF creator_name IN ('postgres', 'flooow_offline_control_owner') THEN
                RAISE EXCEPTION 'Required separately provisioned Package 0090 administrative identity is missing';
            END IF;
            -- An absent wrapper owner creates no objects as that identity here.
            -- Its separately closed defaults remain required before operational use.
            CONTINUE;
        END IF;
        FOREACH default_kind IN ARRAY ARRAY['r','S','f','T','n','L']::pg_catalog."char"[] LOOP
            IF EXISTS (
                SELECT 1 FROM pg_catalog.aclexplode(COALESCE(
                    (SELECT d.defaclacl FROM pg_catalog.pg_default_acl d
                     WHERE d.defaclrole = creator_oid AND d.defaclnamespace = 0
                       AND d.defaclobjtype = default_kind),
                    pg_catalog.acldefault(
                        CASE WHEN default_kind = 'S' THEN 's'::pg_catalog."char"
                             ELSE default_kind END, creator_oid)
                )) a WHERE a.grantee <> creator_oid
            ) THEN
                RAISE EXCEPTION 'Unsafe Package 0090 global creator defaults; separate governed provisioning required';
            END IF;
        END LOOP;
        IF EXISTS (
            SELECT 1 FROM pg_catalog.pg_default_acl d
            CROSS JOIN LATERAL pg_catalog.aclexplode(d.defaclacl) a
            WHERE d.defaclrole = creator_oid AND a.grantee <> creator_oid
        ) OR EXISTS (
            SELECT 1 FROM pg_catalog.pg_default_acl d
            WHERE d.defaclrole = creator_oid
              AND d.defaclobjtype NOT IN ('r','S','f','T','n','L')
        ) THEN
            RAISE EXCEPTION 'Unsafe Package 0090 scoped or unsupported creator defaults';
        END IF;
    END LOOP;
END;
$$;

-- V: restricted NOLOGIN owner; adopt no unsafe pre-existing authority.
DO $$
DECLARE
    owner_role record;
BEGIN
    SELECT * INTO owner_role FROM pg_catalog.pg_roles WHERE rolname = 'flooow_offline_verification_owner';
    IF NOT FOUND THEN
        CREATE ROLE flooow_offline_verification_owner
            NOLOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
        SELECT * INTO owner_role FROM pg_catalog.pg_roles WHERE rolname = 'flooow_offline_verification_owner';
    END IF;
    IF owner_role.rolcanlogin OR owner_role.rolinherit OR owner_role.rolsuper
       OR owner_role.rolcreatedb OR owner_role.rolcreaterole
       OR owner_role.rolreplication OR owner_role.rolbypassrls THEN
        RAISE EXCEPTION 'Unsafe pre-existing flooow_offline_verification_owner attributes';
    END IF;
    IF EXISTS (SELECT 1 FROM pg_catalog.pg_auth_members m
               WHERE m.roleid = owner_role.oid OR m.member = owner_role.oid) THEN
        RAISE EXCEPTION 'Pre-existing flooow_offline_verification_owner membership is forbidden';
    END IF;
    IF EXISTS (SELECT 1 FROM pg_catalog.pg_shdepend d
               WHERE d.refclassid = 'pg_catalog.pg_authid'::pg_catalog.regclass
                 AND d.refobjid = owner_role.oid AND d.deptype IN ('o','a')
                 AND NOT (d.classid = 'pg_catalog.pg_default_acl'::pg_catalog.regclass
                          AND d.deptype = 'o'
                          AND d.dbid = (SELECT b.oid FROM pg_catalog.pg_database b WHERE b.datname = pg_catalog.current_database()))) THEN
        RAISE EXCEPTION 'Pre-existing flooow_offline_verification_owner ownership or ACL authority is forbidden';
    END IF;
END;
$$;

-- I: restricted NOLOGIN owner; adopt no unsafe pre-existing authority.
DO $$
DECLARE
    owner_role record;
BEGIN
    SELECT * INTO owner_role FROM pg_catalog.pg_roles WHERE rolname = 'flooow_offline_issuance_owner';
    IF NOT FOUND THEN
        CREATE ROLE flooow_offline_issuance_owner
            NOLOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
        SELECT * INTO owner_role FROM pg_catalog.pg_roles WHERE rolname = 'flooow_offline_issuance_owner';
    END IF;
    IF owner_role.rolcanlogin OR owner_role.rolinherit OR owner_role.rolsuper
       OR owner_role.rolcreatedb OR owner_role.rolcreaterole
       OR owner_role.rolreplication OR owner_role.rolbypassrls THEN
        RAISE EXCEPTION 'Unsafe pre-existing flooow_offline_issuance_owner attributes';
    END IF;
    IF EXISTS (SELECT 1 FROM pg_catalog.pg_auth_members m
               WHERE m.roleid = owner_role.oid OR m.member = owner_role.oid) THEN
        RAISE EXCEPTION 'Pre-existing flooow_offline_issuance_owner membership is forbidden';
    END IF;
    IF EXISTS (SELECT 1 FROM pg_catalog.pg_shdepend d
               WHERE d.refclassid = 'pg_catalog.pg_authid'::pg_catalog.regclass
                 AND d.refobjid = owner_role.oid AND d.deptype IN ('o','a')
                 AND NOT (d.classid = 'pg_catalog.pg_default_acl'::pg_catalog.regclass
                          AND d.deptype = 'o'
                          AND d.dbid = (SELECT b.oid FROM pg_catalog.pg_database b WHERE b.datname = pg_catalog.current_database()))) THEN
        RAISE EXCEPTION 'Pre-existing flooow_offline_issuance_owner ownership or ACL authority is forbidden';
    END IF;
END;
$$;

-- E: restricted NOLOGIN owner; adopt no unsafe pre-existing authority.
DO $$
DECLARE
    owner_role record;
BEGIN
    SELECT * INTO owner_role FROM pg_catalog.pg_roles WHERE rolname = 'flooow_offline_execution_owner';
    IF NOT FOUND THEN
        CREATE ROLE flooow_offline_execution_owner
            NOLOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
        SELECT * INTO owner_role FROM pg_catalog.pg_roles WHERE rolname = 'flooow_offline_execution_owner';
    END IF;
    IF owner_role.rolcanlogin OR owner_role.rolinherit OR owner_role.rolsuper
       OR owner_role.rolcreatedb OR owner_role.rolcreaterole
       OR owner_role.rolreplication OR owner_role.rolbypassrls THEN
        RAISE EXCEPTION 'Unsafe pre-existing flooow_offline_execution_owner attributes';
    END IF;
    IF EXISTS (SELECT 1 FROM pg_catalog.pg_auth_members m
               WHERE m.roleid = owner_role.oid OR m.member = owner_role.oid) THEN
        RAISE EXCEPTION 'Pre-existing flooow_offline_execution_owner membership is forbidden';
    END IF;
    IF EXISTS (SELECT 1 FROM pg_catalog.pg_shdepend d
               WHERE d.refclassid = 'pg_catalog.pg_authid'::pg_catalog.regclass
                 AND d.refobjid = owner_role.oid AND d.deptype IN ('o','a')
                 AND NOT (d.classid = 'pg_catalog.pg_default_acl'::pg_catalog.regclass
                          AND d.deptype = 'o'
                          AND d.dbid = (SELECT b.oid FROM pg_catalog.pg_database b WHERE b.datname = pg_catalog.current_database()))) THEN
        RAISE EXCEPTION 'Pre-existing flooow_offline_execution_owner ownership or ACL authority is forbidden';
    END IF;
END;
$$;

-- A: restricted NOLOGIN owner; adopt no unsafe pre-existing authority.
DO $$
DECLARE
    owner_role record;
BEGIN
    SELECT * INTO owner_role FROM pg_catalog.pg_roles WHERE rolname = 'flooow_offline_audit_owner';
    IF NOT FOUND THEN
        CREATE ROLE flooow_offline_audit_owner
            NOLOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
        SELECT * INTO owner_role FROM pg_catalog.pg_roles WHERE rolname = 'flooow_offline_audit_owner';
    END IF;
    IF owner_role.rolcanlogin OR owner_role.rolinherit OR owner_role.rolsuper
       OR owner_role.rolcreatedb OR owner_role.rolcreaterole
       OR owner_role.rolreplication OR owner_role.rolbypassrls THEN
        RAISE EXCEPTION 'Unsafe pre-existing flooow_offline_audit_owner attributes';
    END IF;
    IF EXISTS (SELECT 1 FROM pg_catalog.pg_auth_members m
               WHERE m.roleid = owner_role.oid OR m.member = owner_role.oid) THEN
        RAISE EXCEPTION 'Pre-existing flooow_offline_audit_owner membership is forbidden';
    END IF;
    IF EXISTS (SELECT 1 FROM pg_catalog.pg_shdepend d
               WHERE d.refclassid = 'pg_catalog.pg_authid'::pg_catalog.regclass
                 AND d.refobjid = owner_role.oid AND d.deptype IN ('o','a')
                 AND NOT (d.classid = 'pg_catalog.pg_default_acl'::pg_catalog.regclass
                          AND d.deptype = 'o'
                          AND d.dbid = (SELECT b.oid FROM pg_catalog.pg_database b WHERE b.datname = pg_catalog.current_database()))) THEN
        RAISE EXCEPTION 'Pre-existing flooow_offline_audit_owner ownership or ACL authority is forbidden';
    END IF;
END;
$$;

-- P: restricted NOLOGIN owner; adopt no unsafe pre-existing authority.
DO $$
DECLARE
    owner_role record;
BEGIN
    SELECT * INTO owner_role FROM pg_catalog.pg_roles WHERE rolname = 'flooow_offline_principal_lock_owner';
    IF NOT FOUND THEN
        CREATE ROLE flooow_offline_principal_lock_owner
            NOLOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
        SELECT * INTO owner_role FROM pg_catalog.pg_roles WHERE rolname = 'flooow_offline_principal_lock_owner';
    END IF;
    IF owner_role.rolcanlogin OR owner_role.rolinherit OR owner_role.rolsuper
       OR owner_role.rolcreatedb OR owner_role.rolcreaterole
       OR owner_role.rolreplication OR owner_role.rolbypassrls THEN
        RAISE EXCEPTION 'Unsafe pre-existing flooow_offline_principal_lock_owner attributes';
    END IF;
    IF EXISTS (SELECT 1 FROM pg_catalog.pg_auth_members m
               WHERE m.roleid = owner_role.oid OR m.member = owner_role.oid) THEN
        RAISE EXCEPTION 'Pre-existing flooow_offline_principal_lock_owner membership is forbidden';
    END IF;
    IF EXISTS (SELECT 1 FROM pg_catalog.pg_shdepend d
               WHERE d.refclassid = 'pg_catalog.pg_authid'::pg_catalog.regclass
                 AND d.refobjid = owner_role.oid AND d.deptype IN ('o','a')
                 AND NOT (d.classid = 'pg_catalog.pg_default_acl'::pg_catalog.regclass
                          AND d.deptype = 'o'
                          AND d.dbid = (SELECT b.oid FROM pg_catalog.pg_database b WHERE b.datname = pg_catalog.current_database()))) THEN
        RAISE EXCEPTION 'Pre-existing flooow_offline_principal_lock_owner ownership or ACL authority is forbidden';
    END IF;
END;
$$;

-- Q: restricted NOLOGIN owner; adopt no unsafe pre-existing authority.
DO $$
DECLARE
    owner_role record;
BEGIN
    SELECT * INTO owner_role FROM pg_catalog.pg_roles WHERE rolname = 'flooow_offline_readiness_owner';
    IF NOT FOUND THEN
        CREATE ROLE flooow_offline_readiness_owner
            NOLOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
        SELECT * INTO owner_role FROM pg_catalog.pg_roles WHERE rolname = 'flooow_offline_readiness_owner';
    END IF;
    IF owner_role.rolcanlogin OR owner_role.rolinherit OR owner_role.rolsuper
       OR owner_role.rolcreatedb OR owner_role.rolcreaterole
       OR owner_role.rolreplication OR owner_role.rolbypassrls THEN
        RAISE EXCEPTION 'Unsafe pre-existing flooow_offline_readiness_owner attributes';
    END IF;
    IF EXISTS (SELECT 1 FROM pg_catalog.pg_auth_members m
               WHERE m.roleid = owner_role.oid OR m.member = owner_role.oid) THEN
        RAISE EXCEPTION 'Pre-existing flooow_offline_readiness_owner membership is forbidden';
    END IF;
    IF EXISTS (SELECT 1 FROM pg_catalog.pg_shdepend d
               WHERE d.refclassid = 'pg_catalog.pg_authid'::pg_catalog.regclass
                 AND d.refobjid = owner_role.oid AND d.deptype IN ('o','a')
                 AND NOT (d.classid = 'pg_catalog.pg_default_acl'::pg_catalog.regclass
                          AND d.deptype = 'o'
                          AND d.dbid = (SELECT b.oid FROM pg_catalog.pg_database b WHERE b.datname = pg_catalog.current_database()))
                 AND NOT (d.deptype = 'a'
                          AND d.dbid = (SELECT b.oid FROM pg_catalog.pg_database b WHERE b.datname = pg_catalog.current_database())
                          AND ((d.classid = 'pg_catalog.pg_namespace'::pg_catalog.regclass
                                AND d.objid = (SELECT n.oid FROM pg_catalog.pg_namespace n WHERE n.nspname = 'offline_crypto'))
                            OR (d.classid = 'pg_catalog.pg_proc'::pg_catalog.regclass
                                AND d.objid IN (
                                    pg_catalog.to_regprocedure('offline_crypto.hmac(pg_catalog.bytea,pg_catalog.bytea,pg_catalog.text)'),
                                    pg_catalog.to_regprocedure('offline_crypto.timing_safe_equal32(pg_catalog.bytea,pg_catalog.bytea)')
                                ))))) THEN
        RAISE EXCEPTION 'Pre-existing flooow_offline_readiness_owner ownership or ACL authority is forbidden';
    END IF;
    -- SPEC 23: preinstalled crypto grants are required, not unsafe adoption.
    -- Permit only the exact non-owner/non-grantable grants; verify objects below.
    IF NOT EXISTS (
        SELECT 1 FROM pg_catalog.pg_namespace n
        CROSS JOIN LATERAL pg_catalog.aclexplode(n.nspacl) a
        WHERE n.nspname = 'offline_crypto' AND a.grantee = owner_role.oid
          AND a.privilege_type = 'USAGE' AND NOT a.is_grantable
    ) OR EXISTS (
        SELECT 1 FROM pg_catalog.pg_namespace n
        CROSS JOIN LATERAL pg_catalog.aclexplode(n.nspacl) a
        WHERE n.nspname = 'offline_crypto' AND a.grantee = owner_role.oid
          AND (a.privilege_type <> 'USAGE' OR a.is_grantable)
    ) THEN
        RAISE EXCEPTION 'Required exact Q crypto schema USAGE is missing or unsafe';
    END IF;
    IF (SELECT pg_catalog.count(*) FROM pg_catalog.pg_proc p
        CROSS JOIN LATERAL pg_catalog.aclexplode(p.proacl) a
        WHERE p.oid IN (
            pg_catalog.to_regprocedure('offline_crypto.hmac(pg_catalog.bytea,pg_catalog.bytea,pg_catalog.text)'),
            pg_catalog.to_regprocedure('offline_crypto.timing_safe_equal32(pg_catalog.bytea,pg_catalog.bytea)')
        ) AND a.grantee = owner_role.oid AND a.privilege_type = 'EXECUTE'
          AND NOT a.is_grantable) <> 2
       OR EXISTS (
        SELECT 1 FROM pg_catalog.pg_proc p
        CROSS JOIN LATERAL pg_catalog.aclexplode(p.proacl) a
        WHERE p.oid IN (
            pg_catalog.to_regprocedure('offline_crypto.hmac(pg_catalog.bytea,pg_catalog.bytea,pg_catalog.text)'),
            pg_catalog.to_regprocedure('offline_crypto.timing_safe_equal32(pg_catalog.bytea,pg_catalog.bytea)')
        ) AND a.grantee = owner_role.oid
          AND (a.privilege_type <> 'EXECUTE' OR a.is_grantable)
    ) THEN
        RAISE EXCEPTION 'Required exact Q crypto EXECUTE grants are missing or unsafe';
    END IF;
END;
$$;

-- SPEC 23 dependency inspection, never installation or crypto ACL repair.
-- Binary provenance and complete independently approved member inventory remain
-- separate deployment evidence, not inferred from these catalog properties.
DO $$
DECLARE
    deployment_oid pg_catalog.oid;
    readiness_oid pg_catalog.oid;
    crypto_namespace pg_catalog.oid;
    crypto_function record;
BEGIN
    SELECT r.oid INTO deployment_oid FROM pg_catalog.pg_roles r WHERE r.rolname = 'postgres';
    SELECT r.oid INTO readiness_oid FROM pg_catalog.pg_roles r WHERE r.rolname = 'flooow_offline_readiness_owner';
    SELECT n.oid INTO crypto_namespace FROM pg_catalog.pg_namespace n
    WHERE n.nspname = 'offline_crypto' AND n.nspowner = deployment_oid;
    IF crypto_namespace IS NULL OR readiness_oid IS NULL THEN
        RAISE EXCEPTION 'Approved Package 0090 crypto schema/identity prerequisite is missing';
    END IF;
    IF (SELECT pg_catalog.count(*) FROM pg_catalog.pg_extension e
        WHERE e.extowner = deployment_oid AND e.extnamespace = crypto_namespace
          AND ((e.extname = 'pgcrypto' AND e.extversion = '1.4')
            OR (e.extname = 'flooow_offline_mac32' AND e.extversion = '1.0'))) <> 2 THEN
        RAISE EXCEPTION 'Approved version-pinned crypto dependencies are missing or mismatched';
    END IF;
    IF EXISTS (
        SELECT 1 FROM pg_catalog.pg_namespace n
        CROSS JOIN LATERAL pg_catalog.aclexplode(COALESCE(n.nspacl, pg_catalog.acldefault('n', n.nspowner))) a
        WHERE n.oid = crypto_namespace AND a.grantee <> deployment_oid
          AND (a.grantee <> readiness_oid OR a.privilege_type <> 'USAGE' OR a.is_grantable)
    ) THEN
        RAISE EXCEPTION 'Unapproved crypto schema privilege';
    END IF;
    FOR crypto_function IN
        SELECT p.*, l.lanname, e.extname FROM pg_catalog.pg_proc p
        JOIN pg_catalog.pg_language l ON l.oid = p.prolang
        JOIN pg_catalog.pg_depend d ON d.classid = 'pg_catalog.pg_proc'::pg_catalog.regclass
             AND d.objid = p.oid AND d.deptype = 'e'
             AND d.refclassid = 'pg_catalog.pg_extension'::pg_catalog.regclass
        JOIN pg_catalog.pg_extension e ON e.oid = d.refobjid
        WHERE e.extname IN ('pgcrypto', 'flooow_offline_mac32')
    LOOP
        IF crypto_function.proowner <> deployment_oid OR crypto_function.pronamespace <> crypto_namespace THEN
            RAISE EXCEPTION 'Unapproved crypto member owner or schema';
        END IF;
        IF EXISTS (
            SELECT 1 FROM pg_catalog.aclexplode(COALESCE(crypto_function.proacl,
                pg_catalog.acldefault('f', crypto_function.proowner))) a
            WHERE a.grantee <> deployment_oid
              AND (a.grantee <> readiness_oid OR a.privilege_type <> 'EXECUTE' OR a.is_grantable
                OR crypto_function.oid NOT IN (
                    pg_catalog.to_regprocedure('offline_crypto.hmac(pg_catalog.bytea,pg_catalog.bytea,pg_catalog.text)'),
                    pg_catalog.to_regprocedure('offline_crypto.timing_safe_equal32(pg_catalog.bytea,pg_catalog.bytea)')
                ))
        ) THEN
            RAISE EXCEPTION 'Unapproved crypto member privilege';
        END IF;
    END LOOP;
    IF (SELECT pg_catalog.count(*) FROM pg_catalog.pg_proc p
        JOIN pg_catalog.pg_language l ON l.oid = p.prolang
        JOIN pg_catalog.pg_depend d ON d.classid = 'pg_catalog.pg_proc'::pg_catalog.regclass
             AND d.objid = p.oid AND d.deptype = 'e'
             AND d.refclassid = 'pg_catalog.pg_extension'::pg_catalog.regclass
        JOIN pg_catalog.pg_extension e ON e.oid = d.refobjid
        WHERE p.proowner = deployment_oid AND p.pronamespace = crypto_namespace
          AND l.lanname = 'c' AND p.prokind = 'f' AND p.provolatile = 'i'
          AND p.proisstrict AND NOT p.prosecdef AND NOT p.proretset
          AND p.pronargdefaults = 0 AND p.provariadic = 0
          AND p.proargnames IS NULL AND p.proallargtypes IS NULL
          AND p.proargmodes IS NULL AND p.proconfig IS NULL
          AND ((p.oid = pg_catalog.to_regprocedure('offline_crypto.hmac(pg_catalog.bytea,pg_catalog.bytea,pg_catalog.text)')
                AND p.prorettype = 'pg_catalog.bytea'::pg_catalog.regtype
                AND e.extname = 'pgcrypto' AND p.prosrc = 'pg_hmac' AND p.probin = '$libdir/pgcrypto')
            OR (p.oid = pg_catalog.to_regprocedure('offline_crypto.timing_safe_equal32(pg_catalog.bytea,pg_catalog.bytea)')
                AND p.prorettype = 'pg_catalog.bool'::pg_catalog.regtype AND p.proparallel = 's'
                AND e.extname = 'flooow_offline_mac32' AND p.prosrc = 'timing_safe_equal32'
                AND p.probin = '$libdir/flooow_offline_mac32'))) <> 2 THEN
        RAISE EXCEPTION 'Approved exact crypto function contract is missing or mismatched';
    END IF;
END;
$$;

-- Z: restricted NOLOGIN owner; adopt no unsafe pre-existing authority.
DO $$
DECLARE
    owner_role record;
BEGIN
    SELECT * INTO owner_role FROM pg_catalog.pg_roles WHERE rolname = 'flooow_offline_intent_audit_owner';
    IF NOT FOUND THEN
        CREATE ROLE flooow_offline_intent_audit_owner
            NOLOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
        SELECT * INTO owner_role FROM pg_catalog.pg_roles WHERE rolname = 'flooow_offline_intent_audit_owner';
    END IF;
    IF owner_role.rolcanlogin OR owner_role.rolinherit OR owner_role.rolsuper
       OR owner_role.rolcreatedb OR owner_role.rolcreaterole
       OR owner_role.rolreplication OR owner_role.rolbypassrls THEN
        RAISE EXCEPTION 'Unsafe pre-existing flooow_offline_intent_audit_owner attributes';
    END IF;
    IF EXISTS (SELECT 1 FROM pg_catalog.pg_auth_members m
               WHERE m.roleid = owner_role.oid OR m.member = owner_role.oid) THEN
        RAISE EXCEPTION 'Pre-existing flooow_offline_intent_audit_owner membership is forbidden';
    END IF;
    IF EXISTS (SELECT 1 FROM pg_catalog.pg_shdepend d
               WHERE d.refclassid = 'pg_catalog.pg_authid'::pg_catalog.regclass
                 AND d.refobjid = owner_role.oid AND d.deptype IN ('o','a')
                 AND NOT (d.classid = 'pg_catalog.pg_default_acl'::pg_catalog.regclass
                          AND d.deptype = 'o'
                          AND d.dbid = (SELECT b.oid FROM pg_catalog.pg_database b WHERE b.datname = pg_catalog.current_database()))) THEN
        RAISE EXCEPTION 'Pre-existing flooow_offline_intent_audit_owner ownership or ACL authority is forbidden';
    END IF;
END;
$$;

-- ADMIN: SPEC 24 separately provisioned NOLOGIN INHERIT control owner.
-- V043 never creates, alters or repairs this identity.
DO $$
DECLARE
    owner_role record;
BEGIN
    SELECT * INTO owner_role FROM pg_catalog.pg_roles WHERE rolname = 'flooow_offline_control_owner';
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Required separately provisioned flooow_offline_control_owner is missing';
    END IF;
    IF owner_role.rolcanlogin OR NOT owner_role.rolinherit OR owner_role.rolsuper
       OR owner_role.rolcreatedb OR owner_role.rolcreaterole
       OR owner_role.rolreplication OR owner_role.rolbypassrls THEN
        RAISE EXCEPTION 'Unsafe pre-existing flooow_offline_control_owner attributes';
    END IF;
    IF EXISTS (SELECT 1 FROM pg_catalog.pg_auth_members m
               WHERE m.roleid = owner_role.oid OR m.member = owner_role.oid) THEN
        RAISE EXCEPTION 'Pre-existing flooow_offline_control_owner membership is forbidden';
    END IF;
    IF EXISTS (SELECT 1 FROM pg_catalog.pg_shdepend d
               WHERE d.refclassid = 'pg_catalog.pg_authid'::pg_catalog.regclass
                 AND d.refobjid = owner_role.oid AND d.deptype IN ('o','a')
                 AND NOT (d.classid = 'pg_catalog.pg_default_acl'::pg_catalog.regclass AND d.deptype = 'o'
                          AND d.dbid = (SELECT b.oid FROM pg_catalog.pg_database b WHERE b.datname = pg_catalog.current_database()))
                 AND NOT (d.classid = 'pg_catalog.pg_namespace'::pg_catalog.regclass
                          AND d.deptype = 'a'
                          AND d.dbid = (SELECT b.oid FROM pg_catalog.pg_database b WHERE b.datname = pg_catalog.current_database())
                          AND d.objid = (SELECT n.oid FROM pg_catalog.pg_namespace n WHERE n.nspname = 'public'))) THEN
        RAISE EXCEPTION 'Pre-existing flooow_offline_control_owner ownership or ACL authority is forbidden';
    END IF;
    IF EXISTS (
        SELECT 1 FROM pg_catalog.pg_namespace n
        CROSS JOIN LATERAL pg_catalog.aclexplode(n.nspacl) a
        WHERE n.nspname = 'public' AND a.grantee = owner_role.oid
          AND (a.privilege_type <> 'USAGE' OR a.is_grantable)
    ) THEN
        RAISE EXCEPTION 'Only non-grantable public schema USAGE is approved for ADMIN';
    END IF;
END;
$$;

-- T01; SPEC 21.7 / approved G1-G2 structural design.
-- FENCE. Immutable 38-tag header plus fingerprint and retained manifest bytes. No operational UPDATE. Slots/tombstones never rebound; full codec/hash/identity checks remain future guards.
CREATE TABLE public.offline_binding_header (
    binding_schema_version pg_catalog.int4 NOT NULL,
    binding_id pg_catalog.uuid NOT NULL,
    deployment_id pg_catalog.uuid NOT NULL,
    deployment_incarnation_id pg_catalog.uuid NOT NULL,
    run_id pg_catalog.uuid NOT NULL,
    plan_id pg_catalog.uuid NOT NULL,
    execution_plan_version pg_catalog.int4 NOT NULL,
    organization_id pg_catalog.uuid NOT NULL,
    manifest_id pg_catalog.uuid NOT NULL,
    manifest_digest pg_catalog.bytea NOT NULL,
    canonical_manifest_hash pg_catalog.bytea NOT NULL,
    canonical_manifest_encoding_version pg_catalog.int4 NOT NULL,
    mercado_livre_connection_id pg_catalog.uuid NOT NULL,
    omie_connection_id pg_catalog.uuid NOT NULL,
    marketplace_order_id pg_catalog.uuid NOT NULL,
    source_order_reference pg_catalog.text NOT NULL,
    integration_reference pg_catalog.text NOT NULL,
    permission pg_catalog.text NOT NULL,
    reason pg_catalog.text NOT NULL,
    provenance pg_catalog.text NOT NULL,
    principal_id pg_catalog.uuid NOT NULL,
    credential_id pg_catalog.uuid NOT NULL,
    grant_id pg_catalog.uuid NOT NULL,
    decision_id pg_catalog.uuid NOT NULL,
    correlation_id pg_catalog.uuid NOT NULL,
    principal_operation_id pg_catalog.uuid NOT NULL,
    credential_operation_id pg_catalog.uuid NOT NULL,
    grant_operation_id pg_catalog.uuid NOT NULL,
    issued_at pg_catalog.timestamptz NOT NULL,
    valid_from pg_catalog.timestamptz NOT NULL,
    expires_at pg_catalog.timestamptz NOT NULL,
    identity_slots pg_catalog.bytea NOT NULL,
    offline_surface_version pg_catalog.text NOT NULL,
    deadline_policy_version pg_catalog.text NOT NULL,
    deadline_policy_digest pg_catalog.bytea NOT NULL,
    admission_contract_version pg_catalog.text NOT NULL,
    delivery_contract_version pg_catalog.text NOT NULL,
    reconciliation_contract_version pg_catalog.text NOT NULL,
    plan_fingerprint pg_catalog.bytea NOT NULL,
    canonical_manifest_bytes pg_catalog.bytea NOT NULL,
    CONSTRAINT offline_binding_header_pk PRIMARY KEY (binding_id),
    CONSTRAINT offline_binding_header_uq1 UNIQUE (deployment_incarnation_id,plan_id),
    CONSTRAINT offline_binding_header_ck1 CHECK (
        binding_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid AND
        deployment_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid AND
        deployment_incarnation_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid AND
        run_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid AND
        plan_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid AND
        organization_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid AND
        manifest_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid AND
        mercado_livre_connection_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid AND
        omie_connection_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid AND
        marketplace_order_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid AND
        principal_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid AND
        credential_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid AND
        grant_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid AND
        decision_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid AND
        correlation_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid AND
        principal_operation_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid AND
        credential_operation_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid AND
        grant_operation_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid
        AND binding_schema_version = 1
        AND execution_plan_version > 0
        AND canonical_manifest_encoding_version > 0
    ),
    CONSTRAINT offline_binding_header_ck2 CHECK (
        pg_catalog.octet_length(manifest_digest) = 32
        AND pg_catalog.octet_length(canonical_manifest_hash) = 32
        AND pg_catalog.octet_length(deadline_policy_digest) = 32
        AND pg_catalog.octet_length(plan_fingerprint) = 32
        AND pg_catalog.octet_length(canonical_manifest_bytes) > 0
        AND pg_catalog.octet_length(identity_slots) > 0
        AND manifest_digest = canonical_manifest_hash
        AND canonical_manifest_hash = pg_catalog.sha256(canonical_manifest_bytes)
        AND offline_surface_version = '0090-v1'
        AND admission_contract_version = '1'
        AND delivery_contract_version = '1'
        AND reconciliation_contract_version = '1'
        AND permission = 'TRANSACTION_IDENTITY_DECISION_WRITE'
        AND (source_order_reference <> ''
        AND source_order_reference IS NFC NORMALIZED
        AND source_order_reference !~ '[[:cntrl:]]')
        AND (integration_reference <> ''
        AND integration_reference IS NFC NORMALIZED
        AND integration_reference !~ '[[:cntrl:]]')
        AND (reason <> ''
        AND reason IS NFC NORMALIZED
        AND reason !~ '[[:cntrl:]]')
        AND (provenance <> ''
        AND provenance IS NFC NORMALIZED
        AND provenance !~ '[[:cntrl:]]')
        AND (deadline_policy_version <> ''
        AND deadline_policy_version IS NFC NORMALIZED
        AND deadline_policy_version !~ '[[:cntrl:]]')
    ),
    CONSTRAINT offline_binding_header_ck3 CHECK (
        pg_catalog.isfinite(issued_at) AND pg_catalog.isfinite(valid_from) AND pg_catalog.isfinite(expires_at) AND issued_at < expires_at AND valid_from < expires_at
    )
);

-- T02; SPEC 21.7 / approved G1-G2 structural design.
-- OPERATIONAL_STATE/FENCE. ADMIN governs activation/revocation/expiry. lock_token is never changed; UPDATE is granted only to enable row locks.
CREATE TABLE public.offline_binding_lifecycle (
    binding_id pg_catalog.uuid NOT NULL,
    state pg_catalog.text NOT NULL,
    lock_token pg_catalog.int8 NOT NULL,
    CONSTRAINT offline_binding_lifecycle_pk PRIMARY KEY (binding_id),
    CONSTRAINT offline_binding_lifecycle_ck1 CHECK (
        binding_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid AND state IN ('REGISTERED','ACTIVE','REVOKED','EXPIRED') AND lock_token = 0
    )
);

-- T03; SPEC 21.7 / approved G1-G2 structural design.
-- FENCE. ADMIN alone advances generation/claim permission under drain. E changes only current_attempt_id at original claim; cross-generation coherence needs future C guards.
CREATE TABLE public.offline_attempt_pointer (
    binding_id pg_catalog.uuid NOT NULL,
    current_attempt_id pg_catalog.uuid NULL,
    generation pg_catalog.int8 NOT NULL,
    claim_permitted pg_catalog.bool NOT NULL,
    lock_token pg_catalog.int8 NOT NULL,
    CONSTRAINT offline_attempt_pointer_pk PRIMARY KEY (binding_id),
    CONSTRAINT offline_attempt_pointer_ck1 CHECK (
        generation > 0 AND lock_token = 0
    ),
    CONSTRAINT offline_attempt_pointer_ck2 CHECK (
        binding_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid AND
        (current_attempt_id IS NULL OR current_attempt_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid)
    )
);

-- T04; SPEC 21.7 / approved G1-G2 structural design.
-- BOOKKEEPING/OPERATIONAL_STATE/FENCE. Claim initializes original absolute window. No deadline renewal; transition and current-pointer guards remain future wrappers.
CREATE TABLE public.offline_attempt (
    binding_id pg_catalog.uuid NOT NULL,
    attempt_id pg_catalog.uuid NOT NULL,
    generation pg_catalog.int8 NOT NULL,
    state pg_catalog.text NOT NULL,
    claimed_at pg_catalog.timestamptz NOT NULL,
    expires_at pg_catalog.timestamptz NOT NULL,
    lock_token pg_catalog.int8 NOT NULL,
    CONSTRAINT offline_attempt_pk PRIMARY KEY (binding_id,attempt_id),
    CONSTRAINT offline_attempt_uq1 UNIQUE (binding_id,generation),
    CONSTRAINT offline_attempt_ck1 CHECK (
        binding_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid AND
        attempt_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid
        AND generation > 0
        AND lock_token = 0
        AND state IN ('CLAIMED','EFFECTS_IN_PROGRESS','RECOVERY_REQUIRED','EFFECTS_COMPLETE','ABORTED')
    ),
    CONSTRAINT offline_attempt_ck2 CHECK (
        pg_catalog.isfinite(claimed_at) AND pg_catalog.isfinite(expires_at) AND claimed_at < expires_at
    )
);

-- T05; SPEC 21.7 / approved G1-G2 structural design.
-- FENCE/OPERATIONAL_STATE. Digest is private and never projected. No secret reconstruction on restart; absolute deadlines are immutable operationally.
CREATE TABLE public.offline_execution (
    binding_id pg_catalog.uuid NOT NULL,
    attempt_id pg_catalog.uuid NOT NULL,
    generation pg_catalog.int8 NOT NULL,
    execution_id pg_catalog.uuid NOT NULL,
    instance_id pg_catalog.uuid NOT NULL,
    executor_oid pg_catalog.int8 NOT NULL,
    state pg_catalog.text NOT NULL,
    possession_digest pg_catalog.bytea NOT NULL,
    claimed_at pg_catalog.timestamptz NOT NULL,
    expires_at pg_catalog.timestamptz NOT NULL,
    claim_receipt_id pg_catalog.uuid NOT NULL,
    lock_token pg_catalog.int8 NOT NULL,
    CONSTRAINT offline_execution_pk PRIMARY KEY (binding_id,attempt_id,generation),
    CONSTRAINT offline_execution_uq1 UNIQUE (execution_id),
    CONSTRAINT offline_execution_uq2 UNIQUE (claim_receipt_id),
    CONSTRAINT offline_execution_ck1 CHECK (
        state IN ('OWNED','RELEASED','STALE')
    ),
    CONSTRAINT offline_execution_ck2 CHECK (
        binding_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid AND
        attempt_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid AND
        execution_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid AND
        instance_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid AND
        claim_receipt_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid
        AND generation > 0
        AND executor_oid BETWEEN 1
        AND 4294967295
        AND lock_token = 0
        AND pg_catalog.octet_length(possession_digest) = 32
    ),
    CONSTRAINT offline_execution_ck3 CHECK (
        pg_catalog.isfinite(claimed_at) AND pg_catalog.isfinite(expires_at) AND claimed_at < expires_at
    )
);

-- T06; SPEC 21.7 / approved G1-G2 structural design.
-- BOOKKEEPING/OPERATIONAL_STATE/AUDIT. Initial origin is written only with fresh credential Applied. Consumption commit precedes one TTY attempt; no human-receipt guarantee.
CREATE TABLE public.offline_delivery (
    binding_id pg_catalog.uuid NOT NULL,
    attempt_id pg_catalog.uuid NULL,
    generation pg_catalog.int8 NOT NULL,
    execution_id pg_catalog.uuid NULL,
    instance_id pg_catalog.uuid NULL,
    credential_id pg_catalog.uuid NULL,
    initial_operation_id pg_catalog.uuid NULL,
    fresh_applied_receipt_id pg_catalog.uuid NULL,
    state pg_catalog.text NOT NULL,
    delivery_receipt_id pg_catalog.uuid NULL,
    attempted_at pg_catalog.timestamptz NULL,
    operation_deadline pg_catalog.timestamptz NULL,
    observed_at pg_catalog.timestamptz NULL,
    observation_code pg_catalog.text NULL,
    recorded_at pg_catalog.timestamptz NULL,
    lock_token pg_catalog.int8 NOT NULL,
    CONSTRAINT offline_delivery_pk PRIMARY KEY (binding_id),
    CONSTRAINT offline_delivery_ck1 CHECK (
        state IN ('NOT_CREATED','CREATED_NOT_DELIVERABLE','DELIVERY_ATTEMPTED','DELIVERY_ACKNOWLEDGED','DELIVERY_FAILED_REVIEW_REQUIRED','DELIVERY_OUTCOME_UNKNOWN')
    ),
    CONSTRAINT offline_delivery_ck2 CHECK (
        binding_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid AND
        (attempt_id IS NULL OR attempt_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid) AND
        (execution_id IS NULL OR execution_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid) AND
        (instance_id IS NULL OR instance_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid) AND
        (credential_id IS NULL OR credential_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid) AND
        (initial_operation_id IS NULL OR initial_operation_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid) AND
        (fresh_applied_receipt_id IS NULL OR fresh_applied_receipt_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid) AND
        (delivery_receipt_id IS NULL
        OR delivery_receipt_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid)
        AND generation > 0
        AND lock_token = 0
        AND ((state = 'NOT_CREATED'
        AND attempt_id IS NULL
        AND execution_id IS NULL
        AND instance_id IS NULL
        AND credential_id IS NULL
        AND initial_operation_id IS NULL
        AND fresh_applied_receipt_id IS NULL)
        OR (state <> 'NOT_CREATED'
        AND attempt_id IS NOT NULL
        AND execution_id IS NOT NULL
        AND instance_id IS NOT NULL
        AND credential_id IS NOT NULL
        AND initial_operation_id IS NOT NULL
        AND fresh_applied_receipt_id IS NOT NULL))
    ),
    CONSTRAINT offline_delivery_ck3 CHECK (
        ((delivery_receipt_id IS NULL
        AND attempted_at IS NULL
        AND operation_deadline IS NULL)
        OR (delivery_receipt_id IS NOT NULL
        AND attempted_at IS NOT NULL
        AND operation_deadline IS NOT NULL
        AND pg_catalog.isfinite(attempted_at)
        AND pg_catalog.isfinite(operation_deadline)
        AND attempted_at < operation_deadline))
        AND ((state IN ('NOT_CREATED','CREATED_NOT_DELIVERABLE')
        AND delivery_receipt_id IS NULL
        AND attempted_at IS NULL
        AND operation_deadline IS NULL
        AND observed_at IS NULL
        AND observation_code IS NULL
        AND recorded_at IS NULL)
        OR (state IN ('DELIVERY_ATTEMPTED','DELIVERY_ACKNOWLEDGED','DELIVERY_OUTCOME_UNKNOWN')
        AND delivery_receipt_id IS NOT NULL
        AND attempted_at IS NOT NULL
        AND operation_deadline IS NOT NULL)
        OR state = 'DELIVERY_FAILED_REVIEW_REQUIRED')
        AND ((observed_at IS NULL
        AND observation_code IS NULL
        AND recorded_at IS NULL)
        OR (observed_at IS NOT NULL
        AND observation_code IS NOT NULL
        AND recorded_at IS NOT NULL
        AND pg_catalog.isfinite(observed_at)
        AND pg_catalog.isfinite(recorded_at)
        AND observation_code IN ('COMPLETE','PARTIAL','IO_FAILURE','PROCESS_UNCERTAINTY')))
        AND (state <> 'DELIVERY_ACKNOWLEDGED'
        OR (observed_at IS NOT NULL
        AND observation_code IS NOT NULL
        AND recorded_at IS NOT NULL))
    )
);

-- T07; SPEC 21.7 / approved G1-G2 structural design.
-- BOOKKEEPING/FENCE. ISSUED/CONSUMED only; effective validity is derived by future guards. Consumption is atomic with decision, never renewal or replay.
CREATE TABLE public.offline_admission (
    admission_id pg_catalog.uuid NOT NULL,
    deployment_id pg_catalog.uuid NOT NULL,
    incarnation_id pg_catalog.uuid NOT NULL,
    binding_id pg_catalog.uuid NOT NULL,
    attempt_id pg_catalog.uuid NOT NULL,
    generation pg_catalog.int8 NOT NULL,
    execution_id pg_catalog.uuid NOT NULL,
    instance_id pg_catalog.uuid NOT NULL,
    executor_oid pg_catalog.int8 NOT NULL,
    credential_id pg_catalog.uuid NOT NULL,
    credential_revision pg_catalog.int4 NOT NULL,
    principal_id pg_catalog.uuid NOT NULL,
    organization_id pg_catalog.uuid NOT NULL,
    grant_id pg_catalog.uuid NOT NULL,
    grant_revision pg_catalog.int4 NOT NULL,
    authorization_fingerprint pg_catalog.bytea NOT NULL,
    permission pg_catalog.text NOT NULL,
    authenticated_at pg_catalog.timestamptz NOT NULL,
    expires_at pg_catalog.timestamptz NOT NULL,
    durable_state pg_catalog.text NOT NULL,
    consumed_decision_id pg_catalog.uuid NULL,
    consumed_at pg_catalog.timestamptz NULL,
    lock_token pg_catalog.int8 NOT NULL,
    CONSTRAINT offline_admission_pk PRIMARY KEY (admission_id),
    CONSTRAINT offline_admission_uq1 UNIQUE (binding_id,attempt_id,generation,execution_id,instance_id,credential_id,credential_revision,grant_id,grant_revision,permission),
    CONSTRAINT offline_admission_ck1 CHECK (
        (durable_state = 'ISSUED'
        AND consumed_decision_id IS NULL
        AND consumed_at IS NULL)
        OR (durable_state = 'CONSUMED'
        AND consumed_decision_id IS NOT NULL
        AND consumed_at IS NOT NULL)
    ),
    CONSTRAINT offline_admission_ck2 CHECK (
        admission_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid AND
        deployment_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid AND
        incarnation_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid AND
        binding_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid AND
        attempt_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid AND
        execution_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid AND
        instance_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid AND
        credential_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid AND
        principal_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid AND
        organization_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid AND
        grant_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid AND
        (consumed_decision_id IS NULL
        OR consumed_decision_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid)
        AND generation > 0
        AND executor_oid BETWEEN 1
        AND 4294967295
        AND credential_revision > 0
        AND grant_revision > 0
        AND lock_token = 0
        AND pg_catalog.octet_length(authorization_fingerprint) = 32
        AND permission = 'TRANSACTION_IDENTITY_DECISION_WRITE'
    ),
    CONSTRAINT offline_admission_ck3 CHECK (
        pg_catalog.isfinite(authenticated_at)
        AND pg_catalog.isfinite(expires_at)
        AND authenticated_at < expires_at
        AND (consumed_at IS NULL
        OR (pg_catalog.isfinite(consumed_at)
        AND authenticated_at <= consumed_at
        AND consumed_at < expires_at))
    )
);

-- T08; SPEC 21.7 / approved G1-G2 structural design.
-- BOOKKEEPING/AUDIT. Exact successful-stage receipts only, append-only to operational owners. No receipt proves canonical authority on its own.
CREATE TABLE public.offline_stage_receipt (
    binding_id pg_catalog.uuid NOT NULL,
    attempt_id pg_catalog.uuid NOT NULL,
    generation pg_catalog.int8 NOT NULL,
    execution_id pg_catalog.uuid NOT NULL,
    instance_id pg_catalog.uuid NOT NULL,
    stage pg_catalog.text NOT NULL,
    receipt_id pg_catalog.uuid NOT NULL,
    operation_id pg_catalog.uuid NULL,
    frozen_receipt pg_catalog.bytea NOT NULL,
    effect_time pg_catalog.timestamptz NOT NULL,
    CONSTRAINT offline_stage_receipt_pk PRIMARY KEY (binding_id,attempt_id,generation,stage),
    CONSTRAINT offline_stage_receipt_uq1 UNIQUE (receipt_id),
    CONSTRAINT offline_stage_receipt_ck1 CHECK (
        binding_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid AND
        attempt_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid AND
        execution_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid AND
        instance_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid AND
        receipt_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid AND
        (operation_id IS NULL
        OR operation_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid)
        AND generation > 0
        AND stage IN ('ATTESTATION_VERIFIED','PRINCIPAL_APPLIED','INITIAL_CREDENTIAL_APPLIED','GRANT_APPLIED','IDENTITY_DECISION_APPLIED')
    ),
    CONSTRAINT offline_stage_receipt_ck2 CHECK (
        pg_catalog.octet_length(frozen_receipt) > 0
        AND pg_catalog.isfinite(effect_time)
        AND ((stage IN ('ATTESTATION_VERIFIED','IDENTITY_DECISION_APPLIED')
        AND operation_id IS NULL)
        OR (stage IN ('PRINCIPAL_APPLIED','INITIAL_CREDENTIAL_APPLIED','GRANT_APPLIED')
        AND operation_id IS NOT NULL))
    )
);

-- T09; SPEC 21.7 / approved G1-G2 structural design.
-- OPERATIONAL_STATE/AUDIT. E records REQUIRED only with decision. ADMIN independently recomputes evidence; auditor does not write this table.
CREATE TABLE public.offline_reconciliation (
    binding_id pg_catalog.uuid NOT NULL,
    state pg_catalog.text NOT NULL,
    evidence_digest pg_catalog.bytea NULL,
    recorded_at pg_catalog.timestamptz NULL,
    CONSTRAINT offline_reconciliation_pk PRIMARY KEY (binding_id),
    CONSTRAINT offline_reconciliation_ck1 CHECK (
        binding_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid
        AND state IN ('NOT_STARTED','REQUIRED','IN_PROGRESS','RECONCILED','MISMATCH','INDETERMINATE')
        AND (evidence_digest IS NULL
        OR (pg_catalog.octet_length(evidence_digest) = 32
        AND recorded_at IS NOT NULL))
        AND (recorded_at IS NULL
        OR pg_catalog.isfinite(recorded_at))
        AND (state NOT IN ('RECONCILED','MISMATCH','INDETERMINATE')
        OR (evidence_digest IS NOT NULL
        AND recorded_at IS NOT NULL))
    )
);

-- T10; SPEC 21.7 / approved G1-G2 structural design.
-- OPERATIONAL_STATE/AUDIT. ADMIN records terminal result from independent evidence. No operational writes and no rewriting historical terminal outcomes.
CREATE TABLE public.offline_ceremony_result (
    binding_id pg_catalog.uuid NOT NULL,
    result pg_catalog.text NOT NULL,
    evidence_digest pg_catalog.bytea NULL,
    recorded_at pg_catalog.timestamptz NULL,
    CONSTRAINT offline_ceremony_result_pk PRIMARY KEY (binding_id),
    CONSTRAINT offline_ceremony_result_ck1 CHECK (
        binding_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid
        AND ((result = 'NONE'
        AND evidence_digest IS NULL
        AND recorded_at IS NULL)
        OR (result IN ('SUCCESS','FAILURE','MANUAL_REVIEW')
        AND evidence_digest IS NOT NULL
        AND pg_catalog.octet_length(evidence_digest) = 32
        AND recorded_at IS NOT NULL
        AND pg_catalog.isfinite(recorded_at)))
    )
);

-- T11; SPEC 21.7 / approved G1-G2 structural design.
-- FENCE/OPERATIONAL_STATE. READY alone is insufficient: approved live history/ACL/policy/host/watchdog/key checks remain mandatory. No operational writes.
CREATE TABLE public.offline_readiness (
    deployment_id pg_catalog.uuid NOT NULL,
    incarnation_id pg_catalog.uuid NOT NULL,
    state pg_catalog.text NOT NULL,
    active_key_version pg_catalog.int8 NOT NULL,
    policy_version pg_catalog.text NOT NULL,
    policy_digest pg_catalog.bytea NOT NULL,
    history_manifest pg_catalog.bytea NOT NULL,
    acl_manifest pg_catalog.bytea NOT NULL,
    watchdog_checked_at pg_catalog.timestamptz NOT NULL,
    watchdog_healthy pg_catalog.bool NOT NULL,
    CONSTRAINT offline_readiness_pk PRIMARY KEY (incarnation_id),
    CONSTRAINT offline_readiness_ck1 CHECK (
        deployment_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid AND
        incarnation_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid AND state IN ('NOT_READY','READY') AND active_key_version BETWEEN 1 AND 4294967295
    ),
    CONSTRAINT offline_readiness_ck2 CHECK (
        (policy_version <> ''
        AND policy_version IS NFC NORMALIZED
        AND policy_version !~ '[[:cntrl:]]')
        AND pg_catalog.octet_length(policy_digest) = 32
        AND pg_catalog.octet_length(history_manifest) > 0
        AND pg_catalog.octet_length(acl_manifest) > 0
        AND pg_catalog.isfinite(watchdog_checked_at)
    )
);

-- T12; SPEC 21.7 / approved G1-G2 structural design.
-- FENCE. ADMIN governs lineage/version/no-reuse and purge; Q reads five exact fields, never fingerprint tombstones. Local shape checks do not prove cryptographic provenance.
CREATE TABLE public.offline_preflight_key (
    incarnation_id pg_catalog.uuid NOT NULL,
    lineage_id pg_catalog.uuid NOT NULL,
    key_version pg_catalog.int8 NOT NULL,
    key_state pg_catalog.text NOT NULL,
    key_material pg_catalog.bytea NULL,
    key_material_fingerprint pg_catalog.bytea NOT NULL,
    CONSTRAINT offline_preflight_key_pk PRIMARY KEY (incarnation_id,lineage_id,key_version),
    CONSTRAINT offline_preflight_key_uq1 UNIQUE (incarnation_id,key_version),
    CONSTRAINT offline_preflight_key_ck1 CHECK (
        incarnation_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid AND
        lineage_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid AND key_version BETWEEN 1 AND 4294967295
    ),
    CONSTRAINT offline_preflight_key_ck2 CHECK (
        (key_state = 'ACTIVE' AND key_material IS NOT NULL AND pg_catalog.octet_length(key_material) = 32) OR (key_state = 'RETIRED' AND key_material IS NULL)
    ),
    CONSTRAINT offline_preflight_key_ck3 CHECK (
        pg_catalog.octet_length(key_material_fingerprint) = 32
    )
);

-- T13; SPEC 21.7 / approved G1-G2 structural design.
-- FENCE. Immutable policy versions; no operational INSERT/UPDATE or seeded values.
-- Full 29-tag numeric/maxima validation remains future activation/readiness logic.
CREATE TABLE public.offline_deadline_policy (
    policy_version pg_catalog.text NOT NULL,
    policy_digest pg_catalog.bytea NOT NULL,
    canonical_policy pg_catalog.bytea NOT NULL,
    effective_from pg_catalog.timestamptz(6) NOT NULL,
    CONSTRAINT offline_deadline_policy_pk PRIMARY KEY (policy_version),
    CONSTRAINT offline_deadline_policy_ck1 CHECK (
        (policy_version <> '' AND policy_version IS NFC NORMALIZED AND policy_version !~ '[[:cntrl:]]')
    ),
    CONSTRAINT offline_deadline_policy_ck2 CHECK (
        pg_catalog.octet_length(policy_digest) = 32 AND pg_catalog.octet_length(canonical_policy) > 0 AND policy_digest = pg_catalog.sha256(canonical_policy)
    ),
    CONSTRAINT offline_deadline_policy_ck3 CHECK (
        pg_catalog.isfinite(effective_from)
    )
);

-- T14; SPEC 21.7 / approved G1-G2 structural design.
-- AUDIT. Administrative append-only multiset; no artificial identity or operational privileges. No automatic purge of binding/identity/key tombstones.
CREATE TABLE public.offline_diagnostic_evidence (
    binding_id pg_catalog.uuid NOT NULL,
    attempt_id pg_catalog.uuid NULL,
    generation pg_catalog.int8 NOT NULL,
    snapshot_digest pg_catalog.bytea NOT NULL,
    classification pg_catalog.text NOT NULL,
    recorded_at pg_catalog.timestamptz NOT NULL,
    recorder_identity pg_catalog.text NOT NULL,
    CONSTRAINT offline_diagnostic_evidence_ck1 CHECK (
        binding_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid AND
        (attempt_id IS NULL OR attempt_id <> '00000000-0000-0000-0000-000000000000'::pg_catalog.uuid) AND generation > 0 AND pg_catalog.octet_length(snapshot_digest) = 32
    ),
    CONSTRAINT offline_diagnostic_evidence_ck2 CHECK (
        (classification <> ''
        AND classification IS NFC NORMALIZED
        AND classification !~ '[[:cntrl:]]')
        AND (recorder_identity <> ''
        AND recorder_identity IS NFC NORMALIZED
        AND recorder_identity !~ '[[:cntrl:]]')
        AND pg_catalog.isfinite(recorded_at)
    )
);

-- 17 foreign keys; only provisioning cycles/current-pointer initialization defer.
ALTER TABLE public.offline_binding_header
    ADD CONSTRAINT offline_binding_header_fk1 FOREIGN KEY (deployment_incarnation_id)
    REFERENCES public.offline_readiness (incarnation_id)
    ON UPDATE NO ACTION ON DELETE NO ACTION
    NOT DEFERRABLE;
ALTER TABLE public.offline_binding_header
    ADD CONSTRAINT offline_binding_header_fk2 FOREIGN KEY (deadline_policy_version)
    REFERENCES public.offline_deadline_policy (policy_version)
    ON UPDATE NO ACTION ON DELETE NO ACTION
    NOT DEFERRABLE;
ALTER TABLE public.offline_binding_lifecycle
    ADD CONSTRAINT offline_binding_lifecycle_fk1 FOREIGN KEY (binding_id)
    REFERENCES public.offline_binding_header (binding_id)
    ON UPDATE NO ACTION ON DELETE NO ACTION
    NOT DEFERRABLE;
ALTER TABLE public.offline_attempt_pointer
    ADD CONSTRAINT offline_attempt_pointer_fk1 FOREIGN KEY (binding_id)
    REFERENCES public.offline_binding_header (binding_id)
    ON UPDATE NO ACTION ON DELETE NO ACTION
    NOT DEFERRABLE;
ALTER TABLE public.offline_attempt_pointer
    ADD CONSTRAINT offline_attempt_pointer_fk2 FOREIGN KEY (binding_id,current_attempt_id)
    REFERENCES public.offline_attempt (binding_id,attempt_id)
    ON UPDATE NO ACTION ON DELETE NO ACTION
    DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE public.offline_attempt
    ADD CONSTRAINT offline_attempt_fk1 FOREIGN KEY (binding_id)
    REFERENCES public.offline_binding_header (binding_id)
    ON UPDATE NO ACTION ON DELETE NO ACTION
    NOT DEFERRABLE;
ALTER TABLE public.offline_execution
    ADD CONSTRAINT offline_execution_fk1 FOREIGN KEY (binding_id,attempt_id)
    REFERENCES public.offline_attempt (binding_id,attempt_id)
    ON UPDATE NO ACTION ON DELETE NO ACTION
    NOT DEFERRABLE;
ALTER TABLE public.offline_delivery
    ADD CONSTRAINT offline_delivery_fk1 FOREIGN KEY (binding_id)
    REFERENCES public.offline_binding_header (binding_id)
    ON UPDATE NO ACTION ON DELETE NO ACTION
    NOT DEFERRABLE;
ALTER TABLE public.offline_delivery
    ADD CONSTRAINT offline_delivery_fk2 FOREIGN KEY (binding_id,attempt_id,generation)
    REFERENCES public.offline_execution (binding_id,attempt_id,generation)
    ON UPDATE NO ACTION ON DELETE NO ACTION
    NOT DEFERRABLE;
ALTER TABLE public.offline_admission
    ADD CONSTRAINT offline_admission_fk1 FOREIGN KEY (binding_id,attempt_id,generation)
    REFERENCES public.offline_execution (binding_id,attempt_id,generation)
    ON UPDATE NO ACTION ON DELETE NO ACTION
    NOT DEFERRABLE;
ALTER TABLE public.offline_stage_receipt
    ADD CONSTRAINT offline_stage_receipt_fk1 FOREIGN KEY (binding_id,attempt_id,generation)
    REFERENCES public.offline_execution (binding_id,attempt_id,generation)
    ON UPDATE NO ACTION ON DELETE NO ACTION
    NOT DEFERRABLE;
ALTER TABLE public.offline_reconciliation
    ADD CONSTRAINT offline_reconciliation_fk1 FOREIGN KEY (binding_id)
    REFERENCES public.offline_binding_header (binding_id)
    ON UPDATE NO ACTION ON DELETE NO ACTION
    NOT DEFERRABLE;
ALTER TABLE public.offline_ceremony_result
    ADD CONSTRAINT offline_ceremony_result_fk1 FOREIGN KEY (binding_id)
    REFERENCES public.offline_binding_header (binding_id)
    ON UPDATE NO ACTION ON DELETE NO ACTION
    NOT DEFERRABLE;
ALTER TABLE public.offline_readiness
    ADD CONSTRAINT offline_readiness_fk1 FOREIGN KEY (policy_version)
    REFERENCES public.offline_deadline_policy (policy_version)
    ON UPDATE NO ACTION ON DELETE NO ACTION
    NOT DEFERRABLE;
ALTER TABLE public.offline_readiness
    ADD CONSTRAINT offline_readiness_fk2 FOREIGN KEY (incarnation_id,active_key_version)
    REFERENCES public.offline_preflight_key (incarnation_id,key_version)
    ON UPDATE NO ACTION ON DELETE NO ACTION
    DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE public.offline_preflight_key
    ADD CONSTRAINT offline_preflight_key_fk1 FOREIGN KEY (incarnation_id)
    REFERENCES public.offline_readiness (incarnation_id)
    ON UPDATE NO ACTION ON DELETE NO ACTION
    DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE public.offline_diagnostic_evidence
    ADD CONSTRAINT offline_diagnostic_evidence_fk1 FOREIGN KEY (binding_id)
    REFERENCES public.offline_binding_header (binding_id)
    ON UPDATE NO ACTION ON DELETE NO ACTION
    NOT DEFERRABLE;

-- 20 indexes are supplied by the 13 PK and 7 UNIQUE constraints.
-- Exactly three additional indexes follow; no performance index expansion.
CREATE UNIQUE INDEX offline_readiness_ready_deployment_uix
    ON public.offline_readiness (deployment_id) WHERE state = 'READY';
CREATE UNIQUE INDEX offline_preflight_key_active_incarnation_uix
    ON public.offline_preflight_key (incarnation_id) WHERE key_state = 'ACTIVE';
CREATE INDEX offline_diagnostic_evidence_binding_generation_time_ix
    ON public.offline_diagnostic_evidence (binding_id,generation,recorded_at);

-- ADMIN owns all 14 controls; V/I/E/A/P/Q/Z own no tables.
ALTER TABLE public.offline_binding_header OWNER TO flooow_offline_control_owner;
ALTER TABLE public.offline_binding_lifecycle OWNER TO flooow_offline_control_owner;
ALTER TABLE public.offline_attempt_pointer OWNER TO flooow_offline_control_owner;
ALTER TABLE public.offline_attempt OWNER TO flooow_offline_control_owner;
ALTER TABLE public.offline_execution OWNER TO flooow_offline_control_owner;
ALTER TABLE public.offline_delivery OWNER TO flooow_offline_control_owner;
ALTER TABLE public.offline_admission OWNER TO flooow_offline_control_owner;
ALTER TABLE public.offline_stage_receipt OWNER TO flooow_offline_control_owner;
ALTER TABLE public.offline_reconciliation OWNER TO flooow_offline_control_owner;
ALTER TABLE public.offline_ceremony_result OWNER TO flooow_offline_control_owner;
ALTER TABLE public.offline_readiness OWNER TO flooow_offline_control_owner;
ALTER TABLE public.offline_preflight_key OWNER TO flooow_offline_control_owner;
ALTER TABLE public.offline_deadline_policy OWNER TO flooow_offline_control_owner;
ALTER TABLE public.offline_diagnostic_evidence OWNER TO flooow_offline_control_owner;

-- Clear PUBLIC/protected-owner ACLs inherited from creator defaults on NEW controls only.
-- No global default ACL or schema is changed; exact column grants follow.
-- Unapproved third-party/default paths remain a mandatory later effective-ACL gate.
REVOKE ALL PRIVILEGES ON TABLE public.offline_binding_header FROM PUBLIC,flooow_offline_verification_owner,flooow_offline_issuance_owner,flooow_offline_execution_owner,flooow_offline_audit_owner,flooow_offline_principal_lock_owner,flooow_offline_readiness_owner,flooow_offline_intent_audit_owner;
REVOKE ALL PRIVILEGES ON TABLE public.offline_binding_lifecycle FROM PUBLIC,flooow_offline_verification_owner,flooow_offline_issuance_owner,flooow_offline_execution_owner,flooow_offline_audit_owner,flooow_offline_principal_lock_owner,flooow_offline_readiness_owner,flooow_offline_intent_audit_owner;
REVOKE ALL PRIVILEGES ON TABLE public.offline_attempt_pointer FROM PUBLIC,flooow_offline_verification_owner,flooow_offline_issuance_owner,flooow_offline_execution_owner,flooow_offline_audit_owner,flooow_offline_principal_lock_owner,flooow_offline_readiness_owner,flooow_offline_intent_audit_owner;
REVOKE ALL PRIVILEGES ON TABLE public.offline_attempt FROM PUBLIC,flooow_offline_verification_owner,flooow_offline_issuance_owner,flooow_offline_execution_owner,flooow_offline_audit_owner,flooow_offline_principal_lock_owner,flooow_offline_readiness_owner,flooow_offline_intent_audit_owner;
REVOKE ALL PRIVILEGES ON TABLE public.offline_execution FROM PUBLIC,flooow_offline_verification_owner,flooow_offline_issuance_owner,flooow_offline_execution_owner,flooow_offline_audit_owner,flooow_offline_principal_lock_owner,flooow_offline_readiness_owner,flooow_offline_intent_audit_owner;
REVOKE ALL PRIVILEGES ON TABLE public.offline_delivery FROM PUBLIC,flooow_offline_verification_owner,flooow_offline_issuance_owner,flooow_offline_execution_owner,flooow_offline_audit_owner,flooow_offline_principal_lock_owner,flooow_offline_readiness_owner,flooow_offline_intent_audit_owner;
REVOKE ALL PRIVILEGES ON TABLE public.offline_admission FROM PUBLIC,flooow_offline_verification_owner,flooow_offline_issuance_owner,flooow_offline_execution_owner,flooow_offline_audit_owner,flooow_offline_principal_lock_owner,flooow_offline_readiness_owner,flooow_offline_intent_audit_owner;
REVOKE ALL PRIVILEGES ON TABLE public.offline_stage_receipt FROM PUBLIC,flooow_offline_verification_owner,flooow_offline_issuance_owner,flooow_offline_execution_owner,flooow_offline_audit_owner,flooow_offline_principal_lock_owner,flooow_offline_readiness_owner,flooow_offline_intent_audit_owner;
REVOKE ALL PRIVILEGES ON TABLE public.offline_reconciliation FROM PUBLIC,flooow_offline_verification_owner,flooow_offline_issuance_owner,flooow_offline_execution_owner,flooow_offline_audit_owner,flooow_offline_principal_lock_owner,flooow_offline_readiness_owner,flooow_offline_intent_audit_owner;
REVOKE ALL PRIVILEGES ON TABLE public.offline_ceremony_result FROM PUBLIC,flooow_offline_verification_owner,flooow_offline_issuance_owner,flooow_offline_execution_owner,flooow_offline_audit_owner,flooow_offline_principal_lock_owner,flooow_offline_readiness_owner,flooow_offline_intent_audit_owner;
REVOKE ALL PRIVILEGES ON TABLE public.offline_readiness FROM PUBLIC,flooow_offline_verification_owner,flooow_offline_issuance_owner,flooow_offline_execution_owner,flooow_offline_audit_owner,flooow_offline_principal_lock_owner,flooow_offline_readiness_owner,flooow_offline_intent_audit_owner;
REVOKE ALL PRIVILEGES ON TABLE public.offline_preflight_key FROM PUBLIC,flooow_offline_verification_owner,flooow_offline_issuance_owner,flooow_offline_execution_owner,flooow_offline_audit_owner,flooow_offline_principal_lock_owner,flooow_offline_readiness_owner,flooow_offline_intent_audit_owner;
REVOKE ALL PRIVILEGES ON TABLE public.offline_deadline_policy FROM PUBLIC,flooow_offline_verification_owner,flooow_offline_issuance_owner,flooow_offline_execution_owner,flooow_offline_audit_owner,flooow_offline_principal_lock_owner,flooow_offline_readiness_owner,flooow_offline_intent_audit_owner;
REVOKE ALL PRIVILEGES ON TABLE public.offline_diagnostic_evidence FROM PUBLIC,flooow_offline_verification_owner,flooow_offline_issuance_owner,flooow_offline_execution_owner,flooow_offline_audit_owner,flooow_offline_principal_lock_owner,flooow_offline_readiness_owner,flooow_offline_intent_audit_owner;

-- SPEC 22.4 is the sole column ACL manifest: 1013 records, no table-level grant.
-- Each SQL record carries the frozen source line, class, consumer and entrypoint.
-- LOCK is SQL UPDATE, constrained by future reviewed bodies; it is not a PG privilege kind.
-- No CONNECT/USAGE/EXECUTE, service grants or grant options are authored in G3A.
-- SPEC:918 E READ_PRIVILEGE; consumer=AU/AF; entrypoint=S16-S18; transitive=NONE.
-- Required: Actor scope and invoker grant-fingerprint principal join
GRANT SELECT (organization_id) ON TABLE public.command_principal TO flooow_offline_execution_owner;
-- SPEC:919 E READ_PRIVILEGE; consumer=AU/AF; entrypoint=S16-S18; transitive=NONE.
-- Required: Actor scope and invoker grant-fingerprint principal join
GRANT SELECT (principal_id) ON TABLE public.command_principal TO flooow_offline_execution_owner;
-- SPEC:920 E READ_PRIVILEGE; consumer=AU/AF; entrypoint=S16-S18; transitive=NONE.
-- Required: Actor scope and invoker grant-fingerprint principal join
GRANT SELECT (mercado_livre_connection_id) ON TABLE public.command_principal TO flooow_offline_execution_owner;
-- SPEC:921 E READ_PRIVILEGE; consumer=AU/AF; entrypoint=S16-S18; transitive=NONE.
-- Required: Actor scope and invoker grant-fingerprint principal join
GRANT SELECT (omie_connection_id) ON TABLE public.command_principal TO flooow_offline_execution_owner;
-- SPEC:922 E READ_PRIVILEGE; consumer=AU; entrypoint=S16-S18; transitive=NONE.
-- Required: Latest exact credential revision/enabled/currentness
GRANT SELECT (organization_id) ON TABLE public.command_credential_revision TO flooow_offline_execution_owner;
-- SPEC:923 E READ_PRIVILEGE; consumer=AU; entrypoint=S16-S18; transitive=NONE.
-- Required: Latest exact credential revision/enabled/currentness
GRANT SELECT (principal_id) ON TABLE public.command_credential_revision TO flooow_offline_execution_owner;
-- SPEC:924 E READ_PRIVILEGE; consumer=AU; entrypoint=S16-S18; transitive=NONE.
-- Required: Latest exact credential revision/enabled/currentness
GRANT SELECT (credential_id) ON TABLE public.command_credential_revision TO flooow_offline_execution_owner;
-- SPEC:925 E READ_PRIVILEGE; consumer=AU; entrypoint=S16-S18; transitive=NONE.
-- Required: Latest exact credential revision/enabled/currentness
GRANT SELECT (revision) ON TABLE public.command_credential_revision TO flooow_offline_execution_owner;
-- SPEC:926 E READ_PRIVILEGE; consumer=AU; entrypoint=S16-S18; transitive=NONE.
-- Required: Latest exact credential revision/enabled/currentness
GRANT SELECT (state) ON TABLE public.command_credential_revision TO flooow_offline_execution_owner;
-- SPEC:927 E READ_PRIVILEGE; consumer=AU.authenticate; entrypoint=S16; transitive=NONE.
-- Required: Private derived-proof verification; never returned
GRANT SELECT (secret_verifier) ON TABLE public.command_credential_revision TO flooow_offline_execution_owner;
-- SPEC:928 E READ_PRIVILEGE; consumer=AU/AF; entrypoint=S16-S18; transitive=NONE.
-- Required: Latest permission/grant ordering and every frozen authorization-hash input
GRANT SELECT (organization_id) ON TABLE public.command_permission_grant TO flooow_offline_execution_owner;
-- SPEC:929 E READ_PRIVILEGE; consumer=AU/AF; entrypoint=S16-S18; transitive=NONE.
-- Required: Latest permission/grant ordering and every frozen authorization-hash input
GRANT SELECT (principal_id) ON TABLE public.command_permission_grant TO flooow_offline_execution_owner;
-- SPEC:930 E READ_PRIVILEGE; consumer=AU/AF; entrypoint=S16-S18; transitive=NONE.
-- Required: Latest permission/grant ordering and every frozen authorization-hash input
GRANT SELECT (grant_id) ON TABLE public.command_permission_grant TO flooow_offline_execution_owner;
-- SPEC:931 E READ_PRIVILEGE; consumer=AU/AF; entrypoint=S16-S18; transitive=NONE.
-- Required: Latest permission/grant ordering and every frozen authorization-hash input
GRANT SELECT (permission) ON TABLE public.command_permission_grant TO flooow_offline_execution_owner;
-- SPEC:932 E READ_PRIVILEGE; consumer=AU/AF; entrypoint=S16-S18; transitive=NONE.
-- Required: Latest permission/grant ordering and every frozen authorization-hash input
GRANT SELECT (state) ON TABLE public.command_permission_grant TO flooow_offline_execution_owner;
-- SPEC:933 E READ_PRIVILEGE; consumer=AU/AF; entrypoint=S16-S18; transitive=NONE.
-- Required: Latest permission/grant ordering and every frozen authorization-hash input
GRANT SELECT (revision) ON TABLE public.command_permission_grant TO flooow_offline_execution_owner;
-- SPEC:934 E READ_PRIVILEGE; consumer=AU/AF; entrypoint=S16-S18; transitive=NONE.
-- Required: Latest permission/grant ordering and every frozen authorization-hash input
GRANT SELECT (supersedes_grant_id) ON TABLE public.command_permission_grant TO flooow_offline_execution_owner;
-- SPEC:935 E READ_PRIVILEGE; consumer=AU/AF; entrypoint=S16-S18; transitive=NONE.
-- Required: Latest permission/grant ordering and every frozen authorization-hash input
GRANT SELECT (reason) ON TABLE public.command_permission_grant TO flooow_offline_execution_owner;
-- SPEC:936 E READ_PRIVILEGE; consumer=AU/AF; entrypoint=S16-S18; transitive=NONE.
-- Required: Latest permission/grant ordering and every frozen authorization-hash input
GRANT SELECT (provenance) ON TABLE public.command_permission_grant TO flooow_offline_execution_owner;
-- SPEC:937 E READ_PRIVILEGE; consumer=AU/AF; entrypoint=S16-S18; transitive=NONE.
-- Required: Latest permission/grant ordering and every frozen authorization-hash input
GRANT SELECT (correlation_id) ON TABLE public.command_permission_grant TO flooow_offline_execution_owner;
-- SPEC:938 E READ_PRIVILEGE; consumer=AU/AF; entrypoint=S16-S18; transitive=NONE.
-- Required: Latest permission/grant ordering and every frozen authorization-hash input
GRANT SELECT (decided_at) ON TABLE public.command_permission_grant TO flooow_offline_execution_owner;
-- SPEC:939 E READ_PRIVILEGE; consumer=AU; entrypoint=S16-S18; transitive=NONE.
-- Required: Exact organization ACTIVE predicate
GRANT SELECT (organization_id) ON TABLE public.integration_organization TO flooow_offline_execution_owner;
-- SPEC:940 E READ_PRIVILEGE; consumer=AU; entrypoint=S16-S18; transitive=NONE.
-- Required: Exact organization ACTIVE predicate
GRANT SELECT (status) ON TABLE public.integration_organization TO flooow_offline_execution_owner;
-- SPEC:941 E READ_PRIVILEGE; consumer=OE; entrypoint=S17-S18; transitive=NONE.
-- Required: Exact V3 progress scope and input_progress<progress_version fence
GRANT SELECT (organization_id) ON TABLE public.integration_connector_progress TO flooow_offline_execution_owner;
-- SPEC:942 E READ_PRIVILEGE; consumer=OE; entrypoint=S17-S18; transitive=NONE.
-- Required: Exact V3 progress scope and input_progress<progress_version fence
GRANT SELECT (connection_id) ON TABLE public.integration_connector_progress TO flooow_offline_execution_owner;
-- SPEC:943 E READ_PRIVILEGE; consumer=OE; entrypoint=S17-S18; transitive=NONE.
-- Required: Exact V3 progress scope and input_progress<progress_version fence
GRANT SELECT (capability) ON TABLE public.integration_connector_progress TO flooow_offline_execution_owner;
-- SPEC:944 E READ_PRIVILEGE; consumer=OE; entrypoint=S17-S18; transitive=NONE.
-- Required: Exact V3 progress scope and input_progress<progress_version fence
GRANT SELECT (progress_version) ON TABLE public.integration_connector_progress TO flooow_offline_execution_owner;
-- SPEC:945 E READ_PRIVILEGE; consumer=OE; entrypoint=S17-S18; transitive=NONE.
-- Required: Page join/cardinality and ordinal bound
GRANT SELECT (organization_id) ON TABLE public.integration_connector_page_commit TO flooow_offline_execution_owner;
-- SPEC:946 E READ_PRIVILEGE; consumer=OE; entrypoint=S17-S18; transitive=NONE.
-- Required: Page join/cardinality and ordinal bound
GRANT SELECT (connection_id) ON TABLE public.integration_connector_page_commit TO flooow_offline_execution_owner;
-- SPEC:947 E READ_PRIVILEGE; consumer=OE; entrypoint=S17-S18; transitive=NONE.
-- Required: Page join/cardinality and ordinal bound
GRANT SELECT (capability) ON TABLE public.integration_connector_page_commit TO flooow_offline_execution_owner;
-- SPEC:948 E READ_PRIVILEGE; consumer=OE; entrypoint=S17-S18; transitive=NONE.
-- Required: Page join/cardinality and ordinal bound
GRANT SELECT (input_progress_version) ON TABLE public.integration_connector_page_commit TO flooow_offline_execution_owner;
-- SPEC:949 E READ_PRIVILEGE; consumer=OE; entrypoint=S17-S18; transitive=NONE.
-- Required: Page join/cardinality and ordinal bound
GRANT SELECT (record_count) ON TABLE public.integration_connector_page_commit TO flooow_offline_execution_owner;
-- SPEC:950 E READ_PRIVILEGE; consumer=TL; entrypoint=S17-S18; transitive=NONE.
-- Required: Exact source join and registry external/currency equality
GRANT SELECT (organization_id) ON TABLE public.integration_mercado_livre_order_source_observation TO flooow_offline_execution_owner;
-- SPEC:951 E READ_PRIVILEGE; consumer=TL; entrypoint=S17-S18; transitive=NONE.
-- Required: Exact source join and registry external/currency equality
GRANT SELECT (connection_id) ON TABLE public.integration_mercado_livre_order_source_observation TO flooow_offline_execution_owner;
-- SPEC:952 E READ_PRIVILEGE; consumer=TL; entrypoint=S17-S18; transitive=NONE.
-- Required: Exact source join and registry external/currency equality
GRANT SELECT (capability) ON TABLE public.integration_mercado_livre_order_source_observation TO flooow_offline_execution_owner;
-- SPEC:953 E READ_PRIVILEGE; consumer=TL; entrypoint=S17-S18; transitive=NONE.
-- Required: Exact source join and registry external/currency equality
GRANT SELECT (input_progress_version) ON TABLE public.integration_mercado_livre_order_source_observation TO flooow_offline_execution_owner;
-- SPEC:954 E READ_PRIVILEGE; consumer=TL; entrypoint=S17-S18; transitive=NONE.
-- Required: Exact source join and registry external/currency equality
GRANT SELECT (record_ordinal) ON TABLE public.integration_mercado_livre_order_source_observation TO flooow_offline_execution_owner;
-- SPEC:955 E READ_PRIVILEGE; consumer=TL; entrypoint=S17-S18; transitive=NONE.
-- Required: Exact source join and registry external/currency equality
GRANT SELECT (external_order_ref) ON TABLE public.integration_mercado_livre_order_source_observation TO flooow_offline_execution_owner;
-- SPEC:956 E READ_PRIVILEGE; consumer=TL; entrypoint=S17-S18; transitive=NONE.
-- Required: Exact source join and registry external/currency equality
GRANT SELECT (currency) ON TABLE public.integration_mercado_livre_order_source_observation TO flooow_offline_execution_owner;
-- SPEC:957 E READ_PRIVILEGE; consumer=OE; entrypoint=S17-S18; transitive=NONE.
-- Required: Base page counts/source scope and selected integration/currency conflict check
GRANT SELECT (organization_id) ON TABLE public.integration_omie_transaction_evidence TO flooow_offline_execution_owner;
-- SPEC:958 E READ_PRIVILEGE; consumer=OE; entrypoint=S17-S18; transitive=NONE.
-- Required: Base page counts/source scope and selected integration/currency conflict check
GRANT SELECT (connection_id) ON TABLE public.integration_omie_transaction_evidence TO flooow_offline_execution_owner;
-- SPEC:959 E READ_PRIVILEGE; consumer=OE; entrypoint=S17-S18; transitive=NONE.
-- Required: Base page counts/source scope and selected integration/currency conflict check
GRANT SELECT (capability) ON TABLE public.integration_omie_transaction_evidence TO flooow_offline_execution_owner;
-- SPEC:960 E READ_PRIVILEGE; consumer=OE; entrypoint=S17-S18; transitive=NONE.
-- Required: Base page counts/source scope and selected integration/currency conflict check
GRANT SELECT (input_progress_version) ON TABLE public.integration_omie_transaction_evidence TO flooow_offline_execution_owner;
-- SPEC:961 E READ_PRIVILEGE; consumer=OE; entrypoint=S17-S18; transitive=NONE.
-- Required: Base page counts/source scope and selected integration/currency conflict check
GRANT SELECT (record_ordinal) ON TABLE public.integration_omie_transaction_evidence TO flooow_offline_execution_owner;
-- SPEC:962 E READ_PRIVILEGE; consumer=OE; entrypoint=S17-S18; transitive=NONE.
-- Required: Base page counts/source scope and selected integration/currency conflict check
GRANT SELECT (source_order_ref) ON TABLE public.integration_omie_transaction_evidence TO flooow_offline_execution_owner;
-- SPEC:963 E READ_PRIVILEGE; consumer=OE; entrypoint=S17-S18; transitive=NONE.
-- Required: Base page counts/source scope and selected integration/currency conflict check
GRANT SELECT (source_integration_ref) ON TABLE public.integration_omie_transaction_evidence TO flooow_offline_execution_owner;
-- SPEC:964 E READ_PRIVILEGE; consumer=OE; entrypoint=S17-S18; transitive=NONE.
-- Required: Base page counts/source scope and selected integration/currency conflict check
GRANT SELECT (currency) ON TABLE public.integration_omie_transaction_evidence TO flooow_offline_execution_owner;
-- SPEC:965 E READ_PRIVILEGE; consumer=OE; entrypoint=S17-S18; transitive=NONE.
-- Required: V3 counts/version/civil currentness and selected semantic fingerprint
GRANT SELECT (organization_id) ON TABLE public.integration_omie_transaction_evidence_v3 TO flooow_offline_execution_owner;
-- SPEC:966 E READ_PRIVILEGE; consumer=OE; entrypoint=S17-S18; transitive=NONE.
-- Required: V3 counts/version/civil currentness and selected semantic fingerprint
GRANT SELECT (connection_id) ON TABLE public.integration_omie_transaction_evidence_v3 TO flooow_offline_execution_owner;
-- SPEC:967 E READ_PRIVILEGE; consumer=OE; entrypoint=S17-S18; transitive=NONE.
-- Required: V3 counts/version/civil currentness and selected semantic fingerprint
GRANT SELECT (capability) ON TABLE public.integration_omie_transaction_evidence_v3 TO flooow_offline_execution_owner;
-- SPEC:968 E READ_PRIVILEGE; consumer=OE; entrypoint=S17-S18; transitive=NONE.
-- Required: V3 counts/version/civil currentness and selected semantic fingerprint
GRANT SELECT (input_progress_version) ON TABLE public.integration_omie_transaction_evidence_v3 TO flooow_offline_execution_owner;
-- SPEC:969 E READ_PRIVILEGE; consumer=OE; entrypoint=S17-S18; transitive=NONE.
-- Required: V3 counts/version/civil currentness and selected semantic fingerprint
GRANT SELECT (record_ordinal) ON TABLE public.integration_omie_transaction_evidence_v3 TO flooow_offline_execution_owner;
-- SPEC:970 E READ_PRIVILEGE; consumer=OE; entrypoint=S17-S18; transitive=NONE.
-- Required: V3 counts/version/civil currentness and selected semantic fingerprint
GRANT SELECT (provider_created_local) ON TABLE public.integration_omie_transaction_evidence_v3 TO flooow_offline_execution_owner;
-- SPEC:971 E READ_PRIVILEGE; consumer=OE; entrypoint=S17-S18; transitive=NONE.
-- Required: V3 counts/version/civil currentness and selected semantic fingerprint
GRANT SELECT (provider_modified_local) ON TABLE public.integration_omie_transaction_evidence_v3 TO flooow_offline_execution_owner;
-- SPEC:972 E READ_PRIVILEGE; consumer=OE; entrypoint=S17-S18; transitive=NONE.
-- Required: V3 counts/version/civil currentness and selected semantic fingerprint
GRANT SELECT (semantic_fingerprint_version) ON TABLE public.integration_omie_transaction_evidence_v3 TO flooow_offline_execution_owner;
-- SPEC:973 E READ_PRIVILEGE; consumer=OE; entrypoint=S17-S18; transitive=NONE.
-- Required: V3 counts/version/civil currentness and selected semantic fingerprint
GRANT SELECT (source_evidence_semantic_fingerprint) ON TABLE public.integration_omie_transaction_evidence_v3 TO flooow_offline_execution_owner;
-- SPEC:974 E READ_PRIVILEGE; consumer=TL; entrypoint=S17-S18; transitive=NONE.
-- Required: Exact target identity/scope and returned private external/currency
GRANT SELECT (organization_id) ON TABLE public.marketplace_order_identity_registry TO flooow_offline_execution_owner;
-- SPEC:975 E READ_PRIVILEGE; consumer=TL; entrypoint=S17-S18; transitive=NONE.
-- Required: Exact target identity/scope and returned private external/currency
GRANT SELECT (marketplace_key) ON TABLE public.marketplace_order_identity_registry TO flooow_offline_execution_owner;
-- SPEC:976 E READ_PRIVILEGE; consumer=TL; entrypoint=S17-S18; transitive=NONE.
-- Required: Exact target identity/scope and returned private external/currency
GRANT SELECT (external_order_id) ON TABLE public.marketplace_order_identity_registry TO flooow_offline_execution_owner;
-- SPEC:977 E READ_PRIVILEGE; consumer=TL; entrypoint=S17-S18; transitive=NONE.
-- Required: Exact target identity/scope and returned private external/currency
GRANT SELECT (marketplace_order_id) ON TABLE public.marketplace_order_identity_registry TO flooow_offline_execution_owner;
-- SPEC:978 E READ_PRIVILEGE; consumer=TL; entrypoint=S17-S18; transitive=NONE.
-- Required: Exact target identity/scope and returned private external/currency
GRANT SELECT (currency) ON TABLE public.marketplace_order_identity_registry TO flooow_offline_execution_owner;
-- SPEC:979 E READ_PRIVILEGE; consumer=TL; entrypoint=S17-S18; transitive=NONE.
-- Required: PROMOTED/DUPLICATE join and earliest progress/ordinal tie-break
GRANT SELECT (organization_id) ON TABLE public.marketplace_order_occurrence_source_promotion TO flooow_offline_execution_owner;
-- SPEC:980 E READ_PRIVILEGE; consumer=TL; entrypoint=S17-S18; transitive=NONE.
-- Required: PROMOTED/DUPLICATE join and earliest progress/ordinal tie-break
GRANT SELECT (source_connection_id) ON TABLE public.marketplace_order_occurrence_source_promotion TO flooow_offline_execution_owner;
-- SPEC:981 E READ_PRIVILEGE; consumer=TL; entrypoint=S17-S18; transitive=NONE.
-- Required: PROMOTED/DUPLICATE join and earliest progress/ordinal tie-break
GRANT SELECT (source_capability) ON TABLE public.marketplace_order_occurrence_source_promotion TO flooow_offline_execution_owner;
-- SPEC:982 E READ_PRIVILEGE; consumer=TL; entrypoint=S17-S18; transitive=NONE.
-- Required: PROMOTED/DUPLICATE join and earliest progress/ordinal tie-break
GRANT SELECT (source_input_progress_version) ON TABLE public.marketplace_order_occurrence_source_promotion TO flooow_offline_execution_owner;
-- SPEC:983 E READ_PRIVILEGE; consumer=TL; entrypoint=S17-S18; transitive=NONE.
-- Required: PROMOTED/DUPLICATE join and earliest progress/ordinal tie-break
GRANT SELECT (source_record_ordinal) ON TABLE public.marketplace_order_occurrence_source_promotion TO flooow_offline_execution_owner;
-- SPEC:984 E READ_PRIVILEGE; consumer=TL; entrypoint=S17-S18; transitive=NONE.
-- Required: PROMOTED/DUPLICATE join and earliest progress/ordinal tie-break
GRANT SELECT (marketplace_order_id) ON TABLE public.marketplace_order_occurrence_source_promotion TO flooow_offline_execution_owner;
-- SPEC:985 E READ_PRIVILEGE; consumer=TL; entrypoint=S17-S18; transitive=NONE.
-- Required: PROMOTED/DUPLICATE join and earliest progress/ordinal tie-break
GRANT SELECT (outcome) ON TABLE public.marketplace_order_occurrence_source_promotion TO flooow_offline_execution_owner;
-- SPEC:986 E READ_PRIVILEGE; consumer=HD; entrypoint=S17-S18; transitive=NONE.
-- Required: Existing bound decision existence denial/read-route and scoped head/decision identity joins only; no predecessor revision read; private row for helpers is constructed, not SELECT d.*
GRANT SELECT (organization_id) ON TABLE public.marketplace_transaction_identity_decision TO flooow_offline_execution_owner;
-- SPEC:987 E READ_PRIVILEGE; consumer=HD; entrypoint=S17-S18; transitive=NONE.
-- Required: Existing bound decision existence denial/read-route and scoped head/decision identity joins only; no predecessor revision read; private row for helpers is constructed, not SELECT d.*
GRANT SELECT (decision_id) ON TABLE public.marketplace_transaction_identity_decision TO flooow_offline_execution_owner;
-- SPEC:988 E READ_PRIVILEGE; consumer=HD; entrypoint=S17-S18; transitive=NONE.
-- Required: No current head for initial confirmed decision; exact target/subject conflict read
GRANT SELECT (organization_id) ON TABLE public.marketplace_transaction_identity_head TO flooow_offline_execution_owner;
-- SPEC:989 E READ_PRIVILEGE; consumer=HD; entrypoint=S17-S18; transitive=NONE.
-- Required: No current head for initial confirmed decision; exact target/subject conflict read
GRANT SELECT (omie_connection_id) ON TABLE public.marketplace_transaction_identity_head TO flooow_offline_execution_owner;
-- SPEC:990 E READ_PRIVILEGE; consumer=HD; entrypoint=S17-S18; transitive=NONE.
-- Required: No current head for initial confirmed decision; exact target/subject conflict read
GRANT SELECT (source_order_reference) ON TABLE public.marketplace_transaction_identity_head TO flooow_offline_execution_owner;
-- SPEC:991 E READ_PRIVILEGE; consumer=HD; entrypoint=S17-S18; transitive=NONE.
-- Required: No current head for initial confirmed decision; exact target/subject conflict read
GRANT SELECT (marketplace_order_id) ON TABLE public.marketplace_transaction_identity_head TO flooow_offline_execution_owner;
-- SPEC:992 E READ_PRIVILEGE; consumer=HD; entrypoint=S17-S18; transitive=NONE.
-- Required: No current head for initial confirmed decision; exact target/subject conflict read
GRANT SELECT (decision_id) ON TABLE public.marketplace_transaction_identity_head TO flooow_offline_execution_owner;
-- SPEC:993 A READ_PRIVILEGE; consumer=HISTORY; entrypoint=S04; transitive=NONE.
-- Required: Six S04 output/history fields
GRANT SELECT (installed_rank) ON TABLE public.flyway_schema_history TO flooow_offline_audit_owner;
-- SPEC:994 A READ_PRIVILEGE; consumer=HISTORY; entrypoint=S04; transitive=NONE.
-- Required: Six S04 output/history fields
GRANT SELECT (version) ON TABLE public.flyway_schema_history TO flooow_offline_audit_owner;
-- SPEC:995 A READ_PRIVILEGE; consumer=HISTORY; entrypoint=S04; transitive=NONE.
-- Required: Six S04 output/history fields
GRANT SELECT (type) ON TABLE public.flyway_schema_history TO flooow_offline_audit_owner;
-- SPEC:996 A READ_PRIVILEGE; consumer=HISTORY; entrypoint=S04; transitive=NONE.
-- Required: Six S04 output/history fields
GRANT SELECT (script) ON TABLE public.flyway_schema_history TO flooow_offline_audit_owner;
-- SPEC:997 A READ_PRIVILEGE; consumer=HISTORY; entrypoint=S04; transitive=NONE.
-- Required: Six S04 output/history fields
GRANT SELECT (checksum) ON TABLE public.flyway_schema_history TO flooow_offline_audit_owner;
-- SPEC:998 A READ_PRIVILEGE; consumer=HISTORY; entrypoint=S04; transitive=NONE.
-- Required: Six S04 output/history fields
GRANT SELECT (success) ON TABLE public.flyway_schema_history TO flooow_offline_audit_owner;
-- SPEC:999 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (organization_id) ON TABLE public.s2a_accepted_attestation TO flooow_offline_audit_owner;
-- SPEC:1000 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (manifest_id) ON TABLE public.s2a_accepted_attestation TO flooow_offline_audit_owner;
-- SPEC:1001 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (artifact_version) ON TABLE public.s2a_accepted_attestation TO flooow_offline_audit_owner;
-- SPEC:1002 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (schema_version) ON TABLE public.s2a_accepted_attestation TO flooow_offline_audit_owner;
-- SPEC:1003 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (canonicalization_version) ON TABLE public.s2a_accepted_attestation TO flooow_offline_audit_owner;
-- SPEC:1004 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (canonical_manifest_bytes) ON TABLE public.s2a_accepted_attestation TO flooow_offline_audit_owner;
-- SPEC:1005 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (manifest_digest) ON TABLE public.s2a_accepted_attestation TO flooow_offline_audit_owner;
-- SPEC:1006 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (canonical_signature_preimage_bytes) ON TABLE public.s2a_accepted_attestation TO flooow_offline_audit_owner;
-- SPEC:1007 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (algorithm_id) ON TABLE public.s2a_accepted_attestation TO flooow_offline_audit_owner;
-- SPEC:1008 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (signer_key_id) ON TABLE public.s2a_accepted_attestation TO flooow_offline_audit_owner;
-- SPEC:1009 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (signer_key_revision) ON TABLE public.s2a_accepted_attestation TO flooow_offline_audit_owner;
-- SPEC:1010 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (signer_key_fingerprint) ON TABLE public.s2a_accepted_attestation TO flooow_offline_audit_owner;
-- SPEC:1011 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (signer_key_lineage_fingerprint) ON TABLE public.s2a_accepted_attestation TO flooow_offline_audit_owner;
-- SPEC:1012 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (subject_public_key_info_der) ON TABLE public.s2a_accepted_attestation TO flooow_offline_audit_owner;
-- SPEC:1013 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (signature_bytes) ON TABLE public.s2a_accepted_attestation TO flooow_offline_audit_owner;
-- SPEC:1014 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (signer_authority_id) ON TABLE public.s2a_accepted_attestation TO flooow_offline_audit_owner;
-- SPEC:1015 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (signer_authority_revision) ON TABLE public.s2a_accepted_attestation TO flooow_offline_audit_owner;
-- SPEC:1016 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (signer_authority_fingerprint) ON TABLE public.s2a_accepted_attestation TO flooow_offline_audit_owner;
-- SPEC:1017 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (verified_at) ON TABLE public.s2a_accepted_attestation TO flooow_offline_audit_owner;
-- SPEC:1018 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (accepted_proof_fingerprint) ON TABLE public.s2a_accepted_attestation TO flooow_offline_audit_owner;
-- SPEC:1019 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (recorded_at) ON TABLE public.s2a_accepted_attestation TO flooow_offline_audit_owner;
-- SPEC:1020 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (organization_id) ON TABLE public.s2a_attestation_consumption TO flooow_offline_audit_owner;
-- SPEC:1021 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (manifest_id) ON TABLE public.s2a_attestation_consumption TO flooow_offline_audit_owner;
-- SPEC:1022 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (manifest_digest) ON TABLE public.s2a_attestation_consumption TO flooow_offline_audit_owner;
-- SPEC:1023 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (principal_id) ON TABLE public.s2a_attestation_consumption TO flooow_offline_audit_owner;
-- SPEC:1024 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (correlation_id) ON TABLE public.s2a_attestation_consumption TO flooow_offline_audit_owner;
-- SPEC:1025 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (consumed_at) ON TABLE public.s2a_attestation_consumption TO flooow_offline_audit_owner;
-- SPEC:1026 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (organization_id) ON TABLE public.command_principal TO flooow_offline_audit_owner;
-- SPEC:1027 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (principal_id) ON TABLE public.command_principal TO flooow_offline_audit_owner;
-- SPEC:1028 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (mercado_livre_connection_id) ON TABLE public.command_principal TO flooow_offline_audit_owner;
-- SPEC:1029 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (omie_connection_id) ON TABLE public.command_principal TO flooow_offline_audit_owner;
-- SPEC:1030 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (reason) ON TABLE public.command_principal TO flooow_offline_audit_owner;
-- SPEC:1031 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (provenance) ON TABLE public.command_principal TO flooow_offline_audit_owner;
-- SPEC:1032 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (correlation_id) ON TABLE public.command_principal TO flooow_offline_audit_owner;
-- SPEC:1033 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (decided_at) ON TABLE public.command_principal TO flooow_offline_audit_owner;
-- SPEC:1034 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (organization_id) ON TABLE public.command_credential_revision TO flooow_offline_audit_owner;
-- SPEC:1035 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (principal_id) ON TABLE public.command_credential_revision TO flooow_offline_audit_owner;
-- SPEC:1036 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (credential_id) ON TABLE public.command_credential_revision TO flooow_offline_audit_owner;
-- SPEC:1037 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (revision) ON TABLE public.command_credential_revision TO flooow_offline_audit_owner;
-- SPEC:1038 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (supersedes_revision) ON TABLE public.command_credential_revision TO flooow_offline_audit_owner;
-- SPEC:1039 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (state) ON TABLE public.command_credential_revision TO flooow_offline_audit_owner;
-- SPEC:1040 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (reason) ON TABLE public.command_credential_revision TO flooow_offline_audit_owner;
-- SPEC:1041 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (provenance) ON TABLE public.command_credential_revision TO flooow_offline_audit_owner;
-- SPEC:1042 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (correlation_id) ON TABLE public.command_credential_revision TO flooow_offline_audit_owner;
-- SPEC:1043 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (organization_id) ON TABLE public.command_permission_grant TO flooow_offline_audit_owner;
-- SPEC:1044 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (principal_id) ON TABLE public.command_permission_grant TO flooow_offline_audit_owner;
-- SPEC:1045 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (grant_id) ON TABLE public.command_permission_grant TO flooow_offline_audit_owner;
-- SPEC:1046 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (permission) ON TABLE public.command_permission_grant TO flooow_offline_audit_owner;
-- SPEC:1047 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (state) ON TABLE public.command_permission_grant TO flooow_offline_audit_owner;
-- SPEC:1048 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (revision) ON TABLE public.command_permission_grant TO flooow_offline_audit_owner;
-- SPEC:1049 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (supersedes_grant_id) ON TABLE public.command_permission_grant TO flooow_offline_audit_owner;
-- SPEC:1050 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (reason) ON TABLE public.command_permission_grant TO flooow_offline_audit_owner;
-- SPEC:1051 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (provenance) ON TABLE public.command_permission_grant TO flooow_offline_audit_owner;
-- SPEC:1052 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (correlation_id) ON TABLE public.command_permission_grant TO flooow_offline_audit_owner;
-- SPEC:1053 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (decided_at) ON TABLE public.command_permission_grant TO flooow_offline_audit_owner;
-- SPEC:1054 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (organization_id) ON TABLE public.marketplace_transaction_identity_decision TO flooow_offline_audit_owner;
-- SPEC:1055 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (decision_id) ON TABLE public.marketplace_transaction_identity_decision TO flooow_offline_audit_owner;
-- SPEC:1056 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (omie_connection_id) ON TABLE public.marketplace_transaction_identity_decision TO flooow_offline_audit_owner;
-- SPEC:1057 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (source_order_reference) ON TABLE public.marketplace_transaction_identity_decision TO flooow_offline_audit_owner;
-- SPEC:1058 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (marketplace_order_id) ON TABLE public.marketplace_transaction_identity_decision TO flooow_offline_audit_owner;
-- SPEC:1059 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (kind) ON TABLE public.marketplace_transaction_identity_decision TO flooow_offline_audit_owner;
-- SPEC:1060 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (reason) ON TABLE public.marketplace_transaction_identity_decision TO flooow_offline_audit_owner;
-- SPEC:1061 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (revision) ON TABLE public.marketplace_transaction_identity_decision TO flooow_offline_audit_owner;
-- SPEC:1062 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (supersedes_decision_id) ON TABLE public.marketplace_transaction_identity_decision TO flooow_offline_audit_owner;
-- SPEC:1063 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (ml_connection_id) ON TABLE public.marketplace_transaction_identity_decision TO flooow_offline_audit_owner;
-- SPEC:1064 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (ml_capability) ON TABLE public.marketplace_transaction_identity_decision TO flooow_offline_audit_owner;
-- SPEC:1065 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (ml_progress_version) ON TABLE public.marketplace_transaction_identity_decision TO flooow_offline_audit_owner;
-- SPEC:1066 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (ml_record_ordinal) ON TABLE public.marketplace_transaction_identity_decision TO flooow_offline_audit_owner;
-- SPEC:1067 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (external_order_id) ON TABLE public.marketplace_transaction_identity_decision TO flooow_offline_audit_owner;
-- SPEC:1068 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (currency) ON TABLE public.marketplace_transaction_identity_decision TO flooow_offline_audit_owner;
-- SPEC:1069 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (omie_capability) ON TABLE public.marketplace_transaction_identity_decision TO flooow_offline_audit_owner;
-- SPEC:1070 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (omie_progress_version) ON TABLE public.marketplace_transaction_identity_decision TO flooow_offline_audit_owner;
-- SPEC:1071 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (omie_record_ordinal) ON TABLE public.marketplace_transaction_identity_decision TO flooow_offline_audit_owner;
-- SPEC:1072 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (omie_semantic_fingerprint) ON TABLE public.marketplace_transaction_identity_decision TO flooow_offline_audit_owner;
-- SPEC:1073 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (provider_revision_local) ON TABLE public.marketplace_transaction_identity_decision TO flooow_offline_audit_owner;
-- SPEC:1074 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (principal_id) ON TABLE public.marketplace_transaction_identity_decision TO flooow_offline_audit_owner;
-- SPEC:1075 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (credential_id) ON TABLE public.marketplace_transaction_identity_decision TO flooow_offline_audit_owner;
-- SPEC:1076 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (credential_revision) ON TABLE public.marketplace_transaction_identity_decision TO flooow_offline_audit_owner;
-- SPEC:1077 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (grant_id) ON TABLE public.marketplace_transaction_identity_decision TO flooow_offline_audit_owner;
-- SPEC:1078 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (grant_revision) ON TABLE public.marketplace_transaction_identity_decision TO flooow_offline_audit_owner;
-- SPEC:1079 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (permission) ON TABLE public.marketplace_transaction_identity_decision TO flooow_offline_audit_owner;
-- SPEC:1080 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (authorization_semantic_version) ON TABLE public.marketplace_transaction_identity_decision TO flooow_offline_audit_owner;
-- SPEC:1081 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (authorization_fingerprint) ON TABLE public.marketplace_transaction_identity_decision TO flooow_offline_audit_owner;
-- SPEC:1082 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (intent_fingerprint) ON TABLE public.marketplace_transaction_identity_decision TO flooow_offline_audit_owner;
-- SPEC:1083 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (decision_semantic_fingerprint) ON TABLE public.marketplace_transaction_identity_decision TO flooow_offline_audit_owner;
-- SPEC:1084 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (provenance) ON TABLE public.marketplace_transaction_identity_decision TO flooow_offline_audit_owner;
-- SPEC:1085 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (correlation_id) ON TABLE public.marketplace_transaction_identity_decision TO flooow_offline_audit_owner;
-- SPEC:1086 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (decided_at) ON TABLE public.marketplace_transaction_identity_decision TO flooow_offline_audit_owner;
-- SPEC:1087 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (organization_id) ON TABLE public.marketplace_transaction_identity_head TO flooow_offline_audit_owner;
-- SPEC:1088 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (omie_connection_id) ON TABLE public.marketplace_transaction_identity_head TO flooow_offline_audit_owner;
-- SPEC:1089 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (source_order_reference) ON TABLE public.marketplace_transaction_identity_head TO flooow_offline_audit_owner;
-- SPEC:1090 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (marketplace_order_id) ON TABLE public.marketplace_transaction_identity_head TO flooow_offline_audit_owner;
-- SPEC:1091 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (decision_id) ON TABLE public.marketplace_transaction_identity_head TO flooow_offline_audit_owner;
-- SPEC:1092 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=NONE.
-- Required: Existing exact inspect/consumption/decision predicates and full declared accepted/decision projection or frozen helper hash inputs
GRANT SELECT (kind) ON TABLE public.marketplace_transaction_identity_head TO flooow_offline_audit_owner;
-- SPEC:1093 A READ_PRIVILEGE; consumer=RECON.acceptedArtifact; entrypoint=S03; transitive=NONE.
-- Required: Exact accepted signer-key join/state/verified-at/public-key lineage predicates
GRANT SELECT (organization_id) ON TABLE public.s2a_signer_key_revision TO flooow_offline_audit_owner;
-- SPEC:1094 A READ_PRIVILEGE; consumer=RECON.acceptedArtifact; entrypoint=S03; transitive=NONE.
-- Required: Exact accepted signer-key join/state/verified-at/public-key lineage predicates
GRANT SELECT (signer_key_id) ON TABLE public.s2a_signer_key_revision TO flooow_offline_audit_owner;
-- SPEC:1095 A READ_PRIVILEGE; consumer=RECON.acceptedArtifact; entrypoint=S03; transitive=NONE.
-- Required: Exact accepted signer-key join/state/verified-at/public-key lineage predicates
GRANT SELECT (revision) ON TABLE public.s2a_signer_key_revision TO flooow_offline_audit_owner;
-- SPEC:1096 A READ_PRIVILEGE; consumer=RECON.acceptedArtifact; entrypoint=S03; transitive=NONE.
-- Required: Exact accepted signer-key join/state/verified-at/public-key lineage predicates
GRANT SELECT (signer_subject_id) ON TABLE public.s2a_signer_key_revision TO flooow_offline_audit_owner;
-- SPEC:1097 A READ_PRIVILEGE; consumer=RECON.acceptedArtifact; entrypoint=S03; transitive=NONE.
-- Required: Exact accepted signer-key join/state/verified-at/public-key lineage predicates
GRANT SELECT (algorithm_id) ON TABLE public.s2a_signer_key_revision TO flooow_offline_audit_owner;
-- SPEC:1098 A READ_PRIVILEGE; consumer=RECON.acceptedArtifact; entrypoint=S03; transitive=NONE.
-- Required: Exact accepted signer-key join/state/verified-at/public-key lineage predicates
GRANT SELECT (subject_public_key_info_der) ON TABLE public.s2a_signer_key_revision TO flooow_offline_audit_owner;
-- SPEC:1099 A READ_PRIVILEGE; consumer=RECON.acceptedArtifact; entrypoint=S03; transitive=NONE.
-- Required: Exact accepted signer-key join/state/verified-at/public-key lineage predicates
GRANT SELECT (signer_key_fingerprint) ON TABLE public.s2a_signer_key_revision TO flooow_offline_audit_owner;
-- SPEC:1100 A READ_PRIVILEGE; consumer=RECON.acceptedArtifact; entrypoint=S03; transitive=NONE.
-- Required: Exact accepted signer-key join/state/verified-at/public-key lineage predicates
GRANT SELECT (state) ON TABLE public.s2a_signer_key_revision TO flooow_offline_audit_owner;
-- SPEC:1101 A READ_PRIVILEGE; consumer=RECON.acceptedArtifact; entrypoint=S03; transitive=NONE.
-- Required: Exact accepted signer-key join/state/verified-at/public-key lineage predicates
GRANT SELECT (valid_from) ON TABLE public.s2a_signer_key_revision TO flooow_offline_audit_owner;
-- SPEC:1102 A READ_PRIVILEGE; consumer=RECON.acceptedArtifact; entrypoint=S03; transitive=NONE.
-- Required: Exact accepted signer-key join/state/verified-at/public-key lineage predicates
GRANT SELECT (effective_at) ON TABLE public.s2a_signer_key_revision TO flooow_offline_audit_owner;
-- SPEC:1103 A READ_PRIVILEGE; consumer=RECON.acceptedArtifact; entrypoint=S03; transitive=NONE.
-- Required: Exact accepted signer-key join/state/verified-at/public-key lineage predicates
GRANT SELECT (lineage_fingerprint) ON TABLE public.s2a_signer_key_revision TO flooow_offline_audit_owner;
-- SPEC:1104 A READ_PRIVILEGE; consumer=RECON.acceptedArtifact; entrypoint=S03; transitive=NONE.
-- Required: Exact accepted authority join/action/role/source/permission/window predicates
GRANT SELECT (organization_id) ON TABLE public.s2a_signer_authority_revision TO flooow_offline_audit_owner;
-- SPEC:1105 A READ_PRIVILEGE; consumer=RECON.acceptedArtifact; entrypoint=S03; transitive=NONE.
-- Required: Exact accepted authority join/action/role/source/permission/window predicates
GRANT SELECT (signer_authority_id) ON TABLE public.s2a_signer_authority_revision TO flooow_offline_audit_owner;
-- SPEC:1106 A READ_PRIVILEGE; consumer=RECON.acceptedArtifact; entrypoint=S03; transitive=NONE.
-- Required: Exact accepted authority join/action/role/source/permission/window predicates
GRANT SELECT (revision) ON TABLE public.s2a_signer_authority_revision TO flooow_offline_audit_owner;
-- SPEC:1107 A READ_PRIVILEGE; consumer=RECON.acceptedArtifact; entrypoint=S03; transitive=NONE.
-- Required: Exact accepted authority join/action/role/source/permission/window predicates
GRANT SELECT (signer_subject_id) ON TABLE public.s2a_signer_authority_revision TO flooow_offline_audit_owner;
-- SPEC:1108 A READ_PRIVILEGE; consumer=RECON.acceptedArtifact; entrypoint=S03; transitive=NONE.
-- Required: Exact accepted authority join/action/role/source/permission/window predicates
GRANT SELECT (signer_role) ON TABLE public.s2a_signer_authority_revision TO flooow_offline_audit_owner;
-- SPEC:1109 A READ_PRIVILEGE; consumer=RECON.acceptedArtifact; entrypoint=S03; transitive=NONE.
-- Required: Exact accepted authority join/action/role/source/permission/window predicates
GRANT SELECT (signer_key_id) ON TABLE public.s2a_signer_authority_revision TO flooow_offline_audit_owner;
-- SPEC:1110 A READ_PRIVILEGE; consumer=RECON.acceptedArtifact; entrypoint=S03; transitive=NONE.
-- Required: Exact accepted authority join/action/role/source/permission/window predicates
GRANT SELECT (signer_key_revision) ON TABLE public.s2a_signer_authority_revision TO flooow_offline_audit_owner;
-- SPEC:1111 A READ_PRIVILEGE; consumer=RECON.acceptedArtifact; entrypoint=S03; transitive=NONE.
-- Required: Exact accepted authority join/action/role/source/permission/window predicates
GRANT SELECT (signer_key_fingerprint) ON TABLE public.s2a_signer_authority_revision TO flooow_offline_audit_owner;
-- SPEC:1112 A READ_PRIVILEGE; consumer=RECON.acceptedArtifact; entrypoint=S03; transitive=NONE.
-- Required: Exact accepted authority join/action/role/source/permission/window predicates
GRANT SELECT (approval_action) ON TABLE public.s2a_signer_authority_revision TO flooow_offline_audit_owner;
-- SPEC:1113 A READ_PRIVILEGE; consumer=RECON.acceptedArtifact; entrypoint=S03; transitive=NONE.
-- Required: Exact accepted authority join/action/role/source/permission/window predicates
GRANT SELECT (permission) ON TABLE public.s2a_signer_authority_revision TO flooow_offline_audit_owner;
-- SPEC:1114 A READ_PRIVILEGE; consumer=RECON.acceptedArtifact; entrypoint=S03; transitive=NONE.
-- Required: Exact accepted authority join/action/role/source/permission/window predicates
GRANT SELECT (valid_from) ON TABLE public.s2a_signer_authority_revision TO flooow_offline_audit_owner;
-- SPEC:1115 A READ_PRIVILEGE; consumer=RECON.acceptedArtifact; entrypoint=S03; transitive=NONE.
-- Required: Exact accepted authority join/action/role/source/permission/window predicates
GRANT SELECT (valid_until) ON TABLE public.s2a_signer_authority_revision TO flooow_offline_audit_owner;
-- SPEC:1116 A READ_PRIVILEGE; consumer=RECON.acceptedArtifact; entrypoint=S03; transitive=NONE.
-- Required: Exact accepted authority join/action/role/source/permission/window predicates
GRANT SELECT (state) ON TABLE public.s2a_signer_authority_revision TO flooow_offline_audit_owner;
-- SPEC:1117 A READ_PRIVILEGE; consumer=RECON.acceptedArtifact; entrypoint=S03; transitive=NONE.
-- Required: Exact accepted authority join/action/role/source/permission/window predicates
GRANT SELECT (signer_authority_fingerprint) ON TABLE public.s2a_signer_authority_revision TO flooow_offline_audit_owner;
-- SPEC:1118 A READ_PRIVILEGE; consumer=RECON.acceptedArtifact; entrypoint=S03; transitive=NONE.
-- Required: Exact accepted authority join/action/role/source/permission/window predicates
GRANT SELECT (approval_source_id) ON TABLE public.s2a_signer_authority_revision TO flooow_offline_audit_owner;
-- SPEC:1119 A READ_PRIVILEGE; consumer=RECON.acceptedArtifact; entrypoint=S03; transitive=NONE.
-- Required: Exact accepted authority join/action/role/source/permission/window predicates
GRANT SELECT (decided_at) ON TABLE public.s2a_signer_authority_revision TO flooow_offline_audit_owner;
-- SPEC:1120 A READ_PRIVILEGE; consumer=INSPECT/RECON.consumption; entrypoint=S02-S03; transitive=NONE.
-- Required: Bound prefix/unexpected-operation counts, receipt-null shape and effect-time lineage; intent/receipt hash delegated to Z
GRANT SELECT (organization_id) ON TABLE public.command_authority_operation TO flooow_offline_audit_owner;
-- SPEC:1121 A READ_PRIVILEGE; consumer=INSPECT/RECON.consumption; entrypoint=S02-S03; transitive=NONE.
-- Required: Bound prefix/unexpected-operation counts, receipt-null shape and effect-time lineage; intent/receipt hash delegated to Z
GRANT SELECT (operation_id) ON TABLE public.command_authority_operation TO flooow_offline_audit_owner;
-- SPEC:1122 A READ_PRIVILEGE; consumer=INSPECT/RECON.consumption; entrypoint=S02-S03; transitive=NONE.
-- Required: Bound prefix/unexpected-operation counts, receipt-null shape and effect-time lineage; intent/receipt hash delegated to Z
GRANT SELECT (operation) ON TABLE public.command_authority_operation TO flooow_offline_audit_owner;
-- SPEC:1123 A READ_PRIVILEGE; consumer=INSPECT/RECON.consumption; entrypoint=S02-S03; transitive=NONE.
-- Required: Bound prefix/unexpected-operation counts, receipt-null shape and effect-time lineage; intent/receipt hash delegated to Z
GRANT SELECT (principal_id) ON TABLE public.command_authority_operation TO flooow_offline_audit_owner;
-- SPEC:1124 A READ_PRIVILEGE; consumer=INSPECT/RECON.consumption; entrypoint=S02-S03; transitive=NONE.
-- Required: Bound prefix/unexpected-operation counts, receipt-null shape and effect-time lineage; intent/receipt hash delegated to Z
GRANT SELECT (credential_id) ON TABLE public.command_authority_operation TO flooow_offline_audit_owner;
-- SPEC:1125 A READ_PRIVILEGE; consumer=INSPECT/RECON.consumption; entrypoint=S02-S03; transitive=NONE.
-- Required: Bound prefix/unexpected-operation counts, receipt-null shape and effect-time lineage; intent/receipt hash delegated to Z
GRANT SELECT (credential_revision) ON TABLE public.command_authority_operation TO flooow_offline_audit_owner;
-- SPEC:1126 A READ_PRIVILEGE; consumer=INSPECT/RECON.consumption; entrypoint=S02-S03; transitive=NONE.
-- Required: Bound prefix/unexpected-operation counts, receipt-null shape and effect-time lineage; intent/receipt hash delegated to Z
GRANT SELECT (grant_id) ON TABLE public.command_authority_operation TO flooow_offline_audit_owner;
-- SPEC:1127 A READ_PRIVILEGE; consumer=INSPECT/RECON.consumption; entrypoint=S02-S03; transitive=NONE.
-- Required: Bound prefix/unexpected-operation counts, receipt-null shape and effect-time lineage; intent/receipt hash delegated to Z
GRANT SELECT (grant_revision) ON TABLE public.command_authority_operation TO flooow_offline_audit_owner;
-- SPEC:1128 A READ_PRIVILEGE; consumer=INSPECT/RECON.consumption; entrypoint=S02-S03; transitive=NONE.
-- Required: Bound prefix/unexpected-operation counts, receipt-null shape and effect-time lineage; intent/receipt hash delegated to Z
GRANT SELECT (permission) ON TABLE public.command_authority_operation TO flooow_offline_audit_owner;
-- SPEC:1129 A READ_PRIVILEGE; consumer=INSPECT/RECON.consumption; entrypoint=S02-S03; transitive=NONE.
-- Required: Bound prefix/unexpected-operation counts, receipt-null shape and effect-time lineage; intent/receipt hash delegated to Z
GRANT SELECT (state) ON TABLE public.command_authority_operation TO flooow_offline_audit_owner;
-- SPEC:1130 A READ_PRIVILEGE; consumer=INSPECT/RECON.consumption; entrypoint=S02-S03; transitive=NONE.
-- Required: Bound prefix/unexpected-operation counts, receipt-null shape and effect-time lineage; intent/receipt hash delegated to Z
GRANT SELECT (correlation_id) ON TABLE public.command_authority_operation TO flooow_offline_audit_owner;
-- SPEC:1131 A READ_PRIVILEGE; consumer=INSPECT/RECON.consumption; entrypoint=S02-S03; transitive=NONE.
-- Required: Bound prefix/unexpected-operation counts, receipt-null shape and effect-time lineage; intent/receipt hash delegated to Z
GRANT SELECT (decided_at) ON TABLE public.command_authority_operation TO flooow_offline_audit_owner;
-- SPEC:1132 A READ_PRIVILEGE; consumer=INSPECT/RECON.consumption; entrypoint=S02-S03; transitive=NONE.
-- Required: Bound prefix/unexpected-operation counts, receipt-null shape and effect-time lineage; intent/receipt hash delegated to Z
GRANT SELECT (attestation_manifest_id) ON TABLE public.command_authority_operation TO flooow_offline_audit_owner;
-- SPEC:1133 A READ_PRIVILEGE; consumer=RECON.evidence; entrypoint=S03; transitive=NONE.
-- Required: Identity join and canonical evidence projection
GRANT SELECT (organization_id) ON TABLE public.marketplace_order_identity_registry TO flooow_offline_audit_owner;
-- SPEC:1134 A READ_PRIVILEGE; consumer=RECON.evidence; entrypoint=S03; transitive=NONE.
-- Required: Identity join and canonical evidence projection
GRANT SELECT (marketplace_key) ON TABLE public.marketplace_order_identity_registry TO flooow_offline_audit_owner;
-- SPEC:1135 A READ_PRIVILEGE; consumer=RECON.evidence; entrypoint=S03; transitive=NONE.
-- Required: Identity join and canonical evidence projection
GRANT SELECT (external_order_id) ON TABLE public.marketplace_order_identity_registry TO flooow_offline_audit_owner;
-- SPEC:1136 A READ_PRIVILEGE; consumer=RECON.evidence; entrypoint=S03; transitive=NONE.
-- Required: Identity join and canonical evidence projection
GRANT SELECT (marketplace_order_id) ON TABLE public.marketplace_order_identity_registry TO flooow_offline_audit_owner;
-- SPEC:1137 A READ_PRIVILEGE; consumer=RECON.evidence; entrypoint=S03; transitive=NONE.
-- Required: Identity join and canonical evidence projection
GRANT SELECT (currency) ON TABLE public.marketplace_order_identity_registry TO flooow_offline_audit_owner;
-- SPEC:1138 A READ_PRIVILEGE; consumer=RECON.evidence; entrypoint=S03; transitive=NONE.
-- Required: Exact decision-source promotion join and canonical outcome
GRANT SELECT (organization_id) ON TABLE public.marketplace_order_occurrence_source_promotion TO flooow_offline_audit_owner;
-- SPEC:1139 A READ_PRIVILEGE; consumer=RECON.evidence; entrypoint=S03; transitive=NONE.
-- Required: Exact decision-source promotion join and canonical outcome
GRANT SELECT (source_connection_id) ON TABLE public.marketplace_order_occurrence_source_promotion TO flooow_offline_audit_owner;
-- SPEC:1140 A READ_PRIVILEGE; consumer=RECON.evidence; entrypoint=S03; transitive=NONE.
-- Required: Exact decision-source promotion join and canonical outcome
GRANT SELECT (source_capability) ON TABLE public.marketplace_order_occurrence_source_promotion TO flooow_offline_audit_owner;
-- SPEC:1141 A READ_PRIVILEGE; consumer=RECON.evidence; entrypoint=S03; transitive=NONE.
-- Required: Exact decision-source promotion join and canonical outcome
GRANT SELECT (source_input_progress_version) ON TABLE public.marketplace_order_occurrence_source_promotion TO flooow_offline_audit_owner;
-- SPEC:1142 A READ_PRIVILEGE; consumer=RECON.evidence; entrypoint=S03; transitive=NONE.
-- Required: Exact decision-source promotion join and canonical outcome
GRANT SELECT (source_record_ordinal) ON TABLE public.marketplace_order_occurrence_source_promotion TO flooow_offline_audit_owner;
-- SPEC:1143 A READ_PRIVILEGE; consumer=RECON.evidence; entrypoint=S03; transitive=NONE.
-- Required: Exact decision-source promotion join and canonical outcome
GRANT SELECT (marketplace_order_id) ON TABLE public.marketplace_order_occurrence_source_promotion TO flooow_offline_audit_owner;
-- SPEC:1144 A READ_PRIVILEGE; consumer=RECON.evidence; entrypoint=S03; transitive=NONE.
-- Required: Exact decision-source promotion join and canonical outcome
GRANT SELECT (outcome) ON TABLE public.marketplace_order_occurrence_source_promotion TO flooow_offline_audit_owner;
-- SPEC:1145 A READ_PRIVILEGE; consumer=RECON.evidence; entrypoint=S03; transitive=NONE.
-- Required: Evidence row joins and canonical source/integration/currency
GRANT SELECT (organization_id) ON TABLE public.integration_omie_transaction_evidence TO flooow_offline_audit_owner;
-- SPEC:1146 A READ_PRIVILEGE; consumer=RECON.evidence; entrypoint=S03; transitive=NONE.
-- Required: Evidence row joins and canonical source/integration/currency
GRANT SELECT (connection_id) ON TABLE public.integration_omie_transaction_evidence TO flooow_offline_audit_owner;
-- SPEC:1147 A READ_PRIVILEGE; consumer=RECON.evidence; entrypoint=S03; transitive=NONE.
-- Required: Evidence row joins and canonical source/integration/currency
GRANT SELECT (capability) ON TABLE public.integration_omie_transaction_evidence TO flooow_offline_audit_owner;
-- SPEC:1148 A READ_PRIVILEGE; consumer=RECON.evidence; entrypoint=S03; transitive=NONE.
-- Required: Evidence row joins and canonical source/integration/currency
GRANT SELECT (input_progress_version) ON TABLE public.integration_omie_transaction_evidence TO flooow_offline_audit_owner;
-- SPEC:1149 A READ_PRIVILEGE; consumer=RECON.evidence; entrypoint=S03; transitive=NONE.
-- Required: Evidence row joins and canonical source/integration/currency
GRANT SELECT (record_ordinal) ON TABLE public.integration_omie_transaction_evidence TO flooow_offline_audit_owner;
-- SPEC:1150 A READ_PRIVILEGE; consumer=RECON.evidence; entrypoint=S03; transitive=NONE.
-- Required: Evidence row joins and canonical source/integration/currency
GRANT SELECT (source_order_ref) ON TABLE public.integration_omie_transaction_evidence TO flooow_offline_audit_owner;
-- SPEC:1151 A READ_PRIVILEGE; consumer=RECON.evidence; entrypoint=S03; transitive=NONE.
-- Required: Evidence row joins and canonical source/integration/currency
GRANT SELECT (source_integration_ref) ON TABLE public.integration_omie_transaction_evidence TO flooow_offline_audit_owner;
-- SPEC:1152 A READ_PRIVILEGE; consumer=RECON.evidence; entrypoint=S03; transitive=NONE.
-- Required: Evidence row joins and canonical source/integration/currency
GRANT SELECT (currency) ON TABLE public.integration_omie_transaction_evidence TO flooow_offline_audit_owner;
-- SPEC:1153 A READ_PRIVILEGE; consumer=RECON.evidence; entrypoint=S03; transitive=NONE.
-- Required: Canonical V3 version/fingerprint and coalesce civil revision
GRANT SELECT (organization_id) ON TABLE public.integration_omie_transaction_evidence_v3 TO flooow_offline_audit_owner;
-- SPEC:1154 A READ_PRIVILEGE; consumer=RECON.evidence; entrypoint=S03; transitive=NONE.
-- Required: Canonical V3 version/fingerprint and coalesce civil revision
GRANT SELECT (connection_id) ON TABLE public.integration_omie_transaction_evidence_v3 TO flooow_offline_audit_owner;
-- SPEC:1155 A READ_PRIVILEGE; consumer=RECON.evidence; entrypoint=S03; transitive=NONE.
-- Required: Canonical V3 version/fingerprint and coalesce civil revision
GRANT SELECT (capability) ON TABLE public.integration_omie_transaction_evidence_v3 TO flooow_offline_audit_owner;
-- SPEC:1156 A READ_PRIVILEGE; consumer=RECON.evidence; entrypoint=S03; transitive=NONE.
-- Required: Canonical V3 version/fingerprint and coalesce civil revision
GRANT SELECT (input_progress_version) ON TABLE public.integration_omie_transaction_evidence_v3 TO flooow_offline_audit_owner;
-- SPEC:1157 A READ_PRIVILEGE; consumer=RECON.evidence; entrypoint=S03; transitive=NONE.
-- Required: Canonical V3 version/fingerprint and coalesce civil revision
GRANT SELECT (record_ordinal) ON TABLE public.integration_omie_transaction_evidence_v3 TO flooow_offline_audit_owner;
-- SPEC:1158 A READ_PRIVILEGE; consumer=RECON.evidence; entrypoint=S03; transitive=NONE.
-- Required: Canonical V3 version/fingerprint and coalesce civil revision
GRANT SELECT (provider_created_local) ON TABLE public.integration_omie_transaction_evidence_v3 TO flooow_offline_audit_owner;
-- SPEC:1159 A READ_PRIVILEGE; consumer=RECON.evidence; entrypoint=S03; transitive=NONE.
-- Required: Canonical V3 version/fingerprint and coalesce civil revision
GRANT SELECT (provider_modified_local) ON TABLE public.integration_omie_transaction_evidence_v3 TO flooow_offline_audit_owner;
-- SPEC:1160 A READ_PRIVILEGE; consumer=RECON.evidence; entrypoint=S03; transitive=NONE.
-- Required: Canonical V3 version/fingerprint and coalesce civil revision
GRANT SELECT (semantic_fingerprint_version) ON TABLE public.integration_omie_transaction_evidence_v3 TO flooow_offline_audit_owner;
-- SPEC:1161 A READ_PRIVILEGE; consumer=RECON.evidence; entrypoint=S03; transitive=NONE.
-- Required: Canonical V3 version/fingerprint and coalesce civil revision
GRANT SELECT (source_evidence_semantic_fingerprint) ON TABLE public.integration_omie_transaction_evidence_v3 TO flooow_offline_audit_owner;
-- SPEC:1162 A READ_PRIVILEGE; consumer=INSPECT.admissionValidity; entrypoint=S02; transitive=NONE.
-- Required: Current ACTIVE organization needed for effective admission predicate
GRANT SELECT (organization_id) ON TABLE public.integration_organization TO flooow_offline_audit_owner;
-- SPEC:1163 A READ_PRIVILEGE; consumer=INSPECT.admissionValidity; entrypoint=S02; transitive=NONE.
-- Required: Current ACTIVE organization needed for effective admission predicate
GRANT SELECT (status) ON TABLE public.integration_organization TO flooow_offline_audit_owner;
-- SPEC:1164 P READ_PRIVILEGE; consumer=P.boundPrincipal; entrypoint=internal P; transitive=NONE.
-- Required: Bound exact principal/connections before FOR UPDATE
GRANT SELECT (organization_id) ON TABLE public.command_principal TO flooow_offline_principal_lock_owner;
-- SPEC:1165 P READ_PRIVILEGE; consumer=P.boundPrincipal; entrypoint=internal P; transitive=NONE.
-- Required: Bound exact principal/connections before FOR UPDATE
GRANT SELECT (principal_id) ON TABLE public.command_principal TO flooow_offline_principal_lock_owner;
-- SPEC:1166 P READ_PRIVILEGE; consumer=P.boundPrincipal; entrypoint=internal P; transitive=NONE.
-- Required: Bound exact principal/connections before FOR UPDATE
GRANT SELECT (mercado_livre_connection_id) ON TABLE public.command_principal TO flooow_offline_principal_lock_owner;
-- SPEC:1167 P READ_PRIVILEGE; consumer=P.boundPrincipal; entrypoint=internal P; transitive=NONE.
-- Required: Bound exact principal/connections before FOR UPDATE
GRANT SELECT (omie_connection_id) ON TABLE public.command_principal TO flooow_offline_principal_lock_owner;
-- SPEC:1168 P LOCK_ENABLING_UPDATE_PRIVILEGE; consumer=P.boundPrincipal; entrypoint=internal P; transitive=organization_lock -> principal row lock.
-- Required: Minimum one-column UPDATE required for FOR UPDATE; no semantic write
GRANT UPDATE (principal_id) ON TABLE public.command_principal TO flooow_offline_principal_lock_owner;
-- SPEC:1169 Z READ_PRIVILEGE; consumer=IA.fingerprints; entrypoint=internal Z; transitive=NONE.
-- Required: Exact PostgresOfflineFieldProofSupport.fingerprints frozen intent/receipt joins and effect-time predicates; private verifier Z only
GRANT SELECT (organization_id) ON TABLE public.command_authority_operation TO flooow_offline_intent_audit_owner;
-- SPEC:1170 Z READ_PRIVILEGE; consumer=IA.fingerprints; entrypoint=internal Z; transitive=NONE.
-- Required: Exact PostgresOfflineFieldProofSupport.fingerprints frozen intent/receipt joins and effect-time predicates; private verifier Z only
GRANT SELECT (operation_id) ON TABLE public.command_authority_operation TO flooow_offline_intent_audit_owner;
-- SPEC:1171 Z READ_PRIVILEGE; consumer=IA.fingerprints; entrypoint=internal Z; transitive=NONE.
-- Required: Exact PostgresOfflineFieldProofSupport.fingerprints frozen intent/receipt joins and effect-time predicates; private verifier Z only
GRANT SELECT (operation) ON TABLE public.command_authority_operation TO flooow_offline_intent_audit_owner;
-- SPEC:1172 Z READ_PRIVILEGE; consumer=IA.fingerprints; entrypoint=internal Z; transitive=NONE.
-- Required: Exact PostgresOfflineFieldProofSupport.fingerprints frozen intent/receipt joins and effect-time predicates; private verifier Z only
GRANT SELECT (principal_id) ON TABLE public.command_authority_operation TO flooow_offline_intent_audit_owner;
-- SPEC:1173 Z READ_PRIVILEGE; consumer=IA.fingerprints; entrypoint=internal Z; transitive=NONE.
-- Required: Exact PostgresOfflineFieldProofSupport.fingerprints frozen intent/receipt joins and effect-time predicates; private verifier Z only
GRANT SELECT (credential_id) ON TABLE public.command_authority_operation TO flooow_offline_intent_audit_owner;
-- SPEC:1174 Z READ_PRIVILEGE; consumer=IA.fingerprints; entrypoint=internal Z; transitive=NONE.
-- Required: Exact PostgresOfflineFieldProofSupport.fingerprints frozen intent/receipt joins and effect-time predicates; private verifier Z only
GRANT SELECT (credential_revision) ON TABLE public.command_authority_operation TO flooow_offline_intent_audit_owner;
-- SPEC:1175 Z READ_PRIVILEGE; consumer=IA.fingerprints; entrypoint=internal Z; transitive=NONE.
-- Required: Exact PostgresOfflineFieldProofSupport.fingerprints frozen intent/receipt joins and effect-time predicates; private verifier Z only
GRANT SELECT (grant_id) ON TABLE public.command_authority_operation TO flooow_offline_intent_audit_owner;
-- SPEC:1176 Z READ_PRIVILEGE; consumer=IA.fingerprints; entrypoint=internal Z; transitive=NONE.
-- Required: Exact PostgresOfflineFieldProofSupport.fingerprints frozen intent/receipt joins and effect-time predicates; private verifier Z only
GRANT SELECT (grant_revision) ON TABLE public.command_authority_operation TO flooow_offline_intent_audit_owner;
-- SPEC:1177 Z READ_PRIVILEGE; consumer=IA.fingerprints; entrypoint=internal Z; transitive=NONE.
-- Required: Exact PostgresOfflineFieldProofSupport.fingerprints frozen intent/receipt joins and effect-time predicates; private verifier Z only
GRANT SELECT (permission) ON TABLE public.command_authority_operation TO flooow_offline_intent_audit_owner;
-- SPEC:1178 Z READ_PRIVILEGE; consumer=IA.fingerprints; entrypoint=internal Z; transitive=NONE.
-- Required: Exact PostgresOfflineFieldProofSupport.fingerprints frozen intent/receipt joins and effect-time predicates; private verifier Z only
GRANT SELECT (state) ON TABLE public.command_authority_operation TO flooow_offline_intent_audit_owner;
-- SPEC:1179 Z READ_PRIVILEGE; consumer=IA.fingerprints; entrypoint=internal Z; transitive=NONE.
-- Required: Exact PostgresOfflineFieldProofSupport.fingerprints frozen intent/receipt joins and effect-time predicates; private verifier Z only
GRANT SELECT (intent_fingerprint) ON TABLE public.command_authority_operation TO flooow_offline_intent_audit_owner;
-- SPEC:1180 Z READ_PRIVILEGE; consumer=IA.fingerprints; entrypoint=internal Z; transitive=NONE.
-- Required: Exact PostgresOfflineFieldProofSupport.fingerprints frozen intent/receipt joins and effect-time predicates; private verifier Z only
GRANT SELECT (receipt_fingerprint) ON TABLE public.command_authority_operation TO flooow_offline_intent_audit_owner;
-- SPEC:1181 Z READ_PRIVILEGE; consumer=IA.fingerprints; entrypoint=internal Z; transitive=NONE.
-- Required: Exact PostgresOfflineFieldProofSupport.fingerprints frozen intent/receipt joins and effect-time predicates; private verifier Z only
GRANT SELECT (correlation_id) ON TABLE public.command_authority_operation TO flooow_offline_intent_audit_owner;
-- SPEC:1182 Z READ_PRIVILEGE; consumer=IA.fingerprints; entrypoint=internal Z; transitive=NONE.
-- Required: Exact PostgresOfflineFieldProofSupport.fingerprints frozen intent/receipt joins and effect-time predicates; private verifier Z only
GRANT SELECT (decided_at) ON TABLE public.command_authority_operation TO flooow_offline_intent_audit_owner;
-- SPEC:1183 Z READ_PRIVILEGE; consumer=IA.fingerprints; entrypoint=internal Z; transitive=NONE.
-- Required: Exact PostgresOfflineFieldProofSupport.fingerprints frozen intent/receipt joins and effect-time predicates; private verifier Z only
GRANT SELECT (attestation_manifest_id) ON TABLE public.command_authority_operation TO flooow_offline_intent_audit_owner;
-- SPEC:1184 Z READ_PRIVILEGE; consumer=IA.fingerprints; entrypoint=internal Z; transitive=NONE.
-- Required: Exact PostgresOfflineFieldProofSupport.fingerprints frozen intent/receipt joins and effect-time predicates; private verifier Z only
GRANT SELECT (organization_id) ON TABLE public.command_principal TO flooow_offline_intent_audit_owner;
-- SPEC:1185 Z READ_PRIVILEGE; consumer=IA.fingerprints; entrypoint=internal Z; transitive=NONE.
-- Required: Exact PostgresOfflineFieldProofSupport.fingerprints frozen intent/receipt joins and effect-time predicates; private verifier Z only
GRANT SELECT (principal_id) ON TABLE public.command_principal TO flooow_offline_intent_audit_owner;
-- SPEC:1186 Z READ_PRIVILEGE; consumer=IA.fingerprints; entrypoint=internal Z; transitive=NONE.
-- Required: Exact PostgresOfflineFieldProofSupport.fingerprints frozen intent/receipt joins and effect-time predicates; private verifier Z only
GRANT SELECT (mercado_livre_connection_id) ON TABLE public.command_principal TO flooow_offline_intent_audit_owner;
-- SPEC:1187 Z READ_PRIVILEGE; consumer=IA.fingerprints; entrypoint=internal Z; transitive=NONE.
-- Required: Exact PostgresOfflineFieldProofSupport.fingerprints frozen intent/receipt joins and effect-time predicates; private verifier Z only
GRANT SELECT (omie_connection_id) ON TABLE public.command_principal TO flooow_offline_intent_audit_owner;
-- SPEC:1188 Z READ_PRIVILEGE; consumer=IA.fingerprints; entrypoint=internal Z; transitive=NONE.
-- Required: Exact PostgresOfflineFieldProofSupport.fingerprints frozen intent/receipt joins and effect-time predicates; private verifier Z only
GRANT SELECT (reason) ON TABLE public.command_principal TO flooow_offline_intent_audit_owner;
-- SPEC:1189 Z READ_PRIVILEGE; consumer=IA.fingerprints; entrypoint=internal Z; transitive=NONE.
-- Required: Exact PostgresOfflineFieldProofSupport.fingerprints frozen intent/receipt joins and effect-time predicates; private verifier Z only
GRANT SELECT (provenance) ON TABLE public.command_principal TO flooow_offline_intent_audit_owner;
-- SPEC:1190 Z READ_PRIVILEGE; consumer=IA.fingerprints; entrypoint=internal Z; transitive=NONE.
-- Required: Exact PostgresOfflineFieldProofSupport.fingerprints frozen intent/receipt joins and effect-time predicates; private verifier Z only
GRANT SELECT (decided_at) ON TABLE public.command_principal TO flooow_offline_intent_audit_owner;
-- SPEC:1191 Z READ_PRIVILEGE; consumer=IA.fingerprints; entrypoint=internal Z; transitive=NONE.
-- Required: Exact PostgresOfflineFieldProofSupport.fingerprints frozen intent/receipt joins and effect-time predicates; private verifier Z only
GRANT SELECT (organization_id) ON TABLE public.command_credential_revision TO flooow_offline_intent_audit_owner;
-- SPEC:1192 Z READ_PRIVILEGE; consumer=IA.fingerprints; entrypoint=internal Z; transitive=NONE.
-- Required: Exact PostgresOfflineFieldProofSupport.fingerprints frozen intent/receipt joins and effect-time predicates; private verifier Z only
GRANT SELECT (principal_id) ON TABLE public.command_credential_revision TO flooow_offline_intent_audit_owner;
-- SPEC:1193 Z READ_PRIVILEGE; consumer=IA.fingerprints; entrypoint=internal Z; transitive=NONE.
-- Required: Exact PostgresOfflineFieldProofSupport.fingerprints frozen intent/receipt joins and effect-time predicates; private verifier Z only
GRANT SELECT (credential_id) ON TABLE public.command_credential_revision TO flooow_offline_intent_audit_owner;
-- SPEC:1194 Z READ_PRIVILEGE; consumer=IA.fingerprints; entrypoint=internal Z; transitive=NONE.
-- Required: Exact PostgresOfflineFieldProofSupport.fingerprints frozen intent/receipt joins and effect-time predicates; private verifier Z only
GRANT SELECT (revision) ON TABLE public.command_credential_revision TO flooow_offline_intent_audit_owner;
-- SPEC:1195 Z READ_PRIVILEGE; consumer=IA.fingerprints; entrypoint=internal Z; transitive=NONE.
-- Required: Exact PostgresOfflineFieldProofSupport.fingerprints frozen intent/receipt joins and effect-time predicates; private verifier Z only
GRANT SELECT (secret_verifier) ON TABLE public.command_credential_revision TO flooow_offline_intent_audit_owner;
-- SPEC:1196 Z READ_PRIVILEGE; consumer=IA.fingerprints; entrypoint=internal Z; transitive=NONE.
-- Required: Exact PostgresOfflineFieldProofSupport.fingerprints frozen intent/receipt joins and effect-time predicates; private verifier Z only
GRANT SELECT (decided_at) ON TABLE public.command_credential_revision TO flooow_offline_intent_audit_owner;
-- SPEC:1197 Z READ_PRIVILEGE; consumer=IA.fingerprints; entrypoint=internal Z; transitive=NONE.
-- Required: Exact PostgresOfflineFieldProofSupport.fingerprints frozen intent/receipt joins and effect-time predicates; private verifier Z only
GRANT SELECT (organization_id) ON TABLE public.command_permission_grant TO flooow_offline_intent_audit_owner;
-- SPEC:1198 Z READ_PRIVILEGE; consumer=IA.fingerprints; entrypoint=internal Z; transitive=NONE.
-- Required: Exact PostgresOfflineFieldProofSupport.fingerprints frozen intent/receipt joins and effect-time predicates; private verifier Z only
GRANT SELECT (principal_id) ON TABLE public.command_permission_grant TO flooow_offline_intent_audit_owner;
-- SPEC:1199 Z READ_PRIVILEGE; consumer=IA.fingerprints; entrypoint=internal Z; transitive=NONE.
-- Required: Exact PostgresOfflineFieldProofSupport.fingerprints frozen intent/receipt joins and effect-time predicates; private verifier Z only
GRANT SELECT (grant_id) ON TABLE public.command_permission_grant TO flooow_offline_intent_audit_owner;
-- SPEC:1200 Z READ_PRIVILEGE; consumer=IA.fingerprints; entrypoint=internal Z; transitive=NONE.
-- Required: Exact PostgresOfflineFieldProofSupport.fingerprints frozen intent/receipt joins and effect-time predicates; private verifier Z only
GRANT SELECT (decided_at) ON TABLE public.command_permission_grant TO flooow_offline_intent_audit_owner;
-- SPEC:1201 Z READ_PRIVILEGE; consumer=IA.fingerprints; entrypoint=internal Z; transitive=NONE.
-- Required: Exact PostgresOfflineFieldProofSupport.fingerprints frozen intent/receipt joins and effect-time predicates; private verifier Z only
GRANT SELECT (organization_id) ON TABLE public.s2a_accepted_attestation TO flooow_offline_intent_audit_owner;
-- SPEC:1202 Z READ_PRIVILEGE; consumer=IA.fingerprints; entrypoint=internal Z; transitive=NONE.
-- Required: Exact PostgresOfflineFieldProofSupport.fingerprints frozen intent/receipt joins and effect-time predicates; private verifier Z only
GRANT SELECT (manifest_id) ON TABLE public.s2a_accepted_attestation TO flooow_offline_intent_audit_owner;
-- SPEC:1203 Z READ_PRIVILEGE; consumer=IA.fingerprints; entrypoint=internal Z; transitive=NONE.
-- Required: Exact PostgresOfflineFieldProofSupport.fingerprints frozen intent/receipt joins and effect-time predicates; private verifier Z only
GRANT SELECT (manifest_digest) ON TABLE public.s2a_accepted_attestation TO flooow_offline_intent_audit_owner;
-- SPEC:1204 Z READ_PRIVILEGE; consumer=IA.fingerprints; entrypoint=internal Z; transitive=NONE.
-- Required: Exact PostgresOfflineFieldProofSupport.fingerprints frozen intent/receipt joins and effect-time predicates; private verifier Z only
GRANT SELECT (accepted_proof_fingerprint) ON TABLE public.s2a_accepted_attestation TO flooow_offline_intent_audit_owner;
-- SPEC:1205 Q READ_PRIVILEGE; consumer=READINESS.history; entrypoint=internal Q; transitive=NONE.
-- Required: All six full-history digest fields
GRANT SELECT (installed_rank) ON TABLE public.flyway_schema_history TO flooow_offline_readiness_owner;
-- SPEC:1206 Q READ_PRIVILEGE; consumer=READINESS.history; entrypoint=internal Q; transitive=NONE.
-- Required: All six full-history digest fields
GRANT SELECT (version) ON TABLE public.flyway_schema_history TO flooow_offline_readiness_owner;
-- SPEC:1207 Q READ_PRIVILEGE; consumer=READINESS.history; entrypoint=internal Q; transitive=NONE.
-- Required: All six full-history digest fields
GRANT SELECT (type) ON TABLE public.flyway_schema_history TO flooow_offline_readiness_owner;
-- SPEC:1208 Q READ_PRIVILEGE; consumer=READINESS.history; entrypoint=internal Q; transitive=NONE.
-- Required: All six full-history digest fields
GRANT SELECT (script) ON TABLE public.flyway_schema_history TO flooow_offline_readiness_owner;
-- SPEC:1209 Q READ_PRIVILEGE; consumer=READINESS.history; entrypoint=internal Q; transitive=NONE.
-- Required: All six full-history digest fields
GRANT SELECT (checksum) ON TABLE public.flyway_schema_history TO flooow_offline_readiness_owner;
-- SPEC:1210 Q READ_PRIVILEGE; consumer=READINESS.history; entrypoint=internal Q; transitive=NONE.
-- Required: All six full-history digest fields
GRANT SELECT (success) ON TABLE public.flyway_schema_history TO flooow_offline_readiness_owner;
-- SPEC:1211 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (oid) ON TABLE pg_catalog.pg_roles TO flooow_offline_readiness_owner;
-- SPEC:1212 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (rolname) ON TABLE pg_catalog.pg_roles TO flooow_offline_readiness_owner;
-- SPEC:1213 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (rolsuper) ON TABLE pg_catalog.pg_roles TO flooow_offline_readiness_owner;
-- SPEC:1214 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (rolinherit) ON TABLE pg_catalog.pg_roles TO flooow_offline_readiness_owner;
-- SPEC:1215 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (rolcreaterole) ON TABLE pg_catalog.pg_roles TO flooow_offline_readiness_owner;
-- SPEC:1216 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (rolcreatedb) ON TABLE pg_catalog.pg_roles TO flooow_offline_readiness_owner;
-- SPEC:1217 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (rolcanlogin) ON TABLE pg_catalog.pg_roles TO flooow_offline_readiness_owner;
-- SPEC:1218 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (rolreplication) ON TABLE pg_catalog.pg_roles TO flooow_offline_readiness_owner;
-- SPEC:1219 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (rolbypassrls) ON TABLE pg_catalog.pg_roles TO flooow_offline_readiness_owner;
-- SPEC:1220 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (roleid) ON TABLE pg_catalog.pg_auth_members TO flooow_offline_readiness_owner;
-- SPEC:1221 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (member) ON TABLE pg_catalog.pg_auth_members TO flooow_offline_readiness_owner;
-- SPEC:1222 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (admin_option) ON TABLE pg_catalog.pg_auth_members TO flooow_offline_readiness_owner;
-- SPEC:1223 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (inherit_option) ON TABLE pg_catalog.pg_auth_members TO flooow_offline_readiness_owner;
-- SPEC:1224 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (set_option) ON TABLE pg_catalog.pg_auth_members TO flooow_offline_readiness_owner;
-- SPEC:1225 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (oid) ON TABLE pg_catalog.pg_proc TO flooow_offline_readiness_owner;
-- SPEC:1226 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (proname) ON TABLE pg_catalog.pg_proc TO flooow_offline_readiness_owner;
-- SPEC:1227 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (pronamespace) ON TABLE pg_catalog.pg_proc TO flooow_offline_readiness_owner;
-- SPEC:1228 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (proowner) ON TABLE pg_catalog.pg_proc TO flooow_offline_readiness_owner;
-- SPEC:1229 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (prokind) ON TABLE pg_catalog.pg_proc TO flooow_offline_readiness_owner;
-- SPEC:1230 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (prosecdef) ON TABLE pg_catalog.pg_proc TO flooow_offline_readiness_owner;
-- SPEC:1231 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (proisstrict) ON TABLE pg_catalog.pg_proc TO flooow_offline_readiness_owner;
-- SPEC:1232 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (proretset) ON TABLE pg_catalog.pg_proc TO flooow_offline_readiness_owner;
-- SPEC:1233 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (provolatile) ON TABLE pg_catalog.pg_proc TO flooow_offline_readiness_owner;
-- SPEC:1234 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (pronargs) ON TABLE pg_catalog.pg_proc TO flooow_offline_readiness_owner;
-- SPEC:1235 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (pronargdefaults) ON TABLE pg_catalog.pg_proc TO flooow_offline_readiness_owner;
-- SPEC:1236 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (prorettype) ON TABLE pg_catalog.pg_proc TO flooow_offline_readiness_owner;
-- SPEC:1237 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (proargtypes) ON TABLE pg_catalog.pg_proc TO flooow_offline_readiness_owner;
-- SPEC:1238 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (proallargtypes) ON TABLE pg_catalog.pg_proc TO flooow_offline_readiness_owner;
-- SPEC:1239 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (proargmodes) ON TABLE pg_catalog.pg_proc TO flooow_offline_readiness_owner;
-- SPEC:1240 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (proargnames) ON TABLE pg_catalog.pg_proc TO flooow_offline_readiness_owner;
-- SPEC:1241 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (provariadic) ON TABLE pg_catalog.pg_proc TO flooow_offline_readiness_owner;
-- SPEC:1242 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (proconfig) ON TABLE pg_catalog.pg_proc TO flooow_offline_readiness_owner;
-- SPEC:1243 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (proacl) ON TABLE pg_catalog.pg_proc TO flooow_offline_readiness_owner;
-- SPEC:1244 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (oid) ON TABLE pg_catalog.pg_namespace TO flooow_offline_readiness_owner;
-- SPEC:1245 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (nspname) ON TABLE pg_catalog.pg_namespace TO flooow_offline_readiness_owner;
-- SPEC:1246 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (nspowner) ON TABLE pg_catalog.pg_namespace TO flooow_offline_readiness_owner;
-- SPEC:1247 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (nspacl) ON TABLE pg_catalog.pg_namespace TO flooow_offline_readiness_owner;
-- SPEC:1248 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (oid) ON TABLE pg_catalog.pg_class TO flooow_offline_readiness_owner;
-- SPEC:1249 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (relname) ON TABLE pg_catalog.pg_class TO flooow_offline_readiness_owner;
-- SPEC:1250 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (relnamespace) ON TABLE pg_catalog.pg_class TO flooow_offline_readiness_owner;
-- SPEC:1251 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (relowner) ON TABLE pg_catalog.pg_class TO flooow_offline_readiness_owner;
-- SPEC:1252 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (relkind) ON TABLE pg_catalog.pg_class TO flooow_offline_readiness_owner;
-- SPEC:1253 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (relacl) ON TABLE pg_catalog.pg_class TO flooow_offline_readiness_owner;
-- SPEC:1254 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (attrelid) ON TABLE pg_catalog.pg_attribute TO flooow_offline_readiness_owner;
-- SPEC:1255 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (attname) ON TABLE pg_catalog.pg_attribute TO flooow_offline_readiness_owner;
-- SPEC:1256 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (attnum) ON TABLE pg_catalog.pg_attribute TO flooow_offline_readiness_owner;
-- SPEC:1257 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (attisdropped) ON TABLE pg_catalog.pg_attribute TO flooow_offline_readiness_owner;
-- SPEC:1258 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (attacl) ON TABLE pg_catalog.pg_attribute TO flooow_offline_readiness_owner;
-- SPEC:1259 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (defaclrole) ON TABLE pg_catalog.pg_default_acl TO flooow_offline_readiness_owner;
-- SPEC:1260 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (defaclnamespace) ON TABLE pg_catalog.pg_default_acl TO flooow_offline_readiness_owner;
-- SPEC:1261 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (defaclobjtype) ON TABLE pg_catalog.pg_default_acl TO flooow_offline_readiness_owner;
-- SPEC:1262 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (defaclacl) ON TABLE pg_catalog.pg_default_acl TO flooow_offline_readiness_owner;
-- SPEC:1263 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (oid) ON TABLE pg_catalog.pg_database TO flooow_offline_readiness_owner;
-- SPEC:1264 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (datname) ON TABLE pg_catalog.pg_database TO flooow_offline_readiness_owner;
-- SPEC:1265 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (datdba) ON TABLE pg_catalog.pg_database TO flooow_offline_readiness_owner;
-- SPEC:1266 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (datacl) ON TABLE pg_catalog.pg_database TO flooow_offline_readiness_owner;
-- SPEC:1267 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (oid) ON TABLE pg_catalog.pg_type TO flooow_offline_readiness_owner;
-- SPEC:1268 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (typname) ON TABLE pg_catalog.pg_type TO flooow_offline_readiness_owner;
-- SPEC:1269 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (typnamespace) ON TABLE pg_catalog.pg_type TO flooow_offline_readiness_owner;
-- SPEC:1270 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (typtype) ON TABLE pg_catalog.pg_type TO flooow_offline_readiness_owner;
-- SPEC:1271 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (typelem) ON TABLE pg_catalog.pg_type TO flooow_offline_readiness_owner;
-- SPEC:1272 Q READ_PRIVILEGE; consumer=READINESS.ACL22.1; entrypoint=internal Q; transitive=Metadata/privilege checks only.
-- Required: Exact name/type/owner/ACL/attribute/membership/default projection field or catalog join key
GRANT SELECT (typarray) ON TABLE pg_catalog.pg_type TO flooow_offline_readiness_owner;
-- SPEC:1274 V READ_PRIVILEGE; consumer=GUARD-V / BH; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (binding_schema_version) ON TABLE public.offline_binding_header TO flooow_offline_verification_owner;
-- SPEC:1275 V READ_PRIVILEGE; consumer=GUARD-V / BH; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (binding_id) ON TABLE public.offline_binding_header TO flooow_offline_verification_owner;
-- SPEC:1276 V READ_PRIVILEGE; consumer=GUARD-V / BH; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (deployment_id) ON TABLE public.offline_binding_header TO flooow_offline_verification_owner;
-- SPEC:1277 V READ_PRIVILEGE; consumer=GUARD-V / BH; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (deployment_incarnation_id) ON TABLE public.offline_binding_header TO flooow_offline_verification_owner;
-- SPEC:1278 V READ_PRIVILEGE; consumer=GUARD-V / BH; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (run_id) ON TABLE public.offline_binding_header TO flooow_offline_verification_owner;
-- SPEC:1279 V READ_PRIVILEGE; consumer=GUARD-V / BH; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (plan_id) ON TABLE public.offline_binding_header TO flooow_offline_verification_owner;
-- SPEC:1280 V READ_PRIVILEGE; consumer=GUARD-V / BH; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (execution_plan_version) ON TABLE public.offline_binding_header TO flooow_offline_verification_owner;
-- SPEC:1281 V READ_PRIVILEGE; consumer=GUARD-V / BH; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (organization_id) ON TABLE public.offline_binding_header TO flooow_offline_verification_owner;
-- SPEC:1282 V READ_PRIVILEGE; consumer=GUARD-V / BH; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (manifest_id) ON TABLE public.offline_binding_header TO flooow_offline_verification_owner;
-- SPEC:1283 V READ_PRIVILEGE; consumer=GUARD-V / BH; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (manifest_digest) ON TABLE public.offline_binding_header TO flooow_offline_verification_owner;
-- SPEC:1284 V READ_PRIVILEGE; consumer=GUARD-V / BH; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (canonical_manifest_hash) ON TABLE public.offline_binding_header TO flooow_offline_verification_owner;
-- SPEC:1285 V READ_PRIVILEGE; consumer=GUARD-V / BH; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (canonical_manifest_encoding_version) ON TABLE public.offline_binding_header TO flooow_offline_verification_owner;
-- SPEC:1286 V READ_PRIVILEGE; consumer=GUARD-V / BH; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (mercado_livre_connection_id) ON TABLE public.offline_binding_header TO flooow_offline_verification_owner;
-- SPEC:1287 V READ_PRIVILEGE; consumer=GUARD-V / BH; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (omie_connection_id) ON TABLE public.offline_binding_header TO flooow_offline_verification_owner;
-- SPEC:1288 V READ_PRIVILEGE; consumer=GUARD-V / BH; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (marketplace_order_id) ON TABLE public.offline_binding_header TO flooow_offline_verification_owner;
-- SPEC:1289 V READ_PRIVILEGE; consumer=GUARD-V / BH; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (source_order_reference) ON TABLE public.offline_binding_header TO flooow_offline_verification_owner;
-- SPEC:1290 V READ_PRIVILEGE; consumer=GUARD-V / BH; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (integration_reference) ON TABLE public.offline_binding_header TO flooow_offline_verification_owner;
-- SPEC:1291 V READ_PRIVILEGE; consumer=GUARD-V / BH; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (permission) ON TABLE public.offline_binding_header TO flooow_offline_verification_owner;
-- SPEC:1292 V READ_PRIVILEGE; consumer=GUARD-V / BH; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (reason) ON TABLE public.offline_binding_header TO flooow_offline_verification_owner;
-- SPEC:1293 V READ_PRIVILEGE; consumer=GUARD-V / BH; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (provenance) ON TABLE public.offline_binding_header TO flooow_offline_verification_owner;
-- SPEC:1294 V READ_PRIVILEGE; consumer=GUARD-V / BH; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (principal_id) ON TABLE public.offline_binding_header TO flooow_offline_verification_owner;
-- SPEC:1295 V READ_PRIVILEGE; consumer=GUARD-V / BH; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (credential_id) ON TABLE public.offline_binding_header TO flooow_offline_verification_owner;
-- SPEC:1296 V READ_PRIVILEGE; consumer=GUARD-V / BH; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (grant_id) ON TABLE public.offline_binding_header TO flooow_offline_verification_owner;
-- SPEC:1297 V READ_PRIVILEGE; consumer=GUARD-V / BH; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (decision_id) ON TABLE public.offline_binding_header TO flooow_offline_verification_owner;
-- SPEC:1298 V READ_PRIVILEGE; consumer=GUARD-V / BH; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (correlation_id) ON TABLE public.offline_binding_header TO flooow_offline_verification_owner;
-- SPEC:1299 V READ_PRIVILEGE; consumer=GUARD-V / BH; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (principal_operation_id) ON TABLE public.offline_binding_header TO flooow_offline_verification_owner;
-- SPEC:1300 V READ_PRIVILEGE; consumer=GUARD-V / BH; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (credential_operation_id) ON TABLE public.offline_binding_header TO flooow_offline_verification_owner;
-- SPEC:1301 V READ_PRIVILEGE; consumer=GUARD-V / BH; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (grant_operation_id) ON TABLE public.offline_binding_header TO flooow_offline_verification_owner;
-- SPEC:1302 V READ_PRIVILEGE; consumer=GUARD-V / BH; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (issued_at) ON TABLE public.offline_binding_header TO flooow_offline_verification_owner;
-- SPEC:1303 V READ_PRIVILEGE; consumer=GUARD-V / BH; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (valid_from) ON TABLE public.offline_binding_header TO flooow_offline_verification_owner;
-- SPEC:1304 V READ_PRIVILEGE; consumer=GUARD-V / BH; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (expires_at) ON TABLE public.offline_binding_header TO flooow_offline_verification_owner;
-- SPEC:1305 V READ_PRIVILEGE; consumer=GUARD-V / BH; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (identity_slots) ON TABLE public.offline_binding_header TO flooow_offline_verification_owner;
-- SPEC:1306 V READ_PRIVILEGE; consumer=GUARD-V / BH; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (offline_surface_version) ON TABLE public.offline_binding_header TO flooow_offline_verification_owner;
-- SPEC:1307 V READ_PRIVILEGE; consumer=GUARD-V / BH; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (deadline_policy_version) ON TABLE public.offline_binding_header TO flooow_offline_verification_owner;
-- SPEC:1308 V READ_PRIVILEGE; consumer=GUARD-V / BH; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (deadline_policy_digest) ON TABLE public.offline_binding_header TO flooow_offline_verification_owner;
-- SPEC:1309 V READ_PRIVILEGE; consumer=GUARD-V / BH; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (admission_contract_version) ON TABLE public.offline_binding_header TO flooow_offline_verification_owner;
-- SPEC:1310 V READ_PRIVILEGE; consumer=GUARD-V / BH; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (delivery_contract_version) ON TABLE public.offline_binding_header TO flooow_offline_verification_owner;
-- SPEC:1311 V READ_PRIVILEGE; consumer=GUARD-V / BH; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (reconciliation_contract_version) ON TABLE public.offline_binding_header TO flooow_offline_verification_owner;
-- SPEC:1312 V READ_PRIVILEGE; consumer=GUARD-V / BH; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (plan_fingerprint) ON TABLE public.offline_binding_header TO flooow_offline_verification_owner;
-- SPEC:1313 V READ_PRIVILEGE; consumer=GUARD-V / BH; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (canonical_manifest_bytes) ON TABLE public.offline_binding_header TO flooow_offline_verification_owner;
-- SPEC:1314 I READ_PRIVILEGE; consumer=GUARD-I / BH; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (binding_schema_version) ON TABLE public.offline_binding_header TO flooow_offline_issuance_owner;
-- SPEC:1315 I READ_PRIVILEGE; consumer=GUARD-I / BH; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (binding_id) ON TABLE public.offline_binding_header TO flooow_offline_issuance_owner;
-- SPEC:1316 I READ_PRIVILEGE; consumer=GUARD-I / BH; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (deployment_id) ON TABLE public.offline_binding_header TO flooow_offline_issuance_owner;
-- SPEC:1317 I READ_PRIVILEGE; consumer=GUARD-I / BH; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (deployment_incarnation_id) ON TABLE public.offline_binding_header TO flooow_offline_issuance_owner;
-- SPEC:1318 I READ_PRIVILEGE; consumer=GUARD-I / BH; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (run_id) ON TABLE public.offline_binding_header TO flooow_offline_issuance_owner;
-- SPEC:1319 I READ_PRIVILEGE; consumer=GUARD-I / BH; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (plan_id) ON TABLE public.offline_binding_header TO flooow_offline_issuance_owner;
-- SPEC:1320 I READ_PRIVILEGE; consumer=GUARD-I / BH; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (execution_plan_version) ON TABLE public.offline_binding_header TO flooow_offline_issuance_owner;
-- SPEC:1321 I READ_PRIVILEGE; consumer=GUARD-I / BH; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (organization_id) ON TABLE public.offline_binding_header TO flooow_offline_issuance_owner;
-- SPEC:1322 I READ_PRIVILEGE; consumer=GUARD-I / BH; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (manifest_id) ON TABLE public.offline_binding_header TO flooow_offline_issuance_owner;
-- SPEC:1323 I READ_PRIVILEGE; consumer=GUARD-I / BH; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (manifest_digest) ON TABLE public.offline_binding_header TO flooow_offline_issuance_owner;
-- SPEC:1324 I READ_PRIVILEGE; consumer=GUARD-I / BH; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (canonical_manifest_hash) ON TABLE public.offline_binding_header TO flooow_offline_issuance_owner;
-- SPEC:1325 I READ_PRIVILEGE; consumer=GUARD-I / BH; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (canonical_manifest_encoding_version) ON TABLE public.offline_binding_header TO flooow_offline_issuance_owner;
-- SPEC:1326 I READ_PRIVILEGE; consumer=GUARD-I / BH; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (mercado_livre_connection_id) ON TABLE public.offline_binding_header TO flooow_offline_issuance_owner;
-- SPEC:1327 I READ_PRIVILEGE; consumer=GUARD-I / BH; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (omie_connection_id) ON TABLE public.offline_binding_header TO flooow_offline_issuance_owner;
-- SPEC:1328 I READ_PRIVILEGE; consumer=GUARD-I / BH; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (marketplace_order_id) ON TABLE public.offline_binding_header TO flooow_offline_issuance_owner;
-- SPEC:1329 I READ_PRIVILEGE; consumer=GUARD-I / BH; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (source_order_reference) ON TABLE public.offline_binding_header TO flooow_offline_issuance_owner;
-- SPEC:1330 I READ_PRIVILEGE; consumer=GUARD-I / BH; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (integration_reference) ON TABLE public.offline_binding_header TO flooow_offline_issuance_owner;
-- SPEC:1331 I READ_PRIVILEGE; consumer=GUARD-I / BH; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (permission) ON TABLE public.offline_binding_header TO flooow_offline_issuance_owner;
-- SPEC:1332 I READ_PRIVILEGE; consumer=GUARD-I / BH; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (reason) ON TABLE public.offline_binding_header TO flooow_offline_issuance_owner;
-- SPEC:1333 I READ_PRIVILEGE; consumer=GUARD-I / BH; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (provenance) ON TABLE public.offline_binding_header TO flooow_offline_issuance_owner;
-- SPEC:1334 I READ_PRIVILEGE; consumer=GUARD-I / BH; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (principal_id) ON TABLE public.offline_binding_header TO flooow_offline_issuance_owner;
-- SPEC:1335 I READ_PRIVILEGE; consumer=GUARD-I / BH; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (credential_id) ON TABLE public.offline_binding_header TO flooow_offline_issuance_owner;
-- SPEC:1336 I READ_PRIVILEGE; consumer=GUARD-I / BH; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (grant_id) ON TABLE public.offline_binding_header TO flooow_offline_issuance_owner;
-- SPEC:1337 I READ_PRIVILEGE; consumer=GUARD-I / BH; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (decision_id) ON TABLE public.offline_binding_header TO flooow_offline_issuance_owner;
-- SPEC:1338 I READ_PRIVILEGE; consumer=GUARD-I / BH; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (correlation_id) ON TABLE public.offline_binding_header TO flooow_offline_issuance_owner;
-- SPEC:1339 I READ_PRIVILEGE; consumer=GUARD-I / BH; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (principal_operation_id) ON TABLE public.offline_binding_header TO flooow_offline_issuance_owner;
-- SPEC:1340 I READ_PRIVILEGE; consumer=GUARD-I / BH; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (credential_operation_id) ON TABLE public.offline_binding_header TO flooow_offline_issuance_owner;
-- SPEC:1341 I READ_PRIVILEGE; consumer=GUARD-I / BH; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (grant_operation_id) ON TABLE public.offline_binding_header TO flooow_offline_issuance_owner;
-- SPEC:1342 I READ_PRIVILEGE; consumer=GUARD-I / BH; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (issued_at) ON TABLE public.offline_binding_header TO flooow_offline_issuance_owner;
-- SPEC:1343 I READ_PRIVILEGE; consumer=GUARD-I / BH; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (valid_from) ON TABLE public.offline_binding_header TO flooow_offline_issuance_owner;
-- SPEC:1344 I READ_PRIVILEGE; consumer=GUARD-I / BH; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (expires_at) ON TABLE public.offline_binding_header TO flooow_offline_issuance_owner;
-- SPEC:1345 I READ_PRIVILEGE; consumer=GUARD-I / BH; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (identity_slots) ON TABLE public.offline_binding_header TO flooow_offline_issuance_owner;
-- SPEC:1346 I READ_PRIVILEGE; consumer=GUARD-I / BH; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (offline_surface_version) ON TABLE public.offline_binding_header TO flooow_offline_issuance_owner;
-- SPEC:1347 I READ_PRIVILEGE; consumer=GUARD-I / BH; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (deadline_policy_version) ON TABLE public.offline_binding_header TO flooow_offline_issuance_owner;
-- SPEC:1348 I READ_PRIVILEGE; consumer=GUARD-I / BH; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (deadline_policy_digest) ON TABLE public.offline_binding_header TO flooow_offline_issuance_owner;
-- SPEC:1349 I READ_PRIVILEGE; consumer=GUARD-I / BH; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (admission_contract_version) ON TABLE public.offline_binding_header TO flooow_offline_issuance_owner;
-- SPEC:1350 I READ_PRIVILEGE; consumer=GUARD-I / BH; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (delivery_contract_version) ON TABLE public.offline_binding_header TO flooow_offline_issuance_owner;
-- SPEC:1351 I READ_PRIVILEGE; consumer=GUARD-I / BH; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (reconciliation_contract_version) ON TABLE public.offline_binding_header TO flooow_offline_issuance_owner;
-- SPEC:1352 I READ_PRIVILEGE; consumer=GUARD-I / BH; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (plan_fingerprint) ON TABLE public.offline_binding_header TO flooow_offline_issuance_owner;
-- SPEC:1353 I READ_PRIVILEGE; consumer=GUARD-I / BH; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (canonical_manifest_bytes) ON TABLE public.offline_binding_header TO flooow_offline_issuance_owner;
-- SPEC:1354 E READ_PRIVILEGE; consumer=GUARD-E / BH; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (binding_schema_version) ON TABLE public.offline_binding_header TO flooow_offline_execution_owner;
-- SPEC:1355 E READ_PRIVILEGE; consumer=GUARD-E / BH; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (binding_id) ON TABLE public.offline_binding_header TO flooow_offline_execution_owner;
-- SPEC:1356 E READ_PRIVILEGE; consumer=GUARD-E / BH; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (deployment_id) ON TABLE public.offline_binding_header TO flooow_offline_execution_owner;
-- SPEC:1357 E READ_PRIVILEGE; consumer=GUARD-E / BH; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (deployment_incarnation_id) ON TABLE public.offline_binding_header TO flooow_offline_execution_owner;
-- SPEC:1358 E READ_PRIVILEGE; consumer=GUARD-E / BH; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (run_id) ON TABLE public.offline_binding_header TO flooow_offline_execution_owner;
-- SPEC:1359 E READ_PRIVILEGE; consumer=GUARD-E / BH; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (plan_id) ON TABLE public.offline_binding_header TO flooow_offline_execution_owner;
-- SPEC:1360 E READ_PRIVILEGE; consumer=GUARD-E / BH; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (execution_plan_version) ON TABLE public.offline_binding_header TO flooow_offline_execution_owner;
-- SPEC:1361 E READ_PRIVILEGE; consumer=GUARD-E / BH; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (organization_id) ON TABLE public.offline_binding_header TO flooow_offline_execution_owner;
-- SPEC:1362 E READ_PRIVILEGE; consumer=GUARD-E / BH; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (manifest_id) ON TABLE public.offline_binding_header TO flooow_offline_execution_owner;
-- SPEC:1363 E READ_PRIVILEGE; consumer=GUARD-E / BH; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (manifest_digest) ON TABLE public.offline_binding_header TO flooow_offline_execution_owner;
-- SPEC:1364 E READ_PRIVILEGE; consumer=GUARD-E / BH; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (canonical_manifest_hash) ON TABLE public.offline_binding_header TO flooow_offline_execution_owner;
-- SPEC:1365 E READ_PRIVILEGE; consumer=GUARD-E / BH; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (canonical_manifest_encoding_version) ON TABLE public.offline_binding_header TO flooow_offline_execution_owner;
-- SPEC:1366 E READ_PRIVILEGE; consumer=GUARD-E / BH; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (mercado_livre_connection_id) ON TABLE public.offline_binding_header TO flooow_offline_execution_owner;
-- SPEC:1367 E READ_PRIVILEGE; consumer=GUARD-E / BH; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (omie_connection_id) ON TABLE public.offline_binding_header TO flooow_offline_execution_owner;
-- SPEC:1368 E READ_PRIVILEGE; consumer=GUARD-E / BH; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (marketplace_order_id) ON TABLE public.offline_binding_header TO flooow_offline_execution_owner;
-- SPEC:1369 E READ_PRIVILEGE; consumer=GUARD-E / BH; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (source_order_reference) ON TABLE public.offline_binding_header TO flooow_offline_execution_owner;
-- SPEC:1370 E READ_PRIVILEGE; consumer=GUARD-E / BH; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (integration_reference) ON TABLE public.offline_binding_header TO flooow_offline_execution_owner;
-- SPEC:1371 E READ_PRIVILEGE; consumer=GUARD-E / BH; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (permission) ON TABLE public.offline_binding_header TO flooow_offline_execution_owner;
-- SPEC:1372 E READ_PRIVILEGE; consumer=GUARD-E / BH; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (reason) ON TABLE public.offline_binding_header TO flooow_offline_execution_owner;
-- SPEC:1373 E READ_PRIVILEGE; consumer=GUARD-E / BH; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (provenance) ON TABLE public.offline_binding_header TO flooow_offline_execution_owner;
-- SPEC:1374 E READ_PRIVILEGE; consumer=GUARD-E / BH; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (principal_id) ON TABLE public.offline_binding_header TO flooow_offline_execution_owner;
-- SPEC:1375 E READ_PRIVILEGE; consumer=GUARD-E / BH; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (credential_id) ON TABLE public.offline_binding_header TO flooow_offline_execution_owner;
-- SPEC:1376 E READ_PRIVILEGE; consumer=GUARD-E / BH; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (grant_id) ON TABLE public.offline_binding_header TO flooow_offline_execution_owner;
-- SPEC:1377 E READ_PRIVILEGE; consumer=GUARD-E / BH; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (decision_id) ON TABLE public.offline_binding_header TO flooow_offline_execution_owner;
-- SPEC:1378 E READ_PRIVILEGE; consumer=GUARD-E / BH; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (correlation_id) ON TABLE public.offline_binding_header TO flooow_offline_execution_owner;
-- SPEC:1379 E READ_PRIVILEGE; consumer=GUARD-E / BH; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (principal_operation_id) ON TABLE public.offline_binding_header TO flooow_offline_execution_owner;
-- SPEC:1380 E READ_PRIVILEGE; consumer=GUARD-E / BH; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (credential_operation_id) ON TABLE public.offline_binding_header TO flooow_offline_execution_owner;
-- SPEC:1381 E READ_PRIVILEGE; consumer=GUARD-E / BH; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (grant_operation_id) ON TABLE public.offline_binding_header TO flooow_offline_execution_owner;
-- SPEC:1382 E READ_PRIVILEGE; consumer=GUARD-E / BH; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (issued_at) ON TABLE public.offline_binding_header TO flooow_offline_execution_owner;
-- SPEC:1383 E READ_PRIVILEGE; consumer=GUARD-E / BH; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (valid_from) ON TABLE public.offline_binding_header TO flooow_offline_execution_owner;
-- SPEC:1384 E READ_PRIVILEGE; consumer=GUARD-E / BH; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (expires_at) ON TABLE public.offline_binding_header TO flooow_offline_execution_owner;
-- SPEC:1385 E READ_PRIVILEGE; consumer=GUARD-E / BH; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (identity_slots) ON TABLE public.offline_binding_header TO flooow_offline_execution_owner;
-- SPEC:1386 E READ_PRIVILEGE; consumer=GUARD-E / BH; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (offline_surface_version) ON TABLE public.offline_binding_header TO flooow_offline_execution_owner;
-- SPEC:1387 E READ_PRIVILEGE; consumer=GUARD-E / BH; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (deadline_policy_version) ON TABLE public.offline_binding_header TO flooow_offline_execution_owner;
-- SPEC:1388 E READ_PRIVILEGE; consumer=GUARD-E / BH; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (deadline_policy_digest) ON TABLE public.offline_binding_header TO flooow_offline_execution_owner;
-- SPEC:1389 E READ_PRIVILEGE; consumer=GUARD-E / BH; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (admission_contract_version) ON TABLE public.offline_binding_header TO flooow_offline_execution_owner;
-- SPEC:1390 E READ_PRIVILEGE; consumer=GUARD-E / BH; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (delivery_contract_version) ON TABLE public.offline_binding_header TO flooow_offline_execution_owner;
-- SPEC:1391 E READ_PRIVILEGE; consumer=GUARD-E / BH; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (reconciliation_contract_version) ON TABLE public.offline_binding_header TO flooow_offline_execution_owner;
-- SPEC:1392 E READ_PRIVILEGE; consumer=GUARD-E / BH; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (plan_fingerprint) ON TABLE public.offline_binding_header TO flooow_offline_execution_owner;
-- SPEC:1393 E READ_PRIVILEGE; consumer=GUARD-E / BH; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (canonical_manifest_bytes) ON TABLE public.offline_binding_header TO flooow_offline_execution_owner;
-- SPEC:1394 A READ_PRIVILEGE; consumer=GUARD-A/INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (binding_schema_version) ON TABLE public.offline_binding_header TO flooow_offline_audit_owner;
-- SPEC:1395 A READ_PRIVILEGE; consumer=GUARD-A/INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (binding_id) ON TABLE public.offline_binding_header TO flooow_offline_audit_owner;
-- SPEC:1396 A READ_PRIVILEGE; consumer=GUARD-A/INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (deployment_id) ON TABLE public.offline_binding_header TO flooow_offline_audit_owner;
-- SPEC:1397 A READ_PRIVILEGE; consumer=GUARD-A/INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (deployment_incarnation_id) ON TABLE public.offline_binding_header TO flooow_offline_audit_owner;
-- SPEC:1398 A READ_PRIVILEGE; consumer=GUARD-A/INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (run_id) ON TABLE public.offline_binding_header TO flooow_offline_audit_owner;
-- SPEC:1399 A READ_PRIVILEGE; consumer=GUARD-A/INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (plan_id) ON TABLE public.offline_binding_header TO flooow_offline_audit_owner;
-- SPEC:1400 A READ_PRIVILEGE; consumer=GUARD-A/INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (execution_plan_version) ON TABLE public.offline_binding_header TO flooow_offline_audit_owner;
-- SPEC:1401 A READ_PRIVILEGE; consumer=GUARD-A/INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (organization_id) ON TABLE public.offline_binding_header TO flooow_offline_audit_owner;
-- SPEC:1402 A READ_PRIVILEGE; consumer=GUARD-A/INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (manifest_id) ON TABLE public.offline_binding_header TO flooow_offline_audit_owner;
-- SPEC:1403 A READ_PRIVILEGE; consumer=GUARD-A/INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (manifest_digest) ON TABLE public.offline_binding_header TO flooow_offline_audit_owner;
-- SPEC:1404 A READ_PRIVILEGE; consumer=GUARD-A/INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (canonical_manifest_hash) ON TABLE public.offline_binding_header TO flooow_offline_audit_owner;
-- SPEC:1405 A READ_PRIVILEGE; consumer=GUARD-A/INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (canonical_manifest_encoding_version) ON TABLE public.offline_binding_header TO flooow_offline_audit_owner;
-- SPEC:1406 A READ_PRIVILEGE; consumer=GUARD-A/INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (mercado_livre_connection_id) ON TABLE public.offline_binding_header TO flooow_offline_audit_owner;
-- SPEC:1407 A READ_PRIVILEGE; consumer=GUARD-A/INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (omie_connection_id) ON TABLE public.offline_binding_header TO flooow_offline_audit_owner;
-- SPEC:1408 A READ_PRIVILEGE; consumer=GUARD-A/INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (marketplace_order_id) ON TABLE public.offline_binding_header TO flooow_offline_audit_owner;
-- SPEC:1409 A READ_PRIVILEGE; consumer=GUARD-A/INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (source_order_reference) ON TABLE public.offline_binding_header TO flooow_offline_audit_owner;
-- SPEC:1410 A READ_PRIVILEGE; consumer=GUARD-A/INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (integration_reference) ON TABLE public.offline_binding_header TO flooow_offline_audit_owner;
-- SPEC:1411 A READ_PRIVILEGE; consumer=GUARD-A/INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (permission) ON TABLE public.offline_binding_header TO flooow_offline_audit_owner;
-- SPEC:1412 A READ_PRIVILEGE; consumer=GUARD-A/INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (reason) ON TABLE public.offline_binding_header TO flooow_offline_audit_owner;
-- SPEC:1413 A READ_PRIVILEGE; consumer=GUARD-A/INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (provenance) ON TABLE public.offline_binding_header TO flooow_offline_audit_owner;
-- SPEC:1414 A READ_PRIVILEGE; consumer=GUARD-A/INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (principal_id) ON TABLE public.offline_binding_header TO flooow_offline_audit_owner;
-- SPEC:1415 A READ_PRIVILEGE; consumer=GUARD-A/INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (credential_id) ON TABLE public.offline_binding_header TO flooow_offline_audit_owner;
-- SPEC:1416 A READ_PRIVILEGE; consumer=GUARD-A/INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (grant_id) ON TABLE public.offline_binding_header TO flooow_offline_audit_owner;
-- SPEC:1417 A READ_PRIVILEGE; consumer=GUARD-A/INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (decision_id) ON TABLE public.offline_binding_header TO flooow_offline_audit_owner;
-- SPEC:1418 A READ_PRIVILEGE; consumer=GUARD-A/INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (correlation_id) ON TABLE public.offline_binding_header TO flooow_offline_audit_owner;
-- SPEC:1419 A READ_PRIVILEGE; consumer=GUARD-A/INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (principal_operation_id) ON TABLE public.offline_binding_header TO flooow_offline_audit_owner;
-- SPEC:1420 A READ_PRIVILEGE; consumer=GUARD-A/INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (credential_operation_id) ON TABLE public.offline_binding_header TO flooow_offline_audit_owner;
-- SPEC:1421 A READ_PRIVILEGE; consumer=GUARD-A/INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (grant_operation_id) ON TABLE public.offline_binding_header TO flooow_offline_audit_owner;
-- SPEC:1422 A READ_PRIVILEGE; consumer=GUARD-A/INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (issued_at) ON TABLE public.offline_binding_header TO flooow_offline_audit_owner;
-- SPEC:1423 A READ_PRIVILEGE; consumer=GUARD-A/INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (valid_from) ON TABLE public.offline_binding_header TO flooow_offline_audit_owner;
-- SPEC:1424 A READ_PRIVILEGE; consumer=GUARD-A/INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (expires_at) ON TABLE public.offline_binding_header TO flooow_offline_audit_owner;
-- SPEC:1425 A READ_PRIVILEGE; consumer=GUARD-A/INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (identity_slots) ON TABLE public.offline_binding_header TO flooow_offline_audit_owner;
-- SPEC:1426 A READ_PRIVILEGE; consumer=GUARD-A/INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (offline_surface_version) ON TABLE public.offline_binding_header TO flooow_offline_audit_owner;
-- SPEC:1427 A READ_PRIVILEGE; consumer=GUARD-A/INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (deadline_policy_version) ON TABLE public.offline_binding_header TO flooow_offline_audit_owner;
-- SPEC:1428 A READ_PRIVILEGE; consumer=GUARD-A/INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (deadline_policy_digest) ON TABLE public.offline_binding_header TO flooow_offline_audit_owner;
-- SPEC:1429 A READ_PRIVILEGE; consumer=GUARD-A/INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (admission_contract_version) ON TABLE public.offline_binding_header TO flooow_offline_audit_owner;
-- SPEC:1430 A READ_PRIVILEGE; consumer=GUARD-A/INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (delivery_contract_version) ON TABLE public.offline_binding_header TO flooow_offline_audit_owner;
-- SPEC:1431 A READ_PRIVILEGE; consumer=GUARD-A/INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (reconciliation_contract_version) ON TABLE public.offline_binding_header TO flooow_offline_audit_owner;
-- SPEC:1432 A READ_PRIVILEGE; consumer=GUARD-A/INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (plan_fingerprint) ON TABLE public.offline_binding_header TO flooow_offline_audit_owner;
-- SPEC:1433 A READ_PRIVILEGE; consumer=GUARD-A/INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact immutable38-tag recomputation, canonical manifest hash/agreement and scoped guard/declared projection
GRANT SELECT (canonical_manifest_bytes) ON TABLE public.offline_binding_header TO flooow_offline_audit_owner;
-- SPEC:1434 P READ_PRIVILEGE; consumer=GUARD-P/P.boundPrincipal; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: Authentic bound executor/M scope/time and derived principal row lock
GRANT SELECT (binding_id) ON TABLE public.offline_binding_header TO flooow_offline_principal_lock_owner;
-- SPEC:1435 P READ_PRIVILEGE; consumer=GUARD-P/P.boundPrincipal; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: Authentic bound executor/M scope/time and derived principal row lock
GRANT SELECT (deployment_id) ON TABLE public.offline_binding_header TO flooow_offline_principal_lock_owner;
-- SPEC:1436 P READ_PRIVILEGE; consumer=GUARD-P/P.boundPrincipal; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: Authentic bound executor/M scope/time and derived principal row lock
GRANT SELECT (deployment_incarnation_id) ON TABLE public.offline_binding_header TO flooow_offline_principal_lock_owner;
-- SPEC:1437 P READ_PRIVILEGE; consumer=GUARD-P/P.boundPrincipal; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: Authentic bound executor/M scope/time and derived principal row lock
GRANT SELECT (identity_slots) ON TABLE public.offline_binding_header TO flooow_offline_principal_lock_owner;
-- SPEC:1438 P READ_PRIVILEGE; consumer=GUARD-P/P.boundPrincipal; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: Authentic bound executor/M scope/time and derived principal row lock
GRANT SELECT (offline_surface_version) ON TABLE public.offline_binding_header TO flooow_offline_principal_lock_owner;
-- SPEC:1439 P READ_PRIVILEGE; consumer=GUARD-P/P.boundPrincipal; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: Authentic bound executor/M scope/time and derived principal row lock
GRANT SELECT (deadline_policy_version) ON TABLE public.offline_binding_header TO flooow_offline_principal_lock_owner;
-- SPEC:1440 P READ_PRIVILEGE; consumer=GUARD-P/P.boundPrincipal; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: Authentic bound executor/M scope/time and derived principal row lock
GRANT SELECT (deadline_policy_digest) ON TABLE public.offline_binding_header TO flooow_offline_principal_lock_owner;
-- SPEC:1441 P READ_PRIVILEGE; consumer=GUARD-P/P.boundPrincipal; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: Authentic bound executor/M scope/time and derived principal row lock
GRANT SELECT (plan_fingerprint) ON TABLE public.offline_binding_header TO flooow_offline_principal_lock_owner;
-- SPEC:1442 P READ_PRIVILEGE; consumer=GUARD-P/P.boundPrincipal; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: Authentic bound executor/M scope/time and derived principal row lock
GRANT SELECT (organization_id) ON TABLE public.offline_binding_header TO flooow_offline_principal_lock_owner;
-- SPEC:1443 P READ_PRIVILEGE; consumer=GUARD-P/P.boundPrincipal; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: Authentic bound executor/M scope/time and derived principal row lock
GRANT SELECT (principal_id) ON TABLE public.offline_binding_header TO flooow_offline_principal_lock_owner;
-- SPEC:1444 P READ_PRIVILEGE; consumer=GUARD-P/P.boundPrincipal; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: Authentic bound executor/M scope/time and derived principal row lock
GRANT SELECT (mercado_livre_connection_id) ON TABLE public.offline_binding_header TO flooow_offline_principal_lock_owner;
-- SPEC:1445 P READ_PRIVILEGE; consumer=GUARD-P/P.boundPrincipal; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: Authentic bound executor/M scope/time and derived principal row lock
GRANT SELECT (omie_connection_id) ON TABLE public.offline_binding_header TO flooow_offline_principal_lock_owner;
-- SPEC:1446 P READ_PRIVILEGE; consumer=GUARD-P/P.boundPrincipal; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: Authentic bound executor/M scope/time and derived principal row lock
GRANT SELECT (valid_from) ON TABLE public.offline_binding_header TO flooow_offline_principal_lock_owner;
-- SPEC:1447 P READ_PRIVILEGE; consumer=GUARD-P/P.boundPrincipal; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: Authentic bound executor/M scope/time and derived principal row lock
GRANT SELECT (expires_at) ON TABLE public.offline_binding_header TO flooow_offline_principal_lock_owner;
-- SPEC:1448 Q READ_PRIVILEGE; consumer=GUARD-Q/READINESS; entrypoint=internal Q; transitive=Control-only; frozen effects unchanged.
-- Required: Bound preflight/claim identity/incarnation/surface/policy/validity; no domain IDs/order data
GRANT SELECT (binding_id) ON TABLE public.offline_binding_header TO flooow_offline_readiness_owner;
-- SPEC:1449 Q READ_PRIVILEGE; consumer=GUARD-Q/READINESS; entrypoint=internal Q; transitive=Control-only; frozen effects unchanged.
-- Required: Bound preflight/claim identity/incarnation/surface/policy/validity; no domain IDs/order data
GRANT SELECT (deployment_id) ON TABLE public.offline_binding_header TO flooow_offline_readiness_owner;
-- SPEC:1450 Q READ_PRIVILEGE; consumer=GUARD-Q/READINESS; entrypoint=internal Q; transitive=Control-only; frozen effects unchanged.
-- Required: Bound preflight/claim identity/incarnation/surface/policy/validity; no domain IDs/order data
GRANT SELECT (deployment_incarnation_id) ON TABLE public.offline_binding_header TO flooow_offline_readiness_owner;
-- SPEC:1451 Q READ_PRIVILEGE; consumer=GUARD-Q/READINESS; entrypoint=internal Q; transitive=Control-only; frozen effects unchanged.
-- Required: Bound preflight/claim identity/incarnation/surface/policy/validity; no domain IDs/order data
GRANT SELECT (identity_slots) ON TABLE public.offline_binding_header TO flooow_offline_readiness_owner;
-- SPEC:1452 Q READ_PRIVILEGE; consumer=GUARD-Q/READINESS; entrypoint=internal Q; transitive=Control-only; frozen effects unchanged.
-- Required: Bound preflight/claim identity/incarnation/surface/policy/validity; no domain IDs/order data
GRANT SELECT (offline_surface_version) ON TABLE public.offline_binding_header TO flooow_offline_readiness_owner;
-- SPEC:1453 Q READ_PRIVILEGE; consumer=GUARD-Q/READINESS; entrypoint=internal Q; transitive=Control-only; frozen effects unchanged.
-- Required: Bound preflight/claim identity/incarnation/surface/policy/validity; no domain IDs/order data
GRANT SELECT (deadline_policy_version) ON TABLE public.offline_binding_header TO flooow_offline_readiness_owner;
-- SPEC:1454 Q READ_PRIVILEGE; consumer=GUARD-Q/READINESS; entrypoint=internal Q; transitive=Control-only; frozen effects unchanged.
-- Required: Bound preflight/claim identity/incarnation/surface/policy/validity; no domain IDs/order data
GRANT SELECT (deadline_policy_digest) ON TABLE public.offline_binding_header TO flooow_offline_readiness_owner;
-- SPEC:1455 Q READ_PRIVILEGE; consumer=GUARD-Q/READINESS; entrypoint=internal Q; transitive=Control-only; frozen effects unchanged.
-- Required: Bound preflight/claim identity/incarnation/surface/policy/validity; no domain IDs/order data
GRANT SELECT (plan_fingerprint) ON TABLE public.offline_binding_header TO flooow_offline_readiness_owner;
-- SPEC:1456 Q READ_PRIVILEGE; consumer=GUARD-Q/READINESS; entrypoint=internal Q; transitive=Control-only; frozen effects unchanged.
-- Required: Bound preflight/claim identity/incarnation/surface/policy/validity; no domain IDs/order data
GRANT SELECT (valid_from) ON TABLE public.offline_binding_header TO flooow_offline_readiness_owner;
-- SPEC:1457 Q READ_PRIVILEGE; consumer=GUARD-Q/READINESS; entrypoint=internal Q; transitive=Control-only; frozen effects unchanged.
-- Required: Bound preflight/claim identity/incarnation/surface/policy/validity; no domain IDs/order data
GRANT SELECT (expires_at) ON TABLE public.offline_binding_header TO flooow_offline_readiness_owner;
-- SPEC:1458 Z READ_PRIVILEGE; consumer=GUARD-Z/IA; entrypoint=internal Z; transitive=Control-only; frozen effects unchanged.
-- Required: Bound auditor R and exact three canonical operation/intent inputs; no broader economic data
GRANT SELECT (binding_id) ON TABLE public.offline_binding_header TO flooow_offline_intent_audit_owner;
-- SPEC:1459 Z READ_PRIVILEGE; consumer=GUARD-Z/IA; entrypoint=internal Z; transitive=Control-only; frozen effects unchanged.
-- Required: Bound auditor R and exact three canonical operation/intent inputs; no broader economic data
GRANT SELECT (deployment_id) ON TABLE public.offline_binding_header TO flooow_offline_intent_audit_owner;
-- SPEC:1460 Z READ_PRIVILEGE; consumer=GUARD-Z/IA; entrypoint=internal Z; transitive=Control-only; frozen effects unchanged.
-- Required: Bound auditor R and exact three canonical operation/intent inputs; no broader economic data
GRANT SELECT (deployment_incarnation_id) ON TABLE public.offline_binding_header TO flooow_offline_intent_audit_owner;
-- SPEC:1461 Z READ_PRIVILEGE; consumer=GUARD-Z/IA; entrypoint=internal Z; transitive=Control-only; frozen effects unchanged.
-- Required: Bound auditor R and exact three canonical operation/intent inputs; no broader economic data
GRANT SELECT (identity_slots) ON TABLE public.offline_binding_header TO flooow_offline_intent_audit_owner;
-- SPEC:1462 Z READ_PRIVILEGE; consumer=GUARD-Z/IA; entrypoint=internal Z; transitive=Control-only; frozen effects unchanged.
-- Required: Bound auditor R and exact three canonical operation/intent inputs; no broader economic data
GRANT SELECT (offline_surface_version) ON TABLE public.offline_binding_header TO flooow_offline_intent_audit_owner;
-- SPEC:1463 Z READ_PRIVILEGE; consumer=GUARD-Z/IA; entrypoint=internal Z; transitive=Control-only; frozen effects unchanged.
-- Required: Bound auditor R and exact three canonical operation/intent inputs; no broader economic data
GRANT SELECT (deadline_policy_version) ON TABLE public.offline_binding_header TO flooow_offline_intent_audit_owner;
-- SPEC:1464 Z READ_PRIVILEGE; consumer=GUARD-Z/IA; entrypoint=internal Z; transitive=Control-only; frozen effects unchanged.
-- Required: Bound auditor R and exact three canonical operation/intent inputs; no broader economic data
GRANT SELECT (deadline_policy_digest) ON TABLE public.offline_binding_header TO flooow_offline_intent_audit_owner;
-- SPEC:1465 Z READ_PRIVILEGE; consumer=GUARD-Z/IA; entrypoint=internal Z; transitive=Control-only; frozen effects unchanged.
-- Required: Bound auditor R and exact three canonical operation/intent inputs; no broader economic data
GRANT SELECT (plan_fingerprint) ON TABLE public.offline_binding_header TO flooow_offline_intent_audit_owner;
-- SPEC:1466 Z READ_PRIVILEGE; consumer=GUARD-Z/IA; entrypoint=internal Z; transitive=Control-only; frozen effects unchanged.
-- Required: Bound auditor R and exact three canonical operation/intent inputs; no broader economic data
GRANT SELECT (organization_id) ON TABLE public.offline_binding_header TO flooow_offline_intent_audit_owner;
-- SPEC:1467 Z READ_PRIVILEGE; consumer=GUARD-Z/IA; entrypoint=internal Z; transitive=Control-only; frozen effects unchanged.
-- Required: Bound auditor R and exact three canonical operation/intent inputs; no broader economic data
GRANT SELECT (manifest_id) ON TABLE public.offline_binding_header TO flooow_offline_intent_audit_owner;
-- SPEC:1468 Z READ_PRIVILEGE; consumer=GUARD-Z/IA; entrypoint=internal Z; transitive=Control-only; frozen effects unchanged.
-- Required: Bound auditor R and exact three canonical operation/intent inputs; no broader economic data
GRANT SELECT (principal_id) ON TABLE public.offline_binding_header TO flooow_offline_intent_audit_owner;
-- SPEC:1469 Z READ_PRIVILEGE; consumer=GUARD-Z/IA; entrypoint=internal Z; transitive=Control-only; frozen effects unchanged.
-- Required: Bound auditor R and exact three canonical operation/intent inputs; no broader economic data
GRANT SELECT (credential_id) ON TABLE public.offline_binding_header TO flooow_offline_intent_audit_owner;
-- SPEC:1470 Z READ_PRIVILEGE; consumer=GUARD-Z/IA; entrypoint=internal Z; transitive=Control-only; frozen effects unchanged.
-- Required: Bound auditor R and exact three canonical operation/intent inputs; no broader economic data
GRANT SELECT (grant_id) ON TABLE public.offline_binding_header TO flooow_offline_intent_audit_owner;
-- SPEC:1471 Z READ_PRIVILEGE; consumer=GUARD-Z/IA; entrypoint=internal Z; transitive=Control-only; frozen effects unchanged.
-- Required: Bound auditor R and exact three canonical operation/intent inputs; no broader economic data
GRANT SELECT (principal_operation_id) ON TABLE public.offline_binding_header TO flooow_offline_intent_audit_owner;
-- SPEC:1472 Z READ_PRIVILEGE; consumer=GUARD-Z/IA; entrypoint=internal Z; transitive=Control-only; frozen effects unchanged.
-- Required: Bound auditor R and exact three canonical operation/intent inputs; no broader economic data
GRANT SELECT (credential_operation_id) ON TABLE public.offline_binding_header TO flooow_offline_intent_audit_owner;
-- SPEC:1473 Z READ_PRIVILEGE; consumer=GUARD-Z/IA; entrypoint=internal Z; transitive=Control-only; frozen effects unchanged.
-- Required: Bound auditor R and exact three canonical operation/intent inputs; no broader economic data
GRANT SELECT (grant_operation_id) ON TABLE public.offline_binding_header TO flooow_offline_intent_audit_owner;
-- SPEC:1474 Z READ_PRIVILEGE; consumer=GUARD-Z/IA; entrypoint=internal Z; transitive=Control-only; frozen effects unchanged.
-- Required: Bound auditor R and exact three canonical operation/intent inputs; no broader economic data
GRANT SELECT (mercado_livre_connection_id) ON TABLE public.offline_binding_header TO flooow_offline_intent_audit_owner;
-- SPEC:1475 Z READ_PRIVILEGE; consumer=GUARD-Z/IA; entrypoint=internal Z; transitive=Control-only; frozen effects unchanged.
-- Required: Bound auditor R and exact three canonical operation/intent inputs; no broader economic data
GRANT SELECT (omie_connection_id) ON TABLE public.offline_binding_header TO flooow_offline_intent_audit_owner;
-- SPEC:1476 Z READ_PRIVILEGE; consumer=GUARD-Z/IA; entrypoint=internal Z; transitive=Control-only; frozen effects unchanged.
-- Required: Bound auditor R and exact three canonical operation/intent inputs; no broader economic data
GRANT SELECT (reason) ON TABLE public.offline_binding_header TO flooow_offline_intent_audit_owner;
-- SPEC:1477 Z READ_PRIVILEGE; consumer=GUARD-Z/IA; entrypoint=internal Z; transitive=Control-only; frozen effects unchanged.
-- Required: Bound auditor R and exact three canonical operation/intent inputs; no broader economic data
GRANT SELECT (provenance) ON TABLE public.offline_binding_header TO flooow_offline_intent_audit_owner;
-- SPEC:1478 Z READ_PRIVILEGE; consumer=GUARD-Z/IA; entrypoint=internal Z; transitive=Control-only; frozen effects unchanged.
-- Required: Bound auditor R and exact three canonical operation/intent inputs; no broader economic data
GRANT SELECT (correlation_id) ON TABLE public.offline_binding_header TO flooow_offline_intent_audit_owner;
-- SPEC:1479 V READ_PRIVILEGE; consumer=GUARD-V; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Bound lifecycle scope; M ACTIVE predicate or S02 state; Q claim ACTIVE only
GRANT SELECT (binding_id) ON TABLE public.offline_binding_lifecycle TO flooow_offline_verification_owner;
-- SPEC:1480 V READ_PRIVILEGE; consumer=GUARD-V; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Bound lifecycle scope; M ACTIVE predicate or S02 state; Q claim ACTIVE only
GRANT SELECT (state) ON TABLE public.offline_binding_lifecycle TO flooow_offline_verification_owner;
-- SPEC:1481 I READ_PRIVILEGE; consumer=GUARD-I; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Bound lifecycle scope; M ACTIVE predicate or S02 state; Q claim ACTIVE only
GRANT SELECT (binding_id) ON TABLE public.offline_binding_lifecycle TO flooow_offline_issuance_owner;
-- SPEC:1482 I READ_PRIVILEGE; consumer=GUARD-I; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Bound lifecycle scope; M ACTIVE predicate or S02 state; Q claim ACTIVE only
GRANT SELECT (state) ON TABLE public.offline_binding_lifecycle TO flooow_offline_issuance_owner;
-- SPEC:1483 E READ_PRIVILEGE; consumer=GUARD-E; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Bound lifecycle scope; M ACTIVE predicate or S02 state; Q claim ACTIVE only
GRANT SELECT (binding_id) ON TABLE public.offline_binding_lifecycle TO flooow_offline_execution_owner;
-- SPEC:1484 E READ_PRIVILEGE; consumer=GUARD-E; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Bound lifecycle scope; M ACTIVE predicate or S02 state; Q claim ACTIVE only
GRANT SELECT (state) ON TABLE public.offline_binding_lifecycle TO flooow_offline_execution_owner;
-- SPEC:1485 A READ_PRIVILEGE; consumer=INSPECT; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Bound lifecycle scope; M ACTIVE predicate or S02 state; Q claim ACTIVE only
GRANT SELECT (binding_id) ON TABLE public.offline_binding_lifecycle TO flooow_offline_audit_owner;
-- SPEC:1486 A READ_PRIVILEGE; consumer=INSPECT; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Bound lifecycle scope; M ACTIVE predicate or S02 state; Q claim ACTIVE only
GRANT SELECT (state) ON TABLE public.offline_binding_lifecycle TO flooow_offline_audit_owner;
-- SPEC:1487 P READ_PRIVILEGE; consumer=GUARD-P; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: Bound lifecycle scope; M ACTIVE predicate or S02 state; Q claim ACTIVE only
GRANT SELECT (binding_id) ON TABLE public.offline_binding_lifecycle TO flooow_offline_principal_lock_owner;
-- SPEC:1488 P READ_PRIVILEGE; consumer=GUARD-P; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: Bound lifecycle scope; M ACTIVE predicate or S02 state; Q claim ACTIVE only
GRANT SELECT (state) ON TABLE public.offline_binding_lifecycle TO flooow_offline_principal_lock_owner;
-- SPEC:1489 Q READ_PRIVILEGE; consumer=GUARD-Q; entrypoint=internal Q; transitive=Control-only; frozen effects unchanged.
-- Required: Bound lifecycle scope; M ACTIVE predicate or S02 state; Q claim ACTIVE only
GRANT SELECT (binding_id) ON TABLE public.offline_binding_lifecycle TO flooow_offline_readiness_owner;
-- SPEC:1490 Q READ_PRIVILEGE; consumer=GUARD-Q; entrypoint=internal Q; transitive=Control-only; frozen effects unchanged.
-- Required: Bound lifecycle scope; M ACTIVE predicate or S02 state; Q claim ACTIVE only
GRANT SELECT (state) ON TABLE public.offline_binding_lifecycle TO flooow_offline_readiness_owner;
-- SPEC:1491 V READ_PRIVILEGE; consumer=GUARD-V; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Current attempt/generation fencing
GRANT SELECT (binding_id) ON TABLE public.offline_attempt_pointer TO flooow_offline_verification_owner;
-- SPEC:1492 V READ_PRIVILEGE; consumer=GUARD-V; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Current attempt/generation fencing
GRANT SELECT (current_attempt_id) ON TABLE public.offline_attempt_pointer TO flooow_offline_verification_owner;
-- SPEC:1493 V READ_PRIVILEGE; consumer=GUARD-V; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Current attempt/generation fencing
GRANT SELECT (generation) ON TABLE public.offline_attempt_pointer TO flooow_offline_verification_owner;
-- SPEC:1494 I READ_PRIVILEGE; consumer=GUARD-I; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Current attempt/generation fencing
GRANT SELECT (binding_id) ON TABLE public.offline_attempt_pointer TO flooow_offline_issuance_owner;
-- SPEC:1495 I READ_PRIVILEGE; consumer=GUARD-I; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Current attempt/generation fencing
GRANT SELECT (current_attempt_id) ON TABLE public.offline_attempt_pointer TO flooow_offline_issuance_owner;
-- SPEC:1496 I READ_PRIVILEGE; consumer=GUARD-I; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Current attempt/generation fencing
GRANT SELECT (generation) ON TABLE public.offline_attempt_pointer TO flooow_offline_issuance_owner;
-- SPEC:1497 E READ_PRIVILEGE; consumer=GUARD-E; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Current attempt/generation fencing
GRANT SELECT (binding_id) ON TABLE public.offline_attempt_pointer TO flooow_offline_execution_owner;
-- SPEC:1498 E READ_PRIVILEGE; consumer=GUARD-E; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Current attempt/generation fencing
GRANT SELECT (current_attempt_id) ON TABLE public.offline_attempt_pointer TO flooow_offline_execution_owner;
-- SPEC:1499 E READ_PRIVILEGE; consumer=GUARD-E; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Current attempt/generation fencing
GRANT SELECT (generation) ON TABLE public.offline_attempt_pointer TO flooow_offline_execution_owner;
-- SPEC:1500 P READ_PRIVILEGE; consumer=GUARD-P; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: Current attempt/generation fencing
GRANT SELECT (binding_id) ON TABLE public.offline_attempt_pointer TO flooow_offline_principal_lock_owner;
-- SPEC:1501 P READ_PRIVILEGE; consumer=GUARD-P; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: Current attempt/generation fencing
GRANT SELECT (current_attempt_id) ON TABLE public.offline_attempt_pointer TO flooow_offline_principal_lock_owner;
-- SPEC:1502 P READ_PRIVILEGE; consumer=GUARD-P; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: Current attempt/generation fencing
GRANT SELECT (generation) ON TABLE public.offline_attempt_pointer TO flooow_offline_principal_lock_owner;
-- SPEC:1503 E READ_PRIVILEGE; consumer=CLAIM; entrypoint=S13; transitive=Control-only; frozen effects unchanged.
-- Required: Administrative claim exception permission
GRANT SELECT (claim_permitted) ON TABLE public.offline_attempt_pointer TO flooow_offline_execution_owner;
-- SPEC:1504 Q READ_PRIVILEGE; consumer=GUARD-Q; entrypoint=internal Q; transitive=Control-only; frozen effects unchanged.
-- Required: Claim-exception permission independently checked; E owns generation/ownership checks
GRANT SELECT (binding_id) ON TABLE public.offline_attempt_pointer TO flooow_offline_readiness_owner;
-- SPEC:1505 Q READ_PRIVILEGE; consumer=GUARD-Q; entrypoint=internal Q; transitive=Control-only; frozen effects unchanged.
-- Required: Claim-exception permission independently checked; E owns generation/ownership checks
GRANT SELECT (claim_permitted) ON TABLE public.offline_attempt_pointer TO flooow_offline_readiness_owner;
-- SPEC:1506 A READ_PRIVILEGE; consumer=INSPECT; entrypoint=S02-S03; transitive=Control-only; frozen effects unchanged.
-- Required: Current state/generation and coherent lineage projection
GRANT SELECT (binding_id) ON TABLE public.offline_attempt_pointer TO flooow_offline_audit_owner;
-- SPEC:1507 A READ_PRIVILEGE; consumer=INSPECT; entrypoint=S02-S03; transitive=Control-only; frozen effects unchanged.
-- Required: Current state/generation and coherent lineage projection
GRANT SELECT (current_attempt_id) ON TABLE public.offline_attempt_pointer TO flooow_offline_audit_owner;
-- SPEC:1508 A READ_PRIVILEGE; consumer=INSPECT; entrypoint=S02-S03; transitive=Control-only; frozen effects unchanged.
-- Required: Current state/generation and coherent lineage projection
GRANT SELECT (generation) ON TABLE public.offline_attempt_pointer TO flooow_offline_audit_owner;
-- SPEC:1509 V READ_PRIVILEGE; consumer=GUARD-V; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact scoped attempt state, finite absolute window and I1-I17 effect-time coherence
GRANT SELECT (binding_id) ON TABLE public.offline_attempt TO flooow_offline_verification_owner;
-- SPEC:1510 V READ_PRIVILEGE; consumer=GUARD-V; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact scoped attempt state, finite absolute window and I1-I17 effect-time coherence
GRANT SELECT (attempt_id) ON TABLE public.offline_attempt TO flooow_offline_verification_owner;
-- SPEC:1511 V READ_PRIVILEGE; consumer=GUARD-V; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact scoped attempt state, finite absolute window and I1-I17 effect-time coherence
GRANT SELECT (generation) ON TABLE public.offline_attempt TO flooow_offline_verification_owner;
-- SPEC:1512 V READ_PRIVILEGE; consumer=GUARD-V; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact scoped attempt state, finite absolute window and I1-I17 effect-time coherence
GRANT SELECT (state) ON TABLE public.offline_attempt TO flooow_offline_verification_owner;
-- SPEC:1513 V READ_PRIVILEGE; consumer=GUARD-V; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact scoped attempt state, finite absolute window and I1-I17 effect-time coherence
GRANT SELECT (claimed_at) ON TABLE public.offline_attempt TO flooow_offline_verification_owner;
-- SPEC:1514 V READ_PRIVILEGE; consumer=GUARD-V; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact scoped attempt state, finite absolute window and I1-I17 effect-time coherence
GRANT SELECT (expires_at) ON TABLE public.offline_attempt TO flooow_offline_verification_owner;
-- SPEC:1515 I READ_PRIVILEGE; consumer=GUARD-I; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact scoped attempt state, finite absolute window and I1-I17 effect-time coherence
GRANT SELECT (binding_id) ON TABLE public.offline_attempt TO flooow_offline_issuance_owner;
-- SPEC:1516 I READ_PRIVILEGE; consumer=GUARD-I; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact scoped attempt state, finite absolute window and I1-I17 effect-time coherence
GRANT SELECT (attempt_id) ON TABLE public.offline_attempt TO flooow_offline_issuance_owner;
-- SPEC:1517 I READ_PRIVILEGE; consumer=GUARD-I; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact scoped attempt state, finite absolute window and I1-I17 effect-time coherence
GRANT SELECT (generation) ON TABLE public.offline_attempt TO flooow_offline_issuance_owner;
-- SPEC:1518 I READ_PRIVILEGE; consumer=GUARD-I; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact scoped attempt state, finite absolute window and I1-I17 effect-time coherence
GRANT SELECT (state) ON TABLE public.offline_attempt TO flooow_offline_issuance_owner;
-- SPEC:1519 I READ_PRIVILEGE; consumer=GUARD-I; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact scoped attempt state, finite absolute window and I1-I17 effect-time coherence
GRANT SELECT (claimed_at) ON TABLE public.offline_attempt TO flooow_offline_issuance_owner;
-- SPEC:1520 I READ_PRIVILEGE; consumer=GUARD-I; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact scoped attempt state, finite absolute window and I1-I17 effect-time coherence
GRANT SELECT (expires_at) ON TABLE public.offline_attempt TO flooow_offline_issuance_owner;
-- SPEC:1521 E READ_PRIVILEGE; consumer=GUARD-E; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact scoped attempt state, finite absolute window and I1-I17 effect-time coherence
GRANT SELECT (binding_id) ON TABLE public.offline_attempt TO flooow_offline_execution_owner;
-- SPEC:1522 E READ_PRIVILEGE; consumer=GUARD-E; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact scoped attempt state, finite absolute window and I1-I17 effect-time coherence
GRANT SELECT (attempt_id) ON TABLE public.offline_attempt TO flooow_offline_execution_owner;
-- SPEC:1523 E READ_PRIVILEGE; consumer=GUARD-E; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact scoped attempt state, finite absolute window and I1-I17 effect-time coherence
GRANT SELECT (generation) ON TABLE public.offline_attempt TO flooow_offline_execution_owner;
-- SPEC:1524 E READ_PRIVILEGE; consumer=GUARD-E; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact scoped attempt state, finite absolute window and I1-I17 effect-time coherence
GRANT SELECT (state) ON TABLE public.offline_attempt TO flooow_offline_execution_owner;
-- SPEC:1525 E READ_PRIVILEGE; consumer=GUARD-E; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact scoped attempt state, finite absolute window and I1-I17 effect-time coherence
GRANT SELECT (claimed_at) ON TABLE public.offline_attempt TO flooow_offline_execution_owner;
-- SPEC:1526 E READ_PRIVILEGE; consumer=GUARD-E; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact scoped attempt state, finite absolute window and I1-I17 effect-time coherence
GRANT SELECT (expires_at) ON TABLE public.offline_attempt TO flooow_offline_execution_owner;
-- SPEC:1527 P READ_PRIVILEGE; consumer=GUARD-P; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: Exact scoped attempt state, finite absolute window and I1-I17 effect-time coherence
GRANT SELECT (binding_id) ON TABLE public.offline_attempt TO flooow_offline_principal_lock_owner;
-- SPEC:1528 P READ_PRIVILEGE; consumer=GUARD-P; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: Exact scoped attempt state, finite absolute window and I1-I17 effect-time coherence
GRANT SELECT (attempt_id) ON TABLE public.offline_attempt TO flooow_offline_principal_lock_owner;
-- SPEC:1529 P READ_PRIVILEGE; consumer=GUARD-P; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: Exact scoped attempt state, finite absolute window and I1-I17 effect-time coherence
GRANT SELECT (generation) ON TABLE public.offline_attempt TO flooow_offline_principal_lock_owner;
-- SPEC:1530 P READ_PRIVILEGE; consumer=GUARD-P; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: Exact scoped attempt state, finite absolute window and I1-I17 effect-time coherence
GRANT SELECT (state) ON TABLE public.offline_attempt TO flooow_offline_principal_lock_owner;
-- SPEC:1531 P READ_PRIVILEGE; consumer=GUARD-P; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: Exact scoped attempt state, finite absolute window and I1-I17 effect-time coherence
GRANT SELECT (claimed_at) ON TABLE public.offline_attempt TO flooow_offline_principal_lock_owner;
-- SPEC:1532 P READ_PRIVILEGE; consumer=GUARD-P; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: Exact scoped attempt state, finite absolute window and I1-I17 effect-time coherence
GRANT SELECT (expires_at) ON TABLE public.offline_attempt TO flooow_offline_principal_lock_owner;
-- SPEC:1533 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact scoped attempt state, finite absolute window and I1-I17 effect-time coherence
GRANT SELECT (binding_id) ON TABLE public.offline_attempt TO flooow_offline_audit_owner;
-- SPEC:1534 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact scoped attempt state, finite absolute window and I1-I17 effect-time coherence
GRANT SELECT (attempt_id) ON TABLE public.offline_attempt TO flooow_offline_audit_owner;
-- SPEC:1535 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact scoped attempt state, finite absolute window and I1-I17 effect-time coherence
GRANT SELECT (generation) ON TABLE public.offline_attempt TO flooow_offline_audit_owner;
-- SPEC:1536 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact scoped attempt state, finite absolute window and I1-I17 effect-time coherence
GRANT SELECT (state) ON TABLE public.offline_attempt TO flooow_offline_audit_owner;
-- SPEC:1537 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact scoped attempt state, finite absolute window and I1-I17 effect-time coherence
GRANT SELECT (claimed_at) ON TABLE public.offline_attempt TO flooow_offline_audit_owner;
-- SPEC:1538 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact scoped attempt state, finite absolute window and I1-I17 effect-time coherence
GRANT SELECT (expires_at) ON TABLE public.offline_attempt TO flooow_offline_audit_owner;
-- SPEC:1539 V READ_PRIVILEGE; consumer=GUARD-V; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Current OWNED/executor/instance proof and absolute execution window; digest never output
GRANT SELECT (binding_id) ON TABLE public.offline_execution TO flooow_offline_verification_owner;
-- SPEC:1540 V READ_PRIVILEGE; consumer=GUARD-V; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Current OWNED/executor/instance proof and absolute execution window; digest never output
GRANT SELECT (attempt_id) ON TABLE public.offline_execution TO flooow_offline_verification_owner;
-- SPEC:1541 V READ_PRIVILEGE; consumer=GUARD-V; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Current OWNED/executor/instance proof and absolute execution window; digest never output
GRANT SELECT (generation) ON TABLE public.offline_execution TO flooow_offline_verification_owner;
-- SPEC:1542 V READ_PRIVILEGE; consumer=GUARD-V; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Current OWNED/executor/instance proof and absolute execution window; digest never output
GRANT SELECT (execution_id) ON TABLE public.offline_execution TO flooow_offline_verification_owner;
-- SPEC:1543 V READ_PRIVILEGE; consumer=GUARD-V; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Current OWNED/executor/instance proof and absolute execution window; digest never output
GRANT SELECT (instance_id) ON TABLE public.offline_execution TO flooow_offline_verification_owner;
-- SPEC:1544 V READ_PRIVILEGE; consumer=GUARD-V; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Current OWNED/executor/instance proof and absolute execution window; digest never output
GRANT SELECT (executor_oid) ON TABLE public.offline_execution TO flooow_offline_verification_owner;
-- SPEC:1545 V READ_PRIVILEGE; consumer=GUARD-V; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Current OWNED/executor/instance proof and absolute execution window; digest never output
GRANT SELECT (state) ON TABLE public.offline_execution TO flooow_offline_verification_owner;
-- SPEC:1546 V READ_PRIVILEGE; consumer=GUARD-V; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Current OWNED/executor/instance proof and absolute execution window; digest never output
GRANT SELECT (claimed_at) ON TABLE public.offline_execution TO flooow_offline_verification_owner;
-- SPEC:1547 V READ_PRIVILEGE; consumer=GUARD-V; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Current OWNED/executor/instance proof and absolute execution window; digest never output
GRANT SELECT (expires_at) ON TABLE public.offline_execution TO flooow_offline_verification_owner;
-- SPEC:1548 V READ_PRIVILEGE; consumer=GUARD-V; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Current OWNED/executor/instance proof and absolute execution window; digest never output
GRANT SELECT (possession_digest) ON TABLE public.offline_execution TO flooow_offline_verification_owner;
-- SPEC:1549 I READ_PRIVILEGE; consumer=GUARD-I; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Current OWNED/executor/instance proof and absolute execution window; digest never output
GRANT SELECT (binding_id) ON TABLE public.offline_execution TO flooow_offline_issuance_owner;
-- SPEC:1550 I READ_PRIVILEGE; consumer=GUARD-I; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Current OWNED/executor/instance proof and absolute execution window; digest never output
GRANT SELECT (attempt_id) ON TABLE public.offline_execution TO flooow_offline_issuance_owner;
-- SPEC:1551 I READ_PRIVILEGE; consumer=GUARD-I; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Current OWNED/executor/instance proof and absolute execution window; digest never output
GRANT SELECT (generation) ON TABLE public.offline_execution TO flooow_offline_issuance_owner;
-- SPEC:1552 I READ_PRIVILEGE; consumer=GUARD-I; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Current OWNED/executor/instance proof and absolute execution window; digest never output
GRANT SELECT (execution_id) ON TABLE public.offline_execution TO flooow_offline_issuance_owner;
-- SPEC:1553 I READ_PRIVILEGE; consumer=GUARD-I; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Current OWNED/executor/instance proof and absolute execution window; digest never output
GRANT SELECT (instance_id) ON TABLE public.offline_execution TO flooow_offline_issuance_owner;
-- SPEC:1554 I READ_PRIVILEGE; consumer=GUARD-I; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Current OWNED/executor/instance proof and absolute execution window; digest never output
GRANT SELECT (executor_oid) ON TABLE public.offline_execution TO flooow_offline_issuance_owner;
-- SPEC:1555 I READ_PRIVILEGE; consumer=GUARD-I; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Current OWNED/executor/instance proof and absolute execution window; digest never output
GRANT SELECT (state) ON TABLE public.offline_execution TO flooow_offline_issuance_owner;
-- SPEC:1556 I READ_PRIVILEGE; consumer=GUARD-I; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Current OWNED/executor/instance proof and absolute execution window; digest never output
GRANT SELECT (claimed_at) ON TABLE public.offline_execution TO flooow_offline_issuance_owner;
-- SPEC:1557 I READ_PRIVILEGE; consumer=GUARD-I; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Current OWNED/executor/instance proof and absolute execution window; digest never output
GRANT SELECT (expires_at) ON TABLE public.offline_execution TO flooow_offline_issuance_owner;
-- SPEC:1558 I READ_PRIVILEGE; consumer=GUARD-I; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Current OWNED/executor/instance proof and absolute execution window; digest never output
GRANT SELECT (possession_digest) ON TABLE public.offline_execution TO flooow_offline_issuance_owner;
-- SPEC:1559 E READ_PRIVILEGE; consumer=GUARD-E; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Current OWNED/executor/instance proof and absolute execution window; digest never output
GRANT SELECT (binding_id) ON TABLE public.offline_execution TO flooow_offline_execution_owner;
-- SPEC:1560 E READ_PRIVILEGE; consumer=GUARD-E; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Current OWNED/executor/instance proof and absolute execution window; digest never output
GRANT SELECT (attempt_id) ON TABLE public.offline_execution TO flooow_offline_execution_owner;
-- SPEC:1561 E READ_PRIVILEGE; consumer=GUARD-E; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Current OWNED/executor/instance proof and absolute execution window; digest never output
GRANT SELECT (generation) ON TABLE public.offline_execution TO flooow_offline_execution_owner;
-- SPEC:1562 E READ_PRIVILEGE; consumer=GUARD-E; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Current OWNED/executor/instance proof and absolute execution window; digest never output
GRANT SELECT (execution_id) ON TABLE public.offline_execution TO flooow_offline_execution_owner;
-- SPEC:1563 E READ_PRIVILEGE; consumer=GUARD-E; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Current OWNED/executor/instance proof and absolute execution window; digest never output
GRANT SELECT (instance_id) ON TABLE public.offline_execution TO flooow_offline_execution_owner;
-- SPEC:1564 E READ_PRIVILEGE; consumer=GUARD-E; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Current OWNED/executor/instance proof and absolute execution window; digest never output
GRANT SELECT (executor_oid) ON TABLE public.offline_execution TO flooow_offline_execution_owner;
-- SPEC:1565 E READ_PRIVILEGE; consumer=GUARD-E; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Current OWNED/executor/instance proof and absolute execution window; digest never output
GRANT SELECT (state) ON TABLE public.offline_execution TO flooow_offline_execution_owner;
-- SPEC:1566 E READ_PRIVILEGE; consumer=GUARD-E; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Current OWNED/executor/instance proof and absolute execution window; digest never output
GRANT SELECT (claimed_at) ON TABLE public.offline_execution TO flooow_offline_execution_owner;
-- SPEC:1567 E READ_PRIVILEGE; consumer=GUARD-E; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Current OWNED/executor/instance proof and absolute execution window; digest never output
GRANT SELECT (expires_at) ON TABLE public.offline_execution TO flooow_offline_execution_owner;
-- SPEC:1568 E READ_PRIVILEGE; consumer=GUARD-E; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Current OWNED/executor/instance proof and absolute execution window; digest never output
GRANT SELECT (possession_digest) ON TABLE public.offline_execution TO flooow_offline_execution_owner;
-- SPEC:1569 P READ_PRIVILEGE; consumer=GUARD-P; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: Current OWNED/executor/instance proof and absolute execution window; digest never output
GRANT SELECT (binding_id) ON TABLE public.offline_execution TO flooow_offline_principal_lock_owner;
-- SPEC:1570 P READ_PRIVILEGE; consumer=GUARD-P; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: Current OWNED/executor/instance proof and absolute execution window; digest never output
GRANT SELECT (attempt_id) ON TABLE public.offline_execution TO flooow_offline_principal_lock_owner;
-- SPEC:1571 P READ_PRIVILEGE; consumer=GUARD-P; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: Current OWNED/executor/instance proof and absolute execution window; digest never output
GRANT SELECT (generation) ON TABLE public.offline_execution TO flooow_offline_principal_lock_owner;
-- SPEC:1572 P READ_PRIVILEGE; consumer=GUARD-P; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: Current OWNED/executor/instance proof and absolute execution window; digest never output
GRANT SELECT (execution_id) ON TABLE public.offline_execution TO flooow_offline_principal_lock_owner;
-- SPEC:1573 P READ_PRIVILEGE; consumer=GUARD-P; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: Current OWNED/executor/instance proof and absolute execution window; digest never output
GRANT SELECT (instance_id) ON TABLE public.offline_execution TO flooow_offline_principal_lock_owner;
-- SPEC:1574 P READ_PRIVILEGE; consumer=GUARD-P; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: Current OWNED/executor/instance proof and absolute execution window; digest never output
GRANT SELECT (executor_oid) ON TABLE public.offline_execution TO flooow_offline_principal_lock_owner;
-- SPEC:1575 P READ_PRIVILEGE; consumer=GUARD-P; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: Current OWNED/executor/instance proof and absolute execution window; digest never output
GRANT SELECT (state) ON TABLE public.offline_execution TO flooow_offline_principal_lock_owner;
-- SPEC:1576 P READ_PRIVILEGE; consumer=GUARD-P; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: Current OWNED/executor/instance proof and absolute execution window; digest never output
GRANT SELECT (claimed_at) ON TABLE public.offline_execution TO flooow_offline_principal_lock_owner;
-- SPEC:1577 P READ_PRIVILEGE; consumer=GUARD-P; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: Current OWNED/executor/instance proof and absolute execution window; digest never output
GRANT SELECT (expires_at) ON TABLE public.offline_execution TO flooow_offline_principal_lock_owner;
-- SPEC:1578 P READ_PRIVILEGE; consumer=GUARD-P; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: Current OWNED/executor/instance proof and absolute execution window; digest never output
GRANT SELECT (possession_digest) ON TABLE public.offline_execution TO flooow_offline_principal_lock_owner;
-- SPEC:1579 E READ_PRIVILEGE; consumer=CLAIM; entrypoint=S13; transitive=Control-only; frozen effects unchanged.
-- Required: Exact original lost-ack receipt without renewal
GRANT SELECT (claim_receipt_id) ON TABLE public.offline_execution TO flooow_offline_execution_owner;
-- SPEC:1580 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=Control-only; frozen effects unchanged.
-- Required: State/origin/time coherence I2/I5/I13/I15/I17; no possession digest
GRANT SELECT (binding_id) ON TABLE public.offline_execution TO flooow_offline_audit_owner;
-- SPEC:1581 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=Control-only; frozen effects unchanged.
-- Required: State/origin/time coherence I2/I5/I13/I15/I17; no possession digest
GRANT SELECT (attempt_id) ON TABLE public.offline_execution TO flooow_offline_audit_owner;
-- SPEC:1582 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=Control-only; frozen effects unchanged.
-- Required: State/origin/time coherence I2/I5/I13/I15/I17; no possession digest
GRANT SELECT (generation) ON TABLE public.offline_execution TO flooow_offline_audit_owner;
-- SPEC:1583 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=Control-only; frozen effects unchanged.
-- Required: State/origin/time coherence I2/I5/I13/I15/I17; no possession digest
GRANT SELECT (execution_id) ON TABLE public.offline_execution TO flooow_offline_audit_owner;
-- SPEC:1584 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=Control-only; frozen effects unchanged.
-- Required: State/origin/time coherence I2/I5/I13/I15/I17; no possession digest
GRANT SELECT (instance_id) ON TABLE public.offline_execution TO flooow_offline_audit_owner;
-- SPEC:1585 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=Control-only; frozen effects unchanged.
-- Required: State/origin/time coherence I2/I5/I13/I15/I17; no possession digest
GRANT SELECT (executor_oid) ON TABLE public.offline_execution TO flooow_offline_audit_owner;
-- SPEC:1586 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=Control-only; frozen effects unchanged.
-- Required: State/origin/time coherence I2/I5/I13/I15/I17; no possession digest
GRANT SELECT (state) ON TABLE public.offline_execution TO flooow_offline_audit_owner;
-- SPEC:1587 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=Control-only; frozen effects unchanged.
-- Required: State/origin/time coherence I2/I5/I13/I15/I17; no possession digest
GRANT SELECT (claimed_at) ON TABLE public.offline_execution TO flooow_offline_audit_owner;
-- SPEC:1588 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=Control-only; frozen effects unchanged.
-- Required: State/origin/time coherence I2/I5/I13/I15/I17; no possession digest
GRANT SELECT (expires_at) ON TABLE public.offline_execution TO flooow_offline_audit_owner;
-- SPEC:1589 I READ_PRIVILEGE; consumer=ISSUE-STAGE; entrypoint=S09-S10; transitive=Control-only; frozen effects unchanged.
-- Required: Single fresh credential origin initialization; reject second origin
GRANT SELECT (binding_id) ON TABLE public.offline_delivery TO flooow_offline_issuance_owner;
-- SPEC:1590 I READ_PRIVILEGE; consumer=ISSUE-STAGE; entrypoint=S09-S10; transitive=Control-only; frozen effects unchanged.
-- Required: Single fresh credential origin initialization; reject second origin
GRANT SELECT (attempt_id) ON TABLE public.offline_delivery TO flooow_offline_issuance_owner;
-- SPEC:1591 I READ_PRIVILEGE; consumer=ISSUE-STAGE; entrypoint=S09-S10; transitive=Control-only; frozen effects unchanged.
-- Required: Single fresh credential origin initialization; reject second origin
GRANT SELECT (generation) ON TABLE public.offline_delivery TO flooow_offline_issuance_owner;
-- SPEC:1592 I READ_PRIVILEGE; consumer=ISSUE-STAGE; entrypoint=S09-S10; transitive=Control-only; frozen effects unchanged.
-- Required: Single fresh credential origin initialization; reject second origin
GRANT SELECT (execution_id) ON TABLE public.offline_delivery TO flooow_offline_issuance_owner;
-- SPEC:1593 I READ_PRIVILEGE; consumer=ISSUE-STAGE; entrypoint=S09-S10; transitive=Control-only; frozen effects unchanged.
-- Required: Single fresh credential origin initialization; reject second origin
GRANT SELECT (instance_id) ON TABLE public.offline_delivery TO flooow_offline_issuance_owner;
-- SPEC:1594 I READ_PRIVILEGE; consumer=ISSUE-STAGE; entrypoint=S09-S10; transitive=Control-only; frozen effects unchanged.
-- Required: Single fresh credential origin initialization; reject second origin
GRANT SELECT (credential_id) ON TABLE public.offline_delivery TO flooow_offline_issuance_owner;
-- SPEC:1595 I READ_PRIVILEGE; consumer=ISSUE-STAGE; entrypoint=S09-S10; transitive=Control-only; frozen effects unchanged.
-- Required: Single fresh credential origin initialization; reject second origin
GRANT SELECT (initial_operation_id) ON TABLE public.offline_delivery TO flooow_offline_issuance_owner;
-- SPEC:1596 I READ_PRIVILEGE; consumer=ISSUE-STAGE; entrypoint=S09-S10; transitive=Control-only; frozen effects unchanged.
-- Required: Single fresh credential origin initialization; reject second origin
GRANT SELECT (fresh_applied_receipt_id) ON TABLE public.offline_delivery TO flooow_offline_issuance_owner;
-- SPEC:1597 I READ_PRIVILEGE; consumer=ISSUE-STAGE; entrypoint=S09-S10; transitive=Control-only; frozen effects unchanged.
-- Required: Single fresh credential origin initialization; reject second origin
GRANT SELECT (state) ON TABLE public.offline_delivery TO flooow_offline_issuance_owner;
-- SPEC:1598 E READ_PRIVILEGE; consumer=DELIVERY/AUTH/COMPLETE; entrypoint=S14-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Original live single-consumption/report replay, deadline, ACK prerequisite and decision coherence
GRANT SELECT (binding_id) ON TABLE public.offline_delivery TO flooow_offline_execution_owner;
-- SPEC:1599 E READ_PRIVILEGE; consumer=DELIVERY/AUTH/COMPLETE; entrypoint=S14-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Original live single-consumption/report replay, deadline, ACK prerequisite and decision coherence
GRANT SELECT (attempt_id) ON TABLE public.offline_delivery TO flooow_offline_execution_owner;
-- SPEC:1600 E READ_PRIVILEGE; consumer=DELIVERY/AUTH/COMPLETE; entrypoint=S14-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Original live single-consumption/report replay, deadline, ACK prerequisite and decision coherence
GRANT SELECT (generation) ON TABLE public.offline_delivery TO flooow_offline_execution_owner;
-- SPEC:1601 E READ_PRIVILEGE; consumer=DELIVERY/AUTH/COMPLETE; entrypoint=S14-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Original live single-consumption/report replay, deadline, ACK prerequisite and decision coherence
GRANT SELECT (execution_id) ON TABLE public.offline_delivery TO flooow_offline_execution_owner;
-- SPEC:1602 E READ_PRIVILEGE; consumer=DELIVERY/AUTH/COMPLETE; entrypoint=S14-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Original live single-consumption/report replay, deadline, ACK prerequisite and decision coherence
GRANT SELECT (instance_id) ON TABLE public.offline_delivery TO flooow_offline_execution_owner;
-- SPEC:1603 E READ_PRIVILEGE; consumer=DELIVERY/AUTH/COMPLETE; entrypoint=S14-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Original live single-consumption/report replay, deadline, ACK prerequisite and decision coherence
GRANT SELECT (credential_id) ON TABLE public.offline_delivery TO flooow_offline_execution_owner;
-- SPEC:1604 E READ_PRIVILEGE; consumer=DELIVERY/AUTH/COMPLETE; entrypoint=S14-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Original live single-consumption/report replay, deadline, ACK prerequisite and decision coherence
GRANT SELECT (initial_operation_id) ON TABLE public.offline_delivery TO flooow_offline_execution_owner;
-- SPEC:1605 E READ_PRIVILEGE; consumer=DELIVERY/AUTH/COMPLETE; entrypoint=S14-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Original live single-consumption/report replay, deadline, ACK prerequisite and decision coherence
GRANT SELECT (fresh_applied_receipt_id) ON TABLE public.offline_delivery TO flooow_offline_execution_owner;
-- SPEC:1606 E READ_PRIVILEGE; consumer=DELIVERY/AUTH/COMPLETE; entrypoint=S14-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Original live single-consumption/report replay, deadline, ACK prerequisite and decision coherence
GRANT SELECT (state) ON TABLE public.offline_delivery TO flooow_offline_execution_owner;
-- SPEC:1607 E READ_PRIVILEGE; consumer=DELIVERY/AUTH/COMPLETE; entrypoint=S14-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Original live single-consumption/report replay, deadline, ACK prerequisite and decision coherence
GRANT SELECT (delivery_receipt_id) ON TABLE public.offline_delivery TO flooow_offline_execution_owner;
-- SPEC:1608 E READ_PRIVILEGE; consumer=DELIVERY/AUTH/COMPLETE; entrypoint=S14-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Original live single-consumption/report replay, deadline, ACK prerequisite and decision coherence
GRANT SELECT (attempted_at) ON TABLE public.offline_delivery TO flooow_offline_execution_owner;
-- SPEC:1609 E READ_PRIVILEGE; consumer=DELIVERY/AUTH/COMPLETE; entrypoint=S14-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Original live single-consumption/report replay, deadline, ACK prerequisite and decision coherence
GRANT SELECT (operation_deadline) ON TABLE public.offline_delivery TO flooow_offline_execution_owner;
-- SPEC:1610 E READ_PRIVILEGE; consumer=DELIVERY/AUTH/COMPLETE; entrypoint=S14-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Original live single-consumption/report replay, deadline, ACK prerequisite and decision coherence
GRANT SELECT (observed_at) ON TABLE public.offline_delivery TO flooow_offline_execution_owner;
-- SPEC:1611 E READ_PRIVILEGE; consumer=DELIVERY/AUTH/COMPLETE; entrypoint=S14-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Original live single-consumption/report replay, deadline, ACK prerequisite and decision coherence
GRANT SELECT (observation_code) ON TABLE public.offline_delivery TO flooow_offline_execution_owner;
-- SPEC:1612 E READ_PRIVILEGE; consumer=DELIVERY/AUTH/COMPLETE; entrypoint=S14-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Original live single-consumption/report replay, deadline, ACK prerequisite and decision coherence
GRANT SELECT (recorded_at) ON TABLE public.offline_delivery TO flooow_offline_execution_owner;
-- SPEC:1613 P READ_PRIVILEGE; consumer=GUARD-P; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: S17/S18-only live ACK lineage before principal lock
GRANT SELECT (binding_id) ON TABLE public.offline_delivery TO flooow_offline_principal_lock_owner;
-- SPEC:1614 P READ_PRIVILEGE; consumer=GUARD-P; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: S17/S18-only live ACK lineage before principal lock
GRANT SELECT (attempt_id) ON TABLE public.offline_delivery TO flooow_offline_principal_lock_owner;
-- SPEC:1615 P READ_PRIVILEGE; consumer=GUARD-P; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: S17/S18-only live ACK lineage before principal lock
GRANT SELECT (generation) ON TABLE public.offline_delivery TO flooow_offline_principal_lock_owner;
-- SPEC:1616 P READ_PRIVILEGE; consumer=GUARD-P; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: S17/S18-only live ACK lineage before principal lock
GRANT SELECT (execution_id) ON TABLE public.offline_delivery TO flooow_offline_principal_lock_owner;
-- SPEC:1617 P READ_PRIVILEGE; consumer=GUARD-P; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: S17/S18-only live ACK lineage before principal lock
GRANT SELECT (instance_id) ON TABLE public.offline_delivery TO flooow_offline_principal_lock_owner;
-- SPEC:1618 P READ_PRIVILEGE; consumer=GUARD-P; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: S17/S18-only live ACK lineage before principal lock
GRANT SELECT (state) ON TABLE public.offline_delivery TO flooow_offline_principal_lock_owner;
-- SPEC:1619 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=Control-only; frozen effects unchanged.
-- Required: Delivery outcome classification/origin/report consistency I4/I5/I12/I16/I17
GRANT SELECT (binding_id) ON TABLE public.offline_delivery TO flooow_offline_audit_owner;
-- SPEC:1620 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=Control-only; frozen effects unchanged.
-- Required: Delivery outcome classification/origin/report consistency I4/I5/I12/I16/I17
GRANT SELECT (attempt_id) ON TABLE public.offline_delivery TO flooow_offline_audit_owner;
-- SPEC:1621 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=Control-only; frozen effects unchanged.
-- Required: Delivery outcome classification/origin/report consistency I4/I5/I12/I16/I17
GRANT SELECT (generation) ON TABLE public.offline_delivery TO flooow_offline_audit_owner;
-- SPEC:1622 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=Control-only; frozen effects unchanged.
-- Required: Delivery outcome classification/origin/report consistency I4/I5/I12/I16/I17
GRANT SELECT (execution_id) ON TABLE public.offline_delivery TO flooow_offline_audit_owner;
-- SPEC:1623 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=Control-only; frozen effects unchanged.
-- Required: Delivery outcome classification/origin/report consistency I4/I5/I12/I16/I17
GRANT SELECT (instance_id) ON TABLE public.offline_delivery TO flooow_offline_audit_owner;
-- SPEC:1624 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=Control-only; frozen effects unchanged.
-- Required: Delivery outcome classification/origin/report consistency I4/I5/I12/I16/I17
GRANT SELECT (credential_id) ON TABLE public.offline_delivery TO flooow_offline_audit_owner;
-- SPEC:1625 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=Control-only; frozen effects unchanged.
-- Required: Delivery outcome classification/origin/report consistency I4/I5/I12/I16/I17
GRANT SELECT (initial_operation_id) ON TABLE public.offline_delivery TO flooow_offline_audit_owner;
-- SPEC:1626 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=Control-only; frozen effects unchanged.
-- Required: Delivery outcome classification/origin/report consistency I4/I5/I12/I16/I17
GRANT SELECT (fresh_applied_receipt_id) ON TABLE public.offline_delivery TO flooow_offline_audit_owner;
-- SPEC:1627 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=Control-only; frozen effects unchanged.
-- Required: Delivery outcome classification/origin/report consistency I4/I5/I12/I16/I17
GRANT SELECT (state) ON TABLE public.offline_delivery TO flooow_offline_audit_owner;
-- SPEC:1628 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=Control-only; frozen effects unchanged.
-- Required: Delivery outcome classification/origin/report consistency I4/I5/I12/I16/I17
GRANT SELECT (delivery_receipt_id) ON TABLE public.offline_delivery TO flooow_offline_audit_owner;
-- SPEC:1629 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=Control-only; frozen effects unchanged.
-- Required: Delivery outcome classification/origin/report consistency I4/I5/I12/I16/I17
GRANT SELECT (attempted_at) ON TABLE public.offline_delivery TO flooow_offline_audit_owner;
-- SPEC:1630 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=Control-only; frozen effects unchanged.
-- Required: Delivery outcome classification/origin/report consistency I4/I5/I12/I16/I17
GRANT SELECT (operation_deadline) ON TABLE public.offline_delivery TO flooow_offline_audit_owner;
-- SPEC:1631 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=Control-only; frozen effects unchanged.
-- Required: Delivery outcome classification/origin/report consistency I4/I5/I12/I16/I17
GRANT SELECT (observed_at) ON TABLE public.offline_delivery TO flooow_offline_audit_owner;
-- SPEC:1632 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=Control-only; frozen effects unchanged.
-- Required: Delivery outcome classification/origin/report consistency I4/I5/I12/I16/I17
GRANT SELECT (observation_code) ON TABLE public.offline_delivery TO flooow_offline_audit_owner;
-- SPEC:1633 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S02-S03; transitive=Control-only; frozen effects unchanged.
-- Required: Delivery outcome classification/origin/report consistency I4/I5/I12/I16/I17
GRANT SELECT (recorded_at) ON TABLE public.offline_delivery TO flooow_offline_audit_owner;
-- SPEC:1634 E READ_PRIVILEGE; consumer=AUTH/COMPLETE; entrypoint=S16-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact21.5 tuple, durable state/currentness/expiry/replay; inspector never validates caller possession
GRANT SELECT (admission_id) ON TABLE public.offline_admission TO flooow_offline_execution_owner;
-- SPEC:1635 E READ_PRIVILEGE; consumer=AUTH/COMPLETE; entrypoint=S16-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact21.5 tuple, durable state/currentness/expiry/replay; inspector never validates caller possession
GRANT SELECT (deployment_id) ON TABLE public.offline_admission TO flooow_offline_execution_owner;
-- SPEC:1636 E READ_PRIVILEGE; consumer=AUTH/COMPLETE; entrypoint=S16-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact21.5 tuple, durable state/currentness/expiry/replay; inspector never validates caller possession
GRANT SELECT (incarnation_id) ON TABLE public.offline_admission TO flooow_offline_execution_owner;
-- SPEC:1637 E READ_PRIVILEGE; consumer=AUTH/COMPLETE; entrypoint=S16-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact21.5 tuple, durable state/currentness/expiry/replay; inspector never validates caller possession
GRANT SELECT (binding_id) ON TABLE public.offline_admission TO flooow_offline_execution_owner;
-- SPEC:1638 E READ_PRIVILEGE; consumer=AUTH/COMPLETE; entrypoint=S16-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact21.5 tuple, durable state/currentness/expiry/replay; inspector never validates caller possession
GRANT SELECT (attempt_id) ON TABLE public.offline_admission TO flooow_offline_execution_owner;
-- SPEC:1639 E READ_PRIVILEGE; consumer=AUTH/COMPLETE; entrypoint=S16-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact21.5 tuple, durable state/currentness/expiry/replay; inspector never validates caller possession
GRANT SELECT (generation) ON TABLE public.offline_admission TO flooow_offline_execution_owner;
-- SPEC:1640 E READ_PRIVILEGE; consumer=AUTH/COMPLETE; entrypoint=S16-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact21.5 tuple, durable state/currentness/expiry/replay; inspector never validates caller possession
GRANT SELECT (execution_id) ON TABLE public.offline_admission TO flooow_offline_execution_owner;
-- SPEC:1641 E READ_PRIVILEGE; consumer=AUTH/COMPLETE; entrypoint=S16-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact21.5 tuple, durable state/currentness/expiry/replay; inspector never validates caller possession
GRANT SELECT (instance_id) ON TABLE public.offline_admission TO flooow_offline_execution_owner;
-- SPEC:1642 E READ_PRIVILEGE; consumer=AUTH/COMPLETE; entrypoint=S16-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact21.5 tuple, durable state/currentness/expiry/replay; inspector never validates caller possession
GRANT SELECT (executor_oid) ON TABLE public.offline_admission TO flooow_offline_execution_owner;
-- SPEC:1643 E READ_PRIVILEGE; consumer=AUTH/COMPLETE; entrypoint=S16-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact21.5 tuple, durable state/currentness/expiry/replay; inspector never validates caller possession
GRANT SELECT (credential_id) ON TABLE public.offline_admission TO flooow_offline_execution_owner;
-- SPEC:1644 E READ_PRIVILEGE; consumer=AUTH/COMPLETE; entrypoint=S16-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact21.5 tuple, durable state/currentness/expiry/replay; inspector never validates caller possession
GRANT SELECT (credential_revision) ON TABLE public.offline_admission TO flooow_offline_execution_owner;
-- SPEC:1645 E READ_PRIVILEGE; consumer=AUTH/COMPLETE; entrypoint=S16-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact21.5 tuple, durable state/currentness/expiry/replay; inspector never validates caller possession
GRANT SELECT (principal_id) ON TABLE public.offline_admission TO flooow_offline_execution_owner;
-- SPEC:1646 E READ_PRIVILEGE; consumer=AUTH/COMPLETE; entrypoint=S16-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact21.5 tuple, durable state/currentness/expiry/replay; inspector never validates caller possession
GRANT SELECT (organization_id) ON TABLE public.offline_admission TO flooow_offline_execution_owner;
-- SPEC:1647 E READ_PRIVILEGE; consumer=AUTH/COMPLETE; entrypoint=S16-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact21.5 tuple, durable state/currentness/expiry/replay; inspector never validates caller possession
GRANT SELECT (grant_id) ON TABLE public.offline_admission TO flooow_offline_execution_owner;
-- SPEC:1648 E READ_PRIVILEGE; consumer=AUTH/COMPLETE; entrypoint=S16-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact21.5 tuple, durable state/currentness/expiry/replay; inspector never validates caller possession
GRANT SELECT (grant_revision) ON TABLE public.offline_admission TO flooow_offline_execution_owner;
-- SPEC:1649 E READ_PRIVILEGE; consumer=AUTH/COMPLETE; entrypoint=S16-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact21.5 tuple, durable state/currentness/expiry/replay; inspector never validates caller possession
GRANT SELECT (authorization_fingerprint) ON TABLE public.offline_admission TO flooow_offline_execution_owner;
-- SPEC:1650 E READ_PRIVILEGE; consumer=AUTH/COMPLETE; entrypoint=S16-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact21.5 tuple, durable state/currentness/expiry/replay; inspector never validates caller possession
GRANT SELECT (permission) ON TABLE public.offline_admission TO flooow_offline_execution_owner;
-- SPEC:1651 E READ_PRIVILEGE; consumer=AUTH/COMPLETE; entrypoint=S16-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact21.5 tuple, durable state/currentness/expiry/replay; inspector never validates caller possession
GRANT SELECT (authenticated_at) ON TABLE public.offline_admission TO flooow_offline_execution_owner;
-- SPEC:1652 E READ_PRIVILEGE; consumer=AUTH/COMPLETE; entrypoint=S16-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact21.5 tuple, durable state/currentness/expiry/replay; inspector never validates caller possession
GRANT SELECT (expires_at) ON TABLE public.offline_admission TO flooow_offline_execution_owner;
-- SPEC:1653 E READ_PRIVILEGE; consumer=AUTH/COMPLETE; entrypoint=S16-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact21.5 tuple, durable state/currentness/expiry/replay; inspector never validates caller possession
GRANT SELECT (durable_state) ON TABLE public.offline_admission TO flooow_offline_execution_owner;
-- SPEC:1654 E READ_PRIVILEGE; consumer=AUTH/COMPLETE; entrypoint=S16-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact21.5 tuple, durable state/currentness/expiry/replay; inspector never validates caller possession
GRANT SELECT (consumed_decision_id) ON TABLE public.offline_admission TO flooow_offline_execution_owner;
-- SPEC:1655 E READ_PRIVILEGE; consumer=AUTH/COMPLETE; entrypoint=S16-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact21.5 tuple, durable state/currentness/expiry/replay; inspector never validates caller possession
GRANT SELECT (consumed_at) ON TABLE public.offline_admission TO flooow_offline_execution_owner;
-- SPEC:1656 A READ_PRIVILEGE; consumer=INSPECT.admissionValidity; entrypoint=S02-S03; transitive=Control-only; frozen effects unchanged.
-- Required: Exact21.5 tuple, durable state/currentness/expiry/replay; inspector never validates caller possession
GRANT SELECT (admission_id) ON TABLE public.offline_admission TO flooow_offline_audit_owner;
-- SPEC:1657 A READ_PRIVILEGE; consumer=INSPECT.admissionValidity; entrypoint=S02-S03; transitive=Control-only; frozen effects unchanged.
-- Required: Exact21.5 tuple, durable state/currentness/expiry/replay; inspector never validates caller possession
GRANT SELECT (deployment_id) ON TABLE public.offline_admission TO flooow_offline_audit_owner;
-- SPEC:1658 A READ_PRIVILEGE; consumer=INSPECT.admissionValidity; entrypoint=S02-S03; transitive=Control-only; frozen effects unchanged.
-- Required: Exact21.5 tuple, durable state/currentness/expiry/replay; inspector never validates caller possession
GRANT SELECT (incarnation_id) ON TABLE public.offline_admission TO flooow_offline_audit_owner;
-- SPEC:1659 A READ_PRIVILEGE; consumer=INSPECT.admissionValidity; entrypoint=S02-S03; transitive=Control-only; frozen effects unchanged.
-- Required: Exact21.5 tuple, durable state/currentness/expiry/replay; inspector never validates caller possession
GRANT SELECT (binding_id) ON TABLE public.offline_admission TO flooow_offline_audit_owner;
-- SPEC:1660 A READ_PRIVILEGE; consumer=INSPECT.admissionValidity; entrypoint=S02-S03; transitive=Control-only; frozen effects unchanged.
-- Required: Exact21.5 tuple, durable state/currentness/expiry/replay; inspector never validates caller possession
GRANT SELECT (attempt_id) ON TABLE public.offline_admission TO flooow_offline_audit_owner;
-- SPEC:1661 A READ_PRIVILEGE; consumer=INSPECT.admissionValidity; entrypoint=S02-S03; transitive=Control-only; frozen effects unchanged.
-- Required: Exact21.5 tuple, durable state/currentness/expiry/replay; inspector never validates caller possession
GRANT SELECT (generation) ON TABLE public.offline_admission TO flooow_offline_audit_owner;
-- SPEC:1662 A READ_PRIVILEGE; consumer=INSPECT.admissionValidity; entrypoint=S02-S03; transitive=Control-only; frozen effects unchanged.
-- Required: Exact21.5 tuple, durable state/currentness/expiry/replay; inspector never validates caller possession
GRANT SELECT (execution_id) ON TABLE public.offline_admission TO flooow_offline_audit_owner;
-- SPEC:1663 A READ_PRIVILEGE; consumer=INSPECT.admissionValidity; entrypoint=S02-S03; transitive=Control-only; frozen effects unchanged.
-- Required: Exact21.5 tuple, durable state/currentness/expiry/replay; inspector never validates caller possession
GRANT SELECT (instance_id) ON TABLE public.offline_admission TO flooow_offline_audit_owner;
-- SPEC:1664 A READ_PRIVILEGE; consumer=INSPECT.admissionValidity; entrypoint=S02-S03; transitive=Control-only; frozen effects unchanged.
-- Required: Exact21.5 tuple, durable state/currentness/expiry/replay; inspector never validates caller possession
GRANT SELECT (executor_oid) ON TABLE public.offline_admission TO flooow_offline_audit_owner;
-- SPEC:1665 A READ_PRIVILEGE; consumer=INSPECT.admissionValidity; entrypoint=S02-S03; transitive=Control-only; frozen effects unchanged.
-- Required: Exact21.5 tuple, durable state/currentness/expiry/replay; inspector never validates caller possession
GRANT SELECT (credential_id) ON TABLE public.offline_admission TO flooow_offline_audit_owner;
-- SPEC:1666 A READ_PRIVILEGE; consumer=INSPECT.admissionValidity; entrypoint=S02-S03; transitive=Control-only; frozen effects unchanged.
-- Required: Exact21.5 tuple, durable state/currentness/expiry/replay; inspector never validates caller possession
GRANT SELECT (credential_revision) ON TABLE public.offline_admission TO flooow_offline_audit_owner;
-- SPEC:1667 A READ_PRIVILEGE; consumer=INSPECT.admissionValidity; entrypoint=S02-S03; transitive=Control-only; frozen effects unchanged.
-- Required: Exact21.5 tuple, durable state/currentness/expiry/replay; inspector never validates caller possession
GRANT SELECT (principal_id) ON TABLE public.offline_admission TO flooow_offline_audit_owner;
-- SPEC:1668 A READ_PRIVILEGE; consumer=INSPECT.admissionValidity; entrypoint=S02-S03; transitive=Control-only; frozen effects unchanged.
-- Required: Exact21.5 tuple, durable state/currentness/expiry/replay; inspector never validates caller possession
GRANT SELECT (organization_id) ON TABLE public.offline_admission TO flooow_offline_audit_owner;
-- SPEC:1669 A READ_PRIVILEGE; consumer=INSPECT.admissionValidity; entrypoint=S02-S03; transitive=Control-only; frozen effects unchanged.
-- Required: Exact21.5 tuple, durable state/currentness/expiry/replay; inspector never validates caller possession
GRANT SELECT (grant_id) ON TABLE public.offline_admission TO flooow_offline_audit_owner;
-- SPEC:1670 A READ_PRIVILEGE; consumer=INSPECT.admissionValidity; entrypoint=S02-S03; transitive=Control-only; frozen effects unchanged.
-- Required: Exact21.5 tuple, durable state/currentness/expiry/replay; inspector never validates caller possession
GRANT SELECT (grant_revision) ON TABLE public.offline_admission TO flooow_offline_audit_owner;
-- SPEC:1671 A READ_PRIVILEGE; consumer=INSPECT.admissionValidity; entrypoint=S02-S03; transitive=Control-only; frozen effects unchanged.
-- Required: Exact21.5 tuple, durable state/currentness/expiry/replay; inspector never validates caller possession
GRANT SELECT (authorization_fingerprint) ON TABLE public.offline_admission TO flooow_offline_audit_owner;
-- SPEC:1672 A READ_PRIVILEGE; consumer=INSPECT.admissionValidity; entrypoint=S02-S03; transitive=Control-only; frozen effects unchanged.
-- Required: Exact21.5 tuple, durable state/currentness/expiry/replay; inspector never validates caller possession
GRANT SELECT (permission) ON TABLE public.offline_admission TO flooow_offline_audit_owner;
-- SPEC:1673 A READ_PRIVILEGE; consumer=INSPECT.admissionValidity; entrypoint=S02-S03; transitive=Control-only; frozen effects unchanged.
-- Required: Exact21.5 tuple, durable state/currentness/expiry/replay; inspector never validates caller possession
GRANT SELECT (authenticated_at) ON TABLE public.offline_admission TO flooow_offline_audit_owner;
-- SPEC:1674 A READ_PRIVILEGE; consumer=INSPECT.admissionValidity; entrypoint=S02-S03; transitive=Control-only; frozen effects unchanged.
-- Required: Exact21.5 tuple, durable state/currentness/expiry/replay; inspector never validates caller possession
GRANT SELECT (expires_at) ON TABLE public.offline_admission TO flooow_offline_audit_owner;
-- SPEC:1675 A READ_PRIVILEGE; consumer=INSPECT.admissionValidity; entrypoint=S02-S03; transitive=Control-only; frozen effects unchanged.
-- Required: Exact21.5 tuple, durable state/currentness/expiry/replay; inspector never validates caller possession
GRANT SELECT (durable_state) ON TABLE public.offline_admission TO flooow_offline_audit_owner;
-- SPEC:1676 A READ_PRIVILEGE; consumer=INSPECT.admissionValidity; entrypoint=S02-S03; transitive=Control-only; frozen effects unchanged.
-- Required: Exact21.5 tuple, durable state/currentness/expiry/replay; inspector never validates caller possession
GRANT SELECT (consumed_decision_id) ON TABLE public.offline_admission TO flooow_offline_audit_owner;
-- SPEC:1677 A READ_PRIVILEGE; consumer=INSPECT.admissionValidity; entrypoint=S02-S03; transitive=Control-only; frozen effects unchanged.
-- Required: Exact21.5 tuple, durable state/currentness/expiry/replay; inspector never validates caller possession
GRANT SELECT (consumed_at) ON TABLE public.offline_admission TO flooow_offline_audit_owner;
-- SPEC:1678 V READ_PRIVILEGE; consumer=VERIFY-STAGE; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact existing bound stage-receipt replay/lineage and original fresh Applied receipt; no cross-stage service selector
GRANT SELECT (binding_id) ON TABLE public.offline_stage_receipt TO flooow_offline_verification_owner;
-- SPEC:1679 V READ_PRIVILEGE; consumer=VERIFY-STAGE; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact existing bound stage-receipt replay/lineage and original fresh Applied receipt; no cross-stage service selector
GRANT SELECT (attempt_id) ON TABLE public.offline_stage_receipt TO flooow_offline_verification_owner;
-- SPEC:1680 V READ_PRIVILEGE; consumer=VERIFY-STAGE; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact existing bound stage-receipt replay/lineage and original fresh Applied receipt; no cross-stage service selector
GRANT SELECT (generation) ON TABLE public.offline_stage_receipt TO flooow_offline_verification_owner;
-- SPEC:1681 V READ_PRIVILEGE; consumer=VERIFY-STAGE; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact existing bound stage-receipt replay/lineage and original fresh Applied receipt; no cross-stage service selector
GRANT SELECT (execution_id) ON TABLE public.offline_stage_receipt TO flooow_offline_verification_owner;
-- SPEC:1682 V READ_PRIVILEGE; consumer=VERIFY-STAGE; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact existing bound stage-receipt replay/lineage and original fresh Applied receipt; no cross-stage service selector
GRANT SELECT (instance_id) ON TABLE public.offline_stage_receipt TO flooow_offline_verification_owner;
-- SPEC:1683 V READ_PRIVILEGE; consumer=VERIFY-STAGE; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact existing bound stage-receipt replay/lineage and original fresh Applied receipt; no cross-stage service selector
GRANT SELECT (stage) ON TABLE public.offline_stage_receipt TO flooow_offline_verification_owner;
-- SPEC:1684 V READ_PRIVILEGE; consumer=VERIFY-STAGE; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact existing bound stage-receipt replay/lineage and original fresh Applied receipt; no cross-stage service selector
GRANT SELECT (receipt_id) ON TABLE public.offline_stage_receipt TO flooow_offline_verification_owner;
-- SPEC:1685 V READ_PRIVILEGE; consumer=VERIFY-STAGE; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact existing bound stage-receipt replay/lineage and original fresh Applied receipt; no cross-stage service selector
GRANT SELECT (operation_id) ON TABLE public.offline_stage_receipt TO flooow_offline_verification_owner;
-- SPEC:1686 V READ_PRIVILEGE; consumer=VERIFY-STAGE; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact existing bound stage-receipt replay/lineage and original fresh Applied receipt; no cross-stage service selector
GRANT SELECT (frozen_receipt) ON TABLE public.offline_stage_receipt TO flooow_offline_verification_owner;
-- SPEC:1687 V READ_PRIVILEGE; consumer=VERIFY-STAGE; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact existing bound stage-receipt replay/lineage and original fresh Applied receipt; no cross-stage service selector
GRANT SELECT (effect_time) ON TABLE public.offline_stage_receipt TO flooow_offline_verification_owner;
-- SPEC:1688 I READ_PRIVILEGE; consumer=ISSUE-STAGE; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact existing bound stage-receipt replay/lineage and original fresh Applied receipt; no cross-stage service selector
GRANT SELECT (binding_id) ON TABLE public.offline_stage_receipt TO flooow_offline_issuance_owner;
-- SPEC:1689 I READ_PRIVILEGE; consumer=ISSUE-STAGE; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact existing bound stage-receipt replay/lineage and original fresh Applied receipt; no cross-stage service selector
GRANT SELECT (attempt_id) ON TABLE public.offline_stage_receipt TO flooow_offline_issuance_owner;
-- SPEC:1690 I READ_PRIVILEGE; consumer=ISSUE-STAGE; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact existing bound stage-receipt replay/lineage and original fresh Applied receipt; no cross-stage service selector
GRANT SELECT (generation) ON TABLE public.offline_stage_receipt TO flooow_offline_issuance_owner;
-- SPEC:1691 I READ_PRIVILEGE; consumer=ISSUE-STAGE; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact existing bound stage-receipt replay/lineage and original fresh Applied receipt; no cross-stage service selector
GRANT SELECT (execution_id) ON TABLE public.offline_stage_receipt TO flooow_offline_issuance_owner;
-- SPEC:1692 I READ_PRIVILEGE; consumer=ISSUE-STAGE; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact existing bound stage-receipt replay/lineage and original fresh Applied receipt; no cross-stage service selector
GRANT SELECT (instance_id) ON TABLE public.offline_stage_receipt TO flooow_offline_issuance_owner;
-- SPEC:1693 I READ_PRIVILEGE; consumer=ISSUE-STAGE; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact existing bound stage-receipt replay/lineage and original fresh Applied receipt; no cross-stage service selector
GRANT SELECT (stage) ON TABLE public.offline_stage_receipt TO flooow_offline_issuance_owner;
-- SPEC:1694 I READ_PRIVILEGE; consumer=ISSUE-STAGE; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact existing bound stage-receipt replay/lineage and original fresh Applied receipt; no cross-stage service selector
GRANT SELECT (receipt_id) ON TABLE public.offline_stage_receipt TO flooow_offline_issuance_owner;
-- SPEC:1695 I READ_PRIVILEGE; consumer=ISSUE-STAGE; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact existing bound stage-receipt replay/lineage and original fresh Applied receipt; no cross-stage service selector
GRANT SELECT (operation_id) ON TABLE public.offline_stage_receipt TO flooow_offline_issuance_owner;
-- SPEC:1696 I READ_PRIVILEGE; consumer=ISSUE-STAGE; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact existing bound stage-receipt replay/lineage and original fresh Applied receipt; no cross-stage service selector
GRANT SELECT (frozen_receipt) ON TABLE public.offline_stage_receipt TO flooow_offline_issuance_owner;
-- SPEC:1697 I READ_PRIVILEGE; consumer=ISSUE-STAGE; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact existing bound stage-receipt replay/lineage and original fresh Applied receipt; no cross-stage service selector
GRANT SELECT (effect_time) ON TABLE public.offline_stage_receipt TO flooow_offline_issuance_owner;
-- SPEC:1698 E READ_PRIVILEGE; consumer=DELIVERY/COMPLETE; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact existing bound stage-receipt replay/lineage and original fresh Applied receipt; no cross-stage service selector
GRANT SELECT (binding_id) ON TABLE public.offline_stage_receipt TO flooow_offline_execution_owner;
-- SPEC:1699 E READ_PRIVILEGE; consumer=DELIVERY/COMPLETE; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact existing bound stage-receipt replay/lineage and original fresh Applied receipt; no cross-stage service selector
GRANT SELECT (attempt_id) ON TABLE public.offline_stage_receipt TO flooow_offline_execution_owner;
-- SPEC:1700 E READ_PRIVILEGE; consumer=DELIVERY/COMPLETE; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact existing bound stage-receipt replay/lineage and original fresh Applied receipt; no cross-stage service selector
GRANT SELECT (generation) ON TABLE public.offline_stage_receipt TO flooow_offline_execution_owner;
-- SPEC:1701 E READ_PRIVILEGE; consumer=DELIVERY/COMPLETE; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact existing bound stage-receipt replay/lineage and original fresh Applied receipt; no cross-stage service selector
GRANT SELECT (execution_id) ON TABLE public.offline_stage_receipt TO flooow_offline_execution_owner;
-- SPEC:1702 E READ_PRIVILEGE; consumer=DELIVERY/COMPLETE; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact existing bound stage-receipt replay/lineage and original fresh Applied receipt; no cross-stage service selector
GRANT SELECT (instance_id) ON TABLE public.offline_stage_receipt TO flooow_offline_execution_owner;
-- SPEC:1703 E READ_PRIVILEGE; consumer=DELIVERY/COMPLETE; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact existing bound stage-receipt replay/lineage and original fresh Applied receipt; no cross-stage service selector
GRANT SELECT (stage) ON TABLE public.offline_stage_receipt TO flooow_offline_execution_owner;
-- SPEC:1704 E READ_PRIVILEGE; consumer=DELIVERY/COMPLETE; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact existing bound stage-receipt replay/lineage and original fresh Applied receipt; no cross-stage service selector
GRANT SELECT (receipt_id) ON TABLE public.offline_stage_receipt TO flooow_offline_execution_owner;
-- SPEC:1705 E READ_PRIVILEGE; consumer=DELIVERY/COMPLETE; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact existing bound stage-receipt replay/lineage and original fresh Applied receipt; no cross-stage service selector
GRANT SELECT (operation_id) ON TABLE public.offline_stage_receipt TO flooow_offline_execution_owner;
-- SPEC:1706 E READ_PRIVILEGE; consumer=DELIVERY/COMPLETE; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact existing bound stage-receipt replay/lineage and original fresh Applied receipt; no cross-stage service selector
GRANT SELECT (frozen_receipt) ON TABLE public.offline_stage_receipt TO flooow_offline_execution_owner;
-- SPEC:1707 E READ_PRIVILEGE; consumer=DELIVERY/COMPLETE; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact existing bound stage-receipt replay/lineage and original fresh Applied receipt; no cross-stage service selector
GRANT SELECT (effect_time) ON TABLE public.offline_stage_receipt TO flooow_offline_execution_owner;
-- SPEC:1708 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact existing bound stage-receipt replay/lineage and original fresh Applied receipt; no cross-stage service selector
GRANT SELECT (binding_id) ON TABLE public.offline_stage_receipt TO flooow_offline_audit_owner;
-- SPEC:1709 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact existing bound stage-receipt replay/lineage and original fresh Applied receipt; no cross-stage service selector
GRANT SELECT (attempt_id) ON TABLE public.offline_stage_receipt TO flooow_offline_audit_owner;
-- SPEC:1710 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact existing bound stage-receipt replay/lineage and original fresh Applied receipt; no cross-stage service selector
GRANT SELECT (generation) ON TABLE public.offline_stage_receipt TO flooow_offline_audit_owner;
-- SPEC:1711 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact existing bound stage-receipt replay/lineage and original fresh Applied receipt; no cross-stage service selector
GRANT SELECT (execution_id) ON TABLE public.offline_stage_receipt TO flooow_offline_audit_owner;
-- SPEC:1712 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact existing bound stage-receipt replay/lineage and original fresh Applied receipt; no cross-stage service selector
GRANT SELECT (instance_id) ON TABLE public.offline_stage_receipt TO flooow_offline_audit_owner;
-- SPEC:1713 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact existing bound stage-receipt replay/lineage and original fresh Applied receipt; no cross-stage service selector
GRANT SELECT (stage) ON TABLE public.offline_stage_receipt TO flooow_offline_audit_owner;
-- SPEC:1714 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact existing bound stage-receipt replay/lineage and original fresh Applied receipt; no cross-stage service selector
GRANT SELECT (receipt_id) ON TABLE public.offline_stage_receipt TO flooow_offline_audit_owner;
-- SPEC:1715 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact existing bound stage-receipt replay/lineage and original fresh Applied receipt; no cross-stage service selector
GRANT SELECT (operation_id) ON TABLE public.offline_stage_receipt TO flooow_offline_audit_owner;
-- SPEC:1716 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact existing bound stage-receipt replay/lineage and original fresh Applied receipt; no cross-stage service selector
GRANT SELECT (frozen_receipt) ON TABLE public.offline_stage_receipt TO flooow_offline_audit_owner;
-- SPEC:1717 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact existing bound stage-receipt replay/lineage and original fresh Applied receipt; no cross-stage service selector
GRANT SELECT (effect_time) ON TABLE public.offline_stage_receipt TO flooow_offline_audit_owner;
-- SPEC:1718 V READ_PRIVILEGE; consumer=GUARD-V; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: M requires pre-decision eligible reconciliation or S02/S03 state
GRANT SELECT (binding_id) ON TABLE public.offline_reconciliation TO flooow_offline_verification_owner;
-- SPEC:1719 V READ_PRIVILEGE; consumer=GUARD-V; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: M requires pre-decision eligible reconciliation or S02/S03 state
GRANT SELECT (state) ON TABLE public.offline_reconciliation TO flooow_offline_verification_owner;
-- SPEC:1720 I READ_PRIVILEGE; consumer=GUARD-I; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: M requires pre-decision eligible reconciliation or S02/S03 state
GRANT SELECT (binding_id) ON TABLE public.offline_reconciliation TO flooow_offline_issuance_owner;
-- SPEC:1721 I READ_PRIVILEGE; consumer=GUARD-I; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: M requires pre-decision eligible reconciliation or S02/S03 state
GRANT SELECT (state) ON TABLE public.offline_reconciliation TO flooow_offline_issuance_owner;
-- SPEC:1722 E READ_PRIVILEGE; consumer=GUARD-E; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: M requires pre-decision eligible reconciliation or S02/S03 state
GRANT SELECT (binding_id) ON TABLE public.offline_reconciliation TO flooow_offline_execution_owner;
-- SPEC:1723 E READ_PRIVILEGE; consumer=GUARD-E; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: M requires pre-decision eligible reconciliation or S02/S03 state
GRANT SELECT (state) ON TABLE public.offline_reconciliation TO flooow_offline_execution_owner;
-- SPEC:1724 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: M requires pre-decision eligible reconciliation or S02/S03 state
GRANT SELECT (binding_id) ON TABLE public.offline_reconciliation TO flooow_offline_audit_owner;
-- SPEC:1725 A READ_PRIVILEGE; consumer=INSPECT/RECON; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: M requires pre-decision eligible reconciliation or S02/S03 state
GRANT SELECT (state) ON TABLE public.offline_reconciliation TO flooow_offline_audit_owner;
-- SPEC:1726 P READ_PRIVILEGE; consumer=GUARD-P; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: M requires pre-decision eligible reconciliation or S02/S03 state
GRANT SELECT (binding_id) ON TABLE public.offline_reconciliation TO flooow_offline_principal_lock_owner;
-- SPEC:1727 P READ_PRIVILEGE; consumer=GUARD-P; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: M requires pre-decision eligible reconciliation or S02/S03 state
GRANT SELECT (state) ON TABLE public.offline_reconciliation TO flooow_offline_principal_lock_owner;
-- SPEC:1728 V READ_PRIVILEGE; consumer=GUARD-V; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: M/claim requires NONE; inspector preserves immutable terminal result
GRANT SELECT (binding_id) ON TABLE public.offline_ceremony_result TO flooow_offline_verification_owner;
-- SPEC:1729 V READ_PRIVILEGE; consumer=GUARD-V; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: M/claim requires NONE; inspector preserves immutable terminal result
GRANT SELECT (result) ON TABLE public.offline_ceremony_result TO flooow_offline_verification_owner;
-- SPEC:1730 I READ_PRIVILEGE; consumer=GUARD-I; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: M/claim requires NONE; inspector preserves immutable terminal result
GRANT SELECT (binding_id) ON TABLE public.offline_ceremony_result TO flooow_offline_issuance_owner;
-- SPEC:1731 I READ_PRIVILEGE; consumer=GUARD-I; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: M/claim requires NONE; inspector preserves immutable terminal result
GRANT SELECT (result) ON TABLE public.offline_ceremony_result TO flooow_offline_issuance_owner;
-- SPEC:1732 E READ_PRIVILEGE; consumer=GUARD-E; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: M/claim requires NONE; inspector preserves immutable terminal result
GRANT SELECT (binding_id) ON TABLE public.offline_ceremony_result TO flooow_offline_execution_owner;
-- SPEC:1733 E READ_PRIVILEGE; consumer=GUARD-E; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: M/claim requires NONE; inspector preserves immutable terminal result
GRANT SELECT (result) ON TABLE public.offline_ceremony_result TO flooow_offline_execution_owner;
-- SPEC:1734 A READ_PRIVILEGE; consumer=INSPECT; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: M/claim requires NONE; inspector preserves immutable terminal result
GRANT SELECT (binding_id) ON TABLE public.offline_ceremony_result TO flooow_offline_audit_owner;
-- SPEC:1735 A READ_PRIVILEGE; consumer=INSPECT; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: M/claim requires NONE; inspector preserves immutable terminal result
GRANT SELECT (result) ON TABLE public.offline_ceremony_result TO flooow_offline_audit_owner;
-- SPEC:1736 P READ_PRIVILEGE; consumer=GUARD-P; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: M/claim requires NONE; inspector preserves immutable terminal result
GRANT SELECT (binding_id) ON TABLE public.offline_ceremony_result TO flooow_offline_principal_lock_owner;
-- SPEC:1737 P READ_PRIVILEGE; consumer=GUARD-P; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: M/claim requires NONE; inspector preserves immutable terminal result
GRANT SELECT (result) ON TABLE public.offline_ceremony_result TO flooow_offline_principal_lock_owner;
-- SPEC:1738 Q READ_PRIVILEGE; consumer=GUARD-Q; entrypoint=internal Q; transitive=Control-only; frozen effects unchanged.
-- Required: M/claim requires NONE; inspector preserves immutable terminal result
GRANT SELECT (binding_id) ON TABLE public.offline_ceremony_result TO flooow_offline_readiness_owner;
-- SPEC:1739 Q READ_PRIVILEGE; consumer=GUARD-Q; entrypoint=internal Q; transitive=Control-only; frozen effects unchanged.
-- Required: M/claim requires NONE; inspector preserves immutable terminal result
GRANT SELECT (result) ON TABLE public.offline_ceremony_result TO flooow_offline_readiness_owner;
-- SPEC:1740 V READ_PRIVILEGE; consumer=GUARD-V; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Current READY/incarnation/policy/watchdog bounded eligibility; A/Z R ignores mutation expiry
GRANT SELECT (deployment_id) ON TABLE public.offline_readiness TO flooow_offline_verification_owner;
-- SPEC:1741 V READ_PRIVILEGE; consumer=GUARD-V; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Current READY/incarnation/policy/watchdog bounded eligibility; A/Z R ignores mutation expiry
GRANT SELECT (incarnation_id) ON TABLE public.offline_readiness TO flooow_offline_verification_owner;
-- SPEC:1742 V READ_PRIVILEGE; consumer=GUARD-V; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Current READY/incarnation/policy/watchdog bounded eligibility; A/Z R ignores mutation expiry
GRANT SELECT (state) ON TABLE public.offline_readiness TO flooow_offline_verification_owner;
-- SPEC:1743 V READ_PRIVILEGE; consumer=GUARD-V; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Current READY/incarnation/policy/watchdog bounded eligibility; A/Z R ignores mutation expiry
GRANT SELECT (policy_version) ON TABLE public.offline_readiness TO flooow_offline_verification_owner;
-- SPEC:1744 V READ_PRIVILEGE; consumer=GUARD-V; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Current READY/incarnation/policy/watchdog bounded eligibility; A/Z R ignores mutation expiry
GRANT SELECT (policy_digest) ON TABLE public.offline_readiness TO flooow_offline_verification_owner;
-- SPEC:1745 V READ_PRIVILEGE; consumer=GUARD-V; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Current READY/incarnation/policy/watchdog bounded eligibility; A/Z R ignores mutation expiry
GRANT SELECT (watchdog_checked_at) ON TABLE public.offline_readiness TO flooow_offline_verification_owner;
-- SPEC:1746 V READ_PRIVILEGE; consumer=GUARD-V; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Current READY/incarnation/policy/watchdog bounded eligibility; A/Z R ignores mutation expiry
GRANT SELECT (watchdog_healthy) ON TABLE public.offline_readiness TO flooow_offline_verification_owner;
-- SPEC:1747 I READ_PRIVILEGE; consumer=GUARD-I; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Current READY/incarnation/policy/watchdog bounded eligibility; A/Z R ignores mutation expiry
GRANT SELECT (deployment_id) ON TABLE public.offline_readiness TO flooow_offline_issuance_owner;
-- SPEC:1748 I READ_PRIVILEGE; consumer=GUARD-I; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Current READY/incarnation/policy/watchdog bounded eligibility; A/Z R ignores mutation expiry
GRANT SELECT (incarnation_id) ON TABLE public.offline_readiness TO flooow_offline_issuance_owner;
-- SPEC:1749 I READ_PRIVILEGE; consumer=GUARD-I; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Current READY/incarnation/policy/watchdog bounded eligibility; A/Z R ignores mutation expiry
GRANT SELECT (state) ON TABLE public.offline_readiness TO flooow_offline_issuance_owner;
-- SPEC:1750 I READ_PRIVILEGE; consumer=GUARD-I; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Current READY/incarnation/policy/watchdog bounded eligibility; A/Z R ignores mutation expiry
GRANT SELECT (policy_version) ON TABLE public.offline_readiness TO flooow_offline_issuance_owner;
-- SPEC:1751 I READ_PRIVILEGE; consumer=GUARD-I; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Current READY/incarnation/policy/watchdog bounded eligibility; A/Z R ignores mutation expiry
GRANT SELECT (policy_digest) ON TABLE public.offline_readiness TO flooow_offline_issuance_owner;
-- SPEC:1752 I READ_PRIVILEGE; consumer=GUARD-I; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Current READY/incarnation/policy/watchdog bounded eligibility; A/Z R ignores mutation expiry
GRANT SELECT (watchdog_checked_at) ON TABLE public.offline_readiness TO flooow_offline_issuance_owner;
-- SPEC:1753 I READ_PRIVILEGE; consumer=GUARD-I; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Current READY/incarnation/policy/watchdog bounded eligibility; A/Z R ignores mutation expiry
GRANT SELECT (watchdog_healthy) ON TABLE public.offline_readiness TO flooow_offline_issuance_owner;
-- SPEC:1754 E READ_PRIVILEGE; consumer=GUARD-E; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Current READY/incarnation/policy/watchdog bounded eligibility; A/Z R ignores mutation expiry
GRANT SELECT (deployment_id) ON TABLE public.offline_readiness TO flooow_offline_execution_owner;
-- SPEC:1755 E READ_PRIVILEGE; consumer=GUARD-E; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Current READY/incarnation/policy/watchdog bounded eligibility; A/Z R ignores mutation expiry
GRANT SELECT (incarnation_id) ON TABLE public.offline_readiness TO flooow_offline_execution_owner;
-- SPEC:1756 E READ_PRIVILEGE; consumer=GUARD-E; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Current READY/incarnation/policy/watchdog bounded eligibility; A/Z R ignores mutation expiry
GRANT SELECT (state) ON TABLE public.offline_readiness TO flooow_offline_execution_owner;
-- SPEC:1757 E READ_PRIVILEGE; consumer=GUARD-E; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Current READY/incarnation/policy/watchdog bounded eligibility; A/Z R ignores mutation expiry
GRANT SELECT (policy_version) ON TABLE public.offline_readiness TO flooow_offline_execution_owner;
-- SPEC:1758 E READ_PRIVILEGE; consumer=GUARD-E; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Current READY/incarnation/policy/watchdog bounded eligibility; A/Z R ignores mutation expiry
GRANT SELECT (policy_digest) ON TABLE public.offline_readiness TO flooow_offline_execution_owner;
-- SPEC:1759 E READ_PRIVILEGE; consumer=GUARD-E; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Current READY/incarnation/policy/watchdog bounded eligibility; A/Z R ignores mutation expiry
GRANT SELECT (watchdog_checked_at) ON TABLE public.offline_readiness TO flooow_offline_execution_owner;
-- SPEC:1760 E READ_PRIVILEGE; consumer=GUARD-E; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Current READY/incarnation/policy/watchdog bounded eligibility; A/Z R ignores mutation expiry
GRANT SELECT (watchdog_healthy) ON TABLE public.offline_readiness TO flooow_offline_execution_owner;
-- SPEC:1761 A READ_PRIVILEGE; consumer=GUARD-A; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Current READY/incarnation/policy/watchdog bounded eligibility; A/Z R ignores mutation expiry
GRANT SELECT (deployment_id) ON TABLE public.offline_readiness TO flooow_offline_audit_owner;
-- SPEC:1762 A READ_PRIVILEGE; consumer=GUARD-A; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Current READY/incarnation/policy/watchdog bounded eligibility; A/Z R ignores mutation expiry
GRANT SELECT (incarnation_id) ON TABLE public.offline_readiness TO flooow_offline_audit_owner;
-- SPEC:1763 A READ_PRIVILEGE; consumer=GUARD-A; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Current READY/incarnation/policy/watchdog bounded eligibility; A/Z R ignores mutation expiry
GRANT SELECT (state) ON TABLE public.offline_readiness TO flooow_offline_audit_owner;
-- SPEC:1764 A READ_PRIVILEGE; consumer=GUARD-A; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Current READY/incarnation/policy/watchdog bounded eligibility; A/Z R ignores mutation expiry
GRANT SELECT (policy_version) ON TABLE public.offline_readiness TO flooow_offline_audit_owner;
-- SPEC:1765 A READ_PRIVILEGE; consumer=GUARD-A; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Current READY/incarnation/policy/watchdog bounded eligibility; A/Z R ignores mutation expiry
GRANT SELECT (policy_digest) ON TABLE public.offline_readiness TO flooow_offline_audit_owner;
-- SPEC:1766 A READ_PRIVILEGE; consumer=GUARD-A; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Current READY/incarnation/policy/watchdog bounded eligibility; A/Z R ignores mutation expiry
GRANT SELECT (watchdog_checked_at) ON TABLE public.offline_readiness TO flooow_offline_audit_owner;
-- SPEC:1767 A READ_PRIVILEGE; consumer=GUARD-A; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Current READY/incarnation/policy/watchdog bounded eligibility; A/Z R ignores mutation expiry
GRANT SELECT (watchdog_healthy) ON TABLE public.offline_readiness TO flooow_offline_audit_owner;
-- SPEC:1768 P READ_PRIVILEGE; consumer=GUARD-P; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: Current READY/incarnation/policy/watchdog bounded eligibility; A/Z R ignores mutation expiry
GRANT SELECT (deployment_id) ON TABLE public.offline_readiness TO flooow_offline_principal_lock_owner;
-- SPEC:1769 P READ_PRIVILEGE; consumer=GUARD-P; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: Current READY/incarnation/policy/watchdog bounded eligibility; A/Z R ignores mutation expiry
GRANT SELECT (incarnation_id) ON TABLE public.offline_readiness TO flooow_offline_principal_lock_owner;
-- SPEC:1770 P READ_PRIVILEGE; consumer=GUARD-P; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: Current READY/incarnation/policy/watchdog bounded eligibility; A/Z R ignores mutation expiry
GRANT SELECT (state) ON TABLE public.offline_readiness TO flooow_offline_principal_lock_owner;
-- SPEC:1771 P READ_PRIVILEGE; consumer=GUARD-P; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: Current READY/incarnation/policy/watchdog bounded eligibility; A/Z R ignores mutation expiry
GRANT SELECT (policy_version) ON TABLE public.offline_readiness TO flooow_offline_principal_lock_owner;
-- SPEC:1772 P READ_PRIVILEGE; consumer=GUARD-P; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: Current READY/incarnation/policy/watchdog bounded eligibility; A/Z R ignores mutation expiry
GRANT SELECT (policy_digest) ON TABLE public.offline_readiness TO flooow_offline_principal_lock_owner;
-- SPEC:1773 P READ_PRIVILEGE; consumer=GUARD-P; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: Current READY/incarnation/policy/watchdog bounded eligibility; A/Z R ignores mutation expiry
GRANT SELECT (watchdog_checked_at) ON TABLE public.offline_readiness TO flooow_offline_principal_lock_owner;
-- SPEC:1774 P READ_PRIVILEGE; consumer=GUARD-P; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: Current READY/incarnation/policy/watchdog bounded eligibility; A/Z R ignores mutation expiry
GRANT SELECT (watchdog_healthy) ON TABLE public.offline_readiness TO flooow_offline_principal_lock_owner;
-- SPEC:1775 Z READ_PRIVILEGE; consumer=GUARD-Z; entrypoint=internal Z; transitive=Control-only; frozen effects unchanged.
-- Required: Current READY/incarnation/policy/watchdog bounded eligibility; A/Z R ignores mutation expiry
GRANT SELECT (deployment_id) ON TABLE public.offline_readiness TO flooow_offline_intent_audit_owner;
-- SPEC:1776 Z READ_PRIVILEGE; consumer=GUARD-Z; entrypoint=internal Z; transitive=Control-only; frozen effects unchanged.
-- Required: Current READY/incarnation/policy/watchdog bounded eligibility; A/Z R ignores mutation expiry
GRANT SELECT (incarnation_id) ON TABLE public.offline_readiness TO flooow_offline_intent_audit_owner;
-- SPEC:1777 Z READ_PRIVILEGE; consumer=GUARD-Z; entrypoint=internal Z; transitive=Control-only; frozen effects unchanged.
-- Required: Current READY/incarnation/policy/watchdog bounded eligibility; A/Z R ignores mutation expiry
GRANT SELECT (state) ON TABLE public.offline_readiness TO flooow_offline_intent_audit_owner;
-- SPEC:1778 Z READ_PRIVILEGE; consumer=GUARD-Z; entrypoint=internal Z; transitive=Control-only; frozen effects unchanged.
-- Required: Current READY/incarnation/policy/watchdog bounded eligibility; A/Z R ignores mutation expiry
GRANT SELECT (policy_version) ON TABLE public.offline_readiness TO flooow_offline_intent_audit_owner;
-- SPEC:1779 Z READ_PRIVILEGE; consumer=GUARD-Z; entrypoint=internal Z; transitive=Control-only; frozen effects unchanged.
-- Required: Current READY/incarnation/policy/watchdog bounded eligibility; A/Z R ignores mutation expiry
GRANT SELECT (policy_digest) ON TABLE public.offline_readiness TO flooow_offline_intent_audit_owner;
-- SPEC:1780 Z READ_PRIVILEGE; consumer=GUARD-Z; entrypoint=internal Z; transitive=Control-only; frozen effects unchanged.
-- Required: Current READY/incarnation/policy/watchdog bounded eligibility; A/Z R ignores mutation expiry
GRANT SELECT (watchdog_checked_at) ON TABLE public.offline_readiness TO flooow_offline_intent_audit_owner;
-- SPEC:1781 Z READ_PRIVILEGE; consumer=GUARD-Z; entrypoint=internal Z; transitive=Control-only; frozen effects unchanged.
-- Required: Current READY/incarnation/policy/watchdog bounded eligibility; A/Z R ignores mutation expiry
GRANT SELECT (watchdog_healthy) ON TABLE public.offline_readiness TO flooow_offline_intent_audit_owner;
-- SPEC:1782 Q READ_PRIVILEGE; consumer=READINESS; entrypoint=internal Q; transitive=Control-only; frozen effects unchanged.
-- Required: Independent expected manifests and current active-key selection; no adoption of drift
GRANT SELECT (deployment_id) ON TABLE public.offline_readiness TO flooow_offline_readiness_owner;
-- SPEC:1783 Q READ_PRIVILEGE; consumer=READINESS; entrypoint=internal Q; transitive=Control-only; frozen effects unchanged.
-- Required: Independent expected manifests and current active-key selection; no adoption of drift
GRANT SELECT (incarnation_id) ON TABLE public.offline_readiness TO flooow_offline_readiness_owner;
-- SPEC:1784 Q READ_PRIVILEGE; consumer=READINESS; entrypoint=internal Q; transitive=Control-only; frozen effects unchanged.
-- Required: Independent expected manifests and current active-key selection; no adoption of drift
GRANT SELECT (state) ON TABLE public.offline_readiness TO flooow_offline_readiness_owner;
-- SPEC:1785 Q READ_PRIVILEGE; consumer=READINESS; entrypoint=internal Q; transitive=Control-only; frozen effects unchanged.
-- Required: Independent expected manifests and current active-key selection; no adoption of drift
GRANT SELECT (policy_version) ON TABLE public.offline_readiness TO flooow_offline_readiness_owner;
-- SPEC:1786 Q READ_PRIVILEGE; consumer=READINESS; entrypoint=internal Q; transitive=Control-only; frozen effects unchanged.
-- Required: Independent expected manifests and current active-key selection; no adoption of drift
GRANT SELECT (policy_digest) ON TABLE public.offline_readiness TO flooow_offline_readiness_owner;
-- SPEC:1787 Q READ_PRIVILEGE; consumer=READINESS; entrypoint=internal Q; transitive=Control-only; frozen effects unchanged.
-- Required: Independent expected manifests and current active-key selection; no adoption of drift
GRANT SELECT (watchdog_checked_at) ON TABLE public.offline_readiness TO flooow_offline_readiness_owner;
-- SPEC:1788 Q READ_PRIVILEGE; consumer=READINESS; entrypoint=internal Q; transitive=Control-only; frozen effects unchanged.
-- Required: Independent expected manifests and current active-key selection; no adoption of drift
GRANT SELECT (watchdog_healthy) ON TABLE public.offline_readiness TO flooow_offline_readiness_owner;
-- SPEC:1789 Q READ_PRIVILEGE; consumer=READINESS; entrypoint=internal Q; transitive=Control-only; frozen effects unchanged.
-- Required: Independent expected manifests and current active-key selection; no adoption of drift
GRANT SELECT (active_key_version) ON TABLE public.offline_readiness TO flooow_offline_readiness_owner;
-- SPEC:1790 Q READ_PRIVILEGE; consumer=READINESS; entrypoint=internal Q; transitive=Control-only; frozen effects unchanged.
-- Required: Independent expected manifests and current active-key selection; no adoption of drift
GRANT SELECT (history_manifest) ON TABLE public.offline_readiness TO flooow_offline_readiness_owner;
-- SPEC:1791 Q READ_PRIVILEGE; consumer=READINESS; entrypoint=internal Q; transitive=Control-only; frozen effects unchanged.
-- Required: Independent expected manifests and current active-key selection; no adoption of drift
GRANT SELECT (acl_manifest) ON TABLE public.offline_readiness TO flooow_offline_readiness_owner;
-- SPEC:1792 V READ_PRIVILEGE; consumer=GUARD-V; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact bound canonical policy values: transaction/read/attempt/expiry/watchdog time checks; no semantic writes
GRANT SELECT (policy_version) ON TABLE public.offline_deadline_policy TO flooow_offline_verification_owner;
-- SPEC:1793 V READ_PRIVILEGE; consumer=GUARD-V; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact bound canonical policy values: transaction/read/attempt/expiry/watchdog time checks; no semantic writes
GRANT SELECT (policy_digest) ON TABLE public.offline_deadline_policy TO flooow_offline_verification_owner;
-- SPEC:1794 V READ_PRIVILEGE; consumer=GUARD-V; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Exact bound canonical policy values: transaction/read/attempt/expiry/watchdog time checks; no semantic writes
GRANT SELECT (canonical_policy) ON TABLE public.offline_deadline_policy TO flooow_offline_verification_owner;
-- SPEC:1795 I READ_PRIVILEGE; consumer=GUARD-I; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact bound canonical policy values: transaction/read/attempt/expiry/watchdog time checks; no semantic writes
GRANT SELECT (policy_version) ON TABLE public.offline_deadline_policy TO flooow_offline_issuance_owner;
-- SPEC:1796 I READ_PRIVILEGE; consumer=GUARD-I; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact bound canonical policy values: transaction/read/attempt/expiry/watchdog time checks; no semantic writes
GRANT SELECT (policy_digest) ON TABLE public.offline_deadline_policy TO flooow_offline_issuance_owner;
-- SPEC:1797 I READ_PRIVILEGE; consumer=GUARD-I; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Exact bound canonical policy values: transaction/read/attempt/expiry/watchdog time checks; no semantic writes
GRANT SELECT (canonical_policy) ON TABLE public.offline_deadline_policy TO flooow_offline_issuance_owner;
-- SPEC:1798 E READ_PRIVILEGE; consumer=GUARD-E; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact bound canonical policy values: transaction/read/attempt/expiry/watchdog time checks; no semantic writes
GRANT SELECT (policy_version) ON TABLE public.offline_deadline_policy TO flooow_offline_execution_owner;
-- SPEC:1799 E READ_PRIVILEGE; consumer=GUARD-E; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact bound canonical policy values: transaction/read/attempt/expiry/watchdog time checks; no semantic writes
GRANT SELECT (policy_digest) ON TABLE public.offline_deadline_policy TO flooow_offline_execution_owner;
-- SPEC:1800 E READ_PRIVILEGE; consumer=GUARD-E; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Exact bound canonical policy values: transaction/read/attempt/expiry/watchdog time checks; no semantic writes
GRANT SELECT (canonical_policy) ON TABLE public.offline_deadline_policy TO flooow_offline_execution_owner;
-- SPEC:1801 A READ_PRIVILEGE; consumer=GUARD-A; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact bound canonical policy values: transaction/read/attempt/expiry/watchdog time checks; no semantic writes
GRANT SELECT (policy_version) ON TABLE public.offline_deadline_policy TO flooow_offline_audit_owner;
-- SPEC:1802 A READ_PRIVILEGE; consumer=GUARD-A; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact bound canonical policy values: transaction/read/attempt/expiry/watchdog time checks; no semantic writes
GRANT SELECT (policy_digest) ON TABLE public.offline_deadline_policy TO flooow_offline_audit_owner;
-- SPEC:1803 A READ_PRIVILEGE; consumer=GUARD-A; entrypoint=S01-S04; transitive=Control-only; frozen effects unchanged.
-- Required: Exact bound canonical policy values: transaction/read/attempt/expiry/watchdog time checks; no semantic writes
GRANT SELECT (canonical_policy) ON TABLE public.offline_deadline_policy TO flooow_offline_audit_owner;
-- SPEC:1804 P READ_PRIVILEGE; consumer=GUARD-P; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: Exact bound canonical policy values: transaction/read/attempt/expiry/watchdog time checks; no semantic writes
GRANT SELECT (policy_version) ON TABLE public.offline_deadline_policy TO flooow_offline_principal_lock_owner;
-- SPEC:1805 P READ_PRIVILEGE; consumer=GUARD-P; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: Exact bound canonical policy values: transaction/read/attempt/expiry/watchdog time checks; no semantic writes
GRANT SELECT (policy_digest) ON TABLE public.offline_deadline_policy TO flooow_offline_principal_lock_owner;
-- SPEC:1806 P READ_PRIVILEGE; consumer=GUARD-P; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: Exact bound canonical policy values: transaction/read/attempt/expiry/watchdog time checks; no semantic writes
GRANT SELECT (canonical_policy) ON TABLE public.offline_deadline_policy TO flooow_offline_principal_lock_owner;
-- SPEC:1807 Q READ_PRIVILEGE; consumer=GUARD-Q; entrypoint=internal Q; transitive=Control-only; frozen effects unchanged.
-- Required: Exact bound canonical policy values: transaction/read/attempt/expiry/watchdog time checks; no semantic writes
GRANT SELECT (policy_version) ON TABLE public.offline_deadline_policy TO flooow_offline_readiness_owner;
-- SPEC:1808 Q READ_PRIVILEGE; consumer=GUARD-Q; entrypoint=internal Q; transitive=Control-only; frozen effects unchanged.
-- Required: Exact bound canonical policy values: transaction/read/attempt/expiry/watchdog time checks; no semantic writes
GRANT SELECT (policy_digest) ON TABLE public.offline_deadline_policy TO flooow_offline_readiness_owner;
-- SPEC:1809 Q READ_PRIVILEGE; consumer=GUARD-Q; entrypoint=internal Q; transitive=Control-only; frozen effects unchanged.
-- Required: Exact bound canonical policy values: transaction/read/attempt/expiry/watchdog time checks; no semantic writes
GRANT SELECT (canonical_policy) ON TABLE public.offline_deadline_policy TO flooow_offline_readiness_owner;
-- SPEC:1810 Z READ_PRIVILEGE; consumer=GUARD-Z; entrypoint=internal Z; transitive=Control-only; frozen effects unchanged.
-- Required: Exact bound canonical policy values: transaction/read/attempt/expiry/watchdog time checks; no semantic writes
GRANT SELECT (policy_version) ON TABLE public.offline_deadline_policy TO flooow_offline_intent_audit_owner;
-- SPEC:1811 Z READ_PRIVILEGE; consumer=GUARD-Z; entrypoint=internal Z; transitive=Control-only; frozen effects unchanged.
-- Required: Exact bound canonical policy values: transaction/read/attempt/expiry/watchdog time checks; no semantic writes
GRANT SELECT (policy_digest) ON TABLE public.offline_deadline_policy TO flooow_offline_intent_audit_owner;
-- SPEC:1812 Z READ_PRIVILEGE; consumer=GUARD-Z; entrypoint=internal Z; transitive=Control-only; frozen effects unchanged.
-- Required: Exact bound canonical policy values: transaction/read/attempt/expiry/watchdog time checks; no semantic writes
GRANT SELECT (canonical_policy) ON TABLE public.offline_deadline_policy TO flooow_offline_intent_audit_owner;
-- SPEC:1813 Q READ_PRIVILEGE; consumer=READINESS.HMAC; entrypoint=internal Q; transitive=Control-only; frozen effects unchanged.
-- Required: Unique current ACTIVE key/lineage and MAC generation/verification; no material fingerprint read
GRANT SELECT (incarnation_id) ON TABLE public.offline_preflight_key TO flooow_offline_readiness_owner;
-- SPEC:1814 Q READ_PRIVILEGE; consumer=READINESS.HMAC; entrypoint=internal Q; transitive=Control-only; frozen effects unchanged.
-- Required: Unique current ACTIVE key/lineage and MAC generation/verification; no material fingerprint read
GRANT SELECT (lineage_id) ON TABLE public.offline_preflight_key TO flooow_offline_readiness_owner;
-- SPEC:1815 Q READ_PRIVILEGE; consumer=READINESS.HMAC; entrypoint=internal Q; transitive=Control-only; frozen effects unchanged.
-- Required: Unique current ACTIVE key/lineage and MAC generation/verification; no material fingerprint read
GRANT SELECT (key_version) ON TABLE public.offline_preflight_key TO flooow_offline_readiness_owner;
-- SPEC:1816 Q READ_PRIVILEGE; consumer=READINESS.HMAC; entrypoint=internal Q; transitive=Control-only; frozen effects unchanged.
-- Required: Unique current ACTIVE key/lineage and MAC generation/verification; no material fingerprint read
GRANT SELECT (key_state) ON TABLE public.offline_preflight_key TO flooow_offline_readiness_owner;
-- SPEC:1817 Q READ_PRIVILEGE; consumer=READINESS.HMAC; entrypoint=internal Q; transitive=Control-only; frozen effects unchanged.
-- Required: Unique current ACTIVE key/lineage and MAC generation/verification; no material fingerprint read
GRANT SELECT (key_material) ON TABLE public.offline_preflight_key TO flooow_offline_readiness_owner;
-- SPEC:1818 V LOCK_ENABLING_UPDATE_PRIVILEGE; consumer=C/GUARD-V; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Smallest one-column UPDATE to acquire required row lock; no UPDATE statement changes token
GRANT UPDATE (lock_token) ON TABLE public.offline_binding_lifecycle TO flooow_offline_verification_owner;
-- SPEC:1819 V LOCK_ENABLING_UPDATE_PRIVILEGE; consumer=C/GUARD-V; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Smallest one-column UPDATE to acquire required row lock; no UPDATE statement changes token
GRANT UPDATE (lock_token) ON TABLE public.offline_attempt_pointer TO flooow_offline_verification_owner;
-- SPEC:1820 V LOCK_ENABLING_UPDATE_PRIVILEGE; consumer=C/GUARD-V; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Smallest one-column UPDATE to acquire required row lock; no UPDATE statement changes token
GRANT UPDATE (lock_token) ON TABLE public.offline_attempt TO flooow_offline_verification_owner;
-- SPEC:1821 V LOCK_ENABLING_UPDATE_PRIVILEGE; consumer=C/GUARD-V; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Smallest one-column UPDATE to acquire required row lock; no UPDATE statement changes token
GRANT UPDATE (lock_token) ON TABLE public.offline_execution TO flooow_offline_verification_owner;
-- SPEC:1822 I LOCK_ENABLING_UPDATE_PRIVILEGE; consumer=C/GUARD-I; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Smallest one-column UPDATE to acquire required row lock; no UPDATE statement changes token
GRANT UPDATE (lock_token) ON TABLE public.offline_binding_lifecycle TO flooow_offline_issuance_owner;
-- SPEC:1823 I LOCK_ENABLING_UPDATE_PRIVILEGE; consumer=C/GUARD-I; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Smallest one-column UPDATE to acquire required row lock; no UPDATE statement changes token
GRANT UPDATE (lock_token) ON TABLE public.offline_attempt_pointer TO flooow_offline_issuance_owner;
-- SPEC:1824 I LOCK_ENABLING_UPDATE_PRIVILEGE; consumer=C/GUARD-I; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Smallest one-column UPDATE to acquire required row lock; no UPDATE statement changes token
GRANT UPDATE (lock_token) ON TABLE public.offline_attempt TO flooow_offline_issuance_owner;
-- SPEC:1825 I LOCK_ENABLING_UPDATE_PRIVILEGE; consumer=C/GUARD-I; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Smallest one-column UPDATE to acquire required row lock; no UPDATE statement changes token
GRANT UPDATE (lock_token) ON TABLE public.offline_execution TO flooow_offline_issuance_owner;
-- SPEC:1826 E LOCK_ENABLING_UPDATE_PRIVILEGE; consumer=C/GUARD-E; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Smallest one-column UPDATE to acquire required row lock; no UPDATE statement changes token
GRANT UPDATE (lock_token) ON TABLE public.offline_binding_lifecycle TO flooow_offline_execution_owner;
-- SPEC:1827 E LOCK_ENABLING_UPDATE_PRIVILEGE; consumer=C/GUARD-E; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Smallest one-column UPDATE to acquire required row lock; no UPDATE statement changes token
GRANT UPDATE (lock_token) ON TABLE public.offline_attempt_pointer TO flooow_offline_execution_owner;
-- SPEC:1828 E LOCK_ENABLING_UPDATE_PRIVILEGE; consumer=C/GUARD-E; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Smallest one-column UPDATE to acquire required row lock; no UPDATE statement changes token
GRANT UPDATE (lock_token) ON TABLE public.offline_attempt TO flooow_offline_execution_owner;
-- SPEC:1829 E LOCK_ENABLING_UPDATE_PRIVILEGE; consumer=C/GUARD-E; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Smallest one-column UPDATE to acquire required row lock; no UPDATE statement changes token
GRANT UPDATE (lock_token) ON TABLE public.offline_execution TO flooow_offline_execution_owner;
-- SPEC:1830 P LOCK_ENABLING_UPDATE_PRIVILEGE; consumer=C/GUARD-P; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: Smallest one-column UPDATE to acquire required row lock; no UPDATE statement changes token
GRANT UPDATE (lock_token) ON TABLE public.offline_binding_lifecycle TO flooow_offline_principal_lock_owner;
-- SPEC:1831 P LOCK_ENABLING_UPDATE_PRIVILEGE; consumer=C/GUARD-P; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: Smallest one-column UPDATE to acquire required row lock; no UPDATE statement changes token
GRANT UPDATE (lock_token) ON TABLE public.offline_attempt_pointer TO flooow_offline_principal_lock_owner;
-- SPEC:1832 P LOCK_ENABLING_UPDATE_PRIVILEGE; consumer=C/GUARD-P; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: Smallest one-column UPDATE to acquire required row lock; no UPDATE statement changes token
GRANT UPDATE (lock_token) ON TABLE public.offline_attempt TO flooow_offline_principal_lock_owner;
-- SPEC:1833 P LOCK_ENABLING_UPDATE_PRIVILEGE; consumer=C/GUARD-P; entrypoint=internal P; transitive=Control-only; frozen effects unchanged.
-- Required: Smallest one-column UPDATE to acquire required row lock; no UPDATE statement changes token
GRANT UPDATE (lock_token) ON TABLE public.offline_execution TO flooow_offline_principal_lock_owner;
-- SPEC:1834 I LOCK_ENABLING_UPDATE_PRIVILEGE; consumer=C/DELIVERY; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Relevant delivery row lock only
GRANT UPDATE (lock_token) ON TABLE public.offline_delivery TO flooow_offline_issuance_owner;
-- SPEC:1835 E LOCK_ENABLING_UPDATE_PRIVILEGE; consumer=C/DELIVERY; entrypoint=S13-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Relevant delivery row lock only
GRANT UPDATE (lock_token) ON TABLE public.offline_delivery TO flooow_offline_execution_owner;
-- SPEC:1836 E LOCK_ENABLING_UPDATE_PRIVILEGE; consumer=C/AUTH/COMPLETE; entrypoint=S16-S18; transitive=Control-only; frozen effects unchanged.
-- Required: Relevant admission row lock only
GRANT UPDATE (lock_token) ON TABLE public.offline_admission TO flooow_offline_execution_owner;
-- SPEC:1837 V BOOKKEEPING_UPDATE; consumer=VERIFY-STAGE; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Only CLAIMED->EFFECTS_IN_PROGRESS after exact frozen successful receipt
GRANT UPDATE (state) ON TABLE public.offline_attempt TO flooow_offline_verification_owner;
-- SPEC:1838 V BOOKKEEPING_INSERT; consumer=VERIFY-STAGE; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Only owned verification or principal/initial-credential/grant successful stage fields
GRANT INSERT (binding_id) ON TABLE public.offline_stage_receipt TO flooow_offline_verification_owner;
-- SPEC:1839 V BOOKKEEPING_INSERT; consumer=VERIFY-STAGE; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Only owned verification or principal/initial-credential/grant successful stage fields
GRANT INSERT (attempt_id) ON TABLE public.offline_stage_receipt TO flooow_offline_verification_owner;
-- SPEC:1840 V BOOKKEEPING_INSERT; consumer=VERIFY-STAGE; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Only owned verification or principal/initial-credential/grant successful stage fields
GRANT INSERT (generation) ON TABLE public.offline_stage_receipt TO flooow_offline_verification_owner;
-- SPEC:1841 V BOOKKEEPING_INSERT; consumer=VERIFY-STAGE; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Only owned verification or principal/initial-credential/grant successful stage fields
GRANT INSERT (execution_id) ON TABLE public.offline_stage_receipt TO flooow_offline_verification_owner;
-- SPEC:1842 V BOOKKEEPING_INSERT; consumer=VERIFY-STAGE; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Only owned verification or principal/initial-credential/grant successful stage fields
GRANT INSERT (instance_id) ON TABLE public.offline_stage_receipt TO flooow_offline_verification_owner;
-- SPEC:1843 V BOOKKEEPING_INSERT; consumer=VERIFY-STAGE; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Only owned verification or principal/initial-credential/grant successful stage fields
GRANT INSERT (stage) ON TABLE public.offline_stage_receipt TO flooow_offline_verification_owner;
-- SPEC:1844 V BOOKKEEPING_INSERT; consumer=VERIFY-STAGE; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Only owned verification or principal/initial-credential/grant successful stage fields
GRANT INSERT (receipt_id) ON TABLE public.offline_stage_receipt TO flooow_offline_verification_owner;
-- SPEC:1845 V BOOKKEEPING_INSERT; consumer=VERIFY-STAGE; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Only owned verification or principal/initial-credential/grant successful stage fields
GRANT INSERT (operation_id) ON TABLE public.offline_stage_receipt TO flooow_offline_verification_owner;
-- SPEC:1846 V BOOKKEEPING_INSERT; consumer=VERIFY-STAGE; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Only owned verification or principal/initial-credential/grant successful stage fields
GRANT INSERT (frozen_receipt) ON TABLE public.offline_stage_receipt TO flooow_offline_verification_owner;
-- SPEC:1847 V BOOKKEEPING_INSERT; consumer=VERIFY-STAGE; entrypoint=S05-S06; transitive=Control-only; frozen effects unchanged.
-- Required: Only owned verification or principal/initial-credential/grant successful stage fields
GRANT INSERT (effect_time) ON TABLE public.offline_stage_receipt TO flooow_offline_verification_owner;
-- SPEC:1848 I BOOKKEEPING_UPDATE; consumer=ISSUE-STAGE; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Only CLAIMED->EFFECTS_IN_PROGRESS after exact frozen successful receipt
GRANT UPDATE (state) ON TABLE public.offline_attempt TO flooow_offline_issuance_owner;
-- SPEC:1849 I BOOKKEEPING_INSERT; consumer=ISSUE-STAGE; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Only owned verification or principal/initial-credential/grant successful stage fields
GRANT INSERT (binding_id) ON TABLE public.offline_stage_receipt TO flooow_offline_issuance_owner;
-- SPEC:1850 I BOOKKEEPING_INSERT; consumer=ISSUE-STAGE; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Only owned verification or principal/initial-credential/grant successful stage fields
GRANT INSERT (attempt_id) ON TABLE public.offline_stage_receipt TO flooow_offline_issuance_owner;
-- SPEC:1851 I BOOKKEEPING_INSERT; consumer=ISSUE-STAGE; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Only owned verification or principal/initial-credential/grant successful stage fields
GRANT INSERT (generation) ON TABLE public.offline_stage_receipt TO flooow_offline_issuance_owner;
-- SPEC:1852 I BOOKKEEPING_INSERT; consumer=ISSUE-STAGE; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Only owned verification or principal/initial-credential/grant successful stage fields
GRANT INSERT (execution_id) ON TABLE public.offline_stage_receipt TO flooow_offline_issuance_owner;
-- SPEC:1853 I BOOKKEEPING_INSERT; consumer=ISSUE-STAGE; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Only owned verification or principal/initial-credential/grant successful stage fields
GRANT INSERT (instance_id) ON TABLE public.offline_stage_receipt TO flooow_offline_issuance_owner;
-- SPEC:1854 I BOOKKEEPING_INSERT; consumer=ISSUE-STAGE; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Only owned verification or principal/initial-credential/grant successful stage fields
GRANT INSERT (stage) ON TABLE public.offline_stage_receipt TO flooow_offline_issuance_owner;
-- SPEC:1855 I BOOKKEEPING_INSERT; consumer=ISSUE-STAGE; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Only owned verification or principal/initial-credential/grant successful stage fields
GRANT INSERT (receipt_id) ON TABLE public.offline_stage_receipt TO flooow_offline_issuance_owner;
-- SPEC:1856 I BOOKKEEPING_INSERT; consumer=ISSUE-STAGE; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Only owned verification or principal/initial-credential/grant successful stage fields
GRANT INSERT (operation_id) ON TABLE public.offline_stage_receipt TO flooow_offline_issuance_owner;
-- SPEC:1857 I BOOKKEEPING_INSERT; consumer=ISSUE-STAGE; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Only owned verification or principal/initial-credential/grant successful stage fields
GRANT INSERT (frozen_receipt) ON TABLE public.offline_stage_receipt TO flooow_offline_issuance_owner;
-- SPEC:1858 I BOOKKEEPING_INSERT; consumer=ISSUE-STAGE; entrypoint=S07-S12; transitive=Control-only; frozen effects unchanged.
-- Required: Only owned verification or principal/initial-credential/grant successful stage fields
GRANT INSERT (effect_time) ON TABLE public.offline_stage_receipt TO flooow_offline_issuance_owner;
-- SPEC:1859 I BOOKKEEPING_UPDATE; consumer=ISSUE-STAGE; entrypoint=S10; transitive=Control-only; frozen effects unchanged.
-- Required: Only NOT_CREATED->CREATED_NOT_DELIVERABLE fresh Applied origin, unchanged generation
GRANT UPDATE (attempt_id) ON TABLE public.offline_delivery TO flooow_offline_issuance_owner;
-- SPEC:1860 I BOOKKEEPING_UPDATE; consumer=ISSUE-STAGE; entrypoint=S10; transitive=Control-only; frozen effects unchanged.
-- Required: Only NOT_CREATED->CREATED_NOT_DELIVERABLE fresh Applied origin, unchanged generation
GRANT UPDATE (credential_id) ON TABLE public.offline_delivery TO flooow_offline_issuance_owner;
-- SPEC:1861 I BOOKKEEPING_UPDATE; consumer=ISSUE-STAGE; entrypoint=S10; transitive=Control-only; frozen effects unchanged.
-- Required: Only NOT_CREATED->CREATED_NOT_DELIVERABLE fresh Applied origin, unchanged generation
GRANT UPDATE (initial_operation_id) ON TABLE public.offline_delivery TO flooow_offline_issuance_owner;
-- SPEC:1862 I BOOKKEEPING_UPDATE; consumer=ISSUE-STAGE; entrypoint=S10; transitive=Control-only; frozen effects unchanged.
-- Required: Only NOT_CREATED->CREATED_NOT_DELIVERABLE fresh Applied origin, unchanged generation
GRANT UPDATE (fresh_applied_receipt_id) ON TABLE public.offline_delivery TO flooow_offline_issuance_owner;
-- SPEC:1863 I BOOKKEEPING_UPDATE; consumer=ISSUE-STAGE; entrypoint=S10; transitive=Control-only; frozen effects unchanged.
-- Required: Only NOT_CREATED->CREATED_NOT_DELIVERABLE fresh Applied origin, unchanged generation
GRANT UPDATE (execution_id) ON TABLE public.offline_delivery TO flooow_offline_issuance_owner;
-- SPEC:1864 I BOOKKEEPING_UPDATE; consumer=ISSUE-STAGE; entrypoint=S10; transitive=Control-only; frozen effects unchanged.
-- Required: Only NOT_CREATED->CREATED_NOT_DELIVERABLE fresh Applied origin, unchanged generation
GRANT UPDATE (instance_id) ON TABLE public.offline_delivery TO flooow_offline_issuance_owner;
-- SPEC:1865 I BOOKKEEPING_UPDATE; consumer=ISSUE-STAGE; entrypoint=S10; transitive=Control-only; frozen effects unchanged.
-- Required: Only NOT_CREATED->CREATED_NOT_DELIVERABLE fresh Applied origin, unchanged generation
GRANT UPDATE (state) ON TABLE public.offline_delivery TO flooow_offline_issuance_owner;
-- SPEC:1866 E BOOKKEEPING_INSERT; consumer=CLAIM; entrypoint=S13; transitive=Control-only; frozen effects unchanged.
-- Required: Only original administratively permitted claim; token initialized0
GRANT INSERT (binding_id) ON TABLE public.offline_attempt TO flooow_offline_execution_owner;
-- SPEC:1867 E BOOKKEEPING_INSERT; consumer=CLAIM; entrypoint=S13; transitive=Control-only; frozen effects unchanged.
-- Required: Only original administratively permitted claim; token initialized0
GRANT INSERT (attempt_id) ON TABLE public.offline_attempt TO flooow_offline_execution_owner;
-- SPEC:1868 E BOOKKEEPING_INSERT; consumer=CLAIM; entrypoint=S13; transitive=Control-only; frozen effects unchanged.
-- Required: Only original administratively permitted claim; token initialized0
GRANT INSERT (generation) ON TABLE public.offline_attempt TO flooow_offline_execution_owner;
-- SPEC:1869 E BOOKKEEPING_INSERT; consumer=CLAIM; entrypoint=S13; transitive=Control-only; frozen effects unchanged.
-- Required: Only original administratively permitted claim; token initialized0
GRANT INSERT (state) ON TABLE public.offline_attempt TO flooow_offline_execution_owner;
-- SPEC:1870 E BOOKKEEPING_INSERT; consumer=CLAIM; entrypoint=S13; transitive=Control-only; frozen effects unchanged.
-- Required: Only original administratively permitted claim; token initialized0
GRANT INSERT (claimed_at) ON TABLE public.offline_attempt TO flooow_offline_execution_owner;
-- SPEC:1871 E BOOKKEEPING_INSERT; consumer=CLAIM; entrypoint=S13; transitive=Control-only; frozen effects unchanged.
-- Required: Only original administratively permitted claim; token initialized0
GRANT INSERT (expires_at) ON TABLE public.offline_attempt TO flooow_offline_execution_owner;
-- SPEC:1872 E BOOKKEEPING_INSERT; consumer=CLAIM; entrypoint=S13; transitive=Control-only; frozen effects unchanged.
-- Required: Only original administratively permitted claim; token initialized0
GRANT INSERT (lock_token) ON TABLE public.offline_attempt TO flooow_offline_execution_owner;
-- SPEC:1873 E BOOKKEEPING_INSERT; consumer=CLAIM; entrypoint=S13; transitive=Control-only; frozen effects unchanged.
-- Required: Only original OWNED execution/digest/absolute deadlines; token initialized0
GRANT INSERT (binding_id) ON TABLE public.offline_execution TO flooow_offline_execution_owner;
-- SPEC:1874 E BOOKKEEPING_INSERT; consumer=CLAIM; entrypoint=S13; transitive=Control-only; frozen effects unchanged.
-- Required: Only original OWNED execution/digest/absolute deadlines; token initialized0
GRANT INSERT (attempt_id) ON TABLE public.offline_execution TO flooow_offline_execution_owner;
-- SPEC:1875 E BOOKKEEPING_INSERT; consumer=CLAIM; entrypoint=S13; transitive=Control-only; frozen effects unchanged.
-- Required: Only original OWNED execution/digest/absolute deadlines; token initialized0
GRANT INSERT (generation) ON TABLE public.offline_execution TO flooow_offline_execution_owner;
-- SPEC:1876 E BOOKKEEPING_INSERT; consumer=CLAIM; entrypoint=S13; transitive=Control-only; frozen effects unchanged.
-- Required: Only original OWNED execution/digest/absolute deadlines; token initialized0
GRANT INSERT (execution_id) ON TABLE public.offline_execution TO flooow_offline_execution_owner;
-- SPEC:1877 E BOOKKEEPING_INSERT; consumer=CLAIM; entrypoint=S13; transitive=Control-only; frozen effects unchanged.
-- Required: Only original OWNED execution/digest/absolute deadlines; token initialized0
GRANT INSERT (instance_id) ON TABLE public.offline_execution TO flooow_offline_execution_owner;
-- SPEC:1878 E BOOKKEEPING_INSERT; consumer=CLAIM; entrypoint=S13; transitive=Control-only; frozen effects unchanged.
-- Required: Only original OWNED execution/digest/absolute deadlines; token initialized0
GRANT INSERT (executor_oid) ON TABLE public.offline_execution TO flooow_offline_execution_owner;
-- SPEC:1879 E BOOKKEEPING_INSERT; consumer=CLAIM; entrypoint=S13; transitive=Control-only; frozen effects unchanged.
-- Required: Only original OWNED execution/digest/absolute deadlines; token initialized0
GRANT INSERT (state) ON TABLE public.offline_execution TO flooow_offline_execution_owner;
-- SPEC:1880 E BOOKKEEPING_INSERT; consumer=CLAIM; entrypoint=S13; transitive=Control-only; frozen effects unchanged.
-- Required: Only original OWNED execution/digest/absolute deadlines; token initialized0
GRANT INSERT (claimed_at) ON TABLE public.offline_execution TO flooow_offline_execution_owner;
-- SPEC:1881 E BOOKKEEPING_INSERT; consumer=CLAIM; entrypoint=S13; transitive=Control-only; frozen effects unchanged.
-- Required: Only original OWNED execution/digest/absolute deadlines; token initialized0
GRANT INSERT (expires_at) ON TABLE public.offline_execution TO flooow_offline_execution_owner;
-- SPEC:1882 E BOOKKEEPING_INSERT; consumer=CLAIM; entrypoint=S13; transitive=Control-only; frozen effects unchanged.
-- Required: Only original OWNED execution/digest/absolute deadlines; token initialized0
GRANT INSERT (possession_digest) ON TABLE public.offline_execution TO flooow_offline_execution_owner;
-- SPEC:1883 E BOOKKEEPING_INSERT; consumer=CLAIM; entrypoint=S13; transitive=Control-only; frozen effects unchanged.
-- Required: Only original OWNED execution/digest/absolute deadlines; token initialized0
GRANT INSERT (claim_receipt_id) ON TABLE public.offline_execution TO flooow_offline_execution_owner;
-- SPEC:1884 E BOOKKEEPING_INSERT; consumer=CLAIM; entrypoint=S13; transitive=Control-only; frozen effects unchanged.
-- Required: Only original OWNED execution/digest/absolute deadlines; token initialized0
GRANT INSERT (lock_token) ON TABLE public.offline_execution TO flooow_offline_execution_owner;
-- SPEC:1885 E BOOKKEEPING_UPDATE; consumer=CLAIM; entrypoint=S13; transitive=Control-only; frozen effects unchanged.
-- Required: Only original claim; cannot advance generation or claim permission
GRANT UPDATE (current_attempt_id) ON TABLE public.offline_attempt_pointer TO flooow_offline_execution_owner;
-- SPEC:1886 E BOOKKEEPING_INSERT; consumer=AUTH; entrypoint=S16; transitive=Control-only; frozen effects unchanged.
-- Required: Only current authenticated ISSUED tuple; consumed fields NULL; token initialized0
GRANT INSERT (admission_id) ON TABLE public.offline_admission TO flooow_offline_execution_owner;
-- SPEC:1887 E BOOKKEEPING_INSERT; consumer=AUTH; entrypoint=S16; transitive=Control-only; frozen effects unchanged.
-- Required: Only current authenticated ISSUED tuple; consumed fields NULL; token initialized0
GRANT INSERT (deployment_id) ON TABLE public.offline_admission TO flooow_offline_execution_owner;
-- SPEC:1888 E BOOKKEEPING_INSERT; consumer=AUTH; entrypoint=S16; transitive=Control-only; frozen effects unchanged.
-- Required: Only current authenticated ISSUED tuple; consumed fields NULL; token initialized0
GRANT INSERT (incarnation_id) ON TABLE public.offline_admission TO flooow_offline_execution_owner;
-- SPEC:1889 E BOOKKEEPING_INSERT; consumer=AUTH; entrypoint=S16; transitive=Control-only; frozen effects unchanged.
-- Required: Only current authenticated ISSUED tuple; consumed fields NULL; token initialized0
GRANT INSERT (binding_id) ON TABLE public.offline_admission TO flooow_offline_execution_owner;
-- SPEC:1890 E BOOKKEEPING_INSERT; consumer=AUTH; entrypoint=S16; transitive=Control-only; frozen effects unchanged.
-- Required: Only current authenticated ISSUED tuple; consumed fields NULL; token initialized0
GRANT INSERT (attempt_id) ON TABLE public.offline_admission TO flooow_offline_execution_owner;
-- SPEC:1891 E BOOKKEEPING_INSERT; consumer=AUTH; entrypoint=S16; transitive=Control-only; frozen effects unchanged.
-- Required: Only current authenticated ISSUED tuple; consumed fields NULL; token initialized0
GRANT INSERT (generation) ON TABLE public.offline_admission TO flooow_offline_execution_owner;
-- SPEC:1892 E BOOKKEEPING_INSERT; consumer=AUTH; entrypoint=S16; transitive=Control-only; frozen effects unchanged.
-- Required: Only current authenticated ISSUED tuple; consumed fields NULL; token initialized0
GRANT INSERT (execution_id) ON TABLE public.offline_admission TO flooow_offline_execution_owner;
-- SPEC:1893 E BOOKKEEPING_INSERT; consumer=AUTH; entrypoint=S16; transitive=Control-only; frozen effects unchanged.
-- Required: Only current authenticated ISSUED tuple; consumed fields NULL; token initialized0
GRANT INSERT (instance_id) ON TABLE public.offline_admission TO flooow_offline_execution_owner;
-- SPEC:1894 E BOOKKEEPING_INSERT; consumer=AUTH; entrypoint=S16; transitive=Control-only; frozen effects unchanged.
-- Required: Only current authenticated ISSUED tuple; consumed fields NULL; token initialized0
GRANT INSERT (executor_oid) ON TABLE public.offline_admission TO flooow_offline_execution_owner;
-- SPEC:1895 E BOOKKEEPING_INSERT; consumer=AUTH; entrypoint=S16; transitive=Control-only; frozen effects unchanged.
-- Required: Only current authenticated ISSUED tuple; consumed fields NULL; token initialized0
GRANT INSERT (credential_id) ON TABLE public.offline_admission TO flooow_offline_execution_owner;
-- SPEC:1896 E BOOKKEEPING_INSERT; consumer=AUTH; entrypoint=S16; transitive=Control-only; frozen effects unchanged.
-- Required: Only current authenticated ISSUED tuple; consumed fields NULL; token initialized0
GRANT INSERT (credential_revision) ON TABLE public.offline_admission TO flooow_offline_execution_owner;
-- SPEC:1897 E BOOKKEEPING_INSERT; consumer=AUTH; entrypoint=S16; transitive=Control-only; frozen effects unchanged.
-- Required: Only current authenticated ISSUED tuple; consumed fields NULL; token initialized0
GRANT INSERT (principal_id) ON TABLE public.offline_admission TO flooow_offline_execution_owner;
-- SPEC:1898 E BOOKKEEPING_INSERT; consumer=AUTH; entrypoint=S16; transitive=Control-only; frozen effects unchanged.
-- Required: Only current authenticated ISSUED tuple; consumed fields NULL; token initialized0
GRANT INSERT (organization_id) ON TABLE public.offline_admission TO flooow_offline_execution_owner;
-- SPEC:1899 E BOOKKEEPING_INSERT; consumer=AUTH; entrypoint=S16; transitive=Control-only; frozen effects unchanged.
-- Required: Only current authenticated ISSUED tuple; consumed fields NULL; token initialized0
GRANT INSERT (grant_id) ON TABLE public.offline_admission TO flooow_offline_execution_owner;
-- SPEC:1900 E BOOKKEEPING_INSERT; consumer=AUTH; entrypoint=S16; transitive=Control-only; frozen effects unchanged.
-- Required: Only current authenticated ISSUED tuple; consumed fields NULL; token initialized0
GRANT INSERT (grant_revision) ON TABLE public.offline_admission TO flooow_offline_execution_owner;
-- SPEC:1901 E BOOKKEEPING_INSERT; consumer=AUTH; entrypoint=S16; transitive=Control-only; frozen effects unchanged.
-- Required: Only current authenticated ISSUED tuple; consumed fields NULL; token initialized0
GRANT INSERT (authorization_fingerprint) ON TABLE public.offline_admission TO flooow_offline_execution_owner;
-- SPEC:1902 E BOOKKEEPING_INSERT; consumer=AUTH; entrypoint=S16; transitive=Control-only; frozen effects unchanged.
-- Required: Only current authenticated ISSUED tuple; consumed fields NULL; token initialized0
GRANT INSERT (permission) ON TABLE public.offline_admission TO flooow_offline_execution_owner;
-- SPEC:1903 E BOOKKEEPING_INSERT; consumer=AUTH; entrypoint=S16; transitive=Control-only; frozen effects unchanged.
-- Required: Only current authenticated ISSUED tuple; consumed fields NULL; token initialized0
GRANT INSERT (authenticated_at) ON TABLE public.offline_admission TO flooow_offline_execution_owner;
-- SPEC:1904 E BOOKKEEPING_INSERT; consumer=AUTH; entrypoint=S16; transitive=Control-only; frozen effects unchanged.
-- Required: Only current authenticated ISSUED tuple; consumed fields NULL; token initialized0
GRANT INSERT (expires_at) ON TABLE public.offline_admission TO flooow_offline_execution_owner;
-- SPEC:1905 E BOOKKEEPING_INSERT; consumer=AUTH; entrypoint=S16; transitive=Control-only; frozen effects unchanged.
-- Required: Only current authenticated ISSUED tuple; consumed fields NULL; token initialized0
GRANT INSERT (durable_state) ON TABLE public.offline_admission TO flooow_offline_execution_owner;
-- SPEC:1906 E BOOKKEEPING_INSERT; consumer=AUTH; entrypoint=S16; transitive=Control-only; frozen effects unchanged.
-- Required: Only current authenticated ISSUED tuple; consumed fields NULL; token initialized0
GRANT INSERT (consumed_decision_id) ON TABLE public.offline_admission TO flooow_offline_execution_owner;
-- SPEC:1907 E BOOKKEEPING_INSERT; consumer=AUTH; entrypoint=S16; transitive=Control-only; frozen effects unchanged.
-- Required: Only current authenticated ISSUED tuple; consumed fields NULL; token initialized0
GRANT INSERT (consumed_at) ON TABLE public.offline_admission TO flooow_offline_execution_owner;
-- SPEC:1908 E BOOKKEEPING_INSERT; consumer=AUTH; entrypoint=S16; transitive=Control-only; frozen effects unchanged.
-- Required: Only current authenticated ISSUED tuple; consumed fields NULL; token initialized0
GRANT INSERT (lock_token) ON TABLE public.offline_admission TO flooow_offline_execution_owner;
-- SPEC:1909 E BOOKKEEPING_UPDATE; consumer=COMPLETE; entrypoint=S18; transitive=Control-only; frozen effects unchanged.
-- Required: Only successful atomic ISSUED->CONSUMED with decision
GRANT UPDATE (durable_state) ON TABLE public.offline_admission TO flooow_offline_execution_owner;
-- SPEC:1910 E BOOKKEEPING_UPDATE; consumer=COMPLETE; entrypoint=S18; transitive=Control-only; frozen effects unchanged.
-- Required: Only successful atomic ISSUED->CONSUMED with decision
GRANT UPDATE (consumed_decision_id) ON TABLE public.offline_admission TO flooow_offline_execution_owner;
-- SPEC:1911 E BOOKKEEPING_UPDATE; consumer=COMPLETE; entrypoint=S18; transitive=Control-only; frozen effects unchanged.
-- Required: Only successful atomic ISSUED->CONSUMED with decision
GRANT UPDATE (consumed_at) ON TABLE public.offline_admission TO flooow_offline_execution_owner;
-- SPEC:1912 E BOOKKEEPING_UPDATE; consumer=DELIVERY.consume; DELIVERY.report; entrypoint=S14; S15; transitive=Control-only; frozen effects unchanged.
-- Required: One atomic ATTEMPTED permission consumption; One live admissible report; no renewal/redelivery
GRANT UPDATE (state) ON TABLE public.offline_delivery TO flooow_offline_execution_owner;
-- SPEC:1913 E BOOKKEEPING_UPDATE; consumer=DELIVERY.consume; entrypoint=S14; transitive=Control-only; frozen effects unchanged.
-- Required: One atomic ATTEMPTED permission consumption
GRANT UPDATE (delivery_receipt_id) ON TABLE public.offline_delivery TO flooow_offline_execution_owner;
-- SPEC:1914 E BOOKKEEPING_UPDATE; consumer=DELIVERY.consume; entrypoint=S14; transitive=Control-only; frozen effects unchanged.
-- Required: One atomic ATTEMPTED permission consumption
GRANT UPDATE (attempted_at) ON TABLE public.offline_delivery TO flooow_offline_execution_owner;
-- SPEC:1915 E BOOKKEEPING_UPDATE; consumer=DELIVERY.consume; entrypoint=S14; transitive=Control-only; frozen effects unchanged.
-- Required: One atomic ATTEMPTED permission consumption
GRANT UPDATE (operation_deadline) ON TABLE public.offline_delivery TO flooow_offline_execution_owner;
-- SPEC:1916 E BOOKKEEPING_UPDATE; consumer=DELIVERY.report; entrypoint=S15; transitive=Control-only; frozen effects unchanged.
-- Required: One live admissible report; no renewal/redelivery
GRANT UPDATE (observed_at) ON TABLE public.offline_delivery TO flooow_offline_execution_owner;
-- SPEC:1917 E BOOKKEEPING_UPDATE; consumer=DELIVERY.report; entrypoint=S15; transitive=Control-only; frozen effects unchanged.
-- Required: One live admissible report; no renewal/redelivery
GRANT UPDATE (observation_code) ON TABLE public.offline_delivery TO flooow_offline_execution_owner;
-- SPEC:1918 E BOOKKEEPING_UPDATE; consumer=DELIVERY.report; entrypoint=S15; transitive=Control-only; frozen effects unchanged.
-- Required: One live admissible report; no renewal/redelivery
GRANT UPDATE (recorded_at) ON TABLE public.offline_delivery TO flooow_offline_execution_owner;
-- SPEC:1919 E BOOKKEEPING_INSERT; consumer=COMPLETE; entrypoint=S18; transitive=Control-only; frozen effects unchanged.
-- Required: DECISION successful frozen receipt only
GRANT INSERT (binding_id) ON TABLE public.offline_stage_receipt TO flooow_offline_execution_owner;
-- SPEC:1920 E BOOKKEEPING_INSERT; consumer=COMPLETE; entrypoint=S18; transitive=Control-only; frozen effects unchanged.
-- Required: DECISION successful frozen receipt only
GRANT INSERT (attempt_id) ON TABLE public.offline_stage_receipt TO flooow_offline_execution_owner;
-- SPEC:1921 E BOOKKEEPING_INSERT; consumer=COMPLETE; entrypoint=S18; transitive=Control-only; frozen effects unchanged.
-- Required: DECISION successful frozen receipt only
GRANT INSERT (generation) ON TABLE public.offline_stage_receipt TO flooow_offline_execution_owner;
-- SPEC:1922 E BOOKKEEPING_INSERT; consumer=COMPLETE; entrypoint=S18; transitive=Control-only; frozen effects unchanged.
-- Required: DECISION successful frozen receipt only
GRANT INSERT (execution_id) ON TABLE public.offline_stage_receipt TO flooow_offline_execution_owner;
-- SPEC:1923 E BOOKKEEPING_INSERT; consumer=COMPLETE; entrypoint=S18; transitive=Control-only; frozen effects unchanged.
-- Required: DECISION successful frozen receipt only
GRANT INSERT (instance_id) ON TABLE public.offline_stage_receipt TO flooow_offline_execution_owner;
-- SPEC:1924 E BOOKKEEPING_INSERT; consumer=COMPLETE; entrypoint=S18; transitive=Control-only; frozen effects unchanged.
-- Required: DECISION successful frozen receipt only
GRANT INSERT (stage) ON TABLE public.offline_stage_receipt TO flooow_offline_execution_owner;
-- SPEC:1925 E BOOKKEEPING_INSERT; consumer=COMPLETE; entrypoint=S18; transitive=Control-only; frozen effects unchanged.
-- Required: DECISION successful frozen receipt only
GRANT INSERT (receipt_id) ON TABLE public.offline_stage_receipt TO flooow_offline_execution_owner;
-- SPEC:1926 E BOOKKEEPING_INSERT; consumer=COMPLETE; entrypoint=S18; transitive=Control-only; frozen effects unchanged.
-- Required: DECISION successful frozen receipt only
GRANT INSERT (operation_id) ON TABLE public.offline_stage_receipt TO flooow_offline_execution_owner;
-- SPEC:1927 E BOOKKEEPING_INSERT; consumer=COMPLETE; entrypoint=S18; transitive=Control-only; frozen effects unchanged.
-- Required: DECISION successful frozen receipt only
GRANT INSERT (frozen_receipt) ON TABLE public.offline_stage_receipt TO flooow_offline_execution_owner;
-- SPEC:1928 E BOOKKEEPING_INSERT; consumer=COMPLETE; entrypoint=S18; transitive=Control-only; frozen effects unchanged.
-- Required: DECISION successful frozen receipt only
GRANT INSERT (effect_time) ON TABLE public.offline_stage_receipt TO flooow_offline_execution_owner;
-- SPEC:1929 E BOOKKEEPING_UPDATE; consumer=COMPLETE; entrypoint=S18; transitive=Control-only; frozen effects unchanged.
-- Required: Atomic EFFECTS_COMPLETE/RELEASED/REQUIRED with decision; no result write
GRANT UPDATE (state) ON TABLE public.offline_attempt TO flooow_offline_execution_owner;
-- SPEC:1930 E BOOKKEEPING_UPDATE; consumer=COMPLETE; entrypoint=S18; transitive=Control-only; frozen effects unchanged.
-- Required: Atomic EFFECTS_COMPLETE/RELEASED/REQUIRED with decision; no result write
GRANT UPDATE (state) ON TABLE public.offline_execution TO flooow_offline_execution_owner;
-- SPEC:1931 E BOOKKEEPING_UPDATE; consumer=COMPLETE; entrypoint=S18; transitive=Control-only; frozen effects unchanged.
-- Required: Atomic EFFECTS_COMPLETE/RELEASED/REQUIRED with decision; no result write
GRANT UPDATE (state) ON TABLE public.offline_reconciliation TO flooow_offline_execution_owner;

-- SPEC 25.3 / 22.4: exactly seven read-only activation dependencies.
GRANT SELECT (effective_from) ON TABLE public.offline_deadline_policy TO flooow_offline_verification_owner;
GRANT SELECT (effective_from) ON TABLE public.offline_deadline_policy TO flooow_offline_issuance_owner;
GRANT SELECT (effective_from) ON TABLE public.offline_deadline_policy TO flooow_offline_execution_owner;
GRANT SELECT (effective_from) ON TABLE public.offline_deadline_policy TO flooow_offline_audit_owner;
GRANT SELECT (effective_from) ON TABLE public.offline_deadline_policy TO flooow_offline_principal_lock_owner;
GRANT SELECT (effective_from) ON TABLE public.offline_deadline_policy TO flooow_offline_readiness_owner;
GRANT SELECT (effective_from) ON TABLE public.offline_deadline_policy TO flooow_offline_intent_audit_owner;

-- END incomplete G3F.3B candidate. No migration/activation authorization.
-- Never infer authority/READY/implementation proof from this source inventory.
