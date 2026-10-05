# Package 0090 — G3F.4 rehearsal fixture timing qualification

**STATUS: HOLD. G3F4-H01 remains OPEN/HIGH. Fixture-2 was not created or authorized.**

The candidate fails the explicit prerequisite MEASURED_WORST_CASE_US < WATCHDOG_MAX_US. The largest observed DB-clock heartbeat handoff was 80684 us against a candidate maximum of 20000 us. Even the warmed idle population reached 47904 us, so rejecting the candidate does not depend solely on reconnection cost. No transport failure or negative DB-clock interval was observed in 3100 successful samples. These observations do not demonstrate a SQL authorization defect.

User authorization section6 requires reporting the measured requirement and stopping for review when the candidate lacks adequate margin. Qualification therefore stops before fixture-2 creation, policy provisioning, positive S01 readiness and all dependent runtime gates. Historical HOLD reports and fixture-1 remain byte-identical; the disposable container is stopped and private plaintext credential files were erased.

## Distributions — microseconds

| Population | N | Min | p50 | p90 | p95 | p99 | p99.9 | Max | Mean | Sample SD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| idle_warm | 1000 | 1113.000 | 1519.000 | 2058.000 | 2318.000 | 3891.000 | 46780.000 | 47904.000 | 1722.265 | 2099.518 |
| cold_reconnect | 100 | 13445.000 | 21220.000 | 27268.000 | 30812.000 | 52797.000 | N/A (N<1000) | 80684.000 | 22713.150 | 8233.328 |
| load4 | 1000 | 1062.000 | 1410.000 | 2098.000 | 2702.000 | 4263.000 | 6997.000 | 10652.000 | 1582.610 | 630.844 |
| load8 | 1000 | 1064.000 | 1330.000 | 1904.000 | 2633.000 | 3832.000 | 6663.000 | 7302.000 | 1494.431 | 550.021 |

Percentiles use nearest rank. Standard deviation is the sample estimate (N−1). The p99.9 values at N=1000 are empirical order statistics with sparse-tail uncertainty. Combined statistics in the return fields are descriptive across intentionally different populations, not a single homogeneous latency model. Population order was idle/warm, cold/reconnect, load4, load8; no causal claim that load improves latency is made.

## Measurement and environment

Baseline `bd50ae1a21a9df85b5bdfb1da44766d22d11f21d` was fetched, local=remote and clean before authorized tooling. Exact reused project `flooow-0090-g3f4-cc2941797db3`, volume `flooow-0090-g3f4-cc2941797db3-data`, image `sha256:07fc165de5bb569d822460e2df645c5489f99220fc2cb16c86596d39db394561` and private read-only `/review` mount were proven before contact. No other container/database/volume was selected. The endpoint was rediscovered after restart and verified again by the Java Docker identity guard before JDBC. Fresh seed-derived rehearsal ADMIN/service passwords were delivered only through private files; password rotation changed no role attributes, memberships or ACLs.

PostgreSQL 18.4 (Debian 18.4-1.pgdg13+1); JDBC 42.7.12; Microsoft JVM 21.0.12; Windows 11 10.0 (amd64); Docker client/server 29.6.2/29.6.2. The previously pinned Linux/amd64 image is unchanged. CPU/memory controls are recorded verbatim in samples evidence; all numeric container quotas/limits are zero, meaning no explicit container-level quota. Enclosing Docker Desktop/host scheduling is not a guaranteed bound.

PGSimpleDataSource has no application pool in this experiment. Warm/load populations hold distinct physical ADMIN and AUDITOR connections, warmed by ten excluded handoffs. Each cold sample uses fresh ADMIN and AUDITOR backends; AUDITOR reconnection/setup deliberately occurs after the DB heartbeat update. ADMIN is autocommit READ_COMMITTED; AUDITOR is read-only REPEATABLE_READ with explicit rollback after each sample. Physical backend IDs are retained for every sample and were checked distinct. Authoritative age is EXTRACT(EPOCH FROM(clock_timestamp()-DB_RETURNED_HEARTBEAT))*1000000 inside PostgreSQL. Java monotonic clocks measure population durations; start/end client epoch metadata records overall audit elapsed time. Neither is used for authorization freshness.

