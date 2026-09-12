# SPEC-0075 - Governed product-cost economic promotion

## Inputs and ownership

`GovernedProductCostPromotionRequest` contains:

- an exact `MarketplaceEconomicEvidenceSubject`;
- an exact `CrossSystemProductIdentityRelation` scoped by organization, Mercado
  Livre connection, and Omie connection;
- immutable `OmieProductCostSourceObservationKey` coordinates;
- optional `ProductCostQuantityAllocation`; and
- optional explicit `MarketplaceCurrency` authority.

The request subject organization must equal the relation organization. The service
requires the relation's Omie connection to equal the source observation connection.

## Responsibility split

`CrossSystemProductIdentityConfirmationService` resolves current TASK-0165K identity
eligibility. `PostgresGovernedProductCostPromotionAuthority` validates only durable
economic authorities: source, subject, organization and connection scope, currency,
and quantity. It must not acquire a TASK-0165K persistence dependency or implement
fuzzy, semantic, or transitive identity matching.

`GovernedProductCostPromotionService` composes both authorities and writes only via
`MarketplaceIndependentEconomicEvidenceRepository`.

## Durable read contract

The PostgreSQL authority must match exactly:

- organization ID;
- Omie connection, capability, progress version, record ordinal, and provider-product ID;
- Mercado Livre connection, item ID, and seller SKU;
- marketplace order ID and external order ID;
- order, item, identity, subject, and explicit authority currency; and
- observed item quantity and requested allocation quantity.

No row is `SubjectUnresolved`. Null `unit_cmc` is `CostMissing`; numeric zero is
`Available`. Missing explicit currency is `CurrencyUnavailable`. Missing allocation
is `AllocationUnavailable`. Contradictory durable currencies or quantities are
`IntegrityFailure`. More than one matching row is `IntegrityFailure` after the first
row has been materialized.

Omie `nCMC` has no currency authority. Currency comes from exact durable Mercado
Livre order, item, and subject identity evidence and must match the explicit request
authority. No currency default or inference is permitted.

## Identity contract

Only a current `CrossSystemProductIdentityResolution.Confirmed` for the exact
relation permits promotion. Outcomes are:

- unresolved, candidate-only, wrong organization, wrong ML connection, wrong Omie
  connection, seller-SKU equality alone, or within-Omie identity alone:
  `GovernedProductCostPromotionResult.IdentityUnconfirmed`;
- current rejection, including a rejection superseding an earlier confirmation:
  `GovernedProductCostPromotionResult.IdentityRejected`; and
- conflicting effective identity: `GovernedProductCostPromotionResult.IdentityConflict`.

## Economic write contract

For `GovernedProductCostSourceRead.Available`, compute with `BigDecimal`:

`amount = unitCost.multiply(quantity).stripTrailingZeros()`

Canonical zero is retained as `BigDecimal.ZERO`. The value must remain non-negative,
within the existing magnitude bound, and representable at no more than six decimal
places after insignificant-zero normalization. No rounding is allowed.

Append one `MarketplaceIndependentEconomicFact.Component` with:

- family and component type `PRODUCT_COST`;
- direction `DEDUCTION`;
- coverage `PARTIAL`;
- quality `CONFIRMED`;
- the exact subject currency;
- source kind `ERP` and system key `omie`; and
- stable source reference
  `omie-product-cost/{connectionId}/{inputProgressVersion}/{recordOrdinal}/{decisionId}`.

The reference links the promoted fact to the immutable Omie row and effective
TASK-0165K decision. The decision retains organization, both connection scopes,
ML item/SKU, Omie provider product, principal, provenance, correlation ID, revision,
and decision time. The referenced source and marketplace rows retain unit `nCMC`,
quantity, and currency evidence for replay and audit.

Deterministic observation and component IDs make exact replay return
`GovernedProductCostPromotionResult.AlreadyPromoted`. A different immutable source
version may append a second fact. Existing facts are never updated or removed.

## Safety invariants

Blocked promotion produces zero `PRODUCT_COST` writes for unconfirmed/rejected
identity, missing cost, missing currency authority, or missing allocation authority.
No provider mutation, migration, parallel truth store, currency inference, fuzzy
identity, transitive identity, historical rewrite, or completeness claim is allowed.

`SOURCE OBSERVATION != IDENTITY AUTHORITY != SUBJECT AUTHORITY != CURRENCY AUTHORITY != ALLOCATION AUTHORITY != PROMOTED ECONOMIC EVIDENCE != CANONICAL ECONOMIC TRUTH`

`PRODUCT_COST promotion != Economic Truth completeness != reconciliation completeness != decision readiness != recommendation authority != execution authority`
