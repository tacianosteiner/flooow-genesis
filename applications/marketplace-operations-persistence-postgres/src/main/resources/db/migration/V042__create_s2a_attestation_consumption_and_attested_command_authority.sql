-- V042: immutable accepted-attestation consumption and attested authority boundary.
-- No historic row is repaired or rewritten by this migration.

DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM public.command_authority_operation o
    WHERE (o.operation IN ('INITIAL_CREDENTIAL','ROTATE_CREDENTIAL') AND NOT EXISTS (
      SELECT 1 FROM public.command_credential_revision c
      WHERE c.organization_id=o.organization_id AND c.credential_id=o.credential_id
        AND c.revision=o.credential_revision AND c.principal_id=o.principal_id AND c.state=o.state
    )) OR (o.operation IN ('GRANT','REVOKE') AND NOT EXISTS (
      SELECT 1 FROM public.command_permission_grant g
      WHERE g.organization_id=o.organization_id AND g.grant_id=o.grant_id
        AND g.revision=o.grant_revision AND g.principal_id=o.principal_id
        AND g.permission=o.permission AND g.state=o.state
    ))
  ) THEN
    RAISE EXCEPTION 'V042 historical operation integrity preflight failed'
      USING ERRCODE='P0018', DETAIL='HISTORY_INTEGRITY_FAILURE';
  END IF;

  IF EXISTS (
    WITH RECURSIVE protected(role_name) AS (
      VALUES ('flooow_approval_governance'::name), ('flooow_attestation_verifier'::name),
             ('flooow_command_issuer'::name), ('flooow_command_runtime'::name)
    ), closure(member, roleid) AS (
      SELECT m.member,m.roleid FROM pg_catalog.pg_auth_members m
      UNION
      SELECT c.member,m.roleid FROM closure c JOIN pg_catalog.pg_auth_members m ON m.member=c.roleid
    )
    SELECT 1 FROM closure c
    JOIN pg_catalog.pg_roles a ON a.oid=c.member
    JOIN pg_catalog.pg_roles b ON b.oid=c.roleid
    WHERE a.rolname IN (SELECT role_name FROM protected)
      AND b.rolname IN (SELECT role_name FROM protected)
      AND a.rolname<>b.rolname
  ) THEN
    RAISE EXCEPTION 'V042 protected role graph contamination'
      USING ERRCODE='P0018', DETAIL='HISTORY_INTEGRITY_FAILURE';
  END IF;
END $$;

CREATE OR REPLACE FUNCTION public.command_principal_scope() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM public.integration_connection WHERE organization_id=NEW.organization_id
        AND connection_id=NEW.mercado_livre_connection_id AND provider_key='br.com.mercadolivre')
        OR NOT EXISTS (SELECT 1 FROM public.integration_connection WHERE organization_id=NEW.organization_id
        AND connection_id=NEW.omie_connection_id AND provider_key='omie') THEN
        RAISE EXCEPTION 'Invalid command principal provider scope' USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION public.command_credential_lineage() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE previous public.command_credential_revision;
BEGIN
    PERFORM 1 FROM public.command_principal WHERE organization_id=NEW.organization_id
        AND principal_id=NEW.principal_id FOR UPDATE;
    IF NEW.revision > 1 THEN
        SELECT * INTO previous FROM public.command_credential_revision
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

CREATE OR REPLACE FUNCTION public.command_grant_lineage() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE previous public.command_permission_grant;
BEGIN
    PERFORM 1 FROM public.command_principal WHERE organization_id=NEW.organization_id
        AND principal_id=NEW.principal_id FOR UPDATE;
    IF NEW.revision > 1 THEN
        SELECT * INTO previous FROM public.command_permission_grant
            WHERE organization_id=NEW.organization_id AND grant_id=NEW.supersedes_grant_id;
        IF NOT FOUND OR previous.principal_id<>NEW.principal_id
            OR previous.permission<>NEW.permission OR previous.revision<>NEW.revision-1
            OR EXISTS (SELECT 1 FROM public.command_permission_grant
                WHERE organization_id=NEW.organization_id AND supersedes_grant_id=previous.grant_id) THEN
            RAISE EXCEPTION 'Invalid command grant lineage' USING ERRCODE = '23514';
        END IF;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TABLE public.s2a_attestation_consumption (
  organization_id uuid NOT NULL,
  manifest_id uuid NOT NULL,
  manifest_digest char(64) NOT NULL CHECK (manifest_digest ~ '^[0-9a-f]{64}$'),
  principal_id uuid NOT NULL,
  correlation_id uuid NOT NULL,
  consumed_at timestamptz(6) NOT NULL,
  PRIMARY KEY (organization_id,manifest_id),
  UNIQUE (organization_id,manifest_id,principal_id),
  FOREIGN KEY (organization_id,manifest_id) REFERENCES public.s2a_accepted_attestation(organization_id,manifest_id),
  FOREIGN KEY (organization_id,principal_id) REFERENCES public.command_principal(organization_id,principal_id)
);

CREATE FUNCTION public.s2a_v042_reject_consumption_mutation() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$
BEGIN RAISE EXCEPTION 'S2A consumption is immutable' USING ERRCODE='23514'; END $$;
CREATE TRIGGER s2a_attestation_consumption_immutable BEFORE UPDATE OR DELETE ON public.s2a_attestation_consumption
FOR EACH ROW EXECUTE FUNCTION public.s2a_v042_reject_consumption_mutation();

ALTER TABLE public.command_credential_revision ADD CONSTRAINT command_credential_revision_v042_operation_target_key
  UNIQUE (organization_id,credential_id,revision,principal_id,state);
ALTER TABLE public.command_permission_grant ADD CONSTRAINT command_permission_grant_v042_operation_target_key
  UNIQUE (organization_id,grant_id,revision,principal_id,permission,state);
ALTER TABLE public.command_authority_operation ADD COLUMN attestation_manifest_id uuid;
ALTER TABLE public.command_authority_operation ADD CONSTRAINT command_authority_operation_v042_attestation_kind_check
  CHECK (attestation_manifest_id IS NULL OR operation IN ('PRINCIPAL','INITIAL_CREDENTIAL','GRANT'));
ALTER TABLE public.command_authority_operation ADD CONSTRAINT command_authority_operation_v042_consumption_fk
  FOREIGN KEY (organization_id,attestation_manifest_id,principal_id)
  REFERENCES public.s2a_attestation_consumption(organization_id,manifest_id,principal_id);
ALTER TABLE public.command_authority_operation ADD CONSTRAINT command_authority_operation_v042_credential_target_fk
  FOREIGN KEY (organization_id,credential_id,credential_revision,principal_id,state)
  REFERENCES public.command_credential_revision(organization_id,credential_id,revision,principal_id,state);
ALTER TABLE public.command_authority_operation ADD CONSTRAINT command_authority_operation_v042_grant_target_fk
  FOREIGN KEY (organization_id,grant_id,grant_revision,principal_id,permission,state)
  REFERENCES public.command_permission_grant(organization_id,grant_id,revision,principal_id,permission,state);
CREATE UNIQUE INDEX command_authority_operation_v042_manifest_kind_key ON public.command_authority_operation
  (organization_id,attestation_manifest_id,operation)
  WHERE attestation_manifest_id IS NOT NULL AND operation IN ('PRINCIPAL','INITIAL_CREDENTIAL','GRANT');
CREATE UNIQUE INDEX command_authority_operation_v042_grant_receipt_key ON public.command_authority_operation
  (organization_id,grant_id,grant_revision)
  WHERE attestation_manifest_id IS NOT NULL AND operation='GRANT';

CREATE FUNCTION public.s2a_v042_frame(v bytea) RETURNS bytea LANGUAGE sql IMMUTABLE STRICT
SET search_path=pg_catalog,pg_temp AS $$ SELECT convert_to(octet_length(v)::text || ':','UTF8') || v $$;
CREATE FUNCTION public.s2a_v042_text(v text) RETURNS bytea LANGUAGE sql IMMUTABLE STRICT
SET search_path=pg_catalog,pg_temp AS $$ SELECT public.s2a_v042_frame(convert_to(v,'UTF8')) $$;
CREATE FUNCTION public.s2a_v042_instant(v timestamptz) RETURNS bytea LANGUAGE sql IMMUTABLE STRICT
SET search_path=pg_catalog,pg_temp AS $$ SELECT public.s2a_v042_text(to_char(v AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US') || 'Z') $$;

CREATE FUNCTION public.s2a_v042_authority_intent(
  p_kind text,p_operation_id uuid,p_organization_id uuid,p_principal_id uuid,
  p_mercado_livre_connection_id uuid,p_omie_connection_id uuid,p_credential_id uuid,
  p_secret_verifier bytea,p_grant_id uuid,p_reason text,p_provenance text,p_correlation_id uuid,
  p_manifest_id uuid,p_accepted_proof_fingerprint text,p_manifest_digest text
) RETURNS text LANGUAGE plpgsql IMMUTABLE SET search_path=pg_catalog,pg_temp AS $$
DECLARE b bytea:=public.s2a_v042_text('controlled-command-authority/2');
BEGIN
  IF p_kind='PRINCIPAL' THEN
    b:=b||public.s2a_v042_text('principal')||public.s2a_v042_text(p_operation_id::text)||public.s2a_v042_text(p_organization_id::text)||public.s2a_v042_text(p_principal_id::text)||public.s2a_v042_text(p_mercado_livre_connection_id::text)||public.s2a_v042_text(p_omie_connection_id::text);
  ELSIF p_kind='INITIAL_CREDENTIAL' THEN
    b:=b||public.s2a_v042_text('initial-credential')||public.s2a_v042_text(p_operation_id::text)||public.s2a_v042_text(p_organization_id::text)||public.s2a_v042_text(p_principal_id::text)||public.s2a_v042_text(p_credential_id::text)||public.s2a_v042_text(encode(p_secret_verifier,'hex'));
  ELSIF p_kind='GRANT' THEN
    b:=b||public.s2a_v042_text('grant')||public.s2a_v042_text(p_operation_id::text)||public.s2a_v042_text(p_organization_id::text)||public.s2a_v042_text(p_principal_id::text)||public.s2a_v042_text(p_grant_id::text)||public.s2a_v042_text('TRANSACTION_IDENTITY_DECISION_WRITE');
  ELSE RAISE EXCEPTION 'Invalid V042 operation' USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE'; END IF;
  RETURN encode(sha256(b||public.s2a_v042_text(p_reason)||public.s2a_v042_text(p_provenance)||public.s2a_v042_text(p_correlation_id::text)||public.s2a_v042_text(p_manifest_id::text)||public.s2a_v042_text(p_accepted_proof_fingerprint)||public.s2a_v042_text(p_manifest_digest)),'hex');
END $$;

CREATE FUNCTION public.s2a_v042_authority_receipt(
  p_intent_fingerprint text,p_operation text,p_principal_id uuid,p_credential_id uuid,p_credential_revision integer,
  p_grant_id uuid,p_grant_revision integer,p_permission text,p_state text
) RETURNS text LANGUAGE sql IMMUTABLE SET search_path=pg_catalog,pg_temp AS $$
 SELECT encode(sha256(public.s2a_v042_text('controlled-command-authority-receipt/1')||public.s2a_v042_text(p_intent_fingerprint)||public.s2a_v042_text(p_operation)||public.s2a_v042_text(p_principal_id::text)||public.s2a_v042_text(coalesce(p_credential_id::text,''))||public.s2a_v042_text(coalesce(p_credential_revision::text,''))||public.s2a_v042_text(coalesce(p_grant_id::text,''))||public.s2a_v042_text(coalesce(p_grant_revision::text,''))||public.s2a_v042_text(coalesce(p_permission,''))||public.s2a_v042_text(coalesce(p_state,''))),'hex') $$;

CREATE FUNCTION public.s2a_v042_revalidate_snapshot(
 p_organization_id uuid,p_manifest_id uuid,p_schema_version integer,p_claim_manifest_id uuid,p_claim_organization_id uuid,p_mercado_livre_connection_id uuid,p_omie_connection_id uuid,p_source_order_reference text,p_integration_reference text,p_marketplace_order_id uuid,p_permission text,p_accountable_operator uuid,p_approval_source uuid,p_approval_window_start timestamptz,p_approval_window_end timestamptz,p_revocation_owner uuid,p_credential_custodian uuid,p_credential_delivery_method text,p_credential_rotation_owner uuid,p_immediate_revocation_policy text,p_reason text,p_provenance text,p_correlation_id uuid,p_evidence_binding_fingerprint text,
 p_expected_artifact_version integer,p_expected_canonicalization_version integer,p_expected_canonical_manifest_bytes bytea,p_expected_manifest_digest text,p_expected_signature_preimage_bytes bytea,p_expected_algorithm_id text,p_expected_signer_subject_id uuid,p_expected_signer_key_id uuid,p_expected_signer_key_revision integer,p_expected_signer_key_fingerprint text,p_expected_signer_key_lineage_fingerprint text,p_expected_subject_public_key_info_der bytea,p_expected_signature_bytes bytea,p_expected_signer_authority_id uuid,p_expected_signer_authority_revision integer,p_expected_signer_authority_fingerprint text,p_expected_verified_at timestamptz,p_expected_accepted_proof_fingerprint text,p_expected_evidence_binding_fingerprint text
) RETURNS TABLE(result_artifact_version integer,result_schema_version integer,result_canonicalization_version integer,result_canonical_manifest_bytes bytea,result_manifest_digest text,result_signature_preimage_bytes bytea,result_algorithm_id text,result_signer_subject_id uuid,result_signer_key_id uuid,result_signer_key_revision integer,result_signer_key_fingerprint text,result_signer_key_lineage_fingerprint text,result_subject_public_key_info_der bytea,result_signature_bytes bytea,result_signer_authority_id uuid,result_signer_authority_revision integer,result_signer_authority_fingerprint text,result_verified_at timestamptz,result_accepted_proof_fingerprint text,result_signed_evidence_binding_fingerprint text)
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$
DECLARE a public.s2a_accepted_attestation%ROWTYPE; k public.s2a_signer_key_revision%ROWTYPE; au public.s2a_signer_authority_revision%ROWTYPE; m bytea; d text; pre bytea; proof text;
BEGIN
 IF p_claim_organization_id<>p_organization_id OR p_claim_manifest_id<>p_manifest_id THEN RAISE EXCEPTION 'Claim identity mismatch' USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE'; END IF;
 SELECT * INTO a FROM public.s2a_accepted_attestation WHERE organization_id=p_organization_id AND manifest_id=p_manifest_id;
 IF NOT FOUND THEN RAISE EXCEPTION 'Accepted artifact unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE'; END IF;
 m:=public.s2a_v041_manifest_bytes(p_schema_version,p_claim_manifest_id,p_claim_organization_id,p_mercado_livre_connection_id,p_omie_connection_id,p_source_order_reference,p_integration_reference,p_marketplace_order_id,p_permission,p_accountable_operator,p_approval_source,p_approval_window_start,p_approval_window_end,p_revocation_owner,p_credential_custodian,p_credential_delivery_method,p_credential_rotation_owner,p_immediate_revocation_policy,p_reason,p_provenance,p_correlation_id,p_evidence_binding_fingerprint);
 d:=encode(sha256(m),'hex');
 IF m<>a.canonical_manifest_bytes OR d<>a.manifest_digest THEN RAISE EXCEPTION 'Retained manifest integrity failure' USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE'; END IF;
 pre:=public.s2a_v041_signature_preimage(a.algorithm_id,a.signer_key_id,a.signer_key_fingerprint,d);
 IF pre<>a.canonical_signature_preimage_bytes THEN RAISE EXCEPTION 'Retained preimage integrity failure' USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE'; END IF;
 SELECT * INTO k FROM public.s2a_signer_key_revision WHERE organization_id=a.organization_id AND signer_key_id=a.signer_key_id AND revision=a.signer_key_revision;
 IF NOT FOUND OR k.signer_key_fingerprint<>a.signer_key_fingerprint OR k.lineage_fingerprint<>a.signer_key_lineage_fingerprint OR k.subject_public_key_info_der<>a.subject_public_key_info_der OR k.algorithm_id<>a.algorithm_id OR k.signer_key_fingerprint<>encode(sha256(k.subject_public_key_info_der),'hex') OR k.lineage_fingerprint<>public.s2a_signer_key_lineage_fingerprint(k.organization_id,k.signer_key_id,k.revision,k.signer_subject_id,k.algorithm_id,k.subject_public_key_info_der,k.signer_key_fingerprint,k.state,k.valid_from,k.effective_at,k.supersedes_revision,(SELECT p.lineage_fingerprint FROM public.s2a_signer_key_revision p WHERE p.organization_id=k.organization_id AND p.signer_key_id=k.signer_key_id AND p.revision=k.supersedes_revision)) THEN RAISE EXCEPTION 'Historical key integrity failure' USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE'; END IF;
 SELECT * INTO au FROM public.s2a_signer_authority_revision WHERE organization_id=a.organization_id AND signer_authority_id=a.signer_authority_id AND revision=a.signer_authority_revision;
 IF NOT FOUND OR au.signer_subject_id<>k.signer_subject_id OR au.signer_key_id<>k.signer_key_id OR au.signer_key_revision<>k.revision OR au.signer_key_fingerprint<>k.signer_key_fingerprint OR au.signer_authority_fingerprint<>a.signer_authority_fingerprint OR au.approval_action<>'S2A_FIELD_PROOF_APPROVAL' OR au.permission<>'TRANSACTION_IDENTITY_DECISION_WRITE' THEN RAISE EXCEPTION 'Historical authority integrity failure' USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE'; END IF;
 proof:=public.s2a_v041_proof_fingerprint(m,d,pre,a.algorithm_id,a.signer_key_id,k.revision,k.signer_key_fingerprint,k.lineage_fingerprint,k.subject_public_key_info_der,a.signature_bytes,au.signer_authority_id,au.revision,au.signer_authority_fingerprint,a.verified_at);
 IF proof<>a.accepted_proof_fingerprint THEN RAISE EXCEPTION 'Accepted proof integrity failure' USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE'; END IF;
 IF p_expected_artifact_version<>a.artifact_version OR p_expected_canonicalization_version<>a.canonicalization_version OR p_expected_canonical_manifest_bytes<>m OR p_expected_manifest_digest<>d OR p_expected_signature_preimage_bytes<>pre OR p_expected_algorithm_id<>a.algorithm_id OR p_expected_signer_subject_id<>k.signer_subject_id OR p_expected_signer_key_id<>k.signer_key_id OR p_expected_signer_key_revision<>k.revision OR p_expected_signer_key_fingerprint<>k.signer_key_fingerprint OR p_expected_signer_key_lineage_fingerprint<>k.lineage_fingerprint OR p_expected_subject_public_key_info_der<>k.subject_public_key_info_der OR p_expected_signature_bytes<>a.signature_bytes OR p_expected_signer_authority_id<>au.signer_authority_id OR p_expected_signer_authority_revision<>au.revision OR p_expected_signer_authority_fingerprint<>au.signer_authority_fingerprint OR p_expected_verified_at<>a.verified_at OR p_expected_accepted_proof_fingerprint<>proof OR p_expected_evidence_binding_fingerprint<>p_evidence_binding_fingerprint THEN RAISE EXCEPTION 'Immutable snapshot mismatch' USING ERRCODE='P0018',DETAIL='SNAPSHOT_MISMATCH'; END IF;
 RETURN QUERY SELECT a.artifact_version,a.schema_version,a.canonicalization_version,m,d,pre,a.algorithm_id,k.signer_subject_id,k.signer_key_id,k.revision,k.signer_key_fingerprint::text,k.lineage_fingerprint::text,k.subject_public_key_info_der,a.signature_bytes,au.signer_authority_id,au.revision,au.signer_authority_fingerprint::text,a.verified_at,proof,p_evidence_binding_fingerprint;
END $$;

CREATE FUNCTION public.s2a_v042_begin_attested_principal_verification(
 p_organization_id uuid,p_manifest_id uuid,p_operation_id uuid,p_principal_id uuid,
 p_schema_version integer,p_claim_manifest_id uuid,p_claim_organization_id uuid,
 p_mercado_livre_connection_id uuid,p_omie_connection_id uuid,p_source_order_reference text,
 p_integration_reference text,p_marketplace_order_id uuid,p_permission text,
 p_accountable_operator uuid,p_approval_source uuid,p_approval_window_start timestamptz,
 p_approval_window_end timestamptz,p_revocation_owner uuid,p_credential_custodian uuid,
 p_credential_delivery_method text,p_credential_rotation_owner uuid,p_immediate_revocation_policy text,
 p_reason text,p_provenance text,p_correlation_id uuid,p_evidence_binding_fingerprint text
) RETURNS TABLE(
 outcome text,result_operation_id uuid,result_intent_fingerprint text,result_receipt_fingerprint text,result_effect_time timestamptz(6),
 result_artifact_version integer,result_schema_version integer,result_canonicalization_version integer,
 result_canonical_manifest_bytes bytea,result_manifest_digest text,result_signature_preimage_bytes bytea,
 result_algorithm_id text,result_signer_subject_id uuid,result_signer_key_id uuid,result_signer_key_revision integer,
 result_signer_key_fingerprint text,result_signer_key_lineage_fingerprint text,result_subject_public_key_info_der bytea,
 result_signature_bytes bytea,result_signer_authority_id uuid,result_signer_authority_revision integer,
 result_signer_authority_fingerprint text,result_verified_at timestamptz(6),result_accepted_proof_fingerprint text,
 result_signed_evidence_binding_fingerprint text,result_current_durable_evidence_binding text,
 result_observed_effect_time timestamptz(6),result_observed_effective_signer_key_revision integer,
 result_observed_effective_signer_key_state text,result_observed_current_signer_authority_id uuid,
 result_observed_current_signer_authority_revision integer,result_observed_current_signer_authority_fingerprint text
)
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$
DECLARE
 org_status text; op public.command_authority_operation%ROWTYPE; principal public.command_principal%ROWTYPE;
 a public.s2a_accepted_attestation%ROWTYPE; k public.s2a_signer_key_revision%ROWTYPE;
 au public.s2a_signer_authority_revision%ROWTYPE; snapshot record; reconstructed bytea; reconstructed_digest text;
 current_evidence text; computed_intent text; computed_receipt text; resource text; key_leaf_count integer;
 authority_leaf_count integer; ml_count bigint; omie_count bigint;
BEGIN
 SELECT o.status INTO org_status FROM public.integration_organization o
  WHERE o.organization_id=p_organization_id FOR SHARE;
 IF NOT FOUND THEN RAISE EXCEPTION 'Governance unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE'; END IF;
 PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(
  'command-authority-operation/1:'||p_organization_id||':'||p_operation_id,0));
 SELECT * INTO op FROM public.command_authority_operation o
  WHERE o.organization_id=p_organization_id AND o.operation_id=p_operation_id;
 IF FOUND THEN
  IF op.operation IS DISTINCT FROM 'PRINCIPAL' OR op.principal_id IS DISTINCT FROM p_principal_id OR op.attestation_manifest_id IS DISTINCT FROM p_manifest_id
   OR op.correlation_id IS DISTINCT FROM p_correlation_id OR op.credential_id IS NOT NULL OR op.credential_revision IS NOT NULL
   OR op.grant_id IS NOT NULL OR op.grant_revision IS NOT NULL OR op.permission IS NOT NULL OR op.state IS NOT NULL THEN
   RAISE EXCEPTION 'Historical operation integrity failure' USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE';
  END IF;
  computed_intent:=public.s2a_v042_authority_intent('PRINCIPAL',p_operation_id,p_organization_id,p_principal_id,
   p_mercado_livre_connection_id,p_omie_connection_id,NULL,NULL,NULL,p_reason,p_provenance,p_correlation_id,
   p_manifest_id,(SELECT accepted_proof_fingerprint::text FROM public.s2a_accepted_attestation
                  WHERE organization_id=p_organization_id AND manifest_id=p_manifest_id),
   (SELECT manifest_digest::text FROM public.s2a_accepted_attestation
                  WHERE organization_id=p_organization_id AND manifest_id=p_manifest_id));
  computed_receipt:=public.s2a_v042_authority_receipt(computed_intent,'PRINCIPAL',p_principal_id,NULL,NULL,NULL,NULL,NULL,NULL);
  IF op.intent_fingerprint<>computed_intent OR op.receipt_fingerprint<>computed_receipt THEN
   RAISE EXCEPTION 'Historical operation fingerprint integrity failure' USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE';
  END IF;
  SELECT * INTO principal FROM public.command_principal p WHERE p.organization_id=p_organization_id AND p.principal_id=p_principal_id;
  IF NOT FOUND OR principal.mercado_livre_connection_id<>p_mercado_livre_connection_id OR principal.omie_connection_id<>p_omie_connection_id THEN
   RAISE EXCEPTION 'Historical principal integrity failure' USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE';
  END IF;
  SELECT * INTO a FROM public.s2a_accepted_attestation x WHERE x.organization_id=p_organization_id AND x.manifest_id=p_manifest_id;
  IF NOT FOUND OR NOT EXISTS (SELECT 1 FROM public.s2a_attestation_consumption c
    WHERE c.organization_id=p_organization_id AND c.manifest_id=p_manifest_id AND c.principal_id=p_principal_id
      AND c.manifest_digest=a.manifest_digest AND c.correlation_id=p_correlation_id) THEN
   RAISE EXCEPTION 'Historical consumption integrity failure' USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE';
  END IF;
  outcome:='ALREADY_APPLIED'; result_operation_id:=op.operation_id; result_intent_fingerprint:=computed_intent;
  result_receipt_fingerprint:=computed_receipt; result_effect_time:=op.decided_at;
  result_artifact_version:=a.artifact_version; result_schema_version:=a.schema_version; result_canonicalization_version:=a.canonicalization_version;
  result_canonical_manifest_bytes:=a.canonical_manifest_bytes; result_manifest_digest:=a.manifest_digest;
  result_signature_preimage_bytes:=a.canonical_signature_preimage_bytes; result_algorithm_id:=a.algorithm_id;
  SELECT historical_key.signer_subject_id INTO result_signer_subject_id FROM public.s2a_signer_key_revision historical_key
   WHERE historical_key.organization_id=a.organization_id AND historical_key.signer_key_id=a.signer_key_id AND historical_key.revision=a.signer_key_revision
     AND historical_key.signer_key_fingerprint=a.signer_key_fingerprint AND historical_key.lineage_fingerprint=a.signer_key_lineage_fingerprint
     AND historical_key.subject_public_key_info_der=a.subject_public_key_info_der AND historical_key.algorithm_id=a.algorithm_id;
  IF NOT FOUND THEN RAISE EXCEPTION 'Historical signer key integrity failure' USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE'; END IF;
  result_signer_key_id:=a.signer_key_id; result_signer_key_revision:=a.signer_key_revision;
  result_signer_key_fingerprint:=a.signer_key_fingerprint; result_signer_key_lineage_fingerprint:=a.signer_key_lineage_fingerprint;
  result_subject_public_key_info_der:=a.subject_public_key_info_der; result_signature_bytes:=a.signature_bytes;
  result_signer_authority_id:=a.signer_authority_id; result_signer_authority_revision:=a.signer_authority_revision;
  result_signer_authority_fingerprint:=a.signer_authority_fingerprint; result_verified_at:=a.verified_at;
  result_accepted_proof_fingerprint:=a.accepted_proof_fingerprint; result_signed_evidence_binding_fingerprint:=p_evidence_binding_fingerprint;
  RETURN NEXT; RETURN;
 END IF;
 IF org_status<>'ACTIVE' THEN RAISE EXCEPTION 'Organization inactive' USING ERRCODE='P0017',DETAIL='EXPIRED_OR_NOT_YET_VALID'; END IF;
 IF p_claim_organization_id<>p_organization_id OR p_claim_manifest_id<>p_manifest_id OR p_permission<>'TRANSACTION_IDENTITY_DECISION_WRITE' THEN
  RAISE EXCEPTION 'Claim scope mismatch' USING ERRCODE='P0017',DETAIL='SCOPE_MISMATCH';
 END IF;
 PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(
  'command-authority-principal/1:'||p_organization_id||':'||p_principal_id,0));
 SELECT * INTO principal FROM public.command_principal p WHERE p.organization_id=p_organization_id AND p.principal_id=p_principal_id FOR UPDATE;
 IF FOUND THEN RAISE EXCEPTION 'Principal already exists' USING ERRCODE='P0016',DETAIL='GOVERNANCE_CONFLICT'; END IF;
 SELECT * INTO a FROM public.s2a_accepted_attestation x WHERE x.organization_id=p_organization_id AND x.manifest_id=p_manifest_id;
 IF NOT FOUND THEN RAISE EXCEPTION 'Accepted artifact unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE'; END IF;
 reconstructed:=public.s2a_v041_manifest_bytes(p_schema_version,p_claim_manifest_id,p_claim_organization_id,
  p_mercado_livre_connection_id,p_omie_connection_id,p_source_order_reference,p_integration_reference,p_marketplace_order_id,
  p_permission,p_accountable_operator,p_approval_source,p_approval_window_start,p_approval_window_end,p_revocation_owner,
  p_credential_custodian,p_credential_delivery_method,p_credential_rotation_owner,p_immediate_revocation_policy,p_reason,p_provenance,
  p_correlation_id,p_evidence_binding_fingerprint);
 reconstructed_digest:=encode(sha256(reconstructed),'hex');
  IF reconstructed IS DISTINCT FROM a.canonical_manifest_bytes OR reconstructed_digest IS DISTINCT FROM a.manifest_digest THEN
  RAISE EXCEPTION 'Accepted artifact integrity failure' USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE';
 END IF;
 PERFORM 1 FROM public.integration_connector_progress cp WHERE cp.organization_id=p_organization_id
  AND cp.connection_id=p_omie_connection_id AND cp.capability='marketplace-economic.omie-transaction-evidence.reacquisition-v3' FOR UPDATE;
 IF NOT FOUND THEN RAISE EXCEPTION 'Evidence unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE'; END IF;
 FOR resource IN SELECT unnest(ARRAY[
  'transaction-identity/subject/1:'||p_organization_id||':'||p_omie_connection_id||':'||octet_length(p_source_order_reference)||':'||p_source_order_reference,
  'transaction-identity/target/1:'||p_organization_id||':'||p_marketplace_order_id]) ORDER BY 1 LOOP
  PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(resource,0));
 END LOOP;
 PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(
  's2a-attestation/manifest/1:'||p_organization_id||':'||p_manifest_id,0));
 SELECT * INTO a FROM public.s2a_accepted_attestation x WHERE x.organization_id=p_organization_id AND x.manifest_id=p_manifest_id;
 IF NOT FOUND THEN RAISE EXCEPTION 'Accepted artifact unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE'; END IF;
 SELECT * INTO snapshot FROM public.s2a_v042_revalidate_snapshot(p_organization_id,p_manifest_id,p_schema_version,p_claim_manifest_id,
  p_claim_organization_id,p_mercado_livre_connection_id,p_omie_connection_id,p_source_order_reference,p_integration_reference,p_marketplace_order_id,
  p_permission,p_accountable_operator,p_approval_source,p_approval_window_start,p_approval_window_end,p_revocation_owner,p_credential_custodian,
  p_credential_delivery_method,p_credential_rotation_owner,p_immediate_revocation_policy,p_reason,p_provenance,p_correlation_id,p_evidence_binding_fingerprint,
  a.artifact_version,a.canonicalization_version,a.canonical_manifest_bytes,a.manifest_digest,a.canonical_signature_preimage_bytes,a.algorithm_id,
  (SELECT signer_subject_id FROM public.s2a_signer_key_revision WHERE organization_id=a.organization_id AND signer_key_id=a.signer_key_id AND revision=a.signer_key_revision),
  a.signer_key_id,a.signer_key_revision,a.signer_key_fingerprint,a.signer_key_lineage_fingerprint,a.subject_public_key_info_der,a.signature_bytes,
  a.signer_authority_id,a.signer_authority_revision,a.signer_authority_fingerprint,a.verified_at,a.accepted_proof_fingerprint,p_evidence_binding_fingerprint);
 SELECT count(*) INTO ml_count FROM public.marketplace_order_occurrence_source_promotion p WHERE p.organization_id=p_organization_id
  AND p.marketplace_order_id=p_marketplace_order_id AND p.source_connection_id=p_mercado_livre_connection_id
  AND p.source_capability='marketplace-economic.order-source' AND p.outcome IN ('PROMOTED','DUPLICATE');
 SELECT count(*) INTO omie_count FROM public.integration_omie_transaction_evidence e WHERE e.organization_id=p_organization_id
  AND e.connection_id=p_omie_connection_id AND e.capability='marketplace-economic.omie-transaction-evidence.reacquisition-v3'
  AND e.source_order_ref=p_source_order_reference;
 IF ml_count=0 OR omie_count=0 THEN RAISE EXCEPTION 'Evidence unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE'; END IF;
 current_evidence:=public.s2a_v041_evidence_fingerprint(p_organization_id,p_marketplace_order_id,p_mercado_livre_connection_id,
  p_omie_connection_id,p_source_order_reference,p_integration_reference);
 IF current_evidence IS DISTINCT FROM snapshot.result_signed_evidence_binding_fingerprint THEN
  RAISE EXCEPTION 'Evidence scope mismatch' USING ERRCODE='P0017',DETAIL='SCOPE_MISMATCH';
 END IF;
 result_observed_effect_time:=clock_timestamp()::timestamptz(6);
 PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(
  's2a-governance/signer-key/1:'||p_organization_id||':'||snapshot.result_signer_key_id,0));
 SELECT count(*) INTO key_leaf_count FROM public.s2a_signer_key_revision x WHERE x.organization_id=p_organization_id
  AND x.signer_key_id=snapshot.result_signer_key_id AND NOT EXISTS (SELECT 1 FROM public.s2a_signer_key_revision n
   WHERE n.organization_id=x.organization_id AND n.signer_key_id=x.signer_key_id AND n.supersedes_revision=x.revision);
 IF key_leaf_count<>1 THEN RAISE EXCEPTION 'Signer key lineage conflict' USING ERRCODE='P0016',DETAIL='GOVERNANCE_CONFLICT'; END IF;
 SELECT * INTO k FROM public.s2a_signer_key_revision x WHERE x.organization_id=p_organization_id AND x.signer_key_id=snapshot.result_signer_key_id
  AND x.effective_at<=result_observed_effect_time ORDER BY x.effective_at DESC,x.revision DESC LIMIT 1;
 IF NOT FOUND THEN RAISE EXCEPTION 'Signer key unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE'; END IF;
 IF k.valid_from>result_observed_effect_time OR k.state<>'ACTIVE' THEN RAISE EXCEPTION 'Signer key ineligible' USING ERRCODE='P0017',DETAIL='EXPIRED_OR_NOT_YET_VALID'; END IF;
 result_observed_effective_signer_key_revision:=k.revision; result_observed_effective_signer_key_state:=k.state;
 PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended('s2a-governance/signer-authority-scope/1:'||p_organization_id||':'||
  snapshot.result_signer_subject_id||':'||snapshot.result_signer_key_id||':S2A_FIELD_PROOF_APPROVAL:TRANSACTION_IDENTITY_DECISION_WRITE',0));
 SELECT count(*) INTO authority_leaf_count FROM public.s2a_signer_authority_revision x WHERE x.organization_id=p_organization_id
  AND x.signer_subject_id=snapshot.result_signer_subject_id AND x.signer_key_id=snapshot.result_signer_key_id
  AND x.approval_action='S2A_FIELD_PROOF_APPROVAL' AND x.permission='TRANSACTION_IDENTITY_DECISION_WRITE'
  AND NOT EXISTS (SELECT 1 FROM public.s2a_signer_authority_revision n WHERE n.organization_id=x.organization_id AND n.supersedes_signer_authority_id=x.signer_authority_id);
 IF authority_leaf_count=0 THEN RAISE EXCEPTION 'Signer authority unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE'; END IF;
 IF authority_leaf_count<>1 THEN RAISE EXCEPTION 'Signer authority conflict' USING ERRCODE='P0016',DETAIL='GOVERNANCE_CONFLICT'; END IF;
 SELECT * INTO au FROM public.s2a_signer_authority_revision x WHERE x.organization_id=p_organization_id
  AND x.signer_subject_id=snapshot.result_signer_subject_id AND x.signer_key_id=snapshot.result_signer_key_id
  AND x.approval_action='S2A_FIELD_PROOF_APPROVAL' AND x.permission='TRANSACTION_IDENTITY_DECISION_WRITE'
  AND NOT EXISTS (SELECT 1 FROM public.s2a_signer_authority_revision n WHERE n.organization_id=x.organization_id AND n.supersedes_signer_authority_id=x.signer_authority_id);
 IF au.signer_key_revision IS DISTINCT FROM k.revision OR au.signer_key_fingerprint IS DISTINCT FROM k.signer_key_fingerprint THEN
  RAISE EXCEPTION 'Signer authority key scope mismatch' USING ERRCODE='P0017',DETAIL='SCOPE_MISMATCH';
 END IF;
 IF au.state<>'ENABLED' OR au.valid_from>result_observed_effect_time OR result_observed_effect_time>=au.valid_until THEN
  RAISE EXCEPTION 'Signer authority ineligible' USING ERRCODE='P0017',DETAIL='EXPIRED_OR_NOT_YET_VALID';
 END IF;
 computed_intent:=public.s2a_v042_authority_intent('PRINCIPAL',p_operation_id,p_organization_id,p_principal_id,
  p_mercado_livre_connection_id,p_omie_connection_id,NULL,NULL,NULL,p_reason,p_provenance,p_correlation_id,p_manifest_id,
  snapshot.result_accepted_proof_fingerprint,snapshot.result_manifest_digest);
 outcome:='READY'; result_operation_id:=p_operation_id; result_intent_fingerprint:=computed_intent; result_receipt_fingerprint:=NULL; result_effect_time:=NULL;
 result_artifact_version:=snapshot.result_artifact_version; result_schema_version:=snapshot.result_schema_version;
 result_canonicalization_version:=snapshot.result_canonicalization_version; result_canonical_manifest_bytes:=snapshot.result_canonical_manifest_bytes;
 result_manifest_digest:=snapshot.result_manifest_digest; result_signature_preimage_bytes:=snapshot.result_signature_preimage_bytes;
 result_algorithm_id:=snapshot.result_algorithm_id; result_signer_subject_id:=snapshot.result_signer_subject_id;
 result_signer_key_id:=snapshot.result_signer_key_id; result_signer_key_revision:=snapshot.result_signer_key_revision;
 result_signer_key_fingerprint:=snapshot.result_signer_key_fingerprint; result_signer_key_lineage_fingerprint:=snapshot.result_signer_key_lineage_fingerprint;
 result_subject_public_key_info_der:=snapshot.result_subject_public_key_info_der; result_signature_bytes:=snapshot.result_signature_bytes;
 result_signer_authority_id:=snapshot.result_signer_authority_id; result_signer_authority_revision:=snapshot.result_signer_authority_revision;
 result_signer_authority_fingerprint:=snapshot.result_signer_authority_fingerprint; result_verified_at:=snapshot.result_verified_at;
 result_accepted_proof_fingerprint:=snapshot.result_accepted_proof_fingerprint; result_signed_evidence_binding_fingerprint:=snapshot.result_signed_evidence_binding_fingerprint;
 result_current_durable_evidence_binding:=current_evidence; result_observed_current_signer_authority_id:=au.signer_authority_id;
 result_observed_current_signer_authority_revision:=au.revision; result_observed_current_signer_authority_fingerprint:=au.signer_authority_fingerprint;
 RETURN NEXT;
