# ADR-0089 - S2A attestation consumption and attested command authority

## Status

IMPLEMENTATION-EXACT CONTRACT CANDIDATE - REVISION 9.

This ADR freezes the V042 architectural boundary only.

It does not authorize V042 implementation, migration execution, production role assignment, production key use, command-authority activation, provider interaction, transaction-identity execution, or a real field proof.

Baseline:

```text
6d801beb7491a6546c0bad3835a876386cdc6767
```

## Context

The frozen predecessor boundaries are:

```text
V040 = approval governance
V041 = immutable accepted-attestation evidence
V042 = attestation consumption + command-authority binding + execution eligibility
```

V041 is historical accepted evidence, not current execution authority.

```text
ACCEPTED ATTESTATION != CURRENT EXECUTION AUTHORITY
HISTORICAL VALIDITY != CURRENT ELIGIBILITY
SIGNATURE VALID != COMMAND AUTHORITY
EVIDENCE != AUTHORITY
AUTHORITY != EXECUTION
```

The pre-V042 issuer still has direct DML capability over command-authority tables. That is the expected predecessor baseline, but it is not acceptable for the real attested S2A path.

## Decision

V042 introduces the one-time immutable bridge from one accepted V041 attestation to at most one command-principal root.

Before any consumption or command-authority effect V042 must:

1. load the immutable V041 artifact;
2. strictly decode the canonical manifest bytes;
3. require encode(decode(bytes)) to equal the original bytes exactly;
4. recompute the manifest digest;
5. reconstruct and compare the canonical signature preimage;
6. recompute the SPKI fingerprint;
7. reconstruct and recompute the accepted-proof fingerprint;
8. independently verify Ed25519 with Java 21 JCA;
9. resolve immutable historical key and signer-authority references;
10. re-resolve current organization eligibility;
11. re-resolve current signer-key eligibility;
12. re-resolve current signer-authority eligibility;
13. validate the current approval window;
14. validate the exact approved target;
15. rederive the durable evidence-binding fingerprint;
16. validate consumption/replay identity;
17. perform only a narrow attestation-aware authority mutation.

V041 row existence and `AlreadyAccepted` are never sufficient command authority.

## Canonical manifest source

The retained `canonicalManifestBytes` are the single immutable V042 manifest source.

A launcher-supplied duplicate manifest representation cannot become authority.

V042 requires a strict decoder for the frozen manifest v1 canonical representation. It must reject truncated framing, trailing bytes, malformed UTF-8, noncanonical UUID/timestamp/enum/integer/nullable values, non-NFC text, forbidden controls, boundary whitespace where prohibited, silent normalization, trimming, coercion, repair, or defaulting.

Successful decode must satisfy:

```text
encode(decode(canonicalManifestBytes))
=
canonicalManifestBytes
```

byte-for-byte.

## Consumption

Accepted-attestation identity:

```text
organizationId + manifestId
```

Consumption identity:

```text
organizationId + manifestId
```

The immutable consumption binds:

```text
manifestDigest
principalId
correlationId
consumedAt
```

One accepted manifest may create at most one command-principal root.

Exact replay may recover the already committed lineage only. Changed semantic intent under the same identity fails closed.

## Atomic principal boundary

First consumption is one database transaction:

```text
validate accepted artifact
-> validate current execution eligibility
-> create command principal
-> insert immutable attestation consumption
-> append PRINCIPAL command-authority operation
-> commit
```

Failure before commit requires:

```text
ATTESTATION_CONSUMPTION_DELTA = 0
COMMAND_AUTHORITY_DELTA = 0
```

No partially consumed approval is legal.

## Initial credential and grant

The original field-proof attestation may support only the initial real S2A authority sequence:

```text
PRINCIPAL
INITIAL_CREDENTIAL
GRANT
```

INITIAL_CREDENTIAL and GRANT must resolve the existing consumption, require the exact organization/manifest/principal, independently revalidate the artifact and current eligibility, preserve existing V034/V037 replay rules, and append the linked authority-operation receipt.

GRANT is limited to:

```text
TRANSACTION_IDENTITY_DECISION_WRITE
```

The original field-proof manifest does not authorize `ROTATE_CREDENTIAL`, `REVOKE`, or `TRANSACTION_IDENTITY_POLICY_ADMIN`. Those remain separate operational-authority concerns.

## Authority-operation linkage

V042 adds the additive nullable linkage:

```text
command_authority_operation.attestation_manifest_id uuid NULL
```

Historical and synthetic pre-V042 rows may remain NULL.

Real S2A PRINCIPAL, INITIAL_CREDENTIAL, and GRANT operations require the attestation linkage.

No synthetic APPROVAL operation is introduced.

The operation intent fingerprint must bind the attestation identity, manifest digest, and accepted-proof fingerprint.

## Issuer hardening

Migration V042 must atomically remove the practical direct-DML bypass from the real issuer boundary.

After V042, the ordinary `flooow_command_issuer` capability must not have direct INSERT authority over:

```text
command_principal
command_credential_revision
command_permission_grant
command_authority_operation
```

Real attested mutation is permitted only through narrow, single-purpose, attestation-aware capabilities. No generic mutation function, arbitrary operation selector, dynamic SQL, or arbitrary permission widening is permitted.

PUBLIC EXECUTE must be revoked from privileged capabilities. Runtime, verifier, and approval-governance roles must not gain issuer capability.

## Cryptographic authority

```text
POSTGRES_ED25519_AUTHORITY = NO
JAVA_21_JCA_ED25519_AUTHORITY = YES
```

A prior V041 verification is historical evidence, not a shortcut.

## Current execution eligibility

Execution time is database-server-owned `timestamptz(6)`.

A new V042 effect requires:

```text
organization current state = ACTIVE

current effective signer-key leaf
= unambiguous
= ACTIVE

current signer-authority leaf
= unambiguous
= ENABLED
= exact organization
= exact signer/key/action/permission
= currently valid

approvalWindowStart <= executionTime
executionTime < approvalWindowEnd

target = exact manifest target

durable evidence binding
= exact approved evidence binding
```

`verifiedAt` never grandfathers execution.

Retired, revoked, compromised, disabled, expired, future, mismatched, missing, forked, or ambiguous governance state denies new V042 effects.

## Final writer eligibility fence

Creating command authority is still not execution.

The transaction-identity writer must carry the V042 consumption and governance eligibility fence through immutable identity-decision commit.

Before decision insert the writer must prove current command authorization, exact attestation consumption, artifact integrity, Java 21 JCA signature validity, current organization/key/authority/window eligibility, exact target, current durable evidence binding, and all existing writer currentness gates.

Any denial produces no new identity decision.

Lifecycle events after a committed immutable decision do not rewrite historical truth.

## Locking

Provisioning preserves the existing operation-ID-before-principal ordering and adds the attestation/governance fences:

```text
organization FOR SHARE
-> operation-ID advisory lock
-> replay check
-> principal advisory lock
-> principal FOR UPDATE if present
-> attestation advisory lock
-> accepted attestation / consumption
-> signer-key advisory lock
-> signer-authority-scope advisory lock
-> current key leaf
-> current authority leaf
-> artifact reverification
-> evidence eligibility
-> authority mutation
-> authority-operation receipt
-> commit
```

No provider/network call is permitted while protected governance/authority locks are held.

## Failure contract

V042 fails closed on any artifact, canonicalization, digest, signature, SPKI, proof fingerprint, historical lineage, current lifecycle, approval window, target, evidence, permission, replay, consumption, linkage, privilege, role-graph, atomicity, or infrastructure inconsistency.

For any failed new consumption/authority attempt:

```text
ATTESTATION_CONSUMPTION_DELTA = 0
COMMAND_AUTHORITY_DELTA = 0
```

For final writer denial:

```text
IDENTITY_DECISION_DELTA = 0
IDENTITY_HEAD_DELTA = 0
```

## Hard wall

V042 does not itself authorize provider calls, financial authority, Decision Room mutation, policy administration, production signer assignment, production role assignment, or a real field proof.

## Rejected alternatives

- trust V041 row existence as current authority;
- trust `AlreadyAccepted` as execution eligibility;
- re-send manifest fields as a second authority source;
- permissive canonical parsing;
- keep direct issuer INSERT privileges for the real S2A path;
- generic SECURITY DEFINER mutation APIs;
- mark an attestation consumed before principal creation commits;
- allow one manifest to create multiple principal roots;
- let credential/grant operations cross consumption lineage;
- let the original field-proof manifest authorize future rotation/revocation;
- rely only on provisioning-time eligibility without a final writer fence.

## Revision 1 closure

```text
REVISION_1_BASELINE_AUDIT = PASS

CANONICAL_MANIFEST_DECODER_REQUIRED = YES
CONSUMPTION_BRIDGE_REQUIRED = YES
AUTHORITY_OPERATION_LINK_REQUIRED = YES
ISSUER_HARDENING_REQUIRED = YES
FINAL_WRITER_ELIGIBILITY_FENCE_REQUIRED = YES

POSTGRES_ED25519_AUTHORITY = NO
JAVA_21_JCA_ED25519_AUTHORITY = YES

V042_IMPLEMENTATION = HOLD
V042_MIGRATION = HOLD
REAL_FIELD_PROOF = HOLD
```

## Revision 2 adversarial corrections

This section is controlling wherever it conflicts with Revision 1.

Revision 1 failed adversarial review. No implementation is authorized.

### V042 issuer trusted computing boundary

The V042 issuer cryptographic boundary is composite:

```text
dedicated V042 issuer process
+ Java 21 JCA Ed25519
+ flooow_command_issuer capability role
+ one caller-owned READ_COMMITTED JDBC transaction
+ locked V040/V041/V042 snapshot
```

PostgreSQL remains authoritative for tenancy, currentness, lineage integrity,
serialization, replay, immutability, evidence derivation, and exact authority
mutation.

Java 21 JCA remains authoritative for Ed25519 verification.

PostgreSQL cannot prove that Java JCA executed. Possession or compromise of
the dedicated V042 issuer service identity is therefore compromise of the
V042 issuer trusted computing boundary, not a supported alternate API.

V042 must not solve this by granting `flooow_command_issuer` broad direct
SELECT on V040/V041 governance or accepted-attestation tables.

V042 instead requires a narrow snapshot/apply handshake:

```text
BEGIN / SNAPSHOT CAPABILITY
- caller transaction already open
- acquire frozen locks
- resolve exact accepted artifact
- resolve immutable historical references
- resolve current organization/key/authority state
- derive current evidence binding
- capture server-owned executionTime
- return the nonsecret verification snapshot
- perform no command-authority mutation

JAVA PHASE
- same JDBC connection
- same transaction
- reconstruct canonical artifact
- verify all deterministic integrity bindings
- verify Ed25519 with Java 21 JCA

APPLY CAPABILITY
- same transaction
- same protected locks still held
- independently re-resolve security-relevant snapshot values
- require equality with the expected snapshot
- perform only the exact single-purpose authority mutation
- append the exact linked command-authority receipt
```

Exact function names and signatures remain implementation-blueprint work.
No generic mutation function is permitted.

### Runtime writer trusted computing boundary

The final writer uses the same trust split:

```text
dedicated governed writer process
+ Java 21 JCA Ed25519
+ flooow_command_runtime capability role
+ existing caller-owned READ_COMMITTED writer transaction
+ narrow V042 execution-eligibility snapshot capability
```

`flooow_command_runtime` must not receive broad direct SELECT on V040/V041
tables merely to implement V042.

The narrow runtime capability returns the exact linked accepted artifact plus
the locked current governance/evidence snapshot. It performs no
command-authority mutation and no identity-decision mutation.

Java reverification occurs on the same JDBC connection and transaction before
the immutable identity decision.

### Deterministic writer-to-attestation lineage

The final writer must not resolve an attestation by principal alone.

The exact authorized GRANT lineage is the bridge.

The writer already receives through current command authorization:

```text
organizationId
principalId
grantId
grantRevision
permission
```

For real S2A execution it must resolve exactly one linked
`command_authority_operation` satisfying:

```text
organization_id = authorized organization
operation = GRANT
principal_id = authorized principal
grant_id = authorized grantId
grant_revision = authorized grantRevision
permission = TRANSACTION_IDENTITY_DECISION_WRITE
state = ENABLED
attestation_manifest_id IS NOT NULL
```

That row identifies the manifest. The manifest resolves the exact consumption,
and the consumption must resolve back to the same principal.

Zero matching linked GRANT operations denies.

More than one matching linked GRANT operation is integrity failure.

Principal-only attestation lookup is forbidden.

### Frozen linked-operation uniqueness

Revision 1 wording that left linked-operation uniqueness open is superseded.

Preserve the SPEC-0088 frozen rule:

```text
at most one linked operation of each expected kind
per organization + manifest
```

The V042 physical model therefore requires the equivalent of:

```text
UNIQUE (
    organization_id,
    attestation_manifest_id,
    operation
)
WHERE attestation_manifest_id IS NOT NULL
  AND operation IN ('PRINCIPAL','INITIAL_CREDENTIAL','GRANT')
```

The implementation blueprint must express exact PostgreSQL DDL and prove
migration compatibility.

For final writer determinism, one immutable real S2A grant row may also have
only one linked GRANT receipt. This must be enforced by the database, not only
checked in application code.

### Signer-key structural lineage versus effective revision

Revision 1's phrase `current effective signer-key leaf` was imprecise and is
superseded.

V040/V041 distinguish:

```text
STRUCTURAL LEAF
= unique lineage row with no successor

EFFECTIVE REVISION AT executionTime
= highest revision for the key with effective_at <= executionTime
```

A future structural successor may exist while an earlier revision remains the
effective revision.

V042 must:

1. prove key lineage structural integrity and exactly one structural leaf;
2. under the same key lock select the highest revision with
   `effective_at <= executionTime`;
3. require `valid_from <= executionTime`;
4. require that effective revision state is `ACTIVE`;
5. require current signer authority to bind that exact effective key revision
   and fingerprint.

The effective revision is not required to be the structural leaf.

### Current signer-authority scope

Current V042 signer-authority eligibility preserves the full frozen scope:

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

Missing, ambiguous, stale, forked, disabled, mismatched, future, or expired
authority denies.

### Server-owned execution time

For one new V042 attempt:

```text
executionTime = transaction_timestamp()::timestamptz(6)
```

The value comes from the same PostgreSQL transaction and is reused for all
temporal checks and snapshot/apply comparison.

The caller cannot supply executionTime.

### Exact replay precedes fresh-currentness admission

An already committed authority operation is historical immutable state, not a
new authority effect.

Under the operation-ID advisory lock:

```text
existing operation + exact intent + exact attestation linkage
=> AlreadyApplied
=> return immutable existing receipt
=> zero writes
=> no fresh current eligibility required

existing operation + changed intent or linkage
=> IntegrityFailure
=> zero writes

no existing operation
=> continue to fresh V042 artifact/currentness validation
```

This ordering is mandatory for uncertain-commit recovery.

Later expiry, key retirement/revocation, authority disablement, or organization
suspension must not destroy recovery of an already committed exact receipt.

### Legacy issuer path after V042

Revoking direct issuer DML means the current direct-SQL
`PostgresControlledCommandAuthorityIssuer` cannot remain a hidden real
operational bypass.

After V042, real S2A:

```text
PRINCIPAL
INITIAL_CREDENTIAL
GRANT
```

uses only attestation-aware V042 capabilities.

The original field-proof manifest does not authorize:

```text
ROTATE_CREDENTIAL
REVOKE
```

Those operations remain real-path HOLD until a separately reviewed operational
authority contract and narrow capability exist.

V042 must not retain direct authority-table DML merely to keep the legacy
rotate/revoke adapter operational.

### Consumption field provenance

For first consumption:

```text
manifest_digest
= accepted artifact manifest digest
= recomputed digest of retained canonical manifest bytes

correlation_id
= decoded manifest.correlationId

consumed_at
= transaction_timestamp()::timestamptz(6)
```

None may be caller-overridden.

### Semantic outcome contract

The V042 boundary must distinguish at minimum:

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

Infrastructure failures, deadlocks, connectivity failures, and unknown
SQLSTATEs are not ordinary domain outcomes and must not be silently converted
to success or denial.

Exact SQLSTATE allocation and Kotlin type names are implementation-blueprint
work.

### Revision 2 state

```text
REVISION_1_ADVERSARIAL_REVIEW = FAILED
REVISION_2_CORRECTIONS = MATERIALIZED

OPEN_IMPLEMENTATION_AUTHORIZATION = NO

V042_IMPLEMENTATION = HOLD
V042_MIGRATION = HOLD
REAL_FIELD_PROOF = HOLD

NEXT_GATE = V042_REVISION_2_CONTRACT_PACKAGE_ADVERSARIAL_REVIEW
```

## Revision 3 adversarial corrections

This section is controlling wherever it conflicts with Revisions 1 or 2.

Revision 2 failed adversarial review. No implementation is authorized.

### Runtime decision-write hardening

V039 currently grants direct `INSERT` on
`marketplace_transaction_identity_decision` to `flooow_command_runtime`.

That direct DML is incompatible with a V042 execution-eligibility fence that
depends on Java 21 JCA and attestation currentness.

Therefore V042 must atomically revoke:

```text
INSERT ON marketplace_transaction_identity_decision
FROM flooow_command_runtime
```

for the real operational boundary.

The real S2A writer may persist a new identity decision only through a narrow
attestation-aware SECURITY DEFINER apply capability.

The capability must:

- be fixed to the governed transaction-identity table;
- accept no arbitrary table or SQL target;
- use a fixed safe search path;
- use schema-qualified SQL;
- revoke PUBLIC EXECUTE;
- be executable only by `flooow_command_runtime`;
- re-resolve the exact linked GRANT and attestation lineage;
- revalidate the final V042 snapshot;
- enforce the one-explicit-action rule;
- perform the decision INSERT so existing V035/V036 triggers still execute;
- return only the immutable decision result/receipt required by the writer.

A caller holding only `flooow_command_runtime` must not be able to bypass the
V042 attestation fence with direct table INSERT.

Administrative database ownership/superuser trust remains outside the ordinary
operational-role model.

### One manifest / one explicit identity action

ADR/SPEC-0087 define the first field proof as one explicit governed
transaction-identity action whose intended result is one `CONFIRMED` decision.

Single-use authority-root consumption alone does not enforce that property.

V042 therefore freezes the real field-proof GRANT as single-decision.

The exact linked GRANT is already uniquely associated with one consumed
manifest through `command_authority_operation`.

For a new real S2A writer effect, after exact decision replay classification
and while the principal/authority fences remain held:

```text
existing marketplace_transaction_identity_decision
for organization_id + authorized grant_id
= 0
```

must be true.

If another decision already exists for the same real S2A grant:

```text
different decisionId
=> INTEGRITY FAILURE
=> zero new decision/head effect
```

The real V042 field-proof apply capability permits only:

```text
kind = CONFIRMED
revision = 1
supersedesDecisionId = NULL
```

It does not authorize `REJECTED` or `WITHDRAWN`.

This rule uses the already frozen GRANT-to-manifest linkage and does not add a
fifth S2A persistence table.

Concurrent attempts are serialized by the existing organization/principal and
writer lock chain. Exactly one new decision may commit for the real S2A grant.

Future non-field-proof transaction-identity operations require their own
reviewed operational authority boundary. V042 does not preserve generic direct
runtime INSERT as a compatibility escape hatch.

### Exact writer replay ordering

V042 must preserve the existing writer replay semantics instead of inserting a
new attestation-currentness gate before them.

For every writer call:

```text
1. authenticate current credential
2. current command authorizeForWrite
3. compute existing transaction-identity intent
4. acquire decision-ID advisory lock
5. read existing immutable decision by organization + decisionId
```

Then:

```text
existing decision + exact existing intent
=> AlreadyApplied
=> no new write
=> do not require fresh V042 key/authority/window/evidence eligibility

existing decision + changed intent
=> IntegrityFailure
=> no new write

no existing decision
=> enter V042 attestation execution admission
```

This preserves current V036/V039 behavior:

- stale credentials remain denied before replay;
- revoked grants remain denied before replay;
- a currently authorized actor may recover an exact committed receipt;
- later attestation expiry/key revocation/authority disablement does not turn
  historical decision replay into a new execution.

For a new decision only, the V042 lifecycle locks and Java reverification are
held through the final decision apply capability and immutable insert.

### Final effect time

Revision 2's use of `transaction_timestamp()` as the authoritative V042
execution time is superseded.

