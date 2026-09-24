# Fiscal Intelligence: Jurisdictional Architecture

Status: **STRATEGIC RESEARCH — NOT AUTHORIZED FOR IMPLEMENTATION**

Position: **BRAZIL-FIRST — INTERNATIONAL-READY**

## Purpose

FLOOOW should build fiscal intelligence deeply for Brazil without embedding Brazil-specific law, terminology, or tax treatment in universal economic truth. This document preserves the boundaries for future research and design. It creates no Kotlin contract, migration, policy, calculation, provider integration, authority, or execution scope.

```text
BRAZIL-FIRST != BRAZIL-HARDCODED
COUNTRY RULE != CORE ECONOMIC TRUTH
LEGAL/TAX INTERPRETATION != OBSERVED FACT
TAX RULESET IS VERSIONED AND TEMPORAL
MISSING != ZERO
UNKNOWN TAX TREATMENT != ZERO TAX
FX CONVERSION != ORIGINAL ECONOMIC FACT
```

## Universal economic layer

The following concepts are jurisdiction-independent institutional primitives:

- exact money and currency;
- revenue, contribution, economic margin, GMV concentration, and SKU economics;
- evidence, provenance, temporal validity, freshness, and contradiction;
- scenario, assumptions, uncertainty, and recommendation;
- authority, execution, outcome, and lineage.

They must not depend on Simples Nacional, Lucro Presumido, Lucro Real, CBS, IBS, VAT, GST, sales tax, or any national tax regime. A tax interpretation can inform an economic scenario; it cannot redefine an observed commercial or financial fact.

## Jurisdiction-specific layer

Fiscal treatment belongs in explicitly local, evidence-bound context. Candidate local concepts include:

- entity tax regime and taxpayer status;
- tax registrations;
- product or service classification;
- transaction jurisdiction and transaction-specific applicability;
- relevant counterparty tax status;
- exemptions, credits, rates, effective periods, and filing concepts;
- country, state, province, and municipality rules;
- official references and their provenance.

Brazil is the first implementation jurisdiction, not the universal model.

## Candidate fiscal context evidence

`FiscalContextEvidence` is a candidate concept only; its contract is **UNFROZEN**. A future evidence record may need:

```text
jurisdiction
legalEntityIdentity
taxpayerStatus
entityTaxRegime
transactionJurisdiction
productServiceClassification
counterpartyTaxStatus
operationType
rulesetRevision
effectivePeriod
sourceAuthority
provenance
observedAt
validFrom
validTo
freshness
contradictionState
```

Fiscality has two irreducible contexts.

At entity level: regime, taxpayer status, revenue threshold, registrations, and organization eligibility.

At transaction/product level: classification, jurisdiction, origin/destination, counterparty, and transaction applicability.

It must never be reduced to `organization.taxRegime` as the sole truth.

## Governed tax treatment

A future governed evaluation may follow this conceptual flow:

```text
FiscalContextEvidence
+ transaction evidence
+ classification evidence
+ official fiscal references
+ applicable ruleset revision
        |
        v
Governed Tax Treatment Evaluation
        |
        +-> current interpretation
        +-> projected scenario
        +-> simulated alternative
```

This is not a formula or an implementation authorization. An interpretation remains distinct from observed evidence and from core Economic Truth.

## Rulesets are temporal

A tax rule is never a code constant. A candidate identity for a governed ruleset revision is:

```text
jurisdiction
rulesetRevision
effectiveFrom
effectiveTo
sourceAuthority
sourceRevision
acquiredAt
validatedAt
```

A legal change creates a new revision. Historical interpretations must not be silently rewritten under a later revision.

## Money, currency, and valuation

```text
Money != number
Money = amount + currency
FX conversion != original economic fact
```

For example:

```text
OBSERVED       USD 100.00
VALUATION      BRL 532.80
FX RATE        5.328
FX SOURCE      <governed source>
FX OBSERVED_AT <timestamp>
```

The BRL valuation is a separately governed valuation and does not replace the original USD economic fact.

## Brazil-first sequence

The future conceptual sequence is:

```text
universal economic layer
→ fiscal context contract
→ Brazil official fiscal references
→ Brazil taxpayer/entity context
→ Brazil classification evidence
→ contradiction/adjudication
→ Brazil governed tax-treatment policy
→ isolated calculation proofs
→ economic scenario interpretation
→ Fiscal / Finance Decision Rooms
```

This is not the current critical path.

`ExpectedSaleBasisPolicy = UNFROZEN`

This research does not freeze Simples, Presumido, Lucro Real, CBS/IBS, tax credits, NCM/CNAE/CEST treatment, VAT, sales-tax abstractions, or a global tax interface.

## International expansion discipline

FLOOOW will:

1. Build Brazil deeply.
2. Keep universal and jurisdictional boundaries explicit.
3. Prove the product and evidence model in Brazil.
4. Select a second jurisdiction from commercial evidence.
5. Reconcile abstractions through **ADOPT / ADAPT / REJECT**.
6. Generalize only where the second jurisdiction proves an abstraction is real.

No Mexico, United States, Europe, or other jurisdiction is being implemented now. FLOOOW should not create a speculative worldwide tax engine.

The second jurisdiction is an **architectural validation event**. It must answer which Brazil-derived abstractions were universal, which need adaptation, and which must be rejected as global abstractions.

> Build Brazil deeply. Design the boundaries globally. Generalize only when a second jurisdiction provides evidence that the abstraction is real.

> FLOOOW internationalization must mean jurisdiction-aware institutional intelligence, not translating Brazilian screens into another language.

## Decision Rooms

The interaction model in [Decision Rooms Experience Horizon](../roadmap/FLOOOW-DECISION-ROOMS-EXPERIENCE-HORIZON.md) remains universal:

```text
What is observed?
What is projected?
What is simulated?
Which assumptions apply?
What evidence is missing?
What is the economic impact?
What is uncertain?
Who has authority?
```

Fiscal content changes by jurisdiction; the structure of a governed decision does not. A room may present fiscal interpretation and scenarios, but cannot convert them into observed truth, authority, or execution.

## Relation to fiscal-reference evidence

This direction belongs to the existing lane:

`P1 - Fiscal reference and product classification evidence`

Its required distinctions remain:

```text
official fiscal reference != product classification
product classification != tax treatment
tax treatment != economic truth
tax scenario != authority
```

No production interface such as `TaxRegimePolicyProvider` is created or named as frozen. A future fiscal-evaluation boundary may be justified through evidence, but its interface name and shape remain **UNFROZEN**.

## Research exit criteria

Before implementation, FLOOOW needs separately governed evidence for the applicable jurisdiction, entity and transaction context, official references, ruleset revisions, calculation policy, uncertainty, authority boundaries, and isolated calculation proofs. Research must not become executable architecture prematurely.