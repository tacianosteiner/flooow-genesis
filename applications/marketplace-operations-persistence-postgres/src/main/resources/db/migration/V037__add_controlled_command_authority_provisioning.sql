-- Synthetic-testable control-plane infrastructure. No login, principal, credential or grant is seeded.
DO $$ BEGIN
    CREATE ROLE flooow_command_runtime NOLOGIN NOINHERIT;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
    CREATE ROLE flooow_command_issuer NOLOGIN NOINHERIT;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

REVOKE ALL ON command_principal,command_credential_revision,command_permission_grant FROM PUBLIC;
GRANT SELECT,UPDATE ON command_principal TO flooow_command_runtime;
GRANT SELECT ON command_credential_revision,command_permission_grant TO flooow_command_runtime;
GRANT SELECT ON integration_organization,integration_connection TO flooow_command_runtime;
GRANT SELECT,UPDATE,INSERT ON command_principal TO flooow_command_issuer;
GRANT SELECT,INSERT ON command_credential_revision,command_permission_grant TO flooow_command_issuer;
GRANT SELECT ON integration_organization,integration_connection TO flooow_command_issuer;

CREATE TABLE command_authority_operation (
    organization_id uuid NOT NULL,
    operation_id uuid NOT NULL,
    operation text NOT NULL CHECK (operation IN ('PRINCIPAL','INITIAL_CREDENTIAL','ROTATE_CREDENTIAL','GRANT','REVOKE')),
    principal_id uuid NOT NULL,
    credential_id uuid,
    credential_revision integer CHECK (credential_revision IS NULL OR credential_revision>0),
    grant_id uuid,
    grant_revision integer CHECK (grant_revision IS NULL OR grant_revision>0),
    permission text CHECK (permission IS NULL OR permission IN ('TRANSACTION_IDENTITY_DECISION_WRITE','TRANSACTION_IDENTITY_POLICY_ADMIN')),
    state text CHECK (state IS NULL OR state IN ('ENABLED','DISABLED')),
    intent_fingerprint char(64) NOT NULL CHECK (intent_fingerprint ~ '^[0-9a-f]{64}$'),
    receipt_fingerprint char(64) NOT NULL CHECK (receipt_fingerprint ~ '^[0-9a-f]{64}$'),
    correlation_id uuid NOT NULL,
    decided_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (organization_id,operation_id),
    FOREIGN KEY (organization_id,principal_id) REFERENCES command_principal,
    FOREIGN KEY (organization_id,credential_id,credential_revision) REFERENCES command_credential_revision,
    FOREIGN KEY (organization_id,grant_id) REFERENCES command_permission_grant,
    CHECK ((operation='PRINCIPAL' AND credential_id IS NULL AND credential_revision IS NULL
            AND grant_id IS NULL AND grant_revision IS NULL AND permission IS NULL AND state IS NULL)
       OR (operation IN ('INITIAL_CREDENTIAL','ROTATE_CREDENTIAL') AND credential_id IS NOT NULL AND credential_revision IS NOT NULL
            AND grant_id IS NULL AND grant_revision IS NULL AND permission IS NULL AND state IS NOT NULL AND state='ENABLED')
       OR (operation='GRANT' AND credential_id IS NULL AND credential_revision IS NULL
            AND grant_id IS NOT NULL AND grant_revision IS NOT NULL AND permission IS NOT NULL AND state IS NOT NULL AND state='ENABLED')
       OR (operation='REVOKE' AND credential_id IS NULL AND credential_revision IS NULL
            AND grant_id IS NOT NULL AND grant_revision IS NOT NULL AND permission IS NOT NULL AND state IS NOT NULL AND state='DISABLED'))
);
CREATE TRIGGER command_authority_operation_immutable BEFORE UPDATE OR DELETE ON command_authority_operation
    FOR EACH ROW EXECUTE FUNCTION command_authority_immutable();
GRANT SELECT,INSERT ON command_authority_operation TO flooow_command_issuer;