A long-running transaction must not remain eligible merely because it began
before an approval/key/authority expiration boundary.

For every new authority mutation and every new identity-decision mutation, the
final apply capability captures:

```text
effectTime = clock_timestamp()::timestamptz(6)
```

immediately before its final currentness evaluation and mutation.

The caller cannot submit `effectTime`.

The apply capability uses that one value for all temporal checks performed by
that final effect:

```text
effective signer-key revision
signer-key validFrom/state
signer-authority validFrom/validUntil/state
approvalWindowStart/approvalWindowEnd
organization current state
```

For first principal consumption:

```text
s2a_attestation_consumption.consumed_at = effectTime
```

The earlier snapshot phase may perform preliminary eligibility checks, but
only the final apply-phase checks at `effectTime` authorize a new effect.

Java Ed25519 verification remains on the same JDBC connection and transaction;
its mathematical result does not depend on wall-clock time.

### Attested authority intent fingerprint v2

The existing historical/synthetic fingerprint contract remains unchanged:

```text
controlled-command-authority/1
```

Real V042 attested PRINCIPAL, INITIAL_CREDENTIAL, and GRANT operations use a
new versioned intent contract:

```text
domain = controlled-command-authority/2
```

Hash algorithm remains the existing controlled-authority framing:

```text
for each UTF-8 value in order:
    decimal UTF-8 byte length
    ":"
    value

SHA-256(concatenation)
lowercase hexadecimal
```

The v2 operation-specific fields preserve the exact v1 order and append the
attestation binding in this exact order:

```text
manifestId
acceptedProofFingerprint
manifestDigest
```

`acceptedProofFingerprint` is the exact physical meaning of the older
SPEC-0088 term `artifactFingerprint`.

Exact v2 preimages are:

```text
PRINCIPAL

controlled-command-authority/2
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
INITIAL_CREDENTIAL

controlled-command-authority/2
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
GRANT

controlled-command-authority/2
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

UUID text is canonical lowercase UUID text.

All digest/fingerprint text is lowercase hexadecimal.

For the real attested path:

```text
reason = decoded manifest.reason
provenance = decoded manifest.provenance
correlationId = decoded manifest.correlationId
```

These signed values are not caller-overridable.

The V042 database apply capability independently recomputes the v2 intent
fingerprint from validated values. It does not trust a caller-supplied final
fingerprint.

The existing receipt contract remains:

```text
controlled-command-authority-receipt/1
```

and receives the v2 intent fingerprint as its `intent` input. Therefore the
receipt transitively binds the exact V042 attestation without rewriting
historical receipt semantics.

### Physical principal-consumption linkage

The consumption primary key remains:

```text
PRIMARY KEY (organization_id, manifest_id)
```

V042 additionally requires a referential key suitable for exact-principal
linkage:

```text
UNIQUE (
    organization_id,
    manifest_id,
    principal_id
)
```

This is not reverse principal uniqueness. Multiple distinct manifests are not
forbidden from referencing the same principal by this constraint.

For every linked real S2A authority operation, the database must enforce:

```text
FOREIGN KEY (
    organization_id,
    attestation_manifest_id,
    principal_id
)
REFERENCES s2a_attestation_consumption (
    organization_id,
    manifest_id,
    principal_id
)
```

This prevents a linked INITIAL_CREDENTIAL or GRANT receipt from naming a
different principal than the consumed manifest even if application code is
wrong.

The previously frozen partial unique rule remains mandatory:

```text
at most one PRINCIPAL
at most one INITIAL_CREDENTIAL
at most one GRANT
per organization + manifest
```

The linked real GRANT target must also be database-unique for its immutable
grant identity.

No `UNIQUE (organization_id, principal_id)` consumption rule is introduced.

### Typed real-path boundary

The existing `ControlledCommandAuthorityIssuer` and its v1 request DTOs are
historical/synthetic substrate.

V042 must not weaken those types by adding nullable or optional attestation
fields that permit an accidental legacy bypass.

The real V042 path uses a separate non-null attested command-authority
boundary for PRINCIPAL, INITIAL_CREDENTIAL, and GRANT.

Exact Kotlin type names are implementation-blueprint work.

ROTATE_CREDENTIAL and REVOKE remain outside the real field-proof manifest
authority.

### Revision 3 state

```text
REVISION_2_ADVERSARIAL_REVIEW = FAILED
REVISION_3_CORRECTIONS = MATERIALIZED

V042_IMPLEMENTATION = HOLD
V042_MIGRATION = HOLD
REAL_FIELD_PROOF = HOLD

NEXT_GATE = V042_REVISION_3_CONTRACT_PACKAGE_ADVERSARIAL_REVIEW
```

## Revision 4 adversarial corrections

This section is controlling wherever it conflicts with Revisions 1 through 3.

Revision 3 failed adversarial review. No implementation is authorized.

### Exact authority-operation target integrity

V042 uses `command_authority_operation` as a security bridge from current
command authorization to the consumed attestation.

The V037 foreign keys are not sufficient for that role:

- credential operations reference credential identity/revision but do not
  physically bind the operation principal to the credential principal;
- grant operations reference grant identity but do not physically bind
  `grant_revision`, operation principal, permission, or state to the referenced
  grant row.

V042 therefore requires database-enforced exact target tuples.

The physical schema must provide a referenced unique key equivalent to:

```text
command_credential_revision

UNIQUE (
    organization_id,
    credential_id,
    revision,
    principal_id,
    state
)
```

and:

```text
command_permission_grant

UNIQUE (
    organization_id,
    grant_id,
    revision,
    principal_id,
    permission,
    state
)
```

`command_authority_operation` must then enforce equivalent composite foreign
keys:

```text
FOREIGN KEY (
    organization_id,
    credential_id,
    credential_revision,
    principal_id,
    state
)
REFERENCES command_credential_revision (
    organization_id,
    credential_id,
    revision,
    principal_id,
    state
)
```

and:

```text
FOREIGN KEY (
    organization_id,
    grant_id,
    grant_revision,
    principal_id,
    permission,
    state
)
REFERENCES command_permission_grant (
    organization_id,
    grant_id,
    revision,
    principal_id,
    permission,
    state
)
```

NULL semantics preserve PRINCIPAL rows and the non-applicable half of each
operation shape.

These constraints harden both historical operation shape and future attested
operation shape without inventing new command-authority state.

The previously frozen operation-to-consumption principal FK remains required
for non-null attestation links.

### DB-owned attested intent and receipt persistence

For the real V042 attested path, neither final
`intent_fingerprint` nor final `receipt_fingerprint` is caller-owned
persistence data.

The narrow V042 apply capability:

1. reconstructs the exact attested v2 intent from validated database and
   canonical-manifest values;
2. computes `controlled-command-authority/2` itself;
3. computes the existing
   `controlled-command-authority-receipt/1` fingerprint itself from the
   resulting authority tuple;
4. stores those database-computed values.

Java may compute the same fingerprints for golden-vector and cross-runtime
verification, but a Java-provided digest cannot replace database
recomputation.

The receipt preimage remains the existing v1 receipt order:

```text
controlled-command-authority-receipt/1
intentFingerprint
operation
principalId
credentialId-or-empty
credentialRevision-or-empty
grantId-or-empty
grantRevision-or-empty
permission-or-empty
state-or-empty
```

using the existing decimal UTF-8 byte-length framing and lowercase SHA-256.

Historical V037 rows retain their stored v1 values unchanged.

### Exact authority-operation replay

Operation replay classification occurs under the operation-ID advisory lock.

A stored operation may return `AlreadyApplied` only if the database proves
that the complete immutable receipt still represents the exact requested
operation.

For a real V042 linked row, replay must verify all applicable fields:

```text
organization_id
operation_id
operation
principal_id
credential_id
credential_revision
grant_id
grant_revision
permission
state
correlation_id
attestation_manifest_id
intent_fingerprint
receipt_fingerprint
```

and must additionally prove:

```text
linked consumption exists
linked consumption principal matches
linked accepted attestation exists
manifest digest matches
accepted proof fingerprint matches

