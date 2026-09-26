-- V040 is approval governance only. It creates no command or transaction-identity authority.
DO $$ BEGIN
    CREATE ROLE flooow_approval_governance NOLOGIN NOINHERIT;
EXCEPTION WHEN duplicate_object THEN
    ALTER ROLE flooow_approval_governance NOLOGIN NOINHERIT;
END $$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
          FROM pg_catalog.pg_auth_members
         WHERE roleid = 'flooow_approval_governance'::regrole
            OR member = 'flooow_approval_governance'::regrole
    ) THEN
        RAISE EXCEPTION 'Preexisting approval-governance role membership is forbidden';
    END IF;
END $$;

CREATE TABLE s2a_signer_key_revision (
    organization_id uuid NOT NULL,
    signer_key_id uuid NOT NULL,
    revision integer NOT NULL,
    signer_subject_id uuid NOT NULL,
    algorithm_id text NOT NULL,
    subject_public_key_info_der bytea NOT NULL,
    signer_key_fingerprint char(64) NOT NULL,
    state text NOT NULL,
    valid_from timestamptz(6) NOT NULL,
    effective_at timestamptz(6) NOT NULL,
    supersedes_revision integer NULL,
    lineage_fingerprint char(64) NOT NULL,
    reason text NOT NULL,
    provenance text NOT NULL,
    correlation_id uuid NOT NULL,
    recorded_at timestamptz(6) NOT NULL DEFAULT transaction_timestamp(),
    PRIMARY KEY (organization_id, signer_key_id, revision),
    FOREIGN KEY (organization_id) REFERENCES integration_organization(organization_id),
    FOREIGN KEY (organization_id, signer_key_id, supersedes_revision)
        REFERENCES s2a_signer_key_revision(organization_id, signer_key_id, revision),
    UNIQUE (organization_id, signer_key_id, supersedes_revision),
    UNIQUE (organization_id, signer_key_id, revision, signer_key_fingerprint),
    CHECK (revision > 0),
    CHECK ((revision = 1 AND supersedes_revision IS NULL) OR
           (revision > 1 AND supersedes_revision = revision - 1)),
    CHECK (signer_key_id <> '00000000-0000-0000-0000-000000000000'::uuid),
    CHECK (signer_subject_id <> '00000000-0000-0000-0000-000000000000'::uuid),
    CHECK (correlation_id <> '00000000-0000-0000-0000-000000000000'::uuid),
    CHECK (algorithm_id = 'Ed25519'),
    CHECK (state IN ('ACTIVE', 'RETIRED', 'REVOKED', 'COMPROMISED')),
    CHECK (signer_key_fingerprint ~ '^[0-9a-f]{64}$'),
    CHECK (lineage_fingerprint ~ '^[0-9a-f]{64}$'),
    CHECK (octet_length(subject_public_key_info_der) = 44),
    CHECK (substring(subject_public_key_info_der FROM 1 FOR 12) = decode('302a300506032b6570032100', 'hex')),
    CHECK (signer_key_fingerprint::text = encode(sha256(subject_public_key_info_der), 'hex')),
    CHECK (octet_length(reason) BETWEEN 1 AND 512),
    CHECK (reason IS NFC NORMALIZED),
    CHECK (reason = btrim(reason) AND reason !~ '^[[:space:]]|[[:space:]]$' AND reason !~ '[[:cntrl:]]'),
    CHECK (octet_length(provenance) BETWEEN 1 AND 1024),
    CHECK (provenance IS NFC NORMALIZED),
    CHECK (provenance = btrim(provenance) AND provenance !~ '^[[:space:]]|[[:space:]]$' AND provenance !~ '[[:cntrl:]]')
);

