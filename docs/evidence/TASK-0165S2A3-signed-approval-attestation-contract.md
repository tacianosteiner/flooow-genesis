# TASK-0165S2A3 - Signed approval attestation design evidence

## Status

FINAL DESIGN CLOSURE COMPLETE - REVISION 4.

IMPLEMENTATION HOLD.

REAL FIELD PROOF HOLD.

## Source state

The S2A technical ceremony foundation is versioned at:

```text
0575e128a4e7d212ec1bca052e39179179f690b4
```

The initial ADR-0088 / SPEC-0088 design package was created locally with no implementation, staging, commit, push, migration, runtime mutation, provider call, or real authority.

## Audited boundaries

The adversarial design audit reconciled:

- ADR-0083 / SPEC-0083;
- ADR-0086 / SPEC-0086;
- ADR-0087 / SPEC-0087;
- V037 `command_authority_operation`;
- `ControlledCommandAuthorityIssuer`;
- `PostgresControlledCommandAuthorityIssuer`;
- initial ADR-0088 / SPEC-0088 draft.

## Existing authority semantics

The existing model establishes:

```text
credential possession != human intent
authentication != authorization
evidence != authority
command principal/grant = execution authority substrate
command_authority_operation = issuer-effect receipt
writer = transaction-identity decision boundary
```

Current `command_authority_operation` kinds remain:

```text
PRINCIPAL
INITIAL_CREDENTIAL
ROTATE_CREDENTIAL
GRANT
REVOKE
```

## Proven provenance-fit result

`command_authority_operation` is NOT a fit for pre-authority approval evidence.

Classification remains:

```text
COMMAND_AUTHORITY_OPERATION_PROVENANCE_FIT=REJECTED
AUTHORITY_LEDGER_CHANGE_REQUIRED=NO
SEPARATE_NON_AUTHORITATIVE_ATTESTATION_EVIDENCE=REQUIRED
```

## Adversarial finding A — launcher-only approval is bypassable

BLOCKER.

If the signed-manifest check exists only in `execute-field-proof`, a caller possessing the offline issuer capability could call `ControlledCommandAuthorityIssuer` directly and bypass the approval contract.

Therefore:

```text
LAUNCHER_VERIFICATION_ONLY=REJECTED
AUTHORITY_BOUNDARY_ATTESTATION_BINDING=REQUIRED
```

Future real provisioning must deny authority issuance without an accepted attestation bound to the exact organization, target, permission, evidence context, and consumption lineage.

The exact enforcement mechanism remains UNFROZEN.

## Adversarial finding B — manifest must be single-use for authority root

BLOCKER.

The initial replay wording prevented silent replay but did not fully define consumption.

Revised invariant:

```text
ONE manifestId
=> AT MOST ONE command-principal root
```

The expected principal/initial-credential/grant sequence may share one consumption lineage.

The same manifest must never create a second command principal.

Same manifest/digest recovery may only resume or return the same known lineage.

## Adversarial finding C — envelope metadata must be signed

BLOCKER.

The initial manifest digest did not itself bind:

```text
algorithmId
signerKeyId
signerKeyFingerprint
```

Those fields are security relevant.

Revised proposed signature preimage:

```text
DOMAIN=FLOOOW:S2A:APPROVAL-SIGNATURE:1

algorithmId
signerKeyId
signerKeyFingerprint
manifestDigest
```

Deterministic canonical encoding is required.

Algorithm or key substitution must invalidate the signature.

## Adversarial finding D — signer claims cannot authorize themselves

BLOCKER.

Manifest fields such as:

```text
approvalSource
accountableOperator
signer labels
```

are signed descriptive claims only.

They cannot establish signer authority.

An independently trusted, versioned, bounded, revocable signer-authorization source is required.

Until that source is frozen:

```text
SIGNER_AUTHORIZATION_MODEL=UNFROZEN
REAL_FIELD_PROOF=HOLD
```

## Adversarial finding E — historical re-verification

