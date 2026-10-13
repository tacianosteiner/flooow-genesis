# SPEC-0091 historical lineage atomic publication contract

Date: 2026-10-13. **Implemented and proven in disposable PostgreSQL; uncomposed in production.** Production rollout remains HOLD until canonical migration coordination/promotion is independently authorized. Parent [SPEC-0091](SPEC-0091-economic-projection-consumed-evidence-lineage.md); exact schema [DDL blueprint](SPEC-0091-historical-lineage-ddl-blueprint.md). No API, UI, execution, recovery or provider authority.

## Actual composition seam

`PostgresMarketplaceSalesIntelligenceProjection` acquires `DriverManager.getConnection(configuration.url,user,password)`. `PostgresConfiguration` supplies configuration, not a shared DataSource or transaction manager. `materializeIfNewer` uses autocommit, private `encodeState` and `UPSERT_SQL`; `readOne` opens a fresh connection. Its no-row path calls `currentBySubject`, which opens a hidden second connection. That is acceptable only as the current autocommit diagnostic read; it must NEVER be called from the future owned transaction. `MarketplaceSalesIntelligenceProjectionProcessor.materializeChange` reads evidence separately, assembles/calculates, creates the record and snapshot, then calls projection-only materialization. Its current observer is instrumentation before publication, not a persistence sink. Checkpoint advancement is separately retriable.

The future bounded adapter is `PostgresMarketplaceSalesIntelligenceLineagePublicationRepository`, receiving `ConsumedEconomicEvidenceSnapshot` plus `MarketplaceSalesIntelligenceProjectionRecord`. It uses the existing configuration; no global DataSource refactor. Extract a versioned private/package-internal `MarketplaceSalesIntelligenceStateCodecV1` from current `encodeState`, calculation/component/source codecs and their matching decode methods. Extract `readCurrent(connection,...)` and `upsertCurrent(connection,record,revisionId)` helpers. Helpers receive Connection explicitly, never create one, never commit/rollback/close it, never call public projection read methods, and return exact row count/current state rather than interpreting hidden commits. These names are an implementation handoff, not installed runtime classes or dead ports.

Two current visibility seams also need bounded promotion: `ConsumedEconomicEvidenceSnapshot.canonicalManifest` is internal to the operations module, so the PostgreSQL writer cannot call it today. Add a fresh-byte `canonicalManifestForPersistence` bridge following repository valueForPersistence conventions only in the eligible writer tranche. Historical reconstruction needs a versioned typed rehydration factory that accepts stored members/roles/coverage/outcome/context and validates them without invoking assembly or calculation; the current private snapshot constructor/Input.finalize seam cannot be misused to recalculate old outcomes. Neither bridge is added as unused runtime infrastructure in this design-only tranche.

Producer integration is one publication call after snapshot finalization; the old projection-only materialization call must not execute additionally. Before reading/assembling on replay, resolve an existing published trigger internally and verify its frozen history. If missing and current trigger covers it, return the verified current winner as Superseded without claiming an unpublished historical revision. The current in-memory observer must not become a durable sink. No migration is eligible before this composition cutover and legacy-row treatment are reviewed together.

## Pre-write validation

Validate identical organization/order, full subject scope, read evidence version, trigger sequence, both policy versions, projectedAt and typed outcome between snapshot and record. Validate complete member set, kinds/families/recorded times, correction endpoints and context roles against the captured aggregate membership. Frozen coverage must match the typed calculation's missing/partial lists; no COMPLETE from the current partial-only assembler.

Compute canonical manifest bytes/digest again; compare to the immutable snapshot. Strictly encode/decode the frozen payload with codec version 1 and verify round-trip equality under canonical collection ordering. Nested component UUID/type/direction, money currency/amount, source kind/system/reference shape, occurrence time and quality are validated through existing typed domain constructors. Complete market/external identity/currency must match the subject. Reasons, missing/partial lists and components have no duplicates. Reject unknown or extra JSON keys at every nested object, null required scalars, guessed UUIDs, wrong subject/currency, invalid decimals/enums/timestamps and incompatible calculation policies. Require whole-microsecond time before JDBC conversion (do not silently round). Do not call current assembler/calculator on historical decode.

Same publication key compares all frozen canonical bytes (not only SHA-256), manifest versions/digest, subject, read version, trigger, policy context, projectedAt and normalized typed outcome. Canonical collection ordering is semantic equality; a changed member version/kind/role or policy/value is different context. A timestamp generated during a new attempt is not silently substituted for the published timestamp.