CREATE TABLE s2a_signer_authority_revision (
    organization_id uuid NOT NULL,
    signer_authority_id uuid NOT NULL,
    revision integer NOT NULL,
    signer_subject_id uuid NOT NULL,
    signer_authorizing_institution_id uuid NOT NULL,
    signer_role text NOT NULL,
    signer_key_id uuid NOT NULL,
    signer_key_revision integer NOT NULL,
    signer_key_fingerprint char(64) NOT NULL,
    approval_action text NOT NULL,
    permission text NOT NULL,
    valid_from timestamptz(6) NOT NULL,
    valid_until timestamptz(6) NOT NULL,
    state text NOT NULL,
    supersedes_signer_authority_id uuid NULL,
    signer_authority_fingerprint char(64) NOT NULL,
    reason text NOT NULL,
    provenance text NOT NULL,
    approval_source_id uuid NOT NULL,
    correlation_id uuid NOT NULL,
    decided_at timestamptz(6) NOT NULL DEFAULT transaction_timestamp(),
    PRIMARY KEY (organization_id, signer_authority_id),
    UNIQUE (organization_id, signer_subject_id, signer_key_id, approval_action, permission, revision),
    UNIQUE (organization_id, supersedes_signer_authority_id),
    FOREIGN KEY (organization_id, supersedes_signer_authority_id)
        REFERENCES s2a_signer_authority_revision(organization_id, signer_authority_id),
    FOREIGN KEY (organization_id, signer_key_id, signer_key_revision, signer_key_fingerprint)
        REFERENCES s2a_signer_key_revision(organization_id, signer_key_id, revision, signer_key_fingerprint),
    CHECK ((revision = 1 AND supersedes_signer_authority_id IS NULL) OR
           (revision > 1 AND supersedes_signer_authority_id IS NOT NULL)),
    CHECK (signer_authority_id <> '00000000-0000-0000-0000-000000000000'::uuid),
    CHECK (signer_subject_id <> '00000000-0000-0000-0000-000000000000'::uuid),
    CHECK (signer_authorizing_institution_id <> '00000000-0000-0000-0000-000000000000'::uuid),
    CHECK (signer_key_id <> '00000000-0000-0000-0000-000000000000'::uuid),
    CHECK (approval_source_id <> '00000000-0000-0000-0000-000000000000'::uuid),
    CHECK (correlation_id <> '00000000-0000-0000-0000-000000000000'::uuid),
    CHECK (revision > 0 AND signer_key_revision > 0),
    CHECK (signer_role = 'S2A_FIELD_PROOF_APPROVER'),
    CHECK (approval_action = 'S2A_FIELD_PROOF_APPROVAL'),
    CHECK (permission = 'TRANSACTION_IDENTITY_DECISION_WRITE'),
    CHECK (state IN ('ENABLED', 'DISABLED')),
    CHECK (valid_from < valid_until),
    CHECK (signer_key_fingerprint ~ '^[0-9a-f]{64}$'),
    CHECK (signer_authority_fingerprint ~ '^[0-9a-f]{64}$'),
    CHECK (octet_length(reason) BETWEEN 1 AND 512),
    CHECK (reason IS NFC NORMALIZED),
    CHECK (reason = btrim(reason) AND reason !~ '^[[:space:]]|[[:space:]]$' AND reason !~ '[[:cntrl:]]'),
    CHECK (octet_length(provenance) BETWEEN 1 AND 1024),
    CHECK (provenance IS NFC NORMALIZED),
    CHECK (provenance = btrim(provenance) AND provenance !~ '^[[:space:]]|[[:space:]]$' AND provenance !~ '[[:cntrl:]]')
);

CREATE FUNCTION s2a_governance_frame(value bytea) RETURNS bytea
LANGUAGE sql IMMUTABLE STRICT PARALLEL SAFE
RETURN int4send(octet_length(value)) || value;

CREATE FUNCTION s2a_governance_text(value text) RETURNS bytea
LANGUAGE sql IMMUTABLE STRICT PARALLEL SAFE
RETURN public.s2a_governance_frame(convert_to(value, 'UTF8'));

