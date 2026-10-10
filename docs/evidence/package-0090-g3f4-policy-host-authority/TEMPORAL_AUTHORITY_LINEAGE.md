# Temporal authority lineage — source roots, not nearest generated artifacts

Inspection HEAD: bd7ee39123e6186b6d6ce129eaa61c82e009773a. No policy change,
ADMIN execution, canonical T0/key/SIGN, R3, runner or research-branch mutation.

## Coverage and limits

The occurrence inventory contains 5687 lexical matches across 423
matched files: current tracked ADR/SPEC, migrations, tests, evidence, journals,
roadmaps, SQL/PowerShell/Python/Kotlin/Java/C, the72 frozen public external files,
seven allocation-chain inputs and34 request attachments supplied in this session.
The history inventory records37 reachable numeric-changing commits filtered to
Package0090, ceremony, V039–V043 and ADR/SPEC0087–0089 sources. Git history was
searched from ancestors, not only the current snapshot. File author dates and
last commits are recorded; they are not proof of approval or original selection.
Critical introductions below were additionally checked by git blame/reverse log.

Each lexical row includes source/line/date-or-commit/status/original-or-derived/
mutability/authority-role/rationale/dependents and a line hash. Raw long hex and
protected payloads are not reproduced. Generic TTL/deadline hits, unrelated UUIDs,
encoded-byte substrings and unrelated component clocks are not numeric authority.
UNKNOWN classifications remain explicit where a lexical hit has no established
causal role; they do not make the resolved critical conflict disappear. No claim
is made about unavailable earlier conversations or ephemeral files outside scope.

## Chronological decisions

| DATE / COMMIT | DECISION | VALUE | AUTHORITY | RATIONALE | SUPERSEDES | CURRENT STATUS |
|---|---|---|---|---|---|---|
|2026-09-25 /4dfd84f; later scoped addenda|ADR0088 signed bounded approval; V040/V041 semantics|Finite nonempty half-open interval; no prescribed60s|Final design closure, implementation excluded|Bound approval/revocation and exact scope|Only stated design/addendum scope|Foundational semantics, not numeric lifetime |
|2026-10-03 /19131bb, SPEC0090:596 blame|VECTOR_1 minimal-valid synthetic header/window|actual1,000,000us; max2,000,000us; health/interval100/200us|Design-vector context; overall R3 candidate|Positive finite nested codec vector|No production policy|Earliest reviewed binding/max/watchdog scalar root |
|2026-10-03 /60f7bbe|Independent technical fixture approval recorded ADR281–300;29-field policy frozen|Adds preflight tags28/29 at1s/2s; preserves other pairs|FLOOOW_TECHNICAL_FIXTURE_APPROVAL_2026-10-03; TEST_GOLDEN_REHEARSAL_ONLY|Complete amended fixture and independent Python/JVM agreement|Missing test TTL approval only|Digest e840fcad... retained; NOT production policy authority |
|2026-10-04 /fb0b2da;9ba136c|Isolated verification test vector|TEST-RUNTIME-ONLY60s/120s pairs|Disposable validation script, explicitly never production approval|Allow test-stage/expiry experiments|Nothing canonical|Separate numeric occurrence, not evidence that rehearsal60s was copied from it |
|Request11ba2c25 section12, no authenticated timestamp|Delegate duration selection if existing contract does not prescribe it|Smallest practical bounded window; no numeric60|Explicit user signing-scope instruction|Avoid arbitrary long duration; document reason|No existing binding policy|Earliest reviewed duration-discretion authority |
|2026-10-06 /ab0549d, domain report:13/107 blame|Select local nonrenewable operational budget under that discretion|60seconds|Bounded operational design; no window started|Local execution budget; not measured worst-case or security-calibrated constant|No fixture/watchdog bound|Earliest reviewed local numerical selection |
|Requestfa38ec36 section18:517–520; source references prior state|Explicitly adopt current signing contract|DB transaction timestamp +60s nonrenewable|User authority for bounded rehearsal|Freeze issuance basis and duration|No max/fixture supersession|Contract root for later explicit preservation, not first numerical selection |
|2026-10-06 /05fc44e, binding-input/plan closure|Retain generation budget; header relation still unresolved|60s approval, no concrete T0|Derived accepted rehearsal context|Avoid silently inventing header/signature equality|No policy change|Historical causal step |
|2026-10-06 /08d6025, TIME46/47/60/64|Select header=signed endpoints and require policy compatibility|[T0,T0+60s), binding actual/max still authoritative|Accepted local profile plus explicit subsequent request baselines|Original tuple nonrenewable; fail closed on policy conflict|TC-R01 remediates projection; does NOT replace values|Current local profile, no blanket production duration |
|2026-10-10 /f9dc0c9,e0e5e76,bd7ee39; current request|Preserve incompatible frozen profile and benchmark evidence|60m versus1m/2m; warm p99 97,028.8us|Explicit continuation with prohibition of shrink/widen|Evidence cannot grant numeric authority|No numeric supersession|HOLD_SAME_SEMANTIC_CONFLICT |

