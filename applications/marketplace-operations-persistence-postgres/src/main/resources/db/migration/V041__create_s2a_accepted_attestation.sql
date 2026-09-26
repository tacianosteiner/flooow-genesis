DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname='flooow_attestation_verifier') THEN
        CREATE ROLE flooow_attestation_verifier NOLOGIN NOINHERIT;
    END IF;
    IF EXISTS (
        SELECT 1 FROM pg_catalog.pg_auth_members m
        JOIN pg_catalog.pg_roles r ON r.oid=m.roleid
        JOIN pg_catalog.pg_roles u ON u.oid=m.member
        WHERE r.rolname::text='flooow_attestation_verifier' OR u.rolname::text='flooow_attestation_verifier'
           OR (r.rolname::text=ANY(ARRAY['flooow_attestation_verifier','flooow_approval_governance','flooow_command_issuer','flooow_command_runtime']::text[])
           AND u.rolname::text=ANY(ARRAY['flooow_attestation_verifier','flooow_approval_governance','flooow_command_issuer','flooow_command_runtime']::text[]))
    ) THEN RAISE EXCEPTION 'Protected S2A role graph is contaminated'; END IF;
    ALTER ROLE flooow_attestation_verifier NOLOGIN NOINHERIT;
END $$;

CREATE FUNCTION public.s2a_persist_attestation_verification_result(
 p_schema_version integer,p_manifest_id uuid,p_organization_id uuid,p_mercado_livre_connection_id uuid,
 p_omie_connection_id uuid,p_source_order_reference text,p_integration_reference text,p_marketplace_order_id uuid,
 p_permission text,p_accountable_operator uuid,p_approval_source uuid,p_approval_window_start timestamptz,
 p_approval_window_end timestamptz,p_revocation_owner uuid,p_credential_custodian uuid,p_credential_delivery_method text,
 p_credential_rotation_owner uuid,p_immediate_revocation_policy text,p_reason text,p_provenance text,p_correlation_id uuid,
 p_evidence_binding_fingerprint text,p_canonicalization_version integer,p_canonical_manifest_bytes bytea,
 p_manifest_digest text,p_algorithm_id text,p_signer_key_id uuid,p_signer_key_fingerprint text,p_signature_bytes bytea,
 p_expected_canonical_signature_preimage_bytes bytea,p_expected_signer_subject_id uuid,
 p_expected_signer_key_revision integer,p_expected_signer_key_lineage_fingerprint text,
 p_expected_subject_public_key_info_der bytea,p_expected_signer_authority_id uuid,
 p_expected_signer_authority_revision integer,p_expected_signer_authority_fingerprint text,
 p_expected_accepted_proof_fingerprint text)
RETURNS TABLE(outcome text,result_organization_id uuid,result_manifest_id uuid,result_manifest_digest text,
 result_accepted_proof_fingerprint text,result_verified_at timestamptz,result_recorded_at timestamptz)
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$
DECLARE snapshot record; collision record;
BEGIN
 SELECT * INTO STRICT snapshot FROM public.s2a_begin_attestation_verification(
 p_schema_version,p_manifest_id,p_organization_id,p_mercado_livre_connection_id,p_omie_connection_id,
 p_source_order_reference,p_integration_reference,p_marketplace_order_id,p_permission,p_accountable_operator,
 p_approval_source,p_approval_window_start,p_approval_window_end,p_revocation_owner,p_credential_custodian,
 p_credential_delivery_method,p_credential_rotation_owner,p_immediate_revocation_policy,p_reason,p_provenance,
 p_correlation_id,p_evidence_binding_fingerprint,p_canonicalization_version,p_canonical_manifest_bytes,p_manifest_digest,
 p_algorithm_id,p_signer_key_id,p_signer_key_fingerprint,p_signature_bytes);
 IF snapshot.result_canonical_signature_preimage_bytes IS DISTINCT FROM p_expected_canonical_signature_preimage_bytes
 OR snapshot.result_signer_subject_id IS DISTINCT FROM p_expected_signer_subject_id
 OR snapshot.result_signer_key_revision IS DISTINCT FROM p_expected_signer_key_revision
 OR snapshot.result_signer_key_lineage_fingerprint IS DISTINCT FROM p_expected_signer_key_lineage_fingerprint
 OR snapshot.result_subject_public_key_info_der IS DISTINCT FROM p_expected_subject_public_key_info_der
 OR snapshot.result_signer_authority_id IS DISTINCT FROM p_expected_signer_authority_id
 OR snapshot.result_signer_authority_revision IS DISTINCT FROM p_expected_signer_authority_revision
 OR snapshot.result_signer_authority_fingerprint IS DISTINCT FROM p_expected_signer_authority_fingerprint
 OR snapshot.result_accepted_proof_fingerprint IS DISTINCT FROM p_expected_accepted_proof_fingerprint THEN
   RAISE EXCEPTION 'Verifier snapshot mismatch' USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE'; END IF;
 IF snapshot.outcome='VERIFY_NEW' THEN
   BEGIN
     INSERT INTO public.s2a_accepted_attestation VALUES(
      p_organization_id,p_manifest_id,1,p_schema_version,p_canonicalization_version,
      snapshot.result_canonical_manifest_bytes,snapshot.result_manifest_digest,
      snapshot.result_canonical_signature_preimage_bytes,p_algorithm_id,p_signer_key_id,
      snapshot.result_signer_key_revision,p_signer_key_fingerprint,snapshot.result_signer_key_lineage_fingerprint,
      snapshot.result_subject_public_key_info_der,p_signature_bytes,snapshot.result_signer_authority_id,
      snapshot.result_signer_authority_revision,snapshot.result_signer_authority_fingerprint,
      snapshot.result_verified_at,snapshot.result_accepted_proof_fingerprint,snapshot.result_recorded_at);
     outcome:='ACCEPTED';
   EXCEPTION
     WHEN unique_violation THEN
       SELECT a.* INTO collision
       FROM public.s2a_accepted_attestation a
       WHERE a.organization_id=p_organization_id
         AND a.manifest_id=p_manifest_id;

       IF NOT FOUND THEN
         RAISE;
       END IF;

       IF collision.artifact_version IS DISTINCT FROM 1
       OR collision.schema_version IS DISTINCT FROM p_schema_version
       OR collision.canonicalization_version IS DISTINCT FROM p_canonicalization_version
       OR collision.canonical_manifest_bytes IS DISTINCT FROM snapshot.result_canonical_manifest_bytes
       OR collision.manifest_digest::text IS DISTINCT FROM snapshot.result_manifest_digest
       OR collision.canonical_signature_preimage_bytes IS DISTINCT FROM snapshot.result_canonical_signature_preimage_bytes
       OR collision.algorithm_id IS DISTINCT FROM p_algorithm_id
       OR collision.signer_key_id IS DISTINCT FROM p_signer_key_id
       OR collision.signer_key_revision IS DISTINCT FROM snapshot.result_signer_key_revision
       OR collision.signer_key_fingerprint::text IS DISTINCT FROM p_signer_key_fingerprint
       OR collision.signer_key_lineage_fingerprint::text IS DISTINCT FROM snapshot.result_signer_key_lineage_fingerprint
       OR collision.subject_public_key_info_der IS DISTINCT FROM snapshot.result_subject_public_key_info_der
       OR collision.signature_bytes IS DISTINCT FROM p_signature_bytes
       OR collision.signer_authority_id IS DISTINCT FROM snapshot.result_signer_authority_id
       OR collision.signer_authority_revision IS DISTINCT FROM snapshot.result_signer_authority_revision
       OR collision.signer_authority_fingerprint::text IS DISTINCT FROM snapshot.result_signer_authority_fingerprint
       OR collision.verified_at IS DISTINCT FROM snapshot.result_verified_at
       OR collision.accepted_proof_fingerprint::text IS DISTINCT FROM snapshot.result_accepted_proof_fingerprint
       OR collision.recorded_at IS DISTINCT FROM snapshot.result_recorded_at THEN
         RAISE EXCEPTION 'Conflicting concurrent replay'
           USING ERRCODE='P0016';
       END IF;

       outcome:='ALREADY_ACCEPTED';
   END;
 ELSE
   outcome:='ALREADY_ACCEPTED';
 END IF;
 result_organization_id:=p_organization_id; result_manifest_id:=p_manifest_id;
 result_manifest_digest:=snapshot.result_manifest_digest;
 result_accepted_proof_fingerprint:=snapshot.result_accepted_proof_fingerprint;
 result_verified_at:=snapshot.result_verified_at; result_recorded_at:=snapshot.result_recorded_at;
 RETURN NEXT;
