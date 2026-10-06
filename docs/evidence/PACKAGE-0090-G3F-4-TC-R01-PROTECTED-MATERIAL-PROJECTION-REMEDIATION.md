# Package 0090 G3F.4 — TC-R01 protected-material projection remediation

TC_R01_REMEDIATION=PASS; TC_R01_ORIGINAL_SEVERITY=HIGH; TC_R01_FINAL_STATUS=CLOSED. Evidence-only remediation, offline design verification. No database connection, runtime probe, new serializer deployment, key, signature or identifier generation. Production/schema bytes and the execution-denied fence are unchanged.

## Authority, baseline and precedence

Branch `checkpoint/package-0090-cloud-handoff`; local and live remote baseline `1ffbaa312f3c80f478c89298d2e3914ae50ae785`. Before mutation: tracked/staged changes zero, exactly one untracked temporal report, 1255 tracked byte hashes captured. Unexpected scope is a stop condition.

Original temporal-report SHA256 `4bafa0b9575ce6342b909c719acaa50a06df92cd916a8fa4059166145f70085f`. It remains byte-identical: this preserves its initial forensic HOLD and finding discovery as historical evidence. This remediation explicitly supersedes that report's TC-R01 dependency, unpromoted status, stop/commit restrictions and historical Git outcome for the current authorized run. Its eleven temporal conclusions, 28 adversarial cases, ten replay cases and seventeen boundary cases are unchanged. The old HOLD describes the pre-remediation review; the current adjudication below is PASS_UNCHANGED / time closure PASS after successful scoped commit/push verification. Reading either old report as current authority without this supersession is forbidden.

Immutable offending artifact: [ambiguous-commit recovery](PACKAGE-0090-G3F-4-AMBIGUOUS-COMMIT-RECOVERY.json), SHA256 `f22949d33e9daab11765e30f8b3da47be6e874c68f6f3e52e44f81cc367d5743` before/after. Exact current locations: Q12 field at line449, SQL at459, composed snapshot at859 (earlier approximate line references in the initial temporal report remain historical). These are unexecuted templates, not observed disclosure of actual protected values. This document supersedes their public-safe claim and supplies the only corrected public recovery template; it does not change the prior one-transaction graph, disposition algorithm or historical JSON. Other historical recovery prose claiming all26 old templates were secret-free is correspondingly superseded.

## Normative adjudication

PROTECTED_MATERIAL_PUBLIC_PROJECTION=FORBIDDEN. Repository terminology is “protected 256-bit execution possession secret”, stored “SHA-256 digest”, and “private possession digest”; UUID/flag alone is not ownership (SPEC0090 §1 line9). The digest is protected possession-sensitive authentication material, not a public binding fingerprint. Section21.1 line282 forbids its audit projection; §18 line249 excludes execution secrets and derived proofs from logs. Section3 lines62/66 separates current guard-M possession validation from auditor read-only replay. Section21.5 line302 explicitly forbids S02 possession inference; admission audit validity is not current mutation readiness. Section17/18 lines235/239 forbids refresh after restart and assigns DB time authority. Section22.1 execution read-purpose rows1636-1675 state digest never output; grants are internal owner reads, not public projection authority. Section22.3 line976 keeps preflight material fingerprints/tombstones ADMIN-only, never in public ACL/receipts. Section22 public receipt fields remain permitted; section21.11 line497 explicitly allows frozen five-field S10 public receipt but no verifier. These clauses govern recovery composition; no separate recovery exception permits a private digest.

NORMATIVE_CONTRADICTION=old Q12 labeled PUBLIC_COLUMNS and nonsecret_recovery_snapshot exported private possession_digest contrary to SPEC21.1/22. ROOT_CAUSE=prior evidence helper review.py:204-211 copied source-derived table columns with a denylist containing only secret_verifier and key_material; the composed snapshot inherited Q12. No possession-verification requirement justified the field. Its stated purpose was “Detect later execution ownership, never infer an admission from registration”. Durable binding/attempt/generation/execution/instance identity plus state/deadline/claim receipt satisfy that read classification. They never establish present possession.

## Selected replacement boundary

One remediation: explicit closed public field allowlists and sanctioned source provenance, with private guard-M facts left behind their existing boundary. There is no shadow digest, new proof, receipt, field, role, privilege or authority. Public evidence/JSON/log/replay sinks must receive only this projected value, never a raw row, internal record, input tuple, arbitrary nested object or hash of any such object. Unknown provenance fails closed before serialization/hashing; renaming cannot declassify private data. No protected presence/validity/comparison bit is permitted. Existing public row existence/state/time/UUID facts are not proof-presence bits.

The full-snapshot review also excludes ADMIN-only key_material_fingerprint (Q9) and unnecessary opaque frozen_receipt (Q24), external evidence_digest (Q6/Q7), and snapshot_digest (Q25). The latter generic administrative evidence digests have no source-enforced public-preimage whitelist; their names/32-byte shape cannot prove absence of protected derivation. They are denied public export rather than guessed safe. Removing them makes no new normative assertion that all such existing ADMIN facts are secret; private ADMIN checks and existing bounded domain reconciliation retain their authority. Initial registration has no execution/admission/stage/domain effects; any later row forces existing domain reconciliation, never fresh registration or automatic continuation. Public stage/operation identities detect this without exporting opaque payloads. Later exact receipt reconciliation uses only the already specified bounded public receipt contract, not this generic blob. Unknown or conflicting domain provenance stays HOLD.

Existing public SPKI/key lineage/manifest/signature/binding/history/ACL/policy fingerprints remain allowed by their explicit contracts. Frozen V042 initial-credential intent includes the verifier in a preexisting composite commitment (V042:142-164), and its five-field public receipt is expressly specified in SPEC21.11:497; it is not an execution-possession hash or a new workaround. No such existing receipt is promoted into current possession or renewed credential permission. Unrelated safe identifiers are not reclassified as secrets.

SAFE_Q12_PROOF:

```json
{
  "BEFORE_FIELDS": [
    "binding_id",
    "attempt_id",
    "generation",
    "execution_id",
    "instance_id",
    "executor_oid",
    "state",
    "possession_digest",
    "claimed_at",
    "expires_at",
    "claim_receipt_id",
    "lock_token"
  ],
  "AFTER_FIELDS": [
    "binding_id",
    "attempt_id",
    "generation",
    "execution_id",
    "instance_id",
    "executor_oid",
    "state",
    "claimed_at",
    "expires_at",
    "claim_receipt_id",
    "lock_token"
  ],
  "REMOVED_PROTECTED_FIELDS": [
    "possession_digest"
  ],
  "AUTHORIZED_RECOVERY_FIELDS": [
    "binding_id",
    "attempt_id",
    "generation",
    "execution_id",
    "instance_id",
    "executor_oid",
    "state",
    "claimed_at",
    "expires_at",
    "claim_receipt_id",
    "lock_token"
  ],
  "RECOVERY_DECISION_RULE": "Q12 row absent/present and exact existing scope/state/time/receipt classify later execution; any later execution requires domain reconciliation, never claims possession or new mutation readiness. No private value comparison, proof presence or hash enters the decision.",
  "EXECUTED": false
}
```

```sql
SELECT binding_id,attempt_id,generation,execution_id,instance_id,executor_oid,state,claimed_at,expires_at,claim_receipt_id,lock_token FROM public.offline_execution WHERE binding_id=:binding_id
```

Public scalar DTO for Q12 is exactly the eleven AFTER_FIELDS with their existing SQL UUID/int8/OID/text/timestamptz types. No optional possession member, opaque extension, nested tuple or extra hash is accepted. The object contract rejects missing/extra fields and protected/unproved provenance even in an allowed field. Metadata is scoped to existing trusted ADMIN; “public/non-secret” here means safe to serialize as governed recovery evidence, not a new anonymous/public API or service SELECT grant.

## Complete replacement snapshot (unexecuted)

All lookup predicates, authorities and snapshot/quiescence/locking requirements remain those of the original Q1-Q26. No speculative absence from a stale snapshot is permitted. Parameters are bound from retained immutable approved context. The 26 explicit projections below replace the old composed template; SQL to_jsonb(r) sees only the closed SELECT list, never a raw source table. Normalize/sort rows by existing primary keys and exact bytes/UTC microseconds before equality; jsonb_agg arrival order has no outcome authority. Q26 database identity/time observations are public context, not new timestamp issuance.

| Query | Table | Explicit safe columns | Removed from public view |
| --- | --- | --- | --- |
| Q1 | offline_binding_header | binding_schema_version, binding_id, deployment_id, deployment_incarnation_id, run_id, plan_id, execution_plan_version, organization_id, manifest_id, manifest_digest, canonical_manifest_hash, canonical_manifest_encoding_version, mercado_livre_connection_id, omie_connection_id, marketplace_order_id, source_order_reference, integration_reference, permission, reason, provenance, principal_id, credential_id, grant_id, decision_id, correlation_id, principal_operation_id, credential_operation_id, grant_operation_id, issued_at, valid_from, expires_at, identity_slots, offline_surface_version, deadline_policy_version, deadline_policy_digest, admission_contract_version, delivery_contract_version, reconciliation_contract_version, plan_fingerprint, canonical_manifest_bytes |  |
| Q2 | offline_expected_signed_attestation | binding_id, manifest_digest, algorithm_id, signer_key_id, signer_key_fingerprint, signature_bytes, canonical_expected_attestation, commitment_digest |  |
| Q3 | offline_binding_lifecycle | binding_id, state, lock_token |  |
| Q4 | offline_attempt_pointer | binding_id, current_attempt_id, generation, claim_permitted, lock_token |  |
| Q5 | offline_delivery | binding_id, attempt_id, generation, execution_id, instance_id, credential_id, initial_operation_id, fresh_applied_receipt_id, state, delivery_receipt_id, attempted_at, operation_deadline, observed_at, observation_code, recorded_at, lock_token |  |
| Q6 | offline_reconciliation | binding_id, state, recorded_at | evidence_digest |
| Q7 | offline_ceremony_result | binding_id, result, recorded_at | evidence_digest |
| Q8 | offline_readiness | deployment_id, incarnation_id, state, active_key_version, policy_version, policy_digest, history_manifest, acl_manifest, watchdog_checked_at, watchdog_healthy |  |
| Q9 | offline_preflight_key | incarnation_id, lineage_id, key_version, key_state | key_material_fingerprint |
| Q10 | offline_deadline_policy | policy_version, policy_digest, canonical_policy, effective_from |  |
| Q11 | offline_attempt | binding_id, attempt_id, generation, state, claimed_at, expires_at, lock_token |  |
| Q12 | offline_execution | binding_id, attempt_id, generation, execution_id, instance_id, executor_oid, state, claimed_at, expires_at, claim_receipt_id, lock_token | possession_digest |
| Q13 | s2a_signer_key_revision | organization_id, signer_key_id, revision, signer_subject_id, algorithm_id, subject_public_key_info_der, signer_key_fingerprint, state, valid_from, effective_at, supersedes_revision, lineage_fingerprint, reason, provenance, correlation_id, recorded_at |  |
| Q14 | s2a_signer_authority_revision | organization_id, signer_authority_id, revision, signer_subject_id, signer_authorizing_institution_id, signer_role, signer_key_id, signer_key_revision, signer_key_fingerprint, approval_action, permission, valid_from, valid_until, state, supersedes_signer_authority_id, signer_authority_fingerprint, reason, provenance, approval_source_id, correlation_id, decided_at |  |
| Q15 | s2a_accepted_attestation | organization_id, manifest_id, artifact_version, schema_version, canonicalization_version, canonical_manifest_bytes, manifest_digest, canonical_signature_preimage_bytes, algorithm_id, signer_key_id, signer_key_revision, signer_key_fingerprint, signer_key_lineage_fingerprint, subject_public_key_info_der, signature_bytes, signer_authority_id, signer_authority_revision, signer_authority_fingerprint, verified_at, accepted_proof_fingerprint, recorded_at |  |
| Q16 | s2a_attestation_consumption | organization_id, manifest_id, manifest_digest, principal_id, correlation_id, consumed_at |  |
| Q17 | command_principal | organization_id, principal_id, mercado_livre_connection_id, omie_connection_id, reason, provenance, correlation_id, decided_at |  |
| Q18 | command_credential_revision | organization_id, principal_id, credential_id, revision, supersedes_revision, state, reason, provenance, correlation_id, decided_at |  |
| Q19 | command_permission_grant | organization_id, principal_id, grant_id, permission, state, revision, supersedes_grant_id, reason, provenance, correlation_id, decided_at |  |
| Q20 | command_authority_operation | organization_id, operation_id, operation, principal_id, credential_id, credential_revision, grant_id, grant_revision, permission, state, intent_fingerprint, receipt_fingerprint, correlation_id, decided_at, attestation_manifest_id |  |
| Q21 | marketplace_transaction_identity_decision | organization_id, decision_id, omie_connection_id, source_order_reference, marketplace_order_id, kind, reason, revision, supersedes_decision_id, ml_connection_id, ml_capability, ml_progress_version, ml_record_ordinal, external_order_id, currency, omie_capability, omie_progress_version, omie_record_ordinal, omie_semantic_fingerprint, provider_revision_local, principal_id, credential_id, credential_revision, grant_id, grant_revision, permission, authorization_semantic_version, authorization_fingerprint, intent_fingerprint, decision_semantic_fingerprint, provenance, correlation_id, decided_at |  |
| Q22 | marketplace_transaction_identity_head | organization_id, omie_connection_id, source_order_reference, marketplace_order_id, decision_id, kind |  |
| Q23 | offline_admission | admission_id, deployment_id, incarnation_id, binding_id, attempt_id, generation, execution_id, instance_id, executor_oid, credential_id, credential_revision, principal_id, organization_id, grant_id, grant_revision, authorization_fingerprint, permission, authenticated_at, expires_at, durable_state, consumed_decision_id, consumed_at, lock_token |  |
| Q24 | offline_stage_receipt | binding_id, attempt_id, generation, execution_id, instance_id, stage, receipt_id, operation_id, effect_time | frozen_receipt |
| Q25 | offline_diagnostic_evidence | binding_id, attempt_id, generation, classification, recorded_at, recorder_identity | snapshot_digest |
| Q26 | pg_database / pg_control_system | database_name, database_oid, system_identifier, server_version_num, database_version, observed_database_wall_clock |  |

