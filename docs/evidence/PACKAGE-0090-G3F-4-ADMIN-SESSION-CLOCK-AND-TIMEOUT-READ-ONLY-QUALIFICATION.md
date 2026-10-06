# Package 0090 G3F.4 — ADMIN session clock and timeout read-only qualification

**VERDICT: BLOCKED at runtime-start/access authority boundary. Stop review and evidence are internally complete; runtime qualification was not executed. G3F.4 HOLD; inherited B0/H5/M0/L0 unchanged; this gate adds B0/H0/M0/L0.**

The eligible Package 0090 PostgreSQL rehearsal is stopped. No clear current authorization was established to restart it for this gate under NO DATABASE MUTATION. The task explicitly requires stopping when startup authority is unclear. No DB connection, SQL, BEGIN, ROLLBACK, timestamp sample, timeout read, acquisition measurement or 60-second transaction was attempted. Metrics are ABSENT/NOT_OBSERVED, not zero latency, zero backward events or successful survival. Static source/document semantics and nonsecret Docker metadata are not runtime qualification.

## Baseline, scope and authority decision

Branch `checkpoint/package-0090-cloud-handoff`; verified local HEAD and live origin HEAD `29022c522d4a9441d82252488f3cb14f1cc9d2c1`; initial worktree clean. Captured SHA256 for all 1259 tracked files, read/hash inventoried 168 previous Package 0090 evidence files, and read the source seams listed below. This gate creates exactly this one new evidence Markdown. All prior temporal contracts, signing review, TC-R01 and historical JSON remain byte-identical. No contradiction with the frozen [T0,T0+60000000us) contract was found. No implementation or next gate is started.

Current request attachment SHA256 `2b66d2dd367fb9d44d8b183712fa6a69ee5e78af4c8c50d7a4b24de922531841`. Section 2 states: “If not clearly authorized: STOP and report.” Section 19 independently permits preserving an internally complete review even when qualification does not pass. Stopping runtime operations therefore does not prevent recording this negative result and checkpoint-only publication.

Prior timing/08006 request SHA256 `1c7e53ac5610ec8f91b24a6ab72e672748566749f0aa863fd06f622ddd1eaeb4` explicitly ends with stopping the disposable container and erasing diagnostic credentials. The session authorization amendment limited password-only rotation to restoring authentication for that previously prepared diagnostic and also required final shutdown/credential erasure. Those scoped completed operations establish container provenance, not blanket startup or fresh authentication authority for this gate. The immediately preceding signing operational review also requires independently available authorized runtime access before this next qualification and forbids treating erased credentials or stopped state as silently resolved.

Decision: no docker start/exec/compose up, no PostgreSQL startup, no ALTER ROLE or credential restoration, no recovered plaintext credential and no alternate-target connection. A DB startup is not a read-only SQL query and cannot be represented as proven non-mutating persistence behavior. This is an authority uncertainty under the user’s explicit stop clause, not an automatic approval rejection or a SKILL requirement. No permission menu is needed to finish the authorized evidence. Other Docker PostgreSQL instances were discovered; a running task-0160 database is outside this gate’s approved project identity. It was not inspected beyond public container-list metadata, contacted, borrowed or modified. Existing authorization to inspect the approved rehearsal does not authorize choosing a foreign database to obtain measurements.

The separate rehearsal-deployment approval request also authorized a disposable PostgreSQL restart for its section 20 process-lifetime/invalidation tests, followed by section 26 shutdown. That is an explicitly bounded previous test sequence. Its frozen approval artifact describes normal-restart identity semantics (same host incarnation/new process enrollment); those semantics do not themselves grant a new diagnostic startup or eliminate current authorization uncertainty. Neither prior restart instruction nor approval is treated as revoked; its original scope is preserved without silently broadening it to this new qualification. The stopped target remains eligible provenance, not a currently available session.

## Nonsecret runtime discovery — stopped state only

| FIELD | OBSERVATION | EVIDENCE STRENGTH |
| --- | --- | --- |
| DB_INSTANCE | flooow-0090-g3f4-cc2941797db3-postgres | CURRENT Docker identity; not a connected DB identity |
| PROJECT | flooow-0090-g3f4-cc2941797db3 | CURRENT approved project label |
| STATE | exited; running=False; paused=False | CURRENT Docker observation |
| IMAGE | sha256:07fc165de5bb569d822460e2df645c5489f99220fc2cb16c86596d39db394561 | CURRENT exact expected image pin |
| DATA_VOLUME | flooow-0090-g3f4-cc2941797db3-data | CURRENT mount name; no volume content opened |
| DB_HOST | 127.0.0.1 is the approved historical JDBC boundary; live endpoint NOT_AVAILABLE | Not a fresh reachable host proof |
| DB_PORT | UNKNOWN_LIVE_ENDPOINT; internal target 5432/tcp is container config only | Do not reuse historical random published port |
| CONFIGURED_PORT_BINDINGS | {"5432/tcp":[{"HostIp":"127.0.0.1","HostPort":""}]} | CURRENT config, not active routing |
| ACTIVE_PORTS | {} | CURRENT stopped network metadata; not a listening endpoint |
| DB_NAME | g3f4 (HISTORICAL_ONLY) | Previous rehearsal report; no current_database query |
| DB_VERSION | 18.4 (HISTORICAL_ONLY) | Previous server query/image provenance; no current version query |
| DATABASE_OID / SYSTEM_IDENTIFIER | 16384 / 7693118332665065516 (HISTORICAL_ONLY) | Prior frozen evidence; no live match claimed |
| CONNECTION_PATH | historical localhost Docker-published JDBC, physical PGSimpleDataSource seam | Future final ADMIN launch route UNKNOWN |
| POOL_OR_PROXY | no constructed pool in inspected PGSimpleDataSource path; external final ADMIN wrapper/proxy UNKNOWN | Source evidence only |
| SESSION_REUSE | UNKNOWN_RUNTIME | No acquired connection |
| TRANSACTION_PINNING | UNPROVEN_RUNTIME | One physical connection design alone is not selected-path trace |
| STARTUP_PASSWORD_FILE_PRESENT | False | Only known prior pathname existence tested; contents never read |
| AUTHENTICATION_ROUTE | UNQUALIFIED_FOR_CURRENT_GATE | Absent prior plaintext does not prove every possible local/auth route impossible; no alternate auth bypass tried |

Only name/state/image/project/ports/mount metadata was requested from Docker inspect. Config.Env, password values/verifiers, protected row material and volume contents were not read. SHA256 of the retained filtered metadata is recorded in private validation provenance; no full Docker inspect dump is captured. Docker ps -a was discovery only; a nearby running PostgreSQL is not canonical authority.

## Session identity and transaction observations

| REQUIRED READ-ONLY VALUE / PROPERTY | CURRENT RESULT |
| --- | --- |
| pg_backend_pid() | NOT_OBSERVED; zero SQL calls |
| current_database() | NOT_OBSERVED; zero SQL calls |
| current_user | NOT_OBSERVED; zero SQL calls |
| session_user | NOT_OBSERVED; zero SQL calls |
| inet_server_addr() | NOT_OBSERVED; zero SQL calls |
| inet_server_port() | NOT_OBSERVED; zero SQL calls |
| transaction_isolation | NOT_OBSERVED; zero SQL calls |
| transaction_read_only | NOT_OBSERVED; zero SQL calls |
| application_name | NOT_OBSERVED; zero SQL calls |
| transaction_timestamp() | NOT_OBSERVED; zero SQL calls |
| statement_timestamp() | NOT_OBSERVED; zero SQL calls |
| clock_timestamp() | NOT_OBSERVED; zero SQL calls |
| CURRENT_TIMESTAMP | NOT_OBSERVED; zero SQL calls |
| now() | NOT_OBSERVED; zero SQL calls |
| T0_FIXED_WITHIN_TRANSACTION | NOT_OBSERVED; zero SQL calls |
| FRESH_DB_CLOCK_ADVANCES | NOT_OBSERVED; zero SQL calls |
| SAME_BACKEND_SESSION | NOT_OBSERVED; zero SQL calls |
| microsecond round-trip precision | NOT_OBSERVED; zero SQL calls |
| READ_ONLY_60S_TRANSACTION_SURVIVES | NOT_OBSERVED; zero SQL calls |

No test transaction exists to rollback. ROLLBACK_EXECUTED=NO; DATABASE_MUTATION=NO follows from zero DB access, not from a claim that rollback was successfully verified. A live-session identity, stable backend, same transaction and sampled fixed T0 remain required future evidence. No transaction/XID/ceremony identity allocation was invoked.

## Timestamp contract — documentation only

