# ADR-0088 - S2A signed approval attestation boundary

## Status

FINAL DESIGN CLOSURE - REVISION 4.

No implementation, migration, launcher activation, signer key, real authority, or field execution is authorized by this ADR.

Date: 2026-09-25

## Context

ADR-0087 and SPEC-0087 require a signed, bounded approval manifest before any real S2A field-proof mutation.

The S2A technical ceremony foundation is implemented and proven, but the executable approval-attestation contract remains intentionally unfrozen.

The existing command-authority substrate has distinct semantics:

- `command_principal`, `command_credential_revision`, and `command_permission_grant` represent command authority;
- `command_authority_operation` records issuer effects such as `PRINCIPAL`, `INITIAL_CREDENTIAL`, `ROTATE_CREDENTIAL`, `GRANT`, and `REVOKE`;
- the governed transaction-identity writer remains the authority for immutable identity admission;
- durable provider evidence informs the decision but is not authority.

The next boundary must preserve:

```text
SIGNED MANIFEST != AUTHORITY
SIGNATURE VALID != SIGNER AUTHORIZED
VERIFIED APPROVAL != EXECUTION
AUTHORITY != EXECUTION
EVIDENCE != AUTHORITY
```

## Decision

Introduce a distinct pre-authority approval-attestation boundary for S2A.

The signed approval manifest is evidence of a bounded human approval.

It may be verified before command-authority provisioning, but it cannot itself create:

- a command principal;
- a command credential;
- a permission grant;
- a transaction-identity decision;
- provider activity;
- financial authority;
- Decision Room authority;
- policy authority.

The required sequence is:

```text
human approval
-> signed approval manifest
-> structural validation
-> canonicalization
-> manifest digest
-> cryptographic signature verification
-> signer identity resolution
-> signer authorization verification
-> approval window validation
-> exact target validation
-> durable evidence binding validation
-> replay / collision validation
-> verified approval-attestation evidence
-> read-only ceremony preflight

ONLY THEN:

-> generate credential
-> issue principal bound to the accepted attestation
-> bind credential revision 1 under the same attestation consumption
-> one-time protected TTY delivery
-> grant TRANSACTION_IDENTITY_DECISION_WRITE under the same attestation consumption
-> authenticate in process
-> destroy raw credential material
-> existing governed writer
-> post-proof verification
-> optional separately approved revocation
```

The ADR-0087 ceremony order from credential generation onward remains unchanged.

The writer lock ordering remains unchanged.

## Approval evidence is not command authority

`command_authority_operation` must remain an immutable ledger of command-authority issuer effects.

It must not gain a synthetic `APPROVAL` operation.

Approval evidence must exist before a command principal may exist. Therefore it must not require a `command_principal`, credential, or permission-grant foreign key.

A future implementation may persist separate non-authoritative approval-attestation evidence.

That evidence only proves that a bounded approval artifact was successfully verified.

It does not grant execution permission.

## Mandatory authority-boundary enforcement

Launcher-only enforcement is rejected.

A signed-manifest requirement is not an institutional invariant if a caller holding the issuer capability can bypass the launcher and call authority provisioning without an accepted attestation.

Therefore future real provisioning must fail closed unless the authority-provisioning boundary can prove that the request is bound to an accepted, unconsumed approval attestation for the exact organization, action, permission, target, evidence binding, and approval window.

The exact mechanism remains UNFROZEN, but it must satisfy:

```text
DIRECT ISSUER CALL WITHOUT ACCEPTED ATTESTATION
=> DENY

ATTESTATION / REQUEST SCOPE MISMATCH
=> DENY

ATTESTATION ALREADY CONSUMED FOR ANOTHER AUTHORITY ROOT
=> DENY
```

The existing command-authority tables remain the authority substrate. The attestation remains evidence.

## Canonical manifest intent

The v1 manifest binds human-approved intent, not future authority row identifiers.

Required logical fields:

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

`principalId`, `credentialId`, and `grantId` are excluded.

The only permitted permission is:

```text
TRANSACTION_IDENTITY_DECISION_WRITE
```

`TRANSACTION_IDENTITY_POLICY_ADMIN` remains excluded.

