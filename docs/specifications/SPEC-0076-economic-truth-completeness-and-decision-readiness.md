# SPEC-0076 - Economic Truth Completeness and Decision Readiness

## Input contract

`EconomicTruthReadinessEvaluator.evaluate` accepts one organization-scoped `MarketplaceIndependentEconomicEvidence` aggregate, explicit governed authority assessments, a decision profile, and a microsecond-precision evaluation timestamp. Authority inputs cover cross-system identity, currency, exact quantity/allocation, evidence currentness, and the existing `FinancialReconciliationStatus`.

The evaluator is pure and read-only. Callers must obtain organization and authority inputs from authenticated, server-governed contexts; caller text is not authority.

## Profiles

- `UNIT_ECONOMICS` requires identity, revenue, product cost, marketplace fee, currency, allocation, and currentness. Partial component coverage is acceptable for the exact governed occurrence.
- `ADS_PROFITABILITY` adds advertising and fully reconciled evidence.
- `ORDER_MARGIN` adds marketplace commission, shipping, tax, other adjustment, and reconciliation and requires complete component coverage. Contextually inapplicable dimensions may be explicitly `NOT_APPLICABLE`; applicability is never inferred.
- `EXECUTIVE_ECONOMIC_HEALTH` requires every dimension, complete coverage, and reconciliation. A component kind without a governed evidence path remains `MISSING`.

Every result exposes required, optional, satisfied, missing, contradictory, stale/superseded, and unresolved dimensions; per-dimension coverage; supported component facts; active/historical observation references; authority references; reconciliation state; overall completeness; readiness status; and typed blocking reasons.

## Evaluation rules

- No active or historical fact is `MISSING`.
- Historical but no active fact is `STALE` and does not satisfy readiness.
- Estimated active evidence is `OBSERVED`; it does not satisfy a canonical requirement.
- Confirmed active evidence is `CANONICAL` at its asserted `PARTIAL` or `COMPLETE` coverage.
- Distinct active complete confirmed meanings for a component dimension are `CONTRADICTORY`; no newest, largest, smallest, average, or provider-priority heuristic is used.
- `FinancialReconciliationStatus.FULLY_RECONCILED` is `RECONCILED`; pending or partial is unresolved; divergence is contradictory.
- Missing, stale, contradictory, unresolved, or insufficiently covered required dimensions produce `NOT_READY` with exact dimension/reason pairs.
- Optional missing dimensions remain visible but do not block the profile.

Numeric zero is preserved only as an explicitly sourced `EconomicComponent`. Absence produces an empty supported-facts list and never manufactures money.

## Safety boundary

`EVIDENCE -> COMPLETENESS EVALUATION -> RECONCILIATION -> DECISION READINESS`

`READINESS != RECOMMENDATION != AUTHORITY != EXECUTION`

The projection has no recommendation/action fields, no provider connector, no persistence write, no currency or cost default, and no new truth/readiness table. It does not claim causality or canonicalize itself.
