-- TASK-0165P:
-- exact accepted reconciliation assessment identity per durable case revision.
--
-- Existing V024 case rows are intentionally NOT backfilled. A case that existed
-- before this migration therefore retains UNKNOWN HISTORICAL LINEAGE until a
-- later governed revision is committed with verified lineage.

CREATE TABLE marketplace_reconciliation_case_revision_assessment (
    organization_id uuid NOT NULL,
    case_id uuid NOT NULL,
    case_revision bigint NOT NULL CHECK (case_revision > 0),

    assessment_fingerprint_version integer NOT NULL
        CHECK (assessment_fingerprint_version = 1),

    assessment_fingerprint text NOT NULL
        CHECK (assessment_fingerprint ~ '^[0-9a-f]{64}$'),

    assessment_snapshot_schema_version integer NOT NULL
        CHECK (assessment_snapshot_schema_version = 1),

    assessment_snapshot jsonb NOT NULL
        CHECK (
            jsonb_typeof(assessment_snapshot) = 'object'
            AND assessment_snapshot ? 'schemaVersion'
            AND assessment_snapshot->>'schemaVersion' = '1'
        ),

    accepted_at timestamptz(6) NOT NULL,

    PRIMARY KEY (organization_id, case_id, case_revision),

    FOREIGN KEY (organization_id, case_id)
        REFERENCES marketplace_reconciliation_case (organization_id, case_id)
        DEFERRABLE INITIALLY DEFERRED
);

CREATE INDEX marketplace_reconciliation_case_revision_assessment_case_idx
    ON marketplace_reconciliation_case_revision_assessment
        (organization_id, case_id, case_revision DESC);

CREATE OR REPLACE FUNCTION
reject_marketplace_reconciliation_case_revision_assessment_mutation()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION
        'reconciliation case assessment lineage is append-only';
END;
$$;

CREATE TRIGGER
marketplace_reconciliation_case_revision_assessment_no_update
    BEFORE UPDATE
    ON marketplace_reconciliation_case_revision_assessment
    FOR EACH ROW
    EXECUTE FUNCTION
        reject_marketplace_reconciliation_case_revision_assessment_mutation();

CREATE TRIGGER
marketplace_reconciliation_case_revision_assessment_no_delete
    BEFORE DELETE
    ON marketplace_reconciliation_case_revision_assessment
    FOR EACH ROW
    EXECUTE FUNCTION
        reject_marketplace_reconciliation_case_revision_assessment_mutation();

-- A newly inserted lineage row may only become durable when it represents
-- the revision that is current for the case at transaction commit.
CREATE OR REPLACE FUNCTION
validate_reconciliation_case_revision_assessment_current_revision()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    current_revision bigint;
BEGIN
    SELECT revision
      INTO current_revision
      FROM marketplace_reconciliation_case
     WHERE organization_id = NEW.organization_id
       AND case_id = NEW.case_id;

    IF current_revision IS NULL OR current_revision <> NEW.case_revision THEN
        RAISE EXCEPTION
            'reconciliation assessment lineage does not match current case revision';
    END IF;

    RETURN NEW;
END;
$$;

CREATE CONSTRAINT TRIGGER
validate_reconciliation_case_revision_assessment_at_commit
    AFTER INSERT
    ON marketplace_reconciliation_case_revision_assessment
    DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW
    EXECUTE FUNCTION
        validate_reconciliation_case_revision_assessment_current_revision();

-- V024 rows that already exist when V030 is installed are legal legacy rows.
--
-- A same-revision update is lifecycle-only authority. It may change status and
-- resolved_at, but it may not rewrite assessment-bound case context or economic
-- projection in place.
--
-- A newly inserted case or any transition to a different current revision must
-- have matching exact lineage by transaction commit.
CREATE OR REPLACE FUNCTION
validate_reconciliation_case_current_revision_has_assessment()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'UPDATE' THEN
        IF NEW.revision IS NOT DISTINCT FROM OLD.revision THEN
            IF
                NEW.organization_id IS DISTINCT FROM OLD.organization_id OR
                NEW.case_id IS DISTINCT FROM OLD.case_id OR
                NEW.marketplace_order_id IS DISTINCT FROM OLD.marketplace_order_id OR
                NEW.financial_trace_id IS DISTINCT FROM OLD.financial_trace_id OR
                NEW.policy_version IS DISTINCT FROM OLD.policy_version OR
                NEW.currency IS DISTINCT FROM OLD.currency OR
                NEW.opened_at IS DISTINCT FROM OLD.opened_at OR
                NEW.last_observed_at IS DISTINCT FROM OLD.last_observed_at OR
                NEW.absolute_difference_summary IS DISTINCT FROM OLD.absolute_difference_summary OR
                NEW.stage_details IS DISTINCT FROM OLD.stage_details OR
                NEW.evidence_entry_ids IS DISTINCT FROM OLD.evidence_entry_ids
            THEN
                RAISE EXCEPTION
                    'same-revision reconciliation case update may change lifecycle fields only';
            END IF;

            RETURN NEW;
        END IF;
    END IF;

    IF NOT EXISTS (
        SELECT 1
          FROM marketplace_reconciliation_case_revision_assessment lineage
         WHERE lineage.organization_id = NEW.organization_id
           AND lineage.case_id = NEW.case_id
           AND lineage.case_revision = NEW.revision
    ) THEN
        RAISE EXCEPTION
            'current reconciliation case revision lacks assessment lineage';
    END IF;

    RETURN NEW;
END;
$$;

CREATE CONSTRAINT TRIGGER
validate_reconciliation_case_current_revision_lineage_at_commit
    AFTER INSERT OR UPDATE
    ON marketplace_reconciliation_case
    DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW
    EXECUTE FUNCTION
        validate_reconciliation_case_current_revision_has_assessment();
