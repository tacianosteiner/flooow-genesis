# TASK-0165S - Governed Omie SALE / EXPECTED Authority - Design Evidence

Status: S1/V033 PROVEN - REVISION 9 DESIGN FROZEN - ZERO-GRANT AUTH INFRASTRUCTURE SELECTED - S2B/S3/C2 HOLD

Revision: 9

Date: 2026-09-18

## Revision-9 design and selectable implementation evidence

Migration allocation correction: V034 is command authorization infrastructure,
not S2A transaction identity. Historical `S2 / V034` and `S3 / V035` numbering
is SUPERSEDED. The S2A package must inspect and select the next free migration;
S2B/S3 numbers remain unreserved. Historical revisions are retained verbatim.

Current normative boundary: ADR-0082 Revision-9 and dedicated ADR/SPEC-0083.
Revision 6 introduced explicit historical decisions; 7 corrected missing current
integration reference; 8 drafted command admission but incorrectly blocked safe
engineering on real-grant absence. Revision 9 supersedes that gate, R8 permission
names and credential-revision-bound grants. Authentication credentials rotate
while durable actor and grant lineage survive. No operational grants created.

Repository inspection confirms SPEC-0005 single privilege/new specification
requirement, SPEC-0010 exclusions, and SPEC-0074 product coarse-bearer precedent.
No granular vocabulary existed. New exact decision-write and policy-admin
permissions are independent. Working-tree migrations end at V033; select V034
for auth only, without reserving future identity/S3 migration numbers.

Adversarial auth review: body principal/grant/tenant spoofing cannot enter the
server-derived path; zero grants/wrong permission deny; actor remains stable
under rotation; current credential and grant are revalidated in the writer
transaction; shared principal locks serialize revoke; predecessor/unique/FK
checks stop forks/cross-tenant grants. Theft/replay needs activation transport
and operational controls; no HTTP surface is activated in this slice.
Internal design review: selectable substrate BLOCKER=0, unresolved HIGH
threatening authority integrity=0. This is not independent certification.

Decomposition review accepts S2A independently of policy, with exact durable
current V3 and canonical V021/V022 joins, global cardinality and shared future
history/locks. Current contradictory references veto; missing stays neutral to
authorized explicit intent. Corrections cannot mutate stable subject/relation.
Identity writer/schema remains an unselected later package, not a test-proven
implementation. Automatic POLICY_EXACT_MATCH remains unavailable.

S2A DESIGN FROZEN / implementation candidate after auth; S2B HOLD; COMMAND
AUTHORIZATION required dependency; governed field pair count is still zero.
One proven pair permits ExpectedSaleBasisPolicy RESEARCH only, never freeze.
S1 proof file/volumes remain unchanged; S3/C2 HOLD; equivalence/leakage NOT PROVEN.
Old build/audit V034 package stays draft. SPEC-0083 is the closed selectable
package; implementation/tests/checkpoint are recorded separately after execution.

Infrastructure execution: domain principal/credential verification and permission
model, PostgreSQL V034 append-only principal/credential/grant persistence and
same-transaction default-deny resolution implemented without startup wiring,
provisioning endpoint, operational authority rows or transaction decisions.
Two new domain tests and six new disposable PostgreSQL tests passed with zero
failures/errors/skips across the validation sequence. Backend tests were rerun
after correcting the nullable-predecessor SQL CHECK and adding foreign-scope
adversarial assertions. The broader build passed; its report snapshot has 147
XML suites / 1006 tests, mixing fresh execution and cached reports, not 1006
newly executed field tests. Source S1 evidence SHA-256 remains exactly
C64B28EF23F8B4AABCC19CE7BB420764C008C3DDAAC30B276DEEAB842857783E.
No commit or push: HEAD is preserved at the user-frozen 27c291ee checkpoint.
Operational field gate remains closed. This proves infrastructure behavior,
not a governed transaction pair, automatic policy or economic equivalence.

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

## Branch and base

```text
branch:
research/task-0165s-governed-omie-sale-expected-authority

base:
research/task-0165p-governed-reconciliation-assessment-identity-lineage
fcff073793a3bd806d7302dab445404725baa4b9
```


