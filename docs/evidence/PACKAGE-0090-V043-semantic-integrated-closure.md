# Package 0090 V043 source promotion gate — 2026-10-13

**HOLD. Source promotion is NO. This tranche does not complete the requested semantic/integrated closure.** The exact V043 body can now be created transactionally in an isolated PostgreSQL 18.4 database with only its first fence excluded for qualification. That installation proof does not establish complete function semantics, an ACTIVE domain fixture, concurrency safety or an independent successful-operation witness.

Branch: `checkpoint/package-0090-cloud-handoff`. Audited input: `a34bcd0782d0b3c6cb895ab08b0ab46701224974`, equal to origin, clean tracked/staged/untracked state. `git fetch origin`, worktree inventory and protected refs were checked before mutation. Only Package-owned scripts and evidence, plus this bounded ADR/SPEC factual update, change. No migration source changes.

The current user tranche expressly permits fresh disposable qualification and the exact fence-only transformation. This is test execution authority only. No pre-existing independently governed canonical fence-removal authority was established. ADR comments and source interlock comments are not treated as that authority.

## Exact source and transformation

Source: `applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V043__create_governed_offline_field_proof_capability_composition.sql`.

| Representation | Identity |
| --- | --- |
| Git blob | `b398192a68a31c1e4f8ae4448655d215ca5b45fa` |
| Git LF SHA-256 | `b0ea86b6ba355fdf25fe09836bd4b75e4a4a2ad88ab7ef0e4724ca0d5a013e7d` |
| Working CRLF SHA-256 | `3301b254e883ae2ebf9e1d41036f15bc7839c1ae9e2404e692bc2ec864204109` |
| Git LF / working bytes | 2,406,380 / 2,426,865 |
| Lines | 20,485 |
| Top-level statements | 1,235 |
| DDL | 15 tables; 24 function definitions / 22 names; 4 triggers; 3 indexes |
| Other statements | 33 ALTER TABLE; 24 owner transfers; 1,119 GRANT/REVOKE; 12 DO; 1 SET LOCAL |
| Embedded role creation | Seven restricted NOLOGIN owners; separately created control owner required |
| Fence | First top-level DO, LF offset 893, 159 exact bytes; SQLSTATE 55000 |
| Qualification body SHA-256 | `6ad78ba61d70e803d2a878034aa7988b69b6374568f96949b2ef6c8defc7a8c7` |

The harness reads the full Git source, rejects drift against its fixed SHA-256, requires working CRLF-to-LF equality, requires the unique exact fence to be the first parsed statement, removes that span only and reconstructs the original bytes by reinsertion. Remaining ASTs must match after ignoring four parser position fields (`location`, `arg_location`, `rexpr_list_start`, `rexpr_list_end`). No SQL text, literal, type, security option or expression changes. The derived body exists in runner memory/private scratch context, never in the canonical migration directory. The Flyway resource copy contains **only V001–V042** and the Java endpoint guard refuses any other count/version.

Static parser: pglast v8.5. Its grammar/AST is not PostgreSQL 18.4 execution evidence. Native server: `PostgreSQL 18.4 (Debian 18.4-1.pgdg13+1)` on Linux amd64. Both representations' SHA-256 values above are distinct from Flyway signed CRC32 checksums.

## Disposable execution proof

[Final raw observations](package-0090-v043-source-closure-release-gate/qualification.json), [Flyway log](package-0090-v043-source-closure-release-gate/flyway-042.txt), [body log](package-0090-v043-source-closure-release-gate/qualification-body.txt), [native build](package-0090-v043-source-closure-release-gate/native-build.txt).

The runner creates a UUID-named project, fresh network, fresh volume and fresh container from the repository's pinned builder image `sha256:07fc165de5bb569d822460e2df645c5489f99220fc2cb16c86596d39db394561`. The only TCP binding is inspected as `127.0.0.1` with one ephemeral port. The Java helper independently rechecks the exact container/image/labels/mounts/binding immediately before JDBC. Existing containers, volumes, repository DB settings and production credentials are never reused. The native build container has network `none`; no package/crypto download occurs.

Exact V001–V042 Git bytes are independently compared with frozen commit `19131bb9cd655312252c8c83f0f78e7c0742274f` and applied with Flyway 13.2.0. All 42 installed-rank/version/type/script/checksum/success values are independently checked against ordered source and a line-based signed CRC32 computation. The full history is unchanged after candidate qualification and after restart. No fake V043 success row is inserted.

