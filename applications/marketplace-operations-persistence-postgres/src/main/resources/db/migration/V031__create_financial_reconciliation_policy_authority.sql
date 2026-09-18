-- TASK-0165P / live reconciliation prerequisite:
-- durable explicit FinancialReconciliationPolicy authority.
--
-- Policy definitions are immutable and versioned.
-- Selection is scoped by organization + marketplace + currency.
-- There is deliberately no default or environment-derived tolerance policy.

CREATE OR REPLACE FUNCTION
validate_marketplace_financial_reconciliation_tolerances(
    value jsonb
)
RETURNS boolean
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    stage_name text;
    amount_text text;
    amount_value numeric;
    key_count integer;
    required_stages text[] :=
        ARRAY[
            'SALE',
            'MARKETPLACE_COMMISSION',
            'MARKETPLACE_FEE',
            'SHIPPING',
            'ADVERTISING',
            'TAX',
            'PRODUCT_COST',
            'FINANCIAL_COST',
            'OTHER_ADJUSTMENT',
            'SETTLEMENT',
            'PAYMENT_ACCOUNT',
            'BANK'
        ];
BEGIN
    IF value IS NULL OR jsonb_typeof(value) <> 'object' THEN
        RETURN FALSE;
    END IF;

    SELECT count(*)
      INTO key_count
      FROM jsonb_object_keys(value);

    IF key_count <> array_length(required_stages, 1) THEN
        RETURN FALSE;
    END IF;

    FOREACH stage_name IN ARRAY required_stages
    LOOP
        IF NOT value ? stage_name THEN
            RETURN FALSE;
        END IF;

        IF jsonb_typeof(value -> stage_name) <> 'string' THEN
            RETURN FALSE;
        END IF;

        amount_text := value ->> stage_name;

        IF amount_text !~
            '^(0|[1-9][0-9]*)(\.[0-9]{1,6})?$'
        THEN
            RETURN FALSE;
        END IF;

        amount_value := amount_text::numeric;

        IF amount_value >= 1000000000000000000 THEN
            RETURN FALSE;
        END IF;
    END LOOP;

    RETURN TRUE;
END;
$$;

CREATE TABLE marketplace_financial_reconciliation_policy (
    organization_id uuid NOT NULL,
    marketplace_key text NOT NULL
        CHECK (
            octet_length(marketplace_key) BETWEEN 1 AND 100
            AND marketplace_key ~ '^[a-z0-9][a-z0-9.-]*$'
        ),
    currency char(3) NOT NULL
        CHECK (currency ~ '^[A-Z]{3}$'),
    policy_version text NOT NULL
        CHECK (
            octet_length(policy_version) BETWEEN 1 AND 100
            AND policy_version ~ '^[a-z0-9][a-z0-9./-]{0,99}$'
        ),
    stage_tolerances jsonb NOT NULL
        CHECK (
            validate_marketplace_financial_reconciliation_tolerances(
                stage_tolerances
            )
        ),
    created_at timestamptz(6) NOT NULL
        DEFAULT transaction_timestamp(),

    PRIMARY KEY (
        organization_id,
        marketplace_key,
        currency,
        policy_version
    ),

    FOREIGN KEY (organization_id)
        REFERENCES integration_organization (organization_id)
);

CREATE TABLE marketplace_financial_reconciliation_policy_current (
    organization_id uuid NOT NULL,
    marketplace_key text NOT NULL,
    currency char(3) NOT NULL,
    policy_version text NOT NULL,
    activated_at timestamptz(6) NOT NULL
        DEFAULT transaction_timestamp(),

    PRIMARY KEY (
        organization_id,
        marketplace_key,
        currency
    ),

    FOREIGN KEY (
        organization_id,
        marketplace_key,
        currency,
        policy_version
    )
        REFERENCES marketplace_financial_reconciliation_policy (
            organization_id,
            marketplace_key,
            currency,
            policy_version
        )
);

CREATE OR REPLACE FUNCTION
reject_marketplace_financial_reconciliation_policy_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION
        'financial reconciliation policy definitions are immutable';
END;
$$;

CREATE TRIGGER
marketplace_financial_reconciliation_policy_no_update
    BEFORE UPDATE
    ON marketplace_financial_reconciliation_policy
    FOR EACH ROW
    EXECUTE FUNCTION
        reject_marketplace_financial_reconciliation_policy_mutation();

CREATE TRIGGER
marketplace_financial_reconciliation_policy_no_delete
    BEFORE DELETE
    ON marketplace_financial_reconciliation_policy
    FOR EACH ROW
    EXECUTE FUNCTION
        reject_marketplace_financial_reconciliation_policy_mutation();

CREATE OR REPLACE FUNCTION
validate_marketplace_financial_reconciliation_policy_current_update()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF
        NEW.organization_id IS DISTINCT FROM OLD.organization_id OR
        NEW.marketplace_key IS DISTINCT FROM OLD.marketplace_key OR
        NEW.currency IS DISTINCT FROM OLD.currency
    THEN
        RAISE EXCEPTION
            'financial reconciliation policy binding scope is immutable';
    END IF;

    IF
        NEW.policy_version IS NOT DISTINCT FROM OLD.policy_version AND
        NEW.activated_at IS DISTINCT FROM OLD.activated_at
    THEN
        RAISE EXCEPTION
            'financial reconciliation policy activation timestamp requires version change';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER
marketplace_financial_reconciliation_policy_current_scope_guard
    BEFORE UPDATE
    ON marketplace_financial_reconciliation_policy_current
    FOR EACH ROW
    EXECUTE FUNCTION
        validate_marketplace_financial_reconciliation_policy_current_update();

CREATE OR REPLACE FUNCTION
reject_marketplace_financial_reconciliation_policy_current_delete()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION
        'financial reconciliation current policy binding cannot be deleted';
END;
$$;

CREATE TRIGGER
marketplace_financial_reconciliation_policy_current_no_delete
    BEFORE DELETE
    ON marketplace_financial_reconciliation_policy_current
    FOR EACH ROW
    EXECUTE FUNCTION
        reject_marketplace_financial_reconciliation_policy_current_delete();
