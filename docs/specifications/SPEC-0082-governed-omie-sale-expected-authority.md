# SPEC-0082 - Governed Omie SALE / EXPECTED Authority

Status: Draft

Revision: 9

Source decision: ADR-0082

## Revision-9 normative boundary

Current migration allocation: V033 = Omie V3; V034 = command authorization.
Historical `S2 / V034` and `S3 / V035` references are SUPERSEDED. S2A writer
selects the next free migration from actual repository state; S2B automatic
policy and S3 EXPECTED authority are later gates with no reserved numbers.

The complete Revision-9 authoritative S2 decomposition in ADR-0082 supersedes
conflicting older text here, including any automatic-policy prerequisite for
explicit decisions or economic research. S2A explicit durable identity is DESIGN
FROZEN / implementation candidate after dedicated SPEC-0083 authorization.
S2B automatic policy is HOLD / UNAVAILABLE. Both future writers must use one
append-only decision universe and organization-global cardinality, with exact
relation corrections and no stable-subject mutation. Current V3 remains
required; present unequal integration reference conflicts, equal corroborates,
missing is neutral for independently authorized explicit intent only. Exact
canonical target/promotion/base-source joins are server-resolved.

SPEC-0083 is the closed zero-grant infrastructure implementation package.
Identity schema/writer and HTTP wiring are not selected yet. Authorization must
be revalidated immediately before insert in the writer's transaction, sharing
the principal lock with revocation, and exact grant semantic lineage retained.
No active grant, bootstrap principal, bearer escalation or policy implementation.
Revision 6 introduced explicit history, 7 corrected missing reference, 8 drafted
command admission, and 9 replaces its unfinished substrate/overbroad engineering
blocker with the dedicated boundary and safe infrastructure selection.

At least one governed, field-proven CONFIRMED S2A pair admits economic basis
research; no S2B prerequisite. ExpectedSaleBasisPolicy remains unfrozen and all
financial evidence gates remain unchanged. S1/V033 PROVEN; S3/C2 HOLD; economic
equivalence/non-zero leakage NOT PROVEN. Real provisioning/field proof HOLD.
Future migration numbers are unreserved: V034 is selected only for command
authorization after inspecting V001–V033, replacing the old monolithic draft.

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

## Objective

Define a fail-closed design for producing governed `SALE / EXPECTED` authority
from durable Omie sales-order evidence without allowing provider evidence,
diagnostic identity, numeric coincidence, workflow state, missing values or
local acquisition order to become financial truth.

S1/V033 implementation and its real-data field proof are complete.

S2, S3 and C2 implementation are not authorized by this revision.

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


## Revision-4 TransactionIdentityBindingPolicy v1

This revision freezes the S2 transaction-binding semantics but does not
authorize V034 implementation.

### Policy scope

```text
TransactionIdentityBindingPolicyV1(
    organizationId,
    mercadoLivreConnectionId,
    omieConnectionId,
    policyVersion,
    bindingMode =
        OMIE_INTEGRATION_ORDER_REFERENCE_EQUALS_ML_ORDER_ID,
    semanticFingerprint
)
```

The policy is an explicit durable governance declaration. It is not inferred
from historical match frequency or created automatically by the resolver.

### Candidate key

```text
candidateExternalOrderId =
    currentOmieV3.integrationOrderReference
```

Automatic v1 binding never uses:

```text
customerOrderReference
sourceOrderOrigin
total amount
dates
SKU/product references
customer data
shipping references
pack references
payment references
```

### Exact textual rule

The candidate external id must be exactly equal to the V022
`external_order_id` after the existing provider-source normalization contracts.

No numeric or fuzzy canonicalization is authorized.

### ML lineage gate

The selected V022 identity must be backed by the exact policy ML connection.

Required lineage:

```text
V021 source observation
    organization = policy organization
    connection   = policy ML connection
    capability   = marketplace-economic.order-source
    external id  = candidateExternalOrderId

V022 occurrence-source promotion
    exact same V021 source coordinates
    outcome = PROMOTED | DUPLICATE
    marketplace_order_id = selected identity

V022 identity registry
    organization = policy organization
    marketplace = mercado-livre
    external_order_id = candidateExternalOrderId
```

Currency disagreement between the V021 source and V022 identity is integrity
failure, not an identity match.

`marketplace-economic.order-source.reacquisition-v1` is excluded from automatic
policy-v1 lineage until a separately governed promotion path gives that
capability equivalent V022 lineage.

### Omie currentness gate

The Omie side must use the current accepted V3 evidence revision for the exact
policy organization and Omie connection.

Required:

```text
integrationOrderReference present
current revision uniquely resolvable
same-revision semantic state coherent
no second current Omie source order using the same candidate external id
```

### Cardinality gate

For one policy scope:

```text
one Omie current source order
<-> one candidate external id
<-> one V022 canonical marketplace order
```

Any one-to-many or many-to-one condition resolves `CONFLICT`.

