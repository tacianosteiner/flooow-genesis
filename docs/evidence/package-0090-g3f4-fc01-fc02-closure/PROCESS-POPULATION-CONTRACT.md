# Disposable process population contract

Status: EXPERIMENTAL TEST CONTRACT; no canonical or numeric authority.

The finite deployment is the pinned PostgreSQL 18.4 fresh primary in network=none,
without host mounts, replication configuration, archive destination or external
background-worker extensions. Four synthetic service logins are allocated. One
atomic native supervisor bootstraps one receiver, census observer and postmaster.
The approval consumer is the independent root-owned external-custody harness
thread; enforcement is a role of the census observer and receiver, not a separate
unobserved process. Co-location is explicitly recorded, never counted as an
independent health source. It remains a residual limitation of full watchdog parity.

| Process | Classification | Rule |
|---|---|---|
| Allocated client backend | GOVERNED | Native authentication, self pidfd, exact catalog identity, full context and current-generation receiver promotion are mandatory before SQL. |
| Unmanaged/ADMIN client backend | OBSERVED_ONLY | No capability authority; raw governed tables remain denied to unmanaged users. Disposable ADMIN supplies catalog evidence only. |
| Parallel worker with allocated current user | GOVERNED, UNSUPPORTED_EXECUTION_DENIED | V1 has no independent worker enrollment; actual executor/utility guard denies rather than inheriting leader eligibility. |
| Background worker with allocated current user | GOVERNED, UNSUPPORTED_EXECUTION_DENIED | Same guard; this fixture loads no external worker extension. |
| Autovacuum worker | OBSERVED_ONLY | PostgreSQL maintenance is not a governed business-capability execution or eligibility source. |
| Autovacuum launcher | OBSERVED_ONLY | Server maintenance scheduling, no capability admission. |
| Checkpointer | OBSERVED_ONLY | Server persistence, no capability admission. |
| Background writer | OBSERVED_ONLY | Server persistence, no capability admission. |
| WAL writer | OBSERVED_ONLY | Server WAL service, no capability admission. |
| PostgreSQL 18 I/O worker | OBSERVED_ONLY | Actual default primary population includes this type; storage I/O service grants no eligibility. |
| Logical replication launcher | OBSERVED_ONLY | Launcher exists without subscriptions; grants no capability. |
| WAL receiver | EXCLUDED_BY_CONTRACT | No standby/streaming source in the fresh-primary fixture. Known type is classified if observed. |
| WAL sender | EXCLUDED_BY_CONTRACT | No replication session configured; service roles have NOREPLICATION. Known type is classified if observed. |
| Logical replication worker | EXCLUDED_BY_CONTRACT | No subscription, logical slot or publisher configured. |
| Startup/recovery process | OBSERVED_ONLY during bootstrap; EXCLUDED after primary readiness | No recovery/standby deployment is claimed. Postmaster readiness and retained generation remain mandatory. |
| Archiver | EXCLUDED_BY_CONTRACT | Actual archive_mode is recorded; no archive destination is enabled. |
| Slot sync / WAL summarizer | EXCLUDED_BY_CONTRACT | Features are not provisioned; known types are classified, never authority publishers. |
| Postmaster | GOVERNED_CRITICAL_PARTICIPANT | Atomic retained anchor and immutable joint generation; no foreign PID acquisition. |
| Receiver | GOVERNED_CRITICAL_PARTICIPANT | Own retained anchor, original monotonic heartbeat/progress and private socket. |
| Supervisor | GOVERNED_CRITICAL_PARTICIPANT | Atomic own/child anchors, original progress and private bootstrap channel. |
| Observer/census worker | GOVERNED_CRITICAL_PARTICIPANT | Independent retained native worker; Supervisor detects alive-but-stalled progress. |
| Approval consumer | GOVERNED_CRITICAL_PARTICIPANT_NOT_FULLY_NATIVE_ANCHORED | Independent root-custody thread publishes bounded experimental gate; a lease is not complete kernel identity/channel/liveness proof. Keep full qualification HOLD. |
| Enforcement worker | GOVERNED_CRITICAL_ROLE_COLOCATED | Receiver/observer implement enforcement using retained anchors; no separate worker identity is invented. |
| Unknown process type | UNKNOWN_FAIL_CLOSED | Quarantine plus unresolved-observation latch. No silent exclusion, promotion or confirmed absence. |

Actual default types are captured from pg_stat_activity and independently logged
by the new census. Governing a process does not mean granting it execution authority.
Unsupported allocated-user workers must fail closed. Excluded feature populations
must not be promoted into a generic PostgreSQL deployment qualification.

Finite race population: seventeen named birth/death/generation/promotion/quarantine
observations from the user request. Each must map to a deterministic current-code
model vector or a real final runtime schedule. Model PID-tuple reuse is labeled as
such; it does not claim forcing the Linux allocator to reuse a numeric PID.

No universal mathematical scheduling proof or numeric watchdog policy follows.
