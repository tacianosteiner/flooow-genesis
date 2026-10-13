# Package 0090 — ACTIVE fixture / first positive gate

2026-10-13. **BLOCKED; the first authentic positive was not executed.** This tranche prepares actual original TEST signing material, freezes the minimum reader expectation, tests the prerequisite boundary twice from empty databases, and identifies two concrete activation blockers. It does not establish an ACTIVE fixture. No model/success/health flag is used to bypass the precheck.

Branch `checkpoint/package-0090-cloud-handoff`; audited baseline/local/origin `a82bb8ccf352ba89510f52b3d9c3f1ecc3dee7d8`, initially clean. Canonical V043 remains SHA-256 `b0ea86b6ba355fdf25fe09836bd4b75e4a4a2ad88ab7ef0e4724ca0d5a013e7d`, first fence present. Neither canonical migration nor a canonical denial probe runs. Only the exact previously qualified fence-excluded body is applied transactionally in fresh isolated PostgreSQL18.4.

## Minimum path and expectation

Selected wrapper: `public.offline_read_history(uuid,bytea,uuid,text)`, **S04**, direct `test_0090_audit` LOGIN, REPEATABLE READ READ ONLY. Source location: V043 lines7028–7221. It crosses the authentic AUDITOR/immutable-slot/policy/readiness boundary and returns the complete ordered history. It requires no later claim, execution possession, command admission, delivery, issuance or decision effect.

[Frozen first expectation](package-0090-first-positive/first-positive-expectation.json) derives the six output columns and all42 rank/version/type/script/checksum/success tuples independently from canonical V001–V042 and signed line-based CRC32. It does not copy expected output from the target. Expected durable writes, audit writes, version increments and consumption are all NONE, from the stable read-only source contract. This is an expectation, not an observed wrapper return.

[Observed gate](package-0090-first-positive/first-positive-observation.json): precheck FAIL, wrapper invoked NO, positive PASS NO. Raw independent LOGIN/identity checks belong to preparation and are not presented as wrapper execution identity. No positive-context sibling or search-path attack runs without the valid ACTIVE prerequisite set.

## Reaudited gaps and approval graph

[Eight-gap matrix](package-0090-first-positive/fixture-gap-matrix.json), [approval graph](package-0090-first-positive/fixture-approval-provenance.json), [fixture status](package-0090-first-positive/active-fixture-manifest.json).

| Gap | Status | Proven preparation / missing closure |
| --- | --- | --- |
| G1 header/lifecycle | PARTIAL | Actual four role OIDs/names replace model slots; exact38-tag binding encoding; candidate public inputs frozen. Registration cannot commit without readiness FK parent. |
| G2 readiness/history/ACL | PARTIAL | Independent42-row history expectation;1040 exact column ACLs and70 catalog-property checks repeated. Full independently expected effective manifests/current readiness remain absent. |
| G3 native functional health | OPEN | Pinned crypto library and actual signature vectors pass. No complete independent participant enrollment/generation/functional-progress proof. |
| G4 activation/runtime windows | OPEN | Actual finite DB wall clock captured; original golden windows preserved. Independently approved policy activation instant/relative recipe, approval/change identity and durable ADMIN audit are missing. |
| G5 original attestation | PARTIAL | Actual TEST keypair, SPKI, signature, original preimage, digest/fingerprint and exact six-field commitment frozen; native valid/bit-flip/wrong-key/NULL checks pass. Expected-original SQL row cannot commit with its header until dependencies exist. No current authority or frozen V041 acceptance is inferred. |
| G6 custody | PARTIAL | Ed25519 custody lifecycle is tested and erased. Later preflight MAC key/lineage lifecycle remains incomplete; S04 has no direct HMAC/key call. |
| G7 authority lineage | OPEN | Independent direct logins are prepared; first R chain policy→readiness→header→slot remains incomplete. Intent/admission/command effects are not prefilled or required merely to force this reader. |
| G8 durable outcomes | PARTIAL | First-reader expectation frozen; no actual positive output. Other18-wrapper/13-trajectory expectations and outcomes remain unproved. |

Every graph node distinguishes APPROVED_TEST_ONLY, DERIVED_FROM_APPROVED_INPUT or UNAPPROVED, with source, consumer and authority boundary. No gap is labeled production-only. Existing approvals for the exact29-tag fixture-1 policy, TTL1,000,000us/maximum2,000,000us and retained VECTOR_1 material are reused; their numeric values are not changed. Current user phase7 permits generated immutable TEST signing material. That permission is not interpreted as policy activation approval or production signer authority.

**Blocker A — explicit activation approval/audit.** SPEC25.2/25.3/25.4 requires an independently approved finite effective_from and prior independent administrative approval with durable audit containing approval/change identity, actor, target, canonical policy/digest, activation instant and provisioning evidence. The golden approval supplies numeric policy/TTL values, not that activation instant or a reviewed relative DB-clock registration rule. Observing clock_timestamp() does not supply its missing approval. User phase5 explicitly requires the missing fixture decision to be recorded when the mechanism is absent. No policy row is inserted by assuming epoch or now is authorized.

