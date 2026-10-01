# SPEC-0089 - S2A attestation consumption and attested command authority

## Status

REVISION 9 IMPLEMENTATION-EXACT CONTRACT CANDIDATE.

Source decision: ADR-0089.

Baseline:

```text
6d801beb7491a6546c0bad3835a876386cdc6767
```

This specification authorizes contract review only.

It does not authorize V042 implementation, migration execution, real command authority, provider interaction, production secret handling, transaction-identity execution, or a real field proof.

## Invariants

```text
V040 GOVERNANCE != COMMAND AUTHORITY
V041 ACCEPTED EVIDENCE != COMMAND AUTHORITY
V041 HISTORICAL ACCEPTANCE != CURRENT ELIGIBILITY
V042 CONSUMPTION != EXECUTION
COMMAND AUTHORITY != WRITER EXECUTION
EVIDENCE != AUTHORITY
FAIL CLOSED
```

## Existing frozen inputs

V042 consumes without redefining V034 command authority, V037 operation replay, the governed transaction-identity writer, V040 approval governance, V041 accepted-attestation evidence, and SPEC-0088 canonical/signature/evidence/lifecycle contracts.

## Strict canonical decoder

V042 requires exactly one canonical decoder authority for the retained ApprovalManifest v1 bytes.

Semantic operation:

```text
ApprovalManifestCanonicalCodec.decodeCanonicalManifestBytes(bytes)
    -> ApprovalManifest
```

The final implementation name may follow repository conventions, but there must not be competing decoders.

After decoding:

```text
ApprovalManifestCanonicalCodec.canonicalManifestBytes(decoded)
contentEquals
originalCanonicalManifestBytes
```

must be true.

The decoder must consume exactly one complete record, reject trailing bytes, length overflow, malformed UTF-8, invalid scalar values, non-NFC text, forbidden controls, noncanonical UUID/timestamp/enum/integer/nullable representation, silent normalization, trimming, repair, coercion, or defaults.

## Immutable V041 artifact input

V042 loads by `organizationId + manifestId` the immutable artifact containing at least:

```text
artifactVersion
canonicalizationVersion
canonicalManifestBytes
manifestDigest
canonicalSignaturePreimageBytes
algorithmId
signerKeyId
signerKeyRevision
signerKeyFingerprint
signerKeyLineageFingerprint
subjectPublicKeyInfoDer
signatureBytes
signerAuthorityId
signerAuthorityRevision
signerAuthorityFingerprint
verifiedAt
acceptedProofFingerprint
```

Organization and manifest identity must be derived from the canonical manifest and match the accepted row.

## Cryptographic reverification

For every V042 consumption or command-authority mutation:

```text
1. strict decode canonicalManifestBytes
2. byte-identical decode/re-encode check
3. recompute SHA-256 manifest digest
4. compare stored manifestDigest
5. reconstruct canonical signature preimage
6. compare stored signature preimage
7. recompute SHA-256 SPKI fingerprint
8. compare stored key fingerprint
9. reconstruct AcceptedAttestationProof
10. recompute accepted-proof fingerprint
11. compare stored acceptedProofFingerprint
12. verify Ed25519 using Java 21 JCA
13. require true
```

```text
POSTGRES_ED25519_AUTHORITY = NO
JAVA_21_JCA_ED25519_AUTHORITY = YES
```

## Historical governance references

The proof must resolve its exact immutable historical signer-key and signer-authority revisions/fingerprints. Historical integrity is distinct from current eligibility.

## Current key eligibility

Under the frozen V040 key lock, V042 resolves one unambiguous current effective leaf.

At execution time the key must be `ACTIVE`, satisfy `validFrom <= executionTime` and `effectiveAt <= executionTime`, and satisfy the frozen non-reactivation lineage rules.

RETIRED, REVOKED, COMPROMISED, future-effective, missing, or ambiguous state denies.

## Current signer-authority eligibility

Under the V040 authority-scope lock, exactly one current leaf must match the exact organization, signer subject, signer key, `S2A_FIELD_PROOF_APPROVAL`, `TRANSACTION_IDENTITY_DECISION_WRITE`, be `ENABLED`, and be within its validity window.

Missing, stale, forked, disabled, expired, future, ambiguous, or scope-mismatched authority denies.

## Approval window

The decoded manifest must satisfy:

```text
approvalWindowStart <= executionTime
executionTime < approvalWindowEnd
```

`verifiedAt` does not extend the window.

## Target

Target values are derived from the retained canonical manifest.

Request-side values are claims that must equal the manifest; they cannot override it.

Exact approval target includes organization, ML connection, Omie connection, source order reference, integration reference, marketplace order, permission, and evidence-binding fingerprint.

Only `TRANSACTION_IDENTITY_DECISION_WRITE` is permitted.

## Durable evidence

V042 independently rederives the frozen `FLOOOW:S2A:EVIDENCE-BINDING:1` fingerprint from durable repository evidence.

A request-supplied fingerprint never establishes currentness.

Mismatch means DENY and NEW_APPROVAL_REQUIRED.

Writer currentness remains an independent final gate.

## Physical consumption contract

V042 introduces immutable:

```text
s2a_attestation_consumption
```

Frozen logical fields:

```text
organization_id uuid NOT NULL
manifest_id uuid NOT NULL
manifest_digest char(64) NOT NULL
principal_id uuid NOT NULL
correlation_id uuid NOT NULL
consumed_at timestamptz(6) NOT NULL server-owned
```

Identity:

```text
PRIMARY KEY (organization_id, manifest_id)
```

It references the exact accepted-attestation identity and the exact command principal.

There is no mutable consumed flag. UPDATE and DELETE must fail closed.

The exact DDL and index set remain implementation work subject to independent review.

## Authority-operation linkage

V042 adds nullable historical-compatible:

```text
command_authority_operation.attestation_manifest_id uuid NULL
```

When non-null, organization + manifest linkage resolves the corresponding consumption.

Pre-V042 historical/synthetic rows may remain NULL.

Real S2A `PRINCIPAL`, `INITIAL_CREDENTIAL`, and `GRANT` require non-null linkage.

No `APPROVAL` operation is introduced.

The exact uniqueness/index strategy must prove that one manifest cannot fork the expected linked authority lineage.

## Attested principal creation

First consumption uses one caller-owned READ_COMMITTED transaction:

```text
organization FOR SHARE
-> operation-id advisory lock
-> replay check
-> principal advisory lock
-> principal FOR UPDATE if present
-> attestation advisory lock
-> accepted artifact / consumption lookup
-> signer-key advisory lock
-> signer-authority-scope advisory lock
-> historical artifact validation
-> strict manifest reconstruction
-> Java 21 JCA verification
-> current organization/key/authority/window/target/evidence validation
-> insert command_principal
-> insert s2a_attestation_consumption
-> append linked PRINCIPAL operation
-> commit
```

The three mutations are atomic.

Replay semantics:

```text
same manifest + same digest + same principal + same semantic operation
=> idempotent recovery

same manifest + different digest
=> INTEGRITY FAILURE

same manifest + different principal
=> DENY

same operation ID + changed semantic intent
=> INTEGRITY FAILURE
```

## Initial credential

INITIAL_CREDENTIAL requires the existing accepted attestation, existing consumption, same organization/manifest/principal, fresh artifact reverification, fresh execution eligibility, and exact replay semantics.

It may append only the legal V034/V037 initial credential lineage.

It cannot alter consumption or create another principal.

