# Authorized TEST activation, native-health mechanisms and S04 gate

Status: PARTIAL / FIRST S04 POSITIVE BLOCKED. The explicit user decision is
adopted, external TEST audit and policy activation are proven, and seven native
work mechanisms were independently observed. The native freshness gate failed
in both final disposable targets. No READY, header/original registration or
S04 invocation was manufactured. This does not declare the requested primary
runtime goal achieved.

Branch: checkpoint/package-0090-cloud-handoff. Baseline local/origin:
caef8dd8a964a9eb173deda40f85449b43b970dd. Protected refs were verified read-only.
Authority adoption commit: a85531e. Subsequent implementation/evidence commits
are recorded in the final response and Git history.

## Adopted decision

DECISION_ID=TEST_ONLY/0090/activation-and-native-health/s04/v1.
ADR-0090 and SPEC-0090 now record APPROVED_TEST_ONLY. Exact user authority is
retained in USER-AUTHORIZATION.txt and bound by SHA256 in
[accepted-test-decision.json](package-0090-authorized-test-activation-native-health-s04/accepted-test-decision.json).
The earlier proposed amendment remains historical; this accepted decision
supersedes its authority hold within the explicitly approved TEST scope.

Phase2 expressly authorizes deterministic identifiers. UUIDv5 uses the explicit
https://flooow.test/qualification/package0090 TEST namespace, accepted decision
and typed approval/change/actor suffixes, not postgres ownership, commit
authorship, service OIDs, production identities or VECTOR_1 business UUIDs.

approval_id=c72353ad-6d9a-52eb-95d9-aa98d95cc06d.
change_id=ddb3edc5-03be-5c85-829e-aa7ce643d6a3.
approving_actor=TEST_ONLY_USER_APPROVAL/4c02e2a6-ab69-5395-85a1-7542654e9977.
This is a qualification provenance identity; it is not a new production or
operational principal. The accepted source/hash, policy version/digest and
recipe identity are frozen in test-identities.json.

## Earned activation and external audit proof

The trusted qualification writer creates an external audit file with O_EXCL,
writes only with O_APPEND, fsyncs each canonical JSON record, and never rewrites
prior records. It is outside the container mounts and Package operational
tables/APIs. Each record binds sequence, previous_hash, SHA256 record_hash,
decision, approval/change/actor, deployment/incarnation, exact policy/version/
canonical bytes/digest, effective_from, activation recipe and transaction.
PREPARED precedes policy INSERT; COMMITTED follows acknowledged COMMIT and an
independent DB read. Host audit timestamps and the reconciled database outcome
timestamp are retained. Complete chain, exact context and trusted terminal hash
are validated before eligibility could be consumed.

The authoritative non-secret store is retained in a private qualification Temp
directory; exact exported proof copies and trusted tips are retained in Git.
The collector rereads the authoritative external store and requires exact
equality to the exports. This is logical append-only/tamper-evident TEST audit,
not a production WORM/HSM storage claim. A caller-supplied replacement tip is
never an independent trust anchor. Operational service roles cannot access the
external store. A malicious trusted host/root is outside this qualification
trust model.

The ADMIN registration transaction captures pg_catalog.clock_timestamp() once
in a MATERIALIZED CTE, casts to finite timestamptz(6), and obtains its transaction
identity. Exact signed integer epoch microseconds are independently reconstructed
without floating conversion and round-tripped in PostgreSQL. Offset=0.
The approved29-field fixture-1 bytes/digest are unchanged. The loader inserts
the captured instant as immutable effective_from; after audit/commit
reconciliation, ACTIVE is derived from exact metadata and DB clock reaching it.
There is no state='ACTIVE' write, GUC/default or historical epoch activation.

Eighteen activation assertions cover missing/wrong approval/change/actor/
decision/version/digest, valid registration, exact replay, SQL duplicate23505,
future mismatch, NULL metadata and divergent replay. Administrative approval
and activation-metadata denials are enforced by the trusted TEST loader, not
claimed as additional canonical SQL constraints. Exact replay reconciles the
original activation instant and audit; it does not recapture time or upsert.