credential tuple matches exact credential row when applicable
grant tuple matches exact grant row when applicable

database-recomputed controlled-command-authority/2
= stored intent_fingerprint

database-recomputed controlled-command-authority-receipt/1
= stored receipt_fingerprint
```

Only then:

```text
=> AlreadyApplied
=> zero writes
=> no fresh current lifecycle eligibility required
```

Any mismatch, missing target, malformed linked lineage, digest mismatch, or
receipt mismatch is:

```text
=> IntegrityFailure
=> zero writes
```

Replay may not trust `intent_fingerprint` equality by itself.

### Post-V042 issuer privilege floor

After V042 migration, `flooow_command_issuer` has no ordinary direct table
mutation path and no broad read path over the protected command-authority,
V040 governance, V041 accepted-attestation, or V042 consumption tables.

For the real path its ordinary privileges are capability execution only.

At minimum the deployment-equivalent role matrix must prove:

```text
command_principal direct INSERT/UPDATE/DELETE = DENIED
command_credential_revision direct INSERT/UPDATE/DELETE = DENIED
command_permission_grant direct INSERT/UPDATE/DELETE = DENIED
command_authority_operation direct INSERT/UPDATE/DELETE = DENIED

V040 governance direct SELECT/DML = DENIED
V041 accepted-attestation direct SELECT/DML = DENIED
V042 consumption direct SELECT/DML = DENIED

narrow issuer snapshot capability = EXECUTE
narrow attested PRINCIPAL apply = EXECUTE
narrow attested INITIAL_CREDENTIAL apply = EXECUTE
narrow attested GRANT apply = EXECUTE
```

No direct-table privilege may be retained merely to keep
`PostgresControlledCommandAuthorityIssuer` functional.

### Migration integrity preflight

V042 is forward-only hardening. It must never silently rewrite predecessor
history so that new constraints appear to pass.

Before privilege cutover or addition of exact target foreign keys, migration
must fail if any existing `command_authority_operation` is inconsistent with
its referenced credential/grant tuple.

At minimum preflight rejects:

```text
credential operation with missing credential target
credential operation principal != credential principal
credential operation revision/state mismatch

grant/revoke operation with missing grant target
operation principal != grant principal
operation grant_revision != grant revision
operation permission != grant permission
operation state != grant state
```

The migration also rejects protected-role membership contamination before
granting new V042 capabilities.

There is:

```text
NO DELETE
NO UPDATE REPAIR
NO HISTORY REWRITE
NO PRIVILEGE FALLBACK
```

on preflight failure.

The migration transaction aborts unchanged.

### Revision 4 state

```text
REVISION_3_ADVERSARIAL_REVIEW = FAILED
REVISION_4_CORRECTIONS = MATERIALIZED

V042_IMPLEMENTATION = HOLD
V042_MIGRATION = HOLD
REAL_FIELD_PROOF = HOLD

NEXT_GATE = V042_REVISION_4_CONTRACT_PACKAGE_ADVERSARIAL_REVIEW
```

## Revision 5 adversarial corrections

This section is controlling wherever it conflicts with Revisions 1 through 4.

Revision 4 failed adversarial review. No implementation is authorized.

### Self-contained privileged apply locking

Every V042 SECURITY DEFINER apply capability must be serializable by itself.

A capability must never depend on the Kotlin caller having already acquired a
required lock.

Outer Kotlin locking remains defense in depth and preserves current writer
ordering, but direct EXECUTE of an allowed capability must not create a race.

For attested command-authority effects the apply capability reacquires, in the
frozen order:

```text
organization FOR SHARE
-> operation-ID advisory lock
-> exact replay lookup
-> principal advisory lock
-> principal FOR UPDATE when present
-> attestation advisory lock
-> exact accepted-attestation / consumption lookup
-> signer-key advisory lock
-> signer-authority-scope advisory lock
-> final artifact/currentness comparison
-> effect
```

Advisory and row-lock reacquisition in the same transaction is intentional and
must be harmless/reentrant.

For the final attested transaction-identity effect the apply capability
reacquires the existing writer locks before the one-action guard:

```text
organization FOR SHARE
-> principal FOR UPDATE
-> decision-ID advisory lock
-> Omie V3 progress FOR UPDATE
-> sorted subject/target advisory locks
-> exact linked GRANT / manifest / consumption
-> attestation advisory lock
-> signer-key advisory lock
-> signer-authority-scope advisory lock
-> final currentness/evidence checks
-> one-action guard
-> decision INSERT
```

Therefore the single-decision guard executes only after the principal lock is
owned by that same transaction.

Two direct calls with different decision IDs but the same real S2A grant cannot
both observe an admissible zero-decision state.

### Preserve V035/V036 through split decision apply

V042 revokes direct runtime INSERT on the decision table, but it must not erase
the already frozen V035/V036 writer semantics for historical/synthetic
unlinked grants.

After V042 there are two narrow decision-apply classes:

```text
ATTESTED APPLY
- requires exactly one non-null linked GRANT authority operation
- requires exact consumption and accepted attestation
- requires V042 Java/currentness path
- permits only one new root CONFIRMED action

LEGACY-UNLINKED APPLY
- requires no non-null attestation linkage for the authorized grant
- preserves existing V035/V036 decision semantics
- performs the existing database validations/triggers
- cannot be used for any attested grant
```

Both are narrow SECURITY DEFINER boundaries.

Direct table INSERT by `flooow_command_runtime` remains denied.

The legacy-unlinked capability is not an authority-provisioning path. It cannot
create principals, credentials, grants, authority operations, consumption, or
accepted attestations.

A grant with any matching non-null attestation-linked GRANT operation is
categorically ineligible for legacy-unlinked apply.

This preserves predecessor behavior without creating an S2A escape hatch.

### Writer routing by immutable grant lineage

After current command authorization and decision-ID replay classification, a
new writer effect resolves the authorized grant:

```text
organizationId
principalId
grantId
grantRevision
permission
```

Routing is:

```text
exactly one matching non-null linked GRANT operation
=> ATTESTED APPLY path

