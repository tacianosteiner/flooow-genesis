# Adversarial counterexamples and actual mechanics

Branch `checkpoint/package-0090-cloud-handoff`; accepted inspection checkpoint
`f9dc0c9abddfc23f33a795f50c45472f06e02b2a`. No ADMIN promotion, policy provisioning,
V6 T0/key/SIGN, TREG R3, runner, new authority or main merge. All source pins are in
[SOURCE-SHA256.json](SOURCE-SHA256.json). Canonical V6 projection matches f9; all nine registration rows absent.
This is a prerequisite review, not a closure claim for operational readiness.


32 offline counterexamples PASS: actual/max/window conflict, no maximum grace, independent
receipt/freshness semantics, self-authorship, wrong deployment/incarnation/epoch, old sequence,
missing marker/roster/mandatory enrollment/signal/supervisor/drain, future/stale/rollback clocks,
overdue loop and fresh projection without real observation. The valid model case has fictional
complete evidence; it cannot attest a real host. Existing policy codec suite:10 tests PASS.

Two valid profiles with the **same Java phase implementation**, PG18.4 image/JVM/native-source
and exact fixture policy/DDL are retained; their dependency-classpath orchestration differs.
Run1 used the earlier private dependency closure; run2 resolves the repository test runtime
classpath offline through Gradle. Run2 is the committed reproducible harness. Per-run metadata
and distributions are retained alongside the pooled200 samples;20 warmup samples are excluded
from percentiles but retained raw. Earlier setup/compile failures and the provisional output-inclusive
timer revision are not counted as passing profiles and remain private. No latency tail is discarded
from the two accepted populations. No private key is serialized, logged or persisted; each fixture
generates a fresh memory-only key and signs once. All fixture databases/containers are removed.

Measured: actual V001-V042 Flyway schema, real V040 lineage/append functions/triggers, extracted
15 V043 table definitions/FKs and original signed-input trigger, real Ed25519/JCA and PostgreSQL
OpenSSL native verification, seven-row V043 staging, deferred constraints, real commit and fresh
locked query-first nine-row projection. Fenced V043 was never executed or edited.

Limits: synthetic domain evidence and NOLOGIN slot fixtures; guard timing is approval-expiry
predicate only, not complete policy/host/role/domain guard. No operational wrapper/ACL acceptance,
supervision, adversarial lock contention, JVM stall, generation restart, ambiguous-COMMIT injection
or full recovery proof. Writer connection/startup/migration/provider warmup is outside recorded
transaction setup. Total includes phase orchestration, excludes console formatting/output.
The same guarded sequence is not certified as a real ceremony. Short duration cannot authorize
a shorter window, larger policy or100us watchdog. Nearest-rank p99 from200 samples is empirical,
not a confidence bound, worst-case guarantee, SLO or commit safety margin.

| Component | p50 us | p95 us | p99 us | Maximum observed us |
|---|---:|---:|---:|---:|
|transaction_setup|1069.800|2001.500|4541.500|6253.000|
|advisory_locks|832.400|1851.100|5879.900|7472.500|
|t0_capture|917.300|2137.500|6069.300|11926.300|
|ed25519_key_generation|562.200|936.800|1402.700|3559.100|
|spki_fingerprint|30.800|60.400|158.900|350.300|
|v040_staging|7784.200|18491.000|30975.100|134195.200|
|manifest_encoding|269.900|631.500|1704.600|3208.600|
|plan_fingerprint|55.800|132.600|345.200|688.100|
|pre_sign_guard|886.200|2176.300|4428.100|5553.200|
|sign|1090.900|1787.600|2134.600|2982.500|
|jca_verify|1134.900|2067.100|2577.900|5740.800|
|postgresql_verify|1332.400|2524.700|4337.500|4896.200|
|v043_staging|7053.000|17799.600|34496.900|40711.700|
|consistency_queries|1779.300|3792.800|10657.100|17113.300|
|pre_commit_guard|803.700|1879.100|4522.700|7947.700|
|commit|768.300|1691.600|2975.000|7912.000|
|query_first|16381.500|32992.000|59115.000|123145.100|
|total_us|45060.500|88124.500|120445.700|288051.800|

Reproduce final-harness mechanics: `python scripts/validation/package_0090_ceremony_mechanics.py`.
It creates only its own loopback/tmpfs fixture, requires exact PG18.4 image and alternate DB/system identity,
uses offline build dependencies, applies migrations only through042, executes no service/production path,
and removes its container/anonymous volumes in finally. Source compilation and110 warmup/measured
iterations succeeded for the final source; the pooled report includes the earlier equivalent100 samples.