### Result contract

Automatic `CONFIRMED` requires all of:

```text
explicit current policy
exact policy scope
exact integration-reference equality
exact V021 policy-connection lineage
terminal V022 PROMOTED/DUPLICATE lineage
V022 canonical identity
Omie currentness
one-to-one cardinality
no integrity contradiction
```

Otherwise:

```text
missing proof -> UNRESOLVED
ambiguity / contradictory current policy -> CONFLICT
explicit governed rejection -> REJECTED
```

An equality mismatch alone is not persisted as `REJECTED`.

### Persisted lineage

A persisted `CONFIRMED` decision must bind to:

```text
organization
ML connection
Omie connection
policy version
policy semantic fingerprint

Omie V3:
source order reference
provider revision
raw source fingerprint
semantic evidence fingerprint

ML:
V021 source capability
input progress version
record ordinal
V022 marketplace_order_id
external_order_id

decision revision
decision fingerprint
supersession predecessor when applicable
```

No caller-supplied lineage field can substitute for a durable join.

### Policy lifecycle

Policies and decisions are append-only/versioned.

A new policy version supersedes an older policy version explicitly.

More than one unsuperseded effective policy for the same connection pair is
`CONFLICT`.

Policy supersession is prospective. It never rewrites historical decisions.

A materially changed Omie revision requires a new decision revision.

### ExpectedSaleBasisPolicy gate ordering

ExpectedSaleBasisPolicy is no longer a precondition for S2 implementation.

It remains mandatory before S3.

Revised sequence:

```text
S1 proven
-> TransactionIdentityBindingPolicy v1 frozen
-> Revision-4 adversarial review
-> S2 implementation
-> S2 real-data identity proof
-> governed pair corpus
-> ExpectedSaleBasisPolicy research/freeze
-> S3
-> C2
```

This sequencing change does not weaken the financial gate. It strengthens it by
requiring governed cross-system identities before economic-basis comparison.

### Holds after Revision 4

```text
S2 / V034 implementation = HOLD pending Revision-4 adversarial review
ExpectedSaleBasisPolicy  = UNFROZEN / RESEARCH ONLY
S3                       = HOLD
C2                       = HOLD
```

## Revision-3 real-data amendment

Revision 3 incorporates the completed S1/V033 field proof.

### S1 completion

The exact V3 acquisition boundary has proven:

```text
historical v0 / v1 / v2 immutable
V3 base rows    = 141
V3 sidecar rows = 141
V3 line rows    = 196
V3 scope        = one organization + one Omie connection
V3 progress     = exhausted
same-revision semantic conflicts = 0
offline exhausted replay = idempotent
```

Raw provider fingerprint and versioned semantic-evidence fingerprint remain
separate contracts.

### Provider origin semantics

`sourceOrderOrigin` is provider provenance.

It is not a transaction-binding primitive and must not be used as a precondition
for automatic identity confirmation.

Observed real distribution:

```text
API = 124
ERP = 17
MLV = 0
```

Required invariant:

```text
origin evidence
!= transaction identity authority
```

No rule may infer that an Omie order belongs to Mercado Livre because the origin
equals `MLV`, nor reject a possible ML relation because origin is `API` or `ERP`.

### Reference-lineage correction

The real 58.28 candidate has one exact, unambiguous V022 diagnostic relation.

Durable lineage across v0/v1/v2/v3 proves:

```text
integration reference matches canonical ML external reference:
4 generations

customer reference matches canonical ML external reference:
0 generations
```

The historical F2B statement that customer-reference matching was true is
superseded.

This does not freeze the integration reference as identity authority.

Automatic S2 still requires a versioned, connection-scoped
`TransactionIdentityBindingPolicy` or an explicit governed confirmation.

### Missing source evidence

Real V3 evidence includes no explicit `encerrado`, `market_place.nTaxa` or
`market_place.nEnvio` for the 141 acquired orders.

Therefore:

```text
missing encerrado != false
missing nTaxa     != 0
missing nEnvio    != 0
```

A later lifecycle or ExpectedSaleBasisPolicy may qualify only source shapes it
can prove. It must fail closed for required missing inputs rather than inventing
defaults.

### Replay boundary

The final replay was performed after removal of the temporary bootstrap network.

At replay time:

```text
API network count = 1
remaining network = Docker internal
new committed pages = 0
new records = 0
already-committed result >= 1
V3 evidence digest unchanged
historical v0/v1/v2 digest unchanged
```

Provider network availability during bootstrap does not count as replay proof.
Only the post-isolation invocation is admissible for the idempotency gate.

### Post-S1 state

```text
S1 / V033 = PROVEN

TransactionIdentityBindingPolicy research/freeze = NEXT
ExpectedSaleBasisPolicy research/freeze          = NEXT

S2 = HOLD
S3 = HOLD
C2 = HOLD
```

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

S1/V033 is proven by the completed real-data field gate.

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
