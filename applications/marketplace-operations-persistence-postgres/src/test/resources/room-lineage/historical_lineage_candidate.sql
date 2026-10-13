-- TEST-ONLY CANDIDATE. NOT A FLYWAY MIGRATION. DISPOSABLE POSTGRES ONLY.
CREATE TABLE marketplace_sales_intelligence_revision (
    organization_id uuid NOT NULL,
    marketplace_order_id uuid NOT NULL,
    projection_revision bigint GENERATED ALWAYS AS IDENTITY (MINVALUE 1 NO CYCLE),
    trigger_change_sequence bigint NOT NULL CHECK (trigger_change_sequence > 0),
    read_evidence_version bigint NOT NULL CHECK (read_evidence_version > 0),
    marketplace_key text NOT NULL,
    external_order_id text NOT NULL,
    currency char(3) NOT NULL CHECK (currency ~ '^[A-Z]{3}$'),
    projected_at timestamptz(6) NOT NULL,
    assembly_policy_version text NOT NULL CHECK (assembly_policy_version ~ '^[a-z0-9-]+/[1-9][0-9]*$'),
    calculation_policy_version text CHECK (calculation_policy_version ~ '^[a-z0-9][a-z0-9./-]{0,63}$'),
    state_kind text NOT NULL CHECK (state_kind IN ('UNRESOLVED','CALCULATED')),
    calculation_kind text CHECK (calculation_kind IN ('COMPLETE','INCOMPLETE')),
    coverage_count smallint NOT NULL CHECK (coverage_count BETWEEN 0 AND 9),
    state_payload_format_version smallint NOT NULL CHECK (state_payload_format_version = 1),
    state_payload jsonb NOT NULL CHECK (jsonb_typeof(state_payload) = 'object'),
    manifest_format_version smallint NOT NULL CHECK (manifest_format_version = 1),
    manifest_digest text NOT NULL CHECK (manifest_digest ~ '^[0-9a-f]{64}$'),
    manifest_bytes bytea NOT NULL CHECK (octet_length(manifest_bytes) > 0),
    CONSTRAINT msi_revision_pk PRIMARY KEY (organization_id,marketplace_order_id,projection_revision),
    CONSTRAINT msi_revision_global_uk UNIQUE (projection_revision),
    CONSTRAINT msi_revision_trigger_uk UNIQUE (organization_id,marketplace_order_id,trigger_change_sequence),
    CONSTRAINT msi_revision_boundary_uk UNIQUE (organization_id,marketplace_order_id,projection_revision,read_evidence_version),
    CONSTRAINT msi_revision_positive CHECK (projection_revision > 0),
    CONSTRAINT msi_revision_subject_fk FOREIGN KEY (organization_id,marketplace_order_id,currency)
        REFERENCES marketplace_economic_evidence_subject (organization_id,marketplace_order_id,currency),
    CONSTRAINT msi_revision_boundary_fk FOREIGN KEY (organization_id,marketplace_order_id,read_evidence_version)
        REFERENCES marketplace_economic_evidence_update (organization_id,marketplace_order_id,evidence_version),
    CONSTRAINT msi_revision_trigger_fk FOREIGN KEY (organization_id,trigger_change_sequence)
        REFERENCES marketplace_economic_evidence_update (organization_id,change_sequence),
    CONSTRAINT msi_revision_state_shape CHECK (
        (state_kind='UNRESOLVED' AND calculation_policy_version IS NULL AND calculation_kind IS NULL AND coverage_count=0) OR
        (state_kind='CALCULATED' AND calculation_policy_version IS NOT NULL AND calculation_kind IS NOT NULL)
    ),
    CONSTRAINT msi_revision_payload_shape CHECK ((
        (state_kind='UNRESOLVED' AND state_payload ? 'reasons' AND
            jsonb_typeof(state_payload->'reasons')='array' AND
            state_payload - ARRAY['reasons'] = '{}'::jsonb) OR
        (state_kind='CALCULATED' AND calculation_kind='INCOMPLETE' AND
            state_payload ?& ARRAY['missingTypes','partialTypes','suppliedComponents'] AND
            jsonb_typeof(state_payload->'missingTypes')='array' AND
            jsonb_typeof(state_payload->'partialTypes')='array' AND
            jsonb_typeof(state_payload->'suppliedComponents')='array' AND
            state_payload - ARRAY['missingTypes','partialTypes','suppliedComponents'] = '{}'::jsonb) OR
        (state_kind='CALCULATED' AND calculation_kind='COMPLETE' AND
            state_payload ?& ARRAY['marketplace','externalOrderId','orderOccurredAt','currency',
                'grossRevenue','totalMarketplaceFees','totalShipping','totalAdvertising','totalTaxes',
                'totalProductCost','totalFinancialCost','totalOtherAdjustments','contribution',
                'contributionMargin','truthQuality','components'] AND
            jsonb_typeof(state_payload->'components')='array' AND
            state_payload - ARRAY['marketplace','externalOrderId','orderOccurredAt','currency',
                'grossRevenue','totalMarketplaceFees','totalShipping','totalAdvertising','totalTaxes',
                'totalProductCost','totalFinancialCost','totalOtherAdjustments','contribution',
                'contributionMargin','truthQuality','components'] = '{}'::jsonb)
    ) IS TRUE)
);

