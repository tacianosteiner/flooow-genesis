# Native enrollment and smallest host-proof contract — derived obligations

IS_NATIVE_ENROLLMENT_REQUIRED=YES_IN_ACCEPTED_PIDFD_LOGIN_EVENT_DIRECTION
PROTOCOL_IMPLEMENTATION_AUTHORIZED=NO_INCOMPLETE_EPOCH_FRAME_AND_ACK_CONTRACT

## Distinct enrollment/registration/activation objects

Source contracts: SPEC0090 sections3–5/18/25; SELF-ENROLLED-ANCHOR-PROOF;
ENROLLMENT-ENTRYPOINT-AUTHORITY-REVIEW; ENROLLMENT-BINDING-CONTRACT-CLOSURE;
the independently approved deployment/incarnation host record and its private
marker/protected roster. Historical source notes identify mandatory native login
event as the smallest direction with no service EXECUTE delta. The earlier
explicit SQL enrollment helper is a candidate superseded as preferred direction,
not an installed public API. Native protocol shape remains a reviewed draft.

HOST → approved DEPLOYMENT → approved INCARNATION → mandatory physical-backend
ENROLLMENT → continuous qualified WATCHDOG evidence → protected health projection
→ PLAN_BINDING_ADMIN verification → ADMIN activation.

| Question | Accepted representation/obligation | Current gap |
|---|---|---|
|Enrolled object|One live physical PostgreSQL governed service backend, retained self-pidfd and exact connection identity|Not enrollment of a UUID alone, launcher, host row or all DB users |
|Who enrolls|Automatic trusted private native LOGIN handler; receiver independently validates kernel/native/canonical evidence|Current PL/pgSQL handler lacks header lookup/self-anchor/receiver exchange |
|Authority|SERVICE_IDENTITY_ADMIN exact permanent roster; PLAN_BINDING_ADMIN immutable header scope; trusted host/DB deployment configuration|No permission inferred from matching g3f4 role names or writer privilege |
|Identifiers|Server-derived PID/MyProcPid, authenticated/session role OID/name, DB OID, ordinary backend type/start, exact binding/deployment/incarnation/slot, current receiver/control context and namespace|No caller application_name/PID/UUID authority; numeric PID/start/system identifier alone insufficient |
|Freshness|Fresh READ COMMITTED canonical lookup, anchor liveness before/after lookup/action, bounded synchronous admission ACK, current health actual100us|Finite ACK number/derivation, wire length and strong epoch bootstrap not governed |
|Revocation|Fresh action-time authorization and canonical generation/incarnation/state; revoke/expiry/failure denies new action/eligibility and triggers independent drain|No PID reacquisition, reset ownership, renewal or automatic reenrollment from old payload |
|Normal restart|Retain deployment incarnation; invalidate old receiver/server connection context and dead anchors; fresh admission only|Full control-anchor/generation handshake unqualified |
|Restore/clone|Inaccessible NOT_READY pending independently approved reincarnation/host agreement; copied old binding/proof cannot become live authority|System identifier can survive physical clone; actual native reincarnation not implemented |
|DB representation|Immutable offline_binding_header.identity_slots/deployment/incarnation; protected offline_readiness; existing direct ADMIN registration/control tables|No invented enrollment table, durable nonce, lease or parallel SOT |
|Host representation|Approved immutable host artifact/private marker and exact receiver/namespace configuration; retained live kernel anchors/current control context|Artifact approval is durable context, not current liveness or continuous coverage |

Binding registration inserts header plus independent original signed tuple and
control initialization. Activation updates lifecycle/readiness/claim conditions.
Neither registers a physical backend or proves independent enforcement. Header
absence must deny a recognized governed role; the accepted exact approved roster
supplies recognition, not inference from names. Empty cohort is not coverage:
mandatory future admission must be armed and qualified before vacuous coverage
can be relied on. No global role-enrollment expansion is introduced.

## What is watched — source-grounded formal obligations

Let C be independently approved deployment/incarnation/database/role roster/
policy/host-marker/namespace context, not caller data. Let B(C,t) be every live
eligible governed backend in that context. Define the proposed contract obligations:

```text
ENFORCEMENT_HEALTH(C,t) :=
    approved_context_matches_current_host_and_canonical_scope(C,t)
AND protected_mandatory_admission_is_armed(C,t)
AND authenticated_receiver_and_control_generation_are_current(C,t)
AND every b in B(C,t) has a retained live self-anchor and exact bound identity
AND supervised_enforcement_loop_is_within_approved_interval(C,t)
AND action-time identity/authority validation and identity-bound signaling are qualified
AND failure_detection_and_required_drain_are_qualified(C,t)

CONSUMABLE_HEALTH(C,t) :=
    ENFORCEMENT_HEALTH(C,t)
AND independently_written_projection_matches(C)
AND watchdog_healthy = true
AND finite_DB_checked_at <= fresh_DB_now
AND fresh_DB_now - DB_checked_at <= approved_actual_health_age
```

