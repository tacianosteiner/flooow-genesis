# SPEC-0080: Governed Financial Ledger Materialization Boundary

Status: Proposed

Date: 2026-09-13

Source decision: ADR-0080

## Objective

Define the minimum semantic contract required to turn explicitly authorized
financial source facts into immutable Financial Ledger entries without inferring
FinancialLedgerBasis, fabricating stage meaning, or weakening source provenance.

This is a design contract only.

## Governing chain

```text
accepted source evidence
    -> financial semantic authority
    -> governed materialization
    -> MarketplaceFinancialLedgerRepository
    -> FinancialTrace
```

Reconciliation remains downstream:

```text
FinancialTrace
    -> durable reconciliation policy
    -> MarketplaceFinancialReconciliation
```

## Materialization policy version

Introduce conceptually:

```text
FinancialLedgerMaterializationPolicyVersion
```

Version 1 is:

```text
marketplace-financial-ledger-materialization/1
```

The version freezes materialization semantics.

It is not:

- the Economic Truth assembly policy;
- the Economic Truth calculator policy;
- the Financial Reconciliation tolerance policy.

## Source authority

One materializable EconomicComponent must be presented as one exact canonical
component observation plus an explicit authority decision.

The source observation supplies the complete immutable economic payload:

```text
observationId
subject:
  organizationId
  orderId
  marketplace
  externalOrderId
  currency
family
component:
  componentId
  componentType
  direction
  magnitude
  source
  occurredAt
  evidenceQuality
coverageClaim
observedAt
```

An AUTHORIZED component decision binds that exact source to:

```text
sourceAuthorityIdentity = observationId
sourceAuthoritySemanticVersion
materializationPolicyVersion
expectedSourceFingerprint
basis
```

`expectedSourceFingerprint` is an authority claim, not verified truth.

The governed materialization boundary recomputes the source fingerprint
internally from the exact source observation and requires equality with
`expectedSourceFingerprint` before accepting the authority.

The source observation exclusively owns subject context:

```text
organizationId
orderId
marketplace
externalOrderId
currency
```

A component authority does not repeat or override any subject field.

For an EconomicComponent, stage is not authority-selectable. The materializer
derives stage only from the Version 1 compatibility table.

The materializer may not supply a missing field by heuristic.

`sourceAuthoritySemanticVersion` is the version of the semantic contract that
authorizes the financial basis classification. It is explicitly not
MarketplaceEconomicEvidenceVersion, a repository revision, aggregate evidence
sequence, provider cursor, or ingestion progress version.

Version 1 semantic-version text is canonical ASCII matching exactly:

```text
[a-z0-9][a-z0-9./-]{0,63}
```

The value names the accepted basis-authority semantic contract. It is not
generated from observation time, provider cursor, aggregate revision, or
repository state.

Unrelated changes to the evidence aggregate must not change this semantic
version or create a new materialization identity.

## Authority decision

The pure boundary consumes a typed decision:

```text
sealed interface FinancialLedgerMaterializationAuthorityDecision

Authorized(
    authority
)

NotAuthorized(
    reason
)

IntegrityFailure

Unavailable
```

`NotAuthorized` is semantic and causes no trace opening or ledger mutation.

`Unavailable` is operational and must remain distinct from semantic absence.

Version 1 includes at least:

```text
BASIS_AUTHORITY_UNAVAILABLE
FINANCIAL_OCCURRENCE_AUTHORITY_UNAVAILABLE
```

as semantic non-authorization reasons.

Provider-specific authority resolution is deferred to 4C-B3-C. B3-A defines
only the provider-neutral decision and verification boundary.

## Basis is mandatory

FinancialLedgerBasis is mandatory semantic authority.

Version 1 has no default basis.

The following are explicitly invalid derivations:

```text
CONFIRMED -> ACTUAL
ESTIMATED -> EXPECTED
MARKETPLACE -> ACTUAL
ERP -> ACTUAL
MANUAL -> EXPECTED
CALCULATED -> EXPECTED
```

Likewise:

```text
component coverage -> basis
source family -> basis
provider capability -> basis
projection status -> basis
```

is forbidden.

## Economic component compatibility

For an authorized existing EconomicComponent, Version 1 recognizes the following
stage compatibility:

| EconomicComponentType | FinancialLedgerStage |
| --- | --- |
| REVENUE | SALE |
| MARKETPLACE_COMMISSION | MARKETPLACE_COMMISSION |
| MARKETPLACE_FEE | MARKETPLACE_FEE |
| SHIPPING | SHIPPING |
| ADVERTISING | ADVERTISING |
| TAX | TAX |
| PRODUCT_COST | PRODUCT_COST |
| FINANCIAL_COST | FINANCIAL_COST |
| OTHER_ADJUSTMENT | OTHER_ADJUSTMENT |

This table does not create basis authority.

For EconomicComponent materialization, this table is the only stage authority.
Provider adapters, authority resolvers, request payloads, source kinds, and
policy callers cannot select another stage.

A component authority therefore carries no independently selectable stage.
Any external or persisted authority material that claims a different stage for
the same component type is INTEGRITY_FAILURE.

It also does not imply that every current EconomicComponent is eligible.

## Unsupported stage derivation

No existing EconomicComponent may produce:

```text
SETTLEMENT
PAYMENT_ACCOUNT
BANK
```

Those stages require dedicated accepted financial-occurrence authority.

No cross-stage derivation is permitted from amount equality, timestamps, or
external references alone.

## Current evidence limitation

The current independent economic-evidence contract does not provide complete
financial occurrence semantics for:

```text
SETTLEMENT
PAYMENT_ACCOUNT
BANK
```

and current accepted Economic Truth assembly semantics do not permit absence to
become zero or NOT_APPLICABLE.

Version 1 materialization therefore remains NOT_ELIGIBLE for those stages until
a separate accepted occurrence contract exists.

## Exact preservation

For a materialized EconomicComponent:

```text
direction  = component.direction
magnitude  = component.magnitude
source     = component.source
occurredAt = component.occurredAt
```

Currency comes from the exact subject/component invariant.

The materializer performs no arithmetic.

## Financial materialization authority

For EconomicComponent materialization, conceptually:

```text
FinancialLedgerComponentMaterializationAuthority(
    sourceAuthorityIdentity,
    sourceAuthoritySemanticVersion,
    materializationPolicyVersion,
    expectedSourceFingerprint,
    basis
)
```

For EconomicComponent Version 1, `sourceAuthorityIdentity` must equal the
observation identifier exactly.

The source observation already supplies the complete economic payload and is
the exclusive owner of organization, order, marketplace, external-order, and
currency context.

The authority supplies only the accepted financial-basis classification,
semantic-contract version, materialization-policy version, and the expected
fingerprint that the governed boundary must independently verify.

Stage is derived by the materializer from component type and is not present as a
caller-selectable component-authority field.

Dedicated future financial-occurrence authorities for SETTLEMENT,
PAYMENT_ACCOUNT, and BANK are separate types and may explicitly carry stage.

The implementation type names may differ.

## Authority identity

A source authority identity must be immutable and replay-stable.

For EconomicComponent Version 1, `sourceAuthorityIdentity` is exactly the observationId.

No second authority UUID, random identifier, provider cursor, repository revision,
or aggregate version participates in component source-authority identity.

The same observation identity with different semantic material is an integrity
failure.

A fresh UUID generated during retry is not authority.

## Source fingerprint

Source fingerprint verification is mandatory, not optional.

The governed boundary recomputes the fingerprint internally from the exact
MarketplaceEconomicComponentObservation before trusting an Authorized decision.

The authority may carry only `expectedSourceFingerprint`.

If the internally recomputed fingerprint differs from the expected fingerprint,
the result is INTEGRITY_FAILURE and no materialization output is produced.

Only the internally recomputed and verified fingerprint may flow into future
source-to-ledger lineage.

Introduce conceptually:

```text
FinancialLedgerMaterializationSourceFingerprint(
    canonicalizationVersion = 1,
    sha256
)
```

Version 1 fingerprints the complete accepted
MarketplaceEconomicComponentObservation source meaning.

The canonical payload is exactly:

```text
canonicalizationVersion
observationId
subject:
  organizationId
  orderId
  marketplace
  externalOrderId
  currency
family
component:
  id
  type
  direction
  magnitude:
    currency
    amount
  source:
    kind
    systemKey
    externalReference
  occurredAt
  quality
coverageClaim
observedAt
```

Canonicalization Version 1 rules are:

1. UTF-8, no BOM, no insignificant whitespace, and no trailing newline.
2. Object properties appear exactly in the order listed above.
3. UUID values use canonical lowercase text.
4. MarketplaceMoney uses its existing canonical currency plus canonical
   `amount.toPlainString()` representation.
5. `occurredAt` and `observedAt` use UTC RFC-3339 text with exactly six
   fractional digits and `Z`; existing domain microsecond precision is
   preserved.
