# Package 0090 — binding provisioning contract design

**HOLD — new approval authority requires explicit authorization.** Existing Package0090 contracts require independently approved host/incarnation and assign trusted administrative responsibilities. They do not specify an executable immutable host approval artifact, creation/approval ceremony, current revocation source or exact admission-roster deployment format. The proposed contract below is design only and approves no identity. Section19 stops execution before using it.

Branch checkpoint/package-0090-cloud-handoff; local/fetched remote `401a5e313efbec9a4100af8b6b6e237fffb4ca38`. Preserve all22 prior dirty files byte-for-byte, with inventory path/size/SHA/origin/purpose in the approval matrix. Four new required evidence artifacts make26 authorized dirty paths; unrelated0. No commit/push under HOLD. All tracked sources/migrations and previous artifacts unchanged. Disposable PG18.4 read-only catalog inspection completed; container stopped and temporary plaintext erased.

The [approval matrix](PACKAGE-0090-DEPLOYMENT-INCARNATION-APPROVAL-MATRIX.json) contains full-source search inventory, candidate classifications, proposed artifact/ceremony, structural review and complete before/after authority payloads plus lossless raw evidence/tool. The [recognition matrix](PACKAGE-0090-GOVERNED-ROLE-RECOGNITION-MATRIX.json) contains exact runtime allocation and fail-closed design. The [negative matrix](PACKAGE-0090-BINDING-PROVISIONING-NEGATIVE-MATRIX.json) separates expected design rejection from conditional tests NOT_RUN.

All111 Package0090 docs/evidence and linked0087/0088/Task0133 were fully scanned for equivalent approval concepts; canonical ADR/SPEC/V043 and launcher were inspected. SPEC18/21/25 refer to sections of SPEC0090. No standalone ADR133 exists: ADR0090 line133 is the relevant open packaging/representation decision; it forbids changing bootstrap trust, incarnation procedure or guards. TASK0133 is unrelated inventory source authority. Search conclusions apply to the available reviewed repository evidence, not inaccessible external systems.

Approval, allocation, policy, readiness and evidence stay distinct. SPEC0088 original SignedApprovalAttestation approves an exact domain transaction manifest; deployment/incarnation are absent and environment-dependent values excluded. Its Ed25519 keys and signer governance cannot be repurposed for host approval. SPEC25 policy governance approves immutable29-tag policy values and records deployment/incarnation references; those references do not approve a host. Fixture1 approval supplies synthetic golden timing values only. Launcher configuration consumes independent expectations; environment strings do not issue authority. ADR35/SPEC96 expressly require host/private marker agreement and external clone governance; a readiness FK, random UUID, copied system identifier or ADMIN write ability cannot satisfy them.

Existing allocation source: docs/evidence/PACKAGE-0090-G3F-4-INSTALLED-ACL.json, raw SHA256 `709ff68e0b56cf0b48817de326656ae07ddcc25d8b46d4eb8c1f83518a65b662`. It explicitly assigns the four exact role names to slots and exact wrapper grants; its service_roles map has no OIDs. Prior preserved binding matrix pins OID/name/attributes, and fresh installed catalog confirms AUDITOR19616, VERIFIER19621, ISSUER19624, EXECUTOR19631 with unchanged LOGIN/NOINHERIT/non-superuser attributes and zero memberships. Composite projection digest `92376c1065fc132ceda541897b5588ba4e28b51c1bedf92fbc398327dd4cde96` records source digest plus exact OID/name/purpose pairs; it is evidence integrity, not host approval. No prefix, naming convention or human inference assigns a slot. The existing allocation originates in separately authorized SERVICE_IDENTITY_ADMIN rehearsal creation, not this design report.

