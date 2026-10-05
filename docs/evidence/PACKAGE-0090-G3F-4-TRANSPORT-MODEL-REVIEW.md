# Package 0090 - governed watchdog and transport model review

STATUS: G3F.4 HOLD. H01 OPEN/HIGH. A separate required watchdog deployment gap is HIGH. No policy, production adapter, SQL authority, fixture or temporal bound changed.

DECISION: MODEL_C1 is proven for connection/snapshot placement, not eligible S01/Q or operational timing. Numeric-bound review cannot proceed. NEXT_GATE=G3F_4_WATCHDOG_DEPLOYMENT_CLOSURE.

The fetched local/remote baseline was 27103cfd2bfb5b33cec0017cf789a613497363db on checkpoint/package-0090-cloud-handoff; the worktree was clean before these diagnostic files. All baseline tracked files retain their byte hashes, including every historical HOLD report, V001-V043, ADR/SPEC, policy fixtures and production Kotlin sources.

The marker is public.offline_readiness.watchdog_checked_at/watchdog_healthy, with state controlling READY. V043 creates storage owned by flooow_offline_control_owner (NOLOGIN) and read guards; it contains no heartbeat writer function or watchdog UPDATE. Q is a NOLOGIN/read-only readiness capability, not a writer. Existing directly authenticated postgres ADMIN can perform bounded disposable diagnostic DML under the previously approved rehearsal administrative authority; no new authority was required. SPEC25 identifies exact postgres for administrative provisioning; it does not assign a production watchdog login or turn that provisioning into a implemented monitor.

ADR81/SPEC18 line245 require a trusted independent host/database watchdog targeting exact OID/incarnation, enforcing maximum transaction/idle durations through cancel/terminate, blocking claims/effect admission and triggering drain on failure. ADR133 and SPEC line274 leave packaging as implementation work. No executable watchdog was found in tracked application sources, compose, operations scripts or GitHub workflows. The compose PostgreSQL healthcheck only runs pg_isready. Out-of-process trust is intentional, but delivery of that component is unproven; classifying this package as MISSING/HIGH is appropriate. Actual unrelated external deployments remain UNKNOWN. Administrative timestamp emulation cannot close this gap or establish READY.

The actual compiled Kotlin GovernedSources.transaction and four distinct authenticated DataSources were used. Diagnostic DataSource/Connection delegates forward every call to the real PG driver and record timestamps; no mock/frozen JDBC execution or production edit. Configuration order is setAutoCommit(false), setTransactionIsolation(REPEATABLE_READ), setReadOnly(true). Existing postgres observer saw idle/xact_start NULL/backend_xmin NULL after configuration. Explicit BEGIN produced idle-in-transaction/xact_start but no backend_xmin. The first non-transaction-control SELECT established backend_xmin and an exported snapshot. Importing that exact snapshot in a third administrative session proved: A committed before snapshot is visible; B committed after it remains invisible; a new AUDITOR transaction sees B. Read-only AUDITOR xid is unassigned (NULL), not fabricated zero. Exact engine snapshot-acquisition timestamp is unavailable; SQL start/end and first SQL DB-clock upper bound are retained.

Normal S01-first transactions are recorded separately: driver BEGIN READ ONLY precedes the real S01 SELECT. Their nonexistent binding fails P0017 before heartbeat/Q. Population probes intentionally export a snapshot before S01; ADMIN imports it to read only non-secret marker/timestamp/xmin. AUDITOR receives no table grant or private data projection. This proves the same RR MVCC visibility mechanism, not a real S01 heartbeat predicate. All 5000 population S01 calls plus 10 S01-first probes denied safely.

1000 frozen observations and 1000 at each measurement-only 5/10/25/50ms fixed-delay cadence completed. The writer logs actual acknowledged commits, external sequences and tuple xmin without schema changes. Imported observer DB-clock age includes snapshot/export/import/query overhead; it must not be relabeled S01/Q health-check age. Groups were sequential, not randomized; statement logging and shared JVM/platform scheduling affect these descriptive measurements. Aggregate continuous statistics mix four cadences. Cadences are neither fixture values nor approved enforcement intervals.

