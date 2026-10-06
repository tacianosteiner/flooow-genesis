# Package0090 G3F.4 — canonical binding prerequisite scope

**HOLD: complete canonically sourced registration input is absent.** The graph and existing ADMIN data paths are resolved; the conditional authorization also requires every prerequisite identity to be canonically sourced. That last predicate is false. No SQL data, key material or signature was created. Host approval does not supply domain manifest/plan authority.

The frozen approved deployment/incarnation and artifact SHA remain unchanged. The existing negative timing pair stays historical only. All32 previously authorized dirty files retain their exact bytes; six requested evidence files are added. No commit/push is permitted under this HOLD.

The [dependency graph](PACKAGE-0090-G3F-4-BINDING-DEPENDENCY-GRAPH.json) captures all15 control relations, all19 FKs, every installed CHECK/PK/UNIQUE/NOT NULL, triggers, existing semantic functions and the three additional indexes in canonical source. It distinguishes native SQL edges from ADMIN semantic lineage obligations. The minimum FK-valid graph adds four rows: readiness, preflight key, header and expected original. The canonical REGISTERED state also initializes five layers required by SPEC0090 section2: lifecycle, pointer, delivery, reconciliation and ceremony result. Thus minimum canonical additions are **nine SQL rows**, with **four embedded identity slots** and zero separate slot rows. The existing fixture-1 policy requires no new row. Attempts, executions, admissions, stage receipts and diagnostic evidence are not prerequisites to an inactive registration.

Readiness can legally start NOT_READY/watchdog_healthy=false. A fresh per-incarnation HMAC preflight key is actual32-byte material, not metadata only and not an Ed25519 domain signing key. Existing SPEC22.3 already governs trusted ADMIN/CSPRNG provision, lineage, private fingerprint/no-reuse and version bounds; no new key authority is necessary. Material has not been generated because the whole execution predicate is not satisfied. Historical key/readiness cannot be reused; readiness history/ACL bytes must come from canonical observed evidence, never the old x01 placeholders.

The original is an independently supplied SignedApprovalAttestation. Its canonical manifest22fields and signature preimage bind domain approval, algorithm, signer key identity/fingerprint and manifest digest. The signature does not directly include host/deployment/incarnation/database, runtime role allocation, deadline policy or preflight HMAC material. The expected commitment additionally binds that exact original to binding_id. Therefore a new host incarnation alone does **not** prove a new domain signature is required. Neither exact reuse nor mandatory fresh signing can be proven without the complete proposed domain input. The requested binary reuse verdict is intentionally left UNDETERMINED_EXACT_CONTEXT_MISSING: choosing either option now would infer identity or authority without evidence. Reuse of the historical fixture for this gate is denied; a new expected commitment row is required regardless of signature reuse. No attestation was fabricated and no signing ceremony was executed.

The [40-field input matrix](PACKAGE-0090-G3F-4-BINDING-HEADER-INPUT-MATRIX.json) identifies38 framed tags plus retained canonical_manifest_bytes and plan_fingerprint. The host pair, role allocation, fixture-1 and fixed codec contracts have independent sources. A matching approved complete original manifest, immutable execution plan, binding/plan registration identities and binding issuance instant remain unresolved. Historical S02 A/B originals are actual signed test fixtures; complete codec VECTOR1/2/3 are explicitly unsigned. Combining those distinct inputs, extending a signed window, copying test IDs or deriving values from the proposed header is not allowed. Evidence nulls in the matrix describe absent inputs; they are not insert values.

The [provisioning matrix](PACKAGE-0090-G3F-4-PREREQUISITE-PROVISIONING-MATRIX.json) records categories, existing authorities and fail-closed initial rows. Correct order follows the real cycles: readiness/key in one deferred-FK ADMIN transaction, header after readiness, expected original after header, then five initial state rows. Header/original both must exist at commit. The positive initial pointer/delivery generation must also be attributable to ADMIN, not a convenient default. Existing registration paths require no new DB role, grant, service capability, SQL function, signing key or approval authority; absence of a supplied domain input is not permission to create one.

All13 [negative-source cases](PACKAGE-0090-G3F-4-PREREQUISITE-NEGATIVE-MATRIX.json) have rejection and rollback designs. PASS_DESIGN is not PASS_RUNTIME. Wrong host/database/allocation or source values may satisfy SQL shapes, so the design explicitly includes independent pre-write checks. Runtime negatives await a valid canonical baseline. No invalid rows were inserted.