zero matching non-null linked GRANT operations
=> LEGACY-UNLINKED APPLY path

more than one
=> IntegrityFailure
```

The matching linked GRANT must satisfy the exact Revision 4 composite grant
tuple and the operation-to-consumption principal FK.

Application request flags cannot choose the route.

### Attested decision fields derived from the signed manifest

For a new real S2A field-proof decision, the final action is fixed:

```text
kind = CONFIRMED
reason = EXPLICIT_CONFIRMATION
revision = 1
supersedesDecisionId = NULL
permission = TRANSACTION_IDENTITY_DECISION_WRITE
```

The following decision inputs must equal the decoded retained manifest:

```text
sourceOrderReference = manifest.sourceOrderReference
marketplaceOrderId = manifest.marketplaceOrderId
provenance = manifest.provenance
correlationId = manifest.correlationId
```

The actor connection pair must equal the manifest ML/Omie connection pair.

`integrationReference` is validated through the current durable Omie evidence
binding already required by V042.

`decisionId` is not a manifest field. It remains the idempotency identity of
the single execution attempt, but the one-action grant invariant prevents a
second distinct decision ID from creating another effect.

For exact committed decision replay, existing V035/V036 semantics remain:

```text
current command authorization first
same decisionId + same intent
=> AlreadyApplied

changed intent
=> IntegrityFailure
```

A retry may supply a different correlation ID only because replay returns the
stored immutable decision before new-effect V042 admission. It never rewrites
the originally stored manifest correlation ID.

### Controlling final writer order

Revision 3 writer ordering is refined to preserve the established V035/V036
lock sequence before adding the V042 lifecycle locks.

For a new decision:

```text
authenticate
-> authorizeForWrite
-> compute writer intent
-> decision-ID advisory lock
-> exact replay lookup

IF new:
    -> existing transaction_identity_locks
       organization
       principal
       decision ID
       progress
       subject/target
    -> existing target/evidence resolution
    -> resolve exact authorized GRANT route

    IF legacy-unlinked:
        -> final authorizeForWrite
        -> legacy-unlinked apply
        -> existing triggers/head

    IF attested:
        -> acquire attestation/key/authority locks
        -> obtain exact V042 snapshot
        -> strict canonical decode/reconstruction
        -> Java 21 JCA Ed25519 verification
        -> final authorizeForWrite
        -> attested apply reacquires canonical locks
        -> fresh effectTime/currentness/evidence comparison
        -> manifest-derived action-field check
        -> one-action guard
        -> INSERT
        -> existing triggers/head
```

The V042 attestation/key/authority locks are therefore added after the frozen
writer progress/subject/target fences for a new decision.

No provider/network call occurs while these locks are held.

### Direct-call concurrency proof

The following is a mandatory database test independent from the Kotlin writer:

```text
two transactions
same organization
same principal
same linked S2A grant
different decisionId

both call the attested apply capability directly
```

Expected:

```text
one transaction may apply
the other blocks on the canonical lock
after wakeup it observes the committed grant usage
=> IntegrityFailure
total new decision delta = 1
total new head delta = 1
```

A pre-lock `count=0` observation is not authority and must not exist in the
apply implementation.

### Revision 5 state

```text
REVISION_4_ADVERSARIAL_REVIEW = FAILED
REVISION_5_CORRECTIONS = MATERIALIZED

V042_IMPLEMENTATION = HOLD
V042_MIGRATION = HOLD
REAL_FIELD_PROOF = HOLD

NEXT_GATE = V042_REVISION_5_CONTRACT_PACKAGE_ADVERSARIAL_REVIEW
```

## Revision 6 adversarial corrections

This section is controlling wherever it conflicts with Revisions 1 through 5.

Revision 5 failed adversarial review. No implementation is authorized.

### V042 composite trusted-computing boundary

V042 inherits the same cryptographic trust fact already frozen for V041:

```text
PostgreSQL cannot prove that an external Java 21 JCA Ed25519 verification
occurred without itself becoming the Ed25519 verification authority.
```

V042 therefore introduces no fake boolean, nonce, temporary-table marker,
session variable, or caller-supplied "verified" token.

For real attested command-authority provisioning, the trusted boundary is:

```text
dedicated V042 issuer service principal
+ JVM issuer implementation
+ Java 21 JCA Ed25519
+ flooow_command_issuer capability
+ one caller-owned JDBC transaction
+ PostgreSQL governance/currentness/serialization/apply capabilities
```

For real attested transaction-identity execution, the trusted boundary is:

```text
dedicated governed writer service principal
+ JVM writer implementation
+ Java 21 JCA Ed25519
+ flooow_command_runtime capability
+ one caller-owned JDBC transaction
+ PostgreSQL governance/currentness/serialization/apply capabilities
```

Trust classification:

```text
Java 21 JCA = Ed25519 verification authority

PostgreSQL =
tenancy
governance/currentness
durable evidence
serialization
replay
referential integrity
immutability
effect-time eligibility
exact mutation authority