CREATE TABLE marketplace_sales_intelligence_revision_observation (
    organization_id uuid NOT NULL,
    marketplace_order_id uuid NOT NULL,
    projection_revision bigint NOT NULL,
    read_evidence_version bigint NOT NULL,
    observation_id uuid NOT NULL,
    evidence_version bigint NOT NULL CHECK (evidence_version > 0 AND evidence_version <= read_evidence_version),
    identifier_kind text NOT NULL CHECK (identifier_kind IN ('FACT','ATTEMPT','CORRECTION')),
    context_role text NOT NULL CHECK (context_role IN ('CONSUMED_ACTIVE_FACT','HISTORICAL_SUPERSEDED_FACT','CORRECTION_CONTEXT','ATTEMPT_CONTEXT')),
    family text CHECK (family IN ('MARKETPLACE_ORDER','MARKETPLACE_PAYMENT','MARKETPLACE_SHIPPING','PRODUCT_COST','FISCAL_INVOICE','FISCAL_TAX','ADS_IDENTITY','ADS_ALLOCATION')),
    recorded_at timestamptz(6) NOT NULL,
    CONSTRAINT msi_observation_pk PRIMARY KEY (organization_id,marketplace_order_id,projection_revision,observation_id),
    CONSTRAINT msi_observation_tuple_uk UNIQUE (organization_id,marketplace_order_id,projection_revision,observation_id,evidence_version,identifier_kind),
    CONSTRAINT msi_observation_header_fk FOREIGN KEY (organization_id,marketplace_order_id,projection_revision,read_evidence_version)
        REFERENCES marketplace_sales_intelligence_revision (organization_id,marketplace_order_id,projection_revision,read_evidence_version),
    CONSTRAINT msi_observation_source_fk FOREIGN KEY (organization_id,marketplace_order_id,observation_id,evidence_version,identifier_kind)
        REFERENCES marketplace_economic_evidence_identifier (organization_id,marketplace_order_id,observation_id,evidence_version,identifier_kind),
    CONSTRAINT msi_observation_role_shape CHECK (
        (identifier_kind='FACT' AND family IS NOT NULL AND context_role IN ('CONSUMED_ACTIVE_FACT','HISTORICAL_SUPERSEDED_FACT')) OR
        (identifier_kind='ATTEMPT' AND family IS NOT NULL AND context_role='ATTEMPT_CONTEXT') OR
        (identifier_kind='CORRECTION' AND family IS NULL AND context_role='CORRECTION_CONTEXT')
    )
);