```sql
SELECT pg_catalog.jsonb_build_object(
  'Q1', (SELECT coalesce(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r)), '[]'::pg_catalog.jsonb) FROM (SELECT binding_schema_version,binding_id,deployment_id,deployment_incarnation_id,run_id,plan_id,execution_plan_version,organization_id,manifest_id,manifest_digest,canonical_manifest_hash,canonical_manifest_encoding_version,mercado_livre_connection_id,omie_connection_id,marketplace_order_id,source_order_reference,integration_reference,permission,reason,provenance,principal_id,credential_id,grant_id,decision_id,correlation_id,principal_operation_id,credential_operation_id,grant_operation_id,issued_at,valid_from,expires_at,identity_slots,offline_surface_version,deadline_policy_version,deadline_policy_digest,admission_contract_version,delivery_contract_version,reconciliation_contract_version,plan_fingerprint,canonical_manifest_bytes FROM public.offline_binding_header WHERE binding_id=:binding_id OR (deployment_incarnation_id=:incarnation_id AND plan_id=:plan_id) OR run_id=:run_id OR manifest_id=:manifest_id OR principal_id=:principal_id OR credential_id=:credential_id OR grant_id=:grant_id OR decision_id=:decision_id OR principal_operation_id=:principal_operation_id OR credential_operation_id=:credential_operation_id OR grant_operation_id=:grant_operation_id) AS r),
  'Q2', (SELECT coalesce(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r)), '[]'::pg_catalog.jsonb) FROM (SELECT binding_id,manifest_digest,algorithm_id,signer_key_id,signer_key_fingerprint,signature_bytes,canonical_expected_attestation,commitment_digest FROM public.offline_expected_signed_attestation WHERE binding_id=:binding_id) AS r),
  'Q3', (SELECT coalesce(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r)), '[]'::pg_catalog.jsonb) FROM (SELECT binding_id,state,lock_token FROM public.offline_binding_lifecycle WHERE binding_id=:binding_id) AS r),
  'Q4', (SELECT coalesce(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r)), '[]'::pg_catalog.jsonb) FROM (SELECT binding_id,current_attempt_id,generation,claim_permitted,lock_token FROM public.offline_attempt_pointer WHERE binding_id=:binding_id) AS r),
  'Q5', (SELECT coalesce(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r)), '[]'::pg_catalog.jsonb) FROM (SELECT binding_id,attempt_id,generation,execution_id,instance_id,credential_id,initial_operation_id,fresh_applied_receipt_id,state,delivery_receipt_id,attempted_at,operation_deadline,observed_at,observation_code,recorded_at,lock_token FROM public.offline_delivery WHERE binding_id=:binding_id) AS r),
  'Q6', (SELECT coalesce(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r)), '[]'::pg_catalog.jsonb) FROM (SELECT binding_id,state,recorded_at FROM public.offline_reconciliation WHERE binding_id=:binding_id) AS r),
  'Q7', (SELECT coalesce(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r)), '[]'::pg_catalog.jsonb) FROM (SELECT binding_id,result,recorded_at FROM public.offline_ceremony_result WHERE binding_id=:binding_id) AS r),
  'Q8', (SELECT coalesce(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r)), '[]'::pg_catalog.jsonb) FROM (SELECT deployment_id,incarnation_id,state,active_key_version,policy_version,policy_digest,history_manifest,acl_manifest,watchdog_checked_at,watchdog_healthy FROM public.offline_readiness WHERE incarnation_id=:incarnation_id) AS r),
  'Q9', (SELECT coalesce(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r)), '[]'::pg_catalog.jsonb) FROM (SELECT incarnation_id,lineage_id,key_version,key_state FROM public.offline_preflight_key WHERE incarnation_id=:incarnation_id) AS r),
  'Q10', (SELECT coalesce(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r)), '[]'::pg_catalog.jsonb) FROM (SELECT policy_version,policy_digest,canonical_policy,effective_from FROM public.offline_deadline_policy WHERE policy_version=:deadline_policy_version) AS r),
  'Q11', (SELECT coalesce(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r)), '[]'::pg_catalog.jsonb) FROM (SELECT binding_id,attempt_id,generation,state,claimed_at,expires_at,lock_token FROM public.offline_attempt WHERE binding_id=:binding_id) AS r),
  'Q12', (SELECT coalesce(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r)), '[]'::pg_catalog.jsonb) FROM (SELECT binding_id,attempt_id,generation,execution_id,instance_id,executor_oid,state,claimed_at,expires_at,claim_receipt_id,lock_token FROM public.offline_execution WHERE binding_id=:binding_id) AS r),
  'Q13', (SELECT coalesce(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r)), '[]'::pg_catalog.jsonb) FROM (SELECT organization_id,signer_key_id,revision,signer_subject_id,algorithm_id,subject_public_key_info_der,signer_key_fingerprint,state,valid_from,effective_at,supersedes_revision,lineage_fingerprint,reason,provenance,correlation_id,recorded_at FROM public.s2a_signer_key_revision WHERE (organization_id=:organization_id AND signer_key_id=:signer_key_id) OR signer_key_id=:signer_key_id) AS r),
  'Q14', (SELECT coalesce(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r)), '[]'::pg_catalog.jsonb) FROM (SELECT organization_id,signer_authority_id,revision,signer_subject_id,signer_authorizing_institution_id,signer_role,signer_key_id,signer_key_revision,signer_key_fingerprint,approval_action,permission,valid_from,valid_until,state,supersedes_signer_authority_id,signer_authority_fingerprint,reason,provenance,approval_source_id,correlation_id,decided_at FROM public.s2a_signer_authority_revision WHERE (organization_id=:organization_id AND signer_subject_id=:signer_subject_id AND signer_key_id=:signer_key_id AND approval_action='S2A_FIELD_PROOF_APPROVAL' AND permission='TRANSACTION_IDENTITY_DECISION_WRITE') OR signer_authority_id=:signer_authority_id) AS r),
  'Q15', (SELECT coalesce(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r)), '[]'::pg_catalog.jsonb) FROM (SELECT organization_id,manifest_id,artifact_version,schema_version,canonicalization_version,canonical_manifest_bytes,manifest_digest,canonical_signature_preimage_bytes,algorithm_id,signer_key_id,signer_key_revision,signer_key_fingerprint,signer_key_lineage_fingerprint,subject_public_key_info_der,signature_bytes,signer_authority_id,signer_authority_revision,signer_authority_fingerprint,verified_at,accepted_proof_fingerprint,recorded_at FROM public.s2a_accepted_attestation WHERE (organization_id=:organization_id AND manifest_id=:manifest_id) OR manifest_id=:manifest_id) AS r),
  'Q16', (SELECT coalesce(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r)), '[]'::pg_catalog.jsonb) FROM (SELECT organization_id,manifest_id,manifest_digest,principal_id,correlation_id,consumed_at FROM public.s2a_attestation_consumption WHERE (organization_id=:organization_id AND manifest_id=:manifest_id) OR principal_id=:principal_id) AS r),
  'Q17', (SELECT coalesce(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r)), '[]'::pg_catalog.jsonb) FROM (SELECT organization_id,principal_id,mercado_livre_connection_id,omie_connection_id,reason,provenance,correlation_id,decided_at FROM public.command_principal WHERE principal_id=:principal_id) AS r),
  'Q18', (SELECT coalesce(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r)), '[]'::pg_catalog.jsonb) FROM (SELECT organization_id,principal_id,credential_id,revision,supersedes_revision,state,reason,provenance,correlation_id,decided_at FROM public.command_credential_revision WHERE credential_id=:credential_id OR (organization_id=:organization_id AND principal_id=:principal_id)) AS r),
  'Q19', (SELECT coalesce(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r)), '[]'::pg_catalog.jsonb) FROM (SELECT organization_id,principal_id,grant_id,permission,state,revision,supersedes_grant_id,reason,provenance,correlation_id,decided_at FROM public.command_permission_grant WHERE grant_id=:grant_id OR (organization_id=:organization_id AND principal_id=:principal_id)) AS r),
  'Q20', (SELECT coalesce(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r)), '[]'::pg_catalog.jsonb) FROM (SELECT organization_id,operation_id,operation,principal_id,credential_id,credential_revision,grant_id,grant_revision,permission,state,intent_fingerprint,receipt_fingerprint,correlation_id,decided_at,attestation_manifest_id FROM public.command_authority_operation WHERE (organization_id=:organization_id AND (operation_id IN (:principal_operation_id,:credential_operation_id,:grant_operation_id) OR attestation_manifest_id=:manifest_id OR principal_id=:principal_id)) OR operation_id IN (:principal_operation_id,:credential_operation_id,:grant_operation_id)) AS r),
  'Q21', (SELECT coalesce(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r)), '[]'::pg_catalog.jsonb) FROM (SELECT organization_id,decision_id,omie_connection_id,source_order_reference,marketplace_order_id,kind,reason,revision,supersedes_decision_id,ml_connection_id,ml_capability,ml_progress_version,ml_record_ordinal,external_order_id,currency,omie_capability,omie_progress_version,omie_record_ordinal,omie_semantic_fingerprint,provider_revision_local,principal_id,credential_id,credential_revision,grant_id,grant_revision,permission,authorization_semantic_version,authorization_fingerprint,intent_fingerprint,decision_semantic_fingerprint,provenance,correlation_id,decided_at FROM public.marketplace_transaction_identity_decision WHERE decision_id=:decision_id OR (organization_id=:organization_id AND principal_id=:principal_id)) AS r),
  'Q22', (SELECT coalesce(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r)), '[]'::pg_catalog.jsonb) FROM (SELECT organization_id,omie_connection_id,source_order_reference,marketplace_order_id,decision_id,kind FROM public.marketplace_transaction_identity_head WHERE (organization_id=:organization_id AND omie_connection_id=:omie_connection_id AND source_order_reference=:source_order_reference AND marketplace_order_id=:marketplace_order_id) OR decision_id=:decision_id) AS r),
  'Q23', (SELECT coalesce(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r)), '[]'::pg_catalog.jsonb) FROM (SELECT admission_id,deployment_id,incarnation_id,binding_id,attempt_id,generation,execution_id,instance_id,executor_oid,credential_id,credential_revision,principal_id,organization_id,grant_id,grant_revision,authorization_fingerprint,permission,authenticated_at,expires_at,durable_state,consumed_decision_id,consumed_at,lock_token FROM public.offline_admission WHERE binding_id=:binding_id) AS r),
  'Q24', (SELECT coalesce(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r)), '[]'::pg_catalog.jsonb) FROM (SELECT binding_id,attempt_id,generation,execution_id,instance_id,stage,receipt_id,operation_id,effect_time FROM public.offline_stage_receipt WHERE binding_id=:binding_id) AS r),
  'Q25', (SELECT coalesce(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r)), '[]'::pg_catalog.jsonb) FROM (SELECT binding_id,attempt_id,generation,classification,recorded_at,recorder_identity FROM public.offline_diagnostic_evidence WHERE binding_id=:binding_id) AS r),
  'Q26', (SELECT coalesce(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r)), '[]'::pg_catalog.jsonb) FROM (SELECT current_database() AS database_name,(SELECT oid FROM pg_catalog.pg_database WHERE datname=current_database()) AS database_oid,(SELECT system_identifier FROM pg_catalog.pg_control_system()) AS system_identifier,current_setting('server_version_num') AS server_version_num,version() AS database_version,clock_timestamp() AS observed_database_wall_clock) AS r)
) AS nonsecret_recovery_snapshot
```