HIGH.

Persisting only a digest, key fingerprint, and boolean verification result is insufficient for independent future cryptographic re-verification.

An accepted attestation must retain or immutably reference:

```text
canonical manifest bytes or lossless immutable artifact
manifest digest
algorithm ID
signer key ID
signer key fingerprint
signature
signer-authorization lineage reference
```

No signing private key is stored.

## Adversarial finding F — evidence binding contract incomplete

HIGH.

`evidenceBindingFingerprint` is required but its exact v1 ordered input set is not yet frozen.

Implementation before golden vectors would permit incompatible definitions of what the human actually approved.

Therefore:

```text
EVIDENCE_BINDING_V1_INPUT_SET=UNFROZEN
IMPLEMENTATION=HOLD
```

## Adversarial finding G — key lifecycle timing incomplete

HIGH.

Historical signature verification and permission to execute are distinct.

The design must freeze behavior for:

```text
ACTIVE
RETIRED
REVOKED
COMPROMISED
```

and the relevant effective times.

A key may remain historically verifiable while no longer being eligible to authorize a new field proof.

## Adversarial finding H — canonical time / human-policy identifiers

HIGH/MEDIUM.

The design requires a deterministic timestamp representation but has not yet frozen the exact byte representation.

Human identities and policy-bearing fields also need stable IDs or versioned references where they affect verification semantics.

Free-form text must not become an ambiguous authorization primitive.

## Revised selected architecture

```text
human approval
-> canonical manifest
-> signed envelope
-> independent signer authorization
-> accepted immutable attestation evidence
-> mandatory authority-boundary attestation binding
-> one authority-root consumption lineage
-> runtime authentication
-> governed writer
-> immutable identity decision
```

Invariant:

```text
SIGNED MANIFEST != AUTHORITY
SIGNATURE VALID != SIGNER AUTHORIZED
ACCEPTED ATTESTATION != COMMAND GRANT
VERIFIED APPROVAL != EXECUTION
AUTHORITY != EXECUTION
```

## Replay domains

Three replay domains remain independent:

```text
ATTESTATION:
manifestId + manifestDigest + single authority-root consumption

ISSUER:
organizationId + operationId + intentFingerprint

WRITER:
decisionId + immutable intent
```

## Current findings classification

```text
BLOCKER=4
HIGH=4
MEDIUM=2
LOW=0
```

BLOCKER:

1. mandatory attestation enforcement at authority provisioning boundary;
2. single-use authority-root consumption semantics;
3. independently trusted signer-authorization source;
4. signed security-envelope metadata contract.

HIGH:

1. evidence-binding v1 input set;
2. key lifecycle / revocation temporal semantics;
3. exact canonical timestamp representation;
4. independently re-verifiable retention contract.

MEDIUM:

1. stable human/policy identifier representation;
2. concrete attestation-to-authority receipt linkage and storage/locking shape.

These are design findings, not implementation defects.

## Blocker closure revision 2

The four Revision-1 BLOCKER findings were closed at design-contract level.

### Closed B1

```text
LAUNCHER_ONLY_ENFORCEMENT = REJECTED
REAL_ISSUER_DIRECT_AUTHORITY_DML = DENIED_BY_DESIGN
ATTESTATION_AWARE_PROVISIONING_BOUNDARY = REQUIRED
```

The future real issuer must not possess direct INSERT privilege on command-authority or authority-operation tables.

### Closed B2

```text
ATTESTATION_CONSUMPTION = APPEND_ONLY
CONSUMPTION_KEY = organizationId + manifestId
MAX_PRINCIPAL_ROOTS_PER_ATTESTATION = 1
```

Principal creation, consumption, and authority receipt must commit atomically.

### Closed B3

```text
SIGNER_AUTHORIZATION = INDEPENDENT_APPROVAL_GOVERNANCE_LINEAGE
MANIFEST_SELF_CLAIMS = NOT_AUTHORITY
COMMAND_PERMISSION_GRANT = NOT_SIGNER_AUTHORITY
```

