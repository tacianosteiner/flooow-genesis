# ADR-0090 - Governed offline field proof exclusive capability composition

## Status

CONTRACT REVISION 3 CANDIDATE FOR FINAL INDEPENDENT ADVERSARIAL REVIEW. Architectural direction APPROVED_FOR_SPEC; this revision does not claim adversarial approval. IMPLEMENTATION_AUTHORIZED=NO. REAL_FIELD_PROOF=HOLD.

Baseline: main, `77d482c97a663a527dcacc85036c7577dfc92782`. Companion: [SPEC-0090](../specifications/SPEC-0090-governed-offline-field-proof-exclusive-capability-composition.md). Revision3 scope: R2-H01/H02/M01/M02 only; accepted architectural decisions and the18 physical signatures remain preserved. Prior self-review claims are not adversarial approval.

## Context

Prior isolated rehearsal evidence is MIGRATION_CHAIN=PASS, V042=PASS, V042_DEFECT=NO. This documentation revision reruns no migration or database experiment. Existing launcher outcomes and AttestedCeremonyStage remain domain/application vocabulary. New control state supplements them; it never turns historical evidence into current authority.

## Problem

The shared-role composition does not impose a plan-specific database tenant boundary. Revision 0 additionally conflated committed effects with reconciled completion, treated login-based claim replay as execution exclusion, left credential delivery without durable attempt consumption, and left identity, fingerprint, locking and bootstrap mechanisms incomplete.

## Decision

Retain four plan-bound logins, zero memberships, wrapper-only access, immutable binding, no raw service SELECT, no global RLS, frozen V041/V042, two-organization denial and unchanged normal runtime. Introduce orthogonal administrative state, execution-instance fencing, at-most-one delivery attempt, a canonical binding fingerprint, governed deployment reincarnation, a narrow internal principal-lock route, trusted adapter sequencing, explicit bootstrap/compatibility and enforceable deadline policy.

Sixteen public wrapper names remain. `offline_claim_attempt` has three separately typed overloads: acquire attempt/execution, consume delivery-attempt permission, report delivery outcome. Thus the exact public surface has eighteen SQL signatures, not sixteen signatures. This bounded increase resolves F-B02 without an arbitrary operation dispatcher or new authority-producing path. Exact ACLs include each signature individually; no grant by function-name wildcard is permitted.

## Identity Model

Each binding owns distinct VERIFIER, ISSUER, EXECUTOR, AUDITOR LOGIN NOINHERIT identities. All are NOSUPERUSER, NOCREATEROLE, NOCREATEDB, NOREPLICATION, NOBYPASSRLS, zero direct/transitive memberships, no ownership/CREATE/grant options. No membership in shared verifier, issuer, runtime, governance or any owner. New operational access is direct EXECUTE on the assigned slot's exact wrappers only, plus necessary CONNECT/schema USAGE.

Authenticate directly. `session_user` OID/name, immutable slot, deployment incarnation and binding identify the caller; `current_user` inside a definer is not caller identity. Pools are per login/deployment and never reuse sessions across slots. Role rename/recreation fails closed. Prepared statements cache neither binding authority nor execution eligibility.

## Immutable Plan Binding

Header retains binding/run/plan IDs, schema version, deployment and incarnation IDs, canonical manifest/digest, exact organization/connections/order IDs/references/permission/reason/provenance, principal/credential/grant/decision/correlation and three operation IDs, four slot OID/name assignments, validity and policy/surface versions. One plan has one binding within an incarnation; one login has one permanent binding/slot, including tombstones. Never rebind a login or change its organization.

`binding_plan_fingerprint_v1` is a new SHA-256 digest of the fully specified tagged binary encoding in SPEC section 4. It is distinct from existing `OfflineFieldProofExecutionPlan.fingerprint()`. No omitted field, silent normalization or reuse of the old digest is allowed.

Deployment identity stored in a backup is insufficient for clone isolation. Trusted host orchestration keeps clone/restore NOT_READY and inaccessible to operational logins until explicit REINCARNATION rotates the server's incarnation marker, disables restored offline identities and invalidates copied bindings. Incarnation readiness and expected endpoint/incarnation are independent deployment prerequisites. This is an operational boundary against copied deployments, not protection from a hostile host/database administrator.

## Lifecycle

Separate domain-effect projection, binding lifecycle, attempt lifecycle, execution ownership, delivery lifecycle, durable admission/effective validity, reconciliation lifecycle and ceremony result. SPEC section 2 enumerates every legal transition and wrapper eligibility. Unlisted transitions fail closed.

Binding REGISTERED/ACTIVE/REVOKED/EXPIRED governs mutations only. Attempt CLAIMED/EFFECTS_IN_PROGRESS/RECOVERY_REQUIRED/EFFECTS_COMPLETE/ABORTED records progress without claiming reconciliation. Decision APPLY sets EFFECTS_COMPLETE and reconciliation REQUIRED, never ceremony SUCCESS. Reconciliation is read-only at the auditor; its observed IN_PROGRESS/result is local until an administrative recorder persists independently recomputed evidence. Ceremony SUCCESS requires exact reconciliation; FAILURE/MANUAL_REVIEW requires the defined classification. Administrative recording adds no offline mutation entrypoint.

The same bound auditor may inspect/reconcile in every binding/attempt/delivery/reconciliation/result state, including revoked, expired and terminal, provided deployment readiness, authentic immutable identity and policy bounds hold. No special administrative read grant is necessary after expiry/revocation. Read cannot reactivate mutation. Administrative disabling of a login still prevents connection.

## Attempt/Fencing

Separate attempt_id, generation and execution_id. Atomic claim creates one attempt and one active execution for a launcher_instance_id. A client generates a protected 256-bit execution possession secret before claim; only its digest is stored. Claim acknowledgment retry requires that same instance, execution ID and secret. A second process with merely the same login cannot retrieve/reuse ownership. No execution secret appears in outputs/logs; receipt IDs alone grant nothing.

Every mutable wrapper requires the execution proof, matching instance, current attempt/generation, expected slot, canonical binding, deployment readiness and deadlines. Control locks precede domain locks and last until commit. Recovery first drains/cancels prior sessions, marks execution STALE, closes old attempt and advances generation; a newly claimed execution receives the higher generation. Crash/expiry never releases ownership automatically. Trusted adapters do not share or clone execution secrets between process instances.

## Capability Separation

Verifier has two V041 wrappers; issuer six V042 principal/credential/grant wrappers; executor four names including the bounded delivery overloads; auditor four read wrappers. Executor cannot accept evidence, issue authority or govern. Auditor cannot write domain or control state. Pure helpers, row locks and new administrative objects are internal dependencies only.