END $$;

CREATE FUNCTION public.s2a_begin_attestation_verification(
 p_schema_version integer,p_manifest_id uuid,p_organization_id uuid,p_mercado_livre_connection_id uuid,
 p_omie_connection_id uuid,p_source_order_reference text,p_integration_reference text,p_marketplace_order_id uuid,
 p_permission text,p_accountable_operator uuid,p_approval_source uuid,p_approval_window_start timestamptz,
 p_approval_window_end timestamptz,p_revocation_owner uuid,p_credential_custodian uuid,p_credential_delivery_method text,
 p_credential_rotation_owner uuid,p_immediate_revocation_policy text,p_reason text,p_provenance text,p_correlation_id uuid,
 p_evidence_binding_fingerprint text,p_canonicalization_version integer,p_canonical_manifest_bytes bytea,
 p_manifest_digest text,p_algorithm_id text,p_signer_key_id uuid,p_signer_key_fingerprint text,p_signature_bytes bytea)
RETURNS TABLE(outcome text,result_verified_at timestamptz,result_recorded_at timestamptz,
 result_canonical_manifest_bytes bytea,result_manifest_digest text,result_canonical_signature_preimage_bytes bytea,
 result_signer_subject_id uuid,result_signer_key_id uuid,result_signer_key_revision integer,
 result_signer_key_fingerprint text,result_signer_key_lineage_fingerprint text,result_subject_public_key_info_der bytea,
 result_signer_authority_id uuid,result_signer_authority_revision integer,result_signer_authority_fingerprint text,
 result_accepted_proof_fingerprint text)
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$
DECLARE org_status text; existing record; replay boolean:=false;
 keyrow public.s2a_signer_key_revision%ROWTYPE; auth public.s2a_signer_authority_revision%ROWTYPE;
 computed_manifest bytea; computed_digest text; computed_preimage bytea; evidence text;
 leaf_count integer; authority_leaf_count integer; lock_signer_subject_id uuid;
