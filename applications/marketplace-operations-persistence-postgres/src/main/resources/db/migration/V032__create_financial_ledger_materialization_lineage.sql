-- TASK-0165Q / 4C-B3-B1
-- Durable exact source-authority -> immutable Financial Ledger entry lineage.
--
-- This migration does not create provider basis authority and does not
-- materialize any ledger fact by itself.

CREATE TABLE marketplace_financial_ledger_materialization_lineage (
    organization_id uuid NOT NULL
        REFERENCES integration_organization (organization_id),
    source_order_id uuid NOT NULL,
    source_authority_identity uuid NOT NULL,
    source_fingerprint_canonicalization_version integer NOT NULL CHECK (
        source_fingerprint_canonicalization_version = 1
    ),
    source_fingerprint_sha256 text NOT NULL CHECK (
        octet_length(source_fingerprint_sha256) = 64 AND
        source_fingerprint_sha256 ~ '^[0-9a-f]{64}$'
    ),
    source_authority_semantic_version text NOT NULL CHECK (
        octet_length(source_authority_semantic_version) BETWEEN 1 AND 64 AND
        source_authority_semantic_version ~ '^[a-z0-9][a-z0-9./-]{0,63}$'
    ),
    materialization_policy_version text NOT NULL CHECK (
        materialization_policy_version =
            'marketplace-financial-ledger-materialization/1'
    ),
    stage text NOT NULL CHECK (stage IN (
        'SALE',
        'MARKETPLACE_COMMISSION',
        'MARKETPLACE_FEE',
        'SHIPPING',
        'ADVERTISING',
        'TAX',
        'PRODUCT_COST',
        'FINANCIAL_COST',
        'OTHER_ADJUSTMENT'
    )),
    basis text NOT NULL CHECK (basis IN ('EXPECTED', 'ACTUAL')),
    trace_id uuid NOT NULL,
    ledger_entry_id uuid NOT NULL,
    materialized_at timestamptz(6) NOT NULL DEFAULT transaction_timestamp(),

    PRIMARY KEY (
        organization_id,
        source_order_id,
        source_authority_identity
    ),
    UNIQUE (organization_id, ledger_entry_id),

    FOREIGN KEY (
        organization_id,
        source_order_id,
        source_authority_identity
    ) REFERENCES marketplace_economic_evidence_component_fact (
        organization_id,
        marketplace_order_id,
        fact_id
    ),

    FOREIGN KEY (organization_id, trace_id)
        REFERENCES marketplace_financial_trace (organization_id, trace_id),

    FOREIGN KEY (organization_id, ledger_entry_id)
        REFERENCES marketplace_financial_ledger_entry (organization_id, entry_id)
);

CREATE INDEX marketplace_financial_materialization_trace_idx
    ON marketplace_financial_ledger_materialization_lineage (
        organization_id,
        trace_id,
        materialized_at,
        source_authority_identity
    );

CREATE FUNCTION validate_marketplace_financial_materialization_lineage_insert()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    entry_trace_id uuid;
    trace_order_id uuid;
    trace_marketplace_key text;
    trace_external_order_id text;
    trace_currency text;
    entry_stage text;
    entry_basis text;
    entry_direction text;
    entry_magnitude numeric;
    entry_source_kind text;
    entry_source_system_key text;
    entry_external_reference text;
    entry_absence_reason text;
    entry_occurred_at timestamptz;
    entry_corrects_entry_id uuid;

    source_component_type text;
    source_expected_stage text;
    source_marketplace_key text;
    source_external_order_id text;
    source_subject_currency text;
    source_direction text;
    source_magnitude numeric;
    source_currency text;
    source_kind text;
    source_system_key text;
    source_external_reference text;
    source_absence_reason text;
    source_occurred_at timestamptz;
