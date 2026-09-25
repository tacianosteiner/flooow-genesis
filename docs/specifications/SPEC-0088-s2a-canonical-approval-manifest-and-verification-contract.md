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


## Implementation contract completion revision 5

Revision 5 completes two implementation contracts found incomplete during V040 blueprint review. Revision 4 architecture and all earlier closure classifications remain unchanged.

### V040 physical signer-key contract

`s2a_signer_key_revision` has exactly these columns:

```text
organization_id uuid NOT NULL
signer_key_id uuid NOT NULL
revision integer NOT NULL
signer_subject_id uuid NOT NULL
algorithm_id text NOT NULL
subject_public_key_info_der bytea NOT NULL
signer_key_fingerprint char(64) NOT NULL
state text NOT NULL
valid_from timestamptz(6) NOT NULL
effective_at timestamptz(6) NOT NULL
supersedes_revision integer NULL
lineage_fingerprint char(64) NOT NULL
reason text NOT NULL
provenance text NOT NULL
correlation_id uuid NOT NULL
recorded_at timestamptz(6) NOT NULL server-owned
```

Required constraints:

```text
PRIMARY KEY (organization_id, signer_key_id, revision)

FOREIGN KEY (organization_id)
REFERENCES integration_organization(organization_id)

FOREIGN KEY (organization_id, signer_key_id, supersedes_revision)
REFERENCES s2a_signer_key_revision(
    organization_id,
    signer_key_id,
    revision
)

UNIQUE (organization_id, signer_key_id, supersedes_revision)

UNIQUE (
    organization_id,
    signer_key_id,
    revision,
    signer_key_fingerprint
)

CHECK (revision > 0)
CHECK (algorithm_id = 'Ed25519')
CHECK (state IN ('ACTIVE', 'RETIRED', 'REVOKED', 'COMPROMISED'))
CHECK (signer_key_fingerprint ~ '^[0-9a-f]{64}$')
CHECK (lineage_fingerprint ~ '^[0-9a-f]{64}$')
```

The nullable UNIQUE permits multiple first rows across different key IDs while allowing only one successor for any non-null predecessor revision.

```text
revision > 0

revision = 1
=> supersedes_revision IS NULL

revision > 1
=> supersedes_revision = revision - 1

algorithm_id = Ed25519
state = ACTIVE | RETIRED | REVOKED | COMPROMISED
signer_key_fingerprint = lowercaseHex(SHA-256(subject_public_key_info_der))
lineage_fingerprint = lowercase hexadecimal SHA-256
```

Across a successor, organization, key ID, signer subject, algorithm, SPKI DER, key fingerprint, and `valid_from` remain unchanged. A non-ACTIVE current leaf must never transition back to ACTIVE. No complete terminal-to-terminal transition graph is frozen. A future `effective_at` is not denied merely because it is future.

UPDATE and DELETE are forbidden. The current leaf is the unique row with no same-organization/key successor whose `supersedes_revision` equals its revision.

### V040 physical signer-authority contract

`SignerAuthorityId` is an organization-scoped canonical non-nil UUID identifying one immutable revision row. It is not a stable lineage root. Every successor receives a new ID.

`s2a_signer_authority_revision` has exactly these columns:

```text
organization_id uuid NOT NULL
signer_authority_id uuid NOT NULL
revision integer NOT NULL
signer_subject_id uuid NOT NULL
signer_authorizing_institution_id uuid NOT NULL
signer_role text NOT NULL
signer_key_id uuid NOT NULL
signer_key_revision integer NOT NULL
signer_key_fingerprint char(64) NOT NULL
approval_action text NOT NULL
permission text NOT NULL
valid_from timestamptz(6) NOT NULL
valid_until timestamptz(6) NOT NULL
state text NOT NULL
supersedes_signer_authority_id uuid NULL
signer_authority_fingerprint char(64) NOT NULL
reason text NOT NULL
provenance text NOT NULL
approval_source_id uuid NOT NULL
correlation_id uuid NOT NULL
decided_at timestamptz(6) NOT NULL server-owned
```

Required constraints:

