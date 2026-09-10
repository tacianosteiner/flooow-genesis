# Research Design — Marketplace Commerce Observability + Signal Intelligence

Status: research design candidate; no production authorization.

## Purpose

Create the first general commerce-intelligence layer downstream of canonical evidence,
Economic Truth, reconciliation and Sales Intelligence.

It must answer:
- what changed?
- where?
- when?
- how large?
- how unusual?
- what economic surface may be affected?
- what evidence supports the signal?
- how fresh is the underlying context?

It MUST NOT answer "why" as an authoritative claim. That belongs to diagnostic intelligence.

## Existing Flooow patterns to reuse

1. Kernel `Signal` concept.
2. Deterministic systemic-divergence signals.
3. Organization-scoped semantics.
4. Versioned evaluation policy.
5. Durable lineage to source evidence.
6. Fail-closed behavior.
7. Incremental change-feed and replay discipline.
8. Derivative-state rule: signal is not canonical truth.

## Proposed conceptual boundary

CommerceObservation
    ↓
SignalDefinition(policy version)
    ↓
SignalEvaluator
    ↓
SignalOccurrence
    ↓
ObservabilityProjection / read model

Do not require an LLM in this path.

## SignalOccurrence candidate fields

- organizationId
- signalId
- signalType
- subjectRef
- policyVersion
- evaluationWindow
- evaluatedAt
- sourceObservationRefs
- sourceEvidenceRefs
- sourceProjectionVersion/ref
- observedValue
- baselineValue?
- delta?
- severity
- confidence? (only if statistically/epistemically defined; never conflated with severity)
- freshnessState
- economicImpactRef?
- explanationFacts
- lifecycleState
- firstDetectedAt
- lastDetectedAt

## Required semantic separations

severity != confidence
magnitude != economic impact
correlation != cause
signal != hypothesis
projection != truth
missing data != zero
stale != absent
provider timestamp != occurrence authority unless explicitly governed

## Evaluation families

### Deterministic threshold signals
Examples:
margin below floor; Economic Truth NotReady; inventory below threshold; budget exhaustion.

### Relative-change signals
Examples:
sales -20% vs accepted baseline; conversion decline; spend acceleration.

### Distribution/anomaly signals
Use robust methods before complex ML:
rolling median; MAD; quantiles; rate-of-change; seasonal peer baseline.

### Cross-signal composites
Examples:
ROAS down + CVR down + price disadvantage.
Composite signal does NOT imply root cause.

## Baseline architecture

A baseline is versioned policy, not a hidden model output.

Candidate baseline types:
- trailing window;
- weekday/time-of-day matched;
- seasonality-adjusted;
- product cohort;
- campaign regime;
- marketplace/category peer;
- experiment control.

Every anomaly must retain the baseline identity/version used.

## Freshness

Every signal evaluation must be able to distinguish:
FRESH
STALE
INSUFFICIENT
UNKNOWN

A signal generated from stale inputs must never look equivalent to one generated from fresh inputs.

## Lifecycle

Candidate states:
OPEN
PERSISTING
RESOLVED
SUPERSEDED
INVALIDATED

Signal lifecycle should avoid alert storms while preserving historical occurrences.

## First real-data experiments

EXP-OBS-001 — deterministic sales/margin change detection
Measure false positives and detection latency.

EXP-OBS-002 — anomaly baseline comparison
Compare simple trailing baseline vs weekday/time matched baseline.

EXP-OBS-003 — signal economic materiality
Test whether economic-impact filtering reduces low-value alerts without suppressing valuable events.

EXP-OBS-004 — freshness fail-closed behavior
Inject stale/missing provider data and prove no false current-state certainty.

## Acceptance metrics for a future production proposal

- deterministic replay;
- organization isolation;
- bounded incremental computation;
- lineage completeness;
- no Economic Truth redefinition;
- explicit freshness;
- false-positive cost characterized;
- stable signal identity/lifecycle;
- measurable detection advantage over raw dashboard thresholds.

## Future evolution

- adaptive baselines;
- change-point detection;
- causal precursors;
- cross-product anomaly propagation;
- market-vs-account decomposition;
- signal interaction graphs;
- drift detection;
- uncertainty-aware alert suppression.
