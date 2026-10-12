# ADR-0091 — Economic projection consumed-evidence lineage

Status: **accepted design; implementation HOLD**. Date: 2026-10-12. Follows [ADR-0090](ADR-0090-governed-raw-evidence-reference.md). No runtime, migration, endpoint or Room authority is granted.

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

`LINEAGE_IMPLEMENTATION_READY=NO` now. The producer read result must retain each observation's persisted version/kind, and the read/compute/write consistency window must be specified under concurrent ingestion. The V018 upsert currently uses a single autocommit statement; a transactionally unified writer, immutable revision schema, migration and failure/concurrency tests must be accepted before code changes. An event with change sequence N may load a later current aggregate; equating N to the observed evidence version would be false. The design must record both and decide how a retry of N compares snapshots.

Organization scope comes from the existing subject and authenticated read path; no frontend ID or URL is accepted. This lineage explains a derived projection and does not redefine canonical Economic Truth, authorize retrieval, recovery or execution, or equate financial ledger IDs with economic observation IDs.