6. Enum values use their explicit Version 1 literals, never `toString()`.
7. Existing validated marketplace, external-order, system-key, and external
   reference values are emitted exactly; no case folding or trimming is added.
8. A present external reference is encoded as
   `{state:"PRESENT",value:"..."}`.
9. An absent internal reference is encoded as
   `{state:"ABSENT",reason:"INTERNAL_ORIGIN"}`.
10. JSON string escaping follows standard JSON escaping; property ordering is
    part of Version 1 canonicalization.
11. Version 1 enum literals are frozen explicitly and are never obtained from
    `toString()` or enum ordinal:

```text
MarketplaceEconomicEvidenceFamily:
  MARKETPLACE_ORDER
  MARKETPLACE_PAYMENT
  MARKETPLACE_SHIPPING
  PRODUCT_COST
  FISCAL_INVOICE
  FISCAL_TAX
  ADS_IDENTITY
  ADS_ALLOCATION

EconomicComponentType:
  REVENUE
  MARKETPLACE_COMMISSION
  MARKETPLACE_FEE
  SHIPPING
  ADVERTISING
  TAX
  PRODUCT_COST
  FINANCIAL_COST
  OTHER_ADJUSTMENT

EconomicDirection:
  ADDITION
  DEDUCTION

EconomicEvidenceQuality:
  CONFIRMED
  ESTIMATED

EconomicComponentCoverage accepted by component observation:
  COMPLETE
  PARTIAL

EconomicSourceKind:
  MARKETPLACE
  ERP
  MANUAL
  CALCULATED

EconomicExternalReferenceState:
  PRESENT
  ABSENT

EconomicExternalReferenceAbsenceReason:
  INTERNAL_ORIGIN
```

Any future enum addition or literal change is unsupported by canonicalization
Version 1 until a new accepted canonicalization version explicitly defines it.

The source fingerprint includes evidence quality, coverage claim, family,
observation time, marketplace, and external order even though not every field is
copied into the ledger. The fingerprint proves exact source identity rather
than merely ledger-equivalent material.

The fingerprint excludes:

```text
MarketplaceEconomicEvidenceVersion
aggregate change sequence
other facts
collection attempts
corrections unrelated to this observation
database timestamps
trace id
ledger entry id
materialization outcome
```

The same `sourceAuthorityIdentity` or observation identity with a different
fingerprint is INTEGRITY_FAILURE.

B3-A must include deterministic known-answer tests for canonicalization Version
1 before any durable lineage is implemented.

## Trace identity and opening

Materialization first resolves the FinancialTrace for:

```text
organizationId + orderId
```

If absent, it may open exactly one trace using exact subject context:

```text
organizationId
orderId
marketplace
externalOrderId
currency
```

If another trace already exists for that order, its complete context must equal
the source subject.

Context mismatch is INTEGRITY_FAILURE.

## No empty trace creation

NOT_ELIGIBLE evidence does not cause trace creation.

A trace is created only while committing the first eligible materialization.

## Source-to-entry lineage

Every successful materialization must durably bind:

```text
organization
source authority identity
source fingerprint canonicalization version
source fingerprint sha256
source semantic version
materialization policy version
derived stage
basis
traceId
ledgerEntryId
```

The binding is immutable.

Its physical PostgreSQL representation belongs to a later implementation slice.

## Atomicity

For the first materialization of a source authority:

```text
ensure/open trace
append ledger entry
persist source-to-entry lineage
```

must become one authoritative transaction boundary or an equivalently safe
idempotent protocol proving that a source cannot be reported materialized without
its ledger entry.

A lineage row without the corresponding verified ledger entry is integrity
failure.

An unbound ledger entry must not be retrospectively claimed by source identity.

## Exact replay

When the exact same verified source authority is seen again:

```text
-> ALREADY_MATERIALIZED
```

The ledger remains unchanged.

Replay must return the original trace and entry identity internally.

## Conflicting replay

The same source authority identity with a different verified source
fingerprint is INTEGRITY_FAILURE.

The same verified source identity and fingerprint with a different basis,
derived stage, source-authority semantic version, or materialization policy
meaning is semantic reclassification and is not an exact replay.

Version 1 rejects that state as INTEGRITY_FAILURE rather than appending another
entry.

It must never append another entry.

## Source correction

When canonical source evidence explicitly supersedes an already-materialized
source fact, a replacement materialization may append:

```text
new FinancialLedgerEntryDraft(
    ...
    correctsEntryId = previousLedgerEntryId
)
```

