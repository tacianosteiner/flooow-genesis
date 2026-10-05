# Package 0090 - timing and JDBC 08006 forensic diagnosis

**STATUS: diagnostic completed; G3F.4 HOLD; H01 OPEN/HIGH. No temporal qualification or fixture provisioning.**

Baseline 0c4bd74b1ca08fe36fe18eb50aefe912b14f4f98 was verified against fetched checkpoint origin; worktree was clean before prepared diagnostic files. All previous HOLD evidence and fixture definitions remain byte-identical.

The corrected instrumented run completed 9500 real PostgreSQL DB-clock observations, including 5000 load4 iterations with no observed 08006 and no captured exception. This is non-reproduction in one awake-controlled run, not proof the historical failure cannot recur. No positive S01-S18 or eligible continuous-watchdog ceremony was executed.

| Population | N | Min | p50 | p90 | p95 | p99 | p99.9 | Max | Mean | Sample SD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A_warm_persistent | 2000 | 722.000 | 996.000 | 1475.000 | 1733.000 | 2687.000 | 6603.000 | 12612.000 | 1125.782 | 493.467 |
| B_cold_after_heartbeat | 500 | 8291.000 | 10370.000 | 13458.000 | 15577.000 | 32023.000 | 63234.000 | 63234.000 | 11358.776 | 4460.567 |
| C_cold_before_heartbeat | 500 | 1362.000 | 1713.000 | 2309.000 | 2674.000 | 3914.000 | 11189.000 | 11189.000 | 1863.198 | 621.025 |
| D_both_setup_before_heartbeat | 500 | 1583.000 | 1973.000 | 3837.000 | 4731.000 | 6186.000 | 7536.000 | 7536.000 | 2404.884 | 1002.086 |
| E_idle_physical_reuse | 1000 | 775.000 | 1637.000 | 3093.000 | 3391.000 | 4285.000 | 7190.000 | 9008.000 | 1837.794 | 923.923 |
| load4_diagnostic | 5000 | 806.000 | 1229.000 | 1769.000 | 2103.000 | 2945.000 | 5080.000 | 7977.000 | 1334.563 | 423.643 |

All durations are microseconds, empirical nearest rank; cold N500 p99.9 equals its maximum with insufficient extreme-tail resolution. Group order is A/B/C/D/E/load4, not randomized; telemetry, checkpoint I/O and host awake control can affect platform load. No production guarantee or causal benefit of load is inferred.

A. Historical 428349 us cold index 34, ADMIN 138/AUDITOR 139: phase cause UNKNOWN. Aggregate age/PIDs were retained, but exact timestamp, individual timers, waits and JVM telemetry were not. New outliers 54091/63234 us are dominated by composite getConnection startup; for63234 us sample, JDBC connect 50969.8 us, setup 938.3 us, cached backend lookup 3 us, client query 1398.7 us. Server setup log for AUDITOR 536: total 43865 us, including auth 22867 us and fork 535 us. Server auth is protocol wall time including client/network waits, not CPU-only cost; overlapping metrics must not be added. No phase is assigned retroactively to 428349.

B. Historical JDBC 08006 cause UNKNOWN. Original exception message/vendor/cause/nextException were not preserved. New primary Windows evidence shows Modern Standby entry 11:29:16.635Z, disconnected standby 11:29:36.937Z, exit 11:38:37.196Z; the prior driver ends 11:38:38.052530Z. Guard logs stop at 11:29:29.710Z. These prove host power-state correlation with the stalled load4 interval; exact TCP-close direction, timeout origin and Docker-forwarding mechanism are not proven. Historical Docker event retention returned empty and is not evidence of no event.

C. Causal relation between cold index 34 and load4 failure: NOT_PROVEN. No per-sample historical timestamp ties them to the same event. Do not infer PostgreSQL failure or Windows jitter from SQLState alone.

D. Cold-after is a synthetic one-update handoff diagnostic, not actual eligible S01 or a periodically refreshed watchdog. Concrete production composition uses four separate PGSimpleDataSource and on-demand physical connections; no real pool is constructed. ADR/SPEC require independent watchdog enforcement and protected freshness, not a client-synchronized heartbeat/reconnect protocol. Reconnection may consume the visible-marker age conditionally; newer independent updates and REPEATABLE READ visibility determine which timestamp is checked. See HEARTBEAT-MODEL-REVIEW.md.

E. The budget applies at each actual DB-clock predicate to the marker visible to that transaction. Work after that marker and before the check consumes that age. The standalone age query, full S01 duration, heartbeat checks and receipt expiry checks are distinct. Exact source points: outer S01 clock 6925/age 6929; private Q clock 4990/age 4995 before full live ACL/history work; final Q clock 6656 concerns receipt expiry/issuance, not another heartbeat-age comparison. No check ordering or contract is changed by this diagnosis.

MEASURED_OPERATIONAL_PATH_MAX_US=12612 (synthetic A/C/D/E proxy, not eligible S01); MEASURED_RECONNECT_PATH_MAX_US=63234; MEASURED_QUERY_ONLY_MAX_US=8948.700 (client query roundtrip, not server-only execution). Raw phase, GC/CPU/backend and correlated outlier metadata are in TIMING-PHASES.json.

