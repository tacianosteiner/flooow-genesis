# SPEC-0088 - S2A canonical approval manifest and verification contract

## Status and scope

FINAL DESIGN CLOSURE - REVISION 4.

This specification defines the contract shape for a future signed approval-attestation boundary.

It authorizes no implementation, migration, production key, signer registry, launcher activation, authority provisioning, provider request, or real identity decision.

Source decision: ADR-0088.

## Security invariants

```text
SIGNED MANIFEST != AUTHORITY
SIGNATURE VALID != SIGNER AUTHORIZED
VERIFIED APPROVAL != EXECUTION
AUTHORITY != EXECUTION
EVIDENCE != AUTHORITY
MISSING != ZERO
UNRESOLVED AUTHORITY REMAINS UNRESOLVED
FAIL CLOSED
```

## Canonical approval manifest v1

The logical v1 manifest contains exactly:

```text
schemaVersion
manifestId
organizationId
mercadoLivreConnectionId
omieConnectionId
sourceOrderReference
integrationReference
marketplaceOrderId
permission
accountableOperator
approvalSource
approvalWindowStart
approvalWindowEnd
revocationOwner
credentialCustodian
credentialDeliveryMethod
credentialRotationOwner
immediateRevocationPolicy
reason
provenance
correlationId
evidenceBindingFingerprint
```

The v1 schema excludes:

```text
principalId
credentialId
grantId
```

`permission` must equal exactly:

```text
TRANSACTION_IDENTITY_DECISION_WRITE
```

Blank values, malformed UUIDs, malformed timestamps, unsupported schema versions, duplicate fields, absent required fields, or semantically inconsistent values deny verification.

Unknown fields are rejected by default in v1.

Signed descriptive fields do not self-authorize. In particular, `approvalSource`, `accountableOperator`, and signer labels must never substitute for the independent signer-authorization source.

## Normalization

Before canonical encoding:

- UUIDs use canonical lowercase hyphenated representation;
- timestamps represent a single normalized `Instant`;
- the exact canonical timestamp byte representation must be frozen before implementation;
- strings are UTF-8 and nonblank;
- permission uses its exact enum token;
- locale-dependent transformations are prohibited;
- environment-dependent values are prohibited;
- implicit defaults are prohibited.

Human identities and policy-bearing values must ultimately use stable identifiers or versioned policy references where they affect verification semantics.

## Canonical byte encoding

Manifest domain:

```text
FLOOOW:S2A:APPROVAL-MANIFEST:1
```

The proposed v1 encoding is a deterministic length-prefixed UTF-8 stream.

Fields are encoded in the frozen schema order.

Conceptually:

```text
field-name-byte-length ":" field-name
value-byte-length      ":" value
```

Raw JSON bytes are not signed.

JSON may remain an operator-facing transport representation.

Golden vectors are mandatory before implementation can be considered proven.

## Manifest digest

```text
manifestDigest = SHA-256(canonical-manifest-bytes)
```

The digest is nonsecret.

It is not authority and is not a credential.

## Evidence binding fingerprint

`evidenceBindingFingerprint` must bind the exact provider-evidence context approved for the field proof.

It must be derived only from canonical nonsecret evidence identity/currentness facts.

The exact ordered v1 input set is not yet frozen and must be defined with golden vectors before implementation.

A mismatch between signed evidence binding and execution-time evidence:

```text
=> DENY
=> REQUIRE NEW APPROVAL
```

The writer still independently performs authoritative currentness validation.

## Signed envelope

Logical envelope:

```text
manifest
algorithmId
signerKeyId
signerKeyFingerprint
signature
```

The algorithm and key identity must be explicit.

They must not be inferred from machine configuration.

The private key is never persisted as approval evidence.

## Signature preimage

Security-relevant envelope metadata must be cryptographically bound.

Proposed signature domain:

```text
FLOOOW:S2A:APPROVAL-SIGNATURE:1
```

Proposed logical preimage:

```text
algorithmId
signerKeyId
signerKeyFingerprint
manifestDigest
```

encoded deterministically under the frozen canonical encoding.

Changing `algorithmId`, signer key ID, signer key fingerprint, or manifest digest invalidates the signature.

Envelope unknown fields are rejected by default in v1.

