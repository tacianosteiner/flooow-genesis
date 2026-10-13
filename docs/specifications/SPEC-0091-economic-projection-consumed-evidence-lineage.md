# SPEC-0091 — Economic projection consumed-evidence lineage

Status: **in-memory foundation contract; historical persistence HOLD, not migration authorization**. Governs the future producer slice described by [ADR-0091](../adr/ADR-0091-economic-projection-consumed-evidence-lineage.md). Existing `ROOM_OPERATIONAL=false` and all execution/recovery gates remain unchanged.

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

Earlier proposal, superseded in identity/key details by the 2026-10-13 blueprint below. Names were reserved for review, not executable DDL: `marketplace_sales_intelligence_revision` (append-only header and typed outcome) and `marketplace_sales_intelligence_revision_observation` (member rows). Header key should be `(organization_id, marketplace_order_id, projection_revision)` with a server-owned positive revision or other explicitly collision-free revision identity. Include read evidence version, trigger sequence, policy versions, projected time, typed state and an independently computed canonical manifest digest. Binding key should include the header key and observation UUID plus context role; the stored observation version/kind must FK to V015 identifier/update identity under the same organization and order. A correction-edge table or normalized edge columns may be required; SQL review must prevent nullable half-edges and cascade deletion of history.

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


## Implemented in-memory foundation (2026-10-12)

`MarketplaceEconomicObservationLineage` is repository vocabulary. It owns subject scope and a defensively copied, ordered list of exact identifier memberships. `VersionedMarketplaceIndependentEconomicEvidence.observationLineage=null` explicitly means an older adapter/fixture has not supplied durable membership; the Sales Intelligence producer fails closed rather than synthesizing it. PostgreSQL `find` always supplies the complete lineage, validates every identifier row against replay membership, and rejects omissions, extras, wrong kinds/versions or subjects. Positive versions must cover all updates contiguously; a correction has exactly its CORRECTION identifier and FACT replacement at the same update version. Superseded fact versions remain their original update versions. Duplicate apply retains existing membership. `apply` returns matching lineage after the append in its owned transaction.

The aggregate remains the sole owner of payloads, occurrence times, sources, attempts and correction objects. Metadata composes identity/version/kind/family/recorded time and exact correction edges, without duplicating payloads. Attempts DO have a domain family and retain it; corrections have no independent family. FACT and ATTEMPT families must match the aggregate.

`ConsumedEconomicEvidenceSnapshot.Input` captures membership before assembly and finalizes after actual assembly/calculation. The result defensively freezes members, coverage, reasons and calculation collections, validates subject and outcome compatibility, and contains the existing typed projection state. ORDER_ASSEMBLY_STATE is READY/NOT_READY, with exact existing reasons in the frozen outcome. COMPONENT_COVERAGE_STATE is taken from the assembled order only when Ready. NotReady carries no invented component coverage claim. The current assembler treats present components as PARTIAL regardless of observation coverage claims; absent types are MISSING. COMPLETE is supported only if the actual assembly/calculation contract proves it; current policy cannot manufacture it.

CONSUMED_ACTIVE_FACT denotes membership in the active aggregate boundary inspected by assembly, including external identity context; it does not mean individual contribution or causal support. Historical facts are classified from `activeFacts` and accepted correction edges, not row order. Attempts and corrections remain contextual. Absence conclusions use the complete aggregate boundary plus frozen assembly policy/reasons or assembled coverage, never fake missing observations.

### Canonical manifest v1

Algorithm: JCA SHA-256, lowercase hexadecimal; integrity/idempotency context, not a signature. Encoding: each scalar is UTF-8 preceded by a signed four-byte big-endian byte length; -1 is null, 0 is empty. Collection counts are framed base-10 integer scalars. UUIDs are canonical lowercase; integers use base-10 locale-independent text; Instants use epochSecond and nano scalars; money uses currency and canonical decimal `toPlainString`. Enum tokens use `name`, never redacted `toString`, ordinal or object hash. The immutable canonical byte array is generated anew when inspected and never exposed as shared mutable state.

Field order: format/version tag; organization UUID; order UUID; marketplace; external order identity; currency; read evidence version; trigger sequence; projection epochSecond/nano; assembly policy; nullable calculation policy; assembly state; reason count and reasons sorted by enum name; coverage count and (type,state) sorted by type name; member count and members sorted by canonical observation UUID. Every member frames observation UUID, individual evidence version, identifier kind, nullable family, context role, recorded epochSecond/nano, nullable superseded UUID, nullable replacement UUID. Correction edges are therefore bound without nullable half-edges.

Typed projection outcome follows: UNRESOLVED, or INCOMPLETE with organization/order, sorted missing/partial type lists and supplied components, or COMPLETE with organization/order, marketplace/external order, occurrence epochSecond/nano, currency, gross revenue, marketplace fees, shipping, advertising, taxes, product cost, financial cost, other adjustments, contribution, typed defined/undefined margin, truth quality and components. Each component is sorted by UUID and frames organization/order/component UUID, type, direction, currency/amount, source kind/system, typed PRESENT reference or ABSENT reason, occurrence epochSecond/nano and quality. This freezes the existing calculation result but introduces no contribution/truth-quality causal claim taxonomy. Policy versions and trigger/time belong to manifest revision context. The exact executable layout is `ConsumedEconomicEvidenceSnapshot.canonicalManifest`.