```text
PRIMARY KEY (
    organization_id,
    signer_authority_id
)

UNIQUE (
    organization_id,
    signer_subject_id,
    signer_key_id,
    approval_action,
    permission,
    revision
)

UNIQUE (
    organization_id,
    supersedes_signer_authority_id
)

FOREIGN KEY (
    organization_id,
    supersedes_signer_authority_id
)
REFERENCES s2a_signer_authority_revision(
    organization_id,
    signer_authority_id
)

FOREIGN KEY (
    organization_id,
    signer_key_id,
    signer_key_revision,
    signer_key_fingerprint
)
REFERENCES s2a_signer_key_revision(
    organization_id,
    signer_key_id,
    revision,
    signer_key_fingerprint
)

CHECK (
    (revision = 1 AND supersedes_signer_authority_id IS NULL)
    OR
    (revision > 1 AND supersedes_signer_authority_id IS NOT NULL)
)

CHECK (signer_authority_id <> '00000000-0000-0000-0000-000000000000'::uuid)
CHECK (revision > 0)
CHECK (signer_role = 'S2A_FIELD_PROOF_APPROVER')
CHECK (approval_action = 'S2A_FIELD_PROOF_APPROVAL')
CHECK (permission = 'TRANSACTION_IDENTITY_DECISION_WRITE')
CHECK (state IN ('ENABLED', 'DISABLED'))
CHECK (valid_from < valid_until)
CHECK (signer_key_fingerprint ~ '^[0-9a-f]{64}$')
CHECK (signer_authority_fingerprint ~ '^[0-9a-f]{64}$')
```

The signer-key table must expose the referenced four-column UNIQUE key in addition to its primary key.

Frozen values:

```text
signer_role = S2A_FIELD_PROOF_APPROVER
approval_action = S2A_FIELD_PROOF_APPROVAL
permission = TRANSACTION_IDENTITY_DECISION_WRITE
state = ENABLED | DISABLED
valid_from < valid_until
signer_authority_fingerprint = lowercase hexadecimal SHA-256
```

Successor rules:

- revision 1 has no predecessor;
- revision greater than 1 requires a predecessor;
- revision equals predecessor revision plus one;
- predecessor is the unique unsuperseded leaf for the exact organization/subject/key/action/permission scope;
- successor `signer_authority_id` differs from every prior revision ID;
- organization, subject, authorizing institution, signer role, key ID, key revision, key fingerprint, action, permission, validity window, and approval source remain unchanged within a lineage;
- one non-null predecessor may have only one successor;
- UPDATE and DELETE are forbidden;
- no permanent one-root-forever constraint exists;
- no additional ENABLED/DISABLED transition graph is frozen.

A row is current when no same-organization row references its `signer_authority_id` through `supersedes_signer_authority_id`. Eligibility is derived from the unique current leaf:

```text
state = ENABLED
valid_from <= executionTime
executionTime < valid_until
current signer-key lineage independently eligible
```

There is no mutable current-authority table.

### Canonical lineage-fingerprint codec

Both V040 fingerprints use the Revision 3 codec:

```text
frame(bytes) = uint32_big_endian(bytes.length) || bytes
text(value) = frame(UTF8(value))

record = text(domain) || each field encoding in specified order

UUID = text(lowercase canonical UUID)
integer = text(canonical unsigned decimal)
enum = text(exact frozen ASCII token)
Instant = text(uuuu-MM-dd'T'HH:mm:ss.SSSSSS'Z')
byte array = frame(raw bytes)

nullable absent = text("NULL") || frame(empty)
nullable present text/integer = text("PRESENT") || canonical value encoding
```

Text must already be valid UTF-8 and NFC. Reject non-NFC, leading/trailing whitespace, prohibited controls, invalid bounds, or malformed values. Never normalize, trim, case-fold, repair, or transform accepted text.

### Signer-key lineage fingerprint v1

```text
domain = FLOOOW:S2A:SIGNER-KEY-LINEAGE:1
algorithm = SHA-256(canonical bytes) -> lowercase hexadecimal
```

Ordered fields after the domain:

```text
1. organizationId
2. signerKeyId
3. revision
4. signerSubjectId
5. algorithmId
6. subjectPublicKeyInfoDer
7. signerKeyFingerprint
8. state
9. validFrom
10. effectiveAt
11. supersedesRevision
12. predecessorLineageFingerprint
```

Revision 1 encodes both nullable fields as absent. A later revision encodes the exact previous revision and exact predecessor `lineage_fingerprint` as present.

Excluded:

```text
reason
provenance
correlationId
recordedAt
```

Kotlin computes the fingerprint before append. The database independently recomputes and validates it from the submitted semantic values and the locked predecessor row. The stored fingerprint is never trusted without recomputation.

