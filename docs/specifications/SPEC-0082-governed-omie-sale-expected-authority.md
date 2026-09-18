# SPEC-0082 - Governed Omie SALE / EXPECTED Authority

Status: Draft

Revision: 2

Source decision: ADR-0082

## Objective

Define a fail-closed design for producing governed `SALE / EXPECTED` authority
from durable Omie sales-order evidence without allowing provider evidence,
diagnostic identity, numeric coincidence, workflow state, missing values or
local acquisition order to become financial truth.

Implementation is not yet authorized.

## Revision-2 S1 completeness amendment

The provider contract exposes additional source fields that can materially
affect later lifecycle or economic-basis analysis and therefore must be
preserved by V3 before any policy is frozen.

Revision 2 adds:

```text
order-level:
    discount type / percent / amount
    ended flag / reason / local ended time
    marketplace fee amount
    marketplace shipping amount

line-level:
    discount type / percent
    do-not-generate-financial flag
    do-not-sum-total flag
```

These fields are source evidence only. S1 does not interpret them as financial
authority.

## Slice model

```text
S1
Omie lifecycle + origin + financial-basis source evidence

S2
durable connection-scoped ML <-> Omie transaction identity

S3
canonical ERP REVENUE
+ exact source/fact lineage
+ governed SALE / EXPECTED basis authority
```

S1 is the only slice that may become selectable after Revision-1 design review.

S2 requires S1 field proof plus a frozen TransactionIdentityBindingPolicy.

S3 requires S2 plus a frozen ExpectedSaleBasisPolicy.

## Global invariants

```text
missing != zero
unknown != false
numeric equality != economic basis equivalence
candidate != confirmed
diagnostic exact != financial authority
source evidence != canonical evidence
stable source identity != revision-specific fact identity
EXPECTED != ACTUAL
canonical correction != ledger-correction authorization
projection != authority
```

## S1 capability

Intended capability:

```text
marketplace-economic.omie-transaction-evidence.reacquisition-v3
```

Historical v0/v1/v2 evidence remains immutable.

## S1 source evidence contract

V3 must preserve, when the provider supplies them, separate typed fields for:

```text
identity/reference:
    sourceOrderReference
    integrationOrderReference
    customerOrderReference
    sourceOrderOrigin

lifecycle:
    providerCreatedLocal
    providerModifiedLocal

    cancelled
    cancelledLocal

    invoiced
    invoicedLocal

    authorized
    denied
    returned
    partiallyReturned

workflow:
    sourceStatus

order lifecycle/status:
    orderEnded
    orderEndedReason
    orderEndedLocal

order discount evidence:
    orderDiscountType
    orderDiscountPercent
    orderDiscountAmount

financial decomposition:
    totalOrderAmount
    merchandiseAmount
    discountAmount
    deductionAmount

    freightAmount
    insuranceAmount
    otherExpenseAmount

    marketplaceFeeAmount
    marketplaceShippingAmount

    provider tax-total fields used by the supported order contract

item economic detail:
    product identity
    quantity
    unitValue
    discountType
    discountPercent
    discountValue
    deductionValue
    merchandiseValue
    itemTotal
    doNotGenerateFinancial
    doNotSumTotal

observation:
    observedAt
    sourceFingerprint
    sourceEvidenceSemanticFingerprint
```

Exact SQL/Kotlin names may differ, but semantically distinct fields may not be
collapsed.

### Capability-specific V3 record contract

The legacy `OmieTransactionEvidenceRecord` remains the v0/v1/v2 contract. Its
`occurredAt: Instant?` and identifier-oriented `products` shape must not be reused as
the V3 lifecycle/economic authority model.

V3 uses a distinct typed connector record contract, or an equivalently strict
capability-discriminated type, that can represent:

```text
provider-local LocalDateTime lifecycle values
tri-state lifecycle flags
financial decomposition
line-centric item economics
V3 semantic-evidence fingerprint
```

