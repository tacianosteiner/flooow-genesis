# SPEC-0081: Mercado Livre Closed-Order Revenue Financial Basis Authority

Status: Proposed

Date: 2026-09-17

Source decision: ADR-0081

## Objective

Define the first explicit provider-specific authority capable of binding one
durable canonical Mercado Livre REVENUE observation to
FinancialLedgerBasis.ACTUAL.

No other basis mapping is authorized.

## Authority semantic version

Exactly:

mercado-livre.closed-order-revenue/1

The existing materialization policy remains:

marketplace-financial-ledger-materialization/1

## Canonical observation shape

The candidate observation must be durable canonical economic evidence and must
match exactly:

marketplace = mercado-livre
family = MARKETPLACE_ORDER
component.type = REVENUE
component.direction = ADDITION
component.quality = CONFIRMED
coverageClaim = PARTIAL
component.source.kind = MARKETPLACE
component.source.systemKey = br.com.mercadolivre
component.source.externalReference = subject.externalOrderId

Shape compatibility alone never authorizes basis.

## Provider proof query

Resolve durable V023 promotion rows for the exact organization and
MarketplaceOrderId.

Join every candidate row to its exact V021 source key and V022 identity.

A successful proof row requires:

outcome IN (PROMOTED, DUPLICATE)
source capability = marketplace-economic.order-source
source dateClosed IS NOT NULL
source externalOrderId = canonical subject externalOrderId
identity marketplace = mercado-livre
identity MarketplaceOrderId = canonical subject orderId
source currency = identity currency = canonical subject currency
source totalAmount = canonical component magnitude
source dateClosed = canonical component occurredAt
source observedAt = canonical observation observedAt

## Positive decision

After exact provider proof, return existing:

FinancialLedgerComponentMaterializationAuthorityDecision.Authorized

with exactly:

sourceAuthorityIdentity = observation.id
sourceAuthoritySemanticVersion = mercado-livre.closed-order-revenue/1
materializationPolicyVersion = marketplace-financial-ledger-materialization/1
expectedSourceFingerprint = B3-A fingerprint of exact observation
basis = ACTUAL

The authority never supplies or overrides stage.

B3-A continues deriving REVENUE -> SALE exclusively through controlled stage
compatibility.

## Negative decisions

No matching successful durable provider proof:

NotAuthorized(BASIS_AUTHORITY_UNAVAILABLE)

Provider/promotion proof exists but contradicts canonical source semantics:

IntegrityFailure

Database or authority-source operational failure:

Unavailable

No exception, SQL detail, tenant identifier, source reference, amount, or provider
credential may escape in a controlled result.

## Multiple provider rows

Multiple PROMOTED or DUPLICATE rows are allowed only when they prove the same
accepted financial semantic tuple.

Competing successful rows for the same canonical order that prove incompatible
revenue amount, currency, external order, or close time are IntegrityFailure.

## Security and tenant isolation

The operational organization scope and durable canonical observation organization
must match exactly.

Provider payload fields cannot select organization ownership.

Cross-organization proof is never searched as fallback.

## No semantic shortcuts

The implementation must never authorize ACTUAL solely because evidence is:

CONFIRMED
MARKETPLACE
MARKETPLACE_ORDER
PARTIAL
from br.com.mercadolivre
closed
recent
or monetarily equal to another fact.

The durable accepted source contract plus exact provider proof is the authority.

## Required adversarial tests

Future B3-C implementation must prove:

1. exact closed-order revenue proof -> ACTUAL
2. authority semantic version is exact
3. expected source fingerprint is exact B3-A fingerprint
4. missing V023 proof -> BASIS_AUTHORITY_UNAVAILABLE
5. IDENTITY_CONFLICT does not authorize
6. EVIDENCE_CONFLICT does not authorize
7. same provider/source shape without durable proof does not authorize
8. CONFIRMED alone does not authorize
9. source kind MARKETPLACE alone does not authorize
10. totalAmount mismatch fails closed
11. dateClosed mismatch fails closed
12. observedAt mismatch fails closed
13. currency mismatch fails closed
14. externalOrderId mismatch fails closed
15. MarketplaceOrderId mismatch fails closed
16. cross-organization proof is rejected
17. SQL failure -> Unavailable
18. successful authority cannot select a stage
19. no EXPECTED decision exists in Version 1
20. no SETTLEMENT, PAYMENT_ACCOUNT, or BANK result is possible
21. no trace or ledger mutation occurs in the authority resolver
22. existing B3-A/B3-B regression remains green

## Implementation boundary after design acceptance

The first implementation may add only:

- a provider-specific basis-authority application port/policy
- a PostgreSQL authority-source adapter over existing durable tables
- focused pure and PostgreSQL adversarial tests

No migration is authorized by this specification.

No live pipeline wiring is authorized by this specification.

## Completion

B3-C is complete only after source-contract proof, fail-closed authority resolution,
exact ACTUAL semantics, regressions, and assistant audit all pass.