Human and policy-bearing fields must ultimately use stable, unambiguous identifiers or versioned policy references. Free-form labels must not become authorization inputs.

## Evidence binding

The manifest must bind the exact provider-evidence context approved by the human authority through an `evidenceBindingFingerprint`.

The rule is:

```text
approval binds evidence E1
execution observes evidence E2

E1 != E2
=> DENY
=> NEW APPROVAL REQUIRED
```

The exact v1 fingerprint input set remains UNFROZEN and must be frozen with golden vectors before implementation.

The writer remains responsible for authoritative currentness validation.

A matching attestation fingerprint never bypasses writer validation.

## Canonicalization boundary

The signed manifest representation must be deterministic and independent of:

- JSON property order;
- whitespace;
- locale;
- host environment;
- process configuration.

The design direction is a versioned, domain-separated, UTF-8 length-prefixed canonical encoding consistent with existing FLOOOW fingerprint conventions.

Raw JSON bytes are not the cryptographic contract.

Exact timestamp normalization, string normalization rules, and golden vectors remain mandatory before implementation.

## Signed envelope binding

The signature must bind both the canonical manifest digest and security-relevant envelope metadata.

The proposed signature preimage is conceptually:

```text
FLOOOW:S2A:APPROVAL-SIGNATURE:1
algorithmId
signerKeyId
signerKeyFingerprint
manifestDigest
```

Each value must use the same deterministic canonical encoding rules.

`algorithmId`, signer key identity, and key fingerprint must not be unsigned mutable metadata.

Algorithm substitution or downgrade must fail closed.

## Signature boundary

No signature algorithm is frozen by this ADR.

Current design candidates:

```text
Ed25519      = PROPOSED PRIMARY
ECDSA P-256  = PROPOSED COMPATIBILITY
RSA-PSS      = NOT SELECTED FOR INITIAL DESIGN
```

A valid signature proves possession of the corresponding signing key.

It does not prove organizational authorization.

## Signer authorization

Signer authorization is an independent gate.

The verifier must establish:

```text
which key signed
-> which human or institutional role the key represents
-> whether that signer was authorized
   for the exact organization,
   approval action,
   permission,
   and bounded window
```

Manifest fields such as `approvalSource`, `accountableOperator`, or signer labels are descriptive signed claims. They are not a signer-authorization source.

`command_permission_grant` must not be reused as signer authorization because it represents execution authority.

The future signer-authorization source must be independently trusted, versioned, bounded, and revocable.

If no accepted signer-authorization source exists:

```text
DENY
```

even when the cryptographic signature is valid.

## Single-use approval consumption

Manifest replay, issuer replay, and writer replay are independent controls.

`manifestId` identifies one bounded approval ceremony.

An accepted manifest may authorize at most one command-authority root for this field-proof contract.

The expected `PRINCIPAL`, `INITIAL_CREDENTIAL`, and `GRANT` operations may form one controlled consumption lineage under that same attestation, but the manifest must not authorize a second principal root.

Manifest semantics:

```text
new manifestId + valid digest
=> may proceed to verification

same manifestId + same digest + same unfinished/known consumption lineage
=> idempotent recovery only
=> never create a second authority root

same manifestId + same digest + different authority root
=> DENY

same manifestId + different digest
=> INTEGRITY FAILURE
```

The concrete durable consumption model remains UNFROZEN.

Existing `command_authority_operation` idempotency remains unchanged.

Existing writer decision replay remains unchanged.

## Storage and historical re-verification

No raw credential, signing private key, or other secret material may be persisted in approval-attestation evidence.

An accepted attestation must preserve enough nonsecret material to permit later independent cryptographic re-verification of what was approved.

A future evidence record or immutable content-addressed artifact must retain or durably reference:

```text
organizationId
manifestId
schemaVersion
canonicalizationVersion
canonical manifest bytes or a lossless immutable equivalent
manifestDigest
algorithmId
signerKeyId
signerKeyFingerprint
signature
approvalWindowStart
approvalWindowEnd
evidenceBindingFingerprint
correlationId
approvalSource
provenance
verifiedAt
signer-authorization lineage reference
```

The signing private key is never stored.

