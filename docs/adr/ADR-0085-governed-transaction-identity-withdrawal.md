# ADR-0085 — Governed transaction identity withdrawal

## Status

Candidate selected for forward-only implementation and adversarial validation.

Real authority provisioning and field activation remain HOLD.

## Context

V035 supports immutable `CONFIRMED` and `REJECTED` decisions with a derived current head.

A later contradictory current Omie V3 revision correctly blocks a new confirmation against the contradicted target.

However, the same current-evidence compatibility requirement also prevents an authorized correction from releasing a previously confirmed relation.

That creates a governance dead-end: a historical confirmation can continue consuming the global subject and marketplace-target uniqueness reservations even when current evidence no longer corroborates it.

## Decision

Add a third transaction identity kind:

`WITHDRAWN`

`WITHDRAWN` means:

The authority of one current `CONFIRMED` subject-target relation has been explicitly revoked.

It does not mean:

- the historical confirmation never happened;
- the target is proven false;
- the relation is `REJECTED`;
- another target is confirmed;
- current provider evidence itself performed the withdrawal.

## Transition

The only valid initial transition is:

`CONFIRMED -> WITHDRAWN`

The withdrawal:

- must be a `CORRECTION`;
- must supersede the exact current `CONFIRMED` head;
- must keep the same organization, stable Omie subject and marketplace target;
- must copy the exact historical ML and Omie evidence lineage from the parent;
- must use current valid command authorization lineage for the withdrawing principal;
- must not depend on current V3 compatibility with the historical target;
- must not call the provider;
- must not create a replacement confirmation.

## Cardinality

The current-head projection remains derived.

The existing organization-wide partial unique indexes apply only to `kind='CONFIRMED'`.

Advancing a head from `CONFIRMED` to `WITHDRAWN` therefore atomically releases:

- the stable Omie subject confirmed slot;
- the canonical marketplace target confirmed slot.

History remains immutable.

## Locking

Normal confirmation/rejection continues using the V3 ingestion progress fence.

Withdrawal does not use the V3 progress fence because it revokes historical decision authority rather than deriving a new relation from current provider evidence.

Withdrawal still uses the same:

- decision-id advisory lock;
- stable subject advisory lock;
- canonical marketplace target advisory lock;
- authorization/principal serialization.

Therefore it remains compatible with confirmation, correction and future policy writers without allowing two simultaneous current confirmations.

## Consequences

Current contradictory, missing or damaged later V3 evidence cannot make an old confirmed relation permanently irremovable.

Current V3 evidence still cannot create a withdrawal.

The principal and exact permission grant remain authority.

No operational route, real grant or field decision is introduced by this ADR.