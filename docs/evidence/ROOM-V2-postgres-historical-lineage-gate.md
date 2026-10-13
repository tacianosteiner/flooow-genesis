# Room V2 PostgreSQL historical lineage gate

Date: 2026-10-13 (client date). Branch `feature/room-v2-executive-product-evolution`. **Design closure only; persistence HOLD.**

## Baseline and environment

Fetch succeeded; Room HEAD/remote exactly `694ff132694f7ad5a3874daa2d81183c1443ae65`; Room worktree clean, diff check PASS, no new commits required audit. Protected refs: main/origin/main `77d482c97a663a527dcacc85036c7577dfc92782`; Package 0090 `a34bcd0782d0b3c6cb895ab08b0ab46701224974`; global-commerce research `27019d7b3093b7a7d9aeb67d0c099756b13e005a`. Existing unrelated worktree dirt was recorded read-only; no repair, stash, reset, clean, branch deletion or history rewrite.

`docker version`, `docker info`, `docker ps -a`, `docker context ls` inspected. Client 29.6.2, context desktop-linux, endpoint `npipe:////./pipe/dockerDesktopLinuxEngine`; server pipe missing. No daemon, container inventory or disposable ownership could be verified. default context uses docker_engine pipe; neither context was changed or switched. No Docker Desktop/service start, firewall/network policy change or Docker security change. Package 0090 runtime/database was never contacted.

DOCKER_DAEMON_AVAILABLE=NO
TESTCONTAINERS_AVAILABLE=YES_DEPENDENCY_ONLY (2.0.5)
EXISTING_DISPOSABLE_POSTGRES_AVAILABLE=NO_VERIFIED
POSTGRESQL_VERSION=NOT_OBSERVED (repository image postgres:18.4)
POSTGRES_QUALIFICATION=BLOCKED_ENVIRONMENT

The existing retained test classes provision their own disposable Testcontainers PostgreSQL and default Flyway resources. No parallel database harness was created. Fixtures now bind 5432 only to 127.0.0.1 with an ephemeral host port and assert the actual inspected host binding before migration. This is per-test-container configuration, not daemon/security/network policy modification; no container actually started here. Full unrelated persistence tests were not run after the retained initialization failures.

## Required assertion coverage

| Requirement | Retained/added executable test source | Execution |
|---|---|---|
| Exact ID, version, kind under scoped subject | Repository exact observation lineage; now compares returned map to actual SQL identifier rows | Environment blocked |
| Multiple members retain own update versions | Repository multiple durable facts | Environment blocked |
| Correction/replacement version semantics | Exact observation lineage: F1 v1, attempt v2, correction and replacement v3 | Environment blocked |
| Foreign org/wrong order | Scoped repository NotFound assertions | Environment blocked |
| New trigger/lower read version | Retained coalescing writer | Environment blocked |
| Old/equal trigger with higher read version | Added six-direction guard matrix | Compiled, not executed |
| New trigger/equal or higher read version | Guard matrix verifies full durable row after every transition | Compiled, not executed |
| A-first and B-first | Added serialized namespace/publication-order matrix; concurrent baseline tests retained | Compiled, not executed |
| Integrity failure cannot advance checkpoint | Processor later-trigger regression test now explicitly asserts checkpoint remains NONE | Domain PASS |

Guard matrix: start current trigger=9/read=7; (10,6) IntegrityFailure; (8,8) NoOp; (9,8) NoOp; (9,7) NoOp; (10,7) Applied; (11,8) Applied. Every iteration reads the complete durable current record and asserts one current row. For equal/stale trigger, a larger evidence version alone never bypasses trigger identity. V018 NoOp is current-state coverage, not historical equality verification.

## Closed design artifacts