BEGIN
 SELECT o.status INTO org_status FROM public.integration_organization o WHERE o.organization_id=p_organization_id FOR SHARE;
 IF NOT FOUND THEN RAISE EXCEPTION 'Governance unavailable' USING ERRCODE='P0015'; END IF;
 PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended('s2a-attestation/manifest/1:'||p_organization_id||':'||p_manifest_id,0));
 SELECT a.* INTO existing FROM public.s2a_accepted_attestation a WHERE a.organization_id=p_organization_id AND a.manifest_id=p_manifest_id;
 replay:=FOUND;
 IF replay THEN
   result_verified_at:=existing.verified_at; result_recorded_at:=existing.recorded_at;

   IF existing.recorded_at<>existing.verified_at THEN
     RAISE EXCEPTION 'Stored timestamp corruption'
       USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE';
   END IF;

   -- Replay identity is classified immediately under the manifest lock,
   -- before any caller-selected governance resource can be locked.
   IF existing.schema_version IS DISTINCT FROM p_schema_version
   OR existing.canonicalization_version IS DISTINCT FROM p_canonicalization_version
   OR existing.canonical_manifest_bytes IS DISTINCT FROM p_canonical_manifest_bytes
   OR existing.manifest_digest::text IS DISTINCT FROM p_manifest_digest
   OR existing.algorithm_id IS DISTINCT FROM p_algorithm_id
   OR existing.signer_key_id IS DISTINCT FROM p_signer_key_id
   OR existing.signer_key_fingerprint::text IS DISTINCT FROM p_signer_key_fingerprint
   OR existing.signature_bytes IS DISTINCT FROM p_signature_bytes THEN
     RAISE EXCEPTION 'Conflicting replay'
       USING ERRCODE='P0016';
   END IF;
 ELSE
   IF org_status<>'ACTIVE' THEN RAISE EXCEPTION 'Organization inactive' USING ERRCODE='P0017',DETAIL='EXPIRED_OR_NOT_YET_VALID'; END IF;
   result_verified_at:=transaction_timestamp()::timestamptz(6); result_recorded_at:=result_verified_at;
 END IF;
 IF pg_catalog.num_nonnulls(p_schema_version,p_manifest_id,p_organization_id,p_mercado_livre_connection_id,
 p_omie_connection_id,p_source_order_reference,p_integration_reference,p_marketplace_order_id,p_permission,
 p_accountable_operator,p_approval_source,p_approval_window_start,p_approval_window_end,p_revocation_owner,
 p_credential_custodian,p_credential_delivery_method,p_credential_rotation_owner,p_immediate_revocation_policy,
 p_reason,p_provenance,p_correlation_id,p_evidence_binding_fingerprint,p_canonicalization_version,
 p_canonical_manifest_bytes,p_manifest_digest,p_algorithm_id,p_signer_key_id,p_signer_key_fingerprint,p_signature_bytes)<>29
 OR p_schema_version<>1 OR p_canonicalization_version<>1 OR p_algorithm_id<>'Ed25519' OR p_permission<>'TRANSACTION_IDENTITY_DECISION_WRITE'
 OR p_credential_delivery_method<>'PROTECTED_TTY_ONE_TIME' OR p_immediate_revocation_policy<>'SEPARATE_APPROVAL_REQUIRED'
 OR p_manifest_digest!~'^[0-9a-f]{64}$' OR p_evidence_binding_fingerprint!~'^[0-9a-f]{64}$'
 OR p_signer_key_fingerprint!~'^[0-9a-f]{64}$' OR octet_length(p_signature_bytes)<>64
 OR p_manifest_id='00000000-0000-0000-0000-000000000000'::uuid
 OR p_organization_id='00000000-0000-0000-0000-000000000000'::uuid
 OR p_mercado_livre_connection_id='00000000-0000-0000-0000-000000000000'::uuid
 OR p_omie_connection_id='00000000-0000-0000-0000-000000000000'::uuid
 OR p_marketplace_order_id='00000000-0000-0000-0000-000000000000'::uuid
 OR p_accountable_operator='00000000-0000-0000-0000-000000000000'::uuid
 OR p_approval_source='00000000-0000-0000-0000-000000000000'::uuid
 OR p_revocation_owner='00000000-0000-0000-0000-000000000000'::uuid
 OR p_credential_custodian='00000000-0000-0000-0000-000000000000'::uuid
 OR p_credential_rotation_owner='00000000-0000-0000-0000-000000000000'::uuid
 OR p_correlation_id='00000000-0000-0000-0000-000000000000'::uuid
 OR p_signer_key_id='00000000-0000-0000-0000-000000000000'::uuid
 OR octet_length(p_source_order_reference) NOT BETWEEN 1 AND 256
 OR octet_length(p_integration_reference) NOT BETWEEN 1 AND 60
 OR octet_length(p_reason) NOT BETWEEN 1 AND 512 OR octet_length(p_provenance) NOT BETWEEN 1 AND 1024
 OR p_source_order_reference IS NOT NFC NORMALIZED OR p_integration_reference IS NOT NFC NORMALIZED
 OR p_reason IS NOT NFC NORMALIZED OR p_provenance IS NOT NFC NORMALIZED
 OR p_source_order_reference<>btrim(p_source_order_reference) OR p_integration_reference<>btrim(p_integration_reference)
 OR p_reason<>btrim(p_reason) OR p_provenance<>btrim(p_provenance)
 OR p_source_order_reference~'^[[:space:]]|[[:space:]]$'
 OR p_integration_reference~'^[[:space:]]|[[:space:]]$'
 OR p_reason~'^[[:space:]]|[[:space:]]$'
 OR p_provenance~'^[[:space:]]|[[:space:]]$'
 OR p_source_order_reference~'[[:cntrl:]]' OR p_integration_reference~'[[:cntrl:]]'
 OR p_reason~'[[:cntrl:]]' OR p_provenance~'[[:cntrl:]]'
 OR octet_length(p_canonical_manifest_bytes) NOT BETWEEN 1 AND 4096
 OR p_approval_window_start>=p_approval_window_end THEN
   RAISE EXCEPTION 'Unsupported canonical form' USING ERRCODE='P0018',DETAIL='UNSUPPORTED_CANONICAL_FORM'; END IF;
 IF result_verified_at<p_approval_window_start OR result_verified_at>=p_approval_window_end THEN
   RAISE EXCEPTION 'Approval window denied' USING ERRCODE='P0017',DETAIL='EXPIRED_OR_NOT_YET_VALID'; END IF;
 computed_manifest:=public.s2a_v041_manifest_bytes(p_schema_version,p_manifest_id,p_organization_id,p_mercado_livre_connection_id,
 p_omie_connection_id,p_source_order_reference,p_integration_reference,p_marketplace_order_id,p_permission,p_accountable_operator,
 p_approval_source,p_approval_window_start,p_approval_window_end,p_revocation_owner,p_credential_custodian,p_credential_delivery_method,
 p_credential_rotation_owner,p_immediate_revocation_policy,p_reason,p_provenance,p_correlation_id,p_evidence_binding_fingerprint);
 computed_digest:=encode(sha256(computed_manifest),'hex');
 IF computed_manifest<>p_canonical_manifest_bytes OR computed_digest<>p_manifest_digest THEN
   RAISE EXCEPTION 'Canonical integrity failure' USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE'; END IF;
 PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended('s2a-governance/signer-key/1:'||p_organization_id||':'||p_signer_key_id,0));
 SELECT min(k.signer_subject_id::text)::uuid INTO lock_signer_subject_id
 FROM public.s2a_signer_key_revision k
 WHERE k.organization_id=p_organization_id AND k.signer_key_id=p_signer_key_id;
 IF lock_signer_subject_id IS NULL THEN
   RAISE EXCEPTION 'No effective key' USING ERRCODE='P0017',DETAIL='EXPIRED_OR_NOT_YET_VALID'; END IF;
 PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended('s2a-governance/signer-authority-scope/1:'||p_organization_id||':'||lock_signer_subject_id||':'||p_signer_key_id||':S2A_FIELD_PROOF_APPROVAL:TRANSACTION_IDENTITY_DECISION_WRITE',0));
 IF EXISTS(SELECT 1 FROM public.s2a_signer_key_revision k LEFT JOIN public.s2a_signer_key_revision prev
 ON prev.organization_id=k.organization_id AND prev.signer_key_id=k.signer_key_id AND prev.revision=k.supersedes_revision
 WHERE k.organization_id=p_organization_id AND k.signer_key_id=p_signer_key_id AND
 (k.revision<1 OR (k.revision=1 AND k.supersedes_revision IS NOT NULL) OR (k.revision>1 AND k.supersedes_revision<>k.revision-1)
  OR (k.revision>1 AND prev.revision IS NULL) OR (prev.effective_at IS NOT NULL AND k.effective_at<=prev.effective_at)
  OR k.algorithm_id<>'Ed25519' OR octet_length(k.subject_public_key_info_der)<>44
  OR substring(k.subject_public_key_info_der FROM 1 FOR 12)<>decode('302a300506032b6570032100','hex')
  OR k.signer_key_fingerprint<>encode(sha256(k.subject_public_key_info_der),'hex')
  OR (k.revision>1 AND (k.signer_subject_id<>prev.signer_subject_id OR k.algorithm_id<>prev.algorithm_id
  OR k.subject_public_key_info_der<>prev.subject_public_key_info_der OR k.signer_key_fingerprint<>prev.signer_key_fingerprint
  OR k.valid_from<>prev.valid_from OR (prev.state<>'ACTIVE' AND k.state='ACTIVE')))
  OR k.lineage_fingerprint<>public.s2a_signer_key_lineage_fingerprint(k.organization_id,k.signer_key_id,k.revision,k.signer_subject_id,
 k.algorithm_id,k.subject_public_key_info_der,k.signer_key_fingerprint,k.state,k.valid_from,k.effective_at,k.supersedes_revision,prev.lineage_fingerprint)))
 THEN RAISE EXCEPTION 'Key lineage conflict' USING ERRCODE='P0016'; END IF;
 SELECT count(*) INTO leaf_count FROM public.s2a_signer_key_revision k WHERE k.organization_id=p_organization_id AND k.signer_key_id=p_signer_key_id
 AND NOT EXISTS(SELECT 1 FROM public.s2a_signer_key_revision n WHERE n.organization_id=k.organization_id AND n.signer_key_id=k.signer_key_id AND n.supersedes_revision=k.revision);
 IF leaf_count<>1 THEN RAISE EXCEPTION 'Key lineage conflict' USING ERRCODE='P0016'; END IF;
 IF replay THEN
   SELECT k.* INTO keyrow FROM public.s2a_signer_key_revision k WHERE k.organization_id=p_organization_id
   AND k.signer_key_id=existing.signer_key_id AND k.revision=existing.signer_key_revision;
 ELSE
   SELECT k.* INTO keyrow FROM public.s2a_signer_key_revision k WHERE k.organization_id=p_organization_id AND k.signer_key_id=p_signer_key_id
   AND k.effective_at<=result_verified_at ORDER BY k.effective_at DESC,k.revision DESC LIMIT 1;
 END IF;
 IF NOT FOUND THEN RAISE EXCEPTION 'No effective key' USING ERRCODE='P0017',DETAIL='EXPIRED_OR_NOT_YET_VALID'; END IF;
 IF keyrow.valid_from>result_verified_at OR keyrow.state<>'ACTIVE' THEN
   RAISE EXCEPTION 'Effective key unavailable' USING ERRCODE='P0017',DETAIL='EXPIRED_OR_NOT_YET_VALID'; END IF;
 IF keyrow.signer_key_fingerprint<>p_signer_key_fingerprint OR keyrow.algorithm_id<>p_algorithm_id THEN
   RAISE EXCEPTION 'Key scope mismatch' USING ERRCODE='P0017',DETAIL='SCOPE_MISMATCH'; END IF;
 IF keyrow.signer_subject_id<>lock_signer_subject_id THEN
   RAISE EXCEPTION 'Key lineage conflict' USING ERRCODE='P0016'; END IF;
 IF EXISTS(
   SELECT 1 FROM public.s2a_signer_authority_revision a
   LEFT JOIN public.s2a_signer_authority_revision prev
     ON prev.organization_id=a.organization_id AND prev.signer_authority_id=a.supersedes_signer_authority_id
   WHERE a.organization_id=p_organization_id AND a.signer_subject_id=keyrow.signer_subject_id
   AND a.signer_key_id=p_signer_key_id AND a.approval_action='S2A_FIELD_PROOF_APPROVAL'
   AND a.permission='TRANSACTION_IDENTITY_DECISION_WRITE' AND (
     a.revision<1 OR (a.revision=1 AND a.supersedes_signer_authority_id IS NOT NULL)
     OR (a.revision>1 AND (prev.signer_authority_id IS NULL OR prev.revision<>a.revision-1))
     OR (a.revision>1 AND (a.signer_subject_id<>prev.signer_subject_id
       OR a.signer_authorizing_institution_id<>prev.signer_authorizing_institution_id
       OR a.signer_role<>prev.signer_role OR a.signer_key_id<>prev.signer_key_id
       OR a.signer_key_revision<>prev.signer_key_revision OR a.signer_key_fingerprint<>prev.signer_key_fingerprint
       OR a.approval_action<>prev.approval_action OR a.permission<>prev.permission
       OR a.valid_from<>prev.valid_from OR a.valid_until<>prev.valid_until
       OR a.approval_source_id<>prev.approval_source_id))
     OR a.signer_authority_fingerprint<>public.s2a_signer_authority_fingerprint(
       a.organization_id,a.signer_authority_id,a.revision,a.signer_subject_id,
       a.signer_authorizing_institution_id,a.signer_role,a.signer_key_id,a.signer_key_revision,
       a.signer_key_fingerprint,a.approval_action,a.permission,a.valid_from,a.valid_until,a.state,
       a.approval_source_id,a.supersedes_signer_authority_id,prev.signer_authority_fingerprint)
   )) THEN RAISE EXCEPTION 'Authority lineage conflict' USING ERRCODE='P0016'; END IF;
 SELECT count(*) INTO authority_leaf_count FROM public.s2a_signer_authority_revision a
 WHERE a.organization_id=p_organization_id AND a.signer_subject_id=keyrow.signer_subject_id
 AND a.signer_key_id=p_signer_key_id AND a.approval_action='S2A_FIELD_PROOF_APPROVAL'
 AND a.permission='TRANSACTION_IDENTITY_DECISION_WRITE'
 AND NOT EXISTS(SELECT 1 FROM public.s2a_signer_authority_revision n
   WHERE n.organization_id=a.organization_id AND n.supersedes_signer_authority_id=a.signer_authority_id);
 IF authority_leaf_count=0 THEN RAISE EXCEPTION 'Authority unavailable' USING ERRCODE='P0015'; END IF;
 IF authority_leaf_count>1 THEN RAISE EXCEPTION 'Authority ambiguous' USING ERRCODE='P0016'; END IF;
 IF replay THEN
   SELECT a.* INTO auth FROM public.s2a_signer_authority_revision a WHERE a.organization_id=p_organization_id AND a.signer_authority_id=existing.signer_authority_id;
 ELSE
   SELECT a.* INTO auth FROM public.s2a_signer_authority_revision a WHERE a.organization_id=p_organization_id
   AND a.signer_subject_id=keyrow.signer_subject_id AND a.signer_key_id=p_signer_key_id
   AND a.approval_action='S2A_FIELD_PROOF_APPROVAL' AND a.permission='TRANSACTION_IDENTITY_DECISION_WRITE'
   AND NOT EXISTS(SELECT 1 FROM public.s2a_signer_authority_revision n WHERE n.organization_id=a.organization_id
   AND n.supersedes_signer_authority_id=a.signer_authority_id);
 END IF;
 IF NOT FOUND THEN RAISE EXCEPTION 'Authority unavailable' USING ERRCODE='P0015'; END IF;
 IF auth.signer_key_revision<>keyrow.revision OR auth.signer_key_fingerprint<>keyrow.signer_key_fingerprint THEN
   RAISE EXCEPTION 'Authority key mismatch' USING ERRCODE='P0017',DETAIL='SCOPE_MISMATCH'; END IF;
 IF auth.signer_subject_id<>keyrow.signer_subject_id OR auth.approval_source_id<>p_approval_source OR auth.signer_role<>'S2A_FIELD_PROOF_APPROVER'
 OR auth.approval_action<>'S2A_FIELD_PROOF_APPROVAL' OR auth.permission<>p_permission THEN
   RAISE EXCEPTION 'Authority scope mismatch' USING ERRCODE='P0017',DETAIL='SCOPE_MISMATCH'; END IF;
 IF NOT replay AND (auth.state<>'ENABLED' OR auth.valid_from>result_verified_at OR result_verified_at>=auth.valid_until) THEN
   RAISE EXCEPTION 'Authority expired' USING ERRCODE='P0017',DETAIL='EXPIRED_OR_NOT_YET_VALID'; END IF;
 evidence:=public.s2a_v041_evidence_fingerprint(p_organization_id,p_marketplace_order_id,p_mercado_livre_connection_id,
 p_omie_connection_id,p_source_order_reference,p_integration_reference);
 IF evidence<>p_evidence_binding_fingerprint THEN RAISE EXCEPTION 'Evidence scope mismatch' USING ERRCODE='P0017',DETAIL='SCOPE_MISMATCH'; END IF;
 computed_preimage:=public.s2a_v041_signature_preimage(p_algorithm_id,p_signer_key_id,p_signer_key_fingerprint,p_manifest_digest);
 result_accepted_proof_fingerprint:=public.s2a_v041_proof_fingerprint(computed_manifest,computed_digest,computed_preimage,p_algorithm_id,
 p_signer_key_id,keyrow.revision,keyrow.signer_key_fingerprint,keyrow.lineage_fingerprint,keyrow.subject_public_key_info_der,
 p_signature_bytes,auth.signer_authority_id,auth.revision,auth.signer_authority_fingerprint,result_verified_at);
 IF replay AND (existing.canonical_manifest_bytes<>computed_manifest OR existing.manifest_digest<>computed_digest
 OR existing.canonical_signature_preimage_bytes<>computed_preimage OR existing.algorithm_id<>p_algorithm_id
 OR existing.signer_key_id<>p_signer_key_id OR existing.signer_key_revision<>keyrow.revision
 OR existing.signer_key_fingerprint<>keyrow.signer_key_fingerprint OR existing.signer_key_lineage_fingerprint<>keyrow.lineage_fingerprint
 OR existing.subject_public_key_info_der<>keyrow.subject_public_key_info_der OR existing.signature_bytes<>p_signature_bytes
 OR existing.signer_authority_id<>auth.signer_authority_id OR existing.signer_authority_revision<>auth.revision
 OR existing.signer_authority_fingerprint<>auth.signer_authority_fingerprint
 OR existing.accepted_proof_fingerprint<>result_accepted_proof_fingerprint) THEN
   RAISE EXCEPTION 'Conflicting replay' USING ERRCODE='P0016'; END IF;
 outcome:=CASE WHEN replay THEN 'VERIFY_REPLAY' ELSE 'VERIFY_NEW' END;
 result_canonical_manifest_bytes:=computed_manifest; result_manifest_digest:=computed_digest;
 result_canonical_signature_preimage_bytes:=computed_preimage; result_signer_subject_id:=keyrow.signer_subject_id;
 result_signer_key_id:=keyrow.signer_key_id; result_signer_key_revision:=keyrow.revision;
 result_signer_key_fingerprint:=keyrow.signer_key_fingerprint; result_signer_key_lineage_fingerprint:=keyrow.lineage_fingerprint;
 result_subject_public_key_info_der:=keyrow.subject_public_key_info_der; result_signer_authority_id:=auth.signer_authority_id;
 result_signer_authority_revision:=auth.revision; result_signer_authority_fingerprint:=auth.signer_authority_fingerprint;
 RETURN NEXT;
