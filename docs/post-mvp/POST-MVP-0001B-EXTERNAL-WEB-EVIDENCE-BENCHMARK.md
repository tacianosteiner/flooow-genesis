# FLOOOW — POST-MVP-0001B External Web Evidence Benchmark

Status: RESEARCH / BENCHMARK DESIGN — POST-MVP
Captured: 2026-10-10

```text
IMPLEMENTATION_AUTHORIZED=NO
PRODUCTION_INTEGRATION_AUTHORIZED=NO
ROOM_CRITICAL_PATH_IMPACT=NONE
PACKAGE_0090_IMPACT=NONE
ROOM_RUNTIME_IMPACT=NONE
COLLECTOR_OUTPUT_IS_NOT_TRUTH=YES
COLLECTOR_OUTPUT_IS_NOT_AUTHORITY=YES
EXTERNAL_EVIDENCE_REQUIRES_GOVERNED_PROMOTION=YES
PROVIDER_SELECTED=NO
FREE_FIRST_BENCHMARK=YES
```

## Purpose and boundary

Design a vendor-neutral external web evidence acquisition benchmark serving Product Intelligence, Evidence Retrieval, Opportunity Intelligence, Retail / Commerce Intelligence and the External Intelligence Capability Radar. This registers future research; it runs no acquisition or integration.

The strategic objective is a governed acquisition layer that continuously supplies evidence while truth, authority, reconciliation, decision and execution remain inside FLOOOW. Acquisition tools cannot redefine Economic Truth, create authority, allocate capital or execute decisions.

```text
External source
  -> collector / crawler / browser
  -> raw captured evidence
  -> provenance + content hash + retrieval context
  -> extraction / normalization candidate
  -> validation / contradiction
  -> Governed External Intelligence Evidence
  -> Evidence Ledger
  -> Economic Truth / Product Intelligence
  -> Opportunity / Decision Room
```

## Candidate register

These roles and dispositions are supplied research hypotheses, not verified vendor capabilities, measured results or adoption decisions. Official documentation, terms and current capabilities must be checked during source/license/security triage before any experiment.

| Candidate | Role to benchmark | Disposition | Initial test priority |
|---|---|---|---|
| APIFY | Production-style collection jobs, actors, scheduling and datasets | BENCHMARK_ADAPT | 1 |
| FIRECRAWL | Site-to-Markdown/JSON, crawl, search and extraction | BENCHMARK_ADAPT | 2 |
| CRAWL4AI | Self-hosted open-source strategic-control challenger | BENCHMARK_ADAPT | 3 |
| BROWSERBASE_STAGEHAND | Browser-native interaction for dynamic workflows | BENCHMARK_ADAPT | 4 |
| SCRAPEGRAPHAI | Prompt/schema extraction challenger | CHALLENGER_BENCHMARK | 5 |
| BRIGHT_DATA | Specialist difficult-source and permitted anti-bot cases | SPECIALIST_BENCHMARK | 6 |

Priority is benchmark order only. No universal winner is assumed; source-class-specific winners are permitted. No candidate becomes a platform dependency through this register.

### Primary documentation discovery

Public official documentation links were checked on 2026-10-10. They are discovery inputs for the future triage, not independent performance evidence, licensing clearance, a completed benchmark or permission to execute the examples. No account, paid plan, collector integration or provider API job was created.

