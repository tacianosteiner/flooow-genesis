# TASK-0165S2A4 - V040 approval-governance implementation evidence

## Status

V040 approval governance Revision 1 is implemented locally and has passed focused, adversarial, privilege, concurrency, deterministic-fixture, golden-parity and targeted-regression validation.

This evidence does not authorize or execute V041, V042, real signer governance, command authority, transaction identity, provider interaction, or a real field proof.

## Source state

```text
BRANCH=feature/task-0165s2a-controlled-field-proof-ceremony
SOURCE_HEAD=adb5eae464e3eff6c9c1c91f310375ca661b26e5
TRACKED_PRECONDITION=CLEAN
STAGED_PRECONDITION=CLEAN
PREEXISTING_UNTRACKED=.gradle-user-home/
```

## Authorized implementation scope

Exactly seven V040 files remain in scope:

```text
applications/marketplace-operations/src/main/kotlin/io/flooow/marketplace/operations/authorization/ApprovalGovernance.kt
applications/marketplace-operations/src/main/kotlin/io/flooow/marketplace/operations/authorization/ApprovalGovernanceFingerprint.kt
applications/marketplace-operations/src/test/kotlin/io/flooow/marketplace/operations/authorization/ApprovalGovernanceFingerprintTest.kt
applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V040__create_s2a_approval_governance.sql
applications/marketplace-operations-persistence-postgres/src/main/kotlin/io/flooow/marketplace/persistence/postgres/PostgresApprovalGovernance.kt
applications/marketplace-operations-persistence-postgres/src/test/kotlin/io/flooow/marketplace/persistence/postgres/PostgresApprovalGovernanceTest.kt
docs/evidence/TASK-0165S2A4-v040-approval-governance-implementation.md
```

V041 and V042 remain out of scope.

## Revision 1 reconciliation

```text
HIGH_1_CONCURRENCY=CLOSED
HIGH_2_ROLE_MEMBERSHIP=CLOSED
MEDIUM_1_DB_GOLDEN_PARITY=CLOSED
MEDIUM_2_DETERMINISTIC_FIXTURES=CLOSED
IMMUTABILITY_SQLSTATE=23514
```

## Role boundary

```text
PREEXISTING_CONTAMINATED_ROLE=FAIL_CLOSED
PREEXISTING_CLEAN_ROLE=NORMALIZED
ROLE_MEMBERSHIPS_CREATED=0
```

## Golden parity

Kotlin and PostgreSQL independently reproduce all four frozen lineage vectors:

```text
KEY_R1_BYTES=383
KEY_R1_SHA256=9e83dedfa91c44e001cbf4dbbe729436942ca5b6a568865eff3641e45651de65
KEY_R2_BYTES=455
KEY_R2_SHA256=7910bae04e816d4f94cd2086c7963d66d104eb2e33d9795fa14e4f0ca47e21e4
AUTHORITY_R1_BYTES=551
AUTHORITY_R1_SHA256=983e222e3e8d9692261db6613c3f0767947c32399493c3ae7de1824aa6371254
AUTHORITY_R2_BYTES=658
AUTHORITY_R2_SHA256=04cb49bc072d0d5466a767f5bc0424e1e3f7fcd6ae486bd3b6bf4f45328452a6
SPKI_SHA256=06e3fd8fda29bb60ab59557de61edb0aecdb231134be30e75b455f8e1b792fa9
```

## Deterministic fixtures

Revision 1 removes `UUID.randomUUID()` from V040 PostgreSQL fixtures. Synthetic identifiers are fixed and non-real. No frozen real S1 identifiers are used.

## Concurrency results

```text
C01_DIFFERENT_KEY_SUCCESSORS=ONE_APPLIED_ONE_CONFLICT
C02_DIFFERENT_AUTHORITY_SUCCESSORS=ONE_APPLIED_ONE_CONFLICT
C03_KEY_AUTHORITY_LOCK_CONTENTION=COMPLETES_WITHIN_BOUNDED_TIMEOUT_NO_DEADLOCK
C04_FAILED_SUCCESSOR_APPEND=NO_PARTIAL_ROW_REMAINS
C05_CONCURRENT_LOSER=CONFLICT_NOT_INTEGRITY_FAILURE_NOT_TIMEOUT
```

Exact replay remains a separate bounded no-write behavior.

## SQLSTATE isolation

```text
P0013,42501 -> GovernanceUnavailable
P0014,23505 -> Conflict
23502,23503,23514 -> IntegrityFailure
P0010,P0011,P0012 -> rethrow unchanged
unknown -> rethrow unchanged
```

Immutable UPDATE/DELETE is an integrity failure using SQLSTATE `23514`.

## Validation results

```text
ApprovalGovernanceFingerprintTest=PASS
PostgresApprovalGovernanceTest=PASS
PostgresCommandAuthorizationTest=PASS
PostgresControlledCommandAuthorityIssuerTest=PASS
PostgresTransactionIdentityWriterTest=PASS
git diff --check=PASS
AUTHORIZED_SCOPE=PASS
STAGED_COUNT=0
TRACKED_CHANGED_COUNT=0
```

## Zero-command-authority proof

V040 performs no command-authority or transaction-identity DML and creates no accepted attestation, attestation consumption, verifier role, provider call, real authority, or real field-proof execution.

## Residual findings

```text
BLOCKER=0
HIGH=0
MEDIUM=0
LOW=0
```

## Repository state

The seven authorized V040 files remain untracked and unstaged for final review.

```text
GIT_ADD=NO
GIT_COMMIT=NO
GIT_PUSH=NO
V041=HOLD
V042=HOLD
REAL_FIELD_PROOF=HOLD
NEXT_GATE=V040_REV1_FINAL_PACKAGE_REFRESH
```