Existence of an accepted attestation record means verification succeeded. A mutable `verificationStatus` must not turn an accepted attestation into a state machine.

Failed verification attempts may be operationally logged separately, but they are not accepted approval evidence.

The exact storage schema remains UNFROZEN.

## Key lifecycle

Historical verification and execution eligibility are distinct.

A rotated or retired key may remain available for historical verification of prior artifacts.

A key that is revoked or compromised before execution must not authorize a new field-proof execution unless an explicitly frozen policy says otherwise.

The exact activation, retirement, compromise, and revocation temporal semantics remain UNFROZEN and are an implementation blocker.

## Kill rules

REAL_FIELD_PROOF remains HOLD on any:

- missing manifest;
- missing signature;
- malformed manifest;
- unsupported schema;
- unsupported canonicalization;
- invalid signature;
- unsigned or inconsistent security envelope metadata;
- unknown signer key;
- revoked signer key;
- signer not authorized;
- signer authorization lineage unavailable;
- approval expired;
- approval not yet valid;
- organization mismatch;
- Mercado Livre connection mismatch;
- Omie connection mismatch;
- source reference mismatch;
- integration reference mismatch;
- marketplace order mismatch;
- permission mismatch;
- POLICY_ADMIN request;
- evidence binding mismatch;
- manifest ID collision;
- second authority root attempt;
- ambiguous verification;
- inability to preserve independently re-verifiable attestation evidence;
- attestation persistence failure;
- authority provisioning without an accepted attestation binding;
- incomplete launcher configuration;
- missing required human authority value.

Every kill condition must occur before credential generation and before command-authority provisioning.

## Blocker closure revision 2

The four adversarial BLOCKER findings are closed at design-contract level only. No implementation is authorized.

### B1 - authority provisioning enforcement

The real issuer must not rely on launcher discipline.

For the future real-attested path, the issuer database role must have no direct INSERT capability on:

```text
command_principal
command_credential_revision
command_permission_grant
command_authority_operation
```

Real provisioning must occur only through narrow attestation-aware database capabilities owned by the migration/security owner.

Those capabilities must:

```text
verify accepted attestation
verify exact organization and approved target
verify DECISION_WRITE only
verify approval window
verify one authority-root consumption
serialize the attestation consumption
perform the exact authority mutation
append the existing authority-operation receipt
commit atomically
```

They must use fixed semantics, fixed search paths, parameter binding, least privilege, and no general SQL execution.

A direct issuer call or direct SQL authority INSERT without the attestation-aware capability must be denied by database privileges.

The existing authority tables remain the only command-authority substrate.

### B2 - single-use attestation consumption

The durable model is frozen conceptually as two separate immutable records:

```text
accepted attestation evidence
attestation consumption
```

The accepted-attestation identity is:

```text
organizationId + manifestId
```

A future consumption record is keyed by that same identity and binds exactly one:

```text
manifestDigest
principalId
correlationId
consumedAt
```

The consumption record is inserted in the same database transaction that creates the command principal through the attestation-aware authority capability.

Its primary-key uniqueness enforces:

```text
ONE manifestId
=> AT MOST ONE principal root
```

Principal creation plus consumption plus authority-operation receipt is atomic.

Initial credential binding and DECISION_WRITE grant must validate the same consumption record and the same principal.

A same-operation replay may return the existing receipt. It must never create a second principal root.

Credential rotation and later permission revocation are not authorized by the original field-proof manifest and require their own separately accepted authority source.

### B3 - independently trusted signer authorization source

The signer-authorization contract is frozen as a separate approval-governance authority lineage.

It is not command execution authority and does not replace `command_permission_grant`.

A future signer-authority record must be immutable / append-only and bind:

```text
organizationId
signerAuthorityId
revision
signerSubjectId
signerKeyId
signerKeyFingerprint
approvalAction = S2A_FIELD_PROOF_APPROVAL
permission = TRANSACTION_IDENTITY_DECISION_WRITE
validFrom
validUntil
state
supersedesSignerAuthorityId
reason
provenance
correlationId
decidedAt
```

The latest valid lineage controls eligibility.

Missing, revoked, expired, forked, ambiguous, or scope-mismatched signer authority denies approval verification.

