# TASK-0165S - Governed Omie SALE / EXPECTED Authority - Design Evidence

Status: DESIGN ONLY - NO IMPLEMENTATION

Revision: 2

Date: 2026-09-18

## Branch and base

```text
branch:
research/task-0165s-governed-omie-sale-expected-authority

base:
research/task-0165p-governed-reconciliation-assessment-identity-lineage
fcff073793a3bd806d7302dab445404725baa4b9
```

## Revision-0 artifact hashes

The original TASK-0165S design package was created without add/commit/push:

```text
ADR-0082:
9C2E7C1931C73BA8A4CCE475256D5FB1DA516AF8BC95C23DD68D4BBE7CE6FF8B

SPEC-0082:
61929AFC9B2C52EDFBAE3CFE7C1A476C414199966D43D4CF69FDC76176D95753

TASK-0165S evidence:
7D03DB881E415C8840A832A5F100BBE314CBE446D8B63F095A80CDA4238D221B
```

Revision 1 supersedes the design content only. No repository history has yet
been committed.

## Forensic provenance retained

F1:

```text
files = 1543
bytes = 70348665

content manifest SHA-256:
3794cfbe45e3138ce3148450952757f38dcebc9d4f7a7baae655afc32801e18a

metadata manifest SHA-256:
f45b90f1de89f8cfebf6bb3db1f285b66d6b26b11e9edc22a639a8727e19133c

SOURCE_UNCHANGED=True
CLONE_EQUIVALENT=True
```

Historical runtime:

```text
PostgreSQL 18.4
database = flooow
Flyway latest = 029
successful migrations = 29
```

F2B read-only SQL SHA-256:

```text
50366300772DDC3AFCEF1668C8FF039D2D167258166FE38D3CD100FA294F03B8
```

F2B transaction:

```text
REPEATABLE READ
READ ONLY
```

## F2B exact historical evidence

```text
mercado_livre_order_rows      = 85
mercado_livre_distinct_orders = 33

omie_transaction_rows         = 400
omie_distinct_orders          = 135

omie_product_cost_rows        = 2009

marketplace_identity_rows     = 12
revenue_promotion_rows        = 21

financial_ledger_rows         = 0
economic_component_rows       = 12
```

Real diagnostic pair:

```text
exact bijective pairs = 1
via integration reference = true
via customer reference = true

ACTUAL currency = BRL
Omie currency   = missing

ACTUAL amount = 58.280000
Omie valor_total_pedido = 58.280000

raw diagnostic delta = 0.000000
Omie selected revisions = 1
source status = 60
```

## Corrected evidence interpretation

Revision 0 used language that could be read as proving end-to-end financial
viability.

The adversarial review showed that this was too broad because provider-total
economic comparability remains unresolved.

The admissible boundary is now:

```text
REAL CROSS-SYSTEM PATH VIABILITY = PROVEN

REAL EXPECTED/ACTUAL ECONOMIC BASIS EQUIVALENCE = NOT PROVEN

REAL END-TO-END FINANCIAL VIABILITY = NOT YET PROVEN

REAL NON-ZERO FINANCIAL LEAKAGE = NOT PROVEN
```

The 58.28 equality is a diagnostic observation, not economic-basis authority.

## Revision-0 adversarial findings

```text
BLOCKER 1
Omie valor_total_pedido and Mercado Livre total_amount
were not proven economically equivalent.

BLOCKER 2
Stable provider source identity was not separated from
revision-specific canonical fact identity.

BLOCKER 3
Current V032/B3-B materialization deliberately blocks
correction participants.

HIGH 1
Automatic S2 identity lacked a durable connection-scoped
reference binding policy.

HIGH 2
Exact Mercado Livre connection lineage through V022
was not explicit.

HIGH 3
Raw provider sourceFingerprint was insufficient as
the V3 semantic-evidence fingerprint.

HIGH 4
Provider-local lifecycle currentness parsing was
under-specified.

MEDIUM 1
CONFLICT was modeled as a persisted peer decision
instead of a derived resolver state.
```

## Revision-1 dispositions

### Blocker 1 - economic basis

Resolved in design by:

```text
direct totalOrderAmount -> EXPECTED mapping = forbidden

ExpectedSaleBasisPolicy = mandatory before S3

S1 V3 financial decomposition acquisition expanded
to preserve merchandise, discounts, deductions,
freight, insurance, other expenses, relevant tax totals,
and item-level economic evidence
```

No universal formula is asserted.

### Blocker 2 - fact identity

Resolved in design by separating:

```text
stable provider source identity
from
revision-specific semantic fact identity
```

Exact replay must produce the same fact/component IDs.

A later materially changed accepted revision must produce different IDs so V015
can retain distinct superseded/replacement facts.

The exact UUID algorithm remains an S3 pre-implementation gate, not an S1
dependency.

### Blocker 3 - correction materialization

Resolved in design by explicitly limiting current authorization:

```text
canonical SOURCE_CORRECTION may exist in V015

but

current corrected fact
-> NotAuthorized(CORRECTION_MATERIALIZATION_UNSUPPORTED)
```

until a separate governed ledger-correction boundary is designed.

Historical pre-correction ledger lineage remains replayable under current B3-B.

### HIGH 1 - identity binding

Resolved in design by requiring a durable connection-scoped
TransactionIdentityBindingPolicy.

String equality alone cannot establish the policy.

