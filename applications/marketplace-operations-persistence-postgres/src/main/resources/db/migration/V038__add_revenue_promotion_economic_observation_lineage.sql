ALTER TABLE marketplace_order_revenue_source_promotion
    ADD COLUMN economic_observation_id uuid NULL;

ALTER TABLE marketplace_order_revenue_source_promotion
    ADD CONSTRAINT marketplace_order_revenue_source_promotion_economic_observation_fk
    FOREIGN KEY (
        organization_id,
        marketplace_order_id,
        economic_observation_id
    )
    REFERENCES marketplace_economic_evidence_fact (
        organization_id,
        marketplace_order_id,
        fact_id
    );

CREATE OR REPLACE FUNCTION validate_marketplace_order_revenue_source_promotion()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    source_currency char(3);
    source_external_order_id text;
    source_date_closed timestamptz;
    source_total_amount numeric(24,6);
    source_observed_at timestamptz;

    identity_currency char(3);
    identity_external_order_id text;
    identity_marketplace_key text;

    evidence_family text;
    evidence_observed_at timestamptz;
    evidence_component_type text;
    evidence_direction text;
    evidence_magnitude numeric(24,6);
    evidence_currency char(3);
    evidence_source_kind text;
    evidence_source_system_key text;
    evidence_source_external_reference text;
    evidence_occurred_at timestamptz;
    evidence_quality text;
    evidence_coverage text;
BEGIN
    SELECT
        source.currency,
        source.external_order_ref,
        source.date_closed,
        source.total_amount,
        source.observed_at
      INTO
        source_currency,
        source_external_order_id,
        source_date_closed,
        source_total_amount,
        source_observed_at
      FROM integration_mercado_livre_order_source_observation source
     WHERE source.organization_id = NEW.organization_id
       AND source.connection_id = NEW.source_connection_id
       AND source.capability = NEW.source_capability
       AND source.input_progress_version = NEW.source_input_progress_version
       AND source.record_ordinal = NEW.source_record_ordinal;

    SELECT
        identity.currency,
        identity.external_order_id,
        identity.marketplace_key
      INTO
        identity_currency,
        identity_external_order_id,
        identity_marketplace_key
      FROM marketplace_order_identity_registry identity
     WHERE identity.organization_id = NEW.organization_id
       AND identity.marketplace_order_id = NEW.marketplace_order_id;

    IF source_external_order_id IS NULL OR
       identity_external_order_id IS NULL OR
       identity_marketplace_key IS DISTINCT FROM 'mercado-livre' OR
       source_external_order_id IS DISTINCT FROM identity_external_order_id THEN
        RAISE EXCEPTION
            'marketplace order revenue promotion identity mismatch';
    END IF;

    IF source_date_closed IS NULL THEN
        RAISE EXCEPTION
            'marketplace order revenue source is not closed';
    END IF;

    IF NEW.outcome = 'IDENTITY_CONFLICT' THEN
        IF source_currency IS NOT DISTINCT FROM identity_currency THEN
            RAISE EXCEPTION
                'marketplace order revenue identity conflict is not proven';
        END IF;
    ELSIF source_currency IS DISTINCT FROM identity_currency THEN
        RAISE EXCEPTION
            'marketplace order revenue promotion currency mismatch';
    END IF;

    IF NEW.outcome IN ('PROMOTED', 'DUPLICATE') THEN
        IF NEW.economic_observation_id IS NULL THEN
            RAISE EXCEPTION
                'successful revenue promotion requires explicit economic observation lineage';
        END IF;

        SELECT
            fact.family,
            fact.observed_at,
            component.component_type,
            component.direction,
            component.magnitude,
            component.currency,
            component.source_kind,
            component.source_system_key,
            component.source_external_reference,
            component.occurred_at,
            component.quality,
            component.coverage
          INTO
            evidence_family,
            evidence_observed_at,
            evidence_component_type,
            evidence_direction,
            evidence_magnitude,
            evidence_currency,
            evidence_source_kind,
            evidence_source_system_key,
            evidence_source_external_reference,
            evidence_occurred_at,
            evidence_quality,
            evidence_coverage
          FROM marketplace_economic_evidence_fact fact
          JOIN marketplace_economic_evidence_component_fact component
            ON component.organization_id = fact.organization_id
           AND component.marketplace_order_id = fact.marketplace_order_id
           AND component.fact_id = fact.fact_id
         WHERE fact.organization_id = NEW.organization_id
           AND fact.marketplace_order_id = NEW.marketplace_order_id
           AND fact.fact_id = NEW.economic_observation_id;

        IF NOT FOUND THEN
            RAISE EXCEPTION
                'revenue promotion economic observation is unavailable';
        END IF;

        IF evidence_family IS DISTINCT FROM 'MARKETPLACE_ORDER' OR
           evidence_component_type IS DISTINCT FROM 'REVENUE' OR
           evidence_direction IS DISTINCT FROM 'ADDITION' OR
           evidence_quality IS DISTINCT FROM 'CONFIRMED' OR
           evidence_coverage IS DISTINCT FROM 'PARTIAL' OR
           evidence_source_kind IS DISTINCT FROM 'MARKETPLACE' OR
           evidence_source_system_key IS DISTINCT FROM 'br.com.mercadolivre' OR
           evidence_source_external_reference IS DISTINCT FROM source_external_order_id OR
           evidence_currency IS DISTINCT FROM source_currency OR
           evidence_magnitude IS DISTINCT FROM source_total_amount OR
           evidence_occurred_at IS DISTINCT FROM source_date_closed OR
           evidence_observed_at IS DISTINCT FROM source_observed_at THEN
            RAISE EXCEPTION
                'revenue promotion economic observation mismatch';
        END IF;
    ELSE
        IF NEW.economic_observation_id IS NOT NULL THEN
            RAISE EXCEPTION
                'conflict revenue promotion must not claim economic observation lineage';
        END IF;
    END IF;

    RETURN NEW;
END;
$$;