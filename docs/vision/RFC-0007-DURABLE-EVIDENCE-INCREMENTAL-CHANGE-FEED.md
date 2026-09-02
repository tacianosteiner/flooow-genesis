# RFC-0007: Durable Evidence Incremental Change Feed (P0.3 Boundary)

**Version:** 0.2

**Status:** Draft for Experimental Validation

## Objective

Define the smallest proposed boundary required to read committed durable
evidence updates incrementally, ordered, and resumably per organization — the
prerequisite P0.3 needs before any projection, materialization, or read API can
exist — without widening `MarketplaceIndependentEconomicEvidenceRepository`
or reopening V015.

This RFC is pre-ADR, pre-SPEC, and pre-TASK. It proposes concepts and a
two-slice validation plan. It does not authorize production implementation, a
materialized projection table, an API, a UI, or any provider work. Its claims
about query performance and concurrency remain hypotheses until EXP-0006
validates them against real PostgreSQL.

## Context

TASK-0144 (P0.2) deliberately kept `change_sequence` out of the domain, out
of the economic port, and out of every public persist/read result. ADR-0045
already names `change_sequence` as "the durable, resumable cursor a future
P0.3 projection reads directly from the evidence tables," and SPEC-0044's
test 34 proves this query shape works and is stable:

```sql
WHERE organization_id = ? AND change_sequence > :checkpoint
ORDER BY change_sequence
```

The physical PostgreSQL sequence behind `change_sequence` is global. The
ordering guarantee relevant to this proposed feed is per organization. This
RFC does not claim global commit ordering between different organizations.

Reconnaissance against `main` at `61560bb` confirms three things:

1. That query pattern exists today only inside
   `PostgresMarketplaceIndependentEconomicEvidenceRepositoryTest.kt` as test
   scaffolding — no production boundary exposes it.
2. Two existing patterns are structurally adjacent but not directly reusable:
   `PostgresCanonicalInventoryObservationRepository.project()` has a
   transactional/conflict/reconstruction shape but operates on inventory, not
   economic evidence; `integration_connector_progress` has a
   checkpoint-with-lock shape but tracks inbound connector ingestion progress,
   not outbound consumption of an internal durable journal.
3. No mechanism exists today to discover which organizations have pending
   changes relative to a named projection checkpoint.

Building a projection or API directly on top of raw SQL against
`marketplace_economic_evidence_update` — as the test file does today — would
either leak persistence detail into whatever consumes it or tempt someone to
add another method to `MarketplaceIndependentEconomicEvidenceRepository`,
which SPEC-0044 deliberately kept limited to `find`/`apply`.

## Problem Statement

Given the existing, unmodified `marketplace_economic_evidence_update` and
`marketplace_economic_evidence_subject` tables created by V015, experimentally
validate a proposed boundary containing:

1. an incremental change feed that returns bounded evidence-change
   invalidations after a checkpoint, ordered by `change_sequence`, for one
   organization at a time;
2. a checkpoint model that lets independent named projections consume the
   same durable journal at different paces without interference;
3. explicit checkpoint inspection and compare-and-set advancement;
4. a candidate discovery query for organizations with changes pending relative
   to a named projection, including organizations that have no checkpoint row.

## Non-Goals

- No materialized Sales Intelligence read model, table, or schema in this RFC.
  That is P0.3 Slice B and requires separate authorization.
- No historical snapshot feed and no exact reconstruction of the aggregate at
  the version named by a change.
- No evidence-timeline or exact historical-replay solution.
- No API or UI. No provider work (Mercado Livre, Omie). No Economic Truth
  materialization, Ledger, or Reconciliation change.
- No modification to V015,
  `MarketplaceIndependentEconomicEvidencePersistence.kt`, or
  `PostgresMarketplaceIndependentEconomicEvidenceRepository.kt`.
- No generalized event bus, outbox, or pub/sub mechanism. The proposed feed is
  pull-based.
- No V016 or other production migration is authorized by this RFC or EXP-0006.

## Slice A Semantics: Invalidation / Change Feed

Slice A is an **invalidation/change feed**. Each returned change states that an
aggregate changed and supplies its complete
`MarketplaceEconomicEvidenceSubject`, evidence version, sequence, and change
kind. It does not carry the fact/component payload and does not represent an
exact historical snapshot at that version.

A consumer may follow this path:

```text
change
  -> complete subject
  -> MarketplaceIndependentEconomicEvidenceRepository.find(subject)
  -> current aggregate state
```

`find(subject)` may return a version later than the `evidenceVersion` that
originated the change. A batch may contain multiple changes for the same
subject while each subsequent `find(subject)` observes the same latest state.
Slice A therefore does not claim to reproduce each intermediate aggregate
state or an exact evidence timeline. Slice B must address those requirements
if its materialization contract needs them.