Twelve runtime audit assertions cover the eleven requested attacks plus valid
committed chain validation. Six unit/mutation tests additionally prove actual
disk-chain validation, missing reconciliation, mutation, whole-chain rehash
against the original trusted tip, validly hashed UNKNOWN rejection and immutable
approval context. Missing/uncertain audit/commit evidence denies eligibility
even if a policy row physically committed. No distributed transaction atomicity
between PostgreSQL and the external store is claimed.

TEST_POLICY_ACTIVATION_PROVEN=YES.
TEST_ADMIN_AUDIT_CONTRACT_READY=YES.
TEST_ADMIN_AUDIT_TAMPER_EVIDENT=YES.
TEST_ACTIVATION_REPLAY_PROVEN=YES.

## Native implementation and actual observations

The C harness is built inside the pinned disposable Linux image with OpenSSL.
HOST_PLATFORM is the explicit trusted Linux bootstrap process; HEALTH_GUARD is
a separate child process. Actual boot ID, PID namespace, container identity,
process start ticks, pidfds, image/native/harness hashes and target context are
recorded. This does not use the Windows host's PID as participant identity.
The postmaster is the actual PostgreSQL process (PID1 in these containers),
with a separate catalog-probe helper; helper PID is not substituted for the
postmaster anchor.

An external qualification generation ledger allocates random fresh generations
and publishes enrollment/start identity before work ACK. Six other named TEST
component actors are actual independent Linux processes. UNIX SOCK_SEQPACKET
channels carry kernel SCM_CREDENTIALS and SCM_RIGHTS live pidfds; the guard
checks sender PID/UID, expected generation, counter, challenge and catalog.
The producer precedes consumer; other actors do work in parallel. Generation
allocation/enrollment mechanisms are observed, not production generation
lifecycle or complete replacement/replay closure.

| Participant | Executed mechanism and independent witness |
|---|---|
| POSTMASTER | Actual server-start/version, complete42-row history and four role projections; separate guard query matches catalog digest and anchors actual postmaster |
| SUPERVISOR | Actual child spawn; guard independently reads child's PID/parent/start identity and matches its digest |
| RECEIVER | Generation/challenge/catalog-bound enrollment decision digest independently recomputed by guard |
| CENSUS_OBSERVER | Actual DB catalog/history/role reconciliation compared against the guard's separate query |
| APPROVAL_PRODUCER | Fresh in-memory Ed25519 signature of the target-context challenge; public signature independently verified |
| APPROVAL_CONSUMER | Separate process verifies exact producer signature/public key; guard verifies and matches both original byte sequences |
| ENFORCEMENT_WORKER | Actual target child SIGSTOP and waitpid stop acknowledgment; guard independently reads target state T and anchored identity |

These are seven demonstrated work mechanisms. They do not by themselves close
every normative participant requirement. The producer/consumer challenge
publication is not a full canonical V041 original SignedApprovalAttestation
lineage proof. Complete replacement/invalidation/replay/observer-loss and the
seventeen native sibling attacks remain unqualified. No JSON healthy flag,
alive process or heartbeat alone is used to create readiness. The C output's
identity_and_work_complete label refers only to the implemented mechanism
checks, not the complete normative contract.

## Measured freshness blocker

The unchanged fixture policy has watchdog actual100us and maximum200us. S04
consumes the actual100us, not the maximum. The TEST harness conservatively
applies that100us to original BOOTTIME work emissions at the independent guard
catalog observation. It adopts no different participant window.

Final run4 ages:29.209511–72.883114ms. Final run5 ages:29.143401–65.850207ms.
All fourteen participant observations exceeded0.1ms. These ages are measured
before remaining final verification; a later promotion cannot make them
younger. Every scoped work assertion passed, but FIRST_PATH_NATIVE_HEALTH_READY
remains NO. No original emission timestamp was renewed or replaced with a
later guard timestamp to obtain eligibility.

This proves the implemented parallel harness does not meet the approved
boundary. It does not prove every possible implementation is infeasible.
No alternate timing, cached/self-reported health, production heartbeat or
manually inserted READY was substituted. A valid fresh control is absent, so
native/readiness/S04 sibling campaigns are explicitly NOT_EXECUTED rather than
counting denials from an already invalid control as complete attack proof.

