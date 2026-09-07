# TASK-0155: Live Marketplace Economic Pipeline Orchestration

Status: Authorized

Date: 2026-09-06

Governing ADR: ADR-0056

Specification: SPEC-0055

## Objective

Create one bounded, stateless callable pipeline:

```text
Mercado Livre source
-> durable V021
-> canonical V022 identity + OrderOccurrence
-> V023 REVENUE promotion
-> Economic Truth / Sales Intelligence projection
```

## Acceptance

TASK-0155 is accepted only when:

- one new application module owns orchestration only;
- ConnectorRuntime remains the provider execution authority;
- the pipeline is fixed to `br.com.mercadolivre` and
  `marketplace-economic.order-source`;
- no direct provider HTTP is introduced;
- no credential access or inline refresh is introduced;
- source, occurrence, revenue and projection phases are all bounded;
- each source page uses a fresh invocation id;
- global deadline is at most five minutes;
- cancellation is honored between stage invocations;
- non-cancellation source failure still allows already-durable downstream work
  to drain;
- provider mismatch fails closed;
- occurrence block stops revenue/projection;
- revenue block stops projection;
- projection checkpoint conflict/integrity failure blocks;
- max-batch exhaustion is visible as `drained=false`;
- no new persistence/checkpoint/lease/scheduler exists;
- result summaries contain no provider payload, order identity, credentials or
  money values;
- exactly six implementation paths change;
- all SPEC-0055 gates and repository CI pass.

## Explicit non-claims

TASK-0155 does not provide:

- background scheduling;
- organization/connection discovery;
- retry persistence;
- distributed leases;
- a global transaction;
- exactly-once execution;
- an HTTP endpoint;
- UI;
- fee/shipping/tax/product-cost/settlement evidence.

## MVP effect

After TASK-0155 there is one application seam that TASK-0156 can wire to HTTP:

```text
refresh
  -> live provider source
  -> canonical economic evidence
  -> current Sales Intelligence projection
```

## Completion evidence

Implementation evidence is appended only after code exists and all local gates
pass.