The signer may not create or modify its own authority lineage.

Actual signer identities, institutional approvers, key custodians, and initial authority values remain explicit human decisions.

Until at least one explicitly approved signer-authority lineage exists:

```text
REAL_FIELD_PROOF = HOLD
```

### B4 - signed envelope and algorithm contract

The S2A approval-signature v1 algorithm is frozen to:

```text
algorithmId = Ed25519
```

The repository uses JVM toolchain 21, so the v1 design requires the standard JCA Ed25519 implementation and no external crypto provider.

No algorithm negotiation exists in v1.

Any other `algorithmId` is rejected. A future algorithm requires a new signature-contract version.

`signerKeyId` is a canonical UUID.

`signerKeyFingerprint` is:

```text
lowercase-hex(
  SHA-256(
    DER SubjectPublicKeyInfo bytes of the Ed25519 public key
  )
)
```

Signature transport representation is canonical base64url without padding.

The signed preimage is the deterministic length-prefixed UTF-8 canonical record:

```text
domain = FLOOOW:S2A:APPROVAL-SIGNATURE:1
algorithmId = Ed25519
signerKeyId
signerKeyFingerprint
manifestDigest
```

The manifest digest is lowercase hexadecimal SHA-256 of the canonical manifest bytes.

Changing any signed-envelope field invalidates verification.

The signature bytes, public key, key ID, fingerprint, and manifest digest are nonsecret. The private signing key remains secret and is never persisted by FLOOOW approval evidence.

### Blocker closure classification

```text
B1_AUTHORITY_BOUNDARY_ENFORCEMENT = FROZEN
B2_SINGLE_USE_CONSUMPTION = FROZEN
B3_SIGNER_AUTHORIZATION_SOURCE_CONTRACT = FROZEN
B4_SIGNED_ENVELOPE_V1 = FROZEN

BLOCKER = 0
```

Implementation remains HOLD because HIGH and MEDIUM design findings still require closure.


## High findings closure revision 3

The four HIGH findings are closed at design-contract level only. No implementation is authorized.

### H1 - evidence binding fingerprint v1

Frozen domain:

```text
FLOOOW:S2A:EVIDENCE-BINDING:1
```

Frozen digest:

```text
lowercaseHex(SHA-256(canonicalEvidenceBindingBytes))
```

Frozen ordered v1 input set:

```text
1.  domain = FLOOOW:S2A:EVIDENCE-BINDING:1
2.  organizationId
3.  marketplaceOrderId
4.  mercadoLivreConnectionId
5.  mlCapability
6.  mlInputProgressVersion
7.  mlRecordOrdinal
8.  marketplaceKey
9.  marketplaceExternalOrderId
10. mlCurrency
11. mlPromotionOutcome
12. omieConnectionId
13. omieCapability
14. omieInputProgressVersion
15. omieRecordOrdinal
16. omieSourceOrderReference
17. omieIntegrationReference presence
18. omieIntegrationReference value
19. omieCurrency presence
20. omieCurrency value
21. omieSemanticFingerprintVersion
22. omieSemanticFingerprint
23. omieProviderRevisionLocal
```

Frozen values:

```text
mlCapability = marketplace-economic.order-source
marketplaceKey = mercado-livre
mlPromotionOutcome = PROMOTED | DUPLICATE
omieCapability = marketplace-economic.omie-transaction-evidence.reacquisition-v3
omieSemanticFingerprintVersion = 1
omieSemanticFingerprint = lowercase hex SHA-256
```

Target binding, approval evidence-currentness binding, and writer currentness remain distinct.

The approval fingerprint never replaces writer validation.

Omie currency is explicitly nullable:

```text
NULL != EMPTY
NULL != BRL
```

A changed approval-relevant evidence fingerprint at execution means:

```text
DENY
NEW_APPROVAL_REQUIRED
```

Raw Omie provider-payload fingerprint is not part of the approval binding when the accepted V3 semantic evidence and provider revision remain unchanged. The later SPEC-0084 / implemented writer contract governs this boundary.

### H2 - signer key lifecycle v1

Signer key lifecycle is a separate append-only cryptographic lineage.

