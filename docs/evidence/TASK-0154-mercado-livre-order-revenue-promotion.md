# TASK-0154: Mercado Livre Order Revenue Promotion

Status: Authorized

Date: 2026-09-06

Governing ADR: ADR-0055

Specification: SPEC-0054

## Objective

Create the smallest safe live financial bridge required by the MVP:

```text
durable Mercado Livre order total_amount
-> canonical independent REVENUE evidence
```

using the canonical order identity created by TASK-0153.

## Acceptance

TASK-0154 is accepted only when:

- only source rows with `date_closed` are eligible;
- canonical V022 identity is reused rather than reallocated;
- source/identity currency mismatch fails closed;
- source `total_amount` becomes exactly one REVENUE/ADDITION fact;
- exact decimal semantics are preserved;
- family is MARKETPLACE_ORDER;
- evidence quality is CONFIRMED;
- coverage claim is PARTIAL;
- occurredAt is source `date_closed`;
- observedAt is durable source observedAt;
- source is MARKETPLACE / br.com.mercadolivre / external order id;
- existing independent economic evidence remains the only evidence write
  authority;
- equal re-observation is Duplicate;
- changed canonical revenue meaning is explicit conflict;
- no automatic correction occurs;
- no paid amount, sale fee, shipping, tax, settlement or product cost is
  promoted;
- terminal source processing is durable/idempotent;
- infrastructure/integrity failure does not become a terminal business result;
- exactly seven implementation paths change;
- all SPEC-0054 gates and repository CI pass.

## Explicit non-claims

TASK-0154 does not establish:

- complete seller revenue coverage;
- marketplace commission;
- marketplace fixed/other fee;
- financing cost;
- seller shipping cost;
- discount/rebate attribution;
- refunds or chargebacks;
- tax liability/payment/recoverability;
- Mercado Pago settlement/release;
- bank reconciliation;
- product cost;
- final order margin.

## MVP effect

TASK-0154 is intentionally enough to let the future MVP display:

```text
OrderOccurrence = known
Revenue = observed/partial
Fees = missing
Shipping = missing
Product cost = missing
Tax = missing
Settlement = missing
Economic Truth = explicitly incomplete
```

The product must prefer visible incompleteness over invented profitability.

## Completion evidence

Implementation evidence is appended here only after implementation exists and
all local gates pass.