The exact bounded engineering decision still needed is a TEST-only administrative fixture activation mechanism: either approved exact instant, or reviewed registration-transaction DB-clock recipe, with an independent approval/change identity and durable audit implementation. It changes no production policy and is not a business/CEO choice of timing values. Recipe identity and resulting runtime fixture identity must be hashed separately; existing signed windows cannot silently change.

**Blocker B — actual contracted functional health.** SPEC9/18 and the existing Native Health Contract/Design require independent current identity, enrollment/generation, freshness, authenticated channel, completed functional work and dependency/catalog binding. The design identifies seven managed participants plus independent guard/host root; it explicitly remains DESIGN_ONLY_NO_IMPLEMENTATION and `generation_implementation=NOT_AUTHORIZED`. Crypto load, valid signature, alive process or heartbeat alone is not that proof. Applicable native implementation/proof authority and actual independent functional observations remain unestablished. No READY/watchdog_healthy row is fabricated. No independently qualified first-path subset superseding the existing requirement was found.

## Actual generated original and custody

Public inputs are frozen before native validation/registration in each final run's `registered-fixture-manifest.json`; its actual scope is **TEST_ONLY_PREPARED_UNREGISTERED**, not a committed registration. Manifest bytes/digest remain exact VECTOR_1. The historical1970 validity window is preserved and is never presented as current authorization.

Signer identity is explicitly typed deterministic TEST UUIDv5 from deployment UUID, case, fixed input HEAD, V043 hash and generator hash; a governance UUID is not inferred to denote a signer key. Private key material is fresh OpenSSL Ed25519 randomness, not a public deterministic seed. The recipe and generated public fixture are separate immutable identities. Canonical signature preimage uses the frozen five-frame signature domain/algorithm/key/fingerprint/manifest digest. Expected original commitment uses the approved EXPECTED-SIGNED-ATTESTATION/V1 six-tag presence framing, UUIDs, lowercase digest/fingerprint and exact64-byte signature.

The newly tested reference uses integer days/seconds/microseconds, reproducing all three approved golden binding hashes exactly. The older auxiliary float conversion loses one microsecond at VECTOR_1 expiry and produces a different fingerprint. Only the new preparator's reference calculation changes; canonical SQL, approved goldens and the older reference file remain unchanged. Actual OIDs emitted as PostgreSQL JSON strings are explicitly converted to unsigned framing integers; model OIDs are never used.

Private files exist only in a0700 root-owned directory in the new container; PEM modes0600. Only trusted OpenSSL generation/signing processes read private material. Public DER/preimage/signature are exported as fixture evidence; PEM/private seed never is. An actual backend OS-user read fails. Both private keys and public temporary files are erased and absence of both PEMs verified before container cleanup. No production custody/HSM claim, no production key and no field credential exists. [Custody run1](package-0090-first-positive/run-7/key-custody.json), [custody run2](package-0090-first-positive/run-8/key-custody.json).

Native crypto checks execute as trusted administrative primitive qualification, **not** as an authentic positive service wrapper. Positive original signature returns TRUE; bit flip and actual wrong key return FALSE; NULL returns SQL NULL. They do not establish native participant health, current authorization or active crypto-wrapper progress.

## Actual registration boundary

The candidate header and independently supplied original tuple are attempted in one administrative transaction with REGISTERED lifecycle, without activating mutation authority. PostgreSQL rejects the header with SQLSTATE23503, constraint `offline_binding_header_fk1`: incarnation must exist in `offline_readiness`. All header/original/lifecycle counts independently reread as zero afterward. These are expected prerequisite-denial/rollback tests; they are not successful registration or critical-operation failure-injection closure.

This observed FK makes the dependency concrete:

approved activation/audit and valid policy prerequisites → independently validated readiness (never fabricated) → committed immutable header/original pair → authentic slot → eligible reader.

Setting arbitrary NOT_READY/READY data merely to satisfy the FK would not provide the governed metadata and would not close the missing authority. No partial state is mislabeled success.

## Runtime semantics and expansion

[Semantic bindings](package-0090-first-positive/first-positive-semantic-bindings.json): existing global818 candidate groups remain unchanged,0 BOUND,818 UNBOUND. No wrapper traversal occurred, so first-path candidate/unbound denominators are unobserved, not inferred zero; bound count0. First-path NULL/consumer and complete ACL gates remain NO. Existing source/catalog/LOGIN subproofs are distinguished from positive-context proof.

An additional precise source-corpus limitation is recorded: the prior68-function call census omits `offline_read_history`, although the70-function catalog union includes its declaration. A future actual S04 path requires an explicit source-call addendum and honest denominator update. No existing group is relabeled to conceal that omission.