END $$;

CREATE TABLE public.s2a_accepted_attestation (
    organization_id uuid NOT NULL, manifest_id uuid NOT NULL, artifact_version integer NOT NULL,
    schema_version integer NOT NULL, canonicalization_version integer NOT NULL,
    canonical_manifest_bytes bytea NOT NULL, manifest_digest char(64) NOT NULL,
    canonical_signature_preimage_bytes bytea NOT NULL, algorithm_id text NOT NULL,
    signer_key_id uuid NOT NULL, signer_key_revision integer NOT NULL,
    signer_key_fingerprint char(64) NOT NULL, signer_key_lineage_fingerprint char(64) NOT NULL,
    subject_public_key_info_der bytea NOT NULL, signature_bytes bytea NOT NULL,
    signer_authority_id uuid NOT NULL, signer_authority_revision integer NOT NULL,
    signer_authority_fingerprint char(64) NOT NULL, verified_at timestamptz(6) NOT NULL,
    accepted_proof_fingerprint char(64) NOT NULL,
    recorded_at timestamptz(6) NOT NULL DEFAULT transaction_timestamp(),
    PRIMARY KEY (organization_id,manifest_id),
    FOREIGN KEY (organization_id) REFERENCES public.integration_organization(organization_id),
    FOREIGN KEY (organization_id,signer_key_id,signer_key_revision,signer_key_fingerprint)
      REFERENCES public.s2a_signer_key_revision(organization_id,signer_key_id,revision,signer_key_fingerprint),
    FOREIGN KEY (organization_id,signer_authority_id)
      REFERENCES public.s2a_signer_authority_revision(organization_id,signer_authority_id),
    CHECK (artifact_version=1), CHECK (schema_version=1), CHECK (canonicalization_version=1),
    CHECK (algorithm_id='Ed25519'), CHECK (organization_id<>'00000000-0000-0000-0000-000000000000'::uuid),
    CHECK (manifest_id<>'00000000-0000-0000-0000-000000000000'::uuid),
    CHECK (signer_key_id<>'00000000-0000-0000-0000-000000000000'::uuid),
    CHECK (signer_authority_id<>'00000000-0000-0000-0000-000000000000'::uuid),
    CHECK (signer_key_revision>0), CHECK (signer_authority_revision>0),
    CHECK (manifest_digest::text~'^[0-9a-f]{64}$'), CHECK (signer_key_fingerprint::text~'^[0-9a-f]{64}$'),
    CHECK (signer_key_lineage_fingerprint::text~'^[0-9a-f]{64}$'),
    CHECK (signer_authority_fingerprint::text~'^[0-9a-f]{64}$'),
    CHECK (accepted_proof_fingerprint::text~'^[0-9a-f]{64}$'),
    CHECK (octet_length(canonical_manifest_bytes) BETWEEN 1 AND 4096),
    CHECK (octet_length(canonical_signature_preimage_bytes)=222),
    CHECK (octet_length(subject_public_key_info_der)=44),
    CHECK (substring(subject_public_key_info_der FROM 1 FOR 12)=decode('302a300506032b6570032100','hex')),
    CHECK (octet_length(signature_bytes)=64),
    CHECK (manifest_digest::text=encode(sha256(canonical_manifest_bytes),'hex')),
    CHECK (recorded_at=verified_at)
);

