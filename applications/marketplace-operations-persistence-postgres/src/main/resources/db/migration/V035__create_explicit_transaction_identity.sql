-- Empty infrastructure; real authority and field activation remain HOLD.
CREATE TABLE marketplace_transaction_identity_decision (
    organization_id uuid NOT NULL,
    decision_id uuid NOT NULL,
    omie_connection_id uuid NOT NULL,
    source_order_reference text NOT NULL CHECK (octet_length(source_order_reference) BETWEEN 1 AND 256
        AND source_order_reference=btrim(source_order_reference) AND source_order_reference !~ '[[:cntrl:]]'),
    marketplace_order_id uuid NOT NULL,
    kind text NOT NULL CHECK (kind IN ('CONFIRMED','REJECTED')),
    reason text NOT NULL CHECK (reason IN ('EXPLICIT_CONFIRMATION','EXPLICIT_REJECTION','CORRECTION','POLICY_EXACT_MATCH')),
    revision integer NOT NULL CHECK (revision>0),
    supersedes_decision_id uuid,
    ml_connection_id uuid NOT NULL,
    ml_capability text NOT NULL CHECK (ml_capability='marketplace-economic.order-source'),
    ml_progress_version bigint NOT NULL CHECK (ml_progress_version>=0),
    ml_record_ordinal integer NOT NULL CHECK (ml_record_ordinal>=0),
    external_order_id text NOT NULL,
    currency char(3) NOT NULL CHECK (currency ~ '^[A-Z]{3}$'),
    omie_capability text NOT NULL CHECK (omie_capability='marketplace-economic.omie-transaction-evidence.reacquisition-v3'),
    omie_progress_version bigint NOT NULL CHECK (omie_progress_version>=0),
    omie_record_ordinal integer NOT NULL CHECK (omie_record_ordinal>=0),
    omie_semantic_fingerprint char(64) NOT NULL CHECK (omie_semantic_fingerprint ~ '^[0-9a-f]{64}$'),
    provider_revision_local timestamp without time zone NOT NULL,
    principal_id uuid NOT NULL,
    credential_id uuid NOT NULL,
    credential_revision integer NOT NULL CHECK (credential_revision>0),
    grant_id uuid NOT NULL,
    grant_revision integer NOT NULL CHECK (grant_revision>0),
    permission text NOT NULL CHECK (permission='TRANSACTION_IDENTITY_DECISION_WRITE'),
    authorization_semantic_version text NOT NULL CHECK (authorization_semantic_version='command-authorization/1'),
    authorization_fingerprint char(64) NOT NULL CHECK (authorization_fingerprint ~ '^[0-9a-f]{64}$'),
    intent_fingerprint char(64) NOT NULL CHECK (intent_fingerprint ~ '^[0-9a-f]{64}$'),
    decision_semantic_fingerprint char(64) NOT NULL CHECK (decision_semantic_fingerprint ~ '^[0-9a-f]{64}$'),
    provenance text NOT NULL CHECK (octet_length(provenance) BETWEEN 1 AND 1024 AND provenance=btrim(provenance)
        AND provenance !~ '[[:cntrl:]]'),
    correlation_id uuid NOT NULL,
    decided_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (organization_id,decision_id),
    UNIQUE (organization_id,omie_connection_id,source_order_reference,marketplace_order_id,revision),
    UNIQUE (organization_id,supersedes_decision_id),
    CHECK ((revision=1 AND supersedes_decision_id IS NULL AND
        ((kind='CONFIRMED' AND reason='EXPLICIT_CONFIRMATION') OR (kind='REJECTED' AND reason='EXPLICIT_REJECTION')))
        OR (revision>1 AND supersedes_decision_id IS NOT NULL AND reason='CORRECTION')),
    CHECK (reason<>'POLICY_EXACT_MATCH'),
    FOREIGN KEY (organization_id,principal_id) REFERENCES command_principal,
    FOREIGN KEY (organization_id,credential_id,credential_revision) REFERENCES command_credential_revision,
    FOREIGN KEY (organization_id,grant_id) REFERENCES command_permission_grant,
    FOREIGN KEY (organization_id,marketplace_order_id) REFERENCES marketplace_order_identity_registry,
    FOREIGN KEY (organization_id,ml_connection_id,ml_capability,ml_progress_version,ml_record_ordinal)
        REFERENCES marketplace_order_occurrence_source_promotion,
    FOREIGN KEY (organization_id,omie_connection_id,omie_capability,omie_progress_version,omie_record_ordinal)
        REFERENCES integration_omie_transaction_evidence_v3,
    FOREIGN KEY (organization_id,supersedes_decision_id) REFERENCES marketplace_transaction_identity_decision
);

