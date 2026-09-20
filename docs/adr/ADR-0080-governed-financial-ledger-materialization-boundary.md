# ADR-0080: Governed Financial Ledger Materialization Boundary

Status: Accepted; implementation delivered within bounded scope

Date: 2026-09-13

## Current implementation state - 2026-09-20

This section records current repository reality and has normative precedence
over historical implementation-authorization wording later in this ADR.

The governed Financial Ledger Materialization Boundary has since been
implemented through separately reviewed slices, including:

- the governed materialization boundary;
- durable V032 source-to-ledger lineage;
- atomic PostgreSQL materialization commit;
- replay/idempotency protection;
- runtime processing over durable Economic Evidence.

This does not broaden semantic authority. Provider-specific EXPECTED/ACTUAL
authority, settlement/payment-account/bank authority, automatic reconciliation,
recovery authority, financial action, and AI execution remain separately governed.

Historical statements below saying this ADR did not itself authorize production
Kotlin, V032, or implementation describe the original design checkpoint. Those
implementation gates were subsequently reviewed and completed.

## Context

TASK-0165P has established a productive authenticated path from an existing
durable FinancialTrace through durable policy selection, deterministic
reconciliation, internally accepted assessment identity, atomic case revision
lineage, and the runtime execution endpoint.

The remaining field-proof blocker is upstream:

```text
durable marketplace / ERP economic evidence
    -> ?
    -> FinancialTrace
    -> governed reconciliation
```

The existing Financial Ledger contract deliberately requires a normalized caller
to provide exact:

```text
stage
basis = EXPECTED | ACTUAL
direction
magnitude
source provenance
occurredAt
```

The current generic EconomicComponent contract contains:

```text
component type
direction
magnitude
source
occurredAt
evidence quality = CONFIRMED | ESTIMATED
```

It does not contain FinancialLedgerBasis.

Therefore none of the following equivalences is authorized:

```text
CONFIRMED  != ACTUAL
ESTIMATED  != EXPECTED
MARKETPLACE != ACTUAL
ERP         != ACTUAL
CALCULATED  != EXPECTED
MANUAL      != EXPECTED
```

Likewise, component coverage, insertion order, provider name, amount sign,
projection state, or successful collection cannot create financial basis
authority.

A generic amount is not automatically a Financial Ledger fact.

## Decision

Introduce one governed Financial Ledger Materialization Boundary between accepted
upstream evidence and MarketplaceFinancialLedgerRepository.

The boundary must transform an already-authorized financial semantic assertion
into an immutable ledger append.

It must not infer missing semantics.

Conceptually:

```text
durable source evidence
    -> explicit financial materialization authority
    -> governed materialization
    -> immutable FinancialTrace / ledger entry
    -> governed reconciliation
```

The materialization boundary is separate from:

- Economic Truth assembly;
- Economic Truth calculation;
- Sales Intelligence projection;
- Financial Reconciliation;
- reconciliation case lifecycle;
- Decision Room interpretation.

Each remains sovereign over its existing meaning.

## Primary invariant

```text
Economic evidence does not become financial truth merely because it contains money.
```

A financial ledger entry requires explicit authority for every semantic field
that changes its meaning.

## Financial basis authority

EXPECTED and ACTUAL are financial semantics.

The materializer must never derive FinancialLedgerBasis from:

- EconomicEvidenceQuality;
- EconomicSourceKind;
- evidence family;
- component coverage;
- source-system name;
- marketplace name;
- provider capability;
- monetary sign;
- observation recency;
- current projection state;
- calculator output;
- presence or absence of another fact.

An accepted upstream normalization contract must explicitly establish basis.

If basis authority is absent, materialization is not eligible.

No fallback is permitted.

## Authority resolution

Absence of basis authority and operational failure to resolve authority are
different states.

The conceptual authority decision is:

```text
AUTHORIZED(authority)
NOT_AUTHORIZED(reason)
INTEGRITY_FAILURE
UNAVAILABLE
```

`NOT_AUTHORIZED(BASIS_AUTHORITY_UNAVAILABLE)` is a legitimate semantic outcome
and causes no trace or ledger mutation.

`UNAVAILABLE` means the authority source could not be read or evaluated
reliably. It is not converted into NOT_AUTHORIZED.

The materializer receives an explicit decision. It must not interpret a null,
missing field, source kind, evidence quality, or provider response as an
implicit basis decision.

## Controlled stage compatibility

For an existing canonical EconomicComponent, the only structurally compatible
FinancialLedgerStage mapping is:

```text
REVENUE                 -> SALE
MARKETPLACE_COMMISSION  -> MARKETPLACE_COMMISSION
MARKETPLACE_FEE         -> MARKETPLACE_FEE
SHIPPING                -> SHIPPING
ADVERTISING             -> ADVERTISING
TAX                     -> TAX
PRODUCT_COST            -> PRODUCT_COST
FINANCIAL_COST          -> FINANCIAL_COST
OTHER_ADJUSTMENT        -> OTHER_ADJUSTMENT
```