END $$;


CREATE FUNCTION public.s2a_v042_begin_attested_initial_credential_verification(
 p_organization_id uuid,p_manifest_id uuid,p_operation_id uuid,p_principal_id uuid,p_credential_id uuid,p_secret_verifier bytea,
 p_schema_version integer,p_claim_manifest_id uuid,p_claim_organization_id uuid,
 p_mercado_livre_connection_id uuid,p_omie_connection_id uuid,p_source_order_reference text,
 p_integration_reference text,p_marketplace_order_id uuid,p_permission text,
 p_accountable_operator uuid,p_approval_source uuid,p_approval_window_start timestamptz,
 p_approval_window_end timestamptz,p_revocation_owner uuid,p_credential_custodian uuid,
 p_credential_delivery_method text,p_credential_rotation_owner uuid,p_immediate_revocation_policy text,
 p_reason text,p_provenance text,p_correlation_id uuid,p_evidence_binding_fingerprint text
) RETURNS TABLE(
 outcome text,result_operation_id uuid,result_intent_fingerprint text,result_receipt_fingerprint text,result_effect_time timestamptz(6),
 result_artifact_version integer,result_schema_version integer,result_canonicalization_version integer,
 result_canonical_manifest_bytes bytea,result_manifest_digest text,result_signature_preimage_bytes bytea,
 result_algorithm_id text,result_signer_subject_id uuid,result_signer_key_id uuid,result_signer_key_revision integer,
 result_signer_key_fingerprint text,result_signer_key_lineage_fingerprint text,result_subject_public_key_info_der bytea,
 result_signature_bytes bytea,result_signer_authority_id uuid,result_signer_authority_revision integer,
 result_signer_authority_fingerprint text,result_verified_at timestamptz(6),result_accepted_proof_fingerprint text,
 result_signed_evidence_binding_fingerprint text,result_current_durable_evidence_binding text,
 result_observed_effect_time timestamptz(6),result_observed_effective_signer_key_revision integer,
 result_observed_effective_signer_key_state text,result_observed_current_signer_authority_id uuid,
 result_observed_current_signer_authority_revision integer,result_observed_current_signer_authority_fingerprint text
)
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$
DECLARE
 org_status text; op public.command_authority_operation%ROWTYPE; principal public.command_principal%ROWTYPE;
 a public.s2a_accepted_attestation%ROWTYPE; k public.s2a_signer_key_revision%ROWTYPE;
 au public.s2a_signer_authority_revision%ROWTYPE; snapshot record; reconstructed bytea; reconstructed_digest text;
 current_evidence text; computed_intent text; computed_receipt text; resource text; key_leaf_count integer;
 authority_leaf_count integer; ml_count bigint; omie_count bigint;
BEGIN
 SELECT o.status INTO org_status FROM public.integration_organization o
  WHERE o.organization_id=p_organization_id FOR SHARE;
 IF NOT FOUND THEN RAISE EXCEPTION 'Governance unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE'; END IF;
 PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(
  'command-authority-operation/1:'||p_organization_id||':'||p_operation_id,0));
 SELECT * INTO op FROM public.command_authority_operation o
  WHERE o.organization_id=p_organization_id AND o.operation_id=p_operation_id;
 IF FOUND THEN
   IF op.operation IS DISTINCT FROM 'INITIAL_CREDENTIAL' OR op.principal_id IS DISTINCT FROM p_principal_id OR op.credential_id IS DISTINCT FROM p_credential_id OR op.credential_revision IS DISTINCT FROM 1 OR op.attestation_manifest_id IS DISTINCT FROM p_manifest_id
    OR op.correlation_id IS DISTINCT FROM p_correlation_id
   OR op.grant_id IS NOT NULL OR op.grant_revision IS NOT NULL OR op.permission IS NOT NULL OR op.state IS DISTINCT FROM 'ENABLED' THEN
   RAISE EXCEPTION 'Historical operation integrity failure' USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE';
  END IF;
  computed_intent:=public.s2a_v042_authority_intent('INITIAL_CREDENTIAL',p_operation_id,p_organization_id,p_principal_id,
   NULL,NULL,p_credential_id,p_secret_verifier,NULL,p_reason,p_provenance,p_correlation_id,
   p_manifest_id,(SELECT accepted_proof_fingerprint::text FROM public.s2a_accepted_attestation
                  WHERE organization_id=p_organization_id AND manifest_id=p_manifest_id),
   (SELECT manifest_digest::text FROM public.s2a_accepted_attestation
                  WHERE organization_id=p_organization_id AND manifest_id=p_manifest_id));
  computed_receipt:=public.s2a_v042_authority_receipt(computed_intent,'INITIAL_CREDENTIAL',p_principal_id,p_credential_id,1,NULL,NULL,NULL,'ENABLED');
  IF op.intent_fingerprint<>computed_intent OR op.receipt_fingerprint<>computed_receipt THEN
   RAISE EXCEPTION 'Historical operation fingerprint integrity failure' USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE';
  END IF;
  SELECT * INTO principal FROM public.command_principal p WHERE p.organization_id=p_organization_id AND p.principal_id=p_principal_id;
  IF NOT FOUND OR principal.mercado_livre_connection_id<>p_mercado_livre_connection_id OR principal.omie_connection_id<>p_omie_connection_id THEN
   RAISE EXCEPTION 'Historical principal integrity failure' USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM public.command_credential_revision c WHERE c.organization_id=p_organization_id AND c.credential_id=p_credential_id AND c.revision=1 AND c.principal_id=p_principal_id AND c.state='ENABLED' AND c.secret_verifier=p_secret_verifier) THEN
   RAISE EXCEPTION 'Historical credential integrity failure' USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE';
  END IF;
  SELECT * INTO a FROM public.s2a_accepted_attestation x WHERE x.organization_id=p_organization_id AND x.manifest_id=p_manifest_id;
  IF NOT FOUND OR NOT EXISTS (SELECT 1 FROM public.s2a_attestation_consumption c
    WHERE c.organization_id=p_organization_id AND c.manifest_id=p_manifest_id AND c.principal_id=p_principal_id
      AND c.manifest_digest=a.manifest_digest AND c.correlation_id=p_correlation_id) THEN
   RAISE EXCEPTION 'Historical consumption integrity failure' USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE';
  END IF;
  outcome:='ALREADY_APPLIED'; result_operation_id:=op.operation_id; result_intent_fingerprint:=computed_intent;
  result_receipt_fingerprint:=computed_receipt; result_effect_time:=op.decided_at;
  result_artifact_version:=a.artifact_version; result_schema_version:=a.schema_version; result_canonicalization_version:=a.canonicalization_version;
  result_canonical_manifest_bytes:=a.canonical_manifest_bytes; result_manifest_digest:=a.manifest_digest;
   result_signature_preimage_bytes:=a.canonical_signature_preimage_bytes; result_algorithm_id:=a.algorithm_id;
   SELECT historical_key.signer_subject_id INTO result_signer_subject_id FROM public.s2a_signer_key_revision historical_key
    WHERE historical_key.organization_id=a.organization_id AND historical_key.signer_key_id=a.signer_key_id AND historical_key.revision=a.signer_key_revision
      AND historical_key.signer_key_fingerprint=a.signer_key_fingerprint AND historical_key.lineage_fingerprint=a.signer_key_lineage_fingerprint
      AND historical_key.subject_public_key_info_der=a.subject_public_key_info_der AND historical_key.algorithm_id=a.algorithm_id;
   IF NOT FOUND THEN RAISE EXCEPTION 'Historical signer key integrity failure' USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE'; END IF;
  result_signer_key_id:=a.signer_key_id; result_signer_key_revision:=a.signer_key_revision;
  result_signer_key_fingerprint:=a.signer_key_fingerprint; result_signer_key_lineage_fingerprint:=a.signer_key_lineage_fingerprint;
  result_subject_public_key_info_der:=a.subject_public_key_info_der; result_signature_bytes:=a.signature_bytes;
  result_signer_authority_id:=a.signer_authority_id; result_signer_authority_revision:=a.signer_authority_revision;
  result_signer_authority_fingerprint:=a.signer_authority_fingerprint; result_verified_at:=a.verified_at;
  result_accepted_proof_fingerprint:=a.accepted_proof_fingerprint; result_signed_evidence_binding_fingerprint:=p_evidence_binding_fingerprint;
  RETURN NEXT; RETURN;
 END IF;
 IF org_status<>'ACTIVE' THEN RAISE EXCEPTION 'Organization inactive' USING ERRCODE='P0017',DETAIL='EXPIRED_OR_NOT_YET_VALID'; END IF;
 IF p_claim_organization_id<>p_organization_id OR p_claim_manifest_id<>p_manifest_id OR p_permission<>'TRANSACTION_IDENTITY_DECISION_WRITE' THEN
  RAISE EXCEPTION 'Claim scope mismatch' USING ERRCODE='P0017',DETAIL='SCOPE_MISMATCH';
 END IF;
 PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(
  'command-authority-principal/1:'||p_organization_id||':'||p_principal_id,0));
 SELECT * INTO principal FROM public.command_principal p WHERE p.organization_id=p_organization_id AND p.principal_id=p_principal_id FOR UPDATE;
 IF NOT FOUND THEN RAISE EXCEPTION 'Principal unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE'; END IF;
 IF octet_length(p_secret_verifier)<>32 THEN RAISE EXCEPTION 'Credential verifier shape invalid' USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE'; END IF;
 IF EXISTS (SELECT 1 FROM public.command_credential_revision c WHERE c.organization_id=p_organization_id AND (c.credential_id=p_credential_id OR c.principal_id=p_principal_id)) THEN RAISE EXCEPTION 'Initial credential collision' USING ERRCODE='P0016',DETAIL='GOVERNANCE_CONFLICT'; END IF;
 IF NOT EXISTS (SELECT 1 FROM public.s2a_attestation_consumption c WHERE c.organization_id=p_organization_id AND c.manifest_id=p_manifest_id AND c.principal_id=p_principal_id AND c.correlation_id=p_correlation_id) THEN RAISE EXCEPTION 'Consumption unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE'; END IF;
 SELECT * INTO a FROM public.s2a_accepted_attestation x WHERE x.organization_id=p_organization_id AND x.manifest_id=p_manifest_id;
 IF NOT FOUND THEN RAISE EXCEPTION 'Accepted artifact unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE'; END IF;
 reconstructed:=public.s2a_v041_manifest_bytes(p_schema_version,p_claim_manifest_id,p_claim_organization_id,
  p_mercado_livre_connection_id,p_omie_connection_id,p_source_order_reference,p_integration_reference,p_marketplace_order_id,
  p_permission,p_accountable_operator,p_approval_source,p_approval_window_start,p_approval_window_end,p_revocation_owner,
  p_credential_custodian,p_credential_delivery_method,p_credential_rotation_owner,p_immediate_revocation_policy,p_reason,p_provenance,
  p_correlation_id,p_evidence_binding_fingerprint);
 reconstructed_digest:=encode(sha256(reconstructed),'hex');
  IF reconstructed IS DISTINCT FROM a.canonical_manifest_bytes OR reconstructed_digest IS DISTINCT FROM a.manifest_digest THEN
  RAISE EXCEPTION 'Accepted artifact integrity failure' USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE';
 END IF;
 PERFORM 1 FROM public.integration_connector_progress cp WHERE cp.organization_id=p_organization_id
  AND cp.connection_id=p_omie_connection_id AND cp.capability='marketplace-economic.omie-transaction-evidence.reacquisition-v3' FOR UPDATE;
 IF NOT FOUND THEN RAISE EXCEPTION 'Evidence unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE'; END IF;
 FOR resource IN SELECT unnest(ARRAY[
  'transaction-identity/subject/1:'||p_organization_id||':'||p_omie_connection_id||':'||octet_length(p_source_order_reference)||':'||p_source_order_reference,
  'transaction-identity/target/1:'||p_organization_id||':'||p_marketplace_order_id]) ORDER BY 1 LOOP
  PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(resource,0));
 END LOOP;
 PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(
  's2a-attestation/manifest/1:'||p_organization_id||':'||p_manifest_id,0));
 SELECT * INTO a FROM public.s2a_accepted_attestation x WHERE x.organization_id=p_organization_id AND x.manifest_id=p_manifest_id;
 IF NOT FOUND THEN RAISE EXCEPTION 'Accepted artifact unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE'; END IF;
 SELECT * INTO snapshot FROM public.s2a_v042_revalidate_snapshot(p_organization_id,p_manifest_id,p_schema_version,p_claim_manifest_id,
  p_claim_organization_id,p_mercado_livre_connection_id,p_omie_connection_id,p_source_order_reference,p_integration_reference,p_marketplace_order_id,
  p_permission,p_accountable_operator,p_approval_source,p_approval_window_start,p_approval_window_end,p_revocation_owner,p_credential_custodian,
  p_credential_delivery_method,p_credential_rotation_owner,p_immediate_revocation_policy,p_reason,p_provenance,p_correlation_id,p_evidence_binding_fingerprint,
  a.artifact_version,a.canonicalization_version,a.canonical_manifest_bytes,a.manifest_digest,a.canonical_signature_preimage_bytes,a.algorithm_id,
  (SELECT signer_subject_id FROM public.s2a_signer_key_revision WHERE organization_id=a.organization_id AND signer_key_id=a.signer_key_id AND revision=a.signer_key_revision),
  a.signer_key_id,a.signer_key_revision,a.signer_key_fingerprint,a.signer_key_lineage_fingerprint,a.subject_public_key_info_der,a.signature_bytes,
  a.signer_authority_id,a.signer_authority_revision,a.signer_authority_fingerprint,a.verified_at,a.accepted_proof_fingerprint,p_evidence_binding_fingerprint);
 SELECT count(*) INTO ml_count FROM public.marketplace_order_occurrence_source_promotion p WHERE p.organization_id=p_organization_id
  AND p.marketplace_order_id=p_marketplace_order_id AND p.source_connection_id=p_mercado_livre_connection_id
  AND p.source_capability='marketplace-economic.order-source' AND p.outcome IN ('PROMOTED','DUPLICATE');
 SELECT count(*) INTO omie_count FROM public.integration_omie_transaction_evidence e WHERE e.organization_id=p_organization_id
  AND e.connection_id=p_omie_connection_id AND e.capability='marketplace-economic.omie-transaction-evidence.reacquisition-v3'
  AND e.source_order_ref=p_source_order_reference;
 IF ml_count=0 OR omie_count=0 THEN RAISE EXCEPTION 'Evidence unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE'; END IF;
 current_evidence:=public.s2a_v041_evidence_fingerprint(p_organization_id,p_marketplace_order_id,p_mercado_livre_connection_id,
  p_omie_connection_id,p_source_order_reference,p_integration_reference);
 IF current_evidence IS DISTINCT FROM snapshot.result_signed_evidence_binding_fingerprint THEN
  RAISE EXCEPTION 'Evidence scope mismatch' USING ERRCODE='P0017',DETAIL='SCOPE_MISMATCH';
 END IF;
 result_observed_effect_time:=clock_timestamp()::timestamptz(6);
 PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(
  's2a-governance/signer-key/1:'||p_organization_id||':'||snapshot.result_signer_key_id,0));
 SELECT count(*) INTO key_leaf_count FROM public.s2a_signer_key_revision x WHERE x.organization_id=p_organization_id
  AND x.signer_key_id=snapshot.result_signer_key_id AND NOT EXISTS (SELECT 1 FROM public.s2a_signer_key_revision n
   WHERE n.organization_id=x.organization_id AND n.signer_key_id=x.signer_key_id AND n.supersedes_revision=x.revision);
 IF key_leaf_count<>1 THEN RAISE EXCEPTION 'Signer key lineage conflict' USING ERRCODE='P0016',DETAIL='GOVERNANCE_CONFLICT'; END IF;
 SELECT * INTO k FROM public.s2a_signer_key_revision x WHERE x.organization_id=p_organization_id AND x.signer_key_id=snapshot.result_signer_key_id
  AND x.effective_at<=result_observed_effect_time ORDER BY x.effective_at DESC,x.revision DESC LIMIT 1;
 IF NOT FOUND THEN RAISE EXCEPTION 'Signer key unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE'; END IF;
 IF k.valid_from>result_observed_effect_time OR k.state<>'ACTIVE' THEN RAISE EXCEPTION 'Signer key ineligible' USING ERRCODE='P0017',DETAIL='EXPIRED_OR_NOT_YET_VALID'; END IF;
 result_observed_effective_signer_key_revision:=k.revision; result_observed_effective_signer_key_state:=k.state;
 PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended('s2a-governance/signer-authority-scope/1:'||p_organization_id||':'||
  snapshot.result_signer_subject_id||':'||snapshot.result_signer_key_id||':S2A_FIELD_PROOF_APPROVAL:TRANSACTION_IDENTITY_DECISION_WRITE',0));
 SELECT count(*) INTO authority_leaf_count FROM public.s2a_signer_authority_revision x WHERE x.organization_id=p_organization_id
  AND x.signer_subject_id=snapshot.result_signer_subject_id AND x.signer_key_id=snapshot.result_signer_key_id
  AND x.approval_action='S2A_FIELD_PROOF_APPROVAL' AND x.permission='TRANSACTION_IDENTITY_DECISION_WRITE'
  AND NOT EXISTS (SELECT 1 FROM public.s2a_signer_authority_revision n WHERE n.organization_id=x.organization_id AND n.supersedes_signer_authority_id=x.signer_authority_id);
 IF authority_leaf_count=0 THEN RAISE EXCEPTION 'Signer authority unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE'; END IF;
 IF authority_leaf_count<>1 THEN RAISE EXCEPTION 'Signer authority conflict' USING ERRCODE='P0016',DETAIL='GOVERNANCE_CONFLICT'; END IF;
 SELECT * INTO au FROM public.s2a_signer_authority_revision x WHERE x.organization_id=p_organization_id
  AND x.signer_subject_id=snapshot.result_signer_subject_id AND x.signer_key_id=snapshot.result_signer_key_id
  AND x.approval_action='S2A_FIELD_PROOF_APPROVAL' AND x.permission='TRANSACTION_IDENTITY_DECISION_WRITE'
  AND NOT EXISTS (SELECT 1 FROM public.s2a_signer_authority_revision n WHERE n.organization_id=x.organization_id AND n.supersedes_signer_authority_id=x.signer_authority_id);
 IF au.signer_key_revision IS DISTINCT FROM k.revision OR au.signer_key_fingerprint IS DISTINCT FROM k.signer_key_fingerprint THEN
  RAISE EXCEPTION 'Signer authority key scope mismatch' USING ERRCODE='P0017',DETAIL='SCOPE_MISMATCH';
 END IF;
 IF au.state<>'ENABLED' OR au.valid_from>result_observed_effect_time OR result_observed_effect_time>=au.valid_until THEN
  RAISE EXCEPTION 'Signer authority ineligible' USING ERRCODE='P0017',DETAIL='EXPIRED_OR_NOT_YET_VALID';
 END IF;
 computed_intent:=public.s2a_v042_authority_intent('INITIAL_CREDENTIAL',p_operation_id,p_organization_id,p_principal_id,
   NULL,NULL,p_credential_id,p_secret_verifier,NULL,p_reason,p_provenance,p_correlation_id,p_manifest_id,
  snapshot.result_accepted_proof_fingerprint,snapshot.result_manifest_digest);
 outcome:='READY'; result_operation_id:=p_operation_id; result_intent_fingerprint:=computed_intent; result_receipt_fingerprint:=NULL; result_effect_time:=NULL;
 result_artifact_version:=snapshot.result_artifact_version; result_schema_version:=snapshot.result_schema_version;
 result_canonicalization_version:=snapshot.result_canonicalization_version; result_canonical_manifest_bytes:=snapshot.result_canonical_manifest_bytes;
 result_manifest_digest:=snapshot.result_manifest_digest; result_signature_preimage_bytes:=snapshot.result_signature_preimage_bytes;
 result_algorithm_id:=snapshot.result_algorithm_id; result_signer_subject_id:=snapshot.result_signer_subject_id;
 result_signer_key_id:=snapshot.result_signer_key_id; result_signer_key_revision:=snapshot.result_signer_key_revision;
 result_signer_key_fingerprint:=snapshot.result_signer_key_fingerprint; result_signer_key_lineage_fingerprint:=snapshot.result_signer_key_lineage_fingerprint;
 result_subject_public_key_info_der:=snapshot.result_subject_public_key_info_der; result_signature_bytes:=snapshot.result_signature_bytes;
 result_signer_authority_id:=snapshot.result_signer_authority_id; result_signer_authority_revision:=snapshot.result_signer_authority_revision;
 result_signer_authority_fingerprint:=snapshot.result_signer_authority_fingerprint; result_verified_at:=snapshot.result_verified_at;
 result_accepted_proof_fingerprint:=snapshot.result_accepted_proof_fingerprint; result_signed_evidence_binding_fingerprint:=snapshot.result_signed_evidence_binding_fingerprint;
 result_current_durable_evidence_binding:=current_evidence; result_observed_current_signer_authority_id:=au.signer_authority_id;
 result_observed_current_signer_authority_revision:=au.revision; result_observed_current_signer_authority_fingerprint:=au.signer_authority_fingerprint;
 RETURN NEXT;
END $$;

CREATE FUNCTION public.s2a_v042_begin_attested_grant_verification(
 p_organization_id uuid,p_manifest_id uuid,p_operation_id uuid,p_principal_id uuid,p_grant_id uuid,
 p_schema_version integer,p_claim_manifest_id uuid,p_claim_organization_id uuid,
 p_mercado_livre_connection_id uuid,p_omie_connection_id uuid,p_source_order_reference text,
 p_integration_reference text,p_marketplace_order_id uuid,p_permission text,
 p_accountable_operator uuid,p_approval_source uuid,p_approval_window_start timestamptz,
 p_approval_window_end timestamptz,p_revocation_owner uuid,p_credential_custodian uuid,
 p_credential_delivery_method text,p_credential_rotation_owner uuid,p_immediate_revocation_policy text,
 p_reason text,p_provenance text,p_correlation_id uuid,p_evidence_binding_fingerprint text
) RETURNS TABLE(
 outcome text,result_operation_id uuid,result_intent_fingerprint text,result_receipt_fingerprint text,result_effect_time timestamptz(6),
 result_artifact_version integer,result_schema_version integer,result_canonicalization_version integer,
 result_canonical_manifest_bytes bytea,result_manifest_digest text,result_signature_preimage_bytes bytea,
 result_algorithm_id text,result_signer_subject_id uuid,result_signer_key_id uuid,result_signer_key_revision integer,
 result_signer_key_fingerprint text,result_signer_key_lineage_fingerprint text,result_subject_public_key_info_der bytea,
 result_signature_bytes bytea,result_signer_authority_id uuid,result_signer_authority_revision integer,
 result_signer_authority_fingerprint text,result_verified_at timestamptz(6),result_accepted_proof_fingerprint text,
 result_signed_evidence_binding_fingerprint text,result_current_durable_evidence_binding text,
 result_observed_effect_time timestamptz(6),result_observed_effective_signer_key_revision integer,
 result_observed_effective_signer_key_state text,result_observed_current_signer_authority_id uuid,
 result_observed_current_signer_authority_revision integer,result_observed_current_signer_authority_fingerprint text
)
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$
DECLARE
 org_status text; op public.command_authority_operation%ROWTYPE; principal public.command_principal%ROWTYPE;
 a public.s2a_accepted_attestation%ROWTYPE; k public.s2a_signer_key_revision%ROWTYPE;
 au public.s2a_signer_authority_revision%ROWTYPE; snapshot record; reconstructed bytea; reconstructed_digest text;
 current_evidence text; computed_intent text; computed_receipt text; resource text; key_leaf_count integer;
 authority_leaf_count integer; ml_count bigint; omie_count bigint;
