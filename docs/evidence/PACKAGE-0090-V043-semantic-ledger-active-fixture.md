# Package 0090 — semantic ledger / ACTIVE fixture gate

2026-10-13. **HOLD; requested B01/B02/B03/B06 closure remains incomplete.** Branch `checkpoint/package-0090-cloud-handoff`, input HEAD/origin `0c6e9e99d4ea53807c86cabf52ad24121794dd35`, initially clean. Canonical V043 Git SHA-256 remains `b0ea86b6ba355fdf25fe09836bd4b75e4a4a2ad88ab7ef0e4724ca0d5a013e7d`; its first fence is unchanged. This campaign never submits canonical V043, even as a denial probe. It executes only the already-qualified exact fence-excluded body in a fresh disposable PostgreSQL 18.4 environment.

## Ledger and grouping

[Ledger](package-0090-semantic-ledger-active-fixture-final/semantic-ledger.json), [source contexts](package-0090-semantic-ledger-active-fixture-final/source-function-contexts.json), [consumer trace index](package-0090-semantic-ledger-active-fixture-final/consumer-traces.json), [readiness](package-0090-semantic-ledger-active-fixture-final/READINESS.json).

The prior `call-classification`, `call-shapes`, `operator-census`, `lock-order-source-graph`, `qualification`, `READINESS` and their hash manifest are preserved and checked. No old source/census or qualification result is replaced. The four approved NULLIF candidate corrections are reused. All 15,513 frozen occurrences retain original source/hash, function, control path, expression path, argument-expression hash and consumer parent hash. All seven expanded source files match their original Git byte hashes.

The 174 diagnostic groups were not proved to share caller/authority context. **96 groups span multiple source functions.** Deterministic caller/effective-context partitioning produces **818 candidate context groups**, 644 additional groups, zero merges, exactly one assignment per occurrence. Each record has a stable shape ID and references all its source occurrences. These are candidate partitions: cast/NULL/consumer equivalence **within** a partition remains unproved and can require further splitting. 818 is the current recorded denominator, not a certified final semantic-equivalence denominator. No group is BOUND.

All 15,513 structural source paths map deterministically: 14,912 exact corpus paths and 601 relocations of redundant `SelectStmt` type wrappers in bare set-operation members. This removes a serialization ambiguity without changing SQL/AST semantics. Only that known structural wrapper is skipped; arbitrary absent keys still fail. Source/candidate schemas and hashes remain distinct. Structural consumer paths are recorded for all occurrences; semantic consumer propagation and authority consequences remain **0 proven groups**.

The security index is derived independently from ordered V001–V043 CREATE/ALTER OWNER definitions, not generated from the target. The union contains **70 contexts**: all 24 V043 function definitions plus all 68 reachable source functions, with overlap. It distinguishes source function, schema, owner, DEFINER/INVOKER, search_path, strictness, volatility and provenance. INVOKER current identity is explicitly inherited/unproved; it is never flattened into a generic runtime bucket. SESSION_USER/authentic immutable slot remains separately unproved. This is a source/catalog subledger, not the complete table/helper/EXECUTE authority chain.

The NULL taxonomy records TRUE, FALSE, NULL, ABSENT_ROW, MULTIPLE_ROWS, DENIED, INVALID_INPUT, NOT_APPLICABLE, EXPIRED, NOT_YET_VALID, UNPROVISIONED, INACTIVE, REVOKED, TERMINAL and UNKNOWN with SPEC2/3/12/17/25 provenance. It does not assign every state to every function. Required per-consumer NULL/authority cases remain UNKNOWN, not zero. No new governed NULL-authority test is claimed from the previous primitive truth tables.

## Validator behavior

[Integrity result](package-0090-semantic-ledger-active-fixture-final/validator-integrity.json): PASS, 15,513 occurrences, 818 groups, no missing or duplicated assignment, known source signatures and trace references.

[Closure result](package-0090-semantic-ledger-active-fixture-final/validator-closure.json): **DENIED, exit 1**, listing all 818 exact UNBOUND shape IDs plus three gates: ACTIVE fixture, complete effective ACL manifest and authentic positives. That is an expected gate rejection, not a passing semantic proof. The validator rejects fabricated BOUND flags lacking mandatory dimensions, grouping/runtime proof, consumer semantics, state coverage and verified matching SEMANTIC_CALL evidence. Catalog observations cannot substitute for that evidence. Nine mutation/unit tests cover omission, duplicate assignment, unknown signature, absent consumer, forged BOUND, unproved golden-to-ACTIVE promotion, structural wrapper mapping and SQL literal escaping.

## Independently expected ACL and actual catalog