CREATE TABLE marketplace_sales_intelligence_revision_correction (
    organization_id uuid NOT NULL,
    marketplace_order_id uuid NOT NULL,
    projection_revision bigint NOT NULL,
    correction_id uuid NOT NULL,
    evidence_version bigint NOT NULL CHECK (evidence_version > 0),
    correction_kind text NOT NULL DEFAULT 'CORRECTION' CHECK (correction_kind='CORRECTION'),
    superseded_observation_id uuid NOT NULL,
    superseded_evidence_version bigint NOT NULL CHECK (superseded_evidence_version > 0 AND superseded_evidence_version < evidence_version),
    fact_kind text NOT NULL DEFAULT 'FACT' CHECK (fact_kind='FACT'),
    replacement_observation_id uuid NOT NULL,
    CONSTRAINT msi_correction_pk PRIMARY KEY (organization_id,marketplace_order_id,projection_revision,correction_id),
    CONSTRAINT msi_correction_target_uk UNIQUE (organization_id,marketplace_order_id,projection_revision,superseded_observation_id),
    CONSTRAINT msi_correction_distinct CHECK (correction_id<>superseded_observation_id AND correction_id<>replacement_observation_id AND superseded_observation_id<>replacement_observation_id),
    CONSTRAINT msi_correction_source_fk FOREIGN KEY (organization_id,marketplace_order_id,correction_id)
        REFERENCES marketplace_economic_evidence_correction (organization_id,marketplace_order_id,correction_id),
    CONSTRAINT msi_correction_member_fk FOREIGN KEY (organization_id,marketplace_order_id,projection_revision,correction_id,evidence_version,correction_kind)
        REFERENCES marketplace_sales_intelligence_revision_observation (organization_id,marketplace_order_id,projection_revision,observation_id,evidence_version,identifier_kind),
    CONSTRAINT msi_correction_old_fk FOREIGN KEY (organization_id,marketplace_order_id,projection_revision,superseded_observation_id,superseded_evidence_version,fact_kind)
        REFERENCES marketplace_sales_intelligence_revision_observation (organization_id,marketplace_order_id,projection_revision,observation_id,evidence_version,identifier_kind),
    CONSTRAINT msi_correction_new_fk FOREIGN KEY (organization_id,marketplace_order_id,projection_revision,replacement_observation_id,evidence_version,fact_kind)
        REFERENCES marketplace_sales_intelligence_revision_observation (organization_id,marketplace_order_id,projection_revision,observation_id,evidence_version,identifier_kind)
);

CREATE TABLE marketplace_sales_intelligence_revision_reason (
    organization_id uuid NOT NULL,
    marketplace_order_id uuid NOT NULL,
    projection_revision bigint NOT NULL,
    reason text NOT NULL CHECK (reason IN ('ORDER_OCCURRED_AT_UNRESOLVED','ORDER_OCCURRED_AT_CONFLICT','INCONSISTENT_ACTIVE_FACTS')),
    CONSTRAINT msi_reason_pk PRIMARY KEY (organization_id,marketplace_order_id,projection_revision,reason),
    CONSTRAINT msi_reason_header_fk FOREIGN KEY (organization_id,marketplace_order_id,projection_revision)
        REFERENCES marketplace_sales_intelligence_revision (organization_id,marketplace_order_id,projection_revision)
);

CREATE TABLE marketplace_sales_intelligence_revision_coverage (
    organization_id uuid NOT NULL,
    marketplace_order_id uuid NOT NULL,
    projection_revision bigint NOT NULL,
    component_type text NOT NULL CHECK (component_type IN ('REVENUE','MARKETPLACE_COMMISSION','MARKETPLACE_FEE','SHIPPING','ADVERTISING','TAX','PRODUCT_COST','FINANCIAL_COST','OTHER_ADJUSTMENT')),
    coverage_state text NOT NULL CHECK (coverage_state IN ('MISSING','PARTIAL','COMPLETE')),
    CONSTRAINT msi_coverage_pk PRIMARY KEY (organization_id,marketplace_order_id,projection_revision,component_type),
    CONSTRAINT msi_coverage_header_fk FOREIGN KEY (organization_id,marketplace_order_id,projection_revision)
        REFERENCES marketplace_sales_intelligence_revision (organization_id,marketplace_order_id,projection_revision)
);

CREATE TABLE marketplace_sales_intelligence_revision_publication (
    organization_id uuid NOT NULL,
    marketplace_order_id uuid NOT NULL,
    projection_revision bigint NOT NULL,
    published_at timestamptz(6) NOT NULL DEFAULT transaction_timestamp(),
    CONSTRAINT msi_publication_pk PRIMARY KEY (organization_id,marketplace_order_id,projection_revision),
    CONSTRAINT msi_publication_header_fk FOREIGN KEY (organization_id,marketplace_order_id,projection_revision)
        REFERENCES marketplace_sales_intelligence_revision (organization_id,marketplace_order_id,projection_revision)
);

