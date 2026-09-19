# TASK-0165S2A1 — Governed transaction identity withdrawal

## Baseline

Parent HEAD:

`48b5cd3831f3165591ec9519e8b99d4ee540e619`

Parent milestone:

S2A V035 explicit governed transaction identity writer.

## Finding

V035 correctly fails closed when current Omie V3 evidence contradicts a target.

The same compatibility path also prevents an explicitly authorized correction from releasing an older current `CONFIRMED` binding.

This can leave the global subject/target reservation occupied indefinitely.

## Selected correction

Forward-only V036 introduces:

`WITHDRAWN`

Semantics:

`CONFIRMED(O1,M1) -> WITHDRAWN(O1,M1)`

The transition:

- preserves immutable historical confirmation;
- releases the current confirmed reservations;
- does not assert `REJECTED`;
- does not confirm M2;
- copies parent evidence lineage;
- persists new withdrawal authorization lineage;
- does not depend on current V3 compatibility.

## Safety boundary

No real principal, secret, grant, operational route or field decision is created.

S2B remains HOLD.

ExpectedSaleBasisPolicy remains UNFROZEN.

S3 remains HOLD.

C2 remains HOLD.

Real governed pair corpus remains zero until legitimate field authority is provisioned and used.

## Required validation

- domain compilation
- focused PostgreSQL writer tests executed, not cache-only
- contradictory-current-evidence withdrawal
- no implicit replacement confirmation
- evidence-lineage copy
- replay invariance
- confirmed-parent requirement
- concurrent withdrawal serialization
- later V3 integrity damage does not create an irreversible binding
- SQL immutability/projection attacks remain blocked
- full build
- git diff --check

No commit or push is authorized by this execution package.