It is distinct from signer authorization and command execution authority.

Minimum logical key-lineage fields:

```text
organizationId
signerKeyId
revision
signerSubjectId
algorithmId = Ed25519
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

Frozen states:

```text
ACTIVE
RETIRED
REVOKED
COMPROMISED
```

Rules:

```text
ACTIVE
=> historical verification allowed
=> new execution eligible if every other gate passes

RETIRED
=> historical verification allowed
=> new execution denied

REVOKED
=> historical cryptographic verification allowed
=> new execution denied

COMPROMISED
=> signature mathematics may still verify
=> new execution denied
=> historical trust caveat retained
```

Execution eligibility uses database-server-owned time and must recheck the current key lineage, signer-authority lineage, approval window, command authority, and writer currentness before commit.

An accepted but unconsumed attestation is not grandfathered by an earlier verification.

Revocation or compromise after an immutable identity decision commits does not mutate historical truth.

The lifecycle eligibility fence must serialize with execution through the immutable identity-decision commit.

### H3 - canonical representation v1

Frozen primitive family:

```text
UTF-8
ordered schema fields
unsigned uint32 big-endian byte-length framing
domain separation
SHA-256
lowercase hexadecimal digests
```

Canonical frame:

```text
frame(bytes) = uint32_big_endian(bytes.length) || bytes
text(value) = frame(UTF8(value))
```

Required nullable encoding:

```text
absent:
text("NULL") || frame(empty)

present:
text("PRESENT") || text(canonical(value))
```

Canonical Instant:

```text
uuuu-MM-dd'T'HH:mm:ss.SSSSSS'Z'
```

Rules:

- UTC only;
- exactly six fractional digits;
- microsecond precision;
- no locale;
- no leap-second syntax;
- equivalent offsets canonicalize to the same UTC Instant;
- approval and lifecycle windows are half-open.

Omie provider revision remains a distinct timezone-free civil-time primitive:

```text
uuuu-MM-dd'T'HH:mm:ss.SSSSSS
```

String rules:

- valid Unicode scalar sequences only;
- reject unpaired surrogates;
- require NFC and reject non-NFC rather than silently normalize;
- encode accepted text exactly;
- no trimming or case folding;
- reject leading/trailing whitespace;
- reject NUL, C0 controls, DEL, CR, and LF where free-form text is allowed;
- field-specific byte bounds are required.

UUIDs use lowercase canonical UUID text.

Enums use exact frozen case-sensitive ASCII tokens.

Unknown, duplicate, missing, or unsupported canonical fields/versions deny.

Golden vectors must commit exact canonical byte hex and expected SHA-256.

### H4 - independently re-verifiable accepted attestation retention

Frozen model:

```text
one immutable canonical accepted-attestation proof artifact
+ derived non-authoritative index columns
+ separate immutable attestation consumption
```

Minimum durable proof artifact:

```text
artifactDomain = FLOOOW:S2A:ACCEPTED-ATTESTATION-PROOF:1
artifactVersion
canonicalManifestBytes
manifestDigest
canonicalSignaturePreimageBytes
algorithmId = Ed25519
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

The canonical manifest already carries the approved organization, manifest ID, approval window, exact target, evidence binding, permission, correlation, provenance, and human/custody declarations. Those facts must not be duplicated as a second authoritative representation.

Derived index columns are lookup metadata only and must be verified against the immutable artifact.

Every audit or execution read must:

```text
verify artifact fingerprint
parse supported artifact version
recompute manifest digest
reconstruct signed preimage
recompute SPKI fingerprint
verify Ed25519 signature
validate immutable key-lineage reference
validate immutable signer-authority reference
compare derived indexes with artifact facts
fail closed on any mismatch
```

Historical SPKI DER bytes must be retained. Historical private signing keys are never retained.

Failed verification attempts do not belong in the accepted-attestation evidence store.

Accepted attestation, attestation consumption, and command authority remain separate concepts.

### High closure classification

```text
HIGH_1_EVIDENCE_BINDING = CLOSED_BY_DESIGN
HIGH_2_KEY_LIFECYCLE = CLOSED_BY_DESIGN
HIGH_3_CANONICAL_REPRESENTATION = CLOSED_BY_DESIGN
HIGH_4_RETENTION = CLOSED_BY_DESIGN

BLOCKER = 0
HIGH = 0
MEDIUM = 2
```