CREATE FUNCTION s2a_governance_instant(value timestamptz) RETURNS bytea
LANGUAGE sql IMMUTABLE STRICT PARALLEL SAFE
RETURN public.s2a_governance_text(to_char(value AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'));

CREATE FUNCTION s2a_governance_nullable_integer(value integer) RETURNS bytea
LANGUAGE sql IMMUTABLE PARALLEL SAFE
RETURN CASE WHEN value IS NULL
    THEN public.s2a_governance_text('NULL') || public.s2a_governance_frame(''::bytea)
    ELSE public.s2a_governance_text('PRESENT') || public.s2a_governance_text(value::text)
END;

CREATE FUNCTION s2a_governance_nullable_text(value text) RETURNS bytea
LANGUAGE sql IMMUTABLE PARALLEL SAFE
RETURN CASE WHEN value IS NULL
    THEN public.s2a_governance_text('NULL') || public.s2a_governance_frame(''::bytea)
    ELSE public.s2a_governance_text('PRESENT') || public.s2a_governance_text(value)
END;

CREATE FUNCTION s2a_signer_key_lineage_fingerprint(
    organization_id uuid, signer_key_id uuid, revision integer, signer_subject_id uuid,
    algorithm_id text, subject_public_key_info_der bytea, signer_key_fingerprint text,
    key_state text, valid_from timestamptz, effective_at timestamptz,
    supersedes_revision integer, predecessor_lineage_fingerprint text
) RETURNS text
LANGUAGE sql IMMUTABLE PARALLEL SAFE
RETURN encode(sha256(
    public.s2a_governance_text('FLOOOW:S2A:SIGNER-KEY-LINEAGE:1') ||
    public.s2a_governance_text(organization_id::text) ||
    public.s2a_governance_text(signer_key_id::text) ||
    public.s2a_governance_text(revision::text) ||
    public.s2a_governance_text(signer_subject_id::text) ||
    public.s2a_governance_text(algorithm_id) ||
    public.s2a_governance_frame(subject_public_key_info_der) ||
    public.s2a_governance_text(signer_key_fingerprint) ||
    public.s2a_governance_text(key_state) ||
    public.s2a_governance_instant(valid_from) ||
    public.s2a_governance_instant(effective_at) ||
    public.s2a_governance_nullable_integer(supersedes_revision) ||
    public.s2a_governance_nullable_text(predecessor_lineage_fingerprint)
), 'hex');

CREATE FUNCTION s2a_signer_authority_fingerprint(
    organization_id uuid, signer_authority_id uuid, revision integer, signer_subject_id uuid,
    signer_authorizing_institution_id uuid, signer_role text, signer_key_id uuid,
    signer_key_revision integer, signer_key_fingerprint text, approval_action text,
    permission text, valid_from timestamptz, valid_until timestamptz, authority_state text,
    approval_source_id uuid, supersedes_signer_authority_id uuid,
    predecessor_signer_authority_fingerprint text
) RETURNS text
LANGUAGE sql IMMUTABLE PARALLEL SAFE
RETURN encode(sha256(
    public.s2a_governance_text('FLOOOW:S2A:SIGNER-AUTHORITY-LINEAGE:1') ||
    public.s2a_governance_text(organization_id::text) ||
    public.s2a_governance_text(signer_authority_id::text) ||
    public.s2a_governance_text(revision::text) ||
    public.s2a_governance_text(signer_subject_id::text) ||
    public.s2a_governance_text(signer_authorizing_institution_id::text) ||
    public.s2a_governance_text(signer_role) ||
    public.s2a_governance_text(signer_key_id::text) ||
    public.s2a_governance_text(signer_key_revision::text) ||
    public.s2a_governance_text(signer_key_fingerprint) ||
    public.s2a_governance_text(approval_action) ||
    public.s2a_governance_text(permission) ||
    public.s2a_governance_instant(valid_from) ||
    public.s2a_governance_instant(valid_until) ||
    public.s2a_governance_text(authority_state) ||
    public.s2a_governance_text(approval_source_id::text) ||
    public.s2a_governance_nullable_text(supersedes_signer_authority_id::text) ||
    public.s2a_governance_nullable_text(predecessor_signer_authority_fingerprint)
), 'hex');

CREATE FUNCTION s2a_governance_reject_mutation() RETURNS trigger
LANGUAGE plpgsql SECURITY INVOKER SET search_path=pg_catalog,pg_temp
AS $$ BEGIN
    RAISE EXCEPTION 'Approval-governance revisions are immutable' USING ERRCODE='23514';
END $$;

CREATE FUNCTION s2a_signer_key_revision_validate() RETURNS trigger
LANGUAGE plpgsql SECURITY INVOKER SET search_path=pg_catalog,pg_temp
AS $$
DECLARE
    active boolean;
    current_count integer;
    predecessor public.s2a_signer_key_revision%ROWTYPE;
    expected text;
BEGIN
    SELECT status = 'ACTIVE' INTO active
      FROM public.integration_organization
     WHERE organization_id = NEW.organization_id FOR SHARE;
    IF NOT coalesce(active, false) THEN
        RAISE EXCEPTION 'Approval governance unavailable' USING ERRCODE='P0013';
    END IF;
    PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(
        's2a-governance/signer-key/1:' || NEW.organization_id || ':' || NEW.signer_key_id, 0));

    SELECT count(*) INTO current_count
      FROM public.s2a_signer_key_revision k
     WHERE k.organization_id=NEW.organization_id AND k.signer_key_id=NEW.signer_key_id
       AND NOT EXISTS (SELECT 1 FROM public.s2a_signer_key_revision s
                        WHERE s.organization_id=k.organization_id AND s.signer_key_id=k.signer_key_id
                          AND s.supersedes_revision=k.revision);
    IF current_count > 1 THEN
        RAISE EXCEPTION 'Ambiguous signer-key lineage' USING ERRCODE='P0014';
    END IF;

    IF NEW.revision = 1 THEN
        IF current_count <> 0 OR NEW.supersedes_revision IS NOT NULL THEN
            RAISE EXCEPTION 'Signer-key lineage conflict' USING ERRCODE='P0014';
        END IF;
        expected := public.s2a_signer_key_lineage_fingerprint(
            NEW.organization_id,NEW.signer_key_id,NEW.revision,NEW.signer_subject_id,
            NEW.algorithm_id,NEW.subject_public_key_info_der,NEW.signer_key_fingerprint::text,
            NEW.state,NEW.valid_from,NEW.effective_at,NULL,NULL);
    ELSE
        IF current_count <> 1 THEN
            RAISE EXCEPTION 'Signer-key predecessor unavailable' USING ERRCODE='P0014';
        END IF;
        SELECT k.* INTO predecessor FROM public.s2a_signer_key_revision k
         WHERE k.organization_id=NEW.organization_id AND k.signer_key_id=NEW.signer_key_id
           AND NOT EXISTS (SELECT 1 FROM public.s2a_signer_key_revision s
                            WHERE s.organization_id=k.organization_id AND s.signer_key_id=k.signer_key_id
                              AND s.supersedes_revision=k.revision);
        IF NEW.supersedes_revision IS DISTINCT FROM predecessor.revision OR
           NEW.revision <> predecessor.revision + 1 OR
           NEW.signer_subject_id <> predecessor.signer_subject_id OR
           NEW.algorithm_id <> predecessor.algorithm_id OR
           NEW.subject_public_key_info_der <> predecessor.subject_public_key_info_der OR
           NEW.signer_key_fingerprint <> predecessor.signer_key_fingerprint OR
           NEW.valid_from <> predecessor.valid_from OR
           (predecessor.state <> 'ACTIVE' AND NEW.state = 'ACTIVE') THEN
            RAISE EXCEPTION 'Signer-key predecessor or successor conflict' USING ERRCODE='P0014';
        END IF;
        expected := public.s2a_signer_key_lineage_fingerprint(
            NEW.organization_id,NEW.signer_key_id,NEW.revision,NEW.signer_subject_id,
            NEW.algorithm_id,NEW.subject_public_key_info_der,NEW.signer_key_fingerprint::text,
            NEW.state,NEW.valid_from,NEW.effective_at,NEW.supersedes_revision,predecessor.lineage_fingerprint::text);
    END IF;
    IF NEW.lineage_fingerprint::text <> expected THEN
        RAISE EXCEPTION 'Signer-key lineage fingerprint mismatch' USING ERRCODE='23514';
    END IF;
    NEW.recorded_at := transaction_timestamp();
    RETURN NEW;
END $$;

CREATE FUNCTION s2a_signer_authority_revision_validate() RETURNS trigger
LANGUAGE plpgsql SECURITY INVOKER SET search_path=pg_catalog,pg_temp
AS $$
DECLARE
    active boolean;
    key_leaf_count integer;
    current_count integer;
    predecessor public.s2a_signer_authority_revision%ROWTYPE;
    expected text;
BEGIN
    SELECT status = 'ACTIVE' INTO active
      FROM public.integration_organization
     WHERE organization_id = NEW.organization_id FOR SHARE;
    IF NOT coalesce(active, false) THEN
        RAISE EXCEPTION 'Approval governance unavailable' USING ERRCODE='P0013';
    END IF;
    PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(
        's2a-governance/signer-key/1:' || NEW.organization_id || ':' || NEW.signer_key_id, 0));
    PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(
        's2a-governance/signer-authority-scope/1:' || NEW.organization_id || ':' || NEW.signer_subject_id || ':' || NEW.signer_key_id || ':S2A_FIELD_PROOF_APPROVAL:TRANSACTION_IDENTITY_DECISION_WRITE', 0));

    SELECT count(*) INTO key_leaf_count
      FROM public.s2a_signer_key_revision k
     WHERE k.organization_id=NEW.organization_id AND k.signer_key_id=NEW.signer_key_id
       AND NOT EXISTS (SELECT 1 FROM public.s2a_signer_key_revision s
                        WHERE s.organization_id=k.organization_id AND s.signer_key_id=k.signer_key_id
                          AND s.supersedes_revision=k.revision);
    IF key_leaf_count <> 1 THEN
        RAISE EXCEPTION 'Signer-key lineage unavailable or ambiguous' USING ERRCODE='P0014';
    END IF;

    SELECT count(*) INTO current_count
      FROM public.s2a_signer_authority_revision a
     WHERE a.organization_id=NEW.organization_id AND a.signer_subject_id=NEW.signer_subject_id
       AND a.signer_key_id=NEW.signer_key_id AND a.approval_action=NEW.approval_action
       AND a.permission=NEW.permission
       AND NOT EXISTS (SELECT 1 FROM public.s2a_signer_authority_revision s
                        WHERE s.organization_id=a.organization_id
                          AND s.supersedes_signer_authority_id=a.signer_authority_id);
    IF current_count > 1 THEN
        RAISE EXCEPTION 'Ambiguous signer-authority lineage' USING ERRCODE='P0014';
    END IF;

    IF NEW.revision = 1 THEN
        IF current_count <> 0 OR NEW.supersedes_signer_authority_id IS NOT NULL THEN
            RAISE EXCEPTION 'Signer-authority lineage conflict' USING ERRCODE='P0014';
        END IF;
        expected := public.s2a_signer_authority_fingerprint(
            NEW.organization_id,NEW.signer_authority_id,NEW.revision,NEW.signer_subject_id,
            NEW.signer_authorizing_institution_id,NEW.signer_role,NEW.signer_key_id,
            NEW.signer_key_revision,NEW.signer_key_fingerprint::text,NEW.approval_action,
            NEW.permission,NEW.valid_from,NEW.valid_until,NEW.state,NEW.approval_source_id,NULL,NULL);
    ELSE
        IF current_count <> 1 THEN
            RAISE EXCEPTION 'Signer-authority predecessor unavailable' USING ERRCODE='P0014';
        END IF;
        SELECT a.* INTO predecessor FROM public.s2a_signer_authority_revision a
         WHERE a.organization_id=NEW.organization_id AND a.signer_subject_id=NEW.signer_subject_id
           AND a.signer_key_id=NEW.signer_key_id AND a.approval_action=NEW.approval_action
           AND a.permission=NEW.permission
           AND NOT EXISTS (SELECT 1 FROM public.s2a_signer_authority_revision s
                            WHERE s.organization_id=a.organization_id
                              AND s.supersedes_signer_authority_id=a.signer_authority_id);
        IF NEW.supersedes_signer_authority_id IS DISTINCT FROM predecessor.signer_authority_id OR
           NEW.revision <> predecessor.revision + 1 OR
           NEW.signer_authority_id = predecessor.signer_authority_id OR
           NEW.signer_subject_id <> predecessor.signer_subject_id OR
           NEW.signer_authorizing_institution_id <> predecessor.signer_authorizing_institution_id OR
           NEW.signer_role <> predecessor.signer_role OR
           NEW.signer_key_id <> predecessor.signer_key_id OR
           NEW.signer_key_revision <> predecessor.signer_key_revision OR
           NEW.signer_key_fingerprint <> predecessor.signer_key_fingerprint OR
           NEW.approval_action <> predecessor.approval_action OR
           NEW.permission <> predecessor.permission OR
           NEW.valid_from <> predecessor.valid_from OR NEW.valid_until <> predecessor.valid_until OR
           NEW.approval_source_id <> predecessor.approval_source_id THEN
            RAISE EXCEPTION 'Signer-authority predecessor or successor conflict' USING ERRCODE='P0014';
        END IF;
        expected := public.s2a_signer_authority_fingerprint(
            NEW.organization_id,NEW.signer_authority_id,NEW.revision,NEW.signer_subject_id,
            NEW.signer_authorizing_institution_id,NEW.signer_role,NEW.signer_key_id,
            NEW.signer_key_revision,NEW.signer_key_fingerprint::text,NEW.approval_action,
            NEW.permission,NEW.valid_from,NEW.valid_until,NEW.state,NEW.approval_source_id,
            NEW.supersedes_signer_authority_id,predecessor.signer_authority_fingerprint::text);
    END IF;
    IF NEW.signer_authority_fingerprint::text <> expected THEN
        RAISE EXCEPTION 'Signer-authority fingerprint mismatch' USING ERRCODE='23514';
    END IF;
    NEW.decided_at := transaction_timestamp();
    RETURN NEW;