Actual approved signer-authority values remain human decisions.

### Closed B4

```text
SIGNATURE_V1_ALGORITHM = Ed25519
SIGNATURE_V1_DOMAIN = FLOOOW:S2A:APPROVAL-SIGNATURE:1
KEY_FINGERPRINT = SHA256_DER_SUBJECT_PUBLIC_KEY_INFO_LOWER_HEX
SIGNATURE_TRANSPORT = BASE64URL_NO_PADDING
ALGORITHM_NEGOTIATION = NONE
```

JVM toolchain 21 was confirmed in the repository build conventions.

### Revised findings

```text
BLOCKER=0
HIGH=4
MEDIUM=2
LOW=0
```

The remaining HIGH findings are:

1. exact `evidenceBindingFingerprint` v1 ordered input set;
2. key retirement/revocation/compromise temporal semantics;
3. exact canonical timestamp/string representation and golden vectors;
4. accepted-attestation retention representation for durable independent re-verification.

The remaining MEDIUM findings are:

1. stable representation of human/policy identifiers;
2. concrete attestation-to-authority receipt linkage and storage/index/locking shape.

### Gate

```text
BLOCKER_CLOSURE_DESIGN=PASS
IMPLEMENTATION_READY=NO
VERSIONING_READY=NO

NEXT_GATE=HIGH_FINDINGS_CLOSURE_DESIGN
```

No implementation, migration, authority creation, provider call, staging, commit, or push is authorized.


## High findings closure revision 3

The read-only HIGH-closure audit concluded that all four HIGH findings have technically sufficient design contracts.

### Closed HIGH 1

```text
HIGH_1_EVIDENCE_BINDING = CLOSED_BY_DESIGN
DOMAIN = FLOOOW:S2A:EVIDENCE-BINDING:1
DIGEST = SHA256_CANONICAL_BYTES_LOWER_HEX
```

The exact ordered 23-field evidence-binding contract is frozen in SPEC-0088.

The approval binding distinguishes target identity, evidence-currentness binding, and writer currentness.

Omie missing currency remains NULL/neutral and is never inferred as BRL.

The later SPEC-0084 / implemented writer semantic evidence contract governs over the older raw-provider-fingerprint wording.

### Closed HIGH 2

```text
HIGH_2_KEY_LIFECYCLE = CLOSED_BY_DESIGN
KEY_LINEAGE = APPEND_ONLY
STATES = ACTIVE | RETIRED | REVOKED | COMPROMISED
```

Historical cryptographic verification and new execution eligibility are separate.

Only ACTIVE keys are eligible for new execution, subject to every other gate.

Revocation, retirement, or compromise before execution denies.

Later lifecycle events do not mutate already committed identity decisions.

### Closed HIGH 3

```text
HIGH_3_CANONICAL_REPRESENTATION = CLOSED_BY_DESIGN
FRAMING = UINT32_BE_LENGTH_PREFIX
TEXT = UTF8
INSTANT = UTC_MICROSECOND_6_DIGIT_Z
UNICODE = NFC_REQUIRED_NO_SILENT_NORMALIZATION
```

The contract reuses the existing FLOOOW binary length-prefix precedent.

Exact golden-vector bytes and hashes remain mandatory implementation proof.

### Closed HIGH 4

```text
HIGH_4_RETENTION = CLOSED_BY_DESIGN
MODEL = IMMUTABLE_CANONICAL_PROOF_ARTIFACT
INDEXES = DERIVED_NON_AUTHORITATIVE
CONSUMPTION = SEPARATE_IMMUTABLE_RECORD
```

Historical SPKI DER bytes and detached signature material are retained for independent re-verification.

Private keys and command credentials are prohibited.

Failed verification attempts do not become accepted attestation evidence.

### Cross-HIGH reconciliation

All four contracts use the same canonical primitive family:

