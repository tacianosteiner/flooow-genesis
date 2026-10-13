# ADR-0091 — Economic projection consumed-evidence lineage

Status: **accepted design; disposable PostgreSQL engineering proven; production schema HOLD**. Date: 2026-10-12. Follows [ADR-0090](ADR-0090-governed-raw-evidence-reference.md). The in-memory producer foundation is implemented under this contract. No migration, retrieval endpoint or Room execution authority is granted.

## Decision

Capture an immutable **projection revision → exact consumed evidence snapshot** at the Sales Intelligence producer, before `MarketplaceEconomicTruthAssembler.assemble`. Keep typed domain claim outcomes alongside that snapshot, but do not label every consumed observation as individually causal. Current Decision Pressure needs `ORDER_ASSEMBLY_STATE` (including typed not-ready reasons) and `COMPONENT_COVERAGE_STATE` (missing/partial component types). `ECONOMIC_RESULT` and reconciliation claims require later contribution-level proof. English Room copy is never a persisted claim key.

The snapshot must separate active facts, superseded facts, correction relations and collection attempts. `CONSUMED_ACTIVE_FACT`, `CORRECTION_CONTEXT` and `ATTEMPT_CONTEXT` are context roles; `SUPPORTS` or `CONTRADICTS` may be emitted only by an evaluator that actually proves that relationship. In particular, an unresolved missing occurrence is a conclusion over a complete versioned aggregate, not a fact that one attempt alone proves. A missing component is an absence claim over the enumerated active set and declared coverage policy, not an invented observation.

## Producer path found

Baseline finding before commit `7300df0`: `PostgresMarketplaceIndependentEconomicEvidenceRepository.find` replays V015 updates in version order and returns `VersionedMarketplaceIndependentEconomicEvidence(evidence, currentVersion)`. The aggregate still holds historical facts, active facts, attempts and corrections with observation UUIDs. The repository's replay knows each update version while iterating, but its returned model discards the **per-observation** version and change-kind mapping. `MarketplaceSalesIntelligenceProjectionProcessor.materializeChange` loads that aggregate, calls the assembler, optionally calculates the order, and constructs a current projection record. The assembler maps active occurrence/component observations into order values and typed reasons, dropping observation identity. [SPEC-0091](../specifications/SPEC-0091-economic-projection-consumed-evidence-lineage.md) defines the required typed snapshot.

## Historical and atomic model

Current V018 stores one mutable row per organization/order; it is not historical projection storage. V015 event history can replay evidence but cannot by itself reconstruct what a prior projector run **actually saw**, its selected policy code, projection timestamp or exact result after later updates. An append-only projection-revision header plus normalized observation bindings is therefore required. The header must retain projection state and policy context, read evidence version and change sequence; each binding must retain observation UUID, its own evidence version, kind and contextual role. A future current-projection pointer may reference that immutable revision.

One PostgreSQL transaction must insert revision header, all bindings and the current projection transition when the transition is published. No projection-only or orphan-lineage commit is valid. The processor checkpoint may remain a separate operation only if replay is idempotent and verifies exact revision/context equality before treating a stale retry as success. Later evidence/correction creates a new revision; old revisions remain immutable. A duplicate delivery with the same revision key but different manifest is an integrity conflict, not a no-op.

## Alternatives considered

- Binding each displayed claim to every order observation would claim unsupported causality and was rejected.
- Claim-only subsets are attractive for retrieval, but current assembler does not retain observation-level causality for all states. Deferred until proven.
- Deriving old lineage from latest aggregate and `sourceEvidenceVersion` was rejected: a version does not identify the precise consumed set or old policy/result.
- Embedding one opaque JSON lineage blob in mutable V018 was rejected: it weakens FK validation, queryability, append-only history and per-binding checks.
- The selected model is one immutable consumed snapshot plus typed claim outcomes, with later precise subset bindings only where the evaluator proves them.