The trusted activation path is now demonstrated; the old absence-of-authority
blockers are superseded. The remaining scoped blocker is the complete native
health gate, including measured freshness and pending full-contract lifecycle/
original-publication/negative closure. HIGH/MEDIUM/LOW counts remain UNKNOWN
because S04 runtime/security review has not executed. This makes no global
Package severity claim.

## Reproduction, interlocks and tests

Accepted final runs are run4 and run5. Each starts with fresh UUID-labeled
container/network/volume, loopback-only endpoint, pinned image, actual Flyway
V001-V042, exact separately derived qualification body, independently expected
1040-column ACL set,70 function contexts and four direct authentic LOGIN
sessions. Both have different deployment/incarnation identities and identical
final recipe/native binary hashes and semantic assertion cohorts. Both
destroyed all owned Docker resources; temporary connection secrets were erased.

Each run has132 passing assertions and no runner error. Six distinct audit unit
tests passed normally and with Python -O; repeats count once. Total distinct
assertions=138, not264 plus repeated units. Classification:18 activation,
18 audit (including6 units),8 native mechanism/stale-denial,2 readiness
interlocks,9 retained input prerequisites,4 direct LOGIN and79 ACL/catalog
context assertions. The9 retained-row checks are header/attestation
prerequisites, not header/original registration tests. Canonical slot binding,
S04 positive/negative/search-path and runtime semantic tests=0.

Readiness/header/original counts remained0/0/0. Audit LOGIN itself is authentic;
its immutable header slot registration is not proven. ACTIVE_FIXTURE_PRECHECK
is FAIL_NATIVE_FRESHNESS_AND_INCOMPLETE_HEALTH_CONTRACT. S04 was not invoked,
and no actual history rows or runtime semantic bindings are claimed.
The existing independent42-row expectation remains frozen. S04 retains45 call
sites and33 static unvalidated groups, all UNBOUND. Successor global candidates
remain818+33=851, bound0; old818 artifacts are unchanged. NULL/consumer and full
effective S04 ACL closure remain NO.

Development attempts remain separate and preserved: run1 failed Docker Desktop
mount-path interpretation after93 checks; run2 proved activation but failed a
native source/context interface during development after123 checks; run3 passed
132 partial assertions but is superseded by the final activation-metadata/
reconciliation implementation. All three cleaned their owned resources. They
are not silently counted as final accepted campaigns or erased.

ACTIVE_LOADER_REPRODUCIBLE=NO: activation and the stale-denial interlock reproduce,
but an ACTIVE complete first-positive loader has not been achieved.

## Gates, integrity and next action

G1/G2/G5/G6/G8=PARTIAL. G3=PARTIAL (work mechanisms only), G4=PARTIAL
(activation only), G7=PARTIAL (TEST administrative provenance only).
ACTIVE_FIXTURE_FOUNDATION_READY=NO; FIRST_POSITIVE_FIXTURE_READY=NO;
FULL_FIXTURE_READY=NO. B01-B08 remain OPEN; no first positive or global closure
is claimed.

Canonical V043 Git-LF SHA256 remains
b0ea86b6ba355fdf25fe09836bd4b75e4a4a2ad88ab7ef0e4724ca0d5a013e7d.
Fence present; canonical V043 unmodified/unexecuted. V001-V042 remain unchanged.
Main77d482c97a663a527dcacc85036c7577dfc92782,
Room22181b5d821e343658928e6feaa06b96838757e2 and global-commerce
27019d7b3093b7a7d9aeb67d0c099756b13e005a remain unchanged locally/remotely.
No protected worktree mutation, shared DB/production contact, production
policy/key/credentials or field authority. EXECUTION_AUTHORITY=BLOCKED;
RECOVERY_AUTHORITY=BLOCKED; ROOM_OPERATIONAL=NO.

NEXT: qualify a complete native lifecycle/functional observation protocol that
can meet the unchanged100us promotion boundary, using controlled latency and
valid-control attack evidence, before legitimate readiness/header/S04. If that
boundary cannot be met, record measured feasibility and seek a separately
governed TEST timing amendment; do not change values in this tranche.
NEXT_EXECUTED=NO. The remaining17 wrappers are not attempted.
