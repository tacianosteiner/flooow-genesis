# Package 0090 - watchdog deployment closure boundary review

STATUS: STOP before watchdog implementation. Deployment closure was not achieved. G3F.4 HOLD, H01 OPEN/HIGH, watchdog deployment HIGH OPEN. Counts remain BLOCKER0/HIGH2/MEDIUM0/LOW0.

DECISION: preserve the strict target-identity requirement and do not execute destructive native signals. No compliant watchdog component is installed. NEXT_GATE remains G3F_4_WATCHDOG_DEPLOYMENT_CLOSURE; its next bounded technical prerequisite is generation-bound signaling contract/authorization, not numerical policy review.

The fetched local/remote baseline was 401a5e313efbec9a4100af8b6b6e237fffb4ca38, on checkpoint/package-0090-cloud-handoff, with a clean worktree before the new diagnostic. Previous transport review and all tracked baseline files remain byte-identical, including V001-V043, production adapters, ADR/SPEC, both fixtures and all historical HOLD evidence.

The authority review separates two facts. Existing directly authenticated postgres ADMIN already has sufficient catalog/readiness/native-signal privileges; no DB role, grant, service credential sharing or new SQL object is needed to call the existing APIs. However, the user sections5/7/13E/17 require a changed/reused backend identity to fail closed through the destructive action, forbid PID-only action and forbid introducing a third signaling mechanism. Under that strict reading, full implementation needs authorization for a generation-bound signaling primitive beyond the permitted native interface. WATCHDOG_NEW_AUTHORITY_REQUIRED=YES refers to this execution-mechanism authorization, not a missing database grant. No alternative mechanism, trust boundary or SQL function was introduced.