[Expected source/SPEC manifest](package-0090-semantic-ledger-active-fixture-final/expected-acl-manifest.json), [native observations](package-0090-semantic-ledger-active-fixture-final/foundation-runtime.json).

The V043 GRANT/REVOKE AST and normative SPEC exact column rows independently yield the same **1,040 role/relation/column/privilege tuples**. The freshly installed target's explicit column ACL set equals them exactly, including all seven restricted Package owners. The expected set is frozen before target inspection. Every source operation has canonical file/hash/ordinal provenance. This closes that column submanifest only; it does not establish all schema/table/function/sequence/default/PUBLIC/effective paths or authentic ACTIVE caller behavior.

Actual PostgreSQL catalog properties for all **70/70** source contexts match independently expected owner, security mode, strictness, volatility and exact search_path. Actual function OIDs/signatures/ACLs are captured. These installed-property checks do not count as 70 fully proved security contexts: helper/table dependency effects, every effective grant path and ACTIVE attacks remain open.

Four fresh test logins are independently connected with SESSION_USER=CURRENT_USER equal to the expected name, actual pg_roles OID, LOGIN/NOINHERIT, no privileged attributes and zero memberships. Only source-assigned wrapper EXECUTE and public USAGE are granted. Each denies control-owner SET ROLE and raw binding SELECT. No postgres SET ROLE session is presented as caller proof. There is no immutable ACTIVE slot/header yet, so these are actual identity preparation, not authentic positive wrapper operations.

## Immutable fixture foundation and gaps

[Fixture manifest](package-0090-semantic-ledger-active-fixture-final/active-fixture-manifest.json), [positive matrix](package-0090-semantic-ledger-active-fixture-final/positive-wrapper-results.json).

The manifest mines existing approvals instead of inventing inputs: fixture-1's full 29-tag policy, approved TTL 1,000,000us/maximum 2,000,000us, retained ML/Omie rows, and the existing codec goldens. A separate Python codec reconstructs the canonical policy frame and reproduces SHA-256 `e840fcadac2d5198a91cdb7b2345a31d4776cb3ead6e8b697391a4461a1a253d`. Production numeric approval/provisioning remains NO. No production secret or field authority is created.

All approved retained rows load transactionally with frozen constraints into nine tables: organization, connections, progress, page commits, ML observation, registry, promotion, Omie base and Omie V3. The explicit bytea page key uses decode(hex), while the Omie semantic fingerprint remains text. Nine exact row-count checks pass. The first development loader attempt incorrectly used ASCII hex for bytea; that attempt rolled back, is preserved, and the encoding defect is corrected. Approved values and canonical migrations were not changed.

There are **12 required component categories, four complete input declarations and eight missing runtime/authority components**. Four present declarations are policy input, retained rows, codec goldens and service-identity recipe; they are not four ACTIVE runtime components. The eight gaps are:

1. Fully bound immutable live header/lifecycle from actual slots and canonical bytes.
2. Independently expected readiness/history/complete effective ACL manifests.
3. Independently observed native enrollment/participant functional health.
4. Approved live runtime clock/windows and immutable activation metadata.
5. Original verified signed attestation and expected commitment.
6. Disposable key custody, actual MAC/signing inputs and erasure recipe.
7. Canonical authority/intent/consumption/admission lineage.
8. Independently expected durable receipts/states/audit for all thirteen trajectories.

Each category carries exact approved value/hash where available, provenance, TEST_ONLY scope, production_authority=NO and one of the requested approval/derivation classifications. No gap is labeled NEEDS_PRODUCTION_AUTHORITY. The native-health and runtime-window inputs remain separately governed test fixture requirements, not a CEO choice of implementation details. The retained golden epoch is not substituted for live DB time and signed windows are not silently renewed.

The existing full-domain contract explicitly requires complete typed SQL mapping and independently validated original binding/attestation/live readiness before positive execution. The native-health contract rejects alive/heartbeat-only eligibility and model flags as functional health. Consequently this foundation creates **no policy ACTIVE row, READY row, ACTIVE binding, fake attestation, downstream effect or receipt**. The zero-readiness assertion passes. A policy frame is available, but its administrative activation instant/audit and runtime readiness proof are incomplete. No random fixture UUID is generated. Random UUIDs name disposable infrastructure only; actual role OIDs are measured and recorded, not substituted by deterministic/model OIDs.

All **18 exact public wrapper signatures** are POSITIVE_REQUIRED across the complete Package fixture's corresponding scenarios. None is reclassified negative-only to lower the denominator. Proven authentic positives=0, unproven=18; ACTIVE crypto wrapper paths=0. Positive-context search-path/overload attacks remain unexecuted. This is not FULL_FIXTURE_READY or ACTIVE_FIXTURE_CONTRACT_READY.

