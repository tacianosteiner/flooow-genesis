# SPEC-0087 - S2A controlled field-proof ceremony

## Status and scope

Technical implementation is present and proven in disposable deployment-equivalent tests. This specification still creates no real authority, provider call, or real identity decision and does not authorize field execution.


Source decision: ADR-0087.

The implemented technical entrypoint is one offline command, `execute-field-proof`. It has no HTTP route, OpenAPI operation, scheduler, provider connector invocation, or service-bearer fallback.

## Frozen field-proof target

```text
organizationId                 7b6798b7-eefa-4493-9053-4515f0a39c4c
mercadoLivreConnectionId       33e7a252-292c-44ef-bab8-7a06b662c0fb
omieConnectionId               577e56cc-bb2b-4d15-8ee3-c1ce70b03149
omieSourceOrderReference       3532346728
marketplaceExternalOrderId     2000018336941860
marketplaceOrderId             71a04f21-2da1-4078-aa99-22292ad69ca0

ML lineage                     marketplace-economic.order-source / 0 / 1
ML external order and currency 2000018336941860 / BRL

Omie V3 lineage                marketplace-economic.omie-transaction-evidence.reacquisition-v3 / 1 / 31
Omie integration reference     2000018336941860
Omie currency                  NULL (neutral, never inferred)
Omie semantic fingerprint      5254e4e83b4b05e747d60f0548f1ca5f1aaa5af804fe3d1bcbfa696f0ce1663c
Omie provider revision         2026-09-07T22:10:14.000000
```

The command must re-read and verify this durable lineage; these values are neither request-supplied authority nor a substitute for the writer's currentness validation.

## Manifest and approval requirements

A signed, bounded manifest is required before mutation. It identifies the accountable operator, approval source, bounded approval window, organization, exact connection pair, exact target, `TRANSACTION_IDENTITY_DECISION_WRITE`, reason, provenance, correlation ID, revocation owner, credential delivery method, and rotation owner.

Missing, expired, malformed, mismatched, duplicate, or unverifiable manifest data denies execution before credential generation. The implementation must not invent human values.

## Process and TTY contract

`execute-field-proof` is one process. It may use protected TTY input/output only after preflight passes. It must reject redirected stdin/stdout when one-time secret delivery cannot be proven protected. It must not use command arguments, environment variables, files, clipboard, shell history, transcripts, Docker environment, SQL literals, logs, receipts, or error rendering for raw tokens.

The command generates 32 random bytes with `SecureRandom`, constructs the canonical `fc1.<credential UUID>.<base64url>` token only for one-time TTY delivery and immediate in-process authentication, then destroys raw material before the writer transaction.

No raw credential exists between processes.

## State machine

```text
DESIGNED
-> HUMAN_APPROVED
-> PREFLIGHT_PROVEN
-> CREDENTIAL_GENERATED_IN_MEMORY
-> PRINCIPAL_ISSUED
-> CREDENTIAL_BOUND
-> TOKEN_DELIVERED_ONCE
-> GRANT_ACTIVE
-> ACTOR_AUTHENTICATED_IN_PROCESS
-> RAW_SECRET_DESTROYED
-> IDENTITY_APPLIED
-> POST_PROOF_VERIFIED
-> optional GRANT_REVOKED
```

No state invokes a provider. Any failure before identity application must roll back or leave only the independently committed issuer operations explicitly reported as an incomplete ceremony requiring human review; the command must never continue to identity write after an incomplete or ambiguous authorization step.

## Issuer and authentication contract

The command uses the existing `ControlledCommandAuthorityIssuer` under the issuer role to append, in this order:

1. one `command_principal` for the frozen organization and ML/Omie pair;
2. one enabled `command_credential_revision` revision 1;
3. one enabled `command_permission_grant` with only `TRANSACTION_IDENTITY_DECISION_WRITE`.

It uses the same in-memory credential to obtain an `AuthenticatedCommand` under the runtime role. It must then destroy the credential before invoking the writer. Receipts, checkpoints, and rendered errors contain only nonsecret identifiers and nonsecret fingerprints.

## Writer and lock contract

The command invokes the existing `PostgresTransactionIdentityWriter` in one caller-owned `READ COMMITTED`, `autoCommit=false` transaction. It does not add progress locks or a second evidence protocol. The writer and triggers own the authoritative lock sequence and re-check authorization immediately before immutable insert.

The intended result is one `CONFIRMED` decision. Retry after an uncertain commit uses the same decision ID and exact intent; `AlreadyApplied` is success only when it returns the same durable semantic result. Changed intent with the same decision ID is rejected.

## Currentness and durable evidence

The writer must select and validate the exact durable ML and Omie V3 lineage. Missing durable evidence, malformed V3 sidecar/page lineage, unknown provider time, semantic conflict, reference conflict, currency conflict, connection mismatch, or authorization change fail closed. Omie `NULL` currency remains neutral, never BRL by inference.

## Exact row delta and kill rules

Before execution, scoped counts must be exactly:

```text
command_principal = 0
command_credential_revision = 0
command_permission_grant = 0
command_authority_operation = 0
marketplace_transaction_identity_decision = 0
marketplace_transaction_identity_head = 0
```

After one applied proof without revocation:

```text
1|1|1|3|1|1
TOTAL_EXPECTED_NEW_ROWS_AFTER_APPLIED_PROOF = 8
```

Any count mismatch, unexpected table mutation, unexpected permission, provider activity, financial authority, Decision Room authority, direct head mutation, or nonzero unapproved authority record is KILL.

