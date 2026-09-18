# ADR-0082 - Governed Omie SALE / EXPECTED Authority

Status: Proposed

Revision: 9

Date: 2026-09-18

## Revision-9 authoritative S2 decomposition

Current migration allocation: V033 is Omie V3 source evidence; V034 is the
command authorization substrate only. Historical `S2 / V034` and `S3 / V035`
allocations are explicitly SUPERSEDED, not current reservations. S2A writer
uses the next free migration determined from the implementation working tree;
S2B automatic policy and S3 EXPECTED authority use later migrations whose
numbers are not reserved. Preserve historical references as revision evidence.

This section is the current normative precedence over conflicting Revision
5/6/7/8 and older gates. Revision 6 introduced explicit historical identity;
Revision 7 corrected missing current integration reference to neutral for that
path. Revision 8 separated command admission, but left its substrate unfinished
and incorrectly treated missing real grants as a blocker to all engineering.
Revision 9 delegates authorization to dedicated ADR/SPEC-0083 and distinguishes
safe zero-grant infrastructure from operational authority. The R8 permission
names and credential-version-bound grant model are superseded by SPEC-0083.

S2A EXPLICIT GOVERNED IDENTITY = DESIGN FROZEN / implementation candidate after
the dedicated authorization gate. No binding policy is required. S2B AUTOMATIC
POLICY IDENTITY = HOLD; automatic confirmation remains UNAVAILABLE. COMMAND
AUTHORIZATION SUBSTRATE = required dependency, implementable with zero grants.
S1/V033 remains PROVEN. S3/C2 remain HOLD. ExpectedSaleBasisPolicy remains
UNFROZEN / RESEARCH ONLY: economic comparison research is admitted after at
least one field-proven governed CONFIRMED S2A pair, without S2B as a prerequisite.
No financial freeze, economic equivalence or non-zero leakage is proven.

S2A uses only durable historical source evidence, with ACTIVE organization and
server-bound exact provider pair. Suspended/revoked provider connections do not
invalidate durable history; their online credentials/network are not required.
The stable subject is (organizationId, omieConnectionId, sourceOrderReference),
never integration reference, amount, date, SKU, policy or target. The caller
expresses a canonical marketplaceOrderId intent; the server resolves V022
identity/external_order_id, an exact PROMOTED/DUPLICATE V022 promotion and its
exact base V021 source coordinates. No supplied lineage or foreign selectors.

Resolve current V3 for the stable subject using provider modified-local else
created-local, not observation time, no invented timezone. Missing ordering
evidence stays unavailable; maximal contradictory semantic ties conflict.
Current integration reference equal to canonical external_order_id corroborates;
present different value conflicts; missing is neutral only for separately
authorized explicit intent with all other exact durable proof. Older revisions
never substitute for current contradictory/missing evidence. Currency missing
is neutral, present unequal conflicts; monetary equality proves no identity.

One append-only decision universe supports EXPLICIT_CONFIRMATION,
EXPLICIT_REJECTION, CORRECTION and a reserved future POLICY_EXACT_MATCH reason.
The latter must be rejected until a separate accepted S2B implementation exists.
Relation history keys exact stable subject and canonical target; corrections
retain that relation and supersede its current leaf only. Rejected alternatives
may coexist and do not release another relation's confirmation. Changing target
requires explicit correction/rejection of the old confirmed relation before a
new confirmation, never silently changing a stable subject or existing chain.
Across all connection pairs/policies in an organization, at most one current
CONFIRMED target per subject and one current CONFIRMED subject per target.
Stale evidence does not silently release an existing confirmed reservation.

Future identity writers lock the same organization-wide subject and target
resources for explicit/automatic paths. Lock order is organization, stable
principal, sorted identity resources; re-read exact source/currentness and
global leaf cardinality; revalidate dedicated credential and exact permission
inside the same write transaction immediately before immutable insert. Shared
principal lock serializes grant revocation: revocation committed before recheck
denies; decision committed first preserves exact historical authority. Store
principal, credential ID/revision, grant ID/revision, permission and SPEC-0083
semantic version/fingerprint. Corrections need their own currently valid grant.
No public provisioning route and no coarse-bearer fallback.

Adversarial decomposition review: subject/target collision, explicit/automatic
race and correction forks require shared locks plus unique successor constraints;
current contradictory revision vetoes historical confirmation; missing reference
does not fabricate authority; transactional rollback leaves no partial decision;
deadlock retry repeats whole intent, and exact ID replay never rewrites history.
S2A contract has no unresolved authority-integrity HIGH. Identity SQL/writer is
not selected by this revision: its exact schema/locks/tests remain a separate
implementation gate. The closed selectable substrate package is SPEC-0083.

