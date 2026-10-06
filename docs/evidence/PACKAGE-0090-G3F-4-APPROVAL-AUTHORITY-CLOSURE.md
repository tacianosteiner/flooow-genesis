# Package0090 G3F.4 — rehearsal approval authority closure

**Host approval PASS; binding/admission HOLD.** The newly authorized PACKAGE0090_REHEARSAL_HOST_DEPLOYMENT_APPROVAL ceremony was executed for deployment `8f05fc47-d043-47c7-8130-c50890717f3e` and incarnation `83ad4115-4be5-44c6-b0e5-24fd0f068d6f`. Existing allocation digest and actual four OID/name/attribute/membership pairs were revalidated. Both new identities were generated once, recorded initially UNAPPROVED, checked against full Package0090 historical evidence and current non-secret control state, then independently approved by the authorized host administrative workflow. No historical timing UUID was reused.

[Approval artifact](PACKAGE-0090-G3F-4-REHEARSAL-DEPLOYMENT-APPROVAL.json): exact canonical JSON bytes, frozen SHA256 `84a0afd98f68a25c360e7b3e2056e92c9c9d945f364bf9d8931a730908d752de`. Python strict decode/re-encode and independent Node parse/recursive canonical re-encode twice produced identical bytes/digest; read-only attribute applied. Authority comes from the explicit new user authorization and attributable ADMIN decision, not from hashing or UUID existence. Artifact binds baseline, database OID/system identifier, exact PG18.4/container/image/volume, allocation digest/slot tuples, canonical V043 hash/fence, environment and prohibitions. Approval creates no domain execution authority and does not mark READY.

The [binding authorization record](PACKAGE-0090-G3F-4-REHEARSAL-BINDING-AUTHORIZATION.json) is explicitly **withheld**, not a usable one-time provisioning token. Its immutable bytes reference the approval hash, exact pair, system identifier, roles/slot bytes and required existing ADMIN path, but identify missing expected-header input and prerequisite row scope. No fictional binding ID/fingerprint/transaction/commit was assigned.

Why provisioning stopped before write: fresh incarnation has no installed offline_readiness row. Installed header FK1 is immediate and references that row; readiness in turn requires an active key via its deferred FK. The only existing readiness/key context belongs to the expressly prohibited negative timing incarnation and contains placeholder history/ACL bytes. Reuse would violate this task. Additionally, a committed header must have its independently supplied expected original SignedApprovalAttestation: the installed reverse FK is DEFERRABLE INITIALLY DEFERRED, not optional at commit. Section9's exact header + embedded-slot row set does not include readiness/key or original-input rows. Existing canonical registration cannot meet these constraints with only that set; no bypass, SQL fixture helper or new writer is allowed.

Original-input source review: actual S02 A/B original signed manifests exist in the preserved isolated fixture. The complete38-field VECTOR1/2/3 codec goldens explicitly state signed_acceptance_proof=false and belong to a different manifest/context. They are not missing files; they are different evidence. A complete matching independent plan/header/original input for this new canonical registration was not resolved. Combining them, changing signed validity windows, manufacturing a signature or treating host approval as domain approval would fabricate authority. No such construction was used.

This closes the new host-approval governance boundary only. Existing DB data/authority is untouched: headers0/slots0, all control data equal. Fingerprint PRE=POST `d3b57ed08d9ba09f2a3db25219f36f436b6d4d2c5d2f5eccc59ca38ca03ad90b` includes roles/memberships/owners/ACL/defaults/policy/migrations, all control schemas/constraints/triggers, installed function definitions and deployment configuration, excluding authorized header DATA/count. A second read-only snapshot was captured after freezing the artifacts; it matches the original snapshot exactly. Lossless records/tools are in [provisioning evidence](PACKAGE-0090-G3F-4-REHEARSAL-BINDING-PROVISIONING.json).

Native prototype prerequisite is unsatisfied. [Runtime matrix](PACKAGE-0090-G3F-4-LOGIN-EVENT-ENROLLMENT-RUNTIME.json) marks all required cases NOT_RUN. No native function/event registration, receiver, live identity classification, pidfd exchange, ACCEPT/admission barrier or enrolled-process restart qualification occurred. Administrative read-only startup/shutdown is not restart-invalidation proof. The absent-header design remains retained, but no actual native per-login DENY is claimed. [Independent DNA verification](PACKAGE-0090-G3F-4-DNA-INVARIANT-REVIEW.md) records each invariant and the runtime gaps.

Preserved all26 earlier authorized dirty files byte-for-byte, all tracked source files unchanged; six new required artifacts make32 authorized dirty paths and unrelated0. Branch checkpoint/package-0090-cloud-handoff; local/fetched remote `401a5e313efbec9a4100af8b6b6e237fffb4ca38`. No commit/push under HOLD. Container stopped after post-ceremony verification; startup plaintext erased; no password rotation, protected DB/production-secret access, policy/timing/fixture/native/migration mutation or destructive signaling. BLOCKER0/HIGH2/MEDIUM0/LOW0, watchdog HIGH/H01 remain OPEN.

