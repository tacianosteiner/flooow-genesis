-- Infrastructure only: deliberately no INSERT, seed, default actor or grant.
CREATE TABLE command_principal (
    organization_id uuid NOT NULL REFERENCES integration_organization(organization_id),
    principal_id uuid NOT NULL UNIQUE,
    mercado_livre_connection_id uuid NOT NULL,
    omie_connection_id uuid NOT NULL,
    reason text NOT NULL CHECK (length(btrim(reason)) BETWEEN 1 AND 512),
    provenance text NOT NULL CHECK (length(btrim(provenance)) BETWEEN 1 AND 1024),
    correlation_id uuid NOT NULL,
    decided_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (organization_id, principal_id),
    CHECK (mercado_livre_connection_id <> omie_connection_id),
    FOREIGN KEY (organization_id, mercado_livre_connection_id)
        REFERENCES integration_connection(organization_id, connection_id),
    FOREIGN KEY (organization_id, omie_connection_id)
        REFERENCES integration_connection(organization_id, connection_id)
);

CREATE TABLE command_credential_revision (
    organization_id uuid NOT NULL,
    principal_id uuid NOT NULL,
    credential_id uuid NOT NULL,
    revision integer NOT NULL CHECK (revision > 0),
    supersedes_revision integer,
    state text NOT NULL CHECK (state IN ('ENABLED', 'DISABLED')),
    secret_verifier bytea NOT NULL CHECK (octet_length(secret_verifier) = 32),
    reason text NOT NULL CHECK (length(btrim(reason)) BETWEEN 1 AND 512),
    provenance text NOT NULL CHECK (length(btrim(provenance)) BETWEEN 1 AND 1024),
    correlation_id uuid NOT NULL,
    decided_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (organization_id, credential_id, revision),
    UNIQUE (credential_id, revision),
    CHECK ((revision = 1 AND supersedes_revision IS NULL) OR
        (revision > 1 AND supersedes_revision IS NOT NULL AND supersedes_revision = revision - 1)),
    FOREIGN KEY (organization_id, principal_id) REFERENCES command_principal,
    FOREIGN KEY (organization_id, credential_id, supersedes_revision)
        REFERENCES command_credential_revision(organization_id, credential_id, revision)
);
CREATE INDEX command_credential_lookup_idx ON command_credential_revision(credential_id, revision DESC);

CREATE TABLE command_permission_grant (
    organization_id uuid NOT NULL,
    principal_id uuid NOT NULL,
    grant_id uuid NOT NULL,
    permission text NOT NULL CHECK (permission IN
        ('TRANSACTION_IDENTITY_DECISION_WRITE', 'TRANSACTION_IDENTITY_POLICY_ADMIN')),
    state text NOT NULL CHECK (state IN ('ENABLED', 'DISABLED')),
    revision integer NOT NULL CHECK (revision > 0),
    supersedes_grant_id uuid,
    reason text NOT NULL CHECK (length(btrim(reason)) BETWEEN 1 AND 512),
    provenance text NOT NULL CHECK (length(btrim(provenance)) BETWEEN 1 AND 1024),
    correlation_id uuid NOT NULL,
    decided_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (organization_id, grant_id),
    UNIQUE (organization_id, principal_id, permission, revision),
    UNIQUE (organization_id, supersedes_grant_id),
    CHECK ((revision = 1 AND supersedes_grant_id IS NULL) OR
        (revision > 1 AND supersedes_grant_id IS NOT NULL)),
    FOREIGN KEY (organization_id, principal_id) REFERENCES command_principal,
    FOREIGN KEY (organization_id, supersedes_grant_id)
        REFERENCES command_permission_grant(organization_id, grant_id)
);

CREATE FUNCTION command_authority_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Command authority history is immutable' USING ERRCODE = '23514';
END;
$$;
CREATE TRIGGER command_principal_immutable BEFORE UPDATE OR DELETE ON command_principal
    FOR EACH ROW EXECUTE FUNCTION command_authority_immutable();
CREATE TRIGGER command_credential_immutable BEFORE UPDATE OR DELETE ON command_credential_revision
    FOR EACH ROW EXECUTE FUNCTION command_authority_immutable();
CREATE TRIGGER command_grant_immutable BEFORE UPDATE OR DELETE ON command_permission_grant
    FOR EACH ROW EXECUTE FUNCTION command_authority_immutable();

CREATE FUNCTION command_credential_lineage() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE previous command_credential_revision;
BEGIN
    PERFORM 1 FROM command_principal WHERE organization_id=NEW.organization_id
        AND principal_id=NEW.principal_id FOR UPDATE;
    IF NEW.revision > 1 THEN
        SELECT * INTO previous FROM command_credential_revision
            WHERE credential_id=NEW.credential_id ORDER BY revision DESC LIMIT 1;
        IF NOT FOUND OR previous.organization_id<>NEW.organization_id
            OR previous.principal_id<>NEW.principal_id
            OR previous.revision<>NEW.supersedes_revision THEN
            RAISE EXCEPTION 'Invalid command credential lineage' USING ERRCODE = '23514';
        END IF;
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER command_credential_lineage_insert BEFORE INSERT ON command_credential_revision
    FOR EACH ROW EXECUTE FUNCTION command_credential_lineage();

CREATE FUNCTION command_grant_lineage() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE previous command_permission_grant;
BEGIN
    PERFORM 1 FROM command_principal WHERE organization_id=NEW.organization_id
        AND principal_id=NEW.principal_id FOR UPDATE;
    IF NEW.revision > 1 THEN
        SELECT * INTO previous FROM command_permission_grant
            WHERE organization_id=NEW.organization_id AND grant_id=NEW.supersedes_grant_id;
        IF NOT FOUND OR previous.principal_id<>NEW.principal_id
            OR previous.permission<>NEW.permission OR previous.revision<>NEW.revision-1
            OR EXISTS (SELECT 1 FROM command_permission_grant
                WHERE organization_id=NEW.organization_id AND supersedes_grant_id=previous.grant_id) THEN
            RAISE EXCEPTION 'Invalid command grant lineage' USING ERRCODE = '23514';
        END IF;
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER command_grant_lineage_insert BEFORE INSERT ON command_permission_grant
    FOR EACH ROW EXECUTE FUNCTION command_grant_lineage();

CREATE FUNCTION command_principal_scope() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM integration_connection WHERE organization_id=NEW.organization_id
        AND connection_id=NEW.mercado_livre_connection_id AND provider_key='br.com.mercadolivre')
        OR NOT EXISTS (SELECT 1 FROM integration_connection WHERE organization_id=NEW.organization_id
        AND connection_id=NEW.omie_connection_id AND provider_key='omie') THEN
        RAISE EXCEPTION 'Invalid command principal provider scope' USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER command_principal_scope_insert BEFORE INSERT ON command_principal
    FOR EACH ROW EXECUTE FUNCTION command_principal_scope();
