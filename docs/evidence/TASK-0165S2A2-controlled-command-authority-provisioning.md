# TASK-0165S2A2 — Controlled command authority provisioning

Status: VALIDATED CANDIDATE; FINAL DIFF REVIEW PENDING; REAL FIELD PROOF HOLD

Baseline: `f3801f5965f71106467410f9cd7551f0d49c2b62`

## Result

ADR/SPEC-0086 close the control-plane implementation between the technically
proven V034-V036 substrate and any future legitimate authority. V037 adds an
offline `ControlledCommandAuthorityIssuer`, injected `DataSource`, immutable
operation receipt ledger and no-login issuer/runtime PostgreSQL roles. It is not
a public provisioning API or runtime bootstrap.

No real secret, principal, credential, permission grant, provider call/write or
transaction identity decision was created by this task. V037 role and authority
rows exist only inside discarded Testcontainers databases. The canonical local
PostgreSQL instance was not modified.

## Technical findings carried forward

V034 enforces immutable authority lineage and serializes revocation with writer
admission, but it cannot establish deployment role separation itself. A database
owner/superuser can bypass row triggers. That is an explicit activation blocker,
not a reason to silently widen runtime authority.

The previous V036 adversarial gate remains passed at the authoritative baseline.
Its withdrawal behavior is available only to a legitimate future explicit command
authority; later evidence never creates authority automatically.

## Required next implementation gate

Before any real authority row, accept a separately reviewed deployment-role/login
configuration and human operator ceremony under SPEC-0086. The implementation
was proven only against disposable synthetic PostgreSQL. Required operational
evidence still includes privilege deployment results, secret-safe delivery,
transaction/rollback/retry proof and a nonsecret operator receipt.

Only after that implementation is accepted may a separately authorized operator
consider one explicit V036 field action. The first pair changes corpus from zero
only after its immutable decision commits; it does not activate S2B or establish
economic truth.

## State

```text
V033 Omie V3 ..................... PROVEN
V034 Command Authorization ....... TECHNICALLY PROVEN
V035 Explicit Identity ........... TECHNICALLY PROVEN
V036 Governed Withdrawal ......... TECHNICALLY PROVEN

Controlled provisioning .......... VALIDATED CANDIDATE / FINAL DIFF REVIEW PENDING
active real grants ............... 0
real governed decisions .......... 0
real governed pair corpus ........ 0

S2A REAL FIELD PROOF ............. HOLD
S2B .............................. HOLD
ExpectedSaleBasisPolicy .......... UNFROZEN
S3 ............................... HOLD
C2 ............................... HOLD
```

## Remaining adversarial closure

The executed suites prove the protected seam, V037 migration, initial issuance,
idempotent replay, initial-bind serialization, role denial, concurrent rotation,
grant/revoke serialization, cross-tenant rejection, direct SQL NULL/shape attacks
and V034-V036 regression. No real authority may be provisioned without a separate
accepted operator authority and field-proof gate.