BEGIN
 SELECT o.status INTO org_status FROM public.integration_organization o
  WHERE o.organization_id=p_organization_id FOR SHARE;
 IF NOT FOUND THEN RAISE EXCEPTION 'Governance unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE'; END IF;
 PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(
  'command-authority-operation/1:'||p_organization_id||':'||p_operation_id,0));
 SELECT * INTO op FROM public.command_authority_operation o
  WHERE o.organization_id=p_organization_id AND o.operation_id=p_operation_id;
 IF FOUND THEN
  IF op.operation IS DISTINCT FROM 'GRANT' OR op.principal_id IS DISTINCT FROM p_principal_id OR op.credential_id IS NOT NULL OR op.credential_revision IS NOT NULL OR op.grant_id IS DISTINCT FROM p_grant_id OR op.grant_revision IS DISTINCT FROM 1 OR op.attestation_manifest_id IS DISTINCT FROM p_manifest_id
   OR op.correlation_id IS DISTINCT FROM p_correlation_id OR op.credential_id IS NOT NULL OR op.credential_revision IS NOT NULL
   OR op.permission IS DISTINCT FROM 'TRANSACTION_IDENTITY_DECISION_WRITE' OR op.state IS DISTINCT FROM 'ENABLED' THEN
   RAISE EXCEPTION 'Historical operation integrity failure' USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE';
  END IF;
  computed_intent:=public.s2a_v042_authority_intent('GRANT',p_operation_id,p_organization_id,p_principal_id,
   NULL,NULL,NULL,NULL,p_grant_id,p_reason,p_provenance,p_correlation_id,
   p_manifest_id,(SELECT accepted_proof_fingerprint::text FROM public.s2a_accepted_attestation
                  WHERE organization_id=p_organization_id AND manifest_id=p_manifest_id),
   (SELECT manifest_digest::text FROM public.s2a_accepted_attestation
                  WHERE organization_id=p_organization_id AND manifest_id=p_manifest_id));
  computed_receipt:=public.s2a_v042_authority_receipt(computed_intent,'GRANT',p_principal_id,NULL,NULL,p_grant_id,1,'TRANSACTION_IDENTITY_DECISION_WRITE','ENABLED');
  IF op.intent_fingerprint<>computed_intent OR op.receipt_fingerprint<>computed_receipt THEN
   RAISE EXCEPTION 'Historical operation fingerprint integrity failure' USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE';
  END IF;
  SELECT * INTO principal FROM public.command_principal p WHERE p.organization_id=p_organization_id AND p.principal_id=p_principal_id;
  IF NOT FOUND OR principal.mercado_livre_connection_id<>p_mercado_livre_connection_id OR principal.omie_connection_id<>p_omie_connection_id THEN
   RAISE EXCEPTION 'Historical principal integrity failure' USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM public.command_permission_grant g WHERE g.organization_id=p_organization_id AND g.grant_id=p_grant_id AND g.revision=1 AND g.principal_id=p_principal_id AND g.permission='TRANSACTION_IDENTITY_DECISION_WRITE' AND g.state='ENABLED') THEN
   RAISE EXCEPTION 'Historical credential integrity failure' USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE';
  END IF;
  SELECT * INTO a FROM public.s2a_accepted_attestation x WHERE x.organization_id=p_organization_id AND x.manifest_id=p_manifest_id;
  IF NOT FOUND OR NOT EXISTS (SELECT 1 FROM public.s2a_attestation_consumption c
    WHERE c.organization_id=p_organization_id AND c.manifest_id=p_manifest_id AND c.principal_id=p_principal_id
      AND c.manifest_digest=a.manifest_digest AND c.correlation_id=p_correlation_id) THEN
   RAISE EXCEPTION 'Historical consumption integrity failure' USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE';
  END IF;
  outcome:='ALREADY_APPLIED'; result_operation_id:=op.operation_id; result_intent_fingerprint:=computed_intent;
  result_receipt_fingerprint:=computed_receipt; result_effect_time:=op.decided_at;
  result_artifact_version:=a.artifact_version; result_schema_version:=a.schema_version; result_canonicalization_version:=a.canonicalization_version;
  result_canonical_manifest_bytes:=a.canonical_manifest_bytes; result_manifest_digest:=a.manifest_digest;
   result_signature_preimage_bytes:=a.canonical_signature_preimage_bytes; result_algorithm_id:=a.algorithm_id;
   SELECT historical_key.signer_subject_id INTO result_signer_subject_id FROM public.s2a_signer_key_revision historical_key
    WHERE historical_key.organization_id=a.organization_id AND historical_key.signer_key_id=a.signer_key_id AND historical_key.revision=a.signer_key_revision
      AND historical_key.signer_key_fingerprint=a.signer_key_fingerprint AND historical_key.lineage_fingerprint=a.signer_key_lineage_fingerprint
      AND historical_key.subject_public_key_info_der=a.subject_public_key_info_der AND historical_key.algorithm_id=a.algorithm_id;
   IF NOT FOUND THEN RAISE EXCEPTION 'Historical signer key integrity failure' USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE'; END IF;
   result_signer_key_id:=a.signer_key_id; result_signer_key_revision:=a.signer_key_revision;
  result_signer_key_fingerprint:=a.signer_key_fingerprint; result_signer_key_lineage_fingerprint:=a.signer_key_lineage_fingerprint;
  result_subject_public_key_info_der:=a.subject_public_key_info_der; result_signature_bytes:=a.signature_bytes;
  result_signer_authority_id:=a.signer_authority_id; result_signer_authority_revision:=a.signer_authority_revision;
  result_signer_authority_fingerprint:=a.signer_authority_fingerprint; result_verified_at:=a.verified_at;
  result_accepted_proof_fingerprint:=a.accepted_proof_fingerprint; result_signed_evidence_binding_fingerprint:=p_evidence_binding_fingerprint;
  RETURN NEXT; RETURN;
 END IF;
 IF org_status<>'ACTIVE' THEN RAISE EXCEPTION 'Organization inactive' USING ERRCODE='P0017',DETAIL='EXPIRED_OR_NOT_YET_VALID'; END IF;
 IF p_claim_organization_id<>p_organization_id OR p_claim_manifest_id<>p_manifest_id OR p_permission<>'TRANSACTION_IDENTITY_DECISION_WRITE' THEN
  RAISE EXCEPTION 'Claim scope mismatch' USING ERRCODE='P0017',DETAIL='SCOPE_MISMATCH';
 END IF;
 PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(
  'command-authority-principal/1:'||p_organization_id||':'||p_principal_id,0));
 SELECT * INTO principal FROM public.command_principal p WHERE p.organization_id=p_organization_id AND p.principal_id=p_principal_id FOR UPDATE;
 IF NOT FOUND THEN RAISE EXCEPTION 'Principal unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE'; END IF;
 IF EXISTS (SELECT 1 FROM public.command_permission_grant g WHERE g.organization_id=p_organization_id AND (g.grant_id=p_grant_id OR (g.principal_id=p_principal_id AND g.permission='TRANSACTION_IDENTITY_DECISION_WRITE'))) THEN RAISE EXCEPTION 'Initial grant collision' USING ERRCODE='P0016',DETAIL='GOVERNANCE_CONFLICT'; END IF;
 IF NOT EXISTS (SELECT 1 FROM public.s2a_attestation_consumption c WHERE c.organization_id=p_organization_id AND c.manifest_id=p_manifest_id AND c.principal_id=p_principal_id AND c.correlation_id=p_correlation_id) THEN RAISE EXCEPTION 'Consumption unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE'; END IF;
 SELECT * INTO a FROM public.s2a_accepted_attestation x WHERE x.organization_id=p_organization_id AND x.manifest_id=p_manifest_id;
 IF NOT FOUND THEN RAISE EXCEPTION 'Accepted artifact unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE'; END IF;
 reconstructed:=public.s2a_v041_manifest_bytes(p_schema_version,p_claim_manifest_id,p_claim_organization_id,
  p_mercado_livre_connection_id,p_omie_connection_id,p_source_order_reference,p_integration_reference,p_marketplace_order_id,
  p_permission,p_accountable_operator,p_approval_source,p_approval_window_start,p_approval_window_end,p_revocation_owner,
  p_credential_custodian,p_credential_delivery_method,p_credential_rotation_owner,p_immediate_revocation_policy,p_reason,p_provenance,
  p_correlation_id,p_evidence_binding_fingerprint);
 reconstructed_digest:=encode(sha256(reconstructed),'hex');
  IF reconstructed IS DISTINCT FROM a.canonical_manifest_bytes OR reconstructed_digest IS DISTINCT FROM a.manifest_digest THEN
  RAISE EXCEPTION 'Accepted artifact integrity failure' USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE';
 END IF;
 PERFORM 1 FROM public.integration_connector_progress cp WHERE cp.organization_id=p_organization_id
  AND cp.connection_id=p_omie_connection_id AND cp.capability='marketplace-economic.omie-transaction-evidence.reacquisition-v3' FOR UPDATE;
 IF NOT FOUND THEN RAISE EXCEPTION 'Evidence unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE'; END IF;
 FOR resource IN SELECT unnest(ARRAY[
  'transaction-identity/subject/1:'||p_organization_id||':'||p_omie_connection_id||':'||octet_length(p_source_order_reference)||':'||p_source_order_reference,
  'transaction-identity/target/1:'||p_organization_id||':'||p_marketplace_order_id]) ORDER BY 1 LOOP
  PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(resource,0));
 END LOOP;
 PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(
  's2a-attestation/manifest/1:'||p_organization_id||':'||p_manifest_id,0));
 SELECT * INTO a FROM public.s2a_accepted_attestation x WHERE x.organization_id=p_organization_id AND x.manifest_id=p_manifest_id;
 IF NOT FOUND THEN RAISE EXCEPTION 'Accepted artifact unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE'; END IF;
 SELECT * INTO snapshot FROM public.s2a_v042_revalidate_snapshot(p_organization_id,p_manifest_id,p_schema_version,p_claim_manifest_id,
  p_claim_organization_id,p_mercado_livre_connection_id,p_omie_connection_id,p_source_order_reference,p_integration_reference,p_marketplace_order_id,
  p_permission,p_accountable_operator,p_approval_source,p_approval_window_start,p_approval_window_end,p_revocation_owner,p_credential_custodian,
  p_credential_delivery_method,p_credential_rotation_owner,p_immediate_revocation_policy,p_reason,p_provenance,p_correlation_id,p_evidence_binding_fingerprint,
  a.artifact_version,a.canonicalization_version,a.canonical_manifest_bytes,a.manifest_digest,a.canonical_signature_preimage_bytes,a.algorithm_id,
  (SELECT signer_subject_id FROM public.s2a_signer_key_revision WHERE organization_id=a.organization_id AND signer_key_id=a.signer_key_id AND revision=a.signer_key_revision),
  a.signer_key_id,a.signer_key_revision,a.signer_key_fingerprint,a.signer_key_lineage_fingerprint,a.subject_public_key_info_der,a.signature_bytes,
  a.signer_authority_id,a.signer_authority_revision,a.signer_authority_fingerprint,a.verified_at,a.accepted_proof_fingerprint,p_evidence_binding_fingerprint);
 SELECT count(*) INTO ml_count FROM public.marketplace_order_occurrence_source_promotion p WHERE p.organization_id=p_organization_id
  AND p.marketplace_order_id=p_marketplace_order_id AND p.source_connection_id=p_mercado_livre_connection_id
  AND p.source_capability='marketplace-economic.order-source' AND p.outcome IN ('PROMOTED','DUPLICATE');
 SELECT count(*) INTO omie_count FROM public.integration_omie_transaction_evidence e WHERE e.organization_id=p_organization_id
  AND e.connection_id=p_omie_connection_id AND e.capability='marketplace-economic.omie-transaction-evidence.reacquisition-v3'
  AND e.source_order_ref=p_source_order_reference;
 IF ml_count=0 OR omie_count=0 THEN RAISE EXCEPTION 'Evidence unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE'; END IF;
 current_evidence:=public.s2a_v041_evidence_fingerprint(p_organization_id,p_marketplace_order_id,p_mercado_livre_connection_id,
  p_omie_connection_id,p_source_order_reference,p_integration_reference);
 IF current_evidence IS DISTINCT FROM snapshot.result_signed_evidence_binding_fingerprint THEN
  RAISE EXCEPTION 'Evidence scope mismatch' USING ERRCODE='P0017',DETAIL='SCOPE_MISMATCH';
 END IF;
 result_observed_effect_time:=clock_timestamp()::timestamptz(6);
 PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(
  's2a-governance/signer-key/1:'||p_organization_id||':'||snapshot.result_signer_key_id,0));
 SELECT count(*) INTO key_leaf_count FROM public.s2a_signer_key_revision x WHERE x.organization_id=p_organization_id
  AND x.signer_key_id=snapshot.result_signer_key_id AND NOT EXISTS (SELECT 1 FROM public.s2a_signer_key_revision n
   WHERE n.organization_id=x.organization_id AND n.signer_key_id=x.signer_key_id AND n.supersedes_revision=x.revision);
 IF key_leaf_count<>1 THEN RAISE EXCEPTION 'Signer key lineage conflict' USING ERRCODE='P0016',DETAIL='GOVERNANCE_CONFLICT'; END IF;
 SELECT * INTO k FROM public.s2a_signer_key_revision x WHERE x.organization_id=p_organization_id AND x.signer_key_id=snapshot.result_signer_key_id
  AND x.effective_at<=result_observed_effect_time ORDER BY x.effective_at DESC,x.revision DESC LIMIT 1;
 IF NOT FOUND THEN RAISE EXCEPTION 'Signer key unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE'; END IF;
 IF k.valid_from>result_observed_effect_time OR k.state<>'ACTIVE' THEN RAISE EXCEPTION 'Signer key ineligible' USING ERRCODE='P0017',DETAIL='EXPIRED_OR_NOT_YET_VALID'; END IF;
 result_observed_effective_signer_key_revision:=k.revision; result_observed_effective_signer_key_state:=k.state;
 PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended('s2a-governance/signer-authority-scope/1:'||p_organization_id||':'||
  snapshot.result_signer_subject_id||':'||snapshot.result_signer_key_id||':S2A_FIELD_PROOF_APPROVAL:TRANSACTION_IDENTITY_DECISION_WRITE',0));
 SELECT count(*) INTO authority_leaf_count FROM public.s2a_signer_authority_revision x WHERE x.organization_id=p_organization_id
  AND x.signer_subject_id=snapshot.result_signer_subject_id AND x.signer_key_id=snapshot.result_signer_key_id
  AND x.approval_action='S2A_FIELD_PROOF_APPROVAL' AND x.permission='TRANSACTION_IDENTITY_DECISION_WRITE'
  AND NOT EXISTS (SELECT 1 FROM public.s2a_signer_authority_revision n WHERE n.organization_id=x.organization_id AND n.supersedes_signer_authority_id=x.signer_authority_id);
 IF authority_leaf_count=0 THEN RAISE EXCEPTION 'Signer authority unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE'; END IF;
 IF authority_leaf_count<>1 THEN RAISE EXCEPTION 'Signer authority conflict' USING ERRCODE='P0016',DETAIL='GOVERNANCE_CONFLICT'; END IF;
 SELECT * INTO au FROM public.s2a_signer_authority_revision x WHERE x.organization_id=p_organization_id
  AND x.signer_subject_id=snapshot.result_signer_subject_id AND x.signer_key_id=snapshot.result_signer_key_id
  AND x.approval_action='S2A_FIELD_PROOF_APPROVAL' AND x.permission='TRANSACTION_IDENTITY_DECISION_WRITE'
  AND NOT EXISTS (SELECT 1 FROM public.s2a_signer_authority_revision n WHERE n.organization_id=x.organization_id AND n.supersedes_signer_authority_id=x.signer_authority_id);
 IF au.signer_key_revision IS DISTINCT FROM k.revision OR au.signer_key_fingerprint IS DISTINCT FROM k.signer_key_fingerprint THEN
  RAISE EXCEPTION 'Signer authority key scope mismatch' USING ERRCODE='P0017',DETAIL='SCOPE_MISMATCH';
 END IF;
 IF au.state<>'ENABLED' OR au.valid_from>result_observed_effect_time OR result_observed_effect_time>=au.valid_until THEN
  RAISE EXCEPTION 'Signer authority ineligible' USING ERRCODE='P0017',DETAIL='EXPIRED_OR_NOT_YET_VALID';
 END IF;
 computed_intent:=public.s2a_v042_authority_intent('GRANT',p_operation_id,p_organization_id,p_principal_id,
   NULL,NULL,NULL,NULL,p_grant_id,p_reason,p_provenance,p_correlation_id,p_manifest_id,
  snapshot.result_accepted_proof_fingerprint,snapshot.result_manifest_digest);
 outcome:='READY'; result_operation_id:=p_operation_id; result_intent_fingerprint:=computed_intent; result_receipt_fingerprint:=NULL; result_effect_time:=NULL;
 result_artifact_version:=snapshot.result_artifact_version; result_schema_version:=snapshot.result_schema_version;
 result_canonicalization_version:=snapshot.result_canonicalization_version; result_canonical_manifest_bytes:=snapshot.result_canonical_manifest_bytes;
 result_manifest_digest:=snapshot.result_manifest_digest; result_signature_preimage_bytes:=snapshot.result_signature_preimage_bytes;
 result_algorithm_id:=snapshot.result_algorithm_id; result_signer_subject_id:=snapshot.result_signer_subject_id;
 result_signer_key_id:=snapshot.result_signer_key_id; result_signer_key_revision:=snapshot.result_signer_key_revision;
 result_signer_key_fingerprint:=snapshot.result_signer_key_fingerprint; result_signer_key_lineage_fingerprint:=snapshot.result_signer_key_lineage_fingerprint;
 result_subject_public_key_info_der:=snapshot.result_subject_public_key_info_der; result_signature_bytes:=snapshot.result_signature_bytes;
 result_signer_authority_id:=snapshot.result_signer_authority_id; result_signer_authority_revision:=snapshot.result_signer_authority_revision;
 result_signer_authority_fingerprint:=snapshot.result_signer_authority_fingerprint; result_verified_at:=snapshot.result_verified_at;
 result_accepted_proof_fingerprint:=snapshot.result_accepted_proof_fingerprint; result_signed_evidence_binding_fingerprint:=snapshot.result_signed_evidence_binding_fingerprint;
 result_current_durable_evidence_binding:=current_evidence; result_observed_current_signer_authority_id:=au.signer_authority_id;
 result_observed_current_signer_authority_revision:=au.revision; result_observed_current_signer_authority_fingerprint:=au.signer_authority_fingerprint;
 RETURN NEXT;
END $$;

CREATE FUNCTION public.s2a_v042_apply_attested_principal(
 p_organization_id uuid,p_manifest_id uuid,p_operation_id uuid,p_principal_id uuid,
 p_schema_version integer,p_claim_manifest_id uuid,p_claim_organization_id uuid,p_mercado_livre_connection_id uuid,
 p_omie_connection_id uuid,p_source_order_reference text,p_integration_reference text,p_marketplace_order_id uuid,
 p_permission text,p_accountable_operator uuid,p_approval_source uuid,p_approval_window_start timestamptz,
 p_approval_window_end timestamptz,p_revocation_owner uuid,p_credential_custodian uuid,p_credential_delivery_method text,
 p_credential_rotation_owner uuid,p_immediate_revocation_policy text,p_reason text,p_provenance text,p_correlation_id uuid,
 p_evidence_binding_fingerprint text,p_expected_artifact_version integer,p_expected_canonicalization_version integer,
 p_expected_canonical_manifest_bytes bytea,p_expected_manifest_digest text,p_expected_signature_preimage_bytes bytea,
 p_expected_algorithm_id text,p_expected_signer_subject_id uuid,p_expected_signer_key_id uuid,
 p_expected_signer_key_revision integer,p_expected_signer_key_fingerprint text,p_expected_signer_key_lineage_fingerprint text,
 p_expected_subject_public_key_info_der bytea,p_expected_signature_bytes bytea,p_expected_signer_authority_id uuid,
 p_expected_signer_authority_revision integer,p_expected_signer_authority_fingerprint text,p_expected_verified_at timestamptz,
 p_expected_accepted_proof_fingerprint text,p_expected_evidence_binding_fingerprint text
) RETURNS TABLE(outcome text,result_operation_id uuid,result_intent_fingerprint text,result_receipt_fingerprint text,result_effect_time timestamptz(6))
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$DECLARE
 org_status text; op public.command_authority_operation%ROWTYPE; principal public.command_principal%ROWTYPE;
 a public.s2a_accepted_attestation%ROWTYPE; k public.s2a_signer_key_revision%ROWTYPE;
 au public.s2a_signer_authority_revision%ROWTYPE; snapshot record; reconstructed bytea; reconstructed_digest text;
 current_evidence text; computed_intent text; computed_receipt text; resource text; key_leaf_count integer;
 authority_leaf_count integer; ml_count bigint; omie_count bigint; effectTime timestamptz(6);
BEGIN
 SELECT o.status INTO org_status FROM public.integration_organization o
  WHERE o.organization_id=p_organization_id FOR SHARE;
 IF NOT FOUND THEN RAISE EXCEPTION 'Governance unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE'; END IF;
 PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(
  'command-authority-operation/1:'||p_organization_id||':'||p_operation_id,0));
 SELECT * INTO op FROM public.command_authority_operation o
  WHERE o.organization_id=p_organization_id AND o.operation_id=p_operation_id;
 IF FOUND THEN
  IF op.operation IS DISTINCT FROM 'PRINCIPAL' OR op.principal_id IS DISTINCT FROM p_principal_id OR op.attestation_manifest_id IS DISTINCT FROM p_manifest_id
   OR op.correlation_id IS DISTINCT FROM p_correlation_id OR op.credential_id IS NOT NULL OR op.credential_revision IS NOT NULL
   OR op.grant_id IS NOT NULL OR op.grant_revision IS NOT NULL OR op.permission IS NOT NULL OR op.state IS NOT NULL THEN
   RAISE EXCEPTION 'Historical operation integrity failure' USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE';
  END IF;
  SELECT * INTO principal FROM public.command_principal p WHERE p.organization_id=p_organization_id AND p.principal_id=p_principal_id;
  IF NOT FOUND OR principal.mercado_livre_connection_id IS DISTINCT FROM p_mercado_livre_connection_id
   OR principal.omie_connection_id IS DISTINCT FROM p_omie_connection_id OR principal.reason IS DISTINCT FROM p_reason
   OR principal.provenance IS DISTINCT FROM p_provenance OR principal.correlation_id IS DISTINCT FROM p_correlation_id
   OR principal.decided_at IS DISTINCT FROM op.decided_at THEN
   RAISE EXCEPTION 'Historical principal integrity failure' USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE';
  END IF;
  SELECT * INTO a FROM public.s2a_accepted_attestation x WHERE x.organization_id=p_organization_id AND x.manifest_id=p_manifest_id;
  IF NOT FOUND OR NOT EXISTS (SELECT 1 FROM public.s2a_attestation_consumption c
    WHERE c.organization_id=p_organization_id AND c.manifest_id=p_manifest_id AND c.principal_id=p_principal_id
      AND c.manifest_digest=a.manifest_digest AND c.correlation_id=p_correlation_id AND c.consumed_at=op.decided_at) THEN
   RAISE EXCEPTION 'Historical consumption integrity failure' USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE';
  END IF;
  SELECT * INTO snapshot FROM public.s2a_v042_revalidate_snapshot(p_organization_id,p_manifest_id,p_schema_version,p_claim_manifest_id,
   p_claim_organization_id,p_mercado_livre_connection_id,p_omie_connection_id,p_source_order_reference,p_integration_reference,p_marketplace_order_id,
   p_permission,p_accountable_operator,p_approval_source,p_approval_window_start,p_approval_window_end,p_revocation_owner,p_credential_custodian,
   p_credential_delivery_method,p_credential_rotation_owner,p_immediate_revocation_policy,p_reason,p_provenance,p_correlation_id,p_evidence_binding_fingerprint,
   p_expected_artifact_version,p_expected_canonicalization_version,p_expected_canonical_manifest_bytes,p_expected_manifest_digest,
   p_expected_signature_preimage_bytes,p_expected_algorithm_id,p_expected_signer_subject_id,p_expected_signer_key_id,
   p_expected_signer_key_revision,p_expected_signer_key_fingerprint,p_expected_signer_key_lineage_fingerprint,
   p_expected_subject_public_key_info_der,p_expected_signature_bytes,p_expected_signer_authority_id,
   p_expected_signer_authority_revision,p_expected_signer_authority_fingerprint,p_expected_verified_at,
   p_expected_accepted_proof_fingerprint,p_expected_evidence_binding_fingerprint);
  computed_intent:=public.s2a_v042_authority_intent('PRINCIPAL',p_operation_id,p_organization_id,p_principal_id,
   p_mercado_livre_connection_id,p_omie_connection_id,NULL,NULL,NULL,p_reason,p_provenance,p_correlation_id,
   p_manifest_id,snapshot.result_accepted_proof_fingerprint,snapshot.result_manifest_digest);
  computed_receipt:=public.s2a_v042_authority_receipt(computed_intent,'PRINCIPAL',p_principal_id,NULL,NULL,NULL,NULL,NULL,NULL);
  IF op.intent_fingerprint IS DISTINCT FROM computed_intent OR op.receipt_fingerprint IS DISTINCT FROM computed_receipt THEN
   RAISE EXCEPTION 'Historical operation fingerprint integrity failure' USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE';
  END IF;
  RETURN QUERY SELECT 'ALREADY_APPLIED'::text,op.operation_id,computed_intent,computed_receipt,op.decided_at::timestamptz(6);
  RETURN;
 END IF; IF org_status<>'ACTIVE' THEN RAISE EXCEPTION 'Organization inactive' USING ERRCODE='P0017',DETAIL='EXPIRED_OR_NOT_YET_VALID'; END IF;
 IF p_claim_organization_id<>p_organization_id OR p_claim_manifest_id<>p_manifest_id OR p_permission<>'TRANSACTION_IDENTITY_DECISION_WRITE' THEN
  RAISE EXCEPTION 'Claim scope mismatch' USING ERRCODE='P0017',DETAIL='SCOPE_MISMATCH';
 END IF;
 PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(
  'command-authority-principal/1:'||p_organization_id||':'||p_principal_id,0));
 SELECT * INTO principal FROM public.command_principal p WHERE p.organization_id=p_organization_id AND p.principal_id=p_principal_id FOR UPDATE;
 IF FOUND THEN RAISE EXCEPTION 'Principal already exists' USING ERRCODE='P0016',DETAIL='GOVERNANCE_CONFLICT'; END IF;
 SELECT * INTO a FROM public.s2a_accepted_attestation x WHERE x.organization_id=p_organization_id AND x.manifest_id=p_manifest_id;
 IF NOT FOUND THEN RAISE EXCEPTION 'Accepted artifact unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE'; END IF;
 reconstructed:=public.s2a_v041_manifest_bytes(p_schema_version,p_claim_manifest_id,p_claim_organization_id,
  p_mercado_livre_connection_id,p_omie_connection_id,p_source_order_reference,p_integration_reference,p_marketplace_order_id,
  p_permission,p_accountable_operator,p_approval_source,p_approval_window_start,p_approval_window_end,p_revocation_owner,
  p_credential_custodian,p_credential_delivery_method,p_credential_rotation_owner,p_immediate_revocation_policy,p_reason,p_provenance,
  p_correlation_id,p_evidence_binding_fingerprint);
 reconstructed_digest:=encode(sha256(reconstructed),'hex');
  IF reconstructed IS DISTINCT FROM a.canonical_manifest_bytes OR reconstructed_digest IS DISTINCT FROM a.manifest_digest THEN
  RAISE EXCEPTION 'Accepted artifact integrity failure' USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE';
 END IF;
 PERFORM 1 FROM public.integration_connector_progress cp WHERE cp.organization_id=p_organization_id
  AND cp.connection_id=p_omie_connection_id AND cp.capability='marketplace-economic.omie-transaction-evidence.reacquisition-v3' FOR UPDATE;
 IF NOT FOUND THEN RAISE EXCEPTION 'Evidence unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE'; END IF;
 FOR resource IN SELECT unnest(ARRAY[
  'transaction-identity/subject/1:'||p_organization_id||':'||p_omie_connection_id||':'||octet_length(p_source_order_reference)||':'||p_source_order_reference,
  'transaction-identity/target/1:'||p_organization_id||':'||p_marketplace_order_id]) ORDER BY 1 LOOP
  PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(resource,0));
 END LOOP;
 PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(
  's2a-attestation/manifest/1:'||p_organization_id||':'||p_manifest_id,0));
 SELECT * INTO a FROM public.s2a_accepted_attestation x WHERE x.organization_id=p_organization_id AND x.manifest_id=p_manifest_id;
 IF NOT FOUND THEN RAISE EXCEPTION 'Accepted artifact unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE'; END IF;
 SELECT * INTO snapshot FROM public.s2a_v042_revalidate_snapshot(p_organization_id,p_manifest_id,p_schema_version,p_claim_manifest_id,
  p_claim_organization_id,p_mercado_livre_connection_id,p_omie_connection_id,p_source_order_reference,p_integration_reference,p_marketplace_order_id,
  p_permission,p_accountable_operator,p_approval_source,p_approval_window_start,p_approval_window_end,p_revocation_owner,p_credential_custodian,
  p_credential_delivery_method,p_credential_rotation_owner,p_immediate_revocation_policy,p_reason,p_provenance,p_correlation_id,p_evidence_binding_fingerprint,
  p_expected_artifact_version,p_expected_canonicalization_version,p_expected_canonical_manifest_bytes,p_expected_manifest_digest,p_expected_signature_preimage_bytes,p_expected_algorithm_id,
  p_expected_signer_subject_id,p_expected_signer_key_id,p_expected_signer_key_revision,p_expected_signer_key_fingerprint,p_expected_signer_key_lineage_fingerprint,p_expected_subject_public_key_info_der,p_expected_signature_bytes,
  p_expected_signer_authority_id,p_expected_signer_authority_revision,p_expected_signer_authority_fingerprint,p_expected_verified_at,p_expected_accepted_proof_fingerprint,p_expected_evidence_binding_fingerprint);