Immediate revocation is prohibited unless separately approved. If approved, it appends exactly one disabled permission-grant revision and one authority-operation row; expected cumulative count becomes 10.

## Future V039 least-privilege contract

V039 must revoke `PUBLIC EXECUTE` for these V035/V036 functions:

```text
transaction_identity_hash
transaction_identity_grant_fingerprint
transaction_identity_intent
transaction_identity_fingerprint
transaction_identity_locks
transaction_identity_validate
transaction_identity_head_guard
transaction_identity_advance
transaction_identity_immutable
transaction_identity_withdrawal_locks
transaction_identity_withdrawn_validate
```

For the first `CONFIRMED` proof only, grant runtime `EXECUTE` only on:

```text
transaction_identity_hash(...)
transaction_identity_grant_fingerprint(...)
transaction_identity_intent(...)
transaction_identity_fingerprint(...)
transaction_identity_locks(...)
```

Do not grant withdrawal-specific execution. Trigger-only functions receive no unnecessary runtime grant. A deployment-equivalent test must prove that the runtime can insert one valid decision after `PUBLIC EXECUTE` removal and that the `SECURITY DEFINER` head projection still operates.

Runtime table privileges are limited to:

```text
command_principal                              SELECT, UPDATE (already V037)
command_credential_revision                    SELECT (already V037)
command_permission_grant                       SELECT (already V037)
integration_organization                        SELECT (already V037)
integration_connection                          SELECT (already V037)
marketplace_transaction_identity_decision      SELECT, INSERT
marketplace_transaction_identity_head          SELECT
marketplace_order_identity_registry            SELECT
marketplace_order_occurrence_source_promotion  SELECT
integration_mercado_livre_order_source_observation SELECT
integration_omie_transaction_evidence          SELECT
integration_omie_transaction_evidence_v3       SELECT
integration_connector_page_commit              SELECT
integration_connector_progress                 SELECT
```

`UPDATE` on connector progress exists solely for `SELECT ... FOR UPDATE`; no semantic update is allowed. No DELETE, TRUNCATE, DDL, direct head DML, evidence DML, or role-management privilege is permitted.

## Implemented technical proof

The technical implementation has been exercised against disposable PostgreSQL 18.4 with real issuer/runtime database roles.

The following properties are proven:

- runtime CONFIRMED path: PASS
- transaction_identity_locks remains SECURITY INVOKER: PASS
- organization semantic UPDATE by runtime: DENIED
- connector-progress semantic UPDATE by runtime: DENIED
- PUBLIC privileged helper execution: DENIED
- withdrawal-specific runtime execution: DENIED
- direct authority provisioning by runtime: DENIED
- direct decision deletion/head mutation: DENIED
- evidence mutation: DENIED
- target organization/pair/reference binding: PASS
- wrong integration reference before provisioning: DENIED
- missing integration reference before provisioning: DENIED
- cross-organization target before provisioning: DENIED
- raw credential durable occurrence: ZERO
- credential use after destroy: REJECTED

This implementation proof is not equivalent to real field-proof authorization.

## Approval attestation boundary

A signed, bounded manifest remains mandatory before any real mutation. Missing, expired, malformed, mismatched, duplicate, or unverifiable approval material must fail closed.

The following executable attestation details remain intentionally unfrozen and must not be invented by implementation code:

- canonical manifest serialization
- signer identity and verification authority
- signature algorithm and parameters
- signing-key custody
- verification-key distribution
- anti-replay / duplicate identity
- approval artifact storage and retention
- operational delivery and revocation procedure

Therefore the technical foundation may be versioned once all package gates pass, while real field execution remains blocked until a separate approved attestation contract exists.

## CommandCredential zeroization contract

The future domain change must keep the secret only in a mutable private byte array; provide idempotent `destroy()/close()`; overwrite all secret bytes; permanently reject `digest()` and verifier creation after destruction; expose no secret accessor; preserve `CommandCredential([REDACTED])`; and prevent credential-bearing request objects from surviving consumption.

Required tests must observe zeroization through a narrowly scoped test seam, prove use-after-destroy failure, preserve parser/verifier compatibility, and prove no token/verifier appears in rendering, logs, or receipts. JVM `String` source input cannot be deterministically wiped; generator code must therefore originate from bytes and bound textual lifetime to TTY delivery or immediate parsing.

## Required future test matrix

- exact credential grammar; 32-byte `SecureRandom` generation; parser/verifier compatibility;
- zeroization, idempotent destruction, use-after-destroy rejection, redacted rendering, and no secret logging;
- manifest signature, approval window, exact organization/pair/permission validation, and protected TTY enforcement;
- issuer/runtime separation, removed `PUBLIC EXECUTE`, least privilege, and no direct head/evidence DML;
- cross-organization, wrong-connection, wrong-permission, and `POLICY_ADMIN` denial;
- durable evidence/currentness/reference/currency/semantic-conflict denial;
- Applied exactly once, replay `AlreadyApplied`, changed-intent rejection, rollback, uncertain commit, revocation race, and credential-rotation race;
- exact `1|1|1|3|1|1` scoped delta and zero unexpected mutation;
- no provider call, no financial authority, and no Decision Room authority.

## Exclusions

This specification does not authorize a real field proof, provider call, financial classification, ExpectedSaleBasisPolicy, S2B, S3, C2, API route, secret persistence, automatic decision, or public provisioning.