## Owned transaction pseudocode

```kotlin
// Future implementation plan only. No runtime writer is claimed here.
validateSnapshotAndProjection(snapshot, record)
connection().use { owned ->
    owned.autoCommit = false
    owned.transactionIsolation = Connection.TRANSACTION_READ_COMMITTED
    try {
        // Stable existing subject serializes first writers too, unlike absent V018 row.
        requireOne(lockSubjectForPublication(owned, organizationId, orderId))
        // Exact SQL: SELECT ... FROM marketplace_economic_evidence_subject
        // WHERE organization_id=? AND marketplace_order_id=? FOR NO KEY UPDATE
        // Ingestion's root lock is compatible in ordering, not concurrent ownership.
        // No assembler/calculator/provider call while this lock is held.
        validateTriggerMetadata(owned, subject, trigger, triggerUpdateVersion, triggerKind)
        val duplicate = readPublishedTrigger(owned, subject, trigger)
        if (duplicate != null) {
            verifyFrozenHistoricalRevision(owned, duplicate)
            requireExactFrozenEquality(duplicate, snapshot, record) // otherwise INTEGRITY_CONFLICT
            owned.commit()
            return IdenticalPublished(duplicate.projectionRevision)
        }
        val current = readCurrent(owned, subject) // same connection; NULL is first publication
        if (current != null && current.trigger >= trigger) {
            verifyLinkedCurrentOrLegacyScope(owned, current)
            requireCurrentBoundaryCoversTrigger(owned, current, triggerUpdateVersion)
            owned.commit()
            return SupersededByCurrent(current) // no header/member/receipt inserted
        }
        if (current != null && snapshot.readEvidenceVersion < current.readVersion) {
            owned.rollback()
            return IntegrityConflict // later trigger with older read boundary
        }
        val revision = insertHeaderReturningGeneratedRevision(owned, snapshot, codecV1)
        failureHook(AFTER_HEADER)
        snapshot.members.forEachIndexed { index, member ->
            insertMemberExactlyOnce(owned, revision, member) // require update count == 1
            failureHook(if (index == 0) DURING_FIRST_MEMBER else DURING_LATER_MEMBER)
        }
        snapshot.members.filter { it.observation.identifierKind == CORRECTION }.forEach { member ->
            // Extract exact supersedesObservationId/replacementObservationId from metadata;
            // recover target's own version from the captured member set, not current version.
            insertCorrectionExactlyOnce(owned, revision, member.observation)
            failureHook(DURING_CORRECTION_EDGE)
        }
        insertNormalizedReasonsAndCoverage(owned, revision, snapshot)
        failureHook(DURING_OUTCOME_DETAIL)
        failureHook(BEFORE_CURRENT_UPDATE)
        // Test instrumentation inside upsertCurrent alters a bound FK parameter or makes
        // executeQuery raise SQLException at DURING_CURRENT_UPDATE, after input validation.
        requireOne(upsertCurrent(owned, record, revision, failureHook)) // strict trigger + non-regressive read guard
        // Database current trigger creates receipt and checks pointer/header equality.
        failureHook(AFTER_CURRENT_UPDATE_BEFORE_COMMIT)
        forceDeferredConstraints(owned) // SET CONSTRAINTS ALL IMMEDIATE, still inside transaction
        // Verify exact receipt/current link and persisted manifest/member/outcome round-trip.
        verifyNewPublication(owned, revision, snapshot, record)
        owned.commit()
        return Published(revision)
    } catch (error: Exception) {
        rollbackPreservingOriginalFailure(owned, error)
        throwOrMapIntegrityFailure(error)
    }
}
```

`FOR NO KEY UPDATE` on the stable scoped V015 root serializes same-subject publishers even with no V018 row. It also contends with ingestion's root `FOR UPDATE`, intentionally for the short write window; assembly occurs before the lock. One subject per transaction avoids multi-subject lock inversion. READ COMMITTED is selected so a publisher that waits for another publisher sees its committed header/current state in subsequent statements. A REPEATABLE READ transaction started before waiting could keep an obsolete snapshot; do not use a stale snapshot to accept a race-loser publication. Publication never rereads the aggregate to replace the supplied frozen snapshot. It may verify its exact durable member boundary through immutable V015 rows. New ingestion after materialization is permitted coalescing context, not a reason to relabel the old read version.