END $$;

CREATE TRIGGER s2a_signer_key_revision_validate_before_insert
BEFORE INSERT ON s2a_signer_key_revision FOR EACH ROW EXECUTE FUNCTION s2a_signer_key_revision_validate();
CREATE TRIGGER s2a_signer_key_revision_immutable
BEFORE UPDATE OR DELETE ON s2a_signer_key_revision FOR EACH ROW EXECUTE FUNCTION s2a_governance_reject_mutation();
CREATE TRIGGER s2a_signer_authority_revision_validate_before_insert
BEFORE INSERT ON s2a_signer_authority_revision FOR EACH ROW EXECUTE FUNCTION s2a_signer_authority_revision_validate();
CREATE TRIGGER s2a_signer_authority_revision_immutable
BEFORE UPDATE OR DELETE ON s2a_signer_authority_revision FOR EACH ROW EXECUTE FUNCTION s2a_governance_reject_mutation();

CREATE FUNCTION s2a_append_signer_key_revision(
    p_organization_id uuid, p_signer_key_id uuid, p_revision integer, p_signer_subject_id uuid,
    p_algorithm_id text, p_subject_public_key_info_der bytea, p_signer_key_fingerprint text,
    p_state text, p_valid_from timestamptz, p_effective_at timestamptz,
    p_supersedes_revision integer, p_lineage_fingerprint text, p_reason text,
    p_provenance text, p_correlation_id uuid
) RETURNS TABLE(outcome text, result_organization_id uuid, result_signer_key_id uuid,
                result_revision integer, result_fingerprint text, result_recorded_at timestamptz)
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,pg_temp
AS $$
DECLARE existing public.s2a_signer_key_revision%ROWTYPE; active boolean;
BEGIN
    SELECT status='ACTIVE' INTO active FROM public.integration_organization
     WHERE organization_id=p_organization_id FOR SHARE;
    IF NOT coalesce(active,false) THEN RAISE EXCEPTION 'Approval governance unavailable' USING ERRCODE='P0013'; END IF;
    PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(
        's2a-governance/signer-key/1:' || p_organization_id || ':' || p_signer_key_id,0));
    SELECT * INTO existing FROM public.s2a_signer_key_revision
     WHERE organization_id=p_organization_id AND signer_key_id=p_signer_key_id AND revision=p_revision;
    IF FOUND THEN
        IF existing.signer_subject_id=p_signer_subject_id AND existing.algorithm_id=p_algorithm_id AND
           existing.subject_public_key_info_der=p_subject_public_key_info_der AND
           existing.signer_key_fingerprint::text=p_signer_key_fingerprint AND existing.state=p_state AND
           existing.valid_from=p_valid_from AND existing.effective_at=p_effective_at AND
           existing.supersedes_revision IS NOT DISTINCT FROM p_supersedes_revision AND
           existing.lineage_fingerprint::text=p_lineage_fingerprint AND existing.reason=p_reason AND
           existing.provenance=p_provenance AND existing.correlation_id=p_correlation_id THEN
            RETURN QUERY SELECT 'ALREADY_APPLIED',existing.organization_id,existing.signer_key_id,
                existing.revision,existing.lineage_fingerprint::text,existing.recorded_at;
            RETURN;
        END IF;
        RAISE EXCEPTION 'Signer-key row identity conflict' USING ERRCODE='P0014';
    END IF;
    INSERT INTO public.s2a_signer_key_revision(
        organization_id,signer_key_id,revision,signer_subject_id,algorithm_id,subject_public_key_info_der,
        signer_key_fingerprint,state,valid_from,effective_at,supersedes_revision,lineage_fingerprint,
        reason,provenance,correlation_id)
    VALUES(p_organization_id,p_signer_key_id,p_revision,p_signer_subject_id,p_algorithm_id,
        p_subject_public_key_info_der,p_signer_key_fingerprint,p_state,p_valid_from,p_effective_at,
        p_supersedes_revision,p_lineage_fingerprint,p_reason,p_provenance,p_correlation_id)
    RETURNING * INTO existing;
    RETURN QUERY SELECT 'APPLIED',existing.organization_id,existing.signer_key_id,
        existing.revision,existing.lineage_fingerprint::text,existing.recorded_at;
