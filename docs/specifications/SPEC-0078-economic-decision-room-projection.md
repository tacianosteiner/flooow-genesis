# SPEC-0078 - Economic Decision Room Projection

## Read contract

The authenticated organization and canonical lowercase UUID `caseId` select a `DurableReconciliationCase`. Cross-organization lookup is indistinguishable from not found. The endpoint is GET-only and returns `Cache-Control: no-store`.

The response contains case/order/trace/policy/currency coordinates, case status/revision/time, `READY` or `BLOCKED`, `ASSEMBLED` or `NOT_ASSEMBLED`, typed authority/governance/projection blockers, nullable total quantified leakage, stage-level financial variance and interpretation, entry IDs, and governed provenance references.

## Composition

1. Load the durable case by organization and case ID.
2. Read server-governed authority context through `EconomicDecisionRoomAuthoritySource`, bound to typed organization, case, order, trace, policy, currency, and revision coordinates.
3. Read a governed assessment candidate through `EconomicDecisionRoomReconciliationAssessmentSource`, carrying declared case ID/revision coordinates.
4. Validate those coordinates plus assessment organization, order, trace, policy, and currency against the case. This is contextual validation only; immutable historical assessment identity is outside this slice.
5. Only after successful binding validation, assemble present inputs with `EconomicTruthAuthorityAssembler`.
6. Map assembled authority with `EconomicLeakageGovernanceMapper`.
7. Interpret the governed assessment candidate only after contextual validation with `MarketplaceEconomicLeakageInterpretation`; this slice does not prove immutable historical assessment identity.

No assessment is inferred from durable stage fields. No missing authority is converted to `UNRESOLVED`; absent required inputs remain explicit `EconomicTruthAuthorityAssemblyResult.NotAssembled` reasons.

## Fail-closed rules

- Missing assessment: projection `BLOCKED`, total leakage null, durable variance retained, interpretation absent, stage blocker `RECONCILIATION_ASSESSMENT_UNAVAILABLE`.
- Missing authority: `NOT_ASSEMBLED` and explicit assembly failure reasons.
- Authority or assessment binding mismatch: `NOT_ASSEMBLED`, a causal context blocker, no interpretation, and no leakage total.
- Cross-organization mismatch: the same external not-found response as an absent case; the domain retains only a safe diagnostic category.
- Unresolved, contradictory, or stale authority: governance not permitted and every interpreted line `UNQUANTIFIED`.
- Missing expected/actual, incomplete reconciliation, or unsupported stage: line `UNQUANTIFIED`, no zero synthesis, projection blocked, and total leakage null even if another stage has a known leakage subtotal.
- Only a supported, fully governed reconciliation line may be `UNFAVORABLE_LEAKAGE`, `FAVORABLE_VARIANCE`, or `NO_MATERIAL_VARIANCE`.
- Only unfavorable leakage contributes to `totalQuantifiedLeakage`; favorable variance is not leakage.

Production currently has no governed assessment-by-case lineage or complete authority-context source. The runtime adapters intentionally return unavailable, keeping public responses blocked until those governed sources are implemented. Context equivalence must not be treated as evidence identity.

All enum-valued public fields are closed over their exact canonical values in OpenAPI and guarded by a Kotlin-to-OpenAPI contract test.
