# FLOOOW — Post-MVP Engineering Execution Plan
## Room V1 → Product Intelligence → Opportunity Intelligence

**Status:** ENGINEERING EXECUTION BLUEPRINT  
**Version:** 1.0  
**Date:** 2026-10-10  
**Primary audience:** FLOOOW engineering / Codex  
**Critical principle:** Room V1 remains operational while post-MVP capabilities are developed, benchmarked, shadowed and promoted independently.

---

# 1. Executive decision

The correct post-MVP architecture is **not** to replace Room V1 with a large V2 rewrite.

The correct architecture is:

```text
ROOM V1 — STABLE / REAL DATA
          │
          ├────────► Product Intelligence R&D
          ├────────► Evidence Retrieval R&D
          ├────────► Opportunity Intelligence R&D
          ├────────► Foresight R&D
          ├────────► Creator / Distribution Intelligence R&D
          └────────► Capital Opportunity R&D

Each capability moves through:

DISCOVER
→ DATA CONTRACT
→ BASELINE
→ BENCHMARK
→ ADVERSARIAL TEST
→ SHADOW
→ PILOT
→ PROMOTION GATE
→ ROOM VERSION UPGRADE
```

Room V1 is the **institutional truth and operational baseline**.

Experimental intelligence is never allowed to redefine canonical truth merely because a model produces a high score.

---

# 2. Strategic objective

The post-MVP program moves FLOOOW through four capability levels:

```text
LEVEL 1
FLOOOW KNOWS WHAT IS TRUE

LEVEL 2
FLOOOW UNDERSTANDS WHAT IS HAPPENING

LEVEL 3
FLOOOW DISCOVERS WHAT SHOULD BE INVESTIGATED

LEVEL 4
FLOOOW HELPS DETERMINE WHERE CAPITAL SHOULD GO

LEVEL 5
FLOOOW LEARNS WHETHER ITS DECISIONS WERE RIGHT
```

Room V1 completes the foundation for Level 1.

The first post-MVP engineering program targets Level 2.

---

# 3. Non-negotiable production strategy

## 3.1 Room V1 remains active

After `ROOM_OPERATIONAL=YES`, declare an immutable operational milestone:

```text
FLOOOW_ROOM_V1_BASELINE
```

Room V1 continues to receive real-world evidence and outcomes.

Do not freeze business learning.

Do not stop ingestion while post-MVP capabilities are being built.

Do not require experimental AI services for Room V1 availability.

---

## 3.2 Production and research are separate

Use separate runtime and code boundaries.

Conceptual architecture:

```text
                    PRODUCTION
                        │
                  ROOM V1 STABLE
                        │
           canonical/economic truth
                        │
             real outcomes/reconciliation
                        │
                        ▼
                RESEARCH MIRROR
                        │
       ┌────────────────┼────────────────┐
       ▼                ▼                ▼
 PRODUCT INTEL     RETRIEVAL LAB    FORESIGHT LAB
       │                │                │
       └────────────────┼────────────────┘
                        ▼
                   SHADOW OUTPUT
                        │
                  PROMOTION GATE
                        │
                        ▼
                   ROOM V1.x / V2
```

Research systems may **read** approved evidence.

They do not gain authority to mutate canonical production state by default.

---

# 4. Release philosophy

Every new capability receives a maturity state.

```text
DISCOVERED
RESEARCH_APPROVED
DATA_READY
BASELINE_READY
BENCHMARKED
ADVERSARIAL_PASSED
SHADOW
PILOT
PRODUCTION_ELIGIBLE
PRODUCTION_APPROVED
MONITORED
SUPERSEDED
REVOKED
```

No model jumps directly from:

```text
DISCOVERED
```

to:

```text
PRODUCTION
```

---

# 5. Room version model

Recommended strategy:

```text
Room V1.0
Canonical truth + economic truth + reconciliation + authority + governed execution

Room V1.1
Read-only Product Intelligence projections

Room V1.2
Evidence Retrieval / contradiction assistance

Room V1.3
Opportunity candidate projection

Room V1.4
Forecast projections

Room V1.5
Distribution / creator readiness projections

Room V2
Governed Opportunity Decision Room
```

