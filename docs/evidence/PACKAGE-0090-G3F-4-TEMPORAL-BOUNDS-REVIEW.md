# Package 0090 - independent temporal bounds review

CONTRACT_REVIEW=PASS. REHEARSAL_ONLY. Baseline: 33bc82b4e2417aef7394dd0fe4557d3e9285b7f1; local and fetched origin/checkpoint/package-0090-cloud-handoff equal, worktree initially clean. Prior H01 is OPEN/HIGH; previous observed maximum is 80684 us and previous fixture-2 artifact is a rejected-candidate disposition, not a canonical fixture.

Reviewed the actual ADR-0090 and SPEC-0090 sections 18,21.2,21.3,25, together with referenced role/readiness/binding and ACL contracts. ADR lines 77-81 preserve AUDITOR repeatable-read/read-only rollback, DB wall time and mandatory external watchdog; lines 133 and 238-244 distinguish numeric policy design from immutable expiry authority. SPEC citations below refer to the repository specification at this baseline, not a paraphrased prior report.

| Relation | Normative basis | Candidate |
|---|---|---|
| interval <= interval maximum | SPEC 21.2 line 586: every actual/maximum pair | 50000 <= 250000 PASS |
| interval maximum < health window | No universal cross-pair inequality found in ADR or SPEC 18/21.2/21.3/25 | Chosen fixture relation 250000 < 400000 PASS |
| health window <= health window maximum | SPEC 21.2 line 586 | 400000 <= 500000 PASS |
| health maximum < preflight TTL | No universal cross-pair inequality found; independent readiness checks may deny before receipt expiry (line 588) | Chosen fixture relation 500000 < 1000000 PASS |
| preflight TTL <= preflight TTL maximum | SPEC 18 line 241;21.2 line 586;25.3 line 2224 | 1000000 <= 2000000 PASS |

No unstated watchdog-to-TTL relationship is promoted to contract authority. SPEC 18 line 243 mandates attempt/execution/admission/delivery nesting and lock/statement/idle within transaction maximum;21.2 line 586 additionally mandates delivery safety margin strictly below delivery window. All unchanged fixture-1 fields preserve these rules. Existing approved Python codec validates all 28 positive finite signed-int8 durations and nesting, encodes exactly 29 fields and decodes/re-encodes the candidate without difference. The microsecond values are integral multiples of milliseconds where enforcement conversion applies; no upward rounding is needed.

| Parameter | Category A invariant | Category B governed engineering meaning | Category C authorized rehearsal value (us) |
|---|---|---|---:|
| watchdog interval | mandatory independent watchdog, finite approved bound | reviewed enforcement cadence | 50000 |
| watchdog interval maximum | actual <= independently approved maximum | maximum bounded enforcement interval | 250000 |
| watchdog health window | fresh protected heartbeat, future denied, stale fails closed | bounded stale-authority/freshness envelope | 400000 |
| watchdog health maximum | actual <= independently approved maximum | approved ceiling for that envelope | 500000 |
| preflight TTL | original immutable server-derived issuance/expiry, DB clock, no renewal | separately governed receipt lifetime | 1000000 (unchanged) |
| preflight TTL maximum | positive finite actual <= maximum; immutable version | approved ceiling, no fallback | 2000000 (unchanged) |

Category B values are security relevant, not freely adjustable runtime tuning. This authorization supplies exactly the four new fixture-only watchdog bounds. It does not authorize production values, optional watchdog enforcement, receipt grace, policy drift, authority widening or any Category A change.

SPEC 18 lines239-247 and21.2 lines586-588 require database-clock authorization, finite/checked bounds, watchdog/drain and exact immutable policy identity. SPEC 21.3 lines604-616 independently repeats scope/readiness/history/ACL/policy/key/MAC/DB-expiry checks and returns the original receipt on executor validation. SPEC 25 lines2210-2244 requires separately governed ADMIN provisioning under NOT_READY, independently approved complete bytes/digest and effective_from, committed audit evidence, new immutable version/new bindings, and retention of original receipt times. None is altered. Expiry equality is expired: issued_at <= database_now < expires_at. Live SQL heartbeat comparisons use age > health actual as rejection; equality is admissible only if all other guards pass. Health maximum is a policy validation ceiling, not a separate runtime grace window. These are source findings; runtime boundary proof remains pending its prerequisite timing gate.

The earlier maximum 80684 requires 3x=242052 us. Proposed interval maximum 250000 leaves 7948 us above that requirement (ratio250000/80684=3.098507759); health 400000 exceeds interval 50000+3x80684=292052 by 107948 us. These are empirical design margins, not statistical confidence or a production SLO. Expanded qualification must independently satisfy measured maximum <250000, 250000/maximum >=2, and400000 >=50000+2*maximum. The final maximum must therefore be <=125000 us. Values will not be silently increased.

Fixture-2 is defined only after this review PASS using the existing approved canonical codec. Canonical SHA256:28dd69e044c7646d51dd563ea85db96febe4024c816ba8a35b8b1703b65f9084. Prior rejected disposition remains available at baseline33bc82b4e2417aef7394dd0fe4557d3e9285b7f1 and its byte hash is recorded in the new fixture. Its replacement is explicitly authorized by this request. Fixture-1 and every historical HOLD report remain immutable. Fixture-2 definition supplies no database activation authority before the expanded timing gate passes.

Measurement plan: real DB-generated heartbeat and same-cluster observation clock;5000 warm,500 cold,2000 load4,2000 load8,1000 positive-realistic samples. Load uses actual Kotlin governed denials; the additional positive population includes real installed pg_catalog function/column/ACL projection, successful native Ed25519 verification, frozen V041 signature preimage and V042 authority intent/receipt construction with non-secret synthetic inputs. These pure positive operations require existing ADMIN privilege and create no operational effects; no SQL helper or service grant is added. Their work is included after heartbeat and before AUDITOR DB-clock observation. This workload does not assert accepted artifacts, frozen mutations, full catalog policy projection parity, S01 eligibility or a complete ceremony. Those stronger proofs remain gated separately.
