# Fiscal custody research - supplier / seller / 3PL stock flow in Sao Paulo

Status: RESEARCH INPUT - NOT AUTHORIZED FOR AUTOMATION

Captured: 2026-09-06

Source class: specialist guidance obtained during the former MGI design work.

Validation status: NOT independently validated by Flooow Genesis.

## Purpose

Preserve an externally supplied fiscal-operational interpretation for the
scenario in which merchandise is physically held by a third-party logistics
operator while commercial ownership/invoicing flows among supplier/importer,
online seller, logistics operator, and final customer.

This document is knowledge input.

It is not tax advice, an accepted tax engine rule, an ADR, a fiscal policy, or
authorization for automatic invoice/CFOP generation.

Before production use, every rule must be revalidated with qualified Brazilian
tax/accounting counsel for the actual:

- legal entities involved;
- CPF/CNPJ configuration;
- state of origin and destination;
- ICMS taxpayer status;
- Simples Nacional / Lucro Presumido / Lucro Real regime;
- IPI status;
- product NCM and tax treatment;
- warehouse/deposit legal characterization;
- import structure;
- seller/customer profile;
- invoice purpose;
- current legislation and state-specific rules.

## Operational scenario

The original business problem involved:

```text
supplier / importer
        |
        | merchandise movement
        v
third-party logistics warehouse
        |
        | custody / storage / fulfillment
        v
online seller commercial flow
        |
        | sale
        v
final customer
```

A key characteristic is that the merchandise may remain physically in the
logistics operator's warehouse while ownership, commercial invoicing, fiscal
documents, and final fulfillment involve different legal participants.

This creates several distinct realities that Flooow must never collapse into one
event:

- physical custody;
- legal/fiscal ownership;
- commercial purchase/sale;
- storage remittance;
- storage return;
- delivery on behalf of another party;
- tax-bearing invoice;
- non-tax-bearing movement document;
- service billing by the logistics operator.

## Specialist guidance captured verbatim in substance

The specialist guidance supplied during the former MGI work was:

### 1. Storage remittance - supplier to logistics warehouse

Nature:

```text
Remessa Armazenagem
```

Suggested CFOP:

```text
5905 - within Sao Paulo
6905 - interstate
```

Guidance received:

- without ICMS;
- without IPI.

### 2. Storage return - logistics warehouse to supplier

Nature:

```text
Retorno Armazenagem
```

Suggested CFOP:

```text
5907 - within Sao Paulo
6907 - interstate
```

Guidance received:

- without ICMS;
- without IPI.

### 3. Online seller purchase - supplier to online seller

Nature:

```text
Compra Lojista Online
```

Suggested CFOP:

```text
5105
```

Guidance received:

- with ICMS;
- with IPI where applicable.

### 4. Storage and delivery - logistics warehouse to online seller

Nature:

```text
Armazenagem e Entrega
```

Suggested CFOP:

```text
5923 - within Sao Paulo
6923 - interstate
```

Guidance received:

- without ICMS.

### 5. Online seller sale to final customer

Suggested CFOP guidance captured:

```text
5102 / 6102 - sale to legal entity (PJ)
5102 / 6108 - sale to individual (PF)
```

Guidance received:

- ICMS according to the seller's tax regime.

### 6. Logistics operator service invoice

Guidance received:

The logistics operator issues a service invoice for activities such as:

- storage;
- administration of receivables / intermediation.

The exact municipal service classification, ISS treatment, service code, and
invoice semantics were not supplied in the captured note and remain unresolved.

## Cost formation observation

The specialist also highlighted an economic consequence:

The storage-remittance invoice from supplier to warehouse was described as not
carrying ICMS/IPI, while the later supplier sale invoice to the seller may carry
those taxes.

The operational recommendation was therefore to ensure the commercial/economic
product cost anticipates applicable tax burden that appears on the later sale to
the seller, rather than interpreting the tax-free remittance document as the
seller's final acquisition cost.

This is an important Flooow distinction:

```text
movement-document value
!=
commercial acquisition cost
!=
tax-inclusive landed/acquisition economics
```

Genesis must not infer product cost solely from the amount/tax treatment of a
storage-remittance document.

## What this means architecturally

This research strengthens several existing Flooow boundaries.

### Custody is not ownership

Physical stock at the 3PL must be modeled separately from:

- ownership;
- fiscal title;
- commercial seller;
- fulfillment responsibility.

A logistics operator reporting physical inventory must not automatically become
the economic owner of that stock.

### Fiscal movement is not economic sale

