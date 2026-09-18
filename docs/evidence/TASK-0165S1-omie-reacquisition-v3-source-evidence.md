# TASK-0165S1 - Omie Reacquisition V3 Source Evidence

Status: IMPLEMENTATION CANDIDATE - REAL-DATA FIELD PROOF PENDING

Date: 2026-09-18

## Scope

TASK-0165S1 implements only the S1 evidence-acquisition boundary authorized by
ADR-0082 / SPEC-0082 Revision 2.

It does not implement S2, S3, C2, financial-ledger materialization,
reconciliation or Decision Room activation.

## Capability

```text
marketplace-economic.omie-transaction-evidence.reacquisition-v3
```

V3 is a new independent connector-progress namespace.

Historical v0/v1/v2 observations remain readable and unchanged.

## Runtime boundary

FLOOOW registers one connector object per provider.

V3 therefore enters the existing `OmieProviderConnector` as a distinct
capability delegate with a distinct record type.

The legacy transaction parser remains unchanged.

## Persistence boundary

V033 is additive after V032.

V3 persists:

1. the compatibility/source-coordinate row in
   `integration_omie_transaction_evidence`;
2. V3 lifecycle/order/financial decomposition in the immutable V3 sidecar;
3. line-level financial evidence in the immutable V3 line table.

No historical V026 row is updated.

## No financial authority

S1 persists source evidence only.

In particular:

```text
total_order_amount
marketplace_fee_amount
marketplace_shipping_amount
do_not_generate_financial
do_not_sum_total
order_ended
```

are not interpreted as SALE / EXPECTED authority.

`ExpectedSaleBasisPolicy` remains unresolved.

## Fingerprints

Two distinct fingerprints are retained:

```text
source_fingerprint
    raw provider JSON evidence

source_evidence_semantic_fingerprint
    versioned canonical V3 persisted-evidence semantics
```

The semantic fingerprint excludes local acquisition time and raw JSON field
ordering, but includes identity, lifecycle, financial decomposition and
line-level evidence.

## Lifecycle time

Provider lifecycle date/time pairs are parsed as timezone-free `LocalDateTime`.

Partial date/time pairs fail closed as remote-data-invalid.

V3 does not reuse the historical `data_previsao -> UTC midnight` path.

## Current implementation gate

This file is not real-data field proof.

Required next evidence after local tests:

```text
live Omie V3 reacquisition
real candidate lifecycle/origin fields
financial decomposition presence/missing matrix
semantic fingerprint replay stability
v0/v1/v2 historical digest unchanged
organization/connection isolation
no provider writes
```

Until that proof passes:

```text
S1 = IMPLEMENTATION CANDIDATE
S2 = HOLD
S3 = HOLD
```

## Final real-data proof - V6

Final status:

```text
S1 / V033 = PROVEN
```

Provenance:

```text
implementation commit:
27c291ee399a17ed97fdb8953b86a9a4c7301877

final proof script SHA-256:
23B144BD58725B581A16D350763283F40A9A1C0160EBACE1DA3E5C1C4A150C29

final proof checkpoint:
FLOOOW-0165S1-V3-FINAL-FIELD-PROOF-V6-20260918-141706.txt

final proof checkpoint SHA-256:
48820F04E4BDC33CE20BA3C84706CA9F7B8DD6FB0BC217130431DAAFA574BBF6
```

Admissible proof:

```text
historical v0 = 132
historical v1 = 133
historical v2 = 135
historical evidence unchanged = true

V3 base rows    = 141
V3 sidecar rows = 141
V3 line rows    = 196
V3 progress exhausted = true

real origin:
API = 124
ERP = 17
MLV = 0

origin semantics = provenance only

V022 diagnostic relation:
matched rows = 1
canonical marketplace orders = 1
integration matches = 1
customer matches = 0
one-to-many ambiguity = 0
many-to-one ambiguity = 0

durable candidate lineage:
canonical integration-reference matches = 4
canonical customer-reference matches = 0

currentness conflicts = 0

raw fingerprints present = 141
semantic fingerprints present = 141
raw equals semantic = 0

missing order-ended evidence = preserved missing
missing marketplace fee = preserved missing
missing marketplace shipping = preserved missing
```

Replay proof:

```text
temporary bootstrap network disconnected before replay = true
replay network count = 1
replay network internal = true

new committed pages = 0
new records = 0
already committed pages >= 1

V3 replay idempotent = true
v0/v1/v2 immutable = true
```

The real-data proof creates no transaction identity decision and no financial
authority.

Explicit holds remain:

```text
TransactionIdentityBindingPolicy = not yet frozen
ExpectedSaleBasisPolicy = not yet frozen

S2 = HOLD
S3 = HOLD
C2 = HOLD

REAL EXPECTED/ACTUAL ECONOMIC BASIS EQUIVALENCE = NOT PROVEN
REAL END-TO-END FINANCIAL VIABILITY = NOT YET PROVEN
REAL NON-ZERO FINANCIAL LEAKAGE = NOT PROVEN
```