No raw credential, token, private key, or secret verifier source material may enter accepted or consumption evidence.

## Grant

GRANT requires the same accepted attestation/consumption/principal and fresh eligibility.

Permission must equal `TRANSACTION_IDENTITY_DECISION_WRITE`.

POLICY_ADMIN denies.

The authority-operation receipt carries the attestation linkage.

## Rotation and revocation

The original field-proof manifest does not authorize `ROTATE_CREDENTIAL` or `REVOKE`.

Those require separately accepted operational authority for a real path.

## Issuer hardening

Migration V042 must remove practical direct authority-table mutation from `flooow_command_issuer` for:

```text
command_principal
command_credential_revision
command_permission_grant
command_authority_operation
```

Real S2A mutations are available only through narrow attestation-aware capabilities.

No generic SQL, arbitrary table mutation, arbitrary operation type, arbitrary permission, arbitrary manifest substitution, or arbitrary principal substitution is permitted.

PUBLIC EXECUTE is revoked. Runtime, verifier, and approval-governance roles cannot execute issuer capabilities. Protected role-graph contamination fails closed.

## Role separation

Protected roles remain distinct:

```text
flooow_approval_governance
flooow_attestation_verifier
flooow_command_issuer
flooow_command_runtime
```

Issuer and verifier authority must not be merged.

## Final writer admission

The transaction-identity writer is the final execution authority.

The writer transaction must authenticate current command credential, authorize current DECISION_WRITE grant, resolve exact attestation consumption, reload/reconstruct/reverify the artifact, re-resolve current organization/key/authority/window/target/evidence eligibility, run the existing transaction-identity currentness rules, recheck command authorization immediately before immutable insert, then commit the immutable decision.

A helper may factor work but must not weaken transaction lock ownership.

## Race semantics

Required:

```text
revocation/disable commits first
=> later admission denied

execution admission obtains required fence first
=> conflicting lifecycle mutation waits

execution decision commits first
=> later lifecycle mutation does not rewrite historical decision
```

Tests must prove real PostgreSQL serialization/blocking behavior.

## Zero-effect requirements

Failed first consumption:

```text
s2a_attestation_consumption delta = 0
command_principal delta = 0
command_credential_revision delta = 0
command_permission_grant delta = 0
command_authority_operation delta = 0
marketplace_transaction_identity_decision delta = 0
marketplace_transaction_identity_head delta = 0
```

Later INITIAL_CREDENTIAL/GRANT failure leaves no partial revision/operation.

Final writer denial:

```text
IDENTITY_DECISION_DELTA = 0
IDENTITY_HEAD_DELTA = 0
```

Previously committed immutable consumption/authority is not retroactively deleted merely because later execution is denied.

## Mandatory adversarial matrix

Implementation must prove:

- valid strict decode and byte-identical round trip;
- truncated/oversized/trailing/malformed/noncanonical representations deny;
- manifest/digest/preimage/SPKI/key-fingerprint/signature/proof-fingerprint tampering denies;
- historical key/authority reference mismatch denies;
- inactive organization denies;
- retired/revoked/compromised/future/ambiguous/missing key denies;
- disabled/expired/future/forked/missing/mismatched authority denies;
- expired/future approval denies;
- every target mismatch denies;
- POLICY_ADMIN denies;
- changed durable evidence denies;
- request fingerprint cannot replace durable derivation;
- first principal consumption applies once;
- exact replay is idempotent;
- changed intent conflicts;
- second principal root denies;
- concurrent duplicates create one root;
- uncertain commit retry cannot create a second root;
- initial credential/grant cannot cross manifest or principal;
- issuer direct DML is denied for all authority tables;
- runtime/verifier/governance/PUBLIC privilege escalation is denied;
- contaminated role graph denies;
- narrow attested capability succeeds only after all gates;
- rollback at every mutation boundary leaves no partial state;
- writer denies when lifecycle/window/evidence/command authority becomes ineligible;
- admitted writer serializes conflicting revoke/disable;
- no provider/network activity occurs under governance/authority locks.

## Kill rules

Stop implementation on any remaining direct issuer bypass, V041-row shortcut, permissive parsing, duplicate manifest authority source, missing writer fence, second-root path, cross-consumption credential/grant path, POLICY_ADMIN path, generic mutation capability, privilege crossover, partial transaction, provider/network call under protected locks, secret persistence, PostgreSQL-Ed25519 claim, or real field execution before separate authorization.

## Future implementation scope

Expected reviewed surfaces include the canonical codec/decoder, bounded V042 domain/service contract, bounded PostgreSQL issuer replacement, command authorization/writer integration, V042 migration, and focused decoder/database/writer adversarial tests.

The exact file list must be frozen by a separate implementation blueprint before code changes.

## Revision 1 state

```text
REVISION_1_SELF_CLASSIFICATION = SUPERSEDED
REVISION_1_ADVERSARIAL_REVIEW = FAILED

REVISION_2_CORRECTIONS = MATERIALIZED
REVISION_2_ADVERSARIAL_REVIEW = PENDING

V042_IMPLEMENTATION = HOLD
V042_MIGRATION = HOLD
REAL_FIELD_PROOF = HOLD

GIT_ADD = NO
GIT_COMMIT = NO
GIT_PUSH = NO
```

## Revision 2 controlling corrections

This section supersedes conflicting Revision 1 wording.

Revision 1 failed adversarial review. The following contracts are mandatory
before any implementation blueprint may pass.

### Issuer TCB and two-phase capability contract

The V042 issuer TCB is:

```text
dedicated V042 issuer process
+ Java 21 JCA
+ flooow_command_issuer capability
+ one READ_COMMITTED JDBC transaction
+ locked V040/V041/V042 snapshot
```

Do not grant broad direct V040/V041 table SELECT to the issuer.

V042 requires a narrow non-mutating snapshot capability and narrow
single-purpose apply capabilities.

The snapshot capability acquires frozen locks, loads the immutable accepted
artifact, resolves historical references, resolves current
organization/key/authority state, rederives durable evidence, captures
server-owned executionTime, and returns only the nonsecret verification
snapshot.

Java performs canonical reconstruction, fingerprint checks, and Ed25519 JCA
verification on the same connection and transaction.

The apply capability re-resolves the snapshot while the same locks remain
held, compares every security-relevant expected field, and only then performs
the exact authority mutation.

PostgreSQL does not independently prove JCA execution. The dedicated issuer
process identity is part of the trusted computing boundary.

Exact capability names and SQL signatures are frozen in the implementation
blueprint before code.

### Writer TCB and narrow runtime eligibility capability

The final governed writer uses:

```text
dedicated writer process
+ Java 21 JCA
+ flooow_command_runtime capability
+ existing READ_COMMITTED writer transaction
+ narrow V042 execution-eligibility snapshot capability
```

The runtime role receives no broad V040/V041 SELECT grant.

The capability performs no command-authority or identity mutation. It returns
the exact locked artifact/currentness snapshot required for Java
reverification and writer admission.

### Exact writer lineage resolution

Writer attestation resolution is GRANT-lineage based.

Starting from the authorized `CommandAuthorizationLineage`, require exactly
one linked operation:

```text
operation = GRANT
organization_id = actor.organizationId
principal_id = actor.principalId
grant_id = authorization.grantId
grant_revision = authorization.grantRevision
permission = authorization.permission
state = ENABLED
attestation_manifest_id IS NOT NULL
```

Then require:

```text
linked manifest
-> exact s2a_attestation_consumption
-> consumption.principal_id = actor.principalId
-> exact immutable s2a_accepted_attestation
```