Version numbers are conceptual until architecture review promotes them.

Do not create version churn for internal refactors.

A version upgrade must represent a meaningful capability boundary.

---

# 6. First post-MVP epic

# POST-MVP-0001 — PRODUCT INTELLIGENCE BENCHMARK FOUNDATION

This is the first recommended engineering epic after Room V1 becomes operational.

## Mission

Determine which retrieval, embedding, multimodal and reranking stack produces the highest-quality product understanding on **FLOOOW-owned real product data**, under acceptable latency, cost, security and licensing constraints.

The first goal is **not production integration**.

The first goal is to establish a reproducible capability benchmark.

---

# 7. Candidate technology families

Initial challengers:

## Text retrieval

```text
BM25
vs
BGE-M3
vs
Qwen3 Embedding
```

## Multimodal product matching

```text
Marqo Ecommerce Embeddings
vs
Qwen3-VL Embedding
```

## Reranking

```text
Qwen3 Reranker
vs
Qwen3-VL Reranker
```

These are challenger candidates.

No candidate is pre-selected as winner.

Every external capability must preserve:

```text
source
exact model/revision
license
artifact identity
security posture
runtime requirements
benchmark result
cost
latency
ADOPT / ADAPT / REJECT
```

---

# 8. First proprietary dataset

# FLOOOW Product Intelligence Benchmark v1

This dataset is intended to become a durable FLOOOW asset.

Initial target:

```text
MINIMUM:
2,000 adjudicated product pairs

TARGET:
5,000–10,000 adjudicated product pairs
```

Do not optimize for raw volume before label quality.

2,000 high-quality adjudicated pairs are more valuable than 100,000 noisy pairs.

---

# 9. Required product relationship taxonomy

Initial accepted research taxonomy:

```text
SAME_PRODUCT
VARIANT_OF
SUBSTITUTE_FOR
ACCESSORY_FOR
COMPATIBLE_WITH
INCOMPATIBLE_LOOKALIKE
PRIVATE_LABEL_EQUIVALENT_CANDIDATE
UNRELATED
INSUFFICIENT_EVIDENCE
```

Important distinction:

`PRIVATE_LABEL_EQUIVALENT_CANDIDATE` is intentionally a **candidate** relationship.

Visual similarity alone cannot prove common OEM/manufacturer provenance.

---

# 10. Label semantics

## SAME_PRODUCT

Same commercial/technical product despite:
- different photography;
- different title formatting;
- language differences;
- marketplace listing differences.

Must not silently collapse material variants.

---

## VARIANT_OF

Same product family with a meaningful variant such as:
- color;
- size;
- capacity;
- voltage;
- pack size;
- trim;
- model revision when compatible with taxonomy.

---

## SUBSTITUTE_FOR

Different products capable of satisfying substantially the same customer need.

This is not product identity.

Substitution may be context-dependent.

---

## ACCESSORY_FOR

Product designed to complement another product.

---

## COMPATIBLE_WITH

Technical compatibility supported by evidence.

Do not infer compatibility from visual similarity alone.

---

## INCOMPATIBLE_LOOKALIKE

Visually or textually similar product that must **not** be matched as compatible/same.

This label is strategically important.

Hard negatives are essential.

---

## PRIVATE_LABEL_EQUIVALENT_CANDIDATE

Evidence suggests possible OEM/private-label equivalence.

Requires future corroboration such as:
- specifications;
- dimensions;
- construction details;
- certification;
- packaging;
- supplier/manufacturer evidence;
- tooling evidence;
- documentation.

Never promote to canonical common-manufacturer identity from embedding similarity alone.

---

## UNRELATED

No meaningful product relationship within the benchmark task.

---

## INSUFFICIENT_EVIDENCE

Available evidence cannot safely establish another relationship.

This is a first-class label.

The model must be allowed to abstain.

---

# 11. Required source data

