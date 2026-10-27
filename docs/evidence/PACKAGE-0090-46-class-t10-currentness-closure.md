# Package 0090 — 46-class T10 currentness qualification

**COMPLETE_CURRENTNESS_GATE=FAIL.** The 46-class denominator is unchanged. No class is certified: **0 PROVEN, 46 UNPROVEN**. Four confirmed governed actors exercised 14 committed mutation representatives without changing the external generation or transition state. The final observer was not built, following the explicit prerequisite in phase 27. No positive live eligibility, READY, S04 invocation or production currentness architecture is claimed.

Branch: `checkpoint/package-0090-cloud-handoff`. Baseline: `05eb515153036cb2da5657a7b3e9a74595d65848`. The delivery commit is the commit containing this report. Scope is TEST currentness qualification only, not global Package readiness.

The [gate](package-0090-46-class-t10-currentness-closure/currentness-gate-v3.json), [class coverage](package-0090-46-class-t10-currentness-closure/class-coverage-46.json), [direct mutation evidence](package-0090-46-class-t10-currentness-closure/direct-mutation-runtime.json) and [G2→T10 counterexamples](package-0090-46-class-t10-currentness-closure/window-g2-t10.json) retain the negative outcome. [READINESS.json](package-0090-46-class-t10-currentness-closure/READINESS.json) remains blocked.

**What was implemented.** A standalone TEST reference fence lives in private external files, outside canonical database schema. It uses an OS lock around participating journal operations, explicit STABLE/PREPARED/APPLYING/COMMITTED_PENDING_RECONCILIATION/ROLLED_BACK/UNKNOWN states, monotonically incremented API generations, deployment/incarnation context, unique transition IDs and fsynced hash-chained records. Missing metadata cannot silently initialize STABLE during recovery: initialization is explicit and permitted only with a fresh lock identity. A real child-process exit after PREPARED and actual journal-file loss were tested.

This lock constrains participants that acquire it. It does not intercept PostgreSQL statements or privileged file writes. Its model reconciliation evidence and terminal tip are not independently authenticated live transaction/approval evidence. Its conditional reference tuple uses explicit `MODEL_ONLY` markers; even its conditional match returns `live_eligibility=false`. None of these model values is promoted into native health, guard, approval or activation truth. Qualification generation is therefore **not ready** for full currentness.

**Mandatory mediation failure.** The final owned PostgreSQL 18.4 target used unchanged V001–V042 plus the corrected separately derived qualification body. The experiment sampled G0/G1/G2, then committed a reviewed direct mutation, then sampled the external fence again. The covered value changed while state remained STABLE and generation remained unchanged. A generation-only consumer retaining its earlier observation would accept the stale token; the actual overall gate remains DENY.

| Covered representative | Actual mutator/capability |
|---|---|
| Relation RLS | Catalog-proven table owner, via administrative SET ROLE |
| Function configuration | Catalog-proven function owner |
| Role inheritance | Governed postgres ADMIN |
| Implicit database-owner identity | Governed ADMIN changed the owned database owner |
| Role membership | Governed ADMIN granted/revoked an owner membership |
| Effective table ACL | Actual table owner |
| Future function defaults | Governed ADMIN |
| Default expression | Governed ADMIN on Flyway history |
| Index identity | Governed ADMIN renamed/restored an index |
| Trigger enablement | Actual table owner |
| FK deferrability | Actual table owner |
| Return/history content | Governed ADMIN changed/restored one frozen-history checksum |
| Column NOT NULL metadata | Actual table owner |
| Native module byte identity | Actual UID0 write in the owned disposable container |

The native probe appended a byte to the target module's writable-layer file, observed its changed SHA256 without a generation transition, and truncated it back to the original size/hash. The immutable image and repository native source were untouched. All SQL probe values and the module hash were checked after restoration. This does not claim complete restoration of generated catalog OIDs; the entire disposable target was subsequently destroyed.

The four confirmed actor identities are `postgres`, `flooow_offline_control_owner`, `flooow_offline_audit_owner`, and the native harness's container-root actor. They are confirmed positive capabilities, not an exhaustive authority map. Role attributes, database/table/function ownership and memberships were queried. Four operational identities were denied direct table ALTER. Ownership was not inferred from names. One development probe also demonstrated that ownership does not imply schema CREATE authority; that rejected probe was corrected and not counted as a valid mutation representative.