PostgreSQL documents transaction_timestamp(), CURRENT_TIMESTAMP and now() as transaction-start time; statement_timestamp() as statement-start time; clock_timestamp() as actual current time, which can vary within a statement. T0 remains the original server transaction opening; fresh eligibility cannot use transaction-start or client wall time. [PostgreSQL 18 date/time semantics](https://www.postgresql.org/docs/18/functions-datetime.html).

TRANSACTION_TIMESTAMP_SEMANTICS=DOCUMENTED_NOT_RUNTIME_OBSERVED; FRESH_CLOCK_SEMANTICS=DOCUMENTED_NOT_RUNTIME_OBSERVED. Server start precedes any post-opening lock wait and subsequent T0 read; repeated fixed transaction_timestamp is not clock continuity. UTC microsecond transport must preserve exact values, not round/replace the signed endpoints. Current PRECISION_OBSERVED=NOT_OBSERVED. No sample-derived clock discipline, NTP bound, hidden-backwards-step exclusion or universal monotonicity is inferred. Even successful future observation would yield CLOCK_CONTINUITY_UNIVERSALLY_PROVEN=NO.

## Actual timeout inventory and 60-second compatibility

PostgreSQL distinguishes per-command statement_timeout, per-lock-wait lock_timeout, idle open-transaction timeout and whole transaction_timeout; zero disables these limits. A transaction limit can take precedence over longer statement/idle limits. Effective session settings are needed; documented defaults do not fill missing observations. [PostgreSQL 18 client settings](https://www.postgresql.org/docs/18/runtime-config-client.html).

pgJDBC exposes connection, socket/read and cancellation communication timeouts. Driver transport timeout or an exception does not prove an unknown COMMIT was absent. Repository properties must be distinguished from actual connection URL/overrides. [pgJDBC connection properties](https://jdbc.postgresql.org/documentation/use/).

| SETTING | EXACT LIVE VALUE | REPOSITORY / HISTORICAL SCOPE | 60S CLASS | INTERACTION |
| --- | --- | --- | --- | --- |
| statement_timeout | NOT_OBSERVED | No selected ADMIN effective setting | UNKNOWN | May cancel a clock/validation/write command before window end; cancellation/outcome classification still needed |
| lock_timeout | NOT_OBSERVED | No selected ADMIN effective setting | UNKNOWN | Per-wait bound does not bound aggregate canonical lock delay after T0 |
| idle_in_transaction_session_timeout | NOT_OBSERVED | No selected ADMIN effective setting | UNKNOWN | Future local key/SIGN/JCA can idle a server transaction and lose the session |
| transaction_timeout | NOT_OBSERVED | PG18 source supports it; actual configured value unread | UNKNOWN | Finite value below/near60s can terminate whole T_REG; cannot assume permitted lifetime |
| tcp_keepalives_idle | NOT_OBSERVED | No current pg_settings query | UNKNOWN | Connection failure detection is not eligibility or commit-outcome proof |
| tcp_keepalives_interval | NOT_OBSERVED | No current pg_settings query | UNKNOWN | Unqualified detection delay |
| tcp_keepalives_count | NOT_OBSERVED | No current pg_settings query | UNKNOWN | Unqualified detection behavior |
| tcp_user_timeout / client_connection_check_interval | NOT_OBSERVED | Support/value/platform relevance unread | UNKNOWN | Do not infer prompt disconnect detection |
| pool acquisition timeout | UNKNOWN | PGSimpleDataSource has no constructed pool in source; future external wrapper UNKNOWN | UNKNOWN | An external pool could wait/recycle; no finite bound established |
| application connection timeout | UNKNOWN | Prior transport-review harness connectTimeout=5s only | UNKNOWN | Not final ADMIN config; do not apply test URL values |
| application socket/read timeout | UNKNOWN | Prior transport-review harness socketTimeout=10s only | UNKNOWN | Not final ADMIN config; can lose response while server outcome persists |
| application transaction timeout | UNKNOWN | No observed final ADMIN launch config or composer | UNKNOWN | Unknown is not disabled/zero |
| application command timeout | UNKNOWN | No observed final ADMIN statement timeout setting | UNKNOWN | Guard RTT bound and cancellation coverage absent |

TIMEOUT_COMPATIBILITY=UNKNOWN. None is classified SAFE/CONDITIONALLY_SAFE/CONFLICT without its effective selected-session value and semantics. Observed zero server limits would mean no cancellation deadline, not safe bounded latency. A value below 60s can still be conditionally compatible with a proven shorter critical path, but that shorter-path budget is absent. Transaction survival for 61s would only qualify an observed read-only lifetime, not writable locks, WAL, crypto pauses, deterministic commit margin or complete ceremony.

## Source continuity, clock use and supervision inputs

PostgresDataSources.create constructs PGSimpleDataSource with supplied URL/user/password. PostgresConfiguration is declared in PostgresInventoryRiskAssessmentJournal.kt, not a separate configuration file. No actual future ADMIN URL or authentication secret was accessed. PostgresApprovalGovernance.transact uses one connection per individual append and commits that append; it is not the chosen final 11-row same-T_REG composer. GovernedSources.transaction confines one slot operation to its connection and rolls back AUDITOR, but its four service-role path does not prove ADMIN continuity. A misleading source comment calling these “pools” does not make the constructed PGSimpleDataSource a pool. Future external proxy/session replacement is UNKNOWN.

| PROPERTY | CURRENT CLASSIFICATION | FAIL-CLOSED REQUIREMENT |
| --- | --- | --- |
| TRANSACTION_SESSION_PINNING | UNPROVEN_RUNTIME | same approved instance/physical session and one server transaction through all phases |
| BACKEND_CAN_CHANGE_MID_TRANSACTION | UNKNOWN_SELECTED_RUNTIME | deny any unexpected backend/session change; never infer transparent continuation |
| CONNECTION_LOSS_BEHAVIOR | contract denies mutable continuation; actual operational behavior UNQUALIFIED | no automatic reacquisition/new T0; possible durable result -> existing query-first |
| POOL_ACQUISITION_BEHAVIOR | physical DataSource source only; external pool UNKNOWN | do not replace live T_REG to escape acquisition/recycle delay |
| RESTART / FAILOVER / SESSION_TERMINATION | UNQUALIFIED; no destructive fault injection | loss of authoritative time or original custody -> BLOCK incomplete mutable resume |
| QUERY_TIMEOUT | effective value/behavior UNKNOWN | failed/late guard cannot certify eligibility; no application clock fallback |

Targeted source searches for System.currentTimeMillis, Instant.now, Clock.system* and LocalDateTime.now found one production command-authority launcher Instant.now at line190, used for S15 delivery_observed_at (delivery acknowledgment observation). It is not the selected ADMIN T0/fresh-eligibility source. Prior transport-review Instant.now calls label telemetry; System.nanoTime measures diagnostics. The inspected codec/governance/connection seams do not establish an executing final ADMIN signer path. Therefore APP_CLOCK_IN_AUTHORITY_PATH=UNKNOWN, not YES from an unrelated delivery field and not NO from absence of the final implementation. No unrelated application clock was changed. No fallback is authorized.

| SUPERVISION INPUT | CURRENT AVAILABILITY | MISSING PROOF |
| --- | --- | --- |
| backend PID / server identity | source/SQL interface exists; not captured live | approved current session identity and stable sample trace |
| transaction age / T0 | DB timestamp interface documented; not read | actual original-opening instant and same-transaction samples |
| fresh DB clock / remaining window | documented queryable while connected; not read | observed fresh samples, exact microsecond transport, no stale guard admission |
| current phase / original custody | prior design only | executing final ADMIN phase and owner instrumentation |
| connection state | Docker stopped state observed; no JDBC state | actual JDBC session, discontinuity signaling and reconnect denial |
| timeout state | repository/static properties only | effective pg_settings/session override and application transport inventory |
| independent stall/clock/pause observation | existing watchdog contract remains OPEN | actual approved signer/host coverage without whitelist widening |

SUPERVISION_INPUTS_AVAILABLE=STOPPED_CONTAINER_METADATA_AND_DOCUMENTED_SOURCE_INTERFACES_ONLY. SUPERVISION_INPUTS_MISSING=LIVE_BACKEND_T0_DB_CLOCK_REMAINING_WINDOW_PHASE_CUSTODY_CONNECTIVITY_EFFECTIVE_TIMEOUTS_INDEPENDENT_COVERAGE. This does not activate supervision or close the service watchdog.

## Metrics and read-only adversarial coverage

| METRIC | CURRENT RESULT |
| --- | --- |
| CLOCK_SAMPLE_COUNT | 0 |
| CLOCK_BACKWARD_EVENTS | NOT_OBSERVED |
| CLOCK_DUPLICATE_EVENTS | NOT_OBSERVED |
| MAX_FORWARD_DELTA_US | NOT_OBSERVED |
| MIN_FORWARD_DELTA_US | NOT_OBSERVED |
| CLOCK_CONTINUITY_OBSERVED | NOT_OBSERVED |
| DB_CLOCK_GUARD_RTT_SAMPLE_COUNT | 0 |
| DB_CLOCK_GUARD_RTT_P50/P95/P99/MAX | ABSENT |
| CONNECTION_ACQUISITION_SAMPLE_COUNT | 0 |
| CONNECTION_ACQUISITION_P50/P95/P99/MAX | ABSENT |
| PRECISION_OBSERVED | NOT_OBSERVED |
| SAME_BACKEND_SESSION | NOT_OBSERVED |
| READ_ONLY_60S_TRANSACTION_SURVIVES | NOT_TESTED |

| CASE | RESULT | EVIDENCE / REQUIRED HANDLING |
| --- | --- | --- |
| A01 fixed transaction_timestamp | NOT_RUN | same TX repeated exact T0/CURRENT_TIMESTAMP/now values required |
| A02 advancing clock_timestamp | NOT_RUN | fresh DB wall-time samples, not client clock required |
| A03 multiple samples same session | NOT_RUN | retain actual backend/session identity at every sample |
| A04 backend identity stable | NOT_RUN | unexpected identity change must deny continuation |
| A05 timeout inventory readable | NOT_RUN | effective read-only pg_settings/current_setting values required |
| A06 read-only transaction survives60s class | NOT_RUN | approximately full-window observation then explicit ROLLBACK |
| A07 rollback leaves no mutation | NOT_RUN | no transaction opened here; zero DB calls is not runtime rollback proof |
| A08 repeated guard RTT | NOT_RUN | measure monotonic local round trip only; do not label ceremony latency |
| A09 connection acquisition latency | NOT_RUN | separate bounded direct connection population; no production inference |
| A10 DB interruption if safely observable | NOT_INJECTED | no destructive fault or unapproved termination; natural event only |
| A11 session termination contract | CONTRACT_ONLY | loss of authoritative session/time blocks; no actual cancellation trace |
| A12 transaction timeout interaction | UNKNOWN_EFFECTIVE_VALUE | read actual limit before compatibility classification |
| A13 statement timeout interaction | UNKNOWN_EFFECTIVE_VALUE | query cancellation cannot certify absent outcome |
| A14 idle transaction timeout interaction | UNKNOWN_EFFECTIVE_VALUE | local crypto idle period may terminate original session |
| A15 pool session pinning | SOURCE_ONLY_UNQUALIFIED | physical DS source; final external routing/pool config unknown |
| A16 no application clock substitution | UNKNOWN_ADMIN_IMPLEMENTATION | unrelated S15/telemetry clocks not eligibility evidence |
| A17 microsecond precision preserved | NOT_RUN | capture server instants and exact encode/decode equality |
| A18 no backward clock observed | NOT_RUN | zero samples means unknown events, not zero regressions |
| A19 restart/failover unqualified unless safe evidence | UNQUALIFIED_NOT_INJECTED | source contract does not prove runtime recovery |
| A20 supervision inputs inventory | COMPLETE_STATIC_INVENTORY_ONLY | live phase/session/timestamps/timeouts/coverage missing |

Twenty cases are accounted for as NOT_RUN, source/document-only or UNKNOWN; none is labeled runtime PASS. No busy-loop, synthetic timestamp counter, generated identifiers or historical percentile substitution is used.

## Findings and inherited status

| ITEM | STATUS | EFFECT OF THIS GATE |
| --- | --- | --- |
| RUNTIME_ACCESS_PREREQUISITE | BLOCKED; operational dependency, not new severity defect | stopped approved DB and unclear current startup/access authority; runtime qualification not available |
| SWO-H01 ADMIN budget/margin | HIGH / OPEN | no latency/limits/margin proof obtained |
| SWO-H02 ADMIN clock/session/supervision | HIGH / OPEN | primary target remains unqualified; no sampled evidence or independent coverage |
| SWO-H03 single-execution/ambiguous-COMMIT | HIGH / OPEN | no singleton/crash/race/transaction-outcome experiment |
| WATCHDOG deployment | HIGH / OPEN | no implementation, whitelist changes or original deployment closure proof |
| G3F4-H01 temporal fixture/positive transport readiness | HIGH / OPEN | originating rehearsal finding remains; no positive readiness/S01–S18/A-B/parity/rollback/concurrency/restart proof |

THIS_GATE_FINDINGS=B0/H0/M0/L0. No new observed authorization/clock/timeout defect is asserted; unavailable access is already a prerequisite of inherited SWO-H02 and other proof obligations, so it is not counted again as a HIGH. BLOCKED verdict is not BLOCKER severity. AGGREGATE_G3F_4_FINDINGS=B0/H5/M0/L0. No finding closes or narrows numerically; metadata/source inventory only makes the missing access proof explicit. Historical G3F3B-H01 is a different namespace, not current G3F4-H01. The selected fixed tuple/window and canonical V043 fence are unchanged.

## Concrete smallest next gate — not executed

NEXT_GATE=G3F_4_ADMIN_READ_ONLY_RUNTIME_ACCESS_SCOPE_CLOSURE. Resolve exactly the stopped approved project/image/volume startup and ADMIN authentication route for this read-only diagnostic before dependent sampling; do not move to key/SIGN/ceremony implementation, writable latency or COMMIT fault tests. This is required by the observed access barrier, rather than assuming a successful qualification and selecting a later proof. No action in this next gate is executed here.

The bounded reviewable handoff is: use only flooow-0090-g3f4-cc2941797db3-postgres, the pinned image and existing cc2941797db3-data volume; determine permission for its existing PostgreSQL startup lifecycle/persistence separately from read-only application SQL. No rebuild/reinitialization, migration/V043 invocation, fixture/policy/ACL/role-attribute or production change is part of that scope. Determine a legitimate ADMIN authentication route without recovering erased plaintext or assuming password rotation. Existing permitted local authentication, if independently authorized and verified, is preferable to inventing an obligatory role mutation. If any password rotation is actually necessary, it needs its own precise current authorization and nonsecret authority-state equality capture; this task does not provide it. Do not rotate the four service roles merely to sample ADMIN.

Once that prerequisite is resolved, rerun this same qualification with a narrowly scoped SELECT-only probe: capture actual instance/database/user/backend/session/isolation/read-only identity and pg_settings; open one explicit READ ONLY transaction, periodically capture transaction_timestamp/statement_timestamp/clock_timestamp/CURRENT_TIMESTAMP/now and stable backend, observe approximately 61s with spacing (e.g. 100ms, about 610 samples, no busy loop), preserve exact UTC microseconds and separately measure only DB_CLOCK_GUARD_RTT with monotonic client timers; explicitly ROLLBACK. Collect a separately labeled bounded connection acquisition population if safe. This is an unexecuted diagnostic plan, not an arbitrary timing-policy/clock-jump tolerance or a promise that those counts/intervals will qualify extreme tails. Retain all raw deltas; compare DB clock observations and client monotonic diagnostics without granting client time authority. No XID/UUID creation function, secret catalog, V043 function, signer key or real manifest/signature is needed. No destructive fault injection or statement/role/config SET timeout changes. A natural connection loss blocks further observations/authority; observed discontinuity cannot refresh T0. On completion use the approved runtime shutdown/credential hygiene scope and preserve evidence. A successful observational read-only 61s survival remains insufficient for all five HIGH closures.

Additional historical identity/authority provenance: `docs/evidence/PACKAGE-0090-G3F-4-REHEARSAL-DEPLOYMENT-APPROVAL.json` SHA256 `84a0afd98f68a25c360e7b3e2056e92c9c9d945f364bf9d8931a730908d752de`; its original request SHA256 `2c2034bc756947a522438e155481418e8afe320b3c1180a988fd8f324324b822`. Neither was changed.

## Evidence ledger and validation

| READ SOURCE / PRIOR EVIDENCE | BYTE_SHA256 |
| --- | --- |
| applications/marketplace-operations-persistence-postgres/src/main/kotlin/io/flooow/marketplace/persistence/postgres/PostgresDataSources.kt | 3111a5095ccf3ab8bda131b3fe282d48ea9cbcf2b60ae0d548ffe7e904efffe5 |
| applications/marketplace-operations-persistence-postgres/src/main/kotlin/io/flooow/marketplace/persistence/postgres/PostgresApprovalGovernance.kt | 442b9fe79b023e0d7a36134d9c7cf717335a5418c249af8ddcc42521ccb3863d |
| applications/marketplace-operations-persistence-postgres/src/main/kotlin/io/flooow/marketplace/persistence/postgres/PostgresInventoryRiskAssessmentJournal.kt | 9cb13e353e7937251a1d2c56743789d90190c371e8dd77c3bf270b93cfdbe295 |
| applications/command-authority-ceremony/src/main/kotlin/io/flooow/ceremony/GovernedJdbc.kt | 6274b34f8884632503e3b5796d143c06fdaa02a5d8154d9c00173cbb18194017 |
| applications/command-authority-ceremony/src/main/kotlin/io/flooow/ceremony/GovernedOfflineFieldProofLauncher.kt | 4f0732c34e883aa84e88ce220b874479c856e4320c32bbca6e01ac161f92676f |
| applications/marketplace-operations/src/main/kotlin/io/flooow/marketplace/operations/authorization/ApprovalAttestationCanonicalCodec.kt | 74763cd4b0c3ab49b3f2c882f724df3ec10561f9aaa452c7b29fd1d6a943b26d |
| applications/marketplace-operations-persistence-postgres/build.gradle.kts | 5b7f085fb3b59c0c4c701ec60ccef013fd0b0c9bfcd1e80fd6def0991e1e48d4 |
| scripts/validation/Package0090TransportReview.java | 3030ba0c738ecf4443c8067ef40f768fa2406b0b4984f6e2fd4ff0755f499971 |
| docs/specifications/SPEC-0090-governed-offline-field-proof-exclusive-capability-composition.md | d12acc86cbed8d56cd774f427b79dce26258a36ac65a7d78bf2cb1fb37fd9a92 |
| docs/adr/ADR-0090-governed-offline-field-proof-exclusive-capability-composition.md | e1c26d2f202684d5ace54408c83a0fcf100085864270f0c32cb077b9398566a9 |
| compose.yaml | 07bd8d1ba5dd75e78ec6a9baeeb39f3c92b12eb815e782c14a3fcc9e83fdabe9 |
| AGENTS.md | d4eb9ccd39d115b72da41cefddf418e998bd5dcb89c1be37f44a7193f27d6fda |
| docs/evidence/PACKAGE-0090-G3F-4-SIGNING-WINDOW-OPERATIONAL-REVIEW.md | 4beb7f456ec8ad9e956d5ed027401df3c5159b453eb8426d4bab4dd8e54dc0fa |
| docs/evidence/PACKAGE-0090-G3F-4-FINAL-CEREMONY-SIGNING-WINDOW-CONTRACT-REVIEW.md | dbd1e627a0d6727c14b126cd3a5bc2d70b8e3033429086d2accf0482e374c5b8 |
| docs/evidence/PACKAGE-0090-G3F-4-FINAL-CEREMONY-TIME-CONTRACT-CLOSURE.md | 4bafa0b9575ce6342b909c719acaa50a06df92cd916a8fa4059166145f70085f |
| docs/evidence/PACKAGE-0090-G3F-4-TC-R01-PROTECTED-MATERIAL-PROJECTION-REMEDIATION.md | ebe3b97de6a40b48437ebbe3badd41a43a9f8ec4bf36de9fdf865da8f3b9060f |
| docs/evidence/PACKAGE-0090-G3F-4-FINAL-CEREMONY-RECOVERY-CLOSURE.md | 281fc2d1cb0f4c929d6b421bae9a4a408f9441aa5b48d6aa21b1d2cc1af74518 |
| docs/evidence/PACKAGE-0090-G3F-4-TIMING-08006-DIAGNOSIS.md | 08b91488bbc8e9b8030cb3f16224bbae15e03409745249096bf45295cee14862 |
| docs/evidence/PACKAGE-0090-G3F-4-TRANSPORT-MODEL-REVIEW.md | d8488c63390f3c29c9775c8f402e318fd6eab35416a9d0371a9d52f28275f192 |
| docs/evidence/PACKAGE-0090-G3F-4-WATCHDOG-DEPLOYMENT-CLOSURE.md | 858f26755b1d81043f38e96f62c6672ed816f51287571f6c4860cd4b6eb385cb |
| docs/evidence/PACKAGE-0090-G3F-4-ISOLATED-POSTGRES18-REHEARSAL.md | 7fd17925b2eb7125b012a3f8d83e367fd8dfb351bd9e140dadbf1667e8e26b2f |

Validation required before publication: all 1259 prior tracked byte hashes equal, all 168 prior evidence unchanged, exactly one staged new path, A01–A20 present without runtime-PASS claims, all measured population counts zero and all unobserved deltas/percentiles explicit unknown/absent, inherited HIGH sum5 unchanged, approved container still exited, and no DB/crypto/identifier/action effects. These checks validate completeness/truthful negative evidence, not session/runtime feasibility. Commit/push only this artifact under docs(package-0090), fetch/live origin equality and clean worktree. The final checkpoint hash is returned after publication; the immutable body records reviewed baseline rather than guessing its own commit.

Requested RETURN (review baseline; resulting checkpoint returned separately):

```text
G3F_4_ADMIN_SESSION_CLOCK_AND_TIMEOUT_READ_ONLY_QUALIFICATION=BLOCKED
BRANCH=checkpoint/package-0090-cloud-handoff
BASELINE_HEAD=29022c522d4a9441d82252488f3cb14f1cc9d2c1
FINAL_LOCAL_HEAD=REPORTED_AFTER_PUBLICATION
FINAL_REMOTE_HEAD=REPORTED_AFTER_PUBLICATION
LOCAL_EQUALS_REMOTE=YES_BASELINE
WORKTREE_CLEAN=YES_BASELINE
ADMIN_DB_SESSION_QUALIFIED=NO
DB_CLOCK_AUTHORITY_QUALIFIED=NO_RUNTIME_QUALIFICATION
TRANSACTION_TIMESTAMP_SEMANTICS=DOCUMENTED_NOT_RUNTIME_OBSERVED
FRESH_CLOCK_SEMANTICS=DOCUMENTED_NOT_RUNTIME_OBSERVED
SESSION_CONTINUITY_QUALIFIED=NO
TIMEOUT_COMPATIBILITY=UNKNOWN
READ_ONLY_60S_TRANSACTION_SURVIVES=NOT_TESTED
T0_FIXED_WITHIN_TRANSACTION=NOT_OBSERVED
FRESH_DB_CLOCK_ADVANCES=NOT_OBSERVED
SAME_BACKEND_SESSION=NOT_OBSERVED
CLOCK_SAMPLE_COUNT=0
CLOCK_CONTINUITY_OBSERVED=NOT_OBSERVED
CLOCK_CONTINUITY_UNIVERSALLY_PROVEN=NO
DB_CLOCK_GUARD_RTT_SAMPLE_COUNT=0
DB_CLOCK_GUARD_RTT_P50=ABSENT
DB_CLOCK_GUARD_RTT_P95=ABSENT
DB_CLOCK_GUARD_RTT_P99=ABSENT
DB_CLOCK_GUARD_RTT_MAX=ABSENT
CONNECTION_ACQUISITION_SAMPLE_COUNT=0
CONNECTION_ACQUISITION_P50=ABSENT
CONNECTION_ACQUISITION_P95=ABSENT
CONNECTION_ACQUISITION_P99=ABSENT
CONNECTION_ACQUISITION_MAX=ABSENT
CLOCK_BACKWARD_EVENTS=NOT_OBSERVED
CLOCK_DUPLICATE_EVENTS=NOT_OBSERVED
MAX_FORWARD_DELTA_US=NOT_OBSERVED
MIN_FORWARD_DELTA_US=NOT_OBSERVED
PRECISION_OBSERVED=NOT_OBSERVED
APP_CLOCK_IN_AUTHORITY_PATH=UNKNOWN
SUPERVISION_INPUTS_AVAILABLE=STOPPED_CONTAINER_METADATA_AND_DOCUMENTED_SOURCE_INTERFACES_ONLY
SUPERVISION_INPUTS_MISSING=LIVE_BACKEND_T0_DB_CLOCK_REMAINING_WINDOW_PHASE_CUSTODY_CONNECTIVITY_EFFECTIVE_TIMEOUTS_INDEPENDENT_COVERAGE
WATCHDOG_STATUS=OPEN/HIGH
H01_STATUS=OPEN/HIGH
G3F_4_STATUS=HOLD
BLOCKER_COUNT=0
HIGH_COUNT=0
MEDIUM_COUNT=0
LOW_COUNT=0
AGGREGATE_G3F_4_BLOCKER_COUNT=0
AGGREGATE_G3F_4_HIGH_COUNT=5
AGGREGATE_G3F_4_MEDIUM_COUNT=0
AGGREGATE_G3F_4_LOW_COUNT=0
DATABASE_MUTATION=NO
DATABASE_CONNECTIONS=0
SQL_CALLS=0
CONTAINER_START=NO
KEY_GENERATION=NO
SIGNATURE_CREATION=NO
IDENTIFIER_GENERATION=NO
PRODUCTION_IMPLEMENTATION=NO
ARTIFACTS_CREATED=1
ARTIFACTS_MODIFIED=0
COMMIT=REPORTED_AFTER_PUBLICATION
PUSH=CHECKPOINT_ONLY_AFTER_VALIDATION
NEXT_GATE=G3F_4_ADMIN_READ_ONLY_RUNTIME_ACCESS_SCOPE_CLOSURE
NEXT_GATE_STARTED=NO
```

## Immutable prior Package 0090 evidence inventory

| PRIOR ARTIFACT | BYTE_SHA256 |
| --- | --- |
| docs/evidence/PACKAGE-0090-BINDING-AUTHORITY-INTEGRITY.json | 5c0f957f9682f744e1f88a4c4cef0f479a8909bea8f28c343ccdc1e679e54001 |
| docs/evidence/PACKAGE-0090-BINDING-PROVISIONING-CONTRACT-DESIGN.md | 5add8c6da53ffcb722cd78fdc4f4e35c1a50f43431dd4349d8684f02b8254787 |
| docs/evidence/PACKAGE-0090-BINDING-PROVISIONING-MATRIX.json | 8be5d6141b6cfa459137e778362be4161a9f6b440ea07981aca3c24a812eed5a |
| docs/evidence/PACKAGE-0090-BINDING-PROVISIONING-NEGATIVE-MATRIX.json | 5efbd2450fd94990a1cb7c0cbcda789d747006c76176914af96afb7d16689496 |
| docs/evidence/PACKAGE-0090-CURRENT-INDEPENDENT-SOURCE-REVIEW.json | 631b68e8c483ab283c4caa11b96bd6ceac60f3226c6af9bac14d68e564699d36 |
| docs/evidence/PACKAGE-0090-DEPLOYMENT-INCARNATION-APPROVAL-MATRIX.json | ca5550e9273c95b5d91ad9c33e6c8bedd0771135e7f16a2303c76de72d67e1da |
| docs/evidence/PACKAGE-0090-ED25519-NATIVE-REVIEW.json | f5e255dbd134656e58af257c411ca5bd36a5b86b432117bbccf710eaba91f5dc |
| docs/evidence/PACKAGE-0090-ED25519-NATIVE-REVIEW.md | ef1c29c29ea19b221bfa5c3a9e03194576587c028ee8b8074b9f75043cd739ae |
| docs/evidence/PACKAGE-0090-ENROLLMENT-BINDING-CONTRACT-CLOSURE.md | f091d0b11446151dcb9db3636f8d1bc82c9ed0c724767e00fb537a267b64ac86 |
| docs/evidence/PACKAGE-0090-ENROLLMENT-ENTRYPOINT-AUTHORITY-REVIEW.json | a719df6b7ce319d92d701d012711eafd1d46df45a84a84e98d0d944e87858657 |
| docs/evidence/PACKAGE-0090-ENROLLMENT-ENTRYPOINT-AUTHORITY-REVIEW.md | 1b673e92df11070105e0bfb326ab6b23aa262f3543af2ab73476741742412c7b |
| docs/evidence/PACKAGE-0090-ENROLLMENT-ENTRYPOINT-READONLY-SNAPSHOT.json | 3b9cf2ca67890eb3cb42f9ee451b5c495a5fd2a5403b7454831b2965e61aadb0 |
| docs/evidence/PACKAGE-0090-EXECUTOR-FINAL-TESTS.txt | 9b149f2b6bcfb5ef8ec1de75dcb9758ab5f0570180ff73263d923f140bb63bf5 |
| docs/evidence/PACKAGE-0090-FULL-TESTS.txt | 9d4996a557ba6cbabc5a1e90a6e70e596d48c19170b039c680d74a207aabdbc0 |
| docs/evidence/PACKAGE-0090-G3F-3B-CATALOG-GOLDEN-CLOSURE.md | 39e220d5fabcf62e1e37c08603b17681a283a13ec31c7813bba4c718c8373e40 |
| docs/evidence/PACKAGE-0090-G3F-3B-CATALOG-GOLDENS.json | f53bbfb436348ea2c2e75599946fe883c02ad03d0b91ddc5196b296ab3c65b2c |
| docs/evidence/PACKAGE-0090-G3F-3B-CLOUD-EXECUTION.md | 5413f976c7d157557250e74918b6b537446a633b6eccd8f23b976ff9716ed5eb |
| docs/evidence/PACKAGE-0090-G3F-3B-CODEC-GOLDENS.json | 2876d9774823f285fc714cf8ad021cd0b38adb568614a399defa6cc2cd1d1766 |
| docs/evidence/PACKAGE-0090-G3F-3B-EVIDENCE-FIXTURE-001.json | 0c071e9f4de63f3515a3147ea979e872012f3d90602b02fa09f895a869dde15c |
| docs/evidence/PACKAGE-0090-G3F-3B-FIXTURE-001.json | edfb8fe983a2adc5c7fed224fbc418108c4dbfcba9caa67fd15f640d92ddf820 |
| docs/evidence/PACKAGE-0090-G3F-3B-FIXTURE-CLOSURE.md | 4715aa42f0bb5402d4be12b2f18ea53c98bb1211d0e023216cb78c194b223a0c |
| docs/evidence/PACKAGE-0090-G3F-3B-INTERNAL-P-SOURCE-REVIEW.md | c412a8b08e28d39ace980f95e7e3df7cdc7bf28f7881f398f36266b0730194b9 |
| docs/evidence/PACKAGE-0090-G3F-3B-INTERNAL-Q-SOURCE-REVIEW.md | 28551d80e34c2471813333f44dfce09589616c4cbcd8644df7a43a6d6180c7c9 |
| docs/evidence/PACKAGE-0090-G3F-3B-INTERNAL-Z-SOURCE-REVIEW.md | 7559b27c50ec158fbeb7600b3e0c17817cc8764bfac775373560acadd6a47f59 |
| docs/evidence/PACKAGE-0090-G3F-3B-ISOLATED-REHEARSAL-HANDOFF.md | 0b4ad2cfd1358613bbae22f3c2a9e1c95f93494f7c6e036f0812e02892e08f76 |
| docs/evidence/PACKAGE-0090-G3F-3B-NORMATIVE-EVIDENCE-CLOSURE.md | a407056d3581f1e6aad4b70337cef2c59a548a77980e0803ff298693d19a85a8 |
| docs/evidence/PACKAGE-0090-G3F-3B-POST-H02-SECURITY-REVIEW.json | 8e01fe605a44b5575bbf831d39c8ec6959fa8e5b9f4c784e8d1f1af6cb066b0f |
| docs/evidence/PACKAGE-0090-G3F-3B-POST-H02-SECURITY-REVIEW.md | 7f99b920c2c0e00b406a8fa73503748b7f07fe3350eefb27c3d7b1f753192033 |
| docs/evidence/PACKAGE-0090-G3F-3B-PUBLIC-WRAPPER-PREREQUISITES.json | cf4f6e0aae1649782e1eb21b8994906e02410b9876ca1936a8374eb237fedde0 |
| docs/evidence/PACKAGE-0090-G3F-3B-PUBLIC-WRAPPER-PROGRESS.json | 4195c94597cf3439ec23c1afd55a3f4c6802cb62da2f553ca01b49101460f31b |
| docs/evidence/PACKAGE-0090-G3F-3B-PUBLIC-WRAPPERS-CONTRACT-HOLD.md | 6c579261c4c791262258fc999f149e7d523ed9561209ba3ab47d62b0d59213d3 |
| docs/evidence/PACKAGE-0090-G3F-3B-S01-READINESS-AUTHORITY.json | 1b1e835256d0e222bf6e445738e59a7805e9107d1b484f43725d2d94c5308645 |
| docs/evidence/PACKAGE-0090-G3F-3B-S01-TARGET-AUTHORITY-HOLD.md | 5817365e55ee35f27fcb94c2f7fba5440000244340d38c0c08afeee64be09968 |
| docs/evidence/PACKAGE-0090-G3F-3B-S01-TARGET-CLOSURE.json | 3778f846c1e0a0baa700f231e4627601c635fbcce42d6105349f83d27d77e0d6 |
| docs/evidence/PACKAGE-0090-G3F-3B-S01-TARGET-SOURCE-REVIEW.md | 8b5e8d2d0e7a7365a3f7e9a059bcd5f496d0b935991414a6e3b7f4153f5614b0 |
| docs/evidence/PACKAGE-0090-G3F-3B-S02-CONSUMER-AUTHORITY-HOLD.md | ba97d272c245ab2a387a116afb81ccb65ec62899c65a4d46640dadbe42b73968 |
| docs/evidence/PACKAGE-0090-G3F-3B-S02-CONSUMER-AUTHORITY.json | 44bd3a1187c247a4c016890c339d8228d2e83be765aef9e303e53f804fd9e624 |
| docs/evidence/PACKAGE-0090-G3F-3B-S02-VERIFICATION-PATH-HOLD.md | 6c6f19474942bcff9f1cf803f60e8743b4775b2c794f1b69ed0fb29392f8edf2 |
| docs/evidence/PACKAGE-0090-G3F-3B-SOURCE-VALIDATION.json | 9e547dfd80671c2f4d34839ca4bfa537ca221a5a52a5a78b3677fa965a8c0b67 |
| docs/evidence/PACKAGE-0090-G3F-4-08006-DIAGNOSTICS.json | 448b0e84a53763f843fc73f68c6a07446a06d77ea215f5fdc73d964d6db5d18e |
| docs/evidence/PACKAGE-0090-G3F-4-AMBIGUOUS-COMMIT-RECOVERY.json | f22949d33e9daab11765e30f8b3da47be6e874c68f6f3e52e44f81cc367d5743 |
| docs/evidence/PACKAGE-0090-G3F-4-APPROVAL-AUTHORITY-CLOSURE.md | 399040f3e47892302bff29a7e5920c8663f8b3f01cc91fb2576f58e8564cf24a |
| docs/evidence/PACKAGE-0090-G3F-4-ATTESTATION-HEADER-TRANSACTION-GRAPH.json | 7b283eb7a7f12d86753ad2b348caf0252a521c5dd0bba2c61eaff84fb2b2b677 |
| docs/evidence/PACKAGE-0090-G3F-4-BINDING-DEPENDENCY-GRAPH.json | da505a68c1bfd9099d01308a0dd7ed27797017efc9e8cf089521331138c3df85 |
| docs/evidence/PACKAGE-0090-G3F-4-BINDING-GENERATION-AUTHORITY.json | 961119a4894ca5f77540a13824712ec985d63ceabf430e959a11faf7fca93add |
| docs/evidence/PACKAGE-0090-G3F-4-BINDING-HEADER-40-FIELD-MATRIX.json | 908ffd5ed0b61a506ea8522309efacae43b660e7ffbcaf7a51de890ac7c5afec |
| docs/evidence/PACKAGE-0090-G3F-4-BINDING-HEADER-INPUT-CONTRACT-CLOSURE.md | 2f053e975cfcd0b6413c1982cd865bf7b37e5b2b65253e51b2cc3fff548cd8a0 |
| docs/evidence/PACKAGE-0090-G3F-4-BINDING-HEADER-INPUT-MATRIX.json | dd067e6b45207cfc41528f9e3309b02d8f95481000e6404229f2a069cc333646 |
| docs/evidence/PACKAGE-0090-G3F-4-BINDING-PLAN-AUTHORITY-CLOSURE.md | e8e1b23236f32116c7c1d3ad9c59160b9fff370c852a60594003dfcfaf979af9 |
| docs/evidence/PACKAGE-0090-G3F-4-BINDING-PLAN-AUTHORITY-MATRIX.json | 4b6183c0eef78cf254e1ac3ab30b73b0e9a30c76c00362078a44377c6ad8a9e3 |
| docs/evidence/PACKAGE-0090-G3F-4-BINDING-PLAN-FINGERPRINT-CONTRACT.json | 493208b50d2da8f81185f1c8dc93c16676f8ced3ee064133f8b975c798b40de8 |
| docs/evidence/PACKAGE-0090-G3F-4-BINDING-PLAN-REGISTRATION-INPUT-CLOSURE.md | 44e07adf21d4cc9cb823079acef3aa4f9724e4e07da19a823ce902c825f21db9 |
| docs/evidence/PACKAGE-0090-G3F-4-BINDING-REGISTRATION-ID-LINEAGE.json | 0c51ba0d4e74fc06b7db790ac3ad925bc6ae053b76cd9b0337e89783e0dbf6a7 |
| docs/evidence/PACKAGE-0090-G3F-4-BINDING-TIMESTAMP-AUTHORITY.json | 1e04dd75234935bff8fcc3b215c275cd3cdbdf69b837081e96314b08ffc880a9 |
| docs/evidence/PACKAGE-0090-G3F-4-CANONICAL-BINDING-PREREQUISITE-SCOPE.md | 47f863125c3dd2272eddac768f6ca293b4d8378eefc429c29f6d153b4aac251d |
| docs/evidence/PACKAGE-0090-G3F-4-CANONICAL-SOURCE-COMMITTER-RUNTIME.json | 4b8dffa159baf07506b98645b1b60343768f52aa81278b106d39424ec0f6841e |
| docs/evidence/PACKAGE-0090-G3F-4-CEREMONY-CRASH-POINT-MATRIX.json | 9313ed5258fcaa17b6d52fb41e13129959ea2c2f3c4b459f5495af25f8a616f4 |
| docs/evidence/PACKAGE-0090-G3F-4-COMMAND-AUTHORITY-INPUT-GRAPH.json | 6b17cdd3fc575037bbbeef70756bd09f8fcbbf13f9fd7a71b5d200f7c00dbf8b |
| docs/evidence/PACKAGE-0090-G3F-4-CONCURRENCY-2.json | 6c3b4f4dc20ada0013e23976c73e60a5bc86d13479e4ae71719cfded4816a234 |
| docs/evidence/PACKAGE-0090-G3F-4-CONCURRENCY.json | 4fcba43d874705981f55cf77232cee618f9be6bd9e34a31ed9aa995807e08d56 |
| docs/evidence/PACKAGE-0090-G3F-4-DATA-SCOPE-INTEGRITY.json | edb846a66415b5861e7ef2e8c0674975b7b836611d8829d8a3d75ac20cb6b042 |
| docs/evidence/PACKAGE-0090-G3F-4-DNA-INVARIANT-REVIEW.md | c8dd9b3b3c14c73b1bbe39327477ab8a95252007c1659d763f6ca3f5fccc0bd1 |
| docs/evidence/PACKAGE-0090-G3F-4-DOMAIN-DEPENDENCY-GRAPH.json | ef3346b9660448a8815261e16ecb7c03fb2930f0645484730d65d2d1222825cd |
| docs/evidence/PACKAGE-0090-G3F-4-E2E-RUNTIME.json | 9f63fda8b6728b5a8fbca903f4e7fbfc5c1b6ef68edad30149e65caa2c87ec53 |
| docs/evidence/PACKAGE-0090-G3F-4-ELIGIBLE-S01-TIMING.json | ad634aaf8ed1a885132e0f02d58401a31ed8e739dfe36325c4e2ee6c9483fb06 |
| docs/evidence/PACKAGE-0090-G3F-4-EPHEMERAL-REHEARSAL-CREDENTIAL-LIFECYCLE.json | 6b135c84d2db7e0ddc1cd024af0a5c7385445701af6758b4c6ab2f9b86880a4a |
| docs/evidence/PACKAGE-0090-G3F-4-EVIDENCE-BINDING-FINGERPRINT-MATRIX.json | de884a0c2d83b886a072c51978fcf8020549130f0e6b18871127324fa8a8b868 |
| docs/evidence/PACKAGE-0090-G3F-4-EVIDENCE-BINDING-FINGERPRINT-RUNTIME.json | ec46ab8b9c62f6964e1fa1968f25d6954dcd22493567c6186fab7038aefc52cc |
| docs/evidence/PACKAGE-0090-G3F-4-EVIDENCE-BINDING-REPRODUCIBILITY.json | c42a1161499b669f3364c41697371b9fd02e185c54044bcac5f1fb405a236d8b |
| docs/evidence/PACKAGE-0090-G3F-4-FINAL-ATOMIC-CEREMONY-GRAPH.json | 70a7e45bd3e3a03e022b692178386615cd3f36b5489b372bac086a33ea56d467 |
| docs/evidence/PACKAGE-0090-G3F-4-FINAL-CEREMONY-FAILURE-MATRIX.json | 9260d6410f277d887738d419a0d72320881b441d29d6863c84c62352f27a6668 |
| docs/evidence/PACKAGE-0090-G3F-4-FINAL-CEREMONY-RECOVERY-CLOSURE.md | 281fc2d1cb0f4c929d6b421bae9a4a408f9441aa5b48d6aa21b1d2cc1af74518 |
| docs/evidence/PACKAGE-0090-G3F-4-FINAL-CEREMONY-SIGNING-WINDOW-CONTRACT-REVIEW.md | dbd1e627a0d6727c14b126cd3a5bc2d70b8e3033429086d2accf0482e374c5b8 |
| docs/evidence/PACKAGE-0090-G3F-4-FINAL-CEREMONY-TIME-CONTRACT-CLOSURE.md | 4bafa0b9575ce6342b909c719acaa50a06df92cd916a8fa4059166145f70085f |
| docs/evidence/PACKAGE-0090-G3F-4-FINAL-HEADER-40-FIELD-MATRIX.json | 6c09b93703c84c70416dd077aa8391ef96ed317fe2d422d4b4de27fa12d5324f |
| docs/evidence/PACKAGE-0090-G3F-4-FINAL-REHEARSAL.md | 050f5e8f377d3737115a6ca2cc8f0025befdc1f9ceb5e2de4745a8551fdc5d88 |
| docs/evidence/PACKAGE-0090-G3F-4-FIXTURE-002.json | 55dd5e816a714987710447ca3ae40d2294d2d8f8a2baa63c26e39ff855a4fcef |
| docs/evidence/PACKAGE-0090-G3F-4-GOVERNED-ECONOMIC-EVIDENCE.json | fe769ded569a40feea1b04eb856c8c0ae99dc98c81788286d7f6d63676a1b5b6 |
| docs/evidence/PACKAGE-0090-G3F-4-HEARTBEAT-MODEL-REVIEW.md | bd8b75c55bd379b61d6ad1dee0f55691248213dab642005fca2be4450e5bf7fc |
| docs/evidence/PACKAGE-0090-G3F-4-HISTORICAL-ATTESTATION-REUSE-MATRIX.json | bced0e65443678fa9c89ee923de52b48d7e830f131005d2e6fc0fb9cc39b90ba |
| docs/evidence/PACKAGE-0090-G3F-4-IDENTITY-SIGNAL-CLOSURE.md | 57b6fb92b71c2bff1910cd745ba7bc9dc935e4f072e96c6ec77d1ee1b744100c |
| docs/evidence/PACKAGE-0090-G3F-4-IDENTITY-SIGNAL-REVIEW.json | 1b159acadfb3f86b63d20f46ae50267ef42da7c0b7a8ccdcffc17f0c7cdad010 |
| docs/evidence/PACKAGE-0090-G3F-4-IDENTITY-SIGNAL-RUNTIME.json | f0067665ae37d4e4a56c98604a7e7f72465cc0b4b386a6436ce5b0934373e0b6 |
| docs/evidence/PACKAGE-0090-G3F-4-INSTALLED-ACL.json | 709ff68e0b56cf0b48817de326656ae07ddcc25d8b46d4eb8c1f83518a65b662 |
| docs/evidence/PACKAGE-0090-G3F-4-INSTALLED-CATALOG.json | fc1fbd866c984e76da3d7c7c256894de7f8b94898130e11f10b78976d048b715 |
| docs/evidence/PACKAGE-0090-G3F-4-ISOLATED-POSTGRES18-REHEARSAL.md | 7fd17925b2eb7125b012a3f8d83e367fd8dfb351bd9e140dadbf1667e8e26b2f |
| docs/evidence/PACKAGE-0090-G3F-4-LOGIN-EVENT-ENROLLMENT-RUNTIME.json | 7ceadd1ee9100c485d9397ff300c2de5a78af7c24399472b016fcb6b18b8c949 |
| docs/evidence/PACKAGE-0090-G3F-4-ORIGINAL-ATTESTATION-CONTEXT-CLOSURE.md | 4efaff86af2bf81b0ba1045bedbb1a1903686bd3c243a5341e096d37013a1787 |
| docs/evidence/PACKAGE-0090-G3F-4-ORIGINAL-ATTESTATION-CONTEXT-MATRIX.json | dc31510de3abc5271292e370e6dc5ed5e243cb47c9f97fa649300e1564f09e42 |
| docs/evidence/PACKAGE-0090-G3F-4-ORPHAN-SIGNER-RECOVERY.json | aeff2a66622e9c9aa15f0eaac8fde81ebb1a45af926da74e32f2e62c9916c7a5 |
| docs/evidence/PACKAGE-0090-G3F-4-PLAN-IDENTITY-ALLOCATION-CONTRACT.json | c7bbbef6a549dcff8a003569b7ef4ea681af3ab222304ee93f541557d7e8685f |
| docs/evidence/PACKAGE-0090-G3F-4-PLAN-REPLAY-IDEMPOTENCY-MATRIX.json | 5747dcd1b52019ec4ebc0a5e4401cb4e17d89851ba7843af13ba5d7719acd7b6 |
| docs/evidence/PACKAGE-0090-G3F-4-POSITIVE-READINESS.json | 7fda92880398e112f9263aead8211e24e9af68e4eae24ca1b7d127f39ff8b0f2 |
| docs/evidence/PACKAGE-0090-G3F-4-POST-REVOCATION-EVIDENCE-PROOF.json | 0ad1308925f4f6f22f02a1ad6f6d9454639f238bfbf2cfa9aa18840c2360aa19 |
| docs/evidence/PACKAGE-0090-G3F-4-PREREQUISITE-NEGATIVE-MATRIX.json | 81f4ac478a0907faa744a798d40eba3ab38546091702e66bf5da848de30e096a |
| docs/evidence/PACKAGE-0090-G3F-4-PREREQUISITE-PROVISIONING-MATRIX.json | aa16c0678b3162692b2e81cead6d9e01f7dfa191cbd9d487b8f89384b7edbd0a |
| docs/evidence/PACKAGE-0090-G3F-4-RECOVERY-2.json | 7667c937530c1a833ac626a6b33a305a36bb08934aa5eda27cb7bb7640c6ad66 |
| docs/evidence/PACKAGE-0090-G3F-4-REHEARSAL-BINDING-AUTHORIZATION.json | e869dcff6562ed0ce2410efab90bdf6273821da63c37853f0bbffec4ee82e48c |
| docs/evidence/PACKAGE-0090-G3F-4-REHEARSAL-BINDING-PROVISIONING.json | 75abf244535a33e2fd35a7ef373659f146dafc07fa7274bb2d78bc2170e1ad55 |
| docs/evidence/PACKAGE-0090-G3F-4-REHEARSAL-DEPLOYMENT-APPROVAL.json | 84a0afd98f68a25c360e7b3e2056e92c9c9d945f364bf9d8931a730908d752de |
| docs/evidence/PACKAGE-0090-G3F-4-REHEARSAL-DOMAIN-ALLOCATION.json | 6402750ec87ba8a894d590502eebd32e19769d566614cd854c808e9b9f41a313 |
| docs/evidence/PACKAGE-0090-G3F-4-REHEARSAL-DOMAIN-AUTHORITY-CLOSURE.md | 5ed65ebbd0e84b93b82573d9465e85b3b75bb383b62ecf5e32c897a1fcb42fe2 |
| docs/evidence/PACKAGE-0090-G3F-4-REHEARSAL-SECRET-RESIDUE-SCAN.json | 006d46adc2ab0e2282f04f9c33200ffc2fabe002afd6e5f09bbb5341cc2a7848 |
| docs/evidence/PACKAGE-0090-G3F-4-REHEARSAL-SIGNED-DOMAIN.json | ea0c0b15e6d371f88f807d0e2635ec8a2e337fa94f370670ee429823ca7ba4c1 |
| docs/evidence/PACKAGE-0090-G3F-4-REHEARSAL-SOURCE-STORAGE-AUTHORITY-CLOSURE.md | ab02a2d15915695593edddde518a0773b12edc7e77d95a88ee7f78743dd45a69 |
| docs/evidence/PACKAGE-0090-G3F-4-RR-SNAPSHOT-PLACEMENT.json | 6045826ac91e866c20edc8634a5b4d126cac1adc04c03952f0c96c1e54412802 |
| docs/evidence/PACKAGE-0090-G3F-4-RUNTIME-TESTS.json | 1da479d9bca30260552346f20daa7a215b71423faa5ba2c86bf184e54a6372d0 |
| docs/evidence/PACKAGE-0090-G3F-4-SIGNED-ATTESTATION-VERIFICATION.json | 0cd7c0a1a8d91c64d00ededf533f9c04b79aa67dbe31fefb9aa6854aff76fce2 |
| docs/evidence/PACKAGE-0090-G3F-4-SIGNED-DOMAIN-MATRIX.json | f1b89f4b5a89d4c0794de5460c3aa8f4cf6be44fa3ddc201670dd54b7e7e37a1 |
| docs/evidence/PACKAGE-0090-G3F-4-SIGNER-AUTHORITY-REGISTRATION.json | 9ceca53f1a099da6d68c0d8254e5add03674c8fe299d434819bca8ecdb8e7f19 |
| docs/evidence/PACKAGE-0090-G3F-4-SIGNER-KEY-AUTHORITY-MATRIX.json | 609b6b69b8fd68c1fc7eb8ecb6fe3408adbb126c99fde68868c9db8a845f8b5b |
| docs/evidence/PACKAGE-0090-G3F-4-SIGNER-KEY-REGISTRATION.json | f82b3df65ffa02c121b7f4100e1e0a9bb55dbd4e759305fffd305f3ce2a515cc |
| docs/evidence/PACKAGE-0090-G3F-4-SIGNING-CEREMONY-AUTHORITY-CLOSURE.md | a13cad70eefd2c1267c53cdb7d042955ea0edd902e56872f57477e87ceb5d0bd |
| docs/evidence/PACKAGE-0090-G3F-4-SIGNING-CEREMONY-CAPABILITY-MATRIX.json | ee3c7024451f0bfddbbac66221021b11ad565f27d4b8ed32f90fda7cda89177d |
| docs/evidence/PACKAGE-0090-G3F-4-SIGNING-CEREMONY-RESIDUE-SCAN.json | fa6cc39d260037383bc207d2e980659fc0a8ed7aebe340db821b0931c0afc10e |
| docs/evidence/PACKAGE-0090-G3F-4-SIGNING-WINDOW-OPERATIONAL-REVIEW.md | 4beb7f456ec8ad9e956d5ed027401df3c5159b453eb8426d4bab4dd8e54dc0fa |
| docs/evidence/PACKAGE-0090-G3F-4-TC-R01-PROTECTED-MATERIAL-PROJECTION-REMEDIATION.md | ebe3b97de6a40b48437ebbe3badd41a43a9f8ec4bf36de9fdf865da8f3b9060f |
| docs/evidence/PACKAGE-0090-G3F-4-TEMPORAL-BOUNDS-REVIEW.md | 026aaaad878ecb8ff9ecdb46ffd73b210108300df658dc5f2eb0c9b6e80be4f6 |
| docs/evidence/PACKAGE-0090-G3F-4-TIMING-08006-DIAGNOSIS.md | 08b91488bbc8e9b8030cb3f16224bbae15e03409745249096bf45295cee14862 |
| docs/evidence/PACKAGE-0090-G3F-4-TIMING-PHASES.json | 934a01c237140e781e98aba0bea205f8902bbda6b0bea49453dbb8ca6a1b575a |
| docs/evidence/PACKAGE-0090-G3F-4-TIMING-QUALIFICATION-2.json | 998e4b3930fbb9b44c7d07c2c1eaeb5f63e1972068469adefbe54349662a17ea |
| docs/evidence/PACKAGE-0090-G3F-4-TIMING-QUALIFICATION.md | c30c60f340b2c779fefe4bbc17e0294bfb42f13c77a82c0afa6b64196717d65b |
| docs/evidence/PACKAGE-0090-G3F-4-TIMING-SAMPLES.json | e6415ef00764e10a030d1d74ff667870605210a4e1f4a06463bc233707daf15e |
| docs/evidence/PACKAGE-0090-G3F-4-TRANSPORT-MODEL-REVIEW.md | d8488c63390f3c29c9775c8f402e318fd6eab35416a9d0371a9d52f28275f192 |
| docs/evidence/PACKAGE-0090-G3F-4-WATCHDOG-AUTHORITY-REVIEW.json | b5165e1199147939336654739261389a47e96a42d6385eb8598cefe5be5a2baa |
| docs/evidence/PACKAGE-0090-G3F-4-WATCHDOG-DEPLOYMENT-CLOSURE.md | 858f26755b1d81043f38e96f62c6672ed816f51287571f6c4860cd4b6eb385cb |
| docs/evidence/PACKAGE-0090-G3F-4-WATCHDOG-FAILURE-MATRIX.json | 4e4b90dc0aaf552449098fdb179807dfa05550a89c11279524f96caf70ca228b |
| docs/evidence/PACKAGE-0090-G3F-4-WATCHDOG-RUNTIME.json | 97eb1391c509b33a6ce1c902b6b73cd67c399d6c6fc22754942ab217145930e8 |
| docs/evidence/PACKAGE-0090-G3F-4-WATCHDOG-VISIBILITY.json | 397fced6ced8063d537d75429ec75cf79c4125931db5a5bf4645f0c3a14fb145 |
| docs/evidence/PACKAGE-0090-GOVERNED-ROLE-RECOGNITION-MATRIX.json | f1c41a79dad696da214b97f7fb654f0a360bc5a49f2cecfb7862ba63ddaeb354 |
| docs/evidence/PACKAGE-0090-H02-ADAPTER-SCOPE.md | efd9b654f431a4c270070837f657067f5d5f0efb74f9b393ce3474963a102a12 |
| docs/evidence/PACKAGE-0090-H02-ADAPTER-TEST-RESULTS.json | 4bb0027e8f967649264887d06f74ecadbd0874cd3dd24f8b5d2de3038f15a4da |
| docs/evidence/PACKAGE-0090-H02-CLOSURE.json | e35aaea61c683b1de65c6058b2281108fcb682b82bc6996a9027cb2779b5c41a |
| docs/evidence/PACKAGE-0090-H02-FULL-OFFLINE-TESTS.txt | 80a16772cbd0fd245d4ed63403f08dd698e6039cb81a5374d5e75f3705750242 |
| docs/evidence/PACKAGE-0090-H02-G3F4-HANDOFF.md | 3b5c386b1488db2f3f451273b10866caa80d4f11a504fa15eac7805ae31762ef |
| docs/evidence/PACKAGE-0090-H02-INDEPENDENT-ADAPTER-REVIEW.json | 60bfbec29558c8fc7e7258cb6e0efba1045b42f054d9afee678d4a7f20bdc7ea |
| docs/evidence/PACKAGE-0090-H02-INDEPENDENT-SQL-REVIEW.json | 39a891e38abe205f46c8fa7418277d1e1042c87de27d2cc2d11f7bca0479f981 |
| docs/evidence/PACKAGE-0090-INDEPENDENT-G3F-3B-SECURITY-REVIEW.json | d15fe89cf666d64edd62f712d4981eb6388a97e0b54da085fd04612ec6f93c71 |
| docs/evidence/PACKAGE-0090-INDEPENDENT-G3F-3B-SECURITY-REVIEW.md | f8d16c117da7e217c8bbf6f7a9e73ad585f55535a2ddecbe93df26c78a9a7429 |
| docs/evidence/PACKAGE-0090-INDEPENDENT-MUTATION-REVIEW.json | 516a820d7dc0ba1f7b4e1303beddbeac6fa80ea58b74f2f9cfb29bc3cd38b80d |
| docs/evidence/PACKAGE-0090-INDEPENDENT-NATIVE-REVIEW.json | 95572ab1715a8c9dbea4cc98b61c1e158cc829ec8faff410dfbc75c4c4e7a439 |
| docs/evidence/PACKAGE-0090-INDEPENDENT-ORIGINAL-INPUT-REVIEW.json | 7acd0fe26b853a086f03faa4c665508edcc92cd69bf2640e560460aeb57700e6 |
| docs/evidence/PACKAGE-0090-INDEPENDENT-SOURCE-REVIEW.json | 29ae7bd4a7590e83b332829135f910fccda52e8990c23eca2cc17e2ed7f9dd52 |
| docs/evidence/PACKAGE-0090-INDEPENDENT-TEST-INVENTORY.json | 21ff81a9ed01491fee3c765dd0eee2300688c911bdb84ac6c5c069622b49e88d |
| docs/evidence/PACKAGE-0090-ISSUER-DELIVERY-ACK-AUTHORITY.json | e7c6ddaff433cd49a485ba1f6672f3e1acc069745c6d6071718970e71613604e |
| docs/evidence/PACKAGE-0090-LOGIN-EVENT-BINDING-RUNTIME.json | b7767cc2139c4b6b2cdb87252a3ae61ff21bbbfbec416d7c124fa62daa569c1f |
| docs/evidence/PACKAGE-0090-MUTATION-ORIGINAL-INPUT-AUTHORITY.json | bbc19ac21dabbb7fe01f8b4b5a36d0c2d9eecc1624c2ad07c6ac8e309592e0bd |
| docs/evidence/PACKAGE-0090-MUTATION-ORIGINAL-INPUT-AUTHORITY.md | 9c37ee42cf8a8660184a6ca77b28875dba059b666550d19a8c6af89a4b8dd64c |
| docs/evidence/PACKAGE-0090-MUTATION-ORIGINAL-MATCH-REVIEW.json | 5e1e9c662efcf1704d5556be8a81e47ed06bae41e8b88be3ede7a15478ad8586 |
| docs/evidence/PACKAGE-0090-PHASE-A-CLOSURE.json | 36983e944e2f7bc56dc51c7f7b4b6ca6d9a77a4886d2eb25b5bbb28e36e2871e |
| docs/evidence/PACKAGE-0090-PHASE-A-FULL-TESTS.txt | 88ec2118db9feea0ff9163a9448e897271a343b0ac451a3dc6ee99881132875c |
| docs/evidence/PACKAGE-0090-S02-EXPECTED-ATTESTATION-AUTHORITY.json | 67c63d386aff18660289c340351857f6bdf1e598f7592df0e16e8b5d3e054851 |
| docs/evidence/PACKAGE-0090-S02-EXPECTED-ATTESTATION-AUTHORITY.md | 0008fd06ced70d6c2b485da308a32eba1fb1cc745d0171d7cbe58f6a40917f10 |
| docs/evidence/PACKAGE-0090-S02-ISOLATED-PREDICATE-REVIEW.json | 90cf5c3bd99ebad7ed51890c6fe3db4863e59fc386df938017abb6b624720855 |
| docs/evidence/PACKAGE-0090-S02-ORIGINAL-INPUT-CLOSURE.md | f2cea24b34c3d1db628fc662cf13aaf54ac0f1279ff600972edc91bf01ad88ed |
| docs/evidence/PACKAGE-0090-S02-ORIGINAL-INPUT-GOLDENS.json | 56c71b6a2834158718bea4cc8652ee6971087a37dc8501d8a7aac9ce35e22d22 |
| docs/evidence/PACKAGE-0090-S03-SOURCE-REVIEW.md | 605b2af3f44aa6d2fbd6ee2cdf2c8c7e1042d278a55816a18ec686b3b72d5a9d |
| docs/evidence/PACKAGE-0090-S05-S06-ISOLATED-REVIEW.json | 11dad47242f12a6074167da45b8127e69815f8c1f9482f1dc9e151998e709ef2 |
| docs/evidence/PACKAGE-0090-S05-S06-TRANSPORT-GOLDENS.json | 3a8b2cda92514064f712c4e4f71bcb1773c519eaca8b30740547a827174afb50 |
| docs/evidence/PACKAGE-0090-S05-S12-SOURCE-REVIEW.md | d11abb145d1082c6f973c0cb6fa3e5b6c73375055a0b39fa5c3353643be00785 |
| docs/evidence/PACKAGE-0090-S07-S18-ISOLATED-REVIEW.json | 9800d386c58099026f48cd15cdec4dd148b43be5ff6dfe27eba7ebffeff183c4 |
| docs/evidence/PACKAGE-0090-S07-S18-TRANSPORT-GOLDENS.json | eb8eba300cc73a41d1e17f9093a5f264ba886813a4013e792d4d80116c55f754 |
| docs/evidence/PACKAGE-0090-S13-S18-SOURCE-REVIEW.md | 83673b94b7e8900d5a8b1ff069b342341136dfe2af2b9af7c1886675367533b0 |
| docs/evidence/PACKAGE-0090-SELF-ENROLLED-ANCHOR-PROOF.md | e45122541346e7ab1a872a54f6e5290af0823b38a7b11bbdbe8e6b47b4891431 |
| docs/evidence/PACKAGE-0090-SELF-ENROLLED-ANCHOR-REVIEW.json | 9bff9f1f1f0ee845652aac1d02261511b1956d354b29095c2055aadb27cdde63 |
| docs/evidence/PACKAGE-0090-SELF-ENROLLED-ANCHOR-RUNTIME.json | d7cd3aa05e5bb0ea184596c4d2236e817048b413bd6ece554b02c7477944462b |
| docs/evidence/PACKAGE-0090-SOURCE-COMPOSITION-CLOSURE.json | 01291f864f1e4dfd3a2852b647aec018d6ed5fd986af5966474d101bc1615388 |
| docs/evidence/PACKAGE-0090-V-BRIDGE-CAPABILITY-INVENTORY.json | b010edcaf2d98cfae596176619355dce7344be9aa7b2bda39927edaf257265c8 |