END $$;

CREATE FUNCTION s2a_append_signer_authority_revision(
    p_organization_id uuid, p_signer_authority_id uuid, p_revision integer, p_signer_subject_id uuid,
    p_signer_authorizing_institution_id uuid, p_signer_role text, p_signer_key_id uuid,
    p_signer_key_revision integer, p_signer_key_fingerprint text, p_approval_action text,
    p_permission text, p_valid_from timestamptz, p_valid_until timestamptz, p_state text,
    p_supersedes_signer_authority_id uuid, p_signer_authority_fingerprint text, p_reason text,
    p_provenance text, p_approval_source_id uuid, p_correlation_id uuid
) RETURNS TABLE(outcome text, result_organization_id uuid, result_signer_authority_id uuid,
                result_revision integer, result_fingerprint text, result_decided_at timestamptz)
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,pg_temp
AS $$
DECLARE existing public.s2a_signer_authority_revision%ROWTYPE; active boolean;
BEGIN
    SELECT status='ACTIVE' INTO active FROM public.integration_organization
     WHERE organization_id=p_organization_id FOR SHARE;
    IF NOT coalesce(active,false) THEN RAISE EXCEPTION 'Approval governance unavailable' USING ERRCODE='P0013'; END IF;
    PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(
        's2a-governance/signer-key/1:' || p_organization_id || ':' || p_signer_key_id,0));
    PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(
        's2a-governance/signer-authority-scope/1:' || p_organization_id || ':' || p_signer_subject_id || ':' || p_signer_key_id || ':S2A_FIELD_PROOF_APPROVAL:TRANSACTION_IDENTITY_DECISION_WRITE',0));
    SELECT * INTO existing FROM public.s2a_signer_authority_revision
     WHERE organization_id=p_organization_id AND signer_authority_id=p_signer_authority_id;
    IF FOUND THEN
        IF existing.revision=p_revision AND existing.signer_subject_id=p_signer_subject_id AND
           existing.signer_authorizing_institution_id=p_signer_authorizing_institution_id AND
           existing.signer_role=p_signer_role AND existing.signer_key_id=p_signer_key_id AND
           existing.signer_key_revision=p_signer_key_revision AND existing.signer_key_fingerprint::text=p_signer_key_fingerprint AND
           existing.approval_action=p_approval_action AND existing.permission=p_permission AND
           existing.valid_from=p_valid_from AND existing.valid_until=p_valid_until AND existing.state=p_state AND
           existing.supersedes_signer_authority_id IS NOT DISTINCT FROM p_supersedes_signer_authority_id AND
           existing.signer_authority_fingerprint::text=p_signer_authority_fingerprint AND
           existing.reason=p_reason AND existing.provenance=p_provenance AND
           existing.approval_source_id=p_approval_source_id AND existing.correlation_id=p_correlation_id THEN
            RETURN QUERY SELECT 'ALREADY_APPLIED',existing.organization_id,existing.signer_authority_id,
                existing.revision,existing.signer_authority_fingerprint::text,existing.decided_at;
            RETURN;
        END IF;
        RAISE EXCEPTION 'Signer-authority row identity conflict' USING ERRCODE='P0014';
    END IF;
    INSERT INTO public.s2a_signer_authority_revision(
        organization_id,signer_authority_id,revision,signer_subject_id,signer_authorizing_institution_id,
        signer_role,signer_key_id,signer_key_revision,signer_key_fingerprint,approval_action,permission,
        valid_from,valid_until,state,supersedes_signer_authority_id,signer_authority_fingerprint,
        reason,provenance,approval_source_id,correlation_id)
    VALUES(p_organization_id,p_signer_authority_id,p_revision,p_signer_subject_id,p_signer_authorizing_institution_id,
        p_signer_role,p_signer_key_id,p_signer_key_revision,p_signer_key_fingerprint,p_approval_action,p_permission,
        p_valid_from,p_valid_until,p_state,p_supersedes_signer_authority_id,p_signer_authority_fingerprint,
        p_reason,p_provenance,p_approval_source_id,p_correlation_id)
    RETURNING * INTO existing;
    RETURN QUERY SELECT 'APPLIED',existing.organization_id,existing.signer_authority_id,
        existing.revision,existing.signer_authority_fingerprint::text,existing.decided_at;
