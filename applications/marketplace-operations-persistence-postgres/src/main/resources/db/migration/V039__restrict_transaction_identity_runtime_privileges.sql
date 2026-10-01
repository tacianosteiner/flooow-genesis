REVOKE EXECUTE ON FUNCTION transaction_identity_hash(text[]) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION transaction_identity_grant_fingerprint(uuid,uuid) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION transaction_identity_intent(marketplace_transaction_identity_decision) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION transaction_identity_fingerprint(marketplace_transaction_identity_decision) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION transaction_identity_locks(uuid,uuid,uuid,uuid,text,uuid) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION transaction_identity_validate() FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION transaction_identity_head_guard() FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION transaction_identity_advance() FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION transaction_identity_immutable() FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION transaction_identity_withdrawal_locks(uuid,uuid,uuid,uuid,text,uuid) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION transaction_identity_withdrawn_validate() FROM PUBLIC;

-- Narrow privileged row-lock boundary for the organization authorization fence.
-- It performs no semantic DML and returns only whether the exact organization
-- exists in ACTIVE state while holding the required FOR SHARE lock.
CREATE OR REPLACE FUNCTION command_authorization_organization_lock(org uuid)
RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path=pg_catalog,pg_temp
AS $$
DECLARE
    active boolean;
BEGIN
    SELECT status='ACTIVE'
      INTO active
      FROM public.integration_organization
     WHERE organization_id=org
     FOR SHARE;

    RETURN coalesce(active,false);
END;
$$;

REVOKE EXECUTE ON FUNCTION command_authorization_organization_lock(uuid) FROM PUBLIC;

-- Narrow privileged row-lock boundary for the one Omie V3 progress row
-- required by the CONFIRMED identity path. Capability is intentionally fixed:
-- callers cannot use this helper to lock arbitrary connector capabilities.
CREATE OR REPLACE FUNCTION transaction_identity_progress_lock(
    org uuid,
    conn uuid
)
RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path=pg_catalog,pg_temp
AS $$
DECLARE
    locked boolean;
BEGIN
    SELECT true
      INTO locked
      FROM public.integration_connector_progress
     WHERE organization_id=org
       AND connection_id=conn
       AND capability='marketplace-economic.omie-transaction-evidence.reacquisition-v3'
     FOR UPDATE;

    RETURN coalesce(locked,false);
END;
$$;

REVOKE EXECUTE ON FUNCTION transaction_identity_progress_lock(uuid,uuid) FROM PUBLIC;

-- Preserve the original V035 lock order while delegating only the two row locks
-- that require UPDATE privilege to narrow SECURITY DEFINER helpers.
-- The orchestration function itself remains SECURITY INVOKER.
CREATE OR REPLACE FUNCTION transaction_identity_locks(
    org uuid,
    actor uuid,
    id uuid,
    conn uuid,
    ref text,
    target uuid
)
RETURNS void
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path=pg_catalog,pg_temp
AS $$
DECLARE
    resource text;
BEGIN
    IF NOT public.command_authorization_organization_lock(org) THEN
        RAISE EXCEPTION 'Command authority unavailable'
            USING ERRCODE='P0012';
    END IF;

    PERFORM 1
      FROM public.command_principal
     WHERE organization_id=org
       AND principal_id=actor
     FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Command authority unavailable'
            USING ERRCODE='P0012';
    END IF;

    PERFORM pg_catalog.pg_advisory_xact_lock(
        pg_catalog.hashtextextended(
            'transaction-identity/id/1:' || org || ':' || id,
            0
        )
    );

    IF NOT public.transaction_identity_progress_lock(org,conn) THEN
        RAISE EXCEPTION 'Identity evidence unavailable'
            USING ERRCODE='P0002';
    END IF;

    FOR resource IN
        SELECT unnest(ARRAY[
            'transaction-identity/subject/1:' ||
                org || ':' ||
                conn || ':' ||
                pg_catalog.octet_length(ref) || ':' ||
                ref,
            'transaction-identity/target/1:' ||
                org || ':' ||
                target
        ])
        ORDER BY 1
    LOOP
        PERFORM pg_catalog.pg_advisory_xact_lock(
            pg_catalog.hashtextextended(resource,0)
        );
    END LOOP;
END;
$$;

REVOKE EXECUTE ON FUNCTION transaction_identity_locks(uuid,uuid,uuid,uuid,text,uuid) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION transaction_identity_hash(text[])
TO flooow_command_runtime;

GRANT EXECUTE ON FUNCTION transaction_identity_grant_fingerprint(uuid,uuid)
TO flooow_command_runtime;

GRANT EXECUTE ON FUNCTION transaction_identity_intent(marketplace_transaction_identity_decision)
TO flooow_command_runtime;

GRANT EXECUTE ON FUNCTION transaction_identity_fingerprint(marketplace_transaction_identity_decision)
TO flooow_command_runtime;

GRANT EXECUTE ON FUNCTION transaction_identity_locks(uuid,uuid,uuid,uuid,text,uuid)
TO flooow_command_runtime;

GRANT EXECUTE ON FUNCTION command_authorization_organization_lock(uuid)
TO flooow_command_runtime;

GRANT EXECUTE ON FUNCTION transaction_identity_progress_lock(uuid,uuid)
TO flooow_command_runtime;

GRANT SELECT,UPDATE ON command_principal
TO flooow_command_runtime;

GRANT SELECT ON command_credential_revision
TO flooow_command_runtime;

GRANT SELECT ON command_permission_grant
TO flooow_command_runtime;

REVOKE UPDATE ON integration_organization
FROM flooow_command_runtime;

GRANT SELECT ON integration_organization
TO flooow_command_runtime;

GRANT SELECT ON integration_connection
TO flooow_command_runtime;

GRANT SELECT,INSERT ON marketplace_transaction_identity_decision
TO flooow_command_runtime;

GRANT SELECT ON marketplace_transaction_identity_head
TO flooow_command_runtime;

GRANT SELECT ON marketplace_order_identity_registry
TO flooow_command_runtime;

GRANT SELECT ON marketplace_order_occurrence_source_promotion
TO flooow_command_runtime;

GRANT SELECT ON integration_mercado_livre_order_source_observation
TO flooow_command_runtime;

GRANT SELECT ON integration_omie_transaction_evidence
TO flooow_command_runtime;

GRANT SELECT ON integration_omie_transaction_evidence_v3
TO flooow_command_runtime;

GRANT SELECT ON integration_connector_page_commit
TO flooow_command_runtime;

REVOKE UPDATE ON integration_connector_progress
FROM flooow_command_runtime;

GRANT SELECT ON integration_connector_progress
TO flooow_command_runtime;