# ADR-0082 - Governed Omie SALE / EXPECTED Authority

Status: Proposed

Revision: 2

Date: 2026-09-18

## Context

FLOOOW has preserved a historical PostgreSQL 18.4 runtime at Flyway V029 and
executed a read-only real-data feasibility audit for the narrow financial MVP
vertical slice.

Observed historical evidence includes:

- 85 Mercado Livre order-source observations covering 33 orders;
- 400 Omie transaction-evidence rows covering 135 orders;
- 2,009 Omie product-cost observations;
- 12 canonical marketplace-order identities;
- 21 Mercado Livre revenue-promotion terminal rows;
- zero financial-ledger entries.

F2B identified one real Mercado Livre / Omie order pair with exact diagnostic
bijection, valid ACTUAL source promotion evidence, no ACTUAL identity/currency
contradiction, Omie amount evidence, one selected Omie revision, ACTUAL amount
58.280000 BRL, Omie `valor_total_pedido` 58.280000 and raw diagnostic
difference zero.

This proves a real cross-system path exists.

It does not prove:

```text
Omie financial EXPECTED authority
economic-basis equivalence between Omie and Mercado Livre totals
governed cross-system transaction identity
lifecycle/currentness authority
Omie currency authority
ledger materialization
reconciliation
leakage
Decision Room readiness
```

The governing invariant remains:

```text
SOURCE EVIDENCE
!= TRANSACTION IDENTITY AUTHORITY
!= ECONOMIC BASIS AUTHORITY
!= FINANCIAL AUTHORITY
!= CANONICAL ECONOMIC EVIDENCE
!= LEDGER MATERIALIZATION
!= RECONCILIATION
!= LEAKAGE
```

## Revision-1 trigger

The first adversarial review of ADR/SPEC-0082 found:

```text
BLOCKER - Omie valor_total_pedido and Mercado Livre total_amount
          were not proven economically equivalent

BLOCKER - stable source identity had not been separated from
          revision-specific canonical fact identity

BLOCKER - current V032/B3-B materialization deliberately rejects
          correction participants

HIGH    - diagnostic/provider reference equality lacked a durable
          connection-scoped binding policy

HIGH    - Mercado Livre connection lineage was not made explicit

HIGH    - raw provider sourceFingerprint was insufficient as the
          canonical V3 semantic-evidence fingerprint

HIGH    - provider-local lifecycle currentness parsing was under-specified

MEDIUM  - CONFLICT was incorrectly modeled as a peer persisted decision
```

Revision 1 resolves the design contract by making every unresolved semantic
dimension fail closed instead of inferring it.

## Provider-contract finding: economic basis remains unresolved

Mercado Livre documents `total_amount` as the total value of the order and
documents taxes and shipping as separate dimensions in its order/shipment
contracts.

Omie exposes `valor_total_pedido` together with independent order-total fields
including merchandise, discounts, deductions, taxes and separate freight/other
expense fields.

The provider contracts do not establish that:

```text
Omie valor_total_pedido
==
Mercado Livre total_amount
```

as a universal economic identity.

Therefore:

```text
raw numeric equality
!= economic basis equivalence
```

The real 58.28 / 58.28 F2B pair remains diagnostic evidence only until an
explicit ExpectedSaleBasisPolicy resolves the comparison.

## Revision-2 trigger

The S1-focused adversarial review verified that the Omie `ListarPedidos`
response exposes the complete `pedido_venda_produto` structure, including
`cabecalho`, `frete`, `det`, `market_place`, `total_pedido` and `infoCadastro`.

That review also found that Revision 1 still omitted provider fields that may
change lifecycle interpretation or economic-basis research:

```text
cabecalho:
    tipo_desconto_pedido
    perc_desconto_pedido
    valor_desconto_pedido

    encerrado
    enc_motivo
    enc_data
    enc_hora

market_place:
    nTaxa
    nEnvio

det[].produto:
    tipo_desconto
    percentual_desconto

det[].inf_adic:
    nao_gerar_financeiro
    nao_somar_total
```