The [integrity evidence](PACKAGE-0090-G3F-4-DATA-SCOPE-INTEGRITY.json) preserves lossless read-only tools/snapshots, full historical inventory and hashes. Nonsecret authority, migrations and all15 control relations are equal before/after. Actual additions are zero, so ACTUAL_NEW_ROW_SET does not equal the nine-row minimum: DATA_SCOPE_EXACT is not falsely reported PASS. Secret key bytes, passwords and verifiers were excluded. The disposable container is stopped and temporary plaintext credentials erased.

Branch remains checkpoint/package-0090-cloud-handoff, local/fetched remote401a5e313efbec9a4100af8b6b6e237fffb4ca38. Changed scope is six evidence artifacts only; prior32 preserved, unrelated0. Runtime risks remain H01 and watchdog deployment HIGH OPEN (B0/H2/M0/L0). READY/watchdog/session admission/G3G remain NO. No fixture2, temporal change, fence removal, migration, service authority or signal was performed.

The technically determined next gate is **G3F_4_BINDING_HEADER_INPUT_CONTRACT_CLOSURE**: close attributable canonical original/manifest, plan, registration IDs/issuance/generation and their exact mappings. It must establish current existing domain signer authority without borrowing host approval or creating a signing authority. Only after those inputs are closed may the previously authorized minimal graph be provisioned and the rollback runtime matrix executed; login admission remains a later gate.

## Return