effectTime:=clock_timestamp()::timestamptz(6);
SELECT o.status INTO org_status FROM public.integration_organization o WHERE o.organization_id=p_organization_id FOR SHARE;
IF NOT FOUND THEN RAISE EXCEPTION 'Governance unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE'; END IF;
IF org_status<>'ACTIVE' THEN RAISE EXCEPTION 'Organization inactive' USING ERRCODE='P0017',DETAIL='EXPIRED_OR_NOT_YET_VALID'; END IF;
IF effectTime<p_approval_window_start OR effectTime>=p_approval_window_end THEN RAISE EXCEPTION 'Approval window denied' USING ERRCODE='P0017',DETAIL='EXPIRED_OR_NOT_YET_VALID'; END IF;
PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended('s2a-governance/signer-key/1:'||p_organization_id||':'||snapshot.result_signer_key_id,0));
SELECT * INTO k FROM public.s2a_signer_key_revision x WHERE x.organization_id=p_organization_id AND x.signer_key_id=snapshot.result_signer_key_id AND x.effective_at<=effectTime ORDER BY x.revision DESC LIMIT 1;
IF NOT FOUND THEN RAISE EXCEPTION 'Signer key unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE'; END IF;
IF k.state<>'ACTIVE' OR k.valid_from>effectTime THEN RAISE EXCEPTION 'Signer key ineligible' USING ERRCODE='P0017',DETAIL='EXPIRED_OR_NOT_YET_VALID'; END IF;
IF k.signer_subject_id IS DISTINCT FROM snapshot.result_signer_subject_id OR k.algorithm_id IS DISTINCT FROM snapshot.result_algorithm_id OR k.subject_public_key_info_der IS DISTINCT FROM snapshot.result_subject_public_key_info_der OR k.signer_key_fingerprint IS DISTINCT FROM snapshot.result_signer_key_fingerprint THEN RAISE EXCEPTION 'Signer key scope mismatch' USING ERRCODE='P0017',DETAIL='SCOPE_MISMATCH'; END IF;
PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended('s2a-governance/signer-authority-scope/1:'||p_organization_id||':'||snapshot.result_signer_subject_id||':'||snapshot.result_signer_key_id||':S2A_FIELD_PROOF_APPROVAL:TRANSACTION_IDENTITY_DECISION_WRITE',0));
SELECT count(*) INTO authority_leaf_count FROM public.s2a_signer_authority_revision x WHERE x.organization_id=p_organization_id AND x.signer_subject_id=snapshot.result_signer_subject_id AND x.signer_key_id=snapshot.result_signer_key_id AND x.approval_action='S2A_FIELD_PROOF_APPROVAL' AND x.permission='TRANSACTION_IDENTITY_DECISION_WRITE' AND NOT EXISTS(SELECT 1 FROM public.s2a_signer_authority_revision n WHERE n.organization_id=x.organization_id AND n.supersedes_signer_authority_id=x.signer_authority_id);
IF authority_leaf_count=0 THEN RAISE EXCEPTION 'Signer authority unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE'; END IF;
IF authority_leaf_count<>1 THEN RAISE EXCEPTION 'Signer authority conflict' USING ERRCODE='P0016',DETAIL='GOVERNANCE_CONFLICT'; END IF;
SELECT * INTO au FROM public.s2a_signer_authority_revision x WHERE x.organization_id=p_organization_id AND x.signer_subject_id=snapshot.result_signer_subject_id AND x.signer_key_id=snapshot.result_signer_key_id AND x.approval_action='S2A_FIELD_PROOF_APPROVAL' AND x.permission='TRANSACTION_IDENTITY_DECISION_WRITE' AND NOT EXISTS(SELECT 1 FROM public.s2a_signer_authority_revision n WHERE n.organization_id=x.organization_id AND n.supersedes_signer_authority_id=x.signer_authority_id);
IF au.signer_key_revision IS DISTINCT FROM k.revision OR au.signer_key_fingerprint IS DISTINCT FROM k.signer_key_fingerprint THEN RAISE EXCEPTION 'Authority key scope mismatch' USING ERRCODE='P0017',DETAIL='SCOPE_MISMATCH'; END IF;
IF au.state<>'ENABLED' OR au.valid_from>effectTime OR effectTime>=au.valid_until THEN RAISE EXCEPTION 'Authority ineligible' USING ERRCODE='P0017',DETAIL='EXPIRED_OR_NOT_YET_VALID'; END IF;
current_evidence:=public.s2a_v041_evidence_fingerprint(p_organization_id,p_marketplace_order_id,p_mercado_livre_connection_id,p_omie_connection_id,p_source_order_reference,p_integration_reference);
IF current_evidence IS DISTINCT FROM snapshot.result_signed_evidence_binding_fingerprint THEN RAISE EXCEPTION 'Evidence scope mismatch' USING ERRCODE='P0017',DETAIL='SCOPE_MISMATCH'; END IF;
SELECT * INTO principal FROM public.command_principal p WHERE p.organization_id=p_organization_id AND p.principal_id=p_principal_id;
IF FOUND THEN RAISE EXCEPTION 'Principal collision' USING ERRCODE='P0016',DETAIL='GOVERNANCE_CONFLICT'; END IF;
IF EXISTS(SELECT 1 FROM public.s2a_attestation_consumption c WHERE c.organization_id=p_organization_id AND c.manifest_id=p_manifest_id) THEN RAISE EXCEPTION 'Consumption collision' USING ERRCODE='P0016',DETAIL='GOVERNANCE_CONFLICT'; END IF;
computed_intent:=public.s2a_v042_authority_intent('PRINCIPAL',p_operation_id,p_organization_id,p_principal_id,p_mercado_livre_connection_id,p_omie_connection_id,NULL,NULL,NULL,p_reason,p_provenance,p_correlation_id,p_manifest_id,snapshot.result_accepted_proof_fingerprint,snapshot.result_manifest_digest);
computed_receipt:=public.s2a_v042_authority_receipt(computed_intent,'PRINCIPAL',p_principal_id,NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO public.command_principal(organization_id,principal_id,mercado_livre_connection_id,omie_connection_id,reason,provenance,correlation_id,decided_at)
VALUES(p_organization_id,p_principal_id,p_mercado_livre_connection_id,p_omie_connection_id,p_reason,p_provenance,p_correlation_id,effectTime);
INSERT INTO public.s2a_attestation_consumption(organization_id,manifest_id,manifest_digest,principal_id,correlation_id,consumed_at)
VALUES(p_organization_id,p_manifest_id,snapshot.result_manifest_digest,p_principal_id,p_correlation_id,effectTime);
INSERT INTO public.command_authority_operation(organization_id,operation_id,operation,principal_id,credential_id,credential_revision,grant_id,grant_revision,permission,state,intent_fingerprint,receipt_fingerprint,correlation_id,decided_at,attestation_manifest_id)
VALUES(p_organization_id,p_operation_id,'PRINCIPAL',p_principal_id,NULL,NULL,NULL,NULL,NULL,NULL,computed_intent,computed_receipt,p_correlation_id,effectTime,p_manifest_id);
RETURN QUERY SELECT 'APPLIED',p_operation_id,computed_intent,computed_receipt,effectTime;
END $$;
CREATE FUNCTION public.s2a_v042_apply_attested_initial_credential(
 p_organization_id uuid,p_manifest_id uuid,p_operation_id uuid,p_principal_id uuid,p_credential_id uuid,p_secret_verifier bytea,
 p_schema_version integer,p_claim_manifest_id uuid,p_claim_organization_id uuid,p_mercado_livre_connection_id uuid,
 p_omie_connection_id uuid,p_source_order_reference text,p_integration_reference text,p_marketplace_order_id uuid,
 p_permission text,p_accountable_operator uuid,p_approval_source uuid,p_approval_window_start timestamptz,
 p_approval_window_end timestamptz,p_revocation_owner uuid,p_credential_custodian uuid,p_credential_delivery_method text,
 p_credential_rotation_owner uuid,p_immediate_revocation_policy text,p_reason text,p_provenance text,p_correlation_id uuid,
 p_evidence_binding_fingerprint text,p_expected_artifact_version integer,p_expected_canonicalization_version integer,
 p_expected_canonical_manifest_bytes bytea,p_expected_manifest_digest text,p_expected_signature_preimage_bytes bytea,
 p_expected_algorithm_id text,p_expected_signer_subject_id uuid,p_expected_signer_key_id uuid,
 p_expected_signer_key_revision integer,p_expected_signer_key_fingerprint text,p_expected_signer_key_lineage_fingerprint text,
 p_expected_subject_public_key_info_der bytea,p_expected_signature_bytes bytea,p_expected_signer_authority_id uuid,
 p_expected_signer_authority_revision integer,p_expected_signer_authority_fingerprint text,p_expected_verified_at timestamptz,
 p_expected_accepted_proof_fingerprint text,p_expected_evidence_binding_fingerprint text
) RETURNS TABLE(outcome text,result_operation_id uuid,result_intent_fingerprint text,result_receipt_fingerprint text,result_effect_time timestamptz(6))
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$DECLARE
 org_status text; op public.command_authority_operation%ROWTYPE; principal public.command_principal%ROWTYPE;
 credential public.command_credential_revision%ROWTYPE; a public.s2a_accepted_attestation%ROWTYPE; k public.s2a_signer_key_revision%ROWTYPE;
 au public.s2a_signer_authority_revision%ROWTYPE; snapshot record; reconstructed bytea; reconstructed_digest text;
 current_evidence text; computed_intent text; computed_receipt text; resource text; key_leaf_count integer;
 authority_leaf_count integer; ml_count bigint; omie_count bigint; effectTime timestamptz(6);
BEGIN
 SELECT o.status INTO org_status FROM public.integration_organization o
  WHERE o.organization_id=p_organization_id FOR SHARE;
 IF NOT FOUND THEN RAISE EXCEPTION 'Governance unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE'; END IF;
 PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(
  'command-authority-operation/1:'||p_organization_id||':'||p_operation_id,0));
 SELECT * INTO op FROM public.command_authority_operation o
  WHERE o.organization_id=p_organization_id AND o.operation_id=p_operation_id;
 IF FOUND THEN
  IF op.operation IS DISTINCT FROM 'INITIAL_CREDENTIAL' OR op.principal_id IS DISTINCT FROM p_principal_id
   OR op.credential_id IS DISTINCT FROM p_credential_id OR op.credential_revision IS DISTINCT FROM 1
   OR op.grant_id IS NOT NULL OR op.grant_revision IS NOT NULL OR op.permission IS NOT NULL OR op.state IS DISTINCT FROM 'ENABLED'
   OR op.attestation_manifest_id IS DISTINCT FROM p_manifest_id OR op.correlation_id IS DISTINCT FROM p_correlation_id THEN
   RAISE EXCEPTION 'Historical operation integrity failure' USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE';
  END IF;
  SELECT * INTO principal FROM public.command_principal p WHERE p.organization_id=p_organization_id AND p.principal_id=p_principal_id;
  IF NOT FOUND OR principal.mercado_livre_connection_id IS DISTINCT FROM p_mercado_livre_connection_id
   OR principal.omie_connection_id IS DISTINCT FROM p_omie_connection_id THEN
   RAISE EXCEPTION 'Historical principal integrity failure' USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE';
  END IF;
  SELECT * INTO credential FROM public.command_credential_revision c
   WHERE c.organization_id=p_organization_id AND c.credential_id=p_credential_id AND c.revision=1;
  IF NOT FOUND OR credential.principal_id IS DISTINCT FROM p_principal_id OR credential.supersedes_revision IS NOT NULL
   OR credential.state IS DISTINCT FROM 'ENABLED' OR credential.secret_verifier IS DISTINCT FROM p_secret_verifier
   OR credential.reason IS DISTINCT FROM p_reason OR credential.provenance IS DISTINCT FROM p_provenance
   OR credential.correlation_id IS DISTINCT FROM p_correlation_id OR credential.decided_at IS DISTINCT FROM op.decided_at THEN
   RAISE EXCEPTION 'Historical credential integrity failure' USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE';
  END IF;
  SELECT * INTO a FROM public.s2a_accepted_attestation x WHERE x.organization_id=p_organization_id AND x.manifest_id=p_manifest_id;
  IF NOT FOUND OR NOT EXISTS (SELECT 1 FROM public.s2a_attestation_consumption c
    WHERE c.organization_id=p_organization_id AND c.manifest_id=p_manifest_id AND c.principal_id=p_principal_id
      AND c.manifest_digest=a.manifest_digest AND c.correlation_id=p_correlation_id) THEN
   RAISE EXCEPTION 'Historical consumption integrity failure' USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE';
  END IF;
  SELECT * INTO snapshot FROM public.s2a_v042_revalidate_snapshot(p_organization_id,p_manifest_id,p_schema_version,p_claim_manifest_id,
   p_claim_organization_id,p_mercado_livre_connection_id,p_omie_connection_id,p_source_order_reference,p_integration_reference,p_marketplace_order_id,
   p_permission,p_accountable_operator,p_approval_source,p_approval_window_start,p_approval_window_end,p_revocation_owner,p_credential_custodian,
   p_credential_delivery_method,p_credential_rotation_owner,p_immediate_revocation_policy,p_reason,p_provenance,p_correlation_id,p_evidence_binding_fingerprint,
   p_expected_artifact_version,p_expected_canonicalization_version,p_expected_canonical_manifest_bytes,p_expected_manifest_digest,
   p_expected_signature_preimage_bytes,p_expected_algorithm_id,p_expected_signer_subject_id,p_expected_signer_key_id,
   p_expected_signer_key_revision,p_expected_signer_key_fingerprint,p_expected_signer_key_lineage_fingerprint,
   p_expected_subject_public_key_info_der,p_expected_signature_bytes,p_expected_signer_authority_id,
   p_expected_signer_authority_revision,p_expected_signer_authority_fingerprint,p_expected_verified_at,
   p_expected_accepted_proof_fingerprint,p_expected_evidence_binding_fingerprint);
  computed_intent:=public.s2a_v042_authority_intent('INITIAL_CREDENTIAL',p_operation_id,p_organization_id,p_principal_id,
   NULL,NULL,p_credential_id,p_secret_verifier,NULL,p_reason,p_provenance,p_correlation_id,
   p_manifest_id,snapshot.result_accepted_proof_fingerprint,snapshot.result_manifest_digest);
  computed_receipt:=public.s2a_v042_authority_receipt(computed_intent,'INITIAL_CREDENTIAL',p_principal_id,p_credential_id,1,NULL,NULL,NULL,'ENABLED');
  IF op.intent_fingerprint IS DISTINCT FROM computed_intent OR op.receipt_fingerprint IS DISTINCT FROM computed_receipt THEN
   RAISE EXCEPTION 'Historical operation fingerprint integrity failure' USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE';
  END IF;
  RETURN QUERY SELECT 'ALREADY_APPLIED'::text,op.operation_id,computed_intent,computed_receipt,op.decided_at::timestamptz(6);
  RETURN;
 END IF; IF org_status<>'ACTIVE' THEN RAISE EXCEPTION 'Organization inactive' USING ERRCODE='P0017',DETAIL='EXPIRED_OR_NOT_YET_VALID'; END IF;
 IF p_claim_organization_id<>p_organization_id OR p_claim_manifest_id<>p_manifest_id OR p_permission<>'TRANSACTION_IDENTITY_DECISION_WRITE' THEN
  RAISE EXCEPTION 'Claim scope mismatch' USING ERRCODE='P0017',DETAIL='SCOPE_MISMATCH';
 END IF;
 PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(
  'command-authority-principal/1:'||p_organization_id||':'||p_principal_id,0));
 SELECT * INTO principal FROM public.command_principal p WHERE p.organization_id=p_organization_id AND p.principal_id=p_principal_id FOR UPDATE;
 IF NOT FOUND THEN RAISE EXCEPTION 'Principal unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE'; END IF;
 IF principal.mercado_livre_connection_id IS DISTINCT FROM p_mercado_livre_connection_id
  OR principal.omie_connection_id IS DISTINCT FROM p_omie_connection_id THEN
  RAISE EXCEPTION 'Principal scope mismatch' USING ERRCODE='P0017',DETAIL='SCOPE_MISMATCH';
 END IF;
 IF octet_length(p_secret_verifier) IS DISTINCT FROM 32 THEN
  RAISE EXCEPTION 'Credential verifier shape invalid' USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE';
 END IF;
 IF EXISTS (SELECT 1 FROM public.s2a_attestation_consumption c
   WHERE c.organization_id=p_organization_id AND c.manifest_id=p_manifest_id AND c.principal_id IS DISTINCT FROM p_principal_id) THEN
  RAISE EXCEPTION 'Consumption principal scope mismatch' USING ERRCODE='P0017',DETAIL='SCOPE_MISMATCH';
 END IF;
 IF NOT EXISTS (SELECT 1 FROM public.s2a_attestation_consumption c
   WHERE c.organization_id=p_organization_id AND c.manifest_id=p_manifest_id AND c.principal_id=p_principal_id
     AND c.correlation_id=p_correlation_id) THEN
  RAISE EXCEPTION 'Consumption unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE';
 END IF;
 SELECT * INTO a FROM public.s2a_accepted_attestation x WHERE x.organization_id=p_organization_id AND x.manifest_id=p_manifest_id;
 IF NOT FOUND THEN RAISE EXCEPTION 'Accepted artifact unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE'; END IF;
 IF NOT EXISTS (SELECT 1 FROM public.s2a_attestation_consumption c
   WHERE c.organization_id=p_organization_id AND c.manifest_id=p_manifest_id AND c.principal_id=p_principal_id
     AND c.manifest_digest=a.manifest_digest AND c.correlation_id=p_correlation_id) THEN
  RAISE EXCEPTION 'Consumption integrity failure' USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE';
 END IF;
 reconstructed:=public.s2a_v041_manifest_bytes(p_schema_version,p_claim_manifest_id,p_claim_organization_id,
  p_mercado_livre_connection_id,p_omie_connection_id,p_source_order_reference,p_integration_reference,p_marketplace_order_id,
  p_permission,p_accountable_operator,p_approval_source,p_approval_window_start,p_approval_window_end,p_revocation_owner,
  p_credential_custodian,p_credential_delivery_method,p_credential_rotation_owner,p_immediate_revocation_policy,p_reason,p_provenance,
  p_correlation_id,p_evidence_binding_fingerprint);
 reconstructed_digest:=encode(sha256(reconstructed),'hex');
  IF reconstructed IS DISTINCT FROM a.canonical_manifest_bytes OR reconstructed_digest IS DISTINCT FROM a.manifest_digest THEN
  RAISE EXCEPTION 'Accepted artifact integrity failure' USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE';
 END IF;
 PERFORM 1 FROM public.integration_connector_progress cp WHERE cp.organization_id=p_organization_id
  AND cp.connection_id=p_omie_connection_id AND cp.capability='marketplace-economic.omie-transaction-evidence.reacquisition-v3' FOR UPDATE;
 IF NOT FOUND THEN RAISE EXCEPTION 'Evidence unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE'; END IF;
 FOR resource IN SELECT unnest(ARRAY[
  'transaction-identity/subject/1:'||p_organization_id||':'||p_omie_connection_id||':'||octet_length(p_source_order_reference)||':'||p_source_order_reference,
  'transaction-identity/target/1:'||p_organization_id||':'||p_marketplace_order_id]) ORDER BY 1 LOOP
  PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(resource,0));
 END LOOP;
 PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(
  's2a-attestation/manifest/1:'||p_organization_id||':'||p_manifest_id,0));
 SELECT * INTO a FROM public.s2a_accepted_attestation x WHERE x.organization_id=p_organization_id AND x.manifest_id=p_manifest_id;
 IF NOT FOUND THEN RAISE EXCEPTION 'Accepted artifact unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE'; END IF;
 SELECT * INTO snapshot FROM public.s2a_v042_revalidate_snapshot(p_organization_id,p_manifest_id,p_schema_version,p_claim_manifest_id,
  p_claim_organization_id,p_mercado_livre_connection_id,p_omie_connection_id,p_source_order_reference,p_integration_reference,p_marketplace_order_id,
  p_permission,p_accountable_operator,p_approval_source,p_approval_window_start,p_approval_window_end,p_revocation_owner,p_credential_custodian,
  p_credential_delivery_method,p_credential_rotation_owner,p_immediate_revocation_policy,p_reason,p_provenance,p_correlation_id,p_evidence_binding_fingerprint,
  p_expected_artifact_version,p_expected_canonicalization_version,p_expected_canonical_manifest_bytes,p_expected_manifest_digest,p_expected_signature_preimage_bytes,p_expected_algorithm_id,
  p_expected_signer_subject_id,p_expected_signer_key_id,p_expected_signer_key_revision,p_expected_signer_key_fingerprint,p_expected_signer_key_lineage_fingerprint,p_expected_subject_public_key_info_der,p_expected_signature_bytes,
  p_expected_signer_authority_id,p_expected_signer_authority_revision,p_expected_signer_authority_fingerprint,p_expected_verified_at,p_expected_accepted_proof_fingerprint,p_expected_evidence_binding_fingerprint);

effectTime:=clock_timestamp()::timestamptz(6);
SELECT o.status INTO org_status FROM public.integration_organization o WHERE o.organization_id=p_organization_id FOR SHARE;
IF NOT FOUND THEN RAISE EXCEPTION 'Governance unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE'; END IF;
IF org_status<>'ACTIVE' THEN RAISE EXCEPTION 'Organization inactive' USING ERRCODE='P0017',DETAIL='EXPIRED_OR_NOT_YET_VALID'; END IF;
IF effectTime<p_approval_window_start OR effectTime>=p_approval_window_end THEN RAISE EXCEPTION 'Approval window denied' USING ERRCODE='P0017',DETAIL='EXPIRED_OR_NOT_YET_VALID'; END IF;
PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended('s2a-governance/signer-key/1:'||p_organization_id||':'||snapshot.result_signer_key_id,0));
SELECT * INTO k FROM public.s2a_signer_key_revision x WHERE x.organization_id=p_organization_id AND x.signer_key_id=snapshot.result_signer_key_id AND x.effective_at<=effectTime ORDER BY x.revision DESC LIMIT 1;
IF NOT FOUND THEN RAISE EXCEPTION 'Signer key unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE'; END IF;
IF k.state<>'ACTIVE' OR k.valid_from>effectTime THEN RAISE EXCEPTION 'Signer key ineligible' USING ERRCODE='P0017',DETAIL='EXPIRED_OR_NOT_YET_VALID'; END IF;
IF k.signer_subject_id IS DISTINCT FROM snapshot.result_signer_subject_id OR k.algorithm_id IS DISTINCT FROM snapshot.result_algorithm_id OR k.subject_public_key_info_der IS DISTINCT FROM snapshot.result_subject_public_key_info_der OR k.signer_key_fingerprint IS DISTINCT FROM snapshot.result_signer_key_fingerprint THEN RAISE EXCEPTION 'Signer key scope mismatch' USING ERRCODE='P0017',DETAIL='SCOPE_MISMATCH'; END IF;
PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended('s2a-governance/signer-authority-scope/1:'||p_organization_id||':'||snapshot.result_signer_subject_id||':'||snapshot.result_signer_key_id||':S2A_FIELD_PROOF_APPROVAL:TRANSACTION_IDENTITY_DECISION_WRITE',0));
SELECT count(*) INTO authority_leaf_count FROM public.s2a_signer_authority_revision x WHERE x.organization_id=p_organization_id AND x.signer_subject_id=snapshot.result_signer_subject_id AND x.signer_key_id=snapshot.result_signer_key_id AND x.approval_action='S2A_FIELD_PROOF_APPROVAL' AND x.permission='TRANSACTION_IDENTITY_DECISION_WRITE' AND NOT EXISTS(SELECT 1 FROM public.s2a_signer_authority_revision n WHERE n.organization_id=x.organization_id AND n.supersedes_signer_authority_id=x.signer_authority_id);
IF authority_leaf_count=0 THEN RAISE EXCEPTION 'Signer authority unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE'; END IF;
IF authority_leaf_count<>1 THEN RAISE EXCEPTION 'Signer authority conflict' USING ERRCODE='P0016',DETAIL='GOVERNANCE_CONFLICT'; END IF;
SELECT * INTO au FROM public.s2a_signer_authority_revision x WHERE x.organization_id=p_organization_id AND x.signer_subject_id=snapshot.result_signer_subject_id AND x.signer_key_id=snapshot.result_signer_key_id AND x.approval_action='S2A_FIELD_PROOF_APPROVAL' AND x.permission='TRANSACTION_IDENTITY_DECISION_WRITE' AND NOT EXISTS(SELECT 1 FROM public.s2a_signer_authority_revision n WHERE n.organization_id=x.organization_id AND n.supersedes_signer_authority_id=x.signer_authority_id);
IF au.signer_key_revision IS DISTINCT FROM k.revision OR au.signer_key_fingerprint IS DISTINCT FROM k.signer_key_fingerprint THEN RAISE EXCEPTION 'Authority key scope mismatch' USING ERRCODE='P0017',DETAIL='SCOPE_MISMATCH'; END IF;
IF au.state<>'ENABLED' OR au.valid_from>effectTime OR effectTime>=au.valid_until THEN RAISE EXCEPTION 'Authority ineligible' USING ERRCODE='P0017',DETAIL='EXPIRED_OR_NOT_YET_VALID'; END IF;
current_evidence:=public.s2a_v041_evidence_fingerprint(p_organization_id,p_marketplace_order_id,p_mercado_livre_connection_id,p_omie_connection_id,p_source_order_reference,p_integration_reference);
IF current_evidence IS DISTINCT FROM snapshot.result_signed_evidence_binding_fingerprint THEN RAISE EXCEPTION 'Evidence scope mismatch' USING ERRCODE='P0017',DETAIL='SCOPE_MISMATCH'; END IF;
SELECT * INTO principal FROM public.command_principal p WHERE p.organization_id=p_organization_id AND p.principal_id=p_principal_id;
IF NOT FOUND THEN RAISE EXCEPTION 'Principal unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE'; END IF;
IF principal.mercado_livre_connection_id IS DISTINCT FROM p_mercado_livre_connection_id OR principal.omie_connection_id IS DISTINCT FROM p_omie_connection_id THEN RAISE EXCEPTION 'Principal scope mismatch' USING ERRCODE='P0017',DETAIL='SCOPE_MISMATCH'; END IF;
IF NOT EXISTS(SELECT 1 FROM public.s2a_attestation_consumption c WHERE c.organization_id=p_organization_id AND c.manifest_id=p_manifest_id AND c.principal_id=p_principal_id AND c.manifest_digest=snapshot.result_manifest_digest AND c.correlation_id=p_correlation_id) THEN RAISE EXCEPTION 'Consumption lineage unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE'; END IF;
IF EXISTS(SELECT 1 FROM public.command_credential_revision c WHERE c.organization_id=p_organization_id AND (c.credential_id=p_credential_id OR c.principal_id=p_principal_id)) THEN RAISE EXCEPTION 'Initial credential collision' USING ERRCODE='P0016',DETAIL='GOVERNANCE_CONFLICT'; END IF;
IF EXISTS(SELECT 1 FROM public.command_authority_operation o WHERE o.organization_id=p_organization_id AND o.attestation_manifest_id=p_manifest_id AND o.operation='INITIAL_CREDENTIAL') THEN RAISE EXCEPTION 'Initial credential operation collision' USING ERRCODE='P0016',DETAIL='GOVERNANCE_CONFLICT'; END IF;
computed_intent:=public.s2a_v042_authority_intent('INITIAL_CREDENTIAL',p_operation_id,p_organization_id,p_principal_id,NULL,NULL,p_credential_id,p_secret_verifier,NULL,p_reason,p_provenance,p_correlation_id,p_manifest_id,snapshot.result_accepted_proof_fingerprint,snapshot.result_manifest_digest);
computed_receipt:=public.s2a_v042_authority_receipt(computed_intent,'INITIAL_CREDENTIAL',p_principal_id,p_credential_id,1,NULL,NULL,NULL,'ENABLED');
INSERT INTO public.command_credential_revision(organization_id,principal_id,credential_id,revision,supersedes_revision,state,secret_verifier,reason,provenance,correlation_id,decided_at)
VALUES(p_organization_id,p_principal_id,p_credential_id,1,NULL,'ENABLED',p_secret_verifier,p_reason,p_provenance,p_correlation_id,effectTime);
INSERT INTO public.command_authority_operation(organization_id,operation_id,operation,principal_id,credential_id,credential_revision,grant_id,grant_revision,permission,state,intent_fingerprint,receipt_fingerprint,correlation_id,decided_at,attestation_manifest_id)
VALUES(p_organization_id,p_operation_id,'INITIAL_CREDENTIAL',p_principal_id,p_credential_id,1,NULL,NULL,NULL,'ENABLED',computed_intent,computed_receipt,p_correlation_id,effectTime,p_manifest_id);
RETURN QUERY SELECT 'APPLIED',p_operation_id,computed_intent,computed_receipt,effectTime;
END $$;
CREATE FUNCTION public.s2a_v042_apply_attested_grant(
 p_organization_id uuid,p_manifest_id uuid,p_operation_id uuid,p_principal_id uuid,p_grant_id uuid,
 p_schema_version integer,p_claim_manifest_id uuid,p_claim_organization_id uuid,p_mercado_livre_connection_id uuid,
 p_omie_connection_id uuid,p_source_order_reference text,p_integration_reference text,p_marketplace_order_id uuid,
 p_permission text,p_accountable_operator uuid,p_approval_source uuid,p_approval_window_start timestamptz,
 p_approval_window_end timestamptz,p_revocation_owner uuid,p_credential_custodian uuid,p_credential_delivery_method text,
 p_credential_rotation_owner uuid,p_immediate_revocation_policy text,p_reason text,p_provenance text,p_correlation_id uuid,
 p_evidence_binding_fingerprint text,p_expected_artifact_version integer,p_expected_canonicalization_version integer,
 p_expected_canonical_manifest_bytes bytea,p_expected_manifest_digest text,p_expected_signature_preimage_bytes bytea,
 p_expected_algorithm_id text,p_expected_signer_subject_id uuid,p_expected_signer_key_id uuid,
 p_expected_signer_key_revision integer,p_expected_signer_key_fingerprint text,p_expected_signer_key_lineage_fingerprint text,
 p_expected_subject_public_key_info_der bytea,p_expected_signature_bytes bytea,p_expected_signer_authority_id uuid,
 p_expected_signer_authority_revision integer,p_expected_signer_authority_fingerprint text,p_expected_verified_at timestamptz,
 p_expected_accepted_proof_fingerprint text,p_expected_evidence_binding_fingerprint text
) RETURNS TABLE(outcome text,result_operation_id uuid,result_intent_fingerprint text,result_receipt_fingerprint text,result_effect_time timestamptz(6))
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$DECLARE
 org_status text; op public.command_authority_operation%ROWTYPE; principal public.command_principal%ROWTYPE;
 grant_target public.command_permission_grant%ROWTYPE; a public.s2a_accepted_attestation%ROWTYPE; k public.s2a_signer_key_revision%ROWTYPE;
 au public.s2a_signer_authority_revision%ROWTYPE; snapshot record; reconstructed bytea; reconstructed_digest text;
 current_evidence text; computed_intent text; computed_receipt text; resource text; key_leaf_count integer;
 authority_leaf_count integer; ml_count bigint; omie_count bigint; effectTime timestamptz(6);