### Signer-authority fingerprint v1

```text
domain = FLOOOW:S2A:SIGNER-AUTHORITY-LINEAGE:1
algorithm = SHA-256(canonical bytes) -> lowercase hexadecimal
```

Ordered fields after the domain:

```text
1. organizationId
2. signerAuthorityId
3. revision
4. signerSubjectId
5. signerAuthorizingInstitutionId
6. signerRole
7. signerKeyId
8. signerKeyRevision
9. signerKeyFingerprint
10. approvalAction
11. permission
12. validFrom
13. validUntil
14. state
15. approvalSourceId
16. supersedesSignerAuthorityId
17. predecessorSignerAuthorityFingerprint
```

Revision 1 encodes both nullable fields as absent. A later revision encodes the exact predecessor row ID and predecessor `signer_authority_fingerprint` as present.

Excluded:

```text
reason
provenance
correlationId
decidedAt
```

Kotlin and database validation responsibilities match the key-lineage contract.

The predecessor fingerprint cryptographically binds a successor to the exact semantic contents of its predecessor. Row identity and FK provide referential lineage. The predecessor fingerprint provides semantic cryptographic lineage. Neither fingerprint is authority.

### Golden vectors v1

All UUID and Instant values below are their canonical text encodings. The fixed Ed25519 SPKI uses the RFC 8032 test-vector public key.

```text
organizationId = 11111111-1111-4111-8111-111111111111
signerKeyId = 22222222-2222-4222-8222-222222222222
signerSubjectId = 33333333-3333-4333-8333-333333333333
signerAuthorityId revision 1 = 44444444-4444-4444-8444-444444444441
signerAuthorityId revision 2 = 44444444-4444-4444-8444-444444444442
signerAuthorizingInstitutionId = 55555555-5555-4555-8555-555555555555
approvalSourceId = 66666666-6666-4666-8666-666666666666
algorithmId = Ed25519
subjectPublicKeyInfoDer = 302a300506032b6570032100d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a
signerKeyFingerprint = 06e3fd8fda29bb60ab59557de61edb0aecdb231134be30e75b455f8e1b792fa9
validFrom = 2026-09-25T12:00:00.000000Z
validUntil = 2026-10-25T12:00:00.000000Z
```

Each revision block below overrides only the fields it names. Every other field retains the exact common value above and, for a successor, the exact value from its stated revision 1 predecessor. No implicit default participates in a preimage.

Signer-key revision 1:

```text
revision = 1
state = ACTIVE
effectiveAt = 2026-09-25T12:00:00.000000Z
supersedesRevision = NULL
predecessorLineageFingerprint = NULL
byteCount = 383
canonicalPreimageHex = 0000001f464c4f4f4f573a5332413a5349474e45522d4b45592d4c494e454147453a310000002431313131313131312d313131312d343131312d383131312d3131313131313131313131310000002432323232323232322d323232322d343232322d383232322d32323232323232323232323200000001310000002433333333333333332d333333332d343333332d383333332d33333333333333333333333300000007456432353531390000002c302a300506032b6570032100d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a0000004030366533666438666461323962623630616235393535376465363165646230616563646232333131333462653330653735623435356638653162373932666139000000064143544956450000001b323032362d30392d32355431323a30303a30302e3030303030305a0000001b323032362d30392d32355431323a30303a30302e3030303030305a000000044e554c4c00000000000000044e554c4c00000000
expectedSha256 = 9e83dedfa91c44e001cbf4dbbe729436942ca5b6a568865eff3641e45651de65
```

Signer-key revision 2:

```text
revision = 2
state = RETIRED
effectiveAt = 2026-10-01T12:00:00.000000Z
supersedesRevision = PRESENT 1
predecessorLineageFingerprint = PRESENT 9e83dedfa91c44e001cbf4dbbe729436942ca5b6a568865eff3641e45651de65
byteCount = 455
canonicalPreimageHex = 0000001f464c4f4f4f573a5332413a5349474e45522d4b45592d4c494e454147453a310000002431313131313131312d313131312d343131312d383131312d3131313131313131313131310000002432323232323232322d323232322d343232322d383232322d32323232323232323232323200000001320000002433333333333333332d333333332d343333332d383333332d33333333333333333333333300000007456432353531390000002c302a300506032b6570032100d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a000000403036653366643866646132396262363061623539353537646536316564623061656364623233313133346265333065373562343535663865316237393266613900000007524554495245440000001b323032362d30392d32355431323a30303a30302e3030303030305a0000001b323032362d31302d30315431323a30303a30302e3030303030305a0000000750524553454e5400000001310000000750524553454e540000004039653833646564666139316334346530303163626634646262653732393433363934326361356236613536383836356566663336343165343536353164653635
expectedSha256 = 7910bae04e816d4f94cd2086c7963d66d104eb2e33d9795fa14e4f0ca47e21e4
```