If no trustworthy policy exists, automatic S2 confirmation remains unavailable
and explicit governed confirmation is required.

### HIGH 2 - ML connection lineage

Resolved in design by requiring V022 proof that the selected Mercado Livre
connection durably observed/promoted the same canonical order.

Caller-supplied connection IDs do not count as proof.

### HIGH 3 - V3 semantic fingerprint

Resolved in design by separating:

```text
raw provider sourceFingerprint
from
versioned sourceEvidenceSemanticFingerprint
```

Replay validation must cover the complete authority-relevant V3 source
semantics.

### HIGH 4 - lifecycle temporal contract

Resolved in design by freezing:

```text
dd/MM/yyyy + HH:mm:ss
both present -> LocalDateTime
both absent  -> missing
partial pair -> REMOTE_DATA_INVALID

provider revision =
modifiedLocal ?: createdLocal
```

No legacy UTC-midnight `data_previsao` parsing is reusable as V3 lifecycle
authority.

### MEDIUM 1 - conflict model

Resolved in design:

```text
persisted decisions:
CONFIRMED | REJECTED

resolver results:
UNRESOLVED | CONFIRMED | REJECTED | CONFLICT
```

## Revision-1 S1-focused adversarial finding

The Revision-1 structural design was valid, but the S1-focused provider-contract
review found one remaining S1 completeness blocker.

The official Omie order contract exposes additional source evidence that can
change later lifecycle or financial-basis interpretation:

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

det[].inf_adic:
    nao_gerar_financeiro
    nao_somar_total

det[].produto:
    tipo_desconto
    percentual_desconto
```

These fields were not fully preserved by Revision 1.

Because S1 is the evidence-acquisition boundary intended to support later
ExpectedSaleBasisPolicy and lifecycle analysis, implementing V033 without them
would risk requiring another reacquisition generation merely to recover omitted
authority-relevant source evidence.

Disposition:

```text
S1 completeness blocker
    -> resolved in Revision 2 design

financial interpretation
    -> still forbidden in S1
```

Revision 2 adds these fields to the V3 source-evidence and semantic-fingerprint
contract while keeping S2/S3 semantics unchanged.

## Revised TASK-0165S decomposition

```text
S1 / intended V033
lifecycle + origin + financial-basis source evidence

        ↓ S1 field proof

        ├── freeze TransactionIdentityBindingPolicy
        └── freeze ExpectedSaleBasisPolicy

S2 / intended V034
durable governed transaction identity

        ↓ S2 proof

S3 / intended V035
canonical ERP REVENUE
+ exact revision-specific lineage
+ governed SALE / EXPECTED authority
```

## S1-focused second review

The supported Omie `ListarPedidos` response returns the full
`pedido_venda_produto` structure, including `frete`, `det`, `total_pedido` and
`infoCadastro`, so the Revision-1 S1 acquisition target is supported by the
provider contract.

Source-model refinements were added before implementation:

```text
legacy OmieTransactionEvidenceRecord = v0/v1/v2 semantics only
V3 typed record/parser                = capability-specific lifecycle/economic evidence

current product_refs = identifier-oriented diagnostic evidence
V3 financial items   = line-centric economic evidence
```

One provider line may expose multiple identifiers; identifier fan-out must not
duplicate quantity or money. Historical `product_refs` keeps its existing
meaning. V3 also must not inherit legacy `occurredAt` UTC semantics. V033 therefore
needs a dedicated V3 typed record/parser, dedicated item-line representation and a
mandatory V3 semantic-evidence fingerprint while keeping historical rows untouched.

## S1 scope after Revision 1

S1 is still acquisition only.

It may become technically selectable only after a fresh adversarial review
confirms that no unresolved blocker applies to the S1 source-evidence boundary.

S1 must not implement:

```text
ExpectedSaleBasisPolicy formula
S2 transaction decisions
S3 canonical REVENUE
ledger entries
C2
reconciliation
Decision Room production authority
```

## S2 hold

S2 remains HOLD until:

```text
S1 real-data gate passes
TransactionIdentityBindingPolicy is frozen
V022 connection-lineage query semantics are frozen
S2 decision/supersession persistence is reviewed
```

## S3 hold

S3 remains HOLD until:

```text
S2 governed identity passes
ExpectedSaleBasisPolicy is frozen
revision-specific fact identity algorithm/version is frozen
correction-materialization limitation is enforced
exact V035 lineage schema is reviewed
```

## Official roadmap boundary

This revision does not modify the official roadmap.

It does not import Sierra/commercial monetization research.

Discovery does not become official scope automatically.

## Current HOLD state

```text
ADR-0082 Revision 2 = PROPOSED
SPEC-0082 Revision 2 = DRAFT

S1 implementation = HOLD pending Revision-2 adversarial review
S2 implementation = HOLD
S3 implementation = HOLD

C2 implementation = HOLD
ledger materialization runtime activation = HOLD
ledger correction materialization = NOT AUTHORIZED
real reconciliation slice = HOLD
Decision Room production activation = HOLD
```

## Files authorized by this revision

Exactly:

```text
docs/adr/ADR-0082-governed-omie-sale-expected-authority.md
docs/specifications/SPEC-0082-governed-omie-sale-expected-authority.md
docs/evidence/TASK-0165S-governed-omie-sale-expected-authority-design.md
```

No source code, migration, API, OpenAPI, build, journal or roadmap file is
authorized by Revision 1.