ALTER TABLE marketplace_sales_intelligence_projection ADD COLUMN current_revision_id bigint;
ALTER TABLE marketplace_sales_intelligence_projection ADD CONSTRAINT msi_current_revision_fk
    FOREIGN KEY (organization_id,marketplace_order_id,current_revision_id)
    REFERENCES marketplace_sales_intelligence_revision (organization_id,marketplace_order_id,projection_revision);

CREATE INDEX msi_revision_history_idx ON marketplace_sales_intelligence_revision
    (organization_id,marketplace_order_id,projected_at DESC,projection_revision DESC);

CREATE FUNCTION reject_marketplace_sales_history_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'sales intelligence history is immutable';
END;
$$;

CREATE FUNCTION reject_marketplace_sales_sealed_detail() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM marketplace_sales_intelligence_revision_publication
        WHERE organization_id=NEW.organization_id AND marketplace_order_id=NEW.marketplace_order_id
        AND projection_revision=NEW.projection_revision) THEN
        RAISE EXCEPTION 'published sales intelligence detail is sealed';
    END IF;
    RETURN NEW;
END;
$$;

CREATE FUNCTION validate_marketplace_sales_publication_insert() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF pg_trigger_depth() < 2 THEN
        RAISE EXCEPTION 'publication receipt is owned by current projection trigger';
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER msi_receipt_insert_owner BEFORE INSERT ON marketplace_sales_intelligence_revision_publication
    FOR EACH ROW EXECUTE FUNCTION validate_marketplace_sales_publication_insert();

CREATE FUNCTION publish_marketplace_sales_revision() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE r marketplace_sales_intelligence_revision%ROWTYPE;
BEGIN
    IF NEW.current_revision_id IS NULL THEN
        RAISE EXCEPTION 'new publication requires historical revision';
    END IF;
    SELECT * INTO STRICT r FROM marketplace_sales_intelligence_revision
        WHERE organization_id=NEW.organization_id AND marketplace_order_id=NEW.marketplace_order_id
        AND projection_revision=NEW.current_revision_id;
    IF NEW.source_evidence_version IS DISTINCT FROM r.read_evidence_version OR
       NEW.last_applied_change_sequence IS DISTINCT FROM r.trigger_change_sequence OR
       NEW.projected_at IS DISTINCT FROM r.projected_at OR
       NEW.assembly_policy_version IS DISTINCT FROM r.assembly_policy_version OR
       NEW.calculation_policy_version IS DISTINCT FROM r.calculation_policy_version OR
       NEW.state_kind IS DISTINCT FROM r.state_kind OR
       NEW.calculation_kind IS DISTINCT FROM r.calculation_kind OR
       NEW.state_payload IS DISTINCT FROM r.state_payload THEN
        RAISE EXCEPTION 'current projection differs from frozen revision';
    END IF;
    IF TG_OP='UPDATE' THEN
        IF NEW.organization_id IS DISTINCT FROM OLD.organization_id OR
           NEW.marketplace_order_id IS DISTINCT FROM OLD.marketplace_order_id THEN
            RAISE EXCEPTION 'current projection subject is immutable';
        END IF;
        IF NEW.current_revision_id IS NOT DISTINCT FROM OLD.current_revision_id THEN
            RETURN NEW;
        END IF;
        IF NEW.last_applied_change_sequence <= OLD.last_applied_change_sequence OR
           NEW.source_evidence_version < OLD.source_evidence_version THEN
            RAISE EXCEPTION 'current publication regression';
        END IF;
    END IF;
    INSERT INTO marketplace_sales_intelligence_revision_publication
        (organization_id,marketplace_order_id,projection_revision)
        VALUES (NEW.organization_id,NEW.marketplace_order_id,NEW.current_revision_id);
    RETURN NEW;
END;
$$;
CREATE TRIGGER msi_current_publish AFTER INSERT OR UPDATE ON marketplace_sales_intelligence_projection
    FOR EACH ROW EXECUTE FUNCTION publish_marketplace_sales_revision();
CREATE TRIGGER msi_current_no_delete BEFORE DELETE ON marketplace_sales_intelligence_projection
    FOR EACH ROW EXECUTE FUNCTION reject_marketplace_sales_history_mutation();
CREATE TRIGGER msi_current_no_truncate BEFORE TRUNCATE ON marketplace_sales_intelligence_projection
    FOR EACH STATEMENT EXECUTE FUNCTION reject_marketplace_sales_history_mutation();