issuer/runtime capability identity =
security-sensitive application TCB
```

Compromise or unauthorized direct use of the dedicated issuer/runtime service
database identity is TCB compromise. It is not a supported alternate API.

This trust statement does not weaken:

```text
POSTGRES_ED25519_AUTHORITY = NO
JAVA_21_JCA_ED25519_AUTHORITY = YES
V042_MUST_DENY_UNLESS_INDEPENDENT_REVERIFICATION_PASSES = YES
```

It states where that invariant is enforced.

### Deployment membership boundary

V042 migration creates or hardens capabilities only. It creates no production
login credential and assigns no human/operator membership.

At real deployment:

```text
flooow_command_issuer
```

may have only the separately governed dedicated issuer service principal as an
ordinary inbound operational member.

```text
flooow_command_runtime
```

may have only separately governed dedicated runtime/writer service principals
whose use is limited to the governed runtime boundary.

Human/operator membership is forbidden.

Outbound membership from protected roles is forbidden.

Cross-membership among:

```text
flooow_approval_governance
flooow_attestation_verifier
flooow_command_issuer
flooow_command_runtime
```

is forbidden.

Production membership assignment remains outside V042 implementation and
outside the real-field-proof authorization.

### Database tests must not claim Java verification

Direct database tests of attested apply capabilities validate only:

```text
role isolation
argument/snapshot binding
database recomputation
lock ownership
serialization
currentness
referential integrity
single-action enforcement
replay
rollback
mutation scope
```

They must not claim that PostgreSQL proves Ed25519 validity or that a direct
SQL call demonstrates full production admission.

A direct apply test is a privileged TCB-structural test.

End-to-end JVM tests prove:

```text
failed Java JCA verification
=> apply capability is never invoked
=> command-authority / decision deltas = 0
```

and:

```text
successful Java JCA verification
+ exact DB snapshot/currentness
=> apply may be invoked in the same transaction
```

### Legacy-unlinked apply owns the frozen writer locks

The Revision 5 self-contained-lock rule applies explicitly to the
legacy-unlinked decision capability.

Before classifying lineage or inserting a legacy-unlinked decision it obtains:

```text
organization FOR SHARE
-> principal FOR UPDATE
-> decision-ID advisory lock
-> Omie V3 progress FOR UPDATE when required by the decision kind
-> sorted subject/target advisory locks
-> current command-authority tuple
-> linked-GRANT absence check
-> existing V035/V036 validation
-> INSERT
```

For WITHDRAWN it uses the frozen V036 withdrawal lock/evidence shape rather
than inventing a V035 evidence reacquisition requirement.

The linked-GRANT absence check occurs while the principal lock is owned by the
same transaction.

A direct call cannot bypass route classification.

### SECURITY DEFINER owner and caller contract

Every new V042 SECURITY DEFINER capability must:

```text
be owned by the controlled migration/security owner
not be owned by any protected operational role
use SET search_path = pg_catalog, pg_temp
use schema-qualified protected object references
contain no dynamic SQL
revoke EXECUTE from PUBLIC
grant EXECUTE only to the exact intended protected capability role
not grant ALTER/ownership on the function to a protected operational role
```

Protected operational roles must not own protected V042 tables, functions,
indexes, constraints, or triggers.

Authorization to call the function is established by PostgreSQL EXECUTE
privilege and the protected role graph.

If a function performs an additional explicit membership assertion, it must
evaluate the invoker identity rather than accidentally treating the
SECURITY DEFINER owner as the caller. `current_user` inside a
SECURITY DEFINER body must not be used as proof that the invoker is the
protected role.

Administrative database owner/migration owner/superuser trust remains outside
the ordinary operational-caller model.

### Route classification is repeated inside the apply capability

Kotlin route selection is not persistence authority.

The attested apply capability independently proves:

```text
exactly one matching non-null linked GRANT
```

before any new attested decision effect.

The legacy-unlinked apply capability independently proves:

```text
zero matching non-null linked GRANT rows
```

before any new legacy decision effect.

These checks occur under the capability-owned principal lock.

A route classification mismatch between JVM expectation and database reality
is integrity failure.

### Revision 6 state

```text
REVISION_5_ADVERSARIAL_REVIEW = FAILED
REVISION_6_CORRECTIONS = MATERIALIZED

V042_IMPLEMENTATION = HOLD
V042_MIGRATION = HOLD
REAL_FIELD_PROOF = HOLD

NEXT_GATE = V042_REVISION_6_CONTRACT_PACKAGE_ADVERSARIAL_REVIEW
```

## Revision 7 adversarial correction

This section is controlling wherever it conflicts with Revisions 1 through 6.

Revision 6 failed adversarial review with one remaining execution-time
key-continuity HIGH. No implementation is authorized.

### Accepted signing key must equal the execution-time effective key

V042 does not merely require that some current signer key is eligible.

For every new V042 command-authority effect and every new attested
transaction-identity effect, the key that signed the immutable accepted
attestation must be the exact key revision that is effective at final
`effectTime`.

Under the signer-key advisory lock V042 must:

1. validate the complete structural key lineage;
2. require exactly one structural leaf;
3. select the effective revision as the highest revision with
   `effective_at <= effectTime`;
4. require the effective revision state to be `ACTIVE`;
5. require the retained accepted artifact to bind that exact effective
   revision.

The following values must all agree:

```text
accepted artifact signerKeyId
= effective signer_key_id

accepted artifact signerKeyRevision
= effective revision

accepted artifact signerKeyFingerprint
= effective signer_key_fingerprint

accepted artifact signerKeyLineageFingerprint
= recomputed effective lineage_fingerprint

accepted artifact subjectPublicKeyInfoDer
= effective subject_public_key_info_der

accepted artifact algorithmId
= effective algorithm_id
= Ed25519
```

The signer subject used for current authority resolution is not caller-owned.
It is the signer subject of that exact effective/historical key row.

Current signer authority must then bind:

```text
same organization
same signerSubjectId
same signerKeyId
same effective signerKeyRevision
same effective signerKeyFingerprint
S2A_FIELD_PROOF_APPROVER
S2A_FIELD_PROOF_APPROVAL
TRANSACTION_IDENTITY_DECISION_WRITE
decoded manifest approvalSource
ENABLED
validFrom <= effectTime < validUntil
```

A current authority successor may be a later authority revision than the
authority revision retained in the historical accepted proof, provided it
authorizes that same exact effective signing key and exact frozen scope.

The historical accepted signer-authority revision remains immutable evidence;
it is not required to remain the structural-current authority row.

### Rotation semantics

A future key successor whose:

```text
effective_at > effectTime
```

does not prematurely invalidate an attestation signed by the still-effective
predecessor.

Once the successor becomes effective:

```text
accepted signerKeyRevision != execution-time effective revision
```

and the old attestation is not eligible for a new V042 effect.

No historical accepted evidence is deleted or rewritten.

Exact already-committed operation replay remains historical and continues to
follow the frozen replay rules; this key-continuity rule governs only a new
authority or decision effect.

### Failure classification

For a new effect:

```text
no effective key
or effective key state RETIRED/REVOKED/COMPROMISED
=> ExpiredOrNotYetValid

accepted artifact signer-key revision/fingerprint/lineage/SPKI/algorithm
does not equal the execution-time effective key
=> ScopeMismatch

current signer authority does not bind that exact effective key
=> ScopeMismatch

forked/ambiguous/corrupt key or authority lineage
=> GovernanceConflict or IntegrityFailure according to the frozen condition
```

All failures are zero-effect.

### Revision 7 state

```text
REVISION_6_ADVERSARIAL_REVIEW = FAILED
REVISION_7_CORRECTIONS = MATERIALIZED

V042_IMPLEMENTATION = HOLD
V042_MIGRATION = HOLD
REAL_FIELD_PROOF = HOLD

