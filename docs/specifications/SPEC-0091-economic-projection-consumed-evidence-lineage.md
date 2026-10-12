# SPEC-0091 — Economic projection consumed-evidence lineage

Status: **design contract, not migration authorization**. Governs the future producer slice described by [ADR-0091](../adr/ADR-0091-economic-projection-consumed-evidence-lineage.md). Existing `ROOM_OPERATIONAL=false` and all execution/recovery gates remain unchanged.

## Typed claim and snapshot semantics

The minimal domain claim taxonomy is `ORDER_ASSEMBLY_STATE` with exact `READY` / `NOT_READY` and existing `MarketplaceEconomicTruthAssemblyNotReadyReason`, and `COMPONENT_COVERAGE_STATE` with existing component type and `MISSING` / `PARTIAL` / `COMPLETE` where actually computed. The current calculator's complete/incomplete result remains a separate typed projection outcome. `CONTRIBUTION`, `CONTRIBUTION_MARGIN`, `TRUTH_QUALITY`, reconciliation case/stage and specific component value lineage are **not** automatically closed by this first snapshot. Room labels such as “Truth unresolved” are presentation only.

One `ConsumedEvidenceSnapshot` belongs to an exact organization/order/projection revision and contains:

| Field | Type / source | Invariant |
|---|---|---|
| organization and subject | `OrganizationId`, `MarketplaceOrderId`; V015 subject | Both match every observation and V018 projection. |
| read evidence version | `MarketplaceEconomicEvidenceVersion`; repository find | Version of the aggregate actually read; not assumed equal to feed change sequence. |
| trigger change sequence | `ChangeSequenceCheckpoint`; feed event | Positive monotonic cursor whose processing caused the read. |
| assembly/calculation policy | existing typed policy versions; calculation nullable on NotReady | Exact versions used to compute persisted outcome. |
| projection time | microsecond `Instant` | Time of this materialization, not source occurrence time. |
| typed outcome | current V018 state and reasons/result with existing invariant checks | Frozen with revision; never reconstructed from current code without comparing policy. |
| observation members | ordered unique set of `(observationId, evidenceVersion, identifierKind, contextRole)` | Every tuple must resolve to the same V015 organization/order and version; no fabricated observation. |
| correction edges | `(correctionId, supersededObservationId, replacementObservationId)` | Must come from the consumed aggregate and retained V015 rows. |

`contextRole` is one of `CONSUMED_ACTIVE_FACT`, `HISTORICAL_SUPERSEDED_FACT`, `CORRECTION_CONTEXT`, `ATTEMPT_CONTEXT`. These are membership semantics, **not** causal `SUPPORTS` assertions. Family is checked from V015 fact data, with no synthetic family for an attempt. Historical members may be retained for correction explanation without claiming that they contributed to the current calculation. Absence claims require the complete snapshot boundary and policy, not an empty member list treated as proof by itself.

## Proposed normalized persistence shape

Names are reserved for review, not executable DDL: `marketplace_sales_intelligence_revision` (append-only header and typed outcome) and `marketplace_sales_intelligence_revision_observation` (member rows). Header key should be `(organization_id, marketplace_order_id, projection_revision)` with a server-owned positive revision or other explicitly collision-free revision identity. Include read evidence version, trigger sequence, policy versions, projected time, typed state and an independently computed canonical manifest digest. Binding key should include the header key and observation UUID plus context role; the stored observation version/kind must FK to V015 identifier/update identity under the same organization and order. A correction-edge table or normalized edge columns may be required; SQL review must prevent nullable half-edges and cascade deletion of history.

The current V018 row must reference the exact new revision, or an equivalent database-enforced relation must prove which immutable revision it publishes. One transaction inserts header, all members and current V018 transition; failed insert, binding FK, compare-and-swap or projection write rolls all back. No `ON CONFLICT DO NOTHING` may hide a different manifest. Duplicate `(org, order, trigger sequence, read version, policy context)` is idempotent only when the full typed outcome and member manifest match. The current checkpoint advancement remains separately retriable only after the persisted revision is verified.

## Concurrency and replay gate

Current code reads latest evidence after reading a change-feed event. Ingestion can advance the aggregate between those operations. A valid implementation must either establish a transactionally consistent read boundary or explicitly allow coalescing to the later version while recording the actual read version and proving retry behavior. The latter must not silently publish two different snapshots under one revision identity. The accepted approach needs a concrete concurrency test before DDL/code implementation.

Historical retrieval loads the immutable revision and members, validates every V015 tuple and returns the stored outcome/context. Re-running the current assembler is a **comparison experiment**, not a replacement for the recorded old policy/result. Corrections create a later revision whose active set reflects replacement; older revisions retain F1 and correction history remains separately identifiable. Missing/deleted source rows or mismatched versions are integrity failures, not empty evidence.

## Required executable tests before implementation PASS

1. Unresolved absent occurrence with explicit attempt context; later valid fact makes a new complete revision while the old unresolved snapshot remains readable.
2. F1→correction→F2; R1 active set retains F1, R2 active set uses F2 and records the correction edge.
3. Duplicate feed delivery yields one identical revision; divergent replay under same key fails closed.
4. Concurrent evidence ingestion between event read and repository find follows the documented read boundary and records actual version.
5. Fail each header/member/current-projection write in turn; transaction leaves neither orphan lineage nor projection without lineage.
6. Foreign organization, wrong order, wrong version/kind/family and guessed observation ID fail; no cross-tenant existence leak.
7. Policy-version change creates a distinct historical context; old revision remains explainable without using new code semantics.
8. No provider live call, frontend-crafted ID, financial-ledger-ID substitution or raw payload exposure.

No current Room API/UI fields or retrieval endpoint are added by this design.
