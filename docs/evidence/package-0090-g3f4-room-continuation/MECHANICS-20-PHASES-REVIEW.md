# Twenty separately measured phases — disposable mechanics only

ITERATIONS=100, WARMUPS=10 retained raw but excluded from percentile population.
Nearest-rank empirical statistics; no tail-confidence or worst-case bound.
This is an additional population, not pooled with the200 earlier samples.

| Phase | P50 us | P95 us | P99 us | MAX us |
|---|---:|---:|---:|---:|
|transaction_setup|1370.300|2179.300|2883.600|3163.200|
|advisory_locks|1341.500|2161.700|2731.100|3869.100|
|t0_capture|1376.100|2199.700|3116.700|4804.100|
|ed25519_key_generation|548.200|929.600|1160.600|1166.600|
|spki_derivation|9.500|24.100|46.800|65.100|
|fingerprint_derivation|15.300|50.000|73.800|667.600|
|v040_staging|11058.900|17869.300|19170.300|19656.200|
|evidence_binding|101.500|175.300|219.100|273.800|
|manifest_framing|161.700|328.500|395.300|519.600|
|manifest_digest|10.700|29.600|59.900|61.200|
|plan_fingerprint|59.700|128.500|155.100|581.600|
|pre_sign_guard|1341.900|2375.500|3039.900|3131.500|
|sign|984.000|1756.900|1915.600|2873.400|
|jca_verify|966.900|1924.900|2246.600|7754.700|
|postgresql_verify|1807.000|2773.400|3075.300|3245.800|
|v043_staging|9584.100|15549.600|16420.600|17879.100|
|consistency_queries|3183.500|5116.600|5831.400|13266.500|
|pre_commit_guard|1216.000|1939.300|2748.400|7148.700|
|commit|1148.100|1922.800|2847.500|3933.300|
|query_first|22005.200|33400.400|37729.600|40783.800|
|total_us|60416.700|91361.700|97028.800|98078.100|

New diagnostic sources preserve the prior sources and published evidence unchanged.
SPKI derivation/fingerprinting and manifest framing/digest now have separate timers;
evidence binding independently frames and fingerprints the repository EvidenceBinding
field order using synthetic inputs. Plan phase includes exact38-tag framing/hash and
signature-preimage assembly. V040 phase includes its actual lineage/authority routines.
In-transaction validation and fresh query-first both decode/re-encode the actual
manifest via the repository Kotlin ApprovalManifestCanonicalCodec, in addition to
nine-row projection/constraints. All110 iterations passed this independent codec check.

Correction/qualification of earlier evidence: the first harness's manifest used
generic23-field framing with a different order and placeholder evidence fingerprint;
its latency samples were valid for that generic mechanic, not canonical-manifest
parity. Its prior prose claiming an exact manifest shape was too broad. This
successor uses the CODEC source order and an actual round-trip; earlier artifacts
are preserved and never silently relabeled. The intermediate20-phase population
before the round-trip check is not this final population.

Still unqualified: canonical domain evidence, service roles/ACL/operational wrappers,
full policy/host guards, mandatory enrollment, contention, cold writer connection,
JVM stalls, supervision/restarts and ambiguous-COMMIT writer quiescence/recovery.
PRE_SIGN/PRE_COMMIT timings measure only the synthetic approval-expiry predicate.
Query-first is a real fresh connection plus locked projection, not ambiguous-COMMIT
qualification. Execution of these mechanics is not TREG R3 or a Room readiness gate.
No canonical V6 ID/T0/key/signature is used; fresh memory-only fixture keys sign once.
No private key is serialized; disposable containers/volumes removed. The canonical
container is read-only inspected and remains running in its prior state.

Reproduce: `python scripts/validation/package_0090_ceremony_mechanics_r2.py`.
Numeric latency cannot choose policy, shrink60s, widen2s or qualify100us watchdogs.