Principal-only attestation lookup is forbidden.

Zero matching linked GRANT rows means denial.

Multiple matching linked GRANT rows means integrity failure.

### Physical linked-operation uniqueness

Preserve the SPEC-0088 rule:

```text
UNIQUE (
    organization_id,
    attestation_manifest_id,
    operation
)
WHERE attestation_manifest_id IS NOT NULL
  AND operation IN ('PRINCIPAL','INITIAL_CREDENTIAL','GRANT')
```

or exact-equivalent PostgreSQL DDL proven by schema tests.

Additionally, one immutable real S2A grant row may have only one linked GRANT
receipt. The implementation blueprint must freeze a database-enforced partial
unique rule for that target.

Application-only duplicate detection is insufficient.

### Correct key-time semantics

Do not equate structural leaf with effective revision.

Under the key lock V042 proves:

```text
structural lineage valid
structural leaf count = 1
```

and separately selects:

```text
effective key revision
= highest revision with effective_at <= executionTime
```

The effective revision may be an ancestor of a future structural leaf.

Require:

```text
effective.valid_from <= executionTime
effective.state = ACTIVE
```

The current signer-authority leaf must bind the exact effective key revision
and fingerprint.

### Exact current authority scope

Current authority eligibility requires all of:

```text
organizationId
signerSubjectId
signerRole = S2A_FIELD_PROOF_APPROVER
signerKeyId
signerKeyRevision = effective key revision
signerKeyFingerprint = effective key fingerprint
approvalAction = S2A_FIELD_PROOF_APPROVAL
permission = TRANSACTION_IDENTITY_DECISION_WRITE
approvalSourceId = decoded manifest.approvalSource
state = ENABLED
validFrom <= executionTime
executionTime < validUntil
```

### Server-owned executionTime

For every new V042 effect:

```text
executionTime = transaction_timestamp()::timestamptz(6)
```

It is captured from the same transaction and reused for all V042 temporal
checks.

Caller-supplied executionTime is prohibited.

### Replay state machine

Replay classification occurs before fresh currentness checks.

```text
operation-ID lock
-> existing operation lookup

exact existing intent + exact attestation linkage
=> AlreadyApplied(existing immutable receipt)
=> no writes
=> historical replay does not require current eligibility

existing operation with changed intent or linkage
=> IntegrityFailure
=> no writes

no existing operation
=> fresh artifact + currentness + apply path
```

For PRINCIPAL, a consumption without the matching immutable PRINCIPAL operation
is integrity failure because first consumption/principal/receipt are atomic.

For INITIAL_CREDENTIAL or GRANT, existing consumption must match the same
manifest and principal.

### Post-V042 legacy issuer behavior

The direct-SQL issuer adapter is not a permitted real operational fallback
after V042 hardening.

Real S2A PRINCIPAL, INITIAL_CREDENTIAL, and GRANT use only attestation-aware
capabilities.

ROTATE_CREDENTIAL and REVOKE do not inherit the field-proof manifest and remain
unavailable to the real path until a separate operational-authority contract
and narrow capability pass review.

No direct DML privilege may be retained merely for compatibility with the
legacy adapter.

### Consumption value provenance

```text
s2a_attestation_consumption.manifest_digest
= recomputed/accepted artifact manifest digest

s2a_attestation_consumption.correlation_id
= decoded manifest correlationId

s2a_attestation_consumption.consumed_at
= transaction_timestamp()::timestamptz(6)
```

Caller override is prohibited.

### Semantic outcome classification

Freeze these semantic classes:

```text
Applied
AlreadyApplied
InvalidSignature
UnsupportedCanonicalForm
ScopeMismatch
ExpiredOrNotYetValid
GovernanceUnavailable
GovernanceConflict
IntegrityFailure
```

No unknown SQLSTATE, infrastructure error, deadlock, or connection failure may
be converted into `AlreadyApplied`, `Applied`, or ordinary denial.

Exact Kotlin names and SQLSTATE values are frozen in the implementation
blueprint before code changes.

### Additional adversarial proofs

Revision 2 adds mandatory proofs:

- issuer role has no broad direct V040/V041 table SELECT;
- issuer snapshot and apply run on the same JDBC connection and transaction;
- direct apply with mismatched expected snapshot fails closed;
- runtime role has no broad V040/V041 SELECT;
- writer resolves manifest through exact authorized GRANT lineage;
- principal-only attestation lookup is rejected;
- duplicate linked GRANT receipt is database-rejected;
- future key successor does not replace the effective revision before
  `effective_at`;
- approvalSource mismatch denies;
- signerRole mismatch denies;
- exact committed replay returns the historical receipt after later
  expiry/revocation/disablement;
- conflicting replay is classified before fresh currentness evaluation;
- legacy direct issuer methods cannot mutate protected authority tables after
  V042;
- caller-supplied consumption digest/correlation/time cannot alter stored
  values.

### Revision 2 gate

```text
REVISION_1_ADVERSARIAL_REVIEW = FAILED
REVISION_2_CORRECTIONS = MATERIALIZED
REVISION_2_ADVERSARIAL_REVIEW = PENDING

V042_IMPLEMENTATION = HOLD
V042_MIGRATION = HOLD
REAL_FIELD_PROOF = HOLD

GIT_ADD = NO
GIT_COMMIT = NO
GIT_PUSH = NO

NEXT_GATE = V042_REVISION_2_CONTRACT_PACKAGE_ADVERSARIAL_REVIEW
```

## Revision 3 controlling corrections

This section supersedes conflicting Revision 1 and Revision 2 wording.

Revision 2 failed adversarial review.

### Runtime INSERT removal

V042 migration must revoke direct operational decision INSERT:

```sql
REVOKE INSERT
ON public.marketplace_transaction_identity_decision
FROM flooow_command_runtime;
```

The exact migration may combine this with other privilege normalization, but
the resulting deployment-equivalent privilege test must prove:

```text
runtime direct decision INSERT = DENIED
runtime narrow attested decision apply = ALLOWED only after all V042 gates
```

No production/runtime membership may restore the direct INSERT capability.

### Narrow attested decision apply capability

The real S2A writer persists a new decision only through one narrowly scoped
SECURITY DEFINER capability.

It is fixed to the transaction-identity decision contract and performs no
arbitrary SQL.

Before INSERT it independently proves:

```text
caller has flooow_command_runtime capability
authorized grant is current
exact linked GRANT operation exists
linked manifest is non-null
exact consumption exists
consumption principal matches actor principal
exact accepted artifact exists
expected V042 snapshot still matches
final current organization eligibility
final effective key eligibility
final signer-authority eligibility
final approval-window eligibility
final exact target
final durable evidence binding
one-explicit-action invariant
```

It then inserts through the existing decision table so all V035/V036 trigger
validation and immutable head semantics still execute.

PUBLIC, issuer, verifier, and approval-governance roles receive no execute
authority.

### One-action real field-proof state machine

The first S2A field proof permits exactly one new transaction-identity effect.

New real S2A decision requirements:

```text
kind = CONFIRMED
revision = 1
supersedes_decision_id IS NULL
permission = TRANSACTION_IDENTITY_DECISION_WRITE
```

The authorized real S2A grant is single-decision.

Under the existing principal lock and before new INSERT:

```sql
SELECT count(*)
FROM public.marketplace_transaction_identity_decision
WHERE organization_id = <organization>
  AND grant_id = <authorized real S2A grant>;
```