BEGIN
 SELECT o.status INTO org_status FROM public.integration_organization o
  WHERE o.organization_id=p_organization_id FOR SHARE;
 IF NOT FOUND THEN RAISE EXCEPTION 'Governance unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE'; END IF;
 PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(
  'command-authority-operation/1:'||p_organization_id||':'||p_operation_id,0));
 SELECT * INTO op FROM public.command_authority_operation o
  WHERE o.organization_id=p_organization_id AND o.operation_id=p_operation_id;
 IF FOUND THEN
  IF op.operation IS DISTINCT FROM 'GRANT' OR op.principal_id IS DISTINCT FROM p_principal_id
   OR op.credential_id IS NOT NULL OR op.credential_revision IS NOT NULL
   OR op.grant_id IS DISTINCT FROM p_grant_id OR op.grant_revision IS DISTINCT FROM 1
   OR op.permission IS DISTINCT FROM 'TRANSACTION_IDENTITY_DECISION_WRITE' OR op.state IS DISTINCT FROM 'ENABLED'
   OR op.attestation_manifest_id IS DISTINCT FROM p_manifest_id OR op.correlation_id IS DISTINCT FROM p_correlation_id
   OR p_permission IS DISTINCT FROM 'TRANSACTION_IDENTITY_DECISION_WRITE' THEN
   RAISE EXCEPTION 'Historical operation integrity failure' USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE';
  END IF;
  SELECT * INTO principal FROM public.command_principal p WHERE p.organization_id=p_organization_id AND p.principal_id=p_principal_id;
  IF NOT FOUND OR principal.mercado_livre_connection_id IS DISTINCT FROM p_mercado_livre_connection_id
   OR principal.omie_connection_id IS DISTINCT FROM p_omie_connection_id THEN
   RAISE EXCEPTION 'Historical principal integrity failure' USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE';
  END IF;
  SELECT * INTO grant_target FROM public.command_permission_grant g
   WHERE g.organization_id=p_organization_id AND g.grant_id=p_grant_id;
  IF NOT FOUND OR grant_target.principal_id IS DISTINCT FROM p_principal_id OR grant_target.revision IS DISTINCT FROM 1
   OR grant_target.supersedes_grant_id IS NOT NULL OR grant_target.permission IS DISTINCT FROM 'TRANSACTION_IDENTITY_DECISION_WRITE'
   OR grant_target.state IS DISTINCT FROM 'ENABLED' OR grant_target.reason IS DISTINCT FROM p_reason
   OR grant_target.provenance IS DISTINCT FROM p_provenance OR grant_target.correlation_id IS DISTINCT FROM p_correlation_id
   OR grant_target.decided_at IS DISTINCT FROM op.decided_at THEN
   RAISE EXCEPTION 'Historical grant integrity failure' USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE';
  END IF;
  SELECT * INTO a FROM public.s2a_accepted_attestation x WHERE x.organization_id=p_organization_id AND x.manifest_id=p_manifest_id;
  IF NOT FOUND OR NOT EXISTS (SELECT 1 FROM public.s2a_attestation_consumption c
    WHERE c.organization_id=p_organization_id AND c.manifest_id=p_manifest_id AND c.principal_id=p_principal_id
      AND c.manifest_digest=a.manifest_digest AND c.correlation_id=p_correlation_id) THEN
   RAISE EXCEPTION 'Historical consumption integrity failure' USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE';
  END IF;
  SELECT * INTO snapshot FROM public.s2a_v042_revalidate_snapshot(p_organization_id,p_manifest_id,p_schema_version,p_claim_manifest_id,
   p_claim_organization_id,p_mercado_livre_connection_id,p_omie_connection_id,p_source_order_reference,p_integration_reference,p_marketplace_order_id,
   p_permission,p_accountable_operator,p_approval_source,p_approval_window_start,p_approval_window_end,p_revocation_owner,p_credential_custodian,
   p_credential_delivery_method,p_credential_rotation_owner,p_immediate_revocation_policy,p_reason,p_provenance,p_correlation_id,p_evidence_binding_fingerprint,
   p_expected_artifact_version,p_expected_canonicalization_version,p_expected_canonical_manifest_bytes,p_expected_manifest_digest,
   p_expected_signature_preimage_bytes,p_expected_algorithm_id,p_expected_signer_subject_id,p_expected_signer_key_id,
   p_expected_signer_key_revision,p_expected_signer_key_fingerprint,p_expected_signer_key_lineage_fingerprint,
   p_expected_subject_public_key_info_der,p_expected_signature_bytes,p_expected_signer_authority_id,
   p_expected_signer_authority_revision,p_expected_signer_authority_fingerprint,p_expected_verified_at,
   p_expected_accepted_proof_fingerprint,p_expected_evidence_binding_fingerprint);
  computed_intent:=public.s2a_v042_authority_intent('GRANT',p_operation_id,p_organization_id,p_principal_id,
   NULL,NULL,NULL,NULL,p_grant_id,p_reason,p_provenance,p_correlation_id,
   p_manifest_id,snapshot.result_accepted_proof_fingerprint,snapshot.result_manifest_digest);
  computed_receipt:=public.s2a_v042_authority_receipt(computed_intent,'GRANT',p_principal_id,NULL,NULL,p_grant_id,1,'TRANSACTION_IDENTITY_DECISION_WRITE','ENABLED');
  IF op.intent_fingerprint IS DISTINCT FROM computed_intent OR op.receipt_fingerprint IS DISTINCT FROM computed_receipt THEN
   RAISE EXCEPTION 'Historical operation fingerprint integrity failure' USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE';
  END IF;
  RETURN QUERY SELECT 'ALREADY_APPLIED'::text,op.operation_id,computed_intent,computed_receipt,op.decided_at::timestamptz(6);
  RETURN;
 END IF; IF org_status<>'ACTIVE' THEN RAISE EXCEPTION 'Organization inactive' USING ERRCODE='P0017',DETAIL='EXPIRED_OR_NOT_YET_VALID'; END IF;
 IF p_claim_organization_id<>p_organization_id OR p_claim_manifest_id<>p_manifest_id OR p_permission<>'TRANSACTION_IDENTITY_DECISION_WRITE' THEN
  RAISE EXCEPTION 'Claim scope mismatch' USING ERRCODE='P0017',DETAIL='SCOPE_MISMATCH';
 END IF;
 PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(
  'command-authority-principal/1:'||p_organization_id||':'||p_principal_id,0));
 SELECT * INTO principal FROM public.command_principal p WHERE p.organization_id=p_organization_id AND p.principal_id=p_principal_id FOR UPDATE;
 IF NOT FOUND THEN RAISE EXCEPTION 'Principal unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE'; END IF;
 IF principal.mercado_livre_connection_id IS DISTINCT FROM p_mercado_livre_connection_id
  OR principal.omie_connection_id IS DISTINCT FROM p_omie_connection_id THEN
  RAISE EXCEPTION 'Principal scope mismatch' USING ERRCODE='P0017',DETAIL='SCOPE_MISMATCH';
 END IF;

 IF EXISTS (SELECT 1 FROM public.s2a_attestation_consumption c
   WHERE c.organization_id=p_organization_id AND c.manifest_id=p_manifest_id AND c.principal_id IS DISTINCT FROM p_principal_id) THEN
  RAISE EXCEPTION 'Consumption principal scope mismatch' USING ERRCODE='P0017',DETAIL='SCOPE_MISMATCH';
 END IF;
 IF NOT EXISTS (SELECT 1 FROM public.s2a_attestation_consumption c
   WHERE c.organization_id=p_organization_id AND c.manifest_id=p_manifest_id AND c.principal_id=p_principal_id
     AND c.correlation_id=p_correlation_id) THEN
  RAISE EXCEPTION 'Consumption unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE';
 END IF;
 SELECT * INTO a FROM public.s2a_accepted_attestation x WHERE x.organization_id=p_organization_id AND x.manifest_id=p_manifest_id;
 IF NOT FOUND THEN RAISE EXCEPTION 'Accepted artifact unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE'; END IF;
 IF NOT EXISTS (SELECT 1 FROM public.s2a_attestation_consumption c
   WHERE c.organization_id=p_organization_id AND c.manifest_id=p_manifest_id AND c.principal_id=p_principal_id
     AND c.manifest_digest=a.manifest_digest AND c.correlation_id=p_correlation_id) THEN
  RAISE EXCEPTION 'Consumption integrity failure' USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE';
 END IF;
 reconstructed:=public.s2a_v041_manifest_bytes(p_schema_version,p_claim_manifest_id,p_claim_organization_id,
  p_mercado_livre_connection_id,p_omie_connection_id,p_source_order_reference,p_integration_reference,p_marketplace_order_id,
  p_permission,p_accountable_operator,p_approval_source,p_approval_window_start,p_approval_window_end,p_revocation_owner,
  p_credential_custodian,p_credential_delivery_method,p_credential_rotation_owner,p_immediate_revocation_policy,p_reason,p_provenance,
  p_correlation_id,p_evidence_binding_fingerprint);
 reconstructed_digest:=encode(sha256(reconstructed),'hex');
  IF reconstructed IS DISTINCT FROM a.canonical_manifest_bytes OR reconstructed_digest IS DISTINCT FROM a.manifest_digest THEN
  RAISE EXCEPTION 'Accepted artifact integrity failure' USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE';
 END IF;
 PERFORM 1 FROM public.integration_connector_progress cp WHERE cp.organization_id=p_organization_id
  AND cp.connection_id=p_omie_connection_id AND cp.capability='marketplace-economic.omie-transaction-evidence.reacquisition-v3' FOR UPDATE;
 IF NOT FOUND THEN RAISE EXCEPTION 'Evidence unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE'; END IF;
 FOR resource IN SELECT unnest(ARRAY[
  'transaction-identity/subject/1:'||p_organization_id||':'||p_omie_connection_id||':'||octet_length(p_source_order_reference)||':'||p_source_order_reference,
  'transaction-identity/target/1:'||p_organization_id||':'||p_marketplace_order_id]) ORDER BY 1 LOOP
  PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(resource,0));
 END LOOP;
 PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(
  's2a-attestation/manifest/1:'||p_organization_id||':'||p_manifest_id,0));
 SELECT * INTO a FROM public.s2a_accepted_attestation x WHERE x.organization_id=p_organization_id AND x.manifest_id=p_manifest_id;
 IF NOT FOUND THEN RAISE EXCEPTION 'Accepted artifact unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE'; END IF;
 SELECT * INTO snapshot FROM public.s2a_v042_revalidate_snapshot(p_organization_id,p_manifest_id,p_schema_version,p_claim_manifest_id,
  p_claim_organization_id,p_mercado_livre_connection_id,p_omie_connection_id,p_source_order_reference,p_integration_reference,p_marketplace_order_id,
  p_permission,p_accountable_operator,p_approval_source,p_approval_window_start,p_approval_window_end,p_revocation_owner,p_credential_custodian,
  p_credential_delivery_method,p_credential_rotation_owner,p_immediate_revocation_policy,p_reason,p_provenance,p_correlation_id,p_evidence_binding_fingerprint,
  p_expected_artifact_version,p_expected_canonicalization_version,p_expected_canonical_manifest_bytes,p_expected_manifest_digest,p_expected_signature_preimage_bytes,p_expected_algorithm_id,
  p_expected_signer_subject_id,p_expected_signer_key_id,p_expected_signer_key_revision,p_expected_signer_key_fingerprint,p_expected_signer_key_lineage_fingerprint,p_expected_subject_public_key_info_der,p_expected_signature_bytes,
  p_expected_signer_authority_id,p_expected_signer_authority_revision,p_expected_signer_authority_fingerprint,p_expected_verified_at,p_expected_accepted_proof_fingerprint,p_expected_evidence_binding_fingerprint);

effectTime:=clock_timestamp()::timestamptz(6);
SELECT o.status INTO org_status FROM public.integration_organization o WHERE o.organization_id=p_organization_id FOR SHARE;
IF NOT FOUND THEN RAISE EXCEPTION 'Governance unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE'; END IF;
IF org_status<>'ACTIVE' THEN RAISE EXCEPTION 'Organization inactive' USING ERRCODE='P0017',DETAIL='EXPIRED_OR_NOT_YET_VALID'; END IF;
IF effectTime<p_approval_window_start OR effectTime>=p_approval_window_end THEN RAISE EXCEPTION 'Approval window denied' USING ERRCODE='P0017',DETAIL='EXPIRED_OR_NOT_YET_VALID'; END IF;
PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended('s2a-governance/signer-key/1:'||p_organization_id||':'||snapshot.result_signer_key_id,0));
SELECT * INTO k FROM public.s2a_signer_key_revision x WHERE x.organization_id=p_organization_id AND x.signer_key_id=snapshot.result_signer_key_id AND x.effective_at<=effectTime ORDER BY x.revision DESC LIMIT 1;
IF NOT FOUND THEN RAISE EXCEPTION 'Signer key unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE'; END IF;
IF k.state<>'ACTIVE' OR k.valid_from>effectTime THEN RAISE EXCEPTION 'Signer key ineligible' USING ERRCODE='P0017',DETAIL='EXPIRED_OR_NOT_YET_VALID'; END IF;
IF k.signer_subject_id IS DISTINCT FROM snapshot.result_signer_subject_id OR k.algorithm_id IS DISTINCT FROM snapshot.result_algorithm_id OR k.subject_public_key_info_der IS DISTINCT FROM snapshot.result_subject_public_key_info_der OR k.signer_key_fingerprint IS DISTINCT FROM snapshot.result_signer_key_fingerprint THEN RAISE EXCEPTION 'Signer key scope mismatch' USING ERRCODE='P0017',DETAIL='SCOPE_MISMATCH'; END IF;
PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended('s2a-governance/signer-authority-scope/1:'||p_organization_id||':'||snapshot.result_signer_subject_id||':'||snapshot.result_signer_key_id||':S2A_FIELD_PROOF_APPROVAL:TRANSACTION_IDENTITY_DECISION_WRITE',0));
SELECT count(*) INTO authority_leaf_count FROM public.s2a_signer_authority_revision x WHERE x.organization_id=p_organization_id AND x.signer_subject_id=snapshot.result_signer_subject_id AND x.signer_key_id=snapshot.result_signer_key_id AND x.approval_action='S2A_FIELD_PROOF_APPROVAL' AND x.permission='TRANSACTION_IDENTITY_DECISION_WRITE' AND NOT EXISTS(SELECT 1 FROM public.s2a_signer_authority_revision n WHERE n.organization_id=x.organization_id AND n.supersedes_signer_authority_id=x.signer_authority_id);
IF authority_leaf_count=0 THEN RAISE EXCEPTION 'Signer authority unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE'; END IF;
IF authority_leaf_count<>1 THEN RAISE EXCEPTION 'Signer authority conflict' USING ERRCODE='P0016',DETAIL='GOVERNANCE_CONFLICT'; END IF;
SELECT * INTO au FROM public.s2a_signer_authority_revision x WHERE x.organization_id=p_organization_id AND x.signer_subject_id=snapshot.result_signer_subject_id AND x.signer_key_id=snapshot.result_signer_key_id AND x.approval_action='S2A_FIELD_PROOF_APPROVAL' AND x.permission='TRANSACTION_IDENTITY_DECISION_WRITE' AND NOT EXISTS(SELECT 1 FROM public.s2a_signer_authority_revision n WHERE n.organization_id=x.organization_id AND n.supersedes_signer_authority_id=x.signer_authority_id);
IF au.signer_key_revision IS DISTINCT FROM k.revision OR au.signer_key_fingerprint IS DISTINCT FROM k.signer_key_fingerprint THEN RAISE EXCEPTION 'Authority key scope mismatch' USING ERRCODE='P0017',DETAIL='SCOPE_MISMATCH'; END IF;
IF au.state<>'ENABLED' OR au.valid_from>effectTime OR effectTime>=au.valid_until THEN RAISE EXCEPTION 'Authority ineligible' USING ERRCODE='P0017',DETAIL='EXPIRED_OR_NOT_YET_VALID'; END IF;
current_evidence:=public.s2a_v041_evidence_fingerprint(p_organization_id,p_marketplace_order_id,p_mercado_livre_connection_id,p_omie_connection_id,p_source_order_reference,p_integration_reference);
IF current_evidence IS DISTINCT FROM snapshot.result_signed_evidence_binding_fingerprint THEN RAISE EXCEPTION 'Evidence scope mismatch' USING ERRCODE='P0017',DETAIL='SCOPE_MISMATCH'; END IF;
SELECT * INTO principal FROM public.command_principal p WHERE p.organization_id=p_organization_id AND p.principal_id=p_principal_id;
IF NOT FOUND THEN RAISE EXCEPTION 'Principal unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE'; END IF;
IF principal.mercado_livre_connection_id IS DISTINCT FROM p_mercado_livre_connection_id OR principal.omie_connection_id IS DISTINCT FROM p_omie_connection_id THEN RAISE EXCEPTION 'Principal scope mismatch' USING ERRCODE='P0017',DETAIL='SCOPE_MISMATCH'; END IF;
IF NOT EXISTS(SELECT 1 FROM public.s2a_attestation_consumption c WHERE c.organization_id=p_organization_id AND c.manifest_id=p_manifest_id AND c.principal_id=p_principal_id AND c.manifest_digest=snapshot.result_manifest_digest AND c.correlation_id=p_correlation_id) THEN RAISE EXCEPTION 'Consumption lineage unavailable' USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE'; END IF;
IF EXISTS(SELECT 1 FROM public.command_permission_grant g WHERE g.organization_id=p_organization_id AND (g.grant_id=p_grant_id OR (g.principal_id=p_principal_id AND g.permission='TRANSACTION_IDENTITY_DECISION_WRITE'))) THEN RAISE EXCEPTION 'Initial grant collision' USING ERRCODE='P0016',DETAIL='GOVERNANCE_CONFLICT'; END IF;
IF EXISTS(SELECT 1 FROM public.command_authority_operation o WHERE o.organization_id=p_organization_id AND o.attestation_manifest_id=p_manifest_id AND o.operation='GRANT') THEN RAISE EXCEPTION 'Initial grant operation collision' USING ERRCODE='P0016',DETAIL='GOVERNANCE_CONFLICT'; END IF;
computed_intent:=public.s2a_v042_authority_intent('GRANT',p_operation_id,p_organization_id,p_principal_id,NULL,NULL,NULL,NULL,p_grant_id,p_reason,p_provenance,p_correlation_id,p_manifest_id,snapshot.result_accepted_proof_fingerprint,snapshot.result_manifest_digest);
computed_receipt:=public.s2a_v042_authority_receipt(computed_intent,'GRANT',p_principal_id,NULL,NULL,p_grant_id,1,'TRANSACTION_IDENTITY_DECISION_WRITE','ENABLED');
INSERT INTO public.command_permission_grant(organization_id,principal_id,grant_id,permission,state,revision,supersedes_grant_id,reason,provenance,correlation_id,decided_at)
VALUES(p_organization_id,p_principal_id,p_grant_id,'TRANSACTION_IDENTITY_DECISION_WRITE','ENABLED',1,NULL,p_reason,p_provenance,p_correlation_id,effectTime);
INSERT INTO public.command_authority_operation(organization_id,operation_id,operation,principal_id,credential_id,credential_revision,grant_id,grant_revision,permission,state,intent_fingerprint,receipt_fingerprint,correlation_id,decided_at,attestation_manifest_id)
VALUES(p_organization_id,p_operation_id,'GRANT',p_principal_id,NULL,NULL,p_grant_id,1,'TRANSACTION_IDENTITY_DECISION_WRITE','ENABLED',computed_intent,computed_receipt,p_correlation_id,effectTime,p_manifest_id);
RETURN QUERY SELECT 'APPLIED',p_operation_id,computed_intent,computed_receipt,effectTime;
END $$;


