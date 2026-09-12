# ADR-0075 - Governed product-cost economic promotion

Status: Accepted

## Context

Omie product-cost observations expose `nCMC`, but an observation is not authority
to identify a Mercado Livre item, select an economic subject, assign currency, or
allocate quantity. In particular, Omie `nCMC` carries no currency authority.

The repository already has an append-only `MarketplaceIndependentEconomicEvidence`
aggregate and PostgreSQL repository. A separate product-cost table, ledger, truth
store, or promotion journal would split economic authority and weaken replay and
audit guarantees.

## Decision

An immutable Omie product-cost observation may be promoted as independent
`PRODUCT_COST` evidence only when all of these authorities agree exactly:

- a current `CONFIRMED` TASK-0165K cross-system identity decision;
- the exact organization, Mercado Livre connection, Omie connection, ML item ID,
  seller SKU, and Omie provider-product ID;
- the exact durable marketplace subject;
- explicit durable Mercado Livre currency authority; and
- exact durable item quantity/allocation authority.

Identity eligibility remains exclusively in
`CrossSystemProductIdentityConfirmationService`. The PostgreSQL economic authority
adapter does not depend on or duplicate TASK-0165K identity resolution.

The only write seam is `MarketplaceIndependentEconomicEvidenceRepository`, using
`PostgresMarketplaceIndependentEconomicEvidenceRepository` in PostgreSQL. Promotion
appends a `PRODUCT_COST` / `DEDUCTION` component with `PARTIAL` coverage and an ERP
source reference that binds the immutable Omie source coordinate to the effective
TASK-0165K decision ID.

## Amount and replay semantics

The promoted amount is exact:

`observed unit nCMC * exact durable item quantity`

Insignificant trailing zeros are normalized before the existing six-decimal
monetary validation. No rounding occurs. Freight, tax, marketplace fees, discounts,
advertising, and financial charges are not allocated by this boundary.

The same source coordinate and identity decision produce deterministic component
and observation IDs. Exact replay returns `AlreadyPromoted` and creates no duplicate.
A genuinely newer immutable Omie source version receives a different source
reference and may append a new independent fact; the prior fact is retained
unchanged and is not corrected or overwritten.

## Fail-closed boundaries

Missing `nCMC` is `CostMissing`; observed zero is a valid observed zero. Missing
currency is `CurrencyUnavailable`; currency is never inferred from Brazil, Mercado
Livre, seller, account, history, or Omie. Missing allocation is
`AllocationUnavailable`. Contradictory durable currency or quantity is
`IntegrityFailure`.

Seller-SKU text equality is not identity authority. Exact within-Omie identity does
not transitively confirm an ML-to-Omie identity. Rejected, superseded, unresolved,
wrong-scope, and conflicting identity states cannot promote.

The following remain distinct:

`SOURCE OBSERVATION != IDENTITY AUTHORITY != SUBJECT AUTHORITY != CURRENCY AUTHORITY != ALLOCATION AUTHORITY != PROMOTED ECONOMIC EVIDENCE != CANONICAL ECONOMIC TRUTH`

And:

`PRODUCT_COST promotion != Economic Truth completeness != reconciliation completeness != decision readiness != recommendation authority != execution authority`

## Consequences

No provider write occurs. No historical source or economic evidence is rewritten.
No parallel economic store or canonical Economic Truth claim is introduced.
Autonomous recommendation or execution authority is not widened.
