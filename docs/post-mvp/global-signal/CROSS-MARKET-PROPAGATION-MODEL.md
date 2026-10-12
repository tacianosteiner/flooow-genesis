# FLOOOW — Cross-Market Propagation Model

Status: RESEARCH_AUTHORIZED. Version: GS-RESEARCH-1. Implementation authority: NONE.

## Competing research routes

China → US → Brazil is one hypothesis, not an assumed universal path. Preserve China → Europe → Brazil, China → LATAM, US → Brazil, Europe → Brazil and Korea/Japan → US → Brazil as competing hypotheses. Include direct Brazil emergence, simultaneous launch, reverse flow and no propagation as negative/alternative explanations. No route is measured here.

No fixed lag constants, country ranking, causal claim or opportunity score is adopted. Route weights remain UNKNOWN until empirical observations support them. Manufacturer location, seller registration, shipment origin, platform market and attention origin are separate identities.

## Observation design

| Required field | Meaning |
|---|---|
| SIGNAL_ORIGIN | Source/market of observed signal; product manufacturing origin separately evidenced |
| SIGNAL_TIMESTAMP | Event interval plus publication/observation/availability times and timezone |
| PRODUCT_IDENTITY | Evidence-backed product/variant/pack mapping; unresolved permitted |
| CATEGORY_IDENTITY | Original taxonomy and versioned adjudicated FLOOOW mapping |
| MARKET | Sales/viewer/shipment/target market distinguished |
| SOURCE | Catalog ID, evidence URL, method/revision, permissions and covered universe |
| SIGNAL_TYPE | FLOOOW family plus concrete measure; attention/search/purchase distinct |
| SIGNAL_MAGNITUDE | Original unit, currency and denominator; normalized index not absolute volume |
| SIGNAL_VELOCITY | Change over comparable windows; UNKNOWN with insufficient observations |
| CONFIDENCE | Evidence quality/uncertainty description; no adopted numeric score |
| OBSERVED_OR_ESTIMATED | Original measure vs projection vs inferred route |
| FIRST_PARTY_OR_THIRD_PARTY | Record lineage, transformation and sampling context |
| CONTRADICTIONS | Links to conflicting records with scope and unresolved reasons |

Future matching prioritizes manufacturer part/GTIN evidence where legitimately available, then adjudicated brand/model/variant/pack/material/specification. Shared images, translated keywords or fuzzy titles are candidates, not identity proof. Preserve bundles, counterfeit possibilities, private-label ambiguity and near substitutes. Abstain from SKU joins when evidence is insufficient; category-level analysis must be labeled explicitly.

Keep original currency, price basis, tax/shipping, pack size, quantity and measurement unit; any conversion requires dated rate/source and derivation. Display price is not landed cost. NCM/HS categories and retail taxonomies require versioned many-to-many mapping; classification changes must not look like product emergence. Comex corroborates aggregate trade, not shopper conversion [E47–E48](SOURCE-EVIDENCE-REGISTER.md).

## Empirical route test proposal

Define an endpoint (e.g. first rights-cleared target-market listing, verified purchase, import-category change or saturation criterion) before inspecting outcomes. Define emergence rules and denominator under a future experiment contract, not this document. Build launch cohorts including failed/non-propagating products and censored records. Use availability-time as-of snapshots, matched control categories and season/calendar controls. Evaluate out of time and across independent markets/cohorts; report signed lag distributions and missingness rather than a single constant.

Compare route-specific signal bundles to local-market/public baselines. Apparent lead caused solely by faster publication, differing platform adoption or translation/matching error must fail the hypothesis. Advertising campaigns, common global launch plans and shared supplier listing syndication can generate correlated sequences without causal propagation.

## Contradiction input

| Distinct records | Required treatment |
|---|---|
| TikTok rising; marketplace search flat | Preserve attention/intent conflict; no demand confirmation |
| 1688 supplier density rising; retail listings falling | Possible oversupply or identity/coverage gap; do not average |
| Amazon demand estimate rising; landed economics negative | Candidate economics veto/pending evidence, never demand→profit inference |
| China growth rising; Brazil import rule blocks entry | Hypothetical applicability conflict; authoritative regulatory review required for an actual product |
| Search rising; conversion falling | Investigate availability/price/audience mismatch and denominator |
| Attention rising; repeat purchase weak | Separate trial from sustained demand; retention cohort required |

Examples are research scenarios, not claims that these conditions currently hold. Maintain original records, applicability, conflict type and adjudication status. A source with missing coverage cannot negate a positive observation from another universe.

## OpportunityCandidate — conceptual schema, no implementation

```text
OpportunityCandidate {
  product_or_category_identity
  originating_market
  target_market
  signal_bundle
  earliest_observed_at
  propagation_sequence
  demand_evidence
  attention_evidence
  supply_evidence
  trade_evidence
  competitive_evidence
  price_evidence
  landed_economics_status
  regulatory_status
  contradictions
  confidence
  provenance
  evidence_freshness
}
```

Each evidence field is a set of traceable record references with scope/method/time, not a silently combined number. Missing economics/regulation is UNKNOWN, never favorable. Candidate ≠ EconomicTruth; candidate ≠ recommendation; candidate ≠ execution authority. Implementation/policy/capital/production authority is absent.
