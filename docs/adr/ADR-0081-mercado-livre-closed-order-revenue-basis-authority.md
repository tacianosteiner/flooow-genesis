# ADR-0081: Mercado Livre Closed-Order Revenue Financial Basis Authority

Status: Accepted; domain authority implemented, production durable source adapter pending

Date: 2026-09-17

## Current implementation state - 2026-09-20

This section records current repository reality and has normative precedence
over historical implementation assumptions later in this ADR.

The bounded Mercado Livre closed-order REVENUE financial-basis authority has
been implemented for SALE / ACTUAL under semantic version
mercado-livre.closed-order-revenue/1.

The original design identified a limitation because V023 did not persist the
canonical economic observation UUID. V038 has since closed that limitation by
persisting economic_observation_id on marketplace_order_revenue_source_promotion
and binding successful new terminal rows to the exact canonical economic fact.

Historical successful rows remain nullable and are not backfilled.

The production PostgresMercadoLivreClosedOrderRevenueAuthoritySource,
live-pipeline authority wiring, automatic reconciliation, settlement/payment-
account/bank authority, recovery, financial action, and AI decisions remain
separately governed and are not authorized by this status update.

Historical text below saying V023 lacks observation UUID records the constraint
that existed when this ADR was written; V038 supersedes that specific limitation.

## Context

TASK-0165Q 4C-B3-A and 4C-B3-B now provide governed source fingerprinting,
explicit materialization authority decisions, durable source-to-ledger lineage,
atomic trace + entry + lineage commit, replay protection, concurrency safety,
and fail-closed correction context.

The remaining semantic gap is FinancialLedgerBasis.

The accepted Mercado Livre order-revenue promotion contract produces an exact
canonical REVENUE component only from a closed provider order.

Its accepted source semantics include:

- marketplace = mercado-livre
- family = MARKETPLACE_ORDER
- component type = REVENUE
- direction = ADDITION
- magnitude = provider totalAmount
- occurredAt = provider dateClosed
- quality = CONFIRMED
- coverage = PARTIAL
- source kind = MARKETPLACE
- source system = br.com.mercadolivre
- source external reference = externalOrderId

Those properties do not themselves establish EXPECTED or ACTUAL.

ADR-0080 explicitly forbids deriving FinancialLedgerBasis from evidence quality,
source kind, family, coverage, marketplace name, provider name, or recency.

## Decision

Introduce the first provider-specific Financial Ledger basis authority for one
narrow source contract only:

Mercado Livre closed-order REVENUE.

The new semantic authority version is exactly:

mercado-livre.closed-order-revenue/1

When and only when durable provider proof establishes that the exact canonical
REVENUE observation came from an accepted closed Mercado Livre order source,
the authority explicitly classifies that source fact as:

FinancialLedgerBasis.ACTUAL

This is a new explicit financial-semantic contract. It is not an inference from
CONFIRMED, MARKETPLACE, provider name, or evidence family.

## Meaning of ACTUAL

Under this authority version, SALE / ACTUAL means only that the trusted
Mercado Livre closed-order source reports that the sale occurred for the exact
provider totalAmount and dateClosed.

It does not mean that settlement occurred, that money reached a payment account,
that money reached a bank, or that reconciliation succeeded.

## Durable provider proof

Authorization requires durable proof across the existing immutable source chain:

V021 integration_mercado_livre_order_source_observation
V023 marketplace_order_revenue_source_promotion
V022 marketplace_order_identity_registry
V015 canonical independent economic evidence

A qualifying V023 row must reference the exact V021 source row and canonical
MarketplaceOrderId and have outcome PROMOTED or DUPLICATE.

IDENTITY_CONFLICT and EVIDENCE_CONFLICT do not authorize materialization.

## Exact semantic equivalence

The authority must prove exact equality between the durable provider source and
the canonical observation for:

- organization ownership
- MarketplaceOrderId
- marketplace = mercado-livre
- externalOrderId
- currency
- totalAmount == component magnitude
- dateClosed == component occurredAt
- observedAt == observation observedAt
- REVENUE
- ADDITION
- MARKETPLACE_ORDER
- CONFIRMED
- PARTIAL
- MARKETPLACE
- br.com.mercadolivre
- provider externalOrderId source reference

The source system key or external reference alone is never sufficient proof.

## Observation identity

V023 does not persist the generated canonical economic observation UUID.

Therefore Version 1 binds provider authority by exact immutable semantic proof
against the durable canonical observation. The materialization authority still
uses that exact observationId as sourceAuthorityIdentity and uses the existing
B3-A source fingerprint over the complete canonical observation.

No caller-supplied observation that is absent from durable canonical evidence may
be treated as authoritative.

## Controlled outcomes

Exact qualifying proof produces Authorized with ACTUAL basis.

Absence of qualifying provider proof produces:

NotAuthorized(BASIS_AUTHORITY_UNAVAILABLE)

Operational database failure produces:

Unavailable

Contradictory durable provider, identity, promotion, or canonical evidence state
produces:

IntegrityFailure

## Scope

Version 1 authorizes no EXPECTED basis rule.

It authorizes no MARKETPLACE_COMMISSION, MARKETPLACE_FEE, SHIPPING, ADVERTISING,
TAX, PRODUCT_COST, FINANCIAL_COST, or OTHER_ADJUSTMENT provider basis rule.

It cannot produce SETTLEMENT, PAYMENT_ACCOUNT, or BANK.

It does not implement source correction materialization.

## Persistence

No new migration is required for the first authority implementation.

V021, V022, V023, V015, and the B3-B source-to-ledger lineage remain the durable
proof surfaces.

If implementation cannot prove the authority safely from those immutable
surfaces, implementation must stop for a governance amendment rather than add a
heuristic fallback.

## Authorization

Acceptance of this ADR authorizes SPEC-0081 design and later bounded B3-C
implementation only.

It does not authorize live-pipeline wiring, automatic reconciliation execution,
public API changes, settlement ingestion, payment-account ingestion, bank
ingestion, financial actions, recovery, or AI decisions.
