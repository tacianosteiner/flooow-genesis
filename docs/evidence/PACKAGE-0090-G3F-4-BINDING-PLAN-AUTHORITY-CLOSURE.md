# Package0090 G3F.4 — Binding plan authority closure

Bounded gate PASS. Existing PLAN_BINDING_ADMIN is sufficient to attribute and reserve the exact planned identities. No new authority, database object, credential, coordinator, signing/binding permission or actual identifier is created. Overall G3F.4 remains HOLD before signing.

All six prior HOLD artifacts were read and preserved. Their exact13 open fields are ten identity/allocation fields plus issued_at, valid_from and expires_at. The ten close here through one FINAL_CEREMONY_IDENTITY_ALLOCATION event under the existing trusted admin; times, crash recovery and60-second feasibility are deliberately left to their own gates. The complete updated40-field matrix is inside the authority matrix:21 preexisting, four derived,12 final-ceremony generated, three still open;37 closed contracts. No physical identity or fingerprint value is required to close a fixed future generation contract.

Authority is derived from SPEC0090 sections1/2/4, ADR0090 Immutable Plan Binding, the legacy pre-effect recovery-plan constructor and this explicitly scoped authority-closure request. A UUID remains identity only. The event reserves independent once-only OS-CSPRNG UUIDv4 identities for binding/plan/run, principal/credential/grant/decision and three operations, validates distinctness/collisions and binds one independently approved scope before any future effects. A collision denies the entire allocation; no automatic field replacement. The existing nonsecret ceremony plan/input context suffices; no extra table/receipt authority or run coordinator is introduced. Crash custody mechanics are not solved or claimed here.

Binding_id identifies one permanent plan registration within one deployment/incarnation and exact organization/target/slots. It is not a server attempt_id: existing governed generations can change later without rebinding. plan_id is the independent immutable SPEC0090 plan identity, not a member of OfflineFieldProofExecutionPlan. run_id is its planned field-proof recovery run. Legacy VERSION=1 and constructor equality are production source facts. The legacy nine-member ID digest remains forbidden as the38-tag binding fingerprint. No silently mapping adapter is added.

Principal, command credential and grant IDs are only reservations, not authority rows/secrets. Operations remain PRINCIPAL, INITIAL_CREDENTIAL and GRANT canonical V042 idempotency lineages. Their existing (organization_id,operation_id) key, advisory lock, exact intent/receipt rederivation and durable effect/consumption joins discriminate retry from conflict. Decision identity is reserved only after governing plan authority exists; it may precede later command grant/admission effects and never substitutes for their authority. No decision ID or row is created now.

Fingerprint encoding is exact SPEC0090 BINDING/V1 over38 canonical tags, excluding itself, mutable state and secrets. Retained manifest bytes are committed by existing digest/hash tags. Independent pure reference decode/reencode of three previously committed TEST vectors matched their bytes/digests; same input stayed equal and all38 byte perturbations per vector changed digest. These are design codec checks, not physical rehearsal fingerprints, source acceptance, runtime parity or signing. SHA256 collision resistance remains the cryptographic assumption.

Replay rules preserve an exact known logical allocation, classify durable/ambiguous outcomes QUERY-FIRST and deny blind write/regeneration. A new attributable preparation uses a whole fresh set after the prior root is proven abandoned/closed; an operational attempt generation change is separate. A duplicate registration is not an upsert and cannot grant replay mutation. Identity continuity never renews an expired signature/window or restores a retired key. Six cases are covered without adding crash cleanup machinery.

The necessity filter retains only authority boundary, replay safety, idempotency, collision safety and causal ordering; unjustified new mechanisms=0. No container start, PostgreSQL connection, timing benchmark, login/watchdog work, key/UUID generation, signature, signer governance, V043 prerequisite/header, command effect, migration/fence or temporal mutation occurred this gate. Prior runtime findings are carried as historical evidence, not represented as fresh inspection.

