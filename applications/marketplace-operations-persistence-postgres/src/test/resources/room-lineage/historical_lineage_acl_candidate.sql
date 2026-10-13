-- TEST-ONLY ROOM IDENTITY/ACL CONTRACT. NOT FLYWAY; NO LOGIN PROVISIONING.
-- Fixture creates restricted roles separately. Execute as direct postgres.
DO $$ BEGIN
    IF session_user <> 'postgres' OR current_user <> 'postgres' THEN
        RAISE EXCEPTION 'Room deployment requires direct postgres migration identity';
    END IF;
END $$;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO flooow_room_history_runtime;

ALTER TABLE public.marketplace_sales_intelligence_revision OWNER TO flooow_room_history_owner;
ALTER TABLE public.marketplace_sales_intelligence_revision_observation OWNER TO flooow_room_history_owner;
ALTER TABLE public.marketplace_sales_intelligence_revision_correction OWNER TO flooow_room_history_owner;
ALTER TABLE public.marketplace_sales_intelligence_revision_reason OWNER TO flooow_room_history_owner;
ALTER TABLE public.marketplace_sales_intelligence_revision_coverage OWNER TO flooow_room_history_owner;
ALTER TABLE public.marketplace_sales_intelligence_revision_publication OWNER TO flooow_room_history_owner;
-- V018 table ownership controls its column/FK/triggers; a column has no separate owner.
ALTER TABLE public.marketplace_sales_intelligence_projection OWNER TO flooow_room_history_owner;

ALTER FUNCTION public.reject_marketplace_sales_history_mutation() OWNER TO flooow_room_history_owner;
ALTER FUNCTION public.reject_marketplace_sales_sealed_detail() OWNER TO flooow_room_history_owner;
ALTER FUNCTION public.validate_marketplace_sales_publication_insert() OWNER TO flooow_room_history_owner;
ALTER FUNCTION public.publish_marketplace_sales_revision() OWNER TO flooow_room_history_owner;
ALTER FUNCTION public.validate_marketplace_sales_revision_boundary(uuid,uuid,bigint) OWNER TO flooow_room_history_owner;
ALTER FUNCTION public.check_marketplace_sales_revision_boundary() OWNER TO flooow_room_history_owner;

ALTER FUNCTION public.reject_marketplace_sales_history_mutation() SET search_path=pg_catalog,public,pg_temp;
ALTER FUNCTION public.reject_marketplace_sales_sealed_detail() SET search_path=pg_catalog,public,pg_temp;
ALTER FUNCTION public.validate_marketplace_sales_publication_insert() SET search_path=pg_catalog,public,pg_temp;
ALTER FUNCTION public.publish_marketplace_sales_revision() SET search_path=pg_catalog,public,pg_temp;
ALTER FUNCTION public.validate_marketplace_sales_revision_boundary(uuid,uuid,bigint) SET search_path=pg_catalog,public,pg_temp;
ALTER FUNCTION public.check_marketplace_sales_revision_boundary() SET search_path=pg_catalog,public,pg_temp;
-- Only this trigger elevates: receipt INSERT is not granted to the runtime.
ALTER FUNCTION public.publish_marketplace_sales_revision() SECURITY DEFINER;

REVOKE EXECUTE ON FUNCTION public.reject_marketplace_sales_history_mutation(),
    public.reject_marketplace_sales_sealed_detail(), public.validate_marketplace_sales_publication_insert(),
    public.publish_marketplace_sales_revision(), public.validate_marketplace_sales_revision_boundary(uuid,uuid,bigint),
    public.check_marketplace_sales_revision_boundary() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.validate_marketplace_sales_revision_boundary(uuid,uuid,bigint) TO flooow_room_history_runtime;

GRANT INSERT (organization_id,marketplace_order_id,trigger_change_sequence,read_evidence_version,marketplace_key,external_order_id,currency,projected_at,assembly_policy_version,calculation_policy_version,state_kind,calculation_kind,coverage_count,state_payload_format_version,state_payload,manifest_format_version,manifest_digest,manifest_bytes) ON public.marketplace_sales_intelligence_revision TO flooow_room_history_runtime;
GRANT SELECT ON public.marketplace_sales_intelligence_revision TO flooow_room_history_runtime;
GRANT SELECT, INSERT ON TABLE
    public.marketplace_sales_intelligence_revision_observation,
    public.marketplace_sales_intelligence_revision_correction,
    public.marketplace_sales_intelligence_revision_reason,
    public.marketplace_sales_intelligence_revision_coverage TO flooow_room_history_runtime;
GRANT SELECT ON TABLE public.marketplace_sales_intelligence_revision_publication TO flooow_room_history_runtime;
GRANT SELECT, INSERT ON TABLE public.marketplace_sales_intelligence_projection TO flooow_room_history_runtime;
GRANT UPDATE (source_evidence_version,state_kind,assembly_policy_version,calculation_policy_version,
    calculation_kind,state_payload,last_applied_change_sequence,projected_at,current_revision_id)
    ON public.marketplace_sales_intelligence_projection TO flooow_room_history_runtime;

GRANT SELECT (organization_id,marketplace_order_id,currency,marketplace_key,external_order_id)
    ON public.marketplace_economic_evidence_subject TO flooow_room_history_runtime, flooow_room_history_owner;
-- PostgreSQL row locks require UPDATE on at least one column. V015 forbids
-- currency changes and even no-op updates without advancing journal version.
GRANT UPDATE (currency) ON public.marketplace_economic_evidence_subject TO flooow_room_history_runtime;
GRANT SELECT (organization_id,marketplace_order_id,evidence_version,change_sequence)
    ON public.marketplace_economic_evidence_update TO flooow_room_history_runtime, flooow_room_history_owner;
GRANT SELECT (organization_id,marketplace_order_id,observation_id,evidence_version,identifier_kind)
    ON public.marketplace_economic_evidence_identifier TO flooow_room_history_runtime, flooow_room_history_owner;
GRANT SELECT (organization_id,marketplace_order_id,fact_id,evidence_version,family,observed_at)
    ON public.marketplace_economic_evidence_fact TO flooow_room_history_runtime, flooow_room_history_owner;
GRANT SELECT (organization_id,marketplace_order_id,attempt_id,evidence_version,family,attempted_at)
    ON public.marketplace_economic_evidence_collection_attempt TO flooow_room_history_runtime, flooow_room_history_owner;
GRANT SELECT (organization_id,marketplace_order_id,correction_id,evidence_version,superseded_fact_id,replacement_fact_id,observed_at)
    ON public.marketplace_economic_evidence_correction TO flooow_room_history_runtime, flooow_room_history_owner;
-- GENERATED ALWAYS identity allocation needs no runtime sequence grant.
-- No DELETE/UPDATE/TRUNCATE/TRIGGER history, receipt INSERT, owner membership,
-- schema CREATE, source payload SELECT, setval or general EXECUTE is granted.