The complete subject is obtained in the feed adapter by joining the update
journal with `marketplace_economic_evidence_subject`. No second subject lookup
is required from the consumer, and no P0.2 contract or V015 object is modified.

## Candidate Concepts

### `MarketplaceEconomicEvidenceChangeFeed`

A new, narrow port, separate from
`MarketplaceIndependentEconomicEvidenceRepository` and never merged into it:

```kotlin
interface MarketplaceEconomicEvidenceChangeFeed {
    fun changesSince(
        organizationId: OrganizationId,
        checkpoint: ChangeSequenceCheckpoint,
        limit: Int
    ): List<MarketplaceEconomicEvidenceChange>

    fun organizationsWithPendingChanges(
        projectionName: ProjectionName,
        limit: Int
    ): List<OrganizationId>

    fun currentCheckpoint(
        organizationId: OrganizationId,
        projectionName: ProjectionName
    ): ChangeSequenceCheckpoint

    fun advanceCheckpoint(
        organizationId: OrganizationId,
        projectionName: ProjectionName,
        expected: ChangeSequenceCheckpoint,
        next: ChangeSequenceCheckpoint
    ): CheckpointAdvanceResult
}
```

Both collection-returning operations require a positive, bounded `limit`.
`changesSince` is deterministically ordered by ascending `change_sequence`
within the requested organization. Repeated calls using the last returned
sequence as the next checkpoint form deterministic forward pagination.
`organizationsWithPendingChanges` must also define and experimentally prove a
stable deterministic order before this candidate becomes an accepted
contract.

### `MarketplaceEconomicEvidenceChange`

The proposed change contains:

```text
subject: MarketplaceEconomicEvidenceSubject
evidenceVersion: MarketplaceEconomicEvidenceVersion
changeSequence: ChangeSequenceCheckpoint
changeKind: MarketplaceEconomicEvidenceChangeKind
```

The `subject` is complete, including its organization, marketplace order,
marketplace identity, external order identity, and currency. The change does
not expose an evidence payload.

### `ChangeSequenceCheckpoint`

A proposed immutable, validated value with `NONE`/`ZERO` equal to zero and an
explicit persistence accessor. It is not `@JvmInline`, is comparable, accepts
only non-negative values, and does not expose another public raw-value
accessor.

The underlying PostgreSQL sequence is global and may contain gaps. The
checkpoint is interpreted only in conjunction with `organizationId`; it does
not assert cross-organization commit ordering.

### `ProjectionName`

A proposed immutable, validated identifier:

- not blank;
- no more than 100 characters;
- matches `^[a-z0-9][a-z0-9-]*$`.

Different projection names identify independent consumers of the same journal.

### `CheckpointAdvanceResult`

A closed result family:

- `Advanced`;
- `Stale`;
- `Regression`.

`advanceCheckpoint` uses explicit compare-and-set semantics with `expected`
and `next`:

- `next <= expected` returns `Regression` without a write;
- exactly matching durable state may advance to `next` and return `Advanced`;
- a concurrently changed durable value returns `Stale`;
- no regression is silent.

The initial checkpoint for an organization/projection pair with no durable row
is `NONE`. Creation of the first row participates in the same compare-and-set
semantics and must be safe under concurrent first writers.

Reading never advances the checkpoint. `changesSince` and
`organizationsWithPendingChanges` are observational operations. Explicit
checkpoint advancement supports at-least-once processing: a caller that fails
before a successful advance can read the same changes again.

## Candidate Checkpoint Persistence

The proposed durable state is a new table owned by this boundary, not by the
evidence journal:

```sql
projection_checkpoint(
  organization_id uuid NOT NULL REFERENCES integration_organization (organization_id),
  projection_name text NOT NULL,
  last_change_sequence bigint NOT NULL DEFAULT 0 CHECK (last_change_sequence >= 0),
  updated_at timestamptz(6) NOT NULL,
  PRIMARY KEY (organization_id, projection_name),
  CHECK (projection_name ~ '^[a-z0-9][a-z0-9-]{0,99}$')
)
```

The database is authoritative for `updated_at`. The candidate schema uses a
`BEFORE INSERT OR UPDATE` trigger that overwrites it with
`transaction_timestamp()`, following the timestamp-authority pattern already
validated in the repository.

No checkpoint row means `NONE` for that organization/projection pair. Rows for
two different `projection_name` values are independent even when they consume
the same organization and evidence journal.

This schema remains a proposal. EXP-0006 must create it only as ephemeral SQL
inside its Testcontainers test setup. This RFC does not authorize V016.