Exactly four new artifacts plus the six preserved authorized artifacts are validated for checkpoint commit. Old evidence stays temporally attributable: this new contract supersedes its ten plan-family gaps only. Worktree hashes and Git-normalized blob hashes are explicitly distinguished for prior Windows CRLF files; normal Git line-ending normalization does not change their JSON/document content.

Next gate is G3F_4_FINAL_CEREMONY_RECOVERY_CLOSURE because orphan/crash recovery remains open (request section19). The final time contract and60-second feasibility remain additional pre-signing prerequisites; no signing execution is authorized by this PASS. Watchdog/H01 remain OPEN, B0/H2/M0/L0.

Evidence:

- [PACKAGE-0090-G3F-4-BINDING-PLAN-AUTHORITY-MATRIX.json](PACKAGE-0090-G3F-4-BINDING-PLAN-AUTHORITY-MATRIX.json)
- [PACKAGE-0090-G3F-4-PLAN-IDENTITY-ALLOCATION-CONTRACT.json](PACKAGE-0090-G3F-4-PLAN-IDENTITY-ALLOCATION-CONTRACT.json)
- [PACKAGE-0090-G3F-4-PLAN-REPLAY-IDEMPOTENCY-MATRIX.json](PACKAGE-0090-G3F-4-PLAN-REPLAY-IDEMPOTENCY-MATRIX.json)

RETURN (validated precommit baseline; final response reports actual post-push/fetch commit/clean status):