The original ledger entry remains immutable.

Correction lineage must prove the source supersession relationship.

## Same stage and basis correction rule

Ordinary source correction requires:

```text
replacement.stage == previous.stage
replacement.basis == previous.basis
```

Changing stage or basis is semantic reclassification, not correction.

Version 1 does not authorize semantic reclassification.

## Economic reversal

A reversal is a new fact.

It has its own source identity and opposite EconomicDirection.

It does not populate correctsEntryId merely because its amount reverses another
entry.

## Materialization results

Conceptually:

```text
sealed interface GovernedFinancialLedgerMaterializationResult

Materialized(
    traceId,
    entryId
)

AlreadyMaterialized(
    traceId,
    entryId
)

NotEligible(
    reasons
)

Failed(
    failure
)
```

Controlled Version 1 NotEligible reasons:

```text
BASIS_AUTHORITY_UNAVAILABLE
UNSUPPORTED_SOURCE_KIND
UNSUPPORTED_FINANCIAL_STAGE
FINANCIAL_OCCURRENCE_AUTHORITY_UNAVAILABLE
```

Controlled failures:

```text
CONFLICT
INTEGRITY_FAILURE
UNAVAILABLE
```

No controlled result exposes source payload, amount, tenant, external reference,
or credential.

## Cross-tenant protection

The organization read from the exact source observation must equal the
operational tenant scope.

Component authority carries no organization field and cannot override tenant
ownership.

Mismatch fails before trace creation or append.

Organization is never accepted from a public materialization request body.

## Interaction with reconciliation endpoint

The endpoint:

```text
POST /v1/reconciliation/traces/{traceId}/execute
```

remains unchanged.

It cannot:

- create arbitrary ledger facts;
- choose stage;
- choose basis;
- choose amount;
- choose source;
- choose policy;
- materialize missing source evidence.

## Live pipeline integration

A future accepted implementation may add a live-pipeline stage after canonical
evidence promotion.

Conceptually:

```text
provider source
  -> durable canonical evidence
  -> governed ledger materialization
  -> reconciliation readiness
```

This SPEC does not authorize that wiring.

## First implementation slices after acceptance

The expected implementation sequence is:

```text
4C-B3-A
  pure source fingerprint + authority decision + compatibility boundary

4C-B3-B
  durable source-to-ledger lineage + atomic/idempotent commit

4C-B3-C
  first provider-specific basis authority after source-contract audit

4C-B3-D
  live pipeline integration and field-proof execution
```

No provider-specific mapping is authorized by B3-A or B3-B.

## Adversarial acceptance criteria

Future tests must prove at least:

1. CONFIRMED evidence cannot become ACTUAL without explicit basis authority.
2. ESTIMATED evidence cannot become EXPECTED without explicit basis authority.
3. source kind cannot select basis.
4. missing basis is a typed NotAuthorized decision, not null/default inference.
5. operational authority unavailability remains distinct from NotAuthorized.
6. valid EconomicComponent preserves amount, direction, source, and occurredAt.
7. component type alone derives its controlled compatible stage.
8. component authority cannot select or override stage.
9. EconomicComponent cannot create SETTLEMENT, PAYMENT_ACCOUNT, or BANK.
10. fingerprint Version 1 has a fixed known-answer digest.
11. changing evidence quality, coverage claim, observedAt, marketplace, or
    externalOrderId changes the source fingerprint.
12. changing only MarketplaceEconomicEvidenceVersion does not change source
    fingerprint or sourceAuthoritySemanticVersion.
13. exact retry is idempotent.
14. same source identity with different fingerprint fails as INTEGRITY_FAILURE.
15. cross-organization source fails before mutation.
16. trace context mismatch fails closed.
17. source correction appends a ledger correction rather than mutating history.
18. semantic basis/stage reclassification is rejected.
19. reversal is not treated as correction.
20. missing evidence does not become zero.
21. failed materialization cannot report success without durable source-to-entry
    lineage.

## Out of scope

This SPEC does not authorize:

- production code in this design checkpoint;
- V032;
- provider-specific basis rules;
- live pipeline mutation;
- automatic reconciliation;
- settlement, payment-account, or bank adapters;
- public materialization API;
- Decision Room changes;
- economic recovery actions;
- AI decisions.

## References

ADR-0021
SPEC-0021
ADR-0022
SPEC-0022
ADR-0048
SPEC-0047
ADR-0080
ADR-0079
SPEC-0079