Load4/load8 add four/eight persistent governed JDBC sessions to the two measuring sessions (total six/ten). The actual Kotlin GovernedTransaction invokes S02/S05/S07/S13 through the four real service identities on nonexistent scope and receives expected P0017 denials. Completed background calls: load4=745, load8=1441. A 10 ms fixed delay after each completed call regulates traffic without catch-up queues; this is not an expiry assertion or throughput stress test. Positive catalog/crypto/frozen-domain workload was not simulated or claimed. The tested lighter guard traffic already suffices to reject this candidate. Total bounded measurement audit elapsed time: 16.140 s; Java monotonic population durations are also retained independently.

## Temporal classification and preserved invariants

ADR0090 leaves approved numeric policy values and watchdog packaging to governed engineering work. SPEC18/21.2/21.3/25 fixes the security meaning. Category A includes DB time, finite positive actual/max bounds, checked arithmetic, deadline nesting, mandatory trusted watchdog, canonical version/digest binding, no future heartbeat, receipt MAC and non-renewal. Category B consists of separately approved watchdog enforcement cadence/max and health freshness/max; these are engineering parameters with security relevance to stale/revoke bounds, never free configuration. Category C consists of historical fixture-1 test numbers and the explicitly experimental candidate. The authorized preflight TTL 1000000/max2000000 us is fixed for this task.

A newly qualified immutable version would still deny age beyond its actual health window and future timestamps; no optional flag, grace, fallback, receipt renewal, privilege or SQL change is proposed. Source health checks deny age > actual window (equality is not denied by that predicate); authenticated preflight validity is issued_at <= now < expires_at (equality at receipt expiry is expired). These source rules are recorded for future boundary tests and are not represented as runtime boundary proof. The candidate health window is 15 watchdog cadences and 15% of the fixed actual preflight TTL. Those ratios alone do not qualify it, and no stale heartbeat under new bounds was accepted.

## Candidate rejection and exact review handoff

The safety rule was recorded before measurement: watchdog maximum >= 2× observed maximum, observed maximum strictly below watchdog maximum, and health window >= cadence + 2× observed maximum. This factor is an empirical rehearsal safety margin, not a statistical confidence guarantee or new policy authority.

| Check | Result |
|---|---|
| Candidate watchdog interval / maximum | 10000 / 20000 us |
| Measured maximum | 80684 us |
| Maximum minus measured maximum | -60684 us |
| Headroom ratio (max−observed)/observed | -0.7521193793 (-75.2119%) |
| Candidate max / observed max | 0.2478806207 |
| Minimum max required by declared 2× rule | 161368 us; NOT AUTHORIZED |
| Candidate health window / maximum | 150000 / 200000 us |
| Cadence + 2× observed maximum | 171368 us; exceeds candidate actual window |

NEXT_GATE=G3F_4_REHEARSAL_TEMPORAL_BOUNDS_REVIEW. Review the measured lower requirements above against SPEC18 enforcement/revocation/deadline bounds, then govern a revised experimental candidate explicitly. No larger number was installed or adopted. A revised experiment must qualify transport and then prove at least 100 actual S01 positive cycles plus stale/future/missing/incarnation/policy/receipt boundaries before closing H01. Full positive frozen/catalog/crypto workload and scheduler tails remain required; passing this necessary transport predicate alone would never close H01.

The requested FIXTURE-002 JSON is a rejection/disposition artifact, not a fixture definition. Its fixture ID/version/canonical fields/bytes/digest are null. Database policy inventory still contains only the exact fixture-1 row with unchanged canonical bytes, digest and effective_from. The timing readiness row remains NOT_READY/unhealthy with ineligible placeholder manifests, zero bindings, unchanged operational role attributes and identical function ACL digest.

## Return fields