NEXT_GATE = V042_REVISION_7_CONTRACT_PACKAGE_ADVERSARIAL_REVIEW
```

## Revision 8 adversarial correction

This section is controlling wherever it conflicts with Revisions 1 through 7.

Revision 7 failed adversarial review because it incorrectly treated a V040
signer-key lifecycle revision as if it were a distinct cryptographic signing
key.

No implementation is authorized.

### Historical key revision is not cryptographic signing identity

V040 freezes signer-key successors for the same `signer_key_id` to the same:

```text
signerSubjectId
algorithmId
subjectPublicKeyInfoDer
signerKeyFingerprint
validFrom
```

A successor revision changes lifecycle/governance state and effective time. It
does not rotate the Ed25519 public-key material.

The approval signature preimage binds:

```text
signerKeyId
signerKeyFingerprint
```

and does not bind `signerKeyRevision`.

Therefore:

```text
accepted.signerKeyRevision
accepted.signerKeyLineageFingerprint
```

are historical governance evidence captured at V041 acceptance. They are not
the cryptographic identity of the signature and must not be required to equal
the execution-time effective revision/lineage fingerprint.

### Historical accepted-key verification

Before any V042 new effect, V042 still independently verifies the historical
accepted proof.

Using:

```text
organizationId
accepted.signerKeyId
accepted.signerKeyRevision
```

it loads the exact historical V040 key row and requires:

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

It recomputes the historical lineage fingerprint and SPKI fingerprint before
Java JCA reverification.

Any mismatch is retained-proof integrity failure.

### Execution-time effective-key continuity

Separately, under the same signer-key advisory lock, V042 resolves the
execution-time effective lifecycle revision:

```text
effective revision
= highest revision with effective_at <= effectTime
```

and validates the complete structural lineage.

The effective row must satisfy:

```text
effective.state = ACTIVE

effective.signerKeyId
= accepted.signerKeyId

effective.signerKeyFingerprint
= accepted.signerKeyFingerprint

effective.subjectPublicKeyInfoDer
= accepted.subjectPublicKeyInfoDer

effective.algorithmId
= accepted.algorithmId
= Ed25519

effective.signerSubjectId
= historical.signerSubjectId
```

V042 independently recomputes the effective revision's lineage fingerprint.

It does not require:

```text
accepted.signerKeyRevision
= effective.revision
```

and does not require:

```text
accepted.signerKeyLineageFingerprint
= effective.lineageFingerprint
```

because those values intentionally describe different lifecycle revisions.

### Current authority still binds the effective revision

Execution-time signer authority remains strict.

The current authority must bind the exact execution-time effective:

```text
signerSubjectId
signerKeyId
signerKeyRevision
signerKeyFingerprint
```

plus the frozen role, action, permission, approval source, state and time
window.

Therefore an ACTIVE lifecycle successor does not automatically authorize a new
effect.

If the current authority still binds the historical revision while a later
revision is effective:

```text
=> ScopeMismatch
=> zero effect
```

V042 never repairs or advances V040 authority.

### Key-material rotation

V040 does not allow a successor revision under one `signer_key_id` to change
SPKI or key fingerprint.

A cryptographic key-material rotation therefore requires a different governed
key identity rather than reinterpretation of a lifecycle revision.

An accepted artifact remains bound to its signed:

```text
signerKeyId
signerKeyFingerprint
SPKI
```

and cannot silently migrate to a different cryptographic key.

### Temporal examples

If revision 2 is a future lifecycle successor of the same cryptographic key:

```text
effectTime < revision2.effectiveAt
=> revision 1 is effective
```

If every other gate passes, historical accepted revision 1 can be used for a
new effect.

After:

```text
effectTime >= revision2.effectiveAt
```

revision 2 is effective.

The historical accepted revision 1 is not rejected merely because the revision
number changed.

A new effect is allowed only if:

```text
revision 2 remains ACTIVE
cryptographic identity is unchanged as required by V040
current authority binds revision 2 exactly
all other V042 gates pass
```

Otherwise the new effect is denied.

Exact already-committed replay remains historical and unchanged.

### Revision 8 state

```text
REVISION_7_ADVERSARIAL_REVIEW = FAILED
REVISION_8_CORRECTIONS = MATERIALIZED

V042_IMPLEMENTATION = HOLD
V042_MIGRATION = HOLD
REAL_FIELD_PROOF = HOLD

NEXT_GATE = V042_REVISION_8_CONTRACT_PACKAGE_ADVERSARIAL_REVIEW
```

## Revision 9 adversarial correction

This section is controlling wherever it conflicts with Revisions 1 through 8.

Revision 8 failed adversarial review because it described an execution-time
authority state that the frozen V040 model cannot represent.

No implementation is authorized.

### V040 authority lineage cannot rebind signer-key revision

V040 signer-authority succession is intentionally narrower than signer-key
lifecycle succession.

For one signer-authority scope, a successor authority row must preserve the
predecessor:

```text
signerSubjectId
signerAuthorizingInstitutionId
signerRole
signerKeyId
signerKeyRevision
signerKeyFingerprint
approvalAction
permission
validFrom
validUntil
approvalSourceId
```

Therefore an existing V040 authority lineage bound to signer-key revision 1
cannot later produce a successor bound to signer-key revision 2.

V042 must not alter V040 tables, triggers, append functions, lineage rules, or
authority semantics merely to make such rebinding possible.

### Controlling execution consequence

Revision 8 remains correct that historical accepted-key revision and
execution-time effective key revision are distinct lifecycle facts.

However, current execution authority remains exact:

```text
currentAuthority.signerKeyRevision
= effectiveKey.revision

currentAuthority.signerKeyFingerprint
= effectiveKey.signerKeyFingerprint
```

Because V040 cannot rebind an existing authority lineage to another key
revision, the consequence is:

```text
accepted historical key revision = 1
effective lifecycle revision = 2
current authority remains bound to revision 1

=> ScopeMismatch
=> zero new V042 effect
```

This remains true even when revision 2 is `ACTIVE` and preserves the same
Ed25519 SPKI and key fingerprint.

The denial is not because the historical signature became cryptographically
invalid. It is because current V040 execution authority no longer binds the
effective lifecycle revision.

### Future lifecycle successor

A future structural successor does not invalidate early.

If:

```text
revision2.effectiveAt > effectTime
```

revision 1 remains effective.

An accepted artifact historically verified with revision 1 may remain eligible
when the current authority binds revision 1 and every other V042 gate passes.

At the exact transition where revision 2 becomes effective:

```text
effectiveKey.revision = 2
currentAuthority.signerKeyRevision = 1
```

the old attestation becomes ineligible for any new V042 authority or identity
effect.

### Restoring future execution is outside reinterpretation

V042 must not reinterpret the old accepted attestation or mutate V040
governance to restore liveness.

Future governed execution after such a lifecycle transition requires a
separately valid governance/attestation state supported by the frozen model,
for example a separately governed key identity and a newly accepted
attestation for that key/scope.

The exact future operational ceremony is outside V042 unless separately
specified and reviewed.

No old attestation is silently rebound to a different `signerKeyId` or key
revision.

### Historical evidence and replay

The V041 accepted artifact remains immutable historical evidence.

Its historical key revision and lineage fingerprint remain independently
recomputable.

Already-committed exact operation replay and exact identity-decision replay
remain governed by their frozen historical replay rules and create no new
effect.

### Revision 9 state

```text
REVISION_8_ADVERSARIAL_REVIEW = FAILED
REVISION_9_CORRECTIONS = MATERIALIZED

V042_IMPLEMENTATION = HOLD
V042_MIGRATION = HOLD
REAL_FIELD_PROOF = HOLD

NEXT_GATE = V042_REVISION_9_CONTRACT_PACKAGE_ADVERSARIAL_REVIEW
```
