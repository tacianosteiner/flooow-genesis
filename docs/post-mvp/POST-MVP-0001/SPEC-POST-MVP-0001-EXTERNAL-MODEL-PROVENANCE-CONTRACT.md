# FLOOOW — External Model Provenance Contract

Status: ENGINEERING DESIGN — POST-MVP / SEPARATE FROM ROOM CRITICAL PATH
Captured: 2026-10-10
IMPLEMENTATION_AUTHORIZED=NO
PRODUCTION_INTEGRATION_AUTHORIZED=NO
ROOM_CRITICAL_PATH_IMPACT=NONE

This is a proposed documentation contract, not runtime, data-access, model-execution or release authority. Room operational readiness has not been established by this mission.

## Provenance record

Use [retail source discipline](../../research/retail-commerce/RETAIL-COMMERCE-SOURCE-CATALOG.md). Each candidate preserves SOURCE, SOURCE_TYPE, CLAIM, OBSERVED_EVIDENCE, SELF_REPORTED_EVIDENCE, INDEPENDENTLY_REPRODUCED_EVIDENCE, LICENSE, SECURITY, DATA_BOUNDARY, FLOOOW_RELEVANCE and ADOPT / ADAPT / REJECT. Add exact model/revision, official artifact URLs, retrieved-at time, immutable digests, dependency/tokenizer/preprocessor revisions, weight format, required runtime/hardware and responsible reviewer.

GitHub official repository, Hugging Face model card, academic paper, first-party documentation, vendor commercial case and internal FLOOOW benchmark are distinct evidence types. A model-hub upload is not automatically an official producer artifact. Vendor scores remain self-reported until reproduced; unavailable evidence is UNKNOWN, not PASS. Existing research artifacts are preserved historical claims, not refreshed vendor verification.

## Safety and rights before future execution

Verify exact revision license, weight/code licenses, intended use, commercial restrictions, dataset provenance where disclosed and redistribution rights. Review dependency integrity, unsafe serialization, arbitrary remote code, network/telemetry behavior and supply-chain changes. Default future evaluation is isolated, no privileged access or production credentials, with controlled rights-cleared inputs; remote execution requires separately authorized data egress and provider handling terms. REMOTE_CODE_REQUIREMENT is explicit; unknown requirements block execution. No model installation, network service integration or license clearance happens now.

Candidate register: BM25 lexical baseline; BGE-M3 / Qwen3 Embedding text; Marqo Ecommerce Embeddings / Qwen3-VL Embedding multimodal; Qwen3 Reranker / Qwen3-VL Reranker reranking. Every exact revision, availability, license, security and operational qualification remains PENDING. Selection never follows family name or provider marketing alone.

Security/license failures override benchmark gains. ADOPT selects a qualified bounded role, ADAPT requires identified mitigations and reevaluation, REJECT records veto and reason. Any model/revision/input-boundary change invalidates the prior qualification until revalidated. No External Intelligence Capability Radar is present in the inspected main inventory; link it only after exact artifact provenance is established.
