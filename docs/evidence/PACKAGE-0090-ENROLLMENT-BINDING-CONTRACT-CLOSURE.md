# Package 0090 — enrollment binding contract closure

**HOLD.** Canonical domain binding storage and a controlled ADMIN registration path already exist. Zero headers means an unprovisioned, fail-closed installation, not a missing writer. The complete host-bound connection-enrollment contract is not closed: the current deployment/incarnation UUIDs were expressly provisioned as negative timing prerequisites with placeholder manifests, not independently approved host identity. No conditional binding provisioning or native prototype is therefore authorized by this gate's prerequisites.

Branch `checkpoint/package-0090-cloud-handoff`; local and fetched remote HEAD `401a5e313efbec9a4100af8b6b6e237fffb4ca38`. No commit/push under HOLD. Eighteen historical dirty files were inventoried with size/SHA/origin/purpose and preserved, including the latest four omitted by the request's fourteen-file count. The four required new evidence files bring the authorized dirty total to22. Unrelated files0; all tracked files unchanged.

The [provisioning matrix](PACKAGE-0090-BINDING-PROVISIONING-MATRIX.json) inventories all15 installed control relations and24 functions, with owner, exact table/function/column ACL, PK/FK, triggers, immutable/lifecycle distinctions and dependencies. Catalog observations are independent of source expectations. Its source inventory hashes ADR/SPEC/V043 and historical allocation/timing evidence. The [runtime record](PACKAGE-0090-LOGIN-EVENT-BINDING-RUNTIME.json) contains fresh before/after non-secret control data; the [integrity record](PACKAGE-0090-BINDING-AUTHORITY-INTEGRITY.json) preserves complete canonical authority/configuration payloads, lossless capture tool and raw record.

Existing path: ADR Provisioning Impact and SPEC original signed-attestation amendment (lines2474–2492) authorize trusted ADMIN registration via plain INSERT, not a new SECURITY DEFINER registration API. Insert header then independently supplied expected original signed-attestation tuple in one transaction. Installed forward and deferred reverse FKs require both or neither at commit. The private existing ADMIN-owned trigger validates the expected tuple and prevents immutable input UPDATE/DELETE/TRUNCATE. ADMIN is a responsibility; `flooow_offline_control_owner` is a NOLOGIN owner. Existing direct `postgres` deployment authority performs reviewed administration, never a service login or added SET ROLE route. No registration writer needs invention. Registration also needs all38 immutable fields, exact original manifest/signature and required existing control initialization; a socket test cannot synthesize those inputs.

Historical slot allocation is explicit in PACKAGE-0090-G3F-4-INSTALLED-ACL.json.service_roles and its creation tool's per-slot allocation/assigned-wrapper contract. Actual fresh OIDs: AUDITOR19616, VERIFIER19621, ISSUER19624, EXECUTOR19631. Each exact name has LOGIN=true, INHERIT=false, no superuser/bypass/role/database/replication authority and zero incoming/outgoing memberships. This establishes rehearsal allocation without a string heuristic; it does not create a header assignment. Slots are four length-prefixed binary records embedded in header.identity_slots, ordered VERIFIER1/ISSUER2/EXECUTOR3/AUDITOR4, with both role OID and exact NFC name, uniqueness and complete-byte-consumption checks.

Observed deployment `2430bd66-ee5b-49e9-aaf9-9dc1fbd9b547` and incarnation `fa105a00-acf1-4ddf-846b-08096978637d` match the prior timing fixture exactly. That evidence states eligible_for_operation=false and NEGATIVE_PREREQUISITE_ONLY_NEVER_ACTIVATED. Readiness remains NOT_READY/watchdog unhealthy, with one unchanged fixture-1 policy row and placeholder history/ACL bytes. No independently approved host record/private-marker agreement was found in the reviewed allowed sources. Neither row existence, random historical UUID generation, container identity nor a copied system identifier supplies that missing approval. Normal database/application restart retains incarnation; clone/restore requires separately governed REINCARNATION, inaccessible NOT_READY state and old-identity invalidation.

Installed FK graph: header→readiness by incarnation; header→policy by version; header↔expected signed input by binding ID; readiness→policy by version; readiness↔preflight key by incarnation/version; control layers→header/execution. Deployment and policy digest equality, READY/watchdog health, canonical role/fingerprint and temporal checks are operational guard predicates. External host approval is an administrative invariant, not a SQL relation. Therefore BINDING_CANNOT_REFERENCE_UNAPPROVED_INCARNATION=NO and READINESS_CANNOT_BECOME_READY_WITHOUT_VALID_BINDING=NO at the installed-constraint level against trusted ADMIN DML. Governance forbids unapproved operation; this does not promise hostile-admin protection. No READY change or negative ADMIN write was executed.

One permanent role/binding/slot including tombstones is normative. Embedded BYTEA has no global per-role unique index, and existing wrappers resolve a supplied binding, not a completed authenticated-role-only login lookup. Current cardinality is0. A future native lookup must decode all matching canonical assignments, require one valid current context, and reject ambiguity; taking the first match is forbidden. The admission roster must recognize a governed login even when its header is absent, with approved provenance independent of role-name conventions. R permits auditor reads of revoked/expired bindings; ACTIVE-only login semantics cannot be borrowed from M without resolving that difference. No separate binding_revision column exists; immutable schema/plan/fingerprint/surface/policy versions differ from mutable attempt generation.