Field proof activation remains blocked by absent legitimate operator/grant.
Use the existing candidate, not a substitute chosen for success; 58.28 is only
diagnostic. Prove current exact grant, V3, V021/V022 lineage, append, cardinality,
replay, immutability and tenant isolation before counting a governed pair. S2B
additionally requires independent POLICY_ADMIN, real temporal policy activation,
policy semantic lineage, automatic races and its own real field proof.

## Revision-5 authoritative identity contract

Revision 5 is a reconstructed documentary correction, not a replay of an
unavailable Revision-5 script. The independently verified baseline is Revision
4. This section supersedes all earlier S2 policy, lineage, currentness,
cardinality, origin, authority and gate-order statements in this document.
Earlier sections remain historical evidence. Their weaker alternatives cannot
be composed with this contract. S1 source parsing and immutable V033 evidence
remain unchanged. No ExpectedSaleBasisPolicy is frozen.

### Authority and scope

The semantic binding mode remains exactly:
`OMIE_INTEGRATION_ORDER_REFERENCE_EQUALS_ML_ORDER_ID`.

Policy scope is `(organizationId, mercadoLivreConnectionId, omieConnectionId,
semanticPolicyVersion)`. It is an authorization scope, not an identity key or
the boundary of the organization-wide cardinality invariant.

An activation command must be authenticated and separately authorized for
policy administration. The server derives organization, principal and selected
connection pair from trusted authenticated configuration/context. Neither a
body-supplied principal nor possession of a diagnostic match is authority.
A generic service bearer does not implicitly authorize policy administration
or explicit transaction confirmation. Any exposed command requires a separately
governed capability check; no new public API is required by this revision.
Administrative authorization and explicit-confirmation authorization are
distinct from source-ingestion permissions.

The policy declaration carries the integration-convention evidence reference,
its fingerprint, administrative authority provenance, reason and correlation
id. Observed equality/frequency, source origin and model prose cannot substitute
for evidence of that convention. Automatic policy creation is prohibited.

### Append-only policy lifecycle

Each policy decision records organization/connection scope, policy decision id,
decision revision, supersedes id, semantic version, semantic fingerprint,
`ENABLED | DISABLED`, server-derived principal, reason, provenance, correlation
id and server decision time. Revision is sequential; semantic version is a
different dimension. Disable/enable events cannot recycle an old activation
epoch. The current leaf is selected by supersession lineage, never maximum
timestamp alone. Forked leaves or unsupported semantics fail closed.

Same-scope predecessor, previous revision + 1, a unique successor per predecessor
and one root per lifecycle chain are mandatory. An exact replay returns the
original stored result; reusing an id/correlation key with changed command
semantics is integrity failure. Replays cannot mint a new decidedAt or principal.
Policy decisions are never updated or deleted.

Automatic decisions require the current policy leaf to be `ENABLED` and cite
that exact decision id, revision, semantic version and recomputed fingerprint.
Policy activation time is server-assigned; callers cannot backdate authority.

### Prospective-only applicability

An automatic decision requires independently established temporal applicability
of the exact provider semantic revision after the current policy activation.
Pre-activation historical evidence is ineligible for automatic confirmation.
Reacquiring old evidence after activation does not make it prospective. Equality
at a boundary with insufficient precision fails closed. A re-enabled or changed
policy needs its own new epoch; an earlier enabled revision does not authorize
new writes while the current policy is disabled.

Omie provider timestamps are civil local timestamps; policy decidedAt is an
instant. `observedAt` proves acquisition provenance, not provider event time.
Comparing these directly, assigning the host timezone, treating a recently
acquired row as a recently changed provider row, or accepting a caller-provided
`prospective=true` assertion is prohibited. Missing independently justified
temporal ordering returns `UNRESOLVED(POLICY_TEMPORAL_APPLICABILITY_UNPROVEN)`.