The provider contract explicitly states that `encerrado` indicates an ended
order, `nao_gerar_financeiro` suppresses generation of accounts receivable for
an item, `nao_somar_total` excludes an item from the NF-e total, and
`market_place` carries marketplace fee/shipping values.

Because S1 exists to preserve enough source evidence to research later
financial-basis and lifecycle policy, omitting those fields would make V033 an
incomplete acquisition boundary.

Revision 2 therefore expands S1 evidence only. It does not assign financial
meaning to these fields.

## Decision

TASK-0165S remains decomposed into three governed slices, but S1 is expanded to
capture the evidence required to resolve the new basis and currentness gates.

```text
S1 / intended V033
Omie lifecycle + origin + financial-basis source evidence enrichment

        ↓ S1 field proof

        ├── TransactionIdentityBindingPolicy research/freeze
        └── ExpectedSaleBasisPolicy research/freeze

S2 / intended V034
Governed ML <-> Omie transaction identity decision

        ↓ durable identity gate

S3 / intended V035
Canonical ERP REVENUE promotion
+ exact source/canonical lineage
+ SALE / EXPECTED basis authority
```

Completion of one gate makes the next gate possible. It never selects the next
gate automatically.

## S1 - source evidence enrichment

S1 remains source acquisition only.

Intended capability:

```text
marketplace-economic.omie-transaction-evidence.reacquisition-v3
```

Historical v0/v1/v2 evidence remains immutable.

S1 must preserve lifecycle/origin evidence and enough raw financial
decomposition to research the eventual ExpectedSaleBasisPolicy.

At minimum the V3 source contract must be capable of preserving, when supplied
by the provider:

```text
source_order_ref
source_integration_ref
source_customer_order_ref
source_order_origin

source_created_local
source_modified_local

source_cancelled
source_cancelled_local

source_invoiced
source_invoiced_local

source_authorized
source_denied
source_returned
source_returned_partial

source_status

order_discount_type
order_discount_percent
order_discount_amount

source_closed
source_closed_reason
source_closed_local

total_order_amount
merchandise_amount
discount_amount
deduction_amount

freight_amount
insurance_amount
other_expense_amount

marketplace_fee_amount
marketplace_shipping_amount

tax totals required by the supported provider response

item-level economic fields required to explain order basis:
quantity
unit value
discount type
discount percent
discount value
deduction value
merchandise value
item total
do_not_generate_financial
do_not_sum_total

observed_at
source_fingerprint
source_evidence_semantic_fingerprint
```

Exact physical names remain an S1 implementation detail, but the distinctions
must not be collapsed.

### Capability-specific V3 typed record

V3 must use a capability-specific typed source contract/parser rather than silently
changing the meaning of the legacy `OmieTransactionEvidenceRecord`.

The legacy record keeps its historical `occurredAt: Instant?`, status, amount and
identifier-oriented product semantics for v0/v1/v2. V3 needs a distinct typed shape
capable of provider-local lifecycle time and line-level financial evidence.

A V3 implementation may introduce a new record/committer type or a strictly
capability-discriminated equivalent, but it must not route V3 lifecycle authority
through the legacy `data_previsao -> UTC midnight` field.

### Line-level financial evidence

The existing `product_refs` representation is identity-oriented and may emit
multiple identifier observations for one provider item. It must not be overloaded
with item financial amounts.

V3 item economic evidence is line-centric: one provider `det` line remains one
economic line with its quantity/value fields and its available identifiers.

Multiplicity must be retained even when two lines have identical product/value
content. Identifier fan-out must not multiply financial amounts.

### Intended V033 persistence shape

V033 remains additive to V026. Historical columns/rows are not rewritten.

Provider-local lifecycle timestamps are represented as `timestamp without time
zone` (or an equivalent local-time type), never `timestamptz`.

The V3 semantic-evidence fingerprint is mandatory for V3 rows and must be exactly
a 64-character lowercase SHA-256 value.

