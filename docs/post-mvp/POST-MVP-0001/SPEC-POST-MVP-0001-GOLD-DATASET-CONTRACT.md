# FLOOOW — Gold Dataset Contract

Status: ENGINEERING DESIGN — POST-MVP / SEPARATE FROM ROOM CRITICAL PATH
Captured: 2026-10-10
IMPLEMENTATION_AUTHORIZED=NO
PRODUCTION_INTEGRATION_AUTHORIZED=NO
ROOM_CRITICAL_PATH_IMPACT=NONE

This is a proposed documentation contract, not runtime, data-access, model-execution or release authority. Room operational readiness has not been established by this mission.

## Dataset and acceptance

Working name: FLOOOW Product Intelligence Benchmark v1. Minimum 2,000 high-quality adjudicated pairs; target 5,000–10,000. These are future targets, not existing records. Label quality precedes volume. Potential families: internal SKUs, Redmoto, supplier catalogs, China supplier images, technical sheets, marketplace and competitor listings, known compatibility records/mappings and hard negatives. No ingestion occurs now.

Every record contains example_id; product_a_identity; product_b_identity; relationship_label; titles/descriptions and text evidence; structured attributes with units; image references; source references; adjudication status; adjudicator; adjudication timestamp; evidence references; difficulty; hard_negative; notes. Each source preserves SOURCE, SOURCE_TYPE, SOURCE_ID, ACQUISITION_TIME, DATA_RIGHTS_CLASS, TRANSFORMATION_HISTORY and LABEL_PROVENANCE. Missing images/attributes use explicit unavailable reasons, not empty evidence implying absence. Identities include namespace/source and exact material variant, never an unqualified title.

Record rights for acquisition, storage, evaluation and redistribution separately. Unknown or prohibited rights quarantine the record. Preserve original reference/content digest, access restrictions and transformations; avoid personal shopper data and secrets. Two independent initial labels and a separate tie-break adjudicator protect risky relations. Record agreement and reasons; model suggestions are never gold authority. Include contested/abstention examples; coverage counts by relation, source and difficulty expose sparse strata. Schema checks, references, deduplication and rights must pass before DATA_READY.

## Protected splits

Separate TRAIN / DEVELOPMENT, VALIDATION, GOLD TEST and ADVERSARIAL TEST. Gold is never used for tuning, prompts, thresholds, candidate selection or error-driven iterative development. Freeze split manifests and hashes before comparison; an independent evaluator controls final gold release. Findings requiring tuning move to a new benchmark version, not repeated optimization against the same gold.

Construct connected grouping components across supplier family, base SKU, product family, duplicate marketplace listings, reused image hashes, catalog family and likely OEM group. All connected examples stay in one split; the same product cannot leak through differently ordered pairs. A likely OEM group is a conservative split hint, not an identity claim. Publish group provenance, deterministic split seed, distribution and overlap report. Unresolved grouping quarantines examples; no arbitrary train/test percentages are approved here. Adversarial test remains separately frozen and cannot be used as development examples.

Version manifest records dataset digest, schema/taxonomy revision, split digests, source/rights inventory, labels, adjudication lineage, exclusions, counts and change history. Corrections are append-only versioned releases; revoked source rights propagate to future access and reevaluation. See [Redmoto phases](REDMOTO-PRODUCT-DATASET-PLAN.md).