```text
canonical manifest
-> evidence-binding fingerprint
-> signature preimage
-> key/signer lineage fingerprints
-> accepted proof artifact fingerprint
```

Accepted attestation remains evidence.

Signer authorization remains approval-governance authority.

Command permission remains execution authority.

Attestation consumption remains the one-time bridge.

Writer currentness remains the final identity-admission gate.

### Current classification

```text
BLOCKER=0
HIGH=0
MEDIUM=2
LOW=0
```

No new BLOCKER or HIGH was discovered.

Remaining MEDIUM findings:

```text
MEDIUM_1=stable human/policy identifier representation
MEDIUM_2=concrete migration/index/locking and attestation-to-receipt linkage
```

### Gate

```text
HIGH_CLOSURE_DESIGN=PASS
IMPLEMENTATION_READY=NO
VERSIONING_READY=NO
NEXT_GATE=MEDIUM_FINDINGS_CLOSURE_DESIGN
```

No implementation, migration, authority creation, key creation, provider call, staging, commit, or push is authorized.


## Final design closure revision 4

The final read-only design-closure audit concluded that both remaining MEDIUM findings have technically sufficient v1 contracts.

```text
MEDIUM_1_IDENTIFIER_MODEL=CLOSED_BY_DESIGN
MEDIUM_2_PERSISTENCE_LOCKING_LINKAGE=CLOSED_BY_DESIGN
```

Frozen conceptual physical model:

```text
s2a_signer_key_revision
s2a_signer_authority_revision
s2a_accepted_attestation
s2a_attestation_consumption
```

Selected authority linkage:

```text
command_authority_operation.attestation_manifest_id
```

No APPROVAL operation is added.

Future trust separation:

```text
approval governance
!= attestation verifier
!= command issuer
!= command runtime
```

Future real issuer direct authority-table mutation is removed in favor of narrow attestation-aware capabilities.

Three ordered trust boundaries are frozen:

```text
approval governance
-> accepted attestation evidence
-> authority linkage + issuer privilege hardening
```

Final findings:

```text
BLOCKER=0
HIGH=0
MEDIUM=0
LOW=0
NEW_BLOCKER=0
NEW_HIGH=0
NEW_MEDIUM=0
```

Design closure gate:

```text
DESIGN_CLOSURE_AUDIT=PASS
TECHNICAL_DESIGN_COMPLETE=YES
BOUNDED_IMPLEMENTATION_SPECIFIABLE=YES
IMPLEMENTATION_READY=NO
VERSIONING_READY=NO
NEXT_GATE=REVISION_4_DOCUMENT_VALIDATION
```

Implementation and real field proof remain HOLD.


## Human decisions still required
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

## Final classification

```text
ADR_0088=FINAL_DESIGN_CLOSURE_REVISION_4
SPEC_0088=FINAL_DESIGN_CLOSURE_REVISION_4
TASK_0165S2A3=FINAL_DESIGN_CLOSURE_EVIDENCE_REVISION_4

IMPLEMENTATION_READY=NO
VERSIONING_READY=NO

IMPLEMENTATION=HOLD
MIGRATION=HOLD
CRYPTO_IMPLEMENTATION=HOLD
SIGNER_REGISTRY=HOLD
LAUNCHER_CONFIG=HOLD
REAL_FIELD_PROOF=HOLD
REAL_AUTHORITY=NONE
PROVIDER_CALL=NONE

NEXT_GATE=REVISION_4_DOCUMENT_VALIDATION
```

## Implementation contract completion revision 5

Revision 4 architecture remains valid. V040 blueprint review discovered two implementation-contract omissions in the versioned documents:

```text
BLOCKER_1=VERSIONED_PHYSICAL_AUTHORITY_CONTRACT_INCOMPLETE
BLOCKER_2=LINEAGE_FINGERPRINT_PREIMAGES_UNDEFINED
```

Revision 5 closes only those omissions. It does not redesign B1-B4, HIGH 1-HIGH 4, MEDIUM 1-MEDIUM 2, the command-authority substrate, or the V040/V041/V042 trust boundaries.

