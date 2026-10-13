# Room V2 — disposable PostgreSQL historical lineage proof

Date: 2026-10-13. Branch: `feature/room-v2-executive-product-evolution`.
Baseline: `8b96e98c6246e462edd8835393088ee4fcafb0ed`.

## Evidence classification

DESIGN: accepted historical lineage blueprint and atomic publication contract.
COMPILED: native snapshot, shared versioned state codec, uncomposed PostgreSQL writer and internal historical reader.
EXECUTED: domain, PostgreSQL and API tests passed.
POSTGRES-PROVEN: candidate DDL, transactional publication, immutable historical reads, rollback, idempotency and concurrent publication were exercised in disposable PostgreSQL.
NOT-PRODUCTION-MIGRATED: no numbered migration, shared database execution, runtime composition, retrieval endpoint or UI was added.

## Environment and isolation

Docker Engine server `29.6.2`; Docker Desktop `4.85.0 (235549)`; context `desktop-linux`; Linux amd64. Testcontainers `2.0.5`; image `postgres:18.4`; observed server `18.4 (Debian 18.4-1.pgdg13+1)`.

Tests created their own containers. PostgreSQL port bindings explicitly use `127.0.0.1` and are inspected before migrations. Existing containers and shared databases were not reused. No Docker daemon, firewall or security settings were changed. The test baseline uses Flyway through V042, then executes the unnumbered resource `applications/marketplace-operations-persistence-postgres/src/test/resources/room-lineage/historical_lineage_candidate.sql` directly. V043 was not executed. The candidate SQL matches the documented blueprint after newline normalization.

## Commands and results

Run from the Room worktree:

```powershell
.\gradlew.bat :applications:marketplace-operations-persistence-postgres:test --tests '*PostgresMarketplaceIndependentEconomicEvidenceRepositoryTest.exact observation lineage*' --tests '*PostgresMarketplaceIndependentEconomicEvidenceRepositoryTest.multiple durable facts*' --tests '*PostgresMarketplaceSalesIntelligenceProjectionTest.coalescing writer*' --tests '*PostgresMarketplaceSalesIntelligenceProjectionTest.dual monotonic guard*' --tests '*PostgresMarketplaceSalesIntelligenceProjectionTest.coalescing trigger*' --console=plain
.\gradlew.bat :applications:marketplace-operations:test :applications:marketplace-operations-persistence-postgres:test --tests '*PostgresMarketplaceSalesIntelligenceLineageTest' --tests '*PostgresMarketplaceIndependentEconomicEvidenceRepositoryTest' --tests '*PostgresMarketplaceSalesIntelligenceProjectionTest' :applications:marketplace-operations-api:test --console=plain
.\gradlew.bat :applications:marketplace-operations-persistence-postgres:test --tests '*PostgresMarketplaceSalesIntelligenceLineageTest' --console=plain
python scripts/room_lineage/verify_historical_blueprint.py --parser-path C:\Users\xmz_r\AppData\Local\Temp\room-lineage-sql-parser
```

The five retained targeted tests passed in 31 seconds. The full relevant campaign succeeded in 114 seconds: domain 529; PostgreSQL 56 (independent repository 23, current projection 15, historical lineage 18); API 69. All had zero failures, errors or skips: 654 distinct test methods, without adding repeated runs to the count. The API task was up to date in the final campaign following its successful prior execution. After additional financial-component and F1→F2→F3 assertions, the focused 18-test lineage campaign passed again in 24 seconds (aggregate test time 18.835 seconds). Runtime code did not change after the full campaign.

Static parsing passed with pglast v8.5: 41 statements, six functions, 13 foreign-key declarations and aligned declared target types. The script labels its own work `POSTGRES_EXECUTION=NOT_PERFORMED`; actual database execution is evidenced by the separate Testcontainers tests.

## Database proof

The catalog test verifies actual columns, nullability, key targets and types, six primary keys, five unique keys, 13 foreign keys, 26 triggers (including six deferred constraint triggers), identity settings and the current-pointer index. Candidate constraints were not weakened to make tests pass.

The real writer acquires one connection, disables autocommit, locks the scoped subject, writes the frozen revision and exact members, correction edges and normalized outcome, updates V018 and receives a database-owned publication receipt, validates deferred constraints and commits. The test counts acquisitions and transaction actions. No legacy helper with a second connection is called by this writer. The normal application composition does not instantiate it.

Exact duplicate publication returns the existing revision. Changed policy, outcome, member timestamp, materialization timestamp or read boundary under the same trigger fails integrity. Eight precommit injection positions preserve all historical tables and the previous current projection, including failure after receipt creation but before commit. A simulated lost commit acknowledgement actually commits first and returns `CommitOutcomeUnknown`; retry reconciles to the same immutable revision. This case is not represented as a rollback.

Independent PostgreSQL backend sessions exercise both A-first and B-first lock races, with the waiting backend observed in `pg_stat_activity`, plus simultaneous identical publication. Current state never regresses and only winners receive receipts.

Cross-tenant/order reads reveal no existence; mismatched publication scope fails. Direct SQL wrong member kind/version/scope, invalid correction endpoints, self/half edges, wrong source family, orphan revisions, receipt forgery, current-pointer removal and identity moves fail and roll back. Published rows reject UPDATE, DELETE, TRUNCATE and late members/edges. A disposable privileged corruption test temporarily disables one immutable-header trigger, corrupts the digest, restores the trigger before commit, verifies historical integrity rejection and verifies subsequent UPDATE rejection. Database owners capable of disabling triggers remain trusted administrators, not an adversarial security boundary.

## Historical semantics and limits

The internal reader uses stored frozen data and the versioned codec, not the current assembler or calculator. It validates canonical manifest bytes and SHA-256, exact member bindings, correction edges, source families, normalized reasons/coverage and receipt. Financial partial components round-trip with their native typed values. Unknown codec fields, malformed values and duplicate typed reason lists fail closed.

The legitimate producer transitions from unresolved to Ready/Incomplete. Current `assembly/1` emits PARTIAL for present economic evidence and MISSING for absent evidence; it cannot produce Complete. Therefore unresolved-to-Complete is **NOT_APPLICABLE_TO_CURRENT_PRODUCER_POLICY**, not a fabricated proof or an engineering blocker. Standalone calculator capability does not establish producer reachability. No coverage rule, monetary policy or result was changed to force Complete.

Correction revisions preserve F1→F2→F3, prior manifest digests and exact contextual roles. Valid legacy current rows retain NULL historical linkage until a genuine new publication; no historical backfill is invented. Invalid legacy read boundaries fail closed.

## Governance gate

Engineering qualification: YES, disposable scope. Production promotion: HOLD.
The 293-ref audit found V043 owned only by local/remote `checkpoint/package-0090-cloud-handoff`; main remains through V042. No version was allocated or reserved, and no out-of-order/cherry-pick migration behavior was introduced.

One production blocker remains: canonical migration-slot and release-order coordination with Package 0090, followed by explicit production schema promotion review. No unresolved high, medium or low findings remain within this bounded disposable proof. Main, Package 0090 and global commerce research refs/worktrees remain unchanged. Raw evidence retrieval, operational Room, execution and recovery authority remain blocked.

Next technically determined action: coordinate the canonical migration slot and release order, then review production schema promotion. This proof does not execute that next action.