## Wrapper Owner Model

Four separate wrapper owners are NOLOGIN NOINHERIT NOSUPERUSER NOCREATEROLE NOCREATEDB NOREPLICATION NOBYPASSRLS, zero memberships, owners only of their wrappers, not domain/control tables. A separate administrative owner holds control tables. An additional NOLOGIN narrow lock-capability owner holds only the internal principal-lock function and minimum SELECT/column UPDATE needed for locking the existing principal. P is not a service identity. Revision2 also adds separate restricted readiness owner Q and intent-audit owner Z; neither is an operational identity or merged wrapper-owner class.

Verification/issuance owners receive their exact frozen EXECUTE capabilities, control reads/lock-column UPDATE and enumerated bookkeeping writes for successful stage receipts. Execution owner receives only execution/admission/delivery bookkeeping and internal read/lock capabilities. Audit owner reads scoped columns and complete history. No wrapper owner receives generic domain authority/decision/head DML. Restricted control writes cannot activate/revoke/rebind/advance generation/extend validity. SPEC section22.4 enumerates per-column privilege/control-write traceability;21.7 retains exact frozen EXECUTE signatures and transition constraints.

All wrappers and the three new internal capabilities use qualified objects, SECURITY DEFINER, `search_path=pg_catalog,pg_temp`, no dynamic caller-selected identifiers and no PUBLIC EXECUTE. Creation and removal of default PUBLIC EXECUTE occur in the same future migration transaction. PUBLIC schema CREATE and resolvable schemas must be proven safe before the implementation gate.

## Admission

POSSESSION_AUTHORITY=GUARD_M. Separate ADMISSION_VALIDITY_FOR_AUDIT from POSSESSION_VALIDITY_FOR_MUTATION as specified in SPEC3/21.5/22.4. S02 reports the former through its existing admission_effectively_valid bool using only authorized bound admission/authentication history, currentness/expiry and governed state/revocation observations. It must neither validate nor infer current possession or claim mutation readiness from historical admission alone. Guard M alone validates current possession at each mutable operation, bound to organization, admission where applicable and exact operation context; missing/stale/mismatch fails closed. Historical admission never substitutes for possession. Mutation eligibility remains unresolved by S02 until that operation-time validation; all other mutation guards remain required. No S02 signature change, new possession receipt/subsystem, schema or privilege is authorized.

ADMISSION_DURABLE_OR_TRANSACTION_LOCAL=DURABLE. Reuse credential parsing/verifier derivation. Protected derived proof reaches only restricted authentication; no offline SELECT or return of secret_verifier. Private receipt binds executor login, deployment/incarnation, binding, attempt/generation/execution, exact credential revision, principal/org, grant revision/fingerprint and permission. APPLY revalidates current canonical authority and consumes receipt atomically with decision. Durable admission states ISSUED/CONSUMED are separate from derived expiry/revocation/generation/current-authority validity; invalidity never implies status repair or renewal. UUID/flag alone is never admission.

Authentication writes bookkeeping, not canonical authority. Consumed admission never reactivates. Existing-result replay belongs to auditor read guard; mutating wrappers do not offer a closed-attempt replay bypass. Credentials/proof buffers are destroyed after admission commit and before writer entry.

## Transaction Semantics

BEGIN_JCA_APPLY_ENFORCEMENT=ADAPTER_TRUSTED_SEQUENCE. Retain same JDBC connection and READ COMMITTED transaction for verifier BEGIN/JCA/PERSIST, each issuer BEGIN/JCA/APPLY, and executor prepare/V042-BEGIN/JCA/APPLY. Frozen PERSIST/APPLY reexecute/revalidate snapshots/fingerprints. No new BEGIN provenance row, SQL proof of Ed25519 execution or synthetic trust flag is introduced. A malicious trusted adapter is outside the honest-JCA claim, as in existing V041/V042.

Principal, credential, grant and decision retain independent commits. Credential commit also persists CREATED_NOT_DELIVERABLE and originating execution receipt. Before TTY, a separate short executor control transaction atomically persists DELIVERY_ATTEMPTED with execution ID/time and consumes the single delivery permission. Only an acknowledged commit in that same live execution allows its one TTY call. Lost acknowledgment never retries TTY. PostgreSQL cannot prove human receipt; DELIVERY_ACKNOWLEDGED is operational bookkeeping only. No automatic second credential or delivery after restart/recovery.

Auditor uses READ ONLY REPEATABLE READ, bounded database-clock eligibility and rollback. Administrative recording of reconciliation occurs separately and rechecks exact evidence; audit wrappers never update status.

## Revocation

Revoke takes lifecycle locks conflicting with all effect transactions; operations admitted before that lock may commit first. No retroactive rollback. Emergency revoke requires cancel/drain and inspection. Expiry and execution/admission validity are checked with database wall clock before final effects and after frozen mutation returns; a failed postcondition rolls back tentative effects. Eligibility concerns canonical write time, not later COMMIT visibility; valid admitted effects can become visible after expiry, without authorizing subsequent effects. Trusted deployment watchdog enforces finite transaction/idle bounds across the external JCA gap; caller-configurable session defaults alone are insufficient. No credential TTY interaction occurs while SQL locks are held.

## History

History exposes complete installed_rank/version/type/script/checksum/success metadata under the auditor read guard, never raw SELECT or a version cap. Expected manifest rejects all missing/duplicate/extra/failed/altered/unordered entries. Preserve V001-V042 checksums and append the future migration. Offline rolling upgrade is unsupported; old/new compatibility and deployment order are specified in SPEC sections 14 and 16.

## Tenant Isolation

Session selects immutable binding before domain lookups. Every input/proof/reference is checked against it. Foreign or mixed plan/org values fail uniformly before disclosure/effect. Two-org tests include all four slots, execution ownership/proofs, delivery receipts, admission and generation tuples. Reads after terminal remain limited to the same plan.

## Security Properties

Evidence != authority != execution. Acceptance, consumption, current signer/organization/grant eligibility, canonical fingerprints and evidence/head fences remain frozen domain checks. Administrative state never substitutes for them. Execution possession secret adds process exclusion within the trusted launcher model, not immunity to compromised process memory. Delivery guarantees AT_MOST_ONE_DELIVERY_ATTEMPT, never exactly-once human receipt.

## Rejected Alternatives