## Query-first determinism and noninterference

Retain original P1-P10 and nine-step recovery algorithm, except public P6/P7 checks use safe metadata/constraints rather than disclosing protected or unproved digest payloads. Key material tombstone checks remain existing ADMIN-only work, not a public fingerprint export. Initial NONE/NOT_STARTED invariant checks and constraints establish absence of administrative terminal evidence without an exported digest-presence bit. Exact complete eleven-row root -> historical registration/replay, executable=false; later effect rows -> existing domain reconciliation; proper nonempty subset/identity conflict -> invariant violation/HOLD; absent complete root only after writer quiescence/fresh locked snapshot -> whole-root abandonment under existing authority; DB unavailable/in-flight/unknown -> QUERY_FIRST/HOLD. Legacy signer-only orphan requires original path evidence and existing disable-then-retire cleanup before fresh root. No repair/upsert/delete, secret reconstruction, subset IDs, time renewal or blind replay.

For fixed public durable facts and arbitrary different private possession values p1/p2, projection(S,p1)=projection(S,p2); query-first classification depends only on S and verified public context, never p. An actual M operation may accept/deny supplied possession internally; that authorized private validation is not a public recovery oracle. Safe metadata does not prove a missing digest exists/is valid. Missing private proof denies mutation and permits historical reads only; invariant corruption never causes regeneration.

## Adversarial checks

Offline source/contract checks, not deployed adapter/runtime certification. Abstract protected provenance labels are used; no secret bytes or cryptographic material are generated. The executable model rejects literal/renamed/nested/derived/composite/sink-bypass injections, including taint under an allowed column name. Finite state enumeration checks the existing classification vocabulary, not every future database fault.

| Case / PRECONDITION | EXPECTED_DECISION | PUBLIC_DATA_ALLOWED | PROTECTED_DATA_ALLOWED | RECOVERY_RESULT | FAIL_CLOSED_CONDITION | Validation |
| --- | --- | --- | --- | --- | --- | --- |
| P01 literal field | DENY_PUBLIC_OUTPUT | Existing sanctioned scalar identity/state/time facts only | None in public/log/evidence/replay; existing M may privately validate | HOLD export; no retry/regeneration | Unknown field, nesting, tainted or unproved source provenance | PASS_DENIED |
| P02 renamed field | DENY_PUBLIC_OUTPUT | Existing sanctioned scalar identity/state/time facts only | None in public/log/evidence/replay; existing M may privately validate | HOLD export; no retry/regeneration | Unknown field, nesting, tainted or unproved source provenance | PASS_DENIED |
| P03 nested protected tuple | DENY_PUBLIC_OUTPUT | Existing sanctioned scalar identity/state/time facts only | None in public/log/evidence/replay; existing M may privately validate | HOLD export; no retry/regeneration | Unknown field, nesting, tainted or unproved source provenance | PASS_DENIED |
| P04 digest of digest under safe name | DENY_PUBLIC_OUTPUT | Existing sanctioned scalar identity/state/time facts only | None in public/log/evidence/replay; existing M may privately validate | HOLD export; no retry/regeneration | Unknown field, nesting, tainted or unproved source provenance | PASS_DENIED |
| P05 composite equality fingerprint under allowed name | DENY_PUBLIC_OUTPUT | Existing sanctioned scalar identity/state/time facts only | None in public/log/evidence/replay; existing M may privately validate | HOLD export; no retry/regeneration | Unknown field, nesting, tainted or unproved source provenance | PASS_DENIED |
| P06 log sink bypass | DENY_PUBLIC_OUTPUT | Existing sanctioned scalar identity/state/time facts only | None in public/log/evidence/replay; existing M may privately validate | HOLD export; no retry/regeneration | Unknown field, nesting, tainted or unproved source provenance | PASS_DENIED |
| P07 evidence sink bypass | DENY_PUBLIC_OUTPUT | Existing sanctioned scalar identity/state/time facts only | None in public/log/evidence/replay; existing M may privately validate | HOLD export; no retry/regeneration | Unknown field, nesting, tainted or unproved source provenance | PASS_DENIED |
| P08 replay sink bypass | DENY_PUBLIC_OUTPUT | Existing sanctioned scalar identity/state/time facts only | None in public/log/evidence/replay; existing M may privately validate | HOLD export; no retry/regeneration | Unknown field, nesting, tainted or unproved source provenance | PASS_DENIED |
| P09 Recovery without protected column | ALLOW exact historical inspection | Allowlisted durable scope/identity/state/deadlines; no possession evidence | Private M boundary only; no export, reconstruction or replacement | Existing query-first action; historical replay never authorizes mutation | Missing scope, uncertain writer, partial/conflicting root or unknown provenance | PASS |
| P10 Duplicate recovery | RETURN same historical root; no mutation | Allowlisted durable scope/identity/state/deadlines; no possession evidence | Private M boundary only; no export, reconstruction or replacement | Existing query-first action; historical replay never authorizes mutation | Missing scope, uncertain writer, partial/conflicting root or unknown provenance | PASS |
| P11 Different private proofs with identical public facts | IDENTICAL public output; no comparison oracle | Allowlisted durable scope/identity/state/deadlines; no possession evidence | Private M boundary only; no export, reconstruction or replacement | Existing query-first action; historical replay never authorizes mutation | Missing scope, uncertain writer, partial/conflicting root or unknown provenance | PASS |
| P12 Protected proof unavailable after process loss | READ history; DENY mutable continuation; no regeneration | Allowlisted durable scope/identity/state/deadlines; no possession evidence | Private M boundary only; no export, reconstruction or replacement | Existing query-first action; historical replay never authorizes mutation | Missing scope, uncertain writer, partial/conflicting root or unknown provenance | PASS |
| P13 Existing private guard M path | UNCHANGED conceptual private validation; NOT runtime qualified | Allowlisted durable scope/identity/state/deadlines; no possession evidence | Private M boundary only; no export, reconstruction or replacement | Existing query-first action; historical replay never authorizes mutation | Missing scope, uncertain writer, partial/conflicting root or unknown provenance | PASS |
| P14 Historical defective evidence | PRESERVE exact historical bytes and supersede unsafe template | Allowlisted durable scope/identity/state/deadlines; no possession evidence | Private M boundary only; no export, reconstruction or replacement | Existing query-first action; historical replay never authorizes mutation | Missing scope, uncertain writer, partial/conflicting root or unknown provenance | PASS |
| P15 Complete Q1-Q26 snapshot | ALLOW explicit closed projection; unknown field/source DENY | Allowlisted durable scope/identity/state/deadlines; no possession evidence | Private M boundary only; no export, reconstruction or replacement | Existing query-first action; historical replay never authorizes mutation | Missing scope, uncertain writer, partial/conflicting root or unknown provenance | PASS |
| P16 Same legal action after column removal | IDENTICAL query-first outcome for every enumerated abstract state | Allowlisted durable scope/identity/state/deadlines; no possession evidence | Private M boundary only; no export, reconstruction or replacement | Existing query-first action; historical replay never authorizes mutation | Missing scope, uncertain writer, partial/conflicting root or unknown provenance | PASS |
| P17 Replacement digest workaround | DENY new or renamed private-derived public hash | Allowlisted durable scope/identity/state/deadlines; no possession evidence | Private M boundary only; no export, reconstruction or replacement | Existing query-first action; historical replay never authorizes mutation | Missing scope, uncertain writer, partial/conflicting root or unknown provenance | PASS |
| P18 Authority expansion | NONE; existing ADMIN/M/auditor boundaries and V043 fence retained | Allowlisted durable scope/identity/state/deadlines; no possession evidence | Private M boundary only; no export, reconstruction or replacement | Existing query-first action; historical replay never authorizes mutation | Missing scope, uncertain writer, partial/conflicting root or unknown provenance | PASS |

Validation: P01-P18 all PASS; 18432 abstract state/private-context checks (2048 eleven-row presence subsets ×3 scope/quiescence conditions ×3 private labels). The prior pure classification function is extracted without executing its evidence-writing script, compared to independent complete/empty/proper-subset expectations and exercised on projected row identities; legacy governance-only and later-effect outcomes also checked. Noninterference with two different private labels and missing private value; all26 replacement SQL templates unexecuted, explicit projection and forbidden-source checks PASS; 1255 tracked hashes and temporal-report hash unchanged. This model is review tooling in the private work directory, not a production implementation.

## Independent time-contract revalidation

TIME_CONTRACT_REVALIDATION=PASS_UNCHANGED for all eleven temporal conclusions. Re-read the complete original temporal report, all source pins and source clauses above against the corrected recovery boundary after TC-R01 checks passed. Only gate promotion/dependency status changes in this new adjudication. The temporal report itself is preserved unchanged. No timestamp, temporal bound, canonical codec, lifetime, retry identity, signed-byte or clock rule changes.