Signer-authority revision 1:

```text
revision = 1
signerRole = S2A_FIELD_PROOF_APPROVER
signerKeyRevision = 1
approvalAction = S2A_FIELD_PROOF_APPROVAL
permission = TRANSACTION_IDENTITY_DECISION_WRITE
state = ENABLED
supersedesSignerAuthorityId = NULL
predecessorSignerAuthorityFingerprint = NULL
byteCount = 551
canonicalPreimageHex = 00000025464c4f4f4f573a5332413a5349474e45522d415554484f524954592d4c494e454147453a310000002431313131313131312d313131312d343131312d383131312d3131313131313131313131310000002434343434343434342d343434342d343434342d383434342d34343434343434343434343100000001310000002433333333333333332d333333332d343333332d383333332d3333333333333333333333330000002435353535353535352d353535352d343535352d383535352d353535353535353535353535000000185332415f4649454c445f50524f4f465f415050524f5645520000002432323232323232322d323232322d343232322d383232322d32323232323232323232323200000001310000004030366533666438666461323962623630616235393535376465363165646230616563646232333131333462653330653735623435356638653162373932666139000000185332415f4649454c445f50524f4f465f415050524f56414c000000235452414e53414354494f4e5f4944454e544954595f4445434953494f4e5f57524954450000001b323032362d30392d32355431323a30303a30302e3030303030305a0000001b323032362d31302d32355431323a30303a30302e3030303030305a00000007454e41424c45440000002436363636363636362d363636362d343636362d383636362d363636363636363636363636000000044e554c4c00000000000000044e554c4c00000000
expectedSha256 = 983e222e3e8d9692261db6613c3f0767947c32399493c3ae7de1824aa6371254
```

Signer-authority revision 2:

```text
signerAuthorityId = 44444444-4444-4444-8444-444444444442
revision = 2
state = DISABLED
supersedesSignerAuthorityId = PRESENT 44444444-4444-4444-8444-444444444441
predecessorSignerAuthorityFingerprint = PRESENT 983e222e3e8d9692261db6613c3f0767947c32399493c3ae7de1824aa6371254
byteCount = 658
canonicalPreimageHex = 00000025464c4f4f4f573a5332413a5349474e45522d415554484f524954592d4c494e454147453a310000002431313131313131312d313131312d343131312d383131312d3131313131313131313131310000002434343434343434342d343434342d343434342d383434342d34343434343434343434343200000001320000002433333333333333332d333333332d343333332d383333332d3333333333333333333333330000002435353535353535352d353535352d343535352d383535352d353535353535353535353535000000185332415f4649454c445f50524f4f465f415050524f5645520000002432323232323232322d323232322d343232322d383232322d32323232323232323232323200000001310000004030366533666438666461323962623630616235393535376465363165646230616563646232333131333462653330653735623435356638653162373932666139000000185332415f4649454c445f50524f4f465f415050524f56414c000000235452414e53414354494f4e5f4944454e544954595f4445434953494f4e5f57524954450000001b323032362d30392d32355431323a30303a30302e3030303030305a0000001b323032362d31302d32355431323a30303a30302e3030303030305a0000000844495341424c45440000002436363636363636362d363636362d343636362d383636362d3636363636363636363636360000000750524553454e540000002434343434343434342d343434342d343434342d383434342d3434343434343434343434310000000750524553454e540000004039383365323232653365386439363932323631646236363133633366303736373934376333323339393439336333616537646531383234616136333731323534
expectedSha256 = 04cb49bc072d0d5466a767f5bc0424e1e3f7fcd6ae486bd3b6bf4f45328452a6
```

Mandatory mutation checks:

```text
KEY_R1 state ACTIVE -> RETIRED
= d46f26319b9291fe173f9d71767f59a7b04bb455782e037b21e59fc03247a0c9
!= KEY_R1 expectedSha256

KEY_R2 predecessor fingerprint -> 64 lowercase zeroes
= 7cec3b60b5aff97c7056ec2e0261d979681900133c76edea4a059bfed3bb6858
!= KEY_R2 expectedSha256

AUTH_R1 state ENABLED -> DISABLED
= ecf57994085f857f6eb419d397244d3acc6695656cd03388edf1d3cecb2ed95b
!= AUTH_R1 expectedSha256

AUTH_R2 predecessor fingerprint -> 64 lowercase zeroes
= d9aefc960283cac9c386af0a0af728e29e1991d424c0e9fc423562d6032e01d2
!= AUTH_R2 expectedSha256
```

Changing only excluded reason, provenance, correlation, or server-owned record/decision time must reproduce the corresponding unchanged expected SHA-256 above because those values are absent from the canonical preimage.

Executable excluded-metadata checks use these fixed values:

```text
KEY_R1 metadata mutation:
reason = Lifecycle review
provenance = golden-vector-v1-metadata-mutation
correlationId = 77777777-7777-4777-8777-777777777777
recordedAt = 2026-09-25T12:00:01.000000Z
expectedSha256 = 9e83dedfa91c44e001cbf4dbbe729436942ca5b6a568865eff3641e45651de65

AUTHORITY_R1 metadata mutation:
reason = Governance review
provenance = golden-vector-v1-metadata-mutation
correlationId = 88888888-8888-4888-8888-888888888888
decidedAt = 2026-09-25T12:00:01.000000Z
expectedSha256 = 983e222e3e8d9692261db6613c3f0767947c32399493c3ae7de1824aa6371254
```

The metadata-mutation inputs never enter the canonical encoder. Recomputing each corresponding preimage therefore yields byte-for-byte equality with its revision 1 preimage and the stated unchanged digest.

### V040 locking contract

```text
key lock:
s2a-governance/signer-key/1:<organizationId>:<signerKeyId>

authority scope lock:
s2a-governance/signer-authority-scope/1:<organizationId>:<signerSubjectId>:<signerKeyId>:<S2A_FIELD_PROOF_APPROVAL>:<TRANSACTION_IDENTITY_DECISION_WRITE>
```

Authority mutation order:

```text
organization row FOR SHARE
-> signer-key advisory lock
-> signer-authority-scope advisory lock
-> current key leaf
-> current authority leaf
-> predecessor/revision/fingerprint validation
-> append
-> commit
```

No provider/network operation is permitted in the transaction.

### Trust-boundary preservation

```text
V040 = approval governance
V041 = s2a_accepted_attestation + immutable proof evidence + flooow_attestation_verifier
V042 = s2a_attestation_consumption + authority linkage + attestation-aware principal creation + issuer hardening + execution eligibility
```

V041 retains and independently reverifies:

```text
signerKeyId
signerKeyRevision
signerKeyFingerprint
signerKeyLineageFingerprint
signerAuthorityId
signerAuthorityRevision
signerAuthorityFingerprint
```

V041 and V042 must retain the exact historical revisions while re-resolving current key and authority eligibility under the same locks. Command-authority effects remain in V042.

### Revision 5 implementation kill rules

Implementation denies or stops on any:

- stable-root reinterpretation of `SignerAuthorityId`;
- authority successor reusing a prior authority ID;
- revision gap, fork, stale predecessor, or ambiguous leaf;
- missing or mismatched predecessor fingerprint;
- fingerprint mismatch between Kotlin, database recomputation, stored value, or golden vector;
- renamed frozen physical field;
- silent text normalization, trimming, case-folding, or repair;
- noncanonical UUID, integer, enum, Instant, nullable value, or byte framing;
- signer-authority token outside `ENABLED | DISABLED`;
- key token outside `ACTIVE | RETIRED | REVOKED | COMPROMISED`;
- non-ACTIVE key transition back to ACTIVE;
- new permanent authority-root uniqueness;
- provider/network activity while governance locks are held;
- accepted-attestation, consumption, command-authority, issuer-hardening, or writer scope entering V040.

```text
REVISION_5_IMPLEMENTATION_CONTRACT_COMPLETION = PASS
BLOCKER_1_VERSIONED_PHYSICAL_AUTHORITY_CONTRACT = CLOSED
BLOCKER_2_LINEAGE_FINGERPRINT_PREIMAGES = CLOSED
BLOCKER = 0
HIGH = 0
MEDIUM = 0
IMPLEMENTATION = HOLD
MIGRATION = HOLD
REAL_FIELD_PROOF = HOLD
```