The remaining MEDIUM findings are:

```text
MEDIUM_1 = stable human/policy identifier representation
MEDIUM_2 = concrete migration/index/locking and attestation-to-receipt linkage
```

Implementation remains HOLD.


## Final design closure revision 4

The final two MEDIUM findings are closed at design-contract level.

### M1 - stable governance identifiers v1

Stable machine identifiers are organization-scoped canonical lowercase non-nil UUIDs:

```text
GovernanceSubjectId
GovernanceInstitutionId
GovernanceSourceId
SignerAuthorityId
SignerKeyId
```

Identity is always organizationId + identifier.

No display name, email address, username, ticket label, reason, provenance, correlation, or external reference may substitute for stable authority identity.

Frozen tokens:

```text
SIGNER_ROLE = S2A_FIELD_PROOF_APPROVER
CREDENTIAL_DELIVERY_METHOD = PROTECTED_TTY_ONE_TIME
IMMEDIATE_REVOCATION_POLICY = SEPARATE_APPROVAL_REQUIRED
```

Descriptive labels remain non-authoritative metadata only.

### M2 - physical persistence and authority linkage v1

Frozen conceptual tables:

```text
s2a_signer_key_revision
s2a_signer_authority_revision
s2a_accepted_attestation
s2a_attestation_consumption
```

Accepted attestation remains evidence.
Consumption remains the one-time bridge.
Command authority remains the existing authority substrate.

Selected authority linkage:

```text
command_authority_operation.attestation_manifest_id uuid NULL
```

No APPROVAL operation is introduced.

Future real S2A PRINCIPAL, INITIAL_CREDENTIAL, and GRANT operations must carry the same non-null attestation link.

Linked GRANT is restricted to TRANSACTION_IDENTITY_DECISION_WRITE.

The issuer intent fingerprint additionally binds manifestId, accepted artifact fingerprint, and manifest digest.

### Locking contract

Accepted-attestation verification serializes on organization, manifest, signer-key lineage root, and signer-authority lineage root before insert and commit.

Attestation-aware provisioning preserves the existing operation-ID-before-principal ordering and adds the manifest serialization fence before consumption and eligibility validation.

Final execution admission resolves consumption and holds signer-key and signer-authority lifecycle fences through immutable identity-decision commit.

No provider/network call is permitted while authority or lifecycle locks are held.

### Role separation

Future trust roles:

```text
flooow_approval_governance
flooow_attestation_verifier
flooow_command_issuer
flooow_command_runtime
```

The future real issuer loses direct authority-table DML and uses only narrow attestation-aware capabilities.

All privileged functions require least privilege, fixed safe search path, schema-qualified SQL, parameter binding, PUBLIC EXECUTE revoked, and exact single-purpose semantics.

### Migration boundary

Do not assign migration numbers yet.

Freeze three ordered trust boundaries:

```text
1. approval governance
2. accepted attestation evidence
3. authority linkage and issuer privilege hardening
```

The third migration must atomically install linkage constraints, revoke direct issuer DML, and install replacement attestation-aware capabilities.

### Final design classification

```text
BLOCKER = 0
HIGH = 0
MEDIUM = 0
DESIGN_CLOSURE = PASS
```

No implementation, migration, production key, human authority value, or real field proof is authorized.


## Human boundary
### Revision 4 human-boundary clarification

The following values are technically frozen vocabulary:

- SIGNER_ROLE = S2A_FIELD_PROOF_APPROVER
- CREDENTIAL_DELIVERY_METHOD = PROTECTED_TTY_ONE_TIME
- IMMEDIATE_REVOCATION_POLICY = SEPARATE_APPROVAL_REQUIRED

What remains unresolved is the actual human and institutional assignment and explicit acceptance of the accountable operator, authorized signer, authorizing institution, signing-key custodian, revocation owner, credential custodian, credential rotation owner, approval source, and real-field-proof authorization.

A frozen token does not itself create signer authority, command authority, or permission to execute the real field proof.