CREATE FUNCTION validate_marketplace_sales_revision_boundary(org uuid, ord uuid, rev bigint)
RETURNS void LANGUAGE plpgsql AS $$
DECLARE h marketplace_sales_intelligence_revision%ROWTYPE;
expected_reasons jsonb;
expected_missing jsonb;
expected_partial jsonb;
BEGIN
    SELECT * INTO STRICT h FROM marketplace_sales_intelligence_revision
        WHERE organization_id=org AND marketplace_order_id=ord AND projection_revision=rev;
    IF NOT EXISTS (SELECT 1 FROM marketplace_sales_intelligence_revision_publication
        WHERE organization_id=org AND marketplace_order_id=ord AND projection_revision=rev) THEN
        RAISE EXCEPTION 'revision was never published';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM marketplace_economic_evidence_subject s
        WHERE s.organization_id=org AND s.marketplace_order_id=ord AND
        s.marketplace_key=h.marketplace_key AND s.external_order_id=h.external_order_id AND s.currency=h.currency) THEN
        RAISE EXCEPTION 'revision subject mismatch';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM marketplace_economic_evidence_update u
        WHERE u.organization_id=org AND u.marketplace_order_id=ord AND
        u.change_sequence=h.trigger_change_sequence AND u.evidence_version<=h.read_evidence_version) THEN
        RAISE EXCEPTION 'trigger subject or read boundary mismatch';
    END IF;
    IF EXISTS (
        WITH expected AS (
            SELECT observation_id,evidence_version,identifier_kind
            FROM marketplace_economic_evidence_identifier
            WHERE organization_id=org AND marketplace_order_id=ord AND evidence_version<=h.read_evidence_version
        ), actual AS (
            SELECT observation_id,evidence_version,identifier_kind
            FROM marketplace_sales_intelligence_revision_observation
            WHERE organization_id=org AND marketplace_order_id=ord AND projection_revision=rev
        )
        (SELECT * FROM expected EXCEPT SELECT * FROM actual)
        UNION ALL
        (SELECT * FROM actual EXCEPT SELECT * FROM expected)
    ) THEN RAISE EXCEPTION 'durable identifier boundary mismatch'; END IF;
    IF EXISTS (
        WITH expected AS (
            SELECT f.fact_id id,f.evidence_version,'FACT'::text kind,f.family,f.observed_at recorded_at,
                CASE WHEN EXISTS (SELECT 1 FROM marketplace_economic_evidence_correction c
                    WHERE c.organization_id=org AND c.marketplace_order_id=ord AND
                    c.superseded_fact_id=f.fact_id AND c.evidence_version<=h.read_evidence_version)
                THEN 'HISTORICAL_SUPERSEDED_FACT' ELSE 'CONSUMED_ACTIVE_FACT' END role
            FROM marketplace_economic_evidence_fact f
                WHERE f.organization_id=org AND f.marketplace_order_id=ord AND f.evidence_version<=h.read_evidence_version
            UNION ALL
            SELECT a.attempt_id,a.evidence_version,'ATTEMPT',a.family,a.attempted_at,'ATTEMPT_CONTEXT'
            FROM marketplace_economic_evidence_collection_attempt a
                WHERE a.organization_id=org AND a.marketplace_order_id=ord AND a.evidence_version<=h.read_evidence_version
            UNION ALL
            SELECT c.correction_id,c.evidence_version,'CORRECTION',NULL::text,c.observed_at,'CORRECTION_CONTEXT'
            FROM marketplace_economic_evidence_correction c
                WHERE c.organization_id=org AND c.marketplace_order_id=ord AND c.evidence_version<=h.read_evidence_version
        ), actual AS (
            SELECT observation_id,evidence_version,identifier_kind,family,recorded_at,context_role
            FROM marketplace_sales_intelligence_revision_observation
                WHERE organization_id=org AND marketplace_order_id=ord AND projection_revision=rev
        )
        (SELECT * FROM expected EXCEPT SELECT * FROM actual)
        UNION ALL
        (SELECT * FROM actual EXCEPT SELECT * FROM expected)
    ) THEN RAISE EXCEPTION 'exact consumed membership mismatch'; END IF;
    IF EXISTS (
        WITH expected AS (
            SELECT c.correction_id,c.evidence_version,c.superseded_fact_id,f.evidence_version,c.replacement_fact_id
            FROM marketplace_economic_evidence_correction c
            JOIN marketplace_economic_evidence_fact f ON f.organization_id=c.organization_id AND
                f.marketplace_order_id=c.marketplace_order_id AND f.fact_id=c.superseded_fact_id
            WHERE c.organization_id=org AND c.marketplace_order_id=ord AND c.evidence_version<=h.read_evidence_version
        ), actual AS (
            SELECT correction_id,evidence_version,superseded_observation_id,superseded_evidence_version,replacement_observation_id
            FROM marketplace_sales_intelligence_revision_correction
                WHERE organization_id=org AND marketplace_order_id=ord AND projection_revision=rev
        )
        (SELECT * FROM expected EXCEPT SELECT * FROM actual)
        UNION ALL
        (SELECT * FROM actual EXCEPT SELECT * FROM expected)
    ) THEN RAISE EXCEPTION 'exact correction context mismatch'; END IF;
    SELECT COALESCE(jsonb_agg(reason ORDER BY reason COLLATE "C"),'[]'::jsonb) INTO expected_reasons
        FROM marketplace_sales_intelligence_revision_reason
        WHERE organization_id=org AND marketplace_order_id=ord AND projection_revision=rev;
    IF h.state_kind='UNRESOLVED' THEN
        IF jsonb_array_length(expected_reasons)=0 OR h.state_payload->'reasons' IS DISTINCT FROM expected_reasons OR
            EXISTS (SELECT 1 FROM marketplace_sales_intelligence_revision_coverage
                WHERE organization_id=org AND marketplace_order_id=ord AND projection_revision=rev) THEN
            RAISE EXCEPTION 'unresolved normalized outcome mismatch';
        END IF;
    ELSE
        IF expected_reasons <> '[]'::jsonb OR
            (SELECT count(*) FROM marketplace_sales_intelligence_revision_coverage
                WHERE organization_id=org AND marketplace_order_id=ord AND projection_revision=rev) <> h.coverage_count THEN
            RAISE EXCEPTION 'calculated normalized outcome incomplete';
        END IF;
        SELECT COALESCE(jsonb_agg(component_type ORDER BY component_type COLLATE "C"),'[]'::jsonb) INTO expected_missing
            FROM marketplace_sales_intelligence_revision_coverage WHERE organization_id=org AND
            marketplace_order_id=ord AND projection_revision=rev AND coverage_state='MISSING';
        SELECT COALESCE(jsonb_agg(component_type ORDER BY component_type COLLATE "C"),'[]'::jsonb) INTO expected_partial
            FROM marketplace_sales_intelligence_revision_coverage WHERE organization_id=org AND
            marketplace_order_id=ord AND projection_revision=rev AND coverage_state='PARTIAL';
        IF h.calculation_kind='INCOMPLETE' THEN
            IF h.state_payload->'missingTypes' IS DISTINCT FROM expected_missing OR
                h.state_payload->'partialTypes' IS DISTINCT FROM expected_partial OR
                (expected_missing='[]'::jsonb AND expected_partial='[]'::jsonb) THEN
                RAISE EXCEPTION 'incomplete normalized coverage mismatch';
            END IF;
        ELSE
            IF expected_missing<>'[]'::jsonb OR expected_partial<>'[]'::jsonb THEN
                RAISE EXCEPTION 'complete outcome contains missing or partial coverage';
            END IF;
        END IF;
    END IF;