Dates for requests are not fabricated from filesystem mtime. Dependency order is
supported by their explicit baseline/reference text. The ab0549d publication may
contain multiple earlier local artifacts; commit publication is not creation time.

## Why60 exists — classification E

WINDOW_60S_REASON_CLASS=DERIVED_FROM_ANOTHER_CONTRACT. The deeper root is
request11ba2c25 section12's bounded-duration discretion, not a V040 constant.
The signing review:17/71 preserves that discretion without a number. The domain
report:13/107 selects60s as an operational design budget; requestfa38 section18
then treats it as the current signing contract. TIME and later requests explicitly
freeze it. Therefore it is not proven to be an unauthorized implementation default,
placeholder, universal60s security requirement or numeric cold-path guarantee.

Documented qualitative purpose: finite nonrenewable rehearsal approval/execution
budget. Why precisely60 rather than another bounded value has **no quantitative
attack calibration or full-path timing derivation in the reviewed root**. Warm
mechanics do not fill that gap. Earlier unrelated plusSeconds(60), fixture runtime
vectors, UUIDs and test timers are catalogued, not promoted into causal authority.

## Why1s and2s exist

SPEC21.2:596 supplies epoch+1us to epoch+1000001us, an exact1s synthetic
manifest/header interval. Tags14/15 carry binding actual1s/max2s. The other finite
pairs support a minimal-valid nesting vector. The max prevents silent actual
widening and is not a second TTL/grace; absolute expiry and immutable policy
govern operation. No reviewed numerical threat study justifies2s versus another
test ceiling. The named technical approval preserves the complete synthetic29-tag
fixture, while adding only preflight tags28/29. Git author identity cannot prove
which human selected these numbers; the record identifies technical fixture
authority/provenance, not an independently verified personal approver.

This vector predates the reviewed local60s selection. It did not define a universal
complete one-shot ceremony duration. Only the later accepted endpoint-equality
profile makes the full60s header interval collide with its selected binding pair.
No subsequent accepted supersession of either number was found. V039–V043 source,
tests and successful storage do not silently supersede the explicit profile.

##100us lineage and semantics

Same VECTOR_1 root: tags22/23 are WATCHDOG_ENFORCEMENT_INTERVAL100/200us;
tags24/25 are WATCHDOG_HEALTH_MAX_AGE100/200us. They are **two distinct
synthetic test-policy parameters** retained in the selected immutable rehearsal
fixture. Health age is DB-wall-clock age of independent checked_at; interval is
bounded enforcement cadence, not clock tolerance, DB update allowance, native ACK
deadline or an entire cancel/drain latency guarantee. Their numeric source remains
synthetic, not measured operational qualification. Current context cannot ignore
them merely because they are synthetic. No test/ADR amendment made them optional.
Our Docker/psql projection transport failed100us freshness in10/10 observations;
this disproves that tested route, not every possible architecture or a universal
lower bound. No widening or implicit alternative timing interpretation is adopted.