Real installed PostgreSQL18.4 catalog signatures are pg_cancel_backend(integer) and pg_terminate_backend(integer,bigint), the latter timeout defaulting to0. They accept no expected backend_start, database, role or incarnation. The version-tagged native source confirms PID lookup followed by signaling and documents a PID-reuse window. A caller-side predicate or repeated catalog read can reject an already changed identity; it cannot bind that checked generation to the eventual signal. This is an inference from the reviewed API/source, not an observed wrong-target signal. [Pinned PostgreSQL18.4 native source](https://raw.githubusercontent.com/postgres/postgres/REL_18_4/src/backend/storage/ipc/signalfuncs.c).

The strict user gate is stronger than SPEC18's bare OID/incarnation-whitelist wording. This review does not silently add an atomic primitive to SPEC, reinterpret successful observed guard tests as a universal replacement defense, or infer acceptance of the native residual race from the fact that native functions are named. A wrapper around those same functions cannot eliminate their unbound final-action window. A compliant stronger primitive needs separate governance under the existing no-new-mechanism boundary; none is implemented here.

Three real bounded read-only sessions were observed in the exact disposable container. The managed EXECUTOR in g3f4 matched the OID/database/backend_start/incarnation predicate. An unmanaged postgres session and a postgres session in the existing disposable postgres database were rejected. Wrong incarnation and deliberately stale expected backend_start were rejected for every subject. application_name was an observation label only, never the authority whitelist. All subjects finished naturally; no cancellation or termination was sent. The foreign subject also had an unmanaged role, so that case is disclosed as a combined negative control. No actual PID recycling was induced or claimed.

The full normative matrix below is reconstructed from ADR27/35/49/81/133 and SPEC5/6/7/18/21.2/21.3/25, with exact source text/lines retained in WATCHDOG-AUTHORITY-REVIEW.json. Proposed component boundaries are explicitly unimplemented. Shutdown/supervision details not concretely specified in SPEC are identified as derived fail-closed lifecycle obligations rather than invented normative protocol.

| Requirement | SPEC source | Proposed component | Failure action | Persisted state | Authority required |
|---|---|---|---|---|---|
| Monitor all exact governed service session OIDs/names; caller application_name is not authority | ADR:27, SPEC:88, SPEC:245 | Proposed external ADMIN catalog observer; no service process | Reject unmapped/recreated/renamed identities; no signal | Existing immutable slot/deployment configuration; no new SQL relation | Existing trusted deployment ADMIN |
| Exact approved endpoint, deployment and incarnation; clones stay ineligible | ADR:35, SPEC:96, SPEC:220 | Existing disposable endpoint guard plus proposed watcher incarnation validation | Reject wrong database/incarnation before write or signal | Existing incarnation/readiness; NOT_READY retained | Existing trusted deployment ADMIN |
| Protected marker relation, health/state, DB-clock heartbeat | SPEC:245, SPEC:586, SPEC:2210, SPEC:2217 | Proposed external ADMIN UPDATE public.offline_readiness.watchdog_checked_at/watchdog_healthy | Leave or mark NOT_READY/unhealthy on uncertainty; do not set READY by liveness | Existing offline_readiness; immutable policy binding preserved | Existing trusted deployment ADMIN |
| Finite reviewed cadence and maximum tolerated transaction/idle duration | SPEC:239, SPEC:243, SPEC:245, SPEC:586 | Proposed canonical 29-field bound-policy decoder and enforcement loop | Reject absent/zero/overflow/above-max/unqualified values | Existing immutable offline_deadline_policy; no fixture/new numbers | Existing trusted deployment ADMIN |
| Observe transaction wall-clock duration independently of session timeout settings | ADR:81, SPEC:245 | Proposed catalog xact_start/database-clock observer | Cancel/terminate overdue exact governed backend; SET timeout=0 does not bypass | No automatic ownership release; administrative incident evidence | Existing trusted deployment ADMIN |
| Observe idle-in-transaction duration | ADR:81, SPEC:245 | Proposed state/state_change/database-clock observer | Cancel/terminate exact overdue idle transaction; cancel acknowledgment alone is not drain completion | Existing readiness and unchanged ownership | Existing trusted deployment ADMIN |
| Native cancellation with target identity proved before action | SPEC:245 | pg_cancel_backend; permitted by user request section7 | No action if compound identity is unproved or changed | BACKEND_TIMEOUT/BACKEND_CANCELLED observations; no success inference | Existing trusted deployment ADMIN |
| Native termination when cancellation cannot enforce approved duration | SPEC:245 | pg_terminate_backend; permitted by user request section7 | No action against a replacement identity; verify actual target disappearance rather than boolean alone | BACKEND_TERMINATED observation; no completion/ownership inference | Existing trusted deployment ADMIN |
| Watchdog failure blocks new claim/effect admission and triggers drain | SPEC:245, SPEC:610, SPEC:612 | Existing S01/Q/S13 and mutation guards plus proposed independent supervisor/drain controller | Make readiness ineligible; independently drain and reconcile uncertain work | offline_readiness NOT_READY/unhealthy; exact recovery evidence only | Existing trusted deployment ADMIN |
| Stale ownership is never automatically released by crash, disconnect or timeout | ADR:49, SPEC:104 | Governed ADMIN recovery under C locks after prior-session drain | Mark STALE/ABORTED and advance generation only under existing exact recovery conditions | Existing execution/attempt/generation lineage; watchdog does not fabricate domain outcomes | Existing trusted deployment ADMIN |
| Recovery must distinguish early no-effects state from existing committed decision/head | SPEC:52, SPEC:104, SPEC:175 | Governed independent administrative recovery/reconciliation recorder | Existing decision/head requires reconcile; uncertainty requires manual review | Existing evidence/result; no synthetic EFFECTS_COMPLETE/SUCCESS | Existing trusted deployment ADMIN |
| Graceful shutdown cannot leave operational eligibility open | SPEC:245, SPEC:104 | Proposed stop controller: unhealthy/NOT_READY plus verified drain | No healthy heartbeat after shutdown; preserve uncertain ownership | Existing readiness; administrative drain/recovery obligation | Existing ADMIN; shutdown lifecycle is derived from fail-closed requirement, not a new SPEC signal API |
| Process crash/termination or inaccessible DB must fail closed | SPEC:245, SPEC:104 | Proposed independent supervisor plus DB-clock freshness checks | Lost heartbeat ages out; attempt unhealthy update/drain where reachable; on reconnect do not claim previous drain completion | Marker may stay physically unchanged while unreachable; derived freshness ineligible; recovery still required | Existing trusted deployment ADMIN |
| Normal DB restart retains incarnation/ownership; restart alone is not recovery | SPEC:96, SPEC:104, SPEC:612 | Proposed reconnect/startup exclusion and exact incarnation revalidation | No READY auto-promotion or receipt renewal; reconcile uncertain prior sessions/work | Retained incarnation, execution ownership, receipt scope and deadlines | Existing trusted deployment ADMIN |
| No service privilege widening or domain effects from watchdog | SPEC:604, SPEC:606, SPEC:2210 | External existing postgres ADMIN, isolated from four service credential sources | Reject new service grants/new helpers/domain writes | Exact non-secret authority state unchanged | Existing trusted deployment ADMIN |
| Receipts/TTL/policy values remain immutable | SPEC:588, SPEC:612, SPEC:2234 | Existing Q expiry rule and immutable policy storage | No heartbeat-based receipt renewal, fixture2 installation, fixture3 or numeric substitution | Existing policy and receipt bytes/deadlines unchanged | Existing trusted deployment ADMIN |
| Independent deployment packaging and secret-safe evidence | ADR:133, SPEC:249, SPEC:2236 | Proposed scripts/operations/rehearsal-watchdog; not enabled or created | No credential material in repository/logs; no declaration of COMPLETE without runtime proof | Existing trusted administrative evidence outside operational SQL surface | Existing trusted deployment ADMIN |
| PID replacement between observation and action must not receive a destructive signal | USER 5,7,13E,17 | Required generation-bound compare-and-signal execution primitive; absent from allowed native signatures | STOP before enforcement implementation; no signaling calls; no unauthorized alternate mechanism | Existing NOT_READY/unhealthy remains unchanged; deployment HIGH remains OPEN | Explicit governance for a generation-bound signaling mechanism beyond section7 allowed native PID APIs; no new DB role/grant is required for existing APIs |


The intended deployment boundary is out-of-process operations tooling, separate from AUDITOR/VERIFIER/ISSUER/EXECUTOR, with only the existing trusted ADMIN secret source. It must bind exact endpoint/deployment/incarnation and role whitelist; decode existing immutable policy rather than choose new durations; use database clocks for heartbeat and transaction/idle observations; make readiness ineligible on uncertainty; independently supervise failure and execute verified drain without domain effects. Restart is not recovery, receipt renewal or ownership release. A future component must use the approved control-lock recovery/reconciliation path, preserve decision/head evidence and never fabricate completion.

No startup/shutdown command, deployable configuration contract, health PASS or operational failure exit-code contract is supplied for a nonexistent component. The only executable command produced in this gate is the one-shot read-only boundary probe, `python scripts/validation/package_0090_watchdog_boundary_review.py`. It validates its pinned baseline and exact disposable identity, refuses to overwrite its private record, never invokes a signal and stops the disposable at completion. Re-running it after this checkpoint intentionally refuses the changed baseline. Proposed watchdog deployment location is scripts/operations/rehearsal-watchdog, not an enabled package.

Heartbeat refresh, cancellation, termination, normal stop/crash/SIGTERM, disconnect/restart/network/credential/catalog/write failures, timeout enforcement, real PID reuse, admission denial after a formerly healthy watchdog, drain and uncertain-work recovery are NOT_EXECUTED_BOUNDARY_STOP. Every unexecuted observation count is NULL, not an invented zero. Current readiness remains NOT_READY/unhealthy; no positive eligible state or synthetic READY was constructed. Previous continuous-marker observations are historical evidence, not runtime tests of a new component.

Validation: exact disposable project/image/volume/readonly bind and PG18.4 were verified. Existing native signatures and live non-destructive guard facts were confirmed. Complete non-secret role attributes/memberships/ownership/ACL/defaults/policy/migration state pre/post are equal; both canonical fingerprints are d697579bb78f8ecffbeb1407a100a2ef400bebd761967bfa6af8059c1379632c. Role/password mutation count is0. Local server-trust authentication was used for these disposable read-only probes; no credential was shared with a watchdog. The image startup file was required even for existing PGDATA, was not used to authenticate or rotate any database role, and was erased afterward. Marker contents and all baseline file hashes remain identical. Container stopped; no protected database/volume or production secret was used.

Prepared local scope: one read-only diagnostic tool and four required evidence artifacts. User section21 makes commit/push conditional on validation; the watchdog implementation was not validated, so no commit/push was performed. HEAD and fetched remote remain the accepted baseline; worktree contains only these five authorized new files. This is not a claim that the implementation, runtime matrix, contract coverage or deployment HIGH passed. No policy, fixture, production adapter, SQL authority or main branch changed. The necessary technical next action is to resolve the generation-bound signaling execution contract before implementation while preserving the same closed role/ACL/domain boundary. H01 cannot advance to numeric review until deployment closure and later eligible S01/Q timing are separately proven.

Requested return fields (conditional checkpoint is not performed):

```text
WATCHDOG_NEW_AUTHORITY_REQUIRED=YES
WATCHDOG_NEW_DATABASE_PRIVILEGE_REQUIRED=NO
REQUIRED_NEW_AUTHORIZATION=Generation-bound signaling mechanism outside the currently allowed pg_cancel_backend/pg_terminate_backend boundary
WATCHDOG_COMPONENT=NOT_IMPLEMENTED_AUTHORITY_AND_IDENTITY_BOUNDARY_STOP
WATCHDOG_DEPLOYMENT_LOCATION=PROPOSED scripts/operations/rehearsal-watchdog; no deployment enabled
WATCHDOG_TARGET_IDENTITY_MODEL=Expected project/image/volume plus deployment/incarnation/database OID/service role OID/name/PID/backend_start/client-backend category; application_name is not authority
WATCHDOG_PID_REUSE_PROTECTION=Observed stale-token guards PASS; atomic observation-to-signal protection UNPROVEN with allowed native APIs
HEARTBEAT_RUNTIME=NOT_EXECUTED_BOUNDARY_STOP
DB_CLOCK_AUTHORITY=CONFIRMED_EXISTING_CONTRACT_AND_REAL_CATALOG_CLOCK; writer not implemented
TRANSACTION_TIMEOUT_ENFORCEMENT=NOT_EXECUTED_BOUNDARY_STOP
IDLE_TIMEOUT_ENFORCEMENT=NOT_EXECUTED_BOUNDARY_STOP
CANCEL_RUNTIME=NOT_EXECUTED_BOUNDARY_STOP
TERMINATE_RUNTIME=NOT_EXECUTED_BOUNDARY_STOP
WATCHDOG_STOP_FAIL_CLOSED=NOT_EXECUTED_BOUNDARY_STOP
WATCHDOG_CRASH_FAIL_CLOSED=NOT_EXECUTED_BOUNDARY_STOP
DB_DISCONNECT_FAIL_CLOSED=NOT_EXECUTED_BOUNDARY_STOP
DRAIN_RUNTIME=NOT_EXECUTED_BOUNDARY_STOP
OWNERSHIP_AUTO_RELEASE=NO
WATCHDOG_CONTRACT_COVERAGE=INCOMPLETE
WATCHDOG_AUTHORITY_DELTA=NONE
WATCHDOG_DEPLOYMENT_IMPLEMENTATION=MISSING
WATCHDOG_DEPLOYMENT_HIGH=OPEN
G3F4_H01=OPEN
BLOCKER_COUNT=0
HIGH_COUNT=2
MEDIUM_COUNT=0
LOW_COUNT=0
FIXTURE_1_MUTATED=NO
FIXTURE_2_INSTALLED=NO
FIXTURE_3_CREATED=NO
PROTECTED_DATABASE_CONNECTION=NO
PROTECTED_VOLUME_MOUNT=NO
PRODUCTION_SECRET_USE=NO
PASSWORD_ROTATION=NOT_REQUIRED
NON_SECRET_AUTHORITY_FINGERPRINT_PRE=d697579bb78f8ecffbeb1407a100a2ef400bebd761967bfa6af8059c1379632c
NON_SECRET_AUTHORITY_FINGERPRINT_POST=d697579bb78f8ecffbeb1407a100a2ef400bebd761967bfa6af8059c1379632c
PLAINTEXT_CREDENTIAL_FILES_ERASED=YES
DISPOSABLE_CONTAINER_STOPPED=YES
NEXT_GATE=G3F_4_WATCHDOG_DEPLOYMENT_CLOSURE
CHECKPOINT=NOT_EXECUTED_IMPLEMENTATION_VALIDATION_CONDITION_NOT_MET
LOCAL_HEAD=401a5e313efbec9a4100af8b6b6e237fffb4ca38
REMOTE_HEAD=401a5e313efbec9a4100af8b6b6e237fffb4ca38
LOCAL_EQUALS_REMOTE=YES
WORKTREE=DIRTY_NEW_AUTHORIZED_STOP_EVIDENCE_ONLY
NEXT_TECHNICAL_ACTION=Resolve generation-bound signaling contract/authorization before implementation; do not advance numeric-bound review
```
