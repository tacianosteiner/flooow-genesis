# FLOOOW — Post-MVP Roadmap Addendum: Tenant-Neutral Evolution

Status: ROADMAP ADDENDUM
Date: 2026-10-10

This addendum applies to all post-MVP phases.

## Mandatory invariant

```text
REFERENCE BUSINESS != PLATFORM
REFERENCE COHORT != CORE DEPENDENCY
VERTICAL EVIDENCE != UNIVERSAL SEMANTICS
```

## Updated post-MVP sequence

```text
ROOM V1 — TENANT-NEUTRAL / REAL DATA
        ↓
OUTCOME / LEARNING BASELINE
        ↓
PRODUCT INTELLIGENCE BENCHMARK
        │
        ├── Cohort A: Redmoto (initial real-world validation)
        ├── Cohort B: Premium beverages
        ├── Cohort C: future external/customer vertical
        └── additional cohorts
        ↓
CROSS-COHORT GENERALIZATION GATE
        ↓
EVIDENCE RETRIEVAL
        ↓
OPPORTUNITY ENGINE
        ↓
VERTICAL / TENANT LABS
        ↓
FORESIGHT
        ↓
DISTRIBUTION INTELLIGENCE
        ↓
CAPITAL OPPORTUNITY ENGINE
```

## Redmoto wording correction

Replace ambiguous wording such as:

```text
Redmoto Product Intelligence Benchmark
Redmoto Opportunity Engine
```

with:

```text
FLOOOW Product Intelligence Benchmark
  cohort: REDMOTO_INITIAL_REAL_WORLD_COHORT

FLOOOW Opportunity Engine
  validation lab: REDMOTO_REFERENCE_LAB
```

## Promotion requirement

Before claiming a capability as general FLOOOW functionality:

```text
REFERENCE_COHORT_PASS=YES
SECOND_COHORT_PASS=YES
CROSS_COHORT_VARIANCE_ASSESSED=YES
OUT_OF_DOMAIN_LIMITS_DOCUMENTED=YES
TENANT_NEUTRALITY_GATE=PASS
```

This rule does not require every feature to work identically in every industry.
It requires the core abstraction to remain general and vertical specialization to be explicit.
