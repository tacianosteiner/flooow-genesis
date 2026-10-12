# Global Commerce Signal Intelligence

Status: **future strategic research; post-MVP; no implementation or decision authority**. Captured: 2026-10-12. This extends Product Expansion Radar and Foresight & Opportunity Intelligence without changing their existing gates.

## Mission and boundary

The research target is a governed intelligence layer that connects external commerce observations to bounded opportunity hypotheses, then to independent validation and actual reconciled outcomes. External signals never become Economic Truth. An observed price is not landed cost; a creator mention is not supplier validation; estimated GMV is not actual sales; provisional margin is not realized contribution. No state or score approves capital, purchasing, import, FX or execution.

```text
global commerce signals → product identity → cross-source corroboration
  → China-to-world diffusion → Brazil mirror → product mining
  → supplier / industrial-cluster intelligence → importability
  → provisional economics → OpportunityCase → governed validation
  → sample → pilot → private label / import / marketplace launch
  → actual sales → canonical Economic Truth → reconciled learning loop
```

Each arrow is a proposed evidence relationship, not an automatic promotion. A candidate can remain `HOLD`, `BLOCKED`, `CONTRADICTED` or `REJECTED` indefinitely.

## CommerceSignalEvent — conceptual research record

Required concepts: event ID; source and source type; source identity and retrieval method; observed/published/collected timestamps with timezone; country, market and audience market; creator/host identity and role; live/post/listing ID; candidate product identity and category; candidate supplier and industrial cluster; platform; observed price and currency; engagement observations; conversion, sales and stock-out evidence with measurement basis; buyer questions; confidence drivers; provenance URL/document/license; collection limitations and contradictions. Every field carries maturity `OBSERVED`, `PARTIAL`, `UNVERIFIED`, `UNAVAILABLE` or `CONTRADICTED`, independent of the maturity of other fields. Preserve raw evidence reference and transformation lineage; avoid one opaque confidence score.

Source families for later feasibility research: Chinese sourcing creators and international Chinese creators; livestream sellers; Douyin, Taobao Live, Kuaishou, Xiaohongshu, TikTok Shop, Instagram, YouTube and WeChat Channels; factory/supplier lives, MCNs and brand studios; niche Chinese B2B sites, wholesale markets, industrial clusters and trade fairs; marketplaces; search trends; reviews/Q&A; ads/creative; customs and shipment documents. Collection rights, API terms, geography and freshness must be verified separately before ingestion.

## Product identity and corroboration

One physical product can have many brands, titles, SKUs, listings, countries and packaging variants. A future Product Identity Graph compares visual fingerprint, dimensions, materials, technical features, supplier/factory SKU, Chinese listing, TikTok/Amazon/Mercado Livre listings, brand and packaging. Identity states: `EXACT`, `CANDIDATE`, `CONFLICT`, `UNRESOLVED`. A visual similarity match remains `CANDIDATE` absent stronger identifiers and human review. Independent corroboration requires independent source origins; syndication and creator reposts count as one lineage until proven otherwise.

## Livestream and creator intelligence

Do not rank solely by followers. Observe live frequency, concurrent viewers, lift after product introduction, retention, comment velocity, purchase-intent questions, product dwell, evidenced GMV/units, stock-outs, repeat appearances, cross-creator propagation, audience geography, served countries, shipping model, language, product sequence and offer structure. Separate large audience, conversion evidence, early discovery, international propagation and repeatable selling capability. Monitor individual and cross-border sellers, MCNs, brand/factory/supplier studios, marketplace accounts, agencies, training operators, AI/digital-human hosts and hybrid operations. Self-reported sales remain unverified until supported by source records.

## Diffusion and Brazil mirror

A possible path is China cluster → domestic live platforms → creators → Southeast Asia → Europe/US → Brazil. This is an example, never a fixed law. A future Market Diffusion Graph records origin, independent confirmations, market-to-market lead/lag, category-specific precursors, false positives and whether particular creators/factories/lives historically predicted Brazilian outcomes. Backtest by observation date to prevent hindsight leakage.