This is a formalization of existing obligations, not a newly authenticated proof
object or assertion that every term currently PASSes. SPEC18 watches all bound
service backends for stalled/idle/transaction deadlines independent of caller SET,
including auditor bounded reads. Receiver/supervisor continuity and exact identity
are mechanism prerequisites. Marker/policy/catalog/history/roster coherence bind
scope and deployment; a marker or DB reachability alone is never the predicate.

No contract was found making generic launcher integrity, all host process liveness,
every provider credential state or all migration activity a watchdog observation.
Credential/domain authority remains operation-specific canonical guard work;
history/ACL/policy manifests remain independently verified deployment/preflight
conditions. Do not turn this into unrestricted host or provider monitoring.

## Projection/trust boundary and100us semantics

watchdog_checked_at/watchdog_healthy are B: protected projections of independently
observed, currently qualified enforcement. They are not autonomous source-of-truth,
ADMIN activation flags or an active lease. Use existing fields and immutable
policy freshness; no new observed_at/expires_at table or cryptographic signing.
Host observation must genuinely be current when the trusted writer stamps DB time;
updating the timestamp cannot launder an old observation. Consumer uses fresh DB
wall time; transaction_timestamp is a transaction basis, not fresh health time.

PLAN_BINDING_ADMIN consumes current observation and does not create health.
Persistence owner is the NOLOGIN flooow_offline_control_owner (V0431113), distinct
from responsibility semantics. Existing SPEC1 explicitly trusts host/database
superuser and notes SINGLE_ADMIN_CAN_SELF_AUTHORIZE=POSSIBLE unless external
governance separates duties. Therefore hostile-superuser inability to forge a row
is NOT an accepted guarantee. Our isolated consumer ACL/peer proof does not alter
canonical grants, create a new trusted role, or contradict that threat boundary.

The100us actual/200us max pair is age, not transport grace. A separate100/200 pair
is enforcement interval, not ACK, precision tolerance or the full revoke/drain
latency. Both originated as synthetic VECTOR_1 and are unqualified on real host
paths. The observed Docker/psql route is incompatible with100us age; no universal
architectural impossibility is claimed and no value is changed.

## Fail-closed, replay and bypass obligations

Only a retained live descriptor selects a signal target. Private bounded socket
exchange requires kernel credentials/peer/message/self anchor agreement, current
canonical binding, one synchronous exact ACCEPT/DENY and a governed ACK deadline.
Replay of old context/receiver generation/dead anchor is denied; bounded current
observation cannot be extended by copying or restamping it. No PID-only reacquire.
Old projection with false/missing/future/stale health denies eligibility. Loss of
observer stops refresh and requires qualified failure/drain; it does not finish
domain reconciliation or release ownership. Restore cannot infer identity from
copied role OIDs/system identifier/header bytes.

The login event must be private, enabled ALWAYS, protected from alteration, with
event_triggers enabled and no service SET privilege. This requirement already
appears at ENTRYPOINT review:19; it is not a newly invented bypass rule. PG18
documents the configuration workaround for login triggers; our peer-authenticated
nonprivileged fixture role was denied SET event_triggers=false.
[PG18 event triggers](https://www.postgresql.org/docs/18/event-trigger-definition.html).
Fresh wall time versus transaction opening follows
[PG18 date/time semantics](https://www.postgresql.org/docs/18/functions-datetime.html).

## Exact unresolved release boundary

Govern native LOGIN handler/receiver configuration, bounded canonical frame limits,
strong current control/receiver generation and namespace provenance, finite ACK
authority/derivation, native server/header/roster lookup and mandatory absence
denial. Then qualify independent enforcement, signaling, failure supervision,
actual health projection cadence and drain on exact approved scope. Existing
artifact-only09d4... grant supplies none of this missing protocol authority.

No native PostgreSQL handler, event, preload, socket service, epoch bootstrap,
canonical proof object, new service EXECUTE or actual ADMIN successor is installed.
The disposable qualification harness tests existing kernel primitives and private
projection components only. Complete WATCHDOG_PROOF remains HOLD at a real
contract/provisioning authority boundary; generation/ACK representation is not
silently invented or borrowed from unrelated TTLs.