CREATE FUNCTION public.s2a_v042_apply_legacy_unlinked_decision(
    p_organization_id uuid,
    p_decision_id uuid,
    p_omie_connection_id uuid,
    p_source_order_reference text,
    p_marketplace_order_id uuid,
    p_kind text,
    p_reason text,
    p_revision integer,
    p_supersedes_decision_id uuid,
    p_ml_connection_id uuid,
    p_ml_capability text,
    p_ml_progress_version bigint,
    p_ml_record_ordinal integer,
    p_external_order_id text,
    p_currency char(3),
    p_omie_capability text,
    p_omie_progress_version bigint,
    p_omie_record_ordinal integer,
    p_omie_semantic_fingerprint char(64),
    p_provider_revision_local timestamp without time zone,
    p_principal_id uuid,
    p_credential_id uuid,
    p_credential_revision integer,
    p_grant_id uuid,
    p_grant_revision integer,
    p_permission text,
    p_authorization_semantic_version text,
    p_authorization_fingerprint char(64),
    p_intent_fingerprint char(64),
    p_decision_semantic_fingerprint char(64),
    p_provenance text,
    p_correlation_id uuid
)
RETURNS TABLE(
    outcome text,
    result_decision_id uuid,
    result_decision_semantic_fingerprint text,
    result_decided_at timestamptz
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path=pg_catalog,pg_temp
AS $$
DECLARE
    current_principal public.command_principal%ROWTYPE;
    current_credential public.command_credential_revision%ROWTYPE;
    current_grant public.command_permission_grant%ROWTYPE;
    proposed public.marketplace_transaction_identity_decision%ROWTYPE;
    existing public.marketplace_transaction_identity_decision%ROWTYPE;
    persisted public.marketplace_transaction_identity_decision%ROWTYPE;
    proposed_intent text;
    stored_intent text;
    stored_semantic text;
    current_authorization_fingerprint text;
    linked_grant_count bigint;
BEGIN
    IF NOT public.command_authorization_organization_lock(p_organization_id) THEN
        RAISE EXCEPTION 'Command authority unavailable'
            USING ERRCODE='P0012';
    END IF;

    SELECT p.*
      INTO current_principal
      FROM public.command_principal p
     WHERE p.organization_id=p_organization_id
       AND p.principal_id=p_principal_id
     FOR UPDATE;

    IF NOT FOUND
       OR current_principal.mercado_livre_connection_id IS DISTINCT FROM p_ml_connection_id
       OR current_principal.omie_connection_id IS DISTINCT FROM p_omie_connection_id THEN
        RAISE EXCEPTION 'Command authority unavailable'
            USING ERRCODE='P0012';
    END IF;

    SELECT c.*
      INTO current_credential
      FROM public.command_credential_revision c
     WHERE c.organization_id=p_organization_id
       AND c.principal_id=p_principal_id
       AND c.credential_id=p_credential_id
     ORDER BY c.revision DESC
     LIMIT 1;

    IF NOT FOUND
       OR current_credential.revision IS DISTINCT FROM p_credential_revision
       OR current_credential.state IS DISTINCT FROM 'ENABLED' THEN
        RAISE EXCEPTION 'Command authority unavailable'
            USING ERRCODE='P0012';
    END IF;

    IF p_permission IS DISTINCT FROM 'TRANSACTION_IDENTITY_DECISION_WRITE' THEN
        RAISE EXCEPTION 'Command authority unavailable'
            USING ERRCODE='P0012';
    END IF;

    SELECT g.*
      INTO current_grant
      FROM public.command_permission_grant g
     WHERE g.organization_id=p_organization_id
       AND g.principal_id=p_principal_id
       AND g.permission=p_permission
     ORDER BY g.revision DESC
     LIMIT 1;

    IF NOT FOUND OR current_grant.state IS DISTINCT FROM 'ENABLED' THEN
        RAISE EXCEPTION 'Command authority unavailable'
            USING ERRCODE='P0012';
    END IF;

    IF current_grant.grant_id IS DISTINCT FROM p_grant_id
       OR current_grant.revision IS DISTINCT FROM p_grant_revision THEN
        RAISE EXCEPTION 'Command authority unavailable'
            USING ERRCODE='P0012';
    END IF;

    current_authorization_fingerprint :=
        public.transaction_identity_grant_fingerprint(
            p_organization_id,
            p_grant_id
        );

    IF p_authorization_semantic_version IS DISTINCT FROM 'command-authorization/1'
       OR p_authorization_fingerprint IS DISTINCT FROM current_authorization_fingerprint THEN
        RAISE EXCEPTION 'Authorization lineage mismatch'
            USING ERRCODE='23514';
    END IF;

    PERFORM pg_catalog.pg_advisory_xact_lock(
        pg_catalog.hashtextextended(
            'transaction-identity/id/1:' || p_organization_id || ':' || p_decision_id,
            0
        )
    );

    proposed.organization_id := p_organization_id;
    proposed.decision_id := p_decision_id;
    proposed.omie_connection_id := p_omie_connection_id;
    proposed.source_order_reference := p_source_order_reference;
    proposed.marketplace_order_id := p_marketplace_order_id;
    proposed.kind := p_kind;
    proposed.reason := p_reason;
    proposed.revision := p_revision;
    proposed.supersedes_decision_id := p_supersedes_decision_id;
    proposed.ml_connection_id := p_ml_connection_id;
    proposed.ml_capability := p_ml_capability;
    proposed.ml_progress_version := p_ml_progress_version;
    proposed.ml_record_ordinal := p_ml_record_ordinal;
    proposed.external_order_id := p_external_order_id;
    proposed.currency := p_currency;
    proposed.omie_capability := p_omie_capability;
    proposed.omie_progress_version := p_omie_progress_version;
    proposed.omie_record_ordinal := p_omie_record_ordinal;
    proposed.omie_semantic_fingerprint := p_omie_semantic_fingerprint;
    proposed.provider_revision_local := p_provider_revision_local;
    proposed.principal_id := p_principal_id;
    proposed.credential_id := p_credential_id;
    proposed.credential_revision := p_credential_revision;
    proposed.grant_id := p_grant_id;
    proposed.grant_revision := p_grant_revision;
    proposed.permission := p_permission;
    proposed.authorization_semantic_version := p_authorization_semantic_version;
    proposed.authorization_fingerprint := p_authorization_fingerprint;
    proposed.intent_fingerprint := p_intent_fingerprint;
    proposed.decision_semantic_fingerprint := p_decision_semantic_fingerprint;
    proposed.provenance := p_provenance;
    proposed.correlation_id := p_correlation_id;

    proposed_intent := public.transaction_identity_intent(proposed);

    SELECT d.*
      INTO existing
      FROM public.marketplace_transaction_identity_decision d
     WHERE d.organization_id=p_organization_id
       AND d.decision_id=p_decision_id;

    IF FOUND THEN
        stored_intent := public.transaction_identity_intent(existing);
        stored_semantic := public.transaction_identity_fingerprint(existing);

        IF existing.intent_fingerprint IS DISTINCT FROM stored_intent
           OR existing.decision_semantic_fingerprint IS DISTINCT FROM stored_semantic THEN
            RAISE EXCEPTION 'Historical decision integrity failure'
                USING ERRCODE='23514';
        END IF;

        IF p_intent_fingerprint IS DISTINCT FROM proposed_intent
           OR existing.intent_fingerprint IS DISTINCT FROM proposed_intent THEN
            RAISE EXCEPTION 'Decision replay integrity failure'
                USING ERRCODE='23514';
        END IF;

        RETURN QUERY
        SELECT
            'ALREADY_APPLIED'::text,
            existing.decision_id,
            existing.decision_semantic_fingerprint::text,
            existing.decided_at;
        RETURN;
    END IF;

    SELECT count(*)
      INTO linked_grant_count
      FROM public.command_authority_operation o
     WHERE o.organization_id=p_organization_id
       AND o.operation='GRANT'
       AND o.principal_id=p_principal_id
       AND o.grant_id=p_grant_id
       AND o.grant_revision=p_grant_revision
       AND o.permission='TRANSACTION_IDENTITY_DECISION_WRITE'
       AND o.state='ENABLED'
       AND o.attestation_manifest_id IS NOT NULL;

    IF linked_grant_count=1 THEN
        RAISE EXCEPTION 'Legacy-unlinked route mismatch'
            USING ERRCODE='P0018',DETAIL='ROUTE_MISMATCH';
    ELSIF linked_grant_count>1 THEN
        RAISE EXCEPTION 'Ambiguous linked grant route'
            USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE';
    END IF;

    INSERT INTO public.marketplace_transaction_identity_decision(
        organization_id,
        decision_id,
        omie_connection_id,
        source_order_reference,
        marketplace_order_id,
        kind,
        reason,
        revision,
        supersedes_decision_id,
        ml_connection_id,
        ml_capability,
        ml_progress_version,
        ml_record_ordinal,
        external_order_id,
        currency,
        omie_capability,
        omie_progress_version,
        omie_record_ordinal,
        omie_semantic_fingerprint,
        provider_revision_local,
        principal_id,
        credential_id,
        credential_revision,
        grant_id,
        grant_revision,
        permission,
        authorization_semantic_version,
        authorization_fingerprint,
        intent_fingerprint,
        decision_semantic_fingerprint,
        provenance,
        correlation_id
    )
    VALUES (
        p_organization_id,
        p_decision_id,
        p_omie_connection_id,
        p_source_order_reference,
        p_marketplace_order_id,
        p_kind,
        p_reason,
        p_revision,
        p_supersedes_decision_id,
        p_ml_connection_id,
        p_ml_capability,
        p_ml_progress_version,
        p_ml_record_ordinal,
        p_external_order_id,
        p_currency,
        p_omie_capability,
        p_omie_progress_version,
        p_omie_record_ordinal,
        p_omie_semantic_fingerprint,
        p_provider_revision_local,
        p_principal_id,
        p_credential_id,
        p_credential_revision,
        p_grant_id,
        p_grant_revision,
        p_permission,
        p_authorization_semantic_version,
        p_authorization_fingerprint,
        p_intent_fingerprint,
        p_decision_semantic_fingerprint,
        p_provenance,
        p_correlation_id
    )
    RETURNING * INTO persisted;

    RETURN QUERY
    SELECT
        'APPLIED'::text,
        persisted.decision_id,
        persisted.decision_semantic_fingerprint::text,
        persisted.decided_at;
END;
$$;

CREATE FUNCTION public.s2a_v042_begin_attested_decision_verification(
    p_organization_id uuid,
    p_principal_id uuid,
    p_grant_id uuid,
    p_grant_revision integer,
    p_decision_id uuid,
    p_decision_omie_connection_id uuid,
    p_decision_source_order_reference text,
    p_decision_marketplace_order_id uuid,
    p_schema_version integer,
    p_claim_manifest_id uuid,
    p_claim_organization_id uuid,
    p_mercado_livre_connection_id uuid,
    p_omie_connection_id uuid,
    p_source_order_reference text,
    p_integration_reference text,
    p_marketplace_order_id uuid,
    p_permission text,
    p_accountable_operator uuid,
    p_approval_source uuid,
    p_approval_window_start timestamptz,
    p_approval_window_end timestamptz,
    p_revocation_owner uuid,
    p_credential_custodian uuid,
    p_credential_delivery_method text,
    p_credential_rotation_owner uuid,
    p_immediate_revocation_policy text,
    p_reason text,
    p_provenance text,
    p_correlation_id uuid,
    p_evidence_binding_fingerprint text
)
RETURNS TABLE(
    outcome text,
    result_decision_id uuid,
    result_decision_semantic_fingerprint text,
    result_decided_at timestamptz,
    result_manifest_id uuid,
    result_artifact_version integer,
    result_schema_version integer,
    result_canonicalization_version integer,
    result_canonical_manifest_bytes bytea,
    result_manifest_digest text,
    result_signature_preimage_bytes bytea,
    result_algorithm_id text,
    result_signer_subject_id uuid,
    result_signer_key_id uuid,
    result_signer_key_revision integer,
    result_signer_key_fingerprint text,
    result_signer_key_lineage_fingerprint text,
    result_subject_public_key_info_der bytea,
    result_signature_bytes bytea,
    result_signer_authority_id uuid,
    result_signer_authority_revision integer,
    result_signer_authority_fingerprint text,
    result_verified_at timestamptz(6),
    result_accepted_proof_fingerprint text,
    result_signed_evidence_binding_fingerprint text,
    result_current_durable_evidence_binding text,
    result_observed_effect_time timestamptz(6),
    result_observed_organization_status text,
    result_observed_effective_signer_key_revision integer,
    result_observed_effective_signer_key_state text,
    result_observed_current_signer_authority_id uuid,
    result_observed_current_signer_authority_revision integer,
    result_observed_current_signer_authority_fingerprint text
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path=pg_catalog,pg_temp
AS $$
DECLARE
    current_principal public.command_principal%ROWTYPE;
    current_grant public.command_permission_grant%ROWTYPE;
    existing public.marketplace_transaction_identity_decision%ROWTYPE;
    proposed public.marketplace_transaction_identity_decision%ROWTYPE;
    linked_operation public.command_authority_operation%ROWTYPE;
    accepted public.s2a_accepted_attestation%ROWTYPE;
    effective_key public.s2a_signer_key_revision%ROWTYPE;
    current_authority public.s2a_signer_authority_revision%ROWTYPE;
    snapshot record;
    proposed_intent text;
    stored_intent text;
    stored_semantic text;
    reconstructed bytea;
    reconstructed_digest text;
    current_evidence text;
    observed_organization_status text;
    lock_resource text;
    linked_grant_count bigint;
    key_leaf_count bigint;
    authority_leaf_count bigint;
BEGIN
    IF NOT public.command_authorization_organization_lock(p_organization_id) THEN
        RAISE EXCEPTION 'Command authority unavailable'
            USING ERRCODE='P0012';
    END IF;

    SELECT p.*
      INTO current_principal
      FROM public.command_principal p
     WHERE p.organization_id=p_organization_id
       AND p.principal_id=p_principal_id
     FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Command authority unavailable'
            USING ERRCODE='P0012';
    END IF;

    IF p_permission IS DISTINCT FROM 'TRANSACTION_IDENTITY_DECISION_WRITE' THEN
        RAISE EXCEPTION 'Command authority unavailable'
            USING ERRCODE='P0012';
    END IF;

    SELECT g.*
      INTO current_grant
      FROM public.command_permission_grant g
     WHERE g.organization_id=p_organization_id
       AND g.principal_id=p_principal_id
       AND g.permission=p_permission
     ORDER BY g.revision DESC
     LIMIT 1;

    IF NOT FOUND
       OR current_grant.state IS DISTINCT FROM 'ENABLED'
       OR current_grant.grant_id IS DISTINCT FROM p_grant_id
       OR current_grant.revision IS DISTINCT FROM p_grant_revision THEN
        RAISE EXCEPTION 'Command authority unavailable'
            USING ERRCODE='P0012';
    END IF;

    PERFORM pg_catalog.pg_advisory_xact_lock(
        pg_catalog.hashtextextended(
            'transaction-identity/id/1:' || p_organization_id || ':' || p_decision_id,
            0
        )
    );

    proposed.organization_id := p_organization_id;
    proposed.decision_id := p_decision_id;
    proposed.omie_connection_id := p_decision_omie_connection_id;
    proposed.source_order_reference := p_decision_source_order_reference;
    proposed.marketplace_order_id := p_decision_marketplace_order_id;
    proposed.kind := 'CONFIRMED';
    proposed.reason := 'EXPLICIT_CONFIRMATION';
    proposed.revision := 1;
    proposed.supersedes_decision_id := NULL;
    proposed.ml_connection_id := p_mercado_livre_connection_id;
    proposed.principal_id := p_principal_id;
    proposed.provenance := p_provenance;
    proposed_intent := public.transaction_identity_intent(proposed);

    SELECT d.*
      INTO existing
      FROM public.marketplace_transaction_identity_decision d
     WHERE d.organization_id=p_organization_id
       AND d.decision_id=p_decision_id;

    IF FOUND THEN
        stored_intent := public.transaction_identity_intent(existing);
        stored_semantic := public.transaction_identity_fingerprint(existing);

        IF existing.intent_fingerprint IS DISTINCT FROM stored_intent
           OR existing.decision_semantic_fingerprint IS DISTINCT FROM stored_semantic THEN
            RAISE EXCEPTION 'Historical decision integrity failure'
                USING ERRCODE='23514';
        END IF;

        IF existing.intent_fingerprint IS DISTINCT FROM proposed_intent THEN
            RAISE EXCEPTION 'Decision replay integrity failure'
                USING ERRCODE='23514';
        END IF;

        outcome := 'ALREADY_APPLIED';
        result_decision_id := existing.decision_id;
        result_decision_semantic_fingerprint := existing.decision_semantic_fingerprint::text;
        result_decided_at := existing.decided_at;
        RETURN NEXT;
        RETURN;
    END IF;

    SELECT count(*)
      INTO linked_grant_count
      FROM public.command_authority_operation o
     WHERE o.organization_id=p_organization_id
       AND o.operation='GRANT'
       AND o.principal_id=p_principal_id
       AND o.grant_id=p_grant_id
       AND o.grant_revision=p_grant_revision
       AND o.permission='TRANSACTION_IDENTITY_DECISION_WRITE'
       AND o.state='ENABLED'
       AND o.attestation_manifest_id IS NOT NULL;

    IF linked_grant_count=0 THEN
        RAISE EXCEPTION 'Attested route unavailable'
            USING ERRCODE='P0018',DETAIL='ROUTE_MISMATCH';
    ELSIF linked_grant_count>1 THEN
        RAISE EXCEPTION 'Ambiguous linked grant route'
            USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE';
    END IF;

    SELECT o.*
      INTO STRICT linked_operation
      FROM public.command_authority_operation o
     WHERE o.organization_id=p_organization_id
       AND o.operation='GRANT'
       AND o.principal_id=p_principal_id
       AND o.grant_id=p_grant_id
       AND o.grant_revision=p_grant_revision
       AND o.permission='TRANSACTION_IDENTITY_DECISION_WRITE'
       AND o.state='ENABLED'
       AND o.attestation_manifest_id IS NOT NULL;

    IF linked_operation.attestation_manifest_id IS DISTINCT FROM p_claim_manifest_id
       OR p_claim_organization_id IS DISTINCT FROM p_organization_id THEN
        RAISE EXCEPTION 'Linked grant manifest scope mismatch'
            USING ERRCODE='P0017',DETAIL='SCOPE_MISMATCH';
    END IF;

    SELECT a.*
      INTO accepted
      FROM public.s2a_accepted_attestation a
     WHERE a.organization_id=p_organization_id
       AND a.manifest_id=linked_operation.attestation_manifest_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Accepted artifact unavailable'
            USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE';
    END IF;

    reconstructed := public.s2a_v041_manifest_bytes(
        p_schema_version,
        p_claim_manifest_id,
        p_claim_organization_id,
        p_mercado_livre_connection_id,
        p_omie_connection_id,
        p_source_order_reference,
        p_integration_reference,
        p_marketplace_order_id,
        p_permission,
        p_accountable_operator,
        p_approval_source,
        p_approval_window_start,
        p_approval_window_end,
        p_revocation_owner,
        p_credential_custodian,
        p_credential_delivery_method,
        p_credential_rotation_owner,
        p_immediate_revocation_policy,
        p_reason,
        p_provenance,
        p_correlation_id,
        p_evidence_binding_fingerprint
    );
    reconstructed_digest := pg_catalog.encode(pg_catalog.sha256(reconstructed),'hex');

    IF reconstructed IS DISTINCT FROM accepted.canonical_manifest_bytes
       OR reconstructed_digest IS DISTINCT FROM accepted.manifest_digest THEN
        RAISE EXCEPTION 'Accepted artifact integrity failure'
            USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE';
    END IF;

    IF p_decision_omie_connection_id IS DISTINCT FROM p_omie_connection_id
       OR p_decision_source_order_reference IS DISTINCT FROM p_source_order_reference
       OR p_decision_marketplace_order_id IS DISTINCT FROM p_marketplace_order_id
       OR p_permission IS DISTINCT FROM 'TRANSACTION_IDENTITY_DECISION_WRITE'
       OR current_principal.mercado_livre_connection_id IS DISTINCT FROM p_mercado_livre_connection_id
       OR current_principal.omie_connection_id IS DISTINCT FROM p_omie_connection_id THEN
        RAISE EXCEPTION 'Decision claim scope mismatch'
            USING ERRCODE='P0017',DETAIL='SCOPE_MISMATCH';
    END IF;

    PERFORM 1
      FROM public.integration_connector_progress cp
     WHERE cp.organization_id=p_organization_id
       AND cp.connection_id=p_omie_connection_id
       AND cp.capability='marketplace-economic.omie-transaction-evidence.reacquisition-v3'
     FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Evidence unavailable'
            USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE';
    END IF;

    FOR lock_resource IN
        SELECT pg_catalog.unnest(ARRAY[
            'transaction-identity/subject/1:' || p_organization_id || ':' || p_omie_connection_id || ':' ||
                pg_catalog.octet_length(p_source_order_reference) || ':' || p_source_order_reference,
            'transaction-identity/target/1:' || p_organization_id || ':' || p_marketplace_order_id
        ])
        ORDER BY 1
    LOOP
        PERFORM pg_catalog.pg_advisory_xact_lock(
            pg_catalog.hashtextextended(lock_resource,0)
        );
    END LOOP;

    PERFORM pg_catalog.pg_advisory_xact_lock(
        pg_catalog.hashtextextended(
            's2a-attestation/manifest/1:' || p_organization_id || ':' || linked_operation.attestation_manifest_id,
            0
        )
    );

    SELECT a.*
      INTO accepted
      FROM public.s2a_accepted_attestation a
     WHERE a.organization_id=p_organization_id
       AND a.manifest_id=linked_operation.attestation_manifest_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Accepted artifact unavailable'
            USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE';
    END IF;

    SELECT *
      INTO snapshot
      FROM public.s2a_v042_revalidate_snapshot(
        p_organization_id,
        linked_operation.attestation_manifest_id,
        p_schema_version,
        p_claim_manifest_id,
        p_claim_organization_id,
        p_mercado_livre_connection_id,
        p_omie_connection_id,
        p_source_order_reference,
        p_integration_reference,
        p_marketplace_order_id,
        p_permission,
        p_accountable_operator,
        p_approval_source,
        p_approval_window_start,
        p_approval_window_end,
        p_revocation_owner,
        p_credential_custodian,
        p_credential_delivery_method,
        p_credential_rotation_owner,
        p_immediate_revocation_policy,
        p_reason,
        p_provenance,
        p_correlation_id,
        p_evidence_binding_fingerprint,
        accepted.artifact_version,
        accepted.canonicalization_version,
        accepted.canonical_manifest_bytes,
        accepted.manifest_digest,
        accepted.canonical_signature_preimage_bytes,
        accepted.algorithm_id,
        (SELECT k.signer_subject_id
           FROM public.s2a_signer_key_revision k
          WHERE k.organization_id=accepted.organization_id
            AND k.signer_key_id=accepted.signer_key_id
            AND k.revision=accepted.signer_key_revision),
        accepted.signer_key_id,
        accepted.signer_key_revision,
        accepted.signer_key_fingerprint,
        accepted.signer_key_lineage_fingerprint,
        accepted.subject_public_key_info_der,
        accepted.signature_bytes,
        accepted.signer_authority_id,
        accepted.signer_authority_revision,
        accepted.signer_authority_fingerprint,
        accepted.verified_at,
        accepted.accepted_proof_fingerprint,
        p_evidence_binding_fingerprint
    );

    result_observed_effect_time := pg_catalog.clock_timestamp()::timestamptz(6);

    SELECT o.status
      INTO observed_organization_status
      FROM public.integration_organization o
     WHERE o.organization_id=p_organization_id
     FOR SHARE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Governance unavailable'
            USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE';
    END IF;

    result_observed_organization_status := observed_organization_status;

    IF observed_organization_status IS DISTINCT FROM 'ACTIVE'
       OR result_observed_effect_time<p_approval_window_start
       OR result_observed_effect_time>=p_approval_window_end THEN
        RAISE EXCEPTION 'Current approval eligibility denied'
            USING ERRCODE='P0017',DETAIL='EXPIRED_OR_NOT_YET_VALID';
    END IF;

    PERFORM pg_catalog.pg_advisory_xact_lock(
        pg_catalog.hashtextextended(
            's2a-governance/signer-key/1:' || p_organization_id || ':' || snapshot.result_signer_key_id,
            0
        )
    );

    SELECT count(*)
      INTO key_leaf_count
      FROM public.s2a_signer_key_revision k
     WHERE k.organization_id=p_organization_id
       AND k.signer_key_id=snapshot.result_signer_key_id
       AND NOT EXISTS (
            SELECT 1
              FROM public.s2a_signer_key_revision successor
             WHERE successor.organization_id=k.organization_id
               AND successor.signer_key_id=k.signer_key_id
               AND successor.supersedes_revision=k.revision
       );

    IF key_leaf_count<>1 THEN
        RAISE EXCEPTION 'Signer key lineage conflict'
            USING ERRCODE='P0016',DETAIL='GOVERNANCE_CONFLICT';
    END IF;

    SELECT k.*
      INTO effective_key
      FROM public.s2a_signer_key_revision k
     WHERE k.organization_id=p_organization_id
       AND k.signer_key_id=snapshot.result_signer_key_id
       AND k.effective_at<=result_observed_effect_time
     ORDER BY k.effective_at DESC,k.revision DESC
     LIMIT 1;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Signer key unavailable'
            USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE';
    END IF;

    IF effective_key.valid_from>result_observed_effect_time
       OR effective_key.state IS DISTINCT FROM 'ACTIVE' THEN
        RAISE EXCEPTION 'Signer key ineligible'
            USING ERRCODE='P0017',DETAIL='EXPIRED_OR_NOT_YET_VALID';
    END IF;

    IF effective_key.signer_subject_id IS DISTINCT FROM snapshot.result_signer_subject_id
       OR effective_key.algorithm_id IS DISTINCT FROM snapshot.result_algorithm_id
       OR effective_key.subject_public_key_info_der IS DISTINCT FROM snapshot.result_subject_public_key_info_der
       OR effective_key.signer_key_fingerprint IS DISTINCT FROM snapshot.result_signer_key_fingerprint THEN
        RAISE EXCEPTION 'Signer key scope mismatch'
            USING ERRCODE='P0017',DETAIL='SCOPE_MISMATCH';
    END IF;

    result_observed_effective_signer_key_revision := effective_key.revision;
    result_observed_effective_signer_key_state := effective_key.state;

    PERFORM pg_catalog.pg_advisory_xact_lock(
        pg_catalog.hashtextextended(
            's2a-governance/signer-authority-scope/1:' || p_organization_id || ':' ||
            snapshot.result_signer_subject_id || ':' || snapshot.result_signer_key_id ||
            ':S2A_FIELD_PROOF_APPROVAL:TRANSACTION_IDENTITY_DECISION_WRITE',
            0
        )
    );

    SELECT count(*)
      INTO authority_leaf_count
      FROM public.s2a_signer_authority_revision a
     WHERE a.organization_id=p_organization_id
       AND a.signer_subject_id=snapshot.result_signer_subject_id
       AND a.signer_key_id=snapshot.result_signer_key_id
       AND a.approval_action='S2A_FIELD_PROOF_APPROVAL'
       AND a.permission='TRANSACTION_IDENTITY_DECISION_WRITE'
       AND NOT EXISTS (
            SELECT 1
              FROM public.s2a_signer_authority_revision successor
             WHERE successor.organization_id=a.organization_id
               AND successor.supersedes_signer_authority_id=a.signer_authority_id
       );

    IF authority_leaf_count=0 THEN
        RAISE EXCEPTION 'Signer authority unavailable'
            USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE';
    ELSIF authority_leaf_count<>1 THEN
        RAISE EXCEPTION 'Signer authority conflict'
            USING ERRCODE='P0016',DETAIL='GOVERNANCE_CONFLICT';
    END IF;

    SELECT a.*
      INTO STRICT current_authority
      FROM public.s2a_signer_authority_revision a
     WHERE a.organization_id=p_organization_id
       AND a.signer_subject_id=snapshot.result_signer_subject_id
       AND a.signer_key_id=snapshot.result_signer_key_id
       AND a.approval_action='S2A_FIELD_PROOF_APPROVAL'
       AND a.permission='TRANSACTION_IDENTITY_DECISION_WRITE'
       AND NOT EXISTS (
            SELECT 1
              FROM public.s2a_signer_authority_revision successor
             WHERE successor.organization_id=a.organization_id
               AND successor.supersedes_signer_authority_id=a.signer_authority_id
       );

    IF current_authority.signer_key_revision IS DISTINCT FROM effective_key.revision
       OR current_authority.signer_key_fingerprint IS DISTINCT FROM effective_key.signer_key_fingerprint THEN
        RAISE EXCEPTION 'Signer authority key scope mismatch'
            USING ERRCODE='P0017',DETAIL='SCOPE_MISMATCH';
    END IF;

    IF current_authority.state IS DISTINCT FROM 'ENABLED'
       OR current_authority.valid_from>result_observed_effect_time
       OR result_observed_effect_time>=current_authority.valid_until THEN
        RAISE EXCEPTION 'Signer authority ineligible'
            USING ERRCODE='P0017',DETAIL='EXPIRED_OR_NOT_YET_VALID';
    END IF;

    current_evidence := public.s2a_v041_evidence_fingerprint(
        p_organization_id,
        p_marketplace_order_id,
        p_mercado_livre_connection_id,
        p_omie_connection_id,
        p_source_order_reference,
        p_integration_reference
    );

    IF current_evidence IS DISTINCT FROM snapshot.result_signed_evidence_binding_fingerprint THEN
        RAISE EXCEPTION 'Evidence scope mismatch'
            USING ERRCODE='P0017',DETAIL='SCOPE_MISMATCH';
    END IF;

    outcome := 'READY';
    result_decision_id := p_decision_id;
    result_decision_semantic_fingerprint := NULL;
    result_decided_at := NULL;
    result_manifest_id := linked_operation.attestation_manifest_id;
    result_artifact_version := snapshot.result_artifact_version;
    result_schema_version := snapshot.result_schema_version;
    result_canonicalization_version := snapshot.result_canonicalization_version;
    result_canonical_manifest_bytes := snapshot.result_canonical_manifest_bytes;
    result_manifest_digest := snapshot.result_manifest_digest;
    result_signature_preimage_bytes := snapshot.result_signature_preimage_bytes;
    result_algorithm_id := snapshot.result_algorithm_id;
    result_signer_subject_id := snapshot.result_signer_subject_id;
    result_signer_key_id := snapshot.result_signer_key_id;
    result_signer_key_revision := snapshot.result_signer_key_revision;
    result_signer_key_fingerprint := snapshot.result_signer_key_fingerprint;
    result_signer_key_lineage_fingerprint := snapshot.result_signer_key_lineage_fingerprint;
    result_subject_public_key_info_der := snapshot.result_subject_public_key_info_der;
    result_signature_bytes := snapshot.result_signature_bytes;
    result_signer_authority_id := snapshot.result_signer_authority_id;
    result_signer_authority_revision := snapshot.result_signer_authority_revision;
    result_signer_authority_fingerprint := snapshot.result_signer_authority_fingerprint;
    result_verified_at := snapshot.result_verified_at;
    result_accepted_proof_fingerprint := snapshot.result_accepted_proof_fingerprint;
    result_signed_evidence_binding_fingerprint := snapshot.result_signed_evidence_binding_fingerprint;
    result_current_durable_evidence_binding := current_evidence;
    result_observed_current_signer_authority_id := current_authority.signer_authority_id;
    result_observed_current_signer_authority_revision := current_authority.revision;
    result_observed_current_signer_authority_fingerprint := current_authority.signer_authority_fingerprint;
    RETURN NEXT;
END;
$$;

CREATE FUNCTION public.s2a_v042_apply_attested_decision(
    p_organization_id uuid,
    p_decision_id uuid,
    p_decision_omie_connection_id uuid,
    p_decision_source_order_reference text,
    p_decision_marketplace_order_id uuid,
    p_kind text,
    p_decision_reason text,
    p_revision integer,
    p_supersedes_decision_id uuid,
    p_ml_connection_id uuid,
    p_ml_capability text,
    p_ml_progress_version bigint,
    p_ml_record_ordinal integer,
    p_external_order_id text,
    p_currency char(3),
    p_omie_capability text,
    p_omie_progress_version bigint,
    p_omie_record_ordinal integer,
    p_omie_semantic_fingerprint char(64),
    p_provider_revision_local timestamp without time zone,
    p_principal_id uuid,
    p_credential_id uuid,
    p_credential_revision integer,
    p_grant_id uuid,
    p_grant_revision integer,
    p_decision_permission text,
    p_authorization_semantic_version text,
    p_authorization_fingerprint char(64),
    p_intent_fingerprint char(64),
    p_decision_semantic_fingerprint char(64),
    p_decision_provenance text,
    p_decision_correlation_id uuid,
    p_schema_version integer,
    p_claim_manifest_id uuid,
    p_claim_organization_id uuid,
    p_mercado_livre_connection_id uuid,
    p_omie_connection_id uuid,
    p_source_order_reference text,
    p_integration_reference text,
    p_marketplace_order_id uuid,
    p_permission text,
    p_accountable_operator uuid,
    p_approval_source uuid,
    p_approval_window_start timestamptz,
    p_approval_window_end timestamptz,
    p_revocation_owner uuid,
    p_credential_custodian uuid,
    p_credential_delivery_method text,
    p_credential_rotation_owner uuid,
    p_immediate_revocation_policy text,
    p_reason text,
    p_provenance text,
    p_correlation_id uuid,
    p_evidence_binding_fingerprint text,
    p_expected_artifact_version integer,
    p_expected_canonicalization_version integer,
    p_expected_canonical_manifest_bytes bytea,
    p_expected_manifest_digest text,
    p_expected_signature_preimage_bytes bytea,
    p_expected_algorithm_id text,
    p_expected_signer_subject_id uuid,
    p_expected_signer_key_id uuid,
    p_expected_signer_key_revision integer,
    p_expected_signer_key_fingerprint text,
    p_expected_signer_key_lineage_fingerprint text,
    p_expected_subject_public_key_info_der bytea,
    p_expected_signature_bytes bytea,
    p_expected_signer_authority_id uuid,
    p_expected_signer_authority_revision integer,
    p_expected_signer_authority_fingerprint text,
    p_expected_verified_at timestamptz,
    p_expected_accepted_proof_fingerprint text,
    p_expected_evidence_binding_fingerprint text
)
RETURNS TABLE(
    outcome text,
    result_decision_id uuid,
    result_decision_semantic_fingerprint text,
    result_decided_at timestamptz
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path=pg_catalog,pg_temp
AS $$
DECLARE
    current_principal public.command_principal%ROWTYPE;
    current_credential public.command_credential_revision%ROWTYPE;
    current_grant public.command_permission_grant%ROWTYPE;
    proposed public.marketplace_transaction_identity_decision%ROWTYPE;
    existing public.marketplace_transaction_identity_decision%ROWTYPE;
    persisted public.marketplace_transaction_identity_decision%ROWTYPE;
    linked_operation public.command_authority_operation%ROWTYPE;
    accepted public.s2a_accepted_attestation%ROWTYPE;
    effective_key public.s2a_signer_key_revision%ROWTYPE;
    current_authority public.s2a_signer_authority_revision%ROWTYPE;
    snapshot record;
    proposed_intent text;
    stored_intent text;
    stored_semantic text;
    current_authorization_fingerprint text;
    reconstructed bytea;
    reconstructed_digest text;
    current_evidence text;
    observed_organization_status text;
    observed_effect_time timestamptz(6);
    linked_grant_count bigint;
    key_leaf_count bigint;
    authority_leaf_count bigint;
    prior_action_count bigint;
BEGIN
    IF NOT public.command_authorization_organization_lock(p_organization_id) THEN
        RAISE EXCEPTION 'Command authority unavailable'
            USING ERRCODE='P0012';
    END IF;

    SELECT p.*
      INTO current_principal
      FROM public.command_principal p
     WHERE p.organization_id=p_organization_id
       AND p.principal_id=p_principal_id
     FOR UPDATE;

    IF NOT FOUND
       OR current_principal.mercado_livre_connection_id IS DISTINCT FROM p_ml_connection_id
       OR current_principal.omie_connection_id IS DISTINCT FROM p_decision_omie_connection_id THEN
        RAISE EXCEPTION 'Command authority unavailable'
            USING ERRCODE='P0012';
    END IF;

    SELECT c.*
      INTO current_credential
      FROM public.command_credential_revision c
     WHERE c.organization_id=p_organization_id
       AND c.principal_id=p_principal_id
       AND c.credential_id=p_credential_id
     ORDER BY c.revision DESC
     LIMIT 1;

    IF NOT FOUND
       OR current_credential.revision IS DISTINCT FROM p_credential_revision
       OR current_credential.state IS DISTINCT FROM 'ENABLED' THEN
        RAISE EXCEPTION 'Command authority unavailable'
            USING ERRCODE='P0012';
    END IF;

    IF p_decision_permission IS DISTINCT FROM 'TRANSACTION_IDENTITY_DECISION_WRITE' THEN
        RAISE EXCEPTION 'Command authority unavailable'
            USING ERRCODE='P0012';
    END IF;

    SELECT g.*
      INTO current_grant
      FROM public.command_permission_grant g
     WHERE g.organization_id=p_organization_id
       AND g.principal_id=p_principal_id
       AND g.permission=p_decision_permission
     ORDER BY g.revision DESC
     LIMIT 1;

    IF NOT FOUND
       OR current_grant.state IS DISTINCT FROM 'ENABLED'
       OR current_grant.grant_id IS DISTINCT FROM p_grant_id
       OR current_grant.revision IS DISTINCT FROM p_grant_revision THEN
        RAISE EXCEPTION 'Command authority unavailable'
            USING ERRCODE='P0012';
    END IF;

    current_authorization_fingerprint :=
        public.transaction_identity_grant_fingerprint(
            p_organization_id,
            p_grant_id
        );

    IF p_authorization_semantic_version IS DISTINCT FROM 'command-authorization/1'
       OR p_authorization_fingerprint IS DISTINCT FROM current_authorization_fingerprint THEN
        RAISE EXCEPTION 'Authorization lineage mismatch'
            USING ERRCODE='23514';
    END IF;

    PERFORM pg_catalog.pg_advisory_xact_lock(
        pg_catalog.hashtextextended(
            'transaction-identity/id/1:' || p_organization_id || ':' || p_decision_id,
            0
        )
    );

    proposed.organization_id := p_organization_id;
    proposed.decision_id := p_decision_id;
    proposed.omie_connection_id := p_decision_omie_connection_id;
    proposed.source_order_reference := p_decision_source_order_reference;
    proposed.marketplace_order_id := p_decision_marketplace_order_id;
    proposed.kind := p_kind;
    proposed.reason := p_decision_reason;
    proposed.revision := p_revision;
    proposed.supersedes_decision_id := p_supersedes_decision_id;
    proposed.ml_connection_id := p_ml_connection_id;
    proposed.ml_capability := p_ml_capability;
    proposed.ml_progress_version := p_ml_progress_version;
    proposed.ml_record_ordinal := p_ml_record_ordinal;
    proposed.external_order_id := p_external_order_id;
    proposed.currency := p_currency;
    proposed.omie_capability := p_omie_capability;
    proposed.omie_progress_version := p_omie_progress_version;
    proposed.omie_record_ordinal := p_omie_record_ordinal;
    proposed.omie_semantic_fingerprint := p_omie_semantic_fingerprint;
    proposed.provider_revision_local := p_provider_revision_local;
    proposed.principal_id := p_principal_id;
    proposed.credential_id := p_credential_id;
    proposed.credential_revision := p_credential_revision;
    proposed.grant_id := p_grant_id;
    proposed.grant_revision := p_grant_revision;
    proposed.permission := p_decision_permission;
    proposed.authorization_semantic_version := p_authorization_semantic_version;
    proposed.authorization_fingerprint := p_authorization_fingerprint;
    proposed.intent_fingerprint := p_intent_fingerprint;
    proposed.decision_semantic_fingerprint := p_decision_semantic_fingerprint;
    proposed.provenance := p_decision_provenance;
    proposed.correlation_id := p_decision_correlation_id;

    proposed_intent := public.transaction_identity_intent(proposed);

    SELECT d.*
      INTO existing
      FROM public.marketplace_transaction_identity_decision d
     WHERE d.organization_id=p_organization_id
       AND d.decision_id=p_decision_id;

    IF FOUND THEN
        stored_intent := public.transaction_identity_intent(existing);
        stored_semantic := public.transaction_identity_fingerprint(existing);

        IF existing.intent_fingerprint IS DISTINCT FROM stored_intent
           OR existing.decision_semantic_fingerprint IS DISTINCT FROM stored_semantic THEN
            RAISE EXCEPTION 'Historical decision integrity failure'
                USING ERRCODE='23514';
        END IF;

        IF p_intent_fingerprint IS DISTINCT FROM proposed_intent
           OR existing.intent_fingerprint IS DISTINCT FROM proposed_intent THEN
            RAISE EXCEPTION 'Decision replay integrity failure'
                USING ERRCODE='23514';
        END IF;

        RETURN QUERY
        SELECT
            'ALREADY_APPLIED'::text,
            existing.decision_id,
            existing.decision_semantic_fingerprint::text,
            existing.decided_at;
        RETURN;
    END IF;

    SELECT count(*)
      INTO linked_grant_count
      FROM public.command_authority_operation o
     WHERE o.organization_id=p_organization_id
       AND o.operation='GRANT'
       AND o.principal_id=p_principal_id
       AND o.grant_id=p_grant_id
       AND o.grant_revision=p_grant_revision
       AND o.permission='TRANSACTION_IDENTITY_DECISION_WRITE'
       AND o.state='ENABLED'
       AND o.attestation_manifest_id IS NOT NULL;

    IF linked_grant_count=0 THEN
        RAISE EXCEPTION 'Attested route unavailable'
            USING ERRCODE='P0018',DETAIL='ROUTE_MISMATCH';
    ELSIF linked_grant_count>1 THEN
        RAISE EXCEPTION 'Ambiguous linked grant route'
            USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE';
    END IF;

    SELECT o.*
      INTO STRICT linked_operation
      FROM public.command_authority_operation o
     WHERE o.organization_id=p_organization_id
       AND o.operation='GRANT'
       AND o.principal_id=p_principal_id
       AND o.grant_id=p_grant_id
       AND o.grant_revision=p_grant_revision
       AND o.permission='TRANSACTION_IDENTITY_DECISION_WRITE'
       AND o.state='ENABLED'
       AND o.attestation_manifest_id IS NOT NULL;

    IF linked_operation.attestation_manifest_id IS DISTINCT FROM p_claim_manifest_id
       OR p_claim_organization_id IS DISTINCT FROM p_organization_id THEN
        RAISE EXCEPTION 'Linked grant manifest scope mismatch'
            USING ERRCODE='P0017',DETAIL='SCOPE_MISMATCH';
    END IF;

    SELECT a.*
      INTO accepted
      FROM public.s2a_accepted_attestation a
     WHERE a.organization_id=p_organization_id
       AND a.manifest_id=linked_operation.attestation_manifest_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Accepted artifact unavailable'
            USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE';
    END IF;

    reconstructed := public.s2a_v041_manifest_bytes(
        p_schema_version,
        p_claim_manifest_id,
        p_claim_organization_id,
        p_mercado_livre_connection_id,
        p_omie_connection_id,
        p_source_order_reference,
        p_integration_reference,
        p_marketplace_order_id,
        p_permission,
        p_accountable_operator,
        p_approval_source,
        p_approval_window_start,
        p_approval_window_end,
        p_revocation_owner,
        p_credential_custodian,
        p_credential_delivery_method,
        p_credential_rotation_owner,
        p_immediate_revocation_policy,
        p_reason,
        p_provenance,
        p_correlation_id,
        p_evidence_binding_fingerprint
    );
    reconstructed_digest := pg_catalog.encode(pg_catalog.sha256(reconstructed),'hex');

    IF reconstructed IS DISTINCT FROM accepted.canonical_manifest_bytes
       OR reconstructed_digest IS DISTINCT FROM accepted.manifest_digest THEN
        RAISE EXCEPTION 'Accepted artifact integrity failure'
            USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE';
    END IF;

    IF p_ml_connection_id IS DISTINCT FROM p_mercado_livre_connection_id
       OR p_decision_omie_connection_id IS DISTINCT FROM p_omie_connection_id
       OR p_decision_source_order_reference IS DISTINCT FROM p_source_order_reference
       OR p_decision_marketplace_order_id IS DISTINCT FROM p_marketplace_order_id
       OR p_decision_permission IS DISTINCT FROM p_permission
       OR p_permission IS DISTINCT FROM 'TRANSACTION_IDENTITY_DECISION_WRITE'
       OR p_decision_provenance IS DISTINCT FROM p_provenance
       OR p_decision_correlation_id IS DISTINCT FROM p_correlation_id
       OR current_principal.mercado_livre_connection_id IS DISTINCT FROM p_mercado_livre_connection_id
       OR current_principal.omie_connection_id IS DISTINCT FROM p_omie_connection_id THEN
        RAISE EXCEPTION 'Decision claim scope mismatch'
            USING ERRCODE='P0017',DETAIL='SCOPE_MISMATCH';
    END IF;

    IF p_kind IS DISTINCT FROM 'CONFIRMED'
       OR p_decision_reason IS DISTINCT FROM 'EXPLICIT_CONFIRMATION'
       OR p_revision IS DISTINCT FROM 1
       OR p_supersedes_decision_id IS NOT NULL THEN
        RAISE EXCEPTION 'Unsupported attested decision form'
            USING ERRCODE='P0018',DETAIL='UNSUPPORTED_CANONICAL_FORM';
    END IF;

    PERFORM public.transaction_identity_locks(
        p_organization_id,
        p_principal_id,
        p_decision_id,
        p_decision_omie_connection_id,
        p_decision_source_order_reference,
        p_decision_marketplace_order_id
    );

    PERFORM pg_catalog.pg_advisory_xact_lock(
        pg_catalog.hashtextextended(
            's2a-attestation/manifest/1:' || p_organization_id || ':' ||
                linked_operation.attestation_manifest_id,
            0
        )
    );

    SELECT *
      INTO snapshot
      FROM public.s2a_v042_revalidate_snapshot(
        p_organization_id,
        linked_operation.attestation_manifest_id,
        p_schema_version,
        p_claim_manifest_id,
        p_claim_organization_id,
        p_mercado_livre_connection_id,
        p_omie_connection_id,
        p_source_order_reference,
        p_integration_reference,
        p_marketplace_order_id,
        p_permission,
        p_accountable_operator,
        p_approval_source,
        p_approval_window_start,
        p_approval_window_end,
        p_revocation_owner,
        p_credential_custodian,
        p_credential_delivery_method,
        p_credential_rotation_owner,
        p_immediate_revocation_policy,
        p_reason,
        p_provenance,
        p_correlation_id,
        p_evidence_binding_fingerprint,
        p_expected_artifact_version,
        p_expected_canonicalization_version,
        p_expected_canonical_manifest_bytes,
        p_expected_manifest_digest,
        p_expected_signature_preimage_bytes,
        p_expected_algorithm_id,
        p_expected_signer_subject_id,
        p_expected_signer_key_id,
        p_expected_signer_key_revision,
        p_expected_signer_key_fingerprint,
        p_expected_signer_key_lineage_fingerprint,
        p_expected_subject_public_key_info_der,
        p_expected_signature_bytes,
        p_expected_signer_authority_id,
        p_expected_signer_authority_revision,
        p_expected_signer_authority_fingerprint,
        p_expected_verified_at,
        p_expected_accepted_proof_fingerprint,
        p_expected_evidence_binding_fingerprint
    );

    IF snapshot.result_artifact_version IS DISTINCT FROM p_expected_artifact_version
       OR snapshot.result_canonicalization_version IS DISTINCT FROM p_expected_canonicalization_version
       OR snapshot.result_canonical_manifest_bytes IS DISTINCT FROM p_expected_canonical_manifest_bytes
       OR snapshot.result_manifest_digest IS DISTINCT FROM p_expected_manifest_digest
       OR snapshot.result_signature_preimage_bytes IS DISTINCT FROM p_expected_signature_preimage_bytes
       OR snapshot.result_algorithm_id IS DISTINCT FROM p_expected_algorithm_id
       OR snapshot.result_signer_subject_id IS DISTINCT FROM p_expected_signer_subject_id
       OR snapshot.result_signer_key_id IS DISTINCT FROM p_expected_signer_key_id
       OR snapshot.result_signer_key_revision IS DISTINCT FROM p_expected_signer_key_revision
       OR snapshot.result_signer_key_fingerprint IS DISTINCT FROM p_expected_signer_key_fingerprint
       OR snapshot.result_signer_key_lineage_fingerprint IS DISTINCT FROM p_expected_signer_key_lineage_fingerprint
       OR snapshot.result_subject_public_key_info_der IS DISTINCT FROM p_expected_subject_public_key_info_der
       OR snapshot.result_signature_bytes IS DISTINCT FROM p_expected_signature_bytes
       OR snapshot.result_signer_authority_id IS DISTINCT FROM p_expected_signer_authority_id
       OR snapshot.result_signer_authority_revision IS DISTINCT FROM p_expected_signer_authority_revision
       OR snapshot.result_signer_authority_fingerprint IS DISTINCT FROM p_expected_signer_authority_fingerprint
       OR snapshot.result_verified_at IS DISTINCT FROM p_expected_verified_at
       OR snapshot.result_accepted_proof_fingerprint IS DISTINCT FROM p_expected_accepted_proof_fingerprint
       OR snapshot.result_signed_evidence_binding_fingerprint IS DISTINCT FROM p_expected_evidence_binding_fingerprint THEN
        RAISE EXCEPTION 'Immutable snapshot mismatch'
            USING ERRCODE='P0018',DETAIL='SNAPSHOT_MISMATCH';
    END IF;

    observed_effect_time := pg_catalog.clock_timestamp()::timestamptz(6);

    SELECT o.status
      INTO observed_organization_status
      FROM public.integration_organization o
     WHERE o.organization_id=p_organization_id
     FOR SHARE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Governance unavailable'
            USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE';
    END IF;

    IF observed_organization_status IS DISTINCT FROM 'ACTIVE'
       OR observed_effect_time<p_approval_window_start
       OR observed_effect_time>=p_approval_window_end THEN
        RAISE EXCEPTION 'Current approval eligibility denied'
            USING ERRCODE='P0017',DETAIL='EXPIRED_OR_NOT_YET_VALID';
    END IF;

    PERFORM pg_catalog.pg_advisory_xact_lock(
        pg_catalog.hashtextextended(
            's2a-governance/signer-key/1:' || p_organization_id || ':' ||
                snapshot.result_signer_key_id,
            0
        )
    );

    SELECT count(*)
      INTO key_leaf_count
      FROM public.s2a_signer_key_revision k
     WHERE k.organization_id=p_organization_id
       AND k.signer_key_id=snapshot.result_signer_key_id
       AND NOT EXISTS (
            SELECT 1
              FROM public.s2a_signer_key_revision successor
             WHERE successor.organization_id=k.organization_id
               AND successor.signer_key_id=k.signer_key_id
               AND successor.supersedes_revision=k.revision
       );

    IF key_leaf_count<>1 THEN
        RAISE EXCEPTION 'Signer key lineage conflict'
            USING ERRCODE='P0016',DETAIL='GOVERNANCE_CONFLICT';
    END IF;

    SELECT k.*
      INTO effective_key
      FROM public.s2a_signer_key_revision k
     WHERE k.organization_id=p_organization_id
       AND k.signer_key_id=snapshot.result_signer_key_id
       AND k.effective_at<=observed_effect_time
     ORDER BY k.effective_at DESC,k.revision DESC
     LIMIT 1;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Signer key unavailable'
            USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE';
    END IF;

    IF effective_key.valid_from>observed_effect_time
       OR effective_key.state IS DISTINCT FROM 'ACTIVE' THEN
        RAISE EXCEPTION 'Signer key ineligible'
            USING ERRCODE='P0017',DETAIL='EXPIRED_OR_NOT_YET_VALID';
    END IF;

    IF effective_key.signer_subject_id IS DISTINCT FROM snapshot.result_signer_subject_id
       OR effective_key.algorithm_id IS DISTINCT FROM snapshot.result_algorithm_id
       OR effective_key.subject_public_key_info_der IS DISTINCT FROM snapshot.result_subject_public_key_info_der
       OR effective_key.signer_key_fingerprint IS DISTINCT FROM snapshot.result_signer_key_fingerprint THEN
        RAISE EXCEPTION 'Signer key scope mismatch'
            USING ERRCODE='P0017',DETAIL='SCOPE_MISMATCH';
    END IF;

    PERFORM pg_catalog.pg_advisory_xact_lock(
        pg_catalog.hashtextextended(
            's2a-governance/signer-authority-scope/1:' || p_organization_id || ':' ||
            snapshot.result_signer_subject_id || ':' || snapshot.result_signer_key_id ||
            ':S2A_FIELD_PROOF_APPROVAL:TRANSACTION_IDENTITY_DECISION_WRITE',
            0
        )
    );

    SELECT count(*)
      INTO authority_leaf_count
      FROM public.s2a_signer_authority_revision a
     WHERE a.organization_id=p_organization_id
       AND a.signer_subject_id=snapshot.result_signer_subject_id
       AND a.signer_key_id=snapshot.result_signer_key_id
       AND a.approval_action='S2A_FIELD_PROOF_APPROVAL'
       AND a.permission='TRANSACTION_IDENTITY_DECISION_WRITE'
       AND NOT EXISTS (
            SELECT 1
              FROM public.s2a_signer_authority_revision successor
             WHERE successor.organization_id=a.organization_id
               AND successor.supersedes_signer_authority_id=a.signer_authority_id
       );

    IF authority_leaf_count=0 THEN
        RAISE EXCEPTION 'Signer authority unavailable'
            USING ERRCODE='P0015',DETAIL='GOVERNANCE_UNAVAILABLE';
    ELSIF authority_leaf_count<>1 THEN
        RAISE EXCEPTION 'Signer authority conflict'
            USING ERRCODE='P0016',DETAIL='GOVERNANCE_CONFLICT';
    END IF;

    SELECT a.*
      INTO STRICT current_authority
      FROM public.s2a_signer_authority_revision a
     WHERE a.organization_id=p_organization_id
       AND a.signer_subject_id=snapshot.result_signer_subject_id
       AND a.signer_key_id=snapshot.result_signer_key_id
       AND a.approval_action='S2A_FIELD_PROOF_APPROVAL'
       AND a.permission='TRANSACTION_IDENTITY_DECISION_WRITE'
       AND NOT EXISTS (
            SELECT 1
              FROM public.s2a_signer_authority_revision successor
             WHERE successor.organization_id=a.organization_id
               AND successor.supersedes_signer_authority_id=a.signer_authority_id
       );

    IF current_authority.signer_key_revision IS DISTINCT FROM effective_key.revision
       OR current_authority.signer_key_fingerprint IS DISTINCT FROM effective_key.signer_key_fingerprint THEN
        RAISE EXCEPTION 'Signer authority key scope mismatch'
            USING ERRCODE='P0017',DETAIL='SCOPE_MISMATCH';
    END IF;

    IF current_authority.state IS DISTINCT FROM 'ENABLED'
       OR current_authority.valid_from>observed_effect_time
       OR observed_effect_time>=current_authority.valid_until THEN
        RAISE EXCEPTION 'Signer authority ineligible'
            USING ERRCODE='P0017',DETAIL='EXPIRED_OR_NOT_YET_VALID';
    END IF;

    current_evidence := public.s2a_v041_evidence_fingerprint(
        p_organization_id,
        p_marketplace_order_id,
        p_mercado_livre_connection_id,
        p_omie_connection_id,
        p_source_order_reference,
        p_integration_reference
    );

    IF current_evidence IS DISTINCT FROM snapshot.result_signed_evidence_binding_fingerprint THEN
        RAISE EXCEPTION 'Evidence scope mismatch'
            USING ERRCODE='P0017',DETAIL='SCOPE_MISMATCH';
    END IF;

    SELECT count(*)
      INTO prior_action_count
      FROM public.marketplace_transaction_identity_decision d
     WHERE d.organization_id=p_organization_id
       AND d.grant_id=p_grant_id;

    IF prior_action_count>0 THEN
        RAISE EXCEPTION 'Linked grant action already consumed'
            USING ERRCODE='P0018',DETAIL='SINGLE_ACTION_CONSUMED';
    END IF;

    INSERT INTO public.marketplace_transaction_identity_decision(
        organization_id,
        decision_id,
        omie_connection_id,
        source_order_reference,
        marketplace_order_id,
        kind,
        reason,
        revision,
        supersedes_decision_id,
        ml_connection_id,
        ml_capability,
        ml_progress_version,
        ml_record_ordinal,
        external_order_id,
        currency,
        omie_capability,
        omie_progress_version,
        omie_record_ordinal,
        omie_semantic_fingerprint,
        provider_revision_local,
        principal_id,
        credential_id,
        credential_revision,
        grant_id,
        grant_revision,
        permission,
        authorization_semantic_version,
        authorization_fingerprint,
        intent_fingerprint,
        decision_semantic_fingerprint,
        provenance,
        correlation_id
    )
    VALUES (
        p_organization_id,
        p_decision_id,
        p_decision_omie_connection_id,
        p_decision_source_order_reference,
        p_decision_marketplace_order_id,
        p_kind,
        p_decision_reason,
        p_revision,
        p_supersedes_decision_id,
        p_ml_connection_id,
        p_ml_capability,
        p_ml_progress_version,
        p_ml_record_ordinal,
        p_external_order_id,
        p_currency,
        p_omie_capability,
        p_omie_progress_version,
        p_omie_record_ordinal,
        p_omie_semantic_fingerprint,
        p_provider_revision_local,
        p_principal_id,
        p_credential_id,
        p_credential_revision,
        p_grant_id,
        p_grant_revision,
        p_decision_permission,
        p_authorization_semantic_version,
        p_authorization_fingerprint,
        p_intent_fingerprint,
        p_decision_semantic_fingerprint,
        p_decision_provenance,
        p_decision_correlation_id
    )
    RETURNING * INTO persisted;

    RETURN QUERY
    SELECT
        'APPLIED'::text,
        persisted.decision_id,
        persisted.decision_semantic_fingerprint::text,
        persisted.decided_at;
END;
$$;

REVOKE INSERT,UPDATE,DELETE ON public.command_principal,public.command_credential_revision,
  public.command_permission_grant,public.command_authority_operation FROM flooow_command_issuer;
REVOKE INSERT ON public.marketplace_transaction_identity_decision FROM flooow_command_runtime;
REVOKE ALL ON public.s2a_attestation_consumption FROM PUBLIC;
REVOKE ALL ON FUNCTION public.s2a_v042_reject_consumption_mutation() FROM PUBLIC;
REVOKE ALL ON FUNCTION public.s2a_v042_text(text) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.s2a_v042_frame(bytea) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.s2a_v042_instant(timestamptz) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.s2a_v042_authority_intent(text,uuid,uuid,uuid,uuid,uuid,uuid,bytea,uuid,text,text,uuid,uuid,text,text) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.s2a_v042_authority_receipt(text,text,uuid,uuid,integer,uuid,integer,text,text) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.s2a_v042_revalidate_snapshot(uuid,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text,integer,integer,bytea,text,bytea,text,uuid,uuid,integer,text,text,bytea,bytea,uuid,integer,text,timestamptz,text,text) FROM PUBLIC;
BEGIN;

DO $v042_owner_preflight$
DECLARE
    owner_role pg_catalog.pg_roles%ROWTYPE;
    migration_role pg_catalog.pg_roles%ROWTYPE;
BEGIN
    IF pg_catalog.current_setting('server_version_num')::integer < 180000
       OR pg_catalog.current_setting('server_version_num')::integer >= 190000 THEN
        RAISE EXCEPTION 'V042 privilege cutover requires PostgreSQL 18.x';
    END IF;

    IF CURRENT_USER IS DISTINCT FROM SESSION_USER THEN
        RAISE EXCEPTION 'V042 privilege cutover requires CURRENT_USER = SESSION_USER';
    END IF;

    SELECT * INTO migration_role
      FROM pg_catalog.pg_roles
     WHERE rolname = CURRENT_USER;

    IF NOT FOUND OR NOT migration_role.rolsuper THEN
        RAISE EXCEPTION 'V042 privilege cutover requires the repository bootstrap superuser migration identity';
    END IF;

    IF (SELECT pg_catalog.count(*) FROM pg_catalog.pg_roles
         WHERE rolname = ANY (ARRAY[
             'flooow_command_issuer',
             'flooow_command_runtime',
             'flooow_attestation_verifier',
             'flooow_approval_governance'
         ]::text[])) <> 4 THEN
        RAISE EXCEPTION 'V042 protected operational role set is incomplete';
    END IF;

    IF CURRENT_USER = ANY (ARRAY[
        'flooow_command_issuer',
        'flooow_command_runtime',
        'flooow_attestation_verifier',
        'flooow_approval_governance',
        'flooow_v042_capability_owner'
    ]::name[]) THEN
        RAISE EXCEPTION 'V042 migration identity is inside the protected operational trust set';
    END IF;

    SELECT * INTO owner_role
      FROM pg_catalog.pg_roles
     WHERE rolname = 'flooow_v042_capability_owner';

    IF NOT FOUND THEN
        CREATE ROLE flooow_v042_capability_owner
            NOLOGIN
            NOINHERIT
            NOSUPERUSER
            NOCREATEDB
            NOCREATEROLE
            NOREPLICATION
            NOBYPASSRLS;

        SELECT * INTO owner_role
          FROM pg_catalog.pg_roles
         WHERE rolname = 'flooow_v042_capability_owner';
    END IF;

    IF owner_role.rolcanlogin
       OR owner_role.rolinherit
       OR owner_role.rolsuper
       OR owner_role.rolcreatedb
       OR owner_role.rolcreaterole
       OR owner_role.rolreplication
       OR owner_role.rolbypassrls THEN
        RAISE EXCEPTION 'Unsafe pre-existing flooow_v042_capability_owner attributes';
    END IF;

    IF EXISTS (
        SELECT 1
          FROM pg_catalog.pg_auth_members m
         WHERE m.roleid = owner_role.oid
            OR m.member = owner_role.oid
    ) THEN
        RAISE EXCEPTION 'Pre-existing flooow_v042_capability_owner membership is forbidden';
    END IF;

    IF EXISTS (
        WITH RECURSIVE membership(member, roleid) AS (
            SELECT m.member, m.roleid
              FROM pg_catalog.pg_auth_members m
            UNION
            SELECT c.member, m.roleid
              FROM membership c
              JOIN pg_catalog.pg_auth_members m ON m.member = c.roleid
        )
        SELECT 1
          FROM membership c
          JOIN pg_catalog.pg_roles member_role ON member_role.oid = c.member
          JOIN pg_catalog.pg_roles granted_role ON granted_role.oid = c.roleid
         WHERE member_role.rolname = ANY (ARRAY[
                   'flooow_command_issuer',
                   'flooow_command_runtime',
                   'flooow_attestation_verifier',
                   'flooow_approval_governance'
               ]::text[])
           AND granted_role.rolname = ANY (ARRAY[
                   'flooow_command_issuer',
                   'flooow_command_runtime',
                   'flooow_attestation_verifier',
                   'flooow_approval_governance'
               ]::text[])
           AND member_role.oid <> granted_role.oid
    ) THEN
        RAISE EXCEPTION 'Protected operational role graph is transitively contaminated';
    END IF;

    IF EXISTS (
        SELECT 1
          FROM (VALUES
            ('public.s2a_v042_begin_attested_principal_verification(uuid,uuid,uuid,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text)'),
            ('public.s2a_v042_begin_attested_initial_credential_verification(uuid,uuid,uuid,uuid,uuid,bytea,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text)'),
            ('public.s2a_v042_begin_attested_grant_verification(uuid,uuid,uuid,uuid,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text)'),
            ('public.s2a_v042_apply_attested_principal(uuid,uuid,uuid,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text,integer,integer,bytea,text,bytea,text,uuid,uuid,integer,text,text,bytea,bytea,uuid,integer,text,timestamptz,text,text)'),
            ('public.s2a_v042_apply_attested_initial_credential(uuid,uuid,uuid,uuid,uuid,bytea,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text,integer,integer,bytea,text,bytea,text,uuid,uuid,integer,text,text,bytea,bytea,uuid,integer,text,timestamptz,text,text)'),
            ('public.s2a_v042_apply_attested_grant(uuid,uuid,uuid,uuid,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text,integer,integer,bytea,text,bytea,text,uuid,uuid,integer,text,text,bytea,bytea,uuid,integer,text,timestamptz,text,text)'),
            ('public.s2a_v042_apply_legacy_unlinked_decision(uuid,uuid,uuid,text,uuid,text,text,integer,uuid,uuid,text,bigint,integer,text,character,text,bigint,integer,character,timestamp,uuid,uuid,integer,uuid,integer,text,text,character,character,character,text,uuid)'),
            ('public.s2a_v042_begin_attested_decision_verification(uuid,uuid,uuid,integer,uuid,uuid,text,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text)'),
            ('public.s2a_v042_apply_attested_decision(uuid,uuid,uuid,text,uuid,text,text,integer,uuid,uuid,text,bigint,integer,text,character,text,bigint,integer,character,timestamp,uuid,uuid,integer,uuid,integer,text,text,character,character,character,text,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text,integer,integer,bytea,text,bytea,text,uuid,uuid,integer,text,text,bytea,bytea,uuid,integer,text,timestamptz,text,text)')
          ) AS required(identity)
         WHERE pg_catalog.to_regprocedure(required.identity) IS NULL
    ) THEN
        RAISE EXCEPTION 'V042 caller function set is incomplete or ambiguous';
    END IF;
END;
$v042_owner_preflight$;

GRANT USAGE ON SCHEMA public TO flooow_v042_capability_owner;

GRANT SELECT ON TABLE public.integration_organization TO flooow_v042_capability_owner;
GRANT UPDATE ON TABLE public.integration_organization TO flooow_v042_capability_owner;
GRANT SELECT ON TABLE public.integration_connection TO flooow_v042_capability_owner;
GRANT SELECT ON TABLE public.command_principal TO flooow_v042_capability_owner;
GRANT INSERT ON TABLE public.command_principal TO flooow_v042_capability_owner;
GRANT UPDATE ON TABLE public.command_principal TO flooow_v042_capability_owner;
GRANT SELECT ON TABLE public.command_credential_revision TO flooow_v042_capability_owner;
GRANT INSERT ON TABLE public.command_credential_revision TO flooow_v042_capability_owner;
GRANT SELECT ON TABLE public.command_permission_grant TO flooow_v042_capability_owner;
GRANT INSERT ON TABLE public.command_permission_grant TO flooow_v042_capability_owner;
GRANT SELECT ON TABLE public.command_authority_operation TO flooow_v042_capability_owner;
GRANT INSERT ON TABLE public.command_authority_operation TO flooow_v042_capability_owner;
GRANT SELECT ON TABLE public.s2a_attestation_consumption TO flooow_v042_capability_owner;
GRANT INSERT ON TABLE public.s2a_attestation_consumption TO flooow_v042_capability_owner;
GRANT SELECT ON TABLE public.s2a_accepted_attestation TO flooow_v042_capability_owner;
GRANT SELECT ON TABLE public.s2a_signer_key_revision TO flooow_v042_capability_owner;
GRANT SELECT ON TABLE public.s2a_signer_authority_revision TO flooow_v042_capability_owner;
GRANT SELECT ON TABLE public.integration_connector_progress TO flooow_v042_capability_owner;
GRANT UPDATE ON TABLE public.integration_connector_progress TO flooow_v042_capability_owner;
GRANT SELECT ON TABLE public.integration_omie_transaction_evidence TO flooow_v042_capability_owner;
GRANT SELECT ON TABLE public.marketplace_order_occurrence_source_promotion TO flooow_v042_capability_owner;
GRANT SELECT ON TABLE public.marketplace_transaction_identity_decision TO flooow_v042_capability_owner;
GRANT INSERT ON TABLE public.marketplace_transaction_identity_decision TO flooow_v042_capability_owner;
GRANT SELECT ON TABLE public.marketplace_transaction_identity_head TO flooow_v042_capability_owner;
GRANT SELECT ON TABLE public.marketplace_order_identity_registry TO flooow_v042_capability_owner;
GRANT SELECT ON TABLE public.integration_mercado_livre_order_source_observation TO flooow_v042_capability_owner;
GRANT SELECT ON TABLE public.integration_omie_transaction_evidence_v3 TO flooow_v042_capability_owner;
GRANT SELECT ON TABLE public.integration_connector_page_commit TO flooow_v042_capability_owner;

GRANT EXECUTE ON FUNCTION public.s2a_v041_evidence_fingerprint(uuid,uuid,uuid,uuid,text,text) TO flooow_v042_capability_owner;
GRANT EXECUTE ON FUNCTION public.s2a_v041_manifest_bytes(integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text) TO flooow_v042_capability_owner;
GRANT EXECUTE ON FUNCTION public.s2a_v041_frame(bytea) TO flooow_v042_capability_owner;
GRANT EXECUTE ON FUNCTION public.s2a_v041_text(text) TO flooow_v042_capability_owner;
GRANT EXECUTE ON FUNCTION public.s2a_v041_instant(timestamptz) TO flooow_v042_capability_owner;
GRANT EXECUTE ON FUNCTION public.s2a_v041_local(timestamp) TO flooow_v042_capability_owner;
GRANT EXECUTE ON FUNCTION public.s2a_v041_nullable_text(text) TO flooow_v042_capability_owner;
GRANT EXECUTE ON FUNCTION public.s2a_v042_authority_intent(text,uuid,uuid,uuid,uuid,uuid,uuid,bytea,uuid,text,text,uuid,uuid,text,text) TO flooow_v042_capability_owner;
GRANT EXECUTE ON FUNCTION public.s2a_v042_authority_receipt(text,text,uuid,uuid,integer,uuid,integer,text,text) TO flooow_v042_capability_owner;
GRANT EXECUTE ON FUNCTION public.s2a_v042_frame(bytea) TO flooow_v042_capability_owner;
GRANT EXECUTE ON FUNCTION public.s2a_v042_text(text) TO flooow_v042_capability_owner;
GRANT EXECUTE ON FUNCTION public.s2a_v042_revalidate_snapshot(uuid,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text,integer,integer,bytea,text,bytea,text,uuid,uuid,integer,text,text,bytea,bytea,uuid,integer,text,timestamptz,text,text) TO flooow_v042_capability_owner;
GRANT EXECUTE ON FUNCTION public.command_authorization_organization_lock(uuid) TO flooow_v042_capability_owner;
GRANT EXECUTE ON FUNCTION public.transaction_identity_progress_lock(uuid,uuid) TO flooow_v042_capability_owner;
GRANT EXECUTE ON FUNCTION public.transaction_identity_locks(uuid,uuid,uuid,uuid,text,uuid) TO flooow_v042_capability_owner;
GRANT EXECUTE ON FUNCTION public.transaction_identity_withdrawal_locks(uuid,uuid,uuid,uuid,text,uuid) TO flooow_v042_capability_owner;
GRANT EXECUTE ON FUNCTION public.transaction_identity_hash(text[]) TO flooow_v042_capability_owner;
GRANT EXECUTE ON FUNCTION public.transaction_identity_grant_fingerprint(uuid,uuid) TO flooow_v042_capability_owner;
GRANT EXECUTE ON FUNCTION public.transaction_identity_intent(public.marketplace_transaction_identity_decision) TO flooow_v042_capability_owner;
GRANT EXECUTE ON FUNCTION public.transaction_identity_fingerprint(public.marketplace_transaction_identity_decision) TO flooow_v042_capability_owner;

GRANT CREATE ON SCHEMA public TO flooow_v042_capability_owner;

GRANT flooow_v042_capability_owner TO SESSION_USER
    WITH ADMIN FALSE, INHERIT FALSE, SET TRUE;

DO $v042_temporary_membership_assertion$
BEGIN
    IF (SELECT pg_catalog.count(*)
          FROM pg_catalog.pg_auth_members m
         WHERE m.roleid = 'flooow_v042_capability_owner'::pg_catalog.regrole
           AND m.member = SESSION_USER::pg_catalog.regrole
           AND NOT m.admin_option
           AND NOT m.inherit_option
           AND m.set_option) <> 1 THEN
        RAISE EXCEPTION 'V042 temporary owner membership options are not exact';
    END IF;
END;
$v042_temporary_membership_assertion$;

ALTER FUNCTION public.s2a_v042_begin_attested_principal_verification(uuid,uuid,uuid,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text) OWNER TO flooow_v042_capability_owner;
ALTER FUNCTION public.s2a_v042_begin_attested_initial_credential_verification(uuid,uuid,uuid,uuid,uuid,bytea,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text) OWNER TO flooow_v042_capability_owner;
ALTER FUNCTION public.s2a_v042_begin_attested_grant_verification(uuid,uuid,uuid,uuid,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text) OWNER TO flooow_v042_capability_owner;
ALTER FUNCTION public.s2a_v042_apply_attested_principal(uuid,uuid,uuid,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text,integer,integer,bytea,text,bytea,text,uuid,uuid,integer,text,text,bytea,bytea,uuid,integer,text,timestamptz,text,text) OWNER TO flooow_v042_capability_owner;
ALTER FUNCTION public.s2a_v042_apply_attested_initial_credential(uuid,uuid,uuid,uuid,uuid,bytea,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text,integer,integer,bytea,text,bytea,text,uuid,uuid,integer,text,text,bytea,bytea,uuid,integer,text,timestamptz,text,text) OWNER TO flooow_v042_capability_owner;
ALTER FUNCTION public.s2a_v042_apply_attested_grant(uuid,uuid,uuid,uuid,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text,integer,integer,bytea,text,bytea,text,uuid,uuid,integer,text,text,bytea,bytea,uuid,integer,text,timestamptz,text,text) OWNER TO flooow_v042_capability_owner;
ALTER FUNCTION public.s2a_v042_apply_legacy_unlinked_decision(uuid,uuid,uuid,text,uuid,text,text,integer,uuid,uuid,text,bigint,integer,text,character,text,bigint,integer,character,timestamp,uuid,uuid,integer,uuid,integer,text,text,character,character,character,text,uuid) OWNER TO flooow_v042_capability_owner;
ALTER FUNCTION public.s2a_v042_begin_attested_decision_verification(uuid,uuid,uuid,integer,uuid,uuid,text,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text) OWNER TO flooow_v042_capability_owner;
ALTER FUNCTION public.s2a_v042_apply_attested_decision(uuid,uuid,uuid,text,uuid,text,text,integer,uuid,uuid,text,bigint,integer,text,character,text,bigint,integer,character,timestamp,uuid,uuid,integer,uuid,integer,text,text,character,character,character,text,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text,integer,integer,bytea,text,bytea,text,uuid,uuid,integer,text,text,bytea,bytea,uuid,integer,text,timestamptz,text,text) OWNER TO flooow_v042_capability_owner;

REVOKE CREATE ON SCHEMA public FROM flooow_v042_capability_owner;

REVOKE flooow_v042_capability_owner FROM SESSION_USER;

REVOKE EXECUTE ON FUNCTION public.s2a_v042_begin_attested_principal_verification(uuid,uuid,uuid,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION public.s2a_v042_begin_attested_initial_credential_verification(uuid,uuid,uuid,uuid,uuid,bytea,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION public.s2a_v042_begin_attested_grant_verification(uuid,uuid,uuid,uuid,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION public.s2a_v042_apply_attested_principal(uuid,uuid,uuid,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text,integer,integer,bytea,text,bytea,text,uuid,uuid,integer,text,text,bytea,bytea,uuid,integer,text,timestamptz,text,text) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION public.s2a_v042_apply_attested_initial_credential(uuid,uuid,uuid,uuid,uuid,bytea,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text,integer,integer,bytea,text,bytea,text,uuid,uuid,integer,text,text,bytea,bytea,uuid,integer,text,timestamptz,text,text) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION public.s2a_v042_apply_attested_grant(uuid,uuid,uuid,uuid,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text,integer,integer,bytea,text,bytea,text,uuid,uuid,integer,text,text,bytea,bytea,uuid,integer,text,timestamptz,text,text) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION public.s2a_v042_apply_legacy_unlinked_decision(uuid,uuid,uuid,text,uuid,text,text,integer,uuid,uuid,text,bigint,integer,text,character,text,bigint,integer,character,timestamp,uuid,uuid,integer,uuid,integer,text,text,character,character,character,text,uuid) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION public.s2a_v042_begin_attested_decision_verification(uuid,uuid,uuid,integer,uuid,uuid,text,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION public.s2a_v042_apply_attested_decision(uuid,uuid,uuid,text,uuid,text,text,integer,uuid,uuid,text,bigint,integer,text,character,text,bigint,integer,character,timestamp,uuid,uuid,integer,uuid,integer,text,text,character,character,character,text,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text,integer,integer,bytea,text,bytea,text,uuid,uuid,integer,text,text,bytea,bytea,uuid,integer,text,timestamptz,text,text) FROM PUBLIC;

REVOKE EXECUTE ON FUNCTION public.s2a_v042_begin_attested_principal_verification(uuid,uuid,uuid,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text) FROM flooow_command_runtime;
REVOKE EXECUTE ON FUNCTION public.s2a_v042_begin_attested_principal_verification(uuid,uuid,uuid,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text) FROM flooow_attestation_verifier;
REVOKE EXECUTE ON FUNCTION public.s2a_v042_begin_attested_principal_verification(uuid,uuid,uuid,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text) FROM flooow_approval_governance;
REVOKE EXECUTE ON FUNCTION public.s2a_v042_begin_attested_initial_credential_verification(uuid,uuid,uuid,uuid,uuid,bytea,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text) FROM flooow_command_runtime;
REVOKE EXECUTE ON FUNCTION public.s2a_v042_begin_attested_initial_credential_verification(uuid,uuid,uuid,uuid,uuid,bytea,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text) FROM flooow_attestation_verifier;
REVOKE EXECUTE ON FUNCTION public.s2a_v042_begin_attested_initial_credential_verification(uuid,uuid,uuid,uuid,uuid,bytea,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text) FROM flooow_approval_governance;
REVOKE EXECUTE ON FUNCTION public.s2a_v042_begin_attested_grant_verification(uuid,uuid,uuid,uuid,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text) FROM flooow_command_runtime;
REVOKE EXECUTE ON FUNCTION public.s2a_v042_begin_attested_grant_verification(uuid,uuid,uuid,uuid,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text) FROM flooow_attestation_verifier;
REVOKE EXECUTE ON FUNCTION public.s2a_v042_begin_attested_grant_verification(uuid,uuid,uuid,uuid,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text) FROM flooow_approval_governance;
REVOKE EXECUTE ON FUNCTION public.s2a_v042_apply_attested_principal(uuid,uuid,uuid,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text,integer,integer,bytea,text,bytea,text,uuid,uuid,integer,text,text,bytea,bytea,uuid,integer,text,timestamptz,text,text) FROM flooow_command_runtime;
REVOKE EXECUTE ON FUNCTION public.s2a_v042_apply_attested_principal(uuid,uuid,uuid,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text,integer,integer,bytea,text,bytea,text,uuid,uuid,integer,text,text,bytea,bytea,uuid,integer,text,timestamptz,text,text) FROM flooow_attestation_verifier;
REVOKE EXECUTE ON FUNCTION public.s2a_v042_apply_attested_principal(uuid,uuid,uuid,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text,integer,integer,bytea,text,bytea,text,uuid,uuid,integer,text,text,bytea,bytea,uuid,integer,text,timestamptz,text,text) FROM flooow_approval_governance;
REVOKE EXECUTE ON FUNCTION public.s2a_v042_apply_attested_initial_credential(uuid,uuid,uuid,uuid,uuid,bytea,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text,integer,integer,bytea,text,bytea,text,uuid,uuid,integer,text,text,bytea,bytea,uuid,integer,text,timestamptz,text,text) FROM flooow_command_runtime;
REVOKE EXECUTE ON FUNCTION public.s2a_v042_apply_attested_initial_credential(uuid,uuid,uuid,uuid,uuid,bytea,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text,integer,integer,bytea,text,bytea,text,uuid,uuid,integer,text,text,bytea,bytea,uuid,integer,text,timestamptz,text,text) FROM flooow_attestation_verifier;
REVOKE EXECUTE ON FUNCTION public.s2a_v042_apply_attested_initial_credential(uuid,uuid,uuid,uuid,uuid,bytea,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text,integer,integer,bytea,text,bytea,text,uuid,uuid,integer,text,text,bytea,bytea,uuid,integer,text,timestamptz,text,text) FROM flooow_approval_governance;
REVOKE EXECUTE ON FUNCTION public.s2a_v042_apply_attested_grant(uuid,uuid,uuid,uuid,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text,integer,integer,bytea,text,bytea,text,uuid,uuid,integer,text,text,bytea,bytea,uuid,integer,text,timestamptz,text,text) FROM flooow_command_runtime;
REVOKE EXECUTE ON FUNCTION public.s2a_v042_apply_attested_grant(uuid,uuid,uuid,uuid,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text,integer,integer,bytea,text,bytea,text,uuid,uuid,integer,text,text,bytea,bytea,uuid,integer,text,timestamptz,text,text) FROM flooow_attestation_verifier;
REVOKE EXECUTE ON FUNCTION public.s2a_v042_apply_attested_grant(uuid,uuid,uuid,uuid,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text,integer,integer,bytea,text,bytea,text,uuid,uuid,integer,text,text,bytea,bytea,uuid,integer,text,timestamptz,text,text) FROM flooow_approval_governance;
REVOKE EXECUTE ON FUNCTION public.s2a_v042_apply_legacy_unlinked_decision(uuid,uuid,uuid,text,uuid,text,text,integer,uuid,uuid,text,bigint,integer,text,character,text,bigint,integer,character,timestamp,uuid,uuid,integer,uuid,integer,text,text,character,character,character,text,uuid) FROM flooow_command_issuer;
REVOKE EXECUTE ON FUNCTION public.s2a_v042_apply_legacy_unlinked_decision(uuid,uuid,uuid,text,uuid,text,text,integer,uuid,uuid,text,bigint,integer,text,character,text,bigint,integer,character,timestamp,uuid,uuid,integer,uuid,integer,text,text,character,character,character,text,uuid) FROM flooow_attestation_verifier;
REVOKE EXECUTE ON FUNCTION public.s2a_v042_apply_legacy_unlinked_decision(uuid,uuid,uuid,text,uuid,text,text,integer,uuid,uuid,text,bigint,integer,text,character,text,bigint,integer,character,timestamp,uuid,uuid,integer,uuid,integer,text,text,character,character,character,text,uuid) FROM flooow_approval_governance;
REVOKE EXECUTE ON FUNCTION public.s2a_v042_begin_attested_decision_verification(uuid,uuid,uuid,integer,uuid,uuid,text,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text) FROM flooow_command_issuer;
REVOKE EXECUTE ON FUNCTION public.s2a_v042_begin_attested_decision_verification(uuid,uuid,uuid,integer,uuid,uuid,text,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text) FROM flooow_attestation_verifier;
REVOKE EXECUTE ON FUNCTION public.s2a_v042_begin_attested_decision_verification(uuid,uuid,uuid,integer,uuid,uuid,text,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text) FROM flooow_approval_governance;
REVOKE EXECUTE ON FUNCTION public.s2a_v042_apply_attested_decision(uuid,uuid,uuid,text,uuid,text,text,integer,uuid,uuid,text,bigint,integer,text,character,text,bigint,integer,character,timestamp,uuid,uuid,integer,uuid,integer,text,text,character,character,character,text,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text,integer,integer,bytea,text,bytea,text,uuid,uuid,integer,text,text,bytea,bytea,uuid,integer,text,timestamptz,text,text) FROM flooow_command_issuer;
REVOKE EXECUTE ON FUNCTION public.s2a_v042_apply_attested_decision(uuid,uuid,uuid,text,uuid,text,text,integer,uuid,uuid,text,bigint,integer,text,character,text,bigint,integer,character,timestamp,uuid,uuid,integer,uuid,integer,text,text,character,character,character,text,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text,integer,integer,bytea,text,bytea,text,uuid,uuid,integer,text,text,bytea,bytea,uuid,integer,text,timestamptz,text,text) FROM flooow_attestation_verifier;
REVOKE EXECUTE ON FUNCTION public.s2a_v042_apply_attested_decision(uuid,uuid,uuid,text,uuid,text,text,integer,uuid,uuid,text,bigint,integer,text,character,text,bigint,integer,character,timestamp,uuid,uuid,integer,uuid,integer,text,text,character,character,character,text,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text,integer,integer,bytea,text,bytea,text,uuid,uuid,integer,text,text,bytea,bytea,uuid,integer,text,timestamptz,text,text) FROM flooow_approval_governance;

GRANT EXECUTE ON FUNCTION public.s2a_v042_begin_attested_principal_verification(uuid,uuid,uuid,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text) TO flooow_command_issuer;
GRANT EXECUTE ON FUNCTION public.s2a_v042_begin_attested_initial_credential_verification(uuid,uuid,uuid,uuid,uuid,bytea,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text) TO flooow_command_issuer;
GRANT EXECUTE ON FUNCTION public.s2a_v042_begin_attested_grant_verification(uuid,uuid,uuid,uuid,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text) TO flooow_command_issuer;
GRANT EXECUTE ON FUNCTION public.s2a_v042_apply_attested_principal(uuid,uuid,uuid,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text,integer,integer,bytea,text,bytea,text,uuid,uuid,integer,text,text,bytea,bytea,uuid,integer,text,timestamptz,text,text) TO flooow_command_issuer;
GRANT EXECUTE ON FUNCTION public.s2a_v042_apply_attested_initial_credential(uuid,uuid,uuid,uuid,uuid,bytea,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text,integer,integer,bytea,text,bytea,text,uuid,uuid,integer,text,text,bytea,bytea,uuid,integer,text,timestamptz,text,text) TO flooow_command_issuer;
GRANT EXECUTE ON FUNCTION public.s2a_v042_apply_attested_grant(uuid,uuid,uuid,uuid,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text,integer,integer,bytea,text,bytea,text,uuid,uuid,integer,text,text,bytea,bytea,uuid,integer,text,timestamptz,text,text) TO flooow_command_issuer;

GRANT EXECUTE ON FUNCTION public.s2a_v042_apply_legacy_unlinked_decision(uuid,uuid,uuid,text,uuid,text,text,integer,uuid,uuid,text,bigint,integer,text,character,text,bigint,integer,character,timestamp,uuid,uuid,integer,uuid,integer,text,text,character,character,character,text,uuid) TO flooow_command_runtime;
GRANT EXECUTE ON FUNCTION public.s2a_v042_begin_attested_decision_verification(uuid,uuid,uuid,integer,uuid,uuid,text,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text) TO flooow_command_runtime;
GRANT EXECUTE ON FUNCTION public.s2a_v042_apply_attested_decision(uuid,uuid,uuid,text,uuid,text,text,integer,uuid,uuid,text,bigint,integer,text,character,text,bigint,integer,character,timestamp,uuid,uuid,integer,uuid,integer,text,text,character,character,character,text,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text,integer,integer,bytea,text,bytea,text,uuid,uuid,integer,text,text,bytea,bytea,uuid,integer,text,timestamptz,text,text) TO flooow_command_runtime;

REVOKE INSERT, UPDATE, DELETE ON TABLE public.command_principal FROM flooow_command_issuer;
REVOKE INSERT, UPDATE, DELETE ON TABLE public.command_credential_revision FROM flooow_command_issuer;
REVOKE INSERT, UPDATE, DELETE ON TABLE public.command_permission_grant FROM flooow_command_issuer;
REVOKE INSERT, UPDATE, DELETE ON TABLE public.command_authority_operation FROM flooow_command_issuer;

REVOKE INSERT ON TABLE public.marketplace_transaction_identity_decision FROM flooow_command_runtime;

DO $v042_final_assertions$
DECLARE
    owner_role pg_catalog.pg_roles%ROWTYPE;
    owner_oid oid;
BEGIN
    SELECT * INTO STRICT owner_role
      FROM pg_catalog.pg_roles
     WHERE rolname = 'flooow_v042_capability_owner';
    owner_oid := owner_role.oid;

    IF owner_role.rolcanlogin
       OR owner_role.rolinherit
       OR owner_role.rolsuper
       OR owner_role.rolcreatedb
       OR owner_role.rolcreaterole
       OR owner_role.rolreplication
       OR owner_role.rolbypassrls THEN
        RAISE EXCEPTION 'Final V042 owner attributes are unsafe';
    END IF;

    IF EXISTS (
        SELECT 1
          FROM pg_catalog.pg_auth_members m
         WHERE m.roleid = owner_oid OR m.member = owner_oid
    ) THEN
        RAISE EXCEPTION 'Final V042 owner membership is forbidden';
    END IF;

    IF NOT pg_catalog.has_schema_privilege('flooow_v042_capability_owner', 'public', 'USAGE')
       OR pg_catalog.has_schema_privilege('flooow_v042_capability_owner', 'public', 'CREATE') THEN
        RAISE EXCEPTION 'Final V042 owner schema privileges are not exact';
    END IF;

    IF EXISTS (SELECT 1 FROM pg_catalog.pg_namespace WHERE nspowner = owner_oid)
       OR EXISTS (SELECT 1 FROM pg_catalog.pg_database WHERE datdba = owner_oid)
       OR EXISTS (SELECT 1 FROM pg_catalog.pg_class WHERE relowner = owner_oid) THEN
        RAISE EXCEPTION 'Final V042 owner has forbidden schema, database, table, view, or sequence ownership';
    END IF;

    IF EXISTS (
        WITH targets(identity) AS (VALUES
            ('public.s2a_v042_begin_attested_principal_verification(uuid,uuid,uuid,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text)'),
            ('public.s2a_v042_begin_attested_initial_credential_verification(uuid,uuid,uuid,uuid,uuid,bytea,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text)'),
            ('public.s2a_v042_begin_attested_grant_verification(uuid,uuid,uuid,uuid,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text)'),
            ('public.s2a_v042_apply_attested_principal(uuid,uuid,uuid,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text,integer,integer,bytea,text,bytea,text,uuid,uuid,integer,text,text,bytea,bytea,uuid,integer,text,timestamptz,text,text)'),
            ('public.s2a_v042_apply_attested_initial_credential(uuid,uuid,uuid,uuid,uuid,bytea,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text,integer,integer,bytea,text,bytea,text,uuid,uuid,integer,text,text,bytea,bytea,uuid,integer,text,timestamptz,text,text)'),
            ('public.s2a_v042_apply_attested_grant(uuid,uuid,uuid,uuid,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text,integer,integer,bytea,text,bytea,text,uuid,uuid,integer,text,text,bytea,bytea,uuid,integer,text,timestamptz,text,text)'),
            ('public.s2a_v042_apply_legacy_unlinked_decision(uuid,uuid,uuid,text,uuid,text,text,integer,uuid,uuid,text,bigint,integer,text,character,text,bigint,integer,character,timestamp,uuid,uuid,integer,uuid,integer,text,text,character,character,character,text,uuid)'),
            ('public.s2a_v042_begin_attested_decision_verification(uuid,uuid,uuid,integer,uuid,uuid,text,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text)'),
            ('public.s2a_v042_apply_attested_decision(uuid,uuid,uuid,text,uuid,text,text,integer,uuid,uuid,text,bigint,integer,text,character,text,bigint,integer,character,timestamp,uuid,uuid,integer,uuid,integer,text,text,character,character,character,text,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text,integer,integer,bytea,text,bytea,text,uuid,uuid,integer,text,text,bytea,bytea,uuid,integer,text,timestamptz,text,text)')
        )
        SELECT 1
          FROM targets t
          JOIN pg_catalog.pg_proc p ON p.oid = pg_catalog.to_regprocedure(t.identity)
         WHERE p.proowner <> owner_oid
            OR NOT p.prosecdef
            OR NOT EXISTS (
                SELECT 1
                  FROM pg_catalog.unnest(p.proconfig) AS config(setting)
                 WHERE pg_catalog.replace(config.setting, ' ', '') = 'search_path=pg_catalog,pg_temp'
            )
    ) THEN
        RAISE EXCEPTION 'Final V042 caller ownership, SECURITY DEFINER, or search_path posture is incorrect';
    END IF;

    IF (SELECT pg_catalog.count(*) FROM pg_catalog.pg_proc WHERE proowner = owner_oid) <> 9 THEN
        RAISE EXCEPTION 'Final V042 owner function ownership count is not nine';
    END IF;

    IF EXISTS (
        WITH allowed(relid, privilege) AS (VALUES
            ('public.integration_organization'::pg_catalog.regclass, 'SELECT'),
            ('public.integration_organization'::pg_catalog.regclass, 'UPDATE'),
            ('public.integration_connection'::pg_catalog.regclass, 'SELECT'),
            ('public.command_principal'::pg_catalog.regclass, 'SELECT'),
            ('public.command_principal'::pg_catalog.regclass, 'INSERT'),
            ('public.command_principal'::pg_catalog.regclass, 'UPDATE'),
            ('public.command_credential_revision'::pg_catalog.regclass, 'SELECT'),
            ('public.command_credential_revision'::pg_catalog.regclass, 'INSERT'),
            ('public.command_permission_grant'::pg_catalog.regclass, 'SELECT'),
            ('public.command_permission_grant'::pg_catalog.regclass, 'INSERT'),
            ('public.command_authority_operation'::pg_catalog.regclass, 'SELECT'),
            ('public.command_authority_operation'::pg_catalog.regclass, 'INSERT'),
            ('public.s2a_attestation_consumption'::pg_catalog.regclass, 'SELECT'),
            ('public.s2a_attestation_consumption'::pg_catalog.regclass, 'INSERT'),
            ('public.s2a_accepted_attestation'::pg_catalog.regclass, 'SELECT'),
            ('public.s2a_signer_key_revision'::pg_catalog.regclass, 'SELECT'),
            ('public.s2a_signer_authority_revision'::pg_catalog.regclass, 'SELECT'),
            ('public.integration_connector_progress'::pg_catalog.regclass, 'SELECT'),
            ('public.integration_connector_progress'::pg_catalog.regclass, 'UPDATE'),
            ('public.integration_omie_transaction_evidence'::pg_catalog.regclass, 'SELECT'),
            ('public.marketplace_order_occurrence_source_promotion'::pg_catalog.regclass, 'SELECT'),
            ('public.marketplace_transaction_identity_decision'::pg_catalog.regclass, 'SELECT'),
            ('public.marketplace_transaction_identity_decision'::pg_catalog.regclass, 'INSERT'),
            ('public.marketplace_transaction_identity_head'::pg_catalog.regclass, 'SELECT'),
            ('public.marketplace_order_identity_registry'::pg_catalog.regclass, 'SELECT'),
            ('public.integration_mercado_livre_order_source_observation'::pg_catalog.regclass, 'SELECT'),
            ('public.integration_omie_transaction_evidence_v3'::pg_catalog.regclass, 'SELECT'),
            ('public.integration_connector_page_commit'::pg_catalog.regclass, 'SELECT')
        ), checked_privileges(privilege) AS (VALUES
            ('SELECT'), ('INSERT'), ('UPDATE'), ('DELETE'), ('TRUNCATE'),
            ('REFERENCES'), ('TRIGGER'), ('MAINTAIN')
        )
        SELECT 1
          FROM pg_catalog.pg_class c
          JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
          CROSS JOIN checked_privileges cp
         WHERE n.nspname = 'public'
           AND c.relkind = ANY (ARRAY['r','p','v','m','f']::"char"[])
           AND pg_catalog.has_table_privilege(
                   'flooow_v042_capability_owner', c.oid, cp.privilege
               ) IS DISTINCT FROM EXISTS (
                   SELECT 1 FROM allowed a
                    WHERE a.relid = c.oid AND a.privilege = cp.privilege
               )
    ) THEN
        RAISE EXCEPTION 'Final V042 owner relation privilege matrix is not exact';
    END IF;

    IF EXISTS (
        SELECT 1
          FROM (VALUES
            ('public.s2a_v041_evidence_fingerprint(uuid,uuid,uuid,uuid,text,text)'),
            ('public.s2a_v041_manifest_bytes(integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text)'),
            ('public.s2a_v041_frame(bytea)'),
            ('public.s2a_v041_text(text)'),
            ('public.s2a_v041_instant(timestamptz)'),
            ('public.s2a_v041_local(timestamp)'),
            ('public.s2a_v041_nullable_text(text)'),
            ('public.s2a_v042_authority_intent(text,uuid,uuid,uuid,uuid,uuid,uuid,bytea,uuid,text,text,uuid,uuid,text,text)'),
            ('public.s2a_v042_authority_receipt(text,text,uuid,uuid,integer,uuid,integer,text,text)'),
            ('public.s2a_v042_frame(bytea)'),
            ('public.s2a_v042_text(text)'),
            ('public.s2a_v042_revalidate_snapshot(uuid,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text,integer,integer,bytea,text,bytea,text,uuid,uuid,integer,text,text,bytea,bytea,uuid,integer,text,timestamptz,text,text)'),
            ('public.command_authorization_organization_lock(uuid)'),
            ('public.transaction_identity_progress_lock(uuid,uuid)'),
            ('public.transaction_identity_locks(uuid,uuid,uuid,uuid,text,uuid)'),
            ('public.transaction_identity_withdrawal_locks(uuid,uuid,uuid,uuid,text,uuid)'),
            ('public.transaction_identity_hash(text[])'),
            ('public.transaction_identity_grant_fingerprint(uuid,uuid)'),
            ('public.transaction_identity_intent(public.marketplace_transaction_identity_decision)'),
            ('public.transaction_identity_fingerprint(public.marketplace_transaction_identity_decision)')
          ) AS helper(identity)
         WHERE NOT pg_catalog.has_function_privilege(
             'flooow_v042_capability_owner', helper.identity, 'EXECUTE'
         )
    ) THEN
        RAISE EXCEPTION 'Final V042 owner helper EXECUTE closure is incomplete';
    END IF;

    IF EXISTS (
        SELECT 1
          FROM pg_catalog.pg_class c
          JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
         WHERE n.nspname = 'public'
           AND c.relkind = 'S'
           AND (
               pg_catalog.has_sequence_privilege('flooow_v042_capability_owner', c.oid, 'USAGE')
               OR pg_catalog.has_sequence_privilege('flooow_v042_capability_owner', c.oid, 'SELECT')
               OR pg_catalog.has_sequence_privilege('flooow_v042_capability_owner', c.oid, 'UPDATE')
           )
    ) THEN
        RAISE EXCEPTION 'Final V042 owner has forbidden sequence privilege';
    END IF;

    IF EXISTS (
        SELECT 1
          FROM (VALUES
            ('public.s2a_v042_begin_attested_principal_verification(uuid,uuid,uuid,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text)', true),
            ('public.s2a_v042_begin_attested_initial_credential_verification(uuid,uuid,uuid,uuid,uuid,bytea,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text)', true),
            ('public.s2a_v042_begin_attested_grant_verification(uuid,uuid,uuid,uuid,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text)', true),
            ('public.s2a_v042_apply_attested_principal(uuid,uuid,uuid,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text,integer,integer,bytea,text,bytea,text,uuid,uuid,integer,text,text,bytea,bytea,uuid,integer,text,timestamptz,text,text)', true),
            ('public.s2a_v042_apply_attested_initial_credential(uuid,uuid,uuid,uuid,uuid,bytea,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text,integer,integer,bytea,text,bytea,text,uuid,uuid,integer,text,text,bytea,bytea,uuid,integer,text,timestamptz,text,text)', true),
            ('public.s2a_v042_apply_attested_grant(uuid,uuid,uuid,uuid,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text,integer,integer,bytea,text,bytea,text,uuid,uuid,integer,text,text,bytea,bytea,uuid,integer,text,timestamptz,text,text)', true),
            ('public.s2a_v042_apply_legacy_unlinked_decision(uuid,uuid,uuid,text,uuid,text,text,integer,uuid,uuid,text,bigint,integer,text,character,text,bigint,integer,character,timestamp,uuid,uuid,integer,uuid,integer,text,text,character,character,character,text,uuid)', false),
            ('public.s2a_v042_begin_attested_decision_verification(uuid,uuid,uuid,integer,uuid,uuid,text,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text)', false),
            ('public.s2a_v042_apply_attested_decision(uuid,uuid,uuid,text,uuid,text,text,integer,uuid,uuid,text,bigint,integer,text,character,text,bigint,integer,character,timestamp,uuid,uuid,integer,uuid,integer,text,text,character,character,character,text,uuid,integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text,integer,integer,bytea,text,bytea,text,uuid,uuid,integer,text,text,bytea,bytea,uuid,integer,text,timestamptz,text,text)', false)
          ) AS capability(identity, issuer_family)
         WHERE pg_catalog.has_function_privilege('public', capability.identity, 'EXECUTE')
            OR pg_catalog.has_function_privilege('flooow_command_issuer', capability.identity, 'EXECUTE') IS DISTINCT FROM capability.issuer_family
            OR pg_catalog.has_function_privilege('flooow_command_runtime', capability.identity, 'EXECUTE') IS DISTINCT FROM (NOT capability.issuer_family)
            OR pg_catalog.has_function_privilege('flooow_attestation_verifier', capability.identity, 'EXECUTE')
            OR pg_catalog.has_function_privilege('flooow_approval_governance', capability.identity, 'EXECUTE')
    ) THEN
        RAISE EXCEPTION 'Final V042 caller EXECUTE matrix is not exact';
    END IF;

    IF EXISTS (
        SELECT 1
          FROM (VALUES
            ('public.command_principal'::pg_catalog.regclass),
            ('public.command_credential_revision'::pg_catalog.regclass),
            ('public.command_permission_grant'::pg_catalog.regclass),
            ('public.command_authority_operation'::pg_catalog.regclass)
          ) AS protected_relation(relid)
         WHERE NOT pg_catalog.has_table_privilege('flooow_command_issuer', relid, 'SELECT')
            OR pg_catalog.has_table_privilege('flooow_command_issuer', relid, 'INSERT')
            OR pg_catalog.has_table_privilege('flooow_command_issuer', relid, 'UPDATE')
            OR pg_catalog.has_table_privilege('flooow_command_issuer', relid, 'DELETE')
    ) THEN
        RAISE EXCEPTION 'Final V042 issuer direct authority DML posture is not exact';
    END IF;

    IF NOT pg_catalog.has_table_privilege('flooow_command_issuer', 'public.integration_organization', 'SELECT')
       OR NOT pg_catalog.has_table_privilege('flooow_command_issuer', 'public.integration_connection', 'SELECT') THEN
        RAISE EXCEPTION 'Final V042 issuer required reads were not preserved';
    END IF;

    IF pg_catalog.has_table_privilege(
           'flooow_command_runtime',
           'public.marketplace_transaction_identity_decision',
           'INSERT'
       ) THEN
        RAISE EXCEPTION 'Final V042 runtime direct decision INSERT remains available';
    END IF;

    IF NOT pg_catalog.has_table_privilege('flooow_command_runtime', 'public.command_principal', 'SELECT')
       OR NOT pg_catalog.has_table_privilege('flooow_command_runtime', 'public.command_principal', 'UPDATE')
       OR EXISTS (
           SELECT 1
             FROM (VALUES
               ('public.command_credential_revision'::pg_catalog.regclass),
               ('public.command_permission_grant'::pg_catalog.regclass),
               ('public.integration_organization'::pg_catalog.regclass),
               ('public.integration_connection'::pg_catalog.regclass),
               ('public.marketplace_transaction_identity_decision'::pg_catalog.regclass),
               ('public.marketplace_transaction_identity_head'::pg_catalog.regclass),
               ('public.marketplace_order_identity_registry'::pg_catalog.regclass),
               ('public.marketplace_order_occurrence_source_promotion'::pg_catalog.regclass),
               ('public.integration_mercado_livre_order_source_observation'::pg_catalog.regclass),
               ('public.integration_omie_transaction_evidence'::pg_catalog.regclass),
               ('public.integration_omie_transaction_evidence_v3'::pg_catalog.regclass),
               ('public.integration_connector_page_commit'::pg_catalog.regclass),
               ('public.integration_connector_progress'::pg_catalog.regclass)
             ) AS runtime_read(relid)
            WHERE NOT pg_catalog.has_table_privilege('flooow_command_runtime', relid, 'SELECT')
       ) THEN
        RAISE EXCEPTION 'Final V042 runtime required reads were not preserved';
    END IF;
END;
$v042_final_assertions$;

COMMIT;