```json
{
  "DEPENDENCY_GRAPH_COMPLETE": "YES",
  "MINIMUM_NEW_ROW_SET": {
    "offline_readiness": 1,
    "offline_preflight_key": 1,
    "offline_expected_signed_attestation": 1,
    "offline_binding_header": 1,
    "offline_binding_lifecycle": 1,
    "offline_attempt_pointer": 1,
    "offline_delivery": 1,
    "offline_reconciliation": 1,
    "offline_ceremony_result": 1,
    "identity_slot_SQL_rows": 0,
    "embedded_identity_slots": 4,
    "offline_deadline_policy": 0,
    "offline_attempt": 0,
    "offline_execution": 0,
    "offline_admission": 0,
    "offline_stage_receipt": 0,
    "offline_diagnostic_evidence": 0
  },
  "READINESS_ROW_REQUIRED": "YES",
  "READINESS_CREATE_PATH": "EXISTING_GOVERNED_PATH_DIRECT_TRUSTED_ADMIN_INSERT",
  "READINESS_INITIAL_STATE_FAIL_CLOSED": "YES",
  "KEY_OBJECT": "public.offline_preflight_key",
  "KEY_PROVISIONING_PATH": "EXISTING_GOVERNED_PATH",
  "KEY_PREREQUISITE_CLOSED": "YES_CONTRACT_ONLY_ROW_NOT_PROVISIONED",
  "ORIGINAL_ATTESTATION_OBJECT": "SignedApprovalAttestation -> public.offline_expected_signed_attestation",
  "ORIGINAL_ATTESTATION_SOURCE": "SAME_INDEPENDENT_ORIGINAL_SPEC0090_AMENDMENT_AND_SPEC0088",
  "ORIGINAL_ATTESTATION_CREATION_PATH": "EXISTING_TRUSTED_ADMIN_ATOMIC_HEADER_THEN_EXPECTED_REGISTRATION",
  "ATTESTATION_REUSE_ALLOWED": "UNDETERMINED_EXACT_CONTEXT_MISSING",
  "ORIGINAL_ATTESTATION_PREREQUISITE_CLOSED": "NO_CANONICAL_INSTANCE",
  "HEADER_REQUIRED_FIELDS": 40,
  "HEADER_COMPLETE_INPUTS_CLOSED": "NO",
  "READINESS_PROVISIONING_PATH": "EXISTING_GOVERNED_PATH",
  "ATTESTATION_PROVISIONING_PATH": "EXISTING_GOVERNED_PATH_REGISTRATION_INPUT_UNRESOLVED",
  "HEADER_PROVISIONING_PATH": "EXISTING_GOVERNED_PATH",
  "SLOT_PROVISIONING_PATH": "EXISTING_GOVERNED_PATH_EMBEDDED_HEADER_BYTES",
  "ALL_REQUIRED_PROVISIONING_PATHS": "EXISTING_GOVERNED_DATA_PATHS; COMPLETE_INDEPENDENT_INPUT_UNRESOLVED",
  "NEW_DATABASE_ROLE_REQUIRED": "NO",
  "NEW_DATABASE_PRIVILEGE_REQUIRED": "NO",
  "NEW_SERVICE_PRIVILEGE_REQUIRED": "NO",
  "NEW_SQL_FUNCTION_REQUIRED": "NO",
  "NEW_SIGNING_KEY_REQUIRED": "NO",
  "NEW_APPROVAL_AUTHORITY_REQUIRED": "NO",
  "ALL_PREREQUISITES_MATCH_APPROVED_DEPLOYMENT": "NOT_PROVEN_COMPLETE_INSTANCE",
  "ALL_PREREQUISITES_MATCH_APPROVED_INCARNATION": "NOT_PROVEN_COMPLETE_INSTANCE",
  "BINDING_HEADER_COUNT": 0,
  "IDENTITY_SLOT_COUNT": 0,
  "EXPECTED_SLOT_COUNT": 4,
  "MISSING_SLOT_COUNT": 4,
  "EXTRA_SLOT_COUNT": 0,
  "HEADER_COMPLETE": "NO",
  "HEADER_CONTEXT_CANONICAL": "NOT_PROVEN",
  "ATTESTATION_CONTEXT_CANONICAL": "NOT_PROVEN",
  "KEY_CONTEXT_CANONICAL": "NOT_PROVISIONED",
  "READINESS_CONTEXT_CANONICAL": "NOT_PROVISIONED",
  "PREREQUISITE_NEGATIVE_MATRIX": "PASS_DESIGN; NOT_RUN_RUNTIME",
  "READINESS_READY": "NO",
  "WATCHDOG_OPERATIONAL": "NO",
  "SESSION_ADMISSION": "NO",
  "G3G_AUTHORIZED": "NO",
  "AUTHORITY_FINGERPRINT_PRE": "d3b57ed08d9ba09f2a3db25219f36f436b6d4d2c5d2f5eccc59ca38ca03ad90b",
  "AUTHORITY_FINGERPRINT_POST": "d3b57ed08d9ba09f2a3db25219f36f436b6d4d2c5d2f5eccc59ca38ca03ad90b",
  "AUTHORITY_STATE_UNCHANGED": "YES",
  "DATA_SCOPE_FINGERPRINT_PRE": "b6797c640d6eb2e699ec31507c3ad1cecbc774310840ea5dce174cfe2984174e",
  "DATA_SCOPE_FINGERPRINT_POST": "b6797c640d6eb2e699ec31507c3ad1cecbc774310840ea5dce174cfe2984174e",
  "ACTUAL_NEW_ROW_SET": {
    "offline_readiness": 0,
    "offline_preflight_key": 0,
    "offline_expected_signed_attestation": 0,
    "offline_binding_header": 0,
    "offline_binding_lifecycle": 0,
    "offline_attempt_pointer": 0,
    "offline_delivery": 0,
    "offline_reconciliation": 0,
    "offline_ceremony_result": 0,
    "identity_slot_SQL_rows": 0,
    "embedded_identity_slots": 0,
    "offline_deadline_policy": 0,
    "offline_attempt": 0,
    "offline_execution": 0,
    "offline_admission": 0,
    "offline_stage_receipt": 0,
    "offline_diagnostic_evidence": 0
  },
  "DATA_SCOPE_EXACT": "NO_MINIMUM_SET_NOT_PROVISIONED; ZERO_WRITES_VERIFIED",
  "CANONICAL_BINDING_PREREQUISITE_SCOPE": "HOLD_COMPLETE_CANONICAL_INPUT_MISSING",
  "WATCHDOG_DEPLOYMENT_HIGH": "OPEN",
  "G3F4_H01": "OPEN",
  "BLOCKER_COUNT": 0,
  "HIGH_COUNT": 2,
  "MEDIUM_COUNT": 0,
  "LOW_COUNT": 0,
  "LOCAL_HEAD": "401a5e313efbec9a4100af8b6b6e237fffb4ca38",
  "REMOTE_HEAD": "401a5e313efbec9a4100af8b6b6e237fffb4ca38",
  "LOCAL_EQUALS_REMOTE": "YES",
  "WORKTREE": "AUTHORIZED_DIRTY_38_FILES_PRIOR32_UNCHANGED_UNRELATED0",
  "NEXT_GATE": "G3F_4_BINDING_HEADER_INPUT_CONTRACT_CLOSURE",
  "PLAINTEXT_CREDENTIAL_FILES_ERASED": "YES",
  "DISPOSABLE_CONTAINER_STOPPED": "YES"
}
```