Product examples should increasingly include real FLOOOW operating data where legally and commercially permitted:

```text
internal SKUs
Redmoto products
supplier catalogs
China supplier images
technical sheets
product titles
descriptions
attributes
dimensions
packaging
marketplace listings
competitor listings
historical product mapping
known compatibility records
known hard negatives
```

All samples require provenance.

---

# 12. Dataset record contract

Conceptual schema:

```text
ProductPairExample {
    example_id

    product_a_identity
    product_b_identity

    relationship_label

    title_a
    title_b

    description_a
    description_b

    attributes_a
    attributes_b

    image_refs_a[]
    image_refs_b[]

    source_refs[]

    adjudication_status
    adjudicator
    adjudicated_at

    evidence_refs[]

    difficulty_class
    hard_negative

    notes
}
```

Exact implementation language/storage is deferred to engineering design review.

---

# 13. Provenance contract

Every benchmark sample must preserve:

```text
SOURCE
SOURCE_TYPE
SOURCE_ID
ACQUISITION_TIME
DATA_RIGHTS_CLASS
TRANSFORMATION_HISTORY
LABEL_PROVENANCE
```

No unlabeled scraped corpus silently enters the gold dataset.

---

# 14. Gold set protection

The benchmark must prevent evaluation contamination.

Required splits:

```text
TRAIN / DEVELOPMENT
VALIDATION
GOLD TEST
ADVERSARIAL TEST
```

The GOLD TEST set must not be used for iterative prompt/model tuning.

The ADVERSARIAL TEST set must contain deliberately difficult cases.

---

# 15. Leakage prevention

Never allow highly related examples to cross evaluation boundaries when doing so would make the benchmark artificially easy.

Examples requiring grouping:

```text
same supplier family
same base SKU
same product family
same listing duplicated across marketplaces
same image reused
same catalog family
same OEM candidate group
```

Use grouped splitting where appropriate.

---

# 16. Hard-negative program

At least one dedicated benchmark subset must focus on errors that create economic harm.

Examples:

```text
same-looking incompatible motorcycle part

same packaging but different specification

same product title with different voltage

same accessory family but incompatible generation

different capacity product with nearly identical image

different OEM products sharing generic supplier photography

fake/private-label visual similarity without provenance
```

Track false-positive rate separately.

A product-intelligence system that retrieves many true matches but creates dangerous false matches is not production-ready.

---

# 17. Deterministic baseline

Before benchmarking modern embedding models, create a reproducible deterministic baseline.

Candidates:

```text
exact identifiers when available
normalized title match
attribute overlap
lexical BM25
brand/model tokens
dimensions/specification rules
```

The purpose is not to outperform AI.

The purpose is to know whether AI provides actual incremental value.

---

# 18. Benchmark tasks

## Task A — Retrieval

Given product A:

```text
retrieve top K related product candidates
```

Metrics:

```text
Recall@1
Recall@5
Recall@10
MRR
nDCG@K
```

---

## Task B — Pair classification

Given A and B:

predict relationship taxonomy.

Metrics:

```text
macro F1
per-class precision
per-class recall
confusion matrix
abstention quality
```

---

## Task C — Hard negatives

Primary metric:

```text
FALSE_MATCH_RATE
```

Track especially:

```text
SAME_PRODUCT false positives
COMPATIBLE_WITH false positives
PRIVATE_LABEL_EQUIVALENT false positives
```

---

## Task D — Multimodal retrieval

Compare:

```text
text only
image only
text + image
text + image + structured attributes
```

Goal:

measure whether multimodal evidence materially improves product matching.

---

## Task E — Reranking

Compare:

```text
retrieval only
vs
retrieval + reranker
```

Evaluate gain vs:
- latency;
- infrastructure;
- cost;
- complexity.

---

# 19. Benchmark dimensions beyond accuracy

Every candidate must be evaluated on:

```text
QUALITY
LATENCY
THROUGHPUT
MEMORY
GPU REQUIREMENT
CPU VIABILITY
COST PER 1K ITEMS
MODEL SIZE
LICENSE
SECURITY
REMOTE CODE REQUIREMENT
DATA PRIVACY
DEPLOYMENT COMPLEXITY
OPERABILITY
FAILURE MODES
```

No model wins because it has the highest benchmark score alone.

---

# 20. Candidate decision contract

Each candidate receives:

```text
ADOPT
ADAPT
REJECT
```

Example:

```text
MODEL
Qwen3-Embedding

QUALITY
PASS

SECURITY
PASS

LICENSE
PASS

LATENCY
PASS

COST
PASS

DECISION
ADOPT
```

Or:

```text
MODEL
X

QUALITY
BEST

SECURITY
BLOCKED

DECISION
REJECT
```

Security/license gates dominate quality.

---

# 21. Shadow architecture

After a candidate wins the lab:

Do NOT immediately make it authoritative.

Deploy in shadow/read-only mode:

```text
REAL PRODUCT EVENT
       │
       ├────────► Room V1 canonical path
       │
       └────────► Product Intelligence Shadow
                         ↓
                  candidate relationships
                         ↓
                    evidence only
```

Shadow output cannot mutate canonical identity.

---

# 22. Shadow evaluation

Compare model outputs against:

```text
human adjudication
known product mappings
actual operational outcomes
future corrections
```

Measure:

```text
precision
recall
false matches
abstention
stability
drift
latency
cost
```

---

# 23. Human adjudication loop

During early phases:

```text
MODEL PROPOSES
      ↓
HUMAN ADJUDICATES
      ↓
EVIDENCE RECORDED
      ↓
GOLD DATASET IMPROVES
```

Do not automatically turn model output into training truth.

Model-generated labels must never self-certify.

---

# 24. Production promotion gate

A Product Intelligence capability becomes production-eligible only when:

```text
QUALITY_GATE=PASS
HARD_NEGATIVE_GATE=PASS
SECURITY_GATE=PASS
LICENSE_GATE=PASS
PROVENANCE_GATE=PASS
LATENCY_GATE=PASS
COST_GATE=PASS
SHADOW_GATE=PASS
ADVERSARIAL_GATE=PASS
```

Then:

```text
PRODUCTION_ELIGIBLE=YES
```

still does not mean:

```text
PRODUCTION_APPROVED=YES
```

Promotion remains explicit.

---

# 25. Initial Room integration

First integration should be **read-only**.

Example future Room projection:

```text
PRODUCT INTELLIGENCE

Observed product:
SKU-18931

Potential relationships:

SAME_PRODUCT
Marketplace listing X
confidence...
evidence...

VARIANT_OF
SKU-19321
evidence...

PRIVATE_LABEL_EQUIVALENT_CANDIDATE
Supplier item CN-827
evidence...
```

Never silently rewrite canonical product identity.

---

# 26. POST-MVP-0002 — Evidence Retrieval Engine

Starts after Product Intelligence Foundation has a stable benchmark architecture.

Mission:

Find supporting and contradictory evidence for business/economic claims.

Conceptual pipeline:

```text
QUESTION / CLAIM
      ↓
RETRIEVAL
      ↓
RERANKING
      ↓
SUPPORTING EVIDENCE
      +
CONTRADICTORY EVIDENCE
      ↓
PROVENANCE
      ↓
HYPOTHESIS
```

Output remains read-only/inferred until governed promotion.

---

# 27. POST-MVP-0003 — Opportunity Engine v1

Prerequisites:

```text
Room V1 operational
Product Intelligence usable
Evidence Retrieval usable
Economic Truth populated
```

First question:

> What should we investigate that humans have not explicitly asked FLOOOW to investigate?

Pipeline:

```text
ECONOMIC TRUTH
+
PRODUCT GRAPH
+
MARKET EVIDENCE
+
SUPPLIER EVIDENCE
+
COMPETITION
        ↓
OPPORTUNITY CANDIDATE
        ↓
UNCERTAINTY
        ↓
VALUE OF INFORMATION
        ↓
NEXT BEST INFORMATION
        ↓
KILL RULES
        ↓
ROOM
```