must resolve to zero for a new effect.

A nonzero count for a different decision identity is an integrity failure.

The exact same committed `decisionId` is handled by the existing replay path
before V042 new-effect admission.

This preserves the frozen four-table S2A physical model. No additional S2A
execution table is introduced by V042.

### Writer ordering

For `PostgresTransactionIdentityWriter` the controlling order is:

```text
authenticate credential

authorizeForWrite
  -> organization fence
  -> principal FOR UPDATE
  -> current credential
  -> current grant

compute existing writer intent

decision-ID advisory lock

existing decision lookup

IF exact existing:
    return AlreadyApplied
    no V042 fresh-currentness check

IF changed existing:
    return IntegrityFailure

IF new:
    resolve linked GRANT -> manifest -> consumption -> accepted artifact
    acquire V042 attestation/key/authority locks
    obtain V042 nonsecret snapshot
    strict canonical reconstruction
    Java 21 JCA Ed25519 verify
    run existing writer evidence/currentness logic
    final authorizeForWrite
    invoke narrow V042 decision apply capability
        -> capture fresh effectTime
        -> revalidate V042 currentness
        -> rederive evidence binding
        -> enforce one-action rule
        -> INSERT immutable decision
        -> existing triggers/head logic run
    return Applied
```

The same ordering applies to attempts entering the real S2A field-proof path.

`WITHDRAWN` and `REJECTED` are denied by that real-path capability.

Existing non-S2A historical behavior is not evidence of authorization for a
new production path.

### Final effect-time semantics

For a new effect the final apply capability uses:

```text
effectTime = clock_timestamp()::timestamptz(6)
```

not `transaction_timestamp()`.

`effectTime` is database-owned and cannot be supplied by Java.

The final apply statement uses the same `effectTime` value for all temporal
eligibility checks in that effect.

For first principal consumption:

```text
consumed_at = effectTime
```

For INITIAL_CREDENTIAL and GRANT, final V042 temporal eligibility is evaluated
at their respective apply `effectTime`.

For final transaction-identity insertion, final V042 temporal eligibility is
evaluated at its own apply `effectTime` immediately before INSERT.

### Attested command-authority intent v2 exact contract

Historical v1 remains unchanged.

V042 real attested operations use lowercase hexadecimal SHA-256 over the
existing decimal-byte-length framing with:

```text
domain = controlled-command-authority/2
```

Exact ordered values:

```text
PRINCIPAL:
domain
principal
operationId
organizationId
principalId
mercadoLivreConnectionId
omieConnectionId
reason
provenance
correlationId
manifestId
acceptedProofFingerprint
manifestDigest
```

```text
INITIAL_CREDENTIAL:
domain
initial-credential
operationId
organizationId
principalId
credentialId
credentialVerifierDigestLowerHex
reason
provenance
correlationId
manifestId
acceptedProofFingerprint
manifestDigest
```

```text
GRANT:
domain
grant
operationId
organizationId
principalId
grantId
TRANSACTION_IDENTITY_DECISION_WRITE
reason
provenance
correlationId
manifestId
acceptedProofFingerprint
manifestDigest
```

Framing for each value is:

```text
<decimal UTF-8 byte length>:<UTF-8 value>
```

with no separator between framed values.

`acceptedProofFingerprint` is the exact V041
`s2a_accepted_attestation.accepted_proof_fingerprint`.

`manifestDigest` is the independently recomputed and stored exact V041
manifest digest.

`reason`, `provenance`, and `correlationId` come from the decoded signed
manifest.

The database independently recomputes and compares the v2 intent before
mutation.

Existing receipt fingerprint semantics remain
`controlled-command-authority-receipt/1` and receive the v2 intent digest as
the intent field.

Golden vectors for all three v2 intent kinds are mandatory before
implementation is authorized.

### Exact physical consumption/operation principal binding

Consumption requires both:

```text
PRIMARY KEY (organization_id, manifest_id)

UNIQUE (organization_id, manifest_id, principal_id)
```

The latter exists only to support exact-principal referential enforcement.

Linked real authority operation requires:

```text
FOREIGN KEY (
    organization_id,
    attestation_manifest_id,
    principal_id
)
REFERENCES public.s2a_attestation_consumption (
    organization_id,
    manifest_id,
    principal_id
)
```

Historical NULL attestation links remain legal.

Required database uniqueness also includes:

```text
one linked operation per
organization + manifest + operation
for PRINCIPAL / INITIAL_CREDENTIAL / GRANT
```

and:

```text
one linked GRANT authority-operation receipt
per immutable real grant identity
```

The implementation blueprint must provide exact index names and predicates.

### Typed attested issuer contract

Do not add optional `manifestId` or optional attestation parameters to the
legacy `ControlledCommandAuthorityIssuer` request types.

Real V042 provisioning uses a separate typed interface whose PRINCIPAL,
INITIAL_CREDENTIAL, and GRANT requests require non-null:

```text
manifestId
```

and whose implementation resolves manifestDigest and acceptedProofFingerprint
from the immutable accepted artifact rather than accepting them as mutable
launcher authority.

The manifest-derived reason, provenance, correlation, target, and permission
are not caller-overridable.

### Revision 3 adversarial additions

Mandatory tests now include:

- runtime direct `marketplace_transaction_identity_decision` INSERT denied;
- runtime attested apply succeeds only after Java snapshot path and DB recheck;
- second decisionId using the same real S2A grant denied;
- concurrent different decisionIds using the same S2A grant yield one applied
  and one integrity failure;
- exact committed decision replay with a currently authorized actor remains
  `AlreadyApplied` after later attestation expiry/key revocation/authority
  disablement;
- revoked command grant still denies before replay, preserving V036/V039
  semantics;
- long transaction crossing approval expiry is denied by fresh final
  `clock_timestamp()` effectTime;
- future key effective boundary crossed before apply is re-evaluated at final
  effectTime;
- operation-to-consumption cross-principal link is rejected by PostgreSQL;
- v2 PRINCIPAL/INITIAL_CREDENTIAL/GRANT intent golden vectors match Kotlin and
  PostgreSQL;
- changing manifestId, acceptedProofFingerprint, or manifestDigest changes the
  v2 intent digest;
- legacy v1 synthetic fingerprints remain byte-for-byte unchanged;
- nullable-attestation legacy request types cannot enter the real V042 path.

### Revision 3 gate

```text
REVISION_2_ADVERSARIAL_REVIEW = FAILED
REVISION_3_CORRECTIONS = MATERIALIZED
REVISION_3_ADVERSARIAL_REVIEW = PENDING

V042_IMPLEMENTATION = HOLD
V042_MIGRATION = HOLD
REAL_FIELD_PROOF = HOLD

GIT_ADD = NO
GIT_COMMIT = NO
GIT_PUSH = NO

NEXT_GATE = V042_REVISION_3_CONTRACT_PACKAGE_ADVERSARIAL_REVIEW
```

## Revision 4 controlling corrections

This section supersedes conflicting Revision 1 through Revision 3 wording.

Revision 3 failed adversarial review.

### Exact credential-operation referential contract

Add a referenced unique tuple equivalent to:

```sql
UNIQUE (
    organization_id,
    credential_id,
    revision,
    principal_id,
    state
)
```

on `command_credential_revision`.

Add an exact operation FK equivalent to:

```sql
FOREIGN KEY (
    organization_id,
    credential_id,
    credential_revision,
    principal_id,
    state
)
REFERENCES public.command_credential_revision (
    organization_id,
    credential_id,
    revision,
    principal_id,
    state
)
```

