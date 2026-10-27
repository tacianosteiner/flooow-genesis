# Package 0090 — corrected S04 reachable expectation closure v2

The independent expected manifest is complete, matches two fresh owned PostgreSQL 18.4 targets, and is reproducible. Both targets passed the same 29,237 runtime assertions. The first-path mutable currentness denominator is **46 classes**, derived only after those matches. This closes expected graph qualification; `SEMANTIC_BOUND=NO` and live S04 eligibility remains unproven.

Branch: `checkpoint/package-0090-cloud-handoff`. Baseline: `3a9c82865111d4df974ea0d5c5b439f3c982dd26`. The delivery commit is the Git commit containing this report; no self-referential commit hash is embedded.

The machine evidence is in [package-0090-full-reachable-expectation-closure-v2](package-0090-full-reachable-expectation-closure-v2/). Start with [READINESS.json](package-0090-full-reachable-expectation-closure-v2/READINESS.json), [manifest v6](package-0090-full-reachable-expectation-closure-v2/expected-currentness-manifest-v6.json), [reproducibility](package-0090-full-reachable-expectation-closure-v2/reproducibility-v2.json), and [mutation denominator](package-0090-full-reachable-expectation-closure-v2/mutation-class-denominator-v3.json).

**Source boundary.** Canonical V043 is unchanged by this tranche and was never submitted or executed. Its first fence remains intact. Only the separately derived qualification body was manually applied inside each owned disposable target, after the exact 42 frozen migrations. No Flyway repair occurred.

| Frozen identity | Value |
|---|---|
| Canonical V043 Git-LF SHA256 | `007ab786c417c41e2b1702ebf3852cb70ff5c142fa3fde195385e04c6dde8b4a` |
| Flyway signed CRC32 | `1279591798` |
| Separate qualification body SHA256 | `50620e0a64da25c2c33a1060d5e8b632c34f04fbd67636eebf203f9b859c5d70` |
| Authorized return correction | `PACKAGE0090/S04/return-tuple-correction/v1` |
| Final manifest SHA256 | `9f8e5e9113b8cc857497984c57174326aa93940f61039471ba31b0526af05490` |
| Approved image identity | `sha256:07fc165de5bb569d822460e2df645c5489f99220fc2cb16c86596d39db394561` |

**Independent construction.** Expectations precede target observations. Inputs are corrected canonical SQL, the frozen historical 190-site/33-context ledgers, REL_18_4 catalog/source definitions, pinned image bootstrap/extension artifacts, the approved TEST bootstrap, the Flyway constructor/history expectations, and the governed specification/fixture/native design. Targets corroborate those expectations; their values are never substituted into the expected manifest. [Independent input freeze](package-0090-full-reachable-expectation-closure-v2/independent-input-freeze-v2.json) hashes provider files, normative inputs, validation recipes, parser/Python/JVM binaries, and cached JAR inputs. Both targets verified that vector before and after their callbacks.