BEGIN
    SELECT
        entry.trace_id,
        trace.order_id,
        trace.marketplace_key,
        trace.external_order_id,
        trace.currency,
        entry.stage,
        entry.basis,
        entry.direction,
        entry.magnitude,
        entry.source_kind,
        entry.source_system_key,
        entry.external_reference,
        entry.external_reference_absence_reason,
        entry.occurred_at,
        entry.corrects_entry_id
    INTO
        entry_trace_id,
        trace_order_id,
        trace_marketplace_key,
        trace_external_order_id,
        trace_currency,
        entry_stage,
        entry_basis,
        entry_direction,
        entry_magnitude,
        entry_source_kind,
        entry_source_system_key,
        entry_external_reference,
        entry_absence_reason,
        entry_occurred_at,
        entry_corrects_entry_id
    FROM marketplace_financial_ledger_entry entry
    JOIN marketplace_financial_trace trace
      ON trace.organization_id = entry.organization_id
     AND trace.trace_id = entry.trace_id
    WHERE entry.organization_id = NEW.organization_id
      AND entry.entry_id = NEW.ledger_entry_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'financial materialization lineage ledger entry unavailable';
    END IF;

    SELECT
        component.component_type,
        component.direction,
        component.magnitude,
        component.currency,
        component.source_kind,
        component.source_system_key,
        component.source_external_reference,
        component.source_external_reference_absence_reason,
        component.occurred_at
    INTO
        source_component_type,
        source_direction,
        source_magnitude,
        source_currency,
        source_kind,
        source_system_key,
        source_external_reference,
        source_absence_reason,
        source_occurred_at
    FROM marketplace_economic_evidence_component_fact component
    WHERE component.organization_id = NEW.organization_id
      AND component.marketplace_order_id = NEW.source_order_id
      AND component.fact_id = NEW.source_authority_identity;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'financial materialization source component unavailable';
    END IF;

    SELECT
        subject.marketplace_key,
        subject.external_order_id,
        subject.currency
    INTO
        source_marketplace_key,
        source_external_order_id,
        source_subject_currency
    FROM marketplace_economic_evidence_subject subject
    WHERE subject.organization_id = NEW.organization_id
      AND subject.marketplace_order_id = NEW.source_order_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'financial materialization source subject unavailable';
    END IF;

    source_expected_stage := CASE source_component_type
        WHEN 'REVENUE' THEN 'SALE'
        WHEN 'MARKETPLACE_COMMISSION' THEN 'MARKETPLACE_COMMISSION'
        WHEN 'MARKETPLACE_FEE' THEN 'MARKETPLACE_FEE'
        WHEN 'SHIPPING' THEN 'SHIPPING'
        WHEN 'ADVERTISING' THEN 'ADVERTISING'
        WHEN 'TAX' THEN 'TAX'
        WHEN 'PRODUCT_COST' THEN 'PRODUCT_COST'
        WHEN 'FINANCIAL_COST' THEN 'FINANCIAL_COST'
        WHEN 'OTHER_ADJUSTMENT' THEN 'OTHER_ADJUSTMENT'
        ELSE NULL
    END;

    IF source_expected_stage IS NULL THEN
        RAISE EXCEPTION
            'financial materialization component type unsupported';
    END IF;

    IF entry_trace_id <> NEW.trace_id OR
       trace_order_id <> NEW.source_order_id OR
       trace_marketplace_key IS DISTINCT FROM source_marketplace_key OR
       trace_external_order_id IS DISTINCT FROM source_external_order_id OR
       trace_currency IS DISTINCT FROM source_subject_currency OR
       entry_stage <> NEW.stage OR
       entry_basis <> NEW.basis OR
       entry_stage <> source_expected_stage OR
       trace_currency IS DISTINCT FROM source_currency OR
       entry_direction IS DISTINCT FROM source_direction OR
       entry_magnitude IS DISTINCT FROM source_magnitude OR
       entry_source_kind IS DISTINCT FROM source_kind OR
       entry_source_system_key IS DISTINCT FROM source_system_key OR
       entry_external_reference IS DISTINCT FROM source_external_reference OR
       entry_absence_reason IS DISTINCT FROM source_absence_reason OR
       entry_occurred_at IS DISTINCT FROM source_occurred_at THEN
        RAISE EXCEPTION
            'financial materialization lineage semantic mismatch';
    END IF;

    IF entry_corrects_entry_id IS NOT NULL THEN
        RAISE EXCEPTION
            'financial materialization correction lineage is not authorized by B3-B1';
    END IF;

    NEW.materialized_at := transaction_timestamp();
    RETURN NEW;
END;
$$;

CREATE TRIGGER validate_marketplace_financial_materialization_lineage_before_insert
    BEFORE INSERT
    ON marketplace_financial_ledger_materialization_lineage
    FOR EACH ROW
    EXECUTE FUNCTION validate_marketplace_financial_materialization_lineage_insert();

CREATE FUNCTION reject_marketplace_financial_materialization_lineage_mutation()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'financial materialization lineage is immutable';
END;
$$;

CREATE TRIGGER protect_marketplace_financial_materialization_lineage_update
    BEFORE UPDATE
    ON marketplace_financial_ledger_materialization_lineage
    FOR EACH ROW
    EXECUTE FUNCTION reject_marketplace_financial_materialization_lineage_mutation();

CREATE TRIGGER protect_marketplace_financial_materialization_lineage_delete
    BEFORE DELETE
    ON marketplace_financial_ledger_materialization_lineage
    FOR EACH ROW
    EXECUTE FUNCTION reject_marketplace_financial_materialization_lineage_mutation();
