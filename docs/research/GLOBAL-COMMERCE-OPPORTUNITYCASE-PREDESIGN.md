# OpportunityCase — pre-design contract

Status: **conceptual post-MVP research; no implementation or execution authority**. Captured: 2026-10-12. This refines the [global commerce research](GLOBAL-COMMERCE-SIGNAL-INTELLIGENCE.md); it does not alter canonical Economic Truth, Room, Product Expansion Radar, policy or capital gates.

## Unit of judgment

An `OpportunityCase` is a versioned investigation around a **candidate physical-product hypothesis** in a specified market, category and time window. It is not a product master, a procurement request or an OpportunityScore. Every claim is a typed statement with source references, observation time, acquisition time, evidence class, identity relation, method, scope, maturity and contradictions. A case revision preserves what was knowable at that time; later evidence appends a revision rather than rewriting earlier predictions.

| Claim family | Required distinction and blocker |
|---|---|
| `CommerceSignalEvent` | Creator/live/listing/ad/search engagement, with source and metric basis; attention cannot become purchase. |
| Product identity | `EXACT`, `CANDIDATE`, `CONFLICT`, `UNRESOLVED` per pair and variant; candidate joins cannot aggregate sales or diffusion as one physical product. |
| Diffusion | Source-origin-independent observations, market and observation chronology, lag method and negative controls; reposts/syndication share an origin. |
| Brazil mirror | Queried population, sampling frame, demand/listing/price/review/ad/stock observations and explicit unavailable history; missing listing cannot mean an open window. |
| Supplier / trade | Separate factory, trading company, exporter, importer, brand and creator identities; a bill of lading can corroborate a route/relationship but rarely a retail SKU. |
| Importability | Classification, certification, IP, freight, tax and category review by qualified people; a public registry match is not clearance. |
| Provisional economics | Versioned assumptions, quoted prices, MOQ, FX scenario, freight, tax and marketplace fee ranges with uncertainty; never booked cost, realized revenue or reconciled contribution. |
| Outcome | After an authorized pilot, attach actual marketplace/economic records through governed identity and permissions; retain prediction timestamp, forecast version and realized comparison. |

Maturity is **per claim**, not a single case confidence: `UNAVAILABLE`, `UNVERIFIED`, `OBSERVED`, `CORROBORATED`, `CONTRADICTED`, `INVALIDATED`. `CORROBORATED` requires independent origin plus a method-specific agreement test; it does not override a regulator, supplier or finance gate. Contradictions are first-class records with competing sources and disposition. Preserve unknowns and explicit missing-evidence requests, including where a provider lacks access or licenses. A case-level view may show a state and blocker list, but must never hide the weakest mandatory claim behind an average score.

## Revision and decision model

Each revision has case ID, hypothesis/market/variant scope, prior revision, claims considered, identity graph revision, source lineage, evidence cutoff, contradiction set, required evidence, proposed next investigation, required human authority, decision and reason. A decision can be `CONTINUE_INVESTIGATION`, `HOLD`, `BLOCKED`, `REJECTED` or `KILLED`. `HOLD` preserves uncertainty or wait conditions; `BLOCKED` identifies a missing mandatory gate; `REJECTED` records evidence against the hypothesis; `KILLED` records an authorized terminal business decision and its reasons. None erases history or grants procurement. Reopening requires new evidence and a governed revision, not score drift.

Candidate progression labels such as `DISCOVERED`, `CORROBORATED`, `BRAZIL_GAP`, `SUPPLY_VALIDATED`, `ECONOMICS_SUPPORTED`, `VALIDATION_READY`, `SAMPLE`, `PILOT`, `LAUNCHED` and `ECONOMICALLY_RECONCILED` remain research vocabulary; transitions and authorities are **not specified for implementation**. A next eligible investigation is a proposal constrained by permissions, evidence and budget; purchasing samples, supplier commitment, import, launch and capital use need separate named human/policy authority. A case cannot become `VALIDATION_READY` if product identity, acquisition rights, regulatory screen or downside evidence is unresolved under the later approved policy.

## Prediction-to-outcome discipline

Before any pilot, freeze the predicted product/market, observation cutoff, expected demand range, provisional contribution range, risk hypotheses, and success/failure criteria. After a separately authorized action, attach actual outcomes and reconcile to canonical Economic Truth via governed references. Compare calibration, false positives, decision regret and external-signal lead time without leaking future observations into backtests. “No outcome yet” is not success. No existing projection or ledger is reclassified by this pre-design.

Implementation prerequisites are licensed sources, blind identity and trade experiments, a versioned evidence model, role/tenant/redaction policy, policy authority for lifecycle gates, and negative/replay tests. Current status: **DESIGN RESEARCH ONLY; BUILD GATE CLOSED**.
