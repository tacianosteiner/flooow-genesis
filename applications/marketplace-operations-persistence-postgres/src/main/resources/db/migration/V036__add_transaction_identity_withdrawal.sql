-- Forward-only evolution of V035.
-- WITHDRAWN revokes the current authority of one previously CONFIRMED
-- subject-target relation. It does not assert REJECTED and does not
-- confirm any replacement target.
--
-- Real authority provisioning and field activation remain HOLD.

DO $$
DECLARE
    kind_attnum smallint;
    kind_constraint text;
BEGIN
    SELECT attnum::smallint
      INTO STRICT kind_attnum
      FROM pg_attribute
     WHERE attrelid='marketplace_transaction_identity_decision'::regclass
       AND attname='kind'
       AND NOT attisdropped;

    SELECT conname
      INTO STRICT kind_constraint
      FROM pg_constraint
     WHERE conrelid='marketplace_transaction_identity_decision'::regclass
       AND contype='c'
       AND conkey=ARRAY[kind_attnum]::smallint[];

    EXECUTE format(
        'ALTER TABLE marketplace_transaction_identity_decision DROP CONSTRAINT %I',
        kind_constraint
    );
END;
$$;

ALTER TABLE marketplace_transaction_identity_decision
    ADD CONSTRAINT transaction_identity_decision_kind_v2_check
    CHECK (kind IN ('CONFIRMED','REJECTED','WITHDRAWN'));

DO $$
DECLARE
    kind_attnum smallint;
    kind_constraint text;
BEGIN
    SELECT attnum::smallint
      INTO STRICT kind_attnum
      FROM pg_attribute
     WHERE attrelid='marketplace_transaction_identity_head'::regclass
       AND attname='kind'
       AND NOT attisdropped;

    SELECT conname
      INTO STRICT kind_constraint
      FROM pg_constraint
     WHERE conrelid='marketplace_transaction_identity_head'::regclass
       AND contype='c'
       AND conkey=ARRAY[kind_attnum]::smallint[];

    EXECUTE format(
        'ALTER TABLE marketplace_transaction_identity_head DROP CONSTRAINT %I',
        kind_constraint
    );
END;
$$;

ALTER TABLE marketplace_transaction_identity_head
    ADD CONSTRAINT transaction_identity_head_kind_v2_check
    CHECK (kind IN ('CONFIRMED','REJECTED','WITHDRAWN'));

CREATE FUNCTION transaction_identity_withdrawal_locks(
    org uuid,
    actor uuid,
    id uuid,
    conn uuid,
    ref text,
    target uuid
)
RETURNS void
LANGUAGE plpgsql
SET search_path=pg_catalog,public,pg_temp
AS $$
DECLARE
    resource text;
BEGIN
    PERFORM 1
      FROM integration_organization
     WHERE organization_id=org
       AND status='ACTIVE'
     FOR SHARE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Command authority unavailable'
            USING ERRCODE='P0012';
    END IF;

    PERFORM 1
      FROM command_principal
     WHERE organization_id=org
       AND principal_id=actor
     FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Command authority unavailable'
            USING ERRCODE='P0012';
    END IF;

    PERFORM pg_advisory_xact_lock(
        hashtextextended(
            'transaction-identity/id/1:' || org || ':' || id,
            0
        )
    );

    FOR resource IN
        SELECT unnest(
            ARRAY[
                'transaction-identity/subject/1:' ||
                    org || ':' || conn || ':' ||
                    octet_length(ref) || ':' || ref,

                'transaction-identity/target/1:' ||
                    org || ':' || target
            ]
        )
        ORDER BY 1
    LOOP
        PERFORM pg_advisory_xact_lock(
            hashtextextended(resource,0)
        );
    END LOOP;
END;
$$;

CREATE FUNCTION transaction_identity_withdrawn_validate()
RETURNS trigger
LANGUAGE plpgsql
SET search_path=pg_catalog,public,pg_temp
AS $$
DECLARE
    parent marketplace_transaction_identity_decision;
