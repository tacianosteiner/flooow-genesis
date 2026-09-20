CREATE TABLE integration_omie_transaction_evidence_v3 (
    organization_id UUID NOT NULL,
    connection_id UUID NOT NULL,
    capability TEXT NOT NULL,
    input_progress_version BIGINT NOT NULL,
    record_ordinal INTEGER NOT NULL,

    source_order_origin TEXT,

    provider_created_local TIMESTAMP WITHOUT TIME ZONE,
    provider_modified_local TIMESTAMP WITHOUT TIME ZONE,

    source_cancelled BOOLEAN,
    source_cancelled_local TIMESTAMP WITHOUT TIME ZONE,

    source_invoiced BOOLEAN,
    source_invoiced_local TIMESTAMP WITHOUT TIME ZONE,

    source_authorized BOOLEAN,
    source_denied BOOLEAN,
    source_returned BOOLEAN,
    source_partially_returned BOOLEAN,

    order_ended BOOLEAN,
    order_ended_reason TEXT,
    order_ended_local TIMESTAMP WITHOUT TIME ZONE,

    order_discount_type TEXT,
    order_discount_percent NUMERIC(24,6),
    order_discount_amount NUMERIC(24,6),

    merchandise_amount NUMERIC(24,6),
    discount_amount NUMERIC(24,6),
    deduction_amount NUMERIC(24,6),

    freight_amount NUMERIC(24,6),
    insurance_amount NUMERIC(24,6),
    other_expense_amount NUMERIC(24,6),

    marketplace_fee_amount NUMERIC(24,6),
    marketplace_shipping_amount NUMERIC(24,6),

    additional_order_totals JSONB NOT NULL,

    semantic_fingerprint_version INTEGER NOT NULL,
    source_evidence_semantic_fingerprint CHAR(64) NOT NULL,

    PRIMARY KEY (
        organization_id,
        connection_id,
        capability,
        input_progress_version,
        record_ordinal
    ),

    FOREIGN KEY (
        organization_id,
        connection_id,
        capability,
        input_progress_version,
        record_ordinal
    ) REFERENCES integration_omie_transaction_evidence (
        organization_id,
        connection_id,
        capability,
        input_progress_version,
        record_ordinal
    ),

    CHECK (
        capability =
        'marketplace-economic.omie-transaction-evidence.reacquisition-v3'
    ),
    CHECK (semantic_fingerprint_version = 1),
    CHECK (
        source_evidence_semantic_fingerprint ~ '^[0-9a-f]{64}$'
    ),
    CHECK (jsonb_typeof(additional_order_totals) = 'object')
);

CREATE TABLE integration_omie_transaction_evidence_v3_line (
    organization_id UUID NOT NULL,
    connection_id UUID NOT NULL,
    capability TEXT NOT NULL,
    input_progress_version BIGINT NOT NULL,
    record_ordinal INTEGER NOT NULL,
    line_ordinal INTEGER NOT NULL,

    internal_item_ref TEXT,
    integration_item_ref TEXT,

    product_internal_ref TEXT,
    product_integration_ref TEXT,
    product_display_code TEXT,

    quantity NUMERIC(24,6),
    unit_value NUMERIC(24,6),

    discount_type TEXT,
    discount_percent NUMERIC(24,6),
    discount_value NUMERIC(24,6),
    deduction_value NUMERIC(24,6),

    merchandise_value NUMERIC(24,6),
    total_value NUMERIC(24,6),

    do_not_generate_financial BOOLEAN,
    do_not_sum_total BOOLEAN,

    is_kit BOOLEAN,
    is_kit_component BOOLEAN,
    kit_parent_item_ref TEXT,

    PRIMARY KEY (
        organization_id,
        connection_id,
        capability,
        input_progress_version,
        record_ordinal,
        line_ordinal
    ),

    FOREIGN KEY (
        organization_id,
        connection_id,
        capability,
        input_progress_version,
        record_ordinal
    ) REFERENCES integration_omie_transaction_evidence_v3 (
        organization_id,
        connection_id,
        capability,
        input_progress_version,
        record_ordinal
    ),

    CHECK (line_ordinal >= 0),
    CHECK (
        capability =
        'marketplace-economic.omie-transaction-evidence.reacquisition-v3'
    )
);

CREATE INDEX integration_omie_transaction_evidence_v3_lookup_idx
    ON integration_omie_transaction_evidence_v3 (
        organization_id,
        connection_id,
        provider_modified_local,
        provider_created_local
    );

CREATE FUNCTION reject_omie_transaction_v3_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'Omie transaction V3 source evidence is immutable';
END
$$;

CREATE TRIGGER protect_omie_transaction_v3_sidecar_mutation
BEFORE UPDATE OR DELETE ON integration_omie_transaction_evidence_v3
FOR EACH ROW EXECUTE FUNCTION reject_omie_transaction_v3_mutation();

CREATE TRIGGER protect_omie_transaction_v3_line_mutation
BEFORE UPDATE OR DELETE ON integration_omie_transaction_evidence_v3_line
FOR EACH ROW EXECUTE FUNCTION reject_omie_transaction_v3_mutation();

CREATE FUNCTION reject_omie_transaction_v3_base_update()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.capability =
       'marketplace-economic.omie-transaction-evidence.reacquisition-v3'
       OR NEW.capability =
       'marketplace-economic.omie-transaction-evidence.reacquisition-v3'
    THEN
        RAISE EXCEPTION 'Omie transaction V3 base source evidence is immutable';
    END IF;
    RETURN NEW;
END
$$;

CREATE TRIGGER protect_omie_transaction_v3_base_update
BEFORE UPDATE ON integration_omie_transaction_evidence
FOR EACH ROW EXECUTE FUNCTION reject_omie_transaction_v3_base_update();

CREATE FUNCTION reject_omie_transaction_v3_base_delete()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.capability =
       'marketplace-economic.omie-transaction-evidence.reacquisition-v3'
    THEN
        RAISE EXCEPTION 'Omie transaction V3 base source evidence is immutable';
    END IF;
    RETURN OLD;
END
$$;

CREATE TRIGGER protect_omie_transaction_v3_base_delete
BEFORE DELETE ON integration_omie_transaction_evidence
FOR EACH ROW EXECUTE FUNCTION reject_omie_transaction_v3_base_delete();