### Blocker 1 closure evidence

The versioned physical contract now freezes:

```text
SignerAuthorityId = immutable organization-scoped revision-row identity
PRIMARY KEY = organization_id + signer_authority_id
SCOPED_REVISION_UNIQUE = organization + subject + key + action + permission + revision
PREDECESSOR = supersedes_signer_authority_id
NON_NULL_PREDECESSOR_UNIQUE = YES
EXACT_PREDECESSOR_FK = YES
EXACT_SIGNER_KEY_REVISION_FK = YES
CURRENT_LEAF = unique unsuperseded row
MUTABLE_CURRENT_TABLE = NONE
STATE = ENABLED | DISABLED
```

Every successor receives a new signer-authority ID. The authority scope lock is independent of that per-revision ID.

### Blocker 2 closure evidence

Frozen domains:

```text
KEY_LINEAGE_DOMAIN=FLOOOW:S2A:SIGNER-KEY-LINEAGE:1
SIGNER_AUTHORITY_DOMAIN=FLOOOW:S2A:SIGNER-AUTHORITY-LINEAGE:1
```

Both contracts freeze ordered semantic inputs, Revision 3 canonical framing, nullable predecessor encoding, lowercase hexadecimal SHA-256, predecessor fingerprint chaining, DB recomputation, and independent Kotlin computation.

Audit/trace metadata is explicitly excluded:

```text
KEY_EXCLUDED=reason,provenance,correlationId,recordedAt
AUTHORITY_EXCLUDED=reason,provenance,correlationId,decidedAt
```

Golden-vector evidence:

```text
KEY_R1_BYTES=383
KEY_R1_SHA256=9e83dedfa91c44e001cbf4dbbe729436942ca5b6a568865eff3641e45651de65

KEY_R2_BYTES=455
KEY_R2_SHA256=7910bae04e816d4f94cd2086c7963d66d104eb2e33d9795fa14e4f0ca47e21e4

AUTHORITY_R1_BYTES=551
AUTHORITY_R1_SHA256=983e222e3e8d9692261db6613c3f0767947c32399493c3ae7de1824aa6371254

AUTHORITY_R2_BYTES=658
AUTHORITY_R2_SHA256=04cb49bc072d0d5466a767f5bc0424e1e3f7fcd6ae486bd3b6bf4f45328452a6
```

The exact canonical preimage hexadecimal for all four vectors is versioned in SPEC-0088. Semantic-field and predecessor-fingerprint mutations produce different frozen hashes. Changes limited to excluded audit metadata reproduce the original hash.

### Canonical text closure

```text
UTF8=REQUIRED
NFC=REQUIRED_BEFORE_VALIDATION
NON_NFC=DENY
LEADING_OR_TRAILING_WHITESPACE=DENY
PROHIBITED_CONTROL=DENY
SILENT_NORMALIZATION=FORBIDDEN
TRIM=FORBIDDEN
CASE_FOLD=FORBIDDEN
REPAIR=FORBIDDEN
```

### Boundary preservation

```text
V040=APPROVAL_GOVERNANCE
V041=ACCEPTED_ATTESTATION_EVIDENCE_AND_VERIFIER
V042=CONSUMPTION_AUTHORITY_LINKAGE_ISSUER_HARDENING_EXECUTION_ELIGIBILITY

COMMAND_AUTHORITY_EFFECT_IN_V041=NO
APPROVAL_OPERATION_ADDED=NO
POLICY_ADMIN_INCLUDED=NO
PROVIDER_CALL=NONE
REAL_FIELD_PROOF=HOLD
```

### Revision 5 classification