| Required conclusion | Revalidated rule | Source/boundary review | Result |
| --- | --- | --- | --- |
| TIME_CONTRACT_AUTHORITY | Existing PLAN_BINDING_ADMIN for immutable binding profile; existing separately governed rehearsal S2A approval authority for manifest lifetime. Database cluster alone supplies instants. | SPEC18; retained PLAN_BINDING_ADMIN and prior fixed60s rehearsal approval | PASS_UNCHANGED |
| TIME_CAPTURE_EVENT | FINAL_CEREMONY_TIME_CAPTURE: once in the already selected T_REG after canonical locks, before key birth/governance/signing; value is the DB-owned opening instant of that SAME transaction, not the time of the read. | Same T_REG once after locks/prekey; transaction opening value, not read event | PASS_UNCHANGED |
| TIME_SOURCE | T0 := pg_catalog.transaction_timestamp() from exact T_REG; fresh pg_catalog.clock_timestamp() on same approved cluster for every eligibility/recovery observation. These are two functions of one authority, not two independent clocks. | SPEC18: one DB authority; transaction_timestamp identity vs clock_timestamp eligibility | PASS_UNCHANGED |
| ISSUED_AT_CONTRACT | issued_at=T0. Existing binding issuance begins at canonical T_REG opening, after identity allocation but before signing; not allocation time, signature time, verified_at, durable commit time or Q receipt issuance. | Header tag29; same original T0; not allocation/verification/receipt time | PASS_UNCHANGED |
| VALID_FROM_CONTRACT | valid_from=issued_at=T0=manifest.approvalWindowStart. No future-dating relative to fresh DB now; no delayed-start alternative in this profile. | Header tag30; signed manifest position12; exact profile equality | PASS_UNCHANGED |
| EXPIRES_AT_CONTRACT | expires_at=manifest.approvalWindowEnd=T0+60000000us, exact checked addition. Lifetime is the preexisting immutable60s rehearsal approval contract, not config, mutable default, preflight TTL or new policy value. | Header tag31; signed position13; checked +60000000us; policy compatibility still required | PASS_UNCHANGED |
| EXPIRY_BOUNDARY_CONTRACT | Half-open [T0,T0+60000000us). Fresh DB now==expires_at is expired; now<valid_from is future/not-yet-valid and blocks. Eligibility applies at signing and canonical write/postcheck/pre-COMMIT guard, not eventual commit visibility/ACK. | SPEC3 line60/ADR81: canonical-write admission vs later visibility; half-open interval | PASS_UNCHANGED |
| SIGNING_WINDOW_CONTRACT | One unchanged60s approval/header window; key/public authority start at T0 and authority end matches frozen approval end under existing approval governance. Validate fresh DB clock before key/sign, after signature/JCA, before writes, after complete write set and after constraints immediately before COMMIT. No extension, grace, stale transaction-start eligibility check or new receipt. | Same immutable60s; all fresh guards retained; operational margin NOT proven | PASS_UNCHANGED |
| REPLAY_IDEMPOTENCY | Exact committed root -> REPLAY_EXISTING historical header/original/receipts with original T0/expiry unchanged; zero new mutation/signing/time capture, including expiry or new process/runtime/policy. Conflicting/missing root -> BLOCK or RECOVER, never repair. | SPEC17/18: original tuple read only; no resampling/renewal/private proof reconstruction | PASS_UNCHANGED |
| RECOVERY_DETERMINISM | Before any durable outcome assumption use exact identity and corrected nonsecret query set after writer quiescence/canonical locks. Unknown -> RECOVER/HOLD; exact commit -> REPLAY_EXISTING regardless current expiry, with fresh effects denied after expiry; confirmed absent -> prior abandonment/cleanup and whole fresh authorized ceremony. TC-R01 prevents current snapshot from being used/promoted as nonsecret evidence. | Existing algorithm/P1-P10 preserved, replacement public projection here; writer quiescence/locks/fresh snapshot mandatory | PASS_UNCHANGED |
| CRYPTOGRAPHIC_TIME_BINDING | YES_SELECTED_DERIVED_PROFILE: manifest signature binds start/end via manifest digest; equality derives all three header instants. No direct three-header-field signature or whole-header signature claim. | Codec signed22-field manifest endpoints -> manifest SHA256 -> signature preimage; equality derives three header times, not direct header signature | PASS_UNCHANGED |

Additional reread checks: exact microseconds/no rounding; UTC six-fraction canonical text distinct from signed-i64 header codec; checked+60000000us and year0001..9999 selected profile; finite endpoint range/round-trip; T0 captured once before key birth; waits consume original transaction-start window; transaction_timestamp never fresh eligibility; rollback on controlled expired transaction; unknown in-flight COMMIT query-first, not assumed rollback; original committed tuple remains historical after expiry; clock rollback/transient continuity fails closed, restart no automatic unfinished continuation; approved BINDING_VALIDITY actual/max compatibility mandatory; operational watchdog continuity/latency/margin still unqualified; two signed endpoints derive all three header instants by exact equality, not whole-header Ed25519 signature. Original T01-T28, R1-R10 and17 boundary cases remain present and unchanged.

## Exposure occurrence ledger and derived flow review

A=PRIVATE/AUTHORIZED input/custody; B=INTERNAL/PROTECTED stored/guard fact or normative definition; C=PUBLIC/NON-SECRET sanctioned output (or explicitly defective historical declaration); D=HISTORICAL EVIDENCE ONLY; E=UNKNOWN, deny projection. Each listed line includes all matching occurrences on that physical line; ×n indicates multiple matches. Embedded escaped SQL/function source is classified as historical source text, not actual returned digest bytes. Source digests bind exact contents. Historical artifacts never override SPEC. The offending JSON has D preservation status and C-forbidden exposure intent, explicitly recorded below. Unknown generic future blob contents are denied by removing them; no unknown member is admitted.

Search inventory includes every tracked applications file and all PACKAGE0090 evidence/spec/ADR plus preserved temporal report, decoded UTF8/JSON and encoded archive candidates. Patterns: possession_digest, possessionDigest, possession_secret, execution possession and nonsecret_recovery_snapshot; equivalent provenance reviewed through execution_record/final_execution_record, sha256($8/$9), source output frames, protected derived_credential_proof/secret_verifier paths and public intent/receipt fingerprints. No separate production API/JSON schema or public DTO with a possession digest was found. The source output-frame scan covered 12 assignments; none references possession/digest/secret_verifier/key material. Claim SQL returns newly assigned attempt/execution/deadline/receipt metadata, never digest; bootstrap stores sha256($8) privately; mutable guards compare sha256($9) internally and never return it. Internal P returns only guarded bool, inaccessible to public callers. S02/S03 auditor output derives state/authorized domain consistency, not possession comparison; audit owner has no digest SELECT. Launcher uses ephemeral secret context and erases it at finally; JDBC passes private proof parameters with no logging/serialization, output DTOs remain bounded SPEC frames. Tests exercising private input are A test-fixture-only.

Archive walk: 112 PACKAGE0090 JSON artifacts parsed; 432 decoded strings mention possession, inspected as source/contracts/fixtures. Encoded source hits: 16. No archive execution occurred. All histories are immutable.

