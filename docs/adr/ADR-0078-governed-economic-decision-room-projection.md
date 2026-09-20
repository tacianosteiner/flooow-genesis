# ADR-0078 - Governed Economic Decision Room Projection

Status: Accepted

## Context

`DurableReconciliationCase` is an append-only operational snapshot of divergent financial stages. It is not a canonical `FinancialReconciliationAssessment` and contains no sufficient identity, currency, allocation, or currentness authority. Reconstructing an assessment or economic authority from this snapshot would convert financial variance into unsupported economic leakage.

## Decision

Add a separate read-only Decision Room projection at `GET /v1/economic-decision-room/reconciliation/{caseId}`. The existing `/v1/reconciliation/cases` contract remains unchanged.

`EconomicDecisionRoomProjectionService` loads the organization-scoped durable case and consults two small read seams: `EconomicDecisionRoomAuthoritySource` and `EconomicDecisionRoomReconciliationAssessmentSource`. Authority context is bound to typed organization, case, order, trace, policy, currency, and reconciliation-revision coordinates. The current assessment seam validates declared case/revision and assessment context coordinates before assembly. This is necessary contextual binding, but it is not immutable assessment identity. TASK-0165O therefore does not claim that a returned assessment is the exact historical assessment that produced a case revision. Exact governed assessment identity and case-revision lineage are an upstream dependency to be designed separately; production remains fail-closed until that lineage exists. When governed inputs exist, the service composes only existing boundaries in order:

`EconomicTruthAuthorityAssembler -> EconomicLeakageGovernanceMapper -> MarketplaceEconomicLeakageInterpretation`

The assessment must match the case organization, case ID, revision, order, trace, policy, and currency. Missing required authority produces `NOT_ASSEMBLED`. Missing assessment produces `BLOCKED` with `RECONCILIATION_ASSESSMENT_UNAVAILABLE`. A cross-organization mismatch is externally indistinguishable from an absent case while retaining a safe internal diagnostic. Production is wired to explicit unavailable sources until canonical production sources exist; it therefore fails closed rather than reconstructing evidence.

Durable expected, actual, signed variance, absolute variance, and entry IDs remain visible even while interpretation is blocked. They are labeled variance, never leakage. `totalQuantifiedLeakage` is null whenever any stage is unquantifiable; a known subtotal is never published as a total.

## Invariants

`REAL OPERATIONAL DATA -> ECONOMIC TRUTH -> GOVERNED EVIDENCE -> RECONCILIATION -> ECONOMIC AUTHORITY -> LEAKAGE INTERPRETATION -> DECISION ROOM READ MODEL`

`AGENT != TRUTH`

`AGENT != AUTHORITY`

`Financial variance != Economic leakage`

`Missing != zero`

`Context equivalence != evidence identity`

The projection provides no provider write, mutation, recommendation, action, execution authority, causal claim, truth store, or reconciliation engine.
