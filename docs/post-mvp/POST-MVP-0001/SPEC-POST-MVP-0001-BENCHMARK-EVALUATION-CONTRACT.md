# FLOOOW — Benchmark Evaluation Contract

Status: ENGINEERING DESIGN — POST-MVP / SEPARATE FROM ROOM CRITICAL PATH
Captured: 2026-10-10
IMPLEMENTATION_AUTHORIZED=NO
PRODUCTION_INTEGRATION_AUTHORIZED=NO
ROOM_CRITICAL_PATH_IMPACT=NONE

This is a proposed documentation contract, not runtime, data-access, model-execution or release authority. Room operational readiness has not been established by this mission.

## Pre-registered comparisons

Start with exact identifiers, normalized title matching, brand/model tokens, attribute overlap, specification/dimension constraints and BM25 lexical retrieval. Identifiers remain evidence needing contradiction checks. Contradictory specs veto a positive baseline proposal; missing identifiers cannot become a zero-confidence truth. Freeze normalization, tokenization, unit conversion, BM25 parameters and tie-break rules before evaluation. Baselines are designs only, not implemented PASS results.

Text challengers: BGE-M3 and Qwen3 Embedding, compared with BM25. Multimodal: Marqo Ecommerce Embeddings and Qwen3-VL Embedding. Reranking: Qwen3 Reranker and Qwen3-VL Reranker. They are challengers, not winners; exact revisions, license and availability require later verification. No models downloaded or run now.

## Quality metrics

Retrieval reports Recall@1, Recall@5, Recall@10, MRR and nDCG@K with frozen relevance definitions. Recall@K is relevant items recovered divided by adjudicated relevant items; no-positive queries are reported separately. MRR uses the first relevant rank; nDCG uses fixed relation/context-specific relevance grades. A product-pair corpus alone does not supply a complete retrieval truth set: separately adjudicate query candidate pools and report incomplete relevance coverage.

Pair classification reports macro F1, per-class precision/recall, confusion matrix and abstention quality. Abstention measures coverage, selective error rate, useful abstentions on insufficient evidence and missed safe decisions; abstention must not hide low coverage. Report sample denominators, class/source/difficulty strata and uncertainty intervals; use grouping-aware resampling for dependent families.

Primary safety metric FALSE_MATCH_RATE per risky relation = incorrect positive matches on the frozen relevant negative set / number of evaluated negative opportunities for that relation. Also report false discovery proportion = incorrect positive proposals / all positive proposals, and operational economic loss where evidence permits. Zero denominator is UNDEFINED, never zero error. Zero observed failures on a small sample is not proof of safety; report an upper confidence bound and unresolved sample adequacy.

Dedicated hard negatives: incompatible motorcycle lookalikes, same title different voltage, incompatible generation, same packaging different specs, image reuse by unrelated suppliers, private-label visual similarity without manufacturer evidence, different capacity nearly identical photos. Excellent recall cannot offset dangerous false matches.

Compare text only, image only, text + image, text + image + structured attributes; compare retrieval only versus retrieval + reranker on identical queries/pools. Keep score calibration and threshold tuning on validation only. No model score becomes canonical product identity.

## Operating and reproducibility gates

Record QUALITY, LATENCY (cold/warm p50/p95/p99 and failures), THROUGHPUT, MEMORY, GPU_REQUIREMENT, CPU_VIABILITY, COST (per 1,000 items and query), MODEL_SIZE, LICENSE, SECURITY, REMOTE_CODE_REQUIREMENT, DATA_PRIVACY, DEPLOYMENT_COMPLEXITY, OPERABILITY and FAILURE_MODES. Specify workload, batch/concurrency, hardware, index build cost, timeout policy and units. Count failures in total workload and report successful-only metrics separately.

Pre-register relation-specific maximum error, minimum coverage/precision, uncertainty/sampling requirements, latency/cost and resource budgets before challenger results. Numerical limits remain UNSET pending economic-loss evidence and hardware qualification; any UNSET limit blocks eligibility. ADOPT/ADAPT/REJECT is an evidence-backed proposal; license/security/privacy can veto highest quality. Package frozen config, manifests, raw outputs, evaluation revision, environment identity and result/report digests; no result has been produced in this mission.