Compare candidates with Mercado Livre, Amazon Brasil, Shopee Brasil, Brazil-facing TikTok/Instagram, search trends, reviews/Q&A, seller and brand concentration, price distribution, listing/review growth, advertising density, stock and availability. `NO_LOCAL_EVIDENCE`, `EARLY`, `OPEN_WINDOW`, `COMPETITIVE`, `CLOSING`, `SATURATED` are **proposed** states requiring separate definitions, sampling coverage and false-positive tests. No local evidence does not prove an open window.

## Supply, importability and improvement

Supplier research distinguishes factory, trading company, OEM and ODM; cluster, MOQ, quote, capacity, certification, tooling, lead time, customization, packaging, private-label readiness, quality and shipment history. Discovery does not validate a supplier. Importability evidence covers dimensions/weight/volumetric efficiency, fragility, battery/magnet/liquid/chemical/food-contact/electrical traits, ANATEL/INMETRO/ANVISA/MAPA applicability, IP/trademark/patent, customs classification, tax, anti-dumping, freight, MOQ, lead time and concentration. Proposed readiness: `PRELIMINARY_PASS`, `CONSTRAINED`, `BLOCKED`, `INSUFFICIENT_EVIDENCE`; regulatory and customs conclusions require qualified human verification.

Reviews, returns, Q&A, creator/live comments, support and warranty may expose product weaknesses. Preserve the chain: observed complaint → investigated failure pattern → improvement hypothesis → sample → design/spec change → pilot → actual outcome. A complaint does not prove root cause.

## OpportunityCase and decision rooms

Conceptual `OpportunityCase` fields: product identity; origin signals; independent corroboration; global diffusion; Brazil evidence; supplier and importability evidence; provisional economics; competitive and validation states; confidence drivers; contradictions; blockers; next eligible **proposal**; required authority; provenance. Potential lifecycle: `DISCOVERED`, `CORROBORATED`, `BRAZIL_GAP`, `SUPPLY_VALIDATED`, `ECONOMICS_SUPPORTED`, `VALIDATION_READY`, `SAMPLE`, `PILOT`, `PRIVATE_LABEL`, `IMPORT_APPROVED`, `LAUNCHED`, `ECONOMICALLY_RECONCILED`, plus `HOLD`, `BLOCKED`, `REJECTED`, `KILLED`. These are research labels, not implemented state transitions or grants.

A future Opportunity Intelligence room could expose Radar, Global Signals, Product Mining, Diffusion, Brazil Mirror, Supply, Economics, Validation and Evidence. CEO sees materiality **only when evidenced**, stage/blocker/capital posture and next governed decision; CRO sees demand, Brazil gap and channel fit; CFO sees economics maturity and later FX exposure only after an obligation exists; Sourcing sees cluster, MOQ, sample and validation. Every executive sentence needs drilldown to source, date, identity linkage, contradiction and policy context. Raw external observations stay outside canonical Economic Truth.

Future agents may observe, structure, deduplicate, challenge and propose bounded experiments. Human review remains required for sourcing/product validation, regulatory judgment and material purchasing/import/capital allocation. Autonomy requires measured calibration, reversibility and outcome history under separate governance.

## Research experiments before build

1. Sample independently sourced signals across China domestic, international and Brazil markets; measure coverage, latency, licensing and duplicate lineage.
2. Blind-label same-product pairs across listings; measure false merges and unresolved identities before any diffusion inference.
3. Backtest category-specific precursor claims with time-split data and documented false positives.
4. Compare shipment corroboration against social signals without treating a shipment description as exact product identity.
5. Validate supplier, importability and landed-cost assumptions with qualified human evidence; compare provisional economics with later reconciled profit.

Build/defer/reject decisions require these experiments and the existing economic-truth-first governance gate. The [competitor watch](GLOBAL-COMMERCE-SIGNAL-COMPETITOR-WATCH.md) and [ImportYeti assessment](GLOBAL-COMMERCE-SIGNAL-IMPORTYETI-ASSESSMENT.md) are research inputs only.