```text
REVISION_5_IMPLEMENTATION_CONTRACT_COMPLETION=PASS

BLOCKER_1_VERSIONED_PHYSICAL_AUTHORITY_CONTRACT=CLOSED
BLOCKER_2_LINEAGE_FINGERPRINT_PREIMAGES=CLOSED

BLOCKER=0
HIGH=0
MEDIUM=0

ARCHITECTURAL_REVISION=NO
IMPLEMENTATION_CONTRACT_ADDENDUM=YES

IMPLEMENTATION_READY=NO
VERSIONING_READY=NO

IMPLEMENTATION=HOLD
MIGRATION=HOLD
REAL_FIELD_PROOF=HOLD
REAL_AUTHORITY=NONE
PROVIDER_CALL=NONE

NEXT_GATE=REVISION_5_DOCUMENT_ADVERSARIAL_REVIEW
```

## V041 implementation contract completion revision 6 evidence

Revision 6 reconciled the prior V041 audit and froze the manifest,
signature, accepted-proof, persistence, replay, time, locking, trust,
privilege, SQLSTATE and Kotlin contracts without changing architecture.

MANIFEST_V1_BYTES=793
MANIFEST_V1_SHA256=209c15498e4da3568d52e44e121515457b4001e478221002c4b4e3c04184a8d0

SIGNATURE_PREIMAGE_V1_BYTES=222
SIGNATURE_PREIMAGE_V1_SHA256=d011a3dd9a4eca3f07be18bacdb32720effba0babad1b80814156bb20d9bcfa2

ACCEPTED_PROOF_V1_BYTES=1596
ACCEPTED_PROOF_V1_SHA256=9bf856a724a921d7a63a87c551fdcf82e896fb13b184c785909269ecdbe685b9

SIGNATURE_V1_JAVA_21_JCA_VERIFY=PASS
INDEPENDENT_VECTOR_REPRODUCTION=PASS
POSTGRES_ED25519_PRIMITIVE=NONE
TRUSTED_JVM_VERIFIER_BOUNDARY=EXPLICIT
COMMAND_AUTHORITY_EFFECT_IN_V041=ZERO

BLOCKER=0
HIGH=0
MEDIUM=0
LOW=1

IMPLEMENTATION=HOLD
V042=HOLD
REAL_FIELD_PROOF=HOLD
NEXT_GATE=REVISION_6_IMPLEMENTATION_CONTRACT_ADVERSARIAL_REVIEW

## Revision 6.1 trusted verifier boundary closure evidence

The prior LOW classification was upgraded to HIGH because PostgreSQL cannot prove that Java 21 JCA verification occurred before invocation of the accepted-evidence persistence capability.

Closure freezes:

```text
V041_VERIFIER_TCB=JAVA_21_JCA+DEDICATED_PROCESS_IDENTITY+DEDICATED_DB_CAPABILITY+SAME_JDBC_TRANSACTION+LOCKED_V040_SNAPSHOT
POSTGRES_ED25519_AUTHORITY=NO
JAVA_21_JCA_ED25519_AUTHORITY=YES
PERSISTENCE_PRIMITIVE=s2a_persist_attestation_verification_result
PUBLIC_EXECUTE=NO
ISSUER_EXECUTE=NO
RUNTIME_EXECUTE=NO
GOVERNANCE_EXECUTE=NO
HUMAN_OPERATOR_EXECUTE=NO
V041_ROLE_MEMBERSHIP_CREATED_BY_MIGRATION=NO
WRONG_SIGNATURE_PROOF=JVM_TRUSTED_VERIFIER_API
DB_PROOF=STRUCTURE+GOVERNANCE+CANONICAL_INTEGRITY+SERIALIZATION+IMMUTABILITY+REPLAY+PRIVILEGES
V042_INDEPENDENT_ED25519_REVERIFICATION=MANDATORY
V042_MUST_DENY_UNLESS_INDEPENDENT_REVERIFICATION_PASSES=YES
V041_COMMAND_AUTHORITY_EFFECT=ZERO
```

A compromised dedicated verifier identity is a compromise of the complete V041 verifier TCB and can persist invalid-signature evidence satisfying non-cryptographic database constraints. This is not a supported alternate API.

