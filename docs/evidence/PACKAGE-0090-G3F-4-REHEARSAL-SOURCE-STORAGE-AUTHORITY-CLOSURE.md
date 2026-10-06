# Package 0090 G3F.4 — Rehearsal source storage authority closure

Gate PASS. Existing canonical source committers accepted the exact governed allocation after canonical credential activation. Both bindings and connections were revoked; durable historical evidence remained readable and both new-ingestion attempts were denied. No production/provider authentication occurred.

The signed-manifest input contract is now closed 22/22. Four fields retain their previously reviewed future ceremony generation contracts; no signing key, concrete future window, signature, accepted attestation, expected attestation or V043 header was created. Expected attestation and header remain a same-transaction future design.

Roles, memberships, ownership, ACL/default ACL, functions, policies, migrations and control/signing data are unchanged. The 62 prior artifacts and frozen allocation were preserved byte-identically. New scope: six evidence artifacts; no tracked code or SPEC changes. Source committer guards check ACTIVE organization/connection and nonrevoked binding metadata; they resolve no secret bytes. Real scoped SecretVault objects still existed throughout ingestion.

Exactly two independent 48-byte control secrets were generated with SecureRandom (first byte zero, 376 random bits each), never serialized, never provider-formatted. MemoryVault implements the existing SecretVault interface. Existing AES-GCM protects the nonsecret progress cursor with a domain-derived ephemeral control key; only ciphertext/reference lifecycle metadata persists. Zeroing/close/process exit is best effort, not a complete JVM heap/swap guarantee. Scan boundaries are explicit in the residue artifact. Container stopped and administration startup password file erased.

Canonical paths and snapshots, fresh production source hashes, runnable-context review tooling, SQL-state negative proofs, exact row inventory and independent reconstruction are retained in the linked JSON evidence. Reflective repository composition avoids rerunning a fenced migration convenience factory; no schema mutation. Reflection into the pure Omie semantic producer avoids any provider constructor/HTTP transport; canonical source writes still use production committers. No OS-wide network-deny claim.

Production pre-signature lookup is the frozen V041 function also used by related field-proof binding logic. PostgresOfflineFieldProofSupport final post-effect evidence requires a V042 decision/head and was not invoked or claimed successful. No final command authority/decision was needed or created.

Created rows: 22 (10 durable evidence, 12 control lifecycle, including seven canonical audits); secret material durable count zero. Foreign/cross-bound inputs all denied P0017; immutable DB perturbations denied 23503/P0001 and rolled back. Production JVM bytes and a separate Python reconstruction from the post-revocation DB snapshot match exactly, including independently reconstructed Omie semantic JSON.

Overall isolated field proof remains HOLD: WATCHDOG_DEPLOYMENT_HIGH and G3F4_H01 OPEN, HIGH=2. This bounded source-storage gate is FULL PASS. Next technically determined gate is G3F_4_SIGNING_CEREMONY_INSTANCE_EXECUTION; no key generation is part of this gate.

Evidence:

- [PACKAGE-0090-G3F-4-EPHEMERAL-REHEARSAL-CREDENTIAL-LIFECYCLE.json](PACKAGE-0090-G3F-4-EPHEMERAL-REHEARSAL-CREDENTIAL-LIFECYCLE.json)
- [PACKAGE-0090-G3F-4-CANONICAL-SOURCE-COMMITTER-RUNTIME.json](PACKAGE-0090-G3F-4-CANONICAL-SOURCE-COMMITTER-RUNTIME.json)
- [PACKAGE-0090-G3F-4-EVIDENCE-BINDING-FINGERPRINT-RUNTIME.json](PACKAGE-0090-G3F-4-EVIDENCE-BINDING-FINGERPRINT-RUNTIME.json)
- [PACKAGE-0090-G3F-4-POST-REVOCATION-EVIDENCE-PROOF.json](PACKAGE-0090-G3F-4-POST-REVOCATION-EVIDENCE-PROOF.json)
- [PACKAGE-0090-G3F-4-REHEARSAL-SECRET-RESIDUE-SCAN.json](PACKAGE-0090-G3F-4-REHEARSAL-SECRET-RESIDUE-SCAN.json)

RETURN below records the validated precommit baseline. The authorized checkpoint commit/push/fetch is performed after artifact verification; final response supplies resulting actual Git identity and clean status without self-referential commit hashes.