| Path / pinned SHA256 | Class | Every matching physical line (multiplicity) |
| --- | --- | --- |
| applications/command-authority-ceremony/src/main/kotlin/io/flooow/ceremony/GovernedCall.kt<br>`265c6e426610817466943ae7340bc3a5482a0b8dd212ff0f3026fdb4a182bcdc` | A PRIVATE/AUTHORIZED: bounded parameter/ephemeral/test custody | 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22 |
| applications/command-authority-ceremony/src/main/kotlin/io/flooow/ceremony/GovernedJdbc.kt<br>`6274b34f8884632503e3b5796d143c06fdaa02a5d8154d9c00173cbb18194017` | A PRIVATE/AUTHORIZED: bounded parameter/ephemeral/test custody | 52 |
| applications/command-authority-ceremony/src/main/kotlin/io/flooow/ceremony/GovernedOfflineFieldProofLauncher.kt<br>`4f0732c34e883aa84e88ce220b874479c856e4320c32bbca6e01ac161f92676f` | A PRIVATE/AUTHORIZED: bounded parameter/ephemeral/test custody | 86, 89 |
| applications/command-authority-ceremony/src/test/kotlin/io/flooow/ceremony/GovernedAdaptersTest.kt<br>`46623a6c36ee24186df8b5ee94896223f4ad7be2b201007653f7f839e1dd3f73` | A PRIVATE/AUTHORIZED: bounded parameter/ephemeral/test custody | 225 |
| applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V043__create_governed_offline_field_proof_capability_composition.sql<br>`3301b254e883ae2ebf9e1d41036f15bc7839c1ae9e2404e692bc2ec864204109` | B INTERNAL/PROTECTED: DDL, owner ACL, guards/storage; no returned digest | 644, 665, 3029, 3059, 3089, 3119, 3124, 3127, 3130, 3133, 3136, 3139, 3142, 3145, 3148, 4031, 4263, 4454, 4458, 5739, 5740, 5929, 6014, 6136, 6551, 8242, 8476, 8480, 9000, 9002, 9014, 9016, 9042, 9285, 9289, 9951, 9953, 9970, 9972, 9996, 9998, 10029, 10272, 10276, 10881, 10883, 10895, 10897, 10923, 11185, 11189, 12099, 12101, 12115, 12117, 12138, 12140, 12166, 12411, 12415, 13058, 13060, 13072, 13074, 13100, 13364, 13368, 14316, 14318, 14332, 14334, 14376, 14378, 14404, 14648, 14652, 15286, 15288, 15300, 15302, 15328, 15591, 15595, 16534, 16536, 16550, 16552, 16573, 16575, 16610, 16983, 16991, 16992, 17029, 17240, 17244, 17384, 17386, 17415, 17622, 17626, 17670, 17672, 17701, 17915, 17919, 18139, 18141, 18180, 18495, 18499, 19105, 19107, 19138, 19453, 19457, 20420, 20422, 20442, 20444 |
| docs/adr/ADR-0090-governed-offline-field-proof-exclusive-capability-composition.md<br>`e1c26d2f202684d5ace54408c83a0fcf100085864270f0c32cb077b9398566a9` | B INTERNAL/PROTECTED normative classification; no actual data payload | 47, 93, 129, 144 |
| docs/evidence/PACKAGE-0090-BINDING-AUTHORITY-INTEGRITY.json<br>`5c0f957f9682f744e1f88a4c4cef0f479a8909bea8f28c343ccdc1e679e54001` | D HISTORICAL EVIDENCE ONLY | 57601, 268580, 268662, 268756, 268758, 269934×3, 269963×6, 270061×7, 270075×9, 270089×7, 270103×9, 270117×7, 270131×9, 270145×7, 270159×9, 270173×4, 270187×5, 270201×5, 270215×5, 270229×5, 270243×7, 327841, 538820, 538902, 538996, 538998, 540174×3, 540203×6, 540301×7, 540315×9, 540329×7, 540343×9, 540357×7, 540371×9, 540385×7, 540399×9, 540413×4, 540427×5, 540441×5, 540455×5, 540469×5, 540483×7 |
| docs/evidence/PACKAGE-0090-BINDING-PROVISIONING-MATRIX.json<br>`8be5d6141b6cfa459137e778362be4161a9f6b440ea07981aca3c24a812eed5a` | D HISTORICAL EVIDENCE ONLY | 8404, 8542, 8664, 8928, 9159, 9241, 9335, 9337 |
| docs/evidence/PACKAGE-0090-CURRENT-INDEPENDENT-SOURCE-REVIEW.json<br>`631b68e8c483ab283c4caa11b96bd6ceac60f3226c6af9bac14d68e564699d36` | D HISTORICAL EVIDENCE ONLY | 768, 814, 1012, 1058, 1271, 1317, 1503, 1549, 1753, 1799, 1989, 2035, 2244, 2290, 2480, 2526, 2730, 2772, 2974, 3028, 3232, 3290, 3482, 3536, 3756, 3806, 4072, 4122, 4479, 5776, 5971, 6181, 6364, 6565, 6752, 6958, 7145, 7346, 7545, 7746, 7935, 8152, 8415 |
| docs/evidence/PACKAGE-0090-DEPLOYMENT-INCARNATION-APPROVAL-MATRIX.json<br>`ca5550e9273c95b5d91ad9c33e6c8bedd0771135e7f16a2303c76de72d67e1da` | D HISTORICAL EVIDENCE ONLY | 59329, 270308, 270390, 270484, 270486, 271662×3, 271691×6, 271789×7, 271803×9, 271817×7, 271831×9, 271845×7, 271859×9, 271873×7, 271887×9, 271901×4, 271915×5, 271929×5, 271943×5, 271957×5, 271971×7, 329569, 540548, 540630, 540724, 540726, 541902×3, 541931×6, 542029×7, 542043×9, 542057×7, 542071×9, 542085×7, 542099×9, 542113×7, 542127×9, 542141×4, 542155×5, 542169×5, 542183×5, 542197×5, 542211×7 |
| docs/evidence/PACKAGE-0090-FULL-TESTS.txt<br>`9d4996a557ba6cbabc5a1e90a6e70e596d48c19170b039c680d74a207aabdbc0` | D HISTORICAL EVIDENCE ONLY | 254, 255 |
| docs/evidence/PACKAGE-0090-G3F-3B-S01-TARGET-CLOSURE.json<br>`3778f846c1e0a0baa700f231e4627601c635fbcce42d6105349f83d27d77e0d6` | D HISTORICAL EVIDENCE ONLY | 3640, 3646, 4780, 5290, 6394, 9834, 9840, 10974, 11484, 12588 |
| docs/evidence/PACKAGE-0090-G3F-4-08006-DIAGNOSTICS.json<br>`448b0e84a53763f843fc73f68c6a07446a06d77ea215f5fdc73d964d6db5d18e` | D HISTORICAL EVIDENCE ONLY | 57609, 322974, 588339, 859153, 1124519 |
| docs/evidence/PACKAGE-0090-G3F-4-AMBIGUOUS-COMMIT-RECOVERY.json<br>`f22949d33e9daab11765e30f8b3da47be6e874c68f6f3e52e44f81cc367d5743` | D HISTORICAL EVIDENCE ONLY; C FORBIDDEN old Q12/snapshot declaration | 449, 459, 859×2 |
| docs/evidence/PACKAGE-0090-G3F-4-BINDING-DEPENDENCY-GRAPH.json<br>`da505a68c1bfd9099d01308a0dd7ed27797017efc9e8cf089521331138c3df85` | D HISTORICAL EVIDENCE ONLY | 3275, 3357, 3451, 3453, 4652×3, 4681×6, 4779×7, 4793×9, 4807×7, 4821×9, 4835×7, 4849×9, 4863×7, 4877×9, 4891×4, 4905×5, 4919×5, 4933×5, 4947×5, 4961×7 |
| docs/evidence/PACKAGE-0090-G3F-4-BINDING-PLAN-AUTHORITY-CLOSURE.md<br>`e8e1b23236f32116c7c1d3ad9c59160b9fff370c852a60594003dfcfaf979af9` | D HISTORICAL EVIDENCE ONLY | 117 |
| docs/evidence/PACKAGE-0090-G3F-4-BINDING-PLAN-REGISTRATION-INPUT-CLOSURE.md<br>`44e07adf21d4cc9cb823079acef3aa4f9724e4e07da19a823ce902c825f21db9` | D HISTORICAL EVIDENCE ONLY | 11 |
| docs/evidence/PACKAGE-0090-G3F-4-CANONICAL-SOURCE-COMMITTER-RUNTIME.json<br>`4b8dffa159baf07506b98645b1b60343768f52aa81278b106d39424ec0f6841e` | D HISTORICAL EVIDENCE ONLY | 57717, 323082, 534063, 534145, 534239, 534241, 535417×3, 535446×6, 535544×7, 535558×9, 535572×7, 535586×9, 535600×7, 535614×9, 535628×7, 535642×9, 535656×4, 535670×5, 535684×5, 535698×5, 535712×5, 535726×7, 538897, 538979, 539073, 539075, 540251×3, 540280×6, 540378×7, 540392×9, 540406×7, 540420×9, 540434×7, 540448×9, 540462×7, 540476×9, 540490×4, 540504×5, 540518×5, 540532×5, 540546×5, 540560×7 |
| docs/evidence/PACKAGE-0090-G3F-4-COMMAND-AUTHORITY-INPUT-GRAPH.json<br>`6b17cdd3fc575037bbbeef70756bd09f8fcbbf13f9fd7a71b5d200f7c00dbf8b` | D HISTORICAL EVIDENCE ONLY | 141 |
| docs/evidence/PACKAGE-0090-G3F-4-FINAL-ATOMIC-CEREMONY-GRAPH.json<br>`70a7e45bd3e3a03e022b692178386615cd3f36b5489b372bac086a33ea56d467` | D HISTORICAL EVIDENCE ONLY | 57981, 268960, 269042, 269136, 269138, 270314×3, 270343×6, 270441×7, 270455×9, 270469×7, 270483×9, 270497×7, 270511×9, 270525×7, 270539×9, 270553×4, 270567×5, 270581×5, 270595×5, 270609×5, 270623×7, 328620, 539599, 539681, 539775, 539777, 540953×3, 540982×6, 541080×7, 541094×9, 541108×7, 541122×9, 541136×7, 541150×9, 541164×7, 541178×9, 541192×4, 541206×5, 541220×5, 541234×5, 541248×5, 541262×7 |
| docs/evidence/PACKAGE-0090-G3F-4-INSTALLED-ACL.json<br>`709ff68e0b56cf0b48817de326656ae07ddcc25d8b46d4eb8c1f83518a65b662` | D HISTORICAL EVIDENCE ONLY | 5722, 5729, 5736, 5743, 5750 |
| docs/evidence/PACKAGE-0090-G3F-4-INSTALLED-CATALOG.json<br>`fc1fbd866c984e76da3d7c7c256894de7f8b94898130e11f10b78976d048b715` | D HISTORICAL EVIDENCE ONLY | 70, 102, 133, 164, 195, 228, 259, 290, 321, 351, 382, 415, 618, 648, 707, 1517, 1578, 1580 |
| docs/evidence/PACKAGE-0090-G3F-4-PLAN-IDENTITY-ALLOCATION-CONTRACT.json<br>`c7bbbef6a549dcff8a003569b7ef4ea681af3ab222304ee93f541557d7e8685f` | D HISTORICAL EVIDENCE ONLY | 121 |
| docs/evidence/PACKAGE-0090-G3F-4-REHEARSAL-BINDING-PROVISIONING.json<br>`75abf244535a33e2fd35a7ef373659f146dafc07fa7274bb2d78bc2170e1ad55` | D HISTORICAL EVIDENCE ONLY | 59314, 270293, 270375, 270469, 270471, 271647×3, 271676×6, 271774×7, 271788×9, 271802×7, 271816×9, 271830×7, 271844×9, 271858×7, 271872×9, 271886×4, 271900×5, 271914×5, 271928×5, 271942×5, 271956×7, 329554, 540533, 540615, 540709, 540711, 541887×3, 541916×6, 542014×7, 542028×9, 542042×7, 542056×9, 542070×7, 542084×9, 542098×7, 542112×9, 542126×4, 542140×5, 542154×5, 542168×5, 542182×5, 542196×7 |
| docs/evidence/PACKAGE-0090-G3F-4-RUNTIME-TESTS.json<br>`1da479d9bca30260552346f20daa7a215b71423faa5ba2c86bf184e54a6372d0` | D HISTORICAL EVIDENCE ONLY | 786, 861, 936, 1011, 1086, 1161, 1236, 1311, 1381, 1456, 1541, 1631, 1716, 1796 |
| docs/evidence/PACKAGE-0090-G3F-4-TIMING-PHASES.json<br>`934a01c237140e781e98aba0bea205f8902bbda6b0bea49453dbb8ca6a1b575a` | D HISTORICAL EVIDENCE ONLY | 88246, 353612, 1273622 |
| docs/evidence/PACKAGE-0090-H02-FULL-OFFLINE-TESTS.txt<br>`80a16772cbd0fd245d4ed63403f08dd698e6039cb81a5374d5e75f3705750242` | D HISTORICAL EVIDENCE ONLY | 527, 529 |
| docs/evidence/PACKAGE-0090-H02-INDEPENDENT-SQL-REVIEW.json<br>`39a891e38abe205f46c8fa7418277d1e1042c87de27d2cc2d11f7bca0479f981` | D HISTORICAL EVIDENCE ONLY | 768, 814, 1012, 1058, 1271, 1317, 1503, 1549, 1753, 1799, 1989, 2035, 2244, 2290, 2480, 2526, 2730, 2772, 2974, 3028, 3232, 3290, 3482, 3536, 3756, 3806, 4072, 4122, 4479, 5776, 5971, 6181, 6364, 6565, 6752, 6958, 7145, 7346, 7545, 7746, 7935, 8152, 8415 |
| docs/evidence/PACKAGE-0090-INDEPENDENT-SOURCE-REVIEW.json<br>`29ae7bd4a7590e83b332829135f910fccda52e8990c23eca2cc17e2ed7f9dd52` | D HISTORICAL EVIDENCE ONLY | 768, 814, 1012, 1058, 1271, 1317, 1503, 1549, 1753, 1799, 1989, 2035, 2244, 2291, 2334, 2376, 2578, 2632, 2836, 2894, 3086, 3140, 3360, 3410, 3676, 3726, 4083, 5380, 5575, 5785, 5968, 6169, 6356, 6562, 6748, 6948, 7147, 7348, 7537, 7754, 8017 |
| docs/evidence/PACKAGE-0090-PHASE-A-FULL-TESTS.txt<br>`88ec2118db9feea0ff9163a9448e897271a343b0ac451a3dc6ee99881132875c` | D HISTORICAL EVIDENCE ONLY | 147×2 |
| docs/specifications/SPEC-0090-governed-offline-field-proof-exclusive-capability-composition.md<br>`d12acc86cbed8d56cd774f427b79dce26258a36ac65a7d78bf2cb1fb37fd9a92` | B INTERNAL/PROTECTED normative classification; no actual data payload | 9, 62, 153, 264, 282×2, 324, 332, 340, 348, 356, 364, 372, 380, 388, 396, 404, 412, 420, 428, 518, 747, 760, 882, 972, 988×2, 1636, 1646, 1656, 1666, 1668, 1669, 1670, 1671, 1672, 1673, 1674, 1675, 1676, 1977 |
| docs/evidence/PACKAGE-0090-G3F-4-FINAL-CEREMONY-TIME-CONTRACT-CLOSURE.md<br>`4bafa0b9575ce6342b909c719acaa50a06df92cd916a8fa4059166145f70085f` | D HISTORICAL EVIDENCE ONLY | 7×3, 25, 26, 166 |

Encoded archived source locations (classification D):