## Signature algorithm candidates

```text
Ed25519      = PROPOSED PRIMARY
ECDSA P-256  = PROPOSED COMPATIBILITY
RSA-PSS      = NOT SELECTED FOR INITIAL DESIGN
```

No algorithm is frozen yet.

Algorithm agility must not permit downgrade.

## Signer identity and authorization

Cryptographic verification and authorization are distinct gates.

The verifier must resolve from an independently trusted source:

```text
signerKeyId
-> canonical public key
-> signer identity / institutional role
-> authorization scope
-> key lifecycle state
```

Signer authorization must cover:

- exact organization;
- S2A field-proof approval action;
- `TRANSACTION_IDENTITY_DECISION_WRITE`;
- bounded approval window.

A valid signature from an unknown, revoked, expired, or unauthorized signer denies execution.

`command_permission_grant` is not signer authorization.

The signer-authorization source must be versioned, bounded, revocable, and independently trustworthy. Its concrete implementation remains UNFROZEN.

## Key lifecycle requirements

The future contract must define:

- key generation responsibility;
- private-key custody;
- verification-key distribution;
- stable key ID;
- public-key fingerprint;
- activation time;
- retirement time;
- compromise/revocation semantics;
- rotation lineage;
- historical verification.

Historical verification does not imply current execution eligibility.

A compromised or revoked key must fail new execution admission according to the frozen temporal policy.

No production key or signer identity may be invented by implementation code.

External KMS or HSM products are optional deployment choices, not requirements of this design.

## Single-use manifest consumption

Manifest replay is independent from issuer replay and writer replay.

`manifestId` identifies one bounded approval ceremony and may create at most one command-principal root.

The accepted attestation may support the expected authority-operation sequence for that one root:

```text
PRINCIPAL
INITIAL_CREDENTIAL
GRANT
```

but must not authorize a second principal root.

A future consumption guard must enforce:

```text
manifestId unseen + valid digest
=> eligible for verification

same manifestId + same digest + same consumption lineage
=> idempotent recovery only

same manifestId + same digest + different authority root
=> DENY

same manifestId + different manifestDigest
=> INTEGRITY FAILURE
```

The concrete storage/locking model for consumption remains UNFROZEN.

## Verified attestation evidence

A future implementation may persist a separate immutable non-authoritative accepted-attestation record.

It:

- may exist before a principal exists;
- must not require a principal or grant foreign key;
- must not represent permission;
- must not contain raw credential or private-key material;
- must be immutable if persisted;
- must preserve enough nonsecret material for later independent cryptographic re-verification.

Conceptually retain or immutably reference:

```text
organization_id
manifest_id
schema_version
canonicalization_version
canonical_manifest_bytes_or_lossless_artifact
manifest_digest
algorithm_id
signer_key_id
signer_key_fingerprint
signature
approval_window_start
approval_window_end
evidence_binding_fingerprint
correlation_id
approval_source
provenance
verified_at
signer_authorization_lineage_reference
```

Record existence means the attestation was accepted. A mutable `verification_status` is not part of the accepted-attestation truth.

Failed verification attempts are not accepted attestations.

The actual migration, table name, indexes, retention model, artifact representation, and locking model remain UNFROZEN.

## Mandatory authority-provisioning binding

Launcher verification alone is insufficient.

Future real authority provisioning must itself require an accepted attestation binding.

A direct authority-provisioning request without that binding must deny.

At minimum the provisioning boundary must be able to establish:

```text
accepted attestation exists
manifest is not expired
manifest has not been consumed by another authority root
organization matches
target matches
permission matches
evidence binding matches the approved contract
request belongs to the same attestation consumption lineage
```

The exact request field, database constraint, verifier capability, transaction arrangement, and role topology remain UNFROZEN.

The existing command-authority tables remain the only command-authority substrate.

## Relationship to command authority

The existing issuer operations remain:

```text
PRINCIPAL
INITIAL_CREDENTIAL
ROTATE_CREDENTIAL
GRANT
REVOKE
```

No `APPROVAL` operation is introduced.

Future authority requests must preserve a nonsecret link to the accepted approval attestation.

The exact linkage representation remains UNFROZEN.