This ADR does not select or infer:

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

Those are explicit human or institutional decisions.

## Consequences

Approval becomes independently auditable without contaminating the existing command-authority ledger.

The real issuer cannot rely solely on launcher discipline; accepted attestation binding must be enforceable at the provisioning boundary.

No implementation or migration is authorized by this ADR.

## Rejected alternatives

- add `APPROVAL` to `command_authority_operation`;
- treat a valid signed blob as command authority;
- enforce approval only in the launcher;
- leave algorithm/key metadata outside the signed preimage;
- allow one manifest to create multiple principal roots;
- retain only a verification boolean without enough material for later cryptographic re-verification;
- place future principal, credential, or grant IDs inside the human approval;
- reuse `command_permission_grant` as signer authorization;
- automatically accept changed provider evidence under an old approval.


## Implementation contract completion revision 5

Revision 4 remains the architectural decision. Revision 5 is a bounded implementation-contract addendum discovered during the V040 blueprint review. It changes no B1-B4, HIGH 1-HIGH 4, MEDIUM 1-MEDIUM 2, authority boundary, migration boundary, or real-field-proof hold.

### Signer-authority revision identity

`SignerAuthorityId` identifies one immutable organization-scoped signer-authority revision row. It is not a stable lineage-root identifier. Every successor receives a new `signerAuthorityId` and names its predecessor through `supersedesSignerAuthorityId`.

The physical signer-authority lineage therefore uses:

```text
PRIMARY KEY (organizationId, signerAuthorityId)
UNIQUE scoped revision per organization + subject + key + action + permission
UNIQUE non-null predecessor
FOREIGN KEY to the exact predecessor authority row
FOREIGN KEY to the exact signer-key revision and fingerprint
```

The current authority leaf is the unique row for which no same-organization successor references its `signerAuthorityId`. Eligibility is derived from that immutable leaf. No mutable current-authority table is introduced.

Frozen signer-authority state tokens are `ENABLED` and `DISABLED`. Revision 5 introduces no additional transition policy.

### Lineage fingerprint chaining

V040 key and signer-authority revisions carry domain-separated SHA-256 fingerprints over the frozen Revision 3 canonical codec.

```text
key domain:
FLOOOW:S2A:SIGNER-KEY-LINEAGE:1

authority domain:
FLOOOW:S2A:SIGNER-AUTHORITY-LINEAGE:1
```

For a successor, the signed semantic preimage includes both the predecessor identifier/revision reference and the exact predecessor fingerprint. Referential lineage is enforced by row identity and foreign keys; semantic cryptographic lineage is enforced by the predecessor fingerprint.

The fingerprints are integrity evidence. They do not create signer authority, command authority, or execution eligibility.

Reason, provenance, correlation, and database recording/decision timestamps remain audit/trace metadata and are excluded from both lineage fingerprints.

### Governance lock identity

Key mutation serializes on:

```text
s2a-governance/signer-key/1:<organizationId>:<signerKeyId>
```

Signer-authority mutation cannot lock on per-revision `signerAuthorityId`. It serializes on:

```text
s2a-governance/signer-authority-scope/1:
<organizationId>:
<signerSubjectId>:
<signerKeyId>:
<S2A_FIELD_PROOF_APPROVAL>:
<TRANSACTION_IDENTITY_DECISION_WRITE>
```

The mutation order is organization row `FOR SHARE`, signer-key advisory lock, signer-authority-scope advisory lock, current key leaf, current authority leaf, validation, append, commit. No provider or network work is permitted inside the transaction.

### Migration boundary preservation

```text
V040 = approval governance
V041 = accepted immutable attestation evidence + attestation verifier
V042 = consumption + command-authority linkage + issuer hardening + execution eligibility
```

Consumption remains the one-time bridge into a command-principal root and stays in V042 with atomic principal creation. No command-authority effect moves into V041.

```text
REVISION_5_IMPLEMENTATION_CONTRACT_COMPLETION = PASS
ARCHITECTURAL_DECISION_CHANGED = NO
IMPLEMENTATION = HOLD
MIGRATION = HOLD
REAL_FIELD_PROOF = HOLD
```
