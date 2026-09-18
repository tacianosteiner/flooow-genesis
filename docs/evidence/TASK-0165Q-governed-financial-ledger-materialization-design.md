# TASK-0165Q: Governed Financial Ledger Materialization Design

Status: DESIGN READY FOR AUDIT

Date: 2026-09-13

## Purpose

Close the semantic design gap between durable canonical marketplace evidence and
the existing immutable Financial Ledger without implementing production behavior.

## Starting point

TASK-0165P currently provides:

```text
existing FinancialTrace
  -> authenticated reconciliation runtime
  -> durable explicit policy authority
  -> deterministic assessment
  -> internally owned assessment fingerprint
  -> exact snapshot
  -> atomic reconciliation case revision + exact lineage
```

The runtime is no longer the principal blocker for field proof.

The upstream FinancialTrace materialization contract is.

## Repository findings

ADR-0021 / SPEC-0021 require normalized ledger callers to provide explicit:

```text
stage
EXPECTED or ACTUAL basis
direction
magnitude
source
occurredAt
```

The current MarketplaceIndependentEconomicEvidence and EconomicComponent
contracts do not contain FinancialLedgerBasis.

They contain EconomicEvidenceQuality, but quality and basis are different
semantics.

ADR-0021 explicitly states that no live order reaches the ledger until an
ingestion contract is accepted.

ADR-0022 / SPEC-0022 intentionally assume expected and actual facts already exist
at controlled stages before reconciliation compares them.

ADR-0048 / SPEC-0047 prohibit manufacturing economic meaning from absence,
software capability, timestamps, collection attempts, or projection state.

## Design conclusion

Direct:

```text
MarketplaceIndependentEconomicEvidence
    -> FinancialLedgerEntryDraft
```

is rejected.

The accepted proposed path is:

```text
source evidence
    -> explicit financial materialization authority
    -> governed materialization
    -> immutable Financial Ledger
```

## Critical semantic gap

The missing semantic field is not amount.

The key missing authority is:

```text
FinancialLedgerBasis
```

Stage also requires controlled compatibility.

For current EconomicComponent, type-to-stage compatibility can be frozen
explicitly, but this does not infer basis.

## Rejected shortcuts

The design rejects:

```text
CONFIRMED == ACTUAL
ESTIMATED == EXPECTED
MARKETPLACE == ACTUAL
ERP == ACTUAL
CALCULATED == EXPECTED
provider event == ACTUAL
same amount == same stage
Economic Truth result == ledger row
missing evidence == zero
```

## Settlement boundary

SETTLEMENT, PAYMENT_ACCOUNT, and BANK require dedicated accepted financial
occurrence authority.

They cannot be synthesized from EconomicComponent or Economic Truth results.

## Correction requirement

Source correction must become immutable ledger correction.

No history rewrite is permitted.

Basis or stage change is semantic reclassification and is not an ordinary
correction.

## Persistence requirement

A future implementation requires durable source-authority-to-ledger-entry lineage
and atomic/idempotent commit semantics.

No migration is introduced in this design checkpoint.

## Field-proof relevance

After this boundary is implemented and one or more provider-specific financial
authorities are accepted, a real pilot may exercise:

```text
seller/importer
  -> provider evidence
  -> governed ledger facts
  -> FinancialTrace
  -> reconciliation
  -> divergence
  -> human decision
  -> economic result verification
```

The system must not claim field proof before those provider facts actually reach
the ledger under accepted semantics.

## Design audit hardening

The first design audit identified and closed four ambiguities before production
implementation:

1. exact source identity is now mandatory through a versioned canonical source
   fingerprint rather than observation identifier alone;
2. EconomicComponent stage is derived exclusively from controlled component
   compatibility and cannot be selected by authority;
3. authority absence versus operational authority failure is represented as a
   typed decision rather than null/default inference;
4. sourceAuthoritySemanticVersion is explicitly distinct from
   MarketplaceEconomicEvidenceVersion and aggregate change sequence.

B3-A must therefore implement only the pure fingerprint, authority-decision,
and compatibility boundary with known-answer/adversarial tests.

## Final ownership hardening

A second adversarial design audit closed four additional ownership ambiguities:

1. `expectedSourceFingerprint` is only an authority claim; the governed
   boundary recomputes the fingerprint internally before trusting it;
2. EconomicComponent `sourceAuthorityIdentity` is exactly the observationId,
   preventing multiple authority identities for one source observation;
3. the source observation exclusively owns tenant and subject context; component
   authority contains no duplicate subject fields;
4. source-authority semantic-version grammar and fingerprint enum literals are
   frozen explicitly for Version 1.

B3-A does not materialize correction chains. Correction-to-ledger lineage remains
blocked until B3-B defines and proves durable source-to-entry lineage.

No persistence, provider-specific basis rule, live-pipeline wiring, or public API
is authorized by this hardening.

## Design package

- ADR-0080-governed-financial-ledger-materialization-boundary.md
- SPEC-0080-governed-financial-ledger-materialization-boundary.md
- this evidence record

## Implementation authorization

None.

After design audit, the next proposed slice is:

```text
TASK-0165Q / 4C-B3-A
pure source fingerprint + authority decision + controlled compatibility boundary
```

No persistence and no provider-specific mapping should be implemented until that
slice is separately reviewed.
