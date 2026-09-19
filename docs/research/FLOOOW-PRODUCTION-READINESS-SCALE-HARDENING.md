# FLOOOW — Production Readiness & Scale Hardening

Status: PARALLEL READINESS LANE
MVP critical path: SEPARATE

## Connection management

No new direct production dependency on DriverManager.

New adapters should receive an injectable connection seam such as DataSource or ConnectionProvider.

Do not mass-refactor existing repositories during MVP unless required by a proven blocker.

## Local encrypted vault

The current local vault remains acceptable only while its exit criteria are not met.

Exit criteria include:

- multiple replicas;
- ephemeral or shared production runtime;
- distributed shared secret custody;
- master-key rotation requirements;
- centralized secret-access audit requirements.

## API-edge hardening

Before public production exposure explicitly address:

- rate limiting;
- credential revocation lifecycle;
- audit identity;
- TLS assumptions;
- production secret-manager injection.

## Composition root

Application bootstrap decomposition is organizational debt, not current domain debt.

Do not move domain logic merely to reduce file size.

## Security history

Run a full Git-history secret scan, not only a current-snapshot scan.

## Readiness sequence

connection lifecycle / pooling
→ distributed secret custody
→ edge authentication evolution
→ rate limiting
→ composition-root decomposition
→ load and resilience testing
→ production topology validation

## Governance

Every deliberate MVP shortcut should have:

- owner;
- exit criterion;
- trigger condition;
- mitigation;
- readiness lane.

Production debt must be deliberate, not invisible.

## Non-goal

This lane does not redefine:

- Economic Truth;
- identity authority;
- ExpectedSaleBasisPolicy;
- reconciliation semantics;
- Decision Room critical path.