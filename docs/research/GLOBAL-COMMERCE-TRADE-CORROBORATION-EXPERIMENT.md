# Trade-document corroboration — blind experiment

Status: **research protocol; no ImportYeti integration or credential use**. 2026-10-12. Question: can documentary shipments corroborate a social product/supplier hypothesis without manufacturing a product identity or factory relationship?

## Blind sample

Freeze social observations and candidate product identity **before** querying trade documents. Construct a labeled set of independently verified supplier/product/importer relationships and decoys: same-name entities, aliases, trading companies, freight forwarders, generic cargo descriptions, similar HS codes, OEM packaging changes, different physical variants and shipments whose dates precede or lag social attention. Reserve time- and entity-separated holdouts. Adjudicators should see original shipment and independent supplier records, not a model score or social engagement ranking. Document source rights, publication lag and coverage gaps.

Use the [documented ImportYeti PowerQuery datasets](https://docs.importyeti.com/docs/powerquery) only if access and licensing are later approved. The public [API reference](https://docs.importyeti.com/docs/reference) describes US import/export BOLs and Mexico import/export declarations; its [product-to-supplier](https://docs.importyeti.com/docs/reference/v1.0-product-product-suppliers) ranking is a discovery aid, not physical-product proof. No paid API call was made for this design.

## Evaluation

Separate the claims `TRADE_ACTIVITY_OBSERVED`, `PRODUCT_MATCH_CANDIDATE`, `SUPPLIER_RELATIONSHIP_CORROBORATED`, `MANUFACTURER_CONFIRMED` and `SUPPLIER_VALIDATED`. The first requires a document; each later state requires progressively independent identity and operational validation. A shipment by a trading company cannot be silently promoted to factory evidence. Aggregate shipment growth can be tested as a lagged correlate, not causal proof of demand or sell-through.

Report supplier-match and product-match precision/recall, false-positive rate, abstention, alias resolution, unknown-coverage rate, chronology/lead-lag by category, new-importer relation validity, and whether independent shipments change a blinded analyst's conclusion. Stratify by generic versus distinctive descriptions and by intermediary presence. Negative controls include shuffled dates, decoy suppliers and mismatched countries. Publish failures and source discrepancies, not a single opaque corroboration score.

Brazil demand and landed economics require independent Brazil-side evidence; US/Mexico shipment activity alone cannot establish them. Legal/data-use review, provider coverage and retention rights are prerequisites to any collection or joining. The experiment outputs a research evidence record, never Economic Truth or authority to buy/import.
