# FLOOOW — Redmoto Product Dataset Plan

Status: ENGINEERING DESIGN — POST-MVP / SEPARATE FROM ROOM CRITICAL PATH
Captured: 2026-10-10
IMPLEMENTATION_AUTHORIZED=NO
PRODUCTION_INTEGRATION_AUTHORIZED=NO
ROOM_CRITICAL_PATH_IMPACT=NONE

This is a proposed documentation contract, not runtime, data-access, model-execution or release authority. Room operational readiness has not been established by this mission.

## Questions and sampling

Can evidence establish same product across listings, variants, compatible accessories and incompatible lookalikes? Can possible private-label equivalents be surfaced without claiming common OEM identity? Do multimodal inputs outperform text-only matching, and does reranking improve precision within approved latency/cost?

PHASE A: 100–250 manually adjudicated pairs. Establish technical evidence sufficiency, rights and inter-reviewer agreement, emphasizing risky false positives and insufficient evidence. PHASE B: 500–1,000 after rubric repair; diversify supplier/base SKU/family, language, missing modalities and hard negatives. PHASE C: 2,000+ high-quality pairs, followed by 5,000–10,000 only when quality and coverage justify it. Do not begin with 10,000 noisy examples. Each phase requires independent adjudication and documented exclusions, not just a count.

Future steward inventories internal SKUs, authorized catalogs, supplier images/technical sheets, known compatibility mappings and permitted listings. Record source rights and acquisition lineage before collecting. Match proposals use balanced positive, negative and abstention strata, not similarity-only selection. Reviewers verify part fit, voltage, capacity, dimensions, generation and pack differences from evidence. Supplier photography reuse triggers grouping and caution, not OEM identity.

Two initial reviewers and a technical tie-break owner preserve disagreement and rationale. Allocate a protected evaluator-controlled test portion using connected leakage groups; Phase A may develop the rubric but cannot later masquerade as untouched gold. Freeze a new gold set after development. Source gaps, missing records and lack of technical fit evidence remain explicit. Rights, owners and actual data availability are unverified; no data has been ingested or partner contacted.

Read [taxonomy](SPEC-POST-MVP-0001-PRODUCT-RELATIONSHIP-TAXONOMY.md), [dataset contract](SPEC-POST-MVP-0001-GOLD-DATASET-CONTRACT.md) and [evaluation](SPEC-POST-MVP-0001-BENCHMARK-EVALUATION-CONTRACT.md) before future collection. Sample adequacy and relation error limits need pre-registration before production eligibility.
