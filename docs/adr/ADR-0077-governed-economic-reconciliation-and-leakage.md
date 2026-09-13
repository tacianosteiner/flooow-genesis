# ADR-0077 — Governed Economic Reconciliation and Leakage

Status: Proposed

## Context

Flooow already owns a governed financial reconciliation model through
`MarketplaceFinancialReconciliation`, `FinancialReconciliationAssessment`,
durable reconciliation cases, and systemic divergence handling.

TASK-0165N must not create a second reconciliation engine or a parallel truth store.

The missing capability is downstream economic interpretation of an already-governed
financial variance.

The critical invariant is:

FINANCIAL VARIANCE != ECONOMIC LEAKAGE

And:

LEAKAGE OBSERVATION
!= CAUSALITY
!= RECOMMENDATION
!= AUTHORITY
!= EXECUTION

## Decision

Introduce a read-only economic leakage interpretation layer downstream from the
existing reconciliation authority.

Canonical flow:

FinancialTrace
    ↓
MarketplaceFinancialReconciliation
    ↓
FinancialReconciliationAssessment
    ↓
EconomicTruthReconciliationAuthorityBridge
    ↓
EconomicTruthAuthorityAssessment
    ├──→ EconomicTruthReadiness
    └──→ EconomicLeakageGovernanceMapper
              ↓
      EconomicLeakageGovernance
              ↓
MarketplaceEconomicLeakageInterpretation

No second reconciliation engine is introduced.

No new truth table or leakage ledger is introduced.

No provider mutation is introduced.

## Reconciliation authority

`FinancialReconciliationAssessment` remains the reconciliation authority.

`EconomicTruthReconciliationAuthorityBridge` binds that assessment into the same
`EconomicTruthAuthorityAssessment` consumed by readiness and leakage governance.

A conflicting pre-existing reconciliation status fails closed rather than being
silently replaced.

## Leakage governance

Economic interpretation is permitted only when governed authority for:

- cross-system identity;
- currency;
- quantity/allocation;
- evidence currentness;

is sufficient.

Contradictory, unresolved, stale, or otherwise unsupported authority blocks leakage
interpretation.

## Partial reconciliation

`PARTIALLY_RECONCILED` is not sufficient to claim economic leakage or favorable
variance.

Partial reconciliation may represent incomplete observation rather than a completed
economic outcome.

Therefore:

PARTIALLY_RECONCILED → UNQUANTIFIED

until the reconciliation state supports a completed comparison.

## Supported economic interpretation

Initial interpretation is limited to stages with explicit net-economic semantics:

- `SALE`;
- `MARKETPLACE_COMMISSION`;
- `MARKETPLACE_FEE`;
- `SHIPPING`;
- `PRODUCT_COST`;
- `FINANCIAL_COST`.

The following remain uninterpreted unless stronger authority is introduced:

- `ADVERTISING`;
- `TAX`;
- `OTHER_ADJUSTMENT`;
- `SETTLEMENT`;
- `PAYMENT_ACCOUNT`;
- `BANK`.

## Semantic boundary

LEAKAGE OBSERVATION
!= CAUSALITY
!= RECOMMENDATION
!= AUTHORITY
!= EXECUTION

Leakage is an economic observation, not a diagnosis of why the loss occurred.

It grants no recovery authority and triggers no provider write.

## Missing is not zero

Missing expected or actual evidence is never normalized to zero.

Explicitly observed zero remains valid evidence.

## Provenance

Economic leakage interpretation preserves references to:

- financial trace;
- marketplace order;
- reconciliation policy;
- expected ledger entries;
- actual ledger entries;
- upstream authority evidence references.

## Decision Room

TASK-0165N may expose a read-only projection through the existing reconciliation
read seam, but only when the required governed authority is available.

The API must not fabricate leakage from a durable reconciliation case that lacks
sufficient authority context.

## Consequences

Positive:

- one reconciliation authority;
- one readiness authority object;
- no divergence between Room semantics and readiness semantics;
- fail-closed leakage interpretation;
- replayable provenance;
- no parallel truth store.

Trade-off:

Economic coverage remains intentionally incomplete until authority exists.

This is preferred over false certainty.