`upsertCurrent` must have no independent connection or commit. A zero row result under the owned subject lock is an unexpected failed transition: roll back the inserted header/details; do not return legacy NoOpAlreadyCurrent while leaving candidate history. An out-of-contract concurrent legacy writer is blocked by the V018 historical-link trigger at cutover. SQL-state errors/constraint failures are not suppressed to achieve success. Serialization/deadlock retries are bounded and rerun the entire transaction with the same frozen candidate; a divergent already-published key fails. Lost COMMIT response is an ambiguous outcome, not automatic rollback proof: resolve the exact publication key on a fresh owned read and compare frozen context before acknowledgement/retry.

## State machine and checkpoint results

| State under subject lock | Result | Historical effect | Checkpoint |
|---|---|---|---|
| Exact key + all frozen context identical | IdenticalPublished | Reuse stored revision | May advance |
| Exact key + any frozen context differs | IntegrityConflict | No writes | Do not advance |
| No key; current trigger >= incoming; current read covers trigger update | SupersededByCurrent | No candidate history | May advance after winner verification |
| No key; incoming newer; read below current read | IntegrityConflict | No writes | Do not advance |
| No key; incoming newer; read equal/newer | Published | Header/details/current/receipt commit together | May advance after commit |
| SQL failure or forced deferred failure | IntegrityFailure | Roll back all new effects | Do not advance |
| COMMIT acknowledgement lost | Unknown until exact reconciliation | Never infer absent/present | Hold until resolved |

No-op/current coverage is not historical idempotency. An ordinary processor retry first resolves stored context and does not construct a new candidate; direct candidate submission under the same key must compare exactly. Namespace comparisons are trigger-to-trigger and evidence-version-to-evidence-version only; N=9/M=7 is perfectly valid.

## Writer race outcomes

A=(trigger 9, read 7), B=(trigger 10, read 8), same organization/order:

- A takes root lock first: A commits revision/receipt/current 9/7. B then sees A, commits B and current 10/8. Both revisions were accepted publications; both receipts survive.
- B takes root lock first: B commits 10/8. A sees current covers its genuine trigger and returns Superseded; no A header or receipt exists.
- A=(9,8), B=(10,7): A first makes B a regressive IntegrityConflict. B first may validly publish 10/7, then A is stale and creates no history; current is 10/7. A's higher read version does not override the newer trigger. A later genuine trigger must refresh to a non-regressive boundary.
- Two candidates for N: same frozen context gives one publication plus IdenticalPublished; different read version, policy, outcome, members or time gives one publication plus IntegrityConflict. Do not recompute a race loser into silent success.
- Different subjects use different root locks. Tenant and order scope are part of every lock/query/FK; no global order lock or guessed UUID lookup.

No candidate is committed before publication. Rollback includes receipt created by the V018 trigger. Old receipts keep publication proof when current advances; header insertion alone proves nothing.

## Failure injection and executable test handoff

Do not add disabled tests that pretend to exercise a nonexistent writer. The following future `PostgresMarketplaceSalesIntelligenceLineagePublicationRepositoryTest` matrix has exact seams and oracle queries; it becomes runnable only with the qualified migration/writer. Hooks are package-internal constructor instrumentation defaulting to no-op, never HTTP/environment switches. Tests must inject both logical exceptions and real JDBC constraint failures.

For each of the eight failure points in pseudocode: use a fresh order; capture all six historical table counts and current row; execute publication with that single hook failing; read using an independent connection after method completion; assert header/member/edge/reason/coverage/receipt counts unchanged and current row byte-for-byte/context unchanged. Repeat with an existing prior published revision and verify it is readable, immutable and still pointed to. DURING_LATER_MEMBER needs >=2 members; DURING_CORRECTION_EDGE needs a valid correction chain. AFTER_CURRENT_UPDATE_BEFORE_COMMIT must observe in-transaction receipt before throwing and prove it disappears externally. Add a deferred-constraint violation that appears only at SET CONSTRAINTS/COMMIT. Verify one Connection acquisition and no helper commit via a JDBC event recorder; this is ownership proof only, not a substitute for database rollback assertions.