The V3 parser must be capability-specific and cannot feed provider-local lifecycle
through the legacy `parseDate(data_previsao) -> UTC midnight` path.

### V3 item-line shape

The existing `OmieTransactionProductObservation` / `product_refs` model is
identifier-oriented and can represent one provider line through multiple product
identifiers. It is not the V3 economic-line model.

V3 financial item evidence must preserve one provider `det` line as one economic
line containing its available identifiers plus the line's quantity/value fields.

Required invariants:

```text
identifier fan-out does not duplicate money
identical economic lines retain multiplicity
missing item values remain missing
line ordering does not affect semantic fingerprint
```

A dedicated V3 JSONB structure or child relation is acceptable. Reinterpreting
historical `product_refs` is forbidden.

### V033 storage constraints

V033 is additive. Historical rows remain valid with new V3-only fields missing.

For V3 rows:

```text
sourceEvidenceSemanticFingerprint is mandatory
and matches ^[0-9a-f]{64}$

provider-local lifecycle values use a timezone-free SQL representation

V3 line-level economic evidence is stored separately from historical product_refs
```

S1 does not calculate an EXPECTED amount.

## Raw provider fingerprint

`sourceFingerprint` remains the raw/provider-payload fingerprint.

It is not a financial authority fingerprint and is not sufficient by itself for
V3 replay validation.

## V3 semantic-evidence fingerprint

V3 introduces a separate versioned SHA-256 semantic fingerprint over the
normalized persisted V3 evidence.

Canonicalization Version 1 must include all identity, lifecycle and
financial-decomposition fields that can influence later policy decisions.

Rules:

```text
schema/version marker is included
missing is encoded explicitly
true / false / missing are distinct
strings use the provider text normalization contract
decimals use canonical exact-decimal form
zero canonicalizes to "0"
provider-local times use an explicit local format
item multiplicity is retained
items are deterministically ordered for canonicalization
order-ended state is included
order-level discount evidence is included
marketplace fee/shipping evidence is included
item financial-exclusion / total-exclusion flags are included
field names/order are fixed by the fingerprint version
```

The digest is lowercase 64-character hexadecimal SHA-256.

A replay of the same durable page must verify the expected V3 semantic
fingerprint for every row.

## Lifecycle parsing

Provider lifecycle date and time form one local temporal value.

For each pair:

```text
date missing + time missing
    -> missing

date present + time present + valid
    -> LocalDateTime

exactly one present
    -> REMOTE_DATA_INVALID
```

The intended formats are the provider contract formats:

```text
date: dd/MM/yyyy
time: HH:mm:ss
```

No timezone is attached.

V3 must not call or reuse the legacy `data_previsao -> UTC midnight` parsing path
for lifecycle authority.

## Lifecycle consistency

For an order eligible for later currentness:

```text
providerCreatedLocal must be present
providerModifiedLocal, when present, >= providerCreatedLocal
```

A partial or malformed pair is ingestion-invalid.

At the maximal provider revision:

```text
same semantic-evidence fingerprint
    -> replay-equivalent

different semantic-evidence fingerprint
    -> IntegrityFailure
```

`observedAt` may order exact replay metadata after provider revision equality,
but cannot override a newer provider revision.

## Lifecycle booleans

Flags retain:

```text
true
false
missing
```

Conceptual provider mapping:

```text
S -> true
N -> false
missing -> missing
other non-empty -> REMOTE_DATA_INVALID
```

`cancelled = true` later blocks current EXPECTED.

`cancelled = missing` later produces lifecycle-incomplete, not false.

`invoiced = false` does not automatically block an earlier commercial
expectation.

`authorized`, `denied`, `returned` and `partiallyReturned` remain provenance in
Version 1 and do not independently redefine EXPECTED.

## Workflow etapa

`sourceStatus` remains opaque workflow evidence.

No hard-coded etapa value grants or denies EXPECTED.

## S1 persistence boundary

Intended V033 is additive after V032.

It must not:

```text
UPDATE historical V026 rows
backfill invented lifecycle values
backfill invented origin
backfill invented financial decomposition
invent currency
invent timezone
```

## S1 field-proof gate

The S1 real-data report must include, without exposing credentials:

```text
hashed order identity
organization/connection scope
origin
customer/integration references

created local time
modified local time or explicit missing
cancelled true/false/missing
cancelled local time or explicit missing

total order amount
merchandise amount
discount amount
deduction amount
freight / insurance / other expense values or explicit missing
relevant provider tax-total values or explicit missing
item economic fields required for basis analysis

raw provider fingerprint
V3 semantic-evidence fingerprint
exact replay result
```

S1 PASS means acquisition semantics are proven.

It does not mean a financial basis or transaction identity is authorized.

## ExpectedSaleBasisPolicy gate

Direct use of `totalOrderAmount` as `SALE / EXPECTED` is forbidden.

A versioned ExpectedSaleBasisPolicy must resolve the amount that is economically
comparable to the exact Mercado Livre ACTUAL order basis.

The policy input may use only durable V3 evidence plus explicit canonical
currency/identity context.

The policy must specify:

```text
included Omie economic fields
excluded Omie economic fields
discount treatment
deduction treatment
freight treatment
insurance treatment
other-expense treatment
tax treatment
marketplace fee/shipping treatment
item do-not-generate-financial treatment
item do-not-sum-total treatment
order-ended treatment
order-level versus line-level discount treatment
item/order reconciliation rules
missing-field behavior
exact decimal formula
qualifying source shape
policy version
```

The policy must be supported by official field semantics and real matched
evidence.

One zero-delta pair is insufficient to establish a universal formula.

A policy may intentionally authorize only a constrained subset of orders.

If no supported policy applies:

```text
NotAuthorized(FINANCIAL_BASIS_UNRESOLVED)
```

## S2 binding-policy scope

Automatic S2 identity requires a durable TransactionIdentityBindingPolicy scoped
by:

```text
organizationId
MercadoLivreConnectionId
OmieConnectionId
bindingPolicyVersion
```

The policy declares which Omie reference field is authoritative for the external
Mercado Livre order reference for that exact integration relationship.

No binding policy may be inferred solely from historical string equality.

The policy must retain provenance and authorized principal/origin.

If no binding policy exists, automatic confirmation is unavailable.

## S2 Mercado Livre connection proof

The selected Mercado Livre connection must be durably linked to the exact
canonical MarketplaceOrderId through V022.

A qualifying proof is:

```text
identity.first_source_connection_id == selected ML connection
```

or an exact successful V022 occurrence-promotion row from the selected
connection to the same canonical order, with its provider source joined and
semantically consistent.

A caller-supplied connection ID alone is not proof.

Cross-connection fallback is forbidden.

## S2 automatic confirmation

After binding-policy and connection-lineage proof, automatic confirmation may
require:

```text
canonical V022 identity
exact organization
exact selected ML connection lineage
exact selected Omie connection
one current eligible V3 Omie order
binding policy applicable
authoritative Omie reference matches canonical ML external order ID
origin evidence satisfies the binding policy
one ML order -> one eligible Omie order
one Omie order -> one canonical ML order
no competing current contradictory evidence
supported policy versions
```

Corroborating non-authoritative references, when present, must not contradict
the binding.

No fuzzy matching, numeric coercion, leading-zero deletion, amount/date matching
or SKU transaction matching is permitted.

## S2 durable decisions

Intended V034 stores versioned/superseding decisions:

```text
CONFIRMED
REJECTED
```

Conceptual fields include:

```text
organization_id
mercado_livre_connection_id
omie_connection_id
marketplace_order_id
omie_source_order_ref

binding_policy_identity/version
decision
decision_revision
supersedes_decision_id

evidence_fingerprint_version
evidence_fingerprint
principal/provenance
decided_at
```

`CONFLICT` is not a persisted peer decision.

Resolver results are:

```text
UNRESOLVED
CONFIRMED
REJECTED
CONFLICT
```

Competing current decisions/policies or incompatible current evidence resolve to
`CONFLICT`.

## S3 preconditions

S3 requires:

```text
eligible current S1 V3 source revision
resolved ExpectedSaleBasisPolicy
S2 CONFIRMED resolution
exact ML connection lineage
canonical V022 subject
canonical currency authority
explicit non-cancelled lifecycle
resolved exact expected amount
```

## S3 canonical component

Exactly:

```text
family        = MARKETPLACE_ORDER
componentType = REVENUE
direction     = ADDITION

source.kind      = ERP
source.systemKey = omie

quality  = CONFIRMED
coverage = PARTIAL
```

Amount is the exact ExpectedSaleBasisPolicy result.

Currency is the canonical marketplace-order currency.

The authority records that amount source and currency source are distinct.

## Stable source reference

The canonical provider source reference is stable across revisions:

```text
omie-order/{connectionId}/{sourceOrderRef}
```

It identifies the provider source, not a specific economic revision.

## Revision-specific semantic identity

Every accepted economic revision must have a versioned semantic revision
fingerprint covering at least:

```text
stable provider source identity
V3 semantic-evidence fingerprint
S2 decision identity
binding policy version
ExpectedSaleBasisPolicy version
provider revision identity
resolved expected amount
canonical currency
authority semantic version
```

The canonical `fact_id` and `component_id` must be deterministic for that exact
semantic revision and must differ from identifiers for a later materially
different revision.

Required invariant:

```text
exact replay
    -> same fact_id / component_id

later accepted economic revision
    -> different fact_id / component_id
```

The exact UUID derivation algorithm and its version are a mandatory S3
pre-implementation gate.

## Canonical write

S3 writes canonical evidence only through
`MarketplaceIndependentEconomicEvidenceRepository`.

First accepted revision uses `ObserveFact`.

Later accepted changed economic meaning may use V015 `Correct` with
`SOURCE_CORRECTION`, preserving distinct superseded and replacement fact IDs.

Same authoritative provider revision with different semantic material is
`IntegrityFailure`, not correction.

## Current ledger correction limitation

Current V032/B3-B materialization does not support materializing correction
participants.

Therefore S3 Version 1 must never imply otherwise.

A current fact participating in correction lineage returns:

```text
NotAuthorized(CORRECTION_MATERIALIZATION_UNSUPPORTED)
```

for new materialization under the current policy.

Historical exact ledger lineage created before a later correction remains
replayable.

TASK-0165S does not implement ledger correction materialization.

## S3 promotion lineage

Intended V035 binds:

```text
exact V3 source coordinates
V3 semantic-evidence fingerprint

S2 decision identity
binding policy identity/version

ExpectedSaleBasisPolicy identity/version

canonical MarketplaceOrderId
revision-specific canonical fact ID

authority semantic version
authority fingerprint
promotion outcome
promotion timestamp
```

Exact canonical fact ID is mandatory.

## EXPECTED authority result

Conceptually:

```text
Authorized
NotAuthorized(reason)
Unavailable
IntegrityFailure
```

NotAuthorized reasons include:

```text
IDENTITY_UNCONFIRMED
IDENTITY_BINDING_POLICY_UNAVAILABLE
ML_CONNECTION_LINEAGE_UNAVAILABLE
SOURCE_NOT_FOUND
LIFECYCLE_INCOMPLETE
CANCELLED
CURRENT_REVISION_UNPROVEN
FINANCIAL_BASIS_UNRESOLVED
CANONICAL_FACT_NOT_PROMOTED
CURRENCY_AUTHORITY_UNAVAILABLE
CORRECTION_MATERIALIZATION_UNSUPPORTED
```

Operational persistence failure is `Unavailable`.

Contradiction, cross-scope state, same-revision semantic conflict, decision
lineage mismatch, basis-policy mismatch, canonical fact mismatch, fingerprint
mismatch or unsupported version is `IntegrityFailure`.

