# Research Design — Evidence-Bound Diagnostic + Opportunity Intelligence

Status: research design candidate; no production authorization.

## Purpose

Turn bounded signals into testable explanations and economically comparable opportunities.

It must answer:
- what might explain this?
- what evidence supports each explanation?
- what evidence contradicts it?
- what is missing?
- what would falsify it?
- what is the expected economic value of acting?
- is more information worth more than immediate action?

## Existing Flooow patterns to generalize

The recovery domain already demonstrates a safe pattern:
valid deterministic signals
→ evidence-lineaged hypothesis
→ deterministic/versioned validation
→ insufficient/blocked/validated/rejected
→ stop before authorization/execution.

Growth/Ads Opportunity Intelligence should generalize this discipline without coupling itself to recovery semantics.

## Core objects

RootCauseCandidate
Hypothesis
EvidenceLink
InformationGap
ExpectedEconomicImpact
OpportunityCandidate
OpportunityRankingPolicy
ValueOfInformationAssessment

## Hypothesis candidate semantics

A hypothesis must contain:
- organization/scope;
- subject;
- hypothesis type;
- policy/model version;
- originating signal IDs;
- supporting evidence refs;
- opposing evidence refs;
- unknown/missing evidence;
- validity conditions;
- falsification conditions;
- applicable time window;
- confidence statement;
- confidence basis;
- revision;
- state.

Candidate states:
OPEN
INSUFFICIENT
SUPPORTED
CONTRADICTED
REJECTED
EXPIRED
REQUIRES_EXPERIMENT

No LLM prose alone can transition a hypothesis to SUPPORTED.

## Root-cause reasoning

Prefer structured causal decomposition before open-ended generative reasoning.

Example:
Sales decline
→ traffic?
→ conversion?
→ availability?
→ price?
→ Buy Box?
→ organic rank?
→ paid media?
→ promotion?
→ reputation?
→ category demand?

The LLM may propose additional candidates, but each candidate must map to measurable evidence requirements.

## Information Gap

Candidate fields:
- missingFactType;
- reasonRequired;
- acquisitionMethod;
- acquisitionCost;
- expectedDecisionImpact;
- expiry;
- blocking/non-blocking;
- estimatedValueOfInformation.

Key evolution:
The system should sometimes choose "obtain evidence" as the best next action.

## Expected Economic Impact

Never use a single opaque opportunity score as economic authority.

Represent a distribution/range where possible:
- expected revenue delta;
- expected contribution-margin delta;
- downside;
- upside;
- probability / confidence;
- time-to-impact;
- reversibility;
- inventory/cash implications;
- portfolio externalities.

## OpportunityCandidate

An opportunity is a proposed economic possibility, not a fact.

Candidate contents:
- subject;
- originating hypotheses;
- candidate action family;
- expected economic impact;
- risk;
- reversibility;
- information gaps;
- VOI;
- urgency;
- validity horizon;
- confidence;
- policy version;
- experiment requirement;
- decision readiness.

## Ranking

Ranking should be multi-objective and versioned.

Candidate dimensions:
expected incremental economic value
× confidence
× urgency
× strategic value
× reversibility
− downside
− information risk
− portfolio conflict
− operational cost

Do not collapse dimensions irreversibly; retain the components behind any final rank.

## Adversarial diagnostic rule

For any materially high-impact opportunity:
1. generate best supported explanation;
2. seek strongest competing explanation;
3. seek disconfirming evidence;
4. identify missing evidence;
5. assess whether an experiment is required;
6. only then allow decision readiness.

## Decision-readiness states

NOT_READY_MISSING_EVIDENCE
NOT_READY_CONTRADICTED
READY_RECOMMEND_ONLY
READY_EXPERIMENT
READY_FOR_POLICY_REVIEW

No autonomous execution state belongs in this layer.

## Initial marketplace hypotheses

- sales decline caused by traffic loss;
- sales decline caused by conversion deterioration;
- conversion deterioration caused by price disadvantage;
- ad inefficiency caused by organic cannibalization;
- ad scale constrained by stock;
- ad scale constrained by contribution margin;
- lost impression share caused by budget;
- lost impression share caused by ad rank;
- promotion opportunity economically positive;
- catalog/content weakness constraining paid-media return;
- market demand decline vs seller-specific decline.

## First real-data experiments

EXP-DIAG-001 — structured root-cause precision
Human-labelled cases; compare structured decomposition to free-form LLM diagnosis.

EXP-DIAG-002 — disconfirming evidence
Measure reduction in false confident diagnoses after mandatory opposing-evidence search.

EXP-DIAG-003 — information-gap value
Test whether requesting one missing datum changes decisions enough to justify acquisition cost.

EXP-OPP-001 — opportunity economic ranking
Compare economic ranking against raw ROAS/revenue ranking.

EXP-OPP-002 — shadow decisions
Generate decisions but do not execute; compare predicted vs actual/no-action outcomes when feasible.

## Superiority metrics

- diagnosis precision;
- calibrated confidence;
- false-causal-claim rate;
- economic value captured;
- avoided downside;
- decision regret;
- percentage of high-impact decisions with complete lineage;
- value of evidence acquired;
- human attention saved without degraded quality.

## Future evolution

- Bayesian belief updates;
- causal graphs;
- portfolio-level opportunity conflicts;
- counterfactual simulators;
- scenario trees;
- Monte Carlo impact distributions;
- regret minimization;
- learned strategy validity conditions;
- cross-market transfer under similarity gates;
- autonomy earning based on calibrated historical outcomes.