```json
{
  "SOURCE_COMMIT_REQUIRES_ACTIVE_ORGANIZATION": "YES",
  "SOURCE_COMMIT_REQUIRES_ACTIVE_CONNECTION": "YES",
  "SOURCE_COMMIT_REQUIRES_CURRENT_CREDENTIAL_BINDING": "YES",
  "SOURCE_COMMIT_RESOLVES_SECRET_BYTES_DURING_COMMIT": "NO",
  "SOURCE_STORAGE_AUTHORITY_CLOSED": "YES",
  "ORGANIZATION_CREATE_PATH": "IntegrationControlPlaneService.createOrganization -> PostgresIntegrationControlPlaneRepository.createOrganization",
  "ML_CONNECTION_CREATE_PATH": "IntegrationControlPlaneService.createConnection -> PostgresIntegrationControlPlaneRepository.createConnection",
  "OMIE_CONNECTION_CREATE_PATH": "IntegrationControlPlaneService.createConnection -> PostgresIntegrationControlPlaneRepository.createConnection",
  "ML_CREDENTIAL_BIND_PATH": "IntegrationControlPlaneService.bindInitialCredential -> PostgresIntegrationControlPlaneRepository.bindInitialCredential",
  "OMIE_CREDENTIAL_BIND_PATH": "IntegrationControlPlaneService.bindInitialCredential -> PostgresIntegrationControlPlaneRepository.bindInitialCredential",
  "CONNECTION_ACTIVATION_PATH": "bindInitialCredential: SecretVault.store -> canonical repository binding/version1 + ACTIVE + CONNECTION_ACTIVATED audit in one repository transaction",
  "REHEARSAL_ORGANIZATION_DB_INSTANCE": "PASS",
  "REHEARSAL_CONNECTION_DB_INSTANCES": "PASS",
  "EPHEMERAL_REHEARSAL_CREDENTIAL_BINDINGS": "PASS",
  "PROVIDER_AUTHENTICATION_CAPABILITY": "NO",
  "PROVIDER_CREDENTIAL_PRESENT": "NO",
  "PROVIDER_CALL_COUNT": 0,
  "ML_SOURCE_COMMIT": "PASS",
  "ML_ORDER_IDENTITY_CHAIN": "PASS",
  "OMIE_SOURCE_COMMIT": "PASS",
  "PRODUCTION_EVIDENCE_LOOKUP": "PASS",
  "PRODUCTION_IDENTITY_LOOKUP": "PASS",
  "EVIDENCE_BINDING_FINGERPRINT": "4e78b3ec645685d88325e1ad6ca104bfc6e3698a23d652c2fd07fe3c804b14fb",
  "EVIDENCE_BINDING_FINGERPRINT_REPRODUCIBLE": "YES",
  "EVIDENCE_BINDING_FINGERPRINT_INDEPENDENT_MATCH": "YES",
  "EVIDENCE_BINDING_MUTATION_SENSITIVITY": "PASS",
  "DOMAIN_CROSS_BINDING_NEGATIVE_MATRIX": "PASS",
  "SIGNED_MANIFEST_FIELD_COUNT": 22,
  "SIGNED_MANIFEST_CLOSED_FIELD_COUNT": 22,
  "SIGNED_MANIFEST_OPEN_FIELD_COUNT": 0,
  "SIGNED_MANIFEST_OPEN_FIELDS": [],
  "ML_BINDING_REVOKED": "YES",
  "OMIE_BINDING_REVOKED": "YES",
  "ML_CONNECTION_OPERATIONAL_AFTER_GATE": "NO",
  "OMIE_CONNECTION_OPERATIONAL_AFTER_GATE": "NO",
  "REHEARSAL_SECRET_PERSISTED": "NO",
  "REHEARSAL_SECRET_RESIDUE_SCAN": "PASS",
  "POST_REVOCATION_EVIDENCE_LOOKUP": "PASS",
  "POST_REVOCATION_FINGERPRINT_MATCH": "YES",
  "POST_REVOCATION_NEW_ML_COMMIT": "DENIED",
  "POST_REVOCATION_NEW_OMIE_COMMIT": "DENIED",
  "AUTHORITY_FINGERPRINT_PRE": "d3b57ed08d9ba09f2a3db25219f36f436b6d4d2c5d2f5eccc59ca38ca03ad90b",
  "AUTHORITY_FINGERPRINT_POST": "d3b57ed08d9ba09f2a3db25219f36f436b6d4d2c5d2f5eccc59ca38ca03ad90b",
  "AUTHORITY_STATE_UNCHANGED": "YES",
  "ACTUAL_DOMAIN_ROW_SET": {
    "integration_organization": 1,
    "integration_connection": 2,
    "integration_credential_binding": 2,
    "integration_connector_progress": 2,
    "integration_connector_page_commit": 2,
    "integration_mercado_livre_order_source_observation": 1,
    "integration_mercado_livre_order_item_source_observation": 1,
    "marketplace_order_identity_registry": 1,
    "marketplace_order_occurrence_source_promotion": 1,
    "integration_omie_transaction_evidence": 1,
    "integration_omie_transaction_evidence_v3": 1,
    "integration_control_audit": 7
  },
  "DOMAIN_DATA_SCOPE_EXACT": "YES",
  "FIELD_PROOF_CLASSIFICATION": "REHEARSAL_STRUCTURAL_PROOF_NOT_REAL_FIELD_PROOF",
  "PROVIDER_DATA_ORIGIN": "GOVERNED_REHEARSAL_GENERATED_INPUT",
  "PROVIDER_AUTHENTICATION_OCCURRED": "NO",
  "ATTESTATION_HEADER_TRANSACTION_SCOPE_STILL_CLOSED": "YES",
  "CANONICAL_SOURCE_COMMITTER_PRESERVED": "PASS",
  "CREDENTIAL_FENCE_NOT_BYPASSED": "PASS",
  "REAL_PROVIDER_CREDENTIAL_USED": "NO",
  "EPHEMERAL_REHEARSAL_SECRET_EXPLICIT": "PASS",
  "SECRET_NOT_PERSISTED": "PASS",
  "PROVIDER_NETWORK_ACTIVITY": "NO",
  "REHEARSAL_DATA_NOT_MISREPRESENTED": "PASS",
  "INGESTION_REQUIRES_ACTIVE_BINDING": "PASS",
  "POST_REVOCATION_NEW_INGESTION_DENIED": "PASS",
  "DURABLE_EVIDENCE_SURVIVES_CREDENTIAL_REVOCATION": "PASS",
  "DNA_REVIEW": "PASS",
  "REHEARSAL_DOMAIN_INSTANCE_AUTHORITY_CLOSURE": "PASS",
  "KEY_CEREMONY_AUTHORIZED_TO_START": "YES",
  "WATCHDOG_DEPLOYMENT_HIGH": "OPEN",
  "G3F4_H01": "OPEN",
  "BLOCKER_COUNT": 0,
  "HIGH_COUNT": 2,
  "MEDIUM_COUNT": 0,
  "LOW_COUNT": 0,
  "LOCAL_HEAD": "401a5e313efbec9a4100af8b6b6e237fffb4ca38",
  "REMOTE_HEAD": "401a5e313efbec9a4100af8b6b6e237fffb4ca38",
  "LOCAL_EQUALS_REMOTE": "YES_AT_BASELINE_PRECOMMIT",
  "WORKTREE": "VALIDATED_AUTHORIZED_DIRTY68_PRECOMMIT",
  "NEXT_GATE": "G3F_4_SIGNING_CEREMONY_INSTANCE_EXECUTION",
  "ML_SECRET_REFERENCE_HASH": "af0d3d997e384c248527337410fda69ef8fd5982b52d6c7322e0bcd2ecce8349",
  "OMIE_SECRET_REFERENCE_HASH": "84544cd3af215b8fbcc12588ff433b51f86982638f4634012df8dbf234041151",
  "DOMAIN_DATA_FINGERPRINT_PRE": "3c707fc776bac46af908ffd618d58427e14e04385e312cb10e3103466d368b08",
  "DOMAIN_DATA_FINGERPRINT_POST": "95762df6a553b1e5c29e981795b22a2a3d5bdac81abfbc30775581daa3564b4c",
  "NO_NEW_DB_AUTHORITY": "PASS",
  "NO_G3G": "PASS",
  "PLAINTEXT_CREDENTIAL_FILES_ERASED": "YES"
}
```
