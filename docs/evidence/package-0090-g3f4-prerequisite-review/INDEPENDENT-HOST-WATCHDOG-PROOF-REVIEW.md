# Independent host/watchdog proof review — runtime HOLD

Branch `checkpoint/package-0090-cloud-handoff`; accepted inspection checkpoint
`f9dc0c9abddfc23f33a795f50c45472f06e02b2a`. No ADMIN promotion, policy provisioning,
V6 T0/key/SIGN, TREG R3, runner, new authority or main merge. All source pins are in
[SOURCE-SHA256.json](SOURCE-SHA256.json). Canonical V6 projection matches f9; all nine registration rows absent.
This is a prerequisite review, not a closure claim for operational readiness.


Existing contracts are used: ADR0090 independent external enforcement; SPEC18/21.2/21.3/25,
historical watchdog deployment review, self-pidfd proof and enrollment entrypoint/binding reviews.
Historical native-PID compare-then-signal was rejected as insufficient for replacement races.
The self-opened pidfd/socket Phase-A result is a preserved kernel primitive proof, not deployed PostgreSQL enrollment.
No alternate signaling API, SQL helper, service enrollment EXECUTE or production expansion is introduced.

| Question | Smallest compatible model / observed qualification |
|---|---|
|Healthy condition|Exact approved host/deployment/incarnation, current policy/history/catalog/roster, mandatory bounded enrollment, live receiver/control generation, identity-bound signaling, active finite enforcement loop, qualified supervisor/drain and no uncovered eligible backend; an empty cohort alone is insufficient |
|Observer|Independent out-of-process trusted host watchdog/receiver with server-derived identity and retained live self-pidfds; never caller application_name or copied numeric PID |
|Attestor|Existing trusted host/provisioning responsibility under exact scoped approval. Authenticated observer channel/context is required; a producer string or model boolean is not authentication |
|Field ownership|Both fields reside on ADMIN-owned offline_readiness, mutable under trusted deployment administration. The host health writer authors checked_at/healthy; PLAN_BINDING_ADMIN consumes them and does not self-author health. Separate responsibilities do not imply newly granted SQL roles |
|Source of truth|Current host observation/qualified enforcement is the evidence. DB fields are a protected projection consumed by guards, not a substitute observer or self-authenticating proof |
|Deployment binding|Approved host record + private-marker agreement + exact DB/system context + immutable header deployment + approved permanent role roster/history/catalog; system_identifier alone is insufficient |
|Incarnation binding|Same exact tuple in host record/header/readiness; receiver/control process generation context independently revalidated. Normal restart retains incarnation but invalidates old receiver-generation enrollment; clone requires governed reincarnation |
|Freshness|DB-generated finite checked_at, fresh DB clock with high-water continuity, no future timestamp, age<=100us actual.200us is approved ceiling, not grace. Commit/visibility/lock delay consumes age |
|Replay|Retained live anchors + fresh receiver/control generation, nonreused accepted connection context/sequence, exact canonical binding and role scope; payload/old epoch/old timestamp cannot reauthorize. No new persisted nonce/codec/table is approved here |
|Continuous health|Active supervised enforcement plus repeated time-bounded health observations. The existing row is not an active lease: it has no lease owner/epoch/expiry fence; cannot infer irrevocable coverage from healthy=true |
|Failure|Stop health refresh; deny new eligibility after freshness expires, mark unhealthy/NOT_READY where reachable, independently verify drain/recovery. Do not auto-release ownership or fabricate domain completion |

Fresh read-only evidence finds empty preload settings and an ALWAYS-enabled PL/pgSQL login guard
`flooow_g3f4_login_guard_cc2941797db3`. Its actual body checks four role names/OIDs,
database, host marker and recovery. It contains **no header lookup, no self-pidfd transfer,
no receiver enrollment/ACK or generation exchange**. This is a partial host/role guard, not
the governed watchdog proof. No inference is made about unknown processes outside the inspected sources.
Current V6 readiness is NOT_READY/false with no V6 binding; absence cannot be reported as healthy coverage.

The minimal model consumes the existing health projection only after independently authenticated,
current host conditions are proven. ADMIN R2 already avoids timestamp/healthy writes. Its locks
also prevent a concurrent writer refreshing that row until release: pre/post/final freshness and
actual host-to-DB cadence need qualification, not a written healthy flag. A durable deployment approval
is context authority; ephemeral receiver/anchor/enforcement evidence must be current.

The existing09d4... grant is artifact-promotion-only and excludes ADMIN/T0/key/SIGN/runner execution.
It does not authorize a policy change or silently approve missing native admission/epoch/ACK semantics.
Material pending boundary: exact private native login-handler/event configuration and trusted receiver/control
generation deployment, mandatory header-absent denial/self-anchor admission, governed finite ACK budget,
failure supervision and identity-bound enforcement/drain qualification. Existing service grants must remain unchanged.
The14-pair vector has no explicitly assigned enrollment ACK parameter; borrowing preflight TTL,
transaction timeout or freshness because all are microseconds is forbidden without a reviewed derivation.
Neither existing row ownership nor a producer label supplies this missing deployment/contract authority.

WATCHDOG_PROOF_MODEL=DERIVED_OBLIGATIONS_PENDING_ACK_EPOCH_AND_RUNTIME_QUALIFICATION
WATCHDOG_PROOF_INDEPENDENCE=MODEL_PASS_RUNTIME_UNPROVEN
WATCHDOG_PROOF_FRESHNESS=MODEL_BOUNDARY_PASS_RUNTIME_UNPROVEN
DEPLOYMENT_BINDING=DESIGN_BOUND_RUNTIME_COMPOSITE_UNQUALIFIED
INCARNATION_BINDING=DESIGN_BOUND_GENERATION_PROOF_UNQUALIFIED
ADMIN_SELF_AUTHORSHIP=NO
WATCHDOG_GATE=HOLD

No canonical login guard, event, marker, preload, role, ACL, receiver, health field or policy was changed.
The32 offline counterexamples are model assertions, not actual authenticated host/channel tests or watchdog deployment proof.
