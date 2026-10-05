# Package 0090 - final isolated rehearsal disposition

**STATUS: HOLD. Temporal contract review PASS; fixture-2 qualification FAIL; G3F4-H01 OPEN/HIGH.**

Observed maximum 428349 us exceeds authorized 250000 us. Ratio 250000/MAX=0.583636241, below 2.0. Required 2x=856698 us; headroom=-606698 us. Required health 50000+2xMAX=906698 us exceeds 400000 by 506698 us. The explicit user Section 5 STOP applies. No larger bounds are selected or approved.

The dataset is incomplete: 6529 successful DB-clock observations; load4 interrupted with JDBC SQLSTATE08006. This is not a complete expanded qualification or a claimed positive workload. A failed observed bound is already sufficient to reject this candidate, while incomplete data independently prevents PASS. The connection failure root cause is unresolved. No production latency, SQL authorization defect or crash is inferred.

| Population | Successful / required | Min | p50 | p90 | p95 | p99 | p99.9 | Max | Mean | Sample SD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| idle_warm | 5000/5000 | 2347.000 | 3741.000 | 5699.000 | 6968.000 | 13205.000 | 39000.000 | 66375.000 | 4296.106 | 2639.297 |
| cold_reconnect | 500/500 | 24887.000 | 35374.000 | 48910.000 | 58492.000 | 171556.000 | 428349.000 | 428349.000 | 40599.694 | 29641.378 |
| load4 | 1029/2000 | 2507.000 | 3379.000 | 4679.000 | 5689.000 | 14685.000 | 44083.000 | 93077.000 | 3973.254 | 3707.285 |
| load8 | 0/2000 | NOT MEASURED | NOT MEASURED | NOT MEASURED | NOT MEASURED | NOT MEASURED | NOT MEASURED | NOT MEASURED | NOT MEASURED | NOT MEASURED |
| positive_realistic | 0/1000 | NOT MEASURED | NOT MEASURED | NOT MEASURED | NOT MEASURED | NOT MEASURED | NOT MEASURED | NOT MEASURED | NOT MEASURED | NOT MEASURED |

All figures are microseconds. Percentiles use nearest rank; SD uses N-1. At cold N=500 the p99.9 equals the maximum and has inadequate extreme-tail resolution. Load4 figures describe only the partial 1029-sample population. Raw samples and environment metadata are in TIMING-QUALIFICATION-2.json. No missing population is treated as zero latency.

Fixture-2 was defined with the approved 29-field codec after contract review PASS; SHA256 28dd69e044c7646d51dd563ea85db96febe4024c816ba8a35b8b1703b65f9084. The canonical definition is retained with qualification FAIL and database_installed=false. Prior rejected disposition is preserved by baseline commit/hash reference. Fixture-1, historical HOLD evidence, V001-V042, canonical fenced V043, ADR/SPEC, wrappers and ACL authority are unchanged. Pre/post database snapshots match for the collected policy/role/readiness/function-ACL scope. Broader catalog snapshot tooling is compiled but not claimed as executed.

Only the proven exact disposable project/container/volume was contacted. PostgreSQL 18.4 and UTF8 were checked, with actual distinct ADMIN/AUDITOR JDBC sessions and fresh DB-clock ages. New rehearsal-only passwords were rotated only for existing postgres/four service roles; permissions/owners were not changed. The container is STOPPED and private plaintext password/properties files are erased. No protected database/volume, production secret, production policy, G3G, main merge or production deployment was used.

Required downstream artifacts record NOT_EXECUTED_TIMING_GATE_STOP: 200 positive S01 cycles; temporal negatives; fullS01-S18 ceremony; A/B matrix; rollback/ambiguous commit; barriers/concurrency; recovery after durable effects. Actual complete ceremonies=0. Deadlock/double-effect/lost-update/unauthorized-renewal recovery counts remain unknown, not fabricated zeros. Historical native/denial/prerequisite restart proofs do not replace these gates.

BLOCKER=0; HIGH=1; MEDIUM=0; LOW=0. Risk remains incomplete runtime evidence and an unqualified timing envelope, with unresolved 08006 under load. Final PASS and H01 closure are forbidden.

NEXT_GATE=G3F_4_REHEARSAL_TIMING_FAILURE_AND_08006_DIAGNOSIS. Next technically determined action is a bounded diagnostic design for the observed tail and connection failure, under new explicit execution authorization because Section 5 orders STOP. Preserve exact values and raw evidence; do not silently rerun/enlarge bounds, install policy or resume dependent runtime. Only after a newly authorized successful qualification and complete runtime proof can G3F_FINAL be reauthorized.

Validation: javac compiled the final driver; Python syntax compilation passed; canonical fixture decode/re-encode and SHA256 passed; raw counts/statistics and distinct physical backend checks passed; all evidence JSON parsed; prior disposition Git blob hash matched; historical byte hashes and collected pre/post snapshots matched; stopped container and erased credential files were verified. No positive-path runtime validation is claimed.

Branch: checkpoint/package-0090-cloud-handoff. Evidence baseline: 33bc82b4e2417aef7394dd0fe4557d3e9285b7f1. The final commit is reported by Git after committing these artifacts; no self-referential commit hash is invented.