Item financial detail must use a dedicated V3 line-level representation (for
example a dedicated JSONB column or child relation); it must not change the
meaning of historical `product_refs`.

S1 does not create:

```text
financial transaction identity
ExpectedSaleBasisPolicy
canonical REVENUE
financial basis authority
ledger entries
reconciliation
Decision Room authority
```

## Raw provider fingerprint versus semantic-evidence fingerprint

The existing `source_fingerprint` remains raw/provider-payload evidence.

It must not be reused as:

```text
transaction identity fingerprint
financial authority fingerprint
canonical V3 semantic-evidence fingerprint
```

V3 introduces a distinct versioned semantic-evidence fingerprint over the
normalized persisted V3 fields that can affect later identity, lifecycle or
economic-basis decisions.

The canonicalization contract must preserve:

```text
explicit missing markers
true / false / missing distinction
exact decimal semantics
provider-local date/time semantics
normalized provider text
field names and schema version
item multiplicity
deterministic item ordering
order-level discount evidence
order-ended evidence
marketplace fee/shipping evidence
item financial-exclusion flags
```

Exact replay of one V3 page must verify the complete V3 semantic fingerprint,
not only `source_order_ref` plus raw `source_fingerprint`.

## Provider-local lifecycle time contract

Provider date and time fields remain local temporal evidence.

For each date/time pair:

```text
both missing
    -> local timestamp missing

both present and valid
    -> LocalDateTime

only one present
    -> REMOTE_DATA_INVALID
```

V3 must not reuse the legacy logic that turns `data_previsao` into midnight UTC.

The provider revision candidate is:

```text
source_modified_local
    ?: source_created_local
```

For a source eligible for later currentness authority:

```text
source_created_local must be present
source_modified_local, when present, must not precede source_created_local
```

At the same maximal provider revision:

```text
equivalent semantic-evidence fingerprints
    -> replay-equivalent

different semantic-evidence fingerprints
    -> IntegrityFailure
```

FLOOOW `observed_at` does not make an older provider revision newer.

## Workflow etapa

`etapa` remains opaque provider workflow evidence.

The F2B value `60` is not interpreted as expected, actual, valid, invalid,
cancelled, invoiced or authorized.

## Lifecycle booleans

Missing remains missing:

```text
missing cancelled
!= cancelled = false
```

Unknown non-empty provider flag values fail source parsing.

`invoiced = false` does not automatically block an earlier commercial
expectation.

Current `cancelled = true` makes current EXPECTED unavailable while historical
source evidence remains immutable.

## S1 real-data gate

S1 field proof must report, for at least one real candidate:

```text
origin
customer/integration references
lifecycle creation
lifecycle modification when present
explicit cancellation state
financial decomposition fields
item-level basis evidence when supplied
raw provider fingerprint
semantic-evidence fingerprint
exact replay result
organization scope
Omie connection scope
```

The gate must also show which potentially value-shaping fields are missing.

For the real candidate, the gate must explicitly report:

```text
encerrado / enc_data / enc_hora
market_place.nTaxa
market_place.nEnvio
header discount fields
item nao_gerar_financeiro
item nao_somar_total
```

These values are preserved as source evidence only. No S1 rule may infer that
an ended order, financial-excluded item, NF-e-total-excluded item or marketplace
fee/shipping field changes SALE / EXPECTED until a later versioned policy says
so.

A successful S1 acquisition gate does not by itself authorize S2 or S3.

## ExpectedSaleBasisPolicy

No Omie amount field is directly authorized as `SALE / EXPECTED` by this ADR.

A separately frozen, versioned ExpectedSaleBasisPolicy must determine the
economic amount comparable to the exact Mercado Livre ACTUAL basis.

The policy must be derived from:

```text
official provider field semantics
durable V3 financial decomposition
matched real-data evidence
explicit treatment of discounts
explicit treatment of deductions
explicit treatment of freight / insurance / other expenses
explicit treatment of relevant tax dimensions
explicit treatment of marketplace fee/shipping source fields
explicit treatment of item financial-exclusion / total-exclusion flags
explicit treatment of order-level and line-level discount evidence
explicit treatment of ended-order evidence
exact decimal arithmetic
```

The policy must not be inferred from one zero-delta sample.

Before a policy exists:

```text
S3 basis result
-> NotAuthorized(FINANCIAL_BASIS_UNRESOLVED)
```

A policy may be intentionally narrow. If it can prove comparability only for a
restricted source shape, orders outside that shape remain NotAuthorized rather
than receiving a guessed formula.

## TransactionIdentityBindingPolicy

Text equality remains evidence, not identity authority.

Automatic S2 confirmation requires a durable connection-scoped binding policy
for the exact pair:

```text
organization
Mercado Livre connection
Omie connection
binding policy version
```

The policy declares which Omie reference, if any, is authoritative for the
external Mercado Livre order reference under that integration contract.

Possible reference kinds are conceptually:

```text
CUSTOMER_ORDER_REFERENCE
INTEGRATION_ORDER_REFERENCE
```

No reference kind is selected merely because one historical sample happens to
equal a Mercado Livre order ID.

The policy must preserve:

```text
authorized principal / origin
policy provenance
policy version
effective relation semantics
```

If no trustworthy binding policy can be established, automatic identity
confirmation remains unavailable and the alternative is an explicit governed
confirmation decision.

## Mercado Livre connection lineage

A canonical MarketplaceOrderId is not enough to prove the operational Mercado
Livre connection.

S2 must prove that the selected Mercado Livre connection durably observed the
same canonical order through V022 lineage.

A qualifying connection proof is either:

```text
V022 identity.first_source_connection_id
    == selected Mercado Livre connection
```

or a successful exact V022 occurrence-promotion row from that same connection
to the same canonical order, joined back to its exact provider source.

Cross-connection fallback is forbidden.

## S2 decisions and derived conflict

Persisted S2 decisions are:

```text
CONFIRMED
REJECTED
```

with explicit revision/supersession semantics.

`CONFLICT` is a resolver outcome, not a peer human/system decision kind.

Conceptually:

```text
durable decisions/evidence
        ↓
resolution

UNRESOLVED
CONFIRMED
REJECTED
CONFLICT
```

Competing current confirmations, incompatible policy lineages or contradictory
current evidence resolve to `CONFLICT`.

## S2 normalization

Representation-only normalization may:

```text
trim surrounding whitespace
remove one leading representation-only '#'
trim again
reject empty
```

Forbidden:

```text
fuzzy matching
substring matching
numeric coercion
leading-zero deletion
amount/date matching as confirmation
SKU-as-transaction confirmation
```

## S3 preconditions

S3 requires all of:

```text
eligible current S1 source revision
resolved ExpectedSaleBasisPolicy
S2 CONFIRMED transaction identity
exact V022 Mercado Livre connection lineage
canonical V022 order subject
canonical currency authority
explicit non-cancelled lifecycle
resolved expected amount under the exact basis policy
```

## S3 canonical component

When and only when all S3 preconditions are satisfied:

```text
family        = MARKETPLACE_ORDER
componentType = REVENUE
direction     = ADDITION

sourceKind    = ERP
sourceSystem  = omie

quality       = CONFIRMED
coverage      = PARTIAL
```

`COMPLETE` remains forbidden.

Amount comes from the resolved ExpectedSaleBasisPolicy, not directly from
`valor_total_pedido`.

Currency comes from the canonical marketplace-order identity and remains
separately attributable.

## Stable source identity versus revision-specific fact identity

The provider source identity remains stable across revisions:

```text
omie-order/{connectionId}/{sourceOrderRef}
```

That stable source identity must not itself become the canonical fact ID.

A canonical economic fact is revision-specific.

The fact/component identity derivation must include a versioned semantic
revision identity that changes whenever the accepted current economic meaning
changes and remains stable for exact replay.