## Read consistency

Authority reads spanning multiple durable surfaces use one coherent:

```text
READ ONLY
REPEATABLE READ
```

snapshot.

Separately timed reads may not be composed into one authority result.

## Connection lifecycle

New TASK-0165S authority adapters must not add new direct
`DriverManager.getConnection(...)` lifecycle debt.

A narrow injectable connection/DataSource seam is permitted.

No global persistence refactor is authorized.

## Required adversarial coverage

Before S1 completion:

1. v0/v1/v2 rows remain unchanged;
2. V3 replay is idempotent;
3. raw and semantic fingerprints are distinct contracts;
4. semantic fingerprint changes when authority-relevant V3 evidence changes;
5. missing lifecycle remains missing;
6. partial date/time pair is rejected;
7. no provider-local time is converted to UTC;
8. legacy `data_previsao` parser cannot feed V3 lifecycle authority;
9. invalid lifecycle Boolean is rejected;
10. `etapa` cannot grant EXPECTED;
11. missing financial decomposition remains missing;
12. order-ended evidence is preserved without financial interpretation;
13. order-level discount evidence is preserved;
14. marketplace fee/shipping evidence is preserved;
15. item do-not-generate-financial is preserved;
52. item do-not-sum-total is preserved;
53. semantic fingerprint changes when any of those evidence fields changes;
48. exact decimals are preserved;
49. no inferred currency is persisted;
50. no provider mutation occurs.

Before S2 completion:

27. absent binding policy cannot auto-confirm;
16. historical string equality alone cannot auto-confirm;
17. caller-supplied ML connection alone cannot prove lineage;
18. V022 first-source connection proof works;
19. V022 successful occurrence-promotion connection proof works;
20. cross-connection proof fails closed;
21. cross-organization proof fails closed;
22. one-to-many and many-to-one identity fail closed;
23. diagnostic EXACT alone cannot confirm;
24. durable decisions are CONFIRMED/REJECTED;
25. competing current decisions resolve to CONFLICT;
26. supersession is append-only/auditable.

Before S3 completion:

51. `totalOrderAmount` alone cannot authorize EXPECTED;
28. no basis policy -> FINANCIAL_BASIS_UNRESOLVED;
29. policy version and qualifying source shape are exact;
30. missing basis input does not become zero;
31. basis formula uses exact decimal arithmetic;
32. canonical ML currency is used only for the same confirmed order;
33. stable source identity remains stable across reacquisition;
34. exact replay produces same revision-specific fact identity;
35. changed accepted revision produces different fact identity;
36. correction preserves old/new distinct fact IDs;
37. same revision + changed semantics -> IntegrityFailure;
38. V035 lineage binds exact fact ID;
39. basis/fact/fingerprint tampering is detected;
40. correction participant is not newly materializable under current V032/B3-B;
41. historical pre-correction lineage remains replayable;
42. DB failure is Unavailable;
43. repeatable-read snapshot is proven;
44. no new direct DriverManager authority lifecycle is added;
45. no ledger correction implementation is introduced;
46. no reconciliation or Decision Room activation occurs;
47. full build remains green.

## Evidence interpretation

The historical F2B result is now described as:

```text
REAL CROSS-SYSTEM PATH VIABILITY = PROVEN

REAL EXPECTED/ACTUAL ECONOMIC BASIS EQUIVALENCE = NOT PROVEN

REAL END-TO-END FINANCIAL VIABILITY = NOT YET PROVEN

REAL NON-ZERO FINANCIAL LEAKAGE = NOT PROVEN
```

The 58.28 / 58.28 candidate must not be altered to manufacture either basis
equivalence or leakage.

## Implementation gate

Revision 1 is still design only.

After a fresh Revision-2 adversarial review with no blocker applicable to S1,
S1/V033 may become technically selectable.

S2, S3, C2, ledger materialization, reconciliation and Decision Room production
activation remain HOLD until their specific gates are satisfied.