END $$;

REVOKE ALL ON s2a_signer_key_revision,s2a_signer_authority_revision FROM PUBLIC;
REVOKE ALL ON s2a_signer_key_revision,s2a_signer_authority_revision FROM flooow_approval_governance;
REVOKE ALL ON s2a_signer_key_revision,s2a_signer_authority_revision FROM flooow_command_runtime;
REVOKE ALL ON s2a_signer_key_revision,s2a_signer_authority_revision FROM flooow_command_issuer;

REVOKE EXECUTE ON FUNCTION s2a_governance_frame(bytea) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION s2a_governance_text(text) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION s2a_governance_instant(timestamptz) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION s2a_governance_nullable_integer(integer) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION s2a_governance_nullable_text(text) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION s2a_signer_key_lineage_fingerprint(uuid,uuid,integer,uuid,text,bytea,text,text,timestamptz,timestamptz,integer,text) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION s2a_signer_authority_fingerprint(uuid,uuid,integer,uuid,uuid,text,uuid,integer,text,text,text,timestamptz,timestamptz,text,uuid,uuid,text) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION s2a_governance_reject_mutation() FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION s2a_signer_key_revision_validate() FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION s2a_signer_authority_revision_validate() FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION s2a_append_signer_key_revision(uuid,uuid,integer,uuid,text,bytea,text,text,timestamptz,timestamptz,integer,text,text,text,uuid) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION s2a_append_signer_authority_revision(uuid,uuid,integer,uuid,uuid,text,uuid,integer,text,text,text,timestamptz,timestamptz,text,uuid,text,text,text,uuid,uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION s2a_append_signer_key_revision(uuid,uuid,integer,uuid,text,bytea,text,text,timestamptz,timestamptz,integer,text,text,text,uuid)
    TO flooow_approval_governance;
GRANT EXECUTE ON FUNCTION s2a_append_signer_authority_revision(uuid,uuid,integer,uuid,uuid,text,uuid,integer,text,text,text,timestamptz,timestamptz,text,uuid,text,text,text,uuid,uuid)
    TO flooow_approval_governance;