The canonical source is submitted only for a **denial probe** inside a transaction: its first statement raises 55000 before DDL. Canonical migration execution was not completed and no canonical V043 schema/history installation is claimed. The derived body then commits as a qualification transaction, not as a Flyway migration.

Five isolated prerequisite attacks deny and roll back: PUBLIC schema CREATE, unsafe creator defaults, wrong crypto schema owner, PUBLIC native EXECUTE, wrong HMAC volatility. All retain the pre-body control-object count. These establish prerequisite rejection and transactional rollback, not failure injection inside governed multi-write operations.

The post-body catalog observes all 24 offline functions and 15 control tables owned by `flooow_offline_control_owner`. Four fresh LOGIN NOINHERIT/NOSUPERUSER/NOBYPASSRLS service-class test identities and a PUBLIC-equivalent test login receive only the test-assigned wrapper EXECUTE and public schema USAGE. They have zero memberships. These are **unbound, UNPROVISIONED** identities; they are not immutable-slot ACTIVE identities.

All 18 wrapper signatures explicitly deny typed NULL inputs with P0017 (they are not STRICT skip functions). Non-NULL synthetic bootstrap requests also deny with P0017. PUBLIC and all three wrong service classes fail with 42501 for each signature. Four direct service connections cannot SET ROLE postgres/any of eight owners, read the crypto/key surface, create a public helper, or SELECT/DELETE any of 15 control tables. No service behavior uses a postgres SET ROLE shortcut. This does not prove successful authentic-slot behavior, temp-schema poisoning across successful paths, all effective grants or all 68 reachable function contexts.

An independent post-campaign SQL observation finds zero rows in every control table, including policy; no receipt, activation or authority is emitted. Restart changes postmaster start time while preserving system identifier, full history and empty durable control state. A new auditor-class login still denies. This is **bootstrap restart proof only**, not ACTIVE incarnation/generation/replay qualification or the eleven-frame integrated witness.

## Installed crypto proof and limit

The current native C/control/SQL/Makefile bytes are hashed and rebuilt without network installation. Full native binary SHA-256 reproduces the approved repository rehearsal pin `5aeedcdb693442b7738b6f33604e059094f584af29d1879bf35482ca06ef63b5`. This is the dual-function native library, not the older comparator-only pin. Observed build/runtime linkage: PostgreSQL 18.4, OpenSSL 3.5.6, `libcrypto.so.3`. Both extensions are installed directly by postgres: pgcrypto 1.4 and flooow_offline_mac32 1.0, in offline_crypto. The captured pre-body catalog has 39 crypto functions, with Q-only non-owner binary HMAC/comparator access, owner-only text HMAC/Ed25519 and no PUBLIC access. V043 later grants its approved V bridge; the pre-body crypto catalog must not be mislabeled a complete post-body ACL snapshot.

Twenty actual native cases cover RFC 4231 HMAC, independent Python-standard-library HMAC expectations for empty/wrong-key inputs, exact/bit-flipped MACs, 31/32/33-byte lengths, NULL precedence, RFC 8032 Ed25519 verification, invalid signatures/context, malformed SPKI, wrong algorithm, trailing material and truncated signature. SQL NULL remains NULL; malformed non-NULL native inputs raise 22023; invalid well-formed signature returns FALSE. These prove the listed ABI/vector behaviors only. No SQL timing experiment is presented as proof of constant-time behavior. Complete independently approved member/provider provenance, every caller-context outcome and full integrated native-health qualification remain open.

## Deterministic source classifiers

[Call classification](package-0090-v043-source-closure-release-gate/call-classification.json), [corrected call groups](package-0090-v043-source-closure-release-gate/call-shapes.json), [operator census](package-0090-v043-source-closure-release-gate/operator-census.json), [source lock graph](package-0090-v043-source-closure-release-gate/lock-order-source-graph.json).

Continuation-13's 15,513 call occurrences and 175 groups cover the expanded 68-function source corpus, including frozen callees; they are not a V043-only denominator. Four `convert_to(NULLIF(all_names[field_tag],''),'UTF8')` arguments were incorrectly classified bool. The exact V043 declaration is text[], the subscript yields text, and native NULLIF/convert_to observations corroborate text/NULL behavior. A bounded successor corrects those four argument candidates, mechanically regroups all occurrences into **174 groups**, and preserves every historical artifact. No other candidate type is promoted to authoritative resolution.