This makes INITIAL_CREDENTIAL/ROTATE target identity, revision, principal and
state database-verifiable.

### Exact grant-operation referential contract

Add a referenced unique tuple equivalent to:

```sql
UNIQUE (
    organization_id,
    grant_id,
    revision,
    principal_id,
    permission,
    state
)
```

on `command_permission_grant`.

Add an exact operation FK equivalent to:

```sql
FOREIGN KEY (
    organization_id,
    grant_id,
    grant_revision,
    principal_id,
    permission,
    state
)
REFERENCES public.command_permission_grant (
    organization_id,
    grant_id,
    revision,
    principal_id,
    permission,
    state
)
```

This makes GRANT/REVOKE target identity, revision, principal, permission and
state database-verifiable.

The existing narrower V037 foreign keys may remain if harmless, but they
cannot be the sole V042 integrity proof.

### Exact linked-consumption principal contract

The Revision 3 composite operation-to-consumption FK remains mandatory:

```text
organization_id
attestation_manifest_id
principal_id
```

must resolve the exact:

```text
organization_id
manifest_id
principal_id
```

consumption tuple.

Together with the exact credential/grant FKs, the operation ledger cannot
cross either the consumption principal or the referenced authority target.

### Attested intent computation authority

For real V042 operations:

```text
Kotlin v2 intent computation = independent cross-check
PostgreSQL v2 intent computation = persistence authority
```

The PostgreSQL capability reconstructs the Revision 3 exact
`controlled-command-authority/2` preimage from validated values and stores its
own lowercase SHA-256 result.

Caller-provided `intent_fingerprint` may be accepted only as an expected
cross-check value. It is never directly persisted without comparison.

### Receipt fingerprint computation authority

For real V042 operations:

```text
domain = controlled-command-authority-receipt/1
```

Exact ordered values:

```text
domain
intentFingerprint
operation.name
principalId
credentialId-or-empty
credentialRevision-or-empty
grantId-or-empty
grantRevision-or-empty
permission.name-or-empty
state-or-empty
```

Each value uses the same existing framing:

```text
<decimal UTF-8 byte length>:<UTF-8 value>
```

with no separator between framed values.

PostgreSQL computes and persists the receipt fingerprint.

Kotlin must reproduce the same fixed golden vectors.

### Replay verification algorithm

Under the operation-ID advisory lock:

```text
load operation row

IF missing:
    continue new-effect path

IF present:
    validate exact operation kind
    validate exact principal
    validate exact target IDs/revisions
    validate exact permission/state
    validate exact correlation
    validate exact attestation manifest
    validate operation-to-consumption principal FK lineage
    validate accepted artifact identity
    validate exact credential/grant target tuple
    recompute attested v2 intent
    recompute receipt v1
```

Then:

```text
all exact
=> AlreadyApplied
=> zero writes
=> historical receipt returned

any mismatch
=> IntegrityFailure
=> zero writes
```

Fresh organization/key/authority/window/evidence eligibility is not required
for an exact already-committed operation replay.

Stored fingerprint equality alone is insufficient replay proof.

### Post-V042 issuer privilege matrix

The implementation blueprint must materialize and test an explicit
deployment-equivalent matrix.

For `flooow_command_issuer`:

```text
command_principal direct DML = NO
command_credential_revision direct DML = NO
command_permission_grant direct DML = NO
command_authority_operation direct DML = NO

s2a_signer_key_revision direct SELECT/DML = NO
s2a_signer_authority_revision direct SELECT/DML = NO
s2a_accepted_attestation direct SELECT/DML = NO
s2a_attestation_consumption direct SELECT/DML = NO

V042 issuer snapshot EXECUTE = YES
V042 PRINCIPAL apply EXECUTE = YES
V042 INITIAL_CREDENTIAL apply EXECUTE = YES
V042 GRANT apply EXECUTE = YES
```

`PUBLIC`, runtime, verifier, and approval-governance receive no issuer-apply
execution privilege.

Any existing direct V037 issuer grant inconsistent with this matrix is revoked
inside V042.

### Migration preflight contract

Before adding exact target FKs and before privilege cutover, V042 migration
must inspect all existing `command_authority_operation` rows.

Credential operations must match a credential row on:

```text
organization
credentialId
credentialRevision
principalId
state
```

Grant/revoke operations must match a grant row on:

```text
organization
grantId
grantRevision
principalId
permission
state
```

Any mismatch aborts migration.

The migration must not mutate predecessor authority history to satisfy the new
constraints.

Protected role membership contamination also aborts migration before new
capability grants.

### Additional adversarial proofs

Revision 4 adds:

- operation credential principal mismatch rejected by FK;
- operation credential revision mismatch rejected by FK;
- operation grant principal mismatch rejected by FK;
- operation grant revision mismatch rejected by FK;
- operation grant permission mismatch rejected by FK;
- operation grant state mismatch rejected by FK;
- replay with stored intent but mutated target tuple is IntegrityFailure;
- replay with valid intent but invalid stored receipt is IntegrityFailure;
- PostgreSQL and Kotlin v2 intent golden vectors match;
- PostgreSQL and Kotlin receipt-v1 golden vectors match for all three attested
  operation kinds;
- Java-provided final intent/receipt value cannot override DB computation;
- V042 migration aborts on inconsistent legacy authority-operation data;
- migration preflight performs no repair;
- issuer has no direct protected-table DML after V042;
- issuer has no broad direct V040/V041/V042 evidence/governance reads;
- only the four narrow issuer capabilities are executable by issuer.

### Revision 4 gate

```text
REVISION_3_ADVERSARIAL_REVIEW = FAILED
REVISION_4_CORRECTIONS = MATERIALIZED
REVISION_4_ADVERSARIAL_REVIEW = PENDING

V042_IMPLEMENTATION = HOLD
V042_MIGRATION = HOLD
REAL_FIELD_PROOF = HOLD

GIT_ADD = NO
GIT_COMMIT = NO
GIT_PUSH = NO

NEXT_GATE = V042_REVISION_4_CONTRACT_PACKAGE_ADVERSARIAL_REVIEW
```

## Revision 5 controlling corrections

This section supersedes conflicting Revision 1 through Revision 4 wording.

Revision 4 failed adversarial review.

### Apply capabilities own their serialization locks

No privileged V042 apply capability may assume the caller already holds
security-relevant locks.

For attested authority apply the capability itself performs the canonical
V042 provisioning lock sequence.

For attested decision apply the capability itself performs the canonical
writer lock sequence through principal/progress/subject/target before testing
whether the real S2A grant has already produced a decision.

This requirement applies even when the normal Kotlin path has already acquired
the same locks.

### Attested decision apply exact lock sequence

For a new real S2A decision, the narrow apply capability obtains/reobtains:

```text
1. organization ACTIVE row FOR SHARE
2. principal row FOR UPDATE
3. transaction-identity decision-ID advisory lock
4. exact Omie V3 progress row FOR UPDATE
5. sorted transaction-identity subject/target advisory locks
6. exact linked GRANT operation
7. exact consumption
8. attestation advisory lock
9. signer-key advisory lock
10. signer-authority-scope advisory lock
11. final effectTime/currentness/evidence checks
12. one-action grant-usage check
13. INSERT decision
```

Steps 1-5 must be semantically equivalent to the frozen
`transaction_identity_locks` contract.

The one-action query occurs after step 2 and while that principal lock remains
held to commit/rollback.