CREATE TABLE marketplace_transaction_identity_head (
    organization_id uuid NOT NULL,
    omie_connection_id uuid NOT NULL,
    source_order_reference text NOT NULL,
    marketplace_order_id uuid NOT NULL,
    decision_id uuid NOT NULL,
    kind text NOT NULL CHECK (kind IN ('CONFIRMED','REJECTED')),
    PRIMARY KEY (organization_id,omie_connection_id,source_order_reference,marketplace_order_id),
    FOREIGN KEY (organization_id,decision_id) REFERENCES marketplace_transaction_identity_decision
);
CREATE UNIQUE INDEX transaction_identity_confirmed_subject_idx ON marketplace_transaction_identity_head
    (organization_id,omie_connection_id,source_order_reference) WHERE kind='CONFIRMED';
CREATE UNIQUE INDEX transaction_identity_confirmed_target_idx ON marketplace_transaction_identity_head
    (organization_id,marketplace_order_id) WHERE kind='CONFIRMED';

CREATE FUNCTION transaction_identity_hash(VARIADIC fields text[]) RETURNS text LANGUAGE sql IMMUTABLE SET search_path=pg_catalog,public,pg_temp AS $$
    SELECT encode(sha256(convert_to(string_agg(octet_length(value)::text || ':' || value,'' ORDER BY ordinal),'UTF8')),'hex')
        FROM unnest(fields) WITH ORDINALITY AS f(value,ordinal);
$$;