Conceptually:

```text
stable source identity
+ S2 transaction decision identity
+ ExpectedSaleBasisPolicy version
+ provider revision identity
+ resolved expected amount
+ canonical currency
+ authority semantic version
        ↓
semantic revision fingerprint
        ↓
revision-specific fact_id / component_id
```

Exact replay of the same semantic revision must resolve to the same identifiers.

A later accepted economic revision must resolve to different identifiers so
V015 can retain:

```text
superseded_fact_id
!= replacement_fact_id
```

The exact UUID derivation algorithm must be versioned before S3 implementation.

## Canonical correction versus ledger correction

S3 may eventually record a valid V015 `SOURCE_CORRECTION` for a later provider
revision.

That does not imply current ledger materialization can consume it.

Current V032/B3-B materialization deliberately blocks facts participating in a
correction context and does not implement correction ledger lineage.

Therefore Version 1 financial-basis authorization is explicitly
initial-materialization-only for non-correction-participating current facts.

If the current canonical fact participates in correction lineage and no
separate governed ledger-correction boundary exists:

```text
NotAuthorized(CORRECTION_MATERIALIZATION_UNSUPPORTED)
```

Historical ledger lineage already created before a later correction remains
replayable under the existing B3-B contract.

TASK-0165S does not authorize a ledger-correction implementation.

## S3 exact promotion lineage

S3 must bind:

```text
exact V3 source coordinates
V3 semantic-evidence fingerprint
S2 durable transaction decision
binding-policy identity/version
ExpectedSaleBasisPolicy identity/version
canonical MarketplaceOrderId
exact revision-specific V015 fact ID
authority semantic version
authority fingerprint
promotion outcome
promotion time
```

This deliberately improves on V023 by retaining the exact canonical fact ID.

## Governed EXPECTED read contract

Conceptually:

```text
Authorized
NotAuthorized(reason)
Unavailable
IntegrityFailure
```

NotAuthorized reasons include at least:

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

Contradictory durable state, same-revision semantic contradiction, cross-scope
state, lineage mismatch, canonical-fact mismatch, fingerprint mismatch or
unsupported semantic version is `IntegrityFailure`.

## Read consistency and connection lifecycle

An authority decision spanning multiple durable surfaces must use one coherent:

```text
READ ONLY
REPEATABLE READ
```

database snapshot.

New TASK-0165S financial authority adapters must not introduce additional direct
`DriverManager.getConnection(...)` lifecycle debt.

A narrow injectable connection/DataSource seam is permitted. A global
persistence refactor is not authorized.

## Relationship to C2 and later MVP path

TASK-0165S does not implement C2.

Later:

```text
Omie governed expected-sale basis  -> SALE / EXPECTED
Mercado Livre governed REVENUE     -> SALE / ACTUAL

EXPECTED + ACTUAL
    -> ledger
    -> reconciliation
    -> Decision Room
```

The F2B 58.28 pair remains a candidate for the future zero-divergence field
proof, not proof that the two provider totals are universally equivalent.

## Non-goals

TASK-0165S does not authorize:

```text
provider writes
fuzzy transaction identity
product-identity changes
C2 implementation
ledger correction materialization
financial ledger runtime activation
reconciliation execution
Decision Room production activation
frontend changes
automatic recovery
pricing/commercial roadmap integration
Sierra-study integration
autonomous financial action
```

## Required sequence

```text
ADR-0082 / SPEC-0082 Revision-2 adversarial review
        ↓
S1 implementation may become selectable
        ↓
S1 real-data field proof
        ↓
freeze TransactionIdentityBindingPolicy
freeze ExpectedSaleBasisPolicy
        ↓
S2 implementation
        ↓
S2 durable identity proof
        ↓
S3 implementation
        ↓
S3 EXPECTED authority proof
        ↓
return to C2
```

Green at one gate means the next gate is possible. It does not mean the next
gate was chosen.