```json
[
  {
    "path": "docs/evidence/PACKAGE-0090-BINDING-AUTHORITY-INTEGRITY.json",
    "json_path": "/lossless_raw_record/data",
    "encoding": "gzip",
    "classification": "D HISTORICAL EVIDENCE ONLY; embedded source/fixture, not authority"
  },
  {
    "path": "docs/evidence/PACKAGE-0090-DEPLOYMENT-INCARNATION-APPROVAL-MATRIX.json",
    "json_path": "/authority_integrity/lossless_raw_capture/data",
    "encoding": "gzip",
    "classification": "D HISTORICAL EVIDENCE ONLY; embedded source/fixture, not authority"
  },
  {
    "path": "docs/evidence/PACKAGE-0090-ENROLLMENT-ENTRYPOINT-READONLY-SNAPSHOT.json",
    "json_path": "/raw_record/data",
    "encoding": "gzip",
    "classification": "D HISTORICAL EVIDENCE ONLY; embedded source/fixture, not authority"
  },
  {
    "path": "docs/evidence/PACKAGE-0090-G3F-4-BINDING-REGISTRATION-ID-LINEAGE.json",
    "json_path": "/read_only_capture_record/payload",
    "encoding": "gzip",
    "classification": "D HISTORICAL EVIDENCE ONLY; embedded source/fixture, not authority"
  },
  {
    "path": "docs/evidence/PACKAGE-0090-G3F-4-CANONICAL-SOURCE-COMMITTER-RUNTIME.json",
    "json_path": "/review_bundle_gzip_base64",
    "encoding": "gzip",
    "classification": "D HISTORICAL EVIDENCE ONLY; embedded source/fixture, not authority"
  },
  {
    "path": "docs/evidence/PACKAGE-0090-G3F-4-DATA-SCOPE-INTEGRITY.json",
    "json_path": "/capture_record/payload",
    "encoding": "gzip",
    "classification": "D HISTORICAL EVIDENCE ONLY; embedded source/fixture, not authority"
  },
  {
    "path": "docs/evidence/PACKAGE-0090-G3F-4-EVIDENCE-BINDING-REPRODUCIBILITY.json",
    "json_path": "/lossless_readonly_record/payload",
    "encoding": "gzip",
    "classification": "D HISTORICAL EVIDENCE ONLY; embedded source/fixture, not authority"
  },
  {
    "path": "docs/evidence/PACKAGE-0090-G3F-4-IDENTITY-SIGNAL-RUNTIME.json",
    "json_path": "/raw_record/data",
    "encoding": "gzip",
    "classification": "D HISTORICAL EVIDENCE ONLY; embedded source/fixture, not authority"
  },
  {
    "path": "docs/evidence/PACKAGE-0090-G3F-4-ORIGINAL-ATTESTATION-CONTEXT-MATRIX.json",
    "json_path": "/domain_snapshot/payload",
    "encoding": "gzip",
    "classification": "D HISTORICAL EVIDENCE ONLY; embedded source/fixture, not authority"
  },
  {
    "path": "docs/evidence/PACKAGE-0090-G3F-4-REHEARSAL-BINDING-PROVISIONING.json",
    "json_path": "/authority/lossless_pre_capture/data",
    "encoding": "gzip",
    "classification": "D HISTORICAL EVIDENCE ONLY; embedded source/fixture, not authority"
  },
  {
    "path": "docs/evidence/PACKAGE-0090-G3F-4-REHEARSAL-BINDING-PROVISIONING.json",
    "json_path": "/authority/lossless_post_capture/data",
    "encoding": "gzip",
    "classification": "D HISTORICAL EVIDENCE ONLY; embedded source/fixture, not authority"
  },
  {
    "path": "docs/evidence/PACKAGE-0090-G3F-4-SIGNER-AUTHORITY-REGISTRATION.json",
    "json_path": "/snapshots/raw_record/payload",
    "encoding": "gzip",
    "classification": "D HISTORICAL EVIDENCE ONLY; embedded source/fixture, not authority"
  },
  {
    "path": "docs/evidence/PACKAGE-0090-G3F-4-SIGNER-KEY-AUTHORITY-MATRIX.json",
    "json_path": "/governance_snapshot/payload",
    "encoding": "gzip",
    "classification": "D HISTORICAL EVIDENCE ONLY; embedded source/fixture, not authority"
  },
  {
    "path": "docs/evidence/PACKAGE-0090-G3F-4-WATCHDOG-AUTHORITY-REVIEW.json",
    "json_path": "/authority_and_cleanup_record_gzip_base64/data",
    "encoding": "gzip",
    "classification": "D HISTORICAL EVIDENCE ONLY; embedded source/fixture, not authority"
  },
  {
    "path": "docs/evidence/PACKAGE-0090-G3F-4-WATCHDOG-VISIBILITY.json",
    "json_path": "/authority_and_cleanup_record_gzip_base64/data",
    "encoding": "gzip",
    "classification": "D HISTORICAL EVIDENCE ONLY; embedded source/fixture, not authority"
  },
  {
    "path": "docs/evidence/PACKAGE-0090-SELF-ENROLLED-ANCHOR-RUNTIME.json",
    "json_path": "/record/data",
    "encoding": "gzip",
    "classification": "D HISTORICAL EVIDENCE ONLY; embedded source/fixture, not authority"
  }
]
```

Direct classification of the corrected snapshot: all26 queries are C sanctioned non-secret scalar/contract-public fields; no A/B value crosses the snapshot. Superseded Q12 is C forbidden in historical D. Production private reads/stored digest remain B; supplied secret/proof custody remains A. E unknown nested/renamed/opaque/derived inputs are denied, never silently labeled C. A public false/presence/equality result of a private proof check is also forbidden here; public lifecycle existence is separately permitted.

## Equivalent-name and protected-container occurrence inventory

Expanded scan covers every occurrence of the named protected proof/verifier/key and execution-record container terms plus proof-hash parameter expressions. The same classification rule applies to all occurrences on each listed physical line: historical files D; SQL internal custody B; Kotlin protected parameter/custody/test handling A. Public safe members of an internal execution record (state/identity/deadlines) and existing explicitly specified composite public receipt commitments are C only at their sanctioned output boundary, independently enumerated in the source-flow review above. Their container being B does not make every safe member secret; no protected member is exported. Names in normative text describe B boundaries rather than data. This inventory supplements the literal ledger; opaque future preimages E are forbidden public export, not declared safe by field name.