BEGIN
    PERFORM transaction_identity_withdrawal_locks(
        NEW.organization_id,
        NEW.principal_id,
        NEW.decision_id,
        NEW.omie_connection_id,
        NEW.source_order_reference,
        NEW.marketplace_order_id
    );

    IF NEW.kind IS DISTINCT FROM 'WITHDRAWN'
       OR NEW.reason IS DISTINCT FROM 'CORRECTION'
       OR NEW.revision IS NULL
       OR NEW.revision <= 1
       OR NEW.supersedes_decision_id IS NULL THEN

        RAISE EXCEPTION 'Invalid withdrawal transition'
            USING ERRCODE='23514';
    END IF;

    IF NOT EXISTS (
        SELECT 1
          FROM command_principal p

          JOIN integration_connection ml
            ON ml.organization_id=p.organization_id
           AND ml.connection_id=p.mercado_livre_connection_id

          JOIN integration_connection om
            ON om.organization_id=p.organization_id
           AND om.connection_id=p.omie_connection_id

         WHERE p.organization_id=NEW.organization_id
           AND p.principal_id=NEW.principal_id
           AND p.mercado_livre_connection_id=NEW.ml_connection_id
           AND p.omie_connection_id=NEW.omie_connection_id
           AND ml.provider_key='br.com.mercadolivre'
           AND om.provider_key='omie'
    ) THEN
        RAISE EXCEPTION 'Authority scope mismatch'
            USING ERRCODE='23514';
    END IF;

    IF NOT EXISTS (
        SELECT 1
          FROM command_credential_revision c

         WHERE c.organization_id=NEW.organization_id
           AND c.principal_id=NEW.principal_id
           AND c.credential_id=NEW.credential_id
           AND c.revision=NEW.credential_revision
           AND c.state='ENABLED'

           AND NOT EXISTS (
               SELECT 1
                 FROM command_credential_revision next
                WHERE next.credential_id=c.credential_id
                  AND next.revision>c.revision
           )
    )
    OR NOT EXISTS (
        SELECT 1
          FROM command_permission_grant g

         WHERE g.organization_id=NEW.organization_id
           AND g.principal_id=NEW.principal_id
           AND g.grant_id=NEW.grant_id
           AND g.revision=NEW.grant_revision
           AND g.permission=NEW.permission
           AND g.permission='TRANSACTION_IDENTITY_DECISION_WRITE'
           AND g.state='ENABLED'

           AND NOT EXISTS (
               SELECT 1
                 FROM command_permission_grant next
                WHERE next.organization_id=g.organization_id
                  AND next.principal_id=g.principal_id
                  AND next.permission=g.permission
                  AND next.revision>g.revision
           )
    ) THEN
        RAISE EXCEPTION 'Command authority unavailable'
            USING ERRCODE='P0012';
    END IF;

    IF NEW.authorization_semantic_version
            IS DISTINCT FROM 'command-authorization/1'
       OR NEW.authorization_fingerprint
            IS DISTINCT FROM
               transaction_identity_grant_fingerprint(
                   NEW.organization_id,
                   NEW.grant_id
               ) THEN

        RAISE EXCEPTION 'Authorization lineage mismatch'
            USING ERRCODE='23514';
    END IF;

    SELECT d.*
      INTO parent
      FROM marketplace_transaction_identity_decision d

      JOIN marketplace_transaction_identity_head h
        ON h.organization_id=d.organization_id
       AND h.decision_id=d.decision_id

     WHERE d.organization_id=NEW.organization_id
       AND d.decision_id=NEW.supersedes_decision_id
       AND h.omie_connection_id=NEW.omie_connection_id
       AND h.source_order_reference=NEW.source_order_reference
       AND h.marketplace_order_id=NEW.marketplace_order_id
       AND h.kind='CONFIRMED'
       AND d.kind='CONFIRMED';

    IF NOT FOUND
       OR parent.omie_connection_id
            IS DISTINCT FROM NEW.omie_connection_id
       OR parent.source_order_reference
            IS DISTINCT FROM NEW.source_order_reference
       OR parent.marketplace_order_id
            IS DISTINCT FROM NEW.marketplace_order_id
       OR parent.revision + 1
            IS DISTINCT FROM NEW.revision THEN

        RAISE EXCEPTION 'Identity predecessor conflict'
            USING ERRCODE='P0011';
    END IF;

    IF parent.ml_connection_id
            IS DISTINCT FROM NEW.ml_connection_id
       OR parent.ml_capability
            IS DISTINCT FROM NEW.ml_capability
       OR parent.ml_progress_version
            IS DISTINCT FROM NEW.ml_progress_version
       OR parent.ml_record_ordinal
            IS DISTINCT FROM NEW.ml_record_ordinal
       OR parent.external_order_id
            IS DISTINCT FROM NEW.external_order_id
       OR parent.currency
            IS DISTINCT FROM NEW.currency
       OR parent.omie_capability
            IS DISTINCT FROM NEW.omie_capability
       OR parent.omie_progress_version
            IS DISTINCT FROM NEW.omie_progress_version
       OR parent.omie_record_ordinal
            IS DISTINCT FROM NEW.omie_record_ordinal
       OR parent.omie_semantic_fingerprint
            IS DISTINCT FROM NEW.omie_semantic_fingerprint
       OR parent.provider_revision_local
            IS DISTINCT FROM NEW.provider_revision_local THEN

        RAISE EXCEPTION 'Withdrawal evidence lineage mismatch'
            USING ERRCODE='23514';
    END IF;

    IF NEW.intent_fingerprint
            IS DISTINCT FROM transaction_identity_intent(NEW)
       OR NEW.decision_semantic_fingerprint
            IS DISTINCT FROM transaction_identity_fingerprint(NEW) THEN

        RAISE EXCEPTION 'Decision fingerprint mismatch'
            USING ERRCODE='23514';
    END IF;

    NEW.decided_at := clock_timestamp();

    RETURN NEW;
END;
$$;

DROP TRIGGER transaction_identity_validate
    ON marketplace_transaction_identity_decision;

CREATE TRIGGER transaction_identity_validate
BEFORE INSERT ON marketplace_transaction_identity_decision
FOR EACH ROW
WHEN (NEW.kind <> 'WITHDRAWN')
EXECUTE FUNCTION transaction_identity_validate();

CREATE TRIGGER transaction_identity_withdrawn_validate
BEFORE INSERT ON marketplace_transaction_identity_decision
FOR EACH ROW
WHEN (NEW.kind = 'WITHDRAWN')
EXECUTE FUNCTION transaction_identity_withdrawn_validate();