## Candidate Pending-Organization Discovery

`organizationsWithPendingChanges` is proposed as a `LEFT JOIN` plus aggregation
over evidence changes and checkpoints for the requested projection name.
Organizations with journal changes but no checkpoint row must be treated as if
their checkpoint were `NONE`.

The existing V015 uniqueness/index shape on
`(organization_id, change_sequence)` may be relevant to that query, but this
RFC does not claim that the index alone prevents a scan. The candidate query,
its stable ordering, examined-row count, and execution plan must be validated
experimentally with sufficient data volume.

## Experimental Validation Plan — EXP-0006 / Slice A

EXP-0006 remains pre-ADR and must run against real PostgreSQL through
Testcontainers. It must not mock persistence, add a production migration, or
alter any P0.2 production file.

The experiment must validate:

1. `changesSince` returns all bounded changes above `NONE` for an organization;
2. partial checkpoints return only later changes;
3. a checkpoint equal to the current maximum returns no changes;
4. an organization with changes and no checkpoint row appears as pending;
5. multiple organizations maintain independent checkpoint views;
6. two `ProjectionName` values consume the same journal at different speeds
   without interference;
7. `limit` produces deterministic, stable pagination without repetition or
   omission when the returned final sequence becomes the next checkpoint;
8. real concurrent writes through the existing P0.2
   `PostgresMarketplaceIndependentEconomicEvidenceRepository` can occur while
   the feed is read;
9. returned changes remain ordered by `change_sequence` within each
   organization under that concurrency;
10. the experiment does not claim cross-organization commit ordering;
11. two concurrent checkpoint writers using the same `expected` value yield
    exactly one `Advanced` and one `Stale`;
12. `next <= expected` returns `Regression` without changing durable state;
13. the first successful advance for a previously unseen
    organization/projection pair creates its checkpoint row safely;
14. repeated `changesSince` calls with the same checkpoint return the same
    result when no intervening writes occur;
15. `changesSince` never advances a checkpoint implicitly;
16. after explicit successful advancement, the next read reflects the new
    checkpoint;
17. `organizationsWithPendingChanges` is exercised with thousands of journal
    rows across multiple organizations;
18. the exact pending-discovery query is inspected using
    `EXPLAIN (ANALYZE, BUFFERS)` against real PostgreSQL;
19. the captured plan records the actual node types, indexes used, actual rows,
    rows removed by filters, loops, buffer hits/reads, planning time, and
    execution time;
20. the experiment reports the plan as observed evidence and does not convert
    an expected index strategy into a fact before execution.

The experimental `projection_checkpoint` table, trigger, and candidate queries
must exist only inside the experiment's Testcontainers setup. Results are
recorded as `EXP-0006` under `docs/evidence/` only after execution.

## Experimental Decision Matrix

| Experiment outcome | Candidate follow-up |
|---|---|
| All fixtures pass, per-organization ordering remains stable under concurrent P0.2 writes, checkpoint CAS behaves as specified, and the measured pending-discovery plan is acceptable | An ADR may then propose a production boundary and a separately reviewed production schema change. |
| Ordering is unstable under concurrent P0.2 writes | Revisit read and transaction semantics without weakening P0.2 guarantees. |
| Pending discovery examines or scans an unacceptable amount of data | Revisit the discovery shape or indexing before proposing a production contract. |
| Checkpoint CAS permits multiple successful writers, regression, or silent loss | Reject the proposed checkpoint contract and redesign it before an ADR. |

No row in this matrix authorizes an ADR, SPEC, TASK, migration, or production
implementation automatically.

## Relationship to P0.3 Slice B

Slice B is responsible for separately proposing and validating a
read-optimized Sales Intelligence materialization on top of the accepted
invalidation feed, if Slice A is eventually accepted.

Slice B must address:

- materialized list and detail shape;
- rebuild-from-zero semantics;
- exact evidence timeline requirements;
- whether intermediate aggregate versions must be reconstructable;
- staleness and projection-lag exposure;
- first consumer identity;
- atomicity or idempotency between materialization and checkpoint advancement.

Slice A does not resolve those questions.

## Open Design Questions Carried Forward

- Who consumes the feed first: an internal validation query, a test harness, a
  service, or Slice B followed by a future API?
- Must Slice B persist a materialized read model immediately, or can its first
  milestone remain an internal demonstrable consumer?
- Does Slice B require exact per-version reconstruction or only idempotent
  convergence on the current aggregate state?
- Should checkpoint state later include projection lag, replay position,
  failure, or lease metadata?
- What measured pending-discovery cost is acceptable before a different
  discovery structure becomes necessary?