- [Exact DDL blueprint](../specifications/SPEC-0091-historical-lineage-ddl-blueprint.md): six immutable tables, scoped/typed FKs, exact member boundary and correction set, normalized reasons/coverage, versioned frozen V018 outcome, full manifest bytes/digest, scoped current pointer and database-owned publication receipt. No candidate history may commit without publication proof. A redundant current-pointer index was removed during review.
- [Atomic publication contract](../specifications/SPEC-0091-historical-lineage-atomic-publication.md): global generated bigint identity; unique org/order/trigger; exact frozen duplicate equality; stable scoped root lock; one READ COMMITTED connection; no hidden helper connection/commit; all eight failure points plus deferred/ambiguous-commit cases; race state machine; internal stored-history read without assembly/calculation.
- [Migration coordination](ROOM-V2-historical-lineage-migration-coordination.md): 293 refs and 34 worktrees audited; V043 owner/interlock confirmed; no central reservation or approved parallel sequencing found; unnumbered coordination artifact, no V044 claim.

The calculated payload intentionally retains an immutable, versioned copy of the existing tested V018 codec, while identity/claims/edges/publication are relational. This avoids duplicating economics or opaque lineage JSON. Strict nested domain decoding and exact byte/digest reconstruction are mandatory in the future trusted writer/read port; SQL structural checks are not falsely described as policy or crypto proof.

## Gate reassessment

POSTGRES_FOUNDATION_QUALIFIED=NO
DDL_CONTRACT_READY=YES_DESIGN_ONLY
REVISION_IDENTITY_READY=YES_DESIGN_ONLY
IDEMPOTENCY_READY=YES_DESIGN_ONLY
TRANSACTION_MODEL_READY=YES_DESIGN_ONLY
RACE_MODEL_READY=YES_DESIGN_ONLY
FAILURE_TEST_PLAN_READY=YES_DESIGN_ONLY
MIGRATION_SLOT_READY=NO
PERSISTENCE_IMPLEMENTATION_READY=NO

No migration/writer/internal historical read is implemented, no historical revision/member/edge/receipt is persisted and no V018 pointer is installed. Compile-safe unused writer ports or disabled placeholder tests were deliberately not added: they would not close a real gate. The exact pseudocode/test oracles are reviewable and mapped to actual composition seams.

## Validation commands and counts

Retained targeted command (run before test-source improvements):

```powershell
.\gradlew.bat :applications:marketplace-operations-persistence-postgres:test --tests '*PostgresMarketplaceIndependentEconomicEvidenceRepositoryTest.exact observation lineage*' --tests '*PostgresMarketplaceIndependentEconomicEvidenceRepositoryTest.multiple durable facts*' --tests '*PostgresMarketplaceSalesIntelligenceProjectionTest.coalescing writer*' --console=plain
```

3 discovered cases; 3 failed initialization; zero SQL assertion bodies executed. All failures identify unavailable Docker (no assertion regression). Gradle FAILED in 6s; aggregate reported initialization time 0.719s. PostgreSQL/container versions not observed. No Flyway migration executed. Retained initialization was not retried repeatedly after known environment failure.

Focused domain command after checkpoint assertion improvement:

```powershell
.\gradlew.bat :applications:marketplace-operations:test --tests '*MarketplaceSalesIntelligenceProjectionProcessorTest' :applications:marketplace-operations-persistence-postgres:compileTestKotlin --console=plain
```

16 domain cases PASS; build SUCCESSFUL in 21s. Latest final command after loopback fixture improvements:

```powershell
.\gradlew.bat :applications:marketplace-operations:test :applications:marketplace-operations-persistence-postgres:compileTestKotlin --console=plain
```

Build SUCCESSFUL in 12s. 527 unique domain tests across 62 classes PASS, zero failure/error/skip; aggregate test time 3.288s. PostgreSQL main/test compilation PASS, including 2 added matrix cases and enhanced retained lineage SQL assertions. Those added DB bodies are unexecuted, not SQL PASS. Final unique verification inventory: 527 passing domain cases, 3 retained DB initialization failures and 2 newly compiled/unexecuted DB cases (5 DB cases blocked); do not sum repeated focused/full domain runs as new unique coverage.

Static DDL command:

```powershell
python -m pip install --disable-pip-version-check --target <temporary-parser-directory> pglast==8.5
python scripts/room_lineage/verify_historical_blueprint.py --parser-path <temporary-parser-directory>
```