| Field | Result |
|---|---|
| BASELINE | bd50ae1a21a9df85b5bdfb1da44766d22d11f21d |
| DISPOSABLE_ENVIRONMENT_IDENTITY | EXACT_PASS |
| TIMING_SAMPLE_COUNT_WARM | 1000 |
| TIMING_SAMPLE_COUNT_COLD | 100 |
| TIMING_SAMPLE_COUNT_LOAD4 | 1000 |
| TIMING_SAMPLE_COUNT_LOAD8 | 1000 |
| TIMING_MIN_US | 1062.0 |
| TIMING_P50_US | 1427.0 |
| TIMING_P95_US | 3350.0 |
| TIMING_P99_US | 23543.0 |
| TIMING_MAX_US | 80684.0 |
| TEMPORAL_CONTRACT_CLASSIFICATION | A_INVARIANTS_PRESERVED; B_GOVERNED_ENGINEERING_PARAMETERS; C_REHEARSAL_TEST_VALUES |
| CANDIDATE_WATCHDOG_INTERVAL_US | 10000 |
| CANDIDATE_WATCHDOG_MAX_US | 20000 |
| WATCHDOG_MAX_MARGIN_US | -60684.0 |
| WATCHDOG_MAX_MARGIN_RATIO | -0.7521193793069257 |
| CANDIDATE_HEALTH_WINDOW_US | 150000 |
| CANDIDATE_HEALTH_WINDOW_MAX_US | 200000 |
| PREFLIGHT_TTL_US | 1000000 |
| PREFLIGHT_MAX_TTL_US | 2000000 |
| FIXTURE_1_MUTATED | NO |
| FIXTURE_2_CREATED | NO_REJECTION_ARTIFACT_ONLY |
| POSITIVE_READINESS | NOT_EXECUTED_CANDIDATE_STOP |
| STALE_READINESS | NOT_EXECUTED_CANDIDATE_STOP |
| BOUNDARY_SEMANTICS | NOT_EXECUTED_CANDIDATE_STOP |
| G3F4_H01 | OPEN |
| BLOCKER_COUNT | 0 |
| HIGH_COUNT | 1 |
| MEDIUM_COUNT | 0 |
| LOW_COUNT | 0 |
| REAL_ADAPTER_E2E | NOT_RESUMED_H01_OPEN; PRIOR_PARTIAL_EVIDENCE_PRESERVED |
| FROZEN_OPERATIONAL_PARITY | NOT_RESUMED_H01_OPEN; PRIOR_PARTIAL_EVIDENCE_PRESERVED |
| S10_S14_REAL_RUNTIME | NOT_RESUMED_H01_OPEN; PRIOR_PARTIAL_EVIDENCE_PRESERVED |
| ORIGINAL_INPUT_RUNTIME_PARITY | NOT_RESUMED_H01_OPEN; PRIOR_PARTIAL_EVIDENCE_PRESERVED |
| S13_COLD_RUNTIME | NOT_RESUMED_H01_OPEN; PRIOR_PARTIAL_EVIDENCE_PRESERVED |
| ALL18_NEGATIVE_MATRIX | NOT_RESUMED_H01_OPEN; PRIOR_PARTIAL_EVIDENCE_PRESERVED |
| REAL_ROLLBACK | NOT_RESUMED_H01_OPEN; PRIOR_PARTIAL_EVIDENCE_PRESERVED |
| CONCURRENCY_SEMANTICS | NOT_RESUMED_H01_OPEN; PRIOR_PARTIAL_EVIDENCE_PRESERVED |
| RESTART_RECOVERY | NOT_RESUMED_H01_OPEN; PRIOR_PARTIAL_EVIDENCE_PRESERVED |
| G3F_4_ISOLATED_POSTGRES18_REHEARSAL | HOLD |
| PROTECTED_DATABASE_CONNECTION | NO |
| PROTECTED_VOLUME_MOUNT | NO |
| PRODUCTION_SECRET_USE | NO |
| NEXT_GATE | G3F_4_REHEARSAL_TEMPORAL_BOUNDS_REVIEW |

Checkpoint branch: `checkpoint/package-0090-cloud-handoff`; commit local/remote equality and clean worktree are checked after this evidence commit. The artifact cannot contain its own final SHA.

Evidence: [raw samples and metadata](PACKAGE-0090-G3F-4-TIMING-SAMPLES.json), [candidate rejection, no fixture](PACKAGE-0090-G3F-4-FIXTURE-002.json).