| Diagnostic population | N | Visible age p99 us | p99.9 us | Max us | Connection max us | Pearson r |
|---|---:|---:|---:|---:|---:|---:|
| frozen | 1000 | 58754 | 107094 | 133112 | 113527.8 | 0.911218 |
| continuous_5ms | 1000 | 30565 | 57800 | 95862 | 115689.9 | 0.340285 |
| continuous_10ms | 1000 | 88879 | 119512 | 150652 | 139983.7 | 0.310274 |
| continuous_25ms | 1000 | 71899 | 95669 | 99312 | 126111.7 | 0.333787 |
| continuous_50ms | 1000 | 112483 | 134198 | 143735 | 163344.7 | 0.203459 |

Continuous combined N4000: max=150652, p99=93882, p99.9=122987 us (surrogate age only). Physical connection overall max=163344.7 us. Continuous connections >=50ms numbered 111; 111 observed a heartbeat tuple newer than the pre-connect acknowledged tuple. Selected examples and all raw records are retained. This directly refutes an invariably frozen-before-connect marker. Moderate positive within-cadence correlations remain (r=0.340285/0.310274/0.333787/0.203459); do not claim zero coupling or infer causality from correlation. Common scheduling/commit delays and work after snapshot can age the visible row even under MODEL_C1.

Eligible S01/Q: NOT_EXECUTABLE_WITH_CURRENT_FIXTURE. Binding header count is zero; fixture-1 remains the approved immutable policy with 100us health/interval actual and 200us maximum, NOT_READY/unhealthy and placeholder manifests. No independently enforcing watchdog exists in the reviewed package. The contract forbids readiness without it. No synthetic READY activation, new binding, manifest adoption, F2 installation or F3 creation was performed. All three requested real eligible timing maxima remain NULL/unmeasured, not zero. Source placement remains S01 clock6925/age6929, Q clock4990/age4995 before heavy live ACL/history; final Q clock6656 concerns receipt expiry/issuance, not another heartbeat-age check. These source points do not provide executed eligible timings.

Failure/drain: missing or NOT_READY/unhealthy/stale protected marker denies wrapper eligibility through existing readiness guards. A writer must explicitly update unhealthy/NOT_READY; a stopped writer merely lets its timestamp age. SQL freshness failures do not persist a drain or automatically release ownership. Mandatory external OID/incarnation monitor/cancel/terminate is absent, so its failure path was not executed. An old RR AUDITOR snapshot cannot see a newly committed health-state change; it can retain the old marker, while each fresh clock predicate can still expire its age. This is not new effect authority: S13/Q independently recheck readiness before claim, and READ_COMMITTED/VOLATILE mutation paths reload readiness/fresh clocks on entry and final/post-effect fences; failure rolls tentative effects back. Full exact function/line inventory is in WATCHDOG-VISIBILITY. Stale ownership/generation advance, recovery and recorded result remain governed ADMIN drain/reconciliation actions. No emergency cancel/drain implementation or positive-stage test is claimed.

PGSimpleDataSource physically connects per transaction. Correctness depends on identity/isolation/readiness checks, not pooling; connection startup occurs before the RR snapshot. Performance incurs repeated auth/setup; availability/jitter can affect connection, writer scheduling and later read age. Security currently benefits from separate slot authentication and fresh physical-session teardown. A purely operational pool needs no new database authority if four separate slot/deployment identities, incarnation eviction, transaction rollback/reset, read-only/isolation restoration, no cross-slot reuse and failure disposal are preserved. No pool was implemented or performance gain promised.