PostgreSQL operator/function resolution follows the primary [operator rules](https://www.postgresql.org/docs/18/typeconv-oper.html), [function rules](https://www.postgresql.org/docs/18/typeconv-func.html), and frozen REL_18_4 `parse_oper.c`, `parse_func.c`, `parse_coerce.c` and `parse_collate.c`. Exact source and input hashes remain available under `provider/`. The PostgreSQL copyright notice is retained there.

The syntax parser is pglast 8.5 with grammar 18.6. It supplies syntax trees, not provider authority. Actual PostgreSQL 18.4 parse witnesses corroborate selected function/operator/cast/type/collation identities. Two separate derivations with Python hash seeds 17 and 91 produced identical artifact bytes before final release gating; see [derivation reproducibility](package-0090-full-reachable-expectation-closure-v2/derivation-reproducibility-v2.json).

**Closed expected surface.**

| Surface | Independently expected scope |
|---|---:|
| Historical expression sites | 190: 110 operators, 14 explicit casts, 66 other |
| Typed / untyped sites | 190 / 0 |
| Additional implicit/assignment coercion edges | 82 |
| All coercion edges including explicit casts | 96 |
| Governed corrected return casts, separate from historical denominator | 3 |
| Unknown literal consumers | 69 |
| Function context groups / call instances | 33 / 45 |
| Polymorphic call instances | 3, preserving `int8[]` and `text[]` instantiations |
| Reachable full function identities | 411: 403 builtins, 2 canonical PL/pgSQL, 6 native/dispatch interfaces |
| Function resolution candidate signatures | 509 |
| Builtin type selection metadata | 193 |
| Expanded builtin types / generated composite and array types | 61 / 40 |
| Logical relations | 20: 19 tables, 1 view |
| Additional internal TOAST tables | 16 |
| Total relations including TOAST | 36: 35 tables, 1 view; no matviews or sequences |
| Ordered logical columns | 204, plus three factory columns per TOAST table |
| Constraints | 233, including bootstrap PK-generated NOT NULL constraints |
| Triggers | 4 explicit, 76 internal RI triggers from 19 foreign keys |
| Logical indexes / internal TOAST indexes | 33 / 16 |
| Effective ACL entries | 25,466, each checking permission and grant option |
| Graph nodes / edges | 28,662 / 59,554 |
| Unresolved expected nodes / edges | 0 / 0 |

The source read roots, bidirectional FK integrity closure, observer metadata, and future eligibility rules are explicitly distinguished. `pg_roles` expands through its independently expected complete view tree to `pg_authid` and `pg_db_role_setting`, under the view owner's security context. Ordered column types/typmods/nullability/collations/default/identity/generated flags and column ACLs are checked. Generated rowtype/array and TOAST identities bind through parent catalog relationships; no generated OID is guessed.

Constraint naming and bootstrap construction are derived from REL_18_4 `heap.c`, `parse_utilcmd.c`, `indexcmds.c`, `bootstrap.c` and `system_constraints.sql`. TOAST construction follows [REL_18_4 toasting.c](https://github.com/postgres/postgres/blob/REL_18_4/src/backend/catalog/toasting.c). The ACL matrix includes the distinction in [REL_18_4 aclchk.c](https://github.com/postgres/postgres/blob/REL_18_4/src/backend/catalog/aclchk.c): a non-superuser TOAST owner can retain a grant option while system-class modification permission is denied. Dependent rowtype/array NULL ACL behavior comes from [REL_18_4 pg_type.c](https://github.com/postgres/postgres/blob/REL_18_4/src/backend/catalog/pg_type.c), independently of future default revocations.

Planner closure binds heap/btree methods, default families/opclasses, support/strategy members, operator commutator/negator/selectivity providers, aggregate transition/final/combine/serialization providers and function support identities. Candidate overload/variadic/default signatures and type category/preference metadata are checked separately from selected providers. The full cast surface is frozen. Seven rolled-back synthetic resolution probes cover pg_temp function shadow, public overload, operator overload, implicit cast lure, unknown literal lure, shadow type and caller search_path. These are resolution-assumption tests, not a currentness mutation or TOCTOU campaign.

**Rules versus eligibility.** Policy/readiness v3 binds deployment/incarnation, canonical policy/version/digest, one governed activation instant, independent approval and trusted audit terminal, history/ACL/manifest identity, native/guard proof, participant generations, header/original relationships, lifecycle and eligibility. Native v6 binds all seven managed participants plus HEALTH_GUARD/HOST_PLATFORM, enrollment, process/pidfd, binaries/libraries, channels, counters, nonce, actual completed work, dependency/catalog vector, original BOOTTIME freshness, epoch, guard decision/proof and future T9/T10 handoff. Generated values have independent authority and comparison rules; none is predicted or replaced with zero.

Audit v6 requires exact independently approved identities/context, PREPARED then reconciled COMMITTED, exact transaction/activation bindings, immutable hash chain and an independently retained trusted tip. Historical approval and destroyed-target proof retain their old source context and confer no current-target authority. A future corrected-source target needs independently governed authorization/linkage before activation. Pure parser checks use retained historical audit evidence only; no new audit writer, activation or approval was created.

The targets deliberately contain no ACTIVE policy, readiness, header or original attestation. Their live eligibility is **DENY**, not a successful positive S04 proof. A complete future rule contract is distinct from a currently valid native/guard/audit proof. PostgreSQL internal/C bodies are explicit opaque compiled-provider boundaries tied to immutable source/image/binary/library identities; this is not a global recursive SQL dependency claim. Actual loaded mapping/process health remains governed by the future native rule contract, not established by file hashes alone.

**Corrected return consumer.** Both targets independently reproduce old raw tuple SQLSTATE `42804`, then verify the corrected helper's `00000`, all 42 exact six-field rows, delivery order using WITH ORDINALITY, exact projected TEXT types and binary textual content, NULL preservation, UTF8 and qualified type shadow resistance. Only temporary qualification helpers execute. Canonical S04 never executes. SQL coercibility is not used as a substitute for tuple descriptor equality.

**Accepted validation accounting.** Each final target has the same 29,237 distinct `(group,name)` runtime keys, for 58,474 repeated executions. One distinct complete manifest-match assertion and one reproducibility assertion bring the reported total to **29,239 distinct tests, zero accepted failures**. The 22 additional strict post-proof integrity checks are recorded separately and do not inflate that total. Syntax compilation and parser inventory are not counted as runtime tests.

| Runtime group | Distinct assertions per target |
|---|---:|
| Expression typing | 232 |
| Operators | 110 |
| Casts/coercion consumers | 110 |
| Polymorphic | 3 |
| Types | 81 |
| Relations/views/generated type bindings | 323 |
| Defaults/sequences | 170 |
| Constraints/triggers | 371 |
| Planner support/candidate catalog surfaces | 968 |
| Function identity/candidate signatures | 1,116 |
| ACL/default/role checks | 25,542 |
| Resolution attacks | 7 |
| Policy/native/audit expectations | 109 |
| Return consumer | 11 |
| Foundation security contexts / caller identities / retained fixture | 70 / 4 / 10 |

[Target 1](package-0090-full-reachable-expectation-closure-v2/runtime-match-target-1.json) used normal Python; [target 2](package-0090-full-reachable-expectation-closure-v2/runtime-match-target-2.json) used `python -O`. Projects, containers, volumes and loopback ports are distinct. Every owned container/network/volume was removed, their absence was independently checked, and both credential files were unlinked. Unrelated running services were left untouched. [Post-proof integrity](package-0090-full-reachable-expectation-closure-v2/post-proof-integrity-v2.json) also checks the exact preflight case set and original 42 migration/fixture inputs. Its postprocessor is explicitly separate from the previously frozen target recipe vector.

The 16 development attempts and the first qualification prototype remain preserved. Eleven development attempts failed while exposing model/transport/probe issues; five passed. They do not count as final acceptance. These exposed column grants/grantor derivation, catalog C collation, compile-time BKI tokens, bootstrap PK NOT NULL construction, NOT IN/ALL normalization, OID JSON transport, system-class ACL masking, a probe table name and view implicit-cast normalization. Corrections were derived from canonical/primary source rules. No canonical source fix was made. Some development recipes evolved before final freezing; those attempts are diagnostic history, not fully replayable release proofs. The prototype pair was retained as development targets 14/15 when candidate absence coverage was expanded. Final target evidence was not overwritten.

**Findings and remaining boundary.** No open BLOCKER/HIGH/MEDIUM/LOW finding remains within this expected-closure/manifest/reproducibility scope. This is not a global Package 0090 review. Qualification generation, complete mutator coverage, final-consumer invalidation, live corrected-source authorization/readiness/native proof and 100µs feasibility remain unimplemented or unproven here. HOST_PLATFORM and the external host-root TEST audit store are explicit trust assumptions; no production WORM/HSM assurance is claimed.

Execution and recovery authority remain **BLOCKED**; Room is not operational. V001–V042, canonical V043, main, Room and global-commerce research refs are unchanged. No shared/production database was contacted. No readiness/header/original registration, auditor activation, canonical S04 execution, T10 implementation, currentness generator, mutation/TOCTOU campaign or 100µs benchmark occurred.

**Reproduction.** The release refuses regeneration of frozen expectations in place. With the frozen external prerequisites available, create a new owned evidence directory containing the unchanged three foundation inputs, then run `package_0090_active_foundation.py --parser-path <frozen-pglast-8.5> --directory <new-directory> --reachable-v2`. The callback verifies manifest/input hashes before and after qualification and the foundation performs ownership-checked cleanup in `finally`. `package_0090_reachable_v2_release.py verify` checks the frozen vector. `package_0090_reachable_v2_audit_close.py` performs strict post-proof audits before closure; use it for final closure so truthy cleanup lists alone cannot substitute for every successful removal.

The next technically determined action is to define and govern qualification-generation and final-consumer invalidation against all 46 classes and their complete graph scopes/mutators. **That next tranche was not executed.**
