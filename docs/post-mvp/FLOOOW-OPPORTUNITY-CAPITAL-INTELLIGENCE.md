# FLOOOW Opportunity Capital Intelligence

Status: PREPARED_POST_MVP_RESEARCH
Implementation authority: NONE
MVP dependency: NONE
MVP critical path impact: NONE

Classification:
EVOLVE existing Opportunity Capital Foundry
+ COMPOSE REA-X + GECG + LEWM + Decision/Outcome ancestry.

## Thesis

FLOOOW must not begin as a public investment marketplace.

FLOOOW should transform governed business opportunities into
evidence-bound capital decisions, determine how much capital is
economically defensible, compare candidate capital structures,
trace deployed capital through the operating cycle, reconcile
expected versus realized return, and preserve institutional learning.

Canonical chain:

Economic Truth
→ Opportunity
→ Economic Scenario & Capital Context
→ Opportunity Capital Economics
→ Capital Efficiency Frontier
→ Investment Readiness
→ Capital Structure Candidate
→ Governed Capital Decision
→ Capital Trace
→ Operating Outcome
→ Capital Outcome
→ Causal Qualification
→ Capital Performance Memory

## Constitutional distinctions

Opportunity != Investment Instrument
Investment Readiness != Solicitation Authority
Forecast != Economic Truth
Scenario != Economic Truth
Recommendation != Investment Authority
Capital Committed != Capital Deployed
Execution != Outcome
Outcome != Causation
Expected Return != Actual Return

UNKNOWN != REJECT
MISSING != ZERO

## 1. Economic Scenario & Capital Context

Candidate contract:

DecisionEconomicContext

Realized state may include:

- CDI / Selic / effective funding rate
- inflation
- FX
- freight
- duties
- taxes
- relevant commodities/input prices
- working-capital duration
- cash-conversion cycle

Expected state may include:

- qualified market expectations
- external forecasts
- internal model hypotheses
- competing hypotheses
- base scenario
- upside
- downside
- stress

Every forecast retains:

SOURCE
AS_OF
VALIDITY_HORIZON
PROVENANCE
UNCERTAINTY
MODEL_OR_METHOD
SCENARIO_ID

Realized macro evidence and future scenarios MUST NOT collapse into
the same truth class.

## 2. Opportunity Capital Economics

For each Opportunity Asset evaluate where applicable:

CAPITAL_REQUIRED
CAPITAL_BY_STAGE
PEAK_CAPITAL_AT_RISK
CASH_CONVERSION_CYCLE
CAPITAL_DURATION

MOIC
IRR_TIR
NPV_VPL
PAYBACK

EXPECTED_ECONOMIC_VALUE
EXPECTED_LOSS
PROBABILITY_OF_LOSS
STRESS_LOSS

BENCHMARK_RETURN
EXCESS_RETURN_OVER_BENCHMARK
LIQUIDITY_ADJUSTMENT
RISK_ADJUSTED_RETURN

FX_SENSITIVITY
RATE_SENSITIVITY
INFLATION_SENSITIVITY
DEMAND_SENSITIVITY
INVENTORY_DURATION_SENSITIVITY

BREAK_EVEN_FX
BREAK_EVEN_PRICE
MINIMUM_VOLUME
MINIMUM_SELL_THROUGH
MAXIMUM_INVENTORY_DAYS
MAXIMUM_ECONOMIC_CAPITAL_COST

No opaque investment score may replace the underlying dimensions.

## 3. Capital Efficiency Frontier

FLOOOW must distinguish:

CAPITAL_REQUIRED

CAPITAL_OPTIMAL

CAPITAL_MAXIMUM_ECONOMICALLY_DEFENSIBLE

CAPITAL_REQUESTED

The system evaluates the marginal economic value of additional capital.

Possible result:

DO_NOT_RAISE_REQUESTED_AMOUNT

when additional capital reduces risk-adjusted economic value through:

- inventory saturation
- declining marginal demand
- CAC expansion
- discounting
- obsolescence
- longer duration
- working-capital drag
- concentration
- execution constraints

Capital size is an economic decision, not a fundraising target.

## 4. Decision Robustness

Do not optimize only expected return.

Evaluate:

PROBABILITY_POSITIVE_RETURN
PROBABILITY_CAPITAL_IMPAIRMENT
SCENARIO_SURVIVAL_RATE
BREAK_EVEN_THRESHOLDS
DOWNSIDE_CONCENTRATION
TIME_TO_IRRECOVERABILITY
REVERSIBILITY
RECOVERY_OPTIONS

A lower-return opportunity may economically dominate a higher-return
opportunity when robustness, liquidity, downside and capital efficiency
are materially superior.

## 5. Investment Readiness

Candidate states:

NOT_READY_MISSING_EVIDENCE
NOT_READY_CONTRADICTED
NOT_READY_ECONOMICS
NOT_READY_CAPITAL_STRUCTURE

READY_FOR_STRUCTURING
READY_FOR_POLICY_REVIEW
READY_FOR_INVESTMENT_AUTHORITY_REVIEW

No readiness state authorizes investor solicitation.

Readiness requires, where applicable:

- governed opportunity thesis
- demand evidence
- unit economics
- capital requirement
- capital efficiency frontier
- scenario analysis
- stress analysis
- return decomposition
- risk decomposition
- unknowns
- kill rules
- evidence quality
- operator/execution capability
- monitoring plan
- expected/actual reconciliation contract

## 6. Capital Structure Intelligence

FLOOOW may economically compare candidates such as:

DEBT
REVENUE_PARTICIPATION
PROFIT_PARTICIPATION
PREFERRED_RETURN_PLUS_RESIDUAL
EQUITY
PROJECT_OR_SPV_ECONOMICS
RECEIVABLES_FINANCING
INVENTORY_FINANCING
PURCHASE_ORDER_FINANCING

These are analytical candidates only.

No legal vehicle, security, public offering or solicitation mechanism
is selected or authorized by this document.

Decompose:

RETURN_TO_CAPITAL
RISK_PREMIUM
OPERATOR_ECONOMICS
RESIDUAL_ALPHA
FEES
LOSS_ABSORPTION
PRIORITY_OF_PAYMENTS

## 7. Opportunity Capital Twin

Candidate governed projection:

IDENTITY
THESIS
CAPITAL_USE
CAPITAL_TIMELINE

EXPECTED_CASH_FLOWS

P50_DURATION
P90_DURATION

EXPECTED_RETURN
BENCHMARK_EXCESS_RETURN

DOWNSIDE
STRESS_CASE
PROBABILITY_OF_LOSS

BREAK_EVEN_THRESHOLDS

CAPITAL_OPTIMAL
CAPITAL_MAXIMUM

CAPITAL_STRUCTURE_CANDIDATE

SUPPORTING_EVIDENCE
CONTRADICTING_EVIDENCE
UNKNOWNS
KILL_RULES

READINESS
PROVENANCE

The Opportunity Capital Twin is NOT itself a security or investment
recommendation.

## 8. Capital Trace

Trace:

Capital Committed
→ Capital Called
→ Capital Deployed
→ Supplier
→ Production
→ Goods
→ Transit
→ Inventory
→ Sale
→ Receivable
→ Cash
→ Capital Returned
→ Investor Economic Return
→ Operator Economic Return
→ Residual Economic Outcome

Each transition retains:

EVIDENCE
TIME
AUTHORITY
AMOUNT
CURRENCY
ECONOMIC_EFFECT
PROVENANCE
RECONCILIATION_STATUS

Capital Trace MUST reuse governed evidence/ledger/reconciliation ancestry.

SECOND_LEDGER=PROHIBITED

## 9. Capital Performance Memory

Preserve expected versus realized:

EXPECTED_RETURN / ACTUAL_RETURN
EXPECTED_DURATION / ACTUAL_DURATION
EXPECTED_FX / ACTUAL_FX
EXPECTED_DEMAND / ACTUAL_DEMAND
EXPECTED_MARGIN / ACTUAL_MARGIN
EXPECTED_LOSS / ACTUAL_LOSS

Then:

Expected
→ Actual
→ Variance
→ Counterfactual
→ Attribution
→ Causal Qualification
→ Learning Evidence
→ Governed Belief Revision

FLOOOW must distinguish:

GOOD_DECISION_ADVERSE_LUCK
POOR_DECISION_FAVORABLE_LUCK
CORRECT_THESIS_POOR_EXECUTION
WRONG_THESIS_GOOD_EXECUTION
EXTERNAL_REGIME_SHIFT
INTERVENTION_CAUSAL_EFFECT

Outcome alone does not define decision quality.

## 10. Separation of Duties

Preserve:

OPPORTUNITY_ORIGINATOR != ECONOMIC_VERIFIER

ECONOMIC_VERIFIER != INVESTMENT_AUTHORITY

INVESTMENT_AUTHORITY != CAPITAL_CUSTODIAN

CAPITAL_CUSTODIAN != OPERATOR

CREATOR != VERIFIER

Compensation or fundraising incentives may not silently alter
epistemic standards or readiness thresholds.

## 11. Relationship to existing FLOOOW architecture

Economic Truth:
realized economic state.

REA-X:
epistemic qualification.

GECG:
entity, relationship, provenance, time and authority topology.

LEWM:
regime, forecast, uncertainty and competing-scenario context.

Opportunity Intelligence:
opportunity thesis and economic possibility.

Decision Room:
governed decision projection.

P7:
authorized execution, receipt and reconciliation.

P9:
expected versus actual, attribution, causal qualification and learning.

No second Economic Truth.

No second reconciliation engine.

No parallel belief engine.

No parallel authority system.

## 12. Regulatory Boundary

This capability stops at:

CAPITAL_INTELLIGENCE
STRUCTURING_ANALYSIS
INVESTMENT_READINESS
CAPITAL_TRACE
PERFORMANCE_LEARNING

Before any:

PUBLIC_OR_REPEATED_SOLICITATION
SECURITIES_DISTRIBUTION
INVESTOR_MATCHING
CAPITAL_CUSTODY
POOLED_INVESTMENT_VEHICLE
REGULATED_INTERMEDIATION

require:

- dedicated legal/regulatory analysis
- instrument classification
- activity classification
- regulated-party/partner analysis
- tax/corporate analysis
- explicit project-authority promotion

No assumption is made that:

SPV
SCP
contractual participation
token
receivable
debt instrument
private wrapper

avoids securities regulation.

## 13. First benchmark

After MVP stability, run a bounded import-opportunity benchmark.

It must answer:

1. How much capital is required?
2. How much capital is optimal?
3. Where does marginal return decay?
4. What is expected return over benchmark?
5. What are P50/P90 capital-cycle durations?
6. What destroys the thesis?
7. What are break-even FX, price, sell-through and inventory duration?
8. Which candidate capital structure best matches cash-flow and risk?
9. What evidence remains missing?
10. How will capital and realized return be traced and reconciled?

## 14. Promotion gates

POST_MVP_IMPLEMENTATION_AUTHORIZED=NO

MVP_DEPENDENCY=NONE

MVP_CRITICAL_PATH_MUTATION=PROHIBITED

INVESTMENT_SOLICITATION_AUTHORIZED=NO

PUBLIC_OFFERING_AUTHORIZED=NO

CAPITAL_CUSTODY_AUTHORIZED=NO

INVESTOR_MATCHING_AUTHORIZED=NO

LEGAL_VEHICLE_SELECTED=NO

Promotion requires:

- MVP finalized and stable
- ancestry audit
- exact contracts
- benchmark dataset
- scenario provenance rules
- deterministic financial-math tests
- adversarial risk tests
- legal/regulatory classification
- separation-of-duties review
- explicit project-authority decision