---

# 28. First real opportunity laboratory — Redmoto

Canonical research question:

> If Redmoto received R$1,000,000 of additional capital today, where should that capital go to maximize risk-adjusted economic value?

Candidate comparisons may include:

```text
core inventory
ads
new core SKU
adjacent category
motocross boots
adventure luggage
electronics
new brand
acquisition
do not invest
```

`DO_NOT_INVEST` must remain a valid answer.

---

# 29. Capital gates

Future opportunities use:

```text
RESEARCH
→ SAMPLE
→ PROTOTYPE
→ VALIDATION
→ PILOT
→ SCALE
```

Every gate must define:

```text
CAPITAL_REQUIRED
MAXIMUM_LOSS
EVIDENCE_REQUIRED
WHAT_MUST_BE_TRUE
KILL_RULE
NEXT_BEST_INFORMATION
```

Strategic principle:

# Capital is earned by evidence.

---

# 30. POST-MVP-0004 — Premium Beverage Intelligence Lab

Runs after initial Product Intelligence / Opportunity foundations are usable.

Purpose:

Force FLOOOW beyond marketplace-only intelligence.

Tests:

```text
physical retail
assortment
store clusters
sell-in
sell-out
shelf availability
retail media
QR/product experience
shopper evidence
repeat purchase
incremental contribution
```

This begins the Commerce Evidence Graph.

---

# 31. POST-MVP-0005 — Foresight Engine

Do not start forecasting before adequate time-series truth exists.

Future targets:

```text
demand distribution
stockout probability
sell-through
lead-time risk
margin trajectory
capital requirement
```

Forecasts remain typed:

```text
FORECAST
```

never:

```text
ACTUAL
```

---

# 32. POST-MVP-0006 — Creator / Distribution Intelligence

Purpose:

Answer:

> If we build this product, is there a plausible economical route to customers?

Future concepts:

```text
creator graph
audience overlap
unique reach estimation
category-qualified reach
creator-product fit
commercial saturation
content demand
activation economics
observed conversion
```

Followers are not distribution.

---

# 33. POST-MVP-0007 — Capital Opportunity Engine

Prerequisites:

```text
reliable Opportunity Engine
real outcome history
calibrated uncertainty
capital-gate evidence
```

Capabilities:

```text
Opportunity Asset
Capital Thesis
Capital Opportunity Frontier
Portfolio Allocation
NewCo / existing brand / acquisition comparison
```

Do not create public investment marketplace functionality as part of this epic.

---

# 34. Long-term architecture

```text
                            FLOOOW
                              │
                       ROOM / TRUTH
                              │
                ┌─────────────┼─────────────┐
                ▼             ▼             ▼
             PRODUCT       EVIDENCE      FORESIGHT
          INTELLIGENCE     RETRIEVAL
                │             │             │
                └─────────────┼─────────────┘
                              ▼
                       OPPORTUNITY ENGINE
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
           PRODUCT         SUPPLIER        DISTRIBUTION
             GRAPH        INTELLIGENCE     INTELLIGENCE
              │               │               │
              └───────────────┼───────────────┘
                              ▼
                       OPPORTUNITY ASSET
                              │
                              ▼
                        CAPITAL THESIS
                              │
                              ▼
                         CAPITAL GATES
                              │
                              ▼
                           EXECUTION
                              │
                              ▼
                            OUTCOME
                              │
                              ▼
                       RECONCILIATION
                              │
                              ▼
                           LEARNING
```

---

# 35. Engineering branch strategy

Recommended branch families:

```text
research/product-intelligence-benchmark
feature/product-intelligence-shadow
research/evidence-retrieval-engine
feature/evidence-retrieval-shadow
research/opportunity-engine
feature/opportunity-engine-shadow
research/foresight-engine
research/creator-distribution-intelligence
research/capital-opportunity-engine
```

Do not use the Room V1 maintenance branch as an experimental integration branch.

---