Credential rotation and later revocation are not automatically authorized by the original field-proof manifest; their authority source must follow the separately frozen operational contract.

## Verification state machine

```text
RECEIVED
-> STRUCTURALLY_VALID
-> CANONICALIZED
-> DIGESTED
-> SIGNATURE_VALID
-> SIGNER_IDENTIFIED
-> SIGNER_AUTHORIZED
-> WINDOW_VALID
-> TARGET_VALID
-> EVIDENCE_BINDING_VALID
-> REPLAY_VALID
-> VERIFIED_ATTESTATION_RECORDED
```

Any failure is terminal denial for that attempt.

No intermediate state creates command authority.

## Ceremony integration

```text
load manifest
-> structural validation
-> canonicalize
-> digest
-> verify signed envelope
-> resolve signer identity
-> verify signer authorization
-> validate approval window
-> validate exact target
-> re-read durable evidence
-> validate evidence binding
-> validate replay/collision
-> persist accepted attestation evidence
-> existing read-only preflight

ONLY THEN:

-> generate credential
-> issue principal with mandatory attestation binding
-> bind credential revision 1 within the same consumption lineage
-> protected TTY delivery
-> grant TRANSACTION_IDENTITY_DECISION_WRITE within the same consumption lineage
-> authenticate
-> destroy raw credential
-> existing writer transaction
-> post-proof verification
-> optional separately approved revoke
```

ADR/SPEC-0087 writer ordering remains unchanged.

## Failure contract

Every attestation failure before credential generation must produce:

```text
command_principal delta = 0
credential_revision delta = 0
permission_grant delta = 0
command_authority_operation delta = 0
identity_decision delta = 0
identity_head delta = 0
```

Failure to enforce accepted-attestation binding at authority provisioning is a BLOCKER, even when the launcher verifies correctly.

## Required adversarial matrix

Before implementation can be proven:

- canonical golden vectors;
- signature-preimage golden vectors;
- equivalent logical manifest -> identical canonical bytes;
- transport field reordering does not change canonical bytes;
- changed field changes digest;
- changed algorithmId invalidates signature;
- changed signerKeyId invalidates signature;
- changed signerKeyFingerprint invalidates signature;
- duplicate field rejected;
- unknown manifest field rejected;
- unknown envelope field rejected;
- malformed UUID rejected;
- malformed timestamp rejected;
- tampered manifest rejected;
- tampered signature rejected;
- wrong key rejected;
- revoked key rejected;
- unauthorized signer rejected;
- self-declared `approvalSource` cannot authorize a signer;
- unsupported algorithm rejected;
- downgrade rejected;
- expired approval rejected;
- future approval rejected;
- wrong organization rejected;
- wrong ML connection rejected;
- wrong Omie connection rejected;
- wrong sourceOrderReference rejected;
- wrong integrationReference rejected;
- wrong marketplaceOrderId rejected;
- wrong permission rejected;
- POLICY_ADMIN rejected;
- duplicate manifest handled idempotently;
- manifestId collision rejected;
- same manifest cannot create second principal root;
- direct issuer call without accepted attestation denied;
- mismatched attestation/request denied;
- replay after authority issuance does not create second authority;
- evidence changed after signing rejected;
- accepted attestation remains independently re-verifiable after key rotation;
- revoked/compromised key cannot authorize new execution under the frozen temporal policy;
- verification success plus writer denial remains safe;
- unprotected TTY remains rejected;
- credential still destroyed before writer;
- issuer/runtime privilege crossover denied;
- secret/signing private material absent from logs and receipts;
- attestation persistence failure leaves zero command-authority mutation.

## Current adversarial findings

```text
BLOCKER:
- authority provisioning must enforce accepted-attestation binding, not launcher only;
- single-use attestation consumption must prevent a second command-principal root;
- independently trusted signer-authorization source remains unfrozen;
- signed envelope metadata binding must be frozen before implementation.

HIGH:
- evidenceBindingFingerprint v1 input set is unfrozen;
- key revocation/retirement temporal semantics are unfrozen;
- canonical timestamp representation is unfrozen;
- accepted-attestation retention must support later cryptographic re-verification.

MEDIUM:
- stable representation of human identities and policy references is unfrozen;
- concrete authority-operation-to-attestation linkage is unfrozen;
- storage/index/locking shape is unfrozen.
```