The reviewed official Omie `infoCadastro` contract describes separate inclusion
and modification date/time fields. That field contract does not establish an
offset/zone or a trusted temporal bridge to policy activation:
[Omie order contract](https://app.omie.com.br/api/v1/produtos/pedido/).
This is an evidence gap, not permission to infer Brazilian/host UTC offsets.
The exact durable temporal-proof representation and admission algorithm remain
an explicit pre-implementation gate. Until that gate closes, automatic policy
activation/applicability is not implementation-ready. The real historical
candidate may use only a separately governed explicit-confirmation path.

### Stable subject and decision chain

The Omie subject key is exactly
`(organizationId, omieConnectionId, sourceOrderReference)`.
It remains stable when integrationOrderReference, amounts, policy, ML target or
provider revision changes. `integrationOrderReference` is revision material.
Neither policy scope nor marketplace target belongs in the decision-chain key.

One append-only decision chain exists per stable subject. Successors preserve
that subject, use previous revision + 1 and explicitly name the current leaf.
A target change requires an authorized `CORRECTION` superseding the prior leaf,
not a second independent chain. Multiple leaves are an integrity contradiction.
A superseded decision cannot be resurrected as current after later evidence
becomes inconvenient or unavailable.

### Current accepted V3

Use only accepted, durably committed V3 base + sidecar + exact source coordinates
for the selected organization and Omie connection. Missing sidecar/base lineage,
unsupported fingerprint version or a recomputation mismatch is integrity failure.
V0/V1/V2 are not a fallback. V3 is source evidence, not a financial authority.

For each stable subject, `providerRevision = modifiedLocal` when present,
otherwise `createdLocal`. Both missing yields `CURRENT_REVISION_UNPROVEN`.
Present modifiedLocal before createdLocal is integrity failure. Partial/malformed
date/time source pairs retain the existing ingestion-invalid rule. A missing
createdLocal with a present valid modifiedLocal can be ordered only where the
accepted source contract permits it; this does not change the V3 parser.

The maximum providerRevision is the candidate current revision. Equal maximum
revision and equal versioned semantic fingerprint is an equivalent re-observation.
Equal maximum revision with different semantic fingerprint resolves `CONFLICT`;
sourceFingerprint or observation time cannot break that tie. Any source row
without enough revision evidence to establish its relation to the maximum makes
currentness unproven; it cannot be silently discarded. A newer accepted revision
without integrationOrderReference yields `UNRESOLVED`; no older-reference fallback.

Equivalent re-observations choose one deterministic durable source coordinate
for lineage only (capability, input progress version, record ordinal). This
choice never ranks provider currentness. Store and recompute the complete
supported semantic evidence fingerprint, including currentness and binding
material. Source integrity contradictions cannot be repaired by a resolver.

### Exact ML lineage and currency

Automatic confirmation requires a durable V021 row in the policy ML connection,
capability `marketplace-economic.order-source`, exact external reference, and
an exact-source V022 terminal promotion `PROMOTED | DUPLICATE` to the selected
canonical V022 marketplace_order_id in the same organization/marketplace.
V022 first_source_connection_id alone is insufficient. Reacquisition-v1 alone
is insufficient. Caller source keys are hints to validate, not lineage authority.

Compare integrationOrderReference and canonical ML external_order_id using the
existing validated exact textual source semantics. No additional trimming,
case folding, numeric conversion, zero deletion, substring/fuzzy matching,
amount/date/SKU/customer/shipping/pack/payment fallback or origin precondition.
CustomerOrderReference is neither an automatic key nor a hidden veto.

V021 currency must equal V022 canonical identity currency; disagreement is
integrity contradiction. Omie currency missing is neutral for transaction
identity, present/equal is corroborating, present/different resolves `CONFLICT`.
Missing Omie currency is never inferred or written into provider evidence.
These rules grant no amount-comparison or financial-basis authority.

### Organization-wide cardinality

Across every policy and ML/Omie connection in one organization:

```text
one stable Omie subject -> at most one current CONFIRMED marketplace_order_id
one marketplace_order_id -> at most one current CONFIRMED stable Omie subject
```

All unsuperseded CONFIRMED decision leaves participate in reservation checks,
including a stale/temporarily unresolved leaf. Such a reservation is released
only by explicit append-only supersession, never by ignoring a disabled policy,
suspended connection, missing current row or changed integration reference.
Resolved source-candidate ambiguity also fails closed across policy scopes.
No unrelated tenant can block or provide a same-organization proof.

### Connection and organization lifecycle

Activation and any new automatic decision require organization ACTIVE; selected
ML connection ACTIVE/provider `br.com.mercadolivre`; selected Omie connection
ACTIVE/provider `omie`; each exact current credential binding present and
unrevoked. Connection ids and binding versions are server-verified durable
joins. Connection ownership cannot be overridden by caller input.

Suspension/revocation blocks new decisions. History remains immutable.
A historical decision remains audit evidence; the current resolver rechecks
its current source/lineage applicability and never treats history as an enduring
execution permit. Explicit administrative correction may supersede an old
historical decision only through its separately authorized path; it cannot be
used to bypass a connection gate for a new live confirmation.

### Decision reasons and current resolution

Persist `CONFIRMED | REJECTED` only. Reasons are
`POLICY_EXACT_MATCH | EXPLICIT_CONFIRMATION | EXPLICIT_REJECTION | CORRECTION`.
POLICY_EXACT_MATCH is CONFIRMED-only and requires every automatic policy gate.
EXPLICIT_CONFIRMATION requires its own durable authenticated authorization and
pair-specific evidence, but does not require an invented automatic policy.
EXPLICIT_REJECTION is authorized explicit action, never inferred from mismatch.
CORRECTION requires exact current predecessor, explicit correction authorization
and revalidated new target/evidence; automatic resolution cannot label a target
change CORRECTION or silently negate an explicit decision.

An explicit decision does not override tenant isolation, canonical target
integrity, global cardinality, source fingerprint/currentness contradictions or
supported lineage. It may address historical temporal ineligibility and the
absence of a connection-wide automatic convention only with pair-specific proof.
Any exception needs a separately frozen contract, not a caller assertion.

The current read resolver returns UNRESOLVED, CONFIRMED, REJECTED or CONFLICT.
It validates the decision fingerprint, stable subject, current provider revision,
canonical target, exact source lineage and reason-specific authority. A stale
fingerprint/revision or changed integration reference cannot reuse an earlier
CONFIRMED result. An explicit REJECTED leaf cannot be silently superseded by
automatic string equality. A disabled policy blocks new POLICY_EXACT_MATCH
writes; historical valid decisions are not retrospectively reinterpreted as
never authorized, nor are they automatically promoted into fresh authority.

### Atomic write, concurrency and failure semantics

Read-only resolution uses one READ ONLY REPEATABLE READ snapshot. Resolve and
record uses one database transaction, with serializable isolation and all
authorization/evidence checks re-evaluated after deterministic locking:

1. policy scope / authority epoch;
2. stable Omie subject;
3. canonical ML target.

Subject and target lock names include organization and exclude policy scope.
Use persistent lock rows or transaction advisory locks; absence of a decision
row is not absence of a lock. Corrections lock old/new target keys in canonical
sorted order. Policy lifecycle writes share the policy-scope lock; every identity
writer shares the subject/target locks. Credential/organization lifecycle reads
must be coordinated with existing lifecycle writes via their database row locks
and all paths must share an agreed total lock order. Opposite scope/subject/target
operations cannot invent different lock domains.

After locks, re-evaluate current policy, administrative/decision permission,
organization/connections/current bindings, V3 currentness, exact V021/V022,
all current decisions, temporal applicability, currency and global cardinality.
Only then insert. A decision records the coherent evidence snapshot it validated;
later evidence is detected by subsequent current resolution, not by mutating
history. The implementation must explicitly test concurrent ingestion and
lifecycle updates as well as concurrent decision writers.

Deadlock, serialization failure, timeout, network or storage failure is an
infrastructure failure (`Unavailable`), never identity REJECTED/CONFLICT or
proof of zero records. A bounded retry restarts the entire operation with the
same idempotency key and freshly revalidated authority. A changed replay payload
is integrity failure. Unknown commit outcome requires replay/lookup, not a
second independently identified command. No direct DriverManager lifecycle debt.

### Semantic lineage, isolation and implementation gate

Use explicitly versioned canonical encoding, domain-separated SHA-256 and
recomputation on reads. Distinguish absent fields from empty text, decimal
representation from business identity, administrative revision from semantic
version and raw source fingerprint from semantic evidence fingerprint.
The implementation contract must fix byte encoding, field order, null tags,
timestamp precision, exact decimal serialization and known-answer vectors.

Decision material includes organization/stable subject, canonical ML target,
both connections, exact V3 revision/coordinates/raw+semantic fingerprint/version,
exact V021/V022 source/promotion coordinates, canonical external id/currency,
reason-specific administrative or explicit authority, policy id/revision/version/
fingerprint where applicable, temporal evidence, decision revision/predecessor,
principal, provenance/reason/correlation and server decidedAt. Missing lineage
cannot be synthesized from a diagnostic join or body-supplied fingerprint.

Before V034: a final adversarial review must close BLOCKER/HIGH findings and a
closed implementation package must fix the temporal proof admission algorithm,
permission source, policy/decision schema constraints, fingerprint vectors,
cross-writer/lifecycle lock order, exact tests, kill rules and field proof plan.
This documentary correction alone does not declare V034 technically selectable.

```text
S1 / V033 = PROVEN (source acquisition only)
REVISION_5 = RECONSTRUCTED / PENDING FINAL ADVERSARIAL GATE
S2 / V034 = HOLD
EXPECTED_SALE_BASIS_POLICY = UNFROZEN / RESEARCH ONLY
S3 / V035 = HOLD
C2 = HOLD
ECONOMIC_BASIS_EQUIVALENCE = NOT PROVEN
NONZERO_FINANCIAL_LEAKAGE = NOT PROVEN
```

The authorized sequence remains S1 -> identity contract/gates -> S2 -> governed
pair corpus -> ExpectedSaleBasisPolicy research/adversarial freeze -> S3 -> C2
-> reconciliation -> Decision Room. No Sierra/commercial roadmap change.

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


## Revision-4 TransactionIdentityBindingPolicy v1 freeze

Revision 4 freezes the first governed ML <-> Omie transaction-binding policy.
It does not implement S2/V034.

### External contract evidence

Official Omie order documentation defines `codigo_pedido_integracao` as the
order code in the application integrated with Omie and explicitly describes the
field as a relationship map between the applications.

The same contract defines `numero_pedido_cliente` only as an optional customer
order number and `origem_pedido` only as order provenance/origin.

Official Mercado Livre order documentation defines `order.id` as the unique
order identifier.

Therefore the only provider field eligible for automatic binding in policy v1
is:

```text
Omie codigo_pedido_integracao
<-> Mercado Livre order.id
```

Eligibility is not authority. The equality is authoritative only when the
specific connection pair has an explicit durable policy declaring that this is
the integration convention.

Sources reviewed on 2026-09-18:

```text
https://app.omie.com.br/api/v1/produtos/pedido/
https://developers.mercadolivre.com.br/pt_br/gerenciamento-de-vendas
```

### Frozen policy identity

Policy v1 is scoped exactly by:

```text
organizationId
mercadoLivreConnectionId
omieConnectionId
policyVersion
```

Frozen semantic mode:

```text
OMIE_INTEGRATION_ORDER_REFERENCE_EQUALS_ML_ORDER_ID
```

The policy must be durable, immutable, versioned and explicitly registered.
Observed matches must never create, activate or infer the policy.

A policy revision must carry a deterministic semantic fingerprint. Historical
decisions retain the exact policy version and fingerprint that authorized them.

### Exact comparison semantics

Automatic binding compares:

```text
current Omie V3 integrationOrderReference
==
V022 external_order_id
```

Comparison is exact after the source contracts' existing text normalization.

Forbidden coercions:

```text
integer parsing
leading-zero removal
case folding
whitespace trimming beyond source-contract validation
prefix/suffix removal
substring matching
fuzzy matching
amount-assisted matching
date-assisted matching
SKU-assisted matching
customer-assisted matching
origin-assisted matching
```

`customerOrderReference` is never automatic identity authority in v1.

`sourceOrderOrigin` is never identity authority.

### Required Mercado Livre connection lineage

Equality against the V022 registry alone is insufficient.

Automatic confirmation requires one exact durable Mercado Livre source lineage
for the policy's `mercadoLivreConnectionId`:

```text
V021 integration_mercado_livre_order_source_observation
organization_id = policy organization
connection_id   = policy Mercado Livre connection
capability      = marketplace-economic.order-source
external_order_ref = candidate external id

        +
V022 marketplace_order_occurrence_source_promotion
same exact V021 source key
outcome IN (PROMOTED, DUPLICATE)
marketplace_order_id = selected V022 identity

        +
V022 marketplace_order_identity_registry
organization_id = policy organization
marketplace_key = mercado-livre
external_order_id = candidate external id
currency = durable source currency
```

`marketplace-economic.order-source.reacquisition-v1` source rows do not establish
this automatic v1 lineage because the current V022 promotion processor does not
promote that capability.

### Required Omie currentness and uniqueness

Automatic confirmation also requires:

```text
exact policy organization
exact policy Omie connection
V3 source evidence only
one current accepted Omie revision
non-null integrationOrderReference
one current Omie order for the candidate integration reference
one V022 canonical ML identity for the candidate external id
no second current Omie order resolving to that ML identity
no unresolved same-revision semantic conflict
```

Missing or ambiguous currentness fails closed.

### Automatic result

Only when every gate above is proven may the resolver derive:

```text
CONFIRMED
```

with lineage to:

```text
policy scope
policy version
policy fingerprint
Omie connection
Omie V3 source identity + revision + semantic fingerprint
ML connection
exact V021 source key
exact V022 promotion row
V022 canonical marketplace_order_id
external order id
```

Persisted S2 decisions remain:

```text
CONFIRMED
REJECTED
```

Resolver states remain:

```text
UNRESOLVED
CONFIRMED
REJECTED
CONFLICT
```

No exact-string mismatch creates an automatic `REJECTED` decision.

No policy, no durable ML connection lineage, missing integration reference or
unproven currentness resolves to `UNRESOLVED`.

Multiple live candidates, contradictory unsuperseded policy revisions or
one-to-many / many-to-one binding ambiguity resolves to `CONFLICT`.

### Revision and supersession

A later Omie revision that materially changes binding-relevant semantics does
not mutate the historical decision.

It requires a new revision-specific decision and explicit supersession lineage.

A later policy version does not retroactively rewrite decisions produced by an
earlier policy version.

### Real-data interpretation

The current real candidate remains diagnostic evidence:

```text
durable integration-reference canonical matches = 4 / 4 generations
durable customer-reference canonical matches    = 0 / 4 generations
one V022 integration-reference candidate
ambiguity = 0
origin = API
```

This evidence supports the choice of field to govern. It does not by itself
authorize the connection-pair policy.

For the currently observed connection pair:

```text
automatic binding policy registration = NOT YET PROVEN
automatic CONFIRMED decision          = NOT YET AUTHORIZED
```

### ExpectedSaleBasisPolicy sequencing correction

Revision 4 supersedes the earlier sequence that placed both policies before S2.

Expected economic-basis equivalence cannot be responsibly frozen from the
single 58.28 diagnostic pair. S2 must first create a governed set of reliable
cross-system identities.

The governing sequence is now:

```text
S1 / V033 source evidence
        = PROVEN
        |
        v
TransactionIdentityBindingPolicy v1
        = FROZEN DESIGN
        |
        v
Revision-4 adversarial gate
        |
        v
S2 / V034 implementation
        |
        v
S2 durable identity field proof
        |
        v
governed ML <-> Omie pair set
        |
        v
ExpectedSaleBasisPolicy research / adversarial comparison
        |
        v
ExpectedSaleBasisPolicy freeze
        |
        v
S3 / V035 SALE / EXPECTED
        |
        v
C2 ACTUAL
        |
        v
reconciliation
        |
        v
Decision Room
```

Revision 4 does not authorize V034 implementation until its own adversarial
review passes.

ExpectedSaleBasisPolicy remains research-only and unfrozen.

The economic boundary is unchanged:

```text
REAL EXPECTED/ACTUAL ECONOMIC BASIS EQUIVALENCE = NOT PROVEN
REAL END-TO-END FINANCIAL VIABILITY = NOT YET PROVEN
REAL NON-ZERO FINANCIAL LEAKAGE = NOT PROVEN
```

## Revision-6 explicit historical transaction identity contract

Revision 6 adds a distinct, fail-closed authority path for historical
transaction identity decisions. It supersedes earlier S2 wording only where
that wording could combine explicit confirmation with automatic policy matching.
It changes neither S1/V033 source evidence nor the automatic-policy hold.

### Separate authority paths

`POLICY_EXACT_MATCH` is reserved for a future automatic policy path. It requires
an enabled, prospective policy and remains unavailable. It cannot be selected by
an explicit request.

Historical `EXPLICIT_CONFIRMATION`, `EXPLICIT_REJECTION`, and `CORRECTION` are
separate decision authorities. They never create, infer, enable, disable or
supersede `TransactionIdentityBindingPolicy`. A historical equality, a current
decision, a service bearer, or a policy-shaped request is not policy authority.

### Stable subject, target and required durable evidence

The sole transaction-decision chain key is:

```text
(organizationId, omieConnectionId, sourceOrderReference)
```

`integrationOrderReference`, amount, date, SKU and policy scope are excluded.
The target is the existing tenant-qualified V022 `marketplace_order_id`, with
exact Mercado Livre identity registry, `marketplace = mercado-livre`, external
order id, V021 source observation and terminal V022 `PROMOTED | DUPLICATE`
occurrence-promotion lineage. A request may name a canonical target identifier,
but it cannot supply lineage coordinates as a substitute for durable joins.

Every explicit decision binds the current accepted V3 revision for the stable
subject and exact Omie connection: capability, input-progress version, record
ordinal, sourceOrderReference, providerRevision, raw source fingerprint,
semantic-evidence fingerprint and their supported versions. The repository
derives and recomputes this evidence packet. Caller-supplied coordinates or
fingerprints are assertions to validate, never authority.

### Historical currentness rule

The selected model is current accepted V3, not an arbitrary historical revision.
It is the only model that prevents an explicit actor from preserving an old
convenient integration reference while a later accepted revision contradicts it.
ProviderRevision remains `modifiedLocal ?: createdLocal`; observedAt remains
acquisition provenance only. Missing ordering, same maximum revision with a
different semantic fingerprint, or a later current revision without the required
binding material yields `UNRESOLVED` or `CONFLICT` according to Revision 5.

An explicit historical decision may use evidence older than an automatic policy
epoch; it must not satisfy prospective-policy time rules. It is historical only
because its authority is explicit and separately admitted. A later contradictory
accepted V3 revision does not rewrite history, but makes the current resolver
withhold confirmation until an authorized correction or rejection creates a
coherent successor. No fallback to an older V3 revision is allowed.

### Dedicated admission and lifecycle

The existing service bearer establishes organization scope only. It has no
transaction-decision or policy-administration capability. V034 must introduce
two server-derived, independently checked capabilities:

```text
RECORD_TRANSACTION_IDENTITY_DECISION
MANAGE_TRANSACTION_IDENTITY_BINDING_POLICY
```

The second is broader and cannot be implied by the first. The exact trusted
grant issuer, storage, revocation and authenticated principal representation are
still a pre-implementation gate. Until they exist, commands return unavailable;
they do not fall back to the generic bearer or caller `principal_ref`.

Explicit historical decisions require organization ACTIVE and the exact durable
connection records/provider keys, but do not require current provider network
access, ACTIVE connection status, or an unrevoked credential binding. A suspended
or revoked connection prevents new provider activity and automatic policy work;
it does not erase durable historical evidence. This preserves historical
governance while prohibiting a provider call as confirmation evidence. An
organization suspension blocks a new governance write because tenant authority
itself is unavailable.

### Request, reasons and global decision universe

The minimal explicit intent is decision id, correlation id, decision kind,
stable sourceOrderReference, canonical marketplaceOrderId, reason, provenance
and optional predecessor id. Organization, provider connections, principal,
V3/V021/V022 coordinates, policy material and fingerprints are server-derived.
`EXPLICIT_CONFIRMATION` pairs only with CONFIRMED; `EXPLICIT_REJECTION` only
with REJECTED; `CORRECTION` only with an exact current predecessor. Mismatch
never creates rejection.

Both explicit and eventual automatic paths write to one append-only current
decision universe and share organization-wide cardinality:

```text
one stable Omie subject -> at most one current CONFIRMED marketplace_order_id
one marketplace_order_id -> at most one current CONFIRMED stable Omie subject
```

They serialize on the same stable-subject and canonical-target reservations.
Resolve-and-record rechecks currentness, exact lineage, admission, predecessor
and cardinality after deterministic locks. Same-subject/two-target,
two-subject/same-target, explicit-vs-automatic, correction-vs-confirmation and
two-correction races must either serialize to one valid append-only result or
return conflict/unavailable. Deadlock, serialization failure and unknown commit
outcome are infrastructure states, never identity decisions.

### Gate state

```text
EXPLICIT_HISTORICAL_CONTRACT = FROZEN DESIGN / PENDING ADVERSARIAL REVIEW
AUTOMATIC_POLICY_CONFIRMATION = UNAVAILABLE
S2 / V034 = HOLD
S3 / C2 = HOLD
```

## Revision-7 explicit currentness correction

Revision 6 incorrectly carried the automatic-path consequence of a missing
current `integrationOrderReference` into explicit historical confirmation.
That would make a missing revision-material field silently veto a separately
admitted evidence path without proving a contradictory target.

For explicit decisions, the current accepted V3 revision remains mandatory for
the stable subject, and missing/ambiguous provider revision ordering or a same-
revision semantic conflict remains `UNRESOLVED`/`CONFLICT`. A missing current
integrationOrderReference is evidence absence: it blocks automatic matching but
does not itself disprove an explicit target. Explicit confirmation may proceed
only from its independent admitted authority plus the exact V021/V022 target
lineage and current V3 evidence packet. If a current integration reference is
present and exactly contradicts the explicit target's canonical external id,
the resolver returns `CONFLICT`; it cannot select the old reference or write a
confirmation. A later correction/rejection remains explicit and append-only.

This correction does not make missing data a match, does not permit a historical
V3 fallback, and does not enable automatic policy confirmation.

## Revision-8 transaction identity command admission

The existing authentication model creates only `ServicePrincipal(organizationId)`
from `FLOOOW_SERVICE_TOKEN`. It has no operation capability, actor distinction,
durable grant or revocation semantics. Its implicit reuse is forbidden.

V034 must define two distinct server-derived permissions:

```text
RECORD_TRANSACTION_IDENTITY_DECISION
MANAGE_TRANSACTION_IDENTITY_BINDING_POLICY
```

The first admits explicit CONFIRMED, REJECTED and CORRECTION only. The second
admits policy lifecycle only. Neither broad service bearer, provider credential,
connector capability, ingestion credential nor request field implies either.

Each command authenticates through a distinct command credential and yields a
server-derived `TransactionIdentityCommandPrincipal`; request principal,
organization, connections, credential version and grant identifier are forbidden.
Missing/disabled/unsupported credentials fail closed without bearer fallback.

The credential alone is insufficient. A tenant-qualified append-only
`TransactionIdentityCommandGrant` binds grant id/revision/predecessor,
organization, command principal and credential version, permission, exact ML and
Omie connections, ENABLED/DISABLED state, reason/provenance/correlation/server
time and semantic version/fingerprint. Only its current unsuperseded ENABLED
leaf admits a command. A request cannot create it. Forks, changed replays,
fingerprint mismatch and unsupported versions are integrity failures. Secret
rotation requires a new grant leaf; grant disable never rewrites history.

This follows existing tenant, versioned credential-binding, control-audit and
append-only decision patterns without treating a provider connection as a command
grant. The trusted grant issuer/storage/revocation implementation remains a
pre-implementation gate; no real grant or credential is created here.

An explicit request contains only decision id, correlation id, CONFIRMED or
REJECTED, sourceOrderReference, canonical marketplaceOrderId, reason, provenance
and optional predecessor. `marketplaceOrderId` joins V022; sourceOrderReference
selects the stable subject within server-bound scope. V3/V021/V022 coordinates,
lineage and fingerprints are repository-derived. CORRECTION requires the exact
current predecessor and same validation.

Explicit historical admission requires organization ACTIVE, exact durable
provider records/keys, the current accepted V3 packet, exact V021/V022 lineage
and current decision grant. It requires neither provider call, active provider
connection, current provider credential, automatic policy nor prospective time
proof. Server command time is not provider event time and cannot become a policy
epoch. Organization-wide decision reservations and deterministic locks are shared
with the future automatic path.

## Revision-3 real-data S1 proof

S1/V033 is now technically proven from the preserved real Omie dataset and the
exact implementation commit:

```text
implementation commit:
27c291ee399a17ed97fdb8953b86a9a4c7301877

final proof script SHA-256:
23B144BD58725B581A16D350763283F40A9A1C0160EBACE1DA3E5C1C4A150C29

final proof checkpoint SHA-256:
48820F04E4BDC33CE20BA3C84706CA9F7B8DD6FB0BC217130431DAAFA574BBF6

historical Omie rows:
v0 = 132
v1 = 133
v2 = 135

V3:
base rows    = 141
sidecar rows = 141
line rows    = 196

scope:
organizations = 1
Omie connections = 1
```

The real provider origin distribution is:

```text
API = 124
ERP = 17
MLV = 0
```

This disproves the proof-harness assumption that a real Mercado Livre-related
order must have `origem_pedido = MLV`.

Revision 3 therefore freezes:

```text
source_order_origin = provider provenance / corroborating evidence

source_order_origin
!= cross-system transaction identity authority

MLV origin
!= prerequisite for S1

MLV origin
!= prerequisite for S2

API / ERP / MLV origin
cannot confirm ML <-> Omie transaction identity
```

The one real V022 diagnostic match is unambiguous but remains evidence only:

```text
matched V3 rows = 1
distinct canonical marketplace orders = 1

integration-reference match = 1
customer-reference match = 0

Omie -> multiple ML ambiguity = 0
ML -> multiple Omie ambiguity = 0
```

The earlier F2B diagnostic report stated that the same 58.28 candidate matched
through both integration and customer references. Revision 3 preserves that
historical report but supersedes its customer-reference conclusion with the
durable v0/v1/v2/v3 lineage:

```text
canonical integration-reference matches across generations = 4
canonical customer-reference matches across generations    = 0
```

The integration-reference observation is confirmed. The customer-reference
observation is superseded. This correction does not create transaction identity
authority.

The real source shape also proves the missing-value invariant:

```text
order-ended evidence present        = 0 / 141
marketplace fee evidence present    = 0 / 141
marketplace shipping evidence       = 0 / 141

missing ended flag
!= ended = false

missing marketplace fee
!= fee = 0

missing marketplace shipping
!= shipping = 0
```

V3 raw and semantic fingerprints are separately present for all 141 rows and
are distinct contracts.

The final replay was executed only after the API was isolated to a single
Docker-internal network. The reacquisition returned no newly committed page or
record, resolved through the already-committed exhausted V3 progress, left the
V3 evidence unchanged and left v0/v1/v2 evidence unchanged.

Therefore:

```text
S1 / V033 source-evidence acquisition = PROVEN

TransactionIdentityBindingPolicy = NOT YET FROZEN
ExpectedSaleBasisPolicy          = NOT YET FROZEN

S2 implementation = HOLD
S3 implementation = HOLD
C2 implementation = HOLD
```

S1 completion authorizes policy research/freeze work only. It does not authorize
S2, S3, canonical ERP REVENUE, EXPECTED authority, ledger materialization,
reconciliation or Decision Room activation.

The financial-evidence boundary remains unchanged:

```text
REAL CROSS-SYSTEM PATH VIABILITY = PROVEN

REAL EXPECTED/ACTUAL ECONOMIC BASIS EQUIVALENCE = NOT PROVEN

REAL END-TO-END FINANCIAL VIABILITY = NOT YET PROVEN

REAL NON-ZERO FINANCIAL LEAKAGE = NOT PROVEN
```

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
S1 / V033 implementation
        ↓
S1 real-data field proof
        ↓
Revision-3 evidence correction
        ↓
research/freeze TransactionIdentityBindingPolicy
research/freeze ExpectedSaleBasisPolicy
        ↓
S2 implementation only after its own gate
        ↓
S2 durable identity proof
        ↓
S3 implementation only after its own gate
        ↓
S3 EXPECTED authority proof
        ↓
return to C2
```

Completed through Revision 3:

```text
Revision-2 adversarial review = PASS
S1 / V033 implementation      = COMPLETE
S1 real-data field proof      = PASS
Revision-3 correction         = RECORDED
```

Green at one gate means the next gate is possible. It does not mean the next
gate was chosen.
