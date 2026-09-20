# ADR-0079 - Governed Reconciliation Assessment Identity and Case Revision Lineage

Status: Accepted

Date: 2026-09-13

## Context

Flooow already owns financial reconciliation through
`MarketplaceFinancialReconciliation` and
`FinancialReconciliationAssessment`.

`AcceptedFinancialReconciliationAssessment` is the explicit productive seam
into durable reconciliation cases.

`DurableReconciliationCase` is intentionally derived. It preserves the
operational case state, divergence-stage details and evidence references, but
it is not the complete reconciliation assessment.

The current persistence model stores only the latest durable case state.

TASK-0165O exposed the consequence of that boundary: the Economic Decision Room
can validate that an assessment candidate has matching organization, case,
trace, order, policy, currency and case-revision coordinates, but those
coordinates do not prove that the candidate is the exact assessment that
produced that case revision.

The governing invariant is:

`Context equivalence != evidence identity`.

The Decision Room must not mint, reconstruct or self-attest the missing
identity.

## Existing identity loss

The current lifecycle is:

```text
FinancialTrace + FinancialReconciliationPolicy
        |
        v
MarketplaceFinancialReconciliation
        |
        v
FinancialReconciliationAssessment
        |
        v
AcceptedFinancialReconciliationAssessment
        |
        v
GovernedReconciliationCaseOrchestrator
        |
        v
DurableReconciliationCaseProcessor
        |
        v
DurableReconciliationCase
        |
        v
marketplace_reconciliation_case
```

`FinancialReconciliationAssessment` has deterministic domain content but no
governed persistent identity.

The acceptance marker currently adds acceptance time but no content identity.

The durable case is lossy because only reconciliation lines whose status is
`DIVERGENCE` become durable case stages.

The PostgreSQL case table is a current-state projection. Revisions overwrite
the current row rather than preserving the exact accepted assessment that
produced each revision.

Therefore:

```text
case identity != assessment identity
case revision != assessment identity
trace identity != trace contents
policy version != assessment identity
```

## Decision

### 1. Assessment identity is content-addressed

Introduce a versioned content fingerprint for the complete
`FinancialReconciliationAssessment`.

Conceptually:

```text
FinancialReconciliationAssessmentFingerprint
    canonicalizationVersion
    sha256
```

The initial algorithm is SHA-256 over a domain-defined canonical representation.

The fingerprint is immutable for an immutable assessment snapshot.

The fingerprint is not Kotlin `hashCode()`, `toString()`, serializer output or a
hash of the durable reconciliation case.

### 2. Governed identity is established at acceptance

`MarketplaceFinancialReconciliation` remains the deterministic producer of the
assessment.

The governed identity is established when that exact assessment crosses
`AcceptedFinancialReconciliationAssessment.accept(...)`.

The caller may provide the assessment and accepted timestamp.

The caller must not provide or override the assessment fingerprint.

Acceptance computes the fingerprint from the assessment under the governed
canonicalization contract and preserves:

```text
assessment
assessmentFingerprint
acceptedAt
```

This keeps identity computation adjacent to the existing explicit acceptance
boundary without giving callers a self-attestation mechanism.

The fingerprint function itself is deterministic and may be invoked by trusted
domain code for verification before or after acceptance. Mere ability to compute
the same digest does not confer governed authority. Acceptance is the boundary
at which that digest becomes authoritative input to governed case persistence.

### 3. Fingerprint identifies assessment content, not an occurrence

`acceptedAt` is metadata and is excluded from the fingerprint.

The following are also excluded:

```text
caseId
caseRevision
openedAt
lastObservedAt
resolvedAt
```

Therefore two acceptances of exactly the same assessment content produce the
same fingerprint.

No independent `assessmentRevision` is introduced by this decision.

The distinct concepts remain:

```text
ASSESSMENT FINGERPRINT
!= CASE REVISION
!= POLICY VERSION
!= SOURCE EVIDENCE EVOLUTION
```

### 4. Preserve exact case-revision assessment lineage

Introduce append-only durable lineage from a reconciliation case revision to
the exact accepted assessment snapshot.

Conceptually:

```text
(organizationId, caseId, caseRevision)
        |
        +-- assessment fingerprint
        +-- fingerprint/canonicalization version
        +-- acceptedAt
        +-- exact governed assessment snapshot
```

The existing `marketplace_reconciliation_case` remains the operational
current-state projection.

The lineage store is not a second reconciliation engine, Economic Truth store,
leakage ledger or recommendation store.

Its purpose is immutable provenance for the existing
`FinancialReconciliationAssessment` authority.

### 5. Fingerprint alone is insufficient

The lineage must preserve the exact assessment snapshot in addition to the
fingerprint.

A fingerprint mismatch proves that the candidate content differs from the
stored identity or that persisted data is corrupt. A matching SHA-256 digest is
a cryptographic equality candidate, not mathematical proof of byte equality.
Verified equality additionally requires the stored snapshot to reconstruct to
semantically identical assessment content and to recompute to the stored
fingerprint.

A durable case cannot reconstruct that assessment because the case intentionally
drops non-divergent reconciliation lines.

A current `FinancialTrace` also cannot be treated as historical proof because
the trace may have evolved after the assessment was accepted.

### 6. Case and lineage persistence are atomic

Creation or revision of a durable case and insertion of its immutable
case-revision assessment lineage must occur in one database transaction.

The system must never publish a case revision whose governed lineage failed to
commit.

The system must never commit lineage for a case revision whose current case
write failed.