# 36. Data ownership strategy

The strongest long-term asset is not a model checkpoint.

It is the accumulated proprietary evidence:

```text
product relationships
hard negatives
supplier relationships
market outcomes
economic outcomes
creator outcomes
distribution outcomes
forecast errors
capital decisions
actual returns
```

Models can be replaced.

This institutional dataset compounds.

---

# 37. Research-source DNA

Every external capability must identify its source.

Examples:

```text
SOURCE=GitHub official NVIDIA repository
SOURCE_TYPE=OPEN_SOURCE_REPOSITORY

SOURCE=Hugging Face model card
SOURCE_TYPE=MODEL_HUB

SOURCE=Walmart first-party documentation
SOURCE_TYPE=FIRST_PARTY_PLAYER

SOURCE=academic paper
SOURCE_TYPE=ACADEMIC
```

No external claim silently becomes FLOOOW truth.

---

# 38. Success criterion for post-MVP program

The program succeeds when FLOOOW can move from:

```text
“tell me what happened”
```

to:

```text
“I found an economically meaningful condition
you were not explicitly looking for.

Here is the evidence.

Here is what contradicts it.

Here is the uncertainty.

Here is the cheapest next experiment.

Here is what would kill the hypothesis.

Do not deploy large capital yet.”
```

That is the transition from analytics to governed opportunity intelligence.

---

# 39. Immediate engineering order

After Room V1 operational proof:

```text
STEP 0
Freeze Room V1 operational baseline.

STEP 1
Instrument Room outcomes and learning.

STEP 2
Create POST-MVP-0001 Product Intelligence Benchmark Foundation.

STEP 3
Build Product Intelligence Benchmark v1 dataset contract.

STEP 4
Build deterministic/BM25 baseline.

STEP 5
Benchmark BGE-M3 / Qwen3 Embedding.

STEP 6
Benchmark Marqo Ecommerce / Qwen3-VL.

STEP 7
Benchmark rerankers.

STEP 8
Run hard-negative adversarial gate.

STEP 9
Choose ADOPT / ADAPT / REJECT.

STEP 10
Deploy winner in read-only shadow mode.

STEP 11
Accumulate real-world adjudication.

STEP 12
Promote Product Intelligence projection only after promotion gate.
```

---

# 40. First Codex delivery package

Codex should initially produce only the foundation package:

```text
ADR — Product Intelligence Benchmark Architecture

SPEC — Product Intelligence Benchmark Contract

SPEC — Product Relationship Taxonomy

SPEC — Gold Dataset / Split / Leakage Contract

SPEC — External Model Provenance & Promotion Contract

Benchmark dataset schema

Benchmark harness architecture

Deterministic baseline

BM25 baseline

Evaluation metrics

Hard-negative suite

Evidence directory

Execution roadmap
```

Do not integrate external models into production in the first delivery.

---

# 41. First engineering gate

Required return:

```text
ROOM_V1_CHANGED=NO

PRODUCT_INTELLIGENCE_ARCHITECTURE=PASS
DATASET_CONTRACT=PASS
TAXONOMY_CONTRACT=PASS
GOLD_SPLIT_CONTRACT=PASS
LEAKAGE_GUARD=PASS
HARD_NEGATIVE_CONTRACT=PASS
PROVENANCE_CONTRACT=PASS
DETERMINISTIC_BASELINE=PASS
BM25_BASELINE=PASS

EXTERNAL_MODEL_RUNTIME_ENABLED=NO
PRODUCTION_MUTATION=NO

NEXT=MODEL_CHALLENGER_BENCHMARKS
```

---

# 42. Governing principle

Room V1 must remain useful while FLOOOW evolves.

The system evolves by **adding proven intelligence around a stable truth core**, not by repeatedly rebuilding the truth core.

The expected lifecycle is:

```text
stable truth
    ↓
experimental intelligence
    ↓
shadow evidence
    ↓
measured superiority
    ↓
governed promotion
    ↓
new Room capability
```

This is the recommended FLOOOW post-MVP engineering path.
