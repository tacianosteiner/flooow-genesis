# Room V2 — producer lineage architecture audit

Date: 2026-10-12. Baseline: `405a521f9e4093d1fcdcf35d10c92890d4e37221`. Status: **BLOCKED_WITH_EVIDENCE for runtime lineage implementation**.

## Actual data path

`V015 marketplace_economic_evidence_update` and the fact/attempt/correction tables → `PostgresMarketplaceIndependentEconomicEvidenceRepository.find` (repeatable-read replay of all updates, exact sequential versions) → `VersionedMarketplaceIndependentEconomicEvidence` (aggregate + current version) → `MarketplaceSalesIntelligenceProjectionProcessor.materializeChange` → `MarketplaceEconomicTruthAssembler.assemble` (active occurrence and components) → `MarketplaceEconomicTruthCalculator.calculate` when ready → `MarketplaceSalesIntelligenceProjectionRecord` → `PostgresMarketplaceSalesIntelligenceProjection.materializeIfNewer` (one V018 upsert) → `SalesIntelligenceApi.recordJson` → Room.

The feed and checkpoint are separate calls around per-change materialization. The processor skips a change when current projection `lastAppliedChangeSequence >= change.changeSequence`; otherwise it loads the **latest** subject evidence, not an evidence snapshot pinned to the feed event. The resulting `sourceEvidenceVersion` is the version actually read. The feed checkpoint advances after the batch; it is not in the V018 upsert transaction.

## Identity availability at the capture point

| Datum | At repository replay | At processor before assembly | At assembler result / V018 |
|---|---|---|---|
| Observation UUID and subject | `AVAILABLE_IN_MEMORY` and durable V015 | `AVAILABLE_IN_MEMORY` in aggregate facts/attempts/corrections | `AGGREGATED_AWAY` |
| Per-observation version and kind | `AVAILABLE_IN_MEMORY` while replaying V015 update row | `AVAILABLE_IN_REPOSITORY_ONLY`; returned aggregate has no per-member version/kind | `AGGREGATED_AWAY` |
| Family and observed time | `AVAILABLE_IN_MEMORY` on facts | `AVAILABLE_IN_MEMORY`; attempts use attempted time | `AGGREGATED_AWAY` |
| Source kind/system/reference | `AVAILABLE_IN_MEMORY` on applicable facts | `AVAILABLE_IN_MEMORY`; absent for some contexts | `AGGREGATED_AWAY` |
| Correction supersedes/replacement edge | `AVAILABLE_IN_MEMORY` | `AVAILABLE_IN_MEMORY` | `AGGREGATED_AWAY` |
| Aggregate evidence version | `AVAILABLE_IN_MEMORY` | `AVAILABLE_IN_MEMORY` | Retained as `sourceEvidenceVersion` only |
| Assembly reason / calculated result | `NOT_PRODUCED` | Produced after assembly/calculator | V018 state retained; exact member lineage absent |

`UNRESOLVED` arises from assembler reasons: no active occurrence, multiple distinct occurrence times, or inconsistent active components. Attempts may coexist but are not individually proven causes of these reasons. `CALCULATED_INCOMPLETE`/`CALCULATED_COMPLETE` begin with an assembled order from active occurrence/component values; calculator and policy determine complete/partial/missing result. The assembler discards observation IDs when it maps components. The producer still has the aggregate locally, so the right capture point is before/around assembly, with a typed versioned member manifest supplied by the repository.

## Historical and atomic gaps

V018 has one mutable `(organization_id, marketplace_order_id)` row and `ON CONFLICT ... DO UPDATE` if the new change sequence is greater. There is no stored historical projection revision or consumed-member set. V015 replay preserves source changes but does not prove which version a prior processor invocation read or what outcome that policy produced. `materializeIfNewer` opens a connection and executes one upsert with default autocommit; adding a second independent lineage write would permit projection/lineage split-brain. The future writer must own one transaction and an immutable revision linked to the current row. Duplicate/concurrent replay needs a manifest equality rule. The current processor may read version M>N while processing feed change N; event sequence and read version cannot be conflated.

## Gate disposition

`CLAIM_TAXONOMY_DEFINED=YES_DESIGN`: order assembly state and component coverage state; economic result/reconciliation remain later subsets. `CLAIM_GRANULARITY_DECISION=IMMUTABLE_PROJECTION_CONSUMED_SET_PLUS_TYPED_OUTCOME`, without unsupported per-item causal claims. `HISTORICAL_PERSISTENCE_REQUIRED=YES`. `ATOMICITY_MODEL=ONE_TRANSACTION_REQUIRED_NOT_PRESENT`. `REPLAY_MODEL=HISTORICAL_RECORDED_CONTEXT_REQUIRED`. `CORRECTION_MODEL=APPEND_NEW_REVISION_KEEP_OLD`. `OBSERVATION_ID_AVAILABLE_AT_PRODUCER=YES`; `PER_OBSERVATION_VERSION_AVAILABLE_AT_PRODUCER=NO_CURRENT_INTERFACE`. `LINEAGE_IMPLEMENTATION_READY=NO`, `LINEAGE_IMPLEMENTED=NO`, `LINEAGE_PERSISTED=NO`, `LINEAGE_HISTORICAL_PROOF=NO`.

This gate does not claim a runtime defect in the existing current-state projection. It blocks promotion to historical claim lineage until [ADR-0091](../adr/ADR-0091-economic-projection-consumed-evidence-lineage.md) and [SPEC-0091](../specifications/SPEC-0091-economic-projection-consumed-evidence-lineage.md) are satisfied. No migration, database or runtime execution occurred.