### 7. Case revisions follow accepted assessment changes

For lineage-verified cases:

```text
same current assessment fingerprint
    -> unchanged / idempotent replay

different assessment fingerprint
    -> next contiguous case revision
```

A different complete assessment advances the case revision even when the
derived divergence-only durable stage projection happens to remain identical.

This aligns implementation semantics with the existing durable-case decision
that changed assessments advance revision.

The same fingerprint may legitimately appear again at a later non-adjacent
revision if the complete reconciliation state returns to an earlier content
state. Therefore fingerprint is not globally unique per case.

This revision rule applies only after the existing orchestration eligibility
gate has accepted a `DIVERGENCE` assessment. Non-divergent assessments remain
outside case creation/revision and are not granted case-resolution semantics by
this ADR.

Under this ADR, `caseRevision` is the accepted reconciliation-observation
revision. No lifecycle-only mutation is authorized by the current case API. A
future status-only lifecycle write must not silently reuse this assessment
lineage sequence without a separate architectural decision.

### 8. Persistence must reject stale, skipped or conflicting revisions

A revision write must be contiguous.

For an existing case at revision `N`, the only valid new revision is `N + 1`.

A replay of the already-committed revision with the same fingerprint and same
assessment content is idempotent.

The same `(organization, case, revision)` with different fingerprint or
different assessment content is an integrity conflict.

A persistence adapter must not report success when a conditional update affected
zero rows.

### 9. Historical lineage is never fabricated

The migration creates no synthetic lineage for existing reconciliation cases.

For a pre-lineage case:

```text
historical lineage absent
!=
historical lineage verified
```

The system must not backfill lineage from:

- durable case stages;
- case evidence-entry IDs;
- current financial trace contents;
- current reconciliation policy;
- a newly recomputed assessment;
- serializer output.

If an existing legacy case has no verified lineage, the first eligible accepted
assessment after this capability becomes active creates a new case revision and
that new revision receives verified lineage, even if the visible durable
case projection is otherwise unchanged.

This deliberately preserves:

`UNKNOWN HISTORICAL LINEAGE != VERIFIED ASSESSMENT IDENTITY`.

### 10. Consumers verify; they do not attest

A future Decision Room assessment source reads the authoritative durable lineage
for the requested case revision.

The consumer verifies the stored assessment snapshot by recomputing its governed
fingerprint and comparing it with the durable fingerprint.

A transient source that supplies both an "expected fingerprint" and arbitrary
assessment content without an independently durable upstream binding is not
sufficient authority.

The Decision Room remains a consumer/verifier only.

### 11. Organization scope is part of every lineage operation

Every lineage read and write is organization-scoped.

Cross-organization lookup must be indistinguishable from absence at public
boundaries.

No global case-ID or fingerprint lookup may bypass organization scope.

## Canonicalization ownership

The canonicalization algorithm is an application-domain contract owned beside
the financial reconciliation model.

Persistence may store a structured snapshot, but persistence does not define
assessment identity.

JSONB physical ordering, JDBC representation, database formatting, Kotlin
runtime hashes and API serializers cannot affect the fingerprint.

SPEC-0079 freezes canonicalization v1.

## Replay model

A correct replay has three relevant cases:

```text
current lineage fingerprint == accepted fingerprint
    -> no new revision

current lineage fingerprint != accepted fingerprint
    -> create revision N + 1 and lineage atomically

same revision already persisted with same fingerprint and same snapshot
    -> idempotent success
```

A same-revision content conflict fails closed.

## Security and integrity boundary

The implementation must fail closed for:

- caller-declared fingerprint attempts;
- snapshot/fingerprint mismatch;
- organization mismatch;
- stale expected case revision;
- skipped revision;
- same revision with different assessment;
- unknown fingerprint/canonicalization version;
- malformed snapshot;
- lineage missing for a revision claimed to be verified.

No failure grants leakage, recommendation, recovery, mutation or execution
authority.

## Non-goals

This ADR does not authorize:

- a second reconciliation engine;
- an assessment recommendation engine;
- Economic Truth mutation;
- provider writes;
- recovery, refund, claim or settlement execution;
- automatic historical backfill;
- an acceptance-event journal for every repeated acceptance;
- a standalone `assessmentRevision`;
- Decision Room self-attestation;
- changing TASK-0165O before governed lineage exists.

## Consequences

Positive:

- exact accepted-assessment identity becomes durable;
- case revision has auditable provenance;
- complete assessment changes cannot disappear behind a lossy case projection;
- replay and concurrency semantics become explicit;
- future Decision Room reads can verify historical assessment identity;
- legacy uncertainty remains truthful rather than reconstructed.

Trade-offs:

- persistence requires a new append-only lineage structure;
- case persistence must become transactional with lineage;
- processor/orchestrator semantics must compare governed assessment identity, not
  only durable divergence projection;
- legacy cases remain lineage-unverified until a genuinely new governed
  observation is committed.

## Required implementation sequence

Implementation is not authorized by this ADR alone until SPEC-0079 is accepted.

The intended order is:

1. canonical fingerprint domain contract and known-answer tests;
2. accepted-assessment identity binding;
3. exact immutable assessment snapshot contract;
4. append-only lineage persistence;
5. atomic current-case plus lineage commit semantics;
6. replay, concurrency and tamper tests;
7. legacy-case transition tests;
8. production lineage reader;
9. only then return to TASK-0165O and replace contextual-only assessment matching
   with verified case-revision lineage consumption.