Recognition is independent of any active header. A future native login handler loads a complete trusted ADMIN-installed roster pinned to approved external allocation/host context. It derives authenticated role OID and exact name server-side. Exact OID OR exact allocated name selects a potentially governed identity; both components and one unique slot must match before continuation. Rename, drop/recreation or one-component mismatch denies rather than falling into unmanaged path. Neither-component match is unmanaged only when the complete trusted roster is valid. Missing/corrupt roster never becomes an empty roster; service-facing exposure remains excluded until it is valid. Direct postgres ADMIN is not service-enrolled. For every exact governed pair, zero headers/missing matching header, stale approved incarnation or ambiguous assignment denies login. Only one valid context reaches synchronous self-pidfd/SCM_RIGHTS ACCEPT/DENY; no usable governed work before ACCEPT. This closes the absent-header logic at PASS_DESIGN, not installed/runtime PASS.

Preserve existing R/M semantics: AUDITOR R permits bound reads after mutation expiry/revocation/terminal status, when readiness and read policy hold. Do not silently redefine such a retained current approved assignment as stale host approval or require mutation ACTIVE for every auditor login. M still requires ACTIVE and all existing time/possession guards. A current enrollment assignment is distinct from mutable mutation lifecycle. The proposed admission lifecycle needs explicit approval; imposing a stricter ACTIVE-only-all-slots rule would require a separate normative amendment. Likewise enrollment establishes monitoring only and never marks READY or admits wrapper effects while NOT_READY. No new numeric handshake duration, server epoch identity or runtime result is asserted.

Minimal proposed approval: an immutable external candidate identity statement plus a separate immutable administrative approval decision. Required fields bind schema/package/scope/environment, new deployment/incarnation candidates, exact host target/private marker and database/server constraints, expected source/rehearsal migration/history/surface, the four-role allocation artifact/digest/OID-name projection, existing fixture1 policy reference, creation time, approving responsibility/governance authorization reference, approval time, exact scope and current revocation/retirement rule. Versioned strict canonical JSON/SHA256 is proposed; identity and decision bodies exclude their own digest. A hash or self-declared approving field never authorizes: an independently authenticated existing administrative governance record and protected custody must pin the decision digest. No new signing key, service authority, SQL API, role or table is proposed. Concrete custody/reference and codec require authorization; no approval document is instantiated here.

Approver: existing trusted host/deployment ADMIN responsibility under explicit Package0090 governance, independent of AUDITOR/VERIFIER/ISSUER/EXECUTOR; SERVICE_IDENTITY_ADMIN validates allocation and PLAN_BINDING_ADMIN consumes verified approval. ADR allows these administrative responsibilities to be one trusted administrator, so no invented human assignment or required separation of administrative people is added. The new machine-consumable approval purpose/ceremony is a material deployment/evidence authority delta despite using existing administrative principals. NEW_APPROVAL_AUTHORITY_REQUIRED=YES. Runtime services and wrapper owners cannot self-approve or modify authoritative custody/roster.

Future authorized causal sequence: candidate generated once in approval ceremony → explicit independent approval decision → current trust/revocation/target/role/policy/history verification before BEGIN → existing direct ADMIN registration of header + independently supplied original SignedApprovalAttestation in one transaction with required lifecycle initialization → durable exact commit/audit association → role recognition/canonical header lookup → pidfd enrollment. Generation is identity creation, not approval; binding cannot create retroactive approval. No UUIDs were generated, and the two historical timing UUIDs are expressly prohibited for canonical use. Approval is not READY: approved state can remain NOT_READY, unhealthy or unbound; existing watchdog/policy/guard criteria still apply.

Replay: same approval can only return the already verified identical committed registration without another write; no UPSERT or invented binding. Unknown commit requires reconciliation. Same incarnation with changed role digest, same UUIDs with conflicting approval digest, revoked/stale authority or timing-fixture identifiers denies before DML. New incarnation requires existing governed exclusion/drain/invalidation and retirement of old identities; permanent role assignments/tombstones cannot be rebound. Normal DB/application restart retains host incarnation and requires new physical process enrollments. No existing policy or temporal value changes.