The native login-event direction remains design-only. Server-derived authenticated identity and database/backend fields have pinned PostgreSQL source support from the previous review, but no current binding lookup, strong generation/receiver epoch, synchronous ACCEPT/DENY, governed handshake bound or connection fail-closed runtime PASS is asserted. All eleven negative binding cases and eleven prototype cases are explicitly NOT_RUN because conditional prerequisites failed. Historical self-pidfd/SCM_RIGHTS race closure remains preserved, without claiming a new restart/enrollment result.

Existing binding DATA provisioning requires no new database or service privilege. Native handler function/event registration and trusted receiver/epoch deployment remain explicit pending ADMIN configuration changes; do not report those prospective changes as NONE. The complete new-authority contract stays HOLD. No role, ACL, writer, fixture, policy, temporal value, migration or domain record changed. Authority/configuration fingerprints before and after are both `d3b57ed08d9ba09f2a3db25219f36f436b6d4d2c5d2f5eccc59ca38ca03ad90b`; the narrower historical role/ACL fingerprint remains `d697579bb78f8ecffbeb1407a100a2ef400bebd761967bfa6af8059c1379632c`. Data snapshots, all function definitions, constraints/triggers, defaults, memberships, ownership, migrations and tracked hashes match. Disposable stopped and temporary plaintext startup file erased; no password rotation or credential material capture.

Existing findings stay BLOCKER0/HIGH2/MEDIUM0/LOW0, H01 OPEN and watchdog deployment HIGH OPEN. Next technically determined gate: **G3F_4_BINDING_PROVISIONING_CONTRACT_DESIGN**. Define the independently governed host deployment/incarnation approval/marker and header-absent admission roster, cardinality and activation semantics within existing authority; identify the independently supplied original binding inputs; specify generation/ACK provenance and policy binding. Review that concrete contract before provisioning/native runtime qualification. This gate does not authorize a new writer, new privilege, fixture3, temporal change or full watchdog implementation.

```text
BINDING_MODEL_COMPLETE=NO
BINDING_HEADER_COUNT_BEFORE=0
IDENTITY_SLOT_COUNT_BEFORE=0
BINDING_PROVISIONING_PATH=EXISTING_GOVERNED_PATH
BINDING_PROVISIONING_AUTHORITY=TRUSTED_PLAN_BINDING_ADMIN_DIRECT_POSTGRES_CONTROL_DML
ROLE_SLOT_MAPPING_SOURCE=CANONICAL_REHEARSAL_ALLOCATION_ARTIFACT_NOT_ACTIVE_HEADER
CANONICAL_ROLE_SLOT_BINDING=HOLD_UNPROVISIONED
DEPLOYMENT_ID_SOURCE=EXISTING_NEGATIVE_TIMING_FIXTURE_NOT_CANONICALLY_APPROVED
DEPLOYMENT_ID=2430bd66-ee5b-49e9-aaf9-9dc1fbd9b547
INCARNATION_SOURCE=EXISTING_NEGATIVE_TIMING_FIXTURE_NOT_CANONICALLY_APPROVED
INCARNATION_ID=fa105a00-acf1-4ddf-846b-08096978637d
CANONICAL_INCARNATION_BINDING=HOLD_MISSING_INDEPENDENT_HOST_APPROVAL
READINESS_BINDING_RELATIONSHIP=FK_PLUS_OPERATIONAL_SEMANTICS_NOT_HOST_APPROVAL
NEW_DATABASE_AUTHORITY_REQUIRED=NO_FOR_EXISTING_BINDING_DATA_PATH
NEW_SERVICE_AUTHORITY_REQUIRED=NO_FOR_EXISTING_BINDING_DATA_PATH
REHEARSAL_DATA_PROVISIONING_REQUIRED=YES_CONDITIONAL_AUTHORIZATION_NOT_SATISFIED
BINDING_HEADER_COUNT_AFTER=0
IDENTITY_SLOT_COUNT_AFTER=0
NEGATIVE_BINDING_MATRIX=NOT_RUN_CANONICAL_PROVISIONING_PREREQUISITES_UNSATISFIED
AUTHORITY_FINGERPRINT_PRE=d3b57ed08d9ba09f2a3db25219f36f436b6d4d2c5d2f5eccc59ca38ca03ad90b
AUTHORITY_FINGERPRINT_POST=d3b57ed08d9ba09f2a3db25219f36f436b6d4d2c5d2f5eccc59ca38ca03ad90b
AUTHORITY_STATE_UNCHANGED=YES
LOGIN_HANDLER_BINDING_LOOKUP=HOLD_NOT_INSTANTIATED
SERVER_DERIVED_IDENTITY=SOURCE_DESIGN_ONLY_NOT_RUNTIME_PASS
ENROLLMENT_FAIL_CLOSED=HOLD_NO_RUNTIME_PROTOTYPE
ENTRYPOINT_AUTHORITY_DELTA=NONE_APPLIED
SERVICE_EXECUTE_DELTA=NONE
DATABASE_PRIVILEGE_DELTA=NONE
DEPLOYMENT_TRUST_DELTA=NONE_APPLIED_NATIVE_HANDLER_RECEIVER_CONFIGURATION_PENDING
NEW_AUTHORITY_CONTRACT=HOLD
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
WORKTREE=DIRTY_AUTHORIZED_22_FILES
NEXT_GATE=G3F_4_BINDING_PROVISIONING_CONTRACT_DESIGN
```