| Future test | Required independent database oracle |
|---|---|
| unresolved R1 -> later Ready/Incomplete R2 | Both frozen outcomes/bytes persist; R1 still unresolved; no fake zero/observation |
| unresolved -> Complete | Legitimate accepted complete-coverage policy fixture; current policy cannot produce it, so mandatory case remains blocked until that fixture is justified |
| F1 -> correction -> F2 | R1 active F1; R2 superseded F1/active F2/exact correction edge; old policy/outcome untouched |
| exact duplicate | One header/receipt; exact returned ID and all frozen context equal |
| divergent duplicate | INTEGRITY_CONFLICT; no candidate header/current transition |
| A-first/B-first and simultaneous writers | Root-lock barriers; receipts according to accepted ordering; no orphan race loser |
| foreign organization / wrong order | Composite FK rejection and scoped internal-read absence; no attachment/existence leak |
| wrong member version/kind/family | V015 tuple FK/deferred exact source check rejection |
| correction half-edge / wrong revision / self-edge | NOT NULL/check/FKs/deferred exact source edge reject |
| immutable history / late detail append / truncate | Normal DML rejects; no production-role provisioning |
| policy change with new genuine trigger | New revision/receipt; old policy/outcome unchanged; same trigger changed policy conflicts |
| pointer mismatch | Wrong header, org/order, trigger/read/policy/time/state/payload each rejects |
| header without publication | Deferred receipt requirement aborts commit |
| all eight hooks + deferred failure | No partial committed effects; prior revision remains |
| lost COMMIT response | Resolve exact existing key/context; no second divergent publication |
| legacy NULL pointer | No invented backfill; new transitions require linked revision; historical read fails closed |
| no live provider / assembler during historical read | Mock spies fail if called; decode stored snapshot and verify manifest only |

## Internal historical read

The future port exposes only typed internal `findHistoricalRevision(subject,revision)` and `findPublishedRevisionForTrigger(subject,trigger)` results: Found, NotFound, IntegrityFailure. No raw HTTP endpoint. One REPEATABLE READ connection loads header, receipt, members, edges and normalized claims; verifies scope, complete exact V015 boundary, source metadata, normalized outcome and versioned codec; reconstructs frozen snapshot from stored values, computes canonical bytes/SHA-256 and compares both to stored values. Decode policy versions as stored, do not execute their current code. Missing receipt/source/member, unsupported codec/manifest format, NULL legacy link or inconsistent payload is integrity failure, not empty lineage. A foreign organization cannot distinguish a revision owned by another tenant through this port.


## Test fixture cutover constraint

The current projection test class resets with TRUNCATE integration_organization CASCADE and writes through the projection-only adapter. Neither is compatible with the future append-only/sealed history and mandatory linkage triggers. Keep present qualification on unchanged V001-V042. In the eligible historical tranche, use a fresh disposable database/container per historical test or unique organization/order fixtures without TRUNCATE, and update publication tests to the history-aware input. A separately scoped legacy test may explicitly target the old schema solely to qualify its old contract; it must not be reported as new historical schema PASS or used to bypass Package 0090 deployment order. Do not disable triggers or mutate history for test cleanup. Current-row DELETE/TRUNCATE/key movement must be tested as rejected because the current row preserves the publication monotonic floor.


## Implemented proof mapping

The earlier pseudocode is now realized by PostgresMarketplaceSalesIntelligenceLineagePublicationRepository. MarketplaceSalesIntelligenceStateCodecV1 is the bounded extraction of the existing codec, not a second serialization system. Snapshot canonicalManifestForPersistence and rehydratePersisted are installed with validation/defensive copies. No public API route, runtime mode switch or ordinary composition invokes the writer.

The writer uses one explicit owned connection and stable scoped root lock; helpers never acquire/commit separate connections. It validates the trigger boundary, frozen input/record equality, complete stored context and byte/digest equality, then writes all details/current receipt atomically and forces deferred checks. Header/current/receipt verification precedes commit. Concurrent newer-first loses no candidate history; older-first records only accepted intermediate publication. Legacy current coverage resolves genuine durable subject/trigger/read context without claiming a historical backfill. Commit acknowledgement loss returns CommitOutcomeUnknown and is reconciled by exact stored-key lookup; this is distinct from proved pre-commit rollback.

All eight failure points, deferred orphan rejection, real lock-waiting independent backends, duplicate races, scoped SQL attacks, mutation/pointer attacks and controlled corruption are [executed](../evidence/ROOM-V2-disposable-postgres-historical-lineage-proof.md). Current producer Complete is unreachable; current acceptance uses legitimate Ready/Incomplete history, and future Complete-policy qualification remains an extension obligation. The candidate exists only in test resources, never production Flyway locations.