## Implementation gate

The repository now returns exact versioned identifier membership alongside the authoritative aggregate. The producer captures an immutable in-memory consumed boundary and typed outcomes. Historical persistence remains `PERSISTENCE_IMPLEMENTATION_READY=NO`: V043 is already occupied by Package 0090; no new slot is allocated, the normalized historical DDL is not yet finalized, and transaction rollback/idempotency proof is absent. PostgreSQL integration tests compile but cannot execute on this host because Docker is unavailable. See [foundation evidence](../evidence/ROOM-V2-economic-claim-lineage-foundation.md).

### Read and publication decision

Choose intentional **coalescing current reads**. A feed sequence is an invalidation trigger, not a version selector and not evidence causality. V015 `find` already owns a REPEATABLE READ transaction: root and durable replay/identifier tuples belong to one consistent database snapshot. It may read version M after trigger N was fetched, and records both independently. Reject reads below the triggering update version or the previously observed current projection version. No as-of repository port exists; using `findUpdate` alone would not give a complete historical aggregate. Adding pinned aggregate replay would increase the read contract and reconstruction cost without preserving the current producer semantics. Coalescing uses the existing consistent aggregate boundary and avoids pretending N produced M.

Publication must be monotonic in both trigger sequence and read evidence version. V018's guarded upsert now requires a strictly newer trigger AND a non-regressive evidence version. A newer trigger attempting a lower evidence version is an integrity failure and does not advance the checkpoint. A stale/equal trigger remains a current-projection no-op; this is **not** historical manifest verification. The processor checks subject identity before accepting repository data.

Before publication, retry N may capture the newest consistent version and a new materialization time. After publication, N is skipped without a new evidence read or divergent current transition, even if checkpoint advancement previously failed. A race loser can compute an in-memory candidate but cannot label it published history. Snapshot observers run before publication and are internal test instrumentation, not durable sinks. Atomic historical persistence must resolve the published revision before re-reading, retain the original frozen context, and reject divergent submitted duplicates. Existing V018 alone cannot perform that manifest comparison. Policy changes need a new governed reprojection trigger or later explicit revision lifecycle; they cannot bypass the already-applied trigger guard.

Organization scope comes from the existing subject and authenticated read path; no frontend ID or URL is accepted. This lineage explains a derived projection and does not redefine canonical Economic Truth, authorize retrieval, recovery or execution, or equate financial ledger IDs with economic observation IDs.


## 2026-10-13 historical persistence contract closure (design only)

The retained three PostgreSQL cases again failed Docker initialization; no SQL assertion executed. Testcontainers dependency is present, daemon/disposable ownership unavailable, and no service was started. Expanded tests cover all guard directions, both publication orders, exact SQL identifier tuples and loopback-only container bindings. Compile success is not database PASS.

Select the [exact DDL blueprint](../specifications/SPEC-0091-historical-lineage-ddl-blueprint.md) and [atomic publication contract](../specifications/SPEC-0091-historical-lineage-atomic-publication.md): global database-generated positive bigint identity, unique org/order/trigger publication key, one role per member under the current taxonomy, separate exact correction edges, normalized reasons/coverage and immutable versioned existing calculation payload. Full canonical bytes plus SHA-256 bind frozen context. Database-owned receipts retain actual publication proof after the current pointer advances; candidate headers without a receipt fail deferred validation. Legacy NULL pointers remain explicitly unlinked, with no fictional backfill.

Choose short READ COMMITTED publication transactions locking the scoped existing subject FOR NO KEY UPDATE, then duplicate resolution, member/outcome inserts, guarded V018 publication and receipt, forced deferred checks and commit. All helpers use that same connection. Current autocommit diagnostic reads and internal snapshot visibility cannot simply be reused; exact extraction/persistence bridges are recorded for the eligible implementation tranche, with no unused runtime abstraction added now.