A storage remittance/return document may describe physical/legal movement without
representing revenue, COGS recognition, or the seller's commercial acquisition.

Therefore:

```text
fiscal document
+ purpose / nature
+ participants
+ tax treatment
+ custody movement
```

must be interpreted before economic meaning is assigned.

### Source invoice is evidence

CFOP, invoice purpose, tax bases, tax totals, issuer, recipient, and referenced
documents should enter Flooow as source evidence.

They must not become canonical fiscal meaning merely because a provider returned
a code.

### Tax rule must be contextual and versioned

Future fiscal policy cannot be:

```text
if CFOP == 5905 then always X
```

It must consider at least:

- origin/destination UF;
- participant role;
- taxpayer status;
- tax regime;
- product tax classification;
- date/effective legislation;
- operation purpose;
- referenced documents;
- warehouse/deposit legal status.

### Fiscal truth and economic truth interact but remain distinct

A tax-bearing commercial purchase may change economic cost.

A tax-free storage remittance should not silently change commercial acquisition
cost.

Future Flooow reconciliation should be able to trace:

```text
physical movement
-> fiscal document
-> commercial document
-> tax evidence
-> expected economic component
-> actual financial settlement
-> reconciliation
```

without collapsing those layers.

## Areas affected

### Fiscal / accounting

Future capability requirements:

- invoice purpose/nature evidence;
- CFOP evidence;
- issuer/recipient roles;
- referenced-document chain;
- tax-base/tax-total evidence;
- regime/UF effective context;
- fiscal-document relationship graph.

### Finance / economic truth

Future capability requirements:

- distinguish movement-document value from purchase cost;
- preserve recoverable/non-recoverable tax semantics separately;
- reconcile expected acquisition economics with actual supplier invoice;
- prevent storage-remittance values from becoming canonical COGS by accident.

### Operations

Future capability requirements:

- physical custody location;
- stock owner;
- fulfillment responsible party;
- remittance/return state;
- expected fiscal document for each physical transition;
- contradiction when inventory moves without the expected document chain.

### 3PL / logistics operator

Future capability requirements:

- custody acknowledgement;
- receipt/dispatch evidence;
- relationship to remittance/return/delivery documents;
- service billing separated from merchandise economics;
- explicit liability/authority boundaries.

## Candidate future contradiction examples

This research suggests useful future contradiction detection:

```text
physical stock at 3PL
but no active custody/remittance evidence
```

```text
storage-remittance invoice
incorrectly treated as seller purchase/COGS
```

```text
supplier commercial invoice exists
but expected storage/delivery document chain is incomplete
```

```text
final sale occurred
but inventory custody/handoff evidence remains unresolved
```

```text
tax-bearing purchase invoice
but economic cost projection still reflects tax-free remittance value
```

```text
3PL service charge
mixed into merchandise cost without explicit allocation policy
```

These are research hypotheses only and require separately governed contracts.

## Questions that must be resolved before automation

1. Are the listed CFOPs still correct for the exact legal arrangement currently
   intended?
2. Does the warehouse legally qualify for the assumed deposit/storage treatment?
3. How do rules change when participants are in different UFs?
4. What changes for Simples Nacional versus other tax regimes?
5. When is IPI applicable, suspended, excluded, or included?
6. What is the correct treatment for importer-owned versus supplier-owned stock?
7. Which taxes are recoverable credits for each participant?
8. How should ICMS-ST, DIFAL, FCP, PIS/COFINS, import taxes, and other product-
   specific regimes interact with the flow?
9. Which document references/chaves de acesso must connect remittance, return,
   commercial invoice, delivery, and final sale?
10. Which participant is legally authorized/obligated to issue each document?
11. Which municipal service code and ISS treatment applies to the 3PL service?
12. Does "administracao do recebivel/intermediacao" describe the actual contracted
    service or a separate legal service relationship?

## Governance decision

Preserve this scenario now as research evidence.

Do not:

- hard-code the CFOP list;
- create automatic fiscal issuance;
- alter canonical Economic Truth from this note;
- infer tax from warehouse movement alone;
- infer ownership from custody;
- port former MGI fiscal assumptions directly into production.

Revisit this research when Flooow begins one of:

- Omie fiscal invoice ingestion;
- fiscal reconciliation;
- supplier purchase/acquisition economics;
- 3PL custody/fulfillment contracts;
- landed-cost modeling;
- automated fiscal decision support;
- contradiction detection spanning fiscal and physical flows.

At that point the guidance must be validated against current authoritative tax
sources and qualified accounting/legal review before any normative SPEC/ADR.