CREATE FUNCTION transaction_identity_grant_fingerprint(org uuid, id uuid) RETURNS text LANGUAGE sql STABLE SET search_path=pg_catalog,public,pg_temp AS $$
    SELECT transaction_identity_hash('command-authorization/1',g.organization_id::text,g.principal_id::text,
        p.mercado_livre_connection_id::text,p.omie_connection_id::text,g.grant_id::text,g.revision::text,
        g.permission,g.state,coalesce(g.supersedes_grant_id::text,''),g.reason,g.provenance,g.correlation_id::text,
        to_char(g.decided_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS') ||
        CASE WHEN to_char(g.decided_at,'US')='000000' THEN ''
            WHEN right(to_char(g.decided_at,'US'),3)='000' THEN '.' || left(to_char(g.decided_at,'US'),3)
            ELSE '.' || to_char(g.decided_at,'US') END || 'Z')
    FROM command_permission_grant g JOIN command_principal p USING(organization_id,principal_id)
        WHERE g.organization_id=org AND g.grant_id=id;
$$;

CREATE FUNCTION transaction_identity_intent(d marketplace_transaction_identity_decision) RETURNS text LANGUAGE sql IMMUTABLE SET search_path=pg_catalog,public,pg_temp AS $$
    SELECT transaction_identity_hash('transaction-identity-intent/1',d.organization_id::text,d.principal_id::text,
        d.ml_connection_id::text,d.omie_connection_id::text,d.source_order_reference,d.marketplace_order_id::text,
        d.kind,d.reason,d.provenance,coalesce(d.supersedes_decision_id::text,''));
$$;
CREATE FUNCTION transaction_identity_fingerprint(d marketplace_transaction_identity_decision) RETURNS text LANGUAGE sql IMMUTABLE SET search_path=pg_catalog,public,pg_temp AS $$
    SELECT transaction_identity_hash('transaction-identity/1',d.intent_fingerprint,d.ml_connection_id::text,d.ml_capability,
        d.ml_progress_version::text,d.ml_record_ordinal::text,d.external_order_id,d.currency::text,d.omie_capability,'1',
        d.omie_semantic_fingerprint,to_char(d.provider_revision_local,'YYYY-MM-DD"T"HH24:MI:SS.US'),
        d.grant_id::text,d.grant_revision::text,d.permission,d.authorization_semantic_version,d.authorization_fingerprint);
$$;

CREATE FUNCTION transaction_identity_locks(org uuid, actor uuid, id uuid, conn uuid, ref text, target uuid)
RETURNS void LANGUAGE plpgsql SET search_path=pg_catalog,public,pg_temp AS $$
DECLARE resource text;
BEGIN
    PERFORM 1 FROM integration_organization WHERE organization_id=org AND status='ACTIVE' FOR SHARE;
    IF NOT FOUND THEN RAISE EXCEPTION 'Command authority unavailable' USING ERRCODE='P0012'; END IF;
    PERFORM 1 FROM command_principal WHERE organization_id=org AND principal_id=actor FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION 'Command authority unavailable' USING ERRCODE='P0012'; END IF;
    PERFORM pg_advisory_xact_lock(hashtextextended('transaction-identity/id/1:' || org || ':' || id,0));
    PERFORM 1 FROM integration_connector_progress WHERE organization_id=org AND connection_id=conn
        AND capability='marketplace-economic.omie-transaction-evidence.reacquisition-v3' FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION 'Identity evidence unavailable' USING ERRCODE='P0002'; END IF;
    FOR resource IN SELECT unnest(ARRAY[
        'transaction-identity/subject/1:' || org || ':' || conn || ':' || octet_length(ref) || ':' || ref,
        'transaction-identity/target/1:' || org || ':' || target]) ORDER BY 1 LOOP
        PERFORM pg_advisory_xact_lock(hashtextextended(resource,0));
    END LOOP;
END;
$$;

CREATE FUNCTION transaction_identity_validate() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,public,pg_temp AS $$
DECLARE parent marketplace_transaction_identity_decision; latest_local timestamp; fingerprints integer;
BEGIN
    PERFORM transaction_identity_locks(NEW.organization_id,NEW.principal_id,NEW.decision_id,
        NEW.omie_connection_id,NEW.source_order_reference,NEW.marketplace_order_id);
    IF NEW.reason='POLICY_EXACT_MATCH' THEN RAISE EXCEPTION 'Automatic identity unavailable' USING ERRCODE='23514'; END IF;
    IF NOT EXISTS (SELECT 1 FROM command_principal p JOIN integration_connection ml
        ON ml.organization_id=p.organization_id AND ml.connection_id=p.mercado_livre_connection_id
        JOIN integration_connection om ON om.organization_id=p.organization_id AND om.connection_id=p.omie_connection_id
        WHERE p.organization_id=NEW.organization_id AND p.principal_id=NEW.principal_id
        AND p.mercado_livre_connection_id=NEW.ml_connection_id AND p.omie_connection_id=NEW.omie_connection_id
        AND ml.provider_key='br.com.mercadolivre' AND om.provider_key='omie') THEN
        RAISE EXCEPTION 'Authority scope mismatch' USING ERRCODE='23514'; END IF;
    IF NOT EXISTS (SELECT 1 FROM command_credential_revision c WHERE c.organization_id=NEW.organization_id
        AND c.principal_id=NEW.principal_id AND c.credential_id=NEW.credential_id AND c.revision=NEW.credential_revision
        AND c.state='ENABLED' AND NOT EXISTS (SELECT 1 FROM command_credential_revision next
            WHERE next.credential_id=c.credential_id AND next.revision>c.revision))
        OR NOT EXISTS (SELECT 1 FROM command_permission_grant g WHERE g.organization_id=NEW.organization_id
            AND g.principal_id=NEW.principal_id AND g.grant_id=NEW.grant_id AND g.revision=NEW.grant_revision
            AND g.permission=NEW.permission AND g.permission='TRANSACTION_IDENTITY_DECISION_WRITE' AND g.state='ENABLED'
            AND NOT EXISTS (SELECT 1 FROM command_permission_grant next WHERE next.organization_id=g.organization_id
                AND next.principal_id=g.principal_id AND next.permission=g.permission AND next.revision>g.revision)) THEN
        RAISE EXCEPTION 'Command authority unavailable' USING ERRCODE='P0012'; END IF;
    IF NEW.authorization_semantic_version IS DISTINCT FROM 'command-authorization/1' OR
        NEW.authorization_fingerprint IS DISTINCT FROM transaction_identity_grant_fingerprint(NEW.organization_id,NEW.grant_id) THEN
        RAISE EXCEPTION 'Authorization lineage mismatch' USING ERRCODE='23514'; END IF;
    IF NEW.revision>1 THEN
        SELECT d.* INTO parent FROM marketplace_transaction_identity_decision d
            JOIN marketplace_transaction_identity_head h ON h.organization_id=d.organization_id AND h.decision_id=d.decision_id
            WHERE d.organization_id=NEW.organization_id AND d.decision_id=NEW.supersedes_decision_id;
        IF NOT FOUND OR parent.omie_connection_id IS DISTINCT FROM NEW.omie_connection_id
            OR parent.source_order_reference IS DISTINCT FROM NEW.source_order_reference
            OR parent.marketplace_order_id IS DISTINCT FROM NEW.marketplace_order_id OR parent.revision+1 IS DISTINCT FROM NEW.revision THEN
            RAISE EXCEPTION 'Identity predecessor conflict' USING ERRCODE='P0011'; END IF;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM marketplace_order_identity_registry i JOIN marketplace_order_occurrence_source_promotion p
        ON p.organization_id=i.organization_id AND p.marketplace_order_id=i.marketplace_order_id
        JOIN integration_mercado_livre_order_source_observation s ON s.organization_id=p.organization_id
            AND s.connection_id=p.source_connection_id AND s.capability=p.source_capability
            AND s.input_progress_version=p.source_input_progress_version AND s.record_ordinal=p.source_record_ordinal
        WHERE i.organization_id=NEW.organization_id AND i.marketplace_order_id=NEW.marketplace_order_id
            AND i.marketplace_key='mercado-livre' AND i.external_order_id=NEW.external_order_id AND i.currency=NEW.currency
            AND p.source_connection_id=NEW.ml_connection_id AND p.source_capability=NEW.ml_capability
            AND p.source_input_progress_version=NEW.ml_progress_version AND p.source_record_ordinal=NEW.ml_record_ordinal
            AND p.outcome IN ('PROMOTED','DUPLICATE') AND s.external_order_ref=i.external_order_id AND s.currency=i.currency) THEN
        RAISE EXCEPTION 'Target lineage mismatch' USING ERRCODE='23514'; END IF;
    IF EXISTS (SELECT 1 FROM integration_omie_transaction_evidence b LEFT JOIN integration_omie_transaction_evidence_v3 v
        USING(organization_id,connection_id,capability,input_progress_version,record_ordinal)
        LEFT JOIN integration_connector_page_commit p USING(organization_id,connection_id,capability,input_progress_version)
        WHERE b.organization_id=NEW.organization_id AND b.connection_id=NEW.omie_connection_id
            AND b.capability=NEW.omie_capability AND b.source_order_ref=NEW.source_order_reference
            AND (v.semantic_fingerprint_version IS NULL OR v.semantic_fingerprint_version<>1 OR p.record_count IS NULL
                OR b.record_ordinal>=p.record_count OR v.provider_modified_local<v.provider_created_local
                OR b.input_progress_version >= (SELECT progress_version FROM integration_connector_progress pr
                    WHERE pr.organization_id=b.organization_id AND pr.connection_id=b.connection_id AND pr.capability=b.capability)
                OR p.record_count<>(SELECT count(*) FROM integration_omie_transaction_evidence x WHERE x.organization_id=b.organization_id
                    AND x.connection_id=b.connection_id AND x.capability=b.capability AND x.input_progress_version=b.input_progress_version)
                OR p.record_count<>(SELECT count(*) FROM integration_omie_transaction_evidence_v3 x WHERE x.organization_id=b.organization_id
                    AND x.connection_id=b.connection_id AND x.capability=b.capability AND x.input_progress_version=b.input_progress_version))) THEN
        RAISE EXCEPTION 'Omie evidence integrity failure' USING ERRCODE='23514'; END IF;
    IF EXISTS (SELECT 1 FROM integration_omie_transaction_evidence b JOIN integration_omie_transaction_evidence_v3 v
        USING(organization_id,connection_id,capability,input_progress_version,record_ordinal)
        WHERE b.organization_id=NEW.organization_id AND b.connection_id=NEW.omie_connection_id
            AND b.capability=NEW.omie_capability AND b.source_order_ref=NEW.source_order_reference
            AND v.provider_modified_local IS NULL AND v.provider_created_local IS NULL) THEN
        RAISE EXCEPTION 'Currentness unproven' USING ERRCODE='P0010'; END IF;
    SELECT max(coalesce(v.provider_modified_local,v.provider_created_local)) INTO latest_local
        FROM integration_omie_transaction_evidence b JOIN integration_omie_transaction_evidence_v3 v
        USING(organization_id,connection_id,capability,input_progress_version,record_ordinal)
        WHERE b.organization_id=NEW.organization_id AND b.connection_id=NEW.omie_connection_id
            AND b.capability=NEW.omie_capability AND b.source_order_ref=NEW.source_order_reference;
    IF latest_local IS NULL THEN RAISE EXCEPTION 'Identity evidence unavailable' USING ERRCODE='P0002'; END IF;
    SELECT count(DISTINCT v.source_evidence_semantic_fingerprint) INTO fingerprints
        FROM integration_omie_transaction_evidence b JOIN integration_omie_transaction_evidence_v3 v
        USING(organization_id,connection_id,capability,input_progress_version,record_ordinal)
        WHERE b.organization_id=NEW.organization_id AND b.connection_id=NEW.omie_connection_id
            AND b.capability=NEW.omie_capability AND b.source_order_ref=NEW.source_order_reference
            AND coalesce(v.provider_modified_local,v.provider_created_local)=latest_local;
    IF fingerprints<>1 THEN RAISE EXCEPTION 'Current identity conflict' USING ERRCODE='P0011'; END IF;
    IF EXISTS (SELECT 1 FROM integration_omie_transaction_evidence b JOIN integration_omie_transaction_evidence_v3 v
        USING(organization_id,connection_id,capability,input_progress_version,record_ordinal)
        WHERE b.organization_id=NEW.organization_id AND b.connection_id=NEW.omie_connection_id AND b.capability=NEW.omie_capability
            AND b.source_order_ref=NEW.source_order_reference AND coalesce(v.provider_modified_local,v.provider_created_local)=latest_local
            AND ((b.source_integration_ref IS NOT NULL AND b.source_integration_ref<>NEW.external_order_id)
                OR (b.currency IS NOT NULL AND b.currency<>NEW.currency))) THEN
        RAISE EXCEPTION 'Current identity conflict' USING ERRCODE='P0011'; END IF;
    IF NOT EXISTS (SELECT 1 FROM integration_omie_transaction_evidence b JOIN integration_omie_transaction_evidence_v3 v
        USING(organization_id,connection_id,capability,input_progress_version,record_ordinal)
        WHERE b.organization_id=NEW.organization_id AND b.connection_id=NEW.omie_connection_id AND b.capability=NEW.omie_capability
            AND b.input_progress_version=NEW.omie_progress_version AND b.record_ordinal=NEW.omie_record_ordinal
            AND b.source_order_ref=NEW.source_order_reference AND v.source_evidence_semantic_fingerprint=NEW.omie_semantic_fingerprint
            AND coalesce(v.provider_modified_local,v.provider_created_local)=latest_local
            AND latest_local=NEW.provider_revision_local
            AND (b.source_integration_ref IS NULL OR b.source_integration_ref=NEW.external_order_id)
            AND (b.currency IS NULL OR b.currency=NEW.currency)) THEN
        RAISE EXCEPTION 'Current identity conflict' USING ERRCODE='P0011'; END IF;
    IF NEW.intent_fingerprint IS DISTINCT FROM transaction_identity_intent(NEW)
        OR NEW.decision_semantic_fingerprint IS DISTINCT FROM transaction_identity_fingerprint(NEW) THEN
        RAISE EXCEPTION 'Decision fingerprint mismatch' USING ERRCODE='23514'; END IF;
    NEW.decided_at := clock_timestamp();
    RETURN NEW;