H01 PRIMARY_CAUSE=MULTIPLE_CAUSES summarizes demonstrated frozen-marker transport sensitivity, physical connection jitter and RR visibility limitations plus the independent deployment prerequisite gap; it does not identify the historical 428349us/08006 mechanisms. H01 remains OPEN. Separate G3F4-WATCHDOG-DEPLOYMENT-GAP is HIGH because safe operation requires an undelivered component; it does not double count the numeric qualification gap. Counts now BLOCKER0/HIGH2/MEDIUM0/LOW0.

JDBC_08006_ROOT_CAUSE=UNKNOWN. No 08006 was observed here; historical evidence is unchanged. 08006_AS_BOUNDARY_BLOCKER=NO_WITH_FAIL_CLOSED_RECOVERY_REQUIREMENT: GovernedSources propagates the primary failure, attempts rollback without masking it and closes the connection. A failed audit yields no new receipt. Mutation COMMIT uncertainty requires durable reconciliation and existing recovery/drain rules; disconnect never implies rollback confirmation, effect absence, ownership release or permission to replay. This is a handling classification, not executed fault-injection certification.

Password-only authorization was reused on exactly five existing roles. Identity/attributes/memberships/ownership/ACL/defaults/policies/migration state pre/post/end remain equal. Fingerprint=d697579bb78f8ecffbeb1407a100a2ef400bebd761967bfa6af8059c1379632c. No credential/verifier value was queried or preserved. Complete non-secret snapshots and baseline hashes are retained losslessly in the authority/cleanup record. Original readiness contents and logging settings were restored. Plaintext files erased; exact disposable container stopped. No protected database/volume or production secret was used.

Scope: two diagnostic tools plus the four required new evidence artifacts. Baseline production behavior/history stays unchanged. Next technically determined action is bounded watchdog deployment closure under the existing OID/incarnation/fail-closed contract; this gate creates neither that component nor new temporal numbers. Numeric review follows only after eligible S01/Q placement and watchdog prerequisites are proven.