| Candidate | Preserved primary documentation |
|---|---|
| APIFY | [Actor schedules](https://docs.apify.com/actors/running/schedules), [dataset storage](https://docs.apify.com/storage/dataset) |
| FIRECRAWL | [Introduction and acquisition/output interfaces](https://docs.firecrawl.dev/introduction) |
| CRAWL4AI | [Official documentation](https://docs.crawl4ai.com/) |
| BROWSERBASE_STAGEHAND | [Browserbase introduction](https://docs.browserbase.com/welcome/introduction), [Stagehand workflow example](https://docs.browserbase.com/integrations/vercel/quickstart) |
| BRIGHT_DATA | [Scraper Studio FAQ](https://docs.brightdata.com/products/scraper-studio/faqs) |
| SCRAPEGRAPHAI | [Official introduction](https://docs.scrapegraphai.com/introduction) |

Provider documentation informs the benchmark questions; advertised capabilities do not establish source fidelity, correctness, legal rights, cost advantage or FLOOOW fit. Those remain empirical and governed questions.

## FLOOOW-owned acquisition contract

Preserve a future `ExternalEvidenceCollector` boundary with `discover()`, `fetch()`, `crawl()`, `interact()`, `monitor()` and `extract()`. Possible future adapters include ApifyAdapter, FirecrawlAdapter, Crawl4AIAdapter, BrowserbaseAdapter and ScrapeGraphAdapter. No adapter is implemented here. Vendor-specific semantics cannot become FLOOOW core primitives; captured evidence must remain portable across collectors.

## Evidence data contract

Every future evidence item must carry source_url/source_identity, retrieved_at, collector, collector_version, collection_method, raw_content_hash, extraction_schema, schema_version, extracted_candidate_values, observed_vs_inferred, source_type, provenance, retry/failure information, evidence_id and material rights/terms/access notes.

Raw evidence remains challengeable through a content snapshot, content-addressed artifact or independently verifiable source/hash reference. Record inaccessible sources and failed extraction explicitly. An LLM-returned value stays a candidate until governed validation and contradiction handling support promotion; absence is not zero. Retain raw lineage when normalization changes a value. Schema changes require explicit versioning and reevaluation.

## Representative corpus and metrics

The future corpus covers marketplaces, retailers, manufacturers, distributors, supplier/product pages, JavaScript-heavy pages, product variants, compatibility pages, pagination, price changes, stock changes, PDF/specification sources, interaction-heavy flows and permitted difficult-source/anti-bot cases. Use adjudicated expected values and protected evaluation cases; keep source-class results separate and preserve failures and censored observations.

Tenant neutrality is mandatory. REDMOTO may be an initial real-world validation cohort only: `REDMOTO_IS_CORE_DEPENDENCY=NO`; `REFERENCE_COHORT != PLATFORM`. Generalization follows the existing tenant-neutrality gate and independent cohort evidence.

Measure extraction_accuracy, schema_adherence, source_fidelity, unsupported_or_hallucinated_field_rate, coverage, latency, cost_per_successful_evidence_item, dynamic_JS_handling, change_robustness, determinism, reproducibility, provenance_quality, retry_failure_behavior, anti_bot_success_where_permitted, security_posture, licensing_terms, self_hosting_constraints and operational_complexity. Publish denominators, missing observations, corpus/schema/tool versions, acquisition context and reproducible artifacts for each metric. Charge retries and failed attempts to cost per successful valid evidence item; do not compare nominal request prices as equivalent outcomes.

## Cost and promotion gates

Start with free tiers, free credits and open-source/self-hosted versions. Paid capability may only be proposed after evidence shows material value in coverage, reliability, cost per valid evidence or otherwise inaccessible permitted source classes. No paid subscription is authorized. Cost optimization cannot weaken provenance, security, legal compliance or evidence quality.

```text
DISCOVER
  -> SOURCE / LICENSE / SECURITY TRIAGE
  -> DATA CONTRACT
  -> SANDBOX
  -> BENCHMARK
  -> ADVERSARIAL
  -> ADOPT / ADAPT / REJECT
  -> SHADOW
  -> PILOT
  -> PROMOTION GATE
  -> GOVERNED EXTERNAL EVIDENCE
```

0001B advances only with a representative external-source corpus, provider-neutral acquisition contract, provenance/hash requirements, benchmark metrics, security/license/terms review and reproducible ADOPT / ADAPT / REJECT evidence. A scraper, crawler, browser agent or extraction model is an acquisition mechanism; it grants no architectural authority.

## Adversarial review and exclusions

| Risk | Required correction / evidence |
|---|---|
| Vendor lock-in or paid-provider dependency | Portable raw artifacts and FLOOOW-owned contract; free-first evaluation; no mandatory provider |
| Source hallucination or LLM extraction becoming truth | Adjudicated corpus, observed/inferred distinction, unsupported-field measurement and governed promotion |
| Provenance loss or silent schema drift | Source/hash/context retention, explicit schema versions, reproducible replay and drift cases |
| Tenant-specific coupling | Generic primitives; independent cohort and out-of-domain review before generalization |
| Collector becoming authority | No direct truth, decision, capital or execution path; promotion stays inside FLOOOW |
| Legal/access-control bypass | Source/license/security triage; permitted access only; inaccessible cases remain explicit |
| Room critical-path contamination | Documentation-only separate research branch; no Package 0090 dependency or mutation |

This is design review, not a completed runtime benchmark or a security certification.

```text
PRODUCTION_SCRAPING_AUTHORIZED=NO
PRODUCTION_CREDENTIALS_AUTHORIZED=NO
PAID_SUBSCRIPTION_AUTHORIZED=NO
DIRECT_ECONOMIC_TRUTH_INGESTION=FORBIDDEN
DIRECT_DECISION_ROOM_AUTHORITY=FORBIDDEN
DIRECT_CAPITAL_ALLOCATION=FORBIDDEN
BYPASS_ACCESS_CONTROLS=FORBIDDEN
BYPASS_LEGAL_TERMS=FORBIDDEN
```

Registration baseline: fetched origin; branch research/post-mvp-intelligence-program; LOCAL_HEAD=REMOTE_HEAD=3b66269a64644a4dd1ee11525a317eaedd7ec860; tracked dirty=0; staged=0; untracked=0 before writes. Only this document and the master roadmap are in scope. The current instruction holds commit/push pending the priority mission; no implementation authority is granted.

Supplied register request SHA256 (exact attachment bytes): `f48d182083f79cd6fe30fb22354806a84153e8df83af68bfb79de8f50f572561`. Candidate descriptions are preserved as supplied hypotheses; no external benchmark result is asserted.

Next post-MVP gate: source/license/security triage and representative corpus/data-contract design after the roadmap prerequisites; no production acquisition is authorized by registration.