[Expansion DAG](package-0090-first-positive/wrapper-expansion-dag.json) contains all18 exact source signatures, including the three claim overloads distinguished by argument count. It separates R readers from M eligibility and does not confuse a locking/projection begin wrapper with a proved durable write. Ordered mutation branches are S01→S13→S05/S06→S07/S08→S09/S10→S14/S15→S11/S12→S16→S17/S18, subject to every exact original/deadline/possession/delivery/authority condition. It is a source-derived plan, not an executed or globally qualified DAG.

## Reproduction and evidence

The foundation runner is explicitly versioned with optional `--first-positive-preparation`; no monkeypatch/hidden SQL or canonical instrumentation is used. Earlier evidence binds the former runner version at its recorded Git revision and is not rewritten. New final runs bind the current runner/helper/module hashes. Other existing corpus artifacts remain untouched.

Prepare a new output directory with unchanged `active-fixture-manifest.json`, `expected-acl-manifest.json`, `source-function-contexts.json` inputs from the preceding bounded foundation gate, then run:

```powershell
python scripts/validation/package_0090_active_foundation.py --parser-path C:\Users\xmz_r\AppData\Local\Temp\room-lineage-sql-parser --directory <new-run-directory> --first-positive-preparation
python scripts/validation/test_package_0090_first_positive.py --evidence-directory <evidence-root>
python scripts/validation/package_0090_first_positive_evidence.py --directory <evidence-root> --runs <first-run-name> <second-run-name>
```

Final runs [7](package-0090-first-positive/run-7/foundation-runtime.json) and [8](package-0090-first-positive/run-8/foundation-runtime.json) each use a new named/label-verified container, network and volume with one loopback binding and the pinned approved local builder. V001–V042 exact Git resources/Flyway baseline, reviewed local native build and exact derived V043 body are automated. No internet crypto install, existing/shared container, production credential, canonical V043 submission or false V043 success row. Native binary SHA-256 remains `5aeedcdb693442b7738b6f33604e059094f584af29d1879bf35482ca06ef63b5`; PostgreSQL18.4/OpenSSL3.5.6 observed. Only owned runtime resources are destroyed in finally; private scratch connection secrets are erased.

**102 distinct native preparation assertions pass in each run, plus six unit tests:108 distinct tests,0 final failures.** Repetition is not counted twice. Test report grouping: fixture29, ACL/catalog79, authentic positives0, ACTIVE sibling attacks0, semantic bindings0. Preparation/custody/prerequisite-denial behavior reproduces; ACTIVE_LOADER_REPRODUCIBLE remains NO because there is no ACTIVE loader or successful wrapper.

Four material failed attempts are summarized with original record hashes/cleanup/recipe identities: external command timeout of unestablished cause, float precision, JSON OID typing, actual missing-readiness FK. Full local records are retained at the path in `failed-attempt-archive.json`. They are not duplicated as historical trees in Git. Superseded passing preparation records are likewise retained locally. A recursive-delete operation was rejected by automatic policy; reversible archival preserved all data.

## Decision and next gate

```text
ACTIVE_FIXTURE_FOUNDATION_READY=NO
FULL_FIXTURE_READY=NO
FIRST_POSITIVE_EXPECTATION_FROZEN=YES
ACTIVE_FIXTURE_PRECHECK=FAIL
FIRST_AUTHENTIC_POSITIVE_EXECUTED=NO
FIRST_AUTHENTIC_POSITIVE_PASS=NO
ACTIVE_LOADER_REPRODUCIBLE=NO
FIRST_PATH_NULL_CONSUMER_COMPLETE=NO
FIRST_PATH_ACL_COMPLETE=NO
NATIVE_FUNCTIONAL_HEALTH_READY=NO
CRYPTO_INSTALLED_QUALIFIED=NO
B06_STATUS=OPEN
B01_STATUS=OPEN
B02_STATUS=OPEN
B03_STATUS=OPEN
GLOBAL_BOUND_CALL_SHAPES=0
```

Two scoped activation blocker groups are established. Full HIGH/MEDIUM/LOW scoped review remains UNKNOWN; a blocked precheck is not a complete global security review. No B04/B07/B08 campaign or global818 closure is attempted. No policy values, signing windows, frozen SQL, authority boundaries, ACLs or native assertions are weakened.

Main/Room/research refs remain `77d482c97a663a527dcacc85036c7577dfc92782`, `22181b5d821e343658928e6feaa06b96838757e2`, `27019d7b3093b7a7d9aeb67d0c099756b13e005a`. V001–V043 unchanged; no shared/production DB contacted. Room operational NO; execution/recovery BLOCKED.

NEXT (not executed): resolve the exact TEST activation/audit fixture approval and qualified native functional-health implementation/proof boundary; then reconstruct readiness and atomic original registration, require PASS precheck, execute S04 directly as auditor, and add/trace its actual source contexts before any BOUND promotion.