This table establishes stage compatibility only.

For EconomicComponent materialization, the stage is derived exclusively from
this table. A component financial authority does not select or override stage.

If any resolved authority claims a stage inconsistent with this table, the
boundary treats that state as INTEGRITY_FAILURE rather than honoring the
claimed stage.

Dedicated future financial-occurrence authorities for SETTLEMENT,
PAYMENT_ACCOUNT, and BANK are a separate contract and may carry an explicit
stage because no EconomicComponentType supplies those meanings.

It does not establish:

- EXPECTED or ACTUAL;
- eligibility;
- completeness;
- settlement identity;
- payment identity;
- bank identity;
- matching;
- reconciliation.

A future additional EconomicComponentType or FinancialLedgerStage is unsupported
until an accepted contract changes this mapping explicitly.

## Settlement, payment account, and bank

SETTLEMENT, PAYMENT_ACCOUNT, and BANK are not EconomicComponentType values.

They must never be manufactured from an order component or Economic Truth
calculation.

They require dedicated accepted financial-occurrence authority retaining:

```text
organization and order ownership
financial stage
explicit basis
direction
exact magnitude
currency
source provenance
stable source-fact identity
occurredAt
```

A settlement total cannot be relabeled BANK merely because values are equal.

A payment-account event cannot be relabeled SETTLEMENT merely because it arrived
earlier.

Cross-stage equality provides no identity.

## Economic Truth relationship

MarketplaceEconomicTruthAssembler remains the canonical authority for constructing
MarketplaceOrder from independent economic evidence.

MarketplaceEconomicTruthCalculator remains the canonical Economic Truth
calculator.

Neither output is itself a Financial Ledger entry.

The materializer may preserve an exact EconomicComponent as source evidence when
an accepted financial materialization authority binds that component to a
financial basis.

It must not flatten a MarketplaceEconomicResult into ledger entries.

## Source value preservation

When an existing EconomicComponent is authorized for materialization, the
following values are preserved exactly:

```text
organization
order
direction
magnitude
currency
source
occurredAt
```

No monetary calculation, FX conversion, rounding, sign inversion, amount
allocation, aggregation, or timestamp substitution occurs in the materializer.

The controlled component-type-to-stage table supplies stage compatibility.

Explicit financial authority supplies basis.

## Trace opening

The first eligible financial materialization for a subject may ensure that the
subject has one FinancialTrace.

The trace context must equal the accepted subject exactly:

```text
organization
order
marketplace
external order
currency
```

An existing trace with any different context is an integrity failure.

Trace creation is idempotent and organization-scoped.

A collection attempt, NotReady Economic Truth, or ineligible evidence does not
open a trace by itself.

## Exact source identity binding

Observation identity alone is not sufficient durable proof of source meaning.

For component materialization, the boundary requires a versioned canonical
source fingerprint:

```text
FinancialLedgerMaterializationSourceFingerprint(
    canonicalizationVersion,
    sha256
)
```

Version 1 fingerprints the exact accepted
MarketplaceEconomicComponentObservation semantic payload, including:

```text
observation id
complete subject:
  organization
  order
  marketplace
  external order
  currency
family
component:
  component id
  component type
  direction
  exact money
  source
  occurredAt
  evidence quality
coverage claim
observedAt
```

The fingerprint excludes aggregate evidence version, unrelated facts,
collection attempts, corrections not belonging to this observation, database
timestamps, trace identity, ledger identity, and materialization result.

The same observation identity with a different source fingerprint is
INTEGRITY_FAILURE.

For EconomicComponent Version 1, `sourceAuthorityIdentity` is exactly the
observation identifier. No second authority identifier may be generated.

The authority carries only an `expectedSourceFingerprint`. The governed
materialization boundary recomputes the fingerprint internally from the exact
source observation and rejects any mismatch as INTEGRITY_FAILURE.

The source observation exclusively owns organization, order, marketplace,
external-order, and currency context. Component authority cannot repeat or
override those fields.

`sourceAuthoritySemanticVersion` identifies the semantic contract that
authorized financial basis for this exact source. It is not
MarketplaceEconomicEvidenceVersion, not a repository revision, and not an
aggregate change sequence. Adding unrelated evidence must not change source
authority identity or semantic version.

Its Version 1 text uses canonical ASCII matching
`[a-z0-9][a-z0-9./-]{0,63}`.

The exact canonical encoding and all Version 1 enum literals are frozen by
SPEC-0080 and must have known-answer tests before persistence is introduced.

## Durable source-to-ledger lineage

Materialization must retain a durable binding between the exact accepted source
authority and the resulting ledger entry.