END;
$$;

CREATE FUNCTION transaction_identity_head_guard() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,public,pg_temp AS $$
DECLARE d marketplace_transaction_identity_decision;
BEGIN
    IF TG_OP='DELETE' OR pg_trigger_depth()<>2 THEN RAISE EXCEPTION 'Identity head is derived only' USING ERRCODE='23514'; END IF;
    SELECT * INTO d FROM marketplace_transaction_identity_decision WHERE organization_id=NEW.organization_id AND decision_id=NEW.decision_id;
    IF NOT FOUND OR d.omie_connection_id IS DISTINCT FROM NEW.omie_connection_id
        OR d.source_order_reference IS DISTINCT FROM NEW.source_order_reference
        OR d.marketplace_order_id IS DISTINCT FROM NEW.marketplace_order_id OR d.kind IS DISTINCT FROM NEW.kind
        OR (TG_OP='UPDATE' AND (NEW.organization_id IS DISTINCT FROM OLD.organization_id
            OR NEW.omie_connection_id IS DISTINCT FROM OLD.omie_connection_id OR NEW.source_order_reference IS DISTINCT FROM OLD.source_order_reference
            OR NEW.marketplace_order_id IS DISTINCT FROM OLD.marketplace_order_id OR d.supersedes_decision_id IS DISTINCT FROM OLD.decision_id))
        OR (TG_OP='INSERT' AND d.supersedes_decision_id IS NOT NULL) THEN
        RAISE EXCEPTION 'Identity head lineage mismatch' USING ERRCODE='23514'; END IF;
    RETURN NEW;