## Revision-4 identity-policy research and design freeze

Revision 4 was triggered after S1/V033 and Revision 3 were proven.

### Provider-contract research

Official Omie order documentation reviewed on 2026-09-18 states that:

```text
codigo_pedido_integracao
= code of the order in the application integrated with Omie
= relationship map between the applications

numero_pedido_cliente
= optional customer order number

origem_pedido
= provider order origin/provenance
```

Official Mercado Livre documentation reviewed on 2026-09-18 defines `order.id`
as the unique order identifier.

References:

```text
https://app.omie.com.br/api/v1/produtos/pedido/
https://developers.mercadolivre.com.br/pt_br/gerenciamento-de-vendas
```

Disposition:

```text
integrationOrderReference
    = eligible governed binding field

customerOrderReference
    = not automatic binding authority

sourceOrderOrigin
    = provenance only
```

Eligibility is not authority. The connection pair must explicitly declare the
integration convention.

### Repository-contract research

Existing V022 canonical ML identity is:

```text
organizationId
marketplace = mercado-livre
externalOrderId
```

`connectionId` is intentionally excluded from canonical business identity.

The V022 registry preserves the first durable source coordinates, and the
occurrence-promotion ledger preserves exact V021 source coordinates and the
canonical `marketplace_order_id`.

V028 permits the Mercado Livre V021 source tables to store both the base
capability and `reacquisition-v1`.

However, the current V022 promotion processor selects only:

```text
marketplace-economic.order-source
```

Therefore Revision 4 deliberately refuses to treat a reacquisition-v1 row alone
as automatic ML connection-lineage authority.

### Real-data support

S1 field proof established:

```text
V3 rows = 141
origin API = 124
origin ERP = 17
origin MLV = 0

one exact V022 diagnostic candidate
integration match = 1
customer match = 0
ambiguity = 0

candidate durable lineage:
integration canonical match = 4 / 4 generations
customer canonical match    = 0 / 4 generations
```

This supports policy-field selection but is not sufficient to infer a
connection-wide contract.

### Frozen TransactionIdentityBindingPolicy v1

Frozen binding mode:

```text
OMIE_INTEGRATION_ORDER_REFERENCE_EQUALS_ML_ORDER_ID
```

Frozen scope:

```text
organization
Mercado Livre connection
Omie connection
policy version
```

Frozen mandatory gates:

```text
explicit durable policy registration
current accepted Omie V3 revision
non-null integrationOrderReference
exact textual equality
exact base-capability V021 ML connection lineage
terminal V022 PROMOTED/DUPLICATE lineage
V022 canonical identity
currency coherence
one-to-one cardinality
no semantic/currentness contradiction
policy version + fingerprint lineage
```

Forbidden substitutes:

```text
customerOrderReference
origin
amount
date
SKU
product
customer
shipping
pack
payment
fuzzy matching
numeric coercion
```

### Policy/decision lifecycle

Policies are versioned and immutable.

Decisions are revision-specific and immutable.

Supersession is explicit and append-only.

No provider observation automatically creates a policy.

No new policy version rewrites historical decisions.

### Gate-order correction

The earlier design placed both identity and economic-basis policies before S2.

Revision 4 supersedes that order.

Reason:

```text
one diagnostic 58.28 equality
!= economic-basis equivalence

robust ExpectedSaleBasisPolicy research
requires a governed corpus of ML <-> Omie identities

that governed corpus is produced by S2
```

New order:

```text
S1 = PROVEN

TransactionIdentityBindingPolicy v1
    = FROZEN DESIGN

Revision-4 adversarial review
    = NEXT GATE

S2 / V034
    = HOLD until that review passes

ExpectedSaleBasisPolicy
    = RESEARCH ONLY after S2 governed pair proof
    = must be frozen before S3

S3 = HOLD
C2 = HOLD
```

### Revision-4 non-claims

Revision 4 does not claim:

```text
the current connection pair is already registered for automatic binding
the one real candidate proves the integration convention globally
customerOrderReference is identity authority
origin MLV is required
Omie total equals Mercado Livre total economically
S2 is implemented
S3 is implemented
C2 is implemented
```