### Remaining persistence gate and implementation handoff

No SQL migration, historical table, revision pointer or writer is introduced. An eligible next persistence tranche must first finalize DDL and allocate a collision-free migration slot under repository coordination. V043 is occupied by Package 0090 and must remain untouched; V044 is not claimed.

The bounded transaction seam is the PostgreSQL Sales Intelligence adapter: extract its existing binding/upsert into a connection-owned helper, then add a separate history-aware writer that receives the frozen snapshot and projection together. The writer must own one `autoCommit=false` connection, validate exact subject/version/policy/outcome equality, lock the current organization/order transition, and handle an existing published trigger before any new header insert. Insert the immutable header, exact V015 tuple bindings and correction edges, publish the V018 pointer with the dual monotonic guard, then commit. Any exception, binding mismatch, integrity conflict or failed publication rolls back all; no global DataSource refactor is required. Internal helpers must not commit or open independent connections.

Use a server-owned historical revision identity and a unique published-trigger/policy context under organization/order. Duplicate equality must compare all frozen context including manifest and outcome; same key with different context is an integrity conflict. A previously published retry returns its stored immutable context without regenerating time or recomputing against newest evidence. A race loser must resolve the winning publication, never commit an orphan revision. A new policy context requires a governed revision trigger; current skip semantics must not silently create policy history.

DDL still needs reviewed immutable triggers, exact multi-column V015 FKs, normalized typed outcomes/reasons/coverage, no destructive cascade, complete correction-edge constraints, and a database-enforced V018 revision link. Then execute all twelve historical cases and header/member/current-write failure injection inside disposable PostgreSQL without a shared database or externally exposed service. Only passing that evidence may promote historical readiness. Retrieval/redaction authorization remains separate and retrieval readiness remains NO.


## 2026-10-13 selected historical contract and qualification gate

The [DDL blueprint](SPEC-0091-historical-lineage-ddl-blueprint.md) selects all table/constraint/trigger/index names and exact candidate SQL. The [atomic publication contract](SPEC-0091-historical-lineage-atomic-publication.md) specifies the owned connection seam, module visibility/codec promotions, equality rules, root lock/state machine, race outcomes, eight failure points and internal read verification. These supersede the earlier provisional composite publication-key/policy alternatives: key is organization/order/trigger; read version, policies, time, typed outcome and manifest are exact equality context. Policy change under the same trigger is divergent, not a new revision; use a new genuine evidence trigger.

Revision identity is a separate global database-generated positive bigint, never MAX+1 and never a client/trigger/evidence identity. Member PK enforces one context role per observation per revision, matching the current exhaustive classification. Correction edges are separate, non-null and exact-source/member-FK checked. Normalized reason/coverage rows must match the frozen versioned V018 payload; header retains full typed calculation payload and complete canonical bytes/digest. This compatibility codec freezes old values without executing old or current policy logic. Source metadata remains in V015, raw provider payloads never enter this schema.

Current V018 gains a scoped opaque revision FK only in the eligible migration. Database trigger enforces exact context equality, dual monotonic transition and append-only publication receipt. Deferred checks enforce complete scoped source membership/corrections, normalized outcomes and receipt existence; no orphan candidate can be committed. Existing current rows remain explicitly legacy NULL/unlinked, not reconstructed using current assembly.

POSTGRES_FOUNDATION_QUALIFIED=NO (Docker initialization failed; no SQL assertions).
DDL_CONTRACT_READY=YES_DESIGN_ONLY (static SQL/PLpgSQL parsing and declared FK-target checks; no DB execution).
REVISION_IDENTITY_READY=YES_DESIGN_ONLY.
IDEMPOTENCY_READY=YES_DESIGN_ONLY.
TRANSACTION_MODEL_READY=YES_DESIGN_ONLY.
RACE_MODEL_READY=YES_DESIGN_ONLY.
FAILURE_TEST_PLAN_READY=YES (all eight points and independent rollback oracles specified).
MIGRATION_SLOT_READY=NO (V043 owner/interlock and canonical release coordination unresolved).
PERSISTENCE_IMPLEMENTATION_READY=NO.

No migration, atomic writer, historical read port or production composition cutover is installed in this tranche. The required unresolved-to-Complete proof remains blocked by current policy capability and must use a legitimate accepted complete-coverage fixture; do not infer missing evidence to zero. Raw retrieval/UI/authority remain separate and unavailable. Qualification and findings are recorded in [gate evidence](../evidence/ROOM-V2-postgres-historical-lineage-gate.md); [migration coordination](../evidence/ROOM-V2-historical-lineage-migration-coordination.md) allocates no number.