### Split post-V042 runtime apply surface

V042 revokes direct runtime decision INSERT and replaces it with two
single-purpose capabilities.

#### Attested apply

Eligibility requires exactly one matching non-null linked GRANT operation for:

```text
organization
principal
grantId
grantRevision
TRANSACTION_IDENTITY_DECISION_WRITE
ENABLED
```

It then requires exact consumption and accepted-attestation lineage and all
V042 gates.

It permits only the single root CONFIRMED field-proof decision.

#### Legacy-unlinked apply

Eligibility requires:

```text
no matching command_authority_operation
for the authorized grant/grantRevision
with attestation_manifest_id IS NOT NULL
```

It preserves the already frozen V035/V036 database semantics for historical or
synthetic unlinked authority.

It may not create or alter any command-authority or S2A row.

If a matching non-null linked GRANT exists, legacy-unlinked apply must raise a
typed integrity/authorization denial before decision INSERT.

### Runtime privilege matrix after V042

For `flooow_command_runtime`:

```text
direct INSERT marketplace_transaction_identity_decision = NO

legacy-unlinked decision apply EXECUTE = YES
attested decision apply EXECUTE = YES

direct S2A governance/evidence/consumption table DML = NO
issuer apply EXECUTE = NO
verifier apply EXECUTE = NO
approval-governance append EXECUTE = NO
```

The legacy-unlinked capability is the compatibility replacement for the direct
V039 INSERT privilege. Direct INSERT is not restored.

### Deterministic writer route

Routing is derived only from database lineage after current authorization and
decision replay:

```text
linkedCount =
count of exact GRANT authority-operation rows
matching organization + principal + grantId + grantRevision + permission
with attestation_manifest_id IS NOT NULL

linkedCount = 1
=> attested route

linkedCount = 0
=> legacy-unlinked route

linkedCount > 1
=> IntegrityFailure
```

The Revision 3/4 unique constraints should make `>1` impossible for a valid
database, but the application still fails closed if observed.

No request parameter may choose attested versus legacy.

### Exact S2A decision-field binding

For attested apply, require:

```text
command.kind = CONFIRMED
command.reason = EXPLICIT_CONFIRMATION
command.supersedesDecisionId = NULL

command.sourceOrderReference
= decodedManifest.sourceOrderReference

command.marketplaceOrderId
= decodedManifest.marketplaceOrderId

command.provenance
= decodedManifest.provenance

command.correlationId
= decodedManifest.correlationId

actor.mercadoLivreConnectionId
= decodedManifest.mercadoLivreConnectionId

actor.omieConnectionId
= decodedManifest.omieConnectionId
```

The persisted root revision is exactly `1`.

Permission is exactly `TRANSACTION_IDENTITY_DECISION_WRITE`.

Current durable evidence independently validates the manifest
`integrationReference` and evidence-binding fingerprint.

`decisionId` is generated/selected by the ceremony for idempotency and is not
added to ApprovalManifest v1.

### Replay compatibility

Decision replay remains intentionally before fresh V042 admission.

The current command authorization check remains before replay.

Therefore:

```text
revoked/stale command authority
=> denied before replay

currently authorized actor
+ same decisionId
+ same V035/V036 intent
=> AlreadyApplied

same decisionId
+ changed intent/provenance
=> IntegrityFailure
```

Correlation ID remains excluded from the frozen V035/V036 intent hash.

For first attested apply, however, the stored correlation ID must equal the
manifest correlation ID.

A replay with a different retry correlation does not rewrite the stored value.

### Legacy capability regression tests

Revision 5 adds mandatory proof that after direct INSERT revocation:

- an unlinked synthetic CONFIRMED path still satisfies existing V035/V039
  semantics through legacy-unlinked apply;
- an unlinked synthetic REJECTED path remains governed by existing V035
  semantics;
- an unlinked governed V036 WITHDRAWN path remains functional;
- all existing writer replay and grant-revocation tests remain semantically
  unchanged;
- the legacy capability rejects an otherwise valid grant if a matching
  non-null attestation-linked GRANT operation exists.

### Attested direct-call race tests

Without invoking `PostgresTransactionIdentityWriter`, tests must call attested
apply directly from two concurrent runtime-role transactions using the same
linked grant and different decision IDs.

The database must show a real lock waiter.

After release:

```text
decision count for grant = 1
head delta = 1
one caller = applied
one caller = integrity failure
```

No two-success outcome is legal.

### Provisioning apply direct-call tests

Each attested PRINCIPAL, INITIAL_CREDENTIAL, and GRANT apply capability must
also be tested when called directly through its allowed issuer role without a
pre-acquired outer lock.

The capability itself must acquire the documented operation/principal/
attestation/governance locks and preserve exact replay/concurrency semantics.

### Revision 5 gate

```text
REVISION_4_ADVERSARIAL_REVIEW = FAILED
REVISION_5_CORRECTIONS = MATERIALIZED
REVISION_5_ADVERSARIAL_REVIEW = PENDING

V042_IMPLEMENTATION = HOLD
V042_MIGRATION = HOLD
REAL_FIELD_PROOF = HOLD

GIT_ADD = NO
GIT_COMMIT = NO
GIT_PUSH = NO

NEXT_GATE = V042_REVISION_5_CONTRACT_PACKAGE_ADVERSARIAL_REVIEW
```

## Revision 6 controlling corrections

This section supersedes conflicting Revision 1 through Revision 5 wording.

Revision 5 failed adversarial review.

### V042 trusted computing boundary

The implementation contract explicitly mirrors the frozen V041 trust model.

PostgreSQL does not verify Ed25519 and cannot prove that Java JCA executed.

No fake proof token is introduced.

#### Issuer operation

One real V042 issuer operation is:

```text
dedicated issuer service
-> caller-owned READ_COMMITTED JDBC transaction
-> V042 snapshot/lock capability
-> strict canonical reconstruction
-> Java 21 JCA Ed25519 verification
-> V042 single-purpose apply capability
-> commit
```

A failed JCA verification must not invoke apply.

#### Writer operation

One real attested writer operation is:

```text
dedicated governed writer service
-> caller-owned READ_COMMITTED JDBC transaction
-> current command authorization
-> frozen writer locks/evidence
-> V042 attestation/governance snapshot
-> strict canonical reconstruction
-> Java 21 JCA Ed25519 verification
-> final command authorization
-> attested decision apply
-> commit
```

A failed JCA verification must not invoke attested decision apply.

### Capability identity

`flooow_command_issuer` and `flooow_command_runtime` are
security-sensitive NOLOGIN capability roles.

V042 creates no production login, password, token, human assignment, or
protected-role cross-membership.

Deployment membership is a separately governed operation.

No human/operator may directly become the ordinary production member used for
the real attested issuer/writer path.

### Cryptographic test split

Database-only tests:

```text
MUST test:
- role isolation
- snapshot equality
- canonical DB recomputation
- referential integrity
- lock wait/serialization
- replay
- current lifecycle/effectTime
- single-action guard
- direct-DML denial
- rollback

MUST NOT claim:
- InvalidSignature detection by PostgreSQL
- proof that Java JCA executed
```

JVM integration tests:

```text
bad signature
=> Java InvalidSignature
=> no apply invocation
=> zero consumption/authority/decision delta

good signature
=> Java verify true
=> same transaction continues to DB apply
```

### Legacy-unlinked exact self-contained locking

The legacy-unlinked apply capability is not exempt from Revision 5
self-contained locking.