Next bounded gate: **G3F_4_CANONICAL_BINDING_PREREQUISITE_DATA_SCOPE_CLOSURE**. Retain this frozen approved pair/artifact; do not regenerate identities or reapprove the timing UUIDs. Supply/validate the complete exact38-field header and independent original input, and explicitly close the minimal existing prerequisite DATA set: fresh NOT_READY readiness and its required private preflight-key linkage, original expected signed-attestation tuple and required existing lifecycle/control initialization. No new table/function/role/privilege/policy, no READY transition, no duration change and no domain effect is needed or authorized. Review the complete one-time immutable transaction authorization before canonical registration, then qualify the conditionally authorized native admission prototype. Existing canonical constraints/fence must remain intact.

```text
NEW_REHEARSAL_DEPLOYMENT_ID=8f05fc47-d043-47c7-8130-c50890717f3e
NEW_REHEARSAL_INCARNATION_ID=83ad4115-4be5-44c6-b0e5-24fd0f068d6f
INDEPENDENT_DEPLOYMENT_APPROVAL=PASS_HOST_SCOPE_ONLY
INDEPENDENT_INCARNATION_APPROVAL=PASS_HOST_SCOPE_ONLY
APPROVAL_ARTIFACT_SHA256=84a0afd98f68a25c360e7b3e2056e92c9c9d945f364bf9d8931a730908d752de
APPROVAL_AUTHORITY=PACKAGE0090_REHEARSAL_HOST_DEPLOYMENT_APPROVAL
APPROVAL_AUTHORITY_INDEPENDENT_OF_RUNTIME_SERVICES=YES
ROLE_ALLOCATION_MATCHES_RUNTIME=YES
BINDING_PROVISIONING=HOLD_REQUIRED_PREREQUISITE_DATA_AND_COMPLETE_HEADER_INPUT
NEGATIVE_BINDING_MATRIX=NOT_RUN_NO_VALID_BINDING
LOGIN_EVENT_OCCURRED=NOT_RUN_NATIVE_ADMISSION_PROTOTYPE
SERVER_DERIVED_IDENTITY=NOT_RUN_NATIVE_ADMISSION_PROTOTYPE
GOVERNED_ROLE_RECOGNITION_AFTER_SERVER_IDENTITY=NOT_RUN
GOVERNED_ROLE_WITHOUT_BINDING_FAIL_CLOSED=NOT_RUN_RUNTIME
BINDING_TO_APPROVED_DEPLOYMENT=NOT_RUN_NO_HEADER
BINDING_TO_APPROVED_INCARNATION=NOT_RUN_NO_HEADER
PIDFD_SELF_ENROLLMENT=NOT_RUN_THIS_GATE
LOGIN_PIDFD_ENROLLMENT_HANDSHAKE=NOT_RUN
WATCHDOG_ACCEPT=NOT_RUN
SESSION_ADMISSION_BARRIER=NOT_RUN
POSTMASTER_RESTART_INVALIDATION=NOT_RUN_NO_ENROLLMENTS
AUTHORITY_FINGERPRINT_PRE=d3b57ed08d9ba09f2a3db25219f36f436b6d4d2c5d2f5eccc59ca38ca03ad90b
AUTHORITY_FINGERPRINT_POST=d3b57ed08d9ba09f2a3db25219f36f436b6d4d2c5d2f5eccc59ca38ca03ad90b
AUTHORITY_STATE_UNCHANGED=YES
EVIDENCE_BEFORE_CLAIM=PASS
SERVER_IDENTITY_BEFORE_CLASSIFICATION=PASS_DESIGN_RUNTIME_NOT_RUN
APPROVAL_BEFORE_BINDING=PASS_APPROVAL_RECORDED_NO_BINDING_WRITE
AUTHORITY_MINIMIZATION=PASS
FAIL_CLOSED=PASS_PREREQUISITE_STOP_RUNTIME_NOT_RUN
NO_SILENT_FALLBACK=PASS
PROVENANCE_PRESERVED=PASS
RUNTIME_SERVICE_SELF_APPROVAL=NO
HASH_CONFUSED_WITH_AUTHORITY=NO
READINESS_CONFUSED_WITH_APPROVAL=NO
BINDING_CONFUSED_WITH_EXECUTION=NO
DNA_REVIEW=HOLD_NATIVE_ADMISSION_INVARIANTS_NOT_RUNTIME_QUALIFIED
NEW_AUTHORITY_CONTRACT=HOST_APPROVAL_CLOSED_BINDING_ADMISSION_HOLD
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
WORKTREE=DIRTY_AUTHORIZED_32_FILES
NEXT_GATE=G3F_4_CANONICAL_BINDING_PREREQUISITE_DATA_SCOPE_CLOSURE
```