Storage is external to ordinary DB backup, with protected immutable administrative custody and read-only digest-pinned consumer configuration. V043 has no approval_digest column; do not overload provenance, policy digest, signed domain input or existing plan fingerprint. An external administrative transaction record must bind approval digest to exact binding ID/full fingerprint and acknowledged commit. That is an explicit proposed external association, not a cryptographic/structural V043 commitment. Missing external artifact format/custody is the current gap.

Both observed structural flags are EXTERNAL_GOVERNANCE_BY_DESIGN. Host/database ADMIN is trusted and outside operational attacker model, so host approval is intentionally verified before ADMIN DML, not promised as an FK to an absent approval table. Readiness is deployment-wide and provisioned before headers; no reverse header FK is normative, and empty headers remain a valid fail-closed state. Operational guards require matching bound context/readiness independently. No current normative DB invariant change was identified; V043 remains frozen/fenced. If stronger SQL enforcement or an approval digest column is later required, that needs a separate invariant/migration authorization; this design does not add it.

Fresh authority/configuration fingerprint PRE=POST=`d3b57ed08d9ba09f2a3db25219f36f436b6d4d2c5d2f5eccc59ca38ca03ad90b`, excluding header DATA/count and including all roles, memberships, owners/ACL/defaults, policy,15 control schemas/constraints/triggers,24 function definitions/configuration, event/preload/parameter state and migrations. Full non-secret control data also matched; headers/slots remain0. All conditional binding rejection/prototype tests are NOT_RUN because section19 applies. The design matrices do not claim SQL constraints reject external approval mismatches. No two execution-only approval/provisioning artifacts were created, no passwords rotated, no role/grant/policy/fixture/temporal/migration/native mutation or protected database access occurred.

Existing findings remain BLOCKER0/HIGH2/MEDIUM0/LOW0; H01 and watchdog deployment HIGH OPEN. Next determined gate: **G3F_4_REHEARSAL_DEPLOYMENT_APPROVAL_AUTHORITY_AUTHORIZATION**. Review/authorize this concrete external approval purpose, trusted custody/decision reference, exact creation/revocation/replay rules and roster/admission lifecycle. Only then may a separately bounded ceremony generate new identities and approve them; original domain inputs, canonical binding, synchronous epoch/ACK protocol and conditional runtime criteria remain required. No full watchdog implementation is authorized.

