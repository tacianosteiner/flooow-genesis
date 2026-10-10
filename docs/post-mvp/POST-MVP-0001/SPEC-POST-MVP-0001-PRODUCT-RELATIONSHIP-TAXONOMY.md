# FLOOOW — Product Relationship Taxonomy

Status: ENGINEERING DESIGN — POST-MVP / SEPARATE FROM ROOM CRITICAL PATH
Captured: 2026-10-10
IMPLEMENTATION_AUTHORIZED=NO
PRODUCTION_INTEGRATION_AUTHORIZED=NO
ROOM_CRITICAL_PATH_IMPACT=NONE

This is a proposed documentation contract, not runtime, data-access, model-execution or release authority. Room operational readiness has not been established by this mission.

## Label semantics

Each ordered pair has a primary task label and declared context; secondary relationships may be recorded as adjudicated notes, not silently collapsed. ACCESSORY_FOR and SUBSTITUTE_FOR are directional/contextual; COMPATIBLE_WITH must specify target, generation and operating conditions. Benchmark direction is preserved. Genuine conflicts go to review; insufficient evidence never becomes UNRELATED.

| Label | Required semantics and dangerous error |
|---|---|
| SAME_PRODUCT | Same commercial/technical product, with corroborated identifiers and material specifications; different listing/title/photo alone may vary. Never collapse voltage, capacity, generation, pack or vintage variants. Reused GTIN or seller identifier requires investigation. |
| VARIANT_OF | Same evidenced base family with a material variant; record differing attributes. Family resemblance alone is insufficient. A voltage variant is not necessarily compatible. |
| SUBSTITUTE_FOR | Distinct products satisfy the same contextual need within stated constraints. Does not assert identity or universal interchangeability. |
| ACCESSORY_FOR | Evidenced designed complementary use; not necessarily compatible with every generation. Record target and constraints. |
| COMPATIBLE_WITH | Technical fit supported by manufacturer/technical records or documented controlled testing. Similar photos, titles or dimensions alone cannot prove safe compatibility. |
| INCOMPATIBLE_LOOKALIKE | Similar appearance/text plus affirmative evidence of incompatible specification or fit. Missing compatibility evidence alone is insufficient to assert incompatibility. |
| PRIVATE_LABEL_EQUIVALENT_CANDIDATE | Corroborated specifications, construction/dimensions and supplier/document evidence suggest possible equivalence; remains a candidate. Visual similarity or embedding score alone cannot prove common OEM, tooling, manufacturer or interchangeable safety certification. |
| UNRELATED | Sufficient evidence establishes no relevant relationship within the declared task scope. Absence of evidence cannot establish this label. |
| INSUFFICIENT_EVIDENCE | Evidence cannot safely establish another relation; abstention is first-class, with missing evidence/reason preserved. |

SAME_PRODUCT, COMPATIBLE_WITH and PRIVATE_LABEL_EQUIVALENT_CANDIDATE receive separate false-match budgets and independent review. Evidence contradictions block confident labeling until adjudicated. Reviewers see sources and technical constraints, not challenger confidence during initial adjudication. Disagreement must be preserved and escalated to an independent adjudicator; unresolved examples are marked insufficient or excluded with an explicit reason, never coerced into a positive label.

Examples are illustrative, not asserted product matches: visually identical motorcycle parts with different fit -> INCOMPATIBLE_LOOKALIKE when incompatibility is proven; same family different voltage -> VARIANT_OF only with family evidence; duplicate photo without manufacturer records -> INSUFFICIENT_EVIDENCE for OEM equivalence.