| File / SHA256 | Container occurrence class | Every matching line (multiplicity) |
| --- | --- | --- | --- |
| applications/command-authority-ceremony/src/main/kotlin/io/flooow/ceremony/GovernedCall.kt<br>`265c6e426610817466943ae7340bc3a5482a0b8dd212ff0f3026fdb4a182bcdc` | A PRIVATE/AUTHORIZED | 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20×2, 21, 22, 36, 38 |
| applications/command-authority-ceremony/src/main/kotlin/io/flooow/ceremony/GovernedJdbc.kt<br>`6274b34f8884632503e3b5796d143c06fdaa02a5d8154d9c00173cbb18194017` | A PRIVATE/AUTHORIZED | 52×2 |
| applications/command-authority-ceremony/src/main/kotlin/io/flooow/ceremony/GovernedOfflineFieldProofLauncher.kt<br>`4f0732c34e883aa84e88ce220b874479c856e4320c32bbca6e01ac161f92676f` | A PRIVATE/AUTHORIZED | 86, 89, 99, 102 |
| applications/command-authority-ceremony/src/main/kotlin/io/flooow/ceremony/PostgresOfflineFieldProofSupport.kt<br>`c4c0744379576f1f88e8b64ab10970e94b52d1760211c011030ea5b32eebd988` | A PRIVATE/AUTHORIZED | 360 |
| applications/command-authority-ceremony/src/test/kotlin/io/flooow/ceremony/CommandAuthorityCeremonyPostgresTest.kt<br>`714f99ae7642c1bed203e4bf3fde4142a9cdf8b07fec7c9f8eeba20d54f94631` | A PRIVATE/AUTHORIZED | 38 |
| applications/command-authority-ceremony/src/test/kotlin/io/flooow/ceremony/GovernedAdaptersTest.kt<br>`46623a6c36ee24186df8b5ee94896223f4ad7be2b201007653f7f839e1dd3f73` | A PRIVATE/AUTHORIZED | 225, 249 |
| applications/marketplace-operations-persistence-postgres/src/main/kotlin/io/flooow/marketplace/persistence/postgres/PostgresCommandAuthorization.kt<br>`0aef146a943ac0b77054751f65ceb05d35d87316232aadce71017c83c647dabe` | A PRIVATE/AUTHORIZED | 35 |
| applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V034__create_command_authorization.sql<br>`8745476ccc76d6d0b9b100489f317f6cead44afd0072998401d94c3b595bc5d9` | B INTERNAL/PROTECTED | 26×2 |
| applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V042__create_s2a_attestation_consumption_and_attested_command_authority.sql<br>`3bfc5f7c95d235235ff8444453523a6a757980b464bff60ad5150e622d2f1ae1` | B INTERNAL/PROTECTED | 145, 153, 374, 417, 430×2, 465, 542, 885, 928×2, 950, 970, 1043, 1045, 1046 |
| applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V043__create_governed_offline_field_proof_capability_composition.sql<br>`3301b254e883ae2ebf9e1d41036f15bc7839c1ae9e2404e692bc2ec864204109` | B INTERNAL/PROTECTED | 644, 665, 945, 946, 954×3, 957, 1169, 1973, 3029, 3059, 3089, 3119, 3124, 3127, 3130, 3133, 3136, 3139, 3142, 3145, 3148, 3836, 4031, 4263, 4273, 4454×2, 4457×2, 4458×3, 4473, 4474, 4497, 4706, 5008, 5013×2, 5065, 5506, 5739, 5740, 5794, 5929, 6014, 6052, 6136, 6321, 6551, 6562, 6671, 7286, 7651, 7656×2, 7657×2, 7671, 7672, 7678, 7681×2, 7685, 7687, 7693×4, 8242, 8254, 8310, 8476×2, 8479×2, 8480×3, 8492, 8493, 8498×8, 9000×2, 9002×9, 9009, 9014×2, 9016×9, 9023, 9042, 9054, 9119, 9285×2, 9288×2, 9289×3, 9301, 9302, 9307×8, 9951×2, 9953×9, 9960, 9970×2, 9972×9, 9979, 9996×2, 9998×9, 10005, 10029, 10040, 10103, 10272×2, 10275×2, 10276×3, 10288, 10289, 10294×8, 10881×2, 10883×9, 10890, 10895×2, 10897×9, 10904, 10923, 10934, 11016, 11185×2, 11188×2, 11189×3, 11201, 11202, 11207×8, 12099×2, 12101×9, 12108, 12115×2, 12117×9, 12124, 12138×2, 12140×9, 12147, 12166, 12177, 12206, 12242, 12411×2, 12414×2, 12415×3, 12427, 12428, 12433×8, 12679, 13054, 13058×2, 13060×9, 13067, 13072×2, 13074×9, 13081, 13100, 13111, 13140, 13195, 13364×2, 13367×2, 13368×3, 13380, 13381, 13386×8, 13632, 14312, 14316×2, 14318×9, 14325, 14328, 14332×2, 14334×9, 14341, 14376×2, 14378×9, 14385, 14404, 14415, 14479, 14648×2, 14651×2, 14652×3, 14664, 14665, 14670×8, 15286×2, 15288×9, 15295, 15300×2, 15302×9, 15309, 15328, 15339, 15422, 15591×2, 15594×2, 15595×3, 15607, 15608, 15613×8, 16534×2, 16536×9, 16543, 16550×2, 16552×9, 16559, 16573×2, 16575×9, 16582, 16610, 16621, 16646, 16983, 16984, 16991×2, 16992×5, 17005, 17009×2, 17029, 17042, 17067, 17240×2, 17243×2, 17244×3, 17256, 17257, 17262×8, 17378, 17384×2, 17386×9, 17393, 17415, 17429, 17454, 17622×2, 17625×2, 17626×3, 17638, 17639, 17644×8, 17670×2, 17672×9, 17679, 17701, 17704, 17714, 17739, 17915×2, 17918×2, 17919×3, 17931, 17932, 17937×8, 18106, 18118×2, 18133, 18136, 18139×2, 18141×9, 18148, 18151, 18180, 18192, 18217, 18495×2, 18498×2, 18499×3, 18511, 18512, 18517×8, 18846, 18963, 19105×2, 19107×9, 19114, 19117, 19138, 19150, 19175, 19453×2, 19456×2, 19457×3, 19469, 19470, 19475×8, 20179, 20296, 20420×2, 20422×9, 20429, 20432, 20442×2, 20444×9, 20451, 20454, 20469 |
| docs/adr/ADR-0090-governed-offline-field-proof-exclusive-capability-composition.md<br>`e1c26d2f202684d5ace54408c83a0fcf100085864270f0c32cb077b9398566a9` | B INTERNAL/PROTECTED | 47, 67, 93, 129, 144 |
| docs/evidence/PACKAGE-0090-BINDING-AUTHORITY-INTEGRITY.json<br>`5c0f957f9682f744e1f88a4c4cef0f479a8909bea8f28c343ccdc1e679e54001` | D HISTORICAL EVIDENCE ONLY | 54905, 57601, 58718, 58726, 268580, 268662, 268756, 268758, 269122, 269130, 269148×3, 269156, 269178, 269180, 269934×12, 269948, 269963×16, 270019×17, 270061×44, 270075×56, 270089×44, 270103×56, 270117×47, 270131×60, 270145×44, 270159×56, 270173×15, 270187×33, 270201×32, 270215×39, 270229×35, 270243×49, 325145, 327841, 328958, 328966, 538820, 538902, 538996, 538998, 539362, 539370, 539388×3, 539396, 539418, 539420, 540174×12, 540188, 540203×16, 540259×17, 540301×44, 540315×56, 540329×44, 540343×56, 540357×47, 540371×60, 540385×44, 540399×56, 540413×15, 540427×33, 540441×32, 540455×39, 540469×35, 540483×49, 541869 |
| docs/evidence/PACKAGE-0090-BINDING-PROVISIONING-MATRIX.json<br>`8be5d6141b6cfa459137e778362be4161a9f6b440ea07981aca3c24a812eed5a` | D HISTORICAL EVIDENCE ONLY | 8404, 8542, 8664, 8928, 9159, 9241, 9335, 9337, 9909, 9979, 10025, 10109, 10117, 10135×3, 10143, 10165, 10167 |
| docs/evidence/PACKAGE-0090-CURRENT-INDEPENDENT-SOURCE-REVIEW.json<br>`631b68e8c483ab283c4caa11b96bd6ceac60f3226c6af9bac14d68e564699d36` | D HISTORICAL EVIDENCE ONLY | 768, 814, 1012, 1058, 1271, 1317, 1503, 1549, 1753, 1799, 1989, 2035, 2244, 2290, 2480, 2526, 2730, 2772, 2974, 3028, 3232, 3290, 3482, 3494, 3536, 3548, 3756, 3806, 4072, 4122, 4479, 5776, 5971, 6181, 6364, 6565, 6752, 6958, 7145, 7346, 7545, 7746, 7935, 7947, 8152, 8415, 10600, 10714, 11101, 11291, 14729, 14730, 14964, 14965, 15199, 15200 |
| docs/evidence/PACKAGE-0090-DEPLOYMENT-INCARNATION-APPROVAL-MATRIX.json<br>`ca5550e9273c95b5d91ad9c33e6c8bedd0771135e7f16a2303c76de72d67e1da` | D HISTORICAL EVIDENCE ONLY | 56633, 59329, 60446, 60454, 270308, 270390, 270484, 270486, 270850, 270858, 270876×3, 270884, 270906, 270908, 271662×12, 271676, 271691×16, 271747×17, 271789×44, 271803×56, 271817×44, 271831×56, 271845×47, 271859×60, 271873×44, 271887×56, 271901×15, 271915×33, 271929×32, 271943×39, 271957×35, 271971×49, 326873, 329569, 330686, 330694, 540548, 540630, 540724, 540726, 541090, 541098, 541116×3, 541124, 541146, 541148, 541902×12, 541916, 541931×16, 541987×17, 542029×44, 542043×56, 542057×44, 542071×56, 542085×47, 542099×60, 542113×44, 542127×56, 542141×15, 542155×33, 542169×32, 542183×39, 542197×35, 542211×49, 543453 |
| docs/evidence/PACKAGE-0090-FULL-TESTS.txt<br>`9d4996a557ba6cbabc5a1e90a6e70e596d48c19170b039c680d74a207aabdbc0` | D HISTORICAL EVIDENCE ONLY | 254, 255 |
| docs/evidence/PACKAGE-0090-G3F-3B-S01-TARGET-CLOSURE.json<br>`3778f846c1e0a0baa700f231e4627601c635fbcce42d6105349f83d27d77e0d6` | D HISTORICAL EVIDENCE ONLY | 2242, 3640, 3646, 3970, 4780, 5290, 5890, 6394, 8436, 9834, 9840, 10164, 10974, 11484, 12084, 12588 |
| docs/evidence/PACKAGE-0090-G3F-4-08006-DIAGNOSTICS.json<br>`448b0e84a53763f843fc73f68c6a07446a06d77ea215f5fdc73d964d6db5d18e` | D HISTORICAL EVIDENCE ONLY | 54913, 57609, 58726, 58734, 320278, 322974, 324091, 324099, 585643, 588339, 589456, 589464, 856457, 859153, 860270, 860278, 1121823, 1124519, 1125636, 1125644 |
| docs/evidence/PACKAGE-0090-G3F-4-AMBIGUOUS-COMMIT-RECOVERY.json<br>`f22949d33e9daab11765e30f8b3da47be6e874c68f6f3e52e44f81cc367d5743` | D HISTORICAL EVIDENCE ONLY | 378, 385, 391, 449, 459, 613, 859×3 |
| docs/evidence/PACKAGE-0090-G3F-4-BINDING-DEPENDENCY-GRAPH.json<br>`da505a68c1bfd9099d01308a0dd7ed27797017efc9e8cf089521331138c3df85` | D HISTORICAL EVIDENCE ONLY | 464, 465, 3275, 3357, 3451, 3453, 3817, 3825, 3843×3, 3851, 3873, 3875, 4652×12, 4666, 4681×16, 4737×17, 4779×44, 4793×56, 4807×44, 4821×56, 4835×47, 4849×60, 4863×44, 4877×56, 4891×15, 4905×33, 4919×32, 4933×39, 4947×35, 4961×49 |
| docs/evidence/PACKAGE-0090-G3F-4-BINDING-PLAN-AUTHORITY-CLOSURE.md<br>`e8e1b23236f32116c7c1d3ad9c59160b9fff370c852a60594003dfcfaf979af9` | D HISTORICAL EVIDENCE ONLY | 117 |
| docs/evidence/PACKAGE-0090-G3F-4-BINDING-PLAN-REGISTRATION-INPUT-CLOSURE.md<br>`44e07adf21d4cc9cb823079acef3aa4f9724e4e07da19a823ce902c825f21db9` | D HISTORICAL EVIDENCE ONLY | 11 |
| docs/evidence/PACKAGE-0090-G3F-4-CANONICAL-SOURCE-COMMITTER-RUNTIME.json<br>`4b8dffa159baf07506b98645b1b60343768f52aa81278b106d39424ec0f6841e` | D HISTORICAL EVIDENCE ONLY | 55021, 57717, 58834, 58842, 320386, 323082, 324199, 324207, 534063, 534145, 534239, 534241, 534605, 534613, 534631×3, 534639, 534661, 534663, 535417×12, 535431, 535446×16, 535502×17, 535544×44, 535558×56, 535572×44, 535586×56, 535600×47, 535614×60, 535628×44, 535642×56, 535656×15, 535670×33, 535684×32, 535698×39, 535712×35, 535726×49, 538897, 538979, 539073, 539075, 539439, 539447, 539465×3, 539473, 539495, 539497, 540251×12, 540265, 540280×16, 540336×17, 540378×44, 540392×56, 540406×44, 540420×56, 540434×47, 540448×60, 540462×44, 540476×56, 540490×15, 540504×33, 540518×32, 540532×39, 540546×35, 540560×49, 541977×2, 542016×6, 542046×8, 543501×2, 543540×6, 543570×8, 543724, 543769 |
| docs/evidence/PACKAGE-0090-G3F-4-COMMAND-AUTHORITY-INPUT-GRAPH.json<br>`6b17cdd3fc575037bbbeef70756bd09f8fcbbf13f9fd7a71b5d200f7c00dbf8b` | D HISTORICAL EVIDENCE ONLY | 141 |
| docs/evidence/PACKAGE-0090-G3F-4-DATA-SCOPE-INTEGRITY.json<br>`edb846a66415b5861e7ef2e8c0674975b7b836611d8829d8a3d75ac20cb6b042` | D HISTORICAL EVIDENCE ONLY | 20, 1512 |
| docs/evidence/PACKAGE-0090-G3F-4-FINAL-ATOMIC-CEREMONY-GRAPH.json<br>`70a7e45bd3e3a03e022b692178386615cd3f36b5489b372bac086a33ea56d467` | D HISTORICAL EVIDENCE ONLY | 55285, 57981, 59098, 59106, 268960, 269042, 269136, 269138, 269502, 269510, 269528×3, 269536, 269558, 269560, 270314×12, 270328, 270343×16, 270399×17, 270441×44, 270455×56, 270469×44, 270483×56, 270497×47, 270511×60, 270525×44, 270539×56, 270553×15, 270567×33, 270581×32, 270595×39, 270609×35, 270623×49, 325924, 328620, 329737, 329745, 539599, 539681, 539775, 539777, 540141, 540149, 540167×3, 540175, 540197, 540199, 540953×12, 540967, 540982×16, 541038×17, 541080×44, 541094×56, 541108×44, 541122×56, 541136×47, 541150×60, 541164×44, 541178×56, 541192×15, 541206×33, 541220×32, 541234×39, 541248×35, 541262×49 |
| docs/evidence/PACKAGE-0090-G3F-4-INSTALLED-ACL.json<br>`709ff68e0b56cf0b48817de326656ae07ddcc25d8b46d4eb8c1f83518a65b662` | D HISTORICAL EVIDENCE ONLY | 1837, 1844, 4861, 5722, 5729, 5736, 5743, 5750 |
| docs/evidence/PACKAGE-0090-G3F-4-INSTALLED-CATALOG.json<br>`fc1fbd866c984e76da3d7c7c256894de7f8b94898130e11f10b78976d048b715` | D HISTORICAL EVIDENCE ONLY | 70, 102, 133, 164, 195, 198, 228, 259, 290, 321, 351, 382, 415, 618, 648, 707, 1517, 1578, 1580, 2119×3, 2126, 2159, 2161 |
| docs/evidence/PACKAGE-0090-G3F-4-ORIGINAL-ATTESTATION-CONTEXT-MATRIX.json<br>`dc31510de3abc5271292e370e6dc5ed5e243cb47c9f97fa649300e1564f09e42` | D HISTORICAL EVIDENCE ONLY | 2372, 2375 |
| docs/evidence/PACKAGE-0090-G3F-4-PLAN-IDENTITY-ALLOCATION-CONTRACT.json<br>`c7bbbef6a549dcff8a003569b7ef4ea681af3ab222304ee93f541557d7e8685f` | D HISTORICAL EVIDENCE ONLY | 121 |
| docs/evidence/PACKAGE-0090-G3F-4-PREREQUISITE-PROVISIONING-MATRIX.json<br>`aa16c0678b3162692b2e81cead6d9e01f7dfa191cbd9d487b8f89384b7edbd0a` | D HISTORICAL EVIDENCE ONLY | 54 |
| docs/evidence/PACKAGE-0090-G3F-4-REHEARSAL-BINDING-PROVISIONING.json<br>`75abf244535a33e2fd35a7ef373659f146dafc07fa7274bb2d78bc2170e1ad55` | D HISTORICAL EVIDENCE ONLY | 1476×3, 1484, 1506, 1508, 56618, 59314, 60431, 60439, 270293, 270375, 270469, 270471, 270835, 270843, 270861×3, 270869, 270891, 270893, 271647×12, 271661, 271676×16, 271732×17, 271774×44, 271788×56, 271802×44, 271816×56, 271830×47, 271844×60, 271858×44, 271872×56, 271886×15, 271900×33, 271914×32, 271928×39, 271942×35, 271956×49, 326858, 329554, 330671, 330679, 540533, 540615, 540709, 540711, 541075, 541083, 541101×3, 541109, 541131, 541133, 541887×12, 541901, 541916×16, 541972×17, 542014×44, 542028×56, 542042×44, 542056×56, 542070×47, 542084×60, 542098×44, 542112×56, 542126×15, 542140×33, 542154×32, 542168×39, 542182×35, 542196×49, 542266, 542311 |
| docs/evidence/PACKAGE-0090-G3F-4-RUNTIME-TESTS.json<br>`1da479d9bca30260552346f20daa7a215b71423faa5ba2c86bf184e54a6372d0` | D HISTORICAL EVIDENCE ONLY | 786, 861, 936, 1011, 1086, 1161, 1236, 1311, 1381, 1456, 1541, 1631, 1646, 1716, 1796 |
| docs/evidence/PACKAGE-0090-G3F-4-SIGNER-AUTHORITY-REGISTRATION.json<br>`9ceca53f1a099da6d68c0d8254e5add03674c8fe299d434819bca8ecdb8e7f19` | D HISTORICAL EVIDENCE ONLY | 563 |
| docs/evidence/PACKAGE-0090-G3F-4-SIGNER-KEY-AUTHORITY-MATRIX.json<br>`609b6b69b8fd68c1fc7eb8ecb6fe3408adbb126c99fde68868c9db8a845f8b5b` | D HISTORICAL EVIDENCE ONLY | 199 |
| docs/evidence/PACKAGE-0090-G3F-4-SIGNING-CEREMONY-RESIDUE-SCAN.json<br>`fa6cc39d260037383bc207d2e980659fc0a8ed7aebe340db821b0931c0afc10e` | D HISTORICAL EVIDENCE ONLY | 568 |
| docs/evidence/PACKAGE-0090-G3F-4-TIMING-PHASES.json<br>`934a01c237140e781e98aba0bea205f8902bbda6b0bea49453dbb8ca6a1b575a` | D HISTORICAL EVIDENCE ONLY | 85550, 88246, 89363, 89371, 350916, 353612, 354729, 354737, 1270926, 1273622, 1274739, 1274747 |
| docs/evidence/PACKAGE-0090-G3F-4-WATCHDOG-AUTHORITY-REVIEW.json<br>`b5165e1199147939336654739261389a47e96a42d6385eb8598cefe5be5a2baa` | D HISTORICAL EVIDENCE ONLY | 437 |
| docs/evidence/PACKAGE-0090-H02-FULL-OFFLINE-TESTS.txt<br>`80a16772cbd0fd245d4ed63403f08dd698e6039cb81a5374d5e75f3705750242` | D HISTORICAL EVIDENCE ONLY | 527, 529 |
| docs/evidence/PACKAGE-0090-H02-INDEPENDENT-SQL-REVIEW.json<br>`39a891e38abe205f46c8fa7418277d1e1042c87de27d2cc2d11f7bca0479f981` | D HISTORICAL EVIDENCE ONLY | 768, 814, 1012, 1058, 1271, 1317, 1503, 1549, 1753, 1799, 1989, 2035, 2244, 2290, 2480, 2526, 2730, 2772, 2974, 3028, 3232, 3290, 3482, 3494, 3536, 3548, 3756, 3806, 4072, 4122, 4479, 5776, 5971, 6181, 6364, 6565, 6752, 6958, 7145, 7346, 7545, 7746, 7935, 7947, 8152, 8415, 10600, 10714, 11101, 11291, 14729, 14730, 14964, 14965, 15199, 15200 |
| docs/evidence/PACKAGE-0090-INDEPENDENT-G3F-3B-SECURITY-REVIEW.md<br>`f8d16c117da7e217c8bbf6f7a9e73ad585f55535a2ddecbe93df26c78a9a7429` | D HISTORICAL EVIDENCE ONLY | 73 |
| docs/evidence/PACKAGE-0090-INDEPENDENT-SOURCE-REVIEW.json<br>`29ae7bd4a7590e83b332829135f910fccda52e8990c23eca2cc17e2ed7f9dd52` | D HISTORICAL EVIDENCE ONLY | 768, 814, 1012, 1058, 1271, 1317, 1503, 1549, 1753, 1799, 1989, 2035, 2244, 2291, 2334, 2376, 2578, 2632, 2836, 2894, 3086, 3098, 3140, 3360, 3410, 3676, 3726, 4083, 5380, 5575, 5785, 5968, 6169, 6356, 6562, 6748, 6948, 7147, 7348, 7537, 7754, 8017, 10202, 10316, 10703, 10893, 14331, 14332, 14566, 14567, 14801, 14802 |
| docs/evidence/PACKAGE-0090-LOGIN-EVENT-BINDING-RUNTIME.json<br>`b7767cc2139c4b6b2cdb87252a3ae61ff21bbbfbec416d7c124fa62daa569c1f` | D HISTORICAL EVIDENCE ONLY | 85, 130 |
| docs/evidence/PACKAGE-0090-PHASE-A-FULL-TESTS.txt<br>`88ec2118db9feea0ff9163a9448e897271a343b0ac451a3dc6ee99881132875c` | D HISTORICAL EVIDENCE ONLY | 147×2 |
| docs/specifications/SPEC-0090-governed-offline-field-proof-exclusive-capability-composition.md<br>`d12acc86cbed8d56cd774f427b79dce26258a36ac65a7d78bf2cb1fb37fd9a92` | B INTERNAL/PROTECTED | 9, 62, 153, 161, 249, 264, 282×2, 324, 332, 340, 348, 356, 364, 372, 380, 388, 396, 404, 412×2, 420, 428, 464, 470, 518, 620, 622×3, 747, 754×2, 760, 772, 773, 784, 797×2, 882, 972, 976, 988×2, 1009, 1283, 1636, 1646, 1656, 1666, 1668, 1669, 1670, 1671, 1672, 1673, 1674, 1675, 1676, 1912, 1977, 2124 |
| docs/evidence/PACKAGE-0090-G3F-4-FINAL-CEREMONY-TIME-CONTRACT-CLOSURE.md<br>`4bafa0b9575ce6342b909c719acaa50a06df92cd916a8fa4059166145f70085f` | D HISTORICAL EVIDENCE ONLY | 7×3, 25, 26, 166 |

