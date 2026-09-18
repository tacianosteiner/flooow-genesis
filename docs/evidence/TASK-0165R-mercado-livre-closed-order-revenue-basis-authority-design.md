# TASK-0165R: Mercado Livre Closed-Order Revenue Basis Authority Design

Status: DESIGN READY FOR AUDIT

Date: 2026-09-17

## Purpose

Define the first explicit provider-specific FinancialLedgerBasis authority after
TASK-0165Q B3-A/B3-B without inferring basis from generic economic evidence.

## Source-contract audit result

TASK-0154 proves a closed Mercado Livre order REVENUE source with exact
totalAmount, dateClosed, observedAt, canonical order identity, and marketplace
provenance.

TASK-0154 does not itself classify that evidence as EXPECTED or ACTUAL.

ADR-0080 and SPEC-0080 prohibit inferring basis from CONFIRMED, MARKETPLACE,
family, provider name, coverage, or timestamp.

Therefore a new explicit authority contract is required.

## Design decision

Version 1 explicitly defines exact accepted closed Mercado Livre order revenue as
SALE / ACTUAL only after durable V021 + V022 + V023 + V015 proof.

Authority semantic version:

mercado-livre.closed-order-revenue/1

## Important lineage constraint

V023 does not persist the canonical economic observation UUID.

The authority therefore must verify exact immutable provider-source semantics
against the exact durable canonical observation before emitting Authorized.

A matching system key or external order reference is insufficient.

## Explicit exclusions

No EXPECTED mapping.
No provider inference from CONFIRMED.
No settlement authority.
No payment-account authority.
No bank authority.
No live pipeline.
No public API.
No automatic reconciliation.
No source correction materialization.
No AI or financial action.

## Next slice after audit

4C-B3-C1

Implement the provider-specific application authority contract and focused pure
tests only.

4C-B3-C2 will add the PostgreSQL durable proof adapter and adversarial persistence
tests.

4C-B3-D remains the later live-pipeline and field-proof integration slice.
