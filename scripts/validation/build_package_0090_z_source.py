"""Generate the bounded Z source from the already reviewed inline guard codec.

Offline source generation only. No database access; no new SQL helper surface.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V043__create_governed_offline_field_proof_capability_composition.sql'


def build(source):
    p = source.split('AS $offline_p$', 1)[1].split('$offline_p$;', 1)[0]
    declarations = p.split('BEGIN', 1)[0]
    for name in ('attempt_record', 'execution_record', 'pointer_record'):
        declarations = declarations.replace('    '+name+' record;\n', '')
    declarations = declarations.replace('    principal_found pg_catalog.uuid;\n', '')
    guard = p.split('    SELECT h.binding_id', 1)[1].split('    -- C:', 1)[0]
    guard = '    SELECT h.binding_id' + guard
    start = guard.index('    SELECT h.binding_id')
    end = guard.index('      INTO header_record')
    guard = guard[:start] + '''    SELECT h.binding_id,h.deployment_id,h.deployment_incarnation_id,h.identity_slots,
           h.offline_surface_version,h.deadline_policy_version,h.deadline_policy_digest,
           h.plan_fingerprint,h.organization_id,h.manifest_id,h.principal_id,
           h.credential_id,h.grant_id,h.principal_operation_id,h.credential_operation_id,
           h.grant_operation_id,h.mercado_livre_connection_id,h.omie_connection_id,
           h.reason,h.provenance,h.correlation_id
''' + guard[end:]
    guard = guard.replace('slot_number=3', 'slot_number=4')
    return '''-- Internal Z: private canonical intent/receipt comparisons; no secret projection.
CREATE FUNCTION public.offline_internal_verify_authority_intent(
    binding_id pg_catalog.uuid,plan_fingerprint pg_catalog.bytea,
    expected_incarnation_id pg_catalog.uuid,surface_version pg_catalog.text
) RETURNS TABLE(intent_matches pg_catalog.bool,receipt_matches pg_catalog.bool)
LANGUAGE plpgsql STABLE SECURITY DEFINER CALLED ON NULL INPUT
SET search_path=pg_catalog,pg_temp
AS $offline_z$
''' + declarations + '''BEGIN
    IF $1 IS NULL OR $2 IS NULL OR $3 IS NULL OR $4 IS NULL
       OR $1='00000000-0000-0000-0000-000000000000'::pg_catalog.uuid
       OR $3='00000000-0000-0000-0000-000000000000'::pg_catalog.uuid
       OR pg_catalog.octet_length($2)<>32 OR $4<>'0090-v1'
       OR pg_catalog.current_setting('transaction_isolation')<>'repeatable read'
       OR pg_catalog.current_setting('transaction_read_only')<>'on' THEN
        RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
    END IF;
''' + guard + '''    database_now := pg_catalog.clock_timestamp();
    IF NOT pg_catalog.isfinite(database_now) OR NOT pg_catalog.isfinite(policy_record.effective_from)
       OR database_now<policy_record.effective_from
       OR NOT pg_catalog.isfinite(ready_record.watchdog_checked_at)
       OR database_now<ready_record.watchdog_checked_at
       OR EXTRACT(EPOCH FROM(database_now-ready_record.watchdog_checked_at))*1000000>policy_values[23]
       OR EXTRACT(EPOCH FROM(database_now-pg_catalog.transaction_timestamp()))*1000000>policy_values[19] THEN
        RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
    END IF;
    -- Exact canonical operations, never caller-selected IDs or a persisted match flag.
    -- Missing joins produce false; query failure is an error, never inferred absence.
    RETURN QUERY
    SELECT pg_catalog.count(*) BETWEEN 1 AND 3 AND pg_catalog.bool_and(x.intent_ok) IS TRUE,
           pg_catalog.count(*) BETWEEN 1 AND 3 AND pg_catalog.bool_and(x.receipt_ok) IS TRUE
      FROM (
        SELECT o.intent_fingerprint=public.s2a_v042_authority_intent(
                   o.operation,o.operation_id,o.organization_id,o.principal_id,
                   p.mercado_livre_connection_id,p.omie_connection_id,o.credential_id,
                   c.secret_verifier,o.grant_id,p.reason,p.provenance,o.correlation_id,
                   o.attestation_manifest_id,a.accepted_proof_fingerprint,a.manifest_digest) AS intent_ok,
               o.receipt_fingerprint=public.s2a_v042_authority_receipt(
                   o.intent_fingerprint,o.operation,o.principal_id,o.credential_id,
                   o.credential_revision,o.grant_id,o.grant_revision,o.permission,o.state) AS receipt_ok
          FROM public.command_authority_operation o
          JOIN public.command_principal p ON p.organization_id=o.organization_id AND p.principal_id=o.principal_id
          JOIN public.s2a_accepted_attestation a ON a.organization_id=o.organization_id AND a.manifest_id=o.attestation_manifest_id
          LEFT JOIN public.command_permission_grant g ON g.organization_id=o.organization_id AND g.grant_id=o.grant_id
          LEFT JOIN public.command_credential_revision c ON c.organization_id=o.organization_id
               AND c.credential_id=o.credential_id AND c.revision=o.credential_revision
         WHERE o.organization_id=header_record.organization_id
           AND o.attestation_manifest_id=header_record.manifest_id
           AND o.principal_id=header_record.principal_id
           AND p.mercado_livre_connection_id=header_record.mercado_livre_connection_id
           AND p.omie_connection_id=header_record.omie_connection_id
           AND p.reason=header_record.reason AND p.provenance=header_record.provenance
           AND o.correlation_id=header_record.correlation_id
           AND ((o.operation='PRINCIPAL' AND o.operation_id=header_record.principal_operation_id
                 AND o.decided_at=p.decided_at)
             OR (o.operation='INITIAL_CREDENTIAL' AND o.operation_id=header_record.credential_operation_id
                 AND o.credential_id=header_record.credential_id AND c.principal_id=header_record.principal_id
                 AND o.decided_at=c.decided_at)
             OR (o.operation='GRANT' AND o.operation_id=header_record.grant_operation_id
                 AND o.grant_id=header_record.grant_id AND o.credential_id IS NULL
                 AND g.principal_id=header_record.principal_id
                 AND o.decided_at=g.decided_at))
      ) x;
EXCEPTION WHEN OTHERS THEN
    IF SQLSTATE='P0017' THEN
        RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
    END IF;
    RAISE EXCEPTION USING ERRCODE='P0018',MESSAGE='INDETERMINATE';
END;
$offline_z$;
ALTER FUNCTION public.offline_internal_verify_authority_intent(pg_catalog.uuid,pg_catalog.bytea,pg_catalog.uuid,pg_catalog.text) OWNER TO flooow_offline_intent_audit_owner;
REVOKE ALL ON FUNCTION public.offline_internal_verify_authority_intent(pg_catalog.uuid,pg_catalog.bytea,pg_catalog.uuid,pg_catalog.text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.offline_internal_verify_authority_intent(pg_catalog.uuid,pg_catalog.bytea,pg_catalog.uuid,pg_catalog.text) TO flooow_offline_audit_owner;
GRANT EXECUTE ON FUNCTION public.s2a_v042_authority_intent(pg_catalog.text,pg_catalog.uuid,pg_catalog.uuid,pg_catalog.uuid,pg_catalog.uuid,pg_catalog.uuid,pg_catalog.uuid,pg_catalog.bytea,pg_catalog.uuid,pg_catalog.text,pg_catalog.text,pg_catalog.uuid,pg_catalog.uuid,pg_catalog.text,pg_catalog.text) TO flooow_offline_intent_audit_owner;
GRANT EXECUTE ON FUNCTION public.s2a_v042_authority_receipt(pg_catalog.text,pg_catalog.text,pg_catalog.uuid,pg_catalog.uuid,pg_catalog.int4,pg_catalog.uuid,pg_catalog.int4,pg_catalog.text,pg_catalog.text) TO flooow_offline_intent_audit_owner;
GRANT EXECUTE ON FUNCTION public.s2a_v042_frame(pg_catalog.bytea) TO flooow_offline_intent_audit_owner;
GRANT EXECUTE ON FUNCTION public.s2a_v042_text(pg_catalog.text) TO flooow_offline_intent_audit_owner;
GRANT EXECUTE ON FUNCTION public.s2a_v042_instant(pg_catalog.timestamptz) TO flooow_offline_intent_audit_owner;
'''


if __name__ == '__main__':
    source = SOURCE.read_text(encoding='utf-8-sig')
    if 'AS $offline_z$' in source:
        raise SystemExit('Z already exists; no replacement authorized by generator')
    marker = '-- END incomplete G3F.3B candidate.'
    source = source.replace(marker, build(source)+'\n'+marker)
    SOURCE.write_text(source, encoding='utf-8')
