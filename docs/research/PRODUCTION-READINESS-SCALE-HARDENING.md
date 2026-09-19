# FLOOOW — Production Readiness & Scale Hardening

Status: PARALLEL READINESS LANE

MVP critical path: SEPARATE

## Purpose

Production-readiness debt must be explicit without contaminating Economic
Truth work.

## Connection lifecycle rule

Effective immediately:

No new production adapter may introduce a direct dependency on
DriverManager.

New adapters should receive an injectable connection seam such as:

- DataSource;
- ConnectionProvider;
- equivalent infrastructure boundary.

Existing repositories are not mass-refactored during the MVP unless a
proven blocker requires it.

## Connection pooling exit criterion

Connection lifecycle / pooling becomes a blocking production requirement
before meaningful sustained production load.

## Secret custody

The current local encrypted secret vault may remain appropriate during the
current stage only while its exit criteria are not met.

Exit criteria include:

- multiple runtime replicas;
- ephemeral shared production infrastructure;
- distributed secret custody;
- master-key rotation;
- centralized secret-access audit;
- infrastructure requiring external KMS / secret manager.

## API edge hardening

Before public production exposure explicitly address:

- rate limiting;
- credential revocation lifecycle;
- audit identity;
- TLS assumptions;
- production secret-manager injection.

## Composition root

Large application bootstrap code is organizational debt.

Decomposition must remain organizational unless a separate domain
decision authorizes semantic changes.

Possible boundaries:

- AuthenticationConfiguration
- IntegrationBootstrap
- EconomicRoutes
- ReconciliationRoutes
- IdentityRoutes
- HealthRoutes

No refactor solely for aesthetics.

## Git security history

Current-tree secret cleanliness does not prove historical cleanliness.

Required readiness action:

run a full Git-history secret scan.

## Load and resilience

Before production scale:

- connection-pool load test;
- concurrency pressure;
- provider failure simulation;
- database fail/recovery behavior;
- credential rotation under load;
- authorization revocation under load;
- replay/idempotency pressure;
- resource exhaustion behavior.

## Readiness sequence

connection lifecycle / pooling
→ distributed secret custody
→ edge authentication evolution
→ rate limiting
→ composition-root hardening
→ load/resilience testing
→ production topology validation

## Governance requirement

Every deliberate MVP shortcut must have:

- explicit description;
- exit criterion;
- trigger condition;
- mitigation;
- destination readiness lane.

Production debt must be deliberate.

It must never become invisible.

## Non-goal

This lane cannot redefine:

- Economic Truth;
- transaction identity;
- authority;
- ExpectedSaleBasisPolicy;
- reconciliation semantics;
- Governed Decision Room.