CREATE FUNCTION public.s2a_reject_accepted_attestation_mutation() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$
BEGIN RAISE EXCEPTION 'Accepted attestations are immutable' USING ERRCODE='23514'; END $$;
CREATE TRIGGER s2a_accepted_attestation_immutable BEFORE UPDATE OR DELETE ON public.s2a_accepted_attestation
FOR EACH ROW EXECUTE FUNCTION public.s2a_reject_accepted_attestation_mutation();

CREATE FUNCTION public.s2a_v041_frame(v bytea) RETURNS bytea LANGUAGE sql IMMUTABLE STRICT
SET search_path=pg_catalog,pg_temp AS $$ SELECT int4send(octet_length(v))||v $$;
CREATE FUNCTION public.s2a_v041_text(v text) RETURNS bytea LANGUAGE sql IMMUTABLE STRICT
SET search_path=pg_catalog,pg_temp AS $$ SELECT public.s2a_v041_frame(convert_to(v,'UTF8')) $$;
CREATE FUNCTION public.s2a_v041_instant(v timestamptz) RETURNS bytea LANGUAGE sql IMMUTABLE STRICT
SET search_path=pg_catalog,pg_temp AS $$ SELECT public.s2a_v041_text(to_char(v AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US')||'Z') $$;
CREATE FUNCTION public.s2a_v041_local(v timestamp) RETURNS bytea LANGUAGE sql IMMUTABLE STRICT
SET search_path=pg_catalog,pg_temp AS $$ SELECT public.s2a_v041_text(to_char(v,'YYYY-MM-DD"T"HH24:MI:SS.US')) $$;
CREATE FUNCTION public.s2a_v041_nullable_text(v text) RETURNS bytea LANGUAGE sql IMMUTABLE
SET search_path=pg_catalog,pg_temp AS $$ SELECT CASE WHEN v IS NULL THEN public.s2a_v041_text('NULL')||public.s2a_v041_frame(''::bytea) ELSE public.s2a_v041_text('PRESENT')||public.s2a_v041_text(v) END $$;

CREATE FUNCTION public.s2a_v041_manifest_bytes(
 p_schema_version integer,p_manifest_id uuid,p_organization_id uuid,p_mercado_livre_connection_id uuid,
 p_omie_connection_id uuid,p_source_order_reference text,p_integration_reference text,p_marketplace_order_id uuid,
 p_permission text,p_accountable_operator uuid,p_approval_source uuid,p_approval_window_start timestamptz,
 p_approval_window_end timestamptz,p_revocation_owner uuid,p_credential_custodian uuid,p_credential_delivery_method text,
 p_credential_rotation_owner uuid,p_immediate_revocation_policy text,p_reason text,p_provenance text,
 p_correlation_id uuid,p_evidence_binding_fingerprint text) RETURNS bytea LANGUAGE sql IMMUTABLE STRICT
SET search_path=pg_catalog,pg_temp AS $$ SELECT
 public.s2a_v041_text('FLOOOW:S2A:APPROVAL-MANIFEST:1')||public.s2a_v041_text(p_schema_version::text)||
 public.s2a_v041_text(p_manifest_id::text)||public.s2a_v041_text(p_organization_id::text)||
 public.s2a_v041_text(p_mercado_livre_connection_id::text)||public.s2a_v041_text(p_omie_connection_id::text)||
 public.s2a_v041_text(p_source_order_reference)||public.s2a_v041_text(p_integration_reference)||
 public.s2a_v041_text(p_marketplace_order_id::text)||public.s2a_v041_text(p_permission)||
 public.s2a_v041_text(p_accountable_operator::text)||public.s2a_v041_text(p_approval_source::text)||
 public.s2a_v041_instant(p_approval_window_start)||public.s2a_v041_instant(p_approval_window_end)||
 public.s2a_v041_text(p_revocation_owner::text)||public.s2a_v041_text(p_credential_custodian::text)||
 public.s2a_v041_text(p_credential_delivery_method)||public.s2a_v041_text(p_credential_rotation_owner::text)||
 public.s2a_v041_text(p_immediate_revocation_policy)||public.s2a_v041_text(p_reason)||public.s2a_v041_text(p_provenance)||
 public.s2a_v041_text(p_correlation_id::text)||public.s2a_v041_text(p_evidence_binding_fingerprint) $$;

CREATE FUNCTION public.s2a_v041_signature_preimage(p_algorithm_id text,p_signer_key_id uuid,p_signer_key_fingerprint text,p_manifest_digest text)
RETURNS bytea LANGUAGE sql IMMUTABLE STRICT SET search_path=pg_catalog,pg_temp AS $$ SELECT
 public.s2a_v041_text('FLOOOW:S2A:APPROVAL-SIGNATURE:1')||public.s2a_v041_text(p_algorithm_id)||
 public.s2a_v041_text(p_signer_key_id::text)||public.s2a_v041_text(p_signer_key_fingerprint)||public.s2a_v041_text(p_manifest_digest) $$;

CREATE FUNCTION public.s2a_v041_proof_fingerprint(
 p_manifest bytea,p_manifest_digest text,p_preimage bytea,p_algorithm text,p_key_id uuid,p_key_revision integer,
 p_key_fingerprint text,p_lineage_fingerprint text,p_spki bytea,p_signature bytea,p_authority_id uuid,
 p_authority_revision integer,p_authority_fingerprint text,p_verified_at timestamptz) RETURNS text
LANGUAGE sql IMMUTABLE STRICT SET search_path=pg_catalog,pg_temp AS $$ SELECT encode(sha256(
 public.s2a_v041_text('FLOOOW:S2A:ACCEPTED-ATTESTATION-PROOF:1')||public.s2a_v041_text('1')||public.s2a_v041_text('1')||
 public.s2a_v041_frame(p_manifest)||public.s2a_v041_text(p_manifest_digest)||public.s2a_v041_frame(p_preimage)||
 public.s2a_v041_text(p_algorithm)||public.s2a_v041_text(p_key_id::text)||public.s2a_v041_text(p_key_revision::text)||
 public.s2a_v041_text(p_key_fingerprint)||public.s2a_v041_text(p_lineage_fingerprint)||public.s2a_v041_frame(p_spki)||
 public.s2a_v041_frame(p_signature)||public.s2a_v041_text(p_authority_id::text)||public.s2a_v041_text(p_authority_revision::text)||
 public.s2a_v041_text(p_authority_fingerprint)||public.s2a_v041_instant(p_verified_at)),'hex') $$;

CREATE FUNCTION public.s2a_v041_evidence_fingerprint(
 p_organization_id uuid,p_marketplace_order_id uuid,p_mercado_livre_connection_id uuid,
 p_omie_connection_id uuid,p_source_order_reference text,p_integration_reference text)
RETURNS text LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$
DECLARE ml_count bigint; bad bigint; ml record; omie_count bigint; latest timestamp; omie record; bytes bytea;
BEGIN
 SELECT count(*) INTO ml_count FROM public.marketplace_order_occurrence_source_promotion p
 WHERE p.organization_id=p_organization_id AND p.marketplace_order_id=p_marketplace_order_id
 AND p.source_connection_id=p_mercado_livre_connection_id AND p.source_capability='marketplace-economic.order-source'
 AND p.outcome IN ('PROMOTED','DUPLICATE');
 IF ml_count=0 THEN RAISE EXCEPTION 'ML scope mismatch' USING ERRCODE='P0017',DETAIL='SCOPE_MISMATCH'; END IF;
 SELECT count(*) INTO bad FROM public.marketplace_order_occurrence_source_promotion p
 LEFT JOIN public.marketplace_order_identity_registry i ON i.organization_id=p.organization_id AND i.marketplace_order_id=p.marketplace_order_id
 LEFT JOIN public.integration_mercado_livre_order_source_observation s ON s.organization_id=p.organization_id AND s.connection_id=p.source_connection_id
 AND s.capability=p.source_capability AND s.input_progress_version=p.source_input_progress_version AND s.record_ordinal=p.source_record_ordinal
 WHERE p.organization_id=p_organization_id AND p.marketplace_order_id=p_marketplace_order_id
 AND p.source_connection_id=p_mercado_livre_connection_id AND p.source_capability='marketplace-economic.order-source'
 AND p.outcome IN ('PROMOTED','DUPLICATE') AND (i.organization_id IS NULL OR s.organization_id IS NULL
 OR i.marketplace_key IS DISTINCT FROM 'mercado-livre' OR s.external_order_ref IS DISTINCT FROM i.external_order_id
 OR s.currency IS DISTINCT FROM i.currency);
 IF bad<>0 THEN RAISE EXCEPTION 'ML integrity failure' USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE'; END IF;
 SELECT p.source_input_progress_version,p.source_record_ordinal,i.marketplace_key,i.external_order_id,i.currency,p.outcome
 INTO STRICT ml FROM public.marketplace_order_occurrence_source_promotion p
 JOIN public.marketplace_order_identity_registry i ON i.organization_id=p.organization_id AND i.marketplace_order_id=p.marketplace_order_id
 JOIN public.integration_mercado_livre_order_source_observation s ON s.organization_id=p.organization_id AND s.connection_id=p.source_connection_id
 AND s.capability=p.source_capability AND s.input_progress_version=p.source_input_progress_version AND s.record_ordinal=p.source_record_ordinal
 WHERE p.organization_id=p_organization_id AND p.marketplace_order_id=p_marketplace_order_id
 AND p.source_connection_id=p_mercado_livre_connection_id AND p.source_capability='marketplace-economic.order-source'
 AND p.outcome IN ('PROMOTED','DUPLICATE') ORDER BY p.source_input_progress_version,p.source_record_ordinal LIMIT 1;

 SELECT count(*) INTO omie_count FROM public.integration_omie_transaction_evidence b
 WHERE b.organization_id=p_organization_id AND b.connection_id=p_omie_connection_id
 AND b.capability='marketplace-economic.omie-transaction-evidence.reacquisition-v3' AND b.source_order_ref=p_source_order_reference;
 IF omie_count=0 THEN RAISE EXCEPTION 'Omie scope mismatch' USING ERRCODE='P0017',DETAIL='SCOPE_MISMATCH'; END IF;
 SELECT count(*) INTO bad FROM public.integration_omie_transaction_evidence b
 LEFT JOIN public.integration_omie_transaction_evidence_v3 v USING(organization_id,connection_id,capability,input_progress_version,record_ordinal)
 LEFT JOIN public.integration_connector_page_commit pc USING(organization_id,connection_id,capability,input_progress_version)
 LEFT JOIN public.integration_connector_progress cp USING(organization_id,connection_id,capability)
 WHERE b.organization_id=p_organization_id AND b.connection_id=p_omie_connection_id
 AND b.capability='marketplace-economic.omie-transaction-evidence.reacquisition-v3' AND b.source_order_ref=p_source_order_reference
 AND (v.organization_id IS NULL OR pc.organization_id IS NULL OR cp.organization_id IS NULL OR v.semantic_fingerprint_version<>1
 OR v.source_evidence_semantic_fingerprint!~'^[0-9a-f]{64}$' OR b.record_ordinal<0 OR b.record_ordinal>=pc.record_count
 OR b.input_progress_version>=cp.progress_version OR (v.provider_created_local IS NULL AND v.provider_modified_local IS NULL)
 OR (v.provider_created_local IS NOT NULL AND v.provider_modified_local IS NOT NULL AND v.provider_modified_local<v.provider_created_local)
 OR pc.record_count<>(SELECT count(*) FROM public.integration_omie_transaction_evidence x WHERE x.organization_id=b.organization_id
 AND x.connection_id=b.connection_id AND x.capability=b.capability AND x.input_progress_version=b.input_progress_version)
 OR pc.record_count<>(SELECT count(*) FROM public.integration_omie_transaction_evidence_v3 x WHERE x.organization_id=b.organization_id
 AND x.connection_id=b.connection_id AND x.capability=b.capability AND x.input_progress_version=b.input_progress_version));
 IF bad<>0 THEN RAISE EXCEPTION 'Omie integrity failure' USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE'; END IF;
 SELECT max(coalesce(v.provider_modified_local,v.provider_created_local)) INTO latest
 FROM public.integration_omie_transaction_evidence b JOIN public.integration_omie_transaction_evidence_v3 v
 USING(organization_id,connection_id,capability,input_progress_version,record_ordinal)
 WHERE b.organization_id=p_organization_id AND b.connection_id=p_omie_connection_id
 AND b.capability='marketplace-economic.omie-transaction-evidence.reacquisition-v3' AND b.source_order_ref=p_source_order_reference;
 IF latest IS NULL THEN RAISE EXCEPTION 'Omie integrity failure' USING ERRCODE='P0018',DETAIL='INTEGRITY_FAILURE'; END IF;
 SELECT b.input_progress_version,b.record_ordinal,b.source_integration_ref,b.currency,v.semantic_fingerprint_version,
 v.source_evidence_semantic_fingerprint,coalesce(v.provider_modified_local,v.provider_created_local) provider_revision
 INTO STRICT omie FROM public.integration_omie_transaction_evidence b JOIN public.integration_omie_transaction_evidence_v3 v
 USING(organization_id,connection_id,capability,input_progress_version,record_ordinal)
 WHERE b.organization_id=p_organization_id AND b.connection_id=p_omie_connection_id
 AND b.capability='marketplace-economic.omie-transaction-evidence.reacquisition-v3' AND b.source_order_ref=p_source_order_reference
 AND coalesce(v.provider_modified_local,v.provider_created_local)=latest ORDER BY b.input_progress_version,b.record_ordinal LIMIT 1;
 IF EXISTS(SELECT 1 FROM public.integration_omie_transaction_evidence b JOIN public.integration_omie_transaction_evidence_v3 v
 USING(organization_id,connection_id,capability,input_progress_version,record_ordinal)
 WHERE b.organization_id=p_organization_id AND b.connection_id=p_omie_connection_id
 AND b.capability='marketplace-economic.omie-transaction-evidence.reacquisition-v3' AND b.source_order_ref=p_source_order_reference
 AND coalesce(v.provider_modified_local,v.provider_created_local)=latest AND
 (b.source_integration_ref IS DISTINCT FROM omie.source_integration_ref OR b.currency IS DISTINCT FROM omie.currency
 OR v.semantic_fingerprint_version IS DISTINCT FROM omie.semantic_fingerprint_version
 OR v.source_evidence_semantic_fingerprint IS DISTINCT FROM omie.source_evidence_semantic_fingerprint))
 THEN RAISE EXCEPTION 'Omie conflict' USING ERRCODE='P0016'; END IF;
 IF omie.source_integration_ref IS DISTINCT FROM p_integration_reference THEN
   RAISE EXCEPTION 'Omie scope mismatch' USING ERRCODE='P0017',DETAIL='SCOPE_MISMATCH'; END IF;
 IF omie.currency IS NOT NULL AND omie.currency IS DISTINCT FROM ml.currency THEN RAISE EXCEPTION 'Currency conflict' USING ERRCODE='P0016'; END IF;
 bytes:=public.s2a_v041_text('FLOOOW:S2A:EVIDENCE-BINDING:1')||public.s2a_v041_text(p_organization_id::text)||
 public.s2a_v041_text(p_marketplace_order_id::text)||public.s2a_v041_text(p_mercado_livre_connection_id::text)||
 public.s2a_v041_text('marketplace-economic.order-source')||public.s2a_v041_text(ml.source_input_progress_version::text)||
 public.s2a_v041_text(ml.source_record_ordinal::text)||public.s2a_v041_text(ml.marketplace_key)||public.s2a_v041_text(ml.external_order_id)||
 public.s2a_v041_text(ml.currency)||public.s2a_v041_text(ml.outcome)||public.s2a_v041_text(p_omie_connection_id::text)||
 public.s2a_v041_text('marketplace-economic.omie-transaction-evidence.reacquisition-v3')||
 public.s2a_v041_text(omie.input_progress_version::text)||public.s2a_v041_text(omie.record_ordinal::text)||
 public.s2a_v041_text(p_source_order_reference)||public.s2a_v041_nullable_text(omie.source_integration_ref)||
 public.s2a_v041_nullable_text(omie.currency)||public.s2a_v041_text(omie.semantic_fingerprint_version::text)||
 public.s2a_v041_text(omie.source_evidence_semantic_fingerprint)||public.s2a_v041_local(omie.provider_revision);
 RETURN encode(sha256(bytes),'hex');
END $$;

REVOKE ALL ON public.s2a_accepted_attestation FROM PUBLIC;
REVOKE ALL ON public.s2a_accepted_attestation FROM flooow_attestation_verifier;
REVOKE ALL ON FUNCTION public.s2a_reject_accepted_attestation_mutation() FROM PUBLIC;
REVOKE ALL ON FUNCTION public.s2a_v041_frame(bytea) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.s2a_v041_text(text) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.s2a_v041_instant(timestamptz) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.s2a_v041_local(timestamp) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.s2a_v041_nullable_text(text) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.s2a_v041_manifest_bytes(integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.s2a_v041_signature_preimage(text,uuid,text,text) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.s2a_v041_proof_fingerprint(bytea,text,bytea,text,uuid,integer,text,text,bytea,bytea,uuid,integer,text,timestamptz) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.s2a_v041_evidence_fingerprint(uuid,uuid,uuid,uuid,text,text) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.s2a_begin_attestation_verification(integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text,integer,bytea,text,text,uuid,text,bytea) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.s2a_persist_attestation_verification_result(integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text,integer,bytea,text,text,uuid,text,bytea,bytea,uuid,integer,text,bytea,uuid,integer,text,text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.s2a_begin_attestation_verification(integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text,integer,bytea,text,text,uuid,text,bytea) TO flooow_attestation_verifier;
GRANT EXECUTE ON FUNCTION public.s2a_persist_attestation_verification_result(integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamptz,timestamptz,uuid,uuid,text,uuid,text,text,text,uuid,text,integer,bytea,text,text,uuid,text,bytea,bytea,uuid,integer,text,bytea,uuid,integer,text,text) TO flooow_attestation_verifier;
