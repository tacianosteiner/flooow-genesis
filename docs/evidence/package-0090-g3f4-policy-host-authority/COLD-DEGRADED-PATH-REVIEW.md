# Cold/degraded path review — observations, models and unknown tails

Completed warm mechanics are not rerun. The accepted100-sample20-phase population
remains P50=60416.7us/P95=91361.7us/P99=97028.8us/MAX=98078.1us.
Its first retained warmup was205596us, including first measured JVM/JCA/codec work
but excluding JVM launch, migration/provider warmup and initial writer connection.
It is a partial cold observation, not a complete cold ceremony percentile.

New disposable component observations, not a combined ceremony population:
initial container availability 1208337.4us;
fresh psql connection+process+Docker IPC min 206982.7us,
median 241970.1us, max 448782.2us (10samples);
controlled observed advisory-lock contention 1196387.0us.
Do not sum these maxima into an end-to-end p99 or safety guarantee.

| Factor | Observation or model | Coverage/remaining uncertainty |
|---|---|---|
|Cold JVM/class loading|Retained first warmup205596us; codec loaded in validation|JVM launch and complete cold start excluded; no full cold root |
|Cold DB connection|10actual fresh psql/docker process connections|Not JCA/JDBC cold writer connection or pure network latency |
|Container scheduling|Actual initial startup and subprocess wall times|Single sample, includes initialization; scheduling tail unbounded here |
|CPU contention|Model: scheduler delay consumes immutable deadline|No CPU stress injected; no universal bound |
|IO jitter|Model: WAL/storage delay before effect/commit|Physical backup performed, not an IO-jitter distribution |
|GC pause|Model: stopped JVM cannot refresh DB eligibility; enforcer must independently deny/kill/drain|No actual JCA GC-pause or kill test; handler/enforcer incomplete |
|Lock contention|Observed lock holder and real blocked acquisition|Can exceed selected1s transaction allowance; no timing renewal |
|Host supervision delay|Actual projection ages exceed100us|No qualified continuous loop/supervisor/drain latency |
|Local network stack|Fresh connections include IPC/Unix socket overhead|No isolated network jitter/loss tail distribution |
|Process startup|Container and fresh psql process components|Full launcher/receiver/control startup not qualified |
|PG checkpoint/background activity|Physical backup fast checkpoint executes in own fixture|No isolated contention/background/worst-case budget |
|Query-first reconnect|Accepted warm measurement includes fresh JDBC projection; new psql reconnect components|Authority/roles/guarded ambiguous transport still unqualified |
|Ambiguous COMMIT recovery|Actual unsigned ACK discard + writer join + fresh query|Not injected JDBC08006 or proven writer quiescence under lost connection |

WARM_MECHANICAL_P99=97028.8us
COLD_PATH_OBSERVED_OR_SIMULATED=PARTIAL_REAL_COMPONENTS_PLUS_EXPLICIT_FAILURE_MODELS
UNBOUNDED_EXTERNAL_FACTORS=SCHEDULER_CPU_IO_GC_NETWORK_SUPERVISION_RECOVERY_TAILS
RECOMMENDED_SAFETY_ENVELOPE=PROPOSE_RETAINED_NONRENEWABLE_60S_ARTIFACT_PROFILE_WITH_SEPARATELY_QUALIFIED_FINITE_TRANSACTION_HOST_AND_RECOVERY_BOUNDS

The proposal does not authorize that whole tuple or certify60s sufficient. A finite
artifact interval is not permission for an arbitrary stalled1s transaction or
stale100us health observation. Expiry is checked at signing/canonical effects/
pre-COMMIT; COMMIT visibility/ACK may follow original expiry. After uncertainty,
query-first inspects the same root only after writer disposition; no fresh T0,
signature, renewed window, inferred zero or automatic partial-root replay.
Cold/degraded failure aborts or quarantines before new effects. If no qualified
independent enforcement/drain bound exists, operational readiness stays false.
Only separately governed policy/protocol evidence can approve final numeric pairs.