| Alternative | Reason |
| --- | --- |
| Runtime membership plus raw grants | Grants exceed exact plan scope. |
| Runtime membership plus HYBRID/RLS | Privileged nested capabilities and unscoped helpers bypass the proposed caller boundary; FORCE RLS cannot constrain superuser/BYPASSRLS. |
| Rebinding a login across organizations | Stale identities acquire changed authority. |
| Raw SELECT plus application filters | Database callers can bypass filters. |
| Shared runtime audit grants | Widens unrelated capabilities. |
| Collapsing BEGIN/JCA/APPLY | Removes independent trusted verification phases. |
| Login-only idempotent claim | Does not exclude a second launcher process. |
| Exactly-once human delivery | SQL cannot establish receipt and crash outcomes. |
| Extra BEGIN provenance rows | Unnecessary for the existing trusted-adapter/revalidation model. |

## Migration Impact

Future forward migration adds control records, sixteen wrapper names/eighteen exact public signatures and the narrow internal principal-lock/readiness/intent-audit capabilities. No V043 is created/reserved here. V001-V042 immutable; existing runtime schema/RLS/roles/function ownership/security unchanged. No corrective old-launcher grants. New objects require an isolated rehearsal and exact ACL review later.

## Provisioning Impact

Distinguish SCHEMA_DEPLOYMENT_ADMIN, SERVICE_IDENTITY_ADMIN, PLAN_BINDING_ADMIN, SECRET_DELIVERY_OPERATOR and OFFLINE_OPERATOR responsibilities. They need not be distinct people absent external governance. SINGLE_ADMIN_CAN_SELF_AUTHORIZE=POSSIBLE_UNLESS_EXTERNAL_GOVERNANCE_SEPARATES_DUTIES. Host/database superuser is outside the operational attacker model and may bypass ACLs or change session authorization. Admin-proxied operational sessions remain forbidden by procedure, not an impossible SQL detection promise.

Provision readiness/incarnation, policy, owners/wrappers, then four new logins/header/ACLs and activate, then matching launcher. No mixed ceremony versions. Secret delivery for service passwords is separate from the command-credential TTY protocol.

## Compatibility

OLD+V042 is legacy outside this package. OLD+NEW fails closed on extra migration/incompatible surface. NEW+V042 fails closed before effects. NEW+NEW requires exact surface/history/binding/policy versions. Normal runtime remains separately compatible; no new offline capability widens its shared roles.

## Non-Goals

No normal runtime redesign/global RLS/shared-role edit/V039-V042 modification/Room writer/provider authority/financial execution/generic admin API/arbitrary SQL audit/destructive automatic recovery. No defense against hostile host/database superuser. This revision changes documentation only.

## Consequences

Additional control storage, execution possession handling, delivery overloads, incarnation procedure and watchdog evidence are necessary costs. Partial domain commits remain possible; credential effects without decision require manual review. Committed decisions permit bound read-only reconciliation even when mutation eligibility is closed.

## Open Implementation Questions

Only representation/work remains open: migration number, approved numeric policy values and watchdog packaging; migration numbering remains unreserved. These cannot change state transitions, guard semantics, canonical bytes, delivery guarantee, bootstrap trust, incarnation procedure or lock ordering. Resolve representation in implementation design and review before code/migration authorization.

## Acceptance Gates

Repeat adversarial review before implementation design. Later gates require exact catalog/PUBLIC/schema proof; canonical acceptance vectors; two-org/process exclusion tests; delivery crash/lost-ack tests; deterministic revoke/recovery/expiry tests; clone/restore NOT_READY proof; complete history compatibility; preserved JCA/lock fences and normal-runtime regression. Documentation completion does not prove implementation, Room readiness or real field readiness.

## Revision 1 finding disposition

| Finding | Contract resolution |
| --- | --- |
| F-B01 | Orthogonal state machines, total read eligibility, administrative reconciliation recording and separate read replay. |
| F-B02 | Instance/execution possession fencing and durable consumption before one TTY attempt. |
| F-H01 | Tagged/versioned binary binding fingerprint and mandatory vectors. |
| F-H02 | Host-gated NOT_READY plus explicit reincarnation invalidating copies. |
| F-H03 | New binding-only internal principal lock and traced lock sequence. |
| F-H04 | Trusted adapter sequence, frozen snapshot revalidation, no new provenance row. |
| F-M01 | Minimal endpoint/incarnation/surface bootstrap, fail closed. |
| F-M02 | Four-cell compatibility matrix, no offline rolling upgrade. |
| F-M03 | Explicit administrative responsibilities and trusted superuser boundary. |
| F-M04 | Approved bounded policy, database time and mandatory external watchdog/barrier tests. |

## Revision 2 bounded closure