The installed PostgreSQL parser accepts 146 of 174 **typed-NULL probe** contexts and records function/operator OIDs from pg_rewrite. The other 28 include special aggregate syntax, record/void view restrictions, nominal record vs exact composite types and unqualified helpers under the intentionally fixed test path. These are diagnostics, not 28 source defects. Typed NULL does not preserve every source literal/cast/caller/security/authority context. Full semantically bound groups remain **0/174**, never 146/174.

The reproducible census enumerates **23,135 A_Expr occurrences** once per original SQL statement in the same frozen 68-function corpus: 21,701 ordinary OP, 853 DISTINCT, 88 IN, 69 OP_ANY, 407 NOT_BETWEEN, 8 BETWEEN, 8 NULLIF, 1 NOT_DISTINCT. Paths/provenance are retained in a deterministic compressed ledger. Implicit casts, DDL/index/CHECK and runtime operators keep the **full operator denominator UNKNOWN**. Occurrence enumeration is not semantic equivalence proof.

The source graph retains 109 explicit row-lock sites across 30 functions: 95 UPDATE, 14 SHARE. Its conservative relation-order union has a potential strongly connected component among command_principal, integration_connector_progress and integration_organization. Branches/calls/loops, actual row identity, advisory/FK/index locks and transaction boundaries have not established feasibility; this is neither a proved deadlock nor a proved safe global order. `LOCK_EDGE_CYCLE_UNEXPLAINED=UNKNOWN` remains explicit.

## Current gate matrix

| Gate | Latest evidence / what is proven | What is not proven / exactly what closes it |
| --- | --- | --- |
| Exact input and fence | Full parse, fixed source/body hash, reinsertion + AST equivalence, canonical denial; YES for this boundary | No canonical fence-removal authority or successful migration execution |
| B01 exact calls/operators | Four-site NULLIF correction; 174 groups; installed parser diagnostics; 23,135 operator AST sites | All grouped source-context overload/cast/search_path/security/ACL/STRICT/result/authority bindings; 174 groups remain unbound |
| B02 NULL authority semantics | 12 primitive truth tables + 18 exact wrapper NULL denials | Every grouped predicate/consumer and seven SQL RETURN helpers; TRUE/FALSE/UNKNOWN/ABSENT/NOT_APPLICABLE propagation across successful trajectories |
| B03 security and identity | 24 function catalog observations; 240 restricted ACL negatives; zero memberships | Complete independently expected effective ACL/default/schema/object manifest and all 68 caller contexts, authentic-slot positives, temp/overload attacks |
| B04 DML/locks/control | Source-bound 28 writes, 109 lock sites; 10 UPDATE cardinality and nine immediate denial subproofs preserved | 28 full write semantics, actual global lock/isolation graph, two-/multi-session winner/loser/retry trajectories and 13 semantic control paths; complete counts remain zero |
| B05 installed crypto | Pinned build, 39-member pre-body catalog, exact extensions, 20 native vectors | Complete independently approved post-body member/ABI/effective-ACL/provider provenance and every required context/vector; contract approval is not installed completion |
| B06 full fixture/recipes | Reproducible hashed UNPROVISIONED runner with exact baseline, prerequisites, negatives, cleanup | Immutable ACTIVE full-domain recipes for 13 positive cases, scoped policy/control inputs, source rows, durable expected IDs/states/receipts and hashes; not production policy provisioning |
| B07 independent integrated witness | Eleven logical frames/605 model controls preserved; actual empty-state observation is bounded | Independent authenticated observer, durable CAS, native/SQL/OS/session/process/target correlation and all nine cross-layer bindings across successful committed operations |
| B08 ACTIVE restart/failure/adversarial | Same-volume bootstrap restart and continued denial; prerequisite rollback | ACTIVE generation/incarnation/replay, lost acknowledgement, revocation/terminal concurrency and all specified critical multi-write crash/CAS/commit boundaries |

There are eight **known open blocker groups**, not an exhaustive semantic defect denominator. No verified canonical V043 defect was found in this bounded executed campaign. HIGH/MEDIUM/LOW **full review counts remain UNKNOWN**; zero observed failures is not zero unknown defects. The analyser type error is corrected, not an open canonical SQL finding. No closed policy-bootstrap/model/structural finding is reopened. Production numeric policy values and real field operation are not pre-schema source-closure prerequisites.

## Tests and recipes