The binding must be sufficient to prove:

```text
which source authority produced this entry
which exact canonical source fingerprint was verified
which source-authority semantic version authorized basis
which semantic materialization contract/version was used
which trace received it
which immutable ledger entry resulted
whether the operation was an exact replay
whether a later source correction superseded the prior source fact
```

The exact physical table and migration are not authorized by this ADR.

## Correction semantics

Upstream source correction must never mutate an existing ledger entry.

When a source fact is explicitly superseded and the replacement remains
financially authorized:

```text
old source fact
    -> old immutable ledger entry

replacement source fact
    -> new immutable ledger correction
       correctsEntryId = old ledger entry
```

The replacement must preserve the same FinancialLedgerStage and
FinancialLedgerBasis as the corrected ledger fact unless a separately governed
semantic reclassification contract exists.

A correction is not an economic reversal.

An economic reversal remains a new economic fact with its own direction and
source provenance.

## Reclassification

Changing the financial meaning of an already-materialized source fact is not an
ordinary correction.

The following changes are semantic reclassification:

```text
EXPECTED -> ACTUAL
ACTUAL -> EXPECTED
one FinancialLedgerStage -> another FinancialLedgerStage
```

They require an explicit separately accepted governance contract.

A materialization policy/version change must not silently rewrite historical
ledger entries.

## Idempotence

Exact retry must not create a second ledger fact.

Materialization identity must be stable from accepted upstream authority, not a
fresh random identifier created on each retry.

The future implementation may use deterministic domain-separated identifiers or
durable source-authority lineage, but identity mechanics must not create new
financial meaning.

## Fail-closed behavior

The boundary must fail closed on:

- cross-organization source context;
- order mismatch;
- marketplace mismatch;
- external-order mismatch;
- currency mismatch;
- missing financial basis authority;
- unsupported stage;
- source authority conflict;
- source payload identity conflict;
- trace-context mismatch;
- invalid correction lineage;
- semantic reclassification without explicit authority;
- persistence integrity failure.

No failure path may invent zero, basis, stage, provenance, or timestamp.

## Controlled outcomes

The conceptual boundary distinguishes:

```text
MATERIALIZED
ALREADY_MATERIALIZED
NOT_ELIGIBLE
CONFLICT
INTEGRITY_FAILURE
UNAVAILABLE
```

NOT_ELIGIBLE is a legitimate semantic result and does not mutate the ledger.

Examples include missing basis authority and unsupported financial occurrence
type.

## Tenant isolation

organizationId remains server-owned and durable-source-owned.

A provider payload, HTTP request, query parameter, external reference, or caller
header cannot select another organization.

Cross-tenant reads and writes fail closed.

## Runtime relationship

TASK-0165P 4C-B2-B1 may execute reconciliation only for an existing trace.

This ADR does not change that endpoint.

Future materialization may be triggered by the live pipeline, an internal worker,
or another authenticated operational boundary only after its own implementation
slice is accepted.

The public reconciliation execution endpoint must never accept arbitrary ledger
entries.

## Field-proof consequence

Once productive materialization exists, the field-proof chain can become:

```text
real seller/importer source
    -> durable canonical evidence
    -> governed financial materialization
    -> FinancialTrace
    -> durable reconciliation policy
    -> exact reconciliation assessment
    -> case + exact assessment lineage
    -> Decision Room / operational proof
```

This ADR does not claim that the chain is complete today.

## Explicit non-decisions

This ADR does not yet authorize:

- production Kotlin;
- migration V032 or any migration;
- a new table;
- live-pipeline wiring;
- provider-specific EXPECTED/ACTUAL rules;
- Mercado Livre basis mapping;
- Omie basis mapping;
- settlement ingestion;
- payment-account ingestion;
- bank ingestion;
- automatic reconciliation execution;
- Decision Room changes;
- API changes;
- financial actions;
- recovery workflows;
- AI decisions.

## Consequences

The boundary prevents the final major shortcut that could corrupt Economic Truth:
classifying monetary evidence as expected or actual without semantic authority.

It also makes the remaining field-proof work explicit rather than hiding it in a
provider adapter.

## References

- ADR-0021: Marketplace Financial Trace and Economic Ledger Boundary
- SPEC-0021: Marketplace Financial Trace and Economic Ledger
- ADR-0022: Marketplace Financial Reconciliation Boundary
- SPEC-0022: Marketplace Financial Reconciliation
- ADR-0048: Canonical Economic Truth Assembly Semantics
- SPEC-0047: Canonical Economic Truth Assembly
- ADR-0079 / SPEC-0079: Reconciliation Assessment Identity and Revision Lineage
- TASK-0165P

## Authorization

If accepted after audit, this ADR authorizes drafting and reviewing the bounded
SPEC-0080 contract contained in the same design package.

It does not authorize production implementation.