[PostgreSQL role documentation](https://www.postgresql.org/docs/18/role-attributes.html) distinguishes LOGIN and superuser privileges. NOLOGIN alone does not mediate a trusted administrator's existing SET ROLE path. SPEC-0090 line 11 and ADR-0090's clone-isolation boundary exclude hostile host/database administrators from the operational attacker model. These experiments are reviewed governed TEST transitions, not hostile-superuser attacks. They remain in scope. No one of the 46 classes was moved outside the threat model.

**Real database protection, limited scope.** An independently observed PostgreSQL SHARE relation lock prevented an owner DDL operation with SQLSTATE `55P03`. The lock was confirmed through `pg_locks`, rather than inferred from elapsed time. [PostgreSQL's locking rules](https://www.postgresql.org/docs/18/explicit-locking.html) define the conflicting modes and transaction lifetime. This proves the tested relation boundary; it does not prove protection for all relation fields, roles, functions, catalogs, native state or external writers. Consequently no entire class is counted as DB-protected or fully reobserved.

**46-class accounting.** [The freeze](package-0090-46-class-t10-currentness-closure/mutation-denominator-freeze.json) preserves every original CLASS_ID, OBJECT_CLASS, FIELDS, GRAPH_OBJECTS, operation, mutator and requirement, covering the original 28,617 mutable graph objects. The expected manifest remains `9f8e5e9113b8cc857497984c57174326aa93940f61039471ba31b0526af05490`.

The matrix retains all 46 rows. Fourteen have valid runtime mutation representatives and failed mediation assertions. The other 32 remain explicitly unexecuted/blocked; their planned rows are not valid runtime proof and are not counted as tests. All 46 remain UNPROVEN because a representative bypass and incomplete authority/window/mechanism coverage cannot certify a whole class. Proposed protection labels are fully classified; implemented complete protection is not. Class exclusion counts are zero, and unprotected classes are 46.

**Unclosed phases.** G2→T10 has concrete counterexamples. The other requested full-class windows, coherent multi-object observation, actual native/audit replay and reconciliation, and final decision tuple remain NOT_PROVEN. Journal fault models are not actual host-loss, native-replacement, functional-health or independent transaction-outcome proofs. No missing coverage is represented as successful denial testing. No blanket impossibility claim is made about a future capability-enforced mediator or complete lock strategy.

Prebinding is conservatively refused. A reproducible physical `(component, JSON-pointer)` classifier labels all **916,118** manifest/component leaf fields FINAL_REOBSERVED, with zero PREBOUND/PER_EPOCH/PER_EVENT fields. Component hashes, leaf counts and pointer-set digests make the classification reconstructible. This is classification, not proof that a final observer reobserved them or that currentness is safe. The final observer's query/generation/audit/native check counts are null because that observer was not built, rather than inferred as zero.

**Tests.** The final campaign ran with `python -O`. There were **155 distinct tests, 14 failures**, comprising 62 new distinct tests and 93 reused foundation assertions. There were 256 assertion executions. The 114 reference-model executions reduce to 13 distinct behavioral properties: repeated class IDs and identical state traces are not additional distinct tests. Only the final target/model results count below; retained development attempts do not.

| Group | Distinct tests |
|---|---:|
| Authority map probes | 5 |
| Reference transition fence | 2 |
| Reference generation properties | 2 |
| DB protection | 2 |
| Actual mutation/change-and-restoration checks | 28 |
| Mandatory mediation/G2→T10 checks | 14, all failed |
| Reference unknown outcomes | 4 |
| Reference reconciliation refusal | 1 |
| Reference replay fields | 4 |
| Prebinding correctness / decision coherence / final observer | 0 / 0 / 0 |
| Reused foundation ACL/security/caller/fixture checks | 93 |

The model tests establish only their stated reference behavior. They do not satisfy the full T10 unknown/replay/reconciliation gates. [Test accounting](package-0090-46-class-t10-currentness-closure/test-accounting.json) records that distinction and the exact failed assertions. Expected failing mediation assertions produce a nonzero campaign exit. No transport/setup error is hidden as a valid counterexample in the final target.

Development evidence is retained separately: an initially rejected index rename due to schema privilege, a probe corrected to mutate the exact database-owner class field, and the pre-hardening reference recovery run. Archived recipes accompany later development runs. Their results are not substituted into final acceptance. The final executed campaign/fence hashes were compared with the delivered files.

**Findings within this scope.** B01: direct governed ADMIN/owner/native-root mutation bypasses the external fence; a cooperative journal and last generation read do not close the final window. B02: full authority closure, the remaining representatives/window mechanisms, actual native/audit replay/reconciliation and coherent final observer qualification remain incomplete. There are two BLOCKER findings and no additional HIGH/MEDIUM/LOW findings. These are unresolved qualification findings, not production exploit or global readiness claims.

**Integrity.** All owned final container/network/volume removals were successful and resource absence was independently checked. Foundation credentials were unlinked. Only disposable targets were contacted. No private key was generated. Canonical V043 retains SHA256 `007ab786c417c41e2b1702ebf3852cb70ff5c142fa3fde195385e04c6dde8b4a`, signed Flyway CRC32 `1279591798`, and its original fence. Its derived body remains `50620e0a64da25c2c33a1060d5e8b632c34f04fbd67636eebf203f9b859c5d70`. V001–V042 and protected main/Room/research refs are unchanged. Previous evidence was not rewritten.

No production generation schema/table/column, READY, header/original registration, operational auditor activation, canonical V043/S04 execution, promotion, Flyway repair or 100µs benchmark occurred. Execution and recovery remain BLOCKED; Room remains non-operational. The hard stop applies despite FAIL.

Next, **not executed**: govern an enforceable capability/mediation boundary for direct ADMIN/owner/host changes, complete actor/field coverage for all 46 classes, and rerun all required windows before building or certifying the final observer. No 100µs pipeline or optimization tranche follows this failed gate.