Final distinct native cases: **315 passed, 0 failed**: crypto 20; NULL primitives 12; wrapper NULL 18; prerequisite attacks 5; ACL 240; bootstrap caller denials 18; bootstrap restart 2. Five qualification-boundary tests pass normally and under optimized Python; count them once. **320 distinct tests total**. The 174 parser probes are classification observations, not assertion tests. Concurrency tests 0; integrated witness tests 0. Full integration coverage is not claimed.

Run from this Package worktree, with a **new output path**:

```powershell
python scripts/validation/package_0090_source_closure.py --parser-path C:\Users\xmz_r\AppData\Local\Temp\room-lineage-sql-parser --output <new-disposable-evidence-path> --execute-disposable
python scripts/validation/package_0090_call_classifier.py --output-directory <same-evidence-path>
python scripts/validation/package_0090_operator_census.py --output <same-evidence-path>\operator-census.json
python scripts/validation/package_0090_lock_graph.py --output <same-evidence-path>\lock-order-source-graph.json
python scripts/validation/test_package_0090_source_closure.py --parser-path C:\Users\xmz_r\AppData\Local\Temp\room-lineage-sql-parser
python -O scripts/validation/test_package_0090_source_closure.py --parser-path C:\Users\xmz_r\AppData\Local\Temp\room-lineage-sql-parser
```

Inputs: local pinned Docker builder image, Java/Javac, Python, hashed pglast v8.5 install, 141 hashed JVM dependency JARs, exact canonical V001–V043, native source, and frozen source-corpus artifacts. No downloaded crypto, real keys, production secrets or field authority. Outputs: raw logs, version/owner/function/role/ACL observations, actual test results, classified diagnostics, hashes and cleanup evidence. The runner destroys only its own label-verified container/network/volume in finally, and removes private scratch password/properties. Final cleanup is YES. Non-secret scratch can remain for debugging.

[Hash manifest](package-0090-v043-source-closure-release-gate/SHA256-MANIFEST.json) records Package scripts/resources and collected evidence. The raw run additionally records executable recipe hashes, parser files, native inputs/binary, exact migration source/CRC and all JVM dependencies. These freeze the executed **bounded** recipes; they do not claim full execution recipes ready. No hidden manual action is needed between native setup and this runner's asserted campaign. The final five-script recipe hashes match the executed raw record. Historical development attempts are preserved under `attempts/`; compilation and expectation mistakes are explicitly separate from the final passing campaign and do not inflate distinct tests.

## Release decision and protected integrity

```text
V043_SOURCE_SEMANTICS_READY=NO
V043_INTEGRATED_PROOF_READY=NO
V043_EXECUTION_RECIPES_READY=NO
V043_SOURCE_PROMOTION_READY=NO
V043_FENCE_REMOVAL_TECHNICALLY_ELIGIBLE=NO
V043_FENCE_REMOVAL_AUTHORITY_PRESENT=NO
V043_FENCE_PRESENT=YES
CANONICAL_V043_MUTATED=NO
CANONICAL_V043_EXECUTABLE=NO
V043_BODY_QUALIFIED_WITH_FENCE_EXCLUDED_FOR_TEST=YES
CANONICAL_V043_EXECUTED=NO
SHARED_DB_CONTACTED=NO
PRODUCTION_CONTACTED=NO
ROOM_OPERATIONAL=NO
EXECUTION_AUTHORITY=BLOCKED
RECOVERY_AUTHORITY=BLOCKED
```

Main remains `77d482c97a663a527dcacc85036c7577dfc92782`; Room remains `22181b5d821e343658928e6feaa06b96838757e2`; research remains `27019d7b3093b7a7d9aeb67d0c099756b13e005a`, both local/protected remote refs. V001–V042 and canonical V043 source remain byte-identical. No shared/production DB, protected worktree or existing container was used or mutated. Room remains internally engineering/schema/writer-composition ready, without slot, production manifest, activation or migration. Thus `ROOM_RELEASE_BLOCKED_ONLY_BY_V043_PROMOTION=NO`: legitimate slot and production manifest/full-chain qualification are also required by Room's existing gate.

NEXT (not executed): construct the complete source-context call/operator/NULL authority ledger and immutable ACTIVE full-domain fixture/independent observer recipes against this unchanged source hash, then run their restricted positive, concurrency, restart and failure campaigns. Keep all eight blocker groups and the canonical fence until their actual closure and separate canonical promotion authority.
