# ADR-0091 — Economic projection consumed-evidence lineage

Status: **accepted design; in-memory foundation implemented; historical persistence HOLD**. Date: 2026-10-12. Follows [ADR-0090](ADR-0090-governed-raw-evidence-reference.md). The in-memory producer foundation is implemented under this contract. No migration, retrieval endpoint or Room execution authority is granted.

## Decision

Capture an immutable **projection revision → exact consumed evidence snapshot** at the Sales Intelligence producer, before `MarketplaceEconomicTruthAssembler.assemble`. Keep typed domain claim outcomes alongside that snapshot, but do not label every consumed observation as individually causal. Current Decision Pressure needs `ORDER_ASSEMBLY_STATE` (including typed not-ready reasons) and `COMPONENT_COVERAGE_STATE` (missing/partial component types). `ECONOMIC_RESULT` and reconciliation claims require later contribution-level proof. English Room copy is never a persisted claim key.

The snapshot must separate active facts, superseded facts, correction relations and collection attempts. `CONSUMED_ACTIVE_FACT`, `CORRECTION_CONTEXT` and `ATTEMPT_CONTEXT` are context roles; `SUPPORTS` or `CONTRADICTS` may be emitted only by an evaluator that actually proves that relationship. In particular, an unresolved missing occurrence is a conclusion over a complete versioned aggregate, not a fact that one attempt alone proves. A missing component is an absence claim over the enumerated active set and declared coverage policy, not an invented observation.

## Producer path found

`PostgresMarketplaceIndependentEconomicEvidenceRepository.find` replays V015 updates in version order and returns `VersionedMarketplaceIndependentEconomicEvidence(evidence, currentVersion)`. The aggregate still holds historical facts, active facts, attempts and corrections with observation UUIDs. The repository's replay knows each update version while iterating, but its returned model discards the **per-observation** version and change-kind mapping. `MarketplaceSalesIntelligenceProjectionProcessor.materializeChange` loads that aggregate, calls the assembler, optionally calculates the order, and constructs a current projection record. The assembler maps active occurrence/component observations into order values and typed reasons, dropping observation identity. [SPEC-0091](../specifications/SPEC-0091-economic-projection-consumed-evidence-lineage.md) defines the required typed snapshot.

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
