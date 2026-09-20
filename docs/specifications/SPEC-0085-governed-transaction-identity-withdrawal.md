# SPEC-0085 — Governed transaction identity withdrawal

## Scope

This specification evolves V035 forward-only.

It adds explicit neutral withdrawal of one current confirmed transaction identity relation.

It does not implement S2B automatic policy, ExpectedSaleBasisPolicy, S3 or C2.

## State

Allowed decision kinds after V036:

- `CONFIRMED`
- `REJECTED`
- `WITHDRAWN`

`WITHDRAWN` is not equivalent to `REJECTED`.

## Valid withdrawal command

A withdrawal must have:

- `kind = WITHDRAWN`
- `reason = CORRECTION`
- `revision > 1`
- a non-null `supersedesDecisionId`

The predecessor must be the exact current head for:

`organizationId + omieConnectionId + sourceOrderReference + marketplaceOrderId`

and the predecessor kind must be `CONFIRMED`.

A rejected relation cannot be withdrawn.

An already withdrawn relation cannot be withdrawn again by superseding the historical confirmation.

## Evidence lineage

Withdrawal is not a fresh provider-evidence interpretation.

The following fields must be byte/semantic equal to the confirmed parent:

- ML connection
- ML capability
- ML progress version
- ML record ordinal
- external order ID
- currency
- Omie capability
- Omie progress version
- Omie record ordinal
- Omie semantic fingerprint
- provider revision local

Current V3 compatibility checks are intentionally skipped for `WITHDRAWN`.

This does not authorize substitution of newer evidence.

## Authorization

Withdrawal requires the existing exact permission:

`TRANSACTION_IDENTITY_DECISION_WRITE`

The current command credential and current grant must be valid in the write transaction.

The new withdrawal decision persists the new authorization lineage.

The historical parent keeps its original authorization lineage.

## Fingerprints

The intent fingerprint includes the withdrawal kind, `CORRECTION`, target relation, principal, provenance and superseded decision.

The decision semantic fingerprint uses:

- the new intent;
- copied historical evidence lineage;
- current withdrawing authorization lineage.

Correlation ID remains non-semantic.

Replay of an existing decision ID compares the persisted original intent and returns the historical semantic fingerprint.

Replay does not reinterpret later provider evidence.

## Projection

The immutable decision ledger remains authoritative history.

`marketplace_transaction_identity_head` remains a derived current projection.

A successful withdrawal atomically changes the relation head from:

`CONFIRMED`

to:

`WITHDRAWN`

The existing partial uniqueness rules for `CONFIRMED` then release both global reservations.

The withdrawn head remains present to preserve relation history and prevent silent mutation.

## Concurrency

Withdrawal uses the same deterministic subject and target advisory lock namespaces used by V035.

It intentionally does not lock `integration_connector_progress`.

Required concurrency properties:

- two withdrawals of the same confirmed parent: one succeeds;
- withdrawal versus confirmation of another target for the same subject serializes;
- withdrawal versus confirmation of the same target from another subject serializes;
- grant revocation remains serialized through command authorization;
- rollback cannot leave a projection without its immutable decision.

## Fail-closed rules

Reject:

- root `WITHDRAWN`;
- withdrawal of `REJECTED`;
- withdrawal of `WITHDRAWN`;
- stale predecessor;
- changed subject;
- changed target;
- changed historical evidence lineage;
- invalid authorization lineage;
- fingerprint mismatch;
- cross-organization lineage.

## Field status

Implementation tests are synthetic infrastructure proof only.

They do not create:

- a real principal;
- a real grant;
- a real withdrawal;
- a real governed pair corpus.

Real S2A field proof remains HOLD.