For CONFIRMED/REJECTED root or correction operations it reacquires the exact
V035/V039 lock contract required by that decision shape.

For WITHDRAWN it reacquires the V036 withdrawal lock contract.

In all cases:

```text
organization fence
-> principal FOR UPDATE
-> decision-ID advisory lock
-> required progress/evidence lock
-> sorted subject/target advisory locks
-> current grant/credential validation
-> linked-attestation absence check
-> existing V035/V036 trigger validation
-> INSERT
```

The linked-attestation absence check is after principal serialization.

### Attested exact self-contained locking

The attested decision apply continues to own the Revision 5 exact lock
sequence.

The attested single-action check is after principal serialization.

The capability independently re-resolves exact:

```text
grantId
grantRevision
principalId
permission
state
attestationManifestId
consumption principal
accepted artifact
```

and rejects caller/JVM disagreement.

### SECURITY DEFINER hardening

Every V042 privileged function must satisfy all of:

```text
SECURITY DEFINER
SET search_path=pg_catalog,pg_temp
schema-qualified protected objects
no dynamic SQL
PUBLIC EXECUTE revoked
exact capability-role EXECUTE only
controlled migration/security owner
protected operational roles are not owners
protected operational roles cannot ALTER the function
```

Function owners must not be one of:

```text
flooow_approval_governance
flooow_attestation_verifier
flooow_command_issuer
flooow_command_runtime
```

Where an explicit caller-role check is implemented, it must not use
`current_user` as if it represented the invoker inside SECURITY DEFINER.

The blueprint must freeze either:

```text
EXECUTE privilege as the sole caller authorization primitive
```

or an explicit invoker-safe membership check in addition to EXECUTE.

It must not mix ambiguous caller semantics.

### Protected role-graph preflight

Before installing V042 EXECUTE grants, migration must fail closed if the
protected operational role graph contains forbidden cross-membership.

V042 itself adds no production login membership.

The migration must not silently remove or repair contaminated membership.

### Route classification authority

For a new decision the JVM may predict the route, but the apply capability is
authoritative.

Attested capability:

```text
matching linked non-null GRANT count = exactly 1
```

Legacy-unlinked capability:

```text
matching linked non-null GRANT count = 0
```

Any mismatch:

```text
=> IntegrityFailure
=> decision/head delta = 0
```

Both checks occur while the capability-owned principal lock remains held.

### Additional adversarial proofs

Revision 6 adds:

- protected function owner is not any operational protected role;
- runtime/issuer cannot ALTER or replace privileged functions;
- PUBLIC cannot EXECUTE V042 capabilities;
- cross-protected-role membership causes migration preflight failure;
- V042 migration creates no production login membership;
- database direct-call tests do not claim Ed25519 verification;
- JVM bad-signature path proves apply invocation count zero;
- JVM good-signature path proves snapshot and apply use the same transaction;
- legacy-unlinked direct call acquires a real principal-lock waiter under
  concurrency;
- legacy-unlinked route check occurs after principal serialization;
- attested apply independently rejects a JVM-declared attested route if the DB
  link is absent;
- legacy apply independently rejects a JVM-declared legacy route if the DB
  link is present;
- any explicit SECURITY DEFINER caller-role assertion uses invoker-safe
  semantics.

### Revision 6 gate

```text
REVISION_5_ADVERSARIAL_REVIEW = FAILED
REVISION_6_CORRECTIONS = MATERIALIZED
REVISION_6_ADVERSARIAL_REVIEW = PENDING

V042_IMPLEMENTATION = HOLD
V042_MIGRATION = HOLD
REAL_FIELD_PROOF = HOLD

GIT_ADD = NO
GIT_COMMIT = NO
GIT_PUSH = NO

NEXT_GATE = V042_REVISION_6_CONTRACT_PACKAGE_ADVERSARIAL_REVIEW
```

## Revision 7 controlling correction

This section supersedes conflicting Revision 1 through Revision 6 wording.

Revision 6 failed adversarial review only on execution-time signing-key
continuity.

### Exact artifact-to-effective-key equality

For every new V042 effect, after selecting the effective signer-key revision at
fresh final `effectTime`, require exact equality between the accepted artifact
and the effective V040 row:

```text
accepted.signer_key_id
= effective.signer_key_id

accepted.signer_key_revision
= effective.revision

accepted.signer_key_fingerprint
= effective.signer_key_fingerprint

accepted.signer_key_lineage_fingerprint
= recomputed effective.lineage_fingerprint

accepted.subject_public_key_info_der
= effective.subject_public_key_info_der

accepted.algorithm_id
= effective.algorithm_id
= Ed25519
```

The current signer subject is resolved from that exact effective key row.

The current signer-authority leaf must bind the same:

```text
signerSubjectId
signerKeyId
signerKeyRevision
signerKeyFingerprint
```

plus the already frozen action, permission, role, approval source, state and
time window.

### Future-successor behavior

Given:

```text
revision 1 effective_at = T1
revision 2 effective_at = T2
T1 < effectTime < T2
```

revision 1 remains the effective key. An accepted proof signed by revision 1
may remain eligible if every other V042 gate passes.

Given:

```text
effectTime >= T2
```

revision 2 is the effective key.

An accepted proof signed by revision 1 then fails new-effect admission with
`ScopeMismatch`, even if the immutable revision-1 row still stores state
`ACTIVE`.

### Current-authority successor behavior

The accepted proof's historical signer-authority identity is retained and
revalidated as historical evidence.

Execution-time signer authority is independently resolved from the current
authority lineage.

A later current authority revision may authorize the accepted proof only when
it binds the exact execution-time effective key and the same frozen S2A scope.

This does not rewrite the accepted proof's historical authority revision.

### New mandatory tests

Revision 7 adds:

- future key successor exists but is not yet effective -> predecessor-signed
  attestation remains eligible when all other gates pass;
- exact `effective_at` boundary switches the effective key;
- after successor becomes effective, predecessor-signed attestation is denied
  for a new effect;
- accepted signer key revision mismatch -> ScopeMismatch;
- accepted signer key fingerprint mismatch -> ScopeMismatch;
- accepted signer key lineage fingerprint mismatch -> ScopeMismatch or
  IntegrityFailure when stored immutable proof is internally inconsistent;
- accepted SPKI mismatch -> ScopeMismatch or IntegrityFailure according to
  whether mismatch is current-scope versus retained-proof corruption;
- accepted algorithm mismatch -> denial;
- current authority successor binding the same exact effective key may pass;
- current authority binding a different effective key denies;
- exact historical operation replay remains unchanged after key rotation and
  creates zero new effects.

### Revision 7 gate

```text
REVISION_6_ADVERSARIAL_REVIEW = FAILED
REVISION_7_CORRECTIONS = MATERIALIZED
REVISION_7_ADVERSARIAL_REVIEW = PENDING

V042_IMPLEMENTATION = HOLD
V042_MIGRATION = HOLD
REAL_FIELD_PROOF = HOLD

GIT_ADD = NO
GIT_COMMIT = NO
GIT_PUSH = NO

NEXT_GATE = V042_REVISION_7_CONTRACT_PACKAGE_ADVERSARIAL_REVIEW
```

## Revision 8 controlling correction

This section supersedes the conflicting Revision 7 key-continuity rule.

Revision 7 incorrectly required historical accepted key revision/lineage
identity to equal the execution-time lifecycle revision.

### Two distinct key proofs

V042 performs two separate proofs.

#### Historical accepted-key proof

