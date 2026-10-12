# FLOOOW — Temporal Signal Model

Status: RESEARCH_AUTHORIZED. Version: GS-RESEARCH-1. Observed: 2026-10-11. Implementation authority: NONE.

## FLOOOW-owned initial taxonomy

Freeze names for this research version; changing definitions requires a new version and reevaluation. Providers map to these families and cannot redefine them.

| Family | Research meaning / guardrail |
|---|---|
| DEMAND_INTELLIGENCE | Evidence about demand hypotheses; interest is not confirmed demand |
| SHOPPER_INTELLIGENCE | Consideration, journeys and purchasing context within covered populations |
| PRODUCT_INTELLIGENCE | Product/category identity, attributes and emergence; identity can remain unresolved |
| DIGITAL_SHELF_INTELLIGENCE | Listing placement, content and assortment observations |
| ATTENTION_INTELLIGENCE | Exposure/engagement; not purchasing evidence |
| ADVERTISING_INTELLIGENCE | Ad presence/activity and scoped delivery measures |
| COMPETITIVE_INTELLIGENCE | Comparable rival observations, retaining denominator |
| SUPPLY_INTELLIGENCE | Supplier/manufacturer/listing formation; seller ≠ manufacturer |
| TRADE_INTELLIGENCE | Official/permitted goods flows; imports ≠ consumer sell-through |
| AVAILABILITY_INTELLIGENCE | Listed, promised and fulfilled availability distinguished |
| PURCHASE_VERIFICATION | Corroborated purchase events with identity, permissions and returns |
| CHANNEL_MEASUREMENT | Channel-specific measurement with universe and attribution assumptions |
| PRICE_INTELLIGENCE | Currency/unit/pack/date/offer-specific price observations |
| CREATOR_INTELLIGENCE | Creator/content/product mentions and change, retaining audience sampling |
| EMERGING_COMMERCE_INTELLIGENCE | Cross-market emergence hypotheses combining governed evidence |

## Temporal classes are conditional labels

| Class | Candidate examples | Evidence needed / counterexample |
|---|---|---|
| EARLY | Supplier listings, patents/trademarks, creators, ads, attention, search acceleration | Demonstrate lead relative to a defined endpoint; patent may never commercialize; ads may follow sales |
| INTERMEDIATE | Marketplace search/views, shelf/rank, reviews, seller entry and price competition | Comparable repeated observations; reviews may lag sales; listings may precede or follow established demand |
| CONFIRMATORY | Orders, verified purchase, sell-through, imports and repeat purchase | Confirm only the scoped event: an import confirms a trade flow, not retail demand; returns/cancellations retained |
| OUTCOME | Reconciled revenue, gross margin, leakage, returns, retention and contribution | Governed reconciliation/period boundaries; external estimates cannot become owned actuals |

Class assignment depends on endpoint, market, identity and observation process. An order can be confirmatory for a purchase and intermediate for repeat/contribution. Imports may be EARLY relative to retail and CONFIRMATORY only for shipment. Search can be post-outcome curiosity. No universal temporal order or lag is frozen.

## Time and revision contract — research design only

Retain event_at/event_interval, source_published_at, source_updated_at, observed_at, available_to_researcher_at, extraction_at, original timezone, UTC conversion, granularity, window endpoints, source revision/method version and collection/query context. UNKNOWN event time remains UNKNOWN; never substitute retrieval time as product launch time.

First observed is a detection bound, not first occurred. Left-censored already-existing products, right-censored target events, interval-censored publication windows and inaccessible periods must survive in the dataset. Late reporting/revisions cannot travel backward into an as-of evaluation. Freeze the evidence available at each decision date and compare revised series separately.

Vendor weekly publication, nine-day Similarweb lag, daily shelf claims and current ad discovery are documented contexts [E02–E04, E08–E09, E14–E15, E21, E24–E28](SOURCE-EVIDENCE-REGISTER.md); none is a measured delivery SLA. Google Trends timezones and relative normalization require explicit window context. Update frequency ≠ lead time ≠ event freshness ≠ retention.

## Authority hierarchy

L0 owned governed/official/reconciled institutional records; L1 first-party platform; L2 market observations; L3 third-party estimates; L4 community weak signals; L5 Flooow inference. Level != truth. Assign per measurement method and record; preserve source lineage for projections. L0 trade totals still cannot identify a retail SKU or tenant margin.

Research confidence is an uncalibrated assessment with evidence/unknowns, not a numeric policy. Preserve sample universe, missing coverage and contradictory records. Promotion requires future rights-cleared adjudication, method validation and the relevant governed contract; temporal classification grants no execution authority.