No finding authorizes implementation.

## Blocker closure revision 2

The four adversarial BLOCKER findings are resolved by the following frozen v1 contracts.

### Attestation-aware real issuer boundary

Launcher-only enforcement is prohibited.

The future real issuer role has no direct INSERT privilege on command authority or authority-operation tables.

The real path may mutate those tables only through narrow attestation-aware database capabilities.

Each capability must atomically validate the accepted attestation and exact consumption lineage before the corresponding authority mutation.

No general-purpose SECURITY DEFINER function is permitted.

The implementation must prove direct issuer SQL INSERT denial separately from successful attested provisioning.

### Accepted attestation and consumption

Accepted attestation identity:

```text
organizationId + manifestId
```

Consumption identity:

```text
organizationId + manifestId
```

The consumption record binds:

```text
manifestDigest
principalId
correlationId
consumedAt
```

It is append-only and unique for the attestation.

Principal creation, consumption insertion, and PRINCIPAL authority-operation receipt are one atomic transaction.

Initial credential binding and grant issuance require the existing consumption row and exact same principal.

No second principal root is legal for the same accepted attestation.

Same request replay may resolve to the same immutable operation lineage only.

### Signer authorization source v1

Signer authorization comes from an independent append-only approval-governance lineage, not manifest self-claims and not `command_permission_grant`.

Required logical fields:

```text
organizationId
signerAuthorityId
revision
signerSubjectId
signerKeyId
signerKeyFingerprint
approvalAction
permission
validFrom
validUntil
state
supersedesSignerAuthorityId
reason
provenance
correlationId
decidedAt
```

For S2A v1:

```text
approvalAction = S2A_FIELD_PROOF_APPROVAL
permission = TRANSACTION_IDENTITY_DECISION_WRITE
```

The current valid leaf must match the exact organization, key, action, permission, and approval time.

The signer cannot create or revise its own authorization.

No active approved signer-authority lineage means DENY.

The concrete human values remain absent and must not be inferred.

### Signature contract v1

Frozen algorithm:

```text
Ed25519
```

Frozen signature domain:

```text
FLOOOW:S2A:APPROVAL-SIGNATURE:1
```

Frozen public-key fingerprint:

```text
SHA-256(DER SubjectPublicKeyInfo public-key bytes)
=> lowercase hexadecimal
```

Frozen signer key ID:

```text
canonical UUID
```

Frozen signature transport:

```text
canonical base64url without padding
```

Frozen signed logical fields, in order:

```text
algorithmId
signerKeyId
signerKeyFingerprint
manifestDigest
```

with:

```text
algorithmId = Ed25519
```

The record uses the same deterministic UTF-8 length-prefixed encoding family as the manifest.

There is no algorithm negotiation or downgrade path in v1.

Unsupported algorithm => DENY.

### New mandatory adversarial proofs

Future implementation must prove:

- real issuer role direct INSERT on all command-authority tables is denied;
- real issuer role direct INSERT on `command_authority_operation` is denied;
- only narrow attestation-aware capability can create a real authority root;
- principal creation and attestation consumption are atomic;
- same manifest cannot create a second principal under concurrency;
- credential/grant operations cannot cross to a different principal or manifest;
- signer self-claims cannot establish authorization;
- signer-authority fork/stale/revoked lineage denies;
- changed algorithm ID denies;
- changed key ID denies;
- changed key fingerprint denies;
- changed manifest digest denies;
- non-Ed25519 algorithm denies;
- malformed Ed25519 public-key encoding denies;
- malformed/noncanonical signature encoding denies.

### Blocker status

```text
BLOCKER_COUNT = 0

AUTHORITY_BOUNDARY_ATTESTATION_BINDING = FROZEN
SINGLE_USE_ATTESTATION_CONSUMPTION = FROZEN
SIGNER_AUTHORIZATION_SOURCE_CONTRACT = FROZEN
SIGNED_ENVELOPE_V1 = FROZEN
```

Implementation remains blocked by the remaining HIGH/MEDIUM design items.


## High findings closure revision 3

The four HIGH findings are frozen by the following v1 contracts.

### Evidence binding fingerprint v1

Domain:

```text
FLOOOW:S2A:EVIDENCE-BINDING:1
```

Digest:

```text
lowercaseHex(SHA-256(canonicalEvidenceBindingBytes))
```

Ordered fields:

```text
organizationId
marketplaceOrderId
mercadoLivreConnectionId
mlCapability
mlInputProgressVersion
mlRecordOrdinal
marketplaceKey
marketplaceExternalOrderId
mlCurrency
mlPromotionOutcome
omieConnectionId
omieCapability
omieInputProgressVersion
omieRecordOrdinal
omieSourceOrderReference
omieIntegrationReference presence
omieIntegrationReference value
omieCurrency presence
omieCurrency value
omieSemanticFingerprintVersion
omieSemanticFingerprint
omieProviderRevisionLocal
```

The domain is encoded before the fields under the same canonical framing family.

Fixed S2A v1 tokens:

```text
mlCapability = marketplace-economic.order-source
marketplaceKey = mercado-livre
mlPromotionOutcome = PROMOTED | DUPLICATE
omieCapability = marketplace-economic.omie-transaction-evidence.reacquisition-v3
omieSemanticFingerprintVersion = 1
```

Omie NULL currency is encoded as absent and remains neutral. It is never inferred as BRL.

The fingerprint must be rederived only from durable repository evidence. Request-supplied fingerprints or lineage values cannot substitute for repository derivation.

A changed fingerprint means DENY and NEW_APPROVAL_REQUIRED.

Writer currentness remains an independent final gate.

### Signer key lifecycle v1

Signer key lifecycle is an append-only lineage separate from signer authority.

Required logical fields:

```text
organizationId
signerKeyId
revision
signerSubjectId
algorithmId
subjectPublicKeyInfoDer
signerKeyFingerprint
state
validFrom
effectiveAt
supersedesRevision
reason
provenance
correlationId
recordedAt
```

For v1:

```text
algorithmId = Ed25519
state = ACTIVE | RETIRED | REVOKED | COMPROMISED
```

Rules:

- one unambiguous latest leaf;
- forked/missing/unsupported/malformed lineage denies;
- signerKeyId cannot be rebound to different SPKI bytes;
- SPKI fingerprint is recomputed on every verification;
- terminal key state cannot return to ACTIVE;
- rotation creates a new signerKeyId;
- the key holder cannot authorize or mutate its own lifecycle.

Execution-time eligibility:

```text
executionTime = database-server-owned timestamptz(6)

validFrom <= executionTime
AND key state at executionTime = ACTIVE
AND signer-authority lineage is current and valid
AND approvalWindowStart <= executionTime < approvalWindowEnd
AND every existing command-authority and writer gate passes
```

`verifiedAt` does not grandfather future execution.

A manifest signed before retirement/revocation/compromise but executed afterward is denied.

Lifecycle events after committed identity decisions do not rewrite immutable history.

The current key leaf and signer-authority leaf must be serialization-fenced through final execution admission.

### Canonical representation v1

Binary framing:

```text
frame(bytes):
    uint32 big-endian bytes.length
    || bytes

text(value):
    frame(UTF8(value))
```

All records use:

```text
domain-separated
schema-ordered
length-framed
UTF-8
```

No BOM, platform separators, locale formatting, raw JSON signing, or transport-order dependence.

Nullable encoding:

```text
NULL:
text("NULL") || frame(empty)

PRESENT:
text("PRESENT") || text(canonical(value))
```

Canonical Instant:

```text
uuuu-MM-dd'T'HH:mm:ss.SSSSSS'Z'
```

Canonical Omie provider-local civil time:

```text
uuuu-MM-dd'T'HH:mm:ss.SSSSSS
```

The latter must never be timezone-converted.

String validation:

- valid Unicode scalar sequence;
- no unpaired UTF-16 surrogate;
- NFC required;
- non-NFC rejected, not silently normalized;
- no trimming/case folding;
- schema-nonempty fields reject empty;
- reject leading/trailing whitespace;
- reject NUL, C0 control characters, DEL, CR and LF;
- enforce field-specific UTF-8 byte bounds.

UUID:

```text
lowercase canonical UUID
```

Enum:

```text
exact frozen ASCII token
```

Boolean if introduced:

```text
true | false
```

Nonnegative integer if introduced:

```text
base-10
no sign
no leading zero
zero = 0
```

Golden vectors must include exact full canonical byte hex and expected SHA-256.

### Accepted-attestation proof artifact v1

Artifact domain:

```text
FLOOOW:S2A:ACCEPTED-ATTESTATION-PROOF:1
```

Minimum immutable artifact content:

```text
artifactVersion
canonicalManifestBytes
manifestDigest
canonicalSignaturePreimageBytes
algorithmId
signerKeyId
signerKeyFingerprint
subjectPublicKeyInfoDer
signatureBytes
signerKeyLineageRevision
signerKeyLineageFingerprint
signerAuthorityId
signerAuthorityRevision
signerAuthorityRevisionFingerprint
verifiedAt
```

The artifact receives its own domain-separated SHA-256 content fingerprint.

Integrity requirements:

```text
SHA-256(canonicalManifestBytes) = manifestDigest

reconstructed signature preimage
= canonicalSignaturePreimageBytes

SHA-256(subjectPublicKeyInfoDer)
= signerKeyFingerprint

Ed25519.verify(
    subjectPublicKeyInfoDer,
    canonicalSignaturePreimageBytes,
    signatureBytes
) = true
```

The parsed manifest identity must match the accepted-attestation primary identity.

Key-lineage and signer-authority lineage references/fingerprints must resolve to immutable historical revisions.

Any derived index column must equal the value derived from the immutable artifact.

Any mismatch denies.

Failed verification attempts are not accepted attestations.

Private signing keys, raw command credentials, credential tokens, bearer tokens, provider credentials, and secret verifier source material are prohibited.

### Mandatory HIGH adversarial proof matrix

Implementation must prove at minimum:

- every included evidence-binding field mutation changes the digest;
- Omie NULL currency differs from BRL;
- raw provider-only change with equal accepted semantic evidence does not change approval digest;
- newer Omie provider revision changes approval binding;
- same maximum revision with conflicting semantics denies;
- changed evidence after approval denies before credential generation;
- matching approval fingerprint plus writer failure still denies;
- retired/revoked/compromised key cannot authorize new execution;
- historical signature remains cryptographically verifiable after rotation;
- revocation between verification and execution denies;
- lifecycle/execution race follows serialization order;
- backdated compromise does not mutate committed historical decisions;
- offset-equivalent Instants canonicalize identically;
- Omie civil time is never timezone converted;
- noncanonical Unicode/UUID/timestamp/enum inputs deny;
- NULL/empty/present values do not collide;
- field-boundary collision attempts fail;
- retained artifact tampering is detected;
- SPKI/fingerprint disagreement is detected;
- signature tampering denies;
- historical verification works without private key;
- derived index disagreement denies;
- failed verification cannot create accepted evidence;
- accepted evidence cannot itself create command authority.

### High closure status

```text
HIGH_1_EVIDENCE_BINDING = CLOSED_BY_DESIGN
HIGH_2_KEY_LIFECYCLE = CLOSED_BY_DESIGN
HIGH_3_CANONICAL_REPRESENTATION = CLOSED_BY_DESIGN
HIGH_4_RETENTION = CLOSED_BY_DESIGN

BLOCKER_COUNT = 0
HIGH_COUNT = 0
MEDIUM_COUNT = 2
```

Implementation remains HOLD pending closure of the two MEDIUM findings.


## Final design closure revision 4

The final two MEDIUM findings are frozen by the following v1 contracts.

### Governance identifier model v1

Stable organization-scoped UUID primitives:

```text
GovernanceSubjectId
GovernanceInstitutionId
GovernanceSourceId
SignerAuthorityId
SignerKeyId
```

All are canonical lowercase non-nil UUIDs and interpreted with organizationId scope.

Frozen field contract:

```text
accountableOperator: GovernanceSubjectId
signerSubjectId: GovernanceSubjectId
signerRole: S2A_FIELD_PROOF_APPROVER
signerAuthorizingInstitution: GovernanceInstitutionId
signingKeyCustodian: GovernanceSubjectId
revocationOwner: GovernanceSubjectId
credentialCustodian: GovernanceSubjectId
credentialDeliveryMethod: PROTECTED_TTY_ONE_TIME
credentialRotationOwner: GovernanceSubjectId
immediateRevocationPolicy: SEPARATE_APPROVAL_REQUIRED
approvalSource: GovernanceSourceId
signerAuthorityId: UUID
signerKeyId: UUID
```