Historical Revision2 changed only R1-H01/H02/H03/H04/M01/M02; its self-review claims were independently reviewed and two HIGH/two MEDIUM remained. Revision3 below supersedes the four incomplete representations. [SPEC section21](../specifications/SPEC-0090-governed-offline-field-proof-exclusive-capability-composition.md#21-revision-2-normative-closure) retains the unchanged physical signature/frozen dependency manifest; section22 supersedes reviewed ACL codec, S17/S18 dataflow, HMAC lifecycle and column grants.

| Finding | Revision2 decision |
| --- | --- |
| R1-H01 | Eighteen expanded SQL vectors/sixteen names. Claim arities9/12/13, primitive types, explicit scalar delivery arguments and closed typed bytea tuples enumerating frozen parameters/results. Exact returns/cardinality/ACLs, no defaults/variadic/polymorphism; explicit JDBC casts and pre-effect null rejection. |
| R1-H02 | u32 nested lengths/collection counts, u16 tuple counts/tags, u32 numeric versions; exact slot bytes, microsecond actual/max deadline pairs, six-field full history and complete protected ACL projection. Domain-separated SHA-256 digests and real positive key version/HMAC framing. Complete deterministic fixture semantics and nested-slot golden bytes; generated full hex/digest evidence remains required before implementation freeze. |
| R1-H03 | Q NOLOGIN private readiness capability, EXECUTE only A/E. History/catalog/key internal; claim verifies MAC and current incarnation/surface/history/ACL/binding/slot/policy/watchdog before ownership. No raw service SELECT or E history/key SELECT. |
| R1-H04 | Z NOLOGIN binding-only intent/receipt comparison, EXECUTE only A; minimum credential-verifier SELECT privately, frozen canonical recomputation returns only two booleans. A/service never read stored verifier; existing JCA/evidence/head comparisons remain. |
| R1-M01 | Total ISSUED->CONSUMED lifecycle; effective validity derived, duplicate authentication cannot renew/reactivate; successful decision and consumption atomic. |
| R1-M02 | I1-I17 cross-machine invariants and administrative outcome table; stale/closed ownership, uncertainty and inconsistent effects classified explicitly. Terminal result immutable, later diagnostics separate, no automatic recovery/second delivery. |

Choose separate Q/Z over E raw history/key or A verifier access to reduce private authority in mutation/projected audit owners. These are internal dependencies only: four operational identities,zero memberships,wrapper-only access remain. Q vetted future HMAC dependency has fixed identity and requires isolated dependency approval; nothing installed now. Column/control/EXECUTE inventories and S01-S18 two-org/null/cast/PUBLIC cases are explicit in SPEC. OWNER_TRANSITIVE_AUTHORITY=NOT_PROVEN until independent review and actual implementation evidence.

Self-review claims, not independent approval: R1_H01_RESOLVED=YES;R1_H02_RESOLVED=YES;R1_H03_RESOLVED=YES;R1_H04_RESOLVED=YES;R1_M01_RESOLVED=YES;R1_M02_RESOLVED=YES. PACKAGE_1_FREEZE_READY=NO_PENDING_INDEPENDENT_REVIEW;IMPLEMENTATION_AUTHORIZED=NO;REAL_FIELD_PROOF=HOLD. No existing migration/function ownership/security/normal-runtime/RLS change; no new financial/provider/Room authority.

## Revision 3 bounded closure

Correct exactly R2-H01/H02/M01/M02 from the independent Revision2 review. [SPEC section22](../specifications/SPEC-0090-governed-offline-field-proof-exclusive-capability-composition.md#22-revision-3-bounded-normative-closure) is normative. No deployed encoding existed; the ACL domain/version stay V1 and complete catalog value extraction now determines its bytes. No migration number assigned; implementation/field proof remain unauthorized.

| Finding | Revision3 contract change | Evidence still required |
| --- | --- | --- |
| R2-H01 | PG18 modes map to fixed u8 enum; input/all/output ordinals and qualified type identities exact; return shapes, NULL/empty proconfig, effective ACL/PUBLIC/ownership/defaults and canonical ordering closed. Eight conceptual fixtures, including C/no-config and negative ACLs. | Independently generated complete ACL goldens and live installed catalog proof. |
| R2-H02 | S17 caller input is the existing eight command fields, confirmed-only as current launcher. Server derives all54 V042 arguments from binding/admission/current authority/writer evidence. Output exposes only original caller request, scoped commitment and20 required accepted-artifact fields for JCA. S18 receives unchanged envelope and privately rederives facts before frozen APPLY. | Positive writer parity, altered envelope/currentness/authority/two-org/transaction-continuity denial and frozen/JCA tests. |
| R2-M01 | Exactly32 CSPRNG bytes, preflight-only HMAC-SHA-256/domain/MAC32, timing-safe comparison required. ACTIVE/RETIRED atomic rotation, monotonic positive-u32 version per lineage, no reuse, fresh reincarnation lineage/material, key-loss fail closed. | Approved binary/RNG/timing-safe primitive, exact dependency ACL/provenance and HMAC goldens. |
| R2-M02 | Sole per-column owner grant matrix, exact consumer/entrypoint/reason for every retained grant; no generic common read set. Source monetary payload/product_refs/additional_order_totals and unused metadata removed. Lock-enabling UPDATE distinguished from bookkeeping; zero direct domain DML. | Actual body/transitive capability/catalog least-privilege proof. |

S17/JCA/S18 uses the original same-connection READ COMMITTED trusted-adapter sequence and stateless private rederivation, not a new canonical authority, possession mechanism or BEGIN provenance row. Commitment cannot replace admission, execution proof, frozen snapshot/currentness or honest JCA. No private selected evidence, progress or verifier is returned. Retained canonical manifest storage simply makes the existing immutable binding requirement explicit; the38 fingerprint tags are unchanged.

Key storage remains private control storage; Q reads minimum ACTIVE-key metadata/material, ADMIN governs. A/E invoke Q and cannot read keys. New incarnation rejects copied receipts/lineage; normal restart retains fencing and active lineage. Timing-safe implementation/dependency installation are future proof gates, not verified here. Column traceability replaces broad inventories; actual OWNER_TRANSITIVE_AUTHORITY_PROOF=PENDING_IMPLEMENTATION, never SAFE by prose.

Preserve four identities/zero memberships,18 signatures/16 names,wrapper-only/no raw service SELECT,no global RLS,immutable binding,durable exclusion/stale fencing,at-most-one delivery without human receipt,ISSUED/CONSUMED with derived invalidity,I1-I17,clone NOT_READY/incarnation,P lock route,actual lock order,frozen V039-V042,history compatibility/watchdog,unchanged normal runtime and no Room/provider/financial authority. Prior resolved findings have no known contract regression; final independent review must confirm.

GOLDEN_VALUES_REQUIRED_BEFORE_DOCUMENT_FREEZE=NO only when canonical algorithms are complete; GOLDEN_VALUES_REQUIRED_BEFORE_IMPLEMENTATION_FREEZE=YES for binding,slots,policy,history,ACL,preflight frame/HMAC. No invented digest. HMAC_SECURITY_CONTRACT=CLOSED_SELF_REVIEW;HMAC_BINARY_DEPENDENCY_PROOF=PENDING_IMPLEMENTATION. R2_H01_RESOLVED=YES;R2_H02_RESOLVED=YES;R2_M01_RESOLVED=YES;R2_M02_RESOLVED=YES are self-review claims, not independent approval. CONTRACT_REVISION_STATUS=COMPLETE_PENDING_INDEPENDENT_REVIEW;PACKAGE_1_FREEZE_READY=NO_PENDING_FINAL_INDEPENDENT_REVIEW;IMPLEMENTATION_AUTHORIZED=NO;REAL_FIELD_PROOF=HOLD.

## Bounded correction R3-M01

Final Revision3 adversarial review passed with zero BLOCKER/HIGH and one MEDIUM: E retained a predecessor revision SELECT outside the authorized confirmed-only flow. [SPEC section22.6](../specifications/SPEC-0090-governed-offline-field-proof-exclusive-capability-composition.md#226-bounded-correction-r3-m01) removes only E SELECT(public.marketplace_transaction_identity_decision.revision), updates HD to scoped head existence/absence and adds no substitute column/helper/grant.

OFFLINE_DECISION_SUPERSEDES_ALLOWED=NO;OFFLINE_DECISION_EXPECTED_SUPERSEDES=NULL;PREDECESSOR_REVISION_READ_REQUIRED=NO. Proven HEAD_ABSENT derives candidate revision1; HEAD_PRESENT conflicts and denies new effect. Unavailable query never means absence. Frozen writer/V042,18 signatures,private54+expected19 argument mapping,original fingerprints,HMAC,lock order,state machines,admission,fencing,two-org,history,delivery and reconciliation remain unchanged. A's decision audit projection keeps revision; only E's unnecessary privilege is removed.

R3_M01_RESOLVED=YES;E_REVISION_SELECT_REMOVED=YES;HD_EXISTENCE_ONLY=YES;REVISION_1_DERIVED_WITHOUT_PREDECESSOR_READ=YES;UNJUSTIFIED_COLUMN_GRANTS=0;OWNER_PRIVILEGE_CONTRACT_CLOSED=YES;NO_REGRESSION=YES are correction self-review claims, not freeze approval or deployed safety proof. CONTRACT_CORRECTION_STATUS=COMPLETE_PENDING_INDEPENDENT_FREEZE_RECHECK;PACKAGE_1_FREEZE_READY=NO_PENDING_INDEPENDENT_FREEZE_RECHECK;IMPLEMENTATION_AUTHORIZED=NO;REAL_FIELD_PROOF=HOLD. Next gate is independent Package1 freeze recheck.

## Traceability

Predecessors: [ADR-0086](ADR-0086-controlled-command-authority-provisioning.md), [ADR-0087](ADR-0087-s2a-single-process-field-proof-ceremony.md), [SPEC-0089](../specifications/SPEC-0089-s2a-attestation-consumption-and-attested-command-authority.md), [offline runbook](../runbooks/RUNBOOK-S2A-REAL-FIELD-PROOF-OFFLINE.md).

Frozen migrations: [V039](../../applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V039__restrict_transaction_identity_runtime_privileges.sql), [V040](../../applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V040__create_s2a_approval_governance.sql), [V041](../../applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V041__create_s2a_accepted_attestation.sql), [V042](../../applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V042__create_s2a_attestation_consumption_and_attested_command_authority.sql).

Existing application boundaries: [composition](../../applications/command-authority-ceremony/src/main/kotlin/io/flooow/ceremony/PostgresCeremonyComposition.kt), [launcher](../../applications/command-authority-ceremony/src/main/kotlin/io/flooow/ceremony/OfflineFieldProofLauncher.kt), [ceremony](../../applications/command-authority-ceremony/src/main/kotlin/io/flooow/ceremony/ExecuteAttestedFieldProof.kt), [offline support](../../applications/command-authority-ceremony/src/main/kotlin/io/flooow/ceremony/PostgresOfflineFieldProofSupport.kt), [history](../../applications/command-authority-ceremony/src/main/kotlin/io/flooow/ceremony/PostgresOfflineMigrationHistory.kt).

Existing persistence boundaries: [writer](../../applications/marketplace-operations-persistence-postgres/src/main/kotlin/io/flooow/marketplace/persistence/postgres/PostgresTransactionIdentityWriter.kt), [verifier](../../applications/marketplace-operations-persistence-postgres/src/main/kotlin/io/flooow/marketplace/persistence/postgres/PostgresAcceptedAttestationVerifier.kt), [issuer](../../applications/marketplace-operations-persistence-postgres/src/main/kotlin/io/flooow/marketplace/persistence/postgres/PostgresAttestedCommandAuthorityIssuer.kt), [authorization](../../applications/marketplace-operations-persistence-postgres/src/main/kotlin/io/flooow/marketplace/persistence/postgres/PostgresCommandAuthorization.kt).

## G3F.3A crypto dependency contract approval

DESIGN-AMENDMENT / NO-RUNTIME: approve only the two dependency contract decisions under [SPEC section23](../specifications/SPEC-0090-governed-offline-field-proof-exclusive-capability-composition.md#23-g3f3a-crypto-dependency-contract-approval), the normative exact signature/ownership/atomic ACL/default-ACL manifest. This supersedes historical pending dependency approval language above for G3F.3A only; installed/catalog/provenance/golden/RNG and other Package0090 gates remain.

Approve PostgreSQL18 pgcrypto extension1.4 and only binary offline_crypto.hmac(pg_catalog.bytea,pg_catalog.bytea,pg_catalog.text) RETURNS pg_catalog.bytea, statically fixed sha256/HMAC-SHA-256 over the accepted preflight frame. Approve flooow_offline_mac32 extension1.0 and source-exact offline_crypto.timing_safe_equal32(pg_catalog.bytea,pg_catalog.bytea) RETURNS pg_catalog.bool: C IMMUTABLE STRICT PARALLEL SAFE SECURITY INVOKER; SQL NULL short circuit; each non-NULL operand exactly32 payload bytes or22023 error; CRYPTO_memcmp32 comparison. No source/signature alteration or nineteenth public wrapper.

Trusted SCHEMA_DEPLOYMENT_ADMIN D is exact postgres, required future owner of both extensions, private schema and member crypto functions; no assertion of live installation. Existing ADMIN control/key governance remains unchanged. Separate administrative version-pinned installation/ownership/current/default ACL closure is atomic while NOT_READY; V043 MUST NOT CREATE EXTENSION or install/repair crypto. Q alone receives private schema USAGE and exact non-owner EXECUTE on binary HMAC and timing_safe_equal32, without grant option. PUBLIC/all other Package/shared operational identities receive no direct/effective crypto access; no broad pgcrypto grants/defaults.

A/E retain only their guarded Q readiness capability. No plaintext key storage or key retrieval by RUNTIME/EXECUTOR is allowed; existing private ADMIN-governed storage and Q-only material reads remain unchanged. Q's preflight symmetric-MAC duty does not merge V evidence verification with I domain issuance; frozen capabilities, four zero-membership identities and18 signatures remain. DEPLOYMENT != VERIFIER != ISSUER != RUNTIME != EXECUTOR; CAPABILITY != AUTHORITY; INSTALLATION != RUNTIME_PERMISSION; PUBLIC != PACKAGE_0090_AUTHORITY.

Comparator approval binds supplied prior SO_SHA256=61347c5ad692a5e73664ee9a59907576a7ebde9ecdd24edc92fff237c15a11a7, PostgreSQL18.4, OpenSSL3.5.6, CRYPTO_memcmp@@OPENSSL_3.0.0. It proves neither pgcrypto binary identity nor installed ACLs. This amendment performs no runtime/database/role/privilege action.

PGCRYPTO_CONTRACT_APPROVED=YES;TIMING_SAFE_CONTRACT_APPROVED=YES;CRYPTO_OWNERSHIP_APPROVED=YES;CRYPTO_ACL_APPROVED=YES;DEFAULT_ACL_CONTRACT_APPROVED=YES;DEPLOYMENT_RUNTIME_SEPARATION=PASS;UNRESOLVED_BLOCKER_COUNT=0 for the two dependency contract blockers.
CRYPTO_DEPENDENCY_CONTRACT_APPROVAL=PASS;V043_IMPLEMENTATION_READY=YES for bounded G3F.3B contract-scoped implementation, not runtime/activation/field-proof approval;NEXT_GATE=G3F.3B_V043_IMPLEMENTATION_AND_CONTRACT_CLOSURE;REAL_FIELD_PROOF=HOLD.

## ADMIN identity and attribute contract closure

DESIGN-AMENDMENT / OFFLINE / FAIL-CLOSED. Approve ADMIN ownership identity `flooow_offline_control_owner` exclusively under [SPEC section24](../specifications/SPEC-0090-governed-offline-field-proof-exclusive-capability-composition.md#24-admin-identity-and-attribute-contract-closure). Its exact attributes are NOLOGIN, NOSUPERUSER, NOCREATEDB, NOCREATEROLE, NOREPLICATION, NOBYPASSRLS, INHERIT. Require zero incoming/outgoing direct/transitive memberships and no SET ROLE path for protected operational identities; INHERIT grants no authority without membership. The separate V/I/E/A/P/Q/Z owners and four service identities retain NOINHERIT and their existing restrictions.

ADMIN is a non-login control/key ownership role, not a deployment login, verifier, issuer, runtime, executor or application principal. It receives no provider credentials, broad schema/table privileges, schema/database ownership, crypto ownership or operational function ownership. Its closed ownership set is exactly the fourteen Package0090 public control/key tables in SPEC21.7, enumerated in24, plus only their intrinsic indexes/constraints/composite row types. PostgreSQL postgres remains deployment authority and owner of both crypto extensions, offline_crypto schema and crypto members. Trusted administrative actions remain separately governed; ownership is not a new operational entrypoint.

Use separate administrative provisioning: V043 is NOT authorized to create this role, alter its attributes/memberships or repair its existing authority/default ACLs. The future migration must validate its approved posture as a precondition, then may create/transfer only the enumerated controls under deployment authority. Missing/mismatched role fails closed. Existing draft role creation is not authorization and must be replaced in the next V043 implementation task; this amendment does not modify that draft.

ADMIN/current creator defaults and current object ACLs must satisfy SPEC23.3/24 before operational exposure: no default non-owner Package0090 authority, no PUBLIC control/key access, and only existing SPEC22.4 explicit object/column grants. Ownership transfer does not apply the recipient's defaults retroactively. No role receives indirect ownership. No database, role, privilege or migration operation is performed by this amendment.

ADMIN_IDENTITY_APPROVED=YES;ADMIN_ROLE_NAME=flooow_offline_control_owner;ADMIN_LOGIN=NO;ADMIN_SUPERUSER=NO;ADMIN_BYPASSRLS=NO;ADMIN_ROLE_SEPARATION=PASS;ADMIN_OWNERSHIP_SCOPE_CLOSED=YES;ADMIN_ACL_SCOPE_CLOSED=YES;UNRESOLVED_BLOCKER_COUNT=0 for this ADMIN identity contract blocker.
ADMIN_IDENTITY_AND_ATTRIBUTE_CONTRACT_CLOSURE=PASS;V043_IMPLEMENTATION_READY=YES for bounded contract-scoped implementation;NEXT_GATE=G3F.3B_V043_IMPLEMENTATION_AND_CONTRACT_CLOSURE;REAL_FIELD_PROOF=HOLD. Installed/catalog/default-ACL proof and all other implementation gates remain pending.

## G3F.3B.1 preflight receipt expiry contract closure

DESIGN-AMENDMENT / OFFLINE / FAIL-CLOSED. No existing accepted policy duration specifies the preflight receipt lifetime. Add mandatory server-owned, ADMIN-provisioned, immutable policy-versioned `preflight_receipt_ttl` and its approved maximum, positive finite int8 microseconds with actual<=maximum. No numeric production TTL is invented. Both values and approved canonical policy identity must be provisioned in a separate administrative transaction AFTER V043 policy schema creation and BEFORE any policy-dependent Package0090 wrapper use, under SPEC25. Their absence does not block schema creation; it leaves POLICY_BOOTSTRAP_STATE=UNPROVISIONED and policy-dependent wrappers fail closed, never using a hard-coded SQL default.

Under SPEC18/21.2/21.3, Q captures issued_at from authoritative pg_catalog.clock_timestamp() and derives expires_at = issued_at + preflight_receipt_ttl using exact checked microsecond arithmetic. Caller-supplied issuance expiry/time/duration is forbidden. The existing nine-field HMAC receipt binds both instants and the full policy digest; that digest includes the exact immutable policy_version and the new actual/maximum pair at deadline-policy tags28/29 (29 total fields). Reapprove policy versions and dependent manifests/binding digests/golden vectors; historical27-field policies and incomplete fixtures cannot satisfy the amended contract.

S01 uses Q's issuance rule. S13/Q validation uses the original authenticated issued_at and the same current approved policy_version/digest/TTL, requires exact rederived expiry and issued_at<=fresh database time<expires_at, and preserves original receipt bytes. Q never renews on the EXECUTOR route; S13 repeats expiry checks before ownership creation/confirmation and return, including lost-ack replay. Expired receipts fail closed and replay never restores validity. A separate fresh eligible S01 issuance does not renew old receipts, execution deadlines or delivery/admission authority. Other existing eligibility checks remain independent; no role, signature, grant, crypto, V043 or launcher change is authorized by this amendment.

PREFLIGHT_EXPIRY_DERIVATION_CLOSED=YES;CALLER_SUPPLIED_EXPIRY=FORBIDDEN;DATABASE_TIME_AUTHORITY=YES;POLICY_VERSION_BINDING=YES;EXPIRED_REPLAY_ALLOWED=NO;S01_Q_S13_EXPIRY_RULE_CLOSED=YES;UNRESOLVED_BLOCKER_COUNT=0 for this expiry contract blocker.
PREFLIGHT_RECEIPT_EXPIRY_CONTRACT_CLOSURE=PASS;V043_IMPLEMENTATION_READY=YES for bounded implementation;NEXT_GATE=G3F.3B_V043_IMPLEMENTATION_AND_CONTRACT_CLOSURE;REAL_FIELD_PROOF=HOLD. Installed proof, numeric production policy provisioning and runtime/migration authorization remain separate gates.


## S13/S14/S15/S16 output transport contract closure

SPEC-0090 section21.1 S13-S16 exact output transport closure expands only the existing Control outputs field lists under section8/21.5 semantics: S13 eight fields, S14 nine, S15 five, S16 eight. Tags are sequential and unique, order fixed, SQL types explicit, every successful-output field required/non-null and encoded by21.2. Missing evidence denies rather than fabricating a partial receipt. S13/S15/S16 admissible retries preserve original records; S14 repeat preserves original delivery lineage/window with permission_to_attempt=false. No new field, authority, renewal, delivery permission, business state, SQL signature or privilege is introduced. Crypto, ADMIN and preflight expiry contracts remain unchanged.

CONTRACT_CLOSURE_S13_S14_S15_S16_OUTPUT_TUPLES=PASS;UNRESOLVED_BLOCKER_COUNT=0 for this closure;V043_IMPLEMENTATION_READY=YES for bounded contract-scoped implementation;NEXT_GATE=G3F.3B_V043_IMPLEMENTATION_AND_CONTRACT_CLOSURE;REAL_FIELD_PROOF=HOLD. Contract consistency is not source implementation, installed/catalog evidence or migration/runtime authorization.

## Offline policy bootstrap contract closure

DESIGN-AMENDMENT / OFFLINE / FAIL-CLOSED. This amendment supersedes only the earlier requirement to provision policy values before V043 execution. V043 may create the approved Package0090 policy storage/schema objects, including public.offline_deadline_policy, without a policy row. It MUST NOT invent, hard-code, default or provision preflight_receipt_ttl, its approved maximum or a production policy_version. V043_POLICY_VALUE_PROVISIONING_AUTHORIZED=NO.

POLICY_BOOTSTRAP_STATE=UNPROVISIONED | ACTIVE is derived for the exact required policy version/digest, not a caller flag or independent execution authority. UNPROVISIONED includes missing, invalid, unapproved, not-yet-effective or mismatched policy. Policy-dependent wrappers fail closed in this state. ACTIVE requires an explicitly approved, committed, immutable, fully validated policy row whose effective_from has been reached by the database wall clock. ACTIVE alone does not establish deployment READY, binding activation, possession, admission or mutation eligibility.

Exact sequence: V043 schema creation -> separate ADMIN provisioning -> policy validation -> ACTIVE -> wrapper use permitted subject to every existing guard. Trusted deployment administration acts directly as postgres under separate explicit ADMIN policy governance; flooow_offline_control_owner remains the NOLOGIN control-table owner with zero memberships. No service, RUNTIME, EXECUTOR or V/I/E/A/P/Q/Z owner may provision policy. No new login, membership, SET ROLE route, operational entrypoint or function is authorized.

Provisioning supplies an independently approved policy_version, the complete29-field canonical_policy including preflight_receipt_ttl and its approved maximum, policy_digest=SHA-256(canonical_policy), and immutable effective_from timestamptz(6). It explicitly establishes the existing binding/readiness policy-version/digest references where applicable. It is a separate administrative transaction after schema creation, with complete validation before commit and a durable administrative audit record. Missing or invalid evidence rolls back and leaves operational use denied. SPEC25 defines activation, the exact read-only effective_from dependency, audit evidence and rotation. No fallback TTL, session config/GUC, hidden default or caller-supplied TTL is permitted.

Existing receipts retain the exact policy/version, issued_at, expiry and MAC under which they were issued. Rotation uses a newly approved immutable policy_version and separately governed bindings/readiness; it never updates an old policy row or recalculates an old receipt under the new TTL. A receipt that no longer matches current approved binding/readiness fails closed without changing its original expiry. No implicit renewal or new execution authority follows from rotation.

POLICY_BOOTSTRAP_SEQUENCE_CLOSED=YES
V043_POLICY_SCHEMA_CREATION_AUTHORIZED=YES
V043_POLICY_VALUE_PROVISIONING_AUTHORIZED=NO
ADMIN_POLICY_PROVISIONING_REQUIRED=YES
POLICY_UNPROVISIONED_FAILS_CLOSED=YES
SESSION_POLICY_SOURCE_FORBIDDEN=YES
HIDDEN_DEFAULT_FORBIDDEN=YES
RECEIPT_POLICY_IMMUTABILITY=YES
UNRESOLVED_BLOCKER_COUNT=0
CONTRACT_CLOSURE_OFFLINE_POLICY_BOOTSTRAP=PASS
V043_IMPLEMENTATION_READY=YES
NEXT_GATE=G3F.3B_V043_IMPLEMENTATION_AND_CONTRACT_CLOSURE

These results close only the bootstrap contract gap. They authorize the next bounded V043 implementation task, not migration execution, provisioning execution, installed/catalog proof, runtime activation or field proof. REAL_FIELD_PROOF=HOLD.

## Independent technical test-fixture approval — 2026-10-03

FIXTURE_ID=PACKAGE-0090-G3F-3B-FIXTURE-001
POLICY_VERSION=fixture-1
TAG28_PREFLIGHT_RECEIPT_TTL_US=1000000
TAG29_PREFLIGHT_RECEIPT_TTL_APPROVED_MAX_US=2000000
SCOPE=TEST_GOLDEN_REHEARSAL_ONLY
PRODUCTION_POLICY_APPROVAL=NO
PRODUCTION_POLICY_PROVISIONING=NO
APPROVAL_PROVENANCE=FLOOOW_TECHNICAL_FIXTURE_APPROVAL_2026-10-03

Record the independently approved synthetic actual/maximum pair using the
existing VECTOR_1 timing scale. Both are positive finite int8 microseconds,
actual <= maximum; policy_version remains fixture-1. Canonical policy field count
is29, with both values bound and all policy/dependent golden bytes/digests
recomputed and independently verified before closure. This is TEST/REHEARSAL
ONLY: no production default, policy provisioning, live role, database execution,
G3G or field-proof authority is granted. No session/GUC, hidden fallback or
caller-supplied TTL is permitted. Only the prior fixture TTL/maximum approval
dependency is superseded; other implementation/evidence gates remain.

## Complete normative retained TEST evidence fixture — 2026-10-03

Decision: retain complete synthetic rows for VECTOR_1, not an opaque approved
evidence-binding digest. SPEC's complete retained TEST fixture amendment fixes
the one-row ML promotion/registry/source and one-row Omie base/V3/page/progress
inputs, with exact auxiliary physical columns and prerequisite FKs. Organization
UUID6,manifest UUID7,ML UUID8,Omie UUID9,order UUID10,order-1,integration-1 and
fixture-1 are preserved. Source evidence values and test-only provenance are
retained in the evidence JSON; full preimage/manifest/binding goldens for all
three vectors accompany it. Python and JVM independently construct the bytes.
VECTOR_3 encoder-only mutation remains distinct from the coherent alternate.

SCOPE=TEST_GOLDEN_REHEARSAL_ONLY;PRODUCTION_DATA=NO;PROTECTED_DATA=NO;
LIVE_DATA_RETRIEVAL=NO. Synthetic source semantic fingerprint000...001 is a codec
token, never provider/domain acceptance proof. SQL selection/framing execution
parity remains a later separately authorized isolated rehearsal. No frozen
migration,production policy,live role,protected database,G3G or field-proof
authority changes. This closes the normative evidence-input gap and permits
the already authorized V043 source implementation to continue; it does not
declare complete ACL/history/HMAC/private-dataflow goldens or wrapper closure.

## Technical governance approval — S01 connection read authority (2026-10-03)

S01_CONNECTION_READ_AUTHORITY_APPROVED=YES. Owner A may read only
public.integration_connection.organization_id,connection_id,provider_key,
credential_kind,status,binding_version for S01_ONLY/BOUND_CONNECTION_READINESS.
Projection is PRIVATE_PREDICATES_ONLY. Derive both connection IDs and the
organization exclusively from the authenticated binding/header. Each exact
predicate requires bound organization, bound connection, frozen expected provider,
frozen expected credential kind, status ACTIVE and frozen expected binding version.
Require exactly one match for each connection; missing or ambiguous matches deny.
The already authorized integration_organization.organization_id/status pair is
also consumed by S01's private bound ACTIVE predicate; no organization column added.

Whole-table SELECT, credential_binding/secret_ref reads, returned raw connection
rows, service-login SELECT, write/lock privilege, caller-selected connection IDs,
dynamic selectors and metadata projection beyond private predicates are forbidden.
Expected physical per-column grant count is 1026; count alone is never proof.
Recompute the exact normative/source/deployment inventory and reject extras/missing
privileges. Q retains sentinel issuance, with no connection reads added to Q.
This approval changes no V001-V042, execution interlock, protected deployment,
production policy/crypto/roles, G3G or main publication authority.

## S01 target consumer authority amendment ? 2026-10-03

Owner A receives only the six READ_PRIVILEGE columns below on public.integration_mercado_livre_order_source_observation. CONSUMER=S01_ONLY; PURPOSE=FROZEN_MATCHES_TARGET_BOUND_JOIN; PROJECTION=PRIVATE_PREDICATES_ONLY. Existing registry/promotion/Omie base/Omie V3 authority expands only the exact matchesTarget predicate's S03 consumer traceability to S01; no additional columns there. No whole-table/service-login SELECT, raw observation return, write/lock privilege, dynamic selectors, caller target IDs or unrelated ML metadata reads.

The S01 target predicate preserves every join and filter of PostgresCeremonyComposition.runtime.matchesTarget; its six placeholders are replaced only by authenticated binding header fields in producer order. The unchanged EXISTS establishes the frozen target match. A separate readiness cardinality check over that identical join requires one eligible row and rejects ambiguous/multiple rows. No provider normalization: retained mercado-livre differs from frozen br.com.mercadolivre. Synthetic target-only tests cannot prove retained runtime-positive readiness. Organization and both connection predicates, R binding/slot/policy/readiness guards and target readiness all precede Q sentinel issuance. S01 stays STABLE/read-only/no-lock; all-state R reads ignore mutation expiry.

The normative ACL inventory in SPEC-0090 records the exact six added A reads: organization_id, connection_id, capability, input_progress_version, record_ordinal, external_order_ref. Physical grant inventory increases from 1026 to 1032 only upon complete actual/normative set equality. Deployment Q expectations must be regenerated from that complete inventory. V043 interlock remains until full source closure; protected PostgreSQL, production policy/crypto/roles and G3G remain excluded.


## S02 acceptedArtifact consumer authority amendment - 2026-10-03

S02_ACCEPTED_ARTIFACT_CONSUMER_AUTHORITY=APPROVED.
CONSUMER=S02_ONLY; PURPOSE=INSPECT_ACCEPTED_ARTIFACT_PREDICATE;
PROJECTION=PRIVATE_PREDICATES_ONLY.

The existing 27 A signer-key/signer-authority READ_PRIVILEGE rows in section22.4
now also trace to INSPECT.acceptedArtifact/S02. This is solely the exact frozen
PostgresOfflineFieldProofReconciler.inspect -> accepted(connection,input) ->
acceptedArtifact dependency. RECON.acceptedArtifact/S03 authority and semantics
remain unchanged. Preserve all existing joins, states, fingerprints, public-key
lineage, approval source/action/role, permission, verified-at windows and counts/
cardinality, including the non-SQL proof validation performed by the producer.

NEW_COLUMNS=0; NEW_PHYSICAL_GRANTS=0; PHYSICAL_GRANT_COUNT=1032.
No raw signer-row or broader signer metadata output, service-role SELECT,
helper function, current-possession inference, cached fixture truth or authority
inference from ownership/grants is authorized. S02 remains STABLE/read-only,
with bound organization/binding, uniform foreign/nonexistent denial and the
unchanged admission validity rules. This approval supplies consumer traceability
only; it does not turn the SQL signer join into the full acceptedArtifact result.
V001-V042, the V043 interlock, protected DB, production policy/crypto/live roles,
G3G and main publication remain outside this amendment.

## S02 Ed25519 path and invalid-key acceptance contract - 2026-10-03

The supplied bounded native-path approval and invalid-key closure authorize one
thin OpenSSL Ed25519 native primitive in the existing flooow_offline_mac32
package. Fresh verification is mandatory inside the database boundary; caller
truth, cached proof fingerprints and handwritten curve/point logic are forbidden.
The exact native contract, V-owned bridge and ACL manifest are specified in the
S02 fresh Ed25519 amendment of SPEC-0090. This supersedes only the previous
S02 no-helper and Q-only schema limitations for this exact capability.

JCA_PROVIDER_EXCEPTION_TAXONOMY_PARITY=NOT_REQUIRED.
ACCEPTED_ARTIFACT_DECISION_PARITY=REQUIRED.
The known FF point is cryptographic rejection: JCA InvalidKeyException maps to
accepted false; OpenSSL false maps to accepted false. Structural errors remain
22023; operational/allocation/internal failures remain XX000. Only true accepts.
No provider internals, alternate algorithms or authority widening is permitted.

D owns the native primitive; only V gets exact native EXECUTE and private crypto
USAGE. V's fixed-search-path SECURITY DEFINER bridge delegates exactly three
bytea arguments. Only A gets bridge EXECUTE, with no direct native access,
private-schema USAGE or key-material authority. PUBLIC/services have no path.
S02 public signature, eleven outputs, seven counts and read-only behavior stay
unchanged. Physical column grants remain 1032; function/schema capabilities are
separate. Final reproducible binary identity and source evidence do not prove
installed ownership/ACLs or PostgreSQL runtime parity.

V001-V042, V043 execution/interlock, protected DB/runtime installation,
production roles/policy, G3G and main publication remain excluded.
