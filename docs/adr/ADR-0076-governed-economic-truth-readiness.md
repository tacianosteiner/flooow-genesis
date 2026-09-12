# ADR-0076 - Governed Economic Truth Readiness

Status: Accepted

## Context

The append-only `MarketplaceIndependentEconomicEvidence` aggregate records independent economic evidence and supersession history. Evidence presence alone does not establish completeness, reconciliation, or fitness for a decision. Missing facts must never become zero, and one global readiness definition would silently over- or under-authorize different decision classes.

## Decision

Introduce `EconomicTruthReadinessEvaluator`, a deterministic read-only projection over the existing evidence aggregate and explicit upstream identity, currency, allocation, currentness, and reconciliation assessments. It creates no table or ledger and performs no mutation.

The projection reports every repository-native economic component dimension plus identity, currency consistency, quantity/allocation consistency, currentness, and reconciliation. Dimension states are `OBSERVED`, `CANONICAL`, `RECONCILED`, `MISSING`, `CONTRADICTORY`, `STALE`, `UNRESOLVED`, and `NOT_APPLICABLE`. Overall evidence completeness is distinct from profile readiness.

Profiles are explicit: `UNIT_ECONOMICS`, `ADS_PROFITABILITY`, `ORDER_MARGIN`, and `EXECUTIVE_ECONOMIC_HEALTH`. Each exposes required and optional dimensions and its acceptable coverage. Narrow profiles can be ready while broader completeness remains partial. Profiles requiring reconciliation block unless the independent reconciliation assessment is fully reconciled.

Confirmed active evidence is canonical for its asserted coverage; estimated evidence remains observed. Conflicting active complete confirmed assertions fail closed. Superseded-only evidence is stale and cannot satisfy a requirement. Historical references remain visible for audit.

`OTHER_ADJUSTMENT` remains the repository's existing component kind. The projection does not relabel an arbitrary adjustment as a discount or rebate. A profile requiring a dimension with no governed evidence path reports it missing and remains not ready.

## Invariants

`ECONOMIC EVIDENCE != ECONOMIC TRUTH COMPLETENESS != DECISION READINESS != RECOMMENDATION != AUTHORITY != EXECUTION`

`EVIDENCE -> COMPLETENESS EVALUATION -> RECONCILIATION -> DECISION READINESS`

`READINESS != RECOMMENDATION != AUTHORITY != EXECUTION`

Missing cost, ads spend, tax, shipping, or adjustments are not zero. Explicitly observed numeric zero remains a supported fact. No currency, cost, identity, allocation, applicability, or reconciliation state is inferred.

## Consequences

The future Decision Room can explain exactly which facts are supported and which are missing, contradictory, stale, unresolved, partially covered, or unreconciled. The result contains no recommendation, action, execution authority, causality claim, provider write, or canonical truth mutation.