[Migration coordination evidence](../evidence/ROOM-V2-historical-lineage-migration-coordination.md) records V043 ownership and its unconditional execution interlock. No approved parallel sequencing/reservation mechanism was found. An unnumbered coordination artifact is selected; V044 is not reserved and neither Package 0090 nor Flyway configuration is changed. Filename merger alone would not resolve the interlock.

DDL, identity, idempotency, race and rollback models are ready as reviewed design; PostgreSQL execution and migration slot remain NO. The actual producer cannot currently yield Complete because its assembler emits PARTIAL/MISSING; the mandatory historical Complete case cannot be faked and needs a legitimate accepted policy fixture before historical proof PASS. HOLD remains accurate. See [qualification evidence](../evidence/ROOM-V2-postgres-historical-lineage-gate.md).


## 2026-10-13 disposable PostgreSQL qualification and current-policy acceptance

The new authorized proof tranche explicitly separates disposable schema execution from production migration allocation. The exact blueprint executes as an unnumbered test-only resource after V001-V042 in a fresh loopback Testcontainer; V043 is not loaded. Foundation tests now execute successfully. See [executed proof](../evidence/ROOM-V2-disposable-postgres-historical-lineage-proof.md). Earlier environment HOLD statements above record their checkpoints and are not the latest result.

The history-aware writer, strict shared V018 codec and typed stored-snapshot rehydration are implemented and tested directly. The writer is not constructed in normal application composition. One owned connection/transaction publishes header, members, edges, normalized outcomes, V018 pointer and database receipt, validates deferred constraints and verifies frozen bytes. Duplicate equality, divergence, all eight rollback points, real overlapping backend locks, tenant/subject attacks, immutability and corruption rejection are PostgreSQL-proven. Lost COMMIT acknowledgement returns CommitOutcomeUnknown; exact-key reconciliation is required, never an inferred rollback.

Current-policy acceptance requires legitimate NOT_READY -> READY/INCOMPLETE history and correction preservation. That transition is PostgreSQL-proven. MarketplaceEconomicTruthAssembler assembly/1 marks every present component PARTIAL and every absent type MISSING, so its Ready order always makes calculator/1 return Incomplete. Complete remains supported by the standalone calculator for explicit complete/not-applicable coverage, but is not reachable from this production evidence producer. Therefore unresolved-to-Complete is NOT_APPLICABLE_TO_CURRENT_PRODUCER_POLICY and does not block current historical engineering acceptance. A future legitimate complete-coverage producer policy requires its own extension fixture/proof; no production policy or observations were altered to fabricate it.

HISTORICAL_PERSISTENCE_ENGINEERING_READY=YES. MIGRATION_SLOT_READY=NO. PRODUCTION_SCHEMA_PROMOTION_READY=NO. Package 0090 V043 ownership/interlock and canonical sequencing remain unchanged; no V044 claim, production migration, production writer composition, retrieval endpoint, UI or execution/recovery authority.

## Canonical conditional release precedence — 2026-10-13

Accept MODEL_A as the bounded technical sequencing decision: Package 0090 must close and promote executable V043 before Room becomes eligible for a freshly audited next migration slot. This does not authorize V043 execution or reserve V044. No approved withdrawal, independent lane or pre-V043 insertion mechanism exists in the audited repository evidence. Current order is BLOCKED by the unconditional V043 fence and latest Package semantic/integrated HOLD. See [exact-ref coordination audit](../evidence/ROOM-V2-canonical-migration-release-coordination.md).

Disposable Room engineering readiness remains YES. Production-schema technical readiness and writer composition remain NO pending the exact production migration identity/ownership/runtime ACL contract, full ordered-chain qualification, matching future-history clients and an excluded fleet cutover from the legacy projection-only writer. The [production promotion plan](../specifications/SPEC-0091-production-schema-promotion-plan.md) defines these gates and deployment rollback limits. No Package, main, runtime, schema or retrieval authority is changed by this decision.