END;
$$;

CREATE FUNCTION check_marketplace_sales_revision_boundary() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    PERFORM validate_marketplace_sales_revision_boundary(NEW.organization_id,NEW.marketplace_order_id,NEW.projection_revision);
    RETURN NEW;
END;
$$;

CREATE TRIGGER msi_header_immutable BEFORE UPDATE OR DELETE ON marketplace_sales_intelligence_revision
    FOR EACH ROW EXECUTE FUNCTION reject_marketplace_sales_history_mutation();
CREATE TRIGGER msi_header_no_truncate BEFORE TRUNCATE ON marketplace_sales_intelligence_revision
    FOR EACH STATEMENT EXECUTE FUNCTION reject_marketplace_sales_history_mutation();
CREATE CONSTRAINT TRIGGER msi_header_boundary AFTER INSERT ON marketplace_sales_intelligence_revision
    DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION check_marketplace_sales_revision_boundary();

CREATE TRIGGER msi_observation_immutable BEFORE UPDATE OR DELETE ON marketplace_sales_intelligence_revision_observation
    FOR EACH ROW EXECUTE FUNCTION reject_marketplace_sales_history_mutation();
CREATE TRIGGER msi_observation_no_truncate BEFORE TRUNCATE ON marketplace_sales_intelligence_revision_observation
    FOR EACH STATEMENT EXECUTE FUNCTION reject_marketplace_sales_history_mutation();