Such evidence cannot produce V042 consumption or command authority unless V042's separately mandatory independent Ed25519 verification and current-eligibility checks also succeed. Any V042 verification failure requires consumption delta zero and command-authority delta zero.

```
REVISION_6_1_TRUSTED_VERIFIER_HIGH=CLOSED_BY_DESIGN
BLOCKER=0
HIGH=0
MEDIUM=0
LOW=0
IMPLEMENTATION=HOLD
V042=HOLD
REAL_FIELD_PROOF=HOLD
```

## Consolidated documentary closure evidence — Revisions 7-7.3

The canonical ADR and specification now contain a self-contained implementation-exact V041 contract. This evidence entry records documentary closure only; no Kotlin, SQL migration, Gradle, test, role, V040, V042 or real-field-proof implementation was performed.

The consolidated contract freezes:

- the single Kotlin domain surface, including `SignerApprovalPermission` isolation;
- canonical unpadded base64url signed-envelope parsing and defensive byte ownership;
- exact accepted-proof DER storage and byte-content equality;
- the sole manifest/signature, evidence, accepted-proof and typed-JCA codec surfaces;
- both complete PostgreSQL capability signatures;
- the exact 21-column append-only accepted-attestation relation and PK-only index policy;
- Java 21 JCA as the Ed25519 authority and PostgreSQL as the governance/integrity/serialization authority;
- one `READ_COMMITTED` JDBC transaction and the complete lock order;
- server-owned first-acceptance timestamps and stored replay timestamps;
- V040 signer-key temporal resolution and exact authority/effective-key binding;
- complete Mercado Livre and Omie scope/integrity/selection procedures;
- the 22-field durable evidence binding plus its domain frame;
- `DETAIL`-only SQLSTATE result mapping;
- organization lifecycle and historical replay behavior;
- verifier-role contamination and privilege denial;
- the full adversarial test matrix and zero command-authority-effect proof;
- mandatory independent V042 cryptographic and execution-time reverification.

The pre-existing canonical hexadecimal fixtures in SPEC-0088 were not edited. Their preserved anchors are:

```text
MANIFEST_V1_BYTES=793
MANIFEST_V1_SHA256=209c15498e4da3568d52e44e121515457b4001e478221002c4b4e3c04184a8d0
SIGNATURE_PREIMAGE_V1_BYTES=222
SIGNATURE_PREIMAGE_V1_SHA256=d011a3dd9a4eca3f07be18bacdb32720effba0babad1b80814156bb20d9bcfa2
ACCEPTED_PROOF_V1_BYTES=1596
ACCEPTED_PROOF_V1_SHA256=9bf856a724a921d7a63a87c551fdcf82e896fb13b184c785909269ecdbe685b9
EVIDENCE_BINDING_V1_BYTES=529
EVIDENCE_BINDING_V1_SHA256=9f61859daa192ae3482ad3dbb28cd7ebb5d2f143cdb6e83092054a80b512e965
```

```text
REVISION_7_IMPLEMENTATION_EXACT_CONTRACT=CLOSED
REVISION_7_1_SQL_EVIDENCE_CLOSURE=CLOSED
REVISION_7_2_KOTLIN_RECONCILIATION=CLOSED
REVISION_7_3_CODEC_RECONCILIATION=CLOSED

BLOCKER=0
HIGH=0
MEDIUM=0
LOW=0
TECHNICAL_CONTRACT_OPEN_DECISIONS=0

V040_CHANGE_REQUIRED=NO
POSTGRES_ED25519_AUTHORITY=NO
JAVA_21_JCA_ED25519_AUTHORITY=YES
COMMAND_AUTHORITY_EFFECT_IN_V041=ZERO

V041_IMPLEMENTATION=HOLD
V042=HOLD
REAL_FIELD_PROOF=HOLD
NEXT_GATE=CONSOLIDATED_DOCUMENT_DIFF_AUDIT
```