PostgreSQL primary references: [Repeatable Read snapshot semantics](https://www.postgresql.org/docs/18/transaction-iso.html#XACT-REPEATABLE-READ), [snapshot export/import](https://www.postgresql.org/docs/18/functions-admin.html#FUNCTIONS-SNAPSHOT-SYNCHRONIZATION). Executed PG18.4 evidence supports those semantics locally.

Exact requested return fields (checkpoint HEAD/remote/clean proof is supplied after committing this report):

```text
WATCHDOG_MARKER_RELATION=public.offline_readiness
WATCHDOG_MARKER_COLUMNS=['watchdog_checked_at', 'watchdog_healthy', 'state']
WATCHDOG_WRITER_ROLE=postgres (approved disposable ADMIN); production watchdog login binding not specified
WATCHDOG_WRITER_FUNCTION=NONE; direct administrative UPDATE, not Q or a service wrapper
WATCHDOG_WRITER_PRIVILEGE=Existing trusted postgres administrative DML; control-owner table ownership is NOLOGIN; no service write capability
WATCHDOG_WRITER_EXISTS_IN_SQL=NO_DEDICATED_WRITER; STORAGE_AND_READ_GUARDS_EXIST
WATCHDOG_WRITER_EXISTS_IN_APPLICATION=NO
WATCHDOG_WRITER_EXISTS_IN_DEPLOYMENT_PACKAGE=NO
WATCHDOG_DEPLOYMENT_IMPLEMENTATION=MISSING
REHEARSAL_WATCHDOG_NEW_AUTHORITY_REQUIRED=NO
AUDITOR_SNAPSHOT_ESTABLISHMENT_POINT=FIRST_NON_TRANSACTION_CONTROL_SQL_STATEMENT; S01-first query in normal launcher
FROZEN_VISIBLE_AGE_MAX_US=133112.0
CONTINUOUS_WATCHDOG_VISIBLE_AGE_MAX_US=150652.0
CONTINUOUS_WATCHDOG_VISIBLE_AGE_P99_US=93882.0
CONTINUOUS_WATCHDOG_VISIBLE_AGE_P999_US=122987.0
CONNECTION_MAX_US=163344.7
REAL_S01_FIRST_CHECK_AGE_MAX_US=NOT_EXECUTABLE_WITH_CURRENT_FIXTURE
REAL_Q_CHECK_AGE_MAX_US=NOT_EXECUTABLE_WITH_CURRENT_FIXTURE
REAL_S01_TOTAL_MAX_US=NOT_EXECUTABLE_WITH_CURRENT_FIXTURE
RR_VISIBILITY_BEFORE_SNAPSHOT=VISIBLE
RR_VISIBILITY_AFTER_SNAPSHOT=NOT_VISIBLE_IN_EXISTING_TRANSACTION
RR_VISIBILITY_NEW_TRANSACTION=VISIBLE
CONNECT_LATENCY_CORRELATES_WITH_VISIBLE_AGE_FROZEN=YES_OBSERVED; Pearson r=0.9112177468631358
CONNECT_LATENCY_CORRELATES_WITH_VISIBLE_AGE_CONTINUOUS=YES_OBSERVED_WEAKER_WITHIN_EACH_CADENCE; not proof that startup fixes marker or causal attribution
QUALIFIED_TRANSPORT_MODEL=MODEL_C1
TRANSPORT_QUALIFICATION_SCOPE=Snapshot mechanism only; eligible S01/Q and operational watchdog unqualified
POOL_NEW_AUTHORITY_REQUIRED=NO_FOR_OPERATIONAL_PER_SLOT_POOL_WITH_UNCHANGED_SESSION_IDENTITY_AND_ISOLATION
WATCHDOG_FAILURE_ENFORCEMENT=SQL readiness/health/age guards exist; external OID/incarnation monitor and cancel/terminate enforcement missing from reviewed package
WATCHDOG_DRAIN_SEMANTICS=Required independent cancel/drain plus governed ADMIN stale/abort/recovery recording; heartbeat expiry does not persist drain or release ownership
H01_PRIMARY_CAUSE=MULTIPLE_CAUSES
H01_CAN_PROCEED_TO_NUMERIC_BOUND_REVIEW=NO
G3F4_H01=OPEN
JDBC_08006_ROOT_CAUSE=UNKNOWN
08006_AS_BOUNDARY_BLOCKER=NO_WITH_FAIL_CLOSED_RECOVERY_REQUIREMENT
FIXTURE_1_MUTATED=NO
FIXTURE_2_INSTALLED=NO
FIXTURE_3_CREATED=NO
BLOCKER_COUNT=0
HIGH_COUNT=2
MEDIUM_COUNT=0
LOW_COUNT=0
PROTECTED_DATABASE_CONNECTION=NO
PROTECTED_VOLUME_MOUNT=NO
PRODUCTION_SECRET_USE=NO
PASSWORD_ROTATION=PASS
ROTATED_ROLE_COUNT=5
ROLE_STATE_PRE_POST_EQUAL=YES
PASSWORD_ROTATION_SCOPE=EXACT_AUTHORIZED_FIVE_ROLES
ROLE_IDENTITY_UNCHANGED=YES
ROLE_ATTRIBUTES_UNCHANGED=YES
ROLE_MEMBERSHIPS_UNCHANGED=YES
OBJECT_OWNERSHIP_UNCHANGED=YES
ACL_UNCHANGED=YES
DEFAULT_ACL_UNCHANGED=YES
POLICY_UNCHANGED=YES
MIGRATION_STATE_UNCHANGED=YES
NON_SECRET_AUTHORITY_FINGERPRINT_PRE=d697579bb78f8ecffbeb1407a100a2ef400bebd761967bfa6af8059c1379632c
NON_SECRET_AUTHORITY_FINGERPRINT_POST=d697579bb78f8ecffbeb1407a100a2ef400bebd761967bfa6af8059c1379632c
PLAINTEXT_CREDENTIAL_FILES_ERASED=YES
DISPOSABLE_CONTAINER_STOPPED=YES
NEXT_GATE=G3F_4_WATCHDOG_DEPLOYMENT_CLOSURE
```