```json
{
  "UNRESOLVED_INPUT_COUNT": 13,
  "UNRESOLVED_INPUT_NAMES": [
    "binding_id",
    "run_id",
    "plan_id",
    "principal_id",
    "credential_id",
    "grant_id",
    "decision_id",
    "principal_operation_id",
    "credential_operation_id",
    "grant_operation_id",
    "issued_at",
    "valid_from",
    "expires_at"
  ],
  "PLAN_AUTHORITY_OPEN_COUNT": 10,
  "PLAN_AUTHORITY_OPEN_FIELDS": [
    "binding_id",
    "run_id",
    "plan_id",
    "principal_id",
    "credential_id",
    "grant_id",
    "decision_id",
    "principal_operation_id",
    "credential_operation_id",
    "grant_operation_id"
  ],
  "BINDING_PLAN_AUTHORITY": "PLAN_BINDING_ADMIN_EXISTING_TRUSTED_REVIEWED_ADMIN",
  "BINDING_PLAN_CREATION_EVENT": "FINAL_CEREMONY_IDENTITY_ALLOCATION",
  "BINDING_PLAN_SCOPE": "ONE_IMMUTABLE_SPEC0090_PLAN_BINDING_PER_DEPLOYMENT_INCARNATION_EXACT_TARGET_AND_SLOTS",
  "BINDING_PLAN_REPLAY_SEMANTICS": "Same frozen allocation/context and exact semantic request is a logical retry. Changed immutable context, a proven closed/abandoned root followed by newly authorized preparation, or a different plan_id is a new logical allocation/ceremony. An operational generation change alone is not a new binding or plan. Unknown lineage denies both mutation and regeneration.",
  "BINDING_PLAN_AUTHORITY_CLOSED": "YES",
  "PLAN_ID_SEMANTICS": "Identity of the independent complete SPEC0090 immutable registration plan, unique together with deployment incarnation. Not a member of the legacy plan.",
  "PLAN_ID_GENERATION_EVENT": "FINAL_CEREMONY_IDENTITY_ALLOCATION",
  "PLAN_ID_AUTHORITY": "PLAN_BINDING_ADMIN",
  "PLAN_ID_RETRY_RULE": "REUSE_EXACT_ATTRIBUTED_ALLOCATION;QUERY_FIRST_IF_DURABLE_OR_AMBIGUOUS;NO_REBIND",
  "PLAN_ID_CONTRACT_CLOSED": "YES",
  "EXECUTION_PLAN_VERSION": 1,
  "EXECUTION_PLAN_VERSION_SOURCE": "applications/command-authority-ceremony/src/main/kotlin/io/flooow/ceremony/OfflineFieldProofExecutionPlan.kt::VERSION=1;init_version_equality",
  "PLAN_FINGERPRINT_DOMAIN_SEPARATOR": "FLOOOW/OFFLINE-FIELD-PROOF/BINDING/V1",
  "PLAN_FINGERPRINT_FIELDS": [
    "binding_schema_version",
    "binding_id",
    "deployment_id",
    "deployment_incarnation_id",
    "run_id",
    "plan_id",
    "execution_plan_version",
    "organization_id",
    "manifest_id",
    "manifest_digest",
    "canonical_manifest_hash",
    "canonical_manifest_encoding_version",
    "mercado_livre_connection_id",
    "omie_connection_id",
    "marketplace_order_id",
    "source_order_reference",
    "integration_reference",
    "permission",
    "reason",
    "provenance",
    "principal_id",
    "credential_id",
    "grant_id",
    "decision_id",
    "correlation_id",
    "principal_operation_id",
    "credential_operation_id",
    "grant_operation_id",
    "issued_at",
    "valid_from",
    "expires_at",
    "identity_slots",
    "offline_surface_version",
    "deadline_policy_version",
    "deadline_policy_digest",
    "admission_contract_version",
    "delivery_contract_version",
    "reconciliation_contract_version"
  ],
  "PLAN_FINGERPRINT_CODEC": "u32be(domain UTF8 length)||domain||u16be(38)||ascending field u16be(tag)||u32be(payload length)||payload; present01||canonical bytes, null00 (all header inputs required nonnull)",
  "PLAN_FINGERPRINT_REPRODUCIBLE": "YES_DESIGN",
  "RUN_ID_SEMANTICS": "One planned field-proof run/recovery identity carried by the legacy execution plan into the binding scope; not deployment, binding generation, server attempt, launcher instance or execution possession identity.",
  "RUN_ID_GENERATION_EVENT": "FINAL_CEREMONY_IDENTITY_ALLOCATION",
  "RUN_ID_AUTHORITY": "PLAN_BINDING_ADMIN",
  "RUN_ID_REUSE_ALLOWED": "EXACT_SAME_LOGICAL_ALLOCATION_ONLY;NOT_NEW_BINDING_REBIND",
  "RUN_ID_CONTRACT_CLOSED": "YES",
  "BINDING_ID_SEMANTICS": "One permanent registration of one complete plan to one deployment/incarnation, organization, exact target, signed input and four permanent login slots. Not one server attempt: the same binding can have governed higher-generation attempts without changing binding/plan/run IDs.",
  "BINDING_ID_GENERATION_EVENT": "FINAL_CEREMONY_IDENTITY_ALLOCATION",
  "BINDING_ID_AUTHORITY": "PLAN_BINDING_ADMIN",
  "BINDING_ID_REPLAY_RULE": "IMMUTABLE_ONE_REGISTRATION;QUERY_FIRST;PLAIN_INSERT_DUPLICATE_DENIES;NO_UPSERT",
  "BINDING_ID_CONTRACT_CLOSED": "YES",
  "PRINCIPAL_OPERATION_ID_STATUS": "CLOSED_FINAL_CEREMONY_GENERATED",
  "CREDENTIAL_OPERATION_ID_STATUS": "CLOSED_FINAL_CEREMONY_GENERATED",
  "GRANT_OPERATION_ID_STATUS": "CLOSED_FINAL_CEREMONY_GENERATED",
  "DECISION_ID_STATUS": "CLOSED_FINAL_CEREMONY_GENERATED_IDENTITY_ONLY",
  "CANONICAL_IDENTITY_ALLOCATION_EVENT": "FINAL_CEREMONY_IDENTITY_ALLOCATION",
  "CANONICAL_IDENTITY_ALLOCATION_AUTHORITY": "PLAN_BINDING_ADMIN",
  "PLAN_IDENTITY_REPLAY_MATRIX": "PASS_DESIGN",
  "PLAN_IDEMPOTENCY_KEY": "(deployment_incarnation_id,plan_id)",
  "CEREMONY_ATTEMPT_IDENTITY": "Existing final ceremony accepted allocation context identified by (incarnation,plan_id,run_id,binding_id) and exact allocated ID set/immutable approved scope. No extra ceremony-attempt UUID/table.",
  "RETRY_CLASSIFICATION_RULE": "Same frozen allocation/context and exact semantic request is a logical retry. Changed immutable context, a proven closed/abandoned root followed by newly authorized preparation, or a different plan_id is a new logical allocation/ceremony. An operational generation change alone is not a new binding or plan. Unknown lineage denies both mutation and regeneration.",
  "PLAN_IDEMPOTENCY_CLOSED": "YES",
  "NEW_DATABASE_AUTHORITY_REQUIRED": "NO",
  "NEW_SERVICE_AUTHORITY_REQUIRED": "NO",
  "NEW_DOMAIN_AUTHORITY_REQUIRED": "NO",
  "NEW_PLAN_AUTHORITY_REQUIRED": "NO",
  "NO_NEW_AUTHORITY_REQUIRED": "YES",
  "UNJUSTIFIED_NEW_MECHANISM_COUNT": 0,
  "HEADER_CLOSED_AFTER_PLAN_GATE": 37,
  "HEADER_STILL_OPEN_COUNT": 3,
  "HEADER_STILL_OPEN_FIELDS": [
    "issued_at",
    "valid_from",
    "expires_at"
  ],
  "IDENTITY_NOT_AUTHORITY": "PASS",
  "PLAN_NOT_EXECUTION": "PASS",
  "PLAN_NOT_SIGNATURE": "PASS",
  "PLAN_TYPE_SEPARATION": "PASS",
  "REPLAY_RULE_EXPLICIT": "PASS",
  "IDEMPOTENCY_EXPLICIT": "PASS",
  "NO_SILENT_UUID_AUTHORITY": "PASS",
  "NO_UNJUSTIFIED_NEW_AUTHORITY": "PASS",
  "NO_UNJUSTIFIED_NEW_MECHANISM": "PASS",
  "NO_SIGNATURE_BEFORE_CONSUMABLE_TRANSACTION": "PASS",
  "DNA_REVIEW": "PASS",
  "WATCHDOG_DEPLOYMENT_HIGH": "OPEN",
  "G3F4_H01": "OPEN",
  "BLOCKER_COUNT": 0,
  "HIGH_COUNT": 2,
  "MEDIUM_COUNT": 0,
  "LOW_COUNT": 0,
  "LOCAL_HEAD": "ab0549dfaa891b67905e307a3c049301fad48f3b",
  "REMOTE_HEAD": "ab0549dfaa891b67905e307a3c049301fad48f3b",
  "LOCAL_EQUALS_REMOTE": "YES_PRECOMMIT_BASELINE",
  "WORKTREE": "VALIDATED_AUTHORIZED_DIRTY10_PRECOMMIT",
  "NEXT_GATE": "G3F_4_FINAL_CEREMONY_RECOVERY_CLOSURE",
  "PLAN_AUTHORITY_OPEN_COUNT_AFTER": 0,
  "PLAN_FINGERPRINT_HASH": "SHA256",
  "PLAN_FINGERPRINT_GENERATION_EVENT": "Once complete authorized allocation + actual manifest bytes + header times and exact policy/slots exist, compute during final ceremony before complete header registration. May compute before signature because signature is not an input; no hash is physically required now.",
  "EXECUTION_PLAN_VERSION_CLOSED": "YES",
  "DECISION_ID_CREATED_BEFORE_AUTHORITY": "NO",
  "UUID_VALUES_CREATED": 0,
  "SIGNING_CEREMONY_SAFE_TO_EXECUTE": "NO",
  "G3F_4": "HOLD"
}
```
