# SPEC-0077 — Economic Reconciliation and Leakage

## Purpose

Define the deterministic, read-only interpretation of governed financial
reconciliation into economic leakage semantics.

## Inputs

The interpretation pipeline consumes:

1. `FinancialReconciliationAssessment`;
2. `EconomicTruthAuthorityAssessment`;
3. leakage governance derived from that authority.

## Existing reconciliation contract

The existing reconciliation engine owns:

- expected financial side;
- actual financial side;
- signed difference;
- absolute difference;
- tolerance;
- reconciliation status;
- effective expected entry IDs;
- effective actual entry IDs.

TASK-0165N does not redefine these semantics.

## Core invariant

FINANCIAL VARIANCE != ECONOMIC LEAKAGE

A mathematical difference is not sufficient evidence for an economic leakage claim.

## Governance prerequisites

Leakage interpretation requires governed authority for:

- identity;
- currency;
- allocation;
- currentness.

Blocking authority states include repository-native equivalents of:

- unresolved;
- contradictory;
- stale;
- not applicable where economic interpretation requires the authority.

## Interpretation states

The TASK-0165N economic layer uses:

- `NO_MATERIAL_VARIANCE`;
- `UNFAVORABLE_LEAKAGE`;
- `FAVORABLE_VARIANCE`;
- `UNQUANTIFIED`.

`UNQUANTIFIED` must include a typed blocking reason.

## Blocking reasons

Current interpretation blocking reasons include:

- `GOVERNANCE_NOT_SATISFIED`;
- `MISSING_EXPECTED`;
- `MISSING_ACTUAL`;
- `RECONCILIATION_INCOMPLETE`;
- `UNSUPPORTED_STAGE`.

Governance carries typed upstream reasons including:

- `IDENTITY_UNRESOLVED`;
- `CURRENCY_UNRESOLVED`;
- `ALLOCATION_UNRESOLVED`;
- `EVIDENCE_CURRENTNESS_UNRESOLVED`;
- `CONTRADICTORY_AUTHORITY`;
- `STALE_AUTHORITY`.

## Sign semantics

The reconciliation engine defines:

signedDifference = actual - expected

Economic interpretation depends on stage semantics.

### SALE

Lower completed actual revenue than governed expected revenue may be economically
unfavorable.

Higher completed actual revenue may be favorable.

### PRODUCT_COST

A more-negative completed actual cost than governed expected cost may be
unfavorable leakage.

A less-negative completed actual cost may be favorable only when reconciliation
is sufficiently complete.

### MARKETPLACE_COMMISSION

A more-negative completed actual commission burden than governed expectation may
be unfavorable leakage.

### MARKETPLACE_FEE

A more-negative completed actual marketplace fee than governed expectation may
be unfavorable leakage.

### SHIPPING

A more-negative completed actual shipping burden than governed expectation may
be unfavorable leakage where current authority is sufficient.

### FINANCIAL_COST

A more-negative completed actual financial cost than governed expectation may
be unfavorable leakage where current authority is sufficient.

## Unsupported interpretations

TASK-0165N does not infer leakage for:

- advertising;
- tax;
- other adjustments;
- settlement;
- payment account;
- bank.

A variance in these stages remains `UNQUANTIFIED` unless future governed semantics
explicitly authorize interpretation.

## Partial reconciliation rule

`PARTIALLY_RECONCILED` must fail closed.

It cannot produce:

- `UNFAVORABLE_LEAKAGE`;
- `FAVORABLE_VARIANCE`.

It produces:

`UNQUANTIFIED / RECONCILIATION_INCOMPLETE`

## Missing versus zero

missing expected != expected 0

missing actual != actual 0

Explicitly observed zero remains valid.

## Contradiction

Contradictory authority fails closed.

The system must not:

- average contradictory facts;
- select newest merely because it is newest;
- infer provider precedence;
- infer identity;
- infer currency;
- infer quantity;
- infer allocation;
- infer causality.

## Reconciliation authority bridge

`EconomicTruthReconciliationAuthorityBridge`:

- preserves upstream authority evidence;
- binds reconciliation status;
- adds financial trace provenance;
- adds order provenance;
- adds policy provenance;
- adds effective expected entry provenance;
- adds effective actual entry provenance;
- rejects conflicting pre-existing reconciliation status.

## Readiness interaction

`EconomicTruthReadiness` remains the readiness engine.

TASK-0165N does not create another readiness evaluator.

A narrow profile may remain ready when reconciliation is optional.

Profiles requiring reconciliation remain not ready while required reconciliation
is unresolved.

Economic completeness does not imply reconciliation.

Reconciliation does not imply leakage.

Leakage does not imply causality.

Leakage does not imply recommendation.

Leakage does not imply authority.

Leakage does not imply execution.

## Persistence

No TASK-0165N persistence is required for leakage interpretation.

The layer is a governed derivative over existing financial reconciliation and
authority evidence.

## API rule

The existing reconciliation read seam is the preferred Decision Room boundary.

A durable reconciliation case by itself is insufficient to claim governed leakage
unless the required authority context can also be assembled.

When such authority is unavailable, the API must remain truthful and avoid a
quantified leakage claim.

## Security and mutation

TASK-0165N introduces:

- no provider write;
- no recovery action;
- no autonomous recommendation;
- no execution authority;
- no credential exposure.