## Executed recipes and tests

```powershell
python scripts/validation/package_0090_semantic_ledger.py --parser-path C:\Users\xmz_r\AppData\Local\Temp\room-lineage-sql-parser --output <new-ledger-directory>
python scripts/validation/package_0090_semantic_validator.py --directory <ledger-directory> --output <ledger-directory>\validator-integrity.json
python scripts/validation/package_0090_semantic_validator.py --directory <ledger-directory> --closure --output <ledger-directory>\validator-closure.json
python scripts/validation/package_0090_active_foundation.py --parser-path C:\Users\xmz_r\AppData\Local\Temp\room-lineage-sql-parser --directory <ledger-directory>
python scripts/validation/test_package_0090_semantic_foundation.py --evidence-directory <ledger-directory>
python scripts/validation/package_0090_semantic_evidence.py --directory <ledger-directory>
```

The --closure command intentionally fails while obligations remain. The native foundation runner refuses an existing output file, verifies input hashes, uses a new labeled project/container/network/volume with exactly one loopback binding, builds only approved local crypto in a network-none builder, verifies the pinned binary, applies exact V001–V042 via the existing independently guarded Java Flyway helper, and applies only the exact derived body. Its finally block verifies ownership labels, destroys only owned resources and erases private scratch connection secrets. There is no hidden SQL/manual setup between these automated steps. PostgreSQL18.4, OpenSSL3.5.6 and pinned native binary `5aeedcdb693442b7738b6f33604e059094f584af29d1879bf35482ca06ef63b5` are observed. The new runner/source inputs and 141 JVM dependencies are hashed. Full installed crypto/provider qualification remains NO.

**Final campaign: 93 native assertions and nine mutation/unit tests pass; 102 distinct tests, zero final failures.** Native groups: 70 security-context catalog checks, nine ACL checks, four independent login checks, ten retained-fixture/readiness checks. Classification for the requested testing report: semantic-ledger7, NULL-authority0, ACL/catalog79, positive-wrapper0, fixture16 =102. Repeated runs and the previous 320 tests are not added. Earlier loader failure is preserved as development evidence. No full concurrency, restart, multi-write failure injection or integrated witness campaign runs in this tranche.

## Scoped review and release decision

SCOPE_REVIEW=B01_B02_B03_B06. Four scoped blockers remain: complete source-context/grouping/runtime resolution (B01); per-consumer required-state/authority propagation (B02); complete independently expected effective ACL plus authentic positives/attacks (B03); eight missing ACTIVE fixture categories (B06). The nine tests review the new gate/loader boundary; they do not establish an exhaustive adversarial review of those four Package domains. HIGH/MEDIUM/LOW full scoped counts remain UNKNOWN. No global Package severity closure is claimed.

```text
B01_STATUS=OPEN
B02_STATUS=OPEN
B03_STATUS=OPEN
B06_STATUS=OPEN
B04_STATUS=OPEN
B05_STATUS=OPEN
B07_STATUS=OPEN
B08_STATUS=OPEN
KNOWN_BLOCKER_GROUPS_REMAINING=8
CALL_BINDING_SEMANTICS_READY=NO
NULL_SEMANTICS_READY=NO
SECURITY_FUNCTION_SEMANTICS_READY=NO
ROLE_ACL_QUALIFIED=NO
CALLER_BEHAVIOR_QUALIFIED=NO
ACTIVE_FIXTURE_CONTRACT_READY=NO
FULL_FIXTURE_READY=NO
ACTIVE_FIXTURE_RECIPE_READY=NO
ACTIVE_FIXTURE_RECIPE_HASHED=YES_BOUNDED_FOUNDATION_ONLY
CRYPTO_INSTALLED_QUALIFIED=NO
```

Main, Room and research refs remain respectively `77d482c97a663a527dcacc85036c7577dfc92782`, `22181b5d821e343658928e6feaa06b96838757e2`, `27019d7b3093b7a7d9aeb67d0c099756b13e005a`. No V001–V043 source, existing worktree/container, shared DB or production is mutated. Room slot remains NO, Room operational NO, execution/recovery BLOCKED. B04/B07/B08 closure was not attempted; B05 is not promoted.

NEXT (not executed): finish source-context binding/consumer state proofs and independently validated runtime binding/attestation/native-health fixture inputs, freeze the actual ACTIVE loader and approval provenance, then execute the smallest eligible auditor wrapper and expand the eighteen positive scenarios. Do not promote parser/catalog observations or JSON flags to authority.