## Scope, validations and remaining risk

TC-R01 closes HIGH by design evidence, not severity downgrade or claim of executed remediation. CURRENT_GATE_FINDINGS=B0/H0/M0/L0. AGGREGATE_G3F_4_FINDINGS=B0/H2/M0/L0: watchdog deployment and G3F4-H01 remain HIGH/OPEN; G3F_4_STATUS=HOLD, Room/runtime proof incomplete. No other finding is closed. The selected future recovery composer/serializer must implement this allowlist/provenance boundary before execution; historical raw snapshot templates must not be used. Runtime safety/clock continuity/window feasibility are not certified. V043 execution fence is retained.

Final authorized scope is exactly two new tracked evidence documents: this remediation and the preserved temporal report. Historical JSON, SPEC/ADR, production, migrations, credentials, permissions and runtime remain unchanged. Database mutation, key generation, private-key persistence, signature creation, identifier generation, new authority, watchdog change and H01 change all NO. Existing plaintext credential files were not created/read. Container not started; no fixtures installed.

Commit convention: one coherent docs(package-0090) evidence commit, matching prior recovery design closure. The preserved initial time HOLD is explicitly historical; this document supplies current authoritative supersession plus replacement snapshot and independent PASS_UNCHANGED adjudication. Staging/push may occur only after exact two-path audit, all baseline hashes and P01-P18/source/time checks pass. Push only checkpoint/package-0090-cloud-handoff; verify live remote/local equality and clean worktree. This document records precommit validation, not a fictitious self-referential future commit hash; final Git receipt is returned by the agent after verification.

```text
TC_R01_REMEDIATION=PASS
TC_R01_ORIGINAL_SEVERITY=HIGH
TC_R01_FINAL_STATUS=CLOSED
HISTORICAL_ARTIFACT_UNCHANGED=YES
PUBLIC_PROJECTION_POSSESSION_DIGEST=ABSENT
PUBLIC_DERIVED_PROTECTED_MATERIAL=ABSENT
PUBLIC_RECOVERY_SNAPSHOT_SAFE=YES
QUERY_FIRST_RECOVERY_PRESERVED=YES
RECOVERY_DETERMINISM=YES_DESIGN
TIME_CONTRACT_REVALIDATION=PASS_UNCHANGED
G3F_4_FINAL_CEREMONY_TIME_CONTRACT_CLOSURE=PASS_DESIGN_PENDING_FINAL_GIT_VERIFICATION
WATCHDOG_STATUS=OPEN
H01_STATUS=OPEN
G3F_4_STATUS=HOLD
REMEDIATION_BLOCKER_COUNT=0
REMEDIATION_HIGH_COUNT=0
REMEDIATION_MEDIUM_COUNT=0
REMEDIATION_LOW_COUNT=0
AGGREGATE_G3F_4_BLOCKER_COUNT=0
AGGREGATE_G3F_4_HIGH_COUNT=2
AGGREGATE_G3F_4_MEDIUM_COUNT=0
AGGREGATE_G3F_4_LOW_COUNT=0
DATABASE_MUTATION=NO
KEY_GENERATION=NO
PRIVATE_KEY_PERSISTENCE=NO
SIGNATURE_CREATION=NO
IDENTIFIER_GENERATION=NO
NEW_AUTHORITY=NO
NEXT_GATE=G3F_4_FINAL_CEREMONY_SIGNING_WINDOW_CONTRACT_REVIEW
NEXT_GATE_STARTED=NO
```

Post-construction independent verification: reread both complete documents and re-extracted the two SQL blocks; all26 templates match the replacement contract exactly. The full historical JSON tree has four possession_digest-named ACL maps (column metadata, not material) and no stored possession-value members. Synthetic lower/upper endpoint, signed-i64 round-trip and half-open expiry checks pass; current canonical source still signs two manifest endpoints via the original digest preimage and requires six-fraction canonical round-trip. Original temporal and all1255 tracked byte hashes remain equal to pre-remediation values. No database-state equality is inferred from historical data or from absence of SQL execution.