```text
EXISTING_DEPLOYMENT_APPROVAL_CONTRACT=EXTERNAL_GOVERNANCE_REQUIREMENT_ONLY_NO_EXECUTABLE_ARTIFACT_CONTRACT
EXISTING_INCARNATION_APPROVAL_CONTRACT=HOST_GOVERNANCE_AND_REINCARNATION_REQUIREMENT_ONLY_NO_APPROVAL_CEREMONY
EXISTING_APPROVAL_AUTHORITY=TRUSTED_HOST_DEPLOYMENT_ADMIN_RESPONSIBILITY_EXISTS
EXISTING_APPROVAL_ARTIFACT=MISSING_FOR_HOST_DEPLOYMENT_INCARNATION
ROLE_ALLOCATION_ARTIFACT=docs/evidence/PACKAGE-0090-G3F-4-INSTALLED-ACL.json
ROLE_ALLOCATION_DIGEST=709ff68e0b56cf0b48817de326656ae07ddcc25d8b46d4eb8c1f83518a65b662
ROLE_ALLOCATION_AUTHORITY=EXISTING_SERVICE_IDENTITY_ADMIN_REHEARSAL_CREATION_AND_ASSIGNED_WRAPPER_ALLOCATION
ROLE_ALLOCATION_MATCHES_RUNTIME=YES
GOVERNED_ROLE_RECOGNITION_SOURCE=EXPLICIT_HISTORICAL_ALLOCATION_PLUS_PINNED_OID_NAME_EVIDENCE_AND_FRESH_SERVER_CATALOG
GOVERNED_ROLE_RECOGNITION_INDEPENDENT_OF_ACTIVE_HEADER=YES
GOVERNED_ROLE_WITHOUT_BINDING_FAIL_CLOSED=PASS_DESIGN
SELECTED_APPROVAL_MECHANISM=PROPOSED_IMMUTABLE_EXTERNAL_ADMIN_APPROVAL_NOT_AUTHORIZED
APPROVAL_AUTHORITY=PROPOSED_EXISTING_TRUSTED_HOST_DEPLOYMENT_ADMIN_UNDER_EXPLICIT_PACKAGE_GOVERNANCE
APPROVAL_AUTHORITY_INDEPENDENT_OF_RUNTIME_SERVICES=YES
APPROVAL_PRECEDES_BINDING=YES_DESIGN
APPROVAL_STORAGE=PROPOSED_EXTERNAL_IMMUTABLE_ADMIN_ARTIFACT_OUTSIDE_ORDINARY_DB_BACKUP
BINDING_APPROVAL_DIGEST_BINDING=NO_V043_FIELD_EXTERNAL_TRANSACTION_ASSOCIATION_PROPOSED
HOST_APPROVAL_AND_RUNTIME_READINESS_SEPARATE=YES
BINDING_UNAPPROVED_INCARNATION_CLASSIFICATION=EXTERNAL_GOVERNANCE_BY_DESIGN
READINESS_WITHOUT_BINDING_CLASSIFICATION=EXTERNAL_GOVERNANCE_BY_DESIGN
DATABASE_AUTHORITY_DELTA=NONE_REQUIRED_OR_APPLIED_FOR_PROPOSED_APPROVAL_PATH
SERVICE_AUTHORITY_DELTA=NONE
DEPLOYMENT_AUTHORITY_DELTA=PROPOSED_NEW_APPROVAL_CEREMONY_AND_TRUSTED_ROSTER_CONFIGURATION
EVIDENCE_AUTHORITY_DELTA=PROPOSED_NEW_AUTHORITATIVE_APPROVAL_ARTIFACT_NOT_ACTIVATED
NEW_APPROVAL_AUTHORITY_REQUIRED=YES
NEW_REHEARSAL_DEPLOYMENT_ID=NOT_GENERATED
NEW_REHEARSAL_INCARNATION_ID=NOT_GENERATED
INDEPENDENT_DEPLOYMENT_APPROVAL=HOLD_NOT_APPROVED
INDEPENDENT_INCARNATION_APPROVAL=HOLD_NOT_APPROVED
CANONICAL_ROLE_SLOT_BINDING=HOLD_NO_HEADER
CANONICAL_INCARNATION_BINDING=HOLD_NO_APPROVED_INCARNATION
BINDING_PROVISIONING=NOT_RUN_NEW_CONTRACT_AUTHORIZATION_REQUIRED
NEGATIVE_BINDING_MATRIX=PASS_DESIGN_RUNTIME_NOT_RUN
LOGIN_HANDLER_BINDING_LOOKUP=PASS_DESIGN_RUNTIME_NOT_RUN
SERVER_DERIVED_IDENTITY=SOURCE_DESIGN_ONLY
ENROLLMENT_FAIL_CLOSED=PASS_DESIGN_RUNTIME_NOT_RUN
NEW_AUTHORITY_CONTRACT=HOLD_AUTHORIZATION_REQUIRED
DESIGN_SECURITY_REVIEW=HOLD
WATCHDOG_DEPLOYMENT_HIGH=OPEN
G3F4_H01=OPEN
BLOCKER_COUNT=0
HIGH_COUNT=2
MEDIUM_COUNT=0
LOW_COUNT=0
LOCAL_HEAD=401a5e313efbec9a4100af8b6b6e237fffb4ca38
REMOTE_HEAD=401a5e313efbec9a4100af8b6b6e237fffb4ca38
LOCAL_EQUALS_REMOTE=YES
WORKTREE=DIRTY_AUTHORIZED_26_FILES
NEXT_GATE=G3F_4_REHEARSAL_DEPLOYMENT_APPROVAL_AUTHORITY_AUTHORIZATION
```
