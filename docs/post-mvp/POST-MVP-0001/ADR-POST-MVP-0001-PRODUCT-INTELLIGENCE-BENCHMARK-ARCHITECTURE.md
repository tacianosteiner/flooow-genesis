# FLOOOW — ADR POST-MVP-0001 — Product Intelligence Benchmark Architecture

Status: ENGINEERING DESIGN — POST-MVP / SEPARATE FROM ROOM CRITICAL PATH
Captured: 2026-10-10
IMPLEMENTATION_AUTHORIZED=NO
PRODUCTION_INTEGRATION_AUTHORIZED=NO
ROOM_CRITICAL_PATH_IMPACT=NONE

This is a proposed documentation contract, not runtime, data-access, model-execution or release authority. Room operational readiness has not been established by this mission.

## Decision and alternatives

Proposed decision: an isolated, reproducible offline lab with rights-cleared snapshots, independently adjudicated pairs, deterministic/lexical comparators, optional challengers and an evaluation-only evidence store. Choose this over direct production model integration and a Room rewrite because it measures incremental value while preserving canonical truth and availability. No harness, baseline or model has been implemented or qualified in this mission.

Conceptual pipeline: approved snapshot -> provenance validation -> taxonomy/adjudication -> grouped split manifest -> deterministic/BM25 baseline -> challengers -> evaluation -> adversarial review -> ADOPT / ADAPT / REJECT proposal -> separately approved shadow.

The future harness consumes a frozen dataset/split/config; adapters emit ranked candidates, scores, relationship proposals and abstention without mutating inputs. Evaluation records artifact digests, seeds, tokenizer/preprocessing revision, hardware, dependency lock, source lineage, failure counts and metrics. Re-running the same inputs must reproduce deterministic results; stochastic variability must be reported across declared seeds. Cache keys include all input/config/model revisions. Offline failures remain explicit and cannot silently remove difficult examples.

Separate data steward, independent adjudicators, evaluator and promotion authority. Model-generated labels cannot self-certify. Gold access is evaluator-only; developers use development/validation. Human corrections create a new dataset version rather than silently changing a published result.

## Boundaries and trade-offs

Isolation costs duplicated controlled snapshots and adjudication effort; benefits are auditability, leakage prevention and no Room mutation. Storage and implementation language are deferred to a later bounded task. No production API, migration, dependency or external execution is authorized. Before execution, pre-register economic error budgets and operating limits; unfilled thresholds block qualification rather than becoming assumed passes.

See [taxonomy](SPEC-POST-MVP-0001-PRODUCT-RELATIONSHIP-TAXONOMY.md), [dataset](SPEC-POST-MVP-0001-GOLD-DATASET-CONTRACT.md), [evaluation](SPEC-POST-MVP-0001-BENCHMARK-EVALUATION-CONTRACT.md), [provenance](SPEC-POST-MVP-0001-EXTERNAL-MODEL-PROVENANCE-CONTRACT.md) and [execution sequence](POST-MVP-0001-EXECUTION-ROADMAP.md).