No new outlier has a collection-count/time GC increment or a logged safepoint within its iteration. No unexpected backend/postmaster/container restart, OOM or socket failure is observed in the corrected measurement window;retained initial/outlier snapshots share one postmaster start and load4 retains the same physical backend PIDs, Docker state/restart count stays stable, and full server logs contain no fatal/termination/reset evidence. This does not establish those historical outcomes. Normal cold session disconnects and deliberate container start/stop are excluded from unexpected-failure classification.

Harness-only corrections: an initial instrumented attempt consumed 176078ms main-thread CPU at 190s elapsed inside the native CPU-load getter; its thread dump and logs are preserved, and its raw samples were lost on deliberate JVM stop. Console reported A2000/B500 completions, but they are not counted as retained observations. Corrected diagnostic uses ProcessHandle total CPU time and raw checkpoints every 100 samples. Docker logs initially captured only stdout; PostgreSQL logs were on stderr, so the exact retained window was recovered from both streams without repeating measurements. Original read rollback masking and abbreviated chain capture were hardened only in diagnostic tooling. Production adapter remains unchanged.

PASSWORD_ROTATION=PASS; ROTATED_ROLE_COUNT=5 distinct authorized existing roles; PASSWORD_ROTATION_SCOPE=EXACT_AUTHORIZED_FIVE_ROLES. Two PASSWORD-only rounds (10 statements) were necessary because the aborted attempt erased its plaintext credentials before the corrected run. No CREATE/DROP/RENAME/role attribute/membership/privilege mutation occurred. Both rounds separately captured equal pre/post non-secret state; identity/OID/name, all required attributes including rolconnlimit, memberships, owner dependencies/catalog owners, schema/function/table/column/sequence/type/database/large-object ACLs and effective rights, defaults, complete policy and migration history are recorded. No role credential or password-verifier value was queried or captured.

ROLE_IDENTITY_UNCHANGED=YES; ROLE_ATTRIBUTES_UNCHANGED=YES; ROLE_MEMBERSHIPS_UNCHANGED=YES; OBJECT_OWNERSHIP_UNCHANGED=YES; ACL_UNCHANGED=YES; DEFAULT_ACL_UNCHANGED=YES; POLICY_UNCHANGED=YES; MIGRATION_STATE_UNCHANGED=YES; ROLE_STATE_PRE_POST_EQUAL=YES.

NON_SECRET_AUTHORITY_FINGERPRINT_PRE=d697579bb78f8ecffbeb1407a100a2ef400bebd761967bfa6af8059c1379632c
NON_SECRET_AUTHORITY_FINGERPRINT_POST=d697579bb78f8ecffbeb1407a100a2ef400bebd761967bfa6af8059c1379632c
NON_SECRET_AUTHORITY_FINGERPRINT_END=d697579bb78f8ecffbeb1407a100a2ef400bebd761967bfa6af8059c1379632c

Only proven exact disposable project/image/volume/readonly bind was used; PG 18.4 UTF8 and current 127.0.0.1 port were verified before JDBC. Fresh secrets were private ephemeral files only. Logging configuration was restored, transient awake request released, both attempts ended with stopped disposable container and erased credential files. No protected DB/volume, production secret, fixture installation, SQL authority change, bound increase, G3G or main push/merge.

BLOCKER=0; HIGH=1; MEDIUM=0; LOW=0. H01_ROOT_CAUSE=UNKNOWN; JDBC_08006_ROOT_CAUSE=UNKNOWN. Evidence supports model-placement relevance and historical power-state correlation, not complete cause attribution. Historical fixture-2 remains FAIL; no H01 closure or G3F.4 PASS.

NEXT_GATE=G3F_4_REHEARSAL_TRANSPORT_MODEL_REVIEW. Next action: govern the visible heartbeat/check boundary against actual on-demand sessions and external watchdog refresh, preserving DB-clock predicates and RR visibility; specify a bounded eligible operational-path experiment and platform awake/lifecycle evidence before any separate numeric-policy review. No number or fixture-3 is proposed here.

Full server/Docker logs are retained losslessly as GZIP_BASE64_LOSSLESS fields inside08006-DIAGNOSTICS.json, with original byte count and SHA256. Decompression reproduces every line; this is storage encoding, not truncation/redaction. Readable correlated outlier windows remain in TIMING-PHASES.json. Decode with gzip.decompress(base64.b64decode(field["data"])) and verify the recorded SHA256.

Validation: final Java and Python compiled; offline exception-chain validation preserves primary/cause/next/suppressed/vendor code and bounds cycles; lossless log decompression verified; complete 9500 raw sample counts/statistics/session checks validated; complete exception/log retention and outlier correlation inspected; both password rounds and final non-secret fingerprint equality verified; previous source/evidence byte hashes unchanged; diagnostic JSON parsed; exact endpoint/stop/credential-erasure checks passed. Commit/push/fetched head equality is reported after checkpoint creation.