END;
$$;
CREATE FUNCTION transaction_identity_advance() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,public,pg_temp AS $$
BEGIN
    IF NEW.supersedes_decision_id IS NULL THEN
        INSERT INTO public.marketplace_transaction_identity_head VALUES(NEW.organization_id,NEW.omie_connection_id,
            NEW.source_order_reference,NEW.marketplace_order_id,NEW.decision_id,NEW.kind);
    ELSE
        UPDATE public.marketplace_transaction_identity_head SET decision_id=NEW.decision_id,kind=NEW.kind
            WHERE organization_id=NEW.organization_id AND omie_connection_id=NEW.omie_connection_id
            AND source_order_reference=NEW.source_order_reference AND marketplace_order_id=NEW.marketplace_order_id
            AND decision_id=NEW.supersedes_decision_id;
        IF NOT FOUND THEN RAISE EXCEPTION 'Identity head predecessor conflict' USING ERRCODE='23514'; END IF;
    END IF;
    RETURN NEW;
END;
$$;
CREATE FUNCTION transaction_identity_immutable() RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,public,pg_temp AS $$
BEGIN RAISE EXCEPTION 'Identity decision history is immutable' USING ERRCODE='23514'; END;
$$;
CREATE TRIGGER transaction_identity_validate BEFORE INSERT ON marketplace_transaction_identity_decision
    FOR EACH ROW EXECUTE FUNCTION transaction_identity_validate();
CREATE TRIGGER transaction_identity_advance AFTER INSERT ON marketplace_transaction_identity_decision
    FOR EACH ROW EXECUTE FUNCTION transaction_identity_advance();
CREATE TRIGGER transaction_identity_immutable BEFORE UPDATE OR DELETE ON marketplace_transaction_identity_decision
    FOR EACH ROW EXECUTE FUNCTION transaction_identity_immutable();
CREATE TRIGGER transaction_identity_head_guard BEFORE INSERT OR UPDATE OR DELETE ON marketplace_transaction_identity_head
    FOR EACH ROW EXECUTE FUNCTION transaction_identity_head_guard();