Resolve the exact historical key row by:

```text
organizationId
accepted.signerKeyId
accepted.signerKeyRevision
```

Require and recompute:

```text
historical.signerKeyFingerprint
= accepted.signerKeyFingerprint

historical.lineageFingerprint
= accepted.signerKeyLineageFingerprint

historical.subjectPublicKeyInfoDer
= accepted.subjectPublicKeyInfoDer

historical.algorithmId
= accepted.algorithmId
= Ed25519
```

Use the retained SPKI and exact signature preimage for Java 21 JCA
reverification.

#### Execution-time lifecycle proof

Under the same key lock resolve:

```text
effective =
highest key revision with effective_at <= effectTime
```

Require:

```text
effective.state = ACTIVE

effective.signerKeyId
= historical.signerKeyId

effective.signerSubjectId
= historical.signerSubjectId

effective.algorithmId
= historical.algorithmId

effective.subjectPublicKeyInfoDer
= historical.subjectPublicKeyInfoDer

effective.signerKeyFingerprint
= historical.signerKeyFingerprint
```

Recompute the effective lineage fingerprint independently.

No equality requirement exists between:

```text
historical.revision
effective.revision
```

or between:

```text
historical.lineageFingerprint
effective.lineageFingerprint
```

### Why revision equality is forbidden

V040's key-lineage trigger already requires a successor revision for the same
key ID to preserve:

```text
signer subject
algorithm
SPKI
key fingerprint
validFrom
```

The signature preimage does not contain signer-key revision.

Treating revision equality as signing identity would therefore misinterpret a
lifecycle revision as cryptographic key rotation and would create false
execution denials.

### Effective authority requirement remains unchanged

The current signer-authority leaf must bind the exact effective:

```text
signerSubjectId
signerKeyId
signerKeyRevision
signerKeyFingerprint
```

with:

```text
signerRole = S2A_FIELD_PROOF_APPROVER
approvalAction = S2A_FIELD_PROOF_APPROVAL
permission = TRANSACTION_IDENTITY_DECISION_WRITE
approvalSourceId = decoded manifest.approvalSource
state = ENABLED
validFrom <= effectTime < validUntil
```

If the effective lifecycle revision changes and no current authority binds that
effective revision:

```text
=> ScopeMismatch
=> zero new effect
```

### Required tests

Revision 8 replaces the conflicting Revision 7 revision-equality tests with:

- historical accepted revision and effective revision may differ while SPKI,
  key fingerprint, algorithm and subject remain identical;
- historical lineage fingerprint is recomputed against the historical row;
- effective lineage fingerprint is independently recomputed against the
  effective row;
- active successor with unchanged key material plus authority bound to the
  effective revision may pass;
- active successor with authority still bound to the historical revision
  denies;
- RETIRED/REVOKED/COMPROMISED effective revision denies;
- effective SPKI mismatch denies;
- effective key fingerprint mismatch denies;
- effective signer subject mismatch denies;
- retained historical row corruption is IntegrityFailure;
- exact committed replay remains unaffected by later lifecycle revision.

### Revision 8 gate

```text
REVISION_7_ADVERSARIAL_REVIEW = FAILED
REVISION_8_CORRECTIONS = MATERIALIZED
REVISION_8_ADVERSARIAL_REVIEW = PENDING

V042_IMPLEMENTATION = HOLD
V042_MIGRATION = HOLD
REAL_FIELD_PROOF = HOLD

GIT_ADD = NO
GIT_COMMIT = NO
GIT_PUSH = NO

NEXT_GATE = V042_REVISION_8_CONTRACT_PACKAGE_ADVERSARIAL_REVIEW
```

## Revision 9 controlling correction

This section supersedes the conflicting Revision 8 claim that an existing V040
authority scope can advance to another signer-key lifecycle revision.

Revision 8 failed adversarial review on that predecessor-compatibility point.

### Frozen V040 authority binding

For an existing signer-authority lineage, V040 requires every successor to
preserve:

```text
signerKeyId
signerKeyRevision
signerKeyFingerprint
```

along with the other frozen scope fields.

V042 does not modify that contract.

Therefore no V042 implementation may:

- change the V040 authority-lineage trigger to permit signer-key revision
  rebinding;
- rewrite an existing authority row;
- create a parallel authority lineage in the same frozen scope to bypass the
  current leaf;
- reinterpret `signerKeyRevision` as non-semantic;
- treat matching SPKI/fingerprint as sufficient current authority.

### Historical proof versus current execution authority

The two Revision 8 key proofs remain:

```text
1. historical accepted-key integrity proof
2. execution-time effective lifecycle proof
```

Historical accepted revision need not equal effective revision for proof
integrity.

But a new V042 effect additionally requires the frozen current V040 authority
leaf to bind the exact effective revision.

Thus:

```text
historical accepted revision = 1
effective revision = 2
authority leaf binds revision = 1

=> ScopeMismatch
=> command-authority delta = 0
=> identity-decision delta = 0
```

This is the required V042 behavior even if both lifecycle revisions contain the
same:

```text
signerSubjectId
algorithmId
subjectPublicKeyInfoDer
signerKeyFingerprint
validFrom
```

### Transition timing

Before the successor becomes effective:

```text
effectTime < successor.effectiveAt
=> predecessor remains effective
=> authority/predecessor revision may still match
```

At and after the successor effective boundary:

```text
effectTime >= successor.effectiveAt
=> successor is effective
=> old authority revision binding mismatches
=> ScopeMismatch
```

A terminal effective state:

```text
RETIRED | REVOKED | COMPROMISED
```

continues to map to `ExpiredOrNotYetValid` according to the frozen lifecycle
classification.

### No V040 repair in V042

The V042 migration must have zero semantic changes to:

```text
s2a_signer_key_revision
s2a_signer_authority_revision
s2a_append_signer_key_revision(...)
s2a_append_signer_authority_revision(...)
V040 validation triggers
V040 lineage fingerprints
V040 privilege ownership
```

except narrow read/lock access through the new V042 SECURITY DEFINER
capabilities.

No V040 row is inserted, updated, deleted, repaired, or reseeded by V042.

### New mandatory tests

Revision 9 replaces the impossible Revision 8 passing case with:

- ACTIVE key lifecycle successor not yet effective + authority bound to the
  predecessor effective revision -> may pass if all other gates pass;
- ACTIVE successor becomes effective + authority still bound to predecessor
  revision -> ScopeMismatch;
- same SPKI/fingerprint across the two revisions does not override the
  authority revision mismatch;
- V042 cannot append an authority successor with a changed
  `signerKeyRevision` through V040;
- V042 migration leaves V040 DDL/function definitions byte/semantic equivalent
  except for no broad direct privilege expansion;
- no V042 path rewrites an old authority to the effective revision;
- historical accepted proof remains readable/recomputable after the lifecycle
  transition;
- exact committed replay remains historical and writes zero new effects.

### Revision 9 gate

```text
REVISION_8_ADVERSARIAL_REVIEW = FAILED
REVISION_9_CORRECTIONS = MATERIALIZED
REVISION_9_ADVERSARIAL_REVIEW = PENDING

V042_IMPLEMENTATION = HOLD
V042_MIGRATION = HOLD
REAL_FIELD_PROOF = HOLD

GIT_ADD = NO
GIT_COMMIT = NO
GIT_PUSH = NO

NEXT_GATE = V042_REVISION_9_CONTRACT_PACKAGE_ADVERSARIAL_REVIEW
```