Economic conclusions remain:

```text
REAL CROSS-SYSTEM PATH VIABILITY = PROVEN
REAL EXPECTED/ACTUAL ECONOMIC BASIS EQUIVALENCE = NOT PROVEN
REAL END-TO-END FINANCIAL VIABILITY = NOT YET PROVEN
REAL NON-ZERO FINANCIAL LEAKAGE = NOT PROVEN
```

## Revision-3 real-data proof and evidence correction

S1/V033 has completed implementation and real-data proof.

Exact implementation provenance:

```text
branch:
feature/task-0165s1-omie-reacquisition-v3-source-evidence

implementation commit:
27c291ee399a17ed97fdb8953b86a9a4c7301877

final proof script SHA-256:
23B144BD58725B581A16D350763283F40A9A1C0160EBACE1DA3E5C1C4A150C29

final proof checkpoint SHA-256:
48820F04E4BDC33CE20BA3C84706CA9F7B8DD6FB0BC217130431DAAFA574BBF6
```

### Real V3 acquisition

```text
historical v0 = 132
historical v1 = 133
historical v2 = 135

V3 base rows    = 141
V3 sidecar rows = 141
V3 line rows    = 196

organization scopes = 1
Omie connection scopes = 1

provider origin:
API = 124
ERP = 17
MLV = 0
```

### Origin finding

The initial proof harness incorrectly required at least one `MLV` origin.

That requirement is invalid.

Disposition:

```text
implementation defect = NO
parser defect         = NO
proof-policy defect   = YES

source_order_origin = provider provenance only
```

### F2B reference correction

The earlier F2B report stated:

```text
via integration reference = true
via customer reference    = true
```

The first statement is confirmed.

The second statement is superseded by exact durable lineage:

```text
v0 integration = canonical match
v1 integration = canonical match
v2 integration = canonical match
v3 integration = canonical match

canonical integration matches = 4

v0 customer = missing
v1 customer = other
v2 customer = other
v3 customer = other

canonical customer matches = 0
```

The raw provider fingerprint remains the same across the observed v0/v1/v2/v3
generations for the real candidate, so there is no evidence of a provider-side
reference change between those acquisitions.

This correction is diagnostic only. It does not grant
`INTEGRATION_ORDER_REFERENCE` authority.

### Missing-value proof

For the acquired real dataset:

```text
order-ended explicit rows       = 0
marketplace-fee rows            = 0
marketplace-shipping rows       = 0
```

These remain missing and were not coerced to false or zero.

### Final replay

The V3 progress was already exhausted.

The final proof bootstrapped the exact API image, then disconnected and removed
the temporary external bootstrap network before invoking reacquisition.

At the replay boundary the API had exactly one Docker-internal network.

Result:

```text
new committed pages = 0
new records         = 0
already committed   >= 1

V3 replay idempotent = true
v0/v1/v2 immutable  = true
```

### Revision-3 admissible conclusion

```text
S1 / V033 = PROVEN

REAL CROSS-SYSTEM PATH VIABILITY = PROVEN

REAL EXPECTED/ACTUAL ECONOMIC BASIS EQUIVALENCE = NOT PROVEN

REAL END-TO-END FINANCIAL VIABILITY = NOT YET PROVEN

REAL NON-ZERO FINANCIAL LEAKAGE = NOT PROVEN
```

Next authorized work:

```text
research/freeze TransactionIdentityBindingPolicy
research/freeze ExpectedSaleBasisPolicy
```

Still not authorized:

```text
S2 implementation
S3 implementation
C2 implementation
ledger materialization activation
ledger correction materialization
real reconciliation
Decision Room production activation
official roadmap expansion
Sierra/commercial monetization integration
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

## Current governed state

```text
ADR-0082 Revision 3 = PROPOSED
SPEC-0082 Revision 3 = DRAFT

S1 / V033 implementation = COMPLETE
S1 real-data field proof = PASS
S1 / V033 status = PROVEN

TransactionIdentityBindingPolicy = RESEARCH/FREEZE NEXT
ExpectedSaleBasisPolicy = RESEARCH/FREEZE NEXT

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
