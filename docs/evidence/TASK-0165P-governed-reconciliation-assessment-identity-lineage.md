# TASK-0165P - Governed Reconciliation Assessment Identity and Lineage

Date: 2026-09-13

Base: `8cf975b`

Status: DESIGN APPROVED

## Purpose

Resolve the architectural dependency deliberately left open by TASK-0165O:

`BLOCKED BY UPSTREAM GOVERNED ASSESSMENT IDENTITY / REVISION LINEAGE`

The task must establish exact immutable assessment identity and durable
case-revision lineage without making the Economic Decision Room an identity
authority.

## Audit findings

### Finding 1 - no governed assessment identity exists

`FinancialReconciliationAssessment` contains complete deterministic
reconciliation content but has no governed persistent identity.

`AcceptedFinancialReconciliationAssessment` currently preserves the assessment
and `acceptedAt` only.

### Finding 2 - durable case is not an assessment snapshot

`DurableReconciliationCase.fromAssessment(...)` retains only reconciliation
lines whose status is `DIVERGENCE`.

Non-divergent assessment content is intentionally lost at the case boundary.

Therefore a durable case cannot prove or reconstruct the complete assessment
that produced it.

### Finding 3 - current case equality is weaker than assessment equality

Current case idempotence compares the durable case projection.

Two complete assessments may differ outside the retained divergence-stage
projection while producing the same durable case observation.

This means assessment change can currently be invisible to case revision.

### Finding 4 - persistence stores current state, not revision lineage

`marketplace_reconciliation_case` stores one current row per governed
organization/trace/policy case identity.

The repository updates that row as revision advances.

There is no append-only case-revision-to-assessment historical binding.

### Finding 5 - current persistence success semantics are too weak for lineage

The current conditional UPSERT accepts only a greater incoming revision, but the
repository does not use the affected-row count as an explicit application
outcome.

A lineage-capable persistence boundary must distinguish applied, replay,
conflict, integrity failure and unavailability.

### Finding 6 - historical reconstruction would be false authority

Existing case data, current financial traces and newly recomputed assessments do
not prove which complete assessment historically produced an existing revision.

Synthetic historical backfill is therefore prohibited.


### Finding 7 - canonical protocol must not depend on runtime ordinal

Revision 2 freezes stage ordering independently of `FinancialLedgerStage.ordinal`.

### Finding 8 - canonical money text must be version-stable

Revision 2 freezes v1 numeric text and bounds independently of future money-domain refactors.

### Finding 9 - snapshot schema and rehydration authority were underspecified

Revision 2 defines snapshot v1 shape and a domain-owned validated rehydration boundary.

### Finding 10 - atomic lineage needs one composite write boundary

Revision 2 prohibits independently committing case/lineage repositories and requires database-backed concurrency/commit invariants.

### Finding 11 - current lineage must verify before idempotence

Revision 2 requires snapshot/version/context/digest verification before trusting a stored fingerprint.

### Finding 12 - adversarial coverage was incomplete

Revision 2 restores runtime-hash, serializer-independence and same-fingerprint/different-snapshot coverage and adds frozen ordering, money and atomicity vectors.

### Finding 13 - canonical JSON scalar types and variant literals must be explicit

Revision 3 freezes top-level JSON scalar types, `OBSERVED`/`COMPARED` kind
literals and UUID-array element representation so known-answer bytes do not
depend on serializer coercion.

### Finding 14 - snapshot version metadata must not disagree with payload

Revision 3 requires the persisted snapshot schema version and embedded
`schemaVersion` to agree or fail closed.

### Finding 15 - new-case and revision races need explicit proofs

Revision 3 adds adversarial concurrency requirements for identical creates and
different assessments racing from the same current revision.

### Finding 16 - digest equality is not mathematical byte equality

Final review identified an over-strong SHA-256 wording in the draft. The final
design now states the correct contract: byte-equal canonical content must hash
equally, digest mismatch proves inequality/corruption, and a digest match becomes
verified identity only together with semantically identical reconstructed
snapshot content. Equal digest with different semantic snapshot is
`INTEGRITY_FAILURE`.

## Design decisions proposed

ADR-0079 proposes:

- content-addressed assessment identity;
- SHA-256 over canonical domain representation;
- identity computed inside the acceptance boundary, never caller supplied;
- no standalone assessment revision;
- exact immutable assessment snapshot preserved with each lineage record;
- append-only `(organization, case, caseRevision)` lineage;
- atomic current-case and lineage persistence;
- revision advancement on complete assessment fingerprint change;
- no synthetic legacy backfill;
- first post-lineage legacy observation creates a new verified revision;
- Decision Room consumes and verifies lineage but never creates expected
  identity.

SPEC-0079 freezes the canonicalization, persistence and adversarial contracts.

## Central invariants

```text
Context equivalence != evidence identity
```

```text
Assessment fingerprint
!= case revision
!= policy version
!= source evidence evolution
```

```text
Unknown historical lineage
!= verified assessment identity
```

```text
Fingerprint
!= snapshot
```

## Proposed canonical lifecycle

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
        |  fingerprint computed here
        v
GovernedReconciliationCaseOrchestrator
        |
        v
case revision decision
        |
        +---------------------------+
        |                           |
        v                           v
current durable case       exact assessment lineage
        |                           |
        +-------------+-------------+
                      |
                      v
             atomic persistence
                      |
                      v
        verified case-revision provenance
                      |
                      v
         future Decision Room source
```

## Legacy rule

No existing case revision receives synthetic lineage.

For a legacy case with current revision `N` and no lineage, the first eligible
accepted assessment after lineage activation creates revision `N + 1`.

That new revision is the first verified revision.

## Replay rule

For a lineage-verified current revision:

```text
same fingerprint -> unchanged
different fingerprint -> next revision
```

The same fingerprint may recur at a later non-adjacent revision after an
intervening different assessment.

Therefore fingerprint is not globally unique per case.

## Self-attestation rule

A source that returns both an arbitrary assessment and the matching "expected"
fingerprint is not independent identity evidence.

Expected identity must already exist in durable upstream case-revision lineage.

The Decision Room verifies that lineage.

It never creates it.

## Design documents

- `docs/adr/ADR-0079-governed-reconciliation-assessment-identity-and-case-revision-lineage.md`
- `docs/specifications/SPEC-0079-reconciliation-assessment-fingerprint-and-case-revision-lineage.md`

## Explicit non-changes

This design phase does not modify:

- Kotlin production code;
- Kotlin tests;
- PostgreSQL migrations;
- OpenAPI;
- TASK-0165O;
- Economic Truth;
- financial ledger;
- provider integration;
- recovery/execution authority.

`task-0165k-backup.patch` remains untouched.

## Review gate

Implementation is not authorized until ADR-0079 and SPEC-0079 are audited for:

1. identity birth authority;
2. canonicalization stability;
3. revision semantics;
4. atomic persistence;
5. legacy handling;
6. replay/concurrency behavior;
7. cross-organization isolation;
8. self-attestation resistance;
9. compatibility with TASK-0165O;
10. absence of parallel reconciliation or truth authority.