Actual parser directory was `C:/Users/xmz_r/AppData/Local/Temp/room-lineage-sql-parser`; no application dependency file changed. pglast v8.5 parsed 41 SQL statements and all 6 PL/pgSQL function bodies; 13 candidate FKs resolve to declared V015/V018/candidate unique targets with matching column types; names are <=63 bytes. Script explicitly reports POSTGRES_EXECUTION=NOT_PERFORMED and DDL_GATE=DESIGN_ONLY. This is a bounded static check, not catalog/transaction/constraint qualification. Git diff and staged diff checks must pass before each commit.

## Adversarial review and residual findings

| Attack/finding | Severity | Disposition |
|---|---|---|
| No Docker or verified disposable PostgreSQL | BLOCKER | Do not start services automatically; SQL qualification NO |
| V043 occupied AND execution-interlocked; no coordinated release order | BLOCKER | No number or migration; unnumbered coordination request |
| Legacy writer opens second connection; current codec/manifest visibility not ready for owned transaction | HIGH | Explicit same-connection helper/codec/typed rehydration handoff; no naive adapter reuse or runtime promotion |
| Mandatory unresolved-to-Complete historical proof not reachable with current partial-only assembler | HIGH | Require legitimate accepted complete-coverage policy fixture before proof PASS; no invented zeros/observations |
| Cross-org/order, wrong tuple version/kind/family | Reviewed | Composite FKs + exact two-way source-boundary comparison; DB tests pending |
| Correction half-edge/wrong version/chain/self-edge | Reviewed | Non-null distinct endpoints, three exact member FKs, exact bounded source-edge set |
| Header without actual publication; race loser orphan | Reviewed | Database-owned receipt + deferred header validation; writer discards stale candidate before inserts |
| Old receipt falsely requires current pointer still equals old revision | Fixed in design | Receipt persists after pointer advance; old history does not depend on current row |
| Erase/move V018 current row to reset publication floor | Fixed in design | Current DELETE/TRUNCATE and subject-key movement reject; future tests cannot clean up immutable history via cascade TRUNCATE |
| Partial rollback/autocommit escape/zero-row publication | Reviewed | Eight exact injection oracles; one connection; zero-row with inserted candidate must roll back |
| Null policy comparison bypass; old trigger/high version; later trigger/regressive version | Reviewed | IS DISTINCT FROM context checks; separate monotonic namespaces; added DB matrix |
| Old history reconstructed using current policy | Reviewed | Stored versioned codec/context/bytes only; no assembler/calculator calls |
| Wrong manifest/unknown nested payload | Reviewed | Trusted writer and read port strict domain/byte/hash validation; not delegated to SQL regex alone |
| Mutable detail or post-publication append/truncate | Reviewed | Immutable/truncate/sealed-insert triggers; privileged owner tampering explicitly outside normal DML guarantee |
| Duplicate same key with different context | Reviewed | Unique org/order/trigger; exact all-context equality or IntegrityConflict; no DO NOTHING |
| Legacy current rows assigned fabricated history | Reviewed | NULL/unlinked preserved; linkage only on a later genuine transition |

BLOCKER_COUNT=2
HIGH_COUNT=2
MEDIUM_COUNT=0
LOW_COUNT=0

## Integrity and next bounded action

Only test sources, the standalone static verification script and SPEC/ADR/evidence artifacts changed. No runtime implementation, API/OpenAPI/UI/provider source, production setting, Flyway resource or authority changed. ROOM_OPERATIONAL=false; execution/recovery blocked; raw retrieval/UI unavailable. No real/shared/Package 0090 DB, live provider call, publicly exposed PostgreSQL or migration execution.

Next: qualify the retained and expanded two full PostgreSQL classes on a verified disposable loopback-only Testcontainers host; record actual versions and assertion counts. Resolve canonical migration sequencing while preserving the V043 interlock, then allocate explicitly after refreshed inventory. Before declaring historical proof PASS, resolve the legitimate Complete fixture and execute candidate DDL/owned writer rollback/race/tenant tests. Do not start this NEXT task after the final report.