CREATE CONSTRAINT TRIGGER msi_observation_boundary AFTER INSERT ON marketplace_sales_intelligence_revision_observation
    DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION check_marketplace_sales_revision_boundary();
CREATE TRIGGER msi_observation_sealed_insert BEFORE INSERT ON marketplace_sales_intelligence_revision_observation
    FOR EACH ROW EXECUTE FUNCTION reject_marketplace_sales_sealed_detail();

CREATE TRIGGER msi_correction_immutable BEFORE UPDATE OR DELETE ON marketplace_sales_intelligence_revision_correction
    FOR EACH ROW EXECUTE FUNCTION reject_marketplace_sales_history_mutation();
CREATE TRIGGER msi_correction_no_truncate BEFORE TRUNCATE ON marketplace_sales_intelligence_revision_correction
    FOR EACH STATEMENT EXECUTE FUNCTION reject_marketplace_sales_history_mutation();
CREATE CONSTRAINT TRIGGER msi_correction_boundary AFTER INSERT ON marketplace_sales_intelligence_revision_correction
    DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION check_marketplace_sales_revision_boundary();
CREATE TRIGGER msi_correction_sealed_insert BEFORE INSERT ON marketplace_sales_intelligence_revision_correction
    FOR EACH ROW EXECUTE FUNCTION reject_marketplace_sales_sealed_detail();

CREATE TRIGGER msi_reason_immutable BEFORE UPDATE OR DELETE ON marketplace_sales_intelligence_revision_reason
    FOR EACH ROW EXECUTE FUNCTION reject_marketplace_sales_history_mutation();
CREATE TRIGGER msi_reason_no_truncate BEFORE TRUNCATE ON marketplace_sales_intelligence_revision_reason
    FOR EACH STATEMENT EXECUTE FUNCTION reject_marketplace_sales_history_mutation();
CREATE CONSTRAINT TRIGGER msi_reason_boundary AFTER INSERT ON marketplace_sales_intelligence_revision_reason
    DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION check_marketplace_sales_revision_boundary();
CREATE TRIGGER msi_reason_sealed_insert BEFORE INSERT ON marketplace_sales_intelligence_revision_reason
    FOR EACH ROW EXECUTE FUNCTION reject_marketplace_sales_sealed_detail();

CREATE TRIGGER msi_coverage_immutable BEFORE UPDATE OR DELETE ON marketplace_sales_intelligence_revision_coverage
    FOR EACH ROW EXECUTE FUNCTION reject_marketplace_sales_history_mutation();
CREATE TRIGGER msi_coverage_no_truncate BEFORE TRUNCATE ON marketplace_sales_intelligence_revision_coverage
    FOR EACH STATEMENT EXECUTE FUNCTION reject_marketplace_sales_history_mutation();
CREATE CONSTRAINT TRIGGER msi_coverage_boundary AFTER INSERT ON marketplace_sales_intelligence_revision_coverage
    DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION check_marketplace_sales_revision_boundary();
CREATE TRIGGER msi_coverage_sealed_insert BEFORE INSERT ON marketplace_sales_intelligence_revision_coverage
    FOR EACH ROW EXECUTE FUNCTION reject_marketplace_sales_sealed_detail();

CREATE TRIGGER msi_publication_immutable BEFORE UPDATE OR DELETE ON marketplace_sales_intelligence_revision_publication
    FOR EACH ROW EXECUTE FUNCTION reject_marketplace_sales_history_mutation();
CREATE TRIGGER msi_publication_no_truncate BEFORE TRUNCATE ON marketplace_sales_intelligence_revision_publication
    FOR EACH STATEMENT EXECUTE FUNCTION reject_marketplace_sales_history_mutation();
CREATE CONSTRAINT TRIGGER msi_publication_boundary AFTER INSERT ON marketplace_sales_intelligence_revision_publication
    DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION check_marketplace_sales_revision_boundary();