Descriptive metadata cannot establish identity or authorization.

### Physical PostgreSQL model v1

Frozen conceptual tables:

```text
s2a_signer_key_revision
s2a_signer_authority_revision
s2a_accepted_attestation
s2a_attestation_consumption
```

Signer key lineage is append-only and immutable.
Signer authority lineage is append-only approval-governance authority.
Accepted attestation is immutable evidence.
Consumption is the immutable one-time bridge to one command-principal root.

### command_authority_operation linkage

Additive nullable column:

```text
attestation_manifest_id uuid NULL
```

Composite linkage is organization_id + attestation_manifest_id to s2a_attestation_consumption.

Historical/synthetic rows may remain NULL.

Future real S2A PRINCIPAL, INITIAL_CREDENTIAL, and GRANT operations require a non-null link.

A partial unique rule allows at most one linked operation of each kind per organization + manifest.

The authority-operation intent fingerprint additionally includes manifestId, artifactFingerprint, and manifestDigest.

### Lock order

Accepted attestation:
organization FOR SHARE -> attestation advisory lock -> key root FOR SHARE -> signer-authority root FOR SHARE -> verify -> insert -> commit.

Provisioning:
organization FOR SHARE -> operation-ID advisory lock -> replay check -> principal advisory lock -> principal FOR UPDATE if present -> attestation advisory lock -> accepted attestation -> consumption -> key root -> signer-authority root -> reverify -> append authority mutation/consumption/receipt -> commit.

Final execution admission carries attestation consumption and governance lifecycle fences inside the existing writer transaction through immutable decision commit.

No external provider/network call is permitted inside these transactions.

### Role / privilege contract

Future roles:

```text
flooow_approval_governance
flooow_attestation_verifier
flooow_command_issuer
flooow_command_runtime
```

The future real issuer loses direct authority-table DML.
PUBLIC EXECUTE is revoked from privileged functions.
No generic mutation capability is allowed.

### Migration trust boundaries

```text
Migration A - approval governance
Migration B - accepted attestation evidence
Migration C - command authority linkage + privilege hardening
```

Migration C must atomically revoke the old direct issuer path and install the attestation-aware replacement path.

### Final design closure

```text
BLOCKER_COUNT = 0
HIGH_COUNT = 0
MEDIUM_COUNT = 0
DESIGN_CLOSURE = PASS
```

Implementation remains HOLD pending Revision 4 validation and versioning review.


## Human decisions required
### Revision 4 human-boundary clarification

The following values are technically frozen vocabulary:

- SIGNER_ROLE = S2A_FIELD_PROOF_APPROVER
- CREDENTIAL_DELIVERY_METHOD = PROTECTED_TTY_ONE_TIME
- IMMEDIATE_REVOCATION_POLICY = SEPARATE_APPROVAL_REQUIRED

What remains unresolved is the actual human and institutional assignment and explicit acceptance of the accountable operator, authorized signer, authorizing institution, signing-key custodian, revocation owner, credential custodian, credential rotation owner, approval source, and real-field-proof authorization.

A frozen token does not itself create signer authority, command authority, or permission to execute the real field proof.


```text
ACCOUNTABLE_OPERATOR
AUTHORIZED_SIGNER
SIGNER_ROLE
SIGNER_AUTHORIZING_INSTITUTION
SIGNING_KEY_CUSTODIAN
REVOCATION_OWNER
CREDENTIAL_CUSTODIAN
CREDENTIAL_DELIVERY_METHOD
CREDENTIAL_ROTATION_OWNER
IMMEDIATE_REVOCATION_POLICY
```

No default may be invented.

## Implementation hold

This specification does not authorize:

- migration;
- attestation table;
- signer registry;
- crypto implementation;
- production keys;
- launcher config;
- authority provisioning;
- real field proof.

All remain HOLD pending final document validation, controlled versioning, implementation authorization, deployment-equivalent proofs, explicit human governance assignments, and separate real field-proof authorization.
